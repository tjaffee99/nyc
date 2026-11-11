import requests,time
H={'User-Agent':'NYCThroughTime-research/0.1'}
def jget(url,params,tries=8):
    for k in range(tries):
        r=requests.get(url,params=params,headers=H,timeout=90)
        if r.status_code==200 and r.text[:1] in '{[':return r.json()
        time.sleep(min(20*(k+1),120))
    raise RuntimeError('rate '+str(r.status_code))
