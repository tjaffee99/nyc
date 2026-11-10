# Buildings on the USGS sheets of 1888-89 and 1897

Every building that the first USGS topographic sheets of New York draw as a **separate
black mark**, in all five boroughs: farmhouses, village houses, hotels, institutions. Built by
`pipeline/topo_farmsteads.py` (`python topo_farmsteads.py all`; tools in `tools/`).
Sources: USGS Historical Topographic Map Collection, public domain
(https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/PDF/…, catalogue
https://tnmaccess.nationalmap.gov/api/v1/products?datasets=Historical%20Topographic%20Maps&bbox=-74.27,40.48,-73.69,40.93);
NADCON grid `us_noaa_conus.tif` (https://cdn.proj.org, open licence); today's streets and
footprints from the project's own extracts. The readings are this project's (CC0).

**What it is good for, in one paragraph.** 8,864 buildings that stood in 1889 and / or 1897
where the map today shows nothing before the 1920s; 1,358 of them with a year by which they
were gone. Measured precision 0.93 (216 hand-checked marks), recall about 0.65 of the marks
drawn separately; village cores drawn as touching rows or black frontages are **not** read.
It does **not** prove individual standing buildings older than their assessor year: a mark is
good to 15-25 m, and in today's fabric a point that close to a footprint is no evidence
(tested against the same marks moved off their spots, below).

## Files

| File | What |
|---|---|
| `farmsteads.geojson` | 8,864 points (WGS84), one per building mark |
| `coverage.geojson` | the seven 15-minute sheets: neat line, print and survey year, collar text, shift |
| `stats.json` | every count quoted here (rewritten by the export) |
| `tools/` | `look.py` (a window of a sheet with detections and today's roads), `try_window.py` (detector on one window), `contact.py` / `contact_export.py` (contact sheets for the precision check), `crop.py` (GeoTIFF crop), `standing_check.py` (footprint matches against chance), `districts.py` (table of the old villages) |

### Properties of a point

| Property | Meaning |
|---|---|
| `id` | `<quad><survey yy>_<page x>_<page y>` of its first detection (`bk` Brooklyn, `ha` Harlem, `si` Staten Island, `he` Hempstead, `ob` Oyster Bay) |
| `first_year` | survey year of the first edition that shows it: 1889 or 1897. **An upper bound of its construction** ("standing by") |
| `last_year` | survey year of the last 15-minute edition that shows it as a separate mark |
| `gone_by` | 1897: the 1897 revision covers the spot and has no solid ink within 40 m. 1947 / 1955 / 1956 / 1957: the first 1:24,000 edition with nothing within 45 m (no building symbol, no black mass within 30 m, no built-up tint). `null`: no later sheet says so. An upper bound ("gone by"), estimated: see "gone_by" below |
| `new_since` | 1889 where the 1888-89 survey covers the spot and is blank within 40 m: built between the two surveys |
| `kind` | `house` (a single mark; the sheets do not tell house from barn) or `large` (a bar 40-120 m long: long barn, row, hotel, factory). No `church` / `barn_cluster`: the crosses of churches are below the scan's resolution |
| `mark_m` | length of the mark's solid core on the ground (a house mark is 15-30 m whatever the house; for `large` it is about the building's length) |
| `site`, `n_marks` | marks within 60 m of each other share a `site`; `n_marks` = marks of the site (house + barns) |
| `sheet` | sheet ids that show it, e.g. `brooklyn_1889+brooklyn_1897` |
| `confidence` | `high` (on both surveys, or a recorded old building stands there) 1,362; `medium` (one survey, clean mark) 5,970; `low` (`large`, `in_row`, on marsh, or inside the built-up extent of its edition) 1,532 |
| `borough` | Manhattan 262, Bronx 1,633, Brooklyn 2,010, Queens 3,455, Staten Island 1,504 |
| `standing_bin` … | today's footprint within 25 m that could be the building (below) |
| `late_symbol` | later 1:24,000 editions (`1947`, `1947+1955` …) with a building symbol within 45 m and no black mass: something still stood on the spot, not necessarily the same building |
| `earlier_unclear` / `later_unclear` | the other survey has solid ink within 40 m that is not a separate mark (a frontage, a row, lettering): "not shown" cannot be said |
| `builtup` | inside the built-up extent of the same edition (`data/manual/extents/<borough>_1889 / _1897`) |
| `in_row` | one of a touching row of houses, taken back after the detector's first refusal (397 points) |
| `ground` | ground of the survey year if not dry land: `tidal_marsh` 246, `shore` 103 (water cell with land beside it), `wetland` 24, `tidal_flat` 2 |

`standing_*`: `standing_bin` (BIN), `standing_basis` — `recorded` (a recorded or LPC year no
later than `first_year`: 99), `by_then` (an estimated year no later than it, or a "by 1901"
placeholder: 754), `later_estimate` (an estimated year after the survey: 4,796) —
`standing_strength` (`strong` only for `recorded`, and for `by_then` within 12 m in open
ground, i.e. at most 6 footprints within 60 m: 19 rows), `standing_year`, `standing_year_src`
(the built model's), `standing_dist_m` (0 = the point is inside the footprint), `standing_n`
(footprints of the same basis within 25 m), `standing_n60` (footprints within 60 m),
`standing_area_m2`. A footprint with a recorded year after the survey is never offered; one
the model has itself dated from this file (`evidence_by:topo1889 / topo1897`) is classed by
its assessor year. Counts are for the model build of 2026-11-10 18:24; **3,215 marks have no
such footprint. `standing_bin` is a candidate, not a finding — see "Footprints under the
marks against chance".**

## Sheets

Survey years were **read off the collars** (rendered at 200 dpi, `data/interim/farmsteads/collar_*.png`).
The catalogue's "survey year" is 1889 for the first prints and 1897 for all later ones.

| id | Quadrangle | Print | HTMC scan | Collar | Year used | Marks kept on the sheet | Features in the file | Shift onto today's streets (m) | Local shifts (m) | Windows | RMS, m (one window left out) | RMS if one constant shift |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `brooklyn_1889` | Brooklyn | 1889 | 8033200 | Surveyed in 1888-89 | **1889** | 2,021 | 2,023 | +9 E, -38 N | -19..+45 E, -74..-3 N | 66 | 12.5 | 21.1 |
| `brooklyn_1897` | Brooklyn | 1898 | 139309 | Surveyed in 1888-89 and 1897 | **1897** | 2,642 | 2,750 | +9 E, -43 N | -23..+41 E, -79..-18 N | 72 | 12.8 | 20.5 |
| `harlem_1889` | Harlem | 1891 | 472515 | Surveyed in 1888-89 | **1889** | 3,616 | 1,582 | -22 E, -50 N | -60..+117 E, -112..+41 N | 98 | 14.2 | 28.0 |
| `harlem_1897` | Harlem | 1898 | 139657 | Surveyed in 1888-89 and 1897 | **1897** | 3,935 | 1,768 | -12 E, -45 N | -54..+111 E, -107..+4 N | 80 | 16.1 | 29.8 |
| `staten_island_1897` | Staten Island | 1898 | 255388 | Surveyed in 1888-89 and 1897 | **1897** | 3,262 | 1,744 | -3 E, -16 N | -52..+35 E, -55..+118 N | 72 | 18.5 | 24.2 |
| `hempstead_1897` | Hempstead | 1897 (imprint 1961) | 129886 | cut off on this scan; "Surveyed in 1897" on the 1903 print (139678) | **1897** | 2,476 | 226 | -19 E, -31 N | -85..+30 E, -86..+57 N | 64 | 21.7 | 25.4 |
| `oyster_bay_1897` | Oyster Bay | 1897 (imprint 1963) | 136363 | cut off on both scans fetched (136363, 148122); catalogue: 1897 — **not verified** | **1897** | 1,934 | 44 | +24 E, +13 N | -28..+102 E, -76..+80 N | 87 | 16.4 | 28.6 |

* "Marks kept on the sheet" includes New Jersey, Westchester and Nassau: 9,337 marks outside
  the five boroughs stay in the caches (`data/interim/farmsteads/sheets/<id>.json`), not in the file.
* **Not used.** The 1900 editions of Brooklyn (139311), Harlem (139658) and Staten Island
  (255389): their collars carry the same statement as the 1898 prints ("Surveyed in 1888-89 and
  1897"), so they are reprints of the 1897 state; they were not compared mark by mark.
  Paterson (surveyed 1887, 1889, 1897): west of 74°00′ it holds New Jersey and Manhattan's
  Hudson piers. **No 1891 Staten Island sheet exists in the collection** (the first print is
  1898), so Staten Island and Brooklyn west of 74°00′ (Bay Ridge, Fort Hamilton, Red Hook) have
  one state only, 1897; so has Queens east of 73°45′ (Hempstead, Oyster Bay).
* A mark first read on the 1897 state may be older than the 1888-89 survey where that
  survey shows a frontage or lettering on the spot (`earlier_unclear`: 1,312 points) and
  everywhere on the one-state sheets. `new_since` = 1889 (1,933 points) is the firm case.

### Registration and offsets

The GeoPDF's own registration (CTM, NAD27 polyconic) is exact on the neat line; NAD27 → WGS84
through NADCON moves the sheet 35 m east and 12 m north here. What remains is the survey's own
error and the paper: the sheet's thin ink (road casings) is cross-correlated with today's
road centrelines (Overture) in 2.5 km windows (± 127 m); a window counts where two neighbours
found the same shift within 21 m; the shifts are smoothed over 1.5 km and applied locally
(`shift.field` in the cache; the sheet's overall shift beyond 4 km from any window).
**One constant per sheet is not enough**: the Harlem sheets vary from 60 m west to 110 m
east and from 110 m south to level across the sheet (RMS 28-30 m with a constant, 14-16 m with
the field). The earlier agents' constants (Harlem 58 W / 74 S, Brooklyn 42 W / 16 S, Staten
Island 48 W / 69 N; `data/manual/natural/usgs_sheets.json`) were measured on the GeoTIFFs
against the shoreline without NADCON and are not comparable; they were not reused. The
extents agent's finding that street matching does not converge holds for Manhattan's grid
(shifts there may be one block off; no marks are read there).
Checked by eye with today's roads drawn over the sheet (`tools/look.py --roads`): Gravesend,
Jamaica, Richmondtown, Westchester Square — old roads that survive sit within about 10 m.

### The later sheets (for `gone_by` only)

1:24,000, rendered at 300 dpi (2 m per pixel), registered the same way (their own shifts are
1-17 m). The 1947 editions were compiled from aerial photographs of 1940-42 and print built
blocks as black masses; the 1955-57 editions (photographs 1953-57, field checks 1955-57) print a
pink built-up tint inside which only landmark buildings are drawn. Columns: points of the file
on the sheet; with a building symbol within 45 m; unclear (black mass within 30 m, or tint);
blank; `gone_by` set from this sheet.

| id | Quadrangle | Edition | Photographs | Field check | HTMC scan | Shift (m) | RMS | Points | Symbol | Unclear | Blank | gone_by set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `arthur_kill_1947` | Arthur Kill | 1947 | 1940 | – | 136694 | +3 E, +6 N | 7.3 | 875 | 214 | 544 | 117 | 117 |
| `the_narrows_1947` | The Narrows | 1947 | 1941 | – | 139982 | -8 E, +4 N | 7.4 | 479 | 72 | 360 | 47 | 47 |
| `elizabeth_1947` | Elizabeth | 1947 | 1941 | – | 254343 | +5 E, +1 N | 12.8 | 133 | 42 | 77 | 14 | 14 |
| `jersey_city_1947` | Jersey City | 1947 | 1940 | – | 254499 | +3 E, +6 N | 5.7 | 260 | 36 | 217 | 7 | 7 |
| `coney_island_1947` | Coney Island | 1947 | 1940 | – | 137694 | -17 E, -1 N | 4.7 (one window) | 598 | 22 | 538 | 38 | 38 |
| `brooklyn_1947` | Brooklyn | 1947 | 1940 | – | 123124 | -7 E, -3 N | 9.1 | 1,785 | 128 | 1,601 | 56 | 52 |
| `jamaica_1947` | Jamaica | 1947 | 1941 | – | 129963 | +4 E, +10 N | 8.8 | 1,491 | 249 | 1,098 | 144 | 137 |
| `far_rockaway_1947` | Far Rockaway | 1947 | 1941 | – | 138136 | +5 E, +6 N | 35.0 (13 windows, mostly water) | 205 | 44 | 150 | 11 | 11 |
| `flushing_1947` | Flushing | 1947 | 1942 | – | 138246 | +10 E, +5 N | 9.3 | 1,190 | 198 | 929 | 63 | 60 |
| `central_park_1947` | Central Park | 1947 | 1941 | – | 122894 | -10 E, +7 N | 10.7 | 1,023 | 89 | 868 | 66 | 58 |
| `mount_vernon_1947` | Mount Vernon | 1947 | 1941 | – | 130724 | +7 E, +3 N | 4.7 | 287 | 33 | 242 | 12 | 12 |
| `yonkers_1947` | Yonkers | 1947 | 1941 | – | 255024 | -12 E, -2 N | 5.9 | 278 | 85 | 148 | 45 | 43 |
| `lynbrook_1947` | Lynbrook | 1947 | 1941 | – | 130380 | -7 E, -1 N | 7.9 | 198 | 55 | 133 | 10 | 10 |
| `sea_cliff_1947` | Sea Cliff | 1947 | 1941 | – | 136120 | -3 E, 0 N | 13.9 | 44 | 11 | 28 | 5 | 5 |
| `lawrence_1947` | Lawrence | 1947 | 1941 | – | 130229 | -3 E, +2 N | 6.2 | 30 | 4 | 26 | 0 | 0 |
| `arthur_kill_1955` | Arthur Kill | 1955 | 1954 | 1955 | 136697 | -4 E, +4 N | 3.7 | 874 | 494 | 186 | 194 | 121 |
| `the_narrows_1955` | The Narrows | 1955 | 1954 | 1955 | 139984 | -5 E, +5 N | 2.9 | 478 | 112 | 328 | 38 | 15 |
| `elizabeth_1955` | Elizabeth | 1955 | 1953 | 1955 | 254346 | 0 E, +4 N | 4.0 | 131 | 26 | 88 | 17 | 8 |
| `jersey_city_1955` | Jersey City | 1955 | 1954 | 1955 | 254501 | +1 E, -1 N | 3.2 | 260 | 22 | 212 | 26 | 24 |
| `coney_island_1955` | Coney Island | 1955 | 1954 | 1955 | 137695 | -2 E, +4 N | 5.1 | 598 | 35 | 522 | 41 | 21 |
| `flushing_1955` | Flushing | 1955 | 1954 | 1955 | 138249 | +4 E, +2 N | 4.8 | 1,192 | 165 | 900 | 127 | 80 |
| `brooklyn_1956` | Brooklyn | 1956 | not in the record | 1956 | 123128 | 0 E, +2 N | 3.6 | 1,783 | 69 | 1,615 | 99 | 73 |
| `central_park_1956` | Central Park | 1956 | not in the record | 1956 | 122895 | 0 E, -2 N | 3.1 | 1,021 | 153 | 775 | 93 | 60 |
| `mount_vernon_1956` | Mount Vernon | 1956 | 1954 | 1956 | 130719 | -4 E, +3 N | 5.5 | 287 | 14 | 244 | 29 | 21 |
| `yonkers_1956` | Yonkers | 1956 | 1954 | 1956 | 472567 | -2 E, +6 N | 6.7 | 277 | 18 | 221 | 38 | 18 |
| `jamaica_1957` | Jamaica | 1957 | 1957 | 1957 | 129966 | +6 E, +5 N | 5.2 | 1,485 | 91 | 1,275 | 119 | 65 |

Photograph and field-check years are from the USGS metadata records, not read off these
collars. The 1954 editions of Far Rockaway, Lawrence, Lynbrook and Sea Cliff repeat the 1941
photographs and are not used; Perth Amboy (Staten Island's western tip) was not fetched.
`gone_by` uses the edition year (a building absent from photographs of 1940 was gone by 1947).

## Method

1. **Scan.** The GeoPDF's 600 ppi scan (1 px = 2.65 m; a mark is 6-9 px, a road casing 2-3 px;
   the GeoTIFF is a 300 ppi JPEG in which marks cannot be told from the casing they touch),
   rendered tile by tile with `pdftoppm`.
2. **Ink.** Black = brightest channel below a threshold (40 % of the way from the sheet's ink
   to its paper; a second, loose one at 72 % for hairlines). Brown contours and blue water are
   bright in one channel.
3. **Cores.** Opening with a 5 px disc: lines vanish, solid blobs stay. A core is a `mark`
   when 12-40 m long, at most 2.1 : 1, filled; a `bar` when 40-120 m long; longer or larger
   cores are block fronts and heavy lines.
4. **What a core hangs on** (the loose ink it is connected to): nothing; a letter-sized
   component (rejected when other strokes or hairlines hang on it); or the road net. Rejected
   further: a core bordering a closed counter (o, e, a, d, B; also the ladder of rails and
   ties); a bead of something longer and 4 px wide (`body`); anything thick within 8 px that
   is not another mark (letter stem, ball terminal next to its arc, rail, block front); a line
   running through the blob's centre and on beyond it (rail and tie); the hue of a dark brown
   index contour or a dark blue stream; a blob surrounded by water.
5. **Lettering, sheet-wide.** Pieces of letters found in step 4 mark a label: a kept blob
   within 24 px of one (with a second within 55 px), or on the line joining two, is dropped.
   Bars next to lettering or to another stroke are dropped (letter stems).
6. **Rows.** Marks refused only for touching other building ink come back where nothing speaks
   for lettering or rails (square, full size, no line through, no letter piece within 45 px,
   four other marks within 60 px): `in_row`.
7. **Editions.** In the Brooklyn and Harlem quadrangles a mark of 1889 and one of 1897 within
   35 m (mutually nearest) are one building, placed at their mean.
8. **Ground.** Marks on water of the survey year (the built terrain's cover history, with
   the shore given one cell) are dropped: 263. Marks on marsh are kept and flagged.

## Validation

**Precision** — 36 random points of the file per sheet (18 for the two eastern sheets),
each looked at on the scan (`tools/contact_export.py`, seed 21):

| Sheet | Checked | False | Precision |
|---|---|---|---|
| `brooklyn_1889` | 36 | 3 (2 lettering, 2 doubtful counted half) | 0.92 |
| `brooklyn_1897` | 36 | 1 (lettering) | 0.97 |
| `harlem_1889` (faded scan) | 36 | 4.5 (lettering) | 0.88 |
| `harlem_1897` | 36 | 1 (road junction) | 0.97 |
| `staten_island_1897` | 36 | 2 (lettering) | 0.94 |
| `hempstead_1897` (Queens part) | 18 | 0 | 1.00 |
| `oyster_bay_1897` (44 points in the city) | 18 | 4 (2 lettering, road bend, contour crossing a stream) | 0.78 |
| **all** | **216** | **15.5** | **0.93** |

By confidence: high 42.5 / 44 = 0.97, medium 137 / 149 = 0.92, low 21 / 23 = 0.91; `large`
5.5 / 7. Of the 15.5 false marks 11.5 are pieces of lettering (large serif place names, mostly
where a letter crosses a road), 2 road junctions or bends, 1 contour / stream crossing, 1 a
doubtful long bar and marsh mark. A separate sample of 36 `in_row` points: 33 right (two on a
purple library stamp, one in lettering). Earlier detector versions measured 0.72-0.86 on fresh
samples; the tests of step 4 were added from those.

**Recall** — counted on three windows of 1.6 km: Richmondtown 1897 28 of 48 marks (28 of 33
outside the village core), Flatlands 1889 37 of 52, Gravesend 1889 7 of 11: about **0.65**
of the separately drawn marks, 0.85 away from village cores and lettering. Lost: marks
touching each other or a block front, marks drawn on a single-line road (taken for rail
knots), marks next to lettering, the two houses attached to a long barn.

**gone_by** — 59 points lie within 12 m of a standing building with a recorded year before
the survey; 2 of them (3 %; 3 of 63 against the previous model build) were blank on a later sheet (the sheet omits or displaces the
building; e.g. two Riverdale estates on Yonkers 1947). Those are reset to `null`; expect the
same rate among the rest. Before the late sheets' ink threshold was fixed the rate was 5 of 5
checked — the check is what found it.

**Land of its time** — 263 marks in water dropped; 246 on tidal marsh, 24 on freshwater
wetland, 2 on flats kept as `low` (shacks and hotels on the Jamaica Bay marshes are real, so
is some lettering).

**Density** — marks per km² of ground outside the built-up extent of 1897: Staten Island 11.0,
Queens 10.0, Brooklyn 11.1, Bronx 13.1, upper Manhattan 11.1; in 1889: Queens 5.9, Brooklyn
6.1, Bronx 9.1. Against the census (`data/tables/population.csv`): Queens had 87,050 people in
1890 and 1,618 marks on the 1888-89 survey; Staten Island about 63,000 in 1897 (51,693 in
1890, 67,021 in 1900) and 1,504 marks. At five to six people to a house the marks hold a
tenth to an eighth of the people: the rest lived in the villages drawn as frontages, and a
third of the marks are missed. No borough has more marks than its people allow. Town-level
census figures were not looked up.

**Footprints under the marks against chance** (`tools/standing_check.py`): the same marks
moved 150-190 m off their spots find a footprint just as often.

| Best footprint within 25 m | Real | Moved (three offsets) |
|---|---|---|
| recorded year no later than the survey | 99 | 53, 58, 52 |
| estimated year no later than it ("by then"), within 12 m in open ground | 19 | 4, 4, 4 |
| the same, elsewhere | 735 | 653, 674, 663 |
| estimated year after the survey | 4,796 | 4,874, 4,676, 4,857 |

(Model build of 2026-11-10 18:24. Against the build before it, which had not yet used the
marks: 106 against 67-70; 4 against 2-3; 658 against 597-615; 4,738 against 4,597-4,792.)
Only the recorded class stands out (1.5-1.8 times chance; 3 times where at most 6 footprints
stand within 60 m), and the handful of "by then" footprints in open ground. A later-dated
footprint that is the only one within 25 m and lies within 12 m of the mark — the rule
`nyc_buildings.evidence_bounds` used — is found 285 times at the real marks and 225 times at
the moved ones. See `data/research/farmsteads_years.md`.

## Known failures

* **Village cores and platted tracts.** Houses drawn shoulder to shoulder (Westchester village,
  Unionport, Richmondtown's centre, the streets of Gravesend in 1897) merge into bars and
  fronts; only 397 come back as `in_row`. The four squares of Gravesend, Flatbush Avenue,
  Jamaica and Flushing are black frontages: use `data/manual/extents` there.
* **Lettering** is the false positive (5 % of the file): ball terminals and serifs of large
  place names, above all where a letter crosses a road.
* **Marks on single-line roads and beside railways** are lost with the rail-and-tie knots.
* **`large`** is thin (304) and its precision poorer; letter stems and long buildings look alike.
* **Churches, schools** are not told apart; one mark may stand for more than one building
  (the sheets generalise at 1:62,500), and a mark is 15-30 m across whatever the building.
* **Position**: 12-22 m RMS after the local shift, more where the old survey is locally off.
* **The faded Harlem 1891 scan** ("Not Optimal" in the catalogue) reads lettering worse.
* **Not checked**: the 1900 editions; Oyster Bay's survey year on a collar; photograph years
  on the 1947-57 collars; `gone_by` = 1897 by eye (243 points).

## Reproduce

```
cd pipeline
../.venv/bin/python -I topo_farmsteads.py fetch     # 7 + 26 GeoPDFs, 560 MB -> data/raw/farmsteads/
../.venv/bin/python -I topo_farmsteads.py detect    # ~2 CPU-minutes per 15-minute sheet, 10 s per 1:24,000 sheet; under 1 GB
../.venv/bin/python -I topo_farmsteads.py export    # 1 minute; needs data/interim/nyc_buildings.parquet and grid_detail_*
```

Needs poppler's `pdftoppm` on the path. The export re-reads `nyc_buildings.parquet`, so the
`standing_*` columns follow the built model: re-run it after a rebuild.
