# Tables for the 19 outer county units (round of 2026-11-11)

Files (all new; the existing tables are untouched):

| file | columns | rows |
|---|---|---|
| `data/tables/population_outer.csv` | as `population_counties.csv` | 397 |
| `data/tables/places_outer.csv` | as `places_counties.csv` | 230 |
| `data/manual/routes_outer.csv` | as `routes.csv`, mode `highway` | 157 lines of 72 sections |
| `data/manual/fill_zones_outer.csv` | as `fill_zones_counties.csv`, kind `reservoir`, precision `precise` | 137 rings |

Scripts and scratch: `data/interim/outer_tables/` (`make_pop.py`, `make_places.py`, `make_routes.py`, `make_fill.py`,
`match_nid.py`). Downloads in `data/raw/outer_tables/`: the Wikipedia wikitext (`wiki/`), the Census Bureau's *A Century of
Population Growth* OCR (`cpg.txt`, 1.7 MB) and the Army Corps' National Inventory of Dams (`nid.csv`, 69 MB; delete after use,
the URL is the record). Overpass was not reachable; geometry comes from the Overture extracts instead (see below).

## Area keys (population)

The keys are the counties of the census, not the planning regions. Nassau is **not repeated**: `population_counties.csv`
already holds it (1644-2025.5).

| area key | unit(s) of the round | FIPS |
|---|---|---|
| `suffolk` | Suffolk NY | 36103 |
| `putnam` | Putnam NY (first census 1820) | 36079 |
| `orange_ny` | Orange NY | 36071 |
| `dutchess` | Dutchess NY | 36027 |
| `ulster` | Ulster NY | 36111 |
| `sullivan_ny` | Sullivan NY (first census 1810) | 36105 |
| `middlesex_nj` | Middlesex NJ | 34023 |
| `monmouth` | Monmouth NJ | 34025 |
| `ocean` | Ocean NJ (first census 1850) | 34029 |
| `somerset` | Somerset NJ | 34035 |
| `morris` | Morris NJ | 34027 |
| `sussex` | Sussex NJ | 34037 |
| `hunterdon` | Hunterdon NJ | 34019 |
| `mercer` | Mercer NJ (first census 1840) | 34021 |
| `fairfield_ct` | **both** Greater Bridgeport (09120) and Western Connecticut (09190): Fairfield County, which the two regions (with part of Litchfield) replaced. Use it once, not per region | 09001 |
| `new_haven_ct` | South Central Connecticut (09170): New Haven County | 09009 |
| `pike_pa` | Pike PA (first census 1820) | 42103 |

## Population: sources and what is estimated

