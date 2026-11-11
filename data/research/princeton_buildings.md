# Princeton buildings: researched years (round of 2026-11-11)

Table: `data/tables/known_building_dates.princeton.csv`. Builder: `data/research/princeton_build/build_rows.py` with the row specs in `specs.py`.

## Sources opened
- Wikipedia (raw wikitext), about 60 articles: Princeton Historic District (its table of 64 contributing properties, with the year column), Princeton University and its colleges, Alexander Hall, Chapel, Jadwin, Hobey Baker Rink, Mudd, McCarter, Garden Theatre, Drumthwacket, Colross, Tusculum, Maybury Hill, Public Library, Seminary, IAS, Robertson Hall (School of Public and International Affairs), Graduate School, Palmer Square, Princeton Shopping Center, Princeton station, Stone Hill Church, Stuart Country Day School.
- Wikidata SPARQL (inception P571 for items in a box and for the OpenStreetMap `wikidata` tags): used for Clio Hall, East Pyne, Green Hall, TIGER, Thomas Clarke House, Old Kingston Mill.
- OpenStreetMap map API (16 boxes over Princeton): only 2 `start_date` tags (post-2010 buildings), so no building year came from OSM. It supplied names and `wikidata` ids.
- Not reachable: Princeton's own pages (403), etcweb.princeton.edu (certificate failure, 503), archive.org (reset). Wikipedia's API rate-limited hard; `action=raw` worked.

## Result
Rows written by `build_rows.py`; every row's point is `representative_point()` of one footprint and was re-tested point-in-polygon. Most are exact; about 25 carry "estimate" (ranges, matches by position only, footprints that merge several phases).

## Not dated (largest first, all over 3,000 m^2 on campus)
dc0ca7fb (19,132 m2, class 15B, near the stadium), 1446578e (13,573, 15B), Stadium Drive Garage, Princeton University Art Museum (new building reopened 31 Oct 2025; not clear whether the footprint is the new one), Eric and Wendy Schmidt Hall, Briger Hall, Frick Chemistry Laboratory, Dillon is done, 20 Washington Road, Jadwin Hall, Carl Icahn Laboratory, MacMillan, Andlinger Center, Julis Romo Rabinowitz Building, Guyot Hall, Lakeside Garage, Theater Drive Garage, Chambers Street Garage, Princeton High School (modern building; the 1929 building is gone), 693c7715's neighbours 4721 m2 are dated by position only. The Princeton Companion (the real source for these) could not be opened. Hall names (Holder, Blair arch halls, McCosh, Fine, Lewis Library, Whig Hall) have no Wikipedia article or no year in one.

## Possible errors in existing rows
- Alexander Hall (nj_outer): the Princeton University article says groundbreaking 1892, completed 1894 (first commencement held there June 1894). The existing row has 1892.
- Dillon Gymnasium, Firestone, Chapel, Nassau Hall rows agree with the articles opened.
