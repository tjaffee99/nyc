import sys, pandas as pd
sys.path.insert(0, "/home/user/nyc/data/research/lost_works_build"); from lwlib import *
import math
t = pd.concat([pd.read_csv(ROOT / f"data/interim/lost_works_raw/tankpick_{n}.csv") for n in ("char", "char2", "char3")])
keep = []
for r in t.sort_values("ins", ascending=False).itertuples():
    if all(math.hypot((r.lon - k.lon) * 84600, (r.lat - k.lat) * 111000) > 0.6 * (r.diam_m + k.diam_m) / 2 for k in keep): keep.append(r)
t = pd.DataFrame(keep).sort_values(["lat", "lon"], ascending=False)
note = ("BEST GUESS: round oil tank of the Arthur Kill tank farm at Charleston / Rossville, Staten Island. Centre and diameter (+-3 m) read from the City's 1951 aerial mosaic "
        "(circle detector; bright roof, dark shadow) - position good to about 8 m; the owner, the opening year and the closing year are NOT known: start 1922 is a guess "
        "(ground cleared 1900-20), end 1995 a guess (a tank farm of this kind); height 12 m estimated (a 40 ft shell).")
rows = []
for i, r in enumerate(t.itertuples(), 1):
    rows.append(mk(f"bg_charleston_tank_{i:02d}", f"Arthur Kill tank farm, oil tank {i} (Charleston)", 1922, 1995, r.lat, r.lon, 12, "steel",
                   round(r.diam_m), round(r.diam_m), 0, note, "https://en.wikipedia.org/wiki/Charleston,_Staten_Island"))
import csv
d=load()
for k in [k for k in d if k.startswith('bg_charleston')]: del d[k]
w=csv.DictWriter(open(CSV,'w',newline=''),COLS); w.writeheader(); [w.writerow(v) for v in d.values()]
add(rows)
