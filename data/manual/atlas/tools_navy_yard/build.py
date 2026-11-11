"""Builds data/tables/known_building_dates.navy_yard.csv and notable_demolished.navy_yard.csv.
Inputs: data/raw/navy_yard/nrhp_14000261.pdf (NPS NRHP nomination, plan pages 155-158; label boxes from
`pdftotext -bbox`), registration json (reg.py / reg155.py: affine page-point -> UTM 18N from labelled
standing buildings), seg156.json (shaded rectangles found on the 1890 plan by seg.py), built file window.
Run with the scratch dir S holding bb*.html, reg.json, seg156.json."""
import json, re, csv, sys, numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import Polygon, shape, Point, box
from shapely import affinity
from pyproj import Transformer
S=sys.argv[1]; R='/home/user/nyc/'
reg=json.load(open(f'{S}/reg.json')); T=Transformer.from_crs(32618,4326,always_xy=True)
def topt(m,px,py,origin,k): return (origin[0]+px/k, origin[1]+py/k)
def utm(m,p):
    r=reg[m]; x,y=p; return (r['cx'][0]*x+r['cx'][1]*y+r['cx'][2], r['cy'][0]*x+r['cy'][1]*y+r['cy'][2])
def poly_from_px(m,pxs,origin,k): return Polygon([utm(m,topt(m,x,y,origin,k)) for x,y in pxs])
def rect_px(cx,cy,L,W,ang):
    a=np.radians(ang); u=np.array([np.cos(a),np.sin(a)]); v=np.array([-u[1],u[0]])
    c=np.array([cx,cy]); return [tuple(c+s*L/2*u+t*W/2*v) for s,t in ((-1,-1),(1,-1),(1,1),(-1,1))]
