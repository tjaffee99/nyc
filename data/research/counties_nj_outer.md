# New Jersey outer counties: construction years (2026-11-11)

Stage: `pipeline/counties_nj.py <county>` (method as in `counties_nj.py` docstring and `counties_nj.md`).
Output per county: `data/interim/counties/nj_<county>.parquet` + `nj_<county>_report.json`, schema identical to
`nj_essex.parquet` (checked with pyarrow `equals`). Nothing is imputed here; `year_raw` is the tax list's year,
`heap` / `heap_county` flag placeholders.

## Sources
- Footprints: `data/raw/overture/2026-10-21.0/outer_building.parquet` (Overture release 2026-10-21.0: OpenStreetMap
  (ODbL), Microsoft ML Buildings (ODbL), Esri Community Maps), clipped to the TIGER 2024 county outline, >= 12 m2.
- Years: "Parcels and MOD-IV Composite of NJ", NJ Office of GIS, ArcGIS feature service
  https://services2.arcgis.com/XVOqAjTOJ5P6ngMu/arcgis/rest/services/Parcels_Composite_NJ_WM/FeatureServer/0
  (public NJ data; service data last edit 2026-08-18, downloaded 2026-11-11). Parcels selected by `PCL_MUN LIKE '<county code>%'`
  (Hunterdon 10, Mercer 11, Middlesex 12, Monmouth 13, Morris 14, Ocean 15, Somerset 18, Sussex 19); every county's paged
  count equalled the service's count.
- Wikidata inception/opening years of buildings (SPARQL, CC0) and Overture height-source ids (S3) ran for all eight (cheap).
- Raw parcel pages (gz GeoJSON, 4-40 MB per county) are kept in `data/raw/counties_nj/parcels/<county>/`; the derived
  `parcels_<county>.parquet` caches are 13-154 MB (Ocean's was deleted after the run: it is rebuilt from the pages on demand).
  All pages were under 100 MB per county, so none was deleted.

## Results
| County | Footprints | In a parcel | With a year | Main bldgs with year | On municipal heap | Either heap | With height |
|---|---|---|---|---|---|---|---|
| Hunterdon | 63,144 | 63,090 | 76.7% | 87.1% | 5,485 | 8,042 (16.6%) | 79.8% |
| Sussex | 63,608 | 63,495 | 82.9% | 88.6% | 12,265 | 14,126 (26.8%) | 89.3% |
| Somerset | 115,214 | 115,142 | 86.9% | 90.0% | 21,692 | 24,836 (24.8%) | 76.6% |
| Mercer | 115,653 | 115,615 | 88.8% | 92.4% | 36,782 | 38,765 (37.7%) | 88.8% |
| Morris | 177,437 | 177,339 | 91.7% | 94.9% | 42,978 | 47,461 (29.2%) | 81.1% |
| Middlesex | 225,263 | 225,134 | 83.8% | 87.0% | 55,986 | 58,224 (30.8%) | 94.0% |
| Monmouth | 229,578 | 229,410 | 92.1% | 95.5% | 66,124 | 69,560 (32.9%) | 88.6% |
| Ocean | 269,397 | 269,214 | 85.9% | 89.2% | 38,584 | 45,506 (19.7%) | 83.3% |
Total 1,259,294 footprints. "With a year" counts secondary buildings (garages, sheds, which take the main building's year);
the remainder is mostly footprints on parcels with no recorded year (vacant, exempt, or no MOD-IV match).

County-rule heap years (city rule on the whole county; counts of main buildings):
- Hunterdon 1850, 1880, 1890, 1900, 1930, 1940, 1950. Sussex 1900, 1920, 1930, 1935, 1940, 1950, 1960.
- Somerset 1890, 1900, 1910, 1920, 1924, 1929, 1930, 1940, 1950. Mercer 1886, 1887, 1890, 1897, 1900, 1910, 1920, 1925, 1930, 1935, 1940, 1950, 1960.
- Morris 1880, 1890, 1900, 1903, 1906, 1910, 1920, 1930, 1940, 1950. Middlesex 1890, 1900, 1910, 1920, 1930, 1935, 1940.
- Monmouth 1900-1950 by decade. Ocean 1900, 1910, 1920, 1925, 1930, 1935, 1940, 1945, 1950, 1960.
Per-municipality heaps are in each report (`heap_years_by_municipality`); the county-wide counts above are in `heap_years_county_rule`.

## Odd
- Every county joined: 99.9% of footprints fall in a parcel polygon; parcels without a MOD-IV record are 1-4% (Hunterdon 1,868).
- Municipalities whose recorded years are largely one assessor's rounded value (more than half of their dated buildings on a
  municipal heap): Trenton (11,264 of 17,162), Perth Amboy, New Brunswick, North Plainfield, Franklin Boro (Sussex), Boonton, Butler, Dover,
  Jefferson, Mount Olive, Mount Olive (Morris); Seaside Heights, Asbury Park, Belmar (Monmouth/Ocean). The building stage treats these as bounds, as for the five counties.
- Municipalities with few recorded years (under half dated): Andover Boro (8 of 351), Hamburg Boro (292 of 946), Manville Boro
  (1,695 of 4,989), Mine Hill Twp (173 of 1,029), South Plainfield Boro (1,650 of 8,468), Pine Beach Boro (358 of 1,060). These need
  modelled years (`estimated`) from the lead's fill; they are not empty of footprints.
- Hunterdon has 1700-1799 years on ~400 buildings (rounded 1700/1740/1750/1780/1790 heaps are owner-reported); left as the tax list gives them.
- Somerset footprints are mostly OSM and Esri (43,461) with few Microsoft; Hunterdon/Sussex the reverse. Footprint completeness
  against improved residential lots: 82-91% (`share_improved_residential_lots_with_footprint` in each report).
- Memory: Ocean's join peaked near 2.1 GB resident (sampled by ps) during the parcel read/join; the other seven stayed under about 1.3 GB.
  Nothing was killed. Windowed reading was not needed but Ocean is at the limit.
- Heights: from Overture; share with a height 77-94%.
