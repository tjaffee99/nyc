# OpenHistoricalMap buildings in the New York box

What volunteers have traced into OpenHistoricalMap (OHM) inside the map box
(-74.29, 40.47, -73.67, 40.94), normalised by `pipeline/ohm_nyc.py` as an input for "what stood before".

- Source: OpenHistoricalMap, https://www.openhistoricalmap.org/ — data **CC0 1.0**
  (https://www.openhistoricalmap.org/copyright). Read through its Overpass API,
  https://overpass-api.openhistoricalmap.org/api/interpreter, on **2026-11-10** (OHM data timestamp
  2026-11-10T07:21Z), in 80 quadtree tiles cached under `data/raw/ohm/`.
- Regenerate: `cd pipeline && ../.venv/bin/python ohm_nyc.py` (about a minute from the cache; delete
  `data/raw/ohm/` to fetch again). Checks: `.venv/bin/python data/manual/ohm/tools/check_outputs.py`.
- Every number below comes from `data/interim/ohm/stats.json`, `heaps.csv`, `named.csv`, `survivors.csv` and
  `other_summary.json`, which the stage rewrites on each run.

## Headline

| | |
|---|---|
| OHM buildings in the box | **215,215** (215,026 ways, 189 multipolygons; 36 open ways skipped) |
| ... of which a copy of today's NYC Building Footprints | 144,118 (Staten Island 141,494; South Bronx 2,624) — not history |
| ... the import of NYPL's 1854 building footprints (a fire-insurance atlas of 1854) | **61,637** (Manhattan, Battery to about 50th St) |
| ... traced by hand from named maps (Castello Plan ... Bromley 1930) | 4,405 in 53 campaigns (25 of ten buildings or more) |
| ... single buildings without a source tag / other sources | 4,212 / 843 |
| Extinct (OHM `end_date` before 2026) | **34,004** (Manhattan 32,861) |
| ... leaving out the city-import rows | 33,386 (2,456 hand-mapped + 30,930 of the 1854 import) |
| Extinct with a trustworthy end date | **9,352**; without the city-import rows **9,062** (1,685 hand-mapped + 7,377 of the 1854 import) |
| Extinct with trustworthy start **and** end | **1,586**; without the city-import rows **1,296** (912 hand-mapped + 384 of the 1854 import) |
| Extinct but an old footprint of the same outline stands today (`survivor_suspect`) | 1,079 |

The short version: OHM holds one large, real historical layer for New York — the **1854 city south of
50th Street, 61,637 footprints** — whose outlines are useful and whose dates are almost all placeholders
or bounds; a few thousand hand-traced buildings (New Amsterdam 1660, the colonial town, Midtown 1852,
the Lower East Side and downtown of 1890–1930, demolished landmarks) where most named buildings carry
researched dates; and a bulk copy of today's city footprints that adds nothing.

## Files

| file | features | what |
|---|---|---|
| `nyc_buildings.geojson` (8.9 MB) | 10,078 | every OHM building except the two bulk imports: the hand-traced maps, the single buildings, and the 618 city-import rows OHM has given an end date |
| `nyc_buildings_nypl1854.geojson` (49.9 MB) | 61,637 | the import of NYPL's 1854 building footprints, with the dates volunteers have since put on it |
| `data/interim/ohm/nyc_buildings_city_import.geojson` (127 MB, **not committed**) | 143,500 | OHM's copy of the city's Building Footprints (no end date); the project has the official file |
| `extras_water_dated.geojson` (1.4 MB) | 1,174 | by-product: OHM's dated water, island, stream, canal and pier features (see "Shorelines and water") |
| `extras_lost_structures.geojson` (0.1 MB) | 134 | by-product: named, vanished things OHM does not tag `building` (Ebbets Field, Polo Grounds, Shea Stadium, the World's Fairs, St. John's Park, burial grounds, the 1745 palisade ...) |

The brief asked for one file. The three building files have the same properties and together are exactly
one feature per OHM building; they are split because one file would be 186 MB (GitHub refuses files over
100 MB) and three quarters of it would be today's Staten Island.

### Properties (building files)

