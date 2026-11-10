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

## Final report (your last message)

Short and factual: files written (paths, row counts), what was checked and how, what was not
checked, known weak spots, and exact instructions for anything the lead must wire in.
