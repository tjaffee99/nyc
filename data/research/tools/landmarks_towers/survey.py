"""Survey one building for landmark modelling: official footprints + OSM 3D parts, in the
building's own rotated frame (u = local x, v = local y pointing at compass bearing B).

  python survey.py <name> <lon> <lat> [radius=70] [--B deg] [--rings] [--anchor lon,lat] [--all]

Prints: anchor (centroid of the principal footprint unless --anchor), B, each official
footprint within the radius (ring in the rotated frame, simplified 0.4 m), and every OSM
building part whose centroid lies within the principal footprint buffered 6 m (--all: within
the radius): min_height, height, floors, roof, area, bbox in the rotated frame, fill ratio,
and the ring when it is not a plain rectangle (or --rings).
"""
import math
import pickle
import sys
from pathlib import Path

import duckdb
import numpy as np
import shapely
from shapely.geometry import Point, Polygon

ROOT = Path('/home/user/nyc')
FP = ROOT / 'data/interim/nyc_footprints_raw.parquet'
PARTS = ROOT / 'data/raw/overture/2026-10-21.0/building_part.parquet'
CACHE = ROOT / 'data/interim/landmarks_towers/parts.pkl'


def load_parts():
    if CACHE.exists():
        return pickle.loads(CACHE.read_bytes())
    con = duckdb.connect()
    con.execute('INSTALL spatial; LOAD spatial;')
    rows = con.execute(f"""SELECT id, building_id, name, height, min_height, num_floors, roof_shape, roof_height,
        ST_AsWKB(geometry), ST_X(ST_Centroid(geometry)), ST_Y(ST_Centroid(geometry)) FROM '{PARTS}'""").fetchall()
    rows = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], bytes(r[8]), r[9], r[10]) for r in rows]
    CACHE.write_bytes(pickle.dumps(rows))
    return rows


def local(anchor, lon, lat):
    kx = 111_320 * math.cos(math.radians(anchor[1]))
    return (lon - anchor[0]) * kx, (lat - anchor[1]) * 110_574


def to_local_poly(anchor, g):
    polys = []
    for p in getattr(g, 'geoms', [g]):
        if p.geom_type != 'Polygon':
            continue
        ext = [local(anchor, x, y) for x, y in np.asarray(p.exterior.coords)[:, :2]]
        holes = [[local(anchor, x, y) for x, y in np.asarray(r.coords)[:, :2]] for r in p.interiors]
        polys.append(Polygon(ext, holes))
    return shapely.unary_union(polys) if len(polys) != 1 else polys[0]


def rot(B):
    c, s = math.cos(math.radians(B)), math.sin(math.radians(B))
    # world (x, y) -> frame (u, v): u = c x - s y ; v = s x + c y
    return lambda x, y: (c * x - s * y, s * x + c * y)


def rot_poly(g, B):
    f = rot(B)
    return shapely.transform(g, lambda a: np.array([f(x, y) for x, y in a]))


