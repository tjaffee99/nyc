"""Buildings of south-west Connecticut and Pike County (PA) with construction years.

    python counties_ct.py download [region ...]     cached downloads only (CT parcels; Pike: see below)
    python counties_ct.py build    [region ...]     -> data/interim/counties/ct_<region>.parquet (+ _report.json / .txt)
    python counties_ct.py estimate [region ...]     -> <name>_estimates.parquet for footprints without a year
    python counties_ct.py                           everything

Regions (TIGER 2024 county equivalents): greater_bridgeport 09120, western_connecticut 09190,
south_central_connecticut 09170, pike 42103 (pa_pike). Sources, licences, per-town coverage and what
is odd: data/research/counties_ct.md.

Connecticut: Office of Policy and Management / CT Geodata Portal, "Connecticut CAMA and Parcel
Layer" (2026 collection; assessors' CAMA joined to the towns' parcels). `AYB` = actual year built.
Same rules as counties_ny.py (footprint inner point -> smallest parcel under it that carries a year;
the largest building of a parcel is the main one, outbuildings follow it with `secondary`; placeholder
years per town, residential and other records separately; nothing spread or imputed in `year_raw`).
The output has the columns of ny_<county>.parquet.
"""
from __future__ import annotations

import gc
import gzip
import json
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

from common import INTERIM, RAW, log
import counties_ny as ny
from counties_ny import UTM, find_heaps, heap_evidence, heap_min, heap_min_other, mode_or_nan

CACHE = RAW / "counties_ct"
OUT = INTERIM / "counties"
OUTER_FOOTPRINTS = RAW / "overture" / "2026-10-21.0" / "outer_building.parquet"
CAMA = "https://services3.arcgis.com/3FL1kr7L4LvwA2Kb/arcgis/rest/services/Connecticut_CAMA_and_Parcel_Layer/FeatureServer/0/query"
FIELDS = ("OBJECTID,Town_Name,Parcel_ID,Location,Parcel_Type,Unit_Type,State_Use,State_Use_Description,Model,"
          "Living_Area,Land_Acres,Occupancy,AYB,EYB,Zone")
PAGE = 2000
MIN_AREA = 12.0
YEAR_LO, YEAR_HI = 1650, 2026

# key -> (TIGER name, FIPS, file stem, towns)   (towns as spelled in the layer; verified against the
# TIGER outlines with a spatial count of parcels per town, see the research note)
REGIONS = {
    "greater_bridgeport": ("Greater Bridgeport", "09120", "ct_greater_bridgeport",
                           ["Bridgeport", "Easton", "Fairfield", "Monroe", "Stratford", "Trumbull"]),
    "western_connecticut": ("Western Connecticut", "09190", "ct_western_connecticut",
                            ["Bethel", "Bridgewater", "Brookfield", "Danbury", "Darien", "Greenwhich", "New Canaan",
                             "New Fairfield", "New Milford", "Newtown", "Norwalk", "Redding", "Ridgefield", "Sherman",
                             "Stamford", "Weston", "Westport", "Wilton"]),
    "south_central_connecticut": ("South Central Connecticut", "09170", "ct_south_central_connecticut",
                                  ["Bethany", "Branford", "East Haven", "Guilford", "Hamden", "Madison", "Meriden", "Milford",
                                   "New Haven", "North Branford", "North Haven", "Orange", "Wallingford", "West Haven",
                                   "Woodbridge"]),
}
FIX_TOWN = {"Greenwhich": "Greenwich", "Deep_river": "Deep River"}


def fix_town(t):
    return FIX_TOWN.get(t, t)


# ---------------------------------------------------------------------------------------------
# downloads


