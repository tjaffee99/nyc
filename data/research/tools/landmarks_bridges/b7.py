import sys; sys.path.insert(0,'data/interim/landmarks_bridges')
from binfo import *
def grp(key, a, b, others, outline, names, pad=0.03, near=30, step=None, stations=None):
    o=osm(key); c=lambda i: centroid(way(o,i)[1])[0]
    ax,o=info(key,None,None,[a,b]+list(others),outline,ptsA=c(a),ptsB=c(b),files=(),pad=pad,near=near,step=step)
    if stations: elevs(ax,stations)
    for nm in names:
        for n,cl,ls,i in ov('roads_region',f"name = '{nm}'",(ax.anchor[0]-pad,ax.anchor[1]-pad,ax.anchor[0]+pad,ax.anchor[1]+pad)):
            cs=list(ls.coords); k=max(1,len(cs)//5)
            print('   named',nm[:22],cl,round(length(ls)),i[:8],[ax.sa(p) for p in cs[::k]]+[ax.sa(cs[-1])],'ground',round(elev(*cs[0]),1),round(elev(*cs[-1]),1))
    return ax,o
grp('whitestone',1016686393,1016686394,(1016686391,1016686396),392614465,['Bronx-Whitestone Bridge'],stations=range(-1800,1801,200))
grp('throgsneck',1016661640,1016661642,(1016661637,1016661644),392791505,['Throgs Neck Bridge'],stations=range(-1800,1801,200))
grp('bayonne',1013440560,1016686886,(),None,['Bayonne Bridge'],stations=range(-1200,1201,150))
grp('outerbridge',1016687789,1016687791,(1016687794,1016687790,1016687792,1016687793),393391585,['Outerbridge Crossing'],stations=range(-1500,1501,150))
grp('roosevelt',1016496518,1016496519,(),395985758,['Roosevelt Island Bridge'],pad=0.01,stations=range(-500,501,50))
grp('pulaski',1054539113,992001660,(),371935773,['Pulaski Bridge'],pad=0.01,stations=range(-450,451,50))
