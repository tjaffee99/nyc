"""Stage: the buildings of the five boroughs.

  * footprints: the city's Building Footprints (NYC OTI; photogrammetric outlines, +/- 2 ft)
    with the measured roof height above ground (footprints_raw.py)
  * construction year, best evidence first (CLAUDE.md "evidence order"):
      researched rows (data/tables/known_building_dates.csv, by BIN or point)
      > the Landmarks Preservation Commission's building database (date range per building)
      > the year on the footprint / the tax lot (Department of Finance via OTI and PLUTO)
      > neighbours.
    The assessor's years are mostly estimates before about 1975: 80 % sit on 1899, 1900,
    1901, 1910, 1915, 1920 ... ("heaps"). A heap year is detected per borough (count more
    than 3x its non-round neighbours) and is NOT a record:
      - a heap up to 1901 means "by then": the building takes the median of the recorded
        years around it (<= 150 m) that respect the bound, else a spread over the 25 years
        before the heap;
      - a later heap means "about then": the building takes the median of recorded years
        around it inside heap +/- 5 years, else a place in heap +/- 2.5 years, one date per
        ~80 m block so a block fills together.
    Either way the result is `estimated`. Years that are not heaps are `exact`.
  * nothing stands before its ground (land-year grid from land.py, when present)
  * OpenStreetMap's hand-modelled 3D building parts (via Overture) replace the flat
    extrusion of a footprint where they agree with the measured roof height
  * use from the tax lot's building class; facade material by era, class, attachment and
    borough (LPC's recorded primary material where the building is in its database)

Outputs:
  viewer/public/data/core-buildings.bin.gz          Manhattan, one file (always loaded)
  viewer/public/data/region-buildings/13/x/y.bin.gz the other boroughs, z13 tiles
  viewer/public/data/region-buildings/11/x/y.bin.gz large / tall buildings for zoomed-out views
  data/interim/nyc_buildings.parquet                everything, for later stages
  data/interim/nyc_building_points.parquet          lon, lat, start, end, area, height (terrain, roads)
  data/interim/reports/nyc_buildings_summary.json
"""
from __future__ import annotations

import json
import math
import os
import zlib

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from scipy.spatial import cKDTree

from building_binary import (CONF, M_BRICK, M_BROWNSTONE, M_CIVIC, M_CONTEMP, M_DUTCH, M_EARLY, M_FRAME, M_GLASS,
                             M_INDUSTRIAL, M_MASONRY, M_MIDCENTURY, M_STUCCO, M_TOWER70, M_WHITEBRICK, R_FLAT, R_SHINGLE,
                             R_TILE, USE_CATEGORIES, write_buildings)
from common import BOROUGHS, INTERIM, NYC_CRS, OVERTURE_RELEASE, RAW, TABLES, VIEWER_DATA, YEAR_MIN, log

UTM = NYC_CRS
TILE_Z = 13
LOW_Z = 11
OUT = VIEWER_DATA / "region-buildings"
CORE = VIEWER_DATA / "core-buildings.bin.gz"
CORE_BORO = "1"  # Manhattan ships as one file
NOW = 2026.5
# feature codes kept (metadata: 1003 = placeholder triangle, 1005 = temporary structure)
KEEP_CODES = {2100, 5110, 5100, 1000, 1001, 1002, 1004, 1006, 2110}
COLS = ["start_year", "end_year", "height", "base", "year_confidence", "use", "raw_year", "stories", "mat", "roof",
        "fid_key", "geometry"]


def h01(key: str) -> float:
    return (zlib.crc32(key.encode()) % 100003) / 100003.0


def tile_of(lon, lat, z=TILE_Z):
    n = 2 ** z
    x = np.floor((lon + 180) / 360 * n).astype(int)
    lr = np.radians(lat)
    y = np.floor((1 - np.log(np.tan(lr) + 1 / np.cos(lr)) / math.pi) / 2 * n).astype(int)
    return x, y


def tile_origin(x, y, z=TILE_Z):
    n = 2 ** z
    lon = x / n * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lon, lat


# ------------------------------------------------------------------ inputs
def load_footprints():
    t = pd.read_parquet(INTERIM / "nyc_footprints_raw.parquet")
    g = gpd.GeoDataFrame(t.drop(columns=["geometry"]), geometry=shapely.from_wkb(t.geometry.values), crs=4326)
    del t
    g = g[g.feature_code.isin(list(KEEP_CODES)) & ~g.status.fillna("").isin(["Demolition"])]
    g["doitt_id"] = g.doitt_id.astype(str)
    g["boro"] = g.bin.astype("Int64").astype(str).str[0]
    bb = g.base_bbl.fillna("").astype(str).str[0]
    g.loc[~g.boro.isin(list(BOROUGHS)), "boro"] = bb[~g.boro.isin(list(BOROUGHS))]
    only = os.environ.get("NYC_BORO")  # e.g. NYC_BORO=1 for a test run of Manhattan
    if only:
        g = g[g.boro == only]
    g = g.explode(index_parts=False)
    g = g[g.geometry.geom_type == "Polygon"].reset_index(drop=True)
    g["area"] = g.geometry.to_crs(UTM).area.values
    g = g[g["area"] > 12].reset_index(drop=True)
    log(f"buildings: {len(g)} footprints ({g.boro.map(BOROUGHS).value_counts().to_dict()})")
    return g


