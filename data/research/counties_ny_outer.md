# The outer New York counties: footprints with a construction year

> **Superseded in part (2026-11-11, later the same day):** Dutchess and Nassau are no longer all modelled. `data/research/county_years.md` found recorded years for 87 % of Dutchess (the State's parcel centroid points) and assessor-derived cell curves for 97 % of Nassau and for Brookhaven (HISDAC-US BUPR, source `modelled_cells`). The figures below describe the first pass.


Putnam (36079), Sullivan (36105), Ulster (36111), Dutchess (36027), Orange (36071), Nassau (36059), Suffolk (36103).
Stages: `pipeline/counties_ny.py` (parcels, footprints, years as recorded) and `pipeline/counties_ny_estimates.py`
(`build_outer`: years modelled where the roll has none). Built and fetched **2026-11-11**. Westchester and Rockland are
untouched (`counties_ny.md`, `counties_ny_estimates.md`).

## Sources (all fetched 2026-11-11)

| What | URL | Licence / terms | Used for |
|---|---|---|---|
| NYS Tax Parcels Public (2025 rolls, published May 2026) | https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Tax_Parcels_Public/FeatureServer/1 | State's service text: counties "specifically authorized" sharing; as is | parcel outlines, `YR_BLT`, class, municipality |
| NYS Building Footprints (county planimetrics) | https://gisservices.its.ny.gov/arcgis/rest/services/BuildingFootprints/FeatureServer/2 | public | fill where Overture has no footprint |
| NYS Civil Boundaries (layers 6, 7) | https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Civil_Boundaries/FeatureServer | public | municipality names for counties without parcels; pieces of the big counties |
| SHPO CRIS Building USN points | https://services.arcgis.com/1xFZPtKn1wKC6POA/arcgis/rest/services/Building_USN_Points/FeatureServer/2 | public | names; a year where the inventory name ends in one |
| Overture buildings 2026-10-21.0 (`outer_building.parquet`) | the lead's extract | Overture licences | footprints |
| ACS 2018-22 B25034, HISDAC-US FBUY, Wikipedia census tables | as `counties_ny_estimates.md` | public domain / CC0 / CC BY-SA | the modelled years |
| Wikipedia county articles ("<Name> County, New York"), `wiki_pop.json` keys `county:<name>` | https://en.wikipedia.org | CC BY-SA | county census series: fallback of the pre-1940 growth curve (the repo table has none for these counties except Nassau) |

Which counties the State publishes (counts of `COUNTY_NAME` in the parcel layer, 2026-11-11): Putnam 42,291 (34,966 with `YR_BLT`),
Sullivan 67,340 (40,213), Ulster 88,260 (66,748), Orange 145,694 (119,127), Suffolk 586,600 (80,496); **Dutchess 0, Nassau 0**.
Dutchess: the county's open-data hub carries no parcels; its Parcel Access viewer and commercial resellers (ReportAll, about $200)
carry year built; no free bulk file found. Nassau: see `counties_ny.md` (no public year, `YR_BLT` null in the centroid layer).

## Results

| County | Footprints | Of them from the State's layer | Recorded year | Modelled | Placeholder (heap) flagged |
|---|---:|---:|---:|---:|---:|
| Putnam | 41,171 | 4,380 | 39,954 (97.0 %) | 1,217 (3.0 %) | 9,358 |
| Sullivan | 77,991 | 17,404 | 69,444 (89.0 %) | 8,547 (11.0 %) | 20,731 |
| Ulster | 120,160 | 63,516 | 105,778 (88.0 %) | 14,382 (12.0 %) | 24,568 |
| Dutchess | 133,224 | 17,036 | 0 | 133,224 (100 %) | - |
| Orange | 159,031 | 2,737 | 144,827 (91.1 %) | 14,204 (8.9 %) | 31,180 |
| Nassau | 530,817 | 58,318 | 0 | 530,817 (100 %) | - |
| Suffolk | 683,514 | 15,920 | 112,432 (16.4 %) | 571,082 (83.6 %) | 16,222 |

Recorded + modelled = footprints in every county (each footprint has exactly one of `year_raw` / a row in `ny_<county>_estimates.parquet`;
checked). "Heap" counts footprints on a placeholder year (the Westchester rule, per assessing town; they keep `year_raw` and
`heap` = True, no estimate is written for them). The ten most frequent years and the heap years per town are in `ny_<county>_report.json`.

### Per county

- **Putnam**: all 9 municipalities carry years (100 % of main homes). Heaps: 1900, 1920-1950 and some 1960s, county-wide the usual round
  years; 1950 (1,954), 1940 (1,548), 1960 are the most frequent years.
- **Sullivan**: the roll is complete for houses (88-100 % of main homes in every town; Rockland 88 %, Callicoon 90 %). Heavy placeholders:
  1940 (4,593), 1950, 1960, 1930 and 1920 are the top years; 20 heap years flagged county-wide. 17,404 footprints come from the State's layer
  (Overture is thin in the Catskills).
- **Ulster**: Denning 87 %, Hardenburgh 86 %, Kingston (town) 89 % of main homes; the rest ~100 %. 1900 is the top year (4,804). Overture
  has 57,086 buildings, the State's layer 110,172: 63,516 footprints (53 %) are the State's 2007-2013 outlines, they have no heights (25,871 of 120,160
  have one). Kingston the city is in the file (24 municipalities).
- **Orange**: all 41 municipalities dated; 1900 (7,125) and 1920 (5,030) the top years. Largest county file by dated footprints.
- **Dutchess**: no public year anywhere. Footprints only; municipality read from the civil boundaries (30 pieces: villages, towns outside
  villages, cities; "X, Village" / "X, Town" where names collide); `muni_year_share` = 0. All years modelled (ACS blocks groups; 1940-2019 are
  ~80 % of the footprints; the largest year holds 1,988 = 1.5 %).
- **Nassau**: no public year; as Dutchess, 69 municipalities. All modelled. 1950-1959 is Levittown's decade: 19,000 footprints a year there
  (the ACS table says so; real, not a pile-up). The pre-1940 stock has a stepped yearly profile (the town series are census points 10 years apart).
- **Suffolk**: the State's roll has years for **Southampton (about 100 %), Shelter Island, Riverhead (about 90 %), Smithtown (about 56 %)** only;
  Babylon, Brookhaven, East Hampton, Huntington, Islip, Southold carry none (3 parcels in Southold). Those six towns plus the unrecorded part of
  Smithtown and the parcels without a year are modelled: 83.6 % of the file. Villages inside the dated towns that publish nothing (Head of the Harbor
  71 %, Nissequogue 69 %, Village of the Branch 74 %) are mixed.

### Odd things

- **Southampton 1991**: 10,715 recorded houses on 1991 (neighbours 1,300-1,500). Flagged as a placeholder (`EXTRA_HEAPS`, `find_heaps` stops at 1990):
  10,324 footprints with `heap` = True; the scatter test gives 0.75 (spread like its era, not one subdivision). 1994 (3,413) and 1997 (3,125) are
  also high, not flagged. Without this the file would show 11 thousand houses built in one year.
- The State service answers HTTP 400 for a few parcel windows (very large parcels): the downloader halves the window and skips the single parcel it
  cannot return (Sullivan 3239585, Suffolk 2957353 and one or two more; logged `the service cannot return it; skipped`). A few parcels lost.
- Overture's footprints cover rural Ulster, Sullivan and Dutchess poorly; State outlines fill the gap (about half in Ulster). No hand count.
- Population series from Wikipedia failed for towns whose title is a disambiguation (Newburgh town, Warwick, Wallkill, ...): those use the county series.
- CRIS names with a year: Sullivan 5, Ulster 9 (+114 circa), Orange 43 (+25), Suffolk 290; none for Putnam.

## Method changes (code)

- `counties_ny.py`: `OUTER` counties read `outer_building.parquet` (windowed by the county's bounding box, DuckDB 1 GB); Westchester and Rockland still
  read `region_building.parquet`. Counties without parcels (`build_without_parcels`) get a footprints-only file with the same columns.
  Nassau and Suffolk are built in pieces (each city / town outline plus the remainder, `build_pieces`, files in `data/interim/counties/parts/`, deleted after
  the merge; resumable) because one pass needs more than 2 GB; peak was 1.55 GB (Suffolk). The downloads halve refused windows.
- `counties_ny_estimates.py build_outer [county ...]`: one ridge model on every county with recorded years (the two inner ones, Putnam, Sullivan,
  Ulster, Orange, Suffolk); normal equations cached per county (`data/interim/counties_ny_est/trainsums_*.npz`). Old centres for counties
  without hand-made places = centres of the State's cities, villages and towns (Nassau: the repo's places table). Neighbourhood features computed in chunks.
  The inner counties' estimate files are not rewritten.

## Not checked

- No validation of the model on these counties (Westchester's validation, median error 21 years, a third in the right decade, is the only figure; the
  transfer to Long Island, where subdivisions are single-year tracts, is untested; Nassau and Suffolk will be the least accurate).
- `counties_ny.py check` has no known-building list for the new counties; a few spot checks by coordinates remembered from the buildings' articles
  were inconclusive (the points did not fall on the buildings) and are not reported as passes.
- Overture-vs-State duplicates were handled by the Westchester rule (overlap under 10 %); not examined here.
- Raw downloads (largest 70 MB) were kept; nothing over 100 MB was downloaded, total `data/raw/counties_ny` is about 300 MB.
