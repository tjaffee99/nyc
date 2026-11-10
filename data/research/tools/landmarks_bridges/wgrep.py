import re, sys, os, requests, time
def get(t):
    fn=f'data/raw/landmarks_bridges/wiki/{t}.txt'
    if not os.path.exists(fn):
        r=requests.get('https://en.wikipedia.org/w/index.php',params={'title':t,'action':'raw'},headers={'User-Agent':'NYCThroughTime-research/0.1'},timeout=60)
        if r.status_code!=200: print('FAIL',t,r.status_code); return ''
        open(fn,'w').write(r.text); time.sleep(1.2)
    return open(fn).read()
def clean(txt):
    txt=re.sub(r'<ref[^>]*?/>','',txt); txt=re.sub(r'<ref.*?</ref>','',txt,flags=re.S)
    txt=re.sub(r'\{\{(?:convert|cvt)\|([^{}]*?)\}\}',lambda m:' '.join(m.group(1).split('|')[:4]),txt,flags=re.I)
    txt=re.sub(r'\{\{sfn[^{}]*\}\}','',txt,flags=re.I); txt=re.sub(r'\{\{efn[^{}]*\}\}','',txt,flags=re.I)
    txt=re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]',r'\1',txt)
    return txt
def grep(t,rx,mx=25,w=420):
    txt=clean(get(t))
    n=0
    for s in re.split(r'(?<=[.!?])\s+|\n',txt):
        if re.search(rx,s,re.I) and re.search(r'\d',s):
            print('  -',s.strip()[:w]); n+=1
            if n>=mx: break
if __name__=='__main__':
    t=sys.argv[1]; print('=====',t); grep(t,sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else 25)
