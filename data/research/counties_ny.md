# The New York counties next to the city: footprints with the assessor's construction year

Westchester (36119), Nassau (36059), Rockland (36087). Stage: `pipeline/counties_ny.py`
(downloads cached under `data/raw/counties_ny/`, outputs under `data/interim/counties/`).
Everything below was fetched and built on **2026-11-10**; the numbers in the tables are
written from the built files by the stage's reports, not typed.

**In one paragraph.** New York's assessors' inventories reach the public only through the
State's "NYS Tax Parcels Public" layer, and only for the counties that agreed to share and the
municipalities whose assessor files the inventory with the State. **Rockland: yes** — every
municipality, 100 % of the homes carry a year. **Westchester: in part** — 15 of its 43
municipalities are dated (Yonkers, White Plains, Scarsdale, Harrison, the Sound shore from
Pelham to Port Chester, New Castle, Somers, Pound Ridge), 6 partly, and 22 have no year at
all (Mount Vernon, Greenburgh and its six villages, Eastchester, Ossining, Cortlandt,
Peekskill, Bedford, Lewisboro, North Castle, North Salem …). **Nassau: no** — no public year
built exists in bulk; it was not built. The years are good for 20th-century houses and poor
for landmarks, public buildings and anything before 1900.

## Sources

| id | What | From (URL) | Licence / terms | Date |
|---|---|---|---|---|
| `nys_parcels_2025` | NYS Tax Parcels Public: parcel outlines from the counties joined by the State to the 2025 assessment rolls (`YR_BLT`, `PROP_CLASS`, `MUNI_NAME`, `CITYTOWN_NAME`, `SWIS`, `PRINT_KEY` …). 38 counties, among them Westchester (258,145 parcels) and Rockland (92,620); not Nassau | NYS ITS Geospatial Services with the Office of Real Property Tax Services and the contributing counties — https://gis.ny.gov/parcels ; https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Tax_Parcels_Public/FeatureServer/1 | "This map service is available to the public"; the counties "specifically authorized Geospatial Services to share their GIS tax parcel data with the public"; provided as is, no warranty (service description, saved in `data/raw/counties_ny/meta/parcels_service.json`). No licence text beyond that. Owner and mailing fields exist in the layer and were **not** downloaded | Published May 2026 (roll year 2025; parcel geometry 2024-25); fetched 2026-11-10 |
| `overture` | Every Overture footprint of the wider box (the lead's extract `data/raw/overture/2026-10-21.0/region_building.parquet`): outline, `height`, `num_floors`, `name` | Overture Maps buildings theme, release 2026-10-21.0 — https://overturemaps.org | OpenStreetMap parts ODbL; Microsoft ML Buildings CDLA-Permissive-2.0; Esri Community Maps CC BY 4.0 | release 2026-10-21 |
| `nys_bf` | NYS Building Footprints: the counties' planimetric outlines collected for NYSERDA (Westchester County GIS 2013: 273,325; Rockland County GIS Division 2007: 112,557) plus Microsoft outlines the State added. No heights, no years | NYS ITS Geospatial Services — https://gisservices.its.ny.gov/arcgis/rest/services/BuildingFootprints/FeatureServer/2 | Public service, credit "NYSERDA; CIESIN; NYS ITS Geospatial Services; Microsoft; Open Data"; no licence text | source dates 2007 / 2013; fetched 2026-11-10 |
| `cris` | CRIS "Building USN Points": the buildings the State Historic Preservation Office has inventoried (number, name, address, eligibility). **No construction-date field in the public layer** | NYS Office of Parks, Recreation and Historic Preservation, Division for Historic Preservation — https://cris.parks.ny.gov ; https://services.arcgis.com/1xFZPtKn1wKC6POA/arcgis/rest/services/Building_USN_Points/FeatureServer/2 | Public service ("service refreshed daily"); no licence text | fetched 2026-11-10 |
| `nys_civil` | NYS Civil Boundaries (cities, towns, villages) | NYS ITS Geospatial Services — https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Civil_Boundaries/FeatureServer (layers 6, 7) | Public service | Published March 2026; fetched 2026-11-10 |
| `tiger` | County outlines 2024 (`data/raw/tiger/tl_2024_us_county.zip`) | US Census Bureau | Public domain | 2024 |

Checked and **not used**:

- **Westchester County GIS** (https://giswww.westchestergov.com/arcgis/rest/services):
  `DataHub_TaxParcels` is a copy of the State's layer (same vintage, same gaps);
  `MunicipalTaxParcels` (one layer per municipality, 43) carries owner, address and property
  class but no year built in any of its layers (all field lists read). `Parcel_Identification`
  does carry `YR_BLT`, `STORIES_NUMBER`, `BUILDING_SQFT` (288,704 parcels in five layers; in
  the residential layer 127,674 of 203,337 have a year) — but it is the HIFLD / LightBox
  national parcel file of 2020 ("data post-processed and provided by LightBox", downloaded by
  the county from HIFLD), a licensed product, not the county's to give away: **not used, only
  counted**. By postal city it would fill Ossining (6,296 of 7,418 residential parcels dated)
  and Greenburgh (Hartsdale 2,027 of 2,613) but not Mount Vernon (66 of 8,903) or Peekskill
  (1 of 5,691).
- **An older vintage of the State's layer** (NYSGIS_GPO "Westchester County Parcels" on ArcGIS
  Online): same 2025 roll, identical counts per municipality.
- **Municipal layers on ArcGIS Online** for the 22 empty municipalities (searched by name,
  46 services inspected): none with a year built. The towns' own lookups (Image Mate Online
  and similar) are one parcel at a time: not harvested.
- **NYS ORPTS "Property Assessment Data from Local Assessment Rolls"** (data.ny.gov
  `7vem-aaz7`): no year-built column (column list read). ORPTS inventory files by municipality
  were not found published; the ORPTS sales files were not checked.
- **CRIS** has the construction date on each building's record page, not in the public
  layer; no bulk access was found.
- Modelled years exist — HISDAC-US (Zillow-derived built-up records) and the census "year
  structure built" by block group — and were **not used**.

## Method (the same for every county)

1. Footprints: Overture outlines whose inner point lies in the TIGER county outline, 12 m2 or
   more. Where Overture has no building, the State's outline is added (rule: Overture's
   outlines cover less than 10 % and less than 5 m2 of it); `footprint_src` says which.
