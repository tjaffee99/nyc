# places_counties.csv — era-accurate place-name labels for the eight counties around the city

Hudson, Bergen, Essex, Union, Passaic (New Jersey) and Westchester, Nassau, Rockland (New York).
Same columns and conventions as `places.csv` (see `places_README.md`): one row per **name period**
(475 rows); a label is shown iff `year_start <= year < year_end` (`9999` = still in use).
Research collected 2026-11; the three sister tables are described at the end.

| column | meaning |
|---|---|
| `id` | stable id, prefixed by the county of the anchor: `hud_` `ber_` `ess_` `uni_` `pas_` `wes_` `nas_` `roc_`; three rows `reg_` (New Jersey / East Jersey). No id collides with `places.csv` |
| `name` | label text as used in that period |
| `tier` | `region` (the counties and their predecessors, New Jersey / East Jersey — 15) · `city` (Jersey City, Hoboken, Bayonne, Union City, Newark, Elizabeth, Paterson, Passaic, Clifton, Yonkers, Mount Vernon, New Rochelle, White Plains from the year of their city charter — 13) · `town` (every other municipality, the same cities before their charter, earlier names of the same places, and the larger hamlets — 351) · `neighborhood` (absorbed places and planned suburbs: Paulus Hook, Harsimus, Communipaw, Bergen Square, The Heights, Greenville, Journal Square, Newport, Ironbound, Forest Hill, Roseville, Woodside, Vailsburg, Weequahic, Short Hills, Llewellyn Park, Radburn, Elizabethport — 18) · `historic` (Lenape places and bands, patroonships and manors, short-lived names, airfields — 38) · `landscape` (40) |
| `lat`,`lon` | WGS84 label anchor, 5 decimals (see "Coordinates") |
| `year_start`, `year_end` | as in `places.csv` |
| `replaced_by` | `id` of the next name of the same place (93 rows are links of a chain; no gaps: every `year_end` equals the next `year_start`) |
| `county` | `Hudson`, `Bergen`, `Essex`, `Union`, `Passaic`, `Westchester`, `Nassau`, `Rockland`; blank for the 16 rows shared by several counties |
| `note` | what the dates mean. **"estimated"** = the year is not stated as such in the cited article (94 rows; 49 of them were flagged by the check below and say "not found in the cited article"); **"nominal"** = a conventional start (167 rows: 140 municipalities that carry their year of incorporation, the rest natural features and the Dutch-to-English switch of 1664); **"approximate"** = location known only roughly (8 rows). 211 rows carry none of the three words |
| `source_url` | the Wikipedia article supporting the name and year |

Rows per county: Hudson 45, Bergen 88, Essex 41, Union 29, Passaic 25, Westchester 70, Rockland 43, Nassau 118, shared 16.
364 rows are current names; 18 rows start in 1609 (Lenape places: the first year of the map, not a founding date).

## What is in it

* **Every municipality of the five New Jersey counties** (141: Bergen 70, Hudson 12, Essex 22, Union 21, Passaic 16).
* **New York**: Westchester's 6 cities, its towns (the Town of Rye is not a separate label), and its villages
  (Harrison, Mamaroneck, Pelham, Scarsdale, Mount Kisco and Ossining appear once, not as town and village);
  Rockland's 5 towns and 19 villages (South Nyack, dissolved in 2022, is kept); Nassau's 2 cities, 3 towns and 64 villages.
* **Hamlets** (unincorporated, tier `town`): Chappaqua, Katonah, Armonk; Tappan, Palisades, New City, Pearl River, Nanuet, Doodletown;
  Levittown, Hicksville, Jericho, Manhasset, Port Washington, Massapequa, Merrick, East Meadow, Oceanside, Elmont, Syosset,
  Locust Valley, Baldwin, Uniondale, Franklin Square, Seaford, Bellmore, Plainview, Woodmere, Inwood, Roosevelt, East Norwich, Bethpage, Wantagh.
