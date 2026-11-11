# Trenton and New Brunswick, New Jersey: building years and landmark models (towns round, second pass, 2026-11-11)

Files: `data/tables/known_building_dates.trenton_nb.csv` (75 rows), `viewer/src/landmarks/nj-towns.ts` (export `NJ_TOWNS`, 14 models),
scratch `data/research/towns_nj_build/` (`rows.py` matches a spec line to a footprint and writes the row, `fp2.py` extracts the outlines,
`check.ts` is the numeric check, `verify.py` the point-in-polygon check, `fetch.py` / `fetch.sh` the paced Wikipedia fetch, `osm.py`, `wd.py`),
raw downloads `data/interim/towns_nj_raw/` (Wikipedia raw wikitext `wp_*.txt`, Wikidata `wd_*.json`, OpenStreetMap `osm_*.json`).

## Method and sources
- **Every year comes from an opened page**: Wikipedia raw wikitext (one page at a time, 4.5 s apart, `NYCThroughTime-research/0.1`), read in this session.
  Wikidata (SPARQL by box) and the OpenStreetMap map API were used to find names and positions, not as a source of years (OSM has no `start_date` in
  Trenton, a few in the Rutgers campus; those were used only where a Wikipedia page confirms them).
  No state, county, university or hospital page opened: nj.gov (HPO lists 403), sah-archipedia.org (403), rutgers.edu (redirects) were tried once. Trenton's
  Wikipedia pages for the National Register properties (NRHP list of Mercer County, parsed for the Trenton rows) gave most Trenton years; New Brunswick's came
  from the article on Voorhees Mall (section headings with years), the tallest-buildings table in the New Brunswick article, Civic Square and the
  Busch Campus article.
- **Positions**: each row's point is `representative_point()` of the footprint it dates (polygon of `nj_mercer.parquet` / `nj_middlesex.parquet`), to 6 decimals.
  `rows.py` takes a source coordinate (Wikipedia / Wikidata / OSM / NRHP, often coarse) and picks the containing footprint (the largest if several), else the
  nearest within 25 m; ids of footprints used directly are written `id:<8 characters>` in the spec. Rows whose match was an unrelated small outline
  (Henry Clay cigar factory, Dickinson House, In and Out Club, Kuser Estate, Second Street School, Gateway tower, King Block, SoCam) were dropped.
- **Checks** (`verify.py`): 75 rows (Trenton 35, New Brunswick 40); every point lies inside its footprint (0 failures); no footprint is hit by two rows; no
  row falls in a footprint that `known_building_dates.nj_outer.csv` already dates; ids unique. 66 rows are `exact:`, 9 `estimate`.
- Target was 45 per town: **not reached** (Trenton 35, New Brunswick 40). The pages that open give years for few of the university, state and hospital
  buildings; those that did not open are listed below.

## Rows
### Trenton

