# South-west Connecticut landmarks — research notes and numeric checks

Code: `viewer/src/landmarks/ct.ts` (export `CT`, 14 models). Dates table: `data/tables/known_building_dates.ct.csv` (35 rows).
Scratch (gitignored): `data/interim/landmarks_ct/` (`fid.py` footprint → oriented rectangle, `rings.py` → `rings.json`, `ct.tmpl.ts` + `gen.py` → `ct.ts`, `dumpmesh.mjs` + `check.py` = the numeric check). Cached Wikipedia wikitext: `data/raw/landmarks_ct/wp_*.txt`.

## Sources and how they were used

- **Footprints**: Overture Maps buildings 2026-10-21.0 (`outer_building.parquet`; OpenStreetMap / Microsoft ML derived, ODbL-compatible). Each model's anchor is the lon/lat of the Overture row it replaces, and its plan is that row's ring in anchor-local metres, simplified to 0.15 m (the Overture id is in a comment above each ring in `ct.ts`). Overpass was not reachable from the build machine (connection closed; two mirrors timed out), so no OpenStreetMap 3D parts were used.
- **Dimensions and dates**: Wikipedia wikitext (CC BY-SA 4.0, facts only), the article URL in each model's `sources`. **[V]** = read in the cached wikitext in this session. Wikipedia carries few dimensions for these buildings; heights not marked [V] are estimates and say so in the model's `Model:` fact.
- The Wikipedia API (search, REST summary) rate-limited the session; only `index.php?action=raw` worked, so some article titles could not be found (Center Church, United Church, the Soldiers and Sailors Monument, the Glass House were redirects or not found). Years of the two churches come from the project brief.

## Models

| id | years | faces | cited | estimated |
|---|---|---|---|---|
| `harkness_tower` | 1917.5-1921.9 | 168 | height 66 m (216 ft) [V], 284 steps, built 1917-21 [V] | plan 11.6 m square, stage heights, turrets, crown, and the position (about ±8 m: Wikipedia's coordinate has four decimals; moved onto the High Street frontage of Branford College's footprint). Sits on Branford's footprint, replaces nothing |
| `connecticut_hall` | 1750.3-1752.9 | 56 | built 1750-52 / 1752 [V] | plan from the footprint (31.2 x 13.4 m); eave 8.4 m after Overture's 8.8 m; gambrel levels, chimneys, cupola |
| `center_church_new_haven` | 1812.4-1814.9 | 252 | years from the brief | every height (walls 10.5 m, ridge 15.5 m, steeple 46 m), portico, and the front side (toward Temple Street, inferred from the address) |
| `united_church_new_haven` | 1813.4-1815.9 | 232 | years from the brief | the same, steeple 40 m, front toward Temple Street (west) |
| `trinity_church_new_haven` | 1814.4-1816.5 | 108 | walls 38 ft = 11.6 m, nave 103 x 74 ft, tower 25 ft square and 100 ft high, pinnacles 30 ft above the roof [V]; changes of 1871 / 1884 / 1893-1930 / 1961 [V] | front side (west), flat nave roof; the chancel of 1884 shows from 1816 (footprint) |
| `sterling_memorial_library` | 1927.0-1931.3 | 160 | tower 150 ft = 45.7 m, 16 levels, finished 1930, opened April 1931 [V] | nave height 20 m; tower plan 17 x 11 m and position (±8 m, four-decimal coordinate) |
| `beinecke_library` | 1960.5-1963.5 | 72 | opened 1963, Bunshaft, six-storey stack tower inside a windowless shell on four corner piers [V] | shell height 13 m (no height read), pier and mezzanine proportions. LOW |
| `payne_whitney_gymnasium` | 1930.0-1932.5 | 172 | opened 1932, nine-storey tower [V] | block 17 m, tower 15 m square to 50 m (52.8 m with finials); the Wikipedia coordinate is to the second, so the tower is put on the nearest ground inside the footprint (17 m away). LOW |
| `yale_bowl` | 1913.6-1914.9 | 558 | opened 21 Nov 1914, Ferry, elliptical, berm of excavated fill [V] | rim height 11 m and the inner slope; the field is drawn level (the real one is sunk). LOW |
| `union_station_new_haven` | 1918.0-1920.0 | 120 | opened 1920, Cass Gilbert [V] | heights (15 m hall, 10.5 m wings), window panels. The footprint is stepped on one side, so the box is 7 % larger than it |
| `knights_of_columbus_tower` | 1966.0-1969.5 | 180 | 23 floors, completed 1969, four cylindrical corner towers [V]; 98 m from Overture's height | cylinder radius 7.2 m, glazed core 24 m square and 82 m high |
| `barnum_museum` | 1891.0-1893.1 | 123 | opened 18 Feb 1893, three storeys, stone and terra cotta [V] | height 14 m; no roof, turret or frieze. LOW |
| `glass_house_new_canaan` | 1948.5-1949.9 | 208 | 1949 | roof at Overture's 3.6 m; cylinder position and height, post spacing |
| `lockwood_mathews_mansion` | 1864.5-1868.9 | 512 | 1864-68, Second Empire, 62 rooms, 44,000 sq ft [V] | every height (12 m walls, mansard to 17.5 m, lantern and dome to 24.6 m). LOW |

