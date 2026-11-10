# New York City Through Time — project brief

An interactive 3D web map of New York City with a year slider (1609 → today): pan, zoom,
tilt, drag the year, and see what stood then — buildings, shoreline and made land, streets,
railways and elevated lines, bridges, parks, landmarks — with a year counter and a population
counter. Live at https://nyc.theojaffee.net (GitHub Pages, `gh-pages` branch).

It is a port of the Bay Area map (`tjaffee99/bay`, bay.theojaffee.net): same viewer, same
rules, new data. The code was copied, not forked; nothing is shared at run time.

## The owner's standing rules

- Landmarks are **real reconstructions** from cited dimensions, not procedural stand-ins.
- **Real, cited data as much as possible; procedural generation as little as possible.**
  Anything generated is marked `procedural`, anything imputed `estimated`. Prefer tracing a
  real historical map over inventing geometry. An accurate map of less ground beats a
  generated map of more.
- The owner is cost-sensitive: deploy rather than verify at length, and say plainly what was
  not checked.

## Core idea

Every feature is a geometry with a lifespan:

```
{ geometry, kind, height_m, start_year, end_year, year_confidence, source }
```

- `end_year`: `9999` if it still exists. The viewer shows a feature iff `start_year <= year < end_year`.
- `year_confidence`: `exact` (from records) | `estimated` (imputed, or a placeholder year spread
  over its range) | `procedural` (generated to match a historical map) | `reconstructed`
  (hand-modelled landmark from cited dimensions).
- `source`: short id pointing to an entry in `SOURCES.md`.

## Scope

- **Now:** the five boroughs, and seven counties around them: Hudson, Bergen, Essex, Union and
  Passaic (New Jersey), Westchester and Rockland (New York) — `data/manual/extent_counties.json`.
  Manhattan carries the deepest history; the counties have today's buildings with their
  parcel years, the landscape of 1609, made land, streets, railroads, parks and labels, and
  nothing vanished. The owner's priority order for accuracy: Manhattan > the other boroughs >
  the inner suburbs > the outer suburbs.
- **Not on the map, and why:** Nassau publishes no construction years in bulk; 22 of
  Westchester's 43 municipalities publish none either (their ground and streets are drawn,
  their buildings are not: `county_buildings.MIN_YEAR_SHARE`). The rest of the metropolitan
  area (the owner's list: Putnam, Suffolk, Ulster, Dutchess, Orange, Sullivan NY; Middlesex,
  Monmouth, Ocean, Somerset, Morris, Sussex, Hunterdon, Mercer NJ; Greater Bridgeport, Western
  Connecticut and New Haven; Pike PA) is not started. New Jersey's tax list (MOD-IV) covers
  every county of the state; the binding limits are the size of the published site and cost.

## Repo layout

```
/viewer            web app (Vite + TS, deck.gl 9 + MapLibre 5 with an empty style)
/pipeline          python stages, one script per stage (see Makefile)
/data/raw          downloads (gitignored)
/data/interim      cleaned / joined intermediates + reports (gitignored)
/data/manual       hand-traced / hand-researched data (COMMITTED — precious)
/data/tables       small CSVs: population, events, places, landmarks, dates (committed)
/data/research     research notes (landmark dimensions, references)
SOURCES.md         every data source: URL, licence, attribution, use
CLAUDE.md          this file
```

## Running

```
make setup      # python venv + npm install
make data       # downloads + every stage (heavy stages run one at a time)
make dev        # viewer at http://localhost:5173
make deploy     # build + publish viewer/dist to gh-pages -> nyc.theojaffee.net
```

## Checking a build

```
cd pipeline && ../.venv/bin/python audit.py           # invariants on the built building files
cd viewer && node scripts/check-years.cjs http://localhost:5173/   # headless boot at 8 years / views
```

