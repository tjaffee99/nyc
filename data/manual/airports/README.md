# Airfields (`data/manual/airports/`)

`pipeline/airports.py` draws the runways, taxiways, aprons and heliport decks that OpenStreetMap
maps today (Overture 2026-10-21.0 `region_airports.parquet`), each from its airport's opening year
(`data/tables/airports.csv`) and never before its ground (terrain land-year grids). This folder holds
what that cannot give: pavement built later than its airport, and airfields that are gone.

| file | what | read by |
|---|---|---|
| `pavement_dates.csv` | per-feature years by Overture id (Bay format: `part` = `whole` / `axis_interval` / `zone_clip`) | `airports.dated_pavement` |
| `pavement_zones.geojson` | dated zones (`zone`, `start_year`) that clip a feature (`zone_clip` rows) | same |
| `extra_outlines.geojson` | outlines of airfields that are not aerodromes on today's map (`name`, `class`) | `airports.main` -> `data/interim/airports.parquet` |
| `extra_pavement.geojson` | traced pavement of vanished airfields (`airport`, `kind`, `start_year`, `end_year`, `width_m`, `confidence`, `source_url`, `note`) | `airports.main` |
| `tools/fbf.py`, `tools/vanished.py`, `tools/topo_crop.py` | how the files were made | by hand |

Licences: OpenStreetMap data (c) OpenStreetMap contributors, ODbL. USGS Historical Topographic Map
Collection GeoTIFFs: public domain. Wikipedia text: CC BY-SA (facts only, article URL per row).
Abandoned & Little-Known Airfields (airfields-freeman.com): facts quoted with the page URL.

## John F. Kennedy International Airport (6 rows of `pavement_dates.csv`)
Wikipedia: "The first flight from Idlewild was on July 1, 1948"; "Runway 31R (originally 8,000 ft) is
still in use; runway 31L (originally 9,500 ft) opened soon after the rest of the airport"; "Runway 4
(originally 8,000 ft, now runway 4L) opened June 1949 and runway 4R was added ten years later".
Runway 4L/22R (Overture `4c8fb32c`) and its two stopways: 1949.45; runway 4R/22L (`ec6812bb`) and its two
stopways: 1959. Runways 13L/31R and 13R/31L keep the opening year 1948.
NOT done: the lengthenings (31L 9,500 -> 14,511 ft, 4L 8,000 -> 12,079 ft, 31R 8,000 -> 10,000 ft), the
closed runways 1R/19L (to 1957), 7R/25L (to about 1966) and 14/32 (to 1990), and the taxiways and
aprons of Terminal City (1957-62) and later: all taxiways and aprons start in 1948 (estimated).

