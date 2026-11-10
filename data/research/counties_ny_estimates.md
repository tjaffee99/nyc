# Estimated construction years for the county footprints without a recorded year

Written by `pipeline/counties_ny_estimates.py check` from the built files; numbers are not typed. Every row of `data/interim/counties/ny_<county>_estimates.parquet` is an **estimate** (`estimated`): none is a record of the building.

## Sources

| id | What | URL | Licence | Used for |
|---|---|---|---|---|
| `acs_bg` | ACS 5-year 2018-2022, table B25034 (year structure built, housing units) by block group, in the TIGER/Line geodatabase with demographic data | https://www2.census.gov/geo/tiger/TIGER_DP/2022ACS/ACS_2022_5YR_BG_36.gdb.zip | US Census Bureau, public domain | how many buildings of a block group fall in each decade |
| `hisdac_fbuy` | HISDAC-US first built-up year, 250 m cells (Leyk & Uhl 2018, doi:10.7910/DVN/PKJ90M), modelled from Zillow property records | https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/PKJ90M | CC0 1.0 (dataset licence field) | one covariate to order buildings inside a block group; never a date |
| `wiki_census` | decennial census counts of each municipality, from the `US Census population` / `Historical populations` tables of its English Wikipedia article (titles in `data/raw/counties_ny_est/wiki_pop.json`, URL `https://en.wikipedia.org/wiki/<title>`) | https://en.wikipedia.org | CC BY-SA (facts from the Census Bureau) | spread the 1939-or-earlier bin over the town's growth |
| `county_pop` | `data/tables/population_counties.csv` | repo | as cited there | fallback where the town has fewer than 3 census counts up to 1940 or none before 1900 (Bedford, Briarcliff Manor, Tuckahoe, Rye city, Haverstraw village) |
| `places`, `stations` | `data/tables/places_counties.csv` (town / city centres), `data/tables/transit_stations.csv` (mnr, njt, rail) | repo | as cited there | distance covariates |

Not reachable or not used: the Census API (`api.census.gov`) answers every request with a redirect to a "missing key" page; the TIGER_DP geodatabase carries the same table, so it was not needed. HISDAC's BUPR (property-record counts) and BUPL layers were not downloaded. **USGS 1:24,000 sheets (evidence 3): not done.**

## Method

1. Footprint -> block group (point in polygon; nearest if outside). Units: main buildings (the largest outline of a parcel); outbuildings (`secondary`) take their parcel's main building's estimate (`+outbuilding_of_main` in `basis`). Footprints outside any parcel count as mains.
2. The block group's B25034 distribution (10 bins: 1939 or earlier, then decades to 2020+) is the target. Dated buildings of the same block group (partly dated municipalities, other municipalities sharing the group) are counted first and subtracted (units - dated buildings, floored at 0; the whole table is used if less than 20 % would remain). Block groups with under 5 housing units use their municipality's summed distribution (`acs_muni`).
3. Order: a ridge regression (`FEATS`: log distance to the nearest old town centre and to the nearest railroad station, HISDAC FBUY, log footprint area, height, density within 60 m, mean and spread of area and mean height within 100 m, nearest-neighbour distance, use class; each as its rank within the block group, plus squares) predicts a building's within-group age percentile. Trained on the dated, non-heap main buildings of every dated municipality of both counties (validation: that municipality left out). Buildings are sorted by the prediction (+ a small stable hash to break ties) and cut by the target distribution.
4. Year inside a decade: 70 % the building's position within its bin, 30 % a stable hash of its id, so decades do not stack on their first year. 1939-or-earlier: the same position mapped through the municipality's census-population curve (stock built by year t proportional to population(t); before its first census count a ramp over 80 years; 1700 at the earliest) - a reconstruction, not a record; `year_lo` 1700, `year_hi` 1939.
5. `basis`: `acs_bg:<decade>` or `acs_bg:pre1940+town_growth` (`+county_growth` where the county series stood in), `acs_muni:...`; `order` = `model`. HISDAC is in the ordering only, so no row is `hisdac_fbuy:`.

## Validation on the dated municipalities (years hidden, estimated the same way)

Truth = the assessor's `year_raw` of main buildings, **heap years excluded** (round estimates). Every dated municipality outside the test one is kept as known data and as the training set; the test one is hidden entirely. `random` = same table, random order; `distance_only` = ordering by distance to the centre alone.

