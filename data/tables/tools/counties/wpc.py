"""Wikipedia helpers for the counties tables: cached raw wikitext, census-table parser, coordinates."""
import json, os, re, time, urllib.parse, requests
S = requests.Session(); S.headers['User-Agent'] = 'NYCThroughTime-research/0.1'
D = '/home/user/nyc/data/raw/tables_counties/wp/'
os.makedirs(D, exist_ok=True)
API = 'https://en.wikipedia.org/w/api.php'
def fn(title): return D + re.sub(r'[^A-Za-z0-9]+', '_', title)[:150] + '.txt'
def text(title, depth=0):
    f = fn(title)
    if os.path.exists(f): t = open(f, encoding='utf-8').read()
    else:
        t = None
        for k in range(6):
            try: r = S.get('https://en.wikipedia.org/w/index.php', params={'title': title, 'action': 'raw'}, timeout=60)
            except Exception: time.sleep(8); continue
            if r.status_code == 200: t = r.text; break
            if r.status_code == 404: t = ''; break
            ra = r.headers.get('Retry-After'); time.sleep(min(90, int(ra) + 2) if ra and ra.isdigit() else 10 + 10 * k)
        if t is None: return None
        open(f, 'w', encoding='utf-8').write(t); time.sleep(0.6)
    m = re.match(r'\s*#REDIRECT\s*\[\[([^\]#|]+)', t, re.I)
    if m and depth < 3: return text(m.group(1).strip(), depth + 1)
    return t
def census(title):
    """{year: population} from the article's {{US Census population}} template (first one)."""
    t = text(title)
    if not t: return {}
    m = re.search(r'\{\{\s*(US Census population|USCensusPop|Historical populations)', t, re.I)
    if not m: return {}
    seg = t[m.start(): m.start() + 6000]
    out = {}
    for y, v in re.findall(r'\|\s*(1[6-9]\d\d|20[0-2]\d)\s*=\s*([\d,]+)', seg):
        out.setdefault(int(y), int(v.replace(',', '')))
    return out
def get(params, tries=6):
    for k in range(tries):
        try: r = S.get(API, params=params, timeout=60)
        except Exception: time.sleep(8); continue
        if r.status_code == 200: return r.json()
        ra = r.headers.get('Retry-After'); time.sleep(min(90, int(ra) + 2) if ra and ra.isdigit() else 10 + 10 * k)
    raise RuntimeError('api failed')
def coords(titles):
    out = {}
    for i in range(0, len(titles), 50):
        batch = titles[i:i + 50]
        d = get({'action': 'query', 'format': 'json', 'redirects': 1, 'prop': 'coordinates', 'colimit': 'max', 'coprimary': 'primary', 'titles': '|'.join(batch)})['query']
        back = {}
        for n in d.get('normalized', []): back[n['to']] = n['from']
        for r in d.get('redirects', []): back[r['to']] = back.get(r['from'], r['from'])
        for p in d['pages'].values():
            t = p.get('title'); src = back.get(t, t)
            if 'coordinates' in p:
                c = p['coordinates'][0]; out[src] = (c['lat'], c['lon']); out[t] = (c['lat'], c['lon'])
            elif 'missing' in p: out[src] = 'MISSING'; out[t] = 'MISSING'
        time.sleep(1.5)
    return out
