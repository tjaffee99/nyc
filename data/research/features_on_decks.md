# Park and sports features that sit on a roof or a pier deck and are lost on the map

Part of the "outer round" landmarks work (agent `landmarks_more_c`, 2026-11-11). Triggered by the owner's complaint that
Riverbank State Park lacks its running track and other features. Nothing in `ground_detail.py` or the viewer was edited.

## How a feature is drawn, and where it is lost

1. `pipeline/ground_detail.py` takes OpenStreetMap land-use polygons (Overture `base_land_use.parquet`: `pitch`, `track`,
   `playground`, `dog_park`, `recreation_ground`, `grass`, `garden`, `pedestrian`, ...) and dates them (park year, buildings around,
   ...). The date rules never look at what stands *on* the outline.
2. `main()` calls `write_outlines(path, polys, kinds, years, ends, ground)`; there every vertex gets
   `z = ground(lon, lat) + z_extra` with `z_extra = 0.3` and `ground = nyc_buildings.Ground()`, **the terrain elevation** (the
   file header says "z = ground + 0.3 m"). Nothing reads the height of a building or pier underneath.
3. `viewer/src/layers/ground-detail.ts` draws the file with `DrapeExtension` and `DRAPE_PARAMETERS` (`depthWriteEnabled: false`,
   `depthCompare: 'less-equal'`). The comment in `viewer/src/layers/drape-extension.ts` states it: "buildings, trees and roads drawn
   after it still cover it exactly". So a feature 0.3 m above the terrain is hidden by any extrusion above it.
4. The building layers extrude `base .. base + height` (columns `base`, `height` of `data/interim/nyc_buildings.parquet`).
   Examples: the plant under Riverbank State Park (BIN 1084789) has `base` 3.54 and `height` 26.92, a roof at 30.5 m, while the
   park's track, field and courts are at about 3.0 m; Pier 40 has a shed (BIN 1012249, `height` 14.87, `base` -0.1, roof 14.8 m) and
   a pier deck row (`year_src` = `pier`, `base` -1.0, `height` 3.5, top 2.5 m) while its fields are at about 0.3 m;
   Brooklyn Bridge Park's Pier 5 and Pier 2 have decks of the same kind, 2.5 m above the water.
   Pier rows come in pairs in the building file: the deck (3.5 m, until 9999) and a "shed" row (`...:shed`, base 2.5, height 7.5,
   removed in 2009 at Brooklyn Bridge Park).

Nothing is dropped by the stage: the features are in `viewer/public/data/ground-detail.bin.gz` / `region-ground-detail.bin.gz` and
are simply under the extrusions. (Two other side effects, not losses: the pier-deck features of Brooklyn Bridge Park carry the
stage's `boro` 061, Manhattan, and so ship in the start-up file; the plant's footprint is dated 1945 by the "neighbours" rule while the
plant dates from 1978-1986, so for 33 years a grey slab stands in the Hudson there.)

## What was measured

`data/interim/landmarks_more_c/cover.py` joins `data/interim/ground_detail/features.parquet` (city features, the classes above; the
file has no geometry, only the centroid `lon`/`lat` and `area_m2`) with `data/interim/nyc_buildings.parquet` rows that stand or are piers:
a feature counts as covered when its **centroid lies inside** a building / pier polygon and the two lifespans overlap
(`bstart < fend and bend > fstart`). Results are in `cover.csv`, `cover_sports2.csv` (one row per feature) there.

- Sports features (pitch, track, playground, dog park, recreation ground): of 8,499 in the five boroughs, **261 (270,766 m2) have
  their centroid under a standing building or pier deck; 36 of them (86,667 m2) are on pier decks**.
- Greens and plazas (grass, garden, flowerbed, pedestrian, plaza): 128 + 28 grass, 70 + 56 garden, 48 + 29 pedestrian (non-pier + pier)
  ... counted the same way, mostly small pieces next to buildings.
- The centroid test is crude: a feature beside a building whose centroid happens to fall in the building's footprint counts, a big
  feature half covered does not. Reading the list by hand: pier decks and the big roofs below are real; many small ones in the
  long list are borderline. `nearest park label` is the nearest label in `park-labels.json`, not necessarily the feature's park.
  **Not checked on screen** (no GPU here), only numerically.

## A. Pier decks (the pier row is a 3.5 m slab, top 2.5 m above the water; "highest part" is the tallest overlapping row)

