# Gap fill: generated buildings where the evidence shows built ground and the map has none

`pipeline/gap_fill.py` → `data/interim/gapfill/gapfill.parquet`. Every row is **generated** (`procedural`):
a lot-sized outline, a start, an end. None is a traced or recorded building. Each rests on a named piece
of evidence that its spot was built on at that time, and each gives way to anything real: the rows are
recomputed against the map at every run and never share ground with a building of the map while both stand.

Why: a building put up after the last traced atlas of its district and pulled down before 1996 (when the
city's record of removed footprints starts) is in no source the map has. Hell's Kitchen's 50s, Lincoln
Square, East Harlem, the South Bronx, Brownsville, Williamsburg, Long Island City, downtown Jersey City
stood empty or thin at 1880 / 1925 / 1950 although they were densely built.

Last run (2026-11-10 23:46, against the buildings built at 23:16 / 23:20): **149,169 rows** — Manhattan 13,364,
Bronx 23,690, Brooklyn 39,641, Queens 35,861, Staten Island 7,630, Hudson County 28,983. All numbers of
that run are in `numbers.md`.

## Files

| file | content |
|---|---|
| `README.md` | this note |
| `numbers.md` | the checks of the last run (a copy of `data/interim/gapfill/report.md`): rows by area and evidence, the photographs' calls, the test districts before / after, the census check, the invariants |
| `hudson_builtup_1897.geojson` | built-up ground of Hudson County on the USGS 15-minute sheets of 1898 (74 polygons, 3,147 ha), read with the extents part's own tool; same properties as `data/manual/extents/*.geojson` |
| `tools/hudson_1897.py` | makes that file (`.venv/bin/python -I data/manual/gapfill/tools/hudson_1897.py`, 75 s) |

Scratch (gitignored, rebuilt by the stage): `data/interim/gapfill/` — `existing.parquet` (snapshot of the map),
`lots_v3/` (the lots and their photograph scores per z14 block, 2.0 million lots), `sheet_ink_v3/` (Hudson
County: the 1940s sheets read on the lots, `shifts.json`), `rows/` (the rows per block, with diagnostic
columns), `gapfill.parquet`, `stats.json`, `extent_keep.json`, `report.md`, `look/` (thumbnails).
Nothing was downloaded by this stage: it reads what the aerial, extents and piers parts fetched
(`data/raw/aerial`, `data/raw/extents/usgs`, `data/raw/piers/usgs`).

## Output

`gapfill.parquet` — GeoParquet, EPSG:4326, one Polygon per row (rectangles; a few cut around a small map building):

| column | |
|---|---|
| `id` | `gf` + 14 hex digits: hash of the lot's centre (lon, lat to 1e-6) and of the evidence that anchors the row. Unique. Stable across runs as long as the streets and the old buildings of the block (which fix the lot grid) do not change |
| `start_year`, `end_year` | decimal years (two places), `end - start >= 1` |
| `height_m`, `storeys` | by type (below) |
| `material` | `brick` / `frame` |
| `evidence` | what says the spot was built on (table below) |
| `end_basis` | what dates the end (table below) |
| `area` | `"1"` … `"5"` (borough of the nearest building of the map) or `"Hudson"`. In GeoPandas read it as `df["area"]` (`df.area` is the geometric area) |

`evidence`:

| code | rows | meaning |
|---|---|---|
| `aerial1924` | 26,053 | the 1924 photograph shows a building on the lot (the model of `aerial_presence.py`) |
| `aerial1951` | 39,346 | the 1951 photograph does |
| `aerial1924+1951` | 12,595 | both do, with no building of the map on the lot in between |
| `extent<year>+aerial…` | 7,394 | as above, and the lot lies in ground that the built-up snapshot of `<year>` (`data/manual/extents`) shows built: the start is put before that snapshot (for a measured share of such lots, see *Extents*) |
| `extent<year>` | 34,798 | no photograph can speak (the map's own building on the lot dates from before 1927): the lot lies in built-up ground of the snapshot and the map's building on it is at least five years later — a predecessor, for a measured share of such lots. **The weakest rows**: a block-level map and a share |
| `usgs1947_blocks`, `usgs1943_blocks` | 19,061 | Hudson County: the lot lies on a built block front (heavy black ink) of the USGS sheet Jersey City 1:24,000 of 1947 / Weehawken 1:25,000 of 1943 |
| `usgs1897_builtup+usgs194x_blocks` | 4,072 | the same, started before the 1898 sheets' built-up ground (a share) |
| `usgs1897_builtup` | 5,850 | Hudson County: as `extent<year>`, from `hudson_builtup_1897.geojson`, for gaps that close before 1948 |

`end_basis`:

| code | rows | meaning |
|---|---|---|
| `replaced_by_standing` | 75,755 | the building that stands on the spot today went up (the row ends 1-2.5 years before its year) |
| `replaced_by_vanished` | 17,177 | a later building of the map, itself gone, went up on the spot |
| `nycha:<development>` | 1,630 | a housing authority development stands in the same city block (within 90 m, no street between): 2.5-4.5 years before its completion date (Development Data Book, NYC Open Data `evjd-dqpz`, through `data/interim/records/records_by_bin.parquet`) |
| `park:<name>` | 1,427 | the lot lies in a park property acquired later: 0.3-1.8 years after the acquisition date (Parks Properties, NYC Open Data `enfh-gkve`) |
| `highway:<name>` | 2,382 | the lot lies within 25 m of a motorway centre line: 1.5-3.5 years before its opening (`data/interim/roads/highway_years.csv`, the researched openings of `data/manual/routes.csv`) |
| `photo1951_open` | 1,903 | the 1924 photograph shows a building, the 1951 photograph open ground (p <= 0.1): a year between the two, by hash |
| `estimated` | 48,895 | nothing on the spot today and no record: when the nearest large building (>= 400 m2, within 60 m) went up, else a year spread over 1956-1984. In the boroughs a row never ends after 1995: a building standing in 1996 would be in the city's record of removals, and then the map would have it |

## Method

### 1. Lots (candidates, not buildings)

- **City blocks**: the polygons between today's street centre lines (Overture / OpenStreetMap, classes
  residential … trunk; motorways and tunnels are not streets). Blocks under 600 m2 or over 150 ha are left out.
  Ground not enclosed by streets (waterfront strips beyond the last street) gets no lots.
- **Building line**: the block polygon shrunk by the distance at which the block's old buildings (standing,
  built by 1935) stand from the centre lines (15th percentile, 6.5-14 m; 9.2 m — half a 60 ft street —
  where fewer than five old buildings stand).
