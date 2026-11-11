"""Extract + render a basemap of the Hudson waterfront: today's roads, rail, water, buildings; the 1919 / 1891 traced layers.
python -I basemap.py extract ; python -I basemap.py render name lon0 lat0 lon1 lat1 [layers...]  -> data/interim/hudson_waterfront_raw/map_<name>.png"""
import sys, json, pickle
from pathlib import Path
import duckdb, geopandas as gpd, numpy as np
ROOT = Path(__file__).resolve().parents[4]
RAW = ROOT / "data/interim/hudson_waterfront_raw"
OV = ROOT / "data/raw/overture/2026-10-21.0"
STEP = 0.002
B = (-74.14, 40.62, -73.98, 40.80)
def extract():
    c = duckdb.connect(); c.execute("install spatial; load spatial; SET geometry_always_xy=true; SET memory_limit='1200MB'")
    env = f"ST_MakeEnvelope({B[0]},{B[1]},{B[2]},{B[3]})"
    out = {}
    for k, sql in dict(
        roads=f"select class cl, ST_AsWKB(geometry) g from '{OV}/roads_local.parquet' where ST_Intersects(geometry,{env})",
        rail=f"select class cl, ST_AsWKB(geometry) g from '{OV}/rail.parquet' where ST_Intersects(geometry,{env})",
        water=f"select ST_AsWKB(geometry) g from '{OV}/base_water.parquet' where ST_Intersects(geometry,{env})",
        bld=f"select ST_AsWKB(geometry) g from '{ROOT}/data/interim/county_buildings.parquet' where ST_Intersects(geometry,{env})").items():
        df = c.execute(sql).df()
        g = gpd.GeoSeries.from_wkb(df.pop("g").apply(bytes), crs=4326)
        out[k] = gpd.GeoDataFrame(df, geometry=g)
        print(k, len(df))
    pickle.dump(out, open(RAW / "base.pkl", "wb"))
def render(name, x0, y0, x1, y1, layers):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    d = pickle.load(open(RAW / "base.pkl", "rb"))
    asp = 1 / np.cos(np.radians((y0 + y1) / 2))
    W = 14; H = W * (y1 - y0) / (x1 - x0) / asp
    fig, ax = plt.subplots(figsize=(W, H), dpi=100)
    ax.set_facecolor("#ffffff")
    ax.set_aspect(asp); ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
    from shapely.geometry import box
    bb = box(x0, y0, x1, y1)
    land = d["water"]
    land[land.intersects(bb)].plot(ax=ax, color="#cfe6f5")
    d["bld"][d["bld"].intersects(bb)].plot(ax=ax, color="#d8d0c0", linewidth=0)
    r = d["roads"][d["roads"].intersects(bb)]; r.plot(ax=ax, color="#777", linewidth=0.5)
    d["rail"][d["rail"].intersects(bb)].plot(ax=ax, color="#c00", linewidth=0.8)
    cols = ["#0044cc", "#008800", "#cc6600"]
    for i, L in enumerate(layers):
        p = ROOT / "data/manual/atlas" / f"{L}.geojson"
        g = gpd.read_file(p, bbox=(x0, y0, x1, y1))
        g.boundary.plot(ax=ax, color=cols[i % 3], linewidth=0.5)
        cv = ROOT / "data/manual/atlas" / f"{L}_coverage.geojson"
        if cv.exists(): gpd.read_file(cv).boundary.plot(ax=ax, color=cols[i % 3], linewidth=1.2, linestyle="--")
    ax.set_xticks(np.arange(round(x0, 3), x1, STEP)); ax.set_yticks(np.arange(round(y0, 3), y1, STEP))
    ax.tick_params(labelsize=7); ax.grid(True, color="#999", linewidth=0.3)
    fig.tight_layout(); fig.savefig(RAW / f"map_{name}.png"); print(RAW / f"map_{name}.png")
if __name__ == "__main__":
    if sys.argv[1] == "extract": extract()
    else: render(sys.argv[2], *map(float, sys.argv[3:7]), sys.argv[7:])
