import sys, math, pandas as pd
sys.path.insert(0, "/home/user/nyc/data/research/lost_works_build"); from lwlib import *
def ll(x, y): return 40.641 - (y - 35) / 106857, -74.1865 + (x - 305) / 81250
URL = "https://en.wikipedia.org/wiki/Port_Ivory,_Staten_Island"
B = ("BEST GUESS: {what}. Outline and position read by eye from the City's 1951 aerial mosaic of the Procter & Gamble works at Port Ivory (+-12 m, plan +-20 %; the roofs are in shadow and overlap, no plan of the works was found). "
     "Years are NOT known: the works ran 1907-1991 (Wikipedia); this building's start 1915 is a guess and it ends with the works. Height ESTIMATED from the shadow length / type of building.")
rows = []
spec = [("shed_a", "East storage and packing shed (longest roof on the photograph)", 820, 337, 265, 52, 84, 12, "brick"),
        ("shed_b", "East second shed", 868, 348, 182, 36, 88, 12, "brick"),
        ("power", "Power house and boiler house", 760, 487, 70, 50, 18, 22, "brick"),
        ("rail_shed", "Long shed beside the rail spur", 715, 185, 210, 30, 82, 12, "brick"),
        ("process_1", "Soap-making block (kettle house)", 552, 420, 90, 70, 0, 20, "brick"),
        ("process_2", "Process building north", 615, 335, 80, 40, 80, 18, "brick"),
        ("process_3", "Process building south-west", 530, 545, 45, 45, 0, 15, "brick"),
        ("shop", "Shop / warehouse near the south tanks", 715, 525, 55, 40, 35, 12, "brick")]
for k, nm, x, y, w, d, rot, h, mat in spec:
    la, lo = ll(x, y)
    rows.append(mk(f"bg_ivory_{k}", f"Port Ivory (Procter & Gamble works), {nm}", 1915, 1991, la, lo, h, mat, w, d, rot, B.format(what=nm.lower()), URL))
la, lo = ll(655, 303)
rows.append(mk("bg_ivory_stack", "Port Ivory (Procter & Gamble works), power-house stack", 1915, 1991, la, lo, 55, "brick", 6, 6, 0,
               "BEST GUESS: round stack read from the smoke plume on the City's 1951 aerial (+-15 m); diameter 6 m and height 55 m ESTIMATED; years follow the works (1907-1991), start 1915 a guess. A round stack is drawn as a 6 m column (named 'tank' below to be drawn round).", URL))
n = 0
for nm in ("ivt1", "ivt2"):
    t = pd.read_csv(ROOT / f"data/interim/lost_works_raw/tankpick_{nm}.csv")
    for r in t.itertuples():
        if any(abs(r.lat - q["lat"]) < 2e-5 and abs(r.lon - q["lon"]) < 2e-5 for q in [dict(lat=float(x["lat"]), lon=float(x["lon"])) for x in rows if x["id"].startswith("bg_ivory_tank")]): continue
        n += 1
        rows.append(mk(f"bg_ivory_tank_{n:02d}", f"Port Ivory (Procter & Gamble works), storage tank {n}", 1925, 1991, r.lat, r.lon, 10, "steel", round(r.diam_m), round(r.diam_m), 0,
                       "BEST GUESS: round tank (oil or tallow storage) of the Port Ivory works, centre and diameter (+-3 m) read from the City's 1951 aerial mosaic by a circle detector (about 15 of the 45 tanks visible were picked up; the rest are not drawn). Years NOT known: start 1925 guess, ends with the works (1991). Height 10 m estimated.", URL))
rows[8]["shape_note"] = rows[8]["shape_note"].replace(" A round stack is drawn as a 6 m column (named 'tank' below to be drawn round).", "")
rows[8]["name"] = "Port Ivory (Procter & Gamble works), power-house stack (round tank-like stack)"
add(rows)
