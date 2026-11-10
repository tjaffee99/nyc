# Building footprints traced from real-estate atlases

What stood where the fire-insurance tracings (Manhattan below 86th St, downtown Brooklyn) say nothing: the
buildings drawn on the coloured real-estate atlases of the 1880s-90s, read plate by plate from the New York
Public Library's scans. Every outline is a fill the atlas itself colours as a building; nothing is generated.
What the atlas does not give (years of construction and demolition, heights) is not in these files.

| layer | atlas | area |
|---|---|---|
| `kings_towns_1890.geojson` | *Robinson's atlas of Kings County, New York* (E. Robinson, 1890), all 31 plates in the Map Warper dump | the county towns before they joined Brooklyn: Flatbush, New Utrecht (Bay Ridge, Fort Hamilton, Bath Beach, Bensonhurst), Gravesend (the village, Coney Island, Sheepshead Bay), Flatlands (Canarsie) |
| `harlem_1897.geojson` | *Atlas of the city of New York, Manhattan Island* (G. W. & W. S. Bromley, 1897), the 14 plates north of 84th / 86th St | Yorkville north of 84th St, East Harlem, the Upper West Side from 86th St, Morningside Heights, Harlem, Manhattanville, Hamilton Heights, Washington Heights to about 190th St |
| `bronx_23rd_ward_1887.geojson` | *Atlas of the city of New York … 23rd Ward* (E. Robinson & R. H. Pidgeon, 1887), 20 of 21 plates (plate 6 is not in the dump) | the Bronx south of about 170th St: Mott Haven, Port Morris, Melrose, Morrisania, Hunts Point, Highbridge, Claremont |

Each layer has a `<layer>_coverage.geojson` (one polygon per plate read) and a `<layer>_stats.json` (the
numbers of the tables below, written by the export).

## Format

`<layer>.geojson`: FeatureCollection, WGS84 (CRS84), one Polygon per building, no holes. Properties:

| property | |
|---|---|
| `id` | `<source>_<sheet>_<n>` |
| `map_year` | the atlas's publication year (see *Map year and survey year*) |
| `material` | `frame` (the yellow / ochre fill), `brick` (the rose / carmine fill), `stone` (grey fill, city atlases only) |
| `source` | `robinson_kings_1890`, `bromley_manhattan_1897`, `robinson_23rd_ward_1887` |
| `sheet` | plate number as printed, or `image <NYPL image id>` where the Map Warper title does not give it |
| `plate` | the plate's NYPL Map Warper id |
| `area_m2` | |
| `on_today` | true if the outline coincides with one of today's footprints (IoU > 0.5) — measured here for the checks; the pipeline should apply its own rule |
| `today_cover` | share of the outline lying on today's footprints of pre-war buildings (recorded year <= 1940, or none) |

`storeys` is **not** given: the Kings County and Bronx plates do not print it; the Bromley plates do (`3B`,
`4`, `5` in the front of each house) but the figures were not read.

`<layer>_coverage.geojson`: one Feature per plate (`sheet`, `plate`, `buildings`, `registration_m`,
`coincide_share`): the Map Warper mask of the plate — the part of the sheet its georeferencer kept — moved by
the same correction as the buildings. Buildings are kept by their centre: an outline may reach a few metres
over the coverage edge.

## How to use the layers

* **Not complete.** Inside the coverage the tracing finds most buildings but not all (recall measured on
  windows: about 95 % Kings County, 90-95 % Harlem, about 85-90 % Bronx — see each layer). As with the other
  traced layers, absence is not evidence of an empty lot. Do not add these years to `COMPLETE`.
* **A row can be one polygon or a house can be two.** On the two city layers the houses of a row are cut at
  the party walls the atlas draws; where a wall line is faint two houses come out as one outline, where
  figures or a pencil line cross a house it comes out in pieces or with a bite out of it (about one outline in
  ten in the windows looked at). On the Kings County plates (300 ft to the inch) attached buildings are one
  outline. Hence many outlines of standing houses do **not** reach IoU 0.5 with today's footprint although
  they lie on it: `today_cover` is there to tell "lies on pre-war buildings" (probably the same fabric, or a
  pre-war replacement) from "lies on post-war buildings or open ground" (certainly gone).
* **Shapes are the atlas's.** At 1:3,600 (Kings County) a house is 10-25 pixels across; outlines are good to
  about a metre plus the registration. The stone-front strip of a Bromley row house is joined to the house
  where the join was found; where not, the outline is 2 m short at the street.
* **Material** is the atlas's colour and is reliable for frame against brick; `stone` on the Bromley plates is
  the grey fill (churches, a few institutions) — a brownstone-fronted brick house is `brick`.
* **X-crossed buildings** (stables, sheds, barns on the Robinson plates) are in the layer as buildings, without
  a flag.

## Map year and survey year

* Kings County: the plates read are marked "Entered according to Act of Congress in the year 1889 by
  E. Robinson"; the atlas was published in 1890. `map_year` is 1890; a building on it stood by 1889.
* Manhattan: published 1897 (NYPL catalogue date). The collars were not read for a survey date. The NYPL copy
  carries later pencil and blue-crayon lines (not buildings; they are not traced, but they cut a few outlines).
