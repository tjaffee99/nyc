# effects.csv - what happened where (battles, fires, blasts, marches)

Columns: `id,event,kind,side,year,year_end,lon,lat,radius_m,path,source_url,note` (UTF-8, RFC 4180 quoting). 186 rows; an event usually has several rows that share `event`.

- `kind`: `fire` (an area burning: `path` = the burned outline as a closed ring `lon lat; lon lat; ...` and `lon`,`lat` its centroid, `radius_m` empty; or no `path` and `lon`,`lat`,`radius_m`), `explosion` (`radius_m` = reach of the blast), `move` (troops, a mob, an aircraft, a parade: `path` = route in the order travelled, `lon`,`lat` = its first point), `clash` (fighting at a place, `radius_m`), `fleet` (ships or boats: `path` over water), `collapse` (a structure falling, `radius_m` = reach of debris/dust).
- `side` (move, clash, fleet; an explosion's attacker rarely): `american british hessian dutch english lenape union mob police` or empty (civilian ships, aircraft, parades, disasters). For a clash it is the attacking side; the defender is in `note`. `french` is unused.
- `year`, `year_end`: decimal years (day = 1/365 or 1/366 of a year, fraction = clock time / 24). 27 August 1776 03:00 = 1776.6557. Times are those of the account where one exists; otherwise estimated (said in the note). A one-minute blast has `year_end` a few minutes after `year`: the viewer will need to widen it to be visible. Dates are as the sources give them (no Julian/Gregorian conversion).
- `path`: 3-9 points `lon lat` separated by `; `. A path of a `move` or `fleet` is a polyline; the animation should run the whole path between `year` and `year_end`.

## How positions were placed
Nothing here was digitised from a georeferenced map. A site (fort, church, pass, battlefield, building) is placed at its known modern location, from memory of the place and the events/landmark tables, to about 50-200 m. A route follows the roads, passes and shores that the account names, between sited stops; the line between stops is straight or follows today's streets, NOT the roads or shoreline of the time. Every placement that is mine says `estimated:` in `note`; only the 1776 and 1835 fire rings (copied from `data/manual/extents/fire_*.geojson`, themselves estimated from text, low confidence) are not. Radii of blasts, dust, fires are order-of-magnitude choices. Water routes (fleets, boats, aircraft over water) were drawn by hand and not tested against the map's water layer: the lead should check that fleet points fall on water (check list in `data/research/effects.md`).

## Check list (run 2026-11-11)
Header exact; ids unique; every row has what its kind needs; year <= year_end; every coordinate and path point inside (-75.37, 39.47, -71.85, 42.20); every path parses (fire rings closed, >= 4 points incl. closing; moves/fleets >= 3).
