"""Audit the built file against the sites: per site, the standing buildings inside, where their
years come from, and how many carry a year before the site's founding.

  python -I tools/audit.py            # table -> data/interim/sites/audit.csv
"""
import json
import sys
from pathlib import Path

import pandas as pd
from shapely.geometry import shape

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import geom as G  # noqa: E402

if __name__ == "__main__":
    d = json.loads((HERE.parent / "sites.geojson").read_text())
    rows, seen = [], {}
    for f in d["features"]:
        p = f["properties"]
        if p["end_year"] < 1900:
            continue
        g = shape(f["geometry"])
        key = round(g.area, 12)
        if key in seen:
            continue
        seen[key] = p["id"]
        b = G.built(g)
        if not len(b):
            rows.append((p["id"], p["start_year"], 0, 0, 0, 0, "", ""))
            continue
        pre = b[b.start_year < p["start_year"] - 0.5]
        src = b.year_src.value_counts()
        rows.append((p["id"], p["start_year"], len(b), int((b.year_confidence == "estimated").sum()), len(pre),
                     int((pre.year_confidence == "estimated").sum()),
                     " ".join(f"{k}:{v}" for k, v in src.head(4).items()),
                     " ".join(str(int(y)) for y in sorted(b.start_year.round().value_counts().head(4).index))))
    t = pd.DataFrame(rows, columns=["site", "founded", "buildings", "estimated", "before_founding", "before_est",
                                    "year_sources", "common_years"])
    out = G.ROOT / "data" / "interim" / "sites" / "audit.csv"
    t.to_csv(out, index=False)
    print(t.to_string(index=False))
