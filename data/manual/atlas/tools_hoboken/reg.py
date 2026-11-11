"""Own control points for a plate from street crossings read off the 1500 px preview (view.py): python -I reg.py <spec.json>
spec: {"13": [[x, y, "Garden Street", "2nd Street"], ...]}  (preview x, y); replaces the plate's prior in gcps_own.json."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "data/manual/extents/tools"))
import streets as S
Image.MAX_IMAGE_PIXELS = None
own_p = HERE / "gcps_own.json"; own = json.loads(own_p.read_text())
near = S.local(-74.030, 40.745)
for k, pts in json.load(open(sys.argv[1])).items():
    key = "%04d" % int(k); e = own["9102" + key]
    W, H = Image.open(ROOT / f"data/raw/atlas/hoboken/loc_hob1891b_{key}.jpg").size
    f = W / 1500
    g = []
    for x, y, a, b in pts:
        X, Y = S.intersection_xy(a, b, near=near); lo, la = S.lonlat(X, Y); g.append([x * f, y * f, la, lo])
    px = np.array([[p[0], p[1]] for p in g]); xy = np.array([S.local(p[3], p[2]) for p in g])
    A = np.column_stack([px, np.ones(len(px))]); C = np.linalg.lstsq(A, xy, rcond=None)[0]
    res = np.hypot(*(A @ C - xy).T)
    m = .03; cs = [(W*m, H*m), (W*(1-m), H*m), (W*(1-m), H*(1-m)), (W*m, H*(1-m)), (W*m, H*m)]
    e["gcps"] = g; e["mask"] = dict(type="Polygon", coordinates=[[list(S.lonlat(*(np.append(c, 1) @ C))) for c in cs]])
    print(key, "mpp %.3f" % np.sqrt(abs(np.linalg.det(C[:2]))), "affine residuals m", res.round(1).tolist())
own_p.write_text(json.dumps(own))
