"""Writes data/research/aerial_years.md from presence.parquet, the footprint snapshot, the hand check and districts.csv."""
import sys, numpy as np, pandas as pd, duckdb
sys.path.insert(0, '/home/user/nyc/pipeline')
import aerial_presence as ap
HI, LO = ap.T_HI, ap.T_LO
pres = pd.read_parquet(ap.OUT_DIR / 'presence.parquet')
fp = duckdb.connect().execute(f"select doitt_id, boro, lon, lat, start_year, year_src, year_confidence, raw_year, area from '{ap.SNAPSHOT}'").fetchdf().drop_duplicates('doitt_id')
d = fp.merge(pres, on='doitt_id', how='left')
d['heap'] = d.year_src.str.startswith('heap'); d['y'] = np.floor(d.start_year)
hand = pd.read_csv(ap.OUT_DIR / 'hand_check.csv', dtype={'doitt_id': str}).merge(pres, on='doitt_id', how='left')
rate = {}
for yr in (1924, 1951):
    h = hand[hand[f'seen{yr}'].isin(['P', 'A']) & hand[f'p{yr}'].notna()]
    P, A = h[f'p{yr}'][h[f'seen{yr}'] == 'P'], h[f'p{yr}'][h[f'seen{yr}'] == 'A']
    # share of the buildings called "stood" / "open", share of the open ground called "stood" / "open"
    rate[yr] = ((P >= HI).mean(), (P <= LO).mean(), (A >= HI).mean(), (A <= LO).mean())
# reference groups inside the placeholder-year stock of each borough: the "by 1899 / 1900 / 1901" buildings
# all stood in both photographs; the "1955 and later" (for 1951: "1960 and later") ones did not yet
REF = {}
for yr, late in ((1924, 1955), (1951, 1960)):
    for b in ['1', '2', '3', '4', '5', None]:
        k = d[d.heap & d[f'p{yr}'].notna() & ((d.boro == b) if b else True)]
        old = k[k.raw_year.isin([1899, 1900, 1901])][f'p{yr}']; new = k[(k.raw_year >= late) & (k.raw_year <= 1990)][f'p{yr}']
        if b == '1': new = d[d.heap & d[f'p{yr}'].notna() & (d.raw_year >= late) & (d.raw_year <= 1990)][f'p{yr}']   # Manhattan has no late placeholders
        REF[(yr, b)] = ((old >= HI).mean(), (old <= LO).mean(), (new >= HI).mean(), (new <= LO).mean())
def est(st, op, yr, boro=None):
    """Share standing, read between the borough's two reference groups on both calls."""
    a, e, b, c = REF[(yr, boro)]
    if not (st + op > 0): return np.nan
    return 100 * float(np.clip(((st - b) / (a - b) + (c - op) / (c - e)) / 2, 0, 1))
B = [('3', 'Brooklyn'), ('4', 'Queens'), ('2', 'Bronx'), ('5', 'Staten Island'), ('1', 'Manhattan')]
def heap_table(yr):
    k = d[d.heap & d[f'p{yr}'].notna()]
    top = k.raw_year.value_counts(); years = sorted(int(v) for v in top[top >= 3000].index)
    lines = ['| placeholder | ' + ' | '.join(n for _, n in B) + ' |', '|---|' + '---|' * len(B)]
    for yv in years:
        cells = []
        for b, _ in B:
            m = k[(k.raw_year == yv) & (k.boro == b)]
            if len(m) < 300: cells.append('–'); continue
            st, op = (m[f'p{yr}'] >= HI).mean(), (m[f'p{yr}'] <= LO).mean()
            cells.append(f'**{est(st, op, yr, b):.0f} %** ({100*st:.0f} / {100*op:.0f}; {len(m):,})')
        lines.append(f'| {yv} | ' + ' | '.join(cells) + ' |')
    return '\n'.join(lines)
def boro_table():
    lines = ['| borough | placeholder-year buildings | pipeline: standing by 1924 | photo 1924: est. standing (stood / open) | dated after 1924 but standing in the photo | dated by 1924 but open ground in the photo | pipeline: standing by 1951 | photo 1951: est. standing (stood / open) | dated after 1951 but standing | dated by 1951 but open |',
             '|---|---|---|---|---|---|---|---|---|---|']
    for b, nm in B + [(None, 'all')]:
        k = d[d.heap & (d.area >= 40)] if b is None else d[d.heap & (d.area >= 40) & (d.boro == b)]
        cells = [nm, f'{len(k):,}']
        for yr in (1924, 1951):
            p = k[f'p{yr}']; ok = p.notna(); st, op = (p[ok] >= HI).mean(), (p[ok] <= LO).mean()
            late = ok & (k.y > yr); early = ok & (k.y <= yr)
            cells += [f'{100*(k.y <= yr).mean():.0f} %', f'**{est(st, op, yr, b):.0f} %** ({100*st:.0f} / {100*op:.0f})',
                      f'{int((late & (p >= HI)).sum()):,} ({100*(p[late] >= HI).mean():.0f} % of those dated later)',
                      f'{int((early & (p <= LO)).sum()):,} ({100*(p[early] <= LO).mean():.0f} % of those dated earlier)']
        lines.append('| ' + ' | '.join(cells) + ' |')
    return '\n'.join(lines)
