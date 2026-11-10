"""SSURGO soil map unit polygons of the five counties -> data/interim/natural/ssurgo_all.parquet (UTM 18N).
Input: the Web Soil Survey survey-area zips fetched by download.py (USDA NRCS, public domain)."""
import glob

import geopandas as gpd
import pandas as pd

ROOT = "/home/user/nyc"
fr = [gpd.read_file(f) for f in sorted(glob.glob(f"{ROOT}/data/raw/natural/ssurgo/*/*/spatial/soilmu_a_*.shp"))]
g = pd.concat(fr, ignore_index=True).to_crs(32618)
g["ha"] = g.area / 1e4
g.to_parquet(f"{ROOT}/data/interim/natural/ssurgo_all.parquet")
print(len(g), g.groupby("AREASYMBOL").ha.sum().round(0).to_dict())
