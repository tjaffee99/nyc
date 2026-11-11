"""Census fill: generated buildings where the census counts people the map has no building for.
See data/research/census_fill.md.  Subcommands: points | table | ... (see main)."""
from __future__ import annotations
import sys, json, math
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd, duckdb, shapely
from common import INTERIM, RAW, TABLES

WORK = INTERIM / "census_fill"
WORK.mkdir(exist_ok=True)
INNER_FIPS = {"34017": "Hudson", "34003": "Bergen", "34013": "Essex", "34039": "Union", "34031": "Passaic",
              "36119": "Westchester", "36087": "Rockland"}
BOROS = {"36061": ("manhattan", "1"), "36005": ("bronx", "2"), "36047": ("brooklyn", "3"), "36081": ("queens", "4"), "36085": ("staten_island", "5")}
YEARS = list(range(1790, 1961, 10))


def places() -> gpd.GeoDataFrame:
    co = gpd.read_file(f"zip://{RAW / 'tiger' / 'tl_2024_us_county.zip'}").to_crs(4326)
    b = co[co.GEOID.isin(list(BOROS))].copy()
    b["place"] = b.GEOID.map(lambda g: BOROS[g][0]); b["pid"] = b.GEOID; b["kind"] = "borough"; b["county"] = "NYC"
    t = gpd.read_parquet(INTERIM / "towns" / "towns.parquet")
    t = t[t.county_fips.isin(list(INNER_FIPS))].copy()
    t["place"] = t["name"]; t["pid"] = t.geoid; t["kind"] = "town"; t["county"] = t.county_fips.map(INNER_FIPS)
    cols = ["pid", "place", "kind", "county", "geometry"]
    return pd.concat([b[cols], t[cols]], ignore_index=True).pipe(gpd.GeoDataFrame, crs=4326)


def points():
    con = duckdb.connect(); con.execute("SET memory_limit='1200MB'")
    I = INTERIM
    q = f"""select lon, lat, start_year s, end_year e, area_m2 a, 0 src from '{I}/nyc_building_points.parquet'
            union all select lon, lat, start_year, end_year, area_m2, 1 from '{I}/county_points_inner.parquet'"""
    df = con.execute(q).df()
    df.to_parquet(WORK / "points_all.parquet")
    print(len(df))


def pop_series() -> dict:
    """{pid: {year: persons}} for the boroughs (population.csv) and the municipalities (population_towns.csv)."""
    out = {}
    t = pd.read_csv(TABLES / "population.csv")
    t["population"] = pd.to_numeric(t.population.astype(str).str.replace(",", ""), errors="coerce")
    for g, (name, _) in BOROS.items():
        s = t[t.area.astype(str).str.lower().str.strip() == name].dropna(subset=["population"])
        out[g] = dict(zip(s.year.astype(int), s.population.astype(float)))
    tt = pd.read_csv(TABLES / "population_towns.csv", dtype={"geoid": str})
    tt["population"] = pd.to_numeric(tt.population.astype(str).str.replace(",", ""), errors="coerce")
    for g, s in tt.dropna(subset=["population"]).groupby("geoid"):
        out[g] = dict(zip(s.year.astype(int), s.population.astype(float)))
    return out


def interp(series: dict, y: float):
    """Census count at year y: exact, else log-linear between counts; None outside the series (no extrapolation
    except a start at the first count)."""
    if not series:
        return None
    ys = sorted(series)
    if y < ys[0] or y > ys[-1]:
        return None
    for a, b in zip(ys, ys[1:]):
        if a <= y <= b:
            if a == y: return series[a]
            if b == y: return series[b]
            return math.exp(math.log(series[a]) + (math.log(series[b]) - math.log(series[a])) * (y - a) / (b - a))
    return series[ys[0]]


def assign():
    pl = places()
    df = pd.read_parquet(WORK / "points_all.parquet")
    g = gpd.GeoDataFrame(df[[]], geometry=gpd.points_from_xy(df.lon, df.lat), crs=4326)
    idx = np.full(len(df), -1, np.int32)
    for i in range(0, len(g), 400000):
        j = gpd.sjoin(g.iloc[i:i + 400000], pl[["geometry"]], predicate="within", how="left")
        j = j[~j.index.duplicated()]
        idx[i:i + 400000] = j.index_right.fillna(-1).astype(np.int32).values
    df["pi"] = idx
    df.to_parquet(WORK / "points_all.parquet")
    pl.drop(columns="geometry").to_csv(WORK / "places.csv")
    print((idx < 0).mean())


def table():
    pl = pd.read_csv(WORK / "places.csv", dtype={"pid": str}, index_col=0)
    df = pd.read_parquet(WORK / "points_all.parquet")
    ps = pop_series()
    rows = []
    big = df.a.fillna(0).values >= 30
    for y in YEARS + [2020]:
        alive = big & (df.s.values <= y) & (df.e.values > y) & (df.pi.values >= 0)
        cnt = np.bincount(df.pi.values[alive], minlength=len(pl))
        for i, r in pl.iterrows():
            p = interp(ps.get(r.pid, {}), y)
            rows.append({"pid": r.pid, "place": r.place, "county": r.county, "year": y, "pop": p, "bld": int(cnt[i])})
    t = pd.DataFrame(rows)
    t["ppb"] = t["pop"] / t.bld.clip(lower=1)
    t.to_csv(WORK / "table_before.csv", index=False)
    pass


R_E = 6378137.0
URB = None


def grid(name):
    m = json.loads((INTERIM / f"grid_{name}_meta.json").read_text())
    return m, np.load(INTERIM / f"grid_{name}_covers.npy", mmap_mode="r"), np.load(INTERIM / f"grid_{name}_years.npy", mmap_mode="r")


