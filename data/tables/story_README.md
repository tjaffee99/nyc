# story.csv - the guided tour ("story mode")
Columns: `id,year,year_to,lon,lat,zoom,pitch,bearing,seconds,title,text,source_url` (UTF-8, RFC 4180 quoting). One row per stop, in chronological order.
The viewer flies to (lon, lat) at zoom/pitch/bearing, sets the year (running to `year_to` if given, at most 40 years, and the next stop must start at or after it), shows title (max 48) and text (max 230), and rotates 10 degrees for `seconds` (8-20).
Facts and coordinates come from the project's tables: `events.csv` and `events_counties.csv` (dated events, coordinates, source_url), `landmarks_*.csv` (coordinates and lifespans, year_source_url) and `early_nyc.csv` (Lenape sites, Bolton / Parker). Stops taken from a landmark must fall inside its start_year-end_year.
Two stops rest on pages opened for the tour: the 1863 draft riots and the 1975 fiscal crisis (Wikipedia, opened 2026-11); the closing stop uses the population table's census source.
To add a stop: pick the row's year, take lon/lat from the table that holds the place, write one or two plain present-tense sentences that are true of what the map shows at that year, add the source URL, and insert the row in year order.
Then re-check: header exact, ids unique, years non-decreasing, coordinates inside (-74.52, 40.47, -73.40, 41.38), zoom 11-17, pitch 0-70, seconds 8-20, text <= 230, 95-110 rows, seconds sum 1,300-1,400.
Growth stops (`year_to`): Els uptown 1878-83, Brooklyn 1887-94, the race for the sky 1929-30, Lincoln Center 1959-62, Battery Park City 1976-83, September 11 (2001.62-2001.8, the towers vanish).
Total: 106 stops, 1,351 seconds of stops (22.5 minutes) plus about 4 s of flight between stops (about 7 minutes): roughly 29.5 minutes.
Not checked on screen: the captions were written against the tables, not against a rendered map; eyeball the stops where a caption names something drawn (Latting Observatory, Church in the Fort, Lincoln Center).
The generator was a throwaway script; the CSV is the source of truth. Edit it directly.
