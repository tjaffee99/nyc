"""Research helper: the railroad rows (system `rail`) of data/tables/transit_openings.csv.

Standing railroad tracks are dated in pipeline/transit.py from OpenHistoricalMap's dated ways by
position. Where OHM has no dated way, or carries a modern operator date, the rows below date the
tracks by their OpenStreetMap line name (column `line`; `*` = any name) inside a box (from_stop =
"lon lat" south-west corner, to_stop = north-east corner; empty = anywhere in the map).

    ../../../../.venv/bin/python build_rail_rows.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
WP = "https://en.wikipedia.org/wiki/"
ROWS = [
    # route_id, opened, note, source, line, south-west, north-east
    ("rail_park_avenue", "1837-10-26", "New York & Harlem Railroad on Fourth (Park) Avenue reached Harlem on 26 Oct 1837 (the tunnel and viaduct of today are rebuildings of the 1870s and 1890s on the same line)",
     WP + "Park_Avenue_main_line", "*", "-73.985 40.7545", "-73.928 40.8105"),
    ("rail_grand_central", "1913-02-02", "Grand Central Terminal's tracks (the terminal opened 2 Feb 1913; Grand Central Depot stood here from 1871)",
     WP + "Grand_Central_Terminal", "Grand Central Terminal", "", ""),
    ("rail_harlem_bronx", "1842-09-03", "New York & Harlem Railroad from the Harlem River north to Williamsbridge, opened 3 Sep 1842 (White Plains 1 Dec 1844)",
     WP + "New_York_and_Harlem_Railroad", "Harlem Line", "-73.94 40.8105", "-73.84 40.92"),
    ("rail_new_haven", "1849-01-15", "New York & New Haven Railroad to its junction with the Harlem at Woodlawn: first train by January 1849 (month only: estimated day)",
     WP + "New_York_and_New_Haven_Railroad", "New Haven Line", "", ""),
    ("rail_hudson_riverside", "1849-09-29", "Hudson River Railroad along the Hudson, opened to Peekskill 29 Sep 1849",
     WP + "Hudson_River_Railroad", "Hudson Line", "-73.95 40.8775", "-73.89 40.92"),
    ("rail_hudson_harlem_river", "1871-07-01", "Spuyten Duyvil & Port Morris Railroad along the Harlem River, in use by 1871 (year only: estimated day)",
     WP + "Spuyten_Duyvil_and_Port_Morris_Railroad", "Hudson Line", "-73.935 40.8105", "-73.90 40.8775"),
    ("rail_west_side_north", "1849-09-29", "Hudson River Railroad down the west side of Manhattan (covered by Riverside Park in the 1930s)",
     WP + "West_Side_Line", "West Side Line", "-74.00 40.772", "-73.91 40.885"),
    ("rail_west_side_cut", "1937-07-01", "West Side Improvement: the line put in a cut south of 60th Street (year only: estimated day)",
     WP + "West_Side_Line", "West Side Line", "-74.01 40.757", "-73.98 40.772"),
    ("rail_empire_connection", "1991-04-07", "Empire Connection into Penn Station (1991; day from memory of the article: estimated)",
     WP + "West_Side_Line", "West Side Line", "-74.01 40.745", "-73.99 40.757"),
]
tab = ROOT / "data" / "tables" / "transit_openings.csv"
t = pd.read_csv(tab, dtype=str, keep_default_na=False)
new = pd.DataFrame([{"route_id": r[0], "opened": r[1], "note": r[2], "source": r[3], "system": "rail", "line": r[4],
                     "from_stop": r[5], "to_stop": r[6], "via": "", "closed": ""} for r in ROWS])
pd.concat([t[t.system != "rail"], new], ignore_index=True).to_csv(tab, index=False)
print(len(new), "railroad rows")
