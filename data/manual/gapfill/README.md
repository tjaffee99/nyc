# Gap fill: generated buildings where the evidence shows built ground and the map has none

`pipeline/gap_fill.py` → `data/interim/gapfill/gapfill.parquet`. Every row is **generated** (`procedural`):
a lot-sized outline, a start, an end. None is a traced or recorded building. Each rests on a named piece
of evidence that its spot was built on at that time, and each gives way to anything real.

Why: a building put up after the last traced atlas of its district and pulled down before 1996 (when the
city's record of removed footprints starts) is in no source the map has. Hell's Kitchen's 50s, Lincoln
Square, East Harlem, the South Bronx, Brownsville, Williamsburg, Long Island City, downtown Jersey City
stood empty at 1880 / 1925 / 1950 although they were densely built.

## Files

| file | content |
|---|---|
| `README.md` | this note |
| `hudson_builtup_1897.geojson` | built-up ground of Hudson County on the USGS 15-minute sheets of 1898 (74 polygons, 3,147 ha), read with the extents part's own tool (`tools/hudson_1897.py`); same properties as `data/manual/extents/*.geojson` |
| `tools/hudson_1897.py` | makes that file |
| `numbers.md` | the checks of the last run (copied from `data/interim/gapfill/report.md`) |

Scratch (gitignored, rebuilt by the stage): `data/interim/gapfill/` — `existing.parquet` (snapshot of the map),
`lots_v2/` (the lots and their photograph scores per z14 block), `sheet_ink_v2/` (Hudson County: the 1940s
sheets read on the lots), `rows/`, `gapfill.parquet`, `stats.json`, `extent_keep.json`, `report.md`, `look/`
(thumbnails). Nothing was downloaded by this stage: it reads what the aerial, extents and piers parts fetched.

## Output

`gapfill.parquet` — GeoParquet, EPSG:4326, one Polygon per row:

| column | |
|---|---|
| `id` | `gf` + 14 hex digits: hash of the lot's centre (lon, lat to 1e-6) and of the evidence that anchors the row. Stable across runs as long as the streets and the old buildings of the block (which fix the lot grid) do not change |
| `start_year`, `end_year` | decimal years, `start < end - 1` |
| `height_m`, `storeys` | by type (below) |
| `material` | `brick` / `frame` |
| `evidence` | what says the spot was built on (table below) |
| `end_basis` | what dates the end (table below) |
| `area` | `"1"` … `"5"` (borough of the nearest building of the map) or `"Hudson"` |

`evidence`:

| code | meaning |
|---|---|
| `aerial1924` | the 1924 photograph shows a building on the lot (the model of `aerial_presence.py`) |
| `aerial1951` | the 1951 photograph does |
| `aerial1924+1951` | both do, with no building of the map on the lot in between |
| `extent<year>+aerial…` | as above, and the lot lies in ground that the built-up snapshot of `<year>` (`data/manual/extents`) shows built: the start is put before that snapshot (for the share of lots given under *Extents*) |
| `extent<year>` | no photograph can speak (the map's own building on the lot dates from before 1927): the lot lies in built-up ground of the snapshot and the map's building on it is later — a predecessor, for the share of lots given under *Extents* |
| `usgs1947_blocks`, `usgs1943_blocks` | Hudson County: the lot lies on a built block front (heavy black ink) of the USGS sheet Jersey City 1:24,000 of 1947 / Weehawken 1:25,000 of 1943 |
| `usgs1897_builtup`, `usgs1897_builtup+usgs194x_blocks` | Hudson County: as `extent<year>`, from `hudson_builtup_1897.geojson` |

`end_basis`:

| code | meaning |
|---|---|
| `replaced_by_standing` | the building that stands on the spot today went up (the row ends 1-2.5 years before its year) |
| `replaced_by_vanished` | a later building of the map, itself gone, went up on the spot |
| `nycha:<development>` | a housing authority development stands in the same city block (no street between): 2.5-4.5 years before its completion date (Development Data Book, NYC Open Data `evjd-dqpz`, through `data/interim/records/records_by_bin.parquet`) |
| `park:<name>` | the lot lies in a park property acquired later: 0.3-1.8 years after the acquisition date (Parks Properties, NYC Open Data `enfh-gkve`) |
| `highway:<name>` | the lot lies within 25 m of a motorway centre line: 1.5-3.5 years before its opening (`data/interim/roads/highway_years.csv`, the researched openings of `data/manual/routes.csv`) |
| `photo1951_open` | the 1924 photograph shows a building, the 1951 photograph open ground (p <= 0.1): a year between the two, by hash |
| `estimated` | nothing on the spot today and no record: when the nearest large building (>= 400 m2, within 60 m) went up, else a year spread over 1956-1984. In the boroughs a row never ends after 1995: a building standing in 1996 would be in the city's record of removals, and then the map would have it |

## Method

### 1. Lots (candidates, not buildings)

- **City blocks**: the polygons between today's street centre lines (Overture / OpenStreetMap, classes
  residential … trunk; motorways and tunnels are not streets). Blocks under 600 m2 or over 150 ha are left out.
  Ground not enclosed by streets (waterfront strips beyond the last street) gets no lots.
- **Building line**: the block polygon shrunk by the distance at which the block's old buildings (standing,
  built by 1935) stand from the centre lines (15th percentile, 6.5-14 m; 9.2 m — half a 60 ft street —
  where fewer than five old buildings stand).
