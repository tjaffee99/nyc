# Working yards: container terminals and rail yards (`data/manual/ports/`)

Container stacks and rail cars are not buildings in any dataset, so a container terminal reads as bare paved ground and a rail yard
as bare track. `pipeline/port_fill.py` writes **generated** structures for them to `data/interim/gapfill/gapfill_ports.parquet`
(columns of `gapfill_sites.parquet` minus `site`; EPSG:4326 polygons). The map marks every row `procedural`.

## Files

| file | what |
|---|---|
| `terminals.geojson` | 7 container terminals: outline, name, operator, `periods` (first year of container handling, closing year, 9999 = open), `year_basis` (`source` / `estimated`), source URL, the sentence the year rests on, where the outline is from |
| `yards.geojson` | 18 rail yards (16 from `data/manual/sites/sites.geojson`, kind `rail_yard`, still open; Oak Island Yard; Harlem River Yard) with opening year, basis, source |

Both are written once by `python port_fill.py inputs` (the terminal outlines are unions / differences of OpenStreetMap land-use polygons
in Overture's `base_land_use`) and then edited by hand if need be: the stage reads the geojson, not the land use.

## What is real, what is generated

Real: that the terminal or yard is there, its outline (OpenStreetMap land use, or the site outline), and the first year of container
handling or of the yard (cited; **estimated** where `year_basis` says so: Maher 1963, Port Jersey 1977, South Brooklyn 1972 are estimates
of this stage). Generated: every container block, its height, the position of every car, and the years each appears.

## Rules and constants (all named at the top of `port_fill.py`, with the fact each comes from)

Container terminals
- **Free yard** = terminal outline, less water, less today's and vanished buildings (`county_buildings`, `nyc_buildings`) buffered
  6 m, less roads (`roads_local`, `roads_region`) buffered half-carriageway (service 4 m ... trunk 10 m, assumed) + 3 m, less rail
  (`rail.parquet`) buffered 2.5 + 3 m, less a 35 m apron along every water edge (the cranes' rails: gauge 30.5 m plus a lane).
- **Bearing**: the length-weighted dominant direction of the outline where it meets water (3-degree bins); fallback the long side of the
  minimum rotated rectangle. Rows lie on it.
- **Blocks**: 6 containers wide (6 x 2.44 m = 14.6 m), 5-20 forty-foot lengths long (61-244 m), aisles between rows 8-26 m, between
  blocks 12.2-24.4 m, each drawn from a hash of the terminal and the position.
- **Pieces**: every block is cut into pieces of 2-4 forty-foot lengths (24-49 m); a block has a height of 2-5 containers (hash) and each
  piece varies it by one; `height_m` = containers x 2.6 m, `storeys` = containers. A piece is kept only if it lies wholly on free yard
  (or at least 85 % of it does: the free part is kept); 0.15 m is taken off every side so neighbours do not touch.
- **Years**: stacks of a period appear from the year after its opening, over nine years, the quay's edge first (75 % by distance to the
  water, 25 % hash): `start = open + 1 + 9 x (0.75 x d + 0.25 x h)`. A period that closed ends over one year after the closing year.
  Howland Hook has two periods (1973-1987, 1996-): two rows at each position with separate ids and no common years. Nothing is done about
  made land: the lead's ground rule holds stacks back until their ground exists.
- Coverage of the free yard is 24-37 % (target 35-45 %); the shortfall is pieces rejected at obstacles and the narrow slips of free ground.

Rail yards
- Cars on the yard tracks of `rail.parquet` inside the outline (not bridges or tunnels; segments longer than 25 m): boxes 3 m wide, 4 m
  high, 18-26 m long (15.5-22.9 m in the subway yards: A / B Division car lengths), 0.8 m apart, in runs of 3-10 cars, gaps sized for
  40 % of the track length; a car that touches another is dropped; cars keep 1.5 m off buildings and off roads and water.
- `start_year` = the yard's opening year + 0-5 years (hash). `material` `railcar`, `evidence` `yard+railcars`.
- Every segment inside the outline is treated as yard track: running lines through a yard (the Northeast Corridor at Sunnyside) hold
  cars too, which is wrong; tracks in 1910 or 1926 were not today's.
- Not done for a yard whose opening year is not in a source: Croxton, Kearny / Harrison, Oak Point, Fresh Pond, Little Ferry, North Bergen,
  Elizabeth's E-Rail and CSX South Kearny (see `data/research/ports.md`).

## Sources per terminal

| terminal | outline | first container year | source |
|---|---|---|---|
| Port Newark | OSM land use 'Port Newark-Elizabeth' etc, north of 40.6835 N | 1956 (source) | en.wikipedia.org/wiki/Port_Newark%E2%80%93Elizabeth_Marine_Terminal |
| Elizabeth-PA Marine Terminal | same polygon, south of 40.6835 N, + APM, Columbia | 1962 (source) | en.wikipedia.org/wiki/Port_of_New_York_and_New_Jersey |
| Maher Terminals | OSM 'Maher Terminals' | 1963 (estimated) | not found |
| Port Jersey / GCT Bayonne | OSM 'Port Liberty Bayonne' | 1977 (estimated; pier built 1972-76) | en.wikipedia.org/wiki/Port_Jersey |
| Howland Hook / GCT New York | OSM 'Port Liberty New York' | 1973-1986, 1996- (1973 source; idle years from the owner's brief) | en.wikipedia.org/wiki/Howland_Hook_Marine_Terminal |
| Red Hook Container Terminal | OSM 'Red Hook Container Terminal' | 1981 (brief; Wikipedia: 'built in the 1980s') | en.wikipedia.org/wiki/Red_Hook_Container_Terminal |
| South Brooklyn Marine Terminal | OSM 'South Brooklyn Marine Terminal' | 1972 (estimated); mostly break-bulk | none |

## Results (python port_fill.py; numbers in data/interim/ports/stats.json, check.json)

| terminal | rows | covered ha | free yard ha | share |
|---|---|---|---|---|
| Port Newark | 1658 | 84.8 | 284.1 | 0.30 |
| Elizabeth-PAMT | 1238 | 63.8 | 186.2 | 0.34 |
| Maher | 1243 | 63.8 | 183.9 | 0.35 |
| Port Jersey / GCT Bayonne | 442 | 22.6 | 61.2 | 0.37 |
| Howland Hook (per period) | 330 | 16.4 | 59.1 | 0.28 |
| Red Hook | 31 | 1.5 | 6.4 | 0.24 |
| South Brooklyn | 48 | 2.3 | 14.8 | 0.15 |

Yards: 4,474 cars in 16 of 18 yards (Livonia and Pitkin have no track longer than 25 m inside their outlines; Corona and West Side Yard are nearly empty: their track is mostly tunnel, bridge or deck).
