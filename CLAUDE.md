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

- **Now:** the five boroughs. Manhattan carries the deepest history (made land, what stood
  before, landmarks); the other boroughs have today's buildings with their years and heights
  and whatever history has been researched so far (see "Status").
- **Later:** the rest of the metropolitan area (the owner's list: Westchester, Rockland, Putnam,
  Suffolk, Nassau, Ulster, Dutchess, Orange, Sullivan NY; Bergen, Hudson, Passaic, Middlesex,
  Monmouth, Ocean, Somerset, Essex, Union, Morris, Sussex, Hunterdon, Mercer NJ; Greater
  Bridgeport and Western Connecticut planning regions; Pike PA). Not started: it needs
  construction years per county (NJ MOD-IV, NY county rolls, CT towns), and the owner prefers
  an accurate city to a thin region.

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
pairs in the city's own footprints are reported, not failed. After a deploy run the second
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
- GitHub Pages cancels a deployment whose file sync runs over ten minutes: keep the site well
  under ~400 MB. After `make deploy`, confirm the live site by comparing a file's checksum — a
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

`download_nyc` · `download_overture` → `footprints_raw` → `extent` → `terrain_grid` →
`nyc_buildings` (+ `nyc_predecessors`) → `terrain_tiles` → `cities`, `transit`, `roads`,
`ground_detail`, `airports` → `audit` (invariants on the built files) → `deploy`.
Tools: `footprint_at.py` (footprints around a point, in the landmark kit's local metres).

Not yet ported from the Bay copy (kept as reference, they do not run): `sf_predecessors.py`,
`region_predecessors.py` (extent fill, clearance corridors), `sanborn_trace.py`,
`topo_farmsteads.py`, `lidar_parts.py`, `ohm_import.py`, `geocode.py`.

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

## What is not done (as of 2026-11)

- **Above 86th St and outside downtown Brooklyn nothing vanished is drawn** before today's
  buildings: no traced atlas exists in the data for Harlem, the Bronx, most of Brooklyn,
  Queens, Staten Island. Candidates: Bromley / Robinson atlases on the NYPL dump (same
  tooling as `data/manual/extents/tools`), the 1924 and 1951 aerials (maps.nyc.gov tiles),
  farmsteads from the 1890s USGS sheets (`topo_farmsteads.py`, not ported).
- **Lenape settlements are labels only**; no dwellings are drawn.
- **Street trees** (the 2015 census, 680 k trees) are not used; today's trees stand on
  WorldCover canopy pixels.
- **LiDAR massing** (`lidar_parts.py`, not ported): towers without OSM parts are flat extrusions.
- **Researched building dates** (`data/tables/known_building_dates.csv`) do not exist yet:
  exempt and institutional buildings carry the assessor's (often heaped) year.
- **Clearance dates** (Lincoln Center, Stuyvesant Town, public housing superblocks, bridge and
  tunnel approaches): a vanished building with nothing on its spot ends when the big
  building beside it went up — an estimate, not a researched clearance.
- **Piers** are not in the terrain (narrower than a cell) and not drawn as structures.
- **The rest of the metropolitan area** (see Scope).
- Not checked on a real GPU: nothing was looked at on screen in this environment (software
  rendering times out). Checks were numeric (`audit.py`, the agents' per-part checks) and a
  headless boot at eight years / views without console errors.
