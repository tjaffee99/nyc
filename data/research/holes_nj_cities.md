# Holes in New Jersey's inner cities (round of 2026-11-12)

Method: the 36 largest holes of `data/interim/reports/holes.csv` in New Jersey (same hole merged across years, 0.006 x 0.005
degrees), each drawn over the built buildings, Overture roads and rail (`holes_nj_cities_build/render.py`, `named.py`, images in
`data/interim/holes_nj_cities_raw/*.png`) and matched to Overture land use (`cluster.py`). Facts from Wikipedia raw wikitext
(`data/interim/holes_nj_cities_raw/wp_*.txt`, paced, User-Agent `NYCThroughTime-research/0.1`), the Centre for Land Use
Interpretation's Meadowlands pages, Newark Changing's table, search results (marked "snippet"). No plan of any works or yard was
opened: sources give years and points, not outlines.

**The main finding.** Most of the large 1980 holes are not missing buildings. They are parking lots (malls, stadiums), highway
interchanges, rail corridors, airfields and a state park: ground the terrain turns to "city" and that really held no building.
The holes that are missing buildings are Newark's Central Ward (cleared district, years too early), a few lost works whose
outline no source gives, and Paterson, whose whole city is thin before 1920 (below).

## Written

- `data/tables/notable_demolished.nj_cities.csv`: Giants Stadium 1976-2010 and Meadowlands Arena 1981-2016 (both at the
  article's coordinates, +-50 m; the arena's end year and both sizes of the arena are estimates, the row says so).
- `data/manual/ports/yards_historic_nj.geojson` and `data/manual/gapfill/cleared_districts_add.geojson`: valid, empty (see why).

## The holes (largest first; years = hectares)

Kind: **E** = real emptiness, keep; **C** = cleared district; **L** = lost works / building, outline not placeable; **D** = a
standing building with a wrong year; **?** = not explained.

