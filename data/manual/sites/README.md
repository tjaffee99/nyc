# Military and industrial sites (`data/manual/sites/`)

Forts, navy yards, bases, rail yards, gasworks, power plants, refineries, shipyards, works, markets, landfills and the island institutions shaped the city, and today's data dates them badly: exempt and industrial property carries the lot's year on every building (Rikers Island: 201 buildings at 1933; Fort Tilden: 50 at 1900-01), an imputed year, or - where the site is gone - nothing at all. This folder holds the researched sites: their outlines and years, the years of standing buildings inside them, and the structures that are gone. Ported from the Bay project's `data/manual/industrial_sites/` (its decisions 38 and 42), with one difference that matters: the map-edition brackets, which dated 984 footprints there, were tested against independent records here and mostly failed (see "What the map brackets are worth").

## Files

| file | what |
|---|---|
| `sites.geojson` | 121 site features (one per site and name period), WGS84 |
| `../../tables/known_building_dates.sites.csv` | 130 rows: 13 researched years of standing buildings (text), 28 years from USGS map editions (`site_map:` ids, estimated), 50 lot-stamp fixes (`site_stamp:` ids, estimated), 39 site floors (`site_floor:` ids, not dates) |
| `../../tables/notable_demolished.sites.csv` | 24 structures that are gone (11 with an outline, the rest as `footprint_m` + `rotation_deg`) |
| `edition_brackets.csv` | every footprint read on the USGS editions (1645 rows, 52 sites): EVIDENCE ONLY - do not apply it beyond the rows already in the building table |
| `tools/` | `sites_def.py`, `sites_def2.py` (the sites), `buildings_def.py`, `demolished_def.py`, `build.py`, `build_buildings.py`, `build_demolished.py`, `readme.py`; `geom.py` (outlines), `fetch_wp.py` + `wp_titles.txt` + `wp_facts.py` (source text), `topo.py`, `date_editions.py`, `run_editions.py` (USGS editions), `audit.py` |

Downloads are in `data/raw/sites/` (`wp/` article text, `usgs/` sheet crops and metadata), scratch in `data/interim/sites/` (`audit.csv`, `editions/`). Rebuild (a few minutes; `run_editions.py` about 30 minutes cold, each process under 1 GB):

```
cd data/manual/sites
../../../.venv/bin/python -I tools/fetch_wp.py          # cached; one request a second
../../../.venv/bin/python -I tools/build.py --check       # sites.geojson; lists years the source text lacks
../../../.venv/bin/python -I tools/run_editions.py        # edition_brackets.csv (--rebracket: from saved readings)
../../../.venv/bin/python -I tools/build_buildings.py     # known_building_dates.sites.csv
../../../.venv/bin/python -I tools/build_demolished.py    # notable_demolished.sites.csv
../../../.venv/bin/python -I tools/audit.py               # the built file's years inside each site
../../../.venv/bin/python -I tools/readme.py              # this file
```

### `sites.geojson` properties

`id`, `name` (the name in use over `start_year`..`end_year`; a renamed site has one feature per name), `kind` (`fort` | `military_base` | `navy_yard` | `rail_yard` | `gasworks` | `power_plant` | `refinery` | `shipyard` | `factory` | `terminal` | `landfill` | `quarry` | `prison` | `hospital_campus` | `asylum` | `other`), `start_year`, `end_year` (9999 = still that), `after` (`park` | `city` | `vacant` | `same` = the ground stays as `ground` under its next name), `ground` (`paved` | `yard` | `open`: how the terrain should show it), `label`, `source_url`, `note` (says "estimated" for every year or outline that is), plus `date_basis` (`text` | `estimated` for the start year), `floor` (a floor row exists), `area_ha`, `lon`, `lat` (a point inside).

