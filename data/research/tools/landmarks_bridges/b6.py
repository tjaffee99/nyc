import sys; sys.path.insert(0,'data/interim/landmarks_bridges')
from binfo import *
def grp(key, a, b, others, outline, names, pad=0.012, near=30, step=None, stations=None):
    o=osm(key); c=lambda i: centroid(way(o,i)[1])[0]
    ax,o=info(key,None,None,[a,b]+list(others),outline,ptsA=c(a),ptsB=c(b),files=('roads_region','rail'),pad=pad,near=near,step=step)
    if stations: elevs(ax,stations)
    for nm in names:
        for n,cl,ls,i in ov('roads_region',f"name = '{nm}'",(ax.anchor[0]-pad,ax.anchor[1]-pad,ax.anchor[0]+pad,ax.anchor[1]+pad)):
            cs=list(ls.coords); print('   named',nm,cl,round(length(ls)),'from',ax.sa(cs[0]),'to',ax.sa(cs[-1]),'ground',round(elev(*cs[0]),1),round(elev(*cs[-1]),1))
    return ax,o
ax,o=grp('highbridge_washington',1016652745,1016656588,(),393767161,[],step=40,stations=range(-200,321,40))
for w in o['bridgeways']:
    if w[2].get('name')=='High Bridge': print('   HB way',[ax.sa(p) for p in w[1]])
ax,o=grp('highbridge_washington',1016657081,1016657082,(1016657084,1016657085),393737880,['Washington Bridge'],step=80,stations=range(-320,481,40))
ax,o=grp('macombs',1016651859,1016651857,(1016651861,1016651858,1016651860),395345273,['Macombs Dam Bridge','West 155th Street'],step=60,stations=range(-400,401,50))
ax,o=grp('university',1016657433,1016657432,(1016657434,),393646027,['University Heights Bridge','West Fordham Road'],stations=range(-200,201,40))
ax,o=grp('broadway_hudson',1016658464,1016658466,(),393475098,['Broadway'],stations=range(-160,161,40))
ax,o=grp('broadway_hudson',1016658824,1016658822,(1016658825,1016658823),393475101,['Henry Hudson Parkway'],step=100,stations=range(-400,401,50))
