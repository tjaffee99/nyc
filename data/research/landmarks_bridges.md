# Bridges as landmark models — dimensions, sources, estimates

Models: `viewer/src/landmarks/nyc-bridges.ts` (`BRIDGES`, 33 models of 24 bridges).
Table: `data/tables/landmarks_bridges.csv`. Researched 2026-11-10.

## Method

- **Frame.** Every bridge is modelled from z = 0 = sea level (heights "above mean high water"
  are used as heights above z = 0) in a frame whose origin (the landmark's `anchor`) is the middle
  of the main span and whose +y axis runs from one tower / main pier to the other.
- **Tower and pier positions** are the centroids of OpenStreetMap outlines tagged
  `bridge:support=*` (way ids are given per bridge), read on 2026-11-10 from the OSM API
  (`https://api.openstreetmap.org/api/0.6/map?bbox=…`, 22 small boxes kept in
  `data/raw/landmarks_bridges/osm_*.osm`). © OpenStreetMap contributors, ODbL 1.0.
  Overpass (`overpass-api.de` and three mirrors) could not be reached through the session's
  proxy (connection reset / timeouts), so the plain map API was used instead.
- **Check against the cited span.** Where the OSM tower-to-tower distance is within 1 % of the
  cited main span, the OSM positions are used as they are. Where it is not (Manhattan Bridge,
  Hell Gate, High Bridge, Bayonne, Triborough lift span, Broadway Bridge, Pulaski, Henry Hudson),
  the towers / bearings are set the *cited* distance apart about the OSM midpoint on the OSM
  bearing, and the difference is stated below.
- **Centre lines and ends.** Approaches follow the bridge-flagged (`is_bridge`) parts of the
  Overture 2026-10-21.0 road / rail segments (`roads_region.parquet`, `rail.parquet`; ODbL, from
  OpenStreetMap), straight in the frame where they are straight and as polylines (simplified to
  1–1.5 m) where they curve. Water crossings (Bronx Kill, Newtown Creek) are from Overture
  `base_water.parquet`.
- **Heights at the ends** are the viewer's terrain grid (`data/interim/grid_detail_elev.npy`,
  same bilinear lookup as `elevationAt`), so a deck lands on the drawn terrain, except where a
  road goes on elevated beyond the named bridge (stated per bridge).
- **Dimensions** are from the Wikipedia article of each bridge (wikitext read through
  `index.php?action=raw`, cached in `data/raw/landmarks_bridges/wiki/`; CC BY-SA 4.0, facts cited
  with the article URL) and, for four bridges, the NYC DOT fact pages
  (`https://www.nyc.gov/html/dot/html/infrastructure/<name>.shtml`).
- **Not reachable / not used:** Library of Congress HAER pages (403 to scripted requests), MTA
  Bridges & Tunnels pages (403), Port Authority fact pages (script-rendered, no text), the NYC DOT
  pages of the Harlem River bridges (404). No value below comes from them. The one value recalled
  from a Port Authority page without re-reading it (the George Washington Bridge's 610 / 650 ft
  side spans) is marked.
- **Numeric check** (`data/interim/landmarks_bridges/check.mjs`, run on the built meshes):
  tower-to-tower distance vs cited span, highest vertex vs cited height, lowest steel at
  mid-span vs cited clearance, model ends vs the real ends. Results are in the last section.
- Conventions in the tables: **cited** = read in the named source; **OSM** / **Overture** =
  measured from that data; **estimated** = my assumption, also named in the model's "Model" fact.

Colours, member thicknesses (cables and wires are drawn thicker than life so they read), the
number of truss panels, suspenders and stays drawn, and pier / bent spacing on the approaches
are modelling choices, not data. Designer names and "longest when built" statements in the popup
facts were checked against the cached Wikipedia text.

---

## 1. Brooklyn Bridge — `brooklyn_bridge`

Sources: https://en.wikipedia.org/wiki/Brooklyn_Bridge ; https://www.nyc.gov/html/dot/html/infrastructure/brooklyn-bridge.shtml

| Dimension | Value | Source |
|---|---|---|
| Main span | 1,595.5 ft (486.3 m) | Wikipedia; NYC DOT |
| Side spans | 930 ft | Wikipedia |
| Deck width | 85 ft | Wikipedia |
| Tower height | 278.25 ft above mean high water (NYC DOT page gives no height) | Wikipedia |
| Tower plan at high-water line | 140 × 59 ft | Wikipedia |
| Arch openings | 117 ft tall, 33.75 ft wide, floors 119.25 ft above mean water | Wikipedia |
| Clearance at mid-span | 127 ft above mean high water (Wikipedia infobox); 135 ft (NYC DOT) — 127 ft used | Wikipedia / NYC DOT |
| Main cables | four, 15.75 in | Wikipedia |
| Diagonal stays | about 400, 138–449 ft long | Wikipedia |
| Promenade | 18 ft above the roadways | Wikipedia |
| Anchorages | 129 × 119 ft at the base, 117 × 104 ft at the top | Wikipedia |
| Construction | began Jan 2, 1870; opened May 24, 1883 | Wikipedia |
| Tower positions | ways 1255363983 (Manhattan), 317352708 (Brooklyn): 485.1 m apart, bearing 136.2° | OSM |
| Suspended deck ends | 527 / 524 m from mid-span (way 375157262) — cited 242.5 + 283.5 = 526 m | OSM |
| Model ends | 947 m (Manhattan) and 811 m (Brooklyn) from mid-span, ground 9.1 m and 20.0 m | Overture `Brooklyn Bridge`; terrain grid |

