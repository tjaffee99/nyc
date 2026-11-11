import requests,sys,re,time,os
H={'User-Agent':'NYCThroughTime-research/0.1'}
def get(title,fmt='text'):
    fn=f"cache_{re.sub(r'[^A-Za-z0-9]','_',title)}.txt"
    if os.path.exists(fn):return open(fn).read()
    for k in range(4):
      r=requests.get('https://en.wikipedia.org/w/api.php',params={'action':'query','prop':'extracts','explaintext':1,'titles':title,'format':'json','redirects':1},headers=H,timeout=60)
      if r.status_code==200 and r.text.startswith('{'):break
      time.sleep(5*(k+1))
    p=list(r.json()['query']['pages'].values())[0]
    t=p.get('extract','')
    open(fn,'w').write(t);time.sleep(1);return t
if __name__=='__main__':
    for t in sys.argv[1:]:
        x=get(t);print('=====',t,len(x))
