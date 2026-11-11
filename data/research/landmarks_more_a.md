# Landmarks, round "more A": High Line, Farley / Moynihan, Brooklyn Tower and the Dime

Code: `viewer/src/landmarks/nyc-more-a.ts` (export `MORE_A`, 16 models). Generators (not part of the build):
`data/interim/landmarks_more_a/hl_build.py`, `hl_gen.py`, `gen2.py` (OpenStreetMap -> embedded local-metre data).
Downloads: `data/raw/landmarks_more_a/` (OpenStreetMap API tiles `osm_*.json`, relation 7141751 `hl_rel.json`; ODbL).
Overpass was unreachable; the OSM map API (api.openstreetmap.org/api/0.6/map, relation/full) worked.

## High Line (10 models)
- Outline: OSM relation 7141751 (the park multipolygon, 28,600 m2) clipped to sections; breadth 8-10 m (platforms to 25 m).
  Centre line: park footways named "High Line" (ways 277885758 ... 1168715452, 1239197095, 350563861), shortest path
  Gansevoort -> 34th St (1,857 m) smoothed over 30 m (spine 2,275 m with the rail-yards loop). Section cuts at the nearest
  point to West 20th (772 m) and West 30th Street (1,585 m).
- Dates (Wikipedia High Line, read 2026-11-11): dedicated 29 June 1934 (first train 1933); St. John's terminal abandoned 1960;
  southernmost section (Bank St down Washington St to Spring St) demolished "in the 1960s" - year not given, 1961 ESTIMATED;
  Bank-Gansevoort 1991; closed 1980 (last train frozen turkeys); park Section 1 8 Jun 2009, Section 2 7 Jun 2011,
  Section 3 21 Sep 2014, Spur 4 Jun 2019, Moynihan Connector 22 Jun 2023. Construction starts (2006.3, 2009.7, 2012.7,
  2017.5, 2022.0) and the 1932.0 start of the viaduct are ESTIMATED (not read from a source).
- Deck level 9 m (the brief; OSM maps 7.5 m top / 5.5 m underside on the relation; the Wikipedia article gives no height) - estimated.
- Estimated: bent spacing 12 m, columns 0.7 m, rails/ballast, planting strips, railings; the southern line (Washington St from OSM,
  width 9.2 m = park median) - no survey found; its start lies 12 m from the surviving spine. St. John's terminal not modelled.
- Spur: OSM way 1185582162 (7 m wide, estimated); Connector: ways 1185582164, 1021481785, 1080012421 (3.6 m, 14 m gap bridged).
- Check: section ring areas 10,937 / 8,248 / 6,825 m2; every model builds without NaN; deck top 9.0 m (+0.8 / +1.1 m rail / railing).
  ~2,400-3,000 triangles per section (heavier than the usual landmark: the outline has many vertices).

## Farley / Moynihan (3 additive models)
- Outline: OSM way 264667030 (421 8th Ave, 58 nodes) = 228.2 x 117.5 m in the avenue grid (frame bearing 29.1 deg); city BIN 1084820
  (1913, roof 31.24 m, 25,889 m2). Roof 31 m (Wikipedia 101 ft; city 31.2 m; model 31.5 m with a 0.5 m parapet).
- Wikipedia (James_A._Farley_Building, Moynihan_Train_Hall): 1911-14 McKim, Mead & White, opened 5 Sep 1914; 355 ft on Eighth Ave,
  332 ft deep; annex 1932-35 (contract Feb 1934, opened Dec 1935); 20 Corinthian columns 53 ft, 31 steps; Moynihan phase 2 from
  ~Aug 2017, opened 1 Jan 2021, skylight 92 ft, 255,000 sq ft. Court (47.4 x 69 m) and bays from OSM parts (464922601-641, 890243248-251).
- The models are additive (1914 / annex / skylights) so nothing sinks and reappears; the 1914 model hides the city footprint.
  Estimated: the 332 ft depth split (u = 13.5 m), step runs, pavilion size, the court roof at 27 m, vault rise, annex pilasters.
- Penn Station (nyc-lost.ts, 7th-8th Ave) and Madison Square Garden (nyc-civic.ts) are not touched.

## Brooklyn Tower and the Dime (3 models)
- Tower: OSM part 1039403183 (hexagon, 33.7 x 32.5 m, "324 m", 93 levels as mapped), city BIN 3000370 (2022, roof 315.47 m).
  Wikipedia 9_DeKalb_Avenue: 1,066 ft (325 m) to the crown (1,035 ft roof; FAA 1,073 ft), 74 floors, SHoP, topped out 28 Oct 2021, opened 2022.
  Model: roof 315.5 m + three crown steps to 325.0 m (check: zmax 325.00). Setbacks (1.1 % per 39 m), crown, colours ESTIMATED.
  NB the Overture/OSM building at -73.9839,40.6904 is not the Dime (it is BIN 3000323); the Dime is at -73.9825,40.6903.
- Dime Savings Bank: OSM part 248156228 (2,401 m2; city 2,417 m2), dome OSM part 700241894 (r 10.3 m), top 33.3 m (check: 33.30).
  1906-08 Mowbray & Uffinger, opened 19 Dec 1908; 1931-32 Halsey, McCormack & Helmer. Which part was the original lot is NOT published:
  split at x = -31 m is ESTIMATED (west 630 m2 = 1908; east 1,770 m2 = 1932, which carries the rotunda dome). Cornice 24 m estimated.

## Not done
Little Island (Pier 55); the St. John's Park terminal building; interior of the Moynihan hall; no on-screen look (no GPU here).
