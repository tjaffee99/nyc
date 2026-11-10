# Built-up extent of New York by snapshot year

Where the city was **built on** at the date of a real, dated map. One GeoJSON per snapshot
(`<place>_<year>.geojson`, WGS84). The pipeline uses them to turn ground from field to city, to cut
streets, and — only where no traced footprints exist — to place era-typical buildings on real lots,
marked `procedural`.

"Built-up" means blocks (or parts of blocks) the map itself marks as built: stippled or hatched
blocks, shaded parts of blocks, drawn buildings, heavy block fronts. Streets laid out on paper are
not built-up: every map from 1797 on shows a grid well beyond the built edge.

Nothing here is interpolated. A year without a snapshot has no file.

## Files

| file | content |
|---|---|
| `manhattan_<year>.geojson` | 1660, 1743, 1767, 1797, 1836, 1852, 1867, 1889, 1897 |
| `brooklyn_<year>.geojson` | 1767 (the ferry village), 1836, 1889, 1897 |
| `williamsburgh_1836.geojson` | the village before it joined Brooklyn (contained in `brooklyn_1889`) |
| `queens_<year>.geojson`, `bronx_<year>.geojson`, `staten_island_1897.geojson` | 1889 / 1897 from the USGS sheets; the old towns (Flushing, Jamaica, Astoria, Morrisania, Fordham, Stapleton …) are separate polygons in these files, not files of their own |
| `fire_1776.geojson`, `fire_1835.geojson` | burned districts (`kind = burned_district`), **estimated from text, low confidence** — see below |
| `tools/` | everything that made them (see *Tools*) |

Each file is a FeatureCollection, one Feature per polygon, largest first. Properties:
`name`, `place`, `year`, `kind` (`built_up` / `burned_district`), `ring`, `map` (title, author),
`map_url` (catalogue page of the map traced), `scan_url` (the image file), `georeferencing`,
`residual_m`, `confidence`, `method`, `note`, `area_ha` (this polygon), `vertices` (for hand-traced
rings: each vertex as `Street A & Street B` of today, or `map` for a point read off the warped map),
`nested_from` (the earlier snapshot whose area is included), `licence`.

## Snapshots

<!-- TABLE -->
| snapshot | map | own ha | nested ha | added by nesting ha | polygons | residual m | confidence |
|---|---|---|---|---|---|---|---|
| `manhattan_1660` | Afbeeldinge van de Stadt Amsterdam in Nieuw Neederlandt (the Castello Plan), a | 14.7 | 14.7 | 0.0 | 1 | 24.5 | medium |
| `manhattan_1743` | A Plan of the City and Environs of New York as they were in the years 1742-174 | 64.5 | 64.5 | 0.0 | 1 | 13.4 | low-medium |
| `manhattan_1767` | Plan of the City of New York in North America, surveyed in the years 1766 & 17 | 145.3 | 145.3 | 0.0 | 1 | 9.2 | medium-high |
| `manhattan_1797` | A New & Accurate Plan of the City of New York in the State of New York in Nort | 221.1 | 231.5 | 10.1 | 3 | 15.8 | medium-high |
| `manhattan_1836` | Topographical Map of the City and County of New-York, and the adjacent Country | 898.5 | 917.5 | 18.8 | 13 | 7.7 | high |
| `manhattan_1852` | Map of the City of New-York extending northward to Fiftieth St., surveyed and  | 1,424.2 | 1,476.7 | 51.5 | 46 | 6.1 | medium |
| `manhattan_1867` | Plan of New York City, from the Battery to Spuyten Duyvil Creek, showing every | 722.0 | 1,946.6 | 1223.6 | 106 | 10 | medium |
| `manhattan_1889` | USGS 1:62,500 topographic quadrangles: Harlem, N.Y.-N.J. (edition of 1891), Br | 2,424.0 | 3,179.4 | 754.0 | 64 | 30 | low-medium |
| `manhattan_1897` | USGS 1:62,500 topographic quadrangles: Harlem, N.Y.-N.J. (edition of 1897), Br | 4,269.8 | 4,468.4 | 196.2 | 56 | 30 | medium |
| `bronx_1889` | USGS 1:62,500 topographic quadrangles: Harlem, N.Y.-N.J. (edition of 1891), Br | 590.2 | 590.2 | 0.0 | 63 | 30 | low-medium |
| `bronx_1897` | USGS 1:62,500 topographic quadrangles: Harlem, N.Y.-N.J. (edition of 1897), Br | 3,170.6 | 3,193.9 | 23.1 | 86 | 30 | medium |
| `brooklyn_1767` | Plan of the City of New York in North America, surveyed in the years 1766 & 17 | 4.5 | 4.5 | 0.0 | 1 | 9.2 | medium |
| `brooklyn_1836` | Topographical Map of the City and County of New-York, and the adjacent Country | 112.0 | 112.6 | 0.6 | 9 | 9.1 | medium-high |
| `brooklyn_1889` | USGS 1:62,500 topographic quadrangles: Harlem, N.Y.-N.J. (edition of 1891), Br | 3,006.3 | 3,010.3 | 3.9 | 75 | 30 | medium |
| `brooklyn_1897` | USGS 1:62,500 topographic quadrangles: Harlem, N.Y.-N.J. (edition of 1897), Br | 5,813.3 | 5,902.8 | 88.3 | 117 | 30 | medium |
| `queens_1889` | USGS 1:62,500 topographic quadrangles: Harlem, N.Y.-N.J. (edition of 1891), Br | 718.4 | 718.4 | 0.0 | 90 | 30 | low-medium |
| `queens_1897` | USGS 1:62,500 topographic quadrangles: Harlem, N.Y.-N.J. (edition of 1897), Br | 2,741.1 | 2,837.1 | 95.2 | 145 | 30 | medium |
| `staten_island_1897` | USGS 1:62,500 topographic quadrangles: Harlem, N.Y.-N.J. (edition of 1897), Br | 1,212.9 | 1,212.9 | 0.0 | 60 | 30 | low-medium |
| `williamsburgh_1836` | Topographical Map of the City and County of New-York, and the adjacent Country | 30.3 | 30.3 | 0.0 | 12 | 9.1 | medium-high |
| `fire_1776` | no map traced: outline constructed from the written description in Wikipedia,  | 24.7 | 24.7 | 0.0 | 2 | n/a | low |
| `fire_1835` | no map traced: outline constructed from the written description in Wikipedia,  | 10.3 | 10.3 | 0.0 | 1 | n/a | low |
<!-- /TABLE -->