def urban_area():
    """Urban + suburban ground (km2) per place and census year, from the region grid (58 m cells)."""
    from rasterio import features, transform
    from covers import URBAN, SUBURB
    pl = places()
    m, cov, yrs = grid("region")
    rows, cols, res = m["rows"], m["cols"], m["res"]
    X0, Y0 = m["X0"], m["Y0"]
    # cell centres in lon/lat: build place raster in mercator then use lon/lat polygons reprojected
    from pyproj import Transformer
    tr = Transformer.from_crs(4326, 3857, always_xy=True)
    polys = [shapely.transform(g, lambda a: np.column_stack(tr.transform(a[:, 0], a[:, 1]))) for g in pl.geometry]
    T = transform.Affine(res, 0, X0, 0, -res, Y0)
    pr = np.full((rows, cols), 65535, np.uint16)
    for i, g in enumerate(polys):
        features.rasterize([(g, i)], out=pr, transform=T, default_value=i)
    np.save(WORK / "place_raster_region.npy", pr)
    lat = lambda Y: np.degrees(2 * np.arctan(np.exp(Y / R_E)) - np.pi / 2)
    out = np.zeros((len(YEARS), len(pl)))
    for r0 in range(0, rows, 400):
        r1 = min(rows, r0 + 400)
        ymid = Y0 - (np.arange(r0, r1) + .5) * res
        ca = (res * np.cos(np.radians(lat(ymid)))) ** 2 / 1e6   # km2 per cell, per row
        y_ = np.asarray(yrs[:, r0:r1]); c_ = np.asarray(cov[:, r0:r1])
        k = None
        for t, Y in enumerate(YEARS):
            k = (np.nan_to_num(y_, nan=1e9) <= Y).sum(axis=0)
            cv = np.take_along_axis(c_, k[None].astype(np.int64), 0)[0]
            u = np.isin(cv, [URBAN, SUBURB])
            w = (u * ca[:, None])[pr[r0:r1] < 65535]
            out[t] += np.bincount(pr[r0:r1][pr[r0:r1] < 65535], weights=w, minlength=len(pl))
    pd.DataFrame(out, index=YEARS, columns=pl.pid).to_csv(WORK / "urban_km2.csv")


# ---------------------------------------------------------------- the model
# household size (persons per household, US censuses) -> floor for persons per building (x1.15: the map counts
# sheds, barns and garages of 30 m2 and more as buildings, a dwelling is one building in about 1.15)
HH = {1790: 5.8, 1800: 5.7, 1810: 5.7, 1820: 5.7, 1830: 5.6, 1840: 5.6, 1850: 5.55, 1860: 5.3, 1870: 5.1, 1880: 5.0,
      1890: 4.9, 1900: 4.76, 1910: 4.54, 1920: 4.34, 1930: 4.11, 1940: 3.67, 1950: 3.37, 1960: 3.33, 2020: 2.6}
D_REF, PPB_REF, EXPO = 12000.0, 6.5, 0.8     # ppb = 6.5 * (persons per urban km2 / 12000) ** 0.8 (fit on the anchors)
SHORT, MIN_DEF, FILL_TO = 0.75, 40, 0.85


def model():
    t = pd.read_csv(WORK / "table_before.csv", dtype={"pid": str})
    u = pd.read_csv(WORK / "urban_km2.csv", index_col=0); u.columns = u.columns.astype(str)
    t["urb"] = [u.loc[y, p] if y in u.index else np.nan for y, p in zip(t.year, t.pid)]
    t["dens"] = t["pop"] / t.urb.clip(lower=0.05)
    r0 = t[t.year == 2020].set_index("pid")
    r_today = (r0["pop"] / r0.bld.clip(lower=1)).to_dict()
    t["hh"] = t.year.map(HH)
    gen_floor = 1.15 * t.hh
    own = t.pid.map(r_today) * 1.2 * t.hh / HH[2020]          # the place's own ratio today, scaled back by household size
    t["floor"] = np.where(own.notna(), np.minimum(gen_floor, own.fillna(0).clip(lower=2.0)), gen_floor)
    t["ppb_dens"] = PPB_REF * (t.dens / D_REF) ** EXPO
    t["ppb_t"] = np.maximum(t["floor"], t.ppb_dens)
    t["need"] = t["pop"] / t.ppb_t
    t["deficit"] = t.need - t.bld
    t["trigger"] = (t.bld < SHORT * t.need) & (t.deficit > MIN_DEF) & t["pop"].notna() & (t.year <= 1960)
    return t[t.year <= 1960]


def model_table():
    t = model()
    t.to_csv(WORK / "model.csv", index=False)
    g = t[t.trigger].groupby("place").agg(years=("year", "count"), max_def=("deficit", "max"), first=("year", "min"))
    print(g.sort_values("max_def", ascending=False).head(40).round(0).to_string())
    print("total place-years triggered:", int(t.trigger.sum()), " total deficit to 85%:", int((FILL_TO * t.need - t.bld)[t.trigger].sum()))


# ---------------------------------------------------------------- candidates
from pyproj import Transformer
from scipy.spatial import cKDTree
from covers import URBAN, SUBURB
O = RAW / "overture" / "2026-10-21.0"
T_FWD = Transformer.from_crs(4326, 32618, always_xy=True)
T_INV = Transformer.from_crs(32618, 4326, always_xy=True)
HALF = {"residential": 5.0, "unclassified": 5.0, "living_street": 4.0, "tertiary": 7.0, "secondary": 8.0, "primary": 9.0,
        "trunk": 16.0, "motorway": 16.0}          # half carriageway + 1 m: no lot nearer than this to a road's centre line
SETBACK = {"residential": (6.5, 9.0), "unclassified": (6.5, 9.0), "living_street": (6.0, 8.0), "tertiary": (8.0, 10.5),
           "secondary": (9.0, 11.5), "primary": (10.0, 12.0)}
EXCL_LAND = ("park", "cemetery", "golf", "protected", "recreation", "railway")


def proj(geoms, T=T_FWD):
    g = np.asarray(geoms, dtype=object)
    c = shapely.get_coordinates(g)
    x, y = T.transform(c[:, 0], c[:, 1])
    return shapely.set_coordinates(g.copy(), np.column_stack([x, y]))