def download_town(town):
    rng_f = CACHE / "meta" / f"oid_{town}.json"
    rng_f.parent.mkdir(parents=True, exist_ok=True)
    if rng_f.exists():
        rng = json.loads(rng_f.read_text())
    else:
        d = ny.get_json(CAMA, {"where": f"Town_Name='{town}'", "f": "json", "outStatistics": json.dumps([
            {"statisticType": "min", "onStatisticField": "OBJECTID", "outStatisticFieldName": "lo"},
            {"statisticType": "max", "onStatisticField": "OBJECTID", "outStatisticFieldName": "hi"},
            {"statisticType": "count", "onStatisticField": "OBJECTID", "outStatisticFieldName": "n"}])})
        a = d["features"][0]["attributes"]
        rng = {"lo": int(a["lo"]), "hi": int(a["hi"]), "n": int(a["n"])}
        rng_f.write_text(json.dumps(rng))
    d = CACHE / "parcels" / town
    d.mkdir(parents=True, exist_ok=True)
    pages = [(a, min(a + PAGE, rng["hi"] + 1)) for a in range(rng["lo"], rng["hi"] + 1, PAGE)]
    todo = [p for p in pages if not (d / f"oid_{p[0]}_{p[1]}.geojson.gz").exists()]
    log(f"parcels {town}: {rng['n']}, {len(todo)} of {len(pages)} pages to fetch")
    with ThreadPoolExecutor(3) as ex:
        list(ex.map(lambda p: ny.fetch_page(CAMA, f"Town_Name='{town}' AND OBJECTID >= {p[0]} AND OBJECTID < {p[1]}", FIELDS,
                                            d / f"oid_{p[0]}_{p[1]}.geojson.gz"), todo))


def download(keys):
    for k in keys:
        if k == "pike":
            continue
        for t in REGIONS[k][3]:
            download_town(t)


# ---------------------------------------------------------------------------------------------
# parcels


def use_of(code, desc, model):
    """CT State Use code / description -> 0 unknown, 1 single-family home, 2 residential, 3 commercial,
    4 office, 5 industrial, 6 government / civic, 7 other (the codes of the New York stage)."""
    d = desc.lower() if isinstance(desc, str) else ""
    try:
        c = int(str(code)[:3])
    except (TypeError, ValueError):
        c = -1
    if any(w in d for w in ("vac", " lnd", " land", "lnd ", "ubld", "acclnd", "open sp", "farm", "forest")) or d.endswith(("lnd", "land")):
        return 7
    if "single fam" in d or c in (101, 1010):
        return 1
    if any(w in d for w in ("condo", "two fam", "three fam", "four fam", "multi", "apart", "residential", "res ", "dwelling", "family")):
        return 2
    if any(w in d for w in ("office", "bank", "professional")):
        return 4
    if any(w in d for w in ("industr", "manufact", "warehouse", "utility", "factory", "ind/", "whs", "mdl 96")):
        return 5
    if any(w in d for w in ("school", "church", "relig", "mun ", "hospital", "municipal", "town", "state", "federal", "college", "univers",
                            "fire", "police", "library", "cemetery", "exempt", "charit", "public")):
        return 6
    if any(w in d for w in ("store", "retail", "commercial", "restaurant", "hotel", "motel", "shopping", "garage", "service", "mixed")):
        return 3
    if any(w in d for w in ("vacant", "farm", "forest", "park", "open", "recreation", "land")):
        return 7
    if 100 <= c < 200:
        return 2
    if 200 <= c < 300:
        return 3
    return 7 if c >= 0 else 0


def load_parcels(town):
    """The town's parcels (UTM), cached as one GeoParquet."""
    import geopandas as gpd
    import shapely
    out = OUT / f"ct_parcels_{town.replace(' ', '_')}.parquet"
    pages = sorted((CACHE / "parcels" / town).glob("oid_*.geojson.gz"))
    if not pages:
        return None
    if out.exists() and out.stat().st_mtime > max(p.stat().st_mtime for p in pages):
        return gpd.read_parquet(out)
    g = ny.pages_gdf(CACHE / "parcels" / town).to_crs(UTM)
    bad = ~g.geometry.is_valid.values
    if bad.any():
        g.loc[bad, "geometry"] = shapely.make_valid(g.geometry.values[bad])
    ayb = pd.to_numeric(g.AYB, errors="coerce")
    g["yr"] = ayb.where((ayb >= YEAR_LO) & (ayb <= YEAR_HI))
    g["Town_Name"] = fix_town(town)
    g = g[g.geometry.geom_type.isin(["Polygon", "MultiPolygon"]) & ~g.geometry.is_empty]
    OUT.mkdir(parents=True, exist_ok=True)
    g[["OBJECTID", "Town_Name", "Parcel_ID", "Location", "Unit_Type", "State_Use", "State_Use_Description", "Model", "Living_Area",
       "EYB", "yr", "geometry"]].to_parquet(out)
    return gpd.read_parquet(out)