- **Rows along every straight frontage**: the block polygon is simplified by 2.5 m; along each of its edges
  of 20 m and more a row of outlines stands on the building line, at the edge's own bearing, longest frontage
  first; an outline that would lie on one already placed is dropped (corners go to the longer frontage). An
  outline is never deeper than half the block behind its frontage.
- **Inside superblocks** (blocks whose streets were closed: housing projects, Lincoln Center): further rows
  on the block's own frame (the long side of its minimum rotated rectangle), the block cut as *k* blocks,
  *k* = round((depth + 18.3 m) / 79.2 m), with an 18.3 m street between them — the old grid reconstructed
  by rule, not from a map. Only where no frontage row lies.
- **Size of an outline**: measured, not assumed — the median width and depth of the old buildings of the same
  block (of the nearest block that has five, where it has none), within 4.8-8.5 m by 9.5-27 m; depth varies
  0.88-1.12 by hash; detached types stand 1.5 m apart. Type from the median roof height of the block's old
  buildings: under 9 m `frame` (2-3 storeys, frame), 9-13.5 m `rowhouse` (2-4, brick), above `tenement`
  (4-6, brick). Height = storeys x 3.3 m + 1 m (frame: x 3.0 + 1.5).
- **Not a lot**: an outline nearer to a street centre line than that street's half width (6-14 m by class, but
  never more than the block's own building line), on today's water, in a cemetery; an outline that leaves the
  building-line polygon by more than 0.6 m.