def load_pluto():
    p = RAW / "nyc" / "pluto_lots.csv"
    if not p.exists():
        p = RAW / "nyc" / "pluto.csv"
    t = pd.read_csv(p, dtype=str)
    t["bbl"] = t.bbl.str.split(".").str[0]
    for c in ("yearbuilt", "numfloors", "numbldgs", "yearalter1", "yearalter2", "proxcode", "lotfront", "bldgfront"):
        if c in t:
            t[c] = pd.to_numeric(t[c], errors="coerce")
    return t.drop_duplicates("bbl").set_index("bbl")


def load_lpc():
    """LPC building database: BIN -> (year, exact?, primary material, name)."""
    p = RAW / "nyc" / "lpc_buildings.geojson"
    if not p.exists():
        return pd.DataFrame(columns=["bin", "year", "exact", "mat_prim"]).set_index("bin")
    t = gpd.read_file(p, ignore_geometry=True)
    lo = pd.to_numeric(t.date_low, errors="coerce").fillna(0)
    hi = pd.to_numeric(t.date_high, errors="coerce").fillna(0)
    hi = np.where(hi > 0, hi, lo)
    lo = np.where(lo > 0, lo, hi)
    ok = (hi >= YEAR_MIN) & (hi <= NOW) & (lo >= YEAR_MIN - 10)
    span = hi - lo
    year = np.where(span <= 5, hi, (lo + hi) / 2.0)
    circa = pd.to_numeric(t.circa, errors="coerce").fillna(0).values > 0
    nm = t.build_nme.fillna("").astype(str).str.strip() if "build_nme" in t else pd.Series("", index=t.index)
    out = pd.DataFrame({"bin": pd.to_numeric(t.bin, errors="coerce"), "year": year, "exact": (span <= 2) & ~circa,
                        "mat_prim": t.mat_prim.fillna("").astype(str), "area": pd.to_numeric(t.shape_area, errors="coerce"),
                        "lpc_name": nm.where(~nm.isin(["0", ""]), None)})
    out = out[ok & out.bin.notna() & (out.bin % 1000000 != 0)]
    # several rows per BIN (a house and its garage share one): the largest outline is the building
    out = out.sort_values("area").drop_duplicates("bin", keep="last").set_index("bin")
    return out


# ------------------------------------------------------------------ years
def find_heaps(year, boro):
    """Placeholder years per borough: a count more than 3x the median of the non-round,
    not-yet-flagged years within +/- 4 (and at least 300 buildings)."""
    heaps = {}
    for b in np.unique(boro):
        y = year[(boro == b) & np.isfinite(year)].astype(int)
        cnt = dict(zip(*np.unique(y, return_counts=True)))
        flagged: set[int] = set()
        for rnd in (True, False, False):
            for v in sorted(cnt):
                if v > 1990 or v in flagged or (v % 5 == 0) != rnd or cnt[v] < 300:
                    continue
                nb = [cnt.get(u, 0) for u in range(v - 4, v + 5) if u != v and u % 5 and u not in flagged]
                if nb and cnt[v] > 3 * max(float(np.median(nb)), 1.0):
                    flagged.add(v)
        heaps[b] = flagged
    return heaps


def height_floor(H):
    """Earliest plausible year by height: passenger elevators (1870), steel frames (1889)."""
    return np.where(H >= 80, 1895.0, np.where(H >= 40, 1889.0, np.where(H >= 25, 1870.0, -np.inf)))


