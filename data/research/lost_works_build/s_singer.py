import sys
sys.path.insert(0, "/home/user/nyc/data/research/lost_works_build"); from lwlib import *
URL = "https://en.wikipedia.org/wiki/Elizabeth,_New_Jersey"
C = (40.6446, -74.1962)
B = ("BEST GUESS: {w}. The Singer Manufacturing Company's Elizabethport works (opened 1873, 32 acres, the largest single plant of its day; the company left Elizabeth in 1982 - Wikipedia 'Singer Corporation' / 'Elizabeth, New Jersey') "
     "is not placed by any plan found: the works is put on the largest empty ground of today's map between the Elizabeth River and the south end of the Elizabethport streets, "
     "so the position is good to about 200 m at best, and the plan, size, number of buildings and heights are invented in the manner of a multi-storey brick loft works. Years: start is a guess within the works' 1873-1982 life; end 1985 (demolished after the 1982 closing) is a guess.")
spec = [("loft1", "brick loft, north range (about 150 x 22 m, five storeys)", 0, 70, 150, 22, 0, 20, 1873, "brick"),
        ("loft2", "brick loft, middle range (about 150 x 22 m, five storeys)", 0, 40, 150, 22, 0, 20, 1880, "brick"),
        ("loft3", "brick loft, south range (about 150 x 22 m, four storeys)", 0, -10, 150, 22, 0, 16, 1892, "brick"),
        ("loft4", "brick loft, east cross range (about 120 x 22 m, five storeys)", 110, 40, 22, 120, 0, 20, 1905, "brick"),
        ("foundry", "foundry and machine shop (long low shed)", -95, 5, 40, 90, 0, 12, 1873, "brick"),
        ("power", "power house", -90, -60, 40, 30, 0, 14, 1890, "brick"),
        ("stack", "power-house chimney", -55, -60, 5, 5, 0, 50, 1890, "brick")]
rows = []
for k, nm, dx, dy, w, d, rot, h, y0, mat in spec:
    la, lo = off(C[0], C[1], dx, dy)
    rows.append(mk(f"bg_singer_{k}", f"Singer works, Elizabethport: {nm}", y0, 1985, la, lo, h, mat, w, d, rot, B.format(w=nm), URL))
add(rows)
