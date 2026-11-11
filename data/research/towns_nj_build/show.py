import re,sys,glob
# show.py title-substring regex [maxlen]
pat=re.compile(sys.argv[2],re.I); ml=int(sys.argv[3]) if len(sys.argv)>3 else 260
for f in sorted(glob.glob('/home/user/nyc/data/interim/towns_nj_raw/wp_*'+sys.argv[1]+'*')):
    t=open(f,errors='ignore').read()
    t=re.sub(r'<ref[^>]*/>','',t); t=re.sub(r'<ref.*?</ref>','',t,flags=re.S)
    t=re.sub(r'\{\{(?:cite|Cite|citation|Citation)[^{}]*\}\}','',t)
    t=re.sub(r'\[\[(?:File|Image):[^\]]*(?:\[\[[^\]]*\]\][^\]]*)*\]\]','',t)
    t=re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]',r'\1',t)
    print('=====',f.split('wp_')[1][:60],len(t))
    n=0
    for ln in re.split(r'\n|(?<=[.!?]) (?=[A-Z])',t):
        if pat.search(ln) and not ln.startswith(('|image','|caption','{{Use')):
            print(' -',ln.strip()[:ml]); n+=1
            if n>=int(sys.argv[4] if len(sys.argv)>4 else 12): break
