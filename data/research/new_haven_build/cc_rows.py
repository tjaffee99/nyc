import pandas as pd,re
pd.set_option('display.width',250,'display.max_colwidth',60)
m=pd.read_pickle('research/new_haven_build/join.pkl');df=pd.read_pickle('research/new_haven_build/df.pkl')
used=set(pd.read_csv('research/new_haven_build/ct_used_ids.csv').iloc[:,0])
m['yr']=pd.to_numeric(m.cd.str.extract(r'^(\d{4})')[0]);m['circa']=m.cd.fillna('').str.contains('CIRCA')
m=m[m.yr.notna()]
t=df[((df.name.fillna('')!='')|(df.area_m2>1500))&(df.heap.eq(True)|df.year_raw.isna())&~df.id.isin(used)]
mm=m[m.bi.isin(t.index)].copy()
g=mm.groupby('bi').agg(yrs=('yr',lambda s:sorted(set(s))),cd=('cd','first'),cname=('cname',lambda s:'; '.join(str(x) for x in s if x)),n=('yr','size'),circa=('circa','min')).reset_index()
g=g.join(df[['id','name','area_m2','year_raw']],on='bi')
g['spread']=g.yrs.map(lambda y:max(y)-min(y))
g.to_pickle('research/new_haven_build/cc_cand.pkl')
print(len(g),(g.n>1).sum(),(g.spread>5).sum())
print(g[['name','cname','cd','n','area_m2','year_raw']].to_string())
