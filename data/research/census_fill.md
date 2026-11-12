# Census fill: generated buildings where the census counts people the map has no building for

`pipeline/census_fill.py` -> `data/interim/gapfill/gapfill_census.parquet` (139,932 rows, EPSG:4326,
columns of `gapfill.parquet`; `evidence = census+ground`, every row `procedural`). Work files:
`data/interim/census_fill/` (`table_before.csv`, `model.csv`, `table_after.csv`, `holes_before_after.csv`,
`cand_*.npz`, `rows_*.npz`, `look/*.png`). No `.ok` file was written.

Order of use: `points` -> `assign` -> `table` -> `urban_area` -> `model_table` -> per place `cands` + `select`
(`run_county` for the towns of a county) -> `collect`; checks `check_table`, `check_years`, `check_overlap <pid>`,
`holes_check`, `look name year lon lat`.

## 1. The model (persons per building)

The map's count is every row alive at the census year with 30 m2 or more (standing, traced, vanished, generated;
`nyc_building_points` + `county_points_inner`, 2.93 million rows), by the borough's county outline or the
municipality's outline (`towns.parquet`), against the census (`population.csv` for boroughs,
`population_towns.csv` for 559 municipalities; log-linear between counts, none outside the series).

    persons per building (target) = max( floor(year), 6.5 * (persons per urban km2 / 12,000) ** 0.8 )
    floor(year) = 1.15 * household size of the year (US censuses: 5.8 in 1790, 5.3 in 1860, 4.76 in 1900, 4.11 in 1930,
                  3.33 in 1960), at most 1.2 * the place's own ratio today (2020 population / buildings today) scaled by
                  household size / 2.6
    needed buildings = population / target

* Calibration. Persons per urban km2 uses the terrain's city cover (region grid) of the year. The density term is
  a log-log fit to the places the map knows best, a complete traced atlas: Manhattan 1860 (38,000 per km2, 14.2
  persons per building observed; model 17), Manhattan 1900 (42,500 / 19.9; 19.5), Hoboken 1900 / 1930 (22,800 / 12.6,
  21,400 / 11.2; 11.4 and 10.3), Jersey City 1900 / 1920 (10,800 / 6.4, 13,100 / 6.7; 5.9, 7.0). At those anchors the
  map holds 93-110 % of the model's need, so nothing is added there. Villages (5-7) and the floor come from the
  household sizes; "today" bounds the floor in suburbs whose sheds and garages are counted as buildings.
* Trigger: the map holds less than 75 % of the need and the shortfall is over 40 buildings, at a census year
  1790-1960. Then rows are added up to 85 % of the need (never to 100 %), net of the fill's own rows still standing.
  Result: 682 place-years triggered (88 places); after the fill the places stand at about 1.15-1.2 times the target
  (Brooklyn 1860: 15.3 -> 8.3 against a target of 7.0).
* Weak points of the model, stated: the density term is fitted on six points; Brooklyn 1860 (a county figure against an
  atlas that covers the city only) and the Bronx 1910 (mixed tenements and houses) are the least certain deficits. No
  neighbourhood has a census series, so the rule sees places, not neighbourhoods.

## 2. Where

Lots come from today's street lines (Overture: residential, unclassified, living streets, tertiary, secondary,
primary; not service, motorway, trunk): both sides, front edge 6.5-9 m (local) to 10-12 m (primary) from the centre
line, depth 9-16 m, width 5-6.5 (row), 6.5-8 (tenement), 8-10 (semi-detached), 11-17 (detached), the type from today's
building density within 100 m and the median height of the buildings built by 1935 within 150 m (below 9 m frame,
to 13.5 m row house, above tenement: the Bay project's rule). Rejected: outside the place, not city ground in the
terrain at its start (first urban / suburban spell of the cell, detail grid in the city box, else region grid), on today's
water, parks, cemeteries, golf, recreation, rail yards (`data/manual/ports`), the sites of `data/manual/sites`, within a
road's carriageway (half width + 1 m by class), within 1 m of another candidate. A candidate dies if a row of the map
within 3 m stands from its ground year to 1961.

Selection per census year: candidates whose ground became city at least 2.5 years before the end of the decade, not
blocked by a row of the map alive within 3 m at the drawn start, with the map's rows within 60 m under 60 % of the
candidate lots within 60 m; ordered by 0.7 * that share + 0.8 * distance to the place's old centre (the densest 1 % of
candidates by map rows at the first census year with a real town): holes first, then thin ground, outward from the old
centre. Brooklyn 1860 as an example: the fill lies on ground the terrain calls city that the atlas of 1855 does not
cover, south and east of Fort Greene.

## 3. When