| pier row | nearest park label | borough | features | m2 | kinds | highest part (m) | lon, lat |
|---|---|---|---|---|---|---|---|
| Pier 40 | James J Walker Park | Manhattan | 4 | 19596 | pitch | 13.1 | -74.0122, 40.7291 |
| Pier 3 (Brooklyn Bridge Park) | Brooklyn Heights Promenade | Manhattan | 1 | 18984 | recreation_ground | 3.5 | -73.9998, 40.6979 |
| Pier 5 (Brooklyn Bridge Park) | Brooklyn Bridge Park | Manhattan | 3 | 13556 | pitch | 3.5 | -74.0017, 40.6949 |
| Pier 2 (Brooklyn Bridge Park) | Fort Stirling Park | Manhattan | 9 | 8197 | pitch | 10.1 | -73.9987, 40.6996 |
| (unnamed footprint) | Frank Golden Park | Queens | 1 | 6622 | pitch | 3.5 | -73.8352, 40.7848 |
| Pier 1 | The Quarantine | Staten Island | 1 | 4590 | recreation_ground | 3.5 | -74.0710, 40.6411 |
| Pier 25 | Washington Market Park | Manhattan | 3 | 4202 | pitch, playground | 3.5 | -74.0145, 40.7203 |
| Fishing Pier | Franklin D. Roosevelt Boardwalk and Beach | Staten Island | 1 | 2484 | recreation_ground | 3.5 | -74.0745, 40.5789 |
| Pier 97 | De Witt Clinton Park | Manhattan | 2 | 1681 | pitch, playground | 7.5 | -73.9952, 40.7720 |
| Pier 6 (Brooklyn Bridge Park) | Brooklyn Bridge Park | Manhattan | 4 | 1542 | pitch, recreation_ground | 3.5 | -74.0017, 40.6932 |
| Pier 62 (Chelsea Piers) | Hudson River Park | Manhattan | 1 | 1503 | pitch | 7.5 | -74.0094, 40.7487 |
| Pier 46 | Bleecker Playground | Manhattan | 1 | 1193 | recreation_ground | 3.5 | -74.0114, 40.7342 |
| Pier 51 | Gansevoort Market | Manhattan | 1 | 783 | playground | 3.5 | -74.0108, 40.7382 |
| Pier 26 | Washington Market Park | Manhattan | 1 | 712 | pitch | 3.5 | -74.0145, 40.7212 |
| Pier 2 (Brooklyn Bridge Park) | Brooklyn Heights Promenade | Manhattan | 1 | 586 | playground | 10.1 | -73.9997, 40.6995 |
| (unnamed footprint) | Von Briesen Park | Staten Island | 1 | 316 | recreation_ground | 3.5 | -74.0551, 40.6066 |
| Canarsie Pier | Bayview Playground | Brooklyn | 1 | 120 | playground | 3.5 | -73.8835, 40.6289 |

Reading: **Pier 40** (Hudson River Park, W Houston St): the 1998 roof fields (OSM ways 65223814 soccer, 576166509) sit on the shed roof at
14.8 m; the 2005 main field (way 23529474, 5,323 m2) lies in the shed's courtyard (the city's footprint BIN 1012249 has a 14,300 m2 hole), at pier-deck level, open to the sky. (The first run of the cover count above tests centroids against outlines, holes included.) **Brooklyn Bridge Park**: Pier 5
(three turf fields, opened Dec 2012), Pier 2 (basketball, handball, pickleball, roller rink, play turf, opened May 2014), Pier 3
(lawn and greenway terrace, Nov 2013), Pier 6 (volleyball courts, playgrounds, 2010), Pier 1's uplands are not decks. **Hudson River
Park**: Pier 25 (volleyball, mini-golf, playground), Pier 26, Pier 46, Pier 51 (playground), Pier 62 (Chelsea Piers roof), Pier 97 (De Witt
Clinton Park). **Elsewhere**: Pier 1 at the Quarantine (Staten Island), the Fishing Pier at the FDR Boardwalk, a pier row at Frank Golden
Park (Queens, Flushing Bay). A feature on a vanished pier row is only counted while both stand.

## B. Roofs and other covers, non-pier, largest first (feature >= 350 m2 and the covering footprint at least 1.3 times its area, roof >= 4 m)

