"""Built-up ground of the six counties on USGS sheets (public domain, USGS Historical Topographic Map Collection).

1. The 15-minute sheets of 1897-98 (Paterson 1898, Staten Island 1898, Harlem 1897 - the copies of the
   extents part): heavy black ink of the built block fronts, read with the extents part's own tool
   (data/manual/extents/tools/usgs_extent.py, unchanged) and clipped to the counties
   -> data/manual/gapfill/counties_builtup_1897.geojson (property `county`).
   The tool knows today's streets only inside (-74.29, 40.47, -73.67, 40.94): nothing is read north of
   40.94 N (Yonkers north of Getty Square, White Plains, the river towns, Rockland) or west of 74.25 W.
2. The flat urban tint of two sheets of the 1940s that draw no block fronts: Orange, N.J., 1:24,000, 1947
   (pink) and Paterson, N.J., 1:31,680, 1944 (yellow) -> data/manual/gapfill/counties_tint_194x.geojson
   (properties `county`, `year`). The tint colour is taken from the sheet itself at a point in the middle
   of the town; a cell of 10 m is tinted when half of the ground within 30 m has that colour.

    .venv/bin/python -I data/manual/gapfill/tools/counties_usgs.py [builtup] [tint]
"""
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import shapely
import shapely.geometry as sg

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "data" / "manual" / "extents" / "tools"))
OUT = ROOT / "data" / "manual" / "gapfill"
FIPS = {"34003": "Bergen", "34013": "Essex", "34031": "Passaic", "34039": "Union", "36119": "Westchester", "36087": "Rockland"}
URL = "https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/"


def counties():
    g = gpd.read_file("zip://" + str(ROOT / "data/raw/tiger/tl_2024_us_county.zip"),
                      where="GEOID IN ('34003','34013','34031','34039','36119','36087')")
    return {FIPS[r.GEOID]: r.geometry for r in g.itertuples()}


def builtup():
    import classify
    import streets as S
    import usgs_extent as U
    cs = {k: classify.to_local(v) for k, v in counties().items()}
    allc = shapely.union_all(list(cs.values()))
    sheets = [s for s in U.SHEETS if s[0] in ("StatenIsland_1898.tif", "NJ_Paterson_255300_1898_62500_geo.tif", "NY_Harlem_129718_1897_62500_geo.tif")]
    feats = []
    for fn, year, q, title, *rest in sheets:
        quad = U.quad_local(q)
        x0, y0, x1, y1 = quad.bounds
        parts = []
        for i in range(3):                      # the quadrangle in nine pieces: a whole sheet at 2.5 m does not fit in 2 GB
            for j in range(3):
                box = sg.box(x0 + (x1 - x0) * i / 3, y0 + (y1 - y0) * j / 3, x0 + (x1 - x0) * (i + 1) / 3, y0 + (y1 - y0) * (j + 1) / 3)
                env = box.buffer(150).intersection(quad).intersection(allc.buffer(100))
                if env.is_empty or env.area < 1e5:
                    continue
                poly, _, _, _ = U.sheet_mask(fn, env, open_m=rest[0] if rest else 7.5)
                if not poly.is_empty:
                    parts.append(poly.intersection(box.buffer(1)))
        if not parts:
            continue
        g = shapely.union_all(parts).buffer(0)
        print(f"{title}: built-up {g.area / 1e4:.0f} ha in the counties", flush=True)
        for name, cpoly in cs.items():
            part = g.intersection(cpoly.buffer(100))
            for p in (part.geoms if hasattr(part, "geoms") else [part]):
                if p.geom_type != "Polygon" or p.area < 1e4:
                    continue
                ll = shapely.transform(p, lambda c: np.column_stack(S.lonlat(c[:, 0], c[:, 1])))
                feats.append({"type": "Feature", "geometry": sg.mapping(shapely.set_precision(ll, 1e-6)),
                              "properties": {"county": name, "year": 1897, "kind": "built_up", "map": title,
                                             "map_url": "https://ngmdb.usgs.gov/topoview/",
                                             "method": "heavy black ink of built block fronts, share within 80 m (extents/tools/usgs_extent.py)",
                                             "confidence": "low-medium", "area_ha": round(p.area / 1e4, 1), "licence": "public domain (USGS)"}})
    (OUT / "counties_builtup_1897.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    tot = {}
    for f in feats:
        tot[f["properties"]["county"]] = tot.get(f["properties"]["county"], 0) + f["properties"]["area_ha"]
    print("counties_builtup_1897.geojson:", len(feats), "polygons;", {k: round(v) for k, v in tot.items()}, "ha")


TINT = [  # file, year printed, reference point inside the tint (lon, lat), state folder
    ("NJ_Orange_254673_1947_24000_geo.tif", 1947, (-74.2040, 40.7700), "NJ"),
    ("NJ_Paterson_255064_1944_31680_geo.tif", 1944, (-74.1650, 40.9120), "NJ"),
]


def tint():
    import rasterio
    from rasterio import features
    from rasterio.warp import transform, transform_geom
    from scipy import ndimage as ndi
    cs = counties()
    feats = []
    for fn, year, ref, st in TINT:
        with rasterio.open(ROOT / "data/raw/gapfill/usgs" / fn) as src:
            a = src.read([1, 2, 3]).astype("int16")
            xs, ys = transform("EPSG:4326", src.crs, [ref[0]], [ref[1]])
            r, c = src.index(xs[0], ys[0])
            win = a[:, r - 60:r + 60, c - 60:c + 60].reshape(3, -1)
            light = win.sum(0) > 520                               # not ink
            col = np.median(win[:, light], axis=1)
            d = np.abs(a - col[:, None, None]).max(0)
            paper = a.min(0) > 235                                  # white paper is not tint
            m = (d < 28) & ~paper
            k = max(1, int(round(5.0 / src.res[0])))                # 10 m cells
            sh = ndi.uniform_filter(m.astype("float32"), int(60 / src.res[0]) | 1)[::k, ::k] > 0.5
            sh = ndi.binary_opening(sh, iterations=2)
            tr = src.transform * src.transform.scale(k, k)
            polys = [sg.shape(g) for g, v in features.shapes(sh.astype("uint8"), mask=sh, transform=tr) if v == 1]
            g = shapely.union_all(polys).simplify(8.0)
            ll = sg.shape(transform_geom(src.crs, "EPSG:4326", sg.mapping(g)))
        ll = shapely.make_valid(ll)
        print(f"{fn}: tint colour {col.astype(int).tolist()}, tinted {g.area / 1e4:.0f} ha", flush=True)
        for name, cpoly in cs.items():
            part = ll.intersection(cpoly)
            for p in (part.geoms if hasattr(part, "geoms") else [part]):
                if p.geom_type == "Polygon" and p.area > 1e-7:
                    feats.append({"type": "Feature", "geometry": sg.mapping(shapely.set_precision(p, 1e-6)),
                                  "properties": {"county": name, "year": year, "kind": "built_up", "map": fn,
                                                 "map_url": URL + st + "/" + fn, "method": "flat urban tint, share within 30 m",
                                                 "confidence": "low-medium", "licence": "public domain (USGS)"}})
    (OUT / "counties_tint_194x.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    print("counties_tint_194x.geojson:", len(feats), "polygons")


if __name__ == "__main__":
    a = sys.argv[1:] or ["builtup", "tint"]
    if "tint" in a:
        tint()
    if "builtup" in a:
        builtup()
