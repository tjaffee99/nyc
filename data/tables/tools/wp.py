"""Small Wikipedia helpers (generic UA, polite delays)."""
import json, time, urllib.parse, requests
S = requests.Session(); S.headers['User-Agent'] = 'NYCThroughTime-research/0.1'
API = 'https://en.wikipedia.org/w/api.php'
def get(params, tries=7):
    for k in range(tries):
        r = S.get(API, params=params, timeout=60)
        if r.status_code == 200: return r.json()
        ra = r.headers.get('Retry-After')
        time.sleep(min(90, int(ra) + 2) if ra and ra.isdigit() else 15 + 15 * k)
    r.raise_for_status()
def titles_of(urls):
    return sorted({urllib.parse.unquote(u.split('/wiki/')[1].split('#')[0]).replace('_', ' ') for u in urls if 'en.wikipedia.org/wiki/' in u})
def check(titles):
    bad = []; red = {}
    for i in range(0, len(titles), 50):
        d = get({'action': 'query', 'format': 'json', 'redirects': 1, 'titles': '|'.join(titles[i:i+50])})['query']
        for r in d.get('redirects', []): red[r['from']] = r['to']
        for p in d['pages'].values():
            if 'missing' in p or 'invalid' in p: bad.append(p.get('title'))
        time.sleep(3)
    return bad, red
def coords(titles):
    """title -> (lat, lon) from article coordinates (follows redirects)."""
    out = {}
    for i in range(0, len(titles), 50):
        batch = titles[i:i+50]
        d = get({'action': 'query', 'format': 'json', 'redirects': 1, 'prop': 'coordinates', 'colimit': 'max', 'coprimary': 'primary', 'titles': '|'.join(batch)})['query']
        back = {}
        for n in d.get('normalized', []): back[n['to']] = n['from']
        for r in d.get('redirects', []): back[r['to']] = back.get(r['from'], r['from'])
        for p in d['pages'].values():
            t = p.get('title'); src = back.get(t, t)
            if 'coordinates' in p:
                c = p['coordinates'][0]; out[src] = (c['lat'], c['lon']); out[t] = (c['lat'], c['lon'])
            elif 'missing' in p: out[src] = 'MISSING'
        time.sleep(3)
    return out