A standing building's footprint is never copied: a large modern footprint and open ground are cut the same
way, into the lots of the block they lie in. The grid covers the old built ground well but not wholly: in
seven test blocks 84 % of the old standing buildings lie at least half under a lot (East Harlem 93 %,
Stapleton 70 %); irregular blocks and curved streets are where it misses.

### 2. The photographs (the five boroughs)

Every lot is scored on both mosaics by the model of `aerial_presence.py`, **unchanged and not retrained**
(same tiles, same features, same registration: the shift is found from today's footprints older than the
photograph and applied to the lots). The lots take the place of today's footprints in the picture.

A lot counts as **built at the photograph** when

1. no building of the map shares more than 0.5 m2 with it then, none starts within three years after (the
   photograph may show that building going up; assessor years run late) and none ended within two years
   before (most ends of the map are estimates), and
2. the photograph says so. The model's p is calibrated for even odds beforehand; what the photograph shows
   around a lot says more. The odds beforehand are taken from the other **free** lots within 30 m:
   prior = (built + 1.25) / (built + open + 0.5 x no call + 2.5), held within 0.2-0.85, where built / open are
   the clear calls (p >= 0.8 / 0.7 in 1924 / 1951; p <= 0.2 / 0.1). Lots under map buildings say nothing
   (where the map is complete, the free lots between its buildings are the gardens). The lot is kept when
   the odds after its own score reach the model's documented threshold (0.8 for 1924, 0.7 for 1951). With no
   free lot around that is exactly the model's own rule; in a row the photograph shows built an inconclusive
   score (p from about 0.4) is taken as built; among open ground a lot needs p >= 0.94. On Staten Island,
   where the model's own notes call its "stood" unproven, odds of 0.9 are asked, and
3. it is not open country: the lot lies in built-up ground of a snapshot (`data/manual/extents`), or three
   buildings of the map stand within 75 m at that time. Where neither holds the photograph alone is not
   believed (trees and gardens read as roofs).

A clear "open" (p <= 0.2 in 1924, <= 0.1 in 1951) is respected: nothing is generated there for that year.
A lot without a call either way gets nothing. Lots the cached mosaic tiles do not cover get nothing
(133,000 free lots: the aerial part fetched only the tiles within 25 m of a footprint of today).

A building of the map much smaller than the lot (under 30 m2 and under 35 % of the lot: a shed, a shanty of
an early atlas whose end is only estimated) does not take the lot: the row is cut around it (0.3 m clear)
and dropped if less than 55 % is left.

### 3. Years

- **Start.** Never after the evidence (the first photograph, sheet or snapshot that shows the spot built on,
  less a year). Spread back over the *recorded* years of the buildings around: one of the up to 24 nearest
  buildings within 300 m with a recorded (`exact`) year inside the allowed window, picked by hash (the
  nearest with any non-generated year where nothing is recorded; the 30 years before the evidence where
  nothing is dated at all), +/- 1.5 years (the recorded years leave out the placeholder years). The window
  opens when the last map building on the lot ended and when the last built-up snapshot that leaves the lot
  out was made; a lot that the 1924 photograph shows open and the 1951 photograph built starts between the
  two. Nothing before its ground (`ground_rule.earliest_start`); nothing before 1626.
- **End.** The first of: a clearance record (housing authority, park, motorway — table above) that falls
  after the last evidence showing the row and before the map's next building on the spot; the map's next
  building on the spot; "open in 1951"; an estimate. A row seen in 1951 does not end before 1952.
- Two rows of one lot (an early predecessor from an extent, a later one from a photograph) never stand at once.
- Last guard, on the rows as written: a row that shares more than 0.4 m2 with a map building or with another
  row while both stand is dropped (573 in the last run).

### 4. Extents (before the photographs)

`data/manual/extents` (the boroughs, 1660-1897) and `hudson_builtup_1897.geojson` are generalised: they say a
block front was built, not a lot. They are used in two ways, both for a **share** of the lots only:

- a photographed (or, in Hudson County, sheet-read) lot inside built-up ground of a snapshot: the row
  starts before that snapshot;
- a lot inside built-up ground of a snapshot, free of map buildings then (and for a year before), on which
  the map's own building dates from more than five years after the snapshot and before the first lot-level
  evidence (1927 in the boroughs, 1948 in Hudson County): a predecessor until that building went up.