`audit.py` must report 0 for start >= end and out of range; overlapping pairs and nested
pairs in the city's own footprints are reported, not failed; "before their ground" should be 0
(if it is not, run `terrain_tiles.py land`, the two building stages and `terrain_tiles.py`
again: decision 22). The whole chain in order, one stage at a time (about 25 minutes):
`nyc_buildings.py evidence` → `terrain_tiles.py land` → `nyc_buildings.py` →
`county_buildings.py` → `street_trees.py build` → `airports.py` → `terrain_tiles.py` →
`ground_detail.py` → `roads.py` (+ `check`) → `transit.py` → `cities.py` → `nyc_extras.py` →
`audit.py`. Other jobs on the machine get killed for memory while it runs, and it them. After a deploy run the second
command against https://nyc.theojaffee.net/ and compare a file's checksum with `viewer/dist`.

## Working conventions

- Commit after each working step; keep the viewer runnable.
- Every pipeline stage is idempotent and cached; raw downloads are never modified in place.
- When a historical fact or date drives data, cite the source in `SOURCES.md` or next to the data.
- When unsure whether a year is real or a placeholder, mark it `estimated`.
- Metric work is done in UTM 18N (`common.NYC_CRS`); stored geometry is WGS84.

## Rules carried over from the Bay project (they cost the most there)

**Data**
- Assessor years are messy: detect placeholder ("heap") years, treat them as ranges or bounds,
  refine from neighbours, spread heaps instead of stacking them, mark the result `estimated`.
- Evidence order for a year: researched row > landmark / historic-district record > assessor >
  permit > neighbours. Tall or large buildings are never dated from small neighbours.
- Nothing stands before its ground: date made land first, then check every building, tree and
  road against it.
- Demolished things are not in modern data. Base "what stood before" on georeferenced
  atlases and traced footprints, not on generation.
- Invariants, checked on the built files after every rebuild: no two buildings on one spot at
  once (documented > traced > generated); no feature with start >= end; no year carrying
  thousands of buildings more than its neighbours.

**Viewer performance**
- Few layers (per-layer cost dominates): all landmarks are one merged mesh; decorations are one
  instanced layer per kind. Nothing is rebuilt per animation frame; time lives in shaders.
- Tiled layers stay alive across zoom (hidden, not removed) or everything blinks.

**Hosting and machine limits**
- GitHub Pages cancels a deployment whose file sync runs over ten minutes: on this site that
  happens somewhere between 104 and 147 MB (decision 33: the Pages part stays under 100 MB). After `make deploy`, confirm the live site by comparing a file's checksum — a
  pushed deploy is not a published one.
- The build machine has 16 GB: run heavy stages one at a time, process big arrays in chunks.
- Headless screenshots do not work on the build machine (software rendering times out). Verify
  with numeric checks and a headless console-error check, and tell the owner what to eyeball.

**Working with parallel agents**
- One bounded part each, a tool-call budget, exclusive ownership of named files; only the lead
  runs heavy stages and edits shared pipeline / viewer code; agents hand back exact specs or
  patches for anything outside their files.
- Smoke-test each stage with the real data before a long rebuild.
- Landmarks: anchor, orientation and plan from the real footprint, heights from cited sources,
  checked numerically against the footprint and the measured roof height.

## Pipeline stages (pipeline/, one script per stage; see Makefile)

