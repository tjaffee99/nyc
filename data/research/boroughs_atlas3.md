# Atlas tracing, round 5 part 3: the east and north Bronx, southern Staten Island

Tool: `data/manual/atlas/tools_boroughs3/` (copy of `tools_brooklyn2/atlas.py`; `layers.json` written by `mk_layers.py` + `defs.py`;
`run.sh` trace, `run_rb.sh` building match, `report.py` tables, `check_layer.py`, `street_share.py`, `summ.py`). Work files:
`data/interim/atlas_boroughs3/<layer>/*.pkl` (traces kept). Scans: NYPL Map Division (public domain)
`https://images.nypl.org/index.php?id=<imageId>&t=u`; control points and masks: NYC Space/Time Directory Map Warper dump (CC0)
`https://s3.amazonaws.com/spacetime-nypl-org/datasets/mapwarper/mapwarper.objects.ndjson`. All layers are clipped at export to outside the
coverage of every other layer in `data/manual/atlas/` (37 at the time), so no building is traced twice. Not complete inside their coverage;
`map_year` is the NYPL catalogue year. Registration rule (`require_match`): a plate is kept only if a street match or building match
corrected it, or at least 10 outlines coincide with standing footprints within 4 m median, or >= 5 control points cross-validate to <= 4 m.

## Method changes
* Export clips by `outside_layers` read at export time (the list frozen in layers.json went stale when another agent renamed a layer).
* `refine_buildings` takes `--search` / `--q` (12 m search, q 0.2 on the Bronx; 8 m on Staten Island).
* Staten Island plates: frame `db_min` 4, outline 0.2, no `stone` class (63 false stone outlines per plate on 15414 otherwise); the earlier
  setting (db 5, outline 0.4) found about 25 % of the small houses in a window of plate 15414, the final one about 70 % on plate 15421 (looked at).
* A try with street-match on blank streets (`street_empty`) and `--locate` did not help the Bronx plates; not used.

## Looked at (windows drawn over the scan)
* bronx_east_1905 plate 22991 (Pugsley's Creek, mostly open lots, registration good, houses found) and 22984 (Merrill St / Commonwealth Av,
  200 m, final layer): about 85-90 % of the drawn buildings found, outlines on the walls; purple / blue / grey fills (auto houses, stores) missed.
* bronx_north_1905 plate 23056 (E 220th St, 180 m, final): about 85 %; the same colours missed.
* staten_island_south_1917 plate 15414 (Midland Beach, 250 m, tuning only) and 15421 (Great Kills, 250 m, final): about 70 %, outlines are ragged and
  sit inside the fill of small houses; today's footprints do not coincide (the area was rebuilt).
Plates never looked at: all others.

## Checks (all three: valid polygons, 15-5,000 m2, unique ids, centres inside coverage, no overlapping pair)
Share of centroids within 8 m of a street centre line: bronx_east 4.6 %, bronx_north 2.7 %, Staten Island 8.3 % (before two plates were dropped);
roadway slivers by the lead's rule 0.5 %, 0.3 %, 1.4 %.

### bronx_east_1905

3229 outlines (2862 frame, 367 brick), coverage 4.19 km2, 19 plates used; on a standing footprint (IoU > 0.5): 814.

Holes of holes.csv (Bronx / Richmond / Queens, 1860-1920 grids) with their point inside the coverage: 0 of 30 (0 of 215 ha).

| sheet | plate | outlines | registration | street match left (m) | building match residual (m) | coincide share | median offset of those (m) |
|---|---|---|---|---|---|---|---|
| 4 | 22973 | 403 | control points only, not checked | None | None | 0.06 | 1.66 |
| 7 | 22976 | 196 | building match | None | 2.05 | 0.148 | 1.55 |
| 8 | 22977 | 98 | building match | None | 1.24 | 0.459 | 1.61 |
| 9 | 22978 | 124 | building match | None | 0.94 | 0.315 | 1.2 |
| 10 | 22979 | 284 | building match | None | 1.2 | 0.261 | 1.44 |
| 15 | 22984 | 283 | building match | None | 0.99 | 0.163 | 1.33 |
| 19 | 22988 | 161 | building match | None | 1.1 | 0.124 | 1.38 |
| 21 | 22990 | 69 | control points only, not checked | None | None | 0.174 | 2.09 |
| 22 | 22991 | 63 | control points only, not checked | None | None | 0.397 | 1.27 |
| 23 | 22992 | 160 | building match | None | 0.38 | 0.4 | 1.39 |
| 24 | 22993 | 125 | building match | None | 0.59 | 0.384 | 1.53 |
| 26 | 22995 | 98 | control points only, not checked | None | None | 0.408 | 1.13 |
| 29 | 22998 | 84 | building match | None | 1.16 | 0.226 | 1.37 |
| 31 | 23000 | 205 | building match | None | 0.5 | 0.332 | 1.27 |
| 32 | 23001 | 214 | building match | None | 0.34 | 0.528 | 1.23 |
| 33 | 23002 | 130 | building match | None | 1.57 | 0.023 | 1.97 |
| 35 | 23004 | 231 | building match | None | 1.3 | 0.32 | 1.42 |
| 36 | 23005 | 154 | building match | None | 0.53 | 0.273 | 1.19 |
| 43 | 23012 | 147 | building match | None | 1.01 | 0.197 | 1.59 |

