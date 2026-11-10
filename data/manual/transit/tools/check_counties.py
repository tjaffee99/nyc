"""Checks after extending the stage to the counties (run after pipeline/transit.py):
  * nothing outside the map outline (extent ring + the stage's 0.004 degree margin); no path, line or station
    with start >= end; years inside 1830..today;
  * the city's subway output against a copy made before the change (data/interim/transit/before/, if it is
    there): service lines and stations of the subway, the Staten Island Railway and the elevated lines;
  * the counties' stations by system: how many carry a cited day, an estimated one, their track's year.

    ../../../../.venv/bin/python check_counties.py
"""
import gzip
import json
import struct
from pathlib import Path

import numpy as np
import pandas as pd
import shapely
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[4]
V = ROOT / "viewer" / "public" / "data"
B = ROOT / "data" / "interim" / "transit" / "before"
poly = Polygon(json.load(open(ROOT / "data" / "manual" / "extent_ring.json"))["ring"]).buffer(0.004 + 1e-6)
city = Polygon(json.load(open(ROOT / "data" / "manual" / "transit" / "city_ring.json"))["ring"]).buffer(0.004)
ok = True


def fail(msg):
    global ok
    ok = False
    print("FAIL", msg)


def read_bin(f):
    raw = gzip.open(f).read()
    hl = struct.unpack("<I", raw[4:8])[0]
    hd = json.loads(raw[8:8 + hl])
    col = {}
    for c in hd["columns"]:
        dt = {"f32": "<f4", "u32": "<u4", "u8": "u1"}[c["dtype"]]
        n = c["length"]
        b = raw[8 + hl + c["offset"]: 8 + hl + c["offset"] + n * np.dtype(dt).itemsize]
        if c["shuffle"]:
            b = np.frombuffer(b, np.uint8).reshape(np.dtype(dt).itemsize, n).T.copy().tobytes()
        col[c["name"]] = np.frombuffer(b, dt)
    pos = col["positions"].reshape(-1, 3)
    return hd, col, pos[:, 0].astype(float) + hd["origin"][0], pos[:, 1].astype(float) + hd["origin"][1], col["years"].reshape(-1, 2)


hd, col, lon, lat, yrs = read_bin(V / "transit.bin.gz")
inside = shapely.contains_xy(poly, lon, lat)
print(f"transit.bin.gz: {hd['counts']}; vertices outside the outline: {int((~inside).sum())}; start >= end: {int((yrs[:, 0] >= yrs[:, 1]).sum())}; "
      f"years {yrs[:, 0].min():.2f}..{yrs[:, 0].max():.2f}")
if (~inside).any():
    fail("path vertices outside the outline")
if (yrs[:, 0] >= yrs[:, 1]).any() or yrs[:, 0].min() < 1830 or yrs[:, 0].max() > 2026.99 or not np.isfinite(yrs).all():
    fail("path years")
st = col["start_indices"]
mid = (st[:-1] + st[1:]) // 2
cty = ~shapely.contains_xy(city, lon[mid], lat[mid])
seg = np.hypot(np.diff(lon) * 84400, np.diff(lat) * 111320)
seg[st[1:-1] - 1] = 0
plen = np.add.reduceat(seg, st[:-1]) / 1000
for kind, name in ((6, "railroad"), (8, "subway / el / PATH"), (10, "light rail")):
    m = col["kind"] == kind
    gone = yrs[:, 1] < 9000
    print(f"  {name}: city {plen[m & ~cty & ~gone].sum():.0f} km standing, {plen[m & ~cty & gone].sum():.0f} km gone; "
          f"counties {plen[m & cty & ~gone].sum():.0f} km standing, {plen[m & cty & gone].sum():.0f} km gone")

m = json.load(open(V / "transit-lines.json"))
nv = sum(len(l["lon"]) for l in m["lines"])
for l in m["lines"]:
    y = np.array(l["year"], float)
    lo, la = np.array(l["lon"]) + m["origin"][0], np.array(l["lat"]) + m["origin"][1]
    k = np.array(l["knots"])
    if not shapely.contains_xy(poly, lo, la).all():
        fail(f"line {l['id']} leaves the outline")
    if not np.isfinite(y).all() or y.min() < 1830 or y.max() > 2026.99 or len(l["lon"]) > 16000 or len(k) > 500 or l["veh"] not in m["vehicles"]:
        fail(f"line {l['id']}: years / size / vehicle")
    if (np.diff(k[:, 0]) <= 0).any() or (np.diff(k[:, 1]) <= 0).any():
        fail(f"line {l['id']}: knots not increasing")
    if l.get("gap") and min(y) >= l["gap"][0]:
        fail(f"line {l['id']}: opens after it closed")
