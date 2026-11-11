# New Haven landmarks, second round — research notes and numeric checks

Code: `viewer/src/landmarks/new-haven.ts` (export `NEW_HAVEN`, 18 models). Scratch: `data/research/landmarks_new_haven_build/`
(`rings.py` footprint -> anchor-local ring, `dumpmesh.mjs` + `check.py` = the numeric check, `check_out.txt` its output, `fetch.sh` + `wp/` the cached
Wikipedia wikitext read in this session, `fp.py` footprints near a point). Footprints: `data/interim/counties/ct_south_central_connecticut.parquet`
(Overture Maps 2026-10-21.0, ODbL-compatible); the anchor is the footprint's lon/lat rounded to 6 decimals, the ring its outline in the kit's
local metres (x east, y north), simplified to 0.25 m. Dimensions and dates: Wikipedia wikitext (`index.php?action=raw`), all pages opened in this
session; **[V]** = read there. Wikipedia carries heights only for the tall buildings (the list `List_of_tallest_buildings_in_New_Haven` and the
infobox of each), so every other height is an estimate and says so in `facts.Model` (marked LOW). The Wikipedia API was rate limited; titles that
404 were retried under their real names.

## Models

| id | built / end | faces | cited [V] | estimated |
|---|---|---|---|---|
| `connecticut_financial_center` | 1988-1990.5 | 330 | 383 ft = 117 m, 26 floors, completed 1990, Crang and Boake | set-backs, pyramidal roof, start (1988) |
| `state_street_360` | 2008.9-2010.2 | 46 | 338 ft = 103 m, 31 floors, started 1 Dec 2008, completed 2010 | podium 27 m, which part is slab / second block. LOW |
| `union_new_haven_trust` | 1925.5-1927.5 | 263 | 242 ft = 73.8 m, 1927, Cross and Cross, cupola echoing United Church | base, set-back stages, cupola proportions, start |
| `st_marys_new_haven` | 1869-1874.9, end 1981.5 | 88 | dedicated 1874, James Murphy; spire never completed until 1982 | wall 14 m, nave ridge 26 m, tower 32 m with hipped roof, front end (inferred), start. LOW |
| `st_marys_spire_new_haven` | 1981.5-1982.9 | 102 | 230 ft = 70 m tip (list); spire added in the 1982 renovation | the same body; taper of the spire |
| `kline_tower` | 1962-1966.5 | 68 | 250 ft = 76 m roof, 16 floors, built 1962-66, Philip Johnson | top band, colour |
| `ingalls_rink` | 1953.5-1958.9 | 450 | built 1953-58, opened 3 Dec 1958, 90 m arch, max ceiling height 23 m, Saarinen | roof is a lofted hump to 23 m (ceiling height used as roof height); 4 m wall |
| `woolsey_hall` | 1899.5-1901.5 | 229 | opened 1901, Carrere and Hastings, 2,650 seats | every height (walls 18 m, roof 27.6 m), the SW six-column front. LOW |
| `battell_chapel` | 1874.5-1876.9 | 111 | completed 1876, Russell Sturgis Jr., High Victorian Gothic | heights, nave extent, tower position. LOW |
| `rudolph_hall` | 1958-1963.85 | 628 | dedicated 8 Nov 1963, Paul Rudolph, 7 storeys, 30+ levels, ribbed concrete | stepped massing and all heights (31 m). LOW |
| `yale_center_british_art` | 1969-1977.3 | 46 | opened 15 Apr 1977, Kahn, four floors; height 16.7 m is the footprint's | base band, two courtyards, start |
| `pirelli_building_hotel_marcel` | 1968-1970.5 | 60 | 1968-70, Breuer and Gatje, 2-storey base, 2-storey gap on 3 piers, 5-storey upper | storey height (about 4 m, 36 m in all), pier sizes. LOW |
| `crown_towers` | 1965.5-1967.5 | 30 | 222 ft = 67.7 m, 22 floors, 1967 | base, parapet, start |
| `swensen_tower_hgs` | 1930-1932.75 | 120 | opened 29 Sep 1932, J. G. Rogers, 208 ft = 63 m (list; the article says "200-foot tower"), 14 floors | plan 13 m square, stages, turrets, position (+-20 m from a coordinate to the second). LOW |
| `new_haven_coliseum` | 1968-1972.75, end 2007.05 | 508 | Kevin Roche, 1968-72, imploded 20 Jan 2007, 11,497 seats, 4.5 acres, garage on top, coordinate 41.30249 -72.925454 | plan 120 x 92 m and all heights (no footprint is left). LOW |
| `soldiers_sailors_monument_east_rock` | 1886-1887.46 | 152 | work 1886, dedicated 17 June 1887, 112 ft = 34 m (East Rock article; East Rock Park says 122 ft), coordinate 41.32725 -72.90462, red granite shaft, Angel of Peace | all proportions and the 45 degree turn (after the inscriptions' SW/SE/NE/NW faces) |
| `church_street_195` | 1972-1974.5 | 165 | 270 ft = 82.3 m, 18 floors, 1974, William Pederson, second tallest when finished | base, top stage, start |
| `smilow_cancer_hospital` | 2006-2009.2 | 104 | 237 ft = 72 m, 13 floors, 2008 (list) | podium 22 m and the set-back tower. LOW |

Sources: https://en.wikipedia.org/wiki/ plus `List_of_tallest_buildings_in_New_Haven`, `Connecticut_Financial_Center`, `360_State_Street`,
`Union_and_New_Haven_Trust_Building`, `St._Mary's_Church_(New_Haven,_Connecticut)`, `Kline_Biology_Tower`, `Ingalls_Rink`, `Woolsey_Hall`,
`Battell_Chapel`, `Rudolph_Hall`, `Yale_Center_for_British_Art`, `Hotel_Marcel`, `Crown_Towers_(New_Haven,_Connecticut)`, `Humanities_Quadrangle`,
`New_Haven_Coliseum`, `Soldiers'_and_Sailors'_Monument_(New_Haven)`, `East_Rock`, `East_Rock_Park`, `195_Church_Street`, `Yale_New_Haven_Hospital`.
Footprint ids (Overture, first 8 characters): CFC aae0fa32, 360 State 56eba437, Union Trust 1612ac6e (labelled Wells Fargo), St Mary's 4b5f3877,
Kline 8c16abc7, Ingalls 246ac9b8, Woolsey 32000413, Battell c501f924, Rudolph a499f893, YCBA 6605d564, Marcel 2ac069d8, Crown Towers d1084d5f
(8 High Street; e5376f73 is a different footprint with the same name), Swensen tower sits in Humanities Quadrangle cae0084c, 195 Church 7a060433
(labelled KeyBank), Smilow 1b782bfc.

## Numeric check (`check.py`, output in `check_out.txt`)

Plan = union of the model's projected triangles against the union of the footprints it replaces; top = highest vertex against the cited figure.

| model | top (m) | cited | plan / footprint | outside footprint |
|---|---|---|---|---|
| connecticut_financial_center | 116.7 | 116.7 | 1.000 | 0 m2 |
| state_street_360 | 103.0 | 103.0 | 1.000 | 0 |
| union_new_haven_trust | 73.8 | 73.8 | 1.000 | 0 |
| st_marys_new_haven / spire | 36.0 / 70.1 | 70.1 (tip) | 1.030 | 15 m2 |
| kline_tower | 76.2 | 76.2 | 1.006 | 0 |
| ingalls_rink | 23.0 | 23 | 1.000 | 0 |
| woolsey_hall | 27.6 | none | 1.038 | 2 m2 |
| battell_chapel | 40.0 | none | 1.004 | 0 |
| rudolph_hall | 31.0 | none | 1.029 | 18 m2 |
| yale_center_british_art | 16.7 | footprint's | 0.919 (two courtyards cut out) | 0 |
| pirelli_building_hotel_marcel | 36.0 | none | 1.003 | 0 |
| crown_towers | 67.7 | 67.7 | 1.010 | 0 |
| church_street_195 | 82.3 | 82.3 | 1.010 | 9 m2 |
| smilow_cancer_hospital | 72.0 | 72.0 | 1.002 | 0 |

Models with no `replaces` (the tower of the Humanities Quadrangle, the Coliseum, the monument) were checked only for finite vertices and top
(63.4 / 29.1 / 34.1 m); the Swensen tower's point lies 7 m inside the Humanities Quadrangle ring; the Coliseum's site is now "Anthem at Square 10".
No picture of any model was looked at (no GPU here).

## Not done

City Hall (Henry Austin, 1861; clock tower demolished in the 1950s), the Art Gallery (Kahn 1953 / Swartwout 1928), the Peabody Museum (dedicated
December 1925), Morse and Ezra Stiles Colleges (Saarinen, 1961; their footprints are 200-vertex outlines with courtyards, and no height was read),
Grove Street Cemetery's Egyptian gate (1845; no position better than the cemetery coordinate), the Eli / SNET building (no footprint could be matched
to 227 Church Street), the Free Public Library, Hotel Taft (the Wikipedia title leads to New York's Taft), Phelps Gate, Sheffield-Sterling-Strathcona
Hall (pages not found under the titles tried).

## Errors seen in the existing models (ct.ts, not edited)

- `harkness_tower`: the anchor (-72.929515, 41.309354) lies 47.5 m east and 35.1 m south of Branford College's footprint anchor, i.e. outside the
  footprint (about 10 m beyond its south-east edge, in High Street) and 16 m from the nearest protrusion of the ring that looks like the tower base
  (a 12.3 x 8 m bump, centre about (48.1, -19.0) in Branford's frame, footprint e93345eb). The base is 11.6 m square for 66 m (slenderness 5.7) in a
  pale stone colour (#B3A58C) with no wall mass beside it; the pale needle reads as a thin spike next to the dark flat extrusion of the college.
  Suggest: move the anchor onto the bump (+16 m north-north-west), widen the base to about 12.3 m and darken the stone.
