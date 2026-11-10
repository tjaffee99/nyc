"""Fetch the lead section (infobox) wikitext of Wikipedia articles and print the dimension fields."""
import json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path
OUT = Path('/home/user/nyc/data/raw/landmarks_towers/wp')
KEYS = re.compile(r'^\s*\|\s*(architectural|height|roof|tip|antenna_spire|top_floor|observatory|floor_count|floors|start_date|groundbreaking|ground_breaking|topped_out|completion_date|completed|opened|opening|built|architect|architecture_firm|main_contractor|structural_system|floor_area|renovation_date|inauguration_date|cost|coordinates)\b[^=]*=\s*(.+)$', re.I)
for page in sys.argv[1:]:
    f = OUT / (page.replace('/', '_') + '.txt')
    if not f.exists():
        url = 'https://en.wikipedia.org/w/api.php?action=parse&prop=wikitext&section=0&format=json&redirects=1&page=' + urllib.parse.quote(page)
        req = urllib.request.Request(url, headers={'User-Agent': 'NYCThroughTime-research/0.1'})
        ok = False
        for attempt in range(5):
            try:
                d = json.loads(urllib.request.urlopen(req, timeout=30).read())
                f.write_text(d['parse']['wikitext']['*'])
                ok = True
                break
            except Exception as e:
                err = e
                time.sleep(8 * (attempt + 1))
        if not ok:
            print(page, 'ERROR', err); continue
        time.sleep(2.5)
    print('##', page)
    for line in f.read_text().splitlines():
        mm = KEYS.match(line)
        if mm and mm.group(2).strip():
            v = re.sub(r'<ref[^>]*>.*?</ref>|<ref[^>]*/>', '', mm.group(2))
            print(f'   {mm.group(1)}: {v.strip()[:150]}')