print(f"transit-lines.json: {len(m['lines'])} lines, {nv} vertices, texture rows {int(np.ceil((2 * nv + sum(len(l['knots']) for l in m['lines'])) / 2048))}")

s = pd.DataFrame(json.load(open(V / "transit-stations.json")))
out = ~shapely.contains_xy(poly, s.lon.values, s.lat.values)
print(f"transit-stations.json: {len(s)} stations; outside the outline {int(out.sum())}; start >= end {int((s.start >= s.end).sum())}; "
      f"years {s.start.min():.2f}..{s.start.max():.2f}")
if out.any() or (s.start >= s.end).any() or s.start.min() < 1830 or s.start.max() > 2026.99:
    fail("stations")
tab = pd.read_csv(ROOT / "data" / "tables" / "transit_stations.csv", dtype=str, keep_default_na=False)
c = tab[tab.note.str.startswith("[counties]")].copy()
c["in_file"] = c.code.isin(set(s.code))
c["how"] = np.where(c.opened == "", "track's year (estimated)", np.where(c.note.str.contains("opened: estimated|estimated:"), "year or month only (estimated)", "cited day"))
print("county stations (table rows / in the viewer file), by system and how the opening is known:")
print(c.groupby(["system", "how"]).agg(rows=("code", "size"), in_file=("in_file", "sum")).to_string())
print("  not in the viewer file:", c[~c.in_file][["system", "name"]].values.tolist())

if B.exists():
    old = json.load(open(B / "transit-lines.json"))
    new = {l["id"]: l for l in m["lines"]}
    same = sum(1 for l in old["lines"] if l["id"] in new and all(new[l["id"]][k] == l[k] for k in l))
    print(f"before / after: {len(old['lines'])} old service lines, {same} identical in the new file; new lines: "
          f"{[l['id'] for l in m['lines'] if l['id'] not in {x['id'] for x in old['lines']}]}")
    if same != len(old["lines"]):
        fail("the city's service lines changed")
    so = pd.DataFrame(json.load(open(B / "transit-stations.json"))).set_index("code")
    sn = s.drop_duplicates("code").set_index("code")
    heavy = so[so.system == "bart"]
    miss = [c_ for c_ in heavy.index if c_ not in sn.index]
    diff = [c_ for c_ in heavy.index if c_ in sn.index and any(sn.loc[c_, k] != heavy.loc[c_, k] for k in ("system", "lon", "lat", "z", "kind", "start", "end", "line"))]
    print(f"  subway / SIR / el stations before {len(heavy)}: missing now {len(miss)}, changed {len(diff)} {diff[:6]}")
    rest = so[so.system != "bart"]
    ch = [c_ for c_ in rest.index if c_ not in sn.index or any(sn.loc[c_, k] != rest.loc[c_, k] for k in ("lon", "lat", "start", "end"))]
    print(f"  railroad / PATH stations before {len(rest)}: missing or moved now {len(ch)} {ch[:8]}; now 'bart' (PATH): {int((sn.loc[[x for x in rest.index if x in sn.index], 'system'] == 'bart').sum())}")
    if miss or diff:
        fail("the city's subway stations changed")
    ho, co, lo_, la_, yo = read_bin(B / "transit.bin.gz")
    so_, sn_ = co["start_indices"], col["start_indices"]
    n8o, n8n = int((co["kind"] == 8).sum()), int((col["kind"] == 8).sum())
    # the subway's and the els' paths come first in both files
    k = 0
    while k < len(co["kind"]) and k < len(col["kind"]) and co["kind"][k] == 8 and col["kind"][k] == 8 and so_[k + 1] - so_[k] == sn_[k + 1] - sn_[k] and (yo[k] == yrs[k]).all():
        k += 1
    print(f"  transit.bin.gz before {ho['counts']}, kind 8 paths {n8o} -> {n8n}; leading subway / el paths identical in length and years: {k}")
print("OK" if ok else "FAILED")
