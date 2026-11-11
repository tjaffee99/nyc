# Sources

Every dataset the map is built from: where it comes from, its licence, and what it is used
for. Short ids (in `code`) are the values of the `source` fields. Researched tables under
`data/tables/` and `data/manual/` carry a source URL on every row; their READMEs list the
references in full.

## Buildings

| id | What | From | Licence | Used for |
|---|---|---|---|---|
| `nyc_footprints` | Building Footprints (1.08 M outlines; BIN, construction year, measured roof height, ground elevation; photogrammetric, ± 2 ft) | NYC Office of Technology and Innovation, NYC Open Data `5zhs-2jue` — https://data.cityofnewyork.us/d/5zhs-2jue ; metadata https://github.com/CityOfNewYork/nyc-geo-metadata/blob/master/Metadata/Metadata_BuildingFootprints.md | NYC Open Data terms of use (public, no restriction on reuse) | Every building standing today: outline, height, recorded year |
| `pluto` | PLUTO tax lots (year built, floors, building class, attachment) | NYC Department of City Planning, NYC Open Data `64uk-42ks` — https://data.cityofnewyork.us/d/64uk-42ks | NYC Open Data terms of use | Year where the footprint has none; use, storeys, facade material rules |
| `lpc` | Individual Landmark and Historic District Building Database (38,105 buildings: construction date range, primary material, style, architect) | NYC Landmarks Preservation Commission, NYC Open Data `gpmc-yuvp` — https://data.cityofnewyork.us/d/gpmc-yuvp | NYC Open Data terms of use | Construction years (above the assessor's) and wall materials of landmark and historic-district buildings |
| `osm_parts` | OpenStreetMap 3D building parts (set-backs, towers, crowns) | Overture Maps buildings theme, release 2026-10-21.0 — https://overturemaps.org | ODbL (© OpenStreetMap contributors) | Stepped massing of towers where it agrees with the measured roof height |
| `ohm` | OpenHistoricalMap buildings in the map box (documented lost buildings; volunteers' tracings of the Castello Plan 1660, the 1728 survey, Grim 1742, Maerschalck 1755, Dripps 1852, Sanborn and Bromley sheets; NYPL's 1854 footprints of Manhattan to 42nd St) | https://www.openhistoricalmap.org via https://overpass-api.openhistoricalmap.org/api/interpreter, fetched 2026-11-10; `data/manual/ohm/README.md` | CC0 1.0 | What stood before today's buildings; OHM's dates are used only where they are specific to the building |
| `nypl_building_inspector` | Building Inspector: footprints read from the Perris fire-insurance atlases (Manhattan 1857, Brooklyn 1855) and later atlases (1890, 1894) | NYPL Labs / NYC Space/Time Directory — http://spacetime.nypl.org ; https://github.com/nypl-spacetime | CC0 (NYPL public-domain data) | What stood before today's buildings |

The built building files mix OpenStreetMap parts with city data and are offered under ODbL.

### How a building gets its year

1. A researched row (`data/tables/known_building_dates.csv`).
2. The LPC building database (`exact` when the range is two years or less and not "circa").
3. The year on the footprint / tax lot, **if it is not a heap**. Four fifths of the city's
   recorded years sit on 1899, 1900, 1901, 1910, 1915, 1920, 1925, 1930, 1931, 1935, 1940 …:
   the assessor's estimates. A heap year is detected per borough and treated as a range
   ("by 1900", "about 1920"), refined by the recorded years around it, and marked `estimated`.
4. Neighbours of a comparable size.

## Terrain, land and water

| id | What | From | Licence | Used for |
|---|---|---|---|---|
| `3dep` | 1/3 arc-second DEM | US Geological Survey 3D Elevation Program — https://www.usgs.gov/3d-elevation-program | Public domain | Ground elevation |
| `worldcover` | WorldCover 2021 v200, 10 m land cover | European Space Agency — https://esa-worldcover.org | CC BY 4.0 (© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data) | Today's tree canopy, grass, wetland, built-up ground |
| `osm_land` | Land and water polygons (coastline, rivers, lakes), land use (parks, cemeteries, pitches) | OpenStreetMap via Overture Maps base theme, release 2026-10-21.0 | ODbL (© OpenStreetMap contributors) | Today's shoreline and inland water, green outlines |
| `tiger` | County outlines 2024 | US Census Bureau TIGER/Line — https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html | Public domain | The map's extent, borough outlines |
| `nyc_parks` | Parks Properties (outlines, acquisition dates) | NYC Department of Parks and Recreation, NYC Open Data `enfh-gkve` — https://data.cityofnewyork.us/d/enfh-gkve | NYC Open Data terms of use | When each park became a park |

| `ssurgo` | Soil survey of the five counties (NY005, NY047, NY061, NY081, NY085): fill over tidal marsh / reclaimed land | USDA NRCS SSURGO, Web Soil Survey — https://websoilsurvey.nrcs.usda.gov | Public domain | The 1609 marsh and shore outside Manhattan |
| `viele1865` | Egbert Viele, *Sanitary & Topographical Map of the City and Island of New York* (1865): original shore, marsh, ponds, watercourses | Library of Congress, Geography and Map Division — https://www.loc.gov/item/2006629795/ | Public domain | Manhattan's 1609 shore, marshes and streams (georeferenced here, residual ~10 m) |
| `usgs_htmc` | Historical Topographic Map Collection: Harlem 1891 / 1897, Brooklyn 1897, Staten Island 1898, Hempstead 1897, Oyster Bay 1897, Flushing 1947 / 1966, The Narrows 1955 | US Geological Survey — https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/ | Public domain | Shore and marsh before the 20th-century fills; streams; built-up extents of 1889 and 1897; vanished airfields |
| `nypl_maps` | Castello Plan (1660), Grim (1742-44), Ratzer (1766-67), Taylor-Roberts (1797), Dripps (1852, 1867) with the Map Warper's control points | NYPL Digital Collections; NYC Space/Time Directory dump https://s3.amazonaws.com/spacetime-nypl-org/datasets/mapwarper/mapwarper.objects.ndjson | Public domain scans; CC0 control points | Built-up extent snapshots (`data/manual/extents/`) |
| `loc_colton_1836` | Colton, *Topographical Map of the City and County of New-York* (1836) | Library of Congress — https://www.loc.gov/item/2007627512/ | Public domain | Built-up extent of 1836 (Manhattan, Brooklyn, Williamsburgh) |

The natural landscape of 1609 (`data/manual/natural/`), the dated made-land zones
(`data/manual/fill_zones.csv`) and the built-up extents (`data/manual/extents/`) are researched
layers; each has a README with its own sources.

## Transit, streets