- **Bearing**: the block's own — the long side of its minimum rotated rectangle.
- **Rows**: lots face the two long frontages. A block deeper than one city block (a superblock whose streets
  were closed: housing projects, Lincoln Center) is cut as *k* blocks, *k* = round((depth + 18.3 m) / 79.2 m),
  with an 18.3 m street between them — the old grid, reconstructed by rule, not from a map.
- **Size of an outline**: measured, not assumed — the median width and depth of the old buildings of the same
  block (of the nearest block that has five, where it has none), within 4.8-8.5 m by 9.5-27 m; depth varies
  0.88-1.12 by hash; detached types stand 1.5 m apart. Type from the median roof height of the block's old
  buildings: under 9 m `frame` (2-3 storeys, frame), 9-13.5 m `rowhouse` (2-4, brick), above `tenement`
  (4-6, brick). Height = storeys x 3.3 m + 1 m (frame: x 3.0 + 1.5).
- **Not a lot**: an outline within 6-14 m of a street centre line (by class), on today's water, in a cemetery;
  an outline that leaves the building-line polygon by more than 0.6 m.

A standing building's footprint is never copied: a large modern footprint and open ground are cut the same
way, into the lots of the block they lie in.

### 2. The photographs (the five boroughs)

Every lot is scored on both mosaics by the model of `aerial_presence.py`, **unchanged and not retrained**
(same tiles, same features, same registration: the shift is found from today's footprints older than the
photograph and applied to the lots). The lots take the place of today's footprints in the picture.

A lot counts as **built at the photograph** when

1. no building of the map shares more than 0.5 m2 with it then, nor one that starts within three years
   after (the photograph may show that building going up; assessor years run late), and
2. the photograph says so. The model's p is calibrated for even odds beforehand; what stands around a lot
   says more. The odds beforehand are taken from the lots within 30 m whose state is clear (a map building
   on them, or a clear call of the photograph: p >= 0.8 / 0.7 built, p <= 0.2 / 0.1 open):
   prior = (built + 0.5) / (built + open + 2.5), held within 0.2-0.85. The lot is kept when the odds after its
   own score reach the model's documented threshold (0.8 for 1924, 0.7 for 1951). With even odds that is
   exactly the README's rule; in a row the photograph shows built an inconclusive score (p from about 0.4)
   is taken as built; a lot alone among open ground needs p >= 0.94.

A clear "open" (p <= 0.2 in 1924, <= 0.1 in 1951) is respected: nothing is generated there for that year.
A lot without a call either way gets nothing. Lots the mosaics do not cover get nothing.

A building of the map much smaller than the lot (under 30 m2 and under 35 % of the lot: a shed, a shanty of
an early atlas whose end is only estimated) does not take the lot: the row is cut around it (0.3 m clear)
and dropped if less than 55 % is left.

### 3. Years

- **Start.** Never after the evidence (the first photograph, sheet or snapshot that shows the spot built on,
  less a year). Spread back over the *recorded* years of the buildings around: one of the up to 24 nearest
  buildings within 300 m with a recorded (`exact`) year inside the allowed window, picked by hash (the
  nearest with any non-generated year where nothing is recorded; the 30 years before the evidence where
  nothing is dated at all), +/- half a year. The window opens when the last map building on the lot ended and
  when the last built-up snapshot that leaves the lot out was made; a lot that the 1924 photograph shows
  open and the 1951 photograph built starts between the two. Nothing before its ground
  (`ground_rule.earliest_start`); nothing before 1626.
- **End.** The first of: a clearance record (housing authority, park, motorway — table above) that falls
  after the last evidence showing the row and before the map's next building on the spot; the map's next
  building on the spot; "open in 1951"; an estimate. A row seen in 1951 does not end before 1952.
- Two rows of one lot (an early predecessor from an extent, a later one from a photograph) never stand at once.

### 4. Extents (before the photographs)

`data/manual/extents` (the boroughs, 1660-1897) and `hudson_builtup_1897.geojson` are generalised: they say a
block front was built, not a lot. They are used in two ways, both for a **share** of the lots only:

- a photographed lot inside built-up ground of a snapshot: the row starts before that snapshot;
- a lot inside built-up ground of a snapshot, free of map buildings then, on which the map's own building
  dates from more than five years after the snapshot and before the first lot-level evidence (1924
  photograph; 1941 in Hudson County): a predecessor until that building went up.

