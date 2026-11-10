"""Research helper: write data/tables/transit_stations.csv from the downloaded sources.

Inputs (data/raw/transit, data/interim/transit):
  station_match.csv      GTFS station <-> Wikipedia borough-list row <-> Wikidata item (match_stations.py)
  wikipedia/articles/    article wikitext (fetch_articles.py) - the station infoboxes
  wikidata/stations_box.csv   every station item in the map box with P1619 / P3999
  wd_rest.csv            Wikidata station items of the map that are not GTFS subway stations

Rule for an opening day (same for closing days):
  1. the article infobox, when it gives a day;
  2. else a Wikidata P1619 value with day precision;
  3. else the borough list ("NYCS row") day;
  4. else the infobox year or month  -> note says "estimated: year only".
Subway stations that took over a railroad station (Rockaway line: LIRR; Dyre Avenue line: New
York, Westchester & Boston) carry the day subway service began; the note names the railroad.
The note records which sources agree and what the others say.

    ../../../../.venv/bin/python build_station_table.py
"""
from __future__ import annotations

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
from infobox import infoboxes  # noqa: E402
from match_stations import sim, toks  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
RAW = ROOT / "data" / "raw" / "transit"
INT = ROOT / "data" / "interim" / "transit"
TABLES = ROOT / "data" / "tables"
WP = "https://en.wikipedia.org/wiki/"

TITLE_FIX = {
    "145th Street station (IND Eighth Avenue Line, Concourse Line)": "145th Street station (IND lines)",
    "50th Street station (IND Eighth Avenue Line, Queens Boulevard Line)": "50th Street station (IND lines)",
    "Clark Street<!--or Clark Street–Brooklyn Heights?--> station": "Clark Street station",
    "DeKalb Avenue station (BMT Fourth Avenue Line, Brighton Line)": "DeKalb Avenue station (BMT lines)",
    "East 143rd Street–St. Mary's Street|<!--before=143|-->div=IRT station": "East 143rd Street–St. Mary's Street station",
    "Prospect Park station (BMT Brighton Line, Franklin Avenue Line)": "Prospect Park station (BMT lines)",
    "Seventh Avenue station (IND Sixth Avenue Line, Queens Boulevard Line)": "Seventh Avenue station (IND lines)",
}
# subway service began on a line taken over from a railroad: (first subway day, what stood before)
ROCKAWAY = {c: "1956-06-28" for c in ("H02", "H03", "H04", "H06", "H07", "H08", "H09", "H10", "H12", "H13", "H14", "H15")}
ROCKAWAY["H11"] = "1958-01-16"
DYRE = {c: "1941-05-15" for c in ("501", "502", "503", "504", "505")}
# hand decisions where the automatic choice picked the wrong platform set of a complex
MANUAL = {
    # code: (date, note, article)
    "A27": ("1932-09-10", "IND Eighth Avenue Line platforms (the complex infobox carries the 1917 IRT date)",
            "42nd Street–Port Authority Bus Terminal station"),
    "Q01": ("1917-09-04", "Manhattan Bridge (express) platforms of Canal Street, opened with the Broadway Line's first section",
            "Canal Street station (New York City Subway)"),
    "R23": ("1918-01-05", "main line (local) platforms of Canal Street", "Canal Street station (New York City Subway)"),
    "L19": ("1928-07-14", "Canarsie Line completed Montrose Av - Broadway Junction", "Halsey Street station (BMT Canarsie Line)"),
    "D13": ("1933-07-01", "lower (Concourse Line) level of 145th Street, opened with the Concourse Line",
            "145th Street station (IND lines)"),
    "D20": ("1936-01-01", "lower (Sixth Avenue Line) level of West Fourth Street", "West Fourth Street–Washington Square station"),
    "718": ("1916-11-16", "Flushing Line side of Queensboro Plaza (infobox)", "Queensboro Plaza station"),
    "R09": ("1917-02-01", "Astoria Line side of Queensboro Plaza (Astoria Line opened 1 Feb 1917)", "Queensboro Plaza station"),
    "A28": ("1932-09-10", "borough list only", "34th Street–Penn Station (IND Eighth Avenue Line)"),
    "128": ("1917-06-03", "borough list only", "34th Street–Penn Station (IRT Broadway–Seventh Avenue Line)"),
}
# Wikidata items that are not a closed station: a temporary closure, one platform of an open station
DROP = {"Q548622", "Q3498505", "Q2355557"}
CLOSED_LIST = WP + "List_of_closed_New_York_City_Subway_stations"
# closed platforms the automatic pass cannot read (the two South Ferry loops share one article)
EXTRA = [
    ("subway", "X-southferry-outer", "South Ferry (outer loop)", "1905-07-10", "2017-06-27",
     "outer loop platform; closed 16 Mar 2009 when the new terminal opened, in use again 4 Apr 2013 - 27 Jun 2017 after Hurricane Sandy flooded the new one",
     CLOSED_LIST, "IRT Broadway–Seventh Avenue Line", "Underground", "-74.0131", "40.7012"),
    ("subway", "X-southferry-inner", "South Ferry (inner loop)", "1918-07-01", "1977-02-13",
     "inner loop platform (Lexington Avenue shuttle)", CLOSED_LIST, "IRT Lexington Avenue Line", "Underground", "-74.0130", "40.7014"),
]
# single values the automatic rule gets wrong
CORRECT = {
    "Q5123191": ("closed", "1953-12-31", "closed: the infobox's first day (13 Jun 1942) is the end of Second Avenue service; "
                 "Third Avenue trains used the City Hall branch until 31 Dec 1953 (Wikidata)"),
}
EL_LINES = ("IRT Third Avenue Line", "IRT Second Avenue Line", "IRT Sixth Avenue Line", "IRT Ninth Avenue Line",
            "BMT Fulton Street Line", "BMT Fifth Avenue Line", "BMT Lexington Avenue Line", "Fulton Street Line",
            "34th Street Branch", "42nd Street Branch", "59th Street Bridge")
