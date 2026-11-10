"""List named Overture features of a window (to pick outlines by name; never a source of dates).
  python explore.py w s e n [min_ha] [tables]     tables: land_use,water,land,infra,local (comma list)"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from zonelib import *
from shapely import wkb
w, s, e, n = map(float, sys.argv[1:5]); min_ha = float(sys.argv[5]) if len(sys.argv) > 5 else 2.0
tabs = (sys.argv[6] if len(sys.argv) > 6 else 'land_use,water,land,infra').split(',')
F = {'land_use': 'region5_land_use', 'water': 'base_water', 'land': 'base_land', 'infra': 'infrastructure', 'local': 'localities'}
c = con()
for t in tabs:
    rows = c.execute(f"""select name, subtype, class, ST_Area(ST_Transform(geometry, 'EPSG:4326', 'EPSG:32618', true)) / 1e4 ha,
        ST_X(ST_Centroid(geometry)), ST_Y(ST_Centroid(geometry)) from '{OV}/{F[t]}.parquet'
        where name is not null and ST_GeometryType(geometry) in ('POLYGON', 'MULTIPOLYGON')
        and ST_XMax(geometry) >= {w} and ST_XMin(geometry) <= {e} and ST_YMax(geometry) >= {s} and ST_YMin(geometry) <= {n}
        order by ha desc""").fetchall()
    rows = [r for r in rows if r[3] >= min_ha]
    print(f'## {t}: {len(rows)} named polygons >= {min_ha} ha')
    for nm, st, cl, ha, x, y in rows[:int(os.environ.get("CAP", 70))]:
        print(f'  {ha:9.1f} ha  {st}/{cl:14s} {x:.4f} {y:.4f}  {nm}')
