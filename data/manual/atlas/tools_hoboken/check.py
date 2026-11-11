"""Layer checks: share of outlines near a street centre line, and on a standing footprint (IoU > 0.5).  python -I check.py <layer>"""
import sys, json, numpy as np, pandas as pd, geopandas as gpd, shapely
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
L = sys.argv[1]
g = gpd.read_file(ROOT / f"data/manual/atlas/{L}.geojson").to_crs(32618)
parts = [pd.read_parquet(ROOT / "data/raw/overture/2026-10-21.0" / f"{f}.parquet", columns=["geometry"]) for f in ("roads_local",)]
r = gpd.GeoSeries(gpd.GeoSeries.from_wkb(parts[0].geometry) if not hasattr(parts[0].geometry.iloc[0], "geom_type") else parts[0].geometry, crs=4326).to_crs(32618)
b = g.total_bounds; r = r[r.intersects(shapely.box(*b).buffer(50))]
lines = r.values
strip = shapely.union_all(shapely.buffer(lines, 8.0))
inter = shapely.area(shapely.intersection(g.geometry.values, strip)) / g.geometry.area.values
print(L, "outlines", len(g), "| within 8 m of a street centre line: area share > 0.5: %d (%.1f %%), > 0.8: %d" % ((inter > .5).sum(), 100 * (inter > .5).mean(), (inter > .8).sum()))
print("on_today:", int(g["on_today"].sum()), "(%.1f %%)" % (100 * g["on_today"].mean()))