| id | footprint / name | year | basis | page |
|---|---|---|---|---|
| tre_cure_arena | CURE Insurance Arena | 1999 | exact: opened October 6, 1999 (groundbreaking December 2, 1997) | wp:CURE_Insurance_Arena |
| tre_st_mary_cathedral | Cathedral of St. Mary of the Assumption | 1959 | exact: second cathedral dedicated March 14, 1959 after the fire of March 14, 1956 destroyed the church of 1871 | wp:Cathedral_of_St._Mary_of_the_Assumption_(Trenton,_New_Jersey) |
| tre_state_museum | New Jersey State Museum | 1964 | exact: in 1964 the museum moved into facilities created for it in the Capitol Cultural Complex | wp:New_Jersey_State_Museum |
| tre_first_presbyterian | First Presbyterian Church | 1839 | exact: the current church was built in 1839, the third on the site | wp:First_Presbyterian_Church_(Trenton,_New_Jersey) |
| tre_hughes_justice | Richard J. Hughes Justice Complex | 1982 | exact: completed in 1982 and dedicated 1982 | wp:Richard_J._Hughes_Justice_Complex |
| tre_dmv_building | New Jersey Division of Motor Vehicles Building | 1961 | exact: completed in 1961 (Kramer Hirsch & Carchidi) | wp:New_Jersey_Division_of_Motor_Vehicles_Building |
| tre_broad_street_bank | Broad Street National Bank | 1900 | exact: the Broad Street National Bank built in 1900 (named in the DMV Building article) | wp:New_Jersey_Division_of_Motor_Vehicles_Building |
| tre_fisher_federal | Clarkson S. Fisher Federal Building and US Courthouse | 1932 | exact: designed by James A. Wetmore and completed in 1932 | wp:Clarkson_S._Fisher_Federal_Building_and_United_States_Courthouse |
| tre_mercer_courthouse | Mercer County Courthouse | 1903 | estimate: cornerstone laid May 14, 1902; the Greek Revival courthouse it replaced served until 1903 | wp:Mercer_County_Courthouse_(New_Jersey) |
| tre_mercer_criminal_courthouse | Mercer County Criminal Courthouse | 2013 | exact: opened January 14, 2013 | wp:Mercer_County_Courthouse_(New_Jersey) |
| tre_transit_center | Trenton Transit Center | 1976 | estimate: Penn Central and Amtrak built the new Trenton Rail Station in 1976; the station was renovated 2008 and the page lists rebuilt 1893 1976 2008 | wp:Trenton_Transit_Center |
| tre_thunder_ballpark | Trenton Thunder Ballpark | 1994 | exact: opened May 9, 1994 (groundbreaking September 29, 1993) | wp:Trenton_Thunder_Ballpark |
| tre_adams_sickles | Adams and Sickles Building | 1900 | exact: constructed in 1900 | wp:Adams_and_Sickles_Building |
| tre_american_cigar | American Cigar Company Building | 1903 | exact: Built in 1903 as part of Trenton's cigar industry (NRHP listing; infobox built 1903) | wp:American_Cigar_Company_(Trenton,_New_Jersey) |
| tre_bellevue_school | Bellevue Avenue Colored School | 1883 | exact: built in 1883; two-story Italianate by William B. Thines | wp:Bellevue_Avenue_Colored_School |
| tre_brearley_house | Charles Brearley House | 1855 | exact: built in 1855 | wp:Charles_Brearley_House |
| tre_carver_center | Carver Center (Sunlight Elks Lodge) | 1928 | estimate: auditorium built 1922-23, the two-story building facing Fowler Street 1927-28 (J. Osborne Hunt); footprint may be either | wp:Carver_Center_(Trenton,_New_Jersey) |
| tre_east_trenton_library | East Trenton Public Library (Samuel Dickinson house) | 1796 | estimate: built c. 1796 as the Samuel Dickinson house; library from 1926 | wp:East_Trenton_Public_Library |
| tre_golden_swan | Golden Swan-True American (Caola Building) | 1820 | estimate: three row houses built in sections: Hancock 1815, Voorhees 1820, a third later | wp:Golden_Swan–True_American |
| tre_higbee_school | Higbee Street School | 1857 | exact: built in 1857 (Evernham and Hill) | wp:Higbee_Street_School |
| tre_house_379_w_state | House at 379 West State Street | 1885 | exact: designed by William A. Cambell and ready for occupancy in 1885 | wp:House_at_379_West_State_Street |
| tre_mercer_street_friends | Mercer Street Friends Center | 1858 | exact: built in 1858 | wp:Mercer_Street_Friends_Center |
| tre_old_eagle_tavern | Old Eagle Tavern | 1765 | exact: built in 1765 by Robert Waln | wp:Old_Eagle_Tavern |
| tre_reading_station | Philadelphia and Reading Railroad Freight Station | 1888 | exact: station built in 1888 by the Philadelphia and Reading Railroad | wp:Trenton_station_(Reading_Railroad) |
| tre_sacred_heart | Sacred Heart Church | 1889 | exact: dedicated June 30, 1889 | wp:Sacred_Heart_Church_(Trenton,_New_Jersey) |
| tre_st_michaels | St. Michael's Episcopal Church | 1748 | exact: present building at 140 North Warren Street built 1747-1748, renovated 1810 and 1847-48 | wp:St._Michael's_Church_(Trenton,_New_Jersey) |
| tre_mansion_house | Mansion House (Ellarslie) | 1848 | exact: built as a summer residence for Henry McCall Sr. in 1848 (John Notman) | wp:Mansion_House_(Trenton,_New_Jersey) |
| tre_roebling_machine_shop | Roebling Machine Shop | 1890 | exact: machine shop built in 1890 (further work 1901) | wp:Roebling_Machine_Shop |
| tre_state_house_annex | State House Annex | 1931 | exact: the State House Annex was built between 1927 and 1931 (completion year) | wp:New_Jersey_State_House |
| tre_one_west_state | First Mechanics National Bank (One West State Street) | 1930 | exact: designed by York and Sawyer and built in 1930 | wp:Downtown_Trenton_Commercial_Historic_District |
| tre_roebling_block3_market | Roebling Block 3 (Roebling Market) | 1917 | estimate: Block 3 buildings date 1908-1929 (Clark Street Rope Shop 1917, Engine House 1917, Boiler House 1916, Carpenter Shop 1908, North Extension 1929); which | wp:John_A._Roebling's_Sons_Company,_Trenton_N.J.,_Block_3 |
| tre_old_masonic_temple | Old Masonic Temple | 1793 | exact: historic building built in 1793; moved half a block south to 102 Barrack Street in 1915; now a tourist information centre | wp:Old_Masonic_Temple_(Trenton,_New_Jersey) |
| tre_st_hedwig_church | St. Hedwig's Church | 1904 | exact: Hedwig's church was built in 1904 by Polish immigrants | wp:Trenton,_New_Jersey |
| tre_state_planetarium | New Jersey State Planetarium | 1964 | exact: since its opening in 1964 the State Museum's planetarium has been part of its programming | wp:New_Jersey_State_Museum |
| tre_douglass_house | Douglass House | 1766 | estimate: the oldest section dates to circa 1766; moved from South Broad Street to Mill Hill | wp:Douglass_House_(Trenton,_New_Jersey) |

