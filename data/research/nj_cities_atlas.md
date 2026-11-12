# Paterson and Newark from the Sanborn atlases (round of 2026-11-12)

Files: `data/manual/atlas/passaic_paterson_1915.geojson` and `essex_newark_1908.geojson` (each with `_coverage.geojson`, `_stats.json`), tools `data/manual/atlas/tools_nj_cities/`
(`fetch.py` sheet download, `njc.py` trace / mask-match registration / overlays, `regm.py` registration by street crossings, `chk.py` registration check, `finalize.py` acceptance + export, `build_foot.py`; `atlas.py` is the Hoboken copy with new paths),
work files `data/interim/atlas_nj_cities/` (kept small: traced outlines per sheet, `chk.json`, logs), scans `data/raw/atlas/nj_cities/` (deleted after tracing; refetch with `fetch.py`).

## Sources and licence
Library of Congress, Sanborn Maps Collection, public domain (no known restrictions). Item JSON `https://www.loc.gov/item/<id>/?fo=json` gives the IIIF names; sheets at 50 % (0.1 m per pixel, 50 ft to the inch), User-Agent `NYCThroughTime-research/0.1`.
* Paterson 1915: `sanborn05590_004` (vol. 1, sheets 1-99, the congested district and the east side; key map = sheet `0000`). Vols 2-3 (`_005`, `_006`, sheets 101-296), the 1899 (`_002`, `_003`) and 1887 (`_001`) volumes were not traced.
* Newark 1908: `sanborn05571_008` (vol. 3, 1908-09, "Volume Three": north and central Newark, the Central / North Ward, sheets 1-89; key map = sheet `0000`). Vols 1 (Ironbound, `_006`), 2 (`_007`), 4-5 (`_009`, `_010`) and the 1892 and 1926-30 editions were not touched.

## Registration (no control points exist)
Two methods; every sheet was then **checked** against standing buildings (`chk.py`).
1. *Mask match* (Paterson 46 sheets): the traced building mask is matched to a raster of today's Overture footprints (normalised cross-correlation, rotation, scale 0.098-0.104, shift), restricted to a prior of +-80-90 m around the sheet's place on the atlas key map (the key map is a street map: its sheet numbers were read off and a similarity to ground fitted on sheets 7, 8, 6, 12, 17, 22, 27, 30: residuals 11-36 m), then `refine_buildings`. Sheets are rotated by up to +-30 degrees on the page. Without a prior it fails (false matches a block away); in Newark's cleared Central Ward it fails altogether.
2. *Street crossings* (Newark, sheets 47, 50, 52, 56-59, 63-66): crossings read off a 700 px view of the sheet with today's street names (Overture), similarity fit, then `refine_buildings`. Residuals are in the table; sheets 59, 63, 66 had crossings 10-25 m off (a street renamed or moved), the building match then moved them 1-4 m and the check below accepts them.
3. *Check* (`chk.py`): the share of traced area lying on today's footprints at the fit, against the mean share on shifts of 12-45 m (the ring), and the best shift within 15 m. **verified**: ratio >= 1.5 and best shift <= 3 m; **consistent**: ratio >= 1.2 and best shift <= 2.5 m (the optimum sits at the fit but dense blocks make the ring high: unproven, not disproved); **street crossings**: >= 4 crossings, residual <= 2 m, leave-one-out <= 3 m, scale 0.097-0.103 (used for Newark 47, whose ground is almost all cleared: 14 % of its area on today's footprints). Everything else was left out. A 20-24 % share of outlines on street centre lines removed five Paterson sheets of the consistent tier (38, 42, 23, 36, 86).

