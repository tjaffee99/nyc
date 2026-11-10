# Rules for agents working on one part of the map

Read `CLAUDE.md` first (what the project is, the owner's rules, the conventions).

## Ground rules

- You own the files named in your brief and nothing else. Do not edit any other file. If
  something outside your files must change, describe the exact change in your final report.
- Do not run `git commit`, `git push`, `make`, `npm run build`, `npm run dev` or any pipeline
  stage you did not write. The lead commits, builds and runs the heavy stages.
  (`cd viewer && npx tsc --noEmit` is fine for checking a TypeScript file you own.)
- The machine has 16 GB shared with other agents: never load a file over ~200 MB whole. Read
  windows with DuckDB (`.venv/bin/python`, packages: duckdb, geopandas, shapely, pyproj,
  rasterio, numpy, pandas, scipy, requests). Keep any one process under ~2 GB.
- Put downloads under `data/raw/<your-part>/` (gitignored) and scratch work under
  `data/interim/<your-part>/` (gitignored). Never write into another part's folder.
- Real, cited data. Every date, dimension and outline needs a source URL next to it. If a
  value is your estimate, say "estimated" in its note. If you could not verify something,
  say so; never fill a gap with an invented number that looks researched.
- Licences: note the licence of every source you use. Do not scrape data whose terms forbid
  it; public-domain and openly licensed sources first (US government, NYC Open Data, NYPL
  public-domain maps, Library of Congress, OpenStreetMap / OpenHistoricalMap, Wikidata,
  Wikipedia for facts with the article URL).
- Outbound requests: generic User-Agent (`NYCThroughTime-research/0.1`); never put the
  owner's name, e-mail or the repository name in a request.
- Stay inside your tool-call budget. Stop when the budget is nearly spent and report what is
  done and what is not — a smaller verified result beats a larger unverified one.

## What is on disk

- `/home/user/nyc` — this repository. `/home/user/tjaffee99/bay` — the Bay Area project it was
  ported from, read-only, for file formats and worked examples.
- `data/interim/nyc_footprints_raw.parquet` — the city's 1.08 M building footprints (BIN, name,
  recorded year `year_raw`, measured roof height `height_m`, ground elevation `ground_m`,
  centroid `lon`/`lat`, WKB `geometry`, EPSG:4326). Query windows with DuckDB, or use
  `cd pipeline && ../.venv/bin/python footprint_at.py <lon> <lat> [radius_m] [--rings] [--anchor lon,lat]`.
