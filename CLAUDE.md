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
- **But a place that existed must not be empty** (owner, 2026-11-10: "I would prefer generated
  data (within reason) to empty neighborhoods and towns where/when neighborhoods and towns
  actually existed"). Where no outline survives, buildings are generated — only where
  evidence says the ground was built on at that time (a photograph, a map, a census count),
  marked `procedural`, naming that evidence in the popup, and giving way to any real outline.
  The same goes for years: a town whose records carry no construction years is drawn with
  modelled years marked `estimated`, not left out.
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

- **Now:** the five boroughs and 26 counties around them (`data/manual/extent_counties.json`).
  *Inner* (full detail): Hudson, Bergen, Essex, Union and Passaic (New Jersey), Westchester and
  Rockland (New York). *Outer* (a compact tier, decision 39): Nassau, Suffolk, Putnam, Orange,
  Dutchess, Ulster, Sullivan (New York); Middlesex, Monmouth, Ocean, Somerset, Morris, Sussex,
  Hunterdon, Mercer (New Jersey); Greater Bridgeport, Western Connecticut and South Central
  Connecticut (the planning regions that replaced the counties); Pike (Pennsylvania).
  Manhattan carries the deepest history; the inner counties have today's buildings with their
  parcel years, the landscape of 1609, made land, streets, railroads, parks, labels and
  generated rows for what was cleared; the outer counties have today's buildings (houses as
  rectangles) with a year each, thinned trees, the same ground model, highways, stations,
  labels, a few landmarks and their colonial towns. The owner's priority order for accuracy:
  Manhattan > the other boroughs > the inner suburbs > the outer suburbs.
- **Not on the map:** nothing of the owner's list is left out. Beyond it (Litchfield, Hartford,
  the Lehigh Valley, Philadelphia's side of the Delaware) the ground is drawn faded.

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
`county_buildings.py` → `county_buildings.py outer` → `street_trees.py build` → `airports.py` → `terrain_tiles.py` →
`ground_detail.py` → `roads.py` (+ `check`) → `transit.py` → `cities.py` → `nyc_extras.py` →
`audit.py` (about an hour on the wide map). The generated fills read the built files: after a
change to the buildings run the first four stages, then `gap_fill.py fresh assemble report`,
`gap_fill.py counties`, `site_fill.py` and `port_fill.py`, then the whole chain (decisions 34,
36, 44). Other jobs on the machine get killed for memory while it runs, and it them. After a deploy run the second
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
- Headless screenshots work only one way on the build machine: small (760 x 480), through the
  DevTools protocol, with the trees, street tiles and traffic not loaded
  (`viewer/scripts/shots.cjs <url> <out prefix> "<view>" …`; `page.screenshot` never returns
  under software rendering). **Look at what you ship** — the first deployment of the outer
  counties passed every numeric check with no place names, the colonial Princeton 900 m from
  Nassau Street and landmarks nobody could find. Numeric checks first, then a few shots of
  the places that matter, then tell the owner what was and was not looked at.

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

