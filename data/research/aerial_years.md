# What the 1924 and 1951 aerial photographs say about the placeholder years

Source of every number here: `data/manual/aerial/presence.parquet` (method, terms and validation in
`data/manual/aerial/README.md`), joined to `data/interim/nyc_buildings.parquet` as it stood on 2026-11-10.
"Placeholder-year buildings" are the footprints whose `year_src` starts with `heap` (the assessor's rounded
years, which the pipeline spreads over a range and marks `estimated`).

How to read the tables. For every footprint the photograph gives a probability that a building stood on the
outline. **stood** = share with p >= 0.8, **open** = share with p <= 0.2; the rest is unclear. Against 220
hand-checked footprints a "stood" call was right in 94 % (1924) and 96 % (1951) of cases and an "open" call in
92 % and 83 %, but each call finds only part of its side (63 % of the buildings and 71 % of the open
ground in 1924; 59 % and 56 % in 1951), and how much it finds differs a great deal between
boroughs: detached houses under trees are found far less often than Brooklyn rows.

**est. standing** therefore reads each group between two reference groups of the same borough's own
placeholder-year stock: the "by 1899 / 1900 / 1901" buildings, which all stood in both photographs, and
the "1955 and later" ones (for 1951: "1960 and later"), which did not yet. With a, e = the stood and open
shares of the first group and b, c = those of the second, it is the mean of (stood - b) / (a - b) and
(c - open) / (c - e), cut to 0-100 %. The reference shares (a / e / b / c, in %):

- 1924: Brooklyn 67 / 4 / 12 / 66; Queens 38 / 13 / 8 / 68; Bronx 47 / 10 / 8 / 61; Staten Island 19 / 25 / 2 / 83; Manhattan 80 / 3 / 7 / 71
- 1951: Brooklyn 61 / 4 / 17 / 51; Queens 45 / 8 / 18 / 42; Bronx 53 / 5 / 18 / 35; Staten Island 22 / 20 / 4 / 74; Manhattan 69 / 4 / 13 / 54

It is an estimate, good to about +-10 points (more on Staten Island, where a is only a fifth). The late
reference group includes outlines on which an earlier building stood, so the estimate is, if anything, low.
A building "standing" in a photograph means a building stood on today's
outline - in districts that were already built up it may have been an earlier building on the same lot.

## 1. The placeholder years, by borough

Share of the buildings with each placeholder year that already stood in **1924**: **est. standing** (stood % /
open %; number of buildings with a photograph).

| placeholder | Brooklyn | Queens | Bronx | Staten Island | Manhattan |
|---|---|---|---|---|---|
| 1899 | **100 %** (68 / 4; 16,176) | **92 %** (37 / 20; 315) | **98 %** (45 / 10; 1,510) | **100 %** (20 / 23; 2,695) | **97 %** (76 / 3; 655) |
| 1900 | **100 %** (76 / 3; 1,558) | – | – | – | **100 %** (82 / 3; 3,474) |
| 1901 | **98 %** (65 / 4; 13,031) | **100 %** (38 / 13; 4,813) | **100 %** (47 / 10; 3,763) | **96 %** (18 / 27; 2,241) | **97 %** (76 / 3; 849) |
| 1905 | **93 %** (61 / 5; 4,829) | **100 %** (39 / 13; 890) | **87 %** (44 / 19; 704) | **100 %** (20 / 21; 780) | – |
| 1910 | **88 %** (57 / 7; 24,324) | **100 %** (38 / 14; 12,685) | **83 %** (39 / 18; 4,454) | **100 %** (22 / 25; 2,489) | **100 %** (80 / 2; 5,024) |
| 1915 | **85 %** (55 / 9; 6,797) | **92 %** (35 / 18; 7,752) | **69 %** (35 / 26; 2,280) | **94 %** (17 / 27; 2,471) | **100 %** (79 / 2; 539) |
| 1920 | **64 %** (42 / 20; 40,587) | **57 %** (24 / 35; 64,712) | **44 %** (22 / 35; 10,001) | **76 %** (15 / 39; 7,316) | **100 %** (81 / 2; 3,479) |
| 1925 | **47 %** (33 / 31; 41,565) | **29 %** (16 / 51; 49,811) | **35 %** (20 / 41; 8,856) | **64 %** (12 / 44; 5,436) | **92 %** (74 / 7; 868) |
| 1930 | **45 %** (33 / 34; 39,465) | **27 %** (16 / 53; 56,084) | **28 %** (17 / 44; 7,898) | **53 %** (10 / 50; 5,459) | **94 %** (72 / 4; 1,191) |
| 1931 | **86 %** (58 / 11; 20,018) | **100 %** (44 / 19; 9,490) | **89 %** (45 / 19; 3,581) | **100 %** (31 / 24; 2,593) | – |
| 1935 | **22 %** (21 / 49; 8,114) | **1 %** (9 / 67; 23,079) | **2 %** (9 / 60; 3,581) | **46 %** (9 / 55; 2,741) | – |
| 1940 | **1 %** (12 / 64; 9,323) | **0 %** (6 / 76; 33,307) | **2 %** (9 / 60; 4,404) | **34 %** (7 / 61; 2,567) | **90 %** (70 / 8; 474) |
| 1945 | **0 %** (8 / 64; 4,183) | **0 %** (3 / 85; 24,840) | **0 %** (7 / 62; 1,939) | **32 %** (7 / 62; 2,192) | – |
| 1950 | **6 %** (13 / 61; 6,503) | **0 %** (4 / 81; 43,862) | **0 %** (6 / 64; 5,641) | **12 %** (3 / 74; 4,918) | **92 %** (71 / 5; 415) |
| 1955 | **0 %** (7 / 74; 5,535) | **0 %** (5 / 78; 16,588) | **0 %** (7 / 66; 3,709) | **11 %** (3 / 75; 5,325) | – |
| 1960 | **0 %** (8 / 72; 11,239) | **0 %** (8 / 68; 17,188) | **0 %** (7 / 61; 4,704) | **8 %** (3 / 76; 6,462) | – |
| 1965 | **0 %** (11 / 67; 4,179) | **9 %** (11 / 63; 6,798) | **3 %** (8 / 58; 2,451) | **0 %** (2 / 82; 6,802) | – |
| 1970 | **15 %** (17 / 53; 2,493) | **28 %** (15 / 50; 4,337) | **13 %** (11 / 52; 1,553) | **0 %** (1 / 87; 8,943) | – |
| 1975 | **28 %** (26 / 47; 958) | **26 %** (15 / 53; 2,263) | **12 %** (13 / 55; 501) | **0 %** (2 / 86; 6,144) | – |
| 1980 | **57 %** (36 / 24; 584) | **26 %** (15 / 52; 935) | – | **0 %** (1 / 87; 4,440) | – |