| park (nearest label) | borough | feature | m2 | what covers it | class | roof (m, city measure) | covering footprint m2 | lon, lat |
|---|---|---|---|---|---|---|---|---|
| Riverbank State Park | Manhattan | pitch | 6294 | footprint BIN 1084789 | U0 | 21.2 | 108806 | -73.9570, 40.8249 |
| Macombs Dam Park | Bronx | pitch | 6027 | footprint BIN 2130575 | G1 | 4.9 | 30086 | -73.9290, 40.8280 |
| Riverbank State Park | Manhattan | pitch | 5812 | footprint BIN 1084789 | U0 | 21.2 | 108806 | -73.9587, 40.8240 |
| Terrace Playground | Staten Island | pitch | 5536 | footprint BIN 5106896 | W6 | 8.1 | 14244 | -74.0949, 40.6175 |
| Risse Street Park | Bronx | playground | 4995 | footprint BIN 2118047 | U7 | 14.3 | 28264 | -73.8878, 40.8790 |
| Macombs Dam Park | Bronx | track | 4343 | footprint BIN 2130575 | G1 | 4.9 | 30086 | -73.9283, 40.8280 |
| Riverbank State Park | Manhattan | track | 3950 | footprint BIN 1084789 | U0 | 21.2 | 108806 | -73.9566, 40.8249 |
| Terrace Playground | Staten Island | track | 3120 | footprint BIN 5106896 | W6 | 8.1 | 14244 | -74.0953, 40.6175 |
| House of Refuge | Manhattan | recreation_ground | 3008 | Randall's Island Tennis Center | Q1 | 12.5 | 18925 | -73.9184, 40.7928 |
| House of Refuge | Manhattan | recreation_ground | 2966 | Randall's Island Tennis Center | Q1 | 12.5 | 18925 | -73.9186, 40.7925 |
| Washington Park | Brooklyn | recreation_ground | 1787 | footprint BIN 3428630 | G1 | 6.1 | 2703 | -73.9784, 40.6915 |
| Damrosch Park | Manhattan | track | 1218 | footprint BIN 1027085 | W9 | 32.0 | 5475 | -73.9888, 40.7705 |
| Gantry Plaza State Park | Queens | recreation_ground | 1198 | footprint BIN 4541713 | D7 | 119.8 | 7300 | -73.9553, 40.7477 |
| Jardin De La Familia | Bronx | pitch | 1079 | footprint BIN 2009463 | W1 | 27.7 | 4089 | -73.9052, 40.8358 |
| Dutch Kills Playground | Queens | dog_park | 991 | footprint BIN 4623388 | RX | 22.9 | 2531 | -73.9321, 40.7548 |
| Macombs Dam Park | Bronx | pitch | 859 | footprint BIN 2130575 | G1 | 4.9 | 30086 | -73.9304, 40.8274 |
| Corona Yard | Queens | pitch | 822 | Louis Armstrong Stadium | Q1 | 12.5 | 10022 | -73.8454, 40.7510 |
| Riverbank State Park | Manhattan | pitch | 785 | footprint BIN 1084789 | U0 | 21.2 | 108806 | -73.9581, 40.8232 |
| Annadale Playground | Queens | track | 773 | footprint BIN 4442846 | W1 | 14.9 | 4641 | -73.8524, 40.7325 |
| Asphalt Green | Manhattan | pitch | 764 | footprint BIN 1050634 | D4 | 92.7 | 1773 | -73.9463, 40.7784 |
| Terrace Playground | Staten Island | pitch | 689 | footprint BIN 5106896 | W6 | 8.1 | 14244 | -74.0947, 40.6181 |
| Colucci Playground | Bronx | pitch | 682 | footprint BIN 2102976 | W9 | 4.3 | 3399 | -73.8439, 40.8530 |
| Vietnam Veterans Plaza | Manhattan | recreation_ground | 636 | footprint BIN 1083346 | RB | 10.0 | 6410 | -74.0085, 40.7034 |
| Asser Levy Playground | Manhattan | track | 606 | footprint BIN 1022557 | W8 | 21.9 | 6083 | -73.9730, 40.7363 |
| University Place | Brooklyn | pitch | 597 | footprint BIN 3394444 | W6 | 18.0 | 2641 | -73.9792, 40.6906 |
| Bowne Playground | Queens | playground | 591 | footprint BIN 4114657 | W1 | 18.0 | 5306 | -73.8240, 40.7584 |
| Andrews Grove | Queens | pitch | 560 | footprint BIN 4000019 | D4 | 16.7 | 5708 | -73.9565, 40.7443 |
| James A. Bland Playground | Queens | pitch | 556 | footprint BIN 4540380 | RC | 56.6 | 19940 | -73.8367, 40.7574 |
| James A. Bland Playground | Queens | pitch | 548 | footprint BIN 4540380 | RC | 56.6 | 19940 | -73.8365, 40.7575 |
| Damrosch Park | Manhattan | pitch | 506 | footprint BIN 1027085 | W9 | 32.0 | 5475 | -73.9888, 40.7705 |
| 60th Street Yard | Manhattan | playground | 495 | footprint BIN 1089703 | W1 | 50.3 | 2649 | -73.9908, 40.7739 |
| Riverbank State Park | Manhattan | playground | 485 | footprint BIN 1084789 | U0 | 21.2 | 108806 | -73.9577, 40.8259 |
| 60th Street Yard | Manhattan | pitch | 478 | footprint BIN 1089703 | W1 | 50.3 | 2649 | -73.9906, 40.7738 |
| Horace Harding Playground | Queens | playground | 451 | footprint BIN 4072145 | D4 | 21.3 | 2109 | -73.8595, 40.7283 |
| Loreto Playground | Bronx | pitch | 437 | footprint BIN 2102976 | W9 | 4.3 | 3399 | -73.8444, 40.8530 |
| Riverbank State Park | Manhattan | pitch | 400 | footprint BIN 1090423 | U0 | 21.2 | 108806 | -73.9574, 40.8236 |
| Riverbank State Park | Manhattan | pitch | 400 | footprint BIN 1090423 | U0 | 21.2 | 108806 | -73.9576, 40.8237 |
| Macombs Dam Park | Bronx | pitch | 391 | footprint BIN 2130575 | G1 | 4.9 | 30086 | -73.9299, 40.8282 |
| Macombs Dam Park | Bronx | pitch | 380 | footprint BIN 2130575 | G1 | 4.9 | 30086 | -73.9298, 40.8270 |
| Macombs Dam Park | Bronx | pitch | 380 | footprint BIN 2130575 | G1 | 4.9 | 30086 | -73.9300, 40.8284 |

