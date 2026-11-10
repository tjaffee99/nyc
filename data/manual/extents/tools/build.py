"""Build the extent snapshots (GeoJSON) from the definitions in snapshots.py.

  python -I build.py                 # build every snapshot, nest, check, write ../<name>.geojson + report
  python -I build.py preview <name> <x0,y0,x1,y1> <m_per_px> <out.png> [--streets]   # outline over its map

A ring is a list of vertices: ("Street A", "Street B", (x, y)) = intersection of two streets of today
(the (x, y) local-metre hint picks the right one and is checked: more than 80 m off is reported, more than 250 m is an error), or
(x, y) = a free vertex in local metres read off the warped map (the map's shoreline, a field edge).
{"buffer": [...], "width": w} = a ribbon w metres either side of a line (built frontage along a road).
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import shapely
import shapely.geometry as sg
sys.path.insert(0, str(Path(__file__).resolve().parent))
import streets as S

OUT = Path(__file__).resolve().parents[1]
VERBOSE = True
CLASSIFIED = Path(__file__).resolve().parent / "classified"   # outputs of classify_runs.py / usgs_extent.py (committed)
INTERIM = Path(__file__).resolve().parents[4] / "data" / "interim" / "extents"


def resolve(v):
    """-> (x, y, label)"""
    if isinstance(v[0], str):
        a, b = v[0], v[1]
        hint = v[2] if len(v) > 2 else None
        x, y = S.intersection_xy(a, b, hint)
        if hint is not None:
            d = float(np.hypot(x - hint[0], y - hint[1]))
            if d > 250:
                raise ValueError(f"{a} & {b}: resolved {x:.0f},{y:.0f} is {d:.0f} m from the hint {hint}")
            if d > 80 and VERBOSE:
                print(f"   note: {a} & {b} resolved {x:.0f},{y:.0f}, {d:.0f} m from the hint {hint}")
        return x, y, f"{a} & {b}"
    return float(v[0]), float(v[1]), "map"


def ring_geom(spec):
    if isinstance(spec, dict) and "buffer" in spec:
        pts = [resolve(v) for v in spec["buffer"]]
        g = sg.LineString([(p[0], p[1]) for p in pts]).buffer(spec["width"], cap_style="flat")
        return g, [p[2] for p in pts]
    if isinstance(spec, dict) and "file" in spec:   # classified polygons cached by a classify step (local metres)
        g = sg.shape(json.loads((CLASSIFIED / spec["file"]).read_text()))
        return g, ["classified from the map's tone"]
    pts = [resolve(v) for v in spec]
    g = sg.Polygon([(p[0], p[1]) for p in pts])
    if not g.is_valid:
        raise ValueError("ring is not a valid polygon (self-crossing?): " + shapely.is_valid_reason(g))
    return g, [p[2] for p in pts]


def to_wgs(geom):
    return shapely.transform(geom, lambda c: np.column_stack(S.lonlat(c[:, 0], c[:, 1])))


def build(only=None, verbose=True):
    import snapshots
    out = {}
    by_place = {}
    for name, sn in snapshots.SNAPSHOTS.items():
        if only and name not in only:
            continue
        rings = {}
        for rname, spec in sn["rings"].items():
            if isinstance(spec, dict) and "file" in spec and not (CLASSIFIED / spec["file"]).exists():
                print("   missing", spec["file"], "- skipped", name)
                continue
            g, labels = ring_geom(spec)
            rings[rname] = (g, labels)
        if not rings:
            continue
        out[name] = {"sn": sn, "rings": rings}
        by_place.setdefault(sn["place"], []).append(name)
    report = []
    for o in out.values():
        o["own"] = shapely.union_all([g for g, _ in o["rings"].values()]).buffer(0)
    for o in out.values():
        for other in o["sn"].get("also_contains", []):      # an old town swallowed by this place (Williamsburgh -> Brooklyn)
            if other in out:
                o["own"] = shapely.union_all([o["own"], out[other]["own"]])
    for place, names in by_place.items():
        names.sort(key=lambda n: out[n]["sn"]["year"])
        prev = None
        for n in names:
            o = out[n]
            own = o["own"]
            o["added"] = 0.0
            if prev is not None and not o["sn"].get("no_nest") and not out[prev]["sn"].get("kind"):
                missing = out[prev]["all"].difference(own.buffer(0.5))
                o["added"] = missing.area / 1e4
                o["all"] = shapely.union_all([own, out[prev]["all"]])
                o["nested_from"] = prev
            else:
                o["all"] = own
            if not o["sn"].get("kind"):
                prev = n
    for name, o in out.items():
        sn = o["sn"]
        feats = []
        geom = o["all"]
        parts = list(geom.geoms) if hasattr(geom, "geoms") else [geom]
        parts.sort(key=lambda p: -p.area)
        for i, part in enumerate(parts):
            part = part.simplify(1.0)
            rn = [rname for rname, (g, _) in o["rings"].items() if g.representative_point().within(part.buffer(1))]
            labels = [l for rname, (g, lab) in o["rings"].items() if rname in rn for l in lab]
            props = {"name": name, "place": sn["place"], "year": sn["year"], "ring": "+".join(rn) or f"part{i}",
                     "kind": sn.get("kind", "built_up"),
                     "map": sn["map"], "map_url": sn["map_url"], "scan_url": sn.get("scan_url"),
                     "georeferencing": sn.get("georef"), "residual_m": sn.get("residual_m"),
                     "confidence": sn["confidence"], "note": sn["note"], "method": sn.get("method"),
                     "area_ha": round(part.area / 1e4, 2), "vertices": labels,
                     "nested_from": o.get("nested_from"), "licence": sn.get("licence", "public domain (map); tracing CC0")}
            gw = shapely.set_precision(to_wgs(part), 1e-7)      # 1 cm grid; GEOS keeps the result valid
            if not gw.is_valid or gw.geom_type != "Polygon":
                gw = shapely.make_valid(gw)
                polys = [q for q in getattr(gw, "geoms", [gw]) if q.geom_type == "Polygon"]
                gw = max(polys, key=lambda q: q.area) if len(polys) == 1 or gw.geom_type != "MultiPolygon" else gw
            feats.append({"type": "Feature", "properties": props, "geometry": sg.mapping(gw)})
        fc = {"type": "FeatureCollection", "name": name, "features": feats}
        (OUT / f"{name}.geojson").write_text(json.dumps(fc))
        report.append((name, sn["year"], round(o["own"].area / 1e4, 1), round(geom.area / 1e4, 1), round(o["added"], 2), len(parts), geom.is_valid,
                       sn["map"].split(" — ")[0][:78], sn.get("residual_m"), sn["confidence"]))
    if verbose:
        print(f"{'snapshot':24s} year  own_ha  nested_ha  added_by_nesting_ha  parts valid")
        for r in report:
            print(f"{r[0]:24s} {r[1]}  {r[2]:7.1f}  {r[3]:8.1f}  {r[4]:8.2f}  {r[5]:5d} {r[6]}")
    if not only:
        report.sort(key=lambda r: (r[0].startswith("fire"), r[0].split("_1")[0] != "manhattan", r[0].split("_1")[0], r[1]))
        rows = ["| snapshot | map | own ha | nested ha | added by nesting ha | polygons | residual m | confidence |", "|---|---|---|---|---|---|---|---|"]
        for r in report:
            rows.append(f"| `{r[0]}` | {r[7]} | {r[2]:,.1f} | {r[3]:,.1f} | {r[4]:.1f} | {r[5]} | {r[8] if r[8] is not None else 'n/a'} | {r[9]} |")
        readme = OUT / "README.md"
        if readme.exists():
            t = readme.read_text()
            a0, a1 = t.index("<!-- TABLE -->") + len("<!-- TABLE -->"), t.index("<!-- /TABLE -->")
            readme.write_text(t[:a0] + "\n" + "\n".join(rows) + "\n" + t[a1:])
    return out


def main(a):
    if a and a[0] == "preview":
        import snapshots, warp, classify
        name, box, mpp, outp = a[1], [float(v) for v in a[2].split(",")], float(a[3]), a[4]
        o = build([n for n in snapshots.SNAPSHOTS if snapshots.SNAPSHOTS[n]["place"] == snapshots.SNAPSHOTS[name]["place"]], verbose=False)[name]
        m = warp.MapWarp(a[a.index("--map") + 1] if "--map" in a else o["sn"]["map_id"])
        rgb = m.render(*box, mpp)
        layers = [(o["own"], (255, 0, 0))]
        classify.preview(rgb, box, mpp, layers, outp, grid=int(a[a.index("--grid") + 1]) if "--grid" in a else 100, streets="--streets" in a)
        print(outp, "own area %.1f ha" % (o["own"].area / 1e4))
    else:
        build()


if __name__ == "__main__":
    main(sys.argv[1:])
