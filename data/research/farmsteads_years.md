# What the USGS sheets of 1888-89 and 1897 say about building years

Evidence: `data/manual/farmsteads/farmsteads.geojson` (8,864 building marks read off the
USGS 15-minute sheets; method and validation in the README beside it) against the built model
`data/interim/nyc_buildings.parquet` as of 2026-11-10 (`year_src`, `start_year`). Numbers are
from `data/manual/farmsteads/stats.json`, `tools/standing_check.py` and `tools/districts.py`
there; re-run them after a rebuild. Sheets: USGS Historical Topographic Map Collection, public
domain (https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/PDF/…).

## The short answer

1. **The sheets cannot re-date standing buildings one by one.** A mark is good to 15-25 m;
   today a point that close to a footprint means nothing. 5,506 of the 8,864 marks have a
   footprint within 25 m that "could be" the building — and so do the same marks when moved
   150-190 m off their spots. Only footprints with a *recorded* old year stand out (106
   against 68 by chance).
2. **They do show where buildings stood** before the model has any: 8,864 buildings in
   1889 / 1897, 3,358 of them on ground with no footprint within 25 m today, 1,357 with a year
   by which they were gone. That is the use: draw them (see "For the lead").
3. **A short research list comes out of it**: 4 buildings to re-date now, and 32 footprints in
   open ground under a mark whose estimated year is later than the map — several of them
   visibly wrong (Flatlands Reformed Church at 1931, Wave Hill at 1920, the Central Park Dairy
   at 1952).

## 1. Is a footprint under a mark evidence?

For each mark: the best footprint within 25 m (area ≥ 45 m², not taller than 22 m, not over
1,500 m² unless the mark is a long building) that has no recorded year later than the survey.
Classes: `recorded` (LPC or a non-placeholder assessor year, no later than the survey),
`by_then` (an estimate no later than the survey, or a "by 1901" placeholder), `later_estimate`
(an estimate after the survey: the "about 1920 / 1925 / 1930" placeholders). The control is
the same marks moved (150 E, 100 N), (120 W, 160 N), (90 E, 170 S) metres.

| Class | Real | Moved (mean of three) | Ratio |
|---|---|---|---|
| `recorded` | 106 | 68 | 1.55 |
| `by_then` | 662 | 607 | 1.09 |
| `later_estimate` | 4,738 | 4,723 | 1.00 |

By distance (five sheets of seven, run before the two eastern sheets were added; the full
file is the same within a few per cent): `recorded` inside the footprint 17 against 6.7,
within 6 m 20 against 11.7; `by_then` inside 60 against 56, within 6 m 120 against 111;
`later_estimate` inside 953 against 889, within 6 m 1,343 against 1,462. By surroundings
(footprints within 60 m of the mark): with 1-3 footprints `recorded` 20 against 8, `by_then` 7
against 1, `later_estimate` 95 against 88; with 4-6 `later_estimate` 174 against 124; with 13
or more — nine marks in ten — every class is at chance (`by_then` 572 against 532,
`later_estimate` 3,899 against 3,942). By borough the `by_then` ratio is 1.37 on Staten
Island, 1.07 in the Bronx and Queens, 1.01 in Brooklyn.

So: in a block that has since filled up, the map cannot say which house is the old one. Where
the ground is still open (parks, institutions, the Staten Island woods) a footprint under a
mark is worth looking at.

## 2. Standing buildings under an 1890s mark, by borough and `year_src`

Best footprint within 25 m, as in the file (`standing_basis`, `standing_year_src`). "Chance"
for the whole column is in section 1: read the two right-hand columns as the city's fabric, not
as findings.

| Borough | Marks | `recorded`: lpc | assessor | `by_then`: heap_by+spread | heap_by+neighbours | on_map | `later_estimate`: heap_about+spread | heap_about+neighbours | neighbours | assessor (est.) | no footprint within 25 m |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Manhattan | 262 | 17 | 1 | 14 | 1 | 1 | 36 | 13 | 6 | – | 173 |
| Bronx | 1,633 | 19 | 5 | 133 | 14 | – | 529 | 159 | 10 | 1 | 763 |
| Brooklyn | 2,010 | 24 | 3 | 221 | 11 | 1 | 983 | 217 | 17 | – | 533 |
| Queens | 3,455 | 10 | 4 | 140 | 10 | – | 1,863 | 232 | 49 | – | 1,147 |
| Staten Island | 1,504 | 21 | 2 | 116 | – | – | 557 | 61 | 5 | – | 742 |
| **all** | **8,864** | **91** | **15** | **624** | **36** | **2** | **3,968** | **682** | **87** | **1** | **3,358** |

`recorded` matches within 12 m: 63, among them Gracie Mansion (1 m), the Morris-Jumel Mansion
(8.5 m), the Friends Meeting House in Flushing (0 m), Fordham University Church (0 m), Christ
Church in Riverdale (0 m), Greyston (0.2 m), Litchfield Villa (7 m), St Andrew's Church in
Richmondtown (8.3 m), Grant's Tomb (0 m, on the 1897 state only), the Seaman's Retreat on
Staten Island (0 m). They need no new date; they show the marks sit where the buildings are.

