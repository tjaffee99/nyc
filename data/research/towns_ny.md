# West Point and Poughkeepsie: dates and landmarks (towns round, 2026-11-11)

Files: `data/tables/known_building_dates.hudson_towns.csv` (49 rows), `viewer/src/landmarks/ny-towns.ts` (export `NY_TOWNS`, 18 models).
Scripts (in `data/research/towns_ny_build/`): `fetch.sh` (Wikipedia raw wikitext, 7 s apart, cached in `data/interim/towns_ny_raw/wp/`),
`wd.py` (Wikidata SPARQL by box), `osm_ways.py` (OpenStreetMap map API, `data/interim/towns_ny_raw/osm`), `fp.py` (footprints by box),
`rows.py` + `build_csv.py` (the table, with the point-in-polygon test), `rings.py` (footprint -> ring), `dumpmesh.mjs` + `check.py` (numeric check, output `check_out.txt`).
Footprints: `data/interim/counties/ny_orange.parquet` (West Point = town of Highlands; Highland Falls) and `ny_dutchess.parquet` (Overture 2026-10-21.0).

## Dates

Every year is from a page opened in this session (Wikipedia raw wikitext; URL in the row). Row ids `nyht_*`. 49 rows: **West Point / Highland Falls 12**,
**Poughkeepsie 37** (Vassar 12, downtown 13, Marist 12). All 49 points are `representative_point()` of the footprint, 6 decimals; point-in-polygon against
the parquet: **49 of 49 inside**; no footprint is dated twice (also against `known_building_dates.ny_hudson.csv`, which already dates 21 West Point and 7 Vassar footprints).
Rows marked `estimate` (9): Nininger Hall (two dates in one article), Old Cadet Chapel (moved 1910/1911), Johnson Stadium (coordinate 40 m off), Ferry House, Rombout House (about 1854),
Donnelly Hall (enlarged since 1962), Marist chapel (span 1947-57).
Other notes: Overture's "Poughkeepsie" (1,216 m2, height 0.1) is taken as the station (article coordinate 50 m away; the only footprint of the size); the McCann Recreation
Center row: the article puts McCann Arena 100 m north of the footprint named for it.

Not found (Wikipedia pages missing or rate-limited, usma.edu 403): **Eisenhower Hall (9,485 m2)**, Lincoln Hall, Keller hospital, Olmsted Hall (museum), the Visitors Center, Skinner Hall of Music
(Wikidata gives 1931-32), Loeb Art Center, Hudson-side Vassar Brothers hospital buildings, Poughkeepsie City Hall of 1831 (footprint uncertain), Journal Building (1941, footprint uncertain),
Niagara Engine House, Innis Dye Works, Savings Bank (1912), First Baptist Church (footprints 35-45 m from the article coordinates, not written). Largest still undated West Point footprints:
Eisenhower Hall 9,485; CEAC 8,622; unnamed 8,492 (by the Mint); Foley Indoor Practice Center 8,235; Elementary School 6,852; Commissary 6,282; Exchange 6,203.
Poughkeepsie: ACME Bearing Factory 19,614; two unnamed 10.8k; Walker Field House 5,861; Station parking 5,210.

## Models (all `built`/`end` from the cited year; heights as stated)

