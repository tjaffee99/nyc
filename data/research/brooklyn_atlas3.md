# Brooklyn atlas tracing, third part (2026-11-12)

Tool: `data/manual/atlas/tools_brooklyn3/` (copy of `tools_brooklyn2/`; `mk_layers.py` writes `layers.json`, `run.sh` / `run_city.sh` run a layer one
plate at a time, `drop_slivers.py`, `holes_in.py`, `note_tables.py` are new). Work files `data/interim/atlas_brooklyn3/`, scans `data/raw/atlas/brooklyn3/`
(deleted after each plate). Source of scans and control points: NYPL Map Division (public domain), `https://images.nypl.org/index.php?id=<imageId>&t=u`, and the
Map Warper records of the NYC Space/Time Directory dump (CC0), as in the README. Three layers were written, one candidate set was tried and left out, one failed
(Coney Island from Bromley / Hopkins). Nothing is generated.

## What was changed in the tool

* `fix_gcps.py`: the scale window and tolerance are parameters (`SC`, `TOL`; set for the plates in hand, 0.15-0.22 m per pixel).
* `atlas.py` `fills_rows`: the width above which a dark stroke is a "figure" and not a party wall is `fig_open` (was fixed at 3 pixels). On Hyde's plates
  (100 ft to the inch, 0.17 m per pixel) the lot lines between houses are 3-4 pixels thick, so a whole row of fourteen houses came out as one outline; with
  `fig_open` = 5 (and `wall_px` 60, `line_depth` 3.5) it comes out house by house (plate 16001: 37 brick outlines became 174; outlines on standing footprints 4 -> 74).
* Hopkins 1880 is drawn like Robinson's county atlases (300 ft to the inch, pale washes along the street front of each lot): style `robinson_300ft`, streets taken
  as the blank paper (`street_empty`), brick threshold `da_min` 5.5 (the rose wash is pale: da +9 over the paper; the standard 12 found 13 brick outlines on plate 7984, 5.5 finds 87).
* `drop_slivers.py` applies the lead's own roadway-sliver rule (more than 60 % within 5 m of a street centre line and narrower than 5.5 m or longer than 3.5 times its
  width) to the finished layer: dark tram, pipe and gutter lines read as brick or stone. 15 + 67 + 66 outlines dropped in the three layers.

## Layers written

| layer | atlas | plates used | outlines | km2 (plate masks) | on a standing footprint |
|---|---|---|---|---|---|
| `brooklyn_old_1880` | *Atlas of the entire city of Brooklyn* (Hopkins, 1880), 300 ft to the inch | 14 of 17 tried | 2,174 (1,908 frame / 266 brick) | 17.1 | 25 |
| `brooklyn_bayridge_1905` | *Atlas of the borough of Brooklyn*, vol. 6, Ward 30 (E. Belcher Hyde, 1905), 100 ft to the inch | 30 of 32 | 7,239 (2,675 frame / 4,523 brick / 41 stone) | 18.9 | 1,166 |
| `brooklyn_coney_1907` | the same atlas, vol. 7, Ward 31 (Hyde, 1907) | 12 of 18 | 2,613 (2,540 frame / 67 brick / 6 stone) | 8.2 | 16 |

`map_year` is 1880, 1905, 1907 (NYPL catalogue dates; survey dates not read). Source ids: `hopkins_brooklyn_1880`, `hyde_brooklyn_1905_v6`, `hyde_brooklyn_1907_v7`.
Frame = yellow, brick = red or rose, stone = grey / blue (rare). Not complete: see the recall of each layer below. Attached rows of the 1880 layer are one outline
(300 ft to the inch: a house is 12-15 pixels wide); Hyde's rows are cut house by house.

* **`brooklyn_old_1880` is clipped against the Sanborn layers of 1886-88** (`brooklyn_downtown_1887`, `southwest_1886`, `williamsburg_1887`, `greenpoint_1887`, `bedstuy_1888`,
  `bushwick_1888`, `crownheights_1888`, `browns_1887`, `parkslope_1888`; same decade, rule of the brief): of 4,679 outlines traced on the 14 plates 2,174 remain (e.g. plate 7984,
  Bushwick: 957 traced, 98 kept). It adds the 1880 state where the Sanborn volumes have no plate (Gowanus, Park Slope's south, Bushwick west of the plates, the Greenpoint /
  Williamsburg edge, Weeksville, Ocean Hill); inside the Sanborn masks the 1880 outlines are not in the file (they can be had again by deleting `clip` for the layer in `mk_layers.py` and re-running `run.sh brooklyn_old_1880` and `atlas.py export`; the traced work files were deleted to save disk) if the lead wants "stood by 1880" for those buildings as well).