## LaGuardia Airport
Nothing here: all pavement from 1939 ("dedicated on October 15, 1939 ... opened for business on
December 2"). NOT done: the four runways of 1939 (18/36 closed about 1947, 9/27 about 1958), the shift
of 13/31 about 1961 and the runway decks built over Flushing Bay and Bowery Bay in the 1960s; the North
Beach airfield of 1929-1939 on the same ground has no outline.

## Floyd Bennett Field (`tools/fbf.py`)
* Outline: the National Park Service unit "Floyd Bennett Field" (OSM relation 9460480, via Overture
  land use), outer ring, simplified to 5 m, 520 ha. `airports.csv`: 1931-1971.
* Pavement: OpenStreetMap maps all the historic concrete as one apron polygon with 15 holes (relation
  9463532, Overture `03717e73`, 91.6 ha). It is clipped by five zones = the centre lines of the abandoned
  runways (OSM ways tagged `abandoned:aeroway=runway`, API extract of 2026-11-10 in
  `data/raw/airports/osm/fbf.osm`), buffered by 50 m:
  15-33 and old 6-24 from 1931 ("two perpendicular concrete runways in a 'T' shape", 3,110 and 4,000 ft),
  1-19 and 12-30 from 1938 ("the two runways constructed in 1937-1938"), new 6-24 from 1942 ("A new Runway
  6-24 was constructed in 1942") - Wikipedia, Floyd Bennett Field. Where runways cross, the older wins.
* ESTIMATED / not separated: the lengthenings of 1936, 1942 and about 1952 (each runway is drawn at
  its final length from its first year); everything outside the five zones (taxiways, hangar and
  seaplane aprons, the Navy's 1941-45 additions; 52 ha with the 1931 runways) takes 1931.
* The concrete is still there (park roads, parking), so it does not end in 1971; the Coast Guard /
  NYPD apron on the Jamaica Bay side is the heliport of `airports.csv` (1937).

## Flushing Airport (`tools/vanished.py`, `tools/topo_crop.py`)
Sheets: USGS Flushing 1:24,000, 1966 edition (scan 137330, with purple photorevisions) and 1947
(scan 138247). The 1966 sheet draws two landing strips (dashed outline) in a V from 20th Avenue; the
1947 sheet shows the same two dry strips across the marsh. Traced on a 1 m crop in UTM 18N, read off
a 100 m grid by eye (+-10 m), checked by overlaying the result on the sheet:
north-south strip 877 m x 30 m, north-east strip 797 m x 28 m.
Years: airfield 1929-1984 (Wikipedia: "constructed ... beginning in 1927. The airport opened two
years later, in May 1929"; closed 1984). Paving ESTIMATED 1957: "an unpaved landing area" on c. 1951
and 1954 air photos, "2 paved runways" on the July 1960 sectional chart, "NE/SW runway closed" on the
1965 chart (airfields-freeman.com). Before 1957 the field's clay strips are not drawn (no pavement).
Outline (34 ha, ESTIMATED): 20th Avenue, the property line and Linden Place, the ditch beside the
north-east strip, Mill Creek - the part in use as drawn in 1966, not the 250-300 acre property.

## Miller Field
Outline: the NPS unit "Miller Field" (OpenStreetMap, via Overture land use), 66.6 ha; `airports.csv`
1921-1969 ("founded in November 1919 and completed in 1921"; "closed as an airbase in 1969").
"It had a grass runway" (Wikipedia): the two strips drawn dashed on the USGS The Narrows 1:24,000
sheet of 1955 (scan 139985) are traced (975 x 44 m, 601 x 36 m) and kept in `extra_pavement.geojson`
as `kind = turf_strip`, which `airports.py` does NOT draw (it is not pavement). The terrain stage
can use them as mown strips if wanted.

## Not traced
Holmes Airport (Jackson Heights, 16 March 1929 - 1940, two gravel runways of 3,000 and 2,800 ft,
"southeast of the intersection of Astoria Boulevard & East Brooklyn Queens Expressway"): no USGS
1:24,000 edition exists for its years (the series starts 1947). North Beach Airport (1929-1939,
under LaGuardia). Seaplane bases (points in OSM, no pavement): New York Skyports (E 23rd St),
Evers (Bronx), Edo (College Point), Jamaica Bay.

# The counties around the city (2026-11-10)

`airports.py` reads the same extract for the wider map (`common.REGION_BBOX`); an airfield is drawn if
it lies inside the map outline and `data/tables/airports.csv` dates it. `airports.csv` has an optional
column `runway_width_m` (the cited width; without it 45 m at international airports, 23 m elsewhere).
Made land: pieces wait for their ground as in the city; a researched opening year is never moved —
`data/interim/airports/ground_conflicts.csv` (written by the stage) lists every airfield with the latest
land year under its outline.

## Newark Liberty International Airport (`tools/ewr.py`, 199 rows of `pavement_dates.csv`, 3 zones)
Wikipedia: opened 1 October 1928 on 68 acres of reclaimed meadow with a 1,600 ft runway; "In 1952, Runways
1/19 and 6/24 were closed and a new Runway 4/22 (now 4R/22L) opened at a length of 7000 ft"; "Runway 4L/22R
opened in 1970 at a length of 8200 ft"; "takeoff from runway 28" on 16 December 1951 (today's 11/29);
North Terminal 1953-1997; "Former Terminal A and present Terminal B opened in 1973"; Terminal C June 1988;
new Terminal A 8 December 2022.
* Documented: runway 4R/22L 1952.85 (November 1952), runway 4L/22R 1970.
* ESTIMATED (each row says so): runway 11/29 from 1951 ("by then": the year it was built was not found);
  the lengthenings of both 4/22 runways are not separated; every taxiway takes the year of the nearest
  runway; the single apron polygon of the central terminal area (Overture `45291dcc`, 89.5 ha) is cut by
  latitude between the terminal buildings into Terminal C (1988.45), A / B (1973) and new A (2022.9, within
  ~500 m of the new building), taxiways west of 4L/22R follow those bands; north cargo apron 1953 (the
  North Terminal's site). The two aprons by Building One keep the opening year 1928.
* NOT done: the airport of 1928-1952 (the first runway, 1/19, 6/24, the 1935 terminal apron as it was).
  Between 1928 and 1951 only the two aprons by Building One are drawn; the airfield outline (terrain grass)
  is today's 807 ha from 1928 — far larger than the 68 acres of 1928.

## Teterboro, Westchester County, Essex County (Caldwell), Linden
Whole airports from their opening year (`airports.csv`: 1919, 1942, 1929 ESTIMATED, 1942); no runway of
theirs is dated on its own (ESTIMATED: Teterboro's paved runways are certainly later than 1919). Linden's
"original airport with its intersecting runways" (to 1998) is not traced.

## Not drawn
* Greenwood Lake Airport (West Milford), Hill Top Airport, the heliports of the counties (Haverstraw,
  Meadowlands): no opening year found — `airports.py` leaves undated airfields out and logs them.
* Lincoln Park Airport (Morris County) and Hadley Field (South Plainfield, Middlesex County; 40.556, -74.43)
  lie outside the map outline. Little Ferry / Ridgefield Park seaplane base: no pavement, no year found.
* Vanished airfields of the counties (airfields-freeman.com, facts only): 13 rows of `airports.csv` marked
  "label only" and 13 label points in `data/tables/park_names.csv` (Rockland, Miller, Christie, Spring
  Valley, Orangeburg, Ramapo Valley (Mahwah), Totowa-Wayne, Westfield (Clark), Reynolds Field, Armonk,
  Croton Airpark, Somers, La Roe, Peekskill Seaplane Base). Positions are the source's, to 2-3 decimals; no
  outline was traced, nothing is drawn on the ground. Arcola Airport (Paramus, closed 1932-33) and Murchio
  Airport (Wayne) are left out: no opening year in the source. Candidates for tracing from the 1940s-50s USGS
  sheets (as Flushing Airport, `tools/vanished.py`): Totowa-Wayne, Spring Valley, Croton Airpark (paved).
* `tools/counties_tables.py` wrote the counties' rows of `airports.csv`, `golf_courses.csv`, `park_names.csv`.
