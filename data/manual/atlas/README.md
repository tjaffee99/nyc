# Building footprints traced from real-estate atlases

What stood where the fire-insurance tracings (Manhattan below 86th St, downtown Brooklyn) say nothing: the
buildings drawn on the coloured real-estate atlases of the 1880s-90s, read plate by plate from the New York
Public Library's scans. Every outline is a fill the atlas itself colours as a building; nothing is generated.
What the atlas does not give (years of construction and demolition, heights) is not in these files.

| layer | atlas | area | buildings |
|---|---|---|---|
| `kings_towns_1890.geojson` | *Robinson's atlas of Kings County, New York* (E. Robinson, 1890), 29 of its 31 plates | the county towns before they joined Brooklyn: Flatbush, New Utrecht (Bay Ridge, Fort Hamilton, Bath Beach, Bensonhurst), Gravesend (the village, Coney Island, Sheepshead Bay), Flatlands (Canarsie in part) | 6,914 (6,795 frame, 119 brick) |
| `harlem_1897.geojson` | *Atlas of the city of New York, Manhattan Island* (G. W. & W. S. Bromley, 1897), the 14 plates north of 84th / 86th St | Yorkville north of 84th St, East Harlem, the Upper West Side from 86th St, Morningside Heights, Harlem, Manhattanville, Hamilton Heights, Washington Heights to about 190th St | 18,386 (3,057 frame, 15,323 brick, 6 stone) |
| `bronx_23rd_ward_1887.geojson` | *Atlas of the city of New York … 23rd Ward* (E. Robinson & R. H. Pidgeon, 1887), 18 of 21 plates (plate 6 is not in the dump; 16 and 20 left out) | the Bronx south of about 170th St: Mott Haven, Port Morris, Melrose, Morrisania, Hunts Point, Highbridge, Claremont | 5,456 (4,498 frame, 924 brick, 34 stone) |

Each layer has a `<layer>_coverage.geojson` (one polygon per plate read) and a `<layer>_stats.json` (the
numbers of the tables below, written by the export).

## Format

`<layer>.geojson`: FeatureCollection, WGS84 (CRS84), one Polygon per building, no holes. Properties:

| property | |
|---|---|
| `id` | `<source>_<sheet>_<n>` |
| `map_year` | the atlas's publication year (see *Map year and survey year*) |
| `material` | `frame` (the yellow / ochre fill), `brick` (the rose / carmine fill), `stone` (grey fill, city atlases only, rare) |
| `source` | `robinson_kings_1890`, `bromley_manhattan_1897`, `robinson_23rd_ward_1887` |
| `sheet` | plate number as printed, or `image <NYPL image id>` where the Map Warper title does not give it |
| `plate` | the plate's NYPL Map Warper id |
| `area_m2` | |
| `on_today` | true if the outline coincides with one of today's footprints (IoU > 0.5) — measured here for the checks; the pipeline should apply its own rule |
| `today_cover` | share of the outline lying on today's footprints of pre-war buildings (recorded year <= 1940, or none) |

`storeys` is **not** given: the Kings County and Bronx plates do not print it; the Bromley plates do (`3B`,
`4`, `5` in the front of each house) but the figures were not read.

`<layer>_coverage.geojson`: one Feature per plate (`sheet`, `plate`, `buildings`, `registration` — which
matches were applied, or "control points only, not checked" —, `street_match_left_m`,
`building_match_residual_m`, `registration_m` = median offset of the outlines that coincide with a standing
footprint, `coincide_share`): the Map Warper mask of the plate — the part of the sheet its georeferencer kept —
moved by the same correction as the buildings. Buildings are kept by their centre: an outline may reach a few
metres over the coverage edge.

## How to use the layers

* **Not complete.** Inside the coverage the tracing finds most buildings but not all (recall on the windows
  looked at: 95-98 % Kings County, about 93 % Harlem, about 88 % Bronx — see each layer). As with the other
  traced layers, absence is not evidence of an empty lot. Do not add these years to `COMPLETE`.
* **A row can be one polygon or a house can be two.** On the two city layers the houses of a row are cut at
  the party walls the atlas draws; where a wall line is faint two houses come out as one outline, where
  figures or a pencil line cross a house it comes out in pieces or with a bite out of it (about one outline in
  ten in the windows looked at). On the Kings County plates (300 ft to the inch) attached buildings are one
  outline. Hence many outlines of standing houses do **not** reach IoU 0.5 with today's footprint although
  they lie on it: `today_cover` is there to tell "lies on pre-war buildings" (probably the same fabric, or a
  pre-war replacement) from "lies on post-war buildings or open ground" (certainly gone).
* **Shapes are the atlas's.** At 1:3,600 (Kings County) a house is 10-25 pixels across; outlines are good to
  about a metre plus the registration, and edges that run at an angle to the scan keep a pixel staircase. The
  stone-front strip of a Bromley row house is joined to the house where the join was found; where not, the
  outline is 2 m short at the street.
