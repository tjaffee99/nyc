"""Trace the building symbols of a USGS 1:24,000 sheet around a point: black ink, opened by 5 m
(drops lettering, roads, shorelines), vectorised, simplified to 2 m.

  python -I tools/trace_ink.py LON LAT HALF_M YEAR OUT.json [--png OUT.png] [--min 250]

OUT.json: {cx, cy, sheet, polys: [{i, area, cx, cy, ring}]} - rings in metres east / north of
(cx, cy), largest first. Look at the PNG (numbered outlines) and name the polygons wanted in
demolished_def.py as ("traced", "traced/<file>.json", i). Positions +-10 m (NAD27 by PROJ's
three-parameter shift); only sheets that draw single buildings (1954 and later) are worth tracing.
"""
import json
import sys
from pathlib import Path

import numpy as np
from affine import Affine
from rasterio import features
from scipy import ndimage as ndi
from shapely.geometry import shape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import date_editions as D  # noqa: E402
import topo  # noqa: E402


def trace(cx, cy, half, year, min_area=250.0, res=1.0):
    ed = [e for e in topo.editions(cx, cy) if e[0] <= 31680]
    ed = min(ed, key=lambda e: abs(e[2] - year))
    img = topo.render(ed[5], cx, cy, half, res)
    m = D.ink(img, purple=False, dark=110)
    m = ndi.binary_closing(ndi.binary_opening(m, np.ones((5, 5), bool)), np.ones((3, 3), bool))
    tr = Affine(res, 0, -half, 0, -res, half)
    polys = [shape(g).simplify(2.0) for g, _ in features.shapes(m.astype(np.uint8), mask=m, transform=tr)]
    polys = sorted([p for p in polys if p.area >= min_area], key=lambda p: -p.area)
    out = [{"i": i, "area": round(p.area), "cx": round(p.centroid.x, 1), "cy": round(p.centroid.y, 1),
            "ring": [(round(x, 1), round(y, 1)) for x, y in p.exterior.coords]} for i, p in enumerate(polys)]
    return {"cx": cx, "cy": cy, "sheet": ed[5], "map_year": ed[2], "quad": ed[1], "polys": out}, img, polys


if __name__ == "__main__":
    a = sys.argv[1:]
    cx, cy, half, year, dst = float(a[0]), float(a[1]), float(a[2]), int(a[3]), a[4]
    d, img, polys = trace(cx, cy, half, year, float(a[a.index("--min") + 1]) if "--min" in a else 250.0)
    Path(dst).write_text(json.dumps(d))
    for o in d["polys"]:
        print(o["i"], o["area"], o["cx"], o["cy"])
    if "--png" in a:
        from PIL import Image, ImageDraw
        im = Image.fromarray(img)
        dr = ImageDraw.Draw(im)
        for o in d["polys"]:
            dr.line([((x + half), (half - y)) for x, y in o["ring"]], fill=(255, 0, 0), width=2)
            dr.text((o["cx"] + half + 4, half - o["cy"] - 4), str(o["i"]), fill=(0, 0, 255))
        im.save(a[a.index("--png") + 1])
