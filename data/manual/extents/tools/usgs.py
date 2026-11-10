"""USGS historical topographic quadrangles (GeoTIFF, public domain) as a map object with the same
render() as warp.MapWarp: the sheet resampled into local metres through its own georeference
(NAD27 polyconic -> UTM 18N by PROJ), plus a constant shift found against today's streets."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject
from affine import Affine
from rasterio.enums import Resampling
sys.path.insert(0, str(Path(__file__).resolve().parent))
import streets as S

RAW = Path(__file__).resolve().parents[4] / "data" / "raw" / "extents" / "usgs"


class TopoMap:
    def __init__(self, filename, shift=(0.0, 0.0), name=None):
        self.path = RAW / filename
        self.shift = shift          # metres added to the sheet's own coordinates (east, north)
        self.rec = {"name": name or filename, "mask": None}
        with rasterio.open(self.path) as src:
            self.crs, self.res = src.crs, src.res

    def render(self, x0, y0, x1, y1, mpp):
        W, H = int(round((x1 - x0) / mpp)), int(round((y1 - y0) / mpp))
        e0, n0 = x0 + S.X0 - self.shift[0], y0 + S.Y0 - self.shift[1]
        e1, n1 = x1 + S.X0 - self.shift[0], y1 + S.Y0 - self.shift[1]
        dst_tr = Affine(mpp, 0, e0, 0, -mpp, n1)
        with rasterio.open(self.path) as src:
            n = min(src.count, 3)
            arr = np.full((n, H, W), 255, np.uint8)
            for b in range(n):
                reproject(rasterio.band(src, b + 1), arr[b], dst_transform=dst_tr, dst_crs="EPSG:32618",
                          resampling=Resampling.bilinear, dst_nodata=None, init_dest_nodata=False)
        if arr.shape[0] == 1:
            arr = np.repeat(arr, 3, axis=0)
        return np.moveaxis(arr[:3], 0, -1).astype(np.uint8)


if __name__ == "__main__":
    import warp
    from PIL import Image
    fn, box, mpp, out = sys.argv[1], [float(v) for v in sys.argv[2].split(",")], float(sys.argv[3]), sys.argv[4]
    t = TopoMap(fn)
    print(t.crs.to_string()[:80], t.res)
    arr = t.render(*box, mpp)
    warp.annotate(arr, *box, mpp, streets="--streets" in sys.argv, grid=int(sys.argv[sys.argv.index("--grid") + 1]) if "--grid" in sys.argv else 0).save(out)
    print(out, arr.shape)
