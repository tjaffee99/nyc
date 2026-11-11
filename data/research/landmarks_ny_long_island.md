# Long Island landmarks (Nassau and Suffolk) — research notes and numeric checks

Models: `viewer/src/landmarks/ny-long-island.ts` (`NY_LONG_ISLAND`, 16 entries for 11 buildings). Scratch and checks: `data/interim/landmarks_ny_long_island/` (`decomp.py` fits each outline's frame and roof blocks, `check.cjs` rasterises each mesh). Nothing was downloaded to `data/raw/landmarks_ny_long_island/`.

## Sources and licences

- Outlines: Overture 2026-10-21.0 `outer_building.parquet` (OpenStreetMap, ODbL, (c) OpenStreetMap contributors; way ids not looked up, Overture ids: Oheka 98a7ef78, Sagamore Hill 8bab41e4, Montauk Point Lighthouse 80610824, Jones Beach Water Tower 47e9691e, Westbury House 4a67473c, Hempstead House 69de3108, Castle Gould 6874300f, Coe Hall c85849f1, Suffolk County Vanderbilt Museum 05210053, Nassau Veterans Memorial Coliseum 8086c3f9, The Big Duck 60f45490). Overpass was unreachable from this machine.
- Facts: Wikipedia articles (CC BY-SA 4.0; facts only; URLs in each model's `sources`), read through a summarising fetch, not the wikitext: treat figures as read once, not verified against the primary source. NPS Fire Island page (public domain) and web-search summaries (oheka.com, Architectural Paper, Sports Illustrated 1968) for the items marked.

## Numeric check (mesh rasterised at 0.5 m; plan area against the outline; top against the cited height)

| id | faces | top (m) | cited / basis | plan (m2) | outline (m2) | ratio |
|---|---|---|---|---|---|---|
| oheka_castle | 176 | 23.5 | none (estimated) | 3111 | 3102 | 1.003 |
| sagamore_hill_1885 | 92 | 12.0 | Overture 12 m roof | 605 | 747 (minus North Room) | 0.81 (intended) |
| sagamore_hill | 115 | 12.0 | Overture 12 m | 746 | 747 | 0.998 |
| montauk_point_light_1796 | 62 | 24.38 | 80 ft | 57 | 57 | 1.004 |
| montauk_point_light | 94 | 33.68 | 110 ft 6 in | 57 | 57 | 1.004 |
| fire_island_light_1858 / fire_island_light | 134 / 254 | 51.2 | 168 ft | 74 | none (base 32 ft = 9.75 m: 75 m2) | ~1 |
| jones_beach_water_tower | 72 | 57.3 | 188 ft | 74 | 75 | 0.98 |
| westbury_house | 138 | 14.0 | none | 1175 | 1174 | 1.000 |
| hempstead_house | 140 | 24.4 | tower 80 ft | 1703 | 1700 | 1.002 |
| castle_gould | 147 | 16.7 | none | 3044 | 3030 | 1.005 |
| coe_hall | 237 | 17.0 | none | 1548 | 1544 | 1.002 |
| vanderbilt_eagles_nest | 157 | 13.0 | none | 2266 | 2264 | 1.001 |
| nassau_coliseum | 170 | 23.0 | none | 12287 | 12291 | 1.000 |
| big_duck_1937 / big_duck | 216 | 6.10 | 20 ft | 28 | 41.8 (15 x 30 ft cited; outline 28) | 0.67 / 1.0 |

Other checks: Oheka's outline (3,102 m2 = 33,400 sq ft) times 3.3 floors is the cited 109,000 sq ft. Hempstead House's outline is 68 x 38 m = 224 x 125 ft against the cited 225 x 135 ft. Montauk's 8.2 m (27 ft) outline against a 28 ft base diameter.

## What is estimated

Every height without a figure above (Oheka, Westbury, Castle Gould, Coe, Vanderbilt, Coliseum), all roofs, colours, towers' positions, and the wings (the largest rectangles inside each outline, `decomp.py`). Hempstead House's tower (80 ft cited) sits at an assumed place. Fire Island's base (32 ft) and top (15 ft) widths come from a historical-marker summary and the same 32 ft base is NPS's figure for the 1826 tower: unverified. Montauk's top width (5.2 m across flats) and lantern heights are estimates. Dates: Castle Gould 1901-1909 and Hempstead's 1901 start are estimates; Westbury's 1903 is the start of the estate, not of the house; Fire Island's 1858 start is a placeholder; Sagamore's 1905 month is unknown; the duck's 2007 return is October 6, 2007.

## Not built

- **Belmont Park grandstand (1968)**: sources give 1,260 x 300 ft and 112 ft high, opened May 20, 1968, demolished 2024 (Wikipedia; Architectural Paper; Sports Illustrated 1968), but its outline is no longer in Overture, so no footprint exists to anchor it. The grandstand of 1905 has no dimensions in any source read.
- **Fire Island's first tower (1826)**: 74 ft, octagonal bluestone, 32 ft to 16 ft (NPS), but no source read says where it stood.
- The duck's Riverhead (1931-37) and Sears Bellows (1988-2007) sites; Sagamore's piazza; the Coliseum's 2017 fin facade.
