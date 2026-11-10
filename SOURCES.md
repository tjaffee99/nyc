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

