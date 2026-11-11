import urllib.request,urllib.parse,json,sys
base='https://services3.arcgis.com/3FL1kr7L4LvwA2Kb/arcgis/rest/services/CT_Public_Above_Ground_Resources/FeatureServer/1/query'
where=sys.argv[1]
p={'where':where,'outFields':'NAME,STNUM,ST_NAME,ConstructD,Type,NR','returnGeometry':'true','outSR':'4326','f':'json','resultRecordCount':'60'}
d=json.load(urllib.request.urlopen(urllib.request.Request(base+'?'+urllib.parse.urlencode(p),headers={'User-Agent':'NYCThroughTime-research/0.1'}),timeout=60))
for f in d.get('features',[]):
    a=f['attributes'];g=f.get('geometry') or {}
    print(a['NAME'],'|',a['STNUM'],a['ST_NAME'],'|',a['ConstructD'],'|',round(g.get('x',0),5),round(g.get('y',0),5))