### New Brunswick

| id | footprint / name | year | basis | page |
|---|---|---|---|---|
| nb_alexander_library | Archibald S. Alexander Library | 1956 | exact: construction began 1953; opened as Rutgers' main library in 1956 | wp:Archibald_S._Alexander_Library |
| nb_college_ave_gym | College Avenue Gymnasium | 1932 | exact: opened 1932 | wp:College_Avenue_Gymnasium |
| nb_state_theatre | State Theatre | 1921 | exact: opened December 26, 1921 (Thomas W. Lamb) | wp:State_Theatre_(New_Brunswick,_New_Jersey) |
| nb_nb_station | New Brunswick railroad station | 1904 | exact: present station building rebuilt October 1903 - September 28, 1904 | wp:New_Brunswick_station |
| nb_christ_church | Christ Church | 1852 | exact: in 1852 the parish replaced the 100-year-old structure and enlarged it using many stones of the first building | wp:Christ_Church,_New_Brunswick,_New_Jersey |
| nb_second_reformed | Second Reformed Church | 1928 | exact: current church designed by Ludlow and Peabody and dedicated in 1928 | wp:Second_Reformed_Church_(New_Brunswick,_New_Jersey) |
| nb_new_jersey_hall | New Jersey Hall | 1889 | exact: section heading New Jersey Hall (1889) | wp:Voorhees_Mall |
| nb_voorhees_hall | Voorhees Hall | 1903 | exact: section heading Voorhees Hall (1903); the main library until Alexander Library opened 1956 | wp:Voorhees_Mall |
| nb_murray_hall | Murray Hall | 1909 | exact: section heading Murray Hall (1909), designed by Douwe D. Hill with a gift from Andrew Carnegie | wp:Voorhees_Mall |
| nb_milledoler_hall | Milledoler Hall | 1910 | exact: section heading Milledoler Hall (1910), originally the Chemistry Building | wp:Voorhees_Mall |
| nb_graduate_school_education | Graduate School of Education Building | 1961 | exact: its present building was constructed in 1961 | wp:Voorhees_Mall |
| nb_van_dyck_hall | Van Dyck Hall | 1928 | exact: Van Dyck Hall was built in 1928 | wp:Voorhees_Mall |
| nb_social_work_school | School of Social Work (former School of Ceramics) | 1922 | exact: built as the home of the School of Ceramics in 1922 | wp:Voorhees_Mall |
| nb_riverstede | Riverstede (Demarest House) | 1868 | exact: George H. Cook erected this Italianate-Victorian brownstone in 1868 | wp:Voorhees_Mall |
| nb_honors_college | Honors College | 2015 | exact: the Honors College was constructed in 2015 | wp:Voorhees_Mall |
| nb_jj_headquarters | Johnson and Johnson World Headquarters | 1983 | exact: the 16-story building opened in 1983 (Pei Cobb Freed and Partners) | wp:Johnson_and_Johnson_Plaza |
| nb_performing_arts_center | New Brunswick Performing Arts Center | 2019 | exact: construction 2017, completed 2019; official opening September 4, 2019 | wp:New_Brunswick_Performing_Arts_Center |
| nb_free_public_library | New Brunswick Free Public Library | 1903 | exact: the main library built 1903 (Carnegie library) | wp:New_Brunswick_Free_Public_Library |
| nb_poile_zedek | Poile Zedek Synagogue | 1923 | exact: built 1923; converted to apartments 2021 within the preserved walls | wp:Poile_Zedek_Synagogue |
| nb_bishop_house | Bishop House | 1852 | exact: erected in 1852 for James Bishop | wp:Bishop_House_(New_Brunswick,_New_Jersey) |
| nb_wood_lawn | Wood Lawn (Neilson House) | 1830 | exact: built by Colonel James Neilson in 1830 | wp:Wood_Lawn_(New_Brunswick,_New_Jersey) |
| nb_sage_library | Gardner A. Sage Library | 1875 | exact: the Sage Library was completed in 1875 (Detlef Lienau) | wp:New_Brunswick_Theological_Seminary |
| nb_hill_center | Hill Center for the Mathematical Sciences | 1971 | exact: Hill Center opened in 1971 | wp:Busch_Campus_of_Rutgers_University |
| nb_scott_hall | Scott Hall | 1963 | exact: a modern structure built in 1963 | wp:Voorhees_Mall |
| nb_aspire | The Aspire | 2015 | exact: tallest-buildings table lists Aspire, 16/17 floors, 2015 (the roll's 1892 is a placeholder) | wp:New_Brunswick,_New_Jersey |
| nb_george_street_410 | 410 George Street | 1989 | exact: tallest-buildings table lists 410 George Street, 11 floors, 1989 (Rothe-Johnson Architects) | wp:New_Brunswick,_New_Jersey |
| nb_university_center | University Center at Easton Avenue | 1994 | exact: tallest-buildings table lists University Center, 12 floors, 1994 | wp:New_Brunswick,_New_Jersey |
| nb_middlesex_courthouse | Middlesex County Courthouse | 1958 | exact: the last of a series of county courthouses was built in 1958; renovated 2003 | wp:Civic_Square,_New_Brunswick |
| nb_middlesex_admin_building | Middlesex County Administration Building | 1999 | exact: a new Administration Building was completed in 1999 | wp:Civic_Square,_New_Brunswick |
| nb_public_safety_building | Civic Square Public Safety Building | 2000 | exact: the Public Safety Building completed in May 2000 | wp:Civic_Square,_New_Brunswick |
| nb_skyline_tower | Skyline Tower | 1967 | exact: 14 stories, originally built in 1967 as the Middlesex County Administrative Building; renovated 2003 as residential | wp:Civic_Square,_New_Brunswick |
| nb_fricano_towers | Schatzman-Fricano Apartments (John P. Fricano Towers) | 1963 | exact: tallest-buildings table lists Schatzman-Fricano Apartments, 14 floors, 1963 | wp:New_Brunswick,_New_Jersey |
| nb_george_apartments | The George | 2013 | exact: tallest-buildings table lists The George, 14 floors, 2013 | wp:New_Brunswick,_New_Jersey |
| nb_one_spring_street | 1 Spring Street | 2006 | exact: tallest-buildings table lists 1 Spring Street, 23 floors, 2006 (Costas Kondylis) | wp:New_Brunswick,_New_Jersey |
| nb_jersey_mikes_arena | Jersey Mike's Arena (Rutgers Athletic Center) | 1977 | exact: opened November 30, 1977 as the Rutgers Athletic Center (the roll's 2012 is a later renovation) | wp:Jersey_Mike's_Arena |
| nb_william_levine_hall | William Levine Hall (Pharmacy) | 1963 | exact: the original four-wing building was opened in 1963 | wp:Busch_Campus_of_Rutgers_University |
| nb_cabm | Center for Advanced Biotechnology and Medicine | 1990 | exact: the CABM building was completed in 1990 (100,000 sq ft of laboratories and offices) | wp:Busch_Campus_of_Rutgers_University |
| nb_saint_peters_cares | Saint Peter's Center for Ambulatory Resources | 1999 | exact: in 1999 the Center for Ambulatory Resources (CARES) building was constructed | wp:Saint_Peter's_University_Hospital |
| nb_childrens_specialized_hospital | Children's Specialized Hospital | 2007 | estimate: the article is categorised Hospital buildings completed in 2007; no sentence in the text gives the year | wp:Children's_Specialized_Hospital |
| nb_bms_childrens_hospital | The Bristol-Myers Squibb Children's Hospital | 2007 | estimate: infobox says constructed 1998 (lower floors) and 2007 (upper floors added); the text says groundbreaking June 1998 and opened January 2007 | wp:The_Bristol-Myers_Squibb_Children's_Hospital |