All are `end: 9999`. The Soldiers and Sailors Monument, the Fish Church, the Perry Arch and the old centres of Danbury and Greenwich were not modelled (see the end).

## Numeric check (`data/interim/landmarks_ct/check.py`)

Each mesh is built with the kit; its plan is the union of the projected triangles, compared with the Overture footprints whose centroids lie in `replaces`, and its top with the cited height.

| model | top (m) | plan / footprint | centre offset | plan outside footprint |
|---|---|---|---|---|
| connecticut_hall | 14.4 | 1.077 | 0.0 m | 0 m2 |
| center_church | 46.0 | 1.021 | 0.3 m | 6 m2 |
| united_church | 40.0 | 1.027 | 0.0 m | 7 m2 |
| trinity_church | 42.4 | 1.010 | 0.1 m | 0 m2 |
| sterling | 45.7 (cited 45.7) | 1.001 | 0.0 m | 0 m2 |
| beinecke | 13.0 | 1.010 | 0.1 m | 0 m2 |
| payne_whitney | 52.8 | 1.002 | 0.0 m | 0 m2 |
| yale_bowl | 11.0 | 1.001 | 0.0 m | 0 m2 |
| union_station | 15.5 | 1.073 | 0.9 m | 96 m2 |
| knights_of_columbus | 98.0 (Overture 98.0) | 1.028 | 0.1 m | 148 m2 |
| barnum | 14.6 | 1.002 | 0.1 m | 0 m2 |
| glass_house | 4.4 | 1.045 | 0.0 m | 0 m2 |
| lockwood_mathews | 24.6 | 1.060 | 0.2 m | 8 m2 |
| harkness_tower | 66.0 (cited 66) | n/a, 130 of 135 m2 of the base inside Branford College's footprint | | |

Harkness Tower reaches the cited 66.0 m and Sterling's tower the cited 45.7 m exactly. `cd viewer && npx tsc --noEmit` reports no error in `ct.ts`. The Connecticut Hall, Union Station and KofC plans overshoot the footprint by 3-8 % because they are rectangles / cylinders over a stepped or circular-arc ring.

Not checked: nothing was rendered; colours, proportions of the estimated parts and which end of each church is its front need an eye. The Harkness, Sterling and Payne Whitney tower positions rest on rounded Wikipedia coordinates.

## Dates table (`known_building_dates.ct.csv`, 35 rows)

Footprint = the Overture row of that name inside the New Haven box (-72.945..-72.91, 41.295..41.335); `lat`/`lon` is a point guaranteed inside the polygon (`representative_point`). Years are those written in the cited article: the Old Campus article's table (Connecticut, Dwight, Street, Farnam, Durfee, Lawrence, Linsly-Chittenden, Welch, Vanderbilt, Phelps, Lanman-Wright, McClellan, Bingham), the building's own article (Battell, Woolsey, Sterling Library, Sterling Law, Art Gallery, Center for British Art, Rudolph Hall, Beinecke, Payne Whitney, KofC, Union Station, Trinity, Ingalls Rink, Stiles, Morse, Timothy Dwight), Hewitt Quadrangle (Woodbridge Hall), the Yale Repertory Theatre article (the Calvary Baptist Church of 1846). "estimated" is in the note for Branford and Saybrook (Memorial Quadrangle "completed in 1922"; construction 1917-22) and the British Art Center (1974 completed, 1977 opened). Center Church (1814) and United Church (1815) come from the brief. Not matched: Wikipedia has no "List of Yale University buildings" article under that title; Yale's own building list was not fetched.

## Not done

- Soldiers and Sailors Monument on East Rock (no Overture footprint, article not found), Perry Arch (undocumented here), the Fish Church (Overture has the Maguire Memorial Tower, 79.28 m = the 260 ft the article cites, but the church's footprint could not be told from the complex), Danbury and Greenwich centres, the lost buildings of Old Campus (a table of 15 with years exists in the Old Campus article, but they have no footprints).
- Dates for more of the 140 named Yale footprints (Hendrie, Harkness Hall, Sheffield-Sterling-Strathcona, the Peabody) and for the old centre's churches and commercial buildings.
- Front sides of the three Green churches, tower positions of Harkness, Sterling and Payne Whitney: confirm by eye.
