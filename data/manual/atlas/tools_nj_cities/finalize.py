"""Accept sheets by their registration check (chk.json), export the layer, add the check's numbers to coverage and stats.
verified: ratio >= 1.5 and best shift <= 3 m; consistent: ratio >= 1.2 and best shift <= 2.5 m (shares of traced area on today's footprints at the fit against the ring 12-45 m away).
python -I finalize.py <layer>"""
import sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import njc
from njc import A, jl, lay_p
import numpy as np
layer = sys.argv[1]
L = jl(lay_p); chk = json.loads((A.WORK / layer / "chk.json").read_text())
tier = {}
for p in L[layer]["plates"]:
    c = chk.get(p["sheet"]); p.pop("skip", None)
    if not c or "ratio" not in c: p["skip"] = "too few outlines to check (%s)" % (c or {}).get("verdict", "not traced"); continue
    sh = float(np.hypot(*c["best_shift_m"]))
    if c["ratio"] >= 1.5 and sh <= 3: tier[p["sheet"]] = "verified"
    elif c["ratio"] >= 1.2 and sh <= 2.5: tier[p["sheet"]] = "consistent"
    else: p["skip"] = "registration not confirmed (overlap ratio %.2f, best shift %s m)" % (c["ratio"], c["best_shift_m"])
lay_p.write_text(json.dumps(L, indent=1))
A.export(layer)
OUT = A.OUT
cov = json.loads((OUT / f"{layer}_coverage.geojson").read_text())
for f in cov["features"]:
    s = f["properties"]["sheet"]; c = chk[s]
    f["properties"].update(registration="building overlap check: " + tier[s], check_ratio=c["ratio"], check_on_today=c["on_today"], check_best_shift_m=c["best_shift_m"])
(OUT / f"{layer}_coverage.geojson").write_text(json.dumps(cov, separators=(",", ":")))
st = json.loads((OUT / f"{layer}_stats.json").read_text())
for r in st["plates"]:
    s = str(r.get("sheet")); 
    if s in chk: r["check"] = chk[s]; r["tier"] = tier.get(s)
st["total"]["tiers"] = {k: sum(v == k for v in tier.values()) for k in ("verified", "consistent")}
(OUT / f"{layer}_stats.json").write_text(json.dumps(st, indent=1))
print(st["total"])
