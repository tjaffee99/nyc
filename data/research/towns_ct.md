# Stamford and Bridgeport: dates and landmark models (towns round, second pass, 2026-11-11)

Files: `data/tables/known_building_dates.ct_towns.csv` (100 rows), `viewer/src/landmarks/ct-towns.ts` (export
`CT_TOWNS`, 14 models), scripts in `data/research/towns_ct_build/` (`build_ct.py` makes the CSV, `fill.py` makes
the .ts from `ct-towns.tmpl.ts`, `check.py` the numeric check), downloads in `data/interim/towns_ct_raw/`
(Wikipedia wikitext in `wp/`, OpenStreetMap map-API box, Wikidata box results, ConnCRIS points).

## Dates

Footprints: `ct_western_connecticut.parquet` (muni Stamford), `ct_greater_bridgeport.parquet` (muni Bridgeport).
Every row's point is `representative_point()` of its outline; all 45 + 55 rows pass a point-in-polygon test.

- **Manual rows (15 Stamford, 14 Bridgeport)**: each year read on a Wikipedia article fetched in this session
  (URL in the row; wikitext cached in `wp/`). The footprint is identified by the article's coordinates, the
  footprint's own name (Overture carries OpenStreetMap names: "One Landmark Square", "Park Tower Stamford", "Total
  Mortgage Arena", "McLevy Hall", "Saint Augustine Cathedral", "Bridgeport Post Office" ...), size and the mapped
  height (Landmark 89.9 m = 295 ft; Park Tower 106.7 m = 350 ft; Bridgeport Center 76.0 m = 248 ft). Weak matches
  are marked `estimate` in the note (Universalist Church, St. John's Episcopal Church).
- **Summer House** (Stamford, 85 m footprint with the placeholder 1900): identified because OpenStreetMap puts
  Flinders Lane, the restaurant on the ground floor of the article's "Summer House" (completed 2016), 22 m from it.
- **Corrections of the assessor** worth knowing: Basilica of St. John 2019 -> 1868; Fish Church 1955 -> 1958;
  Old Town Hall 1939 -> 1907; Palace and Majestic (Bridgeport) 1900 -> 1922; St. Augustine Cathedral 1964 -> 1868;
  the Universalist church 1810 -> 1870; Atlantic Station 2016 -> 2017.
- **ConnCRIS rows (30 Stamford, 41 Bridgeport)**: the State Historic Preservation Office's public feature service
  (layer 1 of `CT_Public_Above_Ground_Resources`, queried with `cris.py`: 2,370 points for Stamford, 1,592 for
  Bridgeport). For each footprint that is named or at least 700 m2 and whose assessor year is missing or a heap,
  the earliest `ConstructD` of the inventory points inside it. `exact:` when there is one dated point (or the
  points agree within 8 years and none is "CIRCA"), `estimate:` otherwise. Points whose name says DEMOLISHED are
  ignored. Mostly Yale & Towne and Bridgeport factories, schools, churches. Licence CC BY-NC-ND (as the New Haven
  note): the lead decides whether these 71 rows ship; they are separable by `source_url` (the arcgis item page).
- Not found / not done: the Stamford Palace Theatre (Wikipedia gives no coordinates for it; OpenStreetMap's point
  falls on a 2014 footprint), One Stamford Forum and the Marriott (no footprint could be told apart: heights of
  60-64 m near the Forum belong to three separate footprints), the Post Office (421 Atlantic St: no footprint at the
  article's coordinates), Ferguson Library, the Suburban Club, UConn Stamford, RBS/UBS, Harbor Point's towers,
  Hotel Beach, Remington's surviving lofts, the PSEG plant, University of Bridgeport, Bridgeport and St. Vincent's
  hospitals (pages missing or no footprint named). Largest footprints still without a usable year (ids by prefix):
  Stamford 85e62e54 (15,430 m2 at 41.0343, -73.5330), 238ab4a2 (14,633 m2, Harbor Point, 41.0452, -73.5440),
  bd4154f7 (8,572), "NV" f45b4c63 (8,137), 0f5f9793 (7,919, heap 1925), 6cedb71b (7,779); Bridgeport 4805e25a
  (14,840 m2, heap 1940, 41.1591, -73.2127), a01db777 (10,531, none, 41.1777, -73.1783), c14da852 (6,073).
- Sources tried that gave nothing: Wikipedia's search API (blocked), "List of tallest buildings in Stamford" and in
  Bridgeport (404: no such pages), the NRHP lists (no construction years), Wikidata (names and a few
  inception years; no heights).

## Models (14)

Plan, anchor and `replaces` = the footprint (simplified); numeric check from `towns_ct_build/check.py` on the
built meshes (`check_out.txt`): ratio = model silhouette / footprint polygon.

| model | years | top | cited? | plan ratio | notes |
|---|---|---|---|---|---|
| One Landmark Square | 1970-1973 | 89.9 m | 295 ft cited (Wikipedia) | 0.999 | podium, taper, bands estimated |
| Park Tower Stamford | 2007.4-2009.7 | 106.7 m | 350 ft cited | 1.000 | podium 17.5 m (6 floors, article) estimated |
| Atlantic Station | 2015-2017 | 96.0 m | 315 ft cited (footprint says 93 m) | 1.002 | set-back crown estimated |
| Fish Church | 1956-1958.2 | 79.2 m | tower 260 ft and nave 60 ft cited | 1.022 | WHICH part is the sanctuary and where the tower stands are guesses (LOW) |
| Old Town Hall | 1905-1907.2 | 41 m | none published | 1.024 | walls, mansard, clock tower estimated (LOW) |
| Basilica of St. John | 1866.5-1868.5 | 23.0 m | footprint height (ridge) | 1.023 | no tower/spire modelled |
| Bridgeport Center | 1984-1989.5 | 81.4 m | 248 ft red wing and 267 ft main roof cited | 1.032 | red/white split is a cut at the footprint's middle (LOW) |
| City Trust Apartments | 1927-1929.5 | 50.3 m | 165 ft cited | 1.010 | footprint found by article coordinates only; set-backs estimated |
| St. Augustine Cathedral | 1865.65-1868.2 | 55.0 m | 180.5 ft cited | 1.002 | tower end guessed (LOW) |
| Fairfield County Courthouse | 1886.5-1888.5 | 37 m | main roof = footprint 15.9 m; tower estimated | 1.007 | six-story tower per article |
| McLevy Hall | 1852-1854.5 | 14.6 m | ridge = footprint 9.7 m | 1.006 | portico end and cupola estimated (LOW) |
| Total Mortgage Arena | 1999.6-2001.78 | 17 m | opening date cited; 12.0 m = footprint | 1.002 | bowl roof estimated |
| Hartford HealthCare Amphitheater | 2018.6-2021.6 | 20.7 m | opening date cited; apex = footprint | 1.032 | tent is one pyramid |
| Palace and Majestic Theaters | 1921-1922.5 | 24 m | five stories (article), 4.5 m each estimated | 1.002 | |

All 14 pass the plan test (within 10 %); the cited tops are exact by construction (zmax in `check_out.txt`:
89.9, 106.7, 96.0, 79.2 (tower), 81.4, 50.3, 55.0). `cd viewer && npx tsc --noEmit` passes. Face counts 30-357.
Not done: the PSEG Bridgeport Harbor Station stack (no opened page gave a height; its Wikipedia titles 404), Perry
Memorial Arch (no page found), the Stamford Transportation Center and Marriott, Summer House (its 85 m footprint
and the article's 250 ft differ by 12 %).

## Possible errors in existing data

- `known_building_dates.ct.csv`: none checked here.
- Overture's Stamford footprint 74f16290 (Fish Church) is one L-shaped outline of 3,400 m2 with the sanctuary,
  tower and wings merged.
- McLevy Hall's footprint (aa06abd4) is 70 m from the article's coordinates; the Margaret Morton Government Center
  (9,776 m2) lies between: the match rests on the name.
- Assessor years for Stamford and Bridgeport's churches and cathedrals are rebuild years (2019, 1964), not building years.
