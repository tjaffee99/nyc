import sys, math
sys.path.insert(0, "/home/user/nyc/data/research/lost_works_build"); from lwlib import *
URL = "https://en.wikipedia.org/wiki/Elizabeth,_New_Jersey"
A = (40.6447, -74.1965); Bp = (40.6485, -74.1905)          # axis of the very large post-1982 building on the old works ground
lat0 = (A[0] + Bp[0]) / 2; kx = 111320 * math.cos(math.radians(lat0)); ky = 110540
L = math.hypot((Bp[1] - A[1]) * kx, (Bp[0] - A[0]) * ky); ux = (Bp[1] - A[1]) * kx / L; uy = (Bp[0] - A[0]) * ky / L
rot = -math.degrees(math.atan2(uy, ux))         # clockwise-from-east value of the axis direction (negative = rises to the north-east)
B = ("BEST GUESS: {w}. The Singer Manufacturing Company's Elizabethport works (opened 1873, 32 acres 'First to Fifth Street along Trumbull', the largest single plant of its day; the company left Elizabeth in 1982 - Wikipedia 'Singer Corporation', 'Elizabeth, New Jersey'; "
     "the original brick building still stands). Trumbull Street is gone from the map and no plan was found: the works is put on the ground of the very large building built after 1982 on the Elizabethport waterfront side (about 650 m long, on the grid's axis), "
     "at the end of Butler Street; position good to about 120 m, the plan, the number of buildings, sizes and heights are invented in the manner of a multi-storey brick loft works. Years: start a guess within the works' life, end 1983 (demolition after the 1982 closing) a guess.")
spec = [("loft1", "brick loft, north-west range (about 150 x 24 m, five storeys)", 0.22, 42, 150, 24, 20, 1873),
        ("loft2", "brick loft, north-west range (about 150 x 24 m, five storeys)", 0.50, 42, 150, 24, 20, 1880),
        ("loft3", "brick loft, north-west range (about 150 x 24 m, four storeys)", 0.78, 42, 150, 24, 16, 1892),
        ("loft4", "brick loft, south-east range (about 150 x 24 m, five storeys)", 0.30, -42, 150, 24, 20, 1887),
        ("loft5", "brick loft, south-east range (about 150 x 24 m, five storeys)", 0.58, -42, 150, 24, 20, 1900),
        ("foundry", "foundry and machine shop (long low shed, 90 x 40 m)", 0.08, 0, 90, 40, 12, 1873),
        ("power", "power house (40 x 30 m)", 0.93, 0, 40, 30, 14, 1890),
        ("stack", "power-house chimney (5 m across)", 0.97, 25, 5, 5, 50, 1890)]
rows = []
for k, nm, t, nrm, w, d, h, y0 in spec:
    x = t * L * ux - nrm * uy; y = t * L * uy + nrm * ux          # normal = left of the axis (north-west)
    la = A[0] + y / ky; lo = A[1] + x / kx
    rows.append(mk(f"bg_singer_{k}", f"Singer works, Elizabethport: {nm}", y0, 1983, la, lo, h, "brick", w, d, round(rot, 1), B.format(w=nm), URL))
add(rows)