* **Material** is the atlas's colour and is reliable for frame against brick. `stone` (the grey fill: churches,
  a few institutions) is nearly absent — see the lettering filter under *Method*; a brownstone-fronted brick
  house is `brick`.
* **X-crossed buildings** (stables, sheds, barns on the Robinson plates) are in the layer as buildings, without
  a flag.

## Map year and survey year

* Kings County: the plates looked at (3 and 22) are marked "Entered according to Act of Congress in the year
  1889 by E. Robinson"; the atlas was published in 1890. `map_year` is 1890; a building on it stood by 1889.
* Manhattan: published 1897 (NYPL catalogue date). The collars were not read for a survey date. The NYPL copy
  carries later pencil and blue-crayon lines (not buildings; they are not traced, but they cut a few outlines).
* Bronx: published 1887 (NYPL catalogue date); collars not read.

## Sources and licences

* Scans: NYPL Map Division, digital collections (public domain), full-size masters
  `https://images.nypl.org/index.php?id=<imageId>&t=u` (the image ids are in the tables). Kept as JPEG (quality
  95, no chroma subsampling) under `data/raw/atlas/nypl_u/` (gitignored, 0.8 GB for the 65 plates).
* Control points and masks: NYPL Map Warper records in the NYC Space/Time Directory dump
  `https://s3.amazonaws.com/spacetime-nypl-org/datasets/mapwarper/mapwarper.objects.ndjson` (CC0), as worked
  out for `data/manual/extents` (its `tools/warp.py` and `tools/streets.py` are reused, not copied).
* Today's streets and footprints used for registration and checks: Overture roads and the city's footprints
  (`data/raw/overture`, `data/interim/nyc_footprints_raw.parquet`).
* The tracings are this project's (CC0).

## Method (`tools/atlas.py`)

1. **Scan and first fit.** The plate's Map Warper control points give pixel -> ground (affine with 3-9
   points, 2nd order or thin-plate spline with more, chosen by cross-validation in `warp.py`). Most plates have
   only 4-5 points; the fits turned out 2-17 m out. (`warp.py` fits the two directions separately; with a
   spline they are 1-5 m apart, so here ground -> pixel is the forward fit inverted by iteration.)
2. **Street match** (`refine`; Kings County and Bronx). These atlases tint the streets. The tint is matched to
   today's street centrelines in windows of 400 m (300 m in the Bronx) by normalised cross-correlation; windows
   that agree give an affine correction (10 windows or more) or a constant shift (4 or more); two passes
   (search 30 m, then 15 m). The tables give how far the control-point fit was out ("shift found") and what the
   same measurement returns after the correction ("left").
3. **Building match** (`refine_buildings`; Manhattan and Bronx). The traced building mask is matched to
   today's footprints of pre-war buildings in 240 m windows (filled masks, so the rhythm of equal row houses
   cannot alias); the consensus corrects the plate again (affine with 10 windows, shift with 3). On the
   Manhattan plates it ran twice.
4. **Tracing.** Pixel classes in CIE Lab relative to the plate's paper colour: frame = the yellow / ochre
   fill, brick = the rose / carmine fill, stone = the grey fill, ink, and — on the county plates — the orange
   of the property bands. Drawn lines are found as thin dark features whatever they are drawn on.
   * *County plates* (`robinson_300ft`): property outlines are drawn as bands of the same pigments as the
     buildings. A building is a fill wider than a band (9 pixels) or a narrower one of the frame hue away from
     bands, **with an ink outline round at least 62 % of its edge** (30 % if compact) — a band has the lot line
     along one side only. Brick must be 11 pixels wide with 72 % outline. The ochre of the buildings runs to
     the orange of the bands on some sheets and some buildings: where no orange band lies within a 500-pixel
     cell (bands = long thin warm structures), the band hue is read as frame.
   * *City plates* (`bromley_city`, also used for the Bronx atlas): the fill of a row runs through from house
     to house; the party walls are the lot lines drawn across it. Walls = thin drawn lines that hang together
     (connected line components of 120 pixels or more, strokes 3 pixels thick or more left out as figures);
     each connected piece of fill between walls is a building; a small grey piece against a rose one is that
     house's stone front and is joined to it; pieces need an outline round 55 % (Bronx: 35 %, its lines are
     faint) of their edge.
   * Outlines are simplified to about one pixel; a shape that fills 84 % of its bounding rectangle becomes that
     rectangle. Buildings between 15 and 5,000 m2 are kept.
