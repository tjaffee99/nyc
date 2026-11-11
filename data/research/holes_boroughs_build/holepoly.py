"""hole mask -> polygon (WGS84). python -I holepoly.py id [id...]  -> prints area; writes data/interim/holes_boroughs_raw/poly_<id>.geojson"""
import sys, json, numpy as np, shapely
from shapely.geometry import box, mapping
from shapely.ops import unary_union
m=json.load(open('data/interim/grid_detail_meta.json')); res,X0,Y0=m['res'],m['X0'],m['Y0']; R=6378137.0
def hole_polygon(hid, buf=0.0):
    rr,cc=np.load(f'data/interim/holes_boroughs_raw/holefp_{hid}.npy')
    g=unary_union([box(X0+c*res,Y0-(r+1)*res,X0+(c+1)*res,Y0-r*res) for r,c in zip(rr,cc)])
    g=g.buffer(res*0.35).buffer(-res*0.35).simplify(res*0.3)
    if buf: g=g.buffer(buf)
    f=lambda x,y:(np.degrees(x/R),np.degrees(2*np.arctan(np.exp(y/R))-np.pi/2))
    return shapely.transform(g,lambda a: np.array([f(x,y) for x,y in a]))
if __name__=='__main__':
    for h in sys.argv[1:]:
        g=hole_polygon(h); json.dump({'type':'Feature','properties':{'id':h},'geometry':mapping(g)},open(f'data/interim/holes_boroughs_raw/poly_{h}.geojson','w'))
        print(h,g.geom_type,round(g.area*111320*84300/1e4,1),'ha',[round(v,5) for v in g.bounds])
