"""Floyd Bennett Field: airfield outline + dated runway zones -> data/manual/airports.

Inputs
  * OpenStreetMap (ODbL), API extract of 2026-11-10 saved as data/raw/airports/osm/fbf.osm:
      https://api.openstreetmap.org/api/0.6/map?bbox=-73.912,40.576,-73.868,40.607
    the centre lines of the abandoned runways (`abandoned:aeroway=runway`, `abandoned:ref`
    15/33, 12/30, 06/24, 01/19) and the old runway 6-24 (taxiway 'Aviation Road', way 1102727234).
  * Overture 2026-10-21.0 base_land_use (OSM relation 9460480, leisure=park 'Floyd Bennett Field').

Outputs (committed)
  * extra_outlines.geojson   the airfield outline (name, class) for airports.py / the terrain
  * pavement_zones.geojson   one zone per runway: its centre line buffered by 50 m
  * pavement_dates.csv       rows that clip Overture's one big pavement polygon (apron
                             03717e73..., all the historic concrete) by those zones

Run from the repository root:  .venv/bin/python data/manual/airports/tools/fbf.py
"""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer
from shapely.geometry import LineString

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "pipeline"))
OUT = ROOT / "data" / "manual" / "airports"
UTM = "EPSG:32618"
WIKI = "https://en.wikipedia.org/wiki/Floyd_Bennett_Field"
OSM = "https://www.openstreetmap.org/relation/9463532"

# zone id: (year, confidence, OSM ways, evidence) — earlier zones first: a crossing belongs to the older runway
ZONES = {
    "fbf_rwy_15_33": (1931, "documented", "ref:15/33", "Runway 15-33, one of the 'two perpendicular concrete runways in a T shape' "
                      "(3,110 ft) of the airport opened 23 May 1931; lengthened to 3,500 ft in 1936 and 5,000 ft in 1942 — "
                      "the lengthenings are NOT separated (which end grew is not documented in the sources read): whole strip from 1931, estimated for the added ends"),
    "fbf_rwy_old_6_24": (1931, "documented", "way:1102727234", "Old runway 6-24 (4,000 ft), perpendicular to the hangar row, 1931; a taxiway "
                         "after the new 6-24 of 1942 (OSM: abandoned taxiway 'Aviation Road')"),
    "fbf_rwy_1_19": (1938, "documented", "ref:01/19", "Runway 1-19, one of 'the two runways constructed in 1937-1938' (WPA; 3,500 x 150 ft); "
                     "5,000 x 300 ft in 1942, 7,000 ft about 1952 — lengthenings not separated: whole strip from 1938, estimated for the added ends"),
    "fbf_rwy_12_30": (1938, "documented", "ref:12/30", "Runway 12-30, one of 'the two runways constructed in 1937-1938' (WPA; 3,200 x 150 ft); "
                      "5,000 ft in 1942, 5,500 ft about 1952 — lengthenings not separated: whole strip from 1938, estimated for the added ends"),
    "fbf_rwy_new_6_24": (1942, "documented", "ref:06/24", "'A new Runway 6-24 was constructed in 1942' on the north side of the field by the Navy "
                         "(5,000 x 300 ft; 6,000 ft about 1952 — lengthening not separated)"),
}


