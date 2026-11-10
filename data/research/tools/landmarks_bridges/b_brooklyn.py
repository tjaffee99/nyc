import sys; sys.path.insert(0,'data/interim/landmarks_bridges')
from blib import *
o=osm('brooklyn')
tM,_=centroid(way(o,1255363983)[1]); tB,_=centroid(way(o,317352708)[1])
ax=Axis(tM,tB)
print('towers',tM,tB,'dist',round(ax.len,1),'cited 486.3; bearing',round(ax.bearing,2),'anchor',ax.anchor)
for i in (1255363983,317352708,1255363984,888759002):
    w=way(o,i); c,_=centroid(w[1]); print(i,'cen',[round(v,6) for v in c],'sa',ax.sa(c),'mrr',[(round(a,1),round(b,1)) for a,b in mrr(w[1])], w[2].get('bridge:support'))
w=way(o,375157262); al=[ax.al(p) for p in w[1]]; ac=[ax.ac(p) for p in w[1]]
print('outline along',round(min(al)),round(max(al)),'across',round(min(ac)),round(max(ac)))
# outline width along stations
import numpy as np
P=Polygon([(ax.al(p),ax.ac(p)) for p in w[1]])
for s in range(-1000,1001,100):
    it=P.intersection(LineString([(s,-400),(s,400)]))
    if not it.is_empty: print('  s',s,[round(v,1) for v in it.bounds[1::2]])
for n,c,ls,i in ov('roads_region',"name ilike 'Brooklyn Bridge%'"):
    cs=list(ls.coords); print(n,c,round(length(ls)),'from',ax.sa(cs[0]),'to',ax.sa(cs[-1]),len(cs))
for w in o['bridgeways']:
    if 'Promenade' in (w[2].get('name') or '') or 'Brooklyn Bridge'==(w[2].get('name')):
        print(' osm',w[2].get('name'),w[2].get('highway'),ax.sa(w[1][0]),ax.sa(w[1][-1]),w[2].get('layer'))
