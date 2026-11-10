"""Shared constants of the eight counties' natural layer: the 6 m grid (aligned with the city layer's grid, so
that a cell belongs either to the city file or to this one), paths, soil classes."""
ROOT = "/home/user/nyc"
RAW = f"{ROOT}/data/raw/natural_counties"
D = f"{ROOT}/data/interim/natural_counties"
OUT = f"{ROOT}/data/manual/natural/counties"

# UTM 18N, 6 m cells; the city grid is x0=562000, y1=4533000, px=6 (offsets here are multiples of 6 m)
GRID = dict(x0=538000.0, y1=4584000.0, px=6.0, w=16400, h=16500)

AREAS = {"NJ017": "Hudson", "NJ003": "Bergen", "NJ013": "Essex", "NJ039": "Union", "NJ031": "Passaic",
         "NY059": "Nassau", "NY119": "Westchester", "NY087": "Rockland"}
CITY_AREAS = ["NY005", "NY047", "NY061", "NY081", "NY085"]

# soil class codes (per map unit)
WATER, UPLAND, WETSUB, MARSHSUB, TMARSH, TFLAT, BEACH, DUNES, FRESH, AMBIG = 1, 2, 3, 4, 5, 6, 7, 8, 9, 10

# stem: (quad lon0, lat0, lon1, lat1, source id, print year)
SHEETS = {
    "NJ_Staten_Island_255388_1898": (-74.25, 40.5, -74.0, 40.75, "usgs_staten_island_1898"),
    "NY_Brooklyn_123118_1897": (-74.0, 40.5, -73.75, 40.75, "usgs_brooklyn_1897"),
    "NJ_Harlem_472515_1891": (-74.0, 40.75, -73.75, 41.0, "usgs_harlem_1891"),
    "NY_Hempstead_129886_1897": (-73.75, 40.5, -73.5, 40.75, "usgs_hempstead_1897"),
    "NJ_Paterson_255310_1888": (-74.25, 40.75, -74.0, 41.0, "usgs_paterson_1888"),
    "NY_Oyster_Bay_136363_1897": (-73.75, 40.75, -73.5, 41.0, "usgs_oyster_bay_1897"),
    "NY_Babylon_123382_1901": (-73.5, 40.5, -73.25, 40.75, "usgs_babylon_1901"),
    "NY_Northport_128788_1901": (-73.5, 40.75, -73.25, 41.0, "usgs_northport_1901"),
    "NY_Tarrytown_144340_1892": (-74.0, 41.0, -73.75, 41.25, "usgs_tarrytown_1892"),
    "NY_Stamford_144254_1892": (-73.75, 41.0, -73.5, 41.25, "usgs_stamford_1892"),
    "NY_West_Point_144447_1892": (-74.0, 41.25, -73.75, 41.5, "usgs_west_point_1892"),
    "NY_Carmel_140433_1892": (-73.75, 41.25, -73.5, 41.5, "usgs_carmel_1892"),
    "NJ_Ramapo_148251_1891": (-74.25, 41.0, -74.0, 41.25, "usgs_ramapo_1891"),
    "NY_Greenwood_Lake_255191_1891": (-74.5, 41.0, -74.25, 41.25, "usgs_greenwood_lake_1891"),
    "NJ_Morristown_255268_1888": (-74.5, 40.75, -74.25, 41.0, "usgs_morristown_1888"),
    "NJ_Plainfield_255320_1888": (-74.5, 40.5, -74.25, 40.75, "usgs_plainfield_1888"),
}
