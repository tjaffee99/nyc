# Brooklyn Navy Yard, building by building (research notes)

Part of the map's "a place that existed must not be empty" work. Outputs:
`data/tables/known_building_dates.navy_yard.csv` (50 standing buildings), `data/tables/notable_demolished.navy_yard.csv`
(34 lost buildings and structures), tools in `data/manual/atlas/tools_navy_yard/` (`reg.py`, `reg155.py`, `seg.py`,
`seg2.py`, `build.py`, `stats.py`, `final.py`, `match.py`), downloads in `data/raw/navy_yard/`, scratch and the registration
(`reg.json`, `seg156*.json`, `bb15x.html` label boxes) in `data/interim/navy_yard/`. `build.py <scratch dir>` rebuilds both CSVs.

## Sources used

| source | licence | gave |
|---|---|---|
| National Register of Historic Places nomination, "Brooklyn Navy Yard Historic District" (NRIS 14000261, NPS, received April 2014), https://npgallery.nps.gov/GetAsset/314d2a7b-7525-4998-8a77-dd3b9dba7073 (224 pages) | US federal document, public domain | the resource inventory with a date for each building (sections 7), the narrative of lost buildings (section 8: ship houses 1820 and 1893, Lyceum, Building Ways 1903 / 1917, Buildings 4, 15, 18, 91, 93, 190, 294, 296, 530, Hammerhead crane, Cob Dock, Wallabout Market), and six historical plans of the yard from the Brooklyn Navy Yard Archives: Maps #10-#15 (1810, 1827, 1872, 1890, an undated one, 1946) |
| Wikipedia, "Brooklyn Navy Yard" (fetched 2026-11-11 through the API), https://en.wikipedia.org/wiki/Brooklyn_Navy_Yard | CC BY-SA, facts only | second dates for Buildings 3, 41, 77, 92, Admirals Row (ten houses 1864-1901, nine torn down in 2016), the Wallabout Market and Cob Dock history |
| The map's own built file (`data/interim/nyc_buildings.parquet`) | project | names = building numbers of the city's footprints (the footprints carry the yard's number in `name`), BINs, current years |

Outbound requests used the User-Agent `NYCThroughTime-research/0.1`.

## What was done

1. **Standing buildings (50 rows).** For each building number in the NRHP inventory whose footprint is named with that
   number in the city data, one row per BIN: the NRHP year, a second source's year where they differ (said in the note,
   "estimated" for ranges and "ca."): 44 BINs inside the yard outline (45 of the 129 footprints; the rest of the 129
   still carry the lot stamp of 1958 and have no source here) and 6 hospital buildings. The hospital buildings
   (R4-R7, R104, 311) have no number in the city data: each was matched to a footprint by the position of its label on
   NRHP Map #15 registered to the standing buildings (nearest footprint 2-21 m; the match is estimated). Left out on purpose:
   Quarters A, the Surgeon's House (R1) and the Naval Hospital (R95), already dated by the Landmarks Preservation
   Commission in the built file (`year_src` = `lpc`: 1806, 1863, 1834, all consistent with the NRHP); R2/R3, R8/R9,
   R103/R109, R426 (no footprint could be matched to one label). No row contradicts an LPC year (0 of 50 on an LPC footprint).
   Building 296 (row `ny_b296`): the footprint traced from the 1946 plan for 296 is covered 85 % by the city's 14,833 m2
   footprint BIN 3335182, although the NRHP calls 294 and 296 "demolished": the row dates that footprint 1943 and says the
   identity is uncertain.
2. **Plans registered.** The embedded plans of NRHP Maps #12, #13 and #15 were registered by an affine fit (page
   coordinates of the printed building numbers, taken from the PDF text layer, against the centroids of the same-numbered
   standing footprints; outliers dropped one at a time; residuals in UTM metres):
   Map #13 (1890): 8 points, rms 7.1 m; Map #15 (1946): 28 points, rms 11.8 m; Map #12 (1872): 6 points, rms 5.4 m (all 9
   usable points give rms 12 m; 6 rather than 8 points were kept, the 3 dropped ones all had residuals above 13 m).
   Map #14 (undated, rotated sheet) did not fit (rms 61 m) and was not used. Labels stand beside the buildings, so the
   control points themselves are +-10 m. Maps #10 and #11 (1810, 1827) were not registered (one control point, Quarters A).
