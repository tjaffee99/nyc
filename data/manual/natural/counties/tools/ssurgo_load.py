"""SSURGO soil map unit polygons of the eight counties (+ the five boroughs, for the join and for training the
sheet classifier) -> data/interim/natural_counties/ssurgo_counties.parquet (UTM 18N) with a class per map unit.

The class comes from the map unit NAME (the symbols differ between survey areas) and, for natural wet soils, from
the unit's hydric rating in Soil Data Access (muaggatt.hydclprs = per cent of the unit that is hydric soil):

  WATER     Water; Anguilla / Nagunt subaqueous soils
  TFLAT     Nagunt sand, intertidal
  TMARSH    Westbrook, Ipswich, Matunuck, Pawcatuck, Sandyhook: tidal marsh that still exists
  MARSHSUB  Udorthents, organic substratum (fill over marsh peat)
  WETSUB    "... wet substratum": Urban land, wet substratum (Hudson); Udorthents, wet substratum (Bergen, Passaic,
            Rockland, Westchester); Udipsamments, wet substratum and its Urban land complex (Nassau: dredged sand
            over tidal marsh).  Fill over wet ground; the unit does not say whether marsh, swamp or water
  BEACH / DUNES   Beaches; Dune land, Hooksan
  FRESH     natural (not fill, not tidal) units that are >= 85 % hydric: Catden, Timakwa, Natchaug, Freetown,
            Swansea mucks, Preakness, Parsippany, Great Piece, Hasbrouck, Alden, Sun, Sloan, Wallkill, Norwich,
            Passaic, Berryland, Atsion, Walpole, Raynham, Rippowam, Ridgebury (NJ Highlands), Fluvaquents ponded
  AMBIG     fill and urban units that do not say what they cover: Urban land (undifferentiated), Udorthents
            refuse / loamy / loamy fill / smoothed, Bigapple, Laguardia, Ladyliberty, Secaucus, Greenbelt,
            Centralpark, Rikers, Udipsamments, Barren, Fortress and their Urban land complexes
  UPLAND    everything else (natural upland soils; urban land and Udorthents over a named natural soil, till,
            bedrock, outwash or eolian substratum; pits, quarries, dams)
"""
import glob
import json
import os
import re

import geopandas as gpd
import pandas as pd

import sda
from common import AMBIG, AREAS, BEACH, CITY_AREAS, D, DUNES, FRESH, MARSHSUB, RAW, ROOT, TFLAT, TMARSH, UPLAND, WATER, WETSUB

CITY_WATER = r"^(W|Ang1|Mak2|Nag[235]|Nagd5|Psa[25]|Rho[235]|Weq1)$"          # as the city layer's assemble.py
CITY_MARSH = ["IwA", "IPA", "IPMA", "PaA", "MaA", "WbA", "ApA", "UmA", "UmB"]
AMBIG_RX = (r"^(Urban land$|Udorthents, (refuse|loamy|loamy fill|smoothed|Rikers)|Udorthents, loamy, |Urban land, (loamy fill|[Bb]igapple) substratum|"
            r"Bigapple|Laguardia|Ladyliberty|Secaucus|Greenbelt|Centralpark|Rikers|Udipsamments, (nearly level|steep)|"
            r"Urban land-Udipsamments complex|Barren|Fortress|Urban land-Greenbelt|Hooksan-Verrazano)")


def classify(name, hyd):
    n = name or ""
    if n == "Water" or re.match(r"^(Anguilla|Nagunt sand, 0 to)", n):
        return WATER
    if n.startswith("Nagunt sand, intertidal"):
        return TFLAT
    if re.match(r"^(Westbrook|Ipswich|Matunuck|Pawcatuck|Sandyhook)", n):
        return TMARSH
    if "organic substratum" in n:
        return MARSHSUB
    if "wet substratum" in n:
        return WETSUB
    if re.match(AMBIG_RX, n):
        return AMBIG
    if n.startswith("Beaches"):
        return BEACH
    if re.match(r"^(Dune land|Hooksan)", n):
        return DUNES
    if hyd >= 85 and not re.match(r"^(Urban|Udorthents|Udipsamments|Pits|Dam)", n):
        return FRESH
    return UPLAND


