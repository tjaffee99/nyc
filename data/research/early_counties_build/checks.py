import pandas as pd, math, bisect, re
T='data/tables/'
pops={}
for f in ['counties','outer']:
    for r in pd.read_csv(T+f'population_{f}.csv').itertuples(): pops.setdefault(r.area,{})[int(r.year)]=float(r.population)
def Pc(a,t):
    d=pops[a];ys=sorted(d)
    if t<=ys[0]: return d[ys[0]]*math.exp(-0.022*(ys[0]-t))
    if t>=ys[-1]: return d[ys[-1]]
    i=bisect.bisect(ys,t);x,y=ys[i-1],ys[i]
    return math.exp(math.log(d[x])+(math.log(d[y])-math.log(d[x]))*(t-x)/(y-x))
area={};P30={}
for l in open('data/interim/early_counties/spec.py'):
    f=l.split('|')
    if len(f)==11 and f[6].isdigit(): area[f[0]]=f[7];P30[f[0]]=float(f[6])
d=pd.read_csv(T+'early_counties.csv'); e=pd.read_csv(T+'early_nyc.csv')
print('cols equal',list(d.columns)==list(e.columns),'ids unique',d.id.is_unique,'overlap',len(set(d.id)&set(e.id)),'start<end',(d.start_year<d.end_year).all(),'max end',d.end_year.max())
print('bbox ok',d.lon.between(-75.37,-71.85).all() and d.lat.between(39.47,42.20).all(),'rows',len(d),'dwellings',d['count'].sum())
doc=d.shape_note.str.startswith('DOCUMENTED'); print('DOCUMENTED rows',doc.sum(),round(doc.mean(),3),'dwellings',d[doc]['count'].sum(),round(d[doc]['count'].sum()/d['count'].sum(),3))
d['town']=d.id.str.replace(r'^ec_','',regex=True).str.replace(r'_\d+_\d+$','',regex=True)
Y=[1670,1700,1750,1800,1840]
tab=pd.DataFrame({y:d[(d.start_year<=y)&(d.end_year>y)].groupby('town')['count'].sum() for y in Y}).fillna(0).astype(int)
top=tab.sort_values(1840,ascending=False).head(20)
out=[]
for t in top.index:
    out.append('| %s | %s |'%(t,' | '.join('%d (%s)'%(top.loc[t,y],('%d'%(Pc(area[t],y)/top.loc[t,y])) if top.loc[t,y] else '-') for y in Y)))
print('\n'.join(out))
print('totals',tab.sum().to_dict(),'towns',d.town.nunique(),'rows per county',d.groupby('borough').size().to_dict())
for t in tab.index:
    for y in Y:
        if tab.loc[t,y]*6>0.35*Pc(area[t],y): print('HIGH',t,y,tab.loc[t,y],round(Pc(area[t],y)))
# thin check: drawn 1840 vs P30/6
th=[(t,tab.loc[t,1840],round(P30[t]*Pc(area[t],1840)/Pc(area[t],1830)/6)) for t in tab.index if tab.loc[t,1840]<0.9*P30[t]*Pc(area[t],1840)/Pc(area[t],1830)/6]
print('thinned towns',len(th),th[:25])
