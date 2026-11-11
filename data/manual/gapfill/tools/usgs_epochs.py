"""Woodland and built-up ground of the whole map (31 areas: the 26 counties and the five boroughs) read off the
colour tints of USGS / Army Map Service topographic sheets (public domain, USGS Historical Topographic Map Collection).

Notes, sheet table and validation: data/research/usgs_epochs.md

    .venv/bin/python -I data/manual/gapfill/tools/usgs_epochs.py run <sheet key> [wood] [urban]   # fetch, read, delete the scan
    .venv/bin/python -I data/manual/gapfill/tools/usgs_epochs.py assemble                          # pieces -> the geojson files
    .venv/bin/python -I data/manual/gapfill/tools/usgs_epochs.py preview <key> lon lat [halfwidth_px]  # overlay PNG
    .venv/bin/python -I data/manual/gapfill/tools/usgs_epochs.py validate

One sheet at a time, strips of 700 rows (under 1.5 GB). The scan is deleted once its pieces are written
(data/interim/usgs_epochs_raw/pieces/<key>_<kind>.geojson, small).
"""
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "data" / "manual" / "gapfill"
RAW = ROOT / "data" / "interim" / "usgs_epochs_raw"
PIECES = RAW / "pieces"
B = "https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/"
UA = "NYCThroughTime-research/0.1"

AREAS = {"34017": "Hudson", "34003": "Bergen", "34013": "Essex", "34039": "Union", "34031": "Passaic", "36119": "Westchester",
         "36087": "Rockland", "36059": "Nassau", "36103": "Suffolk", "36079": "Putnam", "36071": "Orange", "36027": "Dutchess",
         "36111": "Ulster", "36105": "Sullivan", "34023": "Middlesex", "34025": "Monmouth", "34029": "Ocean", "34035": "Somerset",
         "34027": "Morris", "34037": "Sussex", "34019": "Hunterdon", "34021": "Mercer", "09120": "Greater Bridgeport",
         "09190": "Western Connecticut", "09170": "South Central Connecticut", "42103": "Pike",
         "36005": "Bronx", "36047": "Brooklyn", "36061": "Manhattan", "36081": "Queens", "36085": "Staten Island"}
INNER = {"Hudson", "Bergen", "Essex", "Union", "Passaic", "Westchester", "Rockland"}
CITY = {"Bronx", "Brooklyn", "Manhattan", "Queens", "Staten Island"}

