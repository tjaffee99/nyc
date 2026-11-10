"""Built-up area from the USGS 15-minute sheets of 1889-98 (1:62,500).

These sheets draw a built block front as a heavy black band along the street (a fully built block is
a black ring or a solid bar, an open block a thin outline) and a scattered house as a small black
square. Reading: black ink (dark and neutral; water is blue, contours brown) -> share of black within
`win` metres -> threshold -> opening / closing -> polygons, clipped to the quadrangle and to the borough.

  python -I usgs_extent.py calibrate           # black share in reference windows
  python -I usgs_extent.py build [preview dir] # every sheet -> tools/classified/usgs_<borough>_<year>.json
"""
import json, sys
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
import shapely, shapely.geometry as sg
import geopandas as gpd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import classify, usgs, autoalign, streets as S

ROOT = Path(__file__).resolve().parents[4]
INTERIM = ROOT / "data" / "interim" / "extents"
MPP, WIN, THR = 2.5, 80.0, 0.22
# sheet file, year the map shows (survey year from the ScienceBase record), quadrangle (lon0, lat0, lon1, lat1)
SHEETS = [
    ("NY_Harlem_129718_1897_62500_geo.tif", 1897, (-74.0, 40.75, -73.75, 41.0), "Harlem, N.Y.-N.J., edition of 1897"),
    ("NY_Brooklyn_123118_1897_62500_geo.tif", 1897, (-74.0, 40.5, -73.75, 40.75), "Brooklyn, N.Y., edition of 1897"),
    # these two scans are crisper: their block-front bands measure 10-14 m, so heavy ink = opening by 5 m, not 7.5 m
    ("StatenIsland_1898.tif", 1897, (-74.25, 40.5, -74.0, 40.75), "Staten Island, N.J.-N.Y., edition of 1898", 5.0),
    ("NJ_Paterson_255300_1898_62500_geo.tif", 1897, (-74.25, 40.75, -74.0, 41.0), "Paterson, N.J.-N.Y., edition of 1898", 5.0),
    ("Harlem_1891.tif", 1889, (-74.0, 40.75, -73.75, 41.0), "Harlem, N.Y.-N.J., edition of 1891", 5.0),   # faded scan, bands 12-15 m
    ("NY_Brooklyn_8033120_1891_62500_geo.tif", 1889, (-74.0, 40.5, -73.75, 40.75), "Brooklyn, N.Y., edition of 1891"),
]
BORO = {"36061": "manhattan", "36047": "brooklyn", "36081": "queens", "36005": "bronx", "36085": "staten_island"}


def boroughs():
    g = gpd.read_file("zip://" + str(ROOT / "data/raw/tiger/tl_2024_us_county.zip"), where="STATEFP = '36' AND COUNTYFP IN ('061','047','081','005','085')")
    return {BORO[r.GEOID]: classify.to_local(r.geometry) for r in g.itertuples()}


def quad_local(q):
    lon0, lat0, lon1, lat1 = q
    pts = [(lon0, lat0), (lon1, lat0), (lon1, lat1), (lon0, lat1)]
    return sg.Polygon([S.local(*p) for p in pts])


def black_share(rgb, win_px, near_street=None, rail=None, open_m=7.5):
    """Share of HEAVY black ink within the window: ink that survives an opening by a 5 m disc (bands and
    solid blocks at least 15 m thick). Road casings, thin block outlines of open blocks, railway lines and
    most lettering are thinner. Not counted: where more than half of the surroundings (150 m) is water
    (blue: pier heads); ink further than 60 m from a street of today (lettering printed in the rivers and
    in the hills); ink within 15 m of a railway of today (Overture rail)."""
    a = rgb.astype(np.int16)
    lum = a @ np.array([0.299, 0.587, 0.114])
    inside = lum < 250
    lo, hi = np.percentile(lum[inside], [2, 95])
    cut = min(0.45 * lo + 0.55 * hi - 15, 160)     # 1897 scans: about 105; the faded brown 1891 Harlem scan: about 150
    black = (lum < cut) & ((a.max(-1) - a.min(-1)) < 70)
    if rail is not None:
        black &= ~rail
    heavy = ndi.binary_opening(black, classify.disc(open_m / MPP))
    blue = (a[..., 2] > a[..., 0] + 25) & (a[..., 2] > 110)
    water = ndi.uniform_filter(blue.astype(np.float32), int(150 / MPP) | 1) > 0.5
    if near_street is not None:
        heavy &= near_street
    sh = ndi.uniform_filter(heavy.astype(np.float32), int(win_px) | 1)
    sh[water] = 0
    return sh, black


def rail_raster(box, width=30.0):
    import duckdb
    from rasterio import features
    from affine import Affine
    x0, y0, x1, y1 = box
    lo0, la0 = S.lonlat(x0, y0)
    lo1, la1 = S.lonlat(x1, y1)
    con = duckdb.connect()
    con.execute("install spatial; load spatial;")
    rows = con.execute(f"""select ST_AsWKB(geometry) from '{ROOT}/data/raw/overture/2026-10-21.0/rail.parquet'
        where class in ('standard_gauge', 'unknown') is not false and ST_XMax(geometry) > {lo0} and ST_XMin(geometry) < {lo1}
          and ST_YMax(geometry) > {la0} and ST_YMin(geometry) < {la1}""").fetchall()
    shp = (int(round((y1 - y0) / MPP)), int(round((x1 - x0) / MPP)))
    if not rows:
        return np.zeros(shp, bool)
    g = classify.to_local(shapely.union_all(shapely.from_wkb([bytes(r[0]) for r in rows])))
    return features.rasterize([(g.buffer(width / 2), 1)], out_shape=shp, transform=Affine(MPP, 0, x0, 0, -MPP, y1), dtype="uint8").astype(bool)


