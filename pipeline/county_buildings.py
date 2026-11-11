"""Stage: the buildings of the counties around the city.

Input: data/interim/counties/<state>_<county>.parquet (counties_nj.py, counties_ny.py): one
row per footprint — Overture / state outlines with the construction year of the tax parcel
under them (New Jersey's MOD-IV tax list; New York's assessment rolls), a flag for
placeholder years, and a historic-inventory year where one exists. Only counties with real
years are built (common.REGION_COUNTIES lists the candidates; a county is on the map when
its file exists and data/manual/extent_counties.json names it), and within New York's
counties only the municipalities whose roll carries years (MIN_YEAR_SHARE).

Years, as in the city (nyc_buildings.py): historic inventory > parcel year (unless a
placeholder) > the shared estimator (placeholders are ranges, refined by recorded
neighbours; `estimated`). An outbuilding on a lot takes the lot's year as an estimate.
Nothing stands before its ground. Heights: the outline's own (OpenStreetMap, LiDAR-based
state data, Microsoft's estimates) > floors > a storey and a half by use (no height: said in
the popup's "Height" only by its roundness — there is no measured height for those).

Outputs: viewer/public/data/county-buildings/{13,11}/x/y.bin.gz + index.json,
data/interim/county_building_points.parquet (terrain, roads),
data/interim/county_buildings.parquet, data/interim/reports/county_buildings_summary.json
"""
from __future__ import annotations

import json
import os

import geopandas as gpd
import numpy as np
import pandas as pd

from common import INTERIM, MANUAL, NYC_CRS, VIEWER_DATA, YEAR_MIN, log
from nyc_buildings import (COLS, Ground, fill_estimates, find_heaps, h01, land_check, materials, ring_ground, row_timing,
                           write_tile_set)

UTM = NYC_CRS
OUT = VIEWER_DATA / "county-buildings"
SRC = INTERIM / "counties"
# The outer tier (docs/OUTER_ROUND.md; the owner, 2026-11-11: "compress the houses ... you probably
# only need real detail for a few places outside of the core"): the 19 county units beyond the
# seven around the city. Their own tile set; outlines of house size are stored as rectangles of
# the outline's area on its long axis, nothing under OUTER_MIN_M2 is drawn, and no full file is
# kept. `python county_buildings.py outer` builds it, one county file at a time.
OUT_OUTER = VIEWER_DATA / "outer-buildings"
INNER_FILES = {"nj_bergen", "nj_essex", "nj_hudson", "nj_passaic", "nj_union", "ny_rockland", "ny_westchester"}
OUTER_MIN_M2 = 60.0
RECT_MAX_M2 = 500.0      # a larger building keeps its outline (simplified to OUTER_SIMPLIFY_M)
RECT_FILL = 0.55         # ... and so does one that fills less of its bounding rectangle than this
OUTER_SIMPLIFY_M = 1.2
NOW = 2026.5
# a municipality is built when at least this share of its main buildings carries a year
MIN_YEAR_SHARE = 0.5
# pseudo building classes for the city's material rules, by use code
USE_CLASS = {0: "", 1: "A", 2: "C", 3: "K", 4: "O", 5: "F", 6: "W", 7: "Z"}


def built_counties():
    """County names that are on the map (data/manual/extent_counties.json: {"counties": {fips: name}})."""
    p = MANUAL / "extent_counties.json"
    if not p.exists():
        return None
    return set(json.loads(p.read_text()).get("counties", {}).values())


def county_heaps(raw, county):
    """Placeholder years per county: the city's rule (find_heaps: 300 buildings, three times
    its neighbours) and, for old houses, a rule for small piles. An assessor who does not know
    writes a round year - 1800 for 100 to 250 houses of a county where every other year of
    those decades holds two or three (and 1790, 1810, 1750 ...). Too few for the city's rule,
    but together they put 2,400 buildings in the year 1800 (the audit's spike), and the
    modelled years, which follow the recorded ones, copied the pile. A decade year before 1900
    with 15 or more buildings and four times the median of the plain years within four of it
    is a placeholder too ("by then": estimated from the buildings around, like the city's)."""
    found = find_heaps(raw, county)
    for c in np.unique(county):
        y = raw[(county == c) & np.isfinite(raw)].astype(int)
        y = y[y < 1900]
        cnt = dict(zip(*np.unique(y, return_counts=True)))
        hs = set(found.get(c, set()))
        for v in sorted(cnt):
            if v % 10 or v in hs or cnt[v] < 15:
                continue
            nb = [cnt.get(u, 0) for u in range(v - 4, v + 5) if u % 5 and u not in hs]
            if cnt[v] > 4 * max(float(np.median(nb)), 1.0):
                hs.add(v)
        found[c] = hs
    return found