def main():
    T = Transformer.from_crs(4326, UTM, always_xy=True)
    root = ET.parse(ROOT / "data" / "raw" / "airports" / "osm" / "fbf.osm").getroot()
    nodes = {n.get("id"): (float(n.get("lon")), float(n.get("lat"))) for n in root.iter("node")}
    ways = {}
    for w in root.iter("way"):
        tags = {t.get("k"): t.get("v") for t in w.iter("tag")}
        if "abandoned:aeroway" not in tags:
            continue
        xy = np.array([nodes[x.get("ref")] for x in w.iter("nd") if x.get("ref") in nodes])
        ways[w.get("id")] = (tags, LineString(np.column_stack(T.transform(xy[:, 0], xy[:, 1]))))
    # the Aviation Road piece of 15/33 that carries no ref (way 1136371604) lies on the same axis
    zones, used = [], set()
    for zid, (year, conf, sel, ev) in ZONES.items():
        if sel.startswith("ref:"):
            ids = [k for k, (t, _) in ways.items() if t.get("abandoned:ref") == sel[4:]]
            if sel == "ref:15/33":
                ids.append("1136371604")
        else:
            ids = [sel[4:]]
        used |= set(ids)
        geom = shapely.union_all([ways[i][1].buffer(50, cap_style="flat") for i in ids])
        zones.append({"zone": zid, "kind": "zone", "start_year": year, "end_year": 9999, "confidence": conf,
                      "osm_ways": ",".join(sorted(ids)), "source_url": WIKI, "note": ev, "geometry": geom})
        print(zid, year, len(ids), "ways", f"{geom.area / 1e4:.1f} ha")
    z = gpd.GeoDataFrame(zones, geometry="geometry", crs=UTM).to_crs(4326)
    z.geometry = shapely.set_precision(z.geometry.values, 1e-7)
    z.to_file(OUT / "pavement_zones.geojson", driver="GeoJSON")

    # Overture's pavement polygon of the field (OSM relation 9463532: 'historic aprons ... also
    # historic runways and taxiways that have now been repurposed')
    d = pd.read_parquet(ROOT / "data" / "raw" / "overture" / "2026-10-21.0" / "region_airports.parquet")
    g = gpd.GeoDataFrame(d, geometry=gpd.GeoSeries.from_wkb(d.geometry), crs=4326)
    big = g[(g["class"] == "apron") & g.intersects(shapely.box(-73.905, 40.58, -73.875, 40.605))].to_crs(UTM)
    big = big[big.area > 5e5]
    assert len(big) == 1, len(big)
    oid = big.id.iloc[0]
    c = big.geometry.iloc[0].representative_point()
    lon, lat = Transformer.from_crs(UTM, 4326, always_xy=True).transform(c.x, c.y)
    rows = []
    for q in zones:
        a = big.geometry.iloc[0].intersection(q["geometry"]).area
        rows.append({"airport": "FBF", "feature_class": "apron", "overture_id": oid, "runway": q["zone"].replace("fbf_rwy_", "").replace("_", "-"),
                     "name": "", "lon": round(lon, 6), "lat": round(lat, 6), "part": "zone_clip", "clip_zone": q["zone"], "from_end": "",
                     "d0_m": "", "d1_m": "", "part_lon0": "", "part_lat0": "", "part_lon1": "", "part_lat1": "",
                     "start_year": q["start_year"], "end_year": 9999, "confidence": q["confidence"], "source_url": WIKI,
                     "evidence": f"[{q['zone']}] {q['note']} ({a / 1e4:.1f} ha of the mapped pavement)"})
    # keep the rows of other airports (JFK) that are maintained by hand in the same file
    p = OUT / "pavement_dates.csv"
    old = pd.read_csv(p, dtype=str).fillna("") if p.exists() else pd.DataFrame()
    if len(old):
        old = old[old.airport != "FBF"]
    pd.concat([old, pd.DataFrame(rows).astype(str)], ignore_index=True).to_csv(p, index=False)

    # airfield outline: the NPS park outline of the field
    lu = pd.read_parquet(ROOT / "data" / "raw" / "overture" / "2026-10-21.0" / "base_land_use.parquet")
    lu = lu[(lu["name"] == "Floyd Bennett Field") & (lu["class"] == "park")]
    pk = gpd.GeoSeries.from_wkb(lu.geometry, crs=4326).to_crs(UTM)
    out = shapely.union_all(pk.values).buffer(0)
    out = max(getattr(out, "geoms", [out]), key=lambda q: q.area)
    out = shapely.Polygon(out.exterior).simplify(5)
    print("outline", f"{out.area / 1e4:.0f} ha; pavement inside: {big.geometry.iloc[0].intersection(out).area / big.geometry.iloc[0].area:.2f}")
    o = gpd.GeoDataFrame([{"name": "Floyd Bennett Field", "class": "airport",
                           "source_url": "https://www.openstreetmap.org/relation/9460480",
                           "note": "Outline of the National Park Service unit 'Floyd Bennett Field' (OpenStreetMap relation 9460480, "
                                   "ODbL, via Overture base land_use), outer ring, simplified to 5 m: the airfield of 1931-1971 "
                                   "with the Navy's additions.", "geometry": out}], geometry="geometry", crs=UTM).to_crs(4326)
    o.geometry = shapely.set_precision(o.geometry.values, 1e-7)
    op = OUT / "extra_outlines.geojson"
    if op.exists():
        prev = gpd.read_file(op)
        prev = prev[prev["name"] != "Floyd Bennett Field"]
        if len(prev):
            o = gpd.GeoDataFrame(pd.concat([prev, o], ignore_index=True), geometry="geometry", crs=4326)
    o.to_file(op, driver="GeoJSON")


if __name__ == "__main__":
    main()
