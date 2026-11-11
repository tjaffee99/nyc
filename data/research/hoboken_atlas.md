# Hoboken from the Sanborn atlases (round of 2026-11-12)

Files: `data/manual/atlas/hudson_hoboken_b_1891.geojson` (+ `_coverage`, `_stats`), `data/manual/atlas/hudson_hoboken_1930.geojson` (+ `_coverage`, `_stats`),
tool copy `data/manual/atlas/tools_hoboken/` (`prior.py` / `reg.py` / `view.py` for the 1891 plates, `fetch30.py` / `sheets30.py` for the 1930 sheets, `atlas.py`, `dedupe.py`,
`post.py`, `check.py`, `run_city.sh`, `layers.json`, `gcps_own.json`), work files `data/interim/atlas_hoboken/`, scans `data/raw/atlas/hoboken/` (deleted after tracing; refetch with the tools).

## Sources and licence
Library of Congress, Sanborn Maps Collection, Hudson County N.J., public domain (no known restrictions). IIIF base
`https://tile.loc.gov/image-services/iiif/service:gmd:gmd381m:g3814m:g3814hm:g3814hm_g05511189107:05511_07_1891-<sheet><L|R>` (vol. 7, 1891, 28 double plates; found from
`https://www.loc.gov/item/sanborn05511_007/?fo=json`, which answered on the second day) and `...g3814hm_g05511195107:05511_07_1951-<sheet>` (vol. 7, **1930 re-issue corrected by pasted slips to April 1951**,
`https://www.loc.gov/item/sanborn05511_034/`, 56 single sheets). User-Agent `NYCThroughTime-research/0.1`. Princeton's and NYU's catalogues were not reachable from the machine (certificate error through the proxy, not bypassed); NYPL's site is behind a bot wall; the Map Warper dump has no Hoboken plate (checked again by title).

## What was made
* `hudson_hoboken_b_1891` (map year 1891): the 11 plates of vol. 7 not in `hudson_hoboken_1891` that carry buildings (7, 11, 13-20, 25): 1175 outlines (797 frame, 374 brick, 4 stone), 1.87 km2 of plates, 108 on a standing footprint. The west side was **empty** in 1891: plates 16-18, 21-24, 26-28 show laid-out lots with a handful of sheds (plates 21-24 and 26-28 not traced; 16-18 traced and nearly empty). Plates 1-6, 12 (piers, marsh) not traced.
* `hudson_hoboken_1930` (map year **1930**): sheets 15-32, 34-42, 44-48, 52 of the 1930 re-issue (1990 outlines: 1144 frame, 841 brick, 5 stone; 2.58 km2; 339 on a standing footprint). This is the first state in which the west side (Willow Ave to the Jersey City line) and the south-west are built. Caveat for the lead: the sheets were corrected with pasted slips up to April 1951 (dated slips are not read), so a few outlines are of the 1930s-40s and some 1930 buildings pulled down by 1951 are missing; the honest reading of `map_year` is "stood by 1930 (a few by 1951)".

