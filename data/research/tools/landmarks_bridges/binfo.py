import sys; sys.path.insert(0,'data/interim/landmarks_bridges')
from blib import *
def info(key, tA, tB, others=(), outline=None, files=('roads_region','rail'), pad=0.02, near=30, step=None, ptsA=None, ptsB=None):
    o=osm(key)
    cA = ptsA or centroid(way(o,tA)[1])[0]; cB = ptsB or centroid(way(o,tB)[1])[0]
    ax=Axis(cA,cB)
    print(f'## {key}: A {cA[0]:.6f},{cA[1]:.6f}  B {cB[0]:.6f},{cB[1]:.6f}  dist {ax.len:.1f} m  bearing {ax.bearing:.2f}  anchor {ax.anchor[0]:.6f},{ax.anchor[1]:.6f}')
    for i in ([tA,tB] if tA else [])+list(others):
        w=way(o,i); c,_=centroid(w[1]); print('  way',i,f'{c[0]:.6f},{c[1]:.6f}','sa',ax.sa(c),'mrr',[(round(a,1),round(b)) for a,b in mrr(w[1])], w[2].get('bridge:support'),w[2].get('height'))
    if outline:
        w=way(o,outline); P=Polygon([(ax.al(p),ax.ac(p)) for p in w[1]])
        b=P.bounds; print('  outline along',round(b[0]),round(b[2]),'across',round(b[1]),round(b[3]))
        if step:
            for s in range(int(b[0]//step*step),int(b[2])+1,step):
                it=P.intersection(LineString([(s,-900),(s,900)]))
                if not it.is_empty: print('    s',s,[round(v,1) for v in it.bounds[1::2]])
    a=ax.anchor; bb=(a[0]-pad,a[1]-pad,a[0]+pad,a[1]+pad)
    res=[]
    for f in files:
        for n,c,ls,i in ov(f,'true',bb):
            cs=list(ls.coords)
            if len(cs)<2: continue
            L=LineString([(ax.al(p),ax.ac(p)) for p in cs])
            if L.distance(Point(0,0))<near:
                acs=[q[1] for q in L.coords]
                res.append((f,n,c,round(length(ls)),ax.sa(cs[0]),ax.sa(cs[-1]),round(min(acs)),round(max(acs)),i[:8]))
    for r in sorted(res,key=lambda r:(str(r[1]),r[4][0])): print('  ov',r)
    return ax,o
def elevs(ax,stations,across=0):
    print('  ground:',' '.join(f'{s}:{elev(*unloc(ax.anchor,(s*ax.ux+across*ax.uy, s*ax.uy-across*ax.ux))):.1f}' for s in stations))
if __name__=='__main__':
    ax,o=info('manhattan',1255353996,317352033,(1017507380,1255353998))
    elevs(ax,range(-1100,1101,100))
    ax,o=info('williamsburg',1016434034,1016434035,(1016434036,279593081),533212910,step=200)
    elevs(ax,range(-1300,1301,100))
    ax,o=info('gwb',741784699,741784700,(899357171,),392759062,step=250)
    elevs(ax,range(-1000,1001,100))
