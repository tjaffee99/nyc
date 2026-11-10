# The piers of the port of New York, dated

`piers.geojson` holds the finger piers of the five boroughs as dated outlines: the ones that stand and the ones that are gone. The terrain's cells (29 m) are wider than a pier, so the terrain cannot carry them. The pipeline is meant to draw each outline as a low deck, with a shed where it had one.

Nothing here is generated. Every outline is either today's OpenStreetMap pier or was read off a dated government map, and every year is a cited date, a bracket between two map editions, or marked `estimated`.

## Counts (from `stats.json`)

870 piers: 242 standing (215 from OpenStreetMap, 27 last seen on a chart of 2012 or later and taken as standing) and 628 vanished. A pier that was rebuilt, or whose place stood empty between two piers, is two features.

| borough | piers | standing | vanished |
|---|---|---|---|
| Manhattan | 293 | 93 | 200 |
| Brooklyn | 237 | 70 | 167 |
| Queens | 105 | 25 | 80 |
| Bronx | 84 | 23 | 61 |
| Staten Island | 151 | 31 | 120 |
| **all** | 870 | 242 | 628 |

| decade | start | end |
|---|---|---|
| 1880s | 21 | 0 |
| 1890s | 295 | 0 |
| 1900s | 12 | 0 |
| 1910s | 71 | 39 |
| 1920s | 71 | 10 |
| 1930s | 69 | 39 |
| 1940s | 99 | 66 |
| 1950s | 44 | 37 |
| 1960s | 46 | 60 |
| 1970s | 14 | 70 |
| 1980s | 12 | 56 |
| 1990s | 35 | 90 |
| 2000s | 19 | 67 |
| 2010s | 31 | 94 |
| 2020s | 31 | 0 |
| standing |  | 242 |

The 1890s column is mostly "by 1897" (438 piers have `start_is_upper_bound`). 205 vanished piers have no later map of their place at all: their end is the middle of the years from their last map to 2026, marked `estimated`.

| quality | start_year | end_year |
|---|---|---|
| recorded | 39 | 218 |
| bracket | 194 | 326 |
| estimated | 637 | 326 |

For `end_year`, `recorded` means "stands, it is in OpenStreetMap", plus the cited ends of the piers that were rebuilt.

Outlines: 315 from the charts, 337 from the USGS 1:24,000 sheets, 218 from OpenStreetMap. Sheds: 493 piers drawn roofed, 377 open or not drawn.

Sources read: 42 USGS 1:24,000 sheets as full editions, 9 more for additions only, 24 chart editions, 4 sheets of 1888-98. Listed in `sources_used.csv`.

Set aside: 39 vanished piers in `piers_terrain_conflict.geojson`. Thrown out (`review.csv`): 139 × one sighting, ragged outline; 79 × an earlier pier at a standing pier's place, without an outline of its own; 41 × on land older than itself; 30 × one sighting; 29 × outline not long and thin; 28 × never a pier on any source; 25 × solid ground on most maps before its last sighting; 21 × same spot and years as a better outline; 3 × in OpenStreetMap but on no dated source used here.

## Files

| file | what |
|---|---|
| `piers.geojson` | the piers (WGS84 polygons), one feature per lifespan of a pier |
| `piers_terrain_conflict.geojson` | same format: vanished piers that the maps show but that lie on ground the terrain grid already has as land before the pier's start. Not for drawing as they are. See "For the lead". |
| `research.csv` | cited dates for named piers and pier groups (Wikipedia articles, quoted); overrides the map brackets |
| `sources_used.csv` | every map edition that was read: content years, role, registration, file URL |
| `review.csv` | what was thrown out and why (lon / lat of each) |
| `stats.json` | the counts below, rewritten by `tools/dates.py` |
| `tools/` | everything that made the files; see "Regenerating" |

## Properties