def on_atlas(geoms_utm):
    """Per footprint: the year of the earliest traced atlas that draws this building (NaN: none
    does). The Hudson County layers of data/manual/atlas (Jersey City 1919, the Hoboken plates
    of 1891, the Heights of 1873) were traced to show what is gone; an outline that coincides
    with a building standing today is that building, and so it stood by the atlas's year - the
    only dated evidence for a county whose roll has a real year for one building in four."""
    import json
    import shapely
    from common import MANUAL
    from nyc_extras import ATLAS_SKIP
    out = np.full(len(geoms_utm), np.nan)
    files = [f for f in sorted((MANUAL / "atlas").glob("hudson_*.geojson")) if not f.stem.endswith("_coverage") and f.stem not in ATLAS_SKIP]
    if not files or not len(geoms_utm):
        return out
    garea = shapely.area(geoms_utm)
    for f in files:
        try:
            my = float(f.stem.rsplit("_", 1)[1])
            t = gpd.read_file(f).to_crs(UTM)
        except Exception:  # noqa: BLE001
            continue
        tg = t.geometry.values
        tg = tg[~shapely.is_missing(tg)]
        tg = shapely.make_valid(tg)
        tree = shapely.STRtree(tg)
        gi, ti = tree.query(geoms_utm, predicate="intersects")
        if not len(gi):
            continue
        inter = shapely.area(shapely.intersection(geoms_utm[gi], tg[ti]))
        fa, fb = inter / np.maximum(shapely.area(tg[ti]), 1e-6), inter / np.maximum(garea[gi], 1e-6)
        iou = inter / np.maximum(shapely.area(tg[ti]) + garea[gi] - inter, 1e-6)
        same = (iou >= 0.5) | ((fa >= 0.7) & (fb >= 0.6))
        hit = np.unique(gi[same])
        out[hit] = np.fmin(out[hit], my)
        log(f"counties: {f.stem}: {len(hit)} standing footprints are buildings drawn on the atlas of {int(my)}")
    return out


_TOWNS = []


def town_curves():
    """(STRtree of the municipalities' outlines, their geoids, {geoid: (census years, counts)}), or
    None: town_population.py's table and outlines (decision 54)."""
    if _TOWNS:
        return _TOWNS[0]
    _TOWNS.append(None)
    try:
        import shapely
        from common import INTERIM, TABLES
        tp, tt = INTERIM / "towns" / "towns.parquet", TABLES / "population_towns.csv"
        if tp.exists() and tt.exists():
            towns = gpd.read_parquet(tp).to_crs(4326)
            t = pd.read_csv(tt, dtype={"geoid": str})
            t["population"] = pd.to_numeric(t.population, errors="coerce")
            t["year"] = pd.to_numeric(t.year, errors="coerce")
            t = t.dropna(subset=["population", "year"])
            series = {}
            for gid, grp in t.groupby("geoid"):
                sv = sorted({float(y): float(v) for y, v in zip(grp.year, grp.population)}.items())
                if len(sv) >= 4:
                    series[gid] = (np.array([q[0] for q in sv]), np.array([q[1] for q in sv]))
            _TOWNS[0] = (shapely.STRtree(towns.geometry.values), towns.geoid.astype(str).values, series)
    except Exception as e:  # noqa: BLE001
        log(f"counties: town curves not read ({type(e).__name__}: {e})")
    return _TOWNS[0]


def by_town_growth(lon, lat, year, src, raw):
    """A placeholder that is a bound ("by 1900") was spread over the 25 years before it, the same
    in every town. The towns were not built in the same years: Jersey City's old wards before
    the Civil War, Hoboken from the 1860s, Bayonne and the towns on the Palisades after 1880.
    Each town's buildings that carry the same placeholder keep their order and take years along
    the town's own census curve up to the bound - the growth of each decade weighted by how
    much of it still stands (half lost every 40 years before the bound). Estimated, like the
    spread it replaces; a town without a census series early enough keeps the old spread."""
    tc = town_curves()
    if tc is None:
        return year, 0
    import shapely
    tree, geoids, series = tc
    sel = np.flatnonzero((src == "heap_by+spread") & np.isfinite(raw) & np.isfinite(year))
    if not len(sel):
        return year, 0
    qi, ti = tree.query(shapely.points(np.asarray(lon)[sel], np.asarray(lat)[sel]), predicate="within")
    town = np.full(len(sel), -1)
    town[qi] = ti
    out = year.copy()
    moved = 0
    d = pd.DataFrame({"i": sel, "town": town, "b": raw[sel].astype(int)})
    for (tn, b), grp in d[d.town >= 0].groupby(["town", "b"]):
        sv = series.get(geoids[tn])
        if sv is None or len(grp) < 8 or sv[0][0] > b - 15:
            continue
        ys, ps = sv
        knots = np.r_[ys[0] - 30.0, ys[ys < b], float(b)]
        pops = np.r_[0.0, ps[ys < b], float(np.interp(b, ys, ps))]
        grow = np.clip(np.diff(np.maximum.accumulate(pops)), 0.0, None)
        mid = (knots[:-1] + knots[1:]) / 2
        grow = grow * 0.5 ** ((b - mid) / 40.0)
        if grow.sum() <= 0:
            continue
        cdf = np.r_[0.0, np.cumsum(grow) / grow.sum()] + np.arange(len(knots)) * 1e-9
        idx = grp.i.values
        q = (pd.Series(year[idx]).rank(method="first").values - 0.5) / len(idx)
        new = np.minimum(np.interp(q, cdf, knots), b + 0.9)
        moved += int((np.abs(new - year[idx]) > 2).sum())
        out[idx] = new
    return out, moved


