import sys,urllib.request,json,xml.etree.ElementTree as ET,os,time
# usage: osm.py tag w s e n  -> cached xml; prints named building ways with centre
tag,w,s,e,n=sys.argv[1],*map(float,sys.argv[2:6])
fn=f'data/interim/princeton_yale_round2_raw/osm_{tag}.xml'
if not os.path.exists(fn):
    req=urllib.request.Request(f'https://api.openstreetmap.org/api/0.6/map?bbox={w},{s},{e},{n}',headers={'User-Agent':'NYCThroughTime-research/0.1'})
    open(fn,'wb').write(urllib.request.urlopen(req,timeout=60).read())
r=ET.parse(fn).getroot()
nodes={x.get('id'):(float(x.get('lon')),float(x.get('lat'))) for x in r.findall('node')}
for wy in r.findall('way'):
    t={x.get('k'):x.get('v') for x in wy.findall('tag')}
    if 'building' not in t: continue
    pts=[nodes[nd.get('ref')] for nd in wy.findall('nd') if nd.get('ref') in nodes]
    cx=sum(p[0] for p in pts)/len(pts); cy=sum(p[1] for p in pts)/len(pts)
    keep={k:v for k,v in t.items() if k in('name','start_date','height','building:levels','wikidata','operator','building','addr:housename')}
    if len(keep)>1 or 'name' in keep: print(round(cx,5),round(cy,5),keep)
