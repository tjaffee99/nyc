# Construction years: south-west Connecticut and Pike County, PA

Written by `pipeline/counties_ct.py` (2026-11-11). Outputs in `data/interim/counties/`: `ct_greater_bridgeport`, `ct_western_connecticut`, `ct_south_central_connecticut` (+ `_report.json/.txt`), `pa_pike` + `pa_pike_estimates` + `pa_pike_report.json`. Schema = `ny_westchester.parquet`.

## Sources

| id | What | URL | Date / licence | Used for |
|---|---|---|---|---|
| `ct_cama_2026` | Connecticut CAMA and Parcel Layer: towns' parcels joined to assessors' CAMA records (field `AYB` = actual year built, `EYB` effective year built, `State_Use`) | https://services3.arcgis.com/3FL1kr7L4LvwA2Kb/arcgis/rest/services/Connecticut_CAMA_and_Parcel_Layer/FeatureServer/0 (portal item 82a733423a244c43a9d4bf552954cea9; 2025 edition: item 45cc26320c634f64a67f1b6c6afbd9d1) | CT OPM / GIS Office, 2026 collection, fetched 2026-11-11; public data (no restriction stated in the item) | `year_raw` |
| `overture` | building footprints | `data/raw/overture/2026-10-21.0/outer_building.parquet` | ODbL / CDLA per source_dataset | footprints |
| `tiger` | county-equivalent outlines 2024 | `data/raw/tiger/tl_2024_us_county.zip` | public domain | region outlines |
| `acs_bg` | ACS 5-year 2018-2022 B25034 by block group, Pennsylvania | https://www2.census.gov/geo/tiger/TIGER_DP/2022ACS/ACS_2022_5YR_BG_42.gdb.zip | US Census Bureau, public domain | Pike modelled years |
| `hisdac_fbuy` | first built-up year, 250 m cells (Leyk & Uhl) | https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/PKJ90M | CC0 1.0 (file already in `data/raw/counties_ny_est`) | ordering covariate for Pike only, never a date |

The ACS Pennsylvania geodatabase (82 MB zip, 686 MB unpacked) was deleted after the Pike run; the URL above is the record (`python counties_ct.py pike` needs it again in `data/raw/counties_ct/acs/`: unzip there). Parcel pages: `data/raw/counties_ct/parcels/<town>/` (45 MB).

## Connecticut

Regions (the planning regions of TIGER 2024) were checked with a spatial count of parcels per town inside each outline: Greater Bridgeport 6 towns, Western Connecticut 18, South Central 15 = **39 towns** (the brief's "about 55" does not match TIGER's three regions; the other regions are not on the map). The layer misspells Greenwich as "Greenwhich"; the output says Greenwich.
Method as `counties_ny.py`: footprint inner point -> smallest parcel under it that carries a year; condominium stacks (same outline) take the most frequent year; the largest outline of a parcel is the main building, others follow it (`secondary`). `AYB` outside 1650-2026 (0 is common) counts as no year. Placeholder years: `counties_ny.find_heaps` / `heap_evidence` per town, residential (`use` 0-2) and other records separately. A footprint under 12 m2 is dropped. No state footprint fills (CT has no bulk planimetric layer used here).
`use` is guessed from the free-text `State_Use_Description` (town codes differ: 101 / 1010 are both single family), so it is rough. Bethel and Sherman publish no use fields: all their records count as homes for heap detection. `year_hist` is empty (no CRIS equivalent was looked for).

### Per region and town (recorded year = `AYB` of the parcel under the footprint, any building incl. outbuildings)

**Greater Bridgeport**: 121,697 footprints, 98.4% with a year (98.5% of main buildings), 13,363 on placeholder years; top years {'1920': 2925, '1950': 2902, '1953': 2765, '1955': 2762, '1952': 2556, '1951': 2394, '1956': 2385, '1957': 2211, '1942': 2155, '1941': 2143}

| Town | Footprints | With year | Homes with year | Placeholder years | Development years (kept) |
|---|---:|---:|---:|---|---|
| Bridgeport | 37,839 | 98% | 99% | 1867, 1877, 1882, 1887, 1892, 1897, 1900, 1902, 1907, 1910, 1917, 1920, 1930, 1940, 1942 | - |
| Easton | 4,784 | 97% | 99% | - | - |
| Fairfield | 27,403 | 98% | 99% | 1900, 1920, 1924, 1930, 1946 | - |
| Monroe | 10,301 | 98% | 99% | 1900, 1988 | - |
| Stratford | 25,009 | 99% | 100% | 1890, 1900, 1910, 1912, 1920, 1928, 1930, 1940, 1950 | - |
| Trumbull | 16,361 | 98% | 99% | 1926 | - |

