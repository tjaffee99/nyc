"""Research tables: what the photographs say about the placeholder years, per district.
Reads presence.parquet + the footprint snapshot + data/tables/places.csv; prints markdown."""
import sys, numpy as np, pandas as pd, duckdb
sys.path.insert(0, '/home/user/nyc/pipeline')
import aerial_presence as ap
HI, LO = ap.T_HI, ap.T_LO
pres = pd.read_parquet(ap.OUT_DIR / 'presence.parquet')
fp = duckdb.connect().execute(f"select doitt_id, boro, lon, lat, start_year, year_src, year_confidence, raw_year, area from '{ap.SNAPSHOT}'").fetchdf()
d = fp.merge(pres, on='doitt_id', how='left')
d['heap'] = d.year_src.str.startswith('heap')
d = d[(d.area >= 40)].reset_index(drop=True)
d['y'] = np.floor(d.start_year)
mx = 111320 * np.cos(np.radians(40.7)); my = 110574
def stats(m):
    k = d[m & d.heap]
    r = {'placeholder-year buildings': len(k)}
    for yr in (1924, 1951):
        p = k[f'p{yr}']; ok = p.notna()
        late = ok & (k.y > yr); early = ok & (k.y <= yr)
        r[f'{yr}: pipeline has standing %'] = 100 * (k.y <= yr).mean() if len(k) else np.nan
        r[f'{yr}: photo shows standing %'] = 100 * (p[ok] >= HI).mean() if ok.sum() else np.nan
        r[f'{yr}: photo shows open %'] = 100 * (p[ok] <= LO).mean() if ok.sum() else np.nan
        r[f'{yr}: dated later but standing (n)'] = int((late & (p >= HI)).sum())
        r[f'{yr}: of those dated later, standing %'] = 100 * (p[late] >= HI).mean() if late.sum() >= 20 else np.nan
        r[f'{yr}: dated earlier but open (n)'] = int((early & (p <= LO)).sum())
        r[f'{yr}: of those dated earlier, open %'] = 100 * (p[early] <= LO).mean() if early.sum() >= 20 else np.nan
    return r
pl = pd.read_csv('/home/user/nyc/data/tables/places.csv')
pl = pl[pl.tier.isin(['town', 'neighborhood', 'city', 'village'])]
pl = pl[(pl.lon > -74.27) & (pl.lon < -73.69) & (pl.lat > 40.49) & (pl.lat < 40.92)]
pl = pl.sort_values('year_end').drop_duplicates(subset=['lat', 'lon'], keep='last')
rows = []
for r in pl.itertuples():
    m = (np.hypot((d.lon.values - r.lon) * mx, (d.lat.values - r.lat) * my) <= 600)
    if (m & d.heap.values).sum() < 150: continue
    rows.append({'district': r.name, 'borough': r.county, 'lon': r.lon, 'lat': r.lat, **stats(pd.Series(m))})
t = pd.DataFrame(rows)
t.to_csv(ap.WORK / 'districts.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 300)
focus = ['Gravesend', 'Flatlands', 'New Utrecht', 'Jamaica', 'Flushing']
show = ['district', 'borough', 'placeholder-year buildings'] + [c for c in t.columns if c.startswith('1924')]
print('\n### named districts (600 m around the label), 1924\n'); print(ap._md(t.sort_values('1924: dated later but standing (n)', ascending=False)[show].head(45), '{:.0f}'))
show = ['district', 'borough', 'placeholder-year buildings'] + [c for c in t.columns if c.startswith('1951')]
print('\n### named districts, 1951\n'); print(ap._md(t.sort_values('1951: dated later but standing (n)', ascending=False)[show].head(25), '{:.0f}'))
print('\n### too early, 1924 (dated earlier but the photo shows open ground)\n'); print(ap._md(t.sort_values('1924: dated earlier but open (n)', ascending=False)[['district', 'borough', 'placeholder-year buildings', '1924: pipeline has standing %', '1924: photo shows standing %', '1924: dated earlier but open (n)', '1924: of those dated earlier, open %']].head(20), '{:.0f}'))
print('\n### too early, 1951\n'); print(ap._md(t.sort_values('1951: dated earlier but open (n)', ascending=False)[['district', 'borough', 'placeholder-year buildings', '1951: pipeline has standing %', '1951: photo shows standing %', '1951: dated earlier but open (n)', '1951: of those dated earlier, open %']].head(20), '{:.0f}'))
# borough totals
rows = []
for b, nm in ap.BORO_NAME.items(): rows.append({'borough': nm, **stats(d.boro == b)})
rows.append({'borough': 'all', **stats(pd.Series(np.ones(len(d), bool)))})
print('\n### boroughs\n'); print(ap._md(pd.DataFrame(rows), '{:.0f}'))