`ohm_id` (`way/123`, `relation/45` → https://www.openhistoricalmap.org/way/123), `name`,
`start_year`, `end_year` (decimal years; `end_year` null = no end date in OHM, which does **not** mean
it stands — see below), `start_raw`, `end_raw` (the tags as written), `date_quality`, `start_quality`,
`end_quality`, `levels` (`building:levels`), `height_m` (`height`), `building` (tag value), `source_tag`
(`source=… | source:name=… | source:url=…`), `wikidata`, `wikipedia`, `extinct` (`end_year` < 2026);
and, added: `campaign` (the import or normalised source the building belongs to), `map_year` (year of
the map a traced campaign was drawn from — the building stood then; 1854 for the import), `address`
(`addr:housenumber addr:street`; 61,315 of the 1854 footprints have one), `borough`, `area_m2`,
`overlap_today`, `overlap_bin`, `overlap_year_raw`, `overlap_iou`, `today`, `survivor_suspect`.

Dates: `1851` → 1851.0, `1851-05-04` → 1851.341; a decade (`185X`, `1850s`) → its middle; a range → its
middle; `~1850`, `before 1850` → 1850.0 with quality `decade`. Years before 1000 (the city import's
`start_date=0`) are treated as no date. `start_date:edtf` / `end_date:edtf` are used when the plain tag
is missing. In practice OHM's New York dates are plain years or ISO dates: no building got `decade`.

`start_quality` / `end_quality`: `dated` (a specific year or date nothing speaks against) |
`decade` | `placeholder` (a stamped value, see "Heaps") | `none`. `date_quality` is the weaker of the
two that are present. **Use the per-side fields**: a building with a stamped start and a researched
demolition date has `date_quality=placeholder` but `end_quality=dated`.

## Counts by borough

| | all | `nyc_buildings` | 1854 import | city import (interim) | extinct |
|---|---|---|---|---|---|
| Manhattan | 68,377 | 6,740 | 61,637 | – | 32,861 |
| Staten Island | 142,585 | 1,630 | – | 140,955 | 874 |
| Bronx | 2,699 | 154 | – | 2,545 | 99 |
| Brooklyn | 752 | 752 | – | – | 14 |
| Queens | 213 | 213 | – | – | 122 |
| outside the city (Hudson 312, Westchester 97, Nassau 77, Essex 54, Union 28, Bergen 16, Passaic 5) | 589 | 589 | – | – | 34 |

Borough = TIGER 2024 county of a point inside the footprint. Brooklyn and Queens are almost empty of
history in OHM: Brooklyn is 388 houses of two Sanborn 1888 volumes (Bedford–Stuyvesant, no end dates) and 291
present-day large buildings dated from Emporis; Queens is mostly the 1964 World's Fair pavilions.

## By start decade and end decade

Hand-mapped file (`nyc_buildings.geojson`), all values, then only those with quality `dated`:

```
start, all    1620:1 1630:1 1640:289 1650:10 1660:47 1670:5 1690:6 1700:254 1710:1 1720:8 1730:6 1740:11 1750:46
              1760:16 1770:3 1780:5 1790:8 1800:5 1810:7 1820:66 1830:14 1840:7 1850:1118 1860:293 1870:205 1880:620
              1890:1952 1900:489 1910:344 1920:522 1930:535 1940:269 1950:380 1960:479 1970:206 1980:201 1990:182
              2000:346 2010:587 2020:463
start, dated  1620:1 1630:1 1640:2 1650:10 1660:2 1670:5 1690:6 1700:4 1710:1 1720:8 1730:6 1740:11 1750:10 1760:6
              1770:3 1780:5 1790:8 1800:5 1810:7 1820:11 1830:14 1840:7 1850:155 1860:293 1870:181 1880:232 1890:302
              1900:478 1910:324 1920:522 1930:362 1940:247 1950:308 1960:479 1970:206 1980:201 1990:182 2000:346
              2010:518 2020:322
end, all      1640:1 1650:1 1660:1 1670:2 1690:290 1700:8 1740:1 1750:9 1760:21 1770:4 1780:8 1790:314 1810:2 1820:3
              1830:33 1840:5 1850:64 1860:3 1870:6 1880:6 1890:20 1900:54 1910:41 1920:82 1930:182 1940:62 1950:268
              1960:280 1970:123 1980:74 1990:69 2000:184 2010:694 2020:159
end, dated    as above except 1690:9 1790:10 1920:53 1950:222 2010:255
```

1854 import (`nyc_buildings_nypl1854.geojson`):

```
start, all    1790:14127 1800:16710 1810:6257 1820:2156 1830:7382 1840:13976 1850:994   (+ 28 scattered)
start, dated  1790:24 1800:24 1810:49 1820:84 1830:92 1840:125 1850:994                  (+ 28 scattered)
end, all      1850:514 1860:612 1870:334 1880:1658 1890:2620 1900:2613 1910:1034 1920:15522 1930:1178 1940:1093
              1950:492 1960:1022 1970:466 1980:368 1990:153 2000:600 2010:644 2020:6      (30,707 have no end)
end, dated    1850:142 1860:286 1870:163 1880:232 1890:311 1900:471 1910:471 1920:1339 1930:201 1940:1023
              1950:419 1960:820 1970:340 1980:283 1990:153 2000:394 2010:322 2020:6
```

The spikes are the heaps: 1640 and 1690 (Castello Plan), 1700 and 1790 (the 1728 survey), 1850 (Dripps
1852), 1890 (Sanborn sheets), 1790–1840 and 1920 (the 1854 import).

## Campaigns: where the data comes from and how far its dates can be trusted

Grouped by `source` tag (plate and volume numbers dropped so that one traced atlas is one campaign), by
the import tags, and by the last editor and edit year that Overpass reports. 215 campaigns, 33 with ten
buildings or more. The OHM website API, which holds the changeset comments and each way's first author,
answers 403 (a Cloudflare challenge) to this machine, so **who created what is not known**; "editor" below
is the last editor.

| campaign | buildings | extinct | area | editor, year | start dates | end dates |
|---|---|---|---|---|---|---|
| **NYC Building Footprints import** — `dataset=si_ny_odp_jm`, source https://data.cityofnewyork.us/Housing-Development/Building-Footprints/nqwf-w8eh | 141,494 | 539 | Staten Island | jeffmeyer, 2023 | the city's construction year (the same value as our `year_raw`, with the city's own 1920 / 1930 / 1970 heaps); 1,373 are `0` | 539 ends 2013–2020; the 2016 and 2018 heaps (249) are placeholders, 2019 and 2020 agree with rebuilt lots |
| same, with `cnstrct_yr` / `doitt_id` tags and no source | 2,624 | 79 | South Bronx (40.80–40.82 N) | DAH112 / jeffmeyer, 2018–22 | city year as `YYYY-01-01` | 79 × `2018-11-01`: a stamp |
| **NYPL building footprints of 1854**, `nypl:layer=861`, `nypl:year=1854` — NYPL's "New York City Building Footprints to 42nd Street, 1854", https://geodata.library.columbia.edu/catalog/sde-columbia-cul_nyc_nypl_1854_buildings (same extent) | 61,637 | 30,930 | Manhattan, 40.7016–40.7605 N | imported by nfgusedautoparts, 2020-06; re-dated by DAH112, 2021–22 | 60,210 placeholders / bounds, 1,420 dated — see below | 30,707 none, 23,553 placeholder, 7,377 dated — see below |
| (no source tag) | 4,212 | 584 | Manhattan 2,689, Staten Island 1,048, Hudson County 220 | DAH112, MapSpot, nfgusedautoparts | 3,689 dated: single buildings mapped one at a time (landmarks, towers, new construction) | 474 dated, incl. the 1964 World's Fair pavilions (1963–1966) and Seneca Village (–1857); 111 placeholder (2012, 2014 on the Staten Island shore) |
| Dripps 1852 | 975 | 223 | Midtown (40.750–40.766 N) | DAH112, 2022 | 963 × `1852` = the map year (stood by 1852) | 223 individual years; 752 none, of which only 23 still have their outline |
| Sanborn 1894 | 797 | 389 | Lower East Side – downtown | DAH112, 2022–23 | `1894` × 330, `1890` × 329: stamps; 138 dated | 389 dated (the `1939` group of 68 matches the rebuilt lots) |
| Sanborn-Perris 1890 (Manhattan vol. 4, 5) | 646 | 21 | Midtown (40.741–40.767 N) | Espresso95, 2026 | all `1890` = map year | 18 × `1920` stamp; rest none (258 still stand with the same outline) |
| EMPORIS | 492 | 12 | Brooklyn 291, Manhattan 108, Hudson County 73 | MrMap, 2021 | per-building completion years of present-day large buildings | – |
| Sanborn 1888 (vol. 5, 9) | 388 | 0 | Brooklyn (Bedford–Stuyvesant) | hdevine825, 2024 | all `1888` = map year | none |
| **Castello Plan**, Adams–Stokes redraft (1916) of New Amsterdam in 1660, https://mapwarper.net/maps/4625 | 290 | 290 | below Wall Street | – | `1640` × 209, `1643` × 78: stamps; 3 dated | `1699` × 281: stamp; 9 dated |
| Survey of Manhattan 1728, https://mapwarper.net/maps/49065 | 261 | 261 | south of City Hall (40.703–40.711 N) | – | `1700` × 250: stamp; 11 dated | `1795` × 214: stamp; 47 dated (29 × Great Fire of 1835) |
| Bromley 1902 | 205 | 198 | Lower East Side – downtown | DAH112 | `1890` × 121: stamp; 84 dated | 198 individual years |
| Bromley 1930 (+ 4 mapwarper sheets of the 1930 Land Book, 119 more) | 175 | 123 | Manhattan | DAH112 | individual years | individual years; one sheet (mapwarper 45035) is stamped `1956` × 46 |
| Sanborn-Perris 1894 (vol. 1, pl. 21–22) | 100 | 0 | SoHo | Espresso95, 2026 | all `1894` | none; all 100 still stand |
| Local knowledge | 91 | 12 | Nassau County, Queens | FlowerHillPerson | individual | individual |
| Grim, *Part of New York in 1742*, https://mapwarper.net/maps/11641 | 55 | 55 | City Hall Park – Collect | – | `1664` × 45: stamp | `1795` × 38: stamp; 17 dated |
| Maerschalck, *Plan of the City of New York* 1755, https://mapwarper.net/maps/57378 | 41 | 41 | – | – | `1755` × 36: map year | `1795` × 36: stamp |
| *NYC 1776*, https://mapwarper.net/maps/15936 | 17 | 17 | – | – | `1760` × 10: stamp | `1795` × 16: stamp |
| Sanborn sheets outside the city: Yonkers 1957 (65), Elizabeth 1951 (27), New Rochelle 1911 (20), Hoboken 1891 (15); Queens 1943 (22), Brooklyn 1915 (10) | 159 | 0 | – | MrMap, 2021 | the map year | none |

("–" under editor: the last edit is a 2026 tag clean-up bot, so the mapper is not visible.)

Trust, in one line each:

- **City-footprint imports**: not history; ignore them. They coincide with our footprints (141,650 of
  143,500 have the same outline). The 618 with an end date are in `nyc_buildings.geojson` — possibly useful
  as "demolished 2013–2020", unverified.
- **1854 import**: the outlines are the valuable part and are **not** in the project's own NYPL download
  (`data/raw/nypl/building-inspector.objects.ndjson` has layers 859 = 1857, 860 = 1855, 1138, 1145, 1148 …
  but no 861; of 6,000 sampled OHM footprints 0.3 % repeat a polygon of that file, 43 % coincide loosely
  with one, 12 % touch none). The ways name no atlas; the catalogue record says the footprints were made by
  NYPL "from historical Sanborn fire insurance maps" — for 1854 that should be William Perris's *Maps of
  the City of New York* (1852–54), which was not verified here. Median outline 69 m². Dates: see next section.
- **Hand-traced colonial maps** (Castello, 1728, Grim, Maerschalck, 1776; 664 buildings): good outlines
  for a town that otherwise has none; every date is a stamp except on some 80 named buildings. What is
  certain is `map_year`: the building stood then.
- **Dripps 1852, Sanborn 1888 / 1890 / 1894, Bromley 1902**: start = the map year or a round "about 1890";
  use `map_year` as "standing by". Their end dates, where present, are individual and mostly agree with
  what stands there now.
- **Bromley 1930, the single buildings without a source, EMPORIS, Local knowledge**: per-building dates,
  the best in the set. Named buildings usually carry `wikidata` / `wikipedia` (315 buildings have a
  Wikidata id).

### The 1854 import in detail

The import set `start_date=1796-02-29` and `end_date=1920-02-29` on every way (`fixme: start_date,
end_date - both added for rendering....`); an Overpass query at the state of 2020-08-01 for one box of the
Lower East Side returns 6,068 buildings with exactly those two values, 1,120 with no dates, and nothing else. Everything else was put on afterwards, almost all by one
mapper in 2021–22:

- **Start** — 12,969 still carry the sentinel. The rest were re-stamped area by area: `1809` 16,389,
  `1847` 13,112, `1837` 6,765, `1818` 5,830, `1825` 1,947, `1798` 862, `1849` 739, `1836` 460, `1812` 378,
  `1801` 297, `1796` 272. The values look like "one year after an earlier map that does not show the
  block" — the ways with `1853` say so in a note ("not on the 1852 Dripps map", 835 of 867) — but no
  other value is documented. `1836` covers the district burned on 16–17 December 1835. All are
  **placeholders** (at best lower bounds), except `1853` (kept `dated`: built between the Dripps map of
  1852 and the atlas of 1854). 1,420 starts are `dated`: those 867, the 51 × `1854`, and about 500
  individually researched ones (churches, hotels, named buildings).
- **End** — 14,114 still carry the sentinel; **30,707 have no end date at all** (the mapper removed the
  sentinel). The other 16,816 have a year:
  - 40 year-values (5,914 buildings: `1946` 556, `1926` 376, `1929` 370, `1961` 329, `1948` 308, `1959`
    295, `1909` 284 …) are confirmed on the ground: where a footprint with a recorded year stands on the
    spot today, at least 70 % of them were built within [end − 1, end + 5]. These read as "gone by the
    time the present building went up" (the `1946` group lies on the Peter Cooper Village site; others
    are superblocks of the 1940s–60s and single lots). Kept `dated` — an upper bound that holds, not a
    demolition record.
  - 51 year-values (9,439 buildings: `1889` 1,006, `1904` 821, `1893` 772, `1896` 567, `1930` 452, `1902`
    376, `1894` 334, `1908` 317 …) do not match what was built there (for `1889` and `1893`, 97 % of the
    present buildings are more than three years later, median 31 and 22 years). They look like atlas
    years ("gone by the next atlas"); 414 ways carry a `source:end_date`, 252 of them an NYPL Digital
    Collections item. **Placeholder.**
  - 1,463 carry a year shared by 50 buildings or fewer: `dated`.