| # | place, centre | ha | what it is | kind | source |
|---|---|---|---|---|---|
| 0 | Newark Central Ward (-74.1858, 40.7341) | 1980: 324 | Urban-renewal land of 1952-67 (Old Third Ward 225 acres from 1955, Central Ward project 95 acres from 1957, Hill Street 1959, UMDNJ Fairmount 1961 88 acres, UMDNJ Medical Center 1967 54 acres) and the riot's ruins; Belmont: over 95 % of buildings demolished 1950-1990. Part real, part the generated lots ending in 1975 (see districts) | C / E | newarkchanging.org "Urban Renewal by the Numbers"; "Black and Blight in Newark's Central Ward" |
| 1, 33 | Jersey City, Liberty State Park (-74.0459, 40.7073; -74.0586, 40.6957) | 1980: 77 + 17 | "Before opening in June 1976 the park was the site of abandoned rail facilities built on landfill"; 240 acres of the interior fenced off and contaminated for decades. CNJ Communipaw and Lehigh Valley Black Tom yards closed 1967 / 1976 (`yards_historic.geojson`). Empty by 1980; the CNJ terminal itself stands | E | Wikipedia "Liberty State Park" |
| 2 | Kearny Meadows rail yards (-74.1084, 40.7413) | 1960: 33; 1980: 75 | The fan of yard tracks across the top of South Kearny (Pennsylvania Railroad's Meadows Yard, photographed in service 1953-65; Conrail; NJ Transit's Meadowlands Maintenance Center, CSX intermodal). Tracks are in the map, cars are not; no source gives an opening year | E (no cars) | clui.org "Kearny Railyards"; nrhs.com photos (snippet) |
| 3 | Newark, Turnpike / I-78 / US 1&9 interchange (-74.1857, 40.7057) | 1980: 57 | Highway land: the Newark Bay Extension opened 1956; the Turnpike spurs | E | Wikipedia "Interstate 78 in New Jersey"; map |
| 4 | Elizabeth (-74.1713, 40.6775) | 1980: 56 | Turnpike and Northeast Corridor right of way beside Port Elizabeth (ground becomes "city" with the port, 1962) | E | map |
| 5, 26 | Newark, Doremus Avenue / Oak Island Yard (-74.1324, 40.716; -74.1495, 40.7095) | 1960: 42-9; 1980: 51-20 | Port Newark's rail yards and lots; Oak Island Yard built by the Lehigh Valley in the 1890s, rebuilt by Conrail 1977-79 (snippet). Yard already in `yards.geojson` | E | map; search snippet |
| 6 | Wayne (-74.258, 40.8876) | 1940: 3; 1960: 24; 1980: 43 | Willowbrook Mall's parking lots (opened 24 Sep 1969, enlarged 1970). **The mall's footprint is dated 1944 (`neighbours`): should be 1969** | E + D | Wikipedia "Willowbrook Mall (New Jersey)" |
| 13 | Paramus (-74.0765, 40.9177) | 1960: 18; 1980: 26 | Garden State Plaza's parking (opened 1 May 1957, the first suburban mall in New Jersey; Bamberger's 340,000 sq ft). **Footprint dated 1949 (`neighbours`): should be 1957** | E + D | Wikipedia "Garden State Plaza" |
| 14 | Newark, Ironbound meadow (-74.1292, 40.7282) | 1940: 6; 1960: 14; 1980: 25 | Probably Ruppert Stadium (258 Wilson Avenue, 1926 - demolished 1967; 19,000 seats) and the Turnpike spur land. Wilson Avenue is gone under the Turnpike: place not fixed | L (unplaced) | Wikipedia "Ruppert Stadium (New Jersey)" |
| 16 | Kearny Point (-74.1157, 40.7263) | 1940-80: 24 | Open ground of the Western Electric Kearny Works (broke ground 15 Jun 1928; 3.58 million sq ft; sold 1984) and the Federal Shipbuilding yard (1917-48; shipways, 17 acres in 1921; later ship breaking). Both standing buildings are in the map; the shipways and open yards are not | L / E | Wikipedia "Kearny, New Jersey", "Federal Shipbuilding and Drydock Company"; clui.org |
| 24 | Harrison (-74.1569, 40.7426) | 1900: 20; 1920: 19; 1940-60: 14; 1980: 4 | The industrial belt on the Passaic (Hyatt, Edison lamp and pump works): not researched, no place found | ? |  |
| 19 | Teterboro (-74.0659, 40.8564) | 1980: 23 | Airport (oldest in the area, 1919): airfield ground and hangar apron | E | Wikipedia "Teterboro Airport" |
| 11 | Newark Airport (-74.1921, 40.6947) | 1940-80: 15-29 | Newark Airport (opened 1 Oct 1928): runways and apron; the 1935 terminal stands | E | map |
| 31 | Jersey City, Droyer's Point (-74.0861, 40.6794) | 1980: 18 | Probably Roosevelt Stadium (1937 - closed 1981 - demolished 1985, 24,000 seats; Society Hill built 1996). The article's coordinates are wrong (they fall in Newark Bay); not placed | L (unplaced) | Wikipedia "Roosevelt Stadium" |
| 28 | Wood-Ridge (-74.0939, 40.8612) | 1960: 16; 1980: 19 | Lots around a 161,585 m² plant dated 1942 (exact): apron | E | map |
| East Rutherford | (-74.077, 40.819), (-74.077, 40.825) | 1980: 12 + 11 + 8 | Parking of the Meadowlands Sports Complex; the stadium and arena are the two rows written | E + L | Wikipedia "Giants Stadium" |
| 7, 8, 12, 15, 17, 18, 20-23, 25, 27, 29, 30, 32, 34 | Paterson (-74.174, 40.9239; -74.1549, 40.9015), Woodbridge (x5), Newark (-74.1553, 40.7758), Sayreville, Fair Lawn (x2), Englewood, North Bergen, Secaucus, Jersey City Heights, Carteret, East Orange | 3-33 each | Not explained: the land use (industrial / grass / park) says nothing about what stood; no opened source found in the budget | ? |  |

Loose ends with a position and no size: Brick Towers, Newark, 324 units, completed 1969, demolished 2008 (Wikipedia: 40.7286 N
74.18256 W, a Central Ward project); Stella Wright Homes (seven towers, Waverly Avenue, 1959, imploded in phases to 2002), Kretchmer
Homes (five 8-storey blocks, 1953, imploded 21 Apr 1996), Hayes Homes (12 storeys, 1950s-62): all in the Central Ward district, in
a snippet only; none has an opened source with an outline.

## Districts (corrections for the lead, `cleared_districts.geojson`; features in file order)

