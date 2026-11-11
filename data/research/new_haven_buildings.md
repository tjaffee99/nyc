# New Haven: real construction years (towns round, 2026-11-11)

Hand-over table: `data/tables/known_building_dates.new_haven.csv` (3,718 rows, one per footprint,
all unique ids, every point verified inside its footprint with shapely `contains` against
`ct_south_central_connecticut.parquet`, `muni = 'New Haven'`: 3,718 of 3,718). 2,008 notes start
`exact:`, 1,710 say `estimate`. Scripts: `data/research/new_haven_build/` (`build.py` rebuilds the CSV).

## Method
Targets: 911 footprints with a name or over 1,500 m^2 (616 named); 296 of them have a placeholder
or missing assessor year and are not among the 35 footprints already in `known_building_dates.ct.csv`
(those are skipped). Sources, cheapest first:
1. Wikidata SPARQL (box query, 161 items with inception/opening) and `wbgetentities` for the 134 QIDs
   tagged on OpenStreetMap buildings in the core box (OSM map API, 20 tiles of 0.015 degrees;
   only 26 ways carry `start_date`, 3 of them useful here).
2. Wikipedia wikitext (opened: Old Campus, Science Hill, Davenport, Pierson, Silliman, Berkeley,
   Jonathan Edwards, Grace Hopper, Trumbull, Pauli Murray, Osborn Labs, Kline Tower, Hall of Graduate
   Studies, City Hall, ...). The API rate-limited the shared egress heavily (HTTP 429); about half of the
   planned pages never arrived (Schwarzman Center, Divinity quad, Peabody, Union Station extras, City Hall
   tables, Hillhouse Avenue, Shubert text, library).
3. ConnCRIS (CT State Historic Preservation Office) public feature service, see task B: found late and
   became the main source.

Rows: 17 from Wikipedia/Wikidata/OSM (Davenport 1933, Pierson 1933, Berkeley and Berkeley North 1934,
Sloane Physics 1912, Osborn 1913, Sage Hall 1924, Sterling Chemistry Lab 1923 on the footprint named
"Sterling Hall", Kline Tower 1966, Bass Center 1993, Environmental Science Center 2005, Chemistry Research
Building 2005, Kroon Hall 2008, Connecticut Financial Center 1990, Hotel Marcel 1970, Wright Lab 1966
estimate, Electron Accelerator Lab 1953 estimate) and 3,701 from ConnCRIS (ids `new_haven_cc<UNIQUE_ID>`).
ConnCRIS rows: only where the assessor year is a placeholder or missing, the footprint holds ConnCRIS point(s)
whose dates agree within 3 years, and the point is a named resource or the footprint is named/large. "CIRCA"
and round-decade years are `estimate`. Hand-rejected (name mismatch, several buildings on one footprint,
implausible date): Christ Church (1995 CIRCA), Kroon Hall/Environmental Science Center (points belong to
Osborn and Peabody), Celentano, Founders Hall, Silliman (whole college, Byers Hall 1903), New Haven Clock Co.
(1817 CIRCA), The Winston (32 points), 12 more. The ConnCRIS rows can be filtered by the id prefix `new_haven_cc`.

## Existing rows believed wrong
- `ct_ce058d9d` Yale Repertory Theatre 1846: ConnCRIS (CALVARY BAPTIST CHURCH/YALE REPERTORY THEATER) says
  1871. 1846 is a Wikidata inception for the company/building entry, not the church.
- `ct_c61ce595` Lanman-Wright Hall 1912 against assessor 1871 and `ct_3a982f89` McClellan Hall 1925 against
  assessor 1890: not checked, but Old Campus table dates should be reread (Lanman-Wright was a 1871 Sturgis
  dorm in the assessor, 1912 may be a later building of the name).

## Not dated (largest footprints left, 193 of the 296 targets)
Unnamed state/municipal buildings (12,104 and 9,509 m^2, state administration/ACC land), a municipal school
7,994 m^2 (1950 heap), Silliman College 4,947, 101 College Street 4,615, Wintergreen Building 4,569,
Yale Science Building 3,979, Schwarzman Center 3,345 (the 1901 Commons, source page not fetched), Central
Power Plant 3,069, Dixwell Community House 3,049.

## Task B: bulk evidence for the ordinary buildings
1. **ConnCRIS (SHPO), yes.** ArcGIS feature service
   `https://services3.arcgis.com/3FL1kr7L4LvwA2Kb/arcgis/rest/services/CT_Public_Above_Ground_Resources/FeatureServer/1`
   (owner `kevin.berger_ctshpo`, public, no login, maxRecordCount 2000, plain `query` with `resultOffset`).
   Points. Fields: `NAME, STNUM, ST_NAME, MUNICIP2, DesigStatu, ConstructD` (text: "1912", "1910 CIRCA",
   "LATE 19 CENTURY"), `Periods, Primary_St, Type, District_Names, NR, SR, Local`. Statewide 104,757 points;
   New Haven (`MUNICIP2='New Haven'`) 12,260, 12,096 with geometry, 10,970 with `ConstructD`. 10,391 of
   them fall inside a New Haven footprint (9,776 distinct footprints, 9,152 point-footprint pairs with a
   parseable year, 4,382 of the dated points are "CIRCA", 384 "LATE 19 CENTURY"). For footprints whose
   assessor year is a heap or missing, 6,545 carry a consistent ConnCRIS date (3,198 non-circa).
   Against non-heap assessor years the two agree within 2 years only 65 %, within 5 years 74 %: ConnCRIS is
   itself rounded (1920 appears 274 times) and some points sit on the wrong building, so treat it as
   better than a heap year but not as ground truth. **Licence: CC BY-NC-ND** (item metadata): attribution,
   non-commercial, no derivatives; this needs a decision before publishing derived years. Item page
   `https://www.arcgis.com/home/item.html?id=ad26b781d4dd467bbe28e9b8f8d3d910`.
   Companion polygons: `Public_Historic_Districts` layers 0-3 (NHL, NR, State, Local district; field `Year`).
   Neighbouring towns can be pulled the same way (`where MUNICIP2='Hamden'` etc.).
2. **City of New Haven open data.** Checked on ArcGIS Online: `New_Haven_3D_Buildings` (36,820 multipatches;
   fields BLDGHEIGHT, EAVEHEIGHT, ROOFFORM: heights, no dates), Yale maps' `NewHaven_Buildings` (32,995
   polygons, no attributes), `New_Haven_Local/State/National_Register_Historic_Districts`, and
   `New_Haven_Historical_Mills` (171 points, `earliest_known_date` is a business date, not a building date).
   The city's parcel view service returned 404. No per-building year layer found.
3. **Other.** The statewide `Connecticut_CAMA_and_Parcel_Layer` (services3, owner ctgisoffice) is the assessor
   year the pipeline already uses. Nothing else found with a year per building.