* **Not clipped** `brooklyn_bayridge_1905` and `brooklyn_coney_1907` (no layer of 1900-09 exists; the 1898 and 1890 layers are another decade). Where `kings_towns_1890` (Robinson's Coney Island plate)
  or `brooklyn_*_1898` overlap them they are earlier states of the same ground, as the brief says.

## Checks

Numeric, on the files as written (`check_layer.py`, `street_share.py`): all polygons valid, ids unique, centres inside the coverage, no overlapping pair (> 0.3 of the smaller) within a layer;
`area_out` = outlines over 5,000 m2 (allowed here up to 20,000: factories, hotels, tanks; 0 / 2 / 1). Share of outlines whose centre lies within 8 m of a street centre line
(the lead's `ATLAS_SKIP` test): 3.9 % (1880), 2.0 % (Bay Ridge), 7.1 % (Coney); the lead's roadway-sliver count after my filter: 0 in each.

**Registration.** Control points, then street match (tint or blank paper against today's centre lines, windows of 300 m), then, where the plate has surviving pre-war buildings, the building match
(`bld` column of the export: shift found). Residual left = median of the window shifts after the correction. Bay Ridge: 28 of 30 plates by affine street match (10-22 windows), residual left
1.2-5.0 m (median 2.8), outlines on standing footprints sit 0.3-2.4 m off (median 1.4); twelve plates also corrected by the building match (shifts 0.6-5.6 m). Hopkins 1880: street match on every plate used (6-56
windows), residual 0.6-3.2 m; offsets of the 25 outlines that coincide with standing buildings 0.6-5.8 m (plate 7994 5.8 m, one outline; 7993 4.4 m, 2 outlines: too few to say more). Coney:
street match only (almost nothing there stands today: 16 coinciding outlines), residual 0.7-5.7 m, so **this layer is good to 3-6 m**, worse than the others; the plates with a residual above 5 m
(16057, 16061: 5.1 and 5.7 m on 10 and 4 windows) are in it and said so here.

**Looked at on the scans** (overlay of the exported outlines and today's footprints on the plate, 150-260 m windows): Hopkins 7984 (twice: before and after the brick threshold), 8011, 7994, 7993;
Hyde 16001 (four tuning passes, then the final), 16012, 16015; Hyde Coney 16056, 16057; and, to reject it, Bromley 1899 plate 28123 (below). Results:

* 1880: registration within 1-3 m of the printed lot lines (the blue footprints of today follow the same blocks); most fills traced, **recall about 60-70 %** in the windows: the palest washes
  (frame-ink stains, some rose washes) are missed and a row of attached houses is one outline; no false building on empty ground; ragged edges where lot numbers cross a house. The fills are the
  wash on the lot, which is a little smaller than the house outlined in ink.
* Bay Ridge (Hyde): brick rows house by house, registration 1-2 m on rows that stand today (16001, 16012); **frame houses are traced from the yellow fill inside the brown outline**: ragged and 0.5-1 m
  small on every side (16012, 16015); porches and bays are lost; **false outlines**: grey / purple tram and pipe strips and gutter edges (67 dropped by the sliver rule; two magenta ones on plate 16015 were
  of this kind), lettering inside large lots now and then. Recall about 85 % of the drawn buildings in the windows. The ward's open lots (1905: most of Bay Ridge east of Fort Hamilton) are empty on the map and in the layer.
* Coney (Hyde 1907, plates 16056, 16057): the hotels, bath houses, Music Hall, Carousel, the Scrambler, the Rough Rider and Jackman's Thriller are traced as drawn; the roller-coaster and track strips are not buildings and
  are mostly not in the layer; a few outlines of amusement structures merge (a carousel with its arcade). Position: the street grid fits, but nothing standing today can confirm 3-5 m.

**Not looked at**: 26 of the 30 Bay Ridge plates, 10 of the 14 Hopkins plates (7985, 7986, 7987, 7990, 7991, 7992, 7996, 8003, 8008, 8014) and 10 of the 12 Coney plates. The Hopkins plates 7985, 7991, 7996, 8008
(no coinciding outline and 55-208 outlines) were accepted on the street match alone.

### Left out, and why

* `brooklyn_old_1880`: 8010 (Plate 26, Greenpoint's marsh edge: no street window, `locate` found nothing) and 8016 (Plate 22, Williamsburg: control points 78 m off, no street window); 8015 (Plate 21, shift of 20 m
  to correct, 5.2 m left, only 18 outlines outside the Sanborn masks).
* `brooklyn_bayridge_1905`: 16004 (Plate 13, Fort Hamilton shore: control points 112 m off, no match) and 16025 (Plate 24: 146 m off, 13 outlines).
* `brooklyn_coney_1907`: 16048, 16058, 16060 (Plate 33, the middle of Coney Island), 16065, 16073: control points far off or no street window (3 to 4 windows, no agreement); consistent
  control points were found for 16060 and 16073 (`fix_gcps.py`) but the street match still found no agreement, so they are not placed. Plate 33 is the plate of Surf Ave and the Bowery west of Stillwell Ave.
* **Perris 1868 vol. 4** (Williamsburgh and Greenpoint, plates 66-85, 19 in the dump): scans are foxed, pasted up from slips and the paper reads L 63-68 against 80+ elsewhere; the street match found 0-6 windows, the first
  fit was 5-10 m off, and the tracer found 80-140 outlines on plates that carry 500+ houses (recall about 20 %). Not handed over.
* **Bromley 1899 vol. 3 (Coney Island, plates 5-8, 15)**, **Hopkins's Coney Island map of 1880 (0.98 m per pixel, too small a scale)** and **plate 19 of the 1907 *Atlas of the borough of Brooklyn* (Section 21, Coney Island; compiler not named in the dump, probably Hyde)**: control points 6-350 m off, no
  street window; plate 28123 was placed by a 33 m street shift on 5 windows and showed plate-edge strips and the beach as buildings: not handed over.
* **Dripps 1869** (7 sheets) and **Williamsburgh 1852, Perris 1855 plates 1, 2** : Dripps 1869 and the 1850-52 city maps (`Map of the City of Williamsburgh and town of Bushwick`) are farm-line maps without buildings; Perris
  1855 plates 3-35 are NYPL's Building Inspector tracing already in the map (7,878 outlines, `atlas_1855`, latitude 40.673-40.717, longitude -74.018 to -73.966); plates 1 and 2 hold 100 buildings and no hole.

## The holes (`data/interim/reports/holes.csv`, place Kings, grid detail; each hole is a cluster with one centre point; counted when the centre lies in a layer's coverage)

| layer | 1860 holes inside coverage | 1880 holes inside coverage |
|---|---|---|
| `brooklyn_old_1880` | 62.1 ha of 144.8 (13 of 27 clusters: Bedford, Crown Heights, Weeksville, Ocean Hill, Gowanus, Park Slope south) | 12.6 ha of 69.1 (1 of 11: Greenpoint, -73.9394 40.729) |
| `brooklyn_bayridge_1905` | 0 | 0 |
| `brooklyn_coney_1907` | 0 | 0 |

Read with care: **an 1880 map cannot fill a hole of 1860** by itself; the buildings come in at the date the lead gives them (census growth up to 1880, nearest the old centres first), so what the layer
gives the 1860 holes is outlines of what stood by 1880 on those blocks (the earlier maps, Perris 1855 and Dripps 1869, carry none for them). The 1880 hole at Coney / Manhattan Beach (-73.948 40.5764, 5.1 ha) and
the Bay Ridge shore (-74.0246 40.6097, 3.4 ha, both years) are outside the plates that could be placed. The Navy Yard hole was left alone. The part of the 1860 holes that lies in the Sanborn masks (Bedford, Browns,
Crown Heights) rests on the Sanborn layers of 1886-88, as before.

## The four 1898 layers of `tools_brooklyn2` (point 4: the note that part did not write)

Bromley's *Atlas of the Brooklyn borough of the City of New York, originally Kings County* (G. W. Bromley & Co., Philadelphia, 1898), NYPL Map Division, 160 ft to the inch (0.31 m per pixel), brick rose / frame
yellow / stone grey, (all four are clipped against the nine Sanborn layers and `kings_towns_1890` (`outside_layers` in `tools_brooklyn2/mk_layers.py`); the counts of
"traced" below are before that clip, "exported" after). Style `bromley_city` with the override measured on plate 8518 (stone filter: 200 m2, 6 m wide, aspect 4); the exporter's acceptance rule `require_match` 8 m. Layer
`brooklyn_bayridge_1898` (vol. 2, Ward 30, 12 plates) was written and then put on `ATLAS_SKIP` by the lead: six of its twelve plates could not be placed (their numbers were not recorded in a file;
`data/interim/atlas_brooklyn2/bayridge_run.out` is the log) and it is superseded here by `brooklyn_bayridge_1905`.

Checks (on the files as they are): all outlines valid, ids unique, centres in coverage, no overlapping pair in any of the four; outlines over 5,000 m2 (allowed to 20,000): 4 / 10 / 6 / 5;
centre within 8 m of a street line: 9.2 % (Sunset Park), 3.9 % (Red Hook), 10.9 % (Heights), 11.5 % (Williamsburg); the lead's roadway slivers: 133, 5, 74, 255 (2.7, 0.3, 2.9, 2.0 %).
Coverage = the plates' masks: 5.13, 2.46, 1.21, 8.87 km2. "Control points only" in the tables is the export's label for a plate with no street or building correction; those plates were accepted by
the exporter's rule (b): at least 10 outlines on standing footprints with a median offset of 4 m or less (or five consistent control points). Their offsets are in the last column.
That part's work folder holds overlays of plates 8518, 8519 and 8521 (`s8518.png` ...); no other plate of the four was looked at by that part or by me (its record of what it looked at was not written).


#### brooklyn_sunsetpark_1898

4933 outlines (3486 frame / 1445 brick / 2 stone), 4 plates used, 5.13 km2 of plate masks; 681 coincide with a standing footprint (IoU > 0.5).

| sheet | plate | gcps (CV rms m) | m/px | registration | street left m | traced | exported | on a standing footprint (median offset m) |
|---|---|---|---|---|---|---|---|---|
| B98-8518 | 8518 | 4 (9.5) | 0.308 | affine + affine (12 windows) | 1.9 | 2145 | 2117 | 222 (1.51) |
| B98-8519 | 8519 | 4 (12.4) | 0.304 | shift + shift (4 windows) | 3.3 | 1285 | 1280 | 227 (1.58) |
| B98-8520 | 8520 | 3 (0.0) | 0.305 | shift + affine (8 windows) | 1.0 | 1396 | 1379 | 230 (1.7) |
| B98-8521 | 8521 | 8 (2.7) | 0.308 | control points only | None | 240 | 157 | 2 (2.94) |

#### brooklyn_redhook_1898

1631 outlines (621 frame / 980 brick / 30 stone), 3 plates used, 2.46 km2 of plate masks; 91 coincide with a standing footprint (IoU > 0.5).

| sheet | plate | gcps (CV rms m) | m/px | registration | street left m | traced | exported | on a standing footprint (median offset m) |
|---|---|---|---|---|---|---|---|---|
| B98-8515 | 8515 | 5 (1.7) | 0.307 | shift + shift (6 windows) | 0.5 | 4235 | 1004 | 66 (1.54) |
| B98-8516 | 8516 | 31 (4.8) | 0.306 | control points only | None | 1040 | 160 | 1 (1.68) |
| B98-8517 | 8517 | 45 (1.8) | 0.307 | shift + affine (5 windows) | 1.0 | 1165 | 467 | 24 (2.53) |

#### brooklyn_heights_1898

2541 outlines (1142 frame / 1399 brick / 0 stone), 3 plates used, 1.21 km2 of plate masks; 77 coincide with a standing footprint (IoU > 0.5).

| sheet | plate | gcps (CV rms m) | m/px | registration | street left m | traced | exported | on a standing footprint (median offset m) |
|---|---|---|---|---|---|---|---|---|
| B98-8512 | 8512 | 4 (21.3) | 0.31 | control points only | None | 4438 | 1620 | 31 (1.79) |
| B98-8513 | 8513 | 7 (12.9) | 0.309 | control points only | None | 4772 | 177 | 6 (1.73) |
| B98-8514 | 8514 | 4 (4.2) | 0.308 | affine + affine (24 windows) | 1.5 | 4395 | 744 | 40 (1.54) |

#### brooklyn_williamsburg_1898

12650 outlines (10070 frame / 2569 brick / 11 stone), 7 plates used, 8.87 km2 of plate masks; 1178 coincide with a standing footprint (IoU > 0.5).

| sheet | plate | gcps (CV rms m) | m/px | registration | street left m | traced | exported | on a standing footprint (median offset m) |
|---|---|---|---|---|---|---|---|---|
| B98-8459 | 8459 | 5 (27.0) | 0.305 | control points only | None | 3035 | 2934 | 145 (1.6) |
| B98-8461 | 8461 | 5 (8.4) | 0.307 | affine + affine (20 windows) | 1.1 | 2281 | 1780 | 308 (1.66) |
| B98-8462 | 8462 | 7 (2.4) | 0.306 | control points only | None | 1155 | 1119 | 287 (1.63) |
| B98-8463 | 8463 | 5 (9.9) | 0.303 | affine + affine (24 windows) | 1.2 | 3425 | 1542 | 188 (1.46) |
| B98-8465 | 8465 | 4 (5.0) | 0.308 | shift + shift (8 windows) | 2.7 | 4627 | 2909 | 48 (1.63) |
| B98-8469 | 8469 | 5 (8.1) | 0.307 | control points only | None | 4234 | 1063 | 177 (1.59) |
| B98-8522 | 8522 | 4 (98.1) | 0.304 | control points only | None | 1363 | 1303 | 25 (2.51) |


All four are later states (1898) than the three layers above and are not affected by them.
Heights' plate 8512 (traced 4,438, exported 1,620) and 8513 (4,772 traced, 177 exported) lose most of their outlines to the clip against the Sanborn masks: those plates lie over the downtown Sanborn plates.

## New layers: per-plate tables


#### brooklyn_old_1880

2174 outlines (1908 frame / 266 brick / 0 stone), 14 plates used, 17.15 km2 of plate masks; 25 coincide with a standing footprint (IoU > 0.5).

| sheet | plate | gcps (CV rms m) | m/px | registration | street left m | traced | exported | on a standing footprint (median offset m) |
|---|---|---|---|---|---|---|---|---|
| H80-7984 | 7984 | 5 (6.9) | 0.423 | affine + affine (50 windows) | 2.5 | 957 | 98 | 1 (1.63) |
| H80-7985 | 7985 | 5 (15.2) | 0.425 | shift + affine (7 windows) | 1.8 | 55 | 31 | 0 (None) |
| H80-7986 | 7986 | 4 (107.3) | 0.424 | affine + affine (56 windows) | 2.2 | 638 | 114 | 0 (1.88) |
| H80-7987 | 7987 | 8 (5.0) | 0.424 | affine + affine (17 windows) | 1.8 | 172 | 91 | 0 (2.33) |
| H80-7990 | 7990 | 3 (0.0) | 0.284 | shift + shift (8 windows) | 3.1 | 214 | 22 | 0 (2.41) |
| H80-7991 | 7991 | 4 (0.8) | 0.283 | affine + affine (15 windows) | 1.5 | 61 | 42 | 1 (4.26) |
| H80-7992 | 7992 | 3 (0.0) | 0.29 | affine + affine (14 windows) | 1.0 | 138 | 40 | 0 (2.36) |
| H80-7993 | 7993 | 3 (0.0) | 0.286 | affine + affine (12 windows) | 2.8 | 291 | 253 | 2 (4.44) |
| H80-7994 | 7994 | 3 (0.0) | 0.287 | affine + affine (16 windows) | 1.9 | 395 | 324 | 1 (5.79) |
| H80-7996 | 7996 | 4 (7.7) | 0.422 | affine + affine (13 windows) | 2.1 | 211 | 186 | 0 (None) |
| H80-8003 | 8003 | 4 (8.1) | 0.288 | shift + affine (9 windows) | 3.2 | 409 | 0 | 0 (2.58) |
| H80-8008 | 8008 | 3 (0.0) | 0.286 | affine + shift (10 windows) | 0.6 | 86 | 60 | 0 (None) |
| H80-8011 | 8011 | 5 (5.0) | 0.287 | affine + affine (24 windows) | 1.5 | 943 | 845 | 20 (2.14) |
| H80-8014 | 8014 | 4 (6.5) | 0.284 | shift + affine (6 windows) | 1.7 | 109 | 68 | 0 (None) |

Left out: H80-8010 (8010; 19 traced; left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 9.1 m)); H80-8015 (8015; None traced; left out: street match left 5.2 m after a 20 m correction (control points CV rms 40 m); 18 outlines outside the Sanborn layers); H80-8016 (8016; 501 traced; left out: not placed reliably (no street or building match; 2 outlines on standing footprints, median offset 2.71 m; control points CV rms 78.5 m))

#### brooklyn_bayridge_1905

7239 outlines (2675 frame / 4523 brick / 41 stone), 30 plates used, 18.87 km2 of plate masks; 1166 coincide with a standing footprint (IoU > 0.5).

| sheet | plate | gcps (CV rms m) | m/px | registration | street left m | traced | exported | on a standing footprint (median offset m) |
|---|---|---|---|---|---|---|---|---|
| H05-15992 | 15992 | 153 (11.7) | 0.169 | affine + affine (16 windows) | 2.6 | 486 | 380 | 52 (1.04) |
| H05-15993 | 15993 | 4 (1.7) | 0.17 | affine + affine (19 windows) | 3.0 | 426 | 410 | 70 (1.73) |
| H05-15995 | 15995 | 4 (0.9) | 0.169 | affine + shift (10 windows) | 4.1 | 121 | 114 | 18 (1.36) |
| H05-15997 | 15997 | 4 (0.7) | 0.171 | affine + affine (18 windows) | 4.2 | 167 | 139 | 7 (2.44) |
| H05-15998 | 15998 | 4 (1.5) | 0.17 | affine + affine (15 windows) | 3.1 | 389 | 372 | 45 (1.2) |
| H05-15999 | 15999 | 4 (0.9) | 0.171 | affine + affine (18 windows) | 3.1 | 257 | 226 | 64 (2.09) |
| H05-16000 | 16000 | 4 (0.8) | 0.17 | affine + affine (18 windows) | 1.6 | 161 | 144 | 3 (2.26) |
| H05-16001 | 16001 | 4 (1.5) | 0.17 | affine + affine (17 windows) | 2.9 | 239 | 208 | 72 (1.37) |
| H05-16002 | 16002 | 4 (2.7) | 0.17 | affine + affine (16 windows) | 1.6 | 486 | 381 | 102 (1.33) |
| H05-16003 | 16003 | 4 (5.3) | 0.172 | shift + shift (6 windows) | 2.4 | 68 | 65 | 7 (1.64) |
| H05-16005 | 16005 | 4 (3.1) | 0.171 | affine + affine (15 windows) | 2.9 | 682 | 639 | 205 (1.36) |
| H05-16006 | 16006 | 4 (1.6) | 0.17 | shift + affine (7 windows) | 3.4 | 270 | 253 | 55 (1.56) |
| H05-16007 | 16007 | 4 (1.7) | 0.17 | affine + affine (20 windows) | 3.4 | 329 | 315 | 65 (1.37) |
| H05-16008 | 16008 | 4 (1.0) | 0.17 | affine + affine (21 windows) | 2.9 | 436 | 419 | 53 (1.38) |
| H05-16009 | 16009 | 4 (0.7) | 0.17 | affine + affine (15 windows) | 5.0 | 290 | 279 | 35 (1.89) |
| H05-16010 | 16010 | 4 (1.4) | 0.171 | affine + affine (16 windows) | 2.9 | 555 | 533 | 113 (1.47) |
| H05-16011 | 16011 | 4 (1.5) | 0.17 | affine + affine (19 windows) | 2.5 | 180 | 167 | 16 (1.24) |
| H05-16012 | 16012 | 4 (1.8) | 0.17 | affine + affine (18 windows) | 2.7 | 416 | 409 | 3 (0.87) |
| H05-16013 | 16013 | 52 (2.8) | 0.17 | affine + affine (12 windows) | 3.4 | 360 | 359 | 7 (1.3) |
| H05-16014 | 16014 | 4 (3.1) | 0.17 | affine + affine (18 windows) | 3.2 | 187 | 171 | 53 (1.84) |
| H05-16015 | 16015 | 4 (1.1) | 0.169 | affine + affine (18 windows) | 1.4 | 230 | 225 | 2 (1.7) |
| H05-16016 | 16016 | 4 (1.7) | 0.169 | affine + affine (17 windows) | 4.2 | 114 | 100 | 5 (2.06) |
| H05-16017 | 16017 | 4 (1.9) | 0.169 | affine + affine (22 windows) | 2.8 | 252 | 243 | 58 (1.3) |
| H05-16018 | 16018 | 4 (1.7) | 0.17 | affine + affine (16 windows) | 1.6 | 125 | 107 | 6 (0.82) |
| H05-16019 | 16019 | 4 (2.0) | 0.169 | affine + affine (17 windows) | 2.2 | 56 | 42 | 0 (None) |
| H05-16020 | 16020 | 4 (32.4) | 0.17 | affine + affine (19 windows) | 1.4 | 99 | 94 | 1 (0.63) |
| H05-16021 | 16021 | 4 (0.7) | 0.172 | affine + affine (11 windows) | 2.2 | 130 | 113 | 3 (1.07) |
| H05-16023 | 16023 | 4 (2.1) | 0.169 | affine + affine (12 windows) | 1.2 | 118 | 105 | 7 (1.77) |
| H05-16024 | 16024 | 4 (4.1) | 0.169 | affine + affine (17 windows) | 2.3 | 168 | 113 | 7 (1.86) |
| H05-16026 | 16026 | 4 (1.8) | 0.168 | affine + affine (16 windows) | 3.0 | 121 | 114 | 32 (1.37) |

Left out: H05-16004 (16004; 119 traced; left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 112.0 m)); H05-16025 (16025; 13 traced; left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 146.7 m))

#### brooklyn_coney_1907

2613 outlines (2540 frame / 67 brick / 6 stone), 13 plates used, 8.21 km2 of plate masks; 16 coincide with a standing footprint (IoU > 0.5).

| sheet | plate | gcps (CV rms m) | m/px | registration | street left m | traced | exported | on a standing footprint (median offset m) |
|---|---|---|---|---|---|---|---|---|
| H07-16051 | 16051 | 4 (2.8) | 0.169 | shift + shift (8 windows) | 3.6 | 45 | 43 | 0 (None) |
| H07-16052 | 16052 | 4 (27.8) | 0.182 | shift + shift (7 windows) | 3.5 | 126 | 110 | 0 (None) |
| H07-16053 | 16053 | 8 (3.7) | 0.17 | affine + affine (12 windows) | 1.3 | 115 | 107 | 2 (2.03) |
| H07-16054 | 16054 | 4 (1.9) | 0.17 | affine + affine (12 windows) | 0.7 | 148 | 132 | 1 (1.71) |
| H07-16055 | 16055 | 4 (1.8) | 0.17 | affine + affine (16 windows) | 1.1 | 329 | 298 | 0 (None) |
| H07-16056 | 16056 | 4 (0.3) | 0.17 | shift + shift (5 windows) | 3.0 | 677 | 633 | 6 (2.03) |
| H07-16057 | 16057 | 5 (8.8) | 0.169 | affine + affine (10 windows) | 5.1 | 479 | 425 | 1 (3.55) |
| H07-16059 | 16059 | 4 (1.8) | 0.169 | affine + affine (18 windows) | 1.9 | 34 | 28 | 1 (1.78) |
| H07-16061 | 16061 | 4 (10.0) | 0.168 | shift (4 windows) | 5.7 | 188 | 159 | 0 (None) |
| H07-16066 | 16066 | 4 (1.3) | 0.166 | shift + shift (6 windows) | 4.0 | 45 | 26 | 0 (None) |
| H07-16067 | 16067 | 4 (1.5) | 0.167 | affine + affine (19 windows) | 2.2 | 51 | 40 | 0 (None) |
| H07-16068 | 16068 | 4 (1.9) | 0.168 | affine + affine (15 windows) | 1.9 | 528 | 497 | 3 (2.72) |
| H07-16069 | 16069 | 4 (2.9) | 0.168 | affine + affine (11 windows) | 1.7 | 123 | 115 | 2 (2.97) |

Left out: H07-16048 (16048; 25 traced; left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 32.2 m)); H07-16058 (16058; 25 traced; left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 2.2 m)); H07-16060 (16060; 222 traced; left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 0.0 m)); H07-16065 (16065; 47 traced; left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 16.9 m)); H07-16073 (16073; 35 traced; left out: not placed reliably (no street or building match; 0 outlines on standing footprints, median offset None m; control points CV rms 1.1 m))

