"""Assemble the c.1609 natural landscape of the five boroughs.

Sources, in the order they decide a 6 m cell of today's land:
  Manhattan island inside the Viele 1865 map  -> manhattan.py (water = made land, marsh, ponds, streams)
  elsewhere, by the NRCS soil survey (SSURGO) map unit:
     Urban land, reclaimed substratum (UrA)            -> water
     Urban land, tidal marsh substratum (UmA, UmB)     -> tidal_marsh
     tidal-marsh soils that are still marsh            -> tidal_marsh
     tidal flat / intertidal                           -> tidal_flat
     organic and ponded freshwater soils               -> freshwater_wetland
     beaches / dunes                                   -> beach / dunes unless the 1890s sheet shows water or marsh
     fill soils that do not say what is underneath     -> what the 1888-1898 USGS sheet shows there (water / marsh / dry)
     natural upland soils, urban land over till/outwash-> dry (nothing written), except blocks >= 2 ha that the
                                                          sheet shows wet >= 36 m inside the unit (confidence low)
outputs: data/manual/natural/natural_1609.geojson, streams_1609.geojson, data/interim/natural/natural_stats.json
"""
import json
import re

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio import features
from rasterio.transform import from_origin
from scipy import ndimage
from shapely.geometry import Point, box

import rastools as rt
from usgs_sheets import GRID, SHEETS

ROOT = "/home/user/nyc"
D = f"{ROOT}/data/interim/natural"
OUT = f"{ROOT}/data/manual/natural"
BORO = {"NY005": "Bronx", "NY047": "Brooklyn", "NY061": "Manhattan", "NY081": "Queens", "NY085": "Staten Island"}

WATER_TODAY = r"^(W|Ang1|Mak2|Nag[235]|Nagd5|Psa[25]|Rho[235]|Weq1)$"
RECLAIMED = r"^UrA$"
MARSH_SUB = r"^Um[AB]$"
TIDAL_MARSH = r"^(IwA|IPA|IPMA|PaA|MaA|WbA|ApA|SaA)$"
TIDAL_FLAT = r"^(WaA|Nag0)$"
FRESH = r"^(CaA|NaA|TkA|WkA|PkA|PvA|HaA|LiA|WHA|FFA|LFA)$"
BEACH = r"^(Bs|Bc)$"
DUNES = r"^(HD[ABC]|Hk[AB]|Bl|BBA)$"
AMBIG = r"^(La|LU|LE|LG|EL|UL|Bi[A-E]$|BgA|BV|BaA|Bz|Bk|Fo|Fr|Ja|MV|Vz|UV|UH|HV|Fk|Fl|Gr[AB]$|GO|Kk|Oi|Se|Ll|Ri|Us|Ua|ANS)"
CODES = [(1, WATER_TODAY), (3, RECLAIMED), (4, MARSH_SUB), (5, TIDAL_MARSH), (6, TIDAL_FLAT), (9, FRESH), (7, BEACH), (8, DUNES), (10, AMBIG)]
# reservoirs on the sheets that are not natural ponds (lon, lat, radius m)
NOT_PONDS = [(-73.8790, 40.8770, 300), (-73.9655, 40.6725, 250), (-73.9330, 40.8425, 250), (-73.8890, 40.6880, 500), (-73.8950, 40.8790, 700)]
# names for stream pieces: (name, lon, lat, radius m, reference)
NAMES = [
    ("Minetta Brook", -73.9990, 40.7325, 700, "https://en.wikipedia.org/wiki/Minetta_Creek"),
    ("Collect Pond outlet (Lispenard Meadows drain, later the Canal Street canal)", -74.0040, 40.7200, 350, "https://en.wikipedia.org/wiki/Collect_Pond"),
    ("Collect Pond outlet to the East River (Old Wreck Brook)", -73.9990, 40.7125, 300, "https://en.wikipedia.org/wiki/Collect_Pond"),
    ("Saw Kill", -73.9560, 40.7720, 900, ""),
    ("Harlem Creek", -73.9440, 40.7930, 700, ""),
    ("Montayne's Rivulet", -73.9570, 40.7960, 450, ""),
    ("Sherman Creek", -73.9230, 40.8600, 500, "https://en.wikipedia.org/wiki/Harlem_River#Sherman_Creek"),
    ("Tibbetts Brook", -73.8960, 40.8850, 1300, "https://en.wikipedia.org/wiki/Tibbetts_Brook"),
    ("Mill Brook (Bronx)", -73.9180, 40.8160, 1200, ""),
    ("Sunswick Creek", -73.9370, 40.7630, 700, "https://en.wikipedia.org/wiki/Sunswick_Creek"),
    ("Wallabout Creek", -73.9650, 40.6990, 700, "https://en.wikipedia.org/wiki/Wallabout_Bay"),
    ("Gowanus Creek", -73.9880, 40.6770, 900, "https://en.wikipedia.org/wiki/Gowanus_Canal"),
    ("Newtown Creek (head, English Kills / Maspeth Creek)", -73.9240, 40.7180, 1300, "https://en.wikipedia.org/wiki/Newtown_Creek"),
    ("Flushing Creek", -73.8400, 40.7500, 1500, "https://en.wikipedia.org/wiki/Flushing_River"),
    ("Coney Island Creek", -73.9800, 40.5800, 1500, "https://en.wikipedia.org/wiki/Coney_Island_Creek"),
    ("Spring Creek", -73.8600, 40.6570, 900, "https://en.wikipedia.org/wiki/Spring_Creek_Park"),
    ("Fresh Creek", -73.8830, 40.6450, 700, ""),
    ("Paerdegat Creek (Bedford Creek)", -73.9120, 40.6300, 900, "https://en.wikipedia.org/wiki/Paerdegat_Basin"),
    ("Hawtree Creek", -73.8320, 40.6560, 700, "https://en.wikipedia.org/wiki/Hawtree_Creek"),
    ("Westchester Creek", -73.8400, 40.8330, 1300, "https://en.wikipedia.org/wiki/Westchester_Creek"),
    ("Fresh Kills", -74.1900, 40.5750, 1500, "https://en.wikipedia.org/wiki/Fresh_Kills"),
]