* **Name chains**, for example: `Aressick` → `Paulus Hook` 1638 → `Jersey` 1804 → `Jersey City` 1838; `Hopoghan Hackingh` → `Hoebuck` 1630 → `Hoboken` 1784 (city 1855);
  `Ahasimus` → `Harsimus` 1634 → `Van Vorst` 1841 → `Harsimus` (neighbourhood) 1851; `Gemoenepaen` 1634 → `Communipaw`; `Bergen` 1660 → `Bergen Square` 1870;
  `West Hoboken` + `Union Hill` → `Union City` 1925; `Achter Kol` → `Newark Bay`; `English Neighborhood` 1668 → `Ridgefield` 1871; `Liberty Pole` → `Englewood` 1859;
  `Godwinville` → `Ridgewood` 1866; `Boiling Springs` → `Rutherford` 1881; `Union` → `Lyndhurst` 1917; `East Paterson` → `Elmwood Park` 1973; `Delford` → `Oradell`;
  `Schraalenburgh` → `Dumont`; `New Bridge` → `Riverside` → `River Edge`; `Etna` → `Emerson`; `Undercliff` → `Edgewater`; `Newark` town 1666 → city 1836;
  `Newark Mountains` → `Orange` 1780; `Camptown` → `Irvington` 1852; `Wardsesson` → `Bloomfield`; `Cranetown` → `West Bloomfield` → `Montclair` 1860;
  `Second River` → `Belleville` 1797; `Franklin` → `Nutley` 1902; `Horseneck` → `Caldwell` 1798; `Elizabethtown` 1664 → `Elizabeth` 1855; `Connecticut Farms` → `Union` 1808;
  `Spanktown` → `Rahway`; `Turkey` → `New Providence`; `New Orange` → `Kenilworth`; `Acquackanonk` → `Acquackanonk Landing` 1679 → `Passaic` 1854 (city 1873);
  `Paterson` 1791 (city 1851); `West Paterson` → `Woodland Park` 2009; `Long Pond` → `Greenwood Lake`; `Nappeckamack` → `Colen Donck` 1646 → `Yonkers` (city 1872);
  `Manor of Cortlandt` → `Cortlandt` 1788; `Quarropas` → `White Plains` 1683 (city 1916); `Peningo` → `Hastings` 1660 → `Rye` 1665; `Manor of Pelham` → `Pelham`;
  `Saw Pit` → `Port Chester` 1837; `Sing Sing` 1813 → `Ossining` 1901; `Dearman` → `Irvington` 1854; `North Tarrytown` → `Sleepy Hollow` 1996; `Stephentown` → `Somers`;
  `Croton Lake` → `New Croton Reservoir`; `Tappan` (Lenape) → `Tappan` 1686; `Rumachenanck` → `Haverstraw`; `New Hampstead` → `Ramapo` 1828; `Tappan Slote` → `Piermont` 1839;
  `Sneden's Landing` → `Palisades`; `New Antrim` → `Suffern`; `Verdrietige Hoek` → `Hook Mountain`; `Heemstede` 1644 → `Hempstead`; `Musketa Cove` → `Glen Cove` 1834;
  `Raynortown` → `Freeport`; `Pearsalls` → `Lynbrook`; `Hempstead Harbor` → `Roslyn` 1844; `Central Park` → `Bethpage` 1936; `Jerusalem` → `Wantagh`;
  `Island Trees` → `Levittown` 1947; `Cow Bay` → `Manhasset Bay` 1907; `Success Pond` → `Lake Success`.