The share is **measured at every run** where a traced atlas shows what really stood
(`data/manual/atlas/*_coverage.geojson`): of the lots inside a built-up extent (snapshot within ten years of
the atlas) whose map building is later than the atlas, the share that carried a building in the atlas.
Last run, 101,959 such lots under 17 atlas layers: Manhattan 0.579, Bronx 0.265, Brooklyn 0.250, Queens
0.144; Staten Island and Hudson County (no atlas of the 1890s traced) take all layers together, 0.276
(`data/interim/gapfill/extent_keep.json`). Which lots are kept is by hash. The share differs a great deal
within a borough (Kings County's towns 0.11, Williamsburg 0.59), and one number per borough does not
follow that.

### 5. Hudson County

No aerial model. Evidence:

- **The USGS sheets of the 1940s**, lot by lot: *Jersey City, N.J.-N.Y.*, 1:24,000, edition of 1947
  (photographs of 1940) and *Weehawken, N.J.-N.Y.*, 1:25,000, edition of 1943 (surveyed 1933) draw every
  built block front as a heavy black band and large buildings as black blocks
  (https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/NJ/NJ_Jersey%20City_254499_1947_24000_geo.tif ,
  https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/NJ/NJ_Weehawken_255029_1943_25000_geo.tif ;
  USGS Historical Topographic Map Collection, public domain; the copies of the piers part). The later
  editions (Weehawken 1947, both of 1955) replace the bands by a flat tint and were not used.
  Reading: black ink (luminance < 115, neutral) opened by two pixels (letters, hachures and rails are
  thinner), grown by 5 m (the sheets draw streets wider than they are); a lot is built when 70 % of it is
  ink and at least two lots or buildings within 30 m are built too. Taken as the state of 1941; a lot is
  free when no map building stands on it then, none starts before 1948 and none ended after 1939.
  Registration: the scans are on the datum of 1927 and their drawing is off by up to 35 m in places. Per
  z14 block the shift (within 40 m) that puts most heavy ink under the map's buildings older than 1935 and
  least on today's street lines; a block more than 20 m from its sheet's median shift (5 m east, 16 m south
  for Jersey City; 9 m west, 25 m south for Weehawken) is read with the median; a block without a clear
  answer in the first pass is not read.
  How sure: of 3,795 lots that lie under a map building recorded by 1935, the sheets show 2,492 (66 %) as
  built. How often they show open ground as built is not measured (no set of lots known to be open).
- **The USGS 15-minute sheets of 1898** (`hudson_builtup_1897.geojson`), used as the boroughs' extents.

This is weaker than the photographs: block fronts, not lots; a lot can be off by one; solid black blocks
(factories, sheds) get lot rows along their frontages only, drawn as houses. West of 74°07.5' W (Kearny,
Harrison, East Newark, the western edge of Bayonne) no 1940s sheet was read: only the 1898 extent speaks.

**New Jersey's 1930 aerial mosaic** is reachable (WMS `https://img.nj.gov/imagerywms/BlackWhite1930`, layer
`BlackWhite1930`, NJ Office of GIS, access constraints "none"; EPSG:3857 and others; 6.5 ft pixels; place
names are printed across the photographs). One 512 px picture over Hoboken was fetched to look at; it was
**not used**: the presence model was built on 0.9 m scans and has no validation on a 2 m mosaic with
lettering. A block-level reading (built / open) of it would be the next piece of evidence for the county.

## What the fill rests on, by period