def main():
    h, w, px = GRID["h"], GRID["w"], GRID["px"]
    tr = from_origin(GRID["x0"], GRID["y1"], px, px)
    soil = gpd.read_parquet(f"{D}/ssurgo_all.parquet")
    code = np.full(len(soil), 2, "uint8")
    for c, rx in CODES:
        code[soil.MUSYM.str.match(rx).values & (code == 2)] = c
    soil["code"] = code
    soil["boro"] = soil.AREASYMBOL.map({k: i + 1 for i, k in enumerate(BORO)})
    sc = features.rasterize(((g, int(c)) for g, c in zip(soil.geometry, soil.code)), out_shape=(h, w), transform=tr, fill=0, dtype="uint8")
    boro = features.rasterize(((g, int(c)) for g, c in zip(soil.geometry, soil.boro)), out_shape=(h, w), transform=tr, fill=0, dtype="uint8")
    with rasterio.open(f"{D}/usgs_1890s.tif") as s:
        us = s.read(1); usid = s.read(2)
    cov = gpd.read_parquet(f"{D}/manhattan_coverage.parquet")
    viele = features.rasterize(((g, 1) for g in cov.geometry), out_shape=(h, w), transform=tr, fill=0, dtype="uint8").astype(bool)

    land_today = (sc != 0) & (sc != 1)
    u_water, u_marsh = us == 1, us == 2
    # the first water lines hug the shore and read as marsh: marsh must be >= 60 m wide, else it is water
    core = ndimage.binary_opening(u_marsh, structure=rt.disk(10))
    u_marsh2 = ndimage.binary_dilation(core, structure=rt.disk(4)) & u_marsh
    u_water2 = u_water | (u_marsh & ~u_marsh2)
    u_wet = u_water2 | u_marsh2
    # paper-white patches inside the water lining that today's fill covers: dry patches under 3 ha on fill soils
    # that touch no upland soil are water (a bare islet that small is lost with them)
    amb0 = np.isin(sc, (10, 7, 8))
    dryfill = amb0 & ~u_wet & (us != 255)
    lab, n = ndimage.label(dryfill)
    if n:
        idx = np.arange(1, n + 1)
        small = ndimage.sum(dryfill, lab, index=idx) * px * px < 3e4
        touch = ndimage.maximum(ndimage.binary_dilation(sc == 2, iterations=2), lab, index=idx) > 0
        holes = np.isin(lab, 1 + np.nonzero(small & ~touch)[0])
        u_water2 |= holes
        u_wet |= holes
    del lab
    # tidal = connected to the sea through water / marsh
    conn = u_wet | (sc == 1) | np.isin(sc, (3, 4, 5, 6))
    lab, n = ndimage.label(conn)
    sea_px = ndimage.sum(sc == 1, lab, index=np.arange(1, n + 1))
    tidal = np.isin(lab, 1 + np.nonzero(sea_px * px * px >= 100e4)[0])
    del lab

    out = np.zeros((h, w), "uint8")       # cover code
    src = np.zeros((h, w), "uint8")       # 1 ssurgo, 2 usgs sheet (usid tells which), 3 usgs low-confidence inside upland unit
    COV = {1: "water", 2: "tidal_marsh", 3: "tidal_flat", 4: "beach", 5: "dunes", 6: "pond", 7: "freshwater_wetland"}

    def put(mask, cover, s):
        m = mask & (out == 0)
        out[m] = cover; src[m] = s

    # reclaimed substratum: the soil survey does not say whether the fill went into open water or onto marsh.
    # Where the 1890s sheet still shows it wet, the sheet decides; where it was already filled, cells more than
    # 150 m from open tidewater (water at least 120 m wide today) are taken as salt marsh along a creek (estimated).
    ur = sc == 3
    open_w = ndimage.binary_opening(sc == 1, structure=rt.disk(10))
    far = ndimage.distance_transform_edt(~open_w) * px > 150.0
    put(ur & u_marsh2, 2, 2)
    put(ur & ~u_wet & (us != 255) & far, 2, 5)
    put(ur, 1, 1)
    put(sc == 4, 2, 1)
    put(sc == 5, 2, 4)                    # still marsh today
    put(sc == 6, 3, 1)
    put(sc == 9, 7, 1)
    amb = np.isin(sc, (10, 7, 8))
    put(amb & u_water2 & tidal, 1, 2)
    put(amb & u_marsh2 & tidal, 2, 2)
    put(amb & u_marsh2 & ~tidal, 7, 2)
    inland_w = amb & u_water2 & ~tidal
    put(inland_w, 6, 2)
    put((sc == 7) & (out == 0), 4, 1)
    put((sc == 8) & (out == 0), 5, 1)
    # wet on the sheet well inside a unit the soil survey maps as upland
    upl = sc == 2
    deep = ndimage.binary_opening(u_wet & ndimage.binary_erosion(upl, structure=rt.disk(6)), structure=rt.disk(5))
    lab, n = ndimage.label(deep)
    big = np.isin(lab, 1 + np.nonzero(ndimage.sum(deep, lab, index=np.arange(1, n + 1)) * px * px >= 2e4)[0])
    del lab
    put(big & u_water2 & tidal, 1, 3)
    put(big & u_marsh2 & tidal, 2, 3)
    put(big & u_marsh2 & ~tidal, 7, 3)
    put(big & u_water2 & ~tidal, 6, 3)
    # reservoirs are not ponds
    from pyproj import Transformer
    tf = Transformer.from_crs(4326, 32618, always_xy=True)
    for lon, lat, r in NOT_PONDS:
        x, y = tf.transform(lon, lat)
        m = features.rasterize([(Point(x, y).buffer(r), 1)], out_shape=(h, w), transform=tr, fill=0, dtype="uint8").astype(bool)
        out[m & (out == 6)] = 0
    out[viele] = 0
    out[~land_today] = 0
    # small specks
    for c in COV:
        m = out == c
        lab, n = ndimage.label(m)
        if n:
            small = np.isin(lab, 1 + np.nonzero(ndimage.sum(m, lab, index=np.arange(1, n + 1)) * px * px < (1500 if c != 6 else 3000))[0])
            out[small] = 0

    sid = {i + 1: v[4] for i, v in enumerate(SHEETS.values())}
    rows = []
    for c, cover in COV.items():
        for s in (1, 2, 3, 4, 5):
            m0 = (out == c) & (src == s)
            if not m0.any():
                continue
            parts = [(m0, None)] if s in (1, 4, 5) else [(m0 & (usid == k), sid[k]) for k in sid]
            for m, sheet in parts:
                if not m.any():
                    continue
                if s == 1:
                    source, conf = "ssurgo", "medium"
                    note = {1: "soil survey: Urban land, reclaimed substratum (fill placed in water; may include creek-side marsh)",
                            2: "soil survey: Urban land, tidal marsh substratum (fill over tidal marsh)",
                            3: "soil survey: tidal flat / intertidal soil", 7: "soil survey: organic or ponded freshwater soil",
                            4: "soil survey: beach today; barrier beaches have moved since 1609 (not reconstructed)",
                            5: "soil survey: dune sand today; barrier beaches have moved since 1609 (not reconstructed)"}[c]
                    if c in (4, 5):
                        conf = "low"
                elif s == 4:
                    source, conf, note = "ssurgo", "high", "soil survey: tidal-marsh soil, still marsh today"
                elif s == 5:
                    source, conf = "ssurgo", "low"
                    note = "soil survey: Urban land, reclaimed substratum, already filled on the 1890s sheet; over 150 m from open tidewater, so taken as salt marsh along a creek (estimated)"
                else:
                    source = sheet
                    conf = "medium" if (s == 2 and c == 1) else "low"
                    note = {1: "water on the USGS sheet, land today", 2: "marsh on the USGS sheet (marsh / water split by print texture), land today",
                            7: "marsh on the USGS sheet not connected to tidal water", 6: "inland water on the USGS sheet, land today"}[c]
                    if s == 3:
                        note += "; soil survey maps upland substratum here"
                for g in rt.polygons(m, tr, 1200.0, 5.0):
                    rows.append(dict(cover=cover, source=source, confidence=conf, note=note, geometry=g))
    gen = gpd.GeoDataFrame(rows, crs=32618)
    man = gpd.read_parquet(f"{D}/manhattan_polys.parquet")
    # Ellis Island lies outside the New York soil survey: today's island (Overture) minus the New York enclave of the
    # TIGER county line, which is the island as it stood in 1834 (New Jersey v. New York, 1998; 4.68 acres)
    import duckdb
    from shapely import wkb
    con = duckdb.connect(); con.execute("INSTALL spatial; LOAD spatial;")
    r = con.execute(f"SELECT ST_AsWKB(geometry) FROM '{ROOT}/data/raw/overture/2026-10-21.0/base_land.parquet' WHERE name='Ellis Island' AND class='islet'").fetchall()
    ellis = gpd.GeoSeries([wkb.loads(bytes(r[0][0]))], crs=4326).to_crs(32618).iloc[0]
    cty = gpd.read_file(f"zip://{ROOT}/data/raw/tiger/tl_2024_us_county.zip", bbox=(-74.045, 40.697, -74.036, 40.702))
    nyc_part = cty[cty.GEOID == "36061"].to_crs(32618).geometry.union_all()
    filled = ellis.difference(nyc_part.buffer(0))
    print("Ellis Island: today", round(ellis.area / 4046.86, 1), "acres; original (NY enclave)", round(ellis.intersection(nyc_part).area / 4046.86, 2), "acres")
    ell = gpd.GeoDataFrame([dict(cover="water", source="tiger_ny_enclave", confidence="medium",
                                 note="Ellis Island outside the 1834 island (New York enclave of the state line, New Jersey v. New York 1998); land today", geometry=filled)], crs=32618)
    allp = pd.concat([gen, man, ell], ignore_index=True)
    allp["geometry"] = allp.geometry.buffer(0)
    allp = allp[~allp.geometry.is_empty]
    # stats by borough (centroid in which soil survey area)
    bx = ((allp.geometry.representative_point().x - GRID["x0"]) / px).astype(int).clip(0, w - 1)
    by = ((GRID["y1"] - allp.geometry.representative_point().y) / px).astype(int).clip(0, h - 1)
    names = [""] + list(BORO.values())
    allp["borough"] = [names[b] for b in boro[by.values, bx.values]]
    allp.loc[allp.source == "tiger_ny_enclave", "borough"] = "Ellis Island (New Jersey side)"
    allp["ha"] = allp.area / 1e4
    stats = allp.groupby(["borough", "cover"]).ha.agg(["count", "sum"]).round(1)
    print(stats.to_string())
    made = allp[(allp.cover.isin(["water", "tidal_marsh"])) & ~((allp.confidence == "high") & (allp.source == "ssurgo"))]
    mt = made.groupby(["borough", "cover"]).ha.sum().unstack(fill_value=0)
    mt["total_ha"] = mt.sum(axis=1); mt["total_acres"] = (mt.total_ha * 2.47105).round(0)
    print("\\nwater / tidal marsh c.1609 that is developed land today:\\n", mt.round(0).to_string())
    json.dump({"by_borough_cover": {f"{k[0]}|{k[1]}": {"n": int(v["count"]), "ha": float(v["sum"])} for k, v in stats.iterrows()},
               "made_land_ha": {k: {c: float(x) for c, x in v.items()} for k, v in mt.round(1).iterrows()}}, open(f"{D}/natural_stats.json", "w"), indent=1)
    g4 = allp.drop(columns=["ha"]).to_crs(4326)
    g4["geometry"] = g4.geometry.set_precision(1e-6)
    g4 = g4[~g4.geometry.is_empty]
    g4.to_file(f"{OUT}/natural_1609.geojson", driver="GeoJSON", COORDINATE_PRECISION=6)
    print("polygons", len(g4))

    # ---- streams
    st = gpd.read_parquet(f"{D}/manhattan_streams.parquet")
    st["confidence"] = "medium"
    creek = u_water2 & ~ndimage.binary_opening(u_water2, structure=rt.disk(6)) & land_today & ~viele      # tidal creeks under 70 m wide
    thin_ = (us == 3) & land_today & ~viele
    lines = rt.trace(rt.thin(ndimage.binary_closing(creek | thin_, structure=np.ones((3, 3), bool))), tr, 300.0, spur_px=8)
    ug = gpd.GeoDataFrame(dict(geometry=[l.simplify(5.0) for l in lines]), crs=32618)
    cx = ((ug.geometry.interpolate(0.5, normalized=True).x - GRID["x0"]) / px).astype(int).clip(0, w - 1)
    cy = ((GRID["y1"] - ug.geometry.interpolate(0.5, normalized=True).y) / px).astype(int).clip(0, h - 1)
    ug["source"] = [sid.get(int(k), "usgs") for k in usid[cy.values, cx.values]]
    ug["confidence"] = "low"
    sall = pd.concat([st, ug], ignore_index=True)
    sall["name"] = ""
    sall["ref"] = ""
    for name, lon, lat, r, ref in NAMES:
        x, y = tf.transform(lon, lat)
        hit = sall.geometry.intersects(Point(x, y).buffer(r)) & (sall.name == "")
        sall.loc[hit, "name"] = name
        sall.loc[hit, "ref"] = ref
    sall["name_basis"] = np.where(sall.name == "", "", np.where(sall.ref == "", "proximity to the place; name from general knowledge, no reference verified",
                                                              "proximity to the place named in ref"))
    sall.loc[sall.name == "", "name"] = "unnamed watercourse"
    print(sall.groupby("name").geometry.apply(lambda s: round(s.length.sum())).sort_values(ascending=False).head(30).to_string())
    s4 = sall.to_crs(4326)
    s4["geometry"] = s4.geometry.set_precision(1e-6)
    s4[["name", "source", "confidence", "ref", "name_basis", "geometry"]].to_file(f"{OUT}/streams_1609.geojson", driver="GeoJSON", COORDINATE_PRECISION=6)
    print("streams", len(s4), "km", round(sall.length.sum() / 1000, 1))


if __name__ == "__main__":
    main()