2. Footprint -> the parcel containing its centre (the centroid, or an inner point if the
   centroid falls outside the outline) -> that parcel's `YR_BLT`. Stacked parcels
   (condominium units drawn on one outline, 20,305 records in Westchester) count as one
   parcel with the most frequent year of the stack. If parcels overlap, the smallest one with
   a year wins.
3. The largest outline on a parcel is its main building; the others get the same year and
   `secondary` = true.
4. Years outside 1650-2026 are dropped (none occurred). Nothing is spread, imputed or
   refined: `year_raw` is the assessor's year, NaN where the parcel has none.
5. `heap`: `nyc_buildings.find_heaps` (more than three times the median of the non-round
   neighbouring years), run on main buildings **per assessing unit** (the town or city: the
   assessor) and separately for the residential records (classes 200-299; at least 40
   buildings or 0.2 %) and everything else (at least 10 or 1 %), because the two inventories
   are kept differently: commercial and exempt years are mostly round estimates. One
   addition: a flagged year after 1945 whose buildings sit in a few 400 m cells (under half
   the cells an equal draw from the same era occupies, 30 buildings or more) is a subdivision
   or a condominium complex finished that year and is **not** flagged.
6. `year_hist`: the year an inventory name of the State Historic Preservation Office ends
   with ("Residence (1929)", "PROCTOR'S THEATER, 1913"), where the inventory point lies
   inside the footprint, the name holds exactly one year and no word of demolition or
   alteration. Names with "ca." go to `year_hist_ca` (the surveyor's estimate), not to
   `year_hist`. That is all the public layer offers.
7. `name`: Overture's, else the inventory's unless it only describes ("residential bldg").
8. `use` from the three-digit property class: 210, 215 -> 1; other 200s and 411 (apartments)
   -> 2; 460-465 -> 4; other 400s -> 3; 600s -> 6; 700s -> 5; 100s, 300s, 500s, 800s, 900s ->
   7; no parcel -> 0.

**Overture or the State's footprints?** Compared on Scarsdale and its edges (a 2.5 x 2.2 km
window) and on New City in Rockland (2.9 x 2.8 km):

| | Scarsdale window | New City window |
|---|---|---|
| Outlines, State / Overture | 4,478 / 4,522 | 3,342 / 2,968 |
| State outlines with no Overture outline | 38 | 561 |
| Overture outlines with no State outline | 71 | 139 |
| Overture's own source | OpenStreetMap 3,277, Esri 1,200, Microsoft 45 | Microsoft 2,642, OpenStreetMap 326 |
| Heights | State none; Overture 89 % | State none; Overture 99 % |

