"""Today's ground / water-surface elevation on a 30 m grid (UTM 18N) from the USGS 3DEP 1/3 arc-second DEM
(public domain; the same tiles the project's terrain stage reads) -> data/raw/natural_counties/dem30.tif.
Used only to tell tidal water (surface at sea level) from rivers above the head of tide, lakes and reservoirs."""
import os

import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT
from rasterio.warp import Resampling

from common import GRID, RAW

URL = "/vsicurl/https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/n{lat:02d}w{lon:03d}/USGS_13_n{lat:02d}w{lon:03d}.tif"
PX = 30.0


def main():
    out = f"{RAW}/dem30.tif"
    if os.path.exists(out):
        return
    w, h = int(GRID["w"] * GRID["px"] / PX), int(GRID["h"] * GRID["px"] / PX)
    tr = from_origin(GRID["x0"], GRID["y1"], PX, PX)
    dem = np.full((h, w), np.nan, "float32")
    env = dict(GDAL_HTTP_USERAGENT="NYCThroughTime-research/0.1", GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
               CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif", GDAL_HTTP_MAX_RETRY="4", GDAL_HTTP_RETRY_DELAY="2")
    with rasterio.Env(**env):
        for lat in (41, 42):
            for lon in (75, 74):
                with rasterio.open(URL.format(lat=lat, lon=lon)) as src:
                    with WarpedVRT(src, crs="EPSG:32618", transform=tr, width=w, height=h, resampling=Resampling.average) as vrt:
                        a = vrt.read(1, masked=True).astype("float32").filled(np.nan)
                a[a < -1000] = np.nan
                put = np.isnan(dem) & ~np.isnan(a)
                dem[put] = a[put]
                print("tile", lat, lon, int(put.sum()), flush=True)
    with rasterio.open(out, "w", driver="GTiff", height=h, width=w, count=1, dtype="float32", crs="EPSG:32618", transform=tr, compress="deflate", nodata=np.nan) as dst:
        dst.write(dem, 1)
    print("nan share", float(np.isnan(dem).mean()), "min/max", float(np.nanmin(dem)), float(np.nanmax(dem)))


if __name__ == "__main__":
    main()