- `data/raw/nyc/pluto.csv` — tax lots (bbl, address, bldgclass, numfloors, yearbuilt, …).
- `data/raw/overture/2026-10-21.0/*.parquet` — Overture extracts of the map box
  (-74.29, 40.47, -73.67, 40.94): `building`, `building_part` (OpenStreetMap's 3D parts),
  `base_land`, `base_land_use`, `base_water`, `roads_region` (tertiary and up), `roads_local`,
  `freeways`, `rail`, `region5_land_use`, `region_airports`. Geometry is WKB, WGS84.
- `data/raw/nyc/parks_properties.geojson`, `lpc_individual_landmarks.geojson`,
  `lpc_historic_districts.geojson`; `data/raw/mta/gtfs_subway.zip`;
  `data/raw/nypl/building-inspector.objects.ndjson` (1850s atlas footprints).

## Also on disk since the first round (2026-11)

- `data/interim/nyc_buildings.parquet` — every building as built: today's footprints and
  ~100 k vanished ones (GeoParquet, EPSG:4326): `bin`, `doitt_id`, `name`, `boro` ("1".."5"),
  `start_year`, `end_year` (9999 = standing), `year_confidence`, `year_src` (`lpc`, `assessor`,
  `heap_about+spread`, `heap_by+neighbours`, `neighbours`, `on_map`, `atlas_1857`, `map_1660`,
  `ohm_documented`, `generated` …), `raw_year` (the assessor's year, 0 if none), `height_m`,
  `bldgclass`, `area`. `data/interim/nyc_building_points.parquet` is the light version (lon,
  lat, start_year, end_year, area_m2, height, boro, conf). Both are rewritten by every rebuild:
  if a read fails, wait a minute and retry.
- `data/interim/grid_detail_landyear.npy` (+ `grid_detail_meta.json`, `pipeline/terrain_grid.grid_def`)
  — the year each ~29 m cell of made land became land (NaN: always land, or water today);
  `grid_detail_covers.npy` / `grid_detail_years.npy` — the cover history per cell
  (`pipeline/terrain_tiles.COVER_NAMES`). `pipeline/nyc_buildings.Ground` samples ground elevation.
- `data/manual/natural/` (the 1609 layer and its tools, incl. the georeferenced USGS sheets'
  list `usgs_sheets.json`), `data/manual/fill_zones.csv`, `data/manual/extents/` (built-up
  snapshots, tools for NYPL / LoC / USGS maps incl. the NYPL Map Warper control-point dump),
  `data/manual/ohm/`, `data/manual/transit/`, `data/manual/routes.csv`, `data/tables/*.csv`.
- `data/raw/overture/2026-10-21.0/region_building.parquet` — every Overture footprint of the
  wider box (-74.52, 40.47, -73.40, 41.38): id, subtype, class, name, height, num_floors,
  source_dataset, lon, lat (centre), WKB geometry. About 5 M rows: query windows with DuckDB.
- County outlines: `data/raw/tiger/tl_2024_us_county.zip` (STATEFP + COUNTYFP).

## The counties (since 2026-11-10 afternoon)

- The map now reaches beyond the five boroughs: `data/manual/extent_counties.json` names the
  counties on it (Hudson, Bergen, Essex, Union, Passaic NJ; Westchester, Rockland NY — more may
  follow), `pipeline/extent.py` (`in_extent`, `POLY`) is the outline of the city plus those
  counties, `common.REGION_BBOX` = (-74.52, 40.47, -73.40, 41.38) is the box of every region
  extract and of the region terrain grid (z13, ~58 m cells; the fine z14 grid still covers
  only `common.NYC_BBOX`).
- `data/raw/overture/2026-10-21.0/`: `roads_region`, `roads_local`, `freeways`, `rail`,
  `base_land`, `base_land_use`, `base_water`, `region5_land_use`, `region_airports` were
  refetched for the wider box (same columns as before).
- `data/interim/county_buildings.parquet` (GeoParquet, 1.18 M buildings: `start_year`,
  `end_year`, `year_confidence`, `year_src` (`parcel`, `parcel_secondary`, `heap_…`,
  `neighbours`, `historic_register`), `county`, `height_m`, `area`, `name`, `use`) and the light
  `data/interim/county_building_points.parquet` (lon, lat, start_year, end_year, area_m2,
  height, boro = "9", county, conf). Rewritten by every rebuild: retry a failed read.
- `data/interim/grid_region_landyear.npy` covers the wider box (`pipeline/ground_rule.py`:
  `land_year_at(lon, lat)`, `ground_year(geoms)` read the fine grid where it exists, else this).
- County tables (same columns as the city's): `data/tables/population_counties.csv`,
  `places_counties.csv`, `events_counties.csv`, `parks_counties.csv`;
  `data/manual/fill_zones_counties.csv`; `data/manual/natural/counties/`.

## Standard hand-over formats (so the lead can wire parts in without reading your code)

- A researched year for a standing building: a row in `data/tables/known_building_dates.csv`
  — `id,name,lat,lon,bin,start_year,end_year,source_url,note` (`bin` = the city's Building
  Identification Number when you have it, else the point must lie inside the footprint;
  "estimated" in the note if it is one). Several agents append to this file: write your rows
  to `data/tables/known_building_dates.<your-part>.csv` in the same format and the lead merges.
- A documented building that is gone: `data/tables/notable_demolished.<your-part>.csv` —
  `id,name,start_year,end_year,lat,lon,height_m,storeys,material,outline,shape_note,source_url`
  where `outline` is `lon lat; lon lat; …` (the real outline) or empty with
  `footprint_m` = `WxD` and `rotation_deg` columns added (a rectangle at lat / lon).
- Traced map layers: `data/manual/atlas/<area>_<map year>.geojson`, one polygon per building,
  properties `map_year`, `material` (`brick` | `frame` | `stone` | ``), `storeys` (if the map
  gives them), `source`, `sheet`.

## Final report (your last message)

Short and factual: files written (paths, row counts), what was checked and how, what was not
checked, known weak spots, and exact instructions for anything the lead must wire in.