5. **Export**, with three filters for things that are not buildings (counts per plate in `<layer>_stats.json`):
   * *band pieces* (county plates): a "brick" outline under 50 m2 or filling less than 75 % of its rectangle
     is a piece of carmine band (three of the four brick outlines in Gravesend village were); a frame outline
     under 5 m wide and 4.5 times as long, or hook-shaped, is a piece of orange band. 296 dropped.
   * *lettering* (city plates): the bold block numbers and street names print in the grey of the stone fill; a
     `stone` outline under 80 m2 or filling less than 60 % of its rectangle is dropped (1,639 in the
     Bronx, 256 in Manhattan). Real stone buildings cut up by their own lettering go with them:
     churches are mostly missing.
   * *washed lots* (Bronx): the atlas washes some lots in a pale olive that passes the pixel test for the
     frame yellow. Each frame outline gets a yellow-strength score from the scan (`score_frames`); the scores
     of a plate fall in two groups with a gap between; 859 outlines of the weak group dropped.
   Then: buildings whose centre lies inside the plate's Map Warper mask; where two plates' masks overlap a
   building traced twice is kept once.

## Layers

### kings_towns_1890

Robinson's *Atlas of Kings County* (1890); "Scale 300 ft to the inch" is printed on the Gravesend plate (0.48 m
per pixel) and "200 ft" on Flatbush plate 3 (0.32 m); the other plates were not read for their scale and run
from 0.29 to 0.65 m per pixel (table). Buildings: ochre (frame), carmine (brick), stables and barns crossed.

<!-- TABLE kings_towns_1890 -->
| sheet | Map Warper id | NYPL image | control points (fit, CV rms m) | m / px | street match: windows agreeing, shift found m, left m | building match: windows, residual m | buildings (frame / brick / stone) | on a standing footprint (IoU > 0.5) | their median offset m | status |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 8526 | 1519717 | 5 (affine, 12.0) | 0.322 | affine: 34, 2.2, 2.2 | none | 262 (259 / 3 / 0) | 4 (2 %) | 2.26 | ok |
| 2 | 8527 | 1519718 | 4 (affine, 2.7) | 0.322 | affine: 39, 1.9, 1.9 | none | 605 (585 / 20 / 0) | 12 (2 %) | 1.79 | ok |
| 3 | 8528 | 1519719 | 4 (affine, 4.7) | 0.323 | affine: 38, 1.8, 1.1 | none | 335 (331 / 4 / 0) | 13 (4 %) | 1.3 | ok |
| 4 | 8529 | 1519720 | 4 (affine, 4.2) | 0.32 | affine: 26, 4.9, 1.7 | none | 322 (319 / 3 / 0) | 24 (8 %) | 1.2 | ok |
| 5 | 8530 | 1519721 | 6 (affine, 10.4) | 0.321 | affine: 47, 2.9, 1.4 | none | 47 (46 / 1 / 0) | 0 (0 %) |  | ok |
| 6 | 8531 | 1519722 | 5 (affine, 4.4) | 0.321 | affine: 41, 4.5, 2.3 | none | 261 (260 / 1 / 0) | 9 (3 %) | 1.95 | ok |
| 7 | 8532 | 1519723 | 4 (affine, 5.4) | 0.323 | affine: 28, 5.4, 1.4 | none | 357 (349 / 8 / 0) | 5 (1 %) | 1.49 | ok |
| 8 | 8533 | 1519724 | 4 (affine, 3.0) | 0.321 | affine: 34, 5.9, 1.4 | none | 115 (113 / 2 / 0) | 5 (4 %) | 1.92 | ok |
| 9 | 8534 | 1519725 | 4 (affine, 43.6) | 0.485 | affine: 38, 4.5, 2.0 | none | 405 (398 / 7 / 0) | 5 (1 %) | 2.49 | ok |
| 10 | 8535 | 1519726 | 4 (affine, 12.9) | 0.321 | affine: 32, 5.7, 2.3 | none | 71 (70 / 1 / 0) | 0 (0 %) |  | ok |
| 11 | 8536 | 1519727 | 4 (affine, 2.1) | 0.319 | affine: 38, 4.6, 2.0 | none | 171 (167 / 4 / 0) | 3 (2 %) | 1.21 | ok |
| 12 | 8537 | 1519728 | 4 (affine, 12.8) | 0.322 | affine: 31, 3.2, 2.5 | none | 107 (107 / 0 / 0) | 7 (6 %) | 1.4 | ok |
| 13 | 8538 | 1519729 | 4 (affine, 3.1) | 0.322 | affine: 16, 4.7, 1.5 | none | 76 (76 / 0 / 0) | 2 (3 %) | 4.04 | ok |
| 14 | 8539 | 1519730 | 4 (affine, 19.6) | 0.321 | affine: 33, 5.2, 1.9 | none | 94 (94 / 0 / 0) | 1 (1 %) | 1.27 | ok |
| 15 | 8540 | 1519731 | 4 (affine, 8.1) | 0.321 | affine: 44, 3.2, 2.2 | none | 75 (72 / 3 / 0) | 1 (1 %) | 0.82 | ok |
| 16 | 8541 | 1519732 | 6 (affine, 8.7) | 0.322 | affine: 44, 4.4, 1.6 | none | 180 (178 / 2 / 0) | 4 (2 %) | 1.85 | ok |
| 17 | 8542 | 1519733 | 4 (affine, 19.7) | 0.287 | affine: 12, 12.9, 6.6 | none | 364 (358 / 6 / 0) | 1 (0 %) | 0.53 | ok |
| 18 | 8543 | 1519734 | 25 (affine, 3.6) | 0.321 | affine: 24, 2.3, 2.9 | none | 244 (238 / 6 / 0) | 10 (4 %) | 1.45 | ok |
| 19 | 8544 | 1519735 | 4 (affine, 6.4) | 0.321 | affine: 38, 4.0, 2.1 | none | 72 (66 / 6 / 0) | 1 (1 %) | 1.61 | ok |
| 20 | 8545 | 1519736 | 10 (affine, 4.1) | 0.48 | affine: 14, 3.2, 1.2 | none | 131 (131 / 0 / 0) | 0 (0 %) |  | ok |
| 21 | 8546 | 1519737 | 17 (tps, 7.5) | 0.321 | affine: 19, 7.1, 4.0 | none | 462 (461 / 1 / 0) | 3 (1 %) | 3.22 | ok |
| 22 | 8547 | 1519738 | 39 (tps, 3.2) | 0.484 | affine: 46, 3.2, 2.0 | none | 196 (195 / 1 / 0) | 3 (2 %) | 1.74 | ok |
| 23 | 8548 | 1519739 | 5 (affine, 11.8) | 0.485 | affine: 75, 4.4, 2.9 | none | 235 (232 / 3 / 0) | 1 (0 %) | 1.52 | ok |
| 24 | 8549 | 1519740 | 4 (affine, 5.4) | 0.482 | affine: 76, 4.8, 2.6 | none | 140 (139 / 1 / 0) | 2 (1 %) | 2.64 | ok |
| 25 | 8550 |  |  (, ) |  | none | none | 0 (0 / 0 / 0) | 0 (0 %) |  | left out: the Map Warper control points place the plate about 6 km east of the streets its title names; no reliable match to today's streets was found (needs hand control points) |
| 26 | 8551 | 1519742 | 4 (affine, 7.9) | 0.646 | affine: 134, 11.8, 3.5 | none | 203 (199 / 4 / 0) | 3 (2 %) | 0.99 | ok |
| 27 | 8552 | 1519743 | 12 (tps, 1.6) | 0.644 | affine: 60, 2.3, 1.8 | none | 237 (233 / 4 / 0) | 3 (1 %) | 1.53 | ok |
| 28 | 8553 | 1519744 | 33 (tps, 2.8) | 0.323 | affine: 33, 2.3, 2.1 | none | 408 (405 / 3 / 0) | 10 (2 %) | 1.74 | ok |
| 29 | 8554 | 1519745 | 4 (affine, 3.8) | 0.647 | affine: 126, 5.1, 3.3 | none | 343 (328 / 15 / 0) | 1 (0 %) | 2.26 | ok |
| 30 | 8555 | 1519746 | 5 (affine, 5.9) | 0.483 | affine: 62, 3.5, 2.7 | none | 396 (386 / 10 / 0) | 6 (2 %) | 1.59 | ok |
| 31 | 8556 |  |  (, ) |  | none | none | 0 (0 / 0 / 0) | 0 (0 %) |  | left out: 3 control points; the street match finds the fit 15 m out (median) and no consistent correction |
| **all** | | | | | | | **6914** (6795 / 119 / 0) | 139 (2 %) | | 29 plates, 72.92 km2 |
<!-- /TABLE kings_towns_1890 -->

