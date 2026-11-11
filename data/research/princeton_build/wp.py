import urllib.request,urllib.parse,json,time,sys
UA={'User-Agent':'NYCThroughTime-research/0.1'}
def get(url,tries=5):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=60).read().decode()
        except Exception as e:
            time.sleep(15*(i+1)); err=e
    print('FAIL',url,err,file=sys.stderr); return None
def api(**p):
    p['format']='json'
    t=get('https://en.wikipedia.org/w/api.php?'+urllib.parse.urlencode(p))
    return json.loads(t) if t else None
def members(cat):
    d=api(action='query',list='categorymembers',cmtitle=cat,cmlimit=500)
    return [x['title'] for x in d['query']['categorymembers']]
if __name__=='__main__':
    for c in sys.argv[1:]:
        print(c, '; '.join(members(c)));time.sleep(1)
