"""Hoboken 1930 sheets: prior entries in gcps_own.json (placeholder affine: sheet x = grid east, y = grid south, 0.1 m/px) and 2-up montages
(700 px per sheet) for reading street crossings; then `reg30` replaces the placeholder.
  python -I sheets30.py prior <sheet> ... | montage <out_prefix> <sheet> ... | reg <spec.json>
spec: {"26": [[x, y, "Monroe Street", "1st Street"], ...]}  (x, y in the 700 px montage panel of that sheet)"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "data/manual/extents/tools"))
import streets as S
Image.MAX_IMAGE_PIXELS = None
RAW = ROOT / "data/raw/atlas/hoboken"
own_p = HERE / "gcps_own.json"; own = json.loads(own_p.read_text())
up = np.array([0.204, 0.979]); east = np.array([up[1], -up[0]])
lin = np.array([0.1 * east, -0.1 * up])   # px (x, y) -> (E, N) metres
def entry(k, g, ll):
    key = "%04d" % k
    own["9103" + key] = dict(id=int("9103" + key), name=f"Hoboken 1930, sheet {k}", year=1930, imageId=f"loc_hob1930_{key}", uuid=None,
        url="https://www.loc.gov/item/sanborn05511_034/", gcps=g, mask=dict(type="Polygon", coordinates=[ll]), description="Sanborn Hoboken vol. 7, 1930 re-issue corrected to 1951")
def build(k, pts_px, pts_xy):
    im = Image.open(RAW / f"loc_hob1930_{k:04d}.jpg"); W, H = im.size
    g = []
    for (x, y), (X, Y) in zip(pts_px, pts_xy):
        lo, la = S.lonlat(X, Y); g.append([x, y, la, lo])
    A = np.column_stack([np.array(pts_px), np.ones(len(pts_px))]); C = np.linalg.lstsq(A, np.array(pts_xy), rcond=None)[0]
    m = .025; cs = [(W*m, H*m), (W*(1-m), H*m), (W*(1-m), H*(1-m)), (W*m, H*(1-m)), (W*m, H*m)]
    ll = [list(S.lonlat(*(np.append(c, 1) @ C))) for c in cs]
    entry(k, g, ll); return C
if sys.argv[1] == "prior":
    c0 = np.array(S.local(-74.030, 40.745))
    for k in map(int, sys.argv[2:]):
        W, H = Image.open(RAW / f"loc_hob1930_{k:04d}.jpg").size
        px = [(W * a, H * b) for a, b in ((.1, .1), (.9, .1), (.9, .9), (.1, .9))]
        build(k, px, [np.array(p) @ lin + c0 for p in px])
elif sys.argv[1] == "montage":
    ks = list(map(int, sys.argv[3:])); ims = []
    for k in ks:
        im = Image.open(RAW / f"loc_hob1930_{k:04d}.jpg"); f = im.width / 700
        im = im.resize((700, int(im.height / f)), Image.LANCZOS); d = ImageDraw.Draw(im); d.text((330, 4), f"sheet {k}", fill=(255, 0, 0))
        ims.append(im)
    out = Image.new("RGB", (700 * len(ims), max(i.height for i in ims)), "white")
    for n, i in enumerate(ims): out.paste(i, (700 * n, 0))
    out.save(sys.argv[2]); print(sys.argv[2], out.size)
elif sys.argv[1] == "reg":
    near = S.local(-74.030, 40.745)
    for k, pts in json.load(open(sys.argv[2])).items():
        fixed = k.endswith("t"); k = int(k.rstrip("t")); W, H = Image.open(RAW / f"loc_hob1930_{k:04d}.jpg").size; f = W / 700
        px, xy = [], []
        for x, y, a, b in pts:
            try: xy.append(np.array(S.intersection_xy(a, b, near=near))); px.append((x * f, y * f))
            except Exception as e: print(k, "skipped", a, b, str(e)[:40])
        if fixed:   # collinear points: rotation and scale of the good sheets (mean of their fits), translation from the points
            Cs = [np.array([[0.0] * 2] * 3)]
            L_ = np.mean([np.array(json.loads(Path(HERE / "lin_mean.json").read_text()))], 0)
            tt = np.mean(np.array(xy) - np.array(px) @ L_, 0); C = np.vstack([L_, tt]); build_fixed = True
            m = .025; cs = [(W*m, H*m), (W*(1-m), H*m), (W*(1-m), H*(1-m)), (W*m, H*(1-m)), (W*m, H*m)]
            pp = [(0, 0), (W, 0), (W, H), (0, H)]; g = []
            for (x, y) in pp:
                X, Y = np.array([x, y]) @ L_ + tt; lo, la = S.lonlat(X, Y); g.append([x, y, la, lo])
            entry(k, g, [list(S.lonlat(*(np.append(c, 1) @ C))) for c in cs])
        else:
            C = build(k, px, xy)
        res = np.hypot(*(np.column_stack([np.array(px), np.ones(len(px))]) @ C - np.array(xy)).T)
        print(k, "mpp %.3f" % np.sqrt(abs(np.linalg.det(C[:2]))), "res m", res.round(1).tolist())
own_p.write_text(json.dumps(own))
