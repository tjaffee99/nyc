import json
names={}
for l in open('../../../raw/extents/spacetime/mapwarper.objects.ndjson'):
    o=json.loads(l)
    if isinstance(o['id'],int) and 8440<=o['id']<=8522: names[o['id']]=o['name'].replace('\r\n',' ')
so={'max_m2':20000.0,'outline_big':0.3,'big_px':4800,'big_r':16,'stone':{'da_abs':5.5,'db_min':-9.0,'db_max':0.5,'dL_min':-28.0,'dL_max':-9.0},'blue':{'db_max':-5.5,'db_min':-16.0,'da_min':-6.0,'da_max':3.0,'dL_min':-22.0,'dL_max':-3.0},
 'street_empty':True,'street_min_q':0.2,'street_win_m':300.0,'street_search':[30.0,15.0],'stone_min_m2':200.0,'stone_min_width_m':6.0,'stone_max_aspect':4.0}
def L(year,atlas,source,ids,outside):
    d=dict(map_year=year,atlas=atlas,source=source,style='bromley_city',style_override=so,require_match=8.0,
      source_url='https://digitalcollections.nypl.org/ (NYPL Map Division, public domain); control points: https://s3.amazonaws.com/spacetime-nypl-org/datasets/mapwarper/mapwarper.objects.ndjson (CC0)',
      plates=[{'id':i,'sheet':'B98-%d'%i,'name':names[i]} for i in ids])
    if outside: d['clip']={'outside_layers':outside}
    return d
B98="Atlas of the Brooklyn borough of the City of New York, originally Kings County (G. W. Bromley & Co., Philadelphia, 1898), NYPL Map Division"
Sanb=['brooklyn_downtown_1887','brooklyn_southwest_1886','brooklyn_williamsburg_1887','brooklyn_greenpoint_1887','brooklyn_bedstuy_1888','brooklyn_bushwick_1888','brooklyn_crownheights_1888','brooklyn_browns_1887','brooklyn_parkslope_1888','kings_towns_1890']
lay={
 'brooklyn_sunsetpark_1898':L(1898,B98+', volume 1 (Ward 8)','bromley_brooklyn_1898',[8518,8519,8520,8521],Sanb),
 'brooklyn_redhook_1898':L(1898,B98+', volume 1 (Wards 6, 12)','bromley_brooklyn_1898',[8515,8516,8517],Sanb),
 'brooklyn_heights_1898':L(1898,B98+', volume 1 (Wards 1-6, 10)','bromley_brooklyn_1898',[8512,8513,8514],Sanb),
 'brooklyn_bayridge_1898':L(1898,B98+', volume 2 (Ward 30)','bromley_brooklyn_1898',[8483,8484,8485,8486,8487,8489,8490,8491,8492,8493,8494,8495],Sanb),
 'brooklyn_williamsburg_1898':L(1898,B98+', volume 1 (Wards 13-19)','bromley_brooklyn_1898',[8459,8461,8462,8463,8465,8469,8522],Sanb),
}
json.dump(lay,open('layers.json','w'),indent=1)
for k,v in lay.items(): print(k,[(p['id'],p['name'][:70]) for p in v['plates']])
