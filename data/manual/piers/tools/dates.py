"""Tracks (build.py) -> dated piers: data/manual/piers/piers.geojson, review.csv, stats.json.

  python dates.py

Evidence per pier, in time order: the 1889-98 USGS 15-minute sheets (piers are black strokes: 'pier' when ink lies on
the outline, 'water' when there is none within 30 m), the chart editions, the USGS 1:24,000 editions, OpenStreetMap.
Every source has a content interval [lo, hi] (a USGS sheet: aerial photographs .. date on the map; a chart: its
edition year).  Then
   start <= earliest hi of a source that shows the pier;   start >= latest lo of an earlier source that shows water
   end   >= latest lo of a source that shows the pier;     end   <= earliest hi of a later source without it
and the year written is the middle of the bracket.  `bracket` when the bracket is 20 years or narrower, else
`estimated`; a pier that is already on the first source covering its place gets that source's year, `estimated`, and
`start_is_upper_bound` = true.  research.csv (cited dates) overrides and is `recorded`.
"""
import csv
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import duckdb
import numpy as np
import pyproj
import rasterio
import shapely
import shapely.affinity
from rasterio import features
from shapely.geometry import mapping, shape
from shapely.strtree import STRtree

sys.path.insert(0, str(Path(__file__).parent))
import extract as E
from build import TODAY, UTM, dims, to_utm, to_wgs

HERE = Path(__file__).resolve().parents[1]
STROKE_SHEETS = [  # file (data/raw/natural/usgs), key in data/manual/natural/usgs_sheets.json, survey year, date on map, label, quad
    ("NJ_Harlem_472515_1891_62500_geo.tif", "NJ_Harlem_472515_1891", 1889, 1891, "USGS Harlem 1:62,500 1891 (surveyed 1889)", (-74.0, 40.75, -73.75, 41.0)),
    ("NY_Brooklyn_123118_1897_62500_geo.tif", "NY_Brooklyn_123118_1897", 1897, 1897, "USGS Brooklyn 1:62,500 1897", (-74.0, 40.5, -73.75, 40.75)),
    ("NJ_Staten_Island_255388_1898_62500_geo.tif", "NJ_Staten_Island_255388_1898", 1897, 1898, "USGS Staten Island 1:62,500 1898 (surveyed 1897)", (-74.25, 40.5, -74.0, 40.75)),
    ("NJ_Paterson_255310_1888_62500_geo.tif", "NJ_Paterson_255310_1888", 1888, 1888, "USGS Paterson 1:62,500 1888", (-74.25, 40.75, -74.0, 41.0)),
]
SRC_URL = {
    "usgs": "https://www.usgs.gov/programs/national-geospatial-program/historical-topographic-maps-preserving-past",
    "chart": "https://historicalcharts.noaa.gov/",
    "osm": "https://www.openstreetmap.org/copyright",
}


class Strokes:
    def __init__(self, fn, key, lo, hi, label, quad):
        # the quadrangle in WGS84 (NAD27 + 36 m east, 11 m north here), shrunk by 60 m: nothing is read off the collar
        self.quad = shapely.box(quad[0] + 0.00043 + 0.0007, quad[1] + 0.0001 + 0.0005, quad[2] + 0.00043 - 0.0007, quad[3] + 0.0001 - 0.0005)
        shifts = json.load(open(E.ROOT / "data/manual/natural/usgs_sheets.json"))
        self.shift = shifts[key]["shift_m"]
        with rasterio.open(E.ROOT / "data/raw/natural/usgs" / fn) as s:
            rgb = s.read()[:3]
            self.tr = s.transform
            self.t = pyproj.Transformer.from_crs("EPSG:4326", s.crs.to_wkt(), always_xy=True)
        lum = rgb.astype("int16").sum(0) // 3
        chroma = rgb.max(0).astype("int16") - rgb.min(0)
        self.dark = (lum < 110) & (chroma < 80)
        self.lo, self.hi, self.label, self.name = lo, hi, label, fn
        self.pxm = abs(self.tr.a)

    def look(self, g_wgs):
        if not self.quad.contains(g_wgs.centroid):
            return None

        def f(c):
            x, y = self.t.transform(c[:, 0], c[:, 1])
            inv = ~self.tr
            x, y = np.asarray(x) - self.shift[0], np.asarray(y) - self.shift[1]
            return np.column_stack([inv.a * x + inv.b * y + inv.c, inv.d * x + inv.e * y + inv.f])
        gp = shapely.transform(g_wgs, f)
        x0, y0, x1, y1 = gp.bounds
        c0, r0, c1, r1 = int(x0) - 10, int(y0) - 10, int(x1) + 11, int(y1) + 11
        if c0 < 0 or r0 < 0 or c1 > self.dark.shape[1] or r1 > self.dark.shape[0]:
            return None
        d = self.dark[r0:r1, c0:c1]
        gl = shapely.affinity.translate(gp, -c0, -r0)
        near = features.rasterize([(gl.buffer(8 / self.pxm), 1)], out_shape=d.shape, fill=0, dtype="uint8").astype(bool)
        wide = features.rasterize([(gl.buffer(30 / self.pxm), 1)], out_shape=d.shape, fill=0, dtype="uint8").astype(bool)
        if near.sum() < 4:
            return None
        a, b = float(d[near].mean()), float(d[wide].mean())
        return ("pier" if a >= 0.12 else ("water" if b <= 0.02 else "unknown")), round(a, 2), round(b, 2)


