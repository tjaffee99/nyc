"""Today's water bodies of the eight counties from the soil survey's Water unit and the 3DEP water-surface
elevation, on a 12 m grid:
  sea.tif         tidal water = Water cells at <= 1.5 m, in connected bodies of >= 100 ha (uint8, 12 m)
  inland_water.csv  every other body of >= 4 ha: id, hectares, median surface elevation, a point inside, county
The table is what data/manual/natural/counties/reservoirs.csv was named from."""
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from rasterio import features
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject
from scipy import ndimage

from common import AREAS, D, GRID, RAW, WATER

PX = 12.0


def main():
    w, h = int(GRID["w"] * GRID["px"] / PX), int(GRID["h"] * GRID["px"] / PX)
    tr = from_origin(GRID["x0"], GRID["y1"], PX, PX)
    soil = gpd.read_parquet(f"{D}/ssurgo_counties.parquet", columns=["AREASYMBOL", "code", "geometry"])
    wat = soil[soil.code == WATER]
    water = features.rasterize(((g, 1) for g in wat.geometry), out_shape=(h, w), transform=tr, fill=0, dtype="uint8").astype(bool)
    area_id = {a: i + 1 for i, a in enumerate(AREAS)}
    own = soil[soil.AREASYMBOL.isin(AREAS)]
    cty = features.rasterize(((g, area_id[a]) for g, a in zip(own.geometry, own.AREASYMBOL)), out_shape=(h, w), transform=tr, fill=0, dtype="uint8")
    dem = np.full((h, w), np.nan, "float32")
    with rasterio.open(f"{RAW}/dem30.tif") as s:
        reproject(s.read(1), dem, src_transform=s.transform, src_crs=s.crs, dst_transform=tr, dst_crs="EPSG:32618", resampling=Resampling.nearest, src_nodata=np.nan, dst_nodata=np.nan)
    low = water & (np.isnan(dem) | (dem <= 1.5))
    lab, n = ndimage.label(low)
    big = np.isin(lab, 1 + np.nonzero(ndimage.sum(low, lab, index=np.arange(1, n + 1)) * PX * PX >= 100e4)[0])
    with rasterio.open(f"{D}/sea.tif", "w", driver="GTiff", height=h, width=w, count=1, dtype="uint8", crs="EPSG:32618", transform=tr, compress="deflate") as dst:
        dst.write(big.astype("uint8"), 1)
    print("tidal water ha", round(big.sum() * PX * PX / 1e4), "low water not in a big body ha", round((low & ~big).sum() * PX * PX / 1e4))
    inl = water & ~big
    lab, n = ndimage.label(inl)
    idx = np.arange(1, n + 1)
    ha = ndimage.sum(inl, lab, index=idx) * PX * PX / 1e4
    keep = idx[ha >= 4]
    el = ndimage.median(np.nan_to_num(dem, nan=0.0), lab, index=keep)
    pos = ndimage.maximum_position(ndimage.distance_transform_edt(inl), lab, index=keep)     # the point farthest from the shore
    tf = Transformer.from_crs(32618, 4326, always_xy=True)
    names = [""] + list(AREAS.values())
    rows = []
    for k, e, (r, c) in zip(keep, el, pos):
        lon, lat = tf.transform(GRID["x0"] + (c + 0.5) * PX, GRID["y1"] - (r + 0.5) * PX)
        rows.append(dict(id=int(k), ha=round(float(ha[k - 1]), 1), elev_m=round(float(e), 1), lon=round(lon, 5), lat=round(lat, 5), county=names[cty[r, c]]))
    t = pd.DataFrame(rows).sort_values("ha", ascending=False)
    t.to_csv(f"{D}/inland_water.csv", index=False)
    print(len(t), "inland bodies >= 4 ha;", round(t.ha.sum()), "ha")
    print(t.head(90).to_string(index=False))


if __name__ == "__main__":
    main()
