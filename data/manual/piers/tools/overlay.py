"""Sheet crop with pier outlines drawn on it (visual check).
usage: overlay.py out.png lon0,lat0,lon1,lat1 <sheet.tif>[,<sheet.tif>...] [--final piers.geojson] [--max 900]
Candidates that pass build.keep() are green, the rest orange; with --final the built piers are drawn in blue instead."""
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image, ImageDraw
from rasterio.windows import from_bounds

sys.path.insert(0, str(Path(__file__).parent))
import extract as E


def keep(p):
    return (p["reach_m"] >= 35 and not p["both_ends"] and p["gap_m"] <= 12 and p["rect_fill"] >= 0.55 and
            p["length_m"] >= 1.4 * p["width_m"] and p["width_m"] <= 100 and p["area_m2"] >= 250)


def panel(fn, box, max_px, final=None):
    with rasterio.open(E.RAW / "usgs" / fn) as s:
        geo = E.Geo(s.crs)
        xs, ys = geo.from_wgs([box[0], box[2], box[0], box[2]], [box[1], box[1], box[3], box[3]])
        w = from_bounds(min(xs), min(ys), max(xs), max(ys), transform=s.transform).round_offsets().round_lengths()
        sc = max(1.0, max(w.width, w.height) / max_px)
        a = s.read(window=w, out_shape=(s.count, int(w.height / sc), int(w.width / sc)), boundless=True, fill_value=255)
        tr = s.window_transform(w) * rasterio.Affine.scale(sc)
    im = Image.fromarray(np.moveaxis(a[:3], 0, -1)).convert("RGB")
    dr = ImageDraw.Draw(im)
    if final:
        feats = [(f, (0, 90, 255) if f["properties"]["end_year"] == 9999 else (230, 0, 200)) for f in json.load(open(final))["features"]]     # standing blue, vanished magenta
    else:
        feats = [(f, (0, 170, 0) if keep(f["properties"]) else (255, 140, 0)) for f in
                 json.load(open(E.OUT / "cand" / fn.replace(".tif", ".geojson")))["features"]]
    for f, col in feats:
        g = f["geometry"]
        rings = [g["coordinates"][0]] if g["type"] == "Polygon" else [p[0] for p in g["coordinates"]]
        for ring in rings:
            c = np.array(ring)
            if c[:, 0].max() < box[0] or c[:, 0].min() > box[2] or c[:, 1].max() < box[1] or c[:, 1].min() > box[3]:
                continue
            x, y = geo.from_wgs(c[:, 0], c[:, 1])
            px = [(~tr) * (xx, yy) for xx, yy in zip(x, y)]
            dr.line(px + [px[0]], fill=col, width=2)
    return im


if __name__ == "__main__":
    out, box, sheets = sys.argv[1], [float(v) for v in sys.argv[2].split(",")], sys.argv[3].split(",")
    final = sys.argv[sys.argv.index("--final") + 1] if "--final" in sys.argv else None
    mx = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 900
    ims = [panel(f, box, mx, final) for f in sheets]
    h = min(i.height for i in ims)
    canvas = Image.new("RGB", (sum(i.width for i in ims) + 6 * (len(ims) - 1), h), (255, 255, 255))
    x = 0
    for i in ims:
        canvas.paste(i.crop((0, 0, i.width, h)), (x, 0))
        x += i.width + 6
    canvas.save(out)
    print(out, canvas.size)
