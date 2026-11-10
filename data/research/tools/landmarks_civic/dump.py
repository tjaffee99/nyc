"""Scratch: official footprints + OSM 3D parts around points, local metres. Usage: dump.py name:lon,lat,radius[,minarea] ..."""
import math, sys, duckdb, numpy as np, shapely
ROOT = '/home/user/nyc/'
FP = ROOT + 'data/interim/nyc_footprints_raw.parquet'
BP = ROOT + 'data/raw/overture/2026-10-21.0/building_part.parquet'
con = duckdb.connect()
con.execute("install spatial; load spatial;")
def loc(a, lon, lat):
    kx = 111_320 * math.cos(math.radians(a[1]))
    return (lon - a[0]) * kx, (lat - a[1]) * 110_574
def topoly(g, a):
    poly = max(getattr(g, 'geoms', [g]), key=lambda p: p.area)
    xy = np.array([loc(a, x, y) for x, y in np.asarray(poly.exterior.coords)[:, :2]])
    return shapely.Polygon(xy)
def mrr(p):
    r = p.minimum_rotated_rectangle
    c = np.asarray(r.exterior.coords)[:4]
    e1 = c[1] - c[0]; e2 = c[2] - c[1]
    l1 = np.hypot(*e1); l2 = np.hypot(*e2)
    e = e1 if l1 >= l2 else e2
    brg = (math.degrees(math.atan2(e[0], e[1])) + 360) % 180
    return f"mrr c=({r.centroid.x:.1f},{r.centroid.y:.1f}) {min(l1,l2):.1f}x{max(l1,l2):.1f} long@{brg:.1f}"
def ring(p, tol):
    s = p.simplify(tol)
    return ' '.join(f"[{x:.1f},{y:.1f}]" for x, y in np.asarray(s.exterior.coords)[:-1])
for arg in sys.argv[1:]:
    name, rest = arg.split(':')
    v = [float(t) for t in rest.split(',')]
    lon, lat, rad = v[0], v[1], v[2]
    minarea = v[3] if len(v) > 3 else 25
    tol = v[4] if len(v) > 4 else 0.6
    a = (lon, lat)
    dx = rad / (111_320 * math.cos(math.radians(lat))) * 1.6; dy = rad / 110_574 * 1.6
    print(f"=== {name} anchor {lon},{lat} r={rad}")
    rows = con.execute(f"SELECT bin,name,year_raw,height_m,ground_m,geometry FROM '{FP}' WHERE lon BETWEEN {lon-dx} AND {lon+dx} AND lat BETWEEN {lat-dy} AND {lat+dy}").fetchall()
    out = []
    for bin_, nm, yr, h, gnd, wkb in rows:
        p = topoly(shapely.from_wkb(bytes(wkb)), a)
        d = p.distance(shapely.Point(0, 0))
        if d > rad or p.area < minarea: continue
        out.append((d, bin_, nm, yr, h, gnd, p))
    out.sort(key=lambda r: r[0])
    for d, bin_, nm, yr, h, gnd, p in out:
        print(f" FP d={d:.0f} BIN {bin_} {nm or '-'} yr {yr} roof {h and round(h,1)} gnd {gnd} area {p.area:.0f} cen=({p.centroid.x:.1f},{p.centroid.y:.1f}) {mrr(p)}")
        print("    " + ring(p, tol))
    rows = con.execute(f"SELECT name,height,min_height,roof_shape,roof_height,ST_AsWKB(geometry) FROM '{BP}' WHERE ST_XMin(geometry) < {lon+dx} AND ST_XMax(geometry) > {lon-dx} AND ST_YMin(geometry) < {lat+dy} AND ST_YMax(geometry) > {lat-dy}").fetchall()
    parts = []
    for nm, h, mh, rs, rh, wkb in rows:
        p = topoly(shapely.from_wkb(bytes(wkb)), a)
        d = p.distance(shapely.Point(0, 0))
        if d > rad: continue
        parts.append((d, nm, h, mh, rs, rh, p))
    parts.sort(key=lambda r: (r[0], -(r[2] or 0)))
    import os
    parts = parts[:int(os.environ.get('MAXPART','10'))]
    for d, nm, h, mh, rs, rh, p in parts:
        print(f" PART d={d:.0f} {nm or ''} h {h} min {mh} roof {rs} {rh} area {p.area:.0f} cen=({p.centroid.x:.1f},{p.centroid.y:.1f}) {mrr(p)}")
        if p.area > 15: print("    " + ring(p, tol))
