import sys
sys.path.insert(0, "/home/user/nyc/data/research/lost_works_build"); from lwlib import *
rows = []
C = (40.7153, -74.0328)
B = ("BEST GUESS: {w}. The Colgate & Company plant (85-99 Hudson Street, Jersey City, on the Hudson waterfront; the company's works from 1847; demolished in 1985 for 30 Hudson Street, the Goldman Sachs Tower - Wikipedia 'Colgate Clock (Jersey City)'; "
     "Library of Congress HAER NJ-71-B). The works is put where the Goldman tower stands (the clock stood 1300 ft north of its present place), good to about 60 m; the number of buildings, plans and heights are ESTIMATED; start years are guesses.")
for k, nm, dx, dy, w, d, h, y0 in [("main", "main loft building with the octagonal clock on the roof (Buildings B-7 and B-8, about 100 x 32 m, six storeys)", -15, 20, 100, 32, 28, 1900),
        ("north", "north factory block", 10, 70, 80, 30, 22, 1890),
        ("south", "south factory block", 5, -35, 70, 30, 22, 1912),
        ("power", "power house and chimney", 60, 25, 30, 25, 16, 1912),
        ("pier", "waterfront shed", 75, -10, 70, 22, 8, 1925)]:
    la, lo = off(C[0], C[1], dx, dy)
    rows.append(mk(f"bg_colgate_{k}", f"Colgate plant, Jersey City: {nm}", y0, 1985, la, lo, h, "brick", w, d, 0, B.format(w=nm), "https://en.wikipedia.org/wiki/Colgate_Clock_(Jersey_City)"))
rows.append(mk("bg_roosevelt_stadium", "Roosevelt Stadium (Droyer's Point, Jersey City)", 1937, 1985, 40.7108, -74.1038, 22, "concrete", 190, 150, 0,
    "BEST GUESS: the municipal stadium (opened 23 April 1937, 24,000 seats, closed 1981, demolished 1985, replaced by Society Hill - Wikipedia 'Roosevelt Stadium'). The article's coordinates fall in the water; "
    "the street 'Roosevelt Stadium Court' of Society Hill (Overture) lies at 40.7111 N 74.1027 W and marks the ground: position good to about 100 m; the bowl is drawn as a 190 x 150 m box (a horseshoe grandstand around a field of 500 x 400 ft planned in 1929; size ESTIMATED); height 22 m estimated.", "https://en.wikipedia.org/wiki/Roosevelt_Stadium"))
rows.append(mk("bg_ruppert_stadium", "Ruppert Stadium (Newark Bears)", 1926, 1967, 40.7296, -74.1290, 18, "concrete", 155, 125, 0,
    "BEST GUESS: Ruppert Stadium (258 Wilson Avenue, Newark; opened 1926 as Davids' Stadium, 19,000 seats, demolished 1967 - Wikipedia 'Ruppert Stadium (New Jersey)'; outfield 305-365-410 ft). "
    "Wilson Avenue no longer exists there (the Turnpike spur): the place is the empty ground in the Ironbound meadow the holes list found (about -74.129, 40.728), good to about 200 m; the 155 x 125 m box is estimated from the stated field dimensions plus stands; height estimated.", "https://en.wikipedia.org/wiki/Ruppert_Stadium_(New_Jersey)"))
add(rows)