Left out:

* plate 22971 (sheet 2): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 11.6 m)
* plate 22975 (sheet 6): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 573.6 m)
* plate 22980 (sheet 11): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 25.0 m)
* plate 22981 (sheet 12): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 0.0 m)
* plate 22982 (sheet 13): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 3.9 m)
* plate 22985 (sheet 16): left out: not placed reliably (no street or building match; 1 outlines on standing footprints, median offset 2.24 m; control points CV rms 35.8 m)
* plate 22986 (sheet 17): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 22.5 m)
* plate 22987 (sheet 18): left out: not placed reliably (no street or building match; 6 outlines on standing footprints, median offset 1.55 m; control points CV rms 12.7 m)
* plate 22989 (sheet 20): left out: not placed reliably (no street or building match; 4 outlines on standing footprints, median offset 1.83 m; control points CV rms 22.5 m)
* plate 22996 (sheet 27): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 5.2 m)
* plate 22997 (sheet 28): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 34.6 m)
* plate 22999 (sheet 30): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 67.0 m)
* plate 23003 (sheet 34): left out: not placed reliably (no street or building match; 1 outlines on standing footprints, median offset 1.68 m; control points CV rms 11.3 m)
* plate 23006 (sheet 37): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 75.9 m)
* plate 23007 (sheet 38): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 107.3 m)
* plate 23008 (sheet 39): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 16.0 m)
* plate 23009 (sheet 40): left out: not placed reliably (no street or building match; 1 outlines on standing footprints, median offset 1.63 m; control points CV rms 56.9 m)
* plate 23010 (sheet 41): left out: not placed reliably (no street or building match; 8 outlines on standing footprints, median offset 1.3 m; control points CV rms 12.4 m)
* plate 23011 (sheet 42): left out: not placed reliably (no street or building match; 4 outlines on standing footprints, median offset 2.4 m; control points CV rms 8.0 m)
* plate 23013 (sheet 44): left out: not placed reliably (no street or building match; 4 outlines on standing footprints, median offset 2.28 m; control points CV rms 15.3 m)
* plate 23014 (sheet 45): left out: not placed reliably (no street or building match; 2 outlines on standing footprints, median offset 5.14 m; control points CV rms 15.4 m)
* plate 23015 (sheet 46): left out: not placed reliably (no street or building match; 2 outlines on standing footprints, median offset 1.05 m; control points CV rms 70.0 m)
* plate 23016 (sheet 47): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 0.0 m)
* plate 23018 (sheet 49): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 939.7 m)
* plate 23023 (sheet 54): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 9.1 m)
* plate 23024 (sheet 55): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 0.0 m)
* plate 23025 (sheet 56): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 6.9 m)
* plate 23027 (sheet 58): left out: not placed reliably (no street or building match; 2 outlines on standing footprints, median offset 2.18 m; control points CV rms 10.5 m)
* plate 23030 (sheet 61): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 0.0 m)
* plate 23031 (sheet 62): left out: not placed reliably (no street or building match; 7 outlines on standing footprints, median offset 0.84 m; control points CV rms 5.7 m)
* plate 23032 (sheet 63): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 9.0 m)
* plate 23033 (sheet 64): left out: not placed reliably (no street or building match; 1 outlines on standing footprints, median offset 4.11 m; control points CV rms 4.5 m)
* plate 23034 (sheet 65): left out: not placed reliably (no street or building match; 3 outlines on standing footprints, median offset 1.68 m; control points CV rms 8.6 m)

### bronx_north_1905

2242 outlines (2043 frame, 199 brick), coverage 3.42 km2, 17 plates used; on a standing footprint (IoU > 0.5): 716.

