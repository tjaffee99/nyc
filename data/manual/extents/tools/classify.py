"""Built-up blocks from a warped map by tone: blocks the map shades / stipples / fills with buildings
are darker than paper, streets and unbuilt blocks.

  darkness = (paper - grey) / paper, blurred, then a median over `win` metres (drops line work,
  lettering and scattered field symbols, keeps even tone) -> threshold -> opening, closing across
  streets, small holes filled, small parts dropped -> polygons clipped to a hand-drawn envelope
  (the map's own land; water hachures are as dark as blocks).

Used as a module by build.py (snapshot definitions live there); CLI for a quick look:
  python -I classify.py <map_id> <x0,y0,x1,y1> <out.png> [--mpp 1.5] [--win 9] [--thr 0.12]
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
import shapely
import shapely.geometry as sg
from rasterio import features
from affine import Affine
sys.path.insert(0, str(Path(__file__).resolve().parent))
import warp
import streets as S


def darkness(rgb, win_px, blur_px=1.0, local_bg_px=0):
    g = rgb.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
    paper = np.percentile(g[g < 250], 92) if (g < 250).any() else 255.0   # 255 = outside the scan
    if local_bg_px:   # stained / varnished sheets: paper tone = local 90th percentile of the grey
        k = 8
        small = g[::k, ::k]
        bg = ndi.percentile_filter(small, 90, size=max(3, int(local_bg_px / k) | 1))
        bg = ndi.zoom(bg, (g.shape[0] / bg.shape[0], g.shape[1] / bg.shape[1]), order=1)[:g.shape[0], :g.shape[1]]
        d = np.clip((bg - g) / np.maximum(bg, 1), 0, 1)
    else:
        d = np.clip((paper - g) / paper, 0, 1)
    d = ndi.gaussian_filter(d, blur_px)
    return ndi.median_filter(d, size=max(3, int(win_px) | 1)), paper


def disc(r):
    r = int(round(r))
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


def mask_to_polygons(mask, x0, y1, mpp):
    tr = Affine(mpp, 0, x0, 0, -mpp, y1)
    polys = [sg.shape(g) for g, v in features.shapes(mask.astype(np.uint8), mask=mask, transform=tr) if v == 1]
    return shapely.union_all(polys) if polys else sg.Polygon()


def built_mask(mapobj, box, mpp=1.5, win=9.0, thr=0.12, open_m=4.0, close_m=11.0, hole_ha=0.4, min_ha=0.3,
               envelope=None, verbose=True, local_bg=0.0, not_blue=False):
    """-> (shapely geometry in local metres, rgb array, darkness array)."""
    x0, y0, x1, y1 = box
    rgb = mapobj.render(x0, y0, x1, y1, mpp)
    d, paper = darkness(rgb, win / mpp, local_bg_px=local_bg / mpp)
    m = d > thr
    if not_blue:   # the backing cloth showing in a tear or between sheets is blue-grey, not ink
        m &= ~ndi.binary_dilation(rgb[..., 2].astype(int) > rgb[..., 0].astype(int) + 8, iterations=3)
    if envelope is not None:
        env = features.rasterize([(envelope, 1)], out_shape=m.shape, transform=Affine(mpp, 0, x0, 0, -mpp, y1), dtype="uint8").astype(bool)
        m &= env
    if open_m:
        m = ndi.binary_opening(m, disc(open_m / mpp))
    if close_m:
        pad = int(close_m / mpp) + 2
        m = np.pad(m, pad)
        m = ndi.binary_closing(m, disc(close_m / mpp))[pad:-pad, pad:-pad]
    # fill small holes, drop small parts
    lab, n = ndi.label(~m)
    if n:
        area = ndi.sum(np.ones_like(lab), lab, np.arange(1, n + 1)) * mpp * mpp / 1e4
        edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
        fill = [i + 1 for i in range(n) if area[i] < hole_ha and (i + 1) not in edge]
        m |= np.isin(lab, fill)
    lab, n = ndi.label(m)
    if n:
        area = ndi.sum(np.ones_like(lab), lab, np.arange(1, n + 1)) * mpp * mpp / 1e4
        m = np.isin(lab, [i + 1 for i in range(n) if area[i] >= min_ha])
    geom = mask_to_polygons(m, x0, y1, mpp)
    if envelope is not None:
        geom = geom.intersection(envelope)
    if verbose:
        q = np.percentile(d[env] if envelope is not None else d, [10, 25, 50, 75, 90, 97])
        print(f"   paper {paper:.0f}; darkness percentiles 10/25/50/75/90/97: " + " ".join(f"{v:.3f}" for v in q) + f"; thr {thr}; built {geom.area / 1e4:.1f} ha")
    return geom, rgb, d


def to_wgs(geom):
    return shapely.transform(geom, lambda c: np.column_stack(S.lonlat(c[:, 0], c[:, 1])))


def to_local(geom):
    return shapely.transform(geom, lambda c: np.column_stack(S.local(c[:, 0], c[:, 1])))


def preview(rgb, box, mpp, layers, out, grid=100, streets=False, max_px=1500, fill=True):
    """layers: [(local geometry, (r, g, b))]; saved downsized to max_px."""
    from PIL import ImageDraw
    x0, y0, x1, y1 = box
    from PIL import Image
    im = warp.annotate(rgb, x0, y0, x1, y1, mpp, streets=streets, grid=0)
    P = lambda c: [((x - x0) / mpp, (y1 - y) / mpp) for x, y in c]
    for geom, rgbc in layers:
        if geom is None or geom.is_empty:
            continue
        polys = [p for p in (geom.geoms if hasattr(geom, "geoms") else [geom]) if p.geom_type == "Polygon"]
        if fill and rgbc == (255, 0, 0):   # translucent fill of the extent: which side of a line is "in"
            msk = Image.new("L", im.size, 0)
            dm = ImageDraw.Draw(msk)
            for poly in polys:
                dm.polygon(P(np.array(poly.exterior.coords)), fill=70)
                for ring in poly.interiors:
                    dm.polygon(P(np.array(ring.coords)), fill=0)
            im.paste(Image.new("RGB", im.size, (255, 0, 0)), (0, 0), msk)
        d = ImageDraw.Draw(im, "RGBA")
        for poly in polys:
            for ring in [poly.exterior, *poly.interiors]:
                d.line(P(np.array(ring.coords)), fill=rgbc + (255,), width=2)
    k = max(im.size) / max_px
    if k > 1:
        im = im.resize((int(im.width / k), int(im.height / k)))
        mpp = mpp * k
    arr = np.asarray(im)
    im = warp.annotate(arr, x0, y0, x1, y1, mpp, grid=grid)
    im.save(out)
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    opt = {a[i][2:]: float(a[i + 1]) for i in range(3, len(a) - 1) if a[i].startswith("--")}
    box = [float(v) for v in a[1].split(",")]
    m = warp.MapWarp(a[0])
    geom, rgb, d = built_mask(m, box, mpp=opt.get("mpp", 1.5), win=opt.get("win", 9), thr=opt.get("thr", 0.12))
    print(preview(rgb, box, opt.get("mpp", 1.5), [(geom, (255, 0, 0))], a[2]))
