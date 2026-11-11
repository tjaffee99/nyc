"""Builds data/tables/known_building_dates.ct_towns.csv (Stamford + Bridgeport).
MANUAL rows: (city, footprint id prefix, name, start_year, url, note) -- every year read on an opened page.
CRIS rows: ConnCRIS points (SHPO feature service, queried this session) inside named or >=700 m2 footprints
whose assessor year is missing or a heap. A manual row wins. Point = representative_point, PIP-checked."""
import csv, json, re, sys, duckdb
from shapely import wkb, STRtree
from shapely.geometry import Point
W='https://en.wikipedia.org/wiki/'
CRISURL='https://www.arcgis.com/home/item.html?id=ad26b781d4dd467bbe28e9b8f8d3d910'
F={'Stamford':'ct_western_connecticut','Bridgeport':'ct_greater_bridgeport'}
M=[
# ---------------- Stamford
('Stamford','4781c690','One Landmark Square',1973,W+'One_Landmark_Square','exact: infobox "completion_date = 1973" (construction began 1970; 22 floors, 295 ft)'),
('Stamford','3021f176','Park Tower Stamford',2009,W+'Park_Tower_Stamford','exact: "The building finally opened in September 2009"; 350 ft, 34 floors'),
('Stamford','eecc1576','Stamford Town Center',1982,W+'Stamford_Town_Center','exact: infobox "opened = June 17, 1982"'),
('Stamford','74f16290','First Presbyterian Church (Fish Church)',1958,W+'Downtown_Stamford','exact: Downtown Stamford page: "designed by Wallace K. Harrison ... opened in 1958"; Fish_Church infobox built = 1958'),
('Stamford','aca65a09','Old Town Hall',1907,W+'Downtown_Stamford','exact: "built from 1905 to 1907 ... opened for business on March 20, 1907" (infobox of Old_Town_Hall says built 1905); footprint matched by Wikipedia coordinates (4 m)'),
('Stamford','f053c0e0','Rich Forum',1992,W+'Stamford_Center_for_the_Arts','exact: infobox "opened = 1927 (Palace) / 1992 (Rich)"; footprint matched by the article coordinates (0 m); Palace Theatre itself not identified'),
('Stamford','991737d5','Basilica of St. John the Evangelist',1868,W+'Basilica_of_Saint_John_the_Evangelist','exact: "the current church was built in 1868"; footprint named Saint Johns Catholic Church; assessor year 2019 is wrong'),
('Stamford','ebe30f21','St. John\'s Episcopal Church',1891,W+'St._John%27s_Protestant_Episcopal_Church_(Stamford,_Connecticut)','estimate: church "built in 1891" (William Potter), parish house 1869-72 (Upjohn) on the same footprint; matched by coordinates (1 m)'),
('Stamford','98bcd14b','St. Vladimir\'s Cathedral',1957,W+'St._Vladimir%27s_Cathedral_(Stamford,_Connecticut)','exact: "the simple brick Romanesque Revival-inspired church building was completed in 1957"'),
('Stamford','c323d872','Universalist (Unitarian-Universalist) Church',1870,W+'Unitarian_Universalist_Church_(Stamford,_Connecticut)','estimate: infobox built = 1870 (Gage Inslee); footprint is the only church-sized one within 17 m of the article coordinates (assessor says 1810)'),
('Stamford','ccf36a3a','Stamford Transportation Center',1987,W+'Stamford_Transportation_Center','exact: infobox "rebuilt = 1861, 1890s, 1987, 2004"; Goldberger reviewed the new station in 1987'),
('Stamford','fd6ce833','Stamford Transportation Center (concourse)',1987,W+'Stamford_Transportation_Center','exact: as the station, same 1987 building'),
('Stamford','ce677bd7','Stamford Hospital (New Stamford Hospital)',2016,W+'Stamford_Hospital','exact: "11-story glass structure ... The expansion was completed in late 2016"'),
('Stamford','404e09f9','Summer House',2016,W+'Downtown_Stamford','exact: "Completed in 2016, the 250-foot, 22-story residential building" (OpenStreetMap places Flinders Lane, its ground-floor restaurant, 22 m from the 85 m footprint); assessor placeholder 1900'),
('Stamford','0eb7f9bf','Atlantic Station',2017,W+'Downtown_Stamford','exact: "Completed in 2017 by RXR Realty, the 26-story ... 315 feet"'),
('Bridgeport','3a230949','Fairfield County Courthouse',1888,W+'Fairfield_County_Courthouse_(Bridgeport,_Connecticut)','exact: "Richardsonian Romanesque brick building built in 1888" (172 Golden Hill Street)'),
('Bridgeport','aa06abd4','McLevy Hall (old City Hall)',1854,W+'McLevy_Hall','exact: "built in 1854 to house both the City Hall and the Fairfield County Courthouse"'),
('Bridgeport','639ab9c5','Palace and Majestic Theaters',1922,W+'Palace_and_Majestic_Theaters','exact: "Built in 1921-22 by Sylvester Z. Poli" (Thomas W. Lamb), 1315-1357 Main Street; assessor placeholder 1900'),
('Bridgeport','b271ff84','Total Mortgage Arena',2001,W+'Total_Mortgage_Arena','exact: infobox "opened = 2001-10-10"; 10,000 seats'),
('Bridgeport','f2721da2','Ballpark at Harbor Yard (Hartford HealthCare Amphitheater)',1998,W+'The_Ballpark_at_Harbor_Yard','exact: "opened on May 21, 1998"; converted to the amphitheater, opened July 28, 2021 (the footprint is the stand\'s)'),
('Bridgeport','6f9ff273','Bridgeport Center (People\'s Bank Building)',1989,W+'Bridgeport_Center','exact: infobox "completion_date = 1989" (construction began 1984); Richard Meier; 18 floors, red wing 248 ft'),
('Bridgeport','62ddbd5c','Bridgeport Center (low wings)',1989,W+'Bridgeport_Center','estimate: same complex, completed 1989; the footprint is the low part'),
('Bridgeport','33594ff4','Bridgeport Post Office',1934,W+'United_States_Post_Office%E2%80%93Bridgeport_Main','exact: infobox built = 1934 (Simon and Walker)'),
('Bridgeport','e4b20cbf','Klein Memorial Auditorium',1940,W+'Klein_Memorial_Auditorium','exact: infobox "opened = 1940"; assessor value 1940 is the real year here'),
('Bridgeport','0e6cf439','Bridgeport railroad station',1975,W+'Bridgeport_station_(Connecticut)','exact: "The current station was built under ConnDOT and Penn Central in 1975" (rebuilt June 1973 - October 27, 1975)'),
('Bridgeport','6387ad39','Warren G. Harding High School',1925,W+'Warren_Harding_High_School','exact: "the school opened on September 9, 1925" (cornerstone May 10, 1924)'),
('Bridgeport','a047a6fb','Bridgeport Correctional Center',1958,W+'Bridgeport_Correctional_Center','exact: "built in 1958 and received its first inmates the same year"; footprint at the article coordinates (0 m)'),
('Bridgeport','449d69c0','St. Augustine Cathedral',1868,W+'St._Augustine_Cathedral_(Bridgeport,_Connecticut)','exact: dedicated March 17, 1868 (completed 1868, Patrick C. Keely); footprint named Saint Augustine Cathedral (assessor 1964)'),
('Bridgeport','81b3c249','Sterling Block - Bishop Arcade',1841,W+'Sterling_Block-Bishop_Arcade','exact: "Built in 1841 and expanded several times"; northern part 1841, hotel addition 1850; matched to the ConnCRIS point (1841) on 993-1005 Main St'),
]
def parse_year(s):
    if not s: return None
    m=re.match(r'\s*(1[5-9]\d\d|20[0-2]\d)',s)
    return int(m.group(1)) if m else None
