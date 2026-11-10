"""Stage: OpenHistoricalMap (OHM, CC0) buildings of the map box, normalised for "what stood before".

OHM (https://www.openhistoricalmap.org/, data CC0 1.0) is a volunteer-traced, dated world map. Its Overpass
API (https://overpass-api.openhistoricalmap.org/api/interpreter) is queried in quadtree tiles of at most
MAX_PER_TILE buildings (`out meta geom`), cached under data/raw/ohm/buildings/. Nothing is re-downloaded when
the cache is there; delete data/raw/ohm/ to refresh.

  fetch      Overpass -> data/raw/ohm/buildings/*.json (buildings) and data/raw/ohm/other/*.json (tags of
             everything else in the box: railways, roads, water, land use, places, boundaries)
  build      normalise every building way / multipolygon: dates (ISO / EDTF-ish), placeholder heaps, levels,
             height, source tags, campaign, borough; overlap of every building with today's official
             footprints (data/interim/nyc_footprints_raw.parquet), survivor suspects among the extinct
             -> data/manual/ohm/nyc_buildings.geojson           every building except the two bulk imports
                                                                 (the hand-traced maps and single buildings, and
                                                                 the city-import rows OHM has given an end date)
             -> data/manual/ohm/nyc_buildings_nypl1854.geojson  the import of NYPL's 1854 building footprints
                                                                 (Manhattan to 42nd St), with the volunteers' dates
             -> data/interim/ohm/nyc_buildings_city_import.geojson  OHM's copy of today's NYC Building Footprints
                                                                 (Staten Island, part of the Bronx): not committed,
                                                                 the project has the official file itself
                (same properties in all three; together they are one feature per OHM building of the box)
             -> data/interim/ohm/stats.json, heaps.csv, named.csv, survivors.csv (the numbers in the README)
  survey     count + tag summary of the non-building OHM content -> data/interim/ohm/other_summary.json,
             natural_features.csv
  extras     by-products with geometry, not buildings: data/manual/ohm/extras_water_dated.geojson (OHM's dated
             water, coastline, island, stream and pier features) and extras_lost_structures.geojson (named,
             vanished stadiums, fairgrounds, forts, burial grounds ... that OHM does not tag as building)

Usage:  ../.venv/bin/python ohm_nyc.py [fetch|build|survey|extras|all]      (default: all)

Date rules (README.md in data/manual/ohm/ has the findings):
  start_year / end_year   decimal year of `start_date` / `end_date` (fallback `start_date:edtf` /
                          `end_date:edtf`): 1851 -> 1851.0, 1851-05 -> 1851.333, 1851-05-04 -> 1851.341;
                          a decade ("185X", "1850s") -> its middle (1855.0); a range -> its middle;
                          "~1850", "before 1850", "1850?" -> 1850.0
  start_quality / end_quality (per tag) and date_quality (the weaker of the two that are present):
      dated        a specific year or date
      decade       a decade, a range, an approximate or bounded date
      placeholder  the exact value is shared by more than HEAP_MIN buildings of the same campaign, or by at
                   least 10 and half of it (one date stamped on a whole traced map), and nothing vouches for it
                   (find_heaps: HEAP_DECISIONS, the city-record imports, the successor / record checks)
      none         no tag
Other properties: campaign (the import or normalised source the building belongs to), map_year (year of the
map a traced campaign was drawn from: the building stood then), address, borough, area_m2, overlap_today /
overlap_bin / overlap_year_raw / overlap_iou (today's official footprints under it; null outside the five
boroughs), today (same_outline | built_over | open | no_data), survivor_suspect.
"""
from __future__ import annotations

import csv
import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import LineString, Polygon, mapping
from shapely.ops import polygonize, unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CURRENT_YEAR, INTERIM, MANUAL, NYC_BBOX, RAW, log, session  # noqa: E402

OHM_RAW = RAW / "ohm"
BLD_RAW = OHM_RAW / "buildings"
OTHER_RAW = OHM_RAW / "other"
EXTRA_RAW = OHM_RAW / "extras"
OUT = MANUAL / "ohm"
SCRATCH = INTERIM / "ohm"
OVERPASS = "https://overpass-api.openhistoricalmap.org/api/interpreter"
USER_AGENT = "NYCThroughTime-research/0.1"
FOOTPRINTS = INTERIM / "nyc_footprints_raw.parquet"
TIGER = RAW / "tiger" / "tl_2024_us_county.zip"

MAX_PER_TILE = 9000   # buildings per Overpass request
HEAP_MIN = 50         # an exact date value shared by more buildings of one campaign than this is a heap
NYC_COUNTIES = {"36061": "Manhattan", "36047": "Brooklyn", "36081": "Queens", "36005": "Bronx",
                "36085": "Staten Island"}

# Campaign names of the bulk imports. The 1854 one is NYPL's "New York City Building Footprints to 42nd Street,
# 1854" (https://geodata.library.columbia.edu/catalog/sde-columbia-cul_nyc_nypl_1854_buildings), which OHM
# tags nypl:layer=861, nypl:year=1854.
NYPL_CAMPAIGN = "NYPL building footprints of 1854 (Building Inspector layer 861)"
CITY_IMPORT = "NYC Building Footprints import"
NO_SOURCE = "(no source tag)"