# ---- built file
w=gpd.read_parquet(R+'data/interim/navy_yard/win.parquet'); w['name']=w.name.astype('string')
g=json.load(open(R+'data/manual/sites/sites.geojson'))
yard=[shape(f['geometry']) for f in g['features'] if f['properties']['id']=='brooklyn_navy_yard'][0]
yardm=gpd.GeoSeries([yard],crs=4326).to_crs(32618).iloc[0]
wm=w.to_crs(32618); w['geom_m']=wm.geometry
stand=w[w.end_year==9999]; van=w[w.end_year<9999]
NRHP='https://npgallery.nps.gov/GetAsset/314d2a7b-7525-4998-8a77-dd3b9dba7073'; WP='https://en.wikipedia.org/wiki/Brooklyn_Navy_Yard'
# ---- standing rows
D={ '1':(1942,'Materials Testing Laboratory (former Building 291)','NRHP list: 1941-42 (Wikipedia: c. 1941-1942); range - estimated',NRHP),
 '2':(1942,'Foundry (former Building 290)','NRHP: built on the Wallabout Market ground, erected in four and a half months, opened 1942',NRHP),
 '3':(1917,'Supply Storehouse','NRHP text: contract April 1917, finished September 1917, Navy moved in 1 Oct 1917 (the NRHP list says 1918); Wikipedia: same',NRHP),
 '4':(1944,'Ordnance/Gun Shed (former Building 424)','NRHP non-contributing list: 1944',NRHP),
 '5':(1920,'Light Machine Shop, Electrical & Ordnance, Radio Station','NRHP list: 1920 (the plan of the period: ordered with Building 3, 1917-20; NRHP gives 1920)',NRHP),
 '6':(1955,'Acetylene House (former Building 666)','NRHP non-contributing list: 1955',NRHP),
 '10':(1851,'Engine/Pump House for Dry Dock No. 1','NRHP: 1849-51 (additions 1903, 1936); start year = completion of the dock 1851 - estimated within 1849-51',NRHP),
 '11':(1855,'Buildings 11/11A complex (plumbers and boiler shop, smithery)','NRHP: ca. 1855 (photo captions; use history lists a smithery and foundry in 1862) - estimated',NRHP),
 '12':(1855,'Building 12 (plumbers and boiler shop)','NRHP: ca. 1855 - estimated',NRHP),
 '20':(1865,'Iron Plating Shop','NRHP: 1865 (additions ca. 1882, ca. 1909)',NRHP),
 '22':(1855,'Timber Shed, Mold Loft','NRHP: ca. 1855 - estimated',NRHP),
 '27':(1899,'Administration Building','NRHP: 1899 (addition ca. 1919)',NRHP),
 '30':(1899,'Pattern Shop','NRHP: 1899 (addition 1903)',NRHP),
 '41':(1941,'Central Power Plant','NRHP list: 1941 (Wikipedia: built 1942, replacing the 1899 electric light station); range - estimated',NRHP),
 '42/46':(1919,'Chipping Shed (1919) / Sand House (1922)','NRHP non-contributing list: 1919 and 1922; the earlier year is used for the joint footprint - estimated',NRHP),
 '50':(1936,'Yard Garage, Auto Repair Shop (50/50A)','NRHP: 1936 (addition ca. 1970)',NRHP),
 '51':(1938,'Garbage Incinerator','NRHP: 1938',NRHP),
 '52':(1938,'Coal Plant Office','NRHP: 1938',NRHP),
 '58':(1940,'USMC Non-Commissioned Officers Quarters','NRHP: 1940',NRHP),
 '62':(1940,'Paint Shop','NRHP: 1940',NRHP),
 '74':(1862,'Lime, Pitch and Coal House','NRHP: ca. 1862, moved 1916, second story 1926 - estimated (the standing structure is the moved one)',NRHP),
 '77':(1942,'General Storehouse, Administration Building','NRHP: 1942 (foundation June 1941; Wikipedia: completed September 1941); range 1941-42 - estimated',NRHP),
 '92':(1857,'Marine Corps Commandant/Officers Quarters (Building 92)','Wikipedia: built 1857 (Thomas U. Walter); NRHP list: 1858; range - estimated',WP),
 '120':(1899,'Oil Storehouse','NRHP: 1899',NRHP),
 '121':(1900,'Paymasters Office','NRHP: 1900, moved 1918 (the standing position is the moved one)',NRHP),
 '127':(1903,'Boat Storehouse (rebuilt from the c.1855 timber shed Building 21)','NRHP: 1903',NRHP),
 '128':(1899,'Machine and Erecting Shop (Building 128)','NRHP / Wikipedia: c. 1899-1900 - estimated',NRHP),
 '131':(1902,'Construction & Repair Storehouse and Shops','NRHP: 1902 (addition ca. 1904)',NRHP),
 '132':(1905,'Locomotive Shed (steam engine repair shop)','NRHP: 1905',NRHP),
 '152':(1920,'Chemical Lab','NRHP: 1920',NRHP),
 '249':(1938,'Electric Sub-Station No. 13','NRHP: 1938',NRHP),
 '268':(1941,'Sub-Assembly Shop No. 1','NRHP non-contributing list: 1941 (renovated 2012)',NRHP),
 '269':(1941,'Sub-Assembly Shop No. 2','NRHP: 1941-42; range - estimated',NRHP),
 '275':(1942,'Building Trades Shops','NRHP: 1942',NRHP),
 '280':(1942,'Ordnance Machine Shop','NRHP: 1942 (replaced a nineteenth-century foundry)',NRHP),
 '292':(1942,'Production Utility Building','NRHP: 1942',NRHP),
 '293':(1970,'Paint Fabrication Facility','NRHP non-contributing list: 1970 (Wikipedia: c. 1970s)',NRHP),
 '314':(1942,'Canteen','NRHP: 1942',NRHP),
 '500':(2000,'Duggal Visual Solutions','NRHP non-contributing list: ca. 2000 - estimated',NRHP),
 '991':(1961,'Pump House','NRHP non-contributing list: 1961',NRHP),
 '594':(1941,'Building 270/594, Compressor Building (1941-42) and Field Cafeteria (1943)','NRHP: 1941-42; range - estimated',NRHP)}