t = pd.read_csv(ap.WORK / 'districts.csv')
t = t.drop_duplicates(subset=['district', 'borough'], keep='first')
BC = {'Brooklyn': '3', 'Queens': '4', 'The Bronx': '2', 'Staten Island': '5', 'Manhattan': '1'}
def drow(r):
    e24 = est(r['1924: photo shows standing %'] / 100, r['1924: photo shows open %'] / 100, 1924, BC[r.borough])
    e51 = est(r['1951: photo shows standing %'] / 100, r['1951: photo shows open %'] / 100, 1951, BC[r.borough])
    return (f"| {r.district} | {r.borough.replace('The ', '')} | {int(r['placeholder-year buildings']):,} | {r['1924: pipeline has standing %']:.0f} % | **{e24:.0f} %** ({r['1924: photo shows standing %']:.0f} / {r['1924: photo shows open %']:.0f}) | "
            f"{int(r['1924: dated later but standing (n)'])} | {int(r['1924: dated earlier but open (n)'])} | {r['1951: pipeline has standing %']:.0f} % | **{e51:.0f} %** ({r['1951: photo shows standing %']:.0f} / {r['1951: photo shows open %']:.0f}) | "
            f"{int(r['1951: dated later but standing (n)'])} | {int(r['1951: dated earlier but open (n)'])} |")
DH = ('| district | borough | placeholder-year buildings | pipeline: by 1924 | photo 1924: est. standing (stood / open) | dated later, standing 1924 | dated earlier, open 1924 | pipeline: by 1951 | photo 1951: est. standing (stood / open) | dated later, standing 1951 | dated earlier, open 1951 |\n'
      '|---|---|---|---|---|---|---|---|---|---|---|')
def dtable(names=None, sort=None, n=25, boro=None):
    k = t if names is None else t[t.district.isin(names)]
    if boro: k = k[k.borough.isin(boro)]
    if sort: k = k.sort_values(sort, ascending=False).head(n)
    elif names: k = k.set_index('district').loc[[x for x in names if x in set(k.district)]].reset_index()
    return DH + '\n' + '\n'.join(drow(r) for _, r in k.iterrows())
t['e24'] = [est(a / 100, b / 100, 1924, BC[c]) for a, b, c in zip(t['1924: photo shows standing %'], t['1924: photo shows open %'], t.borough)]
t['late_gap'] = t.e24 - t['1924: pipeline has standing %']
focus = ['Gravesend', 'Flatlands', 'New Utrecht', 'Jamaica', 'Flushing', 'Canarsie', 'Sheepshead Bay', 'Coney Island', 'Flatbush', 'New Lots', 'Elmhurst', 'College Point', 'Whitestone', 'Bayside', 'Far Rockaway']
si = ['Stapleton', 'St. George', 'Tompkinsville', 'New Brighton', 'West New Brighton', 'Port Richmond', 'Mariners Harbor', 'Factoryville', 'Clifton', 'Rosebank', 'Tottenville', 'Richmondtown', 'New Dorp', 'Great Kills', 'Travis']
bx = ['Mott Haven', 'The Hub', 'Melrose', 'Morrisania', 'Tremont', 'West Farms', 'Fordham', 'Kingsbridge', 'Westchester Square', 'Unionport', 'Van Nest', 'Williamsbridge', 'Wakefield', 'Eastchester', 'City Island', 'Hunts Point', 'Pelham Bay']
g = d[d.heap & (d.area >= 40)]
gr = g[np.hypot((g.lon - (-73.9737)) * 84400, (g.lat - 40.5953) * 110574) <= 600]
def cross(k, yr):
    p = k[f'p{yr}']; ok = p.notna()
    return f"{int(ok.sum()):,} with a photograph: {100*(p[ok]>=HI).mean():.0f} % standing, {100*(p[ok]<=LO).mean():.0f} % open ground, {100*((p[ok]>LO)&(p[ok]<HI)).mean():.0f} % unclear"