## Registration (no control points exist: street crossings)
Each plate: both halves (or the single sheet) fetched at 50 % (0.1 m/px), the pixel of 4-6 street crossings read off a 1500 / 700 px preview with today's street names, ground position from today's street centre lines (`streets.py`), affine fit; then `refine_buildings` (match to today's footprints). 1891: preview with the prior street lines to name crossings (`prior.py`, `reg.py`). 1930: `sheets30.py` (affine of the good sheets used where the crossings were collinear or one was wrong: sheets 21, 24, 44, 46 fix rotation and scale and fit the shift only).
Residual of the crossings (m): 1891-b plates 0.2-6 (plate 17 one point 6 m, 15 and 16 up to 5); 1930 sheets 0.1-2.7 except 47 (2.5-6.2, left free: the one window looked at is aligned). Leave-one-out and coinciding outlines per plate are in the tables.
Street-line check (outlines whose area is more than half within 8 m of a street centre line, `check.py`): 1891-b 13 of 1,175 (1.1 %); 1930 59 of 1,966 (3.0 %) before post-filtering. The lead's skip rule is far from met.

Dropped / not traced: sheet 33 (outside Hoboken), 43 (two collinear crossings, 4 outlines), 49 and 50 (60 ft to the inch, shipyard piers: needs another scale), 51 (partly "no longer corrected in this map"), 53, 54 (crossings did not agree: 2-23 m), 55, 56 (empty lots), sheets 1-14 (piers and the Lackawanna yards), skeleton sheets 's'. Plates 44 (1 coinciding outlines, offset 6 m) and 46, 52 (2 each) are verified by their crossings only. Andrew Jackson Gardens (1941, pasted on sheets 34, 35, 37) is blue and was not traced (`post.py` filter found nothing to drop).

## By eye (overlay crops, `atlas.py overlay`)
1891-b plate 19 (150 m): lots traced house by house, runs of attached houses merged, outbuildings missed. 1930 sheet 26 (110 m, two blocks), sheet 16 (140 m: Washington St, rows of brick row houses come out as strips of 3-8 houses), sheet 47 (140 m, Park / Garden 9th-10th: same), sheet 23 (150 m, final layer: about 80 % of drawn buildings traced, pale yellow lots under pasted slips and blue (non-combustible) buildings such as the Grunstein meat-packing plant are missed). Not looked at: 24 of the 33 1930 sheets and 8 of the 11 1891 plates.

## Known failures
Rows of attached houses are one outline (not individual lots); blue-coloured buildings are almost not exported (5 in the whole 1930 layer); washed / slip-covered lots are missed; gasholders and tanks not traced; the book gutter cuts a few 1891 outlines; no storeys read.

## Plate tables
### hudson_hoboken_b_1891
| sheet | control points | mpp | outlines (frame/brick/stone) | on a standing footprint (IoU>0.5) | median offset m | note |
|---|---|---|---|---|---|---|
| 13 | 5 (affine, leave-one-out 7.4 m) | 0.1 | 202 (133/47/1) | 21 (12 %) | 1.55 | |
| 14 | 5 (affine, leave-one-out 4.4 m) | 0.1 | 181 (118/44/0) | 10 (6 %) | 2.54 | |
| 19 | 5 (affine, leave-one-out 0.6 m) | 0.101 | 188 (164/15/2) | 13 (7 %) | 2.29 | |
| 20 | 5 (affine, leave-one-out 4.0 m) | 0.099 | 164 (133/23/1) | 23 (15 %) | 1.73 | |
| 25 | 5 (affine, leave-one-out 0.5 m) | 0.1 | 121 (95/12/0) | 4 (4 %) | 2.91 | |
| 7 | 5 (affine, leave-one-out 1.2 m) | 0.101 | 139 (50/68/0) | 10 (8 %) | 0.89 | |
| 11 | 5 (affine, leave-one-out 9.3 m) | 0.102 | 43 (1/38/0) | 2 (5 %) | 0.7 | |
| 15 | 5 (affine, leave-one-out 9.2 m) | 0.1 | 129 (44/59/0) | 13 (13 %) | 1.65 | |
| 16 | 5 (affine, leave-one-out 8.2 m) | 0.1 | 86 (11/58/0) | 12 (17 %) | 0.85 | |
| 17 | 5 (affine, leave-one-out 9.5 m) | 0.104 | 50 (32/9/0) | 0 (0 %) |  | |
| 18 | 5 (affine, leave-one-out 5.7 m) | 0.098 | 27 (18/1/0) | 0 (0 %) |  | |

### hudson_hoboken_1930
| sheet | control points | mpp | outlines (frame/brick/stone) | on a standing footprint (IoU>0.5) | median offset m | note |
|---|---|---|---|---|---|---|
| 15 | 5 (affine, leave-one-out 2.3 m) | 0.1 | 36 (10/19/1) | 2 (7 %) | 2.34 | |
| 16 | 5 (affine, leave-one-out 2.3 m) | 0.103 | 56 (9/42/0) | 1 (2 %) | 2.82 | |
| 17 | 5 (affine, leave-one-out 1.6 m) | 0.103 | 49 (20/25/0) | 5 (11 %) | 1.91 | |
| 18 | 5 (affine, leave-one-out 3.2 m) | 0.103 | 53 (11/40/0) | 19 (37 %) | 1.59 | |
| 19 | 5 (affine, leave-one-out 3.3 m) | 0.103 | 48 (5/41/0) | 14 (30 %) | 2.76 | |
| 20 | 5 (affine, leave-one-out 1.1 m) | 0.102 | 41 (3/36/0) | 2 (5 %) | 2.94 | |
| 21 | 4 (affine, leave-one-out 0.0 m) | 0.103 | 24 (0/24/0) | 5 (21 %) | 2.86 | |
| 22 | 5 (affine, leave-one-out 1.8 m) | 0.104 | 83 (64/18/1) | 8 (10 %) | 2.25 | |
| 23 | 6 (affine, leave-one-out 1.7 m) | 0.101 | 113 (84/25/1) | 14 (13 %) | 1.94 | |
| 24 | 4 (affine, leave-one-out 0.0 m) | 0.103 | 65 (41/18/0) | 7 (12 %) | 1.54 | |
| 25 | 6 (affine, leave-one-out 1.1 m) | 0.106 | 70 (36/28/0) | 4 (6 %) | 1.86 | |
| 26 | 5 (affine, leave-one-out 3.3 m) | 0.103 | 110 (85/22/0) | 28 (26 %) | 1.78 | |
| 27 | 5 (affine, leave-one-out 1.7 m) | 0.104 | 107 (81/26/0) | 11 (10 %) | 2.09 | |
| 28 | 5 (affine, leave-one-out 2.2 m) | 0.103 | 78 (31/40/0) | 18 (25 %) | 1.34 | |
| 29 | 5 (affine, leave-one-out 2.5 m) | 0.103 | 86 (61/23/0) | 9 (11 %) | 1.68 | |
| 30 | 5 (affine, leave-one-out 1.0 m) | 0.102 | 65 (41/21/0) | 7 (11 %) | 1.16 | |
| 31 | 5 (affine, leave-one-out 1.3 m) | 0.103 | 91 (62/26/0) | 19 (22 %) | 1.69 | |
| 32 | 5 (affine, leave-one-out 1.5 m) | 0.102 | 83 (24/51/0) | 8 (11 %) | 2.59 | |
| 34 | 5 (affine, leave-one-out 2.5 m) | 0.104 | 58 (48/9/0) | 14 (25 %) | 1.54 | |
| 35 | 5 (affine, leave-one-out 3.5 m) | 0.105 | 70 (64/4/1) | 1 (1 %) | 1.25 | |
| 36 | 5 (affine, leave-one-out 1.4 m) | 0.104 | 111 (84/25/0) | 29 (27 %) | 1.13 | |
| 37 | 5 (affine, leave-one-out 2.6 m) | 0.103 | 61 (48/9/0) | 6 (10 %) | 3.19 | |
| 38 | 5 (affine, leave-one-out 2.5 m) | 0.104 | 120 (92/27/0) | 34 (29 %) | 1.02 | |
| 39 | 5 (affine, leave-one-out 2.3 m) | 0.104 | 17 (11/6/0) | 0 (0 %) |  | |
| 40 | 5 (affine, leave-one-out 2.9 m) | 0.105 | 49 (33/13/1) | 12 (26 %) | 2.64 | |
| 41 | 5 (affine, leave-one-out 1.2 m) | 0.104 | 60 (31/26/0) | 16 (28 %) | 1.92 | |
| 42 | 5 (affine, leave-one-out 1.0 m) | 0.103 | 71 (21/47/0) | 16 (24 %) | 1.28 | |
| 44 | 4 (affine, leave-one-out 0.0 m) | 0.103 | 26 (15/9/0) | 1 (4 %) | 6.08 | |
| 45 | 5 (affine, leave-one-out 3.2 m) | 0.104 | 31 (5/24/0) | 9 (31 %) | 2.25 | |
| 46 | 4 (affine, leave-one-out 0.0 m) | 0.103 | 30 (20/10/0) | 2 (7 %) | 1.96 | |
| 47 | 5 (affine, leave-one-out 14.2 m) | 0.106 | 42 (4/35/0) | 3 (8 %) | 2.79 | |
| 48 | 5 (affine, leave-one-out 7.5 m) | 0.105 | 74 (2/71/0) | 13 (18 %) | 1.19 | |
| 52 | 4 (affine, leave-one-out 0.0 m) | 0.103 | 31 (16/14/0) | 2 (7 %) | 3.29 | |

## Coverage (today's Hoboken built-up area = today's footprints in the city outline, buffered 20 m, 2.53 km2)
`hudson_hoboken_1891` 19.7 %, `_b_1891` 57.0 %, `_1930` 80.6 %; all three together 84.7 % (plates' extents, including empty lots). Not covered: the piers and waterfront east of Hudson Street's rail and shipyards (sheets 1-14, 49-50), the north end beyond 14th St (51, 53-56).
Outlines in the west side (west of Clinton Street): 630 (1891-b), 1,098 (1930, before dedupe of the final file counts the same order). South-west (south of 2nd Street, west of Hudson Street): 711 (1891-b), 771 (1930); the old 1891 layer adds 48 there.

## Not done
The northern towns (Weehawken, Union City / West Hoboken / Union Hill, West New York, Guttenberg: LoC `sanborn05511_008` 1900 and `_018` 1910, 148 / 104 sheets) were not started: the budget went to Hoboken. Both volumes are reachable with the same method (item JSON gives the IIIF names).