def assign_years(g, pluto, lpc):
    n = len(g)
    xyp = g.geometry.to_crs(UTM).representative_point()
    xy = np.column_stack([xyp.x.values, xyp.y.values])
    boro = g.boro.values
    H = g.height_m.fillna(0).values.astype(float)
    raw = pd.to_numeric(g.year_raw, errors="coerce").values.astype(float)
    py = pluto.yearbuilt.reindex(g.pluto_bbl.fillna("").astype(str).values).values.astype(float)
    raw = np.where((raw > 0) & np.isfinite(raw), raw, py)
    raw = np.where((raw >= YEAR_MIN) & (raw <= NOW + 1), raw, np.nan)
    heaps = find_heaps(raw, boro)
    log("buildings: heap years " + "; ".join(f"{BOROUGHS[b]} {sorted(v)}" for b, v in heaps.items()))
    is_heap = np.zeros(n, bool)
    for b, hs in heaps.items():
        is_heap |= (boro == b) & np.isin(raw, list(hs))
    year = np.where(is_heap, np.nan, raw)
    conf = np.where(np.isfinite(year), "exact", "estimated").astype(object)
    src = np.where(np.isfinite(year), "assessor", "").astype(object)
    # LPC building database
    lp = lpc.reindex(g.bin.astype("float64").values)
    ly = lp.year.values.astype(float)
    has = np.isfinite(ly)
    year[has] = ly[has]
    conf[has] = np.where(lp.exact.values[has].astype(bool), "exact", "estimated")
    src[has] = "lpc"
    log(f"buildings: {int(has.sum())} footprints dated by the LPC building database, "
        f"{int((src == 'assessor').sum())} by a recorded assessor year, {int(is_heap.sum())} on heap years, "
        f"{int((~np.isfinite(raw)).sum())} without any year")
    # researched rows
    year, conf, src, end = known_dates(g, year, conf, src)
    recorded = np.isfinite(year)
    tree = cKDTree(xy[recorded])
    ry = year[recorded]
    floor = height_floor(H)
    hb = np.array([h01(f"b{int(a)}_{int(b_)}") for a, b_ in zip(np.floor(xy[:, 0] / 80), np.floor(xy[:, 1] / 80))])
    hl = np.array([h01(f"l{k}") for k in g.doitt_id.values])

    def neighbours(idx, k, radius, lo, hi):
        """Median of the recorded years within radius that lie in [lo, hi]; NaN if < 2."""
        d, j = tree.query(xy[idx], k=k, distance_upper_bound=radius)
        v = np.where(np.isfinite(d), ry[np.minimum(j, len(ry) - 1)], np.nan)
        v = np.where((v >= lo[:, None]) & (v <= hi[:, None]), v, np.nan)
        cnt = np.isfinite(v).sum(axis=1)
        with np.errstate(all="ignore"):
            med = np.nanmedian(v, axis=1)
        return np.where(cnt >= 2, med, np.nan)

    # heaps up to 1901: "by then"
    early = np.nonzero(is_heap & ~recorded & (raw <= 1901))[0]
    if len(early):
        up = raw[early] + 1.0
        lo = np.maximum(floor[early], YEAR_MIN)
        med = neighbours(early, 12, 150.0, lo, up)
        spread = raw[early] - 25.0 * (1 - np.sqrt((hb[early] + 0.3 * hl[early]) % 1.0))
        year[early] = np.maximum(np.where(np.isfinite(med), med + (hl[early] - 0.5) * 5.0, spread), lo)
        year[early] = np.minimum(year[early], up)
        src[early] = np.where(np.isfinite(med), "heap_by+neighbours", "heap_by+spread")
    # later heaps: "about then"
    late = np.nonzero(is_heap & ~recorded & (raw > 1901))[0]
    if len(late):
        v = raw[late]
        med = neighbours(late, 8, 100.0, v - 5.0, v + 5.0)
        w0, w1 = v - 2.5, v + 2.5
        # hardly anything was built from mid-1942 to 1945 (war-time building limits)
        w1 = np.where(v == 1940, 1942.4, w1)
        w0 = np.where(v == 1945, 1945.6, w0)
        w1 = np.where(v == 1945, 1948.5, w1)
        # (uniform over the window; the buildings of an ~80 m block land close together)
        spread = w0 + (w1 - w0) * ((hb[late] + 0.3 * hl[late]) % 1.0)
        # (around the local median, +/- 2.5 years: the median alone stacks a district on one year)
        year[late] = np.where(np.isfinite(med), np.clip(med + (hl[late] - 0.5) * 5.0, v - 5.0, v + 5.0), spread)
        year[late] = np.maximum(year[late], floor[late])
        src[late] = np.where(np.isfinite(med), "heap_about+neighbours", "heap_about+spread")
    # no year at all: recorded neighbours of a comparable size (a tower is not dated from the houses around it)
    miss = np.nonzero(~np.isfinite(year))[0]
    if len(miss):
        tall = H[miss] >= 20
        est = np.full(len(miss), np.nan)
        lo = np.maximum(floor[miss], YEAR_MIN)
        hi = np.full(len(miss), NOW)
        est[~tall] = neighbours(miss[~tall], 12, 200.0, lo[~tall], hi[~tall])
        if tall.any():
            big = recorded & (H >= 20)
            if big.sum() > 50:
                t2 = cKDTree(xy[big])
                y2 = year[big]
                d, j = t2.query(xy[miss[tall]], k=8, distance_upper_bound=400.0)
                v = np.where(np.isfinite(d), y2[np.minimum(j, len(y2) - 1)], np.nan)
                v = np.where(v >= lo[tall][:, None], v, np.nan)
                with np.errstate(all="ignore"):
                    est[tall] = np.nanmedian(v, axis=1)
        d1, j1 = tree.query(xy[miss], k=1)
        est = np.where(np.isfinite(est), est, np.maximum(ry[j1], lo))
        year[miss] = est + (hl[miss] - 0.5)
        src[miss] = "neighbours"
    # under construction today
    uc = (g.feature_code.values == 5100) & (src != "known")
    year[uc] = np.maximum(year[uc], 2027.0 + hl[uc])
    conf[uc] = "estimated"
    year = np.clip(year, YEAR_MIN, 2029.0)
    return year, np.nan_to_num(raw), conf, end, src, xy


