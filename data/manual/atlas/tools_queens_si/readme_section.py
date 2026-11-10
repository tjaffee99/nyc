"""Writes the numbers of the 'Queens and Staten Island' section of the README (tables from <layer>_stats.json) to stdout."""
import json, sys
from pathlib import Path
OUT = Path(__file__).resolve().parents[1]
for layer in sys.argv[1:]:
    st = json.loads((OUT / f"{layer}_stats.json").read_text())
    t = st["total"]; fc = t.get("final_checks", {})
    print(f"\n#### {layer}\n")
    print(f"{t['buildings']} buildings ({t['frame']} frame, {t['brick']} brick, {t['stone']} stone), coverage {t['coverage_km2']} km2, "
          f"{t['plates']} plates used; on a standing footprint (IoU > 0.5): {t['on_today']}; dropped by the final checks: "
          f"{fc.get('dropped_centre_outside_coverage',0)} centre outside coverage, {fc.get('dropped_overlapping',0)} overlapping; "
          f"overlapping pairs left {fc.get('overlapping_pairs_left')}, touching / slightly overlapping pairs {fc.get('touching_or_slightly_overlapping_pairs')}.\n")
    print("| sheet | plate | outlines | registration | street match: windows / shift found / left (m) | building match residual (m) | coincide (n, share) | median offset of those (m) | cross-val. of control points (m) |")
    print("|---|---|---|---|---|---|---|---|---|")
    left = []
    for p in st["plates"]:
        if p.get("status") != "ok":
            left.append(p); continue
        s = p.get("street") or {}; b = p.get("bld") or {}
        reg = " + ".join(x for x, k in (("street match", s), ("building match", b)) if k.get("kind", "none") != "none") or "control points only"
        print(f"| {p['sheet']} | {p['plate']} | {p.get('exported_final', p.get('exported'))} | {reg} | {s.get('agree','-')} / {s.get('shift_abs_median','-')} / {s.get('after_abs_median','-')} | {b.get('fit_residual_m','-')} | {p.get('coincide')} ({p.get('share')}) | {p.get('off_median_m')} | {p.get('cv_rms')} |")
    if left:
        print("\nLeft out:\n")
        for p in left:
            print(f"* plate {p['plate']} (sheet {p['sheet']}): {p.get('status','').replace('left out: ','')}")