Reading: **Riverbank State Park** (the plant, BIN 1084789; handled by landmark models `riverbank_state_park` / `north_river_plant_1986`:
2 pitches, the track, 11 more pieces, 20,177 m2 in all); **Macombs Dam Park** (track and field under a 4.9 m garage footprint of 30,000 m2,
BIN class G1, built 2010: the garage roof is a plausible deck but not verified); **Isham Park** (Q6 buildings 6-18 m: field houses or
domes, not verified); **Randall's Island Tennis Center** (air-supported dome: the courts are legitimately inside, 12.5 m);
**Terrace Playground, Staten Island** (a 14,000 m2 W6 building of 8 m; roof field not verified); **Asphalt Green / Gantry Plaza /
Julio Carballo Fields / University Place** (tall buildings 27-126 m: the feature is beside or on a podium; if drawn on top it would float
on a tower, hence the height cap in the proposed change). Stadium fields under their own roofs (Louis Armstrong Stadium) are correct to hide.
Others (Hudson River Park's Chelsea Piers rooftop, school roof playgrounds) appear as small rows in the long list.

## The smallest change that draws them on the deck

In `pipeline/ground_detail.py`, `main()`, after the pieces `polys` are cut and before `write_outlines`:

1. Load the standing/pier rows of `nyc_buildings.parquet` (`geometry`, `base`, `height`, `start_year`, `end_year`, `year_src`); build an STRtree.
2. For each piece find the building with the largest overlap of the piece's outline (share >= 0.6 of the piece's area inside it) whose
   lifespan covers the piece's whole life `[pyear, min(end, 2027)]` (otherwise the feature would float after the deck is gone), and which is a
   deck: `year_src == 'pier'`, or footprint area >= 1.3 x the piece area with `height - base` between 2 and 40 m (no towers).
3. Set a per-piece floor `deck_z = base + height` (for a pier the deck row's top, 2.5 m; Pier 40 and the Riverbank plant their shed / plant
   rows, 14.8 m and 30.5 m) and pass it to `write_outlines` (same `order` permutation as `kinds`): `z = np.maximum(ground(lon, lat), deck_z) + z_extra`
   for that piece's vertices (inner points too: `ground` must not be sampled lower than the deck). With `SEG_M = 25` the flat polygon needs no
   other change; no viewer change is needed (the layer is draped and does not write depth, so the 0.3 m above the roof beats the extrusion,
   and a taller part of the same footprint would still hide it, which is why towers are excluded).