def known_dates(g, year, conf, src):
    """data/tables/known_building_dates.csv: id,name,lat,lon,bin,start_year,end_year,source_url,note —
    researched years for buildings the roll misdates (exempt and institutional property, landmarks
    outside the LPC database). A row applies to the footprint with its BIN, else the one its point is in."""
    end = np.full(len(g), 9999.0)
    p = TABLES / "known_building_dates.csv"
    if not p.exists():
        return year, conf, src, end
    t = pd.read_csv(p)
    by_bin = {int(b): i for i, b in enumerate(g.bin.fillna(0).astype("int64").values) if b % 1000000}
    tree = shapely.STRtree(g.geometry.values)
    hits = 0
    for r in t.itertuples():
        idx = []
        if "bin" in t and pd.notna(getattr(r, "bin", np.nan)):
            idx = [i for i, b in enumerate(g.bin.fillna(0).astype("int64").values) if b == int(r.bin)]
        if not idx and pd.notna(r.lat) and pd.notna(r.lon):
            idx = list(tree.query(shapely.Point(r.lon, r.lat), predicate="within"))
        for i in idx:
            year[i] = float(r.start_year)
            conf[i] = "estimated" if "estimate" in str(getattr(r, "note", "")).lower() else "exact"
            src[i] = "known"
            if pd.notna(r.end_year) and float(r.end_year) < 9000:
                end[i] = float(r.end_year)
            hits += 1
    log(f"buildings: {hits} footprints dated by {len(t)} researched rows")
    del by_bin
    return year, conf, src, end


def land_check(geoms, start, src, height, keys):
    """Nothing stands before its ground (ground_rule.py): a building starts no earlier than
    the latest land year of any cell under its outline, plus the terrain's blend and its own
    construction time. Researched and LPC dates stand: the terrain takes them as evidence
    that the ground was there (ground_rule.write_evidence)."""
    from ground_rule import earliest_start
    es = earliest_start(geoms, height)
    early = np.isfinite(es) & (start < es)
    fix = early & ~np.isin(src, ["known", "lpc"])
    out = start.copy()
    out[fix] = es[fix] + 1.5 * np.array([h01(f"f{k}") for k in np.asarray(keys)[fix]])
    log(f"buildings: {int(fix.sum())} buildings moved to after their ground was made; "
        f"{int((early & ~fix).sum())} with a landmark / researched year stand on ground the land grid dates later")
    return out


def row_timing(xy, year, keys):
    """Sub-year timing: same-year buildings in an 80 m cell go up in order along their
    principal axis (builders worked down the street); others get a hash."""
    x, y = xy[:, 0], xy[:, 1]
    yi = np.floor(year)
    jit = np.array([h01(f"j{k}") for k in keys])
    cell = np.floor(x / 80).astype(np.int64) * 100003 + np.floor(y / 80).astype(np.int64)
    df = pd.DataFrame({"c": cell, "y": yi, "i": np.arange(len(year))})
    sizes = df.groupby(["c", "y"]).i.transform("size").values
    for (_, _), grp in df[sizes >= 3].groupby(["c", "y"]):
        idx = grp.i.values
        P = np.column_stack([x[idx], y[idx]])
        P = P - P.mean(axis=0)
        _, _, vt = np.linalg.svd(P, full_matrices=False)
        order = np.argsort(np.argsort(P @ vt[0]))
        span = min(0.9, 0.12 * len(idx))
        jit[idx] = (0.5 * (0.9 - span) + span * order / max(len(idx) - 1, 1)) / 0.9
    return yi + 0.9 * jit


