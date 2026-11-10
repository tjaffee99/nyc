import sys; sys.path.insert(0,'data/interim/landmarks_bridges')
from binfo import *
o=osm('hellgate_rfk')
ax,o=info('hellgate_rfk',1016643613,1016643614,(),394608567,files=('rail',),near=40,pad=0.03)
# rail centre line: all bridge-flagged NEC parts in window, as station/offset lists
segs=[s for s in ov('rail',"name in ('Northeast Corridor','Fremont Industrial Track','Hell Gate Line')",(-73.94,40.765,-73.895,40.815))]
for n,c,ls,i in segs:
    cs=list(ls.coords); print('  rail',n,round(length(ls)),i[:8],'from',ax.sa(cs[0]),'to',ax.sa(cs[-1]),f'{cs[0][0]:.6f},{cs[0][1]:.6f} -> {cs[-1][0]:.6f},{cs[-1][1]:.6f}')
# outline of the viaducts
for wid in (1256780010,1257919846):
    w=way(o,wid); al=[ax.al(p) for p in w[1]]; print('  viaduct outline',wid,'along',round(min(al)),round(max(al)), 'n',len(w[1]))
print('--- RFK suspension')
ax2,o=info('hellgate_rfk',1016642595,1016642596,(),576000507,files=('roads_region',),near=40,step=200)
elevs(ax2,range(-900,901,100))
for n,c,ls,i in ov('roads_region',"name = 'Robert F. Kennedy Bridge'"):
    cs=list(ls.coords); print('  rfk',c,round(length(ls)),i[:8],'from',ax2.sa(cs[0]),'to',ax2.sa(cs[-1]),f'{cs[0][0]:.6f},{cs[0][1]:.6f} -> {cs[-1][0]:.6f},{cs[-1][1]:.6f}',len(cs))