# Heaps that were looked at by hand (README "Heaps"). key: (campaign, "start" | "end", raw value).
# "documented" = the value is a real, sourced event for those buildings and stays `dated`;
# "bound" = a real lower / upper bound stamped on many buildings (still a placeholder for each one);
# everything else over HEAP_MIN is a placeholder.
HEAP_DECISIONS: dict[tuple[str, str, str], tuple[str, str]] = {
    (NYPL_CAMPAIGN, "start", "1853"): (
        "documented", "on the atlas of 1854 and, by the ways' own note, 'not on the 1852 Dripps map' "
                      "-> built 1852-54 (835 of the 867 carry the note)"),
    (NYPL_CAMPAIGN, "start", "1836"): (
        "bound", "the district burned in the Great Fire of 16-17 December 1835 (Wall St - Broad St - Coenties "
                 "Slip - East River): rebuilt from 1836, standing by 1854; a lower bound, not a building date"),
    (NYPL_CAMPAIGN, "start", "1796-02-29"): (
        "placeholder", "the import's own sentinel (fixme: 'added for rendering')"),
    (NYPL_CAMPAIGN, "end", "1920-02-29"): (
        "placeholder", "the import's own sentinel (fixme: 'added for rendering')"),
    (NO_SOURCE, "end", "2012"): (
        "bound", "Staten Island east shore (Oakwood Beach - Midland Beach, 40.554-40.561 N): probably Hurricane "
                 "Sandy, 29 October 2012; read from the location only, not verified -> kept a placeholder"),
    (NO_SOURCE, "end", "2014"): (
        "bound", "same shore: probably the state buy-out demolitions after Sandy; read from the location only, "
                 "not verified -> kept a placeholder"),
}
# Stamps under the heap threshold: (campaign, side, raw value, raw value of the other side) -> placeholder
SMALL_STAMPS = {
    (NO_SOURCE, "start", "1825", "1857"): "Seneca Village: founding year of the settlement (1825) on every "
                                                  "house; the end, 1857, is the real clearance for Central Park",
}


# ------------------------------------------------------------------ fetch
def _post(query: str, timeout=330):
    s = session()
    s.headers["User-Agent"] = USER_AGENT
    for attempt in range(5):
        try:
            r = s.post(OVERPASS, data={"data": query}, timeout=timeout)
        except Exception as e:  # noqa: BLE001
            log(f"ohm: {type(e).__name__} ({attempt + 1}), waiting")
            time.sleep(20 * (attempt + 1))
            continue
        if r.status_code == 200 and '"elements"' in r.text[:3000]:
            try:
                json.loads(r.text)
            except ValueError:
                log("ohm: truncated answer, retrying")
                time.sleep(15)
                continue
            if '"remark"' in r.text[-600:] and "error" in r.text[-600:]:
                log("ohm: runtime error remark: " + r.text[-300:].strip().replace("\n", " "))
                time.sleep(20 * (attempt + 1))
                continue
            return r.text
        log(f"ohm: HTTP {r.status_code} ({attempt + 1}), waiting")
        time.sleep(25 * (attempt + 1))
    raise RuntimeError("Overpass failed: " + query[:120])


def overpass(query: str, path: Path, pause=2.0) -> Path:
    if path.exists() and path.stat().st_size > 100:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    txt = _post(query)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(txt)
    tmp.rename(path)
    log(f"ohm: {path.name} {len(txt) / 1e6:.1f} MB")
    time.sleep(pause)
    return path


def _bb(box):  # (w, s, e, n) -> Overpass (s, w, n, e)
    w, s, e, n = box
    return f"({s:.5f},{w:.5f},{n:.5f},{e:.5f})"


def _name(box):
    return "_".join(f"{v:.5f}" for v in box).replace("-", "m")


def building_tiles() -> list[tuple]:
    """Quadtree over the map box: leaves hold at most MAX_PER_TILE buildings (counts cached)."""
    BLD_RAW.mkdir(parents=True, exist_ok=True)
    cpath = BLD_RAW / "counts.json"
    counts = json.loads(cpath.read_text()) if cpath.exists() else {}
    w0, s0, e0, n0 = NYC_BBOX
    k = 4
    stack = [(w0 + (e0 - w0) * i / k, s0 + (n0 - s0) * j / k, w0 + (e0 - w0) * (i + 1) / k,
              s0 + (n0 - s0) * (j + 1) / k) for i in range(k) for j in range(k)]
    leaves = []
    while stack:
        box = stack.pop()
        key = _name(box)
        if key not in counts:
            txt = _post(f'[out:json][timeout:120];(way["building"]{_bb(box)};relation["building"]{_bb(box)};);out count;')
            counts[key] = int(json.loads(txt)["elements"][0]["tags"]["total"])
            cpath.write_text(json.dumps(counts, indent=0))
            time.sleep(1.0)
        n = counts[key]
        if n == 0:
            continue
        w, s, e, nn = box
        if n > MAX_PER_TILE and (e - w) > 0.004:
            mx, my = (w + e) / 2, (s + nn) / 2
            stack += [(w, s, mx, my), (mx, s, e, my), (w, my, mx, nn), (mx, my, e, nn)]
        else:
            leaves.append(box)
    return sorted(leaves)


def fetch():
    leaves = building_tiles()
    log(f"ohm: {len(leaves)} building tiles")
    for box in leaves:
        overpass(f'[out:json][timeout:300][maxsize:1073741824];(way["building"]{_bb(box)};relation["building"]{_bb(box)};);out meta geom;',
                 BLD_RAW / f"bld_{_name(box)}.json")
    # everything else: tags only (count + tag summary; nothing of it is imported)
    w0, s0, e0, n0 = NYC_BBOX
    mx, my = (w0 + e0) / 2, (s0 + n0) / 2
    for box in [(w0, s0, mx, my), (mx, s0, e0, my), (w0, my, mx, n0), (mx, my, e0, n0)]:
        overpass(f'[out:json][timeout:300];(way[!"building"]{_bb(box)};relation[!"building"]{_bb(box)};);out tags center;',
                 OTHER_RAW / f"other_{_name(box)}.json")
    overpass(f'[out:json][timeout:300];node[~"^(place|start_date|end_date)$"~"."]{_bb(NYC_BBOX)};out tags;',
             OTHER_RAW / "nodes_place_or_dated.json")
    # two small extras with geometry (see extras()): dated water / shore features, and named structures that
    # are gone but are not tagged building (stadiums, fairgrounds, forts, burial grounds ...)
    b = _bb(NYC_BBOX)
    d = '[~"^(start_date|end_date)$"~"."]'
    nat = '["natural"~"^(water|coastline|bay|wetland|shoal|beach)$"]'
    overpass(f'[out:json][timeout:300];(way{nat}{d}{b};relation{nat}{d}{b};way["waterway"]{d}{b};'
             f'way["place"~"^(island|islet)$"]{b};relation["place"~"^(island|islet)$"]{b};'
             f'way["man_made"="pier"]{d}{b};);out meta geom;', EXTRA_RAW / "water_dated.json")
    k = '[~"^(leisure|man_made|tourism|amenity|historic|aeroway|military|barrier|landuse)$"~"."]'
    overpass(f'[out:json][timeout:300];(way["end_date"]["name"][!"building"]{k}{b};'
             f'relation["end_date"]["name"][!"building"]{k}{b};);out meta geom;', EXTRA_RAW / "lost_structures.json")


