import xml.etree.ElementTree as ET,glob
seen={}
for f in glob.glob('osm_*.xml'):
    for w in ET.parse(f).getroot().iter('way'):
        t={x.get('k'):x.get('v') for x in w.findall('tag')}
        if 'building' in t and (t.get('name') or t.get('height') or t.get('start_date')):
            seen[w.get('id')]=t
for i,t in sorted(seen.items(),key=lambda x:x[1].get('name','')):
    print(i,t.get('name'),'|h',t.get('height'),'|lv',t.get('building:levels'),'|sd',t.get('start_date'),'|',t.get('wikidata'))
