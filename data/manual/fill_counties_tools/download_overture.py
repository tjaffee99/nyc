"""Overture extracts of the wider box (common.REGION_BBOX) for the counties' fill zones.

The lead's extracts under data/raw/overture/ cover only the city's box; this part needs today's
water, land, land use, street centre lines and railways of the eight counties.  Same release,
same anonymous S3 secret and the same columns as pipeline/download_overture.py, so the copied
tools (streets.py, zonelib.py) read them unchanged.  Cached: a file on disk is not fetched again.

  .venv/bin/python data/manual/fill_counties_tools/download_overture.py [name ...]
"""
import os, sys, time
import duckdb

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
OUT = os.path.join(ROOT, 'data', 'raw', 'fill_counties', 'overture')
RELEASE = '2026-10-21.0'
BBOX = (-74.52, 40.47, -73.40, 41.38)            # pipeline/common.REGION_BBOX
POLY = "ST_GeometryType(geometry) IN ('POLYGON', 'MULTIPOLYGON')"
EXTRACTS = {
    'base_water': ('base/type=water', 'id, subtype, class, names.primary AS name, geometry', POLY),
    'base_land': ('base/type=land', 'id, subtype, class, names.primary AS name, geometry', POLY),
    'region5_land_use': ('base/type=land_use', 'id, subtype, class, names.primary AS name, geometry', POLY),
    'infrastructure': ('base/type=infrastructure', 'id, subtype, class, names.primary AS name, geometry',
                       "(names.primary IS NOT NULL OR subtype IN ('airport', 'pier', 'barrier', 'waterway', 'quay'))"),
    'water_lines': ('base/type=water', 'id, subtype, class, names.primary AS name, geometry',
                    "ST_GeometryType(geometry) IN ('LINESTRING', 'MULTILINESTRING') AND names.primary IS NOT NULL"),
    'roads_region': ('transportation/type=segment', 'id, class, subtype, names.primary AS name, road_flags, geometry',
                     "subtype = 'road' AND class IN ('motorway', 'trunk', 'primary', 'secondary', 'tertiary')"),
    'rail': ('transportation/type=segment', 'id, class, subclass, names.primary AS name, rail_flags, geometry',
             "subtype = 'rail'"),
    'roads_local': ('transportation/type=segment', 'id, class, subclass, names.primary AS name, road_flags, geometry',
                    "subtype = 'road' AND (class IN ('residential', 'living_street', 'unclassified') "
                    "OR (class = 'service' AND subclass = 'alley'))"),
    'localities': ('divisions/type=division_area', 'id, subtype, class, names.primary AS name, region, geometry',
                   "subtype IN ('locality', 'county', 'localadmin', 'neighborhood')"),
}


def main(names):
    os.makedirs(OUT, exist_ok=True)
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial; SET memory_limit='2GB'; SET threads=4;")
    con.execute("CREATE OR REPLACE SECRET overture (TYPE s3, PROVIDER config, KEY_ID '', SECRET '', REGION 'us-west-2');")
    w, s, e, n = BBOX
    for name in names:
        out = os.path.join(OUT, f'{name}.parquet')
        if os.path.exists(out):
            print(name, 'cached', flush=True); continue
        theme, cols, cond = EXTRACTS[name]
        t = time.time(); stage = out + '.part'
        try:
            con.execute(f"""COPY (SELECT {cols}
              FROM read_parquet('s3://overturemaps-us-west-2/release/{RELEASE}/theme={theme}/*', hive_partitioning=1)
              WHERE bbox.xmin < {e} AND bbox.xmax > {w} AND bbox.ymin < {n} AND bbox.ymax > {s} AND {cond}
            ) TO '{stage}' (FORMAT parquet, ROW_GROUP_SIZE 20000);""")
        except Exception as ex:
            print(name, 'FAILED', repr(ex)[:300], flush=True); continue
        os.replace(stage, out)
        k = con.execute(f"SELECT count(*) FROM '{out}'").fetchone()[0]
        print(f'{name}: {k} rows, {os.path.getsize(out) / 1e6:.1f} MB, {time.time() - t:.0f} s', flush=True)


if __name__ == '__main__':
    main(sys.argv[1:] or list(EXTRACTS))