| district | field | old | new | source |
|---|---|---|---|---|
| 0 Newark Central Ward | `clearance_end` | 1975 | **1990** | Belmont: "over 95 % of all homes and buildings demolished 1950-1990" (newarkchanging.org); the Medical Center site declared blighted 27 Nov 1967 and cleared after; Stella Wright imploded to 2002, Kretchmer 1996, Brick Towers 2008 (snippets). The hole of 324 ha at 1980 is this ground: with the end at 1975 the generated lots are all gone by 1980 |
| 0 | `clearance_start` | 1955 | 1955 (confirmed) | Old Third Ward project 1955; Central Ward 1957; Hill Street 1959; UMDNJ Fairmount 1961; Medical Center 1967 |
| 2 Newark Route 78 | `clearance_end` | 1970 | **about 1985** (not verified to the year) | I-78 "built in various stages from the 1960s to 1989"; the Newark Bay Extension (Turnpike) opened 1956 |
| 3 Paterson Route 80 | `clearance_end` | 1972 | **1966** | I-80 "completed from Paterson to I-95 by 1966" (Wikipedia). City planning papers: Oregon Avenue removed for Route 80 |
| 1 Newark Route 280 | `clearance_start` | 1960 | 1960 (confirmed) | "Construction ... starting in 1960 near Orange"; end 1972 not verified |
| 4 Paterson downtown / Northside | years | 1965-80 | unchanged, **not verified** | the city's loop road round the centre was part of urban renewal; no block dates found |
| 5 Elizabethport | years | 1955-75 | unchanged, **not verified** | HOPE VI replaced public-housing complexes there later (1990s-2000s: the 1955-75 clearance may be followed by a second one); Singer plant (32 acres, 1873) left in 1982 |

**Real emptiness, keep it empty:** the Central Ward from the 1967 riots and the Medical School clearance until the buildings of
the 1980s-2000s (the map's own post-1990 buildings are real rows); Liberty State Park's interior from 1967-76; every parking lot,
interchange and rail corridor in the table.

**New districts: none written.** Candidate: the Ironbound south of the Pulaski Skyway cut by the Turnpike Newark Bay Extension
(opened 1956) and Port Newark (holes 5, 14); no outline or clearance date was found, and generating lots on a hole whose
cause is highway and port land would add false rows.

## Not holes but found on the way (for the lead)

- **Paterson is thin before 1920**: buildings standing in a bounding box of the city (-74.20..-74.13, 40.89..40.945): 1,147 in 1880
  (51,000 people), 2,821 in 1900 (105,000), 7,716 in 1920 (136,000), 15,080 in 1940. Newark, Elizabeth, Jersey City and
  Kearny/Harrison hold 15-25 people per building in 1900-20; Paterson 37 in 1900 and 44 in 1880. The holes list does not show
  it (the terrain is not "city" there either). Paterson wants a traced atlas or the generated fill from 1880.
- **Wrong years of two malls** (researched rows for `known_building_dates`): Westfield Garden State Plaza, footprint
  `61bd1cde-afb0-4730-80cd-797c35c3ac80` (40.91779, -74.07621), now 1949.7 `neighbours` -> 1957 (opened 1 May 1957); Willowbrook,
  `3607f363-4dc5-49ec-b797-d26eceabbb8d` (40.88907, -74.25925), now 1944.6 `neighbours` -> 1969 (opened 24 Sep 1969).

## Not placed (and why)

Koppers Seaboard coke works, Kearny, 1917-1979 (174 acres, razed 1979; Hackensack River on the north and east, Route 7 south;
Overture's "Koppers Dredged Material Recycling Facility" polygon, -74.1005..-74.0761, 40.743..40.7496, 51 ha, is the site's
present part): no plan; the site is the right size for a `data/manual/sites` polygon. Singer works, Elizabethport (1873-1982,
32 acres at first, "First to Fifth Street along Trumbull"; the original brick building stands): streets not found. GM Linden
Assembly (1937-2009, 2.6 million sq ft, 104 acres, Wikipedia 40.6194 N 74.2555 W): its coordinate lies 450 m from the nearest
hole and the plant outline is not known. Ruppert Stadium and Roosevelt Stadium (above). Rogers, Cooke and Danforth locomotive
works, Paterson (1832 / 1852, ALCO to 1926): no coordinates in the articles. Federal Shipbuilding's yard at Port Newark
(1942-45). Meadows, Waverly and Elizabethport yards (no opening year).
