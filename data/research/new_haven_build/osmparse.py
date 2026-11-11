import glob,json
import xml.etree.ElementTree as ET
res={}
for f in glob.glob('osm/*.xml'):
    root=ET.parse(f).getroot()
    nodes={n.get('id'):(float(n.get('lon')),float(n.get('lat'))) for n in root.iter('node')}
    for w in root.iter('way'):
        t={k.get('k'):k.get('v') for k in w.iter('tag')}
        pts=[nodes[n.get('ref')] for n in w.iter('nd') if n.get('ref') in nodes]
        if len(pts)<4 or not('building' in t or 'start_date' in t or 'wikidata' in t):continue
        res[w.get('id')]=dict(t=t,pts=pts)
    # relations (multipolygon) skipped
json.dump(res,open('osm_ways.json','w'))
sd=[v for v in res.values() if 'start_date' in v['t']]
print(len(res),len(sd),sum('wikidata' in v['t'] for v in res.values()))
for v in sd[:40]:print(v['t'].get('name'),v['t']['start_date'])
