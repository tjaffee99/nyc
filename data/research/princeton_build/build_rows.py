"""Build data/tables/known_building_dates.princeton.csv from specs. Run: .venv/bin/python data/research/princeton_build/build_rows.py"""
import csv,re,sys
sys.path.insert(0,'data/research/princeton_build')
from near import load
from shapely.geometry import Point
H='https://en.wikipedia.org/wiki/Princeton_Historic_District_(Princeton,_New_Jersey)'
W=lambda t:'https://en.wikipedia.org/wiki/'+t
WD=lambda q:'https://www.wikidata.org/wiki/'+q
exec(open('data/research/princeton_build/specs.py').read())   # defines SPEC list of (prefix,name,year,url,note)
rows,geoms,tree=load()
byp={}
for i,r in enumerate(rows): byp.setdefault(r[0][:8],[]).append(i)
out=[];seen=set();ok=0;skipped=[]
existing={r['name'] for r in csv.DictReader(open('data/tables/known_building_dates.nj_outer.csv')) if 'princeton' in r['id']}
for pre,name,year,url,note in SPEC:
    ids=byp.get(pre)
    if not ids or len(ids)!=1: skipped.append((pre,name,'no/ambiguous footprint')); continue
    i=ids[0]; g=geoms[i]; p=g.representative_point()
    if not g.contains(p): skipped.append((pre,name,'pip fail')); continue
    ok+=1
    rid='princeton_'+re.sub(r'[^a-z0-9]+','_',name.lower()).strip('_')+'_'+pre[:4]
    if rid in seen: skipped.append((pre,name,'dup id')); continue
    seen.add(rid)
    out.append([rid,name,f'{p.y:.6f}',f'{p.x:.6f}','',year,9999,url,note])
with open('data/tables/known_building_dates.princeton.csv','w',newline='') as f:
    w=csv.writer(f);w.writerow('id,name,lat,lon,bin,start_year,end_year,source_url,note'.split(','));w.writerows(out)
# independent pip re-check from the written file
chk=0
for r in out:
    pt=Point(float(r[3]),float(r[2]))
    if any(geoms[j].contains(pt) for j in tree.query(pt)): chk+=1
print('rows',len(out),'pip',chk,'skipped',skipped)
