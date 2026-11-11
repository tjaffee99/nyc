# Holes of the 20th century: the Bronx, Queens and Staten Island (round of 2026-11-12)

Files of this part: `data/tables/notable_demolished.boroughs2.csv` (32 rows), `data/tables/known_building_dates.boroughs2.csv` (8 rows),
`data/manual/sites/add_boroughs2.geojson` (5 features, for the lead to merge), scripts in `data/research/holes_boroughs_build/`
(`holes_poly.py` recomputes the holes, `view.py` / `sheet.py` draw the 1924 / 1951 photographs with today's buildings and a metre grid,
`tanks.py` finds round tanks, `build_rows.py`, `build_geojson.py` write the files), downloads in `data/interim/holes_boroughs_raw/`.

## What the list measures, and a flaw found in it

`pipeline/holes.py` marks a building by its **centroid** only. A building of 2-4 ha (the Hunts Point sheds, the Anna M. Kross Center, a hall) clears a
single 38 m cell, so the ground under and around it stays a "hole". `holes_poly.py` repeats the measure with every footprint of 2,000 m2 and more
marking all the cells it covers (7,957 footprints): hectares fall (Bronx 1960 from 151 to 134, 1980 from 189 to 124; the Hunts Point holes about halve; Rikers 1980: 44 ha -> 22 + 19 ha) and the list below is the corrected one. Hole ids in the table are those of
`data/interim/holes_boroughs_raw/holes_bbox_fp.csv` (year_index). Hectares: Bronx 28 / 18 / 116 / 134 / 124, Queens 17 / 7 / 11 / 38 / 53, Staten Island 52 / 59 / 70 / 63 / 81
for 1900 / 1920 / 1940 / 1960 / 1980.

**A second finding for the lead:** the 1924 mosaic is *not* registered where it is built over Rikers Island (the 1924 sheds sit about 200 m from the
outlines that coincide with the 1951 ones); `presence.parquet` carries an `offset_m_1924` for it, my viewer does not. Where I used 1924 (Shooters Island,
Aqueduct) the island's shore and the railroad cut agree with today's maps to within about 20 m.

## The 34 largest holes (merged across 1900-1980), what each was

Source column: W = Wikipedia raw wikitext (fetched 2026-11-11, 4 s apart), P = the City's 1951 / 1924 aerial mosaics (NYC OTI, CC BY 4.0), D = NYC DOC history pages.
"Added" says what went into the files; "stays" = real emptiness (or infrastructure the map does not draw as buildings).