def load_research():
    p = HERE / "research.csv"
    return list(csv.DictReader(open(p))) if p.exists() else []


def street_names(tracks):
    """a street that runs in line with the pier and ends within 60 m of its landward end -> 'foot of <street>'."""
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    segs = []
    for f in ("roads_local", "roads_region"):
        for name, wkb in con.execute(f"SELECT name, ST_AsWKB(geometry) FROM '{E.ROOT}/data/raw/overture/2026-10-21.0/{f}.parquet' WHERE name IS NOT NULL").fetchall():
            segs.append((name, to_utm(shapely.from_wkb(bytes(wkb)))))
    tree = STRtree([s[1] for s in segs])
    out = []
    for t in tracks:
        g = t["g"]
        c = np.array(g.minimum_rotated_rectangle.exterior.coords)[:4]
        e1, e2 = c[1] - c[0], c[2] - c[1]
        if np.hypot(*e1) < np.hypot(*e2):
            ends = [(c[1] + c[2]) / 2, (c[3] + c[0]) / 2]
        else:
            ends = [(c[0] + c[1]) / 2, (c[2] + c[3]) / 2]
        ax = ends[1] - ends[0]
        ax = ax / (np.hypot(*ax) + 1e-9)
        best = None
        for e in ends:
            pt = shapely.Point(*e)
            for j in tree.query(pt.buffer(60)):
                name, line = segs[int(j)]
                d = line.distance(pt)
                if d > 60:
                    continue
                lc = np.array(line.coords)
                k = int(np.argmin(np.hypot(*(lc - e).T)))
                k = min(max(k, 1), len(lc) - 1)
                v = lc[k] - lc[k - 1]
                v = v / (np.hypot(*v) + 1e-9)
                if abs(float(v @ ax)) < math.cos(math.radians(25)):
                    continue
                if best is None or d < best[0]:
                    best = (d, name)
        out.append(best[1] if best else "")
    return out


def clean(obs):
    """observations in time order as runs of P (pier) / A (absent); single contrary observations inside a run are noise."""
    seq = sorted([o for o in obs if o["state"] != "unknown"], key=lambda o: ((o["lo"] + o["hi"]) / 2, o["hi"]))
    while seq and seq[0]["state"] == "land":          # 'land' before the first pier says nothing
        seq.pop(0)
    lab = ["P" if o["state"] == "pier" else "A" for o in seq]
    for i in range(1, len(lab) - 1):                  # P A P -> P P P ;  A P A stays (a short-lived pier is possible)
        if lab[i] == "A" and lab[i - 1] == "P" and lab[i + 1] == "P":
            lab[i] = "x"
    runs = []
    for o, l in zip(seq, lab):
        if l == "x":
            continue
        if runs and runs[-1][0] == l:
            runs[-1][1].append(o)
        else:
            runs.append([l, [o]])
    return runs, sum(l == "x" for l in lab)


def quality(a, b):
    return "bracket" if (b - a) <= 20 else "estimated"


