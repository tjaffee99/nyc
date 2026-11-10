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

## Status and decisions log

(Written at the end of each working session — see below.)
