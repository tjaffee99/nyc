"""Write data/tables/notable_demolished.sites.csv from demolished_def.py.

  cd data/manual/sites && ../../../.venv/bin/python -I tools/build_demolished.py
"""
import csv
import math
import sys
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import demolished_def  # noqa: E402
import geom as G  # noqa: E402

W = "https://en.wikipedia.org/wiki/"
OUT = G.ROOT / "data" / "tables" / "notable_demolished.sites.csv"
COLS = ["id", "name", "start_year", "end_year", "lat", "lon", "height_m", "storeys", "material", "outline", "shape_note",
        "source_url", "footprint_m", "rotation_deg"]


def main():
    rows = []
    for d in demolished_def.DEMOLISHED:
        sh = d["shape"]
        ring, fp, rot = None, "", ""
        if sh[0] == "outline":
            ring = list(sh[1])
        elif sh[0] == "local":
            cx, cy = sh[1], sh[2]
            ring = [(cx + x / G.kx(cy), cy + y / G.KY) for x, y in sh[3]]
        elif sh[0] == "circle":
            ring = list(G.circle(sh[1], sh[2], sh[3], 24).exterior.coords)[:-1]
        elif sh[0] == "blocks":
            g = G.union(*[G.block(p) for p in sh[1]]).convex_hull.simplify(1.0 / G.KY)
            ring = list(g.exterior.coords)[:-1]
        elif sh[0] == "rect":
            fp, rot = f"{sh[1]}x{sh[2]}", sh[3]
        lat, lon = d["lat"], d["lon"]
        outline = ""
        if ring:
            outline = "; ".join(f"{x:.6f} {y:.6f}" for x, y in ring)
            lon = sum(p[0] for p in ring) / len(ring)
            lat = sum(p[1] for p in ring) / len(ring)
        assert d["start"] < d["end"] and lat and lon, d["id"]
        src = d["src"] if d["src"].startswith("http") else W + urllib.parse.quote(d["src"], safe="_,()'&")
        rows.append([d["id"], d["name"], d["start"], d["end"], round(lat, 6), round(lon, 6), d["height_m"], d["storeys"],
                     d["material"], outline, d["shape_note"], src, fp, rot])
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(COLS)
        w.writerows(rows)
    print(len(rows), "rows ->", OUT, "; with outline:", sum(1 for r in rows if r[9]))


if __name__ == "__main__":
    main()