def parcel_stacks(par):
    """One row per distinct parcel outline (condominium units share one): the most frequent year, class."""
    import geopandas as gpd
    c = par.geometry.representative_point()
    key = (np.round(c.x.values).astype(np.int64).astype(str) + "_" + np.round(c.y.values).astype(np.int64).astype(str)
           + "_" + np.round(par.geometry.area.values).astype(np.int64).astype(str))
    par = par.assign(stk=pd.factorize(key)[0])
    first = par.drop_duplicates("stk").set_index("stk")
    multi = par.stk.value_counts()
    multi = sorted(multi[multi > 1].index)
    st = first[["geometry", "Town_Name", "Parcel_ID", "State_Use", "State_Use_Description", "Model", "yr"]].copy()
    if multi:
        m = par[par.stk.isin(multi)]
        st.loc[multi, "yr"] = m.groupby("stk").yr.apply(mode_or_nan)
        # the unit that carries a use description: keep the first
    st["members"] = par.stk.value_counts().reindex(st.index).values
    st["parea"] = st.geometry.area.values
    return gpd.GeoDataFrame(st, geometry="geometry", crs=par.crs).reset_index()


# ---------------------------------------------------------------------------------------------
# footprints


def load_footprints(key):
    import duckdb
    import geopandas as gpd
    import shapely
    name, fips = REGIONS[key][:2]
    poly = ny.county_outline(fips)
    w, s, e, n = poly.bounds
    con = duckdb.connect()
    con.execute("SET memory_limit='1200MB'")
    con.execute("SET enable_progress_bar=false")
    df = con.execute(
        f"SELECT id, name, height, num_floors, source_dataset, ST_AsWKB(geometry) AS wkb FROM read_parquet('{OUTER_FOOTPRINTS}') "
        f"WHERE lon BETWEEN {w - 0.01} AND {e + 0.01} AND lat BETWEEN {s - 0.01} AND {n + 0.01}").df()
    con.close()
    g = gpd.GeoDataFrame(df.drop(columns="wkb"), geometry=shapely.from_wkb(df.wkb.apply(bytes).values), crs=4326)
    g, bad = ny.in_county(g, poly)
    n_all = len(g)
    area = g.geometry.to_crs(UTM).area.values
    g["area_m2"] = np.round(area, 1)
    g = g[area >= MIN_AREA].reset_index(drop=True)
    log(f"footprints {name}: Overture {n_all} in the region, {n_all - len(g)} under {MIN_AREA} m2 dropped, {bad} repaired, {len(g)} kept")
    return g, {"overture_in_region": n_all, "under_min_area": n_all - len(g), "repaired": bad, "kept": len(g)}


# ---------------------------------------------------------------------------------------------
# build