4. Re-date: a piece on a deck never starts before the deck (`pyear = max(pyear, start_year + 0.5)` of the covering row; for the Riverbank
   plant the row must also be re-dated to 1986: see the next section).

For Riverbank State Park specifically the roof of the plant in the building file is 30.5 m (a 26.9 m height from base 3.5) while the cited deck is 21 m
above the river; the landmark model fixes the park without the stage change, but the 14 features would still be under the extrusion of
the footprint of 1945-1986 and under the 30.5 m roof for the years when the landmark's `replaces` has not yet hidden it.

## Also found

- `data/interim/nyc_buildings.parquet` BIN 1084789 (the North River plant) is dated 1945.07 (`neighbours`) and BIN 1090426 (the pool building) is dated 1969.3 (`neighbours`), the other deck buildings (BINs 1090423-1090431) likewise by neighbours: the plant was built 1978-1991 (foundation 1978, works 1986-1991) and the park buildings
  opened with the park in 1993. Suggested rows for `known_building_dates`: 1084789 -> 1978 (estimated end of foundation) / 1986, 1090423-1090431 -> 1993.
  The landmark models hide the generic footprints from 1978 on (`replaces`), not before.

## The change, written (not applied): `data/interim/landmarks_more_c/ground_detail_deck.py` / `.patch`

`diff -u pipeline/ground_detail.py data/interim/landmarks_more_c/ground_detail_deck.py` = `ground_detail_deck.patch` (115 lines, 84 added). It adds
`deck_floor()` (STRtree of standing and pier rows of `nyc_buildings.parquet`; rules as above: pier row, or roof deck = footprint >= 1.3 x the piece and
extrusion `height` 2-40 m; covers >= 60 % of the piece; start_year <= piece start + 0.5 and end_year >= piece end; the highest top wins), the
`floor=` argument of `write_outlines` (`z = fmax(ground, floor) + 0.3`, NaN = none), and one call in `main()` after `Ground()`; the piece starts
no earlier than its deck + 0.5. The four landmark decks (`LANDMARK_DECKS`: rings of the Riverbank plant, Pier 40, Pier 5, Pier 2 from `nyc-more-c.ts`) are skipped
(`exclude_landmarks`), so nothing is drawn twice; a new landmark deck means a new ring there. Test: `data/interim/landmarks_more_c/test_deck.py`.

Roof height it takes: `base + height` of the building file as the viewer extrudes it (`nyc_buildings.py`: base = lowest ground corner - 1 m, height = measured
roof + (mean ground - lowest ground) + 1 m, i.e. roof = mean ground along the outline + measured roof). For the Riverbank plant: base 3.54 + 26.92 = 30.46 m,
because the ring's mean ground is 9.25 m (the outline runs up the bluff to Riverside Drive) and the measured roof is 21.21 m; the terrain grid under the
deck itself reads 19.0-19.7 m, i.e. the true deck is at about 19-21 m, so the drawn plant stands about 10 m too high. Features there come out at 30.76 m, as the
extrusion; the landmark model replaces it, and the plant's `height` should be fixed in `nyc_buildings.py` (use the median ground, not the mean) if other
stations on slopes show the same.

Test results (vertex z incl. +0.3): Riverbank track and pitch 30.76 (without the exclusion); Pier 5 field 2.80; Pier 25 pitch 2.80; Pier 40 courtyard field 2.80 and its
two roof fields 15.07; Pier 2 court 11.26 (it lies under an 8,853 m2, 10 m roof structure, OSM 328275185: a canopy, so raising it is wrong; the exclusion list
covers it, but other canopies could be hit); Central Park's Heckscher ball field unchanged (18.15-18.79); Gantry Plaza (119.8 m), Asphalt Green (92.7 m),
University Place (126 m), Isham Park, Macombs Dam Park (garage of 2010 vs a field of 1903: its lifespan does not span the piece's): no floor, unchanged. With the exclusion
on, the Riverbank, Pier 5, Pier 40 and Pier 2 pieces stay at the terrain (1.2-2.8; 19.3-19.97 at Riverbank).
Limits: a building that stands only part of the piece's life (garage built over an older field) is not a deck (the field is hidden after it); canopies are
indistinguishable from roofs; not run end-to-end (the stage was not run: only the function on real outlines).
