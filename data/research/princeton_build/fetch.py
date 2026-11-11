import sys,os,time,subprocess,urllib.parse
os.makedirs('pages',exist_ok=True)
for l in open(sys.argv[1]):
    t=l.strip()
    if not t: continue
    fn='pages/'+t.replace('/','_')+'.txt'
    if os.path.exists(fn) and os.path.getsize(fn)>200: continue
    for k in range(4):
        r=subprocess.run(['curl','-sS','-m','40','-L','-A','NYCThroughTime-research/0.1','-w','%{http_code}','-o',fn,'https://en.wikipedia.org/w/index.php?action=raw&title='+urllib.parse.quote(t.replace(' ','_'))],capture_output=True,text=True)
        if r.stdout.strip() in ('200','404'): break
        time.sleep(10*(k+1))
    print(r.stdout,t,os.path.getsize(fn),flush=True)
    time.sleep(3)
