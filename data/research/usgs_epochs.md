# USGS / Army Map Service sheets: woodland and built-up ground of the whole map

Tool: `data/manual/gapfill/tools/usgs_epochs.py` (run / assemble / validate / preview). Scans were downloaded one at a time
to `data/interim/usgs_epochs_raw/`, read in strips, deleted; the per-sheet pieces stay in `.../pieces/` (small).
All sheets: USGS Historical Topographic Map Collection, public domain, GeoTIFF, NAD27, 21 m per pixel.

## Files (data/manual/gapfill/)

| file | features | content |
|---|---|---|
| all_woodland_1957.geojson | 49 (MultiPolygon per sheet and county) | woodland tint, editions 1957-61, 31 areas |
| all_tint_1957.geojson | 46 | urban tint, editions 1957-61, 31 areas |
| all_woodland_1949.geojson | 47 | woodland tint, editions 1946-50 |
| all_tint_1949.geojson | 46 | urban tint, editions 1946-50, 31 areas |
| outer_tint_1949.geojson | 25 | the 19 outer counties of all_tint_1949 |

Properties: county (the 26 counties as named in extent_counties.json and the five boroughs), kind, year (edition printed on
the sheet; the survey is older, the 1:250,000 series is compiled from 1930s-50s 7.5/15-minute sheets), sheet, scale,
source_url, method, area_ha, confidence, licence. Polygons simplified to 30 m; woodland is closed over symbols narrower
than ~230 m (roads, streams: at 1:250,000 a road symbol is 150-200 m wide) and holes under 2.6 ha are filled.

## Sheets used (all 1:250,000, Army Map Service; base URL https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/)

| key | sheet | year | file |
|---|---|---|---|
| newark57 | Newark NK 18-11 | 1957 | NJ/NJ_Newark_472533_1957_250000_geo.tif |
| ny57 | New York | 1957 | NY/NY_New%20York_130815_1957_250000_geo.tif |
| providence57 | Providence (Montauk only) | 1957 | RI/RI_Providence_463160_1957_250000_geo.tif |
| hartford61 | Hartford | 1961 | CT/CT_Hartford_331221_1961_250000_geo.tif |
| scranton59 | Scranton | 1959 | PA/PA_Scranton_221783_1959_250000_geo.tif |
| wilmington57 | Wilmington NJ-DE (Ocean Co.) | 1957 | DE/DE_Wilmington_463186_1957_250000_geo.tif |
| albany59 | Albany (Dutchess / Ulster tips) | 1959 | NY/NY_Albany_136546_1959_250000_geo.tif |
| binghamton58 | Binghamton (Ulster / Sullivan tips) | 1958 | NY/NY_Binghamton_123306_1958_250000_geo.tif |
| newark49 | Newark | 1949 | NJ/NJ_Newark_255456_1949_250000_geo.tif |
| ny49 | New York | 1949 | NY/NY_New%20York_130809_1949_250000_geo.tif |
| hartford47 | Hartford | 1947 | CT/CT_Hartford_331218_1947_250000_geo.tif |
| scranton50 | Scranton | 1950 | PA/PA_Scranton_707601_1950_250000_geo.tif |
| wilmington46 | Wilmington | 1946 | DE/DE_Wilmington_707694_1946_250000_geo.tif |
| albany48 | Albany | 1948 | NY/NY_Albany_136545_1948_250000_geo.tif |

Not covered in the 1949 files: Binghamton 1948 (paler print, not calibrated) and Providence 1948 (no woodland tint at Montauk):
a sliver of Ulster / Sullivan north of 42 N and Suffolk east of 72 W (Montauk). The 1946-50 sheets of the Hartford,
Scranton and Albany series are not the same tint colours as 1957: colours were read per sheet (HSV windows in `SHEETS`)
and checked drawn over the scan (Newark/Morris, Hicksville, Mount Kisco, Middletown, Pine Barrens, Montauk).

## Registration

Checked two ways. (1) Neatlines and coast on the sheets drawn over the scan (Montauk: the 41 N / 72 W neatline falls where it
should to within a pixel). (2) Today's buildings recorded before 1937/1929 shifted in 25 m steps against the urban polygons:
the recall is flat and peaks at a shift of 25-50 m (0.541 -> 0.544 and 0.537 -> 0.540). Error against today's coordinates:
about 50 m or better, well below the sheets' own generalisation (a town's outline at 1:250,000 is good to ~100 m).

## Validation (buildings with a recorded year, `conf = exact`, still standing)

