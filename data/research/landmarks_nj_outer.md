# New Jersey outer landmarks (Mercer, Middlesex, Monmouth, Ocean, Morris, Sussex)

Models: `viewer/src/landmarks/nj-outer.ts` (`NJ_OUTER`, 21 entries, 20 buildings/structures + the 1792 State House).
Dates table: `data/tables/known_building_dates.nj_outer.csv` (30 rows).

## Method
- **Plans**: Overture 2026-10-21.0 `outer_building.parquet` (OpenStreetMap-derived, ODbL), read by lon/lat window; the outline is copied into the code in anchor-local metres (anchor = the lon/lat in each model). Bridge deck and the Edison / Barnegat feet come from OpenStreetMap through Nominatim (ways 561300664, 427497491, 704069002; Cleveland Tower node 367681826; ODbL). No building parts exist for these sites.
- **Heights and dates**: article URLs in each model's `sources`, read with WebFetch / WebSearch in this session. Where a source gave no figure it is **estimated** and the model's `Model:` fact says so. Nothing is from the NPS / NRHP PDFs themselves (only reported by search snippets).
- Scratch: `data/interim/landmarks_nj_outer/` (`fp.py` footprint reader, `check.ts` numeric check, `dates.py` builds the CSV).

## Numeric check (`check.ts`, esbuild bundle run in node; plan = union of triangles projected to the ground at 0.5 m; "outside" = plan cells outside the replaced footprint)
| id | built / end | top (m) | cited | plan m2 | footprint m2 | outside m2 |
|---|---|---|---|---|---|---|
| nj_state_house_1792 | 1792-1793 / 1885.2 | 18.5 | block 45.7x15.2 (150x50 ft) | 695 | 694 | - |
| nj_state_house | 1885.2-1889.5 / - | 44.2 | dome 145 ft = 44.2 | 7580 | 7578 | 0 |
| nj_old_barracks | 1758-1759.5 / - | 8.4 | none (OSM 7.7) | 546 | 546 | 0 |
| nj_trenton_battle_monument | 1892-1893.8 / - | 45.72 | 150 ft | 81 | 83 | - |
| nj_lower_trenton_bridge | 1927-1928.9 / - | 11.65 (trusses) | length 312 m | deck 312 m long | OSM way | - |
| nj_trenton_war_memorial | 1930-1932.4 / - | 21 (stage house) | none | 2919 | 2910 | 8 |
| nj_nassau_hall_1756 | 1754-1756.7 / 1855.2 | 24 | none | 885 | (53.6x16.5, recalled) | - |
| nj_nassau_hall | 1855.2-1856.4 / - | 23.6 | none | 1347 | 1324 | 24 |
| nj_princeton_chapel | 1924.5-1928.4 / - | 36.9 | 121 ft = 36.9 | 1800 | 1790 | 11 |
| nj_cleveland_tower | 1911-1913.4 / - | 52.7 | 173 ft = 52.73 | 88 | (9 m square, estimated) | - |
| nj_blair_hall | 1896-1897.8 / - | 26.8 | OSM 26.8 | 1298 | 1289 | 9 |
| nj_princeton_stadium | 1996.8-1998.7 / - | 15.5 | OSM 15.5 | 21816 | 21905 (outer ring) | 55 |
| nj_old_queens | 1809-1825.5 / - | 20.6 | none (OSM 9.6) | 585 | 584 | 0 |
| nj_ford_mansion | 1773-1774.8 / - | 11.8 | none | 304 | 302 | 1 |
| nj_sandy_hook_light | 1763-1764.45 / - | 31.4 | 103 ft = 31.4 | 69 | 68 | 3 |
| nj_twin_lights | 1861-1862.9 / - | 22.25 | 73 ft = 22.25 | 580 | 521 + south tower 44 | 61 (north tower, south tower) |
| nj_barnegat_light | 1857.5-1859 / - | 49.7 | 163 ft = 49.7 | 50 | 49 | 0 |
| nj_lakehurst_hangar_1 | 1919.5-1921.6 / - | 68.3 | 224 ft = 68.3 | 24440 | 24255 | 185 (rectangle fitted) |
| nj_edison_tower | 1937.4-1938.1 / - | 40.67 | 131 ft (118 ft column + 13 ft 8 in bulb) = 40.1 | 117 | OSM circle 48 (7.8 m) + base | - |
| nj_asbury_convention_hall | 1928-1930.6 / - | 20 | none | 8081 | 8068 | 13 |
| nj_high_point_monument | 1928-1930.9 / - | 67.06 | 220 ft = 67.06 | 122 | 122 | 1 |
Vertex counts 84-1,986 (largest: the State House and the bridge). No NaN vertices. `npx tsc --noEmit` passes. Not looked at on screen.

