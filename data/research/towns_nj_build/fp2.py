import duckdb,json,math,os
from shapely import wkb
os.chdir('/home/user/nyc')
con=duckdb.connect(); con.execute("SET memory_limit='1500MB'")
SPEC=[('HUGHES','nj_mercer','id','55180346'),('STMARY','nj_mercer','name','Cathedral of Saint Mary of the Assumption'),('BANK','nj_mercer','id','2a126f24'),('COURTHOUSE','nj_mercer','id','eef1c480'),('CITYHALL','nj_mercer','nameeq','City Hall'),('ROEBLING','nj_mercer','id','d854f05d'),('CURE','nj_mercer','id','b3aba644'),
 ('JJ','nj_middlesex','id','729e7648'),('NBPAC','nj_middlesex','id','18195d41'),('GATEWAY','nj_middlesex','id','83fbc3e2'),('KIRKPATRICK','nj_middlesex','id','e0f294f4'),('WINANTS','nj_middlesex','id','dff6b486'),('STATETHEATRE','nj_middlesex','id','c102f56f'),('VOORHEES','nj_middlesex','id','eeafb7e0')]
out=[];js={}
for key,par,mode,v in SPEC:
    w={'id':f"id like '{v}%'",'name':f"name like '{v}%'",'nameeq':f"name = '{v}' and lat between 40.21 and 40.23 and lon between -74.78 and -74.74"}[mode]
    r=con.execute(f"select id,name,area_m2,height_m,geometry from 'data/interim/counties/{par}.parquet' where {w} order by area_m2 desc limit 1").fetchone()
    s=wkb.loads(bytes(r[4]))
    if s.geom_type=='MultiPolygon': s=max(s.geoms,key=lambda p:p.area)
    rp=s.representative_point(); alon,alat=round(rp.x,6),round(rp.y,6)
    k=111320*math.cos(math.radians(alat)); s2=s.simplify(0.35/111000)
    loc=lambda c:[[round((x-alon)*k,1),round((y-alat)*110574,1)] for x,y in list(c)[:-1]]
    ext=loc(s2.exterior.coords); holes=[loc(q.coords) for q in s2.interiors]
    fl=lambda rr:', '.join(f'{a}, {b}' for a,b in rr)
    out.append(f"const {key} = P({fl(ext)});\n"+''.join(f"const {key}_H{i} = P({fl(h)});\n" for i,h in enumerate(holes))+f"const {key}_ANCHOR: V2 = [{alon}, {alat}];")
    # obb
    best=None
    for a in range(0,180):
        t=math.radians(a);c_,s_=math.cos(t),math.sin(t)
        us=[x*c_+y*s_ for x,y in ext];vs=[-x*s_+y*c_ for x,y in ext]
        ar=(max(us)-min(us))*(max(vs)-min(vs))
        if best is None or ar<best[0]: best=(ar,a,max(us)-min(us),max(vs)-min(vs))
    print(key,r[0][:8],r[1],round(r[2]),r[3] and round(r[3],1),'verts',len(ext),'holes',len(holes),'obb axis-angle(deg from +x ccw)',best[1],'u=%.1f v=%.1f'%(best[2],best[3]),alon,alat)
    js[key]=dict(id=r[0],anchor=[alon,alat],area=r[2],h=r[3],ext=ext,holes=holes)
open('data/research/towns_nj_build/rings.ts.txt','w').write('\n'.join(out)+'\n'); json.dump(js,open('data/research/towns_nj_build/fps.json','w'))
