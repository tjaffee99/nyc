"""QA plot: polygons of a GeoDataFrame coloured by a column, over Overture roads, for a lon/lat box.
usage: python viewmap.py <parquet|geojson> <column> <lon0> <lat0> <lon1> <lat1> <out.png> [px_per_m] [label]
"""
import sys

import duckdb
import geopandas as gpd
import numpy as np
from PIL import Image, ImageDraw
from shapely import wkb
from shapely.geometry import box

OV = "/home/user/nyc/data/raw/overture/2026-10-21.0"
PAL = {
    "water": (120, 170, 230), "tidal_marsh": (120, 200, 150), "tidal_flat": (200, 200, 160), "beach": (240, 220, 150),
    "dunes": (230, 200, 120), "pond": (60, 110, 220), "freshwater_wetland": (90, 170, 90), "forest": (200, 230, 200),
    "UrA": (120, 170, 230), "UmA": (120, 200, 150), "UmB": (120, 200, 150), "UsA": (240, 220, 150), "W": (225, 235, 250),
    "ULA": (235, 170, 170), "ULAl": (235, 170, 170), "LUA": (230, 140, 140), "LUB": (230, 140, 140), "ELUA": (220, 120, 180),
    "LEA": (220, 120, 180), "UoA": (250, 245, 225), "UtA": (245, 245, 245), "UtB": (245, 245, 245),
}


def main():
    path, col = sys.argv[1], sys.argv[2]
    lon0, lat0, lon1, lat1 = map(float, sys.argv[3:7])
    out = sys.argv[7]
    ppm = float(sys.argv[8]) if len(sys.argv) > 8 else 0.25
    label = len(sys.argv) > 9
    g = gpd.read_parquet(path) if path.endswith(".parquet") else gpd.read_file(path)
    bb = gpd.GeoSeries([box(lon0, lat0, lon1, lat1)], crs=4326).to_crs(32618).iloc[0]
    x0, y0, x1, y1 = bb.bounds
    g = g.to_crs(32618)
    g = g[g.intersects(bb)]
    g = g.iloc[np.argsort(-g.area.values)]
    W, H = int((x1 - x0) * ppm), int((y1 - y0) * ppm)
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    tx = lambda c: [((x - x0) * ppm, (y1 - y) * ppm) for x, y in c]
    for _, r in g.iterrows():
        col_v = PAL.get(r[col], (250, 235, 215))
        geoms = r.geometry.geoms if hasattr(r.geometry, "geoms") else [r.geometry]
        for p in geoms:
            if p.geom_type != "Polygon":
                continue
            d.polygon(tx(p.exterior.coords), fill=col_v, outline=(150, 150, 150))
            for h in p.interiors:
                d.polygon(tx(h.coords), fill=(255, 255, 255), outline=(150, 150, 150))
    # today's shoreline (soil survey Water unit) in dark blue
    soil = gpd.read_parquet("/home/user/nyc/data/interim/natural/ssurgo_all.parquet")
    soil = soil[(soil.MUSYM == "W") & soil.intersects(bb)]
    for geom in soil.geometry:
        for p in getattr(geom, "geoms", [geom]):
            d.line(tx(p.exterior.coords), fill=(0, 0, 160), width=2)
            for h in p.interiors:
                d.line(tx(h.coords), fill=(0, 0, 160), width=2)
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    for f, c, w in ((("roads_local", (150, 150, 150), 1),) if ppm >= 0.1 else ()) + (("roads_region", (120, 120, 120), 1),):
        rows = con.execute(
            f"SELECT ST_AsWKB(geometry), name FROM '{OV}/{f}.parquet' WHERE ST_XMax(geometry)>{lon0} AND ST_XMin(geometry)<{lon1} AND ST_YMax(geometry)>{lat0} AND ST_YMin(geometry)<{lat1}"
        ).fetchall()
        gs = gpd.GeoSeries([wkb.loads(bytes(r[0])) for r in rows], crs=4326).to_crs(32618)
        for l in gs:
            for part in getattr(l, "geoms", [l]):
                d.line(tx(part.coords), fill=c, width=w)
    if "natural_1609" in path:
        st = gpd.read_file(path.replace("natural_1609", "streams_1609")).to_crs(32618)
        st = st[st.intersects(bb)]
        for l in st.geometry:
            for part in getattr(l, "geoms", [l]):
                d.line(tx(part.coords), fill=(220, 0, 0), width=1)
    if label:
        for _, r in g.iterrows():
            p = r.geometry.representative_point()
            if bb.contains(p) and r.geometry.area > 4000:
                d.text(((p.x - x0) * ppm, (y1 - p.y) * ppm), str(r[col]), fill=(200, 0, 0))
    im.save(out)
    print(out, im.size)


if __name__ == "__main__":
    main()
