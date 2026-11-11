import json, math, bisect, pandas as pd
from spec import SPEC
T='/home/user/nyc/data/tables/'
pl=pd.concat([pd.read_csv(T+'places_counties.csv'),pd.read_csv(T+'places_outer.csv')]).set_index('id')
pops={}; src={}
for f in ['counties','outer']:
    p=pd.read_csv(T+f'population_{f}.csv')
    for r in p.itertuples():
        pops.setdefault(r.area,{})[int(r.year)]=float(r.population); src.setdefault(r.area,{})[int(r.year)]=r.source_url
ALIAS={}
rot=json.load(open('rot2.json')); rotw=json.load(open('rotw.json'))
def Pc(area,t):
    d=pops[area]; ys=sorted(d)
    if t<=ys[0]:
        return d[ys[0]]*math.exp(-0.022*(ys[0]-t))
    if t>=ys[-1]: return d[ys[-1]]
    i=bisect.bisect(ys,t); a,b=ys[i-1],ys[i]
    return math.exp(math.log(d[a])+(math.log(d[b])-math.log(d[a]))*(t-a)/(b-a))
COLS="id,name,kind,start_year,end_year,lat,lon,height_m,footprint_m,rotation_deg,storeys,material,count,spread_m,confidence,shape_note,source_url,borough".split(',')
CAP=400; CH=30; THIN=160
rows=[]; meta=[]
def endyr(s): return int(min(max(round((s+180)/5)*5,1850),1900))
for line in SPEC.strip().split('\n'):
    key,name,county,loc,t0,H0,P30,area,style,anch,basis=line.split('|')
    t0=int(t0);H0=int(H0);P30=float(P30)
    pr=pl.loc[loc] if ',' not in loc else None
    lat,lon=(map(float,loc.split(',')) if pr is None else (pr.lat,pr.lon))
    url=pr.source_url if pr is not None else 'https://en.wikipedia.org/wiki/'+name.split(' (')[0].replace(' ','_')
    sh=json.load(open('shift.json')).get(key)
    shnote=''
    if sh:
        lat,lon=sh['lat'],sh['lon']; shnote=' Centre moved %d m from the place point to dry ground of the 1609 layer (%.0f%% wet there before).'%(sh['moved_m'],100*sh['w0'])
    anchors=[]
    for a in [x for x in anch.split(';') if x]:
        z=a.split(':'); anchors.append((int(z[0]),int(z[1]),len(z)>2))
    r=rot2=rot.get(key) or rotw.get(key)
    rdeg=r['rot'] if r else 0
    rsrc=('bearing %d deg of the %s of today (Overture roads_region, %s)'%(rdeg,('main street' if r.get('how','').startswith('main') else 'top-class road'),', '.join(r.get('names',[])[:2]) or 'unnamed')) if r else 'rotation 0 (no road found within 1 km; bearing not known)'
    cps=[c for c in [1700,1750,1790,1830] if c>t0+12]
    if P30>2000 and 1810>t0+12: cps.append(1810)
    for a in anchors:
        if a[0]>t0 and a[0] not in cps: cps.append(a[0])
    cps=sorted(set(cps))+[1840]
    pts=[(t0,H0)]+[(a[0],a[1]) for a in anchors]; pts.sort()
    def Hm(t):
        base=H0
        for y,h in pts:
            if y<=t: base=max(base,h)
        # linear interpolation between anchors
        lo=[p for p in pts if p[0]<=t]; hi=[p for p in pts if p[0]>t]
        if lo and hi:
            (y0,h0),(y1,h1)=lo[-1],hi[0]; base=max(base,h0+(h1-h0)*(t-y0)/(y1-y0))
        cur=P30*Pc(area,t)/Pc(area,1830)/6
        return max(base,cur)
    raw={c:Hm(c) for c in cps}; raw[t0]=H0
    # monotone
    prev=0
    for c in sorted(raw): raw[c]=max(raw[c],prev); prev=raw[c]
    Hmax=raw[1840]
    def draw(h):
        if Hmax<=CAP or h<=THIN: return h
        return THIN+(h-THIN)*(CAP-THIN)/(Hmax-THIN)
    scale_note=('' if Hmax<=CAP else ' Drawn thinned: houses above %d are drawn at %.2f per house (compressed; 1840 implies %d, %d drawn).'%(THIN,(CAP-THIN)/(Hmax-THIN),round(Hmax),CAP))
    seq=[t0]+cps; j=0; cum=0
    for k,c in enumerate(seq):
        if k==0:
            n=round(draw(raw[c])); start=t0; span=''
            docrow=any(a[0]==t0 and a[2] for a in anchors)
        else:
            n=round(draw(raw[c]))-cum
            start=int(round((seq[k-1]+c)/2)) if c!=1840 else 1835
            start=max(start,t0+2)
            docrow=any(a[0]==c and a[2] for a in anchors)
        docrow=docrow if k else docrow
        if n<=0 or (k>0 and n<3 and not docrow and c!=1840): continue
        cum+=n
        # footprint
        if style=='S': fp,h,sto,mat=('10x8',6.5,2 if start>=1730 else 1,'stone')
        elif style=='C' and start>=1800: fp,h,sto,mat=('12x9',10.0,3,'brick')
        elif start<1700: fp,h,sto,mat=(('9x7',6.0,2,'wood frame') if style=='N' else ('8x6',5.5,1,'wood frame'))
        elif start<1800: fp,h,sto,mat=('10x8',6.5,2,'wood frame')
        else: fp,h,sto,mat=('11x8',7.5,2,'wood frame')
        # split into chunks
        m=math.ceil(n/CH); per=[n//m+(1 if i<n%m else 0) for i in range(m)]
        for ci,nn in enumerate(per):
            lane=[0,1,-1,2,-2][j%5]*75; blk=j//5; al=[0,1,-1,2,-2,3,-3][blk%7]*330; j+=1
            br=math.radians(rdeg)
            dE=al*math.sin(br)+lane*math.cos(br); dN=al*math.cos(br)-lane*math.sin(br)
            la=lat+dN/110540; lo=lon+dE/(111320*math.cos(math.radians(lat)))
            street=nn>=6
            spread=max(150,8*nn) if street else max(40,18*math.sqrt(nn))
            if k==0: why='the founding cluster of %d dwellings'%nn
            else: why='the dwellings added %d-%d (%d of %d here)'%(seq[k-1],c,nn,n)
            pop=Pc(area,c); 
            if docrow:
                a=[a for a in anchors if a[0]==c][0]
                note=('DOCUMENTED: %s; %d dwellings by %d. '%(basis,a[1],c))
            elif k==0:
                note=('ESTIMATED: founding cluster of %d houses (%s). '%(H0,basis))
            else:
                cur=P30*Pc(area,c)/Pc(area,1830)
                fr=('anchor %s '%'/'.join('%d:%d'%(a[0],a[1]) for a in anchors)) if anchors else ''
                note=('ESTIMATED: %sbasis %s. Village of ca. %d persons in 1830 (recalled from the census, unverified; the township share that lived in the village), scaled to %d by the %s population index (%d vs %d in 1830, population tables) = %d persons / 6 = %d houses, never fewer than the founding cluster of %d%s; %d houses stand by %d. '%(fr,basis,P30,c,area,pop,Pc(area,1830),cur,cur/6,H0,' and the anchors' if anchors else '',round(raw[c]),c))
            note+='This row is %s; positions generated (procedural), on a %s%s.%s'%(why,('street ' if street else 'scatter '),('lane of the town, '+rsrc),scale_note)
            note+=shnote; note=note.replace('"',"'")
            rows.append(dict(id=f'ec_{key}_{c}_{ci}',name=f'{name}, houses of {c}' if k else f'{name}, the first houses',kind='house',start_year=start,end_year=endyr(start),
                lat=round(la,5),lon=round(lo,5),height_m=h,footprint_m=fp,rotation_deg=rdeg,storeys=sto,material=mat,count=nn,spread_m=int(spread),
                confidence='medium' if docrow else 'low',shape_note=note,source_url=(src.get(area,{}).get(c) or url) if docrow else url,borough=county))
# extra rows
rows.append(dict(id='ec_hud_pavonia_0_0',name='Pavonia, the patroonship settlement at Communipaw',kind='house',start_year=1633,end_year=1643,lat=40.70861,lon=-74.06111,height_m=5.5,footprint_m='8x6',rotation_deg=rdeg if False else 0,storeys=1,material='wood frame',count=6,spread_m=90,confidence='low',
  shape_note="ESTIMATED: Michael Pauw's patroonship of Pavonia (1630) had farms and a settlement at Communipaw and Jan Evertsen Bout's bouwerie; destroyed in Kieft's War, 1643 (recalled, not re-fetched). Six dwellings is an assumption; positions generated (procedural).",source_url='https://en.wikipedia.org/wiki/Pavonia,_New_Jersey',borough='Hudson'))
df=pd.DataFrame(rows)[COLS]
df.to_csv('/home/user/nyc/data/tables/early_counties.csv',index=False)
print(len(df),df['count'].sum(),df.confidence.value_counts().to_dict())