Estimated: tower plan at the top (41.5 × 16.2 m; OSM outline 42.8 × 16.6 m); the arch as an
equilateral pointed arch; cable planes (±13.4 and ±2.6 m); saddles 2.5 m below the tower top;
cable low point just above the promenade; floor depth 1.8 m; floor heights between the cited
tower floor (119.25 ft) and mid-span (127 ft + floor), 3.25 % side-span grade; stiffening trusses
drawn to promenade height; anchorage height (deck level); approaches as arcades of piers.
Stays and suspenders are thinned out (8 stays per fan, a suspender every 11 m).

## 2. Manhattan Bridge — `manhattan_bridge`

Sources: https://en.wikipedia.org/wiki/Manhattan_Bridge ; https://www.nyc.gov/html/dot/html/infrastructure/manhattan-bridge.shtml

| Dimension | Value | Source |
|---|---|---|
| Main span | 1,470 ft (448.1 m) (Wikipedia text and NYC DOT; the Wikipedia infobox says 1,480 ft) | NYC DOT; Wikipedia |
| Side spans | 725 ft | Wikipedia |
| Deck width | 120 ft; lower roadway 34–35 ft | Wikipedia |
| Towers | 336 ft (infobox; the article text also says "350 feet") — 336 ft used | Wikipedia |
| Clearance | 135 ft | Wikipedia |
| Stiffening trusses | four, 24 or 26 ft deep, flanking the tracks — 24 ft used | Wikipedia |
| Dates | begun 1901; opened Dec 31, 1909; arch and colonnade 1915 | Wikipedia |
| Tower positions | ways 1255353996, 317352033: **443.9 m** apart (0.9 % short of 448.1 m), bearing 157.0° | OSM |
| Anchorages | ways 1017507380, 1255353998: 58 m along × 49 m across, centred 471 m from mid-span | OSM |
| Model ends | 940 m (Manhattan, ground 12.5 m) and 905 m (Brooklyn, 20.5 m); Overture flags end at 944 / 909 m | Overture (`Canal Street`, `Chrystie Street`); terrain grid |

Towers are set 448.1 m apart about the OSM midpoint (each 2.1 m outside its OSM centroid).
Estimated: truss / cable planes (±5.6, ±14.6 m, from the cited roadway and deck widths); masonry
pier height (9 m); column sections and bracing; saddle height and sag; floor heights away from
mid-span (3 % grade at the towers); anchorage height; the month work began in 1901 (taken as
October); the arch, colonnade and approach arcades are simplified.

## 3. Williamsburg Bridge — `williamsburg_bridge`

Sources: https://en.wikipedia.org/wiki/Williamsburg_Bridge ; https://www.nyc.gov/html/dot/html/infrastructure/williamsburg-bridge.shtml

| Dimension | Value | Source |
|---|---|---|
| Main span | 1,600 ft (487.7 m) | Wikipedia; NYC DOT |
| Deck width | 118 ft | Wikipedia |
| Towers | 333–335 ft above mean high water (Wikipedia); "310 feet" (NYC DOT) — 333 ft used | Wikipedia |
| Tower piers | masonry, 23 ft above mean high water; legs slant inward above the deck, top 14 ft narrower; two 45 ft bracing trusses | Wikipedia |
| Trusses | two, 67 ft apart, 40 ft deep; floor beams 5 ft deep | Wikipedia |
| Clearance | 135 ft at the middle; deck about 122 ft above mean high water at the shores | Wikipedia |
| Cables | four, 18 in | NYC DOT |
| Dates | work began Jun 19, 1896; opened Dec 19–20, 1903 | Wikipedia |
| Tower positions | ways 1016434034, 1016434035: 487.3 m apart, bearing 111.8° | OSM |
| Anchorages | ways 1016434036, 279593081: 49 m across × 41 m along, centred 442 m from mid-span | OSM |
| Model ends | 1,096 m (Manhattan, 7.7 m) and 947 m (Brooklyn, 15.7 m): ends of the deck outline (way 533212910) | OSM; terrain grid |

The side spans are not hung from the cables (cited); their length is not in the sources read and
follows the OSM anchorages (178 m). Estimated: leg sections and bracing pattern; saddle height
and sag; 3 % side-span grade; intermediate towers under the side spans; approach viaduct bents.
The 1952 connector from the Brooklyn plaza to the Brooklyn–Queens Expressway, which Overture
also names `Williamsburg Bridge`, is not modelled.

## 4. George Washington Bridge — `george_washington_bridge_1931`, `george_washington_bridge`

Source: https://en.wikipedia.org/wiki/George_Washington_Bridge

| Dimension | Value | Source |
|---|---|---|
| Main span | 3,500 ft (1,066.8 m) | Wikipedia |
| Length between anchorages | 4,760 ft | Wikipedia |
| Side spans | 610 ft (New Jersey), 650 ft (New York) | **recalled** from the Port Authority fact sheet (page not readable: script-rendered); consistent with 4,760 − 3,500 ft |
| Width | 119 ft; upper roadway 90 ft | Wikipedia |
| Towers | 604 ft above the water | Wikipedia |
| Clearance | 212 ft at mid-span, 195 ft under the New York anchorage (with the lower deck) | Wikipedia |
| Deck | 1931: 12 ft thick, no stiffening truss; 1962 lower-deck sections 30 ft thick | Wikipedia |
| Cables | four, 36 in | Wikipedia |
| Dates | begun Sep 21, 1927; opened Oct 25, 1931; lower level Jun 2, 1959 – Aug 29, 1962 | Wikipedia |
| Tower positions | ways 741784699 (New Jersey), 741784700 (New York): 1,064.5 m apart, bearing 104.4°, 72.5 × 28 m | OSM |
| New York anchorage | way 899357171: 85 × 55 m, centred 748 m from mid-span | OSM |