* Bronx: published 1887 (NYPL catalogue date); collars not read.

## Sources and licences

* Scans: NYPL Map Division, digital collections (public domain), full-size masters
  `https://images.nypl.org/index.php?id=<imageId>&t=u` (the image ids are in the tables). Kept as JPEG (quality
  95, no chroma subsampling) under `data/raw/atlas/nypl_u/` (gitignored, 1.1 GB for the 65 plates).
* Control points and masks: NYPL Map Warper records in the NYC Space/Time Directory dump
  `https://s3.amazonaws.com/spacetime-nypl-org/datasets/mapwarper/mapwarper.objects.ndjson` (CC0), as worked
  out for `data/manual/extents` (its `tools/warp.py` and `tools/streets.py` are reused, not copied).
* Today's streets and footprints used for registration and checks: Overture roads and the city's footprints
  (`data/raw/overture`, `data/interim/nyc_footprints_raw.parquet`).
* The tracings are this project's (CC0).

## Method (`tools/atlas.py`)

1. **Scan and first fit.** The plate's Map Warper control points give pixel -> ground (affine with 3-9
   points, 2nd order or thin-plate spline with more, chosen by cross-validation in `warp.py`). Most plates have
   only 4-5 points, and some fits are 5-16 m out.
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
     along one side only. Brick must be 11 pixels wide with 72 % outline. Where a tile has no orange bands at
     all, the band hue is read as frame (on some sheets the colourist's ochre runs to orange).
   * *City plates* (`bromley_city`, also used for the Bronx atlas): the fill of a row runs through from house
     to house; the party walls are the lot lines drawn across it. Walls = thin drawn lines that hang together
     (connected line components of 120 pixels or more, strokes 3 pixels thick or more left out as figures);
     each connected piece of fill between walls is a building; a small grey piece against a rose one is that
     house's stone front and is joined to it; pieces need an outline round 55 % (Bronx: 35 %, its lines are
     faint) of their edge.
   * Outlines are simplified to about one pixel; a shape that fills 84 % of its bounding rectangle becomes that
     rectangle. Buildings between 15 and 5,000 m2 are kept.
5. **Export.** Buildings whose centre lies inside the plate's Map Warper mask; where two plates' masks overlap
   a building traced twice is kept once.

## Layers

### kings_towns_1890

Robinson's *Atlas of Kings County* (1890), plates 1-31; 300 ft to the inch (0.48 m per pixel), plates 1-6 of
Flatbush 200 ft (0.32 m). Buildings: ochre (frame), carmine (brick), stables and barns crossed.

<!-- TABLE kings_towns_1890 -->
<!-- /TABLE kings_towns_1890 -->

**Registration.** Every plate was corrected on its streets (the planned grid the atlas draws is today's grid).
The control-point fits were 2-5 m out (more on some plates, see "shift found"); after the correction the same
measurement leaves 1-2 m. The towns' buildings have almost all gone, so few plates have enough standing
buildings for an independent check; where there are any, they sit 1-2.5 m (median) from their footprints.

**Looked at.**
* Gravesend village (plate 22, 480 m window around Gravesend Neck Rd and McDonald Av): 88 buildings drawn,
  84 traced (95 %); missed: two crossed sheds standing on property bands, one house on a carmine band, one
  very small shed. 3 false outlines, all pieces of carmine band read as brick (so about 94 % of the outlines
  are buildings); the hotel on the main street came out as four pieces.
* Flatbush (plate 2, 190 m window at the Flatbush Gas Works): 31 drawn, 30 traced, no false outline. Before
  the last change to the tracing this window returned 6 of 31: the frame fill on this sheet is as orange as
  the property bands of other sheets and was dropped as band. The rule now reads the band hue as frame where a
  tile has no orange band; a sheet with both orange bands and orange buildings would still lose buildings.

**Known failures.** Carmine band pieces read as small brick buildings (a few per plate; brick is rare in the
towns, so a brick outline under about 60 m2 away from a street is suspect). Buildings standing on a band of
their own colour are missed. Large buildings covered with lettering (hotels, pavilions at Coney Island) break
into pieces. Attached buildings are one outline.

### harlem_1897

Bromley's *Atlas of the city of New York, Manhattan Island* (1897): plates 31, 32, 34, 36, 37, 38, 40, 42 and
six plates the Map Warper titles only call "Part of Section …" (image ids in the table); about 160 ft to the
inch (0.24 m per pixel), the last plate (Washington Heights) smaller. Rose = brick, grey strip along the front
= stone front, grey = stone, yellow = frame.

<!-- TABLE harlem_1897 -->
<!-- /TABLE harlem_1897 -->

**Registration.** No street tint on this atlas; the plates were fitted on the standing buildings. The first
fits were 1-3.5 m out; the correction's window residual is 0.2-0.8 m, and outlines that coincide with a
footprint sit 1.2-2.1 m (median centre distance, which includes the difference in shape) from it, without a
common direction. Plates 38 (Morningside Heights, mostly empty in 1897) and the Washington Heights plate had
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

**Known failures.** Two houses as one outline where the party wall is faint; a house in pieces under large lot
numbers or pencil lines; stone-front strips not joined; grey hatched grounds are not read (only fills).

### bronx_23rd_ward_1887

Robinson & Pidgeon's atlas of the 23rd Ward (1887), plates 1-5 and 7-21; about 100 ft to the inch (0.17-0.18 m
per pixel). Pale yellow = frame, rose = brick, grey = stone; the sheets are greyish and the lines faint.