*own* = what this map alone shows; *nested* = the file's area (own plus every earlier snapshot of the
place); *added by nesting* = earlier built-up ground this map's reading did not return.

## How to use them

* **Nesting.** Every file contains the earlier snapshots of its place (the union is taken in
  `tools/build.py`). The city did not un-build between two maps; where a later reading misses ground
  an earlier map shows as built, the cause is the reading (a square or yard read as open, a dark
  copy, a different shoreline, a sheet not read), or a real clearance that was built on again
  (Fort George, razed 1790, is in 1767 and absent from the 1797 reading). The table gives the amount
  per snapshot. Two files lean on it by design: `manhattan_1867` (only the sheets north of 20th St were
  read; the rest is 1852) and `manhattan_1889` (nothing read west of 74°00′ W, and a faded scan:
  754 ha of its 3,179 ha come from the earlier snapshots — treat 1889 as a lower bound).
* **Between snapshots.** A block first inside snapshot *k* was built up between *k-1* and *k*.
* **Shoreline.** Extents follow the map's own shore where the edge is the waterfront (1660: Pearl St;
  1743: Water St; 1767 and 1797: the map's wharf line; 1836: the bulkhead line, 30 m inside). The
  USGS snapshots are cut at 60 m from a street of today. Clip with the land-year layer anyway before
  placing buildings: these edges are good to a block, not to a wharf.
* **Open grounds inside the extent** (the Common / City Hall Park, the Battery, Tompkins Square,
  Central Park and squares over 0.6-1 ha) are holes or outside. Smaller squares and yards are filled.
* **Fires are not retreats.** `fire_1776` and `fire_1835` are separate files and are never subtracted
  from an extent. Use them to end the buildings standing inside them in that year.
* **Coverage.** A snapshot says nothing outside its map: Ratzer stops near today's 50th St, Colton
  1836 near 42nd St (and at Bergen St / Clinton Av in Brooklyn), Dripps 1852 at 50th St, Dripps 1867
  was read from 20th St to the Harlem River, the USGS
  snapshots at the quadrangle edges named in their notes.

## Where the maps come from, and how they were georeferenced