Two models: the single-deck bridge ends on Aug 29, 1962, when the two-level model appears.
Upper roadway heights follow the cited clearances plus the cited 30 ft (242 ft at mid-span,
225 ft at the New York anchorage); the 1931 deck is drawn 12 ft deep under the same roadway.
Estimated: cable pairs and legs 106 ft apart; leg sections, lattice pattern and portal arches;
saddle height; cable low point 8 m above the roadway; the New Jersey abutment; the 1962
lower-level approach from the anchorage to the Trans-Manhattan Expressway cut (ends at 53 m,
terrain grid). The terrain grid reads only 25–30 m at the New York anchorage, where the roadway
is at 68 m: the generic road will not meet the upper level there. New Jersey end: side span to
718 m from mid-span; Overture's flag ends at 700 m (ground 70 m).

## 5. Queensboro Bridge — `queensboro_bridge`

Sources: https://en.wikipedia.org/wiki/Queensboro_Bridge ; https://www.nyc.gov/html/dot/html/infrastructure/queensboro-bridge.shtml

| Dimension | Value | Source |
|---|---|---|
| Spans | 469.5, 1,182, 630, 984, 459 ft (3,725 ft) | Wikipedia |
| Approach viaducts | 1,052 ft (Manhattan), 2,588 ft (Queens); 7,449 ft in all | Wikipedia; NYC DOT |
| Trusses | two lines 60 ft apart, 45–118 ft deep; towers 185 ft above the lower chords | Wikipedia |
| Height | 350 ft | Wikipedia |
| Decks | lower 86 ft wide, upper 67 ft | Wikipedia |
| Clearance | at least 118 ft, at most 135–140 ft above mean high water; infobox 130 ft | Wikipedia |
| Piers | 130 × 40 ft at the base, 50 ft arch between two columns | Wikipedia |
| Dates | built 1901–1909; opened Mar 30, 1909 | Wikipedia; NYC DOT |
| Pier positions | ways 1016487161, …159, …155, …154, …157, …170 at −322.0, −180.1, 180.1, 370.9, 671.0, 810.3 m: spans 141.9, 360.2, 190.8, 300.1, 139.3 m (cited 143.1, 360.3, 192.0, 299.9, 139.9 m); bearing 119.6° | OSM |
| Model ends | the cited approach lengths: 642.6 m west (Second Avenue, ground 18.8 m) and 1,599 m east (6.4 m); Overture's lower-level flag ends at 448 m / 1,492 m | Wikipedia; terrain grid |

Estimated: the lower-chord curve (135 ft at the middle of the bridge, 118 ft at the anchor piers:
131.7 ft at the middle of the west channel span); where the 45 ft and 118 ft depths occur (45 ft
at the anchor piers and mid-channel, 118 ft over the island); the top-chord curve; upper deck
7.5 m above the lower; pier taper; approach grades; month of the 1901 start. The upper-level
ramps are not modelled.

## 6. Verrazzano-Narrows Bridge — `verrazzano_narrows_bridge`

Source: https://en.wikipedia.org/wiki/Verrazzano%E2%80%93Narrows_Bridge

| Dimension | Value | Source |
|---|---|---|
| Main span | 4,260 ft (1,298.4 m) | Wikipedia |
| Towers | 693 ft | Wikipedia |
| Width | 103 ft | Wikipedia |
| Clearance | 228 ft at mean high water | Wikipedia |
| Anchorages | 229 × 129 ft | Wikipedia |
| Dates | begun Aug 13–14, 1959; upper level Nov 21, 1964; lower level Jun 28, 1969 | Wikipedia |
| Tower positions | ways 1016642058 (Staten Island), 1016642060 (Brooklyn): 1,296.3 m apart, bearing 67.1°, about 41 × 13 m | OSM |
| Anchorages | ways 899356447, 899356446: centred 1,037 m and 1,048 m from mid-span | OSM |
| Model ends | 1,270 m (Staten Island, 36.6 m) and 1,255 m (Brooklyn) | Overture `Verrazzano-Narrows Bridge`; terrain grid |

One model with both decks (the lower roadway of 1969 lies inside the 1964 trusses). The side-span
length is not in the article text read; the cables enter the anchorages 1,018 m from mid-span
(OSM), i.e. side spans of about 370 m. Estimated: truss depth (24 ft), leg sections (9.4 × 13 m
to 7.6 × 9 m), portal struts, cable pairs at the deck edges, saddle height, sag, roadway heights
at the towers (7 m below mid-span) and anchorages (57 m), and the Brooklyn end height (45 m: the
Belt Parkway ramps go on elevated there).

## 7a. Hell Gate Bridge — `hell_gate_bridge`

Source: https://en.wikipedia.org/wiki/Hell_Gate_Bridge

