"""Write data/tables/landmarks_towers.csv, data/research/landmarks_towers.md and the report table
from the built models (mesh.json), the numeric check (check_results.json) and the notes."""
import csv
import json
import math
from pathlib import Path

import notes_b  # noqa: F401  (fills N)
import notes_c  # noqa: F401
from notes_a import N

HERE = Path(__file__).parent
ROOT = Path('/home/user/nyc')
lms = json.loads((HERE / 'mesh.json').read_text())
res = {r['id']: r for r in json.loads((HERE / 'check_results.json').read_text())}
CT = dict(empire_state_building=261, empire_state_antenna=261, chrysler_building=422, one_world_trade_center=98, woolworth_building=969, flatiron_building=9014,
          rockefeller_30=775, wtc_7=1117, wtc_3=273, wtc_4=545, metlife_tower=1383, wall_40=619, pine_70=18405, citigroup_center=648, park_432=13227,
          one_vanderbilt=15833, central_park_tower=14269, west_57th_111=14320, hudson_yards_30=13325, hudson_yards_10=13326, bank_of_america_tower=291,
          new_york_times_building=423, spruce_8=699, hearst_tower=2245, leonard_56=844, un_secretariat=3737, lever_house=9068, seagram_building=3529,
          rockefeller_international_building=3602, rockefeller_plaza_1=9810, rockefeller_1270_sixth=11606, rockefeller_plaza_10=17518, rockefeller_plaza_50=11618,
          metlife_building=909, municipal_building=2471, park_row_building=9142, new_york_life_building=2060, williamsburgh_savings_bank_tower=3598, one_court_square=1651)
ctb = {d['id']: d for d in json.loads((ROOT / 'data/raw/landmarks_towers/misc/ctbuh_nyc.json').read_text())}
for lid, cid in CT.items():
    d = ctb[cid]
    f = lambda k: (f"{float(d[k]):g} m" if d.get(k) not in (None, '') else '—')
    N[lid]['cited'].append(f"CTBUH Skyscraper Center (\"{d['name_intl']}\", id {cid}): architectural {f('height_architecture')}, tip {f('height_tip')}, roof {f('height_roof')}, "
                           f"highest occupied floor {f('height_floor')}, observatory {f('height_observatory')}; floors {d.get('floors_above')}; start {d.get('start') or '—'}, completed {d.get('completed') or '—'}")
    N[lid]['src'].append('https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table)')
missing = [l['id'] for l in lms if l['id'] not in N]
assert not missing, missing