_EPOCHS = []


def map_epochs():
    """The built-up ground of dated maps as one grid over the whole box: per 0.0006-degree cell
    (about 55 m) the rank of the earliest map that shows it built up (1 = the oldest map; 0 =
    none does). The maps: the USGS sheets of the 1890s, of the 1940s and the 1:250,000 sheets of
    about 1957 (data/manual/gapfill/*builtup_*.geojson, *tint_*.geojson; decisions 43 and 54)."""
    if _EPOCHS:
        return _EPOCHS[0]
    _EPOCHS.append(None)
    try:
        import json
        import rasterio.features
        from rasterio.transform import from_origin
        from shapely.geometry import shape
        from common import MANUAL, REGION_BBOX
        layers = {}
        for f in sorted((MANUAL / "gapfill").glob("*builtup_*.geojson")) + sorted((MANUAL / "gapfill").glob("*tint_*.geojson")):
            for ft in json.loads(f.read_text())["features"]:
                y = pd.to_numeric(ft["properties"].get("year"), errors="coerce")
                if np.isfinite(y) and ft.get("geometry"):
                    layers.setdefault(int(round(float(y) / 10.0) * 10), []).append(shape(ft["geometry"]))
        if not layers:
            return None
        w, s_, e, n_ = REGION_BBOX
        res = 0.0006
        W, H = int(np.ceil((e - w) / res)), int(np.ceil((n_ - s_) / res))
        tr = from_origin(w, n_, res, res)
        grid = np.zeros((H, W), np.uint8)
        years = sorted(layers)
        for k in range(len(years), 0, -1):          # the latest first: an earlier map overwrites
            m = rasterio.features.rasterize([(g, 1) for g in layers[years[k - 1]]], out_shape=(H, W), transform=tr, fill=0, dtype="uint8")
            grid[m == 1] = k
        _EPOCHS[0] = (grid, w, n_, res, years)
        log(f"counties: dated maps of built-up ground: {years} ({[int((grid == k + 1).sum()) for k in range(len(years))]} cells first built up on each)")
    except Exception as e:  # noqa: BLE001
        log(f"counties: dated maps not read ({type(e).__name__}: {e})")
    return _EPOCHS[0]


def order_by_maps(lon, lat, xy, year, src, raw=None):
    """Estimated years follow the order in which the maps show the ground built up. A year that
    is modelled (the census's homes by decade in the block group, the assessor's counts per
    cell) or taken from the buildings around is right as a distribution and blind as to which
    house came first. Within a square kilometre and one kind of estimate the years are dealt
    out again: the buildings on ground an older map shows built up take the earliest. The
    square's set of years does not change; recorded years are not touched."""
    ep = map_epochs()
    if ep is None:
        return year, 0
    grid, w, n_, res, years = ep
    c = np.clip(((np.asarray(lon) - w) / res).astype(int), 0, grid.shape[1] - 1)
    r = np.clip(((n_ - np.asarray(lat)) / res).astype(int), 0, grid.shape[0] - 1)
    rank = grid[r, c].astype(np.int64)
    rank = np.where(rank == 0, len(years) + 1, rank)
    kind = np.where(src == "modelled", 1, np.where(src == "modelled_cells", 2, np.where(src == "neighbours", 3, 0)))
    # (a placeholder that is a bound - "by 1900" - is dealt out again only among the buildings
    # that carry the same placeholder: the bound holds for each of them)
    by = np.array([str(v).startswith("heap_by") for v in src])
    heap_year = np.where(by & np.isfinite(raw), raw, 0).astype(np.int64) if raw is not None else np.zeros(len(year), np.int64)
    kind = np.where(by & (heap_year > 0), 4, kind)
    sel = np.flatnonzero((kind > 0) & np.isfinite(year))
    if not len(sel):
        return year, 0
    key = ((np.floor(xy[sel, 0] / 1000).astype(np.int64) * 100003 + np.floor(xy[sel, 1] / 1000).astype(np.int64)) * 8 + kind[sel]) * 4096 + heap_year[sel]
    d = pd.DataFrame({"i": sel, "key": key, "rank": rank[sel], "year": year[sel]})
    by_map = d.sort_values(["key", "rank", "year"], kind="stable")
    by_year = d.sort_values(["key", "year"], kind="stable")
    out = year.copy()
    out[by_map.i.values] = by_year.year.values
    return out, int((np.abs(out[sel] - year[sel]) > 0.5).sum())