def cover_ground(lon, lat):
    """First urban/suburban spell of the terrain at each point: (start year, end year); NaN start = never city."""
    lon = np.asarray(lon); lat = np.asarray(lat)
    n = len(lon)
    X = np.radians(lon) * R_E
    Y = R_E * np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))
    g = np.full(n, np.nan); ge = np.full(n, np.nan)
    done = np.zeros(n, bool)
    for name in ("detail", "region"):
        m, cov, yrs = grid(name)
        c = np.rint((X - m["X0"]) / m["res"]).astype(int); r = np.rint((m["Y0"] - Y) / m["res"]).astype(int)
        ok = (~done) & (c >= 0) & (c < m["cols"]) & (r >= 0) & (r < m["rows"])
        idx = np.where(ok)[0]
        if not len(idx):
            continue
        o = np.argsort(r[idx] * m["cols"] + c[idx]); idx = idx[o]
        rr, cc = r[idx], c[idx]
        cv = np.stack([np.asarray(cov[k, rr, cc]) for k in range(5)])           # (5, n)
        tt = np.stack([np.asarray(yrs[k, rr, cc]) for k in range(4)])           # (4, n)
        tt = np.nan_to_num(tt, nan=9999.0)
        urb = np.isin(cv, [URBAN, SUBURB])
        gg = np.full(len(idx), np.nan); gend = np.full(len(idx), np.nan)
        for k in range(5):
            start = np.full(len(idx), 1600.0) if k == 0 else tt[k - 1]
            take = urb[k] & np.isnan(gg) & (start < 9999)
            gg[take] = start[take]
        for k in range(5):
            start = np.full(len(idx), 1600.0) if k == 0 else tt[k - 1]
            end = tt[k] if k < 4 else np.full(len(idx), 9999.0)
            inside = urb[k] & ~np.isnan(gg) & (start >= gg) & np.isnan(gend) & (start < 9999)
            # the spell ends at the first change after gg that leaves urban cover
            leave = inside & (k < 4) & ~(urb[k + 1] if k < 4 else True)
            gend[leave] = end[leave]
        gend[~np.isnan(gg) & np.isnan(gend)] = 9999.0
        g[idx] = gg; ge[idx] = gend; done[idx] = True
    return g, ge


def load_real(bb, placepoly=None):
    """All rows of the map (the city's and the counties') in a lon/lat box: (s, e, geometry in UTM, centroid x, y)."""
    x0, y0, x1, y1 = bb
    con = duckdb.connect(); con.execute("INSTALL spatial; LOAD spatial; SET memory_limit='600MB'")
    a = con.execute(f"select start_year s, end_year e, ST_AsWKB(geometry) w from '{INTERIM}/nyc_buildings.parquet' "
                    f"where lon between {x0} and {x1} and lat between {y0} and {y1}").df()
    b = con.execute(f"select start_year s, end_year e, ST_AsWKB(geometry) w from '{INTERIM}/county_buildings.parquet' "
                    f"where ST_Intersects(geometry, ST_MakeEnvelope({x0},{y0},{x1},{y1}))").df()
    d = pd.concat([a, b], ignore_index=True)
    geoms = shapely.from_wkb(d.w.apply(bytes).values)
    geoms = proj(geoms)
    c = shapely.centroid(geoms)
    return d.s.values.astype(np.float32), d.e.values.astype(np.float32), geoms, shapely.get_x(c), shapely.get_y(c)


def load_roads(bb):
    x0, y0, x1, y1 = bb
    con = duckdb.connect(); con.execute("INSTALL spatial; LOAD spatial; SET memory_limit='900MB'")
    env = f"ST_MakeEnvelope({x0},{y0},{x1},{y1})"
    a = con.execute(f"select class, ST_AsWKB(geometry) w from '{O}/roads_local.parquet' where class <> 'service' and ST_Intersects(geometry, {env})").df()
    b = con.execute(f"select class, ST_AsWKB(geometry) w from '{O}/roads_region.parquet' where ST_Intersects(geometry, {env})").df()
    d = pd.concat([a, b], ignore_index=True)
    g = proj(shapely.from_wkb(d.w.apply(bytes).values))
    return d["class"].values, g


def load_excl(bb):
    x0, y0, x1, y1 = bb
    con = duckdb.connect(); con.execute("INSTALL spatial; LOAD spatial; SET memory_limit='900MB'")
    env = f"ST_MakeEnvelope({x0},{y0},{x1},{y1})"
    out = []
    w = con.execute(f"select ST_AsWKB(geometry) w from '{O}/base_water.parquet' where ST_Intersects(geometry, {env})").df()
    out.append(shapely.from_wkb(w.w.apply(bytes).values))
    lu = "(" + ",".join(f"'{k}'" for k in EXCL_LAND) + ")"
    for f in ("base_land_use", "region5_land_use"):
        l = con.execute(f"select ST_AsWKB(geometry) w from '{O}/{f}.parquet' where subtype in {lu} and ST_Intersects(geometry, {env})").df()
        out.append(shapely.from_wkb(l.w.apply(bytes).values))
    for f in sorted((MANUAL := (RAW.parent / "manual")).glob("ports/*.geojson")) + [MANUAL / "sites" / "sites.geojson"]:
        try:
            gg = gpd.read_file(f).to_crs(4326)
            out.append(gg.geometry.values)
        except Exception as e:
            print("excl skip", f, e)
    allg = np.concatenate([np.asarray(o, dtype=object) for o in out])
    allg = allg[~shapely.is_empty(allg)]
    return proj(shapely.make_valid(allg))


