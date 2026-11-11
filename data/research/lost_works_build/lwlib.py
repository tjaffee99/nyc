import csv, math, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
CSV = ROOT / "data/tables/notable_demolished.best_guess.csv"
COLS = "id,name,start_year,end_year,lat,lon,height_m,storeys,material,outline,shape_note,source_url,footprint_m,rotation_deg".split(",")
def load():
    if not CSV.exists(): return {}
    return {r["id"]: r for r in csv.DictReader(open(CSV, newline=""))}
def add(rows):
    d = load()
    for r in rows:
        r = {c: r.get(c, "") for c in COLS}
        assert r["shape_note"].startswith("BEST GUESS:"), r["id"]
        d[r["id"]] = r
    w = csv.DictWriter(open(CSV, "w", newline=""), COLS); w.writeheader()
    for r in d.values(): w.writerow(r)
    print("rows now", len(d))
def mk(id, name, y0, y1, lat, lon, h, mat, w, d, rot, note, url, storeys=""):
    return dict(id=id, name=name, start_year=y0, end_year=y1, lat=round(lat, 6), lon=round(lon, 6), height_m=h, storeys=storeys, material=mat,
                shape_note=note, source_url=url, footprint_m=f"{w:g}x{d:g}", rotation_deg=rot)
def off(lat, lon, dx_m, dy_m):
    return lat + dy_m / 110540, lon + dx_m / (111320 * math.cos(math.radians(lat)))
def drop(ids):
    d = load()
    for i in ids: d.pop(i, None)
    w = csv.DictWriter(open(CSV, "w", newline=""), COLS); w.writeheader()
    for r in d.values(): w.writerow(r)
