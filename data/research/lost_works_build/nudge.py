"""python -I nudge.py prefix maxdist_m  -> move rows (<= maxdist) to the offset with the least overlap with real (non-procedural) buildings alive in their years (and with today's water for non-piers)"""
import sys, math, duckdb, shapely, shapely.affinity as sa, numpy as np
from shapely.strtree import STRtree
sys.path.insert(0, "/home/user/nyc/data/research/lost_works_build"); from lwlib import *
pre, md = sys.argv[1], float(sys.argv[2])
d = load(); ids = [k for k in d if k.startswith(pre)]
c = duckdb.connect(); c.execute("install spatial; load spatial; SET geometry_always_xy=true; SET memory_limit='1200MB'")
OV = ROOT / "data/raw/overture/2026-10-21.0"
for k in ids:
    r = d[k]; lat, lon = float(r["lat"]), float(r["lon"]); w, dd = [float(v) for v in r["footprint_m"].split("x")]
    kx = 111320 * math.cos(math.radians(lat)); ky = 110540; s, e = int(r["start_year"]), int(r["end_year"])
    m = md / 80000 * 1.5; env = f"ST_MakeEnvelope({lon-m-w/kx},{lat-m-w/ky},{lon+m+w/kx},{lat+m+w/ky})"
    gs = []
    for f in ("county_buildings", "nyc_buildings"):
        gs += [shapely.from_wkb(bytes(x[0])) for x in c.execute(f"select ST_AsWKB(geometry) from '{ROOT}/data/interim/{f}.parquet' where ST_Intersects(geometry,{env}) and start_year<{e} and end_year>{s} and year_confidence<>'procedural'").fetchall()]
    water = [] if "pier" in k else [shapely.from_wkb(bytes(x[0])) for x in c.execute(f"select ST_AsWKB(geometry) from '{OV}/base_water.parquet' where ST_Intersects(geometry,{env})").fetchall()]
    tg = [shapely.transform(g, lambda a_: np.column_stack([(a_[:, 0] - lon) * kx, (a_[:, 1] - lat) * ky])) for g in gs + water]
    tree = STRtree(tg)
    base = sa.rotate(shapely.box(-w / 2, -dd / 2, w / 2, dd / 2), -float(r["rotation_deg"] or 0), origin=(0, 0))
    best = None
    for dx in range(-int(md), int(md) + 1, 10):
        for dy in range(-int(md), int(md) + 1, 10):
            p = sa.translate(base, dx, dy); ov = sum(p.intersection(tg[i]).area for i in tree.query(p))
            sc = ov + 0.01 * math.hypot(dx, dy) * w * dd / 100
            if best is None or sc < best[0]: best = (sc, dx, dy, ov)
    sc, dx, dy, ov = best
    r["lat"] = round(lat + dy / ky, 6); r["lon"] = round(lon + dx / kx, 6)
    if dx or dy: r["shape_note"] += f" (Position shifted {math.hypot(dx,dy):.0f} m to keep clear of standing buildings.)"
    print(k, "shift", dx, dy, "overlap m2", round(ov))
import csv
w_ = csv.DictWriter(open(CSV, "w", newline=""), COLS); w_.writeheader(); [w_.writerow(v) for v in d.values()]
