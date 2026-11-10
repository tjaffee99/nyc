"""Downloads for the piers part (all into data/raw/piers/, gitignored).

  python download.py meta      metadata records of every 1:24,000 sheet of the quadrangles that hold city waterfront
                               -> data/raw/piers/meta/*.xml, data/raw/piers/usgs_meta.json
  python download.py sheets    the GeoTIFFs listed in SHEETS -> data/raw/piers/usgs/
  python download.py charts    the nautical chart editions listed in CHARTS -> data/raw/piers/noaa/
  python download.py osm       today's piers (OpenStreetMap via Overture base/infrastructure) -> data/raw/piers/overture_piers.parquet

Sources
  USGS Historical Topographic Map Collection (public domain): product list from The National Map API
  (https://tnmaccess.nationalmap.gov/api/v1/products?datasets=Historical%20Topographic%20Maps&bbox=...), saved earlier by
  the natural-landscape part as data/raw/natural/usgs/tnm_all.json; files at
  https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/<state>/<file>.
  Overture Maps 2026-10-21.0, theme=base, type=infrastructure (OpenStreetMap, ODbL).
"""
import json
import re
import sys
from pathlib import Path

import requests

ROOT = Path("/home/user/nyc")
RAW = ROOT / "data/raw/piers"
UA = {"User-Agent": "NYCThroughTime-research/0.1"}
QUADS = ["Jersey City", "Weehawken", "Central Park", "Brooklyn", "The Narrows", "Coney Island", "Flushing", "Mount Vernon",
         "Mt Vernon", "Yonkers", "Elizabeth", "Arthur Kill", "Perth Amboy", "Far Rockaway", "Jamaica"]
BBOX = (-74.27, 40.48, -73.69, 40.93)


def listing():
    d = json.load(open(ROOT / "data/raw/natural/usgs/tnm_all.json"))
    out = []
    for r in d:
        m = re.search(r"1:(\d+)-scale Quadrangle for (.+?), (\w\w) (\d{4})", r["title"])
        if not m:
            continue
        sc, name, st, yr = int(m.group(1)), m.group(2), m.group(3), int(m.group(4))
        if name in QUADS and sc in (24000, 25000, 31680):
            url = r["urls"].get("GeoTIFF") or r["downloadURL"]
            out.append(dict(quad=name, scale=sc, year=yr, url=url, file=url.split("/")[-1].replace("%20", "_"), meta=r["vendorMetaUrl"],
                            bbox=r["boundingBox"], size=r["sizeInBytes"]))
    return out


def meta():
    (RAW / "meta").mkdir(parents=True, exist_ok=True)
    rows = listing()
    for r in rows:
        p = RAW / "meta" / (r["file"].replace(".tif", ".xml"))
        if not p.exists():
            x = requests.get(r["meta"], headers=UA, timeout=60)
            if x.status_code != 200:
                print("meta failed", r["file"], x.status_code)
                continue
            p.write_text(x.text)
        t = p.read_text()
        g = lambda tag: (re.search(rf"<{tag}>(.*?)</{tag}>", t, re.S) or [None, ""])[1]
        r["begdate"], r["enddate"] = g("begdate"), g("enddate")
        r["origin"] = re.findall(r"<origin>(.*?)</origin>", t)[-1] if "<origin>" in t else ""
        # the HTMC record keeps the dates printed in the map collar as <procstep> pairs
        for key, val in re.findall(r"<procdesc>([^<]{3,40})</procdesc>\s*<procdate>(\d{4})</procdate>", t):
            r[key] = val
        r["supplinf"] = g("supplinf")[:300]
    json.dump(rows, open(RAW / "usgs_meta.json", "w"), indent=1)
    for r in sorted(rows, key=lambda r: (r["quad"], r["year"], r["file"])):
        print(r["quad"], r["scale"], r["year"], r["file"], "|", r["begdate"], r["enddate"], "|", {k: r[k] for k in
              ("Imprint Year", "Photo Revision Year", "Aerial Photo Year", "Field Check Year", "Survey Year", "Edit Year", "Photo Inspection Year", "Planimetric Source Year") if r.get(k)})


