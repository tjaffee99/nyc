"""builds data/tables/notable_demolished.boroughs2.csv and known_building_dates.boroughs2.csv  (run from repo root: .venv/bin/python -I data/research/holes_boroughs_build/build_rows.py)"""
import csv, math, pandas as pd, numpy as np, duckdb
COLS="id,name,start_year,end_year,lat,lon,height_m,storeys,material,outline,shape_note,source_url,footprint_m,rotation_deg".split(',')
rows=[]
def enu(lon0,lat0,E,N): return lon0+E/(111320*math.cos(math.radians(lat0))), lat0+N/111320
def rect_row(id,name,s,e,c,corners,h,mat,note,url):
    lon0,lat0=c
    pts=[enu(lon0,lat0,E,N) for E,N in corners]
    clon=sum(p[0] for p in pts)/len(pts); clat=sum(p[1] for p in pts)/len(pts)
    out='; '.join(f'{p[0]:.6f} {p[1]:.6f}' for p in pts)
    rows.append(dict(id=id,name=name,start_year=s,end_year=e,lat=round(clat,6),lon=round(clon,6),height_m=h,storeys='',material=mat,outline=out,shape_note=note,source_url=url,footprint_m='',rotation_deg=''))
# ---- 1. Shooters Island, Standard Shipbuilding yard, traced on the 1924 photograph (centre of the grid below)
C=(-74.1585,40.6433)
URL='https://en.wikipedia.org/wiki/Shooters_Island'
NOTE=("Roof outline traced on the City's 1924 aerial mosaic (NYC OTI, CC BY 4.0) in a 50 m grid, +-6 m; the buildings of the island's shipyard (Standard Shipbuilding bought the island in 1915, "
      "industrial use 'through 1922', abandoned vessels round it by 1930: Wikipedia). Which of them are Townsend-Downey's of 1898-1910 and which Standard's is not known: start year ESTIMATED "
      "(1916), end year ESTIMATED (gone by the 1951 photograph; none stands today); height and material ESTIMATED (shed).")
def px(x,y): return ((x-562)/1.875,(562-y)/1.875)
sheds=[
 ('hall','Shooters Island shipyard, main shed (125 x 93 m)',[(285,532),(457,538),(458,765),(283,752)],14,'steel'),
 ('west_a','Shooters Island shipyard, west shed A',[(147,572),(232,572),(232,613),(147,613)],10,'steel'),
 ('west_b','Shooters Island shipyard, west shed B (long)',[(212,622),(265,622),(265,783),(212,783)],10,'steel'),
 ('west_c','Shooters Island shipyard, west shed C',[(162,752),(193,752),(193,882),(162,882)],8,'steel'),
 ('long_n','Shooters Island shipyard, long narrow shed',[(470,535),(505,535),(505,740),(470,740)],8,'wood'),
 ('mid_a','Shooters Island shipyard, mid shed A',[(512,590),(640,590),(640,612),(512,612)],8,'wood'),
 ('mid_b','Shooters Island shipyard, mid shed B',[(515,620),(640,620),(640,642),(515,642)],8,'wood'),
 ('south_a','Shooters Island shipyard, south shed A',[(555,942),(668,942),(668,975),(555,975)],8,'wood'),
 ('south_b','Shooters Island shipyard, south office or shop (windowed roof)',[(735,980),(840,980),(840,1025),(735,1025)],8,'brick'),
]
for k,n,pp,h,m in sheds:
    rect_row(f'shooters_{k}',n,1916,1938,C,[px(*p) for p in pp],h,m,NOTE,URL)
# ---- 2. Gulf Oil terminal, Bloomfield: tanks detected on the 1951 photograph
t=pd.read_csv('data/interim/holes_boroughs_raw/tanks_gulfW.csv')
t=t[(t.inside>0.7)&(t.inside>t.outside+0.12)&(t.lat<40.629)&(t.lon>-74.195)&(t.diam_m>=30)&(t.diam_m<=42)].sort_values('acc',ascending=False)
keep=[]
for r in t.itertuples():
    if all(math.hypot((r.lon-q.lon)*84300,(r.lat-q.lat)*111320)>25 for q in keep): keep.append(r)