| id | What | From | Licence | Used for |
|---|---|---|---|---|
| `osm_rail`, `osm_roads` | Rail and road segments | OpenStreetMap via Overture Maps transportation theme, release 2026-10-21.0 | ODbL | Tracks, streets, bridges |
| `ohm_roads` | Vanished roads with dates (the Bloomingdale Road's old line, lanes on the Central Park site, Brooklyn's town roads, the West Side Elevated Highway) | OpenHistoricalMap | CC0 | Researched routes (`data/manual/routes.csv`); OHM's years are often placeholders and are flagged |
| `highway_dates` | Opening years of highways, parkways and bridge approaches, section by section | Wikipedia articles, nycroads.com (URL per row in `data/manual/routes.csv`, `data/tables/street_dates.csv`) | Facts | Dating today's highway geometry; streets opened at a documented date |
| `mta_gtfs` | Subway GTFS (stations, shapes) | Metropolitan Transportation Authority — https://www.mta.info/developers | MTA developer terms | Stations and service lines |

| `mta_stations` | Subway Stations table | MTA Open Data, data.ny.gov `39hk-dx4f` | MTA / New York State open data terms | Station identifiers and structure |
| `wikidata` | Opening dates of stations | Wikidata — https://www.wikidata.org | CC0 | Cross-check of station dates |
| `ohm_rail` | Dated railway ways (subway segments, the demolished elevated lines) | OpenHistoricalMap | CC0 | Geometry of the Ninth, Sixth, Third and Second Avenue and Brooklyn elevated lines; cross-check of opening dates |

Opening and closing dates of lines and stations: `data/tables/transit_*.csv`, each row with its
source (the Wikipedia station and line articles first, checked against Wikidata and
OpenHistoricalMap). Demolished elevated lines and closed railroads: `data/manual/transit/`
(README there). Where no traced line exists an elevated route follows the centre line of the
street it ran above.

## Tables and research

A source URL on every row. Readmes: `data/tables/places_README.md`, `data/manual/fill_README.md`,
`data/manual/ohm/README.md`; landmark dimensions per model in `data/research/landmarks_*.md`.

| What | From | Licence |
|---|---|---|
| Population 1790–1990 by county (present borough areas) | US Census Bureau, Forstall 1996, *Population of States and Counties of the United States: 1790 to 1990* | Public domain |
| Colonial censuses 1698–1786 by county | US Census Bureau 1909, *A Century of Population Growth*, tables 88–99 — https://archive.org/details/centuryofpopulat00unit | Public domain |
| Population 1900–2010 by borough | NYC Department of City Planning, "Total Population New York City & Boroughs 1900 to 2010" | City publication |
| 2020 counts, Vintage 2025 estimates | US Census Bureau | Public domain |
| Early counts and estimates (New Amsterdam, the occupation) | Museum of the City of New York, New Netherland Institute, Wikipedia articles (URL per row) | Facts only |
| Events, eras, place names, park openings | English Wikipedia articles (URL per row) | CC BY-SA 4.0 (facts and coordinates) |
| Made-land dates (`data/manual/fill_zones.csv`) | Wikipedia articles; Battery Park City Authority Phase 1A archaeological study; East Side Coastal Resiliency FEIS ch. 5.4 (URL per row); ring coordinates from OpenStreetMap street lines via Overture | Facts; ODbL for the geometry |
| Landmark dimensions | Wikipedia articles, NIST NCSTAR 1 (World Trade Center), Carstensen & Gildemeister *New York Crystal Palace* (1854), LPC designation data, OpenHistoricalMap outlines (CC0), OpenStreetMap parts (ODbL) — per model in `data/research/landmarks_*.md` | Facts; CC0 / ODbL for outlines |
| Skyscraper heights and years | CTBUH Skyscraper Center — https://www.skyscrapercenter.com/city/new-york-city ; LPC designation reports https://s-media.nyc.gov/agencies/lpc/lp/NNNN.pdf (2000, 0992, 1273, 0219, 1446, 1530, 1936, 2441, 2582, 1625, 1277, 1664, 0079, 2024, 2067, 0971, 2100) | Facts |
| Bridge dimensions, tower and pier positions | Wikipedia bridge articles; NYC DOT bridge fact pages; OpenStreetMap `bridge:support` outlines (ODbL) | Facts; ODbL |
| Storeys by era (generated and traced buildings) | LPC *Rowhouse Manual* — https://www.nyc.gov/assets/lpc/downloads/pdf/pubs/rowhouse.pdf ; `data/manual/extents/README.md` | Facts |
| Golf course, airport and park-name years | Wikipedia articles, nysga.org, sichamber.com, baysidehistorical.org, airfields-freeman.com (URL per row in `data/tables/golf_courses.csv`, `airports.csv`, `park_names.csv`) | Facts |


## Added in the second round (2026-11)

