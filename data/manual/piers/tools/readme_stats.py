"""Rewrites the two generated blocks of ../README.md ("Counts" and the check output) from stats.json, sources_used.csv,
piers.geojson and data/interim/piers/check.log.   python readme_stats.py   (after dates.py and check.py > check.log)"""
import csv
import json
import re
from collections import Counter
from pathlib import Path

H = Path(__file__).resolve().parents[1]
s = json.load(open(H / "stats.json"))
kinds = Counter((r["kind"], r["role"]) for r in csv.DictReader(open(H / "sources_used.csv")))
P = [f["properties"] for f in json.load(open(H / "piers.geojson"))["features"]]
order = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]
tab = lambda rows, head: "\n".join(["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])
b = tab([[o, s["by_borough"].get(o, 0), s["by_borough"].get(o, 0) - s["by_borough_vanished"].get(o, 0), s["by_borough_vanished"].get(o, 0)] for o in order] +
        [["**all**", s["features"], s["standing"], s["vanished"]]], ["borough", "piers", "standing", "vanished"])
decs = sorted(set(s["start_decade"]) | set(k for k in s["end_decade"] if k != "standing"))
d = tab([[k, s["start_decade"].get(k, 0), s["end_decade"].get(k, 0)] for k in decs] + [["standing", "", s["end_decade"]["standing"]]], ["decade", "start", "end"])
q = tab([[k, s["start_quality"].get(k, 0), s["end_quality"].get(k, 0)] for k in ("recorded", "bracket", "estimated")], ["quality", "start_year", "end_year"])
osm = sum(1 for p in P if p["end_year"] == 9999 and p["source"] == "osm")
longb = sum(1 for p in P if p["end_year"] != 9999 and p["end_quality"] == "estimated" and "no later map" in p["note"])
usgs_full = sum(v for (k, r), v in kinds.items() if k.startswith("USGS") and r.startswith("outlines"))
usgs_add = sum(v for (k, r), v in kinds.items() if k.startswith("USGS") and r.startswith("additions"))
charts = sum(v for (k, r), v in kinds.items() if k.startswith("nautical"))
stats = f"""## Counts (from `stats.json`)

{s['features']} piers: {s['standing']} standing ({osm} from OpenStreetMap, {s['standing'] - osm} last seen on a chart of 2012 or later and taken as standing) and {s['vanished']} vanished. A pier that was rebuilt, or whose place stood empty between two piers, is two features.

{b}

{d}

The 1890s column is mostly "by 1897" ({s['start_upper_bound_only']} piers have `start_is_upper_bound`). {longb} vanished piers have no later map of their place at all: their end is the middle of the years from their last map to 2026, marked `estimated`.

{q}

For `end_year`, `recorded` means "stands, it is in OpenStreetMap", plus the cited ends of the piers that were rebuilt.

Outlines: {s['outline_source'].get('noaa', 0)} from the charts, {s['outline_source'].get('usgs', 0)} from the USGS 1:24,000 sheets, {s['outline_source'].get('osm', 0)} from OpenStreetMap. Sheds: {s['shed'].get('shed', 0)} piers drawn roofed, {s['shed'].get('none', 0)} open or not drawn.

Sources read: {usgs_full} USGS 1:24,000 sheets as full editions, {usgs_add} more for additions only, {charts} chart editions, 4 sheets of 1888-98. Listed in `sources_used.csv`.

Set aside: {s['terrain_conflicts']} vanished piers in `piers_terrain_conflict.geojson`. Thrown out (`review.csv`): """ + "; ".join(f"{v} × {k}" for k, v in sorted(s["dropped"].items(), key=lambda kv: -kv[1])) + ".\n\n"
chk = open("/home/user/nyc/data/interim/piers/check.log").read().strip()
touch = re.search(r"; (\d+) outlines touch", chk).group(1)
r = open(H / "README.md").read()
a, e = r.index("## Counts (from `stats.json`)"), r.index("## Files")
r = r[:a] + stats + r[e:]
a, e = r.index("All pass on the files as delivered:"), r.index("Also looked at:")
r = r[:a] + "All pass on the files as delivered:\n\n```\n" + chk + "\n```\n\n" + r[e:]
r = re.sub(r"and \d+ outlines touch a cell", f"and {touch} outlines touch a cell", r)
open(H / "README.md", "w").write(r)
print(stats)
print(chk.split("\n")[-1], "| fails:", sum(l.startswith("FAIL") for l in chk.split("\n")))
