"""After `export`: drop, from each pair of outlines of one layer that overlap by more than 1 m2, the smaller one
(they are the same building traced on two plates whose masks overlap, or two pieces of one house). Rewrites the
layer file and adds `overlap_dropped` to its stats.   python -I dedupe.py <layer>"""
import json, sys
from pathlib import Path
import numpy as np, shapely, pyproj
from shapely.geometry import shape
OUT = Path(__file__).resolve().parents[1]
L = sys.argv[1]
d = json.load(open(OUT / f"{L}.geojson"))
tf = pyproj.Transformer.from_crs(4326, 32618, always_xy=True)
g = [shapely.transform(shape(f["geometry"]), lambda c: np.column_stack(tf.transform(c[:, 0], c[:, 1]))) for f in d["features"]]
arr = np.array(g, object); t = shapely.STRtree(arr)
a, b = t.query(arr, predicate="intersects"); m = a < b; a, b = a[m], b[m]
inter = shapely.area(shapely.intersection(arr[a], arr[b])); k = inter > 1.0
area = shapely.area(arr); drop = set()
for i, j in zip(a[k], b[k]):
    if i in drop or j in drop: continue
    drop.add(i if area[i] <= area[j] else j)
d["features"] = [f for n, f in enumerate(d["features"]) if n not in drop]
(OUT / f"{L}.geojson").write_text(json.dumps(d, separators=(",", ":")))
sp = OUT / f"{L}_stats.json"; s = json.loads(sp.read_text())
s["total"]["overlap_dropped"] = len(drop); s["total"]["buildings"] = len(d["features"])
for k_ in ("brick", "frame", "stone"): s["total"][k_] = sum(f["properties"]["material"] == k_ for f in d["features"])
sp.write_text(json.dumps(s, indent=1)); print(L, "dropped", len(drop), "left", len(d["features"]))