The same for **1951**:

| placeholder | Brooklyn | Queens | Bronx | Staten Island | Manhattan |
|---|---|---|---|---|---|
| 1899 | **98 %** (59 / 4; 16,433) | **100 %** (47 / 10; 323) | **98 %** (53 / 5; 1,529) | **100 %** (23 / 17; 2,732) | **99 %** (66 / 2; 668) |
| 1900 | **100 %** (67 / 3; 1,568) | – | – | – | **98 %** (68 / 5; 3,549) |
| 1901 | **100 %** (62 / 4; 13,350) | **100 %** (45 / 8; 4,875) | **100 %** (54 / 5; 3,844) | **96 %** (22 / 22; 2,286) | **100 %** (75 / 2; 877) |
| 1905 | **97 %** (59 / 4; 4,986) | **98 %** (44 / 8; 825) | **80 %** (49 / 13; 727) | **100 %** (23 / 19; 803) | – |
| 1910 | **97 %** (59 / 4; 24,836) | **100 %** (44 / 7; 12,536) | **93 %** (49 / 6; 4,549) | **100 %** (26 / 15; 2,535) | **100 %** (69 / 3; 5,153) |
| 1915 | **92 %** (55 / 5; 6,956) | **96 %** (43 / 8; 7,707) | **96 %** (51 / 5; 2,328) | **99 %** (22 / 19; 2,540) | **100 %** (76 / 3; 563) |
| 1920 | **91 %** (55 / 6; 41,371) | **88 %** (40 / 9; 64,462) | **86 %** (46 / 7; 10,193) | **100 %** (24 / 18; 7,430) | **100 %** (76 / 2; 3,543) |
| 1925 | **87 %** (52 / 7; 42,187) | **86 %** (39 / 9; 50,125) | **84 %** (46 / 8; 9,014) | **100 %** (23 / 18; 5,514) | **100 %** (80 / 3; 893) |
| 1930 | **93 %** (56 / 6; 40,131) | **88 %** (40 / 10; 55,470) | **85 %** (46 / 7; 8,039) | **100 %** (23 / 18; 5,502) | **100 %** (79 / 3; 1,209) |
| 1931 | **100 %** (70 / 3; 20,321) | **100 %** (62 / 5; 9,592) | **100 %** (65 / 5; 3,691) | **100 %** (41 / 19; 2,622) | – |
| 1935 | **88 %** (53 / 6; 8,193) | **84 %** (38 / 10; 23,263) | **77 %** (43 / 10; 3,674) | **100 %** (22 / 19; 2,790) | – |
| 1940 | **85 %** (52 / 8; 9,449) | **85 %** (39 / 11; 33,306) | **75 %** (42 / 10; 4,462) | **82 %** (18 / 26; 2,609) | **100 %** (75 / 4; 499) |
| 1945 | **74 %** (45 / 11; 4,204) | **66 %** (33 / 16; 25,222) | **27 %** (24 / 24; 1,953) | **67 %** (14 / 32; 2,209) | – |
| 1950 | **54 %** (37 / 21; 6,567) | **34 %** (24 / 27; 44,245) | **16 %** (22 / 29; 5,728) | **50 %** (11 / 42; 4,990) | **98 %** (71 / 9; 434) |
| 1955 | **0 %** (14 / 55; 5,654) | **8 %** (18 / 37; 16,738) | **7 %** (19 / 32; 3,760) | **28 %** (8 / 55; 5,352) | – |
| 1960 | **0 %** (14 / 56; 11,461) | **0 %** (16 / 44; 17,098) | **0 %** (17 / 35; 4,830) | **16 %** (6 / 63; 6,347) | – |
| 1965 | **0 %** (15 / 52; 4,260) | **0 %** (18 / 44; 6,943) | **12 %** (20 / 30; 2,503) | **3 %** (4 / 71; 6,534) | – |
| 1970 | **10 %** (21 / 46; 2,564) | **20 %** (23 / 35; 4,376) | **1 %** (19 / 35; 1,588) | **0 %** (3 / 79; 8,707) | – |
| 1975 | **32 %** (29 / 34; 973) | **14 %** (23 / 40; 2,246) | **0 %** (20 / 40; 509) | **0 %** (3 / 77; 6,164) | – |
| 1980 | **52 %** (37 / 23; 588) | **15 %** (24 / 39; 947) | – | **0 %** (3 / 80; 4,531) | – |

