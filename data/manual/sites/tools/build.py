"""Build data/manual/sites/sites.geojson from sites_def.py / sites_def2.py.

  cd data/manual/sites && ../../../.venv/bin/python -I tools/build.py [--check]

--check also looks each site's years up in the cached source text (tools/wp_facts.py) and
lists the ones the article does not mention (those must say "estimated" in their note).
Outlines are simplified to ~2 m; coordinates rounded to 1e-6 degrees.
"""
import json
import re
import sys
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import geom as G  # noqa: E402
import sites_def  # noqa: E402,F401
import sites_def2  # noqa: E402,F401
import wp_facts  # noqa: E402
from shapely.geometry import mapping  # noqa: E402

OUT = HERE.parent / "sites.geojson"
W = "https://en.wikipedia.org/wiki/"
KINDS = {"fort", "military_base", "navy_yard", "rail_yard", "gasworks", "power_plant", "refinery", "shipyard", "factory",
         "terminal", "landfill", "quarry", "prison", "hospital_campus", "asylum", "other"}


def url(src):
    return src if src.startswith("http") else W + urllib.parse.quote(src, safe="_,()'&")


def rnd(o):
    if isinstance(o, (list, tuple)):
        return [rnd(x) for x in o]
    return round(o, 6)


def build(check=False):
    feats, bad, seen = [], [], set()
    for s in sites_def.SITES:
        assert s["kind"] in KINDS, s["id"]
        assert s["after"] in ("park", "city", "vacant", "same") and s["ground"] in ("paved", "yard", "open"), s["id"]
        assert s["id"] not in seen and s["start"] < s["end"], s["id"]
        seen.add(s["id"])
        try:
            g = s["geom"]()
        except Exception as e:  # noqa: BLE001
            bad.append((s["id"], f"geometry: {e!r}"[:160]))
            continue
        g = g.buffer(0).simplify(2.0 / G.KY)
        if g.is_empty:
            bad.append((s["id"], "empty geometry"))
            continue
        if g.geom_type == "GeometryCollection":
            from shapely.ops import unary_union
            g = unary_union([x for x in g.geoms if x.geom_type in ("Polygon", "MultiPolygon")])
        note = s["note"]
        est = "estimated" in note or s["basis"] != "text"
        if check and not s["src"].startswith("http"):
            f = wp_facts.WP / (s["src"].replace("/", "_") + ".wiki")
            if not f.exists():
                bad.append((s["id"], f"source not cached: {s['src']}"))
            else:
                t = wp_facts.clean(f.read_text(encoding="utf-8"))
                for y in (s["start"], s["end"]):
                    if y < 9999 and not re.search(rf"\b{y}\b", t) and "estimated" not in note:
                        bad.append((s["id"], f"year {y} not in {s['src']}"))
        gj = mapping(g)
        c = g.representative_point()
        feats.append({"type": "Feature",
                      "properties": {"id": s["id"], "name": s["name"], "kind": s["kind"], "start_year": s["start"],
                                     "end_year": s["end"], "after": s["after"], "ground": s["ground"],
                                     "label": bool(s["label"]), "source_url": url(s["src"]), "note": note,
                                     "date_basis": s["basis"], "floor": bool(s["floor"]),
                                     "area_ha": round(G.area_ha(g), 1), "lon": round(c.x, 6), "lat": round(c.y, 6)},
                      "geometry": {"type": gj["type"], "coordinates": rnd(gj["coordinates"])}})
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False, indent=0) + "\n",
                   encoding="utf-8")
    return feats, bad


if __name__ == "__main__":
    feats, bad = build("--check" in sys.argv)
    for f in feats:
        p = f["properties"]
        print(f"{p['id']:38s} {p['kind']:15s} {p['start_year']}-{p['end_year']} {p['area_ha']:7.1f} ha  {f['geometry']['type']}")
    print(len(feats), "features ->", OUT)
    for b in bad:
        print("  PROBLEM", *b)
