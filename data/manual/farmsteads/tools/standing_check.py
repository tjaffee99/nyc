"""Is a footprint under a mark evidence? Real matches against the same marks moved off their spots.

  python -I standing_check.py

Counts of marks whose best footprint (pipeline/topo_farmsteads.FootprintMatcher) falls in a class, by
distance and by how many footprints stand within 60 m of the mark, for the real positions and for the
mean of three moved copies (150 m E / 100 m N, 120 m W / 160 m N, 90 m E / 170 m S)."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyproj

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "pipeline"))
import topo_farmsteads as T

fc = json.loads((T.OUT_DIR / "farmsteads.geojson").read_text())["features"]
P = np.array([f["geometry"]["coordinates"] for f in fc])
E, N = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32618", always_xy=True).transform(P[:, 0], P[:, 1])
fy = np.array([f["properties"]["first_year"] for f in fc])
cls = np.array(["bar" if f["properties"]["kind"] == "large" else "mark" for f in fc])
boro = np.array([f["properties"]["borough"] for f in fc])
fm = T.FootprintMatcher()


def table(dx, dy):
    b = fm.match(E + dx, N + dy, fy, cls)
    b["boro"] = boro[b.index.values]
    b["d"] = pd.cut(b["dist"], [-1, 0.01, 6, 12, 25], labels=["inside", "0-6 m", "6-12 m", "12-25 m"])
    b["dens"] = pd.cut(b["n60"], [0, 3, 6, 12, 1000], labels=["1-3", "4-6", "7-12", "13+"])
    b["cl"] = b["rank"].map({0: "recorded", 1: "by_then", 2: "later"})
    return b


real = table(0, 0)
moved = [table(dx, dy) for dx, dy in T.MOVES]
for key in (["cl"], ["cl", "d"], ["cl", "dens"], ["cl", "boro"], ["cl", "dens", "d"]):
    r = real.groupby(key, observed=True).size().rename("real")
    m = (sum(t.groupby(key, observed=True).size().reindex(r.index, fill_value=0) for t in moved) / len(moved)).round(1).rename("moved (mean of 3)")
    out = pd.concat([r, m], axis=1)
    out["ratio"] = (out["real"] / out["moved (mean of 3)"].replace(0, np.nan)).round(2)
    print(out.to_string(), "\n")

# the filter nyc_buildings.evidence_bounds used on 2026-11-10 to re-date footprints from this file:
# every `recorded` / `by_then` match, and a `later` match that is the only one of its class within 25 m and within 12 m
print("later-dated footprint, the only one within 25 m, within 12 m of the mark:")
f = lambda t: int(((t["cl"] == "later") & (t["n"] == 1) & (t["dist"] <= 12)).sum())
print("  real", f(real), " moved", [f(t) for t in moved])
f = lambda t: int(((t["cl"] == "later") & (t["n"] == 1) & (t["dist"] <= 12) & (t["n60"] <= 3)).sum())
print("  ... and at most 3 footprints within 60 m: real", f(real), " moved", [f(t) for t in moved])
