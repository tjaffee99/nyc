# Landmarks, second pass B (towers and apartment houses)

Model file `viewer/src/landmarks/nyc-more-b.ts`, export `MORE_B`. Generator/checks: `data/interim/landmarks_more_b/` (`gen.py` uses the towers' `gen_massing.build`; `check.ts` builds every mesh and prints its extent).
Footprints: NYC building footprints (BIN named per model). Levels: OpenStreetMap parts via Overture 2026-10-21.0 (ODbL). Dates and heights: Wikipedia articles (linked in each model's sources), CTBUH.

## Audit: what a visitor expects and the map lacked (192 models checked by name)
Already present (not rebuilt): UN, Lever, Seagram, MetLife, 56 Leonard, Williamsburgh Savings, Guggenheim, Met, AMNH, Lincoln Center, Riverside, Brooklyn Museum, BAM.

| # | Missing | Status |
|---|---|---|
| 1 | Time Warner Center / Deutsche Bank Center | built |
| 2 | The Plaza | built |
| 3 | The Dakota | built |
| 4 | Carnegie Hall | built (two states) |
| 5 | One57 | built |
| 6 | 53 West 53 | built |
| 7 | 35 Hudson Yards (and The Edge) | built (Edge platform not drawn) |
| 8 | The Ansonia | built |
| 9 | Oculus / WTC Transportation Hub | not built (curved steel wings; no cited dimensions gathered) |
| 10 | Jacob Javits Center | not built (footprint 64,000 m2 found, height not cited) |
| 11 | Whitney Museum (99 Gansevoort) | not built (footprint found, terrace profile not researched) |
| 12 | The Cloisters / Fort Tryon | not built |
| 13 | TWA Flight Center (JFK) | not built (no footprint matched in the file) |
| 14 | Roosevelt Island Tramway | not built |
| 15 | Intrepid | not built |
| 16 | Staten Island Ferry terminals | not built |
| 17 | Bronx County Courthouse | not built (footprint not found at the address searched) |
| 18 | Kingsbridge Armory | not built (footprint not found in the file at the searched box) |
| 19 | Apollo Theater | not built (low; 2 small footprints) |
| 20 | The Shed | not built |
| 21 | San Remo | not built |
| 22 | Belvedere Castle | not built |
| 23 | Queens Museum (1939 pavilion) | not built |
| 24 | Bronx Zoo Astor Court | not built |
| 25 | Brooklyn Public Library, Central | not built |

## Models (heights checked against the built mesh, all within 0.1 m of target)
| id | name | years | mesh height | faces | estimated |
|---|---|---|---|---|---|
| one57 | One57 | 2009.3-2014.62 | 306.0 (cited 306) | 275 | cascade drawn as OSM steps; glass colour |
| time_warner_center | Time Warner Center | 2000.85-2004.1 | 248 (230 roof + 18 lantern, cited) | 374 | lantern plan; atrium not cut |
| w53 | 53 West 53 | 2014.9-2020.12 | 320.0 (cited 320) | 164 | base 30 m; N/S lean to 60 % depth; no diagrid/spires |
| hudson_yards_35 | 35 Hudson Yards | 2015-2019.2 | 308 (300 cited roof + 8 m mechanical per footprint file) | 44 | mechanical block; slopes not drawn |
| plaza_hotel | The Plaza | 1905.5-1907.75 | 76.8 (cited 76.79) | 158 | cornice 58 m; mansard stepped; no turrets |
| carnegie_hall_1891 | Carnegie Hall as opened | 1889.4-1894.5 (end) | 34 | 16 | block height from 8 storeys |
| carnegie_hall | Carnegie Hall | 1894-1896.5 | 55.2 (footprint file 55.17) | 26 | tower position/plan; hall height |
| dakota | The Dakota | 1880.8-1884.8 | 50.9 (footprint file; cited 56 with finials) | 375 | wall 36 m; stepped roof; no gables/turrets |
| ansonia | The Ansonia | 1899.87-1904.3 | 85.3 (footprint file; no cited height found) | 518 | wall 61 m, mansard, cupolas |

Plan extents of each mesh equal the official footprint rotated to its long-edge bearing (they are built from it). Mesh extents/heights printed by `check.ts`. `npx tsc --noEmit` passes. Nothing viewed on screen.
Caveats: Carnegie Hall's 1891 state is a plain block (the studio tower's exact corner position is estimated); One57 and Time Warner Center OSM parts include small unrelated pieces merged by the generator; Ansonia height not independently cited.