def build(key):
    import geopandas as gpd
    name, fips, stem, towns = REGIONS[key]
    if not all(any((CACHE / "parcels" / t).glob("oid_*.geojson.gz")) for t in towns):
        log(f"{name}: parcels incomplete -> run download")
        return None
    fp, counts = load_footprints(key)
    gc.collect()
    pars = [load_parcels(t) for t in towns]
    st = parcel_stacks(pd.concat(pars, ignore_index=True).pipe(lambda d: gpd.GeoDataFrame(d, geometry="geometry", crs=UTM)))
    del pars
    gc.collect()
    u = fp.geometry.to_crs(UTM)
    cen = u.centroid
    inside = u.contains(cen).values
    pt = gpd.GeoSeries(np.where(inside, cen.values, u.representative_point().values), crs=UTM)
    j = gpd.sjoin(gpd.GeoDataFrame({"fi": np.arange(len(fp))}, geometry=pt, crs=UTM),
                  st[["stk", "yr", "parea", "geometry"]], predicate="within")
    j["noyr"] = j.yr.isna()
    j = j.sort_values(["fi", "noyr", "parea"]).drop_duplicates("fi")
    sidx = pd.Series(j.stk.values, index=j.fi.values).reindex(np.arange(len(fp)))
    sp = st.set_index("stk").reindex(sidx.values)
    has = sidx.notna().values
    year = sp.yr.values.astype(float)
    town = sp.Town_Name.values.astype(object)
    if (~has).any():   # off every parcel (road bed, water edge): the town of the nearest parcel
        nn = gpd.sjoin_nearest(gpd.GeoDataFrame({"fi": np.flatnonzero(~has)}, geometry=pt[~has].values, crs=UTM),
                               st[["Town_Name", "geometry"]]).drop_duplicates("fi")
        town[nn.fi.values] = nn.Town_Name.values
    area = fp.area_m2.values
    order = pd.DataFrame({"s": sidx.values, "a": area}).sort_values(["s", "a"], ascending=[True, False])
    first = order.dropna(subset=["s"]).drop_duplicates("s").index
    secondary = has.copy()
    secondary[first] = False
    n_on = pd.Series(sidx.values).map(pd.Series(sidx.values).value_counts()).fillna(0).astype(int).values
    use = np.array([use_of(c, d, m) for c, d, m in zip(sp.State_Use.values, sp.State_Use_Description.values, sp.Model.values)], dtype=np.int8)
    cls = (sp.State_Use.fillna("").astype(str) + " " + sp.State_Use_Description.fillna("").astype(str)).str.strip().values
    kind = np.where(use <= 2, "homes", "other")   # (Bethel and Sherman publish no use: all count as homes)
    main_year = np.where(secondary, np.nan, year)
    unit = pd.Series(town).fillna("").values
    heap_rows = []
    for k, need in (("homes", heap_min), ("other", heap_min_other)):
        my = np.where(kind == k, main_year, np.nan)
        heap_rows += heap_evidence(find_heaps(my, unit, need), my, unit, pt.x.values, pt.y.values, k)
    county_heaps = {k: sorted(int(v) for v in find_heaps(np.where(kind == k, main_year, np.nan), np.full(len(fp), name), need)[name])
                    for k, need in (("homes", heap_min), ("other", heap_min_other))}
    heap = np.zeros(len(fp), bool)
    for r in heap_rows:
        if r["heap"]:
            heap |= (unit == r["town"]) & (kind == r["kind"]) & (year == r["year"])
    mm = pd.DataFrame({"muni": unit, "ok": np.isfinite(year)})[(kind == "homes") & ~secondary]
    share = mm.groupby("muni").ok.mean()
    muni_share = pd.Series(unit).map(share).fillna(0.0).round(3).values
    ll = fp.geometry.representative_point()
    height = fp.height.values.astype(float)
    height = np.where(height > 0, height, np.nan)
    out = gpd.GeoDataFrame({
        "id": fp.id.values, "county": name, "muni": unit, "town": unit,
        "height_m": height, "height_src": np.where(np.isfinite(height), "overture", ""),
        "floors": fp.num_floors.values.astype(float),
        "year_raw": year, "year_src": np.where(np.isfinite(year), "ct_cama_2026", ""),
        "heap": heap, "secondary": secondary,
        "prop_class": pd.Series(cls).fillna("").astype(str).values, "use": use,
        "year_hist": np.nan, "hist_src": "", "year_hist_ca": np.nan,
        "muni_year_share": muni_share,
        "lon": np.round(ll.x.values, 6), "lat": np.round(ll.y.values, 6),
        "name": fp.name.fillna("").values, "usn": "",
        "parcel": np.where(has, sp.Town_Name.fillna("").astype(str).values + " " + sp.Parcel_ID.fillna("").astype(str).values, ""),
        "n_on_parcel": n_on, "area_m2": area,
        "footprint_src": fp.source_dataset.replace({"OpenStreetMap": "overture:osm", "Microsoft ML Buildings": "overture:microsoft",
                                                    "Esri Community Maps": "overture:esri"}).fillna("").values,
    }, geometry=fp.geometry.values, crs=4326)
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / f"{stem}.parquet"
    out.to_parquet(f.with_suffix(".part"), index=False)
    f.with_suffix(".part").rename(f)
    report(stem, name, out, heap_rows, county_heaps, counts)
    return out


