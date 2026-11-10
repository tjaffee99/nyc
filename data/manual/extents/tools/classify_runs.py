"""Tone-classification runs: built-up blocks read from a map that hatches / shades them or draws
every building. Each run: map, box, parameters, a hand-drawn envelope (the map's own land and the
neighbourhood of the built area: field patterns, hill hachures and lettering outside it are as dark
as blocks) and open grounds to leave out. Result written to tools/classified/<name>_cls.json
(local metres) and used by snapshots.py as {"file": ...}.

  python -I classify_runs.py <name> [preview.png]
"""
import json, sys
from pathlib import Path
import shapely, shapely.geometry as sg
sys.path.insert(0, str(Path(__file__).resolve().parent))
import classify, warp, build

RUNS = {}
RUNS["manhattan_1797"] = dict(
    map_id=15327, box=(3100, 6050, 5800, 8650), mpp=1.5, win=12, thr=0.22, close_m=16, open_m=4, hole_ha=0.6, min_ha=0.3,
    envelope=[(3360, 6084), (3265, 6413), (3204, 6604), (3169, 6985), (3273, 7263), (3291, 7540), (3343, 7748), (3360, 7887),
              (3395, 8078), (3490, 8130), (3490, 8581), (3638, 8581), (3638, 8078), (3620, 7870), (3794, 7904), (3846, 7956),
              (4158, 7956), (4314, 8147), (4383, 8130), (4314, 7922), (4244, 7783), (4418, 7887), (4487, 7956), (4487, 8095),
              (4765, 8130), (4834, 8164), (4851, 8338), (4964, 8338), (4964, 8008), (5025, 7991), (5025, 7625), (5750, 7625),
              (5750, 7190), (5500, 7141), (5354, 7124), (5007, 7107), (4799, 6985), (4487, 6933), (4314, 6725), (4071, 6535), (3915, 6378),
              (3672, 6153), (3534, 6101)],
    exclude=[[("Broadway", "Barclay Street", (3760, 7250)), ("Broadway", "Chambers Street", (3969, 7494)),
              ("Centre Street", "Chambers Street", (4090, 7420)), ("Park Row", "Spruce Street", (4000, 7240))]],
)
# Burr 1834: a test only. The map tints every laid-out block alike, so this reading (1,335 ha) is the
# street grid, not the built-up area; no snapshot is made from it.
RUNS["manhattan_1834"] = dict(
    map_id=15169, box=(3000, 6000, 6800, 11200), mpp=2.0, win=12, thr=0.15, close_m=16, open_m=4, hole_ha=0.6, min_ha=0.3,
)
RUNS["manhattan_1836"] = dict(
    map_id="colton1836", box=(3000, 5900, 7200, 11600), mpp=2.0, win=18, thr=0.19, close_m=18, open_m=12, hole_ha=0.6, min_ha=0.5,
    # the map's shoreline (bulkhead line), read off the warped map to about +-30 m and kept a little
    # inside it: the water is ruled dark near the shore
    envelope=[(3209, 6337), (3160, 6660), (3225, 7040), (3320, 7420), (3377, 7800), (3434, 8180), (3529, 8560), (3586, 8940),
              (3586, 9320), (3586, 9700), (3616, 10080), (3650, 10460), (3690, 10650), (3780, 10840), (3915, 11220), (4010, 11560),
              (5000, 11560), (5000, 10900), (6130, 10900), (6130, 9950), (6470, 9950), (6470, 9472), (6500, 9168), (6680, 8940),
              (6730, 8598), (6680, 8370), (6520, 8180), (6470, 7876), (6500, 7610), (6480, 7306), (6400, 7250), (5888, 7110),
              (5280, 7075), (4976, 6980), (4634, 6830), (4140, 6566), (3760, 6357), (3570, 6262), (3418, 6148), (3266, 6125)],
    exclude=[
        # squares and grounds drawn with trees (as dark as blocks)
        [("Avenue A", "East 7th Street", (5930, 8800)), ("Avenue A", "East 10th Street", (6060, 9030)),
         ("Avenue B", "East 10th Street", (6200, 8950)), ("Avenue B", "East 7th Street", (6070, 8720))],
        [("Broadway", "Barclay Street", (3760, 7250)), ("Broadway", "Chambers Street", (3969, 7494)),
         ("Centre Street", "Chambers Street", (4090, 7420)), ("Park Row", "Spruce Street", (4000, 7240))],
        [("State Street", "Whitehall Street", (3330, 6230)), ("State Street", "Battery Place", (3190, 6460)), (3120, 6480), (3150, 6200), (3250, 6100), (3340, 6110)],
    ],
)
RUNS["manhattan_1852"] = dict(
    map_id=14758, box=(3300, 6000, 7200, 13100), mpp=2.0, win=10, thr=0.17, close_m=16, open_m=6, hole_ha=0.6, min_ha=0.5,
    local_bg=160.0, not_blue=True, open_final_m=10.0,
)
RUNS["brooklyn_1836"] = dict(
    map_id="colton1836_bk", box=(4500, 4500, 6800, 6700), mpp=2.0, win=18, thr=0.19, close_m=18, open_m=12, hole_ha=0.6, min_ha=0.5,
    # Brooklyn: the map's shore from Atlantic St round the Heights and the ferry to the Navy Yard wall, then inland
    envelope=[(4620, 5700), (4725, 5880), (4830, 6150), (4920, 6300), (5010, 6360), (5280, 6420), (5700, 6450),
              (6060, 6510), (6135, 6480), (6150, 6300), (6135, 5850), (6135, 5700), (6500, 5700), (6500, 4980), (4620, 4980)],
)
RUNS["williamsburgh_1836"] = dict(
    map_id="colton1836_bk", box=(7000, 6600, 8900, 8600), mpp=2.0, win=18, thr=0.19, close_m=18, open_m=12, hole_ha=0.6, min_ha=0.3,
    envelope=[(7140, 6780), (7155, 7140), (7215, 7500), (7335, 7800), (7680, 8175), (7920, 8490), (8400, 8490), (8760, 7710), (7950, 6780)],
)


