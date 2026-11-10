"""Evidence-driven fill: buildings where the evidence says ground was built on and the map has none.

A building put up after the last traced atlas of its district and pulled down before 1996 (when
the city's record of removed footprints starts) is in no source the map has: at 1880, 1925 or
1950 whole districts that were densely built stand empty. This stage puts GENERATED buildings
(`procedural`) on such ground - only where a named piece of evidence says the spot was built on
at that time, and only where the map itself has nothing. Rules, sources, validation and limits:
data/manual/gapfill/README.md. In short:

  lots        every city block (the polygons between today's street centre lines) is cut into
              lot-sized outlines in rows along its straight frontages, each row on its frontage's
              bearing; the outline's width and depth are the medians of the old buildings standing
              in the block (4.8-8.5 m by 9.5-27 m; type - frame, row house, tenement - by their
              height). A block deeper than one city block (a superblock whose streets were closed)
              is also cut inside, as the blocks it replaced. The lots are candidates, not buildings.
  evidence    (1) the city's aerial mosaics of 1924 and 1951: the presence model of
              aerial_presence.py scores every lot on the photograph ("a building stands on this
              outline"), unchanged and not retrained; a lot is kept by its own score and by what
              the photograph shows on the free lots around it, and not in open country;
              (2) the built-up extent snapshots (data/manual/extents) for the years before 1924,
              for the share of lots that the traced atlases show for such ground; for Hudson
              County the built block fronts of the USGS sheets of 1943 / 1947 and the built-up
              ground of the sheets of 1898 (data/manual/gapfill);
              (3) records that date a clearance: housing authority completion dates, park
              acquisitions, highway openings.
  a row       a lot the evidence shows built on at a time when no building of the map (standing
              or vanished, any source) touches it. It starts no later than its evidence (spread
              back over the recorded years of the buildings around it) and ends at the clearance
              record, at the photograph that shows it gone, or when the map's next building on
              the spot went up.
  nothing     where no evidence says a spot was built on: no row.

    python gap_fill.py snapshot    # copy of the buildings the map has (nyc + Hudson County)
    python gap_fill.py lots        # per z14 block: the lots and their photograph scores (cached; the long step)
    python gap_fill.py ink         # Hudson County: the 1940s sheets read on the lots (cached)
    python gap_fill.py assemble    # evidence -> rows; data/interim/gapfill/gapfill.parquet
    python gap_fill.py report      # the checks (districts, overlaps, streets, years) -> report.md
    python gap_fill.py             # all five
    python gap_fill.py fresh       # forget the snapshot (after a rebuild with new atlas layers), keep the lots
    python gap_fill.py look <lon> <lat> [name]   # thumbnails of both photographs with the lots drawn

Run time and memory (2026-11-10, the loaded four-core build machine): `lots` 25 minutes with six
processes (`lots` three, `lots-reverse` two, `lots-middle` one), one z14 block (1.85 km) at a time,
under 1 GB each; snapshot 10 s, ink 40 s, assemble 2.5 minutes (three processes), report 1 minute.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np
import pandas as pd
import shapely

import aerial_presence as ap
from common import INTERIM, MANUAL, RAW, TABLES, log

WORK = INTERIM / "gapfill"
DOC = MANUAL / "gapfill"
LAYOUT = 3                # version of the lot layout: a change of the cutting rules needs new lots (and new scores)
LOTS = WORK / f"lots_v{LAYOUT}"
ROWS = WORK / "rows"
EXISTING = WORK / "existing.parquet"
OUT = WORK / "gapfill.parquet"
BUILDINGS = INTERIM / "nyc_buildings.parquet"
COUNTY = INTERIM / "county_buildings.parquet"
OVERTURE = sorted((RAW / "overture").glob("*/roads_local.parquet"))[-1].parent
Z, ZB, NB, TILE = ap.Z, ap.ZB, ap.NB, ap.TILE

# ----------------------------------------------------------------------------- the rules, in one place
WIN_M = 600.0            # streets and buildings are read this far around a z14 block (a city block must close inside)
BLOCK_MIN_M2 = 600.0     # city blocks smaller than this hold no lot
BLOCK_MAX_M2 = 150e4     # ... larger than 150 ha are parks, airports, marsh: not cut
INSET_DEFAULT = 9.2      # centre line to building line: half a 60 ft street
INSET_RANGE = (6.5, 14.0)
STREET_GAP = 18.3        # a closed street inside a superblock: 60 ft between building lines
BLOCK_PERIOD = 79.2      # 200 ft block + 60 ft street
# The size of a lot's outline is measured, not assumed: the median width and depth of the old
# buildings (standing, built by 1935) of the same city block - of the nearest block that has five,
# where it has none - within the bounds of the building types of the time. `bw`, `d` are the fallback
# where nothing old stands anywhere near; `gap` is the space between detached houses; storeys and
# material go with the type.
TYPES = {
    "tenement": dict(bw=7.62, d=22.0, gap=0.0, st=(4, 5, 5, 5, 6), mat="brick"),     # 25 ft lots, 60-90 ft deep
    "rowhouse": dict(bw=5.8, d=12.2, gap=0.0, st=(2, 3, 3, 3, 4), mat="brick"),      # 19-20 ft x 40 ft
    "frame": dict(bw=6.1, d=10.0, gap=1.5, st=(2, 2, 2, 3), mat="frame"),            # 20 x 33 ft on a 25 ft lot
}
WIDTH_RANGE = (4.8, 8.5)
DEPTH_RANGE = (9.5, 27.0)
TYPE_H = (9.0, 13.5)     # median roof height of the block's old buildings: below = frame, between = row house, above = tenement
HALF_STREET = {"residential": 7.0, "unclassified": 7.0, "living_street": 6.0, "tertiary": 9.0, "secondary": 11.0,
               "primary": 13.0, "trunk": 14.0}   # no lot within this distance of a street centre line
P_STOOD = {1924: 0.8, 1951: 0.7}     # data/manual/aerial/README.md "How to use it"
P_OPEN = {1924: 0.2, 1951: 0.1}
P_STATEN = 0.9           # Staten Island: the model's "stood" is unproven there (its README): odds of 9 to 1 are asked
PRIOR_RANGE = (0.2, 0.85)  # odds beforehand from the neighbouring lots (see assemble_block): 0.2 alone, 0.85 in a built row
PHOTO_T = {1924: 1924.5, 1951: 1951.5}
AFTER_GAP = 3.0          # a map building that starts within this of the photograph may be what the photograph shows
BEFORE_GAP = 2.0         # ... and so may one that the map ends within this before it (most ends are estimates)
CONTEXT_M = 75.0         # a photographed lot needs built-up ground of a snapshot, or CONTEXT_N map buildings this near
CONTEXT_N = 3
LEAD = (1.0, 2.5)        # a predecessor ends this long before the building that replaced it was finished
NEAR_M = 30.0            # "neighbours" for the isolation rule
YEAR_POOL_M = 300.0      # recorded years are taken from this far around
# share of the eligible lots kept under a generalised built-up extent: measured against the traced
# atlases at every run (calibrate_extents); these values only where too little can be measured
EXTENT_KEEP = {"all": 0.5}
SMALL_SHARE = 0.35       # a map building smaller than this share of a lot (and than SMALL_M2) notches the lot instead of blocking it
SMALL_M2 = 30.0
NOTCH_MIN = 0.55         # ... if this share of the lot is left
RECORD_FROM = 1995.5     # the city's removed footprints begin in 1996: a fill row of the boroughs cannot end later
OPEN_END = (1956.0, 1984.0)   # seen in 1951, nothing on the spot today, not in the city's removals (1996-): ended in between


def h01(key: str) -> float:
    return int(hashlib.sha1(key.encode()).hexdigest()[:12], 16) / float(16 ** 12)


def hvec(keys, salt=""):
    return np.array([h01(salt + k) for k in keys])


# ----------------------------------------------------------------------------- coordinates
def px_to_lonlat(x, y):
    n = TILE * 2.0 ** Z
    lon = np.asarray(x, "float64") / n * 360.0 - 180.0
    lat = np.degrees(np.arctan(np.sinh(math.pi * (1 - 2 * np.asarray(y, "float64") / n))))
    return lon, lat


def to_px(geoms):
    def tr(c):
        x, y = ap.lonlat_to_pixel(c[:, 0], c[:, 1])
        return np.column_stack([x, y])
    return shapely.transform(geoms, tr)


def to_lonlat(geoms):
    def tr(c):
        lon, lat = px_to_lonlat(c[:, 0], c[:, 1])
        return np.column_stack([lon, lat])
    return shapely.transform(geoms, tr)


def block_px(bx, by):
    """x0, y0, x1, y1 of a z14 block in global pixels of zoom Z."""
    s = NB * TILE
    return bx * s, by * s, (bx + 1) * s, (by + 1) * s


_con = None


def con():
    global _con
    if _con is None:
        import duckdb
        _con = duckdb.connect()
        _con.execute("set memory_limit='1GB'")
        _con.execute("set threads=1")
        _con.execute("load spatial")
    return _con


# ----------------------------------------------------------------------------- snapshot of what the map has
def step_snapshot():
    """Every building the map has (the city's, standing and vanished; Hudson County's), without this
    stage's own rows, sorted by z14 block. nyc_buildings.parquet is rewritten by every rebuild: retry."""
    import duckdb
    if EXISTING.exists():
        return
    WORK.mkdir(parents=True, exist_ok=True)
    n = 2.0 ** ZB
    bk = f"""cast(floor((lon + 180) / 360 * {n}) as integer) as bkx,
             cast(floor((0.5 - ln(tan(radians(lat)) + 1 / cos(radians(lat))) / (2 * pi())) * {n}) as integer) as bky"""
    tmp = EXISTING.with_suffix(".part")
    for attempt in range(8):
        try:
            c = duckdb.connect()
            c.execute("set memory_limit='1500MB'")
            c.execute("load spatial")
            parts = [f"""select coalesce(doitt_id, '') as doitt_id, cast(bin as bigint) as bin, boro, start_year, end_year, year_src,
                               year_confidence, height_m, area, ST_X(ST_Centroid(geometry)) as lon, ST_Y(ST_Centroid(geometry)) as lat,
                               ST_AsWKB(geometry) as wkb
                        from '{BUILDINGS}' where year_src not like 'gapfill%' and boro in ('1','2','3','4','5')"""]
            if COUNTY.exists():
                parts.append(f"""select '' as doitt_id, cast(null as bigint) as bin, 'Hudson' as boro, start_year, end_year, year_src,
                                        year_confidence, height_m, area, ST_X(ST_Centroid(geometry)) as lon,
                                        ST_Y(ST_Centroid(geometry)) as lat, ST_AsWKB(geometry) as wkb
                                 from '{COUNTY}' where county = 'Hudson' and year_src not like 'gapfill%'""")
            c.execute(f"""copy (select row_number() over () as eid, *, {bk} from ({' union all '.join(parts)})
                                where lon is not null and start_year < end_year order by bkx, bky)
                          to '{tmp}' (format parquet, row_group_size 20000)""")
            break
        except (duckdb.IOException, duckdb.InvalidInputException) as e:
            log(f"snapshot: {str(e)[:120]} - retry in 60 s")
            time.sleep(60)
    else:
        raise RuntimeError("could not read the building files")
    tmp.rename(EXISTING)
    r = con().execute(f"select boro, count(*), sum((end_year < 9999)::int) from '{EXISTING}' group by 1 order by 1").fetchall()
    log(f"snapshot: {EXISTING.name}: " + ", ".join(f"{b}: {n_} ({int(v)} vanished)" for b, n_, v in r))


def existing_window(bx, by, cols="eid, boro, start_year, end_year, year_src, year_confidence, height_m, area, bin, lon, lat, wkb"):
    """The map's buildings centred within WIN_M of the block; geometry in global pixels (`g`)."""
    x0, y0, x1, y1 = block_px(bx, by)
    m = WIN_M / 0.9
    lo0, la1 = px_to_lonlat(x0 - m, y0 - m)
    lo1, la0 = px_to_lonlat(x1 + m, y1 + m)
    df = con().execute(f"""select {cols} from '{EXISTING}'
        where bkx between {bx - 1} and {bx + 1} and bky between {by - 1} and {by + 1}
          and lon >= {lo0} and lon < {lo1} and lat >= {la0} and lat < {la1}""").fetchdf()
    g = shapely.from_wkb(df.pop("wkb").map(bytes).values) if len(df) else np.array([], dtype=object)
    ok = np.array([x is not None and not x.is_empty for x in g], bool) if len(df) else np.zeros(0, bool)
    df = df[ok].reset_index(drop=True)
    g = shapely.make_valid(g[ok])
    df["g"] = to_px(g)
    return df


def blocks_todo():
    r = con().execute(f"select bkx, bky, count(*) n from '{EXISTING}' group by 1, 2 order by n desc").fetchall()
    return [(int(a), int(b)) for a, b, n in r if n >= 5]          # the densest blocks first


# ----------------------------------------------------------------------------- streets, water, city blocks
def _window_sql(bx, by, m_px):
    x0, y0, x1, y1 = block_px(bx, by)
    lo0, la1 = px_to_lonlat(x0 - m_px, y0 - m_px)
    lo1, la0 = px_to_lonlat(x1 + m_px, y1 + m_px)
    return f"ST_Intersects(geometry, ST_MakeEnvelope({lo0}, {la0}, {lo1}, {la1}))"


