"""Contact sheet of random detections for the precision check by eye.

  python -I contact.py <sheet id> <out.png> [n=30] [seed=1] [--cls mark|bar] [--rejected] [--box lon0,lat0,lon1,lat1]

Each cell is 96 x 96 scan pixels (254 m) at 2.6x around one kept detection (or, with --rejected,
one rejected candidate), the detection under the cross-hair gap in the centre. Cells are numbered
row by row; the numbers and page positions are printed so a judged cell can be traced back."""
import json
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "pipeline"))
import topo_farmsteads as T

a = [v for v in sys.argv[1:] if not v.startswith("--")]
sid, out = a[0], a[1]
n = int(a[2]) if len(a) > 2 else 30
seed = int(a[3]) if len(a) > 3 else 1
cls = sys.argv[sys.argv.index("--cls") + 1] if "--cls" in sys.argv else None
res = json.loads((T.SHEET_CACHE / f"{sid}.json").read_text())
sh = T.Sheet(sid)
sh.shift = res["shift"]
want_keep = "--rejected" not in sys.argv
marks = [m for m in res["marks"] if m["keep"] == want_keep and m["cls"] != "odd" and (cls is None or m["cls"] == cls)]
if "--box" in sys.argv:
    lon0, lat0, lon1, lat1 = [float(v) for v in sys.argv[sys.argv.index("--box") + 1].split(",")]
    E, N = sh.px_to_utm([m["col"] for m in marks], [m["row"] for m in marks])
    lon, lat = sh._utm.transform(E, N, direction="INVERSE")
    marks = [m for m, lo, la in zip(marks, lon, lat) if lon0 <= lo <= lon1 and lat0 <= la <= lat1]
random.Random(seed).shuffle(marks)
marks = marks[:n]
half, z, cols = 48, 2.6, 6
cell = int(2 * half * z)
rows = (len(marks) + cols - 1) // cols
sheet = Image.new("RGB", (cols * cell, rows * cell), "white")
for i, m in enumerate(marks):
    x0, y0 = int(m["col"]) - half, int(m["row"]) - half
    im = Image.fromarray(sh.render(x0, y0, 2 * half, 2 * half)).resize((cell, cell), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    cx, cy = (m["col"] - x0) * z, (m["row"] - y0) * z
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        d.line([cx + dx * 16, cy + dy * 16, cx + dx * 30, cy + dy * 30], fill=(255, 0, 0), width=2)
    d.rectangle([0, 0, cell - 1, cell - 1], outline=(0, 0, 0))
    d.text((4, 3), f"{i + 1} {m['cls'][0]}{m['ctx'][0]}" + ("" if m["keep"] else " " + m["why"]), fill=(255, 0, 0))
    sheet.paste(im, ((i % cols) * cell, (i // cols) * cell))
    print(i + 1, m["col"], m["row"], m["cls"], m["ctx"], m["why"])
sheet.save(out)
print(out, sheet.size, "of", len([1 for m in res["marks"] if m["keep"] == want_keep]))
