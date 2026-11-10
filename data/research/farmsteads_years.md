# What the USGS sheets of 1888-89 and 1897 say about building years

Evidence: `data/manual/farmsteads/farmsteads.geojson` (8,864 building marks read off the USGS
15-minute sheets; method and validation in the README beside it) against the built model
`data/interim/nyc_buildings.parquet`. Two builds of the model appear below and are named each
time: **build A** (2026-11-10, before 18:24: the model had not yet used the marks) and
**build B** (2026-11-10 18:24:54: 852 footprints already carry `evidence_by:topo1889 / topo1897`
from an earlier export of this file). Numbers come from `stats.json`,
`tools/standing_check.py` and `tools/districts.py` in `data/manual/farmsteads/`; re-run them
after a rebuild. Sheets: USGS Historical Topographic Map Collection, public domain
(https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/PDF/…).

## The short answer

1. **The sheets cannot re-date standing buildings one by one.** A mark is good to 15-25 m;
   in today's fabric a point that close to a footprint means nothing. In build A 5,506 of the
   8,864 marks had a footprint within 25 m that "could be" the building — and so had the same
   marks moved 150-190 m off their spots (5,398 on average). Only footprints with a
   *recorded* old year stand out (106 against 68 by chance).
2. **The model's current use of the marks is too wide.** `nyc_buildings.evidence_bounds`
   dates a footprint "standing by 1889 / 1897" for every `recorded` and `by_then` match and
   for a later-dated footprint that is the only one within 25 m and within 12 m of the mark.
   That last rule finds 285 footprints at the real marks and 225 at the moved ones: about
   four in five are coincidences. In build B 211 footprints with an assessor year after 1901
   — 82 of them after 1939 — are shown as standing in the 1880s or 1890s on that ground: a
   garage of 1980 in Maspeth (BIN 4556300) at 1885, a warehouse of 1950 in Jamaica (4213994)
   at 1883, an apartment house of 1940 by Grand Army Plaza (3029333) at 1886.
3. **What the sheets do show** is where buildings stood before the model has any: 8,864 in
   1889 / 1897, 3,215 of them on spots with no footprint within 25 m today, 1,358 with a year
   by which they were gone. Draw them.
4. **A short list comes out for research**: seven buildings that can be re-dated now, and
   about thirty footprints in open ground under a mark whose year is later than the map —
   several visibly wrong in the assessor's roll (Flatlands Reformed Church at 1931, Wave Hill
   at 1920, the Central Park Dairy with no year).

## 1. Is a footprint under a mark evidence?

For each mark: the best footprint within 25 m (area ≥ 45 m², not taller than 22 m, not over
1,500 m² unless the mark is a long building) that has no recorded year later than the survey.
Classes: `recorded` (LPC, a researched year or a non-placeholder assessor year, no later than
the survey), `by_then` (an estimate no later than the survey, or a "by 1901" placeholder),
`later_estimate` (an estimate after the survey: the "about 1920 / 1925 / 1930" placeholders,
the aerial bounds). The control is the same marks moved (150 E, 100 N), (120 W, 160 N),
(90 E, 170 S) metres. A footprint the model has dated from the marks is judged by its
assessor year, so the test does not feed on itself.

| Class | Build A: real | moved (three offsets) | Build B: real | moved | Ratio (B) |
|---|---|---|---|---|---|
| `recorded` | 106 | 67, 70, 67 | 99 | 53, 58, 52 | 1.82 |
| `by_then` | 662 | 599, 618, 603 | 754 | 657, 678, 667 | 1.13 |
| `later_estimate` | 4,738 | 4,792, 4,597, 4,781 | 4,796 | 4,874, 4,676, 4,857 | 1.00 |
| no footprint within 25 m | 3,358 | | 3,215 | | |

Build B, by distance to the footprint (real against the mean of the three moved copies):
`recorded` inside 17 / 6.3, to 6 m 17 / 9.3, 6-12 m 23 / 11.7, 12-25 m 42 / 27;
`by_then` inside 73 / 67, to 6 m 143 / 133, 6-12 m 160 / 141, 12-25 m 377 / 328;
`later_estimate` inside 1,020 / 951, to 6 m 1,424 / 1,550, 6-12 m 1,143 / 1,183, 12-25 m
1,211 / 1,119. By the number of footprints within 60 m of the mark: with 1-3, `recorded`
20 / 6.7, `by_then` 18 / 2.7, `later_estimate` 122 / 114; with 4-6, `recorded` 20 / 6,
`by_then` 12 / 6.3, `later_estimate` 202 / 144; with 13 or more — nine marks in ten —
`by_then` 682 / 628 and `later_estimate` 4,064 / 4,133. (In build A the open-ground `by_then`
figures were 7 / 1 and 4 / 5.7; part of the rise in B is the model's `neighbours` years, which
now lean on footprints dated from the marks.) By borough (build A) the `by_then` ratio was
1.37 on Staten Island, 1.07 in the Bronx and Queens, 1.01 in Brooklyn.