A row is drawn in the decade before the census year that asked for it (20 years for a place's first count), then its
start is re-dealt along a continuous rate (a tent over the decade, joined to the neighbouring decades' rates) so that no
year stands out; it never starts before its ground (+0.3 y) or at a time a row of the map stands within 3 m. It ends
2 hundredths of a year before the earliest row of the map within 3 m that starts later (89,347 rows; a replacement
after 1995 is not believed and counts as "estimated"), or, if the place's count falls below the need, a random open row
ends in that decade (6,515: `census_decline`), or the ground stops being city (152), or it ends spread over 1960-1995
(43,925: `estimated`).

## 4. Marking

`evidence = census+ground`; `end_basis` in `replaced_by_map`, `census_decline`, `ground_changed`, `estimated`;
`material` frame (2-3 storeys, 7.5-10.5 m) or brick (row house 2-4 storeys, tenement 4-6, from 1830 / 1860; before
1830 all are two-storey frame houses), `height_m` = storeys * 3.0 + 1.5 (frame) or * 3.3 + 1.0; `area` = borough code
"1".."5" or the county name. Ids are `cf` + 14 hex of the row's centre.

## 5. Checks (all on the file in `data/interim/gapfill/`)

Rows: Bronx 19,862, Brooklyn 15,800, Yonkers 12,407, Paterson 11,524, Newark 7,743, Queens 5,937, Passaic about 5,800,
East Orange about 5,800, Elizabeth 5,654, Staten Island 3,535, Mount Vernon about 4,000 ... 83 places, 139,932 rows in
all (per place: `data/interim/census_fill/row_places.parquet`). Manhattan was run and left out (see below).

Persons per building, before / after at the year of the largest deficit (target in brackets):
Brooklyn 1860 15.3 / 8.3 (7.0); Paterson 1910 15.6 / 6.9 (5.8), 1900 16.1 / 7.3; Newark 1880 10.7 / 6.8 (5.8), 1900
11.4 / 8.6 (6.4); Yonkers 1890 15.7 / 6.6 (5.6); Passaic 1910 20.3 / 7.6; East Orange 1920 15.7 / 5.9; Elizabeth 1910
11.5 / 6.4; Queens 1880 26.1 / 7.0 (1790-1870 stay at 17-39: farmland, see below); Bronx 1910 11.4 -> about 7.3.
Full table: `table_after.csv`.

Holes (holes.py's measure, fine grid = the five boroughs and the Hudson waterfront and Paterson's corner; 3 ha at
60 m), the map against map + fill, hectares: 1860 183 -> 116; 1880 292 -> 211; 1900 573 -> 383; 1920 542 -> 396;
1940 629 -> 526; 1960 913 -> 819; 1980 2,070 -> 1,916. By place 1900: Paterson 44 -> 0, Elizabeth 24 -> 7, Brooklyn
66 -> 47, Yonkers 30 -> 17; 1860 Brooklyn 145 -> 82. The Bronx's 152 ha of 1960 and Newark's 148 ha (the Central Ward
after its clearance), Staten Island's and Queens' holes are unchanged (no deficit there: they are real).

Overlap: recomputed from the written file against the map's rows (nyc_buildings + county_buildings geometry) for Paterson,
Newark, Staten Island, Yonkers, the Bronx, Brooklyn and Queens: 0 rows overlap a row of the map alive at the same
time (a 0.05-year tolerance; ends sit 0.02 years before the real start), 0 fill rows overlap one another (7 slab-seam
duplicates in Queens were dropped).

Years: starts per year peak at 6,774 in 1905 (the Bronx's decade 1900-1910 with Yonkers, Mount Vernon, Paterson), a hump
rising from about 1,000 a year in 1899 to 4,000 in 1902 and falling to 640 in 1911; the largest ratio of a year to its
neighbours (years above 300) is 1.6. Ends peak at 2,776 in 1922 (a broad plateau of 2,000 from 1917 to 1929, the real
rows taking the lots), ratio 1.7. Starts by decade: 1830s 2,600, 1840s 8,100, 1850s 12,500, 1860s 8,700, 1870s 16,700,
1880s 7,700, 1890s 10,500, 1900s 44,400, 1910s 8,000.

## 6. What the pictures show (`look/*.png`, 900-1000 m windows)

* Paterson 1900: 599 rows of the map, 4,472 fill rows in street-front rows on the real street grid, lots clear of
  roads and of the real mills; a few fill rows lie on cells the 25 m picture shows white (edge of the 58 m terrain
  cell); block interiors stay empty (lots are 9-16 m deep).
* Newark 1900: the same, along the grid south and west of the real downtown buildings; the hatched look in the south-west is
  rows of 5-6 m lots seen at this scale. No lot on the railway or river.
* Brooklyn 1860 (Fort Greene / Park Slope): the fill leaves the dense atlas rows alone and extends south and east
  over ground the terrain calls city. Where history says the south slope was largely open in 1860, the fill is only as
  good as the terrain's city ground.
* East Bronx 1920: 232 fill rows at the edges of the real blocks, none on the open ground; the real rows dominate.
* Staten Island south shore 1920: 82 rows, sparse (the 1880 fill remains and the island is no longer in deficit).
* Coney Island 1910: nothing: Brooklyn as a whole is not 25 % short in 1910 and the rule cannot see one
  neighbourhood. The empty resort stays empty.
* Brooklyn east (Williamsburg / Bushwick, 1860): the same, 96 fill rows only.

## 7. What is not filled, and why

* Manhattan: run (15,633 rows) and left out. 1790: 696 rows would only repeat decision 8's census-fitted town; 1960:
  14,937 rows come from the density law applied to a borough of 20-storey slabs (22.9 persons per building observed
  against 15.5 modelled): not a clear deficit. The rows are in `data/interim/census_fill/skipped/`.
* Places with a census count and ground that was not city: Queens 1790-1870 (6,000-45,000 people, 100-474 buildings,
  persons per building 60-137), the Bronx 1790-1860, Staten Island 1790-1870 and the outer rural towns stay thin:
  farmhouses on farmland are not placed here (the rule needs built-up ground; the colonial towns and farms of
  `early_nyc.csv` / `early_counties.csv` are the other stage's).
* Neighbourhood holes inside a place that is not in deficit (Coney Island, Bay Ridge, Inwood, Flushing's centre, the
  Rockaways): no sub-place census series exists. They need the traced atlases or a neighbourhood rule.
* Towns without a census series before their first count; the outer counties (only the seven inner counties and
  the boroughs were run); `hh` after 1960 (rows still open at 1960 end spread over 1960-1995, no post-1960
  deficit is computed).
* Interior of blocks (lots reach 16 m from the frontage), back buildings and tenement rear houses.