# key: (state folder, file, year printed, scale, title, nominal box (w, s, e, n), rules)
# rules: HSV windows read off each scan's own colours (scans differ in cast and print).
HSV = lambda h, s, v=0.7: {"h": h, "smin": s, "vmin": v}
SHEETS = {
    "newark57": ("NJ", "NJ_Newark_472533_1957_250000_geo.tif", 1957, 250000, "Newark, NK 18-11, ed. 1957 (AMS)", (-76, 40, -74, 41),
                 {"wood": HSV((0.19, 0.30), 0.13, 0.75), "urban": HSV((0.105, 0.15), 0.5, 0.9)}),
    "ny57": ("NY", "NY_New%20York_130815_1957_250000_geo.tif", 1957, 250000, "New York, NK 18-12, ed. 1957 (AMS)", (-74, 40, -72, 41),
             {"wood": HSV((0.22, 0.34), 0.30, 0.8), "urban": HSV((0.12, 0.18), 0.65, 0.9)}),
    "hartford61": ("CT", "CT_Hartford_331221_1961_250000_geo.tif", 1961, 250000, "Hartford, NK 18-9, ed. 1961 (AMS)", (-74, 41, -72, 42),
                   {"wood": HSV((0.23, 0.32), 0.55, 0.75), "urban": HSV((0.11, 0.17), 0.8, 0.9)}),
    "scranton59": ("PA", "PA_Scranton_221783_1959_250000_geo.tif", 1959, 250000, "Scranton, NK 18-8, ed. 1959 (AMS)", (-76, 41, -74, 42),
                   {"wood": HSV((0.21, 0.29), 0.55, 0.75), "urban": HSV((0.10, 0.17), 0.6, 0.9)}),
    "wilmington57": ("DE", "DE_Wilmington_463186_1957_250000_geo.tif", 1957, 250000, "Wilmington, NJ-DE, ed. 1957 (AMS)", (-76, 39, -74, 40),
                     {"wood": HSV((0.20, 0.30), 0.105, 0.85), "urban": HSV((0.10, 0.17), 0.5, 0.9)}),
    "albany59": ("NY", "NY_Albany_136546_1959_250000_geo.tif", 1959, 250000, "Albany, NK 18-6, ed. 1959 (AMS)", (-74, 42, -72, 43),
                 {"wood": HSV((0.21, 0.29), 0.55, 0.75), "urban": HSV((0.10, 0.17), 0.6, 0.9)}),
    "binghamton58": ("NY", "NY_Binghamton_123306_1958_250000_geo.tif", 1958, 250000, "Binghamton, NK 18-5, ed. 1958 (AMS)", (-76, 42, -74, 43),
                     {"wood": HSV((0.21, 0.29), 0.55, 0.75), "urban": HSV((0.10, 0.17), 0.6, 0.9)}),
    "providence57": ("RI", "RI_Providence_463160_1957_250000_geo.tif", 1957, 250000, "Providence, NK 19-10, ed. 1957 (AMS)", (-72, 41, -69.8833333, 42),
                     {"wood": HSV((0.20, 0.30), 0.12, 0.8), "urban": HSV((0.10, 0.17), 0.5, 0.9)}),
    # the sheets of 1946-1950 (earlier AMS printing: orange urban tint, yellow-green woodland)
    "newark49": ("NJ", "NJ_Newark_255456_1949_250000_geo.tif", 1949, 250000, "Newark, NK 18-11, ed. 1949 (AMS)", (-76, 40, -74, 41),
                 {"wood": HSV((0.16, 0.22), 0.5, 0.5), "urban": HSV((0.105, 0.15), 0.8, 0.9)}),
    "ny49": ("NY", "NY_New%20York_130809_1949_250000_geo.tif", 1949, 250000, "New York, NK 18-12, ed. 1949 (AMS)", (-74, 40, -72, 41),
             {"wood": HSV((0.17, 0.23), 0.5, 0.5), "urban": HSV((0.10, 0.145), 0.85, 0.8)}),
    "hartford47": ("CT", "CT_Hartford_331218_1947_250000_geo.tif", 1947, 250000, "Hartford, NK 18-9, ed. 1947 (AMS)", (-74, 41, -72, 42),
                   {"wood": HSV((0.28, 0.36), 0.28, 0.75), "urban": HSV((0.09, 0.17), 0.7, 0.9)}),
    "scranton50": ("PA", "PA_Scranton_707601_1950_250000_geo.tif", 1950, 250000, "Scranton, NK 18-8, ed. 1950 (AMS)", (-76, 41, -74, 42),
                   {"wood": HSV((0.17, 0.22), 0.5, 0.5), "urban": HSV((0.07, 0.125), 0.6, 0.9)}),
    "wilmington46": ("DE", "DE_Wilmington_707694_1946_250000_geo.tif", 1946, 250000, "Wilmington, NJ-DE, ed. 1946 (AMS)", (-76, 39, -74, 40),
                     {"wood": HSV((0.16, 0.22), 0.5, 0.5), "urban": HSV((0.105, 0.15), 0.8, 0.9)}),
    "albany48": ("NY", "NY_Albany_136545_1948_250000_geo.tif", 1948, 250000, "Albany, NK 18-6, ed. 1948 (AMS)", (-74, 42, -72, 43),
                 {"wood": HSV((0.155, 0.22), 0.55, 0.5), "urban": HSV((0.07, 0.145), 0.7, 0.9)}),
}


def url(key):
    st, fn = SHEETS[key][:2]
    return B + st + "/" + fn


def local(key):
    return RAW / SHEETS[key][1].replace("%20", "_")


def fetch(key):
    p = local(key)
    if not p.exists():
        RAW.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url(key), headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=300) as r, open(str(p) + ".part", "wb") as f:
            while True:
                b = r.read(1 << 20)
                if not b:
                    break
                f.write(b)
        Path(str(p) + ".part").rename(p)
    return p


def areas():
    import geopandas as gpd
    g = gpd.read_file("zip://" + str(ROOT / "data/raw/tiger/tl_2024_us_county.zip"))
    g = g[g.GEOID.isin(AREAS)].copy()
    g["name"] = g.GEOID.map(AREAS)
    return g.to_crs(4326)[["name", "geometry"]]


