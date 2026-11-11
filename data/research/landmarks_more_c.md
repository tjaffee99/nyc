# Landmarks, round "more C": Riverbank State Park and pier-deck fields

Code: `viewer/src/landmarks/nyc-more-c.ts` (export `MORE_C`, 6 models). Generators (not part of the build):
`data/interim/landmarks_more_c/gen.py`, `gen_ts.py`, `gen_piers.py`, `osmways.py`, `feat.py`; check: `check.ts`.
Downloads: `data/raw/landmarks_more_c/` (`rb.osm`, `p40.osm`, `bbp.osm`: OpenStreetMap map API, ODbL; Wikipedia raw wikitext
`Riverbank_State_Park.wiki`, `Pier_40.wiki`, `Brooklyn_Bridge_Park.wiki`; `nysparks.html`, State Parks page read 2026-11-11).

## Riverbank State Park (2 models, anchor = centroid of the plant's footprint BIN 1084789, -73.956775, 40.825532)

Dates and facts (all read 2026-11-11):
- Wikipedia "Riverbank State Park": designed by Dattner Architects and Abel Bainnson Butz, opened 27 May 1993, renamed Denny Farrell
  Riverbank State Park 5 Sept 2017; the plant sits on 2,300 caissons up to 230 ft beneath the river; foundation completed 1978, the
  treatment works built in two phases 1986-1991 (the owner's "in service 1986" is the first phase); 28 acres; 400 m track; 35 ft trees.
- State Parks (parks.ny.gov/visit/state-parks/riverbank-state-park-denny-farrell-riverbank-state-park): "28-acre multi-level landscaped
  recreational [park] rises 69 feet above the Hudson River" = 21.03 m; "five major buildings: a 50-meter pool, a covered skating rink
  (roller skating in summer, ice-skating in winter), an 800-seat cultural theater, a 2,500-seat athletic complex with fitness room, and a
  150-seat restaurant"; outdoors: 25-yard lap pool, wading pool, four tennis courts, four basketball courts, a softball field, four
  hand/paddleball courts, a 400-meter eight-lane running track with a football/soccer field.
- Models: `north_river_plant_1986` built [1978.0, 1986.0], end 1992.0; `riverbank_state_park` built [1991.2, 1993.4], end 9999
  (the 1991.2 start, the 1992.0 hand-over and the two-year "construction" look are ESTIMATED; the opening 27 May 1993 = 1993.4).
  The viewer shows a model fully formed from `built[0]` in construction colouring until `built[1]` and shrinks it in the last 0.8 years
  before `end`: the 0.8-year overlap hides the plant's shrinking under the park's deck.
- Deck height 21.2 m above the terrain at the anchor: the city's measured roof of BIN 1084789 is 21.21 m, State Parks says 21.03 m.
  (The building file draws the plant to 30.5 m absolute: base 3.54, height 26.92; the ground elevation under it, 2.74 m; the two cited figures
  agree with each other, not with that drawing: left to the lead.)

Geometry (OpenStreetMap ways, map API 2026-11-11; local metres around the anchor, x east, y north):
| item | OSM way(s) | note |
|---|---|---|
| deck / plant | city footprint BIN 1084789 (OSM 275080368 has the same outline, `height=29.5`) | 108,250 m2, 41 vertices, 487 m x 552 m bounding box |
| track | 118527547 (outer) minus 386500083 (inner) | 3,930 m2, ring about 10 m wide: 8 lanes, 400 m (cited) |
| football / soccer field | 118527528 `soccer;american_football` | 106 m x 60 m |
| infield | 386500083 minus the pitch | grass |
| softball field | 367236669 | 5,780 m2 |
| tennis | 367235360, 367235363, 367235365, 367235369 | 4 courts (cited: four) |
| basketball | 367235358, 367235362, 367236664, 367236666 | 4 courts (cited: four) |
| handball | 118527555 | one polygon of 780 m2 for the four hand/paddleball courts (cited: four) |
| outdoor pool / wading pool | 118527521 (14 m x 24 m = the 25-yard pool), 1067987926 | |
| playgrounds, gardens, shrubs, grass | 1553756149, 1553756164; 943557524, 1237672046, 1237673788, 943557533, 118527542, 1291178511, 1291178523 | clipped to the deck |
| paths, access road | layer-2 footways of the park; Riverbank Park Access Road 46568279, 118524657, 910522621, 1443589781 | footways buffered 1.1 m each side, road 2.6 m |
| buildings | pool building 118527498, athletic complex 118527506, covered rink 118527530, cultural theater 118527501, restaurant 118527538, pavilion 118527504, greenhouse 1271574699 | |
| footbridge | 46568274 (138th St) | 4 m wide deck at deck level on two piers |

Building heights above the deck (city's measured roof heights of the overlapping footprints, read as above the deck: ESTIMATED because the
city's file puts all of them on the same ground 2.74 m and its deck is higher than they are): pool building 11.89 (BIN 1090426), athletic 8.84
(1090428), rink 13.11 (1090427), cultural theater 8.84 (1090429), restaurant 7.62 (1090431), pavilion 6.1 (1090425); greenhouse 3.5 (no height anywhere, estimated).
Slab heights above the deck: 0.04-0.14 m by draw order. Colours are estimated (the OSM `surface` tag exists only for some courts).
Not done: the 145th Street approach (OSM maps no bridge there: the access road is the only part drawn), railings, trees (up to 35 ft),
the carousel, the plant hall under the deck, the odour-control stacks, the greenhouse's shape.

Numeric checks (`check.ts` through esbuild, run 2026-11-11): plant model 121 triangles, x -230.9..256.6, y -285.5..267.0, top 21.20 m; the footprint's bounds
are x -231..257, y -285..267 (BIN 1084789, 108,250 m2) so the plan matches to 1 m; park model 809 triangles, same bounds, top 34.31 m = 21.2 + 13.11 (the rink).
All 7 OSM building outlines and every slab lie inside the deck (clip 0.97-1.0, the handball polygon 0.97). The anchor and the centroids of BINs 1090423-1090431 are
inside the plant's ring, so `replaces` takes them. 28 acres = 113,300 m2 vs the deck 108,250 m2 (and OSM park polygon 118524694 clipped: 108,181 m2).

## Pier models (4)

Each pier model is the city's pier layer outline (`data/interim/nyc_buildings.parquet`, `doitt_id` `pier:pier_bk_0147`, `pier:pier_bk_0152`) or the shed
footprint (BIN 1012249) extruded to the top of the deck, with the OSM pitches of the pier as slabs 6 cm above it.
- `pier40_terminal_1962` [1958.0, 1962.0] -> 1998.0, `pier40_roof_fields` [1997.5, 1998.5] -> 2005.4 and `pier40_main_field` [2004.0, 2005.4] -> 9999.
  Wikipedia "Pier 40" (read 2026-11-11): "Construction began in 1958 and the terminal was opened in 1962"; "The roof served as parking for over 700 cars";
  "The upper-level recreational area, opened in 1998, features two fields (one small field and one soccer field)"; the main field "occupying the former
  cargo level" was built from 2004 and opened in May 2005. The city's shed footprint (BIN 1012249) has a **courtyard** (a hole of 14,300 m2): the main
  field (OSM 23529474, 5,323 m2) lies wholly in it, at deck level, open to the sky; the model draws the shed with the hole on the pier deck slab
  (`pier:pier_mn_0116`, 3.0 m above the model base = 2.5 m above the water). Roof 14.7 m above the water = the city's measured 13.11 m + its ground 1.6 m
  (the building file draws 14.77 m). Roof fields: OSM 65223814 (3,185 m2), 576166509 (2,023 m2). The month of the 1998 opening is not given: the
  1997.5-1998.5 window is estimated. Not modelled: ramps, the garage at the east end (OSM 1115996380, 19 m), the levels inside the shed.
- `bbp_pier5_fields` [2011.0, 2012.95] -> 9999: Pier 5 "opened in December 2012" (Wikipedia "Brooklyn Bridge Park"); construction of the park began 28
  Jan 2008; the 2011 start is estimated. Three soccer fields, ways 328277180, 328277282, 328277283 (4,454 / 4,494 / 4,540 m2); deck 3.0 m above the model base
  (2.5 m above the water in the city's pier layer: base -1.0 + 3.5).
- `bbp_pier2_courts` [2013.0, 2014.4] -> 9999: "Piers 2 and 4 in May 2014"; "basketball, handball, bocce, and shuffleboard courts; artificial turf; swings;
  fitness bars; and picnic tables" (Wikipedia). Drawn: the OSM pitches inside the pier (5 basketball, pickleball, handball, play turf, roller rink,
  playground); not drawn: bocce, shuffleboard, tables, the roof structure (way 328275185).
Numeric check: tris Pier 40 59 / 63 / 65, Pier 5 28, Pier 2 66; bounds Pier 40 x -181.7..131.3, y -131.3..139.4 (shed outline 57,297 m2 less the 14,297 m2 courtyard; the deck slab is the pier row); Pier 5 x -112..118, y -90..92; Pier 2 x -102..113, y -101..84.
Not verified on screen. Whether `replaces` of a polygon also hides the pier layer's rows (they are building rows with `year_src` pier) rests on the
viewer matching building centroids; the pier rows' centroids lie inside the rings, but the pier layer was not read in the viewer code.
