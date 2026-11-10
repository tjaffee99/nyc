"""Research helper: the railroad rows (system `rail`) of data/tables/transit_openings.csv for the counties around
the city - route ids `cty_*` (rewritten on every run; the city's rows are not touched).

A row dates the Overture / OpenStreetMap tracks whose line name is one of `line` (names separated by `|`)
inside a box (from_stop = "lon lat" south-west corner, to_stop = north-east corner); pipeline/transit.py
takes the first row that fits each point of a track. Every date is from the Wikipedia article in `source`
(line and railroad articles, or the infobox of the station at the end of the stretch); where the article
gives a year or a month only the note says "estimated", and where the day is OpenHistoricalMap's (CC0) the
note says so. Lines without a row keep OpenHistoricalMap's date, else the nearest dated track.

    ../../../../.venv/bin/python build_county_rail_rows.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
WP = "https://en.wikipedia.org/wiki/"
W, E, S, N = -74.60, -73.30, 40.40, 41.45  # "anywhere" bounds
NJ_E = -74.00  # east edge of New Jersey / Rockland boxes (keeps the Long Island Rail Road's "Main Line" out)
HBLR = "Hudson-Bergen Light Rail|Hudson–Bergen Light Rail"
PATH = "Newark - World Trade Center|PATH"
ROWS = [
    # id, opened, note, source, line names, (lon0, lat0, lon1, lat1)
    # ---- Pennsylvania Railroad / Northeast Corridor
    ("nec_njrr_newark", "1834-09-15", "New Jersey Rail Road, Jersey City - Newark, opened 15 Sep 1834; the stretch kept by the Northeast Corridor west of "
     "Manhattan Transfer (today's approach over the Dock Bridge into Newark Penn Station is a realignment of 1935-37 on the same line)",
     WP + "New_Jersey_Rail_Road_and_Transportation_Company", "Northeast Corridor", (-74.166, 40.72, -74.118, 40.76)),
    ("nec_tunnel_extension", "1910-11-27", "Pennsylvania Railroad's New York Tunnel Extension from Manhattan Transfer across the Meadows and under "
     "Bergen Hill and the Hudson, opened 27 Nov 1910", WP + "North_River_Tunnels", "Northeast Corridor", (-74.118, 40.72, NJ_E, 40.80)),
    ("nec_elizabeth", "1835-09", "New Jersey Rail Road extended from Newark to Elizabeth in 1835 (year in the article; September is "
     "OpenHistoricalMap's month: estimated day)", WP + "New_Jersey_Rail_Road_and_Transportation_Company", "Northeast Corridor", (W, 40.667, -74.166, 40.7335)),
    ("nec_rahway", "1836", "New Jersey Rail Road extended from Elizabeth to Rahway and the Raritan in 1836 (year only: estimated day)",
     WP + "New_Jersey_Rail_Road_and_Transportation_Company", "Northeast Corridor", (W, S, -74.166, 40.667)),
    # ---- Lackawanna: Morris & Essex, Boonton line, Montclair branch, Gladstone branch
    ("me_bergen_tunnel", "1876", "Lackawanna's own tunnel under Bergen Hill to Hoboken opened in 1876 (year only: estimated day; before it the "
     "Morris & Essex used the Erie's tunnel)", WP + "Morris_and_Essex_Railroad", "Morristown Line|Main Line", (-74.062, 40.725, -74.02, 40.75)),
    ("me_newark_hoboken", "1862-11-14", "Morris & Essex's own line from Newark across the Meadows towards Hoboken: first train 14 Nov 1862 "
     "(regular use from 13 Oct 1863)", WP + "Morris_and_Essex_Railroad", "Morristown Line", (-74.172, 40.72, -74.062, 40.77)),
    ("me_newark_orange", "1836-11-19", "Morris & Essex, Newark - Orange, opened 19 Nov 1836", WP + "Morris_and_Essex_Railroad",
     "Morristown Line", (-74.2335, 40.72, -74.172, 40.80)),
    ("me_orange_summit", "1837", "Morris & Essex beyond Orange: the stations to Summit opened in 1837 (station infoboxes give the year only: "
     "estimated day)", WP + "Summit_station_(NJ_Transit)", "Morristown Line", (-74.36, 40.70, -74.2335, 40.80)),
    ("me_summit_west", "1838-01-01", "Morris & Essex extended to Morristown on 1 Jan 1838", WP + "Morris_and_Essex_Railroad",
     "Morristown Line", (W, 40.68, -74.36, 40.80)),
    ("dlw_boonton_main", "1870-09-12", "Lackawanna's Boonton Branch (completed 1870; the Lyndhurst, Delawanna, Passaic and Clifton station "
     "infoboxes give 12 Sep 1870), the Main Line's route south of Paterson Junction since 1963", WP + "Boonton_Branch", "Main Line",
     (-74.20, 40.75, -74.062, 40.890)),
    ("erie_paterson_connection", "1963", "Connection from the Boonton Branch to the Erie's main line at Paterson Junction: Main Line trains "
     "moved to the Boonton Branch south of Paterson in 1963 (year only: estimated day; the ends of the connection are where "
     "OpenHistoricalMap's ways end)", WP + "Main_Line_(NJ_Transit)", "Main Line", (-74.20, 40.890, -74.12, 40.8971)),
    ("erie_phrr_paterson", "1832-05-28", "Paterson & Hudson River Railroad: the stretch in Paterson still in use (the Paterson and Passaic "
     "(Erie) station infoboxes give 28 May 1832, the day horse-drawn service began)", WP + "Paterson_station_(NJ_Transit)", "Main Line",
     (-74.20, 40.8971, -74.12, 40.9155)),
    ("erie_paterson_ramapo", "1848-10-19", "Paterson & Ramapo Railroad, Paterson - Suffern (the Glen Rock, Ramsey and Mahwah station infoboxes give "
     "19 Oct 1848; OpenHistoricalMap 17 Oct 1848; the railroad's own article says fall 1849)", WP + "Mahwah_station", "Main Line",
     (-74.20, 40.9155, -74.08, 41.112)),
    ("erie_suffern_west", "1841-09-23", "New York & Erie Railroad, Piermont - Goshen, opened 23 Sep 1841", WP + "New_York_and_Erie_Railroad",
     "Main Line|Southern Tier Line", (W, 41.112, -74.14, N)),
    ("erie_piermont_suffern", "1841-06-30", "New York & Erie Railroad's first stretch from Piermont (the Suffern, Spring Valley and Nanuet station "
     "infoboxes give 30 Jun 1841): the remnant at Suffern", WP + "Suffern_station", "Suffern Industrial Track", None),
    ("erie_bergen_county_south", "1833", "Paterson & Hudson River Railroad across the Meadows, opened in 1833 (year only: estimated day)",
     WP + "Bergen_County_Line", "Bergen County Line", (-74.20, 40.75, NJ_E, 40.829)),
    ("erie_bergen_county_rr", "1881-10-01", "Bergen County Railroad, Rutherford - Glen Rock, opened in 1881 (year in the article; the day is "
     "OpenHistoricalMap's)", WP + "Bergen_County_Line", "Bergen County Line", (-74.20, 40.829, NJ_E, 41.0)),
    ("me_montclair_branch", "1856-06", "Newark & Bloomfield Railroad (Montclair Branch): trains from June 1856 (month only: estimated day)",
     WP + "Montclair_Branch", "Montclair Line", (-74.215, 40.74, -74.17, 40.812)),
    ("montclair_connection", "2002-09-30", "Montclair Connection between the Montclair Branch and the Boonton Line, opened 30 Sep 2002",
     WP + "Montclair-Boonton_Line", "Montclair Line", (-74.215, 40.812, -74.20, 40.8165)),
    ("nygl_montclair", "1873-01-01", "Montclair Railway / New York & Greenwood Lake (completed in 1872 per the line article; the Walnut Street, "
     "Upper Montclair, Little Falls and Mountain View station infoboxes give 1 Jan 1873)", WP + "Upper_Montclair_station", "Montclair Line",
     (-74.27, 40.8165, -74.18, 40.93)),
    ("dlw_boonton_west", "1870-09-12", "Lackawanna's Boonton Branch west of Mountain View (Lincoln Park station infobox: 12 Sep 1870)",
     WP + "Boonton_Branch", "Montclair Line|Montclair Line (Lincoln Park Controlled Siding)|Totowa Industrial Track", (W, 40.85, -74.27, 40.95)),
    ("pd_gladstone", "1872-01-29", "Passaic & Delaware Railroad from Summit (the New Providence, Murray Hill, Berkeley Heights and Gillette station "
     "infoboxes give 29 Jan 1872)", WP + "New_Providence_station", "Gladstone Branch", None),
    # ---- Erie: Pascack Valley, Northern Branch
    ("pvl_hackensack", "1861-01-21", "Hackensack & New York Railroad to Hackensack, 21 Jan 1861 (station table of the line article)",
     WP + "Pascack_Valley_Line", "Pascack Valley Line", (-74.12, 40.75, NJ_E, 40.880)),
    ("pvl_anderson", "1869-09-07", "Hackensack & New York Railroad extended within Hackensack, 7 Sep 1869 (station table of the line article)",
     WP + "Pascack_Valley_Line", "Pascack Valley Line", (-74.12, 40.880, NJ_E, 40.8945)),
    ("pvl_hillsdale", "1870-03-04", "Hackensack & New York Extension Railroad: service to Hillsdale opened 4 Mar 1870",
     WP + "Hackensack_and_New_York_Railroad", "Pascack Valley Line", (-74.12, 40.8945, NJ_E, 41.0025)),
    ("pvl_nanuet", "1871-05-27", "New Jersey & New York Railroad from Hillsdale to the Erie at Nanuet, 27 May 1871 (station table of the line article; "
     "Pearl River station infobox)", WP + "Pascack_Valley_Line", "Pascack Valley Line", (-74.12, 41.0025, NJ_E, 41.0926)),
    ("pvl_erie_piermont", "1841-06-30", "Nanuet - Spring Valley: the New York & Erie's first main line from Piermont (station infoboxes: 30 Jun 1841)",
     WP + "Spring_Valley_station_(New_York)", "Pascack Valley Line|Woodbine Yard", (-74.12, 41.0926, NJ_E, 41.14)),
    ("northern_rr", "1859-05-28", "Northern Railroad of New Jersey, opened 28 May 1859", WP + "Northern_Branch",
     "Northern Running Track", (-74.06, 40.79, -73.90, 41.07)),
    # ---- West Shore, Susquehanna
    ("west_shore_jca", "1873-07-30", "Jersey City & Albany Railroad, Ridgefield - Tappan, began operating 30 Jul 1873 (later the West Shore)",
     WP + "Jersey_City_and_Albany_Railroad", "River Subdivision", (-74.10, 40.834, -73.90, 41.022)),
    ("west_shore_haverstraw", "1880", "Jersey City & Albany Railway extended to Haverstraw in 1880 (year only: estimated day)",
     WP + "West_Shore_Railroad", "River Subdivision", (-74.10, 41.022, -73.90, 41.20)),
    ("west_shore_1883", "1883", "New York, West Shore & Buffalo: Weehawken extension and the line north of Haverstraw, completed 1883 (year only: "
     "estimated day)", WP + "River_Subdivision_(CSX_Transportation)", "River Subdivision", None),
    ("nysw_midland", "1872", "New Jersey Midland Railway: open between Jersey City and Middletown by 1872, first trains in 1871 (year only: estimated)",
     WP + "New_Jersey_Midland_Railway", "Southern Division Main Line|New York, Susquehanna and Western Railway", None),
    # ---- Central of New Jersey, Lehigh Valley, coast line
    ("cnj_raritan_valley", "1839", "Elizabethtown & Somerville Railroad: the Cranford, Westfield, Fanwood and Plainfield station infoboxes give 1839 "
     "(year only: estimated day)", WP + "Westfield_station_(NJ_Transit)", "Raritan Valley Line", (-74.425, 40.55, -74.25, 40.70)),
    ("cnj_raritan_valley_west", "1842-01", "Elizabethtown & Somerville Railroad reached Somerville at the beginning of 1842 (estimated day)",
     WP + "Elizabethtown_and_Somerville_Railroad", "Raritan Valley Line", (W, 40.50, -74.425, 40.70)),
    ("lv_lehigh_line", "1891", "Lehigh Valley Railroad's own route from South Plainfield towards Jersey City, established 1891 (year only: estimated day)",
     WP + "Lehigh_Valley_Railroad", "Lehigh Line", None),
    ("lv_oak_island", "1903", "Oak Island Yard, built by the Lehigh Valley Railroad, opened 1903 (year only: estimated day)", WP + "Oak_Island_Yard",
     "Oak Island Yard", None),
    ("njcl_perth_amboy_woodbridge", "1864-10-11", "Perth Amboy & Woodbridge Railroad, Rahway - Perth Amboy, opened 11 Oct 1864",
     WP + "Perth_Amboy_and_Woodbridge_Railroad", "North Jersey Coast Line", None),
    # ---- New York Central: Hudson and Harlem lines in Westchester (the Bronx rows are the city's)
    ("hudson_peekskill", "1849-09-29", "Hudson River Railroad to Peekskill, service from 29 Sep 1849", WP + "Hudson_Line_(Metro-North)",
     "Hudson Line", (-74.00, 40.92, -73.80, 41.287)),
    ("hudson_north", "1849-12-31", "Hudson River Railroad, Peekskill - Poughkeepsie, opened 31 Dec 1849", WP + "Hudson_River_Railroad",
     "Hudson Line", (-74.00, 41.287, -73.80, N)),
    ("harlem_tuckahoe", "1844-07", "New York & Harlem Railroad reached Tuckahoe in the summer of 1844 (estimated day)", WP + "Harlem_Line",
     "Harlem Line", (-73.90, 40.92, -73.60, 40.951)),
    ("harlem_white_plains", "1844-12-01", "New York & Harlem Railroad to White Plains, 1 Dec 1844", WP + "New_York_and_Harlem_Railroad",
     "Harlem Line", (-73.90, 40.951, -73.60, 41.033)),
    ("harlem_pleasantville", "1846-10", "New York & Harlem Railroad to Pleasantville, October 1846 (month only: estimated day)", WP + "Harlem_Line",
     "Harlem Line", (-73.90, 41.033, -73.60, 41.134)),
    ("harlem_mount_kisco", "1847-02", "New York & Harlem Railroad to Mount Kisco, February 1847 (month only: estimated day)", WP + "Harlem_Line",
     "Harlem Line", (-73.90, 41.134, -73.60, 41.209)),
    ("harlem_croton_falls", "1847-06-01", "New York & Harlem Railroad to Croton Falls, 1 Jun 1847", WP + "New_York_and_Harlem_Railroad",
     "Harlem Line", (-73.90, 41.209, -73.60, N)),
    # ---- PATH (Hudson & Manhattan Railroad) west of Grove Street; the tubes and Jersey City keep OpenHistoricalMap's days
    ("path_newark_penn", "1937-06-20", "Hudson & Manhattan realigned into Newark Penn Station with a new Harrison station, 20 Jun 1937 (Harrison "
     "station infobox; the H&M article says mid-1937)", WP + "Harrison_station_(PATH)", PATH, (-74.20, 40.72, -74.150, 40.76)),
    ("path_manhattan_transfer", "1911-10-01", "Hudson & Manhattan extended from Grove Street to Manhattan Transfer in October 1911 (the day is "
     "OpenHistoricalMap's)", WP + "Hudson_and_Manhattan_Railroad", PATH, (-74.150, 40.70, -74.0445, 40.76)),
    # ---- Hudson-Bergen Light Rail, by section (line article; Newport from the station infoboxes)
    ("hblr_8th_street", "2011-01-31", "Hudson-Bergen Light Rail to 8th Street, 31 Jan 2011", WP + "Hudson–Bergen_Light_Rail", HBLR, (-74.20, 40.63, -74.00, 40.6578)),
    ("hblr_22nd_street", "2003-11-15", "Hudson-Bergen Light Rail to 22nd Street, 15 Nov 2003", WP + "Hudson–Bergen_Light_Rail", HBLR, (-74.20, 40.6578, -74.00, 40.6718)),
    ("hblr_first", "2000-04-15", "Hudson-Bergen Light Rail, 34th Street - Exchange Place and the West Side Avenue branch, opened 15 Apr 2000",
     WP + "Hudson–Bergen_Light_Rail", HBLR, (-74.20, 40.6718, -74.00, 40.7178)),
    ("hblr_newport", "2000-11-18", "Hudson-Bergen Light Rail, Exchange Place - Newport, 18 Nov 2000 (Harborside, Harsimus Cove and Newport station infoboxes)",
     WP + "Newport_station_(Hudson–Bergen_Light_Rail)", HBLR, (-74.20, 40.7178, -74.00, 40.7285)),
    ("hblr_hoboken", "2002-09-29", "Hudson-Bergen Light Rail to Hoboken Terminal, 29 Sep 2002", WP + "Hudson–Bergen_Light_Rail", HBLR, (-74.20, 40.7285, -74.00, 40.7385)),
    ("hblr_lincoln_harbor", "2004-09-07", "Hudson-Bergen Light Rail to Lincoln Harbor, 7 Sep 2004", WP + "Hudson–Bergen_Light_Rail", HBLR, (-74.20, 40.7385, -74.00, 40.7625)),
    ("hblr_port_imperial", "2005-10-29", "Hudson-Bergen Light Rail to Port Imperial, 29 Oct 2005", WP + "Hudson–Bergen_Light_Rail", HBLR, (-74.20, 40.7625, -74.00, 40.7765)),
    ("hblr_tonnelle", "2006-02-25", "Hudson-Bergen Light Rail to Tonnelle Avenue, 25 Feb 2006", WP + "Hudson–Bergen_Light_Rail", HBLR, (-74.20, 40.7765, -74.00, 40.80)),
    # ---- Newark Light Rail (City Subway)
    ("nlr_broad_street_ext", "2006-07-17", "Newark Light Rail's Broad Street extension, 17 Jul 2006", WP + "Newark_Light_Rail", "Newark Light Rail",
     (-74.1725, 40.7385, -74.155, 40.752)),
    ("nlr_penn_station", "1937-06-20", "City Subway completed to Penn Station in 1937 (year in the article; the day is OpenHistoricalMap's)",
     WP + "Newark_Light_Rail", "Newark Light Rail", (-74.1705, 40.730, -74.155, 40.7385)),
    ("nlr_city_subway", "1935-05-26", "Newark City Subway, Broad Street (Military Park) - Heller Parkway, opened 26 May 1935 in the bed of the Morris Canal",
     WP + "Newark_Light_Rail", "Newark Light Rail", (-74.195, 40.730, -74.1705, 40.7787)),
    ("nlr_franklin_avenue", "1940-11-22", "City Subway extended to Franklin Avenue (Branch Brook Park) in 1940 (year in the article; the day is "
     "OpenHistoricalMap's)", WP + "Newark_Light_Rail", "Newark Light Rail", (-74.1765, 40.7787, -74.16, 40.7797)),
    ("nlr_grove_street", "2002-06-22", "Newark Light Rail extended to Grove Street, 22 Jun 2002 (Silver Lake and Grove Street station infoboxes)",
     WP + "Grove_Street_station_(Newark_Light_Rail)", "Newark Light Rail", (-74.20, 40.7787, -74.16, 40.80)),
    # ---- others
    ("airtrain_newark", "1996-05-31", "AirTrain Newark monorail opened 31 May 1996 (the extension to the Northeast Corridor station opened 21 Oct 2001 "
     "and is not separated here: estimated there)", WP + "AirTrain_Newark", "AirTrain Newark", None),
    ("meadowlands_line", "2009-07-26", "Meadowlands Rail Line, opened 26 Jul 2009", WP + "Meadowlands_Rail_Line", "Sports Line", None),
    ("kearny_connection", "1996", "Kearny Connection, opened 1996 (year only: estimated day)", WP + "Kearny_Connection", "Kearny Connection", None),
]
tab = ROOT / "data" / "tables" / "transit_openings.csv"
t = pd.read_csv(tab, dtype=str, keep_default_na=False)
new = pd.DataFrame([{"route_id": "cty_" + r[0], "opened": r[1], "note": r[2], "source": r[3], "system": "rail", "line": r[4],
                     "from_stop": f"{r[5][0]} {r[5][1]}" if r[5] else "", "to_stop": f"{r[5][2]} {r[5][3]}" if r[5] else "", "via": "", "closed": ""}
                    for r in ROWS])
assert new.route_id.is_unique
# the counties' rows go before the city's catch-all rows of the same line names? No: the city's rows are boxed
# to the Bronx / Manhattan, and a row without a box here names a line the city does not have.
pd.concat([t[~t.route_id.str.startswith("cty_")], new], ignore_index=True).to_csv(tab, index=False)
print(len(new), "county railroad rows;", len(t[~t.route_id.str.startswith('cty_')]) + len(new), "rows in the table")