def make_lots(lines, cls, rng, dens_tree, dens_pts_h):
    """Lot rectangles along both sides of each line. Returns arrays cx, cy, w, d, ang(rad), kind(0 frame,1 row,2 tenement), seg."""
    L = shapely.length(lines)
    mid = shapely.line_interpolate_point(lines, 0.5, normalized=True)
    mx, my = shapely.get_x(mid), shapely.get_y(mid)
    mp = np.column_stack([mx, my])
    nb = np.array([len(v) for v in dens_tree.query_ball_point(mp, 100.0)]) if len(mp) else np.zeros(0)
    bha = nb / (np.pi * 1.0)                   # small buildings today per hectare within 100 m
    # median height of the old buildings (built by 1935) within 150 m
    ht = dens_pts_h
    med = np.full(len(mp), np.nan)
    lists = dens_tree.query_ball_point(mp, 150.0)
    for i, v in enumerate(lists):
        if len(v):
            vv = ht[v]; vv = vv[~np.isnan(vv)]
            if len(vv): med[i] = np.median(vv)
    kind = np.where(np.isnan(med), np.where(bha >= 35, 1, 0), np.where(med >= 13.5, 2, np.where(med >= 9.0, 1, 0)))
    u = rng.random((len(lines), 4))
    base_w = np.where(kind == 2, 6.5 + 1.5 * u[:, 0],
              np.where(kind == 1, 5.0 + 1.5 * u[:, 0],
              np.where(bha >= 35, 5.5 + 1.5 * u[:, 0], np.where(bha >= 18, 8.0 + 2.0 * u[:, 0], 11.0 + 6.0 * u[:, 0]))))
    dep = np.where(kind == 2, 14.0 + 2.0 * u[:, 1], np.where(kind == 1, 11.0 + 3.0 * u[:, 1], np.where(bha >= 18, 10.0 + 3.0 * u[:, 1], 9.0 + 4.0 * u[:, 1])))
    lo = np.array([SETBACK.get(c, (6.5, 9.0))[0] for c in cls]); hi = np.array([SETBACK.get(c, (6.5, 9.0))[1] for c in cls])
    sb = lo + (hi - lo) * u[:, 2]
    gap = np.where(bha >= 35, 0.4, np.where(bha >= 18, 1.5, 3.0))
    n = np.floor((L - 4.0) / base_w).astype(int).clip(0)
    seg = np.repeat(np.arange(len(lines)), n)
    j = np.arange(len(seg)) - np.repeat(np.cumsum(n) - n, n)
    wl = (L[seg] - 4.0) / n[seg]
    pos = 2.0 + (j + 0.5) * wl
    cx, cy, ang, wd, dd, kd, sg = [], [], [], [], [], [], []
    for side in (1, -1):
        p = shapely.line_interpolate_point(lines[seg], pos)
        p1 = shapely.line_interpolate_point(lines[seg], np.maximum(pos - 1.0, 0)); p2 = shapely.line_interpolate_point(lines[seg], pos + 1.0)
        tx = shapely.get_x(p2) - shapely.get_x(p1); ty = shapely.get_y(p2) - shapely.get_y(p1)
        nrm = np.hypot(tx, ty); nrm[nrm == 0] = 1
        tx /= nrm; ty /= nrm
        off = sb[seg] + dep[seg] / 2
        cx.append(shapely.get_x(p) - side * ty * off); cy.append(shapely.get_y(p) + side * tx * off)
        ang.append(np.arctan2(ty, tx)); wd.append(wl - gap[seg]); dd.append(dep[seg]); kd.append(kind[seg]); sg.append(seg)
    cat = np.concatenate
    return cat(cx), cat(cy), cat(wd), cat(dd), cat(ang), cat(kd).astype(np.int8), cat(sg), np.tile(bha[seg], 2)


def rect_polys(cx, cy, w, d, ang):
    c, s = np.cos(ang), np.sin(ang)
    corners = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]], float)      # unit square corners
    px = corners[None, :, 0] * (w / 2)[:, None]; py = corners[None, :, 1] * (d / 2)[:, None]
    X = cx[:, None] + px * c[:, None] - py * s[:, None]
    Y = cy[:, None] + px * s[:, None] + py * c[:, None]
    return shapely.polygons(np.stack([X, Y], axis=2))


DEC = YEARS            # density is counted at the census years


_CACHE = {}


def county_data(pid, bb):
    """Everything a place needs, loaded once per county (the loads dominate the run time of a small place)."""
    pl = pd.read_csv(WORK / "places.csv", dtype={"pid": str}, index_col=0)
    co = pl.county[pl.pid == pid].iloc[0]
    if co == "NYC" or co not in set(pl.county):
        key = ("one", pid, bb)
    else:
        key = ("county", co)
    if key not in _CACHE:
        _CACHE.clear()
        gdf = places()
        if key[0] == "county":
            sub = gdf[(pl.county.values == co)]
            x0, y0, x1, y1 = sub.total_bounds
            cbb = (x0 - 0.003, y0 - 0.003, x1 + 0.003, y1 + 0.003)
        else:
            cbb = bb
        s, e, rg, rx, ry = load_real(cbb)
        cls, rd = load_roads(cbb)
        ex = load_excl(cbb)
        _CACHE[key] = dict(bb=cbb, s=s, e=e, rg=rg, rx=rx, ry=ry, cls=cls, rd=rd, ex=ex, rdb=shapely.bounds(rd), exb=shapely.bounds(ex))
    d = _CACHE[key]
    xs_, ys_ = T_FWD.transform([bb[0], bb[2], bb[0], bb[2]], [bb[1], bb[1], bb[3], bb[3]])
    lo_x, hi_x = min(xs_) - 300, max(xs_) + 300
    lo_y, hi_y = min(ys_) - 300, max(ys_) + 300
    m = (d["rx"] >= lo_x) & (d["rx"] <= hi_x) & (d["ry"] >= lo_y) & (d["ry"] <= hi_y)
    r = (d["rdb"][:, 2] >= lo_x) & (d["rdb"][:, 0] <= hi_x) & (d["rdb"][:, 3] >= lo_y) & (d["rdb"][:, 1] <= hi_y)
    x = (d["exb"][:, 2] >= lo_x) & (d["exb"][:, 0] <= hi_x) & (d["exb"][:, 3] >= lo_y) & (d["exb"][:, 1] <= hi_y)
    return d["s"][m], d["e"][m], d["rg"][m], d["rx"][m], d["ry"][m], d["cls"][r], d["rd"][r], d["ex"][x]