| Dimension | Value | Source |
|---|---|---|
| Main span | 1,017 ft between the outer faces of the towers; 977.5 ft clear between the inner faces; 995 ft between tower centres | Wikipedia |
| Deck | 145 ft above mean high water at mid-span, 135 ft clear | Wikipedia |
| Arch top | 300–305 ft above mean high water — 305 ft used | Wikipedia |
| Towers | 220 ft high, concrete clad in granite | Wikipedia |
| Lower chords | 7–11 ft thick, on hinges at the tower bases | Wikipedia |
| Wards Island viaduct | about 2,650 ft, 30 plate-girder spans of 86–93 ft; arch piers up to 120 ft high, 20 × 65 ft | Wikipedia |
| Randalls Island viaduct | about 1,965 ft, 75–80 ft high, 24 spans of 80–87 ft | Wikipedia |
| Little Hell Gate | four inverted bowstring spans, 1,154 ft | Wikipedia |
| Bronx Kill | two-span truss, 350 ft | Wikipedia |
| Total length | 17,000 ft | Wikipedia |
| Dates | begun 1912, finished 1916, dedicated Mar 9, 1917 | Wikipedia |
| Tower positions | ways 1016643613, 1016643614: centroids **328.5 m** apart, 42–44 m across × 27–28 m along, outer faces 357 m apart; bearing 134.6° | OSM |
| Line | Overture rail segment `fb010fe0…` (Northeast Corridor, bridge flag, 5,055 m) moved 7 m sideways to the middle of the four-track deck (it then passes 0.6–2.6 m from the tower centroids) | Overture |
| Bronx Kill piers | ways 1256780015, 1256780016 at 1,086 and 1,213 m along the line | OSM |

OSM's towers do not match the article's three span figures (328.5 m between centroids against
995 ft = 303 m); the model keeps OSM's midpoint, bearing and outer faces and sets the inner
faces the cited 977.5 ft apart, so the towers are 29 m long and their centres 326.9 m apart.
The Little Hell Gate spans are placed from 1,811 to 2,163 m along the line: the low ground
(1.9–3.3 m) of the filled channel, which is also where the cited viaduct lengths put them
(Bronx Kill pier + 1,965 ft, then 1,154 ft, then 2,650 ft to the arch tower: within 15 m).
Estimated: arch ribs 60 ft apart; truss depth 40 ft at the crown and 140 ft at the hinges; hinge
height 8 m; tower plan above the base and the portal; rail grades away from the arch (to 12.8 m
at the Bronx end and 22 m at the Queens end, where the line continues on embankments 6–7 m
above the terrain grid); Bronx Kill truss depth; bowstring sag; one pier per two real ones;
month of the 1912 start.

## 7b. Triborough (Robert F. Kennedy) Bridge — `rfk_bridge_suspension`, `rfk_bridge_harlem_river_lift`, `rfk_bridge_bronx_kill`

Source: https://en.wikipedia.org/wiki/Robert_F._Kennedy_Bridge

| Dimension | Value | Source |
|---|---|---|
| Suspension span | main span 1,380 ft (420.6 m), side spans 700 ft, 2,780 ft; deck 98 ft wide; towers 315 ft above mean high water; 143 ft clear; cables 20 in | Wikipedia |
| Lift span | 310 ft long, 92 ft wide; side spans 195 ft; towers 210 ft above mean high water; 55 ft clear closed, 135 ft raised | Wikipedia |
| Bronx Kill | truss span 383 ft, approaches 1,217 ft; 55 ft clear | Wikipedia |
| Viaduct | concrete piers 60–140 ft apart; 62 ft above mean high water at Little Hell Gate | Wikipedia |
| Dates | groundbreaking Oct 25, 1929; opened Jul 11, 1936 | Wikipedia |
| Suspension towers | ways 1016642595, 1016642596: 419.1 m apart, bearing 149.8° | OSM |
| Lift towers | ways 1016646459, 1016646456: **104.0 m** centre to centre, 34.6 × 7.2 m, bearing 119.0°; OSM's movable roadway is 92–94 m long | OSM |
| Bronx Kill | the kill on Overture's two carriageways (base water), 81 m from the start of segment `40775599…` | Overture |
| Viaducts | Overture `Robert F. Kennedy Bridge` carriageways (nine segments), clipped at the three main structures | Overture |

Lift towers are set with their faces 310 ft apart about the OSM midpoint (centres 101.7 m apart).
Estimated: stiffening truss 20 ft deep under the suspension roadway; leg sections and struts;
saddle height, sag; anchorage blocks (38 × 46 m) and roadway height there (40 m); Queens end
height (20 m, about 10 m above the terrain grid: embankment to the Grand Central Parkway);
viaduct 1.5 m above the cited 62 ft; lift- and side-span truss depths, tower bracing,
counterweights; Bronx Kill truss depth (18 m) and width; the Bronx end height (16 m, about 10 m
above the terrain grid: the Bruckner interchange ramps go on). The ramps beyond the lift
span's Manhattan side span are not modelled.

## 8. High Bridge — `high_bridge`, `high_bridge_river_arches`, `high_bridge_steel_arch`

Source: https://en.wikipedia.org/wiki/High_Bridge_(New_York_City)

| Dimension | Value | Source |
|---|---|---|
| Length, height | 1,450 ft; 138–140 ft above the river — 140 ft used | Wikipedia |
| Stone arches | fifteen: eight of 80 ft, seven of 50 ft; piers 20 × 40 ft at ground level; springers about 84 ft above mean high water | Wikipedia |
| Steel arch | replaced five river arches in 1926–1928; 450 ft (elsewhere "about 400 ft"); 114 ft clear | Wikipedia |
| Dates | begun Aug 13, 1839; water May 30, 1848; walkway 1864; water supply ended 1958; closed 1970s–2015 | Wikipedia |
| Steel-arch piers | ways 1016652745, 1016656588: **142.2 m** centre to centre, bearing 97.0° | OSM |
| Deck outline | way 393767161: from 91 m west to 266 m east of mid-span, 7.5 m wide | OSM |

