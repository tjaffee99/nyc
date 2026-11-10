"""Run the detector on one window of a sheet and draw the result (tuning / checking by eye).

  python -I try_window.py <sheet id> <lon> <lat> <half-width m> <out.png> [zoom]
green = mark kept, blue = bar kept, red = rejected (first letters of the reason)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "pipeline"))
import topo_farmsteads as T

sid, lon, lat, half, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
z = float(sys.argv[6]) if len(sys.argv) > 6 else 2
sh = T.Sheet(sid)
c, r = sh.lonlat_to_px(lon, lat)
n = int(2 * half / sh.m_per_px)
x0, y0 = int(c - n / 2), int(r - n / 2)
rgb = sh.render(x0, y0, n, n)
thr, thrl, paper, inkv = T.ink_threshold(sh.render(sh.W // 2 - 1500, sh.H // 2 - 1500, 3000, 3000))
ms = T.detect_tile(rgb, thr, thrl)
img = Image.fromarray(rgb).resize((int(n * z), int(n * z)), Image.LANCZOS)
d = ImageDraw.Draw(img)
for m in ms:
    col = (0, 170, 0) if m["keep"] and m["cls"] == "mark" else ((0, 0, 255) if m["keep"] else (255, 0, 0))
    px, py = m["col"] * z, m["row"] * z
    d.ellipse([px - 6 * z, py - 6 * z, px + 6 * z, py + 6 * z], outline=col, width=2)
    if not m["keep"]:
        d.text((px + 6 * z, py - 5), m["why"][:3], fill=(255, 0, 0))
img.save(out)
print(sid, "thr", round(thr), round(thrl), "paper", paper, "ink", inkv, "cands", len(ms), "kept", sum(m["keep"] for m in ms))
