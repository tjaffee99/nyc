"""Assemble the c.1609 natural landscape of one county (or merge the counties into the delivered files).

usage:  python assemble.py NJ017        -> data/interim/natural_counties/polys_NJ017.parquet, stats_NJ017.json
        python assemble.py merge        -> data/manual/natural/counties/natural_1609_counties.geojson,
                                           natural_stats_counties.json, usgs_sheets_counties.json

A 6 m cell of today's land (the soil survey's land of that county; cells of the five boroughs' survey areas and
cells under a polygon of the city layer are left out) is decided, in this order, by its NRCS soil map unit
(classes: ssurgo_load.py) and by the USGS sheet of 1888-1901 (sheets.py):

  fill over wet ground ("wet substratum")   marsh / water as the sheet shows it; where the sheet shows land already
                                            (or there is no usable sheet): water within 150 m of open tidewater, salt
                                            marsh farther in, freshwater wetland where not connected to tidewater
                                            (estimated)
  fill over marsh peat ("organic substr.")  tidal_marsh (freshwater_wetland where not connected to tidewater)
  tidal-marsh soils / intertidal sand       tidal_marsh (still marsh today) / tidal_flat
  hydric natural soils                      freshwater_wetland
  fill and urban land that does not say     what the sheet shows: water / marsh / dry; beaches and dunes stay beach /
  what it covers; beaches; dunes            dunes unless the sheet shows water or marsh
  upland soils                              dry (nothing written), except blocks >= 2 ha that the sheet shows wet
                                            >= 36 m inside the unit (confidence low)
  reservoirs of data/manual/fill_zones_counties.csv   dry_valley over today's water

"Tidal" = connected to today's tidal water (sea.tif) through cells that are water or marsh on the sheet, tidal
water today, or wet / organic-substratum fill and marsh soils lying below 8 m, without crossing today's non-tidal
water (surface above 3 m).
Blank paper on a sheet is either land or open water (the water lining stops a few hundred metres from shore): two
fronts spread through the blank cells, one from natural upland and dune soils, one from today's open tidewater
that the sheet leaves blank; a blank cell belongs to the front that reaches it first.  Blank patches neither front
reaches (enclosed by lining or marsh): water if >= 60 % of the patch is water today, holes under 3 ha take what
surrounds them (marsh or water), the rest is land (islands, barrier beaches).  This is used only where the sheet
does line its water (>= 40 % of today's tidal water within 120 m of natural upland soil is wet on it); on a sheet without usable lining, and
where there is no sheet, blank paper says nothing and only the soil survey decides.
A county larger than 26 million cells is worked in horizontal bands with a 1200 m margin (memory).
"""
import glob
import json
import os
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio import features
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject
from scipy import ndimage
from shapely.geometry import Polygon

import rastools as rt
from common import (AMBIG, AREAS, BEACH, D, DUNES, FRESH, GRID, MARSHSUB, OUT, RAW, ROOT, SHEETS, TFLAT, TMARSH, UPLAND, WATER, WETSUB)

PX = GRID["px"]
COV = {1: "water", 2: "tidal_marsh", 3: "tidal_flat", 4: "beach", 5: "dunes", 6: "pond", 7: "freshwater_wetland", 8: "dry_valley"}
CROSS = ndimage.generate_binary_structure(2, 1)
SQ = np.ones((3, 3), bool)
MARGIN = 200          # cells (1200 m)
MAXCELLS = 26e6
SID = [v[4] for v in SHEETS.values()]
SKIP_RESERVOIRS = ("Greenwood Lake", "Weequahic", "Branch Brook")   # a natural lake raised by a dam; two lakes dug in marsh