def streets_window(bx, by):
    """Street centre lines around the block: (lines in pixels, class). Motorways and tunnels are not
    streets (what stood under a motorway stood until it was built)."""
    w = _window_sql(bx, by, WIN_M / 0.9)
    rows = con().execute(f"""select class, ST_AsWKB(geometry) from '{OVERTURE}/roads_local.parquet'
            where class in ('residential', 'unclassified', 'living_street') and {w}
              and coalesce(cast(road_flags as varchar), '') not like '%is_tunnel%'
        union all
        select class, ST_AsWKB(geometry) from '{OVERTURE}/roads_region.parquet'
            where class in ('tertiary', 'secondary', 'primary', 'trunk') and {w}
              and coalesce(cast(road_flags as varchar), '') not like '%is_tunnel%'""").fetchall()
    if not rows:
        return np.array([], dtype=object), np.array([], dtype=object)
    g = shapely.from_wkb([bytes(r[1]) for r in rows])
    cls = np.array([r[0] for r in rows], dtype=object)
    ok = shapely.get_type_id(g) == 1
    return to_px(g[ok]), cls[ok]


def water_window(bx, by):
    """Today's water (no swimming pools) and cemeteries around the block, as one geometry each (pixels)."""
    w = _window_sql(bx, by, 80)
    rows = con().execute(f"""select ST_AsWKB(geometry) from '{OVERTURE}/base_water.parquet'
        where class not in ('swimming_pool', 'reflecting_pool', 'drain', 'ditch') and {w}""").fetchall()
    g = shapely.from_wkb([bytes(r[0]) for r in rows]) if rows else np.array([], dtype=object)
    g = g[np.isin(shapely.get_type_id(g), (3, 6))] if len(g) else g
    water = shapely.union_all(shapely.make_valid(to_px(g))) if len(g) else None
    rows = con().execute(f"""select ST_AsWKB(geometry) from '{OVERTURE}/base_land_use.parquet'
        where class = 'cemetery' and {w}""").fetchall()
    g = shapely.from_wkb([bytes(r[0]) for r in rows]) if rows else np.array([], dtype=object)
    g = g[np.isin(shapely.get_type_id(g), (3, 6))] if len(g) else g
    cem = shapely.union_all(shapely.make_valid(to_px(g))) if len(g) else None
    return water, cem


def rail_window(bx, by):
    """STRtree of today's surface railways around the block, 6 m to each side (no subways: they run
    under the streets). Rail yards and cuts are not building lots, and wagons look like roofs."""
    w = _window_sql(bx, by, 80)
    rows = con().execute(f"""select ST_AsWKB(geometry) from '{OVERTURE}/rail.parquet'
        where class in ('standard_gauge', 'unknown', 'light_rail', 'narrow_gauge') and {w}
          and coalesce(cast(rail_flags as varchar), '') not like '%is_tunnel%'""").fetchall()
    if not rows:
        return None
    g = to_px(shapely.from_wkb([bytes(r[0]) for r in rows]))
    return shapely.STRtree(shapely.buffer(g, 6.0 / MPP, cap_style="flat"))


def city_blocks(lines, bx, by):
    """Polygons between the street centre lines that touch the z14 block."""
    if len(lines) < 3:
        return np.array([], dtype=object)
    merged = shapely.unary_union(lines)
    polys = shapely.get_parts(shapely.polygonize(list(shapely.get_parts(merged))))
    if not len(polys):
        return polys
    x0, y0, x1, y1 = block_px(bx, by)
    box = shapely.box(x0, y0, x1, y1)
    a = shapely.area(polys) * MPP2
    return polys[shapely.intersects(polys, box) & (a >= BLOCK_MIN_M2) & (a <= BLOCK_MAX_M2)]


MPP = ap.metres_per_pixel(40.72)
MPP2 = MPP * MPP


