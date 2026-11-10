"""Date today's footprints inside a site by the USGS 1:24,000 editions that first draw them.

presence(fps) -> DataFrame, one row per footprint x edition: fi, year, quad, state, score
    state = drawn | absent | na   (na: under the sheet's urban tint or lettering, where the
    sheet omits ordinary buildings - absence there says nothing)
bracket(pres, founded) -> per footprint: last_absent, first_drawn, est_start, evidence

A footprint is *drawn* when the sheet's black ink (plus the purple of a photorevision),
opened by ~6 m (drops roads, rails, lettering) - or, for the cross-hatched symbols of large
buildings, ink density >= 22 % over 12 m, opened by ~14 m - covers >= 30 % of the footprint grown by the
registration tolerance (8 m). The 1890s 1:62,500 sheets are used for absence only: no ink
within 80 m of the footprint (their symbols are not to scale and sit up to ~70 m off).
The start year is the midpoint of the last edition not drawing the footprint and the first
edition drawing it - only for a clean sequence (absent on every earlier sheet, drawn on every
later one); always `estimated`.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import ndimage as ndi

sys.path.insert(0, str(Path(__file__).resolve().parent))
import topo  # noqa: E402

def _old_shifts():
    """Registration shifts (metres east, north) of the 1890s 1:62,500 sheets, measured against
    today's streets by the natural-layer tools (data/manual/natural/usgs_sheets.json)."""
    import json
    f = topo.ROOT / "data" / "manual" / "natural" / "usgs_sheets.json"
    try:
        return {k: tuple(v["shift_m"]) for k, v in json.loads(f.read_text()).items() if "shift_m" in v}
    except Exception:  # noqa: BLE001
        return {}


OLD_SHIFT = _old_shifts()
TOL = 8.0
THR = 0.30


def ink(img, purple=False, dark=120):
    r, g, b = (img[:, :, i].astype(int) for i in range(3))
    m = (r < dark) & (g < dark) & (b < dark) & (np.abs(r - g) < 45) & (np.abs(g - b) < 45)
    if purple:
        m |= ((r - g) > 38) & ((b - g) > 18) & (g < 175)
    return m


def tint(img):
    """Urban tint of the 1:24k sheets (salmon / pink, later grey-pink screens)."""
    r, g, b = (img[:, :, i].astype(int) for i in range(3))
    return (r > 185) & ((r - g) > 28) & ((r - b) > 20) & (g > 110)


