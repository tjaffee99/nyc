"""Emit TS constants: Hell Gate rail line, RFK carriageway paths (clipped to the viaducts)."""
import sys; sys.path.insert(0,'data/interim/landmarks_bridges')
from blib import *
import json
from shapely.geometry import box as sbox
from shapely import affinity
out=[]
def emit(name, pts, comment=''):
    out.append(f"const {name}: V2[] = {fmt(pts)};{' // '+comment if comment else ''}")
def emitN(name, lists, comment=''):
    out.append(f"const {name}: V2[][] = [\n  "+',\n  '.join(fmt(p) for p in lists)+f"\n];{' // '+comment if comment else ''}")
# ---- Hell Gate line (Bronx -> Queens)
L=json.load(open(f'{D}/hellgate_line.json'))['line']
emit('HG_LINE', L, 'Overture rail segment fb010fe0 (Northeast Corridor, bridge flag), Bronx end → Queens end, 5,055 m')
# ---- RFK
R=json.load(open(f'{D}/rfk_lines.json'))
def clip(key, ax, half, halfw=45, tol=1.5, keep=None):
    """pieces of carriageway `key` outside the rectangle |along|<=half,|across|<=halfw of axis ax; oriented starting at the rectangle"""
    cs=R[key]; M=LineString([(ax.al(p),ax.ac(p)) for p in cs])
    rect=sbox(-halfw,-half,halfw,half)  # (across, along) -> we use (al, ac) order so swap
    rect=sbox(-half,-halfw,half,halfw)
    d=M.difference(rect)
    parts=list(d.geoms) if hasattr(d,'geoms') else [d]
    res=[]
    for p in parts:
        if p.is_empty or p.length<5: continue
        p=p.simplify(tol); c=list(p.coords)
        if Point(c[-1]).distance(rect) < Point(c[0]).distance(rect): c=c[::-1]
        ll=[unloc(ax.anchor,(a*ax.ux+o*ax.uy, a*ax.uy-o*ax.ux)) for a,o in c]
        res.append((ll, round(p.length), (round(c[0][0]),round(c[0][1])), (round(c[-1][0]),round(c[-1][1]))))
    return res
sax=Axis((-73.927945,40.781308),(-73.925444,40.778032))
print('RFK susp axis', sax.anchor, sax.bearing, sax.len)
pieces=[]
for k in ('c6f25955','255396ef'):
    for ll,ln,a,b in clip(k,sax,sax.len/2+700*0.3048):
        print('  susp piece',k,ln,'m from',a,'to',b); pieces.append((k,ll,a,b))
q=[p[1] for p in pieces if p[2][0]>0]; w=[p[1] for p in pieces if p[2][0]<0]
f69=LineString([loc(sax.anchor,p) for p in R['f69b3055']]).simplify(1.5); f69=[unloc(sax.anchor,p) for p in f69.coords][::-1]
emitN('RFK_Q', q, 'Queens approach, both carriageways, from the anchorage outward')
emitN('RFK_W', w, 'Wards / Randalls Island viaduct, both carriageways, from the anchorage to the junction')
emit('RFK_W2', f69, 'southbound link at the junction (Overture f69b3055), from the viaduct to the junction')
for p in w: print('   W end', p[-1], 'ground', round(elev(*p[-1]),1))
for p in q: print('   Q end', p[-1], 'ground', round(elev(*p[-1]),1))
# ---- Bronx Kill frame
lax=Axis((-73.92872065746688,40.80071737314366),(-73.9276405,40.80026175))
C=unloc(lax.anchor,(762*lax.ux + (-217)*lax.uy, 762*lax.uy - (-217)*lax.ux))
# axis along bearing lax.bearing-90 (toward the Bronx)
import math
br=math.radians(lax.bearing-90); u=(math.sin(br),math.cos(br))
S=unloc(C,(-58.35*u[0],-58.35*u[1])); N=unloc(C,(58.35*u[0],58.35*u[1]))
bax=Axis(S,N)
print('Bronx Kill truss S',S,'N',N,'bearing',bax.bearing,'len',bax.len)
bp=[]
for k in ('51c3eda8','40775599','fa5cdb4c','41aa5b56'):
    for ll,ln,a,b in clip(k,bax,58.35):
        print('  bk piece',k,ln,'m from',a,'to',b, 'end ground', round(elev(*ll[-1]),1)); bp.append(ll)
emitN('RFK_B', bp, 'Bronx Kill approaches and the Randalls Island viaduct to the junction, from the truss outward')
out.append(f"const RFK_BK: [V2, V2] = {fmt([S,N])}; // ends of the Bronx Kill truss span (383 ft) on the carriageways' centre line")
print('lift axis anchor',lax.anchor,'bearing',lax.bearing)
open(f'{D}/gen1.ts.txt','w').write('\n'.join(out)+'\n')
print('chars',sum(len(o) for o in out))
