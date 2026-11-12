"""Drop from an exported layer the sliver-shaped outlines lying in a roadway (the lead's 'bad' rule of street_share.py:
> 60 % of the area within 5 m of a street centre line and narrower than 5.5 m or longer than 3.5 times the width) -
dark tram / pipe lines and gutter strips read as brick or stone. Rewrites <layer>.geojson and <layer>_stats.json.
python -I drop_slivers.py <layer> ..."""
import sys, json, numpy as np, pandas as pd, geopandas as gpd, shapely
RAW = "data/raw/overture/2026-10-21.0/"
ln = np.concatenate([shapely.from_wkb(pd.read_parquet(RAW + f + ".parquet", columns=["geometry"]).geometry.values) for f in ("roads_local", "roads_region")])
b = shapely.bounds(ln); ln = ln[(b[:, 0] > -74.3) & (b[:, 2] < -73.65) & (b[:, 1] > 40.47) & (b[:, 3] < 40.95)]
ln = gpd.GeoSeries(ln, crs=4326).to_crs(32618).values; tree = shapely.STRtree(ln)
for L in sys.argv[1:]:
    p = f"data/manual/atlas/{L}.geojson"; d = json.load(open(p))
    g = gpd.read_file(p).to_crs(32618); G = g.geometry.values
    qi, li = tree.query(G, predicate="intersects"); on = np.zeros(len(g))
    if len(qi): np.add.at(on, qi, shapely.area(shapely.intersection(G[qi], shapely.buffer(ln[li], 5.0, cap_style="flat"))))
    m = shapely.minimum_rotated_rectangle(G); cc = np.array([np.asarray(q.exterior.coords)[:4] for q in m])
    e1, e2 = np.hypot(*(cc[:, 1] - cc[:, 0]).T), np.hypot(*(cc[:, 2] - cc[:, 1]).T); wd, lg = np.minimum(e1, e2), np.maximum(e1, e2)
    bad = (on > 0.6 * shapely.area(G)) & ((wd < 5.5) | (lg > 3.5 * wd))
    if not bad.any(): print(L, "nothing to drop"); continue
    d["features"] = [f for f, k in zip(d["features"], bad) if not k]
    json.dump(d, open(p, "w"), separators=(",", ":"))
    s = json.load(open(f"data/manual/atlas/{L}_stats.json")); t = s["total"]
    t["roadway_slivers_dropped"] = int(bad.sum())
    for k in ("frame", "brick", "stone"): t[k] = sum(f["properties"]["material"] == k for f in d["features"])
    t["buildings"] = len(d["features"]); t["on_today"] = sum(bool(f["properties"]["on_today"]) for f in d["features"])
    for pl in s["plates"]:
        if "exported" in pl and pl.get("status") == "ok": pl["exported"] = sum(f["properties"]["plate"] == int(pl["plate"]) for f in d["features"])
    json.dump(s, open(f"data/manual/atlas/{L}_stats.json", "w"), indent=1)
    print(L, "dropped", int(bad.sum()), "left", len(d["features"]))
