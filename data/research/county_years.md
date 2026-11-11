# Real construction years for Nassau, Dutchess, Suffolk and Pike (round of 2026-11-11)

Stage: `pipeline/county_years.py` (`download dutchess`, `apply dutchess`, `hisdac nassau suffolk`, `validate`). Numbers below are from the built files
(`data/interim/county_years/*.json|csv`).

## Result: footprints by year source

| Area | Footprints | Before: recorded / census model | After: recorded | After: HISDAC cell curve | After: census model |
|---|---:|---|---:|---:|---:|
| Dutchess | 133,224 | 0 / 133,224 | **116,503 (87.4 %)** | 0 | 16,721 (12.6 %) |
| Nassau | 530,817 | 0 / 530,817 | 0 | **513,285 (96.7 %)** | 17,532 (3.3 %) |
| Suffolk | 683,514 | 112,432 / 571,082 | 112,432 | **168,302 (24.6 %)** (Brookhaven) | 402,780 (58.9 %) |
| Pike PA | 38,951 | 0 / 38,951 | 0 | 0 | 38,951 (100 %) |

Per municipality: `data/interim/county_years/sources_{dutchess,nassau,suffolk}.csv`. Suffolk by town (recorded / cell / census): Southampton 59,001 / 14 / 2,517;
Riverhead 19,765 / 23 / 3,468; Smithtown 29,172 / 57 / 18,008; Shelter Island 4,486 / 0 / 168; **Brookhaven 0 / 168,154 / 30,580**; Islip 0 / 43 / 124,885;
Huntington 0 / 0 / 89,060; Babylon 0 / 0 / 79,672; East Hampton 0 / 0 / 29,588; Southold 8 / 11 / 24,833. Nassau: 91-99 % cell curves in every municipality
(Hempstead 97.6 %, Oyster Bay 97.1 %, North Hempstead 96.2 %, Long Beach 91.1 %).

## Leads

1. **NYS Tax Parcel Centroid Points** — https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Tax_Parcel_Centroid_Points/FeatureServer/0 (public, same terms as the parcel
   polygons; 2025 roll). **Dutchess: 110,364 points, 93,398 (84.6 %) with `YR_BLT`** — the polygons are not shared for Dutchess but the points are. Taken in full
   (`download dutchess`, 111 pages of 1,000; filters on `YR_BLT` time out on the server, so pages are OBJECTID windows). Nassau: 423,430 points, `YR_BLT` null
   in all (count of non-null = 0). Suffolk: sampled by envelope in Babylon, Islip, Huntington, East Hampton, Southold (all null) and Smithtown (half), Shelter Island (mixed) —
   the same towns as the polygon layer; the county query times out so it was not downloaded. Pike is not in New York's layer.
   Method: each footprint takes the nearest point whose lot radius (0.8 x sqrt(lot area) + 10 m, 25-200 m) reaches it; the largest outline of a point is the main
   building, the rest `secondary` with its year; placeholder years by the Westchester rule (`counties_ny.find_heaps`, per assessing town).
   **Validated** against the polygon join where both exist (Orange, a 19,330-point window, 6,910 buildings dated both ways): 96.5 % same year, 97.5 % within 5 y
   (mains 97.6 % / 98.4 %). A variant preferring the nearest *dated* point gained 0.7 points of coverage but dated 19 % of buildings the roll leaves undated; not used.
   Limits: 16,721 Dutchess footprints (12.6 %) stay without a year (vacant/exempt/commercial parcels with no `YR_BLT`, buildings out of every lot radius);
   the Dutchess footprints have no polygons so a building beside a vacant lot can take a neighbour's year in a few percent of cases (that is the 3.5 % above).
2. **Town / county services** — nothing free found. Nassau: `legacygis.nassaucountyny.gov` (Akanda, IASWorld) has lot geometry, SBL only (earlier note); the Land Records
   Viewer is per parcel behind a captcha — not touched. Suffolk: `gis.suffolkcountyny.gov` returns 404; ArcGIS Online search for the towns' parcel layers with a year gave nothing
   relevant. Dutchess: open-data hub has no parcels (earlier note). Commercial: ReportAll ($200-250, Nassau/Suffolk/Pike), landrecords.us, Regrid — year built, paid licence, not used.
3. **data.ny.gov** — `7vem-aaz7` (assessment rolls): 100+ fields, no year built. Catalog search for property sales with year built: nothing for real property (only IDA/authority datasets).
4. **Pennsylvania** — Pike's parcel layer is a Regrid-hosted ArcGIS Online service (services6.arcgis.com/drkDXByy6E3bYW3a): token required; PASDA lists no Pike parcels with
   attributes (search returned nothing); only vendors. Nothing taken. **HISDAC for Pike is empty: 88 dated property records against 41,696 in all (0.2 %)** — the source
   (ZTRAX) has no Pike assessor years — so Pike stays the ACS model (`pa_pike_estimates.parquet` unchanged).