| Municipality | n | median abs. error (years) | share within 10 y | within 5 y | same decade | median error, random order | distance only |
|---|---:|---:|---:|---:|---:|---:|---:|
| Yonkers | 25,791 | 22 | 29% | 17% | 36% | 26 | 25 |
| White Plains | 5,943 | 21 | 34% | 22% | 38% | 26 | 26 |
| Scarsdale | 5,434 | 25 | 26% | 16% | 42% | 29 | 28 |
| Rye | 3,611 | 28 | 23% | 13% | 28% | 37 | 35 |
| Somers | 4,663 | 12 | 45% | 25% | 26% | 20 | 19 |
| Harrison | 6,017 | 21 | 31% | 18% | 26% | 26 | 26 |
| New Castle | 4,864 | 16 | 36% | 19% | 27% | 26 | 23 |
| Pelham | 1,336 | 30 | 23% | 15% | 47% | 30 | 30 |
| **all** | 57,659 | 21 | 31% | 18% | 34% | | |

By true decade (all test municipalities pooled):

| True decade | n | median abs. error | within 10 y |
|---|---:|---:|---:|
| pre1940 | 22,643 | 28 | 18% |
| 1940 | 3,442 | 19 | 29% |
| 1950 | 11,677 | 13 | 45% |
| 1960 | 6,654 | 14 | 41% |
| 1970 | 3,194 | 16 | 34% |
| 1980 | 2,963 | 15 | 38% |
| 1990 | 2,761 | 12 | 45% |
| 2000 | 2,491 | 17 | 37% |
| 2010 | 1,302 | 37 | 22% |
| 2020 | 532 | 64 | 7% |

Recorded vs estimated vs ACS-expected decade shares, five dated towns (test run):

**Yonkers**

| Decade | recorded (non-heap) | estimated | ACS expected |
|---|---:|---:|---:|
| pre1940 | 49.1% | 33.9% | 33.6% |
| 1940 | 6.7% | 9.3% | 9.2% |
| 1950 | 22.7% | 22.3% | 22.1% |
| 1960 | 10.4% | 14.1% | 14.1% |
| 1970 | 3.4% | 9.2% | 9.4% |
| 1980 | 2.0% | 4.1% | 4.2% |
| 1990 | 2.2% | 2.5% | 2.6% |
| 2000 | 2.1% | 2.6% | 2.7% |
| 2010 | 0.9% | 1.9% | 1.9% |
| 2020 | 0.4% | 0.1% | 0.1% |

**White Plains**

| Decade | recorded (non-heap) | estimated | ACS expected |
|---|---:|---:|---:|
| pre1940 | 37.8% | 35.5% | 36.3% |
| 1940 | 6.7% | 4.4% | 4.5% |
| 1950 | 27.7% | 23.0% | 22.5% |
| 1960 | 8.9% | 9.8% | 10.0% |
| 1970 | 2.2% | 4.8% | 4.9% |
| 1980 | 7.3% | 9.1% | 8.8% |
| 1990 | 5.4% | 6.6% | 6.6% |
| 2000 | 2.7% | 2.4% | 2.3% |
| 2010 | 1.0% | 3.9% | 3.8% |
| 2020 | 0.3% | 0.4% | 0.4% |

**Scarsdale**

| Decade | recorded (non-heap) | estimated | ACS expected |
|---|---:|---:|---:|
| pre1940 | 48.2% | 48.9% | 48.9% |
| 1940 | 5.7% | 5.2% | 5.2% |
| 1950 | 17.3% | 18.8% | 18.9% |
| 1960 | 6.9% | 5.2% | 5.2% |
| 1970 | 3.3% | 3.7% | 3.6% |
| 1980 | 3.5% | 4.5% | 4.4% |
| 1990 | 2.8% | 1.9% | 1.9% |
| 2000 | 4.8% | 5.1% | 5.1% |
| 2010 | 5.4% | 6.6% | 6.6% |
| 2020 | 2.0% | 0.1% | 0.1% |

**Rye**

| Decade | recorded (non-heap) | estimated | ACS expected |
|---|---:|---:|---:|
| pre1940 | 35.4% | 31.2% | 32.0% |
| 1940 | 3.7% | 6.2% | 6.2% |
| 1950 | 14.8% | 15.6% | 15.6% |
| 1960 | 10.8% | 10.7% | 10.7% |
| 1970 | 4.5% | 5.1% | 5.1% |
| 1980 | 5.4% | 5.7% | 5.5% |
| 1990 | 5.1% | 5.6% | 5.5% |
| 2000 | 7.7% | 11.3% | 11.1% |
| 2010 | 9.6% | 7.6% | 7.3% |
| 2020 | 2.9% | 1.0% | 1.0% |

