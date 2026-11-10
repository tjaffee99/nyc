# Building footprints traced from real-estate atlases

What stood where the fire-insurance tracings (Manhattan below 86th St, downtown Brooklyn) say nothing: the
buildings drawn on the coloured real-estate atlases of the 1880s-90s, read plate by plate from the New York
Public Library's scans. Every outline is a fill the atlas itself colours as a building; nothing is generated.
What the atlas does not give (years of construction and demolition, heights) is not in these files.

| layer | atlas | area | buildings |
|---|---|---|---|
| `kings_towns_1890.geojson` | *Robinson's atlas of Kings County, New York* (E. Robinson, 1890), 29 of its 31 plates | the county towns before they joined Brooklyn: Flatbush, New Utrecht (Bay Ridge, Fort Hamilton, Bath Beach, Bensonhurst), Gravesend (the village, Coney Island, Sheepshead Bay), Flatlands (Canarsie in part) | 6,914 (6,795 frame, 119 brick) |
| `harlem_1897.geojson` | *Atlas of the city of New York, Manhattan Island* (G. W. & W. S. Bromley, 1897), the 15 plates north of 84th / 86th St (one of them, plate 35, georeferenced here) | Yorkville north of 84th St, East Harlem, the Upper West Side from 86th St, Morningside Heights, Harlem, Manhattanville, Hamilton Heights, Washington Heights to about 190th St | 19,925 (3,114 frame, 16,805 brick, 6 stone) |
| `manhattan_midtown_1897.geojson` | the same atlas, 11 plates (one of them, plate 19, georeferenced here) | Manhattan from 40th St to 84th / 86th St, river to river: Hell's Kitchen, Lincoln Square, the Upper West Side to 86th St, Midtown, Turtle Bay, the Upper East Side, Yorkville to 84th St | 19,302 (1,690 frame, 17,579 brick, 7 stone, 26 gasholders) |
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
| `kind` | `building`, or `gasholder` (a round iron tank, `material` empty; `manhattan_midtown_1897` only). Present in the two layers exported since it was added (`manhattan_midtown_1897`, `harlem_1897`); the Kings County and Bronx files do not have it |

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
* Two plates of the 1897 Manhattan atlas are not in the dump (19 and 35): their control points were made here
  from the scans (`tools/gcps_own.json`, CC0); see `manhattan_midtown_1897`.
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

**Plate 35** (W 108th / 110th St to W 125th St, Lenox Av to Columbus Av and Morningside Park: central Harlem) is not in the Map Warper dump and was missing from the first version of this layer - a hole of about 1 km2 that the per-plate checks did not show. It was added later (1,539 outlines), georeferenced here like plate 19 of the Midtown layer: scan NYPL image 1516798; 36 control points at the crossings of W 112th-124th St with Manhattan, Eighth and Seventh Av (`tools/gcps_own.json`, map id 900035), cross-validated 2.4 m; then the building match (32 windows, 0.7 m). 19 % of its outlines coincide with a standing footprint, at 1.7 m. The two blocks south of 110th St lie outside its control points: the two standing buildings there sit 3 m off. One window looked at (W 119th-120th St at St Nicholas Av): rows traced house by house and on their footprints; a large frame greenhouse is one outline; a small frame building and a crossed stable missed or in pieces. The 18,386 outlines of the first version are unchanged. **Plate 45 (Inwood, north of about 190th St) is also not in the dump and is not in the layer**: its streets are not a grid, so it needs hand control points (image 1516775).

Bromley's *Atlas of the city of New York, Manhattan Island* (1897): plates 31, 32, 34, 35, 36, 37, 38, 40, 42 and
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
| 35 | 900035 | 1516798 | 36 (tps, 2.4) | 0.241 | none | affine: 32, 0.7 | 1539 (57 / 1482 / 0) | 289 (19 %) | 1.67 | ok |
| **all** | | | | | | | **19925** (3114 / 16805 / 6) | 2395 (12 %) | | 15 plates, 21.13 km2 |
<!-- /TABLE harlem_1897 -->

**Registration.** No street tint on this atlas; the plates were fitted on the standing buildings. The first
fits were 1-3.5 m out; the correction's window residual is 0.2-1.7 m, and outlines that coincide with a
footprint sit 1.2-2.1 m (median centre distance, which includes the difference in shape) from it, without a
common direction. Plate 38 (Morningside Heights, mostly empty in 1897) and the Washington Heights plate had
too few standing buildings for the match and keep the control-point fit (cross-validated 1-2 m).

**Why so few coincide.** 12 % of the outlines reach IoU 0.5 with a footprint of today, 38 % lie on pre-war
footprints for four fifths of their area or more, 50 % for less than a fifth. The last group is the answer to
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

### manhattan_midtown_1897