<!-- TABLE bronx_23rd_ward_1887 -->
<!-- /TABLE bronx_23rd_ward_1887 -->

**Registration.** The weakest of the three. The control-point fits (3-9 points) were up to 16 m out; the
street match (the atlas tints its streets lilac) corrects most plates to about 2 m by its own measure; where
standing buildings exist the building match was applied on top. Almost nothing of 1887 stands in Mott Haven
and Morrisania, so most plates have no independent check — the table says for each plate what was applied and
what is left. A plate without any correction keeps the control-point fit and may be several metres out.

**Looked at.** E 141st-143rd St at the railway (plate 2, 200 m): about 115 buildings drawn, 99 outlines with
the first setting; the missed ones had outlines too faint for the 55 % rule, which was lowered to 35 % for this
atlas — not looked at again after the change.

**Known failures.** Faint outlines (missed buildings, or two houses in one outline); crossed sheds partly
filled; figures inside small buildings.

## Checks

* `export` checks every polygon: valid, 15-5,000 m2, centre inside the coverage (counts in `<layer>_stats.json`
  under `total`: `invalid`, `area_out_of_range`, `outside_coverage` — all 0).
* Registration: per plate in the tables (street match before / after, building match residual, median offset
  of the outlines that coincide with a standing footprint). A plate whose standing buildings sit more than 8 m
  from their footprints is left out by `export`; none was.
* By eye: the overlays named under each layer (`tools/atlas.py overlay`: plate crop with the traced outlines
  and today's footprints).

Not checked: the layers in the pipeline or the viewer; plates other than those named under "Looked at" by eye;
the storeys; the survey dates on the collars of the 1887 and 1897 atlases.

## Not done, and what would extend this

| area | atlas in the Map Warper dump | note |
|---|---|---|
| Brooklyn's row-house belt (Bedford, Bushwick, Park Slope) | Bromley 1880 (28 plates, 4 control points each), Robinson 1886 (38 plates, 12-13 points), Hyde 1898 (73 plates) | at 300 ft to the inch the party walls are one pixel: rows would come out as one outline each. The large-scale volumes ("Atlas 61-97", 1886-1908, 20-100 plates each) would give houses, with the city style |
| Gravesend / Flatlands again in 1899 | Hyde, *Atlas of the Brooklyn Borough* vol. 3 (33 plates) | a second date for the towns |
| Queens (Jamaica, Flushing, Newtown, Long Island City) | Wolverton 1891 (18 plates at county scale), Hyde 1901-07 ward atlases (9-48 plates) | not opened |
| the Bronx north of 170th St | Robinson 1885 (Ward 24 plates at 500-800 ft to the inch: too small), Bromley 1893 / 1897 / 1900 volumes | not opened |
| Manhattan above 86th St in the 1880s | Robinson 1885 (plates 22-33, 5-26 points), Bromley 1879 / 1891 | an earlier state of Harlem; Robinson's style is the county style |
| Staten Island | Beers 1874 (too small a scale), Robinson 1898 / 1907 | not opened |
| plate 6 of the 23rd Ward atlas | not in the dump | a hole in the Bronx coverage (around E 149th St / Third Av) |

## Tools

`python -I data/manual/atlas/tools/atlas.py <command>` from the repository root with the project's venv
(packages used: numpy, scipy, shapely, rasterio, Pillow, duckdb; no OpenCV).

| | |
|---|---|
| `layers.json` | the layers: atlas, map year, style, plates (Map Warper id, sheet), per-layer settings |
| `atlas.py fetch <layer>` | master scans -> `data/raw/atlas/nypl_u/` |
| `atlas.py refine <layer> [plate]` | street match -> `data/interim/atlas/<layer>/<plate>_corr.json` |
| `atlas.py trace <layer> [plate]` | tracing -> `data/interim/atlas/<layer>/<plate>.pkl` (pixel outlines, ground outlines, match against today) |
| `atlas.py refine_buildings <layer> [plate]` | building match, then the ground outlines again |
| `atlas.py export <layer>` | the three files of a layer |
| `atlas.py readme` | the tables of this file |
| `atlas.py overlay <layer> <plate> <x,y> <size_m> <out.png> [--px]` | picture for checking by eye |
| `run_layer.sh`, `run_city.sh`, `run_reg.sh` | the three runs in parallel workers (county plates; city plates; registration only). Do not edit them while they run |

`pipeline/sanborn_trace.py` (the Bay project's Sanborn tool, written for one district's street frame) is kept as
it was copied, with a note at its head: nothing of it runs here, the atlas tracing is `tools/atlas.py`.

A trace takes 1-3 minutes of processor time per plate and under 1 GB (the plate is read in tiles, and only
around fills).
