"""Contact sheets of the landmark meshes (axonometric, painter's algorithm) for eyeballing.

  python render.py <out.png> <cellw> <cellh> <cols> id[:zmin[:az[:el]]] ...
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
lms = {l['id']: l for l in json.loads((HERE / 'mesh.json').read_text())}
out, cw, ch, ncol = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
specs = sys.argv[5:]
rows = math.ceil(len(specs) / ncol)
img = Image.new('RGB', (cw * ncol, ch * rows), (236, 240, 244))
dr = ImageDraw.Draw(img)
L = np.array([-0.45, -0.55, 0.7]); L /= np.linalg.norm(L)
for k, spec in enumerate(specs):
    parts = spec.split(':')
    ids = parts[0].split('+')
    zmin = float(parts[1]) if len(parts) > 1 and parts[1] else -1
    az = float(parts[2]) if len(parts) > 2 and parts[2] else 215.0   # camera looks from the south-west-ish
    el = float(parts[3]) if len(parts) > 3 and parts[3] else 18.0
    tris = np.concatenate([np.array(lms[i]['pos'], float).reshape(-1, 3, 3) for i in ids])
    cols = np.concatenate([np.array(lms[i]['col'], float).reshape(-1, 3, 3)[:, 0, :] for i in ids])
    keep = tris[:, :, 2].max(axis=1) >= zmin
    tris, cols = tris[keep], cols[keep]
    a, e = math.radians(az), math.radians(el)
    # camera sits at azimuth az (compass, from north clockwise) looking at the model
    right = np.array([-math.cos(a), math.sin(a), 0.0])
    fwd = np.array([-math.sin(a), -math.cos(a), 0.0])  # horizontal view direction
    X = tris @ right
    D = tris @ fwd
    Y = tris[:, :, 2] * math.cos(e) + (-D) * math.sin(e)
    depth = D.mean(axis=1) * math.cos(e) + tris[:, :, 2].mean(axis=1) * math.sin(e)
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    nl = np.linalg.norm(n, axis=1); nl[nl == 0] = 1
    shade = 0.5 + 0.5 * np.abs((n / nl[:, None]) @ L)
    x0, x1, y0, y1 = X.min(), X.max(), max(Y.min(), zmin * math.cos(e) - 5 if zmin > 0 else Y.min()), Y.max()
    s = min((cw - 16) / max(x1 - x0, 1e-6), (ch - 30) / max(y1 - y0, 1e-6))
    ox = (k % ncol) * cw + cw / 2 - s * (x0 + x1) / 2
    oy = (k // ncol) * ch + ch - 8 + s * y0
    for i in np.argsort(-depth):
        pts = [(ox + s * X[i, j], oy - s * Y[i, j]) for j in range(3)]
        c = tuple(int(v) for v in np.clip(cols[i] * shade[i], 0, 255))
        dr.polygon(pts, fill=c)
    dr.text(((k % ncol) * cw + 4, (k // ncol) * ch + 3), ids[0] + (f' z>{zmin:.0f}' if zmin > 0 else '') + f' az{az:.0f}', fill=(40, 40, 40))
img.save(out)
print('saved', out, img.size)