# ------------------------------------------------------------------ shape
def apply_parts(g):
    """Replace flat footprint extrusions with OpenStreetMap's hand-modelled building parts
    (set-backs, towers on podiums, crowns) where they exist and agree with the measured roof:
    at least two different part heights, parts covering most of the footprint, and the
    tallest part between 0.85x and 1.3x the measured roof height (OSM heights include
    spires and masts). What the parts do not cover keeps the footprint's own height."""
    d = RAW / "overture" / OVERTURE_RELEASE
    if not (d / "building_part.parquet").exists():
        return g
    parts = gpd.read_parquet(d / "building_part.parquet")
    parts = (parts if parts.crs is not None else parts.set_crs(4326)).to_crs(UTM)
    parts = parts[parts.geometry.geom_type.isin(["Polygon", "MultiPolygon"]) & parts.building_id.notna()]
    gu = g.geometry.to_crs(UTM)
    sidx = gu.sindex
    area = gu.area.values
    Hm = g.height_m.fillna(0).values
    drop, add = set(), []
    n_used = 0
    for bid, ps in parts.groupby("building_id"):
        ph = ps.height.astype(float)
        if ph.notna().sum() < 2 or ph.nunique() < 2:
            continue
        outline = shapely.union_all(ps.geometry.values).buffer(0.3)
        cands = [c for c in sidx.query(outline, predicate="intersects")
                 if c not in drop and gu.iloc[c].intersection(outline).area > 0.5 * area[c]]
        if not cands:
            continue
        donor = max(cands, key=lambda c: area[c])
        roof = max(Hm[c] for c in cands)
        top = float(ph.max())
        if roof <= 0 or not (0.85 * roof <= top <= 1.3 * roof + 15):
            continue
        if outline.area < 0.6 * sum(area[c] for c in cands):
            continue
        row = g.iloc[donor]
        for c in cands:
            rest = gu.iloc[c].difference(outline)
            for piece in getattr(rest, "geoms", [rest]):
                if piece.geom_type == "Polygon" and piece.area > 40 and piece.area > 0.08 * area[c] \
                        and not piece.buffer(-3.0).is_empty:
                    r = g.iloc[c].copy()
                    r["geometry"] = piece
                    r["part_base"] = 0.0
                    add.append(r)
        for p in ps.itertuples():
            if pd.isna(p.height):
                continue
            base = float(p.min_height) if pd.notna(p.min_height) else 0.0
            for piece in getattr(p.geometry, "geoms", [p.geometry]):
                if p.height - base < 0.5 or piece.area < 2:
                    continue
                r = row.copy()
                r["geometry"] = piece
                r["height_m"] = float(p.height - base)
                r["part_base"] = base
                r["doitt_id"] = f"{row.doitt_id}:{p.id[-8:]}"
                add.append(r)
        drop.update(cands)
        n_used += 1
    log(f"buildings: OSM parts used for {n_used} buildings: {len(drop)} footprints -> {len(add)} parts")
    g = g.assign(part_base=0.0)
    if not add:
        return g
    keep = g.drop(g.index[list(drop)])
    extra = gpd.GeoDataFrame(add, geometry="geometry", crs=UTM).to_crs(4326)
    extra["area"] = gpd.GeoSeries([r.geometry for r in add], crs=UTM).area.values
    out = pd.concat([keep, extra], ignore_index=True)
    return gpd.GeoDataFrame(out, geometry="geometry", crs=4326)


def use_codes(cls, code, area):
    """Use from the tax lot's building class (PLUTO bldgclass, first letter)."""
    a = np.array([c[:1] if isinstance(c, str) and c else "" for c in cls])
    use = np.zeros(len(a), np.uint8)
    use[a == "A"] = 1
    use[np.isin(a, ["B", "C", "D", "R", "S"])] = 2
    use[np.isin(a, ["K", "J", "H", "L"])] = 3
    use[a == "O"] = 4
    use[np.isin(a, ["E", "F", "G", "T", "U"])] = 5
    use[np.isin(a, ["M", "W", "P", "Q", "Y", "I", "N"])] = 6
    use[np.isin(a, ["V", "Z"])] = 7
    use[(use == 0) & (area < 300)] = 1
    return use


LPC_MATERIALS = [("brownstone", M_BROWNSTONE), ("brick", M_BRICK), ("wood", M_FRAME), ("clapboard", M_FRAME),
                 ("shingle", M_FRAME), ("limestone", M_MASONRY), ("marble", M_MASONRY), ("granite", M_CIVIC),
                 ("terra", M_MASONRY), ("cast iron", M_MASONRY), ("cast-iron", M_MASONRY), ("stone", M_MASONRY),
                 ("sandstone", M_BROWNSTONE), ("stucco", M_STUCCO), ("concrete", M_MIDCENTURY), ("glass", M_GLASS),
                 ("metal", M_CONTEMP), ("aluminum", M_CONTEMP), ("vinyl", M_STUCCO)]