**Left out.** Plate 25 (Flatlands village, Avenue C to Avenue L between Ocean Av and Ralph Av): its Map
Warper control points place it about 6 km east of the streets its title names; a search for its true place on
today's streets was ambiguous (the grid repeats). It needs hand control points — **the Flatlands village is
therefore not in the layer.** Plate 31 (Canarsie, east part): 3 control points, 15 m out by the street match,
no consistent correction.

**Registration.** Every plate kept was corrected on its streets (the planned grid the atlas draws is today's
grid). The control-point fits were 2-13 m out (median 4.4 m); after the correction the same measurement leaves
1.1-4.0 m (median 2.1 m), except plate 17 (Bath Beach): 6.6 m, with a looser match (300 m windows, lower
threshold) because its village streets were replatted — treat that plate as good to about 7 m. The towns'
buildings have almost all gone; on the 11 plates with five or more standing buildings these sit 1.2-2.5 m
(median) from their footprints.

**Looked at** (plate crops with the outlines drawn on them):
* Gravesend village (plate 22, 480 m around Gravesend Neck Rd and McDonald Av), final layer: 88 buildings
  drawn, 87 traced (99 %); missed: one very small shed. Of the outlines, 2 are pieces of orange lot band and 4
  are extra pieces of the hotel on the main street, which lettering cuts up. (In the picture looked at the
  village's one brick building was missing, dropped by the band-piece filter; its threshold was then moved
  from 80 to 75 % and the building is in the layer — checked by its position, not by eye. The three pieces of
  carmine band in the window stay out.)