# ------------------------------------------------------------------ geometry
def _line(geom):
    return [(p["lon"], p["lat"]) for p in geom if p]


def _rings_to_polys(outer_lines, inner_lines):
    def polys(lines):
        ls = [LineString(c) for c in lines if len(c) >= 2]
        return list(polygonize(unary_union(ls))) if ls else []
    outers, inners = polys(outer_lines), polys(inner_lines)
    if not outers:
        return None
    parts = []
    for o in outers:
        holes = [i for i in inners if o.contains(i.representative_point())]
        parts.append(o.difference(unary_union(holes)) if holes else o)
    return unary_union(parts)


def element_polygon(e):
    """Polygon / MultiPolygon of an Overpass `out geom` building way or multipolygon relation, or None."""
    g = None
    if e["type"] == "way":
        c = _line(e.get("geometry", []))
        if len(c) >= 4 and c[0] == c[-1]:
            g = Polygon(c)
    elif e["type"] == "relation":
        outer, inner = [], []
        for m in e.get("members", []):
            if m.get("type") != "way" or not m.get("geometry"):
                continue
            c = _line(m["geometry"])
            if len(c) >= 2:
                (inner if m.get("role") == "inner" else outer).append(c)
        g = _rings_to_polys(outer, inner)
    if g is None or g.is_empty:
        return None
    if not g.is_valid:
        g = shapely.make_valid(g)
    if g.geom_type == "GeometryCollection":
        ps = [p for p in g.geoms if p.geom_type in ("Polygon", "MultiPolygon")]
        g = unary_union(ps) if ps else None
    if g is None or g.is_empty or g.geom_type not in ("Polygon", "MultiPolygon"):
        return None
    return g


# ------------------------------------------------------------------ dates
_DAYS = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
_ISO = re.compile(r"^(-?\d{1,4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?$")
_DECADE = re.compile(r"^(\d{3})(?:[xXuU?]|0s|0's)$")
_CENTURY = re.compile(r"^(?:c(\d{1,2})|(\d{1,2})(?:st|nd|rd|th) century)$", re.I)
_APPROX = re.compile(r"^(?:~|c\.?\s*|ca\.?\s*|circa\s+|about\s+|before\s+|after\s+|early\s+|late\s+|mid\s+|\.\.|/)?"
                     r"(-?\d{4})(?:-\d{1,2})?(?:-\d{1,2})?(?:~|\?|%|\.\.|/|s)?$", re.I)
_RANGE = re.compile(r"^(-?\d{4})(?:-\d{1,2}){0,2}\s*(?:/|\.\.|\s-\s|–|-)\s*(-?\d{4})(?:-\d{1,2}){0,2}$")


def parse_date(raw):
    """OHM date string -> (decimal year | None, 'dated' | 'decade' | 'none')."""
    if raw is None:
        return None, "none"
    s = str(raw).strip()
    if not s:
        return None, "none"
    m = _ISO.match(s)
    if m:
        y = float(m.group(1))
        mo, d = m.group(2), m.group(3)
        if mo and 1 <= int(mo) <= 12:
            doy = _DAYS[int(mo) - 1] + ((min(int(d), 31) - 1) if d else 0)
            y += doy / 365.25
        if y < 1000 or y > 2100:
            return None, "none"
        return round(y, 3), "dated"
    m = _DECADE.match(s)
    if m:
        return float(m.group(1)) * 10 + 5.0, "decade"
    m = _CENTURY.match(s)
    if m:
        c = int(m.group(1) or m.group(2))
        return (c - 1) * 100 + 50.0, "decade"
    m = _RANGE.match(s)
    if m and int(m.group(2)) >= int(m.group(1)):
        return round((int(m.group(1)) + int(m.group(2))) / 2.0, 1), "decade"
    m = _APPROX.match(s)
    if m:
        return float(m.group(1)), "decade"
    m = re.search(r"(?<!\d)(\d{4})(?!\d)", s)
    if m:
        return float(m.group(1)), "decade"
    return None, "none"


def _num(v):
    if v is None:
        return None
    m = re.match(r"^\s*(-?\d+(?:[.,]\d+)?)\s*(m|ft|'|feet)?\s*$", str(v))
    if not m:
        return None
    x = float(m.group(1).replace(",", "."))
    if m.group(2) in ("ft", "'", "feet"):
        x *= 0.3048
    return round(x, 2)


# mapwarper.net map ids met in the box -> (label, year the map shows); from the ways' own source:name tags
MAPWARPER = {
    "4625": ("Castello Plan, New Amsterdam in 1660 (Adams-Stokes redraft of 1916; mapwarper 4625)", 1660),
    "49065": ("Survey of Manhattan 1728 (mapwarper 49065)", 1728),
    "11641": ("Grim, Part of New York in 1742 (mapwarper 11641)", 1742),
    "57378": ("Maerschalck, Plan of the City of New York 1755 (mapwarper 57378)", 1755),
    "15936": ("NYC 1776 (mapwarper 15936)", 1776),
    "45035": ("Bromley Land Book 1930 (mapwarper 45035)", 1930),
    "44942": ("Bromley Land Book 1930 (mapwarper 44942)", 1930),
    "44952": ("Bromley Land Book 1930 (mapwarper 44952)", 1930),
    "45043": ("Bromley Land Book 1930 (mapwarper 45043)", 1930),
    "41751": ("Bromley Land Book 1927 (mapwarper 41751)", 1927),
    "30668": ("Sanborn 1894 Manhattan vol. 1 plate 3 (mapwarper 30668)", 1894),
}
_MAPWORD = re.compile(r"sanborn|bromley|perris|dripps|land book|atlas|\bmap\b|\bplan\b|survey|robinson|viele|ratzer", re.I)