Tint: "recorded < year" inside = recall of built-up ground (in suburbs of scattered houses it is low); "recorded > year+10"
inside = how often a building recorded later still lies in tinted ground (should be small if "outside = not yet built").
Woodland: "recorded < year" inside = houses already there that lie in the woodland polygons (want near 0).

Overall (all 31 areas): tint 1949 recall 45.1 %, later-built inside 12.0 %; tint 1957 recall 36.8 %, later-built inside 14.3 %
(the 1957 figure falls because later infill is also inside); woodland 1949: 5.8 % of earlier buildings inside (28.5 % of
those built after 1959); woodland 1957: 7.4 % (24.2 % of those built after 1967).

Tables (columns: county, n recorded before the year, share inside, n recorded > year+10, share inside):

## all_woodland_1949.geojson  (year 1949, wood); polygons cover 11254 km2 at 41N
| county | recorded < year | inside | recorded > year+10 | inside |
|---|---|---|---|---|
| Bergen | 30176.0 | 2.0% | 64196.0 | 13.7% |
| Bronx | 8459.0 | 0.7% | 16550.0 | 1.8% |
| Brooklyn | 17427.0 | 0.0% | 31605.0 | 0.1% |
| Dutchess | 6124.0 | 6.9% | 48115.0 | 16.6% |
| Essex | 47781.0 | 4.2% | 27740.0 | 29.1% |
| Greater Bridgeport | 21603.0 | 4.7% | 32980.0 | 32.2% |
| Hudson | 7207.0 | 0.0% | 13929.0 | 0.0% |
| Hunterdon | 3011.0 | 8.2% | 24336.0 | 12.5% |
| Manhattan | 18271.0 | 0.0% | 10286.0 | 0.0% |
| Mercer | 9389.0 | 3.2% | 36231.0 | 10.7% |
| Middlesex | 14519.0 | 4.5% | 74359.0 | 21.7% |
| Monmouth | 11469.0 | 7.4% | 94234.0 | 27.7% |
| Morris | 12301.0 | 20.9% | 68031.0 | 48.9% |
| Ocean | 5140.0 | 21.1% | 152478.0 | 64.0% |
| Orange | 8091.0 | 9.5% | 59889.0 | 20.1% |
| Passaic | 9223.0 | 12.7% | 25626.0 | 47.9% |
| Putnam | 3306.0 | 23.7% | 16463.0 | 29.7% |
| Queens | 13221.0 | 0.4% | 36472.0 | 0.3% |
| Rockland | 5712.0 | 10.3% | 44673.0 | 24.3% |
| Somerset | 4803.0 | 11.6% | 48876.0 | 20.1% |
| South Central Connecticut | 21410.0 | 6.2% | 70208.0 | 30.0% |
| Staten Island | 1085.0 | 2.6% | 47864.0 | 11.6% |
| Suffolk | 2299.0 | 23.7% | 58283.0 | 50.7% |
| Sullivan | 3309.0 | 13.9% | 17270.0 | 28.9% |
| Sussex | 3149.0 | 31.2% | 25974.0 | 36.7% |
| Ulster | 5513.0 | 6.9% | 26569.0 | 18.2% |
| Union | 25741.0 | 3.7% | 31234.0 | 17.4% |
| Westchester | 35549.0 | 3.2% | 39197.0 | 17.2% |
| Western Connecticut | 24926.0 | 9.4% | 87540.0 | 30.1% |
| ALL | 380214 | 5.8% | 1331208 | 28.5% |