def materials(year, H, area, use, boro, cls, prox, code, lpc_mat):
    """Facade material and roof by era, class, attachment and borough. Rules of thumb:
    Manhattan's fire limits required masonry south of 14th St from 1815 and island-wide by
    the 1880s, so its row houses and tenements are brick or (c.1845-1900) brownstone-fronted;
    Brooklyn's and the Bronx's attached rows likewise; free-standing houses in Queens, Staten
    Island and the outer wards are frame until the 1920s, brick or frame after; lofts and
    office buildings 1890-1940 are limestone / terra cotta / buff brick; post-war apartment
    slabs white or red brick; towers bronze glass and concrete 1955-85, glass after."""
    n = len(year)
    mat = np.zeros(n, np.uint8)
    roof = np.full(n, R_FLAT, np.uint8)
    a = np.array([c[:1] if isinstance(c, str) and c else "" for c in cls])
    hsh = np.array([h01(f"m{i}") for i in range(n)])
    attached = np.isin(prox, [2, 3]) | (np.isin(boro, ["1"]) & ~np.isin(prox, [1]))
    small_res = np.isin(a, ["A", "B", "S"]) | ((use <= 2) & (area < 260) & (H < 16))
    walkup = np.isin(a, ["C"]) | ((use == 2) & (H < 24))
    garage = code == 5110

    def put(mask, m, r=R_FLAT):
        sel = mask & (mat == 0)
        mat[sel] = m
        roof[sel] = r

    for key, m in LPC_MATERIALS:
        put(np.array([key in s for s in lpc_mat]), m, R_SHINGLE if m == M_FRAME else R_FLAT)
    put(year < 1700, M_DUTCH, R_TILE)
    put((year < 1830) & ~attached, M_EARLY, R_SHINGLE)
    put(year < 1830, M_BRICK, R_SHINGLE)
    put(garage & (year < 1945), M_FRAME, R_SHINGLE)
    put(garage, M_MIDCENTURY, R_FLAT)
    put((use == 6) & (year < 1960) & (H > 10), M_CIVIC, R_FLAT)
    put((use == 5) & (year < 1950), M_BRICK, R_FLAT)
    put(use == 5, M_INDUSTRIAL, R_FLAT)
    # row houses and small flats
    put(small_res & attached & (year >= 1845) & (year < 1900) & (hsh < 0.6), M_BROWNSTONE, R_FLAT)
    put(small_res & attached & (year < 1945), M_BRICK, R_FLAT)
    put(small_res & ~attached & (year < 1925), M_FRAME, R_SHINGLE)
    put(small_res & ~attached & (year < 1945) & (hsh < 0.5), M_BRICK, R_SHINGLE)
    put(small_res & ~attached & (year < 1945), M_FRAME, R_SHINGLE)
    put(small_res & (year < 1975) & (hsh < 0.6), M_BRICK, R_SHINGLE)
    put(small_res & (year < 1975), M_MIDCENTURY, R_SHINGLE)
    put(small_res & attached, M_BRICK, R_FLAT)
    put(small_res, M_STUCCO, R_SHINGLE)
    # tenements, walk-ups, apartment houses
    put(walkup & (year < 1945), M_BRICK, R_FLAT)
    put((use == 2) & (year < 1945) & (H >= 30) & (hsh < 0.6), M_MASONRY, R_FLAT)
    put((use == 2) & (year < 1945), M_BRICK, R_FLAT)
    put((use == 2) & (year < 1975) & (hsh < 0.45), M_WHITEBRICK, R_FLAT)
    put((use == 2) & (year < 1975), M_BRICK, R_FLAT)
    # lofts, stores, offices
    put((use >= 3) & (year < 1890), M_BRICK, R_FLAT)
    put((use >= 3) & (year < 1945) & (H >= 20), M_MASONRY, R_FLAT)
    put((use >= 3) & (year < 1945), M_BRICK, R_FLAT)
    put((year >= 1955) & (year < 1986) & (H >= 40), M_TOWER70, R_FLAT)
    put((year >= 1986) & (H >= 40), M_GLASS, R_FLAT)
    put((year >= 1945) & (year < 1990), M_MIDCENTURY, R_FLAT)
    put(year < 1945, M_BRICK, R_FLAT)
    put(mat == 0, M_CONTEMP, R_FLAT)
    return mat, roof


def ring_ground(ground, geoms):
    """Lowest and mean ground height under each polygon's outer ring."""
    xy, idx = shapely.get_coordinates(shapely.get_exterior_ring(np.asarray(geoms, dtype=object)), return_index=True)
    gz = ground(xy[:, 0], xy[:, 1])
    first = np.flatnonzero(np.r_[True, idx[1:] != idx[:-1]])
    counts = np.diff(np.r_[first, len(idx)])
    return np.minimum.reduceat(gz, first), np.add.reduceat(gz, first) / counts


