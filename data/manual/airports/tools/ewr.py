"""Newark Liberty International Airport: pavement by period -> rows of ../pavement_dates.csv
(airport = EWR) and three zones of ../pavement_zones.geojson (zone = ewr_*).

Cited (https://en.wikipedia.org/wiki/Newark_Liberty_International_Airport, read 2026-11-10):
  * "The airport opened on October 1, 1928" on "68 acre of level ground ... upon which a
    1600 ft runway was to be laid" — that first runway and runways 1/19 and 6/24 (closed
    1952) are gone and NOT traced.
  * "In 1952, Runways 1/19 and 6/24 were closed and a new Runway 4/22 (now 4R/22L) opened at
    a length of 7000 ft. After 1970, this runway was extended to 9800 ft ..." ("Newark
    remained closed until November 1952, with ... a new runway").
  * "Runway 4L/22R opened in 1970 at a length of 8200 ft and was extended to its current
    length by 2000."
  * "... lost a cylinder on takeoff from runway 28" (16 December 1951): today's 11/29 was
    in use by then; its year of construction was not found -> 1951, ESTIMATED ("by then").
  * "Former Terminal A and present Terminal B opened in 1973"; "Terminal C was then
    completed, and opened in June 1988"; "The new Terminal A officially opened on December 8,
    2022"; North Terminal 1953-1997 ("the opening of the North Terminal in 1953").
ESTIMATED (every row says so): the runway lengthenings are not separated; a taxiway takes
the year of the runway it lies nearest to; the one apron polygon of the central terminal
area is cut by latitude between the terminal buildings (Overture building centres: C
40.6963, B 40.6900, former A 40.6877, new A 40.6840) into Terminal C (1988), A / B (1973)
and new Terminal A (2022.9, only within ~500 m of the new building) and taxiways west of runway 4L/22R follow those bands; the
north cargo apron (site of the North Terminal) 1953. The two aprons by Building One (the
1935 administration building's area) keep the airport's opening year.
Run: ../../../../.venv/bin/python ewr.py   (idempotent: replaces the EWR rows / ewr_ zones)."""
import csv, json, sys
from pathlib import Path
import geopandas as gpd, numpy as np, pandas as pd, shapely
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "pipeline"))
from common import NYC_CRS, OVERTURE_RELEASE, RAW  # noqa: E402
URL = "https://en.wikipedia.org/wiki/Newark_Liberty_International_Airport"
R4L = {"16acc162-283e-373a-a09b-9d5bd41fb6d4", "d5932d73-66f5-3768-9f83-56c19870bcb5", "923ac889-3a1e-399c-b7b0-6a23940890b4",
       "7699a0d0-a5b9-3496-8b71-d7c6a2d8128f", "f1c984d5-9d9d-34db-b66e-fa45fdf629ca", "b26d0712-a2f1-3e69-833c-ff99f6240be1"}
R4R = {"b134c1f0-161b-366c-9dd7-fe3c17ee7a22", "62ba45ab-e343-3d51-9514-864b256d70ed", "5cfd4da9-0242-3e82-a902-91278bb58efb",
       "42db52c9-fdc7-3ec7-9de8-c133dc0095ab", "5f71bae5-a575-35e4-be6b-942e160edba1"}
R11 = {"e58b319e-09ab-3fa6-a015-9821605258e3", "1ca92ac9-2efb-3660-a92f-673d00364721", "a76b4adc-3609-3a2b-8031-dbac4d786136",
       "91aa44ce-730b-33bd-a4b2-c51ef8c89b73"}
GROUPS = {"4L/22R": (R4L, 1970.0, "'Runway 4L/22R opened in 1970 at a length of 8200 ft and was extended to its current length by 2000' — the extension is not separated (estimated for the added part)"),
          "4R/22L": (R4R, 1952.85, "'In 1952, Runways 1/19 and 6/24 were closed and a new Runway 4/22 (now 4R/22L) opened at a length of 7000 ft' (airport reopened November 1952); the later lengthening is not separated (estimated for the added part)"),
          "11/29": (R11, 1951.0, "ESTIMATED 'by then': in use as runway 28 on 16 December 1951 ('lost a cylinder on takeoff from runway 28'); its year of construction was not found")}
BIG_APRON = "45291dcc-f3e9-3eb0-939a-9b83a4202a29"
NORTH_CARGO = "c4b7ff4c-f8a4-36b1-ba8c-1e4bebd436e8"
OLD_AREA = {"ad7b7ba5-18f8-3164-935b-0bd540bfdc1d", "d83d5fc6-5dee-3ecd-8508-a7f4b7492cdf"}   # by Building One: airport opening year
BANDS = [("ewr_terminal_c", 40.6932, 40.7005, 1988.45, "'Terminal C was then completed, and opened in June 1988'"),
         ("ewr_terminal_ab", 40.6858, 40.6932, 1973.0, "'Former Terminal A and present Terminal B opened in 1973'"),
         ("ewr_terminal_a_new", 40.6810, 40.6858, 2022.9, "'The new Terminal A officially opened on December 8, 2022'")]
NEW_A = (-74.1855, 40.6840)   # centre of the new Terminal A building (Overture): its band holds only what lies within ~500 m

