# Princeton and Yale, round 2 (2026-11-11)

Tables: `data/tables/known_building_dates.princeton2.csv` (16 rows) and `.new_haven2.csv` (4 rows); every point is `representative_point()` of its footprint and passed a point-in-polygon test (20 of 20). Scripts: `data/research/princeton_yale_round2_build/` (`mk.py` + `specs_p.py` / `specs_n.py`). Raw pages: `data/interim/princeton_yale_round2_raw/`.

## How sources behaved
princeton.edu, discovery.princeton.edu (not resolvable), nuclearprinceton and architizer answered 403; the Wikipedia API is rate-limited, `action=raw` and WebFetch of article URLs work. paw.princeton.edu, dailyprincetonian.com, princetonianamuseum.org, engineering.princeton.edu, news.yale.edu, nhba.yale.edu and ConnCRIS opened. Search-result summaries were NOT counted as opened pages; rows that rest on one say so.

## Princeton rows (per building: year, page opened)
Stadium 1998 (Wikipedia; footprint 1446578e is the stadium by Wikidata Q6587721 coordinates); Jadwin Hall 1970 (Princetoniana Museum); Frick Chemistry Laboratory 2010 (PAW 13 Oct 2010, four storeys, atrium 75 ft); Icahn Laboratory 2003 (Daily Princetonian May 2003); Andlinger Center 2016 (engineering.princeton.edu 6 Jan 2016); Guyot Hall 1909 (PAW); Stadium Drive Garage 2022 (PAW April 2022, planned); estimates: Art Museum 2025 (footprint may still be the 1966 building's), Briger Hall 2025, Lakeside (dc0ca7fb, c237ff6e, garage) 2015 (matched by position), 20 Washington Road 1929 (renovated former Frick lab; 1929 from an unopened snippet), Julis Romo Rabinowitz Building 2016, Peretsman Scully Hall 2013 (footprint 64f9cfac, matched by position and OSM levels=5), Princeton High School 1929 (Moore Street building; footprint also holds 2003-07 additions).

## Princeton still undated (over 2,500 m2)
Eric and Wendy Schmidt Hall eee60462 (conversion of Guyot, not a new year found), Theater Drive and Chambers Street and Spring Street and Prospect Avenue garages, MacMillan, 185 Nassau Street, DeNunzio Pool, Athletic Center, Academic Center, ba283dce, 19dd9b1e, e29e599b, 5bb60626, plus apartment/commercial and school footprints (Avalon, The Alice, Johnson Park School, Littlebrook ES and others). Fine Hall, McCosh, Holder, Whig, Lewis, Frist were not on the undated list (already dated).

## New Haven rows
Yale Science Building 2019 (Yale News, exact); Silliman College 1940 (Wikipedia; merged phases, estimate); Schwarzman Center 1901 (ConnCRIS "1901 CIRCA", estimate); Central Power Plant 1917 (Yale New Haven Building Archive, which also says 1918). Not found in an opened source: 101 College Street, Wintergreen Building, the Peabody, Hotel Taft/Shubert/courthouses/library (already dated by assessor or ConnCRIS), City Hall (1861 ConnCRIS), Divinity (assessor 1932). Remaining large heap/missing footprints: 5d87de70, 64118fbc, cebd14e2, 0cc08bb3, 40eb8744, f97a3f40, 4e942153, fa8acda2, 56c8439d, 445002d0, bd4a0939, 618e4cb7, 354a9a2e, daf839c5, b4f38ae2 and the industrial ones (a27c5a4f, 3f906e01, 62d73c0c, 772bd44a).

## The three doubted rows of known_building_dates.ct.csv
- Yale Repertory Theatre: Wikipedia (raw, opened) says Calvary Baptist Church "was erected in 1846"; ConnCRIS (opened) says 1871 for CALVARY BAPTIST CHURCH/YALE REPERTORY THEATER at 1120 Chapel St. Two opened sources disagree; 1846 is the congregation's building per Wikipedia, 1871 may be a rebuild. Not resolved.
- Lanman-Wright Hall 1912: Old Campus table in Wikipedia (opened): "1912, William Adams Delano", built as Wright Hall, renamed after 1993. Row stands.
- McClellan Hall 1925: same table, Walter B. Chambers, 1925. Row stands. (Assessor 1871/1890 are wrong.)

## Models (viewer/src/landmarks/*.ts): only `Model:` facts and `sources` changed, no height changed
Footprint heights in nj_mercer are mostly `ms_ml` (machine-learned) and were not trusted over a cited figure; none of the models differed from a lidar or Overture/OSM height by more than 20 percent, so no height was corrected.
- 360 State Street: 103 m now cited (Wikipedia infobox, 31 floors); OSM says 91 (kept 103).
- Lewis Library: Daily Princetonian: four stories above grade, tower over 100 ft; 32.0 m consistent, exact figure's page not opened.
- CFC 116.7 (OSM 116), Union and New Haven Trust 73.8 (OSM 74), Kline 76.2 (OSM 77): confirmed.
- Ingalls Rink: 23 m ceiling confirmed on Wikipedia.
- Rudolph Hall: seven stories, 30+ levels; Hotel Marcel: nine stories incl. gap; these agree with the models. Heights in metres remain estimates.
- Chancellor Green: lidar roof 19.7 m vs model ridge 22 m (12 percent).
- Fine Hall: 3 + 10 floors confirmed (Wikipedia, mathematics department).
- Woolsey, Battell, Alexander, East Pyne, Jadwin Gym, Art Museum: no height on any opened page; still estimated.
Open questions for the lead: Princeton models with ms_ml footprints (Alexander 7.5 m against a 13 m eave) show the footprint height is not a reliable check.
