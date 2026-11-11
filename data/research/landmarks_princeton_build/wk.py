import json,subprocess,sys,time,os
qs=sys.argv[1:]
for q in qs:
    f='wiki/'+q.replace(' ','_')+'.json'
    for t in range(6):
        r=subprocess.run(['curl','-sS','-A','NYCThroughTime-research/0.1','-G','https://en.wikipedia.org/w/api.php','--data-urlencode','action=query','--data-urlencode','generator=search','--data-urlencode','gsrsearch='+q,'--data-urlencode','gsrlimit=2','--data-urlencode','prop=extracts','--data-urlencode','explaintext=1','--data-urlencode','exlimit=2','--data-urlencode','format=json'],capture_output=True,text=True).stdout
        try:
            d=json.loads(r); open(f,'w').write(r); print(q,[(p['title'],len(p.get('extract',''))) for p in d['query']['pages'].values()]); break
        except Exception: time.sleep(10)
    time.sleep(4)
