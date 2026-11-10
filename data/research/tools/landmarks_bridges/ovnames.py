import sys; sys.path.insert(0,'data/interim/landmarks_bridges')
from blib import *
names=sys.argv[1:]
for nm in names:
    print('==',nm)
    segs=ov('roads_region',f"name = '{nm}'")
    allp=[]
    for n,c,ls,i in segs:
        cs=list(ls.coords); allp+= [cs[0],cs[-1]]
        print(f'   {c} {length(ls):7.0f} m  {cs[0][0]:.6f},{cs[0][1]:.6f} -> {cs[-1][0]:.6f},{cs[-1][1]:.6f}  {i[:8]} npts {len(cs)}')
    # farthest pair
    best=(0,None,None)
    for p in allp:
        for q in allp:
            d=math.hypot(*loc(p,q))
            if d>best[0]: best=(d,p,q)
    if best[1]: print(f'   extent {best[0]:.0f} m: {best[1][0]:.6f},{best[1][1]:.6f} .. {best[2][0]:.6f},{best[2][1]:.6f}  ground {elev(*best[1]):.1f} / {elev(*best[2]):.1f}')