- **No end date does not mean standing.** Of the 30,707 without one, 21,552 are built over by a
  different outline, 4,242 are open ground, and only 4,913 coincide with a footprint standing today.

## Heaps

Rule (`find_heaps` in the stage): an exact `start_date` or `end_date` value shared by more than 50
buildings of one campaign, or by at least 10 buildings and half of the campaign, is a placeholder. Not
flagged: the city imports' start years (one assessor year per building); named or Wikidata-tagged
buildings of the no-source group; and heaps that something vouches for —

| verdict | heaps | buildings | meaning |
|---|---|---|---|
| `placeholder` | 105 | 88,507 | stamped; nothing vouches for it |
| `bound` | 3 | 571 | a real bound stamped on many (1836 after the Great Fire; 2012 and 2014 on the Staten Island shore, probably Hurricane Sandy and the buy-outs — read from the location only, not verified); still `placeholder` |
| `record` | 105 | 141,812 | city-import start years; `dated`, but they are our own `year_raw` |
| `successor_consistent` | 43 | 6,114 | end heaps the present buildings confirm (above); `dated` |
| `record_consistent` | 5 | 518 | start heaps where ≥ 70 % of the same-outline footprints today carry that year ± 1 (new construction of 2019–2021, `1900`, `1854`); `dated` |
| `documented` | 1 | 867 | `1853` on the 1854 import (note on the ways); `dated` |