def county_files(outer=False):
    files = (sorted(SRC.glob("n[jy]_*.parquet")) + sorted(SRC.glob("ct_*.parquet")) + sorted(SRC.glob("pa_*.parquet"))) if SRC.exists() else []
    files = [f for f in files if not f.stem.endswith(("_estimates", "_inventory"))]   # (read beside their county's file, below)
    return [f for f in files if (f.stem not in INNER_FILES) == outer]


def load(files=None, outer=False):
    if files is None:
        files = county_files()
    keep = None if outer else built_counties()
    if os.environ.get("COUNTIES"):   # test run: only these (names, comma-separated)
        keep = set(os.environ["COUNTIES"].split(","))
    parts = []
    for f in files:
        g = gpd.read_parquet(f)
        if g.crs is None:
            g = g.set_crs(4326)
        if keep is not None:
            g = g[g.county.isin(list(keep))]
        # New York's rolls publish no year at all for some municipalities (22 of Westchester's
        # 43: Mount Vernon, Greenburgh, Peekskill ...; data/research/counties_ny.md). Their
        # buildings are not drawn: a year for them could only be generated.
        # Where the roll has none (22 of Westchester's 43 municipalities), a year comes from
        # <file>_estimates.parquet (counties_ny_estimates.py: the census's count of homes by
        # decade built per block group, spread by the town's growth — an estimate, and marked
        # so). Without that file those municipalities are left out rather than given a year.
        ep = f.with_name(f.stem + "_estimates.parquet")
        if ep.exists():
            e = pd.read_parquet(ep).drop_duplicates("id").set_index("id")
            g["year_est"] = pd.to_numeric(e.year_est.reindex(g["id"].values).values, errors="coerce")
            g["est_basis"] = e.basis.reindex(g["id"].values).values if "basis" in e else None
            log(f"counties: {f.name}: {int(g.year_est.notna().sum())} footprints carry an estimated year ({ep.name})")
        elif "muni_year_share" in g:
            n0 = len(g)
            g = g[pd.to_numeric(g.muni_year_share, errors="coerce").fillna(0) >= MIN_YEAR_SHARE]
            if len(g) < n0:
                log(f"counties: {f.name}: {n0 - len(g)} footprints left out (municipalities whose roll has no construction years)")
        # a state inventory's construction dates (conncris.py): only where the assessor's year
        # is a placeholder or missing - a plain year as year_hist, a "circa" year as year_hist_ca
        ip = f.with_name(f.stem + "_inventory.parquet")
        if ip.exists() and len(g):
            inv = pd.read_parquet(ip).drop_duplicates("id").set_index("id")
            yi = pd.to_numeric(inv.year_inv.reindex(g["id"].values).values, errors="coerce")
            ca = inv.circa.reindex(g["id"].values).fillna(False).values.astype(bool)
            rawy = pd.to_numeric(g.year_raw, errors="coerce").values.astype(float)
            need = (g.heap.fillna(False).astype(bool).values | ~np.isfinite(rawy)) & np.isfinite(yi)
            for col in ("year_hist", "year_hist_ca"):
                if col not in g:
                    g[col] = np.nan
            free = need & ~np.isfinite(pd.to_numeric(g.year_hist, errors="coerce").values.astype(float))
            g["year_hist"] = np.where(free & ~ca, yi, pd.to_numeric(g.year_hist, errors="coerce"))
            g["year_hist_ca"] = np.where(free & ca, yi, pd.to_numeric(g.year_hist_ca, errors="coerce"))
            log(f"counties: {f.name}: the state inventory dates {int((free & ~ca).sum())} footprints with a placeholder or no "
                f"assessor year, and {int((free & ca).sum())} more with a 'circa' year")
        if len(g):
            parts.append(g.to_crs(4326))
            log(f"counties: {f.name}: {len(g)} footprints")
    if not parts:
        return None
    g = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), geometry="geometry", crs=4326)
    g = g.explode(index_parts=False)
    g = g[g.geometry.geom_type == "Polygon"].reset_index(drop=True)
    g["area"] = g.geometry.to_crs(UTM).area.values
    # (outbuildings under 25 m2 — sheds — are not drawn in the counties: the site must stay small;
    # in the outer tier nothing under OUTER_MIN_M2: garages go too)
    return g[g["area"] > (OUTER_MIN_M2 if outer else 25)].reset_index(drop=True)


