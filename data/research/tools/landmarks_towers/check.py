"""Numeric check of the tower models against the official footprints and the OSM parts.

  python check.py [id-substring ...]

Per landmark: the footprints the viewer will hide (same rule as index.ts replacedMask), the
model's plan outline (projection of every face above z = 0.5 m) vs the union of those
footprints (area ratio, centroid offset, intersection-over-union), the model's top vs the
cited height (data/tables/landmarks_towers.csv height_m), and the plan area above each
OSM level vs the union of OSM parts there.
"""
import csv
import json
import math
import subprocess
import sys
from pathlib import Path

import duckdb
import numpy as np
import shapely
from shapely.geometry import Polygon, Point

sys.path.insert(0, str(Path(__file__).parent))
from survey import FP, load_parts, to_local_poly  # noqa: E402

HERE = Path(__file__).parent
ROOT = Path('/home/user/nyc')


def shadow(tris, zcut):
    """Union of the xy projection of the triangle parts above zcut."""
    polys = []
    for t in tris:
        if t[:, 2].max() <= zcut + 1e-6:
            continue
        pts = []
        for i in range(3):
            a, b = t[i], t[(i + 1) % 3]
            ain, bin_ = a[2] >= zcut, b[2] >= zcut
            if ain:
                pts.append((a[0], a[1]))
            if ain != bin_:
                f = (zcut - a[2]) / (b[2] - a[2])
                pts.append((a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1])))
        if len(pts) >= 3:
            p = Polygon(pts)
            if p.area > 1e-4:
                polys.append(p if p.is_valid else p.buffer(0))
    return shapely.union_all(polys) if polys else Polygon()


def section(tris, z):
    """Outline of the model cut by the horizontal plane z (walls polygonized, faces merged)."""
    segs = []
    for t in tris:
        zz = t[:, 2]
        if zz.min() > z or zz.max() < z or zz.max() - zz.min() < 1e-9:
            continue
        pts = []
        for i in range(3):
            a, b = t[i], t[(i + 1) % 3]
            if (a[2] - z) * (b[2] - z) < 0:
                lo, hi = (a, b) if a[2] < b[2] else (b, a)  # same floats from both triangles of a wall
                f = (z - lo[2]) / (hi[2] - lo[2])
                pts.append((lo[0] + f * (hi[0] - lo[0]), lo[1] + f * (hi[1] - lo[1])))
            elif a[2] == z:
                pts.append((a[0], a[1]))
        pts = list(dict.fromkeys(pts))
        if len(pts) >= 2:
            segs.append(shapely.LineString(pts[:2]))
    if not segs:
        return Polygon()
    faces = list(shapely.polygonize([shapely.union_all(segs)]).geoms)
    return shapely.union_all(faces) if faces else Polygon()


ZBASE = {}
SHADOW = {'citigroup_center', 'central_park_tower', 'vessel', 'lever_house'}  # raised on stilts: compare the plan projection instead of the wall section


