"""Where is the map missing its past?  Built-up ground without buildings.

The terrain turns ground to city when the first buildings around it stand, when a dated map
shows it built up, or when a yard or works is founded. Where the ground is city in a year and
nothing stands on it, something is missing: buildings that were pulled down and that no atlas
layer, record or generated fill has put back. This stage measures that on the fine grid (the
five boroughs and the Hudson waterfront) and on the region grid:

  python holes.py            -> data/interim/reports/holes.csv (one row per hole and year),
                                holes_by_place.csv (hectares per borough / town and year)

A hole: at least 3 ha of connected cells that are URBAN in that year, further than 60 m (fine
grid) from any building standing then. Railroad yards with generated cars, parks, cemeteries,
water and farmland are not holes. It is a measure, not a rule: wide streets, squares and
rail lines read as holes too (the list is for looking, largest first).
"""
from __future__ import annotations

import json

import duckdb
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from scipy import ndimage

from common import INTERIM, RAW
from covers import SUBURB, URBAN

YEARS = (1860, 1880, 1900, 1920, 1940, 1960, 1980)
R = 6378137.0


def cover_at(covers, years, y):
    k = (np.nan_to_num(np.asarray(years), nan=1e9) <= y).sum(axis=0)
    return np.take_along_axis(np.asarray(covers), k[None].astype(np.int64), 0)[0]


def run(name, min_ha, reach):
    m = json.loads((INTERIM / f"grid_{name}_meta.json").read_text())
    covers = np.load(INTERIM / f"grid_{name}_covers.npy", mmap_mode="r")
    years = np.load(INTERIM / f"grid_{name}_years.npy", mmap_mode="r")
    rows, cols, res, X0, Y0 = m["rows"], m["cols"], m["res"], m["X0"], m["Y0"]
    lon0, lon1 = np.degrees(X0 / R), np.degrees((X0 + cols * res) / R)
    lat = lambda Y: np.degrees(2 * np.arctan(np.exp(Y / R)) - np.pi / 2)
    lat1, lat0 = lat(Y0), lat(Y0 - rows * res)
    con = duckdb.connect()
    con.execute("SET memory_limit='2500MB'")
    pts = []
    for f in ("nyc_building_points", "county_points_inner", "county_points_outer"):
        p = INTERIM / f"{f}.parquet"
        if p.exists():
            pts.append(con.execute(f"select lon, lat, start_year, end_year from '{p}' where lon between {lon0} and {lon1} and lat between {lat0} and {lat1}").df())
    # the vanished and generated buildings are in the city's and the counties' built files
    for f in ("nyc_buildings", "county_buildings"):
        p = INTERIM / f"{f}.parquet"
        if p.exists():
            pts.append(con.execute(f"""select (bbox.xmin + bbox.xmax) / 2 lon, (bbox.ymin + bbox.ymax) / 2 lat, start_year, end_year
                                       from (select ST_Extent(geometry) bbox, start_year, end_year from '{p}' where end_year < 9000)
                                       where bbox.xmin between {lon0} and {lon1} and bbox.ymin between {lat0} and {lat1}""").df()
                       if False else con.execute(f"INSTALL spatial; LOAD spatial; select ST_X(ST_Centroid(geometry)) lon, ST_Y(ST_Centroid(geometry)) lat, start_year, end_year "
                                                 f"from '{p}' where end_year < 9000").df())
    b = pd.concat(pts, ignore_index=True)
    b = b[(b.lon >= lon0) & (b.lon <= lon1) & (b.lat >= lat0) & (b.lat <= lat1)]
    X = np.radians(b.lon.values) * R
    Y = R * np.log(np.tan(np.pi / 4 + np.radians(b.lat.values) / 2))
    c = np.clip(np.rint((X - X0) / res).astype(int), 0, cols - 1)
    r = np.clip(np.rint((Y0 - Y) / res).astype(int), 0, rows - 1)
    cell_ha = (res * np.cos(np.radians((lat0 + lat1) / 2))) ** 2 / 1e4
    k = int(round(reach / (res * 0.758)))
    out = []
    for y in YEARS:
        urb = np.isin(cover_at(covers, years, y), [URBAN, SUBURB])
        alive = (b.start_year.values <= y) & (b.end_year.values > y)
        has = np.zeros((rows, cols), bool)
        has[r[alive], c[alive]] = True
        near = ndimage.binary_dilation(has, iterations=max(k, 1))
        hole = ndimage.binary_opening(urb & ~near, iterations=1)
        lab, n = ndimage.label(hole)
        if not n:
            continue
        sizes = ndimage.sum(hole, lab, index=np.arange(1, n + 1)) * cell_ha
        cen = ndimage.center_of_mass(hole, lab, index=np.arange(1, n + 1))
        for s, (cr, cc) in zip(sizes, cen):
            if s >= min_ha:
                out.append({"grid": name, "year": y, "ha": round(float(s), 1), "lon": round(float(np.degrees((X0 + cc * res) / R)), 5),
                            "lat": round(float(lat(Y0 - cr * res)), 5)})
    return pd.DataFrame(out)


def main():
    h = pd.concat([run("detail", 3.0, 60.0)], ignore_index=True)
    # name the place: the borough or the municipality
    g = gpd.GeoDataFrame(h, geometry=gpd.points_from_xy(h.lon, h.lat), crs=4326)
    co = gpd.read_file(f"zip://{RAW / 'tiger' / 'tl_2024_us_county.zip'}")[["GEOID", "NAME", "geometry"]].to_crs(4326)
    g = gpd.sjoin(g, co, predicate="within", how="left").drop(columns="index_right").rename(columns={"NAME": "county"})
    tp = INTERIM / "towns" / "towns.parquet"
    if tp.exists():
        towns = gpd.read_parquet(tp)[["name", "geometry"]].rename(columns={"name": "town"})
        g = gpd.sjoin(g, towns, predicate="within", how="left").drop(columns="index_right")
    else:
        g["town"] = None
    g["place"] = g.town.fillna(g.county)
    rep = INTERIM / "reports"
    g.drop(columns="geometry").sort_values(["year", "ha"], ascending=[True, False]).to_csv(rep / "holes.csv", index=False)
    by = g.pivot_table(index="place", columns="year", values="ha", aggfunc="sum", fill_value=0).round(0)
    by["max"] = by.max(axis=1)
    by.sort_values("max", ascending=False).to_csv(rep / "holes_by_place.csv")
    print(by.sort_values("max", ascending=False).head(28).astype(int).to_string())
    print("\nlargest single holes:")
    print(g.drop(columns="geometry").sort_values("ha", ascending=False).head(24)[["year", "ha", "place", "lon", "lat"]].to_string(index=False))


if __name__ == "__main__":
    main()
