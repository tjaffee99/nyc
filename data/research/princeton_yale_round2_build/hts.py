import duckdb,re
from shapely import wkb,Point
con=duckdb.connect(); con.execute("SET memory_limit='1500MB'")
def run(f,src,ids):
    anchors=[]
    for m in re.finditer(r"anchor: (?:([A-Z_]+)|\[(-?[\d.]+), ([\d.]+)\])",open(src).read()): anchors.append(m)
    txt=open(src).read()
    consts={m.group(1):(float(m.group(2)),float(m.group(3))) for m in re.finditer(r"const ([A-Z_]+_ANCHOR): V2 = \[(-?[\d.]+), ([\d.]+)\]",txt)}
    for m in re.finditer(r"id: '([a-z0-9_]+)',\n\s+name: '([^']+)'.*?anchor: (?:([A-Z_]+)|\[(-?[\d.]+), ([\d.]+)\])",txt,re.S):
        pid,name,c,x,y=m.groups()
        if c: x,y=consts[c]
        else: x,y=float(x),float(y)
        rows=con.execute(f"select name,height_m,height_src,floors,footprint_src,area_m2,geometry from '{f}' where lon between {x-.0015} and {x+.0015} and lat between {y-.0012} and {y+.0012}").fetchall()
        best=None
        for r in rows:
            g=wkb.loads(bytes(r[6])); d=g.distance(Point(x,y))
            if best is None or d<best[0]: best=(d,r)
        r=best[1]; print(pid,'|',r[0],'| h',None if r[1] is None else round(r[1],1),r[2],'| fl',r[3],r[4],'| area',int(r[5]),'| d',round(best[0]*1e5))
run('data/interim/counties/nj_mercer.parquet','viewer/src/landmarks/princeton.ts',0)
print()
run('data/interim/counties/ct_south_central_connecticut.parquet','viewer/src/landmarks/new-haven.ts',0)