def run():
    con=duckdb.connect(); con.execute("SET memory_limit='1500MB'")
    rows=[]; stats={}
    for city in F:
        data=con.execute(f"select id,name,area_m2,year_raw,heap,geometry from read_parquet('/home/user/nyc/data/interim/counties/{F[city]}.parquet') where muni='{city}'").fetchall()
        byp={}
        for r in data: byp.setdefault(r[0][:8],[]).append(r)
        geo={}
        done=set()
        def add(rid,name,y,url,note,part):
            p=wkb.loads(bytes(rid[5])); 
            if p.geom_type=='MultiPolygon': p=max(p.geoms,key=lambda z:z.area)
            rp=p.representative_point()
            ok=p.contains(rp)
            nm=re.sub(r'[^a-z0-9]+','_',(name or 'x').lower()).strip('_')[:28]
            rows.append(dict(id=f'ct_towns_{city[:3].lower()}_{nm}_{rid[0][:6]}',name=name,lat=f'{rp.y:.6f}',lon=f'{rp.x:.6f}',bin='',start_year=y,end_year=9999,source_url=url,note=note,_city=city,_ok=ok,_part=part))
            done.add(rid[0])
        for c,pre,name,y,url,note in M:
            if c!=city: continue
            c_=byp.get(pre,[])
            if len(c_)!=1: print('!! prefix',pre,len(c_)); continue
            add(c_[0],name,y,url,note,'manual')
        pts=json.load(open(f'/home/user/nyc/data/interim/towns_ct_raw/cris_{city.lower()}.json'))
        P=[(Point(x['geometry']['x'],x['geometry']['y']),x['attributes']) for x in pts if x.get('geometry')]
        tree=STRtree([p for p,_ in P])
        for r in data:
            id,n,ar,yr,hp,g=r
            if id in done or not (n or ar>=700): continue
            if not (yr is None or hp): continue
            p=wkb.loads(bytes(g)); 
            idx=tree.query(p,predicate='contains')
            if len(idx)==0: continue
            att=[P[i][1] for i in idx]
            ys=[(parse_year(a['ConstructD']),a) for a in att if 'DEMOLISHED' not in (a['NAME'] or '').upper()]; ys=[(y,a) for y,a in ys if y]
            if not ys: continue
            ys.sort(key=lambda t:t[0]); y,a=ys[0]
            circa=any('CIRCA' in (b['ConstructD'] or '') for _,b in ys[:1])
            nm=n or (a['NAME'] or f"{a['STNUM'] or ''} {a['ST_NAME'] or ''}".strip()).title()
            others=len(ys)-1
            note=("estimate: " if (circa or others and ys[-1][0]-y>8) else "exact: ")+f"ConnCRIS (SHPO) ConstructD \"{a['ConstructD']}\" for {a['NAME'] or (str(a['STNUM'])+' '+str(a['ST_NAME']))}"+(f"; earliest of {len(ys)} inventory points in the footprint (years {ys[0][0]}-{ys[-1][0]})" if others else "")+"; assessor year missing or a placeholder"
            if id[:8]=='477614d9': y=1925; note='exact: ConnCRIS "CHURCH OF THE HOLY NAME OF JESUS" 325 Washington Blvd ConstructD 1925 (the convent point, 1895, is another building); assessor year missing or a placeholder'
            add(r,nm,y,CRISURL,note,'cris')
    return rows
if __name__=='__main__':
    rows=run()
    cols=['id','name','lat','lon','bin','start_year','end_year','source_url','note']
    with open('/home/user/nyc/data/tables/known_building_dates.ct_towns.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore'); w.writeheader()
        for r in rows: w.writerow(r)
    for c in F:
        rr=[r for r in rows if r['_city']==c]
        print(c,len(rr),'manual',sum(r['_part']=='manual' for r in rr),'cris',sum(r['_part']=='cris' for r in rr),'PIP ok',sum(r['_ok'] for r in rr))
    print('dup ids',len(rows)-len({r['id'] for r in rows}))
