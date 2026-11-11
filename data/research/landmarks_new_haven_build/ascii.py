import sys, shapely, re
# usage: ascii.py "x,y,x,y..." [cell]
nums=[float(v) for v in sys.argv[1].replace(' ','').split(',')]
cell=float(sys.argv[2]) if len(sys.argv)>2 else 2
pts=list(zip(nums[0::2],nums[1::2])); poly=shapely.Polygon(pts)
x0,y0,x1,y1=poly.bounds
y=y1
print(f"bounds x {x0:.0f}..{x1:.0f} y {y0:.0f}..{y1:.0f}; N up, cell {cell} m")
while y>y0-cell:
    row=''
    x=x0
    while x<x1+cell:
        row+= '#' if poly.contains(shapely.Point(x,y)) else '.'
        x+=cell
    print(f"{y:5.0f} {row}"); y-=cell