# kind -> (source: "ssurgo" or "sheet", confidence, note)
KINDS = {
    1: ("sheet", "medium", "water on the USGS sheet, land today"),
    2: ("sheet", "low", "marsh on the USGS sheet (marsh / water split by print texture), land today"),
    3: ("sheet", "low", "marsh on the USGS sheet not connected to tidal water, land today"),
    4: ("sheet", "low", "inland water on the USGS sheet, land today (may be a mill pond or reservoir of the 19th century)"),
    5: ("sheet", "medium", "marsh on the USGS sheet; soil survey: fill over wet substratum"),
    6: ("sheet", "medium", "marsh on the USGS sheet not connected to tidal water; soil survey: fill over wet substratum"),
    7: ("ssurgo", "low", "soil survey: fill over wet substratum; land already on the USGS sheet, or no usable sheet; within 150 m of open tidewater, so taken as filled water (estimated)"),
    8: ("ssurgo", "low", "soil survey: fill over wet substratum; land already on the USGS sheet, or no usable sheet; over 150 m from open tidewater, so taken as salt marsh (estimated)"),
    9: ("ssurgo", "low", "soil survey: fill over wet substratum, not connected to tidewater; taken as freshwater wetland (estimated; the survey does not say swamp, wet meadow or flood plain)"),
    10: ("ssurgo", "medium", "soil survey: Udorthents, organic substratum (fill over marsh peat)"),
    11: ("ssurgo", "medium", "soil survey: Udorthents, organic substratum (fill over peat), not connected to tidewater"),
    12: ("ssurgo", "high", "soil survey: tidal-marsh soil, still marsh today"),
    13: ("ssurgo", "medium", "soil survey: intertidal sand"),
    14: ("ssurgo", "medium", "soil survey: hydric natural soil (muck, or poorly drained mineral soil, >= 85 % hydric)"),
    15: ("ssurgo", "low", "soil survey: beach today; barrier beaches have moved since 1609 (not reconstructed)"),
    16: ("ssurgo", "low", "soil survey: dune sand today; barrier beaches have moved since 1609 (not reconstructed)"),
    17: ("sheet", "low", "water on the USGS sheet, land today; soil survey maps upland here"),
    18: ("sheet", "low", "marsh on the USGS sheet, land today; soil survey maps upland here"),
    19: ("sheet", "low", "marsh on the USGS sheet not connected to tidal water; soil survey maps upland here"),
    20: ("sheet", "low", "inland water on the USGS sheet, land today; soil survey maps upland here"),
    21: ("sheet", "medium", "water on the USGS sheet, land today; soil survey: fill over wet substratum"),
    22: ("sheet", "low", "blank on the USGS sheet seaward of its water lining (open water is not lined far from shore), land today: taken as open water"),
    23: ("sheet", "low", "blank on the USGS sheet seaward of its water lining, land today: taken as open water; soil survey: fill over wet substratum"),
}


