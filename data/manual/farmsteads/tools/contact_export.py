"""Contact sheet of random exported features of one sheet (the precision check of the published file).

  python -I contact_export.py <sheet id> <out.png> [n=36] [seed=1] [--confidence high|medium|low]

Cells as in contact.py; the label gives the cell number, first/last year and confidence. The cell
is cut from the sheet named (for a building on two editions: the one asked for)."""
import json
import random
import sys
from pathlib import Path

import pyproj
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "pipeline"))
import topo_farmsteads as T

a = [v for v in sys.argv[1:] if not v.startswith("--")]
sid, out = a[0], a[1]
n = int(a[2]) if len(a) > 2 else 36
seed = int(a[3]) if len(a) > 3 else 1
conf = sys.argv[sys.argv.index("--confidence") + 1] if "--confidence" in sys.argv else None
fc = json.loads((T.OUT_DIR / "farmsteads.geojson").read_text())["features"]
fc = [f for f in fc if sid in f["properties"]["sheet"].split("+") and (conf is None or f["properties"]["confidence"] == conf)]
total = len(fc)
random.Random(seed).shuffle(fc)
fc = fc[:n]
sh = T.Sheet(sid)
sh.shift = json.loads((T.SHEET_CACHE / f"{sid}.json").read_text())["shift"]
utm = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32618", always_xy=True)
half, z, cols = 48, 2.6, 6
cell = int(2 * half * z)
sheet = Image.new("RGB", (cols * cell, ((len(fc) + cols - 1) // cols) * cell), "white")
for i, f in enumerate(fc):
    p = f["properties"]
    E, N = utm.transform(*f["geometry"]["coordinates"])
    c, r = sh.utm_to_px(E, N)
    x0, y0 = int(c) - half, int(r) - half
    im = Image.fromarray(sh.render(x0, y0, 2 * half, 2 * half)).resize((cell, cell), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    cx, cy = (c - x0) * z, (r - y0) * z
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        d.line([cx + dx * 16, cy + dy * 16, cx + dx * 30, cy + dy * 30], fill=(255, 0, 0), width=2)
    d.rectangle([0, 0, cell - 1, cell - 1], outline=(0, 0, 0))
    d.text((4, 3), f"{i + 1} {p['first_year'] % 100}-{p['last_year'] % 100} {p['confidence'][0]} {p['kind'][0]}", fill=(255, 0, 0))
    sheet.paste(im, ((i % cols) * cell, (i // cols) * cell))
    print(i + 1, p["id"], p["confidence"], p["kind"], p["first_year"], p["last_year"])
sheet.save(out)
print(out, sheet.size, "of", total)
