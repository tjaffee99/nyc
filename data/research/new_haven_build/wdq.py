import json,requests,time
from wm import jget
H={'User-Agent':'NYCThroughTime-research/0.1'}
ways=json.load(open('osm_ways.json'))
q=sorted({v['t']['wikidata'] for v in ways.values() if 'wikidata' in v['t']})
print(len(q))
out={}
for i in range(0,len(q),50):
    J=jget('https://www.wikidata.org/w/api.php',{'action':'wbgetentities','ids':'|'.join(q[i:i+50]),'props':'claims|labels|sitelinks','languages':'en','format':'json'})
    for k,e in J['entities'].items():
        cl=e.get('claims',{})
        def d(p):
            return [c['mainsnak']['datavalue']['value']['time'][1:11] for c in cl.get(p,[]) if 'datavalue' in c['mainsnak']]
        out[k]=dict(label=e.get('labels',{}).get('en',{}).get('value'),inc=d('P571'),op=d('P1619'),sl=e.get('sitelinks',{}).get('enwiki',{}).get('title'))
    time.sleep(1)
json.dump(out,open('wd_osm.json','w'))
for k,v in out.items():
    if v['inc'] or v['op']:print(k,v)
