"""Research helper: railroads of the counties that are gone -> features with "part": "counties" in
data/manual/transit/former_railroads.geojson (rewritten on every run; the city's features are not touched).

  * OpenHistoricalMap railway ways with an end date in the counties (data/raw/transit/ohm/ohm_rail_region.json,
    CC0), dates as mapped (a bare year means the year only) - the Erie's Piermont, Nyack, Newark, Caldwell and
    Greenwood Lake lines, the Haverstraw and New City branches, the Harrison cut-off ... Street railways are
    left out. The Central of New Jersey's main line across Newark Bay takes cited dates (CITED).
  * The New York, Westchester & Boston Railway north of the city line and the Putnam Division: no
    OpenHistoricalMap ways; the geometry is OpenStreetMap's abandoned right of way and the rail trail on it
    (osm/osm_razed_region.json and osm/osm_trails_region.json, ODbL), the dates are from the two articles,
    by stretch (the ends of the stretches are placed at the stations' longitudes / latitudes: estimated).

    ../../../../.venv/bin/python build_county_former.py
"""
import json
import sys
from pathlib import Path

import requests
from shapely.geometry import LineString, Polygon

ROOT = Path(__file__).resolve().parents[4]
RAW = ROOT / "data" / "raw" / "transit"
OUT = ROOT / "data" / "manual" / "transit" / "former_railroads.geojson"
WP = "https://en.wikipedia.org/wiki/"
BOX = (-74.52, 40.47, -73.40, 41.38)
poly = Polygon(json.load(open(ROOT / "data" / "manual" / "extent_ring.json"))["ring"]).buffer(0.004)
city = Polygon(json.load(open(ROOT / "data" / "manual" / "transit" / "city_ring.json"))["ring"]).buffer(0.004)
CITED = {
    # OpenHistoricalMap name: (start, end, note, source)
    "CNJ Mainline": ("1864", "1978-08-06", "Central Railroad of New Jersey's main line to Jersey City across Newark Bay: opened 1864 (year only: estimated day); "
                     "main line trains left it under the Aldene Plan on 30 Apr 1967, the last freight crossed the bridge in 1976, the last Bayonne shuttle ran "
                     "6 Aug 1978; the bridge's lift spans came down from July 1980", WP + "CRRNJ_Newark_Bay_Bridge"),
}


def trails():
    f = RAW / "osm" / "osm_trails_region.json"
    if not f.exists():
        s = requests.Session()
        s.headers["User-Agent"] = "NYCThroughTime-research/0.1"
        if Path("/root/.ccr/ca-bundle.crt").exists():
            s.verify = "/root/.ccr/ca-bundle.crt"
        q = (f'[out:json][timeout:200];way["name"~"^(South County Trailway|North County Trailway)$"]({BOX[1]},{BOX[0]},{BOX[3]},{BOX[2]});out body geom;')
        import time
        for k in range(6):
            time.sleep(8 * k)
            try:
                r = s.post("https://overpass-api.de/api/interpreter", data={"data": q}, timeout=300)
                if r.status_code == 200 and r.content[:1] == b"{":
                    f.write_bytes(r.content)
                    break
            except Exception as e:  # noqa: BLE001
                print("trails", repr(e)[:120])
    return json.load(open(f))["elements"] if f.exists() else []


def feat(name, start, end, st, g, source, licence, **extra):
    return {"type": "Feature", "properties": {"name": name, "start": start, "end": end, "structure": st, "kind": "rail", "part": "counties",
                                               "source": source, "licence": licence, **extra},
            "geometry": {"type": "LineString", "coordinates": [[round(x, 6), round(y, 6)] for x, y in g.coords]}}


def structure(t):
    layer = t.get("layer", "0")
    layer = int(float(layer)) if layer.lstrip("-").replace(".", "").isdigit() else 0
    return "tunnel" if (t.get("tunnel") and t.get("tunnel") != "no") or layer < 0 else "elevated" if (t.get("bridge") and t.get("bridge") != "no") else "ground"


NYWB_WHITE_PLAINS = {72660744, 213202445}   # OpenStreetMap ways of the White Plains branch
NYWB_NOT_BUILT = {76697943}                 # a way beyond the White Plains terminal (no such line was opened)


def nywb(lon, lat, way=0):
    """Opening day of the New York, Westchester & Boston at a place (article: main line 29 May 1912, White Plains
    branch 1 Jul 1912, Larchmont 1921, Mamaroneck 1926, Harrison 1927, Rye 1928, Port Chester December 1929)."""
    if way in NYWB_WHITE_PLAINS:
        return "1912-07-01"
    if lon < -73.787:
        return "1912-05-29"
    for east, day in ((-73.758, "1921"), (-73.736, "1926"), (-73.712, "1927"), (-73.682, "1928")):
        if lon < east:
            return day
    return "1929-12"


def putnam_end(lat):
    """When the Putnam Division's track went out of use (article: removal north of East View from 1962; Elmsford
    served until 1975; cut back to Chauncey by 1977; last customer, in the Bronx, 1989)."""
    return "1962" if lat > 41.078 else "1975" if lat > 41.055 else "1977" if lat > 41.007 else "1989"


