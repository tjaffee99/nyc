# Skyscraper landmarks — dimensions, sources, estimates and checks

Research notes for `viewer/src/landmarks/nyc-towers.ts` (`TOWERS`) and `data/tables/landmarks_towers.csv`:
46 landmark models of the towers that stand today. Written by the towers agent; regenerate with
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

All 46 models pass 1 and 2. Results below were produced on 2026-11-10.

## Summary

| id | cited m | model m | official m² | model m² | Δ area | centroid m | built |
|---|---|---|---|---|---|---|---|
| empire_state_building | 381.0 | 381.0 | 7898 | 7903 | +0.1 % | 0.0 | 1930.21–1931.33 |
| empire_state_antenna | 443.2 | 443.2 | — | — | — | — | 1950.57–1953 |
| chrysler_building | 318.9 | 318.9 | 3393 | 3395 | +0.1 % | 0.0 | 1928.87–1930.4 |
| one_world_trade_center | 541.3 | 541.3 | 3836 | 3838 | +0.0 % | 0.0 | 2006.32–2014.84 |
| woolworth_building | 241.4 | 241.4 | 2224 | 2226 | +0.1 % | 0.0 | 1910.84–1913.31 |
| flatiron_building | 93.6 | 93.6 | 1019 | 1014 | -0.6 % | 0.0 | 1901.45–1902.75 |
| rockefeller_30 | 259.1 | 259.1 | 9137 | 9140 | +0.0 % | 0.0 | 1931.6–1933.35 |
| rockefeller_international_building | 156.1 | 156.1 | 5075 | 5076 | +0.0 % | 0.0 | 1933.5–1935.33 |
| rockefeller_plaza_1 | 149.0 | 149.0 | 1625 | 1624 | -0.1 % | 0.0 | 1936.5–1937.9 |
| rockefeller_1270_sixth | 124.7 | 124.7 | 2297 | 2295 | -0.1 % | 0.0 | 1931.7–1932.9 |
| rockefeller_plaza_10 | 69.5 | 69.5 | 5447 | 5448 | +0.0 % | 0.0 | 1939.5–1940.9 |
| rockefeller_plaza_50 | 69.5 | 69.5 | 3324 | 3325 | +0.0 % | 0.0 | 1937.5–1938.9 |
| rockefeller_british_empire_building | 38.4 | 38.4 | 1261 | 1260 | -0.1 % | 0.0 | 1932.3–1933.5 |
| rockefeller_maison_francaise | 38.4 | 38.4 | 1255 | 1257 | +0.2 % | 0.0 | 1932.3–1933.5 |
| radio_city_music_hall | 35.0 | 35.0 | 4270 | 4270 | +0.0 % | 0.0 | 1931.9–1932.99 |
| wtc_7 | 226.5 | 226.5 | 3002 | 3002 | +0.0 % | 0.0 | 2002.35–2006.39 |
| wtc_3 | 328.9 | 328.9 | 5262 | 5288 | +0.5 % | 0.2 | 2008.05–2018.44 |
| wtc_4 | 297.7 | 297.7 | 4547 | 4545 | -0.0 % | 0.0 | 2008.05–2013.87 |
| metlife_tower | 213.4 | 213.4 | 564 | 563 | -0.1 % | 0.0 | 1907–1909.5 |
| wall_40 | 282.5 | 282.5 | 3011 | 3007 | -0.1 % | 0.0 | 1929.35–1930.33 |
| pine_70 | 290.2 | 290.2 | 2910 | 2909 | -0.1 % | 0.0 | 1930.37–1932.37 |
| citigroup_center | 278.9 | 278.9 | 5686 | 5677 | -0.2 % | 0.2 | 1974.3–1977.8 |
| park_432 | 425.5 | 425.5 | 3186 | 3235 | +1.5 % | 0.1 | 2012.1–2015.98 |
| one_vanderbilt | 427.0 | 427.0 | 4001 | 3998 | -0.1 % | 0.0 | 2016.8–2020.7 |
| central_park_tower | 472.4 | 472.4 | 3891 | 4005 | +2.9 % | 0.6 | 2014.37–2020.9 |
| steinway_hall | 67.0 | 67.0 | 1855 | 1829 | -1.4 % | 0.5 | 1924.5–1925.82 |
| west_57th_111 | 435.3 | 435.3 | — | — | — | — | 2014.5–2021.9 |
| hudson_yards_30 | 387.1 | 387.1 | 17990 | 18046 | +0.3 % | 0.3 | 2014.5–2019.2 |
| hudson_yards_10 | 267.6 | 267.6 | 4103 | 4102 | -0.0 % | 0.0 | 2012.92–2016.41 |
| vessel | 45.7 | 45.7 | 1644 | 1566 | -4.7 % | 0.0 | 2017.3–2019.2 |
| bank_of_america_tower | 365.8 | 365.8 | 7858 | 7856 | -0.0 % | 0.0 | 2004.58–2009.33 |
| new_york_times_building | 318.8 | 318.8 | 6583 | 6581 | -0.0 % | 0.0 | 2004.8–2007.88 |
| spruce_8 | 265.2 | 265.2 | 2880 | 2880 | +0.0 % | 0.0 | 2006.5–2011.1 |
| hearst_magazine_building | 30.0 | 30.0 | 3521 | 3524 | +0.1 % | 0.0 | 1927.45–1928.5 |
| hearst_tower | 182.0 | 182.0 | — | — | — | — | 2003.33–2006.75 |
| leonard_56 | 250.2 | 250.2 | 1418 | 1416 | -0.1 % | 0.0 | 2012.8–2016.9 |
| un_secretariat | 153.9 | 153.9 | 1805 | 1810 | +0.3 % | 0.0 | 1948.7–1951.45 |
| un_general_assembly | 32.0 | 32.0 | 18841 | 19091 | +1.3 % | 0.5 | 1950.1–1952.78 |
| lever_house | 93.6 | 93.6 | 2835 | 2857 | +0.8 % | 0.0 | 1950.5–1952.33 |
| seagram_building | 157.0 | 157.0 | 2892 | 2894 | +0.1 % | 0.0 | 1955.7–1958.39 |
| metlife_building | 246.3 | 246.3 | 10016 | 10011 | -0.0 % | 0.0 | 1960.9–1963.18 |
| municipal_building | 176.8 | 176.8 | 4335 | 4333 | -0.1 % | 0.0 | 1909.54–1914.5 |
| park_row_building | 119.2 | 119.2 | 1246 | 1245 | -0.0 % | 0.0 | 1896.8–1899.55 |
| new_york_life_building | 187.5 | 187.5 | 7427 | 7419 | -0.1 % | 0.0 | 1926.5–1928.95 |
| williamsburgh_savings_bank_tower | 156.0 | 156.0 | 1649 | 1648 | -0.0 % | 0.0 | 1927.5–1929.25 |
| one_court_square | 205.1 | 205.1 | 2418 | 2418 | -0.0 % | 0.0 | 1987–1990 |

## Buildings

### Empire State Building (`empire_state_building`)

- **Anchor** [-73.985705, 40.748453]; **built** 1930.21 – 1931.33; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/Empire_State_Building; https://s-media.nyc.gov/agencies/lpc/lp/2000.pdf (LP-2000, 1981); city footprint BIN 1015862; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - roof 1,250 ft (381.0 m), tip 1,454 ft (443.2 m), top floor 1,224 ft (373.1 m) — Wikipedia infobox; LPC: "1250-foot high"
  - 86th-floor deck at 1,050 ft (320 m) — Wikipedia
  - five-storey base on the whole lot; set-backs at the 21st, 25th, 30th, 72nd, 81st and 85th storeys; "symmetrical massing" — Wikipedia
  - tower nine bays wide from the 6th to the 25th floor, seven to the 72nd, six to the 81st, five to the mast — LPC
  - mooring mast: a 158 ft (48 m) steel shaft above the 86th floor — Wikipedia (→ 320 + 48 = 368 m, drum to the 373.1 m top floor, cap to the 381.0 m roof)
  - lot 425 × 200 ft — Wikipedia (official footprint: 128.3 × 58.1 m)
  - construction started 17 Mar 1930; opened 1 May 1931 — Wikipedia
  - CTBUH Skyscraper Center ("Empire State Building", id 261): architectural 381 m, tip 443.23 m, roof 381 m, highest occupied floor 373.08 m, observatory 373.08 m; floors 102; start 1930, completed 1931
- **Measured (footprint / OSM parts):**
  - OSM part tops 17 m (5 floors), 75 (20), 90 (24), 115 (29), 255 (71), 290 (80), 310, 320 and 330 m, with the plan of each level (H-plan recesses of the shaft included)
  - the OSM tower parts are drawn 2.6 m south of the lot axis; because the building is symmetrical they are moved 2.6 m north onto the axis of the official footprint (centre u 4.2, v 0.85)
  - the official footprint carries a 453 m² annex west of the lot on 33rd St; its height, 23.8 m, is that of the unnamed OSM/Overture building at that spot
- **Estimated or simplified:**
  - mast diameter (13.2 m at its foot is the OSM part; the taper to 11.8 m is estimated), the 102nd-floor drum (radius 4.6–5 m), the four buttresses and their tops (343 and 352 m)
  - the dark window bands in the shaft recesses are decoration