def recorded_evidence():
    """(outlines EPSG:4326, years, strong) of the county buildings with a recorded year of
    their own: evidence that their ground existed (ground_rule.write_evidence). A state
    inventory year is strong; a parcel year (not a placeholder, the lot's main building) weak."""
    g = load()
    if g is None:
        return np.zeros(0, dtype=object), np.zeros(0), np.zeros(0, bool)
    n = len(g)
    county = g.county.astype(str).values
    raw = pd.to_numeric(g.year_raw, errors="coerce").values.astype(float)
    raw = np.where((raw >= YEAR_MIN) & (raw <= NOW + 1), raw, np.nan)
    heap = g.heap.fillna(False).astype(bool).values.copy() if "heap" in g else np.zeros(n, bool)
    for c, hs in county_heaps(raw, county).items():
        heap |= (county == c) & np.isin(raw, list(hs))
    secondary = g.secondary.fillna(False).astype(bool).values if "secondary" in g else np.zeros(n, bool)
    hist = pd.to_numeric(g.year_hist, errors="coerce").values.astype(float) if "year_hist" in g else np.full(n, np.nan)
    hist_ok = np.isfinite(hist) & (hist >= YEAR_MIN) & (hist <= NOW)
    year = np.where(hist_ok, hist, np.where(heap | secondary, np.nan, raw))
    ok = np.isfinite(year)
    return g.geometry.values[ok], year[ok], hist_ok[ok]


def researched(g):
    """(year, is an estimate) per footprint from the researched tables' rows without a BIN."""
    import shapely
    from common import TABLES
    year = np.full(len(g), np.nan)
    est = np.zeros(len(g), bool)
    rows = []
    for p in sorted(TABLES.glob("known_building_dates*.csv")):
        if p.name.endswith(".records.csv"):
            continue
        t = pd.read_csv(p)
        if "bin" in t:
            t = t[pd.to_numeric(t["bin"], errors="coerce").fillna(0) == 0]
        t = t[pd.to_numeric(t.start_year, errors="coerce").notna() & pd.to_numeric(t.lon, errors="coerce").notna()
              & ~t.id.astype(str).str.startswith("site_floor:")]
        if len(t):
            rows.append(t)
    if not rows:
        return year, est
    t = pd.concat(rows, ignore_index=True)
    b = g.total_bounds
    t = t[(t.lon.astype(float) >= b[0]) & (t.lon.astype(float) <= b[2]) & (t.lat.astype(float) >= b[1]) & (t.lat.astype(float) <= b[3])]
    if not len(t):
        return year, est
    qi, gi = shapely.STRtree(g.geometry.values).query(shapely.points(t.lon.values.astype(float), t.lat.values.astype(float)), predicate="within")
    year[gi] = t.start_year.values.astype(float)[qi]
    est[gi] = t.note.astype(str).str.lower().str.contains("estimate").values[qi] if "note" in t else False
    log(f"counties: {len(np.unique(gi))} footprints dated by researched rows ({len(t) - len(np.unique(qi))} of {len(t)} rows in the area matched none)")
    return year, est


def compact(geoms_utm, area):
    """The outer tier's outlines: a house-sized outline that fills its bounding rectangle becomes
    that rectangle, shrunk about its centre to the outline's own area; the rest is simplified."""
    import shapely
    mrr = shapely.minimum_rotated_rectangle(geoms_utm)
    ok = np.array([q is not None and q.geom_type == "Polygon" for q in mrr], bool)
    ma = np.where(ok, shapely.area(mrr), np.inf)
    rect = ok & (area < RECT_MAX_M2) & (area >= RECT_FILL * ma)
    out = shapely.simplify(geoms_utm, OUTER_SIMPLIFY_M, preserve_topology=True)
    if rect.any():
        c = shapely.get_coordinates(mrr[rect]).reshape(-1, 5, 2)
        mid = c[:, :4].mean(axis=1, keepdims=True)
        k = np.sqrt(area[rect] / ma[rect])[:, None, None]
        out[rect] = shapely.polygons(mid + (c - mid) * k)
    return out, rect


