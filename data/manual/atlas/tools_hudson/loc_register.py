"""Own control points for Library of Congress Sanborn / Brush sheets (not georeferenced): the two halves of a double
plate are joined (IIIF, pct:<p>), and control points are given as pixel positions of street intersections read off a
preview, whose ground position is computed from today's street centrelines (streets.py).
  python -I loc_register.py <spec.json>
spec: {"series": {"base": IIIF base up to the sheet suffix, "year": 1891, "prefix": "05511_07_1891-"},
       "plates": {"08": {"preview_pct": 14, "pts": [[x, y, "Street A", "Street B"], ...]}}}   (x, y in the preview of the joined plate)
Writes data/raw/atlas/nypl_u/loc_<key>.jpg (joined plate at 50 %) and entries in gcps_own.json (ids 910000 + n)."""
import json, sys, io
from pathlib import Path
import numpy as np
import requests
from PIL import Image
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "data" / "manual" / "extents" / "tools"))
import streets as S
UA = {"User-Agent": "NYCThroughTime-research/0.1"}
Image.MAX_IMAGE_PIXELS = None
spec = json.load(open(sys.argv[1]))
ser = spec["series"]
own_p = HERE / "gcps_own.json"
own = json.loads(own_p.read_text()) if own_p.exists() else {}
near = S.local(*ser.get("near", [-74.032, 40.744]))
for key, pl in spec["plates"].items():
    out = ROOT / "data" / "raw" / "atlas" / "nypl_u" / f"loc_{ser['tag']}_{key}.jpg"
    if not out.exists():
        halves = []
        for s in "LR":
            r = requests.get(f"{ser['base']}-{key}{s}/full/pct:50/0/default.jpg", headers=UA, timeout=180)
            r.raise_for_status()
            halves.append(Image.open(io.BytesIO(r.content)).convert("RGB"))
        W = halves[0].width + halves[1].width
        im = Image.new("RGB", (W, max(h.height for h in halves)), "white")
        im.paste(halves[0], (0, 0)); im.paste(halves[1], (halves[0].width, 0))
        im.save(out, quality=92)
    k = (50 / pl["preview_pct"])
    g = []
    for x, y, a, b in pl["pts"]:
        X, Y = S.intersection_xy(a, b, near=near)
        lo, la = S.lonlat(X, Y)
        g.append([x * k, y * k, la, lo])
    im = Image.open(out)
    fit = np.array([[p[0], p[1]] for p in g]); xy = np.array([S.local(p[3], p[2]) for p in g])
    A = np.column_stack([fit, np.ones(len(fit))]); C = np.linalg.lstsq(A, xy, rcond=None)[0]
    res = np.hypot(*(A @ C - xy).T)
    mpp = float(np.sqrt(abs(np.linalg.det(C[:2]))))
    # mask: the sheet's paper, 3 % in from the joined image's edges
    m = 0.03; corners = np.array([[im.width * m, im.height * m], [im.width * (1 - m), im.height * m], [im.width * (1 - m), im.height * (1 - m)], [im.width * m, im.height * (1 - m)], [im.width * m, im.height * m]])
    ll = [S.lonlat(*(np.append(c, 1) @ C)) for c in corners]
    own[f"{ser['id0']}{key}"] = dict(id=int(f"{ser['id0']}{key}"), name=f"{ser['title']}, plate {key}", year=ser["year"], imageId=f"loc_{ser['tag']}_{key}", uuid=None,
        url=ser["url"], gcps=g, mask=dict(type="Polygon", coordinates=[[list(p) for p in ll]]), description=ser["title"])
    print(key, im.size, "mpp %.3f" % mpp, "affine residuals m", np.round(res, 1).tolist(), "id", own[f"{ser['id0']}{key}"]["id"])
own_p.write_text(json.dumps(own))