Street-line check (outlines whose area is mostly within 8 m of a centre line, `check.py`): Paterson 395 of 6,201 (6.4 %; Hoboken had 1-3 %: Paterson's lots are narrow and its streets 12-15 m), Newark 12 of 1,908 (0.6 %). Windows looked at over the scan: Paterson sheets 8, 7, 6 (first fits), 15, 16, 4, 3, 5, 9, 10, 11, 13, 14, 18 (footprints over the sheet; 3, 5, 10, 11, 13 were then left out), 7 and 32 (traced outlines over the scan), Newark 56 and 58 (traced outlines and footprints over the scan: the outlines sit on the lots). Not looked at: the other 40 Paterson and 8 Newark sheets (numbers only).

## What was made
* `passaic_paterson_1915` (map year 1915): **53 sheets**, **6201 outlines** (5545 frame, 655 brick, 1 stone), 1133 on a standing footprint, **4.47 km2** of sheets (22.6 % of Paterson's built area of today: footprints buffered 20 m inside the city outline, 17.6 km2). Tiers: {'verified': 38, 'consistent': 15, 'street crossings': 0}.
* `essex_newark_1908` (map year 1908): **11 sheets**, **1908 outlines** (1755 frame, 153 brick), 448 on a standing footprint, **1.06 km2** (2.5 % of Newark's built area of today, 35.9 km2 city outline incl. port and airport). Tiers: {'verified': 10, 'consistent': 0, 'street crossings': 1}.

## Sheets, Paterson 1915
| sheet | how placed | outlines exported | on a standing footprint (IoU>0.5) | overlap check: share on today / ring, ratio, best shift m | tier |
|---|---|---|---|---|---|
| 8 | mask match to footprints (rot 0.0, scale 0.099) + building match (shift, [0.12, 0.06] m) | 88 | 5 (6%) | 0.73 / 0.42, 1.74, [1, 0] | verified |
| 6 | mask match to footprints (rot 29.0, scale 0.100) + building match (shift, [-0.22, -0.02] m) | 59 | 6 (10%) | 0.8 / 0.533, 1.5, [0, 0] | verified |
| 7 | mask match to footprints (rot -2.0, scale 0.100) + building match (shift, [-0.07, -0.13] m) | 83 | 5 (6%) | 0.803 / 0.526, 1.53, [0, 0] | verified |
| 9 | mask match to footprints (rot 25.5, scale 0.100) + building match (shift, [-0.4, 0.11] m) | 56 | 2 (4%) | 0.66 / 0.429, 1.54, [-1, 0] | verified |
| 11 | mask match to footprints (rot 3.0, scale 0.096) + building match (shift, [-0.09, -0.2] m) | 291 | 1 (0%) | 0.183 / 0.117, 1.56, [1, 0] | verified |
| 12 | mask match to footprints (rot 26.0, scale 0.101) + building match (affine, [-0.02, -0.06] m) | 202 | 30 (15%) | 0.564 / 0.274, 2.06, [0, 0] | verified |
| 16 | mask match to footprints (rot -1.5, scale 0.100) + building match (shift, [0.77, -2.12] m) | 138 | 5 (4%) | 0.497 / 0.348, 1.43, [-1, 0] | consistent |
| 17 | mask match to footprints (rot 12.5, scale 0.100) + building match (shift, [0.39, -0.03] m) | 102 | 6 (6%) | 0.755 / 0.37, 2.04, [0, 0] | verified |
| 18 | mask match to footprints (rot -2.0, scale 0.098) | 118 | 0 (0%) | 0.467 / 0.376, 1.24, [1, -2] | consistent |
| 3 | mask match to footprints (rot -2.0, scale 0.104) | 130 | 2 (2%) | 0.259 / 0.188, 1.38, [0, 0] | consistent |
| 4 | mask match to footprints (rot 0.5, scale 0.103) + building match (shift, [-1.99, -0.17] m) | 124 | 0 (0%) | 0.467 / 0.37, 1.26, [1, 0] | consistent |
| 14 | mask match to footprints (rot 0.0, scale 0.103) | 209 | 1 (0%) | 0.328 / 0.236, 1.39, [0, -1] | consistent |
| 15 | mask match to footprints (rot -2.0, scale 0.098) + building match (shift, [2.04, 0.93] m) | 103 | 6 (6%) | 0.387 / 0.24, 1.61, [-1, -1] | verified |
| 20 | mask match to footprints (rot -18.0, scale 0.096) | 47 | 0 (0%) | 0.644 / 0.493, 1.31, [0, 0] | consistent |
| 22 | mask match to footprints (rot 0.0, scale 0.101) + building match (affine, [0.01, -0.02] m) | 134 | 47 (35%) | 0.675 / 0.303, 2.22, [0, 0] | verified |
| 25 | mask match to footprints (rot -6.0, scale 0.096) + building match (shift, [1.03, -2.06] m) | 94 | 0 (0%) | 0.355 / 0.252, 1.41, [-1, 2] | consistent |
| 26 | mask match to footprints (rot -5.5, scale 0.096) | 143 | 2 (1%) | 0.392 / 0.299, 1.31, [1, 0] | consistent |
| 27 | mask match to footprints (rot -12.5, scale 0.100) + building match (affine, [-0.02, 0.02] m) | 155 | 88 (57%) | 0.901 / 0.295, 3.06, [0, 0] | verified |
| 29 | mask match to footprints (rot 41.5, scale 0.096) + building match (shift, [1.82, 1.06] m) | 155 | 1 (1%) | 0.468 / 0.386, 1.21, [-1, 0] | consistent |
| 30 | mask match to footprints (rot -8.5, scale 0.100) + building match (affine, [0.02, 0.0] m) | 144 | 111 (77%) | 0.936 / 0.271, 3.46, [0, 0] | verified |
| 31 | mask match to footprints (rot -1.0, scale 0.101) + building match (shift, [0.61, -0.58] m) | 146 | 24 (16%) | 0.529 / 0.298, 1.78, [0, 0] | verified |
| 32 | mask match to footprints (rot -0.5, scale 0.100) + building match (shift, [-0.49, -0.37] m) | 190 | 57 (30%) | 0.654 / 0.302, 2.16, [0, 0] | verified |
| 33 | mask match to footprints (rot -2.0, scale 0.101) + building match (shift, [-0.07, 0.27] m) | 192 | 64 (33%) | 0.669 / 0.272, 2.46, [0, 0] | verified |
| 34 | mask match to footprints (rot -2.5, scale 0.100) + building match (affine, [-0.16, 0.12] m) | 210 | 108 (51%) | 0.749 / 0.289, 2.6, [0, 0] | verified |
| 35 | mask match to footprints (rot -20.0, scale 0.098) + building match (shift, [-0.65, -0.74] m) | 50 | 1 (2%) | 0.543 / 0.381, 1.42, [0, 0] | consistent |
| 39 | mask match to footprints (rot 0.0, scale 0.104) + building match (shift, [1.57, 0.21] m) | 123 | 12 (10%) | 0.595 / 0.341, 1.74, [-2, 0] | verified |
| 40 | mask match to footprints (rot -2.5, scale 0.101) + building match (shift, [-0.29, 0.56] m) | 95 | 10 (10%) | 0.6 / 0.325, 1.85, [1, -2] | verified |
| 41 | mask match to footprints (rot 1.0, scale 0.097) | 124 | 1 (1%) | 0.403 / 0.276, 1.46, [-1, 0] | consistent |
| 43 | mask match to footprints (rot -4.0, scale 0.100) + building match (shift, [0.14, -0.12] m) | 103 | 3 (3%) | 0.234 / 0.114, 2.05, [-1, 0] | verified |
| 44 | mask match to footprints (rot -32.0, scale 0.100) + building match (shift, [0.78, -1.41] m) | 112 | 10 (9%) | 0.454 / 0.209, 2.18, [0, 1] | verified |
| 45 | mask match to footprints (rot -4.0, scale 0.100) + building match (shift, [-0.18, -0.2] m) | 173 | 64 (37%) | 0.738 / 0.244, 3.02, [0, 0] | verified |
| 46 | mask match to footprints (rot -4.5, scale 0.100) | 63 | 6 (10%) | 0.544 / 0.359, 1.52, [0, 0] | verified |
| 48 | mask match to footprints (rot -6.0, scale 0.101) + building match (shift, [-0.45, 0.06] m) | 121 | 36 (30%) | 0.652 / 0.359, 1.82, [0, 0] | verified |
| 52 | mask match to footprints (rot -4.0, scale 0.102) | 58 | 1 (2%) | 0.498 / 0.345, 1.44, [0, -1] | consistent |
| 54 | mask match to footprints (rot -5.0, scale 0.098) | 52 | 1 (2%) | 0.512 / 0.28, 1.83, [0, 0] | verified |
| 55 | mask match to footprints (rot 5.0, scale 0.096) | 93 | 0 (0%) | 0.47 / 0.33, 1.43, [0, 1] | consistent |
| 57 | mask match to footprints (rot -9.5, scale 0.098) | 81 | 1 (1%) | 0.401 / 0.288, 1.39, [-1, 1] | consistent |
| 62 | mask match to footprints (rot 2.5, scale 0.104) | 114 | 1 (1%) | 0.41 / 0.273, 1.5, [1, 1] | verified |
| 63 | mask match to footprints (rot -10.0, scale 0.103) | 123 | 2 (2%) | 0.397 / 0.262, 1.51, [0, 1] | verified |
| 64 | mask match to footprints (rot -4.0, scale 0.104) | 90 | 2 (2%) | 0.389 / 0.259, 1.5, [-1, 0] | verified |
| 65 | mask match to footprints (rot -8.0, scale 0.097) + building match (shift, [0.22, -0.24] m) | 79 | 3 (4%) | 0.549 / 0.298, 1.84, [0, 1] | verified |
| 67 | mask match to footprints (rot -9.0, scale 0.100) + building match (shift, [0.24, 0.0] m) | 167 | 78 (47%) | 0.808 / 0.248, 3.27, [0, 0] | verified |
| 68 | mask match to footprints (rot -8.5, scale 0.100) + building match (shift, [-0.27, 0.56] m) | 155 | 83 (54%) | 0.908 / 0.27, 3.36, [0, 0] | verified |
| 69 | mask match to footprints (rot -8.5, scale 0.101) + building match (shift, [-0.04, -0.2] m) | 85 | 49 (58%) | 0.8 / 0.257, 3.11, [0, 0] | verified |
| 70 | mask match to footprints (rot -8.0, scale 0.101) + building match (shift, [0.3, 0.38] m) | 154 | 99 (64%) | 0.858 / 0.231, 3.71, [0, 0] | verified |
| 71 | mask match to footprints (rot -8.5, scale 0.106) | 131 | 2 (2%) | 0.358 / 0.266, 1.35, [-1, 0] | consistent |
| 72 | mask match to footprints (rot 0.0, scale 0.100) | 67 | 1 (2%) | 0.377 / 0.247, 1.52, [-1, 0] | verified |
| 81 | mask match to footprints (rot -10.5, scale 0.096) + building match (shift, [-0.09, -2.68] m) | 86 | 5 (6%) | 0.519 / 0.286, 1.82, [0, 1] | verified |
| 82 | mask match to footprints (rot -8.5, scale 0.101) + building match (shift, [0.38, 0.49] m) | 133 | 85 (64%) | 0.899 / 0.275, 3.27, [0, 0] | verified |
| 85 | mask match to footprints (rot 22.5, scale 0.096) | 65 | 1 (2%) | 0.502 / 0.318, 1.58, [1, 0] | verified |
| 94 | mask match to footprints (rot -1.0, scale 0.105) | 68 | 3 (4%) | 0.438 / 0.282, 1.55, [0, 1] | verified |
| 47 | mask match to footprints (rot -34.5, scale 0.096) + building match (shift, [2.93, 2.36] m) | 71 | 2 (3%) | 0.282 / 0.15, 1.88, [0, -2] | verified |
| 50 | mask match to footprints (rot -4.5, scale 0.104) + building match (shift, [-2.2, -0.39] m) | 52 | 0 (0%) | 0.525 / 0.306, 1.72, [0, 1] | verified |

Left out (traced but not placed, or too few outlines): 10 (left out: registration not confirmed (overlap ratio 1.02, best shift [), 5 (left out: registration not confirmed (overlap ratio 1.16, best shift [), 2 (left out: registration not confirmed (overlap ratio 0.84, best shift [), 13 (left out: registration not confirmed (overlap ratio 1.42, best shift [), 19 (left out: registration not confirmed (overlap ratio 1.29, best shift [), 21 (left out: registration not confirmed (overlap ratio 1.20, best shift [), 23 (left out: consistent tier only and 20-24 % of its outlines lie on toda), 24 (left out: registration not confirmed (overlap ratio 1.16, best shift [), 28 (left out: registration not confirmed (overlap ratio 1.67, best shift [), 36 (left out: consistent tier only and 20-24 % of its outlines lie on toda), 38 (left out: consistent tier only and 20-24 % of its outlines lie on toda), 42 (left out: consistent tier only and 20-24 % of its outlines lie on toda), 51 (left out: registration not confirmed (overlap ratio 1.28, best shift [), 53 (left out: registration not confirmed (overlap ratio 1.04, best shift [), 58 (left out: too few outlines to check (too few outlines)), 59 (left out: too few outlines to check (too few outlines)), 61 (left out: registration not confirmed (overlap ratio 1.46, best shift [), 86 (left out: consistent tier only and 20-24 % of its outlines lie on toda), 87 (left out: too few outlines to check (too few outlines)), 88 (left out: too few outlines to check (too few outlines)), 89 (left out: too few outlines to check (too few outlines)), 90 (left out: registration not confirmed (overlap ratio 0.81, best shift [), 95 (left out: registration not confirmed (overlap ratio 0.79, best shift [), 96 (left out: registration not confirmed (overlap ratio 1.08, best shift [), 49 (left out: registration not confirmed (overlap ratio 0.83, best shift [), 56 (left out: registration not confirmed (overlap ratio 0.95, best shift [).

## Sheets, Newark 1908
| sheet | how placed | outlines exported | on a standing footprint (IoU>0.5) | overlap check: share on today / ring, ratio, best shift m | tier |
|---|---|---|---|---|---|
| 50 | street crossings (6; residual max 1.3 m, leave-one-out max 1.7 m, 0.100 m/px, rot 69) + building match (affine, [1.22, 0.86] m) | 178 | 39 (22%) | 0.587 / 0.269, 2.18, [0, 0] | verified |
| 63 | street crossings (5; residual max 12.9 m, leave-one-out max 19.9 m, 0.102 m/px, rot -26) + building match (shift, [-1.42, -4.46] m) | 154 | 7 (4%) | 0.469 / 0.302, 1.55, [0, 0] | verified |
| 47 | street crossings (5; residual max 0.8 m, leave-one-out max 1.9 m, 0.099 m/px, rot 69) | 113 | 0 (0%) | 0.14 / 0.128, 1.09, [-4, -14] | street crossings |
| 56 | street crossings (7; residual max 4.0 m, leave-one-out max 6.0 m, 0.100 m/px, rot 70) + building match (affine, [-1.74, -0.89] m) | 233 | 109 (47%) | 0.704 / 0.287, 2.45, [0, 0] | verified |
| 57 | street crossings (7; residual max 2.1 m, leave-one-out max 3.0 m, 0.101 m/px, rot 70) + building match (affine, [-1.04, -3.7] m) | 235 | 111 (47%) | 0.593 / 0.258, 2.3, [0, 0] | verified |
| 52 | street crossings (4; residual max 2.0 m, leave-one-out max 4.7 m, 0.102 m/px, rot -21) + building match (shift, [-1.75, 2.45] m) | 163 | 22 (14%) | 0.574 / 0.282, 2.04, [-1, 0] | verified |
| 64 | street crossings (6; residual max 9.9 m, leave-one-out max 11.9 m, 0.099 m/px, rot -23) + building match (shift, [-3.21, 3.91] m) | 141 | 20 (14%) | 0.572 / 0.271, 2.12, [0, 1] | verified |
| 58 | street crossings (7; residual max 1.8 m, leave-one-out max 2.5 m, 0.098 m/px, rot 70) + building match (affine, [-2.92, -2.5] m) | 219 | 104 (48%) | 0.747 / 0.292, 2.56, [0, 0] | verified |
| 65 | street crossings (7; residual max 5.3 m, leave-one-out max 6.8 m, 0.102 m/px, rot 64) + building match (shift, [1.6, 3.87] m) | 173 | 11 (6%) | 0.278 / 0.162, 1.72, [0, 1] | verified |
| 66 | street crossings (7; residual max 14.2 m, leave-one-out max 22.4 m, 0.097 m/px, rot 68) + building match (shift, [2.77, 0.71] m) | 107 | 6 (6%) | 0.505 / 0.249, 2.03, [0, 0] | verified |
| 59 | street crossings (7; residual max 25.3 m, leave-one-out max 35.6 m, 0.097 m/px, rot 68) + building match (shift, [2.01, 4.4] m) | 192 | 19 (10%) | 0.53 / 0.269, 1.97, [1, 2] | verified |

Left out: 46 (left out: too few outlines to check (not traced)), 34 (left out: too few outlines to check (not traced)), 41 (left out: too few outlines to check (not traced)), 30 (left out: too few outlines to check (not traced)), 17 (left out: registration not confirmed (overlap ratio 1.24, best shift [), 49 (left out: registration not confirmed (overlap ratio 1.32, best shift [), 48 (left out: registration not confirmed (overlap ratio 1.10, best shift [), 51 (left out: registration not confirmed (overlap ratio 0.90, best shift [), 55 (left out: registration not confirmed (overlap ratio 1.40, best shift [), 45 (left out: registration not confirmed (overlap ratio 0.89, best shift [), 43 (left out: too few outlines to check (not traced)), 44 (left out: too few outlines to check (not traced)), 39 (left out: too few outlines to check (not traced)), 42 (left out: too few outlines to check (not traced)), 62 (left out: too few outlines to check (not traced)), 60 (left out: too few outlines to check (not traced)).
Traced but never placed (no crossing with a street of today found, or the check failed): sheets 17, 30, 34, 41, 43, 44, 45, 46, 48, 49, 51, 55, 60, 62.

## Holes of `holes.csv` (cells of Paterson / Newark)
Paterson: the layer covers 29-52 % of the hole area listed for 1900-1940 (23 of 44 ha in 1900, 15 of 52 in 1920, 20 of 56 in 1940) and 28 of 97 ha in 1980. Newark: **almost none** (5 of 291 ha in 1980; 0 before): the Central Ward that was cleared lies on sheets 20-45 and 17-19, whose streets are gone; these could not be placed.

## What the tracing misses
* Dense downtown blocks (Paterson sheets 7, 14, 16, 18) come out as block-sized or merged outlines; outlines over 5,000 m2 are dropped by the tool, so Paterson's big brick mills and department stores are **under-represented** (655 brick against 5,545 frame outlines).
* Blue (non-combustible) buildings, gasholders, tanks, washed lots and slip-covered lots are missed or merged; rows of attached houses are often one outline; no storeys were read.
* Sheets are 1915 (Paterson) and 1908 (Newark): later pasted corrections were not read (Newark's 1908-09 sheets carry none visible here).
* Newark's Central Ward cleared blocks, the Route 280 corridor and downtown are **not covered**; Paterson vols 2-3 (outer wards, Riverside, Dublin's west bank beyond sheet 3, the Great Falls mills on sheets 1-3) are only partly in vol. 1; sheets 1, 2, 3, 5, 10, 13 of vol. 1 were not placed.
* Registration of the consistent tier (15 Paterson sheets) rests on the overlap optimum only.