rows=[]; newstart={}
for n,(yr,desc,why,url) in D.items():
    s=stand[stand.name==n]
    if len(s)==0: print('NO FOOTPRINT',n); continue
    for b_,gg in s.groupby('bin'):
        gg=gg.assign(a=gg.geom_m.area).sort_values('a',ascending=False)
        if len(s.bin.unique())>1 and gg.a.iloc[0]<400 and n in('128','131'): continue
        p=gg.geometry.iloc[0].representative_point()
        est='estimated' in why
        rows.append(dict(id=f'ny_b{n.replace("/","_")}',name=f'Building {n}: {desc}',lat=round(p.y,6),lon=round(p.x,6),bin=int(b_),start_year=yr,end_year=9999,source_url=url,
            note=(why+('. ' if not why.endswith('.') else ' ')+f'Matched by the city footprint named "{n}" (BIN {int(b_)}); built file had {gg.start_year.iloc[0]:.0f} ({gg.year_src.iloc[0]}).')))
        newstart[int(b_)]=yr
HOSP=[(3395464,'R5','Infectious Diseases Quarters',1915),(3395463,'R6','Infectious Diseases Quarters',1915),(3395462,'R7','Infectious Diseases Quarters',1915),
      (3348107,'R4','Quarters No. 4',1864),(3348100,'R104','Guard House and Gate Keeper Lodge',1850),(3057919,'311','Motion Picture Exchange',1942)]
for b_,lab,desc,yr in HOSP:
    s=stand[stand.bin==b_]
    if len(s)==0: print('NO HOSP',b_); continue
    p=s.geometry.iloc[0].representative_point()
    rows.append(dict(id=f'ny_nh_{lab}',name=f'Naval Hospital Building {lab}: {desc}',lat=round(p.y,6),lon=round(p.x,6),bin=b_,start_year=yr,end_year=9999,source_url=NRHP,
      note=f'NRHP inventory (Area 3, U.S. Naval Hospital): {desc}, {"ca. " if yr in (1864,1850) else ""}{yr}; building number matched to this footprint by the position of its label on NRHP Map #15 (1946 plan) registered to the footprints (nearest footprint {"" }within 14-25 m): the match is estimated; built file had {s.start_year.iloc[0]:.0f} ({s.year_src.iloc[0]}). Year estimated where "ca.".'))
    newstart[b_]=yr
pd.DataFrame(rows).to_csv(R+'data/tables/known_building_dates.navy_yard.csv',index=False)
print('standing rows',len(rows))
# ---- lost structures
cands=[]   # dict: id,name,start,end,h,st,mat,poly_m,note,url,kind
seg=json.load(open(f'{S}/seg156.json')); lab156=[]
t=open(f'{S}/bb156.html').read()
for x in re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>',t):
    lab156.append(((float(x[0])+float(x[2]))/2,(float(x[1])+float(x[3]))/2))
def add(**k): cands.append(k)
U1890='NRHP Map #13 (1890 plan of the yard, Brooklyn Navy Yard Archives; traced from the registered image)'
# manual 1890 plan shapes
o156=(40,300); k156=300/72*0+4.1667
add(id='ny_timber_shed_15',name='Building 15, timber shed (twin of Building 16)',start=1841,end=1980,h=9,st=1,mat='brick',
    poly=poly_from_px('156',[(183,502),(217,502),(217,727),(183,727)],o156,k156),
    note=f'Start ca. 1841 (NRHP: built c. 1841 as one of a pair with Building 16); part demolished 1937 (WPA), the rest "probably after 1979" (Wikipedia) so end 1980 is estimated; outline traced from the 1890 plan ({U1890}), +-10 m; height estimated; the NRHP gives 300 ft x 60 ft for Building 15 but the plan shows about 120 m (400 ft) - outline as drawn.',url=NRHP)
