import sys, json, math, numpy as np, shapely
sys.path.insert(0,'data/research/holes_boroughs_build')
from holepoly import hole_polygon
from shapely.geometry import Polygon, mapping
from shapely.ops import unary_union
cl=json.load(open('data/interim/holes_boroughs_raw/clusters.json'))
def ids(i): return {int(y):v[1] for y,v in cl[i-1]['yrs'].items()}
feats=[]
def ha(g):
    return round(shapely.transform(g,lambda a: a*[111320*0.757,111320]).area/1e4,1)
def add(id,name,kind,s,e,after,ground,label,url,note,basis,g):
    c=g.representative_point()
    feats.append({'type':'Feature','properties':dict(id=id,name=name,kind=kind,start_year=s,end_year=e,after=after,ground=ground,label=label,source_url=url,note=note,date_basis=basis,floor=False,area_ha=ha(g),lon=round(c.x,6),lat=round(c.y,6)),'geometry':mapping(g)})
# 1 Freedomland remnant (cluster 3)
g=hole_polygon(ids(3)[1980]).buffer(0.0003)
add('freedomland_remnant','Freedomland site after the park (open ground)','other',1964,1984,'city','open',False,'https://en.wikipedia.org/wiki/Freedomland_U.S.A.',
    "After Freedomland closed (1964) Co-op City took the parking lot and the Little Old New York and Satellite City areas (first residents 1968), Bay Plaza Shopping Center was built 'during the early 1980s' on five further park areas, and a tract at the Hutchinson River Parkway stayed undeveloped until 2012 (Wikipedia). Outline = the cells of the 1980 hole (ground the map shows as city with no building within 60 m), buffered 30 m: ESTIMATED; end year 1984 ESTIMATED ('early 1980s'). Ground: marsh fill and cleared park, not city.",'text',g)
# 2 Rikers fields: 1960 hole, then 1980 holes
g60=hole_polygon(ids(1)[1960])
add('rikers_fields_1932','Rikers Island dump surface and farm fields (1932-1971)','landfill',1932,1971,'same','open',False,'https://en.wikipedia.org/wiki/Rikers_Island',
    "The 1951 aerial photograph (City of New York, NYC OTI) shows the island's centre, south and east as dump surface and ploughed or grassed fields; the jail stood on the north-west corner only. Landfill 'continued until 1943' (Wikipedia). The first jails of the east and middle opened 1971-72 (George Motchan 1971, Davoren 1972: DOC history page). Outline = the 1960 hole of holes.csv (cells more than 60 m from any building of the map, 80 ha): ESTIMATED; end year 1971 = the first of the east jails. The jail site feature (rikers_island_jails, ground 'paved') makes the whole island city ground from 1932: this feature is meant to take precedence.",'estimated',g60)
g80=unary_union([hole_polygon(ids(4)[1980]),hole_polygon(ids(5)[1980]),hole_polygon(ids(9)[1980])])
add('rikers_fields_1971','Rikers Island east and middle fields before the later jails (1971-1988)','landfill',1971,1988,'same','open',False,'https://correctionhistory.org/html/chronicl/nycdoc/html/jailst1a.html',
    "Cells of the 1980 holes (three clusters, about 56 ha) that are still more than 60 m from any building of 1980: the ground between the jails of 1971-78 (Motchan 1971, Davoren 1972, Anna M. Kross 1978) and those of 1985-91 (Otis Bantum 1985, Rose M. Singer 1988, Vierno 1991). End year 1988 (the Rose M. Singer Center) ESTIMATED; outline ESTIMATED. Part of this ground is the compound of the Anna M. Kross Center (about 40 acres: DOC), whose many buildings the built file dates 1984-85 (neighbours) while the centre was completed in 1978.",'estimated',g80)
# 3 Aqueduct barracks candidate (E/N metres from centre)
C=(-73.8293,40.6700)
pts=[(-60,225),(45,225),(78,60),(82,-120),(0,-205),(-105,-195),(-105,-60),(-92,100)]
g=Polygon([(C[0]+E/(111320*0.757),C[1]+N/111320) for E,N in pts])
add('aqueduct_barracks_site','Rows of long gabled sheds beside Aqueduct Racetrack (not identified)','other',1925,1960,'city','yard',False,'https://en.wikipedia.org/wiki/Aqueduct_Racetrack',
    "Ten long gabled sheds (about 80 x 22 m each) in parallel rows stand on the City's 1951 aerial mosaic west of the Ozone Park blocks and east of the Long Island Rail Road cutting; the 1924 mosaic shows open fields there, and nothing stands on the ground today (a 12.6 ha hole in 1980). Barracks or stables of the racetrack (Aqueduct was rebuilt 1956-59: Wikipedia): NOT IDENTIFIED. Years ESTIMATED (after 1924, gone by the 1959 reopening is a guess). Offered for the lead's site_fill (roofs read off the photograph); outline hand-drawn, +-25 m.",'estimated',g)
# 4 Gulf Oil terminal
ids8=ids(8)
g=unary_union([hole_polygon(v) for v in ids8.values()]).buffer(0.0006)
add('gulf_oil_terminal','Gulf Oil terminal, Bloomfield','terminal',1936,1998,'vacant','yard',True,'https://en.wikipedia.org/wiki/Bloomfield,_Staten_Island',
    "Terminal 'built in 1936', 82 tanks of 215 million gallons, closed in 1998 (Wikipedia). Outline = the cells of the holes of 1900-1980 (ground the map shows as city with no building within 60 m) buffered 50 m: ESTIMATED (the 1951 mosaic covers part of the terminal only); the tanks that show on it are in notable_demolished.boroughs2.csv.",'text',g)
json.dump({'type':'FeatureCollection','features':feats},open('data/manual/sites/add_boroughs2.geojson','w'))
for f in feats: print(f['properties']['id'],f['properties']['area_ha'],f['geometry']['type'])
