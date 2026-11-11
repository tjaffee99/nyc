import sys
sys.path.insert(0, "/home/user/nyc/data/research/lost_works_build"); from lwlib import *
H = "https://en.wikipedia.org/wiki/Hoboken,_New_Jersey"
rows = []
# piers: east-west decks, west end at the old bulkhead (River Street), x centre -74.0281
for i, (nm, lat, y0, y1, ev) in enumerate([
        ("Hamburg-American pier (southern, foot of about 1st Street)", 40.7378, 1901, 1960, "the HAL piers lay south of the North German Lloyd piers; Nos. 5 and 6 burned in 1921, No. 4 in 1944 (Wikipedia, Hoboken piers)"),
        ("Hamburg-American pier (middle)", 40.7391, 1901, 1960, "as above"),
        ("North German Lloyd pier (foot of 3rd Street, rebuilt in steel after the fire of 30 June 1900)", 40.7404, 1901, 1960, "the Norddeutscher Lloyd piers at the foot of 3rd and 4th Streets burned on 30 June 1900 (Wikipedia, Hoboken)"),
        ("North German Lloyd pier (foot of 4th Street)", 40.7417, 1901, 1960, "as above"),
        ("North German Lloyd pier (foot of 5th Street)", 40.7430, 1901, 1960, "as above")], 1):
    la, lo = lat, -74.0256
    rows.append(mk(f"bg_hoboken_pier_{i}", f"Hoboken: {nm}", y0, y1, la, lo, 9, "wood", 235, 28, 0,
        f"BEST GUESS: pier with its shed, Hoboken waterfront. {ev}. No plan, length or exact position was found: the pier is put at the foot of its street (north-south position good to about 60 m), "
        "about 235 m long and 28 m wide (a steel pier of 1901-05 of the usual size, ESTIMATED), shed 9 m high, drawn from the bulkhead (about where Sinatra Drive runs) east into the river. "
        "Years: the first piers were built in the 1860s; this row starts at the rebuilding after the fire (1901), and its end 1960 (the lines left Hoboken in the 1960s-70s) is a guess.", H))
rows.append(mk("bg_hoboken_pier_pre1901", "Hoboken: North German Lloyd piers and sheds before the fire of 1900 (one box for three piers)", 1868, 1900, 40.7416, -74.0258, 8, "wood", 215, 300, 0,
    "BEST GUESS: the three North German Lloyd wooden piers at the foot of 3rd and 4th Streets that burned on 30 June 1900 (Wikipedia, Hoboken) are drawn as one low block 215 x 300 m "
    "(the fire ran over 'a third of a mile' of piers); position good to about 80 m, plan, size and the 1868 start (the line's move to Hoboken: a guess) NOT known; height 8 m estimated.", H))
C = (40.7502, -74.0246)
B = ("BEST GUESS: {w}. The Maxwell House coffee plant stood on the Hoboken waterfront at 10th-12th Streets, built 1939 on the Elysian Fields ground and closed in March 1992 (Wikipedia 'Maxwell House'; 24 acres); "
     "no plan was found and no traced layer covers the made land east of Hudson Street. The plant is put on the empty ground between 10th and 12th Streets and the river (good to about 70 m); size, number of buildings and heights are ESTIMATED; "
     "the end year is a guess (the buildings came down for the condominium conversion of the 1990s-2010s).")
for k, nm, dx, dy, w, d, h, y0, y1 in [("main", "main roasting and packing building with the rooftop sign", 0, 0, 150, 70, 28, 1939, 2002),
                                    ("warehouse", "green-coffee warehouse", -10, 90, 120, 40, 18, 1939, 2002),
                                    ("power", "boiler and power house", 70, -70, 45, 35, 22, 1939, 2002),
                                    ("silos", "storage silos block", -80, -75, 50, 30, 30, 1945, 2002)]:
    la, lo = off(C[0], C[1], dx, dy)
    rows.append(mk(f"bg_hoboken_maxwell_{k}", f"Maxwell House plant, Hoboken: {nm}", y0, y1, la, lo, h, "brick", w, d, 0, B.format(w=nm), "https://en.wikipedia.org/wiki/Maxwell_House"))
Y = (40.7538, -74.0238)
for k, (dx, dy, w, d) in enumerate([(0, 0, 90, 28), (-5, 60, 110, 26), (0, 115, 70, 30)], 1):
    la, lo = off(Y[0], Y[1], dx, dy)
    rows.append(mk(f"bg_hoboken_yard_shop_{k}", f"Hoboken shipyard (Tietjen & Lang drydock, later Todd, Bethlehem Steel), shop {k}", 1890, 1999, la, lo, 14, "steel", w, d, 0,
        "BEST GUESS: a shop or shed of the shipyard at the foot of 12th-16th Streets (Tietjen & Lang from 1884, Todd Shipyards, Bethlehem Steel; closed 1999 - Wikipedia 'Hoboken, New Jersey'). Not placed by any plan: "
        "position good to about 100 m (the shipyard's block lies north of the Maxwell House plant), size and height ESTIMATED; start 1890 and end 1999 follow the yard's life, not this building's.", H))
la, lo = 40.7449, -74.0248
rows.append(mk("bg_hoboken_stevens_castle", "Stevens Castle (Castle Stevens, Castle Point)", 1854, 1959, la, lo, 20, "stone", 45, 32, 0,
    "BEST GUESS: the Stevens family's castellated stone mansion on Castle Point, built 1853-54 and pulled down in 1959 for the Wesley J. Howe Center (Wikipedia 'Stevens Institute of Technology'). "
    "Position from the campus buildings around it (good to about 25 m); the plan of 45 x 32 m, the height (three storeys and towers) and the material are ESTIMATED from photographs described in the sources, no dimensions were found.", "https://en.wikipedia.org/wiki/Stevens_Institute_of_Technology"))
add(rows)