## all_woodland_1957.geojson  (year 1957, wood); polygons cover 11855 km2 at 41N
| county | recorded < year | inside | recorded > year+10 | inside |
|---|---|---|---|---|
| Bergen | 59333.0 | 2.2% | 43645.0 | 8.8% |
| Bronx | 9630.0 | 0.0% | 15284.0 | 0.0% |
| Brooklyn | 18539.0 | 0.1% | 30468.0 | 0.3% |
| Dutchess | 12527.0 | 11.1% | 38358.0 | 19.5% |
| Essex | 62181.0 | 3.5% | 18706.0 | 10.6% |
| Greater Bridgeport | 35233.0 | 11.9% | 23430.0 | 37.5% |
| Hudson | 8133.0 | 0.0% | 11163.0 | 0.0% |
| Hunterdon | 4653.0 | 3.4% | 21580.0 | 4.9% |
| Manhattan | 19235.0 | 0.0% | 8248.0 | 0.0% |
| Mercer | 15636.0 | 3.3% | 29754.0 | 6.9% |
| Middlesex | 31497.0 | 4.6% | 57585.0 | 16.4% |
| Monmouth | 21396.0 | 8.3% | 80852.0 | 21.7% |
| Morris | 24059.0 | 10.6% | 54585.0 | 22.1% |
| Ocean | 11741.0 | 27.2% | 140559.0 | 55.9% |
| Orange | 13505.0 | 10.7% | 51319.0 | 20.9% |
| Passaic | 18400.0 | 8.6% | 15871.0 | 33.3% |
| Putnam | 5062.0 | 27.7% | 13564.0 | 35.9% |
| Queens | 21983.0 | 0.0% | 34194.0 | 0.0% |
| Rockland | 12338.0 | 19.6% | 30677.0 | 27.4% |
| Somerset | 9281.0 | 4.7% | 39809.0 | 11.9% |
| South Central Connecticut | 41054.0 | 12.9% | 52247.0 | 35.7% |
| Staten Island | 1593.0 | 5.6% | 47426.0 | 8.2% |
| Suffolk | 5607.0 | 14.9% | 49550.0 | 28.9% |
| Sullivan | 4600.0 | 20.3% | 16084.0 | 37.2% |
| Sussex | 5291.0 | 23.5% | 22526.0 | 30.9% |
| Ulster | 8511.0 | 15.7% | 23495.0 | 32.7% |
| Union | 43969.0 | 3.9% | 18058.0 | 6.9% |
| Westchester | 51777.0 | 3.3% | 27640.0 | 18.9% |
| Western Connecticut | 43362.0 | 16.1% | 65223.0 | 32.7% |
| ALL | 620126 | 7.4% | 1081900 | 24.2% |

## all_tint_1949.geojson  (year 1949, urban); polygons cover 1327 km2 at 41N
| county | recorded < year | inside | recorded > year+10 | inside |
|---|---|---|---|---|
| Bergen | 30176.0 | 57.3% | 64196.0 | 27.1% |
| Bronx | 8459.0 | 75.4% | 16550.0 | 72.6% |
| Brooklyn | 17427.0 | 80.4% | 31605.0 | 70.8% |
| Dutchess | 6124.0 | 13.7% | 48115.0 | 2.0% |
| Essex | 47781.0 | 64.8% | 27740.0 | 31.4% |
| Greater Bridgeport | 21603.0 | 51.5% | 32980.0 | 15.2% |
| Hudson | 7207.0 | 61.5% | 13929.0 | 48.2% |
| Hunterdon | 3011.0 | 0.0% | 24336.0 | 0.0% |
| Manhattan | 18271.0 | 66.1% | 10286.0 | 61.9% |
| Mercer | 9389.0 | 30.4% | 36231.0 | 1.7% |
| Middlesex | 14519.0 | 19.4% | 74359.0 | 3.3% |
| Monmouth | 11469.0 | 34.0% | 94234.0 | 7.6% |
| Morris | 12301.0 | 11.8% | 68031.0 | 1.3% |
| Ocean | 5140.0 | 21.7% | 152478.0 | 3.5% |
| Orange | 8091.0 | 17.4% | 59889.0 | 1.5% |
| Passaic | 9223.0 | 34.6% | 25626.0 | 7.1% |
| Putnam | 3306.0 | 1.6% | 16463.0 | 0.2% |
| Queens | 13221.0 | 65.6% | 36472.0 | 58.4% |
| Rockland | 5712.0 | 22.1% | 44673.0 | 3.3% |
| Somerset | 4803.0 | 18.7% | 48876.0 | 1.8% |
| South Central Connecticut | 21410.0 | 32.4% | 70208.0 | 5.9% |
| Staten Island | 1085.0 | 38.5% | 47864.0 | 21.0% |
| Suffolk | 2299.0 | 14.4% | 58283.0 | 6.9% |
| Sullivan | 3309.0 | 1.8% | 17270.0 | 0.2% |
| Sussex | 3149.0 | 7.3% | 25974.0 | 0.5% |
| Ulster | 5513.0 | 19.5% | 26569.0 | 1.8% |
| Union | 25741.0 | 54.3% | 31234.0 | 25.0% |
| Westchester | 35549.0 | 50.5% | 39197.0 | 19.3% |
| Western Connecticut | 24926.0 | 23.2% | 87540.0 | 3.7% |
| ALL | 380214 | 45.1% | 1331208 | 12.0% |
registration: recall at no shift 0.541; best shift of the points dx=25 m east, dy=-25 m north: 0.544

