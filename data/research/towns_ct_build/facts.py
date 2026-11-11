import sys,re,glob,os
D='/home/user/nyc/data/interim/towns_ct_raw/wp/'
keys=re.compile(r'^\|\s*(built|built_date|completed|completion_date|opened|opened_date|open_date|opening_date|construction_start_date|start_date|year_built|date_built|dedicated|consecrated|height|roof|top_floor|floor_count|floors|architect|architecture_firm|architectural_style|cost|destroyed|demolished|dedication|established|founded|coordinates|material|structural_system|building_type|status|dates?)\s*=\s*(.+)',re.I)
def clean(s):
    s=re.sub(r'<ref[^>]*/>','',s); s=re.sub(r'<ref[^>]*>.*?</ref>','',s,flags=re.S)
    s=re.sub(r'\{\{(?:cvt|convert)\|([^|}]*)\|([^|}]*)[^}]*\}\}',r'\1 \2',s)
    s=re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]',r'\1',s); s=re.sub(r"'''?",'',s); return s
for t in sys.argv[1:]:
    p=D+t+'.txt'
    if not os.path.exists(p): print('##',t,'MISSING'); continue
    x=open(p).read(); print('##',t)
    for l in x.split('\n')[:140]:
        m=keys.match(l)
        if m and m.group(2).strip(): print('  ',m.group(1),'=',clean(m.group(2))[:140])
    body=clean(x.split('\n\n')[-0] if False else x)
    # lead: first prose line after infobox
    for l in x.split('\n'):
        if l.startswith("'''") : print('  LEAD:',clean(l)[:700]); break