def run(name, out_png=None, prev_boxes=None):
    r = RUNS[name]
    m = warp.MapWarp(r["map_id"])
    if r.get("envelope"):
        env = sg.Polygon([build.resolve(v)[:2] for v in r["envelope"]])
    else:   # the area the Map Warper mask keeps (the map inside its neat line)
        env = sg.box(*r["box"])
        if m.rec.get("mask"):
            env = classify.to_local(sg.shape(m.rec["mask"])).buffer(0).intersection(env)
    for ex in r.get("exclude", []):
        env = env.difference(sg.Polygon([build.resolve(v)[:2] for v in ex]))
    geom, rgb, d = classify.built_mask(m, r["box"], mpp=r["mpp"], win=r["win"], thr=r["thr"], open_m=r["open_m"],
                                       close_m=r["close_m"], hole_ha=r["hole_ha"], min_ha=r["min_ha"], envelope=env,
                                       local_bg=r.get("local_bg", 0.0), not_blue=r.get("not_blue", False))
    geom = geom.simplify(2.0)
    for add in r.get("add", []):
        geom = geom.union(sg.Polygon([build.resolve(v)[:2] for v in add]))
    for rem in r.get("remove", []):
        geom = geom.difference(sg.Polygon([build.resolve(v)[:2] for v in rem]))
    if r.get("open_final_m"):   # strips narrower than twice this: shore hachures read as built
        geom = geom.buffer(-r["open_final_m"]).buffer(r["open_final_m"])
        geom = shapely.union_all([p for p in getattr(geom, "geoms", [geom]) if p.area >= r["min_ha"] * 1e4])
    geom = geom.buffer(0)
    (build.CLASSIFIED / f"{name}_cls.json").write_text(json.dumps(sg.mapping(geom)))
    print(name, "classified area %.1f ha, parts %d" % (geom.area / 1e4, len(getattr(geom, "geoms", [geom]))))
    if out_png:
        classify.preview(rgb, r["box"], r["mpp"], [(env, (0, 170, 0)), (geom, (255, 0, 0))], out_png)
    for i, pb in enumerate(prev_boxes or []):   # closer looks: (x0, y0, x1, y1, m_per_px)
        classify.preview(m.render(*pb[:4], pb[4]), pb[:4], pb[4], [(env, (0, 170, 0)), (geom, (255, 0, 0))],
                         str(out_png).replace(".png", f"_{i}.png"))
    return geom


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
