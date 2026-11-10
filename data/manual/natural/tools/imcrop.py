"""Crop a plain image by pixel box, with a labelled pixel grid, for picking control points.
usage: python imcrop.py <image> <x0> <y0> <x1> <y1> <out.png> [scale] [grid_px]
"""
import sys

from PIL import Image, ImageDraw

Image.MAX_IMAGE_PIXELS = None
src, x0, y0, x1, y1, out = sys.argv[1], *map(int, sys.argv[2:6]), sys.argv[6]
scale = float(sys.argv[7]) if len(sys.argv) > 7 else 1.0
grid = int(sys.argv[8]) if len(sys.argv) > 8 else 0
im = Image.open(src).crop((x0, y0, x1, y1))
if scale != 1.0:
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
if grid:
    d = ImageDraw.Draw(im)
    gx = (x0 // grid + 1) * grid
    while gx < x1:
        d.line([((gx - x0) * scale, 0), ((gx - x0) * scale, im.height)], fill=(255, 0, 255), width=1)
        d.text(((gx - x0) * scale + 2, 2), str(gx), fill=(255, 0, 255))
        gx += grid
    gy = (y0 // grid + 1) * grid
    while gy < y1:
        d.line([(0, (gy - y0) * scale), (im.width, (gy - y0) * scale)], fill=(255, 0, 255), width=1)
        d.text((2, (gy - y0) * scale + 2), str(gy), fill=(255, 0, 255))
        gy += grid
im.save(out)
print(out, im.size)