One stamp below the threshold is set by hand: `1825` on the 55 Seneca Village houses (the settlement's
founding year; their end, 1857, is the real clearance for Central Park). The full list is
`data/interim/ohm/heaps.csv`; the largest outside the two imports:

`1852` × 963 Dripps · `1890` × 618 Sanborn-Perris 1890 · `1888` × 388 Sanborn 1888 · `1894` × 330 and
`1890` × 329 Sanborn 1894 · end `1699` × 281, start `1640` × 209 and `1643` × 78 Castello ·
start `1700` × 250, end `1795` × 214 Survey 1728 · `1890` × 121 Bromley 1902 · `1894` × 100
Sanborn-Perris 1894 · `1890` × 80 no source · `2022` × 141 no source (64 % agree with the city, under
the 70 % bar).

The `1795` end on the four colonial maps (304 buildings) and `1699` on the Castello Plan read as the
mappers' "until the next layer": `1700` is the start stamp of the 1728 survey and `1796` the start
sentinel of the 1854 import.

## New Amsterdam and the colonial town

Present. **290 buildings of the Castello Plan** (the 1916 Adams–Stokes redraft, georeferenced at
https://mapwarper.net/maps/4625; median 30 m²), all `extinct`, all inside -74.015, 40.703 – -74.008, 40.709.
Dates are stamps (1640 / 1643 → 1699); the fact is `map_year=1660`. Named with their own dates: Stadt Huys
(1653–1699), De Old Kirke (1633–1643), Lovelace Tavern (1670–1706). Fort Amsterdam is four relations
without a source (Fort Amsterdam 1626–1664, Fort James 1664–1673 and 1674–1691, Fort George 1783–1788, all
the same 2,800 m² outline). Outside the building layer OHM also has, for the same town: the canals (Heere
Graft 1624–1664, Prinzen Gracht, later Broad Canal 1665–1676), 10 streets from the Castello Plan and 35 from
a *New-York Historical Society Quarterly* article, the Governor's Garden, the Schaape-Waytie, the old
graveyard, Noten Eylandt (1624–1699) — the areas are in `extras_lost_structures.geojson` and
`extras_water_dated.geojson`.

Then: 261 buildings of a **1728 survey** (OHM names it only "Survey of Manhattan 1728"; Trinity Church
1698–1776, Federal Hall 1703–1813, the sugar houses), 55 of **Grim's 1742** plan, 41 of **Maerschalck
1755**, 17 of a **1776** map, the Bridewell (1775–1838), New Gaol (1757–1829), King's College (1760–1776),
Middle Dutch Church, Government House (1790–1815).

## Famous lost buildings found

Dates as OHM has them (not re-verified here); all with quality `dated` unless noted. `today` = what the
official footprints show on the spot.

| building | OHM id | start → end | note |
|---|---|---|---|
| Pennsylvania Station | way/198645203 | 1910 → 1963 | 30,298 m², Wikidata Q14707174; 1963 is when demolition began (from memory, not checked here) |
| Singer Building | way/198552870 | 1900 → 1968 | start is OHM's; the tower is usually dated 1908 (from memory, not checked here) |
| City Investing Building | way/198552871 | 1908 → 1968 | |
| Crystal Palace | way/198109868 | 1853 → 1858-10-05 | 12,348 m², from the 1854 atlas; today open (Bryant Park) |
| Croton Distributing Reservoir | relation/2689733 | 1842 → 1900 | |
| "Hippodrome" at Madison Square (-73.9899, 40.7421; Franconi's) | way/198119304 | 1853 → 1856 | from the 1854 atlas; the 1905 Hippodrome on Sixth Avenue is **not** in OHM |
| Metropolitan Opera House (old; OHM spells it "Metropoliatan") | way/198759005 | 1883 → 1967 | Q6825160 |
| Madison Square Garden III ("New Madison Square Garden") | way/198759004 | 1925 → 1969 | Garden I and II are **not** in OHM |
| World Trade Center 1, 2, 4, 5, 6, 7, Marriott | way/198201501, 198201503, 198590237, 198590239, 198590240, 198590241, 201988026 | 1970-12-23 / 1971-07-19 / … → 2001-09-11 | with levels and heights (417 m, 415.1 m) |
| Hudson Terminal (north, south) | way/198650813, 198650814 | 1908 → 1968, 1972 | |
| New York World Building | way/198589815 | 1890-12-10 → 1955 | |
| Tribune Building | way/198589816 | 1875 → 1966 | |
| City Hall Post Office | way/198589818 | 1880 → 1939 | Q5123209 |
| Equitable Life Building | way/198592110 | 1870-05-01 → 1912-01-09 | Q3272426 |
| Gillender Building | way/198549671 | 1897 → 1910 | |
| Manhattan Life Insurance Building | way/198753431 | 1894 → 1964 | |
| Produce Exchange | way/198782080 | 1861 → 1957 | OHM's start looks like the earlier exchange, not the 1880s building (from memory, not checked here) |
| Astor House | way/198103647, 198753439 | 1836 → 1913, 1914 → 1926 | first is on the 1854 import with placeholder quality |
| Hotel Astor / Astor Theatre | way/198777235, 198777252 | 1904 → 1967 / 1906 → 1982 | |
| Fifth Avenue Hotel | way/198744459 | 1859 → 1908 | |
| St. Nicholas Hotel, Metropolitan Hotel | way/198157364, 198153114 | 1853 → 1878, 1852-09-01 → 1895 | |
| New York Biltmore Hotel | way/198744666 | 1913 → 1981 | survivor suspect: the frame stands (rebuilt as an office building) |
| Grand Central Palace | way/198777075 | 1911 → 1964 | |
| Barnum's Museum / Scudder's American Museum | way/198107533, relation/2697423 | 1841 → 1865-07-13 / 1830 → 1840 | |
| Park Theatre, Bowery Theatre, Wallack's | way/198589840, 198158388, 198157410 | 1798-01 → 1848-12-16, 1845-08-04 → 1929-06-05, 1850-12-23 → 1869 | |
| Ziegfeld Theatre; Morosco, Bijou, Fulton, Gaiety, Klaw theatres | way/198777204 … | 1930 (stamp) → 1967; → 1982 | |
| Tontine Coffee House | way/198102666 | 1793 → 1855 | end is in a placeholder group |
| Columbia College / King's College | way/198103779, relation/2697316, relation/2697337 | 1784 → 1857, 1857 → 1882, 1760 → 1776 | |
| New York Hospital | way/198160478 | 1791 → 1873 | |
| The Tombs (Halls of Justice; second Tombs) | way/198158994, 198785304 | 1838 → 1901, 1902 → 1940 | |
| Tammany Hall (first) | way/198105174 | 1811 → 1915 | |
| Washington Market, Fulton Market | way/199408682, 198766154 | 1880 → 1967, 1888 → 1950 | |
| Castle Garden (as a hall) | relation/2694062 | 1824 → 1854 | OHM convention: a new feature per use; the fort stands |
| 1964 World's Fair pavilions | 105 buildings | 1963 → 1966 | Queens; plus Singer Bowl 1963 → 1977 |
| Seneca Village | 57 buildings | 1825 (stamp) → 1857 | incl. African Union Church |

Not buildings in OHM, so in `extras_lost_structures.geojson`: **Ebbets Field** (relation, 1913–1960),
**Polo Grounds** (1890–1964), **Shea Stadium** (1964–2009), Hilltop Park (1903–1913), the 1939 and 1964
World's Fair grounds, St. John's Park (1827–1866), Radio Row (1921–1967), the African Burial Ground
(1703–1794), Reservoir Square, Mulberry Bend Park, the 1745 palisade and the 1776 fortifications.

Looked for and **not found**: the 1905 Hippodrome, Madison Square Garden I and II, the first
Waldorf-Astoria, the Roxy Theatre, the Lenox Library, St. John's Chapel, old Yankee Stadium, Steeplechase /
Luna Park / Dreamland, the Latting Observatory, the Vanderbilt and Schwab houses.

## Overlap with today's official footprints

For every building in the five boroughs (589 outside have `today=no_data`): `overlap_today` = share of its
area under footprints of `data/interim/nyc_footprints_raw.parquet`; `overlap_bin`, `overlap_year_raw`,
`overlap_iou` = the footprint with the largest overlap. `today` = `same_outline` (that footprint has IoU
≥ 0.5, or covers ≥ 70 % of the OHM building with IoU ≥ 0.35) | `built_over` (≥ 30 % covered, different
outline) | `open`. Checked independently on 300 extinct buildings (UTM areas against the union of the
footprints): largest difference 0.009.

| extinct buildings | open | built over | same outline | survivor suspect |
|---|---|---|---|---|
| hand-mapped file (3,074) | 1,404 | 1,293 | 343 | 212 |
| 1854 import (30,930) | 12,615 | 16,732 | 1,583 | 867 |

`survivor_suspect` (1,079) = extinct in OHM, same outline today, and the standing footprint's `year_raw` is
earlier than OHM's end year. They are of three kinds:

- 776 on the 1854 import still carry the sentinel end `1920-02-29`: survivors of the 1854 city that nobody
  has looked at (the city's year for them is usually a placeholder itself — 1900, 1910, 1920).
- OHM's habit of ending a feature when the building changes name or use and starting another on the same
  outline: New York Biltmore Hotel 1913–1981 (BIN 1035360, 1914), Sony Building 1983–2020 (BIN 1035769),
  the Queens Museum as "New York City Pavilion" 1939–1940 and 1964–1965 and "United Nations General
  Assembly" 1946–1950 (BIN 4458851), Asch Building 1901–1929 (BIN 1008823), Engine Company 31 1895–1972.
- city-import rows ended 2013–2020 whose footprint is still in the city file (125).

The list is `data/interim/ohm/survivors.csv`. For "what stood before", a survivor suspect must not be drawn
as a vanished predecessor.

## What else OHM has in the box (not imported; counts and tags only)

55,275 other elements: 37,725 ways, 1,851 relations, 15,699 tagged nodes with a place or a date.
Detail in `data/interim/ohm/other_summary.json`.

### Shorelines and water — for `data/manual/natural/` and `fill_zones.csv`

**OHM has no systematic historic shoreline for New York**: of 326 `natural=coastline` ways, 317 are the
undated modern coast (PGS / Bing / Yahoo imports) and 9 are dated island outlines. **But it has a dozen
dated water polygons that are pieces of older waterfront**, plus ponds, marshes and streams — all with
geometry in `extras_water_dated.geojson`:

| OHM id | name | valid | where |
|---|---|---|---|
| relation/2691396 | Hudson River | 1610 → 1848 | the Hudson waterfront, Battery to about W 20th St (-74.020, 40.705 – -74.008, 40.745) |
| relation/2691393 | East River 1843 | → 1848 | the East River waterfront of lower Manhattan (-74.010, 40.700 – -73.995, 40.710) |
| relation/2691390, 2691391, 2691392 | East River 1843 | 1610 → 1848 | further up the East River; 2691390 lies off the Lower East Side (40.713–40.727 N) |
| relation/2694063 | Coenties Slip | → 1848 | the open slip |
| relation/2693970 | Hudson River | → 1975 | -74.019, 40.705 – -74.013, 40.719: matches the Battery Park City fill |
| relation/2389640 | East River | 1832-02-29 → | mouth of the East River / Upper Bay |
| 119 ways | (piers) | 1800 → 1848, a stamp | the piers and slips that go with the "1843" water |
| way/198744892 | Turtle Bay | → 1920 | the cove at E 45th–48th St |
| relation/2697000, 2697001 | Spuyten Duyvil Creek | 1621 → 1913, 1621 → 1894 | the old creek loops |
| relation/2696999, 2697002 | Harlem River Ship Canal | 1895 → 1935, 1936 → | |
| way/201395606, relation/2691577, 2871177 | Flushing Creek, Meadow Lake | → 1936; 1937 → | the World's Fair reshaping |
| way/198570750, 198570753, 198570752 | Collect Pond, Little Collect Pond, outlet to the North River | → 1811, → 1811, → 1810 | from https://mapwarper.net/maps/54573 |
| way/198594825, 198587973 | Lispenard's Meadow, Salt Meadows (Lower East Side) | → 1800, → 1808 | wetlands |
| way/198590774, 198640127 | Minetta Creek, Kalch Hoek stream | → 1820, → 1800 | |
| way/198716390, 202432562, 199373949, 27459262 | Noten Eylandt 1624–1699; Bedloe's Island 1673–1956; Ellis Island (original islet → 1935, enlarged 1935 →) | | island outlines; Governors Island after the fill is relation/2389631 (1913 →) |
| way/198588035, 198588036 | West Dock, East Dock (the Great Dock) | 1700 → 1745 | from the 1728 survey |
| 822 ways + 53 ponds | (streams and ponds, unnamed) | → `1610`, a stamp for "before settlement" | the **Mannahatta Project** streams (`import=Wilikia_streams_jm`, from https://web.archive.org/web/20211102022334/https://welikia.org/wp-content/uploads/mannahatta_streams.zip); the ways carry an attribution to the Wildlife Conservation Society — OHM publishes them as CC0, the original's own terms were not checked |

The "1843" water and piers carry no source tag; the name suggests a map of 1843. Dates on these are OHM's
and unverified.

### Railways — for the transit agent

4,116 ways and 1,887 station / stop nodes; all but one element have a start date and **these are opening
dates by segment, not stamps** (`1904-10-27` first subway, `1915-06-22`, `1932-09-10` …). `railway=subway`
2,852 ways, `rail` 1,129, `light_rail` 96, `tram` 17 (streetcars are almost absent). 1,245 ways start
before 1900. **264 ways have an end date**, among them the elevated lines: IRT Ninth Avenue Line (→
1940-06-11), Sixth Avenue (→ 1938-12-04), Second Avenue (→ 1940-06-11 / 1942-06-13), Third Avenue (→
1955-05-12; Bronx → 1973-04-29), City Hall spur, "NYC Elevated Railway" 1878 →; the New York and Harlem
Railroad on Fourth Avenue and the Bowery (1833-06-10 / 1834-05-09 → 1912), New York Central yards (1867 →
1927), Hudson Terminal tubes (1909 → 1971), CNJ Communipaw Terminal (1889 → 1967-04-30), the LIRR Rockaway
Beach Branch (→ 1962), the Williamsburg Bridge trolley. Each elevated line has only 3–7 ended ways.

### Roads

28,730 ways. 16,822 belong to the Staten Island import and 11,236 of those are stamped `1875` (not dates).
Outside it: 7,624 ways without a source, 1,341 "Local knowledge", 725 from
an *Atlas of the entire city of Brooklyn*, 93 from https://mapwarper.net/maps/4623. 240 ways start in the
1600s and 1,669 in the 1700s (1,356 of them Staten Island stamps `1703`, `1704`, `1701`, `1781`). 1,891 have
an end date (`1966` × 89, `2002` × 72, `1958` × 62, `2009` × 58 …), among them the **West Side Elevated Highway** with
opening dates by section (1930-11-13 … 1948-11-29) and closing dates (1973-12-16 … 1982-06-23). 3,393 ways
are tagged `bridge`, 1,757 `tunnel`.

### Land use, places, boundaries, the rest

- `landuse` 392 (construction 105, residential 71, cemetery 40, farmland 40, meadow 28 …; 228 ended):
  colonial farms and commons from the 1742 and 1776 maps, burial grounds, fairgrounds. `leisure` 573
  (parks 421, with opening years on 310).
- `place` 395 (193 nodes): towns, villages, hamlets and counties with dates, 135 of them from the Newberry
  *Atlas of Historical County Boundaries*. `boundary` 1,132 relations, 958 with an end date — county and
  town lines through time and **157 ward boundaries** (Ward 5 1834–1840, 1840–1855 …; 38 cite the NYPL
  NYC Space/Time Directory).
- `amenity` 787, `shop` 401, `tourism` 142: point businesses from one NYPL Digital Collections item of
  1941, the Bromley 1930 / 1955 land books and Sanborn 1905 (start = end = the map year). `man_made` 185 (137
  piers), `aeroway` 38 (Idlewild / JFK runways and terminals with dates), `building:part` 40 (the World
  Trade Center).

## Using it

- A predecessor layer for Manhattan south of about 50th Street in 1854: `nyc_buildings_nypl1854.geojson`, with
  `map_year` as "standing in 1854". Start: unknown before 1854 (the stamps are lower bounds at best) —
  `estimated`. End: `end_year` where `end_quality == "dated"` (7,377, an upper bound); otherwise bounded by
  `overlap_year_raw` when `today == "built_over"`, and unknown when `open`. Drop or hand over to the modern
  data the 6,496 with `today == "same_outline"`.
- The project's own 1857 layer (859) covers the same ground three years later; 43 % of the 1854 outlines
  coincide with one of the project's NYPL polygons. Chain them rather than stack them.
- `nyc_buildings.geojson`: filter `campaign` not starting with "NYC Building Footprints import" (9,460
  left). Its 2,456 extinct buildings are the documented layer (landmarks, colonial town, clearances): 1,685
  with a trustworthy end, 912 with both dates trustworthy, 87 survivor suspects; today 1,098 of the sites
  are open, 1,137 built over, 187 the same outline.
- Different campaigns redraw the same building (Castello / 1728 / Grim; Dripps 1852 / the 1854 import;
  Sanborn 1894 / Bromley 1902): overlaps in space **and** time between OHM features were not removed or
  counted.

## Not checked, weak spots

- No OHM date was verified against an outside source. "Dated" means "specific and not a detected stamp".
- Changeset comments and first authors could not be read (403 from the OHM website API), so the reading of
  the 1854 import's start stamps as "one year after an earlier map" rests on the `1853` notes alone.
- `successor_consistent` and `survivor_suspect` lean on the city's `year_raw`, which has its own heaps.
- The heap rule misses stamps on fewer than 10 buildings and may flag a real common year in a small
  campaign; `2022` × 141 (no source) is probably real.
- Two OHM buildings have start = end (way/198522406, relation/2798367); they are passed through.
- Identity of "Survey of Manhattan 1728" and of the "1843" waterfront source: as tagged in OHM, not traced
  back to a catalogued map.
