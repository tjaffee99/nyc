import duckdb,csv,sys
from shapely import wkb,Point
part=sys.argv[1]  # specs file module
exec(open(f'data/research/princeton_yale_round2_build/specs_{part}.py').read())
con=duckdb.connect(); con.execute("SET memory_limit='1500MB'")
out=[];bad=0
for pid,name,year,url,note in SPECS:
    r=con.execute(f"select id,geometry from '{PARQ}' where {WHERE} and id like '{pid}%'").fetchall()
    if len(r)!=1: print('ID?',pid,len(r)); bad+=1; continue
    g=wkb.loads(bytes(r[0][1])); p=g.representative_point()
    ok=g.contains(Point(p.x,p.y))
    if not ok: bad+=1; print('NOT INSIDE',pid)
    out.append([f'{PREFIX}_{name.lower().replace(" ","_").replace("/","_")}_{pid[:4]}',name,round(p.y,6),round(p.x,6),'',year,9999,url,note])
w=csv.writer(open(f'data/tables/known_building_dates.{PREFIX}.csv','w',newline=''))
w.writerow('id,name,lat,lon,bin,start_year,end_year,source_url,note'.split(','))
w.writerows(out); print(len(out),'rows; failures',bad)