| id | What | From | Licence | Used for |
|---|---|---|---|---|
| `aerial_1924`, `aerial_1951` | Aerial mosaics of the city, 1924 and 1951 | NYC OTI (1924 from the Department of City Planning, 1951 from the Municipal Archives), ArcGIS tile layers `Ortho_1924_Mosaic` and `NYC_Orthos_1951` (items `afbb5db6b3fd494384357923e6c72622`, `bca6c3f866f844b490925cc9c26d2e40`) | © City of New York, CC BY 4.0 per finder.nyc.gov/nyc-lib/tiles; tiles are not redistributed | `data/manual/aerial/presence.parquet`: was a building on each footprint's outline in 1924 / 1951 |
| `oti_building_historic` | Retired building footprints (demolitions 1996-2026) | NYC OTI building footprints, historic layer — NYC Open Data | NYC Open Data terms of use | Buildings removed since the 1990s (`data/manual/demolished`) |
| `dob_jobs`, `nycha`, `ll84`, `dof_roll`, `hpd_buildings` | New-building jobs and certificates of occupancy; housing authority developments; energy benchmarking filings (owner-reported year); the assessment roll's estimate flag; the housing department's building file with the tenement class (`kj4p-ruqc`) | NYC Department of Buildings, NYCHA, Mayor's Office of Climate, Department of Finance, HPD — NYC Open Data (URL per row; `data/research/building_records.md`) | NYC Open Data terms of use | Recorded years, bounds on estimated years (`data/tables/known_building_dates.records.csv`, `data/manual/records`) |
| `usgs_htmc_farmsteads` | USGS sheets at 1:62,500 surveyed 1888-89 and 1897 (Brooklyn, Harlem, Staten Island, Hempstead, Oyster Bay) and 26 sheets at 1:24,000 of 1947-57 | USGS Historical Topographic Map Collection (GeoPDF); NADCON grid from cdn.proj.org | Public domain; open | Building marks outside the built-up city (`data/manual/farmsteads`), piers (`data/manual/piers`), sites |
| `atlas_traced` | Atlas sheets traced for this map: Harlem 1897, the 23rd ward of the Bronx 1887, the towns of Kings County 1890 | NYPL Digital Collections with the Map Warper's control points (sheet list in `data/manual/atlas`) | Public domain scans; CC0 control points | What stood before today's buildings in those districts |
| `bolton1922`, `bolton1920`, `parker1922`, `danckaerts1679`, `stokes_manatus` | R. P. Bolton, *Indian Paths in the Great Metropolis* (1922) and *New York City in Indian Possession* (1920); A. C. Parker, *The Archeological History of New York* (1922); Jasper Danckaerts' journal (1679-80); I. N. P. Stokes, *Iconography of Manhattan Island* vol. 2 (the Manatus map of 1639) | archive.org (URL per row in `data/tables/early_nyc.csv`; notes in `data/research/early_nyc.md`) | Public domain | Lenape settlements and the colony's outlying farms, mills and villages |
| `tree_inventory` | Forestry tree points and planting spaces (`hn5i-inap`, `82zj-84is`); growth equations: McPherson, van Doorn & Peper 2016, Urban Tree Database (RDS-2016-0005) | NYC Parks — NYC Open Data; USDA Forest Service | NYC Open Data terms of use; public domain | Street and park trees with planting years (`data/research/street_trees.md`) |
| `nj_modiv` | MOD-IV tax list and parcels of Hudson, Bergen, Essex, Union and Passaic counties | New Jersey Office of GIS / Division of Taxation (URLs in `pipeline/counties_nj.py`) | Public | Construction years of the New Jersey counties' buildings |
| `nys_parcels_2025`, `nys_bf`, `cris`, `nys_civil` | NYS Tax Parcels Public (2025 rolls: year built), the state's building footprints, the historic-resource inventory, civil boundaries | New York State GIS (URLs and dates in `data/research/counties_ny.md`) | "Available to the public", as-is | Construction years in Rockland and the dated municipalities of Westchester |
| `overture_region` | Every Overture footprint, land, water, land use, roads, rail of the wider box | Overture Maps release 2026-10-21.0 (OpenStreetMap, Microsoft footprints) | ODbL / CDLA | Footprints, streets, tracks, greens of the counties |
| `ssurgo_counties`, `usgs_counties` | Soil survey of the seven counties; USGS sheets Paterson 1888, Harlem 1891, Staten Island 1898, Tarrytown 1892 | USDA NRCS; USGS | Public domain | The landscape of 1609 in the counties (`data/manual/natural/counties`) |
| `osm_overpass`, `ohm_region`, `wikidata_stations`, `path_gtfs` | Stations, route relations and abandoned railways; dated railway ways; station opening dates; PATH schedule | OpenStreetMap via Overpass (ODbL); OpenHistoricalMap (CC0); Wikidata (CC0); Port Authority GTFS (data.trilliumtransit.com/gtfs/path-nj-us) | as stated | Railroads, PATH and light rail of the counties (`data/manual/transit/README.md`) |
| `airfields_freeman` | Abandoned & Little-Known Airfields | airfields-freeman.com (page URL per row) | Facts only | Vanished airfields of the counties |
| county tables | NJ Department of State 1906, *Compendium of Censuses 1726-1905* (archive.org/details/101270621.nlm.nih.gov); Samuel Smith 1765, *History of the Colony of Nova-Caesaria*; Census Bureau county totals; English Wikipedia articles for places, events, parks, highways, lines and stations (URL per row) | as cited per row | Public domain; CC BY-SA 4.0 (facts) | Population, labels, events, park, highway and railroad dates of the counties |

Made-land dates of the counties: `data/manual/fill_counties_README.md` (a source per zone).
Military and industrial sites: `data/manual/sites/README.md`. Story captions:
`data/tables/story_README.md`.

## Added in the third pass and the sites round (2026-11-10/11)

| id | What | From | Licence | Use |
|---|---|---|---|---|
| `sanborn_brooklyn_188x` | Sanborn-Perris, *Insurance maps of Brooklyn*, volumes 1-9, 1886-88 | NYPL Map Division scans; control points: NYPL Map Warper (NYC Space/Time Directory dump) | Public domain scans; CC0 control points | Brooklyn's built core house by house (`data/manual/atlas/brooklyn_*`) |
| `bromley_bronx_1904`, `bromley_bronx_1921` | G. W. Bromley & Co., atlases of the borough of the Bronx (sections 9-13) | NYPL, as above | Public domain; CC0 | The South Bronx in two later states |
| `hyde_queens_1901`, `hyde_queens_1907`, `bromley_richmond_1917` | E. Belcher Hyde, *Atlas of the borough of Queens* (vols. 1-3); Bromley, *Atlas of the borough of Richmond* | NYPL, as above | Public domain; CC0 | Long Island City, Jamaica, Flushing, Rockaway; Staten Island's north shore |
| `hopkins_jersey_city_1919`, `spielmann_brush_1873`, `brush_hudson_1887` | G. M. Hopkins, *Atlas of Jersey City* vol. 1; Spielmann & Brush, *Insurance maps of Jersey City*; Brush, *Insurance maps of Hudson County* | NYPL, as above | Public domain; CC0 | Jersey City and the Heights (`hudson_*`; the 1887 plate failed the street check and is skipped) |
| `sanborn_hoboken_1891` | Sanborn-Perris, Hoboken 1891, three plates placed by street crossings | Library of Congress Sanborn collection (`loc.gov/collections/sanborn-maps`, IIIF) | Public domain | Hoboken (three plates) |
| `usgs_1940s`, `usgs_1897` | USGS 1:24,000 / 1:25,000 sheets of 1943-47 (Jersey City, Weehawken, Elizabeth, Yonkers, Mount Vernon, White Plains, Nyack, Haverstraw, Mamaroneck …) and the 1897-98 sheets' built-up tint | USGS Historical Topographic Map Collection (`prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo`) | Public domain | Evidence for the generated fill in Hudson County and the old towns of the other counties (`pipeline/gap_fill.py`, `data/manual/gapfill`) |
| `nj_1930` | New Jersey's black-and-white aerial mosaic of 1930 | NJ Office of GIS (`img.nj.gov/imagerywms/BlackWhite1930`) | Public | Looked at for the Hudson County fill (README there) |
| `acs_bg` | American Community Survey 2018-2022, table B25034 (homes by decade built) by block group | US Census Bureau, TIGER/Line with demographic data | Public domain | Modelled years where the roll has none (`counties_ny_estimates.py`) |
| `hisdac_fbuy` | HISDAC-US first built-up year, 250 m cells (Leyk & Uhl 2018, doi:10.7910/DVN/PKJ90M) | Harvard Dataverse | CC0 | Ordering inside a block group in the same model |
| `nrhp_navy_yard` | National Register nomination of the Brooklyn Navy Yard Historic District (2014, NRIS 14000261): building inventory and the yard plans of 1872, 1890 and 1946 reproduced in it | National Park Service (`npgallery.nps.gov`) | Public domain | Dated standing buildings and traced lost buildings of the yard (`data/research/navy_yard.md`) |
| `nps_wadsworth`, `doc_rikers`, `lpc_2040` | Cultural Landscape Report for Fort Wadsworth (2023); the Department of Correction's history of its jails; LPC report on Fort Totten | National Park Service (`npshistory.com`); `correctionhistory.org`; NYC LPC | Public domain; facts only | Dated buildings of the forts and Rikers Island (`data/research/sites_buildings.md`) |
| `haer_bush`, `cdi_maspeth` | HAER NY-201 Bush Terminal; Controlled Demolition Inc. on the Maspeth gas holders | Library of Congress (`tile.loc.gov`); `controlled-demolition.com` | Public domain; facts only | Bush Terminal's lofts, the two holders (`data/research/industry_buildings.md`) |
| `aerial_1924`, `aerial_1951` (second use) | The city's aerial mosaics, as in the second round | NYC (tile services in `pipeline/aerial_presence.py`) | Public | Roofs inside yards, forts and institutions (`pipeline/site_fill.py`): outlines read off the photographs by a program, marked `procedural` |

