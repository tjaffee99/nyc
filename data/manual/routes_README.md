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
   bridge; 365 rows of 179 routes: 95 routes in the city, 84 in the counties around it). They are **not
   drawn**: they date Overture's geometry. A motorway / trunk segment takes the year of the row whose line
   runs along it (within 150 m and parallel; `roads.py freeway_items`), ramps the latest year of the roads
   they join. A motorway segment that no row dates stays on the 1960 default and is listed in
   `data/interim/roads/report.json` (`freeways.on_default`, km by county in `freeways.km_by_area`) — a missing
   row, not a date. A trunk road without a row is an arterial street: dated like the main roads, by the
   buildings along it.
2. **What is gone** (drawn from the row's line between its years): the elevated West Side (Miller) Highway
   in ten stretches by opening and demolition (`miller_*`), ferries (`ferry_*`), vanished streets and colonial
   roads traced in OpenHistoricalMap (`ohm_<way id>`).

## Where the lines come from (never from memory)

- **Highways**: the shortest path along the named motorway / trunk segments of
  `data/raw/overture/<release>/freeways.parquet` (through their connectors) between two anchors. An anchor is
  the point of the highway nearest to a named cross street or crossing highway (the street's line is extended
  to the highway where it stops short), or an end of the named highway. `all` rows are every mainline segment
  carrying the name (bridge and tunnel approaches). The definitions — names, anchors, year, note, source —
  are `roads_tools/hw_defs.py` (the city) and `roads_tools/hw_defs_counties.py` (Hudson, Bergen, Essex, Union,
  Passaic, Westchester, Rockland).
- **Highways of the counties** (`hw_defs_counties.py`, 84 routes): most New Jersey highways have no name in
  Overture, only a number, so a definition may select segments by route number — `ref:US:I 684`,
  `ref:US:NJ 21`, `ref0:…` for the unnamed segments only, `class:motorway` to leave out the stretches where
  the numbered route is an old road. The numbers are Overture's `routes` (OpenStreetMap route relations),
  fetched once by `roads_tools/fetch_refs.py` into `data/raw/roads/overture/freeway_refs.parquet` (the
  pipeline's `freeways.parquet` does not carry them). Two more anchors need no typed coordinate: `endof` (the
  end of another highway: where the Eastern Spur rejoins the turnpike) and `border` (where the highway crosses
  a county line of the TIGER outlines: the Palisades Parkway at the state line); an `all` row can be cut to
  the counties it is about (`CLIP`: the Taconic in Westchester, Route 17 in Bergen). Each row is followed by
  the other carriageway(s) of its path (`segment_seq` 2…): a row dates what runs within 150 m of it, and the
  turnpike's four roadways or a parkway's wide median are wider than that.
  A hint coordinate (`x("Central Avenue", (-74.211, 40.753))`) only tells two crossings of the same name
  apart; the anchor is the crossing itself, and a wrong hint makes the row fail, not move.
  `make_routes.py cross "<name>"` lists the named roads crossing a highway in order, to choose anchors from.
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
  route numbers likewise (Overture `routes`), county lines from TIGER/Line 2024 (public domain),
  OpenHistoricalMap (CC0).

## The counties' rows: what is a record and what is an estimate

Every year is a sentence of the page in `source_url`, quoted or paraphrased in `note`. 24 of the 84 routes
say `estimated`, for one of these reasons (the note says which):

- **a bound, not an opening**: the Palisades Interstate Parkway north of the Thruway (opened section by
  section from the late 1940s, dates not found: the day the whole parkway was open, 1958-08-28) and its two
  miles between the state line and exit 5; Route 17 in Bergen County ("by 1937"); Route 208 ("by 1953", "by
  1960"); I-80 between Paterson and the Garden State Parkway ("by 1966");
- **one year for a stretch opened in stages**: the Palisades Parkway in New Jersey (the last section, 1957),
  I-78 from Route 24 to the turnpike (1974-77: 1977), I-280 west of Newark (1966-73: 1973), the Saw Mill
  River Parkway from Elmsford to Chappaqua (1930s: 1940), the Thruway north of Suffern, the Cross County
  Parkway (begun 1929, its wye to the Hutchinson open in 1932, finished 1947: 1932), US 1/9 along Newark
  Airport (1928);
- **a section end taken at the nearest crossing road**, where the source names a town or an exit that
  Overture does not: turnpike exit 15E at the Pulaski Skyway, "Cranford" at Route 28, "Paterson" at Route 20,
  "Passaic Park" at Route 3, "Yonkers" at the Cross County Parkway, "Chappaqua" at Quaker Road, "Suffern" at
  US 202;
- **sources that disagree**: I-684 north of Bedford Hills (one sentence has Purdys - Brewster open in 1969,
  another Goldens Bridge - Brewster finished in December 1974: the later), the Newark Bay Extension (completed
  1956-04-04; another article has it open through in September 1956: the earlier), the Taconic in Westchester
  (nycroads.com 1932; Wikipedia a ribbon-cutting in December 1931).

Replaced bridges keep the first bridge's year on today's line, as the Goethals Bridge does: the Tappan Zee
Bridge (1955-12-15; the Governor Mario M. Cuomo Bridge, parallel and just north, opened 2017-08-26 and
2018-09-11) and the Wittpenn Bridge (1930-11-05; its replacement 2021-10-02).

## Not in the file (looked for, not found as a traced line or a dated source)

- The Eastern Post Road and the Kingsbridge Road through Manhattan: OHM has no named trace (only a
  "Road to Boston" below Chatham Square that is today's Park Row / Bowery, and one 0.8 km piece of the
  Kingsbridge Road at Marble Hill, 1853-1935, which is in the file); two unnamed OHM ways across the site of
  Central Park are probably parts of the Post Road and are in the file as "(unnamed old road)".
- Ferries whose end year the sources leave open (South Ferry – Atlantic Avenue 1836–?, Hamilton Avenue 1846–?,
  Catherine Ferry 1795–?, Grand Street, Houston Street, 10th and 23rd Street to Greenpoint, the Astoria ferry),
  the 23rd Street Hudson ferries, and the NYC Ferry routes other than the East River route.
- Highways in the map's faded edge beyond the counties (Northern State Parkway, Sunrise Highway, Merritt
  Parkway, Connecticut Turnpike, I-78 west of Union County, the Taconic in Putnam County): no row, they stay
  on the default year.
- In the counties, no dated source was found for (they stay on the default and are listed in `report.json`):
  the US 46 freeway east of Hasbrouck Heights (Ridgefield Park - Fort Lee), McCarter Highway (Route 21 in
  Newark), McLean Boulevard (Route 20: "built by the 1930s"), the Newark - Jersey City Turnpike (Route 7), Port
  Jersey Boulevard, the Larry Doby Highway, Bergen Boulevard, short unnamed connectors.
- State highways classed `trunk` without a row — US 22, Route 23, US 9W, US 202, NY 303, US 46 west of
  Clifton, US 1/9 through Elizabeth, Linden and Jersey City — are dated by the buildings along them (about
  200 km in the counties): right for an old road that became a state highway, too late or too early for a
  1930s bypass.
- Old roads of the counties: only the Boston Post Road in Westchester (1673) and the Paterson Plank Road
  (chartered 1851) have a row (`data/tables/street_dates.csv`). Not done for want of a dated source read in
  time: the Albany Post Road, the Newark Plank Road / Newark Turnpike (an act of 1765, bridges 1795, a plank
  road charter 1849 — which of today's roads carries it was not checked), the King's Highway in Rockland.

## Rebuilding

```
cd data/manual/roads_tools
../../../.venv/bin/python fetch_refs.py           # once: route numbers of the motorway / trunk segments
../../../.venv/bin/python make_routes.py          # the counties' rows (hw_defs_counties.py); every other row stays
../../../.venv/bin/python make_routes.py all      # everything from scratch (city highways, ferries, OHM roads too)
../../../.venv/bin/python make_routes.py cross "Garden State Parkway" "ref:US:NJ 21"   # crossing roads, in order
../../../.venv/bin/python make_street_dates.py    # -> data/tables/street_dates.csv
```

Every run prints one line per row (length, ends) and `!!` for a row that could not be built. Edit `hw_defs.py`
/ `hw_defs_counties.py` / `ferry_defs.py` / `ohm_roads.py` / `make_street_dates.py`, not the CSVs: the CSVs
are written by the scripts. `wiki.py`, `wraw.py`, `nyr.py` fetch and cache the cited pages (data/raw/roads/)
and print the sentences that carry a year.

The city's rows were built on the Overture extract of the city box. `make_routes.py all` rebuilds them on the
wider extract: an anchor "end of the named highway" then lies further out, which is why the rows that reach
beyond the city (Bronx River and Hutchinson River parkways, New England Thruway, the Thruway, the Palisades
Parkway, the turnpike) are defined in `hw_defs_counties.py` and take the place of their `hw_defs.py`
namesakes; the ferries' and the other city rows' anchors have hints or lie on roads that end in the city, but
an `all` rebuild has not been run since the box grew — compare the result with the committed file (`git diff
--stat data/manual/routes.csv`) before keeping it.

`data/tables/street_dates.csv`: the `boro` column takes boroughs (1-5) and county FIPS codes, separated by
spaces; a row without one applies to the five boroughs only, never to the counties (their Broadway or Kings
Highway is another road).