The share is **measured at every run** where a traced atlas shows what really stood
(`data/manual/atlas/*_coverage.geojson`): of the lots inside a built-up extent (snapshot within ten years of
the atlas) whose map building is later than the atlas, the share that carried a building in the atlas
(`data/interim/gapfill/extent_keep.json`; 0.5 if fewer than 300 lots can be judged). Which lots are kept is
by hash.

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
  thinner), grown by 5 m (the sheets draw streets wider than they are); a lot is built when half of it is
  ink and at least two lots or buildings within 30 m are built too. Taken as the state of 1941; a lot is
  free when no map building stands on it then nor starts before 1948.
  Registration: the scans are on the datum of 1927 and their drawing is off by up to 35 m in places. Per
  z14 block the shift (within 40 m) that puts most heavy ink under the map's buildings older than 1935 and
  least on today's street lines; a block without a clear answer is not read.
- **The USGS 15-minute sheets of 1898** (`hudson_builtup_1897.geojson`), used as the boroughs' extents.

This is weaker than the photographs: block fronts, not lots; a lot can be off by one; solid black blocks
(factories, sheds) get lot rows along their frontages only. West of 74°07.5' W (Kearny, Harrison, East
Newark, the western edge of Bayonne) no 1940s sheet was read: only the 1898 extent speaks there.

**New Jersey's 1930 aerial mosaic** is reachable (WMS `https://img.nj.gov/imagerywms/BlackWhite1930`, layer
`BlackWhite1930`, NJ Office of GIS, access constraints "none"; EPSG:3857 and others; 6.5 ft pixels; place
names are printed across the photographs). It was looked at over Hoboken and **not used**: the presence
model was built on 0.9 m scans and has no validation on a 2 m mosaic with lettering. A block-level reading
(built / open) of it would be the next piece of evidence for the county.

## What the fill rests on, by period

| period | the boroughs | Hudson County |
|---|---|---|
| before 1889 / 1897 | start years only: spread back from later evidence over the recorded years around; the extents place a share of the starts before their snapshot. No row exists without later evidence | the same, from the 1898 sheets |
| 1889 / 1897 - 1924 | built-up extents (generalised; a measured share of the lots) for lots whose map building is later; rows of the photographs that started earlier | 1898 extent likewise, to 1941 |
| 1924 - 1951 | the two photographs, lot by lot | the 1940s sheets, block front by block front |
| 1951 - 1996 | nothing shows a building standing after 1951: the end is a clearance record, the year of the building that took the spot, or an estimate (1956-1984) | the year of the building that took the spot, or an estimate |
| after 1996 | no rows (the city's record of removals takes over) | rows may run to the year of today's building |

## Limits

- The model is right about 94-96 % of the time on real footprints at its thresholds and finds 60-70 % of what
  stood; on lot outlines it finds less (see `numbers.md`: lots under buildings known to be older than the
  photograph). The fill is therefore **thinner than the districts were**. It is not thinned further: the
  census check in `numbers.md` is an upper check only.
- Dense blocks: streets and yards in shadow read as buildings in 10-20 % of cases (the model's own
  validation); with built neighbours such a lot is kept. Yards inside built rows are over-filled, isolated
  buildings in open ground under-filled.
- A standing building with a placeholder year a few years after a photograph that shows a building on its
  lot may be that very building (the pipeline moves such years only outside dense blocks). The fill then
  draws a generic building until the standing one "starts". `numbers.md` gives the count.
- Lot lines are not real: the grid is laid by rule on today's blocks. In superblocks the closed streets are
  reconstructed by rule (lots can lie on a street that the photograph shows — the photograph then usually
  rejects them, not always).
- Waterfront ground outside the street grid, piers, rail yards (lots within 6 m of today's surface tracks are
  dropped) get nothing.
- Between 1951 and 1996 no source shows what stood; ends in that period are records or estimates.
- Staten Island and open country: the model is weak there (its README); few rows.

## Running

```
cd pipeline
../.venv/bin/python gap_fill.py            # snapshot, lots, ink, assemble, report
../.venv/bin/python gap_fill.py fresh assemble report   # after a rebuild of the buildings (new atlas layers): new snapshot, same lots
../.venv/bin/python gap_fill.py look <lon> <lat> <name> # thumbnails of both photographs (and the 1940s sheet) with the lots
```

`lots` is the long step: about 355 z14 blocks, 15-30 s each on a free core (cut the lots, score them on two
mosaics); 3 processes of under 1 GB; `lots-reverse` adds two from the other end of the list. It is cached
(`lots_v2/`) and need not be repeated when the map changes: the lots depend on the streets and on the old
standing buildings only. A change of the cutting rules needs `LAYOUT` raised in the script. `assemble`
(a few minutes, 3 processes under 1 GB) reads the snapshot of the map and writes the rows; it must be rerun
after every rebuild that adds buildings, or the fill will overlap them. `report` recomputes the invariants
from the written rows.