sh=poly_from_px('156',[(270,258),(350,262),(355,420),(335,432),(268,420)],(67.2,211.2),4.1667)
add(id='ny_ship_house_d_1890',name='Ship house (shown "Ship House D" on the 1890 plan)',start=1820,end=1893,h=25,st=1,mat='frame',poly=sh,
    note='Wooden ship houses of the building ways were built in 1820 and "up until 1893" covered the ways (NRHP section 8; NYT 15 Oct 1893 "Last of an Old Ship House"); that this one is of 1820 is estimated; outline traced from the 1890 plan, +-10 m; height estimated.',url=NRHP)
# automatic 1890 boxes
pxc=lambda pts:[(x,y) for x,y in pts]
nseg=0
segb=json.load(open(f'{S}/seg156b.json'))
accepted=[]
for bx in seg['boxes']+segb['boxes']:
    pts=bx; poly=poly_from_px('156',pts,o156,seg['k'])
    if any(poly.intersection(q).area>0.3*poly.area for q in accepted): continue
    cxy=np.mean(pts[:4],axis=0); cpt=(o156[0]+cxy[0]/seg['k'],o156[1]+cxy[1]/seg['k'])
    ls=[np.hypot(pts[i+1][0]-pts[i][0],pts[i+1][1]-pts[i][1]) for i in range(2)]
    if max(ls)/min(ls)<2.2: continue
    if any(Point(lx,ly).distance(Point(cpt))<8 for lx,ly in lab156): continue
    if poly.area<300 or poly.area>3500: continue
    nseg+=1; accepted.append(poly)
    add(id=f'ny_plan1890_{nseg:02d}',name=f'Yard shop or storehouse {nseg} (shown on the 1872 and 1890 plans)',start=1862,end=1980,h=8,st=1,mat='brick',poly=poly,
        note=f'Shaded building on NRHP Map #13 (1890 plan) in the yard grid that the 1872 plan (Map #12) already shows built up; use not read (labels illegible); start 1862 estimated (the standing shops of this grid are dated ca. 1855-65 by the NRHP and the yard was built up by 1872), end estimated within 1946 (the grid is still built up on the 1946 plan) and 2016; outline a minimum rectangle fitted to the shaded area (+-8 m); height and material estimated.',url=NRHP)
# 1946 plan shapes
o158=(30,220); ob=(65,365); oc=(360,270); k=300/72
add(id='ny_building_18',name='Building 18, turret and erection shop',start=1940,end=1980,h=20,st=1,mat='steel',
    poly=poly_from_px('158',[(340,170),(393,178),(327,524),(262,498)],o158,k),
    note='NRHP: construction began 1939 for the battleship programme (800 ft x 100 ft, single bay, welding facilities and mold loft); start 1940 and end 1980 are estimated (demolished, no date found); outline traced from the 1946 plan (NRHP Map #15) registered to the standing buildings, +-10 m; height estimated.',url=NRHP)
add(id='ny_building_ways_2',name='Building Ways No. 2 (Connecticut ways, west slip)',start=1917,end=1970,h=4,st=1,mat='concrete',
    poly=poly_from_px('158',[(477,172),(527,172),(447,610),(390,596)],o158,k),
    note='NRHP: Building Ways No. 2 built 1917 (the Indiana, keel 1920); extended 1937-39; "demolished" (no date): end 1970 is estimated; outline from the 1946 plan, +-12 m (an open slipway, not a roofed building); height estimated.',url=NRHP)
add(id='ny_building_ways_1',name='Building Ways No. 1 (Connecticut ways, east slip)',start=1903,end=1970,h=4,st=1,mat='concrete',
    poly=poly_from_px('158',[(540,175),(588,175),(505,650),(447,610)],o158,k),
    note='NRHP: Building Ways No. 1 removed and rebuilt 1903 for the Connecticut (the Maine, 1890, was launched on the earlier ways); end 1970 estimated (demolished, no date); outline from the 1946 plan, +-12 m; height estimated.',url=NRHP)