## all_tint_1957.geojson  (year 1957, urban); polygons cover 1804 km2 at 41N
| county | recorded < year | inside | recorded > year+10 | inside |
|---|---|---|---|---|
| Bergen | 59333.0 | 53.8% | 43645.0 | 32.6% |
| Bronx | 9630.0 | 67.2% | 15284.0 | 68.2% |
| Brooklyn | 18539.0 | 76.8% | 30468.0 | 77.3% |
| Dutchess | 12527.0 | 8.3% | 38358.0 | 1.7% |
| Essex | 62181.0 | 63.2% | 18706.0 | 41.4% |
| Greater Bridgeport | 35233.0 | 22.8% | 23430.0 | 8.0% |
| Hudson | 8133.0 | 68.2% | 11163.0 | 59.1% |
| Hunterdon | 4653.0 | 0.0% | 21580.0 | 0.0% |
| Manhattan | 19235.0 | 71.9% | 8248.0 | 68.1% |
| Mercer | 15636.0 | 26.4% | 29754.0 | 2.4% |
| Middlesex | 31497.0 | 14.6% | 57585.0 | 3.8% |
| Monmouth | 21396.0 | 28.7% | 80852.0 | 10.3% |
| Morris | 24059.0 | 10.8% | 54585.0 | 1.8% |
| Ocean | 11741.0 | 16.6% | 140559.0 | 4.4% |
| Orange | 13505.0 | 12.1% | 51319.0 | 1.4% |
| Passaic | 18400.0 | 27.5% | 15871.0 | 9.2% |
| Putnam | 5062.0 | 1.0% | 13564.0 | 0.1% |
| Queens | 21983.0 | 80.1% | 34194.0 | 69.7% |
| Rockland | 12338.0 | 13.5% | 30677.0 | 3.7% |
| Somerset | 9281.0 | 15.9% | 39809.0 | 1.9% |
| South Central Connecticut | 41054.0 | 7.8% | 52247.0 | 2.0% |
| Staten Island | 1593.0 | 41.4% | 47426.0 | 24.2% |
| Suffolk | 5607.0 | 39.4% | 49550.0 | 19.0% |
| Sullivan | 4600.0 | 1.8% | 16084.0 | 0.2% |
| Sussex | 5291.0 | 4.4% | 22526.0 | 0.4% |
| Ulster | 8511.0 | 14.4% | 23495.0 | 1.6% |
| Union | 43969.0 | 47.0% | 18058.0 | 37.4% |
| Westchester | 51777.0 | 52.1% | 27640.0 | 23.5% |
| Western Connecticut | 43362.0 | 12.8% | 65223.0 | 2.8% |
| ALL | 620126 | 36.8% | 1081900 | 14.3% |
registration: recall at no shift 0.537; best shift of the points dx=0 m east, dy=-50 m north: 0.540


## Reading the numbers

- Outer counties, tint: later-built buildings inside the tint are 0-4 % in Dutchess, Putnam, Sullivan, Sussex, Hunterdon,
  Morris, Orange, Somerset, Ocean, Middlesex, Mercer (1949) - "outside the 1949 tint" is good evidence of "not a town yet"
  there. In the inner counties and boroughs the tint covers whole conurbations, so late infill sits inside (Bergen 27 %,
  Essex 31 %, Union 25 %, Queens 58 %): "inside" is NOT evidence of an early year there.
- Recall of old buildings is 0-35 % in the outer counties (most pre-1949 houses are farms and hamlets that a 1:250,000 sheet
  does not tint); the tint is a floor for towns (cities, boroughs, large villages), not a census of old houses.
- Woodland: low for early buildings in the built-up counties (Hudson 0 %, Essex 3 %, Bergen 2 %, Westchester 3 %); 15-28 % in
  Ocean, Putnam, Sullivan, Sussex, Rockland where villages sit in woods and the tint is drawn over them. "Inside woodland
  polygon" therefore means "wooded around then" only for ground without a recorded early building.

## Not done: the 1890-1905 epoch (part A, first epoch) for the outer counties

The 15-minute sheets of the 1880s-1900s in the outer counties (about 770 sheets/printings, 6-10 MB each) are 5.3 m per pixel
scans in yellowed paper, with brown contours and dark-grey roads and railways. Towns are shown as street grids and small
building marks, not as a tint. I tried black-ink density, thickened dots (2x2 opening) and dark-line density on Morristown
1888: they pick railways, road bends, labels and contour clutter, the towns (Morristown, Boonton, Madison) appear only as dense
grids that no threshold separated from rural lines; and the 1:125,000 sheets of 1900-05 cover only part of the box (Passaic,
Raritan, Navesink, Islip, Litchfield; the Raritan scan I fetched was mostly collar). No file was written rather than noise.
What would work: hand-tracing the larger towns (a few hundred polygons), or a line-density classifier trained on the
inner counties' 1897 polygons (`counties_builtup_1897.geojson`) with the validation above.
