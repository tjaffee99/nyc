"""Research helper (run once, by hand): join the three station sources into a draft of
data/tables/transit_stations.csv for the subway and the Staten Island Railway.

  GTFS / MTA station table   every parent station (code, name, MTA line, structure, lon/lat)
  Wikipedia borough lists    {{NYCS row 2 |name= |div= |line= |open={{Dts|...}}}} — opening day
  Wikidata (P1619)           opening day + coordinates + the English article of each station

A GTFS station is matched to one Wikipedia row (optimal assignment on name, line, division,
borough and - where the article has a Wikidata item - distance), and through the row's article
to the Wikidata item. The two dates are compared; the result is written with both sources.

    ../../.venv/bin/python match_stations.py   (from data/manual/transit/tools)
"""
from __future__ import annotations

import re
import sys
import urllib.parse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

ROOT = Path(__file__).resolve().parents[4]
RAW = ROOT / "data" / "raw" / "transit"
OUT = ROOT / "data" / "interim" / "transit"
OUT.mkdir(parents=True, exist_ok=True)

BORO = {"M": "Manhattan", "Bx": "the_Bronx", "Bk": "Brooklyn", "Q": "Queens"}
ORD = {"first": "1", "second": "2", "third": "3", "fourth": "4", "fifth": "5", "sixth": "6", "seventh": "7",
       "eighth": "8", "ninth": "9", "tenth": "10", "eleventh": "11", "twelfth": "12"}
ABBR = {"street": "st", "streets": "sts", "avenue": "av", "avenues": "avs", "ave": "av", "boulevard": "blvd",
        "parkway": "pkwy", "pky": "pkwy", "road": "rd", "square": "sq", "place": "pl", "heights": "hts",
        "junction": "jct", "drive": "dr", "center": "ctr", "highway": "hwy", "saint": "st", "east": "e",
        "west": "w", "north": "n", "south": "s", "plaza": "plz", "university": "univ", "fort": "ft",
        "mount": "mt", "turnpike": "tpke", "island": "is", "park": "pk", "terminal": "term", "lane": "ln",
        "new": "new", "york": "york", "washington": "wash", "playground": "plgd", "court": "ct", "house": "house"}


def toks(s: str) -> set[str]:
    s = s.lower().replace("&amp;", "&")
    s = re.sub(r"[–—/\-&,.()']", " ", s)
    out = set()
    for t in s.split():
        t = ORD.get(t, t)
        t = re.sub(r"^(\d+)(st|nd|rd|th)$", r"\1", t)
        t = ABBR.get(t, t)
        if t not in ("station", "the", "of", "and"):
            out.add(t)
    return out