class Ground:
    """Terrain height (m) at lon / lat from the terrain grids (detail first)."""

    def __init__(self):
        from terrain_grid import grid_def
        self.grids = []
        for name in ("detail", "region"):
            gd = grid_def(name)
            e = np.load(INTERIM / f"grid_{name}_elev.npy")
            self.grids.append((gd, np.where(e < -500, 0, e)))

    def __call__(self, lon, lat):
        lon = np.asarray(lon, float)
        lat = np.asarray(lat, float)
        X = np.radians(lon) * 6378137.0
        Y = 6378137.0 * np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))
        out = np.full(lon.shape, np.nan)
        for gd, e in self.grids:
            c = (X - gd["X0"]) / gd["res"]
            r = (gd["Y0"] - Y) / gd["res"]
            ok = np.isnan(out) & (c >= 0) & (r >= 0) & (c < gd["cols"] - 1) & (r < gd["rows"] - 1)
            c0 = np.floor(c[ok]).astype(int)
            r0 = np.floor(r[ok]).astype(int)
            fx = c[ok] - c0
            fy = r[ok] - r0
            out[ok] = (e[r0, c0] * (1 - fx) + e[r0, c0 + 1] * fx) * (1 - fy) + (e[r0 + 1, c0] * (1 - fx) + e[r0 + 1, c0 + 1] * fx) * fy
        return np.maximum(np.nan_to_num(out), 0.9)


# ------------------------------------------------------------------ main
def build():
    g = load_footprints()
    pluto = load_pluto()
    lpc = load_lpc()
    year, raw, conf, end, src, xy = assign_years(g, pluto, lpc)
    start = row_timing(xy, year, g.doitt_id.values)
    start = np.where(src == "known", year, start)
    start = land_check(g.geometry.values, start, src, g.height_m.fillna(7.0).values.astype(float), g.doitt_id.values)
    start = np.minimum(start, 2029.9)   # under construction today (also when its made land is dated later)
    g = g.assign(start_year=start, end_year=end, year_confidence=conf, raw_year=raw, year_src=src)
    bbl = g.pluto_bbl.fillna("").astype(str).values
    g["bldgclass"] = pluto.bldgclass.reindex(bbl).values
    g["prox"] = pluto.proxcode.reindex(bbl).values if "proxcode" in pluto else np.nan
    floors = pluto.numfloors.reindex(bbl).values.astype(float)
    nb = pluto.numbldgs.reindex(bbl).values.astype(float)
    g["lpc_mat"] = lpc.mat_prim.reindex(g.bin.astype("float64").values).fillna("").str.lower().values
    # names: the footprint's own (few), else the LPC database's building name
    if "lpc_name" in lpc:
        ln = lpc.lpc_name.reindex(g.bin.astype("float64").values).values
        own = g["name"].values
        g["name"] = [a if isinstance(a, str) and a.strip() else (b if isinstance(b, str) else None) for a, b in zip(own, ln)]
    # measured roof height; where missing, floors of the lot, else a storey and a half
    H = g.height_m.fillna(0).values.astype(float)
    H = np.where(H > 1.5, H, np.where(floors > 0, floors * 3.3 + 1.5, np.where(g.feature_code.values == 5110, 3.2, 7.0)))
    g["height_m"] = H
    g["floors"] = np.where((floors > 0) & ~(nb > 1), floors, np.nan)
    g = apply_parts(g)
    H = g.height_m.values.astype(float)
    area = g["area"].values.astype(float)
    stories = np.where(np.isfinite(g.floors.values.astype(float)) & (g.part_base.values == 0), g.floors.values.astype(float),
                       np.maximum(1, np.round((H + g.part_base.values) / 3.4)))
    use = use_codes(g.bldgclass.values, g.feature_code.values, area)
    mat, roof = materials(g.start_year.values, H + g.part_base.values, area, use, g.boro.values, g.bldgclass.values,
                          g.prox.values.astype(float), g.feature_code.values, g.lpc_mat.fillna("").values)
    ground = Ground()
    gmin, gmean = ring_ground(ground, g.geometry.values)
    pb = g.part_base.values.astype(float)
    # foundation at the lowest corner, roof at mean ground + height; floating parts start at their base
    g = g.assign(height=np.where(pb > 0, H, H + (gmean - gmin) + 1.0), base=np.where(pb > 0, gmean + pb, gmin - 1.0),
                 use=use, stories=stories, mat=mat, roof=roof, fid_key=g.doitt_id.astype(str))
    return g