def build(g, outer=False):
    """Years, heights, materials and ground of the footprints `g` -> the rows of the map."""
    n = len(g)
    xyp = g.geometry.to_crs(UTM).representative_point()
    xy = np.column_stack([xyp.x.values, xyp.y.values])
    county = g.county.astype(str).values
    keys = g["id"].astype(str).values
    raw = pd.to_numeric(g.year_raw, errors="coerce").values.astype(float)
    raw = np.where((raw >= YEAR_MIN) & (raw <= NOW + 1), raw, np.nan)
    heap = g.heap.fillna(False).astype(bool).values.copy() if "heap" in g else np.zeros(n, bool)
    found = county_heaps(raw, county)
    for c, hs in found.items():
        heap |= (county == c) & np.isin(raw, list(hs))
    log("counties: heap years " + "; ".join(f"{c} {sorted(int(v) for v in hs)}" for c, hs in found.items()))
    # (a pile at 1700 or 1750 is not "about 1700": it is "old, year unknown". As a bound it put
    # 240 houses of Hudson County in the 1670s-90s; it is read as "built by 1800")
    raw = np.where(heap & (raw < 1790), 1800.0, raw)
    secondary = g.secondary.fillna(False).astype(bool).values if "secondary" in g else np.zeros(n, bool)
    year = np.where(heap, np.nan, raw)
    src = np.where(np.isfinite(year), np.where(secondary, "parcel_secondary", "parcel"), "").astype(object)
    hist = pd.to_numeric(g.year_hist, errors="coerce").values.astype(float) if "year_hist" in g else np.full(n, np.nan)
    hist_ok = np.isfinite(hist) & (hist >= YEAR_MIN) & (hist <= NOW)
    year = np.where(hist_ok, hist, year)
    src = np.where(hist_ok, "historic_register", src).astype(object)
    # researched rows (data/tables/known_building_dates*.csv without a BIN: campuses and civic
    # buildings outside the city): the footprint the row's point lies in takes its year
    ky, kest = researched(g)
    kn = np.isfinite(ky)
    year = np.where(kn, ky, year)
    src = np.where(kn, np.where(kest, "known_est", "known"), src).astype(object)
    hist_ok = hist_ok | kn
    # an inventory's approximate year ("circa 1900", a round decade): better than the assessor's
    # placeholder, not a record. Spread over six years so that it is not a heap of its own.
    hca = pd.to_numeric(g.year_hist_ca, errors="coerce").values.astype(float) if "year_hist_ca" in g else np.full(n, np.nan)
    ca_ok = np.isfinite(hca) & ~np.isfinite(year) & (hca >= YEAR_MIN) & (hca <= NOW)
    if ca_ok.any():
        jit = np.array([h01(f"ca{k}") for k in np.asarray(keys)[ca_ok]]) * 6.0 - 3.0
        year = year.copy()
        year[ca_ok] = hca[ca_ok] + jit
        src = np.where(ca_ok, "historic_register_ca", src).astype(object)
        log(f"counties: {int(ca_ok.sum())} footprints take an inventory's approximate ('circa') year")
    # heights
    H = pd.to_numeric(g.height_m, errors="coerce").values.astype(float)
    floors = pd.to_numeric(g.floors, errors="coerce").values.astype(float) if "floors" in g else np.full(n, np.nan)
    use = pd.to_numeric(g.use, errors="coerce").fillna(0).values.astype(np.uint8) if "use" in g else np.zeros(n, np.uint8)
    area = g["area"].values
    guess = np.where(use == 1, 7.0, np.where(area < 60, 3.5, np.where(use == 5, 8.0, np.where(area > 1500, 9.0, 7.5))))
    measured = np.isfinite(H) & (H > 1.5)
    H = np.where(measured, H, np.where(floors > 0, floors * 3.3 + 1.5, guess))
    # only the lot's main building is evidence for its neighbours
    rec_for_nb = np.where(secondary, np.nan, year)
    est, src2 = fill_estimates(xy, rec_for_nb, raw, heap | secondary, H, keys, src.copy())
    year = np.where(np.isfinite(year), year, est)
    src = np.where(src == "", src2, src).astype(object)
    # no year on the roll at all: the modelled estimate beats "like the nearest recorded building"
    if "year_est" in g:
        ye = pd.to_numeric(g.year_est, errors="coerce").values.astype(float)
        use_est = np.isfinite(ye) & ~np.isfinite(raw) & ~hist_ok
        year = np.where(use_est, ye, year)
        # (two kinds of estimate: the census's homes by decade per block group, and - where the
        # assessor's own records were counted per 250 m cell and five-year step, HISDAC-US - that
        # cell's curve: county_years.py, about twice as close)
        basis = g.est_basis.fillna("").astype(str).values if "est_basis" in g else np.full(n, "", dtype=object)
        cells = np.array([b.startswith("hisdac_bupr") for b in basis])
        src = np.where(use_est, np.where(cells, "modelled_cells", "modelled"), src).astype(object)
        # The census has one open bin "1939 or earlier", and the estimator spreads it along the
        # town's population curve — which ignores that old houses were pulled down (it had
        # 3,000 of today's Westchester buildings standing before 1800). Each building keeps its
        # rank; the ages follow the county's RECORDED pre-1940 buildings.
        for c in np.unique(county[use_est]):
            m = use_est & (county == c) & (year < 1940)
            ref = np.sort(year[(county == c) & (src == "parcel") & (year < 1940)])
            if m.sum() > 50 and len(ref) > 500:
                rk = (pd.Series(year[m]).rank(method="first").values - 0.5) / m.sum()
                year[m] = np.quantile(ref, rk)
        log(f"counties: {int(use_est.sum())} footprints without a roll year take the modelled estimate")
    # bound-type placeholders along each town's census curve (by_town_growth)
    bb0 = g.geometry.bounds
    year, grown = by_town_growth(((bb0.minx + bb0.maxx) / 2).values, ((bb0.miny + bb0.maxy) / 2).values, year, src, raw)
    if grown:
        log(f"counties: {grown} 'built by' placeholder years follow their town's census growth")
    # standing on a traced atlas: built by its year (on_atlas). Not for a recorded year.
    if np.isin(county, ["Hudson"]).any():
        hud = np.flatnonzero(county == "Hudson")
        my = np.full(n, np.nan)
        my[hud] = on_atlas(g.geometry.to_crs(UTM).values[hud])
        late = np.isfinite(my) & ~np.isin(src, ["parcel", "historic_register", "known"]) & (year > my)
        if late.any():
            year = year.copy()
            year[late] = my[late] - 2.0 - 22.0 * np.array([h01(f"am{k}") for k in np.asarray(keys)[late]])
            src = np.where(late, "on_map", src).astype(object)
            log(f"counties: {int(late.sum())} Hudson County buildings with an estimated year stand on a traced atlas: dated to before it")
    # the order of building-out follows the dated maps (order_by_maps)
    bb = g.geometry.bounds
    year, moved = order_by_maps(((bb.minx + bb.maxx) / 2).values, ((bb.miny + bb.maxy) / 2).values, xy, year, src, raw)
    if moved:
        log(f"counties: {moved} estimated years dealt out again in the order the dated maps show the ground built up")
    year = np.clip(year, YEAR_MIN, 2029.0)
    conf = np.where(np.isin(src, ["parcel", "historic_register", "known"]), "exact", "estimated").astype(object)
    log(f"counties: {n} footprints: {pd.Series(src).str.split(':').str[0].value_counts().to_dict()}")
    start = row_timing(xy, year, keys)
    start0 = start
    start = land_check(g.geometry.values, start, src, H, keys)
    conf = np.where(start > start0 + 0.05, "estimated", conf).astype(object)   # waits for its ground: no longer the record's year
    start = np.minimum(start, 2029.9)
    stories = np.where(floors > 0, floors, np.maximum(1, np.round(H / 3.4)))
    cls = np.array([USE_CLASS.get(int(u), "") for u in use], dtype=object)
    # (one material per 250 m cell, use and decade: a subdivision is one colour)
    grp = (np.floor(xy[:, 0] / 250).astype(int).astype(str) + "_" + np.floor(xy[:, 1] / 250).astype(int).astype(str)
           + "|" + use.astype(str) + "|" + (np.floor(start / 10) * 10).astype(int).astype(str))
    mat, roof = materials(start, H, area, use, np.full(n, "9", dtype=object), cls, np.full(n, np.nan),
                          np.zeros(n, int), np.full(n, "", dtype=object), group=grp)
    ground = Ground()
    gmin, gmean = ring_ground(ground, g.geometry.values)
    names = g["name"].values if "name" in g else np.full(n, None, dtype=object)
    out = gpd.GeoDataFrame({"start_year": start, "end_year": 9999.0, "height": H + (gmean - gmin) + 1.0, "base": gmin - 1.0,
                            "year_confidence": conf, "use": use, "raw_year": np.nan_to_num(raw), "stories": stories,
                            "mat": mat, "roof": roof, "fid_key": keys, "year_src": src, "name": names, "county": county,
                            "height_m": H, "area": area, "start_free": np.minimum(start0, start)}, geometry=g.geometry.values, crs=4326)
    if outer:
        gm, rect = compact(out.geometry.to_crs(UTM).values, area)
        out["geometry"] = gpd.GeoSeries(gm, crs=UTM).to_crs(4326).values
        log(f"counties: {int(rect.sum())} of {n} outlines stored as rectangles")
    else:
        out["geometry"] = out.geometry.to_crs(UTM).simplify(0.6, preserve_topology=True).to_crs(4326)
    out = out[~out.geometry.is_empty & out.geometry.is_valid & (out.geometry.geom_type == "Polygon")]
    return out, measured