- **Check:** top 381.0 m vs cited 381.0 m (+0.0); wall outline at 0.6 m (with empire_state_antenna) 7903 m² vs official 7898 m² (+0.1 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 377.6 m; hides BIN 1015862.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-17 m: 7658 / 7905; 17-75 m: 4251 / 4254; 75-90 m: 3260 / 3264; 90-115 m: 2627 / 2629; 115-255 m: 2060 / 2064; 255-290 m: 1729 / 1731; 290-310 m: 1284 / 1283; 310-320 m: 1142 / 1144; 320-330 m: 764 / 780; 330-390 m: 142 / 112; 390-443 m: 55 / 3.

### Empire State Building antenna (`empire_state_antenna`)

- **Anchor** [-73.985705, 40.748453]; **built** 1950.57 – 1953; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/Empire_State_Building; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - construction of the broadcast tower began 27 Jul 1950; "the 200-foot (60 m) broadcast tower was completed in 1953" — Wikipedia
  - today's pinnacle: 203 ft (61.9 m) in the text, 204 ft in the infobox; tip 1,454 ft (443.2 m) — Wikipedia
  - CTBUH Skyscraper Center ("Empire State Building", id 261): architectural 381 m, tip 443.23 m, roof 381 m, highest occupied floor 373.08 m, observatory 373.08 m; floors 102; start 1930, completed 1931
- **Measured (footprint / OSM parts):**
  - rides on the Empire State Building model (same anchor, no `replaces`)
- **Estimated or simplified:**
  - simplification: one model, 381 → 443.2 m, for 1950 to today (the first tower differed slightly in height)
  - lattice widths (3.4 m at the foot, 0.5 m at the tip) and the three platforms
- **Check:** top 443.2 m (cited 443.2 m); no footprint of its own — checked together with the model it stands on.

### Chrysler Building (`chrysler_building`)

- **Anchor** [-73.975366, 40.751644]; **built** 1928.87 – 1930.4; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/Chrysler_Building; https://s-media.nyc.gov/agencies/lpc/lp/0992.pdf (LP-0992, 1978); city footprint BIN 1036156; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - roof 925 ft (282 m), top floor 899 ft, spire 1,046 ft (318.9 m) — Wikipedia infobox; LPC: 1046 feet
  - the needle: 185 ft long, 8 ft square at its base — Wikipedia (Architectural Forum 1930); LPC: "185-foot spire"
  - trapezoid lot: 201 ft on Lexington, 167 ft on 42nd St, 205 ft on 43rd St — Wikipedia (official footprint: 60.5 / 50.5 / 61.6 m)
  - "Above the fourth story, the building is penetrated on the east and west sides by light courts extending to the face of the tower, while on the north and south the structure gradually rises in a series of setbacks" — LPC
  - set-backs at storeys 16, 18, 23, 28 and 31; none between the 31st and 60th — Wikipedia; LPC: first set-back at the 16th storey, the fourth "to the thirty-first story marks the emergence of the tower shaft"
  - radiator caps at the 31st-floor corners "spanning about 15 feet" — LPC; eagles at the 61st floor — Wikipedia
  - Maltese-cross plan above the 60th floor; the crown "a cruciform groin vault" of seven concentric members in Nirosta steel — Wikipedia
  - excavation mid-Nov 1928 to mid-Jan 1929; first steel 27 Mar 1929; opened 27 May 1930 — Wikipedia
  - CTBUH Skyscraper Center ("Chrysler Building", id 422): architectural 318.9 m, tip 318.9 m, roof 281.94 m, highest occupied floor 252.3 m, observatory 238.7 m; floors 77; start 1928, completed 1930
- **Measured (footprint / OSM parts):**
  - OSM part tops: base 15 m, set-backs 50, 70, 80, 90 m; shaft 28.7 × 34.9 m to 199 m (61st floor), corners chamfered above 185 m
  - cross arms 13–16 m wide to 224 m; crown tier tops 235, 242, 249, 256, 262, 267, 272 m with widths 22.2, 20.5, 17.3, 13.9, 9.9, 8.1, 5.9 m and a 7 m arch rise (OSM roof heights)
  - the OSM parts overhang the official outline by 2–3 m to the south: they are shifted onto the official centroid and clipped to the official outline
- **Estimated or simplified:**
  - arches drawn as half-ellipses, each tier a cross of two barrel vaults; the number of triangular windows per arch (7, 5 or 3) is schematic
  - spire base tapering from 5.2 m at 270 m to the cited 8 ft at the 282 m roof
  - eagle length 3.2 m, radiator-cap ornaments, 5 m black granite ground storey
- **Check:** top 318.9 m vs cited 318.9 m (+0.0); wall outline at 0.6 m 3395 m² vs official 3393 m² (+0.1 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 288.6 m; hides BIN 1036156.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-15 m: 3623 / 3465; 15-50 m: 2889 / 2794; 50-70 m: 1985 / 2000; 70-80 m: 1638 / 1652; 80-89 m: 1120 / 1169; 91-185 m: 996 / 1024; 186-198 m: 866 / 901; 200-224 m: 685 / 686; 224-227 m: 685 / 493; 229-235 m: 488 / 481; 235-242 m: 488 / 410; 242-249 m: 488 / 292; 249-256 m: 488 / 189; 256-262 m: 488 / 97; 262-267 m: 488 / 65; 267-272 m: 488 / 35; 272-282 m: 488 / 13; 282-319 m: 1 / 1.

### One World Trade Center (`one_world_trade_center`)

- **Anchor** [-74.013174, 40.713009]; **built** 2006.32 – 2014.84; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/One_World_Trade_Center; https://www.skyscrapercenter.com/building/one-world-trade-center/98 (CTBUH; listed, figures taken from Wikipedia); city footprint BIN 1088469; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - roof 1,368 ft (417.0 m); glass parapet 33 ft 4 in (10.16 m); architectural height 1,776 ft (541.3 m); spire 407.9 ft (124.3 m) — Wikipedia
  - 200 ft (61 m) square footprint; windowless base 185 ft (56 m) covering floors 1–19; from the 20th floor the edges are chamfered into eight isosceles triangles, a perfect octagon near the middle, a parapet square turned 45° at the top — Wikipedia
  - construction began 27 Apr 2006; spire complete 10 May 2013; opened 3 Nov 2014 — Wikipedia
  - CTBUH Skyscraper Center ("One World Trade Center", id 98): architectural 541.3 m, tip 546.2 m, roof 416.97 m, highest occupied floor 386.5 m, observatory 386.5 m; floors 94; start 2006, completed 2014
- **Measured (footprint / OSM parts):**
  - base square from the official footprint: 62.1 × 62.3 m (3,836 m²)
  - communications ring radius 17.7 m at 417–420 m — OSM part
- **Estimated or simplified:**
  - the top square is taken with its corners over the mid-points of the base edges (side 44.0 m = 144 ft), which makes the four upright triangles vertical; CTBUH describes the parapet as "a 150-foot-by-150-foot square, rotated 45 degrees from the base"
  - mast taper (radius 2.9 → 0.3 m), ring width 2.5 m, eight struts
- **Check:** top 541.3 m vs cited 541.3 m (+0.0); wall outline at 0.6 m 3838 m² vs official 3836 m² (+0.0 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 429.3 m; hides BIN 1088469.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-417 m: 4222 / 3496; 417-420 m: 996 / 275; 420-541 m: 26 / 6.

### Woolworth Building (`woolworth_building`)

- **Anchor** [-74.008315, 40.712451]; **built** 1910.84 – 1913.31; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/Woolworth_Building; https://s-media.nyc.gov/agencies/lpc/lp/1273.pdf (LP-1273, 1983); city footprint BIN 1087167; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - 792 ft (241.4 m) — Wikipedia, LPC
  - "The 30-story tower rises above a 30-story base"; the tower is "84' X 86' at its base; setbacks on all sides at the 45th floor reduce its dimensions to 69' X 71', and again at the 50th floor to 69' X 61'"; a tourelle at each corner — LPC
  - above the 53rd storey a pyramid 105 ft high, the observation gallery above the 55th floor at 730 ft — LPC (→ eave 209.4 m, gallery 222.5 m)
  - construction officially began 4 Nov 1910; opened 24 Apr 1913 — Wikipedia
  - CTBUH Skyscraper Center ("Woolworth Building", id 969): architectural 241.4 m, tip 241.4 m, roof —, highest occupied floor 221.7 m, observatory 221.7 m; floors 58; start 1910, completed 1913
- **Measured (footprint / OSM parts):**
  - U-shaped base from the official footprint (2,224 m², light court 11.8 m wide open to the west), to 120 m (OSM part top)
  - stage heights 170 and 194 m — OSM part tops (cross-check: a uniform storey between 120 m and the 209.4 m eave puts the 45th and 50th floors at 174.4 and 193.9 m)
  - the OSM "tower" parts (29.7 and 24.1 m wide) are wider than the LPC dimensions; the LPC dimensions are used
- **Estimated or simplified:**
  - 84 ft is taken east–west and 86 ft along Broadway; the tower stands flush with the Broadway front and the upper stages are centred on it
  - top stage drawn with 4.5 m chamfers (OSM draws an octagon)
  - tourelles: radius 2.3 m, tops 203 and 212 m; lantern 5.2 m across
- **Check:** top 241.4 m vs cited 241.4 m (+0.0); wall outline at 0.6 m 2226 m² vs official 2224 m² (+0.1 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 237.7 m; hides BIN 1087167.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-120 m: 2212 / 2226; 120-170 m: 849 / 671; 170-175 m: 583 / 474; 175-194 m: 560 / 474; 194-215 m: 405 / 392; 215-238 m: 335 / 22.

### Flatiron Building (`flatiron_building`)

- **Anchor** [-73.989652, 40.741016]; **built** 1901.45 – 1902.75; **kind** building.
- **Sources:** https://en.wikipedia.org/wiki/Flatiron_Building; https://s-media.nyc.gov/agencies/lpc/lp/0219.pdf (LP-0219, 1966; no dimensions); city footprint BIN 1016278; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - "it originally stood 285 ft tall"; the article now gives 307 ft (93.6 m) and 22 floors; "originally 20 floors; a cowcatcher retail space and penthouse were added shortly after the building's opening" — Wikipedia
  - completed June 1902, opened 1 Oct 1902 — Wikipedia infobox
  - CTBUH Skyscraper Center ("Flatiron Building", id 9014): architectural 93.57 m, tip 93.57 m, roof 86.87 m, highest occupied floor —, observatory —; floors 22; start —, completed 1902
- **Measured (footprint / OSM parts):**
  - triangle and prow from the official footprint (1,019 m²); the city measures the roof at 91.5 m
- **Estimated or simplified:**
  - construction start 1901.45 (the site was bought in May 1901; no start date found)
  - main roof at 86.9 m and the penthouse to 93.6 m: CTBUH gives roof 86.87 m and architectural height 93.57 m
  - base, shaft and capital levels (16, 70, 84 m), the 1.5 m cornice, the penthouse outline, the 5.5 m prow
  - simplification: penthouse and prow are drawn from 1902 although they were added a few years later
- **Check:** top 93.6 m vs cited 93.6 m (+0.0); wall outline at 0.6 m 1014 m² vs official 1019 m² (-0.6 %), centroid offset 0.0 m, IoU 0.99; city-measured roof 91.5 m; hides BIN 1016278.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-88 m: 463 / 1218.

### 30 Rockefeller Plaza (RCA Building) (`rockefeller_30`)

- **Anchor** [-73.979651, 40.759166]; **built** 1931.6 – 1933.35; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/30_Rockefeller_Plaza; https://s-media.nyc.gov/agencies/lpc/lp/1446.pdf (LP-1446, Rockefeller Center, 1985; not mined); city footprint BIN 1076262; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - roof 850 ft (259.1 m), 66 floors, completed 1933 — Wikipedia infobox
  - "work on its superstructure started in March 1932" — Wikipedia
  - CTBUH Skyscraper Center ("Comcast Building", id 775): architectural 259.08 m, tip —, roof 256 m, highest occupied floor 252.4 m, observatory 256 m; floors 70; start 1931, completed 1933
- **Measured (footprint / OSM parts):**
  - official footprint 9,137 m²: the slab, the studio wings and the 16-storey building on Sixth Avenue are one footprint
  - OSM part tops: base 10 m, wings 20 / 40 / 43 m, west building 70 m, slab steps 45 / 125 / 133 / 175 / 190 / 220 / 235 / 245 m, top stage (70.3 × 19.6 m) to 260 m — drawn to the cited 259.1 m
- **Estimated or simplified:**
  - none in the geometry; `built` starts at 1931.6: CTBUH gives the year 1931, the month is a guess
- **Check:** top 259.1 m vs cited 259.1 m (+0.0); wall outline at 0.6 m 9140 m² vs official 9137 m² (+0.0 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 254.4 m; hides BIN 1076262.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-10 m: 9016 / 9151; 10-20 m: 7443 / 7470; 20-40 m: 7026 / 7041; 40-43 m: 6593 / 6606; 43-45 m: 4038 / 6606; 45-70 m: 3983 / 3987; 70-125 m: 2796 / 2799; 125-133 m: 2728 / 2734; 133-175 m: 2680 / 2734; 175-190 m: 2596 / 2606; 190-220 m: 2553 / 2606; 220-235 m: 2455 / 2465; 235-245 m: 2367 / 2377; 245-260 m: 1347 / 1378.

### International Building (Rockefeller Center) (`rockefeller_international_building`)

- **Anchor** [-73.977617, 40.75914]; **built** 1933.5 – 1935.33; **kind** building.
- **Sources:** https://en.wikipedia.org/wiki/International_Building_(Rockefeller_Center); city footprint BIN 1083860; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - roof 512 ft (156.1 m), 41 floors, completed 1 May 1935 — Wikipedia infobox
  - CTBUH Skyscraper Center ("International Building", id 3602): architectural 156.06 m, tip 156.06 m, roof 156.06 m, highest occupied floor —, observatory —; floors 41; start 1933, completed 1935
- **Measured (footprint / OSM parts):**
  - official footprint 5,075 m²: the tower and the two six-storey wings on Fifth Avenue
  - OSM part tops 8, 17, 20, 25, 28, 35, 60, 110, 145, 156 m with their outlines
- **Estimated or simplified:**
  - `built` starts at 1933.5 (year from CTBUH)
- **Check:** top 156.1 m vs cited 156.1 m (+0.0); wall outline at 0.6 m 5076 m² vs official 5075 m² (+0.0 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 155.9 m; hides BIN 1083860.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-8 m: 5075 / 5288; 8-17 m: 4877 / 4881; 17-20 m: 4694 / 4702; 20-25 m: 4245 / 4253; 25-28 m: 2915 / 2940; 28-35 m: 2569 / 2573; 35-60 m: 2357 / 2362; 60-110 m: 2285 / 2290; 110-145 m: 2212 / 2217; 145-156 m: 1687 / 1686.

### 1 Rockefeller Plaza (Time & Life Building of 1937) (`rockefeller_plaza_1`)

- **Anchor** [-73.978904, 40.757989]; **built** 1936.5 – 1937.9; **kind** building.
- **Sources:** https://en.wikipedia.org/wiki/1_Rockefeller_Plaza; city footprint BIN 1077286; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - "Completed in 1937" — Wikipedia
  - CTBUH Skyscraper Center ("One Rockefeller Plaza", id 9810): architectural 149 m, tip 149 m, roof 149 m, highest occupied floor —, observatory —; floors 34; start 1936, completed 1937
- **Measured (footprint / OSM parts):**
  - official footprint 1,625 m² (the city records 128.9 m for it)
  - OSM part tops 25, 29, 138, 149 m with their outlines
- **Estimated or simplified:**
  - `built` 1936.5–1937.9: years only
- **Check:** top 149.0 m vs cited 149.0 m (+0.0); wall outline at 0.6 m 1624 m² vs official 1625 m² (-0.1 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 128.8 m; hides BIN 1077286.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-25 m: 1285 / 1641; 25-29 m: 1106 / 1110; 29-138 m: 935 / 934; 138-149 m: 602 / 601.

### 1270 Avenue of the Americas (RKO Building) (`rockefeller_1270_sixth`)

- **Anchor** [-73.979837, 40.760062]; **built** 1931.7 – 1932.9; **kind** building.
- **Sources:** https://en.wikipedia.org/wiki/Rockefeller_Center; city footprint BIN 1083861; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - the RKO Building has no article of its own (Wikipedia redirects to Rockefeller Center); height and year are CTBUH's
  - CTBUH Skyscraper Center ("1270 Avenue of the Americas", id 11606): architectural 124.66 m, tip 124.66 m, roof —, highest occupied floor —, observatory —; floors 31; start —, completed 1932
- **Measured (footprint / OSM parts):**
  - official footprint 2,297 m²; city roof 123.7 m
  - OSM part tops 26, 30, 110, 117, 125 m with their outlines
- **Estimated or simplified:**
  - `built` starts at 1931.7: no start date found
- **Check:** top 124.7 m vs cited 124.7 m (+0.0); wall outline at 0.6 m 2295 m² vs official 2297 m² (-0.1 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 123.7 m; hides BIN 1083861.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-26 m: 2297 / 2339; 26-30 m: 2009 / 2009; 30-110 m: 1480 / 1481; 110-117 m: 1216 / 1216; 117-125 m: 523 / 525.

### 10 Rockefeller Plaza (Eastern Air Lines Building) (`rockefeller_plaza_10`)

- **Anchor** [-73.979707, 40.758363]; **built** 1939.5 – 1940.9; **kind** building.
- **Sources:** https://en.wikipedia.org/wiki/10_Rockefeller_Plaza; city footprint BIN 1077284; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - "Completed in 1940" — Wikipedia
  - CTBUH Skyscraper Center ("10 Rockefeller Plaza", id 17518): architectural 69.5 m, tip 69.5 m, roof —, highest occupied floor —, observatory —; floors 17; start 1939, completed 1940
- **Measured (footprint / OSM parts):**
  - official footprint 5,447 m² (slab and the garage block); city roof 67.0 m
  - OSM part tops 13, 20, 24, 61, 67 m with their outlines; top drawn at the cited 69.5 m
- **Estimated or simplified:**
  - `built` 1939.5–1940.9: years only
- **Check:** top 69.5 m vs cited 69.5 m (+0.0); wall outline at 0.6 m 5448 m² vs official 5447 m² (+0.0 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 67.0 m; hides BIN 1077284.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-12 m: 5516 / 5522; 13-18 m: 4050 / 4055; 18-20 m: 3229 / 4055; 20-24 m: 2229 / 2233; 24-61 m: 1296 / 1298; 61-67 m: 927 / 930.

### 50 Rockefeller Plaza (Associated Press Building) (`rockefeller_plaza_50`)

- **Anchor** [-73.978626, 40.759553]; **built** 1937.5 – 1938.9; **kind** building.
- **Sources:** https://en.wikipedia.org/wiki/50_Rockefeller_Plaza; city footprint BIN 1083859; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - "Completed in 1938" — Wikipedia
  - CTBUH Skyscraper Center ("Bank of America Building", id 11618): architectural 69.49 m, tip —, roof —, highest occupied floor —, observatory —; floors 17; start —, completed 1938
- **Measured (footprint / OSM parts):**
  - official footprint 3,324 m²; city roof 73.7 m
  - OSM part tops 20, 55, 60, 70, 74 m with their outlines; the stack is cut at the cited 69.5 m, which leaves out the 185 m² bulkhead
- **Estimated or simplified:**
  - `built` starts at 1937.5: no start date found
- **Check:** top 69.5 m vs cited 69.5 m (+0.0); wall outline at 0.6 m 3325 m² vs official 3324 m² (+0.0 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 73.7 m; hides BIN 1083859.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-20 m: 3324 / 3341; 20-55 m: 1937 / 1941; 55-60 m: 1426 / 1428; 60-70 m: 1104 / 1102; 70-74 m: 185 / 0.

### British Empire Building (`rockefeller_british_empire_building`)

- **Anchor** [-73.977797, 40.758586]; **built** 1932.3 – 1933.5; **kind** building.
- **Sources:** https://en.wikipedia.org/wiki/British_Empire_Building; city footprint BIN 1075692; OSM parts.
- **Cited dimensions and dates:**
  - completed 1933; roof 90 ft (27.4 m) excluding the penthouse; six storeys and a 1½-storey penthouse — Wikipedia infobox
- **Measured (footprint / OSM parts):**
  - official footprint about 1,260 m²; the city measures the top at 38.9 / 39.6 m
  - OSM part tops 20, 25 (main roof), 30, 35 m with their outlines
- **Estimated or simplified:**
  - the OSM heights are multiplied by 27.4 / 25 so that the main roof meets the cited 90 ft; the penthouse top then comes to 38.4 m, close to the city's measurement
  - `built` starts at 1932.3: no start date found
- **Check:** top 38.4 m vs cited 38.4 m (+0.0); wall outline at 0.6 m 1260 m² vs official 1261 m² (-0.1 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 38.9 m; hides BIN 1075692.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-20 m: 1295 / 1260; 20-25 m: 888 / 889; 25-30 m: 424 / 425; 30-35 m: 263 / 425.

### La Maison Française (`rockefeller_maison_francaise`)

- **Anchor** [-73.978023, 40.758277]; **built** 1932.3 – 1933.5; **kind** building.
- **Sources:** https://en.wikipedia.org/wiki/La_Maison_Francaise_(Rockefeller_Center); city footprint BIN 1082656; OSM parts.
- **Cited dimensions and dates:**
  - completed 1933; roof 90 ft (27.4 m) excluding the penthouse; six storeys and a 1½-storey penthouse — Wikipedia infobox
- **Measured (footprint / OSM parts):**
  - official footprint about 1,260 m²; the city measures the top at 38.9 / 39.6 m
  - OSM part tops 20, 25 (main roof), 30, 35 m with their outlines
- **Estimated or simplified:**
  - the OSM heights are multiplied by 27.4 / 25 so that the main roof meets the cited 90 ft; the penthouse top then comes to 38.4 m, close to the city's measurement
  - `built` starts at 1932.3: no start date found
- **Check:** top 38.4 m vs cited 38.4 m (+0.0); wall outline at 0.6 m 1257 m² vs official 1255 m² (+0.2 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 39.6 m; hides BIN 1082656.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-20 m: 1305 / 1257; 20-25 m: 888 / 890; 25-30 m: 425 / 425; 30-35 m: 263 / 425.

### Radio City Music Hall (`radio_city_music_hall`)

- **Anchor** [-73.979276, 40.759826]; **built** 1931.9 – 1932.99; **kind** building.
- **Sources:** https://en.wikipedia.org/wiki/Radio_City_Music_Hall; city footprint BIN 1083862; OSM parts.
- **Cited dimensions and dates:**
  - opened 27 Dec 1932 — Wikipedia
- **Measured (footprint / OSM parts):**
  - official footprint 4,270 m²; city roof 35.1 m
  - OSM part tops 30 and 35 m
- **Estimated or simplified:**
  - `built` starts at 1931.9: no start date found
  - no cited height: the model is the OSM massing; marquee not modelled
- **Check:** top 35.0 m vs cited 35.0 m (+0.0); wall outline at 0.6 m 4270 m² vs official 4270 m² (+0.0 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 35.1 m; hides BIN 1083862.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-30 m: 4692 / 4300; 30-35 m: 3517 / 3518.

### 7 World Trade Center (`wtc_7`)

- **Anchor** [-74.012075, 40.713414]; **built** 2002.35 – 2006.39; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/7_World_Trade_Center; city footprint BIN 1086510; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - architectural 743 ft (226.5 m), roof 741 ft (225.9 m), 52 floors — Wikipedia infobox
  - the first ten floors hold a substation behind stainless-steel louvres — Wikipedia
  - construction began 7 May 2002; opened 23 May 2006 — Wikipedia
  - CTBUH Skyscraper Center ("7 World Trade Center", id 1117): architectural 226.5 m, tip 226.5 m, roof 222.55 m, highest occupied floor 206.81 m, observatory —; floors 49; start 2002, completed 2006
- **Measured (footprint / OSM parts):**
  - parallelogram footprint 3,002 m²; city roof 226.7 m
- **Estimated or simplified:**
  - the height of the ten-storey louvred base, 36 m
- **Check:** top 226.5 m vs cited 226.5 m (+0.0); wall outline at 0.6 m 3002 m² vs official 3002 m² (+0.0 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 226.7 m; hides BIN 1086510.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-224 m: 3106 / 3002; 225-228 m: 170 / 0.

### 3 World Trade Center (`wtc_3`)

- **Anchor** [-74.01166, 40.710978]; **built** 2008.05 – 2018.44; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/3_World_Trade_Center; city footprint BIN 1088797; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - 1,079 ft (328.9 m), 80 floors — Wikipedia infobox
  - groundbreaking January 2008; lower podium completed November 2012; opened 11 Jun 2018; K-bracing on the facade — Wikipedia
  - CTBUH Skyscraper Center ("3 World Trade Center", id 273): architectural 328.88 m, tip 328.88 m, roof —, highest occupied floor —, observatory —; floors 69; start 2010, completed 2018
- **Measured (footprint / OSM parts):**
  - outlines from the official footprint (5,262 m²)
  - OSM part tops: podium 75 m, south section 220 m, north section 281 m. OSM's own top (352 m) is 23 m above the cited height, so these levels are weak
- **Estimated or simplified:**
  - K-bracing drawn schematically on the east and west faces
- **Check:** top 328.9 m vs cited 328.9 m (+0.0); wall outline at 0.6 m 5288 m² vs official 5262 m² (+0.5 %), centroid offset 0.2 m, IoU 0.99; city-measured roof 324.3 m; hides BIN 1088797.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-75 m: 5269 / 5314; 75-220 m: 3398 / 3463; 220-281 m: 2747 / 2867; 281-352 m: 2176 / 2234.

### 4 World Trade Center (`wtc_4`)

- **Anchor** [-74.011994, 40.710316]; **built** 2008.05 – 2013.87; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/4_World_Trade_Center; city footprint BIN 1088795; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - roof 978 ft (298.1 m) — Wikipedia infobox
  - floors 7–46 are parallelograms of 44,000 sq ft, floors 48–63 trapezoids of 36,000 sq ft — Wikipedia
  - groundbreaking January 2008; opened 13 Nov 2013 — Wikipedia
  - CTBUH Skyscraper Center ("4 World Trade Center", id 545): architectural 297.73 m, tip 297.73 m, roof 291.94 m, highest occupied floor 279.85 m, observatory 218 m; floors 65; start 2008, completed 2014
- **Measured (footprint / OSM parts):**
  - podium on the official footprint (4,547 m²), 25 m (OSM)
  - lower parallelogram and upper trapezoid outlines and the 220 m break — OSM parts
- **Estimated or simplified:**
  - weak spot: the OSM plans (3,281 and 2,547 m²) are about 20 % smaller than the cited floor areas; the OSM outlines are kept
  - the 220 m break is OSM; CTBUH lists a deck at 218.0 m, which supports it (the floor numbers at a uniform storey would give about 190 m)
- **Check:** top 297.7 m vs cited 297.7 m (+0.0); wall outline at 0.6 m 4545 m² vs official 4547 m² (-0.0 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 298.2 m; hides BIN 1088795.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-25 m: 4702 / 4546; 25-220 m: 3281 / 3285; 220-310 m: 2547 / 2512.

### Metropolitan Life Insurance Company Tower (`metlife_tower`)

- **Anchor** [-73.987358, 40.741276]; **built** 1907 – 1909.5; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/Metropolitan_Life_Insurance_Company_Tower; https://s-media.nyc.gov/agencies/lpc/lp/1530.pdf (LP-1530, 1989); city footprint BIN 1016741; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - roof 700 ft (213.4 m) — Wikipedia; LPC: the lantern is "700 feet above the sidewalk"
  - plan 75 ft on Madison Avenue by 85 ft on 24th Street — Wikipedia, LPC (official footprint: 21.8 × 26.2 m)
  - "from within the arcaded capital rises a setback capped with a pyramidal spire, cupola and lantern" — LPC
  - clock faces 26.5 ft in diameter on the 25th–27th floors — Wikipedia
  - built 1907–09 — LPC
  - CTBUH Skyscraper Center ("Metropolitan Life Tower", id 1383): architectural 213.36 m, tip 213.36 m, roof 200.26 m, highest occupied floor —, observatory —; floors 50; start 1907, completed 1909
- **Measured (footprint / OSM parts):**
  - OSM part tops: shaft 150 m, set-back stage 150–165 m (22.9 × 20.9 m), pyramid 165–190 m, cupola 190–206 m, top 213 m
- **Estimated or simplified:**
  - clock centre at 95 m (26th of about 41 shaft storeys)
  - the cupola top at 200 m (OSM) agrees with CTBUH's roof height of 200.26 m
  - 18 m base band, cornice, cupola radius 3.8 m, lantern radius 0.9 m
- **Check:** top 213.4 m vs cited 213.4 m (+0.0); wall outline at 0.6 m 563 m² vs official 564 m² (-0.1 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 182.9 m; hides BIN 1016741.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-150 m: 575 / 653; 150-165 m: 476 / 479; 165-190 m: 436 / 251; 190-206 m: 41 / 50; 206-213 m: 1 / 2.

### 40 Wall Street (`wall_40`)

- **Anchor** [-74.009731, 40.707024]; **built** 1929.35 – 1930.33; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/40_Wall_Street; https://s-media.nyc.gov/agencies/lpc/lp/1936.pdf (LP-1936, 1995); city footprint BIN 1001018; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - 927 ft (282.5 m) — Wikipedia, LPC; 70 floors (LPC: 71)
  - "crowned by a pyramidal roof capped by a spire"; roof of lead-coated copper with a spire and flagpole; set-backs atop the 12th, 19th, 23rd, 26th, 28th and 29th storeys — LPC
  - construction began May 1929; completed 1 May 1930 — Wikipedia
  - CTBUH Skyscraper Center ("The Trump Building", id 619): architectural 282.55 m, tip 282.55 m, roof 263.96 m, highest occupied floor 254.82 m, observatory —; floors 71; start 1929, completed 1930
- **Measured (footprint / OSM parts):**
  - OSM levels 30, 40, 64, 75, 90, 100, 112, 123, 130, 212, 230 m with their outlines; pyramid base 23.3 m square at 230 m, pyramid part to 262 m
- **Estimated or simplified:**
  - pyramid drawn to a 4.4 m platform at 259 m, lantern to 264 m, spire to the cited 282.5 m
  - `replaces` is the official outline shrunk 3 m so that the 100 m neighbour (BIN 1001017) is not hidden by the viewer's tall-sliver rule
- **Check:** top 282.5 m vs cited 282.5 m (+0.0); wall outline at 0.6 m 3007 m² vs official 3011 m² (-0.1 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 246.0 m; hides BIN 1001018.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-12 m: 2993 / 3101; 12-30 m: 2991 / 3101; 30-40 m: 2831 / 2841; 40-58 m: 2457 / 2468; 58-60 m: 2403 / 2468; 60-64 m: 2237 / 2468; 64-70 m: 2159 / 2168; 70-75 m: 2104 / 2168; 75-90 m: 1908 / 1919; 90-100 m: 1473 / 1474; 100-108 m: 1240 / 1236; 108-112 m: 1209 / 1236; 112-123 m: 1124 / 1120; 123-130 m: 1053 / 1057; 130-212 m: 801 / 801; 212-225 m: 691 / 692; 225-230 m: 608 / 692; 230-260 m: 524 / 168; 260-262 m: 524 / 11; 262-267 m: 11 / 11; 267-282 m: 3 / 2.

### 70 Pine Street (`pine_70`)

- **Anchor** [-74.007723, 40.706481]; **built** 1930.37 – 1932.37; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/70_Pine_Street; https://s-media.nyc.gov/agencies/lpc/lp/2441.pdf (LP-2441, 2011); city footprint BIN 1001007; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - architectural 952 ft (290.2 m), roof 850 ft, top floor 800 ft, 67 floors — Wikipedia infobox
  - spire 124 ft above the observation deck: a glass lantern 27 ft and a stainless-steel pinnacle 97 ft — Wikipedia; LPC: "27-foot-tall tiered glass lantern, and a 97-foot-tall stainless steel spire" (→ deck 252.4 m, lantern to 260.6 m)
  - construction started May 1930 and took 24 months — Wikipedia
  - CTBUH Skyscraper Center ("70 Pine", id 18405): architectural 290.17 m, tip 290.17 m, roof 260 m, highest occupied floor 243.84 m, observatory 240 m; floors 67; start 1930, completed 1932
- **Measured (footprint / OSM parts):**
  - OSM levels from 45 m to 252 m (18 steps) with their outlines
- **Estimated or simplified:**
  - lantern radius 3.6 m, pinnacle 3.2 → 1 m
- **Check:** top 290.2 m vs cited 290.2 m (+0.0); wall outline at 0.6 m 2909 m² vs official 2910 m² (-0.1 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 249.3 m; hides BIN 1001007.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-45 m: 2900 / 2917; 45-50 m: 2510 / 2513; 50-60 m: 2253 / 2250; 60-65 m: 2065 / 2067; 65-70 m: 1915 / 1917; 70-75 m: 1701 / 1704; 75-80 m: 1546 / 1547; 80-90 m: 1386 / 1387; 90-100 m: 1215 / 1217; 100-105 m: 1094 / 1095; 105-112 m: 1079 / 1095; 112-210 m: 847 / 844; 210-220 m: 760 / 764; 220-224 m: 713 / 715; 224-234 m: 655 / 650; 234-238 m: 550 / 553; 238-242 m: 408 / 401; 242-250 m: 168 / 168; 250-252 m: 122 / 168; 252-256 m: 101 / 37; 256-258 m: 50 / 37; 259-261 m: 21 / 37; 264-290 m: 2 / 1.

### Citigroup Center (601 Lexington Avenue) (`citigroup_center`)

- **Anchor** [-73.969938, 40.75838]; **built** 1974.3 – 1977.8; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/Citigroup_Center; https://s-media.nyc.gov/agencies/lpc/lp/2582.pdf (LP-2582, 2016); city footprint BIN 1036474; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - 915 ft (278.9 m), 59 floors — Wikipedia, LPC
  - "it rises on four 24-foot-square super columns and a massive octagonal elevator core"; each column "centered beneath one facade", "more than 100 feet tall"; roof "cut off at a 45-degree angle"; the church set at 45° to the tower — LPC
  - stilts rising 112 ft; the roof "rises 160 ft above the top story and faces south, sloping at a 45-degree angle" — Wikipedia
  - groundbreaking April 1974, work twelve months later; topped out 6 Oct 1976; completed 1977 — Wikipedia
  - CTBUH Skyscraper Center ("601 Lexington", id 648): architectural 278.9 m, tip 278.9 m, roof 278.9 m, highest occupied floor —, observatory —; floors 63; start 1974, completed 1977
- **Measured (footprint / OSM parts):**
  - official footprint 5,686 m²: tower, St Peter's Church and the east wing in one polygon; the tower is placed with its west and south faces on the footprint edges
  - OSM parts: east wing 26 m with a 30 m centre, terraces 22 / 18 / 14 / 10 m, church 15–17 m, core 16.5 m across
- **Estimated or simplified:**
  - tower side 47.9 m: a 45° roof with a 160 ft (48.8 m) rise spans the whole depth (OSM draws 49.4 m); eave at 231 m
  - church drawn as a granite prism with a tapered top; plaza structures 7 m
  - plan check by projection (the tower stands on stilts)
- **Check:** top 278.9 m vs cited 278.9 m (+0.0); plan projection 5677 m² vs official 5686 m² (-0.2 %), centroid offset 0.2 m, IoU 0.99; city-measured roof 277.7 m; hides BIN 1036474.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-7 m: 5637 / 5677; 7-10 m: 5016 / 5483; 10-14 m: 4392 / 5285; 18-22 m: 3664 / 5028; 22-26 m: 3504 / 4986; 26-28 m: 1710 / 3103; 28-30 m: 1497 / 3103; 30-35 m: 689 / 2294; 35-38 m: 2566 / 2294; 38-45 m: 2550 / 2294; 45-69 m: 2529 / 2294; 69-242 m: 2424 / 2294; 242-279 m: 2177 / 881.

### 432 Park Avenue (`park_432`)

- **Anchor** [-73.971802, 40.761511]; **built** 2012.1 – 2015.98; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/432_Park_Avenue; city footprints BIN 1088817 and 1035787; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - architectural 1,396 ft (425.5 m), 85 floors numbered to 96 — Wikipedia infobox
  - "Five two-story windbreaks, spaced every 12 floors from the top, are unenclosed" — Wikipedia
  - excavation early 2012; topped out 10 Oct 2014; completed 23 Dec 2015 — Wikipedia
  - CTBUH Skyscraper Center ("432 Park Avenue", id 13227): architectural 425.7 m, tip 425.7 m, roof 416.27 m, highest occupied floor 392.14 m, observatory —; floors 85; start 2011, completed 2015
- **Measured (footprint / OSM parts):**
  - tower square 28.7 × 28.2 m (OSM part; the 93 ft / 28.5 m of the brief agrees)
  - retail building on 57th St 30 m (OSM part); lot outline from the official footprint
- **Estimated or simplified:**
  - windbreak heights from a uniform 4.43 m level (425.5 m over 96 numbered levels)
  - the plaza on 56th St (1.2 m) and the Park Avenue pavilion (12 m) have no measured height
  - `replaces` is the main lot only: the 7.6 m strip BIN 1035787 (recorded at 425.5 m) is hidden by the viewer's tall-sliver rule; an outline wide enough to contain it would also hide the 80 m neighbour BIN 1035788
- **Check:** top 425.5 m vs cited 425.5 m (+0.0); wall outline at 0.6 m 3235 m² vs official 3186 m² (+1.5 %), centroid offset 0.1 m, IoU 0.98; city-measured roof 425.5 m; hides BIN 1035787 (tall-sliver rule), 1088817.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-30 m: 1890 / 1669; 30-33 m: 1050 / 812; 33-39 m: 1030 / 812; 39-44 m: 1011 / 812; 45-47 m: 966 / 812; 47-54 m: 958 / 812; 54-58 m: 910 / 812; 58-66 m: 888 / 812; 66-69 m: 834 / 812; 69-426 m: 804 / 812.

### One Vanderbilt (`one_vanderbilt`)

- **Anchor** [-73.97855, 40.752973]; **built** 2016.8 – 2020.7; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/One_Vanderbilt; city footprint BIN 1090825; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - roof 1,301 ft (396.5 m), spire 1,401 ft (427.0 m), 62 floors numbered to 73 — Wikipedia
  - "the tower tapers as it rises, with several pavilions and a pinnacle at the top" — Wikipedia
  - groundbreaking 18 Oct 2016; opened 14 Sep 2020 — Wikipedia
  - CTBUH Skyscraper Center ("One Vanderbilt Avenue", id 15833): architectural 427.02 m, tip 427.02 m, roof 392.6 m, highest occupied floor 330.1 m, observatory 330.1 m; floors 62; start 2017, completed 2020
- **Measured (footprint / OSM parts):**
  - base from the official footprint (65.7 × 61 m, 4,001 m²)
  - OSM part tops 75, 315, 330, 350, 397 m with their outlines (the four interlocking volumes)
- **Estimated or simplified:**
  - the model steps where the building tapers: between 75 and 315 m the plan is constant
  - spire radius 1.6 → 0.25 m, placed on the centre of the top OSM part
- **Check:** top 427.0 m vs cited 427.0 m (+0.0); wall outline at 0.6 m 3998 m² vs official 4001 m² (-0.1 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 427.0 m; hides BIN 1090825.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-12 m: 3865 / 4016; 12-75 m: 3796 / 4016; 75-315 m: 3281 / 3287; 315-330 m: 1915 / 1906; 330-350 m: 951 / 943; 350-397 m: 287 / 287; 397-427 m: 6 / 2.

### Central Park Tower (`central_park_tower`)

- **Anchor** [-73.981011, 40.76643]; **built** 2014.37 – 2020.9; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/Central_Park_Tower; city footprint BIN 1090180; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - architectural 1,550 ft (472.4 m), 98 floors — Wikipedia infobox
  - a cantilever "extending 28 ft from the eastern side of the tower", starting "roughly 290 ft" up over the Art Students League — Wikipedia (OSM: 8.3 m from 89 m)
  - excavation May 2014; topped out 17 Sep 2019; completed 2020 — Wikipedia
  - CTBUH Skyscraper Center ("Central Park Tower", id 14269): architectural 472.44 m, tip 472.44 m, roof 461.92 m, highest occupied floor 431.75 m, observatory —; floors 98; start 2014, completed 2020
- **Measured (footprint / OSM parts):**
  - base: the official outline without the cantilever's shadow (3,679 m²), 23 m and 44 m (OSM part tops)
  - tower outlines and levels 89, 127, 163, 237, 332, 342, 433, 466, 472 m — OSM parts
- **Estimated or simplified:**
  - `built` ends at 2020.9 (only the year is cited)
  - `replaces` is cut back around the 85 m neighbour in the south-west notch (BIN 1024901) and excludes the cantilever's shadow
  - plan check by projection (cantilever)
- **Check:** top 472.4 m vs cited 472.4 m (+0.0); plan projection 4005 m² vs official 3891 m² (+2.9 %), centroid offset 0.6 m, IoU 0.97; city-measured roof 472.4 m; hides BIN 1090180.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-23 m: 3401 / 4005; 23-44 m: 3113 / 3356; 44-89 m: 1069 / 1315; 89-127 m: 1311 / 1313; 127-163 m: 1127 / 1128; 163-237 m: 901 / 902; 237-332 m: 854 / 856; 332-342 m: 825 / 826; 342-433 m: 791 / 793; 433-466 m: 622 / 624; 466-471 m: 182 / 624.

### Steinway Hall (`steinway_hall`)

- **Anchor** [-73.97756, 40.764957]; **built** 1924.5 – 1925.82; **kind** building.
- **Sources:** https://s-media.nyc.gov/agencies/lpc/lp/2100.pdf (LP-2100, 2001); https://en.wikipedia.org/wiki/111_West_57th_Street; city footprint BIN 1023728; OSM / Overture building "Steinway Hall" (67 m).
- **Cited dimensions and dates:**
  - sixteen storeys, built 1924–25; "L-shaped in plan, with a front portion clad in Indiana limestone that terminates in a set back, four-story colonnaded tower"; the 58th Street portion "has setbacks above the ninth and twelfth stories" — LPC
  - completed 27 Oct 1925 — Wikipedia infobox
- **Measured (footprint / OSM parts):**
  - height 67 m — OSM/Overture building (no cited height found)
  - the official footprint (1,855 m², 30.4 × 61.1 m) is the whole lot including the 2022 tower
- **Estimated or simplified:**
  - which part of the lot each wing covers (57th St front on the west 13 m; 58th St portion across the lot north of the tower)
  - storey height 4.2 m (67 m / 16); tower plan
- **Check:** top 67.0 m vs cited 67.0 m (+0.0); wall outline at 0.6 m (with west_57th_111) 1829 m² vs official 1855 m² (-1.4 %), centroid offset 0.5 m, IoU 0.94; city-measured roof 435.2 m; hides BIN 1023728.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-30 m: 699 / 1829; 30-200 m: 448 / 449; 200-248 m: 418 / 418; 248-283 m: 387 / 386; 283-308 m: 356 / 356; 308-328 m: 325 / 325; 328-343 m: 294 / 294; 343-358 m: 263 / 263; 358-373 m: 232 / 232; 373-383 m: 201 / 201; 383-393 m: 170 / 170; 393-405 m: 139 / 139; 405-417 m: 108 / 109; 417-435 m: 77 / 78.

### 111 West 57th Street (Steinway Tower) (`west_57th_111`)

- **Anchor** [-73.97756, 40.764957]; **built** 2014.5 – 2021.9; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/111_West_57th_Street; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - architectural 1,428 ft (435.3 m), 84 floors — Wikipedia infobox
  - "The tower's northern elevation rises directly up to the pinnacle, and the southern elevation contains several setbacks" — Wikipedia
  - construction on the tower began in 2014; topped out October 2019; completed 2022 — Wikipedia
  - CTBUH Skyscraper Center ("111 West 57th Street", id 14320): architectural 435.25 m, tip 435.25 m, roof 383.28 m, highest occupied floor 345.5 m, observatory —; floors 84; start 2015, completed 2021
- **Measured (footprint / OSM parts):**
  - tower 18.2 m wide (OSM; the 60 ft of the brief), 25 m deep at the base of the shaft; thirteen set-backs of the south face between 200 and 417 m, top 435 m — OSM parts
  - 30 m base on 57th St — OSM part
- **Estimated or simplified:**
  - none in the geometry; rides on the Steinway Hall footprint (same lot, no `replaces` of its own)
- **Check:** top 435.3 m (cited 435.3 m); no footprint of its own — checked together with the model it stands on.

### 30 Hudson Yards and the Shops (`hudson_yards_30`)

- **Anchor** [-74.00091, 40.753522]; **built** 2014.5 – 2019.2; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/30_Hudson_Yards; city footprint BIN 1088961; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - 1,270 ft (387.1 m), 73 floors; groundbreaking ceremony 4 Dec 2012; opened 15 Mar 2019 — Wikipedia
  - the Edge: a triangular deck "jutting out from the 100th floor", at 1,100 ft (335 m), opened March 2020 — Wikipedia
  - CTBUH Skyscraper Center ("30 Hudson Yards", id 13325): architectural 387.07 m, tip 387.07 m, roof 379.17 m, highest occupied floor 342.14 m, observatory 336.65 m; floors 73; start 2014, completed 2019
- **Measured (footprint / OSM parts):**
  - the official footprint (17,990 m²) is the tower and the Shops in one polygon recorded at 385.6 m
  - tower outlines and levels 10, 130, 140, 310, 335–340 (the deck), 387 m — OSM parts, clipped to the official outline
- **Estimated or simplified:**
  - the Shops are extruded on the official outline to 45 m: no measured height was found (Overture lists 67 m with "4 floors", which is not credible)
  - the Edge is drawn from its start though it opened a year after the tower
- **Check:** top 387.1 m vs cited 387.1 m (+0.0); wall outline at 0.6 m 18046 m² vs official 17990 m² (+0.3 %), centroid offset 0.3 m, IoU 1.0; city-measured roof 385.6 m; hides BIN 1088961.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-10 m: 6635 / 18052; 10-130 m: 6410 / 5799; 130-133 m: 5059 / 5799; 133-140 m: 4603 / 3991; 140-240 m: 4477 / 3847; 240-310 m: 4003 / 3847; 310-335 m: 1920 / 2411; 335-340 m: 2564 / 2411; 340-395 m: 1920 / 1766.

### 10 Hudson Yards (`hudson_yards_10`)

- **Anchor** [-74.001525, 40.752686]; **built** 2012.92 – 2016.41; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/10_Hudson_Yards; city footprint BIN 1089323; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - roof 878 ft (267.6 m), 52 floors; groundbreaking 4 Dec 2012; completed 31 May 2016 — Wikipedia infobox
  - the south facade cantilevers over the High Line spur — Wikipedia
  - CTBUH Skyscraper Center ("10 Hudson Yards", id 13326): architectural 267.67 m, tip 267.67 m, roof —, highest occupied floor 214.58 m, observatory —; floors 52; start 2013, completed 2016
- **Measured (footprint / OSM parts):**
  - base from the official footprint (4,103 m²; the city records only 45.4 m for it)
  - levels 105, 120, 165, 240, 273 m — OSM parts; the top is drawn at the cited 267.6 m
- **Estimated or simplified:**
  - nothing; the sloped roof is drawn flat
- **Check:** top 267.6 m vs cited 267.6 m (+0.0); wall outline at 0.6 m 4102 m² vs official 4103 m² (-0.0 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 45.4 m; hides BIN 1089323.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-20 m: 4142 / 4302; 20-105 m: 4128 / 4302; 105-120 m: 3698 / 3860; 120-165 m: 3861 / 3855; 165-240 m: 2651 / 2646; 240-273 m: 2178 / 2171.

### Vessel (`vessel`)

- **Anchor** [-74.002161, 40.753803]; **built** 2017.3 – 2019.2; **kind** monument.
- **Sources:** https://en.wikipedia.org/wiki/Vessel_(structure); city footprints BIN 1090391 and 1090967.
- **Cited dimensions and dates:**
  - 150 ft (45.7 m), 16 storeys, 154 flights, 80 landings; groundbreaking April 2017, topped out December 2017, opened 15 Mar 2019 — Wikipedia
- **Measured (footprint / OSM parts):**
  - top 46 m across — the official footprint (1,595 m²)
- **Estimated or simplified:**
  - base width 15 m (50 ft): from memory of the designer's published figure, not re-verified
  - two concentric copper shells and eight landing rings stand for the lattice of stairs
  - plan check by projection (the structure widens upward)
- **Check:** top 45.7 m vs cited 45.7 m (+0.0); plan projection 1566 m² vs official 1644 m² (-4.7 %), centroid offset 0.0 m, IoU 0.94; city-measured roof 47.2 m; hides BIN 1090967, 1090391.

### Bank of America Tower (`bank_of_america_tower`)

- **Anchor** [-73.984707, 40.755566]; **built** 2004.58 – 2009.33; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/Bank_of_America_Tower_(Manhattan); city footprint BIN 1087268; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - "an architectural spire at its south end, rising 1200 ft; the roof height at that location is 945 ft" (365.8 m, 288.0 m); 55 floors — Wikipedia
  - groundbreaking 2 Aug 2004; completed 1 May 2009 — Wikipedia
  - CTBUH Skyscraper Center ("Bank of America Tower", id 291): architectural 365.8 m, tip 365.8 m, roof 287.89 m, highest occupied floor 234.5 m, observatory —; floors 55; start 2004, completed 2009
- **Measured (footprint / OSM parts):**
  - base from the official footprint (7,858 m², with the Stephen Sondheim Theatre)
  - podium 15 / 30 m, shaft to 236 m, crown facets 240–279 m — OSM parts
- **Estimated or simplified:**
  - the crown levels above 236 m are stretched by 1.21 so that OSM's 279 m top meets the cited 288 m roof
  - spire radius 2.6 → 0.25 m from 245 m
- **Check:** top 365.8 m vs cited 365.8 m (+0.0); wall outline at 0.6 m 7856 m² vs official 7858 m² (-0.0 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 270.6 m; hides BIN 1087268.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-15 m: 7965 / 8035; 15-30 m: 7423 / 7431; 30-236 m: 3590 / 3590; 236-239 m: 2566 / 3590; 240-245 m: 1203 / 2253; 245-250 m: 986 / 2015; 250-257 m: 803 / 1844; 257-262 m: 530 / 1844; 262-279 m: 228 / 208; 279-366 m: 25 / 3.

### The New York Times Building (`new_york_times_building`)

- **Anchor** [-73.989691, 40.755922]; **built** 2004.8 – 2007.88; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/The_New_York_Times_Building; city footprint BIN 1087186; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - "rises 748 ft from the street to its roof, while the exterior curtain wall rises to 840 ft and its mast rises to 1046 ft" (228.0, 256.0, 318.8 m); 52 floors — Wikipedia
  - work began late 2004; opened 19 Nov 2007 — Wikipedia
  - CTBUH Skyscraper Center ("New York Times Tower", id 423): architectural 318.77 m, tip 318.77 m, roof 227.38 m, highest occupied floor 219.9 m, observatory —; floors 52; start 2004, completed 2007
- **Measured (footprint / OSM parts):**
  - podium from the official footprint (6,583 m²), 25 m; cruciform tower to 227 m, core to 232 m — OSM parts, clipped to the official outline
- **Estimated or simplified:**
  - mast radius 1.3 → 0.2 m
- **Check:** top 318.8 m vs cited 318.8 m (+0.0); wall outline at 0.6 m 6581 m² vs official 6583 m² (-0.0 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 230.1 m; hides BIN 1087186.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-6 m: 6285 / 6638; 6-12 m: 6312 / 6638; 12-25 m: 6365 / 6638; 25-227 m: 2696 / 2369; 227-232 m: 804 / 727; 232-244 m: 84 / 4; 244-319 m: 4 / 1.

### 8 Spruce Street (New York by Gehry) (`spruce_8`)

- **Anchor** [-74.005612, 40.710907]; **built** 2006.5 – 2011.1; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/8_Spruce; city footprint BIN 1087485; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - roof 870 ft (265.2 m), 76 floors; construction start 2006, completion 2010; opened February 2011 — Wikipedia
  - CTBUH Skyscraper Center ("Eight Spruce Street", id 699): architectural 265.18 m, tip 271.58 m, roof 256.66 m, highest occupied floor 252.09 m, observatory —; floors 76; start 2006, completed 2011
- **Measured (footprint / OSM parts):**
  - podium from the official footprint (2,880 m²), 26 m; set-backs at 29, 32, 37, 90, 140, 180 m — OSM parts; top drawn at the cited 265.2 m (OSM 272, city 262.4)
- **Estimated or simplified:**
  - the rippling steel skin is not modelled
- **Check:** top 265.2 m vs cited 265.2 m (+0.0); wall outline at 0.6 m 2880 m² vs official 2880 m² (+0.0 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 262.4 m; hides BIN 1087485.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-26 m: 2895 / 2907; 26-29 m: 2294 / 2286; 29-32 m: 1976 / 1978; 32-37 m: 1718 / 1722; 37-90 m: 1472 / 1478; 90-140 m: 1338 / 1342; 140-180 m: 1214 / 1218; 180-272 m: 1109 / 1110.

### Hearst Magazine Building (`hearst_magazine_building`)

- **Anchor** [-73.983624, 40.766572]; **built** 1927.45 – 1928.5; **kind** building.
- **Sources:** https://en.wikipedia.org/wiki/Hearst_Tower_(Manhattan); https://s-media.nyc.gov/agencies/lpc/lp/1625.pdf (LP-1625, 1988); city footprint BIN 1025451; OSM parts.
- **Cited dimensions and dates:**
  - six-storey base built 1927–28 "of an office tower that was never constructed" — LPC
  - excavation had begun by June 1927 — Wikipedia
- **Measured (footprint / OSM parts):**
  - official footprint 3,521 m² (59 × 60.5 m); 30 m high — OSM part
- **Estimated or simplified:**
  - none in the geometry (a plain extrusion; the corner pylons are not modelled)
- **Check:** top 30.0 m vs cited 30.0 m (+0.0); wall outline at 0.6 m (with hearst_tower) 3524 m² vs official 3521 m² (+0.1 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 174.0 m; hides BIN 1025451.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-30 m: 3980 / 3524; 30-182 m: 2001 / 1916.

### Hearst Tower (`hearst_tower`)

- **Anchor** [-73.983624, 40.766572]; **built** 2003.33 – 2006.75; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/Hearst_Tower_(Manhattan); OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - roof 597 ft (182.0 m), 46 floors — Wikipedia infobox
  - "Each of the upper stories has a footprint of 160 by 120 ft, with the longer dimension extending from east to west" — Wikipedia (OSM: 51.1 × 39.3 m)
  - "The diagrid divides the tower's sides horizontally into eight tiers, each measuring four stories high"; "the diagonal beams are typically 57 ft long by 40 ft wide"; "The setbacks above the sixth floor contain a skylight 40 ft wide" — Wikipedia
  - work began 30 Apr 2003; completed 2006 — Wikipedia
  - CTBUH Skyscraper Center ("Hearst Tower", id 2245): architectural 181.97 m, tip 181.97 m, roof 181.97 m, highest occupied floor —, observatory —; floors 46; start 2003, completed 2006
- **Measured (footprint / OSM parts):**
  - rides on the Hearst Magazine Building footprint
- **Estimated or simplified:**
  - tier height 16.27 m from the 57 ft diagonal on a 40 ft base; the eight tiers are measured down from the roof, so the diagrid starts at 51.8 m with a glazed zone below
  - tower centred on the base; the chamfered "bird's-mouth" corners are not modelled
- **Check:** top 182.0 m (cited 182.0 m); no footprint of its own — checked together with the model it stands on.

### 56 Leonard Street (`leonard_56`)

- **Anchor** [-74.0063, 40.717657]; **built** 2012.8 – 2016.9; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/56_Leonard_Street; city footprint BIN 1088646; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - roof 821 ft (250.2 m), 60 floors, 500,005 sq ft — Wikipedia infobox
  - foundation work 2008, shut down; construction resumed October 2012; completed 2017 — Wikipedia
  - CTBUH Skyscraper Center ("56 Leonard", id 844): architectural 250.24 m, tip 250.24 m, roof 250.24 m, highest occupied floor 242.6 m, observatory —; floors 57; start 2008, completed 2016
- **Measured (footprint / OSM parts):**
  - official footprint 1,418 m² (the city records only 77.7 m for it); no OSM parts
- **Estimated or simplified:**
  - schematic model: a 30 m base zone on the official outline, a 31 × 25 m shaft (775 m² = floor area / floors) and pseudo-random slabs for the cantilevered floors
- **Check:** top 250.2 m vs cited 250.2 m (+0.0); wall outline at 0.6 m 1416 m² vs official 1418 m² (-0.1 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 77.7 m; hides BIN 1088646.

### United Nations Secretariat Building (`un_secretariat`)

- **Anchor** [-73.968101, 40.748928]; **built** 1948.7 – 1951.45; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/United_Nations_Secretariat_Building; city footprint BIN 1083875; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - roof 505 ft (153.9 m), 39 floors; slab 72 × 287 ft; glass curtain walls west and east, marble north and south; mechanical storeys faced with latticed panels — Wikipedia
  - groundbreaking 14 Sep 1948; completed June 1951 — Wikipedia
  - CTBUH Skyscraper Center ("United Nations Secretariat Building", id 3737): architectural 154.3 m, tip 154.3 m, roof 152.2 m, highest occupied floor 140.8 m, observatory —; floors 39; start 1947, completed 1953
- **Measured (footprint / OSM parts):**
  - official footprint 21.0 × 86.1 m (1,805 m²); city roof 156.3 m
- **Estimated or simplified:**
  - the mechanical bands are drawn at 21, 60, 107 and 149 m (6th, 16th, 28th, 39th floors from memory, at 3.9 m a storey)
- **Check:** top 153.9 m vs cited 153.9 m (+0.0); wall outline at 0.6 m 1810 m² vs official 1805 m² (+0.3 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 156.3 m; hides BIN 1083875.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-156 m: 1909 / 1810.

### United Nations General Assembly and Conference buildings (`un_general_assembly`)

- **Anchor** [-73.967464, 40.749842]; **built** 1950.1 – 1952.78; **kind** building.
- **Sources:** https://en.wikipedia.org/wiki/United_Nations_General_Assembly_Building; city footprint BIN 1083872; OSM parts.
- **Cited dimensions and dates:**
  - four-storey building about 380 × 160 ft with concave west and east walls and a dome; Assembly Hall 75 ft tall — Wikipedia
  - steelwork from February 1950; dedicated 10 Oct 1952 — Wikipedia
- **Measured (footprint / OSM parts):**
  - the official footprint (18,841 m², recorded at 21.6 m) covers the General Assembly and Conference buildings and the terraces between and north of them
  - General Assembly 25 m with a 34 m dome to 32 m, Conference Building 20–23 m — OSM parts
- **Estimated or simplified:**
  - terraces outside the OSM parts drawn 1.2 m high
  - flat roofs (the Assembly roof really sweeps up to the north); dome drawn from 22 m
  - the Conference Building is drawn from 1950 too (same footprint)
- **Check:** top 32.0 m vs cited 32.0 m (+0.0); wall outline at 0.6 m 19091 m² vs official 18841 m² (+1.3 %), centroid offset 0.5 m, IoU 0.99; city-measured roof 21.6 m; hides BIN 1083872.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-18 m: 12968 / 13028; 18-20 m: 12506 / 13028; 20-23 m: 10294 / 10352; 23-25 m: 6268 / 10352; 25-32 m: 933 / 373.

### Lever House (`lever_house`)

- **Anchor** [-73.972873, 40.759615]; **built** 1950.5 – 1952.33; **kind** building.
- **Sources:** https://en.wikipedia.org/wiki/Lever_House; https://s-media.nyc.gov/agencies/lpc/lp/1277.pdf (LP-1277, 1982); city footprint BIN 1035732; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - 307 ft (93.6 m), 21 floors (LPC: 24-storey); built 1950–52; opened 29 Apr 1952 — Wikipedia
  - "a vertical slab rising above a horizontal base"; "open colonnaded space … with a planted courtyard open to the sky" — LPC
  - CTBUH Skyscraper Center ("Lever House", id 9068): architectural 93.57 m, tip 93.57 m, roof 93.57 m, highest occupied floor —, observatory —; floors 21; start 1950, completed 1952
- **Measured (footprint / OSM parts):**
  - lot from the official footprint (2,835 m²), whose interior ring is the garden court, 20.4 × 18.2 m (372 m²)
  - tower slab 51 × 16.8 m from 15 m — OSM part
- **Estimated or simplified:**
  - raised slab between 5.2 and 10.4 m, recessed third storey to 15 m
  - columns on an 8.8 m grid
  - plan check by projection (the base stands on columns)
- **Check:** top 93.6 m vs cited 93.6 m (+0.0); plan projection 2857 m² vs official 2835 m² (+0.8 %), centroid offset 0.0 m, IoU 0.99; city-measured roof 82.1 m; hides BIN 1035732.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-15 m: 2829 / 2857; 15-94 m: 803 / 805.

### Seagram Building (`seagram_building`)

- **Anchor** [-73.971977, 40.758387]; **built** 1955.7 – 1958.39; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/Seagram_Building; https://s-media.nyc.gov/agencies/lpc/lp/1664.pdf (LP-1664, 1989); city footprint BIN 1036465; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - roof 516 ft, 38 floors — Wikipedia infobox; the model uses CTBUH's 156.97 m (515 ft, the brief's figure)
  - "backed by a ten-story bustle, full-height spine, and five-story wings" — LPC
  - demolition from September 1955, superstructure from May 1956; opened 22 May 1958 — Wikipedia
  - CTBUH Skyscraper Center ("Seagram Building", id 3529): architectural 156.97 m, tip 156.97 m, roof 156.97 m, highest occupied floor —, observatory —; floors 38; start 1956, completed 1958
- **Measured (footprint / OSM parts):**
  - plan from the official footprint (2,892 m²; the plaza is not part of it)
  - wings 20 m, bustle 40 m, slab with its spine (34.7 × 43 m) — OSM parts; top drawn at the cited 157.0 m (OSM 162, city 161.9 m)
- **Estimated or simplified:**
  - nothing but the colour
- **Check:** top 157.0 m vs cited 157.0 m (+0.0); wall outline at 0.6 m 2894 m² vs official 2892 m² (+0.1 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 161.8 m; hides BIN 1036465.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-20 m: 2915 / 2980; 20-40 m: 2038 / 2043; 40-120 m: 1353 / 1341; 120-162 m: 1338 / 1341.

### MetLife Building (Pan Am Building) (`metlife_building`)

- **Anchor** [-73.976653, 40.753522]; **built** 1960.9 – 1963.18; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/MetLife_Building; city footprint BIN 1085630; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - roof 808 ft (246.3 m), 59 floors; an elongated octagon on a nine-storey base — Wikipedia
  - substructure from May 1960; topped out 9 May 1962; opened 7 Mar 1963 — Wikipedia
  - CTBUH Skyscraper Center ("MetLife Building", id 909): architectural 246.28 m, tip 246.28 m, roof 246.28 m, highest occupied floor —, observatory —; floors 59; start 1960, completed 1963
- **Measured (footprint / OSM parts):**
  - base from the official footprint (10,016 m²; the city records only 47.9 m for it)
  - base 30 and 38 m, octagonal tower 90.8 × 42.4 m — OSM parts
- **Estimated or simplified:**
  - nothing but the colour
- **Check:** top 246.3 m vs cited 246.3 m (+0.0); wall outline at 0.6 m 10011 m² vs official 10016 m² (-0.0 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 47.9 m; hides BIN 1085630.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-30 m: 10033 / 10029; 30-38 m: 6350 / 6736; 38-246 m: 3482 / 3483.

### Manhattan Municipal Building (`municipal_building`)

- **Anchor** [-74.003634, 40.712968]; **built** 1909.54 – 1914.5; **kind** building.
- **Sources:** https://en.wikipedia.org/wiki/Manhattan_Municipal_Building; https://s-media.nyc.gov/agencies/lpc/lp/0079.pdf (LP-0079, 1966); city footprint BIN 1001394; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - "The tower rises to around 560 ft above ground level; including the Civic Fame statue, the building stands at around 580 ft" (176.8 m); statue 25 ft; 40 storeys — Wikipedia
  - "rising to a height of 25 stories with a tower above" — LPC
  - work officially started 17 Jul 1909 and continued through 1914 — Wikipedia
  - CTBUH Skyscraper Center ("The David N. Dinkins Manhattan Municipal Building", id 2471): architectural 176.79 m, tip 176.79 m, roof 170.69 m, highest occupied floor —, observatory —; floors 34; start 1909, completed 1914
- **Measured (footprint / OSM parts):**
  - plan from the official footprint (4,335 m²) to 107 m; tiers 107–113, 113–123, 123–135, 135–149, 149–165, 165–177 m — OSM parts
- **Estimated or simplified:**
  - the top tier ends at the 170.7 m roof (CTBUH) and the statue is drawn as a gilded shaft above it to the cited 176.8 m
  - the vaulted passage of Chambers Street through the base is not cut out
- **Check:** top 176.8 m vs cited 176.8 m (+0.0); wall outline at 0.6 m 4333 m² vs official 4335 m² (-0.1 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 168.4 m; hides BIN 1001394.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-107 m: 4379 / 4333; 107-113 m: 1419 / 1443; 113-123 m: 646 / 670; 123-135 m: 379 / 373; 135-144 m: 324 / 244; 144-149 m: 253 / 244; 149-165 m: 139 / 126; 165-177 m: 64 / 3; 177-183 m: 2 / 0.

### Park Row Building (`park_row_building`)

- **Anchor** [-74.007777, 40.71118]; **built** 1896.8 – 1899.55; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/Park_Row_Building; https://s-media.nyc.gov/agencies/lpc/lp/2024.pdf (LP-2024, 1999); city footprint BIN 1001249; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - 391 ft (119.2 m); "26 full floors, a partial 27th floor, and a pair of four-story cupolas"; built 1896–99 — Wikipedia
  - "Each tower is comprised of three fully visible stories, with a fourth story located in the large dome" — LPC
  - CTBUH Skyscraper Center ("15 Park Row", id 9142): architectural 119.18 m, tip —, roof 102.11 m, highest occupied floor —, observatory —; floors 30; start 1896, completed 1899
- **Measured (footprint / OSM parts):**
  - official footprint 1,246 m² (with its light courts); city roof 118.9 m; no OSM parts
- **Estimated or simplified:**
  - cupolas 8.6 m across on the two front wings, rising from the 102.1 m main roof (CTBUH roof height), domes from 113.5 m
  - `built` 1896.8–1899.55: only the years are cited
- **Check:** top 119.2 m vs cited 119.2 m (+0.0); wall outline at 0.6 m 1245 m² vs official 1246 m² (-0.0 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 118.9 m; hides BIN 1001249.

### New York Life Building (`new_york_life_building`)

- **Anchor** [-73.985584, 40.742754]; **built** 1926.5 – 1928.95; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/New_York_Life_Building; https://s-media.nyc.gov/agencies/lpc/lp/2067.pdf (LP-2067, 2000); city footprint BIN 1016880; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - 615 ft (187.5 m) — Wikipedia
  - "The octagonal pyramidal roof at the top is 88 ft tall and includes the 35th through 40th stories" — Wikipedia (→ 160.7 m); 34 storeys plus the six-storey crown, constructed 1927–28 — LPC
  - foundation work from August 1925 — Wikipedia
  - CTBUH Skyscraper Center ("New York Life Building", id 2060): architectural 187.5 m, tip 187.5 m, roof —, highest occupied floor —, observatory —; floors 33; start 1926, completed 1928
- **Measured (footprint / OSM parts):**
  - plan from the official footprint (7,427 m²); set-backs at 22, 60, 115, 148 m and the octagon (24 m across) — OSM parts
- **Estimated or simplified:**
  - pyramid drawn to a 2.4 m finial base at 184.5 m
- **Check:** top 187.5 m vs cited 187.5 m (+0.0); wall outline at 0.6 m 7419 m² vs official 7427 m² (-0.1 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 142.6 m; hides BIN 1016880.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-22 m: 7428 / 7419; 22-60 m: 5051 / 5057; 60-115 m: 1951 / 1954; 115-148 m: 1148 / 1146; 148-152 m: 496 / 466; 152-188 m: 467 / 173.

### Williamsburgh Savings Bank Tower (`williamsburgh_savings_bank_tower`)

- **Anchor** [-73.977718, 40.685517]; **built** 1927.5 – 1929.25; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/Williamsburgh_Savings_Bank_Tower; https://s-media.nyc.gov/agencies/lpc/lp/0971.pdf (LP-0971, 1977); city footprint BIN 3059183; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - roof 512 ft (156 m), 41 floors — Wikipedia; LPC: "Soaring 512 feet"
  - "The centers of the clock faces are 430 ft high, and the faces measure 27 ft across" — Wikipedia
  - cornerstone 9 Apr 1928; topped out by the end of July 1928; opened 1 Apr 1929 — Wikipedia
  - CTBUH Skyscraper Center ("One Hanson Place", id 3598): architectural 156.06 m, tip 156.06 m, roof 156.06 m, highest occupied floor 145.39 m, observatory —; floors 42; start 1927, completed 1929
- **Measured (footprint / OSM parts):**
  - plan from the official footprint (1,649 m²); set-backs at 10, 24, 60, 69, 80, 85, 110, 115, 140, 145 m — OSM parts
- **Estimated or simplified:**
  - `built` starts at 1927.5: CTBUH gives the year only
  - dome radius 5.4 m, rise 8 m from 145 m (CTBUH: highest occupied floor 145.39 m)
- **Check:** top 156.0 m vs cited 156.0 m (+0.0); wall outline at 0.6 m 1648 m² vs official 1649 m² (-0.0 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 157.6 m; hides BIN 3059183.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-10 m: 1723 / 1715; 10-24 m: 1496 / 1497; 24-60 m: 1359 / 1364; 60-69 m: 1322 / 1327; 69-80 m: 1037 / 1042; 80-85 m: 815 / 818; 85-110 m: 359 / 361; 110-115 m: 173 / 361; 115-140 m: 136 / 154; 140-145 m: 117 / 117; 145-156 m: 84 / 66.

### One Court Square (Citicorp Building) (`one_court_square`)

- **Anchor** [-73.943869, 40.747013]; **built** 1987 – 1990; **kind** tower.
- **Sources:** https://en.wikipedia.org/wiki/One_Court_Square; city footprint BIN 4307108; OSM parts; https://www.skyscrapercenter.com/city/new-york-city (CTBUH, embedded building table).
- **Cited dimensions and dates:**
  - roof 673 ft (205.1 m), 50 floors; construction began by 1987; completed and opened 1989 — Wikipedia (the brief gives 1990)
  - CTBUH Skyscraper Center ("One Court Square", id 1651): architectural 205.13 m, tip —, roof 205.13 m, highest occupied floor —, observatory —; floors 50; start —, completed 1990
- **Measured (footprint / OSM parts):**
  - plan from the official footprint (2,418 m²) to 170 m; stepped top 170–200 m — OSM parts; the top is raised to the cited 205.1 m (OSM 200, city 192.9 m)
- **Estimated or simplified:**
  - nothing but the colour
- **Check:** top 205.1 m vs cited 205.1 m (+0.0); wall outline at 0.6 m 2418 m² vs official 2418 m² (-0.0 %), centroid offset 0.0 m, IoU 1.0; city-measured roof 192.9 m; hides BIN 4307108.
- **Set-back check** (plan area in m² above the middle of each OSM level, OSM / model): 0-170 m: 2390 / 2454; 170-178 m: 2140 / 2146; 178-185 m: 1526 / 1532; 185-192 m: 997 / 999; 192-200 m: 558 / 558.

## Known weak spots

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