UB='https://en.wikipedia.org/wiki/Bloomfield,_Staten_Island'
from types import SimpleNamespace as NS
keep.append(NS(lon=-74.18519,lat=40.61939,diam_m=38.0))   # the bright tank with a halo the detector missed (read by eye)
for i,r in enumerate(sorted(keep,key=lambda q:(-q.lat,q.lon))):
    d=round(r.diam_m*2)/2
    rows.append(dict(id=f'gulf_tank_{i+1:02d}',name=f'Gulf Oil terminal, oil storage tank {i+1} (Bloomfield)',start_year=1936,end_year=1999,lat=round(r.lat,6),lon=round(r.lon,6),height_m=12,storeys='',material='steel',outline='',
      shape_note=("Round tank seen on the City's 1951 aerial mosaic (NYC OTI, CC BY 4.0): centre and diameter measured by a circle detector and checked on the image, +-5 m; the 1951 mosaic covers only part of the terminal, which had 82 tanks "
                  "of 215 million gallons in all. Terminal 'built in 1936', closed 1998 (Wikipedia, Bloomfield). Year each tank was built and the year it came down are ESTIMATED (1936 and 1999: the terminal's own); height ESTIMATED (a 40 ft shell)."),
      source_url=UB,footprint_m=f'{d:g}x{d:g}',rotation_deg=0))
pd.DataFrame(rows)[COLS].to_csv('data/tables/notable_demolished.boroughs2.csv',index=False,quoting=csv.QUOTE_MINIMAL)
print(len(rows),'rows;',len(keep),'tanks')
# ---- 3. standing buildings on Rikers dated by the photograph
con=duckdb.connect(); con.execute("INSTALL spatial; LOAD spatial;")
kb=[]
spec=[(2109478,'Rikers Island, long dormitory sheds of the penitentiary yard (six parallel sheds, footprint 2109478)',1940,
       "The six long parallel sheds stand on this outline in the City's 1951 aerial mosaic and are not on the 1924 one; the built file had 1984.8 (neighbours). Rikers' jail opened 1932 (DOC history page jailist1.html); the sheds were built between the two photographs: 1940 is the middle of 1932-1951, ESTIMATED. Use of the buildings not identified."),
      (2116653,'Rikers Island, hollow-square building at the northern end (footprint 2116653)',1936,
       "A hollow-square building with a courtyard stands on this outline in the City's 1951 aerial mosaic; the row of site_map:rikers_island_jails:2116653 (1961, 'absent on the 1956 sheet') is contradicted by the photograph. Built after the jail opened in 1932 and before 1951; 1936 ESTIMATED (the DOC history page dates the original Rikers Island Hospital to 1932 and the Penitentiary to 1933, which this may be; not established).")]
HP='https://en.wikipedia.org/wiki/Hunts_Point,_Bronx'
for b,n,y,why in [(2109490,'Hunts Point Produce Market, building (footprint 2109490)',1967,'Produce Market'),(2109489,'Hunts Point Produce Market, building (footprint 2109489)',1967,'Produce Market'),
                  (2109488,'Hunts Point Produce Market, building (footprint 2109488)',1967,'Produce Market'),(2109486,'Hunts Point Meat Market, building (footprint 2109486)',1974,'Meat Market'),
                  (2109487,'Hunts Point Meat Market, building (footprint 2109487)',1974,'Meat Market'),(2109485,'Hunts Point Meat Market, building (footprint 2109485)',1974,'Meat Market')]:
    spec.append((b,n,y,f"One of the big sheds of the {why}, which opened in {y} ('the openings of the New York City Produce market in 1967 and Hunts Point Meat Market in 1974': Wikipedia, Hunts Point); the built file dated it from its neighbours' years (2003-08 for the meat sheds, 1971-76 for the produce ones), which leaves the market's ground empty in 1980. Opening year used for the whole market: ESTIMATED (an extension of a later year is possible; the 1951 photograph shows the ground as dump and marsh)."))
for b,n,y,note in spec:
    r=con.execute(f"select ST_X(ST_PointOnSurface(geometry)),ST_Y(ST_PointOnSurface(geometry)),ST_Contains(geometry,ST_PointOnSurface(geometry)) from 'data/interim/nyc_buildings.parquet' where bin={b}").fetchone()
    assert r[2]
    kb.append(dict(id=f'boroughs2_{b}',name=n,lat=round(r[1],6),lon=round(r[0],6),bin=b,start_year=y,end_year=9999,source_url=(HP if n.startswith('Hunts') else 'https://correctionhistory.org/html/chronicl/nycdoc/html/jailist1.html'),note=note))
pd.DataFrame(kb).to_csv('data/tables/known_building_dates.boroughs2.csv',index=False)
print(kb[0]['lat'],kb[0]['lon'])
