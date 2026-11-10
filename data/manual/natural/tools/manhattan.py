"""Manhattan island c.1609 from the georeferenced Viele 1865 map (viele_class.tif) with the SSURGO soil survey as
a veto: water (= made land and everything outside Viele's original shore that is land today), tidal marsh,
freshwater wetland, ponds and the stream lines.  Output: data/interim/natural/manhattan_{polys,streams}.parquet
"""
import geopandas as gpd
import numpy as np
import rasterio
from rasterio import features
from scipy import ndimage
from shapely.geometry import box

import rastools as rt

ROOT = "/home/user/nyc"
D = f"{ROOT}/data/interim/natural"
# SSURGO units that record original dry ground (natural soils, or urban land over till / outwash / rock)
UPLAND_RE = r"^(Ut|Uo|UF|UG|GU|Gb|GC|CG|Cp|CH|CC|RH|Ch|Cw|FG|No|NU|Mo|Bt|Sc|ST|Wd|Su|Px|PP)"
# not natural: the two Central Park reservoirs drawn by Viele (lon0, lat0, lon1, lat1)
RESERVOIRS = [(-73.9700, 40.7775, -73.9545, 40.7915)]


def main():
    with rasterio.open(f"{D}/viele_class.tif") as s:
        cls = s.read(1); tr = s.transform; crs = s.crs; H, W = s.height, s.width
    px = tr.a
    soil = gpd.read_parquet(f"{D}/ssurgo_all.parquet")
    soil = soil[soil.AREASYMBOL == "NY061"]
    ras = lambda g: features.rasterize(((x, 1) for x in g), out_shape=(H, W), transform=tr, fill=0, dtype="uint8").astype(bool)
    today = ras(soil[soil.MUSYM != "W"].geometry)
    upl = soil[soil.MUSYM.str.match(UPLAND_RE)]
    upland_core = ras(upl.geometry.buffer(0).union_all().buffer(-25).geoms if hasattr(upl.geometry.union_all().buffer(-25), "geoms") else [upl.geometry.union_all().buffer(-25)])
    resv = ras(gpd.GeoSeries([box(*b) for b in RESERVOIRS], crs=4326).to_crs(32618))

    up, gr, bl = cls == 1, cls == 3, cls == 4
    land = ndimage.binary_closing(up | gr, structure=np.ones((3, 3), bool), iterations=2)
    land = ndimage.binary_fill_holes(land)
    land = ndimage.binary_opening(land, structure=rt.disk(2))
    lab, n = ndimage.label(land)
    sizes = ndimage.sum(land, lab, index=np.arange(1, n + 1))
    L = lab == (1 + int(np.argmax(sizes)))                      # Manhattan island as Viele drew its original shore
    L |= upland_core & ndimage.binary_dilation(L, iterations=40)  # soil survey veto next to it
    L = ndimage.binary_fill_holes(L)
    # today's land of New York County that belongs to the island (not Roosevelt / Wards / Randalls / Governors)
    tl, tn = ndimage.label(today)
    keep = np.unique(tl[L & today]); keep = keep[keep > 0]
    island = np.isin(tl, keep) & (cls > 0)
    island &= ndimage.binary_dilation(L, structure=rt.disk(5), iterations=40)  # within 600 m of the original island
    water = island & ~L
    water = ndimage.binary_opening(water, structure=np.ones((3, 3), bool))

    # Viele washes every watercourse with a green band about 50 m wide; marsh proper is wider than 84 m
    g0 = gr & L & ~resv
    core = ndimage.distance_transform_edt(g0) * px > 42.0
    marsh = (ndimage.distance_transform_edt(~core) * px <= 46.0) & g0
    marsh = ndimage.binary_closing(marsh, structure=rt.disk(2)) & L
    marsh = ndimage.binary_fill_holes(marsh) & ~bl
    ml, mn = ndimage.label(marsh)
    big = ndimage.sum(marsh, ml, index=np.arange(1, mn + 1)) * px * px >= 12000   # blobs under 1.2 ha are band junctions
    marsh = np.isin(ml, 1 + np.nonzero(big)[0])
    ml, mn = ndimage.label(marsh)
    near_tide = ndimage.binary_dilation(~L & (cls > 0), structure=rt.disk(5), iterations=8)  # 120 m
    tidal_ids = np.unique(ml[near_tide & marsh]); tidal_ids = tidal_ids[tidal_ids > 0]
    tidal = np.isin(ml, tidal_ids)
    # ... or the soil survey maps "Urban land, tidal marsh substratum" under a fifth or more of it
    uma = ras(soil[soil.MUSYM.isin(["UmA", "UmB"])].geometry)
    if mn:
        frac = ndimage.mean(uma.astype("float32"), ml, index=np.arange(1, mn + 1))
        tidal |= np.isin(ml, 1 + np.nonzero(frac >= 0.2)[0])
    fresh = marsh & ~tidal

    pond = ndimage.binary_opening(bl & L & ~resv, structure=np.ones((3, 3), bool))
    pl, pn = ndimage.label(pond)
    edge = np.unique(pl[ndimage.binary_dilation(~L, iterations=3) & pond])
    pond &= ~np.isin(pl, edge[edge > 0])

    rows = []
    for cover, m, amin, conf, note in (
        ("water", water, 300, "medium", "made land / outside the original shore on Viele 1865 (salmon tint or river), land today"),
        ("tidal_marsh", tidal, 2000, "medium", "marsh on Viele 1865 within 120 m of the original shore or on tidal marsh substratum of the soil survey"),
        ("freshwater_wetland", fresh, 2000, "medium", "marsh on Viele 1865, inland"),
        ("pond", pond, 800, "medium", "pond on Viele 1865"),
    ):
        for g in rt.polygons(m, tr, amin, 4.0):
            rows.append(dict(cover=cover, source="viele1865", confidence=conf, note=note, geometry=g))
    out = gpd.GeoDataFrame(rows, crs=32618)
    out.to_parquet(f"{D}/manhattan_polys.parquet")
    print(out.assign(ha=out.area / 1e4).groupby("cover").ha.agg(["count", "sum"]).round(1))

    bands = gr & L & ~marsh & ~resv
    bands = ndimage.binary_opening(bands, structure=rt.disk(2))
    bands = ndimage.binary_closing(bands, structure=np.ones((3, 3), bool))
    sk = rt.thin(bands)
    lines = rt.trace(sk, tr, 150.0)
    st = gpd.GeoDataFrame(dict(source="viele1865", geometry=[l.simplify(4.0) for l in lines]), crs=32618)
    st.to_parquet(f"{D}/manhattan_streams.parquet")
    print("streams", len(st), "km", round(st.length.sum() / 1000, 1), "longest m", round(st.length.max()))
    # coverage mask of the Viele method, for the citywide assembly
    cov = island | L
    covp = rt.polygons(ndimage.binary_closing(cov, structure=rt.disk(3)), tr, 10000, 6.0)
    gpd.GeoDataFrame(dict(geometry=covp), crs=32618).to_parquet(f"{D}/manhattan_coverage.parquet")
    np.save(f"{D}/man_debug.npy", (L.astype("uint8") + 2 * island.astype("uint8") + 4 * upland_core.astype("uint8"))[::4, ::4])
    print("acres made land (water 1609, land today):", round(out[out.cover == "water"].area.sum() / 4046.86), "island ha", round(island.sum() * px * px / 1e4))


if __name__ == "__main__":
    main()