* South of the village (plate 22, 330 m): 16 outlines, all buildings; none missed that I could see.
* Flatbush, the gas works (plate 2, 190 m), traced afresh with the final settings: 31 drawn, 30 traced, no
  false outline.
* Bath Beach (plate 17, 230 m), final layer of an earlier run: about 50 drawn, 49 traced, no false outline.
* Coney Island, West 1st St and the hotels (plate 21, 300 m), final layer: about 93 drawn, 91 traced, no false
  outline; missed: a long narrow crossed shed (dropped as band-shaped) and one small building.

Two failures were found this way and repaired, and are the reason to expect others on plates not looked at:
the Flatbush window first returned 6 of 31 (the frame fill there is as orange as the property bands of other
sheets) and the Coney Island window about 70 % (the frame fill there is pale; a lightness limit was dropping
it). The colourists' pigments differ from sheet to sheet; 25 of the 29 plates were not looked at.

**Known failures.** Pieces of wide orange band read as frame buildings (2 in 95 in the village; the shape
filter removes the long and hooked ones). Buildings standing on a band of their own colour are missed or
merged with it. Large buildings covered with lettering break into pieces. Attached buildings are one outline.
Brick is under-read (the filter against band pieces is strict).

### harlem_1897

Bromley's *Atlas of the city of New York, Manhattan Island* (1897): plates 31, 32, 34, 36, 37, 38, 40, 42 and
six plates the Map Warper titles only call "Part of Section …" (image ids in the table); 0.24 m per pixel
(the scale statement was not read), the two northern plates smaller (0.32 and 0.49 m). Rose = brick, grey strip
along the front = stone front, grey = stone, yellow = frame.

<!-- TABLE harlem_1897 -->
| sheet | Map Warper id | NYPL image | control points (fit, CV rms m) | m / px | street match: windows agreeing, shift found m, left m | building match: windows, residual m | buildings (frame / brick / stone) | on a standing footprint (IoU > 0.5) | their median offset m | status |
|---|---|---|---|---|---|---|---|---|---|---|
| image 1516793 | 8224 | 1516793 | 34 (tps, 1.2) | 0.245 | none | affine: 56, 0.81 | 2268 (268 / 2000 / 0) | 210 (9 %) | 2.11 | ok |
| 31 | 8225 | 1516794 | 5 (affine, 5.4) | 0.244 | none | affine: 24, 0.55 | 838 (124 / 714 / 0) | 144 (17 %) | 2.11 | ok |
| 32 | 8226 | 1516795 | 25 (tps, 1.2) | 0.243 | none | affine: 18, 0.58 | 1561 (208 / 1353 / 0) | 134 (9 %) | 1.33 | ok |
| 36 | 8230 | 1516799 | 20 (tps, 1.3) | 0.244 | none | affine: 30, 0.72 | 1525 (55 / 1470 / 0) | 239 (16 %) | 1.42 | ok |
| image 1516796 | 8227 | 1516796 | 4 (affine, 9.3) | 0.245 | none | affine: 28, 0.63 | 2601 (506 / 2095 / 0) | 229 (9 %) | 1.37 | ok |
| 37 | 8231 | 1516800 | 28 (affine, 1.2) | 0.245 | none | affine: 23, 0.69 | 947 (113 / 834 / 0) | 87 (9 %) | 1.75 | ok |
| 34 | 8228 | 1516797 | 24 (affine, 1.6) | 0.243 | none | affine: 25, 0.75 | 2282 (294 / 1988 / 0) | 193 (8 %) | 1.77 | ok |
| 38 | 8186 | 1516755 | 17 (affine, 1.5) | 0.245 | none | none | 286 (115 / 171 / 0) | 9 (3 %) | 1.86 | ok |
| image 1516771 | 8202 | 1516771 | 4 (affine, 8.5) | 0.244 | none | affine: 10, 0.19 | 1131 (269 / 862 / 0) | 113 (10 %) | 1.19 | ok |
| 40 | 8188 | 1516757 | 23 (affine, 1.2) | 0.243 | none | affine: 41, 0.48 | 2223 (145 / 2078 / 0) | 480 (22 %) | 1.3 | ok |
| image 1516756 | 8187 | 1516756 | 19 (affine, 1.4) | 0.243 | none | shift: 7, 1.66 | 674 (258 / 416 / 0) | 27 (4 %) | 1.43 | ok |
| 42 | 8201 | 1516770 | 23 (poly2, 1.3) | 0.243 | none | affine: 18, 0.36 | 663 (124 / 538 / 1) | 118 (18 %) | 1.31 | ok |
| image 1516773 | 8204 | 1516773 | 70 (tps, 1.1) | 0.324 | none | affine: 21, 0.6 | 901 (298 / 602 / 1) | 109 (12 %) | 1.48 | ok |
| image 1516774 | 8205 | 1516774 | 25 (tps, 1.9) | 0.49 | none | none | 486 (280 / 202 / 4) | 14 (3 %) | 1.61 | ok |
| **all** | | | | | | | **18386** (3057 / 15323 / 6) | 2106 (11 %) | | 14 plates, 20.07 km2 |
<!-- /TABLE harlem_1897 -->