SUBWAY_PREFIX = ("IRT ", "BMT ", "IND ")
SIR_LINES = ("Staten Island Railway", "North Shore Branch", "South Beach Branch")
LIRR_LINES = ("Port Washington Branch", "Atlantic Branch", "Main Line (Long Island Rail Road)", "Montauk Branch",
              "Rockaway Beach Branch", "Evergreen Branch", "Far Rockaway Branch", "Bushwick Branch", "Whitestone Branch",
              "Bay Ridge Branch", "Hempstead Branch", "Belmont Park Branch", "Cedarhurst Cut-off",
              "Flushing and North Side Railroad", "East Side Access", "Lower Montauk", "Main Line", "West Hempstead Branch")
MNR_LINES = ("Harlem Line", "Hudson Line", "Park Avenue main line", "New Haven Line", "Hell Gate Line", "Putnam Division",
             "MTA New Haven Line", "Northeast Corridor", "West Side Line", "Port Morris Branch")
PATH_LINES = ("Uptown Hudson Tubes", "Downtown Hudson Tubes", "PATH")


def system_of(lines: str) -> str:
    ls = [x.strip() for x in lines.split("|") if x.strip()]
    if any(any(x.startswith(e) for e in EL_LINES) for x in ls):
        return "el"
    if any(x.startswith(SUBWAY_PREFIX) for x in ls):
        return "subway"
    if any(any(x.startswith(e) for e in SIR_LINES) for x in ls):
        return "sir"
    if any(any(x.startswith(e) for e in PATH_LINES) for x in ls):
        return "path"
    if any(any(x.startswith(e) for e in MNR_LINES) for x in ls):
        return "mnr"
    if any(any(x.startswith(e) for e in LIRR_LINES) for x in ls):
        return "lirr"
    return ""


def wd_days(vals: str) -> list[str]:
    """'1904-10-27/11|1905-01-01/9' -> day-precision dates."""
    return sorted(v.split("/")[0] for v in vals.split("|") if v and v.split("/")[1].startswith("11"))


