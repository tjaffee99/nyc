"""What the inputs say at a point: soil map unit and class, sheet class, delivered cover.  usage: python probe.py lon,lat[,label] ..."""
import sys
import geopandas as gpd, rasterio
from pyproj import Transformer
from shapely.geometry import Point
from common import D, OUT, SHEETS

soil = gpd.read_parquet(f"{D}/ssurgo_counties.parquet")
out = gpd.read_file(f"{OUT}/natural_1609_counties.geojson")
names = {1: "water", 2: "upland", 3: "wetsub", 4: "marshsub", 5: "tmarsh", 6: "tflat", 7: "beach", 8: "dunes", 9: "fresh", 10: "ambig"}
cls = {0: "blank", 1: "water", 2: "marsh", 3: "thin line", 255: "off sheet"}
tf = Transformer.from_crs(4326, 32618, always_xy=True)
for a in sys.argv[1:]:
    p = a.split(","); lon, lat = float(p[0]), float(p[1])
    x, y = tf.transform(lon, lat)
    s = soil[soil.contains(Point(x, y))]
    so = "; ".join(f"{r.AREASYMBOL} {r.MUSYM} {r.muname[:48]} [{names[r.code]}]" for r in s.itertuples()) or "no soil polygon"
    sh = []
    for stem, v in SHEETS.items():
        if v[0] <= lon < v[2] and v[1] <= lat < v[3]:
            try:
                with rasterio.open(f"{D}/sheet_{v[4]}.tif") as r:
                    xs, ys = Transformer.from_crs(4326, r.crs.to_wkt(), always_xy=True).transform(lon, lat)
                    sh.append(v[4][5:] + "=" + cls[int(next(r.sample([(xs, ys)]))[0])])
            except Exception:
                sh.append(v[4][5:] + "=not classified")
    o = out[out.contains(Point(lon, lat))]
    print(f"{(p[2] if len(p) > 2 else ''):28s} {lon:.4f},{lat:.4f} | {so} | sheet {' '.join(sh)} | out: {', '.join(o.cover + ' (' + o.source + ')') or 'none'}")