`download_nyc` · `download_overture` (+ `region`, `region_buildings`) → `footprints_raw` →
`extent` → `terrain_grid` → committed inputs refreshed by their own stages (`ohm_nyc`,
`aerial_presence`, `topo_farmsteads`, `building_records`, `counties_nj`, `counties_ny`) →
`nyc_buildings evidence` → `terrain_tiles land` → `nyc_buildings` (+ `nyc_predecessors`,
`nyc_extras`) → `county_buildings` → `street_trees` → `airports` → `terrain_tiles` →
`ground_detail`, `roads`, `transit`, `cities`, `nyc_extras` (site labels) → `audit` → `deploy`.
Tools: `footprint_at.py` (footprints around a point, in the landmark kit's local metres).

Not ported from the Bay copy (kept as reference, they do not run): `sf_predecessors.py`,
`region_predecessors.py` (extent fill, clearance corridors), `sanborn_trace.py`,
`lidar_parts.py`, `ohm_import.py`, `geocode.py`.

## Status and decisions log

(Deviations from the Bay project and New York-specific decisions, with reasons. Add to it.)

1. **Extent: the five boroughs** (TIGER county outlines grown ~1 km; the fade is 1 km wide so
   Manhattan's Hudson shore, 500-700 m from the state line, does not fade). New Jersey's shore
   lies in the faded band without buildings. One bounding box (`common.NYC_BBOX`) for the
   terrain grids and every extract.
2. **Buildings: Manhattan is one file, the other boroughs are z13 tiles.** The viewer's
   "core" set (always loaded, 118 k features with the vanished ones) is Manhattan; the other
   boroughs load as tiles from zoom 11, large / tall buildings from zoom 9. Clicks work on both.
3. **Years.** `nyc_buildings.py` docstring has the rules. The city's construction years come
   from the assessor and four fifths are heaps (1899, 1900, 1901, 1910, 1915, 1920, 1925,
   1930, 1931, 1935, 1940 …, detected per borough): a heap up to 1901 means "by then", a later
   one "about then" (± 2.5 years; 1940 stops at mid-1942, 1945 starts after the war). Recorded
   years around a heap building refine it; the result is `estimated`. The LPC building
   database (38 k buildings) outranks the assessor. Height floors: 25 m ≥ 1870, 40 m ≥ 1889,
   80 m ≥ 1895 for estimated years.
4. **Heights are measured** (the footprints' roof height). OpenStreetMap's 3D parts replace
   the flat extrusion of ~3,300 buildings where at least two part heights exist and the
   tallest part is within 0.85-1.3x of the measured roof.
5. **Terrain: the Bay's two grids** (z13 ≈ 58 m for zooms 8-13, z14 ≈ 29 m close in) over the
   whole box. The viewer's terrain code assumes those zooms; a finer Manhattan grid would
   need viewer work. Piers are narrower than a cell and are not in the terrain.
6. **Farms are a model.** No citywide map of fields exists before the USGS sheets: ground that
   is city today is cleared outward from the colonial settlements at 12 years per km (seeds
   = towns in `places.csv` founded before 1800), Manhattan no later than 1779 (the British
   occupation stripped it of wood), elsewhere no later than 1860; steep ground and today's
   wooded big parks stay forest. `estimated`; no farmsteads are generated.
7. **The forest of 1609 is drawn** (procedural tree positions in real forest cells, each tree
   gone when its cell is cleared); today's trees stand on real WorldCover canopy pixels.
8. **What stood before** (`nyc_predecessors.py`, rules in its docstring). Evidence order:
   documented lost buildings (OpenHistoricalMap rows with their own end date) > traced map
   layers > generated. Traced layers: NYPL Building Inspector (Perris 1857 Manhattan to
   ~86th St, 1855 Brooklyn, 1890 / 1894 atlases), NYPL's 1854 footprints to 42nd St and
   volunteers' tracings via OHM (Castello Plan 1660, the 1728 survey, Grim 1742, Maerschalck
   1755, Dripps 1852, Sanborn, Bromley). Outline and wall material are real; start, end and
   storeys are estimated. A traced outline that coincides with a standing building is that
   building (re-dated to before its map if its own year was only an estimate). The traced
   layers are incomplete, so absence from a later map is never evidence of demolition; only
   1660 and 1854 count as complete. OHM's dates are used only where its importer
   (`ohm_nyc.py`) found them specific to the building — most are stamps.
   **Before the first atlases** the town is generated (`procedural`): on the outlines of the
   1852-57 atlases (standing in for the lots), inside the built-up extent snapshots
   (`data/manual/extents`), backwards in generations of 45-105 years, thinned so the number
   standing follows the census counts (persons per building 4.5 in 1660 to 13.5 in 1850).
   Above 86th St and outside downtown Brooklyn nothing vanished is drawn yet.
9. **Built data is not committed.** `make data` rebuilds it (about 20 minutes after the
   downloads); `make deploy` ships it. Only `data/manual`, `data/tables`, `data/research` are
   precious.
10. **First view:** Manhattan from the harbour at bearing 29° (the avenues run up the screen).
11. **Made land** (`data/manual/fill_zones.csv`, rules in `fill_README.md`, applied by
    `terrain_tiles.fill_layers`): made land = today's land that the 1609 layer says was
    water, marsh or pond. Coarse zones only date it; precise zones (Lower Manhattan's bands
    along Pearl / Water / Front / South and Greenwich / Washington / West streets, Battery
    Park City …) are painted as drawn. Precise beats coarse, then the earliest end wins;
    land grows outward across a zone's years; made land without a zone appears four years
    before the buildings around it. Reservoirs have lifespans; Thirteenth Avenue is filled
    and cut back. Buildings on made land never predate it (LPC and researched dates stand).
12. **The 1609 layer** (`data/manual/natural/`): tidal marsh, flats, ponds, wetlands, old
    shoreline and 428 km of vanished streams from the NRCS soil survey, the 1891-98 USGS
    sheets and Viele's 1865 map. Dry land without evidence is forest. Streams are one terrain
    cell wide (29 m: a stylisation) and last until the city or a park takes the ground.
13. **Click popups say where a year comes from** (`Evidence`: LPC, city record, assessor's
    rounded year, atlas, OpenHistoricalMap, generated) and name named buildings.
14. **Population counter**: the borough under the map centre when zoomed in, else the five
    boroughs' area; before the first census of the area (1698) the town on Manhattan
    ("New Amsterdam" until September 1664), before 1626 the Lenape estimate.
15. **Landmarks** (`viewer/src/landmarks/nyc-*.ts`, 192 models; dimensions and what is
    estimated per model in `data/research/landmarks_*.md`): 33 bridge models of 24 bridges on
    OpenStreetMap tower and pier positions; 46 towers on the official footprints with OSM
    set-backs and cited heights; 66 civic buildings, churches, museums, forts and stadiums;
    47 lost landmarks (Twin Towers, Penn Station, Crystal Palace, Fort Amsterdam, the Wall,
    ballparks). Each model's `Model:` fact names its estimates and is shown in the popup;
    half of the lost ones are LOW confidence (no published height). One broken model does not
    stop the others (`loadLandmarks` catches it).
16. **Transit** (`transit.py`): subway, Staten Island Railway and the demolished elevated
    lines with trains; railroads as track and station labels only. The viewer's system keys
    are still the Bay's: `bart` = subway / SIR / els, `muni` = railroad stations; vehicle keys
    `bart` = B Division car, `ebart` = A Division car, `el` = elevated car. Elevated routes
    without a traced line follow the centre line of the street they ran above.
17. **Ground detail and airports** (`ground_detail.py`, `airports.py`): OSM outlines dated by
    the park's researched year, else the Parks acquisition date, else the standing buildings
    around (vanished buildings are not counted: they dated plazas to 1851). Airfield
    outlines turn the terrain to grass from their opening year.
18. **Built-up extents** (`data/manual/extents`, per borough): used to bound the start of
    traced buildings and to place the generated pre-atlas town. A snapshot says nothing
    outside its map (Ratzer and Dripps 1852 to 50th St, Colton to 42nd St), and one within
    15 years of an atlas is not a lower bound.

19. **Roads** (`roads.py`): Overture / OpenStreetMap geometry. A street is cut a year before
    the second-earliest building within 45 m (counting vanished ones), never before its ground
    (median land year under it); researched rows (`data/tables/street_dates.csv`: the 1811
    grid, Broadway, the Bowery, Seventh Avenue South …) override. Highways take the opening
    year of the researched row running parallel (`data/manual/routes.csv`, 155 rows) and are
    drawn in 3D from Overture's level / bridge flags; decks under a landmark bridge model are
    left out and their ends pinned to the model's height. Vanished roads, ferries and the
    West Side Elevated Highway are drawn from `routes.csv`. Researched openings are not
    pushed later by the land-year grid (`data/interim/roads/ground_conflicts.csv` lists them).
20. **The published site must stay small.** Deployment times here varied wildly on one day:
    149 MB went through in 8.5 minutes (the first deployment, certificate included), 152 MB
    was cancelled at GitHub Pages' ten-minute limit, 104 MB was live within a minute. Hence:
    tree records to a metre and whole years, overview tiles with 15 % of the trees (the share
    the viewer draws below zoom 12.5), building coordinates in 1e-6 degrees, outlines
    simplified to 0.4 m. Budget: about 110 MB. `pipeline/deploy.py` prints the size; check
    the "pages build and deployment" run afterwards and compare a checksum with the live
    site — a pushed deploy is not a published one (a failed run leaves the old site up).
21. **City ground** (terrain): the second-earliest building within ~45 m, counting vanished
    ones; the extent snapshots fill gaps (built-up ground is city no later than the maps show
    it — above 86th St and in the old towns no traced buildings exist); a park made where the
    city already stood is city ground first; undated greens take the year of the buildings
    standing around them today.

22. **Nothing stands before its ground** (`ground_rule.py`): a building starts no earlier
    than the latest land year of any cell its outline touches, plus the terrain's 2.5-year
    blend and its own construction time. The other direction is evidence: landmark and
    researched dates, outlines traced from dated maps and (two of them) recorded assessor or
    parcel years move a cell's land year back (`nyc_buildings.py evidence`, before
    `terrain_tiles.py land`). The full terrain run reuses the land years of the `land` run,
    so buildings and ground agree by construction. A building that waits for its ground is
    marked `estimated`. Piers are exempt.
23. **Evidence for years, beyond the assessor** (all in `nyc_buildings.py`; popups say which):
    - *Aerial photographs of 1924 and 1951* (`data/manual/aerial`, `aerial_presence.py`): a
      probability per footprint that a building stood on its outline. "Stood" moves a
      placeholder year earlier only outside Manhattan and outside dense blocks (elsewhere the
      photograph may show a predecessor); "open ground" moves it later, except in open
      country and on Staten Island. A year pushed later is spread over five years.
    - *Tenement classes* (`data/manual/records/year_bounds.csv`): old-law by April 1901,
      new-law 1901-1929; a recorded year that breaks its class by three years is a placeholder.
    - *City records* (`known_building_dates.records.csv`): first certificates of occupancy,
      housing authority completion dates; owner-reported years are `estimated`.
    - *Placeholders*: "1931" is a bound ("by 1931"), like 1899 / 1901; a year stamped on five
      or more buildings of an institutional lot, and a year the Department of Finance flags,
      are `estimated`.
    - *Not used as evidence*: a later-dated footprint under an 1890s map mark (a coincidence
      four times in five).
24. **What stood before, additions** (`nyc_extras.py` → `nyc_predecessors.py`): the city's
    retired footprints (42,000 buildings removed 1996-2026, each with its removal year; the
    replacement is re-dated to after it when its own year was an estimate); atlas layers
    traced for this map (`data/manual/atlas`: Harlem 1897, the Bronx's 23rd ward 1887, Kings
    County's towns 1890); the building marks of the 1889 / 1897 USGS sheets as farmsteads
    (position real, outline generated: `procedural`); documented lost buildings of the forts
    and works (`notable_demolished.sites.csv`).
25. **Lenape settlements and the colony's outlying farms** (`data/tables/early_nyc.csv`, notes
    in `data/research/early_nyc.md`): 179 researched sites. The site and its dates are from
    Bolton, Parker, Danckaerts and the Manatus map; the number of dwellings is from a source in
    12 rows and estimated elsewhere; where each dwelling of a cluster stands is generated
    (`procedural`, kept off the water and marsh of 1609; Lenape dwellings are drawn at twice
    their size). Rows that still stand date the standing footprint.
26. **Piers** (`data/manual/piers`): decks and sheds as low platforms over the water, from the
    USGS sheets and charts. None is dated before 1888 (the first sheet), so the port of the
    canal era has no piers.
27. **Military and industrial sites** (`data/manual/sites`): 122 sites with outline, years and
    ground. Yards and works are city ground from their founding, forts and asylum grounds
    open grass; buildings inside a site flagged `floor` are not older than it; labels in
    tier `site`.
28. **Street and park trees** (`street_trees.py`, `data/research/street_trees.md`): the city's
    inventory, 884 k trees; 13 % carry a planting date, the rest are dated from the trunk
    by species (`estimated`). The terrain draws no canopy tree on a cell that holds one.
29. **Farms, woods and parks** (`terrain_tiles.py`; a model, `estimated`): clearing spreads from
    the colonial settlements, later on steep ground (which becomes pasture); steep ground and
    a fifth of the rest (woodlots) stay wooded; today's woods outside parks are second growth
    on fields given up 1882-1937; parks and cemeteries are cleared with their neighbours and
    turn to park when laid out (they are not islands of the forest of 1609); the planting
    grounds beside the Lenape settlements are fields from the start.
30. **Colours** (`nyc_buildings.materials`): where the rules leave a choice it is made once
    per tax block, class and decade, and once per complex for lots with several buildings;
    glazed white brick only from 1950.
31. **The counties** (`county_buildings.py`, own tile set `data/county-buildings`): Overture and
    state footprints with parcel years (`counties_nj.py`: MOD-IV; `counties_ny.py`: the state's
    parcel layer), placeholder years detected per county / assessing unit, the city's
    estimator and ground rule. Landscape of 1609: `data/manual/natural/counties`; made land:
    `data/manual/fill_zones_counties.csv` (coarse rings only date ground the 1609 layer says
    was wet; reservoirs turn today's water cells to water at their year). Streets, highways,
    railroads, PATH and light rail, parks, golf courses, airfields, labels, population:
    the city's stages on the wider box (`common.REGION_BBOX`), each with county rows in its
    tables. The fine terrain grid still covers only the city box: beyond it the ground is
    58 m cells.
32. **Story mode** (`viewer/src/story.ts`, `data/tables/story.csv`): a guided tour — 106 stops,
    about half an hour — that flies from stop to stop, eases the year, shows a caption and
    turns the camera; a stop can let the years run. `?story` starts it at load.

33. **Split hosting** (`pipeline/deploy.py`, `viewer/src/remote.ts`). With the counties the
    build is 194 MB. GitHub Pages cancelled its deployment twice at 147 MB (the sync ran past
    ten minutes; the upload itself took six seconds) and publishes 80-104 MB in about a
    minute. So the whole build is pushed to `gh-pages`, a Jekyll `exclude` written by
    `deploy.py` leaves the three heaviest tile sets out of the Pages build
    (`data/region-buildings`, `data/county-buildings`, `tiles/terrain/13`: 115 MB), and the
    published page reads those from the branch through `raw.githubusercontent.com` (cross-
    origin reads are allowed; JSON arrives as text/plain; the repository must stay public).
    Local builds read everything locally. That host is not a content network and limits
    requests per visitor: if the site gets real traffic, move the tile sets to proper storage.
    Keep the Pages part under 100 MB.

## What is not done (as of 2026-11-10, end of the second round)

- **The tenement generation in the cleared districts.** Lincoln Square has no traced source
  for 1880-1955; East Harlem and the South Bronx have one atlas year each (1897, 1887) and
  nothing between it and the projects. A vanished building with nothing on its spot still
  ends when the big building beside it went up — an estimate, not a researched clearance.
- **Outside lower Manhattan, downtown Brooklyn and the three new atlas areas nothing vanished
  is drawn** except removed buildings since 1996, farmstead marks and the researched sites.
- **Piers before 1888**, and piers as part of the terrain (narrower than a cell).
- **The counties' history**: no vanished buildings, no landmarks; Westchester's 22 undated
  municipalities and Nassau have no buildings; the Hudson shore north of Hastings rests on the
  soil survey alone; the Newark Bay Bridge and the Pulaski Skyway are drawn too low.
- **Landmarks**: no new models in this round; some forts and works are plain documented boxes.
- **Removed trees** are not drawn (the viewer has no end year for trees).
- **LiDAR massing** (`lidar_parts.py`, not ported): towers without OSM parts are flat extrusions.
- **The Harlem USGS sheet's registration** in the city's 1609 layer may be off by tens of
  metres at Hart Island (found by the counties' agent, not corrected).
- Not checked on a real GPU: nothing was looked at on screen in this environment. Checks were
  numeric (`audit.py`, each part's own checks) and a headless boot without console errors.
