"""Tables for data/research/boroughs_atlas3.md:  python -I report.py <layer> ...  (stats, coverage, holes covered)"""
import json, sys
import pandas as pd
import shapely.geometry as sg
from shapely.ops import unary_union
h = pd.read_csv("data/interim/reports/holes.csv"); h = h[h.county.isin(["Bronx", "Richmond", "Queens"]) & (h.year <= 1930)]
for L in sys.argv[1:]:
    s = json.load(open(f"data/manual/atlas/{L}_stats.json")); t = s["total"]
    cov = json.load(open(f"data/manual/atlas/{L}_coverage.geojson"))["features"]
    U = unary_union([sg.shape(c["geometry"]).buffer(0) for c in cov])
    ins = h[[U.contains(sg.Point(x, y)) for x, y in zip(h.lon, h.lat)]]
    out = [f"### {L}", "", f"{t['buildings']} outlines ({t['frame']} frame, {t['brick']} brick), coverage {t['coverage_km2']} km2, {t['plates']} plates used; on a standing footprint (IoU > 0.5): {t['on_today']}.", ""]
    out.append(f"Holes of holes.csv (Bronx / Richmond / Queens, 1860-1920 grids) with their point inside the coverage: {len(ins)} of {len(h)} ({ins.ha.sum():.0f} of {h.ha.sum():.0f} ha).")
    out += ["", "| sheet | plate | outlines | registration | street match left (m) | building match residual (m) | coincide share | median offset of those (m) |", "|---|---|---|---|---|---|---|---|"]
    left = []
    for c in cov:
        r = c["properties"]
        out.append(f"| {r.get('sheet')} | {r.get('plate')} | {r.get('buildings')} | {r.get('registration')} | {r.get('street_match_left_m')} | {r.get('building_match_residual_m')} | {r.get('coincide_share')} | {r.get('registration_m')} |")
    for r in s["plates"]:
        if str(r.get("status", "")).startswith(("left out", "rejected", "not traced")):
            left.append(f"* plate {r.get('plate')} (sheet {r.get('sheet')}): {r.get('status')}")
    out += ["", "Left out:", ""] + left + [""]
    print("\n".join(out))
