# Improved farmland by county, 1821-1875 (calibration for the farm model)

Table: `data/tables/farmland_counties.csv` (73 rows). Written 2026-11-11 for the owner's question "was there
*that* much farming in 1820? like the entire metro area?". Columns: `county_fips` (the unit's main county),
`unit_fips` (today's counties the census figure covers, joined by `+`), `improved_acres`, `farm_acres`
(improved + unimproved land in farms, 1850 only), `land_acres` (sum of today's land area, Census 2020
Gazetteer `ALAND_SQMI` x 640, over `unit_fips`), `improved_share` = improved / land_acres.

## What the table holds (and does not)

| Year | Counties | Source | Check made |
|---|---|---|---|
| 1821 | 11 NY counties (Kings, Queens+Nassau, Richmond, Westchester+Bronx, Rockland, Putnam, Orange, Dutchess, Ulster, Sullivan, Suffolk) | Spafford, *Gazetteer of the State of New-York* (1824), the county entries quote the 1821 state census | none (see below) |
| 1850 | 27 units: the 12 NY counties above and New York County, 12 NJ counties (all but Union, which is inside Essex), Fairfield, New Haven, Pike | Federal census 1850, Table XI Agriculture, state sections | NY, NJ, CT: column summed to the printed state total |
| 1855, 1865 | the 12 NY counties | NY state census, "Recapitulation of agricultural statistics" | 1855 passes, 1865 fails by 1,327 acres |
| 1875 | 11 NY counties (New York County blank) | NY state census 1875, Table 56 | passes, two values recovered from the total |

Not in the table: 1825, 1835, 1845 (not found), 1880, 1900 (OCR of the volumes at census.gov is not text and
the archive.org copies were not reachable in the budget), 1925/1930 and 1950 (see "Not found"), anything for
the NJ counties before 1850 or after it, Bronx and Union as counties of their own (they were part of
Westchester and Essex in every year covered; Bronx from 1914, Union from 1857; no census of those years was read).
Nothing is interpolated.

## Sources, licence, how each number was read

All sources are US or New York State government publications of 1824-1877, public domain.

- **1850**: `https://www2.census.gov/library/publications/decennial/1850/1850a/1850-census-report-{new-york,new-jersey,connecticut,pennsylvania}.pdf`
  (the PDFs have an OCR text layer; `pdftotext -layout`). Table XI, "Acres of land in farms: improved, unimproved".
  New York: the OCR gave Suffolk as 148,612; the sum of the 59 counties then missed the printed total
  12,408,964 by exactly 5,000. I rendered the table (PDF page 35, a 5008 x 6960 scan) and read the county column
  by eye: Suffolk is 143,612, and every other inner county matches the OCR; with Suffolk corrected the sum equals
  the total. New Jersey (20 counties) and Connecticut (8) sum to their printed totals (1,767,991; 1,768,178).
  Pike (PA): read by name from the layout text, the state total not summed (the pdftotext rows were out of
  line with the county names; the numbers follow the name line, as they do for the checked counties).
  The unimproved column was not summed for NJ and CT, so `farm_acres` there is unchecked.
  Definition 1850: improved land = land "improved" by the farmer (tilled, meadow, pasture, orchard, garden),
  woodland and wild land are "unimproved". Farms only: land of a non-farm owner is not counted.
- **1855**: Hough's state census, `https://archive.org/details/cu31924078305582` (full text,
  `_djvu.txt`). "Recapitulation of agricultural statistics", column "Improved". OCR prints half acres as
  a stray glyph after the digits ("266,4351"); the first three digits after the comma were taken. The 60
  county values sum to 13,657,465 against the printed total 13,657,490 (OCR) - the gap is the dropped halves.
  The comparison sheet of 1821-1855 improved acres by county that the brief mentions is **not in this
  volume** (its only comparison is the state totals, in the introduction: state improved acres 1821 ... 1855);
  the volume's county pages hold 1855 only.
- **1865**: `https://archive.org/details/censusofstateofn_1865newy`, recapitulation table, column "Improved,
  1865". The OCR is poor: Delaware, Montgomery and Oswego have an unreadable last digit (set to 0 / 20 / 0
  to complete the sum) and the sum of the 60 values is 14,826,110 against the state total 14,827,437:
  **1,327 acres (0.009 %) short, one value carries an OCR error I did not locate**. Use +-1,500 acres on any
  1865 county. Only an image check of the page would fix it.
- **1875**: `https://archive.org/details/censusofstateofn1875newy`, "Table No. 56 recapitulation", column
  "Improved". 59 county values + blank New York County sum to the printed 15,875,552 only if Hamilton =
  4,332 (OCR "«4.332", read as 44,332 at first) and Orange = 321,411 (OCR token cut off at "321.4"; the last
  digits are recovered from the total, so Orange 1875 has no independent check). The county list in the OCR
  lacks New York: the line is blank or a dash and the sum implies none (the row is left out). All the rest
  of the NY state-census definitions of "improved" are as in 1850.
