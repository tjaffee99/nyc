import sys; sys.path.insert(0,'data/interim/landmarks_bridges')
from blib import *
from shapely.geometry import box as sbox
out=[]
def emitN(name, lists, comment=''):
    out.append(f"const {name}: V2[][] = [\n  "+',\n  '.join(fmt(p) for p in lists)+f"\n];{' // '+comment if comment else ''}")
def outside(name, ax, y0, y1, label, tol=1.5, halfw=60, where=None, file='roads_region', minlen=20):
    """pieces of the named bridge-flagged segments outside stations [y0,y1] of the frame, oriented from the frame outward"""
    res=[]
    rect=sbox(y0,-halfw,y1,halfw)
    for n,c,ls,i in ov(file, where or f"name = '{name}'", (ax.anchor[0]-0.04,ax.anchor[1]-0.04,ax.anchor[0]+0.04,ax.anchor[1]+0.04)):
        M=LineString([(ax.al(p),ax.ac(p)) for p in ls.coords])
        d=M.difference(rect)
        for p in (list(d.geoms) if hasattr(d,'geoms') else [d]):
            if p.is_empty or p.length<minlen: continue
            p=p.simplify(tol); cc=list(p.coords)
            if Point(cc[-1]).distance(rect) < Point(cc[0]).distance(rect): cc=cc[::-1]
            ll=[unloc(ax.anchor,(a*ax.ux+o*ax.uy, a*ax.uy-o*ax.ux)) for a,o in cc]
            res.append(ll)
            print(f'  {label} {i[:8]} {p.length:.0f} m from ({cc[0][0]:.0f},{cc[0][1]:.0f}) to ({cc[-1][0]:.0f},{cc[-1][1]:.0f}) npts {len(cc)} end ground {elev(*ll[-1]):.1f}')
    return res
tn=Axis((-73.793647,40.802753),(-73.793599,40.797806))
emitN('TN_PATHS', outside('Throgs Neck Bridge',tn,-1100,820,'TN'), 'Overture carriageways beyond the straight viaducts (Bronx curve, Queens end), from the bridge outward')
by=Axis((-74.141287,40.644153),(-74.143182,40.639554))
emitN('BY_PATHS', outside('Bayonne Bridge',by,-290,290,'BY'), 'Overture carriageways of the Bayonne and Port Richmond viaducts, from the arch abutments outward')
ob=Axis((-74.24943,40.524669),(-74.246739,40.524818))
emitN('OB_PATHS', outside('Outerbridge Crossing',ob,-600,930,'OB'), 'Overture carriageways of the New Jersey approach beyond the straight, from the bridge outward')
# Goethals
o=osm('goethals'); c=lambda i: centroid(way(o,i)[1])[0]
e1,e2,w1,w2=c(1016689044),c(1016689045),c(1016689046),c(1016689047)
print('goethals supports',e1,e2,w1,w2)
mid=lambda a,b:((a[0]+b[0])/2,(a[1]+b[1])/2)
ga=Axis(mid(w1,w2),mid(e1,e2))
print('GOE axis W',mid(w1,w2),'E',mid(e1,e2),'dist',round(ga.len,1),'cited 274.3 bearing',round(ga.bearing,2))
for nm,p in (('e1',e1),('e2',e2),('w1',w1),('w2',w2)): print('  ',nm,ga.sa(p))
for n,cl,ls,i in ov('roads_region',"name = 'Goethals Bridge'"):
    cs=list(ls.coords); k=max(1,len(cs)//6); print('  goe seg',cl,round(length(ls)),i[:8],[ga.sa(p) for p in cs[::k]]+[ga.sa(cs[-1])],'ground',round(elev(*cs[0]),1),round(elev(*cs[-1]),1))
print('  ground:',' '.join(f'{s}:{elev(*unloc(ga.anchor,(s*ga.ux,s*ga.uy))):.1f}' for s in range(-1200,1201,150)))
emitN('GO_PATHS', outside('Goethals Bridge',ga,-420,420,'GO',halfw=80), 'Overture carriageways of the approach viaducts, from the cable-stayed spans outward')
# Macombs: W 155th St viaduct
o=osm('macombs'); c=lambda i: centroid(way(o,i)[1])[0]
A=mid(c(1016651859),c(1016651860)); B=mid(c(1016651857),c(1016651858)); ma=Axis(A,B)
print('MACOMBS axis',A,B,'dist',round(ma.len,1),'bearing',round(ma.bearing,2),'pivot',ma.sa(c(1016651861)))
emitN('MD_PATHS', outside('West 155th Street',ma,-64,500,'MD',halfw=40)+outside('Macombs Dam Bridge',ma,-64,202,'MD2',halfw=40), '155th Street viaduct (Overture West 155th Street, bridge flag) and the Bronx end beyond Jerome Avenue, from the bridge outward')
open(f'{D}/gen2.ts.txt','w').write('\n'.join(out)+'\n'); print('chars',sum(len(x) for x in out))
