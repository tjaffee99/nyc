"""For every row not flagged estimated/nominal: does the cited Wikipedia article contain the year(s)? Writes verify_years.txt."""
import csv, os, re, sys, time, urllib.parse, requests
S = requests.Session(); S.headers['User-Agent'] = 'NYCThroughTime-research/0.1'
D = '/home/user/nyc/data/raw/tables/wpx/'
os.makedirs(D, exist_ok=True)
def text(title):
    fn = D + re.sub(r'[^A-Za-z0-9]+', '_', title) + '.txt'
    if os.path.exists(fn): return open(fn, encoding='utf-8').read()
    for k in range(6):
        try:
            r = S.get('https://en.wikipedia.org/w/index.php', params={'title': title, 'action': 'raw', 'redirect': 'yes'}, timeout=60)
        except Exception: time.sleep(10); continue
        if r.status_code == 200:
            t = r.text
            m = re.match(r'#REDIRECT\s*\[\[([^\]#|]+)', t, re.I)
            if m: return text(m.group(1).strip())
            open(fn, 'w', encoding='utf-8').write(t); time.sleep(1.2); return t
        if r.status_code == 404: open(fn, 'w').write(''); return ''
        ra = r.headers.get('Retry-After'); time.sleep(min(90, int(ra) + 2) if ra and ra.isdigit() else 15 + 15 * k)
    return None
out = []
def run(fn, idc, y0c, y1c, notec, skip=lambda r: False):
    rows = list(csv.DictReader(open(fn, encoding='utf-8')))
    n = bad = 0
    for r in rows:
        u = r['source_url']
        if 'en.wikipedia.org/wiki/' not in u or skip(r): continue
        t = text(urllib.parse.unquote(u.split('/wiki/')[1].split('#')[0]).replace('_', ' '))
        if t is None: out.append(f'{fn.split("/")[-1]} {r[idc]}: FETCH FAILED'); continue
        n += 1
        miss = [y for y in ([r[y0c]] + ([r[y1c]] if y1c and r[y1c] not in ('9999', '') else [])) if y not in ('1609',) and y.split('.')[0] not in t]
        if miss: bad += 1; out.append(f'{fn.split("/")[-1]} {r[idc]} | {r.get("name", r.get("title", ""))} | years not in article: {",".join(miss)} | {r.get(notec, "")[:110]}')
    out.append(f'## {fn.split("/")[-1]}: checked {n}, flagged {bad}')
T = '/home/user/nyc/data/tables/'
est = lambda r: bool(re.search(r'estimated|nominal|approximate', r.get('note', ''), re.I))
run(T + 'places.csv', 'id', 'year_start', 'year_end', 'note', skip=est)
run(T + 'parks.csv', 'name', 'start_year', 'end_year', 'start_event', skip=lambda r: r['confidence'] == 'estimated')
run(T + 'events.csv', 'title', 'year', None, 'description')
open('verify_years.txt', 'w').write('\n'.join(out) + '\n')
print('\n'.join(o for o in out if o.startswith('##')))
