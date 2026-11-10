# Rail transit — research notes

Method, sources and the tools that rebuild the tables: `data/manual/transit/README.md`.
This file keeps the decisions, the facts they rest on, and what is still open.

## What the stage draws (`pipeline/transit.py`, built 2026-11-10)

| | km of track | how dated |
|---|---|---|
| subway + Staten Island Railway, standing | 1 418 (764 tunnel, 312 elevated / bridge, 342 at grade or in cut) | `transit_openings.csv`, stretch by stretch |
| elevated lines that are gone | 212 (105 km of route, two tracks) | `transit_openings.csv` (`el` rows), station by station |
| railroads, PATH, light rail, standing | 891 (656 ground, 52 elevated, 183 tunnel) | 9 `rail` rows; OpenHistoricalMap dates by position; yards from the nearest dated track |
| railroads and bits of subway that are gone | 80 | OpenHistoricalMap start / end dates as mapped; High Line; NYW&B |

Track kilometres count every track (a four-track subway counts four times) and include the faded
margin of the map (the New Jersey waterfront opposite Manhattan and Staten Island).
49 service lines carry trains: 26 subway / SIR lines (one per GTFS route; the A runs two, to
Far Rockaway and to Lefferts Boulevard) and 23 lines of elevated railways that are gone (hidden
after their closing day). 827 stations are written for the viewer (719 subway / SIR / elevated,
108 railroad).

## Decisions

* **Opening day of a station** = the day the station first opened on its present line and
  structure (infobox), not the day subway service began there — except on the two lines taken
  over from railroads (Rockaway, Dyre Avenue), where the subway day is used and the railroad
  station is named in the note. So the Jamaica line carries 1885–1893 (Brooklyn Elevated), the
  Myrtle Avenue line 1888–89, the Brighton line 1878 (Brooklyn, Flatbush & Coney Island), the
  Liberty Avenue elevated 1915, although their borough-list days are the Dual Contracts days.