def frontage_rows(poly, inset_m, key, bw, d, gap):
    """Rows of lot outlines along every straight frontage of a city block (edges of 20 m and more of
    the block polygon simplified by 2.5 m), longest frontage first; an outline that would lie on one
    already placed is dropped, so corners go to the longer frontage. Each outline stands on the
    building line (`inset_m` inside the centre-line polygon), is `bw` wide and about `d` deep - not
    deeper than half the block behind that frontage. Returns [(rectangle, row index)]."""
    inner = shapely.buffer(poly, -inset_m / MPP, join_style="mitre")
    if inner.is_empty or shapely.area(inner) * MPP2 < 150:
        return []
    tol = shapely.buffer(inner, 0.6 / MPP)
    shapely.prepare(tol)
    shapely.prepare(poly)
    ring = shapely.simplify(poly, 2.5 / MPP)
    if ring.geom_type != "Polygon":
        return []
    c = np.asarray(ring.exterior.coords)[:-1]
    iv = shapely.get_coordinates(inner)
    edges = []
    for a in range(len(c)):
        p0, p1 = c[a], c[(a + 1) % len(c)]
        Lp = float(np.hypot(*(p1 - p0)))
        if Lp * MPP >= 20.0:
            edges.append((Lp, p0, p1))
    edges.sort(key=lambda e: -e[0])
    w_px, bw_px, in_px, dmin = (bw + gap) / MPP, bw / MPP, inset_m / MPP, 0.88 * d
    out, placed = [], []
    for ri, (Lp, p0, p1) in enumerate(edges):
        t = (p1 - p0) / Lp
        nrm = np.array([-t[1], t[0]])
        mid = p0 + t * Lp / 2 + nrm * (in_px + 3.0 / MPP)
        if not shapely.contains_xy(poly, mid[0], mid[1]):
            nrm = -nrm
        nl = int(Lp // w_px)
        if nl < 1:
            continue
        Hn = float(((iv - p0) @ nrm).max()) * MPP - inset_m           # depth of the block behind this frontage
        if Hn < dmin * 0.8:
            continue
        avail = Hn / 2 - 0.5 if Hn >= 2 * dmin + 1.0 else Hn
        us = (Lp - nl * w_px) / 2 + (gap / 2) / MPP + w_px * np.arange(nl)
        dd = d * (0.88 + 0.24 * np.array([h01(f"{key}:f{ri}:{i}") for i in range(nl)]))
        dd = np.minimum(dd, max(avail, dmin * 0.8)) / MPP
        A = p0 + t * us[:, None] + nrm * in_px
        B = A + t * bw_px
        C = B + nrm * dd[:, None]
        D = A + nrm * dd[:, None]
        g = shapely.polygons(np.stack([A, B, C, D, A], axis=1))
        g = g[shapely.contains(tol, g)]
        if len(g) and placed:
            hit = np.unique(shapely.STRtree(np.array(placed, dtype=object)).query(shapely.buffer(g, -0.15 / MPP), predicate="intersects")[0])
            keep = np.ones(len(g), bool)
            keep[hit] = False
            g = g[keep]
        for q in g:
            placed.append(q)
            out.append((q, ri))
    return out


def lots_of_block(poly, kind, inset_m, key, bw, d):
    """Lot-sized building outlines of one city block: rectangles in rows along the long frontages.

    The block's frame is its minimum rotated rectangle (u along the long side). The building line is
    the centre-line polygon shrunk by `inset_m` (measured from the block's old buildings). Rows of
    lots face the two long frontages, each outline `bw` wide and about `d` deep (0.88-1.12 d, by
    hash), `gap` apart; a block deeper than one city block (BLOCK_PERIOD) is cut as k blocks with
    closed streets (STREET_GAP) between them, k = round((depth + gap) / period). Outlines that leave
    the building line polygon by more than 0.6 m are dropped. Returns [(rectangle, row index)]."""
    t = TYPES[kind]
    inner = shapely.buffer(poly, -inset_m / MPP, join_style="mitre")
    if inner.is_empty or shapely.area(inner) * MPP2 < 150:
        return []
    r = np.asarray(shapely.minimum_rotated_rectangle(poly).exterior.coords)
    e1, e2 = r[1] - r[0], r[2] - r[1]
    eu = e1 if np.hypot(*e1) >= np.hypot(*e2) else e2
    ang = math.atan2(eu[1], eu[0])
    ca, sa = math.cos(ang), math.sin(ang)
    o = r[0]

    def fwd(c):          # pixels -> the block's frame, metres
        q = (c - o) * MPP
        return np.column_stack([q[:, 0] * ca + q[:, 1] * sa, -q[:, 0] * sa + q[:, 1] * ca])

    def back(c):
        return np.column_stack([c[:, 0] * ca - c[:, 1] * sa, c[:, 0] * sa + c[:, 1] * ca]) / MPP + o

    inner_f = shapely.transform(inner, fwd)
    umin, vmin, umax, vmax = shapely.bounds(inner_f)
    L, H = umax - umin, vmax - vmin
    w = bw + t["gap"]
    n = int(L // w)
    dmin = 0.88 * d
    if n < 1 or H < dmin:
        return []
    u0 = umin + (L - n * w) / 2 + t["gap"] / 2
    rows = []                                     # (front v, direction +1 / -1, depth available)
    k = max(1, int(round((H + STREET_GAP) / BLOCK_PERIOD)))
    P = (H + STREET_GAP) / k
    for j in range(k):
        v0 = vmin + j * P
        v1 = v0 + P - STREET_GAP
        depth = v1 - v0
        if depth >= 2 * dmin + 1.0:
            rows.append((v0, 1.0, depth / 2 - 0.5))
            rows.append((v1, -1.0, depth / 2 - 0.5))
        else:
            rows.append((v0, 1.0, depth))
    rects, rown = [], []
    us = u0 + w * np.arange(n)
    for ri, (vf, sgn, avail) in enumerate(rows):
        dd = d * (0.88 + 0.24 * np.array([h01(f"{key}:{ri}:{i}") for i in range(n)]))
        dd = np.minimum(dd, max(avail, dmin * 0.8))
        va = np.full(n, vf)
        vb = vf + sgn * dd
        lo, hi = np.minimum(va, vb), np.maximum(va, vb)
        c = np.empty((n, 5, 2))
        c[:, 0] = np.column_stack([us, lo])
        c[:, 1] = np.column_stack([us + bw, lo])
        c[:, 2] = np.column_stack([us + bw, hi])
        c[:, 3] = np.column_stack([us, hi])
        c[:, 4] = c[:, 0]
        rects.append(c)
        rown.append(np.full(n, ri))
    c = np.concatenate(rects)
    rown = np.concatenate(rown)
    g = shapely.polygons(c)
    tol = shapely.buffer(inner_f, 0.6)
    shapely.prepare(tol)
    keep = shapely.contains(tol, g)
    if not keep.any():
        return []
    g = shapely.transform(g[keep], back)
    return list(zip(g, rown[keep]))


def make_lots(bx, by):
    """The candidate lots centred in a z14 block: DataFrame (geometry in pixels as `g`)."""
    lines, cls = streets_window(bx, by)
    ex = existing_window(bx, by)
    polys = city_blocks(lines, bx, by)
    cols = ["cid", "cb", "kind", "row", "g"]
    if not len(polys) or not len(ex):
        return pd.DataFrame(columns=cols), ex, lines, cls
    cen = shapely.centroid(ex.g.values)
    standing = (ex.end_year.values == 9999)
    old = standing & (ex.start_year.values <= 1935) & (ex.area.values >= 35)
    tree = shapely.STRtree(cen)
    pi, bi = tree.query(polys, predicate="contains")
    # per city block: building line, type and outline size from its own old buildings
    med_h = np.full(len(polys), np.nan)
    med_w = np.full(len(polys), np.nan)
    med_d = np.full(len(polys), np.nan)
    inset = np.full(len(polys), INSET_DEFAULT)
    rc = shapely.get_coordinates(shapely.get_exterior_ring(shapely.minimum_rotated_rectangle(ex.g.values[old])))
    side_s = np.full(len(ex), np.nan)
    side_l = np.full(len(ex), np.nan)
    if old.any() and len(rc) == 5 * int(old.sum()):
        rc = rc.reshape(-1, 5, 2)
        l1 = np.hypot(*(rc[:, 1] - rc[:, 0]).T) * MPP
        l2 = np.hypot(*(rc[:, 2] - rc[:, 1]).T) * MPP
        side_s[old], side_l[old] = np.minimum(l1, l2), np.maximum(l1, l2)
    order = np.argsort(pi, kind="stable")
    pi, bi = pi[order], bi[order]
    starts = np.searchsorted(pi, np.arange(len(polys) + 1))
    for k in range(len(polys)):
        b = bi[starts[k]:starts[k + 1]]
        if not len(b):
            continue
        bo = b[old[b]]
        if len(bo) >= 3:
            med_h[k] = np.nanmedian(ex.height_m.values[bo])
        if len(bo) >= 5 and np.isfinite(side_s[bo]).sum() >= 5:
            med_w[k] = np.nanmedian(side_s[bo])
            med_d[k] = np.nanmedian(side_l[bo])
        bs = bo                                   # the old buildings keep the old building line (towers stand back from it)
        if len(bs) >= 5:
            d = shapely.distance(ex.g.values[bs], shapely.boundary(polys[k])) * MPP
            d = d[d < 40]
            if len(d) >= 5:
                inset[k] = float(np.clip(np.percentile(d, 15), *INSET_RANGE))
    # blocks without old buildings take the type of the nearest block that has them
    known = np.isfinite(med_h)
    if known.any():
        from scipy.spatial import cKDTree
        pc = shapely.get_coordinates(shapely.centroid(polys))
        _, j = cKDTree(pc[known]).query(pc)
        med_h = np.where(known, med_h, med_h[known][j])
    else:
        med_h[:] = 7.0
    kind = np.where(med_h >= TYPE_H[1], "tenement", np.where(med_h >= TYPE_H[0], "rowhouse", "frame"))
    known = np.isfinite(med_w)
    if known.any():
        from scipy.spatial import cKDTree
        pc = shapely.get_coordinates(shapely.centroid(polys))
        _, j = cKDTree(pc[known]).query(pc)
        med_w, med_d = np.where(known, med_w, med_w[known][j]), np.where(known, med_d, med_d[known][j])
    else:
        med_w = np.array([TYPES[q]["bw"] for q in kind])
        med_d = np.array([TYPES[q]["d"] for q in kind])
    med_w = np.clip(med_w, *WIDTH_RANGE)
    med_d = np.clip(med_d, *DEPTH_RANGE)
    x0, y0, x1, y1 = block_px(bx, by)
    out = []
    for k, poly in enumerate(polys):
        pc = shapely.centroid(poly)
        lon, lat = px_to_lonlat(pc.x, pc.y)
        cb = hashlib.sha1(f"{lon:.5f},{lat:.5f},{shapely.area(poly) * MPP2:.0f}".encode()).hexdigest()[:10]
        fr = frontage_rows(poly, inset[k], cb, float(med_w[k]), float(med_d[k]), TYPES[kind[k]]["gap"])
        for g, ri in fr:
            out.append((cb, kind[k], int(ri), g, inset[k]))
        # the inside of a superblock (and blocks without straight frontages): rows on the block's own frame
        deep = lots_of_block(poly, kind[k], inset[k], cb, float(med_w[k]), float(med_d[k]))
        if deep and fr:
            dg = np.array([q for q, _ in deep], dtype=object)
            hit = np.unique(shapely.STRtree(np.array([q for q, _ in fr], dtype=object)).query(shapely.buffer(dg, -0.15 / MPP), predicate="intersects")[0])
            deep = [x for j_, x in enumerate(deep) if j_ not in set(hit.tolist())]
        for g, ri in deep:
            out.append((cb, kind[k], 100 + int(ri), g, inset[k]))
    if not out:
        return pd.DataFrame(columns=cols), ex, lines, cls
    df = pd.DataFrame(out, columns=["cb", "kind", "row", "g", "inset"])
    c = shapely.get_coordinates(shapely.centroid(df.g.values))
    inb = (c[:, 0] >= x0) & (c[:, 0] < x1) & (c[:, 1] >= y0) & (c[:, 1] < y1)
    df = df[inb].reset_index(drop=True)
    c = c[inb]
    if not len(df):
        return pd.DataFrame(columns=cols), ex, lines, cls
    # not on a street, not in today's water, not in a cemetery
    # (a lot stands on its block's building line: the street it faces cannot exclude it, a wider street
    # at the end of its row can)
    bad = np.zeros(len(df), bool)
    if len(lines):
        ins = df.inset.values
        for name in np.unique(cls):
            ln = lines[cls == name]
            a_, b_ = shapely.STRtree(ln).query(df.g.values, predicate="dwithin", distance=HALF_STREET[name] / MPP)
            if len(a_):
                dist = shapely.distance(df.g.values[a_], ln[b_]) * MPP
                bad[a_[dist < np.minimum(HALF_STREET[name], ins[a_] - 0.3)]] = True
    water, cem = water_window(bx, by)
    for area in (water, cem):
        if area is not None and not area.is_empty:
            shapely.prepare(area)
            bad |= shapely.intersects(area, df.g.values)
    df = df[~bad].drop(columns=["inset"]).reset_index(drop=True)
    c = c[~bad]
    lon, lat = px_to_lonlat(c[:, 0], c[:, 1])
    df["lon"] = lon
    df["lat"] = lat
    df["cid"] = [hashlib.sha1(f"{a:.6f},{b:.6f}".encode()).hexdigest()[:14] for a, b in zip(lon, lat)]
    df = df.drop_duplicates("cid").reset_index(drop=True)
    return df, ex, lines, cls


# ----------------------------------------------------------------------------- the photographs
_models = {}


def model(year):
    if year not in _models:
        _models[year] = ap.load_model(year)
    return _models[year]


def score_lots(bx, by, lots_px, ex, year):
    """p (a building stands on the outline in the photograph of `year`), cover and the registration
    level for every lot. The model, its features and its registration are aerial_presence.py's,
    unchanged; the lots take the place of today's footprints in the picture (they tile the
    blocks), today's footprints older than the photograph find the shift."""
    n = len(lots_px)
    p = np.full(n, np.nan, "float32")
    cover = np.zeros(n, "float32")
    level = np.zeros(n, "int8")
    blk = ap.load_block(year, bx, by)
    if blk is None or n == 0:
        return p, cover, level
    g, valid, x0, y0 = blk
    cut = ap.PAD * TILE - ap.MARGIN
    g, valid = g[cut:-cut, cut:-cut], valid[cut:-cut, cut:-cut]
    x0, y0 = x0 + cut, y0 + cut
    valid = ap.blank_mask(g, valid, year)
    if not valid.any():
        return p, cover, level
    P = ap.pixel_layers(g, valid)
    H, W = g.shape
    off = np.array([x0, y0], "float64")
    real = ex[(ex.end_year.values == 9999) & (ex.start_year.values <= year - 1) & (ex.area.values > 60)]
    rc = shapely.get_coordinates(shapely.centroid(real.g.values)) - off if len(real) else np.zeros((0, 2))
    inside = (rc[:, 0] > 0) & (rc[:, 0] < W) & (rc[:, 1] > 0) & (rc[:, 1] < H) if len(real) else np.zeros(0, bool)
    rg = real.g.values[inside]
    allg = shapely.transform(np.concatenate([rg, lots_px]), lambda c: c - off)
    use = np.zeros(len(allg), bool)
    use[:len(rg)] = True
    cen = shapely.centroid(allg)
    dx, dy, lv = ap.estimate_offsets(P["G"], valid, allg, use, shapely.get_x(cen), shapely.get_y(cen))
    cand = allg[len(rg):]
    dx, dy, lv = dx[len(rg):], dy[len(rg):], lv[len(rg):]
    if lv.any():
        xy = shapely.get_coordinates(cand)
        rep = shapely.get_num_coordinates(cand)
        cand = shapely.set_coordinates(cand.copy(), xy + np.column_stack([np.repeat(dx, rep), np.repeat(dy, rep)]))
    f = ap.block_features(g, valid, P, cand)
    m, xs, ps = model(year)
    X = np.column_stack([np.asarray(f[name], "float64") for name in ap.MODEL_FEATS])
    p = np.interp(m.decision(X), xs, ps).astype("float32")
    cover = np.asarray(f["cover"], "float32")
    p[~(cover >= ap.COVER_MIN)] = np.nan
    return p, cover, lv.astype("int8")


def lots_path(bx, by):
    return LOTS / f"{bx}_{by}.parquet"


def do_block(job):
    bx, by = job
    out = lots_path(bx, by)
    if out.exists():
        return job, -1, 0.0
    t0 = time.time()
    try:
        df, ex, _, _ = make_lots(bx, by)
        if len(df):
            for year in ap.YEARS:
                p, cover, lv = score_lots(bx, by, df.g.values, ex, year)
                df[f"p{year}"] = p
                df[f"cover{year}"] = cover
                df[f"reg{year}"] = lv
            df["wkb"] = shapely.to_wkb(to_lonlat(df.g.values))
        df = df.drop(columns=["g"])
        df["bx"] = np.int32(bx)
        df["by"] = np.int32(by)
    except Exception as e:  # noqa: BLE001 - one bad block must not stop the run; it is reported and left for a rerun
        log(f"lots: block {bx}_{by} failed: {type(e).__name__}: {str(e)[:200]}")
        return job, -2, time.time() - t0
    tmp = out.with_suffix(f".part{os.getpid()}")
    df.to_parquet(tmp, compression="zstd", index=False)
    tmp.rename(out)
    return job, len(df), time.time() - t0


def _fresh_connection():
    global _con
    _con = None            # a DuckDB connection does not survive a fork


def step_lots(workers=3, only=None, reverse=False, middle=False, budget_s=None):
    from multiprocessing import Pool
    LOTS.mkdir(parents=True, exist_ok=True)
    jobs = [j for j in (only or blocks_todo()) if not lots_path(*j).exists()]
    if reverse:                     # a second run can work from the other end (`lots-reverse`)
        jobs = jobs[::-1]
    if middle:                      # ... and a third from the middle outwards (`lots-middle [seconds]`), one process
        m_ = len(jobs) // 2
        jobs = [j for pair in zip(jobs[m_:], jobs[m_ - 1::-1]) for j in pair] + jobs[2 * m_:]
    if _con is not None:
        _con.close()
    _fresh_connection()
    log(f"lots: {len(jobs)} blocks to cut and score, {workers} workers")
    t0 = time.time()
    done = n = bad = 0
    if workers <= 1 or len(jobs) <= 1:
        it = map(do_block, jobs)
        pool = None
    else:
        _fresh_connection()
        pool = Pool(workers, initializer=_fresh_connection, maxtasksperchild=8)
        it = pool.imap_unordered(do_block, jobs)
    for job, k, dt in it:
        if budget_s and time.time() - t0 > budget_s:
            break
        done += 1
        n += max(k, 0)
        bad += k == -2
        if done % 10 == 0 or done == len(jobs):
            log(f"lots: {done}/{len(jobs)} blocks, {n} lots, {bad} failed, {time.time() - t0:.0f} s")
    if pool is not None:
        pool.close()
        pool.join()


# ----------------------------------------------------------------------------- Hudson County: the USGS sheets of 1947
# The 1:24,000 / 1:25,000 sheets of 1947 (compiled from aerial photographs of 1940) draw every built
# block front as a heavy black band and large buildings as black blocks. Per lot: the share of its
# outline that is heavy black ink. (The 1955 editions replace the bands by a flat urban tint.)
SHEETS_1947 = {"NJ_Jersey_City_254499_1947_24000_geo.tif": (-74.125, 40.625, -74.0, 40.75),      # edition of 1947
               "NJ_Weehawken_255029_1943_25000_geo.tif": (-74.125, 40.75, -74.0, 40.875)}        # edition of 1943 (the 1947 one is tinted)
SHEET_YEAR = {"NJ_Jersey_City_254499_1947_24000_geo.tif": 1947, "NJ_Weehawken_255029_1943_25000_geo.tif": 1943}
SHEET_DIR = RAW / "piers" / "usgs"          # downloaded by the piers part (data/manual/piers/tools/sheets.json has the URLs)
INK = WORK / f"sheet_ink_v{LAYOUT}"
INK_T, INK_GAP, INK_MIN = 1941.0, 7.0, 0.7   # the photographs behind the sheets are of 1940; printed 1947
SHIFT_TOL = 20.0                             # metres a block's shift may lie from its sheet's median


def ink_block(bx, by, forced=None):
    """cid -> share of heavy black ink on the 1947 sheet, for the lots of a block that a sheet covers."""
    import rasterio
    from affine import Affine
    from rasterio import features
    from rasterio.enums import Resampling
    from rasterio.warp import reproject
    from scipy import ndimage as ndi
    lp = lots_path(bx, by)
    if not lp.exists():
        return None
    lots = pd.read_parquet(lp)
    if not len(lots):
        return None
    x0, y0, x1, y1 = block_px(bx, by)
    k = 2                                           # the sheet is read on the z16 grid (1.8 m; the scans are 2 m)
    mrg = 40
    Wd = (x1 - x0) // k + 2 * mrg
    res = 156543.03392804097 / 2 ** Z * k
    tr = Affine(res, 0, (x0 - mrg * k) * res / k - 20037508.342789244, 0, -res, 20037508.342789244 - (y0 - mrg * k) * res / k)
    out = np.full(len(lots), np.nan, "float32")
    g = shapely.transform(to_px(shapely.from_wkb(lots.wkb.values)), lambda c: (c - np.array([x0 - mrg * k, y0 - mrg * k])) / k)
    lines, _ = streets_window(bx, by)
    ex = existing_window(bx, by)
    shifts = {}
    year_of = np.zeros(len(lots), "int16")
    sh_e = np.zeros(len(lots), "float32")
    sh_s = np.zeros(len(lots), "float32")
    for fn, (lo0, la0, lo1, la1) in SHEETS_1947.items():
        sel = np.flatnonzero((lots.lon.values >= lo0) & (lots.lon.values < lo1) & (lots.lat.values >= la0) & (lots.lat.values < la1))
        p = SHEET_DIR / fn
        if not len(sel) or not p.exists():
            continue
        with rasterio.open(p) as src:
            a = np.zeros((3, Wd, Wd), "uint8")
            for b in range(3):
                reproject(rasterio.band(src, b + 1), a[b], dst_transform=tr, dst_crs="EPSG:3857", resampling=Resampling.bilinear)
        a = a.astype("int16")
        lum = a[0] * 0.299 + a[1] * 0.587 + a[2] * 0.114
        black = (lum < 115) & ((a.max(0) - a.min(0)) < 70)
        heavy = ndi.binary_opening(black, iterations=2)           # letters, hachures and rails are thinner than a block front
        # where the sheet sits against today's map. The scans are georeferenced on the datum of 1927
        # (PROJ moves them to within about 10 m) and their drawing is off by up to 35 m in places (the
        # piers part measured it). Per block: the shift within 40 m that puts most heavy ink under the
        # buildings of the map that stood then and least on today's street lines. No clear answer: no reading.
        org_ = np.array([x0 - mrg * k, y0 - mrg * k])
        old = ex[(ex.start_year.values <= 1935) & (ex.end_year.values > INK_T) & (ex.area.values > 40)]
        if len(lines) < 80 or len(old) < 150:
            continue
        sr = features.rasterize([(q, 1) for q in shapely.transform(lines, lambda c: (c - org_) / k)], out_shape=heavy.shape, fill=0,
                                dtype="uint8").astype("float32")
        br = features.rasterize([(q, 1) for q in shapely.transform(old.g.values, lambda c: (c - org_) / k)], out_shape=heavy.shape,
                                fill=0, dtype="uint8").astype("float32")
        Fh = np.fft.rfft2(heavy.astype("float32"))
        R_ = 22
        sc = (np.fft.irfft2(Fh * np.conj(np.fft.rfft2(br)), s=heavy.shape) / max(br.sum(), 1.0)
              - np.fft.irfft2(Fh * np.conj(np.fft.rfft2(sr)), s=heavy.shape) / max(sr.sum(), 1.0))
        sc = np.roll(np.roll(sc, R_, 0), R_, 1)[:2 * R_ + 1, :2 * R_ + 1]            # sc[dy + R_, dx + R_]
        kk = np.unravel_index(sc.argmax(), sc.shape)
        if forced and SHEET_YEAR[fn] in forced:          # the sheet's own median shift (step_ink, second pass)
            kk = (int(round(forced[SHEET_YEAR[fn]][1] / (k * MPP))) + R_, int(round(forced[SHEET_YEAR[fn]][0] / (k * MPP))) + R_)
        elif not (sc.max() - np.median(sc) >= 0.12 and 0 < kk[0] < 2 * R_ and 0 < kk[1] < 2 * R_):
            continue
        dx, dy = int(kk[1] - R_), int(kk[0] - R_)
        shifts[fn] = [round(dx * k * MPP, 1), round(dy * k * MPP, 1), round(float(sc[dy + R_, dx + R_]), 2), round(float(np.median(sc)), 2)]
        year_of[sel] = SHEET_YEAR[fn]
        sh_e[sel], sh_s[sel] = shifts[fn][0], shifts[fn][1]
        # the sheets draw the streets wider than they are (and the block fronts pushed back by as much):
        # the ink is grown by 5 m before it is read on the lots
        heavy = ndi.binary_dilation(heavy, iterations=3)
        L = features.rasterize([(q, int(j) + 1) for j, q in zip(sel, shapely.transform(g[sel], lambda c: c + np.array([dx, dy])))],
                               out_shape=heavy.shape, fill=0, dtype="int32")
        cnt = np.bincount(L.ravel(), minlength=len(lots) + 1)[1:]
        s = np.bincount(L.ravel(), weights=heavy.ravel(), minlength=len(lots) + 1)[1:]
        with np.errstate(invalid="ignore", divide="ignore"):
            v = s / cnt
        out[sel] = v[sel]
    if not np.isfinite(out).any():
        return None
    log(f"ink: block {bx}_{by}: sheet shifts (m east, m south, ink under old buildings minus on streets, median of the search) {shifts}")
    return pd.DataFrame({"cid": lots.cid.values, "ink1947": out, "sheet_year": year_of, "shift_e": sh_e, "shift_s": sh_s})[np.isfinite(out)]


def _ink_job(job, force=False, forced=None):
    out = INK / f"{job[0]}_{job[1]}.parquet"
    if out.exists() and not force:
        return
    try:
        df = ink_block(*job, forced=forced)
    except Exception as e:  # noqa: BLE001
        log(f"ink: block {job} failed: {type(e).__name__}: {str(e)[:200]}")
        return
    if df is None:
        df = pd.DataFrame({"cid": [], "ink1947": [], "sheet_year": []})
    tmp = out.with_suffix(f".part{os.getpid()}")
    df.to_parquet(tmp, index=False)
    tmp.rename(out)


def step_ink():
    """The 1947 sheets on the lots of the blocks that hold Hudson County buildings (cached)."""
    INK.mkdir(parents=True, exist_ok=True)
    r = con().execute(f"select bkx, bky, count(*) n from '{EXISTING}' where boro = 'Hudson' group by 1, 2 order by n desc").fetchall()
    jobs = [(int(a), int(b)) for a, b, _ in r if lots_path(int(a), int(b)).exists() and not (INK / f"{int(a)}_{int(b)}.parquet").exists()]
    log(f"ink: {len(jobs)} blocks")
    for j in jobs:
        _ink_job(j)
    # second pass: a block whose shift lies more than SHIFT_TOL from its sheet's median is read again
    # with the median (a wrong peak on a regular street grid is likelier than a local jump of the drawing)
    rows = []
    for p in sorted(INK.glob("*.parquet")):
        d = pd.read_parquet(p)
        for sy, q in d.groupby("sheet_year") if len(d) else ():
            rows.append((p.stem, int(sy), float(q.shift_e.median()), float(q.shift_s.median())))
    if not rows:
        return
    t = pd.DataFrame(rows, columns=["block", "sheet", "e", "s"])
    med = t.groupby("sheet")[["e", "s"]].median()
    t["off"] = np.hypot(t.e - t.sheet.map(med.e), t.s - t.sheet.map(med.s))
    (INK / "shifts.json").write_text(json.dumps({"median_shift_m_east_south": {int(k_): [round(v.e, 1), round(v.s, 1)] for k_, v in med.iterrows()},
                                                 "blocks": t.round(1).to_dict("records")}, indent=1))
    redo = sorted(set(t.block[t.off > SHIFT_TOL]))
    log(f"ink: sheet medians (m east, m south) {med.round(1).to_dict('index')}; {len(redo)} blocks read again with the median: {redo}")
    forced = {int(k_): (float(v.e), float(v.s)) for k_, v in med.iterrows()}
    for b in redo:
        bx_, by_ = (int(v) for v in b.split("_"))
        _ink_job((bx_, by_), force=True, forced=forced)


# ----------------------------------------------------------------------------- evidence other than the photographs
PLACE_AREA = {"manhattan": "1", "bronx": "2", "brooklyn": "3", "williamsburgh": "3", "queens": "4", "staten_island": "5"}
_cache = {}


def snapshots():
    """{area: [(year, prepared polygon, class)]}: the built-up extent snapshots of the boroughs
    (data/manual/extents; class `usgs` for the generalised 1:62,500 sheets of 1889 / 1897, else `map`)
    and Hudson County's urban tint (data/manual/gapfill/hudson_builtup_<year>.geojson, class `usgs`).
    Each file already contains the earlier snapshots of its place."""
    if "snaps" in _cache:
        return _cache["snaps"]
    per = {}
    files = [(f, PLACE_AREA.get(f.stem.rsplit("_", 1)[0])) for f in sorted((MANUAL / "extents").glob("*_[0-9][0-9][0-9][0-9].geojson"))]
    files += [(f, "Hudson") for f in sorted(DOC.glob("hudson_builtup_[0-9][0-9][0-9][0-9].geojson"))]
    for f, area in files:
        if area is None:
            continue
        year = int(f.stem.rsplit("_", 1)[1])
        polys = []
        for ft in json.load(open(f))["features"]:
            if ft.get("geometry") and ft["properties"].get("kind", "built_up") == "built_up":
                polys.append(shapely.make_valid(shapely.from_geojson(json.dumps(ft["geometry"]))))
        if polys:
            per.setdefault(area, {}).setdefault(year, []).extend(polys)
    out = {}
    for area, ys in per.items():
        out[area] = []
        for year in sorted(ys):
            poly = shapely.union_all(ys[year])
            shapely.prepare(poly)
            out[area].append((year, poly, "usgs" if (area == "Hudson" or year in (1889, 1897)) else "map"))
    _cache["snaps"] = out
    return out


def nycha_bins():
    """BIN -> (completion as a decimal year, development): the housing authority's Development Data
    Book (data/interim/records, the records agent's table; data/research/building_records.md)."""
    if "nycha" not in _cache:
        d = {}
        p = INTERIM / "records" / "records_by_bin.parquet"
        if p.exists():
            for b, y, nme in con().execute(f"select bin, y, rname from '{p}' where src = 'nycha' and y is not null").fetchall():
                d[int(b)] = (float(y), str(nme).replace("NYCHA ", "").strip())
        _cache["nycha"] = d
    return _cache["nycha"]


def parks():
    """(STRtree of the city's park properties in lon / lat, acquisition year or NaN, name)."""
    if "parks" not in _cache:
        geoms, yrs, names = [], [], []
        p = RAW / "nyc" / "parks_properties.geojson"
        if p.exists():
            for ft in json.load(open(p))["features"]:
                if not ft.get("geometry"):
                    continue
                pr = ft["properties"]
                ad = str(pr.get("acquisitiondate") or "")
                y = float("nan")
                if len(ad) >= 7 and ad[:4].isdigit() and 1600 < int(ad[:4]) < 2030:
                    y = int(ad[:4]) + (int(ad[5:7]) - 0.5) / 12.0
                geoms.append(shapely.make_valid(shapely.from_geojson(json.dumps(ft["geometry"]))))
                yrs.append(y)
                names.append(str(pr.get("signname") or pr.get("name311") or "park"))
        geoms = np.array(geoms, dtype=object)
        _cache["parks"] = (shapely.STRtree(geoms) if len(geoms) else None, np.array(yrs), np.array(names, dtype=object))
    return _cache["parks"]


def motorways():
    """(STRtree of motorway centre lines in pixels, opening year, name): Overture geometry, years from
    roads.py (data/interim/roads/highway_years.csv - the researched openings of data/manual/routes.csv
    carried onto the segments). Tunnels are left out."""
    if "mw" not in _cache:
        p = INTERIM / "roads" / "highway_years.csv"
        tree, yrs, names = None, np.array([]), np.array([], dtype=object)
        if p.exists():
            hy = pd.read_csv(p, usecols=["id", "name", "class", "year"])
            hy = hy[(hy["class"] == "motorway") & hy.year.notna()].drop_duplicates("id").set_index("id")
            rows = con().execute(f"""select id, ST_AsWKB(geometry) from '{OVERTURE}/freeways.parquet'
                where class = 'motorway' and coalesce(cast(road_flags as varchar), '') not like '%is_tunnel%'""").fetchall()
            rows = [r for r in rows if r[0] in hy.index]
            if rows:
                g = to_px(shapely.from_wkb([bytes(r[1]) for r in rows]))
                ids = [r[0] for r in rows]
                yrs = hy.year.reindex(ids).values.astype(float)
                names = np.array([n if isinstance(n, str) and n else "motorway" for n in hy.name.reindex(ids).values], dtype=object)
                tree = shapely.STRtree(g)
        _cache["mw"] = (tree, yrs, names)
    return _cache["mw"]


def pick_years(Yk, lo, hi, u):
    """One year per row from the K candidate years of its neighbours that lie in (lo, hi]; NaN if none."""
    ok = (Yk > lo[:, None]) & (Yk <= hi[:, None])
    cnt = ok.sum(1)
    r = np.minimum((u * cnt).astype(int), np.maximum(cnt - 1, 0))
    pick = (np.cumsum(ok, 1) == (r + 1)[:, None]) & ok
    y = Yk[np.arange(len(Yk)), pick.argmax(1)].astype(float)
    y[cnt == 0] = np.nan
    return y


# ----------------------------------------------------------------------------- how much a built-up extent says about one lot
def coverages():
    """[(map year, prepared polygon, layer)] of the traced atlas layers (data/manual/atlas/*_coverage.geojson)."""
    if "cov" not in _cache:
        out = []
        for f in sorted((MANUAL / "atlas").glob("*_coverage.geojson")):
            layer = f.stem[:-len("_coverage")]
            if not layer[-4:].isdigit():
                continue
            polys = [shapely.make_valid(shapely.from_geojson(json.dumps(ft["geometry"])))
                     for ft in json.load(open(f))["features"] if ft.get("geometry")]
            if polys:
                poly = shapely.union_all(polys)
                shapely.prepare(poly)
                out.append((int(layer[-4:]), poly, layer))
        _cache["cov"] = out
    return _cache["cov"]


def calibrate_block(job):
    """Where a traced atlas shows what really stood: of the lots inside a built-up extent (a snapshot
    within 10 years of the atlas) on which the map's building dates from 5 years or more after the
    atlas (and before 1927), how many carried a building in the atlas? {layer: [lots, with a building]}."""
    from scipy.spatial import cKDTree
    bx, by = job
    res = {}
    lp = lots_path(bx, by)
    if not lp.exists():
        return res
    x0, y0, x1, y1 = block_px(bx, by)
    lo0, la1 = px_to_lonlat(x0, y0)
    lo1, la0 = px_to_lonlat(x1, y1)
    box = shapely.box(lo0, la0, lo1, la1)
    covs = [c for c in coverages() if shapely.intersects(c[1], box)]
    if not covs:
        return res
    lots = pd.read_parquet(lp)
    ex = existing_window(bx, by)
    if not len(lots) or not len(ex):
        return res
    n = len(lots)
    g = to_px(shapely.from_wkb(lots.wkb.values))
    cen = shapely.get_coordinates(shapely.centroid(g))
    exc = shapely.get_coordinates(shapely.centroid(ex.g.values))
    area = ex.boro.values[cKDTree(exc).query(cen)[1]].astype(object)
    li, ei = shapely.STRtree(ex.g.values).query(g, predicate="intersects")
    ia = shapely.area(shapely.intersection(g[li], ex.g.values[ei])) * MPP2
    ba = shapely.area(ex.g.values[ei]) * MPP2
    k = (ia > 0.5) & ~((ba <= SMALL_SHARE * (shapely.area(g) * MPP2)[li]) & (ba <= SMALL_M2))
    li, ei = li[k], ei[k]
    ps, pe = ex.start_year.values[ei], ex.end_year.values[ei]
    src = ex.year_src.values[ei].astype(str)
    traced = np.array([s_.split("_")[0] in ("traced", "atlas", "map") and s_[-4:].isdigit() for s_ in src])
    snaps = snapshots()
    lon, lat = lots.lon.values, lots.lat.values
    for ya, poly, layer in covs:
        ins = shapely.contains_xy(poly, lon, lat)
        T = ya + 0.5
        alive = (ps <= T) & (pe > T)
        if not ins.any() or (alive & traced & np.array([s_.endswith(str(ya)) for s_ in src])).sum() < 20:
            continue                                 # the layer is not in the map (yet)
        inext = np.zeros(n, bool)
        for ar in np.unique(area[ins]):
            for year, epoly, _ in snaps.get(ar, []):
                if abs(year - ya) <= 10:
                    inext |= (area == ar) & shapely.contains_xy(epoly, lon, lat)
        other = np.zeros(n, bool)
        other[li[alive & ~traced]] = True
        pred = np.zeros(n, bool)
        pred[li[alive & traced]] = True
        nxt = np.zeros(n, bool)
        nxt[li[(ps > T + 5) & (ps <= PHOTO_T[1924] + AFTER_GAP)]] = True
        elig = ins & inext & ~other & nxt
        for ar in np.unique(area[elig]):
            res[f"{layer}|{ar}"] = [int((elig & (area == ar)).sum()), int((elig & pred & (area == ar)).sum())]
    return res


def calibrate_extents(jobs, workers=3):
    """EXTENT_KEEP from the traced atlases (see calibrate_block); kept as it is where fewer than 300 lots can be judged."""
    from multiprocessing import Pool
    tot = {}
    _fresh_connection()
    with Pool(workers, initializer=_fresh_connection, maxtasksperchild=20) as pool:
        for r in pool.imap_unordered(calibrate_block, jobs):
            for layer, (a, b) in r.items():
                t = tot.setdefault(layer, [0, 0])
                t[0] += a
                t[1] += b
    n_, p_ = sum(v[0] for v in tot.values()), sum(v[1] for v in tot.values())
    if n_ >= 300:
        EXTENT_KEEP["all"] = round(p_ / n_, 3)             # areas without a traced atlas: all atlases together
    per = {}
    for key_, (a, b) in tot.items():
        t = per.setdefault(key_.split("|")[1], [0, 0])
        t[0] += a
        t[1] += b
    for ar, (a, b) in per.items():
        if a >= 300:
            EXTENT_KEEP[ar] = round(b / a, 3)
    (WORK / "extent_keep.json").write_text(json.dumps({"layers": tot, "lots": n_, "with_a_building_in_the_atlas": p_,
                                                       "share_used": EXTENT_KEEP}, indent=1))
    log(f"assemble: built-up extents against the traced atlases: {tot}; share of the lots kept under an extent: {EXTENT_KEEP}")


# ----------------------------------------------------------------------------- evidence -> rows
ROW_COLS = ["id", "start_year", "end_year", "height_m", "storeys", "material", "evidence", "end_basis", "area",
            "cid", "kind", "next_exact", "next_start", "t_ev", "p1924", "p1951", "lon", "lat", "wkb"]


def rows_path(bx, by):
    return ROWS / f"{bx}_{by}.parquet"


def assemble_block(job):
    """The rows of one z14 block and its counts."""
    from scipy.spatial import cKDTree
    import ground_rule
    bx, by = job
    st = {"lots": 0}
    lp = lots_path(bx, by)
    empty = pd.DataFrame(columns=ROW_COLS)
    if not lp.exists():
        return empty, st
    lots = pd.read_parquet(lp)
    ex = existing_window(bx, by)
    if not len(lots) or not len(ex):
        return empty, st
    n = len(lots)
    st["lots"] = n
    gll = shapely.from_wkb(lots.wkb.values)
    g = to_px(gll)
    cen = shapely.get_coordinates(shapely.centroid(g))
    exc = shapely.get_coordinates(shapely.centroid(ex.g.values))
    es, ee = ex.start_year.values, ex.end_year.values
    _, j = cKDTree(exc).query(cen)
    area = ex.boro.values[j].astype(object)          # borough / county of the nearest building of the map
    cid = lots.cid.values
    # the pairs lot x building of the map that share ground (more than half a square metre)
    li, ei = shapely.STRtree(ex.g.values).query(g, predicate="intersects")
    ia = shapely.area(shapely.intersection(g[li], ex.g.values[ei])) * MPP2
    k = ia > 0.5
    li, ei = li[k], ei[k]
    ps, pe = es[ei], ee[ei]
    pstand = pe == 9999
    la = shapely.area(g) * MPP2
    # a building much smaller than the lot (a shed, a shanty of an early atlas) does not take the lot:
    # the row is cut around it. Anything larger blocks the lot while it stands.
    ba = shapely.area(ex.g.values[ei]) * MPP2
    minor = (ba <= SMALL_SHARE * la[li]) & (ba <= SMALL_M2)

    def window(T, gap):
        """Per lot at time T: free (no building of the map on it, none starting within `gap` after),
        a = end of the last building before T, b = start of the next one, and whether that stands today."""
        free = np.ones(n, bool)
        free[li[(ps <= T + gap) & (pe > T) & ~minor]] = False
        a = np.full(n, -np.inf)
        m = pe <= T
        np.maximum.at(a, li[m], pe[m])
        b = np.full(n, np.inf)
        m = ps > T + gap
        np.minimum.at(b, li[m], ps[m])
        bst = np.zeros(n, bool)
        mm = m & (ps == b[li])
        np.logical_or.at(bst, li[mm], pstand[mm])
        return free, a, b, bst

    r_near = NEAR_M / MPP
    W, stood, openg, ctx = {}, {}, {}, {}
    for Y in ap.YEARS:
        T = PHOTO_T[Y]
        W[Y] = window(T, AFTER_GAP)
        p = lots[f"p{Y}"].values.astype(float)
        nyc = area != "Hudson"
        # The model's p is calibrated for even odds beforehand. What the photograph shows around a lot
        # says more. The odds beforehand are taken from the other FREE lots within NEAR_M (lots the map
        # leaves empty): built by a clear call, open by a clear call, or without a call (counted as half
        # open). Lots that carry a map building say nothing here - where the map is complete, the free
        # lots between its buildings are the gardens. No free lot around: even odds, the model's own
        # rule. In a row of free lots that the photograph shows built, a lot with an inconclusive score
        # is taken as built; among open ground a lot needs p >= 0.94.
        alive = (es <= T + AFTER_GAP) & (ee > T)
        clear_b = W[Y][0] & (p >= P_STOOD[Y])
        clear_o = W[Y][0] & (p <= P_OPEN[Y])
        scored = W[Y][0] & np.isfinite(p) & ~clear_b & ~clear_o

        def around(m_):
            return cKDTree(cen[m_]).query_ball_point(cen, r_near, return_length=True) - m_.astype(int) if m_.any() else np.zeros(n, int)
        tb, to, tn = around(clear_b), around(clear_o), around(scored)
        prior = np.clip((tb + 1.25) / (tb + to + 0.5 * tn + 2.5), PRIOR_RANGE[0], PRIOR_RANGE[1])
        with np.errstate(invalid="ignore", divide="ignore"):
            post = prior * p / (prior * p + (1 - prior) * (1 - p))
        s = W[Y][0] & (post >= np.where(area == "5", P_STATEN, P_STOOD[Y])) & nyc & (W[Y][1] <= T - BEFORE_GAP)
        lonely = W[Y][0] & (p >= P_STOOD[Y]) & nyc & ~s
        # open country: where neither a built-up snapshot nor the map's own buildings say that anything
        # stood around, the photograph alone is not believed (trees and gardens read as roofs)
        near_map = cKDTree(exc[alive]).query_ball_point(cen, CONTEXT_M / MPP, return_length=True) if alive.any() else np.zeros(n, int)
        ctx[Y] = near_map >= CONTEXT_N
        st[f"by_row{Y}"] = int((s & ~(p >= P_STOOD[Y])).sum())
        stood[Y] = s
        openg[Y] = (p <= P_OPEN[Y]) & nyc
        cov = W[Y][0] & np.isfinite(p) & nyc
        st[f"free{Y}"] = int(W[Y][0].sum())
        st[f"scored{Y}"] = int(cov.sum())
        st[f"stood{Y}"] = int(stood[Y].sum())
        st[f"alone{Y}"] = int(lonely.sum())
        st[f"open{Y}"] = int((cov & openg[Y]).sum())
        st[f"nocall{Y}"] = int((cov & ~openg[Y] & ~stood[Y]).sum())
        st[f"nophoto{Y}"] = int((W[Y][0] & ~np.isfinite(p) & nyc).sum())
        # the model on lots where the answer is known (reported, not used)
        kn = np.zeros(n, bool)
        mk = ~minor & (ps <= Y - 3) & (pe > T) & (ex.year_confidence.values[ei] == "exact") & (ia[k] >= 0.5 * la[li])
        kn[li[mk]] = True
        kn &= np.isfinite(p) & nyc
        st[f"known{Y}_n"] = int(kn.sum())
        st[f"known{Y}_built"] = int((kn & (post >= P_STOOD[Y])).sum())
        st[f"known{Y}_built_raw"] = int((kn & (p >= P_STOOD[Y])).sum())
        st[f"known{Y}_open"] = int((kn & (p <= P_OPEN[Y])).sum())
        ptree_, pyrs_, _ = parks()
        if ptree_ is not None:
            a_, b_ = ptree_.query(shapely.points(lots.lon.values, lots.lat.values), predicate="within")
            inp = np.zeros(n, bool)
            inp[a_[pyrs_[b_] <= Y - 5]] = True
            touched = np.zeros(n, bool)
            touched[li[(ps <= T + 30) & (pe > T - 30)]] = True
            inp &= ~touched & np.isfinite(p) & nyc
            st[f"park{Y}_n"] = int(inp.sum())
            st[f"park{Y}_built"] = int((inp & (post >= P_STOOD[Y])).sum())
            st[f"park{Y}_built_raw"] = int((inp & (p >= P_STOOD[Y])).sum())
            st[f"park{Y}_open"] = int((inp & (p <= P_OPEN[Y])).sum())
    f24, a24, b24, bst24 = W[1924]
    f51, a51, b51, bst51 = W[1951]
    T51 = PHOTO_T[1951]
    same = f24 & f51 & (b24 > T51 + AFTER_GAP)       # one gap of the map spans both photographs

    # extent bounds per lot
    snaps = snapshots()
    ext_lo = np.full(n, -np.inf)
    ext_hi = np.full(n, np.nan)
    contained = {}
    for ar in np.unique(area):
        sel = np.flatnonzero(area == ar)
        for year, poly, cls in snaps.get(ar, []):
            ins = shapely.contains_xy(poly, lots.lon.values[sel], lots.lat.values[sel])
            contained[(ar, year)] = sel[ins]
            first = ins & np.isnan(ext_hi[sel])
            ext_hi[sel[first]] = year
            out_before = ~ins & np.isnan(ext_hi[sel])
            ext_lo[sel[out_before]] = year

    for Y in ap.YEARS:
        no_ctx = stood[Y] & ~ctx[Y] & ~np.isfinite(ext_hi)
        st[f"no_context{Y}"] = int(no_ctx.sum())
        stood[Y] &= ~no_ctx
        st[f"stood{Y}"] = int(stood[Y].sum())

    parts = []          # (lot index, anchor, evidence, start lo, start hi, hard end, next stands, mode)

    def add(m, anchor, ev, lo, hi, b, bst, mode):
        i = np.flatnonzero(m)
        if len(i):
            parts.append(pd.DataFrame({"i": i, "anchor": anchor, "evidence": ev, "s_lo": np.broadcast_to(lo, n)[i],
                                       "s_hi": np.broadcast_to(hi, n)[i], "b": b[i], "bst": bst[i], "mode": mode}))

    s24, s51 = stood[1924], stood[1951]
    lo24 = np.maximum(a24, ext_lo)
    add(s24 & same & s51, "24", "aerial1924+1951", lo24, 1923.5, b51, bst51, "after51")
    add(s24 & same & ~s51 & openg[1951], "24", "aerial1924", lo24, 1923.5, b51, bst51, "between")
    add(s24 & same & ~s51 & ~openg[1951], "24", "aerial1924", lo24, 1923.5, b51, bst51, "after51")
    add(s24 & ~same, "24", "aerial1924", lo24, 1923.5, b24, bst24, "replaced")
    only51 = s51 & ~(s24 & same)
    after24 = np.where(s24 & ~same, b24, -np.inf)         # the lot's 1924 row ended when that building went up
    add(only51 & same & openg[1924], "51", "aerial1951", np.maximum(a51, PHOTO_T[1924] + 0.5), 1950.5, b51, bst51, "after51")
    add(only51 & ~(same & openg[1924]), "51", "aerial1951", np.maximum(np.maximum(a51, ext_lo), after24), 1950.5, b51, bst51, "after51")

    # Hudson County: the block fronts of the 1947 sheets
    ip = INK / f"{bx}_{by}.parquet"
    hud = area == "Hudson"
    if hud.any() and ip.exists():
        inkdf = pd.read_parquet(ip).set_index("cid")
        ink = inkdf.ink1947.reindex(cid).values.astype(float)
        sheet_year = inkdf.sheet_year.reindex(cid).fillna(0).values.astype(int)
        fH, aH, bH, bstH = window(INK_T, INK_GAP)
        sH = hud & fH & (ink >= INK_MIN) & (aH <= INK_T - BEFORE_GAP)
        alive = (es <= INK_T + INK_GAP) & (ee > INK_T)
        na = cKDTree(exc[alive]).query_ball_point(cen, r_near, return_length=True) if alive.any() else np.zeros(n, int)
        nl = cKDTree(cen[sH]).query_ball_point(cen, r_near, return_length=True) - sH.astype(int) if sH.any() else np.zeros(n, int)
        lonelyH = sH & ((na + nl) < 2)
        sH &= ~lonelyH
        st["hudson_free1941"] = int((hud & fH & np.isfinite(ink)).sum())
        knH = np.zeros(n, bool)                     # lots under a map building recorded by 1935: does the sheet show them?
        mk = ~minor & (ps <= 1935) & (pe > INK_T) & (ex.year_confidence.values[ei] == "exact") & (ia[k] >= 0.5 * la[li])
        knH[li[mk]] = True
        knH &= hud & np.isfinite(ink)
        st["hudson_known_n"] = int(knH.sum())
        st["hudson_known_ink"] = int((knH & (ink >= INK_MIN)).sum())
        st["hudson_ink_built"] = int(sH.sum())
        st["hudson_ink_alone"] = int(lonelyH.sum())
        st["hudson_ink_open"] = int((hud & fH & (ink < INK_MIN)).sum())
        for sy in np.unique(sheet_year[sH]):
            add(sH & (sheet_year == sy), "47", f"usgs{sy}_blocks", np.maximum(aH, ext_lo), 1939.5, bH, bstH, "snap")
        covered47 = sH
    else:
        covered47 = np.zeros(n, bool)

    # built-up extents: a lot inside the built-up ground of a snapshot, free then, whose gap in the map
    # closes before the first photograph (the boroughs) - for Hudson County, any gap
    seen_b = {}
    for (ar, year), idx in contained.items():
        if not len(idx):
            continue
        cls = [c for y, _, c in snaps[ar] if y == year][0]
        fE, aE, bE, bstE = window(year + 0.5, 5.0)
        m = np.zeros(n, bool)
        m[idx] = True
        m &= fE
        if ar != "Hudson":
            m &= bE <= PHOTO_T[1924] + AFTER_GAP
        else:
            m &= bE <= INK_T + INK_GAP              # as in the boroughs: only gaps that close before the lot-level evidence
        m &= aE <= year - 1.0
        m &= hvec(cid, "keep") < EXTENT_KEEP.get(ar, EXTENT_KEEP["all"]) if m.any() else m
        for i in np.flatnonzero(m):                 # one row per gap: the first snapshot that shows it
            if seen_b.get(int(i)) == bE[i]:
                m[i] = False
            else:
                seen_b[int(i)] = bE[i]
        prev = [y for y, _, _ in snaps[ar] if y < year]
        lo = np.maximum(aE, np.where(ext_hi == year, ext_lo, prev[-1] if prev else -np.inf))
        ev = f"usgs{year}_builtup" if ar == "Hudson" else f"extent{year}"
        add(m, f"x{year}", ev, lo, float(year), bE, bstE, "replaced" if ar != "Hudson" else "snap")
    if not parts:
        return empty, st
    R = pd.concat(parts, ignore_index=True)
    i = R.i.values
    # a photographed lot inside built-up ground of an earlier snapshot: the building seen in the
    # photograph (or one before it on the lot) is taken to stand by that snapshot - for the same share
    # of the lots as under the extent alone, because the snapshots are generalised
    hi_i = ext_hi[i]
    keep_x = hvec(cid[i], "keep") < np.array([EXTENT_KEEP.get(a_, EXTENT_KEEP["all"]) for a_ in area[i]])
    capped = (np.isin(R.anchor.values, ("24", "51", "47")) & np.isfinite(hi_i) & keep_x & (hi_i < R.s_hi.values)
              & (R.s_lo.values < hi_i - 1.0))
    R.loc[capped, "s_hi"] = hi_i[capped]
    R.loc[capped, "evidence"] = [("usgs%d_builtup+%s" if a_ == "Hudson" else "extent%d+%s") % (h_, e_)
                                 for h_, e_, a_ in zip(hi_i[capped], R.evidence.values[capped], area[i][capped])]
    key = np.array([f"{c}:{a}" for c, a in zip(cid[i], R.anchor.values)], dtype=object)
    u1, u2, u3, u4 = hvec(key, "s"), hvec(key, "j"), hvec(key, "e"), hvec(key, "h")
    T_ev = np.where(R.anchor.values == "24", PHOTO_T[1924], np.where(R.anchor.values == "51", T51,
                    np.where(R.anchor.values == "47", INK_T, R.s_hi.values + 0.5)))
    kind = lots.kind.values[i]

    # ---- start: spread back from the evidence over the recorded years around
    lo, hi = R.s_lo.values.astype(float), R.s_hi.values.astype(float)
    start = np.full(len(R), np.nan)
    for pool in ((ex.year_confidence.values == "exact") & (es > 1600), (ex.year_confidence.values != "procedural") & (es > 1600)):
        if pool.sum() < 1:
            continue
        K = min(24, int(pool.sum()))
        d, jj = cKDTree(exc[pool]).query(cen[i], k=K, distance_upper_bound=YEAR_POOL_M / MPP)
        d, jj = d.reshape(len(i), K), jj.reshape(len(i), K)
        Yk = np.where(np.isfinite(d), es[pool][np.minimum(jj, pool.sum() - 1)], np.nan)
        y = pick_years(Yk, lo, hi, u1)
        start = np.where(np.isnan(start), y, start)
    fb = hi - u1 * np.minimum(30.0, hi - lo)                    # nothing recorded around: the 30 years before the evidence
    start = np.where(np.isnan(start), fb, start)
    start = start + 3.0 * (u2 - 0.5)                              # recorded years leave out the placeholder years: +-1.5
    start = np.where(start > hi, 2 * hi - start, start)           # never after the evidence
    start = np.maximum(start, np.maximum(lo + 0.2, 1626.0))        # never before the lot is free
    start = np.minimum(start, np.maximum(hi, lo + 0.2))

    # ---- height (needed by the ground rule), then nothing before its ground
    storeys = np.array([TYPES[kd]["st"][int(h * len(TYPES[kd]["st"])) % len(TYPES[kd]["st"])] for kd, h in zip(kind, u4)], float)
    early = start < 1880
    storeys = np.where(early & (kind == "tenement"), np.minimum(storeys, 5), storeys)
    height = np.where(kind == "frame", storeys * 3.0 + 1.5, storeys * 3.3 + 1.0)
    material = np.array([TYPES[kd]["mat"] for kd in kind], dtype=object)
    gr = ground_rule.earliest_start(gll[i], height)
    waits = np.isfinite(gr) & (gr > start)
    start = np.where(waits, gr, start)
    st["waits_for_ground"] = int(waits.sum())

    # ---- end
    b = R.b.values.astype(float)
    lead = LEAD[0] + (LEAD[1] - LEAD[0]) * u3
    end = np.where(np.isfinite(b), b - lead, np.nan)
    basis = np.where(np.isfinite(b), np.where(R.bst.values, "replaced_by_standing", "replaced_by_vanished"), "").astype(object)
    mode = R["mode"].values
    # clearance records
    rec_end = np.full(len(R), np.nan)
    rec_basis = np.full(len(R), "", dtype=object)
    park_year = np.full(len(R), np.nan)
    ptree, pyrs, pnames = parks()
    if ptree is not None:
        a_, b_ = ptree.query(shapely.points(lots.lon.values[i], lots.lat.values[i]), predicate="within")
        park_year[a_] = pyrs[b_]
        okp = np.isfinite(pyrs[b_])
        rec_end[a_[okp]] = pyrs[b_][okp] + 0.3 + 1.5 * u3[a_[okp]]
        rec_basis[a_[okp]] = ["park:" + s_ for s_ in pnames[b_][okp]]
    mtree, myrs, mnames = motorways()
    if mtree is not None:
        a_, b_ = mtree.query_nearest(shapely.points(cen[i]), max_distance=25.0 / MPP, all_matches=False)
        rec_end[a_] = myrs[b_] - 1.5 - 2.0 * u3[a_]
        rec_basis[a_] = ["highway:" + s_ for s_ in mnames[b_]]
    nb = nycha_bins()
    isn = np.array([int(v) in nb if np.isfinite(v) else False for v in ex.bin.values.astype(float)]) & (ee == 9999)
    if isn.any():
        lines, _ = streets_window(bx, by)
        streets = shapely.union_all(lines) if len(lines) else None
        d, jj = cKDTree(exc[isn]).query(cen[i], distance_upper_bound=90.0 / MPP)
        near = np.flatnonzero(np.isfinite(d))
        if len(near):
            src = np.flatnonzero(isn)[jj[near]]
            seg = shapely.linestrings(np.stack([cen[i][near], exc[src]], axis=1))
            if streets is not None:
                shapely.prepare(streets)
                near_ok = ~shapely.intersects(streets, seg)        # the same city block: no street between
            else:
                near_ok = np.ones(len(near), bool)
            near, src = near[near_ok], src[near_ok]
            comp = np.array([nb[int(v)][0] for v in ex.bin.values[src]])
            rec_end[near] = comp - 2.5 - 2.0 * u3[near]
            rec_basis[near] = ["nycha:" + nb[int(v)][1] for v in ex.bin.values[src]]
    # a record counts when it falls after the evidence and before the map's next building
    seen51 = np.array(["1951" in e_ for e_ in R.evidence.values])
    T_min = np.where(seen51, T51, T_ev)                    # the last evidence that shows the row standing
    rec_ok = np.isfinite(rec_end) & (rec_end > T_min + 0.5) & ~(rec_end >= np.where(np.isfinite(end), end, np.inf))
    between = mode == "between"
    rec_ok &= ~between | (rec_end < T51 - 0.5)
    end = np.where(rec_ok, rec_end, end)
    basis = np.where(rec_ok, rec_basis, basis)
    # the photograph of 1951 shows the lot open: gone between the two
    m = between & ~rec_ok
    end = np.where(m, PHOTO_T[1924] + 1.0 + u3 * (T51 - PHOTO_T[1924] - 2.0), end)
    basis = np.where(m, "photo1951_open", basis)
    # the map's next building on the spot dates from after the city's record of removals began: the
    # fill row would be in that record had it stood until then - it went earlier, when is not known
    late = np.isfinite(end) & (end > RECORD_FROM) & (T_ev < RECORD_FROM - 12) & (area[i] != "Hudson")
    end = np.where(late, np.nan, end)
    # nothing on the spot today and no record: when the big building beside it went up, else spread
    m = np.isnan(end)
    if m.any():
        big = (ee == 9999) & (ex.area.values >= 400)
        e2 = np.full(len(R), np.nan)
        if big.any():
            d, jj = cKDTree(exc[big]).query(cen[i], k=min(6, int(big.sum())), distance_upper_bound=60.0 / MPP)
            d, jj = d.reshape(len(i), -1), jj.reshape(len(i), -1)
            ys = np.where(np.isfinite(d), es[big][np.minimum(jj, big.sum() - 1)], np.nan)
            ys = np.where((ys > T_min[:, None] + 3.0) & (ys < RECORD_FROM), ys, np.nan)
            has = np.isfinite(ys).any(1)
            first = np.where(has, np.nanargmin(np.where(np.isfinite(ys), d, np.inf), axis=1), 0)
            e2 = np.where(has, ys[np.arange(len(i)), first] - 1.5 - 1.5 * u3, np.nan)
        lo_e = np.where(T_min >= T51 - 12, OPEN_END[0], T_min + 2.0)      # a row not seen in 1951 may have gone before it
        e3 = lo_e + u3 * np.maximum(OPEN_END[1] - lo_e, 5.0)
        end = np.where(m, np.where(np.isfinite(e2), e2, e3), end)
        basis = np.where(m, "estimated", basis)
    # a park (or a motorway) older than the fill: no row
    drop = np.isfinite(park_year) & (park_year <= T_ev)
    if mtree is not None:
        a_, b_ = mtree.query_nearest(shapely.points(cen[i]), max_distance=12.0 / MPP, all_matches=False)
        on = np.zeros(len(R), bool)
        on[a_] = myrs[b_] <= T_ev[a_]
        drop |= on
    st["in_older_park_or_motorway"] = int(drop.sum())
    rail = rail_window(bx, by)
    if rail is not None:
        on_rail = np.zeros(len(R), bool)
        on_rail[np.unique(rail.query(g[i], predicate="intersects")[0])] = True
        st["on_rail"] = int((on_rail & ~drop).sum())
        drop |= on_rail
    # two rows of one lot never stand at once: the later one starts when the earlier has gone
    o = np.lexsort((start, i))
    for q in range(1, len(o)):
        if i[o[q]] == i[o[q - 1]] and start[o[q]] < end[o[q - 1]] + 0.3:
            start[o[q]] = end[o[q - 1]] + 0.3
    short = ~(end - start >= 1.0)
    st["no_time_left"] = int((short & ~drop).sum())
    keep = ~drop & ~short
    nx = {}
    for l_, s_, c_ in zip(li, ps, ex.year_confidence.values[ei] == "exact"):
        nx[(int(l_), round(float(s_), 3))] = nx.get((int(l_), round(float(s_), 3)), False) or bool(c_)
    next_exact = np.array([nx.get((int(l_), round(float(b_), 3)), False) if np.isfinite(b_) else False for l_, b_ in zip(i, b)])
    # cut the rows around the small buildings that stand on their lots during their time
    gout = g[i].copy()
    row_of = {}
    for r_ in np.flatnonzero(keep):
        row_of.setdefault(int(i[r_]), []).append(r_)
    cutn = 0
    for l_, e_ in zip(li[minor], ei[minor]):
        for r_ in row_of.get(int(l_), ()):
            if es[e_] < end[r_] and ee[e_] > start[r_]:
                gout[r_] = shapely.difference(gout[r_], shapely.buffer(ex.g.values[e_], 0.3 / MPP))
                cutn += 1
    if cutn:
        for r_ in np.flatnonzero(keep):
            gm = gout[r_]
            if gm.geom_type != "Polygon":
                parts_ = [q for q in shapely.get_parts(gm) if q.geom_type == "Polygon"]
                gm = max(parts_, key=lambda q: q.area) if parts_ else None
                gout[r_] = gm
            if gm is None or gm.is_empty or gm.area * MPP2 < NOTCH_MIN * la[i[r_]]:
                keep[r_] = False
    st["notched"] = cutn
    # written years: the start rounded up, the end down (two rows a hundredth of a year apart must not meet)
    start = np.ceil(start * 100 - 1e-6) / 100
    end = np.floor(end * 100 + 1e-6) / 100
    keep &= end - start >= 1.0
    # last guard, on the outlines and years as written: no row shares ground with a map building while both stand
    kk = np.flatnonzero(keep)
    if len(kk):
        gk = np.array([gout[q] for q in kk], dtype=object)
        a_, b_ = shapely.STRtree(ex.g.values).query(gk, predicate="intersects")
        t_ = (start[kk][a_] < ee[b_]) & (es[b_] < end[kk][a_])
        a_, b_ = a_[t_], b_[t_]
        if len(a_):
            ov = shapely.area(shapely.intersection(gk[a_], ex.g.values[b_])) * MPP2 > 0.4
            bad_ = np.unique(a_[ov])
            keep[kk[bad_]] = False
            st["dropped_on_a_map_building"] = int(len(bad_))
    wkb_out = np.array(shapely.to_wkb(to_lonlat(np.array([q if q is not None else shapely.Point() for q in gout], dtype=object))), dtype=object)
    out = pd.DataFrame({
        "id": ["gf" + hashlib.sha1(k_.encode()).hexdigest()[:14] for k_ in key],
        "start_year": start, "end_year": end, "height_m": np.round(height, 1), "storeys": storeys,
        "material": material, "evidence": R.evidence.values, "end_basis": basis, "area": area[i],
        "cid": cid[i], "kind": kind, "next_exact": next_exact, "next_start": b, "t_ev": T_ev, "p1924": lots.p1924.values[i], "p1951": lots.p1951.values[i],
        "lon": lots.lon.values[i], "lat": lots.lat.values[i], "wkb": wkb_out})[keep].reset_index(drop=True)
    return out[ROW_COLS], st


def _assemble_job(job):
    try:
        out, st = assemble_block(job)
    except Exception as e:  # noqa: BLE001
        log(f"assemble: block {job} failed: {type(e).__name__}: {str(e)[:200]}")
        return job, None, {"failed": 1}
    ROWS.mkdir(parents=True, exist_ok=True)
    tmp = rows_path(*job).with_suffix(f".part{os.getpid()}")
    out.to_parquet(tmp, compression="zstd", index=False)
    tmp.rename(rows_path(*job))
    return job, len(out), st


def step_assemble(workers=3, only=None):
    """Evidence -> rows for every block, then one file. Rows are recomputed every time (they depend
    on the snapshot of the map); the lots and their photograph scores are reused."""
    import geopandas as gpd
    from multiprocessing import Pool
    ROWS.mkdir(parents=True, exist_ok=True)
    jobs = only or [(int(p.stem.split("_")[0]), int(p.stem.split("_")[1])) for p in sorted(LOTS.glob("*.parquet"))]
    for p in ROWS.glob("*.parquet"):            # rows of an earlier run (another snapshot, other blocks) must not survive
        p.unlink()
    t0 = time.time()
    total = {}
    calibrate_extents(jobs, workers)
    _fresh_connection()
    with Pool(workers, initializer=_fresh_connection, maxtasksperchild=12) as pool:
        for k, (job, nrows, st) in enumerate(pool.imap_unordered(_assemble_job, jobs)):
            for a, v in st.items():
                total[a] = total.get(a, 0) + v
            if (k + 1) % 25 == 0:
                log(f"assemble: {k + 1}/{len(jobs)} blocks, {time.time() - t0:.0f} s")
    df = pd.concat([pd.read_parquet(p) for p in sorted(ROWS.glob("*.parquet"))], ignore_index=True)
    df = df.drop_duplicates("id").reset_index(drop=True)
    # no two rows on one spot at once, across the whole file (lots of neighbouring blocks, frontage against inner rows)
    gpx = to_px(shapely.from_wkb(df.wkb.values))
    a_, b_ = shapely.STRtree(gpx).query(gpx, predicate="intersects")
    t_ = (a_ < b_) & (df.start_year.values[a_] < df.end_year.values[b_]) & (df.start_year.values[b_] < df.end_year.values[a_])
    a_, b_ = a_[t_], b_[t_]
    ov = shapely.area(shapely.intersection(gpx[a_], gpx[b_])) * MPP2 > 0.4 if len(a_) else np.zeros(0, bool)
    drop_ = np.unique(b_[ov])
    total["dropped_on_another_row"] = int(len(drop_))
    df = df.drop(index=drop_).reset_index(drop=True)
    total["rows"] = len(df)
    (WORK / "stats.json").write_text(json.dumps(total, indent=1))
    geom = shapely.from_wkb(df.wkb.values)
    cols = ["id", "start_year", "end_year", "height_m", "storeys", "material", "evidence", "end_basis", "area"]
    gdf = gpd.GeoDataFrame(df[cols], geometry=geom, crs="EPSG:4326")
    tmp = OUT.with_suffix(".part")
    gdf.to_parquet(tmp, compression="zstd", index=False)
    tmp.rename(OUT)
    log(f"assemble: {len(gdf)} rows -> {OUT} ({OUT.stat().st_size / 1e6:.1f} MB), {time.time() - t0:.0f} s; {total}")


# ----------------------------------------------------------------------------- checks
def _box(lo0, la0, lo1, la1):
    return [(lo0, la0), (lo1, la0), (lo1, la1), (lo0, la1)]


# the test districts of the brief (lon / lat rings, approximate)
DISTRICTS = {
    "Hell's Kitchen (W 34-59, 8 Av - Hudson)": [(-73.9934, 40.7524), (-73.9820, 40.7682), (-73.9940, 40.7737), (-74.0058, 40.7577)],
    "Lincoln Square (W 59-72, west of Broadway)": [(-73.9819, 40.7681), (-73.9815, 40.7788), (-73.9895, 40.7818), (-73.9950, 40.7738)],
    "East Harlem (E 96-125, east of Park Av)": [(-73.9519, 40.7874), (-73.9390, 40.8052), (-73.9290, 40.8010), (-73.9415, 40.7820)],
    "Lower East Side east of Essex St": [(-73.9872, 40.7222), (-73.9898, 40.7150), (-73.9905, 40.7100), (-73.9770, 40.7100), (-73.9740, 40.7195)],
    "South Bronx (Mott Haven, Melrose, Morrisania)": _box(-73.935, 40.800, -73.895, 40.840),
    "Brownsville": _box(-73.925, 40.655, -73.900, 40.675),
    "Williamsburg": _box(-73.970, 40.700, -73.940, 40.722),
    "Downtown Brooklyn / Cadman Plaza": _box(-73.995, 40.688, -73.980, 40.702),
    "Long Island City": _box(-73.960, 40.740, -73.930, 40.758),
    "Stapleton": _box(-74.085, 40.620, -74.070, 40.635),
    "Downtown Jersey City": _box(-74.055, 40.712, -74.030, 40.728),
    "Hoboken": _box(-74.045, 40.735, -74.022, 40.760),
}
CHECK_YEARS = (1880, 1900, 1925, 1950, 1975)


def _check_job(job):
    """Independent re-check of one block's rows against the map: overlaps in time, streets, water."""
    bx, by = job
    rp = rows_path(bx, by)
    res = {"overlap_pairs": 0, "overlap_m2": 0.0, "on_street": 0, "in_water": 0, "self_overlap": 0}
    if not rp.exists():
        return res
    r = pd.read_parquet(rp, columns=["id", "start_year", "end_year", "wkb"])
    if not len(r):
        return res
    g = to_px(shapely.from_wkb(r.wkb.values))
    ex = existing_window(bx, by, cols="start_year, end_year, wkb")
    a, b = shapely.STRtree(ex.g.values).query(g, predicate="intersects")
    t = (r.start_year.values[a] < ex.end_year.values[b]) & (ex.start_year.values[b] < r.end_year.values[a])
    a, b = a[t], b[t]
    if len(a):
        ia = shapely.area(shapely.intersection(g[a], ex.g.values[b])) * MPP2
        res["overlap_pairs"] = int((ia > 0.5).sum())
        res["overlap_m2"] = float(ia[ia > 0.5].sum())
    lines, cls = streets_window(bx, by)
    if len(lines):
        st = shapely.STRtree(shapely.buffer(lines, 5.5 / MPP, cap_style="flat"))
        res["on_street"] = int(len(np.unique(st.query(g, predicate="intersects")[0])))
    water, _ = water_window(bx, by)
    if water is not None and not water.is_empty:
        shapely.prepare(water)
        res["in_water"] = int(shapely.intersects(water, g).sum())
    a, b = shapely.STRtree(g).query(g, predicate="intersects")
    t = (a < b) & (r.start_year.values[a] < r.end_year.values[b]) & (r.start_year.values[b] < r.end_year.values[a])
    if t.any():
        ia = shapely.area(shapely.intersection(g[a[t]], g[b[t]])) * MPP2
        res["self_overlap"] = int((ia > 0.5).sum())
    return res


def step_report(workers=3):
    import geopandas as gpd
    from multiprocessing import Pool
    f = gpd.read_parquet(OUT)
    c = shapely.get_coordinates(shapely.centroid(f.geometry.values))
    f["lon"], f["lat"] = c[:, 0], c[:, 1]
    L = ["# gap_fill.py: checks", "", f"Rows: {len(f)}. Made {time.strftime('%Y-%m-%d %H:%M')} from the snapshot of the map taken "
         f"{time.strftime('%Y-%m-%d %H:%M', time.localtime(EXISTING.stat().st_mtime))}.", ""]
    st = json.loads((WORK / "stats.json").read_text()) if (WORK / "stats.json").exists() else {}

    L += ["## Rows by area and evidence", "", "| area | evidence | rows | median start | median end |", "|---|---|---|---|---|"]
    for (ar, ev), d in f.groupby(["area", "evidence"]):
        L.append(f"| {ar} | {ev} | {len(d)} | {d.start_year.median():.0f} | {d.end_year.median():.0f} |")
    L += ["", "| area | rows |", "|---|---|"] + [f"| {a} | {n} |" for a, n in f.groupby("area").size().items()]
    L += ["", "## What dates the end", "", "| end basis | rows |", "|---|---|"]
    L += [f"| {a} | {n} |" for a, n in f.end_basis.str.split(":").str[0].value_counts().items()]

    L += ["", "## The photographs: lots the map leaves free at the photograph", "",
          "| | 1924 | 1951 |", "|---|---|---|"]
    for lab, key in (("lots free of any map building at the photograph", "free"), ("... with a photograph", "scored"),
                     ("called built (kept)", "stood"), ("... of them on the strength of the row (own score inconclusive)", "by_row"),
                     ("called built by its own score, not kept: alone, or the map's building ended just before", "alone"),
                     ("called built, not kept: open country (no built-up snapshot, no map buildings around)", "no_context"),
                     ("called open ground (rejected)", "open"), ("no call (not filled)", "nocall"), ("no photograph there", "nophoto")):
        L.append(f"| {lab} | {st.get(key + '1924', '')} | {st.get(key + '1951', '')} |")
    L += ["", "The model on lot outlines, against what is known (not used for anything, a check of the transfer from footprints to lots):", "",
          "| lots | n | called built % | called open % |", "|---|---|---|---|"]
    for lab, key in (("under a map building with a recorded year 3+ years before the 1924 photograph", "known1924"),
                     ("in a park older than the 1924 photograph, free of buildings", "park1924"),
                     ("under a map building with a recorded year 3+ years before the 1951 photograph", "known1951"),
                     ("in a park older than the 1951 photograph, free of buildings", "park1951")):
        n_ = st.get(key + "_n", 0)
        if n_:
            L.append(f"| {lab} | {n_} | {100 * st.get(key + '_built', 0) / n_:.1f} | {100 * st.get(key + '_open', 0) / n_:.1f} |")
    rws = pd.concat([pd.read_parquet(p_, columns=["end_basis", "next_exact", "next_start", "t_ev", "evidence"]) for p_ in sorted(ROWS.glob("*.parquet"))], ignore_index=True)
    same = (rws.end_basis == "replaced_by_standing") & ~rws.next_exact & (rws.next_start - rws.t_ev <= 15) & rws.evidence.str.contains("aerial")
    L += ["", f"Dropped at the last guard: {st.get('dropped_on_a_map_building', 0)} rows on a map building, {st.get('dropped_on_another_row', 0)} on another row."]
    L += ["", f"Rows of the photographs that end under a standing building whose own year is an estimate within 15 years after the "
          f"photograph (the photograph may show that very building): {int(same.sum())} of {int(rws.evidence.str.contains('aerial').sum())}.",
          "", f"Hudson County, the 1940s sheets: lots free in 1941 with a reading {st.get('hudson_free1941', 0)}, heavy ink (kept) "
          f"{st.get('hudson_ink_built', 0)}, heavy ink but alone (dropped) {st.get('hudson_ink_alone', 0)}, no ink {st.get('hudson_ink_open', 0)}. "
          f"Lots under a map building recorded by 1935: {st.get('hudson_known_n', 0)}, of them with heavy ink "
          f"{st.get('hudson_known_ink', 0)}.", "",
          f"Dropped rows: in a park or on a motorway older than the evidence {st.get('in_older_park_or_motorway', 0)}, on a railway "
          f"{st.get('on_rail', 0)}, no time left between start and end {st.get('no_time_left', 0)}. Rows that wait for their ground "
          f"(start moved later by ground_rule): {st.get('waits_for_ground', 0)}. Cuts around small map buildings: {st.get('notched', 0)}.", ""]

    # districts
    L += ["## Test districts: buildings standing on the map, before -> after the fill", "",
          "| district | " + " | ".join(str(y) for y in CHECK_YEARS) + " | fill rows by evidence |", "|---|" + "---|" * (len(CHECK_YEARS) + 1)]
    for name, ring in DISTRICTS.items():
        poly = shapely.Polygon(ring)
        lo0, la0, lo1, la1 = poly.bounds
        e = con().execute(f"""select lon, lat, start_year, end_year from '{EXISTING}'
            where lon >= {lo0} and lon <= {lo1} and lat >= {la0} and lat <= {la1}""").fetchdf()
        e = e[shapely.contains_xy(poly, e.lon.values, e.lat.values)]
        d = f[(f.lon >= lo0) & (f.lon <= lo1) & (f.lat >= la0) & (f.lat <= la1)]
        d = d[shapely.contains_xy(poly, d.lon.values, d.lat.values)]
        cells = []
        for y in CHECK_YEARS:
            b_ = int(((e.start_year <= y) & (e.end_year > y)).sum())
            a_ = int(((d.start_year <= y) & (d.end_year > y)).sum())
            cells.append(f"{b_} -> {b_ + a_}")
        ev = ", ".join(f"{k} {v}" for k, v in d.evidence.value_counts().items())
        L.append(f"| {name} | " + " | ".join(cells) + f" | {ev} |")

    # counts against the census
    L += ["", "## Against the census (an upper check)", "", "Buildings standing (map + fill) and persons per building.", "",
          "| area | year | population | map | fill | persons per building before -> after |", "|---|---|---|---|---|---|"]
    pops = {}
    for p in (TABLES / "population.csv", TABLES / "population_counties.csv"):
        if p.exists():
            t = pd.read_csv(p)
            for ar, d in t.groupby(t.area.astype(str).str.lower().str.strip()):
                pops[ar] = (pd.to_numeric(d.year, errors="coerce").values, pd.to_numeric(d.population.astype(str).str.replace(",", ""), errors="coerce").values)
    names = {"1": "manhattan", "2": "bronx", "3": "brooklyn", "4": "queens", "5": "staten_island", "Hudson": "hudson"}
    ex_counts = {}
    for ar in names:
        for y in (1880, 1900, 1920, 1950):
            ex_counts[(ar, y)] = con().execute(f"select count(*) from '{EXISTING}' where boro = '{ar}' and start_year <= {y} and end_year > {y}").fetchone()[0]
    for ar, nm in names.items():
        if nm not in pops:
            continue
        py, pv = pops[nm]
        ok = np.isfinite(py) & np.isfinite(pv)
        for y in (1880, 1900, 1920, 1950):
            if ok.sum() < 2 or y < py[ok].min():
                continue
            pop = float(np.interp(y, py[ok][np.argsort(py[ok])], pv[ok][np.argsort(py[ok])]))
            m_ = ex_counts[(ar, y)]
            a_ = int(((f["area"] == ar) & (f.start_year <= y) & (f.end_year > y)).sum())     # f.area is geopandas' own
            L.append(f"| {nm} | {y} | {pop:,.0f} | {m_} | {a_} | {pop / max(m_, 1):.1f} -> {pop / max(m_ + a_, 1):.1f} |")

    # invariants
    jobs = [(int(p.stem.split("_")[0]), int(p.stem.split("_")[1])) for p in sorted(ROWS.glob("*.parquet"))]
    tot = {}
    _fresh_connection()
    with Pool(workers, initializer=_fresh_connection, maxtasksperchild=20) as pool:
        for r in pool.imap_unordered(_check_job, jobs):
            for k, v in r.items():
                tot[k] = tot.get(k, 0) + v
    gpx = to_px(f.geometry.values)
    a_, b_ = shapely.STRtree(gpx).query(gpx, predicate="intersects")
    t_ = (a_ < b_) & (f.start_year.values[a_] < f.end_year.values[b_]) & (f.start_year.values[b_] < f.end_year.values[a_])
    tot["self_overlap"] = int((shapely.area(shapely.intersection(gpx[a_[t_]], gpx[b_[t_]])) * MPP2 > 0.5).sum()) if t_.any() else 0
    sy = np.floor(f.start_year.values).astype(int)
    ey = np.floor(f.end_year.values).astype(int)
    sc, ec = pd.Series(sy).value_counts(), pd.Series(ey).value_counts()
    L += ["", "## Invariants (recomputed from the written rows, block by block)", "",
          f"- rows that share ground (> 0.5 m2) with a building of the map while both stand: **{tot.get('overlap_pairs', 0)}** pairs ({tot.get('overlap_m2', 0):.0f} m2)",
          f"- rows that share ground (> 0.5 m2) with another row while both stand, whole file: **{tot.get('self_overlap', 0)}** pairs",
          f"- rows within 5.5 m of a street centre line of today: **{tot.get('on_street', 0)}**",
          f"- rows on today's water: **{tot.get('in_water', 0)}**",
          f"- rows with start >= end: **{int((f.start_year >= f.end_year).sum())}**; shorter than a year: {int((f.end_year - f.start_year < 1).sum())}",
          f"- duplicate ids: **{int(f.id.duplicated().sum())}**",
          f"- most rows starting in one year: {int(sc.iloc[0])} ({int(sc.index[0])}); next: " + ", ".join(f"{int(v)} ({int(k)})" for k, v in sc.iloc[1:5].items()),
          f"- most rows ending in one year: {int(ec.iloc[0])} ({int(ec.index[0])}); next: " + ", ".join(f"{int(v)} ({int(k)})" for k, v in ec.iloc[1:5].items()),
          f"- start years: 5 % {np.percentile(f.start_year, 5):.0f}, median {f.start_year.median():.0f}, 95 % {np.percentile(f.start_year, 95):.0f}; "
          f"end years: 5 % {np.percentile(f.end_year, 5):.0f}, median {f.end_year.median():.0f}, 95 % {np.percentile(f.end_year, 95):.0f}",
          f"- standing rows by year: " + ", ".join(f"{y}: {int(((f.start_year <= y) & (f.end_year > y)).sum())}" for y in (1850, 1880, 1900, 1925, 1950, 1975, 2000)), ""]
    (WORK / "report.md").write_text("\n".join(L))
    print("\n".join(L))


# ----------------------------------------------------------------------------- looking at it
def step_look(lon, lat, name="look", half_m=170.0, rows=None):
    """Thumbnails of both photographs around a point, lots drawn: green = the model says a building
    stood (p >= threshold), red = open (p <= threshold), yellow = no call; blue = the map's own
    buildings alive that year. With `rows` (the assembled rows of the block) the kept rows are
    drawn thick. Written to data/interim/gapfill/look/<name>_<year>.png."""
    from PIL import Image, ImageDraw
    x, y = ap.lonlat_to_pixel(lon, lat)
    bx, by = int(x // (NB * TILE)), int(y // (NB * TILE))
    lp = lots_path(bx, by)
    if not lp.exists():
        do_block((bx, by))
    lots = pd.read_parquet(lp)
    g = to_px(shapely.from_wkb(lots.wkb.values)) if len(lots) else np.array([], dtype=object)
    ex = existing_window(bx, by)
    kept = None
    rp = ROWS / f"{bx}_{by}.parquet"
    if rp.exists():
        kept = pd.read_parquet(rp)
    (WORK / "look").mkdir(parents=True, exist_ok=True)
    h = int(half_m / MPP)
    S = 3
    outs = []
    for year in ap.YEARS:
        blk = ap.load_block(year, bx, by)
        if blk is None:
            continue
        img, valid, x0, y0 = blk
        cx, cy = int(x - x0), int(y - y0)
        a0, b0 = max(cx - h, 0), max(cy - h, 0)
        crop = np.clip(img[b0:cy + h, a0:cx + h], 0, 255).astype("uint8")
        im = Image.fromarray(crop).convert("RGB").resize((crop.shape[1] * S, crop.shape[0] * S), Image.BICUBIC)
        dr = ImageDraw.Draw(im)
        org = np.array([x0 + a0, y0 + b0], "float64")
        box = shapely.box(org[0], org[1], org[0] + crop.shape[1], org[1] + crop.shape[0])

        def draw(geom, col, width=1):
            for part in shapely.get_parts(geom):
                if part.geom_type != "Polygon":
                    continue
                c = (np.asarray(part.exterior.coords) - org) * S
                dr.line([tuple(q) for q in c], fill=col, width=width)
        T = PHOTO_T[year]
        alive = ex[(ex.start_year.values <= T) & (ex.end_year.values > T)]
        for gm in alive.g.values[shapely.intersects(alive.g.values, box)]:
            draw(gm, (70, 130, 255))
        if len(lots):
            p = lots[f"p{year}"].values
            sel = np.flatnonzero(shapely.intersects(g, box))
            for i in sel:
                col = (0, 230, 0) if p[i] >= P_STOOD[year] else (255, 60, 60) if p[i] <= P_OPEN[year] else (240, 220, 0)
                draw(g[i], col)
        if kept is not None and len(kept):
            kk = kept[(kept.start_year.values <= T) & (kept.end_year.values > T)]
            kg = to_px(shapely.from_wkb(kk.wkb.values))
            for gm in kg[shapely.intersects(kg, box)]:
                draw(gm, (255, 255, 255), 3)
        out = WORK / "look" / f"{name}_{year}.png"
        im.save(out)
        outs.append(str(out))
    print("\n".join(outs))


def step_look_sheet(lon, lat, name="look", half_m=200.0):
    """The same for Hudson County on the 1947 sheet: green = heavy ink on the lot (>= INK_MIN), red = none;
    blue = the map's buildings alive in 1941; white = the kept rows alive in 1941."""
    import rasterio
    from affine import Affine
    from PIL import Image, ImageDraw
    from rasterio.enums import Resampling
    from rasterio.warp import reproject
    x, y = ap.lonlat_to_pixel(lon, lat)
    bx, by = int(x // (NB * TILE)), int(y // (NB * TILE))
    fn = [f for f, (a, b, c, d) in SHEETS_1947.items() if a <= lon < c and b <= lat < d]
    if not fn or not (SHEET_DIR / fn[0]).exists() or not lots_path(bx, by).exists():
        return
    h = int(half_m / MPP)
    S = 3
    res = 156543.03392804097 / 2 ** Z
    ip = INK / f"{bx}_{by}.parquet"
    inkdf = pd.read_parquet(ip) if ip.exists() else None
    se, ss = (float(inkdf.shift_e.median()), float(inkdf.shift_s.median())) if inkdf is not None and len(inkdf) else (0.0, 0.0)
    # the sheet is drawn where the block's registration puts it
    tr = Affine(res / S, 0, (x - h + se / MPP) * res - 20037508.342789244, 0, -res / S, 20037508.342789244 - (y - h + ss / MPP) * res)
    a = np.zeros((3, 2 * h * S, 2 * h * S), "uint8")
    with rasterio.open(SHEET_DIR / fn[0]) as src:
        for b in range(3):
            reproject(rasterio.band(src, b + 1), a[b], dst_transform=tr, dst_crs="EPSG:3857", resampling=Resampling.bilinear)
    im = Image.fromarray(np.moveaxis(a, 0, -1))
    dr = ImageDraw.Draw(im)
    org = np.array([x - h, y - h])
    box = shapely.box(x - h, y - h, x + h, y + h)

    def draw(geom, col, width=1):
        for part in shapely.get_parts(geom):
            if part.geom_type == "Polygon":
                dr.line([tuple(q) for q in (np.asarray(part.exterior.coords) - org) * S], fill=col, width=width)
    ex = existing_window(bx, by)
    alive = ex[(ex.start_year.values <= INK_T + INK_GAP) & (ex.end_year.values > INK_T)]
    for gm in alive.g.values[shapely.intersects(alive.g.values, box)]:
        draw(gm, (40, 110, 255))
    lots = pd.read_parquet(lots_path(bx, by))
    g = to_px(shapely.from_wkb(lots.wkb.values))
    ink = inkdf.set_index("cid").ink1947.reindex(lots.cid.values).values if inkdf is not None else np.full(len(lots), np.nan)
    for i in np.flatnonzero(shapely.intersects(g, box)):
        draw(g[i], (0, 200, 0) if ink[i] >= INK_MIN else (255, 60, 60))
    rp = rows_path(bx, by)
    if rp.exists():
        kk = pd.read_parquet(rp)
        kk = kk[(kk.start_year.values <= INK_T) & (kk.end_year.values > INK_T)]
        kg = to_px(shapely.from_wkb(kk.wkb.values))
        for gm in kg[shapely.intersects(kg, box)]:
            draw(gm, (255, 0, 255), 3)
    out = WORK / "look" / f"{name}_1947sheet.png"
    im.save(out)
    print(out)


if __name__ == "__main__":
    args = sys.argv[1:] or ["snapshot", "lots", "ink", "assemble", "report"]
    if args[0] == "block":                      # one block, for a smoke test: gap_fill.py block <lon> <lat>
        step_snapshot()
        x, y = ap.lonlat_to_pixel(float(args[1]), float(args[2]))
        j = (int(x // (NB * TILE)), int(y // (NB * TILE)))
        LOTS.mkdir(parents=True, exist_ok=True)
        print(j, do_block(j))
        sys.exit(0)
    if args[0] == "one":                        # assemble one block: gap_fill.py one <lon> <lat>
        x, y = ap.lonlat_to_pixel(float(args[1]), float(args[2]))
        j = (int(x // (NB * TILE)), int(y // (NB * TILE)))
        print(j, _assemble_job(j)[1:])
        sys.exit(0)
    if args[0] == "look":
        step_snapshot()
        step_look(float(args[1]), float(args[2]), args[3] if len(args) > 3 else "look")
        step_look_sheet(float(args[1]), float(args[2]), args[3] if len(args) > 3 else "look")
        sys.exit(0)
    for a in args:
        if a == "snapshot":
            step_snapshot()
        elif a == "lots":
            step_snapshot()
            step_lots()
        elif a == "lots-reverse":
            step_snapshot()
            step_lots(workers=2, reverse=True)
        elif a == "lots-middle":
            step_snapshot()
            step_lots(workers=1, middle=True, budget_s=float(args[1]) if len(args) > 1 else None)
            break
        elif a == "ink":
            step_snapshot()
            step_ink()
        elif a == "assemble":
            step_snapshot()
            step_ink()
            step_assemble()
        elif a == "report":
            step_report()
        elif a == "fresh":
            EXISTING.unlink(missing_ok=True)
        else:
            raise SystemExit(f"unknown step {a}")
