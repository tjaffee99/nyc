"""Writes layers.json for the layers of this part. run from tools_boroughs3/: python -I mk_layers.py"""
import json, glob, os, re
import shapely.geometry as sg
from shapely.ops import unary_union
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
A = os.path.join(ROOT, "data/manual/atlas")
DUMP = os.path.join(ROOT, "data/raw/extents/spacetime/mapwarper.objects.ndjson")
MINE = ("bronx_east_", "bronx_north_", "staten_island_south_", "queens_")  # filtered below by name list
mine = set(json.load(open(os.path.join(HERE, "mine.json")))) if os.path.exists(os.path.join(HERE, "mine.json")) else set()
existing = sorted(os.path.basename(f)[:-len("_coverage.geojson")] for f in glob.glob(A + "/*_coverage.geojson"))
existing = [e for e in existing if e not in mine]
cov = []
for e in existing:
    for ft in json.load(open(f"{A}/{e}_coverage.geojson"))["features"]:
        cov.append(sg.shape(ft["geometry"]).buffer(0))
U = unary_union(cov)
recs = {}
for l in open(DUMP):
    o = json.loads(l)
    if o.get("geometry"):
        recs[o["id"]] = o
URL = "https://digitalcollections.nypl.org/ (NYPL Map Division, public domain); control points: https://s3.amazonaws.com/spacetime-nypl-org/datasets/mapwarper/mapwarper.objects.ndjson (CC0)"
BRONX_SO = {"brick": {"da_min": 4.5, "db_max": 5.0, "L_min": 45}, "street_min_q": 0.2, "street_win_m": 300.0, "outline": 0.3}

def pick(pattern, minnew=0.3, box=None, field="name"):
    out = []
    for i, o in recs.items():
        txt = (o["name"] + " " + (o["data"].get("description") or "")).replace("\r\n", " ")
        m = re.search(pattern, txt)
        if not m: continue
        s = sg.shape(o["geometry"]); c = s.centroid
        if box and not (box[0] < c.x < box[2] and box[1] < c.y < box[3]): continue
        new = s.difference(U).area / max(s.area, 1e-12)
        if new < minnew: continue
        sh = re.search(r"Plate No\. (\d+)", o["name"])
        out.append(dict(id=i, sheet=sh.group(1) if sh else "image %s" % o["data"]["imageId"], name=o["name"].replace("\r\n", " ")[:100], new=round(new, 2)))
    return sorted(out, key=lambda p: (int(p["sheet"]) if p["sheet"].isdigit() else 999, p["id"]))

def layer(year, atlas, source, plates, so, style="bromley_city", **kw):
    d = dict(map_year=year, atlas=atlas, source=source, style=style, style_override=so, require_match=8.0, source_url=URL,
             plates=plates, clip=dict(outside_layers=existing))
    d.update(kw); return d

if __name__ == "__main__":
    lay = {}
    if os.path.exists(os.path.join(HERE, "layers.json")):
        lay = json.load(open(os.path.join(HERE, "layers.json")))
    exec(open(os.path.join(HERE, "defs.py")).read())
    json.dump(lay, open(os.path.join(HERE, "layers.json"), "w"), indent=1)
    json.dump(sorted(lay), open(os.path.join(HERE, "mine.json"), "w"))
    for k, v in lay.items(): print(k, len(v["plates"]), [p["sheet"] for p in v["plates"]][:80])
