# routes.csv — researched routes (highways, ferries, vanished roads)

Read by `pipeline/roads.py`. One row per stretch with its own years:

```
route_id,name,mode,year_start,year_end,elevated,segment_seq,geom_type,geom,note,source_url
```

- `mode`: `freeway` / `highway` / `bridge` (a road), `ferry`, `road` (a vanished street or colonial road).
  Rail of any kind (els, subways, railroads, streetcars) is `pipeline/transit.py`'s and is not drawn from here.
- `year_start`, `year_end`: decimal years (1954-06-23 = 1954.47); `9999` = still there. A year known only as a
  year is written as that year.
- `elevated`: `ground` | `viaduct` (drawn 9 m up with deck and bents) | `tunnel` (not drawn).
- `geom_type` is always `lonlat`; `geom` = `lon lat; lon lat; …`.
- `note` says what the source says; `estimated` marks every year or line that is not a record.
- every row has a `source_url`.

## What the rows do

1. **Standing highways, parkways, bridge and tunnel approaches** (`year_end` 9999; modes freeway / highway /
   bridge; 157 rows). They are **not drawn**: they date Overture's geometry. A motorway / trunk segment takes
   the year of the row whose line runs along it (within 150 m and parallel; `roads.py freeway_items`), ramps
   the latest year of the roads they join. A motorway segment that no row dates stays on the 1960 default and
   is listed in `data/interim/roads/report.json` — a missing row, not a date.
2. **What is gone** (drawn from the row's line between its years): the elevated West Side (Miller) Highway
   in ten stretches by opening and demolition (`miller_*`), ferries (`ferry_*`), vanished streets and colonial
   roads traced in OpenHistoricalMap (`ohm_<way id>`).

## Where the lines come from (never from memory)

- **Highways**: the shortest path along the named motorway / trunk segments of
  `data/raw/overture/<release>/freeways.parquet` (through their connectors) between two anchors. An anchor is
  the point of the highway nearest to a named cross street or crossing highway (the street's line is extended
  to the highway where it stops short), or an end of the named highway. `all` rows are every mainline segment
  carrying the name (bridge and tunnel approaches). The definitions — names, anchors, year, note, source —
  are `roads_tools/hw_defs.py`.
- **West Side Elevated Highway**: the centre line of West Street / Eleventh Avenue / Twelfth Avenue (Overture
  trunk segments), which it stood over, cut at the cross streets named in the source.
- **Ferries** (`roads_tools/ferry_defs.py`): terminals are the foot of the named street (its end vertex toward
  the water, or where it meets the waterfront street — on the Hudson side West Street, the shore before Battery
  Park City) or the centroid of the named terminal building (Overture buildings). The course over the water is
  schematic: a straight line, bent once where it would cross land on the terrain grid (land made after the
  ferry began counts as water); an end that now lies inland is pulled back to today's shore.
- **OpenHistoricalMap roads** (`roads_tools/ohm_roads.py`; OHM data is CC0): Overpass
  `way[highway][end_date]` in the map box (cached: `data/raw/roads/ohm/highways_enddate.json`). Kept: road-like
  ways inside the five boroughs, at least 150 m long, begun before 1870 (or the Long Island Motor Parkway),
  whose line does NOT run along a road of today (less than 40 % of it within 15 m of, and parallel to, an
  Overture road): a renamed or rebuilt street is carried by today's street. 137 ways, 94 km: the old town
  roads of Kings County (Gowanus Road, Jamaica Road, Flatbush Road, Gravesend Neck Road, the old line of the
  Kings Highway…), the Bloomingdale Road's old line from 86th Street to Manhattanville, the lanes on the site of
  Central Park (to 1857), the Lower East Side and Civic Center streets erased by housing projects and
  approaches, the Long Island Motor Parkway (1912-1938).
  Years are OHM's. OHM marks many as `arbitrary`: a placeholder start (1600) is replaced by **1704**, the year
  the colonial highway act had the King's Highway and the county roads laid out (the roads are older), and an
  end "about the date of the map that no longer shows it" is kept — both flagged `estimated` in the note; lines
  traced from a schematic map are flagged "line accuracy low". Researched instead of OHM's: the Bloomingdale
  Road (1703 - 1868). Dropped: way 198423801 (crosses Central Park, end-dated 1902).

## Sources and licences

- Opening and closing dates: Wikipedia articles (CC BY-SA; facts only, URL per row) and nycroads.com road
  histories (facts only, URL per row).
- Geometry: Overture Maps 2026-10-21.0 transportation and buildings (ODbL / CDLA; OpenStreetMap-derived),
  OpenHistoricalMap (CC0).

## Not in the file (looked for, not found as a traced line or a dated source)

- The Eastern Post Road and the Kingsbridge Road through Manhattan: OHM has no named trace (only a
  "Road to Boston" below Chatham Square that is today's Park Row / Bowery, and one 0.8 km piece of the
  Kingsbridge Road at Marble Hill, 1853-1935, which is in the file); two unnamed OHM ways across the site of
  Central Park are probably parts of the Post Road and are in the file as "(unnamed old road)".
- Ferries whose end year the sources leave open (South Ferry – Atlantic Avenue 1836–?, Hamilton Avenue 1846–?,
  Catherine Ferry 1795–?, Grand Street, Houston Street, 10th and 23rd Street to Greenpoint, the Astoria ferry),
  the 23rd Street Hudson ferries, and the NYC Ferry routes other than the East River route.
- Highways outside the city inside the map's faded edge (Northern State Parkway, Saw Mill River Parkway,
  Sunrise Highway): no row, they stay on the default year.

## Rebuilding

```
cd data/manual/roads_tools
../../../.venv/bin/python make_routes.py          # -> data/manual/routes.csv (prints every row's length and ends)
../../../.venv/bin/python make_street_dates.py    # -> data/tables/street_dates.csv
```

Edit `hw_defs.py` / `ferry_defs.py` / `ohm_roads.py` / `make_street_dates.py`, not the CSVs: the CSVs are
written whole. `wiki.py`, `wraw.py`, `nyr.py` fetch and cache the cited pages (data/raw/roads/) and print
the sentences that carry a year.
