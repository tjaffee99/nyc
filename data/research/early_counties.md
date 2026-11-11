# Early towns of the counties around the city (`data/tables/early_counties.csv`)

Columns, kinds and rules are those of `early_nyc.csv` (decision 25), read by the same generator
(`nyc_extras.early_sites`): every row is `kind=house`, so a row with `count` >= 6 is a street
village (houses on both sides of a line on bearing `rotation_deg`, half-length `spread_m`) and a
smaller one a scatter. Positions are generated (`procedural`); nothing here stands today (every
`end_year` is 1850-1900, none 9999). **Build files** (spec of the 161 towns, generator, rotation
and dry-ground scripts, their outputs): `data/research/early_counties_build/` (`python gen.py`
from that directory, with `rot2.json`, `rotw.json`, `shift.json` beside it, rewrites the table; the
working copies were in the git-ignored `data/interim/early_counties/`).

## What the table is

161 towns, hamlets, manors and landings of the 26 county units (not Jamaica or the city), 1,065 rows,
19,001 dwellings standing by 1840. Per town: the founding cluster (`start_year` = the founding year
of the places table) and one row per growth step: houses added by 1700, 1750, 1790, (1810 for towns
of over 2,000), 1830 and 1840, each with `start_year` the middle of its span (1840: 1835) and
`end_year` = start + 180 clamped to 1850-1900 (they stay standing to the end of the generation and
are then replaced by real or filled buildings, so the dwellings of 1840 are all of those added by
then). A step of fewer than 3 houses is merged into the next. A step is split into chunks of at most
30 houses on parallel lanes 75 m apart (and blocks 330 m along the street), so a big town is a
block of street strips, not one line.

## Where the numbers come from

* **Count.** Houses at year Y = max(founding cluster, anchors, curve). Curve = (village persons in
  1830 / 6) x (county population at Y / county population in 1830), the county series of
  `population_counties.csv` / `population_outer.csv` (log-linear between points; before the first
  point 2.2 % a year back; Mercer, Ocean, Putnam, Sullivan, Pike borrow Hunterdon, Monmouth, Dutchess,
  Ulster, Sussex; both Connecticut regions of the west use Fairfield, the south central one New
  Haven). Six persons per house.
* **Village persons in 1830** (`P30` in the spec) were **recalled from memory of the decennial
  census and town histories, order of magnitude, not looked up**: Wikipedia answered 429 (rate
  limit) from this machine all through the task, and no other source was fetched. Treat them as
  ESTIMATED with low confidence. Every row's `shape_note` says so.
