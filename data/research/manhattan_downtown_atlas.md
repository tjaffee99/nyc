# Manhattan south of 40th Street, 1897 (Bromley) - `manhattan_downtown_1897`

Round of 2026-11-12 (`docs/ROUND4.md`). One layer, `data/manual/atlas/manhattan_downtown_1897.geojson` (+ `_coverage`,
`_stats`): 41,254 outlines (3,788 frame, 37,422 brick, 6 stone, 38 gasholders) on 20 plates, 19.6 km2 of plate
coverage (water and piers included), cut at the same line as the Midtown layer (the 40th St centreline, so no building is
in both layers: 0 outlines of this layer overlap an outline of `manhattan_midtown_1897`). With it the island has one
continuous traced state of 1897 from the Battery to the Harlem layer's edge at 125th St (Inwood excepted, below).

## Source and tool

Bromley, *Atlas of the city of New York, Manhattan Island* (1897), NYPL Map Division (public domain), full-size masters
`https://images.nypl.org/index.php?id=<imageId>&t=u` (image ids 1516758-1516769, 1516772, 1516777, 1516787-1516792).
Control points and masks: NYPL Map Warper records in the NYC Space/Time Directory dump (CC0); plate 19 (900019) from
`tools/gcps_own.json` of the Midtown layer. Tool: `data/manual/atlas/tools_downtown/atlas.py`, a copy of `tools/atlas.py`
with the Midtown layer's settings unchanged (`layers.json`: same `bromley_city` style and `style_override`, blue
gasholders, stone filters) and four changes:
* `export` knows `clip.south_of` (the mirror of `north_of`);
* a plate's entry in `layers.json` may give `paper` (the paper's Lab colour) and its own `style_override`;
* `overlay` colours the `iron` class;
* work files under `data/interim/atlas_downtown/`, scans under `data/raw/atlas/downtown/` (285 MB, gitignored).
`run_plate.sh` (trace, then the building match) and `run_reg2.sh` (second building-match pass, as on Midtown) are the
whole run: about 20 s of tracing and 40 s of registration per plate, under 1.5 GB.

Every plate of the atlas south of 40th St is in the Map Warper dump; none had to be placed by hand. Plates 1, 8, 9, 10,
12, 14, 15, 17 carry their number in the title, the others ("Part of Section 1 / 1 & 2 / 2 / 3") only their image id
(table). Two plates of the Midtown layer (19 and image 1516788; their registration files copied from
`data/interim/atlas/manhattan_midtown_1897/`, so the registration is the same) were traced again for the strip between 36th
and 40th St that the Midtown layer cut off (1,571 outlines kept of the 1,611 the Midtown note says it cut); Plate 21 was tried
the same way, contributed nothing south of the line and is not in the layer.

## Two plates needed a setting of their own

* **Plate 8 (image 1516764, the Bowery, Little Italy, the Lower East Side north of Houston): paper colour.** The plate is
  four fifths brick; the mode of its light pixels is the rose of the brick (Lab 67, 11, 5) and the tool read the tan of the
  street tint as frame buildings (492 outlines, none of them buildings, 2 coinciding with a standing footprint). Given the
  paper of the other plates (Lab 82, 0, 10): 2,754 outlines, 302 coinciding.
* **Plate 1 (image 1516758, the Battery to Wall St and the Seaport): brick pigment.** Its rose is greyer (median a 7.1, b 7.0
  against a 9.8, b 5.2 on Plate 8); with the standard `da_min` 7.5 half the fill was missed and the tracing came out as
  ragged blobs over the lettering (974 outlines). With `da_min` 4.5 (and the other brick limits as before) the outlines
  follow the lots (1,193 kept). Looked at (the Wall St - Broad St - Exchange Pl blocks): the outlines follow the
  lots; the stone-front strips are separate grey pieces, as everywhere.

## Checks, per plate