## Added in the round of 2026-11-11 (outer counties, landmarks, ports, effects)

Sources of the outer counties (the 19 units of `docs/OUTER_ROUND.md`), the second landmark pass, the ports and yards, the effects
and story tables. Everything below was fetched or read on 2026-11-11 unless a row says otherwise. Where a note gives no URL the
row says so; where a note gives no licence the row says "not stated in the note". Per-model citations stay in
`data/research/landmarks_*.md` and in each model's `sources`. Rows that say "see above" reuse a source listed in an earlier
section for a new purpose.

**Building years of the outer counties**

| id | What | From | Licence | Use |
|---|---|---|---|---|
| `nj_modiv_outer` | "Parcels and MOD-IV Composite of NJ": parcels with the tax list's year built, for Hunterdon, Mercer, Middlesex, Monmouth, Morris, Ocean, Somerset and Sussex | NJ Office of GIS — https://services2.arcgis.com/XVOqAjTOJ5P6ngMu/arcgis/rest/services/Parcels_Composite_NJ_WM/FeatureServer/0 (service data last edited 2026-08-18) | "public NJ data" (note); no licence text quoted | Construction years of 1,259,294 footprints in eight counties (`pipeline/counties_nj.py`, `data/research/counties_nj_outer.md`) |
| `overture_outer` | Overture buildings 2026-10-21.0 for the whole outer box (`outer_building.parquet`), also `outer_freeways`, `outer_water` | Overture Maps (OpenStreetMap, Microsoft ML Buildings, Esri Community Maps) — see `overture_region` above | ODbL / CDLA per source_dataset (as `overture_region`) | Footprints of all 19 units; motorway geometry for `routes_outer.csv`; water polygons for the reservoirs; landmark plans |
| `wikidata_outer_buildings` | Wikidata inception / opening years of buildings (SPARQL) and Overture height-source ids | Wikidata; Overture (S3) | CC0 (Wikidata, as stated in the note) | Ran for all eight New Jersey counties (`counties_nj_outer.md`); the note does not say what was kept |
| `nys_parcels_outer` | NYS Tax Parcels Public (2025 rolls, published May 2026) — https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Tax_Parcels_Public/FeatureServer/1 | NY State GIS (see `nys_parcels_2025` above) | State's service text: counties "specifically authorized" sharing; as is | Parcel outlines, `YR_BLT`, class, municipality for Putnam, Sullivan, Ulster, Orange and the dated towns of Suffolk (`data/research/counties_ny_outer.md`) |
| `nys_bf_outer` | NYS Building Footprints (county planimetrics) — https://gisservices.its.ny.gov/arcgis/rest/services/BuildingFootprints/FeatureServer/2 | NY State GIS | "public" (note) | Fill where Overture has no footprint (about half of Ulster's footprints) |
| `nys_civil_outer` | NYS Civil Boundaries (layers 6, 7) — https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Civil_Boundaries/FeatureServer | NY State GIS | "public" (note) | Municipality names for Dutchess and Nassau (no parcels) and pieces of the big counties |
| `shpo_cris_outer` | SHPO CRIS Building USN points — https://services.arcgis.com/1xFZPtKn1wKC6POA/arcgis/rest/services/Building_USN_Points/FeatureServer/2 | NY State Historic Preservation Office | "public" (note) | Names, and a year where the inventory name ends in one (Sullivan 5, Ulster 9, Orange 43, Suffolk 290) |
| `nys_centroids` | NYS Tax Parcel Centroid Points (2025 roll) — https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Tax_Parcel_Centroid_Points/FeatureServer/0 | NY State GIS | "public, same terms as the parcel polygons" (note) | Year built of 110,364 Dutchess lots, whose polygons are not shared: 87.4 % of Dutchess footprints dated (`pipeline/county_years.py`, `data/research/county_years.md`); validated against Orange (96.5 % same year). Nassau's points carry no year; Suffolk's were not downloaded |
| `hisdac_bupr` | HISDAC-US BUPR (built-up property records), 250 m cells, 43 layers 1810-2015 — https://doi.org/10.7910/DVN/YSWMDR (Uhl & Leyk 2020; file `BUPR.tar.gz`, 250 MB, deleted after clipping) | Harvard Dataverse | CC0 (note) | Cell curves of the years built for Nassau (96.7 % of its footprints) and Brookhaven (Suffolk); the building ordered inside a cell by the census model. `estimated`. Median error 11 y where tested on Harrison and Scarsdale (`county_years.md`). Pike's records are empty (0.2 %) so it is not used there |
| `ct_cama` | Connecticut CAMA and Parcel Layer (`AYB` actual year built) — https://services3.arcgis.com/3FL1kr7L4LvwA2Kb/arcgis/rest/services/Connecticut_CAMA_and_Parcel_Layer/FeatureServer/0 (portal item 82a733423a244c43a9d4bf552954cea9; 2025 edition item 45cc26320c634f64a67f1b6c6afbd9d1) | CT Office of Policy and Management / GIS Office, 2026 collection | public data, no restriction stated in the item (note) | Construction years of the 39 towns of Greater Bridgeport, Western Connecticut and South Central Connecticut (`pipeline/counties_ct.py`, `data/research/counties_ct.md`) |
| `acs_bg_pa` | ACS 5-year 2018-2022, B25034, Pennsylvania block groups — https://www2.census.gov/geo/tiger/TIGER_DP/2022ACS/ACS_2022_5YR_BG_42.gdb.zip | US Census Bureau | public domain (note) | Pike County's modelled years: all 38,951 footprints `estimated` (no open year built exists; the county's parcel service needs a token; commercial files were not bought) |
| `acs_bg`, `hisdac_fbuy`, `nys_parcels_2025`, `nj_modiv` (further uses) | see above | see above | see above | The ACS model also dates the Dutchess leftovers and the Nassau / Suffolk footprints outside the cell curves; HISDAC FBUY orders Pike's buildings inside a block group, never dates one; the NJ tax list and NY parcels are the recorded years of the outer counties |
| `tiger_2024_counties` | TIGER 2024 county and county-equivalent outlines (`tl_2024_us_county.zip`) | US Census Bureau | public domain (note) | Clipping footprints and assigning stations to counties and the planning regions of Connecticut |
| `wikipedia_county_series` | English Wikipedia county articles ("<Name> County, New York"), `wiki_pop.json` | Wikipedia — https://en.wikipedia.org | CC BY-SA (facts only) | Pre-1940 growth curve of the modelled years where the repository's table has none |