**Western Connecticut**: 248,598 footprints, 96.5% with a year (97.4% of main buildings), 31,677 on placeholder years; top years {'1950': 6544, '1900': 6534, '1960': 6150, '1955': 5250, '1930': 4790, '1965': 4752, '1920': 4232, '1956': 4229, '1964': 4090, '1940': 4003}

| Town | Footprints | With year | Homes with year | Placeholder years | Development years (kept) |
|---|---:|---:|---:|---|---|
| Bethel | 9,232 | 89% | 92% | 1890, 1900, 1930, 1940 | - |
| Bridgewater | 1,872 | 89% | 92% | - | - |
| Brookfield | 8,552 | 97% | 99% | 1800, 1850, 1940, 1978 | - |
| Danbury | 27,493 | 96% | 99% | 1853, 1870, 1873, 1878, 1880, 1883, 1888, 1890, 1893, 1900, 1903, 1920, 1940 | - |
| Darien | 9,462 | 98% | 99% | 1900, 1906, 1910, 1916, 1920, 1921, 1926 | - |
| Greenwich | 27,282 | 94% | 96% | 1900, 1910, 1920, 1930, 1940, 1950, 1980, 1990 | - |
| New Canaan | 9,234 | 97% | 98% | 1900, 1920 | - |
| New Fairfield | 8,142 | 97% | 99% | 1930, 1935, 1936, 1940, 1945, 1950, 1960, 1965 | - |
| New Milford | 16,359 | 96% | 99% | 1800, 1850, 1880, 1890, 1900, 1905, 1920, 1930, 1935, 1940, 1950, 1960, 1970, 1989 | - |
| Newtown | 16,835 | 97% | 100% | 1900, 1930, 1940 | - |
| Norwalk | 29,744 | 97% | 99% | 1850, 1870, 1880, 1885, 1890, 1895, 1900, 1905, 1910, 1915, 1920, 1930, 1935, 1940, 1948, 1950 | - |
| Redding | 6,048 | 98% | 99% | 1900, 1986 | - |
| Ridgefield | 12,111 | 97% | 98% | 1900, 1910, 1920, 1930, 1935, 1940, 1950 | - |
| Sherman | 3,182 | 95% | 95% | 1900, 1950 | - |
| Stamford | 35,214 | 97% | 99% | 1870, 1880, 1890, 1900, 1905, 1910, 1920, 1925, 1930, 1939, 1940, 1941, 1950 | - |
| Weston | 5,680 | 99% | 100% | 1940 | - |
| Westport | 13,119 | 99% | 100% | 1900, 1910, 1920, 1929, 1930, 1940, 1950, 1957, 1960, 1985 | - |
| Wilton | 9,037 | 98% | 99% | 1900, 1930 | - |

**South Central Connecticut**: 211,169 footprints, 97.5% with a year (98.5% of main buildings), 51,203 on placeholder years; top years {'1900': 13875, '1920': 8298, '1950': 6450, '1930': 5340, '1960': 4657, '1955': 4485, '1910': 4264, '1956': 3841, '1952': 3790, '1940': 3764}

| Town | Footprints | With year | Homes with year | Placeholder years | Development years (kept) |
|---|---:|---:|---:|---|---|
| Bethany | 3,115 | 98% | 100% | - | - |
| Branford | 12,104 | 96% | 99% | 1850, 1880, 1890, 1900, 1910, 1915, 1920, 1925, 1928, 1930, 1935, 1938, 1940, 1950, 1960 | - |
| East Haven | 12,086 | 99% | 100% | 1900, 1910, 1920, 1930, 1940, 1950, 1974, 1979 | - |
| Guilford | 11,905 | 97% | 99% | 1850, 1900, 1920, 1930, 1940, 1950 | - |
| Hamden | 21,879 | 96% | 99% | 1890, 1900, 1910, 1915, 1920, 1925, 1930, 1940, 1945, 1950, 1955, 1960, 1965, 1970, 1975, 1980, 1990 | - |
| Madison | 9,757 | 98% | 100% | 1900, 1920, 1925, 1930, 1940 | - |
| Meriden | 21,546 | 99% | 100% | 1865, 1880, 1885, 1890, 1895, 1900, 1901, 1905, 1910, 1915, 1920, 1925, 1930, 1940, 1941, 1950 | - |
| Milford | 23,452 | 98% | 99% | 1890, 1900, 1910, 1915, 1918, 1920, 1925, 1928, 1930, 1935, 1938, 1940, 1941, 1942, 1950, 1960, 1970 | - |
| New Haven | 29,261 | 97% | 99% | 1850, 1860, 1870, 1875, 1880, 1890, 1900, 1905, 1910, 1915, 1918, 1920, 1925, 1930, 1935, 1940, 1950, 1960 | - |
| North Branford | 6,740 | 96% | 99% | - | - |
| North Haven | 11,537 | 97% | 99% | 1900, 1920, 1941, 1960 | - |
| Orange | 6,333 | 96% | 98% | - | - |
| Wallingford | 19,410 | 98% | 99% | 1870, 1880, 1890, 1900, 1910, 1920, 1925, 1930, 1940, 1950 | - |
| West Haven | 17,761 | 99% | 100% | 1890, 1900, 1910, 1920, 1925, 1930, 1935, 1938, 1940, 1941, 1945, 1950, 1960 | 1951 |
| Woodbridge | 4,283 | 99% | 100% | 1970 | - |