- **1821**: Spafford (1824), `https://archive.org/details/gazetteerofstate00spaf_0`, the county entry's
  paragraph quoting the state census of 1821: "acres of improved land". The OCR text was searched by county
  heading and the first county-level "improved land" figure taken (Dutchess 342,811; Westchester 226,699;
  Orange 221,966; Suffolk 175,994; Ulster 134,035 "occupied"; Queens 118,022; Putnam 79,113; Rockland 42,611;
  Sullivan 28,138; Kings 22,530; Richmond 19,792). **No check against a table total or the scan**: the only
  test is that the figures are of the size of 1850. The figures were attached to counties by their position
  in the text (county heading to first county-level paragraph); an entry that sat in the wrong county would be
  visible in the numbers only for Putnam, where I verified the paragraph ("79,113 acres of improved land ...
  persons employed in agriculture 1996") mentions Putnam. New York County: Spafford gives none. The brief
  says 1821 was the first state count; the 1821 and 1825 totals by county from Hough's comparative
  table could not be found, so the 1821 column rests on one secondary source.

## Definitions and where they change

1821-1875 state censuses and the federal censuses of 1850 and 1860: "improved" = cleared land of farms (and in
the state counts, 1821-1835, possibly of all owners): cropland, meadow, pasture and orchard, not woodland. The
federal censuses of 1850-1920 use the same term (I did not read the later volumes' definitions; the farm minimum changed more than once). From 1925 the census stopped asking for "improved land" in the county tables and reports "crop
land" (harvested, failure, idle or fallow) and pasture in three classes: a 1930/1925 value would be crop land
plus plowable pasture, not comparable to this column. None of those years is in the table.

Boundaries (`unit_fips` carries them): Queens + Nassau until 1899; Westchester + today's Bronx until 1874,
and from 1874 to 1895 Westchester + the Bronx east of the Bronx River (the western Bronx - Kingsbridge,
Morrisania, West Farms - passed to New York County in 1874; no table split them, so 1875 shares for
Westchester are understated and New York County 1875 would be `36061+36005`); New York County + western Bronx
from 1874; Essex + Union until 1857; Monmouth + Ocean until 1850 (the 1850 census lists them apart); Hudson
and Passaic are carved out of Bergen and Essex (1840, 1837) and today's borders differ slightly from
those of 1850. `land_acres` is today's land only; water and tidal marsh are not subtracted for the
past (filled land is counted as land today, so Manhattan, Brooklyn and Hudson shares are understated).

## The answer to the owner's question

Yes for the inner suburbs, no for the city, and "the entire metro area" overstates it: in the counties that
were farmland, roughly **half to three quarters of the land was improved farmland in the 1820s**, and the
rest woodland, marsh, shore and ground in towns. Around 1821 (the first state count, secondary source,
unchecked): Westchester with the Bronx 75 %, Richmond 54 %, Kings 51 %, Queens with Nassau 47 %, Putnam 54 %,
Dutchess 67 %, Orange 43 %, Rockland 38 %, Suffolk 30 % (long island's outer half was pine plains), Ulster
19 %, Sullivan 5 % (of today's land). Manhattan: no figure; 1850 gives 2,428 improved acres of 14,500
(17 %), falling to 1,050 in 1855. In 1850 (checked): Westchester with the Bronx 65 %, Bergen 54 %, Essex
with Union 52 %, Queens with Nassau 49 %, Middlesex 59 %, Somerset 71 %, Hunterdon 72 %, Mercer 66 %,
Monmouth 49 %, Morris 46 %, Fairfield 52 %, New Haven 53 %, Kings 39 %, Richmond 28 %, Hudson 31 %,
Passaic 29 %. The peak among the dates read was 1850 for Dutchess, 1855 for Putnam, 1865 for Rockland and 1875 for Orange
(all later than the 1820s, with swings of under 10 points), and **1821 for Westchester, Kings, Richmond and Suffolk** (they shrank from there:
Westchester 75 % in 1821, 65 % in 1850, 58 % in 1875; Kings 51 %, 39 %, 21 %). In the 1820s the improved
share, for the counties that have a figure, was never above 75 %: a fifth to a half of each county was not
farmland, in good agreement with a model that leaves "a fifth of the workable ground" in woodlot, and
steep, wet or sandy ground (Hudson Highlands, the Hackensack meadows, Long Island's plains) outside
the fields. Two cautions: the census counted improved land only on *farms* and only what farmers returned;
and the 1821 figures are the least checked in the table. The comparison with the map's model (share of
ground drawn as field in 1820) has not been made here.

## Not found

- NY state censuses of 1825, 1835, 1845 by county (the Hough volume of 1855 does not contain them; the
  1845 and 1835 volumes were not located on archive.org in the budget; Spafford 1824 gives 1821 only).
- NJ and CT before 1850 (no state count; the secondary sources - Wacker, *Land and People*; Harvard Forest
  land-use data - were not looked up).
- Federal 1860, 1880, 1900: the census.gov PDFs (`.../1880/vol-03-agriculture/`,
  `.../1900/volume-5/`, `.../1860/agriculture/`) are scanned images with no usable OCR layer (the 1880
  text is unreadable); no OCR engine on this machine. 1925/1930: the Cornell / NASS archive's file URLs
  returned 404 pages; archive.org has the 1930 New York volume (`1930AgNyStatsByCo_djvu.txt`) but its tables
  are transposed (one column per county) and the OCR text pages are inconsistent; the "all land in farms" and
  "crop land, total" rows could be read only for the first counties of the alphabet. 1925 Part I (eastern
  states) was not found on archive.org. 1950 not tried. Unlike 1850-1920 these years carry crop land, not
  improved land.
- Pike County beyond 1850, Union (as a unit) and the Bronx (as a county) in any year, New York County's 1875
  figure (the OCR drops it), the Pennsylvania state total for a check.
- The raw downloads (PDFs, OCR texts) remain under `data/raw/farmland/`; none is over 100 MB.
