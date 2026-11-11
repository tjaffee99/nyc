"""rows.py <town: trenton|nb> spec.txt  -> matches each spec line to a footprint, writes/updates the CSV rows for that town
spec line: slug|name|lon|lat|year|url|note   (lon,lat = any point on/near the building; or fid=<id> in place of lon|lat as 'id:<footprint id>')"""
import sys,csv,duckdb,os
from shapely import wkb
from shapely.geometry import Point
town,spec=sys.argv[1:3]
par={'trenton':'nj_mercer','nb':'nj_middlesex'}[town]
OUT='/home/user/nyc/data/tables/known_building_dates.trenton_nb.csv'
con=duckdb.connect(); con.execute("SET memory_limit='1500MB'")
lines=[l.rstrip('\n').split('|') for l in open(spec) if l.strip() and not l.startswith('#')]
existing={}
if os.path.exists(OUT):
    for r in csv.DictReader(open(OUT)): existing[r['id']]=r
used={}
for r in existing.values(): used[(r['id'])]=1
new=0
for p in lines:
    slug,name,lon,lat,year,url,note=p[:7]
    sid=f'{"tre" if town=="trenton" else "nb"}_{slug}'
    if lon.startswith('id:'):
        row=con.execute(f"select id,name,area_m2,height_m,geometry from 'data/interim/counties/{par}.parquet' where id like ?",[lon[3:]+'%']).fetchall()
        g=wkb.loads(bytes(row[0][4])); d=0
    else:
        lon,lat=float(lon),float(lat); e=0.0004
        rows=con.execute(f"select id,name,area_m2,height_m,geometry from 'data/interim/counties/{par}.parquet' where lon between ? and ? and lat between ? and ?",[lon-e,lon+e,lat-e,lat+e]).fetchall()
        pt=Point(lon,lat); best=None
        for r in rows:
            g=wkb.loads(bytes(r[4])); 
            if g.contains(pt): c=(0,-r[2],r)  # containing, bigger first
            else:
                dd=g.distance(pt)*111000
                c=(1,dd,r) if dd<25 else None
            if c and (best is None or c[:2]<best[:2]): best=c
        if not best: print('NOMATCH',slug,name); continue
        row=[best[2]]; g=wkb.loads(bytes(best[2][4])); d=best[1] if best[0] else 0
    r=row[0]; rp=g.representative_point()
    assert g.contains(rp)
    rec={'id':sid,'name':name,'lat':f'{rp.y:.6f}','lon':f'{rp.x:.6f}','bin':'','start_year':year,'end_year':'9999','source_url':url,'note':note}
    flag='' if (best is None or best[0]==0) else f' (nearest {best[1]:.0f}m)'
    print(f'{sid:34s} {name[:30]:30s} -> {str(r[1])[:34]:34s} {r[2]:6.0f}m2 h{r[3] and round(r[3])} {year}{flag}')
    if sid in existing: existing[sid]=rec
    else: existing[sid]=rec; new+=1
os.makedirs(os.path.dirname(OUT),exist_ok=True)
w=csv.DictWriter(open(OUT,'w',newline=''),fieldnames=['id','name','lat','lon','bin','start_year','end_year','source_url','note'])
w.writeheader()
for r in existing.values(): w.writerow(r)
print('rows now',len(existing),'new',new)
