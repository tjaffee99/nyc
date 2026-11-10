# Rail transit through time — how the data was assembled

Everything `pipeline/transit.py` draws comes from four committed things:

| file | what | rows |
|---|---|---|
| `data/tables/transit_stations.csv` | every station with opening / closing day, note, source, line, structure, lon/lat | 829 |
| `data/tables/transit_openings.csv` | every stretch of line with its opening day (closing day for what is gone) | 234 |
| `data/tables/transit_station_names.csv` | earlier names of renamed stations | 2 |
| `data/manual/transit/elevated_lines.geojson` | routes of the 17 elevated lines / branches that are gone | 17 lines, 105 km |
| `data/manual/transit/former_railroads.geojson` | railroads and bits of subway that are gone | 145 pieces |

The scripts in `tools/` rebuild them from downloads kept under `data/raw/transit/` (gitignored).
Run them from `data/manual/transit/tools` with `../../../../.venv/bin/python <script>` in this order:

1. `match_stations.py` — joins the 475 GTFS subway stations (MTA station table: line, division,
   structure) to the rows of Wikipedia's four borough station lists and, through the article of
   each row, to its Wikidata item (optimal assignment on name, line, division, borough, distance).
2. `fetch_articles.py` — downloads the wikitext of every station article (and any list of titles).
3. `build_station_table.py` — writes `transit_stations.csv`.
4. `build_openings.py` — writes the subway and Staten Island Railway rows of `transit_openings.csv`.
5. `build_elevated.py` — writes `elevated_lines.geojson` and the `el` rows of `transit_openings.csv`.
6. `build_former_railroads.py` — writes `former_railroads.geojson`.
7. `build_rail_rows.py` — writes the `rail` rows of `transit_openings.csv`.
8. `check_built.py` — checks the three built viewer files (run after `pipeline/transit.py`).

## Sources and licences

| source | used for | licence |
|---|---|---|
| MTA subway GTFS (`data/raw/mta/gtfs_subway.zip`) | stations, stop order, service-line shapes, routes, colours, weekday trip counts | MTA developer terms (open data) |
| MTA "Subway Stations" table, data.ny.gov 39hk-dx4f | line, division and structure (subway / elevated / open cut …) of every GTFS station | NY Open Data |
| Wikidata (query.wikidata.org; P1619 opening, P3999 closure, P625 coordinates, P81 line) | opening / closing days, coordinates of closed and elevated stations | CC0 |
| English Wikipedia — borough station lists, list of closed stations, every station article's infobox, line articles | opening / closing days (facts, with the article URL in `source`) | CC BY-SA (facts cited) |
| OpenHistoricalMap (Overpass, `data/raw/transit/ohm/ohm_rail.json`) | geometry of demolished elevated lines and railroads; dates of standing railroad tracks; cross-check of the subway dates | CC0 |
| OpenStreetMap via Overture (`rail.parquet`, `roads_*.parquet`) and Overpass (abandoned railway ways) | standing track geometry; street centre lines under elevated lines OHM lacks; High Line and New York, Westchester & Boston remains | ODbL |

## Station days (`transit_stations.csv`)

Rule, for opening and closing alike: (1) the article infobox when it gives a day; (2) else a
Wikidata value with day precision; (3) else the borough list day; (4) else the infobox year or
month — the note then says **estimated** (mid-year / mid-month is used). The note records which
sources agree and what the others say; the Wikidata id is in brackets.

Of the 496 GTFS stations (475 subway + 21 Staten Island Railway): for 255 subway stations
infobox, borough list and Wikidata agree on the day; for 180 two sources agree; 27 rest on one
source; 10 were set by hand (platform sets of complexes: Canal St, West 4 St, 145 St, Queensboro
Plaza, 42 St–Port Authority, Halsey St, 34 St–Penn Station — each with its reason in the note);
7 are estimated (3 Brighton Line stations and 4 Staten Island stations known only to the year).
Wikidata alone would have been wrong for about a quarter of the stations (months mis-entered as
December for July on the Canarsie Line, 1915-09-13 for most Fourth Avenue stations …); the
borough lists carry the day subway service began on lines that are older (Jamaica, Myrtle,
Brighton, Liberty Avenue), where the infobox has the day the station first opened.

Subway stations that took over a railroad station carry the day subway service began: the
Rockaway line (Long Island Rail Road stations from the 1880s, subway 28 Jun 1956 / 16 Jan 1958)
and the Dyre Avenue line (New York, Westchester & Boston stations of 1912, subway 15 May 1941).

Closed stations: 32 on lines that still run (City Hall loop, Worth St, 18th St, 91st St, South
Ferry loops, Myrtle Av, Dean St, the Jamaica elevated east of 121st St, the Culver shuttle …),
168 on the elevated lines that are gone, 23 on the Staten Island branches, plus railroad
stations (83 LIRR, 18 New York Central / New Haven, 8 PATH: the railroad rows are mostly known
to the year only — 71 of 109 are marked estimated).