Three models: the ten surviving stone arches (1848–today), the five river arches (1848–1927)
and the steel arch (1927/28–today). The steel-arch piers are set 450 ft (137.2 m) apart about
the OSM midpoint. Inference used for the arch layout: five 80 ft arches on 10 ft piers are
exactly 450 ft, so the 80 ft arches stood 90 ft apart; with 50 ft arches 60 ft apart, one 50 ft
arch on the Manhattan side and three 80 ft plus six 50 ft arches on the Bronx side end 87 m west
and 261 m east of mid-span — the OSM outline ends at 91 m and 266 m. The split "one arch west,
nine east" is estimated (it is what the outline allows; the sources read do not state it).
Estimated: pier thickness at the springing (10 ft); crown level of the 50 ft arches; width 21 ft;
the two ends in the valley sides (140 m west, 302 m east: the cited 1,450 ft); steel rib depth
(2.4 m), spacing and springing height (13 m); the year the river arches came down (1927) and
the months of the rebuilding.

## 9a. Bronx–Whitestone Bridge — `bronx_whitestone_bridge`

Source: https://en.wikipedia.org/wiki/Bronx%E2%80%93Whitestone_Bridge

| Dimension | Value | Source |
|---|---|---|
| Main span | 2,300 ft (701.0 m); side spans 735 ft; 3,770 ft between anchorages | Wikipedia |
| Towers | 377 ft above mean high water | Wikipedia |
| Roadway | rises 150 ft above mean high water; clearance 134 ft 10 in | Wikipedia |
| Width | 74 ft between the cables | Wikipedia |
| Anchorages | 180 × 110 ft | Wikipedia |
| Trusses | added early 1940s, removed 2003–2005 | Wikipedia |
| Dates | tower contract Jun 1937; opened Apr 29, 1939 | Wikipedia |
| Tower positions | ways 1016686393 (Bronx), 1016686394 (Queens): 698.5 m apart, bearing 153.9° | OSM |
| Anchorages | ways 1016686391, 1016686396: centred 581–582 m from mid-span | OSM |
| Model ends | 1,175 m (Bronx, ground 4.2 m) and 899 m (Queens, 11.8 m) | Overture `Bronx-Whitestone Bridge`; terrain grid |

State shown: without stiffening trusses (1939–1940s and since 2005). Estimated: leg sections,
portal struts, pier size, saddle height and sag, roadway heights at the towers (3.2 m below
mid-span) and anchorages (33 m), approach piers; construction start taken as June 1937.

## 9b. Throgs Neck Bridge — `throgs_neck_bridge`

Source: https://en.wikipedia.org/wiki/Throgs_Neck_Bridge