add(id='ny_building_4_structural',name='Building 4, structural shop (later mold loft)',start=1918,end=1980,h=14,st=1,mat='steel',
    poly=poly_from_px('158',[(22,85),(115,80),(240,122),(310,128),(375,140),(330,215),(250,290),(205,310),(150,255),(95,195),(60,155),(35,130)],ob,k),
    note='NRHP: structural shop of ca. 1918-19 (Building 4, demolished; the name passed to the 1944 gun shed); start estimated within 1917-19, end 1980 estimated (no date); outline traced from the 1946 plan, +-12 m; height estimated.',url=NRHP)
for bid,nm,x0,x1,y0,y1 in (('294','Building 294, sub-assembly shop',335,420,475,838),('296','Building 296, sub-assembly shop',465,553,482,845)):
    add(id=f'ny_building_{bid}',name=nm,start=1942 if bid=='294' else 1943,end=2000,h=22,st=1,mat='steel',poly=poly_from_px('158',[(x0,y0),(x1,y0),(x1,y1),(x0,y1)],oc,k),
        note=f'NRHP: Buildings 294 and 296 (both demolished) built 1942 and 1943, 800-foot steel sheds on the Wallabout Market ground; end 2000 is estimated (demolished before 2014, no date found: range 1966-2013); outline from the 1946 plan, +-10 m; width, height and material estimated.',url=NRHP)
KENT=[('297','Building 297 (Kent Avenue Basin area)',[(473,395),(556,395),(556,420),(473,420)]),
      ('373','Building 373 (Kent Avenue Basin area)',[(608,478),(660,500),(665,535),(615,540)]),
      ('286','Building 286 (Kent Avenue Basin area; number read from the plan, uncertain)',rect_px(575,352,95,38,42)),
      ('299','Building 299 (Kent Avenue Basin area)',rect_px(375,238,68,40,25)),
      ('284','Building 284 (Kent Avenue Basin area; number read from the plan, uncertain)',rect_px(527,188,40,38,40))]
for bid,nm,pts in KENT:
    add(id=f'ny_building_{bid}',name=nm,start=1942,end=1980,h=10,st=1,mat='',poly=poly_from_px('158',pts,oc,k),
        note='NRHP: the Navy filled the Kent Avenue Basin in 1942 and built "nearly a dozen buildings, none of which survives"; start 1942 estimated (a plan of 1946 shows it), end 1980 estimated (range 1966-2014); outline traced from the 1946 plan, +-12 m; use, height and material estimated.',url=NRHP)
# 1872 plan: marine barracks, ship houses
o155=(0,0); k155=150/72
add(id='ny_building_91',name='Building 91, Marine barracks',start=1858,end=1918,h=12,st=2,mat='brick',poly=poly_from_px('155',rect_px(810,873,125,22,0),o155,k155),
    note='Wikipedia / NRHP: Marine Barracks Grounds laid out ca. 1858 (land bought 1848) around a parade ground, Building 91 a long barracks; razed ca. 1918 for Buildings 3 and 5; outline from the 1872 plan (NRHP Map #12) registered to six standing buildings (rms 5 m), +-15 m; storeys and height estimated.',url=NRHP)
b92=stand[stand.name=='92'].geom_m.iloc[0]
add(id='ny_building_93',name='Building 93, Marine officers quarters (twin of Building 92)',start=1858,end=1941,h=14,st=3,mat='brick',poly=poly_from_px('155',rect_px(893,950,25,30,0),o155,k155),
    note=f'NRHP / Wikipedia: nearly identical to Building 92 (three storeys, brick), at the opposite end of the parade ground; razed 1941 for Building 77. Position from the 1872 plan (+-20 m); plan size is the size of Building 92 ({b92.area:.0f} m2) - rectangle, estimated.',url=NRHP)
