"""markdown tables of a layer's per-plate numbers from its _stats.json: python -I note_tables.py <layer> ..."""
import json, sys
for L in sys.argv[1:]:
    s = json.load(open(f'data/manual/atlas/{L}_stats.json')); t = s['total']
    print(f"\n#### {L}\n\n{t['buildings']} outlines ({t['frame']} frame / {t['brick']} brick / {t['stone']} stone), {t['plates']} plates used, {t['coverage_km2']} km2 of plate masks; {t['on_today']} coincide with a standing footprint (IoU > 0.5).\n")
    print("| sheet | plate | gcps (CV rms m) | m/px | registration | street left m | traced | exported | on a standing footprint (median offset m) |\n|---|---|---|---|---|---|---|---|---|")
    left = []
    for p in s['plates']:
        st = p.get('street') or {}
        if not p.get('status', '').startswith('ok'):
            left.append(f"{p['sheet']} ({p['plate']}; {p.get('n')} traced; {p['status']})"); continue
        reg = (st.get('kind') or 'none') + ((' + ' + st['kind2']) if st.get('kind2') else '') + (f" ({st.get('agree')} windows)" if st.get('agree') else '')
        if p.get('corrected') is False: reg = 'control points only'
        print(f"| {p['sheet']} | {p['plate']} | {p['gcps']} ({p['cv_rms']}) | {p['mpp']} | {reg} | {st.get('after_abs_median')} | {p['n']} | {p.get('exported')} | {p.get('coincide')} ({p.get('off_median_m')}) |")
    if left: print("\nLeft out:", "; ".join(left))