def sheet_mask(fn, env, thr=THR, open_m=7.5):
    x0, y0, x1, y1 = [5 * np.floor(v / 5) for v in env.bounds]
    t = usgs.TopoMap(fn)
    rgb = t.render(x0, y0, x1, y1, MPP)
    box = (x0, y0, x1, y1)
    near = autoalign.street_raster(box, MPP, width=120.0) > 0
    sh, black = black_share(rgb, WIN / MPP, near_street=near, rail=rail_raster(box), open_m=open_m)
    k = 2                                   # morphology on a 5 m grid (the share is smooth over 80 m)
    mp = MPP * k
    m = sh[::k, ::k] > thr
    m = ndi.binary_opening(m, classify.disc(25 / mp))           # lettering strokes, a house or two, a rail yard line
    m = ndi.binary_closing(np.pad(m, 12), classify.disc(40 / mp))[12:-12, 12:-12]
    lab, n = ndi.label(m)
    if n:
        area = ndi.sum(np.ones_like(lab), lab, np.arange(1, n + 1)) * mp * mp / 1e4
        m = np.isin(lab, [i + 1 for i in range(n) if area[i] >= 1.5])
    lab, n = ndi.label(~m)
    if n:
        area = ndi.sum(np.ones_like(lab), lab, np.arange(1, n + 1)) * mp * mp / 1e4
        edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
        m |= np.isin(lab, [i + 1 for i in range(n) if area[i] < 1.0 and (i + 1) not in edge])
    g = classify.mask_to_polygons(m, x0, y1, mp).intersection(env)
    return g.simplify(4.0), rgb[::k, ::k], (x0, y0, x1, y1), sh


def _unused():
    pass


def main(a):
    if a[0] == "calibrate":
        wins = {"midtown_dense": (6000, 12000, 7000, 13000), "harlem_dense": (8700, 17200, 9700, 18200), "central_park": (6600, 14600, 7300, 15800),
                "central_park": (7100, 15450, 7400, 15750),
                "wash_heights": (7500, 20500, 8500, 21500), "morrisania": (10300, 18800, 11300, 19800), "unionport_plat": (15500, 20300, 16500, 21200),
                "flushing": (19000, 12800, 19800, 13600), "wakefield": (13800, 26500, 14800, 27500)}
        t = usgs.TopoMap(SHEETS[0][0])
        box = (5000, 11500, 20000, 28000)
        rgb = t.render(*box, MPP)
        sh, black = black_share(rgb, WIN / MPP)
        print("black share percentiles 25/50/75/90/97", np.percentile(sh, [25, 50, 75, 90, 97]).round(2))
        for k, (x0, y0, x1, y1) in wins.items():
            i0, i1, j0, j1 = int((box[3] - y1) / MPP), int((box[3] - y0) / MPP), int((x0 - box[0]) / MPP), int((x1 - box[0]) / MPP)
            w = sh[i0:i1, j0:j1]
            print(f"{k:14s} mean black share {w.mean():.2f}; area over 0.10/0.15/0.22/0.30/0.40: " + " ".join(f"{(w > q).mean():.2f}" for q in (0.10, 0.15, 0.22, 0.30, 0.40)))
        return
    boro = boroughs()
    allb = shapely.union_all(list(boro.values()))
    out = {}
    for fn, year, q, title, *rest in SHEETS:
        env = quad_local(q).intersection(allb.buffer(150))
        cache = INTERIM / f"usgs_sheet_{Path(fn).stem[:22]}.json"
        only = a[a.index("--only") + 1] if "--only" in a else None
        if only and only not in fn and cache.exists():       # re-read one sheet, take the others from their last reading
            g = sg.shape(json.loads(cache.read_text()))
            print(f"{title}: cached reading, built {g.area / 1e4:.0f} ha", flush=True)
            for b, poly in boro.items():
                part = g.intersection(poly.buffer(150))
                if not part.is_empty and part.area > 1e4:
                    out.setdefault((b, year), []).append(part)
            continue
        g, rgb, box, sh = sheet_mask(fn, env, open_m=rest[0] if rest else 7.5)
        cache.write_text(json.dumps(sg.mapping(g)))
        print(f"{title}: built {g.area / 1e4:.0f} ha; black pixels {100 * float((sh > 0).mean()):.0f} % of the area has heavy ink nearby", flush=True)
        for b, poly in boro.items():
            part = g.intersection(poly.buffer(150))
            if not part.is_empty and part.area > 1e4:
                out.setdefault((b, year), []).append(part)
        if len(a) > 1 and not a[1].startswith("--"):
            classify.preview(rgb, box, MPP * 2, [(g, (255, 0, 0))], f"{a[1]}/usgs_{Path(fn).stem[:18]}_{year}.png", grid=1000)
    for (b, year), parts in sorted(out.items()):
        g = shapely.union_all(parts).buffer(0)
        (Path(__file__).resolve().parent / "classified" / f"usgs_{b}_{year}.json").write_text(json.dumps(sg.mapping(g)))
        print(f"usgs_{b}_{year}: {g.area / 1e4:.0f} ha, parts {len(getattr(g, 'geoms', [g]))}")


if __name__ == "__main__":
    main(sys.argv[1:])
