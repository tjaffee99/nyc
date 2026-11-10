"""Road centre lines around a point: per name, bearing and perpendicular offset from the anchor."""
import sys, math, duckdb, shapely, numpy as np
R = '/home/user/nyc/data/raw/overture/2026-10-21.0/'
def main(lon, lat, rad):
    kx = 111_320 * math.cos(math.radians(lat)); ky = 110_574
    dx = rad / kx; dy = rad / ky
    con = duckdb.connect()
    rows = []
    for f in ('roads_local.parquet', 'roads_region.parquet'):
        cols = [c[0] for c in con.execute(f"DESCRIBE SELECT * FROM '{R}{f}'").fetchall()]
        namecol = 'name' if 'name' in cols else ("names.primary" if 'names' in cols else cols[0])
        gcol = 'geometry'
        bb = "bbox.xmin < {x1} AND bbox.xmax > {x0} AND bbox.ymin < {y1} AND bbox.ymax > {y0}" if 'bbox' in cols else "TRUE"
        q = f"SELECT {namecol} AS name, {gcol} AS g FROM '{R}{f}' WHERE " + bb.format(x0=lon-dx, x1=lon+dx, y0=lat-dy, y1=lat+dy)
        try:
            rows += con.execute(q).fetchall()
        except Exception as e:
            print('ERR', f, cols, e); return
    win = shapely.box(-rad, -rad, rad, rad)
    acc = {}
    for name, g in rows:
        if not name: continue
        geom = shapely.from_wkb(bytes(g))
        for ls in getattr(geom, 'geoms', [geom]):
            xy = np.asarray(ls.coords)[:, :2]
            L = shapely.LineString([((x-lon)*kx, (y-lat)*ky) for x, y in xy]).intersection(win)
            if L.is_empty: continue
            for part in getattr(L, 'geoms', [L]):
                if part.geom_type != 'LineString' or part.length < 8: continue
                acc.setdefault(name, []).append(part)
    for name, parts in sorted(acc.items()):
        pts = np.vstack([np.asarray(p.coords) for p in parts])
        c = pts.mean(0); u, s, vt = np.linalg.svd(pts - c)
        d = vt[0]; brg = (math.degrees(math.atan2(d[0], d[1])) + 360) % 180
        n = np.array([d[1], -d[0]])  # right-hand normal
        off = float(-c @ n)  # signed distance of anchor from line (anchor at origin)
        foot = c + d * float(-c @ d)
        resid = float(np.abs((pts - c) @ n).max())
        tot = sum(p.length for p in parts)
        print(f"  {name:28s} bearing {brg:6.1f}  nearest point on line [{foot[0]:7.1f},{foot[1]:7.1f}] dist {math.hypot(*foot):6.1f} m  (len {tot:.0f} m, max dev {resid:.1f})")
if __name__ == '__main__':
    for a in sys.argv[1:]:
        label, lon, lat, rad = a.split(',')
        print(f"== {label} anchor {lon},{lat} r={rad}")
        main(float(lon), float(lat), float(rad))