def hsv(a):
    """a: (3, h, w) uint8 -> h, s, v float32 arrays."""
    f = a.astype("float32") / 255.0
    mx, mn = f.max(0), f.min(0)
    d = mx - mn
    s = np.where(mx > 0, d / np.maximum(mx, 1e-6), 0)
    dd = np.maximum(d, 1e-6)
    r, g, b = f
    h = np.where(mx == r, ((g - b) / dd) % 6, np.where(mx == g, (b - r) / dd + 2, (r - g) / dd + 4)) / 6.0
    return h, s, mx


def read_masks(key, kinds, strip=700):
    """-> dict kind -> (bool mask, transform, crs) over the window of the sheet that holds the areas."""
    import rasterio
    from rasterio.windows import Window
    from rasterio.warp import transform_bounds
    from scipy import ndimage as ndi
    p = fetch(key)
    rules = SHEETS[key][6]
    w0, s0, e0, n0 = SHEETS[key][5]
    with rasterio.open(p) as src:
        W, S, E, N = max(w0, -75.37), max(s0, 39.47), min(e0, -71.85), min(n0, 42.2)
        x0, y0, x1, y1 = transform_bounds("EPSG:4326", src.crs, W - 0.01, S - 0.01, E + 0.01, N + 0.01)
        c0, r1 = ~src.transform * (x0, y0)
        c1, r0 = ~src.transform * (x1, y1)
        c0, c1 = int(max(0, min(c0, c1) - 5)), int(min(src.width, max(c0, c1) + 5))
        r0, r1 = int(max(0, min(r0, r1) - 5)), int(min(src.height, max(r0, r1) + 5))
        out = {k: np.zeros((r1 - r0, c1 - c0), bool) for k in kinds}
        m = 8
        for ra in range(r0, r1, strip):
            rb = min(ra + strip, r1)
            ma, mb = max(ra - m, 0), min(rb + m, src.height)
            a = src.read(window=Window(c0, ma, c1 - c0, mb - ma))
            h, s, v = hsv(a)
            del a
            for k in kinds:
                R = rules[k]
                g = (h >= R["h"][0]) & (h <= R["h"][1]) & (s >= R["smin"]) & (v >= R["vmin"])
                if k == "wood":              # ink (roads, streams, marsh marks, contours, water) is neutral: wood where the
                    # green outweighs bare paper within 9 px, and there is some green
                    neutral = (v < 0.8) | ((s > 0.3) & ~g) | ((h > 0.42) & (s > 0.1))
                    paper = ~g & ~neutral
                    gs = ndi.uniform_filter(g.astype("float32"), 9)
                    ps = ndi.uniform_filter(paper.astype("float32"), 9)
                    t = (gs > 0.12) & (gs >= 0.5 * (gs + ps))
                    t = ndi.binary_opening(t, iterations=1)
                else:
                    t = ndi.uniform_filter(g.astype("float32"), 5) > 0.35
                    t = ndi.binary_closing(t, iterations=1)
                out[k][ra - r0:rb - r0] = t[ra - ma:rb - ma]
        tr = src.transform * src.transform.translation(c0, r0)
        return out, tr, src.crs, src.res[0]


def vectorise(mask, tr, crs, res, key, kind, minpx):
    """-> array of simplified polygons in lon/lat, clipped to the sheet's nominal box."""
    import shapely
    import shapely.geometry as sg
    from pyproj import Transformer
    from rasterio import features
    from scipy import ndimage as ndi
    if kind == "wood":
        # symbols (roads, streams, marsh marks) under ~230 m wide break the tint: closed; holes under 60 pixels are woodland
        mask = ndi.binary_closing(mask, iterations=5)
        lab, n = ndi.label(~mask)
        sz = np.bincount(lab.ravel())
        mask |= (sz[lab] < 60) & (lab > 0)
        del lab
    lab, n = ndi.label(mask)
    if n:
        sz = np.bincount(lab.ravel())
        mask = (sz[lab] >= minpx) & (lab > 0)
    del lab
    polys = np.array([sg.shape(g) for g, v in features.shapes(mask.astype("uint8"), mask=mask, transform=tr) if v == 1], dtype=object)
    if not len(polys):
        return polys
    polys = shapely.simplify(polys, 30.0)
    t = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    polys = shapely.transform(polys, lambda c: np.column_stack(t.transform(c[:, 0], c[:, 1])))
    polys = shapely.make_valid(polys)
    w, s, e, n_ = SHEETS[key][5]
    box = sg.box(w + 0.0008, s + 0.0008, e - 0.0008, n_ - 0.0008)
    inside = shapely.contains(box, polys)
    polys[~inside] = shapely.intersection(polys[~inside], box)
    return polys[~shapely.is_empty(polys)]


