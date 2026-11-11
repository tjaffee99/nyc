"""Stage: time-varying terrain tiles (elevation + land-cover history + decorations).

For every lattice vertex we derive a short land-cover *history* — a natural cover (1609)
plus up to four dated changes — from data wherever possible:

  natural (1609)   data/manual/natural/natural_1609.geojson where it exists (water, tidal
                   marsh and flats, ponds, wetlands, beach, forest, grassland; researched
                   from soil surveys and historical maps); elsewhere today's land is
                   upland forest and ESA WorldCover wetland is marsh (rule, `estimated`)
  made land        natural water / marsh / pond that is land today becomes land at the year
                   of its zone in data/manual/fill_zones.csv (growing outward across the
                   zone's years); precise zones (Manhattan's bands) are painted as drawn;
                   made land without a zone appears a little before the first buildings on it
  farms            cleared for fields and pasture outward from the colonial settlements
                   (seed years below / data/tables/places.csv towns; about 12 years per km;
                   Manhattan bare of woods by the 1776-83 occupation) — a model, `estimated`;
                   steep ground and today's big wooded parks stay forest
  city ground      second-earliest building within ~45 m of the cell (incl. vanished ones);
                   urban vs suburban by how much of the cell buildings cover
  parks            NYC Parks properties from their acquisition date (data/tables/parks.csv
                   where researched), other green outlines from OpenStreetMap (Overture)

Decorations per tile: the forest of 1609 until each cell is cleared, and today's trees on
real WorldCover canopy pixels dated by their park / neighbourhood.

Tile file (BAYT): tiles/{z}/{x}/{y}.bin.gz with columns
  elev i16 (decimetres), cover u8[5] per vertex, year u16[4] per vertex
  ((year-1000)*10, 0 = no change), deco_pos u16[2], deco_kind u8,
  deco_size u8 (metres), deco_years u16[2] (start, end; 0 = open)

Outputs: viewer/public/tiles/terrain/{z}/{x}/{y}.bin.gz, viewer/public/data/elevation-*.bin.gz,
viewer/public/data/terrain.json, data/interim/grid_<name>_landyear.npy
`python terrain_tiles.py land` only writes the land-year grids (for nyc_buildings.py).
"""
from __future__ import annotations

import json
import math
import sys
import zlib

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from rasterio import features
from rasterio.transform import Affine
from scipy import ndimage

from common import BORO_COUNTY, INTERIM, MANUAL, OVERTURE_RELEASE, RAW, TABLES, VIEWER_DATA, YEAR_MIN, log
from covers import (BEACH, DEEP, DUNES, FARM, FILL, FLAT, FOREST, GRASS, MARSH, PARK, PASTURE, RESERVOIR, ROCK,
                    SCRUB, SHALLOW, SUBURB, URBAN, WET, WETLAND)
from export_columnar import write_columnar
from terrain_grid import GRIDS, VERTS, grid_def

TILES = VIEWER_DATA.parent / "tiles" / "terrain"
OVT = RAW / "overture" / OVERTURE_RELEASE

COVER_NAMES = ["deep_water", "shallow_water", "tidal_flat", "tidal_marsh", "beach", "dunes", "grassland",
               "scrub", "oak_woodland", "forest", "farmland", "orchard", "vineyard", "pasture", "salt_pond",
               "diked_wetland", "urban", "park", "rock", "riparian", "fill", "wetland", "reservoir", "burned",
               "suburban"]
# decoration kinds
D_BROADLEAF, D_CONIFER, D_PALM, D_ORCHARD, D_FARMHOUSE, D_SHRUB, D_FARMYARD = range(7)

# natural_1609.geojson `cover` -> cover code (water is split into deep / shallow below)
NATURAL = {"water": SHALLOW, "tidal_marsh": MARSH, "tidal_flat": FLAT, "beach": BEACH, "dunes": DUNES,
           "pond": RESERVOIR, "freshwater_wetland": WETLAND, "forest": FOREST, "grassland": GRASS,
           "shrub": SCRUB, "rock": ROCK}
# paint order (later wins; data/manual/natural/README.md): pond > wetland > marsh > flat > beach > dunes > water
NATURAL_ORDER = ["forest", "grassland", "shrub", "rock", "water", "dunes", "beach", "tidal_flat", "tidal_marsh",
                 "freshwater_wetland", "pond"]

# Colonial settlements the farms spread from (lon, lat, year): fallback when
# data/tables/places.csv is not there. Founding years from the town articles of Wikipedia.
SEEDS = [(-74.0135, 40.7040, 1625), (-73.9900, 40.7260, 1651), (-73.9370, 40.8010, 1658), (-73.9900, 40.6930, 1646),
         (-73.9360, 40.6220, 1636), (-73.9580, 40.6500, 1652), (-74.0010, 40.6130, 1657), (-73.9300, 40.7000, 1661),
         (-73.9740, 40.5950, 1645), (-73.8300, 40.7630, 1645), (-73.8790, 40.7370, 1652), (-73.8000, 40.7020, 1656),
         (-74.0880, 40.5830, 1661), (-74.1460, 40.5710, 1700), (-73.8430, 40.8380, 1654), (-73.9230, 40.8090, 1639),
         (-73.8950, 40.8610, 1671), (-73.9020, 40.8790, 1693), (-73.8280, 40.8870, 1664)]


_H_OFF = [0, 0]   # row, column of the grid being worked on within its whole grid (windowed runs)


