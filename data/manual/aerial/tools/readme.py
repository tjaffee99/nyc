"""Writes data/manual/aerial/README.md: prose + the tables of data/interim/aerial/report.md."""
import re, sys
sys.path.insert(0, '/home/user/nyc/pipeline')
import aerial_presence as ap
rep = (ap.WORK / 'report.md').read_text()
y24, y51 = rep.split('## 1951')
def sec(txt, start, end):
    a = txt.index(start); b = txt.index(end, a) if end else len(txt)
    return txt[a:b].strip()
def tab(txt, start, end):
    s = sec(txt, start, end)
    return s[s.index('|'):].strip()
cov = {y: tab(t, 'Coverage and registration', 'District hold-out') for y, t in ((1924, y24), (1951, y51))}
hold = {y: sec(t, 'District hold-out', 'Calibration') for y, t in ((1924, y24), (1951, y51))}
cal = {y: tab(t, 'Calibration', 'Hand check:') for y, t in ((1924, y24), (1951, y51))}
hand = {y: sec(t, 'Hand check:', 'Hand check by threshold') for y, t in ((1924, y24), (1951, y51))}
thr = {y: tab(t, 'Hand check by threshold', 'Unclear by eye') for y, t in ((1924, y24), (1951, y51))}
unclear = {y: sec(t, 'Unclear by eye', 'Recorded years against') for y, t in ((1924, y24), (1951, y51))}
recd = {y: tab(t, 'Recorded years against the photograph', 'Placeholder years') for y, t in ((1924, y24), (1951, y51))}
txt = f"""# Aerial presence: did a building stand on each of today's footprints in 1924 and in 1951?

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
  (`https://tiles.arcgis.com/tiles/yG5s3afENB5iO9fj/arcgis/rest/services/Ortho_1924_Mosaic/MapServer/tile/{{z}}/{{y}}/{{x}}`) and
  "NYC Orthos 1951" https://nyc.maps.arcgis.com/home/item.html?id=bca6c3f866f844b490925cc9c26d2e40
  (`.../NYC_Orthos_1951/MapServer/tile/{{z}}/{{y}}/{{x}}`). Standard web-mercator XYZ tiles, no key.
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

{cov[1924]}

1951:

{cov[1951]}

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

{hold[1924]}

Columns: "stood" = footprints recorded before the photograph; "street" and "open" = the two certain
"nothing stood" sets; fabric = share of the ground within 50 m that is building today.

Calibration:

{cal[1924]}

{hand[1924]}

{thr[1924]}

{unclear[1924]}

### 1951

{hold[1951]}

Calibration:

{cal[1951]}

{hand[1951]}

{thr[1951]}

{unclear[1951]}

### Recorded years against the photographs

Share of the buildings with a recorded year that the photograph shows standing / on open ground. The first
row of each table is the training side (older than the photograph); the others were not used.

1924:

{recd[1924]}

1951:

{recd[1951]}

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
"""
(ap.OUT_DIR / 'README.md').write_text(txt)
print(len(txt), 'chars')