feats, km = [], {}
old = json.load(open(OUT))
keep = [f for f in old["features"] if f["properties"].get("part") != "counties"]
seen = set()
for w in json.load(open(RAW / "ohm" / "ohm_rail_region.json"))["elements"]:
    t = w.get("tags", {})
    if w["type"] != "way" or not t.get("end_date") or not t.get("start_date") or len(w.get("geometry", [])) < 2:
        continue
    if t.get("railway") not in ("rail", "light_rail", "narrow_gauge", "disused", "abandoned"):
        continue
    g = LineString([(p["lon"], p["lat"]) for p in w["geometry"]])
    c = g.interpolate(0.5, normalized=True)
    if not poly.contains(c) or city.contains(c):
        continue
    nm = t.get("name", "")
    start, end, extra = t["start_date"], t["end_date"], {}
    src = f"https://www.openhistoricalmap.org/way/{w['id']}"
    if nm in CITED:
        start, end, note, s2 = CITED[nm]
        extra = {"note": note, "geometry_source": src}
        src = s2
    if nm == "CNJ Newark Bay Bridge" and "bridge1864" not in seen:
        # OpenHistoricalMap draws the four tracks of the lift bridge of 1926; the crossing dates from 1864 (trestle and
        # swing bridge, bascule bridge 1904): one of the four tracks stands in for the earlier bridges
        seen.add("bridge1864")
        start = "1864"
        extra = {"note": "the earlier bridges on this crossing (opened 1864, year only: estimated day; rebuilt 1887 and 1904), drawn on one track of "
                         "the 1926 lift bridge: position estimated", "geometry_source": src}
        src = WP + "CRRNJ_Newark_Bay_Bridge"
    if len(start) < 4 or start[:4] >= end[:4] or int(start[:4]) < 1825:
        continue
    feats.append(feat(nm, start, end, structure(t), g, src, "CC0 (OpenHistoricalMap)", **extra))
    km[nm or "(no name, OpenHistoricalMap)"] = km.get(nm or "(no name, OpenHistoricalMap)", 0) + g.length * 100
for src_file, els in (("razed", json.load(open(RAW / "osm" / "osm_razed_region.json"))["elements"]), ("trails", trails())):
    for w in els:
        t = w.get("tags", {})
        if w["type"] != "way" or len(w.get("geometry", [])) < 2 or w["id"] in seen:
            continue
        nm = t.get("name", "")
        op = " ".join(t.get(k, "") for k in ("operator", "old_railway_operator", "abandoned:operator", "old_name"))
        g = LineString([(p["lon"], p["lat"]) for p in w["geometry"]])
        c = g.interpolate(0.5, normalized=True)
        if not poly.contains(c) or city.contains(c):
            continue
        osm = f"https://www.openstreetmap.org/way/{w['id']}"
        if "Westchester and Boston" in nm + op or "Westchester & Boston" in nm + op:
            seen.add(w["id"])
            if w["id"] in NYWB_NOT_BUILT:
                continue
            pts = list(g.coords)
            days = [nywb(x, y, w["id"]) for x, y in pts]
            a = 0
            for k in range(1, len(pts) + 1):  # one piece per run of points that opened together
                if k == len(pts) or days[k] != days[a]:
                    if k - a >= 2 or (k < len(pts) and k - a >= 1):
                        part = LineString(pts[a:min(k + 1, len(pts))]) if k < len(pts) else LineString(pts[a:k])
                        feats.append(feat("New York, Westchester & Boston Railway", days[a], "1937-12-31", structure(t), part,
                                          WP + "New_York,_Westchester_and_Boston_Railway", "ODbL (OpenStreetMap contributors)", geometry_source=osm,
                                          note="closed 31 Dec 1937; the opening is that of its stretch (ends of the stretches estimated)"))
                        km["New York, Westchester & Boston"] = km.get("New York, Westchester & Boston", 0) + part.length * 100
                    a = k
        elif nm in ("North County Trailway", "South County Trailway") or (nm == "Putnam Branch" and c.y < 41.345):
            seen.add(w["id"])
            feats.append(feat("New York & Putnam Railroad (Putnam Division)", "1881", putnam_end(c.y), structure(t), g,
                              WP + "New_York_and_Putnam_Railroad", "ODbL (OpenStreetMap contributors)", geometry_source=osm,
                              note="opened 1881 (year only: estimated day); passenger trains until 29 May 1958; the end is when the track of the "
                                   "stretch went out of use (years only, stretch ends estimated)" + ("; geometry: the rail trail on the roadbed" if "Trailway" in nm else "")))
            km["Putnam Division"] = km.get("Putnam Division", 0) + g.length * 100
old["features"] = keep + feats
OUT.write_text(json.dumps(old))
print(len(keep), "city pieces kept;", len(feats), "county pieces,", round(sum(km.values())), "km")
for k, v in sorted(km.items(), key=lambda kv: -kv[1])[:40]:
    print(f"  {v:6.1f} km  {k}")
