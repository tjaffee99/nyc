import sys,re,shapely
txt=open('rings_batch2.txt').read()+open('rings_batch1.txt').read()+open('rings_batch0.txt').read()
for pre in sys.argv[2:]:
    m=re.search(r'// '+pre+r'.*?\n.*?\nP\((.*?)\)\n',txt,re.S)
    nums=[float(v) for v in m.group(1).replace(' ','').split(',')]
    pts=list(zip(nums[0::2],nums[1::2])); poly=shapely.Polygon(pts); cell=float(sys.argv[1])
    x0,y0,x1,y1=poly.bounds; y=y1
    print(pre, f"x {x0:.0f}..{x1:.0f} y {y0:.0f}..{y1:.0f} cell {cell}")
    while y>y0-cell:
        x=x0; row=''
        while x<x1+cell: row+='#' if poly.contains(shapely.Point(x,y)) else '.'; x+=cell
        print(f"{y:5.0f} {row}"); y-=cell
