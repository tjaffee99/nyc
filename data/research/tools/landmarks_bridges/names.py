import duckdb
con=duckdb.connect()
con.execute('install spatial; load spatial; SET geometry_always_xy = true;')
for f in ['freeways','roads_region','rail','roads_local']:
    p=f'data/raw/overture/2026-10-21.0/{f}.parquet'
    fl = 'rail_flags' if f=='rail' else 'road_flags'
    r=con.execute(f"""select name, class, count(*), round(sum(st_length_spheroid(geometry))) as len,
       sum(case when len(list_filter({fl}, lambda x: list_contains(x."values", 'is_bridge')))>0 then 1 else 0 end) nb
       from '{p}'
       where name ilike '%bridge%' or name ilike '%crossing%' or name ilike '%viaduct%' or name ilike '%hell gate%' group by 1,2 order by 1""").fetchall()
    print('==',f)
    for x in r: print(x)