The same Bromley atlas of 1897 as `harlem_1897`, for the band from 40th St to the Harlem layer's edge at
84th / 86th St, river to river: plates 19, 21, 25, 26, 27, 28, 29 and four plates the Map Warper titles only call
"Part of Section ..." (image ids in the table); 0.25 m per pixel. 19,302 outlines (1,690 frame, 17,579 brick, 7
stone, 26 gasholders), 11.2 km2. The layer is cut at the line of 40th St (today's centreline) and at the
coverage of `harlem_1897`, so no building is in both layers (1,611 outlines traced south of 40th St or inside
the Harlem coverage are left out).

<!-- TABLE manhattan_midtown_1897 -->
| sheet | Map Warper id | NYPL image | control points (fit, CV rms m) | m / px | street match: windows agreeing, shift found m, left m | building match: windows, residual m | buildings (frame / brick / stone) | on a standing footprint (IoU > 0.5) | their median offset m | status |
|---|---|---|---|---|---|---|---|---|---|---|
| image 1516786 | 8217 | 1516786 | 20 (tps, 1.4) | 0.249 | none | affine: 25, 0.83 | 2028 (471 / 1554 / 0) | 154 (8 %) | 1.67 | ok |
| 19 | 900019 | 1516787 | 30 (poly2, 2.6) | 0.246 | none | affine: 21, 0.8 | 1642 (225 / 1407 / 0) | 117 (7 %) | 1.84 | ok |
| 25 | 8209 | 1516778 | 30 (poly2, 1.2) | 0.247 | none | affine: 32, 0.79 | 1654 (107 / 1543 / 0) | 160 (10 %) | 1.5 | ok |
| 21 | 8212 | 1516781 | 49 (poly2, 1.2) | 0.252 | none | affine: 22, 1.35 | 2631 (170 / 2455 / 0) | 117 (4 %) | 1.8 | ok |
| 27 | 8211 | 1516780 | 38 (poly2, 1.1) | 0.251 | none | affine: 22, 0.6 | 1293 (169 / 1121 / 0) | 107 (8 %) | 1.82 | ok |
| 29 | 8214 | 1516783 | 38 (poly2, 1.3) | 0.25 | none | affine: 38, 0.88 | 1317 (210 / 1107 / 0) | 161 (12 %) | 1.77 | ok |
| 28 | 8213 | 1516782 | 90 (tps, 1.2) | 0.249 | none | affine: 62, 0.85 | 1702 (49 / 1653 / 0) | 154 (9 %) | 2.11 | ok |
| image 1516788 | 8219 | 1516788 | 38 (poly2, 1.3) | 0.246 | none | affine: 47, 2.14 | 1225 (57 / 1168 / 0) | 22 (2 %) | 4.41 | ok |
| image 1516784 | 8215 | 1516784 | 34 (tps, 1.3) | 0.248 | none | affine: 30, 1.19 | 2151 (28 / 2117 / 6) | 73 (3 %) | 2.74 | ok |
| image 1516785 | 8216 | 1516785 | 18 (tps, 1.5) | 0.248 | none | affine: 19, 0.74 | 2233 (131 / 2101 / 1) | 44 (2 %) | 2.88 | ok |
| 26 | 8210 | 1516779 | 37 (tps, 1.1) | 0.251 | none | affine: 48, 0.94 | 1426 (73 / 1353 / 0) | 203 (14 %) | 1.75 | ok |
| **all** | | | | | | | **19302** (1690 / 17579 / 7) | 1312 (7 %) | | 11 plates, 11.2 km2 |
<!-- /TABLE manhattan_midtown_1897 -->

**Plate 19** (W 36th-47th St, Eighth Av to the Hudson: Hell's Kitchen's 40s, the gas works) **is not in the Map
Warper dump**; without it the band has a hole there. Its scan is NYPL image 1516787 (found by its place in the
atlas's run of image ids). Control points were made here (`tools/gcps_own.json`, map id 900019): on the scan
the streets and avenues are the bands without building fill; their middle lines, fitted per street and per
avenue, cross at 30 points (W 37th-46th St with Ninth, Tenth and Eleventh Av), set against today's centreline
crossings. Cross-validated 2.6 m (2nd-order fit), then the building match as on the other plates. The plate's
"mask" is the block of ground its title names, from today's centrelines.

**Registration.** Every plate was fitted on its standing buildings (three passes); the window residual of the
last pass is 0.6-2.14 m. Outlines that coincide with a footprint of today sit 1.5-4.41 m (median
centre distance) from it. The weakest plate is "image 1516788" (Eighth Av to Park Av, 40th-47th St: Times Square
and Grand Central, where almost nothing of 1897 stands): 22 coinciding outlines, 4.4 m - much of that is the
difference between a traced part and today's whole building, but the plate has the least to hold it.

**How much coincides.** 7 % of the outlines reach IoU 0.5 with a footprint of today (2-14 % by
plate), 40 % lie on pre-war footprints for four fifths of their area or more, 48 % for less than a fifth.

**Settings that differ from `harlem_1897`** (`layers.json`): outlines up to 20,000 m2 (armouries, car depots,
Grand Central Depot, breweries, slaughterhouses: 91 outlines over 2,000 m2, 10 over 5,000 m2); a large,
wide fill needs only 30 % of its outline (St Patrick's Cathedral came out with 48 % under its bold lettering and
was missing); the grey of stone is read a little lighter; pale blue round outlines of 250 m2 or more are
**gasholders** (`kind = gasholder`, `material` empty; round = fills 85 % of its convex hull, the hull as compact
as a circle to 88 %) - every other pale blue outline is water between piers or a blue-tinted yard and is dropped
(254; pale blue counts as fill only where it is 25 pixels wide, so that the blue-crayon strokes on the NYPL
copy do not hang tails on the houses they cross); a stone outline must be 200 m2, 6 m wide and less than four times as long as wide (the grey
strip of a row's stone fronts otherwise comes out as a building; 303 grey pieces dropped, mostly lettering).

**Looked at** (plate crops with the outlines drawn on them, 150 m windows unless said):
* Hell's Kitchen, W 52nd-53rd St between Tenth and Eleventh Av: about 60 buildings drawn, about 55 covered by
  an outline, no false outline; two or three outlines hold two houses, one crossed stable is in X-shaped pieces.
* Hell's Kitchen, W 55th-56th St between Ninth and Tenth Av: about 62 drawn, about 56 covered, no false
  outline; missed: three crossed frame sheds, a frame building, half of a frame church under its lettering;
  one outline holds three houses; the grey front strips of two rows are not joined (those houses are 2 m short).
* Hell's Kitchen, W 44th-45th St between Ninth and Tenth Av (plate 19): about 110 drawn, about 100 covered,
  no false outline; five crossed stables in X-shaped pieces, three small frame rear buildings missed. Standing
  tenements lie on their footprints.
* Lincoln Square, W 62nd-63rd St between Amsterdam and West End Av: about 62 drawn, all covered, no false
  outline; two outlines hold two to four houses.
* Queensboro Bridge approach, E 59th-60th St between First and Second Av: about 85 drawn, about 78 covered, no
  false outline; about eight outlines hold two to four houses, about ten are ragged where figures stand on the
  house; a crossed frame shed and two or three houses at the sheet fold missed.
* Yorkville, E 77th-78th St between First and Second Av: about 75 drawn, about 70 covered, no false outline;
  the grey front strips of one block face are not joined; three or four outlines hold two or three houses.
* St Patrick's Cathedral (E 50th-51st St): missing in the first run, in the layer after the change above, with
  its two residences; the outline is short of the real plan where the lettering crosses it.
* The stock yards and slaughterhouses at W 58th-61st St, West End Av (300 m): Eastman's Dressed Beef Co. and
  the two large brick buildings of the next block are single outlines; the empty block of the Union Stock Yards
  has nothing; no tracks or lot lines came out as buildings.
* Every gasholder and stone outline of the layer as written (26 and 7) and the 32 largest other outlines
  of an earlier run, one by one: the gasholders are gasholders (one cut short by the sheet fold; two earlier
  versions of the rule let five pieces of water and a blue-tinted car yard through, or lost four real holders); the stone outlines are St Patrick's and its two houses, three
  churches and one institution; of the 32 large outlines 31 are single buildings or works (armouries, depots,
  breweries, slaughterhouses, the Foundling Asylum, the Normal College, a grain elevator) and one is a row of
  about fifteen houses on E 41st St run together.
The windows were looked at on earlier runs of the layer; after the last re-trace (which changed the handling
of large, grey and blue fills only) the Queensboro window was looked at again on the layer as written, the first
Hell's Kitchen window on the run before it; both are as described.

**Churches.** Most churches on these plates are drawn rose (brick) or yellow (frame) and are traced as such,
often ragged under their lettering. Grey (stone) buildings are few: seven are in the layer. Sixteen grey outlines
of 200 m2 or more were traced before the cut at 40th St and the filters; the nine not exported were not looked
at one by one (some lie outside the band, some are front strips).

**Known failures.** As for Harlem: two to four houses as one outline where party walls are faint (about one
outline in ten; at worst a whole block face); houses in pieces or ragged under figures; stone-front strips not
joined; crossed stables and sheds in X-shaped pieces or missing; small frame rear buildings missed. Blackwell's
(Roosevelt) Island is not on these plates.


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
  traced or exported outlines and today's footprints) — ten windows on the first three layers (six on four plates of Kings County, two on two plates of
  Harlem, two on two plates of the Bronx), one more on Harlem's plate 35, and eight windows on five plates of
  the Midtown layer with every gasholder, stone outline and the 32 largest outlines one by one.

Not checked: the layers in the pipeline or the viewer; the other 59 of the 73 plates by eye; the storeys; the survey
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
| Manhattan south of 40th St, 1897 | the same atlas, plates 1-18 (Map Warper ids 8189-8222, 3-49 control points) | traced layers of 1854 / 1857 / 1894 exist there; plate "image 1516792" (W 26th-40th St, Eighth Av to the river, with the 30th St yard) was traced for this run and left out by the cut at 40th St |
| Inwood | plate 45 of the 1897 Manhattan atlas (NYPL image 1516775), not in the dump | irregular streets: hand control points needed |
| storeys on the Bromley plates | printed in each house | would need a digit reader (the Bay tool has one for Sanborn marks) |

## Tools

`python -I data/manual/atlas/tools/atlas.py <command>` from the repository root with the project's venv
(packages used: numpy, scipy, shapely, rasterio, Pillow, duckdb; no OpenCV).

| | |
|---|---|
| `layers.json` | the layers: atlas, map year, style, plates (Map Warper id, sheet, `skip` with the reason), per-layer settings |
| `gcps_own.json` | control points made here for plates that are not in the Map Warper dump (plate 19 of the 1897 Manhattan atlas), in the dump's record format |
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

## Queens and Staten Island (`tools_queens_si/`, added 2026-11)

Five layers from NYPL's Hyde (Queens, 1901 / 1907) and Bromley (Staten Island, 1917) plates, traced with a copy of the
tool (`tools_queens_si/`, work in `data/interim/atlas_queens_si/`, scans shared in `data/raw/atlas/nypl_u/`). All are NOT complete
inside their coverage (about 65-90 % of the drawn houses found, see below); absence is not evidence of an empty lot.
`map_year` is the publication year of the volume as catalogued by NYPL (Hyde vol. 2 / 3 / 1 1901; vol. 1 1907; Bromley Richmond 1917);
the survey dates on the collars were not read. Not added to `COMPLETE`.

| layer | atlas (plate scale ~160 ft to the inch, 0.15-0.30 m per pixel) | area | buildings |
|---|---|---|---|
| `queens_lic_1901` | Atlas of the borough of Queens, vol. 2, First and second wards (1901): 21 of 30 plates | Hunters Point, Ravenswood, Dutch Kills, Astoria, Steinway, Woodside, Winfield, Elmhurst, Corona, Maspeth, Laurel Hill, East Williamsburgh (Newtown) | 10,933 (9,705 frame, 1,228 brick) |
| `queens_jamaica_1901` | same atlas, vol. 1, Fourth and fifth wards (1901): 7 of 9 plates | Jamaica centre and its neighbourhoods; 1 plate of Far Rockaway | 3,779 (3,473 frame, 306 brick) |
| `queens_flushing_1901` | same atlas, vol. 3, Third ward (1901): 14 of 21 plates | Flushing ward outside the village centre (the centre is on overview plates 19 and 20 at 1.1 m per pixel: not traced) | 3,490 (3,400 frame, 90 brick) |
| `queens_rockaway_1907` | same atlas, vol. 1 (1907): 5 of 7 plates (32, 34, 35, 38, 39; plate 40 has 2 outlines, 37 is unplaced) | Far Rockaway / Rockaway | 2,026 (2,004 frame, 22 brick) |
| `staten_island_north_1917` | Atlas of the city of New York, borough of Richmond (G. W. Bromley, 1917): 19 of 84 plates | St George and Stapleton (plates 15450-15454), Port Richmond, West and Mariners Harbor (Ward 3 plates 15367-15373, 15399-15404, 15433, 15442-15445) | 8,844 (8,294 frame, 548 brick, 2 stone) |

Sources: NYPL Map Division scans (public domain) `https://images.nypl.org/index.php?id=<imageId>&t=u`; control points and masks: NYC Space/Time
Directory Map Warper dump (CC0). Plate ids in the layers' `plate` property are Map Warper ids; `sheet` is the plate number, or `image <id>`
where the Map Warper title has none (all Staten Island plates). `storeys` not read (the plates print them). `source` ids: `queens_wards12_1901`,
`queens_wards45_1901`, `queens_ward3_1901`, `queens_wards45_1907`, `bromley_richmond_1917`.

### What was changed in the copy of the tool

* `style_override` for these atlases: frame fill `db_min` 5 (the scans are dark and the wash is weak: the Bronx setting), outline share 0.40; Hyde plates
  also without the `stone` class (the grey of tracks, rail and street lettering read as stone). Thresholds are in pixels: plates at 0.15 m per pixel were not tuned separately.
* `refine_buildings` takes `--search` (12 m control-point errors need 14 m, then 6 m) and `--q`; scripts `run_chain.sh` (Staten Island: trace, coarse
  and fine building match), `run_hyde.sh` (Queens: street match, trace, fine building match), `run_rev.sh`.
* Hyde's plates tint the streets, so the street match of `refine` works (found 5-17 m of shift on the Queens plates, 1-2 m left); Bromley's Richmond plates
  do not, so only the building match (survivors) can register them: it found 14-19 windows, shifts of up to 5 m, residual 0.5-1.4 m.
* `export` drops slivers: an outline under 3 m wide and 4 times as long, under 4.5 m wide and over 14 m long, or over 30 m long and 6 times as long as wide
  (street tint, property bands and rail read as buildings along roads; the count per layer was not recorded: 385 outlines on the first Long Island City pass). `final_checks.py` (after `export`) removes outlines
  whose centre lies outside the coverage and overlaps (over 30 % of the smaller), and writes the checks into `total.final_checks` of the stats file.
* `apply_skips.py`: Staten Island plates are kept only if the building match corrected them or at least 5 outlines sit on standing footprints within 3 m.
  `skip` reasons for Queens plates were written by hand (control points off by 13-2,200 m and no street match).

### Checks

* Numeric, all five layers (`final_checks.py`): all polygons valid, 15-5,000 m2, ids unique, centres inside coverage (1 stray centre in Jamaica and 0 elsewhere removed),
  no pair overlapping by more than 30 % of the smaller outline; 8-51 pairs per layer touch or overlap slightly (a few tenths of a m2: shared walls drawn twice).
* Registration: per plate in the tables below. Outlines that coincide with a standing footprint (IoU > 0.5; the share is low because the places were replaced,
  and because ragged outlines rarely reach IoU 0.5) sit a median 0.5-2.8 m from it on every plate used (the largest single plate: 2.8 m). No kept plate has survivors more than 3 m off.
* By eye (windows of 260-420 m with the exported outlines over the plate, `atlas.py overlay ... --final`): 
  * Hunters Point, `queens_lic_1901` plate 15730 (rows of frame and brick houses, factories): about 70 % of the drawn buildings found; some merged into one outline, a few
    outlines in pieces, a band of false outlines along the railway edge before the sliver filter was added (not seen again after it).
  * Astoria / Woolsey St, plate 15737: about 75 %; false slivers along tinted streets (reduced by the sliver filter); the brick of Public School found.
  * Corona, plate 15712: about 85 % of frame houses, outlines good, standing buildings coincide; a few outbuildings missed.
  * Dutch Kills fields, plate 15705, and Newtown meadows, plate 15717: nearly empty on the plate; nothing false seen, 2 houses missed.
  * Bradley Ave, plate 15733 (first, unfiltered test): ragged outlines, about 50 %, the grey railroad wash read as stone (this is why `stone` is off for Hyde).
  * Jamaica, plates 17261 and 17263: about 85 %, rows traced as single buildings; one long false brick strip on a property line before the final sliver rule.
  * Rockaway, plate 15620: houses found (about 80 %); false long outlines along Ave. and Lane edges before the final sliver rule (checked only before it).
  * Flushing ward, plate 15748: about 80 %; a few false strips on a dotted lot line.
  * Staten Island, Port Richmond, plate 15370: about 90 %, registration good, houses traced separately; small outbuildings missed.
  * Staten Island, plates 15451 (Stapleton / Tompkinsville), 15450 (St George, Tompkinsville Ave), 15454, 15373: about 85-90 %; the dark rose-grey brick houses are often missed; ragged false pieces
    here and there (plate 15454, the lots by First St); pale lot washes are traced as buildings now and then.
  The windows were looked at before the final sliver rule on Queens plates 15620, 17263 and 15748 (numeric checks were rerun, the pictures not). Never looked at by eye: Queens
  plates 15731, 15734-15736, 15704, 15706, 15708-15711, 15717 elsewhere, 15720-15721, 15741-15743, 15745-15750, 15753, 15756-15758, 15761, 17262, 17264, 17270-17271, 17282,
  15622, 15623, 15626, 15627; Staten Island plates other than the five named above. Plates 15735, 15731 and others of Hunters Point / Long Island City were not looked at.
* Known failures: row houses sometimes one outline or in pieces; brick of dark tone missed; false outlines on street tint and lot washes; the cross-validation of the control points is
  3-17 m on most plates (the registration is the street match or the survivors, not the control points); coincidence share is no measure of recall.

### Left untraced, and with what

* Staten Island (Bromley 1917, 84 plates): 19 used; 56 were traced but left out because nothing verifies their registration (control points 7-23 m off, no street tint to
  match, fewer than 5 outlines on standing footprints: Wards 4 and 5 - Tottenville, Prince's Bay, Great Kills, Eltingville, Rossville - and many of the Ward 1-3 plates
  between Stapleton and Port Richmond, mostly rural or marsh); 9 not traced (run stopped). A hand-made control point set or a street-line match would place the left-out plates
  (their traces are in `data/interim/atlas_queens_si/si_bromley_1917/`, `skip` reasons in `tools_queens_si/layers.json`).
  Other atlases for the island: Bromley 1907 / Hyde 1907 (`si_1907`: 34 plates at county scale, configured in `layers.json`, not run), Sanborn 1898 (76 plates "Atlas 160"), Beers 1874 (26 plates, small scale).
* Queens: Flushing village (overview plates only: Bromley 1909 plates at 300 ft per inch, 47 plates, configured as `queens_bromley_1909`, not run), College Point, Whitestone, Woodhaven, Richmond Hill, Ozone Park, Hollis
  (Hyde 1907 vol. 1 plates 13-31, `queens_hyde_1907_jamaica`: 41 plates fetched, not traced), Ravenswood / Astoria plates of vol. 2 1907 (`queens_hyde_1907_lic`: 48 plates, not fetched), Rockaway Beach and Arverne (plates 33, 36, 40 and the Rockaway peninsula
  of Hyde 1907; Wolverton 1891 plate 13 is Arverne), the unplaced Hyde 1901 plates 15732, 15707, 15714, 15716, 15719, 15722-15725 (Newtown, Maspeth, Glendale, Middle Village).
  Hunters Point and Astoria are covered by 1901 only (a 1907 state exists on plates 15669 ff.).

#### queens_lic_1901

10933 buildings (9705 frame, 1228 brick, 0 stone), coverage 30.69 km2, 21 plates used; on a standing footprint (IoU > 0.5): 477; dropped by the final checks: 0 centre outside coverage, 0 overlapping; overlapping pairs left 0, touching / slightly overlapping pairs 51.

| sheet | plate | outlines | registration | street match: windows / shift found / left (m) | building match residual (m) | coincide (n, share) | median offset of those (m) | cross-val. of control points (m) |
|---|---|---|---|---|---|---|---|---|
| 1 | 15730 | 1015 | street match + building match | 6 / 7.9 / 2.8 | 0.81 | 85 (0.084) | 1.29 | 2.6 |
| 2 | 15731 | 385 | street match | 22 / 10.0 / 1.3 | - | 6 (0.016) | 1.53 | 7.2 |
| 4 | 15733 | 335 | street match + building match | 15 / 10.6 / 1.0 | 2.16 | 11 (0.033) | 1.91 | 18.1 |
| 5 | 15734 | 136 | street match | 25 / 4.6 / 1.2 | - | 2 (0.015) | 1.51 | 33.4 |
| 6 | 15735 | 659 | street match + building match | 22 / 5.8 / 2.3 | 1.2 | 34 (0.052) | 1.42 | 13.3 |
| 7 | 15736 | 932 | street match | 23 / 12.0 / 1.3 | - | 14 (0.015) | 1.41 | 3.3 |
| 8 | 15737 | 1114 | street match | 19 / 11.7 / 1.3 | - | 40 (0.036) | 1.36 | 2.3 |
| 9 | 15704 | 833 | street match | 29 / 9.6 / 1.6 | - | 34 (0.041) | 1.66 | 0.0 |
| 10 | 15705 | 552 | street match + building match | 17 / 9.5 / 1.6 | 1.81 | 32 (0.058) | 1.55 | 4.8 |
| 11 | 15706 | 250 | street match | 22 / 5.6 / 1.1 | - | 17 (0.068) | 1.62 | 0.0 |
| 13 | 15708 | 241 | street match | 16 / 16.8 / 2.2 | - | 3 (0.012) | 1.06 | 13.1 |
| 14 | 15709 | 180 | street match | 20 / 6.1 / 1.2 | - | 5 (0.028) | 2.09 | 11.4 |
| 15 | 15710 | 473 | street match | 6 / 6.6 / 1.4 | - | 4 (0.008) | 1.21 | 21.4 |
| 16 | 15711 | 524 | street match | 22 / 9.5 / 0.8 | - | 42 (0.08) | 1.45 | 24.5 |
| 17 | 15712 | 834 | street match | 29 / 5.4 / 1.4 | - | 34 (0.041) | 1.53 | 2.6 |
| 20 | 15715 | 591 | street match + building match | 14 / 5.2 / 2.2 | 1.51 | 22 (0.037) | 1.61 | 6.5 |
| 22 | 15717 | 475 | street match | 14 / 7.4 / 1.5 | - | 26 (0.055) | 1.44 | 4.8 |
| 23 | 15718 | 761 | street match + building match | 32 / 16.8 / 2.4 | 1.78 | 40 (0.053) | 2.22 | 4.8 |
| 25 | 15720 | 293 | street match | 17 / 5.3 / 1.5 | - | 19 (0.065) | 1.74 | 2.7 |
| 26 | 15721 | 188 | control points only | - / - / - | - | 2 (0.011) | 1.17 | 2.4 |
| image 1693974 | 15713 | 162 | street match | 9 / 5.4 / 1.3 | - | 5 (0.031) | 1.52 | 19.3 |

Left out:

* plate 15732 (sheet 3): control points 38.7 m (cross-validation) and the street match found only 2 windows: unplaced
* plate 15707 (sheet 12): no street match (2 windows) and 19 outlines: unplaced
* plate 15714 (sheet 19): control points 55 m out, no street match: unplaced
* plate 15716 (sheet 21): no street match, 16 m control points: unplaced
* plate 15719 (sheet 24): no street match, control points 13 m out: unplaced
* plate 15722 (sheet 27): no street match, control points 16 m out: unplaced
* plate 15723 (sheet 28): control points 93 m out, no street match: unplaced
* plate 15724 (sheet 29): control points 52 m out, no street match: unplaced
* plate 15725 (sheet 30): no street match, control points 14.5 m out: unplaced

#### queens_jamaica_1901

3779 buildings (3473 frame, 306 brick, 0 stone), coverage 11.7 km2, 7 plates used; on a standing footprint (IoU > 0.5): 153; dropped by the final checks: 1 centre outside coverage, 0 overlapping; overlapping pairs left 0, touching / slightly overlapping pairs 11.

| sheet | plate | outlines | registration | street match: windows / shift found / left (m) | building match residual (m) | coincide (n, share) | median offset of those (m) | cross-val. of control points (m) |
|---|---|---|---|---|---|---|---|---|
| 2 | 17261 | 661 | street match + building match | 23 / 12.1 / 1.6 | 0.5 | 75 (0.113) | 1.46 | 38.4 |
| 3 | 17262 | 697 | street match + building match | 38 / 12.4 / 2.2 | 0.34 | 19 (0.027) | 1.43 | 27.2 |
| 4 | 17263 | 861 | street match | 33 / 8.4 / 2.0 | - | 41 (0.048) | 1.35 | 32.0 |
| 5 | 17264 | 477 | street match | 28 / 9.4 / 1.1 | - | 12 (0.025) | 1.23 | 26.5 |
| 11 | 17270 | 373 | street match | 25 / 3.3 / 1.2 | - | 1 (0.003) | 1.23 | 8.0 |
| 12 | 17271 | 286 | street match | 25 / 7.7 / 1.2 | - | 2 (0.007) | 2.13 | 5.5 |
| 23 | 17282 | 424 | street match | 20 / 5.3 / 1.7 | - | 3 (0.007) | 1.95 | 7.3 |

Left out:

* plate 17260 (sheet 1): control points 100 m out and no street match: unplaced
* plate 17279 (sheet 20): control points 25 m out, no street match, no outline on a standing building: unplaced

#### queens_flushing_1901

3490 buildings (3400 frame, 90 brick, 0 stone), coverage 18.63 km2, 14 plates used; on a standing footprint (IoU > 0.5): 50; dropped by the final checks: 0 centre outside coverage, 0 overlapping; overlapping pairs left 0, touching / slightly overlapping pairs 14.

| sheet | plate | outlines | registration | street match: windows / shift found / left (m) | building match residual (m) | coincide (n, share) | median offset of those (m) | cross-val. of control points (m) |
|---|---|---|---|---|---|---|---|---|
| 1 | 15741 | 54 | street match | 15 / 10.9 / 0.6 | - | 3 (0.056) | 1.62 | 12.0 |
| 2 | 15742 | 276 | street match | 23 / 8.1 / 0.8 | - | 4 (0.014) | 1.99 | 29.0 |
| 3 | 15743 | 336 | street match | 17 / 6.5 / 1.1 | - | 3 (0.009) | 0.58 | 0.0 |
| 5 | 15745 | 440 | street match + building match | 15 / 14.5 / 1.1 | 0.79 | 2 (0.005) | 2.61 | 26.4 |
| 6 | 15746 | 126 | street match | 16 / 2.9 / 2.1 | - | 0 (0.0) | None | 16.4 |
| 7 | 15747 | 380 | street match | 29 / 8.2 / 1.6 | - | 2 (0.005) | 1.53 | 11.6 |
| 8 | 15748 | 652 | street match | 22 / 9.2 / 1.4 | - | 25 (0.038) | 1.73 | 5.4 |
| 9 | 15749 | 173 | street match | 20 / 4.6 / 0.7 | - | 1 (0.006) | 2.1 | 13.6 |
| 10 | 15750 | 30 | street match | 11 / 2.7 / 0.5 | - | 0 (0.0) | None | 56.0 |
| 13 | 15753 | 368 | street match | 19 / 7.2 / 1.5 | - | 4 (0.011) | 2.74 | 3.6 |
| 16 | 15756 | 143 | street match | 20 / 5.8 / 2.4 | - | 2 (0.014) | 2.28 | 0.0 |
| 17 | 15757 | 142 | street match | 8 / 20.5 / 2.5 | - | 0 (0.0) | None | 28.8 |
| 18 | 15758 | 228 | street match | 21 / 3.1 / 1.0 | - | 0 (0.0) | None | 21.1 |
| 21 | 15761 | 142 | street match | 9 / 10.1 / 1.3 | - | 4 (0.028) | 1.47 | 9.7 |

Left out:

* plate 15744 (sheet 4): control points 92 m out, no street match: unplaced
* plate 15751 (sheet 11): 9 outlines, control points 78 m out: unplaced
* plate 15752 (sheet 12): 3 control points, no street match, no survivors: unplaced
* plate 15754 (sheet 14): control points 32 m out, no street match: unplaced
* plate 15755 (sheet 15): control points 2.2 km out: unplaced
* plate 15759 (sheet 19): overview plate at 1.1 m per pixel (Flushing, ward 3): houses are a few pixels, not traceable; no street match
* plate 15760 (sheet 20): overview plate at 1.1 m per pixel: not traceable; no street match

#### queens_rockaway_1907

2026 buildings (2004 frame, 22 brick, 0 stone), coverage 9.13 km2, 5 plates used; on a standing footprint (IoU > 0.5): 29; dropped by the final checks: 0 centre outside coverage, 0 overlapping; overlapping pairs left 0, touching / slightly overlapping pairs 8.

| sheet | plate | outlines | registration | street match: windows / shift found / left (m) | building match residual (m) | coincide (n, share) | median offset of those (m) | cross-val. of control points (m) |
|---|---|---|---|---|---|---|---|---|
| 32 | 15620 | 499 | street match | 14 / 5.6 / 1.1 | - | 5 (0.01) | 1.69 | 219.5 |
| 34 | 15622 | 426 | street match | 15 / 6.3 / 1.4 | - | 5 (0.012) | 1.82 | 52.7 |
| 35 | 15623 | 162 | street match | 13 / 14.9 / 1.8 | - | 0 (0.0) | None | 15.5 |
| 38 | 15626 | 638 | street match | 18 / 17.0 / 1.9 | - | 7 (0.011) | 2.56 | 0.0 |
| 39 | 15627 | 301 | street match + building match | 16 / 6.5 / 2.1 | 0.66 | 12 (0.04) | 1.09 | 5.3 |

Left out:

* plate 15625 (sheet 37): 3 control points, street match fails (23 m off, no consensus): unplaced
* plate 15628 (sheet 40): 2 outlines: nothing to place

#### staten_island_north_1917

8844 buildings (8294 frame, 548 brick, 2 stone), coverage 14.4 km2, 19 plates used; on a standing footprint (IoU > 0.5): 557; dropped by the final checks: 0 centre outside coverage, 0 overlapping; overlapping pairs left 0, touching / slightly overlapping pairs 28.

| sheet | plate | outlines | registration | street match: windows / shift found / left (m) | building match residual (m) | coincide (n, share) | median offset of those (m) | cross-val. of control points (m) |
|---|---|---|---|---|---|---|---|---|
| image 1646236 | 15367 | 838 | building match | - / - / - | 0.96 | 88 (0.105) | 1.19 | 12.1 |
| image 1646237 | 15368 | 251 | control points only | - / - / - | - | 7 (0.028) | 1.52 | 11.2 |
| image 1646238 | 15369 | 483 | building match | - / - / - | 0.56 | 93 (0.193) | 1.24 | 6.6 |
| image 1646239 | 15370 | 581 | building match | - / - / - | 0.63 | 39 (0.067) | 0.91 | 7.0 |
| image 1646240 | 15371 | 640 | building match | - / - / - | 0.77 | 20 (0.031) | 1.16 | 7.8 |
| image 1646241 | 15372 | 571 | building match | - / - / - | 1.45 | 9 (0.016) | 1.79 | 11.2 |
| image 1646242 | 15373 | 608 | building match | - / - / - | 0.54 | 44 (0.072) | 1.05 | 7.7 |
| image 1646268 | 15399 | 346 | building match | - / - / - | 0.61 | 7 (0.02) | 1.83 | 5.0 |
| image 1646269 | 15400 | 341 | building match | - / - / - | 1.07 | 14 (0.041) | 1.21 | 10.1 |
| image 1646270 | 15401 | 402 | building match | - / - / - | 1.46 | 15 (0.037) | 1.45 | 14.9 |
| image 1646273 | 15404 | 305 | building match | - / - / - | 0.53 | 11 (0.036) | 1.65 | 16.7 |
| image 1646302 | 15433 | 214 | building match | - / - / - | 0.16 | 2 (0.009) | 0.49 | 8.1 |
| image 1646311 | 15442 | 267 | control points only | - / - / - | - | 5 (0.019) | 2.25 | 15.2 |
| image 1646313 | 15444 | 213 | control points only | - / - / - | - | 7 (0.033) | 1.32 | 15.8 |
| image 1646314 | 15445 | 295 | building match | - / - / - | 0.9 | 19 (0.064) | 1.74 | 11.0 |
| image 1646319 | 15450 | 491 | building match | - / - / - | 0.47 | 71 (0.145) | 1.23 | 11.8 |
| image 1646320 | 15451 | 567 | building match | - / - / - | 0.14 | 73 (0.129) | 1.33 | 13.5 |
| image 1646321 | 15452 | 787 | control points only | - / - / - | - | 5 (0.006) | 1.38 | 12.3 |
| image 1646323 | 15454 | 644 | building match | - / - / - | 0.7 | 28 (0.043) | 1.31 | 5.3 |

Left out: 65 plates (listed with their reasons in `staten_island_north_1917_stats.json` and as `skip` in `tools_queens_si/layers.json`): the Staten Island plates whose registration nothing verifies (see above) and plates not traced (not reached).


## Hudson County, New Jersey (`hudson_*` layers, `tools_hudson/`)

Traced with a copy of the tool (`tools_hudson/atlas.py`: its footprints are `county_buildings.parquet` for Hudson County,
written to `data/interim/atlas_hudson/hudson_footprints.parquet`; scratch under `data/interim/atlas_hudson/`). Same format
and the same warnings as the layers above. Nothing is generated; the files are not complete inside their coverage.

| layer | atlas | area | buildings |
|---|---|---|---|
| `hudson_jersey_city_1919.geojson` | *Atlas of Jersey City, N.J.*, vol. 1 (G. M. Hopkins Co., 1919), 100 ft to the inch, 27 of its 40 plates | Jersey City: downtown (Paulus Hook is not covered, see below), Van Vorst, Harsimus, the Heights, Journal Square, Bergen-Lafayette, Communipaw, Greenville; Hoboken is not in this atlas | 34,668 (29,276 frame, 5,329 brick, 63 stone) |
| `hudson_hoboken_1891.geojson` | Sanborn / Brush *Insurance maps of Hudson County*, vol. 7, Hoboken, 1891 (LoC, 50 ft to the inch), plates 8, 9, 10 | Hoboken between Garden and River Streets, 2nd to 11th Streets (about 0.5 km2) | 357 (91 frame, 265 brick, 1 stone) |
| `hudson_heights_1873.geojson` | Spielmann & Brush, *Insurance maps of Jersey City*, 1873, vol. 4 plate 31 (NYPL) | Hudson City / the Heights: Webster, New York, Palisade Avenues, Griffith to South Streets | 252 (244 frame) |
| `hudson_heights_1887.geojson` | Chas. B. Brush, *Insurance maps of Hudson County*, vol. 8 plate 3 (NYPL) | Jersey City Heights, Summit Ave / Paterson Plank Road | 176 (175 frame) |

`map_year` is the atlas's date (1919, 1891, 1873, 1887). Hopkins 1919 shows the city as revised to 1919 (a building on it stood by 1919);
the Sanborn / Brush plates of 1891 carry copyright lines 1873, 1887 and 1891 (the sheet is a revision of the 1873 survey).
Materials: pink = `brick`, yellow = `frame`, blue / grey = `stone`; the green fill (outbuildings, shown on the Hopkins plates) is not exported.

### Source survey (what exists for Hudson County)
1. **Georeferenced in the NYPL Map Warper dump** (CC0 control points; NYPL scans public domain): Hopkins, *Atlas of Jersey City* vol. 1,
   1919 (plates 1, 3-6, 8-13, 15-32, 36-40 = 34 plates; 2, 7, 14, 33-35 are not in the dump); Spielmann & Brush, *Insurance maps of Jersey City*
   vol. 1, 1866 (8 plates: 2, 5, 9, 11, 16, 17, 19, 29; hand-drawn, 3-5 control points; one tried and left out, see below) and vol. 4, 1873 (plates
   29, 30, 31); Brush, *Insurance maps of Hudson County* vol. 8, 1887 (plates 2, 3); Hopkins's county atlas 1873 (plates "Jersey City",
   "Jersey City Pier", "Weehawken township": small scale, not used). **Not in the dump**: Hoboken, Bayonne, Union City / West Hoboken, West New York,
   Weehawken, North Bergen, Secaucus, Harrison, Kearny (no Hopkins 1873 / 1908, Bromley, Fowler or Spielmann & Brush Hoboken plate was found by title
   or by bounding box (-74.17..-73.98, 40.64..40.82)).
2. **Not georeferenced, public domain, Library of Congress Sanborn collection** (`https://www.loc.gov/collections/sanborn-maps/`, IIIF images
   `https://tile.loc.gov/image-services/iiif/...`, 5,600 x 8,150 px per half page, 50 ft to the inch, double plates split in L / R halves, rights: public domain),
   Hudson County, sanborn05511: vol. 1-2 1885 (Jersey City, 72 sheets each), vol. 11 1887, **vol. 7 1891 (Hoboken, 28 plates)**, vols. 3-6 1896 and 9-10 1898
   (Jersey City, Bayonne), vol. 8 1900 (Weehawken, West Hoboken, Union, West New York, Guttenberg, North Bergen, Secaucus), vols. 1-2 1906 and 3-6, 8-10 1910-12
   (Jersey City, Union Hill, Bayonne), Harrison / Kearny / East Newark 1907 (sanborn05501_001, 78 sheets), then 1918-24 single sheets, 1936-38, 1950-51 revisions.
   About 1,300 plates for 1885-1912. They are the way to Hoboken, Bayonne, Union City, Harrison and Paulus Hook / Exchange Place before 1919.
3. Not looked at: Rutgers' Historical Maps of New Jersey, Princeton, NYPL's un-georeferenced Hudson County volumes.

**Registration without control points works** (tried on three Hoboken plates, `tools_hudson/loc_register.py`): the two halves are joined; the
pixel positions of 8-10 street intersections are read off a 14 % preview, their ground positions come from today's street centrelines (Overture, `streets.py`)
and an affine fit leaves 0.2-4 m (median about 1.3 m); the building match against the standing footprints then moves the plate by a further 1.3-1.8 m. In Hoboken's
regular grid this needs two calls per plate (one look, one spec). The same tracing settings serve Sanborn colours (pink / yellow / blue-grey).

### Registration, per plate
The Map Warper control points are the first fit (4-56 points, cross-validated 1-15 m); `refine_buildings` then matches the traced outlines to today's footprints of
pre-war buildings and corrects the plate by 2-5 m on most plates (the control-point fits were 3-5 m out in the same direction on most Jersey City plates).
There is no street tint on these atlases, so no street match. **Rule applied here**: a plate is kept if at least 10 outlines coincide with a standing footprint
(IoU > 0.5) with a median centre offset under 4 m, or its control points cross-validate at about 3 m or better; otherwise it is left out and listed.
Left out: Hopkins plates 3, 6, 26, 27, 29, 39, 40 and Spielmann & Brush 1873 plates 29, 32, Brush 1887 plate 2 (reasons in the tables). Hopkins plates 10, 13, 18, 29-31 (sheets 10, 13, 18, 22 and similar, with 3-5 control points) have no building match and keep the control-point fit; they are verified only by 11-14 coinciding outlines each (median offsets 1.2-2.8 m), which is thin. Hoboken plate 8 has 5 coinciding outlines only: it rests on the street-intersection fit plus a 4-window building match.

### Tables
<!-- TABLE hudson_jersey_city_1919 -->
| sheet | Map Warper id | control points (fit, CV rms m) | m / px | building match | buildings (frame / brick / stone) | on a standing footprint (IoU > 0.5) | their median offset m | status |
|---|---|---|---|---|---|---|---|---|
| 1 | 26192 | 40 (tps, 3.0) | 0.11 | shift: 8 windows, 1.19 m | 600 (324 / 275 / 1) | 35 (6 %) | 1.95 | ok |
| 3 | 26194 | | | | 0 | | | left out: unverified: 4 control points (cross-validated 6 m), no building match, only 5 outlines coincide with a standing footprint |
| 4 | 26195 | 8 (affine, 8.3) | 0.111 | affine: 17 windows, 0.52 m | 1011 (769 / 242 / 0) | 218 (22 %) | 1.19 | ok |
| 5 | 26196 | 5 (affine, 7.4) | 0.11 | shift: 4 windows, 0.77 m | 234 (120 / 114 / 0) | 12 (5 %) | 1.54 | ok |
| 6 | 26197 | | | | 0 | | | left out: unverified: 7 control points (cross-validated 5.9 m), 3 coinciding outlines, no building match |
| 8 | 26199 | 10 (affine, 6.8) | 0.111 | shift: 5 windows, 0.45 m | 850 (702 / 146 / 2) | 48 (6 %) | 1.35 | ok |
| 9 | 26200 | 4 (affine, 2.2) | 0.167 | affine: 23 windows, 0.27 m | 1020 (786 / 230 / 4) | 67 (7 %) | 1.39 | ok |
| 10 | 26201 | 4 (affine, 8.5) | 0.146 | none | 1335 (1054 / 272 / 9) | 14 (1 %) | 1.15 | ok |
| 11 | 26202 | 4 (affine, 5.7) | 0.165 | affine: 54 windows, 1.01 m | 2648 (2282 / 362 / 4) | 677 (26 %) | 1.32 | ok |
| 12 | 26203 | 5 (affine, 2.8) | 0.161 | affine: 19 windows, 0.69 m | 2314 (2084 / 229 / 1) | 176 (8 %) | 1.45 | ok |
| 13 | 26204 | 5 (affine, 1.0) | 0.171 | none | 1689 (1434 / 255 / 0) | 11 (1 %) | 1.94 | ok |
| 15 | 26206 | 11 (affine, 15.2) | 0.166 | affine: 44 windows, 0.95 m | 2216 (1844 / 371 / 1) | 371 (17 %) | 1.28 | ok |
| 16 | 26207 | 32 (tps, 4.1) | 0.166 | affine: 42 windows, 2.05 m | 2127 (1789 / 338 / 0) | 219 (10 %) | 1.54 | ok |
| 17 | 26208 | 6 (affine, 3.4) | 0.167 | affine: 32 windows, 0.98 m | 955 (690 / 265 / 0) | 108 (11 %) | 1.52 | ok |
| 18 | 26209 | 3 (affine, 0.0) | 0.169 | none | 1232 (1054 / 169 / 9) | 11 (1 %) | 2.84 | ok |
| 19 | 26210 | 17 (affine, 4.7) | 0.169 | affine: 20 windows, 0.84 m | 980 (839 / 134 / 7) | 178 (18 %) | 1.25 | ok |
| 20 | 26211 | 18 (affine, 3.7) | 0.168 | affine: 43 windows, 1.21 m | 2217 (1961 / 255 / 1) | 333 (15 %) | 1.37 | ok |
| 21 | 26212 | 16 (tps, 5.9) | 0.168 | affine: 34 windows, 1.5 m | 1802 (1510 / 292 / 0) | 233 (13 %) | 1.3 | ok |
| 22 | 26213 | 4 (affine, 5.6) | 0.167 | affine: 46 windows, 0.75 m | 1559 (1331 / 228 / 0) | 353 (23 %) | 1.21 | ok |
| 23 | 26214 | 4 (affine, 3.2) | 0.165 | affine: 14 windows, 0.65 m | 896 (818 / 78 / 0) | 162 (18 %) | 1.2 | ok |
| 24 | 26215 | 24 (affine, 3.3) | 0.166 | shift: 9 windows, 0.47 m | 538 (467 / 68 / 3) | 133 (25 %) | 1.2 | ok |
| 25 | 26216 | 4 (affine, 7.0) | 0.224 | affine: 11 windows, 0.49 m | 669 (594 / 75 / 0) | 99 (15 %) | 1.33 | ok |
| 26 | 26217 | | | | 0 | | | left out: control points inconsistent (cross-validated 9594 m), nothing standing to check |
| 27 | 26218 | | | | 0 | | | left out: unverified: control-point fit only (cross-validated 7.3 m); the 2 coinciding outlines sit 6.8 m off |
| 28 | 26219 | 19 (affine, 6.5) | 0.222 | shift: 8 windows, 0.43 m | 682 (545 / 137 / 0) | 101 (15 %) | 1.47 | ok |
| 29 | 26220 | | | | 0 | | | left out: control points inconsistent (cross-validated 21 m), 9 coinciding outlines, no building match |
| 30 | 26221 | 11 (affine, 1.9) | 0.223 | affine: 12 windows, 0.54 m | 750 (668 / 82 / 0) | 78 (10 %) | 1.45 | ok |
| 31 | 26222 | 4 (affine, 420.8) | 0.218 | none | 596 (521 / 75 / 0) | 14 (2 %) | 1.53 | ok |
| 32 | 26223 | 12 (affine, 5.7) | 0.222 | shift: 4 windows, 0.6 m | 519 (443 / 75 / 1) | 55 (11 %) | 0.96 | ok |
| 36 | 26227 | 15 (affine, 4.7) | 0.22 | affine: 18 windows, 0.67 m | 3541 (3184 / 355 / 2) | 342 (10 %) | 1.5 | ok |
| 37 | 26228 | 56 (tps, 3.8) | 0.221 | affine: 41 windows, 1.35 m | 1426 (1282 / 139 / 5) | 124 (9 %) | 1.55 | ok |
| 38 | 26229 | 12 (tps, 2.6) | 0.219 | shift: 6 windows, 1.01 m | 394 (272 / 109 / 13) | 16 (4 %) | 1.87 | ok |
| 39 | 26230 | | | | 0 | | | left out: unverified: control-point fit only (cross-validated 9.1 m), no outline coincides with a standing footprint |
| 40 | 26231 | | | | 0 | | | left out: unverified: control-point fit only (42 points, cross-validated 3.9 m), no outline coincides with a standing footprint (Bayonne industrial shore) |
<!-- /TABLE hudson_jersey_city_1919 -->

Hoboken 1891:

| sheet | Map Warper id | control points (fit, CV rms m) | m / px | building match | buildings (frame / brick / stone) | on a standing footprint (IoU > 0.5) | their median offset m | status |
|---|---|---|---|---|---|---|---|---|
| 8 | 91010008 | 8 (affine, 2.0) | 0.099 | none | 108 (41 / 67 / 0) | 5 (5 %) | 1.74 | ok |
| 9 | 91010009 | 10 (affine, 1.8) | 0.1 | none | 162 (44 / 117 / 1) | 29 (18 %) | 1.26 | ok |
| 10 | 91010010 | 10 (poly2, 1.9) | 0.099 | none | 87 (6 / 81 / 0) | 8 (9 %) | 2.18 | ok |

Heights 1873:

| sheet | Map Warper id | control points (fit, CV rms m) | m / px | building match | buildings (frame / brick / stone) | on a standing footprint (IoU > 0.5) | their median offset m | status |
|---|---|---|---|---|---|---|---|---|
| 29 | 28490 | | | | 0 | | | left out: unverified: 4 control points cross-validate at 32 m, only 6 outlines coincide with a standing footprint |
| 30 | 28491 | 4 (affine, 266.3) | 0.069 | none | 252 (244 / 6 / 2) | 16 (6 %) | 2.31 | ok |
| 31 | 28492 | | | | 0 | | | left out: unverified: 22 control points but cross-validated 9.9 m, 2 coinciding outlines, no building match |

Heights 1887:

| sheet | Map Warper id | control points (fit, CV rms m) | m / px | building match | buildings (frame / brick / stone) | on a standing footprint (IoU > 0.5) | their median offset m | status |
|---|---|---|---|---|---|---|---|---|
| 2 | 26155 | | | | 0 | | | left out: unverified: 3 control points (no cross-validation possible), no outline coincides with a standing footprint |
| 3 | 26156 | 5 (affine, 1.3) | 0.068 | none | 176 (175 / 1 / 0) | 1 (1 %) | 0.84 | ok |

Spielmann & Brush 1866 (NYPL, hand-drawn): plates 28496, 28497, 28499, 28500 were traced and yielded 6-12 outlines each out of dozens drawn (pale
hand colours, lots not divided by lines, large unbroken fills), none coinciding with a standing footprint and the control points either 3 (no cross-validation)
or cross-validated 16 m: **no 1866 layer was made.**

### Checks
* Numeric, on the final files (read back with shapely, UTM 18N): all polygons valid; areas 15-5,000 m2; ids unique; every centre inside its layer's coverage; no two
  outlines of a layer overlap by more than 1 m2 (the export left 155 pairs on the Hopkins plates where two plates' masks overlap or a house was cut in two;
  `tools_hudson/dedupe.py` dropped the smaller of each pair: 132 outlines). Share on a standing footprint (IoU > 0.5): Hopkins 12 % (4,187), Hoboken 12 %, Heights 1873 6 %, 1887 0.6 %.
  The median offset of those outlines is 1.0-2.2 m on every kept plate (Hopkins 0.96-1.95 m), well under the 4 m limit.
* By eye (overlay crops, `atlas.py overlay ... [--final]`): Hopkins plate 1 (Henderson / Washington St, 160 m, with the first and with the final settings),
  plate 11 (Griffith St), plate 20 (Oak St), plate 37, plate 16 (Summit area), Spielmann & Brush 1873 plate 31 and Brush 1887 plate 3 (one window each), Hoboken
  plates 8 and 10 (150-170 m each). On the Hopkins windows about 90-95 % of the drawn buildings are traced (rows come out house by house), outlines are ragged where lot
  numbers are written over a yellow house, a few pale yellow outhouses are missed, a few pieces of lettering and the book gutter make false slivers; the green fill
  (outbuildings) is not exported. In the first window the pale Hopkins yellow was missed by the Bromley threshold (most of the yellow buildings in the window, not counted): `db_min` 9 -> 6.5 fixed it.
  On the 1873 and 1887 windows nearly all drawn buildings are traced (1887: all but a few, the plate is mostly empty ground in 1887; 1873: about 90 %; these two windows were judged roughly, not counted). On the Hoboken
  windows about 85 % of the drawn buildings are traced, but **runs of attached houses come out as one outline** (a row of 3-8 houses; the Sanborn lot lines are thinner than Hopkins's); the
  Hoboken layer therefore has about 120 outlines per plate where 400 lots are drawn.
* Not looked at by eye: 22 of the 27 Hopkins plates (all except 1, 11, 16, 20, 37), Hoboken plate 9, the north and south ends of every plate. No window was checked for outlines on ground the
  fill-zone file dates later than the map year (the Hopkins atlas shows the filled waterfront as built; the loader will have to check each outline against the land year).

### Known failures
Rows merged on the Sanborn plates (above); the pale yellow of some Hopkins sheets is close to the paper's tone, so frame buildings on faded plates may be under-read (not measured);
the book gutter (a dark stripe) cuts Hoboken's outlines at the centre; gasholders and circular tanks are not traced; plates whose control points are unverifiable were left out, which
removes Bayonne's shore, much of Greenville / Constable Hook (Hopkins plates 39, 40), and the Jersey City waterfront terminals (plates 6, 26, 27); Hopkins plates 2, 7, 14, 33-35 are not
in the Map Warper dump at all. The 1919 file is 34 MB (coordinates to 6 decimals).

### What remains and how
* Hoboken: 25 further plates of vol. 7 (1891) and the same city in 1896-1912, Bayonne (vols. 9-10, 1898 / 1912), Union Hill, West Hoboken, Weehawken, West New York, Harrison and Kearny
  (1900, 1907, 1910): each a double plate, registered with `loc_register.py` by street intersections and then `trace` / `refine_buildings` / `export` / `dedupe.py`. In the regular grids this
  is 2-3 calls per plate; the pier plates 1-6 have no streets and need a corner of the grid on the plate. Rows merged: tune `wall_px`, `line_depth` for the thin Sanborn lot lines.
* Downtown Jersey City before 1919 (Paulus Hook, Exchange Place, Pavonia / Erie terminals): Sanborn 1885 / 1896 / 1906 (vols. 1-2, 3-4) the same way; the 1866 NYPL plates are hand-drawn and not traceable by colour.
* Hopkins 1919 plates 2, 7, 14, 33-35 (and the plates left out) need hand control points (street intersections) as above.