3. **Lost buildings (34 rows).** Outlines: (a) `seg.py`/`seg2.py` found shaded rectangles on the 1890 plan automatically
   (grey fill against the local background; minimum rotated rectangles; only elongated ones of 300-3,500 m2 that do not
   carry a label and are not on a standing footprint): 12 "yard shop" rows; (b) polygons read by eye off 300-dpi crops of
   the 1946 plan (Building 18, Building Ways 1 and 2, the structural shop Building 4, Building 294, five buildings of the
   Kent Avenue Basin ground) and of the 1890 and 1872 plans (timber shed 15, ship houses, Marine barracks Buildings 91 and
   93). (c) Admirals' Row: nine houses (B left out), dates from the NRHP inventory, **positions estimated** from the
   plan labels, rectangles `12x16` rotated 85 degrees. Every outline is `+-8 to 15 m`, as each row's `shape_note` says.
   Every row is inside the yard outline (>= 50 % of its area; the ways extend over the water and are clipped), none
   overlaps a vanished building of the map in time (0 pairs), and the 13 time-overlap pairs with standing footprints are
   all with small footprints that carry the 1958 lot stamp (see "wiring").

## Dates and what is estimated

* A start year is the NRHP's (ca. 1841 timber shed 15; 1820 ship houses; 1903 / 1917 the Ways; 1858 Marine barracks;
  1939-40 Building 18; 1942 / 1943 Buildings 294 / 296; the Admirals' Row inventory years 1864-1901). Rows from the
  1872 / 1890 plans without a date in any source (12 "yard shop" rows) start at **1862, estimated** (the grid was built
  up on the 1872 plan; neighbouring standing shops are dated ca. 1855-65 by the NRHP).
* Most end years are **estimated**: the NRHP says "demolished" without a date. 1980 is a placeholder in a range of
  1966-2016 for things the 1946 plan shows (still on the plan, so >= 1946; gone by 2014, the nomination). Dated ends: ship
  houses 1893 (NYT 15 Oct 1893 via the NRHP), Building 93 1941, Building 91 ca. 1918, Admirals' Row 2016 (Wikipedia; one of
  the ten survived, which is not stated, so all rows carry 2016).
* Heights, storeys and materials are estimated (no source gives them for the lost buildings); each note says so.

## What was not found / not done

* No yard-wide plan beyond the NRHP's six: the New York Public Library's pages (Sanborn "Plan of United States Navy Yard
  and Wall About Basin") answered with a bot block; the Library of Congress searches returned no plan of the yard; the
  HAER / HABS data pages and the LPC designation reports were not fetched (budget).
* **Not placed** (documented but no position or size): the first Naval Lyceum (Building 1, 1833, near Quarters A, demolished
  ca. 1917-18 for the Ways), the Round House, Building 115 (1890 machine shop), Building 190 (boat shed, 1919), Building 530
  (roundhouse, 1914), Building 21 and Building 23 (timber sheds), Building 6 (joiners' shop), the Hammerhead crane (350 t,
  1941-42, beside Building 270, demolished: no date), the Cob Dock's guard house, boiler house, shell house, brig and
  ordnance sheds, the Wallabout Market buildings (razed 1941), the laboratory of the Naval Hospital (1853), the first
  yard hospital (1811).
* Not traced: the 1810 / 1827 plans (so the yard of 1810-1850 has only the ship houses, the Marine buildings and Quarters A;
  the 1872 shop rows start 1862 by estimate), the Cob Dock, the 1946 plan's remaining numbered buildings (23, 24, 63, 13, 14,
  125, 424 ...; about 150 more shaded buildings), 1890 shops that touch a label circle.
* The dry docks (1-6), piers and portal cranes are structures with NRHP dates (Dock 1 1841-51, 2 1887-90, 3 1893-97, 4 1913,
  5 and 6 1942) but are not in the building data; listed here for whoever draws them.
* The yard's building count after these rows: 1850 9 (map now 5), 1880 54 (27), 1900 84 (52), 1925 128 (85), 1944 193 (125),
  1966 221 (195), 1810 0 (the Commandant's house, Quarters A, stands outside the yard outline). The yard held several
  hundred buildings in 1944; about 75 of the 129 standing footprints are still lot-stamped (1958) and most of the 1946 plan's
  buildings are untraced, so the figures are floors, not totals.