What this says:

- **The placeholders are in the right order but run late.** Of Brooklyn's "1925" and "1930" buildings
  nearly half already stood in 1924; in Queens and the Bronx between a quarter and a third; of "1935" a fifth
  in Brooklyn and next to none elsewhere; "1940" and later came after the photograph.
- **"1931" is not a year at all.** In every borough the "1931" buildings are as old as the "1905-1915" ones
  (Brooklyn: 58 % plainly standing in 1924 and 11 % plainly open, against 33 % / 34 % for "1930"). It should be
  read as "by 1931" - a bound like 1899 / 1901 - not as "about 1931".
- **"1920" is not "by 1920"**: about two thirds of Brooklyn's "1920" buildings stood in 1924, somewhat over
  half of Queens' and under half of the Bronx's; the rest came after the photograph.
- **"1905", "1910", "1915" hold** in Brooklyn and Queens (85-100 %); in the Bronx about three in ten of "1915"
  came after 1924.
- **By 1951 nearly everything up to "1940" stood** (75-100 %). **"1945" and "1950" straddle the photograph**:
  of "1945" about seven in ten stood in Brooklyn and Queens and a quarter in the Bronx; of "1950" about half
  in Brooklyn, a third in Queens, a sixth in the Bronx. "1955" and later came after it.
- The late placeholders in old districts ("1970", "1975", "1980" in Brooklyn and Queens: 15-57 % "standing" in
  1924) are buildings on lots that were built on before: an earlier building, or an old one given a new year.
- Staten Island's column is the weakest: the classifier recognises only a fifth of its certainly old
  buildings, so its estimates rest on a narrow scale (read them to +-25 points).
