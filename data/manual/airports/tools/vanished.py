"""Vanished airfields traced on USGS historical topographic sheets (HTMC GeoTIFFs, public
domain; rendered with tools/topo_crop.py in UTM 18N and read off the 100 m grid by eye,
+-10 m): Flushing Airport and Miller Field.
  -> extra_pavement.geojson   runway polygons (airport, kind, start_year, end_year, width_m,
                              confidence, source_url, note); kind 'turf_strip' is kept for
                              the record but is not pavement (airports.py does not draw it)
  -> extra_outlines.geojson   airfield outlines (name, class), added to Floyd Bennett Field's
Run from the repository root:  .venv/bin/python data/manual/airports/tools/vanished.py
"""
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely
from shapely.geometry import LineString, Polygon

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "data" / "manual" / "airports"
UTM = "EPSG:32618"
S = "https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/NY/"
FLU66 = S + "NY_Flushing_137330_1966_24000_geo.tif"
NAR55 = S + "NY_The%20Narrows_139985_1955_24000_geo.tif"
FREEMAN = "https://www.airfields-freeman.com/NY/Airfields_NY_NY_Queens.htm"

# airport, kind, name, (x0, y0), (x1, y1) centre line in UTM 18N metres, width, start, end, confidence, source, note
STRIPS = [
    ("Flushing Airport", "runway", "north-south runway (18/36)", (598315, 4515112), (598525, 4514260), 30, 1957, 1984, "estimated", FLU66,
     "Traced on the USGS Flushing 1:24,000 sheet, 1966 edition (scan 137330): the dashed strip from 20th Avenue south-south-east "
     "along Linden Place, 877 m (2,880 ft) x 30 m — the '2,950 ft paved runway' of the 1962 AOPA directory. Paving year ESTIMATED 1957: "
     "'an unpaved landing area' on c. 1951 and 1954 air photos, '2 paved runways' on the July 1960 sectional chart "
     "(Abandoned & Little-Known Airfields). The same dry strip crosses the marsh on the 1947 sheet. Ends with the airport, 1984 "
     "(the asphalt lay derelict and flooded afterwards)."),
    ("Flushing Airport", "runway", "north-east / south-west runway", (598952, 4515130), (598498, 4514478), 28, 1957, 1984, "estimated", FLU66,
     "Traced on the same sheet: the dashed strip from 20th Avenue south-west to the foot of the north-south runway, 797 m (2,615 ft) "
     "x 28 m. Paved by July 1960 ('2 paved runways'); 'NE/SW runway closed' on the 1965 sectional chart but still drawn on the 1966 "
     "sheet: kept to 1984 (ESTIMATED)."),
    ("Miller Field", "turf_strip", "east-west landing strip", (575605, 4491317), (576570, 4491177), 44, 1921, 1969, "estimated", NAR55,
     "Grass landing strip (Miller Field 'had a grass runway ... the last airport with a grass runway in New York City', Wikipedia) "
     "as drawn dashed on the USGS The Narrows 1:24,000 sheet of 1955 (scan 139985): 975 m x 44 m from the Hylan Boulevard corner "
     "east-south-east. NOT pavement: not drawn by airports.py."),
    ("Miller Field", "turf_strip", "north-west / south-east landing strip", (576131, 4491465), (576453, 4490957), 36, 1921, 1969, "estimated", NAR55,
     "Second grass strip on the same sheet, 601 m x 36 m, from Elm Tree Avenue toward the hangars at the shore. NOT pavement."),
]

# Flushing Airport as drawn on the 1966 sheet: 20th Avenue (north), the property line and
# Linden Place (west), the drainage ditch beside the north-east runway and Mill Creek (east, south)
FLUSHING = [(598225, 4515140), (598975, 4515145), (598900, 4515040), (598700, 4514765), (598522, 4514492), (598522, 4514400),
            (598572, 4514270), (598480, 4514185), (598262, 4514790), (598225, 4514808)]


def main():
    feats = []
    for ap, kind, name, a, b, w, y0, y1, conf, src, note in STRIPS:
        geom = LineString([a, b]).buffer(w / 2, cap_style="flat")
        feats.append({"airport": ap, "kind": kind, "piece": name, "start_year": y0, "end_year": y1, "width_m": w,
                      "confidence": conf, "source_url": src, "note": note, "geometry": geom})
    g = gpd.GeoDataFrame(feats, geometry="geometry", crs=UTM).to_crs(4326)
    g.geometry = shapely.set_precision(g.geometry.values, 1e-7)
    g.to_file(OUT / "extra_pavement.geojson", driver="GeoJSON")
    outl = [{"name": "Flushing Airport", "class": "airport", "source_url": FLU66,
             "note": "ESTIMATED field boundary read off the USGS Flushing 1:24,000 sheet, 1966 edition: 20th Avenue, the property line "
                     "and Linden Place, the ditch beside the north-east runway and Mill Creek (the airport's 250-300 acres of marsh "
                     "reached further; this is the part in use as drawn).", "geometry": Polygon(FLUSHING)}]
    lu = pd.read_parquet(ROOT / "data" / "raw" / "overture" / "2026-10-21.0" / "base_land_use.parquet")
    m = lu[(lu["name"] == "Miller Field") & (lu["class"] == "park")]
    mg = shapely.union_all(gpd.GeoSeries.from_wkb(m.geometry, crs=4326).to_crs(UTM).values).buffer(0)
    mg = max(getattr(mg, "geoms", [mg]), key=lambda q: q.area)
    outl.append({"name": "Miller Field", "class": "military_airport", "source_url": "https://www.openstreetmap.org/search?query=Miller%20Field%20Staten%20Island",
                 "note": "Outline of the National Park Service unit 'Miller Field' (OpenStreetMap, ODbL, via Overture base land_use), "
                         "outer ring simplified to 5 m: the Army reservation of 1919-1969 as it survives (the 1955 USGS sheet draws "
                         "the same block between Hylan Boulevard, New Dorp Lane and the beach).",
                 "geometry": Polygon(mg.exterior).simplify(5)})
    o = gpd.GeoDataFrame(outl, geometry="geometry", crs=UTM)
    for n, a in zip(o["name"], o.area / 1e4):
        print(n, f"{a:.1f} ha")
    o = o.to_crs(4326)
    o.geometry = shapely.set_precision(o.geometry.values, 1e-7)
    op = OUT / "extra_outlines.geojson"
    prev = gpd.read_file(op) if op.exists() else None
    if prev is not None:
        prev = prev[~prev["name"].isin(o["name"])]
        o = gpd.GeoDataFrame(pd.concat([prev, o], ignore_index=True), geometry="geometry", crs=4326)
    o.to_file(op, driver="GeoJSON")
    print(len(g), "strips;", len(o), "outlines")


if __name__ == "__main__":
    main()
