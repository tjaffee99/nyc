"""python -I check.py [prefix]  -> for each best_guess row: overlap with buildings alive in its years (area share), centre in today's water, outside/inside"""
import sys, math, duckdb, pandas as pd, shapely, shapely.affinity as sa, geopandas as gpd
sys.path.insert(0, "/home/user/nyc/data/research/lost_works_build"); from lwlib import *
pre = sys.argv[1] if len(sys.argv) > 1 else ""
rows = [r for r in load().values() if r["id"].startswith(pre)]
c = duckdb.connect(); c.execute("install spatial; load spatial; SET geometry_always_xy=true; SET memory_limit='1200MB'")
OV = ROOT / "data/raw/overture/2026-10-21.0"
bad = 0
for r in rows:
    lat, lon = float(r["lat"]), float(r["lon"]); w, d = [float(v) for v in r["footprint_m"].split("x")]
    kx = 111320 * math.cos(math.radians(lat)); ky = 110540
    poly = sa.rotate(shapely.box(-w / 2, -d / 2, w / 2, d / 2), -float(r["rotation_deg"] or 0), origin=(0, 0))
    poly = sa.scale(poly, 1 / kx, 1 / ky, origin=(0, 0)); poly = sa.translate(poly, lon, lat)
    s, e = int(r["start_year"]), int(r["end_year"])
    env = f"ST_MakeEnvelope({poly.bounds[0]},{poly.bounds[1]},{poly.bounds[2]},{poly.bounds[3]})"; wkt = poly.wkt
    msgs = []
    for f in ("county_buildings", "nyc_buildings"):
        q = c.execute(f"select count(*), count(*) filter (where year_confidence<>'procedural'), coalesce(sum(ST_Area(ST_Intersection(geometry, ST_GeomFromText('{wkt}')))),0) from '{ROOT}/data/interim/{f}.parquet' where ST_Intersects(geometry,{env}) and start_year<{e} and end_year>{s} and ST_Intersects(geometry, ST_GeomFromText('{wkt}'))").fetchone()
        if q[0]: msgs.append(f"{q[0]} bldg ({q[1]} not procedural) {q[2] * kx * ky:.0f} m2 of {w*d:.0f}")
    wa = c.execute(f"select coalesce(sum(ST_Area(ST_Intersection(geometry, ST_GeomFromText('{wkt}')))),0) from '{OV}/base_water.parquet' where ST_Intersects(geometry,{env})").fetchone()[0] * kx * ky
    if wa > 0.15 * w * d: msgs.append(f"water {wa:.0f} m2")
    if msgs: bad += 1; print(r["id"], "; ".join(msgs))
print("rows", len(rows), "flagged", bad)
