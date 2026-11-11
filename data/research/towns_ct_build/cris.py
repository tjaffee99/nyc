import sys, json, urllib.request, urllib.parse, os
# usage: cris.py out.json MUNI   (downloads ConnCRIS points of a municipality, paged)
out,mun=sys.argv[1:3]
U="https://services3.arcgis.com/3FL1kr7L4LvwA2Kb/arcgis/rest/services/CT_Public_Above_Ground_Resources/FeatureServer/1/query"
res=[];off=0
while True:
    p=dict(where=f"MUNICIP2='{mun}'",outFields="NAME,STNUM,ST_NAME,MUNICIP2,DesigStatu,ConstructD",outSR=4326,f="json",resultOffset=off,resultRecordCount=1000,returnGeometry="true")
    r=urllib.request.Request(U+"?"+urllib.parse.urlencode(p),headers={'User-Agent':'NYCThroughTime-research/0.1'})
    d=json.load(urllib.request.urlopen(r,timeout=90))
    f=d.get('features',[]); res+=f; print(len(res),file=sys.stderr)
    if len(f)<1000 and not d.get('exceededTransferLimit'): break
    off+=len(f)
json.dump(res,open(out,'w'))
