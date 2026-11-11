# Outer counties: railway stations and airfields (2026-11-11)

Files: `data/tables/transit_stations_outer.csv` (302 rows), `data/tables/airports_outer.csv` (29 rows).
Nothing here was run through the pipeline; `transit.py` and `airports.py` do not read these files yet.

## 1. How the seven counties are wired (what the lead has to match)

### Railway stations
* `pipeline/transit.py`, `main()`: `stations = pd.read_csv(TABLES / "transit_stations.csv", dtype=str, keep_default_na=False)`.
  The same frame goes to `dated_network(openings, gt, stations)`, `manual_lines(openings, stations, ground)` and
  `station_rows(stations, ...)`; `openings` is `transit_openings.csv`.
* Columns (exactly): `system,code,name,opened,closed,note,source,line,structure,lon,lat`.
  `system` = lirr / mnr / njt / hblr / nlr / path / sir / el / subway / rail (free text; only `subway, sir, el, path` are
  "heavy" in `station_rows`; everything else is written as viewer system `muni`, a label with no platform).
  `code` = Wikidata Q-id (unique key; the optional `transit_station_names.csv` joins on system+code). `opened` / `closed` =
  ISO day (a year-only source is written `YYYY-07-01` and the note says "estimated"). `structure` is empty for all county rows.
  `line` is free text (the line's name). `lon,lat` WGS84.
* County rows are tagged `[counties] ` at the start of `note` and are rewritten by
  `data/manual/transit/tools/build_county_stations.py` (OpenStreetMap node positions, Wikidata/infobox days; Overpass). My rows carry
  `[outer] ` instead. A station with an empty `opened` gets the opening year of the nearest railroad track within 250 m
  (`track_year`, built from the `rr` tracks); with no track it is dropped. `closed` empty = 9999. `end <= start` rows are dropped.
  Only stations inside `extent_poly()` (the map outline, `extent.py` / `data/manual/extent_counties.json`) are kept.
* Closed stations of the counties were put in system `rail`; open ones keep the operator's system (`mnr`, `njt`). I followed that:
  LIRR stations of any state (open or closed) are `lirr`, as in the city's table.

### Airfields
* `pipeline/airports.py`, `main()`: `t = pd.read_csv(TABLES / "airports.csv")`; the outlines (`g`, polygons whose class is in
  `AIRPORT_CLASSES`) come from `data/raw/overture/<release>/region_airports.parquet` (REGION_BBOX only), filtered by
  `extent.in_extent`; they are matched to the table **by `name` equal to the outline's name** (`ports.merge(t[["name","opened","closed","runway_width_m"]]
  .drop_duplicates("name"), on="name")`). An outline whose name is not in the table is "undated, left out" (the log lists them).
  Pavement (runways, taxiways, aprons) joins its airport by touching or the nearest outline within 1.5 km.
* Columns (exactly): `name,opened,closed,source_url,notes,runway_width_m` (years, not days; width optional).
* Fields gone from today's map (Floyd Bennett, Flushing, the Rockland and Westchester ones) have **no OSM outline**: they come from
  `data/manual/airports/extra_outlines.geojson` (properties `name`, `class`, geometry) and `extra_pavement.geojson`
  (`airport`, `kind`, `start_year`, `end_year`), and still need their row in the csv.
* `airports.csv` has no Nassau or Suffolk row (checked): Mitchel Field and Roosevelt Field are in my file, not duplicated.

## 2. What would have to change (patch description for the lead)

1. `transit.py` `main()`: read `transit_stations.csv` and, if present, `transit_stations_outer.csv`, `pd.concat` them (same columns,
   codes are unique and none is in the first file; verified). Run `build_county_stations.py`-style tools never over the new file: it
   is hand-assembled (below), not rewritten by a stage.
2. The `rail` rows of `transit_openings.csv` (`cty_*`) date the railroad **track**; the outer lines have none, so the 250 m
   fallback is what dates a station without a year (38 rows) and OHM / nearest-track dating covers the rest. Rows for the LIRR,
   Harlem, Hudson, New Haven, Port Jervis and NJ Transit lines in the outer box are the lead's (or another part's) to add.
3. `extent_poly()` must contain the outer counties, or every row is dropped by `poly.contains`.
4. `airports.py` line `t = pd.read_csv(TABLES / "airports.csv")`: concat with `airports_outer.csv`; point the airport read at an
   extract that covers `OUTER_BBOX` (today `region_airports.parquet` covers only REGION_BBOX; no outer airport file exists in
   `data/raw/overture/2026-10-21.0/`). Names in my file are the Wikipedia names; the OSM `name` of an outline may differ
   (noted in the row where I know it: "Long Island MacArthur", "Solberg Airport"): **compare the names of the outline file with
   the csv and rename rows to match**.
5. Closed fields (Mitchel Field 1918-1961, Roosevelt Field 1911-1951, Grumman Bethpage 1937-1996, Calverton 1954-2015) need
   outlines in `extra_outlines.geojson`; the csv rows alone draw nothing.

## 3. Railway stations: how the file was made

Sources (all fetched 2026-11-11, raw copies in `data/raw/outer_transport/`):
* **Wikidata SPARQL** (CC0), four boxes (Long Island, Hudson Valley, New Jersey, Connecticut), every item that is a (subclass of)
  railway station with a coordinate P625, opening P1619, closing P3999, line P81, operator P137 (`wd_*.json`), plus a second pass by
  English-Wikipedia sitelink for names in the station lists (`wd2_li/hv/nj.json`; the Connecticut pass was rate-limited and not
  retrieved). The endpoint allows one query per minute. Position = Wikidata's, rounded to five decimals; each point was assigned to a
  county by the TIGER 2024 polygons (`data/raw/tiger`), items already in `transit_stations.csv` (by code) dropped.
* **Wikipedia** (CC BY-SA; facts only), via `Special:Export` (the API is rate-limited): station tables with opening / closing days
  of Port Jervis Line, Danbury, Waterbury, New Canaan, Harlem, Hudson, New Haven lines, and NJ Transit's North Jersey Coast, Raritan Valley,
  Morristown, Montclair-Boonton, Gladstone, Northeast Corridor and Princeton Branch articles (`wp_*.xml`); the earlier lists of
  LIRR and Metro-North stations (`data/raw/transit/wikipedia/`) give an opening year for each current station, and the LIRR
  "disused and former stations" table gives opening and closing years.
* Rule for the opening: the **earliest** source wins (the station's first opening, not today's building: Hicksville 1837, not the
  station house); a day is `exact` only where a table or Wikidata gives a day, every other year is `YYYY-07-01` and "estimated" in
  the note. When two sources differ by more than two years the later one is named in the note ("list gives ...").
  Closing: Wikidata P3999, else the line article, else the list of disused stations.
* Stations whose first station closed and a new one opened (New Hamburg 1849-1973 and 1981; Wassaic 1852-1972 and 2000) have two rows
  (second code ends `-2`).
* Dropped: freight stations, museums, towers, bus/airport stops, open-ended items with no line and no date (Wikidata has
  Miller Place, Hermanville, Wampmissic, Rondout ... with nothing to date them), the Roselle-Roselle Park item (its coordinate is wrong:
  40.44 N, in Middlesex; the station is in Union County, on the map already).

Counts (rows; lirr / mnr / njt / rail = closed or non-Metro-North, non-NJT):

| County | lirr | mnr | njt | rail |
|---|---|---|---|---|
| Nassau | 63 | | | |
| Suffolk | 75 | | | |
| Putnam | | 7 | | |
| Dutchess | | 12 | | 9 |
| Orange | | 6 | | 3 |
| Ulster | | | | 7 (Ulster & Delaware, Ashokan reservoir stations closed 1913, Kingston Point) |
| Western Connecticut | | 24 | | 8 |
| Greater Bridgeport | | 5 | | |
| South Central Connecticut | | 4 | | 8 (Shore Line East, Hartford Line, closed ones) |
| Middlesex NJ | | | 11 | |
| Monmouth | | | 14 | |
| Ocean | | | 2 | |
| Somerset | | | 11 | 2 |
| Morris | | | 15 | 2 |
| Hunterdon | | | 4 | 1 |
| Mercer | | | 4 | 5 (River Line, West Trenton, closed ones) |
| Sussex, Sullivan, Pike | 0 | 0 | 0 | 0 |

By line (largest): Montauk Branch 26, North Jersey Coast 21, Port Jefferson 18, New Haven Line 15, Ronkonkoma 14, Danbury 13, Babylon 13,
Main Line 13, Harlem 12, Oyster Bay 12, Morristown 11, Raritan Valley 10, Gladstone 8, Hudson 6, Port Jervis 6 ... 33 rows (mostly
closed) have no line. 78 rows have a closing date (LIRR 44, rail 34). 80 rows have an exact opening day (Wikidata or a table), 188 carry
at least one estimated item, 29 have no opening at all (the stage dates them from their track): East Norwalk-type rows of the New Haven
Line were filled with the line's opening (Greenwich, Riverside 25 Dec 1848; Noroton Heights, Rowayton, East Norwalk, Green's Farms 1849;
Dykeman's, Towner's 1848; Cold Spring 1849), **estimated**, the station's own year not found.

## 4. Airfields

29 rows (`airports_outer.csv`). Each note starts READ (a fact read in the Wikipedia article in this round: quoted) or says
UNVERIFIED / ESTIMATED (year from general knowledge or a placeholder inside a stated range: Kingston-Ulster, Warwick, Somerset, Sussex,
Princeton, Stewart, Lakehurst, Sikorsky, Grumman Bethpage, Calverton's opening, Hudson Valley 1935, Sullivan 1965). 18 rows start READ (
other 11 are not. Closed: Mitchel Field 1961 (READ), Roosevelt Field 1951 (READ), Grumman Bethpage 1996, Calverton 2015.

Not done: airfields-freeman.com was not fetched (no call budget), so the lesser closed fields of Nassau, Suffolk, Orange, Dutchess,
Ulster, Sullivan, Monmouth, Ocean, Middlesex and Somerset are missing (Zahn's, Bayport, Wading River, Warwick's earlier fields ...), and
so are Orange County's Randall Airport, Sky Acres, Stormville, Wurtsboro, Ellenville, Central Jersey Regional, Lakewood, Red Bank,
Old Bridge, Marlboro (founded 1922 according to its article, READ), Flying W, Sky Manor, Robbinsville, Pike County. Greenwood Lake
Airport (West Milford) is inside the present map. No runway widths are given.

## 5. What is missing

* Former LIRR stations of Nassau and Suffolk that Wikidata holds without a coordinate (about 70: Meadowbrook, Mitchel Field,
  Roosevelt Raceway, Motor Parkway, Hempstead Plains stops, Pilgrim State, Camp Upton, Bluepoint, Goose Creek ...): names and years are
  in the Wikipedia list; positions would need the OpenStreetMap map API or old maps. Rocky Point, Shoreham, Sag Harbor, Noyack Road
  and Laurel are included (positions from the sitelink pass).
* Metro-North Port Jervis Line: Tuxedo and Otisville (Wikidata has no coordinate in the box query), and the Waterbury Branch's
  Ansonia, Derby-Shelton, Seymour, Beacon Falls, Naugatuck, Waterbury (most outside OUTER_BBOX or not retrieved); Manitou (Putnam).
  Chester, Goshen, Monroe (closed 1983-84) have no coordinate.
* Sussex, Sullivan, Pike and Ulster (Amtrak/Hudson: Kingston is Rhinecliff, in Dutchess, present) have no passenger stations of the
  kind asked for; Ocean has only Bay Head and Point Pleasant Beach (Wikidata items), Manasquan is in Monmouth.
* Hartford Line and Shore Line East appear only where Wikidata has an item in the box; the SLE "service began" day (Dec 2001 /
  May 1990) is not an opening of the station and was not used. Branford, Guilford, Madison carry Wikidata's 1990.
* Structure (surface / elevated) is empty everywhere, as in the county rows.
* Hudson Line, Harlem Line, Port Jervis Line dates come from the line articles, which give "year" more often than a day; a
  day-precision pass through the stations' own articles (as `infobox.py` did for the counties) was not done: it would turn about 100
  estimated openings into days.
* Not checked: coordinates against the track (the stage snaps heavy stations only); Wikidata coordinates are the article's
  and can be tens of metres off (platform vs. station house); one was found wrong (Roselle-Roselle Park). Amtrak: Poughkeepsie,
  Rhinecliff, Trenton, Princeton Junction, Metropark, New Brunswick, Stamford, Bridgeport, New Haven (Union) are present through Wikidata;
  there is no separate Amtrak column.

## 6. Licences

Wikidata: CC0. Wikipedia text: CC BY-SA 4.0, only dates and facts are used (cite the article in `source`). TIGER: public domain.
No OpenStreetMap data used here. Add the three entries to `SOURCES.md` (not edited by this part).
