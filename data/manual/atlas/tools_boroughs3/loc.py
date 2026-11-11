"""local x,y of a plate's mask centroid:  python -I loc.py <plate>"""
import json,sys
from pyproj import Transformer
import shapely.geometry as sg
t=Transformer.from_crs(4326,32618,always_xy=True)
for l in open('data/raw/extents/spacetime/mapwarper.objects.ndjson'):
    if l.startswith('{"id":%s,'%sys.argv[1]):
        c=sg.shape(json.loads(l)['geometry']).centroid; x,y=t.transform(c.x,c.y); print('%d,%d'%(x-580000,y-4500000))