def ring_str(g, tol=0.4):
    g = g.simplify(tol)
    out = []
    for p in getattr(g, 'geoms', [g]):
        out.append(' '.join(f'[{x:.1f},{y:.1f}]' for x, y in list(p.exterior.coords)[:-1]))
        for h in p.interiors:
            out.append('   hole: ' + ' '.join(f'[{x:.1f},{y:.1f}]' for x, y in list(h.coords)[:-1]))
    return ' | '.join(out)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    flags = sys.argv[1:]
    name, lon, lat = args[0], float(args[1]), float(args[2])
    rad = float(args[3]) if len(args) > 3 else 70.0
    dx = rad / (111_320 * math.cos(math.radians(lat))) * 1.6
    dy = rad / 110_574 * 1.6
    con = duckdb.connect()
    rows = con.execute(f"""SELECT bin, name, year_raw, height_m, ground_m, lon, lat, geometry FROM '{FP}'
        WHERE lon BETWEEN {lon - dx} AND {lon + dx} AND lat BETWEEN {lat - dy} AND {lat + dy}""").fetchall()
    q0 = (lon, lat)
    fps = []
    for bin_, nm, yr, h, gnd, clon, clat, wkb in rows:
        g = shapely.from_wkb(bytes(wkb))
        gl = to_local_poly(q0, g)
        d = gl.distance(Point(0, 0))
        if d <= rad:
            fps.append([d, bin_, nm, yr, h, gnd, g])
    fps.sort(key=lambda r: (r[0], -(r[4] or 0)))
    main_fp = fps[0]
    if '--anchor' in flags:
        anchor = tuple(float(v) for v in flags[flags.index('--anchor') + 1].split(','))
    else:
        c = main_fp[6].centroid
        anchor = (round(c.x, 6), round(c.y, 6))
    mainl = to_local_poly(anchor, main_fp[6])
    if '--B' in flags:
        B = float(flags[flags.index('--B') + 1])
    else:
        xy = np.asarray(mainl.minimum_rotated_rectangle.exterior.coords)
        e = np.diff(xy, axis=0)
        k = int(np.argmax(np.hypot(e[:, 0], e[:, 1])))
        bearing = math.degrees(math.atan2(e[k, 0], e[k, 1])) % 180
        B = ((bearing + 45) % 90) - 45
    print(f'=== {name}: anchor [{anchor[0]}, {anchor[1]}]  B = {B:.1f} deg (frame +y bearing)  ground {main_fp[5]} m')
    print('--- official footprints (frame u,v):')
    for d, bin_, nm, yr, h, gnd, g in fps:
        gl = rot_poly(to_local_poly(anchor, g), B)
        u0, v0, u1, v1 = gl.bounds
        c = gl.centroid
        print(f' BIN {bin_} {nm or "-"} yr {yr} roof {h} gnd {gnd} area {gl.area:.0f} d={d:.0f} cen({c.x:.1f},{c.y:.1f}) '
              f'bbox u[{u0:.1f},{u1:.1f}] v[{v0:.1f},{v1:.1f}] fill {gl.area / max((u1 - u0) * (v1 - v0), 1e-9):.2f}')
        if d < 1 or '--rings' in flags:
            print('    ring: ' + ring_str(gl))
    print('--- OSM parts (frame u,v):')
    sel = []
    keep = mainl.buffer(6)
    for pid, bid, nm, h, mh, nf, rs, rh, wkb, clon, clat in load_parts():
        if abs(clon - anchor[0]) > dx or abs(clat - anchor[1]) > dy:
            continue
        gl = to_local_poly(anchor, shapely.from_wkb(wkb))
        if gl.is_empty:
            continue
        c = gl.centroid
        if ('--all' in flags and math.hypot(c.x, c.y) <= rad) or keep.contains(c):
            sel.append((mh or 0, h or 0, nf, rs, rh, nm, rot_poly(gl, B)))
    sel.sort(key=lambda r: (r[0], r[1]))
    amin = float(flags[flags.index('--min') + 1]) if '--min' in flags else 25.0
    small = [s for s in sel if s[6].area < amin]
    if small:
        print(f' ({len(small)} parts under {amin:.0f} m2 not listed; z range {min(s[0] for s in small):.0f}-{max(s[1] for s in small):.0f})')
    for mh, h, nf, rs, rh, nm, gl in sel:
        if gl.area < amin:
            continue
        u0, v0, u1, v1 = gl.bounds
        fill = gl.area / max((u1 - u0) * (v1 - v0), 1e-9)
        print(f' z {mh:6.1f}-{h:6.1f} fl {nf} roof {rs or "-"}/{rh or "-"} area {gl.area:6.0f} u[{u0:.1f},{u1:.1f}] v[{v0:.1f},{v1:.1f}] '
              f'fill {fill:.2f} {nm or ""}')
        if fill < 0.93 or '--rings' in flags:
            print('    ring: ' + ring_str(gl, 0.6))
    # massing profile: union area of parts at sample heights
    if sel:
        zs = sorted({round(s[0], 1) for s in sel} | {round(s[1], 1) for s in sel})
        prof = []
        for a, b2 in zip(zs[:-1], zs[1:]):
            zm = (a + b2) / 2
            u = shapely.unary_union([s[6] for s in sel if s[0] <= zm < s[1]])
            if not u.is_empty:
                prof.append(f'{a:.0f}-{b2:.0f}:{u.area:.0f}')
        print('--- OSM union area by level: ' + '  '.join(prof))


if __name__ == '__main__':
    main()
