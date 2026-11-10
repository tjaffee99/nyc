"""Look at a sheet around a point at full scan resolution.

  python -I look.py <sheet id> <lon> <lat> <half-width m> <out.png> [zoom] [--det] [--roads]

--det draws the cached detections of the sheet (green = kept, red = rejected with the reason's
first letters), --roads today's road centrelines (blue) through the sheet's shift.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "pipeline"))
import topo_farmsteads as T


def look(sid, lon, lat, half, zoom=1.0, det=False, roads=False, shift=None):
    sh = T.Sheet(sid)
    cache = T.SHEET_CACHE / f"{sid}.json"
    res = json.loads(cache.read_text()) if cache.exists() else None
    if shift is not None:
        sh.shift = shift
    elif res and res.get("shift"):
        sh.shift = res["shift"]
    c, r = sh.lonlat_to_px(lon, lat)
    n = int(2 * half / sh.m_per_px)
    x0, y0 = int(c - n / 2), int(r - n / 2)
    img = Image.fromarray(sh.render(x0, y0, n, n))
    if zoom != 1:
        img = img.resize((int(n * zoom), int(n * zoom)), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    if roads:
        for line in T.modern_roads_px(sh, x0, y0, n, n):
            d.line([((x - x0) * zoom, (y - y0) * zoom) for x, y in line], fill=(0, 90, 255), width=1)
    if det and res:
        for m in res["marks"]:
            px, py = (m["col"] - x0) * zoom, (m["row"] - y0) * zoom
            if 0 <= px < img.width and 0 <= py < img.height:
                ok = m.get("keep", True)
                rr = 11 * zoom if zoom > 1 else 11
                d.ellipse([px - rr, py - rr, px + rr, py + rr], outline=(0, 170, 0) if ok else (255, 0, 0), width=2)
                if not ok:
                    d.text((px + rr, py - 5), m.get("why", "")[:4], fill=(255, 0, 0))
    return img


if __name__ == "__main__":
    a = [v for v in sys.argv[1:] if not v.startswith("--")]
    img = look(a[0], float(a[1]), float(a[2]), float(a[3]), float(a[5]) if len(a) > 5 else 1.0, "--det" in sys.argv, "--roads" in sys.argv)
    img.save(a[4])
    print(a[4], img.size)
