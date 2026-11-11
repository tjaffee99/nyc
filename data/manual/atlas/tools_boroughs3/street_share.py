"""Share of a layer's outlines near today's street centre lines (the lead's ATLAS_SKIP test):
python -I street_share.py <layer> ...   -> centroid within 8 m of a centre line; and the lead's 'bad' rule
(sliver-shaped, >60 % of the area within 5 m of a centre line)."""
import sys, numpy as np, pandas as pd, geopandas as gpd, shapely
RAW = "data/raw/overture/2026-10-21.0/"
ln = np.concatenate([shapely.from_wkb(pd.read_parquet(RAW + f + ".parquet", columns=["geometry"]).geometry.values) for f in ("roads_local", "roads_region")])
b = shapely.bounds(ln); ln = ln[(b[:, 0] > -74.3) & (b[:, 2] < -73.65) & (b[:, 1] > 40.47) & (b[:, 3] < 40.95)]
ln = gpd.GeoSeries(ln, crs=4326).to_crs(32618).values; tree = shapely.STRtree(ln)
for L in sys.argv[1:]:
    g = gpd.read_file(f"data/manual/atlas/{L}.geojson").to_crs(32618); G = g.geometry.values
    c = shapely.centroid(G); near = np.zeros(len(g), bool)
    qi, _ = tree.query(c, predicate="dwithin", distance=8.0); near[np.unique(qi)] = True
    qi, li = tree.query(G, predicate="intersects"); on = np.zeros(len(g))
    if len(qi): np.add.at(on, qi, shapely.area(shapely.intersection(G[qi], shapely.buffer(ln[li], 5.0, cap_style="flat"))))
    m = shapely.minimum_rotated_rectangle(G); cc = np.array([np.asarray(q.exterior.coords)[:4] for q in m])
    e1, e2 = np.hypot(*(cc[:, 1] - cc[:, 0]).T), np.hypot(*(cc[:, 2] - cc[:, 1]).T); wd, lg = np.minimum(e1, e2), np.maximum(e1, e2)
    bad = (on > 0.6 * shapely.area(G)) & ((wd < 5.5) | (lg > 3.5 * wd))
    print(L, "n", len(g), "centroid_within_8m_of_street %.1f%%" % (100 * near.mean()), "lead_roadway_slivers", int(bad.sum()), "(%.1f%%)" % (100 * bad.mean()))