## Stretches of line (`transit_openings.csv`)

Columns: `route_id, opened, note, source, system, line, from_stop, to_stop, via, closed`.

* `subway`, `sir` (164 rows): `from_stop` / `to_stop` are GTFS stop ids (or a `lon lat` point)
  and `via` is the GTFS shape the stretch is traced along. A stretch between two neighbouring
  stations opens with the later of the two; a station younger than both neighbours is an infill
  station (22 found, listed by the script); 79 stretches are corrected by hand in `FIX`, `CHAIN`
  and `SPLIT` of `build_openings.py`, each with its reason and article (river tunnels and
  connections that opened after the stations at both ends, track older than its platforms).
  Express stretches that only repeat a local stretch are dropped.
  Cross-check: every row is compared with the start dates of OpenHistoricalMap's ways along it;
  the 40-odd rows that differ by more than 0.3 year were read one by one — in each the table
  follows the station articles (OHM is coarser there, or dates a rebuilt structure).
* `el` (61 rows): stations are Wikidata ids, `via` the line id of `elevated_lines.geojson`. A
  stretch is in use while a station of the line is open on each side of it (so infill stations
  and stations closed while trains still ran through do not cut the line).
* `rail` (9 rows): `line` is the OpenStreetMap line name, `from_stop` / `to_stop` the corners of a
  box; used where OpenHistoricalMap has no dated way or a modern operator date.

## Elevated lines that are gone (`elevated_lines.geojson`)

Geometry, in this order: OpenHistoricalMap railway ways with an end date (the Manhattan lines
and parts of Fulton Street, Fifth Avenue and Lexington Avenue in Brooklyn); elsewhere **the
centre line of the street the structure stood over**: the shortest street path through the
line's stations (Wikidata coordinates) and through the documented corners listed in
`build_elevated.py` (110th Street curve, 53rd Street, Division / Allen Street, 23rd Street, 38th
Street in Brooklyn, Grand / Lexington Avenue). Each feature says what share of its length is OHM
geometry (`geometry_source`); `route` names the streets; `source` is the line's article.

| line | km | OHM share |
|---|---|---|
| Ninth Avenue (South Ferry – 155th St) | 16.3 | 68 % |
| Sixth Avenue (Battery Place – 53rd St / Ninth Av) | 8.3 | 76 % |
| Third Avenue (South Ferry – Gun Hill Road) | 24.9 | 65 % |
| Second Avenue (Chatham Sq – 129th St) | 13.1 | 78 % |
| City Hall, 34th Street and 42nd Street branches | 1.3 | City Hall 100 %, others street |
| Queensboro Bridge branch | 2.5 | street (bridge roadway) |
| Brooklyn Bridge tracks (Park Row – Sands St) | 1.9 | 75 % |
| Ninth Avenue extension (Polo Grounds shuttle) | 1.1 | straight lines between stations — **estimated** |
| Fulton Street (Fulton Ferry – 80th St) | 13.8 | 42 % |
| Fifth Avenue (Fulton St – 65th St) | 7.6 | 31 % |
| Lexington Avenue (Myrtle Av – Broadway) | 4.4 | 40 % |
| Myrtle Avenue west of Broadway | 4.9 | street |
| Jamaica Avenue east of 121st St | 3.0 | street |
| Broadway to Broadway Ferry | 0.9 | street |
| Culver shuttle | 2.0 | street (37th Street) |

Not drawn: the Park Avenue elevated of 1885–91 in Brooklyn, the Fifth Avenue line north of
Fulton Street (Hudson Avenue to Sands Street), the Fulton line's Sands Street link, the 58th
Street stub of the Sixth Avenue line, the Bronx Park stub of the Third Avenue line, the Sea
Beach / West End / Culver surface predecessors, the World's Fair spur of 1939–40.

## Railroads

Standing tracks: Overture standard-gauge, light-rail and PATH tracks inside the map. Each takes
(1) a `rail` row of `transit_openings.csv`, (2) else the start date of the OpenHistoricalMap way
at that place (LIRR, Northeast Corridor / Hell Gate, Penn Station tunnels, PATH, Bay Ridge
Branch …), (3) else — yards and sidings — the date of the nearest dated track within 400 m
(**estimated**); tracks with none of the three are left out. Railroads that are gone are the
OpenHistoricalMap ways with an end date (Hudson River Railroad on the West Side, the Whitestone
and Rockaway Beach branches, the Staten Island North Shore and South Beach branches, Hudson
Terminal …) with OHM's dates as mapped, the High Line pieces OpenStreetMap still has as railway
(1934–1980) and the New York, Westchester & Boston right of way (1912–1937).
