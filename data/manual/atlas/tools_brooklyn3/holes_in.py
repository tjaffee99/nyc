"""hectares of the Kings holes (holes.csv, grid 'detail', centroid of each hole) inside a layer's coverage:
python -I holes_in.py <layer> ..."""
import sys, json, pandas as pd
from shapely.geometry import shape, Point
from shapely import union_all
h = pd.read_csv('data/interim/reports/holes.csv'); h = h[h.place == 'Kings']
for L in sys.argv[1:]:
    cov = union_all([shape(f['geometry']).buffer(0) for f in json.load(open(f'data/manual/atlas/{L}_coverage.geojson'))['features']])
    for y in (1860, 1880):
        k = h[h.year == y]; ins = k[[cov.contains(Point(r.lon, r.lat)) for r in k.itertuples()]]
        print(L, y, 'holes in coverage: %.1f ha of %.1f (%d of %d clusters)' % (ins.ha.sum(), k.ha.sum(), len(ins), len(k)), list(zip(ins.lon.round(4), ins.lat.round(4), ins.ha)))
