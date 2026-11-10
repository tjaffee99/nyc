"""Markdown of the "Brooklyn" README section from the layers' stats and coverage files:  python -I readme_section.py <layer> ..."""
import json, sys
out = []
tot = dict(b=0, f=0, br=0, st=0, km=0.0, used=0, left=0)
for L in sys.argv[1:]:
    s = json.load(open(f"data/manual/atlas/{L}_stats.json"))
    cov = {str(f["properties"]["plate"]): f["properties"] for f in json.load(open(f"data/manual/atlas/{L}_coverage.geojson"))["features"]}
    t = s["total"]
    out.append(f"\n#### {L}\n")
    out.append(f"{t['buildings']:,} buildings ({t['frame']:,} frame / {t['brick']:,} brick / {t['stone']:,} stone), {t['plates']} plates used, "
               f"coverage {t['coverage_km2']} km2, {t['on_today']:,} on a standing footprint (IoU > 0.5, {100*t['on_today']/max(t['buildings'],1):.0f} %).\n")
    out.append("| sheet | plate | control points (CV rms m) | registration | street match: left m | buildings (frame / brick / stone) | on a standing footprint | their median offset m |")
    out.append("|---|---|---|---|---|---|---|---|")
    left = []
    for p in s["plates"]:
        if p["status"] != "ok":
            left.append(f"{p['sheet']} ({p['plate']}; {p.get('n', 0)} outlines traced; CV rms {p.get('cv_rms')} m; {p.get('coincide', 0)} on standing footprints)")
            continue
        c = cov.get(str(p["plate"]), {})
        st = p.get("street") or {}
        out.append(f"| {p['sheet']} | {p['plate']} | {p.get('gcps')} ({p.get('cv_rms')}) | {c.get('registration', '')} | "
                   f"{c.get('street_match_left_m', '')} | {p['exported']} ({p['frame']} / {p['brick']} / {p['stone']}) | "
                   f"{p['coincide']} ({100*p['share']:.0f} %) | {c.get('registration_m', '')} |")
    out.append(f"\nLeft out ({len(left)}): " + ("; ".join(left) if left else "none") + ".\n")
    tot["b"] += t["buildings"]; tot["f"] += t["frame"]; tot["br"] += t["brick"]; tot["st"] += t["stone"]; tot["km"] += t["coverage_km2"]; tot["used"] += t["plates"]; tot["left"] += len(left)
out.append(f"\nAll Brooklyn layers: {tot['b']:,} buildings ({tot['f']:,} frame / {tot['br']:,} brick / {tot['st']:,} stone), {tot['used']} plates used, {tot['left']} left out, {tot['km']:.1f} km2 of coverage (layers may overlap at their edges: the layers were not deduplicated against each other).")
print("\n".join(out))