def cands(pid, k=0, n=1):
    k, n = int(k), int(n)
    pl = pd.read_csv(WORK / "places.csv", dtype={"pid": str}, index_col=0)
    gdf = places()
    i = int(pl.index[pl.pid == pid][0]); poly = gdf.geometry.iloc[i]
    rng = np.random.default_rng(int(pid[-6:]) + 7)
    x0, y0, x1, y1 = poly.bounds
    sx0, sx1 = x0 + (x1 - x0) * k / n, x0 + (x1 - x0) * (k + 1) / n       # this slab of the place (west to east)
    bb = (sx0 - 0.002, y0 - 0.002, sx1 + 0.002, y1 + 0.002)
    print(pid, pl.place[i], "slab", k, n, "loading", flush=True)
    s, e, rg, rx, ry, cls, rd, ex = county_data(pid, bb)
    print(" real rows", len(s), flush=True)
    keep = np.isin(cls, list(HALF))
    cls, rd = cls[keep], rd[keep]
    print(" roads", len(rd), "excl", len(ex), flush=True)
    # roads that are lot fronts: not motorway / trunk
    lot_front = np.isin(cls, list(SETBACK))
    # today's buildings for the district type
    stand = (e > 9000) & (s < 1935) & (np.asarray(shapely.area(rg)) >= 30)
    con = duckdb.connect()
    hh = con.execute(f"select lon, lat, height h from '{INTERIM}/nyc_building_points.parquet' where lon between {bb[0]} and {bb[2]} and lat between {bb[1]} and {bb[3]} and end_year > 9000 and start_year < 1935 and area_m2 between 30 and 600 "
                     f"union all select lon, lat, height from '{INTERIM}/county_points_inner.parquet' where lon between {bb[0]} and {bb[2]} and lat between {bb[1]} and {bb[3]} and start_year < 1935 and area_m2 between 30 and 600").df()
    hx, hy = T_FWD.transform(hh.lon.values, hh.lat.values)
    # density of ALL today's small buildings, heights of the old ones
    con2 = duckdb.connect()
    td = con2.execute(f"select lon, lat from '{INTERIM}/nyc_building_points.parquet' where lon between {bb[0]} and {bb[2]} and lat between {bb[1]} and {bb[3]} and end_year > 9000 and area_m2 between 30 and 600 "
                      f"union all select lon, lat from '{INTERIM}/county_points_inner.parquet' where lon between {bb[0]} and {bb[2]} and lat between {bb[1]} and {bb[3]} and area_m2 between 30 and 600").df()
    tx_, ty_ = T_FWD.transform(td.lon.values, td.lat.values)
    dens_tree = cKDTree(np.column_stack([tx_, ty_]))
    # for the median height, use a tree of the old ones: store heights aligned to a second tree
    old_tree = cKDTree(np.column_stack([hx, hy]))
    hv = np.nan_to_num(hh.h.values, nan=0.0)
    hv = np.where(hv > 0, hv, np.nan)
    cx, cy, w, d, ang, kind, seg, bha = make_lots_wrap(rd[lot_front], cls[lot_front], rng, dens_tree, old_tree, hv)
    print(" raw lots", len(cx), flush=True)
    # inside the place and the ground is city
    inside = shapely.contains_xy(proj([poly])[0], cx, cy)
    lon, lat = T_INV.transform(cx, cy)
    g, ge = cover_ground(lon, lat)
    inside &= (lon >= sx0) & (lon < sx1)
    ok = inside & ~np.isnan(g) & (g <= 1960) & (ge > g + 1)
    sel = np.where(ok)[0]
    cx, cy, w, d, ang, kind, bha, g, ge, seg = [a[sel] for a in (cx, cy, w, d, ang, kind, bha, g, ge, seg)]
    polys = rect_polys(cx, cy, w, d, ang)
    print(" in place and city ground", len(polys), flush=True)
    # exclusions: water, parks, cemeteries, rail yards, sites
    ok = np.ones(len(polys), bool)
    if len(ex):
        tr = shapely.STRtree(polys)
        hit = tr.query(ex, predicate="intersects")[1]       # the big polygons are the (prepared) query side
        ok[hit] = False
    # a road's carriageway: group by class
    for c, hw in HALF.items():
        m = cls == c
        if not m.any():
            continue
        tr = shapely.STRtree(polys)
        hit = tr.query(rd[m], predicate="dwithin", distance=hw)
        # a lot's own front road is further away than hw by construction
        ok[np.unique(hit[1])] = False
    print(" after exclusions", int(ok.sum()), flush=True)
    sel = np.where(ok)[0]
    cx, cy, w, d, ang, kind, bha, g, ge, polys = [a[sel] for a in (cx, cy, w, d, ang, kind, bha, g, ge, polys)]
    # lots against each other (greedy, in a random order, keep the first): no two within 1 m
    tr = shapely.STRtree(polys)
    a_, b_ = tr.query(polys, predicate="dwithin", distance=1.0)
    m = a_ < b_
    a_, b_ = a_[m], b_[m]
    order = np.argsort(a_, kind="stable"); a_, b_ = a_[order], b_[order]
    starts = np.searchsorted(a_, np.arange(len(polys) + 1))
    alive = np.ones(len(polys), bool)
    # greedy by index (the lots are already in a random street order)
    for k in range(len(polys)):
        if alive[k]:
            alive[b_[starts[k]:starts[k + 1]]] = False
    sel = np.where(alive)[0]
    cx, cy, w, d, ang, kind, bha, g, ge, polys = [a[sel] for a in (cx, cy, w, d, ang, kind, bha, g, ge, polys)]
    print(" after lots vs lots", len(polys), flush=True)
    # the map's rows near each lot
    rtree = shapely.STRtree(rg)
    ci, ri = rtree.query(polys, predicate="dwithin", distance=3.0)
    dist = shapely.distance(polys[ci], rg[ri])
    hit = dist < 3.0
    ci, ri = ci[hit], ri[hit]
    hs, he = s[ri], e[ri]
    # a lot that is blocked from its ground year to 1960 by one row is dropped
    blocked = np.zeros(len(polys), bool)
    full = (hs <= g[ci] + 0.5) & (he >= 1961)
    blocked[ci[full]] = True
    # density of the map's rows within 60 m, at each census year, and of the lots
    rc = np.column_stack([rx, ry]); lc = np.column_stack([cx, cy])
    rt = cKDTree(rc)
    cnt = np.zeros((len(cx), len(DEC)), np.uint8)
    for lo_ in range(0, len(cx), 50000):
        sl = slice(lo_, lo_ + 50000)
        nbs = rt.query_ball_point(lc[sl], 60.0)
        ln = np.array([len(v) for v in nbs])
        flat = np.concatenate(nbs).astype(np.int64) if ln.sum() else np.zeros(0, np.int64)
        own = np.repeat(np.arange(len(nbs)), ln)
        for t, Y in enumerate(DEC):
            al = (s[flat] <= Y) & (e[flat] > Y)
            cnt[sl][:, t] = 0
            c_ = np.bincount(own[al], minlength=len(nbs)).clip(0, 255)
            cnt[sl, t] = c_
    lt = cKDTree(lc)
    cand_n = np.array([len(v) for v in lt.query_ball_point(lc, 60.0)]).astype(np.uint16)
    # the place's old centre
    ys_ = np.array(DEC)
    ctr = np.array(proj([poly.centroid])[0].coords[0])
    inpoly = shapely.contains_xy(proj([poly])[0], rx, ry)
    for Y in DEC:
        al = inpoly & (s <= Y) & (e > Y)
        if al.sum() >= 150:
            ctr = np.array([np.median(rx[al]), np.median(ry[al])]); break
    keep = ~blocked
    remap = -np.ones(len(cx), np.int64); remap[keep] = np.arange(keep.sum())
    hmask = keep[ci]
    np.savez_compressed(WORK / (f"cand_{pid}.npz" if n == 1 else f"cand_{pid}_{k}.npz"), cx=cx[keep], cy=cy[keep], w=w[keep].astype(np.float32), d=d[keep].astype(np.float32),
                        ang=ang[keep].astype(np.float32), kind=kind[keep], bha=bha[keep].astype(np.float32), g=g[keep].astype(np.float32),
                        ge=ge[keep].astype(np.float32), cnt=cnt[keep], cand_n=cand_n[keep], ctr=ctr,
                        hc=remap[ci[hmask]].astype(np.int32), hs=hs[hmask].astype(np.float32), he=he[hmask].astype(np.float32))
    print(" candidates kept", int(keep.sum()), "of", len(cx), " hits", int(hmask.sum()), " peak MB", __import__("resource").getrusage(__import__("resource").RUSAGE_SELF).ru_maxrss // 1024, flush=True)


def run_county(*pids):
    for pid in pids:
        if (WORK / f"rows_{pid}.npz").exists():
            continue
        try:
            cands(pid)
            select(pid)
        except Exception as ex_:
            print("FAILED", pid, repr(ex_), flush=True)


def make_lots_wrap(lines, cls, rng, dens_tree, old_tree, hv):
    class _H:
        pass
    # make_lots wants a tree for the density (100 m) and heights for the 150 m median: give it both
    class Tree:
        def query_ball_point(self, pts, r):
            return dens_tree.query_ball_point(pts, r) if r <= 100.0 else old_tree.query_ball_point(pts, r)
    return make_lots(lines, cls, rng, Tree(), hv)


# ---------------------------------------------------------------- selection
RATIO_CUT = 0.6


def select(pid):
    m = model()
    mp = m[m.pid == pid].set_index("year")
    parts = [dict(np.load(f)) for f in ([WORK / f"cand_{pid}.npz"] if (WORK / f"cand_{pid}.npz").exists() else sorted(WORK.glob(f"cand_{pid}_*.npz")))]
    z, off = {}, 0
    for p_ in parts:
        p_["hc"] = p_["hc"] + off; off += len(p_["cx"])
    for key in parts[0]:
        z[key] = parts[0][key] if key == "ctr" else np.concatenate([p_[key] for p_ in parts])
    n = len(z["cx"])
    rng = np.random.default_rng(int(pid[-6:]) + 11)
    o = np.argsort(z["hc"], kind="stable")
    hc, hs, he = z["hc"][o], z["hs"][o], z["he"][o]
    ctr = z["ctr"]
    dist = np.hypot(z["cx"] - ctr[0], z["cy"] - ctr[1]) / 1000.0
    dn = dist / max(np.percentile(dist, 95), 0.5)
    ratio_all = z["cnt"].astype(np.float32) / np.maximum(z["cand_n"], 1)[:, None]
    used = np.zeros(n, bool)
    S = np.full(n, np.nan); E = np.full(n, np.inf); basis = np.full(n, "", object)
    u0 = rng.random(n); u1 = rng.random(n)
    log = []
    first = True
    for ti, y in enumerate(YEARS):
        if y not in mp.index or not np.isfinite(mp.loc[y, "pop"]):
            continue
        r = mp.loc[y]
        alive = used & (S <= y) & (E > y)
        have = r.bld + alive.sum()
        placed = retired = 0
        if have > r.need:
            op = np.where(alive & np.isinf(E))[0]
            k = int(min(have - r.need, len(op)))
            if k > 0:
                pick = op[np.argsort(u1[op])[:k]]
                E[pick] = np.maximum(S[pick] + 1.0, y - 10 + 10 * rng.random(k)); basis[pick] = "census_decline"
                retired = k
        elif have < SHORT * r.need and r.need - have > MIN_DEF:
            k = int(FILL_TO * r.need - have)
            win = 20.0 if first else 10.0
            elig = (~used) & (z["g"] < y - 0.5) & (z["ge"] > y) & (ratio_all[:, ti] < RATIO_CUT)
            lo = np.maximum(y - win, z["g"] + 0.3); hi = y - 0.2
            elig &= hi > lo + 0.3
            sc = lo + u0 * (hi - lo)
            hm = elig[hc]
            hci = hc[hm]; hsi = hs[hm]; hei = he[hm]; ss = sc[hci]
            blocked = np.zeros(n, bool)
            blocked[hci[(hsi <= ss) & (ss < hei)]] = True
            er = np.full(n, np.inf)
            later = hsi > ss
            np.minimum.at(er, hci[later], hsi[later])
            ok = elig & ~blocked & ((er - sc) >= 2.0)
            idx = np.where(ok)[0]
            score = ratio_all[idx, ti] + 0.3 * dn[idx]
            pick = idx[np.argsort(score, kind="stable")[:k]]
            used[pick] = True; S[pick] = sc[pick]
            ge_ = z["ge"][pick] - 0.5
            e0 = np.minimum(er[pick], np.where(z["ge"][pick] < 9000, ge_, np.inf))
            E[pick] = e0
            basis[pick] = np.where(er[pick] <= np.where(z["ge"][pick] < 9000, ge_, np.inf), "replaced_by_map", np.where(z["ge"][pick] < 9000, "ground_changed", ""))
            placed = len(pick)
            log.append((y, int(r.bld), int(r.need), int(k), placed, int(ok.sum())))
        first = False
    # rows still open: spread over 1960-1995
    op = used & np.isinf(E)
    E[op] = np.maximum(S[op] + 1.0, 1960 + 35 * u1[op]); basis[op] = "estimated"
    # a row whose end came out before its start + 1 (never): safety
    E[used] = np.maximum(E[used], S[used] + 1.0)
    idx = np.where(used)[0]
    np.savez_compressed(WORK / f"rows_{pid}.npz", idx=idx, S=S[idx], E=E[idx], basis=basis[idx].astype(str),
                        **{k: z[k][idx] for k in ("cx", "cy", "w", "d", "ang", "kind", "bha")})
    print(pid, mp.place.iloc[0], "candidates", n, "rows", len(idx))
    for l in log:
        print("   year %d: map %d need %d  ask %d  placed %d (feasible %d)" % l)


def collect(*pids):
    from shapely import wkb
    pl = pd.read_csv(WORK / "places.csv", dtype={"pid": str}, index_col=0).set_index("pid")
    frames = []
    for f in sorted(WORK.glob("rows_*.npz")):
        pid = f.stem[5:]
        z = np.load(f)
        if not len(z["idx"]):
            continue
        S, E, kind = z["S"].astype(float), z["E"].astype(float), z["kind"].astype(int).copy()
        h = (np.floor(np.abs(z["cx"] * 7.31 + z["cy"] * 3.17)) % 97) / 97.0
        kind[S < 1830] = 0
        kind[(S < 1860) & (kind == 2)] = 1
        st = np.zeros(len(S))
        frame = np.array([2, 2, 2, 3]); row = np.array([2, 3, 3, 3, 4]); ten = np.array([4, 5, 5, 5, 6])
        for kk, arr in ((0, frame), (1, row), (2, ten)):
            mm = kind == kk
            hh_ = h[mm]
            if kk == 2:
                st[mm] = np.where(S[mm] < 1880, 4 + (hh_ > 0.6), arr[(hh_ * len(arr)).astype(int) % len(arr)])
            elif kk == 1 and True:
                st[mm] = np.where(S[mm] < 1860, 2 + (hh_ > 0.5), arr[(hh_ * len(arr)).astype(int) % len(arr)])
            else:
                st[mm] = np.where(S[mm] < 1830, 2, arr[(hh_ * len(arr)).astype(int) % len(arr)])
        height = np.where(kind == 0, st * 3.0 + 1.5, st * 3.3 + 1.0)
        mat = np.where(kind == 0, "frame", "brick")
        polys = rect_polys(z["cx"].astype(float), z["cy"].astype(float), z["w"].astype(float), z["d"].astype(float), z["ang"].astype(float))
        polys = proj(polys, T_INV)
        c = shapely.centroid(polys)
        ids = ["cf" + ("%014x" % (hash((round(float(x), 6), round(float(y), 6))) & 0xFFFFFFFFFFFFFF)) for x, y in zip(shapely.get_x(c), shapely.get_y(c))]
        r = pl.loc[pid]
        area = {"36061": "1", "36005": "2", "36047": "3", "36081": "4", "36085": "5"}.get(pid, r.county)
        frames.append(gpd.GeoDataFrame({"id": ids, "start_year": np.round(S, 2), "end_year": np.round(E, 2), "height_m": np.round(height, 1),
                                        "storeys": st, "material": mat, "evidence": "census+ground", "end_basis": z["basis"],
                                        "area": area, "geometry": polys}, crs=4326))
        frames[-1]["pid"] = pid
    g = pd.concat(frames, ignore_index=True)
    g = g.drop_duplicates("id")
    g.drop(columns="pid").to_parquet(INTERIM / "gapfill" / "gapfill_census.parquet")
    g[["id", "pid"]].to_parquet(WORK / "row_places.parquet")
    print(len(g), "rows ->", INTERIM / "gapfill" / "gapfill_census.parquet")
    print(g.groupby("pid").size().rename(pl.place).sort_values(ascending=False).head(30))


# ---------------------------------------------------------------- checks
def load_out():
    g = gpd.read_parquet(INTERIM / "gapfill" / "gapfill_census.parquet")
    rp = pd.read_parquet(WORK / "row_places.parquet")
    g = g.merge(rp, on="id", how="left")
    return g


def check_table():
    """persons per building before / after, per place and census year."""
    g = load_out()
    pts = pd.read_parquet(WORK / "model.csv".replace(".csv", ".csv")) if False else None
    t = pd.read_csv(WORK / "model.csv", dtype={"pid": str})
    add = []
    for y in YEARS:
        al = (g.start_year <= y) & (g.end_year > y)
        c = g[al].groupby("pid").size()
        add.append(pd.DataFrame({"pid": c.index, "year": y, "gen": c.values}))
    a = pd.concat(add)
    t = t.merge(a, on=["pid", "year"], how="left")
    t["gen"] = t.gen.fillna(0)
    t["ppb_before"] = t["pop"] / t.bld.clip(lower=1)
    t["ppb_after"] = t["pop"] / (t.bld + t.gen).clip(lower=1)
    t.to_csv(WORK / "table_after.csv", index=False)
    top = g.groupby("pid").size().sort_values(ascending=False).index[:10]
    pd.set_option("display.width", 250)
    for pid in top:
        x = t[(t.pid == pid) & (t.gen > 0)][["place", "year", "pop", "bld", "need", "gen", "ppb_before", "ppb_after", "ppb_t"]]
        print(x.round(1).to_string(index=False))
    return t


def check_years():
    g = load_out()
    sy = np.floor(g.start_year).astype(int).value_counts().sort_index()
    ey = np.floor(g.end_year).astype(int).value_counts().sort_index()
    out = {}
    for name, v in (("starts", sy), ("ends", ey)):
        v = v.reindex(range(int(v.index.min()), int(v.index.max()) + 1), fill_value=0)
        nb = (v.rolling(7, center=True, min_periods=3).sum() - v) / (v.rolling(7, center=True, min_periods=3).count() - 1)
        ratio = (v / nb.clip(lower=1))
        big = v[(v > 300)]
        out[name] = {"max": int(v.max()), "max_year": int(v.idxmax()), "worst_vs_neighbours": float(ratio[v > 300].max()) if (v > 300).any() else 0.0,
                     "year": int(ratio[v > 300].idxmax()) if (v > 300).any() else None}
        print(name, out[name])
        v.to_csv(WORK / f"{name}_by_year.csv")
    return out


def check_overlap(pid):
    g = load_out()
    g = g[g.pid == pid]
    pl = pd.read_csv(WORK / "places.csv", dtype={"pid": str}, index_col=0)
    i = int(pl.index[pl.pid == pid][0]); poly = places().geometry.iloc[i]
    x0, y0, x1, y1 = poly.bounds
    s, e, rg, rx, ry = load_real((x0 - .002, y0 - .002, x1 + .002, y1 + .002))
    gp = proj(g.geometry.values)
    tr = shapely.STRtree(rg)
    gi, ri = tr.query(gp, predicate="intersects")
    gs, ge = g.start_year.values[gi], g.end_year.values[gi]
    ov = (s[ri] < ge) & (e[ri] > gs)
    # lots against lots
    t2 = shapely.STRtree(gp)
    a, b = t2.query(gp, predicate="intersects")
    m = a < b
    ov2 = (g.start_year.values[a[m]] < g.end_year.values[b[m]]) & (g.end_year.values[a[m]] > g.start_year.values[b[m]])
    print(pid, "rows", len(g), " overlapping a row of the map alive at the same time:", int(ov.sum()), " (distinct lots %d)" % len(set(gi[ov])), " lot-lot overlaps:", int(ov2.sum()))
    return int(ov.sum()), int(ov2.sum())


def holes_check():
    """holes.py's measure on the map as it was, and on the map plus these rows (the fine grid)."""
    import holes as H
    from scipy import ndimage
    pts = pd.read_parquet(WORK / "points_all.parquet", columns=["lon", "lat", "s", "e"])
    g = load_out()
    gc = shapely.centroid(g.geometry.values)
    add = pd.DataFrame({"lon": shapely.get_x(gc), "lat": shapely.get_y(gc), "s": g.start_year.values, "e": g.end_year.values})
    pl = places()
    m, cov, yrs = grid("detail")
    rows, cols, res, X0, Y0 = m["rows"], m["cols"], m["res"], m["X0"], m["Y0"]
    pr = np.load(WORK / "place_raster_detail.npy") if (WORK / "place_raster_detail.npy").exists() else None
    if pr is None:
        from rasterio import features, transform
        tr = Transformer.from_crs(4326, 3857, always_xy=True)
        T = transform.Affine(res, 0, X0 - res / 2, 0, -res, Y0 + res / 2)
        pr = np.full((rows, cols), 65535, np.uint16)
        for i, geom in enumerate(pl.geometry):
            gm = shapely.transform(geom, lambda a: np.column_stack(tr.transform(a[:, 0], a[:, 1])))
            features.rasterize([(gm, i)], out=pr, transform=T, default_value=i)
        np.save(WORK / "place_raster_detail.npy", pr)
    cell_ha = (res * np.cos(np.radians(40.75))) ** 2 / 1e4
    k = int(round(60.0 / (res * 0.758)))
    out = []
    for label, b in (("before", pts), ("after", pd.concat([pts, add], ignore_index=True))):
        X = np.radians(b.lon.values) * R_E; Y = R_E * np.log(np.tan(np.pi / 4 + np.radians(b.lat.values) / 2))
        c = np.rint((X - X0) / res).astype(int); r = np.rint((Y0 - Y) / res).astype(int)
        inb = (c >= 0) & (c < cols) & (r >= 0) & (r < rows)
        c, r, s_, e_ = c[inb], r[inb], b.s.values[inb], b.e.values[inb]
        for y in H.YEARS:
            urb = np.isin(H.cover_at(cov, yrs, y), [URBAN, SUBURB])
            al = (s_ <= y) & (e_ > y)
            has = np.zeros((rows, cols), bool); has[r[al], c[al]] = True
            near = ndimage.binary_dilation(has, iterations=max(k, 1))
            hole = ndimage.binary_opening(urb & ~near, iterations=1)
            lab, n = ndimage.label(hole)
            if not n:
                continue
            sizes = ndimage.sum(hole, lab, index=np.arange(1, n + 1)) * cell_ha
            keepl = np.where(sizes >= 3.0)[0] + 1
            msk = np.isin(lab, keepl)
            pid_ = pr[msk]; ok = pid_ < 65535
            ha = np.bincount(pid_[ok], minlength=len(pl)) * cell_ha
            for i in np.where(ha > 0)[0]:
                out.append({"which": label, "year": y, "place": pl.place.iloc[i], "pid": pl.pid.iloc[i], "ha": ha[i]})
    d = pd.DataFrame(out)
    d.to_csv(WORK / "holes_before_after.csv", index=False)
    p = d.pivot_table(index=["place"], columns=["year", "which"], values="ha", aggfunc="sum", fill_value=0)
    tot = d.groupby(["which", "year"]).ha.sum().unstack(0)
    print(tot.round(0))
    return d


def look(name, year, lon, lat, half=900):
    """A picture of one place and year: the terrain's city ground (grey), the map's rows alive then (black), the fill (red)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PatchCollection
    from matplotlib.patches import Polygon as MPoly
    year = float(year); lon = float(lon); lat = float(lat); half = float(half)
    cx, cy = T_FWD.transform(lon, lat)
    d = half / 80000.0
    s, e, rg, rx, ry = load_real((lon - d * 1.4, lat - d, lon + d * 1.4, lat + d))
    al = (s <= year) & (e > year)
    g = load_out()
    gp = proj(g.geometry.values)
    cg = shapely.centroid(gp)
    gx, gy = shapely.get_x(cg), shapely.get_y(cg)
    inwin = (abs(gx - cx) < half * 1.5) & (abs(gy - cy) < half * 1.1)
    ga = inwin & (g.start_year.values <= year) & (g.end_year.values > year)
    # terrain city ground on a 25 m raster
    xs = np.arange(cx - half * 1.5, cx + half * 1.5, 25.0); ys = np.arange(cy - half * 1.1, cy + half * 1.1, 25.0)
    XX, YY = np.meshgrid(xs, ys)
    lo, la = T_INV.transform(XX.ravel(), YY.ravel())
    gg, gge = cover_ground(lo, la)
    city = ((gg <= year) & (gge > year)).reshape(XX.shape)
    fig, ax = plt.subplots(figsize=(9, 6.5), dpi=100)
    ax.imshow(city, extent=(xs[0], xs[-1], ys[0], ys[-1]), origin="lower", cmap="Greys", vmin=0, vmax=4, alpha=0.5)
    win = (abs(rx - cx) < half * 1.6) & (abs(ry - cy) < half * 1.2) & al
    def patches(geoms):
        out = []
        for gm in geoms:
            if gm.geom_type == "Polygon":
                out.append(MPoly(np.asarray(gm.exterior.coords), closed=True))
        return out
    ax.add_collection(PatchCollection(patches(rg[win]), facecolor="#222", edgecolor="none"))
    ax.add_collection(PatchCollection(patches(gp[ga]), facecolor="#d62728", edgecolor="none"))
    ax.set_xlim(cx - half * 1.5, cx + half * 1.5); ax.set_ylim(cy - half * 1.1, cy + half * 1.1); ax.set_aspect("equal")
    ax.set_title(f"{name} {int(year)}: grey = ground the terrain calls city, black = {int(win.sum())} rows of the map, red = {int(ga.sum())} census fill", fontsize=9)
    ax.axis("off")
    (WORK / "look").mkdir(exist_ok=True)
    fig.savefig(WORK / "look" / f"{name}_{int(year)}.png", bbox_inches="tight"); plt.close(fig)
    print(name, year, "map", int(win.sum()), "fill", int(ga.sum()))


if __name__ == "__main__":
    globals()[sys.argv[1]](*sys.argv[2:])
