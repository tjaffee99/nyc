# Princeton landmarks, towns round (2026-11-11)

Models: `viewer/src/landmarks/princeton.ts`, export `PRINCETON` (14 entries). Scratch: `data/research/landmarks_princeton_build/`
(`fp.py` extracts the outlines, `check.ts` is the numeric check, `rings.ts.txt` the generated outline constants, `osm.py` read the OSM map API).

## Method
- **Plans**: `data/interim/counties/nj_mercer.parquet` (Overture / OpenStreetMap, ODbL), the named footprint, simplified to 0.35 m, anchored at its `representative_point()`, converted to local metres with the kit's formula. Footprint ids below. Courtyards (East Pyne, the Art Museum) are holes in the walls and cap; `replaces` holds the outer ring only.
- **Sources**: Wikipedia pages and the Princeton Campus Architecture pages of the Princetoniana Museum (`princetonianamuseum.org`), fetched this session; where a page would not open (Wikipedia has no article for East Pyne, Holder, Fine, Robertson, Whig, Clio; the Lewis fact sheet returned 403, the NJ State Library page for Holder Tower was a bot check) the figure comes from a **web-search result snippet** and is marked so below. No height was published for most buildings: those are estimates from storeys and named in each model's `Model:` fact. OSM (map API, four boxes of 0.01 degree) carries almost no `height` / `start_date` tags in Princeton (Alexander Hall `building:levels=3` only); the Overture `height_m` of a footprint was not used as a cited height.
- Dates: `built: [start, completion]`; where only an opening year is cited the start is an estimate (said in the model).

## Numeric check (`check.ts` rasterised at 0.5 m; plan = union of triangles on the ground, outside = plan cells outside the replaced outline)
| id | built | top (m) | cited top | plan m2 | footprint m2 | outside m2 | verts |
|---|---|---|---|---|---|---|---|
| pr_alexander_hall | 1892-1894.45 | 25 | none (estimated) | 1182 | 1130 | 53 | 672 |
| pr_east_pyne_hall | 1896-1897.9 | 44 | none (estimated) | 1974 | 1943 net (2458 with court) | 39 | 1188 |
| pr_chancellor_green | 1872-1873.4 | 27 (octagon wall 15.2 cited) | octagon 50 ft = 15.2 | 687 | 658 | 28 | 462 |
| pr_holder_hall | 1909-1911 | 44.2 | tower 145 ft = 44.2 | 1821 | 1821 | 0 | 414 |
| pr_firestone_library | 1946.5-1948.5 | 18.7 | none (estimated) | 8489 | 8489 | 0 | ~600 |
| pr_robertson_hall | 1963.5-1966.4 | 13 | ground storey 28 ft = 8.5 | 2152 | 2090 | 63 | 1482 |
| pr_lewis_library | 2006-2008.7 | 32.0 | 105 ft = 32.004 | 2451 | 2449 | 1 | 414 |
| pr_fine_hall | 1966.5-1970.2 | 51.82 | 170 ft = 51.816 | 1933 | 1916 | 17 | 966 |
| pr_jadwin_gymnasium | 1964.5-1969.4 | 18 | none (estimated) | 11045 | 10856 | 186 | 543 |
| pr_mccarter_theatre | 1928-1930.15 | 24.4 | none (estimated) | 2932 | 2930 | 1 | 423 |
| pr_whig_hall | 1891-1893 | 13.5 | none (estimated) | 470 | 435 | 35 | 675 |
| pr_clio_hall | 1891-1893 | 13.5 | none (estimated) | 501 | 486 | 17 | 648 |
| pr_art_museum | 2021.5-2025.83 | 18.5 | none (estimated) | 7438 | 7474 | 0 | 654 |
| pr_nassau_presbyterian | 1835-1836.5 | 34 | none (estimated) | 1796 | 1740 | 55 | 561 |
All plans are within 10 % of the footprint (largest: Alexander Hall +4.6 %, Whig Hall +8 %). Where a height is cited the top matches to under 0.01 m (Holder, Lewis, Fine). `npx tsc --noEmit` passes; the file also type-checks alone. No NaN vertices. Not looked at on screen.

