# Aerial presence: did a building stand on each of today's footprints in 1924 and in 1951?

`presence.parquet` - one row per standing footprint of `data/interim/nyc_buildings.parquet` (1,096,365 rows, 10.7 MB):

| column | meaning |
|---|---|
| `doitt_id` | string, as in `nyc_buildings.parquet` (six ids occur twice in the city's file; one row is kept) |
| `bin` | the city's Building Identification Number |
| `p1924`, `p1951` | probability that a building stood on the outline in the photograph (0-1, three decimals). NaN = no photograph there. It is evidence from the image alone, calibrated so that both answers are equally likely beforehand; it is **not** a probability that *today's* building stood |
| `cover1924`, `cover1951` | the mosaic covers the footprint and a 3 m ring around it (at least 95 % of it) |
| `offset_m_1924`, `offset_m_1951` | length in metres of the registration shift applied to the outline for that mosaic (0 = none found, none applied) |
| `built_share_50m` | share of the ground within about 50 m that is building today (the "fabric" of the validation tables; below 0.15 the "open" call is weak, above 0.45 the "stood" call says little about today's building) |

`hand_check.csv` - the 220 footprints judged by eye on both mosaics (`seen1924`, `seen1951`: P building on the
outline, A open ground, U unclear, X no photograph). Hand-made validation data: keep it.

`tools/` - the scripts that drew the hand-check sheets and wrote this file and the research note from the
results (they read `data/interim/aerial/`).

Made by `pipeline/aerial_presence.py` (one stage, five cached steps: `tiles`, `features`, `synthetic`, `model`,
`predict`; `report` writes the tables below to `data/interim/aerial/report.md`). What the result says about
the placeholder years is in `data/research/aerial_years.md`.

## Source and terms

- **The photographs**: the City of New York's two historical mosaics, published by NYC OTI (Office of
  Technology and Innovation). 1924: "acquired from the Department of City Planning", the Fairchild sectional
  aerial map of the city; 1951: "acquired from the Department of Records Municipal Archives". Both "manually
  georeferenced using visible locations"; resolution and flight dates "unknown" (the city's metadata:
  https://github.com/CityOfNewYork/nyc-geo-metadata/blob/master/Metadata/Metadata_AerialImagery.md).
- **Where the tiles were read**: the public hosted tile layers of the city's ArcGIS Online account
  (owner `maps.nyc.data`, access "public"):
  "NYC Orthos 1924" https://nyc.maps.arcgis.com/home/item.html?id=afbb5db6b3fd494384357923e6c72622
  (`https://tiles.arcgis.com/tiles/yG5s3afENB5iO9fj/arcgis/rest/services/Ortho_1924_Mosaic/MapServer/tile/{z}/{y}/{x}`) and
  "NYC Orthos 1951" https://nyc.maps.arcgis.com/home/item.html?id=bca6c3f866f844b490925cc9c26d2e40
  (`.../NYC_Orthos_1951/MapServer/tile/{z}/{y}/{x}`). Standard web-mercator XYZ tiles, no key.
- **Not** the address in the brief: `https://maps.nyc.gov/xyz/1.0.0/photo/1924/...` now answers every request
  with one 10,519-byte picture reading "Map Tile Service has moved. Visit api-portal.nyc.gov". The new service
  (`https://api.nyc.gov/geoserver/gwc/service/tms/1.0.0/photo%3A1924@EPSG%3A900913@png8/...`) needs a
  subscription key from the city's API portal (401 without one). No key was used or asked for: the ArcGIS
  layers are the same mosaics, public.
- **Terms**: the ArcGIS items carry "NYC.gov Terms of Use" (https://www.nyc.gov/home/terms-of-use.page: the
  city's property, no clause against automated reading; do not disrupt the servers). The city's tile
  documentation (https://finder.nyc.gov/nyc-lib/tiles/index.html) states for the same tile sets: "(c) City of
  New York, licensed for reuse under the Creative Commons Attribution (CC BY 4.0) license". The 1924
  photographs were published in 1924 (public domain in the United States). **Attribution: (c) City of New
  York, NYC OTI, CC BY 4.0.** No image is redistributed: the tiles stay in `data/raw/aerial/` (gitignored), the
  repository carries only the per-footprint numbers.
- **Fetching**: one keep-alive connection, `User-Agent: NYCThroughTime-research/0.1`, about six tiles a
  second, every tile cached under `data/raw/aerial/<year>/17/<x>/<y>.jpg|png` (a `.404` marker for a tile the
  service does not have) and never fetched twice. 13,507 tiles per year (those within 25 m of a footprint),
  27,014 in all, 76 minutes, 193 MB (1924, JPEG) + 773 MB (1951, PNG).
- **Other years on the same account** (not used; listed in the metadata above): 1996, 2001-02, 2004 and every
  second year to 2024 - true orthophotographs at 0.3 m and better. They could date demolitions and the
  placeholder years after 1951 ("1955" ... "1980") the same way.

## What the tiles are

- Zoom: the services answer down to z20, z21 is 404. **The scans stop at z17.** z18 is z17 enlarged
  (correlation of a z18 block with the z17 block enlarged: 0.996 for 1924, 0.999 for 1951; share of the image
  energy above z17's own half-Nyquist: 1.3 % and 0.4 %). z17 is 0.905 m per pixel here; what can be told apart
  on the ground is about **2 m (1924) and 2.5 m (1951)**. A detached house is a blob of 8 x 12 pixels with a
  bright and a dark roof face; a row house is not separable from its neighbours.
- 1924 is sharp, summer, long shadows. 1951 is softer and harder in contrast (bright ground, dark roofs).
- **Dates checked**: in the 1924 mosaic Yankee Stadium (opened 1923) stands, the site of the Bronx County
  Courthouse (1931-34) is open ground and the old Waldorf-Astoria (demolished 1929) stands where the Empire
  State Building is; the 1951 mosaic has the courthouse, the Empire State and the Chrysler Building.
- **Gaps**: the 1924 mosaic is the sectional map itself - between its sheets run pure-white gutters 3 to 10 m
  wide, in places with the sheet number printed on a light patch. 4 tiles are missing for 1924, 111 for 1951
  (the Rockaway peninsula, the Great Kills shore), and some 1951 tiles are transparent. A footprint is
  "covered" when at least 95 % of it and of the 3 pixels around it is photograph (not transparent, not a
  white patch of 25 or more pure-white pixels in 1924, not flat black).

Coverage and registration, 1924:

| borough | footprints | covered % | shifted % | median shift m | 90% shift m |
|---|---|---|---|---|---|
| Bronx | 104241 | 98.0 | 32.4 | 4.0 | 6.6 |
| Brooklyn | 333207 | 98.2 | 42.1 | 5.5 | 6.5 |
| Manhattan | 55660 | 97.2 | 65.9 | 5.4 | 6.9 |
| Queens | 460852 | 97.8 | 23.7 | 4.9 | 6.6 |
| Staten Island | 142406 | 97.6 | 14.5 | 6.4 | 8.3 |
| all | 1096366 | 97.9 | 31.1 | 5.3 | 6.9 |

1951:

| borough | footprints | covered % | shifted % | median shift m | 90% shift m |
|---|---|---|---|---|---|
| Bronx | 104241 | 100.0 | 27.4 | 6.4 | 7.3 |
| Brooklyn | 333207 | 100.0 | 39.8 | 5.8 | 7.7 |
| Manhattan | 55660 | 100.0 | 53.4 | 4.5 | 6.6 |
| Queens | 460852 | 97.3 | 26.0 | 6.1 | 7.7 |
| Staten Island | 142406 | 98.4 | 12.5 | 6.6 | 7.8 |
| all | 1096366 | 98.6 | 30.0 | 5.7 | 7.7 |

## Method

1. **Registration.** The mosaics are off against today's map by several metres, differently from place to
   place. Per block of 8 x 8 tiles (1.85 km) and per quarter of it (930 m): the mean edge strength of the
   photograph along the outlines of the buildings the pipeline has standing that year is computed for every
   shift within +-8 pixels; its peak is where roof edges fall on outlines. The buildings are split in two
   halves at random and a shift is accepted only when both halves find the same peak (within a pixel, not on
   the border of the window; two noise peaks agree by chance about once in thirty). A quarter uses its own
   shift, else the block's, else none. A third of the footprints get a shift (two thirds in Manhattan, one
   in seven on Staten Island, where there is too little standing to register on); its median is 5.3 m (1924)
   and 5.7 m (1951), nine in ten are under 7-8 m. Tested on four Brooklyn blocks of 1924 before the rule was
   fixed: the shift found from the placeholder-year buildings alone and the best shift for the recorded-year
   buildings alone agreed within a pixel in two blocks, within two pixels in a third and not at all in the
   fourth (117 recorded buildings) - hence the two-halves rule. Not tested beyond that; where no shift was
   found the outline score is still searched over +-3 pixels.
2. **Features** (33 per footprint and year, image only - no size, shape, height, borough or year of today's
   building): brightness inside, in a 3-pixel ring and in the 5 pixels beyond (as local z-scores: exposure
   differs between frames), their spread, the shares of very dark and very bright pixels (shadows, roofs),
   edge strength along the outline (also the best within +-3 pixels), straightness of the edges along the
   building's own axes, and the same kinds of measure over 30 m and 100 m around (edge density, contrast,
   roof-sized blobs).
3. **Labels.** Recorded years (`year_src` lpc / assessor, exact) say where a building certainly stood - it is
   older than the photograph (3 years and more: 29,498 footprints for 1924, 67,282 for 1951). They hardly ever
   say where none stood: four in ten of the buildings recorded 3-8 years *after* 1924 show a building on their
   outline in the photograph (replacements, and assessor years that run late). So the "nothing stood" side is
   made of two sets that are certain: **street outlines** - real footprints of ordinary size moved onto the
   carriageway of the nearest street and turned along it (about 32,000 per year, in 58 blocks spread over the
   boroughs) - and **open ground** - footprints recorded 25 years or more after the photograph in
   surroundings where at least 12 buildings have recorded years, none before the photograph, and fewer than
   one in ten carries a placeholder year (15,942 and 12,152). Both sides weigh the same.
4. **Model.** Gradient-boosted trees on histograms (250 trees of depth 5), written in numpy because the
   environment has no scikit-learn; isotonic calibration on the hold-out scores.
5. **Hold-out.** Whole districts: squares of 3.8 km, in five folds; the final model is trained on all.
6. **Hand check.** 220 footprints (44 per borough: 30 placeholder-year, 14 recorded; at least 50 m2), drawn
   at random before any model existed, shown on each mosaic without their years (thumbnails of 47 m, the
   outline drawn unshifted) and judged by eye by the agent that built this - not by a person. It is the only
   test against something other than the recorded years; `tools/handsheet.py` redraws the sheets.

## Validation

### 1924

District hold-out, 77138 labelled outlines: AUC 0.957 (recorded-before vs street outlines 0.951, vs open ground 0.963)

| group | AUC | n stood | stood: p>=0.8 % | stood: p<=0.2 % | n street | street: p>=0.8 % | street: p<=0.2 % | n open | open: p>=0.8 % | open: p<=0.2 % |
|---|---|---|---|---|---|---|---|---|---|---|
| all | 0.957 | 29498 | 75.2 | 3.3 | 31698 | 4.2 | 66.9 | 15942 | 4.0 | 81.5 |
| Bronx | 0.924 | 2451 | 64.8 | 6.0 | 4121 | 5.0 | 64.8 | 745 | 2.7 | 79.3 |
| Brooklyn | 0.935 | 10615 | 77.2 | 2.2 | 7307 | 5.2 | 62.1 | 1223 | 18.9 | 59.9 |
| Manhattan | 0.922 | 13319 | 81.6 | 1.5 | 3238 | 10.5 | 45.8 | 323 | 28.5 | 33.7 |
| Queens | 0.913 | 2669 | 51.7 | 10.5 | 11922 | 2.7 | 70.9 | 3113 | 3.5 | 82.4 |
| Staten Island | 0.892 | 444 | 32.2 | 21.8 | 5110 | 1.7 | 79.8 | 10538 | 1.8 | 85.3 |
| dense >45% | 0.923 | 11625 | 81.7 | 1.7 | 4075 | 10.5 | 45.9 | 217 | 31.8 | 27.6 |
| detached 15-30% | 0.935 | 2579 | 52.4 | 8.3 | 14561 | 2.1 | 75.9 | 12022 | 3.2 | 83.3 |
| open <15% | 0.802 | 551 | 19.1 | 33.9 | 1070 | 0.7 | 82.9 | 1587 | 3.8 | 81.3 |
| rows 30-45% | 0.950 | 14743 | 76.1 | 2.4 | 11992 | 5.0 | 61.7 | 2116 | 5.9 | 76.4 |

Columns: "stood" = footprints recorded before the photograph; "street" and "open" = the two certain
"nothing stood" sets; fabric = share of the ground within 50 m that is building today.

Calibration:

| bin | n | mean p | share that stood |
|---|---|---|---|
| (-0.001, 0.1] | 29601.00 | 0.03 | 0.03 |
| (0.1, 0.2] | 5564.00 | 0.14 | 0.13 |
| (0.2, 0.35] | 5660.00 | 0.26 | 0.27 |
| (0.35, 0.5] | 4015.00 | 0.42 | 0.42 |
| (0.5, 0.65] | 3796.00 | 0.58 | 0.58 |
| (0.65, 0.8] | 4342.00 | 0.72 | 0.72 |
| (0.8, 0.9] | 4551.00 | 0.85 | 0.85 |
| (0.9, 1.0] | 19609.00 | 0.97 | 0.97 |

Hand check: 220 sampled, seen: {'P': 98, 'A': 91, 'U': 27, 'X': 4}; with a probability and a clear call: 188; AUC 0.918

| hand | between | p<=0.2 | p>=0.8 |
|---|---|---|---|
| building seen | 30 | 6 | 61 |
| open ground seen | 22 | 65 | 4 |

| group | seen building | seen open | p>=0.8: n | p>=0.8: building % | p<=0.2: n | p<=0.2: open % | buildings found % | open found % |
|---|---|---|---|---|---|---|---|---|
| all | 97 | 91 | 65 | 94 | 71 | 92 | 63 | 71 |
| Bronx | 16 | 20 | 9 | 78 | 14 | 93 | 44 | 65 |
| Brooklyn | 26 | 10 | 18 | 100 | 8 | 75 | 69 | 60 |
| Manhattan | 37 | 1 | 32 | 100 | 3 | 33 | 86 | 100 |
| Queens | 14 | 24 | 5 | 80 | 17 | 94 | 29 | 67 |
| Staten Island | 4 | 36 | 1 | 0 | 29 | 100 | 0 | 81 |

| call | n | right % | share of its side found % |
|---|---|---|---|
| p >= 0.95 | 32 | 94 | 31 |
| p >= 0.9 | 44 | 93 | 42 |
| p >= 0.8 | 65 | 94 | 63 |
| p >= 0.7 | 74 | 89 | 68 |
| p >= 0.6 | 86 | 85 | 75 |
| p <= 0.05 | 42 | 100 | 46 |
| p <= 0.1 | 56 | 98 | 60 |
| p <= 0.2 | 71 | 92 | 71 |
| p <= 0.3 | 78 | 91 | 78 |
| p <= 0.4 | 83 | 88 | 80 |

Unclear by eye (27): mean p 0.65

### 1951

District hold-out, 111267 labelled outlines: AUC 0.936 (recorded-before vs street outlines 0.914, vs open ground 0.957)

| group | AUC | n stood | stood: p>=0.8 % | stood: p<=0.2 % | n street | street: p>=0.8 % | street: p<=0.2 % | n open | open: p>=0.8 % | open: p<=0.2 % |
|---|---|---|---|---|---|---|---|---|---|---|
| all | 0.936 | 67282 | 68.7 | 4.4 | 31833 | 5.9 | 54.3 | 12152 | 3.3 | 81.0 |
| Bronx | 0.918 | 9976 | 70.4 | 6.1 | 4137 | 5.6 | 53.9 | 471 | 0.8 | 80.9 |
| Brooklyn | 0.925 | 19850 | 72.0 | 2.5 | 7320 | 4.9 | 48.7 | 877 | 11.6 | 69.4 |
| Manhattan | 0.857 | 19733 | 78.9 | 2.4 | 3243 | 20.8 | 26.6 | 167 | 40.7 | 32.3 |
| Queens | 0.890 | 16175 | 54.2 | 6.7 | 11987 | 4.2 | 56.9 | 357 | 7.6 | 69.5 |
| Staten Island | 0.888 | 1548 | 34.9 | 19.8 | 5146 | 2.4 | 74.1 | 10280 | 1.9 | 83.2 |
| dense >45% | 0.880 | 20463 | 80.6 | 1.6 | 4081 | 17.0 | 29.4 | 142 | 50.7 | 24.6 |
| detached 15-30% | 0.920 | 12781 | 47.5 | 9.0 | 14637 | 2.9 | 63.7 | 9082 | 2.3 | 83.2 |
| open <15% | 0.800 | 2198 | 22.9 | 30.6 | 1084 | 2.1 | 72.9 | 1055 | 2.7 | 80.4 |
| rows 30-45% | 0.935 | 31840 | 72.6 | 2.6 | 12031 | 6.2 | 49.7 | 1873 | 4.9 | 74.9 |

Calibration:

| bin | n | mean p | share that stood |
|---|---|---|---|
| (-0.001, 0.1] | 21287.00 | 0.04 | 0.04 |
| (0.1, 0.2] | 8813.00 | 0.14 | 0.14 |
| (0.2, 0.35] | 10173.00 | 0.28 | 0.28 |
| (0.35, 0.5] | 5772.00 | 0.44 | 0.44 |
| (0.5, 0.65] | 7440.00 | 0.57 | 0.57 |
| (0.65, 0.8] | 9304.00 | 0.73 | 0.73 |
| (0.8, 0.9] | 10507.00 | 0.85 | 0.85 |
| (0.9, 1.0] | 37971.00 | 0.96 | 0.96 |

Hand check: 220 sampled, seen: {'P': 138, 'U': 45, 'A': 34, 'X': 3}; with a probability and a clear call: 172; AUC 0.906

| hand | between | p<=0.2 | p>=0.8 |
|---|---|---|---|
| building seen | 52 | 4 | 82 |
| open ground seen | 12 | 19 | 3 |

| group | seen building | seen open | p>=0.8: n | p>=0.8: building % | p<=0.2: n | p<=0.2: open % | buildings found % | open found % |
|---|---|---|---|---|---|---|---|---|
| all | 138 | 34 | 85 | 96 | 23 | 83 | 59 | 56 |
| Bronx | 31 | 3 | 21 | 95 | 1 | 100 | 65 | 33 |
| Brooklyn | 34 | 2 | 19 | 100 | 3 | 33 | 56 | 50 |
| Manhattan | 40 | 0 | 27 | 100 | 1 | 0 | 68 | nan |
| Queens | 27 | 6 | 14 | 100 | 4 | 75 | 52 | 50 |
| Staten Island | 6 | 23 | 4 | 50 | 14 | 100 | 33 | 61 |

| call | n | right % | share of its side found % |
|---|---|---|---|
| p >= 0.95 | 33 | 100 | 24 |
| p >= 0.9 | 56 | 98 | 40 |
| p >= 0.8 | 85 | 96 | 59 |
| p >= 0.7 | 103 | 95 | 71 |
| p >= 0.6 | 116 | 96 | 80 |
| p <= 0.05 | 16 | 100 | 47 |
| p <= 0.1 | 18 | 94 | 50 |
| p <= 0.2 | 23 | 83 | 56 |
| p <= 0.3 | 37 | 68 | 74 |
| p <= 0.4 | 43 | 63 | 79 |

Unclear by eye (45): mean p 0.53

### Recorded years against the photographs

Share of the buildings with a recorded year that the photograph shows standing / on open ground. The first
row of each table is the training side (older than the photograph); the others were not used.

1924:

| recorded year | source | n | p>=0.8 % | p<=0.2 % |
|---|---|---|---|---|
| 1884-1921 | lpc | 12711 | 83.4 | 1.0 |
| 1884-1921 | assessor | 9909 | 71.1 | 4.0 |
| 1927-1932 | lpc | 2182 | 45.6 | 30.8 |
| 1927-1932 | assessor | 13135 | 42.5 | 24.4 |
| 1933-1939 | lpc | 466 | 39.7 | 31.1 |
| 1933-1939 | assessor | 4933 | 27.1 | 44.1 |
| 1940-1954 | lpc | 331 | 46.8 | 21.8 |
| 1940-1954 | assessor | 16867 | 13.1 | 68.5 |
| 1955-2030 | lpc | 519 | 52.6 | 16.0 |
| 1955-2030 | assessor | 156889 | 25.5 | 42.0 |

1951:

| recorded year | source | n | p>=0.8 % | p<=0.2 % |
|---|---|---|---|---|
| 1911-1948 | lpc | 6068 | 63.6 | 4.3 |
| 1911-1948 | assessor | 38093 | 70.0 | 4.4 |
| 1954-1959 | lpc | 164 | 49.4 | 12.8 |
| 1954-1959 | assessor | 6804 | 40.5 | 29.0 |
| 1960-1966 | lpc | 183 | 54.1 | 9.8 |
| 1960-1966 | assessor | 6757 | 51.5 | 17.7 |
| 1967-1981 | lpc | 92 | 56.5 | 5.4 |
| 1967-1981 | assessor | 12609 | 29.2 | 46.0 |
| 1982-2030 | lpc | 119 | 70.6 | 4.2 |
| 1982-2030 | assessor | 132747 | 30.5 | 33.3 |

Read: a building recorded in 1927-32 has a building on its outline in the 1924 photograph in 43-46 % of
cases - also for the Landmarks Commission's researched dates. That is replacement on the same lot (and, for
the assessor, late years), not an error of the photograph.

## How to use it

- **"Stood by 1924"**: `p1924 >= 0.8` - right in 94 % of the hand-checked cases (61 of 65), finds 63 % of the
  buildings. `>= 0.9`: 93 % (41 of 44), finds 42 %.
- **"Not yet built in 1924"**: `p1924 <= 0.2` - right in 92 % (65 of 71), finds 71 % of the open ground;
  `<= 0.1`: 98 % (55 of 56), finds 60 %. **Not where `built_share_50m < 0.15`** (open country, big lots under
  trees) and with care on Staten Island: there a third (Staten Island: a fifth) of the buildings known to be
  older than the photograph get p <= 0.2.
- **"Stood by 1951"**: `p1951 >= 0.7` - right in 95 % (98 of 103), finds 71 %.
- **"Not yet built in 1951"**: `p1951 <= 0.1` - right in 94 % (17 of 18), finds half; `<= 0.2` is right in
  only 83 % (19 of 23). Same warning for open country.
- Between the thresholds (30 % of the footprints in 1924, 41 % in 1951): no call. Do not move a date on it.
- "Stood" means *a* building on the outline. It dates today's building only where replacement is unlikely:
  a placeholder-year house in a district that was being built up (most of Brooklyn south of Prospect Park,
  Queens, the Bronx, Staten Island). In Manhattan and wherever `built_share_50m > 0.45` nearly every outline
  had a building in both photographs (hand check, Manhattan 1924: 37 buildings, 1 open) and "stood" says
  nothing about today's building; "open" stays valid there and is rare.
- A building that stood in 1924 stood in 1951: where `p1924 >= 0.8` and `p1951 <= 0.2` (11,527 footprints, 4 %
  of the "stood 1924" calls) one of the two is wrong, or an earlier building came down in between - no call.
- For a district or a placeholder year rather than a building, count the two calls and read them between
  the borough's own reference groups ("by 1899 / 1901" = all standing, "1955 and later" = none), as
  `data/research/aerial_years.md` does: the share a call finds differs too much between boroughs (Brooklyn
  rows 67 %, Queens houses 38 %, Staten Island 19 %) for one citywide correction.

## Known failures

- **Isolated houses in open country** (fabric below 15 %): hold-out AUC 0.80; only one in five older
  buildings is recognised and one in three is called open. Trees hide small roofs at 2 m.
- **Staten Island**: few buildings to register on (one footprint in seven gets a shift), few older recorded
  buildings to learn from (444 for 1924); 32 % of them recognised, 22 % called open. The hand check has 4
  buildings there for 1924 - none recognised.
- **Trees and gardens beside houses** read as buildings: the hand-checked "open ground" cases with a high p
  in 1924 are mostly tree cover and gardens next to built lots.
- **Dense blocks**: streets between tall buildings lie in shadow; 10 % (1924) and 17-21 % (1951) of the street
  outlines there get p >= 0.8. Thin and L-shaped footprints in Manhattan can get low p although the block is
  built.
- **The white gutters of 1924** are caught only when pure white: where a sheet number is printed on a grey
  patch the footprint keeps a (meaningless, middling) probability - one of 220 in the hand check.
- **Registration** was accepted for a third of the footprints only; elsewhere the outline may sit up to
  about 7 m off the roof, which blurs the per-footprint evidence (the 30 m and 100 m measures do not care).
- The 1951 mosaic is the weaker one: 20 % of the hand sample could not be called by eye (12 % for 1924).
- Small buildings: garages and sheds under about 40 m2 are a few pixels; their p is mostly what surrounds
  them.
- The street outlines used for training in 58 blocks were made with the coverage test as first written
  (before the white gutters were caught): about 2 % of them lie partly on a gutter.

## Reproducing

```
cd pipeline
../.venv/bin/python aerial_presence.py tiles       # 76 min of fetching, 966 MB under data/raw/aerial (cached)
../.venv/bin/python aerial_presence.py features    # 610 block-years, 15-20 s each on the loaded build machine; several runs can share the work
../.venv/bin/python aerial_presence.py synthetic   # street outlines in 58 blocks
../.venv/bin/python aerial_presence.py model       # about 4 min per year
../.venv/bin/python aerial_presence.py predict report
```

Every step skips what exists (`data/interim/aerial/`: `footprints.parquet` is a snapshot of the standing
footprints taken at the first run - delete it, `features/`, `synthetic/`, `cover/`, the models and
`tiles_needed.parquet` to follow a rebuilt `nyc_buildings.parquet`; the tiles need not be fetched again).
`recover` recomputed the coverage after the gutter test was tightened in this run; a fresh `features` run
does not need it. Memory: under 1 GB per process. Not run as part of `make data`.