a = pd.read_parquet(RAW / "overture" / OVERTURE_RELEASE / "region_airports.parquet")
g = gpd.GeoDataFrame(a, geometry=gpd.GeoSeries.from_wkb(a.geometry), crs=4326).to_crs(NYC_CRS)
ewr = g[(g["class"] == "international_airport") & g["name"].str.contains("Newark", na=False)].geometry.iloc[0]
f = g[g["class"].isin(["runway", "stopway", "taxiway", "taxilane", "apron"]) & (g.geometry.distance(ewr) < 350)].copy()
axis = {k: shapely.union_all(f[f.id.isin(ids)].geometry.values) for k, (ids, _, _) in GROUPS.items()}
ll = f.to_crs(4326)
west_of_4l = shapely.union_all(f[f.id.isin(R4L)].geometry.values).buffer(150, single_sided=True)   # either side: tested by longitude below
cols = ["airport", "feature_class", "overture_id", "runway", "name", "lon", "lat", "part", "clip_zone", "from_end", "d0_m", "d1_m",
        "part_lon0", "part_lat0", "part_lon1", "part_lat1", "start_year", "end_year", "confidence", "source_url", "evidence"]
rows = []
def row(r, c, part, zone, year, conf, ev, rw=""):
    rows.append({"airport": "EWR", "feature_class": r["class"], "overture_id": r["id"], "runway": rw, "name": r["name"] if isinstance(r["name"], str) else "",
                 "lon": round(c.x, 6), "lat": round(c.y, 6), "part": part, "clip_zone": zone, "start_year": year, "end_year": 9999,
                 "confidence": conf, "source_url": URL, "evidence": ev})
# longitude of runway 4L/22R's axis at a latitude (its west side is the terminal area)
l4 = np.asarray(ll[ll.id == "16acc162-283e-373a-a09b-9d5bd41fb6d4"].geometry.iloc[0].coords)
def lon_4l(lat):
    return np.interp(lat, sorted(l4[:, 1]), l4[np.argsort(l4[:, 1]), 0])
for (_, r), gu, gl in zip(f.iterrows(), f.geometry.values, ll.geometry.values):
    c = gl.representative_point() if gl.geom_type == "Polygon" else gl.interpolate(0.5, normalized=True)
    grp = next((k for k, (ids, _, _) in GROUPS.items() if r["id"] in ids), None)
    if grp:
        _, y, ev = GROUPS[grp]
        main = r["class"] == "runway" and gu.length > 1500
        row(r, c, "whole", "", y, "documented" if main and grp != "11/29" else "estimated", ev if main else f"part of runway {grp}: {ev}", grp)
        continue
    if r["id"] == BIG_APRON:
        for z, _y0, _y1, y, ev in BANDS:
            row(r, c, "zone_clip", z, y, "estimated", f"central terminal area, cut by latitude between the terminal buildings (ESTIMATED extent): {ev}")
        continue
    if r["id"] in OLD_AREA:
        continue
    if r["id"] == NORTH_CARGO:
        row(r, c, "whole", "", 1953.0, "estimated", "ESTIMATED: the north cargo apron lies on the North Terminal's site — 'the opening of the North Terminal in 1953'; "
            "'In 1997, the North Terminal was torn down to make a new air cargo facility' (today's outline is the cargo apron's)")
        continue
    near = min(GROUPS, key=lambda k: gu.distance(axis[k]))
    y, ev = GROUPS[near][1], f"ESTIMATED: nearest runway is {near} ({GROUPS[near][1]:.0f}); taxiways and aprons are dated with the runway they serve"
    band = next((b for b in BANDS if b[1] <= c.y < b[2]), None)
    if band and band[0] == "ewr_terminal_a_new" and np.hypot((c.x - NEW_A[0]) * 0.758, c.y - NEW_A[1]) > 0.0045:
        band = None
    if band and c.x < lon_4l(c.y) - 0.0018:   # more than ~150 m west of runway 4L/22R: the terminal area
        y, ev = max(y, band[3]), f"ESTIMATED: in the central terminal area — {band[4]}"
    row(r, c, "whole", "", y, "estimated", ev)
p = HERE.parent / "pavement_dates.csv"
old = pd.read_csv(p, dtype=str, keep_default_na=False)
old = old[old.airport != "EWR"]
out = pd.concat([old, pd.DataFrame(rows, columns=cols).astype(object).where(lambda d: d.notna(), "")], ignore_index=True)
out.to_csv(p, index=False, quoting=csv.QUOTE_MINIMAL)
zp = HERE.parent / "pavement_zones.geojson"
z = json.loads(zp.read_text())
z["features"] = [ft for ft in z["features"] if not str(ft["properties"].get("zone", "")).startswith("ewr_")]
for name, y0, y1, year, ev in BANDS:
    z["features"].append({"type": "Feature", "properties": {"zone": name, "start_year": year, "source_url": URL, "note": f"latitude band {y0}-{y1} (ESTIMATED extent): {ev}"},
                          "geometry": {"type": "Polygon", "coordinates": [[[-74.20, y0], [-74.15, y0], [-74.15, y1], [-74.20, y1], [-74.20, y0]]]}})
zp.write_text(json.dumps(z))
d = pd.DataFrame(rows)
print(len(rows), "EWR rows;", d.groupby(["feature_class", "start_year"]).size().to_dict())
