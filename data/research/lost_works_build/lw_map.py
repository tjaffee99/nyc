"""python -I lw_map.py name x0 y0 x1 y1 [year] [aerial=1951|1924] [rows=csv]
Renders roads (named), rail, water, buildings (alive in `year` if given, else all), existing notable rows, my best_guess rows."""
import sys, io, math, urllib.request
from pathlib import Path
import duckdb, geopandas as gpd, numpy as np, pandas as pd, shapely
from shapely.geometry import box
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data/interim/lost_works_raw"
OV = ROOT / "data/raw/overture/2026-10-21.0"
def q(c, sql):
    df = c.execute(sql).df(); g = gpd.GeoSeries.from_wkb(df.pop("g").apply(bytes), crs=4326)
    return gpd.GeoDataFrame(df, geometry=g)
def tile_img(kind, x0, y0, x1, y1, z=18):
    from PIL import Image
    def tx(lon): return (lon + 180) / 360 * 2**z
    def ty(lat): return (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * 2**z
    a, b, c_, d = int(tx(x0)), int(ty(y1)), int(tx(x1)), int(ty(y0))
    svc = {"1951": "NYC_Orthos_1951", "1924": "Ortho_1924_Mosaic"}[kind]
    W = (c_ - a + 1) * 256; H = (d - b + 1) * 256; im = Image.new("RGB", (W, H))
    for i in range(a, c_ + 1):
        for j in range(b, d + 1):
            p = OUT / f"tile_{kind}_{z}_{i}_{j}.png"
            if not p.exists():
                u = f"https://tiles.arcgis.com/tiles/yG5s3afENB5iO9fj/arcgis/rest/services/{svc}/MapServer/tile/{z}/{j}/{i}"
                try: p.write_bytes(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "NYCThroughTime-research/0.1"}), timeout=30).read())
                except Exception as e: continue
            try: im.paste(Image.open(p).convert("RGB"), ((i - a) * 256, (j - b) * 256))
            except Exception: pass
    lon = lambda x: x / 2**z * 360 - 180
    lat = lambda y: math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / 2**z))))
    return im, (lon(a), lon(c_ + 1), lat(d + 1), lat(b))
def main():
    name = sys.argv[1]; x0, y0, x1, y1 = map(float, sys.argv[2:6]); rest = sys.argv[6:]
    year = next((int(r) for r in rest if r.isdigit()), None)
    aer = next((r.split("=")[1] for r in rest if r.startswith("aerial=")), None)
    c = duckdb.connect(); c.execute("install spatial; load spatial; SET geometry_always_xy=true; SET memory_limit='1200MB'")
    env = f"ST_MakeEnvelope({x0},{y0},{x1},{y1})"
    roads = q(c, f"select name n, ST_AsWKB(geometry) g from '{OV}/roads_local.parquet' where ST_Intersects(geometry,{env})")
    rail = q(c, f"select ST_AsWKB(geometry) g from '{OV}/rail.parquet' where ST_Intersects(geometry,{env})")
    water = q(c, f"select ST_AsWKB(geometry) g from '{OV}/base_water.parquet' where ST_Intersects(geometry,{env})")
    yc = f"and start_year<={year} and end_year>{year}" if year else ""
    blds = []
    for f in ("county_buildings", "nyc_buildings"):
        blds.append(q(c, f"select start_year s, end_year e, ST_AsWKB(geometry) g from '{ROOT}/data/interim/{f}.parquet' where ST_Intersects(geometry,{env}) {yc}"))
    b = pd.concat(blds)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    asp = 1 / math.cos(math.radians((y0 + y1) / 2)); W = 14; H = W * (y1 - y0) / (x1 - x0) / asp
    fig, ax = plt.subplots(figsize=(W, H), dpi=90); ax.set_aspect(asp); ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
    if aer:
        im, (a, bb_, c_, d) = tile_img(aer, x0, y0, x1, y1); ax.imshow(im, extent=(a, bb_, c_, d), zorder=0)
    else:
        water.plot(ax=ax, color="#cfe6f5")
    if "nobld" not in rest: b.plot(ax=ax, facecolor="none" if aer else "#d8d0c0", edgecolor="#ff0" if aer else "#a09070", linewidth=0.4)
    for r in rest:
        if r.startswith("atlas="):
            ag = gpd.read_file(ROOT / "data/manual/atlas" / (r.split("=")[1] + ".geojson"), bbox=(x0, y0, x1, y1)); ag.boundary.plot(ax=ax, color="#0a0", linewidth=0.7)
    roads.plot(ax=ax, color="#fff" if aer else "#777", linewidth=0.5); rail.plot(ax=ax, color="#c00", linewidth=0.7)
    seen = set()
    for r in roads.itertuples():
        n = r.n
        if isinstance(n, str) and n and n not in seen and r.geometry.length > 0.0004:
            seen.add(n); p = r.geometry.interpolate(0.5, normalized=True)
            if x0 < p.x < x1 and y0 < p.y < y1: ax.text(p.x, p.y, n[:28], fontsize=6, color="#00f" if not aer else "#0ff")
    for rp in [ROOT / "data/tables/notable_demolished.best_guess.csv"] + [ROOT / "data/tables" / r.split("=")[1] for r in rest if r.startswith("rows=")]:
        if not rp.exists(): continue
        t = pd.read_csv(rp); col = "#f0f" if "best_guess" in rp.name else "#0a0"
        for r in t.itertuples():
            if not (x0 < r.lon < x1 and y0 < r.lat < y1): continue
            if isinstance(r.footprint_m, str):
                w, d = [float(v) for v in r.footprint_m.lower().replace("×", "x").split("x")]
                rot = 0 if pd.isna(r.rotation_deg) else float(r.rotation_deg)
                kx = 111320 * math.cos(math.radians(r.lat)); ky = 110540
                import shapely.affinity as sa
                poly = sa.rotate(box(-w / 2, -d / 2, w / 2, d / 2), -rot, origin=(0, 0))
                xs, ys = poly.exterior.xy
                ax.plot([r.lon + x / kx for x in xs], [r.lat + y / ky for y in ys], color=col, linewidth=1.2)
                ax.text(r.lon, r.lat, str(r.id)[-12:], fontsize=5, color=col)
    step = 0.002 if (x1 - x0) < 0.05 else 0.005
    ax.set_xticks(np.arange(math.ceil(x0 / step) * step, x1, step)); ax.set_yticks(np.arange(math.ceil(y0 / step) * step, y1, step))
    ax.tick_params(labelsize=7); ax.grid(True, color="#999", linewidth=0.3); ax.set_title(name + (f" year {year}" if year else ""))
    fig.tight_layout(); p = OUT / f"lw_{name}.png"; fig.savefig(p); print(p)
main()