- Manhattan: nearly everything stood in both photographs; they cannot order its placeholder years
  (a building stood on almost every outline, often not today's).

## 2. Boroughs: the pipeline's dates against the photographs

| borough | placeholder-year buildings | pipeline: standing by 1924 | photo 1924: est. standing (stood / open) | dated after 1924 but standing in the photo | dated by 1924 but open ground in the photo | pipeline: standing by 1951 | photo 1951: est. standing (stood / open) | dated after 1951 but standing | dated by 1951 but open |
|---|---|---|---|---|---|---|---|---|---|
| Brooklyn | 221,742 | 47 % | **60 %** (43 / 26) | 35,200 (31 % of those dated later) | 11,359 (11 % of those dated earlier) | 88 % | **86 %** (54 / 10) | 4,523 (17 % of those dated later) | 8,754 (4 % of those dated earlier) |
| Queens | 291,987 | 28 % | **28 %** (17 / 53) | 24,587 (12 % of those dated later) | 23,581 (29 % of those dated earlier) | 83 % | **75 %** (37 / 15) | 9,081 (19 % of those dated later) | 24,514 (10 % of those dated earlier) |
| Bronx | 64,808 | 36 % | **36 %** (21 / 42) | 5,808 (14 % of those dated later) | 5,514 (24 % of those dated earlier) | 79 % | **67 %** (41 / 14) | 2,586 (19 % of those dated later) | 4,441 (9 % of those dated earlier) |
| Staten Island | 73,438 | 23 % | **37 %** (9 / 62) | 2,980 (5 % of those dated later) | 4,667 (28 % of those dated earlier) | 48 % | **54 %** (14 / 46) | 1,649 (5 % of those dated later) | 7,059 (20 % of those dated earlier) |
| Manhattan | 16,386 | 86 % | **100 %** (80 / 3) | 1,582 (73 % of those dated later) | 339 (2 % of those dated earlier) | 100 % | **100 %** (72 / 3) | 17 (57 % of those dated later) | 517 (3 % of those dated earlier) |
| all | 668,361 | 36 % | **41 %** (27 / 43) | 70,157 (17 % of those dated later) | 45,460 (19 % of those dated earlier) | 81 % | **73 %** (42 / 16) | 17,856 (14 % of those dated later) | 45,285 (8 % of those dated earlier) |

In Brooklyn the pipeline has 47 % of the placeholder-year buildings standing by 1924; the photograph puts
it near 60 %. In Queens and the Bronx the totals agree, but one building in eight dated after 1924 plainly
stands in the photograph and a quarter of those dated before it plainly stand on open ground: the totals are
right and the order inside the districts is not. Staten Island may have more standing than the pipeline says
(weak evidence). For 1951 the pipeline has more standing than the photograph in Queens and the Bronx (83 %
against about 75 %, 79 % against about 67 %): the "1945" and "1950" placeholders spread backwards.

## 3. Districts

600 m around the label of each place in `data/tables/places.csv` (the label is the old village or the
neighbourhood centre, so the window is a sample of the district, not all of it).

### Gravesend

Around the village centre (-73.9737, 40.5953): 2,553 placeholder-year buildings.
1924: 2,501 with a photograph: 21 % standing, 35 % open ground, 44 % unclear. 1951: 2,553 with a photograph: 51 % standing, 9 % open ground, 41 % unclear. The pipeline has 27 % of them standing by 1924 and
89 % by 1951; the photographs give about 34 % and 83 %.

| placeholder | buildings | stood 1924 | open 1924 | est. standing 1924 | pipeline: by 1924 |
|---|---|---|---|---|---|
| 1920 | 280 | 25 % | 30 % | 41 % | 100 % |
| 1925 | 602 | 27 % | 30 % | 43 % | 43 % |
| 1930 | 541 | 12 % | 44 % | 18 % | 0 % |
| 1931 | 360 | 31 % | 18 % | 57 % | 0 % |
| 1935 | 92 | 12 % | 41 % | 20 % | 0 % |
| 1940 | 114 | 11 % | 49 % | 12 % | 0 % |
| 1950 | 101 | 8 % | 51 % | 8 % | 0 % |
| 1960 | 133 | 11 % | 37 % | 22 % | 0 % |

The totals are not far apart (27 % against about a third by 1924); what is wrong is *which* buildings. The
pipeline has every "1920" building standing by 1924 - the photograph shows about two in five - and none of the
"1930", "1931" and "1935" ones, of which about 18 %, 57 % and 20 % stood. The old village's houses carry
"1931" and "1930" like the new streets around them and so appear in the 1930s, which is what the owner saw:
351 buildings dated after 1924 plainly stand in the 1924 photograph, and 197 dated before it plainly stand on
open ground.

### The districts the brief named, and their like

| district | borough | placeholder-year buildings | pipeline: by 1924 | photo 1924: est. standing (stood / open) | dated later, standing 1924 | dated earlier, open 1924 | pipeline: by 1951 | photo 1951: est. standing (stood / open) | dated later, standing 1951 | dated earlier, open 1951 |
|---|---|---|---|---|---|---|---|---|---|---|
| Gravesend | Brooklyn | 2,554 | 27 % | **34 %** (21 / 35) | 351 | 197 | 89 % | **83 %** (51 / 9) | 59 | 133 |
| Flatlands | Brooklyn | 2,795 | 48 % | **47 %** (31 / 29) | 326 | 238 | 96 % | **93 %** (55 / 5) | 41 | 123 |
| New Utrecht | Brooklyn | 2,225 | 42 % | **77 %** (48 / 10) | 526 | 58 | 91 % | **96 %** (58 / 4) | 61 | 75 |
| Jamaica | Queens | 434 | 42 % | **100 %** (55 / 4) | 152 | 7 | 96 % | **100 %** (70 / 1) | 14 | 6 |
| Flushing | Queens | 327 | 20 % | **100 %** (57 / 7) | 142 | 4 | 72 % | **100 %** (52 / 6) | 38 | 9 |
| Canarsie | Brooklyn | 2,242 | 31 % | **42 %** (25 / 29) | 344 | 122 | 68 % | **60 %** (40 / 19) | 123 | 100 |
| Sheepshead Bay | Brooklyn | 1,048 | 31 % | **22 %** (16 / 43) | 68 | 76 | 89 % | **58 %** (33 / 13) | 17 | 107 |
| Coney Island | Brooklyn | 255 | 20 % | **86 %** (56 / 9) | 105 | 2 | 82 % | **99 %** (62 / 6) | 23 | 5 |
| Flatbush | Brooklyn | 881 | 43 % | **96 %** (62 / 4) | 314 | 10 | 99 % | **100 %** (71 / 3) | 6 | 28 |
| New Lots | Brooklyn | 1,736 | 43 % | **60 %** (40 / 23) | 277 | 66 | 85 % | **89 %** (54 / 7) | 50 | 41 |
| Elmhurst | Queens | 1,657 | 29 % | **94 %** (35 / 15) | 360 | 53 | 76 % | **99 %** (44 / 7) | 138 | 83 |
| College Point | Queens | 760 | 28 % | **22 %** (10 / 47) | 48 | 60 | 59 % | **31 %** (24 / 28) | 36 | 83 |
| Whitestone | Queens | 1,428 | 23 % | **52 %** (20 / 32) | 197 | 51 | 79 % | **60 %** (29 / 15) | 72 | 149 |
| Bayside | Queens | 1,517 | 16 % | **20 %** (14 / 56) | 145 | 76 | 63 % | **51 %** (29 / 21) | 107 | 153 |
| Far Rockaway | Queens | 872 | 42 % | **85 %** (30 / 16) | 170 | 67 | 94 % | **79 %** (34 / 9) | 12 | 62 |

### The old Staten Island villages

| district | borough | placeholder-year buildings | pipeline: by 1924 | photo 1924: est. standing (stood / open) | dated later, standing 1924 | dated earlier, open 1924 | pipeline: by 1951 | photo 1951: est. standing (stood / open) | dated later, standing 1951 | dated earlier, open 1951 |
|---|---|---|---|---|---|---|---|---|---|---|
| Stapleton | Staten Island | 876 | 64 % | **100 %** (47 / 4) | 180 | 24 | 97 % | **100 %** (47 / 5) | 7 | 42 |
| St. George | Staten Island | 720 | 64 % | **100 %** (41 / 5) | 108 | 19 | 96 % | **100 %** (40 / 6) | 17 | 41 |
| Tompkinsville | Staten Island | 1,166 | 60 % | **100 %** (24 / 24) | 69 | 110 | 90 % | **100 %** (34 / 15) | 24 | 135 |
| New Brighton | Staten Island | 815 | 70 % | **60 %** (12 / 47) | 31 | 258 | 92 % | **100 %** (22 / 13) | 11 | 79 |
| West New Brighton | Staten Island | 1,512 | 55 % | **100 %** (21 / 24) | 112 | 126 | 92 % | **100 %** (31 / 5) | 34 | 52 |
| Port Richmond | Staten Island | 1,391 | 63 % | **100 %** (24 / 13) | 153 | 112 | 97 % | **100 %** (37 / 8) | 15 | 102 |
| Mariners Harbor | Staten Island | 1,073 | 64 % | **89 %** (17 / 31) | 46 | 128 | 87 % | **93 %** (21 / 23) | 21 | 195 |
| Factoryville | Staten Island | 687 | 68 % | **100 %** (28 / 14) | 76 | 70 | 95 % | **100 %** (35 / 5) | 4 | 21 |
| Clifton | Staten Island | 979 | 53 % | **100 %** (29 / 24) | 108 | 55 | 87 % | **100 %** (30 / 20) | 8 | 116 |
| Rosebank | Staten Island | 834 | 62 % | **100 %** (21 / 18) | 64 | 82 | 88 % | **100 %** (30 / 13) | 7 | 56 |
| Tottenville | Staten Island | 527 | 42 % | **87 %** (14 / 23) | 39 | 44 | 78 % | **59 %** (13 / 36) | 6 | 122 |
| Richmondtown | Staten Island | 230 | 19 % | **31 %** (4 / 55) | 5 | 10 | 46 % | **18 %** (5 / 57) | 9 | 70 |
| New Dorp | Staten Island | 1,393 | 21 % | **25 %** (6 / 66) | 50 | 157 | 70 % | **100 %** (22 / 17) | 89 | 140 |
| Great Kills | Staten Island | 1,035 | 15 % | **24 %** (5 / 66) | 32 | 56 | 49 % | **46 %** (10 / 41) | 23 | 113 |
| Travis | Staten Island | 400 | 33 % | **66 %** (12 / 38) | 33 | 43 | 65 % | **59 %** (13 / 38) | 12 | 81 |

On Staten Island the "open" call is not safe (see the caveats: one certainly old house in four or five is
called open there, and only a fifth to a third is recognised), and the estimates stand on a narrow scale.
The north-shore villages (Stapleton, St. George, Port Richmond) show as standing; the "dated earlier, open"
counts for New Brighton, Tompkinsville, Mariners Harbor or Westerleigh are in good part houses under trees
that the classifier misses, not evidence against the pipeline.

### The old Bronx villages

| district | borough | placeholder-year buildings | pipeline: by 1924 | photo 1924: est. standing (stood / open) | dated later, standing 1924 | dated earlier, open 1924 | pipeline: by 1951 | photo 1951: est. standing (stood / open) | dated later, standing 1951 | dated earlier, open 1951 |
|---|---|---|---|---|---|---|---|---|---|---|
| Mott Haven | Bronx | 423 | 43 % | **100 %** (80 / 2) | 181 | 2 | 91 % | **100 %** (67 / 5) | 17 | 13 |
| The Hub | Bronx | 522 | 45 % | **100 %** (69 / 3) | 204 | 9 | 94 % | **100 %** (63 / 3) | 21 | 15 |
| Melrose | Bronx | 377 | 62 % | **100 %** (60 / 4) | 78 | 6 | 97 % | **100 %** (68 / 3) | 9 | 13 |
| Morrisania | Bronx | 329 | 65 % | **100 %** (62 / 3) | 64 | 4 | 96 % | **100 %** (70 / 3) | 9 | 10 |
| Tremont | Bronx | 553 | 76 % | **100 %** (62 / 6) | 75 | 25 | 100 % | **100 %** (73 / 1) | 2 | 4 |
| West Farms | Bronx | 212 | 67 % | **100 %** (50 / 10) | 35 | 11 | 99 % | **100 %** (61 / 4) | 3 | 9 |
| Fordham | Bronx | 635 | 74 % | **100 %** (50 / 9) | 71 | 36 | 99 % | **100 %** (69 / 2) | 3 | 11 |
| Kingsbridge | Bronx | 673 | 53 % | **73 %** (37 / 25) | 87 | 49 | 94 % | **91 %** (49 / 6) | 14 | 32 |
| Westchester Square | Bronx | 776 | 55 % | **88 %** (39 / 11) | 113 | 28 | 85 % | **87 %** (48 / 8) | 33 | 26 |
| Unionport | Bronx | 1,541 | 44 % | **88 %** (37 / 10) | 277 | 43 | 83 % | **84 %** (48 / 10) | 64 | 86 |
| Van Nest | Bronx | 1,652 | 47 % | **66 %** (31 / 24) | 160 | 88 | 73 % | **85 %** (48 / 9) | 107 | 62 |
| Williamsbridge | Bronx | 1,093 | 44 % | **46 %** (20 / 31) | 115 | 93 | 81 % | **79 %** (42 / 8) | 72 | 53 |
| Wakefield | Bronx | 2,116 | 33 % | **29 %** (16 / 42) | 162 | 224 | 84 % | **93 %** (49 / 6) | 104 | 74 |
| Eastchester | Bronx | 208 | 24 % | **28 %** (20 / 48) | 35 | 31 | 70 % | **55 %** (37 / 18) | 14 | 11 |
| City Island | Bronx | 898 | 41 % | **41 %** (18 / 32) | 60 | 73 | 85 % | **34 %** (22 / 18) | 13 | 115 |
| Hunts Point | Bronx | 320 | 27 % | **80 %** (40 / 22) | 67 | 7 | 85 % | **100 %** (64 / 7) | 25 | 13 |
| Pelham Bay | Bronx | 1,090 | 28 % | **61 %** (23 / 18) | 158 | 51 | 80 % | **72 %** (41 / 11) | 57 | 83 |

### Dated clearly too late (photograph of 1924 well ahead of the pipeline; Staten Island left out)

Districts with at least 500 placeholder-year buildings, by the gap between the photograph's estimate and
the pipeline's share standing by 1924.

| district | borough | placeholder-year buildings | pipeline: by 1924 | photo 1924: est. standing (stood / open) | dated later, standing 1924 | dated earlier, open 1924 | pipeline: by 1951 | photo 1951: est. standing (stood / open) | dated later, standing 1951 | dated earlier, open 1951 |
|---|---|---|---|---|---|---|---|---|---|---|
| Brownsville | Brooklyn | 1,138 | 15 % | **89 %** (58 / 8) | 529 | 11 | 72 % | **82 %** (47 / 5) | 115 | 38 |
| Elmhurst | Queens | 1,657 | 29 % | **94 %** (35 / 15) | 360 | 53 | 76 % | **99 %** (44 / 7) | 138 | 83 |
| Ridgewood | Queens | 2,085 | 42 % | **100 %** (78 / 2) | 952 | 15 | 97 % | **100 %** (72 / 2) | 29 | 30 |
| Ozone Park | Queens | 2,450 | 42 % | **100 %** (40 / 15) | 509 | 93 | 93 % | **100 %** (45 / 6) | 35 | 114 |
| Greenpoint | Brooklyn | 1,406 | 43 % | **100 %** (77 / 1) | 657 | 11 | 98 % | **100 %** (70 / 1) | 12 | 15 |
| Prospect Heights | Brooklyn | 549 | 45 % | **100 %** (79 / 2) | 249 | 5 | 99 % | **100 %** (76 / 1) | 3 | 3 |
| The Hub | Bronx | 522 | 45 % | **100 %** (69 / 3) | 204 | 9 | 94 % | **100 %** (63 / 3) | 21 | 15 |
| Flatbush | Brooklyn | 881 | 43 % | **96 %** (62 / 4) | 314 | 10 | 99 % | **100 %** (71 / 3) | 6 | 28 |
| Dutch Kills | Queens | 527 | 48 % | **100 %** (52 / 8) | 132 | 9 | 93 % | **100 %** (64 / 5) | 25 | 26 |
| Astoria | Queens | 1,152 | 42 % | **93 %** (36 / 17) | 241 | 68 | 91 % | **100 %** (51 / 8) | 41 | 75 |
| Sunnyside | Queens | 691 | 6 % | **53 %** (23 / 36) | 148 | 12 | 90 % | **100 %** (63 / 6) | 30 | 29 |
| West Flushing | Queens | 2,216 | 53 % | **100 %** (40 / 14) | 402 | 111 | 91 % | **92 %** (44 / 12) | 90 | 233 |
| Borough Park | Brooklyn | 2,126 | 48 % | **93 %** (61 / 6) | 583 | 38 | 77 % | **100 %** (67 / 2) | 224 | 20 |
| Bensonhurst | Brooklyn | 2,390 | 40 % | **84 %** (54 / 9) | 719 | 46 | 94 % | **88 %** (51 / 4) | 48 | 86 |
| Unionport | Bronx | 1,541 | 44 % | **88 %** (37 / 10) | 277 | 43 | 83 % | **84 %** (48 / 10) | 64 | 86 |
| Far Rockaway | Queens | 872 | 42 % | **85 %** (30 / 16) | 170 | 67 | 94 % | **79 %** (34 / 9) | 12 | 62 |
| Belmont | Bronx | 933 | 60 % | **99 %** (46 / 9) | 180 | 58 | 99 % | **100 %** (66 / 3) | 5 | 24 |
| Glendale | Queens | 1,334 | 61 % | **100 %** (47 / 7) | 238 | 60 | 99 % | **100 %** (54 / 6) | 3 | 75 |
| Kew Gardens | Queens | 1,526 | 59 % | **97 %** (36 / 13) | 196 | 95 | 92 % | **100 %** (46 / 6) | 42 | 73 |
| Bay Ridge | Brooklyn | 2,471 | 63 % | **99 %** (66 / 4) | 537 | 38 | 97 % | **100 %** (64 / 3) | 33 | 58 |
| Woodside | Queens | 1,583 | 37 % | **72 %** (28 / 25) | 280 | 148 | 87 % | **100 %** (59 / 4) | 79 | 44 |
| New Utrecht | Brooklyn | 2,225 | 42 % | **77 %** (48 / 10) | 526 | 58 | 91 % | **96 %** (58 / 4) | 61 | 75 |

### Dated clearly too early (pipeline well ahead of the 1924 photograph; Staten Island left out)

| district | borough | placeholder-year buildings | pipeline: by 1924 | photo 1924: est. standing (stood / open) | dated later, standing 1924 | dated earlier, open 1924 | pipeline: by 1951 | photo 1951: est. standing (stood / open) | dated later, standing 1951 | dated earlier, open 1951 |
|---|---|---|---|---|---|---|---|---|---|---|
| Gerritsen Beach | Brooklyn | 1,378 | 53 % | **0 %** (4 / 74) | 28 | 550 | 92 % | **49 %** (32 / 21) | 12 | 240 |
| Soundview | Bronx | 671 | 28 % | **0 %** (6 / 72) | 28 | 115 | 62 % | **44 %** (35 / 23) | 25 | 45 |
| Marine Park | Brooklyn | 2,730 | 25 % | **0 %** (0 / 99) | 1 | 657 | 97 % | **80 %** (47 / 7) | 26 | 192 |
| Forest Hills | Queens | 1,833 | 35 % | **12 %** (10 / 57) | 114 | 347 | 100 % | **94 %** (39 / 5) | 1 | 96 |
| Country Club | Bronx | 1,510 | 20 % | **0 %** (7 / 65) | 64 | 162 | 59 % | **15 %** (19 / 27) | 62 | 143 |
| Morris Park | Bronx | 1,981 | 25 % | **5 %** (10 / 59) | 141 | 241 | 89 % | **72 %** (41 / 11) | 66 | 178 |
| Clason Point | Bronx | 733 | 39 % | **20 %** (10 / 43) | 33 | 107 | 84 % | **43 %** (28 / 17) | 18 | 80 |
| Broad Channel | Queens | 764 | 47 % | **30 %** (14 / 47) | 59 | 166 | 97 % | **20 %** (13 / 22) | 1 | 93 |
| Belle Harbor | Queens | 1,363 | 25 % | **8 %** (8 / 58) | 63 | 161 | 89 % | **nan %** (nan / nan) | 0 | 0 |
| St. Albans | Queens | 1,329 | 30 % | **13 %** (11 / 59) | 94 | 178 | 93 % | **74 %** (35 / 13) | 22 | 157 |
| Corona | Queens | 706 | 32 % | **16 %** (11 / 57) | 50 | 111 | 73 % | **70 %** (35 / 15) | 46 | 58 |
| Baychester | Bronx | 917 | 16 % | **0 %** (3 / 65) | 16 | 77 | 44 % | **0 %** (15 / 36) | 57 | 55 |
| East Flatbush | Brooklyn | 2,536 | 24 % | **9 %** (10 / 52) | 159 | 225 | 96 % | **87 %** (52 / 6) | 50 | 151 |
| Bergen Beach | Brooklyn | 1,454 | 11 % | **0 %** (0 / 92) | 6 | 144 | 35 % | **10 %** (21 / 45) | 56 | 46 |
| Rosedale | Queens | 1,792 | 11 % | **0 %** (0 / 90) | 3 | 171 | 51 % | **0 %** (5 / 70) | 4 | 438 |
| Sheepshead Bay | Brooklyn | 1,048 | 31 % | **22 %** (16 / 43) | 68 | 76 | 89 % | **58 %** (33 / 13) | 17 | 107 |
| Castle Hill | Bronx | 866 | 7 % | **0 %** (2 / 80) | 17 | 53 | 36 % | **27 %** (27 / 27) | 87 | 26 |
| Laurelton | Queens | 2,071 | 15 % | **8 %** (8 / 58) | 134 | 168 | 94 % | **72 %** (34 / 13) | 25 | 224 |

These are the districts of the 1920s and 1930s on the outer plains and shores: the 1924 photograph shows
fields, marsh or bare sand where the pipeline already has a quarter to a half of the houses.

## 4. Caveats that matter for using this

- **Open country and leafy villages**: where less than 15 % of the ground within 50 m is built today, a
  third of the buildings known to be older than the photograph get p <= 0.2, and only a fifth get p >= 0.8
  (isolated houses under trees are not resolved at 2 m). There, and on Staten Island generally, "open" is
  weak evidence; "stood" stays good.
- **Built-up districts**: "stood" is evidence about the outline, not about today's building. Of the
  buildings with a *recorded* year 3 to 8 years after the 1924 photograph, 43 % show a building on the outline
  in it (46 % for the Landmarks Commission's dates, which are researched): replacements, and assessor years
  that are themselves late. The photograph is dated right: Yankee Stadium (1923) stands in it, the Bronx
  County Courthouse site (1931-34) is open ground, the old Waldorf-Astoria (demolished 1929) stands where the
  Empire State Building is.
- The white gutters between the sheets of the 1924 mosaic, the Rockaway and Great Kills gaps of the 1951
  mosaic and water edges carry no evidence (2.1 % and 1.4 % of the footprints).
- The hand check is 220 footprints, 44 per borough, read off thumbnails of the mosaics by the agent that
  built this (not by a person, and not on a large screen), with 12 % (1924) and 20 % (1951) left as unclear.
- Nothing here was compared with a second source (a Sanborn or Bromley sheet of the 1920s would do for a
  few blocks of Gravesend).