## Not dated (largest footprints in the brief's classes with no opened source)
Trenton: Capital Health Regional Medical Center (14,778 m2), Trenton Water Filtration Plant (12,006), Roebling Lofts (2,597; one of the Block 3 buildings, which
one is not known), Trenton Central High School's building of 2019 (no footprint at the Wikipedia coordinates), the State Prison's cell blocks (Front House 1798,
Fortress Penitentiary 1832-36 and the 1982 prison are cited by the article but the footprints could not be told apart), Trenton Psychiatric Hospital (opened 1848;
its buildings unidentified), State Library (2,114), Department of Environmental Protection, State Office buildings, Trenton Fire Headquarters (4,407), Trenton Free
Public Library and City Hall Annex (roll heap years), Hotels of State Street (Lafayette Park Hotel 2002 on the roll). The Trinity Cathedral (dedicated 24 Jan 1954) was not located.
New Brunswick: Robert Wood Johnson University Hospital main block (20,096 m2; additions of 1916 and 1958 are cited, the footprint's year is not),
Saint Peter's main hospital (1907 foundation, 1959 and 1976 additions: no footprint identified), Hyatt Regency (10,213), the Heldrich (roll 2007 is consistent
with the article), Rutgers' Livingston and Cook-Douglass buildings (Tillett, Lucy Stone, Foran, Douglass Library, Cook Student Center: no page opened),
Weeks Hall, Busch Student Center and Dining Hall (the roll's 1944 is a placeholder), Zimmerli Art Museum building (roll 1900 heap), the Cancer Institute (5,576).

## Models (`NJ_TOWNS`, 14)
Plans are the real footprints (simplified to 0.35 m, anchored at the representative point); `replaces` is the footprint. Numeric check by `check.ts`
(plan rasterised at 0.5 m; `outside` = plan outside the replaced outline). All plans within 10 % of the footprint (the largest excess: Broad Street National
Bank +7 %, Kirkpatrick Chapel +6 %, City Hall +5 %); every cited top is matched to under 0.01 m.

| id | footprint (parquet id) | built | top (m) | basis of the top | plan m2 | footprint m2 | outside m2 |
|---|---|---|---|---|---|---|---|
| trn_hughes_justice | 55180346 | 1979.5-1982.5 | 41.62 | cited (Wikipedia: eleven storeys, 41.62 m); wings 30 m estimated | 9145 | 9192 | 0 |
| trn_st_mary_cathedral | a6854ba1 | 1957-1959.2 | 29.87 | cited (bell tower 98 ft); nave 10.5 m, which end is the front: estimated | 1635 | 1640 | 2 |
| trn_broad_street_bank | 2a126f24 | 1899-1900.5 | 54.8 | footprint's measured roof height (no figure published) | 2338 | 2199 | 152 (cornice) |
| trn_mercer_courthouse | eef1c480 | 1902.4-1903.5 | 27.1 | footprint's measured roof height, read as a central drum and dome (estimated form) | 3074 | 2970 | 116 (portico) |
| trn_city_hall | d17d69d6 | 1907.5-1910 | 21.2 | footprint's measured roof height, hipped roof estimated | 1489 | 1416 | 78 |
| trn_roebling_machine_shop | d854f05d | 1889.6-1890.8 | 16.2 | footprint's measured roof height, clerestory gable estimated | 5914 | 5950 | 0 |
| trn_cure_arena | b3aba644 | 1997.9-1999.8 | 18.0 | estimated (footprint's measured height is 11.9 m, an average); 12 m walls + 6 m barrel roof | 9167 | 9216 | 0 |
| nb_jj_headquarters | 729e7648 | 1980-1983.5 | 70.0 | cited (infobox roof 70 m, 16 storeys); tower plan and place estimated | 6310 | 6346 | 2 |
| nb_performing_arts_center | 18195d41 | 2017.5-2019.67 | 89.61 | cited (infobox roof 89.61 m, 23 storeys); podium 22 m estimated | 2685 | 2694 | 0 |
| nb_gateway | 83fbc3e2 | 2010-2012.5 | 90.83 | cited (298 ft roof, 23 storeys); tower placed near Wikipedia's coordinates, plan estimated | 3939 | 3952 | 0 |
| nb_kirkpatrick_chapel | e0f294f4 | 1872-1873.4 | 16.76 | cited (55 ft; 116 x 57.5 ft = 620 m2 against the footprint's 602) | 634 | 602 | 35 (buttresses) |
| nb_winants_hall | dff6b486 | 1888.5-1890.5 | 18.0 | estimated (walls 13 m = footprint's measured height; hip roof 4.6 m) | 921 | 925 | 1 |
| nb_state_theatre | c102f56f | 1920.5-1921.99 | 23.6 | estimated (no figure; stage house) | 2205 | 2212 | 0 |
| nb_voorhees_hall | eeafb7e0 | 1902-1903.9 | 16.8 | estimated (no figure; 1903 date cited) | 2127 | 2082 | 53 |

Per model, what is estimated (also in each `Model:` fact): construction starts (the opening / completion year is cited, the start is not, except
the cornerstone of the courthouse, the groundbreaking of CURE Arena and the construction years of the Performing Arts Center); all roofs, set-backs, colours,
which end of a church or theatre is the front, and the places of the towers on complexes. Not modelled for lack of a cited height and a distinct
form: Geology Hall, New Brunswick station (1904, 520 m2), Christ Church, SHI Stadium (Piscataway: stands, not a building footprint), the Trenton
Transit Center, the Trenton Bath House (in Ewing, no footprint named), the State Prison's front house.

## Things that look wrong in existing tables or models
- `known_building_dates.nj_outer.csv`: the Trenton War Memorial row starts 1930 ("built 1930-1932, opened 1932"); every other row is the completion year,
  and Trenton's Wikipedia article says "Completed in 1932" (the roll also says 1932). Wikidata gives the Trenton Central High School as 1932; that building was
  demolished and replaced in September 2019, so the roll's year for its footprint, if any, is right only for the new school.
- Wikipedia's Johnson & Johnson Plaza infobox says completed 1982, its text and the New Brunswick tallest-buildings table say 1983 (used).
- Wikidata dates the Anderson-Capner House 1709; its article says 1764 (no footprint at the coordinates, not written).
