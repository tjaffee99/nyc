"""Research helper: the railroad, PATH and light rail stations of the counties around the city
-> rows of data/tables/transit_stations.csv whose note starts with "[counties]" (rewritten on every run;
the city's rows are not touched).

  * Standing stations: OpenStreetMap station / halt nodes inside the map outline (Overpass,
    data/raw/transit/osm/osm_stations_region.json, ODbL) of the networks NJ Transit, Metro-North,
    PATH, Hudson-Bergen Light Rail and Newark Light Rail that are not in the table yet. Position and
    name are OpenStreetMap's; the Wikidata item is the node's `wikidata` tag.
  * Stations that are gone: Wikidata station items of the region box with a closing date (P3999) or
    the class "former railway station" (CC0), position = Wikidata's coordinate.
  * Days, the rule of the city's table: (1) the infobox of the station's Wikipedia article when it gives
    a day; (2) else Wikidata's P1619 / P3999 with day precision; (3) else the infobox month or year,
    else Wikidata's year - the note then says "estimated" (mid-month / mid-year is used). Where an
    infobox lists several dates the earliest year in the field is the opening (a later full date is a
    rebuilding). A station with no opening date anywhere keeps an empty `opened`: pipeline/transit.py
    gives it the opening year of the track it stands on and the note says so (estimated).
  * AirTrain Newark's stations are not in the table (a monorail inside the airport).

    ../../../../.venv/bin/python build_county_stations.py
"""
import json
import re
import sys
import urllib.parse
from pathlib import Path

import numpy as np
import pandas as pd
from shapely.geometry import Point, Polygon

sys.path.insert(0, str(Path(__file__).parent))
from fetch_articles import fetch  # noqa: E402
from infobox import infoboxes, parse_date  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
RAW = ROOT / "data" / "raw" / "transit"
TAB = ROOT / "data" / "tables" / "transit_stations.csv"
MARK = "[counties] "
poly = Polygon(json.load(open(ROOT / "data" / "manual" / "extent_ring.json"))["ring"]).buffer(0.004)

# days the sources above do not give, each with its article
MANUAL = {
    # code: (opened, closed, note, source)
    "Q4631436": ("2003-11-15", "", "the Hudson-Bergen Light Rail reached 22nd Street on 15 Nov 2003 (line article)",
                 "https://en.wikipedia.org/wiki/Hudson%E2%80%93Bergen_Light_Rail"),
}


def system_of(t):
    net = (t.get("network", "") + ";" + t.get("operator", "")).lower()
    st = t.get("station", "")
    if "airtrain" in net:
        return ""
    if "path" in net.split(";") or "port authority trans-hudson" in net or (st == "subway" and "path" in net):
        return "path"
    if st == "light_rail" or "light rail" in net:
        return "nlr" if "newark" in net else "hblr" if "hudson" in net else "lr?"
    if "metro-north" in net:
        return "mnr"
    if "nj transit" in net or "new jersey transit" in net or "njt" in net:
        return "njt"
    return ""


def clean(s):
    s = re.sub(r"<ref[^>]*/>", "", s or "")
    s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    return re.sub(r"<!--.*?-->", "", s, flags=re.S)


def first_date(raw):
    """(ISO day, precision) of the earliest date in an infobox field."""
    raw = clean(raw)
    d, p = parse_date(raw)
    yrs = [int(y) for y in re.findall(r"\b(1[7-9]\d\d|20[0-2]\d)\b", raw)]
    if d and yrs and min(yrs) < int(d[:4]):
        return f"{min(yrs)}-07-01", "year"
    return d, p


def article_title(url):
    return urllib.parse.unquote(url.rsplit("/wiki/", 1)[-1]).replace("_", " ") if "/wiki/" in url else ""


def dates(wdrow, title):
    """-> opened, closed, note, lines (infobox first, then Wikidata)."""
    ib = {}
    if title:
        txt = fetch(title) or ""
        m = re.search(r"\{\{\s*Infobox (station|NYCS|New York City Subway station)\b", txt, re.I)
        if m:
            from infobox import _balanced, _fields
            f = _fields(txt[m.start() + 2:_balanced(txt, m.start()) - 2])
            ib = {"opened": first_date(f.get("opened", "") or f.get("open", "")), "closed": parse_date(clean(f.get("closed", ""))),
                  "lines": "; ".join(infoboxes(txt)[0]["lines"][:3]) if infoboxes(txt) else ""}
    out, notes = {}, []
    for key, wcol, pcol in (("opened", "opened", "openedPrec"), ("closed", "closed", "closedPrec")):
        d, p = ib.get(key, ("", ""))
        wd = (wdrow or {}).get(wcol, "")[:10]
        wp = (wdrow or {}).get(pcol, "")
        if d and p == "day":
            out[key] = d
            notes.append(f"{key}: infobox" + (" and Wikidata agree" if wd == d else f"; Wikidata {wd[:4] if wp != '11' else wd}" if wd else ""))
        elif wd and wp == "11":
            out[key] = wd
            notes.append(f"{key}: Wikidata" + (f"; infobox gives only {d[:7] if p == 'month' else d[:4]}" if d else ""))
        elif d:
            out[key] = d
            notes.append(f"{key}: estimated, the infobox gives only the {p} {d[:7] if p == 'month' else d[:4]}")
        elif wd:
            out[key] = wd[:4] + "-07-01"
            notes.append(f"{key}: estimated, Wikidata gives only the year {wd[:4]}")
        else:
            out[key] = ""
    return out["opened"], out["closed"], "; ".join(notes), ib.get("lines", "")