Holes of holes.csv (Bronx / Richmond / Queens, 1860-1920 grids) with their point inside the coverage: 0 of 30 (0 of 215 ha).

| sheet | plate | outlines | registration | street match left (m) | building match residual (m) | coincide share | median offset of those (m) |
|---|---|---|---|---|---|---|---|
| 7 | 23048 | 131 | building match | None | 0.98 | 0.275 | 1.36 |
| 8 | 23049 | 79 | control points only, not checked | None | None | 0.19 | 0.97 |
| 9 | 23050 | 229 | building match | None | 0.95 | 0.231 | 1.29 |
| 10 | 23051 | 240 | building match | None | 0.31 | 0.3 | 1.05 |
| 11 | 23052 | 112 | building match | None | 0.83 | 0.366 | 1.55 |
| 15 | 23056 | 266 | building match | None | 0.3 | 0.455 | 1.0 |
| 16 | 23057 | 163 | building match | None | 0.18 | 0.276 | 1.04 |
| 17 | 23058 | 192 | building match | None | 0.25 | 0.453 | 1.44 |
| 18 | 23059 | 136 | control points only, not checked | None | None | 0.316 | 1.19 |
| 19 | 23060 | 36 | control points only, not checked | None | None | 0.361 | 1.04 |
| 20 | 23061 | 45 | control points only, not checked | None | None | 0.267 | 1.71 |
| 21 | 23062 | 99 | control points only, not checked | None | None | 0.101 | 1.75 |
| 23 | 23064 | 99 | building match | None | 0.47 | 0.414 | 1.35 |
| 24 | 23065 | 94 | building match | None | 0.49 | 0.468 | 1.12 |
| 27 | 23068 | 107 | building match | None | 0.18 | 0.458 | 0.98 |
| 29 | 23070 | 88 | building match | None | 0.91 | 0.273 | 1.47 |
| 52 | 23095 | 126 | control points only, not checked | None | None | 0.079 | 2.45 |

Left out:

* plate 23042 (sheet 1): left out: not placed reliably (no street or building match; 1 outlines on standing footprints, median offset 2.03 m; control points CV rms 87.5 m)
* plate 23043 (sheet 2): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 43.1 m)
* plate 23044 (sheet 3): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 7.1 m)
* plate 23045 (sheet 4): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 9.8 m)
* plate 23046 (sheet 5): left out: not placed reliably (no street or building match; 1 outlines on standing footprints, median offset 1.88 m; control points CV rms 44.2 m)
* plate 23047 (sheet 6): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 57.0 m)
* plate 23053 (sheet 12): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 56.7 m)
* plate 23055 (sheet 14): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 167.5 m)
* plate 23063 (sheet 22): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 17.5 m)
* plate 23066 (sheet 25): left out: not placed reliably (no street or building match; 4 outlines on standing footprints, median offset 1.19 m; control points CV rms 5.2 m)
* plate 23071 (sheet 30): left out: not placed reliably (no street or building match; 4 outlines on standing footprints, median offset 2.87 m; control points CV rms 10.0 m)
* plate 23072 (sheet 31): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 7.9 m)
* plate 23074 (sheet 33): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 38.1 m)
* plate 23075 (sheet 34): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 18.9 m)
* plate 23076 (sheet 35): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 399.2 m)
* plate 23079 (sheet 38): left out: not placed reliably (no street or building match; 1 outlines on standing footprints, median offset 1.01 m; control points CV rms 15.6 m)
* plate 23080 (sheet 39): left out: not placed reliably (no street or building match; 1 outlines on standing footprints, median offset 1.86 m; control points CV rms 32.3 m)
* plate 23081 (sheet 40): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 36.1 m)
* plate 23083 (sheet 42): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 27.8 m)
* plate 23084 (sheet 43): left out: not placed reliably (no street or building match; 3 outlines on standing footprints, median offset 0.89 m; control points CV rms 3.5 m)
* plate 23085 (sheet 44): left out: not placed reliably (no street or building match; 6 outlines on standing footprints, median offset 1.74 m; control points CV rms 3.9 m)
* plate 23086 (sheet 45): left out: not placed reliably (no street or building match; 2 outlines on standing footprints, median offset 2.02 m; control points CV rms 7.6 m)
* plate 23087 (sheet 46): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 25.3 m)
* plate 23090 (sheet 48): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 345.6 m)
* plate 23093 (sheet 50): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 423.6 m)
* plate 23094 (sheet 51): left out: not placed reliably (no street or building match; 6 outlines on standing footprints, median offset 1.52 m; control points CV rms 96.4 m)