def run(key, kinds):
    import shapely
    import shapely.geometry as sg
    PIECES.mkdir(parents=True, exist_ok=True)
    kinds = kinds or ["wood", "urban"]
    masks, tr, crs, res = read_masks(key, kinds)
    A = areas()
    for k in kinds:
        minpx = 12 if k == "wood" else 6
        polys = vectorise(masks.pop(k), tr, crs, res, key, k, minpx)
        feats = []
        if len(polys):
            tree = shapely.STRtree(polys)
            for r in A.itertuples():
                i = tree.query(r.geometry, predicate="intersects")
                if not len(i):
                    continue
                pp = polys[i]
                inside = shapely.contains(r.geometry, pp)
                pp[~inside] = shapely.intersection(pp[~inside], r.geometry)
                for p in pp:
                    for q in (p.geoms if hasattr(p, "geoms") else [p]):
                        if q.geom_type != "Polygon" or q.area < 2e-7:
                            continue
                        feats.append({"type": "Feature", "geometry": sg.mapping(shapely.set_precision(q, 1e-5)),
                                      "properties": {"county": r.name}})
        (PIECES / f"{key}_{k}.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
        import resource
        print(key, k, len(feats), "polygons; peak", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024, "MB", flush=True)


def preview(key, lon, lat, hw=500):
    import rasterio
    from PIL import Image
    from rasterio.features import rasterize
    from rasterio.warp import transform, transform_geom
    import shapely.geometry as sg
    p = fetch(key)
    with rasterio.open(p) as s:
        x, y = transform("EPSG:4326", s.crs, [lon], [lat])
        r, c = s.index(x[0], y[0])
        hh = hw * 3 // 4
        w = s.read(window=((r - hh, r + hh), (c - hw, c + hw)), boundless=True, fill_value=255)
        tr = s.window_transform(((r - hh, r + hh), (c - hw, c + hw)))
        img = np.moveaxis(w, 0, 2).copy()
        for kind, col in (("wood", (255, 0, 255)), ("urban", (0, 0, 255))):
            f = PIECES / f"{key}_{kind}.geojson"
            if not f.exists():
                continue
            shapes = []
            for ft in json.loads(f.read_text())["features"]:
                shapes.append((transform_geom("EPSG:4326", s.crs, ft["geometry"]), 1))
            if not shapes:
                continue
            m = rasterize(shapes, out_shape=w.shape[1:], transform=tr)
            from scipy import ndimage as ndi
            edge = m.astype(bool) & ~ndi.binary_erosion(m.astype(bool), iterations=2)
            img[edge] = col
    Image.fromarray(img).save(str(PIECES.parent / f"preview_{key}.png"))
    print(PIECES.parent / f"preview_{key}.png")


# which pieces go into which product file: product -> (kind, [sheet keys], year in the file's name, label)
PRODUCTS = {
    "all_woodland_1957.geojson": ("wood", ["newark57", "ny57", "providence57", "hartford61", "scranton59", "wilmington57", "albany59", "binghamton58"],
                                  "woodland", "green woodland tint of the Army Map Service 1:250,000 series, editions 1957-1961"),
    "all_tint_1957.geojson": ("urban", ["newark57", "ny57", "providence57", "hartford61", "scranton59", "wilmington57", "albany59", "binghamton58"],
                              "built_up", "urban tint (yellow / orange) of the Army Map Service 1:250,000 series, editions 1957-1961"),
}


def _ha(g):
    import shapely
    lat = g.centroid.y
    return g.area * (111320.0 ** 2) * np.cos(np.radians(lat)) / 1e4


def assemble(names=None):
    import shapely
    import shapely.geometry as sg
    for fn, (kind, keys, label, method) in PRODUCTS.items():
        if names and fn not in names:
            continue
        feats = []
        for key in keys:
            f = PIECES / f"{key}_{kind}.geojson"
            if not f.exists():
                continue
            by = {}
            for ft in json.loads(f.read_text())["features"]:
                by.setdefault(ft["properties"]["county"], []).append(sg.shape(ft["geometry"]))
            st, name, year, scale, title, box, _ = SHEETS[key]
            for county, gs in sorted(by.items()):
                g = shapely.set_precision(shapely.union_all(gs), 1e-5)
                if g.is_empty:
                    continue
                feats.append({"type": "Feature", "geometry": sg.mapping(g),
                              "properties": {"county": county, "kind": label, "year": year, "year_note": "edition printed on the sheet (the survey is older)",
                                             "sheet": title, "scale": f"1:{scale}", "source_url": url(key).replace("%20", "%20"),
                                             "method": method, "area_ha": round(_ha(g)),
                                             "confidence": "medium" if kind == "wood" else "medium-high", "licence": "public domain (USGS)"}})
        (OUT / fn).write_text(json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")))
        sz = (OUT / fn).stat().st_size / 1e6
        print(fn, len(feats), "features,", round(sz, 1), "MB,", sum(f["properties"]["area_ha"] for f in feats), "ha", flush=True)


BORO = {1: "Manhattan", 2: "Bronx", 3: "Brooklyn", 4: "Queens", 5: "Staten Island"}


def points(cols=("lon", "lat", "start_year", "end_year", "conf", "county")):
    import pandas as pd
    out = []
    for f in ("county_points_inner", "county_points_outer"):
        out.append(pd.read_parquet(ROOT / "data/interim" / f"{f}.parquet", columns=list(cols), filters=[("conf", "=", "exact")]))
    c = pd.read_parquet(ROOT / "data/interim/nyc_building_points.parquet", columns=["lon", "lat", "start_year", "end_year", "conf", "boro"],
                        filters=[("conf", "=", "exact")])
    c["county"] = c.boro.map({str(k): v for k, v in BORO.items()})
    c = c[c.county.notna()]
    out.append(c[list(cols)])
    return pd.concat(out, ignore_index=True)


def validate(fn, year, kind, shifts=False):
    """kind 'wood': share of today's buildings recorded before `year` that lie inside the polygons (want ~0).
       kind 'urban': recall of buildings recorded before `year` and share of those recorded after year + 10 (want small)."""
    import shapely
    import shapely.geometry as sg
    import pandas as pd
    d = json.loads((OUT / fn).read_text())
    polys = [sg.shape(f["geometry"]) for f in d["features"]]
    g = shapely.union_all(polys)
    shapely.prepare(g)
    P = points()
    P = P[P.end_year >= 9000]
    rows = []
    for county, q in P.groupby("county"):
        x, y = q.lon.values, q.lat.values
        inside = shapely.contains_xy(g, x, y)
        s = q.start_year.values
        early = s < year
        late = s > year + 10
        r = {"county": county, "early_n": int(early.sum()), "early_in": float(inside[early].mean()) if early.any() else np.nan,
             "late_n": int(late.sum()), "late_in": float(inside[late].mean()) if late.any() else np.nan}
        rows.append(r)
    df = pd.DataFrame(rows).set_index("county")
    tot_e = (df.early_n * df.early_in.fillna(0)).sum() / df.early_n.sum()
    tot_l = (df.late_n * df.late_in.fillna(0)).sum() / df.late_n.sum()
    print(f"## {fn}  (year {year}, {kind}); polygons cover {g.area * (111320.0 ** 2) * 0.76 / 1e6:.0f} km2 at 41N")
    print("| county | recorded < year | inside | recorded > year+10 | inside |\n|---|---|---|---|---|")
    for c, r in df.iterrows():
        print(f"| {c} | {r.early_n} | {r.early_in:.1%} | {r.late_n} | {r.late_in:.1%} |")
    print(f"| ALL | {df.early_n.sum()} | {tot_e:.1%} | {df.late_n.sum()} | {tot_l:.1%} |")
    if shifts:                                   # registration: shift old buildings east/north in 25 m steps and see where the recall peaks
        old = P[(P.start_year < year - 20)].sample(min(150000, int((P.start_year < year - 20).sum())), random_state=1)
        best = []
        for dx in range(-100, 101, 25):
            row = []
            for dy in range(-100, 101, 25):
                x = old.lon.values + dx / (111320 * 0.757)
                y = old.lat.values + dy / 111320
                row.append(float(shapely.contains_xy(g, x, y).mean()))
            best.append(row)
        b = np.array(best)
        i, j = np.unravel_index(b.argmax(), b.shape)
        print(f"registration: recall at no shift {b[4, 4]:.3f}; best shift of the points dx={(i - 4) * 25} m east, dy={(j - 4) * 25} m north: {b.max():.3f}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "run":
        run(a[1], a[2:])
    elif a[0] == "preview":
        preview(a[1], float(a[2]), float(a[3]), int(a[4]) if len(a) > 4 else 500)
    elif a[0] == "assemble":
        assemble(a[1:])
    elif a[0] == "validate":
        validate(a[1], int(a[2]), a[3], len(a) > 4)