**Somers**

| Decade | recorded (non-heap) | estimated | ACS expected |
|---|---:|---:|---:|
| pre1940 | 9.3% | 10.0% | 12.2% |
| 1940 | 3.5% | 4.6% | 5.4% |
| 1950 | 11.2% | 11.3% | 11.5% |
| 1960 | 17.2% | 11.7% | 11.9% |
| 1970 | 17.5% | 16.6% | 16.0% |
| 1980 | 14.0% | 19.3% | 18.5% |
| 1990 | 14.8% | 10.7% | 10.2% |
| 2000 | 9.7% | 9.9% | 8.7% |
| 2010 | 2.0% | 4.8% | 4.6% |
| 2020 | 0.8% | 1.1% | 0.9% |

## What is estimated

### Westchester: 139,394 of 282,725 footprints

Largest number of estimates on one year: 2,578 (1959); median over years: 112.

| Municipality | Footprints | pre1940 | 1940-1949 | 1950-1959 | 1960-1969 | 1970-1979 | 1980-1989 | 1990-1999 | 2000-09 | 2010-19 | 2020-25 | pre-1940 curve from | top year share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
|  | 7 | 14% (acs 18%) | 0% (acs 8%) | 0% (acs 5%) | 0% (acs 13%) | 0% (acs 7%) | 14% (acs 21%) | 0% (acs 2%) | 0% (acs 3%) | 71% (acs 22%) | 0% (acs 0%) | county | 14.3% |
| Ardsley | 1,672 | 17% (acs 15%) | 3% (acs 3%) | 40% (acs 42%) | 9% (acs 9%) | 4% (acs 4%) | 10% (acs 11%) | 2% (acs 2%) | 3% (acs 3%) | 12% (acs 12%) | 0% (acs 0%) | town Ardsley, New York | 4.2% |
| Bedford | 8,269 | 24% (acs 24%) | 5% (acs 6%) | 14% (acs 15%) | 11% (acs 12%) | 16% (acs 15%) | 12% (acs 13%) | 7% (acs 7%) | 9% (acs 8%) | 1% (acs 2%) | 1% (acs 1%) | county | 2.3% |
| Briarcliff Manor | 2,662 | 10% (acs 9%) | 3% (acs 3%) | 15% (acs 17%) | 20% (acs 23%) | 4% (acs 4%) | 12% (acs 12%) | 16% (acs 14%) | 14% (acs 11%) | 6% (acs 5%) | 1% (acs 0%) | county | 4.8% |
| Bronxville | 1,453 | 76% (acs 76%) | 3% (acs 3%) | 10% (acs 10%) | 2% (acs 3%) | 3% (acs 3%) | 0% (acs 0%) | 2% (acs 2%) | 1% (acs 1%) | 2% (acs 2%) | 0% (acs 0%) | town Bronxville, New York | 3.9% |
| Buchanan | 1,236 | 20% (acs 21%) | 11% (acs 13%) | 18% (acs 20%) | 11% (acs 13%) | 7% (acs 9%) | 7% (acs 6%) | 9% (acs 11%) | 16% (acs 8%) | 0% (acs 0%) | 0% (acs 0%) | county | 8.1% |
| Cortlandt | 12,961 | 15% (acs 14%) | 6% (acs 6%) | 23% (acs 25%) | 17% (acs 16%) | 9% (acs 10%) | 12% (acs 13%) | 8% (acs 8%) | 7% (acs 7%) | 2% (acs 2%) | 0% (acs 0%) | town Cortlandt, New York | 2.5% |
| Croton-on-Hudson | 3,380 | 33% (acs 34%) | 6% (acs 6%) | 19% (acs 23%) | 7% (acs 8%) | 7% (acs 9%) | 11% (acs 11%) | 6% (acs 4%) | 3% (acs 3%) | 3% (acs 1%) | 4% (acs 1%) | town Croton-on-Hudson, New York | 3.0% |
| Dobbs Ferry | 3,099 | 38% (acs 38%) | 2% (acs 2%) | 16% (acs 17%) | 13% (acs 15%) | 4% (acs 5%) | 10% (acs 10%) | 5% (acs 4%) | 6% (acs 5%) | 7% (acs 4%) | 0% (acs 0%) | town Dobbs Ferry, New York | 2.3% |
| Eastchester | 5,977 | 31% (acs 28%) | 14% (acs 14%) | 31% (acs 34%) | 9% (acs 10%) | 5% (acs 6%) | 3% (acs 3%) | 2% (acs 3%) | 3% (acs 2%) | 1% (acs 1%) | 0% (acs 0%) | town Eastchester, New York | 3.4% |
| Elmsford | 1,581 | 25% (acs 25%) | 1% (acs 1%) | 19% (acs 20%) | 18% (acs 21%) | 9% (acs 10%) | 3% (acs 4%) | 10% (acs 3%) | 3% (acs 3%) | 11% (acs 12%) | 0% (acs 0%) | county | 6.6% |
| Greenburgh | 13,973 | 13% (acs 14%) | 7% (acs 8%) | 26% (acs 31%) | 14% (acs 16%) | 9% (acs 9%) | 11% (acs 7%) | 7% (acs 6%) | 9% (acs 6%) | 3% (acs 2%) | 0% (acs 0%) | town Greenburgh, New York | 2.8% |
| Harrison | 842 | 4% (acs 9%) | 2% (acs 6%) | 6% (acs 14%) | 27% (acs 12%) | 12% (acs 14%) | 13% (acs 12%) | 11% (acs 14%) | 5% (acs 4%) | 7% (acs 9%) | 12% (acs 5%) | county | 20.4% |
| Hastings-on-Hudson | 2,940 | 49% (acs 47%) | 8% (acs 8%) | 19% (acs 22%) | 12% (acs 13%) | 2% (acs 2%) | 3% (acs 3%) | 2% (acs 1%) | 2% (acs 2%) | 2% (acs 1%) | 0% (acs 0%) | town Hastings-on-Hudson, New York | 2.3% |
| Irvington | 2,198 | 22% (acs 26%) | 10% (acs 6%) | 30% (acs 27%) | 5% (acs 7%) | 6% (acs 7%) | 14% (acs 13%) | 9% (acs 10%) | 1% (acs 2%) | 0% (acs 0%) | 2% (acs 3%) | town Irvington, New York | 8.7% |
| Larchmont | 60 | 33% (acs 22%) | 17% (acs 27%) | 8% (acs 16%) | 23% (acs 6%) | 5% (acs 7%) | 3% (acs 5%) | 0% (acs 0%) | 0% (acs 1%) | 10% (acs 16%) | 0% (acs 0%) | town Larchmont, New York | 21.7% |
| Lewisboro | 6,880 | 18% (acs 17%) | 5% (acs 5%) | 10% (acs 10%) | 14% (acs 13%) | 17% (acs 16%) | 22% (acs 23%) | 7% (acs 8%) | 4% (acs 5%) | 2% (acs 2%) | 0% (acs 0%) | town Lewisboro, New York | 2.7% |
| Mamaroneck | 92 | 17% (acs 32%) | 13% (acs 17%) | 5% (acs 15%) | 38% (acs 12%) | 2% (acs 4%) | 15% (acs 7%) | 2% (acs 5%) | 2% (acs 4%) | 4% (acs 6%) | 0% (acs 0%) | town Mamaroneck (town), New York | 30.4% |
| Mamaroneck, Village | 129 | 16% (acs 23%) | 9% (acs 14%) | 3% (acs 5%) | 15% (acs 20%) | 4% (acs 2%) | 21% (acs 10%) | 12% (acs 16%) | 4% (acs 4%) | 16% (acs 7%) | 0% (acs 0%) | county | 8.5% |
| Mount Kisco | 1,579 | 12% (acs 13%) | 3% (acs 3%) | 21% (acs 20%) | 29% (acs 29%) | 8% (acs 8%) | 12% (acs 14%) | 4% (acs 4%) | 12% (acs 9%) | 0% (acs 0%) | 0% (acs 0%) | town Mount Kisco, New York | 3.6% |
| Mount Pleasant | 3,269 | 14% (acs 17%) | 7% (acs 9%) | 16% (acs 22%) | 13% (acs 12%) | 16% (acs 17%) | 10% (acs 4%) | 10% (acs 7%) | 11% (acs 9%) | 3% (acs 2%) | 0% (acs 0%) | town Mount Pleasant, New York | 4.3% |
| Mount Vernon | 13,312 | 46% (acs 47%) | 12% (acs 12%) | 13% (acs 13%) | 10% (acs 10%) | 6% (acs 6%) | 3% (acs 3%) | 3% (acs 3%) | 4% (acs 4%) | 3% (acs 3%) | 0% (acs 0%) | town Mount Vernon, New York | 1.4% |
| New Castle | 551 | 16% (acs 24%) | 2% (acs 4%) | 15% (acs 14%) | 11% (acs 6%) | 5% (acs 8%) | 24% (acs 29%) | 19% (acs 11%) | 2% (acs 2%) | 7% (acs 3%) | 0% (acs 0%) | town New Castle, New York | 8.3% |
| New Rochelle | 7,292 | 45% (acs 46%) | 8% (acs 9%) | 13% (acs 13%) | 8% (acs 8%) | 4% (acs 4%) | 6% (acs 5%) | 6% (acs 5%) | 5% (acs 6%) | 3% (acs 3%) | 1% (acs 1%) | town New Rochelle, New York | 1.7% |
| North Castle | 6,106 | 16% (acs 14%) | 4% (acs 3%) | 15% (acs 15%) | 19% (acs 20%) | 9% (acs 10%) | 7% (acs 7%) | 15% (acs 15%) | 7% (acs 9%) | 8% (acs 7%) | 0% (acs 0%) | town North Castle, New York | 2.2% |
| North Salem | 3,491 | 27% (acs 29%) | 3% (acs 4%) | 8% (acs 9%) | 14% (acs 15%) | 19% (acs 20%) | 13% (acs 10%) | 9% (acs 6%) | 6% (acs 5%) | 3% (acs 2%) | 0% (acs 0%) | town North Salem, New York | 2.6% |
| Ossining | 2,204 | 9% (acs 10%) | 4% (acs 5%) | 11% (acs 14%) | 17% (acs 22%) | 5% (acs 6%) | 25% (acs 28%) | 12% (acs 5%) | 12% (acs 4%) | 5% (acs 5%) | 0% (acs 1%) | town Ossining (town), New York | 6.4% |
| Ossining, Village | 6,185 | 35% (acs 39%) | 6% (acs 7%) | 16% (acs 18%) | 10% (acs 9%) | 7% (acs 8%) | 8% (acs 7%) | 7% (acs 5%) | 3% (acs 3%) | 7% (acs 4%) | 0% (acs 0%) | town Ossining (village), New York | 2.2% |
| Peekskill | 6,194 | 34% (acs 37%) | 4% (acs 4%) | 12% (acs 14%) | 13% (acs 15%) | 8% (acs 9%) | 9% (acs 9%) | 6% (acs 5%) | 8% (acs 5%) | 4% (acs 2%) | 1% (acs 0%) | town Peekskill, New York | 1.7% |
| Pelham | 23 | 35% (acs 43%) | 4% (acs 9%) | 4% (acs 8%) | 22% (acs 11%) | 30% (acs 22%) | 0% (acs 0%) | 0% (acs 2%) | 4% (acs 5%) | 0% (acs 0%) | 0% (acs 0%) | town Pelham (town), New York | 13.0% |
| Pelham Manor | 22 | 59% (acs 65%) | 5% (acs 6%) | 14% (acs 13%) | 18% (acs 8%) | 5% (acs 3%) | 0% (acs 0%) | 0% (acs 0%) | 0% (acs 4%) | 0% (acs 0%) | 0% (acs 0%) | county | 13.6% |
| Pleasantville | 1,352 | 35% (acs 35%) | 4% (acs 5%) | 23% (acs 24%) | 15% (acs 15%) | 10% (acs 12%) | 5% (acs 6%) | 2% (acs 1%) | 1% (acs 1%) | 5% (acs 1%) | 0% (acs 0%) | town Pleasantville, New York | 4.1% |
| Port Chester | 145 | 20% (acs 18%) | 19% (acs 22%) | 20% (acs 14%) | 10% (acs 14%) | 6% (acs 9%) | 1% (acs 3%) | 7% (acs 7%) | 7% (acs 7%) | 9% (acs 5%) | 0% (acs 0%) | town Port Chester, New York | 6.9% |
| Pound Ridge | 205 | 13% (acs 18%) | 0% (acs 1%) | 21% (acs 18%) | 13% (acs 14%) | 19% (acs 21%) | 3% (acs 6%) | 23% (acs 12%) | 7% (acs 8%) | 1% (acs 2%) | 0% (acs 0%) | town Pound Ridge, New York | 13.2% |
| Rye | 1,068 | 12% (acs 19%) | 7% (acs 15%) | 20% (acs 21%) | 6% (acs 10%) | 4% (acs 9%) | 16% (acs 7%) | 5% (acs 4%) | 25% (acs 10%) | 4% (acs 4%) | 1% (acs 0%) | county | 11.8% |
| Rye Brook | 48 | 2% (acs 5%) | 0% (acs 1%) | 8% (acs 13%) | 17% (acs 25%) | 10% (acs 14%) | 15% (acs 13%) | 12% (acs 18%) | 35% (acs 10%) | 0% (acs 1%) | 0% (acs 0%) | county | 20.8% |
| Scarsdale | 219 | 29% (acs 34%) | 5% (acs 6%) | 20% (acs 21%) | 10% (acs 5%) | 7% (acs 7%) | 10% (acs 9%) | 1% (acs 2%) | 5% (acs 8%) | 14% (acs 7%) | 0% (acs 0%) | county | 7.8% |
| Sleepy Hollow | 968 | 43% (acs 51%) | 8% (acs 6%) | 8% (acs 9%) | 11% (acs 8%) | 4% (acs 6%) | 1% (acs 2%) | 10% (acs 12%) | 15% (acs 6%) | 0% (acs 0%) | 0% (acs 0%) | town Sleepy Hollow, New York | 6.7% |
| Somers | 2,621 | 2% (acs 13%) | 1% (acs 5%) | 2% (acs 9%) | 2% (acs 8%) | 18% (acs 15%) | 29% (acs 19%) | 26% (acs 9%) | 13% (acs 7%) | 7% (acs 13%) | 2% (acs 1%) | town Somers, New York | 6.7% |
| Tarrytown | 3,164 | 31% (acs 38%) | 9% (acs 12%) | 18% (acs 14%) | 8% (acs 11%) | 9% (acs 6%) | 10% (acs 8%) | 5% (acs 4%) | 6% (acs 3%) | 5% (acs 4%) | 0% (acs 0%) | town Tarrytown, New York | 8.7% |
| Tuckahoe | 1,526 | 25% (acs 25%) | 7% (acs 7%) | 11% (acs 12%) | 19% (acs 19%) | 11% (acs 10%) | 10% (acs 10%) | 6% (acs 5%) | 4% (acs 5%) | 7% (acs 7%) | 0% (acs 0%) | county | 2.4% |
| White Plains | 2,394 | 26% (acs 30%) | 3% (acs 5%) | 13% (acs 10%) | 16% (acs 15%) | 9% (acs 10%) | 13% (acs 9%) | 7% (acs 7%) | 7% (acs 8%) | 6% (acs 6%) | 0% (acs 0%) | town White Plains, New York | 3.5% |
| Yonkers | 1,792 | 12% (acs 21%) | 9% (acs 12%) | 22% (acs 18%) | 14% (acs 15%) | 20% (acs 13%) | 5% (acs 6%) | 7% (acs 3%) | 4% (acs 5%) | 7% (acs 6%) | 0% (acs 0%) | town Yonkers, New York | 4.6% |
| Yorktown | 4,253 | 12% (acs 14%) | 5% (acs 7%) | 15% (acs 17%) | 11% (acs 15%) | 12% (acs 13%) | 24% (acs 17%) | 8% (acs 4%) | 7% (acs 6%) | 3% (acs 5%) | 3% (acs 2%) | town Yorktown, New York | 4.6% |

