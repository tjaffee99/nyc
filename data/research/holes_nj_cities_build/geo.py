import json,sys,time,urllib.request,urllib.parse
pts=[("newark_cw",-74.1858,40.7341,2500),("jc1980",-74.0459,40.7073,1800),("kearny_we",-74.1084,40.7413,1500),("newark_s",-74.1857,40.7057,1500),("eliz",-74.1713,40.6775,1500),("newark_e",-74.1324,40.716,1500),("kearny_fed",-74.1157,40.7263,1500),("paterson",-74.174,40.9239,1200),("pat2",-74.1549,40.9015,1000),("carteret",-74.2426,40.5649,2000)]
for n,x,y,r in pts:
    u='https://en.wikipedia.org/w/api.php?action=query&list=geosearch&gscoord=%s|%s&gsradius=%d&gslimit=60&format=json'%(y,x,r)
    d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'NYCThroughTime-research/0.1'})))
    print('##',n,x,y)
    for g in d['query']['geosearch']: print(' ',g['title'],round(g['lat'],5),round(g['lon'],5),g['dist'])
    time.sleep(3)
