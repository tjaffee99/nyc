import csv, sys, json, urllib.parse, urllib.request
UA={'User-Agent':'NYCThroughTime-research/0.1'}
def check(urls):
    titles=sorted({urllib.parse.unquote(u.split('/wiki/')[1].split('#')[0]).replace('_',' ') for u in urls if 'en.wikipedia.org/wiki/' in u})
    bad=[]; red={}
    for i in range(0,len(titles),50):
        q='https://en.wikipedia.org/w/api.php?action=query&format=json&redirects=1&titles='+urllib.parse.quote('|'.join(titles[i:i+50]))
        d=json.load(urllib.request.urlopen(urllib.request.Request(q,headers=UA),timeout=60))['query']
        for r in d.get('redirects',[]): red[r['from']]=r['to']
        for n in d.get('normalized',[]): pass
        for p in d['pages'].values():
            if 'missing' in p or 'invalid' in p: bad.append(p.get('title'))
    return titles,bad,red
if __name__=='__main__':
    for f in sys.argv[1:]:
        urls=[r['source_url'] for r in csv.DictReader(open(f))]
        t,bad,red=check(urls)
        print(f, len(t),'titles; MISSING:',bad); print(' redirects:',red)
