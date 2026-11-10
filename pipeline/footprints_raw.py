"""Stage: the city's building footprints (data/raw/nyc/building_footprints.csv, WKT) as
GeoParquet with plain column names, metric heights and a centroid, so later stages and
tools can read windows of it without parsing 500 MB of CSV.

Output: data/interim/nyc_footprints_raw.parquet (EPSG:4326; one row per footprint)
"""
from __future__ import annotations

import duckdb

from common import INTERIM, RAW, log

OUT = INTERIM / "nyc_footprints_raw.parquet"
FT = 0.3048


def main():
    if OUT.exists():
        log("footprints_raw: cached")
        return OUT
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial; SET memory_limit='6GB'; SET threads=4;")
    src = RAW / "nyc" / "building_footprints.csv"
    con.execute(f"""
    COPY (
      SELECT DOITT_ID AS doitt_id, BIN AS bin, CAST(BASE_BBL AS VARCHAR) AS base_bbl,
             CAST("Map Pluto BBL" AS VARCHAR) AS pluto_bbl, NAME AS name,
             "Construction Year" AS year_raw, "Feature Code" AS feature_code,
             "Geometry Source" AS geom_source, LAST_STATUS_TYPE AS status,
             round("Height Roof" * {FT}, 2) AS height_m, round("Ground Elevation" * {FT}, 2) AS ground_m,
             ST_X(ST_Centroid(g)) AS lon, ST_Y(ST_Centroid(g)) AS lat,
             ST_AsWKB(g) AS geometry
      FROM (SELECT *, ST_GeomFromText(the_geom) AS g
            FROM read_csv('{src}', header=true, sample_size=200000, types={{'BASE_BBL': 'VARCHAR', 'Map Pluto BBL': 'VARCHAR'}}))
      ORDER BY floor(lat * 200), lon
    ) TO '{OUT}' (FORMAT parquet, ROW_GROUP_SIZE 20000);""")
    n = con.execute(f"SELECT count(*) FROM '{OUT}'").fetchone()[0]
    log(f"footprints_raw: {n} footprints -> {OUT}")
    return OUT


if __name__ == "__main__":
    main()
