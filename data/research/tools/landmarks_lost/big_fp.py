import sys, math, duckdb, shapely, numpy as np
SRC = '/home/user/nyc/data/interim/nyc_footprints_raw.parquet'
con = duckdb.connect()
for a in sys.argv[1:]:
    label, lon, lat, rad, minarea = a.split(','); lon=float(lon); lat=float(lat); rad=float(rad); minarea=float(minarea)
    kx = 111_320 * math.cos(math.radians(lat)); ky = 110_574
    rows = con.execute(f"SELECT bin, name, year_raw, height_m, ground_m, geometry FROM '{SRC}' WHERE lon BETWEEN {lon-rad/kx} AND {lon+rad/kx} AND lat BETWEEN {lat-rad/ky} AND {lat+rad/ky}").fetchall()
    print(f"== {label} anchor {lon},{lat}")
    for bin_, name, yr, h, gnd, wkb in rows:
        g = shapely.from_wkb(bytes(wkb)); p = max(getattr(g, 'geoms', [g]), key=lambda q: q.area)
        L = shapely.Polygon([((x-lon)*kx, (y-lat)*ky) for x, y in np.asarray(p.exterior.coords)[:, :2]])
        if L.area < minarea: continue
        mr = list(L.minimum_rotated_rectangle.exterior.coords)
        e1 = math.dist(mr[0], mr[1]); e2 = math.dist(mr[1], mr[2]); k = 0 if e1 >= e2 else 1
        brg = (math.degrees(math.atan2(mr[k+1][0]-mr[k][0], mr[k+1][1]-mr[k][1])) + 360) % 180
        S = L.simplify(1.0)
        print(f"  BIN {bin_} {name or '-'} yr {yr} roof {h} ground {gnd} area {L.area:.0f} obb {max(e1,e2):.1f}x{min(e1,e2):.1f} brg {brg:.1f} c [{L.centroid.x:.1f},{L.centroid.y:.1f}]")
        print('    ring: ' + ' '.join(f'[{x:.1f},{y:.1f}]' for x, y in list(S.exterior.coords)[:-1]))
