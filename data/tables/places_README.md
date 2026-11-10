# places.csv — era-accurate place-name labels for the five boroughs

One row per **name period** of a place (447 rows). A label is shown iff
`year_start <= year < year_end` (same rule as features; `9999` = still in use).

| column | meaning |
|---|---|
| `id` | stable id, prefixed by borough: `mn_` Manhattan, `bk_` Brooklyn, `qn_` Queens, `bx_` the Bronx, `si_` Staten Island, `reg_` counties / boroughs / colonial regions, `ls_` waters and landscape shared by several boroughs |
| `name` | label text as used in that period |
| `tier` | `region` (Lenapehoking, Nieuw-Nederland, the counties and boroughs — 14) · `city` (Nieuw Amsterdam / New York / New Orange, City of Brooklyn, Long Island City — 7) · `town` (Dutch and English towns and villages while they were separate places — 47) · `neighborhood` (219) · `historic` (Lenape places, forts, vanished villages and districts, short-lived names — 68) · `landscape` (islands, rivers, bays, kills, hills, points, meadows — 92) |
| `lat`,`lon` | WGS84 label anchor, 5 decimals |
| `year_start` | first year the name was in use for the place (founding, patent, naming, subdivision — `note` says which) |
| `year_end` | first year it was no longer the label (rename, annexation, demolition); `9999` = current |
| `replaced_by` | `id` of the next name for the same place (119 rows are links of a chain). Usually `year_end` of the old row = `year_start` of the new one; deliberate gaps: Snakapins 1643 → Cornell's Neck 1646, Gas House District 1945 → Stuyvesant Town 1947, Washington Market 1967 → Tribeca 1973, Catholic Protectory 1938 → Parkchester 1940, Freedomland 1964 → Co-op City 1968 |
| `county` | the borough (`Manhattan`, `Brooklyn`, `Queens`, `The Bronx`, `Staten Island`); blank for city-wide regions and shared waters (32 rows) |
| `note` | what the dates mean. **"estimated"** marks any year not stated as such in the source (230 rows); **"nominal"** marks a conventional year where no naming date exists (52 rows); **"approximate"** marks a location known only roughly (12 rows) |
| `source_url` | the page supporting the name and year (Wikipedia articles, CC BY-SA) |

Rows per borough: Manhattan 121, Brooklyn 90, Queens 82, the Bronx 63, Staten Island 59, city-wide 32.
282 rows are current names (`year_end` = 9999).

## Conventions

