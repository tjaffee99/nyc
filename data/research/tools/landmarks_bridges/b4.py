import sys; sys.path.insert(0,'data/interim/landmarks_bridges')
from blib import *
A=(-73.923383,40.783592); B=(-73.920608,40.781506)
ax=Axis(A,B)
seg=[s for s in ov('rail',"name='Northeast Corridor'",(-73.94,40.765,-73.895,40.815)) if length(s[2])>4000 and s[3].startswith('fb010fe0')][0]
ls=seg[2]; cs=list(ls.coords)
M=LineString([loc(ax.anchor,p) for p in cs])
print('line length',round(M.length), 'npts',len(cs))
def dist_on(p): 
    q=Point(loc(ax.anchor,p)); return round(M.project(q),1), round(M.distance(q),1)
print('arch towers on line', dist_on(A), dist_on(B), 'anchor', dist_on(ax.anchor))
for k in ('hellgate_rfk','rfk_north'):
    o=osm(k)
    for w in o['ways']:
        if 'bridge:support' in w[2]:
            c,_=centroid(w[1]); d=dist_on(c)
            if d[1]<40: print('  support',k,w[0],f'{c[0]:.6f},{c[1]:.6f}','line dist',d,[(round(a,1),round(b)) for a,b in mrr(w[1])])
    for w in o['bridgeways']:
        if w[2].get('railway')=='rail':
            d0=dist_on(w[1][0]); d1=dist_on(w[1][-1])
            if min(d0[1],d1[1])<30: print('  railway',k,w[0],w[2].get('name'),w[2].get('bridge:name'),w[2].get('bridge:structure'),w[2].get('layer'),d0,d1)
# ground along the line every 250 m
print('ground:',' '.join(f'{d}:{elev(*unloc(ax.anchor,(M.interpolate(d).x,M.interpolate(d).y))):.1f}' for d in range(0,int(M.length)+1,250)))
S=M.simplify(1.5); print('simplified npts',len(S.coords))
import json
json.dump({'line':[unloc(ax.anchor,p) for p in S.coords]},open('data/interim/landmarks_bridges/hellgate_line.json','w'))
