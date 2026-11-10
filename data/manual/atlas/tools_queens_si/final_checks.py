"""Post-export checks and clean-up of the layers of this tool copy (run after `atlas.py export <layer>`):
drops outlines whose centre lies outside the coverage polygons or that overlap another outline of the layer
(intersection over 30 % of the smaller one: the smaller goes), checks validity, area (15-5,000 m2) and unique ids,
and writes the numbers into <layer>_stats.json under total.final_checks.   python -I final_checks.py <layer> ..."""
import json, sys
from pathlib import Path
import numpy as np, shapely, shapely.geometry as sg
from pyproj import Transformer
OUT = Path(__file__).resolve().parents[1]
T = Transformer.from_crs(4326, 32618, always_xy=True)
def loc(g):
    return shapely.transform(g, lambda q: np.column_stack(T.transform(q[:, 0], q[:, 1])))
for layer in sys.argv[1:]:
    fc = json.loads((OUT / f"{layer}.geojson").read_text())
    cv = json.loads((OUT / f"{layer}_coverage.geojson").read_text())
    feats = fc["features"]
    G = np.array([loc(sg.shape(f["geometry"])) for f in feats], object)
    U = shapely.union_all([loc(sg.shape(c["geometry"])) for c in cv["features"]]).buffer(1.0)
    keep = shapely.contains(U, shapely.centroid(G))
    n_out = int((~keep).sum())
    # overlaps
    tree = shapely.STRtree(G)
    i, j = tree.query(G, predicate="intersects")
    m = i < j
    i, j = i[m], j[m]
    A = shapely.area(G)
    inter = shapely.area(shapely.intersection(G[i], G[j]))
    small = np.minimum(A[i], A[j])
    bad = inter > 0.3 * small
    n_pairs_before = int(bad.sum())
    for a, b in zip(i[bad], j[bad]):
        keep[a if A[a] < A[b] else b] = False
    sel = np.where(keep)[0]
    feats2 = [feats[k] for k in sel]
    G2 = G[sel]
    A2 = shapely.area(G2)
    ids = [f["properties"]["id"] for f in feats2]
    tree = shapely.STRtree(G2)
    i, j = tree.query(G2, predicate="intersects")
    m = i < j
    ov = int((shapely.area(shapely.intersection(G2[i[m]], G2[j[m]])) > 0.3 * np.minimum(A2[i[m]], A2[j[m]])).sum()) if m.any() else 0
    touch = int(m.sum())
    res = dict(buildings=len(feats2), dropped_centre_outside_coverage=n_out, dropped_overlapping=n_pairs_before,
               invalid=int((~shapely.is_valid(G2)).sum()), area_out_of_range=int(((A2 < 15) | (A2 > 5000)).sum()),
               duplicate_ids=len(ids) - len(set(ids)), overlapping_pairs_left=ov, touching_or_slightly_overlapping_pairs=touch,
               on_today=sum(f["properties"]["on_today"] for f in feats2),
               frame=sum(f["properties"]["material"] == "frame" for f in feats2), brick=sum(f["properties"]["material"] == "brick" for f in feats2),
               stone=sum(f["properties"]["material"] == "stone" for f in feats2),
               total_footprint_km2=round(float(A2.sum()) / 1e6, 3))
    fc["features"] = feats2
    (OUT / f"{layer}.geojson").write_text(json.dumps(fc, separators=(",", ":")))
    st = json.loads((OUT / f"{layer}_stats.json").read_text())
    st["total"].update(buildings=res["buildings"], frame=res["frame"], brick=res["brick"], stone=res["stone"], on_today=res["on_today"],
                       outside_coverage=0, invalid=res["invalid"], area_out_of_range=res["area_out_of_range"])
    st["total"]["final_checks"] = res
    # per plate counts after the clean-up
    cnt = {}
    for f in feats2:
        cnt[str(f["properties"]["plate"])] = cnt.get(str(f["properties"]["plate"]), 0) + 1
    for p in st["plates"]:
        if p.get("status") == "ok":
            p["exported_final"] = cnt.get(str(p["plate"]), 0)
    (OUT / f"{layer}_stats.json").write_text(json.dumps(st, indent=1))
    print(layer, json.dumps(res))
