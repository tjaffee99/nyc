"""Today's footprints for Paterson / Newark (Overture buildings, region file) in the format atlas.py reads: bin, year_raw (0: none), lon, lat, WKB.
python -I build_foot.py"""
import duckdb
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
con = duckdb.connect(); con.execute("install spatial; load spatial; set memory_limit='1200MB'")
out = ROOT / "data/interim/atlas_nj_cities/nj_footprints.parquet"
src = ROOT / "data/raw/overture/2026-10-21.0"
q = f"""copy (select 0::bigint as bin, 0::bigint as year_raw, lon, lat, ST_AsWKB(geometry) as geometry from (
  select lon, lat, geometry from read_parquet('{src}/region_building.parquet') union all select ST_X(ST_Centroid(geometry)) as lon, ST_Y(ST_Centroid(geometry)) as lat, geometry from read_parquet('{src}/building.parquet'))
  where lon between -74.30 and -74.05 and lat between 40.66 and 41.02) to '{out}' (format parquet)"""
con.execute(q)
print(con.execute(f"select count(*), min(lat), max(lat), min(lon), max(lon) from '{out}'").fetchall())
