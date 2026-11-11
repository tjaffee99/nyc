# Round of 2026-11-11, night: build-out order, Jersey City and Hoboken, outer streets, town populations

Read `CLAUDE.md` (the owner's rules; decisions 34, 39-44, 52-53) and `docs/AGENTS.md` first. Your own
brief names your part and the files you own. Rules of `docs/TOWNS_ROUND.md` apply (opened sources
only; User-Agent `NYCThroughTime-research/0.1`, never the owner's name, e-mail or the repository
name; Wikipedia: raw wikitext, one page every 4 seconds, cached; raw downloads under
`data/raw/` or `data/interim/<part>_raw/`, never in `data/research/`; no git, no deploy).

## What the owner said (verbatim, with a screenshot of Jersey City and Hoboken around 1900)

> a lot of the data from these towns, especially the years of the buildings, seems fake. think much
> harder about the order in which all of these towns were actually built out, the patterns of
> farmland and forest over time, etc. surely some kind of maps exist in the past? also a lot of
> Jersey City and Hoboken are empty before the modern era, which seems wrong.
> get rid of the red and blue lines during the Revolution. also get rid of *all* of the animations
> in overworld map mode. they should only be in story mode.
> also the outer suburbs don't have roads.
> also the whole thing is super slow on mobile. Perhaps it would be good to load just the five
> boroughs + the Hudson Waterfront by default and toggle the rest?
> also the population counter in the corner should change dynamically based on the town or
> neighborhood as well. e.g. if you zoom into Newark it should tell you the population of Newark and
> not just Essex County. and if you zoom all the way out it should tell you the population of the
> entire NYC metro, not just NYC proper.

## Machine (stricter than before: four agents and the lead's rebuild share it)

- 16 GB for everybody: **one process of yours at a time, under 1.5 GB** (DuckDB:
  `SET memory_limit='1200MB'`; work in tiles or chunks, never a whole region in memory).
- Disk: 6 GB free for everybody. Keep your part **under 1.2 GB at any moment**; delete a raw file
  once what you need is derived (the URL in your note is the record). `df -h /home/user` first.
- The lead's rebuild is running: do not run pipeline stages other than your own new script.
- Make every step resumable (skip what is written); the container can restart.

## The map

Box of everything: `common.REGION_BBOX` = (-75.37, 39.47, -71.85, 42.20). Inner box (the city and
the seven inner counties, full detail): (-74.52, 40.47, -73.40, 41.38). County outlines:
`data/raw/tiger/tl_2024_us_county.zip`; the 26 counties and their FIPS: `docs/OUTER_ROUND.md` and
`data/manual/extent_counties.json`. Built buildings with their years, one point each:
`data/interim/nyc_building_points.parquet` (city), `county_points_inner.parquet`,
`county_points_outer.parquet` (lon, lat, start_year, end_year, conf, county, area_m2).
