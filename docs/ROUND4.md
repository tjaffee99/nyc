# Round of 2026-11-12: the places that are missing their past

Read `CLAUDE.md` (the owner's rules; decisions 8, 24, 34, 54 and "What is not done") and
`data/manual/atlas/README.md` in full: it is the method, the file format and the checks of every
traced atlas layer on this map, with the tools per part (`data/manual/atlas/tools*/`). Your own
brief names your area and your files.

## What the owner said (verbatim)

> fix Hoboken, and any other towns (or parts of NYC proper) that are missing information in the past

## What "missing" means here, measured

`pipeline/holes.py` lists ground the map shows as built-up city in a year with no building
standing within 60 m (`data/interim/reports/holes.csv`: year, hectares, place, lon, lat;
`holes_by_place.csv`). Buildings that were pulled down are in no modern dataset; this map puts
them back from **traced atlas outlines** (real outlines, estimated years), from records, and
last from generated lots. Tracing a dated atlas is the fix the owner prefers ("prefer tracing a
real historical map over inventing geometry"). Read the holes of your area before choosing
plates: trace where the map is empty first.

## Rules

- A layer is `data/manual/atlas/<area>_<year>.geojson` with its `_coverage.geojson` and
  `_stats.json`, in exactly the README's format (the lead's stage `pipeline/nyc_extras.py`
  reads every layer in that folder: columns, CRS and the year in the file name must be right).
  One layer per atlas volume and year. Do not edit existing layers; a new state of a district
  already traced gets its own file.
- Copy the tool you build on into your own `data/manual/atlas/tools_<part>/` and change it
  there. Work files under `data/interim/atlas_<part>/`, scans under `data/raw/atlas/<part>/`.
- Sources that worked before: NYPL's Map Division scans (`https://images.nypl.org/index.php?id=<imageId>&t=u`)
  with the control points of NYPL's Map Warper dump (README, "Sources and licences"); the
  Library of Congress's Sanborn sheets placed by street crossings (`tools_hudson/loc_register.py`)
  — loc.gov answered 503 on 2026-11-11: try once, and use NYPL if it still fails. Other public
  collections with georeferenced or plainly scanned atlases are fine (say which, with URLs and
  the licence). User-Agent `NYCThroughTime-research/0.1`; never the owner's name, e-mail or the
  repository name.
- **Checks, with numbers in your note, per layer** (as the README's tables): control-point fit,
  street match (the shift found against today's street lines and what is left), the share of
  outlines within 8 m of a street centre line (the lead skips a layer where that share is high:
  `nyc_extras.ATLAS_SKIP`), the count of outlines and how many coincide with a standing
  building. Draw a few windows over the scan and look at them (write a small PNG, read it).
  A layer that is 15 m off is worse than no layer: do not hand over what you could not register.
- Machine (five agents and the lead share it): one process of yours at a time, **under
  1.5 GB**; disk **under 700 MB for your part at any moment** — delete a scan when its plate is
  traced (`df -h /home/user` first: 6 GB are free for everybody). Resumable steps; write as you go.
- No git, no pipeline stage, no deploy, no edits outside your files.
- Final report (under 300 words): layers written (area, atlas, year, plates, outlines, km²
  covered), the checks' numbers, which holes of `holes.csv` your layers now cover and which
  they do not, what you could not register and why.
