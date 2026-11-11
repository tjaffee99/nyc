import json,re,sys
d=json.load(open('wt.json'))
def clean(s):
    s=re.sub(r'<ref.*?(</ref>|/>)','',s,flags=re.S);s=re.sub(r'\{\{[^{}]*\}\}','',s)
    s=re.sub(r'\[\[File:[^\]]*\]\]','',s);s=re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]',r'\1',s);return s.replace("'''","").strip()
for k in sys.argv[1:]:
    t=d.get(k,'')
    print('####',k,len(t))
    for tab in re.findall(r'\{\|.*?\n\|\}',t,flags=re.S):
        for row in tab.split('\n|-')[1:]:
            cells=[clean(c) for c in re.split(r'\n[|!]',row) if c.strip()]
            cells=[re.sub(r'^[^|]*\|(?!\|)','',c) if '|' in c[:60] and 'scope' in c[:40] else c for c in cells]
            if any(re.search(r'\b1[6-9]\d\d\b|\b20[0-2]\d\b',c[:40]) for c in cells):
                print(' | '.join(c[:90].replace('\n',' ') for c in cells[:5]))