for i,(c,(L,W,a)) in enumerate((((330,495),(95,28,80)),((408,562),(70,28,70))),1):
    add(id=f'ny_ship_house_{i}_1872',name=f'Ship house {i} (as drawn on the 1872 plan)',start=1820,end=1893,h=25,st=1,mat='frame',poly=poly_from_px('155',rect_px(c[0],c[1],L,W,a),o155,k155),
        note='NRHP: two wooden ship houses built 1820, removed by 1893; the plan of 1872 (NRHP Map #12) shows them west of the Wallabout shore; outline a rectangle read off the registered plan (+-15 m); height estimated.',url=NRHP)
# ---- validate / filter
out=[]; rep=[]
for c in cands:
    pm=c['poly']
    if not pm.is_valid: pm=pm.buffer(0)
    c['poly']=pm
    inter=pm.intersection(yardm).area/pm.area
    ov_s=0; partner=None; replaced=None; cov=0
    for _,r in stand.iterrows():
        gm=r.geom_m
        if not gm.intersects(pm): continue
        ia=gm.intersection(pm).area
        b_=int(r.bin) if not pd.isna(r.bin) else None
        if not (b_ in newstart and newstart[b_]>c['start']): cov=max(cov,ia/pm.area)
        if ia/gm.area<0.2: continue
        if b_ in newstart:                      # standing building with a researched year
            if newstart[b_]<=c['start'] and ia/gm.area>=0.5: ov_s=max(ov_s,ia/gm.area); partner=b_
            elif newstart[b_]>c['start']: replaced=min(replaced or 9999,newstart[b_])
        elif r.year_src!='lot_year' and r.start_year<c['end'] and ia/gm.area>=0.5 and r.start_year<=c['start']:
            ov_s=max(ov_s,ia/gm.area); partner=b_
    if replaced and replaced<c['end']:
        c['end']=int(replaced); c['note']+=f' End set to {int(replaced)}, the year of the standing building that replaced it (estimated).'
    ov_v=0
    for _,r in van.iterrows():
        gm=r.geom_m
        if gm.intersects(pm) and r.start_year<c['end'] and c['start']<r.end_year:
            ov_v=max(ov_v,gm.intersection(pm).area/min(gm.area,pm.area))
    rep.append((c['id'],round(inter,2),round(ov_s,2),round(ov_v,2)))
    if inter<0.5 or ov_s>0 or ov_v>0.4 or cov>=0.5: c['drop']=True
    c['inter']=inter;c['ov_s']=ov_s;c['ov_v']=ov_v
    out.append(c)
for r in rep: print(r)
# Building 296: the traced outline coincides with a standing footprint -> dated row, not a lost building
s296=stand[stand.bin==3335182]
if len(s296):
    p=s296.geometry.iloc[0].representative_point()
    rows.append(dict(id='ny_b296',name='Building 296 (sub-assembly shop, 800 ft) - footprint on its site',lat=round(p.y,6),lon=round(p.x,6),bin=3335182,start_year=1943,end_year=9999,source_url=NRHP,
      note='estimated: NRHP says Buildings 294 and 296 (1942, 1943) were demolished, but the city footprint BIN 3335182 (14,833 m2, ~244 x 61 m) covers 85 % of the outline traced from the 1946 plan for 296: either the shed (or its frame) survives or a later building replaced it on the same plan; the year is 296\'s, the identity is uncertain; built file had 1959 (lot_year).'))
    newstart[3335182]=1943
    for c in out:
        if c['id']=='ny_building_296': c['drop']=True
pd.DataFrame(rows).to_csv(R+'data/tables/known_building_dates.navy_yard.csv',index=False)
fields=['id','name','start_year','end_year','lat','lon','height_m','storeys','material','outline','shape_note','source_url','footprint_m','rotation_deg']
with open(R+'data/tables/notable_demolished.navy_yard.csv','w',newline='') as f:
    wr=csv.DictWriter(f,fieldnames=fields); wr.writeheader(); nk=0
    for c in out:
        if c.get('drop'): continue
        pm=c['poly']; pm=pm.intersection(yardm) if c['inter']<0.999 else pm
        ll=[T.transform(x,y) for x,y in list(pm.exterior.coords)[:-1]]
        cc=pm.centroid; lon,lat=T.transform(cc.x,cc.y)
        wr.writerow(dict(id=c['id'],name=c['name'],start_year=c['start'],end_year=c['end'],lat=round(lat,6),lon=round(lon,6),height_m=c['h'],storeys=c['st'],material=c['mat'],
            outline='; '.join(f'{x:.6f} {y:.6f}' for x,y in ll),shape_note=c['note'],source_url=c['url'],footprint_m='',rotation_deg='')); nk+=1
