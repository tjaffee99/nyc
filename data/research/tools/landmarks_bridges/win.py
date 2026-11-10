import duckdb, sys
con=duckdb.connect()
con.execute('install spatial; load spatial; SET geometry_always_xy = true;')
W = {'manhattan':(-73.9905,40.7075,0.008),'hellgate':(-73.9218,40.7826,0.012),'henryhudson':(-73.9222,40.8777,0.004),
     'kosciuszko':(-73.9291,40.7277,0.006),'broadway':(-73.9112,40.8737,0.003),'highbridge':(-73.9303,40.8423,0.004)}
for k,(x,y,d) in W.items():
    print('==',k)
    for f in ['freeways','roads_region','rail','roads_local']:
        p=f'data/raw/overture/2026-10-21.0/{f}.parquet'
        fl = 'rail_flags' if f=='rail' else 'road_flags'
        r=con.execute(f"""select name, class, count(*), round(sum(st_length_spheroid(geometry))) as len
           from '{p}'
           where st_intersects(geometry, st_makeenvelope({x-d},{y-d*0.76},{x+d},{y+d*0.76}))
             and len(list_filter({fl}, lambda x: list_contains(x."values", 'is_bridge')))>0
           group by 1,2 order by 4 desc limit 12""").fetchall()
        for t in r: print('  ',f,t)
