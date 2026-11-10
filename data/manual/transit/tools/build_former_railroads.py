"""Research helper: railroads and pieces of subway that are gone -> data/manual/transit/former_railroads.geojson.

  * OpenHistoricalMap railway ways with an end date inside the map (CC0), except the elevated
    lines (those are in elevated_lines.geojson with station-by-station dates) and street railways;
    dates are OHM's start_date / end_date as mapped (a bare year means the year only).
  * The West Side freight viaduct (High Line), 1934-1980: the OpenStreetMap ways still tagged as
    abandoned railway (ODbL) - only the parts OSM keeps as railway are drawn.

    ../../../../.venv/bin/python build_former_railroads.py
"""
import json
import sys
from pathlib import Path

from shapely.geometry import LineString, Polygon

ROOT = Path(__file__).resolve().parents[4]
RAW = ROOT / "data" / "raw" / "transit"
EL = ("IRT Ninth", "IRT Sixth", "IRT Second", "IRT Third", "IRT City Hall", "NYC Elevated", "BMT Fifth", "BMT Fulton", "BMT Lexington")
poly = Polygon(json.load(open(ROOT / "viewer" / "public" / "data" / "map-extent.json"))["ring"]).buffer(0.004)
feats, km = [], {}
for w in json.load(open(RAW / "ohm" / "ohm_rail.json"))["elements"]:
    t = w.get("tags", {})
    if w["type"] != "way" or not t.get("end_date") or not t.get("start_date") or t.get("railway") not in ("rail", "subway", "light_rail", "narrow_gauge", "disused", "abandoned"):
        continue
    nm = t.get("name", "")
    if nm.startswith(EL) or (nm == "" and t["start_date"] == "1883" and t["end_date"] == "1944"):
        continue
    g = LineString([(p["lon"], p["lat"]) for p in w["geometry"]])
    if not poly.contains(g.centroid) or len(t["start_date"]) < 4 or t["start_date"][:4] >= t["end_date"][:4]:
        continue
    layer = int(float(t.get("layer", "0") or 0)) if t.get("layer", "0").lstrip("-").replace(".", "").isdigit() else 0
    st = "tunnel" if t.get("tunnel") or layer < 0 else "elevated" if (t.get("bridge") or layer > 0) else "ground"
    kind = "subway" if t.get("railway") == "subway" or nm.startswith(("IRT", "BMT", "IND", "Hudson Terminal")) else "rail"
    feats.append({"type": "Feature", "properties": {
        "name": nm, "start": t["start_date"], "end": t["end_date"], "structure": st, "kind": kind,
        "source": f"https://www.openhistoricalmap.org/way/{w['id']}", "licence": "CC0 (OpenHistoricalMap)"},
        "geometry": {"type": "LineString", "coordinates": [[round(x, 6), round(y, 6)] for x, y in g.coords]}})
    km[nm] = km.get(nm, 0) + g.length * 100
for w in json.load(open(RAW / "osm" / "osm_razed.json"))["elements"]:
    t = w.get("tags", {})
    if w["type"] != "way" or t.get("name") not in ("High Line",):
        continue
    g = LineString([(p["lon"], p["lat"]) for p in w["geometry"]])
    feats.append({"type": "Feature", "properties": {
        "name": "West Side freight line viaduct (High Line)", "start": "1934-06-29", "end": "1980",
        "structure": "elevated", "kind": "rail", "joins_elevated": True,
        "note": "dedicated 29 Jun 1934; last train in 1980 (year only: estimated)",
        "source": "https://en.wikipedia.org/wiki/High_Line", "geometry_source": f"https://www.openstreetmap.org/way/{w['id']}",
        "licence": "ODbL (OpenStreetMap contributors)"},
        "geometry": {"type": "LineString", "coordinates": [[round(x, 6), round(y, 6)] for x, y in g.coords]}})
    km["High Line"] = km.get("High Line", 0) + g.length * 100
# New York, Westchester & Boston Railway south of East 180th Street (north of it the line is today's
# Dyre Avenue subway): the abandoned right of way as OpenStreetMap still has it (via Overture)
import geopandas as gpd
r = gpd.read_parquet(ROOT / "data" / "raw" / "overture" / "2026-10-21.0" / "rail.parquet")
for g in r[r["name"] == "New York, Westchester and Boston Railway"].geometry:
    if g.geom_type != "LineString" or not poly.contains(g.centroid):
        continue
    feats.append({"type": "Feature", "properties": {
        "name": "New York, Westchester & Boston Railway", "start": "1912-05-29", "end": "1937-12-31", "structure": "ground", "kind": "rail",
        "note": "passenger service 29 May 1912 - 31 Dec 1937", "source": "https://en.wikipedia.org/wiki/New_York,_Westchester_and_Boston_Railway",
        "geometry_source": "OpenStreetMap abandoned railway (Overture rail extract)", "licence": "ODbL (OpenStreetMap contributors)"},
        "geometry": {"type": "LineString", "coordinates": [[round(x, 6), round(y, 6)] for x, y in g.coords]}})
    km["NYW&B"] = km.get("NYW&B", 0) + g.length * 100
(ROOT / "data" / "manual" / "transit" / "former_railroads.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
print(len(feats), "pieces", file=sys.stderr)
for k, v in sorted(km.items(), key=lambda kv: -kv[1]):
    print(f"   {v:6.1f} km  {k}", file=sys.stderr)