def campaign_of(t: dict) -> str:
    """The mapping campaign a building belongs to: a bulk import, else its source tag, normalised
    (plate / volume numbers and secondary sources dropped so one traced atlas is one campaign)."""
    if "nypl:layer" in t or "bkln:integer" in t:
        return NYPL_CAMPAIGN
    src = (t.get("source") or "").strip()
    if t.get("dataset"):
        return f"{CITY_IMPORT} ({t['dataset']})"
    if "doitt_id" in t or "cnstrct_yr" in t:
        return f"{CITY_IMPORT} (Bronx, cnstrct_yr / doitt_id attributes, no source tag)"
    if "data.cityofnewyork.us" in src:
        return f"{CITY_IMPORT} (other)"
    s = (src or t.get("source:name") or t.get("source:url") or t.get("source:1") or "").strip()
    if not s:
        return NO_SOURCE
    m = re.search(r"mapwarper\.net/maps/(\d+)", s)
    if m:
        return MAPWARPER.get(m.group(1), (f"mapwarper.net/maps/{m.group(1)}", None))[0]
    if re.search(r"(wikipedia|wikimedia)\.org", s):
        return "wikipedia / wikimedia (per-building article or image)"
    s = s.split(";")[0]
    s = re.sub(r"#.*$", "", s)
    s = re.sub(r"^https?://(www\.)?", "", s).rstrip("/")
    s = re.sub(r",?\s*\(?(?:Manhattan\s+)?(?:Vol(?:ume)?\.?\s*\d+|V\d+)(?:, southern half)?\)?", "", s)
    s = re.sub(r",?\s*plate\s*(?:no\.?\s*)?\d+", "", s, flags=re.I)
    s = re.sub(r",\s*Manhattan\s*$", "", re.sub(r"\s+", " ", s).strip(" ,"))
    return s[:90] or NO_SOURCE


def map_year_of(campaign: str, t: dict):
    """Year of the map a traced campaign was drawn from (the building stood then), or None."""
    if campaign == NYPL_CAMPAIGN:
        return 1854
    for label, y in MAPWARPER.values():
        if campaign == label:
            return y
    if _MAPWORD.search(campaign):
        m = re.search(r"(?<!\d)(1[6-9]\d\d|20[0-2]\d)(?!\d)", campaign)
        if m:
            return int(m.group(1))
    return None


# ------------------------------------------------------------------ build
def load_buildings():
    """Every building way / multipolygon of the cached tiles, once each: list of dicts + array of geometries."""
    rows, geoms, seen = [], [], set()
    skipped = Counter()
    for f in sorted(BLD_RAW.glob("bld_*.json")):
        for e in json.load(open(f))["elements"]:
            key = f"{e['type']}/{e['id']}"
            if key in seen or e["type"] not in ("way", "relation"):
                continue
            seen.add(key)
            g = element_polygon(e)
            if g is None:
                skipped["no polygon (open way / broken relation)"] += 1
                continue
            t = e.get("tags", {})
            rows.append({"ohm_id": key, "tags": t, "version": e.get("version"), "changeset": e.get("changeset"),
                         "user": e.get("user"), "timestamp": e.get("timestamp")})
            geoms.append(g)
    log(f"ohm: {len(rows)} building polygons; skipped {dict(skipped)}")
    return rows, np.array(geoms, dtype=object), skipped


def assign_borough(pts):
    """Borough (or the county outside the city) of each point, from TIGER counties."""
    import geopandas as gpd
    c = gpd.read_file(f"zip://{TIGER}", bbox=NYC_BBOX, columns=["GEOID", "NAME", "STATEFP"])
    st = {"36": "NY", "34": "NJ", "09": "CT"}
    out = np.array(["(open water / outside any county)"] * len(pts), dtype=object)
    tree = shapely.STRtree(c.geometry.values)
    i, j = tree.query(pts, predicate="within")
    for a, b in zip(i, j):
        geoid = c.GEOID.values[b]
        out[a] = NYC_COUNTIES.get(geoid, f"outside NYC: {c.NAME.values[b]} County, {st.get(c.STATEFP.values[b], '')}")
    return out


def overlaps_today(geoms):
    """For every geometry (lon/lat): share of its area under today's official footprints, and the largest
    overlapping footprint (BIN, year_raw, IoU, share of the OHM building it covers). Footprints are read in
    0.04-degree windows. Area ratios are taken in lon/lat (an affine stretch of metres at building scale,
    so the ratios are unchanged)."""
    import duckdb
    n = len(geoms)
    frac = np.zeros(n)
    best_bin = np.full(n, None, dtype=object)
    best_year = np.full(n, np.nan)
    best_iou = np.zeros(n)
    best_share = np.zeros(n)
    g = geoms
    b = shapely.bounds(g)
    cx, cy = (b[:, 0] + b[:, 2]) / 2, (b[:, 1] + b[:, 3]) / 2
    cell = 0.04
    ci, cj = np.floor(cx / cell).astype(int), np.floor(cy / cell).astype(int)
    con = duckdb.connect()
    con.execute("SET memory_limit='1GB'")
    for key in sorted(set(zip(ci.tolist(), cj.tolist()))):
        sel = np.nonzero((ci == key[0]) & (cj == key[1]))[0]
        w, s, e, nn = b[sel, 0].min(), b[sel, 1].min(), b[sel, 2].max(), b[sel, 3].max()
        m = 0.004  # footprints are selected by centroid; 0.004 deg (~340 m) covers the largest buildings
        fp = con.execute(
            f"SELECT bin, year_raw, geometry FROM read_parquet('{FOOTPRINTS}') "
            f"WHERE lon BETWEEN {w - m} AND {e + m} AND lat BETWEEN {s - m} AND {nn + m}").fetchall()
        if not fp:
            continue
        fg = shapely.from_wkb([bytes(r[2]) for r in fp])
        bad = ~shapely.is_valid(fg)
        if bad.any():
            fg[bad] = shapely.make_valid(fg[bad])
        fbin = np.array([r[0] for r in fp], dtype=object)
        fyear = np.array([np.nan if r[1] is None else float(r[1]) for r in fp])
        tree = shapely.STRtree(fg)
        a, c = tree.query(g[sel], predicate="intersects")
        if not len(a):
            continue
        inter = shapely.area(shapely.intersection(g[sel][a], fg[c]))
        ga = shapely.area(g[sel])
        fa = shapely.area(fg)
        order = np.lexsort((-inter, a))
        a, c, inter = a[order], c[order], inter[order]
        tot = np.zeros(len(sel))
        np.add.at(tot, a, inter)
        frac[sel] = np.minimum(tot / np.maximum(ga, 1e-15), 1.0)
        first = np.r_[True, a[1:] != a[:-1]]
        ai, cc, ii = a[first], c[first], inter[first]
        keep = ii > 0
        ai, cc, ii = ai[keep], cc[keep], ii[keep]
        best_bin[sel[ai]] = fbin[cc]
        best_year[sel[ai]] = fyear[cc]
        best_iou[sel[ai]] = ii / np.maximum(ga[ai] + fa[cc] - ii, 1e-15)
        best_share[sel[ai]] = ii / np.maximum(ga[ai], 1e-15)
    return frac, best_bin, best_year, best_iou, best_share


