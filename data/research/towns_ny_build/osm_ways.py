import sys, xml.etree.ElementTree as ET
# usage: osm_ways.py file.xml  -> ways with building tags & (name|start_date|height|levels)
for f in sys.argv[1:]:
    r=ET.parse(f).getroot(); nodes={n.get('id'):(float(n.get('lon')),float(n.get('lat'))) for n in r.findall('node')}
    for w in r.findall('way'):
        t={x.get('k'):x.get('v') for x in w.findall('tag')}
        if 'building' not in t: continue
        if not any(k in t for k in ('name','start_date','height','building:levels','wikidata')): continue
        pts=[nodes[n.get('ref')] for n in w.findall('nd') if n.get('ref') in nodes]
        cx=sum(p[0] for p in pts)/len(pts); cy=sum(p[1] for p in pts)/len(pts)
        print(w.get('id'),round(cx,5),round(cy,5),{k:v for k,v in t.items() if k in('name','start_date','height','building:levels','wikidata','building','year_built','construction_date')})