* **Counties**: `Bergen County` 1683 (also as the label of today's Hudson until `Hudson County` 1840), `Essex County` 1683 (also over today's Union until `Union County` 1857),
  `Passaic County` 1837, `Westchester County` 1683 (anchored in the present county; the city's table keeps its own label in the Bronx until 1874),
  `Queens County` 1683 → `Nassau County` 1899, `Orange County` 1683 → `Rockland County` 1798.
* **Lenape places and bands** with a documented location (`historic`, start 1609, every end year an estimate or the first land sale): Hopoghan Hackingh, Aressick, Ahasimus,
  Achkinheshacky (Hackensack), Acquackanonk, Pompton, Wiechquaesgeck, Nappeckamack, Quarropas, Peningo, Siwanoy, Sint Sinck, Kitchawank, Tappan, Rumachenanck (Haverstraw),
  Marsapeague (Massapequa, at Fort Massapeag), Meroke (Merrick), Matinecock.
* **Landscape**: the Palisades, Hackensack Meadows → the Meadowlands (1969), Achter Kol → Newark Bay, Hackensack and Passaic rivers, the Watchungs, the Ramapos, Great Falls,
  Long Pond → Greenwood Lake, Snake Hill, Constable Hook, Bergen Point, New Barbadoes Neck, Tappan Zee, Haverstraw Bay, the Hudson Highlands, Croton Point, Kensico Reservoir,
  Croton Lake → New Croton Reservoir, Verdrietige Hoek → Hook Mountain, Stony Point, High Tor, Rockland Lake, Bear Mountain, Hempstead Plains, Hempstead Harbor,
  Cow Bay → Manhasset Bay, Cow Neck, Great Neck, Oyster Bay Harbor, Jones Beach, South Oyster Bay, Success Pond → Lake Success.

## How the years were made and checked

* The rows were written by hand (`tools/counties/places_ca.txt` … `places_cd.txt`) and built by `tools/counties/make_places_counties.py`.
* **140 municipalities carry their year of incorporation**, read by the script from the cited article ("incorporated as a borough … on …", the infobox, or the first
  "incorporated … year" sentence) and then read over by eye. Their note says so and says "nominal start": the place and often the name are older, and that was not researched.
  Seen on the map this gives a wave of labels in 1894 (Bergen County's "boroughitis") and in 1926-1932 (Nassau's estate villages) that is a legal, not a settlement, fact.
* For every other row the script looked for `year_start` and `year_end` in the cited article. 49 rows whose year is not there were flagged
  "Year … not found in the cited article: estimated." Some of those years are certainly right (Bergen joined Jersey City in 1870) but stand in another article.
  Years corrected from the articles: Harsimus 1634, English Neighborhood 1668, New Bridge 1744, Bloomfield 1794, Tarrytown 1645, East Meadow 1655, Harrison (NY) 1696, Wallington 1895.
  The check proves that the year appears in the article, not that the sentence says what the note says.
* Dutch → English switches are dated to 1664 (nominal) as in `places.csv`.

## Coordinates

* 373 rows: coordinates of the cited Wikipedia article (MediaWiki API, 2026-11). For a municipality that is the article's point, usually the centre of the built-up area or the
  municipal building, **not a researched historic core**.
* 31 rows: coordinates of the Wikipedia article of the historic core named in the note or in `tools/counties/places_counties_coordsrc.json` — Paulus Hook, Bergen Square,
  Four Corners (Newark), First Presbyterian Church of Elizabeth, Bergen County Court House on the Hackensack Green, Bloomfield Green, Fort Lee Historic Park, New Bridge Landing,
  Philipse Manor Hall (Yonkers), Philipsburg Manor House, Van Cortlandt Manor, Old Dutch Church of Sleepy Hollow, Tappan Historic District, Stony Point Battlefield,
  Hempstead village, Oyster Bay hamlet, Fort Massapeag, Ringwood Manor, Springfield (CDP).
* 71 rows are hand-placed from general knowledge (regions, rivers and ridges, vanished places, and 11 municipalities whose article point fell in woods, marsh or an industrial tract:
  Kearny, Secaucus, Mahwah, Alpine, East Rutherford, Englewood Cliffs, Norwood, West Orange, West Milford, Bloomingdale, Chestnut Ridge, plus White Plains and Rye at the
  old court house site and the Square House). Treat them as good to a few hundred metres.
* OpenStreetMap place nodes could not be used: the Overpass servers were not reachable from this session. Nothing was checked with `footprint_at.py` (no anchor lies in the city's box).
* Checks made (`tools/counties/check_places_counties.py`): every anchor lies in the box (40.47-41.38, -74.52 to -73.40) and inside its county (TIGER 2024 outlines);
  every `city` / `town` / `neighborhood` anchor has at least 15 Overture footprints within about 300 m except Teterboro (airport), Rockleigh, Ringwood (at the manor),
  Cortlandt, North Salem, North Castle (rural towns), Doodletown (vacated), Chestnut Ridge, Centre Island and Cove Neck (estates).

## Known gaps and caveats

* **Naming years of most small municipalities are not researched** (see above). Researched earlier names exist only for the places listed under "Name chains".
* **Not included**: neighbourhoods of the cities other than the 18 listed (nothing for Paterson, Elizabeth, Yonkers, New Rochelle, Bayonne, Hoboken); hamlets and CDPs not listed above
  (among them Hartsdale, Valhalla, Purchase, Verplanck, Montrose, Yorktown Heights, Congers, Monsey, Orangeburg, Blauvelt, Sparkill, West Nyack, Stony Point hamlet, Tomkins Cove, Garnerville,
  Carle Place, Albertson, Glen Head, Greenvale, West Hempstead, Hewlett, Point Lookout, Old Bethpage, Woodbury); the former townships as such (Acquackanonk, Saddle River, Franklin, Harrington,
  Hackensack Township, Pompton, Manchester, Hohokus, Orvil); the Town of Rye; the Raritan band (their country lay south of Union County, on the Raritan) and the Rockaway band
  (in the city's table as Reckouwacky); the harbours and necks of the Sound shore in Westchester; smaller rivers (Saddle, Ramapo, Rahway, Elizabeth, Saw Mill, Croton, Bronx); airports and parks (own tables).
* **Uncertain identifications and conflicting dates**: Achkinheshacky, Achter Col, Pompton, Siwanoy, Sint Sinck, Kitchawank, Meroke and Matinecock are placed approximately; the end of Colen Donck (1672)
  and the start of "Yonkers" as a label are estimates; New Providence was renamed in 1759 by tradition, 1778 in other accounts; Bloomfield's naming is 1794 (society) or 1796;
  Suffern (1796), Palisades (1870), Greenwood Lake (1860), Rockland Lake (1835), Ironbound (1900), Franklin Square, Maplewood, Elizabethport, Massapequa are decade-level estimates.
* `New Barbadoes` (the township, 1693-1921) and `Hackensack` (its village) are shown side by side, 1 km apart, by design.
* The two New Jersey region labels (`New Jersey`, `East Jersey`) are anchored west of Newark; the lead may prefer to drop them at close zooms.
* 475 rows is slightly over the 300-450 asked for; dropping the 140 incorporation-only rows would leave the researched 335.

## The sister tables (same folder; generators in `tools/counties/`, run `validate_counties.py` after any rebuild)

* `population_counties.csv` (246 rows): the **present area** of each county at every census 1790-2020 and the 1 July 2025 estimate, colonial counts, and the 1682 account of East Jersey.
  Boundary changes: Hudson (1840), Passaic (1837), Union (1857) and Bergen's Union township (1852) are rebuilt from the township returns of 1810-1850 in the
  New Jersey Compendium of Censuses 1726-1905 (read from the page images; each year's townships add up to the county total); townships later cut by a county line
  (Saddle River / Manchester, New Barbadoes and Lodi / Harrison, Harrison / Union, Springfield / Millburn) are split by the first count after the cut, which makes those rows estimates.
  No township returns exist for 1790 and 1800 or for the colonial censuses: those years are split by the 1810 shares. Westchester and Nassau before 1900 are the Census Bureau's own
  present-area figures (Forstall 1996, New York notes 3 and 11), the complements of the city's `bronx` and `queens` rows. Rockland 1790 = Haverstraw + Orangetown.
  The word "estimate" in a note marks every figure that is not a count or a sum of counted towns (109 rows).
* `events_counties.csv` (49 rows): none repeats `events.csv`. A month or day is given only where the cited article states the full date. Two years are not confirmed by the cited
  article: the Paterson and Hudson River Railroad (1832 here; the article says the railroad "was started in 1833") and Port Newark (1915).
* `parks_counties.csv` (55 rows): `name` is the OpenStreetMap name of the outline, checked against the Overture land-use extract. 41 `exact` (the year stands in the cited article),
  14 `estimated`. **Names shared by several outlines in the region** (the pipeline matches by name): `Lincoln Park` (this row: Jersey City), `Mount Pleasant Cemetery` (Newark; another in Westchester),
  `Evergreen Cemetery` (Hillside), `Gate of Heaven Cemetery` (Mount Pleasant, Westchester), `Eastside Park` (Paterson), `Military Park` (Newark) — match these with the county as well.

## Sources and licences

* Names, dates and 404 coordinates: English Wikipedia (text CC BY-SA 4.0; facts and coordinates only; each row carries its article URL).
* Population: US Census Bureau publications (public domain); New Jersey Department of State, Compendium of Censuses 1726-1905 (1906, public domain, Internet Archive scan);
  Samuel Smith, History of the Colony of Nova-Caesaria (1765, public domain).
* Checks only: TIGER/Line 2024 county outlines (public domain); Overture Maps buildings and land use, which carry OpenStreetMap data (ODbL) — the park names in `parks_counties.csv` are OpenStreetMap names.