def report(stem, name, g, heaps, county_heaps, counts):
    dated = g.year_raw.notna()
    main = ~g.secondary
    rep = {"region": name, "footprints": int(len(g)), "counts": counts,
           "with_year": int(dated.sum()), "share_with_year": round(float(dated.mean()), 4),
           "main_buildings": int(main.sum()), "main_with_year": int((dated & main).sum()),
           "share_main_with_year": round(float((dated & main).sum() / max(main.sum(), 1)), 4),
           "heap_buildings": int(g.heap.sum()), "county_heaps": county_heaps,
           "top_years": {str(int(y)): int(n) for y, n in g.year_raw.value_counts().head(10).items()},
           "towns": {}}
    for t, d in g.groupby("town"):
        m = ~d.secondary
        yrs = d.year_raw.dropna()
        rep["towns"][t] = {"footprints": int(len(d)), "share_with_year": round(float(d.year_raw.notna().mean()), 3),
                           "share_homes_with_year": float(d.muni_year_share.iloc[0]),
                           "heap_buildings": int(d.heap.sum()),
                           "heap_years": sorted({h["year"] for h in heaps if h["town"] == t and h["heap"]}),
                           "tract_years": sorted({h["year"] for h in heaps if h["town"] == t and not h["heap"]}),
                           "median_year": None if not len(yrs) else int(yrs.median()),
                           "top_years": {str(int(y)): int(n) for y, n in yrs.value_counts().head(5).items()}}
    rep["decades"] = {str(int(k)): int(v) for k, v in (g.year_raw.dropna() // 10 * 10).value_counts().sort_index().items()}
    (OUT / f"{stem}_report.json").write_text(json.dumps(rep, indent=1))
    lines = [f"{name}: {rep['footprints']} footprints, {rep['share_with_year']:.1%} with a year, {rep['heap_buildings']} on placeholder years",
             "top years: " + json.dumps(rep["top_years"])]
    for t, r in sorted(rep["towns"].items()):
        lines.append(f"{t:16s} {r['footprints']:7d}  year {r['share_with_year']:.0%}  homes {r['share_homes_with_year']:.0%}  heaps {r['heap_years']}  tracts {r['tract_years']}")
    (OUT / f"{stem}_report.txt").write_text("\n".join(lines) + "\n")
    log(lines[0])


# ---------------------------------------------------------------------------------------------
# modelled years (Pike County: no open parcel file with a year; see data/research/counties_ct.md)
# A simplified form of counties_ny_estimates.py: the census's count of homes by decade built per block
# group (ACS 2018-2022 B25034) sets how many buildings fall in each decade, an ordering score
# (HISDAC-US first-built-up year of the 250 m cell, distance to the old centres, a stable hash) says
# which, footprints under 40 m2 beside a larger one follow it. No parcels: every footprint is its own lot.

ACS_PA = RAW / "counties_ct" / "acs" / "ACS_2022_5YR_BG_42.gdb.zip"
FBUY = RAW / "counties_ny_est" / "hisdac" / "x" / "FBUY" / "data" / "FBUY.tif"
BINS = [("pre1940", 1800, 1939, "B25034_E011"), ("1940s", 1940, 1949, "B25034_E010"), ("1950s", 1950, 1959, "B25034_E009"),
        ("1960s", 1960, 1969, "B25034_E008"), ("1970s", 1970, 1979, "B25034_E007"), ("1980s", 1980, 1989, "B25034_E006"),
        ("1990s", 1990, 1999, "B25034_E005"), ("2000s", 2000, 2009, "B25034_E004"), ("2010s", 2010, 2019, "B25034_E003"),
        ("2020-25", 2020, 2025, "B25034_E002")]
# old centres of Pike County (borough / village centres; coordinates of the places, WGS84)
PIKE_CENTRES = [(-74.8018, 41.3226), (-74.7035, 41.3695), (-74.8657, 41.2184), (-74.9535, 41.3150)]  # Milford, Matamoras, Dingmans Ferry, Lackawaxen-ish
MIN_MAIN = 40.0


def hash01(ids):
    return pd.util.hash_array(np.asarray(ids, dtype=object)).astype(np.float64) / 2.0 ** 64


def fbuy_at(lon, lat):
    import rasterio
    from pyproj import Transformer
    ds = rasterio.open(FBUY)
    x, y = Transformer.from_crs(4326, ds.crs, always_xy=True).transform(lon, lat)
    c, r = ~ds.transform * (np.asarray(x), np.asarray(y))
    r, c = np.floor(r).astype(int), np.floor(c).astype(int)
    a = ds.read(1, window=((r.min(), r.max() + 1), (c.min(), c.max() + 1)))
    v = a[r - r.min(), c - c.min()].astype(float)
    v[(v < 1700) | (v > 2020)] = np.nan
    return v


def load_bg_pa(bbox):
    import geopandas as gpd
    import pyogrio
    g = str(next((CACHE / "acs").glob("*.gdb")))
    bg = pyogrio.read_dataframe(g, layer="ACS_2022_5YR_BG_42_PENNSYLVANIA", bbox=bbox, columns=["GEOID"])
    t = pyogrio.read_dataframe(g, layer="X25_HOUSING_CHARACTERISTICS", read_geometry=False, columns=["GEOIDFQ"] + [b[3] for b in BINS])
    t["GEOID"] = t.pop("GEOIDFQ").str[-12:]
    return gpd.GeoDataFrame(bg.merge(t, on="GEOID", how="left"), geometry="geometry", crs=4326)


def model_years(df, units, centres, seed_ids=None):
    """df: id, lon, lat, area_m2, bg, fbuy (index = row). units: GEOID -> 10 ACS counts. Returns DataFrame
    (index of df): year_est, year_lo, year_hi, basis, secondary."""
    from scipy.spatial import cKDTree
    from pyproj import Transformer
    tr = Transformer.from_crs(4326, 32618, always_xy=True)
    x, y = tr.transform(df.lon.values, df.lat.values)
    cx, cy = tr.transform([c[0] for c in centres], [c[1] for c in centres])
    dcen = cKDTree(np.c_[cx, cy]).query(np.c_[x, y])[0]
    area = df.area_m2.values
    big = np.flatnonzero(area >= MIN_MAIN)
    # outbuildings: under MIN_MAIN m2 within 40 m of a larger footprint follow the nearest one
    follow = np.arange(len(df))
    if len(big):
        d, k = cKDTree(np.c_[x[big], y[big]]).query(np.c_[x, y])
        small = (area < MIN_MAIN) & (d <= 40)
        follow[small] = big[k[small]]
    main = follow == np.arange(len(df))
    h = hash01(df.id.values)
    fb = pd.Series(df.fbuy.values)
    bgs = df.bg.values
    year = np.full(len(df), np.nan)
    lo = np.full(len(df), np.nan)
    hi = np.full(len(df), np.nan)
    basis = np.full(len(df), "", object)
    # county-wide fallback distribution
    allu = np.sum([v for v in units.values()], axis=0).astype(float)
    for b in pd.unique(bgs):
        idx = np.flatnonzero((bgs == b) & main)
        if not len(idx):
            continue
        u = np.nan_to_num(np.asarray(units.get(b, allu), float))
        src = "acs_bg"
        if u.sum() < 5:
            u, src = allu, "acs_county"
        # (the block group's units are all of its homes, buildings of other kinds included)
        share = u / u.sum()
        # order: older first
        fr = fb.iloc[idx].rank(pct=True).fillna(0.5).values
        dr = pd.Series(dcen[idx]).rank(pct=True).values
        score = 0.55 * fr + 0.3 * dr + 0.35 * h[idx]
        order = np.argsort(score)
        n = len(idx)
        cum = np.minimum(np.round(np.cumsum(share) * n).astype(int), n)
        start = 0
        for bi, (lab, y0, y1, _) in enumerate(BINS):
            end = cum[bi]
            m = end - start
            if m <= 0:
                start = max(start, end)
                continue
            sel = idx[order[start:end]]
            pos = (np.arange(m) + 0.5) / m
            t = np.clip(pos + 0.3 * (h[sel] - 0.5), 0, 1)
            if bi == 0:      # stock built before 1940: growth curve ~ (t - 1800)^3, i.e. half built by 1915
                yy = y0 + (y1 - y0) * np.clip(t, 0, 1) ** (1 / 3.0)
                basis[sel] = f"{src}:pre1940+growth_curve"
            else:
                yy = y0 + (y1 - y0 + 1) * np.clip(t, 0, 0.999)
                basis[sel] = f"{src}:{lab}"
            year[sel], lo[sel], hi[sel] = np.floor(yy), y0, y1
            start = end
        left = idx[order[start:]]      # rounding remainder: the newest bin
        if len(left):
            year[left], lo[left], hi[left], basis[left] = 2020, 2020, 2025, f"{src}:2020-25"
    fo = np.flatnonzero(~main)
    for c, a in (("y", year), ("lo", lo), ("hi", hi)):
        a[fo] = a[follow[fo]]
    basis[fo] = pd.Series(basis[follow[fo]]).astype(str).values
    basis[fo] = [b + "+outbuilding_of_main" if b else b for b in basis[fo]]
    return pd.DataFrame({"year_est": year, "year_lo": lo, "year_hi": hi, "basis": basis, "secondary": ~main}, index=df.index)


def build_pike():
    import geopandas as gpd
    stem = "pa_pike"
    if not ACS_PA.exists() and not list((CACHE / "acs").glob("*.gdb")):
        log("Pike: ACS download missing")
        return None
    poly = ny.county_outline("42103")
    import counties_ct as me
    saved = me.REGIONS
    me.REGIONS = dict(saved, pike=("Pike", "42103", stem, []))
    try:
        fp, counts = me.load_footprints("pike")
    finally:
        me.REGIONS = saved
    bg = load_bg_pa(tuple(poly.bounds))
    ll = fp.geometry.representative_point()
    pts = gpd.GeoDataFrame({"i": np.arange(len(fp))}, geometry=ll.values, crs=4326)
    j = gpd.sjoin(pts, bg[["GEOID", "geometry"]], how="left", predicate="within").drop_duplicates("i")
    fp["bg"] = j.GEOID.values
    miss = fp.bg.isna().values
    if miss.any():
        k = gpd.sjoin_nearest(pts[miss].to_crs(32618), bg[["GEOID", "geometry"]].to_crs(32618)).drop_duplicates("i")
        fp.loc[fp.index[miss], "bg"] = k.GEOID.values
    fp["lon"], fp["lat"] = np.round(ll.x.values, 6), np.round(ll.y.values, 6)
    fp["fbuy"] = fbuy_at(fp.lon.values, fp.lat.values)
    units = {r.GEOID: np.array([r[b[3]] for b in BINS], float) for _, r in bg.iterrows()}
    est = model_years(fp, units, PIKE_CENTRES)
    height = fp.height.values.astype(float)
    height = np.where(height > 0, height, np.nan)
    out = gpd.GeoDataFrame({
        "id": fp.id.values, "county": "Pike", "muni": "Pike County", "town": "Pike County",
        "height_m": height, "height_src": np.where(np.isfinite(height), "overture", ""), "floors": fp.num_floors.values.astype(float),
        "year_raw": np.nan, "year_src": "", "heap": False, "secondary": est.secondary.values, "prop_class": "", "use": np.int8(0),
        "year_hist": np.nan, "hist_src": "", "year_hist_ca": np.nan, "muni_year_share": 0.0,
        "lon": fp.lon.values, "lat": fp.lat.values, "name": fp.name.fillna("").values, "usn": "", "parcel": "", "n_on_parcel": 0,
        "area_m2": fp.area_m2.values,
        "footprint_src": fp.source_dataset.replace({"OpenStreetMap": "overture:osm", "Microsoft ML Buildings": "overture:microsoft",
                                                    "Esri Community Maps": "overture:esri"}).fillna("").values,
    }, geometry=fp.geometry.values, crs=4326)
    OUT.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT / f"{stem}.parquet", index=False)
    e = est.assign(id=fp.id.values, bg=fp.bg.values, order="model")[["id", "year_est", "year_lo", "year_hi", "basis", "bg", "order"]]
    e = e.assign(year_est=e.year_est.astype("int16"), year_lo=e.year_lo.astype("int16"), year_hi=e.year_hi.astype("int16"))
    e.to_parquet(OUT / f"{stem}_estimates.parquet", index=False)
    rep = {"region": "Pike", "footprints": int(len(out)), "counts": counts, "share_with_year": 0.0, "share_modelled": 1.0,
           "main_buildings": int((~out.secondary).sum()), "units_acs": int(sum(v.sum() for v in units.values())),
           "decades_est": {str(int(k)): int(v) for k, v in (e.year_est // 10 * 10).value_counts().sort_index().items()}}
    (OUT / f"{stem}_report.json").write_text(json.dumps(rep, indent=1))
    log(f"Pike: {len(out)} footprints, {rep['main_buildings']} main, ACS units {rep['units_acs']}")
    return out


def validate(county_stem="ny_westchester", towns=("Scarsdale", "White Plains", "Rye")):
    """The Pike model run on dated Westchester towns with their years hidden (ACS table of New York)."""
    import geopandas as gpd
    import pyogrio
    from counties_ny_estimates import RAW as ER, BINS as NB
    df = pd.read_parquet(OUT / f"{county_stem}.parquet", columns=["id", "muni", "town", "area_m2", "year_raw", "heap", "secondary", "lon", "lat"])
    g = str(next((ER / "acs/gdb").glob("*.gdb")))
    bg = pyogrio.read_dataframe(g, layer="ACS_2022_5YR_BG_36_NEW_YORK", columns=["GEOID"], bbox=(-73.9, 40.9, -73.6, 41.1))
    t = pyogrio.read_dataframe(g, layer="X25_HOUSING_CHARACTERISTICS", read_geometry=False, columns=["GEOIDFQ"] + [b[3] for b in BINS])
    t["GEOID"] = t.pop("GEOIDFQ").str[-12:]
    bg = gpd.GeoDataFrame(bg.merge(t, on="GEOID"), geometry="geometry", crs=4326)
    rows = []
    for tn in towns:
        d = df[df.town.eq(tn) | df.muni.eq(tn)].reset_index(drop=True)
        d["fbuy"] = fbuy_at(d.lon.values, d.lat.values)
        j = gpd.sjoin(gpd.GeoDataFrame({"i": d.index}, geometry=gpd.points_from_xy(d.lon, d.lat), crs=4326), bg[["GEOID", "geometry"]], predicate="within").drop_duplicates("i")
        d["bg"] = pd.Series(j.GEOID.values, index=j.i.values).reindex(d.index).values
        d = d[d.bg.notna()].reset_index(drop=True)
        units = {r.GEOID: np.array([r[b[3]] for b in BINS], float) for _, r in bg.iterrows()}
        e = model_years(d, units, [(-73.8, 41.0)] if tn != "Rye" else [(-73.684, 40.98)])
        ok = d.year_raw.notna() & ~d.heap & ~d.secondary & e.year_est.notna()
        err = (e.year_est[ok] - d.year_raw[ok]).abs()
        rows.append((tn, int(ok.sum()), float(err.median()), float((err <= 10).mean()), float(((e.year_est[ok] // 10) == (d.year_raw[ok] // 10)).mean())))
    for r in rows:
        print("%-14s n=%6d median abs err %.0f y, within 10 y %.0f%%, same decade %.0f%%" % (r[0], r[1], r[2], 100 * r[3], 100 * r[4]))
    return rows


def main(argv):
    if argv and argv[0] == "validate":
        validate()
        return
    cmd = argv[0] if argv and argv[0] in ("download", "build", "estimate") else "all"
    keys = [a for a in argv if a in REGIONS or a == "pike"] or list(REGIONS) + ["pike"]
    if cmd in ("download", "all"):
        download(keys)
    if cmd in ("build", "all"):
        for k in keys:
            if k in REGIONS:
                build(k)
    if "pike" in keys or (cmd in ("estimate", "all") and not [a for a in argv if a in REGIONS]):
        build_pike()


if __name__ == "__main__":
    main(sys.argv[1:])
