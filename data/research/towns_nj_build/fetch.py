import sys,os,re,time,urllib.parse,urllib.request,glob
D='/home/user/nyc/data/interim/towns_nj_raw/'
def fn(t): return D+'wp_'+re.sub(r'[^A-Za-z0-9\n]','_',t)+'.txt'
def get(t,depth=0):
    f=fn(t)
    if os.path.exists(f) and os.path.getsize(f)>0 and not open(f,errors='ignore').read(200).startswith('<!DOCTYPE'):
        txt=open(f,errors='ignore').read()
    else:
        u='https://en.wikipedia.org/w/index.php?title='+urllib.parse.quote(urllib.parse.unquote(t))+'&action=raw'
        try: txt=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'NYCThroughTime-research/0.1'}),timeout=60).read().decode('utf8','ignore')
        except Exception as e: print('FAIL',t,e); time.sleep(4.5); return
        open(f,'w').write(txt); time.sleep(4.5)
    m=re.match(r'\s*#redirect\s*\[\[([^\]#|]+)',txt,re.I)
    print('ok',t,len(txt),'->'+m.group(1) if m else '')
    if m and depth<2: get(m.group(1).replace(' ','_'),depth+1)
for t in open(sys.argv[1]).read().split('\n'):
    if t.strip(): get(t.strip())