Features overlap on purpose where a site was renamed (Fort Columbus / Fort Jay, Blackwell's / Welfare Island, Morse / Bethlehem). An outline is today's or the last mapped one: where the ground is made land (Governors Island's south, the Navy Yard's east, Rikers, Ellis Island, the yards on fill) the terrain's land year decides when the ground exists - paint a site cell only once it is land. Fort Lafayette's island is water today.

## Method

**Years** are from text: the Wikipedia article named in `source_url` (CC BY-SA; facts only), whose wikitext is cached in `data/raw/sites/wp/` and was searched for each year (`tools/wp_facts.py grep`; `build.py --check` fails a year the article does not contain unless the note calls it estimated). A year the article gives only loosely ('around 1851', 'by 1880', 'until the 1970s') is in the table as estimated. No founding year of a site comes from a map bracket. A site without a citable founding year was left out (list at the end).

**Outlines**: OpenStreetMap land-use and island polygons (Overture 2026-10-21.0 `region5_land_use`, `base_land`; ODbL) where the site, or the park or estate that took its ground, is mapped; Landmarks Preservation Commission historic districts (Governors Island, Fort Totten, Sea View, Eberhard Faber; the city's file is in State Plane feet although its header says CRS84 - `geom.lpc` reprojects it); street blocks polygonized from today's streets (`geom.block`); Fort Lafayette's island traced on the USGS The Narrows sheet. Everything else is a circle or a hand-given ring around the cited location and says "Outline estimated" - the tax lots on disk have no geometry, so no site is outlined from its lots.

**Standing buildings** (`buildings_def.py`): the footprint is found from the name OpenStreetMap gives a building inside the site, or from the article's coordinates, and its BIN read from `nyc_footprints_raw.parquet`. A row is not written where the built file already has an LPC year within five years (20 of the 33 buildings checked: most armories, the IRT powerhouse, Castle Williams, Liggett Hall ...).

**Site floors**: one `site_floor:<site id>` row per site whose outline is a mapped one and whose founding is from text: no building inside the outline predates the founding. Meant for estimated years only (LPC and recorded years stand: Governors Island, Fort Totten and Welfare Island keep buildings older than a later name). Where the assessor's year is the lot's year stamped on the site's buildings and older than the site, the floor is written out as rows (50 `site_stamp:` rows, all in fort_tilden), because the pipeline's floor does not reach recorded years.

**Structures that are gone** (`demolished_def.py`): outlines of Fort Lafayette, the two Elmhurst gas holders, five holders of the Gas House District, Goldwater Memorial Hospital and City Hospital were read on USGS 1:24,000 sheets in a metre grid (`topo.py render`; NAD27 by PROJ's three-parameter shift, +-10 m); Waterside is its two street blocks; the rest are rectangles from cited or estimated dimensions.

### What the map brackets are worth

`date_editions.py` reads every footprint of a site on each USGS 1:24,000 edition (1947 editions from 1940-42 photographs, 1954-57, 1966, 1977-81 photorevisions, 1995-98) and on the calibrated 1890s 1:62,500 sheets: *drawn* when black (or revision purple) ink, opened by 6 m, or hatching, covers 30 % of the footprint. The first sheet that draws a footprint after a sheet that leaves it empty brackets its year. Tested on the 1645 footprints of 52 sites:

* 319 footprints have an independent year (LPC exact, or an assessor year not shared by the lot). 49 of them got a clean absent-then-drawn bracket. **The independent year lay inside the bracket for 3.** For 35 the building is older than the bracket (Governors Island's 1870s houses 'absent 1940, drawn 1954'), for 11 newer.
* Of 180 footprints independently dated to 1935 or earlier, 129 (72 %) are drawn on the first 1:24,000 sheet. Military posts are the worst (Governors Island 33 of 59, Fort Totten 27 of 39): the 1947 editions leave most buildings of a reservation off. Elsewhere about one old building in six is missed on a sheet, and the misses repeat on the next sheet (Sea View: 4 of 37 old pavilions bracketed 30-40 years late).
* The 1947 editions fill built-up blocks solid black and rail-yard track fans read as buildings, so *drawn* is not evidence for a single footprint there (seen on the Coney Island and 207th Street yards).
* `tools/validate_brackets.py` prints these numbers.

So the brackets are **not** used as the Bay project used them. `build_buildings.py` writes a map year only for 7 isolated civil campuses and plants founded after 1925 (28 rows): 20 footprints drawn on the first sheet after the site's founding take the founding year (the true year lies between the founding and that sheet), and 8 absent-then-drawn brackets on Rikers Island, where the sheets were also looked at (the 1977 and 1997 revisions print the new jails in purple). These rows could not be checked against records - no building in those sites has an independent year inside a bracket - and all say "estimated". Everything else stays in `edition_brackets.csv` as readings, not dates.

## Sites

121 features: 21 rail_yard, 13 hospital_campus, 12 fort, 12 factory, 10 terminal, 10 asylum, 9 landfill, 8 military_base, 7 other, 7 shipyard, 4 power_plant, 2 gasworks, 2 refinery, 2 prison, 1 navy_yard, 1 quarry. Start years: 113 from text, 8 estimated, 0 from map brackets. End years: 80 sites have ended, 11 of those years are estimated. Outlines: 88 mapped, 33 estimated.

| id | name | kind | years | estimated | outline | source (en.wikipedia.org/wiki/...) |
|---|---|---|---|---|---|---|
| `governors_island_fort_jay_1794` | Fort Jay | fort | 1794-1809 | end | LPC district | Governors_Island |
| `governors_island_fort_columbus` | Fort Columbus | fort | 1809-1904 | start | LPC district | Governors_Island |
| `governors_island_army_1904` | Fort Jay | military_base | 1904-1966 | - | OpenStreetMap | Governors_Island |
| `governors_island_coast_guard` | Coast Guard Support Center Governors Island | military_base | 1966-1996 | - | OpenStreetMap | Governors_Island |
| `fort_wood` | Fort Wood | fort | 1806-1937 | - | OpenStreetMap | Liberty_Island |
| `fort_gibson` | Fort Gibson | fort | 1808-1890 | outline | estimated | Ellis_Island |
| `ellis_island_station` | Ellis Island immigration station | other | 1892-1954 | - | OpenStreetMap | Ellis_Island |
| `fort_hamilton` | Fort Hamilton | fort | 1825- | - | OpenStreetMap | Fort_Hamilton |
| `fort_wadsworth_1806` | Fort Richmond and Fort Tompkins | fort | 1806-1865 | - | OpenStreetMap | Fort_Wadsworth |
| `fort_wadsworth` | Fort Wadsworth | fort | 1865-1994 | - | OpenStreetMap | Fort_Wadsworth |
| `fort_at_willets_point` | Fort at Willets Point | fort | 1862-1898 | - | LPC district | Fort_Totten_(Queens) |
| `fort_totten` | Fort Totten | fort | 1898-1974 | - | OpenStreetMap | Fort_Totten_(Queens) |
| `fort_schuyler` | Fort Schuyler | fort | 1833-1934 | - | OpenStreetMap | Fort_Schuyler |
| `suny_maritime_college` | New York State Maritime College (Fort Schuyler) | other | 1934- | - | OpenStreetMap | Fort_Schuyler |
| `fort_tilden` | Fort Tilden | fort | 1917-1974 | end | OpenStreetMap | Fort_Tilden |
| `fort_lafayette` | Fort Lafayette | fort | 1812-1960 | - | USGS sheet | Fort_Lafayette |
| `nas_new_york` | Naval Air Station New York | military_base | 1941-1971 | end | OpenStreetMap | Floyd_Bennett_Field |
| `miller_field` | Miller Field | military_base | 1919-1969 | - | OpenStreetMap | Miller_Field_(Staten_Island) |
| `nas_rockaway` | Naval Air Station Rockaway | military_base | 1917-1930 | outline | estimated | Naval_Air_Station_Rockaway |
| `brooklyn_navy_yard` | Brooklyn Navy Yard | navy_yard | 1801-1966 | - | OpenStreetMap | Brooklyn_Navy_Yard |
| `brooklyn_navy_yard_industrial` | Brooklyn Navy Yard | factory | 1969- | - | OpenStreetMap | Brooklyn_Navy_Yard |
| `brooklyn_naval_hospital` | Brooklyn Naval Hospital | hospital_campus | 1838-1948 | - | OpenStreetMap | Brooklyn_Naval_Hospital |
| `brooklyn_army_base` | Brooklyn Army Base | military_base | 1919-1966 | - | OpenStreetMap | Brooklyn_Army_Terminal |
| `brooklyn_army_terminal` | Brooklyn Army Terminal | terminal | 1981- | - | OpenStreetMap | Brooklyn_Army_Terminal |
| `naval_station_new_york` | Naval Station New York | military_base | 1990-1994 | - | OpenStreetMap | Naval_Station_New_York |
| `stapleton_piers` | Stapleton piers (Foreign-Trade Zone No. 1) | terminal | 1920-1975 | end, outline | estimated | Stapleton,_Staten_Island |
| `halloran_general_hospital` | Halloran General Hospital | hospital_campus | 1942-1947 | - | OpenStreetMap | Halloran_General_Hospital |
| `willowbrook_state_school` | Willowbrook State School | asylum | 1947-1987 | - | OpenStreetMap | Willowbrook_State_School |
| `quarantine_tompkinsville` | The Quarantine | hospital_campus | 1799-1858 | outline | estimated | Staten_Island_Quarantine_War |
| `hoffman_island_quarantine` | Hoffman Island Quarantine | hospital_campus | 1873-1938 | end | OpenStreetMap | Hoffman_Island |
| `swinburne_island_quarantine` | Swinburne Island Quarantine | hospital_campus | 1870-1938 | end | OpenStreetMap | Swinburne_Island |
| `seamens_retreat` | Seamen's Retreat / U.S. Marine Hospital (Bayley Seton) | hospital_campus | 1831- | - | street blocks | Bayley_Seton_Hospital |
| `sailors_snug_harbor` | Sailors' Snug Harbor | other | 1831-1976 | - | OpenStreetMap | Sailors'_Snug_Harbor |
| `creedmoor_rifle_range` | Creedmoor Rifle Range | military_base | 1873-1907 | - | OpenStreetMap | Creedmoor_Rifle_Range |
| `sunnyside_yard` | Sunnyside Yard | rail_yard | 1910- | - | OpenStreetMap | Sunnyside_Yard |
| `thirtieth_street_yard` | 30th Street Yard | rail_yard | 1851-1987 | start | OpenStreetMap | West_Side_Yard |
| `west_side_yard` | West Side Yard | rail_yard | 1987- | - | OpenStreetMap | West_Side_Yard |
| `st_johns_park_freight_terminal` | St. John's Park Freight Depot | rail_yard | 1867-1927 | outline | estimated | St._John's_Park |
| `sixtieth_street_yard` | 60th Street Yard | rail_yard | 1880-1975 | start, end, outline | estimated | Riverside_South,_Manhattan |
| `bay_ridge_65th_street_yard` | Bay Ridge Yard | rail_yard | 1876- | - | OpenStreetMap | 65th_Street_Yard |
| `coney_island_yard` | Coney Island Yard | rail_yard | 1926- | - | OpenStreetMap | New_York_City_Subway_yards |
| `yard_207th_street` | 207th Street Yard | rail_yard | 1932- | - | OpenStreetMap | IND_Eighth_Avenue_Line |
| `jamaica_yard` | Jamaica Yard | rail_yard | 1936- | - | OpenStreetMap | New_York_City_Subway_yards |
| `corona_yard` | Corona Yard | rail_yard | 1928- | - | OpenStreetMap | New_York_City_Subway_yards |
| `livonia_yard` | Livonia Yard | rail_yard | 1923- | - | OpenStreetMap | New_York_City_Subway_yards |
| `pitkin_yard` | Pitkin Yard | rail_yard | 1948- | - | OpenStreetMap | New_York_City_Subway_yards |
| `concourse_yard` | Concourse Yard | rail_yard | 1933- | - | OpenStreetMap | New_York_City_Subway_yards |
| `canarsie_yard` | Canarsie (Rockaway Parkway) Yard | rail_yard | 1917- | - | OpenStreetMap | New_York_City_Subway_yards |
| `east_new_york_yard` | East New York Yard | rail_yard | 1885- | - | OpenStreetMap | New_York_City_Subway_yards |
| `yard_239th_street` | 239th Street Yard | rail_yard | 1916- | - | OpenStreetMap | New_York_City_Subway_yards |
| `unionport_yard` | East 180th Street and Unionport Yards | rail_yard | 1918- | start | OpenStreetMap | New_York_City_Subway_yards |
| `morris_park_shops` | Morris Park Shops | rail_yard | 1889- | - | OpenStreetMap | Morris_Park_Facility |
| `hillside_facility` | Hillside Maintenance Complex (Long Island Rail Road) | rail_yard | 1991- | - | OpenStreetMap | Hillside_Facility |
| `brooklyn_eastern_district_terminal` | Brooklyn Eastern District Terminal | rail_yard | 1906-1983 | - | OpenStreetMap | Brooklyn_Eastern_District_Terminal |
| `harlem_river_yard` | Harlem River Yard | rail_yard | 1991- | outline | estimated | Harlem_River_Intermodal_Yard |
| `elmhurst_gas_tanks` | Elmhurst gas tanks | gasworks | 1910-1996 | - | OpenStreetMap | Elmhurst_gas_tanks |
| `gashouse_district` | Gas House District | gasworks | 1842-1945 | outline | estimated | Stuyvesant_Town%E2%80%93Peter_Cooper_Village |
| `waterside_station` | Waterside Generating Station | power_plant | 1901-2005 | - | street blocks | Waterside_Generating_Station |
| `east_river_station` | East River Generating Station | power_plant | 1926- | - | OpenStreetMap | East_River_Generating_Station |
| `ravenswood_station` | Ravenswood Generating Station | power_plant | 1963- | - | OpenStreetMap | Ravenswood_Generating_Station |
| `poletti_power_project` | Charles Poletti Power Project (Astoria 6) | power_plant | 1977-2010 | - | OpenStreetMap | Charles_Poletti_Power_Project |
| `astral_oil_works` | Astral Oil Works | refinery | 1867-1949 | end, outline | estimated | Astral_Oil_Works |
| `standard_oil_brooklyn_refinery` | Standard Oil Brooklyn Refinery | refinery | 1870-1966 | start, outline | estimated | Greenpoint_oil_spill |
| `burlee_staten_island_shipbuilding` | Burlee Dry Dock / Staten Island Shipbuilding (Mariners Harbor) | shipyard | 1903-1938 | outline | estimated | Bethlehem_Staten_Island |
| `bethlehem_staten_island` | Bethlehem Steel shipyard | shipyard | 1938-1959 | outline | estimated | Bethlehem_Staten_Island |
| `morse_dry_dock` | Morse Dry Dock and Repair Company (56th Street) | shipyard | 1900-1938 | start, outline | estimated | Bethlehem_Brooklyn_56th_Street |
| `bethlehem_56th_street` | Bethlehem Steel shipyard | shipyard | 1938-1963 | outline | estimated | Bethlehem_Brooklyn_56th_Street |
| `erie_basin_dry_docks` | Erie Basin dry docks | shipyard | 1866-2008 | outline | estimated | Robins_Dry_Dock_and_Repair_Company |
| `continental_iron_works` | Continental Iron Works | shipyard | 1861-1928 | outline | estimated | Continental_Iron_Works |
| `morgan_iron_works` | Morgan Iron Works | factory | 1838-1907 | outline | estimated | Morgan_Iron_Works |
| `allaire_iron_works` | Allaire Iron Works | factory | 1816-1869 | outline | estimated | Allaire_Iron_Works |
| `shooters_island_shipyard` | Townsend-Downey Shipyard | shipyard | 1898-1910 | - | OpenStreetMap | Shooters_Island |
| `steinway_factory` | Steinway & Sons | factory | 1870- | - | OpenStreetMap | Steinway,_Queens |
| `havemeyers_elder_refinery` | Havemeyers & Elder sugar refinery | factory | 1856-1882 | outline | estimated | Domino_Sugar_Refinery |
| `domino_sugar_refinery` | Domino Sugar Refinery | factory | 1882-2004 | outline | estimated | Domino_Sugar_Refinery |
| `pfizer_brooklyn` | Chas. Pfizer & Co. | factory | 1849-2008 | outline | estimated | Pfizer |
| `eberhard_faber_pencil_factory` | Eberhard Faber Pencil Company | factory | 1872-1956 | - | LPC district | Eberhard_Faber_Pencil_Factory |
| `port_ivory` | Port Ivory (Procter & Gamble) | factory | 1907-1991 | outline | estimated | Port_Ivory,_Staten_Island |
| `kreischer_brick_works` | Kreischer Brick Works | factory | 1854-1927 | outline | estimated | Charleston,_Staten_Island |
| `kreischer_clay_pits` | Kreischer clay pits | quarry | 1854-1927 | start, outline | estimated | Clay_Pit_Ponds_State_Park_Preserve |
| `nassau_smelting` | Nassau Smelting and Refining (Tottenville) | factory | 1900-2001 | outline | estimated | Tottenville,_Staten_Island |
| `bush_terminal` | Bush Terminal | terminal | 1895- | outline | estimated | Bush_Terminal |
| `fulton_fish_market` | Fulton Fish Market | terminal | 1822-2005 | outline | estimated | Fulton_Fish_Market |
| `washington_market` | Washington Market | terminal | 1813-1967 | end, outline | estimated | Washington_Market |
| `gansevoort_market` | Gansevoort Market | terminal | 1879- | - | street blocks | Meatpacking_District,_Manhattan |
| `hunts_point_produce_market` | Hunts Point Market | terminal | 1967- | - | OpenStreetMap | Hunts_Point,_Bronx |
| `hunts_point_meat_market` | Hunts Point Cooperative (Meat) Market | terminal | 1974- | - | OpenStreetMap | Hunts_Point,_Bronx |
| `new_fulton_fish_market` | New Fulton Fish Market | terminal | 2005- | - | OpenStreetMap | Fulton_Fish_Market |
| `bronx_terminal_market` | Bronx Terminal Market | terminal | 1935-2006 | - | OpenStreetMap | Bronx_Terminal_Market |
| `fresh_kills_landfill` | Fresh Kills Landfill | landfill | 1948-2001 | - | OpenStreetMap | Fresh_Kills_Landfill |
| `brookfield_landfill` | Brookfield Avenue Landfill | landfill | 1966-1980 | end | OpenStreetMap | Fresh_Kills_Landfill |
| `corona_ash_dumps` | Corona Ash Dumps | landfill | 1910-1934 | outline | estimated | Flushing_Meadows%E2%80%93Corona_Park |
| `pelham_bay_landfill` | Pelham Bay Landfill (Tallapoosa Point) | landfill | 1963-1978 | outline | estimated | Pelham_Bay_Park |
| `pennsylvania_avenue_landfill` | Pennsylvania Avenue Landfill | landfill | 1956-1979 | - | OpenStreetMap | Shirley_Chisholm_State_Park |
| `fountain_avenue_landfill` | Fountain Avenue Landfill | landfill | 1961-1985 | - | OpenStreetMap | Shirley_Chisholm_State_Park |
| `edgemere_landfill` | Edgemere Landfill | landfill | 1938-1991 | - | OpenStreetMap | Edgemere_Landfill |
| `ferry_point_landfill` | Ferry Point landfill | landfill | 1952-1970 | - | OpenStreetMap | Ferry_Point_Park |
| `barren_island_works` | Barren Island works | factory | 1859-1934 | outline | estimated | Barren_Island,_Brooklyn |
| `rikers_island_landfill` | Rikers Island dump | landfill | 1884-1932 | - | OpenStreetMap | Rikers_Island |
| `rikers_island_jails` | Rikers Island jails | prison | 1932- | - | OpenStreetMap | Rikers_Island |
| `blackwells_island` | Blackwell's Island | prison | 1828-1921 | - | OpenStreetMap | Roosevelt_Island |
| `welfare_island` | Welfare Island | hospital_campus | 1921-1973 | - | OpenStreetMap | Roosevelt_Island |
| `hart_island` | Hart Island potter's field | other | 1868- | - | OpenStreetMap | Hart_Island |
| `north_brother_island` | Riverside Hospital | hospital_campus | 1885-1963 | - | OpenStreetMap | North_and_South_Brother_Islands_(New_York_City) |
| `randalls_island_institutions` | House of Refuge | asylum | 1845-1935 | - | OpenStreetMap | Randalls_and_Wards_Islands |
| `wards_island_institutions` | Wards Island asylum | asylum | 1847-1899 | - | OpenStreetMap | Randalls_and_Wards_Islands |
| `manhattan_state_hospital` | Manhattan State Hospital | asylum | 1899-1936 | end | OpenStreetMap | Manhattan_Psychiatric_Center |
| `manhattan_psychiatric_center` | Manhattan Psychiatric Center | asylum | 1936- | start | OpenStreetMap | Manhattan_Psychiatric_Center |
| `richmond_county_poor_farm` | Richmond County Poor Farm | asylum | 1829-1898 | - | OpenStreetMap | New_York_City_Farm_Colony |
| `new_york_city_farm_colony` | New York City Farm Colony | asylum | 1898-1975 | - | OpenStreetMap | New_York_City_Farm_Colony |
| `seaview_hospital` | Sea View Hospital | hospital_campus | 1905- | - | LPC district | Seaview_Hospital |
| `creedmoor_state_hospital` | Creedmoor State Hospital | asylum | 1912- | - | OpenStreetMap | Creedmoor_Psychiatric_Center |
| `kings_county_hospital` | Kings County Hospital | hospital_campus | 1831- | - | OpenStreetMap | Kings_County_Hospital_Center |
| `long_island_state_hospital` | Long Island State Hospital (Kingsboro Psychiatric Center) | asylum | 1895- | - | OpenStreetMap | Kingsboro_Psychiatric_Center |
| `bellevue_hospital` | Bellevue Hospital | hospital_campus | 1798- | - | OpenStreetMap | Bellevue_Hospital |
| `bronx_state_hospital` | Bronx State Hospital (Bronx Psychiatric Center) | asylum | 1963- | - | OpenStreetMap | Bronx_Psychiatric_Center |
| `bronx_municipal_hospital` | Bronx Municipal Hospital Center (Jacobi) | hospital_campus | 1955- | - | OpenStreetMap | Jacobi_Medical_Center |
| `kingsbridge_veterans_hospital` | Veterans' Hospital, Kingsbridge Road | hospital_campus | 1922- | - | OpenStreetMap | James_J._Peters_VA_Medical_Center |
| `freedomland` | Freedomland U.S.A. | other | 1960-1964 | outline | estimated | Freedomland_U.S.A. |
| `steeplechase_park` | Steeplechase Park | other | 1897-1964 | outline | estimated | Steeplechase_Park |
| `luna_park_1903` | Luna Park | other | 1903-1944 | - | OpenStreetMap | Luna_Park_(Coney_Island,_1903) |

The `note` of each feature says how its years were obtained and what is estimated.

## Standing buildings with a researched year

| id | name | BIN | year | note |
|---|---|---|---|---|
| `bat_building_a` | Brooklyn Army Terminal Building A | 3413923 | 1919 | Built May 1918 - September 1919. (the built file had 1930 from heap_about+spread) |
| `bat_building_b` | Brooklyn Army Terminal Building B | 3347532 | 1919 | Built May 1918 - September 1919. (the built file had 1929 from heap_about+spread) |
| `fw_battery_weed` | Battery Weed (Fort Richmond) | 5163514 | 1861 | Built 1845-1861. (the built file had 1853 from lpc) |
| `fh_caponier` | Fort Hamilton caponier (Harbor Defense Museum) | 3345713 | 1831 | Part of the fort completed 1831 (estimated: the article dates the fort). (the built file had 1933 from heap_about+spread) |
| `fs_fort_schuyler` | Fort Schuyler | 2100433 | 1856 | Begun 1833, dedicated 1856. (the built file had 1844 from lpc) |
| `ssh_music_hall` | Sailors' Snug Harbor Music Hall | 5113037 | 1892 | Music hall of 1892 (R. W. Gibson). (the built file had 1900 from assessor) |
| `ri_smallpox_hospital` | Smallpox Hospital (ruin) | 1090045 | 1856 | Opened 1856 (wings 1903-05); a ruin since the 1950s, still standing. (the built file had 2028 from lpc) |
| `armory_fort_washington_avenue` | Fort Washington Avenue Armory (22nd Regiment) | 1063381 | 1911 | Built 1911. (the built file had 1944 from assessor) |
| `armory_13th_regiment` | 13th Regiment Armory (Sumner Armory) | 3045367 | 1894 | Completed 1894. (the built file had 1933 from heap_about+spread) |
| `armory_flushing` | Flushing Armory | 4112351 | 1906 | Built 1906. (the built file had 1901 from assessor) |
| `red_hook_grain_terminal` | Red Hook Grain Terminal | 3008877 | 1922 | Built 1922 (opened 1 September). (the built file had 1922 from assessor) |
| `domino_refinery_building` | Domino Sugar Refinery (filter, pan and finishing house) | 3335796 | 1883 | Rebuilt 1882-1883 (complete by July 1883). (the built file had 1885 from assessor) |
| `east_river_station_building` | East River Generating Station | 1022553 | 1926 | Began operating 23 November 1926. (the built file had 1965 from neighbours) |

Map years (`site_map:<site>:<BIN>`): rikers_island_jails 8, bronx_state_hospital 8, bronx_municipal_hospital 3, poletti_power_project 3, willowbrook_state_school 2, fresh_kills_landfill 2, hunts_point_produce_market 2.

## Structures that are gone

| id | name | years | shape | height m | note |
|---|---|---|---|---|---|
| `fort_lafayette` | Fort Lafayette (Fort Diamond) | 1822-1960 | outline | 14 | Square casemated island fort (about 61 m a side, open parade), traced on the USGS The Narrows 1:24,000 sheet of 1955 (photographs 1954), +-10 m; begun 1812, completed 1822, demolished 1960; height estimated (three tiers). |
| `fort_gansevoort` | Fort Gansevoort (White Fort) | 1812-1854 | 60x35 m, 28.0 deg | 6 | In use 1812-1849, demolished 1854 (the article's coordinates); size, shape, height and material estimated. |
| `fort_washington_1776` | Fort Washington (Fort Knyphausen) | 1776-1783 | 110x80 m, 20.0 deg | 3 | Pentagonal earthwork of 1776 on the site of Bennett Park (West 183rd-185th Street, Fort Washington Avenue); taken 16 November 1776; end year estimated (the British evacuation); outline and height estimated. |
| `fort_tryon_1776` | Fort Tryon (Forest Hill redoubt) | 1776-1783 | 50x35 m, 20.0 deg | 3 | Outwork of Fort Washington (16 November 1776), named Fort Tryon by the British; end year, position within the park, outline and height estimated. |
| `fort_putnam_1776` | Fort Putnam (Fort Greene) | 1776-1847 | 80x60 m, 0.0 deg | 3 | Earthwork fort on the hill of today's Fort Greene Park, built under Nathanael Greene (the year 1776 is from the Fort Defiance article's account of Greene's forts, not stated in this one), refortified in the War of 1812 as Fort Greene; the hill became Washington Park in 1847 (end year = the park); outline and height estimated. |
| `fort_defiance_1776` | Fort Defiance (Red Hook) | 1776-1783 | 70x50 m, 30.0 deg | 3 | Redoubt of 1776 at today's Conover and Van Dyke Streets; end year (the British evacuation), outline and height estimated. |
| `cobble_hill_fort_1776` | Cobble Hill Fort (Corkscrew Fort; Fort Swift in 1812) | 1776-1783 | 40x40 m, 0.0 deg | 3 | Fort on the conical hill at Atlantic Avenue, Pacific and Court Streets; the British cut off its top during the occupation (end year estimated); refortified as Fort Swift in the War of 1812; outline and height estimated. |
| `elmhurst_gas_holder_north` | Elmhurst gas tank (north holder, Newtown Holder Station) | 1910-1996 | outline | 61 | Holder 200 ft tall (cited); circle of 84 m read on the USGS Brooklyn 1:24,000 sheet of 1956, +-10 m; the pair was built between 1910 and 1921 - which holder came first is estimated; dismantling began 1996. |
| `elmhurst_gas_holder_south` | Elmhurst gas tank (south holder, Newtown Holder Station) | 1921-1996 | outline | 61 | Holder 200 ft tall (cited); circle of 84 m read on the USGS Brooklyn 1:24,000 sheet of 1956, +-10 m; start year estimated (the pair was built between 1910 and 1921); dismantling began 1996. |
| `gashouse_district_holder_1` | Gas holder, Gas House District (Consolidated Gas) | 1890-1945 | outline | 30 | Holder symbol read on the USGS Brooklyn 1:24,000 sheet of 1947 (photographs 1940), +-15 m and generalised; start year estimated (the district's tanks date from 1842 on and were many 'by the late 19th century'), end year estimated (clearance for Stuyvesant Town, 1945); height estimated. |
| `gashouse_district_holder_2` | Gas holder, Gas House District (Consolidated Gas) | 1890-1945 | outline | 30 | Holder symbol read on the USGS Brooklyn 1:24,000 sheet of 1947 (photographs 1940), +-15 m and generalised; start year estimated (the district's tanks date from 1842 on and were many 'by the late 19th century'), end year estimated (clearance for Stuyvesant Town, 1945); height estimated. |
| `gashouse_district_holder_3` | Gas holder, Gas House District (Consolidated Gas) | 1890-1945 | outline | 30 | Holder symbol read on the USGS Brooklyn 1:24,000 sheet of 1947 (photographs 1940), +-15 m and generalised; start year estimated (the district's tanks date from 1842 on and were many 'by the late 19th century'), end year estimated (clearance for Stuyvesant Town, 1945); height estimated. |
| `gashouse_district_holder_4` | Gas holder, Gas House District (Consolidated Gas) | 1890-1945 | outline | 30 | Holder symbol read on the USGS Brooklyn 1:24,000 sheet of 1947 (photographs 1940), +-15 m and generalised; start year estimated (the district's tanks date from 1842 on and were many 'by the late 19th century'), end year estimated (clearance for Stuyvesant Town, 1945); height estimated. |
| `gashouse_district_holder_5` | Gas holder, Gas House District (Consolidated Gas) | 1890-1945 | outline | 30 | Holder symbol read on the USGS Brooklyn 1:24,000 sheet of 1947 (photographs 1940), +-15 m and generalised; start year estimated (the district's tanks date from 1842 on and were many 'by the late 19th century'), end year estimated (clearance for Stuyvesant Town, 1945); height estimated. |
| `goldwater_memorial_hospital` | Goldwater Memorial Hospital (Welfare Hospital for Chronic Diseases) | 1939-2014 | outline | 20 | Opened July 1939, closed 2013 (demolition year 2014 estimated); hull of the chevron pavilions traced on the USGS Central Park 1:24,000 sheet of 1966, +-10 m; height estimated. |
| `city_hospital_roosevelt_island` | City Hospital (Charity Hospital) | 1861-1994 | outline | 18 | Renwick's hospital completed 1861, closed 1957, demolished 1994; outline traced on the USGS Central Park 1:24,000 sheet of 1966, +-10 m; height estimated. |
| `blackwells_island_penitentiary` | Blackwell's Island Penitentiary | 1830-1936 | 180x18 m, -60.0 deg | 15 | Opened 3 August 1830; the inmates left and the jail was demolished by 1936, Goldwater hospital taking the ground; position, footprint and height estimated. |
| `pearl_street_station` | Pearl Street Station (Edison Electric Illuminating Company) | 1882-1895 | 15x30 m, -50.0 deg | 15 | 255-257 Pearl Street on a lot of 50 by 100 ft (cited); generating from 4 September 1882, burned 1890 and rebuilt, decommissioned 1895 (end = that year; the building's demolition was not researched); orientation, height and material estimated. |
| `waterside_station_buildings` | Waterside Generating Station (Nos. 1 and 2) | 1901-2007 | outline | 40 | No. 1 (38th-39th Street) October 1901, No. 2 (39th-40th Street) November 1906; decommissioned 2005 (demolition year estimated); outline: the two street blocks; height estimated. |
| `st_johns_park_freight_depot` | St. John's Park Freight Depot (Hudson River Railroad) | 1868-1927 | 130x125 m, 28.0 deg | 15 | Four-acre depot on the former park: construction began 1867 (start 1868 estimated: the opening), demolished 1927; footprint from the 4 acres, storeys and height estimated. |
| `havemeyers_elder_refinery_1856` | Havemeyers & Elder sugar refinery (first) | 1856-1882 | 100x60 m, 28.0 deg | 25 | First Williamsburg refinery of 1856, replaced by the complex built 1882-83 on the west side of Kent Avenue between South 2nd and South 6th Streets; footprint, height and material estimated. |
| `admirals_row` | Admiral's Row (ten officers' houses, Brooklyn Navy Yard) | 1864-2016 | 220x25 m, 8.0 deg | 12 | Ten houses built between 1864 and 1901, demolished 2016 but for one; the footprint is the row along Flushing Avenue: position, extent, storeys and height estimated. |
| `steeplechase_pavilion_of_fun` | Pavilion of Fun (Steeplechase Park) | 1908-1966 | 137x85 m, 0.0 deg | 20 | Steel-and-glass hall of 450 by 280 ft (cited), opened in the 1908 season, demolished September 1966; position inside the park, orientation and height estimated. |
| `dreamland_tower` | Dreamland tower (Beacon Tower) | 1904-1911 | 15x15 m, 0.0 deg | 114 | Tower 375 ft high (cited; some sources 370 ft), opened 15 May 1904, burned 27 May 1911; position (the article's coordinates of the park), footprint and material estimated. |

Not duplicated: the lost landmarks already modelled in `viewer/src/landmarks/nyc-lost.ts` (none of the above is among them; Castle Williams, Battery Weed, Fort Tompkins and the Fort Hamilton casemate fort are civic models).

## Not done

* **No citable year found in the budget, so left out:** the Maspeth holders and the Brooklyn Union works in Greenpoint, the Astoria, Hunts Point, Citizens (Gowanus) and Coney Island gas works; Hudson Avenue, Hell Gate, Sherman Creek, Kent Avenue, Arthur Kill and Astoria generating stations (the outlines of four of them are in OpenStreetMap); Oak Point, Fresh Pond, Mott Haven, Highbridge, Arlington, St. George, Long Island City, Vanderbilt, Westchester, Lenox, Jerome, 240th Street and 36th-38th Street yards; the Harlem River yard before 1991; Jay Street Connecting and New York Dock terminals; Port Mobil; Webb's and the other East River shipyards, Novelty and Delamater iron works; S.S. White, Atlantic Terra Cotta, the breweries, National Sugar; Wallabout Market (dated 1884-1941, no outline); the Brooklyn Terminal Market; St. Albans Naval Hospital; the Staten Island and the lost 71st Regiment armories; Great Kills and Soundview fills; Fort Stirling, Fort Number Eight, Fort Independence, Fort George, the North Battery.
* **Not researched:** navy-yard ship houses, grain elevators, coal trestles and float bridges, brewhouses; Rikers Island's jails by name (the article has no opening years: 8 are bracketed, 193 keep the lot's 1933); the pavilions of North Brother, Randall's, Wards and Hart islands; Bush Terminal's lofts one by one (warehouses 1892-1910, lofts 1905-1925).
* **Outlines** of 30-odd sites are circles or rings around a cited location, and site outlines do not grow (the Navy Yard's stages, Fresh Kills' mounds): one outline per name period.
* Nothing was looked at in the viewer.

## Sources and licences

* Wikipedia (en), CC BY-SA 4.0 - facts and coordinates; one article per row in `source_url`; text cache `data/raw/sites/wp/` (titles in `tools/wp_titles.txt`).
* OpenStreetMap via Overture Maps 2026-10-21.0 (`region5_land_use`, `base_land`, `base_water`, `building` names, roads), ODbL - outlines and building names.
* NYC Landmarks Preservation Commission historic districts, NYC Parks properties, NYC building footprints (NYC Open Data, public).
* USGS Historical Topographic Map Collection, public domain - 1:24,000 and 1:62,500 quadrangles read through the TNM Access API listing (`data/raw/natural/usgs/tnm_all.json`) and `https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/`.