## 3. Buildings to re-date

**Now** (`standing_basis = by_then`, `standing_strength = strong`: within 12 m, at most six
footprints within 60 m; chance expects 2.7 such rows, there are 4):

| Mark | BIN | Borough | Where | Model year (`heap_by+spread`) | Standing by |
|---|---|---|---|---|---|
| `bk89_01492_07848` | 3336561 | Brooklyn | -73.97963, 40.57691 (Coney Island; class P9, 598 m²) | 1890 | 1889 |
| `ha97_03681_04660` | 2086275 | Bronx | -73.90975, 40.90714 (Riverdale; A3, 276 m²) | 1898 | 1897 |
| `si97_01717_09624` | 5145361 | Staten Island | -74.22605, 40.53730 (A1, 169 m²) | 1879 | 1897 |
| `si97_01720_09609` | 5169938 | Staten Island | -74.22594, 40.53764 (A1, 370 m²) | 1898 | 1897 |

These tighten a "by 1901" placeholder by a few years; they are not the buildings the
assessor has decades too late.

**To research** (`later_estimate`, the mark within 6 m of the footprint, at most three
footprints within 60 m: 32 rows; chance expects about 19, so roughly four in ten are the mapped
building). The identifications in the last column are mine, from where the point lies — **not
verified**; each needs its own source before it goes into `known_building_dates.csv`.

| Mark | BIN | Borough | lon, lat | Class, m² | Model year | Probably |
|---|---|---|---|---|---|---|
| `bk89_02884_05885` | 3339077 | Brooklyn | -73.93623, 40.62379 | M1, 302 | 1931 | Flatlands Dutch Reformed Church (Kings Highway at East 40th St); the church is of the 1840s |
| `ha97_03600_05052` | 2117850 | Bronx | -73.91233, 40.89771 | Q1, 435 | 1920 | Wave Hill House, Riverdale (1840s) |
| `ha97_01639_10485` | 1083812 | Manhattan | -73.97395, 40.76811 | Q1, 898 | 1952 | the Dairy, Central Park (about 1870) |
| `ha97_08025_09614`, `ha97_07975_09631` | 4610440, 4540373 | Queens | -73.7735, 40.7888 | Y1, 491 / 3,848 | 1911 / 1910 | Fort Totten buildings |
| `ha97_03296_09322` | 1088188 | Manhattan | -73.92195, 40.79576 | Q1, 220 | 2019 | a building on Randalls / Wards Island |
| `si97_02722_08628` | 5077594 | Staten Island | -74.19470, 40.56113 | A1, 102 | 1940 | a house alone in the woods: a farmhouse candidate |
| `ha89_04801_05466` | 2124011 | Bronx | -73.87828, 40.88894 | Z8, 649 | 1929 | Woodlawn Cemetery building |
| `bk89_01851_03758` | 3029333 | Brooklyn | -73.96868, 40.67429 | D4, 1,457 | 1938 | an apartment house: a replacement |
| the other 23 | | | | E, K, D, F, G, O, U classes | 1927-1988 | warehouses, shops, apartment houses, utilities: replacements on the old site |

List them all with: `standing_basis == "later_estimate" and standing_dist_m <= 6 and
standing_n60 <= 3`; with `standing_n60 <= 6` there are 90 (chance about 60 %).

## 4. The old villages

Within 700 m of the village centre (centres are my estimates, good to a block or two:
`tools/districts.py`). "Marks" are separately drawn buildings read by the detector (recall
about 0.65, and nothing inside a black frontage); "model" is what `nyc_buildings.parquet` has
standing in that year, vanished and generated buildings included.

| District | Marks 1889 | Marks 1897 | of them in the built-up extent | Model: standing 1889 | 1897 | 1930 | Footprints today | with an estimated year after 1897 | Marks on a `recorded` footprint | on a `by_then` one | Gone by 1947-57 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Gravesend | 6 | 18 | 5 | 23 | 57 | 2,339 | 4,510 | 4,096 | 0 | 4 | 0 |
| Flatlands | 37 | 25 | 2 | 26 | 75 | 4,084 | 5,857 | 5,653 | 1 | 1 | 0 |
| New Utrecht | 5 | 29 | 5 | 51 | 132 | 3,102 | 4,747 | 3,958 | 0 | 6 | 0 |
| Flatbush | 28 | 10 | 5 | 73 | 107 | 1,268 | 1,910 | 1,218 | 1 | 2 | 0 |
| Bushwick | 4 | 5 | 1 | 216 | 411 | 2,073 | 2,907 | 1,879 | 0 | 0 | 1 |
| Newtown (Elmhurst) | 27 | 30 | 10 | 46 | 68 | 1,307 | 3,502 | 2,693 | 0 | 5 | 0 |
| Jamaica | 27 | 26 | 4 | 12 | 28 | 541 | 1,042 | 678 | 1 | 1 | 2 |
| Flushing | 21 | 14 | 5 | 12 | 37 | 218 | 1,301 | 489 | 1 | 1 | 0 |
| College Point | 11 | 12 | 1 | 16 | 79 | 1,930 | 3,803 | 2,986 | 0 | 0 | 0 |
| Richmondtown | no sheet | 20 | 2 | 30 | 42 | 116 | 703 | 346 | 1 | 2 | 2 |
| Tottenville | no sheet | 29 | 5 | 99 | 271 | 937 | 2,400 | 1,105 | 0 | 5 | 1 |
| Westchester Square | 32 | 24 | 11 | 58 | 130 | 1,189 | 1,943 | 1,324 | 1 | 9 | 2 |
| Williamsbridge | 41 | 12 | 12 | 60 | 129 | 1,464 | 2,865 | 2,041 | 0 | 9 | 3 |
| Kingsbridge | 29 | 20 | 13 | 53 | 157 | 816 | 1,428 | 829 | 0 | 5 | 3 |