gy = gr.raw_year.value_counts().head(8)
gtab = '\n'.join(f"| {int(yv)} | {n} | {100*(gr.p1924[gr.raw_year==yv]>=HI).mean():.0f} % | {100*(gr.p1924[gr.raw_year==yv]<=LO).mean():.0f} % | {est((gr.p1924[gr.raw_year==yv]>=HI).mean(), (gr.p1924[gr.raw_year==yv]<=LO).mean(), 1924, '3'):.0f} % | {100*(gr.y[gr.raw_year==yv]<=1924).mean():.0f} % |" for yv, n in sorted(gy.items()))
late_top = t[(t['placeholder-year buildings'] >= 500) & ~t.borough.isin(['Staten Island'])].sort_values('late_gap', ascending=False).head(22)
early_top = t[(t['placeholder-year buildings'] >= 500) & ~t.borough.isin(['Staten Island'])].sort_values('late_gap').head(18)
ref_lines = '\n'.join(f"- {yr}: " + '; '.join(f"{nm} {100*REF[(yr,b)][0]:.0f} / {100*REF[(yr,b)][1]:.0f} / {100*REF[(yr,b)][2]:.0f} / {100*REF[(yr,b)][3]:.0f}" for b, nm in B) for yr in (1924, 1951))
txt = f"""# What the 1924 and 1951 aerial photographs say about the placeholder years

Source of every number here: `data/manual/aerial/presence.parquet` (method, terms and validation in
`data/manual/aerial/README.md`), joined to `data/interim/nyc_buildings.parquet` as it stood on 2026-11-10.
"Placeholder-year buildings" are the footprints whose `year_src` starts with `heap` (the assessor's rounded
years, which the pipeline spreads over a range and marks `estimated`).

How to read the tables. For every footprint the photograph gives a probability that a building stood on the
outline. **stood** = share with p >= {HI}, **open** = share with p <= {LO}; the rest is unclear. Against 220
hand-checked footprints a "stood" call was right in 94 % (1924) and 96 % (1951) of cases and an "open" call in
92 % and 83 %, but each call finds only part of its side ({100*rate[1924][0]:.0f} % of the buildings and {100*rate[1924][3]:.0f} % of the open
ground in 1924; {100*rate[1951][0]:.0f} % and {100*rate[1951][3]:.0f} % in 1951), and how much it finds differs a great deal between
boroughs: detached houses under trees are found far less often than Brooklyn rows.

**est. standing** therefore reads each group between two reference groups of the same borough's own
placeholder-year stock: the "by 1899 / 1900 / 1901" buildings, which all stood in both photographs, and
the "1955 and later" ones (for 1951: "1960 and later"), which did not yet. With a, e = the stood and open
shares of the first group and b, c = those of the second, it is the mean of (stood - b) / (a - b) and
(c - open) / (c - e), cut to 0-100 %. The reference shares (a / e / b / c, in %):

{ref_lines}

It is an estimate, good to about +-10 points (more on Staten Island, where a is only a fifth). The late
reference group includes outlines on which an earlier building stood, so the estimate is, if anything, low.
A building "standing" in a photograph means a building stood on today's
outline - in districts that were already built up it may have been an earlier building on the same lot.

## 1. The placeholder years, by borough

Share of the buildings with each placeholder year that already stood in **1924**: **est. standing** (stood % /
open %; number of buildings with a photograph).

{heap_table(1924)}

The same for **1951**:

{heap_table(1951)}

What this says:

- **The placeholders are in the right order but run late.** Of Brooklyn's "1925" and "1930" buildings
  nearly half already stood in 1924; in Queens and the Bronx between a quarter and a third; of "1935" a fifth
  in Brooklyn and next to none elsewhere; "1940" and later came after the photograph.
- **"1931" is not a year at all.** In every borough the "1931" buildings are as old as the "1905-1915" ones
  (Brooklyn: 58 % plainly standing in 1924 and 11 % plainly open, against 33 % / 34 % for "1930"). It should be
  read as "by 1931" - a bound like 1899 / 1901 - not as "about 1931".
- **"1920" is not "by 1920"**: about two thirds of Brooklyn's "1920" buildings stood in 1924, somewhat over
  half of Queens' and under half of the Bronx's; the rest came after the photograph.
- **"1905", "1910", "1915" hold** in Brooklyn and Queens (85-100 %); in the Bronx about three in ten of "1915"
  came after 1924.
- **By 1951 nearly everything up to "1940" stood** (75-100 %). **"1945" and "1950" straddle the photograph**:
  of "1945" about seven in ten stood in Brooklyn and Queens and a quarter in the Bronx; of "1950" about half
  in Brooklyn, a third in Queens, a sixth in the Bronx. "1955" and later came after it.
- The late placeholders in old districts ("1970", "1975", "1980" in Brooklyn and Queens: 15-57 % "standing" in
  1924) are buildings on lots that were built on before: an earlier building, or an old one given a new year.
- Staten Island's column is the weakest: the classifier recognises only a fifth of its certainly old
  buildings, so its estimates rest on a narrow scale (read them to +-25 points).
- Manhattan: nearly everything stood in both photographs; they cannot order its placeholder years
  (a building stood on almost every outline, often not today's).

## 2. Boroughs: the pipeline's dates against the photographs

{boro_table()}

In Brooklyn the pipeline has 47 % of the placeholder-year buildings standing by 1924; the photograph puts
it near 60 %. In Queens and the Bronx the totals agree, but one building in eight dated after 1924 plainly
stands in the photograph and a quarter of those dated before it plainly stand on open ground: the totals are
right and the order inside the districts is not. Staten Island may have more standing than the pipeline says
(weak evidence). For 1951 the pipeline has more standing than the photograph in Queens and the Bronx (83 %
against about 75 %, 79 % against about 67 %): the "1945" and "1950" placeholders spread backwards.

## 3. Districts

600 m around the label of each place in `data/tables/places.csv` (the label is the old village or the
neighbourhood centre, so the window is a sample of the district, not all of it).

### Gravesend

Around the village centre (-73.9737, 40.5953): {len(gr):,} placeholder-year buildings.
1924: {cross(gr, 1924)}. 1951: {cross(gr, 1951)}. The pipeline has {100*(gr.y<=1924).mean():.0f} % of them standing by 1924 and
{100*(gr.y<=1951).mean():.0f} % by 1951; the photographs give about {est((gr.p1924.dropna()>=HI).mean(), (gr.p1924.dropna()<=LO).mean(), 1924, '3'):.0f} % and {est((gr.p1951.dropna()>=HI).mean(), (gr.p1951.dropna()<=LO).mean(), 1951, '3'):.0f} %.

| placeholder | buildings | stood 1924 | open 1924 | est. standing 1924 | pipeline: by 1924 |
|---|---|---|---|---|---|
{gtab}

The totals are not far apart (27 % against about a third by 1924); what is wrong is *which* buildings. The
pipeline has every "1920" building standing by 1924 - the photograph shows about two in five - and none of the
"1930", "1931" and "1935" ones, of which about 18 %, 57 % and 20 % stood. The old village's houses carry
"1931" and "1930" like the new streets around them and so appear in the 1930s, which is what the owner saw:
351 buildings dated after 1924 plainly stand in the 1924 photograph, and 197 dated before it plainly stand on
open ground.

### The districts the brief named, and their like

{dtable(focus)}

### The old Staten Island villages

{dtable(si)}

On Staten Island the "open" call is not safe (see the caveats: one certainly old house in four or five is
called open there, and only a fifth to a third is recognised), and the estimates stand on a narrow scale.
The north-shore villages (Stapleton, St. George, Port Richmond) show as standing; the "dated earlier, open"
counts for New Brighton, Tompkinsville, Mariners Harbor or Westerleigh are in good part houses under trees
that the classifier misses, not evidence against the pipeline.

### The old Bronx villages

{dtable(bx)}

### Dated clearly too late (photograph of 1924 well ahead of the pipeline; Staten Island left out)

Districts with at least 500 placeholder-year buildings, by the gap between the photograph's estimate and
the pipeline's share standing by 1924.

{dtable(list(late_top.district), None)}

### Dated clearly too early (pipeline well ahead of the 1924 photograph; Staten Island left out)

{dtable(list(early_top.district), None)}

These are the districts of the 1920s and 1930s on the outer plains and shores: the 1924 photograph shows
fields, marsh or bare sand where the pipeline already has a quarter to a half of the houses.

## 4. Caveats that matter for using this

- **Open country and leafy villages**: where less than 15 % of the ground within 50 m is built today, a
  third of the buildings known to be older than the photograph get p <= {LO}, and only a fifth get p >= {HI}
  (isolated houses under trees are not resolved at 2 m). There, and on Staten Island generally, "open" is
  weak evidence; "stood" stays good.
- **Built-up districts**: "stood" is evidence about the outline, not about today's building. Of the
  buildings with a *recorded* year 3 to 8 years after the 1924 photograph, 43 % show a building on the outline
  in it (46 % for the Landmarks Commission's dates, which are researched): replacements, and assessor years
  that are themselves late. The photograph is dated right: Yankee Stadium (1923) stands in it, the Bronx
  County Courthouse site (1931-34) is open ground, the old Waldorf-Astoria (demolished 1929) stands where the
  Empire State Building is.
- The white gutters between the sheets of the 1924 mosaic, the Rockaway and Great Kills gaps of the 1951
  mosaic and water edges carry no evidence (2.1 % and 1.4 % of the footprints).
- The hand check is 220 footprints, 44 per borough, read off thumbnails of the mosaics by the agent that
  built this (not by a person, and not on a large screen), with 12 % (1924) and 20 % (1951) left as unclear.
- Nothing here was compared with a second source (a Sanborn or Bromley sheet of the 1920s would do for a
  few blocks of Gravesend).
"""
open('/home/user/nyc/data/research/aerial_years.md', 'w').write(txt)
print(len(txt), 'chars')
