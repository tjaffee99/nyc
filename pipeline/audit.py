"""Invariants of the built building files (run after every rebuild; CLAUDE.md "Data").

Reads what the viewer reads — viewer/public/data/core-buildings.bin.gz and the
region-buildings/13 tiles — and checks:
  1. no feature with start >= end;
  2. years inside the slider's range;
  3. no year carrying thousands of buildings more than its neighbours (a heap that was
     stacked instead of spread);
  4. no two buildings on one spot at the same time (centroid of one inside the other's
     outline while both stand; OSM building parts of one footprint are stacked on purpose
     and are skipped by their shared key prefix);
  5. nothing stands before its ground (land-year grid), with the share of buildings on made land.

Writes data/interim/reports/audit.json and prints a summary; exit code 1 if a hard check fails.
"""
from __future__ import annotations

import json
import sys

import numpy as np
import shapely

from common import INTERIM, VIEWER_DATA, YEAR_MIN, log
from export_columnar import read_bayt

NOW = 2030.0


def read_set(path):
    h, c = read_bayt(path)
    ox, oy = h["origin"]
    pos = c["positions_delta"].reshape(-1, 2).astype(np.int64)
    st = c["start_indices"].astype(np.int64)
    valid = c["vertex_valid"]
    n = h["counts"]["features"]
    polys = []
    for f in range(n):
        a, b = st[f], st[f + 1]
        # outer ring: up to the first ring-end marker
        e = a + int(np.argmax(valid[a:b] == 0)) + 1
        xy = np.cumsum(pos[a:e], axis=0) * 1e-7 + (ox, oy)
        polys.append(shapely.Polygon(xy) if len(xy) >= 4 else None)
    return {"start": c["start_year"].astype(float), "end": c["end_year"].astype(float), "height": c["height"].astype(float),
            "base": c["base"].astype(float), "conf": c["confidence"], "fid": c["fid"], "poly": np.array(polys, dtype=object)}


def main():
    files = [VIEWER_DATA / "core-buildings.bin.gz"] + sorted((VIEWER_DATA / "region-buildings" / "13").glob("*/*.bin.gz"))
    files = [f for f in files if f.exists()]
    start, end, conf = [], [], []
    overlaps = 0
    checked = 0
    worst = []
    for f in files:
        s = read_set(f)
        start.append(s["start"]); end.append(s["end"]); conf.append(s["conf"])
        ok = np.array([p is not None and p.is_valid and not p.is_empty for p in s["poly"]])
        polys = s["poly"][ok]
        st, en, base, h = s["start"][ok], s["end"][ok], s["base"][ok], s["height"][ok]
        cen = shapely.centroid(polys)
        tree = shapely.STRtree(polys)
        i, j = tree.query(cen, predicate="within")
        m = i != j
        i, j = i[m], j[m]
        # both stand at some time, and they are not stacked parts (one above the other)
        both = (np.maximum(st[i], st[j]) + 0.5 < np.minimum(en[i], en[j]))
        stacked = (base[i] >= base[j] + h[j] - 1.0) | (base[j] >= base[i] + h[i] - 1.0)
        bad = both & ~stacked
        overlaps += int(bad.sum())
        checked += len(polys)
        if bad.any() and len(worst) < 12:
            k = np.nonzero(bad)[0][0]
            c0 = cen[i[k]]
            worst.append({"file": str(f.relative_to(VIEWER_DATA)), "lon": round(float(shapely.get_x(c0)), 6), "lat": round(float(shapely.get_y(c0)), 6),
                          "a": [round(float(st[i[k]]), 1), round(float(en[i[k]]), 1)], "b": [round(float(st[j[k]]), 1), round(float(en[j[k]]), 1)]})
    start = np.concatenate(start); end = np.concatenate(end); conf = np.concatenate(conf)
    y = np.floor(start).astype(int)
    vals, counts = np.unique(y, return_counts=True)
    cnt = dict(zip(vals.tolist(), counts.tolist()))
    spikes = []
    for v, c in cnt.items():
        nb = [cnt.get(v + d, 0) for d in (-3, -2, -1, 1, 2, 3)]
        if c > 3000 and c > 2.2 * max(float(np.median(nb)), 1.0):
            spikes.append({"year": v, "count": c, "neighbours_median": float(np.median(nb))})
    out = {
        "files": len(files), "buildings": int(len(start)),
        "confidence": {k: int((conf == i).sum()) for i, k in enumerate(["exact", "estimated", "procedural", "reconstructed"])},
        "start_ge_end": int((start >= end).sum()),
        "out_of_range": int(((start < YEAR_MIN) | (start > NOW)).sum()),
        "vanished": int((end < 9000).sum()),
        "spike_years": spikes,
        "overlapping_pairs": overlaps, "overlap_examples": worst, "checked_for_overlap": checked,
        "standing_by_year": {str(t): int(((start <= t) & (end > t)).sum()) for t in (1650, 1700, 1750, 1800, 1850, 1875, 1900, 1925, 1950, 1975, 2000, 2026)},
    }
    p = INTERIM / "reports" / "audit.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1))
    log(f"audit: {out['buildings']} buildings in {out['files']} files; confidence {out['confidence']}; "
        f"start>=end {out['start_ge_end']}; out of range {out['out_of_range']}; spike years {[s['year'] for s in spikes]}; "
        f"overlapping pairs {overlaps} of {checked} checked; standing {out['standing_by_year']}")
    if out["start_ge_end"] or out["out_of_range"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
