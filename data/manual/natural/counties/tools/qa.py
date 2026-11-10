"""Checks on the delivered file: point tests, overlap with the city layer, overlap between polygons of different
cover, cells claimed twice.  usage: python qa.py"""
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from common import OUT, ROOT

POINTS = [  # name, lon, lat, expectation
    ("Port Newark (container terminal)", -74.150, 40.688, "wet"), ("Newark Airport (terminals)", -74.175, 40.690, "wet"),
    ("Port Elizabeth", -74.150, 40.670, "wet"), ("Liberty State Park", -74.055, 40.704, "wet"),
    ("Liberty Science Center (Communipaw)", -74.0545, 40.7085, "wet"), ("Black Tom (Liberty State Park south)", -74.0555, 40.6935, "wet"),
    ("Harsimus Cove (Newport)", -74.037, 40.727, "wet"), ("Hoboken west side (4th & Jackson)", -74.043, 40.743, "wet"),
    ("Bayonne ocean terminal (MOTBY)", -74.075, 40.662, "wet"), ("Kearny Point", -74.105, 40.725, "wet"),
    ("Meadowlands sports complex (stadium)", -74.0745, 40.8135, "wet"), ("Teterboro Airport", -74.061, 40.850, "wet"),
    ("Secaucus outlets (Meadowlands)", -74.070, 40.790, "wet"), ("Playland, Rye", -73.6735, 40.9665, "wet"),
    ("Piermont pier (middle)", -73.906, 41.0425, "wet"), ("Piermont marsh", -73.913, 41.030, "wet"),
    ("Croton Point landfill", -73.893, 41.186, "wet"), ("Croton-Harmon yard", -73.8826, 41.1898, "wet"),
    ("Sleepy Hollow, General Motors site", -73.870, 41.083, "wet"), ("Tarrytown waterfront", -73.868, 41.075, "wet"),
    ("Mamaroneck, Harbor Island Park", -73.732, 40.944, "wet"),
    ("Journal Square", -74.063, 40.7325, "dry"), ("Paulus Hook (Grand & Washington)", -74.0345, 40.715, "dry"),
    ("Hoboken, Castle Point", -74.0245, 40.745, "dry"), ("Snake Hill (Laurel Hill), Secaucus", -74.088, 40.760, "dry"),
    ("Newark, Broad & Market", -74.1724, 40.7357, "dry"), ("Elizabeth, Broad St", -74.2150, 40.6640, "dry"),
    ("Hackensack, Main St", -74.043, 40.886, "dry"), ("Fort Lee", -73.970, 40.850, "dry"),
    ("Paterson, Great Falls overlook", -74.1795, 40.9155, "dry"), ("White Plains, Main St", -73.7655, 41.033, "dry"),
    ("Yonkers, Getty Square", -73.8987, 40.9335, "dry"), ("Nyack, Main & Broadway", -73.918, 41.0905, "dry"),
    ("Haverstraw, Main St", -73.9645, 41.1965, "dry"), ("Tarrytown, Broadway & Main", -73.8585, 41.076, "dry"),
    ("Kensico Reservoir", -73.7656, 41.0844, "dry_valley"), ("Wanaque Reservoir", -74.3024, 41.0494, "dry_valley"),
    ("Oradell Reservoir", -74.0185, 40.9627, "dry_valley"), ("New Croton Reservoir", -73.840, 41.233, "dry_valley"),
    ("Lake DeForest", -73.9584, 41.156, "dry_valley"),
]
WET = {"water", "tidal_marsh", "tidal_flat", "pond", "freshwater_wetland"}


def main():
    g = gpd.read_file(f"{OUT}/natural_1609_counties.geojson")
    counties = set(g.county)
    pts = gpd.GeoDataFrame(pd.DataFrame(POINTS, columns=["name", "lon", "lat", "expect"]), geometry=[Point(p[1], p[2]) for p in POINTS], crs=4326)
    j = gpd.sjoin(pts, g[["cover", "source", "confidence", "county", "geometry"]], how="left", predicate="within")
    bad = 0
    for _, r in j.iterrows():
        got = r.cover if isinstance(r.cover, str) else "dry (no polygon)"
        ok = (r.expect == "wet" and got in WET) or (r.expect == "dry" and got.startswith("dry (")) or (r.expect == "dry_valley" and got == "dry_valley")
        bad += not ok
        print(f"{'ok ' if ok else 'NO '} {r['name'][:42]:42s} expect {r.expect:10s} got {got:18s} {r.source if isinstance(r.source, str) else '':26s} {r.confidence if isinstance(r.confidence, str) else ''}")
    print("points not as expected:", bad, "of", len(j), "(counties in the file:", sorted(counties), ")")
    u = g.to_crs(32618)
    city = gpd.read_file(f"{ROOT}/data/manual/natural/natural_1609.geojson").to_crs(32618)
    ov = gpd.overlay(u[["cover", "geometry"]], city[["cover", "geometry"]], how="intersection", keep_geom_type=True)
    print("overlap with the city layer's polygons: m2", round(ov.area.sum()), "pieces", len(ov), "largest m2", round(ov.area.max()) if len(ov) else 0)
    a = u.reset_index()[["index", "cover", "geometry"]]
    pairs = gpd.sjoin(a, a, predicate="overlaps")
    pairs = pairs[pairs.index_left < pairs.index_right]
    if len(pairs):
        ar = [a.geometry.iloc[i].intersection(a.geometry.iloc[k]).area for i, k in zip(pairs.index_left, pairs.index_right)]
        print("polygon pairs that overlap:", len(pairs), "total m2", round(sum(ar)), "largest m2", round(max(ar)))
    else:
        print("no overlapping polygon pairs")
    print("invalid geometries:", int((~g.is_valid).sum()), "; polygons", len(g), "; hectares by cover:", (u.area.groupby(u.cover).sum() / 1e4).round(0).to_dict())


if __name__ == "__main__":
    main()