- 1790-2020 (every census from the county's first): the Census Bureau's county counts (Forstall 1996 for 1790-1990, then the
  2000, 2010, 2020 censuses) **as tabulated in the Wikipedia county article** (`{{US Census population}}`), read by script
  from the wikitext. The figures were not checked against the Census Bureau PDF. The counts are those of the county of the census
  year: the boundary changes are written in the first row of each county (Putnam from Dutchess 1812, Sullivan from Ulster 1809,
  Ocean from Monmouth 1850, Mercer from Burlington, Hunterdon and Middlesex 1838, Pike from Wayne 1814; Rockland out of Orange 1798,
  Greene out of Ulster 1800). The present-area correction `population_counties.csv` makes for its counties was not made here.
- No 2025.5 estimate rows (the existing file has them for its counties).
- Colonial counts (8 rows; "estimate" in the note): *A Century of Population Growth* (Census Bureau 1909, tables 88, 97, 98), read
  from the archive.org OCR by hand (OCR errors are possible): Suffolk 1698 (2,679), 1756 (10,291), 1771 (13,128) - same ground as
  today; Ulster 1756, 1771; Dutchess 1771; Orange 1756, 1771 - those counties were larger then (Ulster held Sullivan and Greene,
  Dutchess held Putnam, Orange held Rockland) and are **not scaled**: the note says so. The colonial counts of 1698-1749 and 1786
  for these counties, Dutchess 1756, and New Jersey's colonial counts (1726, 1738, 1745, 1784) and Connecticut's were not read.
- No founding-era estimate (like the 1644 Hempstead row) was found for these counties in a source at hand.

## Places

`places_outer.csv`: 230 rows over the 18 other units (Nassau has 118 rows in `places_counties.csv` and was not added to): Suffolk 27,
Putnam 9, Orange 18, Dutchess 15, Ulster 12, Sullivan 9, Middlesex NJ 16, Monmouth 18, Ocean 11, Somerset 11, Morris 13, Sussex 9,
Hunterdon 8, Mercer 9, Greater Bridgeport 7, Western Connecticut 16, South Central Connecticut 16, Pike 6. Every row is tier `city`
(county seats and cities) or `town`; no name chains (`replaced_by` empty) and no regions, landscape features or Lenape places.
Ids are prefixed `suf_ put_ ora_ dut_ uls_ sul_ mid_ mon_ oce_ som_ mor_ sus_ hun_ mer_ brg_ wct_ scc_ pik_`.
Not every municipality is there: the colonial towns, county seats, cities and the larger old villages are; the rest are not.

- Year rule, as the brief: first-settlement year for the colonial towns, incorporation year for the suburbs. The note says which
  and whether the year was found: `nominal ... stated in the cited article` (the year occurs in the Wikipedia article's history
  sentences, checked by script), `nominal ... not found in the cited article`, `estimated` (my reckoning, kept because a place that
  existed must not be empty). Of the 230 rows 82 carry a year found in the cited article, 60 are "nominal ... not found in the cited article" (the year may still be right: the article may give it in a table or not at all) and 88 are `estimated` (mine, or a bracket): **treat
  the settlement years of the minor towns as approximate**.
- Coordinates were typed from memory (five decimals), then checked against the Census 2023 Gazetteer (`data/raw/outer_tables/gaz/`,
  script `data/interim/outer_tables/gaz_fix.py`). Rule: a row matching the gazetteer's place file (city, borough, village, CDP)
  keeps my old-centre point if within 2.5 km, else takes the gazetteer point; a row matching only the county-subdivision file
  (towns, townships: their point is the centroid of the whole township) keeps my point unless it is more than 8 km away. 209 rows kept,
  15 moved (note "position: Census gazetteer", or the Academy's Plain for West Point, set by hand because the CDP point lies in the
  woods), 6 with no gazetteer match (Garrison, Menlo Park, Peapack-Gladstone, Whitehouse Station, Dingmans Ferry, Greeley) kept from
  memory and marked so in the note. Kept rows were not checked beyond that: a point may still be up to 2.5 km (places) or 8 km
  (townships) from the true centre.
- Greater Bridgeport has only 7 rows because the region is 6 towns; Shelton, Derby and the Naugatuck Valley are another region.
- Mercer's Hamilton and Ewing, Somerset's Franklin and Hillsborough and similar townships without a village centre are missing.

## Highways

`routes_outer.csv`: 157 lines (`segment_seq` 1-4: the roadways of a divided highway as separate lines, longest first) of 72 sections.
Geometry is **not from Overpass** (blocked on this machine) but from Overture's transportation segments of the outer box
(`class motorway`, plus `trunk` for named parkways), selected by `name` and by route ref (`routes`), merged, split into
carriageways of 400 m or more and simplified to at most 30 points (about 50-150 m tolerance). Overture's roads derive from
OpenStreetMap (ODbL). Each section is a bounding box on a route, so its ends are cut by latitude or longitude, not at an
interchange; where the note says "breakpoints by longitude" the cut may be several hundred metres off the interchange it names.
Segments inside `common.REGION_BBOX` (-74.52, 40.47, -73.40, 41.38) are left out for routes the existing `routes.csv` already
dates there; the Long Island parkways and the Long Island Expressway **are** included inside it for Nassau, because `routes.csv`
has no row for them outside New York City.

Dated sections (year from the Wikipedia route article's history, to the day where it gives one; `estimated:` in the note when
not): New Jersey Turnpike Exit 5-11 (1951.91), Garden State Parkway south of the Raritan (five sections, 1952-1954), I-195, Route 29
(Trenton), I-80 (Netcong-Denville), I-287 (four sections), I-78 (two), I-84 in New York (nine sections, 1963-1971) and in Connecticut
(two), I-684 (Brewster), the Thruway (Orange-Ulster), Taconic Parkway (Putnam, Dutchess, three sections), Route 17 (Orange, Sullivan),
the Long Island Expressway (ten sections, 1958-1970), Northern State (seven), Southern State (four), Sagtikos, Sunken Meadow (two),
Wantagh (two), Meadowbrook (two), Sunrise Highway (two), Merritt and Wilbur Cross (four), Connecticut Turnpike I-95, Routes 8 and 25,
I-91, I-691.

**Estimated** (23 lines, noted "estimated:"): I-195 west stretch; I-287 Edison-Bedminster; I-78 west of Exit 13; I-84 west of
Greenville and New Hampton-Newburgh; Thruway Orange-Ulster (1954-55 bracket); Taconic north of NY 55; Route 17 in Orange and Sullivan;
the 1927 Southern State section; two Northern State stretches; Merritt and Wilbur Cross sections (month or order not read); Route 25;
I-84 Connecticut; I-91 and I-691 in Connecticut (placeholders, no source read).

**Missing** (no row; the roads stay on roads.py's 1960 default and appear in its report): I-295 in Mercer, I-95 sections that opened
after 1958, I-84 in Pike (Pennsylvania), US 1 and Route 18/33/35/24/72/133 freeways, I-287 Route 24-Route 10 (inside the region box),
the New York State Thruway's exact openings by section, Sunrise Highway's freeway conversions of 1994-98, the Long Island Expressway
east of Manorville (no segments selected), Routes 9, 15 (Hartford side) and 17 in Ulster, the Palisades Parkway (its Orange County end
is in the existing `pip_north`), Route 17K, and every non-motorway state highway.

## Reservoirs and made lakes

`fill_zones_outer.csv`: 137 rings (kind `reservoir`, `year_end` 9999, precision `precise`) for 129 water bodies of 40 ha and more in
the 19 units (counts by unit in the final report; `borough` = the county or planning region). Ring = the Overture water polygon
(`outer_water.parquet`), exterior only, simplified to 30 m, extra parts of a multipolygon of 8 ha or more as `_b`, `_c`.
Year = the National Inventory of Dams' "Year Completed" of the largest dam within 350 m of the outline (the dam's `NID ID` is in
the note); the nine bodies listed in `make_fill.py` (`OV`) were corrected by hand from Wikipedia: Candlewood Lake 1929 (the NID
lists only a 1902 dike), Lake Zoar 1919 (Stevenson Dam; the match took the Shepaug Dam, 1955), Lake Lillinonah 1955, Rondout Reservoir
1950, Lake Hopatcong 1831 (enlargement of a natural lake by the Morris Canal dam, estimated), Greenwood Lake 1928 (NID's present dam;
the first dam's date was not found, estimated), Croton Falls Reservoir 1911, the two Ashokan basins 1915, West Branch Reservoir 1895,
Lake Carnegie 1906 (NID says 1900).
Caveats: (1) the NID year may be a mill dam or a rebuild, not the closing of the lake as it is today; (2) natural lakes that a
dam enlarged are in the table with the dam's year; the ring only matters for the water that the 1609 layer does not hold; I left out
Lake Mahopac, Swartswood Lake, Culvers Lake and Mecox Bay; other natural lakes with a small dam may still be in (Whaley Lake 1850,
Lake Mohawk's 1927 is real); (3) bodies without a matching dam in the NID are absent: Lake Montauk, Mercer Lake, Assunpink Lake,
Squantz Pond, Popolopen Lake, Mombasha Lake, Budd Lake and some others; Lake Wallenpaupack is 1926 (Tafton dike, NID), Round Valley
1961, Spruce Run 1964, Manasquan Reservoir 1990 (NID); (4) CT bodies outside the three planning regions (Northwest Hills, Capitol,
Naugatuck Valley ...) are not in the file; (5) the water polygons are Overture's of 2026-10-21: names are Overture's.
Nassau and Suffolk each have one (Hempstead Lake 1873, Mill Pond 1920).
