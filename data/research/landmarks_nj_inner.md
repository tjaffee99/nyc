# New Jersey inner counties: landmarks — research notes and numeric checks

Models: `viewer/src/landmarks/nj-inner.ts` (`NJ_INNER`, 11 entries). Scratch: `data/interim/landmarks_nj_inner/` (`fp.py` footprints near a point, `ring2.py` ring in a model frame, `dump.ts` + the check below).

## Method

- **Plan, anchor, orientation**: footprints of `data/interim/county_buildings.parquet` (Overture / state footprints; ODbL, (c) OpenStreetMap contributors where they come from there), vertex mean as frame origin, frame +y at the footprint's minimum-rotated-rectangle bearing (cathedral, Penn, National Newark, City Hall, CRRNJ, Hoboken, 30 Hudson, Loew's, MetLife, Union County). Rings simplified to 0.4 m (1.5 m for MetLife).
- **Cited dimensions**: Wikipedia article text read in this session (facts only; CC BY-SA 4.0), URL in each model's `sources`. No other source was opened. Overpass (OpenStreetMap) was unreachable from this machine, so no way ids exist.
- **The footprint files' heights are not used** (most are the 9.0 m default or a neighbour imputation); 30 Hudson's 140 m is wrong (238 m cited).
- Footprint `start_year`s in the county file are assessor or imputed years, not the landmarks' years (the MetLife footprint says 1990).

## Check (mesh built with the kit, plan = union of all triangles projected to the ground, against the ring it replaces)

| id | faces | top (m) | cited / target top | plan area (m2) | ring (m2) | ratio | centroid offset (m) |
|---|---|---|---|---|---|---|---|
| newark_cathedral_basilica | 153 | 71.0 | 71 (232 ft) | 5067 | 4830 | 1.05 | 0.9 |
| newark_penn_station | 84 | 29.0 | none cited | 27729 | 27308 | 1.02 | 1.9 |
| national_newark_building | 126 | 142.0 | 142 (466 ft) | 3347 | 3333 | 1.00 | 0.1 |
| newark_city_hall | 319 | 52.0 | none cited | 3396 | 3366 | 1.01 | 0.2 |
| crrnj_terminal | 42 | 27.0 | none cited | 4757 | 4740 | 1.00 | 0.1 |
| hoboken_terminal | 131 | 68.6 | 68.6 (225 ft) | 33941 | 33929 | 1.00 | 0.0 |
| thirty_hudson_street | 120 | 238.0 | 238 (781 ft) | 5663 | 5660 | 1.00 | 0.0 |
| loews_jersey_theatre | 41 | 27.7 | none cited | 2370 | 2345 | 1.01 | 0.3 |
| metlife_stadium | 220 | 48.0 | none cited | 54557 | 54228 | 1.01 | 0.0 |
| giants_stadium | 158 | 54.0 | 54 (south tower) | 39137 | 38695 | 1.01 | 0.1 |
| union_county_courthouse | 112 | 72.54 | 72.54 (238 ft) | 4024 | 4019 | 1.00 | 0.0 |

Tops are exact for every cited height. The cathedral's 5 % excess is the nave roof and towers reaching past the simplified ring. `npx tsc --noEmit` passes.

## Estimated / unverified, per model

- **Cathedral**: wall 24 m, ridges (+10 m nave, +12 m transept), tower plan (8.6 m) and position on the façade end. The façade end (+y, narrow end) is inferred from the footprint (chevet-like chapels at the other end), not verified; the footprint is about 150 m long and its nave narrower than the cited 111 x 50 m, so the plan follows the footprint, not the cited size.
- **Newark Penn**: no height cited; 9 / 22 / 29 m are estimates.
- **National Newark**: roof 142 m cited; set-back sizes and heights estimated. Wikipedia's infobox says 1933, text and category 1931; `built` ends 1931.5. 1180 Raymond Boulevard was not built (nothing cited, no footprint identified).
- **City Hall**: Wikipedia says only "built 1902"; completion 1906 not verified. Five storeys cited; 27 m eaves, dome estimated.
- **CRRNJ**: no heights cited; train shed (12 platforms, 20 tracks, no size cited) not modelled; start 1888 estimated.
- **Hoboken**: tower 225 ft cited; head house (footprint clipped at y < -150), 24 m and 11 m heights, tower plan and position (middle of the Hudson Place front) estimated. The tower stood 1907-1942, was replaced by a radio tower and a replica in 2006; the model shows it throughout.
- **30 Hudson**: 238 m cited; two set-backs estimated.
- **Loew's Jersey**: opening cited; no height cited (27.7 m is the dataset's value); the fly tower split is an estimate.
- **MetLife**: outline from the footprint; rim height 46 m, rake and field level estimated (no height in the article); pylons 54 ft cited.
- **Giants Stadium**: outline built from the cited 230 x 180 m, position from Wikipedia's coordinates (+-30 m), orientation assumed parallel to MetLife. Footprint file holds no Giants Stadium (site is empty). Bowl 44 m and tower 54 m cited.
- **Union County Courthouse**: tower 72.54 m cited; which wing carries it is unknown (placed on the cross plan's central block); base 15 m estimated.

## Not built

Prudential headquarters (no form sourced), 1180 Raymond Boulevard, the Colgate Clock and Paterson Great Falls mills (no footprint/dimensions read), Paterson City Hall (footprint found at -74.17198, 40.91705, 47.6 x 24.7 m, but no height or tower figure in the article), Bergen County Courthouse (Wikipedia URL 404, no data), Pulaski Skyway and Newark Bay Bridge (not attempted: needs the real line of the road, budget).