### Rockland: 4,454 of 99,559 footprints

Largest number of estimates on one year: 249 (2003); median over years: 6.

| Municipality | Footprints | pre1940 | 1940-1949 | 1950-1959 | 1960-1969 | 1970-1979 | 1980-1989 | 1990-1999 | 2000-09 | 2010-19 | 2020-25 | pre-1940 curve from | top year share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
|  | 2 | 0% (acs 0%) | 0% (acs 0%) | 0% (acs 41%) | 0% (acs 0%) | 0% (acs 0%) | 50% (acs 55%) | 50% (acs 4%) | 0% (acs 0%) | 0% (acs 0%) | 0% (acs 0%) | county | 50.0% |
| Airmont | 54 | 9% (acs 10%) | 7% (acs 5%) | 15% (acs 10%) | 4% (acs 4%) | 15% (acs 22%) | 4% (acs 6%) | 28% (acs 13%) | 15% (acs 28%) | 4% (acs 3%) | 0% (acs 0%) | county | 9.3% |
| Chestnut Ridge | 62 | 10% (acs 14%) | 10% (acs 6%) | 10% (acs 19%) | 5% (acs 8%) | 18% (acs 26%) | 39% (acs 8%) | 5% (acs 15%) | 3% (acs 3%) | 2% (acs 1%) | 0% (acs 0%) | county | 32.3% |
| Clarkstown | 795 | 5% (acs 7%) | 6% (acs 3%) | 5% (acs 10%) | 10% (acs 12%) | 19% (acs 29%) | 13% (acs 15%) | 14% (acs 13%) | 25% (acs 7%) | 2% (acs 3%) | 0% (acs 0%) | town Clarkstown, New York | 18.5% |
| Grand View-on-Hudson | 5 | 0% (acs 0%) | 0% (acs 1%) | 80% (acs 44%) | 0% (acs 2%) | 0% (acs 4%) | 0% (acs 45%) | 0% (acs 4%) | 20% (acs 1%) | 0% (acs 0%) | 0% (acs 0%) | county | 20.0% |
| Haverstraw | 577 | 0% (acs 1%) | 0% (acs 2%) | 1% (acs 6%) | 1% (acs 4%) | 42% (acs 47%) | 12% (acs 13%) | 21% (acs 15%) | 23% (acs 13%) | 0% (acs 0%) | 0% (acs 0%) | town Haverstraw (town), New York | 11.1% |
| Haverstraw, Village | 175 | 11% (acs 22%) | 5% (acs 10%) | 9% (acs 14%) | 11% (acs 18%) | 3% (acs 5%) | 7% (acs 10%) | 6% (acs 3%) | 38% (acs 12%) | 11% (acs 7%) | 0% (acs 0%) | county | 18.3% |
| Hillburn | 27 | 15% (acs 13%) | 15% (acs 18%) | 11% (acs 17%) | 0% (acs 0%) | 37% (acs 35%) | 4% (acs 4%) | 0% (acs 0%) | 11% (acs 11%) | 7% (acs 3%) | 0% (acs 0%) | town Hillburn, New York | 11.1% |
| Kaser | 11 | 9% (acs 1%) | 0% (acs 2%) | 0% (acs 1%) | 0% (acs 13%) | 0% (acs 5%) | 0% (acs 3%) | 45% (acs 31%) | 27% (acs 19%) | 9% (acs 25%) | 9% (acs 1%) | county | 18.2% |
| Montebello | 64 | 17% (acs 16%) | 6% (acs 14%) | 2% (acs 6%) | 8% (acs 11%) | 3% (acs 6%) | 11% (acs 12%) | 11% (acs 14%) | 42% (acs 21%) | 0% (acs 1%) | 0% (acs 0%) | county | 28.1% |
| New Hempstead | 53 | 9% (acs 11%) | 6% (acs 13%) | 13% (acs 17%) | 11% (acs 12%) | 19% (acs 30%) | 6% (acs 8%) | 0% (acs 0%) | 36% (acs 7%) | 0% (acs 2%) | 0% (acs 0%) | county | 26.4% |
| New Square | 65 | 5% (acs 3%) | 0% (acs 1%) | 0% (acs 1%) | 0% (acs 2%) | 11% (acs 9%) | 14% (acs 13%) | 28% (acs 24%) | 17% (acs 22%) | 26% (acs 25%) | 0% (acs 0%) | county | 7.7% |
| Nyack | 160 | 5% (acs 6%) | 1% (acs 2%) | 17% (acs 14%) | 20% (acs 24%) | 16% (acs 14%) | 12% (acs 11%) | 2% (acs 3%) | 12% (acs 10%) | 11% (acs 12%) | 2% (acs 2%) | town Nyack, New York | 4.4% |
| Orangetown | 649 | 9% (acs 13%) | 10% (acs 13%) | 15% (acs 20%) | 13% (acs 16%) | 10% (acs 11%) | 9% (acs 11%) | 7% (acs 6%) | 18% (acs 6%) | 8% (acs 6%) | 0% (acs 0%) | town Orangetown, New York | 14.5% |
| Piermont | 41 | 12% (acs 15%) | 7% (acs 10%) | 7% (acs 9%) | 7% (acs 8%) | 15% (acs 13%) | 29% (acs 31%) | 10% (acs 3%) | 12% (acs 11%) | 0% (acs 0%) | 0% (acs 0%) | town Piermont, New York | 9.8% |
| Pomona | 28 | 0% (acs 1%) | 0% (acs 0%) | 7% (acs 5%) | 29% (acs 27%) | 4% (acs 6%) | 54% (acs 51%) | 4% (acs 2%) | 0% (acs 1%) | 4% (acs 8%) | 0% (acs 0%) | county | 10.7% |
| Ramapo | 544 | 3% (acs 4%) | 2% (acs 2%) | 6% (acs 6%) | 14% (acs 14%) | 6% (acs 7%) | 7% (acs 8%) | 10% (acs 11%) | 18% (acs 18%) | 30% (acs 28%) | 4% (acs 2%) | town Ramapo, New York | 4.6% |
| Sloatsburg | 57 | 12% (acs 14%) | 2% (acs 1%) | 37% (acs 30%) | 14% (acs 19%) | 19% (acs 22%) | 2% (acs 2%) | 9% (acs 9%) | 5% (acs 3%) | 0% (acs 1%) | 0% (acs 0%) | county | 8.8% |
| Spring Valley | 298 | 7% (acs 7%) | 1% (acs 2%) | 7% (acs 7%) | 23% (acs 25%) | 12% (acs 10%) | 5% (acs 5%) | 2% (acs 2%) | 7% (acs 6%) | 35% (acs 34%) | 0% (acs 1%) | town Spring Valley, New York | 5.4% |
| Stony Point | 582 | 1% (acs 5%) | 2% (acs 5%) | 6% (acs 15%) | 14% (acs 27%) | 4% (acs 10%) | 6% (acs 8%) | 8% (acs 15%) | 44% (acs 10%) | 14% (acs 5%) | 0% (acs 0%) | town Stony Point, New York | 33.3% |
| Suffern | 77 | 40% (acs 39%) | 12% (acs 13%) | 3% (acs 4%) | 1% (acs 5%) | 30% (acs 22%) | 13% (acs 13%) | 0% (acs 1%) | 0% (acs 2%) | 1% (acs 2%) | 0% (acs 0%) | town Suffern, New York | 9.1% |
| Upper Nyack | 15 | 27% (acs 30%) | 0% (acs 6%) | 20% (acs 26%) | 13% (acs 13%) | 7% (acs 5%) | 13% (acs 9%) | 0% (acs 3%) | 20% (acs 6%) | 0% (acs 3%) | 0% (acs 0%) | town Upper Nyack, New York | 20.0% |
| Wesley Hills | 48 | 0% (acs 0%) | 0% (acs 0%) | 4% (acs 8%) | 15% (acs 8%) | 12% (acs 12%) | 29% (acs 33%) | 19% (acs 17%) | 0% (acs 0%) | 21% (acs 22%) | 0% (acs 0%) | county | 10.4% |
| West Haverstraw | 65 | 9% (acs 10%) | 2% (acs 3%) | 9% (acs 7%) | 6% (acs 8%) | 23% (acs 20%) | 25% (acs 29%) | 6% (acs 16%) | 20% (acs 6%) | 0% (acs 1%) | 0% (acs 0%) | town West Haverstraw, New York | 18.5% |

