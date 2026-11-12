"""Manual registration by street crossings.
 python -I regm.py view <layer> <out.png> <sheet> [<sheet>]       sheets 700 px wide with today's street centre lines (cyan) and names, at the current fit
 python -I regm.py reg <layer> <spec.json>                         spec {"<sheet>": [[x, y, "Main Street", "Market Street"], ...]}  (x, y in the 700 px view)
reg: affine fit of the crossings (ground from today's street lines near the sheet's current position), writes gcps_own.json, then refine_buildings."""
import json, sys, os
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import njc
from njc import A, S, jl, own_p, lay_p, pid_of
import shapely
from PIL import Image, ImageDraw
def view(layer, out, sheets, w=700):
    ims = []
    names, g = S.roads(); b = shapely.bounds(g)
    for sh in sheets:
        P = A.Plate(layer, pid_of(layer, sh), verbose=False); img = P.img(); H, W = img.shape[:2]; f = W / w
        im = Image.fromarray(img).resize((w, int(H / f)), Image.LANCZOS); d = ImageDraw.Draw(im, "RGBA")
        cs = P.fwd(np.array([[0, 0], [W, 0], [W, H], [0, H]], float)); x0, y0, x1, y1 = cs[:, 0].min() - 60, cs[:, 1].min() - 60, cs[:, 0].max() + 60, cs[:, 1].max() + 60
        sel = np.flatnonzero((b[:, 2] > x0) & (b[:, 0] < x1) & (b[:, 3] > y0) & (b[:, 1] < y1))
        for i in sel:
            for ln in getattr(g[i], "geoms", [g[i]]):
                q = P.inv(np.asarray(ln.coords)) / f
                d.line([tuple(p) for p in q], fill=(0, 200, 255, 160), width=1)
                ins = [p for p in q if 30 < p[0] < w - 30 and 20 < p[1] < im.height - 20]
                if ins:
                    p = ins[len(ins) // 2]; d.text((p[0] + 2, p[1] + 1), str(names[i]).replace(" street", " st").replace(" avenue", " av"), fill=(0, 70, 255, 255))
        d.text((w // 2, 3), f"sheet {sh}", fill=(255, 0, 0, 255)); ims.append(im)
    o = Image.new("RGB", (w * len(ims), max(i.height for i in ims)), "white")
    for n, i in enumerate(ims): o.paste(i, (w * n, 0))
    o.save(out); print(out, o.size)
def reg(layer, spec):
    own = jl(own_p)
    for sh, pts in json.load(open(spec)).items():
        pid = pid_of(layer, sh); P = A.Plate(layer, pid, verbose=False); H, W = P.img().shape[:2]; f = W / 700
        c = P.fwd(np.array([[W / 2, H / 2]]))[0]
        px, xy = [], []
        for x, y, a, b in pts:
            try: xy.append(np.array(S.intersection_xy(a, b, near=tuple(c)))); px.append((x * f, y * f))
            except Exception as e: print(sh, "skipped", a, b, str(e)[:50])
        px = np.array(px); xy = np.array(xy)
        def sim(px, xy):
            u = px[:, 0] - 1j * px[:, 1]; g = xy[:, 0] + 1j * xy[:, 1]
            M = np.column_stack([u, np.ones(len(u))]); co = np.linalg.lstsq(M, g, rcond=None)[0]
            return co
        def apply(co, p):
            g = co[0] * (p[:, 0] - 1j * p[:, 1]) + co[1]; return np.column_stack([g.real, g.imag])
        co = sim(px, xy); res = np.hypot(*(apply(co, px) - xy).T)
        loo = []
        for k in range(len(px)):
            m = np.arange(len(px)) != k
            loo.append(float(np.hypot(*(apply(sim(px[m], xy[m]), px[k:k + 1]) - xy[k:k + 1])[0])) if m.sum() >= 2 else float("nan"))
        mpp = float(abs(co[0])); rot = float(np.degrees(np.angle(co[0])))
        e = own[str(pid)]
        def T(p): return apply(co, np.array([p], float))[0]
        pts = [(0, 0), (W, 0), (W, H), (0, H), (W / 2, H / 2), (W / 4, H / 4), (3 * W / 4, H / 4), (3 * W / 4, 3 * H / 4), (W / 4, 3 * H / 4)]
        e["gcps"] = [[p[0], p[1], S.lonlat(*T(p))[1], S.lonlat(*T(p))[0]] for p in pts]
        mm = .03; cs = [(W * mm, H * mm), (W * (1 - mm), H * mm), (W * (1 - mm), H * (1 - mm)), (W * mm, H * (1 - mm)), (W * mm, H * mm)]
        e["mask"] = dict(type="Polygon", coordinates=[[list(S.lonlat(*T(q))) for q in cs]]); e["placeholder"] = False
        e["fit"] = dict(kind="crossings", n=len(px), res_m=[round(float(v), 1) for v in res], loo_m=[round(v, 1) for v in loo], mpp=round(mpp, 4), rot=round(rot, 1))
        own_p.write_text(json.dumps(own))
        cf = A.WORK / layer / f"{pid}_corr.json"
        if cf.exists(): cf.unlink()
        A.regeo(layer, pid, verbose=False)
        r = A.refine_buildings(layer, pid, win_m=140.0, min_q=0.2, verbose=False)
        st = njc.pickle.load(open(A.WORK / layer / f"{pid}.pkl", "rb"))["stats"]
        print(sh, "n", len(px), "res", e["fit"]["res_m"], "loo", e["fit"]["loo_m"], "mpp", e["fit"]["mpp"], "| bld", r.get("kind"), r.get("shift_median"), "coincide", st["coincide"], st.get("off_median_m"), flush=True)
if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "view": view(a[1], a[2], a[3:])
    else: reg(a[1], a[2])