Method as the README's: control points, then the building match twice (240 m windows, outlines against today's footprints of
pre-war buildings); there is no street tint on a Bromley plate, so no street match. Last two columns: the share of outlines
within 8 m of a street centre line (the lead's `ATLAS_SKIP` test) next to the same share measured on the Perris 1854 outlines
(`map_1854`, a complete, independently registered survey) inside the same plate, and the outlines with no building of the map
standing in 1897 under them (below).

| sheet | Map Warper id | NYPL image | control points (fit, CV rms m) | m / px | building match: windows agreeing / run, residual m | outlines kept (frame / brick / stone) | on a standing footprint (IoU > 0.5) | their median offset m | within 8 m of a street line (this layer / the 1854 outlines of the same plate) | new: no 1897 building of the map under it |
|---|---|---|---|---|---|---|---|---|---|---|
| image 1516792 | 8223 | 1516792 | 3 (affine, 0.0) | 0.242 | shift: 7/11, 0.97 | 1748 (182 / 1566 / 0) | 24 (1 %) | 2.18 | 11 % / 11 % | 394 (23 %) |
| 17 | 8222 | 1516791 | 10 (affine, 5.3) | 0.243 | affine: 57/66, 1.12 | 3136 (61 / 3072 / 3) | 113 (4 %) | 2.03 | 3 % / 5 % | 585 (19 %) |
| image 1516790 | 8221 | 1516790 | 23 (poly2, 1.0) | 0.242 | affine: 22/22, 0.93 | 2462 (140 / 2321 / 0) | 182 (7 %) | 1.46 | 10 % / 13 % | 436 (18 %) |
| 14 | 8220 | 1516789 | 20 (tps, 1.6) | 0.244 | affine: 49/60, 0.82 | 2755 (29 / 2725 / 1) | 209 (8 %) | 2.05 | 2 % / 3 % | 527 (19 %) |
| image 1516769 | 8200 | 1516769 | 4 (affine, 2.6) | 0.245 | affine: 45/48, 0.63 | 2111 (288 / 1814 / 0) | 221 (10 %) | 1.46 | 8 % / 8 % | 479 (23 %) |
| image 1516767 | 8198 | 1516767 | 22 (affine, 1.4) | 0.247 | affine: 75/75, 1.05 | 2753 (90 / 2661 / 2) | 486 (18 %) | 1.59 | 8 % / 12 % | 504 (18 %) |
| 12 | 8199 | 1516768 | 8 (affine, 1.9) | 0.245 | affine: 33/33, 0.58 | 2725 (241 / 2474 / 0) | 388 (14 %) | 1.3 | 10 % / 17 % | 715 (26 %) |
| 15 | 8203 | 1516772 | 4 (affine, 995.0) | 0.245 | shift: 8/8, 0.57 | 1333 (140 / 1175 / 0) | 70 (5 %) | 1.14 | 13 % / 15 % | 553 (41 %) |
| 10 | 8197 | 1516766 | 10 (affine, 11.1) | 0.247 | affine: 52/56, 1.79 | 2586 (283 / 2303 / 0) | 256 (10 %) | 1.63 | 29 % / 35 % | 509 (20 %) |
| 9 | 8196 | 1516765 | 15 (affine, 3.3) | 0.245 | affine: 33/42, 0.99 | 2573 (519 / 2054 / 0) | 206 (8 %) | 1.7 | 29 % / 26 % | 523 (20 %) |
| 8 | 8195 | 1516764 | 49 (tps, 1.5) | 0.246 | affine: 46/47, 1.25 | 2754 (257 / 2497 / 0) | 302 (11 %) | 1.87 | 28 % / 41 % | 676 (25 %) |
| image 1516763 | 8194 | 1516763 | 32 (tps, 1.1) | 0.245 | affine: 11/11, 0.16 | 2425 (355 / 2070 / 0) | 133 (6 %) | 1.24 | 33 % / 31 % | 658 (27 %) |
| image 1516762 | 8193 | 1516762 | 18 (tps, 1.4) | 0.244 | shift: 6/6, 0.2 | 1776 (231 / 1545 / 0) | 81 (5 %) | 1.53 | 24 % / 27 % | 349 (20 %) |
| image 1516761 | 8192 | 1516761 | 34 (tps, 1.3) | 0.245 | affine: 30/33, 0.81 | 2283 (256 / 2027 / 0) | 277 (12 %) | 1.57 | 30 % / 42 % | 458 (20 %) |
| image 1516760 | 8191 | 1516760 | 16 (affine, 2.2) | 0.247 | affine: 41/50, 1.23 | 1893 (284 / 1609 / 0) | 240 (13 %) | 2.39 | 23 % / 30 % | 321 (17 %) |
| image 1516759 | 8190 | 1516759 | 20 (affine, 1.2) | 0.246 | shift: 6/7, 0.67 | 1842 (166 / 1676 / 0) | 63 (3 %) | 1.76 | 32 % / 40 % | 448 (24 %) |
| image 1516777 | 8208 | 1516777 | 26 (affine, 1.3) | 0.244 | affine: 28/38, 1.13 | 1335 (30 / 1305 / 0) | 88 (7 %) | 2.15 | 23 % / 37 % | 307 (23 %) |
| 1 | 8189 | 1516758 | 39 (tps, 2.5) | 0.246 | affine: 21/25, 1.52 | 1193 (39 / 1154 / 0) | 33 (3 %) | 3.2 | 33 % / 46 % | 228 (19 %) |
| 19 | 900019 | 1516787 | 30 (poly2, 2.6) | 0.246 | affine: 21/23, 0.71 | 789 (161 / 628 / 0) | 34 (4 %) | 1.84 | 16 % / 10 % | 180 (23 %) |
| image 1516788 | 8219 | 1516788 | 38 (poly2, 1.3) | 0.246 | affine: 46/51, 1.98 | 782 (36 / 746 / 0) | 25 (3 %) | 4.37 | 8 % / 13 % | 138 (18 %) |
{'layer': 'manhattan_downtown_1897', 'plates': 20, 'buildings': 41254, 'frame': 3788, 'brick': 37422, 'stone': 6, 'gasholders': 38, 'on_today': 3431, 'invalid': 0, 'area_out_of_range': 0, 'outside_coverage': 0, 'coverage_km2': 19.59}

(In this table the Midtown plates 19 and image 1516788 count only the strip south of 40th St.) Totals: 41,254 outlines,
3,431 (8 %) coincide with a standing footprint at a median 1.1-4.4 m (per plate above); the export dropped 190
lettering pieces, 534 pieces of water wash, 30 duplicates, and cut 5,570 outlines north of the line.

**Street share.** 18 % of the outlines lie within 8 m of a street centre line (3-13 % on the 14th-40th St plates, 21-33 % on
the downtown plates). The share is set by street width: below Houston St the old streets are 10-15 m wide and any house on
them is within 8 m of the centre line. The 1854 outlines give 27-46 % on the same downtown plates and 3-13 % on the grid
plates, so the layer sits on the same lines as the Perris survey: below its share on 17 of the 20 plates and 2-6 points above it on
three (9, 19, image 1516763). Under the lead's 30 % skip level as a whole (18 %); five downtown plates are at 28-33 %, all within
their 1854 reference.

**Plates that rest on few anchors.** 8189 (Plate 1: 21 windows, 3 % of its outlines on standing footprints, median 3.2 m
because almost everything there is rebuilt; the lots on the picture sit on the footprints that remain, looked at), 8203
(Plate 15, the Stuyvesant Town ground: four Map Warper points that fit badly, CV 995 m, so the plate stands on the 8 building
windows - 70 outlines coincide at 1.1 m; the area is cleared today, which is why so few footprints exist; looked at: the
blocks, gasholder and lot rows are clean, but its registration cannot be checked against anything else), 8223 (3 points,
7 windows, 24 coincide; looked at: the Chelsea rows near Ninth Av, the church and the rows that stand today sit on their footprints), 8193 and 8190
(6 windows). The second pass moved none of them by more than 0.6 m.

## Looked at (outlines drawn over the scan, windows of 300-450 m)

Plate 1 (Wall St - Broad St), plate 8 (the Bowery at Stanton St, before and after the paper fix), plate 8190 (Fulton - Ferry -
Peck Slip - Pearl St: tracing ragged but one outline per lot, stairs along slanted edges, block lettering bites into houses),
plate 8194 (Stanton - Rivington St at Clinton St: tenements house by house, rear tenements and sheds; crossed stables come out as
triangles, as in the Midtown note), plate 8203 (E 14th - 18th St east of Avenue A: lots, coal yards, the gasholder, a gas
works circle recognised as iron), plate 8223 (Chelsea, W 28th - 22nd St at Ninth Av: houses, the Church of the Holy Apostles
as stone). 20 plates, 7 windows: the other plates were not looked at.

## What the earlier layers already held (nyc_buildings.parquet, rows standing in 1897 inside the plates' masks)

| district (plates) | km2 | rows standing in 1897 | of them pulled down since | from the 1890s layers / traced_1897 | Perris 1854 / atlas 1857 rows still standing by an estimated end | generated fill | still standing today |
|---|---|---|---|---|---|---|---|
| Chelsea, Garment district, Murray Hill, Gramercy (8223, 8222, 8221, 8220, 8200) | 5.7 | 15,726 | 13,404 | 2,948 | 9,620 | 766 | 2,322 |
| Greenwich Village, West Village (8197, 8196, 8198) | 3.3 | 10,164 | 7,004 | 532 | 6,201 | 208 | 3,160 |
| East Village, Lower East Side north of Houston (8199, 8195, 8203) | 3.1 | 8,333 | 6,561 | 324 | 5,613 | 561 | 1,772 |
| Lower East Side, Chinatown (8194, 8193, 8192) | 2.6 | 9,467 | 8,412 | 2,224 | 5,894 | 166 | 1,055 |
| Tribeca, SoHo, Civic Center, Financial District, the Battery (8191, 8190, 8208, 8189) | 4.1 | 8,388 | 7,065 | 2,171 | 4,571 | 212 | 1,323 |

("From the 1890s layers": atlas_1890 / 1894 / 1895 / 1893 rows, i.e. NYPL's Building Inspector layers.) The 1890s layers are
nearly complete on no plate: the best coverage is the Chelsea / Murray Hill plates 17, image 1516790 and 1516792 (about 750-950
rows each on 1.1 km2, against 2,000-3,000 outlines of this layer on the same plates), the Lower East Side's image 1516760-1516763
and Plate 1 (360-790 each). Elsewhere (Plates 8, 9, 10, 12, 14, 15: 3-130 rows each) most of what the map shows for 1897 is
the Perris survey of 1854-57 with an estimated end year, generated lots, or buildings that still stand. The map's 1854
rows are real outlines but they say what stood 40 years earlier: of the 41,254 outlines, 14,937 coincide (at least half of the
outline) with one of those 1854 / 1857 rows.

## New information

Outline counted as *new* when buildings the map has standing in 1897 (any source) cover less than half of it.

| district | outlines | no 1897 building of the map under them | no building from a 1890s layer, or still standing, or a researched / LPC row under them |
|---|---|---|---|
| Chelsea, Garment district, Murray Hill, Gramercy (14th-40th St) | 13,783 | 2,739 (20 %) | 8,649 (63 %) |
| Greenwich Village, West Village | 7,912 | 1,536 (19 %) | 4,621 (58 %) |
| East Village, Lower East Side north of Houston | 6,812 | 1,944 (29 %) | 4,947 (73 %) |
| Lower East Side, Chinatown | 6,484 | 1,465 (23 %) | 4,037 (62 %) |
| Tribeca, SoHo, Civic Center, Financial District, the Battery | 6,263 | 1,304 (21 %) | 3,555 (57 %) |
| **all** | **41,254** | **8,988 (22 %)** | **25,809 (63 %)** |

Right column: under it only Perris rows (`map_1854`, `atlas_1857`, real outlines of 1854-57 whose end year is an estimate),
generated lots, or nothing - no record of the 1890s and no standing building. These 63 % are not "missing
buildings": most of them are the same houses as the Perris rows, now with a surveyed outline for 1897. The 8,988 in the middle
column are houses (and extensions, sheds, rear tenements, 1860-97 infill) that the map had no outline for at all in 1897. The
districts: the figures of the East Village (29 %) and Plate 15 (41 %, the cleared Avenue A - D ground) are highest.

## What is not covered, and Inwood

* Governors Island, Ellis Island and the other islands are on no plate of this part (19 of the 60,778 buildings of the 1854-57 maps south of 40th St
  lie outside the coverage, at Governors Island's position). Piers are drawn as the atlas draws them (hatched, not read).
* Not complete, as the README says for every layer: crossed stables and sheds come out in pieces; the lettering of block numbers
  bites into the outlines of rows and some stone buildings (churches) are missing; stone fronts are separate pieces; recall was
  not measured on this layer (the Midtown layer's 93 % is the nearest figure).
* **Inwood (plate 45, image 1516775): not delivered.** The scan was fetched and 22 control points made - the crossings of Tenth and
  Ninth Av with W 203rd-216th St (today's centre lines; the avenues from the row profile of the scan, the streets' x positions
  read from the ink profile and fitted as evenly spaced, 3.2 m cross-validated, `gcps_own.json` id 900045, layer entry
  `manhattan_inwood_1897` in `layers.json`) - and the plate traced (214 candidates). Not handed over: (1) the plate shows
  Inwood almost unbuilt in 1897 - the grid of lots drawn at length, a few dozen houses; (2) the traced candidates include
  lettering and ruled lot lines; (3) the building match found no windows (0 coincide) to confirm the hand-made registration, and
  a picture of the blocks against today's footprints shows the plate about ten metres off in places. "A layer that is 15 m off is
  worse than no layer". Inwood's 1897 houses still wait for tracing with better control (Dyckman farmhouse, Isham Park and the
  surviving churches as anchors).