## Per model: what is cited, what is estimated
- **State House**: cited: 1792 start, 150x50 ft first block, 1845 / 1885 / 1889 / 1891 / 1903 / 1906-12 stages, dome 145 ft, gold leaf. Estimated: eave heights (9.5 m first block, 14 m wings), drum and dome profile, 1792 block's position and orientation (under the central pavilion, bearing 110°), completion of the first block (one year). 1845 additions not modelled. Wings drawn whole from 1885.
- **Old Barracks**: cited 1758 (begun 31 May 1758, finished March 1759: NRHP nomination as quoted by a search result), stone, U shape. Estimated: 8.4 m height, flat roof.
- **Battle Monument**: cited 150 ft total, 13 ft statue, dates (cornerstone 26 Dec 1891, capstone 31 Aug 1893, dedication 19 Oct 1893). Estimated: column taper, pedestal stages, statue form. The 83 m2 base is the real outline.
- **Lower Trenton Bridge**: cited 1,022 ft, Pennsylvania (Petit) through truss, opened 30 Nov 1928, "Trenton Makes" sign on the south side. Real: alignment and 10.8 m width (OSM way). Estimated: 6 spans, 7 m truss depth, deck height, sign size/side (drawn on the west-bearing side of the frame; check against the bridge's south side), construction start 1927. The 1806 bridge is not modelled.
- **War Memorial**: cited 1930-32, buff limestone, 1,833-seat theatre. Estimated: all heights (14.5 m cornice, 21 m stage house).
- **Nassau Hall**: cited 1754-56, fires 6 March 1802 and March 1855, Notman's cupola and towers, 32x40 ft prayer hall. The 176x54 ft size of the 1756 hall is **recalled, not re-read**; heights, roofs, cupola and tower sizes are estimated; the 1905 wings are in the 1855+ outline only.
- **Chapel**: cited 277 ft length, 76 ft transepts, 121 ft height, no tower, 1924 / 1925 / 1928 dates. Estimated: aisle wall 19 m, nave width 13.5 m, transept roof.
- **Cleveland Tower**: cited 173 ft (Princeton Graduate College history page), Cram, 1913. Real position (OSM node). Estimated: 9 m square plan, orientation (336.5°, the OGC's east wall), stage proportions, start 1911.
- **Blair Hall**: cited tower 1896 (Princeton Historic District article), OSM tower height 26.8 m. Estimated: 14.5 m eaves, the tower's position along the building and its 9 m plan. Hall/arch dates 1896-97.
- **Princeton Stadium**: cited opened 19 Sept 1998, 27,800 seats, four-sided grandstands; real outer ring and field (Overture). Estimated: seating rake. Palmer Stadium (1914-96; 42,000-45,750 seats, sources differ) not modelled.
- **Old Queens**: cited 1809 cornerstone, 1825 cupola, McComb, Federal. No height cited (OSM 9.6 m): 12 m eaves and a 20.6 m cupola are estimated.
- **Ford Mansion**: cited 1774, Georgian, wood siding, Washington Dec 1779 - June 1780. Estimated: 7.4 m eaves, hipped roof, chimneys, start 1773.
- **Sandy Hook Light**: cited 11 June 1764, octagonal stone, 103 ft, focal height 89 ft. Estimated: taper (9.6 m to 6 m), gallery and lantern.
- **Twin Lights**: cited 1862, north octagonal / south square, 73 ft (USCG; one stock caption says 64 ft), 246 ft above sea. Real: quarters outline and south tower footprint. Estimated: north tower's position and both towers' widths, quarters 8.2 m, start 1861. The 320 ft spacing quoted by a caption does not match the outline (about 60 m) and was not used.
- **Barnegat Light**: cited 163 ft, lit 1 Jan 1859, Meade, 1857 collapse of the 1835 tower. Real foot (8 m, OSM). Estimated: taper, red-over-white colouring (from photographs), lantern.
- **Hangar No. 1**: cited 1921, 966 x 350 x 224 ft (Wikipedia; the NRHP nomination as quoted by a search result says 961 x 350 x 200 ft; another source 960 x 328 x 190). Height 224 ft matches OSM's 68 m. The Overture outline is 235 x 105 m, **shorter than the cited 294 x 110 m**: the plan follows the outline. Arch profile and doors estimated.
- **Edison Tower**: cited 17 May 1937 start, dedicated 11 Feb 1938, 131 ft, bulb 13 ft 8 in Pyrex, concrete, Massena & DuPont (a stock-photo source says 129 ft and another 118 ft column: the sum is used). Foot from OSM; the octagonal section and taper estimated.
- **Asbury Park Convention Hall**: cited 1928-30 (the infobox says "opened 1925": conflicting), Warren & Wetmore, 215 ft over the beach, steel-encased concrete piles, Paramount Theatre joined by an arcade. Estimated: all heights.
- **High Point Monument**: cited 220 ft granite and quartz obelisk, 1928-30, 291 steps, Kuser. Estimated: base stages, taper 6.2 to 3.2 m.

## Dates table
30 rows: 11 Princeton (Princeton Historic District article's building list), 10 Rutgers Queens / College Avenue campus (article "Queens Campus, Rutgers University" and "College Avenue Campus"), 9 Trenton (State House, Old Barracks, Kelsey, War Memorial, City Hall and Free Public Library from the Trenton chronology, Friends Meeting House, Trent House). The point is each Overture footprint's representative point (inside the outline). "Estimated" in the note where the source gives a range or the footprint's identity is assumed.

## Not done
- Models: Fine Hall tower (its place in the OSM outline could not be fixed), Palmer Stadium, Trenton's old bridge of 1806, the 1845 State House, Princeton's Palmer / Firestone. Princeton Fine Hall tower: about 170 ft, dedicated 17 March 1970 (Princetoniana Museum snippet), unverified.
- Dates: Masonic temples (no named footprint), Trenton's courthouse (sources conflict: 1839 / cornerstone 1902), First Presbyterian (rebuilt dates conflict), the Princeton halls whose years came only from memory. Tower of Blair not dated separately.
- A web result for the Lakehurst hangar contained text addressed to an AI; it was ignored.
- Nothing seen on screen; no raw downloads kept (the URLs above are the record).