34. **Traced atlas layers and the generated fill** (third pass, 2026-11-10/11; the owner's
    rule "a place that existed must not be empty").
    - *Traced* (`data/manual/atlas/*_YYYY.geojson`, README there per layer; tools per part in
      `tools*/`): Manhattan 40th-125th St (Bromley 1897), Brooklyn's built core (Sanborn-Perris
      1886-88, house by house, nine layers), the South Bronx in three states (1887, 1904,
      1921), Queens' old centres (Hyde 1901 / 1907), Staten Island's north shore (Bromley
      1917), Jersey City (Hopkins 1919), three Hoboken plates (1891). About 359,000 outlines.
      They are not complete inside their coverage. An outline mostly covered by standing
      buildings of the map's time is those buildings (rows are not cut as the lots are);
      sliver-shaped outlines in a roadway are dropped; a layer that fails the lead's street
      check is skipped (`nyc_extras.ATLAS_SKIP`). Where no earlier map or extent bounds a
      traced building's start, it follows the borough's or county's census growth up to the
      map year, nearest the old centres first.
    - *Generated* (`pipeline/gap_fill.py` -> `data/interim/gapfill/gapfill*.parquet`,
      `data/manual/gapfill/README.md`): lot-sized outlines along today's block frontages,
      kept only where the 1924 or 1951 aerial photograph shows a building on the lot, where a
      dated map's built-up area covers the block (a share measured against the traced
      atlases), or — Hudson County — where the 1940s USGS sheets draw the block front as
      built. `procedural`, lowest rank, the popup names the evidence. Order: build the
      building files, run `gap_fill.py fresh assemble report`, build again. False rows are
      expected in the thousands in leafy suburbs; no hand-checked precision figure exists.
    - *The other six counties* (`gap_fill.py counties` -> `gapfill_counties.parquet`, 71,000 rows): on
      the states' real parcels, where the parcel's building is 25 or more years younger than a
      neighbourhood built up before 1945 (the Bay project's rule), or a 1940s / 1897 USGS sheet
      shows the ground built. `procedural`.
    - Vanished structures outside the city are held against the counties' standing buildings.
35. **Modelled years where the roll has none** (`counties_ny_estimates.py`,
    `data/research/counties_ny_estimates.md`): 139,000 Westchester and 4,500 Rockland
    footprints take a year from the census's count of homes by decade built per block group;
    the pre-1940 stock follows the ages of the county's recorded buildings. Validated with
    the dated towns' years hidden: median error 21 years, a third in the right decade.
    `estimated`, source `modelled`.

36. **Yards, forts and institutions** (2026-11-11; the owner: "the Brooklyn Navy Yard is too
    empty for too long. Fix it and fix other similar military/industrial sites"). Three causes,
    three fixes:
    - *Lot stamps.* A year stamped on five or more buildings of an institutional lot is dropped
      (not kept as an estimate): the building is dated like one without a year — the photographs,
      the site's founding, its neighbours. One that a photograph shows standing is spread over
      up to 45 years before it (`evidence_by:`), not stacked at the photograph.
    - *Research* (`data/research/navy_yard.md`, `sites_buildings.md`, `industry_buildings.md`):
      the Navy Yard from its National Register inventory and the yard plans of 1872, 1890 and
      1946 registered on standing buildings (50 standing buildings dated, 34 lost ones, 25 with
      an outline traced from a plan, ±8-15 m); Fort Wadsworth, Rikers Island's jails, Floyd
      Bennett Field and others (41 dated); Bush Terminal's lofts. Written sources date few
      buildings of such sites and place almost no lost ones: this route is exhausted quickly.
    - *Roofs read off the photographs* (`pipeline/site_fill.py` -> `gapfill_sites.parquet`): inside
      the sites of `data/manual/sites` each aerial photograph (1924, 1951) is segmented; a
      building-sized patch that fills its bounding rectangle and that the presence model reads
      as a standing building, where the map has none, becomes a building: outline approximate
      (a rectangle on the roof), years estimated (spread back up to 60 years, not before the
      site's founding), `procedural`, lowest rank. `site_fill.py look site=<id>` draws them on
      the photographs: that is how they were checked (by eye, on four sites; no precision figure).
    - Order of a full rebuild: build the building files → `gap_fill.py fresh assemble report` →
      `site_fill.py` → build again.
    - Limits: nothing before the 1860s is added (a roof of 1924 is not spread back further),
      sites outside the city have no photographs, piers and dry docks are not buildings.
37. **Undated made land is dated from the buildings' own years, not their waiting years.** Made
    land without a zone appears four years before the second-earliest building around it. That
    used the built years, which had already waited for the land: every rebuild pushed land and
    buildings about half a year later (Bush Terminal's lofts of 1904-14 stood at 1931-35). The
    building points carry `start_free` (the year before the ground rule moved it) and the
    terrain uses that. A researched estimate (`known_est`) is ground evidence like a roll year.
    Under a building of 300 m² or more the land is no younger than that building
    (`terrain_tiles.own_years`): a point stands for one cell, a factory covers twenty, and the
    nearest point to its far corner may be a new neighbour's.
38. **A generated row must never pass for a real one** (found 2026-11-11). The fill's rows
    enter the vanished-buildings stage as class `documented`; the label test for that class ran
    first, so every one of them was labelled as an OpenHistoricalMap record (the popup named
    the wrong evidence on the site of 2026-11-10), and `gap_fill.py`'s snapshot of "what the
    map has" then held the fill's own earlier rows: a rerun filled around them instead of
    replacing them. The label is `gapfill:<evidence>` again and the snapshot leaves out any
    `procedural` row. After a change to the fill, check
    `select year_src, count(*) ... where year_confidence = 'procedural'` on the built file.

39. **The outer counties are a compact tier** (round of 2026-11-11; the owner: "add the rest of
    the counties now … compress the houses and tree procedural generation if you must"). One box
    for everything, `common.REGION_BBOX` = `OUTER_BBOX` = (-75.37, 39.47, -71.85, 42.20).
    - *Buildings* (`county_buildings.py outer` → `data/outer-buildings`, one county file at a
      time): 3.01 million, 68 MB, 22.5 bytes a building. A house under 500 m² that fills 55 % of
      its smallest enclosing rectangle is drawn as that rectangle with the outline's area;
      nothing under 60 m²; corners to half a metre (`building_binary.COMPACT_SCALE`), years to a
      quarter, heights to half a metre, a one-byte id. Larger buildings keep their outline,
      simplified to 1.2 m. The inner counties' set is unchanged.
    - *Trees*: outside `terrain_tiles.INNER_BBOX` 30 % of the canopy trees, drawn 1.6 times as
      large. *Ground detail* outside it: outlines of 5,000 m² and more.
    - *Tables with outer rows*, read by the city's stages: `places_outer.csv`,
      `population_outer.csv`, `transit_stations_outer.csv`, `airports_outer.csv`,
      `data/manual/routes_outer.csv`, `fill_zones_outer.csv` (137 reservoirs),
      `landmarks_bridges_hudson.csv`. Place coordinates were checked against the Census
      gazetteer (the agents' own were from memory and up to kilometres off).
    - *Hosting*: `deploy.py`'s list of sets read from the branch now also holds
      `data/outer-buildings`, `data/region-streets`, `data/region-trees` and
      `data/region-ground-detail.bin.gz`. The build is 391 MB: 87 MB through Pages, 304 MB
      read from the branch.
    - *Viewer*: the tiled layers (terrain, buildings, streets) ask for tiles inside
      `extent.ts MAP_BOX`, which must be the pipeline's `REGION_BBOX`. It was the inner
      counties' box in three places: the first deployment of the outer counties published
      their data and drew none of it. `check-years.cjs` counts the outer tiles fetched
      (run the outer views alone — after the inner ones the software renderer's queue is
      still busy and the count reads 0).
40. **Years in the outer counties** (`data/research/county_years.md`, `counties_*.md`). The
    owner: "I don't believe that you actually have to model 100% for any county. There must be
    some data somewhere" — there was. New Jersey: MOD-IV. New York: the state parcel layer and
    the State's parcel centroid points (Dutchess: 87 % recorded). Connecticut: the towns' CAMA
    files (`AYB`). Where a roll publishes no year — Nassau, Brookhaven — the building takes one
    from HISDAC-US's counts of buildings by five-year period in its 250 m cell (built from the
    assessors' own records; source `modelled_cells`). Islip, Huntington, Babylon, East Hampton,
    Southold and Pike County still rest on the census model of decision 35 (`modelled`).
    Overall 43 % recorded, 57 % `estimated`. None of the Long Island years was validated
    against a hidden sample.
41. **The wide terrain is worked in windows** (`terrain_tiles.histories_whole`). The region grid
    is 5,377 × 5,249 cells of 58 m; every change of cover is a pair of full arrays, so it is
    computed in 9 windows (32-tile cores, 3-tile margins) and the cores are put together. The
    noise is the whole grid's (`_H_OFF`), so fields and woodlots run across a window's edge.
    Tiles beyond the outline are not written. All reservoirs are one change of cover and all
    airfields one (one each ran the densest window out of memory). The fine grid still covers
    only the city box.
42. **Farmland follows the censuses** (`terrain_tiles.farm_census`,
    `data/tables/farmland_counties.csv`, `data/research/farmland.md`; the owner: "was there
    *that* much farming in 1820? like the entire metro area?" — no). The model of decision 29
    keeps its order of clearing; the share of each county that is cleared at 1820, 1850 and
    1880 is set to the census's improved acreage (Ocean 7 % at its peak, Pike 6 %, Sussex 24 %
    in 1820 and 45 % in 1850, Somerset 71 %). The run logs every county's figures.
43. **Districts that were cleared and rebuilt** (`gap_fill.py counties` → `cleared_blocks()`,
    `data/manual/gapfill/cleared_districts.geojson`: 14 districts, Newark's Central Ward
    first; the owner: "appear before they were destroyed and are not just farmland until the
    90s"). Inside a district every block front carries generated lots from the district's
    building-up to its clearance (`procedural`, the popup names the evidence); the counties'
    built-up areas of the 1897 and 1940s USGS sheets (`counties_builtup_1897.geojson`,
    `counties_tint_194x.geojson`) date the city ground. `gapfill_counties.parquet`: 110,000 rows.
44. **Ports, rail yards and other working ground** (`port_fill.py`, `data/manual/ports/`: 7
    container terminals, 18 yards; `gapfill_ports.parquet`, 9,800 rows, read only when
    `gapfill_ports.ok` exists). Container stacks and standing railroad cars from the
    terminal's or yard's opening year: the terminal and its year are real, positions, sizes and
    colours generated (`procedural`, material 16 `containers`, the popup says so). Airfields
    are mown grass (green, not the dry yellow of open ground).
45. **Piers reach the land** (`nyc_extras._to_land`): a deck whose landward end stands in the
    water of its own year is carried to the shore (up to 96 m: three terrain cells); 780 decks.
    The shore is the terrain's, so a pier can still end a cell short on screen.
46. **Things on decks** (`ground_detail.deck_floor`, `data/research/features_on_decks.md`):
    pitches, tracks and courts on a landmark's roof deck (Riverbank State Park, Pier 40,
    Brooklyn Bridge Park's piers) are drawn at the deck's height, not under it.
47. **A low apartment building is not a row house**: building class D is never `small_res`
    (Co-op City's garden apartments were coloured and labelled as row houses).
48. **Effects** (`viewer/src/layers/effects.ts`, `data/tables/effects.csv`: 186 rows;
    `effects_README.md`): fires, explosions, battles (columns moving, clashes), fleets and
    collapses as animated marks at their dates, two flat layers driven from the traffic clock.
    Dates and places are largely from general knowledge (`estimated` in the table), not from
    opened sources. A failure in the layer switches it off rather than the map (`fxBroken`).
49. **The counties' colonial towns** (`data/tables/early_counties.csv`: 161 towns, 1,065 rows;
    `nyc_extras.early_sites`): as decision 25 — the town and its founding are researched (from
    general knowledge, see the note), the houses and where each stands are generated. A row is
    the dwellings a town added between two counts, dated at the middle of the span: each house
    takes its own year within the span (stacked at the midpoint, 4,600 houses appeared in 1770
    and as many in 1810 and 1835 — the audit's "spike years", which should be an empty list).
50. **Story and page** (the owner's requests of 2026-11-11): 217 stops (stops outside the map's
    outline are dropped at start); pace 0.62 of the written seconds, flights 1.7-5.2 s; a stop
    is approached up to 8 years early so that what it shows appears while it is on screen; events
    that are not buildings are stops too. The Story button stands between Play and the slider
    and starts at the slider's year — at 1609 only while the page still stands at the 1900 it
    loaded with. The sources are a small "i" in the corner.
51. **Landmarks, second pass** (`nyc-more-{a,b,c}.ts`, `nj-inner.ts`, `nj-outer.ts`,
    `ny-hudson.ts`, `ny-long-island.ts`, `ct.ts`; notes `data/research/landmarks_*.md`): about
    120 models — the High Line, the Farley Building / Moynihan Train Hall, the Brooklyn Tower
    on the Dime, Riverbank State Park, Pier 40; Newark, Jersey City, Princeton, Trenton, West
    Point, Kykuit, Sleepy Hollow, Oheka Castle, New Haven and Yale, the Hudson's bridges. A
    model outside the map's outline is not built (`loadLandmarks`).

52. **The towns round: Princeton and New Haven** (2026-11-11; the owner: "The outer counties
    aren't labeled and a lot of the data (building dates etc) looks fake and there are no
    landmarks. Double check especially important towns like Princeton and New Haven";
    `docs/TOWNS_ROUND.md`). What was wrong, and what was done:
    - *No names*: the label layer never read `places_outer.csv`. It does now, and
      `places_auto.py` adds 3,180 villages, hamlets and neighbourhoods of the outer counties
      (`places_outer_auto.csv`, tier `hamlet` new): name and position are OpenStreetMap's place
      points (Overture divisions), each shown from the year a twentieth of today's buildings
      within 600 m stand on the map (`estimated`).
    - *Town centres*: `places_outer.csv` held the Census gazetteer's interior point of each
      municipality — Princeton's lies 900 m from Nassau Street. 122 of 230 places moved to
      the place point (`data/tables/tools/recentre_places.py`), and the colonial towns were
      regenerated around them (`data/research/early_counties_build`: `rot2.py`, `shift.py`,
      `gen.py`). A table's coordinates are checked against a second source **and looked at**.
    - *Landmarks*: the 16 models were drawn but few, small and lost among flat blocks.
      `princeton.ts` (14) and `new-haven.ts` (18) add the buildings the towns are known by;
      most heights are estimated from storeys (each `Model:` fact says so), and some cited
      figures of the Princeton part come from search-result snippets, not opened pages.
    - *Years*: a university pays no tax, so the roll has no year for its buildings (Princeton:
      136 of the 145 footprints over 1,500 m² undated; Jadwin Gymnasium of 1969 stood at 1911),
      and New Haven's assessor writes 1900, 1910 or 1920 for 60 % of the city. Researched rows
      (`known_building_dates.princeton.csv`: 83; `.new_haven.csv`: 17; each from an opened
      page) date the named campus and civic buildings; the rest stays `estimated`.
    - *Counter*: before a county's first census count it shows no number (it showed New York
      City's).
    - **Connecticut's historic resources inventory (ConnCRIS)**, found by the New Haven part: a
      public point layer of the State Historic Preservation Office with a construction date
      per surveyed building. Its licence is CC BY-NC-ND; the owner allowed it ("Do all of those
      things then", 2026-11-11) — used with attribution (the page's sources, `SOURCES.md`), only
      the year enters the map, the layer is not republished. See decision 53.

53. **The towns round, second pass** (2026-11-11, evening; the owner: "Do all of those things
    then" — the list of what was still weak).
    - *ConnCRIS in bulk* (`pipeline/conncris.py fetch` / `build` →
      `data/interim/counties/ct_<region>_inventory.parquet`, read by `county_buildings.load()`):
      36,380 points in the map's 39 Connecticut towns. A footprint whose assessor year is a
      placeholder or missing takes the inventory's: about 4,200 plain years (`exact`, source
      `historic_register`) and 7,400 "circa" or round ones (`estimated`, source
      `historic_register_ca`, spread over six years). Several points in one footprint must
      agree within five years. A recorded assessor year is never replaced: where both exist
      they agree within two years in 57-70 % (points on the neighbour's building, rounded
      years). New York's CRIS "circa" years (`year_hist_ca`) are used the same way now.
    - *Small piles at round years are placeholders* (`county_buildings.county_heaps`): an
      assessor who does not know writes 1800 for 100-250 old houses of a county where the
      years around hold two or three; too few for the city's rule (300 buildings), enough to
      put 2,400 buildings in 1800 — the audit's spike — and the modelled years, which follow
      the recorded ones, copied the pile. A decade year before 1900 with 15 buildings and four
      times the median of the plain years within four of it is a placeholder in the counties.
    - *Buildings re-dated from an atlas wait for their ground* (`nyc_predecessors.py`): 69 of the
      78 buildings the audit found before their ground were standing buildings moved to
      before the map that shows them, after the ground rule had run. `audit.py` now reports
      which kinds of rows stand before their ground (`before_ground_by_source`).
    - *Greens* (`nyc_extras.on_green`): no generated colonial dwelling stands on a town green,
      a common or a burying ground of today's map (715 outlines from Overture's land use).
    - *More towns* (same pass as decision 52, one agent per pair; notes `data/research/towns_*.md`,
      `princeton_yale_round2.md`): researched years for 20 more footprints at Princeton and
      Yale, 100 at Stamford and Bridgeport, 49 at West Point and Poughkeepsie, and those of
      Trenton and New Brunswick (`known_building_dates.{princeton2,new_haven2,ct_towns,
      hudson_towns,trenton_nb}.csv`); landmark models `ct-towns.ts` (14), `ny-towns.ts` (18),
      `nj-towns.ts`. About 14 of the 32 models of decision 52 carry a cited height; the rest
      say what is estimated. Wikipedia rate-limits this machine (fetch raw wikitext, slowly);
      Princeton's and West Point's own sites refuse it.

54. **Build-out order, the Hudson waterfront, a light default** (2026-11-11, night; the owner:
    "the years of the buildings seem fake. think much harder about the order in which all of
    these towns were actually built out, the patterns of farmland and forest over time …
    surely some kind of maps exist in the past? also a lot of Jersey City and Hoboken are
    empty before the modern era"; `docs/ROUND3.md`).
    - *Maps of 1946-61* (`data/manual/gapfill/all_tint_{1949,1957}.geojson`,
      `all_woodland_{1949,1957}.geojson`, `outer_tint_1949.geojson`; tool
      `gapfill/tools/usgs_epochs.py`; `data/research/usgs_epochs.md`): the urban tint and the
      green woodland tint of the Army Map Service's 1:250,000 sheets, for all 31 areas,
      registered to about 50 m. Validated on buildings with a recorded year: 5.8-7.4 % of those
      older than the map lie in its woodland; the tint shows towns, not farms (recall 37-45 %),
      and in the inner counties it covers whole conurbations (it dates nothing there). The
      1890s sheets could not be read reliably in the outer counties (no tint; black ink is
      railways and labels as much as towns): not done.
    - *Estimated years follow the maps* (`county_buildings.order_by_maps`, `map_epochs`): within
      a square kilometre and one kind of estimate (census model, counts per cell, neighbours; a
      "by" placeholder among the buildings that carry the same one) the years are dealt out
      again so that buildings on ground an older map shows built up (1897, 1940s, 1949, 1957)
      take the earliest. The square's set of years does not change; recorded years are not
      touched. It orders, it does not date.
    - *Standing on a traced atlas* (`county_buildings.on_atlas`, Hudson County): a standing
      building that coincides with an outline of the 1919 Jersey City atlas (or Hoboken 1891,
      the Heights 1873) and has only an estimated year is dated to before the atlas (978
      buildings; source `on_map`). Hudson's roll has a real year for one building in four.
    - *The woods of 1957 in the terrain* (`terrain_tiles.woods_of_1957`): open then and wooded
      today — the woods came back after 1957, not in 1882-1937; wooded then and built on
      since — the field goes back to woods before the houses come.
    - *The lost railroad yards of the Hudson waterfront* (`data/manual/ports/yards_historic.geojson`,
      `data/research/hudson_waterfront.md`): nine rail properties with opening and closing
      years; outlines hand-drawn from today's streets and the 1919 layer (50-150 m).
      `port_fill.py` draws parallel tracks in the six that are gone and stands cars on them
      until the yard closed (5,008 cars, `procedural`). `notable_demolished.hudson.csv`: nine
      lost terminals as boxes of estimated size. `port_fill.py` no longer takes its own rows
      of the run before as obstacles (a rerun stood nothing on yards that already had cars).
    - *Not done there*: no more of Hoboken was traced (the Library of Congress's site was
      down; the scans of the three plates of 1891 are gone from the machine); the
      Hamburg-American piers, Colgate, Stevens Castle and Maxwell House have no opened source
      that places them within 40 m.
    - *The page*: effects (`effects.ts`) are drawn only while the guided tour runs, and only
      fires, explosions and collapses — the troop columns, clashes and fleets are gone (the
      owner). By default the page loads the **core**: the five boroughs and Hudson County
      (`scope.ts`, `extent.py core_ring` → `core-extent.json`); "Show the whole region" loads
      the counties (remembered on the device; a link into the counties opens them). Everything
      that asks the extent follows; the region's elevation grid, ground detail and outer
      building index are not loaded in the core. Local streets are drawn darker (they were in
      `region-streets` for the outer counties all along and did not read on suburban ground).
    - *The counter* (`cities.py`, `tables.ts localPopulationAt`): below zoom 9.3 the
      metropolitan area (the sum of every county's series on the map, from 1790); from zoom
      11.3 outside the city the town under the centre of the map
      (`pipeline/town_population.py` → `data/tables/population_towns.csv`: the census counts
      of the municipalities from the `US Census population` template of their Wikipedia
      articles, fetched slowly; outlines: TIGER county subdivisions,
      `data/interim/towns/towns.parquet`); between, the county. No neighbourhood figures: no
      historical series exists for them.

55. **The places that were missing their past** (2026-11-12; the owner: "fix Hoboken, and any
    other towns (or parts of NYC proper) that are missing information in the past";
    `docs/ROUND4.md`).
    - *Measured first* (`pipeline/holes.py` → `data/interim/reports/holes.csv`,
      `holes_by_place.csv`): ground that is city in a year with no building standing within
      60 m, per place and year. It found what nobody had guessed: Newark's Central Ward after
      its clearance (324 ha in one piece in 1980), Brooklyn in 1860 (229 ha), the Bronx from
      1940 (Rikers Island, Freedomland's ground, Hunts Point), Staten Island, Paterson. It
      marks a building by its centre, so large sheds leave false holes; streets, squares and
      rail lines read as holes too. A list for looking, not a rule. Hoboken has no such hole:
      its gap was bare made land in the west and south with nothing on it at all.
    - *Hoboken* (`data/manual/atlas/hudson_hoboken_b_1891`, `hudson_hoboken_1930`;
      `data/research/hoboken_atlas.md`): the Sanborn atlas at the Library of Congress, placed
      by street crossings — the 11 plates of 1891 not traced before (1,175 outlines) and the
      1930 re-issue corrected with pasted slips to 1951 (1,990 outlines on 33 sheets: "stood
      by 1930, a few by 1951"). With the three plates of before, 85 % of Hoboken's built area
      has real outlines. The west side is empty on the 1891 plates (laid-out lots): it was
      built between then and 1930. Rows of attached houses are one outline; the piers,
      shipyards and the north end are not covered; Weehawken, Union City and West New York
      were not started.
    - *Manhattan south of 40th Street* (`manhattan_downtown_1897`,
      `data/research/manhattan_downtown_atlas.md`): the plates of Bromley's 1897 atlas the
      midtown layer had left, 41,254 outlines on 20 plates — one state of 1897 from the Battery
      to 125th Street. 8,988 stand where the map had nothing in 1897; 14,937 coincide with
      Perris rows of 1854-57. 18 % lie within 8 m of a street line (28-33 % below Houston
      Street, where the Perris outlines give 27-46 %: narrow streets, not registration).
      Inwood's plate could not be registered (10 m off; almost unbuilt in 1897).
    - *Brooklyn* (`brooklyn_{sunsetpark,redhook,heights,williamsburg}_1898`, tool
      `tools_brooklyn2/`): Bromley's 1898 atlas outside the layers of 1886-90 — 21,755
      outlines (Sunset Park and the Bush Terminal shore 4,933, Red Hook 1,631, the Heights and
      the old core 2,541, east Williamsburg 12,650); the outlines that coincide with standing
      buildings sit 1.5-2.5 m off. `brooklyn_bayridge_1898` is not used (`ATLAS_SKIP`: half its
      plates could not be placed). Coney Island and a state before 1880 were not done.
    - *The generated lots follow their town* (`nyc_extras._town_starts`): within a municipality
      the fill's lots keep their order and start along its census curve up to its peak, never
      after the lot's evidence (79,000 lots; Hoboken: 2,542 standing in 1900 against 1,559).
    - *The 20th century's holes* (`data/research/holes_boroughs.md`, `holes_nj_cities.md`):
      32 lost buildings in the Bronx, Queens and Staten Island (Shooters Island's shipyard
      sheds, traced on the 1924 photograph; 23 tanks of the Gulf Oil terminal at Bloomfield,
      read off the 1951 one; `notable_demolished.boroughs2.csv`), eight dates (the Hunts Point
      markets 1967 and 1974, Rikers), five ground sites (Rikers' fields, Freedomland's ground);
      Giants Stadium and the Meadowlands Arena; the Central Ward's clearance runs to 1990 (it
      ended in 1975: the cause of the 324 ha), Route 78's to 1985, Paterson's Route 80 to 1966.
      Much of what is left is real: the Central Ward after 1967, Liberty State Park's interior
      after the yards closed, landfills, parking fields, marsh.

56. **The rest of the missing past: traced where a plate could be placed, generated where not**
    (2026-11-12, second round; the owner: "bro go do it. procedurally generate it based off
    your best guess if you need to"; `docs/ROUND5.md`).
    - *Traced* (eight layers, 37,700 outlines; `data/research/brooklyn_atlas3.md`,
      `boroughs_atlas3.md`, `nj_cities_atlas.md`): Brooklyn's old city where the Sanborn
      volumes have no plate (`brooklyn_old_1880`, Hopkins, 300 ft to the inch — a row is one
      outline; 2,174), Bay Ridge (`brooklyn_bayridge_1905`, Hyde; 7,239), Coney Island's edges
      (`brooklyn_coney_1907`, Hyde; 2,613 — the plates of West Brighton itself could not be
      placed), the Bronx east of the Bronx River and its north (`bronx_east_1905`,
      `bronx_north_1905`, Bromley; 5,471 on 36 of 95 plates), southern Staten Island
      (`staten_island_south_1917`, Bromley; 12,080 on 49 of 65 plates, about 70 % of the drawn
      houses found, outlines ragged), Paterson (`passaic_paterson_1915`, Sanborn vol. 1 at the
      Library of Congress; 6,201 on 53 sheets, 23 % of the city's built area, placed by
      matching the traced mask to today's footprints) and a corner of Newark
      (`essex_newark_1908`; 1,908 on 11 sheets — the Central Ward's sheets were not placed).
      The lead's street check (centres within 8 m of a centre line): 2-11 %.
    - *Census fill* (`pipeline/census_fill.py` → `gapfill_census.parquet`, 169,448 rows;
      `data/research/census_fill.md`): where a borough or a municipality of the inner counties
      holds fewer buildings in a census year than its count needs (persons per building from
      the household size of the year and the density of its built-up ground, fitted on the
      places with a complete atlas — Manhattan 1860 / 1900, Hoboken, Jersey City; trigger:
      under 75 % of the need, filled to 85 %), lot-sized outlines along today's street fronts,
      on ground the terrain calls city, holes first and outward from the old centre, started
      in the decade before the census that asks for them, ended when a row of the map takes
      the lot (else spread over 1960-1995). `procedural`, evidence `census+ground`, the popup
      says so. Bronx 29,007, Brooklyn 17,604 (all before 1860), Yonkers 13,602, Newark 12,930,
      Queens 11,572, Paterson 9,619. It sees places, not neighbourhoods; Manhattan and the
      outer counties are not filled; farmhouses on farmland are not its business.
    - *Districts filled by a best guess* (`census_fill.py districts`,
      `data/manual/gapfill/guess_districts.geojson` → `gapfill_districts.parquet`, 7,072 rows):
      Coney Island's West Brighton (1,591 written, 951 in the map), Rockaway Beach (2,678 /
      2,673), Arverne-Edgemere (2,711 / 2,493), Inwood before the subway (92). The share of a district's street-front lots built on, by
      year, is the lead's guess from general knowledge of the place (the file says what each
      rests on): not a measured figure, no opened source. Evidence `guess+<district>`; the
      popup says "a best guess … position, size and years are invented".
    - *Lost works by best guess* (`notable_demolished.best_guess.csv`, 143 rows, every note
      starting "BEST GUESS:"; `data/research/lost_works_best_guess.md`): the Kearny works,
      Singer at Elizabethport, Colgate, the Hoboken piers, Maxwell House, Stevens Castle,
      Roosevelt and Ruppert stadiums, Freedomland, Port Ivory, the Arthur Kill tanks, Newark's
      housing towers, the Paterson locomotive shops. Positions ±8 m (tanks read off the 1951
      photograph) to ±500 m (the Newark towers); every plan inside the New Jersey works is
      invented.
    - *The resorts' sand* (`fill_zones.csv`: `bk_coney_west_brighton_sand` 1865-80,
      `qn_rockaway_beach_sand` 1876-90, `qn_arverne_edgemere_sand` 1886-1900; coarse, best
      guess): the soil survey maps the barrier beach as made land and the terrain dated it
      from today's buildings (median 1918 at West Brighton), so the first build moved 518 of
      Coney Island's guessed hotels of the 1880s into the 1920s-40s and dropped 400. The
      rings date the sand to the resorts' building-up; and a lot of the census or district
      fill whose ground comes more than 8 years after it is dropped, never moved
      (`nyc_predecessors.py`; 1,514 lots). Coney Island's rows north of Mermaid Avenue
      (marsh until the 1900s) are among them.
    - *Result* (`holes.py`, hectares of built-up ground with no building within 60 m, before
      → after): 1860 184 → 87, 1880 293 → 219, 1900 626 → 409, 1920 578 → 411; Brooklyn 1860
      145 → 58, Paterson 1900 44 → 0, Elizabeth 1900 24 → 7, Staten Island 1900 44 → 22.
      Buildings standing: 1850 155,000 → 169,000, 1900 622,000 → 681,000, 1925 1.36 → 1.46
      million. Audit of 2026-11-12: 6,140,661 buildings, 0 with start >= end, 0 out of range,
      no spike year, 12 before their ground, 7,174 overlapping pairs (6,526 before: not
      looked into). Looked at on screen: Brooklyn around Fort Greene in 1860, Coney Island
      in 1890, Rockaway Beach in 1900 — nothing else, and nothing on a real GPU.
    - **Recount one figure of every agent's report yourself.** The first census fill tested
      its lots against the `lon` / `lat` columns of `nyc_buildings.parquet`, which are empty
      for many vanished and generated rows: they were missing from its collision test (in
      the Coney Island box it saw 2,841 of 5,839 rows) and its "0 overlaps" was unproven. It showed only when the district fill
      reported 14 buildings where a plain count of the points file gives 294. The loader takes
      rows by geometry now and the whole fill was rerun.
    - *Order of a full rebuild now*: the first four stages without the markers
      `gapfill_census.ok` / `gapfill_districts.ok` (the fill must not count itself) →
      `census_fill.py points`, `assign`, `table`, `urban_area`, `model_table`, per place
      `cands` + `select` (`run_cf.sh`, `run_county`), `collect`, `districts` (8 minutes in
      all) → `touch` the markers → the whole chain. `gap_fill.py`, `site_fill.py` and
      `port_fill.py` were not rerun this round: their rows give way to the new traced
      outlines in the build.

## What is not done (as of 2026-11-12)

- **Between the atlases and 1996** nothing real shows what stood: one atlas state per
  district (two or three in the South Bronx), then the photographs of 1924 and 1951 as
  generated lots, then the city's removals from 1996. Clearance dates are records only for
  housing projects, parks and highways.
- **Traced layers still missing**: Inwood and Coney Island's centre (generated by a best
  guess only, decision 56); Brooklyn before 1880 inside the Sanborn volumes' ground (the
  1880 outlines there were clipped away: one state per block) and before 1855 anywhere; 59
  of the 95 plates of the 1905 Bronx atlas (not registered) and the Bronx of 1898; 16 plates
  of Staten Island; Flushing's centre (the only plates are too coarse), College Point,
  Whitestone, Corona, Richmond Hill, the Rockaway beach towns (best guess only); Hoboken's
  piers, shipyards and north end, Weehawken, Union City, West New York, Bayonne; Paterson
  beyond volume 1 of 1915 (77 % of its built area) and before 1915; Newark beyond 11
  sheets of 1908 (the Central Ward, the Ironbound, downtown). Manhattan has one state
  (1897) between 1857 and 1996. Storeys were not read off any atlas.
- **Lost works** (decisions 55, 56): the Kearny works, Singer, Colgate, the Hoboken piers,
  Stevens Castle, the stadiums, Freedomland, Port Ivory and the tank farms stand where a
  best guess puts them (±8 m to ±500 m, plans invented); Lorillard, Hayes Homes, the
  Holland America pier, Federal's Port Newark yard and about half the Arthur Kill tanks are
  not placed at all.
- **The census fill** (decision 56) is a model with six calibration points; Brooklyn in
  1860 south and east of Fort Greene and the Bronx around 1910-20 are its least certain
  parts; nothing in it was checked against a photograph or a map of the lot.
- **Yards, forts and institutions before the 1860s**: only researched buildings (decision 36);
  Fort Hamilton, Fort Schuyler, Fort Tilden, Governors Island's lost buildings, Hart Island,
  Creedmoor, Kings County and the other hospital campuses were not researched building by
  building; the Navy Yard's 1946 plan still holds about 150 untraced buildings.
- **Piers before 1888**, and piers as part of the terrain (narrower than a cell).
- **The counties' history**: vanished buildings only as generated rows (decisions 34, 43); the
  Hudson shore north of Hastings rests on the soil survey alone; the Newark Bay Bridge and the
  Pulaski Skyway are drawn too low.
- **The outer counties**: no vanished buildings outside the cleared districts and the colonial
  towns; no 1609 layer of their own (dry land is forest, today's water is water, no vanished
  streams or marsh); demolished railroads and trolleys are not drawn (the cached
  OpenHistoricalMap rail extract covers the old box: delete `ohm_rail_region.json` under
  `data/raw` to refetch); closed airfields have no outline; six Suffolk towns and Pike County
  have census-modelled years.
- **Princeton and New Haven** (decision 52): about fifteen of Princeton's large campus
  footprints still have no opened source for their year (Schmidt Hall, MacMillan, the garages,
  DeNunzio Pool …); in New Haven the inventory covers the surveyed buildings only, so most
  placeholder years outside the historic districts remain spread; City Hall, the Peabody, the
  Shubert, 101 College Street are undated; the Yale Repertory Theatre is 1846 on Wikipedia and
  1871 in the inventory (unresolved); Harkness Tower's position is good to about 15 m.
- **The other towns** (decision 53): West Point's Eisenhower Hall and three more of its
  largest buildings, Poughkeepsie's factories, Stamford's One Stamford Forum, Marriott and
  Harbor Point blocks and Bridgeport's hospitals and university are undated or unmatched;
  most model heights there are from the footprint or estimated; the PSEG stack, the Perry
  Arch and the Stamford station are not modelled.
- **Large empty working ground**: the 25 largest empty patches (tank farms, quarries, depots)
  listed by the ports part were not filled.
- **Effects and the colonial towns of the counties** rest on general knowledge, not opened
  sources; the story's event captions were not checked line by line.
- **Landmarks**: some forts and works are plain documented boxes.
- **Removed trees** are not drawn (the viewer has no end year for trees).
- **LiDAR massing** (`lidar_parts.py`, not ported): towers without OSM parts are flat extrusions.
- **The Harlem USGS sheet's registration** in the city's 1609 layer may be off by tens of
  metres at Hart Island (found by the counties' agent, not corrected).
- **The audit of 2026-11-12** (6,140,661 buildings): 12 buildings stand before their ground
  (one each of a dozen kinds of rows: not looked into); 7,174 overlapping pairs, 650 more
  than before this round (not looked into: probably generated lots against outlines traced
  this round that overlap them by less than 40 %).
- Not checked on a real GPU: nothing was looked at on screen in this environment. Checks were
  numeric (`audit.py`, each part's own checks) and a headless boot without console errors.