| property | meaning |
|---|---|
| `id` | `pier_<mn/bk/qn/bx/si>_<n>`; renumbered on every rebuild, not stable |
| `name` | OpenStreetMap's name for a standing pier, the researched name, or `Pier, foot of <street>` when a street in line with the pier ends within 60 m of it (taken from today's street data); empty otherwise. Pier numbers of vanished piers were not researched. |
| `start_year`, `end_year` | decimal years; `end_year` 9999 = stands |
| `start_quality`, `end_quality` | `recorded` (a cited date; for `end_year` 9999: it is in OpenStreetMap), `bracket` (between two map editions 20 years or less apart: the year is the middle and the note names both), `estimated` (a wider bracket, an upper bound, or absence from OpenStreetMap only) |
| `start_is_upper_bound` | true: the pier is already on the first source that covers its place, so `start_year` is that source's year and the pier is older by an unknown amount. Half of the piers are like this; most say "by 1897". |
| `shed` | `none` or `shed`: whether the maps draw the pier roofed. `headhouse` is in the vocabulary but nothing here was researched to that level. |
| `shed_start`, `shed_end` | only when the maps show the roof coming or going during the pier's life |
| `deck_m` | 2.5 everywhere (the brief's default; not measured) |
| `shed_m` | 10.0 wherever there is a shed: an estimate for a one-storey transit shed, not a measurement |
| `source`, `source_url` | where the outline comes from: `osm`, `noaa_<chart id>`, `usgs_<sheet>`, with the file's URL |
| `note` | how each date was arrived at, naming the map editions |
| `evidence` | every reading in time order: year, source type (`s` 1890s sheet, `c` chart, `u` USGS 1:24,000), state (`p` pier, `w` water, `l` land) |
| `borough`, `length_m`, `width_m` | borough of the nearest building (the county lines put the whole East River in Manhattan); size of the outline's bounding rectangle |
| `made_land_share` | vanished piers: share of the outline on terrain cells that become land before the pier's end |
| `shed_building_share` | standing piers: share of the outline under buildings of the city's footprints (see "Sheds") |
| `research_url` | present when `research.csv` set a date |

## Sources and licences

| source | licence | used for |
|---|---|---|
| USGS Historical Topographic Map Collection, 1:24,000 sheets of 1935, 1947, 1955-57, 1966-69, 1994-95 and photorevisions of 1979-81, for the quadrangles Jersey City, Weehawken, Central Park, Brooklyn, The Narrows, Coney Island, Flushing, Mount Vernon, Yonkers, Elizabeth, Arthur Kill, Perth Amboy, Far Rockaway, Jamaica. Files at `https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/`; each file's URL is in `tools/sheets.json`. | public domain (US government) | outlines and presence, whole city |
| USGS 1:62,500 sheets Harlem 1891, Brooklyn 1897, Staten Island 1898, Paterson 1888 (the copies and shifts of the natural-landscape part, `data/manual/natural/usgs_sheets.json`) | public domain | presence only: a pier is a black stroke |
| US Coast & Geodetic Survey / NOAA charts 745 → 12335 "Hudson and East Rivers, Governors Island to 67th Street" and 541 → 12334 "New York Harbor, Upper Bay and Narrows", 1:10,000, editions 1927-2020 (24 editions used). Office of Coast Survey Historical Map & Chart Collection, <https://historicalcharts.noaa.gov/> | public domain (US government) | outlines and presence in the working port, every few years |
| OpenStreetMap `man_made=pier` polygons through Overture Maps 2026-10-21.0 (theme base, type infrastructure) | ODbL: attribute "© OpenStreetMap contributors" | today's piers |
| Wikipedia articles named in `research.csv` | CC BY-SA; only dates and short quotations are used | cited dates |
| PROJ grid `us_noaa_conus.tif` (NADCON, <https://cdn.proj.org/>) | public domain | NAD27 → NAD83 for the USGS sheets |
| the project's own terrain grid, building points and street data | — | checks, borough, street names |

Not used, and why:

- **Chart 541 of 1898 and 1912**: no land tint, so the automatic fit is not to be believed (26-29 m rms on a land mask that separates nothing). They would need control points by hand.
- **Chart 745 of 1939**: the fit is too weak (17 m rms on 8 blocks).
- **Eight of the thirteen photorevised sheets (1979-81) and the Weehawken sheet of 1943**: downloaded, not read. The 1943 sheet did not finish in the extraction (stopped after ten minutes on its first step) and the run behind it was cut off. Photorevisions only add piers, so the loss is small: a pier built between 1967 and 1977 outside the charts may be dated later than it should.
- **The 1995-98 sheets of Brooklyn, Coney Island, Flushing, Mount Vernon, The Narrows and Yonkers**: reprints of the photorevised sheets ("photoinspected"), not a new state. Left out on purpose.
- **The NYPL atlases (Bromley)** and **the 1924 / 1951 aerials**: not attempted.
- **OpenHistoricalMap's pier polygons** (`data/manual/ohm/extras_water_dated.geojson`, about 119 East River piers stamped 1800-1848): real outlines, but the dates are placeholders. They are the obvious next source for the waterfront before 1890.
- **New Jersey's shore** (Hoboken, Jersey City): left out as the brief allows. The same charts cover it.

## Method

1. **Reading a sheet** (`tools/extract.py`). Non-water is what is not water-coloured (tinted sheets), or black ink with small enclosed areas filled, plus the land of the period (untinted scans). Lines and lettering are opened away. *Core land* is non-water opened by 45 m, which removes everything narrower than 90 m. A *finger* is what remains outside the core. Each finger is kept with its outline, its bounding rectangle, how far it reaches from the core, where it touches it, and the share of ink inside it.
2. **Reading a chart** (`tools/chart.py`). The scans carry no georeference. The land tint is found by Otsu's threshold; the chart is fitted to today's shoreline, first coarsely (rotation, scale, offset by cross-correlation; chart 745 is turned 29.5° so that the avenues run up the sheet), then in 35 blocks by least squares. The fits are 2-4 m rms, except chart 745 of 1931 (9 m) and 1944 (5 m) and chart 541 of 1927 (6 m); those three are then treated like the USGS scans (step 4) and never supply control. Then the same finger analysis.
3. **What counts as a pier** (`tools/build.py`). A finger that reaches 35 m or more from the bulkhead, is attached at one end only (this drops bridges and quays), is at least 1.4 times as long as wide and at most 100 m wide, fills 55 % of its rectangle (62 % outside the working port), and lies over today's tidal water or over land made later. Dropped as natural: unroofed fingers at marshes, and short fingers on the ocean beaches (groynes).
4. **Registration of the USGS scans.** They sit up to 30 m off in places. Each sheet's local offset is measured from the piers whose position is known (OpenStreetMap's and the well-fitted charts') and its own outlines are moved back by it (`data/interim/piers/sheet_offsets.json`).
5. **One pier across editions is one track**: two outlines match when half of the smaller lies in the larger. The outline kept is OpenStreetMap's for a standing pier, else the best-fitted chart's, else a USGS sheet's. An outline that is nearly its bounding rectangle is replaced by it, since outlines read off a 2 m raster are ragged.
6. **Every track is looked up on every source** that covers it: `pier` (60 % of the outline solid, water beside it), `water` (30 % or less solid), `land` (inside land wider than 90 m, or solid with solid ground beside it), else unknown. Photorevisions and office-edited reprints count only when they show the pier, because they add and never remove.
7. **Dates** (`tools/dates.py`). Each source has a content interval: a USGS sheet from its aerial photographs to the date on the map, a chart its edition year. A single contrary reading between two agreeing ones is treated as a misreading. Two or more absences in a row split a track into two lifespans.
   - end ≥ the latest source that shows the pier; end ≤ the earliest later source without it; the year is the middle.
   - start ≤ the earliest source that shows it; start ≥ the latest earlier source that shows water; the year is the middle. With no earlier source, the year is the first sighting and `start_is_upper_bound` is true.
   - A pier last seen on a chart of 2012 or later and missing from OpenStreetMap is taken as standing (`estimated`).
   - Where the terrain makes more than half of the outline land before the maps' end, the pier ends at the terrain's year (`estimated`).
   - `research.csv` overrides, and adds the earlier pier where a pier was rebuilt (Pier 57, Pier 26, Steeplechase Pier).

## Sheds

`shed` comes from how the sheets draw the pier: hatched (1955-69 sheets), solid black (1947 sheets) or olive (charts from 1959) means roofed; a white or plain outline means an open deck. The roof test is the share of ink inside the outline (30 % or more).

For a standing pier with buildings of the city's footprints on a quarter or more of it, the roof belongs to the buildings data: `shed` is `none`, or `shed_end` is the year the earliest of those buildings starts in `nyc_building_points.parquet`. The note says which.

`shed_m` is 10 m everywhere and is an estimate. No shed height was researched. The two-storey liner piers were taller.

## Checks (`tools/check.py`)

All pass on the files as delivered:

```
ok   properties present: 0 of 870 
ok   ids unique: 0 of 870 
ok   qualities: 0 of 870 
ok   shed vocabulary: 0 of 870 
ok   shed has a height: 0 of 870 
ok   start year present: 0 of 870 
ok   start < end: 0 of 870 
ok   years in range: 0 of 870 
ok   shed years inside the pier's: 0 of 870 
ok   every date has its source in the note: 0 of 870 
ok   valid polygons: 0 of 870 
ok   inside the five counties: 0 of 870 
ok   100 m2 or more: 0 of 870 
ok   map outlines are long and thin (length >= 1.3 x width, width <= 105 m): 0 of 652 
ok   no two piers on one spot at once: 0 of 870 
ok   vanished piers on land older than themselves (terrain grid, > 60 % of the outline): 0 of 628 ; 189 outlines touch a cell that is made land before their end (roots, and fills the maps date later than the terrain)
ok   named piers carry their researched dates: 0 of 11 
features 870 | standing 242 | vanished 628
```

Also looked at: overlays of the result on the 1955 and 1967 sheets for Lower Manhattan, the Hudson to 50th Street, Sunset Park, St George to Stapleton, Greenpoint and Williamsburg, College Point (`tools/overlay.py`); the picture of the whole city (`tools/overview.py`).

## Known weak spots

- **Start years before 1930.** Outside the charts the only sources before 1940 are the 1889-98 sheets, where a pier is a stroke one or two pixels wide. "By 1897" is the best that can be said for half the piers, and a stroke cannot tell a pier from the older pier it replaced on the same spot. Before 1889 nothing was read.
- **End years after 1966 outside the charts.** The Bronx, most of Queens, the west and south of Staten Island and south Brooklyn have no chart here, and several of their 1995 sheets are reprints. A pier last seen in 1966 and gone today gets the middle of 1966-2026, marked `estimated`.
- **Charts lag.** A chart edition shows what the Coast Survey knew, which can be a few years behind, and ruins stay charted.
- **Small piers.** Anything narrower than about 12 m is below what the method reads. Small standing piers from OpenStreetMap that no map draws get a weak year, said in the note.
- **Wide piers that are gone** (over 90 m, such as the container-era piers replaced by fill) are read as land and are missing.
- **Two piers drawn touching** on a sheet come out as one outline or are rejected.
- **Pier numbers** of vanished piers are not given.
- **No visual check of every pier.** About 150 outlines were looked at in the overlays. The rest rest on the numeric tests.

## Regenerating

```
cd data/manual/piers/tools
../../../../.venv/bin/python download.py meta && ... download.py sheets && ... download.py charts && ... download.py osm && ... download.py wiki
../../../../.venv/bin/python extract.py        # every USGS sheet: about a minute each
../../../../.venv/bin/python chart.py          # every chart: about five minutes each; run one at a time (2 GB)
../../../../.venv/bin/python build.py          # tracks and lookups -> data/interim/piers/tracks.json
../../../../.venv/bin/python dates.py          # -> piers.geojson, piers_terrain_conflict.geojson, review.csv, stats.json
../../../../.venv/bin/python check.py
```

Downloads go to `data/raw/piers/` (about 2.4 GB), intermediates to `data/interim/piers/`. The NADCON grid must be at `data/raw/piers/proj/us_noaa_conus.tif`.

## For the lead

- **Drawing.** Extrude each outline from the water to `deck_m` (2.5 m) between `start_year` and `end_year`. Where `shed` is `shed`, add a box of `shed_m` (10 m, estimated) on the outline inset by about 2 m, between `shed_start` (default: the pier's start) and `shed_end` (default: the pier's end).
- **Do not land-check the piers against the terrain grid.** A pier root always overlaps the bulkhead cell, and 189 outlines touch a cell that the terrain makes land before the pier's end. `made_land_share` says how much.
- **`piers_terrain_conflict.geojson`** holds the vanished piers where the terrain has the ground as land before the pier's start (`terrain_land_year`, `terrain_conflict_share`). Most are short pieces at the bulkhead. The ones along the Chelsea shore sit on the Thirteenth Avenue fill of 1837 that was dug out again for the Chelsea Piers: the terrain keeps that ground as land. Either fix the terrain year from the pier's dates or leave these out.
- **`start_is_upper_bound`** piers appear on the slider in the year of their first map. If the waterfront should not spring up in 1897, the honest alternatives are to fade them in, or to trace an older source (see "Not used").
- **Attribution** for `SOURCES.md`: USGS Historical Topographic Map Collection (public domain); NOAA Office of Coast Survey Historical Map & Chart Collection (public domain); © OpenStreetMap contributors (ODbL) via Overture Maps.
