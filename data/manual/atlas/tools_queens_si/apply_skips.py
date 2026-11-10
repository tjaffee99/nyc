"""Leave out the plates of a layer whose registration nothing verifies (Staten Island, Bromley 1917: no street tint, so only the
building match can check a plate). Kept: a plate corrected by the building match (affine or shift), or with at least 5 outlines
on standing footprints whose median offset is 3 m or less. Reads <layer>_stats.json (from `atlas.py export`), writes `skip` into layers.json."""
import json, sys
from pathlib import Path
H = Path(__file__).resolve().parent
L = json.loads((H / "layers.json").read_text())
layer = sys.argv[1]
st = json.loads((H.parent / f"{layer}_stats.json").read_text())
by = {str(p["plate"]): p for p in st["plates"]}
n = 0
for pl in L[layer]["plates"]:
    p = by.get(str(pl["id"]))
    if not p or p.get("status") != "ok":
        continue
    bld = (p.get("bld") or {}).get("kind", "none") != "none"
    corr = Path(H.parents[3] / "data/interim/atlas_queens_si" / layer / f"{pl['id']}_corr.json")
    has_corr = corr.exists()
    surv = (p.get("coincide") or 0) >= 5 and (p.get("off_median_m") or 99) <= 3.0
    if not (bld or has_corr or surv):
        pl["skip"] = "registration not verified (control points only, cross-validation %s m; %s outlines on standing footprints%s)" % (
            p.get("cv_rms"), p.get("coincide"), "" if p.get("off_median_m") is None else ", median offset %s m" % p["off_median_m"])
        n += 1
(H / "layers.json").write_text(json.dumps(L, indent=1))
print(layer, "left out", n)
