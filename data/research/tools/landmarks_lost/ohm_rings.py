"""Print OHM outlines (CC0) as local-metre rings around their centroid, with area and oriented bbox."""
import json, math, sys
import shapely
from shapely.geometry import Polygon, LineString, MultiPolygon
from shapely.ops import polygonize, unary_union, linemerge

def local(anchor, lon, lat):
    kx = 111_320 * math.cos(math.radians(anchor[1]))
    return ((lon - anchor[0]) * kx, (lat - anchor[1]) * 110_574)

def geom_of(e):
    if e['type'] == 'way':
        pts = [(p['lon'], p['lat']) for p in e['geometry']]
        return Polygon(pts) if len(pts) >= 4 and pts[0] == pts[-1] else LineString(pts)
    outers = []; inners = []
    for m in e.get('members', []):
        if m['type'] != 'way' or 'geometry' not in m: continue
        ls = LineString([(p['lon'], p['lat']) for p in m['geometry']])
        (inners if m.get('role') == 'inner' else outers).append(ls)
    polys = list(polygonize(unary_union(outers + inners)))
    if polys:
        return unary_union([Polygon(p.exterior) for p in polys]).difference(unary_union([q for q in polys if any(q.equals(Polygon(i)) for i in inners if i.is_ring)] or [Polygon()])) if False else max([unary_union([Polygon(p.exterior) for p in polys])], key=lambda z: z.area)
    g = unary_union(polys) if polys else linemerge(outers)
    if inners and polys:
        ip = list(polygonize(unary_union(inners)))
        g = g.difference(unary_union(ip)) if ip else g
    return g

def describe(e, simp=0.4, anchor=None):
    g = geom_of(e)
    if g.is_empty:
        print('## EMPTY', e['type'], e['id'], e.get('tags',{}).get('name'), [(m.get('role'), len(m.get('geometry',[])), m['geometry'][0]==m['geometry'][-1]) for m in e.get('members',[]) if 'geometry' in m]); return
    c = g.centroid if g.geom_type in ('Polygon','MultiPolygon') else g.envelope.centroid
    a = anchor or (c.x, c.y)
    t = e.get('tags', {})
    print(f"## {e['type']}/{e['id']} {t.get('name')} [{t.get('start_date')}..{t.get('end_date')}] h={t.get('height')} levels={t.get('building:levels')} src={t.get('source','')[:80]}")
    print(f"   anchor {a[0]:.6f},{a[1]:.6f}")
    polys = list(g.geoms) if hasattr(g, 'geoms') else [g]
    for p in polys:
        if p.geom_type != 'Polygon':
            xy = [local(a, x, y) for x, y in p.coords]
            print('   line:', ' '.join(f'[{x:.1f},{y:.1f}]' for x, y in xy)); continue
        L = Polygon([local(a, x, y) for x, y in p.exterior.coords], [[local(a, x, y) for x, y in r.coords] for r in p.interiors])
        mr = L.minimum_rotated_rectangle
        q = list(mr.exterior.coords)
        e1 = math.hypot(q[1][0]-q[0][0], q[1][1]-q[0][1]); e2 = math.hypot(q[2][0]-q[1][0], q[2][1]-q[1][1])
        k = 0 if e1 >= e2 else 1
        brg = (math.degrees(math.atan2(q[k+1][0]-q[k][0], q[k+1][1]-q[k][1])) + 360) % 180
        S = L.simplify(simp)
        print(f"   area {L.area:.0f} m2  obb {max(e1,e2):.1f} x {min(e1,e2):.1f} m  long-axis bearing {brg:.1f}  centroid_local [{L.centroid.x:.1f},{L.centroid.y:.1f}]")
        print('   ring:', ' '.join(f'[{x:.1f},{y:.1f}]' for x, y in list(S.exterior.coords)[:-1]))
        for r in S.interiors:
            print('   hole:', ' '.join(f'[{x:.1f},{y:.1f}]' for x, y in list(r.coords)[:-1]))

if __name__ == '__main__':
    d = json.load(open(sys.argv[1]))
    import os
    SIMP = os.environ.get('SIMP', '0.4')
    ids = set(sys.argv[2:])
    for e in d['elements']:
        if not ids or f"{e['type'][0]}{e['id']}" in ids:
            describe(e, simp=float(SIMP))
