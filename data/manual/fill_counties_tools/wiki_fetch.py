"""Fetch Wikipedia articles as raw wikitext (index.php?action=raw) into data/raw/fill_counties/wiki/.

Used only to check dates of fill / excavation; every fact taken from an article is cited in
fill_zones_counties.csv with the article URL (text CC BY-SA 4.0).  Polite: 1.5 s between requests,
generic User-Agent, cached (a title already on disk is not fetched again).

  .venv/bin/python data/manual/fill_counties_tools/wiki_fetch.py titles.txt        # fetch
  .venv/bin/python data/manual/fill_counties_tools/wiki_fetch.py --grep REGEX T1 T2  # sentences with a year
"""
import os, re, sys, time, urllib.parse
import requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
OUT = os.path.join(ROOT, 'data', 'raw', 'fill_counties', 'wiki')
UA = {'User-Agent': 'NYCThroughTime-research/0.1'}
KEY = (r'landfill|\bfill|filled|reclaim|dredg|bulkhead|drain|marsh|acre|excavat|enlarg|expan|'
       r'extend|canal|basin|reservoir|shore|creek|joined|connected|island|meadow|swamp|dump|pond')


def path(title):
    return os.path.join(OUT, re.sub(r'[^A-Za-z0-9_.()-]', '_', title.replace(' ', '_')) + '.txt')


def fetch(title, depth=0):
    p = path(title)
    if os.path.exists(p):
        return open(p, encoding='utf-8').read()
    url = 'https://en.wikipedia.org/w/index.php?action=raw&title=' + urllib.parse.quote(title.replace(' ', '_'))
    for attempt in range(4):
        r = requests.get(url, headers=UA, timeout=30)
        if r.status_code == 429:
            time.sleep(8 * (attempt + 1))
            continue
        break
    time.sleep(1.5)
    if r.status_code != 200:
        txt = f'#MISSING {r.status_code}'
    else:
        txt = r.text
        m = re.match(r'\s*#REDIRECT\s*\[\[([^\]#|]+)', txt, re.I)
        if m and depth < 2:
            txt = f'#REDIRECTED_TO {m.group(1)}\n' + fetch(m.group(1).strip(), depth + 1)
    open(p, 'w', encoding='utf-8').write(txt)
    return txt


def clean(t):
    t = re.sub(r'<ref[^>/]*/>', '', t)
    t = re.sub(r'<ref[^>]*>.*?</ref>', '', t, flags=re.S)
    for _ in range(4):
        t = re.sub(r'\{\{(?:convert|cvt)\|([^|{}]+)\|([^|{}]+)[^{}]*\}\}', r'\1 \2', t)
        t = re.sub(r'\{\{[^{}]*\}\}', '', t)
    t = re.sub(r'\[\[(?:File|Image):[^\]]*\]\]', '', t)
    t = re.sub(r'\[\[[^\]|]*\|([^\]]*)\]\]', r'\1', t)
    t = re.sub(r'\[\[([^\]]*)\]\]', r'\1', t)
    t = re.sub(r"'{2,}", '', t)
    t = re.sub(r'<[^>]+>', '', t)
    return t


def sentences(title, extra=None, cap=40, width=330):
    t = clean(fetch(title))
    out = []
    rx = re.compile(extra or KEY, re.I)
    for para in t.split('\n'):
        if para.startswith(('|', '{', '}', '!', '*', '=')) and not para.startswith('* '):
            continue
        for s in re.split(r'(?<=[.!?])\s+(?=[A-Z])', para):
            if re.search(r'\b(1[6-9]\d\d|20[0-2]\d)\b', s) and rx.search(s):
                out.append(s.strip()[:width])
    return out[:cap]


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    a = sys.argv[1:]
    if a and a[0] == '--grep':
        rx = a[1] if a[1] != '-' else None
        for t in a[2:]:
            txt = fetch(t)
            print(f'\n### {t}  [{len(txt)} ch]' + ('  MISSING' if txt.startswith('#MISSING') else ''))
            for s in sentences(t, rx):
                print(' -', s)
    else:
        titles = [l.strip() for l in open(a[0]) if l.strip() and not l.startswith('#')]
        for t in titles:
            txt = fetch(t)
            tag = 'MISSING' if txt.startswith('#MISSING') else ('-> ' + txt.split('\n')[0][15:] if txt.startswith('#REDIRECTED') else 'ok')
            print(f'{len(txt):7d} {tag:10s} {t}', flush=True)


def grep_all(rx, cap=6, width=420, titles=None):
    """Search every cached article for sentences matching rx; print title + sentence."""
    import glob
    r = re.compile(rx, re.I)
    for p in sorted(glob.glob(os.path.join(OUT, '*.txt'))):
        name = os.path.basename(p)[:-4]
        if titles and not re.search(titles, name, re.I):
            continue
        t = clean(open(p, encoding='utf-8').read())
        hits = []
        for para in t.split('\n'):
            for s in re.split(r'(?<=[.!?])\s+(?=[A-Z])', para):
                if r.search(s):
                    hits.append(s.strip()[:width])
        for s in hits[:cap]:
            print(f'[{name}] {s}')
