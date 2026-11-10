import sys; sys.path.insert(0,'data/interim/landmarks_bridges')
from binfo import *
o=osm('queensboro')
c=lambda i: centroid(way(o,i)[1])[0]
ax,o=info('queensboro',None,None,(1016487161,1016487159,1016487155,1016487154,1016487157,1016487170,1016487160,1016487156,1016487153,1016487158),500906008,ptsA=c(1016487159),ptsB=c(1016487155),step=250,near=25)
elevs(ax,range(-700,1701,100))
# lower level centre line stations
for n,cl,ls,i in ov('roads_region',"name like 'Ed Koch Queensboro Bridge Lower%'"):
    print('  line',n,[ax.sa(p) for p in ls.coords])
ax,o=info('verrazzano',1016642058,1016642060,(899356447,899356446),375153091,step=250,pad=0.03)
elevs(ax,range(-1500,1501,100))
for n,cl,ls,i in ov('roads_region',"name = 'Verrazzano-Narrows Bridge'"):
    cs=list(ls.coords); print('  line',round(length(ls)),[ax.sa(p) for p in cs[::max(1,len(cs)//6)]]+[ax.sa(cs[-1])])