* **Opening day of track** = later of the two neighbouring stations, corrected by hand where
  track and platforms differ. The corrections with their reasons are in `build_openings.py`
  (`FIX`, `CHAIN`, `SPLIT`). The ones that matter most:
  - 1904 subway: City Hall – Grand Central – (today's shuttle) – Times Square – 145th St on
    27 Oct 1904; 157th St 12 Nov 1904; Lenox Avenue to 145th St 23 Nov 1904; West Farms 26 Nov 1904;
    the link under the Harlem River 10 Jul 1905; Fulton St 16 Jan 1905, Wall St 12 Jun 1905,
    Bowling Green 10 Jul 1905; Joralemon Street tunnel to Borough Hall 9 Jan 1908; Atlantic Avenue
    1 May 1908; 157th – 221st St 12 Mar 1906; 225th St 14 Jan 1907; 242nd St 1 Aug 1908.
  - Dual Contracts: Fourth Avenue / Sea Beach / Manhattan Bridge 22 Jun 1915; Steinway tunnel
    22 Jun 1915; Queensboro Plaza 1916–17; Astoria 1 Feb 1917; Corona 21 Apr 1917; Broadway line
    4 Sep 1917 – 1 Sep 1919; Seventh Avenue 3 Jun 1917 / 1 Jul 1918; Lexington Avenue 17 Jul 1918;
    Clark Street tunnel 15 Apr 1919; 60th Street and Montague Street tunnels and the Flatbush
    Avenue link of the Brighton line 1 Aug 1920; Eastern Parkway 23 Aug 1920; Pelham 1918–20;
    Jerome 1917–18; White Plains Road 1917–20; Culver 1919–20; West End 1916–17; Canarsie 1924–28;
    Flushing 21 Jan 1928; Nassau Street 29 May 1931.
  - IND: Eighth Avenue 10 Sep 1932; Cranberry tunnel 1 Feb 1933; Concourse 1 Jul 1933; Queens
    Boulevard 19 Aug 1933 / 31 Dec 1936 / 24 Apr 1937 / 11 Dec 1950; Crosstown 19 Aug 1933 /
    1 Jul 1937; South Brooklyn 20 Mar – 7 Oct 1933; Sixth Avenue 1 Jan 1936 / 15 Dec 1940; Rutgers
    tunnel and Fulton Street 9 Apr 1936; Fulton Street east 30 Dec 1946 / 28 Nov 1948 / 29 Apr 1956.
  - Later: Dyre Avenue 15 May 1941; Culver ramp 30 Oct 1954; 60th Street tunnel connection
    1 Dec 1955; Rockaway 28 Jun 1956 (Far Rockaway 16 Jan 1958); Chrystie Street 26 Nov 1967
    (Williamsburg Bridge link in service 1 Jul 1968); 57th St / Sixth Av 1 Jul 1968; 148th St
    13 May 1968; Archer Avenue 11 Dec 1988; 63rd Street 29 Oct 1989, its Queens connector
    16 Dec 2001; 7 extension 13 Sep 2015; Second Avenue 1 Jan 2017.
* **Two levels in one street** cannot be told apart in plan: the Sixth Avenue express tracks of
  1967 lie under the local tracks of 1940 and are drawn with 1940; the Flushing line under 42nd
  Street (1926–27) lies under the 1904 shuttle and its tunnel is drawn from 1904. Where an
  elevated line stands over a subway of the same division (Broadway Junction, Queens Plaza) the
  two are kept apart by level (station structure from the MTA table, tunnel flag of the track).
* **Heights**: elevated structures 8.5 m to the rail (+4.5 m per further OSM level); ramps of at
  most 4 % computed over the track graph; the decks of the Manhattan (41 m), Williamsburg (41 m),
  Queensboro (40 m), Brooklyn (38.7 m) and Hell Gate (41 m) bridges and the Culver Viaduct at
  Smith–Ninth Streets (26.7 m) from their articles (clearance above mean high water). Lines in
  open cut (Brighton, Sea Beach, Franklin) are drawn at ground level: OSM / Overture carry no
  cutting depth.
* **Trains** are procedural: one line per route, constant headway = 20 h ÷ weekday trips of the
  route in the GTFS feed (the A split between its two branches), real car sizes (B Division R160
  18.35 × 2.98 × 3.70 m; A Division R142 15.65 × 2.62 × 3.62 m; elevated cars about 14.3 × 2.67 m),
  train lengths 10 cars (7: 11; C J M L: 8; G H SIR: 5; 42 St shuttle: 6; Franklin shuttle: 2).

## Cross-checks

* 475 subway stations: infobox = borough list = Wikidata for 255; two of three agree for 180;
  one source for 27; set by hand 10; year only 3. Staten Island Railway: 4 of 21 year only.
* `build_openings.py` prints every stretch whose date differs from OpenHistoricalMap's by more
  than 0.3 year. Read one by one: Flushing 111 St (13 Oct 1925), Jamaica 111 St – Cypress Hills
  (28 May 1917), Broadway line stages, Fourth Avenue (22 Jun 1915), Queens Boulevard
  (31 Dec 1936), 63rd Street — the table follows the station articles; OHM dates the whole line
  with one stage there. The Rockaway and Dyre rows differ on purpose (subway day, not railroad).
* `check_built.py` (all pass): every GTFS station has a table row and is in the viewer file; no
  path, line vertex or station outside 1830 … 2026; no start ≥ end; everything inside the map
  box; no line longer than the shader's search (16 384 vertices, 512 stops).

## Not verified / weak spots

* **Nothing was looked at on screen** (no browser on the build machine). Numeric checks only.
* Elevated routes away from OpenHistoricalMap geometry follow today's street centre lines through
  the stations: where the street is gone or the Wikidata coordinate is off, the line is off by up
  to a few tens of metres, and a few kinks remain where the path changes between OHM geometry and
  the street. Fulton Street elevated: the Lafayette Avenue and Grand Avenue stations have wrong
  Wikidata coordinates and were left out of the route (their dates equal their neighbours').
  The Polo Grounds shuttle is straight lines between three stations (estimated).
* Elevated stretch dates come from station days only. The Ninth Avenue line therefore starts
  with its first stations (14 Feb 1870, Barclay – Warren Street) and not with the July 1868 trial
  on Greenwich Street; the Brooklyn Bridge tracks start with the elevated trains of 18 Jun 1898,
  not the cable railway of 24 Sep 1883.
* OpenHistoricalMap's dates for railroads are taken as mapped; bare years are mid-year. Yard and
  siding tracks without a dated way take the nearest dated track (713 segments); 562 segments
  with nothing dated within 400 m are left out (mostly Staten Island freight tracks and the New
  Jersey margin). Railroad stations are labels only; 71 of 109 are known to the year only.
* Railroad rows from memory of the articles, to be checked: Empire Connection 7 Apr 1991; West
  Side cut 1937; Spuyten Duyvil & Port Morris 1871. Queensboro Bridge elevated service
  23 Jul 1917 – 13 Jun 1942 (from the Second Avenue line article as remembered, not re-read).
* The High Line is only the pieces OpenStreetMap still maps as abandoned railway (0.9 km of
  the 2.3 km viaduct); the southern part to St. John's Park Terminal is not drawn.
* Not included: the LIRR and Metro-North as train services (tracks and station labels only),
  PATH trains, AirTrain, streetcars, the Park Avenue elevated in Brooklyn (1885–91), surface
  predecessors of the Sea Beach / West End / Culver lines, the 1939–40 World's Fair spur, the
  Sedgwick / Bronx Park / 58th Street stubs, earlier station names (only Jay Street – Borough Hall
  and Lawrence Street are in `transit_station_names.csv`).
* The 2 / 3 between Borough Hall and Hoyt Street (Clark Street tunnel approach, 15 Apr 1919) runs
  beside the 1908 line and is drawn from 1908.