def main():
    wd = pd.read_csv(RAW / "wikidata" / "stations_box.csv", dtype=str, keep_default_na=False)
    wd["qid"] = wd.s.str.rsplit("/", n=1).str[-1]
    wd_open = {q: "|".join(sorted(set(a[:10] + "/" + b[:2] for a, b in zip(g.opened, g.openedPrec) if a)))
               for q, g in wd.groupby("qid")}
    m = pd.read_csv(INT / "station_match.csv", dtype=str, keep_default_na=False)
    mta = pd.read_csv(RAW / "mta_stations" / "stations.csv", dtype=str, keep_default_na=False)
    rows = []
    stats = {"3 agree": 0, "2 agree": 0, "1 source": 0, "estimated": 0, "manual": 0}

    # ---------------- subway (GTFS)
    matched = {r.gtfs_stop_id: r for r in m.itertuples()}
    for s in mta[mta.division != "SIR"].itertuples():
        code = s.gtfs_stop_id
        r = matched.get(code)
        base = {"system": "subway", "code": code, "name": s.stop_name, "closed": "", "line": f"{s.division} {s.line}",
                "structure": s.structure, "lon": s.gtfs_longitude, "lat": s.gtfs_latitude}
        if code in MANUAL:
            d, note, title = MANUAL[code]
            rows.append({**base, "opened": d, "note": note, "source": WP + urllib.parse.quote(title.replace(" ", "_"))})
            stats["manual"] += 1
            continue
        title = TITLE_FIX.get(r.title, r.title)
        ib = infoboxes(fetch(title) or "")
        lt = toks(r.wline)
        best, bs = None, -1.0
        for b in ib:
            sc = max([sim(lt, toks(l)) for l in b["lines"]] or [0]) - 0.1 * (len(b["lines"]) - 1)
            if sc > bs:
                best, bs = b, sc
        ibd, ibp = (best["opened"], best["opened_prec"]) if best else ("", "")
        wdd = wd_days(wd_open.get(r.qid, "")) if r.qid else []
        wp = r.wopen
        src = WP + urllib.parse.quote(title.replace(" ", "_"))
        if code in ROCKAWAY or code in DYRE:
            d = ROCKAWAY.get(code) or DYRE[code]
            rr = "Long Island Rail Road" if code in ROCKAWAY else "New York, Westchester & Boston Railway"
            note = f"day subway service began (borough list); a {rr} station stood here from {ibd[:4] or 'earlier'} (infobox)"
            stats["2 agree" if d in wdd else "1 source"] += 1
        elif ibp == "day":
            d = ibd
            a, b = (d == wp), (d in wdd)
            if a and b:
                note = "infobox, borough list and Wikidata agree"
                stats["3 agree"] += 1
            elif a:
                note = "infobox and borough list agree" + (f"; Wikidata {'/'.join(wdd)}" if wdd else "")
                stats["2 agree"] += 1
            elif b:
                note = "infobox and Wikidata agree" + (f"; borough list {wp}" if wp else "")
                stats["2 agree"] += 1
            else:
                note = "infobox" + (f"; borough list {wp}" if wp else "") + (f"; Wikidata {'/'.join(wdd)}" if wdd else "")
                stats["1 source"] += 1
        elif wdd:
            cand = [x for x in wdd if not ibd or x[:4] >= ibd[:4]] or wdd
            d = cand[0]
            note = f"Wikidata {r.qid}" + (f"; infobox gives only {ibd[:4]}" if ibd else "") + (f"; borough list {wp}" if wp else "")
            stats["2 agree" if d == wp else "1 source"] += 1
        elif wp:
            d = wp
            note = "borough list" + (f"; infobox gives only {ibd[:4]}" if ibd else "")
            stats["1 source"] += 1
        elif ibd:
            d = ibd
            note = f"estimated: the infobox gives only the year {ibd[:4]} (mid-year used)"
            stats["estimated"] += 1
        else:
            d = ""
            note = "estimated: no date found"
            stats["estimated"] += 1
        if r.qid:
            note += f" [{r.qid}]"
        rows.append({**base, "opened": d, "note": note, "source": src})

    # ---------------- everything else Wikidata knows inside the map
    rest = pd.read_csv(INT / "rest_dates.csv", dtype=str, keep_default_na=False)
    sir = mta[mta.division == "SIR"].copy()
    sir["lon"] = sir.gtfs_longitude.astype(float)
    sir["lat"] = sir.gtfs_latitude.astype(float)
    used_sir = set()
    n_rest = {"el": 0, "subway": 0, "sir": 0, "lirr": 0, "mnr": 0, "path": 0}
    for x in rest.itertuples():
        lines = x.ib_lines or x.lines
        system = system_of(lines)
        if not system:
            continue
        opd, clo = "", ""
        notes = []
        wo, wc = wd_days(x.wd_open), wd_days(x.wd_closed)
        if x.ib_open and x.ib_open_prec == "day":
            opd = x.ib_open
            notes.append("opened: infobox" + (" and Wikidata agree" if opd in wo else (f"; Wikidata {'/'.join(wo)}" if wo else "")))
        elif wo:
            opd = wo[0]
            notes.append("opened: Wikidata" + (f"; infobox gives only {x.ib_open[:4]}" if x.ib_open else ""))
        elif x.ib_open:
            opd = x.ib_open
            notes.append(f"opened: estimated, the infobox gives only {'the month' if x.ib_open_prec == 'month' else 'the year'} {x.ib_open[:7] if x.ib_open_prec == 'month' else x.ib_open[:4]}")
        elif x.wd_open:
            opd = x.wd_open.split("|")[0].split("/")[0][:4] + "-07-01"
            notes.append(f"opened: estimated, Wikidata gives only the year {opd[:4]}")
        if x.ib_closed and x.ib_closed_prec == "day":
            clo = x.ib_closed
            notes.append("closed: infobox" + (" and Wikidata agree" if clo in wc else (f"; Wikidata {'/'.join(wc)}" if wc else "")))
        elif wc:
            clo = wc[0]
            notes.append("closed: Wikidata" + (f"; infobox gives only {x.ib_closed[:4]}" if x.ib_closed else ""))
        elif x.ib_closed:
            clo = x.ib_closed
            notes.append(f"closed: estimated, the infobox gives only the year {x.ib_closed[:4]}")
        elif x.wd_closed:
            clo = x.wd_closed.split("|")[0].split("/")[0][:4] + "-07-01"
            notes.append(f"closed: estimated, Wikidata gives only the year {clo[:4]}")
        name = re.sub(r"\s+station$", "", x.label)
        src = WP + urllib.parse.quote(x.title.replace(" ", "_"))
        if system == "sir" and not clo:
            # a station of today's Staten Island Railway: attach to its GTFS stop
            d = np.hypot((sir.lon - float(x.lon)) * 84400, (sir.lat - float(x.lat)) * 111320)
            j = int(np.argmin(d.values))
            if d.values[j] < 400 and sir.gtfs_stop_id.iloc[j] not in used_sir:
                g = sir.iloc[j]
                used_sir.add(g.gtfs_stop_id)
                rows.append({"system": "sir", "code": g.gtfs_stop_id, "name": g.stop_name, "opened": opd, "closed": "",
                             "note": "; ".join(notes) + f" [{x.qid}]", "source": src, "line": "Staten Island Railway",
                             "structure": g.structure, "lon": g.gtfs_longitude, "lat": g.gtfs_latitude})
                n_rest["sir"] += 1
            continue
        if system == "subway" and not clo:
            continue  # a complex item or a platform set already covered by its GTFS station
        if not opd:
            continue
        rows.append({"system": system, "code": x.qid, "name": name, "opened": opd, "closed": clo,
                     "note": "; ".join(notes), "source": src, "line": "; ".join(v.strip() for v in lines.split("|") if v.strip()), "structure": x.ib_struct[:30],
                     "lon": x.lon, "lat": x.lat})
        n_rest[system] += 1
    for g in sir[~sir.gtfs_stop_id.isin(used_sir)].itertuples():
        rows.append({"system": "sir", "code": g.gtfs_stop_id, "name": g.stop_name, "opened": "", "closed": "",
                     "note": "estimated: no dated article found", "source": WP + "List_of_Staten_Island_Railway_stations",
                     "line": "Staten Island Railway", "structure": g.structure, "lon": g.gtfs_longitude, "lat": g.gtfs_latitude})

    out = pd.DataFrame(rows, columns=["system", "code", "name", "opened", "closed", "note", "source", "line", "structure", "lon", "lat"])
    out = out[~out.code.isin(DROP)]
    for code, (col, val, why) in CORRECT.items():
        out.loc[out.code == code, col] = val
        out.loc[out.code == code, "note"] = out.loc[out.code == code, "note"] + "; " + why
    out = pd.concat([out, pd.DataFrame(EXTRA, columns=out.columns)], ignore_index=True)
    order = {"subway": 0, "sir": 1, "el": 2, "path": 3, "lirr": 4, "mnr": 5}
    out["_o"] = out.system.map(order)
    out["_c"] = (out.closed != "").astype(int)
    out = out.sort_values(["_o", "_c", "line", "code"]).drop(columns=["_o", "_c"])
    out.to_csv(INT / "transit_stations_draft.csv", index=False)
    out.to_csv(TABLES / "transit_stations.csv", index=False)
    print(stats, n_rest, len(out), file=sys.stderr)
    print("no date:", out[out.opened == ""][["system", "code", "name"]].to_string(), file=sys.stderr)


if __name__ == "__main__":
    main()