def write_outputs(g):
    full = g
    g = g[COLS + ["boro"] + [c for c in ("year_src", "name") if c in g]].copy()
    g["geometry"] = g.geometry.to_crs(UTM).simplify(0.4, preserve_topology=True).to_crs(4326)
    ok = ~g.geometry.is_empty & g.geometry.is_valid & (g.geometry.geom_type == "Polygon")
    g = g[ok]
    full = full[ok.values]
    rp = g.geometry.representative_point()
    au = g.geometry.to_crs(UTM).area.values
    INTERIM.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"lon": rp.x.values, "lat": rp.y.values, "start_year": g.start_year.values, "end_year": g.end_year.values,
                  "area_m2": au, "height": g.height.values, "boro": g.boro.values,
                  "conf": g.year_confidence.values}).to_parquet(INTERIM / "nyc_building_points.parquet")
    full.drop(columns=[c for c in ("lpc_mat",) if c in full]).to_parquet(INTERIM / "nyc_buildings.parquet")
    # Manhattan: one file
    core = g[g.boro == CORE_BORO]
    if len(core):
        b = core.total_bounds
        raw_b, gz_b = write_buildings(CORE, core, (float(b[0]), float(b[1])), CONF, USE_CATEGORIES)
        log(f"buildings: core file {len(core)} buildings, {gz_b / 1e6:.1f} MB gzip")
    rest = g[g.boro != CORE_BORO]
    tx, ty = tile_of(rp.x.values[(g.boro != CORE_BORO).values], rp.y.values[(g.boro != CORE_BORO).values])
    rest = rest.assign(tx=tx, ty=ty)
    index = []
    for (x, y), t in rest.groupby(["tx", "ty"]):
        path = OUT / str(TILE_Z) / str(x) / f"{y}.bin.gz"
        write_buildings(path, t, tile_origin(x, y), CONF, USE_CATEGORIES)
        index.append({"x": int(x), "y": int(y), "n": int(len(t)), "bbox": [round(float(v), 5) for v in t.total_bounds]})
    # zoomed out: only buildings big enough to see there, outlines simplified to 1.5 m
    ru = rest.geometry.to_crs(UTM)
    big = (ru.area.values > 600) | (rest.height.values - 1.0 > 12)
    low = rest[big].copy()
    low["geometry"] = ru[big].simplify(1.5, preserve_topology=True).to_crs(4326).values
    low = low[~low.geometry.is_empty & low.geometry.is_valid & (low.geometry.geom_type == "Polygon")]
    lp = low.geometry.representative_point()
    lx, ly = tile_of(lp.x.values, lp.y.values, LOW_Z)
    low = low.assign(tx=lx, ty=ly)
    low_index = []
    for (x, y), t in low.groupby(["tx", "ty"]):
        write_buildings(OUT / str(LOW_Z) / str(x) / f"{y}.bin.gz", t, tile_origin(x, y, LOW_Z), CONF, USE_CATEGORIES)
        low_index.append({"x": int(x), "y": int(y), "n": int(len(t))})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.json").write_text(json.dumps({"z": TILE_Z, "tiles": index, "low": {"z": LOW_Z, "tiles": low_index}},
                                               separators=(",", ":")))
    log(f"buildings: {len(index)} tiles with {len(rest)} buildings, {len(low_index)} low-zoom tiles with {len(low)}")
    report(g)


def report(g):
    y = np.floor(g.start_year.values).astype(int)
    vals, counts = np.unique(y, return_counts=True)
    top = sorted(zip(counts.tolist(), vals.tolist()), reverse=True)[:12]
    out = {"buildings": int(len(g)), "by_borough": g.boro.map(BOROUGHS).value_counts().to_dict(),
           "confidence": g.year_confidence.value_counts().to_dict(),
           "busiest_years": [{"year": v, "count": c} for c, v in top],
           "per_decade": {str(int(d)): int(c) for d, c in zip(*np.unique(y // 10 * 10, return_counts=True))},
           "start_ge_end": int((g.start_year.values >= g.end_year.values).sum())}
    p = INTERIM / "reports" / "nyc_buildings_summary.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1))
    log(f"buildings: confidence {out['confidence']}; busiest years {top[:6]}")


def evidence():
    """Dated outlines that prove the ground under them existed (ground_rule.write_evidence):
    landmark records and researched rows (strong), recorded assessor years (weak), and the
    outlines traced from dated maps (strong, at the map's year). Run before
    `terrain_tiles.py land`."""
    from ground_rule import write_evidence
    g = load_footprints()
    year, raw, conf, end, src, xy = assign_years(g, load_pluto(), load_lpc())
    rec = np.isin(src, ["lpc", "known", "assessor"])
    geoms = [g.geometry.values[rec]]
    years = [year[rec]]
    strong = [np.isin(src[rec], ["lpc", "known"])]
    try:
        from nyc_predecessors import load_structures
        t = load_structures()
        ty = np.where(t.cls.values == "traced", t.map_year.values.astype(float), t.start_doc.values.astype(float))
        geoms.append(t.geometry.to_crs(4326).values)
        years.append(ty)
        strong.append(np.ones(len(t), bool))
    except Exception as e:  # noqa: BLE001
        log(f"buildings: traced layers not used as ground evidence ({e})")
    write_evidence(np.concatenate([np.asarray(a, dtype=object) for a in geoms]), np.concatenate(years), np.concatenate(strong))


def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "evidence":
        evidence()
        return
    g = build()
    try:
        from nyc_predecessors import add_predecessors
    except ImportError:
        add_predecessors = None
    if add_predecessors is not None:
        g = add_predecessors(g)
    if os.environ.get("NYC_DRY"):   # test run: build everything, write nothing
        report(g)
        return
    write_outputs(g)


if __name__ == "__main__":
    main()
