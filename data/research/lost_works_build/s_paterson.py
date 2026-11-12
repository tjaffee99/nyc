import sys
sys.path.insert(0, "/home/user/nyc/data/research/lost_works_build"); from lwlib import *
P = (40.91346, -74.17884)          # the preserved erecting shop (Paterson Museum, 2 Market Street)
R = ("BEST GUESS: {w}. Rogers Locomotive and Machine Works, Paterson (Thomas Rogers 1832; Rogers Locomotive & Machine Works from 1856; absorbed by the American Locomotive Company 1901, plant buildings used as warehouses into the 1920s; "
     "only the erecting shop, now the Paterson Museum / Thomas Rogers Building, still stands - Wikipedia 'Rogers Locomotive and Machine Works'). No plan of the other shops was found: "
     "they are put on the open ground beside the preserved erecting shop (position good to about 120 m; size, plan, storeys and the start years ESTIMATED); end 1925 is a guess (the buildings were warehouses into the 1920s).")
C = ("BEST GUESS: {w}. Cooke Locomotive and Machine Works, Paterson (founded 1852 by John Cooke, absorbed by the American Locomotive Company 1901; ALCO closed the Paterson shops about 1926 - Wikipedia 'Cooke Locomotive and Machine Works'). "
     "No plan or address was found: the shop is put south-east of the Rogers works on the Passaic's east bank (position good to about 250 m); size and height ESTIMATED.")
rows = []
for k, nm, dx, dy, w, d, h, y0 in [("machine", "machine shop (three storeys, 120 x 25 m)", 60, 30, 120, 25, 14, 1850), ("boiler", "boiler shop (one storey, 80 x 25 m)", 50, -25, 80, 25, 12, 1860),
                                   ("foundry", "foundry (70 x 30 m)", 130, 20, 70, 30, 12, 1857), ("smithy", "smith shop (60 x 20 m)", 40, 70, 60, 20, 8, 1870), ("paint", "paint and finishing shop (50 x 20 m)", 120, -30, 50, 20, 10, 1880)]:
    la, lo = off(P[0], P[1], dx, dy)
    rows.append(mk(f"bg_rogers_{k}", f"Rogers Locomotive Works, Paterson: {nm}", y0, 1925, la, lo, h, "brick", w, d, 0, R.format(w=nm), "https://en.wikipedia.org/wiki/Rogers_Locomotive_and_Machine_Works"))
for k, nm, dx, dy, w, d, h, y0 in [("main", "main erecting and machine shop (100 x 30 m)", 230, -90, 100, 30, 14, 1852), ("foundry", "foundry (60 x 25 m)", 280, -40, 60, 25, 12, 1860)]:
    la, lo = off(P[0], P[1], dx, dy)
    rows.append(mk(f"bg_cooke_{k}", f"Cooke Locomotive Works, Paterson: {nm}", y0, 1926, la, lo, h, "brick", w, d, 0, C.format(w=nm), "https://en.wikipedia.org/wiki/Cooke_Locomotive_and_Machine_Works"))
add(rows)
