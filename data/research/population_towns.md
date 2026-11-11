# Municipal population series (round 3, 2026-11-11)

Files: `pipeline/town_population.py`, `data/tables/population_towns.csv` (9,118 rows, 559 municipalities),
`data/interim/towns/towns.parquet` (outlines), `towns/done.csv` (per-municipality status and the article used),
`towns/checks.txt` (output of `town_population.py checks`), raw pages in `data/raw/wikipedia_towns/` (39 MB).

## Method
- Outlines: TIGER 2024 county subdivisions (`tl_2024_{34,36,09,42}_cousub.zip`), the 26 counties (Connecticut:
  planning-region codes 09120/09170/09190), water-only rows (ALAND 0), "not defined" rows and reservations dropped,
  simplified to 40 m in UTM 18N, stored EPSG:4326. New York keeps towns and cities (no villages), so village
  populations are inside their town's. Columns `geoid, name, namelsad, county_fips, state, geometry`.
  `name`: NJ/PA townships keep "Township" ("Woodbridge Township"), boroughs/cities/towns do not; NY towns "Hempstead town",
  NY cities and CT towns bare. The five boroughs are not included.
- Series: English Wikipedia raw wikitext, `{{US Census population}}` or `{{Historical populations}}` (positional
  year/count pairs), redirects followed, the template with most years kept; title candidates tried in order
  ("X, State", "X Township, State", "X (town), New York", "X, County, State"), a page is accepted only if it is not a
  disambiguation and names the county in its infobox. One page per 4.5 s, back-off on 429/5xx, cached; resumable
  (`done.csv`). Order: largest first by number of buildings in the polygon (the Census API now answers only with a
  key — keyless requests are redirected to "missing key" — so it was **not used**).
- Join: `population_towns.geoid` == `towns.parquet.geoid` (10-digit TIGER GEOID, string, leading zero in Connecticut/Pennsylvania).
  `county` is the map's county name (as in `extent_counties.json`); the county tables use lower-case/underscored names.
- Rows are each census year the article lists (1790-2020), whatever it lists: municipalities that did not exist, or were
  not tabulated, earlier start later (mean first year 1865). Gaps of 1800/1810 in New York towns are the census's (towns
  were not tabulated), not parse errors.

## Coverage
559 of 559 municipalities have a series (all pages parsed; none failed). Mean first year 1865. 557 have 2020, 558 have 2010.
Missing 2020: Porter and Shohola townships (Pike PA; their pages stop at 2010). Per county (municipalities / mean first
year): Bergen 70/1892, Dutchess 22/1838, Essex 22/1870, Greater Bridgeport 6/1822, Hudson 12/1871, Hunterdon 26/1858,
Mercer 12/1846, Middlesex 25/1864, Monmouth 53/1888, Morris 39/1879, Nassau 5/1842, Ocean 33/1886, Orange 24/1839,
Passaic 16/1894, Pike 13/1968, Putnam 6/1853, Rockland 5/1818, Somerset 21/1862, South Central CT 15/1828, Suffolk 10/1800,
Sullivan 15/1846, Sussex 24/1855, Ulster 21/1830, Union 21/1873, Westchester 25/1828, Western CT 18/1813.
`fill` stage: adds a 2020 row from the infobox only if the template lacks it (1 row, Kent town).

## Defects found and fixed
- Name collisions: Hopewell township, Milford township (PA) and the two Washington townships (Morris, Bergen) first got a
  borough's article; found by the duplicate-2020-value test and fixed with `OVERRIDE` in the script.
- TIGER 2024 gives Princeton LSAD "00" and "Bridgewater" contains "water": both were dropped by the first filter, fixed.

## Known problems (not fixed)
- Orange, Connecticut: the article says 16,614 for 1920 (a typo for about 1,614; 1910 and 1940 are ~1,500-2,000). Drop it.
- Princeton (merged 2013): only 2010 and 2020; the old borough and township are not on the map.
- Genuine jumps from boundary changes, not errors: Fishkill 1910 13,858 -> 1920 2,095 (Beacon), Kingston town 1870 -> 1880,
  Kearny 1880 -> 1890, North Brunswick 1850 -> 1860, Chatham township 1890 -> 1900, Green Brook township 1890 -> 1900.
- Infobox 2020 differs from the template for Dingman and Neversink (infobox is a later estimate); the template is the census.
- Carmel (Putnam) has no 1950 value; the article's template skips it.
- Not checked: every series against the Census; page choice for municipalities whose name is shared with a village
  (New York) was validated by the infobox county test and by county sums only.

## Checks (see `towns/checks.txt`)
Series printed for Newark, Jersey City, Paterson, Elizabeth, Yonkers, New Rochelle, White Plains, Hoboken, Bayonne,
Princeton, Trenton, New Brunswick, Stamford, Bridgeport, New Haven, Hempstead town, Poughkeepsie city; no spikes of 4x
over both neighbours. 2020 values are the census's (Newark 311,549, Jersey City 292,449, Yonkers 211,569, New Haven 134,023,
Bridgeport 148,654, Stamford 135,470, Hempstead 793,409; matches the article infoboxes except 2 noted above).
County sums (towns vs county table), 1950 and 2020: within 0.2 % for 2020 in all 22 counties compared, and for 1950 in all but three (below); Middlesex, Orange, Sullivan, the Connecticut regions and Pike
have no matching county-table row in the check (name mismatch) and were not compared. Outside 2 %: Dutchess 1950 0.973, Mercer 1950 0.923 (Princeton's predecessors absent),
Putnam 1950 0.731 (Carmel has no 1950).

## Resuming
`cd pipeline && ../.venv/bin/python town_population.py fetch` (skips what `done.csv` lists), then `fill`, then `checks`.
