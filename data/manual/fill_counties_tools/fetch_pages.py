"""Fetch web pages (history pages, reports) as text into data/raw/fill_counties/pages/ and print the
sentences that match a regex.  Cached; generic User-Agent; 1 s between requests.

  python fetch_pages.py REGEX cap width URL [URL ...]      (REGEX '-' = only fetch and report size)
"""
import hashlib, html, os, re, sys, time
import requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
OUT = os.path.join(ROOT, 'data', 'raw', 'fill_counties', 'pages')
UA = {'User-Agent': 'NYCThroughTime-research/0.1'}


def path(url):
    stem = re.sub(r'[^A-Za-z0-9]+', '_', url.split('//', 1)[-1])[:90]
    return os.path.join(OUT, stem + '_' + hashlib.md5(url.encode()).hexdigest()[:6] + '.txt')


def text_of(raw, ctype):
    if 'pdf' in ctype or raw[:5] == b'%PDF-':
        import io
        try:
            from pypdf import PdfReader
        except Exception:
            return '#PDF (no pypdf)'
        return '\n'.join((p.extract_text() or '') for p in PdfReader(io.BytesIO(raw)).pages)
    t = raw.decode('utf-8', 'replace')
    t = re.sub(r'(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>', ' ', t)
    t = re.sub(r'(?i)<(br|/p|/div|/li|/h[1-6]|/tr)[^>]*>', '\n', t)
    t = html.unescape(re.sub(r'<[^>]+>', ' ', t))
    return re.sub(r'[ \t\r\f\v]+', ' ', t)


def fetch(url):
    p = path(url)
    if os.path.exists(p):
        return open(p, encoding='utf-8').read()
    try:
        r = requests.get(url, headers=UA, timeout=40)
        txt = text_of(r.content, r.headers.get('content-type', '')) if r.status_code == 200 else f'#MISSING {r.status_code}'
    except Exception as e:
        txt = f'#MISSING {e!r}'[:200]
    time.sleep(1.0)
    os.makedirs(OUT, exist_ok=True)
    open(p, 'w', encoding='utf-8').write(txt)
    return txt


if __name__ == '__main__':
    rx, cap, width = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    for u in sys.argv[4:]:
        t = fetch(u)
        print(f'\n### {u} [{len(t)} ch] {t[:40] if t.startswith("#") else ""}')
        if rx == '-' or t.startswith('#MISSING'):
            continue
        k = 0
        for s in re.split(r'(?<=[.!?])\s+(?=[A-Z"])|\n+', t):
            s = s.strip()
            if len(s) > 30 and re.search(rx, s, re.I) and k < cap:
                k += 1; print(' -', s[:width])