def main():
    tab = pd.read_csv(TAB, dtype=str, keep_default_na=False)
    tab = tab[~tab.note.str.startswith(MARK)]
    have = set(tab.code)
    old_xy = tab[tab.system.isin(["path", "mnr", "lirr"]) & (tab.lon != "")][["lon", "lat"]].astype(float).values
    wd = pd.read_csv(RAW / "wikidata" / "stations_region.csv", dtype=str, keep_default_na=False)
    wd["qid"] = wd.s.str.rsplit("/", n=1).str[-1]
    wd = wd.sort_values(["qid", "openedPrec"], ascending=[True, False]).drop_duplicates("qid")
    wdq = {r["qid"]: r for r in wd.to_dict("records")}
    rows, seen = [], set()

    def near_old(lon, lat, m=150.0):
        if not len(old_xy):
            return False
        d = np.hypot((old_xy[:, 0] - lon) * 84400, (old_xy[:, 1] - lat) * 111320)
        return bool(d.min() < m)

    # ---- standing stations (OpenStreetMap)
    for e in json.load(open(RAW / "osm" / "osm_stations_region.json"))["elements"]:
        t = e.get("tags", {})
        lon = e.get("lon", e.get("center", {}).get("lon"))
        lat = e.get("lat", e.get("center", {}).get("lat"))
        if lon is None or t.get("railway") not in ("station", "halt") or not t.get("name"):
            continue
        sysm = system_of(t)
        if not sysm or not poly.contains(Point(lon, lat)):
            continue
        if sysm == "lr?":
            sysm = "nlr" if lon < -74.13 else "hblr"
        # the city's own stations stay as they are; New Jersey's shore lies inside the old outline
        if sysm == "mnr" and lat < 40.915 and lon > -73.94:
            continue
        qid = t.get("wikidata", "")
        code = qid or f"osm{e['id']}"
        if code in have or code in seen or (sysm in ("path", "mnr") and near_old(lon, lat)):
            continue
        seen.add(code)
        w = wdq.get(qid)
        title = article_title(w["article"]) if w is not None else ""
        op, cl, note, lines = dates(w, title)
        src = w["article"] if (w is not None and w["article"]) else (f"https://www.wikidata.org/wiki/{qid}" if qid else f"https://www.openstreetmap.org/{e['type']}/{e['id']}")
        if code in MANUAL:
            op, cl, note, src = MANUAL[code][0], MANUAL[code][1], MANUAL[code][2], MANUAL[code][3]
        if not op:
            note = "opened: not found - pipeline/transit.py gives it the opening year of its track (estimated)"
        rows.append({"system": sysm, "code": code, "name": t["name"], "opened": op, "closed": "", "note": MARK + note + (f" [{qid}]" if qid else ""),
                     "source": src, "line": lines or (w["lines"] if w is not None else ""), "structure": "", "lon": f"{lon:.6f}", "lat": f"{lat:.6f}"})
    # ---- stations that are gone (Wikidata)
    for w in wd.to_dict("records"):
        if w["qid"] in have or w["qid"] in seen or not ("railway station" in w["inst"] or "tram stop" in w["inst"] or "metro station" in w["inst"]):
            continue
        m = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", w["coord"])
        if not m:
            continue
        lon, lat = float(m.group(1)), float(m.group(2))
        if not poly.contains(Point(lon, lat)):
            continue
        if not (w["closed"] or "former railway station" in w["inst"]):
            continue
        # the city's closed stations are in the table already (its own tool); here only the counties
        if lon > -74.02 and lat < 40.915 and lon < -73.70:
            continue
        op, cl, note, lines = dates(w, article_title(w["article"]))
        if not cl:
            continue
        if op and cl <= op:
            continue
        name = re.sub(r"\s+(railway |railroad )?station$", "", w["sLabel"], flags=re.I)
        seen.add(w["qid"])
        if not op:
            note = (note + "; " if note else "") + "opened: not found - pipeline/transit.py gives it the opening year of its track (estimated)"
        rows.append({"system": "rail", "code": w["qid"], "name": name, "opened": op, "closed": cl, "note": MARK + note + f" [{w['qid']}]",
                     "source": w["article"] or f"https://www.wikidata.org/wiki/{w['qid']}", "line": lines or w["lines"], "structure": "",
                     "lon": f"{lon:.6f}", "lat": f"{lat:.6f}"})
    new = pd.DataFrame(rows)
    out = pd.concat([tab, new], ignore_index=True)
    out.to_csv(TAB, index=False)
    print(len(new), "county station rows;", len(out), "rows in the table")
    print(new.groupby("system").agg(n=("code", "size"), dated=("opened", lambda s: (s != "").sum()),
                                    estimated=("note", lambda s: s.str.contains("estimated").sum()),
                                    closed=("closed", lambda s: (s != "").sum())).to_string())


if __name__ == "__main__":
    main()
