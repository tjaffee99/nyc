"""Research helper: downloads for the counties around the city (Hudson, Bergen, Essex, Union, Passaic NJ;
Westchester, Rockland NY) -> data/raw/transit/ (gitignored). Every part is cached; delete a file to refetch.

  ohm/ohm_rail_region.json      OpenHistoricalMap railway ways + station nodes of the region box (CC0)
  osm/osm_stations_region.json  OpenStreetMap stations / halts / tram stops, also disused ones (ODbL)
  osm/osm_routes_region.json    OpenStreetMap route relations of PATH and the two light rail systems (ODbL)
  osm/osm_razed_region.json     OpenStreetMap abandoned / razed / disused railway ways (ODbL)
  wikidata/stations_region.csv  Wikidata station items of the region box with P1619 / P3999 (CC0)
  gtfs_path/, gtfs_mnr/         the Port Authority's PATH GTFS and the MTA's Metro-North GTFS (public feeds)

NJ Transit's GTFS sits behind a developer login and is not used: its stations come from OpenStreetMap.

    ../../../../.venv/bin/python fetch_region.py
"""
import csv
import io
import sys
import time
import zipfile
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[4]
RAW = ROOT / "data" / "raw" / "transit"
BOX = (-74.52, 40.47, -73.40, 41.38)  # common.REGION_BBOX
W, S, E, N = BOX
UA = {"User-Agent": "NYCThroughTime-research/0.1"}
CA = "/root/.ccr/ca-bundle.crt"
OHM = "https://overpass-api.openhistoricalmap.org/api/interpreter"
OSM = "https://overpass-api.de/api/interpreter"
WD = "https://query.wikidata.org/sparql"


def sess():
    s = requests.Session()
    s.headers.update(UA)
    if Path(CA).exists():
        s.verify = CA
    return s


def overpass(url, query, out, tries=3):
    out = RAW / out
    if out.exists() and out.stat().st_size > 1000:
        print("have", out.name, out.stat().st_size)
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    for k in range(tries):
        try:
            r = sess().post(url, data={"data": query}, timeout=420)
            if r.status_code == 200 and r.content[:1] == b"{":
                out.write_bytes(r.content)
                print("wrote", out.name, len(r.content))
                return
            print(out.name, "status", r.status_code, r.text[:200].replace("\n", " "))
        except Exception as e:  # noqa: BLE001
            print(out.name, "error", repr(e)[:200])
        time.sleep(20 * (k + 1))
    print("FAILED", out.name)


def wikidata():
    out = RAW / "wikidata" / "stations_region.csv"
    if out.exists() and out.stat().st_size > 1000:
        print("have", out.name)
        return
    rows, head = [], None
    # four tiles: the label service and the class closure time out on the whole box
    xs, ys = [W, (W + E) / 2, E], [S, (S + N) / 2, N]
    for i in range(2):
        for j in range(2):
            q = f"""SELECT ?s ?sLabel ?opened ?openedPrec ?closed ?closedPrec ?coord ?article
 (GROUP_CONCAT(DISTINCT ?instLabel; separator="|") AS ?inst) (GROUP_CONCAT(DISTINCT ?lineLabel; separator="|") AS ?lines)
 (GROUP_CONCAT(DISTINCT ?opLabel; separator="|") AS ?ops) WHERE {{
  SERVICE wikibase:box {{ ?s wdt:P625 ?coord . bd:serviceParam wikibase:cornerSouthWest "Point({xs[i]} {ys[j]})"^^geo:wktLiteral ;
     wikibase:cornerNorthEast "Point({xs[i + 1]} {ys[j + 1]})"^^geo:wktLiteral . }}
  ?s wdt:P31 ?inst . ?inst wdt:P279* wd:Q12819564 .
  OPTIONAL {{ ?s p:P1619/psv:P1619 [wikibase:timeValue ?opened; wikibase:timePrecision ?openedPrec] }}
  OPTIONAL {{ ?s p:P3999/psv:P3999 [wikibase:timeValue ?closed; wikibase:timePrecision ?closedPrec] }}
  OPTIONAL {{ ?s wdt:P81 ?line . ?line rdfs:label ?lineLabel . FILTER(LANG(?lineLabel) = "en") }}
  OPTIONAL {{ ?s wdt:P137 ?op . ?op rdfs:label ?opLabel . FILTER(LANG(?opLabel) = "en") }}
  OPTIONAL {{ ?article schema:about ?s ; schema:isPartOf <https://en.wikipedia.org/> }}
  ?inst rdfs:label ?instLabel . FILTER(LANG(?instLabel) = "en")
  OPTIONAL {{ ?s rdfs:label ?sLabel . FILTER(LANG(?sLabel) = "en") }}
}} GROUP BY ?s ?sLabel ?opened ?openedPrec ?closed ?closedPrec ?coord ?article"""
            for k in range(3):
                try:
                    r = sess().get(WD, params={"query": q}, headers={"Accept": "text/csv"}, timeout=200)
                    if r.status_code == 200:
                        rd = list(csv.reader(io.StringIO(r.text)))
                        head = rd[0]
                        rows += rd[1:]
                        print("wikidata tile", i, j, len(rd) - 1)
                        break
                    print("wikidata", r.status_code, r.text[:200])
                except Exception as e:  # noqa: BLE001
                    print("wikidata error", repr(e)[:200])
                time.sleep(15)
    if head:
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(head)
            w.writerows(rows)
        print("wrote", out.name, len(rows))