def sheets(names):
    (RAW / "usgs").mkdir(parents=True, exist_ok=True)
    rows = {r["file"]: r for r in listing()}
    for n in names:
        r = rows[n]
        p = RAW / "usgs" / n
        if p.exists() and p.stat().st_size == r["size"]:
            continue
        with requests.get(r["url"], headers=UA, timeout=300, stream=True) as x:
            x.raise_for_status()
            with open(p, "wb") as f:
                for chunk in x.iter_content(1 << 20):
                    f.write(chunk)
        print(n, p.stat().st_size, flush=True)


def osm():
    import duckdb
    out = RAW / "overture_piers.parquet"
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial;")
    con.execute("CREATE OR REPLACE SECRET overture (TYPE s3, PROVIDER config, KEY_ID '', SECRET '', REGION 'us-west-2');")
    x0, y0, x1, y1 = BBOX
    src = "s3://overturemaps-us-west-2/release/2026-10-21.0/theme=base/type=infrastructure/*"
    con.execute(f"""COPY (SELECT id, subtype, class, names.primary AS name, CAST(source_tags AS JSON) AS tags, height, surface,
                           sources[1].dataset AS source_dataset, sources[1].record_id AS source_record, geometry
                    FROM read_parquet('{src}', hive_partitioning=1)
                    WHERE bbox.xmin < {x1} AND bbox.xmax > {x0} AND bbox.ymin < {y1} AND bbox.ymax > {y0}
                      AND (subtype IN ('pier', 'quay') OR class IN ('pier', 'quay', 'breakwater', 'groyne')))
                    TO '{out}' (FORMAT parquet)""")
    print(con.execute(f"SELECT subtype, class, ST_GeometryType(geometry) t, count(*) FROM '{out}' GROUP BY ALL ORDER BY 4 DESC").fetchall())


CHARTS = {  # NOAA / US Coast & Geodetic Survey charts, Office of Coast Survey Historical Map & Chart Collection (public domain)
    # 745 -> 12335  "Hudson and East Rivers, Governors Island to 67th Street", 1:10,000
    # (the collection's "745-<n>-<year>" files before 1959 are another agency's chart 745, Racine Harbor: not used)
    "745": ["3N745-31", "3N745-35", "3N745-39", "3N745-44", "745-1-1959", "745-10-1966", "745-10-1967", "745-8-1970", "745-8-1973",
            "12335-4-1976", "12335-5-1979", "12335-4-1982", "12335-11-1986", "12335-2-1990", "12335-2-1994", "12335-1-1998",
            "12335-12-2001", "12335-09-2006", "12335-03-2012", "12335-1-2020"],
    # 541 -> 12334  "New York Harbor, Upper Bay and Narrows (anchorage chart)", 1:10,000
    "541": ["541-5-1898", "541-5-1912", "541-9-1916", "541-2-1927", "541-2-1930", "541-4-1934", "541-2-1938", "541-10-1942", "541-5-1947",
            "541-11-1957", "541-8-1966", "541-7-1970", "541-4-1974", "12334-4-1978", "12334-8-1982", "12334-2-1986", "12334-3-1990",
            "12334-4-1994", "12334-12-1997", "12334-8-2000", "12334-04-2004", "12334-08-2008", "12334-11-2013", "12334-1-2020"],
}


def charts():
    """JPGs through the collection's own download link (https://historicalcharts.noaa.gov/search.php, chart number search)."""
    import time
    (RAW / "noaa").mkdir(parents=True, exist_ok=True)
    for series, ids in CHARTS.items():
        for cid in ids:
            p = RAW / "noaa" / f"{cid}.jpg"
            if p.exists() and p.stat().st_size > 1e6:
                continue
            for attempt in range(3):
                try:
                    with requests.get("https://historicalcharts.noaa.gov/includes/downloadsingle.php", params={"filename": cid, "fileExt": ".jpg"},
                                      headers=UA, timeout=600, stream=True) as x:
                        x.raise_for_status()
                        with open(p, "wb") as f:
                            for chunk in x.iter_content(1 << 20):
                                f.write(chunk)
                    print(cid, p.stat().st_size, flush=True)
                    break
                except Exception as e:
                    print("retry", cid, repr(e)[:100], flush=True)
                    time.sleep(5)
            time.sleep(1)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "meta":
        meta()
    elif cmd == "sheets":
        sheets(sys.argv[2:] or json.load(open(Path(__file__).parent / "sheets.json")))
    elif cmd == "osm":
        osm()
    elif cmd == "charts":
        charts()