**Registration.** No street tint on this atlas; the plates were fitted on the standing buildings. The first
fits were 1-3.5 m out; the correction's window residual is 0.2-1.7 m, and outlines that coincide with a
footprint sit 1.2-2.1 m (median centre distance, which includes the difference in shape) from it, without a
common direction. Plate 38 (Morningside Heights, mostly empty in 1897) and the Washington Heights plate had
too few standing buildings for the match and keep the control-point fit (cross-validated 1-2 m).

**Why so few coincide.** 11 % of the outlines reach IoU 0.5 with a footprint of today, 37 % lie on pre-war
footprints for four fifths of their area or more, 52 % for less than a fifth. The last group is the answer to
"what stood before": East Harlem under the housing projects, the frame houses of the 1890s edge. The middle
group is partly row houses replaced before the war by apartment houses on several lots, partly standing houses
the tracing cut or joined differently from today's footprints (see *How to use*). The registration is not the
cause: rows that survive lie on their footprints to within about a metre in the windows looked at.

**Looked at.**
* W 130th-131st St between Lenox and Seventh Av (plate 40, 130 m): about 50 buildings drawn, 47 traced as one
  outline each; one crossed frame building in two pieces; two or three houses with the stone front missing or
  a bite at a lot number.
* Pleasant Av / E 120th St (plate "image 1516796", 140 m): about 80 drawn, 74 outlines; three or four
  buildings missed (a rose building without a clear outline, one frame building), stone fronts missing on one
  row (those houses are 2 m short), two houses cut by a blue-crayon line.
Both before the lettering filter; 12 of the 14 plates were not looked at.

**Known failures.** Two houses as one outline where the party wall is faint; a house in pieces under large lot
numbers or pencil lines; stone-front strips not joined; stone buildings mostly missing; grey hatched grounds
are not read (only fills).

### bronx_23rd_ward_1887

Robinson & Pidgeon's atlas of the 23rd Ward (1887), plates 1-5, 7-15, 17-19 and 21; 0.17-0.18 m per pixel (the scale
statement was not read). Pale yellow = frame, rose = brick, grey = stone; the sheets are greyish and the lines
faint.

