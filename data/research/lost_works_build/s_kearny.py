import sys
sys.path.insert(0, "/home/user/nyc/data/research/lost_works_build"); from lwlib import *
rows = []
# ---- Western Electric Kearny Works
WE = ("BEST GUESS: {w}. Western Electric's Kearny Works (100 Central Avenue / 3 Distribution Avenue; building began 1923, cable production from 1925, groundbreaking of the great expansion 15 June 1928, "
      "3,579,000 sq ft on 144 acres, closing announced 27 January 1983, sold 21 May 1984 - Wikipedia 'Western Electric'). Many of its long loft buildings still stand along Distribution Avenue and are on the map; "
      "no plan of the buildings that were taken down was found, so these are put on the empty ground of the 144 acres east of Central Avenue and the rail spur (position good to about 120 m), "
      "in the same size and direction as the standing lofts (about 200 x 55 m, six storeys, ESTIMATED from the standing ones); start years follow the plant's building campaigns (1925-1930) and are guesses; end 1989 is a guess (demolished after the sale of 1984).")
for k, (la, lo, w, d, h, y0) in enumerate([(40.7298, -74.1062, 200, 55, 28, 1928), (40.7316, -74.1048, 190, 55, 28, 1929), (40.7283, -74.1040, 160, 50, 24, 1930), (40.7262, -74.1068, 130, 45, 24, 1928)], 1):
    rows.append(mk(f"bg_we_kearny_loft{k}", f"Western Electric Kearny Works, loft building {k} (lost)", y0, 1989, la, lo, h, "brick", w, d, -70, WE.format(w=f"loft building {k}, about {w} x {d} m"), "https://en.wikipedia.org/wiki/Western_Electric"))
rows.append(mk("bg_we_kearny_power", "Western Electric Kearny Works, power house and chimney (lost)", 1925, 1989, 40.7275, -74.1085, 24, "brick", 60, 40, -70, WE.format(w="power house, 60 x 40 m, height ESTIMATED"), "https://en.wikipedia.org/wiki/Western_Electric"))
# ---- Federal Shipbuilding: ways along the Hackensack
FED = ("BEST GUESS: {w}. Federal Shipbuilding and Dry Dock Company, Kearny Point (founded 24 July 1917 by US Steel; ways finished autumn 1917; 17 acres and 2,400 ft of Hackensack frontage in 1921; "
       "12 ways in 1921; bought by the Navy 1948 - Wikipedia 'Federal Shipbuilding and Drydock Company'). Some of the shops still stand and are on the map (Building 77); no plan of the shipways was found: "
       "they are put as parallel ways at right angles to the river on the east shore south of the shops (position good to about 100 m, spacing and length ESTIMATED: 150 m ways under gantry cranes, 8 m high). The ways were in use 1917-1948.")
for i in range(8):
    rows.append(mk(f"bg_federal_way_{i+1:02d}", f"Federal Shipbuilding (Kearny), shipway {i+1} with gantry", 1917, 1948, 40.7208 + i * 0.00068, -74.1028, 8, "steel", 150, 16, 0, FED.format(w=f"shipway {i+1} of the Kearny yard"), "https://en.wikipedia.org/wiki/Federal_Shipbuilding_and_Drydock_Company"))
# ---- Koppers Seaboard coke works
K = ("BEST GUESS: {w}. The Koppers (Seaboard) coke works at Kearny, 1917-1979 (174 acres, razed 1979, Hackensack River to the north and east, Route 7 to the south; the ground is the present Koppers Coke Peninsula "
     "- holes_nj_cities.md; Overture's brownfield polygon -74.1005..-74.0761 x 40.743..40.7496). No plan of the works was found: the buildings are put on the land strip between the turnpike and the river as a typical by-product coke plant "
     "(two long oven batteries, coal bunkers, a by-products plant, gas holder, stack); position good to about 300 m, plan, sizes, heights and the parts present ALL ESTIMATED; years follow the works' life (1917-1979).")
C = (40.7452, -74.0905)
for k, nm, dx, dy, w, d, h, rot in [("battery1", "coke oven battery 1 (160 x 18 m)", -40, 22, 160, 18, 14, 0), ("battery2", "coke oven battery 2 (160 x 18 m)", -40, -12, 160, 18, 14, 0),
        ("bunker", "coal bunker and conveyor house", -135, 5, 30, 14, 25, 0), ("byproducts", "by-products and benzol plant", 90, 8, 90, 50, 18, 0),
        ("tar", "tar distillation house", 85, -40, 40, 30, 14, 0), ("stack", "oven stack (4 m across)", -125, 25, 4, 4, 70, 0), ("holder", "round gas holder (40 m)", 160, 30, 40, 40, 25, 0)]:
    la, lo = off(C[0], C[1], dx, dy)
    rows.append(mk(f"bg_koppers_{k}", f"Koppers Seaboard coke works, Kearny: {nm}", 1917, 1979, la, lo, h, "steel" if k in ("holder",) else "brick", w, d, rot, K.format(w=nm), "https://en.wikipedia.org/wiki/Kearny,_New_Jersey"))
add(rows)
