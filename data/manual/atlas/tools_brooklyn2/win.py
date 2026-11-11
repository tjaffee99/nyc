"""print local x,y (m) of a spot inside a layer's plate: python win.py <layer> <plate> [k]  (k-th quartile of the plate's building centroids, default 0.5 -> centre-most)"""
import json,sys,numpy as np
from pyproj import Transformer
L,P=sys.argv[1],int(sys.argv[2]); q=float(sys.argv[3]) if len(sys.argv)>3 else 0.5
g=json.load(open(f'data/manual/atlas/{L}.geojson'))['features']
c=np.array([np.mean(f['geometry']['coordinates'][0],axis=0) for f in g if f['properties']['plate']==P])
m=np.median(c,axis=0); d=np.hypot(*(c-m).T); i=np.argsort(d)[int(q*(len(d)-1)*0.4)]
x,y=Transformer.from_crs(4326,32618,always_xy=True).transform(*c[i]); print('%d,%d'%(x-580000,y-4500000))