So: in a block that has since filled up the map cannot say which house is the old one.
Where the ground is still open (parks, institutions, the Staten Island woods) a footprint
under a mark is worth a look, not more.

## 2. Standing buildings under an 1890s mark, by borough and `year_src` (build B)

Best footprint within 25 m, as in the file (`standing_basis`, `standing_year_src`). Read the
two middle columns as the city's fabric (section 1), not as findings.

| Borough | Marks | `recorded` | `by_then` | `later_estimate` | no footprint within 25 m |
|---|---|---|---|---|---|
| Manhattan | 262 | 19 | 19 | 60 | 164 |
| Bronx | 1,633 | 21 | 164 | 723 | 725 |
| Brooklyn | 2,010 | 25 | 271 | 1,203 | 511 |
| Queens | 3,455 | 12 | 181 | 2,143 | 1,119 |
| Staten Island | 1,504 | 22 | 119 | 667 | 696 |
| **all** | **8,864** | **99** | **754** | **4,796** | **3,215** |

By the model's `year_src` of that footprint, all boroughs:

* `recorded` 99: `lpc` 91, `assessor` 6, `known` 2.
* `by_then` 754: `evidence_by:topo1897` 368 and `evidence_by:topo1889` 275 (the model's own
  use of the marks; their assessor years are "by 1901" placeholders — in build A these 643
  were `heap_by+spread` 624 and `heap_by+neighbours` 36, less a few), `evidence_by:law_old`
  76, `neighbours` 19, `assessor_flagged` 6, `on_map` 4, `lot_year` 2, `heap_by+spread` 2,
  `after_map` 1, `heap_by+neighbours` 1.