Where the placeholders are clearly too late, district by district:

* **Flatlands, Jamaica, Flushing, Newtown.** The 1888-89 survey alone draws more separate
  buildings (37, 27, 21, 27 read; about half as many again drawn) than the model has standing in
  1889 (26, 12, 12, 46), before counting the village streets drawn as frontage. In Jamaica
  and Flushing the model has 12 buildings in 1889 inside 700 m of the centre of a town of
  several thousand people.
* **Gravesend.** The model has 23 buildings in 1889 and 57 in 1897; 4,096 of today's 4,510
  footprints carry an estimated year after 1897. The sheet (below) shows the four squares
  built along their fronts and 15-20 houses around in 1889, twice that in 1897. The file has
  20 of the separate ones.
* **Williamsbridge, Kingsbridge, Westchester Square.** 41, 29 and 32 marks of 1889 against
  60, 53 and 58 model buildings; here the two are of the same order, and the villages
  proper are frontage on the sheet.
* **New Utrecht.** The church stands on 74°00′, the sheet edge: its west half is on the
  Staten Island sheet (1897 state only). 5 marks of 1889 east of the line, 29 in 1897.
* **Bushwick, Flatbush.** Already inside or at the edge of the built-up extent in 1889; the
  marks say little there.
* **Richmondtown, Tottenville.** One state (1897). Richmondtown: 20 marks along Richmond
  Road and Arthur Kill Road read, 17 more in the village centre drawn touching and not read;
  model 42 in 1897.

In none of these does the map single out which standing house is old (section 1). What it
supports is the district-wide statement: these places had dozens of buildings on these
streets in 1889, and the model should show buildings there.

### Gravesend on the sheets (looked at, 600 ppi, around -73.972, 40.596)

*1888-89 survey (print of 1889).* The four squares of the town plan lie either side of a
railroad running north-south through their middle, labelled PROSPECT PARK AND CONEY ISLAND
RAILROAD (today's McDonald Avenue); the fronts of the two northern squares and the inner
fronts of the southern ones are black bands (built frontage), the outer southern fronts thin
lines (open). Separate marks: two on the road leaving the north-east corner, three or four
along the road east of the squares (Gravesend Neck Road), one west of them, two long buildings
on the lane running south-west, and a 100 m long building with two houses against it on the
Neck Road 800 m east. North-east, an oval race track with a long stand on its west side. A
second railroad runs 400 m west; tidal marsh and a creek begin 500 m south-west ("Gravesend
Beach" is lettered across them). Today's Village Road, Gravesend Neck Road and McDonald Avenue
fall on the sheet's roads within about 10 m after the shift.

*1897 state (print of 1898).* All four squares are black-fronted; a row of six to eight houses
stands along the Neck Road just east of them, four more on the north-east road, new streets
north-west of the village carry a dozen houses, the streets south of the squares are lined
with houses drawn touching (not read), and the long building on the Neck Road has grown to
some 300 m.

In the file within 700 m: 20 points — 6 of the 1888-89 survey (4 of them again in 1897), 14
first on the 1897 state (5 of those on ground the first survey shows empty: built 1889-97).

## For the lead

* Do **not** re-date footprints from `standing_bin` wholesale. Use the four rows of
  section 3 (start no later than `first_year`, `estimated`), research the list below them.
* Draw the marks as buildings that stood (the README's "how to use" is in the final report
  and repeated here): every point except those with `standing_basis = recorded` is a
  building of 1889 / 1897 on the terrain, `estimated` in everything but its position and the
  fact that it stood.
* The districts table is the argument for giving these villages buildings before 1900 at
  all: the model's counts for 1889 are below what one survey draws as separate marks.

## Not checked

The identifications in section 3; town-level census figures; the district centres against a
gazetteer; the 1900 editions; whether a mark that coincides with a `by_then` footprint in a
dense block is that building (it cannot be, from this evidence).