def main():
    only = sys.argv[1:]
    subprocess.run(['/home/user/nyc/viewer/node_modules/.bin/esbuild', str(HERE / 'dump.ts'), '--bundle', '--format=esm', '--platform=node',
                    f'--outfile={HERE / "dump.mjs"}', '--log-level=warning'], check=True)
    r = subprocess.run(['node', str(HERE / 'dump.mjs'), *only], check=True, capture_output=True, text=True)
    print(r.stdout.strip())
    cited = {}
    csvp = ROOT / 'data/tables/landmarks_towers.csv'
    if csvp.exists():
        for row in csv.DictReader(csvp.open()):
            cited[row['id']] = float(row['height_m'])
    con = duckdb.connect()
    parts = load_parts()
    all_lms = json.loads((HERE / 'mesh.json').read_text())
    results = []
    for lm in all_lms:
        anchor = lm['anchor']
        tris = np.array(lm['pos']).reshape(-1, 3, 3)
        ztop = tris[:, :, 2].max()
        res = {'id': lm['id'], 'name': lm['name'], 'top': round(float(ztop), 1), 'cited': cited.get(lm['id'])}
        results.append(res)
        riders = [o for o in all_lms if o is not lm and o['anchor'] == anchor and not o['replaces']]
        if lm['replaces'] and riders:
            tris = np.concatenate([tris] + [np.array(o['pos']).reshape(-1, 3, 3) for o in riders])
            res['with'] = [o['id'] for o in riders]
        c = cited.get(lm['id'])
        print(f"\n== {lm['id']} ({lm['name']}) built {lm['built']} tris {len(tris)}  top {ztop:.1f} m"
              + (f"  cited {c:.1f} m  diff {ztop - c:+.1f}" if c else '  (no cited height in csv)'))
        if not lm['replaces']:
            print('   no replaces (rides on another model)')
            res['rider'] = True
            continue
        kx = 111_320 * math.cos(math.radians(anchor[1]))
        polys = [Polygon(p) for p in lm['replaces']]
        allx = [p[0] for r in lm['replaces'] for p in r]
        ally = [p[1] for r in lm['replaces'] for p in r]
        x0, x1, y0, y1 = min(allx) - 40, max(allx) + 40, min(ally) - 40, max(ally) + 40
        rows = con.execute(f"""SELECT bin, name, year_raw, height_m, lon, lat, geometry FROM '{FP}'
            WHERE lon BETWEEN {anchor[0] + x0 / kx} AND {anchor[0] + x1 / kx} AND lat BETWEEN {anchor[1] + y0 / 110574} AND {anchor[1] + y1 / 110574}""").fetchall()
        hidden = []
        for bin_, nm, yr, h, lon, lat, wkb in rows:
            cx, cy = (lon - anchor[0]) * kx, (lat - anchor[1]) * 110_574
            pt = Point(cx, cy)
            inside = any(p.contains(pt) for p in polys)
            # index.ts: tall (> 60 m) footprints within ~12 m of the outline go too
            # index.ts: distance in units of 0.00015 deg lon / 0.00011 deg lat, hit below 1
            sx, sy = 0.00015 * kx, 0.00011 * 110_574
            near = (h or 0) > 60 and any(shapely.affinity.scale(p.exterior, 1 / sx, 1 / sy, origin=(0, 0)).distance(Point(cx / sx, cy / sy)) < 1 for p in polys)
            if inside or near:
                g = to_local_poly(anchor, shapely.from_wkb(bytes(wkb)))
                hidden.append((bin_, nm, yr, h, g, inside))
                print(f"   hides BIN {bin_} {nm or '-'} yr {yr} roof {h} m area {g.area:.0f}" + ('' if inside else f'  [NEAR-TALL rule, not inside; centroid local {cx:.1f},{cy:.1f}]'))
        if not hidden:
            print('   !! hides no footprint')
            continue
        off = shapely.union_all([h[4] for h in hidden])
        zb = ZBASE.get(lm['id'], 0.6)
        sh = shadow(tris, 0.5) if lm['id'] in SHADOW else section(tris, zb)
        iou = sh.intersection(off).area / max(sh.union(off).area, 1e-9)
        d = math.hypot(sh.centroid.x - off.centroid.x, sh.centroid.y - off.centroid.y)
        hmax = max(h[3] or 0 for h in hidden)
        res.update({'hides': [f"{h[0]}" + ('' if h[5] else ' (tall-sliver rule)') for h in hidden], 'official': round(off.area), 'model': round(sh.area),
                    'pct': round(100 * (sh.area / off.area - 1), 1), 'd': round(d, 1), 'iou': round(iou, 2), 'roof': round(hmax, 1),
                    'how': 'projection' if lm['id'] in SHADOW else 'walls'})
        print(f"   plan ({'projection' if lm['id'] in SHADOW else 'walls at z = 0.6 m'}): model {sh.area:.0f} m2 vs official {off.area:.0f} m2 ({100 * (sh.area / off.area - 1):+.1f} %), centroid offset {d:.1f} m, IoU {iou:.2f}; "
              f"measured roof (city) {hmax:.1f} m")
        # OSM profile
        keep = off.buffer(6)
        sel = []
        for pid, bid, nm, h, mh, nf, rs, rh, wkb, clon, clat in parts:
            if abs(clon - anchor[0]) > 0.004 or abs(clat - anchor[1]) > 0.003:
                continue
            g = to_local_poly(anchor, shapely.from_wkb(wkb))
            if not g.is_empty and keep.contains(g.centroid):
                sel.append((mh or 0, h or 0, g))
        if sel:
            zs = sorted({round(s[0], 1) for s in sel} | {round(s[1], 1) for s in sel})
            line = []
            for a, b in zip(zs[:-1], zs[1:]):
                if b - a < 2:
                    continue
                zm = (a + b) / 2
                u = shapely.union_all([s[2] for s in sel if s[0] <= zm < s[1]])
                m = shadow(tris, zm)
                line.append(f"{a:.0f}-{b:.0f}: osm {u.area:.0f} / model {m.area:.0f}")
            print('   levels (plan area above mid-level): ' + ' | '.join(line))
            res['levels'] = line


    if not only:
        (HERE / 'check_results.json').write_text(json.dumps(results, indent=1))


if __name__ == '__main__':
    main()