def erode(m, r):
    a = ndimage.binary_erosion(m, structure=CROSS, iterations=r - r // 2)
    return ndimage.binary_erosion(a, structure=SQ, iterations=r // 2) if r // 2 else a


def dilate(m, r):
    a = ndimage.binary_dilation(m, structure=CROSS, iterations=r - r // 2)
    return ndimage.binary_dilation(a, structure=SQ, iterations=r // 2) if r // 2 else a


def big_parts(mask, min_cells):
    lab, n = ndimage.label(mask)
    if not n:
        return mask
    keep = np.nonzero(np.bincount(lab.ravel())[1:] >= min_cells)[0] + 1
    return np.isin(lab, keep)


def blank_paper(blank, land_anchor, sea_anchor, u_marsh, u_water, water_today):
    """Decide blank paper at 24 m: returns (pale_water, pale_marsh) masks at 6 m.  See the module docstring."""
    h, w = blank.shape
    red = lambda a: a.reshape(h // 4, 4, w // 4, 4).mean(axis=(1, 3), dtype="float32")
    b = red(blank) >= 0.5
    st = np.zeros(b.shape, "uint8")                      # 1 land front, 2 water front
    st[b & (red(land_anchor) >= 0.5)] = 1
    st[b & (red(sea_anchor) >= 0.9) & (st == 0)] = 2
    for _ in range(4000):
        free = b & (st == 0)
        if not free.any():
            break
        nl = ndimage.binary_dilation(st == 1, structure=SQ) & free
        nw = ndimage.binary_dilation(st == 2, structure=SQ) & free & ~nl
        if not nl.any() and not nw.any():
            break
        st[nl] = 1
        st[nw] = 2
    m24, w24, wt24 = red(u_marsh), red(u_water), red(water_today)
    rest = b & (st == 0)
    lab, n = ndimage.label(rest)
    pw, pm = st == 2, np.zeros(b.shape, bool)
    if n:
        idx = np.arange(1, n + 1)
        size = ndimage.sum(rest, lab, index=idx)
        wshare = ndimage.mean(wt24, lab, index=idx)
        dil = ndimage.maximum_filter(lab, size=3)
        ring = (dil > 0) & (lab == 0)
        ids = dil[ring]
        mc = np.bincount(ids, weights=m24[ring], minlength=n + 1)[1:]
        wc = np.bincount(ids, weights=np.maximum(w24, wt24)[ring], minlength=n + 1)[1:]
        tc = np.bincount(ids, minlength=n + 1)[1:]
        enclosed = (mc + wc) > 0.5 * np.maximum(tc, 1)
        as_w = (wshare >= 0.6) | ((size * 576 < 3e4) & enclosed & (wc >= mc))
        as_m = (size * 576 < 3e4) & enclosed & (mc > wc) & ~as_w
        pw |= np.isin(lab, idx[as_w])
        pm |= np.isin(lab, idx[as_m])
    up = lambda a: np.repeat(np.repeat(a, 4, axis=0), 4, axis=1)
    return up(pw) & blank, up(pm) & blank


def reservoir_rings():
    """Reservoir outlines the lead's fill zones carry (name, year, source), as UTM polygons."""
    f = f"{ROOT}/data/manual/fill_zones_counties.csv"
    if not os.path.exists(f):
        return []
    t = pd.read_csv(f)
    out = []
    for _, r in t[(t.kind.astype(str).str.lower() == "reservoir") & (t.ring_type == "lonlat")].iterrows():
        if any(s in r["name"] for s in SKIP_RESERVOIRS):
            continue
        pts = [tuple(float(v) for v in p.split()) for p in str(r.ring).split(";") if p.strip()]
        if len(pts) >= 4:
            g = gpd.GeoSeries([Polygon(pts)], crs=4326).to_crs(32618).buffer(0).iloc[0]
            out.append((r["name"], int(float(r.year_start)), str(r.source_url) if isinstance(r.source_url, str) else "", g))
    return out


def band(area, name, soilwin, rings, c0, c1, r0, r1, k0, k1, acc):
    """One window (rows r0:r1, columns c0:c1 of the grid); polygons are written for the core rows k0:k1 only."""
    h, w = r1 - r0, c1 - c0
    X0, Y1 = GRID["x0"] + c0 * PX, GRID["y1"] - r0 * PX
    tr = from_origin(X0, Y1, PX, PX)
    win = soilwin.cx[X0:X0 + w * PX, Y1 - h * PX:Y1]
    ras = lambda gs: features.rasterize(((g, 1) for g in gs), out_shape=(h, w), transform=tr, fill=0, dtype="uint8").astype(bool) if len(gs) else np.zeros((h, w), bool)
    sc = features.rasterize(((g, int(c)) for g, c in zip(win.geometry, win.code)), out_shape=(h, w), transform=tr, fill=0, dtype="uint8")
    city = ras(win[win.city].geometry)
    own = ras(win[win.AREASYMBOL == area].geometry)
    acc["cells_in_both_this_county_and_city_survey"] += int((own & city).sum())
    own &= ~city
    natural_up = (sc == UPLAND) & ~city          # the boroughs' polygons carry no class here
    cityp = gpd.read_file(f"{ROOT}/data/manual/natural/natural_1609.geojson", bbox=tuple(gpd.GeoSeries([Polygon([(X0, Y1), (X0 + w * PX, Y1), (X0 + w * PX, Y1 - h * PX), (X0, Y1 - h * PX)])], crs=32618).to_crs(4326).total_bounds)).to_crs(32618)
    if len(cityp):                                   # e.g. the New Jersey side of Ellis Island, already in the city file
        own &= ~features.rasterize(((g, 1) for g in cityp.geometry), out_shape=(h, w), transform=tr, fill=0, dtype="uint8", all_touched=True).astype(bool)
    own[:k0 - r0] = False
    own[k1 - r0:] = False
    del city, cityp, win
    us = np.full((h, w), 255, "uint8"); usid = np.zeros((h, w), "uint8")
    for k, sid in enumerate(SID, start=1):
        f = f"{D}/sheet_{sid}.tif"
        if not os.path.exists(f):
            continue
        with rasterio.open(f) as s:
            tmp = np.full((h, w), 255, "uint8")
            reproject(rasterio.band(s, 1), tmp, dst_transform=tr, dst_crs="EPSG:32618", resampling=Resampling.nearest, src_nodata=255, dst_nodata=255)
        p = (tmp != 255) & (us == 255)
        us[p] = tmp[p]; usid[p] = k
        del tmp, p
    with rasterio.open(f"{RAW}/dem30.tif") as s:
        dem = np.full((h, w), np.nan, "float32")
        reproject(rasterio.band(s, 1), dem, dst_transform=tr, dst_crs="EPSG:32618", resampling=Resampling.bilinear, src_nodata=np.nan, dst_nodata=np.nan)
    with rasterio.open(f"{D}/sea.tif") as s:
        sea = np.zeros((h, w), "uint8")
        reproject(rasterio.band(s, 1), sea, dst_transform=tr, dst_crs="EPSG:32618", resampling=Resampling.nearest)
    water_today = sc == WATER
    sea = sea.astype(bool) & water_today
    barrier = dilate(water_today & ~sea & (dem > 3.0), 10)
    low8 = ~(dem > 8.0)
    del dem
    u_water, u_marsh = us == 1, us == 2
    # does the sheet line its water?  share of today's near-shore tidal water that is wet on it
    shore = sea & dilate(natural_up, 20)          # tidal water within 120 m of natural upland soil: shores that have not moved
    del natural_up
    lined = np.zeros((h, w), bool)
    for k in np.unique(usid[usid > 0]):
        m = shore & (usid == k)
        share = float((u_water | u_marsh)[m].mean()) if m.sum() >= 2000 else 0.0
        acc["lining_share"].setdefault(SID[k - 1], []).append([int(m.sum()), round(share, 3)])
        if share >= 0.4:
            lined |= usid == k
    del shore
    # blank paper: land or open water?
    open_w = dilate(erode(sea, 10), 10) & sea
    blank = ~(u_water | u_marsh) & (sc != 0)
    pale_w, pale_m = blank_paper(blank, blank & np.isin(sc, (UPLAND, DUNES)), blank & open_w, u_marsh, u_water, water_today)
    pale_w &= lined; pale_m &= lined
    u_water |= pale_w; u_marsh |= pale_m
    del blank, pale_m, lined
    # tidal = connected to today's tidal water
    conn = (u_water | u_marsh | sea | (np.isin(sc, (WETSUB, MARSHSUB, TMARSH, TFLAT)) & low8)) & ~barrier
    del barrier, low8
    lab, n = ndimage.label(conn)
    tidal = np.zeros((h, w), bool)
    if n:
        tidal = (np.bincount(lab[sea & conn], minlength=n + 1) * PX * PX >= 1e4)[lab] & conn
    del lab, conn
    # the first water lines hug the shore and read as marsh: tidal marsh must be >= 120 m wide, else it is water
    narrow = u_marsh & ~(dilate(erode(u_marsh, 10), 14)) & tidal
    u_marsh2 = u_marsh & ~narrow
    u_water2 = u_water | narrow
    del narrow, u_marsh, u_water
    near_open = dilate(open_w, 25)
    del open_w, sea
    land = own & ~water_today
    out = np.zeros((h, w), "uint8"); kind = np.zeros((h, w), "uint8")

    def put(mask, cover, k):
        m = mask & land & (out == 0)
        out[m] = cover; kind[m] = k

    ws = sc == WETSUB
    put(ws & u_marsh2 & tidal, 2, 5)
    put(ws & u_marsh2 & ~tidal, 7, 6)
    put(ws & pale_w & tidal, 1, 23)
    put(ws & u_water2 & tidal, 1, 21)
    put(ws & u_water2 & ~tidal, 6, 4)
    put(ws & tidal & near_open, 1, 7)
    put(ws & tidal, 2, 8)
    put(ws, 7, 9)
    del ws, near_open
    put((sc == MARSHSUB) & tidal, 2, 10)
    put(sc == MARSHSUB, 7, 11)
    put(sc == TMARSH, 2, 12)
    put(sc == TFLAT, 3, 13)
    put(sc == FRESH, 7, 14)
    amb = np.isin(sc, (AMBIG, BEACH, DUNES))
    put(amb & pale_w & tidal, 1, 22)
    put(amb & u_water2 & tidal, 1, 1)
    put(amb & u_marsh2 & tidal, 2, 2)
    put(amb & u_marsh2 & ~tidal, 7, 3)
    put(amb & u_water2 & ~tidal, 6, 4)
    put(sc == BEACH, 4, 15)
    put(sc == DUNES, 5, 16)
    del amb
    # wet on the sheet well inside a unit the soil survey maps as upland
    u_wet = u_water2 | u_marsh2
    deep = big_parts(dilate(erode(u_wet & erode(sc == UPLAND, 6), 5), 5) & u_wet & (sc == UPLAND), int(2e4 / (PX * PX)))
    del u_wet
    put(deep & u_water2 & tidal, 1, 17)
    put(deep & u_marsh2 & tidal, 2, 18)
    put(deep & u_marsh2 & ~tidal, 7, 19)
    put(deep & u_water2 & ~tidal, 6, 20)
    del deep, tidal, u_water2, u_marsh2
    for c in COV:                                    # small specks
        m = out == c
        if m.any():
            small = m & ~big_parts(m, int((3000 if c == 6 else 1500) / (PX * PX)))
            out[small] = 0; kind[small] = 0
    rows = []
    # reservoirs: dry valleys under today's water
    for rname, year, url, geom in rings:
        if geom.bounds[2] < X0 or geom.bounds[0] > X0 + w * PX or geom.bounds[3] < Y1 - h * PX or geom.bounds[1] > Y1:
            continue
        m = features.rasterize([(geom.buffer(40), 1)], out_shape=(h, w), transform=tr, fill=0, dtype="uint8").astype(bool) & water_today & own
        if m.sum() * PX * PX < 5000:
            continue
        hs = us[m] != 255
        wet_share = round(float(np.isin(us[m], (1, 2)).sum() / max(1, hs.sum())), 3) if hs.any() else None
        acc["reservoirs"].append(dict(name=rname, county=name, year=year, ha=round(float(m.sum() * PX * PX / 1e4), 1), sheet_wet_share=wet_share,
                                      sheets=sorted(set(SID[k - 1] for k in np.unique(usid[m]) if k))))
        out[m] = 8
        note = f"{rname} (water from {year}): dry valley before the dam, under water today; outline: soil survey Water inside the fill-zone ring ({url})"
        for g in rt.polygons(m, tr, 1200.0, 5.0):
            rows.append(dict(cover="dry_valley", source="fill_zones_counties", confidence="medium", note=note, county=name, kind=99, geometry=g))
    for c, cover in COV.items():
        if c == 8:
            continue
        for k in np.unique(kind[out == c]):
            src, conf, note = KINDS[int(k)]
            m0 = (out == c) & (kind == k)
            parts = [(m0, "ssurgo")] if src == "ssurgo" else [(m0 & (usid == j), SID[j - 1]) for j in np.unique(usid[m0]) if j]
            for m, source in parts:
                for g in rt.polygons(m, tr, 1200.0, 5.0):
                    rows.append(dict(cover=cover, source=source, confidence=conf, note=note, county=name, kind=int(k), geometry=g))
    ha = lambda m: float(m.sum() * PX * PX / 1e4)
    acc["land_today_ha"] += ha(land); acc["water_today_ha"] += ha(own & water_today)
    acc["no_sheet_land_ha"] += ha(land & (us == 255)); acc["blank_paper_taken_as_water_ha"] += ha(pale_w & land)
    for c, cover in COV.items():
        acc["cover_ha"][cover] = acc["cover_ha"].get(cover, 0.0) + ha(out == c)
    for k in np.unique(kind[kind > 0]):
        key = f"{COV[int(out[kind == k][0])]} | {KINDS[int(k)][2][:70]}"
        acc["by_kind_ha"][key] = acc["by_kind_ha"].get(key, 0.0) + ha(kind == k)
    acc["made_land_ha"]["was_water"] += ha(out == 1)
    acc["made_land_ha"]["was_tidal_marsh"] += ha((out == 2) & (kind != 12))
    acc["made_land_ha"]["tidal_marsh_still_marsh"] += ha((out == 2) & (kind == 12))
    return rows


def county(area):
    name = AREAS[area]
    soil = gpd.read_parquet(f"{D}/ssurgo_counties.parquet", columns=["AREASYMBOL", "code", "city", "geometry"])
    b = soil[soil.AREASYMBOL == area].total_bounds
    c0 = max(0, int((b[0] - GRID["x0"]) // PX) - MARGIN); c1 = min(GRID["w"], int((b[2] - GRID["x0"]) // PX) + 1 + MARGIN)
    k0 = max(0, int((GRID["y1"] - b[3]) // PX)); k1 = min(GRID["h"], int((GRID["y1"] - b[1]) // PX) + 1)
    c1 -= (c1 - c0) % 4
    soilwin = soil.cx[GRID["x0"] + c0 * PX:GRID["x0"] + c1 * PX, GRID["y1"] - (k1 + MARGIN) * PX:GRID["y1"] - (k0 - MARGIN) * PX].copy()
    del soil
    rings = reservoir_rings()
    nb = max(1, int(np.ceil((k1 - k0 + 2 * MARGIN) * (c1 - c0) / MAXCELLS)))
    edges = [k0 + round(i * (k1 - k0) / nb) for i in range(nb + 1)]
    acc = dict(county=name, area=area, bands=nb, land_today_ha=0.0, water_today_ha=0.0, no_sheet_land_ha=0.0, blank_paper_taken_as_water_ha=0.0, cover_ha={}, by_kind_ha={},
               made_land_ha=dict(was_water=0.0, was_tidal_marsh=0.0, tidal_marsh_still_marsh=0.0), reservoirs=[], lining_share={}, cells_in_both_this_county_and_city_survey=0)
    rows = []
    for i in range(nb):
        r0 = max(0, edges[i] - MARGIN); r1 = min(GRID["h"], edges[i + 1] + MARGIN)
        r1 -= (r1 - r0) % 4
        rows += band(area, name, soilwin, rings, c0, c1, r0, r1, edges[i], min(edges[i + 1], r1), acc)
        print(name, "band", i + 1, "of", nb, "rows", r1 - r0, "cols", c1 - c0, "polygons so far", len(rows), flush=True)
    g = gpd.GeoDataFrame(rows, crs=32618) if rows else gpd.GeoDataFrame(dict(cover=[], source=[], confidence=[], note=[], county=[], kind=[]), geometry=[], crs=32618)
    g.to_parquet(f"{D}/polys_{area}.parquet")
    rnd = lambda d: {k: (round(v, 1) if isinstance(v, float) else v) for k, v in d.items()}
    for k in ("cover_ha", "by_kind_ha", "made_land_ha"):
        acc[k] = rnd(acc[k])
    acc = rnd(acc); acc["polygons"] = len(g)
    json.dump(acc, open(f"{D}/stats_{area}.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in acc.items() if k != "by_kind_ha"}), flush=True)


def merge():
    fr = [gpd.read_parquet(f) for f in sorted(glob.glob(f"{D}/polys_*.parquet")) if "NY059" not in f]
    g = pd.concat([f for f in fr if len(f)], ignore_index=True)
    g["geometry"] = g.geometry.buffer(0)
    g = g[~g.geometry.is_empty]
    g4 = g.drop(columns=["kind"]).to_crs(4326)
    g4["geometry"] = g4.geometry.set_precision(1e-6)
    g4 = g4[~g4.geometry.is_empty]
    g4[["cover", "source", "confidence", "note", "county", "geometry"]].to_file(f"{OUT}/natural_1609_counties.geojson", driver="GeoJSON", COORDINATE_PRECISION=6)
    stats = {json.load(open(f))["county"]: json.load(open(f)) for f in sorted(glob.glob(f"{D}/stats_*.json")) if "NY059" not in f}
    json.dump(stats, open(f"{OUT}/natural_stats_counties.json", "w"), indent=1)
    sheets = {os.path.basename(f)[6:-5]: json.load(open(f)) for f in sorted(glob.glob(f"{D}/sheet_usgs_*.json"))}
    json.dump(sheets, open(f"{OUT}/usgs_sheets_counties.json", "w"), indent=1)
    print("polygons", len(g4), "MB", round(os.path.getsize(f"{OUT}/natural_1609_counties.geojson") / 1e6, 1))
    print(g4.groupby(["county", "cover"]).size().unstack(fill_value=0).to_string())
    print(g4.source.value_counts().to_string())


if __name__ == "__main__":
    merge() if sys.argv[1] == "merge" else county(sys.argv[1])
