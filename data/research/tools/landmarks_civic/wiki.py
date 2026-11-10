"""Scratch: fetch Wikipedia wikitext (cached) and print dimension contexts. Usage: wiki.py Title[:kw1|kw2] ..."""
import re, sys, time, os, urllib.parse, requests
D = '/home/user/nyc/data/raw/landmarks_civic/wiki/'
for arg in sys.argv[1:]:
    title, _, kws = arg.partition(':')
    f = D + title.replace('/', '_') + '.txt'
    if not os.path.exists(f):
        r = requests.get('https://en.wikipedia.org/wiki/' + urllib.parse.quote(title) + '?action=raw', headers={'User-Agent': 'NYCThroughTime-research/0.1'}, timeout=30)
        if r.status_code == 429:
            time.sleep(25); r = requests.get('https://en.wikipedia.org/wiki/' + urllib.parse.quote(title) + '?action=raw', headers={'User-Agent': 'NYCThroughTime-research/0.1'}, timeout=30)
        if r.status_code != 200:
            print(f"=== {title}: HTTP {r.status_code}"); time.sleep(2); continue
        open(f, 'w').write(r.text); time.sleep(3)
    t = open(f).read()
    m0 = re.match(r'#REDIRECT\s*\[\[([^\]]+)\]\]', t, flags=re.I)
    if m0:
        print('  redirect ->', m0.group(1)); r = requests.get('https://en.wikipedia.org/wiki/' + urllib.parse.quote(m0.group(1).replace(' ', '_')) + '?action=raw', headers={'User-Agent': 'NYCThroughTime-research/0.1'}, timeout=30); t = r.text; open(f, 'w').write(t); time.sleep(1.2)
    t = re.sub(r'<ref[^>]*?/>', '', t); t = re.sub(r'<ref[^>]*>.*?</ref>', '', t, flags=re.S)
    t = re.sub(r'\{\{sfn[^}]*\}\}|\{\{efn[^}]*\}\}|\{\{rp\|[^}]*\}\}', '', t); t = t.replace('\n', ' ')
    print(f"=== {title} ({len(t)} chars)")
    seen = []; n = 0
    C = r'\{\{(?:convert|cvt)\|[^}]*\}\}'
    pat = C if not kws else ('(?:' + kws + ')[^.]{0,150}' + C + '|' + C + '[^.]{0,70}(?:' + kws + ')')
    for m in re.finditer(pat, t, flags=re.I):
        s = max(0, m.start() - (110 if not kws else 30)); e = min(len(t), m.end() + (50 if not kws else 40))
        if seen and s < seen[-1]: s = seen[-1]
        if e <= s: continue
        seen.append(e); n += 1
        if n > int(os.environ.get('MAXHIT', '40')): break
        print('  …' + t[s:e].strip())
