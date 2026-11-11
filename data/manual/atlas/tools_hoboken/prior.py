"""Hoboken 1891 plates not yet traced: fetch both halves (LoC IIIF, 50 %), join, and give each plate a PRIOR registration
(template affine of plates 8-10 + translation from the volume's index map), written to gcps_own.json as 4 pseudo control points.
The street match (atlas.py refine / locate) then finds the real place.  python -I prior.py <key> ...
"""
import json, sys, io
from pathlib import Path
import numpy as np, requests
from PIL import Image
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "data/manual/extents/tools"))
import streets as S
Image.MAX_IMAGE_PIXELS = None
UA = {"User-Agent": "NYCThroughTime-research/0.1"}
BASE = "https://tile.loc.gov/image-services/iiif/service:gmd:gmd381m:g3814m:g3814hm:g3814hm_g05511189107:05511_07_1891"
RAW = ROOT / "data/raw/atlas/hoboken"
# plate number labels on the index map (pct:20 preview, px)
IDX = {1:(820,1165),2:(828,985),3:(838,795),4:(832,632),5:(815,458),6:(800,280),7:(692,1108),8:(702,935),9:(703,800),10:(708,630),
 11:(672,462),12:(672,305),13:(565,1108),14:(565,962),15:(565,795),16:(565,630),17:(535,462),18:(535,282),19:(440,1112),20:(440,962),
 21:(437,795),22:(437,632),23:(410,465),24:(440,282),25:(310,1112),26:(325,960),27:(328,795),28:(350,632)}
old = json.load(open(HERE.parent / "tools_hudson/gcps_own.json"))
def fit(g):
    px = np.array([[p[0], p[1]] for p in g]); xy = np.array([S.local(p[3], p[2]) for p in g])
    return np.linalg.lstsq(np.column_stack([px, np.ones(len(px))]), xy, rcond=None)[0]
def centre(v):
    ring = np.array(v["mask"]["coordinates"][0][:4]); return np.array(S.local(*ring.mean(0)[::1]))
C9 = fit(old["91010009"]["gcps"]); lin = C9[:2]
cen = {p: centre(old["9101%04d" % p]) for p in (8, 9, 10)}
# scale: metres per index px along the 8-10 line
d_idx = np.array(IDX[10]) - np.array(IDX[8]); d_g = cen[10] - cen[8]
th = np.arctan2(*(cen[10] - cen[8])[::-1])  # not used
s = np.linalg.norm(d_g) / np.linalg.norm(d_idx)
up = (cen[10] - cen[8]) / np.linalg.norm(cen[10] - cen[8])      # grid "north" (index up) in local E,N
east = np.array([up[1], -up[0]])
def ground_centre(k):
    d = np.array(IDX[k]) - np.array(IDX[8])
    return cen[8] + s * (d[0] * east + (-d[1]) * up)
own_p = HERE / "gcps_own.json"
own = json.loads(own_p.read_text()) if own_p.exists() else {}
if __name__ == "__main__":
    print("index scale m/px %.3f" % s, "grid up", up.round(3))
    for key in sys.argv[1:]:
        k = int(key); key = "%04d" % k
        out = RAW / f"loc_hob1891b_{key}.jpg"
        if not out.exists():
            halves = []
            for h in "LR":
                import time
                for tr in range(8):
                    try:
                        r = requests.get(f"{BASE}-{key}{h}/full/pct:50/0/default.jpg", headers=UA, timeout=240); r.raise_for_status()
                        im_ = Image.open(io.BytesIO(r.content)).convert("RGB"); break
                    except Exception as e:
                        print("retry", key, h, str(e)[:60], flush=True); time.sleep(3 + 3 * tr)
                halves.append(im_)
            W = halves[0].width + halves[1].width
            im = Image.new("RGB", (W, max(h.height for h in halves)), "white")
            im.paste(halves[0], (0, 0)); im.paste(halves[1], (halves[0].width, 0)); im.save(out, quality=92)
        im = Image.open(out); W, H = im.size
        g0 = ground_centre(k)
        t = g0 - np.array([W / 2, H / 2]) @ lin
        pts = [(W * a, H * b) for a, b in ((.1, .1), (.9, .1), (.9, .9), (.1, .9))]
        g = []
        for x, y in pts:
            X, Y = np.array([x, y]) @ lin + t
            lo, la = S.lonlat(X, Y); g.append([x, y, la, lo])
        m = .03; cs = [(W*m, H*m), (W*(1-m), H*m), (W*(1-m), H*(1-m)), (W*m, H*(1-m)), (W*m, H*m)]
        ll = [list(S.lonlat(*(np.array(c) @ lin + t))) for c in cs]
        own["9102" + key] = dict(id=int("9102" + key), name=f"Hoboken 1891 (b), plate {k}", year=1891, imageId=f"loc_hob1891b_{key}", uuid=None,
            url="https://www.loc.gov/item/sanborn05511_007/", gcps=g, mask=dict(type="Polygon", coordinates=[ll]), description="Sanborn/Brush Hoboken 1891 vol 7")
        print(key, im.size, "prior centre", g0.round(0))
    own_p.write_text(json.dumps(own))
