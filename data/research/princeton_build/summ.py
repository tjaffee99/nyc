import re,sys,os,glob
files=sys.argv[1:] or sorted(glob.glob('pages/*.txt'))
for f in files:
    t=open(f).read()
    t=re.sub(r'<ref[^>]*?/>|<ref.*?</ref>|<!--.*?-->','',t,flags=re.S)
    t=re.sub(r'\{\{[Ss]fn[^}]*\}\}','',t)
    print('##',os.path.basename(f)[:-4],len(t))
    for l in t.split('\n')[:400]:
        if re.match(r'\|\s*(built|completed|opened|open|established|construction_start|construction_end|year_built|date_opened|dedicated|cornerstone|groundbreaking|built_start|architect)\s*=',l) and re.search(r'\d{4}',l): print('  IB',l.strip()[:160])
    n=0
    for s in re.split(r'(?<=[.!?])\s+',t):
        if n<6 and re.search(r'\b(built|completed|opened|constructed|dedicated|erected|designed)\b',s) and re.search(r'\b1[6-9]\d\d\b|\b20[0-2]\d\b',s) and len(s)<420 and not s.startswith('|') and not s.startswith('['+'['+'File'):
            print('  -',s.replace('\n',' ')[:330]); n+=1