def presence(fps, log=print):
    """fps: GeoDataFrame (EPSG:4326) of footprints. Footprints are grouped by 7.5' quad."""
    rows = []
    cen = fps.geometry.representative_point()
    quad = [(int(np.floor(x / 0.125)), int(np.floor(y / 0.125))) for x, y in zip(cen.x, cen.y)]
    fps = fps.assign(_q=quad, _cx=cen.x.values, _cy=cen.y.values)
    for q, grp in fps.groupby("_q"):
        w, s, e, n_ = grp.geometry.total_bounds
        cx, cy = (w + e) / 2, (s + n_) / 2
        x0, y0 = topo.ll2loc(w, s, cx, cy)
        half = float(min(3000.0, max(abs(x0), abs(y0)) + 150))
        eds = topo.editions(float(grp._cx.median()), float(grp._cy.median()))
        for sc, name, year, kind, imp, url, yrs in eds:
            res = 2.0 if sc <= 25000 else 4.0
            res = max(res, half / 1400.0)
            old = sc > 31680
            shift = (0.0, 0.0)
            if old:
                shift = OLD_SHIFT.get(url.split("/")[-1].replace("%20", "_").replace("_62500_geo.tif", ""))
                if shift is None:
                    continue  # only the 15' sheets whose registration was measured
            try:
                img = topo.render(url, cx, cy, half, res, shift=tuple(shift))
            except Exception as ex:  # noqa: BLE001
                log(f"   skip {name} {year}: {ex}")
                continue
            if img is None:
                continue
            n = img.shape[0]
            blank = (img.min(axis=2) > 250)
            m = ink(img, purple=(year >= 1968), dark=120 if not old else 95)
            k = max(1, int(round(6.0 / res)))
            if old:
                mo = m
            else:
                # solid symbols: ink opened by ~6 m; hatched symbols (large buildings are drawn
                # cross-hatched from the 1950s): ink density >= 22 % over ~12 m, opened by ~14 m
                solid = ndi.binary_opening(m, np.ones((k, k), bool))
                k2 = max(2, int(round(14.0 / res)))
                dens = ndi.uniform_filter(m.astype(np.float32), max(3, int(round(12.0 / res))))
                hat = ndi.binary_opening(dens >= 0.22, np.ones((k2, k2), bool))
                mo = solid | hat
            tn = ndi.uniform_filter(tint(img).astype(np.float32), int(80 / res)) if not old else None
            tp = max(1, int(round((TOL if not old else 80.0) / res)))
            nd = 0
            for fi, gm in zip(grp.index, grp.geometry):
                x, y = topo.ll2loc(*np.asarray(gm.exterior.coords).T, cx, cy)
                i0 = int(max(0, (x.min() + half) / res - 2 * tp - 2)); i1 = int(min(n, (x.max() + half) / res + 2 * tp + 3))
                j0 = int(max(0, (half - y.max()) / res - 2 * tp - 2)); j1 = int(min(n, (half - y.min()) / res + 2 * tp + 3))
                if i1 - i0 < 2 or j1 - j0 < 2:
                    continue
                from PIL import Image, ImageDraw
                im = Image.new("L", (i1 - i0, j1 - j0), 0)
                ImageDraw.Draw(im).polygon([((a + half) / res - i0, (half - b) / res - j0) for a, b in zip(x, y)], fill=1, outline=1)
                pm = np.asarray(im, bool)
                pb = ndi.binary_dilation(pm, iterations=tp)
                if blank[j0:j1, i0:i1][pb].mean() > 0.5:
                    continue  # off the map face
                sc_ = float(mo[j0:j1, i0:i1][pb].mean())
                if old:
                    state = "absent" if sc_ == 0 else "na"
                else:
                    if sc_ >= THR:
                        state = "drawn"
                    elif tn[(j0 + j1) // 2, (i0 + i1) // 2] > 0.25:
                        state = "na"
                    else:
                        state = "absent"
                nd += state == "drawn"
                rows.append((fi, year, sc, name, state, round(sc_, 3), imp or 0))
            log(f"   {name} {year} (1:{sc}): {nd} of {len(grp)} drawn")
    return pd.DataFrame(rows, columns=["fi", "year", "scale", "quad", "state", "score", "imprint"])


def bracket(pres, founded=None):
    out = []
    for fi, t in pres.groupby("fi"):
        t = t.sort_values("year")
        t24 = t[t.scale <= 31680]
        st = dict(zip(t24.year, t24.state))
        yrs = sorted(st)
        first = None
        for k, y in enumerate(yrs):
            if st[y] != "drawn":
                continue
            later = [st[z] for z in yrs[k:] if st[z] != "na"]
            if np.mean([s == "drawn" for s in later]) >= 0.6:
                first = y
                break
        if first is None:
            out.append((fi, np.nan, np.nan, np.nan, "never drawn"))
            continue
        if founded and first < founded - 1:
            # the sheet is older than the site: it draws a predecessor on the same ground
            out.append((fi, np.nan, float(first), np.nan, f"drawn before the site's founding ({int(first)}): a predecessor"))
            continue
        absent = [y for y, s in zip(t.year, t.state) if s == "absent" and y < first and (founded is None or y >= founded - 1)]
        la = max(absent) if absent else None
        # a clean bracket only: nothing drawn before the last absence, nothing absent after the
        # first drawing (else the symbol was missed on some sheet, or the building replaced another)
        clean = (not any(st[z] == "drawn" for z in yrs if z < first)
                 and not any(st[z] == "absent" for z in yrs if z > first))
        if la is not None and not clean:
            out.append((fi, np.nan, float(first), np.nan, f"inconsistent sheets (first drawn {int(first)})"))
            continue
        if la is not None:
            est = (la + first) / 2.0
            if founded:
                est = max(est, founded)
            ev = f"absent on the {int(la)} sheet, drawn on the {int(first)} sheet"
        elif founded and first - founded <= 15:
            est, ev = float(founded), f"drawn on the first sheet after the site's founding ({int(first)})"
        else:
            est, ev = np.nan, f"drawn on the {int(first)} sheet (no earlier sheet shows the ground empty)"
        out.append((fi, la if la is not None else np.nan, float(first), est, ev))
    return pd.DataFrame(out, columns=["fi", "last_absent", "first_drawn", "est_start", "evidence"]).set_index("fi")