Commercial year-built files (ReportAll, landrecords.us, Regrid) were looked at and not used: paid licence. No open year exists for
Pike County or for Suffolk's Islip, Huntington, Babylon, East Hampton and Southold (those stay modelled).

**Farmland**

| id | What | From | Licence | Use |
|---|---|---|---|---|
| `census_1850_agriculture` | Federal census 1850, Table XI Agriculture, state volumes (New York, New Jersey, Connecticut, Pennsylvania) — https://www2.census.gov/library/publications/decennial/1850/1850a/1850-census-report-{new-york,new-jersey,connecticut,pennsylvania}.pdf | US Census Bureau (OCR text layer; Suffolk corrected by eye on the scan) | Public domain (government publication of 1850) | Improved acres of 27 units (`data/tables/farmland_counties.csv`, `data/research/farmland.md`); New York, New Jersey and Connecticut columns summed to the printed state totals, Pike not summed |
| `ny_census_1855` | New York state census 1855, "Recapitulation of agricultural statistics" (Hough) — https://archive.org/details/cu31924078305582 | NY Secretary of State, via archive.org | Public domain | Improved acres of the 12 New York counties (60 values sum to 13,657,465 against the printed 13,657,490: OCR dropped half acres) |
| `ny_census_1865` | New York state census 1865, recapitulation — https://archive.org/details/censusofstateofn_1865newy | NY Secretary of State, via archive.org | Public domain | Improved acres; poor OCR: the sum is 1,327 acres short of the state total, one value wrong and not located (use +-1,500 acres) |
| `ny_census_1875` | New York state census 1875, Table 56 recapitulation — https://archive.org/details/censusofstateofn1875newy | NY Secretary of State, via archive.org | Public domain | Improved acres of 11 counties; two values recovered from the printed total (Hamilton, Orange), so Orange 1875 has no independent check |
| `spafford_1824` | H. G. Spafford, *A Gazetteer of the State of New-York* (1824) — https://archive.org/details/gazetteerofstate00spaf_0 | archive.org | Public domain | The 1821 state census's improved acres, 11 counties, read from each county entry: not checked against a table or the scan; the least reliable column |
| `census_gazetteer_2020` | Census 2020 Gazetteer (`ALAND_SQMI` by county) | US Census Bureau | not stated in the note (US government data) | `land_acres`, the denominator of `improved_share` (today's land, so made land is counted as land) |

Not found, so not in the table (`farmland.md`): New York state counts of 1825, 1835 and 1845; New Jersey and Connecticut before 1850;
the federal volumes of 1860, 1880 and 1900 (scans without text); 1925, 1930 and 1950 (crop land, not comparable). Wacker's *Land and
People* and the Harvard Forest land-use data were named as leads and not looked up (no URL in the note).

**Places, population, stations and airports of the outer counties**

| id | What | From | Licence | Use |
|---|---|---|---|---|
| `wiki_county_census` | The `{{US Census population}}` tables of the Wikipedia county articles, 1790-2020 | English Wikipedia (wikitext) — https://en.wikipedia.org | CC BY-SA 4.0 (facts only) | `data/tables/population_outer.csv` (397 rows). Read by script and not checked against the Census Bureau PDFs (the Forstall counts are as the article tabulates them; no present-area correction was made, boundary changes are noted in each county's first row) |
| `cpg_1909` (further use) | *A Century of Population Growth*, tables 88, 97, 98 — see above | Census Bureau 1909, archive.org OCR | Public domain | Eight colonial counts (Suffolk 1698, 1756, 1771; Ulster, Orange 1756 and 1771; Dutchess 1771) read by hand from the OCR, possible OCR errors; the counties of then were larger and are not scaled |
| `gazetteer_2023` | Census 2023 Gazetteer, place and county-subdivision files | US Census Bureau | not stated in the note (no URL in the note) | Check of the typed coordinates of `data/tables/places_outer.csv` (230 rows): 15 moved, 6 unmatched and kept from memory (Garrison, Menlo Park, Peapack-Gladstone, Whitehouse Station, Dingmans Ferry, Greeley) |
| `places_outer_wikipedia` | English Wikipedia article for each town (URL per row of `places_outer.csv`) | Wikipedia | CC BY-SA 4.0 (facts only) | Settlement and incorporation years. Of 230 rows 82 carry a year found in the cited article, 60 are "nominal, not found in the cited article" and 88 are `estimated` (the author's reckoning, kept because a place that existed must not be empty): treat the minor towns' years as approximate. Coordinates were typed from memory |
| `wikidata_stations_outer` | Wikidata SPARQL: railway stations with coordinate, opening P1619, closing P3999, line P81, operator P137 (four boxes: Long Island, Hudson Valley, New Jersey, Connecticut; the Connecticut sitelink pass was rate-limited and not retrieved) | Wikidata — endpoint not named in the note | CC0 (note) | `data/tables/transit_stations_outer.csv`, 302 rows (positions rounded to five decimals) |
| `wikipedia_station_lists` | Wikipedia station tables (Port Jervis, Danbury, Waterbury, New Canaan, Harlem, Hudson and New Haven lines; NJ Transit's North Jersey Coast, Raritan Valley, Morristown, Montclair-Boonton, Gladstone, Northeast Corridor and Princeton Branch; the earlier LIRR and Metro-North lists; the LIRR disused-stations table), via `Special:Export` | English Wikipedia (no URL in the note) | CC BY-SA 4.0 (dates and facts only) | Opening and closing days and years of the stations. Earliest source wins; a year-only source is written `YYYY-07-01` and noted "estimated" (188 of 302 rows carry an estimated item, 29 have no opening and are dated from the nearest track); some New Haven Line openings are the line's year, not the station's |
| `airports_outer_wikipedia` | Wikipedia articles of 29 airfields (Mitchel, Roosevelt, Grumman Bethpage, Calverton, Lakehurst, Stewart and others) | English Wikipedia (URL per row of `data/tables/airports_outer.csv`) | CC BY-SA 4.0 (facts only) | Opening and closing years: 18 rows are marked READ (quoted from the article), 11 are UNVERIFIED / ESTIMATED from general knowledge or a placeholder inside a stated range. `airfields_freeman` (above) was not fetched for these counties |

**Routes and bridges**

| id | What | From | Licence | Use |
|---|---|---|---|---|
| `routes_outer_overture` | Overture transportation segments (`motorway`, `trunk` for named parkways) of the outer box, selected by name and route ref | Overture 2026-10-21.0 (derived from OpenStreetMap) — see `overture_outer` | ODbL (note) | Geometry of `data/manual/routes_outer.csv` (157 lines, 72 sections), cut by latitude or longitude and not at the interchange |
| `routes_outer_wikipedia` | Wikipedia route articles (Turnpike, Garden State Parkway, I-78, I-80, I-84, I-195, I-287, I-684, the Thruway, Taconic, Route 17, the Long Island parkways and Expressway, Merritt / Wilbur Cross, Connecticut Turnpike and others) | English Wikipedia (no URL in the note) | CC BY-SA 4.0 (facts only) | Opening dates of the sections, to the day where the article gives one. 23 lines are marked `estimated:`; I-91 and I-691 in Connecticut are placeholders with no source read |
| `bridges_hudson_osm` | OpenStreetMap ways of the Poughkeepsie Railroad Bridge (24185107) and other bridge lines; Overture bridge-flagged segments for the Tappan Zee, Bear Mountain, Mid-Hudson and Newburgh-Beacon bridges | OpenStreetMap (ODbL) via Overture `outer_freeways.parquet` | ODbL | Bridge lines of the Hudson-valley models (`data/research/landmarks_ny_hudson.md`). The old Tappan Zee line is an estimate (78 m south of the new eastbound roadway) |

**Reservoirs and dams**

| id | What | From | Licence | Use |
|---|---|---|---|---|
| `nid` | National Inventory of Dams, `nid.csv` (69 MB, deleted after use) | US Army Corps of Engineers (no URL in the note: "the URL is the record", not recorded) | not stated in the note | "Year Completed" of the largest dam within 350 m of each water outline: the years of `data/manual/fill_zones_outer.csv` (137 rings, 129 bodies of 40 ha and more). May be a mill dam or a rebuild, not the lake as it is today |
| `reservoir_corrections_wikipedia` | Wikipedia articles for nine corrected bodies (Candlewood Lake 1929, Lake Zoar 1919, Lake Lillinonah 1955, Rondout 1950, Lake Hopatcong 1831, Greenwood Lake 1928, Croton Falls 1911, Ashokan 1915, West Branch 1895, Lake Carnegie 1906) | English Wikipedia (no URL in the note) | CC BY-SA 4.0 (facts only) | Hand corrections of the NID match; Hopatcong 1831 and Greenwood Lake 1928 are `estimated` |

Reservoir outlines are Overture's water polygons (`outer_water.parquet`, ODbL). Bodies without a matching NID dam are absent (Lake
Montauk, Mercer Lake, Assunpink, Squantz, Popolopen, Mombasha, Budd and others); Connecticut bodies outside the three planning regions
are not in the file.

**Ports and rail yards** (`data/research/ports.md`, `data/manual/ports/README.md`)

| id | What | From | Licence | Use |
|---|---|---|---|---|
| `port_wikipedia` | Port Newark-Elizabeth Marine Terminal (first container voyage, Ideal X, 26 April 1956) — https://en.wikipedia.org/wiki/Port_Newark%E2%80%93Elizabeth_Marine_Terminal ; Port of New York and New Jersey (Elizabeth, 1962) — https://en.wikipedia.org/wiki/Port_of_New_York_and_New_Jersey ; Howland Hook Marine Terminal — https://en.wikipedia.org/wiki/Howland_Hook_Marine_Terminal ; Red Hook Container Terminal — https://en.wikipedia.org/wiki/Red_Hook_Container_Terminal ; Port Jersey — https://en.wikipedia.org/wiki/Port_Jersey ; Oak Island Yard (opened 1903) — https://en.wikipedia.org/wiki/Oak_Island_Yard | English Wikipedia | CC BY-SA 4.0 (used only for the years quoted) | First year of container handling and yard openings (`data/manual/ports/terminals.geojson`, `yards.geojson`) |
| `port_estimates` | Opening years not found in a source: Maher 1963, Port Jersey container handling 1977, South Brooklyn Marine Terminal 1972 | the stage's own estimates | n/a | `year_basis` `estimated` in `terminals.geojson`. Howland Hook's idle years 1986-1996 come from the owner's brief (United States Lines' failure in November 1986 is from memory, not checked in a source) |
| `port_outlines` | OpenStreetMap land use ("Port Newark-Elizabeth", "Maher Terminals", "Port Liberty Bayonne", "Port Liberty New York", "Red Hook Container Terminal", "South Brooklyn Marine Terminal"), rail, road and water layers | Overture 2026-10-21.0 `base_land_use` etc. (OpenStreetMap) | ODbL / CDLA | Outlines of the seven terminals and the track of 18 yards; the container blocks and railcars drawn on them are generated (`procedural`, `data/interim/gapfill/gapfill_ports.parquet`) |
| `yards_sites` | 16 rail-yard outlines and years of `data/manual/sites/sites.geojson` (sources in that file) | see `data/manual/sites/README.md` | as there | The subway and LIRR yards |

Not drawn for lack of a year in a source: Croxton Yard / North Jersey Intermodal Terminal (Wikipedia gives none; an AI-written page that
says 1890s was not used), Oak Point, Little Ferry, North Bergen, Kearny / Harrison, Fresh Pond Junction (a mirror site said "early 20th
century"), CSX South Kearny, E-Rail Elizabeth, Global Marine Terminal, River Terminal Development.

**Cleared districts and the counties' USGS built-up layers** (`data/manual/gapfill/README.md`, `numbers_counties.md`)

| id | What | From | Licence | Use |
|---|---|---|---|---|
| `usgs_1940s`, `usgs_1897` (further use) | USGS sheets of 1897-98 (built-up tint) and of the 1940s (block fronts, tint) — see above. Jersey City 1947 (1:24,000) — https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/NJ/NJ_Jersey%20City_254499_1947_24000_geo.tif ; Weehawken 1943 (1:25,000) — https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/NJ/NJ_Weehawken_255029_1943_25000_geo.tif | USGS Historical Topographic Map Collection | Public domain | Ground evidence of the counties' generated fill (`gap_fill.py counties`) and of the cleared blocks: evidence labels `usgs1897_builtup`, `usgs194x_blocks`, `usgs194x_tint`. The 1940s sheets of Elizabeth, Weehawken, Yonkers, Mount Vernon and Central Park were fetched again into `data/raw/gapfill/usgs/` (no URL in the note). Sheets register off by up to 35 m; 66 % of lots under map buildings recorded by 1935 read as built (Jersey City) |
| `cleared_districts` | 14 researched districts (Newark Central Ward, Newark Route 280 and Route 78 corridors, Paterson Route 80 and downtown, Elizabethport, Passaic Eastside, Hackensack centre, Englewood Fourth Ward, East Orange / Orange, Yonkers Getty Square, White Plains downtown, New Rochelle centre, Mount Vernon south side): clearance years and a source URL per district | `data/manual/gapfill/cleared_districts.geojson` (URLs are in the file, not in the notes) | Facts; Wikipedia pages per the file (licence not stated in the note) | Cleared-block rows `cleared_block+<sheet>` (25,165 rows, `procedural`). The clearance years and the district outlines are the stage author's reading of those pages and were **not re-checked online** (`estimated`); the density factors are fitted to the owner's 60-110 % band, not measured |

**Early towns of the counties**

| id | What | From | Licence | Use |
|---|---|---|---|---|
| `smith_1765` (further use) | Samuel Smith, *History of the Colony of Nova-Caesaria* (1765), pp. 159-161 — https://archive.org/details/historyofcolonyo00smit | archive.org | Public domain | Documented counts of 1682: Newark about 100 families, Elizabeth-Town about 150, Bergen about 70. Hempstead 1644 (30-40 families; Wikipedia, Hempstead village, CC BY-SA) is the fourth. 12 rows, 290 dwellings in all |
| `early_counties_memory` | Village populations of 1830 (`P30`) and the founding clusters (3-35 houses) of 161 towns | **recalled from memory of the decennial census and town histories, order of magnitude; not looked up** (Wikipedia answered 429 all through the task and no other source was fetched) | n/a | `data/tables/early_counties.csv` (1,065 rows, 19,001 dwellings by 1840). Every row is `estimated`, low confidence; positions and house placement are generated (`procedural`); the rotation of each street follows today's roads. Barber and Howe (1844), Gordon's *Gazetteer of New Jersey* (1834) and Spafford (1824) are named as the better sources and were not used (no URL in the note for the first two) |

**Effects and story events** (`data/tables/effects.csv`, `data/tables/story.csv`)

| id | What | From | Licence | Use |
|---|---|---|---|---|
| `effects_wikipedia` | The Wikipedia article of each event (`source_url` per row of `effects.csv`; the event list is in `data/research/effects.md`): the Revolution's battles and fires, Kieft's War, the fires of 1835 and 1845, Black Tom, General Slocum, the Hindenburg, 9/11 and others | English Wikipedia | CC BY-SA 4.0 (facts only) | 186 rows. **Dates, hours, routes and places were written from recall of the standard accounts, not from an opened page**: the pages answered HTTP 429 or were not opened (HTTP 200 only confirmed the links, except Paulus Hook, General Slocum, Great Fire of 1835, Henry Hudson, Leisler's Rebellion, New Amsterdam, Peach War). Positions are placed from memory to 50-200 m (`estimated:` in each note); blast, fire and dust radii are order-of-magnitude; aircraft tracks are schematic. Six links were replaced by the town's article (Fairfield, Norwalk, New Haven, Paterson, Hoboken, Bowling Green) |
| `effects_fire_rings` | The 1776 and 1835 fire outlines (`data/manual/extents/fire_*.geojson`) | the project's own, estimated from text | n/a | Low-confidence rings, copied unchanged; the 1845 ring is a hand-drawn estimate |
| `story_tables` | Facts and coordinates from `events.csv`, `events_counties.csv`, `landmarks_*.csv`, `early_nyc.csv`, `population` | the project's own tables (sources as above) | as the tables | `data/tables/story.csv`, 217 stops. Two stops rest on Wikipedia pages opened in 2026-11 (the 1863 draft riots, the 1975 fiscal crisis). The pages for the battles of White Plains, Trenton and Princeton, the Military Academy, the Morris Canal, Branch Brook Park and others were **not opened**: their facts come from the landmark notes, the tables or well-known dates. The event dates should be compared with `effects.csv` |

**Features on roofs and pier decks** (`data/research/features_on_decks.md`)

| id | What | From | Licence | Use |
|---|---|---|---|---|
| `features_decks` | City building footprints (BIN, measured roof heights), pier rows of `nyc_buildings.parquet`, OpenStreetMap land-use features via Overture `base_land_use`, the park labels file | NYC OTI footprints (see above); OpenStreetMap (ODbL) | NYC Open Data terms; ODbL | A count of the sports features whose centroid lies under a standing building or pier deck (261 of 8,499; 36 on pier decks). The note names no external publication. The proposed change to `ground_detail.py` is a patch, not applied. Opening dates it quotes (Pier 5 Dec 2012, Pier 2 May 2014, Riverbank 1993) are from the landmark notes |

**Landmarks of the round** (one row per note; per-model citations in the note and in each model's `sources`)

| id | What | From | Licence | Use |
|---|---|---|---|---|
| `lm_more_a` | High Line, Farley / Moynihan, Brooklyn Tower and the Dime (`data/research/landmarks_more_a.md`, `viewer/src/landmarks/nyc-more-a.ts`) | OpenStreetMap map API tiles and relation 7141751 (the High Line park), way 264667030, parts 1039403183, 248156228, 700241894 (`api.openstreetmap.org/api/0.6/map`; ODbL); Wikipedia High Line, James A. Farley Building, Moynihan Train Hall, 9 DeKalb Avenue (read 2026-11-11; no URLs in the note); city BINs 1084820 and 3000370 | ODbL; CC BY-SA 4.0 (facts) | Plans and heights. Deck level 9 m is the brief's figure (not in Wikipedia); 1961 for the southern demolition, the 1932 viaduct start and the park construction starts are estimated |
| `lm_more_b` | Towers and apartment houses: One57, Time Warner Center, 53 West 53, 35 Hudson Yards, the Plaza, Carnegie Hall, the Dakota, the Ansonia; second round Oculus, Javits, Whitney, Cloisters, TWA, Apollo, San Remo, Belvedere Castle, Queens Museum, Brooklyn Public Library, Bronx courthouse, Kingsbridge Armory (`landmarks_more_b.md`, `nyc-more-b.ts`) | NYC building footprints (BIN per model); levels from OpenStreetMap parts via Overture 2026-10-21.0; Wikipedia articles (linked in each model's `sources`); CTBUH | NYC Open Data terms; ODbL; CC BY-SA 4.0 (facts) | Heights checked against the built mesh. The Ansonia has no independently cited height; the Shed, the Roosevelt Island Tramway and St. George Terminal were not built (no footprint) |
| `lm_more_c` | Riverbank State Park and four pier-deck models (Pier 40, Pier 5, Pier 2) (`landmarks_more_c.md`, `nyc-more-c.ts`) | OpenStreetMap map API (`rb.osm`, `p40.osm`, `bbp.osm`; ODbL); Wikipedia "Riverbank State Park", "Pier 40", "Brooklyn Bridge Park" (raw wikitext); NY State Parks page — https://parks.ny.gov/visit/state-parks/riverbank-state-park-denny-farrell-riverbank-state-park | ODbL; CC BY-SA 4.0 (facts); State Parks page: not stated in the note | Dates (opened 27 May 1993), deck height 21.03 m (State Parks) vs the city's 21.21 m, building heights above the deck (estimated). Other estimated: the 1991.2 start, the 1998 roof-fields window, colours |
| `lm_nj_inner` | 11 New Jersey models: Newark cathedral, Penn Station, National Newark Building, City Hall, CRRNJ terminal, Hoboken Terminal, 30 Hudson, Loew's Jersey, MetLife and Giants stadiums, Union County courthouse (`landmarks_nj_inner.md`, `nj-inner.ts`) | `data/interim/county_buildings.parquet` footprints (Overture / state footprints; ODbL); Wikipedia articles (URL per model; read in the session) | ODbL; CC BY-SA 4.0 (facts) | Plans and cited heights (71, 142, 68.6, 238, 54, 72.54 m); no other source was opened. Wikipedia's 1933 vs 1931 for the National Newark Building conflict (1931.5 used); no heights cited for Penn, City Hall, CRRNJ, Loew's, MetLife |
| `lm_nj_outer` | 21 models in Mercer, Middlesex, Monmouth, Ocean, Morris and Sussex (State House, Old Barracks, Battle Monument, Lower Trenton Bridge, Nassau Hall, Princeton chapel, Rutgers' Old Queens, Ford Mansion, Sandy Hook and Barnegat lights, Twin Lights, Lakehurst Hangar No. 1, Edison Tower, Asbury Park Convention Hall, High Point Monument and others) and a 30-row dates table (`landmarks_nj_outer.md`, `nj-outer.ts`, `known_building_dates.nj_outer.csv`) | Overture 2026-10-21.0 `outer_building.parquet` (ODbL); OpenStreetMap ways 561300664, 427497491, 704069002 and node 367681826 via Nominatim; Wikipedia (read with WebFetch / WebSearch); NRHP nominations only as quoted in search results; Princeton Graduate College history page (Cleveland Tower) | ODbL; CC BY-SA 4.0 (facts); others not stated in the note | Cited: 150 ft, 163 ft, 220 ft, 224 ft and similar heights. Sources conflict and are noted: Asbury Park hall (1928-30 vs infobox "opened 1925"), Hangar No. 1 (966 x 350 x 224 ft vs 961 x 350 x 200 ft vs 960 x 328 x 190), Edison Tower (129 / 131 / 118 ft). Nassau Hall's 1756 size is recalled, not re-read. A web result contained text addressed to an AI and was ignored. Fine Hall's 1970 date and 170 ft are a museum snippet, unverified |
| `lm_ny_hudson` | 23 models in Westchester, Rockland and the Hudson valley: Kykuit, Old Dutch Church, Philipsburg Manor, Lyndhurst, West Point, Bannerman's Castle, Vassar, Springwood, Vanderbilt Mansion, New Croton Dam, Mohonk and eight bridge models; a 28-row dates table (`landmarks_ny_hudson.md`, `ny-hudson.ts`, `known_building_dates.ny_hudson.csv`) | Overture 2026-10-21.0 footprints and `outer_freeways.parquet` (ODbL); OpenStreetMap ways 24185107 (Walkway Over the Hudson) and 1005972999 (others cut off in the note); Wikipedia wikitext of each article read 2026-11-11 (copies in `data/raw/landmarks_ny_hudson/`, gitignored; URLs in each model's `sources`) | ODbL; CC BY-SA 4.0 (facts) | Dates and bridge dimensions (main spans, tower heights, clearances). No NPS, HABS or LPC document was opened. Building heights are mostly estimated (the articles give almost none). The Kensico Dam and Playland were not built |
| `lm_ny_long_island` | 11 buildings in 16 models: Oheka, Sagamore Hill, Montauk and Fire Island lights, Jones Beach water tower, Westbury House, Hempstead House, Castle Gould, Coe Hall, Vanderbilt Eagle's Nest, Nassau Coliseum, the Big Duck (`landmarks_ny_long_island.md`, `ny-long-island.ts`) | Overture 2026-10-21.0 outlines (ODbL; Overture ids in the note); Wikipedia through a summarising fetch, not wikitext; NPS Fire Island page; web-search summaries (oheka.com, Architectural Paper, Sports Illustrated 1968) | ODbL; CC BY-SA 4.0 (facts); NPS: public domain (note) | Heights (168 ft, 188 ft, 80 ft, 110 ft 6 in) "read once, not verified against the primary source". Belmont Park's grandstand (1968, 1,260 x 300 ft, 112 ft) was not built (outline gone from Overture). No URLs in the note |
| `lm_ct` | 14 models in New Haven County and New Canaan: Harkness Tower, Connecticut Hall, three Green churches, Sterling Library, Beinecke, Payne Whitney, Yale Bowl, Union Station, Knights of Columbus tower, Barnum Museum, Glass House, Lockwood-Mathews Mansion; a 35-row dates table (`landmarks_ct.md`, `ct.ts`, `known_building_dates.ct.csv`) | Overture 2026-10-21.0 footprints (ODbL-compatible; Overture id in a comment above each ring); Wikipedia wikitext (cached in `data/raw/landmarks_ct/`; only `index.php?action=raw` worked; URLs in each model's `sources`); "the project brief" for the churches' years | ODbL-compatible; CC BY-SA 4.0 (facts) | Cited: Harkness 66 m, Sterling tower 45.7 m, Trinity walls 38 ft. Wikipedia carries few dimensions, so most heights are estimated and several models are marked LOW. Center and United Church years come from the brief, not a source (the articles were not found). Tower positions rest on rounded Wikipedia coordinates |


## Added in the towns round of 2026-11-11 (Princeton, New Haven, the outer counties' names)

| id | What | From | Licence | Use |
|---|---|---|---|---|
| `overture_divisions` | Overture divisions 2026-10-21.0 (`theme=divisions/type=division`: localities and neighbourhoods with the position of OpenStreetMap's place node), fetched for the map's box | Overture Maps — https://docs.overturemaps.org/guides/divisions/ | ODbL (OpenStreetMap-derived) | Town centres of `places_outer.csv` (122 moved, `data/tables/tools/recentre_places.py`); names and positions of the 3,180 labels of `places_outer_auto.csv` (`pipeline/places_auto.py`); the year a label appears is this map's own estimate |
| `wikipedia_princeton` | Princeton Historic District (table of contributing properties) and the articles on individual buildings of Princeton University, the Seminary and the town | Wikipedia — https://en.wikipedia.org/wiki/Princeton_Historic_District_(Princeton,_New_Jersey) and the URLs in each row | CC BY-SA (facts only) | Years of 83 footprints (`known_building_dates.princeton.csv`); dates and some heights of the models in `princeton.ts` (per model: `data/research/landmarks_princeton.md`) |
| `wikipedia_new_haven` | Articles on Yale's colleges and Science Hill buildings and on New Haven's towers and monuments | Wikipedia — the URLs in each row | CC BY-SA (facts only) | Years of 17 footprints (`known_building_dates.new_haven.csv`); dates and cited heights of the models in `new-haven.ts` (`data/research/landmarks_new_haven.md`) |
| `wikidata_towns` | Wikidata inception dates of buildings in the two towns | Wikidata — https://query.wikidata.org | CC0 | Seven Princeton rows; cross-checks |
| `osm_map_api` | OpenStreetMap map API, small boxes over the two campuses (names, `wikidata` ids, a few `start_date` and `height` tags) | https://api.openstreetmap.org/api/0.6/map | ODbL | Matching names to footprints; almost no years (two `start_date` tags in Princeton) |
| `conncris` (found, **not used**) | CT Public Above Ground Resources: points of Connecticut's historic resources inventory with a construction date (`ConstructD`); 12,260 points in New Haven, 10,970 dated | Connecticut State Historic Preservation Office — https://services3.arcgis.com/3FL1kr7L4LvwA2Kb/arcgis/rest/services/CT_Public_Above_Ground_Resources/FeatureServer/1 | **CC BY-NC-ND** (item metadata) | Not used and not in the repository pending the owner's decision on the licence; would date about 6,500 New Haven footprints whose assessor year is a placeholder (`data/research/new_haven_buildings.md`) |