Each decade cell: share of the municipality's estimated footprints (in brackets the table's expected share, which differs where dated buildings in shared block groups were subtracted or the rounding of small groups bites).

## Weak spots

- A decade is only as good as the order inside the block group; the order model beats a random one by a few years, not by much (table above). Expect the right decade for roughly a third of buildings; the distribution of decades per block group is what is trustworthy, not any single building.
- B25034 counts housing units, not buildings: apartment blocks hold many units, so a decade of apartment building is over-represented in the target relative to the building count. Non-residential buildings take the residential distribution.
- The 'recorded' column excludes heap years (round, mostly old), which makes it younger than the truth; the ACS-vs-recorded gap in Yonkers (pre-1940: ACS 34 %, assessor 49 %) is also the units-versus-buildings effect above: ACS counts apartments, the assessor's list counts buildings.
- ACS sample error (the margins of error are in the geodatabase, not used) is large for small block groups; the 2018-2022 survey puts the cut at 2022; the footprints are 2026.
- Demolished houses are not in B25034: the target is of surviving units only, the same as the footprints.
- The pre-1940 curve assumes the surviving stock was built in proportion to population; the real stock has older buildings under-represented (demolition), so early years are probably too common.
- Overture/State footprints include sheds and garages that have no parcel main building; they are treated as mains and take housing-unit shares.
- Nassau: the method needs only footprints, Census data and the order covariates, so it would run; with no recorded year in the county at all the order model could not be trained there and would be borrowed from Westchester and Rockland (an unchecked transfer across the county line), and the same per-building accuracy (about a third in the right decade) would apply.
