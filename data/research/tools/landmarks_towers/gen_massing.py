"""Regenerate the measured-massing block of viewer/src/landmarks/nyc-towers.ts.

For every building in config.json: the anchor (centroid of its main official footprint), the
frame bearing B, the official footprint ring(s) and the stepped massing from OpenStreetMap's
building parts (Overture extract), all in the building frame (u = +x, v = +y at bearing B).

  python gen_massing.py [id ...]     # rewrites the block; prints a summary for the ids given
"""
import json
import math
import sys
from pathlib import Path

import duckdb
import numpy as np
import shapely
from shapely.geometry import Point

from survey import FP, load_parts, to_local_poly, rot_poly

HERE = Path(__file__).parent
TS = Path('/home/user/nyc/viewer/src/landmarks/nyc-towers.ts')


def ring_ts(p):
    return '[' + ', '.join(f'[{x:.1f}, {y:.1f}]' for x, y in list(p.exterior.coords)[:-1]) + ']'


def build(cfg, verbose):
    lon, lat = cfg['at']
    con = duckdb.connect()
    d = 0.0025
    rows = con.execute(f"""SELECT bin, name, height_m, geometry FROM '{FP}' WHERE lon BETWEEN {lon - d} AND {lon + d} AND lat BETWEEN {lat - d} AND {lat + d}""").fetchall()
    fps = []
    for bin_, nm, h, wkb in rows:
        g = shapely.from_wkb(bytes(wkb))
        fps.append((to_local_poly((lon, lat), g).distance(Point(0, 0)), bin_, nm, h, g))
    fps.sort(key=lambda r: r[0])
    main = fps[0]
    own = [main] + [f for f in fps[1:] if f[1] in cfg.get('bins', [])]
    if 'anchor' in cfg:
        anchor = tuple(cfg['anchor'])
    else:
        c = shapely.union_all([f[4] for f in own]).centroid if cfg.get('anchor_union') else main[4].centroid
        anchor = (round(c.x, 6), round(c.y, 6))
    mainl = to_local_poly(anchor, main[4])
    if 'B' in cfg:
        B = cfg['B']
    else:
        xy = np.asarray(mainl.minimum_rotated_rectangle.exterior.coords)
        e = np.diff(xy, axis=0)
        k = int(np.argmax(np.hypot(e[:, 0], e[:, 1])))
        B = round(((math.degrees(math.atan2(e[k, 0], e[k, 1])) % 180 + 45) % 90) - 45, 1)
    foots = [rot_poly(to_local_poly(anchor, f[4]), B) for f in own]
    offu = shapely.union_all(foots)
    keep = shapely.union_all([to_local_poly(anchor, f[4]) for f in own]).buffer(cfg.get('keep', 6))
    sel = []
    if cfg.get('osm', True):
        zmax = cfg.get('zmax', 1e9)
        sh = cfg.get('shift')  # {"zmin": z, "du": .., "dv": ..}: parts topping above zmin are moved
        for pid, bid, nm, h, mh, nf, rs, rh, wkb, clon, clat in load_parts():
            if abs(clon - anchor[0]) > 0.004 or abs(clat - anchor[1]) > 0.003:
                continue
            g = to_local_poly(anchor, shapely.from_wkb(wkb))
            if g.is_empty or g.area < cfg.get('minpart', 8) or not keep.contains(g.centroid):
                continue
            mh, h = mh or 0, h or 0
            if mh >= zmax:
                continue
            g = rot_poly(g, B)
            if sh and h > sh['zmin'] + 0.01:
                g = shapely.affinity.translate(g, sh.get('du', 0), sh.get('dv', 0))
            sel.append((mh, min(h, zmax), g))
    levels = []
    if sel:
        zs = sorted({round(s[0], 1) for s in sel} | {round(s[1], 1) for s in sel})
        merge = cfg.get('merge', 3.0)
        for a, b in zip(zs[:-1], zs[1:]):
            zm = (a + b) / 2
            u = shapely.union_all([s[2] for s in sel if s[0] <= zm < s[1]])
            if u.is_empty:
                continue
            if levels and (b - a < merge or levels[-1][2].symmetric_difference(u).area < 0.02 * u.area):
                if b - a >= merge and levels[-1][1] - levels[-1][0] < merge:
                    levels[-1][2] = u
                levels[-1][1] = b
            else:
                levels.append([a, b, u])
        dx = dy = 0.0
        if cfg.get('align') and levels:
            dx, dy = offu.centroid.x - levels[0][2].centroid.x, offu.centroid.y - levels[0][2].centroid.y
        tol = cfg.get('tol', 0.8)
        if cfg.get('clip'):  # keep the stack inside the official outline (grown 0.5 m)
            clipper = offu.buffer(0.5)
        for L in levels:
            g = shapely.affinity.translate(L[2], dx, dy)
            if cfg.get('clip'):
                g = g.intersection(clipper)
            L[2] = g.buffer(0.3).buffer(-0.3).simplify(tol)
    if cfg.get('base_from_foot') and levels:  # lowest level takes the official outline
        levels[0][2] = offu
    out = [f"  {cfg['id']}: {{", f"    anchor: [{anchor[0]}, {anchor[1]}],", f"    B: {B},",
           '    foot: [' + ', '.join(ring_ts(p.simplify(0.3)) for f in foots for p in getattr(f, 'geoms', [f])) + '],', '    levels: [']
    summ = []
    for a, b, u in levels:
        for p in getattr(u, 'geoms', [u]):
            if p.area < cfg.get('minpiece', 15):
                continue
            out.append(f'      [{round(a, 1):g}, {round(b, 1):g}, {ring_ts(p)}],')
            x0, y0, x1, y1 = p.bounds
            summ.append(f'   {a:5.0f}-{b:5.0f}  area {p.area:6.0f}  u[{x0:.1f},{x1:.1f}] v[{y0:.1f},{y1:.1f}] n={len(p.exterior.coords) - 1} cen({p.centroid.x:.1f},{p.centroid.y:.1f})')
    out += ['    ]', '  },']
    if verbose:
        print(f"== {cfg['id']}: anchor [{anchor[0]}, {anchor[1]}] B {B}; official: " + '; '.join(f'BIN {f[1]} {f[2] or "-"} roof {f[3]} area {g.area:.0f}' for f, g in zip(own, foots)))
        for g in foots:
            print('   foot: ' + ring_ts(g.simplify(0.3)))
        print('\n'.join(summ) if summ else '   (no OSM levels)')
    return '\n'.join(out)


def main():
    cfgs = json.loads((HERE / 'config.json').read_text())
    want = sys.argv[1:]
    blocks = [build(c, c['id'] in want or 'all' in want) for c in cfgs]
    src = TS.read_text()
    a, b = src.index('// <massing>'), src.index('// </massing>')
    gen = '// <massing>\nconst M: Record<string, Massing> = {\n' + '\n'.join(blocks) + '\n};\n'
    TS.write_text(src[:a] + gen + src[b:])
    print(f'wrote {len(cfgs)} massing entries')


if __name__ == '__main__':
    main()