def gtfs(name, urls):
    d = RAW / name
    if (d / "stops.txt").exists():
        print("have", name)
        return
    for url in urls:
        try:
            r = sess().get(url, timeout=120)
            if r.status_code == 200 and r.content[:2] == b"PK":
                d.mkdir(parents=True, exist_ok=True)
                z = zipfile.ZipFile(io.BytesIO(r.content))
                for m in z.namelist():  # plain text members only, flat
                    if m.endswith(".txt") and "/" not in m and ".." not in m:
                        (d / m).write_bytes(z.read(m))
                (d / "SOURCE.txt").write_text(url + "\n")
                print("wrote", name, sorted(p.name for p in d.iterdir()))
                return
            print(name, url, "status", r.status_code, r.content[:80])
        except Exception as e:  # noqa: BLE001
            print(name, url, "error", repr(e)[:200])
    print("FAILED", name)


what = sys.argv[1:] or ["ohm", "stations", "routes", "razed", "wikidata", "gtfs"]
bb = f"({S},{W},{N},{E})"
if "ohm" in what:
    overpass(OHM, f'[out:json][timeout:400];(way["railway"]{bb};node["railway"~"station|halt|stop"]{bb};);out body geom;', "ohm/ohm_rail_region.json")
if "stations" in what:
    overpass(OSM, f'[out:json][timeout:300];(nwr["railway"~"^(station|halt|tram_stop)$"]{bb};nwr["disused:railway"~"station|halt"]{bb};'
             f'nwr["abandoned:railway"~"station|halt"]{bb};nwr["railway:historic"~"station|halt"]{bb};nwr["historic:railway"~"station|halt"]{bb};'
             f'nwr["historic"="railway_station"]{bb};);out center tags;', "osm/osm_stations_region.json")
if "routes" in what:
    overpass(OSM, f'[out:json][timeout:300];(relation["route"~"^(subway|light_rail|tram)$"]["network"~"PATH|NJ Transit|NJT|Hudson|Newark",i]{bb};'
             f'relation["route"~"^(subway|light_rail|tram)$"]["operator"~"Port Authority|NJ Transit|New Jersey Transit",i]{bb};);out body geom;',
             "osm/osm_routes_region.json")
if "razed" in what:
    overpass(OSM, f'[out:json][timeout:400];(way["railway"~"^(abandoned|razed|dismantled|disused)$"]{bb};way["abandoned:railway"]{bb};'
             f'way["razed:railway"]{bb};way["disused:railway"]{bb};way["highway"]["abandoned:railway"]{bb};'
             f'way["highway"~"cycleway|path|footway"]["railway"="abandoned"]{bb};);out body geom;', "osm/osm_razed_region.json")
if "wikidata" in what:
    wikidata()
if "gtfs" in what:
    gtfs("gtfs_path", ["http://data.trilliumtransit.com/gtfs/path-nj-us/path-nj-us.zip",
                       "https://data.trilliumtransit.com/gtfs/path-nj-us/path-nj-us.zip"])
    gtfs("gtfs_mnr", ["https://rrgtfsfeeds.s3.amazonaws.com/gtfsmnr.zip",
                      "http://web.mta.info/developers/data/mnr/google_transit.zip"])
