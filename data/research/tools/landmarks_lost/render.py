import json, sys, math
import numpy as np
from PIL import Image, ImageDraw
M = json.load(open('/home/user/nyc/data/interim/landmarks_lost/meshes.json'))
def render(mid, size=460, view='top'):
    m = M[mid]; P = np.array(m['pos'], float).reshape(-1, 3, 3); C = np.array(m['col'], float).reshape(-1, 3, 3)[:, 0, :]
    n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); ln = np.linalg.norm(n, axis=1); ln[ln == 0] = 1; n = n / ln[:, None]
    L = np.array([0.4, -0.5, 0.77]); shade = 0.55 + 0.45 * np.abs(n @ L)
    if view == 'top':
        U = P[:, :, 0]; V = P[:, :, 1]; depth = P[:, :, 2].max(1)
    elif view == 'south':   # looking north: x right, z up
        U = P[:, :, 0]; V = P[:, :, 2]; depth = -P[:, :, 1].mean(1)
    else:                   # iso from the south-west
        a = math.radians(35); e = math.radians(35)
        xr = P[:, :, 0] * math.cos(a) + P[:, :, 1] * math.sin(a); yr = -P[:, :, 0] * math.sin(a) + P[:, :, 1] * math.cos(a)
        U = xr; V = yr * math.sin(e) + P[:, :, 2] * math.cos(e); depth = -(yr * math.cos(e) - P[:, :, 2] * math.sin(e)).mean(1)
    rings = m['replaces'] if view == 'top' else []
    allu = np.concatenate([U.ravel()] + [np.array(r)[:, 0] for r in rings]); allv = np.concatenate([V.ravel()] + [np.array(r)[:, 1] for r in rings])
    u0, u1, v0, v1 = allu.min(), allu.max(), allv.min(), allv.max(); s = (size - 24) / max(u1 - u0, v1 - v0, 1e-6)
    im = Image.new('RGB', (size, size), (235, 238, 240)); d = ImageDraw.Draw(im)
    X = lambda u: 12 + (u - u0) * s; Y = lambda v: size - 12 - (v - v0) * s
    for i in np.argsort(depth):
        col = tuple(int(min(255, c * shade[i])) for c in C[i])
        d.polygon([(X(U[i, k]), Y(V[i, k])) for k in range(3)], fill=col)
    for r in rings:
        pts = [(X(x), Y(y)) for x, y in r]; d.line(pts + [pts[0]], fill=(220, 30, 30), width=1)
    d.text((6, 4), f"{mid} [{view}]", fill=(0, 0, 0))
    return im
ids = sys.argv[2:]; views = ['top', 'iso']
W = 460; sheet = Image.new('RGB', (W * len(views), W * len(ids)), 'white')
for r, mid in enumerate(ids):
    for c, v in enumerate(views): sheet.paste(render(mid, W, v), (c * W, r * W))
sheet.save(sys.argv[1]); print(sheet.size)
