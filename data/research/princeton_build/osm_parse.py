import glob,json
import xml.etree.ElementTree as ET
out={}
for f in glob.glob('osm_*.xml'):
    r=ET.parse(f).getroot()
    nodes={n.get('id'):(float(n.get('lon')),float(n.get('lat'))) for n in r.findall('node')}
    for w in r.findall('way'):
        t={x.get('k'):x.get('v') for x in w.findall('tag')}
        if 'building' not in t and 'tourism' not in t and 'amenity' not in t: continue
        pts=[nodes[n.get('ref')] for n in w.findall('nd') if n.get('ref') in nodes]
        if len(pts)<4: continue
        out['w'+w.get('id')]={'t':t,'pts':pts}
json.dump(out,open('osm_buildings.json','w'))
print(len(out))
d=[v for v in out.values() if any(k in v['t'] for k in ('start_date','wikidata','wikipedia','construction_date','check_date:start_date'))]
print(len(d))
for v in d: print(v['t'].get('name'),v['t'].get('start_date'),v['t'].get('wikidata'))