| Dimension | Value | Source |
|---|---|---|
| Main span | 1,800 ft (548.6 m); tower to anchorage 555 ft; 2,910 ft between anchorages; 11,250 ft in all | Wikipedia |
| Towers | 346 ft above mean high water, on concrete islands 20 ft above it; flattened segmental arches under the struts | Wikipedia |
| Clearance | 142 ft | Wikipedia |
| Dates | groundbreaking Oct 22, 1957; opened Jan 11, 1961 | Wikipedia |
| Tower positions | ways 1016661640 (Bronx), 1016661642 (Queens): 547.0 m apart, bearing 179.6° | OSM |
| Anchorages | ways 1016661637, 1016661644: 60 × 42 m, centred 450 m from mid-span (the article's "250 by 350 ft" was not used) | OSM |
| Viaducts | straight from 1,100 m north to 820 m south of mid-span, then Overture's two carriageways (Bronx curve 916–928 m, Queens end 184–188 m) | Overture `Throgs Neck Bridge` |

Estimated: stiffening truss 28 ft deep under the roadway; deck width 28 m; legs 31 m apart and
their sections; saddle height, sag; roadway heights away from mid-span; the Queens end stops
about 22 m up (the Clearview / Cross Island ramps continue), the Bronx end at 7 m.

## 10a. Bayonne Bridge — `bayonne_bridge_1931`, `bayonne_bridge`

Source: https://en.wikipedia.org/wiki/Bayonne_Bridge

| Dimension | Value | Source |
|---|---|---|
| Arch span | 1,675 ft (510.54 m) | Wikipedia |
| Width | 85 ft | Wikipedia |
| Arch heights | lower chord 266 ft, upper chord 325 ft above the Kill Van Kull | Wikipedia |
| Clearance | 151 ft as built; 215 ft since Jun 8, 2017 (roadway raised 2013–2019, finished May 24, 2019) | Wikipedia |
| Viaducts | Port Richmond 2,010 ft, Bayonne 3,010 ft | Wikipedia |
| Dates | opened Nov 15, 1931 | Wikipedia |
| Abutments | ways 1013440560 (Bayonne), 1016686886 (Staten Island): centroids **533.1 m** apart, about 40 × 33 m, bearing 197.5° | OSM |
| Viaducts | Overture `Bayonne Bridge` carriageways | Overture |

Two models (deck at 151 ft until Jun 8, 2017; at 215 ft since). The arch bearings are set
1,675 ft apart about the OSM midpoint. Estimated: arch trusses 74 ft apart; bearing height 9 m;
arch depth at the ends (67.5 ft); floor depth 2.6 m; viaduct grades to the terrain grid (8.5 m
at the Bayonne end, 17 m at the Staten Island end); the month work began in 1928 (taken as
September). The 2013–2017 construction of the new deck above the old one is not shown.

## 10b. Goethals Bridge — `goethals_bridge_1928`, `goethals_bridge_eastbound`, `goethals_bridge_westbound`

Sources: https://en.wikipedia.org/wiki/Goethals_Bridge ; https://en.wikipedia.org/wiki/Goethals_Bridge_(1928%E2%80%932017)

| Dimension | Value | Source |
|---|---|---|
| 1928 bridge | cantilever, main span 672 ft, 135 ft clear (infobox 140), 62 ft wide, 7,109 ft long; opened Jun 29, 1928; closed Jun 9, 2017; demolished from Jan 2018 | Wikipedia |
| New bridges | cable-stayed, main span 900 ft (274.3 m); towers not above 272 ft, slanting outward; 135 ft clear; ground broken May 2014; eastbound Jun 10, 2017; westbound May 21, 2018 | Wikipedia |
| Tower footings | ways 1016689046/47 (west), 1016689044/45 (east): 273.6 m apart, bearing 124.9°; the two bridges 15–16 m either side of the common centre line | OSM |
| Viaducts | Overture `Goethals Bridge` carriageways | Overture |

Estimated (new spans): tower form (two legs per deck leaning outward to 272 ft), stay pattern
(12 pairs each way per leg), deck width 62 ft and depth 3 m, roadway heights, start of the
westbound span's construction (2016). Estimated (1928 bridge): **its position** — drawn parallel
to the new spans 45 m north of their common centre line; the sources read do not give its line —
anchor-arm length (77.6 m), suspended span, truss heights, straight viaducts (7,109 ft centred
on the main span), construction start (taken as the Outerbridge Crossing's, 1925), end date
2018.0 for all spans.

## 10c. Outerbridge Crossing — `outerbridge_crossing`

Source: https://en.wikipedia.org/wiki/Outerbridge_Crossing

| Dimension | Value | Source |
|---|---|---|
| Main span | 750 ft (228.6 m) | Wikipedia |
| Clearance | 143 ft | Wikipedia |
| Width, length | 62 ft; 8,800 ft | Wikipedia |
| Dates | built 1925–1928; opened Jun 29, 1928 | Wikipedia |
| Main piers | ways 1016687789, 1016687791: 228.3 m apart, bearing 85.9° | OSM |
| Anchor piers | ways 1016687790, 1016687792: 114 m beyond the main piers | OSM |
| Viaducts | Overture `Outerbridge Crossing`: east end 924 m from mid-span (ground 12 m); the New Jersey approach curves away beyond 600 m | Overture |

Estimated: truss heights (36 m over the main piers, 12 m at the anchor piers), suspended span
(114 m), trusses 14 m apart, floor 2.2 m, roadway grades, month of the 1925 start.

## 11a. Macombs Dam Bridge — `macombs_dam_bridge`

Source: https://en.wikipedia.org/wiki/Macombs_Dam_Bridge

| Dimension | Value | Source |
|---|---|---|
| Swing span | 408 or 415 ft | Wikipedia |
| Length, clearance | 2,540 ft; 25 ft | Wikipedia |
| 155th Street viaduct | 1,600 ft; begun Dec 1890 | Wikipedia |
| Dates | river span from May 1892; opened May 1, 1895 | Wikipedia |
| Swing span | rest-pier ends, ways 1016651857–60: axis 126.6 m (415 ft = 126.5 m), bearing 84.3°; pivot pier way 1016651861, 14.5 m across | OSM |
| Approaches | Overture `Macombs Dam Bridge` and the bridge-flagged `West 155th Street` | Overture |

Estimated: truss depths and 13 m spacing; the camelback span over the railroad (220 ft, from
66 to 133 m east of the pivot); pier sizes; roadway heights; viaduct height at Coogan's Bluff
(20.6 m, the terrain grid; the real bluff is higher). The shelter houses are not modelled.

## 11b. Washington Bridge — `washington_bridge`

Source: https://en.wikipedia.org/wiki/Washington_Bridge_(Harlem_River)

| Dimension | Value | Source |
|---|---|---|
| Arches | two of 510 ft; 134 ft clear at mean high water | Wikipedia |
| Length, width | 2,375 ft; deck 80 ft | Wikipedia |
| Ribs | six, 13 ft deep, 14 ft apart | Wikipedia |
| Main piers | 40 ft wide, 98 ft long at the skewbacks; nearly 100 ft from skewback to deck | Wikipedia |
| Approaches | semicircular arches of 60 ft on 13 ft piers; three in the Bronx plus an elliptical arch of 56 ft | Wikipedia |
| Dates | work began Jul 1886; opened Dec 1, 1888 | Wikipedia |
| Main piers | ways 1016657081, 1016657082: 167.2 m apart (510 + 40 ft = 167.6 m), 29–30 m across, bearing 120.4° | OSM |
| Ends | deck outline (way 393737880) and Overture `Washington Bridge`: 161 m west, 351 m east of the middle of the river arch | OSM; Overture |

The third main pier is placed one arch (550 ft) east of the middle pier. Estimated: parabolic
ribs; skewback height; floor depth 1.2 m; three approach arches on the Manhattan side; the Bronx
end height (40.5 m, terrain grid; the grid reads 31.5 m at the Manhattan end on the cliff edge,
where the deck is level at 46 m).

## 11c. University Heights Bridge — `university_heights_bridge`

Source: https://en.wikipedia.org/wiki/University_Heights_Bridge

Cited: swing span 264–270 ft; 50 ft wide; two 100 ft approach spans; opened Jan 1, 1895 as the
Harlem Ship Canal Bridge; floated to this site in June 1906; opened here Jan 8, 1908.
OSM: movable roadway 81.1 m (42.6 m west to 38.5 m east of the midpoint of rest piers
1016657433 / 1016657432, which are 88.5 m apart); pivot pier way 1016657434 (12.6 m); bearing
119.0°. Overture `University Heights Bridge`: 98.6 m west to 70.2 m east.
Estimated: closed clearance (25 ft — not in the article text read), truss depths and spacing,
pier sizes, end heights (7 m). The model's dates are those of this site (1906–1908).

## 11d. Broadway Bridge — `broadway_bridge`

Source: https://en.wikipedia.org/wiki/Broadway_Bridge_(Manhattan)

Cited: lift span 304 ft (92.7 m); 25 ft clear closed, 136 ft raised; towers 160 ft above mean
water; 558 ft long; built 1957–1962; subway Dec 26, 1960, roadway Jan 1961.
OSM: tower piers ways 1016658464, 1016658466, **94.3 m** apart, 32 × 5.5 m, bearing 44.6°;
outline 175 m. Towers set 304 ft apart about the midpoint.
Estimated: truss depth 10 m and spacing 17 m; tower bracing; counterweights; flanking spans;
end heights; month of the 1957 start. Earlier bridges on the site are not modelled.

## 11e. Henry Hudson Bridge — `henry_hudson_bridge`

Source: https://en.wikipedia.org/wiki/Henry_Hudson_Bridge

Cited: arch span 841 ft (256.3 m); 2,208 ft long; 143 ft clear; opened Dec 12, 1936; upper level
May 7, 1938. OSM: arch abutments (ways 1016658825, 1016658823) 258.6 m apart; end piers (ways
1016658824, 1016658822) 278.8 m apart; bearing 49.1°; outline 502 m. Overture bridge flags on
`Henry Hudson Parkway`: 323 m south to 321 m north (one roadway), 237 m to 251 m (the other).
Estimated: rib depth 12.5 ft and spacing 15 m; springing height 6 m; decks 6 m apart; spandrel
columns and bents; roadway heights toward the ends; construction start (mid-1935). One model
with both levels.

## 11f. Kosciuszko Bridge — `kosciuszko_bridge_1939`, `kosciuszko_bridge_eastbound`, `kosciuszko_bridge_westbound`

Source: https://en.wikipedia.org/wiki/Kosciuszko_Bridge

Cited: new spans cable-stayed, main span 624 ft, 90 ft clear, each deck 1,001 ft on 56 stays,
pylons 287 ft; eastbound Apr 27, 2017, westbound Aug 29, 2019; work from 2014. 1939 bridge:
main span 300 ft, 125 ft clear, 6,021 ft; opened Aug 23, 1939; on the site of the westbound
span; main span removed Jul 2017, approaches demolished Oct 1, 2017.
Overture: bridge-flagged `Brooklyn-Queens Expressway` segments `e2ac78e7…` (1,141 m) and
`8f4b1e93…` (875 m); Newtown Creek on them at 454–537 m and 356–442 m from the Brooklyn end.
OpenStreetMap has no pylon outlines here, but it splits the eastbound roadway into a way of
307 m (way 1314069242: the 1,001 ft deck) from 326 to 633 m along the line. With the cited 624 ft
main span and 377 ft back span the pylons stand 441 m along the line: on the Brooklyn bank, 13 m
from the water (the other way round they would stand in the creek at 516 m). The westbound
roadway is one unsplit way; its pylons are placed the same 13 m behind the Brooklyn water edge
(estimated).
Estimated: pylon sections; stay pattern (14 pairs each way); deck widths (27 m, 25 m); girder
depth; the month work began in 2014; 1939 truss depth and width, its 4 % approaches and bents,
its construction start (1938); the old viaducts are cut where today's bridge-flagged roadway
ends (23–26 m up).

## 11g. Marine Parkway–Gil Hodges Memorial Bridge — `marine_parkway_bridge`

Source: https://en.wikipedia.org/wiki/Marine_Parkway%E2%80%93Gil_Hodges_Memorial_Bridge

Cited: lift span 540 ft (164.6 m), 55 ft clear, 150 ft raised; three main spans 1,500 ft
together; 4,022 ft long; contracts mid-1936, main span floated in Jan 13, 1937, opened
Jul 3, 1937. Overture: two carriageways, 1,236 m. OSM: movable roadway 180 m long, centred
9.5 m south of the middle of the Overture line; no tower outlines.
Estimated: tower positions (lift span centred on OSM's movable span) and height (215 ft);
truss depths; equal flanking spans (480 ft); pier sizes; approach grades; start month.

## 11h. Roosevelt Island Bridge — `roosevelt_island_bridge`

Source: https://en.wikipedia.org/wiki/Roosevelt_Island_Bridge

Cited: lift span 418 ft (127.4 m); 40 ft wide; 2,877 ft long; 100 ft clear when open; begun
Mar 17, 1952; opened May 18, 1955. OSM: tower piers ways 1016496518, 1016496519, 134.2 m
centre to centre (= 418 ft between tower faces with towers 6.8 m deep), bearing 122.3°;
outline from 89 m west to 178 m east; Overture's Queens end 182.4 m east (ground 3.8 m).
Estimated: closed clearance (40 ft), tower height (170 ft), truss depth, counterweights, Queens
approach grade. The ramp into the Motorgate garage is not modelled.

## 11i. Pulaski Bridge — `pulaski_bridge`

Source: https://en.wikipedia.org/wiki/Pulaski_Bridge

Cited: bascule, main span 177 ft (54.0 m); 39 ft clear; 2,810 ft long; opened Sep 10, 1954.
OSM: bascule piers ways 1054539113, 992001660, **52.4 m** apart, 34–38 m across, bearing 10.8°.
Piers set 177 ft apart about the midpoint. Approaches: Overture `Pulaski Bridge` carriageways.
Estimated: girder depths, pier and operator-house sizes, construction start (1952).

---

## Numeric check of the built models (2026-11-10)

Span = distance between the two clusters of highest (or springing-level) vertices; top = highest
vertex; clearance = lowest vertex above the water within 16 m of mid-span (chord thickness
included, so a few decimetres under the cited figure where the low steel is a beam).

| Model | Cited span (m) | Model (m) | Cited top (m) | Model (m) | Cited clearance (m) | Model (m) |
|---|---|---|---|---|---|---|
| brooklyn_bridge | 486.3 | 485.1 (−0.26 %) | 84.8 | 84.8 | 38.7 | 38.7 |
| manhattan_bridge | 448.1 | 448.1 | 102.4 | 102.4 | 41.1 | 41.1 |
| williamsburg_bridge | 487.7 | 487.3 (−0.08 %) | 101.5 | 101.5 | 41.1 | 40.7 |
| george_washington_bridge (both) | 1,066.8 | 1,064.5 (−0.22 %) | 184.1 | 184.1 | 64.6 | 64.6 |
| queensboro_bridge | 360.3 (west span) | 360.2 | 106.7 | 106.7 | 39.6 (130 ft) | 40.0 |
| verrazzano_narrows_bridge | 1,298.4 | 1,296.3 (−0.16 %) | 211.2 | 211.2 | 69.5 | 69.5 |
| hell_gate_bridge | 297.9 clear (977.5 ft) | 297.9 | 93.0 | 93.0 | 41.1 | 41.2 |
| rfk_bridge_suspension | 420.6 | 419.1 (−0.35 %) | 96.0 | 96.0 | 43.6 | 43.2 |
| rfk_bridge_harlem_river_lift | 94.5 between faces | 94.5 | 64.0 | 64.0 | 16.8 | 16.8 |
| rfk_bridge_bronx_kill | 116.7 | 116.7 | — | 35.2 | 16.8 | 16.8 |
| high_bridge_steel_arch | 137.2 | 137.2 (piers) | 42.7 deck | 43.8 with parapet | 34.75 | 34.75 at the crown |
| washington_bridge | 155.4 (510 ft) | 155.0 | — | 46.0 | 40.8 | 40.8 at the crown |
| bronx_whitestone_bridge | 701.0 | 698.5 (−0.36 %) | 114.9 | 114.9 | 41.1 | 41.1 |
| throgs_neck_bridge | 548.6 | 547.0 (−0.29 %) | 105.5 | 105.5 | 43.3 | 42.9 |
| bayonne_bridge (both) | 510.5 | 510.5 | 99.1 | 99.1 | 46.0 / 65.5 | 46.0 / 65.5 |
| outerbridge_crossing | 228.6 | 228.3 (−0.13 %) | — | 79.7 (estimated) | 43.6 | 43.1 |
| goethals_bridge_east/westbound | 274.3 | 273.7 (−0.23 %) | 82.9 | 83.0 | 41.1 | 41.1 |
| goethals_bridge_1928 | 204.8 | 204.8 | — | 73.2 (estimated) | 41.1 | 40.6 |
| macombs_dam_bridge | 124.4–126.5 | 126.6 | — | 28.6 (estimated) | 7.6 | 7.1 |
| university_heights_bridge | 80.5–82.3 | 81.1 | — | 21.6 (estimated) | 7.6 (estimated) | 7.1 |
| broadway_bridge | 92.7 | 92.7 | 48.8 | 48.8 | 7.6 | 7.2 |
| henry_hudson_bridge | 256.3 | 256.3 | — | 55.4 (estimated) | 43.6 | 43.6 at the crown |
| kosciuszko_bridge_east/westbound | 190.2 | 190.2 | 87.5 | 87.5 | 27.4 | 27.4 |
| kosciuszko_bridge_1939 | 91.4 | 91.4 | — | 51.5 (estimated) | 38.1 | 37.7 |
| marine_parkway_bridge | 164.6 between faces | 164.6 | — | 65.5 (estimated) | 16.8 | 16.3 |
| roosevelt_island_bridge | 127.4 between faces | 127.4 | — | 51.8 (estimated) | — | 12.2 (estimated) |
| pulaski_bridge | 54.0 | 54.0 | — | 21.0 | 11.9 | 11.9 at mid-span |

Ends: Brooklyn, Williamsburg, Queensboro (cited approach lengths), Whitestone, Marine Parkway,
Roosevelt Island (Queens end) and the Verrazzano's Staten Island end finish within 1 m of the
real end and within 2 m of the terrain height; Manhattan Bridge 4 m short of Overture's flag
ends; Hell Gate 2 m past both ends of the line (on embankment height); Washington Bridge ends
exactly at Overture's flag ends, level at 46 m on the Manhattan cliff edge (grid 31.5 m) and at
40.5 m in the Bronx (grid 38.5 m); the others end as described per bridge.

Not checked: nothing was looked at in the viewer (no rendering on the build machine); the
models were only checked numerically and for finite coordinates (33 models, 368,340 vertices).
