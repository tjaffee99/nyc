# The round of 2026-11-11: landmarks, cleared districts, farms, the outer counties

Read `CLAUDE.md` (the owner's rules, decisions 31, 34-38) and `docs/AGENTS.md` (ground rules, standard
hand-over formats, final report) first. This file adds what is specific to this round. Your own
brief names your part and your files.

## What the owner asked (verbatim)

> do another pass on landmarks. Some obvious ones that have been missed: the High Line, Penn Station
> (Moynihan Hall), Brooklyn Tower.
> make sure that areas that have been destroyed and rebuilt in the past (e.g. Springfield/Belmont,
> Newark) appear before they were destroyed and are not just farmland until the 90s or whatever.
> was there *that* much farming in 1820? like the entire metro area?
> also add the rest of the counties now. use Sonnet subagents and compress the houses and tree
> procedural generation if you must. you probably only need real detail for a few places outside of
> the core (New Haven, Trenton, Princeton, West Point, Kykuit, Sleepy Hollow, Oheka Castle etc etc)

## Machine limits in this round (stricter than docs/AGENTS.md)

- **Disk: 12 GB free for everybody.** Keep your part under 1.5 GB at any time. Delete a raw
  download as soon as you have derived what you need from it (say so in your research note: the
  URL is the record). Check `df -h /home/user` before a large download.
- **Memory: one process at a time, under 2 GB** (`SET memory_limit='1500MB'` in DuckDB; read
  windows, never whole files). The lead runs 10 GB rebuilds on the same machine: a job of yours may
  be killed. Make every step resumable (skip what is already written) and simply run it again.
- The container can restart: write results to your files as you go, not at the end.

## Overpass is blocked on this machine

Every OpenStreetMap Overpass host fails from here: do not spend calls on it. (Reachable: the
OpenStreetMap map API for small boxes, `api.openstreetmap.org/api/0.6/map?bbox=…`; OpenHistoricalMap's
Overpass; Wikidata's SPARQL endpoint; Wikipedia.) OpenStreetMap-derived geometry is
on disk as Overture extracts under `data/raw/overture/2026-10-21.0/` (read with DuckDB and
`load spatial`, filter by an envelope, never whole): `outer_building.parquet` (footprints of the
whole box), `outer_freeways.parquet` (motorway and trunk segments with `name` and `routes`),
`outer_water.parquet` (water polygons with names); for the present map also `base_land_use.parquet`
(parks, campuses, cemeteries), `base_water.parquet`, `rail.parquet`, `roads_region.parquet`.

## The outer counties (19 units; "the map" = the 12 it has today plus these)

| State | Counties (FIPS) |
|---|---|
| New York | Nassau 36059, Suffolk 36103, Putnam 36079, Orange 36071, Dutchess 36027, Ulster 36111, Sullivan 36105 |
| New Jersey | Middlesex 34023, Monmouth 34025, Ocean 34029, Somerset 34035, Morris 34027, Sussex 34037, Hunterdon 34019, Mercer 34021 |
| Connecticut (planning regions, the county equivalents of TIGER 2024) | Greater Bridgeport 09120, Western Connecticut 09190, South Central Connecticut 09170 |
| Pennsylvania | Pike 42103 |

Box for every extract: `common.OUTER_BBOX` = (-75.37, 39.47, -71.85, 42.20). County outlines:
`data/raw/tiger/tl_2024_us_county.zip`. Overture footprints of the whole box:
`data/raw/overture/2026-10-21.0/outer_building.parquet` (the lead is downloading it; same columns as
`region_building.parquet`, which covers only the present map: id, subtype, class, name, height,
num_floors, has_parts, source_dataset, lon, lat, geometry WKB). Wait for it rather than fetching
footprints yourself.

The outer counties are a **compact tier**: today's buildings with a year each, the lead compresses
houses to rectangles and thins the trees. No vanished buildings are expected there except in the
cleared centres named in a brief. Accuracy priority (the owner): Manhattan > the other boroughs >
the inner suburbs > the outer suburbs.

## County building years: what the lead needs from a data part

One file per county in `data/interim/counties/`, named `nj_<county>.parquet`, `ny_<county>.parquet`,
`ct_<region>.parquet` or `pa_pike.parquet`, **with exactly the columns of the existing files**
(`python -c "import pyarrow.parquet as pq; print(pq.read_schema('data/interim/counties/nj_essex.parquet'))"`),
which `pipeline/county_buildings.py` reads (it globs `n[jy]_*.parquet` and `ct_*.parquet`; say so if
you need `pa_*`). Where the public roll has no year, also `<name>_estimates.parquet` as
`pipeline/counties_ny_estimates.py` writes it (`year_est`, `est_basis`): a town must not be empty.
A report per county as the existing ones (`*_report.json`): footprints, share with a recorded
year, placeholder years found, the ten most frequent years.

## Landmarks (every landmark part)

- The kit: `viewer/src/landmarks/kit.ts`, `types.ts`; registry `index.ts` (the lead adds your
  export there: name it in your report). Read two existing models of the kind you are building
  (`nyc-civic.ts` for buildings, `nyc-bridges.ts` for bridges, `nyc-lost.ts` for things that are
  gone) and the matching research note (`data/research/landmarks_civic.md` …) before writing.
- **Real reconstructions from cited dimensions**: anchor, orientation and plan from the real
  footprint; heights from a cited source. Footprints: `pipeline/footprint_at.py <lon> <lat> [radius]`
  in the city; `data/interim/county_buildings.parquet` (read a window with DuckDB) in the seven
  counties already on the map; elsewhere the OpenStreetMap building way through Overpass (ODbL:
  note the way id), or `outer_building.parquet` once it exists.
- Every model carries a `Model:` fact that names what is estimated (as the existing ones do), a
  start year and, if it is gone or was rebuilt, an end year; a building that changed (a tower
  added, a hall rebuilt) is two models with consecutive lifespans.
- Check: `cd viewer && npx tsc --noEmit` passes; and a numeric check of each model against its
  footprint and cited height (plan size within a few metres, top height within 2 %), in the way
  the research notes of the earlier parts report it. No screenshots: they do not work here.
- Keep models light: a landmark is tens to a few hundred faces, not thousands.
- Budget your effort: a correct simple massing with the right plan, height and dates beats an
  elaborate unfinished one. Finish and check one model before starting the next.
