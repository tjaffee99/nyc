import sys,os,time,urllib.request,urllib.parse
D='/home/user/nyc/data/interim/holes_nj_cities_raw'
def get(t):
    fn=os.path.join(D,'wp_'+t.replace('/','_').replace(' ','_')+'.txt')
    if os.path.exists(fn): return fn
    u='https://en.wikipedia.org/w/index.php?action=raw&title='+urllib.parse.quote(t.replace(' ','_'))
    for i in range(3):
        try:
            r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'NYCThroughTime-research/0.1'}),timeout=30)
            open(fn,'wb').write(r.read());break
        except Exception as e:
            print(t,'ERR',e,flush=True);time.sleep(5)
    else: return None
    time.sleep(4);return fn
if __name__=='__main__':
    for t in sys.argv[1:]: print(t,get(t),flush=True)
