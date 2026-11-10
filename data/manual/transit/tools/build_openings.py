"""Research helper: draft data/tables/transit_openings.csv for the subway and the Staten Island
Railway from the dated stations (transit_stations.csv) and the GTFS stop sequences.

Every stretch between two neighbouring stations (taken from the stop sequence of every GTFS
shape; express stretches that only repeat local ones are dropped) opens when the later of its
two stations opened. A station younger than both its neighbours is an infill station: the track
through it takes the neighbours' date (listed for review). Hand corrections are in FIX below,
each with its source. Runs of neighbouring stretches with one date along a route become one
row: route_id, opened, note, source, system, line, from_stop, to_stop, via (the GTFS shape the
stretch is traced along), closed.

The draft is cross-checked against OpenHistoricalMap's dated railway ways (CC0): rows whose
OHM date differs by more than 0.3 year are printed for review.

    ../../../../.venv/bin/python build_openings.py
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[4]
RAW = ROOT / "data" / "raw" / "transit"
INT = ROOT / "data" / "interim" / "transit"
G = RAW / "gtfs"
UTM = "EPSG:32618"
WP = "https://en.wikipedia.org/wiki/"

LINE_ARTICLE = {
    "8th Av - Fulton St": "IND_Eighth_Avenue_Line", "Broadway - 7Av": "IRT_Broadway–Seventh_Avenue_Line",
    "6th Av - Culver": "IND_Sixth_Avenue_Line", "Broadway - Brighton": "BMT_Brighton_Line", "Jamaica": "BMT_Jamaica_Line",
    "Lenox - White Plains Rd": "IRT_White_Plains_Road_Line", "Canarsie": "BMT_Canarsie_Line",
    "Queens Blvd": "IND_Queens_Boulevard_Line", "Lexington Av": "IRT_Lexington_Avenue_Line", "Flushing": "IRT_Flushing_Line",
    "Staten Island": "Staten_Island_Railway", "Eastern Pky": "IRT_Eastern_Parkway_Line", "Pelham": "IRT_Pelham_Line",
    "Rockaway": "IND_Rockaway_Line", "Jerome Av": "IRT_Jerome_Avenue_Line", "4th Av": "BMT_Fourth_Avenue_Line",
    "West End": "BMT_West_End_Line", "Concourse": "IND_Concourse_Line", "Crosstown": "IND_Crosstown_Line",
    "Astoria": "BMT_Astoria_Line", "Sea Beach": "BMT_Sea_Beach_Line", "Broadway": "BMT_Broadway_Line",
    "Myrtle Av": "BMT_Myrtle_Avenue_Line", "Liberty Av": "IND_Fulton_Street_Line", "Nostrand": "IRT_Nostrand_Avenue_Line",
    "Clark St": "IRT_Broadway–Seventh_Avenue_Line", "Dyre Av": "IRT_Dyre_Avenue_Line",
    "Franklin Shuttle": "BMT_Franklin_Avenue_Line", "63rd St": "63rd_Street_lines", "Queens - Archer": "Archer_Avenue_lines",
    "Second Av": "Second_Avenue_Subway", "Lexington - Shuttle": "42nd_Street_Shuttle", "Manhattan Bridge": "Chrystie_Street_Connection",
    "Sea Beach / West End / Culver / Brighton": "Coney_Island–Stillwell_Avenue_station",
}

# Hand corrections of single stretches: (stop A, stop B) -> (day, note, source). The automatic
# rule (later of the two stations) is wrong where the track is older or younger than the platforms.
FIX = {
    # the 1904 subway ran 33 St - Grand Central - (today's shuttle) - Times Sq - 50 St; today's
    # Lexington and Seventh Avenue platforms there date from 1918 / 1917, the track from 1904
    ("127", "126"): ("1904-10-27", "original 1904 subway north of Times Square (today's platforms opened 1917)", WP + "Early_history_of_the_IRT_subway"),
    ("120", "123"): ("1904-10-27", "original 1904 subway", WP + "Early_history_of_the_IRT_subway"),
    ("632", "631"): ("1904-10-27", "original 1904 subway south of Grand Central (today's platforms opened 1918)", WP + "Early_history_of_the_IRT_subway"),
    # river tunnels and connections that opened after the stations at both ends
    ("R11", "R09"): ("1920-08-01", "60th Street Tunnel", WP + "60th_Street_Tunnel"),
    ("R13", "R11"): ("1919-09-01", "Broadway Line extended to Lexington Avenue", WP + "BMT_Broadway_Line"),
    ("G20", "B04"): ("2001-12-16", "63rd Street Connector to the Queens Boulevard Line", WP + "63rd_Street_lines"),
    ("G14", "B04"): ("2001-12-16", "63rd Street Connector to the Queens Boulevard Line", WP + "63rd_Street_lines"),
    ("G21", "R11"): ("1955-12-01", "60th Street Tunnel Connection (11th Street Cut) from the Queens Boulevard Line", WP + "60th_Street_Tunnel_Connection"),
    ("D13", "A14"): ("1932-09-10", "Eighth Avenue Line south of 145 St (the lower-level platforms opened with the Concourse Line in 1933)", WP + "IND_Eighth_Avenue_Line"),
    ("A42", "F20"): ("1937-07-01", "Crosstown Line completed: Hoyt-Schermerhorn Sts to the South Brooklyn Line at Bergen St", WP + "IND_Crosstown_Line"),
    ("213", "214"): ("1904-11-26", "West Farms Division of 1904 (to 180th Street-Bronx Park); East 180th Street station itself opened 1917", WP + "IRT_White_Plains_Road_Line"),
    ("D43", "N10"): ("1915-06-22", "Sea Beach Line to Coney Island (today's terminal platforms: 1917-19)", WP + "BMT_Sea_Beach_Line"),
    ("B23", "D43"): ("1917-07-21", "West End Line completed to Coney Island", WP + "BMT_West_End_Line"),
    ("F38", "F39"): ("1920-05-01", "Culver Line completed to Coney Island", WP + "IND_Culver_Line"),
    ("139", "142"): ("1918-07-01", "Seventh Avenue Line to South Ferry (the last 400 m into the 2009 terminal follow the approach to the 1918 loop)", WP + "IRT_Broadway–Seventh_Avenue_Line"),
    ("D21", "D22"): ("1967-11-26", "Chrystie Street Connection", WP + "Chrystie_Street_Connection"),
    ("M18", "D21"): ("1968-07-01", "Chrystie Street Connection, Williamsburg Bridge link (built with the 1967 connection; first trains 1 Jul 1968)", WP + "Chrystie_Street_Connection"),
    ("Q01", "R30"): ("1915-06-22", "Manhattan Bridge subway tracks (Fourth Avenue / Sea Beach service to Chambers Street)", WP + "Manhattan_Bridge"),
    ("B10", "B08"): ("1989-10-29", "63rd Street Line", WP + "63rd_Street_lines"),
    ("Q05", "B08"): ("2017-01-01", "Second Avenue Subway connection to the 63rd Street Line", WP + "Second_Avenue_Subway"),
    ("R14", "B08"): ("1989-10-29", "63rd Street Line connection to the Broadway Line (regular service from 2017)", WP + "63rd_Street_lines"),
    ("A55", "A57"): ("1956-04-29", "Fulton Street Line extended to Grant Avenue and up to the Liberty Avenue elevated", WP + "IND_Fulton_Street_Line"),
    ("A57", "A59"): ("1956-04-29", "ramp to the Liberty Avenue elevated (the elevated itself opened 1915-09-25)", WP + "IND_Fulton_Street_Line"),
    ("A61", "H01"): ("1956-06-28", "Rockaway Line (ex-LIRR Rockaway Beach Branch) connected to the Liberty Avenue elevated", WP + "IND_Rockaway_Line"),
    ("A61", "H02"): ("1956-06-28", "Rockaway Line", WP + "IND_Rockaway_Line"),
    ("H01", "H02"): ("1956-06-28", "Rockaway Line (Aqueduct Racetrack station itself opened 1959)", WP + "IND_Rockaway_Line"),
    ("H01", "H03"): ("1956-06-28", "Rockaway Line", WP + "IND_Rockaway_Line"),
    ("F27", "F29"): ("1954-10-30", "Culver ramp: IND connected to the Culver elevated at Ditmas Avenue", WP + "IND_Culver_Line"),
    ("F27", "F26"): ("1933-10-07", "South Brooklyn Line to Church Avenue", WP + "IND_Culver_Line"),
    ("G22", "G24"): ("1933-08-19", "Crosstown Line Queens Plaza - Nassau Avenue", WP + "IND_Crosstown_Line"),
    ("M16", "M18"): ("1908-09-16", "Williamsburg Bridge subway tracks", WP + "Williamsburg_Bridge"),
    ("J27", "L22"): ("1928-07-14", "Canarsie Line", WP + "BMT_Canarsie_Line"),
    ("G05", "J12"): ("1988-12-11", "Archer Avenue Line (lower level) and ramp to the Jamaica elevated", WP + "Archer_Avenue_lines"),
    ("G06", "J12"): ("1988-12-11", "Archer Avenue Line (lower level) and ramp to the Jamaica elevated", WP + "Archer_Avenue_lines"),
    ("F05", "G07"): ("1988-12-11", "Archer Avenue Line (upper level) branch from the Queens Boulevard Line", WP + "Archer_Avenue_lines"),
    ("F06", "G07"): ("1988-12-11", "Archer Avenue Line (upper level) branch from the Queens Boulevard Line", WP + "Archer_Avenue_lines"),
    ("726", "725"): ("2015-09-13", "7 Subway Extension", WP + "7_Subway_Extension"),
    ("D43", "D42"): ("1919-05-29", "Brighton Line into Stillwell Avenue terminal", WP + "Coney_Island–Stillwell_Avenue_station"),
    ("F39", "D42"): ("1920-05-01", "Culver Line completed to Coney Island", WP + "IND_Culver_Line"),
    ("D26", "S04"): ("1878-08-18", "Brooklyn, Flatbush & Coney Island Railway north of Prospect Park (Franklin Avenue Line)", WP + "BMT_Franklin_Avenue_Line"),
    ("S04", "S03"): ("1878-08-18", "Franklin Avenue Line (Botanic Garden station itself opened 1928)", WP + "BMT_Franklin_Avenue_Line"),
    ("S03", "S01"): ("1896-08-15", "Franklin Avenue Line extended north to the Fulton Street elevated (the 1878 line ended at Bedford station, Atlantic Avenue)", WP + "BMT_Franklin_Avenue_Line"),
}
# express stretches kept although a younger local stretch runs beside them
KEEP = {("423", "234")}
# One date for a chain of neighbouring stations (the track is older than some of its platforms)
CHAIN = [
    (["D26", "D27", "D28", "D29", "D30", "D31", "D32", "D33", "D34", "D35", "D37", "D38", "D39", "D40"], "1878-07-02",
     "Brooklyn, Flatbush & Coney Island Railway, Prospect Park - Brighton Beach (surface line; grade-separated 1905-08, station dates in transit_stations.csv)",
     WP + "BMT_Brighton_Line"),
    (["R36", "R39", "R40", "R41"], "1915-06-22", "Fourth Avenue Line to 59th Street (45th and 53rd Street stations followed on 22 Sep 1915)", WP + "BMT_Fourth_Avenue_Line"),
    (["113", "112", "111", "110", "109"], "1906-03-12", "West Side Branch 157th Street - Dyckman Street - 221st Street (168th, 181st and 191st Street stations opened later)", WP + "IRT_Broadway–Seventh_Avenue_Line"),
    (["235", "236", "237", "238", "239"], "1920-08-23", "Eastern Parkway Line Atlantic Avenue - Utica Avenue (Bergen St, Grand Army Plaza and Eastern Parkway stations opened 10 Oct 1920)", WP + "IRT_Eastern_Parkway_Line"),
    (["F16", "F18", "A41"], "1936-04-09", "Rutgers Street Tunnel, East Broadway - Jay Street", WP + "Rutgers_Street_Tunnel"),
    (["S28", "S27", "S26", "S25", "S24", "S23", "S22", "S21", "S20", "S19", "S18"], "1860-04-23", "Staten Island Railway, Vanderbilt's Landing (Clifton) - Eltingville", WP + "Staten_Island_Railway"),
]
for _chain, _d, _n, _s in CHAIN:
    for _a, _b in zip(_chain[:-1], _chain[1:]):
        FIX[(_a, _b)] = (_d, _n, _s)
# A stretch that is two things: cut it at a point (lon, lat) on its shape. (a, b): (lon, lat, first part, second part)
SPLIT = {
    ("R30", "D22"): (-73.9944, 40.7157,
                     ("1915-06-22", "Manhattan Bridge north tracks (to the Broadway / Nassau Street lines until 1967)", WP + "Manhattan_Bridge"),
                     ("1967-11-26", "Chrystie Street Connection: Manhattan Bridge north tracks to Grand Street and the Sixth Avenue Line", WP + "Chrystie_Street_Connection")),
}


def decyear(s: str) -> float:
    d = dt.date.fromisoformat(str(s).strip())
    return round(d.year + (d.timetuple().tm_yday - 1) / 365.25, 3)


def to_utm(lon, lat):
    s = gpd.GeoSeries(gpd.points_from_xy(lon, lat), crs=4326).to_crs(UTM)
    return np.column_stack([s.x.values, s.y.values])


def densify(xy, step=10.0):
    out = [xy[0]]
    for a, b in zip(xy[:-1], xy[1:]):
        d = float(np.hypot(*(b - a)))
        if d < 0.3:
            continue
        n = int(np.ceil(d / step))
        for k in range(1, n + 1):
            out.append(a + (b - a) * (k / n))
    return np.array(out)


def load_network():
    """-> stations (dict code -> row), edges: {(a, b): {xy, shape, route, len}} from every GTFS shape."""
    stops = pd.read_csv(G / "stops.txt", dtype=str)
    parent = dict(zip(stops.stop_id, stops.parent_station.fillna("")))
    par = stops[stops.location_type == "1"]
    pxy = dict(zip(par.stop_id, to_utm(par.stop_lon.astype(float).values, par.stop_lat.astype(float).values)))
    trips = pd.read_csv(G / "trips.txt", dtype=str)
    st = pd.read_csv(G / "stop_times.txt", dtype=str, usecols=["trip_id", "stop_id", "stop_sequence"])
    st["stop_sequence"] = st.stop_sequence.astype(int)
    rep = trips.groupby("shape_id").agg(trip=("trip_id", "first"), route=("route_id", "first"), n=("trip_id", "size")).reset_index()
    st = st[st.trip_id.isin(rep.trip)]
    seqs = {t: g.sort_values("stop_sequence").stop_id.map(lambda s: parent.get(s) or s).tolist() for t, g in st.groupby("trip_id")}
    shapes = pd.read_csv(G / "shapes.txt")
    sxy = to_utm(shapes.shape_pt_lon.values, shapes.shape_pt_lat.values)
    shapes["x"], shapes["y"] = sxy[:, 0], sxy[:, 1]
    geo = {sid: g.sort_values("shape_pt_sequence")[["x", "y"]].values for sid, g in shapes.groupby("shape_id")}
    edges, shape_seq = {}, {}
    for r in rep.sort_values("n", ascending=False).itertuples():
        if r.shape_id not in geo:
            continue
        xy = densify(geo[r.shape_id], 10.0)
        seq = seqs[r.trip]
        idx, prev = [], 0
        for s in seq:
            d = np.hypot(*(xy[prev:] - pxy[s]).T)
            k = prev + int(np.argmin(d))
            idx.append(k)
            prev = k
        shape_seq[r.shape_id] = {"route": r.route, "stops": seq, "idx": idx, "xy": xy, "n": r.n}
        for (a, ia), (b, ib) in zip(zip(seq[:-1], idx[:-1]), zip(seq[1:], idx[1:])):
            key = (a, b) if (a, b) in edges or (b, a) not in edges else (b, a)
            if key in edges or ib - ia < 2:
                continue
            edges[(a, b)] = {"xy": xy[ia:ib + 1], "shape": r.shape_id, "route": r.route, "len": (ib - ia) * 10.0}
    return pxy, edges, shape_seq


def drop_covered(edges):
    """Express stretches that only repeat shorter (local) stretches."""
    keys = sorted(edges, key=lambda k: edges[k]["len"])
    pts, own = [], []
    for i, k in enumerate(keys):
        pts.append(edges[k]["xy"])
        own.append(np.full(len(edges[k]["xy"]), i))
    P, O = np.concatenate(pts), np.concatenate(own)
    tree = cKDTree(P)
    keep = {}
    for i, k in enumerate(keys):
        e = edges[k]
        nb = tree.query_ball_point(e["xy"], 30.0)
        cov = np.mean([any(edges[keys[O[j]]]["len"] < 0.9 * e["len"] and O[j] != i for j in idx) for idx in nb])
        if cov < 0.93 or k in KEEP or k[::-1] in KEEP:
            keep[k] = e
    return keep


def main():
    stn = pd.read_csv(INT / "transit_stations_draft.csv", dtype=str, keep_default_na=False)
    cur = stn[stn.system.isin(["subway", "sir"]) & (stn.closed == "") & ~stn.code.str.startswith("Q" + "")]
    cur = stn[stn.system.isin(["subway", "sir"]) & (stn.closed == "")]
    sdate = {r.code: r.opened for r in cur.itertuples() if r.opened}
    sname = dict(zip(cur.code, cur.name))
    sline = dict(zip(cur.code, cur.line))
    pxy, edges, shape_seq = load_network()
    edges = drop_covered(edges)
    print(f"{len(edges)} stretches between neighbouring stations", file=sys.stderr)

    # neighbours of every station (over the kept stretches) for the infill test
    nbr = defaultdict(set)
    for a, b in edges:
        nbr[a].add(b)
        nbr[b].add(a)
    infill = {}
    for s, ns in nbr.items():
        if len(ns) >= 2 and s in sdate:
            others = sorted(sdate[n] for n in ns if n in sdate)
            if others and sdate[s] > others[-1] and decyear(sdate[s]) - decyear(others[-1]) > 0.02:
                infill[s] = others[-1]
    date, why = {}, {}
    for (a, b), e in edges.items():
        fx = FIX.get((a, b)) or FIX.get((b, a))
        if (a, b) in SPLIT or (b, a) in SPLIT:
            date[(a, b)], why[(a, b)] = "split", ("split", "", "")
            continue
        if fx:
            date[(a, b)], why[(a, b)] = fx[0], ("fix", fx[1], fx[2])
            continue
        da = infill.get(a, sdate.get(a, ""))
        db = infill.get(b, sdate.get(b, ""))
        if a in infill and b in infill:
            da, db = sdate[a], sdate[b]
        d = max(da, db)
        date[(a, b)] = d
        why[(a, b)] = ("auto", "", "")
    print("infill stations (track older than the platforms):", file=sys.stderr)
    for s, d in sorted(infill.items()):
        print(f"   {s:4s} {sname.get(s, '')[:28]:28s} station {sdate[s]}  track {d}", file=sys.stderr)

    # rows: runs of equal date along each shape (most used shapes first), each stretch once
    done, rows = set(), []
    for sid, sq in sorted(shape_seq.items(), key=lambda kv: -kv[1]["n"]):
        run = None
        for a, b in zip(sq["stops"][:-1], sq["stops"][1:]):
            key = (a, b) if (a, b) in edges else (b, a) if (b, a) in edges else None
            if key is None or key in done:
                run = None
                continue
            done.add(key)
            d, w = date[key], why[key]
            if run and run["opened"] == d and run["why"] == w and run["to"] == a:
                run["to"] = b
                run["keys"].append(key)
            else:
                run = {"from": a, "to": b, "opened": d, "why": w, "via": sid, "route": sq["route"], "keys": [key]}
                rows.append(run)

    # OHM cross-check
    ohm = json.load(open(RAW / "ohm" / "ohm_rail.json"))
    op, od = [], []
    for w in ohm["elements"]:
        t = w.get("tags", {})
        if w["type"] != "way" or t.get("railway") not in ("subway", "rail", "light_rail") or t.get("end_date") or not t.get("start_date"):
            continue
        g = w["geometry"]
        xy = densify(to_utm(np.array([p["lon"] for p in g]), np.array([p["lat"] for p in g])), 15.0)
        op.append(xy)
        od += [t["start_date"]] * len(xy)
    otree = cKDTree(np.concatenate(op))
    od = np.array(od)

    def ohm_year(s):
        s = s.strip()
        try:
            if len(s) == 4:
                return float(s) + 0.5
            if len(s) == 7:
                return decyear(s + "-15")
            return decyear(s[:10])
        except ValueError:
            return np.nan

    out = []
    for r in rows:
        xy = np.concatenate([edges[k]["xy"] for k in r["keys"]])
        dd, ii = otree.query(xy, distance_upper_bound=14.0)
        ok = np.isfinite(dd)
        oh = Counter(od[ii[ok]]).most_common(3) if ok.any() else []
        line = sline.get(r["from"], "")
        mta_line = line.split(" ", 1)[1] if " " in line else line
        kind, note, src = r["why"]
        if kind == "split":
            a, b = r["keys"][0]
            lon, lat, p1, p2 = SPLIT.get((a, b)) or SPLIT[(b, a)]
            if (b, a) in SPLIT:
                p1, p2 = p2, p1
            cut = f"{lon} {lat}"
            for (d_, n_, s_), f_, t_ in ((p1, r["from"], cut), (p2, cut, r["to"])):
                out.append({"route_id": f"subway_{r['from']}_{r['to']}_{d_[:4]}", "opened": d_, "note": n_, "source": s_, "system": "subway",
                            "line": line, "from_stop": f_, "to_stop": t_, "via": r["via"], "closed": "", "km": 0, "ohm": "", "kind": "split",
                            "from_name": sname.get(f_, f_), "to_name": sname.get(t_, t_)})
            continue
        note = note or f"{sname.get(r['from'], r['from'])} - {sname.get(r['to'], r['to'])}"
        src = src or WP + LINE_ARTICLE.get(mta_line, "New_York_City_Subway")
        system = "sir" if r["route"] == "SI" else "subway"
        rid = f"{system}_{r['from']}_{r['to']}"
        km = sum(edges[k]["len"] for k in r["keys"]) / 1000
        out.append({"route_id": rid, "opened": r["opened"], "note": note, "source": src, "system": system, "line": line,
                    "from_stop": r["from"], "to_stop": r["to"], "via": r["via"], "closed": "", "km": round(km, 2),
                    "ohm": "|".join(f"{a}x{b}" for a, b in oh), "kind": kind,
                    "from_name": sname.get(r["from"], ""), "to_name": sname.get(r["to"], "")})
        if oh and r["opened"]:
            y = ohm_year(oh[0][0])
            if np.isfinite(y) and abs(y - decyear(r["opened"])) > 0.3 and not (len(oh[0][0]) == 4 and oh[0][0] == r["opened"][:4]):
                print(f"   CHECK {rid:22s} {note[:44]:44s} table {r['opened']}  OHM {out[-1]['ohm'][:60]}", file=sys.stderr)
    df = pd.DataFrame(out)
    df.to_csv(INT / "transit_openings_draft.csv", index=False)
    cols = ["route_id", "opened", "note", "source", "system", "line", "from_stop", "to_stop", "via", "closed"]
    final = df.sort_values(["system", "line", "opened", "route_id"])[cols]
    keep_path = ROOT / "data" / "tables" / "transit_openings.csv"
    if keep_path.exists():  # rows of other systems (elevated, railroads) are kept as they are
        old = pd.read_csv(keep_path, dtype=str, keep_default_na=False)
        final = pd.concat([final, old[~old.system.isin(["subway", "sir"])]], ignore_index=True)
    final.to_csv(keep_path, index=False)
    print(f"{len(df)} rows, {df.km.sum():.0f} km; no date: {(df.opened == '').sum()}", file=sys.stderr)


if __name__ == "__main__":
    main()
