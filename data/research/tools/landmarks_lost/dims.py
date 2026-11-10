import re, sys
def sents(path, maxn=60, extra=None, width=330):
    t = open(path, encoding='utf-8').read()
    t = re.sub(r'<ref[^>]*/>', '', t)
    t = re.sub(r'<ref[^>]*>.*?</ref>', '', t, flags=re.S)
    t = re.sub(r'\{\{sfn[^}]*\}\}', '', t)
    t = re.sub(r'\{\{efn\|', '(note: ', t)
    pat = re.compile(r'\{\{(?:convert|cvt)\|[^}]*\}\}|\b\d[\d,\.]*\s*(?:feet|foot|ft|metres|meters|m\b|acres|stories|storeys|story)', re.I)
    out = []
    for para in t.split('\n'):
        if para.startswith('|') and not re.search(r'height|floor|roof|antenna|area|built|demol|start|complet|open|clos|destr', para, re.I):
            continue
        for s in re.split(r'(?<=[\.\!\?])\s+(?=[A-Z\[\{])', para):
            if pat.search(s) or (extra and re.search(extra, s, re.I)):
                s = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', s)
                s = re.sub(r'\{\{(?:convert|cvt)\|([^}]*)\}\}', lambda m: ' '.join(m.group(1).split('|')[:4]), s, flags=re.I)
                s = s.strip()
                if len(s) > width: 
                    m = pat.search(s) or re.search(extra or 'zzzz', s, re.I) or re.search('.', s)
                    a = max(0, m.start()-width//2); s = s[a:a+width]
                out.append(s)
    seen=set(); n=0
    for s in out:
        if s in seen: continue
        seen.add(s); print(' -', s); n+=1
        if n>=maxn: print(' ...'); break
if __name__ == '__main__':
    args = sys.argv[1:]
    maxn = 60; extra=None
    files=[]
    for a in args:
        if a.startswith('-n'): maxn=int(a[2:])
        elif a.startswith('-e'): extra=a[2:]
        else: files.append(a)
    for f in files:
        print('=====', f); sents(f, maxn, extra)
