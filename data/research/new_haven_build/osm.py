import requests,time,json,os,sys
import xml.etree.ElementTree as ET
H={'User-Agent':'NYCThroughTime-research/0.1'}
os.makedirs('osm',exist_ok=True)
W,S,E,N=-72.9500,41.2800,-72.8800,41.3400   # core
step=0.015
out=[]
x=W
while x<E:
    y=S
    while y<N:
        fn=f'osm/{x:.4f}_{y:.4f}.xml'
        if not os.path.exists(fn):
            for k in range(5):
                r=requests.get('https://api.openstreetmap.org/api/0.6/map',params={'bbox':f'{x:.5f},{y:.5f},{x+step:.5f},{y+step:.5f}'},headers=H,timeout=120)
                if r.status_code==200:break
                print(fn,r.status_code);time.sleep(10*(k+1))
            else: y+=step;continue
            open(fn,'wb').write(r.content);time.sleep(1)
        y+=step
    x+=step
