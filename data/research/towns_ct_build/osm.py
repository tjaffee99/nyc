import sys, urllib.request, xml.etree.ElementTree as ET, json, os, time
# usage: osm.py w s e n out.json  -> named/dated building ways with centroid
w,s,e,n,out=sys.argv[1:6]
if not os.path.exists(out+'.xml'):
    r=urllib.request.Request(f"https://api.openstreetmap.org/api/0.6/map?bbox={w},{s},{e},{n}",headers={'User-Agent':'NYCThroughTime-research/0.1'})
    open(out+'.xml','wb').write(urllib.request.urlopen(r,timeout=90).read())
t=ET.parse(out+'.xml').getroot()
nodes={x.get('id'):(float(x.get('lon')),float(x.get('lat'))) for x in t.findall('node')}
res=[]
for el in t.findall('way')+t.findall('relation'):
    tg={x.get('k'):x.get('v') for x in el.findall('tag')}
    if 'building' not in tg and 'tourism' not in tg and 'amenity' not in tg: continue
    if not any(k in tg for k in ('name','start_date','wikidata','height','building:levels')): continue
    pts=[nodes[nd.get('ref')] for nd in el.findall('nd') if nd.get('ref') in nodes]
    if not pts: continue
    res.append(dict(id=el.get('id'),lon=sum(p[0] for p in pts)/len(pts),lat=sum(p[1] for p in pts)/len(pts),**tg))
json.dump(res,open(out,'w'))
for r in res:
    if 'start_date' in r or 'wikidata' in r or 'height' in r or 'name' in r: print(r['id'],r.get('name'),'|sd',r.get('start_date'),'|h',r.get('height'),'|lv',r.get('building:levels'),'|',r.get('wikidata'),'|',round(r['lon'],5),round(r['lat'],5))
