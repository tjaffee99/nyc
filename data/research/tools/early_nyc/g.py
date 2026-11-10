import re, sys, glob, os
D = '/home/user/nyc/data/raw/early_nyc/wiki/'
def clean(s):
    s = re.sub(r'<ref[^>]*?/>', '', s); s = re.sub(r'<ref[^>]*>.*?</ref>', '', s, flags=re.S)
    s = re.sub(r'\{\{(?:convert|cvt)\|([^|}]+)\|([^|}]+)[^}]*\}\}', r'\1 \2', s)
    s = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', s); s = re.sub(r"'{2,}", '', s)
    return re.sub(r'\s+', ' ', s)
def g(fname, pat, n=2, w=230):
    fs = glob.glob(D + fname + '.wiki')
    if not fs: print(f'## {fname}: (no file)'); return
    t = clean(open(fs[0]).read()); k = 0
    for m in re.finditer(pat, t, flags=re.I):
        a = max(0, m.start() - w // 3); print(f'## {fname} /{pat}/: …{t[a:a + w]}…'); k += 1
        if k >= n: break
    if k == 0: print(f'## {fname} /{pat}/: NO MATCH')
def coord(fname):
    fs = glob.glob(D + fname + '.wiki')
    if not fs: return None
    t = open(fs[0]).read()
    m = re.search(r'\{\{coord\|([^}]*)\}\}', t, flags=re.I)
    return m.group(1)[:80] if m else None
if __name__ == '__main__':
    for a in sys.argv[1:]:
        f, p = a.split('::'); g(f, p)
