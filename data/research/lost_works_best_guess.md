# Lost works placed by best estimate (round of 2026-11-12)

The owner: "procedurally generate it based off your best guess if you need to". File: `data/tables/notable_demolished.best_guess.csv`
(143 rows, same columns as `notable_demolished.sites.csv`; read by `nyc_extras.notable()` through its glob; all 143 parse to valid
geometry, checked by calling `notable()`). Every `shape_note` starts "BEST GUESS:" and says what is known and what is guessed.
Scripts (one per works, idempotent; run `nudge.py` after them): `data/research/lost_works_build/` (`lwlib.py` row helper,
`lw_map.py` basemap/aerial overlay, `check.py` overlap test, `nudge.py` moves a row up to N m to clear real buildings and today's water,
`tanks2.py` + `tankpick2.py` round-tank detector on the 1951 mosaic, `blobs.py` empty-ground finder). Downloads/pictures: `data/interim/lost_works_raw/`
(Wikipedia raw wikitext, paced, User-Agent `NYCThroughTime-research/0.1`; the 1951 tiles from the City's public ArcGIS layer as in `aerial_presence.py`).
Wikimedia Commons / the API rate-limited the machine at once: no aerial photograph of the New Jersey works could be opened.

## Rule used for every row
Position from the best evidence held, size and height estimated, years bounded by the works' cited life; each row is checked against
buildings alive in its years (`check.py`: the standing, non-generated ones; generated lots give way to a documented row) and against
today's water (piers excepted). Where a row overlapped a real building it was moved (`nudge.py`; the note then says "shifted N m").
Not looked at on screen in the viewer: only on matplotlib basemaps/aerial overlays.

| works | rows | position | basis |
|---|---|---|---|
| Arthur Kill tank farm, Charleston, S.I. | 22 tanks (about 45 on the photograph) | +-8 m | 1951 mosaic, circle detector re-scored for a bright uniform disc with a shadow side (30 m tanks); all 22 drawn over the photo sit on a tank; the others (dark or in shadow) were not picked up. Owner and years unknown: 1922-1995 guessed |
| Port Ivory (P&G), S.I. | 35 (5 buildings, a stack, 29 tanks in three groups) | +-12 m buildings, tanks +-3..10 m | 1951 mosaic read by eye; the two long east sheds, the rail shed and the power-house area coincide with REAL footprints (assessor 1934; city demolition 2007) and were NOT added; power house and shop overlap them by under 20 % |
| Hunts Point gas works, Bronx | 5 (large gas holder 72 m, small holder, three sheds) | +-10 m | 1951 mosaic; owner and years unknown (1920-1970 guessed; the Co-op Market was built there 1967-74) |
| Freedomland U.S.A. | 8 set pieces | +-150 m | only the article's compass placement of the sections (Little Old New York north, San Francisco south, Satellite City south-east) inside the site polygon `freedomland` |
| Singer works, Elizabethport | 8 (five lofts, foundry, power house, stack) | +-120 m | "First to Fifth Street along Trumbull" (holes note); Trumbull Street is gone; the 650 m diagonal of the very large post-1982 building is taken as the plant's ground; plan invented |
| Western Electric Kearny Works | 5 lost buildings | +-120 m | many lofts still stand along Distribution Avenue (real, on the map); lost ones put on the empty east of the 144 acres, in the standing lofts' direction and size |
| Federal Shipbuilding, Kearny Point | 6 shipways | +-100 m | 2,400 ft of Hackensack frontage, 12 ways (Wikipedia); ways drawn parallel on the east shore; two sat in today's water and were dropped |
| Koppers Seaboard coke works, Kearny | 7 | +-300 m | holes note: Hackensack N and E, Route 7 S, the Koppers brownfield polygon; typical by-product plant layout invented |
| Colgate plant, Jersey City | 5 | +-60..120 m | Wikipedia 'Colgate Clock (Jersey City)': plant at 85-99 Hudson St, razed 1985 for 30 Hudson Street (the clock now stands 1300 ft south); rows moved up to 120 m to clear real buildings |
| Roosevelt Stadium | 1 | +-100 m | the street "Roosevelt Stadium Court" in Society Hill (Overture) marks the ground; the article's own coordinates are in the water |
| Ruppert Stadium | 1 | +-200 m | the Ironbound meadow hole of the holes list; Wilson Avenue is gone |
| Hoboken: HAL / NDL piers | 5 piers 1901-1960 + one block for the three wooden NDL piers 1868-1900 | +-60 m N-S, length estimated | foot of 1st-5th Streets (Wikipedia: NDL piers at the foot of 3rd and 4th, burned 30 June 1900; HAL south of them) |
| Hoboken: Maxwell House | 4 | +-70 m | 1939-1992, 10th-12th Streets (Wikipedia); no traced outline there (`hudson_hoboken_1930` covers the blocks west of Hudson Street only) |
| Hoboken: shipyard shops (Tietjen & Lang / Todd / Bethlehem) | 3 | +-100 m | north of the Maxwell plant |
| Stevens Castle | 1 | +-25 m | Howe Center site beside the campus buildings; 45 x 32 m estimated |
| Newark housing: Brick Towers 3, Stella Wright 7, Kretchmer 5, Columbus Homes 4 | 19 | Brick Towers +-100 m (Wikipedia point); the rest +-500 m | the rest only "in the Central Ward cleared district"; counts of Columbus towers unknown |
| Rogers 5 shops, Cooke 2 | 7 | Rogers +-120 m, Cooke +-250 m | the preserved erecting shop (Paterson Museum, 40.91346 -74.17884) as the anchor |

## Traced outlines already on the map (no row written)
None of the traced atlas layers covers any of these: the Hoboken layers (`hudson_hoboken_1891`, `_b_1891`, `_1930`) cover the street blocks
only, not the piers, the made land of the Maxwell plant, the shipyard or Castle Point (checked on an overlay). The Port Ivory sheds that stand today
are real footprints (see above); the standing Western Electric lofts, Federal's shops (Building 77 and others), the Singer original building and the
Rogers erecting shop are on the map as real buildings.

## Still not placed
- **Lorillard** (Jersey City): no source, no position; **Dixon Crucible** (167 Wayne Street) stands (Dixon Mills) - nothing to add.
- **Holland America pier** at Hoboken: no source for which pier.
- **Hayes Homes** (Newark): the years are unclear in the notes ("1950s-62"); the street is at about -74.1893 40.7352 but no row written.
- The other ~20 tanks of the Charleston farm; the Gulf Oil tanks beyond the photograph; Hunts Point's third/fourth round holder (only two found).
- Federal's yard at Port Newark (1942-45), Meadows/Waverly/Elizabethport rail yards (no brief).

## What is guessed (not sourced)
Every size and height outside the 1951 photographs; every plan inside the NJ works; the order and number of buildings; the Newark towers' layout; start years
of single buildings; most end years of demolition. Unopened: Western Electric's 1981 "The New Kearny" article, HAER NJ-71-B (Colgate), the NJ Historic Trust items on
the Rogers shop, ConnCRIS-style registers for none of these. Search snippets only: Stella Wright / Kretchmer / Brick Towers / Columbus Homes (from `holes_nj_cities.md`).
