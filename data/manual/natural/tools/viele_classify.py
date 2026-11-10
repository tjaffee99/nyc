"""Classify the Viele 1865 scan by colour and warp it to a 3 m UTM 18N grid with the stored georeference.

classes (uint8): 0 outside map / unknown, 1 upland (pale tint), 2 made land (salmon), 3 marsh or stream band
(green), 4 blue (pond, reservoir, river edge), 5 river paper (cream).
outputs: data/interim/natural/viele_class.tif, viele_rgb.tif (smoothed colours, for eyeballing)
"""
import json
import os

import numpy as np
import rasterio
from PIL import Image
from rasterio.transform import from_origin
from scipy import ndimage

import viele_georef as vg

Image.MAX_IMAGE_PIXELS = None
ROOT = "/home/user/nyc"
D = f"{ROOT}/data/interim/natural"
PX = 3.0


def smooth():
    p = f"{D}/viele_smooth.npy"
    if os.path.exists(p):
        return np.load(p)
    im = np.asarray(Image.open(vg.SRC)).astype("float32")
    L = im.mean(axis=2)
    ink = L < (ndimage.uniform_filter(L, 21) - 18)
    w = (~ink).astype("float32")
    sm = np.stack([ndimage.gaussian_filter(im[..., i] * w, 3) / np.maximum(ndimage.gaussian_filter(w, 3), 1e-3) for i in range(3)], axis=2)
    np.save(p, sm.astype("uint8"))
    return sm.astype("uint8")


def classify(sm):
    r, g, b = (sm[..., i].astype("int16") for i in range(3))
    rg = r - g
    cls = np.full(r.shape, 5, "uint8")           # cream paper: R-G about 17
    cls[(rg <= 10) & (g - b >= 12)] = 1           # pale upland tint: R-G about 3, G-B about 20 (river shading is greyer)
    cls[(rg < -4) | ((g - r > 2) & (r < 135))] = 3  # green: marsh, meadow streams
    cls[(rg >= 24) & (r - b >= 36)] = 2           # salmon: made land
    cls[(b - r > 8) & (b >= g - 2)] = 4           # blue
    return cls


def main():
    G = json.load(open(vg.OUT))
    sm = smooth()
    cls = classify(sm)
    H, W = cls.shape
    # main map only: drop frame, title, sections and the inset of the lower right
    yy, xx = np.mgrid[0:H, 0:W]
    out_of_map = (yy < 150) | (yy > 2900) | (xx < 250) | (xx > 9600) | ((xx > 8150) & (yy > 1450)) | ((xx > 6900) & (yy > 2150))
    cls[out_of_map] = 0
    del yy, xx
    # output grid
    gx, gy = np.meshgrid(np.linspace(250, 9600, 60), np.linspace(150, 2900, 30))
    e = np.empty(gx.size); n = np.empty(gx.size)
    m = gx.ravel() < G["seam"]
    e[m], n[m] = vg.apply(G["halves"]["left"]["coef"], gx.ravel()[m], gy.ravel()[m])
    e[~m], n[~m] = vg.apply(G["halves"]["right"]["coef"], gx.ravel()[~m], gy.ravel()[~m])
    x0, x1, y0, y1 = np.floor(e.min() / PX) * PX, np.ceil(e.max() / PX) * PX, np.floor(n.min() / PX) * PX, np.ceil(n.max() / PX) * PX
    w, h = int((x1 - x0) / PX), int((y1 - y0) / PX)
    # inverse (UTM -> pixel) per half: second-order least squares on the forward grid
    inv = {}
    for name, mm in (("left", m), ("right", ~m)):
        E, N = (e[mm] - 585000) / 10000, (n[mm] - 4510000) / 10000
        A = np.c_[np.ones_like(E), E, N, E * E, E * N, N * N]
        inv[name] = (np.linalg.lstsq(A, gx.ravel()[mm], rcond=None)[0], np.linalg.lstsq(A, gy.ravel()[mm], rcond=None)[0])
        print(name, "inverse fit rms px", np.sqrt(np.mean((A @ inv[name][0] - gx.ravel()[mm]) ** 2)))
    out = np.zeros((h, w), "uint8")
    rgb = np.zeros((3, h, w), "uint8")
    for r0 in range(0, h, 500):
        r1 = min(h, r0 + 500)
        NN, EE = np.mgrid[r0:r1, 0:w]
        E = ((x0 + (EE + 0.5) * PX) - 585000) / 10000
        N = ((y1 - (NN + 0.5) * PX) - 4510000) / 10000
        A = np.stack([np.ones_like(E), E, N, E * E, E * N, N * N], axis=-1)
        pxl, pyl = A @ inv["left"][0], A @ inv["left"][1]
        pxr, pyr = A @ inv["right"][0], A @ inv["right"][1]
        left = pxl < G["seam"]
        px = np.where(left, pxl, pxr); py = np.where(left, pyl, pyr)
        ok = (px >= 0) & (px < W - 1) & (py >= 0) & (py < H - 1) & (left | (pxr >= G["seam"]))
        ix, iy = np.clip(np.round(px).astype(int), 0, W - 1), np.clip(np.round(py).astype(int), 0, H - 1)
        out[r0:r1] = np.where(ok, cls[iy, ix], 0)
        for i in range(3):
            rgb[i, r0:r1] = np.where(ok, sm[iy, ix, i], 0)
    tr = from_origin(x0, y1, PX, PX)
    prof = dict(driver="GTiff", height=h, width=w, count=1, dtype="uint8", crs="EPSG:32618", transform=tr, compress="deflate")
    with rasterio.open(f"{D}/viele_class.tif", "w", **prof) as dst:
        dst.write(out, 1)
    prof.update(count=3)
    with rasterio.open(f"{D}/viele_rgb.tif", "w", **prof) as dst:
        dst.write(rgb)
    print("class share", {int(k): round(float((out == k).mean()), 3) for k in range(6)}, out.shape)


if __name__ == "__main__":
    main()