### What is odd

- 2-4 % of footprints have no year (parcel without AYB, building off every parcel, AYB = 0): left empty, **not modelled** (no `ct_*_estimates.parquet`; writing one would switch `county_buildings.py` to year_est for the whole file). `county_buildings.py` dates them from neighbours as it does for New Jersey. Bethel (89 %) and Bridgewater (89 %) are the lowest.
- Placeholder years are many: 1900 is the largest single year of South Central (13,875 buildings in 211,000); several towns' assessors round to 5 or 10 years (Hamden, Meriden, New Haven, Milford: 1915, 1925, 1935 ...). Bridgeport shows 1867-1907 in steps of five. Flagged by the same rule as New York; the flag does not change `year_raw`. The estimator treats flagged years as bounds.
- Heaps below 1850 (Brookfield, New Milford, Western region 1800 / 1850) are assessors' "old house" defaults.
- Footprints off every parcel (road bed, water edge) take the nearest parcel's town but have no year.

## Pike County, Pennsylvania (42103)

**No open parcel or assessment file with a year built was found.** The county's parcel service on ArcGIS Online (`pike_county_pa_parcels`, services6.arcgis.com/drkDXByy6E3bYW3a) answers "Token Required"; the county's own pages (https://www.pikepa.org/government/assessment/) point to an online GIS and a paid assessor subscription; commercial files exist (landrecords.us, reportallusa.com, about $200, year built said to be in the first; not bought, licence not open); PASDA lists no Pike parcel layer with a year. Not used: any of these.
All 38,951 footprints (Overture, >= 12 m2) are therefore **modelled** (`pa_pike_estimates.parquet`: `year_est`, `year_lo`, `year_hi`, `basis`, `bg`, `order`; `pa_pike.parquet` has `year_raw` empty, `muni_year_share` 0, municipality "Pike County" because no municipal outlines were fetched).
Model (`counties_ct.model_years`, a simplified form of `counties_ny_estimates.py`): ACS B25034 counts per block group set how many main buildings fall in each decade; order within the block group = 0.55 x HISDAC FBUY rank + 0.3 x distance to Milford / Matamoras / Dingmans Ferry / Lackawaxen rank + 0.35 x stable hash (older first); year inside a decade by position (reflected hash jitter); the 1939-or-earlier bin follows a growth curve (half built by about 1915: a stylisation, not a record). No parcels: a footprint under 40 m2 within 40 m of a larger one follows it (`+outbuilding_of_main`), 1,072 of them. Block groups with under 5 units use the county's distribution. Seasonal homes count in B25034, so the 1970s-2000s dominate (the county's real history).
Validation (Pike has no dated buildings; same code on Westchester towns with years hidden, heap years excluded, New York ACS): Scarsdale median error 30 y (23 % within 10 y, 13 % same decade), White Plains 26 y (27 %, 17 %), Rye 35 y (18 %, 9 %). That is about the skill of random ordering in `counties_ny_estimates.md` (26-37 y): the decade counts are right, which building takes which decade is close to chance, and Pike's rural spread is probably better than these towns. Do not read single buildings as dated.

## For the lead

- `county_buildings.py` globs `n[jy]_*.parquet` and `ct_*.parquet`: add `pa_*.parquet` (the `_estimates` filter already works on the stem). The three CT files carry `county` = "Greater Bridgeport" / "Western Connecticut" / "South Central Connecticut" and Pike `county` = "Pike": `extent_counties.json` names must match. Parcel caches are named `parcels_ct_<town>.parquet` so that they are not globbed.
- `year_src` = `ct_cama_2026`; Pike has none (all via `year_est`, basis `acs_bg:...`).
- Re-run: `python counties_ct.py download | build | pike | validate` (a region key limits it; builds take under 30 s, below 2 GB).