<!-- TABLE bronx_23rd_ward_1887 -->
| sheet | Map Warper id | NYPL image | control points (fit, CV rms m) | m / px | street match: windows agreeing, shift found m, left m | building match: windows, residual m | buildings (frame / brick / stone) | on a standing footprint (IoU > 0.5) | their median offset m | status |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 8625 | 1523107 | 4 (affine, 5.4) | 0.174 | affine: 12, 4.9, 2.1 | shift: 3, 0.45 | 240 (119 / 120 / 1) | 3 (1 %) | 2.17 | ok |
| 2 | 8626 | 1523108 | 4 (affine, 5.9) | 0.175 | affine: 29, 6.4, 2.6 | shift: 7, 0.53 | 880 (527 / 353 / 0) | 72 (8 %) | 1.44 | ok |
| 3 | 8627 | 1523109 | 8 (affine, 12.9) | 0.173 | affine: 24, 3.2, 3.9 | none | 285 (238 / 47 / 0) | 5 (2 %) | 2.7 | ok |
| 4 | 8628 | 1523110 | 4 (affine, 2.3) | 0.174 | affine: 16, 5.7, 0.8 | none | 213 (156 / 56 / 1) | 1 (0 %) | 2.0 | ok |
| 5 | 8629 | 1523111 | 8 (affine, 10.3) | 0.179 | affine: 27, 16.2, 2.2 | none | 828 (726 / 102 / 0) | 21 (2 %) | 1.39 | ok |
| 7 | 8631 | 1523113 | 3 (affine, 0.0) | 0.174 | affine: 26, 7.6, 2.1 | none | 289 (264 / 25 / 0) | 5 (2 %) | 0.95 | ok |
| 8 | 8632 | 1523114 | 5 (affine, 7.9) | 0.173 | affine: 26, 6.6, 1.7 | none | 504 (466 / 38 / 0) | 8 (2 %) | 1.32 | ok |
| 9 | 8633 | 1523115 | 5 (affine, 16.1) | 0.174 | affine: 35, 13.3, 1.7 | none | 633 (568 / 64 / 1) | 18 (3 %) | 1.49 | ok |
| 10 | 8634 | 1523116 | 4 (affine, 5.9) | 0.174 | affine: 30, 4.9, 1.5 | none | 610 (563 / 47 / 0) | 11 (2 %) | 1.59 | ok |
| 11 | 8635 | 1523117 | 3 (affine, 0.0) | 0.174 | shift: 5, 16.9, 2.6 | none | 46 (40 / 6 / 0) | 0 (0 %) |  | ok |
| 12 | 8636 | 1523118 | 4 (affine, 22.8) | 0.22 | affine: 19, 6.0, 3.0 | none | 89 (72 / 15 / 2) | 0 (0 %) |  | ok |
| 13 | 8637 | 1523119 | 7 (affine, 6.9) | 0.217 | affine: 27, 3.0, 1.7 | none | 245 (242 / 1 / 2) | 3 (1 %) | 2.71 | ok |
| 14 | 8638 | 1523120 | 9 (affine, 7.1) | 0.218 | affine: 14, 4.0, 2.8 | none | 101 (94 / 5 / 2) | 1 (1 %) | 1.49 | ok |
| 15 | 8639 | 1523121 | 5 (affine, 10.6) | 0.22 | affine: 17, 9.9, 2.7 | none | 72 (70 / 1 / 1) | 0 (0 %) | 1.88 | ok |
| 16 | 8640 |  |  (, ) |  | none | none | 0 (0 / 0 / 0) | 0 (0 %) |  | left out: control points inconsistent (cross-validated 27 m) and no street match to check or correct the fit |
| 17 | 8641 | 1523123 | 4 (affine, 82.6) | 0.217 | affine: 17, 9.6, 2.3 | none | 158 (134 / 20 / 4) | 3 (2 %) | 1.83 | ok |
| 18 | 8642 | 1523124 | 4 (affine, 4.3) | 0.215 | affine: 14, 11.6, 7.2 | none | 90 (69 / 21 / 0) | 0 (0 %) |  | ok |
| 19 | 8643 | 1523125 | 9 (affine, 25.8) | 0.287 | shift: 5, 5.0, 3.9 | none | 133 (118 / 2 / 13) | 0 (0 %) |  | ok |
| 20 | 8644 |  |  (, ) |  | none | none | 0 (0 / 0 / 0) | 0 (0 %) |  | left out: control points inconsistent (cross-validated 173 m) and no street match to check or correct the fit |
| 21 | 8645 | 1523127 | 5 (affine, 7.4) | 0.29 | none | none | 40 (32 / 1 / 7) | 0 (0 %) |  | ok |
| **all** | | | | | | | **5456** (4498 / 924 / 34) | 151 (3 %) | | 18 plates, 15.76 km2 |
<!-- /TABLE bronx_23rd_ward_1887 -->

**Registration.** The weakest of the three. The control-point fits (3-9 points) were 3-17 m out (median 6 m).
The street match (the atlas tints its streets lilac; looser settings than for Kings County) corrects 17
plates, leaving 0.8-3.9 m by its own measure and 7.2 m on plate 18 (on plate 19 it rests on 5 windows only);
where standing buildings exist the building match was applied on top (plates 1 and 2). Three plates got no
street match — too few streets of today match on Hunts Point and east of it. **Plates 16 and 20 are left
out**: their control points disagree among themselves (27 m and 173 m cross-validated) and nothing checks
them. **Plate 21 keeps its control-point fit (cross-validated 7 m), unchecked.** Almost nothing of
1887 stands in Mott Haven and Morrisania; on the 7 plates with five or more standing buildings these sit
1.0-2.7 m from their footprints.

**Looked at.**
* E 141st-143rd St at the railway (plate 2, 200 m), with the first settings: about 115 buildings drawn, 99
  outlines; the missed ones had outlines too faint for the 55 % rule, which was then lowered to 35 %.
* Plate 5 (Melrose, 150 m), final layer: about 50 drawn, 44 traced (88 %), no false outline after the
  washed-lot filter (before it, a washed lot of 3,400 m2 and five ragged pieces of it were in the window);
  missed: four pale-yellow buildings and a crossed shed; about eight outlines ragged where figures are written
  on the building.

**Known failures.** Pale buildings missed; faint outlines (two houses in one outline); crossed sheds partly
filled; ragged outlines under figures; a washed lot that scores as yellow as a building would pass (none seen).
Rose-washed lots, if the atlas has any, are not filtered — not looked for.

## Checks

* `export` checks every polygon: valid, 15-5,000 m2, centre inside the coverage (counts in `<layer>_stats.json`
  under `total`: `invalid`, `area_out_of_range`, `outside_coverage` — all 0). The files were read back
  independently with shapely for the same checks.
* Registration: per plate in the tables (street match before / after, building match residual, median offset
  of the outlines that coincide with a standing footprint). A plate whose standing buildings sit more than 8 m
  from their footprints is left out by `export`; none was. Two plates were left out because no trustworthy
  fit was found (Kings County 25, 31) and two because their control points are inconsistent and nothing
  checks them (Bronx 16, 20).
