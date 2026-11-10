"""Fetch whole-article wikitext (cached) and print the sentences that date construction."""
import json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path
OUT = Path('/home/user/nyc/data/raw/landmarks_towers/wp_full')
OUT.mkdir(parents=True, exist_ok=True)
PAT = re.compile(r'(groundbreaking|ground[- ]breaking|broke ground|construction (?:of [^.]{0,60} )?(?:began|started|commenced)|work (?:began|started)|excavation|topped out|opened (?:on|in)|was completed|completed in|officially opened|first tenants)', re.I)
def clean(t):
    t = re.sub(r'<ref[^>]*?/>', '', t)
    t = re.sub(r'<ref[^>]*>.*?</ref>', '', t, flags=re.S)
    t = re.sub(r'\{\{(?:convert|cvt)\|([^|}]+)\|([^|}]+)[^}]*\}\}', r'\1 \2', t, flags=re.I)
    t = re.sub(r'\{\{[^{}]*\}\}', '', t)
    t = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', t)
    return t
for page in sys.argv[1:]:
    f = OUT / (page.replace('/', '_') + '.txt')
    if not f.exists():
        url = 'https://en.wikipedia.org/wiki/' + urllib.parse.quote(page) + '?action=raw'
        req = urllib.request.Request(url, headers={'User-Agent': 'NYCThroughTime-research/0.1'})
        ok = False
        for attempt in range(6):
            try:
                raw = urllib.request.urlopen(req, timeout=40).read().decode('utf-8')
                f.write_text(raw); ok = True; break
            except Exception as e:
                err = e; time.sleep(3 * (attempt + 1))
        if not ok:
            print('##', page, 'ERROR', err, flush=True); continue
        time.sleep(1.2)
    txt = clean(f.read_text())
    print('##', page, flush=True)
    seen = 0
    for sent in re.split(r'(?<=[.!?])\s+', txt):
        if PAT.search(sent) and re.search(r'\b(18|19|20)\d\d\b', sent) and len(sent) < 420:
            print('   -', sent.strip().replace('\n', ' ')[:300], flush=True)
            seen += 1
            if seen >= 7: break
