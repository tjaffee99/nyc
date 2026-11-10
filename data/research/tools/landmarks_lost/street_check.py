"""For each model: today's street centre lines (Overture) that run inside its site outline (shrunk 3 m)."""
import json, math, duckdb, shapely
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
R = '/home/user/nyc/data/raw/overture/2026-10-21.0/'
M = json.load(open('/home/user/nyc/data/interim/landmarks_lost/meshes.json'))
con = duckdb.connect()
import numpy as np
names = []; geoms = []
for f in ('roads_local.parquet', 'roads_region.parquet'):
    cols = [c[0] for c in con.execute(f"DESCRIBE SELECT * FROM '{R}{f}'").fetchall()]
    rows = con.execute(f"SELECT name, class, geometry FROM '{R}{f}'").fetchall()
    for name, cls, g in rows:
        names.append(name or f'(unnamed {cls})'); geoms.append(bytes(g))
G = shapely.from_wkb(geoms)
tree = shapely.STRtree(G)
print('roads', len(G))
for i, m in M.items():
    if not m['replaces']: continue
    lon, lat = m['anchor']; kx = 111_320 * math.cos(math.radians(lat)); ky = 110_574
    site = unary_union([Polygon(r).buffer(0) for r in m['replaces']]).buffer(-3)
    if site.is_empty: continue
    x0, y0, x1, y1 = site.bounds
    hits = {}
    for k in tree.query(shapely.box(lon + x0 / kx, lat + y0 / ky, lon + x1 / kx, lat + y1 / ky)):
        geom = G[k]
        for ls in getattr(geom, 'geoms', [geom]):
            L = LineString([((c[0] - lon) * kx, (c[1] - lat) * ky) for c in ls.coords]).intersection(site)
            if not L.is_empty and L.length > 4:
                hits[names[k]] = hits.get(names[k], 0) + L.length
    print(f"{i:34s} site {site.area:7.0f} m2 | " + ('; '.join(f'{k} {v:.0f} m' for k, v in sorted(hits.items(), key=lambda t: -t[1])[:6]) or 'no street inside'))