def _write_geojson(path: Path, feats_iter, name: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(path, "w") as f:
        f.write('{"type":"FeatureCollection","name":"%s","crs":{"type":"name","properties":{"name":'
                '"urn:ogc:def:crs:OGC:1.3:CRS84"}},\n"features":[\n' % name)
        for props, g in feats_iter:
            f.write(("" if n == 0 else ",\n") + json.dumps(
                {"type": "Feature", "properties": props, "geometry": mapping(g)},
                separators=(",", ":"), ensure_ascii=False))
            n += 1
        f.write("\n]}\n")
    log(f"ohm: wrote {path} ({n} features, {path.stat().st_size / 1e6:.1f} MB)")
    return n


def _rounded(geoms, grid=1e-6):
    """Coordinates rounded to 6 decimals (0.1 m); outlines the rounding breaks are repaired, polygons kept."""
    rg = shapely.set_precision(geoms, grid, mode="pointwise")
    for i in np.nonzero(~shapely.is_valid(rg))[0]:
        g = shapely.make_valid(rg[i])
        if g.geom_type == "GeometryCollection":
            ps = [p for p in g.geoms if p.geom_type in ("Polygon", "MultiPolygon")]
            g = unary_union(ps) if ps else geoms[i]
        rg[i] = g if g.geom_type in ("Polygon", "MultiPolygon") and not g.is_empty else geoms[i]
    return rg


def decade(y):
    return None if y is None else int(np.floor(y / 10.0) * 10)


def find_heaps(rows):
    """Mark placeholder dates. A heap is an exact raw value that more than HEAP_MIN buildings of one campaign
    share, or that at least 10 buildings and half of a campaign share (one date stamped on a traced map).
    Exceptions: the city-record imports' start years (one assessor year per building, not a stamp); named or
    wikidata-tagged buildings of the no-source group (mapped one by one); heaps HEAP_DECISIONS lists as a
    documented event; end heaps that the successors on the ground confirm (`successor_consistent`: at least
    20 of the heap's buildings lie under a footprint standing today with a recorded year, and for 70 % of
    them that year is within [end - 1, end + 5] - the lot was rebuilt at that date); start heaps that the
    city's records confirm (`record_consistent`: at least 20 of them have the same outline as a footprint
    standing today and 70 % of those carry the same year, +-1)."""
    heaps = []
    for side in ("start", "end"):
        groups = defaultdict(list)
        camp_n = Counter()
        for i, r in enumerate(rows):
            v = r[f"{side}_raw"]
            if not v:
                continue
            camp_n[r["campaign"]] += 1
            if r["campaign"] == NO_SOURCE and (r["tags"].get("name") or r["tags"].get("wikidata")):
                continue
            groups[(r["campaign"], v)].append(i)
        for (camp, val), idx in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            cnt = len(idx)
            dominant = cnt >= 10 and cnt >= 0.5 * camp_n[camp] and camp != NO_SOURCE
            if cnt <= HEAP_MIN and not dominant:
                continue
            verdict, note = HEAP_DECISIONS.get((camp, side, val), ("placeholder", ""))
            if camp.startswith(CITY_IMPORT) and side == "start":
                verdict, note = "record", "city record year per building (as year_raw); not a stamp"
            succ = ""
            decided = (camp, side, val) in HEAP_DECISIONS or verdict == "record"
            if side == "end":
                d = [rows[i]["overlap_year_raw"] - rows[i]["end_year"] for i in idx
                     if rows[i]["end_year"] is not None and (rows[i]["overlap_today"] or 0) >= 0.3
                     and rows[i]["overlap_year_raw"] is not None]
                if d:
                    ok = float(np.mean([(-1 <= x <= 5) for x in d]))
                    succ = f"{len(d)} under a dated footprint, {100 * ok:.0f} % built within [end-1, end+5]"
                    if len(d) >= 20 and ok >= 0.7 and not decided:
                        verdict, note = "successor_consistent", ("the buildings standing there today were built "
                                                                 "at this date: gone by then (an upper bound, "
                                                                 "confirmed on the ground)")
            else:
                d = [rows[i]["overlap_year_raw"] - rows[i]["start_year"] for i in idx
                     if rows[i]["start_year"] is not None and rows[i]["today"] == "same_outline"
                     and rows[i]["overlap_year_raw"] is not None]
                if d:
                    ok = float(np.mean([abs(x) <= 1 for x in d]))
                    succ = f"{len(d)} with the same outline today, {100 * ok:.0f} % with that recorded year (+-1)"
                    if len(d) >= 20 and ok >= 0.7 and not decided:
                        verdict, note = "record_consistent", "the city records the same year for the same outline"
            heaps.append({"campaign": camp, "side": side, "value": val, "buildings": cnt,
                          "campaign_with_date": camp_n[camp], "verdict": verdict, "successors": succ, "note": note})
            if verdict in ("placeholder", "bound"):
                for i in idx:
                    rows[i][f"{side}_quality"] = "placeholder"
    for (camp, side, val, other), note in SMALL_STAMPS.items():
        o = "end" if side == "start" else "start"
        idx = [i for i, r in enumerate(rows) if r["campaign"] == camp and r[f"{side}_raw"] == val
               and r[f"{o}_raw"] == other]
        for i in idx:
            rows[i][f"{side}_quality"] = "placeholder"
        heaps.append({"campaign": camp, "side": side, "value": val, "buildings": len(idx),
                      "campaign_with_date": "", "verdict": "placeholder", "successors": "", "note": note})
    return heaps


def build():
    import pyproj
    rows, geoms, skipped = load_buildings()
    n = len(rows)
    # ---- attributes
    for r in rows:
        t = r["tags"]
        r["start_raw"] = t.get("start_date") or t.get("start_date:edtf")
        r["end_raw"] = t.get("end_date") or t.get("end_date:edtf")
        r["start_year"], r["start_quality"] = parse_date(r["start_raw"])
        r["end_year"], r["end_quality"] = parse_date(r["end_raw"])
        r["campaign"] = campaign_of(t)
        r["map_year"] = map_year_of(r["campaign"], t)
        r["extinct"] = r["end_year"] is not None and r["end_year"] < CURRENT_YEAR
    # ---- borough, area
    pts = shapely.point_on_surface(geoms)
    boro = assign_borough(pts)
    tf = pyproj.Transformer.from_crs(4326, 32618, always_xy=True)
    area = shapely.area(shapely.transform(geoms, lambda xy: np.column_stack(tf.transform(xy[:, 0], xy[:, 1]))))
    # ---- overlap with today's official footprints (every building; survivor_suspect only for the extinct)
    frac, obin, oyear, oiou, oshare = overlaps_today(geoms)
    for i, r in enumerate(rows):
        r["overlap_today"] = round(float(frac[i]), 3)
        r["overlap_bin"] = None if obin[i] is None else str(int(obin[i]))
        yr = oyear[i]
        r["overlap_year_raw"] = None if not np.isfinite(yr) or yr <= 0 else int(yr)
        r["overlap_iou"] = round(float(oiou[i]), 3)
        # same outline: the largest footprint under it has IoU >= 0.5, or covers >= 70 % of the OHM building
        # with IoU >= 0.35 (an outline redrawn from another survey)
        same = oiou[i] >= 0.5 or (oshare[i] >= 0.7 and oiou[i] >= 0.35)
        r["today"] = "same_outline" if same else ("built_over" if frac[i] >= 0.3 else "open")
        # survivor suspect: OHM says it is gone, but a footprint of about the same outline stands today whose
        # recorded year is earlier than the year OHM says the building went
        r["survivor_suspect"] = bool(r["extinct"] and same and r["overlap_year_raw"] is not None
                                     and r["overlap_year_raw"] < r["end_year"])
    for i, r in enumerate(rows):  # the official footprints cover the five boroughs only
        if boro[i] not in NYC_COUNTIES.values():
            r.update(overlap_today=None, overlap_bin=None, overlap_year_raw=None, overlap_iou=None,
                     today="no_data", survivor_suspect=False)
    # ---- placeholder heaps
    heaps = find_heaps(rows)
    rank = {"placeholder": 0, "decade": 1, "dated": 2}
    for r in rows:
        q = [x for x in (r["start_quality"], r["end_quality"]) if x != "none"]
        r["date_quality"] = min(q, key=rank.get) if q else "none"

    def props(i):
        r = rows[i]
        t = r["tags"]
        src = " | ".join(f"{k}={t[k]}" for k in ("source", "source:name", "source:url") if t.get(k))
        addr = " ".join(x for x in (t.get("addr:housenumber"), t.get("addr:street")) if x)
        return {
            "ohm_id": r["ohm_id"], "name": t.get("name"),
            "start_year": r["start_year"], "end_year": r["end_year"],
            "start_raw": r["start_raw"], "end_raw": r["end_raw"],
            "date_quality": r["date_quality"], "start_quality": r["start_quality"], "end_quality": r["end_quality"],
            "levels": _num(t.get("building:levels")), "height_m": _num(t.get("height")),
            "building": t.get("building"), "source_tag": src or None,
            "wikidata": t.get("wikidata"), "wikipedia": t.get("wikipedia"),
            "extinct": r["extinct"],
            "campaign": r["campaign"], "map_year": r["map_year"], "address": addr or None,
            "borough": boro[i], "area_m2": round(float(area[i]), 1),
            "overlap_today": r["overlap_today"], "overlap_bin": r["overlap_bin"],
            "overlap_year_raw": r["overlap_year_raw"], "overlap_iou": r["overlap_iou"],
            "today": r["today"], "survivor_suspect": r["survivor_suspect"],
        }

    rg = _rounded(geoms)
    is_nypl = np.array([r["campaign"] == NYPL_CAMPAIGN for r in rows])
    is_city = np.array([r["campaign"].startswith(CITY_IMPORT) and not r["extinct"] for r in rows])
    main = np.nonzero(~is_nypl & ~is_city)[0]
    nypl = np.nonzero(is_nypl)[0]
    city = np.nonzero(is_city)[0]
    _write_geojson(OUT / "nyc_buildings.geojson", ((props(i), rg[i]) for i in main), "ohm_nyc_buildings")
    _write_geojson(OUT / "nyc_buildings_nypl1854.geojson", ((props(i), rg[i]) for i in nypl),
                   "ohm_nyc_buildings_nypl1854")
    SCRATCH.mkdir(parents=True, exist_ok=True)
    _write_geojson(SCRATCH / "nyc_buildings_city_import.geojson", ((props(i), rg[i]) for i in city),
                   "ohm_nyc_buildings_city_import")
    for old in (OUT / "nyc_buildings_nypl_import.geojson",):
        if old.exists():
            old.unlink()

    # ---- numbers for the README
    with open(SCRATCH / "heaps.csv", "w", newline="") as f:
        wri = csv.DictWriter(f, fieldnames=list(heaps[0].keys()))
        wri.writeheader()
        wri.writerows(heaps)

    def cnt(keyf, sel):
        c = Counter(keyf(i) for i in sel)
        return dict(sorted(c.items(), key=lambda kv: (-kv[1], str(kv[0]))))

    def dec(field, sel, q=None):
        c = Counter(decade(rows[i][f"{field}_year"]) for i in sel
                    if rows[i][f"{field}_year"] is not None and (q is None or rows[i][f"{field}_quality"] in q))
        return {str(k): v for k, v in sorted(c.items())}

    def block(sel):
        ex = [i for i in sel if rows[i]["extinct"]]
        return {
            "n": len(sel), "extinct": len(ex),
            "date_quality": cnt(lambda i: rows[i]["date_quality"], sel),
            "start_quality": cnt(lambda i: rows[i]["start_quality"], sel),
            "end_quality": cnt(lambda i: rows[i]["end_quality"], sel),
            "extinct_end_dated": sum(rows[i]["end_quality"] == "dated" for i in ex),
            "extinct_both_dated": sum(rows[i]["end_quality"] == "dated" and rows[i]["start_quality"] == "dated" for i in ex),
            "borough": cnt(lambda i: boro[i], sel), "borough_extinct": cnt(lambda i: boro[i], ex),
            "start_decade": dec("start", sel), "end_decade": dec("end", sel),
            "start_decade_dated": dec("start", sel, ("dated",)), "end_decade_dated": dec("end", sel, ("dated",)),
            "today": cnt(lambda i: rows[i]["today"], sel), "today_extinct": cnt(lambda i: rows[i]["today"], ex),
            "today_no_end": cnt(lambda i: rows[i]["today"], [i for i in sel if rows[i]["end_year"] is None]),
            "survivor_suspect": sum(rows[i]["survivor_suspect"] for i in sel),
            "named": sum(bool(rows[i]["tags"].get("name")) for i in sel),
            "wikidata": sum(bool(rows[i]["tags"].get("wikidata")) for i in sel),
            "levels": sum(bool(rows[i]["tags"].get("building:levels")) for i in sel),
            "height": sum(bool(rows[i]["tags"].get("height")) for i in sel),
        }

    by_camp = defaultdict(list)
    for i, r in enumerate(rows):
        by_camp[r["campaign"]].append(i)
    camps = {}
    for k, sel in sorted(by_camp.items(), key=lambda kv: -len(kv[1])):
        ids = [int(rows[i]["ohm_id"].split("/")[1]) for i in sel]
        ex = [i for i in sel if rows[i]["extinct"]]
        camps[k] = {
            "n": len(sel), "extinct": len(ex), "map_year": rows[sel[0]]["map_year"],
            "start_quality": cnt(lambda i: rows[i]["start_quality"], sel),
            "end_quality": cnt(lambda i: rows[i]["end_quality"], sel),
            "start_top": dict(Counter(rows[i]["start_raw"] for i in sel).most_common(4)),
            "end_top": dict(Counter(rows[i]["end_raw"] for i in sel).most_common(4)),
            "today": cnt(lambda i: rows[i]["today"], sel),
            "survivor_suspect": sum(rows[i]["survivor_suspect"] for i in sel),
            "named": sum(bool(rows[i]["tags"].get("name")) for i in sel),
            "borough": dict(list(cnt(lambda i: boro[i], sel).items())[:3]),
            "id_min": min(ids), "id_max": max(ids),
            "last_editors": dict(Counter(rows[i]["user"] for i in sel).most_common(3)),
            "last_edit_years": dict(sorted(Counter((rows[i]["timestamp"] or "")[:4] for i in sel).items())),
        }
    stats = {
        "fetched": time.strftime("%Y-%m-%d", time.gmtime(max(f.stat().st_mtime for f in BLD_RAW.glob("bld_*.json")))),
        "ways": sum(r["ohm_id"].startswith("way") for r in rows),
        "relations": sum(r["ohm_id"].startswith("rel") for r in rows), "skipped": dict(skipped),
        "files": {"nyc_buildings.geojson": len(main), "nyc_buildings_nypl1854.geojson": len(nypl),
                  "interim/nyc_buildings_city_import.geojson": len(city)},
        "all": block(range(n)), "main_file": block(main), "nypl1854_file": block(nypl), "city_import_file": block(city),
        "building_tag": dict(list(cnt(lambda i: rows[i]["tags"].get("building"), range(n)).items())[:25]),
        "campaigns": camps,
    }
    (SCRATCH / "stats.json").write_text(json.dumps(stats, indent=1, ensure_ascii=False))
    cols = ["ohm_id", "name", "start_raw", "end_raw", "start_quality", "end_quality", "extinct", "building", "levels",
            "height", "wikidata", "wikipedia", "campaign", "borough", "area_m2", "today", "overlap_today",
            "overlap_iou", "overlap_bin", "overlap_year_raw", "survivor_suspect", "lon", "lat"]

    def line(i):
        r, t = rows[i], rows[i]["tags"]
        return [r["ohm_id"], t.get("name"), r["start_raw"], r["end_raw"], r["start_quality"], r["end_quality"],
                r["extinct"], t.get("building"), t.get("building:levels"), t.get("height"), t.get("wikidata"),
                t.get("wikipedia"), r["campaign"], boro[i], round(float(area[i])), r["today"], r["overlap_today"],
                r["overlap_iou"], r["overlap_bin"], r["overlap_year_raw"], r["survivor_suspect"],
                round(pts[i].x, 6), round(pts[i].y, 6)]
    for fn, sel in (("named.csv", [i for i, r in enumerate(rows) if r["tags"].get("name") or r["tags"].get("wikidata")]),
                    ("survivors.csv", [i for i, r in enumerate(rows) if r["survivor_suspect"]])):
        with open(SCRATCH / fn, "w", newline="") as f:
            wri = csv.writer(f)
            wri.writerow(cols)
            wri.writerows(line(i) for i in sel)
    a = stats["all"]
    log(f"ohm: {n} buildings, {a['extinct']} extinct, quality {a['date_quality']}, "
        f"survivor suspects {a['survivor_suspect']}")
    return stats


# ------------------------------------------------------------------ survey of the rest
SURVEY_KEYS = ("railway", "highway", "natural", "waterway", "water", "landuse", "leisure", "place", "boundary",
               "man_made", "historic", "amenity", "barrier", "route", "aeroway", "military", "bridge", "tunnel",
               "building:part", "power", "shop", "tourism")


def survey():
    els = {}
    for f in sorted(OTHER_RAW.glob("*.json")):
        for e in json.load(open(f))["elements"]:
            els[(e["type"], e["id"])] = e
    out = {"elements": len(els), "by_type": dict(Counter(k[0] for k in els))}
    w0, s0, e0, n0 = NYC_BBOX
    summ = {}
    for key in SURVEY_KEYS:
        sub = [e for e in els.values() if key in e.get("tags", {})]
        if not sub:
            continue
        tg = [e["tags"] for e in sub]
        st = [parse_date(t.get("start_date") or t.get("start_date:edtf")) for t in tg]
        en = [parse_date(t.get("end_date") or t.get("end_date:edtf")) for t in tg]
        sy = [y for y, _ in st if y is not None]
        ey = [y for y, _ in en if y is not None]
        summ[key] = {
            "n": len(sub), "by_type": dict(Counter(e["type"] for e in sub)),
            "with_start": len(sy), "with_end": len(ey),
            "with_both": sum(1 for a, b in zip(st, en) if a[0] is not None and b[0] is not None),
            "ended_before_today": sum(1 for y in ey if y < CURRENT_YEAR),
            "values": dict(Counter(t[key] for t in tg).most_common(14)),
            "sources": dict(Counter(campaign_of(t) for t in tg).most_common(8)),
            "start_raw_top": dict(Counter(t.get("start_date") for t in tg if t.get("start_date")).most_common(8)),
            "end_raw_top": dict(Counter(t.get("end_date") for t in tg if t.get("end_date")).most_common(8)),
            "start_century": {str(k): v for k, v in sorted(Counter(int(y // 100 * 100) for y in sy).items())},
            "end_century": {str(k): v for k, v in sorted(Counter(int(y // 100 * 100) for y in ey).items())},
            "named": sum(1 for t in tg if t.get("name")),
            "names_sample": [t["name"] for t in tg if t.get("name")][:12],
        }
    out["keys"] = summ
    SCRATCH.mkdir(parents=True, exist_ok=True)
    (SCRATCH / "other_summary.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    # natural / water / coastline features one by one (the shoreline question)
    with open(SCRATCH / "natural_features.csv", "w", newline="") as f:
        wri = csv.writer(f)
        wri.writerow(["ohm_id", "natural", "water", "waterway", "place", "landuse", "name", "start_date", "end_date",
                      "source", "lon", "lat"])
        for (typ, i), e in sorted(els.items()):
            t = e.get("tags", {})
            if not any(k in t for k in ("natural", "waterway", "water")) and t.get("place") not in ("island", "islet") \
                    and t.get("landuse") not in ("landfill", "reservoir", "basin"):
                continue
            c = e.get("center") or {}
            wri.writerow([f"{typ}/{i}", t.get("natural"), t.get("water"), t.get("waterway"), t.get("place"),
                          t.get("landuse"), t.get("name"), t.get("start_date"), t.get("end_date"),
                          campaign_of(t), c.get("lon"), c.get("lat")])
    log(f"ohm: survey of {len(els)} non-building elements -> {SCRATCH / 'other_summary.json'}")
    return out


# ------------------------------------------------------------------ extras (not buildings)
KIND_KEYS = ("natural", "water", "waterway", "place", "leisure", "man_made", "tourism", "amenity", "historic",
             "aeroway", "military", "barrier", "landuse")


def _any_geometry(e):
    g = element_polygon(e)
    if g is not None:
        return g
    if e["type"] == "way":
        c = _line(e.get("geometry", []))
        return LineString(c) if len(c) >= 2 else None
    lines = [LineString(_line(m["geometry"])) for m in e.get("members", [])
             if m.get("type") == "way" and m.get("geometry") and len(m["geometry"]) >= 2]
    return unary_union(lines) if lines else None


def extras():
    """Two small by-products, outside the building files: OHM's dated water / shore features of the box and
    its named, vanished structures that are not tagged building. Dates are parsed as for buildings; a raw
    value shared by more than HEAP_MIN features of a file is marked placeholder."""
    for raw, out, name in ((EXTRA_RAW / "water_dated.json", OUT / "extras_water_dated.geojson", "ohm_nyc_water_dated"),
                           (EXTRA_RAW / "lost_structures.json", OUT / "extras_lost_structures.geojson",
                            "ohm_nyc_lost_structures")):
        if not raw.exists():
            log(f"ohm: {raw.name} missing (run fetch)")
            continue
        feats = []
        for e in json.load(open(raw))["elements"]:
            if e["type"] not in ("way", "relation"):
                continue
            g = _any_geometry(e)
            if g is None or g.is_empty:
                continue
            t = e.get("tags", {})
            sr, er = t.get("start_date") or t.get("start_date:edtf"), t.get("end_date") or t.get("end_date:edtf")
            sy, sq = parse_date(sr)
            ey, eq = parse_date(er)
            feats.append(({
                "ohm_id": f"{e['type']}/{e['id']}", "name": t.get("name"),
                "kind": "; ".join(f"{k}={t[k]}" for k in KIND_KEYS if k in t),
                "start_year": sy, "end_year": ey, "start_raw": sr, "end_raw": er,
                "start_quality": sq, "end_quality": eq,
                "source_tag": " | ".join(f"{k}={t[k]}" for k in ("source", "source:name", "source:url") if t.get(k)) or None,
                "campaign": campaign_of(t), "wikidata": t.get("wikidata"), "wikipedia": t.get("wikipedia"),
                "extinct": ey is not None and ey < CURRENT_YEAR,
            }, shapely.set_precision(g, 1e-6, mode="pointwise")))
        for side in ("start", "end"):
            c = Counter(p[f"{side}_raw"] for p, _ in feats if p[f"{side}_raw"])
            for p, _ in feats:
                if p[f"{side}_raw"] and c[p[f"{side}_raw"]] > HEAP_MIN:
                    p[f"{side}_quality"] = "placeholder"
        _write_geojson(out, feats, name)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("fetch", "all"):
        fetch()
    if what in ("build", "all"):
        build()
    if what in ("survey", "all"):
        survey()
    if what in ("extras", "all"):
        extras()
