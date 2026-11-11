import csv,duckdb,json
rows=list(csv.DictReader(open('/home/user/nyc/data/interim/reports/holes.csv')))
nj={'Newark','Woodbridge township','Jersey City','Kearny','Elizabeth','Paterson','Secaucus','North Bergen township','Carteret','Bayonne','East Rutherford','Sayreville','Wayne township','Linden','Harrison','East Orange','Ridgefield','Teterboro','Wood-Ridge','Paramus','Totowa','Clifton','Bloomfield township','Fair Lawn','Belleville township','Hackensack','Elmwood Park','Edgewater','Englewood','Fort Lee','Passaic','Lyndhurst','Hillside','Union','Rahway','Irvington','Orange','West Orange','Bergenfield','Garfield','Lodi','Little Ferry','Moonachie','Carlstadt','South Hackensack','Weehawken','Union City','West New York','Hoboken','Elizabeth city','Roselle','Hawthorne','Haledon','Prospect Park'}
cl=[]
for r in rows:
    if r['place'] not in nj: continue
    x,y,ha,yr=float(r['lon']),float(r['lat']),float(r['ha']),int(r['year'])
    for c in cl:
        if abs(c['x']-x)<0.006 and abs(c['y']-y)<0.005:
            c['yrs'][yr]=c['yrs'].get(yr,0)+ha;break
    else: cl.append(dict(x=x,y=y,yrs={yr:ha},p=r['place']))
cl.sort(key=lambda c:-max(c['yrs'].values()))
cl=cl[:36]
con=duckdb.connect();con.execute('install spatial;load spatial')
O='/home/user/nyc/data/raw/overture/2026-10-21.0/'
out=[]
for i,c in enumerate(cl):
    q=f"ST_Point({c['x']},{c['y']})"
    lu=con.execute(f"select subtype,class,names.primary from '{O}base_land_use.parquet' where ST_DWithin(geometry,{q},0.0007) limit 6").fetchall() if False else None
    try:
        lu=con.execute(f"select subtype,class,ST_Distance(geometry,{q})*100000 from '{O}base_land_use.parquet' where ST_Intersects(geometry,ST_Buffer({q},0.0012)) order by 3 limit 5").fetchall()
    except Exception as e: lu=str(e)[:80]
    rd=con.execute(f"select name,class,round(ST_Distance(geometry,{q})*100000) d from '{O}roads_local.parquet' where ST_Intersects(geometry,ST_Buffer({q},0.0015)) and name is not null order by d limit 4").fetchall()
    print(i,c['p'],round(c['x'],4),round(c['y'],4),{k:round(v) for k,v in c['yrs'].items()},lu,[r[0] for r in rd])
