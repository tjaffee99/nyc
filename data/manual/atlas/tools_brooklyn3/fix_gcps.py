"""Control points of a plate that the Map Warper fit badly (CV rms > 8 m): keep the largest group of points that agree on
one similarity transform (scale fixed to the Sanborn scan's 0.098-0.112 m per pixel), within 5 m; write the plate's record with
only those points to gcps_own.json (read first by warp.record).   python -I fix_gcps.py <layer> <plate> ...
Plates with fewer than 3 agreeing points are not written (they stay left out)."""
import sys, json, itertools
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "extents" / "tools"))
import warp, streets as S  # noqa
TOL = 6.0
SC = (0.18, 0.22)
OWNF = HERE / "gcps_own.json"
own = json.loads(OWNF.read_text())
for pid in sys.argv[2:]:
    warp.OWN = Path("/nonexistent")
    rec = warp.record(pid)
    g = np.array(rec["gcps"], float)
    px = g[:, :2]
    X, Y = S.local(g[:, 3], g[:, 2])
    xy = np.column_stack([X, Y])
    best = (0, None)
    for i, j in itertools.combinations(range(len(px)), 2):
        dp, dx = px[j] - px[i], xy[j] - xy[i]
        if np.hypot(*dp) < 300:
            continue
        s = np.hypot(*dx) / np.hypot(*dp)
        if not SC[0] <= s <= SC[1]:
            continue
        # similarity with reflection (image y down): x = s R [u, -v]
        ang = np.arctan2(dx[1], dx[0]) - np.arctan2(-dp[1], dp[0])
        R = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]])
        M = s * R @ np.diag([1, -1])
        pred = (px - px[i]) @ M.T + xy[i]
        e = np.hypot(*(pred - xy).T)
        n = int((e < TOL).sum())
        if n > best[0] or (n == best[0] and best[1] is not None and e[e < TOL].mean() < best[1][1]):
            best = (n, (e < TOL, e[e < TOL].mean(), s))
    n = best[0]
    if n < 3:
        print(pid, "no consensus", len(px), "points", flush=True)
        continue
    ok = best[1][0]
    rec = dict(rec)
    rec["gcps"] = [list(map(float, r)) for r in g[ok]]
    own[str(pid)] = rec
    print(pid, "kept", n, "of", len(px), "scale %.4f" % best[1][2], "mean err %.1f m" % best[1][1], flush=True)
OWNF.write_text(json.dumps(own))