def segments(t):
    """lifespans of the pier(s) at one place."""
    runs, noise = clean(t["obs"])
    standing = t["osm"] is not None
    segs = []
    for i, (l, os_) in enumerate(runs):
        if l != "P":
            continue
        prev = runs[i - 1][1] if i > 0 else None
        nxt = runs[i + 1][1] if i + 1 < len(runs) else None
        b_s = min(o["hi"] for o in os_)
        first = min(os_, key=lambda o: o["hi"])
        last = max(os_, key=lambda o: o["lo"])
        a_e = last["lo"]
        seg = dict(obs=os_, first=first, last=last)
        if prev:
            pw = max(prev, key=lambda o: o["lo"])
            a_s = min(pw["lo"], b_s)
            seg.update(start=round((a_s + b_s) / 2, 1), start_quality=quality(a_s, b_s), start_bound=False,
                       start_note=f"not on {pw['label']}; first on {first['label']}")
        else:
            seg.update(start=float(b_s), start_quality="estimated", start_bound=True,
                       start_note=f"already on the first source of its place, {first['label']}: built by then, earlier life not traced")
        if nxt:
            nw = min(nxt, key=lambda o: o["hi"])
            b_e = max(nw["hi"], a_e)
            seg.update(end=round((a_e + b_e) / 2, 1), end_quality=quality(a_e, b_e), end_note=f"last on {last['label']}; gone on {nw['label']}"
                       + (" (its place is land there)" if nw["state"] == "land" else ""))
        elif standing:
            seg.update(end=9999, end_quality="recorded", end_note="stands (OpenStreetMap)")
        else:
            seg.update(end=round((a_e + TODAY) / 2, 1), end_quality=quality(a_e, TODAY),
                       end_note=f"last on {last['label']}; not in OpenStreetMap {TODAY}")
        segs.append(seg)
    if standing and (not runs or runs[-1][0] == "A"):
        # today's pier is on no map: built after the last source that shows water there
        if runs:
            pw = max(runs[-1][1], key=lambda o: o["lo"])
            segs.append(dict(obs=[], first=None, last=None, start=round((pw["lo"] + TODAY) / 2, 1), start_quality=quality(pw["lo"], TODAY), start_bound=False,
                             start_note=f"not on {pw['label']}; in OpenStreetMap {TODAY}", end=9999, end_quality="recorded", end_note="stands (OpenStreetMap)"))
        else:
            segs.append(dict(obs=[], first=None, last=None, start=None, start_quality="estimated", start_bound=True,
                             start_note="on no dated source used here", end=9999, end_quality="recorded", end_note="stands (OpenStreetMap)"))
    return segs, noise


def shed_of(seg):
    """shed / open from the sheets that draw buildings: USGS 1:24,000 (hatched or black = roofed) and charts from 1959."""
    ev = [(o["lo"], o["hi"], o["ink"] >= 0.3, o["label"]) for o in seg["obs"] if o.get("ink") is not None and not o.get("stroke") and (not o["chart"] or o["lo"] >= 1959)]
    if not ev:
        return dict(shed="none", shed_note="no source that shows roofs")
    ev.sort()
    flags = [e[2] for e in ev]
    if not any(flags):
        return dict(shed="none", shed_note="drawn as an open deck")
    out = dict(shed="shed", shed_note="drawn roofed (hatched / black) on " + "; ".join(e[3] for e in ev if e[2])[:160])
    if not all(flags):
        k = max(i for i, f in enumerate(flags) if f)
        if k + 1 < len(flags) and all(flags[:k + 1]):                 # roofed, then open
            out["shed_end"] = round((ev[k][0] + ev[k + 1][1]) / 2, 1)
            out["shed_note"] += f"; open deck on {ev[k + 1][3]}"
        j = min(i for i, f in enumerate(flags) if f)
        if j > 0 and all(flags[j:]):                                 # open, then roofed
            out["shed_start"] = round((ev[j - 1][0] + ev[j][1]) / 2, 1)
        if sum(flags) < len(flags) / 2 and "shed_end" not in out and "shed_start" not in out:
            return dict(shed="none", shed_note="drawn open on most sources")
    return out


