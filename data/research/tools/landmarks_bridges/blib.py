import pickle, math, duckdb, shapely, numpy as np
from shapely.geometry import Polygon, LineString, Point
from shapely import wkb
from shapely.ops import substring, linemerge
D='data/interim/landmarks_bridges'
OV='data/raw/overture/2026-10-21.0'
def osm(key): return pickle.load(open(f'{D}/osm_{key}.pkl','rb'))
def way(o,i):
    for w in o['ways']+o['bridgeways']:
        if w[0]==str(i): return w
def K(lat): return 111320*math.cos(math.radians(lat))
def loc(a,p): return ((p[0]-a[0])*K(a[1]), (p[1]-a[1])*110574)
def unloc(a,p): return (a[0]+p[0]/K(a[1]), a[1]+p[1]/110574)
def centroid(g):
    """centroid of lon/lat ring (metric-weighted)"""
    a=g[0]; P=Polygon([loc(a,p) for p in g]); c=P.centroid
    return unloc(a,(c.x,c.y)), P
def mrr(g):
    """min rotated rect dims (long, short), long-side bearing"""
    a=g[0]; P=Polygon([loc(a,p) for p in g]).minimum_rotated_rectangle
    xs=list(P.exterior.coords)
    e=[(math.hypot(xs[i+1][0]-xs[i][0],xs[i+1][1]-xs[i][1]), math.degrees(math.atan2(xs[i+1][0]-xs[i][0],xs[i+1][1]-xs[i][1]))%180) for i in range(2)]
    e.sort(reverse=True)
    return e
class Axis:
    def __init__(s,A,B):
        s.A=A; s.B=B; s.anchor=((A[0]+B[0])/2,(A[1]+B[1])/2)
        a=loc(s.anchor,A); b=loc(s.anchor,B)
        dx=b[0]-a[0]; dy=b[1]-a[1]; s.len=math.hypot(dx,dy); s.ux=dx/s.len; s.uy=dy/s.len
        s.bearing=math.degrees(math.atan2(dx,dy))%360
    def al(s,p):
        l=loc(s.anchor,p); return l[0]*s.ux+l[1]*s.uy
    def ac(s,p):
        l=loc(s.anchor,p); return l[0]*s.uy-l[1]*s.ux
    def sa(s,p): return (round(s.al(p),1), round(s.ac(p),1))
con=None
def ov(file, where, bbox=None, bridge_only=True):
    """Overture segments -> list of (name, class, LineString lonlat) clipped to is_bridge ranges"""
    global con
    if con is None:
        con=duckdb.connect(); con.execute('install spatial; load spatial; SET geometry_always_xy = true;')
    fl='rail_flags' if file=='rail' else 'road_flags'
    q=f"select id,name,class,{fl},st_aswkb(geometry) from '{OV}/{file}.parquet' where ({where})"
    if bbox: q+=f" and st_intersects(geometry, st_makeenvelope({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}))"
    out=[]
    for i,n,c,flags,g in con.execute(q).fetchall():
        ls=wkb.loads(bytes(g))
        if not bridge_only: out.append((n,c,ls,i)); continue
        for f in flags or []:
            if 'is_bridge' in f['values']:
                bt=f['between'] or [0,1]
                out.append((n,c,substring(ls,bt[0],bt[1],normalized=True),i))
    return out
def fmt(pts,nd=6): return '['+', '.join(f'[{p[0]:.{nd}f}, {p[1]:.{nd}f}]' for p in pts)+']'
def simplify(ls,a,tol=1.0):
    """simplify lonlat linestring with metric tolerance"""
    L=LineString([loc(a,p) for p in ls.coords]).simplify(tol)
    return [unloc(a,p) for p in L.coords]
def length(ls):
    c=list(ls.coords); a=c[0]
    return LineString([loc(a,p) for p in c]).length

import json
_g=None
def elev(lon,lat):
    """ground elevation (m) from the viewer's terrain grid (same lookup as elevationAt)"""
    global _g
    if _g is None:
        m=json.load(open('data/interim/grid_detail_meta.json')); _g=(m,np.load('data/interim/grid_detail_elev.npy'))
    m,a=_g; R=6378137
    X=lon*math.pi*R/180; Y=R*math.log(math.tan(math.pi/4+lat*math.pi/360))
    c=(X-m['X0'])/m['res']; r=(m['Y0']-Y)/m['res']
    if c<0 or r<0 or c>m['cols']-1 or r>m['rows']-1: return 0.0
    c0=int(c); r0=int(r); c1=min(c0+1,m['cols']-1); r1=min(r0+1,m['rows']-1); fx=c-c0; fy=r-r0
    v=lambda rr,cc: max(float(a[rr,cc]),0)
    return (v(r0,c0)*(1-fx)+v(r0,c1)*fx)*(1-fy)+(v(r1,c0)*(1-fx)+v(r1,c1)*fx)*fy
