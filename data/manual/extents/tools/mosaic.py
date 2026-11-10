"""Built-up area from a multi-sheet plan that draws every building (Dripps 1867): each sheet is warped
with its own Map Warper control points and read by tone (classify.built_mask) inside its mask, set in
by 25 m from the neat line; the sheets' readings are merged.

  python -I mosaic.py calib <name>              # coverage in reference windows for several thresholds
  python -I mosaic.py run <name> [preview.png]  # -> tools/classified/<name>_cls.json
"""
import json, sys
from pathlib import Path
import numpy as np
import shapely, shapely.geometry as sg
sys.path.insert(0, str(Path(__file__).resolve().parent))
import shapely.affinity
import classify, warp, build, autoalign

RUNS = {
    "manhattan_1867": dict(
        # sheets 9-18 of 20: 20th St to the Harlem River (south of 20th St the city was solid by 1852)
        sheets=[8575, 8576, 8577, 8578, 8579, 8580, 8581, 8582, 8583, 8584],
        mpp=2.0, win=10, thr=0.11, close_m=16, open_m=6, hole_ha=0.6, min_ha=0.5, local_bg=160.0, preview=[8578, 8580],
        central_park=True,      # drawn with planting and rock hachures as dark as built blocks
        near_street_m=70.0,
        open_final_m=10.0,      # shore hachures and the railway along the Hudson read as strips under 20 m wide
        calib={"built_w30s": (4500, 10900, 5000, 11400), "built_e30s": (5900, 10700, 6400, 11200), "w50s": (5000, 12700, 5600, 13300),
               "e50s": (6300, 12400, 6900, 13000), "central_park": (6500, 14000, 7000, 14600), "yorkville": (7700, 14500, 8300, 15100),
               "west_70s": (5600, 14200, 6200, 14800), "harlem": (8700, 17300, 9300, 17900)},
    ),
}


def sheet_env(m, r=None):
    env = classify.to_local(sg.shape(m.rec["mask"])).buffer(0).buffer(-25)
    if (r or {}).get("central_park"):
        # Central Park from its two southern corners (59th St at 8th and 5th Avs, today's streets) and its
        # length, 51 blocks of 20 to the mile (4,104 m), along the avenues
        a = np.array(build.resolve(("Central Park South", "Central Park West", (5950, 13700)))[:2])
        b = np.array(build.resolve(("Central Park South", "5th Avenue", (6800, 13250)))[:2])
        u = (b - a) / np.hypot(*(b - a))
        n = np.array([-u[1], u[0]])
        n = n if n[1] > 0 else -n
        park = sg.Polygon([a, b, b + 4104 * n, a + 4104 * n])
        env = env.difference(park.buffer(-15))
    return env


def read_sheet(mid, r, thr=None, preview=None):
    m = warp.MapWarp(mid)
    env = sheet_env(m, r)
    x0, y0, x1, y1 = [2 * np.floor(v / 2) for v in env.bounds]
    build.VERBOSE = False
    g, rgb, d = classify.built_mask(m, (x0, y0, x1 + 2, y1 + 2), mpp=r["mpp"], win=r["win"], thr=thr or r["thr"], open_m=r["open_m"],
                                    close_m=r["close_m"], hole_ha=r["hole_ha"], min_ha=r["min_ha"], envelope=env,
                                    local_bg=r["local_bg"], not_blue=r.get("not_blue", False), verbose=False)
    if preview:
        classify.preview(rgb, (x0, y0, x1 + 2, y1 + 2), r["mpp"], [(env, (0, 170, 0)), (g, (255, 0, 0))], preview)
    # constant shift of the sheet against today's streets (the four-point fits can sit 10-30 m off):
    # windows matched within +-35 m (less than half a short block, so the block rhythm cannot alias)
    shift = (0.0, 0.0)
    try:
        b = env.buffer(-250).bounds
        sh = autoalign.windows_shift(m, b, 2.0, 500, 250, 35, min_q=3.0)
        if len(sh) >= 6:
            med = np.median(sh[:, 2:4], axis=0)
            dev = np.hypot(*(sh[:, 2:4] - med).T)
            good = dev < 12
            if good.sum() >= 6 and good.mean() >= 0.5:
                shift = tuple(float(v) for v in sh[good, 2:4].mean(0))
            print(f"   sheet {mid}: street match {len(sh)} windows, {int(good.sum())} agree, shift applied ({shift[0]:.0f}, {shift[1]:.0f}) m", flush=True)
        else:
            print(f"   sheet {mid}: street match found {len(sh)} windows - no shift applied", flush=True)
    except Exception as e:  # noqa
        print("   street match failed:", e)
    g = shapely.affinity.translate(g, *shift)
    env = shapely.affinity.translate(env, *shift)
    return m, env, g, d, shift


def main(a):
    name = a[1]
    r = RUNS[name]
    if a[0] == "calib":
        for mid in r["sheets"]:
            m = warp.MapWarp(mid, verbose=False)
            env = sheet_env(m)
            for k, w in r["calib"].items():
                wb = sg.box(*w)
                if not env.contains(wb):
                    continue
                rgb = m.render(*w, r["mpp"])
                d, paper = classify.darkness(rgb, r["win"] / r["mpp"], local_bg_px=r["local_bg"] / r["mpp"])
                print(f"sheet {mid} {k:14s} paper {paper:.0f}  share darker than 0.10/0.14/0.17/0.20/0.25: " + " ".join(f"{(d > t).mean():.2f}" for t in (0.10, 0.14, 0.17, 0.20, 0.25)))
        return
    parts, envs = [], []
    for mid in r["sheets"]:
        m, env, g, d, shift = read_sheet(mid, r, preview=(a[2].replace(".png", f"_{mid}.png") if len(a) > 2 and mid in r.get("preview", []) else None))
        print(f"sheet {mid}: {m.rec['name'][:40]} read {env.area / 1e4:.0f} ha, built {g.area / 1e4:.0f} ha, residual {m.cv_rms:.0f} m", flush=True)
        parts.append(g)
        envs.append(env)
    g = shapely.union_all(parts).buffer(10).buffer(-10).buffer(0)       # close the sheet seams
    if r.get("near_street_m"):
        # shore hachures and the river-side railway read as long strips: keep only ground within
        # near_street_m of a street of today (the parkways along both rivers are not in the street set)
        import streets as S
        names, sg_ = S.roads()
        b = shapely.bounds(sg_)
        bb = g.bounds
        sel = (b[:, 2] > bb[0]) & (b[:, 0] < bb[2]) & (b[:, 3] > bb[1]) & (b[:, 1] < bb[3])
        near = shapely.union_all(shapely.buffer(sg_[sel], r["near_street_m"], quad_segs=2))
        g = g.intersection(near).buffer(0)
    if r.get("open_final_m"):
        g = g.buffer(-r["open_final_m"]).buffer(r["open_final_m"]).buffer(0)
        g = shapely.union_all([p for p in getattr(g, "geoms", [g]) if p.area >= r["min_ha"] * 1e4])
    cov = shapely.union_all(envs)
    (build.CLASSIFIED / f"{name}_cls.json").write_text(json.dumps(sg.mapping(g.simplify(2.0))))
    (build.CLASSIFIED / f"{name}_coverage.json").write_text(json.dumps(sg.mapping(cov.simplify(5.0))))
    print(name, "built %.0f ha in %.0f ha read" % (g.area / 1e4, cov.area / 1e4))


if __name__ == "__main__":
    main(sys.argv[1:])