def sim(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    w = lambda t: 3.0 if t.isdigit() else 1.0
    inter = sum(w(t) for t in a & b)
    union = sum(w(t) for t in a | b)
    return inter / union


def wiki_rows() -> pd.DataFrame:
    rows = []
    for code, boro in BORO.items():
        txt = (RAW / "wikipedia" / f"List_of_New_York_City_Subway_stations_in_{boro}.wiki").read_text()
        for m in re.finditer(r"\{\{NYCS row 2\|(.*)", txt):
            body = m.group(1)
            body = re.sub(r"<ref[^>]*/>", "", body)
            body = re.sub(r"<ref[^>]*>.*?</ref>", "", body)
            f = {}
            for part in re.split(r"\|(?=\s*[a-z0-9]+\s*=)", body):
                if "=" in part:
                    k, v = part.split("=", 1)
                    f[k.strip()] = v.strip()
            name = f.get("name", "")
            d = re.search(r"\{\{[Dd]ts\|(\d{4})-(\d{1,2})-(\d{1,2})", f.get("open", "")) or \
                re.search(r"\{\{[Dd]ts\|(\d{4})\|(\d{1,2})\|(\d{1,2})", f.get("open", ""))
            opened = f"{int(d.group(1)):04d}-{int(d.group(2)):02d}-{int(d.group(3)):02d}" if d else ""
            div = f.get("div", "")
            line = f.get("line", "")
            if line == "lines":
                line = re.sub(r"\[\[[^|\]]*\|([^\]]*)\]\]", r"\1", f.get("multiline2", ""))
            if f.get("partof"):
                title = f["partof"]
            elif f.get("stationdab", "n").lower().startswith("y"):
                title = f"{name} station ({div} {line})"
            else:
                title = f"{name} station"
            rows.append({"boro": code, "wname": f.get("text", name) or name, "div": div, "wline": line, "wopen": opened,
                         "title": title.rstrip("}").strip(), "raw_open": f.get("open", "")})
    return pd.DataFrame(rows)


def main():
    mta = pd.read_csv(RAW / "mta_stations" / "stations.csv", dtype=str)
    mta["lat"] = mta.gtfs_latitude.astype(float)
    mta["lon"] = mta.gtfs_longitude.astype(float)
    sub = mta[mta.division != "SIR"].reset_index(drop=True)
    w = wiki_rows()
    wd = pd.read_csv(RAW / "wikidata" / "stations_box.csv", dtype=str)
    wd["title"] = wd.article.fillna("").map(lambda u: urllib.parse.unquote(u.rsplit("/", 1)[-1]).replace("_", " "))
    c = wd.coord.str.extract(r"Point\(([-\d.]+) ([-\d.]+)\)").astype(float)
    wd["wlon"], wd["wlat"] = c[0], c[1]
    by_title = {t: g for t, g in wd[wd.title != ""].groupby("title")}

    w["wlon"] = np.nan
    w["wlat"] = np.nan
    w["qid"] = ""
    w["wd_open"] = ""
    w["wd_prec"] = ""
    for i, r in w.iterrows():
        g = by_title.get(r.title)
        if g is None:
            continue
        w.loc[i, ["wlon", "wlat"]] = [g.wlon.iloc[0], g.wlat.iloc[0]]
        w.loc[i, "qid"] = g.s.iloc[0].rsplit("/", 1)[-1]
        op = g.dropna(subset=["opened"])
        if len(op):
            w.loc[i, "wd_open"] = "|".join(sorted(set(op.opened.str[:10])))
            w.loc[i, "wd_prec"] = "|".join(sorted(set(op.openedPrec.astype(str))))

    n, m = len(sub), len(w)
    cost = np.full((n, m), 50.0)
    st = [toks(s) for s in sub.stop_name]
    sl = [toks(s) for s in sub.line]
    wt = [toks(s) for s in w.wname]
    wl = [toks(s) for s in w.wline]
    kx = 111320 * np.cos(np.radians(40.72))
    for i in range(n):
        for j in range(m):
            if sub.borough[i] != w.boro[j]:
                continue
            s = 3.0 * sim(st[i], wt[j]) + 1.5 * sim(sl[i], wl[j]) + (1.5 if sub.division[i] == w["div"][j] else 0.0)
            if np.isfinite(w.wlon[j]):
                d = np.hypot((sub.lon[i] - w.wlon[j]) * kx, (sub.lat[i] - w.wlat[j]) * 111320)
                s += 3.0 * max(0.0, 1.0 - d / 400.0) - min(d, 5000.0) / 500.0
            cost[i, j] = -s
    ri, ci = linear_sum_assignment(cost)
    res = sub.iloc[ri].reset_index(drop=True)
    wm = w.iloc[ci].reset_index(drop=True)
    res = pd.concat([res[["gtfs_stop_id", "stop_name", "division", "line", "borough", "structure", "daytime_routes", "lon", "lat"]], wm], axis=1)
    res["score"] = -cost[ri, ci]
    res["dist"] = np.hypot((res.lon - res.wlon) * kx, (res.lat - res.wlat) * 111320)
    res.to_csv(OUT / "station_match.csv", index=False)
    un = sub[~sub.gtfs_stop_id.isin(res.gtfs_stop_id)]
    print(f"{n} GTFS subway stations, {m} Wikipedia rows, {len(res)} matched, {len(un)} GTFS unmatched", file=sys.stderr)
    print(un[["gtfs_stop_id", "stop_name", "line"]].to_string(), file=sys.stderr)
    low = res[(res.score < 4.0) | (res.dist > 300)]
    pd.set_option("display.width", 250)
    print(low[["gtfs_stop_id", "stop_name", "line", "wname", "wline", "wopen", "wd_open", "score", "dist"]].to_string(), file=sys.stderr)
    print("no wikidata item:", (res.qid == "").sum(), "| no wd date:", (res.wd_open == "").sum(),
          "| no wp date:", (res.wopen == "").sum(), file=sys.stderr)
    both = res[(res.wd_open != "") & (res.wopen != "")]
    agree = both.apply(lambda r: r.wopen in r.wd_open.split("|"), axis=1)
    print(f"both dated: {len(both)}, agree: {agree.sum()}, disagree: {(~agree).sum()}", file=sys.stderr)
    print(both[~agree][["gtfs_stop_id", "stop_name", "line", "wname", "wline", "wopen", "wd_open", "wd_prec"]].to_string(), file=sys.stderr)


if __name__ == "__main__":
    main()