* **Founding clusters** (`H0`) are assumptions (3-35 houses by the size of the settlement; 80 for
  New Haven's Eaton party of about 500 persons / 6) unless an anchor says otherwise.
* **Thinning.** Above 160 houses a town is drawn at a reduced rate (to 400 at 1840): ten towns
  (Newark, Elizabeth, Paterson, New Haven, New Brunswick, Poughkeepsie, Newburgh, Kingston, Trenton,
  Bridgeport) imply 500-2,500 houses in 1840; the note of each row states the factor. The generated
  village therefore never exceeds what the population implies.
* **DOCUMENTED (12 rows, 290 dwellings, 1.1 % of rows).** Only counts that the repository's own
  population notes quote with a source: Newark 1682 "a compact town, consisting of about one hundred
  families" and Elizabeth-Town 1682 "supposed to consist of one hundred and fifty families" and Bergen
  1682 "about 70 families" (Samuel Smith, *History of the Colony of Nova-Caesaria*, 1765, pp. 159-161,
  https://archive.org/details/historyofcolonyo00smit, public domain), Hempstead 1644 "thirty to forty
  families" (35 taken; Wikipedia, Hempstead village, CC BY-SA). One house per family is the
  assumption. Communipaw's 20 families (same account, "a village of 20 families") is not tied to a
  name in the source: ESTIMATED. New Paltz's twelve patentees: ESTIMATED (recalled).
  Everything else is ESTIMATED; no household count was fetched for any other town.
* **Rotation.** Length-weighted bearing (mod 180) of the roads of today (`roads_region.parquet`)
  within ~500 m of the old centre: those whose name has Main, Broad, High, Market, Front, Church,
  Water, King, Queen, Post, Albany or Hudson (the old street), else the top road class. Where the
  window held none, a 1-km window; two towns (Shelter Island, Marlborough) have none: rotation 0.
  An estimate, not a map of the old street; Newark's 25 deg mixes Broad and Market streets.
* **Position.** The places tables' point (checked there against the gazetteer); Rahway and
  Philipsburg Manor Upper Mills (41.0905, -73.8650, +-300 m) are from memory. Pavonia (1633-43, six
  houses at Communipaw) is one extra row.
* **Dry ground.** For the seven inner counties each centre was tested against the 1609 layer
  (`natural_1609_counties.geojson`: tidal marsh, freshwater wetland, water): seven centres with 15 %+
  wet cover within 160 m were moved to the nearest drier spot (stated in the note: English
  Neighborhood 500 m, Schraalenburgh 300 m, Hackensack 150 m, Rye 150 m, Peekskill 150 m, Harrison 100 m,
  Hoboken 50 m). **Outside those seven counties there is no 1609 layer (the generator's `natural_wet`
  covers the city box only), so the dry-ground test was not made** for the 19 outer units; coastal
  centres (Perth Amboy, New Haven, Bridgeport, Norwalk, Stamford, Southampton, Sag Harbor) may lose
  or gain dwellings when the lead's layer exists. With the generator run on this table the city box's
  layer dropped 185 of 19,001 dwellings.

## Dwellings standing (table value) and, in brackets, county persons per generated house

| town | 1670 | 1700 | 1750 | 1800 | 1840 |
|---|---|---|---|---|---|
| Bridgeport | 0 | 4 | 149 (101) | 337 (113) | 400 (124) |
| Poughkeepsie | 0 | 111 (42) | 199 (70) | 395 (120) | 400 (130) |
| Newark | 30 (12) | 100 (9) | 177 (23) | 258 (47) | 400 (79) |
| Elizabeth | 20 (28) | 150 (6) | 153 (18) | 326 (25) | 400 (32) |
| Paterson | 0 | 0 | 0 | 10 | 400 (41) |
| Newburgh | 0 | 0 | 59 (68) | 301 (97) | 400 (126) |
| Trenton | 0 | 59 (47) | 168 (49) | 333 (63) | 400 (61) |
| Norwalk | 15 (172) | 44 (113) | 133 (113) | 333 (114) | 400 (124) |
| New Haven | 161 (13) | 161 (26) | 206 (61) | 338 (95) | 400 (121) |
| Kingston | 25 (48) | 32 (73) | 97 (73) | 284 (87) | 400 (114) |
| Danbury | 0 | 44 (113) | 133 (113) | 333 (114) | 400 (124) |
| New Brunswick | 0 | 124 (17) | 205 (32) | 367 (48) | 400 (54) |
| Sag Harbor | 0 | 0 | 89 (100) | 163 (121) | 323 (100) |
| Goshen | 0 | 0 | 22 | 102 (287) | 280 (181) |
| Morristown | 0 | 0 | 71 (94) | 171 (103) | 273 (94) |
| Orange (NJ) | 0 | 0 | 36 | 83 (146) | 273 (116) |
| Stamford | 30 (86) | 30 (167) | 80 (188) | 193 (197) | 265 (188) |
| Bergen | 15 (37) | 70 (9) | 70 (9) | 70 (42) | 261 (34) |
| Tarrytown | 0 | 7 | 61 (167) | 133 (192) | 259 (167) |
| Rahway | 0 | 0 | 57 (50) | 133 (63) | 255 (50) |

County persons per house is the whole county's population over the one town's houses, so it should
be well above six; it is lowest (6-9) where a documented count of 1682 meets a county series whose
own source reckoned five persons to a family (Newark, Elizabeth, Bergen), and where the county was
small (Hudson). Dwellings are counted at the middle of each step (the convention of the brief), so a
step is in full at its midpoint: the dwellings of 1670 for New Haven include the 1700 step
(start 1669). 1840 is capped at 400 (thinned). Totals standing: 792 (1670), 1,747 (1700), 4,610
(1750), 11,231 (1800), 18,995 (1840).

## Not done, and checks not made

* Not looked up: any town's census or household count other than the four above; the 1830 village
  populations; founding sizes. These are the first thing to improve (Barber and Howe 1844 / 1841,
  Gordon's *Gazetteer of New Jersey* 1834 and Spafford's *Gazetteer of New York* 1824 give village
  houses for many of these towns).
* Towns not in the table: Nassau's Freeport/Raynortown, Jerusalem, East Meadow, North Hempstead;
  the 1788 township labels (Cortlandt, Pelham, Greenburgh, Mount Pleasant, Yorktown, North Salem,
  Pound Ridge, North Castle, New Castle, Orangetown, Clarkstown, New Hampstead, New Antrim, Suffern
  (1796), Hamden, North Haven, Woodbridge CT, Weston, Brookfield, New Fairfield, Trumbull,
  Mahwah, Fort Lee, Ringwood's neighbours); Sullivan County (Bethel, Cochecton) and Pike's Lackawaxen;
  Sussex's Andover and Walpack; Hunterdon's Frenchtown, Milford, Whitehouse, Stockton; Morris's
  Chester, Rockaway, Denville; Mercer's Yardville and Robbinsville; Middletown (Monmouth) and the
  smaller Monmouth hamlets Colts Neck and Holmdel are in the places tables but Colts Neck is out;
  Kingston's 1777 burning and the Revolutionary war (houses are not cut by it); West Point
  (military); mills, ironworks and farms outside villages.
* The generated rows were not looked at on screen. Not checked: that the houses stand on the
  right side of each river or on dry ground outside the seven inner counties.
