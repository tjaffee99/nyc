import sys,urllib.request,json,xml.etree.ElementTree as ET,time,os
# usage: osm.py out.json w s e n [w s e n ...]
out=sys.argv[1]; a=list(map(float,sys.argv[2:]))
res={}
for i in range(0,len(a),4):
    w,s,e,n=a[i:i+4]
    u=f'https://api.openstreetmap.org/api/0.6/map?bbox={w},{s},{e},{n}'
    for t in range(3):
        try:
            x=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'NYCThroughTime-research/0.1'}),timeout=90).read();break
        except Exception as ex: print('err',u,ex); time.sleep(5); x=None
    if not x: continue
    r=ET.fromstring(x)
    nodes={n.get('id'):(float(n.get('lon')),float(n.get('lat'))) for n in r.iter('node')}
    for wy in r.iter('way'):
        tg={t.get('k'):t.get('v') for t in wy.iter('tag')}
        if 'building' not in tg: continue
        if not any(k in tg for k in ('name','start_date','height','wikidata','building:levels')): continue
        pts=[nodes[n.get('ref')] for n in wy.iter('nd') if n.get('ref') in nodes]
        if not pts: continue
        res[wy.get('id')]={'tags':tg,'lon':sum(p[0] for p in pts)/len(pts),'lat':sum(p[1] for p in pts)/len(pts)}
    time.sleep(2)
json.dump(res,open(out,'w'))
for k,v in res.items():
    t=v['tags']; print(k,t.get('name'),'|',t.get('start_date'),t.get('height'),t.get('building:levels'),t.get('wikidata'),'|',round(v['lon'],4),round(v['lat'],4))
