"""Checks on the three built transit files (run after pipeline/transit.py):
every GTFS station has a row and is in the viewer file; years inside 1830..today; no path or
station with start >= end; everything inside the map box; no line vertex without a year."""
import gzip, json, struct, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
V = ROOT / "viewer" / "public" / "data"
BOX = (-74.52, 40.47, -73.40, 41.38)  # common.REGION_BBOX (the outline itself: check_counties.py)
ok = True

def fail(msg):
    global ok
    ok = False
    print("FAIL", msg)

raw = gzip.open(V / "transit.bin.gz").read()
hl = struct.unpack("<I", raw[4:8])[0]
hd = json.loads(raw[8:8 + hl])
base = 8 + hl
col = {}
for c in hd["columns"]:
    dt = {"f32": "<f4", "u32": "<u4", "u8": "u1"}[c["dtype"]]
    n = c["length"]
    b = raw[base + c["offset"]: base + c["offset"] + n * np.dtype(dt).itemsize]
    if c["shuffle"]:
        b = np.frombuffer(b, np.uint8).reshape(np.dtype(dt).itemsize, n).T.copy().tobytes()
    col[c["name"]] = np.frombuffer(b, dt)
pos = col["positions"].reshape(-1, 3)
lon, lat = pos[:, 0] + hd["origin"][0], pos[:, 1] + hd["origin"][1]
yrs = col["years"].reshape(-1, 2)
print(f"transit.bin.gz: {hd['counts']} bbox {lon.min():.3f} {lat.min():.3f} {lon.max():.3f} {lat.max():.3f} "
      f"years {yrs[:, 0].min():.2f}..{yrs[:, 0].max():.2f} z {pos[:, 2].min():.1f}..{pos[:, 2].max():.1f}")
if lon.min() < BOX[0] or lat.min() < BOX[1] or lon.max() > BOX[2] or lat.max() > BOX[3]:
    fail("paths outside the map box")
if (yrs[:, 0] >= yrs[:, 1]).any():
    fail(f"{(yrs[:, 0] >= yrs[:, 1]).sum()} paths with start >= end")
if yrs[:, 0].min() < 1830 or yrs[:, 0].max() > 2026.99 or not np.isfinite(yrs).all():
    fail("path years out of range")
st = np.diff(col["start_indices"])
if (st < 2).any():
    fail("paths with fewer than 2 vertices")
print("  kinds", dict(zip(*np.unique(col["kind"], return_counts=True))), "elevated", dict(zip(*np.unique(col["elevated"], return_counts=True))),
      "with an end year", int((yrs[:, 1] < 9000).sum()))

m = json.load(open(V / "transit-lines.json"))
nv = 0
for l in m["lines"]:
    n = len(l["lon"])
    nv += n
    for k in ("lat", "z", "cum", "year", "tunnel", "half"):
        if len(l[k]) != n:
            fail(f"line {l['id']}: {k} length")
    y = np.array(l["year"], float)
    if not np.isfinite(y).all() or y.min() < 1830 or y.max() > 2026.99:
        fail(f"line {l['id']}: years {y.min()} {y.max()}")
    if n > 16000 or len(l["knots"]) > 500:
        fail(f"line {l['id']}: too long for the shader's search ({n} vertices, {len(l['knots'])} knots)")
    if l["veh"] not in m["vehicles"]:
        fail(f"line {l['id']}: vehicle {l['veh']}")
    k = np.array(l["knots"])
    if (np.diff(k[:, 0]) <= 0).any() or (np.diff(k[:, 1]) <= 0).any():
        fail(f"line {l['id']}: knots not increasing")
print(f"transit-lines.json: {len(m['lines'])} lines, {nv} vertices, texture rows {int(np.ceil((2 * nv + sum(len(l['knots']) for l in m['lines'])) / 2048))}")

s = pd.DataFrame(json.load(open(V / "transit-stations.json")))
tab = pd.read_csv(ROOT / "data" / "tables" / "transit_stations.csv", dtype=str, keep_default_na=False)
gt = pd.read_csv(ROOT / "data" / "raw" / "transit" / "gtfs" / "stops.txt", dtype=str)
par = set(gt[gt.location_type == "1"].stop_id)
print(f"transit-stations.json: {len(s)} stations; GTFS parents {len(par)}, in table {len(par & set(tab.code))}, in viewer file {len(par & set(s.code))}")
if par - set(tab.code):
    fail(f"GTFS stations without a table row: {sorted(par - set(tab.code))}")
if par - set(s.code):
    fail(f"GTFS stations missing from the viewer file: {sorted(par - set(s.code))}")
if (s.start >= s.end).any():
    fail("stations with start >= end")
if s.start.min() < 1830 or s.start.max() > 2026.99:
    fail(f"station years {s.start.min()} {s.start.max()}")
if (s.lon < BOX[0]).any() or (s.lon > BOX[2]).any() or (s.lat < BOX[1]).any() or (s.lat > BOX[3]).any():
    fail("stations outside the map box")
ids = {l["id"] for l in m["lines"]}
if not set(s.line) <= ids:
    fail("stations on unknown lines")
print("  by system/kind", s.groupby(["system", "kind"]).size().to_dict(), "closed", int((s.end < 9000).sum()), "renamed", int(s.get("names").notna().sum()) if "names" in s else 0)
print("OK" if ok else "CHECKS FAILED")
sys.exit(0 if ok else 1)
