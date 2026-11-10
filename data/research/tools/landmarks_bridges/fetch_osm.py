import requests, time, os, sys
OUT='data/raw/landmarks_bridges'
B = {
 'brooklyn':(-74.0030,40.7020,-73.9905,40.7105),
 'manhattan':(-73.9965,40.7015,-73.9855,40.7135),
 'williamsburg':(-73.9820,40.7095,-73.9620,40.7175),
 'gwb':(-73.9700,40.8450,-73.9400,40.8580),
 'queensboro':(-73.9650,40.7500,-73.9380,40.7620),
 'verrazzano':(-74.0620,40.5990,-74.0290,40.6140),
 'hellgate_rfk':(-73.9330,40.7740,-73.9160,40.7870),
 'rfk_north':(-73.9340,40.7950,-73.9150,40.8040),
 'highbridge_washington':(-73.9330,40.8395,-73.9230,40.8490),
 'whitestone':(-73.8340,40.7930,-73.8250,40.8100),
 'throgsneck':(-73.8010,40.7920,-73.7870,40.8110),
 'bayonne':(-74.1480,40.6370,-74.1360,40.6470),
 'goethals':(-74.2060,40.6320,-74.1900,40.6390),
 'outerbridge':(-74.2540,40.5215,-74.2390,40.5290),
 'macombs':(-73.9370,40.8260,-73.9300,40.8300),
 'university':(-73.9175,40.8615,-73.9125,40.8640),
 'broadway_hudson':(-73.9250,40.8720,-73.9090,40.8800),
 'kosciuszko':(-73.9340,40.7240,-73.9240,40.7320),
 'marine':(-73.9030,40.5660,-73.8940,40.5810),
 'roosevelt':(-73.9490,40.7620,-73.9420,40.7660),
 'pulaski':(-73.9550,40.7360,-73.9500,40.7420),
}
S=requests.Session(); S.headers['User-Agent']='NYCThroughTime-research/0.1'
def get(name,bb,depth=0):
    fn=f'{OUT}/osm_{name}.osm'
    if os.path.exists(fn) and os.path.getsize(fn)>1000: return
    r=S.get('https://api.openstreetmap.org/api/0.6/map',params={'bbox':','.join(map(str,bb))},timeout=120)
    print(name,bb,r.status_code,len(r.content),flush=True)
    if r.status_code==200:
        open(fn,'wb').write(r.content)
    elif r.status_code==400 and depth<2:
        x0,y0,x1,y1=bb; xm=(x0+x1)/2
        get(name+'_a',(x0,y0,xm,y1),depth+1); get(name+'_b',(xm,y0,x1,y1),depth+1)
    time.sleep(1.5)
for k,bb in B.items():
    if len(sys.argv)>1 and k not in sys.argv[1:]: continue
    try: get(k,bb)
    except Exception as e: print(k,'ERR',e)
