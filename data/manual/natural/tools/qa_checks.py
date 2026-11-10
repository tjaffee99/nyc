"""Numeric sanity checks of natural_1609.geojson against well-known anchors (not used as geometry)."""
import os

import duckdb
import geopandas as gpd
import numpy as np
from shapely import wkb
from shapely.geometry import Point, box

ROOT = "/home/user/nyc"
P = f"{ROOT}/data/manual/natural/natural_1609.geojson"
g = gpd.read_file(P)
print("file MB", round(os.path.getsize(P) / 1e6, 1), "features", len(g), "invalid", int((~g.is_valid).sum()), "covers", g.cover.value_counts().to_dict())
gu = g.to_crs(32618)
pts = {
    "Collect, Centre St & Worth St (pond)": (-74.0020, 40.7153), "Canal St & W Broadway, Lispenard Meadows (marsh)": (-74.0045, 40.7215),
    "Ave C & E 10th, Stuyvesant meadows (marsh)": (-73.9785, 40.7255), "Battery Park City (water)": (-74.0160, 40.7120),
    "South St Seaport, Front St (water)": (-74.0035, 40.7065), "E 108th & 2nd Ave, Harlem flats (marsh)": (-73.9430, 40.7915),
    "Times Square (dry)": (-73.9855, 40.7580), "City Hall Park (dry)": (-74.0065, 40.7128),
    "Flushing Meadows Unisphere (marsh)": (-73.8451, 40.7464), "LaGuardia Airport (water/marsh)": (-73.8740, 40.7770),
    "JFK central terminal area (marsh)": (-73.7800, 40.6420), "Rikers Island east (water)": (-73.8760, 40.7900),
    "Brooklyn Navy Yard, Wallabout (water/marsh)": (-73.9710, 40.7020), "Gowanus, 3rd Ave & 3rd St (marsh)": (-73.9900, 40.6765),
    "Red Hook (marsh/water)": (-74.0100, 40.6750), "Coney Island Creek filled part (marsh/water)": (-73.9700, 40.5830),
    "Hunts Point market (marsh)": (-73.8740, 40.8060), "Co-op City (marsh)": (-73.8270, 40.8740),
    "Fresh Kills landfill (marsh)": (-74.1900, 40.5700), "Governors Island south (water)": (-74.0215, 40.6862),
    "Governors Island north, Fort Jay (dry)": (-74.0165, 40.6915), "Floyd Bennett Field (marsh)": (-73.8910, 40.5930),
    "Prospect Park (dry)": (-73.9690, 40.6600), "Greenpoint, Newtown Creek side (marsh/water)": (-73.9440, 40.7350),
    "Liberty Island (dry or water)": (-74.0445, 40.6892), "Randalls Island centre (water/marsh)": (-73.9230, 40.7940),
}
sidx = g.sindex
for k, (lon, lat) in pts.items():
    hit = g.iloc[list(sidx.query(Point(lon, lat), predicate="intersects"))]
    print(f"  {k:55s} -> {', '.join(hit.cover + ' [' + hit.source + ',' + hit.confidence + ']') or 'none (dry upland)'}")
# street anchors: signed distance of the street to the 1609 water edge (negative = street inside 1609 water)
con = duckdb.connect(); con.execute("INSTALL spatial; LOAD spatial;")
wat = gu[gu.cover == "water"].geometry.union_all()
for nm, bb in (("Pearl Street", (-74.016, 40.701, -74.000, 40.7095)), ("Greenwich Street", (-74.02, 40.704, -74.005, 40.725))):
    rows = con.execute(f"SELECT ST_AsWKB(geometry) FROM '{ROOT}/data/raw/overture/2026-10-21.0/roads_local.parquet' WHERE name='{nm}' AND ST_XMin(geometry)>{bb[0]} AND ST_XMax(geometry)<{bb[2]} AND ST_YMin(geometry)>{bb[1]} AND ST_YMax(geometry)<{bb[3]}").fetchall()
    gs = gpd.GeoSeries([wkb.loads(bytes(r[0])) for r in rows], crs=4326).to_crs(32618)
    p = gpd.GeoSeries([l.interpolate(d) for l in gs for d in np.arange(0, l.length, 15)], crs=32618)
    sd = np.where(p.within(wat), -1, 1) * p.distance(wat.boundary)
    print(f"  {nm}: n={len(p)} inside 1609 water {np.mean(sd < 0):.2f}; signed distance to the shore median {np.median(sd):.0f} m, p10 {np.percentile(sd, 10):.0f}, p90 {np.percentile(sd, 90):.0f}")
# islands: today's land (soil survey) minus 1609 water / marsh
soil = gpd.read_parquet(f"{ROOT}/data/interim/natural/ssurgo_all.parquet")
wet = gu[gu.cover.isin(["water", "tidal_marsh", "tidal_flat"])].geometry.union_all()
for nm, bb in (("Governors Island", (-74.030, 40.682, -74.0115, 40.696)), ("Rikers Island", (-73.895, 40.785, -73.868, 40.799)),
               
               ):
    b = gpd.GeoSeries([box(*bb)], crs=4326).to_crs(32618).iloc[0]
    s = soil[(soil.MUSYM != "W") & soil.intersects(b)].geometry.union_all().intersection(b)
    print(f"  {nm}: land today {s.area / 4046.86:.0f} acres, of it dry in 1609 {s.difference(wet).area / 4046.86:.0f} acres")
col = gu[(gu.cover == "pond") & gu.intersects(gpd.GeoSeries([box(-74.006, 40.711, -73.997, 40.720)], crs=4326).to_crs(32618).iloc[0])]
print("  ponds around the Collect:", [round(a / 4046.86, 1) for a in col.area], "acres")
st = gpd.read_file(f"{ROOT}/data/manual/natural/streams_1609.geojson")
print("streams file MB", round(os.path.getsize(f"{ROOT}/data/manual/natural/streams_1609.geojson") / 1e6, 1), len(st), st.source.value_counts().to_dict())
