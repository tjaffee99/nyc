import sys, time, urllib.request, urllib.parse, os
out='data/interim/holes_boroughs_raw/wp'; os.makedirs(out,exist_ok=True)
for t in [l.strip() for l in open(sys.argv[1]) if l.strip()]:
    fn=f"{out}/{t.replace('/','_')}.wiki"
    if os.path.exists(fn) and os.path.getsize(fn)>200: continue
    u='https://en.wikipedia.org/w/index.php?title='+urllib.parse.quote(t)+'&action=raw'
    try:
        r=urllib.request.Request(u,headers={'User-Agent':'NYCThroughTime-research/0.1'})
        d=urllib.request.urlopen(r,timeout=30).read()
        open(fn,'wb').write(d); print(t,len(d),flush=True)
    except Exception as e: print(t,'ERR',e,flush=True)
    time.sleep(4)