### staten_island_south_1917

12080 outlines (11366 frame, 714 brick), coverage 81.8 km2, 49 plates used; on a standing footprint (IoU > 0.5): 267.

Holes of holes.csv (Bronx / Richmond / Queens, 1860-1920 grids) with their point inside the coverage: 4 of 30 (48 of 215 ha).

| sheet | plate | outlines | registration | street match left (m) | building match residual (m) | coincide share | median offset of those (m) |
|---|---|---|---|---|---|---|---|
| image 1646244 | 15375 | 252 | street match | 3.9 | None | 0.008 | 2.97 |
| image 1646246 | 15377 | 218 | street match | 2.8 | None | 0.014 | 2.01 |
| image 1646247 | 15378 | 216 | street match | 3.1 | None | 0.023 | 1.76 |
| image 1646248 | 15379 | 155 | street match | 3.7 | None | 0.0 | None |
| image 1646249 | 15380 | 72 | street match | 2.4 | None | 0.028 | 1.26 |
| image 1646250 | 15381 | 37 | street match | 2.1 | None | 0.0 | None |
| image 1646251 | 15382 | 172 | street match | 3.3 | None | 0.012 | 1.48 |
| image 1646252 | 15383 | 74 | street match | 2.3 | None | 0.0 | None |
| image 1646253 | 15384 | 163 | street match | 3.3 | None | 0.0 | None |
| image 1646254 | 15385 | 133 | street match | 3.5 | None | 0.0 | None |
| image 1646255 | 15386 | 186 | street match | 3.7 | None | 0.0 | None |
| image 1646256 | 15387 | 61 | street match | 2.6 | None | 0.0 | None |
| image 1646257 | 15388 | 336 | street match | 2.6 | None | 0.006 | 1.9 |
| image 1646261 | 15392 | 176 | street match | 3.8 | None | 0.011 | 1.23 |
| image 1646272 | 15403 | 172 | street match | 2.5 | None | 0.035 | 1.07 |
| image 1646274 | 15405 | 101 | street match | 1.9 | None | 0.04 | 1.33 |
| image 1646275 | 15406 | 168 | street match | 1.8 | None | 0.012 | 1.58 |
| image 1646276 | 15407 | 452 | street match | 1.7 | None | 0.0 | None |
| image 1646278 | 15409 | 94 | street match | 2.8 | None | 0.0 | None |
| image 1646279 | 15410 | 315 | street match | 1.5 | None | 0.01 | 1.8 |
| image 1646282 | 15413 | 241 | street match | 4.3 | None | 0.012 | 1.1 |
| image 1646283 | 15414 | 254 | street match | 2.1 | None | 0.004 | 0.75 |
| image 1646284 | 15415 | 208 | street match | 3.1 | None | 0.019 | 1.39 |
| image 1646285 | 15416 | 335 | street match | 5.4 | None | 0.003 | 0.12 |
| image 1646286 | 15417 | 125 | street match | 1.0 | None | 0.0 | None |
| image 1646288 | 15419 | 116 | street match | 2.8 | None | 0.026 | 3.01 |
| image 1646289 | 15420 | 102 | street match | 3.8 | None | 0.01 | 1.38 |
| image 1646290 | 15421 | 396 | street match | 2.1 | None | 0.0 | None |
| image 1646291 | 15422 | 31 | street match | 3.5 | None | 0.0 | None |
| image 1646292 | 15423 | 281 | street match | 2.4 | None | 0.007 | 2.4 |
| image 1646293 | 15424 | 114 | street match | 4.2 | None | 0.009 | 1.98 |
| image 1646294 | 15425 | 117 | street match | 2.2 | None | 0.0 | None |
| image 1646296 | 15427 | 115 | street match | 3.7 | None | 0.0 | None |
| image 1646298 | 15429 | 264 | street match | 2.6 | None | 0.008 | 1.5 |
| image 1646299 | 15430 | 115 | street match | 4.4 | None | 0.0 | None |
| image 1646303 | 15434 | 815 | street match + building match | 2.1 | 0.78 | 0.012 | 1.65 |
| image 1646304 | 15435 | 196 | street match | 3.7 | None | 0.005 | 15.5 |
| image 1646305 | 15436 | 182 | street match | 4.4 | None | 0.0 | None |
| image 1646306 | 15437 | 123 | street match | 4.6 | None | 0.008 | 0.83 |
| image 1646308 | 15439 | 293 | street match | 3.3 | None | 0.007 | 1.18 |
| image 1646309 | 15440 | 265 | street match | 6.1 | None | 0.004 | 3.0 |
| image 1646310 | 15441 | 102 | street match | 4.0 | None | 0.0 | None |
| image 1646318 | 15449 | 194 | street match + building match | 3.6 | 1.77 | 0.057 | 1.89 |
| image 1646322 | 15453 | 181 | street match | 3.1 | None | 0.017 | 1.14 |
| image 1646324 | 15455 | 855 | street match + building match | 1.6 | 1.03 | 0.05 | 1.58 |
| image 1646325 | 15456 | 384 | street match + building match | 1.3 | 0.99 | 0.094 | 1.26 |
| image 1646326 | 15457 | 590 | street match + building match | 2.0 | 0.4 | 0.075 | 1.18 |
| image 1646327 | 15458 | 556 | street match + building match | 2.2 | 0.81 | 0.056 | 1.33 |
| image 1646328 | 15459 | 977 | street match + building match | 2.2 | 0.48 | 0.034 | 1.29 |