**NYPL maps (1743, 1767, 1797, 1852, 1867).** NYPL's Map Warper is retired (maps.nypl.org now redirects to a
web archive), but its ground control points survive in the NYC Space/Time Directory dump
<https://s3.amazonaws.com/spacetime-nypl-org/datasets/mapwarper/mapwarper.objects.ndjson> (9,657
maps; per map: NYPL image id, control points `[x, y, lat, lon]`, mask; CC0). `tools/find_maps.py`
lists them. The control points refer to NYPL's **full-size master** (`https://images.nypl.org/index.php?id=<imageId>&t=u`,
a TIFF), not to the IIIF image of the same id, which is trimmed and smaller (Ratzer: IIIF 4736 × 6407,
master 5046 × 6758 — with the IIIF image the warp was off by hundreds of metres). `tools/warp.py`
fits pixel → UTM 18N with an affine, 2nd-order or thin-plate-spline model chosen by cross-validation
(10-fold, leave-one-out under 60 points), after dropping blunders; **the residual quoted is the
cross-validated RMS**: how far a control point lands from where a fit that did not see it puts it.

**Library of Congress (1836).** Colton's map is not in the dump. Six points read by eye, then
`tools/autoalign.py`: in 700 m windows the map's light street strips are matched to today's street
centrelines (Overture roads) by cross-correlation; windows that agree with one affine fit become
control points (60 over Manhattan; 19 more for the Brooklyn fit); thin-plate spline.

**Castello Plan (1660).** 13 points picked on the plan against today's intersections of Broadway,
Wall, William, Pearl, Broad and Whitehall Sts, Exchange Pl and Beaver St, and the fort (Custom House
block). The plan is a bird's-eye drawing; the 24.5 m residual is the drawing's, and the extent's
edges are set on today's streets, not on the warped image.

**USGS (1889, 1897).** GeoTIFFs as georeferenced by USGS, no further fit. Checked by eye on four
crops against today's streets: within about 20-40 m. Automatic matching (as used for the Bay Area
sheets) did not converge here: the block pattern is too regular.

All maps are public domain (NYPL public-domain collections; Library of Congress Geography and Map
Division, "free to use and reuse"; USGS). The tracings and readings are this project's (CC0).

## The snapshots one by one

### manhattan_1660 — the Castello Plan
*Afbeeldinge van de Stadt Amsterdam in Nieuw Neederlandt*, after Jacques Cortelyou's survey of 1660
(copy of c. 1665-70, Florence; NYPL photograph, image 54682). Every house is drawn. The extent is
the town inside the wall east of Broadway — Wall St, Pearl St (the East River shore of 1660), State
St, Broadway — with Fort Amsterdam, plus the house row on the west side of Broadway from Beaver St
to Morris St. **14.7 ha.** The usual "about 22 ha below Wall St" is the whole area inside the wall
shore to shore; the difference is the gardens, the Company's garden and the burial ground between
Broadway and the Hudson, which the plan draws without houses, and the strand. Block interiors east of
Broadway are gardens on the plan: place houses along the street fronts only. Confidence medium.

