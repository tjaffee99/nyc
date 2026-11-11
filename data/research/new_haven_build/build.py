import pandas as pd,duckdb,re,csv
from shapely import wkb
W='https://en.wikipedia.org/wiki/'
CC='https://services3.arcgis.com/3FL1kr7L4LvwA2Kb/arcgis/rest/services/CT_Public_Above_Ground_Resources/FeatureServer/1/query?where=UNIQUE_ID%3D{}&outFields=NAME,STNUM,ST_NAME,ConstructD,Periods,DesigStatu&f=json'
# (footprint name, area_min, area_max, year, url, note)
A=[
('Davenport College',0,1e9,1933,W+'Davenport_College','exact: "Its buildings were completed in 1933"'),
('Pierson College',0,1e9,1933,W+'Pierson_College','exact: "Opened in 1933" (one of the eight original colleges by James Gamble Rogers)'),
('Berkeley College',0,1e9,1934,W+'Berkeley_College,_Yale_University','exact: "opened in 1934" (built on the site of the Berkeley Oval, cleared 1933)'),
('Berkeley College (North)',0,1e9,1934,W+'Berkeley_College,_Yale_University','exact: "opened in 1934"'),
('Sloane Physics Laboratory',0,1e9,1912,W+'Science_Hill_(Yale_University)','exact: Science Hill table, Sloane Physics Laboratory "1912" (Charles C. Haight), the first science building on the Sachem\'s Wood property'),
('Osborn Memorial Laboratories',0,1e9,1913,W+'Osborn_Memorial_Laboratories','exact: "The Osborn Memorial Laboratories ... were built in 1913"; Science Hill table "1913"'),
('Sage Hall',0,1e9,1924,W+'Science_Hill_(Yale_University)','exact: "The school first came to Science Hill in 1924 with the completion of Sage Hall"; table "1924"'),
('Kline Tower',0,1e9,1966,W+'Kline_Biology_Tower','exact: infobox construction 1962, completion 1966; "the tallest building in the city from 1966 to 1969" (the Science Hill table says 1965)'),
('Hotel Marcel',0,1e9,1970,'https://www.wikidata.org/wiki/Q63615028','exact: Wikidata inception 1970 and OpenStreetMap start_date 1970 (Marcel Breuer building; assessor year 2004 is a conversion)'),
('Connecticut Financial Center',0,1e9,1990,W+'Connecticut_Financial_Center','exact: "completed in 1990" (assessor 1987 is the start of construction)'),
('Bass Center',0,1e9,1993,W+'Science_Hill_(Yale_University)','exact: Science Hill table, Bass Center for Molecular & Structural Biology "1993"'),
('Class of 1954 Environmental Science Center',0,1e9,2005,W+'Science_Hill_(Yale_University)','exact: Science Hill table, "2005"'),
('Class of 1954 Chemistry Research Building',0,1e9,2005,W+'Science_Hill_(Yale_University)','exact: Science Hill table, "2005"'),
('Kroon Hall',0,1e9,2008,W+'Science_Hill_(Yale_University)','exact: "In 2008, the school opened Kroon Hall adjacent to Sage"; table "2008"'),
('Sterling Hall',7000,8000,1923,W+'Science_Hill_(Yale_University)','exact: Science Hill table, Sterling Chemistry Laboratory "1923" (William Adams Delano), 225 Prospect St; footprint named Sterling Hall at the same spot (name matched by place)'),
('Wright Laboratory',2000,3000,1966,W+'Science_Hill_(Yale_University)','estimate: Wright Nuclear Structure Laboratory built 1966 (Douglas Orr); the lab was rebuilt and reopened in 2017 so the standing outline may be later'),
('Electron Accelerator Laboratory',0,1e9,1953,W+'Science_Hill_(Yale_University)','estimate: Science Hill table lists "Accelerator Laboratories" 1953 (Douglas Orr); footprint name matched loosely'),
]
c=duckdb.connect();c.execute("SET memory_limit='1500MB'")
df=c.execute("select id,name,area_m2,year_raw,heap,geometry from 'interim/counties/ct_south_central_connecticut.parquet' where muni='New Haven'").fetchdf()
df['g']=[wkb.loads(bytes(b)) for b in df.geometry]
used=set(pd.read_csv('research/new_haven_build/ct_used_ids.csv').iloc[:,0])
rows={}
def add(i,year,url,note,idn):
    r=df.loc[i]
    if r.id in used:return
    p=r.g.representative_point()
    if any(v['id']=='new_haven_'+idn for v in rows.values()):idn=f'{idn}_{i}'
    rows[r.id]=dict(id='new_haven_'+idn,name=r['name'] or '',lat=round(p.y,6),lon=round(p.x,6),bin='',start_year=int(year),end_year=9999,source_url=url,note=note,_area=round(r.area_m2),_fid=r.id,_g=r.g)