In Westchester the two are the same buildings (98 % match at IoU > 0.5, median IoU 0.80; the
State's outlines are slightly more detailed, 10.4 against 8.9 vertices): **Overture is
better** — current, with heights. In Rockland Overture is mostly Microsoft's machine-drawn
outlines and misses buildings (6.1 % of the dated residential parcels were touched by no
Overture outline); the State's 2007 planimetrics are **more complete and crisper**
but 19 years old and without heights. Hence Overture first, the State's outlines in the gaps.

## The counties


### Westchester (36119)

**Is it in the public layer?** Yes — but `YR_BLT` is filled only where the municipality's
assessor files its inventory with the State. Counted on the service itself (2026-11-10):
119,031 of 258,145 parcels carry a year (46 %); of the residential parcels (classes 2xx)
110,166 of 190,972 (58 %). Per municipality it is all or nothing, with a few in between —
see the table. Nothing else public was found for the empty ones (see "Checked and not
used").


### Westchester: the built file (`data/interim/counties/ny_westchester.parquet`)

- Footprints: 281,474 Overture outlines have their inner point in the county; 3,072 under 12 m2 dropped; 4,323 outlines of the State's layer added where Overture has none (the State's layer holds 273,270 of 12 m2 or more) -> **282,725 rows**.
- Outline sources: `overture:osm` 231,333, `overture:esri` 42,639, `overture:microsoft` 4,430, `nys_bf_2013` 3,517, `nys_bf_microsoft` 806.
- With a year: **143,331 (50.7 %)**; main buildings 109,762 of 200,899 (54.6 %); secondary (not the largest outline of their parcel) 81,826; outside every parcel 537.
- Single-family homes (class 210 / 215), main buildings: 88,773 of 154,353 dated (57.5 %). Commercial, industrial, civic and other main buildings: 3,803 of 15,015 dated (25 %).
- On heap years: **18,307** footprints (13 % of the dated); main buildings 11,856 (11 %).
- With a height: **241,639 (85 %)** (Overture's `height`; 528 of them are 1.5 m or less); with a floor count 906; named 7,374; with an inventory year 133 (+ 133 'circa').
- Years run 1700-2025; geometry: 0 invalid.

Per municipality (`muni` = the village, the town outside its villages, or the city; the assessing unit is the town or city — for a village in two towns, the one with most of it). "Main homes dated" = share of the main buildings on residential parcels (classes 200-299) that carry a year = column `muni_year_share`.

| Municipality | Assessing unit | Footprints | With a year | Share | Main homes dated | On heap years | With a height |
|---|---|---:|---:|---:|---:|---:|---:|
| (no parcel within 300 m) |  | 7 | 0 | 0 % | 0 % | 0 | 5 |
| Ardsley | Greenburgh | 1,672 | 0 | 0 % | 0 % | 0 | 1,637 |
| Bedford | Bedford | 9,223 | 954 | 10 % | 12 % | 0 | 8,860 |
| Briarcliff Manor | Ossining | 2,900 | 238 | 8 % | 9 % | 44 | 2,818 |
| Bronxville | Eastchester | 1,528 | 75 | 5 % | 1 % | 0 | 1,120 |
| Buchanan | Cortlandt | 1,261 | 25 | 2 % | 3 % | 0 | 1,213 |
| Cortlandt | Cortlandt | 13,429 | 468 | 4 % | 3 % | 0 | 12,980 |
| Croton-on-Hudson | Cortlandt | 3,634 | 254 | 7 % | 9 % | 0 | 3,496 |
| Dobbs Ferry | Greenburgh | 3,099 | 0 | 0 % | 0 % | 0 | 2,951 |
| Eastchester | Eastchester | 6,063 | 86 | 1 % | 1 % | 0 | 5,022 |
| Elmsford | Greenburgh | 1,581 | 0 | 0 % | 0 % | 0 | 1,525 |
| Greenburgh | Greenburgh | 13,973 | 0 | 0 % | 0 % | 0 | 13,229 |
| Harrison | Harrison | 8,531 | 7,689 | 90 % | 99 % | 0 | 7,726 |
| Hastings-on-Hudson | Greenburgh | 2,940 | 0 | 0 % | 0 % | 0 | 2,272 |
| Irvington | Greenburgh | 2,198 | 0 | 0 % | 0 % | 0 | 1,977 |
| Larchmont | Mamaroneck | 2,378 | 2,318 | 98 % | 100 % | 627 | 2,079 |
| Lewisboro | Lewisboro | 6,880 | 0 | 0 % | 0 % | 0 | 6,451 |
| Mamaroneck | Mamaroneck | 3,826 | 3,734 | 98 % | 100 % | 468 | 3,165 |
| Mamaroneck, Village | Mamaroneck | 5,553 | 5,424 | 98 % | 100 % | 1,658 | 3,611 |
| Mount Kisco | Mount Kisco | 2,962 | 1,383 | 47 % | 62 % | 173 | 2,888 |
| Mount Pleasant | Mount Pleasant | 10,724 | 7,455 | 70 % | 82 % | 466 | 8,527 |
| Mount Vernon | Mount Vernon | 13,860 | 548 | 4 % | 4 % | 0 | 8,981 |
| New Castle | New Castle | 7,639 | 7,088 | 93 % | 100 % | 449 | 7,452 |
| New Rochelle | New Rochelle | 18,233 | 10,941 | 60 % | 72 % | 1,950 | 13,876 |
| North Castle | North Castle | 6,106 | 0 | 0 % | 0 % | 0 | 5,434 |
| North Salem | North Salem | 3,491 | 0 | 0 % | 0 % | 0 | 3,226 |
| Ossining | Ossining | 2,204 | 0 | 0 % | 0 % | 0 | 2,175 |
| Ossining, Village | Ossining | 6,185 | 0 | 0 % | 0 % | 0 | 5,951 |
| Peekskill | Peekskill | 6,310 | 116 | 2 % | 2 % | 0 | 6,190 |
| Pelham | Pelham | 2,464 | 2,441 | 99 % | 100 % | 514 | 1,766 |
| Pelham Manor | Pelham | 2,259 | 2,237 | 99 % | 100 % | 279 | 1,623 |
| Pleasantville | Mount Pleasant | 2,756 | 1,404 | 51 % | 58 % | 228 | 2,084 |
| Port Chester | Rye (town) | 6,458 | 6,313 | 98 % | 100 % | 3,140 | 5,582 |
| Pound Ridge | Pound Ridge | 3,381 | 3,176 | 94 % | 99 % | 171 | 3,039 |
| Rye | Rye (city) | 5,904 | 4,836 | 82 % | 97 % | 324 | 4,979 |
| Rye Brook | Rye (town) | 3,290 | 3,242 | 98 % | 100 % | 515 | 2,935 |
| Scarsdale | Scarsdale | 7,130 | 6,911 | 97 % | 100 % | 0 | 6,569 |
| Sleepy Hollow | Mount Pleasant | 2,295 | 1,327 | 58 % | 72 % | 231 | 1,898 |
| Somers | Somers | 10,002 | 7,381 | 74 % | 99 % | 871 | 9,523 |
| Tarrytown | Greenburgh | 3,164 | 0 | 0 % | 0 % | 0 | 3,038 |
| Tuckahoe | Eastchester | 1,548 | 22 | 1 % | 1 % | 0 | 1,131 |
| White Plains | White Plains | 12,481 | 10,087 | 81 % | 96 % | 2,772 | 7,846 |
| Yonkers | Yonkers | 36,836 | 35,044 | 95 % | 100 % | 2,562 | 28,870 |
| Yorktown | Yorktown | 14,367 | 10,114 | 70 % | 83 % | 865 | 13,919 |

Heap years per assessing unit (count of main buildings on the year), residential records ("homes", classes 200-299) and everything else ("other") tested separately:

| Assessing unit | Homes | Other |
|---|---|---|
| Mamaroneck | 1897 (46), 1900 (78), 1902 (50), 1905 (50), 1907 (48), 1910 (75), 1912 (59), 1920 (194), 1947 (88), 1948 (85), 1978 (63) | 1900 (14), 1920 (63), 1930 (128), 1940 (125), 1950 (91), 1960 (47), 1970 (18), 1980 (22), 1990 (10) |
| Mount Kisco | 1927 (51) | 1982 (90) |
| Mount Pleasant | 1900 (131), 1910 (45), 1912 (44), 1920 (135), 1922 (85), 1940 (70) | 1900 (21), 1920 (15), 1925 (13), 1930 (10), 1940 (12), 1950 (19), 1970 (14) |
| New Castle | 1900 (50), 1920 (59), 1927 (67), 1930 (83) | - |
| New Rochelle | 1880 (82), 1885 (292), 1890 (147), 1895 (73), 1900 (242), 1905 (226), 1906 (113), 1987 (70) | - |
| Pelham | 1890 (47), 1900 (56), 1910 (71), 1920 (277) | 1980 (32) |
| Pound Ridge | 1860 (66) | - |
| Rye (city) | 1900 (76), 1910 (48), 1915 (72) | - |
| Rye (town) | 1880 (43), 1890 (88), 1900 (758), 1905 (59), 1910 (190), 1915 (69), 1920 (376), 1925 (223), 1930 (288), 1940 (120), 1950 (376) | 1880 (15), 1890 (10), 1900 (182), 1910 (34), 1915 (13), 1920 (44), 1925 (23), 1930 (36), 1950 (13), 1960 (26) |
| Somers | 1930 (175), 1935 (212), 1938 (61), 1940 (106), 1945 (61) | - |
| White Plains | 1920 (51), 1923 (146), 1924 (1554) | - |
| Yonkers | 1890 (118), 1900 (725) | 1900 (128), 1950 (54), 1960 (89), 1965 (103), 1970 (125), 1975 (102), 1980 (73), 1985 (40), 1990 (68) |
| Yorktown | 1920 (66), 1926 (41), 1930 (143), 1931 (52), 1935 (71), 1940 (148) | - |

Flagged by count but concentrated in a few 400 m cells (one development, NOT flagged): Mount Kisco 1949 (48 homes, spread 0.36); Mount Kisco 1978 (45 homes, spread 0.2); Mount Kisco 1987 (105 homes, spread 0.3); New Rochelle 1979 (62 homes, spread 0.43); Rye (town) 1978 (44 homes, spread 0.45); Rye (town) 1979 (93 homes, spread 0.3); Rye (town) 1985 (134 homes, spread 0.45); Rye (town) 1986 (81 homes, spread 0.41); Rye (town) 1963 (45 other, spread 0.38).

For comparison, the same test on the whole county: homes [1880, 1885, 1890, 1900, 1910, 1920], other [1900, 1920, 1930, 1940, 1950, 1960, 1965, 1970, 1975, 1980, 1982, 1990].

Weak heaps (count under four times the neighbouring years; could be a real peak): Mamaroneck 1902 (50, x3.4); Mamaroneck 1905 (50, x3.4); Mamaroneck 1907 (48, x3.3); Mamaroneck 1912 (59, x3.4); Mamaroneck 1920 (194, x3.0); Mamaroneck 1947 (88, x3.5); Mamaroneck 1948 (85, x3.3); Mount Pleasant 1940 (70, x3.2); New Castle 1927 (67, x3.8); New Rochelle 1906 (113, x3.0); Rye (city) 1915 (72, x3.7); Rye (town) 1925 (223, x3.2); Rye (town) 1940 (120, x3.2); Somers 1938 (61, x3.1); Somers 1945 (61, x3.6); White Plains 1923 (146, x3.9); Yorktown 1935 (71, x3.9).

Main buildings by decade of the assessor's year:

| before 1800 | 1800s | 1810s | 1820s | 1830s | 1840s | 1850s | 1860s | 1870s | 1880s | 1890s | 1900s | 1910s | 1920s | 1930s | 1940s | 1950s | 1960s | 1970s | 1980s | 1990s | 2000s | 2010s | 2020s |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 164 | 49 | 22 | 55 | 34 | 37 | 153 | 196 | 341 | 775 | 1,882 | 5,915 | 5,045 | 19,510 | 8,949 | 6,234 | 22,029 | 13,522 | 6,636 | 6,095 | 5,122 | 4,066 | 2,047 | 884 |

Against the State Historic Preservation Office's inventory names (independent of the assessor), main buildings:

- names with a plain year, e.g. "Residence (1929)": 18 pairs; assessor within 2 years 15, within 10 years 16; assessor more than 10 years later 1, more than 10 years earlier 1; of those off by more than 10, 0 sit on flagged heap years.
- names with a 'circa' year, e.g. "Queen Anne house ca 1890": 115 pairs; assessor within 2 years 8, within 10 years 34; assessor more than 10 years later 74, more than 10 years earlier 7; of those off by more than 10, 31 sit on flagged heap years.

Well-known buildings (`python counties_ny.py check`; hit = within 3 years):

| Building | Known year (from) | Result | Detail |
|---|---|---|---|
| Yonkers City Hall | 1910 (brief) | no year | assessor - secondary, inventory -, class 652, Yonkers, "Yonkers City Hall" |
| Philipse Manor Hall, Yonkers | 1682 (memory) | no year | assessor -, inventory -, class 681, Yonkers, "Philipse Manor Hall" |
| Kykuit, Pocantico Hills | 1913 (memory) | no year | assessor -, inventory -, class 250, Mount Pleasant, "Kykuit" |
| Westchester County Courthouse, White Plains | 1974 (wd) | no year | assessor -, inventory -, class 652, White Plains, "" |
| Old Dutch Church of Sleepy Hollow | 1685 (memory) | no year | assessor -, inventory -, class 620, Sleepy Hollow, "Old Dutch Church" |
| John Jay Homestead, Katonah | 1801 (memory) | no year | assessor -, inventory -, class 210, Bedford, "John Jay House" |
| Glenview Mansion (Hudson River Museum), Yonkers | 1876 (cris) | miss | assessor 1909 secondary, inventory -, class 682, Yonkers, "Glenview Mansion (1876)" |
| Sherwood House, Yonkers | 1740 (memory) | no year | assessor -, inventory -, class 612, Yonkers, "Sherwood House Museum" |
| Thomas Paine Cottage, New Rochelle | 1793 (memory) | no year | assessor -, inventory -, class 681, New Rochelle, "Thomas Paine Cottage" |
| Leland Castle, New Rochelle | 1859 (memory) | no year | assessor - secondary, inventory -, class 632, New Rochelle, "Leland Castle" |
| Jacob Purdy House, White Plains | 1721 (memory) | no year | assessor -, inventory -, class 963, White Plains, "JACOB PURDY HOUSE" |
| White Plains Armory | 1910 (memory) | no year | assessor -, inventory -, class 411, White Plains, "WHITE PLAINS ARMORY" |
| Wayside Cottage, Scarsdale | 1720 (memory) | miss | assessor 1987, inventory -, class 612, Scarsdale, "WAYSIDE COTTAGE" |
| Playland bathhouse, Rye | 1928 (memory) | no year | assessor - secondary, inventory -, class 590, Rye, "PLAYLAND AMUSEMENT PARK / Playland Bathh" |
| Peter Augustus Jay House (Jay Estate), Rye | 1838 (memory) | no year | assessor - secondary, inventory -, class 250, Rye, "Peter Augustus Jay House/Jay Estate Main" |
| Timothy Knapp House, Rye | 1670 (wp-list) | no year | assessor -, inventory -, class 210, Rye, "Timothy Knapp House" |
| Capitol Theatre, Port Chester | 1926 (memory) | miss | assessor 1896, inventory -, class 449, Port Chester, "The Capitol Theatre" |
| Life Savers Building, Port Chester | 1920 (memory) | miss | assessor 1988, inventory -, class 411, Port Chester, "Life Savers Building" |
| Bolton Priory, Pelham Manor | 1838 (wd) | hit | assessor 1838, inventory -, class 210, Pelham Manor, "BOLTON PRIORY" |
| Pelhamdale, Pelham Manor | 1750 (memory) | hit | assessor 1752, inventory -, class 210, Pelham Manor, "Pelhamdale" |
| PepsiCo headquarters, Purchase | 1970 (memory) | no year | assessor -, inventory -, class 464, Harrison, "PepsiCo Headquarters" |
| Union Church of Pocantico Hills | 1921 (wd) | no year | assessor -, inventory -, class 620, Mount Pleasant, "Union Church of Pocantico Hills" |
| Reader's Digest headquarters, Chappaqua | 1939 (memory) | no year | assessor -, inventory -, class 411, New Castle, "Reader's Digest Headquarters" |
| Horace Greeley House, Chappaqua | 1820 (memory) | miss | assessor 1854, inventory -, class 482, New Castle, "Horace Greeley House" |
| IBM Watson Research Center, Yorktown | 1961 (memory) | no year | assessor -, inventory -, class 464, Yorktown, "TJ Watson Research Center" |
| Alder Manor, Yonkers | 1912 (memory) | miss (flagged heap) | assessor 1970 heap secondary, inventory -, class 612, Yonkers, "W B THOMPSON MANSION - Alder Manor" |
| St. Joseph's Seminary, Dunwoodie | 1896 (memory) | no year | assessor -, inventory -, class 620, Yonkers, "Saint Joseph's Seminary" |
| Yonkers station | 1911 (memory) | hit | assessor 1911, inventory -, class 843, Yonkers, "Yonkers Station" |
| Yonkers Main Post Office | 1927 (memory) | no year | assessor -, inventory -, class 652, Yonkers, "Yonkers Main Post Office" |
| Proctor's Theater, Yonkers | 1916 (memory) | hit | assessor 1915, inventory -, class 464, Yonkers, "RKO PROCTOR'S THEATRE" |
| Proctor's Theater, Mount Vernon | 1913 (cris) | hit by the inventory year | assessor 1912, inventory 1913, class 464, Mount Vernon, "PROCTOR'S THEATER, 1913" |
| Lyndhurst, Tarrytown | 1838 (memory) | no year | assessor - secondary, inventory -, class 681, Tarrytown, "Lyndhurst Mansion" |
| Sunnyside, Tarrytown | 1835 (memory) | no year | assessor - secondary, inventory -, class 681, Tarrytown, "Washington Irving's Sunnyside cottage" |
| Manor House, Larchmont | 1797 (memory) | hit | assessor 1797, inventory -, class 210, Larchmont, "MANOR HOUSE (MUNRO HOUSE)" |
| Bar Building, White Plains | 1926 (memory) | no year | assessor -, inventory -, class 464, White Plains, "Bar Building" |
| Scarsdale station | 1904 (memory) | no year | assessor -, inventory -, class 450, Scarsdale, "SCARSDALE RAILROAD STATION - HARLEM LINE" |
| Boyce Thompson Institute, Yonkers | 1924 (memory) | hit | assessor 1924, inventory -, class 480, Yonkers, "Boyce Thompson Institute" |
| Mamaroneck Methodist Church | 1859 (memory) | miss (flagged heap) | assessor 1910 heap, inventory -, class 620, Mamaroneck, Village, "Mamaroneck United Methodist Church" |
| Holy Trinity Church, Mamaroneck | 1886 (wd) | hit | assessor 1885, inventory -, class 620, Mamaroneck, Village, "Holy Trinity Roman Catholic Church" |
| Trump Plaza, New Rochelle | 2007 (wd) | no year | assessor -, inventory -, class 411, New Rochelle, "Trump Plaza" |

Tally: no year 25, miss 7, hit 8.

### Rockland (36087)

**Is it in the public layer?** Yes, and filled: 84,200 of 92,620 parcels carry a year (91 %),
69,645 of 69,807 residential parcels (99.8 %), in every one of the 23 municipalities (five
assessing towns: Clarkstown, Haverstraw, Orangetown, Ramapo, Stony Point).


### Rockland: the built file (`data/interim/counties/ny_rockland.parquet`)

- Footprints: 77,051 Overture outlines have their inner point in the county; 481 under 12 m2 dropped; 22,989 outlines of the State's layer added where Overture has none (the State's layer holds 94,673 of 12 m2 or more) -> **99,559 rows**.
- Outline sources: `overture:microsoft` 64,426, `nys_bf_2007` 22,638, `overture:osm` 12,144, `nys_bf_microsoft` 351.
- With a year: **95,105 (95.5 %)**; main buildings 68,557 of 70,655 (97.0 %); secondary (not the largest outline of their parcel) 28,904; outside every parcel 160.
- Single-family homes (class 210 / 215), main buildings: 58,477 of 58,541 dated (99.9 %). Commercial, industrial, civic and other main buildings: 3,407 of 4,809 dated (71 %).
- On heap years: **13,544** footprints (14 % of the dated); main buildings 7,365 (11 %).
- With a height: **72,534 (73 %)** (Overture's `height`; 907 of them are 1.5 m or less); with a floor count 110; named 1,660; with an inventory year 20 (+ 10 'circa').
- Years run 1700-2025; geometry: 0 invalid.

Per municipality (`muni` = the village, the town outside its villages, or the city; the assessing unit is the town or city — for a village in two towns, the one with most of it). "Main homes dated" = share of the main buildings on residential parcels (classes 200-299) that carry a year = column `muni_year_share`.

| Municipality | Assessing unit | Footprints | With a year | Share | Main homes dated | On heap years | With a height |
|---|---|---:|---:|---:|---:|---:|---:|
| (no parcel within 300 m) |  | 2 | 0 | 0 % | 0 % | 0 | 0 |
| Airmont | Ramapo | 3,723 | 3,669 | 98 % | 100 % | 275 | 2,681 |
| Chestnut Ridge | Ramapo | 3,446 | 3,384 | 98 % | 100 % | 346 | 1,975 |
| Clarkstown | Clarkstown | 30,003 | 29,208 | 97 % | 100 % | 2,901 | 24,140 |
| Grand View-on-Hudson | Orangetown | 199 | 194 | 98 % | 100 % | 59 | 147 |
| Haverstraw | Haverstraw | 4,210 | 3,633 | 86 % | 100 % | 534 | 3,112 |
| Haverstraw, Village | Haverstraw | 1,905 | 1,730 | 91 % | 100 % | 664 | 1,485 |
| Hillburn | Ramapo | 468 | 441 | 94 % | 100 % | 269 | 317 |
| Kaser | Ramapo | 213 | 202 | 95 % | 100 % | 53 | 179 |
| Montebello | Ramapo | 1,930 | 1,866 | 97 % | 100 % | 195 | 1,460 |
| New Hempstead | Ramapo | 1,816 | 1,763 | 97 % | 100 % | 146 | 1,118 |
| New Square | Ramapo | 540 | 475 | 88 % | 100 % | 69 | 467 |
| Nyack | Orangetown | 1,985 | 1,825 | 92 % | 100 % | 612 | 1,042 |
| Orangetown | Orangetown | 16,770 | 16,121 | 96 % | 100 % | 1,999 | 12,188 |
| Piermont | Orangetown | 861 | 820 | 95 % | 100 % | 247 | 520 |
| Pomona | Haverstraw | 1,360 | 1,332 | 98 % | 100 % | 64 | 885 |
| Ramapo | Ramapo | 9,140 | 8,596 | 94 % | 100 % | 891 | 6,444 |
| Sloatsburg | Ramapo | 1,518 | 1,461 | 96 % | 100 % | 432 | 1,117 |
| Spring Valley | Ramapo | 3,277 | 2,979 | 91 % | 100 % | 859 | 1,467 |
| Stony Point | Stony Point | 7,645 | 7,063 | 92 % | 100 % | 925 | 5,438 |
| Suffern | Ramapo | 2,744 | 2,667 | 97 % | 100 % | 979 | 1,961 |
| Upper Nyack | Clarkstown | 1,077 | 1,062 | 99 % | 100 % | 175 | 761 |
| Wesley Hills | Ramapo | 2,199 | 2,151 | 98 % | 100 % | 143 | 1,568 |
| West Haverstraw | Haverstraw | 2,528 | 2,463 | 97 % | 100 % | 707 | 2,062 |

Heap years per assessing unit (count of main buildings on the year), residential records ("homes", classes 200-299) and everything else ("other") tested separately:

| Assessing unit | Homes | Other |
|---|---|---|
| Clarkstown | 1900 (174), 1910 (70), 1920 (206), 1925 (113), 1930 (237), 1935 (120), 1940 (195) | 1950 (15), 1960 (79), 1965 (57), 1968 (54), 1970 (144), 1975 (89), 1978 (45), 1980 (94) |
| Haverstraw | 1865 (40), 1900 (271), 1915 (47), 1920 (112), 1925 (70), 1930 (84), 1935 (47), 1940 (60), 1950 (105) | 1865 (13), 1900 (28), 1960 (48), 1968 (28), 1970 (63), 1971 (13), 1972 (11), 1973 (25), 1975 (15), 1980 (47), 1985 (11), 1990 (14) |
| Orangetown | 1860 (50), 1867 (46), 1870 (41), 1880 (106), 1890 (110), 1897 (42), 1900 (235), 1910 (136), 1912 (63), 1916 (63), 1917 (69), 1918 (65), 1920 (185), 1930 (185) | 1890 (14), 1900 (54), 1910 (16), 1920 (25), 1930 (16), 1950 (19), 1960 (63), 1970 (64), 1975 (19), 1980 (51), 1982 (12) |
| Ramapo | 1860 (53), 1880 (62), 1890 (150), 1900 (499), 1910 (262), 1920 (220), 1930 (190), 1940 (119) | 1900 (32), 1960 (155), 1970 (285), 1975 (74), 1980 (161), 1985 (48), 1990 (70) |
| Stony Point | 1880 (57), 1900 (57), 1930 (51), 1940 (56), 1950 (145) | 1950 (16), 1960 (10) |

Flagged by count but concentrated in a few 400 m cells (one development, NOT flagged): Haverstraw 1956 (195 homes, spread 0.29); Ramapo 1972 (55 other, spread 0.33).

For comparison, the same test on the whole county: homes [1860, 1880, 1890, 1900, 1910, 1920, 1930, 1940], other [1900, 1950, 1960, 1965, 1968, 1970, 1975, 1980, 1985, 1990].

Weak heaps (count under four times the neighbouring years; could be a real peak): Clarkstown 1925 (113, x3.2); Clarkstown 1935 (120, x3.7); Haverstraw 1950 (105, x3.3); Orangetown 1918 (65, x3.8); Orangetown 1930 (185, x3.3).

Main buildings by decade of the assessor's year:

| before 1800 | 1800s | 1810s | 1820s | 1830s | 1840s | 1850s | 1860s | 1870s | 1880s | 1890s | 1900s | 1910s | 1920s | 1930s | 1940s | 1950s | 1960s | 1970s | 1980s | 1990s | 2000s | 2010s | 2020s |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 130 | 81 | 41 | 45 | 45 | 73 | 167 | 354 | 228 | 528 | 681 | 1,723 | 1,290 | 2,544 | 2,084 | 2,118 | 11,269 | 17,299 | 10,679 | 6,465 | 5,026 | 3,074 | 1,661 | 952 |

Against the State Historic Preservation Office's inventory names (independent of the assessor), main buildings:

- names with a plain year, e.g. "Residence (1929)": no pairs (the inventory years are on parcels without an assessor's year, or on secondary buildings).
- names with a 'circa' year, e.g. "Queen Anne house ca 1890": 2 pairs; assessor within 2 years 0, within 10 years 1; assessor more than 10 years later 1, more than 10 years earlier 0; of those off by more than 10, 1 sit on flagged heap years.

Well-known buildings (`python counties_ny.py check`; hit = within 3 years):

| Building | Known year (from) | Result | Detail |
|---|---|---|---|
| Edward Hopper House, Nyack | 1858 (memory) | near (<= 10 y) | assessor 1867, inventory -, class 600, Nyack, "EDWARD HOPPER HOUSE - NOW ART CENTER" |
| DeWint House, Tappan | 1700 (memory) | no year | assessor - secondary, inventory -, class 681, Orangetown, "DeWint House" |
| Tappan Reformed Church | 1835 (memory) | hit | assessor 1835, inventory -, class 620, Orangetown, "TAPPAN REFORMED CHURCH" |
| Nyack Library | 1903 (memory) | no year | assessor -, inventory -, class 611, Nyack, "Nyack Library" |
| Rockland County Courthouse, New City | 1928 (memory) | miss | assessor 1988 secondary, inventory -, class 652, Clarkstown, "Rockland County Courthouse" |
| Stony Point Lighthouse | 1826 (memory) | no year | assessor -, inventory -, class 961, Stony Point, "Stony Point Lighthouse" |
| Lafayette Theatre, Suffern | 1924 (memory) | miss | assessor 1940, inventory -, class 512, Suffern, "Lafayette Theatre" |
| Palisades Center, West Nyack | 1998 (memory) | hit | assessor 1998, inventory -, class 451, Clarkstown, "Palisades Center" |
| Old Stone Church, Upper Nyack | 1813 (memory) | miss | assessor 1914, inventory -, class 210, Upper Nyack, "Old Stone Church" |
| Bear Mountain Inn | 1915 (wp-list) | no year | assessor -, inventory -, class 961, Stony Point, "Bear Mountain Inn" |
| Blauvelt-Cropsey Farm, New City (1790s) | 1795 (wp-list) | miss | assessor 1769, inventory -, class 590, Clarkstown, "Blauvelt-Cropsey Farm/Cropsey Community " |
| First Reformed Church, Piermont | 1946 (wp-list) | miss (flagged heap) | assessor 1960 heap, inventory -, class 620, Piermont, "Piermont Reformed Church" |
| Kings Daughters Public Library, Haverstraw | 1903 (wp-list) | no year | assessor -, inventory -, class 611, Haverstraw, Village, "Fowler Building - Haverstraw King's Daug" |
| Jacob Sloat House, Sloatsburg | 1848 (wp-list) | hit | assessor 1850, inventory -, class 642, Sloatsburg, "Jacob Sloat House" |
| US Post Office, Haverstraw | 1934 (wp-list) | miss (flagged heap) | assessor 1960 heap, inventory -, class 652, Haverstraw, Village, "US POST OFFICE-HAVERSTRAW" |
| US Post Office, Spring Valley | 1936 (wp-list) | miss (flagged heap) | assessor 1980 heap, inventory -, class 650, Spring Valley, "US POST OFFICE-SPRING VALLEY" |
| US Post Office, Pearl River | 1935 (wp-list) | no year | assessor -, inventory -, class 652, Orangetown, "Pearl River Main Post Office" |
| North Main Street School, Spring Valley | 1916 (wp-list) | no footprint found |  |
| Camp Hill School, Pomona | 1923 (wp-list) | no footprint found |  |
| Pig Knoll School, Pomona | 1915 (wp-list) | no footprint found |  |
| English Church, New City | 1827 (wp-list) | miss | assessor 1950 secondary, inventory -, class 620, Ramapo, "OLD ENGLISH CHURCH/NEW HEMPSTEAD PRESBYT" |
| John Green House, Nyack | 1819 (wp-list) | miss (flagged heap) | assessor 1918 heap, inventory -, class 230, Nyack, "John Green House" |
| The Homestead, Haverstraw (c. 1800) | 1800 (wp-list) | miss (flagged heap) | assessor 1900 heap, inventory -, class 210, Haverstraw, Village, "HOMESTEAD" |
| Edward Salyer House, Pearl River | 1765 (wp-list) | miss | assessor 1750, inventory -, class 210, Orangetown, "EDWARD SALYER HOUSE/CONQUES RES" |
| Michael Salyer Stone House, Orangetown | 1790 (wp-list) | miss | assessor 1732, inventory -, class 210, Orangetown, "Michael Salyer Stone House" |
| McCready House, Sloatsburg | 1889 (wp-list) | near (<= 10 y) (flagged heap) | assessor 1880 heap, inventory -, class 280, Sloatsburg, "McCready House Carriage Barn" |
| William H. Rose House, Stony Point (c. 1862) | 1862 (wp-list) | hit | assessor 1860, inventory -, class 280, Stony Point, "William H. Rose House" |
| Sloat House, Sloatsburg | 1755 (wp-list) | no footprint found |  |
| H. R. Stevens House, New City | 1775 (wp-list) | hit | assessor 1776, inventory -, class 210, Clarkstown, "H. R. Stevens House" |
| Tallman-Budke House, Clarkstown | 1790 (wp-list) | miss (flagged heap) | assessor 1900 heap secondary, inventory -, class 210, Clarkstown, "Tallman-Budke House" |
| House at 352 Piermont Avenue | 1780 (wp-list) | no footprint found |  |

Tally: near 2, no year 6, hit 5, miss 13, no footprint found 5.

### Nassau (36059): no public year built — not built

What was tried, all on 2026-11-10:

1. **NYS Tax Parcels Public**: Nassau is not among the 38 counties that let the State publish
   their parcels (the service's own list; a count for `COUNTY_NAME='Nassau'` returns 0).
2. **NYS Tax Parcel Centroid Points** (the State's layer for *all* counties,
   https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Tax_Parcel_Centroid_Points/FeatureServer/0):
   Nassau has 423,430 parcel points on the 2025 roll (Hempstead 230,107, Oyster Bay 102,019,
   North Hempstead 73,474, Long Beach 9,850, Glen Cove 7,980) and `YR_BLT` is **null in every
   one** (min and max of the field are null in all five units). Nassau's Department of
   Assessment keeps its own system and does not file its inventory with the State.
3. **Nassau County itself**: the Land Records Viewer (https://lrv.nassaucountyny.gov) shows a
   property's record one parcel at a time behind a captcha (or an account); its map services
   (https://legacygis.nassaucountyny.gov/arcgis/rest/services, `Akanda` and `IASWorld`) serve
   parcel and lot outlines with section / block / lot only — no assessment attribute. No
   bulk file with year built was found on the county's site; `data.nassaucountyny.gov` does
   not answer (the gateway could not connect). The county's assessment-roll downloads carry
   values, owners and classes, not the inventory (per the search results; not opened). Harvesting
   the viewer parcel by parcel is against the spirit of the captcha and was not attempted.
4. **data.ny.gov assessment rolls** (`7vem-aaz7`): no year built for any county.
5. **Copies on ArcGIS Online** ("Nassau Interactive Map Parcels" and others): the State's
   2020 file shared with state agencies, re-posted by third parties — no `YR_BLT` among its
   fields, and not a source one may rely on. Commercial resellers sell Nassau parcels with a
   year built (about $250): not open data.
6. Footprints would not be the problem: the State's layer has 575,634 Nassau outlines (Nassau
   County 2013) and Overture covers the county.

So the brief's Nassau checks (Garden City's cathedral 1885, Old Westbury Gardens 1906,
Levittown 1947-51) could not be run. Modelled years (HISDAC-US, the census "year structure
built") exist for Nassau and were not used. **Verdict: leave Nassau off the map** until the
county releases its inventory (a FOIL request to the Department of Assessment is the route).

## Known problems

- **Westchester is a patchwork.** 22 municipalities have no years; a map of Westchester by
  the owner's rule has holes right at the city line (Mount Vernon) and along the Hudson
  (Hastings to Tarrytown, Ossining, Peekskill). `ny_westchester_munis.geojson` has the
  outlines with `dated` = yes / partly / no.
- **The assessor's year is a residential year.** Exempt and commercial parcels mostly carry
  none in Westchester (city halls, courthouses, churches, museums, estates in trust, office
  parks: 25 of the 40 well-known buildings checked have no year). Where they carry one it is
  usually a round estimate (in Rockland 45 % of the non-residential years end in 0, 60 % in
  0 or 5) or the year of a conversion (Life Savers Building 1988, Wayside Cottage 1987).
  These are flagged `heap` where the count shows it; the rest cannot be told apart.
- **Before 1900 the years run late.** Against the Historic Preservation Office's survey of
  old Yonkers ("ca." dates) the assessor is more than ten years late for two buildings in
  three; "1900" there means "by 1900", as in the city.
- **Twentieth-century houses check out**: 13 of Scarsdale's 15 surveyed residences match to
  the year;
  BelleFair in Rye Brook (built 1999-2003, date from memory) has 199 of 201 parcels on
  1999-2001; Heritage Hills in Somers (begun 1973-74, from memory) starts in 1974.
- **`secondary` is by size only.** On a parcel with several real buildings (garden
  apartments, campuses, estates, condominium land) all but the largest are flagged and share
  the parcel's year, which belongs to one of them. Westchester has 17,360 footprints on
  parcels with ten or more outlines, Rockland 4,401.
- **One outline, several parcels.** A row of attached houses drawn as one outline takes the
  year of the parcel under its centre.
- **The State's gap-filling outlines are from 2007 (Rockland) and 2013 (Westchester)**: a
  few may be gone; they have no height. `footprint_src` starts with `nys_bf`.
- **Heights are Overture's**, almost all machine estimates (unrounded decimals), not
  measured roofs; several hundred are under 1.5 m. `floors` is nearly empty.
- **`year_hist` is thin**: the public inventory layer has no date field, so only names that
  end in a year give one. The dated register entries the lead may want are better added
  by hand through `known_building_dates`.
- The parcel outlines are the counties' tax maps (no edge matching, a few metres off in
  places): a footprint on a lot line can take the neighbour's year.
- The 'known year' of the checks marked *memory* was not re-read today (Wikipedia's API
  refused the requests: rate limit); the others are from the sources named.

## Verdict

- **Rockland — good enough, put it on the map.** 95.5 % of the footprints and all but 0.1 % of
  the main homes carry a real year; one in ten main buildings sits on a flagged heap year
  (pre-1945 round years, and the round years of the commercial records), which the lead's
  estimator treats as ranges. The outline set is Overture plus the State's 2007 outlines.
- **Westchester — only in part.** Good enough: the 15 municipalities with `muni_year_share`
  of 0.9 or more (Harrison, Larchmont, Mamaroneck town and village, New Castle, Pelham,
  Pelham Manor, Port Chester, Pound Ridge, Rye, Rye Brook, Scarsdale, Somers, White Plains,
  Yonkers): 91 % of their footprints dated. Usable with a warning: the 6 partly dated
  (New Rochelle 72 % of main homes, Mount Pleasant 82 %, Yorktown 83 %, Sleepy Hollow 72 %,
  Mount Kisco 63 %, Pleasantville 58 %) — a third of their buildings would be estimated from
  neighbours. Not good enough: the 22 others (2.5 % dated) — by the owner's rule they stay
  off the map; estimating whole towns from nothing is the generated map the owner does not
  want.
- **Nassau — no.** No public year built.

## For the lead

- `pipeline/county_buildings.py` already reads `data/interim/counties/ny_*.parquet`. To keep
  only dated ground: `g = g[g.muni_year_share >= 0.9]` (or 0.5 to include the partly dated)
  for the New York files; without it the 22 empty Westchester municipalities (113 thousand
  footprints) are dated entirely by `fill_estimates`.
- `year_hist` holds only plain inventory years (safe as `historic_register`, `exact`);
  `year_hist_ca` holds the 'circa' ones — treat as `estimated` if used.
- `heap` is already per assessing unit and per kind of record; the county-wide
  `find_heaps` in `county_buildings.py` adds nothing harmful.
- Extra columns: `town` (assessing unit), `parcel` (SWIS + print key), `n_on_parcel`,
  `usn` (inventory number), `footprint_src`, `area_m2`, `lon`, `lat`, `muni_year_share`,
  `hist_src`, `year_hist_ca`.
- Rebuild: `cd pipeline && ../.venv/bin/python counties_ny.py` (downloads are cached; the
  build peaked at 1.3 GB for Westchester, 0.6 GB for Rockland, and takes three to five minutes; `check` rewrites the tables of
  well-known buildings).


## Summary table

| County | Footprints | With a year | On heap years | With a height | Verdict |
|---|---:|---:|---:|---:|---|
| Westchester | 282,725 | 143,331 (50.7 %) | 18,307 | 241,639 (85 %) | in part: 15 municipalities yes, 6 partly, 22 no |
| Rockland | 99,559 | 95,105 (95.5 %) | 13,544 | 72,534 (73 %) | yes |
| Westchester, the 15 dated municipalities only | 118,132 | 107,921 (91.4 %) | 14,350 | 96,765 (82 %) | |
| Westchester, the 6 partly dated | 51,337 | 32,624 (63.5 %) | 3,913 | 43,192 (84 %) | |
| Westchester, the 22 without years | 113,256 | 2,786 (2.5 %) | 44 | 101,682 (90 %) | |
| Nassau | not built | no public year built | - | - | no |

