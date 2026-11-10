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
