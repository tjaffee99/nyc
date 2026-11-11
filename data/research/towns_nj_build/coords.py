import re,sys,glob
for k in sys.argv[1:]:
    for f in glob.glob('/home/user/nyc/data/interim/towns_nj_raw/wp_*'+k+'*'):
        t=open(f,errors='ignore').read()
        m=re.search(r'\{\{\s*(?:coord|Coord|coords)\s*\|([^}]*)\}\}',t)
        lat=re.search(r'lat(?:itude)?\s*=\s*(-?[\d.]+)',t); lon=re.search(r'lon(?:gitude)?\s*=\s*(-?[\d.]+)',t)
        out=None
        if m:
            p=[x.strip() for x in m.group(1).split('|')]
            nums=[]
            for x in p:
                if re.fullmatch(r'-?[\d.]+',x): nums.append(float(x))
                elif x in 'NSEW': nums.append(x)
                else: 
                    if nums and not isinstance(nums[-1],str) and False: pass
            # decimal case
            if len(p)>=2 and re.fullmatch(r'-?[\d.]+',p[0]) and re.fullmatch(r'-?[\d.]+',p[1]): out=(float(p[0]),float(p[1]))
            else:
                # dms: d|m|s|N|d|m|s|W
                try:
                    i=[j for j,x in enumerate(p) if x in('N','S')][0]; lat_=[float(x) for x in p[:i]]; sl=p[i]
                    e=[j for j,x in enumerate(p) if x in('E','W')][0]; lon_=[float(x) for x in p[i+1:e]]; sw=p[e]
                    la=sum(v/60**k for k,v in enumerate(lat_)); lo=sum(v/60**k for k,v in enumerate(lon_))
                    out=(la*(1 if sl=='N' else -1),lo*(1 if sw=='E' else -1))
                except Exception: pass
        elif lat and lon: out=(float(lat.group(1)),float(lon.group(1)))
        print(f.split('wp_')[1][:50],out)
