"""What the marks say about the old villages (numbers for data/research/farmsteads_years.md).

  python -I districts.py [radius_m=700]

Per district (centre = the old village's church or crossroads, coordinates from memory of today's
map: estimated, good to a block or two): the marks of the sheets within the radius, and what the built
model (data/interim/nyc_buildings.parquet) has standing there in the survey years.
"""
import json
import sys
from pathlib import Path

import duckdb
import numpy as np
import pyproj

ROOT = Path(__file__).resolve().parents[4]
DISTRICTS = [   # name, borough, lon, lat (estimated centres)
    ("Gravesend", "Brooklyn", -73.9720, 40.5960), ("Flatlands", "Brooklyn", -73.9355, 40.6245), ("New Utrecht", "Brooklyn", -74.0005, 40.6088),
    ("Flatbush", "Brooklyn", -73.9590, 40.6502), ("Bushwick", "Brooklyn", -73.9413, 40.7155), ("Newtown (Elmhurst)", "Queens", -73.8785, 40.7375),
    ("Jamaica", "Queens", -73.7985, 40.7035), ("Flushing", "Queens", -73.8300, 40.7630), ("College Point", "Queens", -73.8460, 40.7860),
    ("Richmondtown", "Staten Island", -74.1455, 40.5712), ("Tottenville", "Staten Island", -74.2430, 40.5115),
    ("Westchester Square", "Bronx", -73.8425, 40.8395), ("Williamsbridge", "Bronx", -73.8640, 40.8780), ("Kingsbridge", "Bronx", -73.9050, 40.8790),
]
R = float(sys.argv[1]) if len(sys.argv) > 1 else 700.0
utm = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32618", always_xy=True)
fc = json.loads((ROOT / "data/manual/farmsteads/farmsteads.geojson").read_text())["features"]
P = np.array([f["geometry"]["coordinates"] for f in fc])
E, N = utm.transform(P[:, 0], P[:, 1])
pr = [f["properties"] for f in fc]
con = duckdb.connect()
bp = ROOT / "data/interim/nyc_buildings.parquet"
print("| District | marks 1889 | marks 1897 | of them in the built-up extent | model: standing in 1889 | in 1897 | in 1930 | today's footprints | today's with an estimated year after 1897 | marks on a `recorded` footprint | on a `by_then` footprint (strong) | gone by 1947-57 |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|")
for name, boro, lon, lat in DISTRICTS:
    e0, n0 = utm.transform(lon, lat)
    m = np.hypot(E - e0, N - n0) <= R
    sel = [p for p, k in zip(pr, m) if k]
    n89 = sum(p["first_year"] == 1889 for p in sel)
    n97 = sum(p["last_year"] == 1897 for p in sel)
    bu = sum(bool(p["builtup"]) for p in sel)
    rec = sum(p["standing_basis"] == "recorded" for p in sel)
    byt = sum(p["standing_basis"] == "by_then" for p in sel)
    bys = sum(p["standing_basis"] == "by_then" and p["standing_strength"] == "strong" for p in sel)
    gone = sum(p["gone_by"] is not None and p["gone_by"] >= 1947 for p in sel)
    dlon, dlat = R / (111320 * np.cos(np.radians(lat))), R / 110950
    q = f"""select start_year, end_year, year_confidence, lon, lat from '{bp}'
            where lon between {lon - dlon} and {lon + dlon} and lat between {lat - dlat} and {lat + dlat}"""
    b = con.execute(q).df()
    be, bn = utm.transform(b["lon"].values, b["lat"].values)
    b = b[np.hypot(be - e0, bn - n0) <= R]
    st = lambda y: int(((b["start_year"] <= y) & (b["end_year"] > y)).sum())
    today = b[b["end_year"] == 9999]
    late_est = int(((today["year_confidence"] != "exact") & (today["start_year"] > 1897)).sum())
    print(f"| {name} | {n89 if boro in ('Brooklyn', 'Queens', 'Bronx') else 'no sheet'} | {n97} | {bu} | {st(1889)} | {st(1897)} | {st(1930)} | {len(today)} | {late_est} | {rec} | {byt} ({bys}) | {gone} |")