| period | the boroughs | Hudson County |
|---|---|---|
| before 1889 / 1897 | start years only: spread back from later evidence over the recorded years around; the extents place a share of the starts before their snapshot. No row exists without later evidence | the same, from the 1898 sheets |
| 1889 / 1897 - 1924 | built-up extents (generalised; a measured share of the lots) for lots whose map building is later; rows of the photographs that started earlier | 1898 extent likewise, to 1941 |
| 1924 - 1951 | the two photographs, lot by lot | the 1940s sheets, block front by block front |
| 1951 - 1996 | nothing shows a building standing after 1951: the end is a clearance record, the year of the building that took the spot, or an estimate (1956-1984) | the year of the building that took the spot, or an estimate |
| after 1996 | no rows (the city's record of removals takes over) | rows may run to the year of today's building (5,978 rows stand in 2000) |

## Limits (see `numbers.md` for the figures)

- **Thinner than the districts were.** On lots under map buildings known to be older than the photograph the
  rule calls 74 % built (4 % / 2 % open); a quarter of what stood is not found. 244,000 free lots of 1924
  and 239,000 of 1951 got no call and no row.
- **Not all rows stood.** On lots in parks older than the photograph (trees: the worst case) the rule calls
  13 % built; the model's own validation gives 2-6 % on open ground and streets, 10-20 % in dense blocks.
  With 630,000 free lots called open in 1924, false rows are expected in the thousands; they concentrate
  where houses stand among trees and gardens. In the one suburban view looked at (Ozone Park, 1924) ten rows
  had been added among some 500 houses of the map and the largest group of them (seven) lies on what looks
  like a wooded lot. In the dense districts looked at (Lincoln Square, Melrose, Brownsville) the rows lie
  on the roofs of the photograph.
- A standing building with a placeholder year a few years after a photograph that shows a building on its
  lot may be that very building (the pipeline moves such years only outside dense blocks). The fill then
  draws a generic building until the standing one "starts": 13,864 of the 85,411 photograph rows end under
  a standing building whose year is an estimate within 15 years after the photograph. `rows/*.parquet`
  carries `next_exact`, `next_start`, `t_ev` for them.
- `extent<year>` and `usgs1897_builtup` rows (40,648) rest on a block-level map and a measured share: which
  lots of a block had a predecessor is by hash.
- Lot lines are not real: the grid is laid by rule on today's blocks. In superblocks the closed streets are
  reconstructed by rule (a lot can lie on a street that the photograph shows — the photograph usually
  rejects it, not always).
- Waterfront ground outside the street grid, piers, rail yards (lots within 6 m of today's surface tracks are
  dropped) get nothing.
- Between 1951 and 1996 no source shows what stood; ends in that period are records or estimates.
- The census check is an upper check only and binds nowhere (persons per building after the fill: Manhattan
  21.6, Bronx 13.2, Brooklyn 7.9, Queens 3.8, Staten Island 3.1, Hudson 7.5 in 1950 — the map counts
  garages and sheds as buildings, so the low figures are the map's own).

## Running

```
cd pipeline
../.venv/bin/python gap_fill.py            # snapshot, lots, ink, assemble, report
../.venv/bin/python gap_fill.py fresh assemble report   # after a rebuild of the buildings (new atlas layers): new snapshot, same lots
../.venv/bin/python gap_fill.py look <lon> <lat> <name> # thumbnails of both photographs (and the 1940s sheet) with the lots
```

- `lots` is the long step: 355 z14 blocks, 2.0 million lots, each block cut and scored on two mosaics. Run
  here in 25 minutes by six processes (`lots`: three; `lots-reverse`: two from the other end of the list;
  `lots-middle [seconds]`: one from the middle) on the loaded four-core build machine, each under 1 GB. It is
  cached (`lots_v3/`) and need not be repeated when the map changes: the lots depend on the streets and on
  the old standing buildings only. A change of the cutting rules needs `LAYOUT` raised in the script.
- `snapshot` 10 s, `ink` 40 s, `assemble` 2.5 minutes (three processes under 1 GB; the calibration of the
  extents first), `report` 1 minute.
- `assemble` must be rerun after every rebuild that adds or re-dates buildings, or the fill will overlap
  them. The snapshot leaves out rows whose `year_src` starts with `gapfill`, so the stage can read a
  building file that already holds its own rows.

## The counties beyond Hudson (`gap_fill.py counties`, added 2026-11-11)

Essex, Union, Passaic, Bergen, Westchester and Rockland have today's buildings with parcel years and
nothing vanished. Rows are generated on the states' real parcels, not on a lot grid; the rules are in
the comment block above `COUNTIES` in `pipeline/gap_fill.py`:

- `parcel_neighbourhood`: the Bay project's rule — the parcel's neighbourhood was built up before 1945
  (25th percentile of the recorded years of the buildings within 150 m, at least eight), its own
  building is 25 or more years younger, and six in ten recorded neighbours are older than it by 20
  years: an earlier building stood from the neighbourhood's development until today's replaced it.
- `usgs<year>_blocks` / `usgs<year>_tint`: the parcel lies on the built block fronts, or in the urban
  tint, of a 1940s USGS sheet and its own building is later.
- `usgs1897_builtup`: the parcel lies in built-up ground of the 1897-98 sheets and its own building
  is later (a share; alone only where the gap closes by 1948).

71,321 rows; counts per county and evidence, the census check and the overlap checks are in
`numbers_counties.md`. Output `data/interim/gapfill/gapfill_counties.parquet` (the loader reads every
`gapfill*.parquet`). Not rerun by the city's `fresh assemble`: `gap_fill.py counties` after a change
to the counties' buildings. All rows `procedural`; no hand-checked precision figure.

## Inside the yards, forts and institutions (`pipeline/site_fill.py`, added 2026-11-11)

The lot fill needs street frontages; a navy yard, a fort, an island of hospitals or a works has none,
and no fire-insurance atlas mapped federal and city grounds. `site_fill.py` reads roofs off the two
aerial photographs inside the grounds of `data/manual/sites/sites.geojson` (96 grounds; landfills and
quarries left out; successive sites on one outline are one ground):

1. Each photograph is segmented (Felzenszwalb, three scales). A patch of 60-20,000 m² that fills 70 %
   of its bounding rectangle, at least 5 m wide, is a candidate roof, drawn as that rectangle and
   moved by the photograph's measured shift against the map.
2. The presence model (`aerial_presence.py`, unchanged) scores each candidate on its photograph; kept
   at the lot fill's thresholds (0.8 for 1924, 0.7 for 1951, Staten Island 0.9), only where the map
   has no building on more than 30 % of it at the time, not on today's water, not on today's surface
   tracks (rolling stock), not larger than 2,500 m² in a fort or an institution (parade grounds,
   courts), and only while the site existed. Of overlapping candidates the best-scored stays; kept
   roofs that touch are one building.
3. Years: a roof of 1924 starts before the photograph, spread back over 60 years (a third over the
   recorded years of the site's own buildings where it has five), not before the site's founding; a
   roof found only in 1951 that the 1924 photograph does not show starts in between. Ends: when the
   map's next building on the spot went up, 1926-1950 where the 1951 photograph no longer shows it,
   with the site where it closed, else 1956-1984. Heights by the kind of site (a shed over 2,500 m²:
   10-16 m).

Result (2026-11-11): 2,192 buildings in 72 sites; standing 208 in 1880, 535 in 1900, 1,213 in 1925,
1,440 in 1950. The largest: Bush Terminal, Fort Tilden, Blackwell's Island, the Standard Oil works on
Newtown Creek, Fort Totten, the Navy Yard, Fort Hamilton. `procedural`, evidence
`site+aerial1924`, `site+aerial1951`, `site+aerial1924+1951`.

Checked by eye only (`site_fill.py look site=<id>` draws the outlines on both photographs): the Navy
Yard (outlines sit on roofs; perhaps half of the roofs in the picture are found) and Fort Hamilton
(mostly on buildings; one parade ground was outlined before the size limit was added). No precision
figure. Known failure modes: a paved court or lawn of roof size; a ship at a quay inside a site's
outline; a roof split along its ridge into two rectangles that did not join.

## Cleared blocks (`gap_fill.py counties`, added 2026-11-11, second pass)

The owner: "areas that have been destroyed and rebuilt (Springfield/Belmont, Newark) must appear before they were
destroyed". The county rules above keep a share of the parcels under the 1897 and 1940s evidence and need old recorded
buildings around; a district that was cleared in 1955-80 and rebuilt after 1990 has neither (Newark's Central Ward held
2,649 standing buildings in 1950, its survivors three to four times that per hectare). New rule, evidence
`cleared_block+<sheet>` (rules in the comment above `cleared_districts()` in `pipeline/gap_fill.py`):

- **Block** = the polygon between today's street centre lines (the stage's `city_blocks`, at most 40 ha).
- (b) fewer than a third of today's buildings on it date from before 1945 (any year, recorded or not); and
  (c) it lies inside one of the 14 researched districts (`cleared_districts.geojson`: name, county, clearance years,
  source URL, density factor) OR at least three buildings stand on it and 60 % of them have a recorded (exact, parcel)
  year after 1950; and
  (a) ground: the block's lots rest on the built-up ground of the 1897-98 sheets or on built block fronts of a 1940s sheet
  (at least half of the lots), inside a district also on the 1940s urban tint (at least 30 % of the lots). Without it, no row:
  rule (c) alone is never proof that the block was built.
- **Lots**: today's parcels where they are lot-sized (`parcel_outline`, 40-1,500 m2), else the street-frontage rows of
  `make_lots` (the city's lot cutter, sized by the old buildings of the nearest block that has five) where a parcel is
  larger or none exists (closed streets, highway land). Every position gets a building (no share), then a district's
  `density_factor` thins it (below).
- **Years**: start from the recorded years of the buildings within 800 m (not 300 m), at most 1897 where the 1897 sheet shows
  the block built (else the census distribution of the county's people up to 1897, nearer old centres earlier), at most 1944
  where only a 1940s sheet does; end at the district's clearance years (uniform between them) or when today's building on
  the spot went up (two years of lead), whichever is earlier; rows with no building today end 1956-84 outside a district.
  Highway rows end at the motorway's opening year as before. Never on a map building while both stand (final guard), never
  before the ground (`ground_rule`), never on a street, on water or on a railway. These rows win an overlap with older rules' rows.
- **Density factor** (`density_factor` of each district, 0.48-1.0): a district's frontage rows are full lots; the surviving old
  blocks nearby (the reference: at least 8 buildings, 70 % dated before 1930, same town, within 1 km) are less dense than that
  (industry, yards, a few detached houses), so each district keeps the share of lot positions at which map + fill reaches 100 %
  of the reference density, the mean of its 1925 and 1950 values (the calibration is the owner's 60-110 % band, not a measured
  truth); 1.0 where the evidence rules, not the factor, limit the density. Outside the researched districts no thinning.
- **Districts** are bounding polygons drawn by the stage's author from the street grid and today's building years (approximate and
  generous: blocks that still hold old buildings fail rule (b) and are not touched). Clearance years and source URLs are the
  author's reading of the pages named in the file and were not re-checked online in this round: estimated.
- `GAPFILL_CB=0` runs the stage without the rule (the "before" of the report).

Housekeeping: the 1940s sheets of Elizabeth, Weehawken, Yonkers, Mount Vernon and Central Park (formerly read from the piers part's
folder, now gone) were fetched again into `data/raw/gapfill/usgs/` (USGS, public domain), and the stage reads them from there;
`SHEET_SHIFT_FALLBACK` holds the first run's registration for them.

Result and checks: `numbers_counties.md` ("Cleared districts"). 110,054 rows (91,933 without the rule), of them 25,165 cleared-block rows
(Essex 11,642, Westchester 4,788, Passaic 5,333, Bergen 2,491, Union 911). 9,604 blocks are candidates of (b) and (c); 914 pass (a).
Invariants as before, all 0: overlaps in time with map buildings and with other rows, rows on streets or water, start >= end.
Not met: Hackensack (64 % / 49 % of the reference in 1925 / 1950), Passaic Eastside (64 / 63), Elizabethport (73 / 69) and the Route 80 corridor
of Paterson (74 / 75) stay below or at the band's floor because most of their cleared blocks have no evidence (a) (no 1897 built-up ground,
no 1940s block-front sheet read there); five districts are 112-128 % of the reference in 1925 (the factor was fitted to the mean of 1925 and 1950),
and 1900 compares badly with the reference (the reference blocks were not yet built in 1900). Not done: the sheets of Hackensack (1940),
Orange (1947) and Paterson (1944) are read as tint or not at all, not as block fronts; no precision figure; Union and Rockland have almost no
cleared districts here (Elizabethport only).