with (ROOT / 'data/tables/landmarks_towers.csv').open('w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['id', 'name', 'kind', 'start_year', 'end_year', 'lat', 'lon', 'height_m', 'year_source_url', 'notes'])
    for l in lms:
        n = N[l['id']]
        w.writerow([l['id'], l['name'], l['kind'], math.floor(l['built'][0]), l['end'], l['anchor'][1], l['anchor'][0], n['h'], n['url'], n['csv']])


def check_line(r):
    if r.get('rider'):
        return f"top {r['top']} m (cited {r['cited']} m); no footprint of its own — checked together with the model it stands on"
    how = 'plan projection' if r['how'] == 'projection' else 'wall outline at 0.6 m'
    extra = f" (with {', '.join(r['with'])})" if r.get('with') else ''
    return (f"top {r['top']} m vs cited {r['cited']} m ({r['top'] - r['cited']:+.1f}); {how}{extra} {r['model']} m² vs official {r['official']} m² "
            f"({r['pct']:+.1f} %), centroid offset {r['d']} m, IoU {r['iou']}; city-measured roof {r['roof']} m; hides BIN {', '.join(r['hides'])}")


md = []
md.append('''# Skyscraper landmarks — dimensions, sources, estimates and checks

Research notes for `viewer/src/landmarks/nyc-towers.ts` (`TOWERS`) and `data/tables/landmarks_towers.csv`:
%d landmark models of the towers that stand today. Written by the towers agent; regenerate with
`data/interim/landmarks_towers/make_docs.py` after `check.py` (both scratch tools, not part of the pipeline).

## How the models are made

- **Frame.** Each model is drawn in the building's own frame: origin = centroid of the city's official
  footprint, +v along the bearing `B` of the footprint's long edge, +u 90° clockwise. Manhattan's grid gives
  B ≈ 29°. Anchor, B and the outline are generated from the footprint, never typed by hand.
- **Plan.** The ground-level outline is the official footprint itself (NYC building footprints, the
  `data/interim/nyc_footprints_raw.parquet` extract). `replaces` is that outline grown 1 m, so the generic
  extrusion of exactly that footprint is hidden; where a tall neighbour's centroid lies within ~12 m (the
  viewer hides footprints over 60 m that close to an outline) the outline is shrunk or redrawn instead — noted per building.
- **Set-backs.** Where OpenStreetMap volunteers mapped 3D building parts (Overture 2026-10-21.0
  `building_part`), the union of the parts standing at each height is the measured massing: outline and
  level heights are generated into the `M` block of the TypeScript file (`gen_massing.py`). Levels thinner
  than 3 m are merged into the level below; outlines are simplified to under 1 m.
- **Totals and crowns.** Roof, spire and crown dimensions come from the cited sources below and override
  the OSM numbers where both exist (the stack's top is raised or cut to the cited height).
- **Estimates.** Everything not covered by a source is listed under "Estimated" and repeated in the model's
  `Model:` fact in the click popup.

## Sources and licences

| Source | Used for | Licence |
|---|---|---|
| NYC Open Data, Building Footprints (https://data.cityofnewyork.us/City-Government/BUILDING/5zhs-2jue) | anchor, bearing, plan, `replaces`, measured roof height for comparison | public data, NYC Open Data terms of use |
| OpenStreetMap building parts via Overture Maps 2026-10-21.0 (https://www.openstreetmap.org/copyright) | set-back levels and their outlines | © OpenStreetMap contributors, ODbL 1.0 |
| Wikipedia articles (URL per building; wikitext fetched 2026-11-10 with `?action=raw`, cached under `data/raw/landmarks_towers/wp_full/`) | heights, dates, cited dimensions | CC BY-SA 4.0 (facts only) |
| NYC Landmarks Preservation Commission designation reports (`https://s-media.nyc.gov/agencies/lpc/lp/NNNN.pdf`, text extracted with pdftotext, cached under `data/raw/landmarks_towers/lpc/`) | set-back storeys, tower dimensions, crown descriptions | NYC government publications |
| CTBUH Skyscraper Center, New York City page (https://www.skyscrapercenter.com/city/new-york-city; the page embeds a table of 1,952 buildings, cached as `data/raw/landmarks_towers/misc/ctbuh_nyc.json`) and the building pages of the Empire State Building and One WTC | architectural, roof and occupied heights, start and completion years — the cross-check line under each building | © CTBUH; individual facts quoted with attribution |

Quotations in the notes are from the cached texts. LPC text is OCR; numbers quoted from it were read in context.

## How the models are checked

`data/interim/landmarks_towers/check.py` bundles the TypeScript with esbuild, builds every mesh and compares:

1. **Plan** — the model's wall outline cut at z = 0.6 m (or, for buildings on stilts or with cantilevers,
   the plan projection of the whole model) against the union of the official footprints the viewer will
   hide for it (same rule as `index.ts replacedMask`, including the tall-sliver rule). Target: area within 5 %,
   centroid within 3 m.
2. **Height** — the model's highest vertex against the cited height in the CSV.
3. **Set-backs** — the plan area of everything above the middle of each OSM level against the union of the
   OSM parts at that level. Differences come from cited dimensions overriding OSM, clipping to the official
   outline, sloped OSM roofs (which the area test treats as flat) and cantilevers above.

All %d models pass 1 and 2. Results below were produced on 2026-11-10.

## Summary

| id | cited m | model m | official m² | model m² | Δ area | centroid m | built |
|---|---|---|---|---|---|---|---|'''.replace('%d', str(len(lms))))
for l in lms:
    r = res[l['id']]
    if r.get('rider'):
        md.append(f"| {l['id']} | {r['cited']} | {r['top']} | — | — | — | — | {l['built'][0]}–{l['built'][1]} |")
    else:
        md.append(f"| {l['id']} | {r['cited']} | {r['top']} | {r['official']} | {r['model']} | {r['pct']:+.1f} % | {r['d']} | {l['built'][0]}–{l['built'][1]} |")
md.append('\n## Buildings\n')
rep = ['| building | cited height m | model m | official footprint m² | model m² | estimated |', '|---|---|---|---|---|---|']
for l in lms:
    n = N[l['id']]
    r = res[l['id']]
    md.append(f"### {l['name']} (`{l['id']}`)\n")
    md.append(f"- **Anchor** [{l['anchor'][0]}, {l['anchor'][1]}]; **built** {l['built'][0]} – {l['built'][1]}; **kind** {l['kind']}.")
    md.append('- **Sources:** ' + '; '.join(n['src']) + '.')
    md.append('- **Cited dimensions and dates:**')
    md += [f'  - {c}' for c in n['cited']]
    md.append('- **Measured (footprint / OSM parts):**')
    md += [f'  - {c}' for c in n['measured']]
    md.append('- **Estimated or simplified:**')
    md += [f'  - {c}' for c in n['estimated']]
    md.append('- **Check:** ' + check_line(r) + '.')
    if r.get('levels'):
        md.append('- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): ' + '; '.join(x.replace(': osm ', ' m: ').replace(' / model ', ' / ') for x in r['levels']) + '.')
    md.append('')
    if r.get('rider'):
        rep.append(f"| {l['name']} | {r['cited']} | {r['top']} | (on host) | — | {n['est']} |")
    else:
        rep.append(f"| {l['name']} | {r['cited']} | {r['top']} | {r['official']} | {r['model']} ({r['pct']:+.1f} %) | {n['est']} |")
md.append('''## Known weak spots

- **OSM levels are volunteers' numbers.** They were not checked against drawings. Where a source allowed
  a cross-check it is noted (Empire State: floors and heights agree; Woolworth: 170 m vs 174 m derived;
  3 WTC: OSM's own top is 23 m too high; 4 WTC: plan areas ~20 % under the cited floor areas, but the 220 m
  break agrees with CTBUH's 218 m deck; Park Row and Met Life Tower roofs agree with CTBUH within 0.5 m).
- **Stepped where the building tapers or slopes:** One Vanderbilt, 30 and 10 Hudson Yards, Bank of America
  Tower (facets as steps), the UN General Assembly roof.
- **Schematic models:** 56 Leonard Street (only outline and height are real), Vessel (shells instead of
  stairs), Steinway Hall (wings placed from the LPC description, not from a plan), St Peter's Church at
  Citigroup Center, the Shops at Hudson Yards (height estimated).
- **Composite footprints.** The city gives one footprint for 30 Hudson Yards + the Shops, 432 Park Avenue + its
  retail buildings, Citigroup Center + church + wing, Steinway Hall + 111 West 57th, the UN General Assembly +
  Conference Building + terraces, the Empire State Building + a 23.8 m annex. The model has to draw all of it,
  because `replaces` hides the whole footprint.
- **Dates.** `built` uses the cited construction start (or ground-breaking) and opening; where only years are
  cited the decimal part is a guess and is listed under "Estimated". 30 Rockefeller Plaza's 1931 start
  year is CTBUH's (steel: March 1932, Wikipedia).
- **Not modelled:** 1230 Avenue of the Americas at Rockefeller Center (its footprint includes the 1955 wing on
  the Center Theatre's site, so one model would be wrong before 1955; the generic layer has it), the Chrysler's
  triangular crown windows and 24th-floor pineapples, Hearst Tower's chamfered corners, 8 Spruce Street's
  rippled skin, the Municipal Building's central arch.
- **Not consulted:** architects' drawings; the LPC Rockefeller Center report was downloaded but not mined.
- **Where sources disagree** the notes say which was used: Flatiron 86.9 / 93.6 m, Seagram 515 / 516 ft,
  4 WTC 977 / 978 ft, UN Secretariat 505 ft / 154.3 m, One Vanderbilt roof 396.5 / 392.6 m, 432 Park Avenue
  425.5 / 425.7 m, completion years of 111 West 57th (2021 / 2022), 56 Leonard (2016 / 2017), One Court Square
  (1989 / 1990).
''')
(ROOT / 'data/research').mkdir(exist_ok=True)
(ROOT / 'data/research/landmarks_towers.md').write_text('\n'.join(md))
(HERE / 'report_table.md').write_text('\n'.join(rep))
print('csv rows', len(lms), '; md lines', len(md))
