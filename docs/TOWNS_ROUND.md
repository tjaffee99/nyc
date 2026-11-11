# The towns round (2026-11-11, later): Princeton and New Haven

Read `CLAUDE.md` (the owner's rules; decisions 39, 40, 51) and `docs/AGENTS.md` first. This file is
what is specific to this round. Your own brief names your part and the files you own.

## What the owner said (verbatim)

> The outer counties aren't labeled and a lot of the data (building dates etc) looks fake and there
> are no landmarks. Double check especially important towns like Princeton and New Haven

## What the lead found

- Labels: a viewer bug, fixed.
- Landmarks: the models are drawn (5 in Princeton: `viewer/src/landmarks/nj-outer.ts`; 11 in New
  Haven: `ct.ts`) but they are few, small and plain, and lost among flat blocks.
- Dates: the buildings that matter most have no real year.
  - Princeton (`data/interim/counties/nj_mercer.parquet`, `muni` like 'PRINCETON'): 388 named
    footprints, 356 of them without a usable year; 136 of the 145 footprints over 1,500 m².
    The University is tax-exempt (class 15B): MOD-IV has no year or the placeholder 1910
    (Jadwin Gymnasium, 1969, is drawn at 1911; the stadium of 1998 at 1909).
  - New Haven (`ct_south_central_connecticut.parquet`, `muni` = 'New Haven'): 616 named
    footprints, 228 without a usable year. The assessor records 1900 for 8,264 of 29,261
    buildings, 1920 for 2,777, 1910 for 1,719 (placeholders: 60 % of the city).
  - A wrong year also gives a wrong wall colour (everything "before 1945" is brick).

## Rules for this round

- **Opened sources only.** Every year you write comes from a page you fetched in this session,
  with its URL. Nothing from memory. If a source cannot be opened, the row is not written (or is
  written with "estimate" in its note and says why).
- Outbound requests: User-Agent `NYCThroughTime-research/0.1`; never the owner's name, e-mail or
  the repository name. No scraping of per-parcel lookup sites behind captchas, logins or terms.
  Reachable: Wikipedia (rate-limits: pause between calls), Wikidata's SPARQL endpoint, the
  OpenStreetMap map API for small boxes (`https://api.openstreetmap.org/api/0.6/map?bbox=w,s,e,n`,
  at most about 0.02° on a side per call: it returns tags such as `name`, `start_date`,
  `wikidata`), university and city pages. OpenStreetMap's Overpass hosts are blocked.
- Machine: one process at a time, under 2 GB (`SET memory_limit='1500MB'` in DuckDB; filter by a
  box, never read a whole file). Disk: 7 GB free for everybody: no downloads over 200 MB.
- You own only the files your brief names. No git. No pipeline stage, no build, no deploy. Write
  results to your files as you go (the container can restart).
- Footprints: `data/interim/counties/nj_mercer.parquet` / `ct_south_central_connecticut.parquet`
  (columns `id, name, muni, lon, lat, area_m2, height_m, year_raw, heap, prop_class, geometry`
  (WKB, EPSG:4326)); the same outlines with more attributes are in
  `data/raw/overture/2026-10-21.0/outer_building.parquet` (1.3 GB: always filter by a box).

## Hand-over format: dates

`data/tables/known_building_dates.<part>.csv`, columns exactly
`id,name,lat,lon,bin,start_year,end_year,source_url,note` (as `known_building_dates.ct.csv`):

- one row per footprint (a college of four footprints is four rows);
- `lat`, `lon`: a point **inside** the footprint — `shapely` `representative_point()` of the
  outline, not the centroid (a quadrangle's centroid lies in its courtyard) — to 6 decimals;
  check every row with a point-in-polygon test against the parquet and report the count;
- `bin` empty; `end_year` 9999; `start_year` the year the building was completed (opened);
- `note` starts with `exact:` and quotes what the source says, or contains the word `estimate`
  when the year is a range or a guess (the builder marks those `estimated`);
- `id`: `<part>_<short name>`; unique.

The builder (`pipeline/county_buildings.py researched()`) dates the footprint under each point.

## Hand-over format: landmarks

As `docs/OUTER_ROUND.md`, section "Landmarks": real reconstructions from cited dimensions; plan,
anchor and orientation from the real footprint; heights from an opened source (name what is
estimated in the `Model:` fact); `replaces` holds the footprint outline(s) so the flat block under
the model is hidden; `cd viewer && npx tsc --noEmit` must pass; a numeric check of plan and height
per model in your research note. Read two models in `viewer/src/landmarks/nj-outer.ts` or `ct.ts`
and the kit (`kit.ts`, `types.ts`) before writing. The lead registers your export in `index.ts`.
A landmark here should be recognisable from 500 m: give it its roof, its tower, its portico —
not a box — within a few hundred faces.