| # | place (lon, lat) | ha by year | what the ground was | src | added / why nothing |
|---|---|---|---|---|---|
| 1 | Rikers Island, whole island (-73.8805, 40.7915) | 1940 87, 1960 80 | jail in the north-west corner from 1932 (hospital 1932, penitentiary 1933); centre, south and east are dump surface and fields in 1951 (landfill until 1943, 90 -> 415 acres) | W, D, P | `rikers_fields_1932` (80 ha, open ground to 1971) in the GeoJSON; 2 standing sheds re-dated; stays otherwise (real fill) |
| 2 | Charleston / Rossville, Arthur Kill shore (-74.2394, 40.5456) | 1900-60 20, 1980 37 | on the 1951 photograph a large oil tank farm (about 25 round tanks, 40-60 m) with a wharf, west of the Kreischer clay pits; the ground was cleared in 1900-20 for it (the pits are `kreischer_clay_pits`) | P | **nothing**: no opened source names the company or dates the tanks (Wikipedia's Charleston / Rossville pages do not mention oil; the search endpoint rate-limited me). Tanks would be as the Gulf ones below. Real emptiness otherwise |
| 3 | Freedomland / Bay Plaza, Baychester (-73.8266, 40.8661) | 1960 26, 1980 32 | Freedomland U.S.A. 1960-64 (85 acres of a 205-acre lease on a landfilled marsh; Co-op City took the parking lot, Little Old New York and Satellite City 1965-68; Bay Plaza early 1980s on five more areas; one tract empty to 2012) | W | `freedomland_remnant` (41 ha, open 1964-84). No building row: the article gives no dimensions or positions of any structure, and no photograph of 1960-64 is held |
| 4 | Rikers east (-73.8757, 40.7903) | 1980 22 | fields between the east jails (Motchan 1971, Davoren 1972, Vierno 1991) | D | in `rikers_fields_1971` (57 ha, to 1988) |
| 5 | Rikers centre (-73.8855, 40.7891) | 1980 19 | the Anna M. Kross Center compound (1978; 40 acres, 40 housing areas), most of whose footprints are dated 1984-85 by neighbours | D | in `rikers_fields_1971`; the many footprints of the compound are not listed one by one (not identified from the DOC page) |
| 6 | Port Ivory, Procter & Gamble works (-74.1776, 40.6396) | 1920 19, 1960 13, 1980 12 | soap works 1907-1991: a dense block of long sheds, a tank group and a power plant in 1951; site `port_ivory` exists, the map has 19 generated roofs | W, P | **nothing**: the roofs overlap and cast shadows; I could not separate outlines within 40 m on the 1951 image (see "not placed") |
| 7 | Bronx State Hospital site, Morris Park (-73.8419, 40.8516) | 1900 16, 1940 17 | 1924: scrub and marsh between the New Haven's yards and the Hutchinson valley; 1951: six long rectangular beds; hospital 1963 | P, W | stays (open ground) |
| 8 | Gulf Oil terminal, Bloomfield (-74.1867, 40.6155) | 1900 4 -> 1960-80 17 | oil terminal built 1936, 82 tanks, 215 million gallons, closed 1998 | W, P | 23 tanks as rows; site `gulf_oil_terminal` in the GeoJSON |
| 9 | Rikers north-west compound (-73.8884, 40.7951) | 1940 9, 1980 15 | the penitentiary yard: six long sheds, a hollow-square building, a five-wing cell block, all on the 1951 photograph | P, D | 2 standing footprints re-dated |
| 10 | Aqueduct, west of the Ozone Park blocks (-73.8312, 40.668) | 1960 4, 1980 13 | ten long gabled sheds in rows on the 1951 photograph, open fields in 1924, nothing now | P, W | `aqueduct_barracks_site` suggested to the lead (unidentified) |
| 11 | Hunts Point Meat Market (-73.8743, 40.8056) | 1960 4, 1980 12 | market opened 1974; its sheds carried 2003-08 | W | 3 sheds re-dated to 1974 |
| 12 | Hunts Point Produce Market (-73.8748, 40.8125) | 1960 7, 1980 11 | market opened 1967; sheds carried 1971-76 | W | 3 sheds re-dated to 1967 |
| 13 | Bronx River meander at Soundview (-73.8592, 40.8152) | 1860-1900 8 | tidal marsh in the 1924 photograph (the terrain's city cover is the error) | P | stays |
| 14 | Idlewild / JFK edge (-73.791, 40.6654) | 1960 8, 1980 8 | vacant lots, a ball field and the Belt Parkway cut in 1951 | P | stays |
| 15 | Fresh Kills / Brookfield (-74.1668, 40.5788) | 1980 7 | landfill and the airfield-like cleared ground of 1951 | P | stays (landfill; `brookfield_landfill`, `fresh_kills_landfill` exist) |
| 16 | Jamaica Yard (-73.8293, 40.7197) | 1940 7 | LIRR / subway yard (`jamaica_yard`) | P | stays (track, not buildings) |
| 17 | Shooters Island (-74.1596, 40.6435) | 1900-80 5-7 | Townsend-Downey 1898-1910, then Standard Shipbuilding (bought the island 1915, industrial to 1922); the 1924 mosaic shows a hall, sheds and a fan of ten ways; 1951: bare ground; now a bird sanctuary | W, P | 9 shed rows from the 1924 photograph |
| 18 | Port Morris / Randall's Point (-73.898, 40.812) | 1940 3, 1980 7 | rail and expressway ground | P | stays |
| 19 | Edgemere landfill (-73.768, 40.5934) | 1980 6 | `edgemere_landfill` 1938-91 | W | stays |
| 20 | Tottenville shore, Conference House (-74.2518, 40.5019) | 1900 6 | woods and fields in the 1924 photograph | P | stays |
| 21 | Broad Channel (-73.805, 40.5885) | 1900 6 | marsh / bay islands | - | stays |
| 22-34 | smaller (3.4-5 ha): Maspeth (-73.9231, 40.7343), (-73.9268, 40.7283); Jamaica Estates (-73.8012, 40.721); Flushing Meadows (-73.8394, 40.7629: the ash-dump fairground); JFK (-73.7989, 40.6671); Aqueduct (-73.8288, 40.6629; -73.8291, 40.6766); Fresh Kills (-74.1553, 40.5801); Hunts Point (-73.8808, 40.8165); Hoffman Island (-74.0539, 40.5789, water); Kreischerville (-74.2399, 40.5381); Riverdale (-73.9196, 40.8859) | | marsh, parkland, yards, road cuts | P (only the Flushing and Aqueduct ones looked at) | stays; not researched |

Looked at on the photographs: 1, 2, 3 (no photo of the park), 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 20. Numbers 18, 19, 21-34 were not opened one by one.

## What was written

### `notable_demolished.boroughs2.csv` (32 rows, all `procedural`-free: outlines or circles measured on the photographs)

* **Shooters Island shipyard** (9 rows, 1916-1938, estimated): hall 125 x 93 m, three west sheds, a long narrow shed, two mid sheds, a south shed, a windowed shop.
  Outlines read off the 1924 mosaic in a 50 m grid and drawn back over it (checked: they sit on the roofs, +-6 m). Facts: Standard Shipbuilding bought the island 1915,
  industrial use through 1922, derelict vessels round it by 1930 (Wikipedia). Which sheds are Townsend-Downey's (1898-1910) is not known. The 1951 photograph shows bare ground.
  The ten shipways of the fan are not buildings and were not drawn.
* **Gulf Oil terminal tanks** (23 rows, 1936-1999, estimated): round tanks of 36-38 m found on the 1951 mosaic by a Hough circle detector (22) plus one read by eye,
  checked by drawing them over the photograph (all sit on a tank). The mosaic covers only part of the terminal, which had 82 tanks; the others lie on tiles the project does not hold.
  Height 12 m estimated. Name contains "tank" and `footprint_m` is `DxD`, so `nyc_extras.notable()` draws them round.

### `known_building_dates.boroughs2.csv` (8 rows)

* Rikers: footprint 2109478 (the six sheds, 1984.8 by neighbours, p1951 0.97 -> 1940 estimated) and 2116653 (hollow-square building, 1961 from a map bracket the 1951 photograph contradicts -> 1936 estimated).
* Hunts Point: three produce-market sheds -> 1967, three meat-market sheds -> 1974 (the markets' opening years; the built file had 1971-76 and 2003-08).
* Not written: 2116652 (p1924 0.96, but the 1924 mosaic is misregistered there), 2109474 (carries the Otis Bantum row of 1985 from the name OpenStreetMap puts on it; the 1951 photograph shows a five-wing
  cell block on its outline, which is the 1933 penitentiary: the name match looks wrong, or the building was replaced on the same ground; unresolved).

### `add_boroughs2.geojson` (5 features, schema of `sites.geojson`)

`rikers_fields_1932` (landfill/open 1932-1971, 81 ha), `rikers_fields_1971` (1971-1988, 57 ha), `freedomland_remnant` (open 1964-1984, 41 ha), `gulf_oil_terminal` (terminal/yard 1936-1998, 33 ha, `label` true),
`aqueduct_barracks_site` (1925-1960 estimated, 7 ha: for `site_fill.py` to read roofs from the photograph; identity not established). Outlines of the first three and the Gulf one are the hole cells
(`holes_poly.py`), buffered. Both Rikers features must win over `rikers_island_jails` (ground `paved`, 166 ha, which makes the whole island city from 1932 and is why 80 ha show as a hole in 1940-60).
Order of rebuild after merging: the holes tool again.

## Real emptiness that should stay

Rikers' central and east fill (until the jails of 1971-91), the Freedomland ground 1964-84, the marsh and meander holes (Soundview 13, Broad Channel 21, Tottenville 20, Morris Park 7 in 1900-40),
landfills (Fresh Kills, Edgemere, Brookfield), rail yards (Jamaica, Port Morris), road cuts. The terrain's "city" cover on these is the error, not the missing building.

## Not placed, and why

* **Port Ivory works (P&G, 1907-91)**: a real, large hole, but on the 1951 image the works is a dense block of roofs under shadow; I could not split it into outlines good to 40 m, and no source gives its buildings. Needs a plan (Sanborn / Hopkins) or a segmentation with `site_fill.py` run on a wider outline.
* **Arthur Kill tank farms (hole 2)**: no opened source for owner or dates.
* **Freedomland's structures**: no dimensions or positions in the article; the map of the park (a US outline, Chicago and San Francisco ends) was not found.
* **Hunts Point gas holders and coal yard (1951)**: four round holders and a long building are on the photograph; no opened source.
* **Rikers before 1951**: the 1924 photograph shows a row of dormitory sheds that are not in 1951; the 1924 registration is off there, so they were not traced.
* The 1939 and 1964 World's Fair grounds are not a hole of this list (the Flushing Meadows holes are 4-5 ha of ash-dump ground); not checked against the landmark models.
* The 82 tanks of the Gulf terminal: 23 are placed; the rest lie outside the photographs held.

## Method limits (plainly)

Outlines from photographs are +-5-6 m and drawn by eye (Shooters Island) or by detector (tanks); years of every lost row are estimates bounded by the cited founding and closing years and by which photograph shows the object.
The hole cells are the grid's (38 m). No precision figure exists for any of it; the Shooters and Gulf rows were looked at on the images, nothing was looked at on the live map.