def points_of(out):
    rp = out.geometry.representative_point()
    return pd.DataFrame({"lon": rp.x.values, "lat": rp.y.values, "start_year": out.start_year.values, "end_year": out.end_year.values,
                         "area_m2": out["area"].values, "height": out.height.values, "boro": "9", "county": out.county.values,
                         "conf": out.year_confidence.values, "start_free": out.start_free.values})


def merge_points():
    """county_building_points.parquet (terrain, roads, ground detail) = the inner counties' points
    and the outer tier's, whichever run wrote last."""
    parts = [pd.read_parquet(f) for f in (INTERIM / "county_points_inner.parquet", INTERIM / "county_points_outer.parquet") if f.exists()]
    if parts:
        pd.concat(parts, ignore_index=True).to_parquet(INTERIM / "county_building_points.parquet")


def main_outer():
    """The outer tier: one county file at a time (Suffolk alone is 600,000 footprints)."""
    files = county_files(outer=True)
    if os.environ.get("FILES"):          # test run: only these stems (comma-separated)
        files = [f for f in files if f.stem in os.environ["FILES"].split(",")]
    outs, pts = [], []
    for f in files:
        g = load([f], outer=True)
        if g is None or not len(g):
            continue
        out, _ = build(g, outer=True)
        pts.append(points_of(out))
        outs.append(out[COLS + ["year_src", "name", "county"]])
        del g, out
    if not outs:
        log("counties: no outer county files yet (data/interim/counties)")
        return
    out = gpd.GeoDataFrame(pd.concat(outs, ignore_index=True), geometry="geometry", crs=4326)
    pd.concat(pts, ignore_index=True).to_parquet(INTERIM / "county_points_outer.parquet")
    merge_points()
    write_tile_set(out[COLS + ["year_src", "name"]], OUT_OUTER, compact=True)
    size = sum(q.stat().st_size for q in OUT_OUTER.rglob("*.bin.gz")) / 1e6
    y = np.floor(out.start_year.values).astype(int)
    summary = {"buildings": int(len(out)), "by_county": out.county.value_counts().to_dict(),
               "confidence": out.year_confidence.value_counts().to_dict(),
               "source": pd.Series(out.year_src.values).str.split(":").str[0].value_counts().to_dict(),
               "tile_set_mb": round(size, 1), "bytes_per_building": round(size * 1e6 / max(len(out), 1), 1),
               "per_decade": {str(int(d)): int(c) for d, c in zip(*np.unique(y // 10 * 10, return_counts=True))}}
    p = INTERIM / "reports" / "outer_buildings_summary.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(summary, indent=1))
    log(f"counties (outer): {summary['buildings']} buildings {summary['by_county']}; {size:.0f} MB, "
        f"{summary['bytes_per_building']} bytes per building; confidence {summary['confidence']}")


def main():
    import sys
    if "outer" in sys.argv[1:]:
        return main_outer()
    g = load()
    if g is None:
        log("counties: no county files (data/interim/counties) or none on the map yet - nothing to build")
        return
    out, measured = build(g)
    points_of(out).to_parquet(INTERIM / "county_points_inner.parquet")
    merge_points()
    out.to_parquet(INTERIM / "county_buildings.parquet")
    write_tile_set(out[COLS + ["year_src", "name"]], OUT)
    y = np.floor(out.start_year.values).astype(int)
    summary = {"buildings": int(len(out)), "by_county": out.county.value_counts().to_dict(),
               "confidence": out.year_confidence.value_counts().to_dict(),
               "source": pd.Series(out.year_src.values).str.split(":").str[0].value_counts().to_dict(),
               "measured_height_share": round(float(measured.mean()), 3),
               "per_decade": {str(int(d)): int(c) for d, c in zip(*np.unique(y // 10 * 10, return_counts=True))}}
    p = INTERIM / "reports" / "county_buildings_summary.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(summary, indent=1))
    log(f"counties: {summary['buildings']} buildings {summary['by_county']}; confidence {summary['confidence']}; "
        f"measured heights {summary['measured_height_share']:.0%}")


if __name__ == "__main__":
    main()
