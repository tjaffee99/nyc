import sys
sys.path.insert(0, "/home/user/nyc/data/research/lost_works_build"); from lwlib import *
def ll(x, y): return 40.812 - (y - 35) / 62000, -73.883 + (x - 325) / 46923
URL = "https://en.wikipedia.org/wiki/Hunts_Point,_Bronx"
B = ("BEST GUESS: {w}. Seen on the City's 1951 aerial mosaic at Hunts Point (the peninsula's gas works beside the rail yards; owner and exact years not found in any opened source): position read by eye "
     "(+-10 m), size from the pixels (+-15 %); start 1920 and end 1970 are guesses (it stands in 1951; the Hunts Point Co-operative Market was built on this ground 1967-74); height estimated from its shadow.")
rows = []
for k, nm, x, y, w, d, rot, h, mat in [("holder1", "large telescopic gas holder (about 72 m across, the long shadow shows it risen)", 660, 235, 72, 72, 0, 40, "steel"),
        ("holder2", "small round gas holder or tank", 825, 345, 36, 36, 0, 18, "steel"),
        ("shed_a", "long white-roofed retort / boiler house", 625, 362, 81, 116, 80, 16, "brick"),
        ("shed_b", "white-roofed purifier house", 687, 302, 54, 72, 80, 14, "brick"),
        ("shed_c", "long dark shed beside the road", 672, 420, 36, 100, 75, 10, "brick")]:
    la, lo = ll(x, y)
    rows.append(mk(f"bg_hunts_{k}", f"Hunts Point gas works, {nm}", 1920, 1970, la, lo, h, mat, w, d, rot, B.format(w=nm), URL))
add(rows)