def main():
    raw = json.load(open(E.OUT / "tracks.json"))
    tracks = []
    for r in raw:
        g_w = shape(r["geom"])
        tracks.append(dict(r, gw=g_w, g=to_utm(g_w)))
    strokes = [Strokes(*a) for a in STROKE_SHEETS]
    for t in tracks:
        for s in strokes:
            r = s.look(t["gw"])
            if r is not None and r[0] != "unknown":
                t["obs"].append(dict(src=s.name, label=s.label, lo=s.lo, hi=s.hi, state=r[0], solid=r[1], core=None, ink=None, chart=False, stroke=True))
    sheets = E.SHEETS

    # made land under the outline during its life (terrain grid, 38 m cells) and today's buildings on it
    gm = json.load(open(E.ROOT / "data/interim/grid_detail_meta.json"))
    ly = np.load(E.ROOT / "data/interim/grid_detail_landyear.npy")
    gtr = rasterio.Affine(*gm["transform"])
    wm = pyproj.Transformer.from_crs("EPSG:32618", "EPSG:3857", always_xy=True)
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")

    def land_years(g):
        pts = [g.representative_point()] + [g.exterior.interpolate(f, normalized=True) for f in np.linspace(0, 1, 12, endpoint=False)]
        inner = [p for p in [shapely.Point(*c) for c in np.array(g.buffer(-3).exterior.coords)[::3]]] if not g.buffer(-3).is_empty and g.buffer(-3).geom_type == "Polygon" else []
        X, Y = wm.transform([p.x for p in pts + inner], [p.y for p in pts + inner])
        c, r = ~gtr * (np.array(X), np.array(Y))
        v = ly[np.clip(r.astype(int), 0, ly.shape[0] - 1), np.clip(c.astype(int), 0, ly.shape[1] - 1)]
        return v

    research = load_research()
    rpts = [(shapely.Point(*UTM.transform(float(r["lon"]), float(r["lat"]))), r) for r in research]
    names = street_names(tracks)
    feats, review = [], []
    for t, street in zip(tracks, names):
        segs, noise = segments(t)
        if not segs:
            review.append(dict(reason="never a pier on any source", borough=t["borough"], lon=round(t["gw"].centroid.x, 5), lat=round(t["gw"].centroid.y, 5)))
            continue
        L, Wd = dims(t["g"])
        lyv = land_years(t["g"])
        hits = [r for p, r in rpts if t["g"].distance(p) <= float(r.get("radius_m") or 25)]
        for k, seg in enumerate(segs):
            standing = seg["end"] == 9999
            # single unconfirmed sighting: drop when another source of the same years shows water
            if not standing and len(seg["obs"]) == 1 and t["osm"] is None:
                o = seg["obs"][0]
                contra = [x for x in t["obs"] if x["state"] in ("water", "land") and x["src"] != o["src"] and abs((x["lo"] + x["hi"]) / 2 - (o["lo"] + o["hi"]) / 2) <= 4]
                if contra:
                    review.append(dict(reason=f"one sighting ({o['label']}) against {contra[0]['label']}", borough=t["borough"], lon=round(t["gw"].centroid.x, 5), lat=round(t["gw"].centroid.y, 5)))
                    continue
            geom = t["gw"]
            src_sheet = t.get("outline_src")
            if t["osm"] is not None and not standing and t.get("map_geom"):
                geom = shape(t["map_geom"])             # an earlier pier on the site of today's: the outline the maps give
            p = dict(name=(t["osm"]["name"] if t["osm"] and standing else "") or (f"Pier, foot of {street}" if street else ""),
                     start_year=seg["start"], end_year=seg["end"], start_quality=seg["start_quality"], end_quality=seg["end_quality"],
                     start_is_upper_bound=seg["start_bound"], deck_m=2.5, borough=t["borough"], length_m=round(L), width_m=round(Wd))
            p.update(shed_of(seg))
            if p["shed"] != "none":
                p["shed_m"] = 10.0
            note = [seg["start_note"], seg["end_note"], p.pop("shed_note")]
            if p["shed"] != "none":
                note.append("shed height 10 m is an estimate (one-storey transit shed)")
            if standing and t["osm"] is not None:
                p["source"] = "osm"
                rec = t["osm"].get("record") or ""
                m = re.match(r"([wr])(\d+)", rec)
                p["source_url"] = f"https://www.openstreetmap.org/{'way' if m.group(1) == 'w' else 'relation'}/{m.group(2)}" if m else SRC_URL["osm"]
            elif src_sheet and src_sheet.startswith("chart_"):
                cid = src_sheet[6:-4]
                p["source"] = "noaa_" + cid
                p["source_url"] = f"https://historicalcharts.noaa.gov/includes/downloadsingle.php?filename={cid}&fileExt=.jpg"
            elif src_sheet:
                p["source"] = "usgs_" + src_sheet.replace("_geo.tif", "")
                p["source_url"] = sheets[src_sheet]["url"]
            else:
                p["source"], p["source_url"] = "osm", SRC_URL["osm"]
            # ground: share of the outline on cells that are land while the pier stands
            if seg["start"] is not None:
                p["land_share"] = round(float(np.mean(lyv <= (seg["end"] if seg["end"] != 9999 else TODAY) - 1)), 2)
            for r in hits:
                if (r.get("applies") or "last") == "last" and k != len(segs) - 1:
                    continue
                if (r.get("applies") or "last") == "first" and k != 0:
                    continue
                for f in ("name", "shed"):
                    if r.get(f):
                        p[f] = r[f]
                for f in ("start_year", "end_year", "shed_start", "shed_end", "shed_m", "deck_m"):
                    if r.get(f):
                        p[f] = float(r[f]) if "." in r[f] else int(r[f])
                        if f == "start_year":
                            p["start_quality"], p["start_is_upper_bound"] = r.get("start_quality") or "recorded", False
                        if f == "end_year":
                            p["end_quality"] = r.get("end_quality") or "recorded"
                note.insert(0, f"researched: {r['note']} [{r['source_url']}]")
                p["research_url"] = r["source_url"]
            if noise:
                note.append(f"{noise} source(s) in between do not show it (taken as misreadings)")
            p["note"] = "; ".join(n for n in note if n)
            p["evidence"] = " ".join(f"{o['lo']}{'s' if o.get('stroke') else ('c' if o['chart'] else 'u')}:{o['state'][0]}" for o in
                                     sorted([o for o in t["obs"] if o["state"] != "unknown"], key=lambda o: (o["lo"], o["hi"])))
            feats.append(dict(type="Feature", geometry=mapping(geom), properties=p))
    # ids, order
    code = {"Manhattan": "mn", "Brooklyn": "bk", "Queens": "qn", "Bronx": "bx", "Staten Island": "si"}
    feats.sort(key=lambda f: (f["properties"]["borough"], round(shape(f["geometry"]).centroid.y, 4), round(shape(f["geometry"]).centroid.x, 4), f["properties"]["start_year"] or 0))
    cnt = Counter()
    for f in feats:
        b = code[f["properties"]["borough"]]
        cnt[b] += 1
        f["properties"] = dict(id=f"pier_{b}_{cnt[b]:04d}", **f["properties"])
        f["geometry"] = mapping(shapely.set_precision(shape(f["geometry"]), 1e-6))
    json.dump(dict(type="FeatureCollection", features=feats), open(HERE / "piers.geojson", "w"))
    with open(HERE / "review.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["reason", "borough", "lon", "lat"])
        w.writeheader()
        w.writerows(review)
    P = [f["properties"] for f in feats]
    dec = lambda y: "standing" if y == 9999 else ("unknown" if y is None else f"{int(y // 10 * 10)}s")
    stats = dict(features=len(P), standing=sum(p["end_year"] == 9999 for p in P), vanished=sum(p["end_year"] != 9999 for p in P),
                 by_borough=dict(Counter(p["borough"] for p in P)), by_borough_vanished=dict(Counter(p["borough"] for p in P if p["end_year"] != 9999)),
                 start_decade=dict(sorted(Counter(dec(p["start_year"]) for p in P).items())), end_decade=dict(sorted(Counter(dec(p["end_year"]) for p in P).items())),
                 start_quality=dict(Counter(p["start_quality"] for p in P)), end_quality=dict(Counter(p["end_quality"] for p in P)),
                 start_upper_bound_only=sum(p["start_is_upper_bound"] for p in P), shed=dict(Counter(p["shed"] for p in P)),
                 dropped=dict(Counter(r["reason"].split(" (")[0] for r in review)), outline_source=dict(Counter(p["source"].split("_")[0] for p in P)))
    json.dump(stats, open(HERE / "stats.json", "w"), indent=1)
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