5. **HISDAC-US BUPR** — Uhl & Leyk 2020, https://doi.org/10.7910/DVN/YSWMDR (CC0; file 3790309, `BUPR.tar.gz` 250 MB, deleted after clipping to
   `data/interim/county_years/bupr_window.npz`, 43 layers 1810-2015 + `BUPR_contemporary`). Values are cumulative counts of dated property records per 250 m cell at each
   half-decade (checked on the densest cell); `BUPR_contemporary` counts all records, dated or not: 2015 / contemporary is HISDAC's own completeness. By county:
   Nassau 388,421 of 402,124 (96.6 %); Dutchess 94,907 / 99,820 (95.1 %); Orange 92 %, Ulster 94 %, Putnam 95 %, Rockland 97 %; Westchester 55 %; **Suffolk 205,308 / 507,284 (40.5 %)**;
   Pike 0.2 %. Per-cell completeness inside Suffolk: Brookhaven is covered, Islip, Huntington, Babylon, East Hampton, Southold are not (cells under 12 dated records).
   Used: Nassau and Suffolk. Method (`cells_assign`): a footprint without a parcel is an outbuilding when it is under 60 m2 and a footprint at least 1.8x larger lies within 35 m (it
   takes its main's year); the mains of a cell are ordered by the existing census-model year (the ridge-model ordering of `counties_ny_estimates.py` plus ACS block-group
   decade), and the k-th of n takes the year at quantile (k-0.5)/n of the cell's normalised curve, linear inside the five-year step; steps 1811-2015, the lump built by 1810
   spread over 1750-1810. A cell uses its own curve at 12 or more dated records, else its 3 x 3 block; the census model stays where the block has fewer, where dated/all records
   is under 75 %, or where records per main building is outside 0.4-2.5 (condominium or missing records). Buildings the model puts after 2015 keep that (HISDAC was compiled
   in 2016). `basis` = `hisdac_bupr:<step end year>` (+`+outbuilding_of_main`), `order` = `bupr_cell`, `year_lo`/`year_hi` = the step. Still `estimated`.
   **Sanity check** — Levittown (box -73.54..-73.49, 40.71..40.74, 16,526 footprints): 11,849 now on 1947-1952 (known: built 1947-51); the census model had 5,000 there.
6. **Documented subdivisions** — not done: the cell curves already put Levittown on its years (above); no outlines with sourced dates were entered (`data/manual/subdivisions.geojson` not created).

## Validation (assessor's year known; `county_years.py validate`, `data/interim/county_years/validation.json`)

Truth = main buildings, placeholder years excluded. The BUPR counts include the buildings tested (as they do for the undated ones in production). Same ordering inside a cell.

| Test | n | median abs. error | within 10 y | same decade |
|---|---:|---:|---:|---:|
| Cell curve, ordered by the census model (Harrison, Scarsdale, years hidden) | 8,666 | **11 y** | 48 % | 31 % |
| Census model, same buildings | 8,666 | 23 y | 27 % | 15 % |
| Cell curve, random order (the same two towns) | 8,666 | 15 y | 43 % | 28 % |
| Cell curve, random order: Rockland / Orange / Putnam | 58,544 / 71,117 / 21,971 | 7 / 11 / 12 y | 57 / 49 / 46 % | 40 / 32 / 28 % |
| Cell curve, ordered by the truth (upper bound): Rockland / Orange / Putnam | | 2 / 3 / 3 y | 87 / 74 / 75 % | 71 / 56 / 56 % |

Only two of the eight validation towns line up with the saved validation rows; the rest were not compared. The cell curve is roughly twice as accurate as the ACS block-group model; the ordering
inside a cell is the weak part. Nassau's cells are denser than Rockland's, so its errors should be nearer Rockland's. Nothing was validated on Long Island itself (no recorded years there).

## What remains modelled, and why

- Suffolk's Islip, Huntington, Babylon, East Hampton, Southold (350,000 footprints), Smithtown's undated part and the leftovers of Brookhaven: ZTRAX has few records there, the State holds no year for them.
- Pike (38,951): no year in any open source; ZTRAX empty.
- Nassau 17,532 (cells without enough or complete records) and Dutchess 16,721 (no year on their lot).
- Nassau's pre-1900 stock is smaller than the model had (0.9 % vs 2.2 % of footprints before 1900): the assessor's years run late for old houses (see `counties_ny.md`), so BUPR under-counts them.
  The 1920s are 11.5 % of Nassau (8.1 % before): a placeholder year at 1925 may be in the curves (not flagged; the cumulative cube cannot show single years).

## For the lead (rebuild)

- Order: `county_years.py apply dutchess` (writes `ny_dutchess.parquet` from `data/interim/county_years/orig_ny_dutchess.parquet`; delete that backup if `counties_ny.py build dutchess`
  has rebuilt the footprints) -> `counties_ny_estimates.py build_outer dutchess` (needs the ACS NY geodatabase again: `counties_ny_estimates.py download`; it was deleted for space; Dutchess now
  joins the training set) -> `county_years.py hisdac nassau suffolk` (reads the estimates as `build_outer` wrote them, refreshes its `orig_*_estimates` backup itself; needs `bupr_window.npz`, 265 MB kept).
- Each footprint still has exactly one of `year_raw` / a row in `_estimates` (checked). `ny_dutchess_report.json/.txt` and `_munis.geojson` describe the old all-modelled build; the new counts are in
  `data/interim/county_years/dutchess_apply_report.json`. `muni_year_share` for Dutchess is now the share of main homes with a year per municipality.
- `counties_ny_estimates.py`: Dutchess removed from the training exclusion (one line); other counties' estimate files were not rewritten (their weights would differ in the 3rd decimal).
- Raw: `data/raw/county_years/centroids_dutchess` (pages, small), `centroids_val_orange`; BUPR tarball and tifs deleted (the URL above is the record).
