"""Checks on the built extent files: loads, validity, area, nesting, bounds.
  python -I check.py
"""
import json, sys
from pathlib import Path
import shapely, shapely.geometry as sg
sys.path.insert(0, str(Path(__file__).resolve().parent))
import classify

OUT = Path(__file__).resolve().parents[1]
ALSO = {"brooklyn_1889": ["williamsburgh_1836"]}


def load(p):
    fc = json.loads(p.read_text())
    geoms = [sg.shape(f["geometry"]) for f in fc["features"]]
    g = shapely.union_all(geoms)
    return fc, classify.to_local(g), geoms


def main():
    files = sorted(OUT.glob("*.geojson"))
    by = {}
    bad = 0
    for p in files:
        fc, g, geoms = load(p)
        pr = fc["features"][0]["properties"]
        ok = all(x.is_valid for x in geoms) and g.is_valid
        b = shapely.union_all(geoms).bounds
        inbox = -74.29 < b[0] and b[2] < -73.67 and 40.47 < b[1] and b[3] < 40.94
        need = all(pr.get(k) not in (None, "") for k in ("year", "map", "map_url", "confidence", "note"))
        by.setdefault(pr["place"], []).append((pr["year"], p.stem, g, pr.get("kind")))
        bad += not (ok and inbox and need)
        print(f"{p.stem:22s} features {len(geoms):4d}  area {g.area / 1e4:9.1f} ha  valid {ok}  in map box {inbox}  properties {need}  size {p.stat().st_size // 1024} KB")
    print("nesting:")
    names = {n: g for v in by.values() for (_, n, g, _) in v}
    for place, v in by.items():
        v.sort()
        for (y0, n0, g0, k0), (y1, n1, g1, k1) in zip(v, v[1:]):
            miss = g0.difference(g1.buffer(1.0)).area / 1e4
            bad += miss > 0.05
            print(f"   {n1} contains {n0}: {'yes' if miss <= 0.05 else 'NO'} (outside: {miss:.2f} ha)")
    for big, small in ALSO.items():
        for s in small:
            if big in names and s in names:
                miss = names[s].difference(names[big].buffer(1.0)).area / 1e4
                bad += miss > 0.05
                print(f"   {big} contains {s}: {'yes' if miss <= 0.05 else 'NO'} (outside: {miss:.2f} ha)")
    print("problems:", bad)


if __name__ == "__main__":
    main()