WIKI = ["Chelsea Piers", "Pier 57", "Pier 40 at Hudson River Park", "Pier 54 (Manhattan)", "Little Island at Pier 55", "Manhattan Cruise Terminal",
        "City Pier A", "Hudson River Park", "Pier 17", "South Street Seaport", "Brooklyn Bridge Park", "Bush Terminal", "Brooklyn Army Terminal",
        "Red Hook Container Terminal", "Stapleton, Staten Island", "Naval Station New York", "St. George Terminal", "Whitehall Terminal",
        "Battery Maritime Building", "Riegelmann Boardwalk", "Canarsie Pier", "Gansevoort Peninsula", "Pier 76", "Intrepid Museum",
        "East River Greenway", "Pier 15 (Manhattan)", "Pier 11/Wall Street", "Pier 35 (Manhattan)", "Battery Park City", "Westway (New York)",
        "West Side Line", "69th Street Transfer Bridge", "Brooklyn Navy Yard", "Brooklyn Cruise Terminal", "South Brooklyn Marine Terminal",
        "Domino Park", "WNYC Transmitter Park", "Gantry Plaza State Park", "Fulton Ferry, Brooklyn", "New York Dock Company",
        "Howland Hook Marine Terminal", "Pier 25 (Hudson River)", "Pier 26 (Hudson River)", "Christopher Street Pier", "Erie Basin (Brooklyn)",
        "Atlantic Basin", "American Veterans Memorial Pier", "Steeplechase Pier", "East River Park", "Stuyvesant Cove Park", "Pier 42 (Manhattan)",
        "Pier 36 (Manhattan)", "Riverside Park South", "Hunters Point South Park", "Bush Terminal Piers Park", "Marine Ocean Terminal at Bayonne",
        "Sunset Park, Brooklyn", "Red Hook, Brooklyn", "Port of New York and New Jersey", "FDR Drive", "Tompkinsville, Staten Island",
        "Brooklyn Heights Promenade", "Pier 1 (Brooklyn Bridge Park)", "Empire Stores", "Greenpoint Terminal Market", "India Street Pier",
        "Newtown Barge Park", "Hudson River Waterfront Walkway", "Piers 92 and 94", "Pier 94", "Pier 97 (Hudson River)", "Pier 86"]


def wiki():
    """plain-text extracts of the Wikipedia articles the dates were read from (CC BY-SA; facts only are used)."""
    import time
    (RAW / "wiki").mkdir(parents=True, exist_ok=True)
    for t in WIKI:
        p = RAW / "wiki" / (re.sub(r"[^A-Za-z0-9]+", "_", t) + ".json")
        if p.exists() and p.stat().st_size > 200 and p.read_text()[:1] == "{":
            continue
        for attempt in range(4):
            x = requests.get("https://en.wikipedia.org/w/api.php", params=dict(action="query", prop="extracts", explaintext=1, redirects=1,
                                                                               format="json", titles=t), headers=UA, timeout=60)
            if x.status_code == 200 and x.text[:1] == "{":
                p.write_text(x.text)
                break
            time.sleep(4 + 4 * attempt)
        time.sleep(1.5)
    for p in sorted((RAW / "wiki").glob("*.json")):
        try:
            pg = list(json.load(open(p))["query"]["pages"].values())[0]
            print(p.name, "|", pg.get("title"), "|", len(pg.get("extract", "")))
        except Exception as e:
            print(p.name, "ERR", str(e)[:50])


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "wiki":
    wiki()