def h01_grid(rows, cols, salt=0, block=1):
    """Deterministic hash in [0, 1) per cell (or per block x block cells)."""
    r = ((np.arange(rows) + _H_OFF[0]) // block).astype(np.uint64)[:, None]
    c = ((np.arange(cols) + _H_OFF[1]) // block).astype(np.uint64)[None, :]
    M = np.uint64(0xFFFFFFFF)
    h = ((r * np.uint64(73856093)) & M) ^ ((c * np.uint64(19349663)) & M) ^ np.uint64(salt * 83492791 & 0xFFFFFFFF)
    h = ((h ^ (h >> np.uint64(13))) * np.uint64(0x5BD1E995)) & M
    h ^= h >> np.uint64(15)
    return (h % np.uint64(100003)).astype(np.float64) / 100003.0


def load_grid(name):
    g = grid_def(name)
    d = {k: np.load(INTERIM / f"grid_{name}_{k}.npy") for k in ("elev", "wc")}
    d["elev"] = d["elev"].astype(np.float32)
    d["elev"][d["elev"] < -500] = np.nan
    return g, d

def enc_year(y):
    y = np.asarray(y, dtype=float)
    out = np.where(np.isfinite(y), np.clip(np.rint((y - 1000.0) * 10), 1, 65535), 0)
    return out.astype(np.uint16)


def lonlat_of(g):
    rows, cols = g["rows"], g["cols"]
    X = g["X0"] + np.arange(cols) * g["res"]
    Y = g["Y0"] - np.arange(rows) * g["res"]
    lon = X / 20037508.342789244 * 180.0
    lat = np.degrees(2 * np.arctan(np.exp(Y / 6378137.0)) - np.pi / 2)
    return np.meshgrid(lon, lat)


def rasterize_on(g, shapes, fill=np.nan, dtype="float32", all_touched=False):
    t = Affine(*g["transform"][:6]) if not isinstance(g["transform"], Affine) else g["transform"]
    return features.rasterize(shapes, out_shape=(g["rows"], g["cols"]), transform=t, fill=fill, dtype=dtype,
                              all_touched=all_touched)


def nearest_fill(a, valid):
    """Fill invalid cells with the value of the nearest valid cell."""
    if not valid.any():
        return a
    idx = ndimage.distance_transform_edt(~valid, return_distances=False, return_indices=True)
    return a[tuple(idx)]




def read_wkb_parquet(path, where=None, crs=3857):
    d = pd.read_parquet(path)
    if where is not None:
        d = d[where(d)]
    return gpd.GeoDataFrame(d.drop(columns=["geometry"]), geometry=gpd.GeoSeries.from_wkb(d.geometry), crs=4326).to_crs(crs)


def parse_ring(ring):
    pts = [tuple(float(v) for v in p.split()) for p in str(ring).split(";") if p.strip()]
    return shapely.Polygon(pts) if len(pts) >= 3 else None


def to_merc(geom):
    return shapely.transform(geom, lambda c: np.column_stack([np.radians(c[:, 0]) * 6378137.0,
                                                              6378137.0 * np.log(np.tan(np.pi / 4 + np.radians(c[:, 1]) / 2))]))


def land_now_mask(g):
    """Today's land and inland water from OpenStreetMap (via Overture): the coastline's land
    polygons minus river / lake / pond / canal polygons."""
    land = read_wkb_parquet(OVT / "base_land.parquet", lambda d: d.subtype == "land")
    wat = read_wkb_parquet(OVT / "base_water.parquet",
                           lambda d: d.subtype.isin(["river", "lake", "pond", "reservoir", "canal", "water"])
                           & ~d["class"].isin(["swimming_pool", "wastewater", "fountain", "reflecting_pool"]))
    lm = rasterize_on(g, [(geom, 1) for geom in land.geometry if geom is not None], fill=0, dtype="uint8").astype(bool)
    wat = wat[wat.geometry.area > 1500]
    inland = rasterize_on(g, [(geom, 1) for geom in wat.geometry if geom is not None], fill=0, dtype="uint8").astype(bool)
    still = wat[wat.subtype.isin(["lake", "pond", "reservoir"]) | (wat["class"].isin(["lake", "pond", "reservoir", "basin"]))]
    lake = rasterize_on(g, [(geom, 1) for geom in still.geometry if geom is not None], fill=0, dtype="uint8").astype(bool) if len(still) else np.zeros_like(lm)
    return lm & ~inland, lake & lm


def borough_raster(g):
    """Borough per cell: 1 Manhattan, 2 Bronx, 3 Brooklyn, 4 Queens, 5 Staten Island, 0 outside."""
    co = gpd.read_file(f"zip://{RAW / 'tiger' / 'tl_2024_us_county.zip'}")
    co = co[(co.STATEFP == "36") & co.COUNTYFP.isin(list(BORO_COUNTY))].to_crs(3857)
    code = {"061": 1, "005": 2, "047": 3, "081": 4, "085": 5}
    return rasterize_on(g, [(r.geometry, code[r.COUNTYFP]) for r in co.itertuples()], fill=0, dtype="uint8")


def natural_cover(name, g, d, land_now, lake_now):
    """Cover code per cell in 1609 and a flag: True where it comes from the researched layer."""
    rows, cols = g["rows"], g["cols"]
    wc = d["wc"]
    N = np.where(land_now, FOREST, SHALLOW).astype(np.uint8)
    # rule (no researched layer): WorldCover wetland is tidal marsh near the sea, bare ground on the ocean is beach
    sea = ~land_now & ~lake_now
    near_sea = ndimage.binary_dilation(sea, iterations=max(1, int(round(600 / (g["res"] * 0.758)))))
    N[land_now & (wc == 90)] = np.where(near_sea, MARSH, WETLAND)[land_now & (wc == 90)]
    N[land_now & (wc == 60) & ndimage.binary_dilation(sea, iterations=3)] = BEACH
    N[lake_now] = RESERVOIR
    known = np.zeros((rows, cols), bool)
    files = [f for f in (MANUAL / "natural" / "natural_1609.geojson",
                         MANUAL / "natural" / "counties" / "natural_1609_counties.geojson") if f.exists()]
    if files:
        nat = pd.concat([gpd.read_file(f).to_crs(3857)[["cover", "geometry"]] for f in files], ignore_index=True)
        nat = gpd.GeoDataFrame(nat, geometry="geometry", crs=3857)
        # ground that was a dry valley in 1609 and is under a reservoir today: forest until the dam
        dv = nat[(nat.cover == "dry_valley") & nat.geometry.notna() & ~nat.geometry.is_empty]
        if len(dv):
            m = rasterize_on(g, [(geom, 1) for geom in dv.geometry], fill=0, dtype="uint8").astype(bool)
            N[m] = FOREST
            known |= m
        nat = nat[nat.cover.isin(list(NATURAL)) & nat.geometry.notna() & ~nat.geometry.is_empty]
        for cov in NATURAL_ORDER:
            sel = nat[nat.cover == cov]
            if not len(sel):
                continue
            m = rasterize_on(g, [(geom, 1) for geom in sel.geometry], fill=0, dtype="uint8").astype(bool)
            N[m] = NATURAL[cov]
            known |= m
        log(f"terrain {name}: natural 1609 layer covers {int(known.sum())} cells "
            f"({ {c: int((N[known] == NATURAL[c]).sum()) for c in NATURAL_ORDER} })")
    else:
        log(f"terrain {name}: no data/manual/natural/natural_1609.geojson yet - today's shoreline, forest on dry land")
    # streams that are gone or buried (data/manual/natural/streams_1609.geojson): one cell wide
    # on dry land, until the city or a park takes the ground
    stream = np.zeros((rows, cols), bool)
    sp = MANUAL / "natural" / "streams_1609.geojson"
    if sp.exists():
        st = gpd.read_file(sp).to_crs(3857)
        st = st[st.geometry.notna() & ~st.geometry.is_empty]
        stream = rasterize_on(g, [(geom, 1) for geom in st.geometry], fill=0, dtype="uint8").astype(bool)
        stream &= land_now & ~np.isin(N, list(WET | {WETLAND}))
        N[stream] = RESERVOIR
        log(f"terrain {name}: {int(stream.sum())} stream cells from {len(st)} lines")
    # open water far from the 1609 shore, or deep today, is deep water
    wet = np.isin(N, [SHALLOW, DEEP])
    dist = ndimage.distance_transform_edt(wet) * g["res"] * 0.758
    shallow_dem = np.isfinite(d["elev"]) & (d["elev"] > -3.0)
    N[wet & (dist > 350) & ~shallow_dem] = DEEP
    return N, known, stream


# precise rings whose inland edge only approximates the old shore: the 1609 layer wins there
SOFT_INNER = {"mn_er_1_pearl_water", "mn_hr_1_greenwich_washington", "mn_battery_early"}


def fill_layers(name, g, N, land_now, lake_now, urban_y, still_wet, known):
    """Made land, cuts and reservoirs from data/manual/fill_zones.csv (rules: fill_README.md).

    Returns land_year (year a naturally wet cell that is land today became land, NaN
    elsewhere), N (precise rings repaint the natural cover inside them), events
    [(mask, cover, year array)] for cuts and for water filled and dug out again, and
    reservoirs [(mask, start, end)].

      * coarse rings only date cells that are land today and were water / marsh / pond in 1609;
      * precise rings are painted as drawn (the ground inside was water until the fill),
        except the inland edge of the first bands where the researched 1609 layer says land;
      * where fill rings overlap, precise beats coarse and then the earliest end wins;
      * pond_fill and water_fill rings win inside their outline over fill rings;
      * each ring's land grows from its inland edge outward across its years;
      * a precise fill ring over today's water makes land that a later excavation ring
        removes again (Thirteenth Avenue); a coarse excavation needs the 1609 layer to say
        the ground was land."""
    rows, cols = g["rows"], g["cols"]
    events, reservoirs = [], []
    wet_codes = list(WET | {WETLAND})
    wetN = np.isin(N, wet_codes)
    zone = np.full((rows, cols), -1, np.int32)        # index of the ring dating each cell
    zprec = np.zeros((rows, cols), np.int8)
    zone_start = np.full((rows, cols), np.nan, np.float32)
    zone_end = np.full((rows, cols), np.nan, np.float32)
    temp_land = np.zeros((rows, cols), bool)          # filled water that is water again today
    z = None
    parts = []
    for p in (MANUAL / "fill_zones.csv", MANUAL / "fill_zones_counties.csv", MANUAL / "fill_zones_outer.csv"):
        if p.exists():
            try:
                parts.append(pd.read_csv(p))
            except Exception as e:  # noqa: BLE001 - a file being written
                log(f"terrain {name}: {p.name} unreadable ({e})")
    if parts:
        z = pd.concat(parts, ignore_index=True)
    n_zone = 0
    if z is not None and len(z):
        z["poly"] = [parse_ring(r) for r in z.ring]
        z = z[z.poly.notna()].reset_index(drop=True)
        z["poly"] = [to_merc(q if q.is_valid else q.buffer(0)) for q in z.poly]
        z["prec"] = (z.precision.fillna("coarse").astype(str) == "precise").astype(int) if "precision" in z else 0
        order = {"fill": 0, "pond_fill": 1, "water_fill": 1, "excavation": 2, "reservoir": 3}
        z["ord"] = z.kind.map(order).fillna(9)
        for zi, r in z.sort_values(["ord", "prec"]).iterrows():
            kind, prec = str(r.kind), int(r.prec)
            # a coarse ring narrower than a cell (a railroad causeway along the shore) dates every cell it touches
            thin = kind == "fill" and not prec and r.poly.length > 0 and 2 * r.poly.area / r.poly.length < g["res"]
            m = rasterize_on(g, [(r.poly, 1)], fill=0, dtype="uint8", all_touched=bool(thin)).astype(bool)
            if not m.any():
                continue
            ys = float(r.year_start)
            ye = float(r.year_end) if float(r.year_end) < 9000 else ys
            if kind in ("fill", "pond_fill", "water_fill"):
                if prec:
                    # the ring says: water (or pond / meadow) here until the fill
                    repaint = m & land_now & ~wetN
                    if r.zone_id in SOFT_INNER:
                        repaint &= ~known
                    N[repaint] = WETLAND if kind == "pond_fill" else SHALLOW
                    wetN |= repaint
                    if kind == "fill":
                        temp_land |= m & ~land_now & ~lake_now
                sel = m & wetN & (land_now | temp_land)
                if kind == "fill":
                    # precise beats coarse; then the earliest end wins
                    better = (zone < 0) | (prec > zprec) | ((prec == zprec) & (ye < np.nan_to_num(zone_end, nan=1e9)))
                    sel &= better
                zone[sel] = zi
                zprec[sel] = prec
                zone_start[sel] = ys
                zone_end[sel] = ye
                n_zone += 1
            elif kind == "excavation":
                cut = m & ~land_now & ~lake_now
                if prec:
                    was_land = cut & ~temp_land
                else:
                    was_land = cut & known & ~np.isin(N, wet_codes)   # needs the 1609 layer
                N[was_land & np.isin(N, [SHALLOW, DEEP])] = FOREST
                wetN &= ~was_land
                sel = cut & (temp_land | was_land)
                if sel.any():
                    events.append((sel, SHALLOW, np.full((rows, cols), ye, np.float32)))
                    temp_land &= ~cut
                    n_zone += 1
            elif kind == "reservoir":
                # one that still holds water: only the cells that are water today (the rings
                # close across causeways and take in islands); a drained one: the whole ring
                sel = m & (lake_now if float(r.year_end) >= 9000 else (land_now | lake_now))
                if not sel.any():
                    continue
                N[sel & (N == RESERVOIR) & ~known] = FOREST
                reservoirs.append((sel, ys, float(r.year_end)))
                n_zone += 1
        log(f"terrain {name}: {n_zone} of {len(z)} zones applied ({int((zone >= 0).sum())} cells dated)")
    else:
        log(f"terrain {name}: no data/manual/fill_zones.csv yet")
    # filled water that no cut removed and that is water today: not land after all
    zone[temp_land & ~land_now] = -1
    # (marsh that is still marsh today is not made land)
    made = wetN & ~lake_now & ~still_wet & (land_now | (zone >= 0))
    land_year = np.full((rows, cols), np.nan, np.float32)
    if made.any():
        natural_land = ~np.isin(N, wet_codes)
        dist = ndimage.distance_transform_edt(~natural_land).astype(np.float32)
        k = made & (zone >= 0)
        if k.any():
            # each ring's land grows outward from its inland edge over the ring's years
            lab = zone + 1
            ids = np.unique(lab[k])
            dmax = dict(zip(ids, ndimage.maximum(dist, lab, index=ids)))
            dmin = dict(zip(ids, ndimage.minimum(dist, lab, index=ids)))
            lo = np.vectorize(dmin.get, otypes=[np.float32])(lab[k])
            hi = np.vectorize(dmax.get, otypes=[np.float32])(lab[k])
            t = (dist[k] - lo) / np.maximum(hi - lo, 1e-3)
            land_year[k] = zone_start[k] + t * (zone_end[k] - zone_start[k])
        # made land without a zone: a few years before the first buildings on or near it
        rest = made & ~np.isfinite(land_year)
        if rest.any():
            uy = nearest_fill(np.where(np.isfinite(urban_y), urban_y, 0).astype(np.float32), np.isfinite(urban_y))
            # (a building's point lies in one cell; a large building covers many, and the nearest
            # point to its far corner may be a new building next door)
            uy = np.fmin(uy, own_years(g))
            land_year[rest] = np.clip(uy[rest] - 4.0, YEAR_MIN + 20, 2020)
            log(f"terrain {name}: {int(rest.sum())} made-land cells have no zone: dated 4 years before their first use")
    # evidence that the ground was there earlier (ground_rule.py): a landmark record, a
    # researched row or an outline on a dated map moves a cell's land year back; so do two
    # recorded assessor years against a dated zone, or one where the year was a fallback guess
    from ground_rule import EVIDENCE_LEAD, evidence_on
    sy, w1, w2 = evidence_on(g)
    lim = np.fmin(sy, np.where(zone >= 0, w2, w1)) - EVIDENCE_LEAD
    adj = made & np.isfinite(lim) & (land_year > lim)
    if adj.any():
        land_year[adj] = np.maximum(lim[adj], YEAR_MIN + 1.0)
        log(f"terrain {name}: {int(adj.sum())} made-land cells dated earlier by buildings recorded or mapped on them")
    return land_year, N, events, reservoirs


def own_years(g, min_m2=300.0):
    """Per cell: the earliest year (before the ground rule) of a building of min_m2 or more whose
    outline touches the cell or one next to it; NaN where none. Generated buildings do not count."""
    from rasterio import features
    from rasterio.transform import Affine
    rows, cols, res = g["rows"], g["cols"], g["res"]
    out = np.full((rows, cols), np.inf, np.float32)
    shapes = []
    for f in (INTERIM / "nyc_buildings.parquet", INTERIM / "county_buildings.parquet"):
        if not f.exists():
            continue
        import pyarrow.parquet as pq
        names = pq.read_schema(f).names
        b = pd.read_parquet(f, columns=[c for c in ("geometry", "start_year", "start_free", "year_confidence", "area") if c in names])
        b = b[(b.year_confidence.values != "procedural") & (b["area"].values >= min_m2)]
        y = b.start_year.values.astype(np.float32)
        if "start_free" in b:
            sf = b.start_free.values.astype(np.float32)
            y = np.where(np.isfinite(sf), sf, y)
        gm = shapely.from_wkb(b.geometry.values)
        gm = shapely.transform(gm, lambda c: np.column_stack([np.radians(c[:, 0]) * 6378137.0,
                                                               6378137.0 * np.log(np.tan(np.pi / 4 + np.radians(c[:, 1]) / 2))]))
        shapes += list(zip(gm, y.tolist()))
    if not shapes:
        return np.full((rows, cols), np.nan, np.float32)
    shapes.sort(key=lambda q: -q[1])          # the earliest is burnt last
    tr = Affine(res, 0, g["X0"] - res / 2, 0, -res, g["Y0"] + res / 2)      # the grid's values sit on its nodes
    out = features.rasterize(shapes, out_shape=(rows, cols), transform=tr, fill=np.inf, dtype="float32", all_touched=True)
    out = ndimage.minimum_filter(out, 3, mode="nearest")
    n = int(np.isfinite(out).sum())
    log(f"terrain: {len(shapes)} buildings of {min_m2:.0f} m2 or more date the ground under {n} cells")
    return np.where(np.isfinite(out), out, np.nan).astype(np.float32)


def building_evidence(g, standing_only=False, free=False):
    """City ground from the buildings themselves: the year of the second-earliest building
    within one cell of each cell (incl. vanished ones, unless standing_only), and the share
    of the ground they cover. free: the buildings' years before the ground rule moved them
    (`start_free`) - what dates made land must not itself depend on the land's date."""
    rows, cols = g["rows"], g["cols"]
    urban_y = np.full((rows, cols), np.nan, np.float32)
    cover = np.zeros((rows, cols), np.float32)
    files = [f for f in (INTERIM / "nyc_building_points.parquet", INTERIM / "county_building_points.parquet") if f.exists()]
    if not files:
        log("terrain: no building points yet (nyc_buildings.py) - no city ground")
        return urban_y, cover
    b = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    if free and "start_free" in b:
        b["start_year"] = np.where(np.isfinite(b.start_free.values.astype(float)), b.start_free.values, b.start_year.values)
    if standing_only:
        b = b[b.end_year >= 9000]
    X = np.radians(b.lon.values) * 6378137.0
    Y = 6378137.0 * np.log(np.tan(np.pi / 4 + np.radians(b.lat.values) / 2))
    c = np.rint((X - g["X0"]) / g["res"]).astype(np.int64)
    r = np.rint((g["Y0"] - Y) / g["res"]).astype(np.int64)
    ok = (c >= 1) & (c < cols - 1) & (r >= 1) & (r < rows - 1)
    r, c, y, a = r[ok], c[ok], b.start_year.values[ok].astype(np.float32), b.area_m2.values[ok].astype(np.float32)
    cell_m2 = (g["res"] * 0.758) ** 2
    np.add.at(cover, (r, c), a / cell_m2)
    win = 3 if g["z"] == 14 else 1
    off = range(-(win // 2), win // 2 + 1)
    idx = np.concatenate([(r + dr) * cols + (c + dc) for dr in off for dc in off])
    yy = np.tile(y, len(off) ** 2)
    order = np.lexsort((yy, idx))
    idx, yy = idx[order], yy[order]
    first = np.r_[True, idx[1:] != idx[:-1]]
    second = np.r_[False, first[:-1]] & ~first
    flat = urban_y.ravel()
    flat[idx[first]] = yy[first]          # a lone building: its own year
    flat[idx[second]] = yy[second]        # else the second earliest
    cover = ndimage.uniform_filter(cover, 3, mode="constant")
    return urban_y, cover


def extent_years(g):
    """Year each cell was built up according to the extent snapshots (data/manual/extents):
    between the snapshot of its borough that first shows it built and the one before
    (NaN: in no snapshot). They only fill gaps: where no building, standing or traced, dates
    the ground — above 86th St, in the old towns — the city still appears when the maps say."""
    from pyproj import Transformer

    from common import NYC_CRS
    from nyc_predecessors import extent_snapshots
    rows, cols = g["rows"], g["cols"]
    out = np.full((rows, cols), np.nan, np.float32)
    try:
        snaps, _ = extent_snapshots()
    except Exception as e:  # noqa: BLE001
        log(f"terrain: extent snapshots not used ({e})")
        return out
    tr = Transformer.from_crs(NYC_CRS, 3857, always_xy=True)
    h = h01_grid(rows, cols, salt=11, block=4).astype(np.float32)
    for series in snaps.values():
        prev = None
        for year, poly in series:
            pm = shapely.transform(poly, lambda c: np.column_stack(tr.transform(c[:, 0], c[:, 1])))
            m = rasterize_on(g, [(pm, 1)], fill=0, dtype="uint8").astype(bool) & np.isnan(out)
            lo = prev if prev is not None else year - 20.0
            out[m] = lo + (year - lo) * h[m]
            prev = year
    # the counties: the built-up ground of the USGS sheets of 1897-98 and the urban tint of the
    # sheets of the 1940s (data/manual/gapfill, read for the generated fill). A district that was
    # cleared and rebuilt has no old building left to date its ground: without these it stays
    # farmland until the town houses of the 1990s.
    done = np.zeros((rows, cols), bool)
    for fn, back in (("hudson_builtup_1897.geojson", 30.0), ("counties_builtup_1897.geojson", 30.0), ("counties_tint_194x.geojson", 47.0)):
        f = MANUAL / "gapfill" / fn
        if not f.exists():
            continue
        e = gpd.read_file(f).to_crs(3857)
        for year, grp in e.groupby(e.year.astype(float)):
            m = rasterize_on(g, [(q, 1) for q in grp.geometry.values if q is not None and not q.is_empty], fill=0, dtype="uint8").astype(bool)
            m &= np.isnan(out) | (done & (out > year))
            # (ground a later sheet shows built and the 1897 sheet does not: built in between)
            lo = year - back
            out[m] = lo + (year - lo) * h[m]
            done |= m
    return out


def park_layers(g, urban_fill):
    """Year each cell became a park / cemetery / green (NaN elsewhere) and the big wooded greens."""
    rows, cols = g["rows"], g["cols"]
    park_y = np.full((rows, cols), np.nan, np.float32)
    big = np.zeros((rows, cols), bool)
    names = {}
    for pc in (TABLES / "parks.csv", TABLES / "parks_counties.csv"):
        if pc.exists():
            t = pd.read_csv(pc)
            names.update({str(n).strip().lower(): float(y) for n, y in zip(t.name, t.start_year) if pd.notna(y)})
    shapes = []
    pp = RAW / "nyc" / "parks_properties.geojson"
    if pp.exists():
        pk = gpd.read_file(pp).to_crs(3857)
        yr = pd.to_datetime(pk.acquisitiondate, errors="coerce")
        y = (yr.dt.year + (yr.dt.day_of_year - 1) / 365.0).values.astype(float)
        for geom, yy, nm, ac in zip(pk.geometry, y, pk.signname.fillna("").astype(str), pd.to_numeric(pk.acres, errors="coerce")):
            if geom is None or geom.is_empty:
                continue
            yy = names.get(nm.strip().lower(), yy)
            shapes.append((geom, yy if np.isfinite(yy) and yy >= YEAR_MIN else np.nan, geom.area * 0.575 > 400_000))
    lu = OVT / "base_land_use.parquet"
    if lu.exists():
        gl = read_wkb_parquet(lu, lambda d: d["class"].isin(["park", "cemetery", "golf_course", "nature_reserve", "recreation_ground", "grave_yard", "garden"]))
        for geom, nm in zip(gl.geometry, gl.name.fillna("").astype(str)):
            if geom is None or geom.is_empty or geom.area * 0.575 < 4000:
                continue
            shapes.append((geom, names.get(nm.strip().lower(), np.nan), geom.area * 0.575 > 400_000))
    # undated outlines first so dated ones win
    shapes.sort(key=lambda s: (np.isfinite(s[1]), -s[0].area))
    # (one pass each, not one per outline: the wide region holds fifteen thousand greens and
    # every pass scans 28 million cells; the order is the loop's - a later shape burns over an
    # earlier one)
    isp = np.zeros((rows, cols), bool)
    if shapes:
        isp = rasterize_on(g, [(s[0], 1) for s in shapes], fill=0, dtype="uint8").astype(bool)
        dated = [(s[0], float(s[1])) for s in shapes if np.isfinite(s[1])]
        if dated:
            park_y = rasterize_on(g, dated, fill=np.nan, dtype="float32")
        bigs = [(s[0], 1) for s in shapes if s[2]]
        if bigs:
            big = rasterize_on(g, bigs, fill=0, dtype="uint8").astype(bool)
    # greens without a date: the year the neighbourhood around was built (estimated)
    und = isp & ~np.isfinite(park_y)
    park_y[und] = urban_fill[und]
    return park_y, isp, big


def settlement_seeds():
    seeds = list(SEEDS)
    for p in (TABLES / "places.csv", TABLES / "places_counties.csv", TABLES / "places_outer.csv"):
        if p.exists():
            t = pd.read_csv(p)
            t = t[t.tier.isin(["city", "town"]) & (pd.to_numeric(t.year_start, errors="coerce") < 1800)]
            seeds += [(float(r.lon), float(r.lat), float(r.year_start)) for r in t.itertuples() if float(r.year_start) >= 1624]
    return seeds


def farm_years(g, lon, lat, boro, cap=True):
    """Year each cell was cleared for fields: 12 years per km outward from the nearest colonial
    settlement (a model; `estimated`). Manhattan was bare of woods by the end of the British
    occupation (1783): firewood for the garrison took what the farms had left."""
    kx = 111_320 * math.cos(math.radians(40.7))
    # (the front is smooth: on the wide region grid - 28 million cells, 700 seeds - it is
    # computed on every fourth cell and interpolated)
    step = 4 if lon.size > 6_000_000 else 1
    lo, la = lon[::step, ::step], lat[::step, ::step]
    F = np.full(lo.shape, np.inf, np.float32)
    for slon, slat, sy in settlement_seeds():
        dkm = np.hypot((lo - slon) * kx, (la - slat) * 110_574) / 1000.0
        F = np.minimum(F, (sy + 3 + 12.0 * dkm).astype(np.float32))
    if step > 1:
        F = ndimage.zoom(F, (lon.shape[0] / F.shape[0], lon.shape[1] / F.shape[1]), order=1, mode="nearest")
        F = F[:lon.shape[0], :lon.shape[1]]
        if F.shape != lon.shape:
            F = np.pad(F, ((0, lon.shape[0] - F.shape[0]), (0, lon.shape[1] - F.shape[1])), mode="edge")
        F = F.astype(np.float32)
    if cap:
        F = np.where(boro == 1, np.minimum(F, 1779.0), np.minimum(F, 1860.0))
    return F + 6.0 * h01_grid(*lon.shape, salt=3, block=6).astype(np.float32)


def farm_census(g, F, order, farmable, land, boro):
    """The clearing years of `farmable` ground, county by county, so that the cleared share of the
    county's land follows the censuses' improved farmland (data/tables/farmland_counties.csv:
    New York's state censuses from 1821, the federal ones from 1850). The model's order stays —
    `order` is the year the settlement front reaches a cell plus slope and a field-sized noise, so
    the best and nearest ground goes first and woods stay scattered among the fields — but how much
    is cleared by a year is the census's count, not the model's guess. The ground the first census
    finds cleared keeps the model's years (no count is older); ground beyond the peak share is never
    cleared. A county without figures (and Manhattan, which the British garrison stripped) keeps
    the model's years `F`."""
    p = TABLES / "farmland_counties.csv"
    if not p.exists():
        log("terrain: no data/tables/farmland_counties.csv - farmland follows the model alone")
        return F
    t = pd.read_csv(p, dtype={"county_fips": str, "unit_fips": str})
    t["share"] = pd.to_numeric(t.improved_share, errors="coerce")
    t["year"] = pd.to_numeric(t.year, errors="coerce")
    t = t[t.share.notna() & t.year.notna() & (t.share > 0) & (t.share <= 1.0)]
    unit = t.unit_fips.fillna(t.county_fips) if "unit_fips" in t else t.county_fips
    series = {}
    for fips_list, yr, sh in zip(unit.astype(str), t.year.values, t.share.values):
        for f in fips_list.replace(" ", "").split("+"):
            series.setdefault(f.zfill(5), {})[float(yr)] = float(sh)
    # (a county with one census only - New Jersey and Connecticut have 1850 alone - grows to that
    # share by that year and no further: its peak a few decades later was somewhat higher)
    series = {f: sorted(v.items()) for f, v in series.items() if len(v) >= 1 and f != "36061"}
    if not series:
        return F
    co = gpd.read_file(f"zip://{RAW / 'tiger' / 'tl_2024_us_county.zip'}")
    co["fips"] = co.STATEFP + co.COUNTYFP
    co = co[co.fips.isin(list(series))].to_crs(3857).reset_index(drop=True)
    cid = rasterize_on(g, [(r.geometry, i + 1) for i, r in enumerate(co.itertuples())], fill=0, dtype="uint16")
    out = F.copy()
    said = []
    for i, r in enumerate(co.itertuples()):
        inside = cid == i + 1
        n_land = int((inside & land).sum())
        m = inside & farmable
        if n_land < 200 or m.sum() < 50:
            continue
        ys = np.array([q[0] for q in series[r.fips]])
        sh = np.array([q[1] for q in series[r.fips]])
        k = int(np.argmax(sh))
        o = order[m]
        rank = (np.argsort(np.argsort(o, kind="stable"), kind="stable") + 0.5) / n_land
        # up to the first census: the ground it finds cleared, at the model's own years (the
        # front reached most of it long before; what the model has later is spread over the 25
        # years before the count)
        t0, s0 = float(ys[0]), float(sh[0])
        yr = np.full(int(m.sum()), np.inf, np.float32)
        early = rank <= s0
        Fm = F[m]
        jit = (rank * 9973.0) % 1.0
        yr[early] = np.where(Fm[early] <= t0 - 1.0, Fm[early], t0 - 1.0 - 25.0 * jit[early])
        # after it: the censuses' own growth to the peak; ground beyond the peak share stays wooded
        if k > 0:
            cs = np.maximum.accumulate(sh[:k + 1])
            keep = np.r_[True, np.diff(cs) > 1e-6]
            late = ~early
            yr[late] = np.interp(rank[late], cs[keep], ys[:k + 1][keep], right=np.inf)
        out[m] = yr
        got = {int(y): round(float((yr <= y).sum()) / n_land, 2) for y in (1820, 1850, 1880)}
        said.append(f"{r.NAME} peak {sh[k]:.0%} in {int(ys[k])}, cleared {got}")
    log(f"terrain: farmland of {len(said)} counties follows the censuses: " + "; ".join(said))
    return out


def lenape_fields(lon, lat):
    """Cells within the planting grounds of the Lenape settlements of data/tables/early_nyc.csv
    (kind lenape_settlement): maize, beans and squash were grown beside the villages, and the
    colonists took those "old fields" over first. The sites are researched; the size of the
    fields is not (60 m + 12 m per dwelling, at most 350 m around the site: `estimated`)."""
    m = np.zeros(lon.shape, bool)
    p = TABLES / "early_nyc.csv"
    if not p.exists():
        return m
    t = pd.read_csv(p)
    t = t[t.kind.astype(str) == "lenape_settlement"]
    kx = 111_320 * math.cos(math.radians(40.7))
    for slon, slat, n in zip(t.lon.astype(float), t.lat.astype(float), pd.to_numeric(t["count"], errors="coerce").fillna(4)):
        r = min(350.0, 60.0 + 12.0 * float(n))
        dlon, dlat = r / kx, r / 110_574
        box = (np.abs(lon - slon) < dlon) & (np.abs(lat - slat) < dlat)
        if box.any():
            m |= box & (np.hypot((lon - slon) * kx, (lat - slat) * 110_574) < r)
    return m


_MADE = {}   # per grid: the made-land cells of the last histories() run


def made_land_year(name, covers, years):
    """The land-year grid the ground rule reads: the year each MADE-LAND cell turns to land
    in the cover history. Not the vanished streams (a line one cell wide: a stylisation) and
    not today's wetland: there the ground changes when the city arrives, which is dated from
    the buildings themselves — a building made to wait for that would push it later, pass
    after pass."""
    ly = land_year_of(covers, years)
    ly[~_MADE[name]] = np.nan
    return ly


def histories(name, g, d, land_only=False, reuse_land=True):
    rows, cols = g["rows"], g["cols"]
    lon, lat = lonlat_of(g)
    elev = np.nan_to_num(d["elev"], nan=0.0).astype(np.float32)
    wc = d["wc"]
    land_now, lake_now = land_now_mask(g)
    boro = borough_raster(g)
    urban_y, bcover = building_evidence(g)
    N, known, stream = natural_cover(name, g, d, land_now, lake_now)
    built = np.isfinite(urban_y)
    urban_fill = nearest_fill(np.where(built, urban_y, 0).astype(np.float32), built) if built.any() else np.full((rows, cols), 1900.0, np.float32)
    # undated greens take the year of the buildings standing around them today (a housing
    # estate's lawns are as old as the estate, not as the tenements it replaced)
    urban_now_y, _ = building_evidence(g, standing_only=True)
    now_ok = np.isfinite(urban_now_y)
    urban_now_fill = nearest_fill(np.where(now_ok, urban_now_y, 0).astype(np.float32), now_ok) if now_ok.any() else urban_fill
    del urban_now_y, now_ok
    park_y, is_park, big_green = park_layers(g, urban_now_fill)
    ext_y = extent_years(g)
    # made land without a dated zone appears a little before its first use: the buildings
    # around, the park it lies in, or the built-up extent that first includes it
    # (the buildings' years as they were before they waited for their ground: dated from the
    # waiting years, the ground and its buildings pushed each other half a year later with every rebuild)
    urban_free, _ = building_evidence(g, free=True)
    free_ok = np.isfinite(urban_free)
    free_fill = nearest_fill(np.where(free_ok, urban_free, 0).astype(np.float32), free_ok) if free_ok.any() else urban_fill
    del urban_free, free_ok
    first_use = np.fmin(np.fmin(free_fill, np.where(is_park, park_y, np.nan)), ext_y).astype(np.float32)
    # (streams are not made land: nothing waits for them, the city simply covers them)
    land_year, N, extra, reservoirs = fill_layers(name, g, N, land_now, lake_now, first_use, (land_now & (wc == 90)) | stream, known)
    if land_only:
        return land_year
    # The buildings, streets and tracks were checked against the land years of the `land` run
    # (grid_<name>_landyear.npy). Made land without a dated zone takes its year from the
    # buildings around it, so a recomputation after the buildings moved would differ by a few
    # years and leave some of them standing before their ground: keep the saved years.
    sv = INTERIM / f"grid_{name}_landyear.npy"
    if reuse_land and sv.exists():
        saved = np.load(sv, mmap_mode="r")
        if "win" in g and saved.shape == g["whole"]:
            saved = np.asarray(saved[g["win"]])
        if saved.shape == land_year.shape:
            both = np.isfinite(saved) & np.isfinite(land_year)
            land_year = np.where(both, saved, land_year).astype(np.float32)
    # slope (rise over run) for "too steep to plough"
    cell_m = g["res"] * 0.758
    gy, gx = np.gradient(elev, cell_m)
    slope = np.hypot(gx, gy)
    h = h01_grid(rows, cols, salt=1)
    # ---- today's ground
    wet_now = ~land_now
    near_built = ndimage.maximum_filter(built, 5) if built.any() else built
    is_city = land_now & ~is_park & (built | ((wc == 50) & near_built) | (wc == 50))
    suburb = is_city & (bcover < 0.22) & (ndimage.uniform_filter(np.isin(wc, [10, 30]).astype(np.float32), 5) > 0.35)
    city_y = np.where(built, urban_y, urban_fill).astype(np.float32)
    # the extent snapshots fill gaps: built-up ground is city no later than the maps show it
    city_y = np.fmin(city_y, ext_y).astype(np.float32)
    open_grass = land_now & ~is_park & ~is_city & np.isin(wc, [30, 40, 60])
    wooded_now = land_now & (wc == 10) & ~is_city
    # Woods that were never cleared. Farming took nearly all the workable ground around the
    # city by the middle of the 19th century (three quarters of Kings, Queens, Richmond and
    # Westchester counties was improved farmland in the censuses of 1850-80); what stayed
    # wooded was the steep and rocky ground and each farm's woodlot. Today's woods are mostly
    # second growth on fields given up between the 1880s and the 1930s, and the big parks and
    # cemeteries were farms and rough pasture before they were laid out — they are not islands
    # of the forest of 1609. So: steep ground stays forest; a fifth of the rest stays as
    # woodlots (a third where woods stand today: the poorer ground); everything else is cleared
    # with its neighbours, and where woods stand today they grow back (below).
    lot_h = h01_grid(rows, cols, salt=11, block=5)
    woodlot = lot_h < np.where(wooded_now, 0.33, 0.18)
    kept_woods = (wooded_now & (slope > 0.2)) | woodlot
    # ---- events
    events = []

    def event(mask, cover, year):
        if np.ndim(cover) == 0:
            cover = np.full((rows, cols), cover, np.uint8)
        yr = np.where(mask, year, np.nan).astype(np.float32)
        events.append((cover.astype(np.uint8), yr))

    made = np.isfinite(land_year)
    _MADE[name] = made
    event(made, FILL, land_year)
    for m, cv, yr in extra:
        event(m, cv, yr)
    ground_y = np.where(made, land_year, -np.inf)   # nothing before its ground
    # reservoirs: water from their year; one that was drained hands the ground to today's
    # use (park or city) at its end, and nothing else happens there in between
    in_res = np.zeros((rows, cols), bool)
    for m, ys, ye in reservoirs:
        event(m, RESERVOIR, np.full((rows, cols), ys, np.float32))
        in_res |= m
        if ye < 9000:
            city_y = np.where(m, np.fmax(city_y, ye), city_y).astype(np.float32)
            park_y = np.where(m, np.fmax(park_y, ye), park_y).astype(np.float32)
    # researched sites (data/manual/sites/sites.geojson, README there): a yard, works or
    # terminal is city ground from its founding; a fort, asylum, hospital ground or landfill is
    # open grass from its founding until today's use takes the ground
    site_y = np.full((rows, cols), np.nan, np.float32)
    open_y = np.full((rows, cols), np.nan, np.float32)
    sp = MANUAL / "sites" / "sites.geojson"
    if sp.exists():
        try:
            st = gpd.read_file(sp).to_crs(3857)
            for geom, gr, y0 in zip(st.geometry, st.ground.astype(str), pd.to_numeric(st.start_year, errors="coerce")):
                if geom is None or geom.is_empty or not np.isfinite(y0):
                    continue
                m = rasterize_on(g, [(geom, 1)], fill=0, dtype="uint8").astype(bool) & land_now
                tgt = site_y if gr in ("paved", "yard") else open_y
                tgt[m] = np.fmin(tgt[m], y0)
            city_y = np.fmin(city_y, site_y).astype(np.float32)
            log(f"terrain {name}: site ground: {int(np.isfinite(site_y).sum())} cells of yards and works, "
                f"{int(np.isfinite(open_y).sum())} cells of forts and open grounds")
        except Exception as e:  # noqa: BLE001
            log(f"terrain {name}: sites not used ({type(e).__name__}: {e})")
    # farms: dry natural land that is city, small park or open grass today
    F = farm_years(g, lon, lat, boro)
    farmable = land_now & ~made & np.isin(N, [FOREST, GRASS, SCRUB]) & ~kept_woods & (slope < 0.16)
    target_y = np.where(is_park, np.fmin(park_y, city_y), city_y)
    # (steeper ground was cleared later, and as pasture; the Lenape's planting grounds are
    # fields from the start)
    F = (F + 220.0 * np.clip(slope - 0.03, 0.0, 0.13)).astype(np.float32)
    order = (farm_years(g, lon, lat, boro, cap=False) + 220.0 * np.clip(slope - 0.03, 0.0, 0.13)
             + 140.0 * h01_grid(rows, cols, salt=23, block=8)).astype(np.float32)
    F = farm_census(g, F, order, farmable, land_now, boro)
    del order
    fields_1609 = lenape_fields(lon, lat) & land_now & ~made & np.isin(N, [FOREST, GRASS, SCRUB]) & (slope < 0.12)
    F = np.where(fields_1609, float(YEAR_MIN), F).astype(np.float32)
    farmable |= fields_1609
    # woods of today on ground that was farmed: no city or park follows, the woods come back
    second_growth = wooded_now & ~is_park & ~is_city & farmable
    target_y = np.where(second_growth, np.inf, target_y)
    farm_ok = farmable & (F < target_y - 8.0) & ~(F > open_y)
    # (the open ground of a site: only where it comes before what is there today)
    later = np.nan_to_num(np.where(is_park, park_y, np.where(is_city, city_y, np.inf)), nan=np.inf)
    event(np.isfinite(open_y) & (open_y < later - 2.0), GRASS, np.fmax(open_y, ground_y + 0.5))
    pasture = (h01_grid(rows, cols, salt=7, block=10) < np.clip(0.25 + 3.5 * slope, 0.25, 0.8)) & ~fields_1609
    event(farm_ok & ~pasture, FARM, F)
    event(farm_ok & pasture, PASTURE, F)
    # old fields given up: second growth from the 1880s to the 1930s (never sooner than 40 years after the clearing)
    event(farm_ok & second_growth, FOREST, np.fmax(F + 40.0, 1882.0 + 55.0 * h))
    # airfields (airports.py -> data/interim/airports.parquet): mown grass from the opening year;
    # one that closed hands the ground on to today's use when it closed
    ap = INTERIM / "airports.parquet"
    if ap.exists():
        af = gpd.read_parquet(ap).to_crs(3857)
        af = af[~af["class"].astype(str).str.contains("heliport")]
        for geom, opened, closed in zip(af.geometry, af.opened.astype(float), af.closed.astype(float)):
            if geom is None or geom.is_empty:
                continue
            m = rasterize_on(g, [(geom, 1)], fill=0, dtype="uint8").astype(bool) & land_now
            if not m.any():
                continue
            event(m, GRASS, np.fmax(opened, ground_y + 0.5))
            if closed < 9000:
                city_y = np.where(m, np.fmax(city_y, closed), city_y).astype(np.float32)
                park_y = np.where(m, np.fmax(park_y, closed), park_y).astype(np.float32)
            else:
                is_city &= ~m      # the field is still a field: pavement and terminals are drawn on it
                open_grass &= ~m
    # a park made where the city already stood (a cleared tenement block, an estate's grounds):
    # city ground first — buildings stood there well before, or the maps show it built up
    # a generation earlier
    was_y = np.fmin(np.where(urban_y < park_y - 5.0, urban_y, np.nan), np.where(ext_y < park_y - 25.0, ext_y, np.nan))
    was_y = np.fmin(was_y, np.where(site_y < park_y - 5.0, site_y, np.nan))   # a yard or works that became a park
    event(is_park & land_now & np.isfinite(was_y), URBAN, np.fmax(was_y, ground_y + 0.5))
    # city ground
    event(is_city & ~suburb, URBAN, np.fmax(city_y, ground_y + 0.5))
    event(is_city & suburb, SUBURB, np.fmax(city_y, ground_y + 0.5))
    # open ground that is neither park nor built on (airfields, verges, landfill mounds)
    event(open_grass & (made | ~np.isin(N, [GRASS, BEACH, DUNES, MARSH, WETLAND])), GRASS, np.fmax(city_y, ground_y + 1.0))
    # parks, cemeteries, greens (lakes made with the park appear with it)
    event(is_park & land_now, PARK, np.fmax(park_y, ground_y + 1.0))
    made_lake = lake_now & is_park & ~known & ~in_res
    N[made_lake] = FOREST
    event(made_lake, RESERVOIR, park_y)
    # woods that grew back on cleared or made ground (not parks: their trees are decorations)
    regrow = wooded_now & ~is_park & ~stream & (made | ~np.isin(N, [FOREST]))
    event(regrow, FOREST, np.fmax(ground_y + 25.0, 1900.0 + 60.0 * h))
    # today's marsh on ground that was open water in 1609 (accretion, restored marsh)
    event(land_now & (wc == 90) & np.isin(N, [SHALLOW, DEEP]) & ~made, MARSH, 1900.0 + 60.0 * h)

    # ---- assemble: natural cover + up to four changes in time order
    C = np.stack([e[0] for e in events])
    Y = np.stack([e[1] for e in events])
    order = np.argsort(np.where(np.isnan(Y), np.inf, Y), axis=0, kind="stable")
    C = np.take_along_axis(C, order, 0)
    Y = np.take_along_axis(Y, order, 0)
    covers = np.zeros((5, rows, cols), np.uint8)
    years = np.full((4, rows, cols), np.nan, np.float32)
    covers[0] = N
    last = N.copy()
    n = np.zeros((rows, cols), np.int8)
    for e in range(C.shape[0]):
        ce, ye = C[e], Y[e]
        # bare fill that is built on within 4 years goes straight to the city (saves a slot):
        # the city's cover arrives AT THE LAND YEAR. (It used to arrive with the city, up to four
        # years later, and the ground stayed water or marsh under buildings that the ground
        # rule had already let stand.)
        if e + 1 < C.shape[0] and (ce == FILL).any():
            soon_c = np.zeros((rows, cols), np.uint8)
            for e2 in range(C.shape[0] - 1, e, -1):   # the nearest following event wins
                m2 = np.isin(C[e2], [URBAN, SUBURB, PARK]) & (Y[e2] - ye < 4)
                soon_c = np.where(m2, C[e2], soon_c)
            ce = np.where((ce == FILL) & (soon_c > 0), soon_c, ce)
        ok = np.isfinite(ye) & (ce != last) & (n < 4) & (ye >= YEAR_MIN)
        # fields never follow city, fill or park
        ok &= ~(np.isin(ce, [FARM, PASTURE]) & np.isin(last, [URBAN, SUBURB, FILL, PARK, GRASS]))
        rr, cc = np.nonzero(ok)
        covers[n[ok] + 1, rr, cc] = ce[ok]
        years[n[ok], rr, cc] = ye[ok]
        last = np.where(ok, ce, last)
        n = n + ok
    # unused slots repeat the last cover
    for s in range(1, 5):
        covers[s] = np.where(n >= s, covers[s], covers[s - 1])
    log(f"terrain {name}: changes per vertex {np.bincount(n.ravel(), minlength=5).tolist()}; "
        f"made land {int(made.sum())} cells, city {int(is_city.sum())}, park {int(is_park.sum())}, farms {int(farm_ok.sum())}")
    wood_y = np.where(regrow, np.fmax(ground_y + 25.0, 1900.0 + 60.0 * h), np.nan).astype(np.float32)
    return covers, years, elev, urban_y, np.where(is_park, park_y, np.nan).astype(np.float32), wood_y


WINDOW_CELLS = 8_000_000   # a grid larger than this is worked in windows (the whole region is 28 million cells)
WINDOW_TILES = 32          # the core of a window, in tiles of the grid
WINDOW_MARGIN = 3          # ... and the tiles around it that are computed and thrown away (11 km)


def histories_whole(name, g, d, **kw):
    """histories() for a grid of any size. A small grid is done in one piece. The whole region
    (5,377 x 5,249 cells) does not fit in memory in one piece - every change of cover is a full
    array - so it is worked in windows of WINDOW_TILES tiles with a margin, and the cores are
    put together. What reaches further than the margin (the nearest built-up ground of an empty
    district, a county's order of clearing) is taken per window; the noise is the whole grid's,
    so fields and woodlots run on across a window's edge. A window wholly beyond the map's
    outline is not computed: water where WorldCover has none or water, forest elsewhere."""
    from extent import POLY
    rows, cols = g["rows"], g["cols"]
    if rows * cols <= WINDOW_CELLS:
        _H_OFF[0] = _H_OFF[1] = 0
        return histories(name, g, d, **kw)
    covers = np.zeros((5, rows, cols), np.uint8)
    years = np.full((4, rows, cols), np.nan, np.float32)
    urban_y = np.full((rows, cols), np.nan, np.float32)
    park_y = np.full((rows, cols), np.nan, np.float32)
    wood_y = np.full((rows, cols), np.nan, np.float32)
    made = np.zeros((rows, cols), bool)
    elev = np.nan_to_num(d["elev"], nan=0.0).astype(np.float32)
    keep = POLY.buffer(0.05)
    shapely.prepare(keep)
    ntx, nty = g["tx1"] - g["tx0"], g["ty1"] - g["ty0"]
    k = 0
    for wy in range(0, nty, WINDOW_TILES):
        for wx in range(0, ntx, WINDOW_TILES):
            cx0, cy0 = wx, wy
            cx1, cy1 = min(wx + WINDOW_TILES, ntx), min(wy + WINDOW_TILES, nty)
            # core, in cells of the whole grid (the last row / column of vertices belongs to the last window)
            r0, r1 = cy0 * VERTS, (cy1 * VERTS + 1 if cy1 == nty else cy1 * VERTS)
            c0, c1 = cx0 * VERTS, (cx1 * VERTS + 1 if cx1 == ntx else cx1 * VERTS)
            w, s_, e, n_ = tile_lonlat(g["tx0"] + cx0, g["ty0"] + cy1 - 1, g["z"])[0], tile_lonlat(g["tx0"] + cx0, g["ty0"] + cy1 - 1, g["z"])[1], \
                tile_lonlat(g["tx0"] + cx1 - 1, g["ty0"] + cy0, g["z"])[2], tile_lonlat(g["tx0"] + cx1 - 1, g["ty0"] + cy0, g["z"])[3]
            if not shapely.intersects(keep, shapely.box(w, s_, e, n_)):
                wcw = d["wc"][r0:r1, c0:c1]
                base = np.where(np.isin(wcw, [0, 80]), DEEP, FOREST).astype(np.uint8)
                covers[:, r0:r1, c0:c1] = base[None]
                continue
            mx0, my0 = max(cx0 - WINDOW_MARGIN, 0), max(cy0 - WINDOW_MARGIN, 0)
            mx1, my1 = min(cx1 + WINDOW_MARGIN, ntx), min(cy1 + WINDOW_MARGIN, nty)
            R0, R1, C0, C1 = my0 * VERTS, my1 * VERTS + 1, mx0 * VERTS, mx1 * VERTS + 1
            res = g["res"]
            X0, Y0 = g["X0"] + C0 * res, g["Y0"] - R0 * res
            gw = {"name": name, "z": g["z"], "tx0": g["tx0"] + mx0, "ty0": g["ty0"] + my0, "tx1": g["tx0"] + mx1, "ty1": g["ty0"] + my1,
                  "rows": R1 - R0, "cols": C1 - C0, "res": res, "X0": X0, "Y0": Y0,
                  "transform": Affine(res, 0, X0 - res / 2, 0, -res, Y0 + res / 2),
                  "win": (slice(R0, R1), slice(C0, C1)), "whole": (rows, cols)}
            dw = {"elev": d["elev"][R0:R1, C0:C1], "wc": d["wc"][R0:R1, C0:C1]}
            _H_OFF[0], _H_OFF[1] = R0, C0
            k += 1
            log(f"terrain {name}: window {k}: tiles x {gw['tx0']}..{gw['tx1']} y {gw['ty0']}..{gw['ty1']} ({gw['rows']} x {gw['cols']} cells)")
            cw, yw, _, uw, pw, ww = histories(name, gw, dw, **kw)
            rr, cc = slice(r0 - R0, r1 - R0), slice(c0 - C0, c1 - C0)
            covers[:, r0:r1, c0:c1] = cw[:, rr, cc]
            years[:, r0:r1, c0:c1] = yw[:, rr, cc]
            urban_y[r0:r1, c0:c1] = uw[rr, cc]
            park_y[r0:r1, c0:c1] = pw[rr, cc]
            wood_y[r0:r1, c0:c1] = ww[rr, cc]
            made[r0:r1, c0:c1] = _MADE[name][rr, cc]
            del cw, yw, uw, pw, ww
    _H_OFF[0] = _H_OFF[1] = 0
    _MADE[name] = made
    return covers, years, elev, urban_y, park_y, wood_y


def decorations(name, g, covers, years, elev, urban_y, park_y, wood_y):
    """Return a function (tx, ty) -> decoration columns for that native tile: the forest of
    1609 until its cell is cleared (procedural positions in real forest cells), and today's
    trees on real WorldCover canopy pixels, dated by their park / the buildings around."""
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.warp import reproject
    from terrain_grid import wc_tiles

    _, lon0, lat0, lon1, lat1 = GRIDS[name]
    sub = 4 if name == "detail" else 2
    res = g["res"] / sub
    t = Affine(res, 0, g["X0"] - g["res"] / 2, 0, -res, g["Y0"] + g["res"] / 2)
    shape = (g["rows"] * sub, g["cols"] * sub)
    fine = np.zeros(shape, np.uint8)
    for url in wc_tiles(lon0, lat0, lon1, lat1):
        try:
            opts = {"overview_level": 0} if name == "region" else {}
            with rasterio.open(url, **opts) as src:
                tmp = np.zeros(shape, np.uint8)
                reproject(rasterio.band(src, 1), tmp, src_nodata=0, dst_transform=t, dst_crs="EPSG:3857", dst_nodata=0,
                          resampling=Resampling.mode, num_threads=4)
                fine = np.where(tmp > 0, tmp, fine)
        except Exception as e:  # noqa: BLE001
            log(f"deco {name}: skip {url.split('/')[-1]} {e}")
    tree_fine = fine == 10
    del fine
    land_year = land_year_of(covers, years)
    # no trees on sports fields or inside building footprints
    blockers = []
    lu = OVT / "base_land_use.parquet"
    if lu.exists():
        gl = read_wkb_parquet(lu, lambda d: d["class"].isin(["stadium", "pitch", "track", "fairway", "green", "tee", "bunker", "driving_range"]))
        blockers += [(geom, 1) for geom in gl.geometry if geom is not None]
    bpath = INTERIM / "nyc_buildings.parquet"
    if name == "detail" and bpath.exists():
        bg = gpd.read_parquet(bpath, columns=["geometry"]).to_crs(3857)
        blockers += [(geom, 1) for geom in bg.geometry if geom is not None]
        del bg
    if blockers:
        block = features.rasterize(blockers, out_shape=shape, transform=t, fill=0, dtype="uint8").astype(bool)
        tree_fine &= ~block
        del block, blockers
    # the city's tree inventory stands for itself (street_trees.py): no canopy tree on its cells
    if name == "detail":
        try:
            from street_trees import inventory_mask
            tree_fine &= ~inventory_mask(t, shape, reach=1)
        except Exception as e:  # noqa: BLE001
            log(f"terrain {name}: tree inventory not used to thin the canopy trees ({type(e).__name__}: {e})")
    # the 1609 forest: cells whose natural cover is forest and that were cleared later
    nat_forest = covers[0] == FOREST
    cleared_y = np.where(nat_forest & (covers[1] != FOREST), years[0], np.nan).astype(np.float32)
    stays = nat_forest & ~np.isfinite(cleared_y)
    log(f"deco {name}: canopy sub-cells {int(tree_fine.sum())}, forest cells cleared later {int(np.isfinite(cleared_y).sum())}")

    def at_vertex(arr, fy, fx):
        return arr[np.clip(np.rint(fy / sub).astype(int), 0, g["rows"] - 1), np.clip(np.rint(fx / sub).astype(int), 0, g["cols"] - 1)]

    def fn(tx, ty):
        r0 = (ty - g["ty0"]) * VERTS * sub
        c0 = (tx - g["tx0"]) * VERTS * sub
        rs = slice(max(r0, 0), min(r0 + VERTS * sub, shape[0]))
        cs = slice(max(c0, 0), min(c0 + VERTS * sub, shape[1]))
        rng = np.random.default_rng(1609 + tx * 100003 + ty)
        kinds, ys, xs, sizes, starts, ends = [], [], [], [], [], []
        # The outer counties' tier (docs/OUTER_ROUND.md): a wooded tile stores 20,000 trees, and
        # beyond the inner counties that alone would be several hundred megabytes. There a
        # share of them is kept, each drawn larger, so the woods read the same from above.
        w, s_, e, n_ = tile_lonlat(tx, ty, g["z"])
        outer = name == "region" and not (INNER_BBOX[0] <= (w + e) / 2 <= INNER_BBOX[2] and INNER_BBOX[1] <= (s_ + n_) / 2 <= INNER_BBOX[3])
        thin, grow = (OUTER_TREES, OUTER_TREE_SIZE) if outer else (1.0, 1.0)
        # --- today's trees on real canopy pixels
        tr, tc = np.nonzero(tree_fine[rs, cs])
        keep = rng.random(len(tr)) < (0.45 if name == "detail" else 0.3) * thin
        tr, tc = tr[keep] + rs.start, tc[keep] + cs.start
        if len(tr):
            fy = tr + rng.uniform(-0.45, 0.45, len(tr))
            fx = tc + rng.uniform(-0.45, 0.45, len(tr))
            uy = at_vertex(urban_y, fy, fx)
            py = at_vertex(park_y, fy, fx)
            wy = at_vertex(wood_y, fy, fx)
            always = at_vertex(stays, fy, fx)
            start = np.full(len(fy), np.nan)
            start = np.where(np.isfinite(wy), wy + rng.uniform(0, 4, len(fy)), start)
            start = np.where(np.isnan(start) & np.isfinite(py), py + rng.uniform(2, 12, len(fy)), start)
            start = np.where(np.isnan(start) & np.isfinite(uy), uy + rng.uniform(5, 25, len(fy)), start)
            # canopy with no date at all on ground that was cleared: second growth after the clearing
            cy = at_vertex(cleared_y, fy, fx)
            start = np.where(np.isnan(start) & np.isfinite(cy), np.fmax(cy + 40, 1880) + rng.uniform(0, 50, len(fy)), start)
            ly = at_vertex(land_year, fy, fx)
            start = np.where(np.isfinite(ly), np.fmax(np.nan_to_num(start, nan=-1e9), ly + rng.uniform(4, 15, len(fy))), start)
            start = np.where(always & ~np.isfinite(ly), np.nan, start)   # woods that never went: always there
            kind = np.where(rng.random(len(fy)) < 0.08, D_CONIFER, D_BROADLEAF)
            size = np.where(kind == D_CONIFER, rng.uniform(12, 22, len(fy)), rng.uniform(9, 19, len(fy)))
            size = np.where(np.isfinite(uy) & np.isnan(wy), size * 0.75, size)
            kinds.append(kind); ys.append(fy); xs.append(fx); sizes.append(size); starts.append(start); ends.append(np.full(len(fy), np.nan))
        # --- the forest of 1609 on cells cleared later (it stands until the clearing)
        cr0, cc0 = max(r0 // sub, 0), max(c0 // sub, 0)
        cy_t = cleared_y[cr0:min(r0 // sub + VERTS, g["rows"]), cc0:min(c0 // sub + VERTS, g["cols"])]
        vy, vx = np.nonzero(np.isfinite(cy_t))
        if len(vy):
            per = 9 if name == "detail" else 3
            vy = np.repeat(vy, per); vx = np.repeat(vx, per)
            # (trees are drawn at about twice their size: one or two per 29 m cell read as closed forest)
            keep = rng.random(len(vy)) < (0.42 if name == "detail" else 0.4) * thin
            vy, vx = vy[keep], vx[keep]
            fy = (vy + cr0 + rng.uniform(-0.5, 0.5, len(vy))) * sub
            fx = (vx + cc0 + rng.uniform(-0.5, 0.5, len(vy))) * sub
            end = cy_t[vy, vx] - rng.uniform(0, 6, len(vy))
            kind = np.where(rng.random(len(fy)) < 0.08, D_CONIFER, D_BROADLEAF)
            kinds.append(kind); ys.append(fy); xs.append(fx)
            sizes.append(np.where(kind == D_CONIFER, rng.uniform(14, 24, len(fy)), rng.uniform(11, 21, len(fy))))
            starts.append(np.full(len(fy), np.nan)); ends.append(end)
        if not kinds:
            return {}
        kinds = np.concatenate(kinds); ys = np.concatenate(ys); xs = np.concatenate(xs)
        sizes = np.concatenate(sizes); starts = np.concatenate(starts); ends = np.concatenate(ends)
        ly = np.clip((ys / sub - (ty - g["ty0"]) * VERTS) / VERTS * 65535, 0, 65535)
        lx = np.clip((xs / sub - (tx - g["tx0"]) * VERTS) / VERTS * 65535, 0, 65535)
        # Positions to about a metre (multiples of 32 of the tile's 65,535) and years to whole
        # years: trees need no more, and the files gzip much smaller. Quantised HERE, before
        # the rank-based pruning, because the viewer ranks a tree by its stored position.
        return {
            "deco_pos": (np.column_stack([lx, ly]).astype(np.uint16) & np.uint16(0xFFE0)).ravel(),
            "deco_kind": kinds.astype(np.uint8),
            "deco_size": np.clip(np.rint(sizes * grow / 2) * 2, 2, 254).astype(np.uint8),
            "deco_years": np.column_stack([enc_year(np.round(starts)), enc_year(np.round(ends))]).ravel(),
        }

    return fn


INNER_BBOX = (-74.52, 40.47, -73.40, 41.38)   # the city and the seven counties around it: full tree density
OUTER_TREES = 0.3          # share of the trees stored beyond it
OUTER_TREE_SIZE = 1.6      # ... each drawn this much larger


def tile_lonlat(tx, ty, z):
    """(west, south, east, north) of a tile."""
    n = 2.0 ** z
    lat = lambda y: math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))   # noqa: E731
    return tx / n * 360.0 - 180.0, lat(ty + 1), (tx + 1) / n * 360.0 - 180.0, lat(ty)


def write_tiles(name, g, covers, years, elev, deco_fn=None, zooms=None):
    from extent import POLY
    z_native = g["z"]
    zooms = zooms or [z_native]
    count = skipped = 0
    # (the grid is a box, the map is the counties: a tile wholly beyond the map's outline - the
    # Catskills, Pennsylvania, eastern Connecticut - is not written)
    keep = POLY.buffer(0.03)
    shapely.prepare(keep)
    for z in zooms:
        k = 2 ** (z_native - z)
        tx0 = g["tx0"] // k
        tx1 = -(-g["tx1"] // k)
        ty0 = g["ty0"] // k
        ty1 = -(-g["ty1"] // k)
        for tx in range(tx0, tx1):
            for ty in range(ty0, ty1):
                if not shapely.intersects(keep, shapely.box(*tile_lonlat(tx, ty, z))):
                    skipped += 1
                    continue
                # native-lattice vertex indices for this tile
                gx = (tx * k - g["tx0"]) * VERTS + np.arange(VERTS + 1) * k
                gy = (ty * k - g["ty0"]) * VERTS + np.arange(VERTS + 1) * k
                inside_x = (gx >= 0) & (gx < g["cols"])
                inside_y = (gy >= 0) & (gy < g["rows"])
                if not inside_x.any() or not inside_y.any():
                    continue
                gxc = np.clip(gx, 0, g["cols"] - 1)
                gyc = np.clip(gy, 0, g["rows"] - 1)
                sel = np.ix_(gyc, gxc)
                cv = covers[:, sel[0], sel[1]].copy()
                yr = years[:, sel[0], sel[1]].copy()
                el = elev[sel].copy()
                outside = ~np.outer(inside_y, inside_x)
                cv[:, outside] = DEEP
                yr[:, outside] = np.nan
                el[outside] = -10
                if (cv[0] == DEEP).all() and np.isnan(yr).all():
                    continue  # open water: the water plane covers it
                cols = {
                    "elev": np.clip(np.rint(el * 10), -32000, 32000).astype(np.int16).ravel(),
                    "cover": np.moveaxis(cv, 0, -1).reshape(-1).astype(np.uint8),
                    "year": enc_year(np.moveaxis(yr, 0, -1).reshape(-1)),
                }
                if deco_fn is not None and z == z_native:
                    cols.update(deco_fn(tx, ty))
                out = TILES / str(z) / str(tx) / f"{ty}.bin.gz"
                write_columnar(out, cols, counts={"n": VERTS + 1, "z": z, "x": tx, "y": ty,
                                                  "deco": int(len(cols.get("deco_kind", [])))})
                count += 1
    log(f"terrain {name}: wrote {count} tiles for zooms {zooms} ({skipped} beyond the map's outline left out)")


def land_year_of(covers, years):
    """Year each vertex became dry land (NaN: always land, or still water)."""
    wet0 = np.isin(covers[0], list(WET))
    out = np.full(covers.shape[1:], np.nan, np.float32)
    for e in range(4):
        became = wet0 & np.isnan(out) & ~np.isin(covers[e + 1], list(WET)) & np.isfinite(years[e])
        out[became] = years[e][became]
    return out


def write_elevation_lookup(name, g, elev, step):
    """Coarse elevation grid for the viewer (placing landmarks, labels, cars)."""
    e = elev[::step, ::step]
    out = VIEWER_DATA / f"elevation-{name}.bin.gz"
    write_columnar(out, {"elev": np.clip(np.rint(e * 10), -32000, 32000).astype(np.int16).ravel()},
                   counts={"rows": e.shape[0], "cols": e.shape[1]},
                   meta={"X0": g["X0"], "Y0": g["Y0"], "res": g["res"] * step, "units": "decimetres, EPSG:3857 vertex lattice"})
    log(f"terrain {name}: elevation lookup {e.shape} -> {out}")


def region_under_detail(g, elev):
    """Where the 30 m detail grid exists (San Francisco), the coarse region tiles shown
    from further out never rise above it: each region cell takes the lowest detail
    elevation around it. Roads, rails and buildings are draped on the detail grid, so a
    freeway in a cut (US-101 below Potrero Hill) is no longer buried under the averaged
    hillside until the detail tiles load."""
    from terrain_grid import grid_def
    gd = grid_def("detail")
    ed = np.load(INTERIM / "grid_detail_elev.npy").astype(np.float32)
    ed = np.where(ed < -500, np.nan, ed)
    mn = ndimage.minimum_filter(np.nan_to_num(ed, nan=1e4), size=3)
    rows, cols = elev.shape
    X = g["X0"] + (np.arange(cols) + 0.5) * g["res"]
    Y = g["Y0"] - (np.arange(rows) + 0.5) * g["res"]
    c = np.floor((X - gd["X0"]) / gd["res"]).astype(int)
    r = np.floor((gd["Y0"] - Y) / gd["res"]).astype(int)
    okc = (c >= 0) & (c < gd["cols"])
    okr = (r >= 0) & (r < gd["rows"])
    out = elev.copy()
    sub = mn[np.ix_(r[okr], c[okc])]
    reg = out[np.ix_(np.nonzero(okr)[0], np.nonzero(okc)[0])]
    valid = sub < 5e3
    reg[valid] = np.minimum(reg[valid], sub[valid])
    out[np.ix_(np.nonzero(okr)[0], np.nonzero(okc)[0])] = reg
    log(f"terrain region: {int(valid.sum())} cells capped by the detail grid")
    return out


def merge_detail_deco():
    """The z13 region tiles over the detail grid carry the detail grid's decorations (the
    trees, orchards and farmsteads of their z14 children) instead of their own: the viewer
    shows z13 tiles from zoom 11.5 and z14 tiles from 12.5, and two independently placed
    sets would swap every tree in the urban bay plain at that zoom."""
    from export_columnar import read_bayt
    kids = {}
    for f in (TILES / "14").glob("*/*.bin.gz"):
        x, y = int(f.parent.name), int(f.name.split(".")[0])
        kids.setdefault((x >> 1, y >> 1), []).append((x, y, f))
    n_par = n_add = 0
    for (px, py), ch in kids.items():
        pf = TILES / "13" / str(px) / f"{py}.bin.gz"
        if not pf.exists():
            continue
        h, c = read_bayt(pf)
        pos = c.get("deco_pos", np.zeros(0, np.uint16)).reshape(-1, 2)
        kind = c.get("deco_kind", np.zeros(0, np.uint8))
        size = c.get("deco_size", np.zeros(0, np.uint8))
        yrs = c.get("deco_years", np.zeros(0, np.uint16)).reshape(-1, 2)
        qx = (pos[:, 0] >= 32768).astype(int)
        qy = (pos[:, 1] >= 32768).astype(int)
        keep = np.ones(len(kind), bool)
        P, K, S, Yr = [], [], [], []
        for x, y, f in ch:
            ox, oy = x - 2 * px, y - 2 * py
            keep &= ~((qx == ox) & (qy == oy))
            _, cc = read_bayt(f)
            if "deco_kind" not in cc or not len(cc["deco_kind"]):
                continue
            cp = cc["deco_pos"].reshape(-1, 2).astype(np.float64)
            P.append(np.column_stack([(ox * 65535 + cp[:, 0]) / 2, (oy * 65535 + cp[:, 1]) / 2]))
            K.append(cc["deco_kind"]); S.append(cc["deco_size"]); Yr.append(cc["deco_years"].reshape(-1, 2))
        P = np.concatenate([pos[keep].astype(np.float64)] + P) if P else pos[keep].astype(np.float64)
        K = np.concatenate([kind[keep]] + K) if K else kind[keep]
        S = np.concatenate([size[keep]] + S) if S else size[keep]
        Yr = np.concatenate([yrs[keep]] + Yr) if Yr else yrs[keep]
        cols = {k: c[k] for k in ("elev", "cover", "year")}
        if len(K):
            cols.update({"deco_pos": np.clip(np.rint(P), 0, 65535).astype(np.uint16).ravel(),
                         "deco_kind": K.astype(np.uint8), "deco_size": S.astype(np.uint8),
                         "deco_years": Yr.astype(np.uint16).ravel()})
        counts = dict(h.get("counts", {}), deco=int(len(K)))
        write_columnar(pf, cols, counts=counts)
        n_par += 1
        n_add += int(len(K)) - int(keep.sum())
    log(f"terrain: {n_par} z13 tiles over the detail grid take its decorations ({n_add:+d} instances)")


def rank_byte(lon, lat):
    """rankByte() of viewer/src/layers/deco-layer.ts (32-bit integer hash of the position)."""
    M = np.uint64(0xFFFFFFFF)
    a = np.floor(np.asarray(lon, np.float64) * 3.3e4 + 0.5).astype(np.int64).astype(np.uint64) & M
    b = np.floor(np.asarray(lat, np.float64) * 3.3e4 + 0.5).astype(np.int64).astype(np.uint64) & M
    h = ((a * np.uint64(73856093)) & M) ^ ((b * np.uint64(19349663)) & M)
    h = ((h ^ (h >> np.uint64(13))) * np.uint64(0x5BD1E995)) & M
    h ^= h >> np.uint64(15)
    return (h % np.uint64(256)).astype(np.int64)


def prune_unseen_deco():
    """Drop the decorations the viewer never draws (2026-11: the published site had grown to
    half a gigabyte, four fifths of the terrain tiles being tree records). The tile loader
    (decodeTile in viewer/src/layers/terrain.ts) skips, by the tree's position rank,
      * broadleaf / conifer trees of rank > 0.4 in a dense tile (> 6,000 instances per z13
        tile area) at every zoom, and
      * every tree, shrub and orchard tree of rank > 0.4 in a z13 tile drawn as such — the
        only way a z13 tile under four z14 detail tiles is ever drawn.
    The same test here, with the same hash on the same coordinates, so nothing visible
    changes; the viewer keeps its own test."""
    from export_columnar import read_bayt
    n_tiles = n_drop = n_all = 0
    for z in (13, 14):
        for f in (TILES / str(z)).glob("*/*.bin.gz"):
            x, y = int(f.parent.name), int(f.name.split(".")[0])
            h, c = read_bayt(f)
            if "deco_kind" not in c or not len(c["deco_kind"]):
                continue
            kind = c["deco_kind"]
            pos = c["deco_pos"].reshape(-1, 2)
            gx = pos[:, 0].astype(np.float64) / 65535 * 64
            gy = pos[:, 1].astype(np.float64) / 65535 * 64
            west, east = x / 2 ** z * 360 - 180, (x + 1) / 2 ** z * 360 - 180
            lon = west + ((east - west) * gx) / 64
            nn = math.pi - (2 * math.pi * (y + gy / 64)) / 2 ** z
            lat = (180 / math.pi) * np.arctan(np.sinh(nn))
            high = rank_byte(lon, lat) / 255 > 0.4
            dense = len(kind) * (4 if z == 14 else 1) > 6000
            drop = high & (kind <= 1) & dense
            if z == 13 and all((TILES / "14" / str(2 * x + i) / f"{2 * y + j}.bin.gz").exists() for i in (0, 1) for j in (0, 1)):
                # (the overview tiles keep the share the viewer draws below zoom 12.5:
                # decoration-meshes.ts treeLod keep = 0.15)
                drop |= rank_byte(lon, lat) / 255 > 0.15
            n_all += len(kind)
            if not drop.any():
                continue
            keep = ~drop
            cols = {k: c[k] for k in ("elev", "cover", "year")}
            cols.update({"deco_pos": pos[keep].ravel(), "deco_kind": kind[keep], "deco_size": c["deco_size"][keep],
                         "deco_years": c["deco_years"].reshape(-1, 2)[keep].ravel()})
            write_columnar(f, cols, counts=dict(h.get("counts", {}), deco=int(keep.sum())))
            n_tiles += 1
            n_drop += int(drop.sum())
    log(f"terrain: {n_drop} of {n_all} decorations the viewer never draws removed from {n_tiles} tiles")


def pack_tiles():
    """Last pass over the z13 / z14 tiles: decorations sorted by position and the 16-bit
    columns byte-shuffled, so the files gzip a quarter smaller (the published site must stay
    small: CLAUDE.md "Hosting"). Nothing the viewer reads changes: the reader un-shuffles,
    and the order of decorations carries no meaning."""
    from export_columnar import read_bayt
    before = after = 0
    for z in (13, 14):
        for f in (TILES / str(z)).glob("*/*.bin.gz"):
            before += f.stat().st_size
            h, c = read_bayt(f)
            cols = {"elev|shuffle": c["elev"], "cover": c["cover"], "year|shuffle": c["year"]}
            if "deco_kind" in c and len(c["deco_kind"]):
                pos = c["deco_pos"].reshape(-1, 2)
                yrs = c["deco_years"].reshape(-1, 2)
                # by position (coarse rows, then coarse columns): neighbours share high bytes and years
                o = np.lexsort((pos[:, 0], pos[:, 1], pos[:, 0] >> 9, pos[:, 1] >> 9))
                cols.update({"deco_pos|shuffle": np.ascontiguousarray(pos[o]).ravel(), "deco_kind": c["deco_kind"][o],
                             "deco_size": c["deco_size"][o], "deco_years|shuffle": np.ascontiguousarray(yrs[o]).ravel()})
            write_columnar(f, cols, counts=h.get("counts", {}))
            after += f.stat().st_size
    log(f"terrain: tiles packed, {before / 1e6:.1f} MB -> {after / 1e6:.1f} MB")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "land":
        for name in ("region", "detail"):
            # the same cover histories as the full run (so the year a cell turns to land is
            # the one the viewer shows), recomputed from the evidence and the buildings on disk
            g, d = load_grid(name)
            covers, years = histories_whole(name, g, d, reuse_land=False)[:2]
            np.save(INTERIM / f"grid_{name}_landyear.npy", made_land_year(name, covers, years))
        return
    meta = {}
    for name, zooms, step in (("region", [8, 9, 10, 11, 12, 13], 2), ("detail", [14], 2)):
        g, d = load_grid(name)
        covers, years, elev, urban_y, park_y, wood_y = histories_whole(name, g, d)
        if name == "region":
            elev = region_under_detail(g, elev)
        deco = decorations(name, g, covers, years, elev, urban_y, park_y, wood_y)
        write_tiles(name, g, covers, years, elev, deco, zooms)
        write_elevation_lookup(name, g, elev, step)
        np.save(INTERIM / f"grid_{name}_landyear.npy", made_land_year(name, covers, years))
        np.save(INTERIM / f"grid_{name}_covers.npy", covers)
        np.save(INTERIM / f"grid_{name}_years.npy", years)
        meta[name] = {"z": g["z"], "tx0": g["tx0"], "ty0": g["ty0"], "tx1": g["tx1"], "ty1": g["ty1"], "zooms": zooms}
    merge_detail_deco()
    prune_unseen_deco()
    pack_tiles()
    (VIEWER_DATA / "terrain.json").write_text(json.dumps({"grids": meta, "covers": COVER_NAMES,
                                                          "deco": ["broadleaf", "conifer", "palm", "orchard", "farmhouse", "shrub", "farmyard"]}, indent=1))


if __name__ == "__main__":
    main()