def main():
    os.makedirs(D, exist_ok=True)
    mu_json = f"{D}/mapunits.json"
    if not os.path.exists(mu_json):
        syms = ",".join(f"'{a}'" for a in AREAS)
        cols, rows = sda.query(f"""SELECT l.areasymbol, m.musym, m.muname, m.muacres, a.hydclprs, a.drclassdcd, a.flodfreqdcd, a.pondfreqprs, m.mukey
            FROM legend l JOIN mapunit m ON m.lkey=l.lkey JOIN muaggatt a ON a.mukey=m.mukey WHERE l.areasymbol IN ({syms}) ORDER BY 1,2""")
        json.dump(dict(cols=cols, rows=rows), open(mu_json, "w"))
    mu = pd.DataFrame(json.load(open(mu_json))["rows"], columns=json.load(open(mu_json))["cols"])
    mu["hyd"] = pd.to_numeric(mu.hydclprs, errors="coerce").fillna(0)
    mu["code"] = [classify(n, h) for n, h in zip(mu.muname, mu.hyd)]
    mu["mukey"] = mu.mukey.astype(str)
    fr = []
    for f in sorted(glob.glob(f"{RAW}/ssurgo/*/*/spatial/soilmu_a_*.shp")):
        g = gpd.read_file(f).to_crs(32618)
        g["MUKEY"] = g.MUKEY.astype(str)
        g = g.merge(mu[["mukey", "muname", "code", "hyd"]], left_on="MUKEY", right_on="mukey", how="left")
        assert g.code.notna().all(), f
        g["city"] = False
        fr.append(g[["AREASYMBOL", "MUSYM", "MUKEY", "muname", "code", "hyd", "city", "geometry"]])
    for f in sorted(glob.glob(f"{ROOT}/data/raw/natural/ssurgo/*/*/spatial/soilmu_a_*.shp")):   # the city's five areas
        g = gpd.read_file(f).to_crs(32618)
        g["MUKEY"] = g.MUKEY.astype(str)
        g["muname"] = ""
        g["hyd"] = 0.0
        g["code"] = UPLAND
        g.loc[g.MUSYM.str.match(CITY_WATER), "code"] = WATER
        g.loc[g.MUSYM.isin(CITY_MARSH), "code"] = TMARSH
        g["city"] = True
        fr.append(g[["AREASYMBOL", "MUSYM", "MUKEY", "muname", "code", "hyd", "city", "geometry"]])
    g = pd.concat(fr, ignore_index=True)
    g["code"] = g.code.astype("uint8")
    g["geometry"] = g.geometry.buffer(0)
    g["ha"] = g.area / 1e4
    g.to_parquet(f"{D}/ssurgo_counties.parquet")
    names = {1: "water", 2: "upland", 3: "wetsub", 4: "marshsub", 5: "tmarsh", 6: "tflat", 7: "beach", 8: "dunes", 9: "fresh", 10: "ambig"}
    t = g[~g.city].groupby(["AREASYMBOL", "code"]).ha.sum().unstack(fill_value=0).round(0).astype(int).rename(columns=names)
    print(t.to_string())
    print("bounds", [round(v) for v in g[~g.city].total_bounds], "city areas", sorted(g[g.city].AREASYMBOL.unique()))
    u = mu[mu.code.isin([3, 4, 9, 10])].sort_values(["code", "areasymbol"])
    json.dump({names[c]: sorted(set(f"{a} {s} {n}" for a, s, n in zip(x.areasymbol, x.musym, x.muname))) for c, x in u.groupby("code")},
              open(f"{D}/unit_classes.json", "w"), indent=1)


if __name__ == "__main__":
    main()
