"""Write data/tables/known_building_dates.sites.csv:

  1. researched years of standing buildings (buildings_def.py, text sources),
  2. years bracketed by USGS map editions (edition_brackets.csv from run_editions.py), `estimated`,
  3. one floor row per site with floor=True: id `site_floor:<site id>` - no building inside the
     site's outline (sites.geojson) may predate the founding (to be applied to estimated years).

  cd data/manual/sites && ../../../.venv/bin/python -I tools/build_buildings.py
"""
import csv
import json
import sys
import urllib.parse
from pathlib import Path

import pandas as pd
from shapely.geometry import Point, shape

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import buildings_def  # noqa: E402
import geom as G  # noqa: E402
import topo  # noqa: E402

W = "https://en.wikipedia.org/wiki/"
OUT = G.ROOT / "data" / "tables" / "known_building_dates.sites.csv"
COLS = ["id", "name", "lat", "lon", "bin", "start_year", "end_year", "source_url", "note"]


# Sites whose buildings may take a map-bracket year (site id -> founding year). Kept to isolated
# civil campuses and plants founded after 1925, whose first sheets after the founding draw single
# buildings: the readings failed everywhere else (README, "What the map brackets are worth").
BRACKET_SITES = {
    "rikers_island_jails": 1932, "bronx_state_hospital": 1963, "bronx_municipal_hospital": 1955,
    "hunts_point_produce_market": 1967, "hunts_point_meat_market": 1974, "poletti_power_project": 1977,
    "willowbrook_state_school": 1942, "fresh_kills_landfill": 1948,
}
# absent-then-drawn brackets are written only where the sheets were also looked at (Rikers Island:
# the 1977 and 1997 revisions print the new jails in purple)
TWO_SIDED = {"rikers_island_jails"}


# floors that should also reach assessor years (the lot's year stamped on every building)
FLOOR_NOTE = {
    "fort_tilden": "; HERE ALSO to assessor years: the lot's 1900 / 1901 is stamped on 50 of the fort's 60 buildings",
}


def url(src):
    return src if src.startswith("http") else W + urllib.parse.quote(src, safe="_,()'&")


def osm_building(site_geom, name):
    w, s, e, n = site_geom.bounds
    r = G.con().execute(
        f"select st_x(st_centroid(geometry)), st_y(st_centroid(geometry)) from '{G.OV}/building.parquet' "
        "where name = $5 and st_intersects(geometry, st_makeenvelope($1,$2,$3,$4))", [w, s, e, n, name]).fetchall()
    r = [p for p in r if site_geom.buffer(0.0005).contains(Point(p))]
    if not r:
        raise KeyError(f"no OSM building named {name!r}")
    return r[0]


def footprint_at(lon, lat, reach=60.0):
    fp = G.footprints(G.circle(lon, lat, reach + 150))
    if not len(fp):
        return None
    p = Point(lon, lat)
    inside = fp[[g.contains(p) for g in fp.geometry]]
    if len(inside):
        return inside.sort_values("area_m2").iloc[-1]
    d = [g.distance(p) * G.KY for g in fp.geometry]
    fp = fp.assign(d=d)
    near = fp[fp.d <= reach]
    return near.sort_values("area_m2").iloc[-1] if len(near) else None


