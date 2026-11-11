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


def county_files(outer=False):
    files = (sorted(SRC.glob("n[jy]_*.parquet")) + sorted(SRC.glob("ct_*.parquet")) + sorted(SRC.glob("pa_*.parquet"))) if SRC.exists() else []
    files = [f for f in files if not f.stem.endswith("_estimates")]   # (read beside their county's file, below)
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
    for c, hs in find_heaps(raw, county).items():
        heap |= (county == c) & np.isin(raw, list(hs))
    secondary = g.secondary.fillna(False).astype(bool).values if "secondary" in g else np.zeros(n, bool)
    hist = pd.to_numeric(g.year_hist, errors="coerce").values.astype(float) if "year_hist" in g else np.full(n, np.nan)
    hist_ok = np.isfinite(hist) & (hist >= YEAR_MIN) & (hist <= NOW)
    year = np.where(hist_ok, hist, np.where(heap | secondary, np.nan, raw))
    ok = np.isfinite(year)
    return g.geometry.values[ok], year[ok], hist_ok[ok]


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
    found = find_heaps(raw, county)
    for c, hs in found.items():
        heap |= (county == c) & np.isin(raw, list(hs))
    log("counties: heap years " + "; ".join(f"{c} {sorted(int(v) for v in hs)}" for c, hs in found.items()))
    secondary = g.secondary.fillna(False).astype(bool).values if "secondary" in g else np.zeros(n, bool)
    year = np.where(heap, np.nan, raw)
    src = np.where(np.isfinite(year), np.where(secondary, "parcel_secondary", "parcel"), "").astype(object)
    hist = pd.to_numeric(g.year_hist, errors="coerce").values.astype(float) if "year_hist" in g else np.full(n, np.nan)
    hist_ok = np.isfinite(hist) & (hist >= YEAR_MIN) & (hist <= NOW)
    year = np.where(hist_ok, hist, year)
    src = np.where(hist_ok, "historic_register", src).astype(object)
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
        src = np.where(use_est, "modelled", src).astype(object)
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
    year = np.clip(year, YEAR_MIN, 2029.0)
    conf = np.where(np.isin(src, ["parcel", "historic_register"]), "exact", "estimated").astype(object)
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
