"""Town centres for places_outer.csv from OpenStreetMap's place points (Overture divisions).

The table's coordinates were checked against the Census gazetteer, whose point for a
municipality is an interior point of its outline: Princeton's lies 900 m north-west of Nassau
Street, in a field. A label, and the colonial town generated around it (early_counties.csv),
belong at the centre. The place points come from Overture's divisions theme (localities: the
position of OpenStreetMap's place node), fetched once for the map's box:

  python recentre_places.py fetch     # data/raw/overture/<release>/outer_divisions.parquet (2 s)
  python recentre_places.py report    # what would move, and how far
  python recentre_places.py apply     # write places_outer.csv (moves of 150 m to 6 km)

After `apply`: regenerate the colonial towns (data/research/early_counties_build: rot2.py,
shift.py, gen.py) - they are placed around these points.
"""
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TABLE = HERE.parent / "places_outer.csv"
RELEASE = "2026-10-21.0"
DIV = ROOT / "data" / "raw" / "overture" / RELEASE / "outer_divisions.parquet"
BOX = (-75.37, 39.47, -71.85, 42.20)
MIN_M, MAX_M = 150.0, 6000.0


def fetch():
    import duckdb
    con = duckdb.connect()
    con.execute("SET memory_limit='1500MB'; INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial;")
    con.execute("CREATE OR REPLACE SECRET overture (TYPE s3, PROVIDER config, KEY_ID '', SECRET '', REGION 'us-west-2');")
    src = f"s3://overturemaps-us-west-2/release/{RELEASE}/theme=divisions/type=division/*"
    w, s, e, n = BOX
    con.execute(f"""COPY (SELECT id, names.primary AS name, subtype, class, country, region, population,
                                 ST_X(geometry) AS lon, ST_Y(geometry) AS lat
                          FROM read_parquet('{src}', hive_partitioning=1)
                          WHERE bbox.xmin >= {w} AND bbox.xmax <= {e} AND bbox.ymin >= {s} AND bbox.ymax <= {n})
                    TO '{DIV}' (FORMAT PARQUET)""")
    print(con.execute(f"select subtype, count(*) from '{DIV}' group by 1 order by 2 desc").fetchall())


def key(name):
    s = str(name).lower()
    s = re.sub(r"\b(township|borough|village|city|town) of\b|\b(township|borough|village|cdp)\b", "", s)
    return re.sub(r"[^a-z]", "", s)


def dist_m(lat1, lon1, lat2, lon2):
    return np.hypot((lat2 - lat1) * 110540.0, (lon2 - lon1) * 111320.0 * math.cos(math.radians(lat1)))


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "report"
    if what == "fetch":
        return fetch()
    t = pd.read_csv(TABLE)
    d = pd.read_parquet(DIV)
    d = d[d.subtype.isin(["locality", "neighborhood"])].copy()
    # (a point at whole hundredths of a degree is a stand-in, not a place node: Southeast, Putnam County)
    d = d[~(((d.lat * 100).round(6) % 1 == 0) & ((d.lon * 100).round(6) % 1 == 0))]
    d["k"] = d.name.map(key)
    by = {k: g for k, g in d.groupby("k")}
    rows = []
    for r in t.itertuples():
        g = by.get(key(r.name))
        if g is None:
            rows.append((r.id, r.name, r.county, np.nan, np.nan, np.nan, "no place of that name"))
            continue
        dm = dist_m(float(r.lat), float(r.lon), g.lat.values, g.lon.values)
        # (a locality before a neighbourhood of the same name)
        order = np.lexsort((dm, (g.subtype.values != "locality").astype(int)))
        j = next((i for i in order if dm[i] <= MAX_M), None)
        if j is None:
            rows.append((r.id, r.name, r.county, np.nan, np.nan, float(dm.min()), "nearest of that name is further than 6 km"))
            continue
        rows.append((r.id, r.name, r.county, float(g.lat.values[j]), float(g.lon.values[j]), float(dm[j]),
                     f"{g.subtype.values[j]}:{g['class'].values[j]}"))
    rep = pd.DataFrame(rows, columns=["id", "name", "county", "lat", "lon", "moved_m", "what"])
    move = rep[rep.lat.notna() & (rep.moved_m >= MIN_M)]
    print(f"{len(rep)} places: {int(rep.lat.notna().sum())} matched, {len(move)} move by 150 m or more, {int(rep.lat.isna().sum())} unmatched")
    print("moves over 1.5 km:")
    print(move[move.moved_m > 1500].sort_values("moved_m", ascending=False).to_string(index=False, float_format=lambda v: f"{v:.5f}" if abs(v) < 200 else f"{v:.0f}"))
    print("unmatched:", ", ".join(rep[rep.lat.isna()].name.tolist()))
    print("moved_m quartiles:", move.moved_m.quantile([0.25, 0.5, 0.75, 0.95]).round().tolist())
    if what == "apply":
        m = move.set_index("id")
        for i, r in t.iterrows():
            if r.id in m.index:
                t.at[i, "lat"] = round(float(m.at[r.id, "lat"]), 5)
                t.at[i, "lon"] = round(float(m.at[r.id, "lon"]), 5)
                note = str(r.note) if isinstance(r.note, str) else ""
                t.at[i, "note"] = (note + "; " if note else "") + f"centre: OpenStreetMap's place point (moved {m.at[r.id, 'moved_m']:.0f} m from the gazetteer's interior point)"
        t.to_csv(TABLE, index=False)
        print("written", TABLE)


if __name__ == "__main__":
    main()
