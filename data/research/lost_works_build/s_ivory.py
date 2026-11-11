import sys, math, pandas as pd
sys.path.insert(0, "/home/user/nyc/data/research/lost_works_build"); from lwlib import *
def ll(x, y): return 40.641 - (y - 35) / 106857, -74.1865 + (x - 305) / 81250
URL = "https://en.wikipedia.org/wiki/Port_Ivory,_Staten_Island"
B = ("BEST GUESS: {what}. Outline and position read by eye from the City's 1951 aerial mosaic of the Procter & Gamble works at Port Ivory (+-12 m, plan +-20 %; the roofs are in shadow and overlap, no plan of the works was found). "
     "Years are NOT known: the works ran 1907-1991 (Wikipedia); this building's start 1915 is a guess and it ends with the works. Height ESTIMATED from the shadow length / type of building.")
rows = []
spec = [        ("power", "Power house and boiler house", 760, 487, 70, 50, 18, 22, "brick"),
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
more = []
g2 = [(680,622),(706,622),(732,622),(668,640),(694,640),(720,640),(746,640),(660,658),(686,658),(712,658),(738,658),(757,658),(705,678),(731,678),(752,678)]
g3 = [(610,236),(618,250),(612,264),(614,278),(610,292),(576,218),(570,233),(575,250),(570,268),(566,285)]
for tag, pts, dm in (("g2", g2, 26), ("g3", g3, 19)):
    for i, (x, y) in enumerate(pts, 1):
        la, lo = ll(x, y)
        more.append(mk(f"bg_ivory_tank{tag}_{i:02d}", f"Port Ivory (Procter & Gamble works), storage tank group {tag[1]} no. {i}", 1925, 1991, la, lo, 10, "steel", dm, dm, 0,
                       "BEST GUESS: one tank of a visible group of round tanks (15 in a staggered block, or two columns of 5), position read by eye from the City's 1951 aerial mosaic (+-10 m within the group), diameter estimated from the pixels. Years NOT known: start 1925 guess, ends with the works (1991). Height 10 m estimated.", URL))
add(more)

# the two long east sheds and the rail shed coincide with real footprints (assessor 1934; city demolition 2007): not added
drop(['bg_ivory_tank_09','bg_ivory_tankg3_04','bg_ivory_tankg3_05'])