import pickle
print('lost rows',nk,'dropped',[c['id'] for c in out if c.get('drop')])
if len(sys.argv)>2:
    for c in out:
        if not c.get('drop'): continue
        pm=c['poly']; print('\n',c['id'],round(pm.area),'m2')
        for _,r in stand.iterrows():
            if r.geom_m.intersects(pm):
                a=r.geom_m.intersection(pm).area
                if a>50: print('   stand',r.bin,r['name'],round(r.geom_m.area),'ov',round(a),round(r.start_year),r.year_src,r.height_m)
# ---- Admirals Row houses (NRHP Area 1 inventory dates; positions from the labels on NRHP Map #15, estimated)
t158=open(f'{S}/bb158.html').read()
lab={}
for x in re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>',t158):
    n=x[4]; px=(float(x[0])+float(x[2]))/2; py=(float(x[1])+float(x[3]))/2
    if n in list('BCDEFGHIKL') and 85<px<145 and 488<py<512: lab[n]=(px,py)
AR={'B':(1872,'Residence of the Captain of the Yard (1931 addition)'),'C':(1872,'Residence of the Equipment Officer'),'D':(1873,'Residence of the Ordnance Officer'),
    'E':(1864,'Residence (Naval Constructor / Chief Engineer / Surgeon)'),'F':(1864,'Residence (Naval Constructor / Chief Engineer / Surgeon)'),'G':(1864,'Residence (Naval Constructor / Chief Engineer / Surgeon)'),
    'H':(1881,'Residence of the General Storekeeper'),'I':(1889,'Residence of the Civil Engineer'),'K':(1901,'Residence of the Senior Member, Board of Inspectors'),'L':(1901,'Residence of the Senior Member, Board of Inspectors')}
stack={}
for n,(px,py) in lab.items(): stack.setdefault(round(px/4),[]).append(n)
with open(R+'data/tables/notable_demolished.navy_yard.csv','a',newline='') as f:
    wr=csv.DictWriter(f,fieldnames=fields); na=0
    for n,(yr,desc) in AR.items():
        if n=='B': continue  # a standing 183 m2 footprint (BIN 3421811) sits on the estimated spot: possibly the surviving house or its garage
        if n not in lab: print('no label',n); continue
        px,py=lab[n]; grp=sorted(stack[round(px/4)],key=lambda q:lab[q][1]); i=grp.index(n)
        px+= (i-(len(grp)-1)/2)*5.0; py+=9
        e,nn=utm('158',(px,py)); lon,lat=T.transform(e,nn)
        wr.writerow(dict(id=f'ny_admirals_row_{n}',name=f"Admirals' Row, Quarters {n}: {desc}",start_year=yr,end_year=2016,lat=round(lat,6),lon=round(lon,6),height_m=12,storeys=3,material='brick',outline='',
          shape_note=f"Start year: NRHP inventory (Area 1; {yr}); end: Wikipedia, nine of the ten houses were torn down in 2016 (which one survived is not stated; end 2016 estimated for this one). Position estimated: the label of the house on NRHP Map #15 (1946 plan, registered, rms ~10 m) moved 25 m toward Flushing Avenue and spread along the row when labels are stacked; footprint 12 x 16 m, rotation (Flushing Avenue) and storeys/height estimated.",
          source_url=NRHP,footprint_m='12x16',rotation_deg=85)); na+=1
print('admirals rows',na)