* `later_estimate` 4,796: `heap_about+spread` 2,820, `evidence_by:aerial1924` 587,
  `heap_about+neighbours` 440, `assessor_flagged` 192, `evidence_after:aerial1924` 112,
  `evidence_by:topo1897` 111 and `evidence_by:topo1889` 103 (**footprints the model now dates
  from the mark although the assessor's year is after the survey**), `evidence_by:aerial1951`
  93, `evidence_by:law_1929` 86, `evidence_after:aerial1951` 81, `lot_year` 62, `neighbours`
  56, `owner_reported` 19, `evidence_by:law_old` 13, `evidence_after:law_1929` 10, `after_map`
  5, `after_demolition` 4, `assessor` 1, `evidence_by:site` 1.

In build A (before any of this): `recorded` — lpc 91, assessor 15; `by_then` —
heap_by+spread 624, heap_by+neighbours 36, on_map 2; `later_estimate` — heap_about+spread
3,967, heap_about+neighbours 682, neighbours 87, others 2.

Of the 852 footprints carrying `evidence_by:topo…` in build B, 641 have an assessor year up
to 1901, 129 one of 1902-1939, 82 one of 1940 or later (classes K1 stores, D4 / D7 apartment
houses, A1-A5 houses, M1 churches).

`recorded` matches within 12 m: 59, among them Gracie Mansion (1 m), the Morris-Jumel Mansion
(8.5 m), the Friends Meeting House in Flushing (0 m), Fordham University Church (0 m), Christ
Church in Riverdale (0 m), Greyston (0.2 m), Litchfield Villa (7 m), St Andrew's Church in
Richmondtown (8.3 m), Grant's Tomb (0 m, first on the 1897 state), the Seaman's Retreat on
Staten Island (0 m). They need no new date; they show the marks sit where the buildings are.

## 3. Buildings to re-date

**Now** — `standing_basis = by_then`, `standing_strength = strong` (within 12 m of the mark,
at most six footprints within 60 m). Build A had 4 such rows against 2.7 by chance; build B
has 19 against 4, of which these seven do not lean on the marks themselves:

| Mark | BIN | Borough | Where | Assessor year | Standing by |
|---|---|---|---|---|---|
| `bk89_01492_07848` | 3336561 | Brooklyn | -73.97963, 40.57691 (Coney Island; class P9, 598 m²) | 1900 (placeholder) | 1889 |
| `ha97_03681_04660` | 2086275 | Bronx | -73.90975, 40.90714 (Riverdale; A3, 276 m²) | 1899 (placeholder) | 1897 |
| `si97_01717_09624` | 5145361 | Staten Island | -74.22605, 40.53730 (A1, 169 m²) | 1899 (placeholder) | 1897 |
| `si97_01720_09609` | 5169938 | Staten Island | -74.22594, 40.53764 (A1, 370 m²) | 1899 (placeholder) | 1897 |
| `ha97_03867_04502` | 2098642 | Bronx | -73.90390, 40.91094 (W6, 509 m²; the model has `lot_year` 1848) | 1848 | agrees |
| `ha97_03893_06229` | 2015290 | Bronx | -73.90318, 40.86944 (C7, 1,026 m²; `evidence_by:law_old`) | 1922 | 1897 |
| `ha97_04573_06405` | 2123952 | Bronx | -73.88175, 40.86521 (Q1, 1,915 m², Bronx Park) | 1897 | agrees |

The other twelve `strong` rows of build B are `neighbours` years equal to the survey year
(1889 / 1897: apparently the feedback named above) and one K4 building on Staten Island whose model year
is 1992 (BIN 5079802): leave them.

**To research** — a later-dated footprint with the mark within 6 m and at most three
footprints within 60 m: 32 rows in build A (38 in B), about 20 expected by chance, so roughly
a third are the mapped building. The identifications are mine, from where the point lies —
**not verified**; each needs its own source before it goes into `known_building_dates.csv`.

| Mark | BIN | Borough | lon, lat | Class, m² | Assessor year | Probably |
|---|---|---|---|---|---|---|
| `bk89_02884_05885` | 3339077 | Brooklyn | -73.93623, 40.62379 | M1, 302 | 1931 | Flatlands Dutch Reformed Church (Kings Highway at East 40th St), a church of the 1840s |
| `ha97_03600_05052` | 2117850 | Bronx | -73.91233, 40.89771 | Q1, 435 | 1920 | Wave Hill House, Riverdale (1840s) |
| `ha97_01639_10485` | 1083812 | Manhattan | -73.97395, 40.76811 | Q1, 898 | none | the Dairy, Central Park (about 1870) |
| `ha97_08025_09614`, `ha97_07975_09631` | 4610440, 4540373 | Queens | -73.7735, 40.7888 | Y1, 491 / 3,848 | none | Fort Totten buildings |
| `ha97_03296_09322` | 1088188 | Manhattan | -73.92195, 40.79576 | Q1, 220 | none | a building on Randalls / Wards Island |
| `si97_02722_08628` | 5077594 | Staten Island | -74.19470, 40.56113 | A1, 102 | 1940 | a house alone in the woods: a farmhouse candidate |
| `si97_07703_06343` | 3340027 | Brooklyn | -74.03929, 40.61629 | Q1, 298 | 1928 | a building in Fort Hamilton / Shore Road park |
| `ha89_04801_05466` | 2124011 | Bronx | -73.87828, 40.88894 | Z8, 649 | 1931 | a Woodlawn Cemetery building |
| `bk89_06732_01192` | 4439910 | Queens | -73.81588, 40.73533 | W5, 1,481 | 1907 | "Jefferson Hall" (the model's name): 1907 is after the survey — a replacement, or the map's building rebuilt |
| the rest | | | | E, K, D, F, G, O, U, I, T classes | 1925-2015 | warehouses, shops, apartment houses, utilities: replacements on the old site |

List them with `standing_basis == "later_estimate" and standing_dist_m <= 6 and
standing_n60 <= 3`; with `standing_n60 <= 6` there are 100 (about two thirds chance).

## 4. The old villages (build B)

Within 700 m of the village centre (centres are my estimates, good to a block or two:
`tools/districts.py`). "Marks" are separately drawn buildings read by the detector (recall
about 0.65, and nothing inside a black frontage); "model" is what `nyc_buildings.parquet` has
standing in that year, vanished and generated buildings included.

| District | Marks 1889 | Marks 1897 | of them in the built-up extent | Model: standing 1889 | 1897 | 1930 | Footprints today | with an estimated year after 1897 | Marks on a `recorded` footprint | on a `by_then` one | Gone by 1947-57 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Gravesend | 6 | 18 | 5 | 20 | 52 | 2,619 | 4,510 | 4,154 | 0 | 4 | 0 |
| Flatlands | 37 | 25 | 2 | 26 | 71 | 4,239 | 5,857 | 5,669 | 1 | 1 | 0 |
| New Utrecht | 5 | 29 | 5 | 58 | 143 | 3,503 | 4,747 | 4,002 | 0 | 6 | 0 |
| Flatbush | 28 | 10 | 5 | 77 | 125 | 1,473 | 1,910 | 1,216 | 1 | 2 | 0 |
| Bushwick | 4 | 5 | 1 | 433 | 878 | 2,262 | 2,907 | 1,519 | 0 | 0 | 1 |
| Newtown (Elmhurst) | 27 | 30 | 10 | 50 | 72 | 1,549 | 3,502 | 2,741 | 0 | 5 | 0 |
| Jamaica | 27 | 26 | 4 | 14 | 31 | 654 | 1,042 | 712 | 1 | 1 | 2 |
| Flushing | 21 | 14 | 5 | 15 | 38 | 344 | 1,301 | 546 | 1 | 1 | 0 |
| College Point | 11 | 12 | 1 | 26 | 99 | 1,989 | 3,803 | 3,026 | 0 | 0 | 0 |
| Richmondtown | no sheet | 20 | 2 | 25 | 30 | 76 | 703 | 394 | 1 | 2 | 2 |
| Tottenville | no sheet | 29 | 5 | 88 | 222 | 894 | 2,400 | 1,194 | 0 | 5 | 1 |
| Westchester Square | 32 | 24 | 11 | 63 | 132 | 1,275 | 1,943 | 1,356 | 1 | 9 | 2 |
| Williamsbridge | 41 | 12 | 12 | 63 | 130 | 1,554 | 2,865 | 2,091 | 0 | 12 | 3 |
| Kingsbridge | 29 | 20 | 13 | 51 | 153 | 869 | 1,428 | 880 | 0 | 5 | 3 |

Where the placeholders are clearly too late:

* **Flatlands, Jamaica, Flushing.** The 1888-89 survey alone draws more separate buildings
  (37, 27, 21 read; about half as many again are drawn, by the measured recall) than the model
  has standing in 1889 (26, 14, 15) — before counting the village streets the sheet draws as
  frontage. Jamaica and Flushing are the plainest cases: villages with built-up main streets
  on the sheet, 14 and 15 buildings in the model.
* **Gravesend.** The model has 20 buildings in 1889 and 52 in 1897; 4,154 of today's 4,510
  footprints carry an estimated year after 1897. The sheet (below) shows the four squares
  built along their fronts and, by eye, 15-20 separate houses around in 1889 and about twice
  that in 1897. The file has 20 of the separate ones.
* **Richmondtown.** 20 marks of 1897 read along Richmond Road and Arthur Kill Road, 17 more
  in the village centre drawn touching and not read; the model has 30 in 1897.
* **Newtown, Williamsbridge, Kingsbridge, Westchester Square.** 27-41 marks of 1889 against
  50-63 model buildings: the same order, and the villages proper are frontage on the sheet.
* **New Utrecht.** The church stands on 74°00′, the sheet edge: the west half is on the
  Staten Island sheet (1897 state only). 5 marks of 1889 east of the line, 29 in 1897.
* **Bushwick, Flatbush, College Point, Tottenville.** Inside or at the edge of the built-up
  extent, or already well stocked in the model; the marks add little.

In none of these does the map single out which standing house is old (section 1). What it
supports is the district-wide statement: these places had dozens of buildings on these roads
in 1889, and the marks give their positions.

### Gravesend on the sheets (looked at, 600 ppi, around -73.972, 40.596)

*1888-89 survey (print of 1889).* The four squares of the town plan lie either side of a
railroad running north-south through their middle, lettered PROSPECT PARK AND CONEY ISLAND
RAILROAD (today's McDonald Avenue). The fronts of the two northern squares and the inner
fronts of the southern ones are black bands (built frontage); the outer southern fronts are
thin lines (open). Separate marks: two on the road leaving the north-east corner, three or
four along the road east of the squares (Gravesend Neck Road), one west of them, two long
buildings on the lane running south-west, and a long building of about 100 m with two houses
against it on the Neck Road 800 m east. North-east, an oval race track with a long stand on
its west side. A second railroad runs 400 m to the west; tidal marsh and a creek begin 500 m
south-west, with "Gravesend Beach" lettered across them. After the shift today's Village Road,
Gravesend Neck Road and McDonald Avenue fall on the sheet's roads within about 10 m.

*1897 state (print of 1898).* All four squares are black-fronted; a row of six to eight houses
stands along the Neck Road just east of them, four more on the north-east road; new streets
north-west of the village carry about a dozen houses; the streets south of the squares are
lined with houses drawn touching (not read); the long building on the Neck Road has grown to
some 300 m.

In the file within 700 m: 20 points — 6 of the 1888-89 survey (4 of them again in 1897), 14
first on the 1897 state (5 of those on ground the first survey shows empty: built 1889-97).

## For the lead

* `nyc_buildings.evidence_bounds`: keep `recorded`; keep `by_then` only with
  `standing_strength == "strong"`; drop the `later_estimate` branch. With the file as it is
  that dates about 20 footprints from the marks instead of 852.
* `nyc_extras.farmsteads`: do not leave out the `by_then` marks (754): nine in ten of those
  footprints are not the mapped building, so the building of 1889 / 1897 is missing there.
  Leave out only `recorded` within 12 m and `by_then` + `strong`.
* The research list of section 3 is for `known_building_dates.csv`, one source each.

## Not checked

The identifications in section 3; town-level census figures; the district centres against a
gazetteer; the 1900 editions; the second-order feedback through `neighbours` years in build B
(not removed from the counts).