Left out:

* plate 15389 (sheet image 1646258): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 15.6 m)
* plate 15390 (sheet image 1646259): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 5.6 m)
* plate 15391 (sheet image 1646260): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 105.4 m)
* plate 15393 (sheet image 1646262): left out: not placed reliably (no street or building match; 1 outlines on standing footprints, median offset 1.06 m; control points CV rms 22.5 m)
* plate 15394 (sheet image 1646263): left out: not placed reliably (no street or building match; 2 outlines on standing footprints, median offset 2.4 m; control points CV rms 0.0 m)
* plate 15395 (sheet image 1646264): left out: street match only 9 windows with a constant shift and 5.5-6.7 m left after it, no outline on a standing building: registration not good enough
* plate 15402 (sheet image 1646271): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 16.2 m)
* plate 15408 (sheet image 1646277): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 10.2 m)
* plate 15411 (sheet image 1646280): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 24.1 m)
* plate 15412 (sheet image 1646281): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 33.5 m)
* plate 15418 (sheet image 1646287): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 17.4 m)
* plate 15426 (sheet image 1646295): left out: street match only 9 windows with a constant shift and 5.5-6.7 m left after it, no outline on a standing building: registration not good enough
* plate 15428 (sheet image 1646297): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 17.6 m)
* plate 15432 (sheet image 1646301): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 22.9 m)
* plate 15438 (sheet image 1646307): left out: not placed reliably (no street or building match; 2 outlines on standing footprints, median offset 2.0 m; control points CV rms 7.3 m)
* plate 15443 (sheet image 1646312): left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 18.7 m)

## Plates dropped by hand
Staten Island 15395 and 15426: street match with a constant shift from 9 windows, 6.7 / 5.5 m left, no outline on a standing building.
Bronx east: plates with few buildings and no match (22971, 22975, 22980-22982, 22985-22987, 22989, 22996-22997, 23003, 23006-23010, 23013-23015, 23018, 23023-23025, 23027, 23030-23034) are left out by the rule above (street match and building match found 0-3 windows; 23027 and 23031 hold 200 and 177 outlines, Pugsley's Creek / Throgs Neck shore, and could not be placed).

## Not done
* **Queens**: no layer. The Hyde 1907 plates (`queens_jamaica_1907`, `queens_rockaway_beach_1907`, `queens_newtown_1907`) were configured and the run
  started but stopped on the lead's request before any was exported or checked; no file of them is in `data/manual/atlas`. Flushing's centre
  (Bromley 1909 plates, 0.9 m per pixel, houses 10 px: judged too coarse; tried on plate 8134, a rural window), College Point, Whitestone,
  the Rockaway beach towns beyond queens_rockaway_1907, Corona, Richmond Hill remain untraced.
* Staten Island: 14 plates unplaced (15389-15391, 15393, 15394, 15402, 15408, 15411, 15412, 15418, 15428, 15432, 15438, 15443: no street or building
  match, control points 5-105 m off), plus the two dropped; Tottenville and Prince's Bay are only partly covered. The 1907 atlas and Sanborn 1898 not used.
* Bronx: Inwood is Manhattan (not in this area). The 1898 Atlas 43 / 44 states of the east Bronx were not traced; City Island and Riverdale beyond
  the plates above (Vol. B plates 48-52 placed only for sheet 52) are thin.
