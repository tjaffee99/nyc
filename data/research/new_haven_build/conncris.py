import requests,json
B='https://services3.arcgis.com/3FL1kr7L4LvwA2Kb/arcgis/rest/services/CT_Public_Above_Ground_Resources/FeatureServer/1/query'
H={'User-Agent':'NYCThroughTime-research/0.1'}
rows=[];off=0
while True:
    r=requests.get(B,params={'where':"MUNICIP2='New Haven'",'outFields':'NAME,UNIQUE_ID,STNUM,ST_NAME,MUNICIP2,DesigStatu,ConstructD,Periods,Primary_St,Type,District_Names,NR,Longitude,LATITUDE','outSR':4326,'returnGeometry':'true','resultOffset':off,'resultRecordCount':2000,'orderByFields':'OBJECTID','f':'json'},headers=H,timeout=120).json()
    f=r.get('features',[]);rows+=f;off+=len(f)
    if not f or not r.get('exceededTransferLimit'):break
json.dump(rows,open('conncris_nh.json','w'))
import collections
print(len(rows))
c=collections.Counter(bool((x['attributes']['ConstructD'] or '').strip()) for x in rows);print(c)
print(collections.Counter(x['attributes']['ConstructD'] for x in rows).most_common(25))
for x in rows[:5]:print(x['attributes'],x['geometry'])