def main():
    d = json.loads((HERE.parent / "sites.geojson").read_text())
    sites = {f["properties"]["id"]: (f["properties"], shape(f["geometry"])) for f in d["features"]}
    rows, log, bins = [], [], set()
    # 1. text
    for b in buildings_def.BUILDINGS:
        try:
            if b["loc"][0] == "osm":
                lon, lat = osm_building(sites[b["loc"][1]][1], b["loc"][2])
            else:
                lon, lat = b["loc"][1], b["loc"][2]
            f = footprint_at(lon, lat)
        except Exception as e:  # noqa: BLE001
            log.append((b["id"], f"NOT FOUND: {e}"))
            continue
        if f is None or pd.isna(f.bin):
            log.append((b["id"], "NOT FOUND: no footprint"))
            continue
        cur = G.con().execute(f"select start_year, year_confidence, year_src from '{G.BL}' where bin = $1 and end_year = 9999 "
                              "order by area desc limit 1", [float(f.bin)]).fetchall()
        cy, cc, cs = cur[0] if cur else (float("nan"), "", "")
        c = f.geometry.representative_point()
        tag = f"bin {int(f.bin)} {f.area_m2:.0f} m2; built file {cy:.0f} {cs} {cc}"
        if cs == "lpc" and abs(cy - b["year"]) <= 5:
            log.append((b["id"], "agrees with LPC, not written: " + tag))
            continue
        log.append((b["id"], f"written {b['year']}: " + tag))
        bins.add(int(f.bin))
        rows.append([b["id"], b["name"], round(c.y, 6), round(c.x, 6), int(f.bin), b["year"], 9999, url(b["src"]),
                     b["note"] + (" (the built file had " + f"{cy:.0f} from {cs})" if cur else "")])
    n_text = len(rows)
    # 2. map brackets - only for the sites of BRACKET_SITES (see the README, "What the map brackets are worth")
    n_map = 0
    f_br = HERE.parent / "edition_brackets.csv"
    if f_br.exists():
        t = pd.read_csv(f_br)
        quad = {}
        for r in t.itertuples():
            if not r.bin or pd.isna(r.est_start) or r.bin in bins or r.built_src == "lpc":
                continue
            if r.site not in BRACKET_SITES:
                continue
            weak = (r.built_conf == "estimated") or bool(r.stamped)
            if not weak or pd.isna(r.built_year):
                continue
            two = pd.notna(r.last_absent)
            if two and r.first_drawn - r.last_absent > 25:
                continue  # too wide to say anything (an 1890s sheet against the 1940s one)
            if two and r.site not in TWO_SIDED:
                continue
            if two:
                # one empty sheet is not enough: a symbol missed once makes a false bracket (measured:
                # one in six old buildings is missed on a given sheet). Ask for two empty 1:24k sheets
                # before the first drawing, or a site founded after the last empty sheet.
                n_abs = sum(1 for x in str(r.sheets).split() if x.endswith(":a") and int(x[:4]) < r.first_drawn)
                if n_abs < 2 and BRACKET_SITES[r.site] <= r.last_absent:
                    continue
            if two and r.last_absent - 1 <= r.built_year <= r.first_drawn + 1:
                continue  # the built year already lies in the bracket
            if not two and abs(r.built_year - r.est_start) <= 2:
                continue
            key = (int(r.lon // 0.125), int(r.lat // 0.125))
            if key not in quad:
                eds = [e for e in topo.editions(r.lon, r.lat) if e[0] <= 31680]
                quad[key] = eds[-1][1] if eds else "?"
            bins.add(int(r.bin))
            n_map += 1
            rows.append([f"site_map:{r.site}:{int(r.bin)}", "", r.lat, r.lon, int(r.bin), round(float(r.est_start), 1), 9999,
                         "https://ngmdb.usgs.gov/topoview/viewer/",
                         f"estimated: USGS {quad[key]} 1:24,000 editions - {r.evidence} (sheets {r.sheets}); the built "
                         f"file had {r.built_year:.0f} from {r.built_src}; site={r.site}"])
    # 3. floors
    n_floor = 0
    for sid, (p, g) in sites.items():
        if not p["floor"]:
            continue
        n_floor += 1
        rows.append([f"site_floor:{sid}", p["name"] + " (no building older than the site)", p["lat"], p["lon"], "",
                     p["start_year"], 9999, p["source_url"],
                     f"site_floor; site={sid}; no building inside this site's outline (data/manual/sites/sites.geojson) "
                     f"predates {p['start_year']} - apply to estimated years only" + FLOOR_NOTE.get(sid, "")])
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(COLS)
        w.writerows(rows)
    for x in log:
        print("  ", *x)
    print(f"{len(rows)} rows -> {OUT}: {n_text} text, {n_map} map brackets, {n_floor} site floors")


if __name__ == "__main__":
    main()