* The export checks and writes the same thing: validity and area are tested on the coordinates as written
  (6 decimals), in degrees and in metres; two outlines of one plate on one spot are reduced to the larger.
* By eye: the overlays named under each layer (`tools/atlas.py overlay … [--final]`: plate crop with the
  traced or exported outlines and today's footprints) — ten windows: six on four plates of Kings County, two
  on two plates of Manhattan, two on two plates of the Bronx.

Not checked: the layers in the pipeline or the viewer; the other 53 of the 61 plates by eye; the storeys; the survey
dates on the collars of the 1887 and 1897 atlases; whether the brick outlines of the Bronx include rose-washed
lots.

## Not done, and what would extend this

| area | atlas in the Map Warper dump | note |
|---|---|---|
| Flatlands village; Canarsie east | Kings County plates 25 and 31 | hand control points (four street corners each) and a re-run would add them |
| Brooklyn's row-house belt (Bedford, Bushwick, Park Slope) | Bromley 1880 (28 plates, 4 control points each), Robinson 1886 (38 plates, 12-13 points), Hyde 1898 (73 plates) | at 300 ft to the inch the party walls are one pixel: rows would come out as one outline each. The large-scale volumes ("Atlas 61-97", 1886-1908, 20-100 plates each) would give houses, with the city style |
| Gravesend / Flatlands again in 1899 | Hyde, *Atlas of the Brooklyn Borough* vol. 3 (33 plates) | a second date for the towns |
| Queens (Jamaica, Flushing, Newtown, Long Island City) | Wolverton 1891 (18 plates at county scale), Hyde 1901-07 ward atlases (9-48 plates) | not opened |
| the Bronx north of 170th St | Robinson 1885 (Ward 24 plates at small scale), Bromley 1893 / 1897 / 1900 volumes | not opened |
| Manhattan above 86th St in the 1880s | Robinson 1885 (plates 22-33, 5-26 points), Bromley 1879 / 1891 | an earlier state of Harlem; Robinson's style is the county style |
| Staten Island | Beers 1874 (small scale), Robinson 1898 / 1907 | not opened |
| plates 6, 16, 20 of the 23rd Ward atlas | 6 is not in the dump; 16 and 20 need hand control points | holes in the Bronx coverage (around E 149th St / Third Av; Longwood; Hunts Point) |
| storeys on the Bromley plates | printed in each house | would need a digit reader (the Bay tool has one for Sanborn marks) |

## Tools

`python -I data/manual/atlas/tools/atlas.py <command>` from the repository root with the project's venv
(packages used: numpy, scipy, shapely, rasterio, Pillow, duckdb; no OpenCV).

| | |
|---|---|
| `layers.json` | the layers: atlas, map year, style, plates (Map Warper id, sheet, `skip` with the reason), per-layer settings |
| `atlas.py fetch <layer>` | master scans -> `data/raw/atlas/nypl_u/` |
| `atlas.py refine <layer> [plate] [--q 0.25 --win 300]` | street match -> `data/interim/atlas/<layer>/<plate>_corr.json`. `--locate [--hint dx,dy]` first searches +- 8 km for a plate the Map Warper misplaced (tried on Kings County plate 25: ambiguous, not used) |
| `atlas.py trace <layer> [plate]` | tracing -> `data/interim/atlas/<layer>/<plate>.pkl` (pixel outlines, ground outlines, match against today) |
| `atlas.py refine_buildings <layer> [plate]` | building match, then the ground outlines again (`regeo` does only the latter) |
| `atlas.py score_frames <layer>` | yellow strength of the frame outlines (Bronx; run after the last `regeo`) |
| `atlas.py export <layer>` | the three files of a layer |
| `atlas.py readme` | the tables of this file |
| `atlas.py overlay <layer> <plate> <x,y> <size_m> <out.png> [--px] [--final]` | picture for checking by eye |
| `run_layer.sh`, `run_city.sh`, `run_reg.sh` | the runs in parallel workers (county plates; city plates; registration only). Do not edit them while they run: the shell reads them as it goes |

To rebuild a layer: `fetch`, then `run_layer.sh kings_towns_1890 4` or `run_city.sh harlem_1897 2` or
`run_city.sh bronx_23rd_ward_1887 2 street` followed by `run_reg.sh bronx_23rd_ward_1887 2` and
`score_frames`, then `export` and `readme`. Kings County plate 17 was registered with
`refine kings_towns_1890 8542 --q 0.25 --win 300` and `regeo`.

`pipeline/sanborn_trace.py` (the Bay project's Sanborn tool, written round one district's street frame) is kept
as it was copied, with a note at its head: nothing of it runs here; the atlas tracing is `tools/atlas.py`.

A trace takes about a minute of processor time per plate and under 1 GB (the plate is read in tiles, and only
around fills).
