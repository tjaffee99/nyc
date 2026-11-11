"""After export + dedupe: drop the outlines of the Andrew Jackson Gardens (a public housing project of 1941 pasted onto the 1930 sheets, so not a state of 1930):
sheet 34 (panel x < 250, y < 470 of the 700 px montage), sheet 35 (x < 270), sheet 37 (x < 420, y > 520).  python -I post.py hudson_hoboken_1930"""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import atlas as A
from shapely.geometry import shape
L = sys.argv[1]; OUT = A.OUT
d = json.load(open(OUT / f"{L}.geojson"))
box = {34: lambda x, y: x < 250 and y < 470, 35: lambda x, y: x < 270, 37: lambda x, y: x < 420 and y > 520}
P = {k: A.Plate(L, 91030000 + k, verbose=False) for k in box}
keep = []; drop = 0
for f in d["features"]:
    k = int(f["properties"]["sheet"]) if str(f["properties"].get("sheet", "")).isdigit() else None
    if k in box:
        c = shape(f["geometry"]).centroid
        x, y = P[k].inv(np.array([A.S.local(c.x, c.y)]))[0]
        f_ = P[k].img().shape[1] / 700
        if box[k](x / f_, y / f_): drop += 1; continue
    keep.append(f)
d["features"] = keep
(OUT / f"{L}.geojson").write_text(json.dumps(d, separators=(",", ":")))
sp = OUT / f"{L}_stats.json"; s = json.loads(sp.read_text())
s["total"]["andrew_jackson_gardens_dropped"] = drop; s["total"]["buildings"] = len(keep)
for m in ("brick", "frame", "stone"): s["total"][m] = sum(f["properties"]["material"] == m for f in keep)
sp.write_text(json.dumps(s, indent=1)); print("dropped", drop, "left", len(keep))
