# Hudson waterfront: railroad yards and lost terminals (round of 2026-11-11, night)

Files: `data/manual/ports/yards_historic.geojson` (9 outlines, built by `data/manual/atlas/tools_hoboken2/write_yards.py`),
`data/tables/notable_demolished.hudson.csv` (9 rows), base-map tool `tools_hoboken2/basemap.py` (renders today's roads, rail,
buildings and the traced layers; used to read coordinates off). Raw pages: `data/interim/hudson_waterfront_raw/wp_*.txt`
(Wikipedia raw wikitext, paced, User-Agent `NYCThroughTime-research/0.1`). Other facts came through WebFetch / WebSearch of the
pages named in each outline's `basis` (the search snippets are marked "via search snippet" where used).

## Method and its limit

No plan of any yard or terminal was opened: the sources give years and a point, not geometry. Every outline is hand-drawn
from today's street lines (Overture), today's track fans (`rail.parquet`) and the 1919 Hopkins layer's coverage, read off base
maps, so **good to about 50-150 m (stated per yard)**. Sizes of terminal blocks are **estimated** (the `shape_note` says so);
points are Wikipedia's coordinates, which for stations are the station site (+-40 m).
The USGS sheets and Hopkins plates were not re-opened (raw scans are not on this machine).

## Yards (`yards_historic.geojson`)

| id | years | basis |
|---|---|---|
| prr_exchange_place_terminal_tracks | 1873-1961 | 1873 12-track ferry terminal (timeline); last passenger train 17 Nov 1961 (Wikipedia Exchange Place (PRR station)) |
| prr_harsimus_cove_yard | 1868-1976 | freight terminal 1868; cove filled by 1870 a quarter mile east of Henderson St; stockyards between the terminals; end ESTIMATED ("abandoned by the 1970s"; Newport from 1986) |
| harsimus_stem_embankment | 1905-9999 | built 1901-1905 (NR nomination, via search snippet); still stands; no tracks in today's data, so tracks must be generated |
| erie_pavonia_terminal_yard | 1861-1959 | opened 1 May 1861; closed 12 Dec 1958; demolished 1961; end 1959 ESTIMATED |
| cnj_communipaw_terminal_yard | 1864-1967 | terminal 1864 / 1889; passenger closing 30 Apr 1967; freight after that not checked |
| lehigh_valley_black_tom_national_docks | 1883-1976 | National Docks Railway 1883; end ESTIMATED (Liberty State Park 1976) |
| dlw_hoboken_terminal_yard | 1862-9999 | first terminal 14 Nov 1862; still a yard (today's tracks already in rail.parquet) |
| west_shore_weehawken_terminal_yard | 1884-1959 | Wikipedia Weehawken Terminal; length of the yard not in the sources |
| greenville_yard_prr | 1904-9999 | PRR 1904; still a yard |

Not written: the Erie's Weehawken yards (no place found in an opened source), the Lehigh Valley's 1889 South Cove terminal and
its Jersey City yards beyond Black Tom, the Pennsylvania's Jersey City stockyards as a separate outline (inside the Harsimus
Cove polygon), Bayonne's yards.

## Lost buildings (`notable_demolished.hudson.csv`)

PRR Exchange Place 1873-84 and 1891-1963; Erie Pavonia 1861-73 and 1887-1961; DL&W Hoboken 1862-73, 1873-85 and 1885-1905;
West Shore Weehawken 1884-1959; Lehigh Valley Black Tom pier and warehouses 1883-1916. Years from the pages named in each
row; sizes and heights estimated; the 1873 Pavonia fire year is from an external-link title in the article (not read).

Not written, with reasons:
- **Hamburg-American and North German Lloyd piers**: the NDL piers stood "at the foot of 3rd and 4th Streets" and burned 30 June
  1900 (three piers over "a third of a mile"), the HAL piers lay south of them (Nos. 5, 6 burned 1921, No. 4 1944), but no pier
  length or exact position was found: not placeable within 40 m.
- **Colgate works** (85-99 Hudson St, demolished 1985): the address and the clock's present position (40.712028 N 74.03389 W,
  400 m south of the old building) put it near 40.7156 N 74.034 W, +-60 m, and no year of building was found.
- **Stevens Castle** (1853-1959, Castle Point, replaced by the Howe Center): no coordinates or size in any opened source.
- **Maxwell House plant** (built 1939, closed March 1992, 24 acres, Hoboken waterfront 10th-12th Streets): no building plan.
- **Lipton Tea building**: not lost (Hudson Tea Building, 1500 Hudson St, stands; built 1913-19, closed 1960s).
- **Holland America pier, Bethlehem Steel / Tietjen & Lang sheds** (yard founded 1890, 12th-16th Streets, closed 1999), the
  stockyards' abattoir, Jersey City Hall's predecessors, the Hoboken elevated station, the Courthouse predecessor, the Lorillard
  and Dixon works: no opened source with a position.

## Part 3 (more of Hoboken from the atlases): not done

The Library of Congress item page (`loc.gov/item/sanborn05511_007/`) answered 503 Service Unavailable on three tries, so the IIIF
base of vol. 7's plates could not be found; the raw scans of the three plates already traced are not on this machine either.
No layer `hudson_hoboken2_*` exists. The method (`tools_hudson/loc_register.py`, `atlas.py`) is unchanged and could be run when
LoC answers; the existing Hoboken layer finds about 120 of 400 lots per plate, so a continuation would be thin.

## What the lead must change to read these files

1. `port_fill.build_yards()` reads only `yards.geojson` and draws cars on **today's** `rail.parquet` tracks, always to 9999
   (`end_year=STILL_EXISTS`). For the historic yards:
   - read `yards_historic.geojson` as well (`Y = yards + historic`); properties: `id`, `name`, `start_year`, `end_year`,
     `year_basis` (a dict `{start, end}`, not a string), `source`, `basis`, `outline`, `kind`, `track_bearing_deg`, `track_gap_m`.
   - the lost yards (all except the three still open) have **no track in today's data**: generate parallel tracks inside the
     polygon at `track_bearing_deg` and `track_gap_m` (about 4.6 m) instead of clipping `rail.parquet`, and emit
     `end_year = props.end_year` (cars end over one year after it, as the terminals' periods do).
   - for `harsimus_stem_embankment`, `dlw_hoboken_terminal_yard` and `greenville_yard_prr` (end 9999) the clipped
     `rail.parquet` tracks work; the embankment's seven tracks need generating.
   - ground rule: Newport, Harsimus Cove, Liberty State Park and Weehawken's shore are made land: the yard's cars wait for their
     ground as the stacks do; the 1873 yards stand on land filled by 1870 (decision 11 may date it later: check
     `fill_zones_counties.csv`).
2. `nyc_extras.notable()` globs `notable_demolished*.csv`, so `notable_demolished.hudson.csv` is read as it stands (same
   columns as the sites file; rows are boxes: `footprint_m` w x d metres, `rotation_deg` clockwise from east-west).
3. The ground rule may push the 1861-73 rows later if the terrain dates Pavonia / Paulus Hook's made land late.
