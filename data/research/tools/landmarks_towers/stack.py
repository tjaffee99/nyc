"""Stepped massing of a building from OSM 3D parts, as TS-ready level rings in the building frame.

  python stack.py <name> <lon> <lat> [--B deg] [--anchor lon,lat] [--tol 0.8] [--merge 3] [--align] [--zmax z] [--minpart 8]

Each output row: [z0, z1, ring] — the union of the parts standing between z0 and z1, simplified.
--align translates the OSM parts so the centroid of their lowest level sits on the official
footprint's centroid.
"""
import math
import sys

import duckdb
import numpy as np
import shapely
from shapely.geometry import Point

from survey import FP, load_parts, to_local_poly, rot_poly


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    flags = sys.argv[1:]
    opt = lambda k, d: float(flags[flags.index(k) + 1]) if k in flags else d
    name, lon, lat = args[0], float(args[1]), float(args[2])
    tol, merge, zmax, minpart = opt('--tol', 0.8), opt('--merge', 3.0), opt('--zmax', 1e9), opt('--minpart', 8.0)
    con = duckdb.connect()
    d = 0.0012
    rows = con.execute(f"""SELECT bin, height_m, geometry FROM '{FP}' WHERE lon BETWEEN {lon - d} AND {lon + d} AND lat BETWEEN {lat - d} AND {lat + d}""").fetchall()
    best = None
    for bin_, h, wkb in rows:
        g = shapely.from_wkb(bytes(wkb))
        dist = to_local_poly((lon, lat), g).distance(Point(0, 0))
        if best is None or dist < best[0]:
            best = (dist, bin_, h, g)
    if '--anchor' in flags:
        anchor = tuple(float(v) for v in flags[flags.index('--anchor') + 1].split(','))
    else:
        c = best[3].centroid
        anchor = (round(c.x, 6), round(c.y, 6))
    mainl = to_local_poly(anchor, best[3])
    if '--B' in flags:
        B = opt('--B', 0)
    else:
        xy = np.asarray(mainl.minimum_rotated_rectangle.exterior.coords)
        e = np.diff(xy, axis=0)
        k = int(np.argmax(np.hypot(e[:, 0], e[:, 1])))
        B = ((math.degrees(math.atan2(e[k, 0], e[k, 1])) % 180 + 45) % 90) - 45
    off = rot_poly(mainl, B)
    keep = mainl.buffer(6)
    sel = []
    for pid, bid, nm, h, mh, nf, rs, rh, wkb, clon, clat in load_parts():
        if abs(clon - anchor[0]) > 0.004 or abs(clat - anchor[1]) > 0.003:
            continue
        g = to_local_poly(anchor, shapely.from_wkb(wkb))
        if g.is_empty or g.area < minpart or not keep.contains(g.centroid):
            continue
        sel.append((mh or 0, min(h or 0, zmax), rot_poly(g, B)))
    zs = sorted({round(s[0], 1) for s in sel} | {round(s[1], 1) for s in sel})
    levels = []
    for a, b in zip(zs[:-1], zs[1:]):
        zm = (a + b) / 2
        u = shapely.union_all([s[2] for s in sel if s[0] <= zm < s[1]])
        if u.is_empty:
            continue
        levels.append([a, b, u])
    # merge thin levels and near-identical neighbours
    out = []
    for a, b, u in levels:
        if out and (b - a < merge or out[-1][2].symmetric_difference(u).area < 0.02 * u.area):
            if b - a >= merge and out[-1][1] - out[-1][0] < merge:
                out[-1][2] = u
            out[-1][1] = b
        else:
            out.append([a, b, u])
    dx = dy = 0.0
    if '--align' in flags and out:
        dx, dy = off.centroid.x - out[0][2].centroid.x, off.centroid.y - out[0][2].centroid.y
    print(f'// {name}: anchor [{anchor[0]}, {anchor[1]}], B = {B:.1f}; official area {off.area:.0f}, cen 0,0; OSM base area {out[0][2].area:.0f}, '
          f'cen {out[0][2].centroid.x:.1f},{out[0][2].centroid.y:.1f}; shift applied {dx:.1f},{dy:.1f}')
    for a, b, u in out:
        u = shapely.affinity.translate(u, dx, dy).simplify(tol)
        for p in getattr(u, 'geoms', [u]):
            if p.area < 15:
                continue
            ring = ', '.join(f'[{x:.1f}, {y:.1f}]' for x, y in list(p.exterior.coords)[:-1])
            print(f'  [{a:.0f}, {b:.0f}, [{ring}]],  // {p.area:.0f} m2' + (f' ({len(p.interiors)} holes dropped)' if p.interiors else ''))


if __name__ == '__main__':
    main()