## Per model
Footprint ids are the parquet ids (first 8 characters).
- **Alexander Hall** (567b56ec; 47 x 32 m, Overture 1,136 m2). Cited: groundbreaking 1892, completed 1894, opened 9 June 1894, William Appleton Potter, Richardsonian Romanesque, brownstone and red granite, 900 seats (https://en.wikipedia.org/wiki/Alexander_Hall_(Princeton_University)); 1892 in the district article. Estimated: 13 m eave, gable ridge 21 m, four conical turrets to 25 m (the real hall's tower and rose window are not modelled).
- **East Pyne Hall** (426e2cee, with courtyard). Cited: 1896-97 Potter (William A. Potter's works list, Wikipedia search result), "built in 1897", quadrangle 216 x 155 ft with a large tower over the western arch and a shorter battlemented one over the eastern (Princetoniana Museum page via search result https://www.princetonianamuseum.org/artifact/252ecfae-9f12-4bf4-ae94-647a29375c32; the outline is 65.9 x 50.6 m = 216 x 166 ft, the cited 155 ft is the courtyard-side measure). Estimated: all heights (14 m wall, towers 44 m and 24 m), tower plans. Towers on the western and eastern sides of the box frame.
- **Chancellor Green** (9ffc978a). Cited: erected 1872 (1905 library history https://static-prod.lib.princeton.edu/scsites/libraryhistory/1905_Williams.html; dedicated May 1873 by the Princetoniana Museum), octagon 64 ft across and 50 ft high, 160 ft wing to wing (the outline is 48.3 m = 158 ft). Conflict: the district article (Wikipedia) and `known_building_dates.nj_outer.csv` say 1870. Estimated: wing height 10 m, roof 22 m, lantern 27 m.
- **Holder Hall** (eb015a8f). Cited (search-result snippets of the NJ State Library record and a 2008 blog): commissioned 1909, dorm 1910, tower 1911, tower 145 ft (some sources 140 ft), Day & Klauder. Estimated: 15 m eave, tower plan 9.6 m, its place (outline's deepest point).
- **Firestone Library** (a680979a). Cited: opened 1948, extended 1971 and 1988, O'Connor & Kilham, four floors above ground (https://en.wikipedia.org/wiki/Firestone_Library). Estimated: 14.5 m eave, roof and entrance bay, start 1946.5. The outline includes the extensions (shown for all years).
- **Robertson Hall** (35939728; 65 x 32.4 m rectangle). Cited (Princetoniana Museum page, fetched): gift 1961, dedicated May 1966, three levels, main storey 28 ft, 58 tapered quartz-faced columns, travertine walls, Yamasaki. Estimated: 4.2 m upper floor, 3.6 m setback, column taper, start 1963.5. The columns stand on the footprint's edge.
- **Lewis Library** (97ea1042). Cited (university fact sheet, 403 on fetch, via search result): opened 11 Sept 2008, 105 ft to the parapet (103 ft in earlier coverage), 87,000 gsf, 4 / 3 / 2 storeys. Estimated: wing height 9.5 m, tower plan and place, start 2006. Gehry's folded roofs are reduced to a flat steel-grey cap and a lidded tower.
- **Fine Hall** (76ac0cb7). Cited (Princetoniana Museum pages, fetched): commissioned 1966, dedicated 17 March 1970, Warner, Burns, Toan and Lunde, three-storey base plus ten floors, tower 170 ft / 17 stories (zoning negotiation of 1965; other sources say 14 stories). Estimated: base 11 m, tower plan, window bands.
- **Jadwin Gymnasium** (e1cca83e). Cited (Wikipedia, fetched): groundbreaking 1964, opened 1969, Walker O. Cain & Associates, 250,000 sq ft on five levels, three interlocking shells. Estimated: all heights; shells drawn as parabolic vaults of 18, 15, 12.5 m.
- **McCarter Theatre** (8113c576). Cited: opened 21 Feb 1930, 40-ft proscenium (Wikipedia, fetched); Collegiate Gothic (search result). No architect confirmed. Estimated: heights, roof, stage-house end (the end with more room), start 1928.
- **Whig Hall, Clio Hall** (73a4015f, ed67075a). Cited: completed 1893, Arthur Page Brown, marble Greek Revival, identical (https://lostnewengland.com/2021/03/clio-and-whig-halls-princeton-new-jersey/); erected 1890-92 per the Princeton archive (search result), Ionic temple form (NJ State Library record). Estimated: heights, six-column portico, fronts facing each other, start 1891.
- **Art Museum** (4e124c10, three courtyards). Cited (Wikipedia, fetched): construction from summer 2021, opened 31 Oct 2025, Adjaye with Cooper Robertson, three storeys, nine interlocking pavilions, 144-145,000 sq ft. Estimated: all heights; the raised volumes sit on a 3 x 3 grid, not the real pavilion layout.
- **Nassau Presbyterian Church** (d3aaadcd). Cited: burned 1835, completed 1836, Charles Steadman, Greek Revival, stuccoed brick (Wikipedia, fetched). Estimated: heights, portico, steeple (34 m) and that the front faces Nassau Street.

## Not done
Nassau Inn and Palmer Square (no opened source for date or height), Princeton Battle Monument (1922: no source opened; the district article gives 50 ft / 15 m), Fuld Hall, Morven, Miller Chapel, McCosh Hall, Dickinson Hall, Graduate College quadrangle, Seminary Alexander Hall (1814, McComb; footprint 81c40e94).

## Notes on the existing Princeton models (not edited)
- `nj_chancellor_green` is not a model, but the dates row for Chancellor Green says 1870; the library history says erected 1872, dedicated 1873.
- Blair Hall's note says its construction years were "from memory"; the Nassau Hall 1756 size was "recalled". Nothing else clearly wrong found.
