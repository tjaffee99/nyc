"""Sentences of cached articles that match a regex (no year needed).  python wgrep.py REGEX cap width T1 T2 ...
(reads data/raw/fill_counties/wiki/; titles are fetched if missing)"""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
import wiki_fetch as W
rx = re.compile(sys.argv[1], re.I); cap = int(sys.argv[2]); width = int(sys.argv[3])
for t in sys.argv[4:]:
    txt = W.fetch(t)
    head = txt[:50].replace('\n', ' ') if txt.startswith('#') else ''
    print(f'\n### {t} [{len(txt)}] {head}')
    k = 0
    for para in W.clean(txt).split('\n'):
        if para.startswith(('|', '{', '}', '!')):
            continue
        for s in re.split(r'(?<=[.!?])\s+(?=[A-Z])', para):
            if rx.search(s) and k < cap:
                k += 1; print(' -', s.strip()[:width])