# A
for nm,lo,hi,y,u,n in A:
    sel=df[(df.name==nm)&(df.area_m2>=lo)&(df.area_m2<=hi)]
    if not len(sel):print('NO FOOTPRINT',nm)
    for i in sel.index:add(i,y,u,n,re.sub(r'[^a-z0-9]+','_',nm.lower()).strip('_')+('' if len(sel)==1 else f'_{i}'))
nA=len(rows)
# B ConnCRIS
m=pd.read_pickle('research/new_haven_build/join.pkl')
m['yr']=pd.to_numeric(m.cd.str.extract(r'^(\d{4})')[0]);m['circa']=m.cd.fillna('').str.contains('CIRCA')
m=m[m.yr.notna()]
m['hn']=m.cname.fillna('').str.strip()!=''
g=m.groupby('bi').agg(yrs=('yr',lambda s:sorted(set(s))),cid=('cid','first'),cd=('cd','first'),circa=('circa','min'),n=('yr','size'),hn=('hn','max'),cname=('cname',lambda s:'; '.join(str(x) for x in s if isinstance(x,str))[:60])).reset_index()
g['spread']=g.yrs.map(lambda y:max(y)-min(y))
REJ_NAMES={'Christ Church','Kroon Hall','Class of 1954 Environmental Science Center','Prospect/Sachem Garage','Founders Hall','Celentano Building','Administration Building','Silliman College','Loria Center','Clinic Building','Howe Street Garage','The Winston','New Haven Colonial Historical Society Building','Slifka Center for Jewish Life','First Unitarian Universalist Church','149 York Street','Davenport College'}
REJ_CN=('DELAURO PARK','NEW HAVEN CLOCK COMPANY')
nB=0
for _,r in g.iterrows():
    f=df.loc[r.bi]
    if f.id in rows or f.id in used:continue
    heap_or_missing=bool(f.heap) or pd.isna(f.year_raw)
    if not heap_or_missing:continue
    if r.spread>3 and not(r.spread<=5):continue
    if f['name'] in REJ_NAMES or any(x in r.cname for x in REJ_CN):continue
    big=f.area_m2>1500 or bool(f['name'])
    if not (big or r.hn):continue   # tier 2 only for individually named resources
    yr=int(min(r.yrs));rd=yr%10==0
    q=f'"{r.cd}"'
    if r.circa or rd:
        note=f'estimate: ConnCRIS (CT State Historic Preservation Office inventory) ConstructD {q}'+(' (round year, may be a placeholder)' if rd and not r.circa else ' (circa)')+(f'; resource "{r.cname[:40]}"' if r.cname and r.cname!='' else '')
    else:
        note=f'exact: ConnCRIS (CT State Historic Preservation Office inventory) ConstructD {q}'+(f'; resource "{r.cname[:40]}"' if r.cname else '')
    add(r.bi,yr,CC.format(int(r.cid)),note,f'cc{int(r.cid)}')
    nB+=1
print('A',nA,'B',nB,'total',len(rows))
out=pd.DataFrame(rows.values())
# point-in-polygon test
from shapely.geometry import Point
ok=[g.contains(Point(x,y)) for g,x,y in zip(out._g,out.lon,out.lat)]
print('pip pass',sum(ok),'of',len(out))
out=out[ok]
out.drop(columns=['_area','_fid','_g']).drop(columns=[]).to_csv('tables/known_building_dates.new_haven.csv',index=False,quoting=csv.QUOTE_MINIMAL)
out[['id','name','_area','start_year','note']].to_pickle('research/new_haven_build/out.pkl')
print(out.start_year.describe(), out.note.str.startswith('exact').sum())