* **Renames are chains** via `replaced_by`, for example:
  `Nieuw Amsterdam` 1625 → `New York` 1664 → `New Orange` 1673 → `New York` 1674 (the last moves from the Wall Street city hall to today's City Hall in 1812);
  `Fort Amsterdam` → `Fort James` → `Fort Willem Hendrick` → `Fort James` → `Fort William Henry` → `Fort Anne` → `Fort George` (–1790);
  `Minnehanonck` → `Varkens Eylandt` 1637 → `Manning's Island` → `Blackwell's Island` 1686 → `Welfare Island` 1921 → `Roosevelt Island` 1973;
  `Pagganck` → `Noten Eylandt` 1624 → `Nutten Island` 1664 → `Governors Island` 1784;
  `Great Oyster Island` → `Bedloe's Island` 1667 → `Liberty Island` 1956;
  `Little Oyster Island` → `Gibbet Island` → `Ellis Island`;
  `Sapohanikan` → `Noortwyck` → `Greenwich` 1713 → `Greenwich Village`;
  `Midwout` 1651 → `Flatbush`; `Nieuw Amersfoort` 1636 → `Flatlands`; `Boswijck` 1661 → `Bushwick`; `Vlissingen` 1645 → `Flushing`; `Middelburgh` 1652 → `Newtown` → `Elmhurst` 1896; `Rustdorp` 1656 → `Jamaica`; `Hallett's Cove` 1652 → `Astoria` 1839; `Oostdorp` 1654 → `Westchester` → `Westchester Square` 1895; `Bronck's Land` 1639 → `Morrisania`; `Cocclestown` → `Richmond` → `Richmondtown`; `Linoleumville` 1873 → `Travis`; `Longacre Square` → `Times Square` 1904; `San Juan Hill` → `Lincoln Square` 1959; `Yellow Hook` → `Bay Ridge` 1853; `Crow Hill` → `Crown Heights` 1916; `Brushville` 1824 → `Queens` → `Queens Village` 1923.
* **Dutch → English name switches** are dated to the takeover of 1664 unless a source dates the change; those rows say "nominal".
* **Towns that were absorbed** get two rows: `town` until annexation or absorption, then `neighborhood` (Harlem, Greenwich Village, Yorkville, Manhattanville, Flatbush, Flatlands, Gravesend, Bushwick, Flushing, Jamaica, Astoria, Morrisania, Fordham, West Farms). Annexation years used: Williamsburgh and Bushwick 1855 (act of 1854, in effect 1 Jan 1855), the west Bronx towns 1874, New Lots 1886, Flatbush / Gravesend / New Utrecht 1894, the east Bronx 1895, Flatlands 1896, everything else at the consolidation of 1 Jan 1898.
* **Counties and boroughs**: the county labels of 1683 hand over to the borough labels in 1898 (the counties continue to exist). The Bronx is `Westchester County` 1683 → `Annexed District` 1874 → `The Bronx` 1898; Staten Island is `Richmond County` → `Richmond` (borough) 1898 → `Staten Island` 1975. Island labels (`Manhattan Island`, `Staten Island`) run as `landscape` until the borough takes the name.
* **Lenape places** (`historic`, 24 rows with start 1609): only places with a documented location (Sapohanikan, Werpoes, Shorakapkok, Konaande Kongh, Nechtanc, Kapsee, Muscoota, Marechkawieck, Keskachauge, Canarsee, Nayack, Ihpetonga, Mespaetches, Jameco, Snakapins, Ranachqua, Nipinichsen, Aquehonga Manacknong, the island names) and the bands of the area (Wecquaesgeek, Siwanoy, Matinecock, Reckouwacky). Their `year_start` is 1609, the first year of the map, not a founding date; every end year is estimated (the land sale or the founding of the colonial village on the spot).
* **Natural features with no documented naming date** (Upper Bay, Lower Bay, the Narrows, Long Island Sound, Flushing Bay …) start in 1664 or 1700 and say "nominal" or "estimated"; features with a known naming carry it (Hellegat 1614, Bronx River 1639, Hutchinson River 1643).
* Neighbourhood names coined late carry the coinage year: SoHo 1962, Tribeca 1973 (estimated), NoHo 1976 (estimated), Dumbo 1978, Boerum Hill 1964, Prospect Lefferts Gardens 1968, Sunset Park 1965 (estimated), East Village 1964 (estimated), Nolita 1996 (estimated), Hell's Kitchen 1881, Times Square 1904, Co-op City 1968, Starrett City 1974, Hudson Yards 2019.

## Coordinates

* 165 rows use the coordinates of the cited Wikipedia article (fetched through the MediaWiki API, 2026-11).
* 282 rows are hand-placed (from general knowledge of the place, not read off a georeferenced map or gazetteer) at the historic core or at a point named in the note: the old village centres of the colonial towns, vanished places, name chains (every link of a chain shares one anchor), waters and region labels.
* Checks made: every anchor falls inside its borough (TIGER 2024 county outlines; only the Long Island Sound label lies outside the city, by design); every `city` / `town` / `neighborhood` anchor has at least 15 building footprints within about 300 m, except Port Ivory (industrial); the colonial town anchors were compared with the city's designated landmarks (`lpc_individual_landmarks.geojson`): Flatbush Reformed Church 50 m, Flatlands Reformed Church 45 m, New Utrecht Reformed Church 44 m, Van Sicklen House in Gravesend 55 m, Brooklyn City Hall 98 m, Flushing Friends Meeting House 46 m, Reformed Church of Newtown 82 m, Grace Church in Jamaica 25 m, New Lots Reformed Church 86 m, Westchester Square 115 m, Voorlezer's House in Richmondtown 192 m, City Hall 5 m, the Custom House on the Fort Amsterdam site 7 m.
* Not checked against anything but the borough outline: the other hand-placed anchors (Lenape places, 19th-century villages such as Carmansville, Bloomingdale, Harsenville, Strattonport, Factoryville, and the landscape labels). Treat them as good to a few hundred metres.

## How the years were checked

For every row not flagged estimated / nominal / approximate (171 rows) the cited article was downloaded and searched for `year_start` and `year_end`. Rows whose year was not in the article were corrected from the article (Washington Market 1813, Carnegie Hill 1901, West Farms patent 1666, Douglaston 1866, Prohibition Park 1877) or flagged "estimated" (37 rows). Eight rows remain whose year is an administrative date not repeated in the cited article: counties created 1683, Bushwick 1855, the 1874 annexation (Fordham, West Farms), consolidation 1898 (Downtown Brooklyn, Richmondtown). The check proves the year appears in the article, not that the sentence says what the note says.

## Known gaps and caveats

* **Estimated years are the majority** (230 of 447): most neighbourhood names have no naming date in their article, so the year is the decade of development or of the event the name refers to.
* **Not included**: the five colonial towns of Staten Island (Castleton, Northfield, Southfield, Westfield, Middletown) and the villages of Edgewater and New Brighton as municipalities; the Town of Hempstead's hold on the Rockaways before 1898; Eastchester and Pelham as towns; many present-day neighbourhoods (Manhattan: West Village, Bowery, Two Bridges, Civic Center, Theater District, NoMad, Koreatown, Hudson Heights, Manhattan Valley; Brooklyn: Ocean Hill, Stuyvesant Heights, Greenwood Heights, Homecrest, Madison; Queens: Briarwood, Bellerose, Glen Oaks, Auburndale, Malba, Beechhurst, South Ozone Park, South Jamaica, LeFrak City; the Bronx: Morris Heights, Mount Hope, Allerton, Pelham Parkway, Edenwald, Schuylerville; Staten Island: Sunnyside, Emerson Hill, Elm Park, Arlington, Richmond Valley); Lenape places known only by name; airports and parks (they have their own tables).
* **Uncertain identifications**: the Lenape name Minnehanonck is given by different sources to Roosevelt Island and to Randalls Island (used here for Roosevelt Island only); Kapsee, Werpoes, Konaande Kongh, Nipinichsen, Mespaetches and Stony Brook are placed approximately; Oude Dorp is placed near South Beach although its one surviving house stands 2.6 km inland.
* **Conflicting sources**: New Amsterdam's start (fort laid out 1625, used here; settlers on Governors Island 1624); Bushwick's annexation (1854 act, 1855 in effect); Corona's renaming (1870 or 1872); Duane Park (1795 or 1797, see parks.csv); Marble Hill is in the borough of Manhattan although on the mainland since 1914.
* `Lenapehoking` is a modern word used as the regional label; its end year (1700) is an estimate.
* Research collected 2026-11 from Wikipedia; verify before treating any single date as authoritative.

## Sources and licences

* Names, dates and 165 coordinates: English Wikipedia articles (text CC BY-SA 4.0; facts and coordinates only, each row carries its article URL).
* Checks only (nothing copied into the table): US Census Bureau TIGER/Line 2024 county outlines (public domain), NYC Landmarks Preservation Commission individual landmarks and NYC building footprints (NYC Open Data).
* The rows were written by hand in `data/interim/tables/places_a.txt` … `places_d.txt` with corrections in `places_fix.json` and assembled by `make_places.py` in the same (gitignored) folder; `places.csv` is the copy of record.