### manhattan_1743 — Grim's plan
David Grim's plan of the city "as they were in the years 1742-1743 and 1744", drawn from memory in
1813 (NYPL image psnypl_map_304, Map Warper 15328, 13 points, residual 13.4 m). Built blocks are
drawn with shaded house fronts. Only the northern edge is taken from it (Fulton St – Ann St – Nassau
St – Beekman St – Pearl St – Peck Slip); the Hudson side is Ratzer's shore, the East River side Water
St. **64.5 ha.** Low-medium: a recollection drawn seventy years later, edge good to one or two blocks.
The surveyed plans of the period — Lyne–Bradford (1728-31) and Maerschalck (1755, LoC
<https://www.loc.gov/item/73691802/>) — were not georeferenced here; either would replace this.

### manhattan_1767 and brooklyn_1767 — Ratzer
*Plan of the City of New York … surveyed in the years 1766 & 1767*, Bernard Ratzer (NYPL image
434801, Map Warper 15264; 150 of 153 points, residual 9.2 m). Built blocks are stippled dark; laid-out
blocks (Delancey's grid, the Trinity Church farm streets) are outlines over field pattern. Hand-traced:
Hudson shore, Reade St, Broadway, round the Common, Park Row, the blocks towards the Fresh Water,
Bayard St, Madison St, Catherine St, the wharf line; and the house rows along the Bowery to Broome St.
**145.3 ha.** A tone classification of the same area gave 144.5 ha (threshold 0.14) — the two agree,
the hand trace is the file. Medium-high; edge good to a block.
Brooklyn is the ferry village only (**4.5 ha**).

### manhattan_1797 — Taylor–Roberts
*A New & Accurate Plan of the City of New York*, 1797 (NYPL image psnypl_map_303, Map Warper 15327,
30 points, residual 15.8 m). The plan hatches built blocks and built parts of blocks. Classified by
tone inside a hand-drawn envelope that keeps out the meadows and hill hachures north of the town.
**221 ha own, 232 ha nested.** Medium-high. The largest residual of the NYPL maps: an edge can sit
half a short block off.

### manhattan_1836, brooklyn_1836, williamsburgh_1836 — Colton
*Topographical Map of the City and County of New-York, and the adjacent Country*, J. H. Colton & Co.,
1836 (LoC <https://www.loc.gov/item/2007627512/>, image `wd000155`, full resolution crop; residual
7.7 m Manhattan, 9.1 m Brooklyn). Colton shades the built part of every block and leaves the rest
white — the best pre-1850 source. Classified by tone (median over 18 m, threshold 0.19, opening 12 m
so that block outlines of unbuilt blocks do not count). **898 ha own** in Manhattan (to about 14th
St on the east, 21st St on the west, with built pieces to the low 30s), **112 ha** Brooklyn, **30 ha**
Williamsburgh. High / medium-high. The hachured grounds north-east of Third Av and 23rd St (Bellevue,
Kips Bay, Murray Hill) were kept out of the reading: houses there are not in the extent.

### manhattan_1852 — Dripps / Harrison
*Map of the City of New-York extending northward to Fiftieth St.*, surveyed by John F. Harrison,
published by M. Dripps (NYPL image 1528179, Map Warper 14758, 36 points, residual 6.1 m). Every
building is drawn. Built-up = where the drawn footprints darken the sheet against its local paper
tone (threshold 0.17, calibrated: built-out blocks 88-94 % covered, farmland under 8 %); strips under
20 m wide (shore hachures) dropped. **1,424 ha own.** Medium: the NYPL copy is varnished and dark, thin edges of the city can be off by a block, and
which state of the plate this copy is was not checked (first issued 1852; the Map Warper record says
1857). If it is a later state the snapshot is late by up to five years.

### manhattan_1867 — Dripps, every lot and building
*Plan of New York City, from the Battery to Spuyten Duyvil Creek, showing every lot and building
thereon*, M. Dripps, 1867, sheets 9-18 of 20 (NYPL images 1520732-1520741, Map Warper 8575-8584;
3-5 control points per sheet, affine; cross-validated residual 0-27 m by sheet, median 8 m; sheet 12
sits about 25 m off today's streets by eye). The plan hatches every building; empty lots are outlines.
`tools/mosaic.py` reads each sheet by tone inside its mask (threshold 0.11 against the local paper
tone: built-out blocks of the West 30s read 0.6 covered, the empty West 70s 0.2 before clean-up),
merges the sheets, cuts Central Park, keeps only ground within 70 m of a street of today (the shore
hachures and the river-side railway read as long strips) and drops strips under 20 m.
**722 ha own in the 3,444 ha read** (20th St to the Harlem River); **1,947 ha nested.** Medium.
The first snapshot that reaches Yorkville, Manhattanville and Harlem: built pieces along Third Av in
the 60s-80s and the 110s-120s. Known false readings: hatched institutions' grounds and hill hachures
(Mount Morris, a few squares) come out as built rectangles; a strip 25 m inside every sheet join is
not read.

### *_1889 and *_1897 — USGS 15-minute sheets
Harlem and Brooklyn, editions of 1891 (→ 1889) and 1897; Staten Island and Paterson, editions of 1898
(→ 1897). The sheets draw a built block front as a heavy black band and a built-out block as a solid
bar. Built-up = heavy ink over 22 % of the ground within 80 m (about 40 % of the frontage; built-out
Midtown reads 0.57-0.64, Central Park 0.01, the Washington Heights plats 0.08). Heavy = surviving an
opening by 7.5 m on the two bold 1897 sheets and Brooklyn 1891, by 5 m on the crisper Staten Island and
Paterson sheets and the faded Harlem 1891 scan (their bands measure 10-15 m). Medium (1897),
low-medium (1889):
* 1889 Manhattan and Brooklyn lack everything west of 74°00′ W (the Paterson and Staten Island sheets
  of that survey were not read): the lower west side is the 1852 extent. Manhattan 1889 reads 2,424 ha
  against 4,270 ha in 1897 — more than eight years of building; part of the gap is the faded scan.
* The 1891 Harlem scan is faded; its threshold is set per sheet and reads thinner than the 1897 scans.
* Years are the USGS catalogue's content dates; the collars were not read.
* Platted tracts drawn house by house (Unionport, Wakefield, parts of Queens) read as partly built.

### fire_1776, fire_1835 — estimated
No map of either burned district was traced. Both outlines are constructed from the descriptions in
Wikipedia (<https://en.wikipedia.org/wiki/Great_Fire_of_New_York_(1776)>,
<https://en.wikipedia.org/wiki/Great_Fire_of_New_York>), quoted in each file's `note`, and are
**estimates, low confidence**. 1776: from Whitehall Slip to Broadway at Beaver St, then Broadway to the
Hudson up to Barclay St, without the St Paul's block. 1835: William St – Wall St – the East River –
Broad St / Coenties Slip; the north edge at Wall St is my reading of "17 blocks", against the
article's "Maiden Lane". The 1776 article shows a contemporary map with the burned blocks marked in
red; an 1836 map of the burnt district exists. Tracing either would replace these.

## Checks

* Every polygon valid (`shapely.is_valid`), every file loads; areas printed by `tools/build.py`.
* Nesting holds by construction and is re-checked in the built files (`tools/check.py`).
* Size against people (population figures quoted from memory of the censuses — recheck against the
  project's population table): 1771, 21,900 on 145 ha = 150 per ha; 1800, 60,500 on 232 ha = 260;
  1835, 268,000 on 918 ha = 290; 1850, 515,500 on 1,477 ha = 350; 1900, 1,850,000 on Manhattan's 1897
  extent (4,468 ha) = about 410. Rising and of the right order for a walking city.
* Ratzer hand trace against tone classification: 145.3 vs 144.5 ha.

Not checked: the files in the viewer; the fire outlines against any map; the USGS survey years on the
collars; the Dripps plate state.

## What the built fabric looked like (for generated buildings on real lots)

Storey ranges for row houses are quoted from the NYC Landmarks Preservation Commission's *Rowhouse
Manual* (<https://www.nyc.gov/assets/lpc/downloads/pdf/pubs/rowhouse.pdf>, read for this file).
Lines marked ESTIMATE are mine, not sourced.

| snapshot | typical buildings | storeys | source |
|---|---|---|---|
| 1660 | Dutch town houses, gable to the street, wood and brick; a few larger (the Stadt Huys, the church in the fort) | 1 to 2 plus garret, as drawn on the Castello Plan itself (ESTIMATE of 1-2½ from the drawing) | the plan (`scan_url`) |
| 1743, 1767 | Dutch gabled houses surviving south of Wall St; English Georgian brick houses; warehouses on the slips | ESTIMATE 2-3 plus garret | no source read |
| 1797 | Federal row houses, brick, peaked roof with dormers; frame houses at the edge | "two to three stories high with basement and attic half-story with dormer windows" (Federal, 1800-1835) | LPC Rowhouse Manual |
| 1836 | Federal and Greek Revival rows; counting houses and stores downtown | Greek Revival (1830-1850): "three to three and one-half stories high with basement" | LPC Rowhouse Manual |
| 1852 | Greek Revival, Gothic Revival, Anglo-Italianate and Italianate brownstone rows; first tenements; stores and lofts on Broadway | Gothic Revival (1840-60): "three stories plus basement"; Anglo-Italianate (1840-60): "three to five stories high"; tenements ESTIMATE 4-5; lofts ESTIMATE 4-5 | LPC Rowhouse Manual; ESTIMATE |
| 1867 | Italianate, Anglo-Italianate and Second Empire brownstone rows; pre-law tenements; frame houses and shanties at the edge (Yorkville, Harlem) | Anglo-Italianate (1840-60) and Second Empire (1860-75): "three to five stories high"; tenements ESTIMATE 4-5; edge frame houses ESTIMATE 2-3 | LPC Rowhouse Manual; ESTIMATE |
| 1889 | Second Empire and Neo-Grec brownstones, old-law ("dumbbell") tenements after the Tenement House Act of 1879, cast-iron lofts, first elevator office buildings | Second Empire (1860-75) and Neo-Grec (1865-85): "three to five stories high"; tenements ESTIMATE 5-6 on 25 × 100 ft lots; cast-iron lofts ESTIMATE 5-6 | LPC Rowhouse Manual; <https://en.wikipedia.org/wiki/Old_Law_Tenement> (the law and the plan form; it gives no storey count) |
| 1897 | the same, plus Renaissance Revival rows uptown and flats | Renaissance Revival (1880-1920): "two to three stories high"; flats ESTIMATE 5-7 | LPC Rowhouse Manual; ESTIMATE |

Outside Manhattan and downtown Brooklyn the 1889-97 fabric is detached and row frame houses of 2-3
storeys (ESTIMATE). Lots: Manhattan's grid lot is 25 × 100 ft (ESTIMATE from general knowledge of the
1811 plan, not re-read); use the real tax lots.

## Maps looked at and not used, and what would fill the gaps

| years | map | status |
|---|---|---|
| 1695 | Miller plan | drawn from memory in London, not to scale; not attempted |
| 1728-31 | Lyne–Bradford plan | no scan found in the Map Warper dump or by three LoC searches; would give a surveyed 1730 |
| 1755 | Maerschalck plan, LoC item 73691802 (`ar110100`) | found, not georeferenced (budget) |
| 1775 | Montresor plan, Map Warper 12949 (111 points) | not opened here |
| 1782 | British Headquarters map | not looked for |
| 1807 / 1817 | Bridges (Map Warper 15281), Poppleton (14716, 108 points; 15128) | rendered and viewed: street and block lines without a mark for built blocks that I could read; no extent taken |
| 1829 / 1834 / 1840 | Burr (12809, 15169, 15089) | 1834 classified: the map tints all laid-out blocks alike (1,335 ha, the whole grid) — not an extent |
| 1865 | Viele, sanitary and topographical map (16216) | not opened here; a topographical map, not expected to mark built blocks |
| 1867 | Dripps 1867, sheets 2-8 (south of 20th St; Map Warper 8568-8574) and 19-20 (north of the Harlem plain; 8585, 8586) | not read: south of 20th St the 1852 extent stands in; Washington Heights and Inwood have nothing before 1889 |
| 1879 / 1891 | Bromley atlases (plates in the dump, e.g. 27677-27689) | not opened here; atlases of this kind colour every building, plate by plate — a candidate for a real c. 1880 snapshot |
| Brooklyn 1850-69 | *Map of Consolidated City Brooklyn* 1850 (27001, 117 points), Dripps 1869 sheets (8559-8566; the same drawing style as Dripps 1867, so `tools/mosaic.py` should read them) | not processed: **Brooklyn has no snapshot between 1836 and 1889** |

## Tools

`python -I tools/<script>` from the repository root with the project's venv.

| script | does |
|---|---|
| `streets.py` | `intersection("Wall Street", "Broadway")` → lon, lat from Overture roads; nearest intersection; pedestrianised stretches (Wall St west of William St) are met by prolonging the street line |
| `find_maps.py` | search the Map Warper dump by name, year, area |
| `warp.py` | fit control points, residuals, render any box of a map in local metres with today's streets and a grid (`info`, `view`) |
| `gcps_own.json` | control points made here (Castello Plan, Colton 1836) |
| `autoalign.py` | control points from matching a map's streets to today's |
| `classify.py`, `classify_runs.py` | tone classification and its per-map parameters, envelopes, exclusions |
| `mosaic.py` | multi-sheet building plans (Dripps 1867): each sheet read by tone, merged |
| `usgs.py`, `usgs_extent.py` | USGS sheets: render, heavy-ink reading |
| `classified/` | the polygons these readings produced (local metres), read by `build.py` |
| `snapshots.py` | **the snapshot definitions**: map, URLs, notes, hand-traced rings |
| `build.py` | builds every GeoJSON, nests, prints areas, fills the table above |
| `check.py` | validity, nesting and area checks on the built files |

Local coordinates used throughout the tools: X = UTM 18N easting − 580,000, Y = northing − 4,500,000
(metres). Downloads are cached under `data/raw/extents/` (gitignored; about 300 MB). `build.py` needs
no download: hand-traced rings are in `snapshots.py`, classified readings in `tools/classified/`.
Re-reading a map (`classify_runs.py <name>`, `mosaic.py run manhattan_1867`, `usgs_extent.py build`)
fetches its scan again; the USGS run takes about eight minutes and 2 GB of memory.
