"""Plate thumbnail with today's street centre lines (cyan) and a ground grid: python -I view.py <layer> <plate> <out.png> [width_px]"""
import sys, numpy as np
from pathlib import Path
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import atlas as A, shapely
S = A.S
layer, pid, out = sys.argv[1:4]; wpx = int(sys.argv[4]) if len(sys.argv) > 4 else 1500
P = A.Plate(layer, pid, verbose=False); img = P.img(); H, W = img.shape[:2]
f = W / wpx
im = Image.fromarray(img).resize((wpx, int(H / f)), Image.LANCZOS); d = ImageDraw.Draw(im, "RGBA")
c = P.fwd(np.array([[W / 2, H / 2]]))[0]
names, g = S.roads(); b = shapely.bounds(g)
r = 450
sel0 = (b[:, 2] > c[0] - r) & (b[:, 0] < c[0] + r) & (b[:, 3] > c[1] - r) & (b[:, 1] < c[1] + r)
g = g[sel0]
nm = np.array(names)[(b[:, 2] > c[0] - r) & (b[:, 0] < c[0] + r) & (b[:, 3] > c[1] - r) & (b[:, 1] < c[1] + r)] if False else None
sel = (b[:, 2] > c[0] - r) & (b[:, 0] < c[0] + r) & (b[:, 3] > c[1] - r) & (b[:, 1] < c[1] + r)
nm = np.array(names)[sel]
for x, n in zip(g, nm):
    for ln in getattr(x, "geoms", [x]):
        q = P.inv(np.asarray(ln.coords)) / f
        d.line([tuple(p) for p in q], fill=(0, 200, 255, 200), width=2)
        ins = [p for p in q if 60 < p[0] < wpx - 120 and 40 < p[1] < im.height - 40]
        if ins:
            p = ins[len(ins) // 2]; d.text((p[0] + 3, p[1] + 2), str(n).replace(" street", "").replace(" avenue", " av"), fill=(0, 90, 255, 255))
im.save(out); print(out, im.size)
