import csv,duckdb,collections
from shapely import wkb
from shapely.geometry import Point
con=duckdb.connect()
def fp(par,lon,lat):
    e=0.0003
    rows=con.execute(f"select id,name,area_m2,geometry from 'data/interim/counties/{par}.parquet' where lon between ? and ? and lat between ? and ?",[lon-e,lon+e,lat-e,lat+e]).fetchall()
    pt=Point(lon,lat); return [r for r in rows if wkb.loads(bytes(r[3])).contains(pt)]
mine=list(csv.DictReader(open('data/tables/known_building_dates.trenton_nb.csv')))
other=list(csv.DictReader(open('data/tables/known_building_dates.nj_outer.csv')))
cnt=collections.Counter(); bad=0; hit=collections.defaultdict(list)
for r in mine:
    par='nj_mercer' if r['id'].startswith('tre_') else 'nj_middlesex'
    f=fp(par,float(r['lon']),float(r['lat']))
    cnt[r['id'][:3]]+=1
    if not f: bad+=1; print('NOT INSIDE',r['id'])
    for x in f: hit[(par,x[0])].append(r['id'])
dup={k:v for k,v in hit.items() if len(v)>1}
print(dict(cnt),'point-in-polygon failures',bad,'footprints hit by 2+ rows',dup)
oh=set()
for r in other:
    for par in('nj_mercer','nj_middlesex'):
        for x in fp(par,float(r['lon']),float(r['lat'])): oh.add((par,x[0]))
print('overlap with nj_outer footprints:',[v for k,v in hit.items() if k in oh])
ids=[r['id'] for r in mine]; print('unique ids',len(ids)==len(set(ids)))
bys=collections.Counter(('exact' if r['note'].startswith('exact:') else 'estimate' if 'estimate' in r['note'] else 'OTHER') for r in mine); print(bys)
