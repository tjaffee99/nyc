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
8. **What stood before** (`nyc_predecessors.py`): NYPL Building Inspector footprints (Perris
   1857 Manhattan to ~86th St, 1855 Brooklyn, 1890 / 1894 atlases). Outline and wall material
   are real; start, end and storeys are estimated by the rules in the docstring. A traced
   outline that coincides with a standing building is that building (re-dated to before its
   atlas if its own year was only an estimate).
9. **Built data is not committed.** `make data` rebuilds it (about 20 minutes after the
   downloads); `make deploy` ships it. Only `data/manual`, `data/tables`, `data/research` are
   precious.
10. **First view:** Manhattan from the harbour at bearing 29° (the avenues run up the screen).