| id | years | faces | cited | estimated |
|---|---|---|---|---|
| taylor_hall_west_point | 1908-1910 | 166 | 180 ft (54.86 m) tower, 1910, CGF | tower position/stages, eave 10.7 m (footprint roof 13.7), start. Brief said 160 ft: the article opened says 180 ft |
| thayer_hall_west_point | 1907.5-1911 | 268 | riding hall 1909 (list: 1911), converted 1958 | all heights (wall 16, ridge 22.5), piers. LOW |
| pershing_barracks_west_point | 1891-1895 | 138 | West Academic Bldg, Hunt, 4 years, 1895 | wall/roof split; top 14.7 = footprint |
| cullum_hall_west_point | 1894-1898 | 174 | begun 1894, completed 1898, marble | podium, eave, 6-column front; top 12.9 = footprint |
| thayer_hotel_west_point | 1925-1926.4 | 282 | opened 27 May 1926, 5 floors, Gothic | storey height, roof, no tower. LOW |
| battle_monument_west_point | 1895-1897.41 | 262 | shaft 46 ft (14.02 m) x 5 ft, unveiled 30 May 1897; coordinate | plinth 3.4 m, balls, Fame; overall 22 m. start |
| old_cadet_chapel_west_point | 1910-1910.9 | 134 | built 1836, moved 1910, Greek Revival | portico/end, eave; top 8.0 = footprint |
| vassar_chapel | 1902.5-1904.5 | 93 | built 1904, Norman, granite | single ridge, no tower/apse; top 11.9 = footprint. LOW |
| thompson_library_vassar | 1903.5-1905.5 | 202 | completed 1905, three wings round a central tower, battlements, pinnacles | tower 37 m and its position (plan hub), wing 8.9 = footprint. LOW |
| rockefeller_hall_vassar | 1895.5-1897.9 | 104 | built 1897 (Wikidata 19 Nov 1897) | wall/roof; top 10.8 = footprint. LOW |
| raymond / lathrop / davison_house_vassar | 1895.5-1897.3 / 1899.5-1901.3 / 1900.5-1902.3 | 84 / 66 / 84 | 1897 / 1901 / 1902, five floors | 3.4 m floors (17 m), roof (to 20.5 m). LOW |
| poughkeepsie_station | 1916.5-1918 | 120 | built 1918, Warren and Wetmore, 4 storeys into the rock | block height 16.4 m. LOW |
| bardavon_poughkeepsie | 1868-1869.5 | 192 | built 1869, J. A. Wood | cornice, split; top 19.4 = footprint. LOW |
| dutchess_county_courthouse | 1902-1903.95 | 48 | 1903, four storeys, red brick | storey 4.4 m, cornice 19.5 m. LOW |
| poughkeepsie_post_office | 1937.78-1939.5 | 206 | cornerstone 13 Oct 1937, two years, 63,000 sq ft = 3 floors x 1,880 m2, cupola | eave 10.8, hip, cupola to 20.6 m. LOW |
| luckey_platt_poughkeepsie | 1921.5-1923.5 | 92 | opened 1923, five storeys | cornice band; top 26 = footprint |

Footprint ids (Overture, first 8): Taylor 01f229a7, Thayer Hall bc16b66a, Pershing 6ed3648d, Cullum 9961f828, Thayer Hotel 6c36759d, Old Cadet Chapel 01bd39d8, Vassar Chapel 6f97eb26,
Thompson b63d7c9b, Rockefeller 16301305, Raymond b604d28a, Lathrop 82fd2029, Davison 069b8bab, station 0559131f, Bardavon bb649847, Court House 4643fb5d, Post Office e32aa3d7, Luckey Platt 350fcd54.
Anchor = footprint lon/lat, ring simplified 0.25 m (`rings.py`). Battle Monument: anchor is the article's coordinate (41 23 40.93 N, 73 57 24.66 W); no footprint.

## Numeric check (`check_out.txt`; plan = union of the model's triangles vs the replaced footprint; top = highest vertex)

Plan/footprint 1.004-1.059 for all 17 models with a footprint (largest: Cullum 1.059 from the cornice overhang; Davison 1.053); outside the footprint at most 352 m2 (Thayer Hall, a 235 m
long ridge on a notched ring), mostly 0-60 m2. Tops: Taylor 54.9 (cited 54.86, 0.1 %); Battle Monument shaft 14.02 cited, overall 22.2 estimated; Pershing 14.7, Cullum 12.9, Old Cadet
Chapel 8.0, Vassar Chapel 11.9, Rockefeller 10.8, Bardavon 19.4, Luckey Platt 26.0 equal the footprint heights; the rest are estimates (Thayer Hall 22.5, Thayer Hotel 23.4,
Thompson tower 37.2, dorms 20.5, station 16.4, Court House 19.5, Post Office 20.6). `npx tsc --noEmit` passes.

## Doubts about existing data

- `known_building_dates.ny_hudson.csv` has Thayer Hall at 1911 (the hall list) while the grounds article's narrative says the riding hall was completed in 1909; Lee and Sherman Barracks 1962 are consistent.
- Overture heights of 0.1 m (Post Office, station) are "no value", not heights.
- The brief's 160 ft for Taylor Hall's tower: the opened page says 180 ft.
