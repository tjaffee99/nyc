"""Independent numeric checks of an exported layer:  python -I check_layer.py <layer> ...
valid, 15-5000 m2, unique ids, centres inside coverage, overlapping pairs (> 0.3 of the smaller), per-plate counts."""
import json, sys, collections
import numpy as np, shapely
from shapely.geometry import shape
from shapely import transform
from pyproj import Transformer
T = Transformer.from_crs(4326, 32618, always_xy=True)
for layer in sys.argv[1:]:
    d = json.load(open(f"data/manual/atlas/{layer}.geojson"))
    cov = json.load(open(f"data/manual/atlas/{layer}_coverage.geojson"))
    g = [transform(shape(f["geometry"]), lambda c: np.column_stack(T.transform(c[:, 0], c[:, 1]))) for f in d["features"]]
    cg = [transform(shape(f["geometry"]), lambda c: np.column_stack(T.transform(c[:, 0], c[:, 1]))) for f in cov["features"]]
    ids = [f["properties"]["id"] for f in d["features"]]
    a = shapely.area(np.array(g, object))
    cu = shapely.union_all(cg).buffer(0)
    cen = shapely.centroid(np.array(g, object))
    pa = np.array(g, object)
    i, j = shapely.STRtree(pa).query(pa, predicate="intersects")
    m = i < j
    i, j = i[m], j[m]
    inter = shapely.area(shapely.intersection(pa[i], pa[j]))
    ov = int((inter > 0.3 * np.minimum(a[i], a[j])).sum())
    mats = collections.Counter(f["properties"]["material"] for f in d["features"])
    print(layer, "n", len(g), "invalid", int((~shapely.is_valid(pa)).sum()), "area_out", int(((a < 15) | (a > 5000)).sum()),
          "dup_ids", len(ids) - len(set(ids)), "centre_outside", int((~shapely.contains(cu, cen)).sum()), "overlap_pairs", ov,
          "touch_pairs", len(i), "materials", dict(mats), "cov_km2", round(cu.area / 1e6, 3),
          "on_today", sum(f["properties"]["on_today"] for f in d["features"]))
