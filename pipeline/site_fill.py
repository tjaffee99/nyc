"""Buildings inside the yards, forts and institutions (data/manual/sites), read off the aerial
photographs of 1924 and 1951.

The evidence-driven fill (gap_fill.py) cuts lots along street frontages: a navy yard, a fort, an
island of institutions or a works has no frontages, and what stood inside it before today's
buildings is in no atlas (the fire-insurance atlases did not map federal and city grounds). Here
the photographs themselves give the outlines:

  roofs     each photograph is cut into patches of even tone (Felzenszwalb's segmentation); a patch
            of building size that fills its bounding rectangle is a candidate roof, drawn as that
            rectangle and moved by the photograph's measured shift against the map.
  evidence  the presence model of aerial_presence.py (unchanged, through gap_fill.score_lots) scores
            every candidate on its photograph; kept at the lot fill's thresholds (Staten Island 0.9),
            only where no building of the map, standing or vanished, lies on it at the time, not on
            today's water, and only while the site existed. Kept roofs that touch are one building.
  years     a building seen in 1924 starts no later than the photograph, spread back over SPREAD
            years (a third of them over the recorded years of the site's own buildings where it has
            five), not before the site's founding; one seen only in 1951 that the 1924 photograph
            does not show starts in between. It ends when the map's next building on the
            spot went up, at the photograph that shows it gone, in the years after the site closed,
            or between 1956 and 1984 where nothing says. All years are estimates.
  marked    `procedural` (an outline found by a program is not a survey), evidence `site+aerial1924`,
            `site+aerial1951` or `site+aerial1924+1951`; the lowest rank, like the lot fill: anything
            real replaces it.

    python site_fill.py                  # fetch the missing photograph tiles, read, write gapfill_sites.parquet
    python site_fill.py report           # counts per site
    python site_fill.py look site=<id>   # both photographs of a site with the outlines drawn

Run after `gap_fill.py fresh assemble` (it reads that stage's snapshot of the map and its rows).
About four minutes.
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
import shapely

import aerial_presence as ap
import gap_fill as gf
from common import MANUAL, log

OUT = gf.WORK / "gapfill_sites.parquet"
STATS = gf.WORK / "site_stats.json"
MPP = 0.905              # metres per pixel of the photographs at this latitude (aerial_presence.Z)
SKIP_KINDS = {"landfill", "quarry"}
SEG_SCALES = (25, 80, 250)   # Felzenszwalb's scale: larger = larger patches; a roof may come out at any of them
ROOF_M2 = (60.0, 20000.0)
ROOF_FILL = 0.7          # share of its bounding rectangle a patch must fill
ROOF_MIN_SIDE = 5.0      # metres
ROOF_ASPECT = 12.0
OCCUPIED = 0.3           # share of a candidate under a building of the map: the map has it
JOIN_PX = 1.3            # kept roofs this near are one building (the two slopes of a ridged roof)
SPREAD = 60.0            # years a start is spread back
POOL_MIN = 5
POOL_SHARE = 1 / 3
KIND = {  # storeys to choose from, metres per storey, material
    "industrial": ((1, 1, 2, 2, 3), 4.2, "brick"),
    "military": ((1, 2, 2, 3), 3.3, "frame"),
    "fort": ((1, 2, 2, 3), 3.3, "brick"),
    "institution": ((2, 3, 3, 4), 3.6, "brick"),
}
ONLY = [q.split("=", 1)[1] for q in sys.argv[1:] if q.startswith("site=")]     # for a test: site=<id>
KIND_OF = {"fort": "fort", "military_base": "military", "hospital_campus": "institution", "asylum": "institution",
           "prison": "institution", "other": "institution"}
EVID = {1: "site+aerial1924", 2: "site+aerial1924+1951", 3: "site+aerial1951"}


def sites():
    """The grounds: one row per outline. A ground that the table carries as successive sites (a fort
    renamed, an army post handed to the coast guard) is one ground with its phases; phases that
    follow one another without a gap are one run (start, end, kind of its last phase)."""
    import geopandas as gpd
    g = gpd.read_file(MANUAL / "sites" / "sites.geojson")
    g = g[~g.kind.isin(SKIP_KINDS) & g.geometry.notna()].reset_index(drop=True)
    g["start_year"] = pd.to_numeric(g.start_year, errors="coerce").fillna(1800)
    g["end_year"] = pd.to_numeric(g.end_year, errors="coerce").fillna(9999)
    g["gpx"] = gf.to_px(shapely.make_valid(g.geometry.values))
    c = shapely.get_coordinates(shapely.centroid(g.gpx.values))
    g["key"] = [f"{round(x / 20)}_{round(y / 20)}_{round(a)}" for (x, y), a in zip(c, g.area_ha.values)]
    rows = []
    for _, q in g.sort_values("start_year").groupby("key", sort=False):
        runs = []
        for r in q.itertuples():
            if runs and r.start_year <= runs[-1][1] + 1:
                runs[-1] = (runs[-1][0], max(runs[-1][1], r.end_year), r.kind)
            else:
                runs.append((r.start_year, r.end_year, r.kind))
        rows.append({"id": q.id.values[0], "gpx": q.gpx.values[0], "area_ha": float(q.area_ha.values[0]), "runs": runs})
    g = pd.DataFrame(rows).sort_values("area_ha").reset_index(drop=True)     # a site inside a larger one keeps its own ground
    if ONLY:
        g = g[g.id.isin(ONLY)].reset_index(drop=True)
    return g


def run_at(runs, y):
    for a, b, k in runs:
        if a <= y < b:
            return a, b, k
    return None


def fetch_tiles(S):
    """The photograph tiles under the sites (the presence stage fetched them only around today's footprints)."""
    need = set()
    for g in S.gpx.values:
        x0, y0, x1, y1 = shapely.bounds(g)
        for tx in range(int((x0 - 70) // gf.TILE), int((x1 + 70) // gf.TILE) + 1):
            for ty in range(int((y0 - 70) // gf.TILE), int((y1 + 70) // gf.TILE) + 1):
                need.add((tx, ty))
    for year in ap.YEARS:
        miss = [t for t in sorted(need) if ap.tile_path(year, gf.Z, *t) is None]
        for tx, ty in miss:
            ap.fetch_tile(year, gf.Z, tx, ty, pause=0.05)
        log(f"site fill: {year}: {len(need)} tiles under the sites, {len(miss)} fetched")


def photo(bx, by, year):
    """The block's photograph as gap_fill.score_lots reads it: grey, valid, pixel layers, origin."""
    blk = ap.load_block(year, bx, by)
    if blk is None:
        return None
    g, valid, x0, y0 = blk
    cut = ap.PAD * gf.TILE - ap.MARGIN
    g, valid = g[cut:-cut, cut:-cut], valid[cut:-cut, cut:-cut]
    valid = ap.blank_mask(g, valid, year)
    if not valid.any():
        return None
    return g, valid, ap.pixel_layers(g, valid), np.array([x0 + cut, y0 + cut], "float64")


def roofs(g, valid, win):
    """Candidate roofs in the window (array pixels x0, y0, x1, y1) of a photograph: rectangles, array pixels."""
    from scipy import ndimage as ndi
    from skimage.measure import find_contours, regionprops
    from skimage.segmentation import felzenszwalb
    ax0, ay0, ax1, ay1 = win
    crop = g[ay0:ay1, ax0:ax1]
    if crop.shape[0] < 30 or crop.shape[1] < 30 or valid[ay0:ay1, ax0:ax1].mean() < 0.2:
        return []
    sm = ndi.gaussian_filter(crop, 0.8) / 255.0
    out = []
    px2 = MPP * MPP
    for scale in SEG_SCALES:
        lab = felzenszwalb(sm, scale=scale, sigma=0.5, min_size=50)
        for r in regionprops(lab + 1):
            if not (ROOF_M2[0] <= r.area * px2 <= ROOF_M2[1]):
                continue
            m = np.zeros((r.bbox[2] - r.bbox[0] + 2, r.bbox[3] - r.bbox[1] + 2), bool)
            m[1:-1, 1:-1] = r.image
            m = ndi.binary_opening(m, iterations=1)
            if m.sum() * px2 < ROOF_M2[0]:
                continue
            cs = find_contours(m.astype(float), 0.5)
            c = max(cs, key=len)
            if len(c) < 4:
                continue
            poly = shapely.Polygon(np.column_stack([c[:, 1] + r.bbox[1] - 1 + ax0, c[:, 0] + r.bbox[0] - 1 + ay0]))
            if not poly.is_valid:
                poly = poly.buffer(0)
            if poly.is_empty or poly.geom_type != "Polygon":
                continue
            mrr = shapely.minimum_rotated_rectangle(poly)
            if mrr.geom_type != "Polygon" or poly.area < ROOF_FILL * mrr.area:
                continue
            rc = shapely.get_coordinates(mrr)
            a, b = np.hypot(*(rc[1] - rc[0])) * MPP, np.hypot(*(rc[2] - rc[1])) * MPP
            if min(a, b) < ROOF_MIN_SIDE or max(a, b) > ROOF_ASPECT * min(a, b):
                continue
            out.append(mrr)
    return out


def best(geoms, p):
    """The kept candidates without the ones that lie on a better one (the same roof found at another scale)."""
    order = np.lexsort((-shapely.area(geoms), -np.round(p, 2)))
    keep, got = [], []
    for i in order:
        o = geoms[i]
        if got:
            j = shapely.STRtree(got).query(o, predicate="intersects")
            if len(j) and shapely.area(shapely.intersection(o, shapely.union_all([got[k] for k in j]))) > 0.3 * o.area:
                continue
        got.append(o)
        keep.append(i)
    return geoms[np.array(keep, int)] if keep else geoms[:0]


def joined(geoms):
    """Kept roofs that touch, as one outline each."""
    if not len(geoms):
        return []
    u = shapely.buffer(shapely.union_all(shapely.buffer(geoms, JOIN_PX, join_style="mitre")), -JOIN_PX, join_style="mitre")
    out = []
    for p in (u.geoms if hasattr(u, "geoms") else [u]):
        if p.geom_type != "Polygon" or p.is_empty or p.area * MPP * MPP < ROOF_M2[0] * 0.8:
            continue
        mrr = shapely.minimum_rotated_rectangle(p)
        if p.area >= 0.8 * mrr.area:
            out.append(mrr)
            continue
        q = shapely.buffer(shapely.buffer(shapely.Polygon(p.exterior), -2.5, join_style="mitre"), 2.5, join_style="mitre")   # no thin tails
        for v in (q.geoms if hasattr(q, "geoms") else [q]):
            if v.geom_type == "Polygon" and not v.is_empty and v.area * MPP * MPP >= ROOF_M2[0]:
                out.append(shapely.simplify(v, 1.5))
    return out


def on_map(geoms, both, y):
    """Per outline at year y: share under the map's buildings of the time, the end of the last
    building before and the start of the next one after on the spot."""
    n = len(geoms)
    share, last, nxt = np.zeros(n), np.full(n, -np.inf), np.full(n, np.inf)
    if not n or not len(both):
        return share, last, nxt
    bg = both.g.values
    li, ei = shapely.STRtree(bg).query(geoms, predicate="intersects")
    if not len(li):
        return share, last, nxt
    ia = shapely.area(shapely.intersection(geoms[li], bg[ei])) / shapely.area(geoms[li])
    bs, be = both.start_year.values[ei].astype(float), both.end_year.values[ei].astype(float)
    on = (bs <= y + gf.AFTER_GAP) & (be > y - gf.BEFORE_GAP)
    np.add.at(share, li[on], ia[on])
    k = ia > 0.1
    aft = k & (bs > y + gf.AFTER_GAP)
    np.minimum.at(nxt, li[aft], bs[aft])
    bef = k & (be <= y - gf.BEFORE_GAP)
    np.maximum.at(last, li[bef], be[bef])
    return share, last, nxt


def step_build():
    import geopandas as gpd
    gf.step_snapshot()
    S = sites()
    fetch_tiles(S)
    fill = None
    if gf.OUT.exists():
        f = gpd.read_parquet(gf.OUT)
        fill = pd.DataFrame({"start_year": f.start_year.values.astype(float), "end_year": f.end_year.values.astype(float),
                             "g": gf.to_px(f.geometry.values)})
    s_blk = gf.NB * gf.TILE
    taken = []
    rows, st = [], {}
    for _, s in S.iterrows():
        x0, y0, x1, y1 = shapely.bounds(s.gpx)
        blocks = [(bx, by) for bx in range(int(x0 // s_blk), int(x1 // s_blk) + 1) for by in range(int(y0 // s_blk), int(y1 // s_blk) + 1)]
        run = {y: run_at(s.runs, y) for y in ap.YEARS}
        mine = shapely.difference(s.gpx, shapely.union_all(taken)) if taken else s.gpx
        taken.append(s.gpx)
        if all(r is None for r in run.values()) or mine.is_empty:
            continue
        lon, lat = gf.px_to_lonlat(*shapely.get_coordinates(shapely.centroid(s.gpx))[0])
        staten = (lat < 40.65) and (lon < -74.05)
        thr = {y: (gf.P_STATEN if staten else gf.P_STOOD[y]) for y in ap.YEARS}
        found = {y: [] for y in ap.YEARS}          # (outline in map pixels, block, what the map has around)
        exs = {}
        for b in blocks:
            ex = gf.existing_window(*b)
            exs[b] = ex
            water, _ = gf.water_window(*b)
            for y in ap.YEARS:
                if run[y] is None or not len(ex):
                    continue
                ph = photo(*b, y)
                if ph is None:
                    continue
                g, valid, P, off = ph
                H, W = g.shape
                bx0, by0 = b[0] * s_blk - off[0], b[1] * s_blk - off[1]        # the block proper, array pixels
                win = (int(max(x0 - off[0] - 12, 0)), int(max(y0 - off[1] - 12, 0)), int(min(x1 - off[0] + 12, W)), int(min(y1 - off[1] + 12, H)))
                if win[2] - win[0] < 30 or win[3] - win[1] < 30:
                    continue
                cand = roofs(g, valid, win)
                if not cand:
                    continue
                cand = np.array(cand, dtype=object)
                cc = shapely.get_coordinates(shapely.centroid(cand))
                k = (cc[:, 0] >= bx0) & (cc[:, 0] < bx0 + s_blk) & (cc[:, 1] >= by0) & (cc[:, 1] < by0 + s_blk)
                cand = cand[k]
                if not len(cand):
                    continue
                # the photograph's shift against the map, from the buildings that stood then
                real = ex[(ex.end_year.values == 9999) & (ex.start_year.values <= y - 1) & (ex.area.values > 60)]
                rg = shapely.transform(real.g.values, lambda c: c - off) if len(real) else np.array([], dtype=object)
                allg = np.concatenate([rg, cand])
                use = np.zeros(len(allg), bool)
                use[:len(rg)] = True
                cen = shapely.centroid(allg)
                dx, dy, _ = ap.estimate_offsets(P["G"], valid, allg, use, shapely.get_x(cen), shapely.get_y(cen))
                dx, dy = dx[len(rg):], dy[len(rg):]
                rep = shapely.get_num_coordinates(cand)
                xy = shapely.get_coordinates(cand) - np.column_stack([np.repeat(dx, rep), np.repeat(dy, rep)]) + off
                cm = shapely.set_coordinates(cand.copy(), xy)                     # map pixels
                inside = shapely.contains(mine, shapely.centroid(cm))
                if water is not None:
                    inside &= ~(shapely.area(shapely.intersection(cm, water)) > 0.3 * shapely.area(cm))
                cm = cm[inside]
                if not len(cm):
                    continue
                p, _, _ = gf.score_lots(*b, cm, ex, y)
                both = ex[["start_year", "end_year", "g"]]
                if fill is not None and len(fill):
                    near = fill[shapely.intersects(fill.g.values, shapely.box(*shapely.total_bounds(cm)))]
                    both = pd.concat([both, near], ignore_index=True)
                share, _, _ = on_map(cm, both, y)
                keep = (p >= thr[y]) & (share <= OCCUPIED)
                q = st.setdefault(s.id, {})
                q[f"cand{y}"] = q.get(f"cand{y}", 0) + int(len(cm))
                q[f"stood{y}"] = q.get(f"stood{y}", 0) + int((p >= thr[y]).sum())
                hit = both[(both.start_year.values <= y + gf.AFTER_GAP) & (both.end_year.values > y - gf.BEFORE_GAP)]
                for o in joined(best(cm[keep], p[keep])):
                    # cut away what the map has at the time
                    h2 = hit[shapely.intersects(hit.g.values, o)] if len(hit) else hit
                    if len(h2):
                        o = shapely.difference(o, shapely.buffer(shapely.union_all(h2.g.values), 1.0))
                        if not o.is_empty and o.geom_type != "Polygon":
                            o = max(getattr(o, "geoms", [o]), key=lambda v: v.area)
                        if o.is_empty or o.geom_type != "Polygon" or o.area * MPP * MPP < ROOF_M2[0]:
                            continue
                    found[y].append((o, b, both))
        # the same outline on the other photograph, and what the map has before and after on the spot
        other = {1924: 1951, 1951: 1924}
        po = {y: np.full(len(found[y]), np.nan) for y in ap.YEARS}
        sh_o = {y: np.zeros(len(found[y])) for y in ap.YEARS}
        info = {y: {} for y in ap.YEARS}
        for y in ap.YEARS:
            for b in blocks:
                idx = [i for i, (_, bb, _) in enumerate(found[y]) if bb == b]
                if not idx:
                    continue
                gm = np.array([found[y][i][0] for i in idx], dtype=object)
                both = found[y][idx[0]][2]
                if run[other[y]] is not None and len(exs[b]):
                    po[y][idx] = gf.score_lots(*b, gm, exs[b], other[y])[0]
                    sh_o[y][idx] = on_map(gm, both, other[y])[0]
                _, last, nxt = on_map(gm, both, y)
                _, _, nxt_o = on_map(gm, both, other[y])
                for j, i in enumerate(idx):
                    info[y][i] = (last[j], nxt[j], nxt_o[j])
        # recorded years of the site's own buildings
        allx = pd.concat(list(exs.values()), ignore_index=True).drop_duplicates("eid") if exs else pd.DataFrame()
        pool = np.zeros(0)
        if len(allx):
            q = allx[(allx.year_confidence.values == "exact") & shapely.intersects(allx.g.values, s.gpx)]
            pool = np.sort(q.start_year.values.astype(float))
        n_site = 0
        a_rows = []                                 # outlines of 1924 that stood on in 1951
        order = [(1924, i) for i in range(len(found[1924]))] + [(1951, i) for i in range(len(found[1951]))]
        for y, i in order:
            o = found[y][i][0]
            c = shapely.centroid(o)
            u = gf.h01(f"sfa|{s.id}|{round(c.x)}|{round(c.y)}")
            u2 = gf.h01(f"sfb|{s.id}|{round(c.x)}|{round(c.y)}")
            u3 = gf.h01(f"sfc|{s.id}|{round(c.x)}|{round(c.y)}")
            last, nxt, nxt_o = info[y][i]
            pv = po[y][i]
            if y == 1924:
                on51 = run[1951] is not None and sh_o[y][i] <= OCCUPIED and np.isfinite(pv) and (pv >= thr[1951] or (pv > 0.3 and u3 < pv))
                sg = 2 if on51 else 1
                if sg == 2:
                    a_rows.append(o)
            else:
                if any(shapely.area(shapely.intersection(o, v)) > 0.3 * o.area for v in a_rows):
                    continue                            # the 1924 outline already stands here
                sg = 3
            S0, _, kd = run[y]
            last_seen = 1951 if sg in (2, 3) else 1924
            E0 = run[last_seen][1]
            storeys, per, mat = KIND[KIND_OF.get(kd, "industrial")]
            lo = max(S0, last + 1.0)
            if sg == 3 and run[1924] is not None and np.isfinite(pv) and pv < 0.5:
                lo = max(lo, 1925.0)                    # the 1924 photograph does not show it
            hi = y - 0.5
            pl = pool[(pool >= lo) & (pool <= hi)]
            if len(pl) >= POOL_MIN and u3 < POOL_SHARE:
                start = float(pl[int(u * len(pl)) % len(pl)]) + 0.6 * (u2 - 0.5)
            else:
                start = hi - (0.5 + u * min(SPREAD, max(hi - lo - 0.5, 1.0)))
            start = float(np.clip(start, lo, hi))
            nx = nxt_o if sg == 2 else nxt
            if np.isfinite(nx):
                end, basis = nx - (gf.LEAD[0] + u2 * (gf.LEAD[1] - gf.LEAD[0])), "replaced"
            elif sg == 1:
                end, basis = 1926.0 + u2 * 24.0, "gone_by_1951"
            elif E0 < 9999:
                end, basis = E0 + 8.0 * u2, "site_closed"            # cleared in the years after the site closed
            else:
                end, basis = gf.OPEN_END[0] + u2 * (gf.OPEN_END[1] - gf.OPEN_END[0]), "open_today"
            if sg == 1:
                end = min(end, 1950.5)
            end = min(end, gf.RECORD_FROM)
            if end <= last_seen + 0.6:
                continue
            area = float(o.area) * MPP * MPP
            ns = storeys[int(u * 997) % len(storeys)]
            h = ns * per + 1.0
            if area > 2500 and kd not in KIND_OF:
                ns, h = 1, 10.0 + 6.0 * u3                 # a high-bay shed
            rows.append({"id": f"{s.id}_{round(c.x)}_{round(c.y)}", "start_year": round(start, 2), "end_year": round(end, 2),
                         "height_m": round(h, 1), "storeys": ns, "material": mat, "evidence": EVID[sg], "end_basis": basis,
                         "area": round(area, 1), "site": s.id, "geometry": o})
            n_site += 1
        st.setdefault(s.id, {}).update({"rows": n_site, "start": float(s.runs[0][0]), "end": float(s.runs[-1][1]), "kind": s.runs[-1][2],
                                        "kept1924": len(found[1924]), "kept1951": len(found[1951])})
        log(f"site fill: {s.id}: {n_site} buildings ({len(found[1924])} roofs kept on the 1924 photograph, {len(found[1951])} on 1951)")
    out = pd.DataFrame(rows)
    new = gpd.GeoDataFrame(out.drop(columns="geometry"), geometry=gf.to_lonlat(out.geometry.values), crs=4326) if len(out) else None
    if ONLY and OUT.exists():                      # a test run of some sites: the other sites' rows are kept
        old = gpd.read_parquet(OUT)
        old = old[~old.site.isin(S.id.values)]
        new = pd.concat([old, new], ignore_index=True) if new is not None else old
    if new is not None and len(new):
        new.to_parquet(OUT, index=False)
    elif OUT.exists():
        OUT.unlink()
    if not ONLY:
        STATS.write_text(json.dumps(st, indent=1))
    log(f"site fill: {len(out)} buildings in {out.site.nunique() if len(out) else 0} sites -> {OUT.name}; "
        + (str(out.evidence.value_counts().to_dict()) if len(out) else ""))
    return out


def step_report():
    import geopandas as gpd
    if not OUT.exists():
        print("no rows")
        return
    r = gpd.read_parquet(OUT)
    t = pd.DataFrame(json.loads(STATS.read_text())).T if STATS.exists() else pd.DataFrame()
    c = pd.DataFrame({"rows": r.groupby("site").size(), "ha": r.groupby("site").area.sum() / 1e4,
                      "in1900": r[(r.start_year <= 1900) & (r.end_year > 1900)].groupby("site").size(),
                      "in1925": r[(r.start_year <= 1925) & (r.end_year > 1925)].groupby("site").size(),
                      "in1950": r[(r.start_year <= 1950) & (r.end_year > 1950)].groupby("site").size(),
                      "in1975": r[(r.start_year <= 1975) & (r.end_year > 1975)].groupby("site").size()}).fillna(0)
    if len(t):
        c = c.join(t[[q for q in ("kind", "start", "cand1924", "stood1924", "cand1951", "stood1951") if q in t]])
    pd.set_option("display.width", 220)
    pd.set_option("display.max_rows", 200)
    print(c.sort_values("rows", ascending=False).round(1).to_string())
    print("all:", len(r), r.evidence.value_counts().to_dict(), r.end_basis.value_counts().to_dict())


def step_look(sid, scale=0.7):
    """Both photographs of a site with the outlines (red: seen in 1924 only, yellow: in both, cyan:
    in 1951 only) and the map's own buildings of the time (green) -> gapfill/look/."""
    import geopandas as gpd
    from PIL import Image, ImageDraw
    S = sites().set_index("id")
    s = S.loc[sid]
    x0, y0, x1, y1 = [int(v) for v in shapely.bounds(s.gpx)]
    x0, y0, x1, y1 = x0 - 40, y0 - 40, x1 + 40, y1 + 40
    rows = gpd.read_parquet(OUT)
    rows = rows[rows.site == sid]
    rg = gf.to_px(rows.geometry.values)
    s_blk = gf.NB * gf.TILE
    exs = [gf.existing_window(bx, by) for bx in range(x0 // s_blk, x1 // s_blk + 1) for by in range(y0 // s_blk, y1 // s_blk + 1)]
    ex = pd.concat(exs, ignore_index=True).drop_duplicates("eid")
    (gf.WORK / "look").mkdir(exist_ok=True)
    for year in ap.YEARS:
        img = np.zeros((y1 - y0, x1 - x0), "uint8")
        for tx in range(x0 // gf.TILE, x1 // gf.TILE + 1):
            for ty in range(y0 // gf.TILE, y1 // gf.TILE + 1):
                t = ap.read_tile(year, gf.Z, tx, ty)
                if t is None:
                    continue
                ax, ay = tx * gf.TILE - x0, ty * gf.TILE - y0
                sx0, sy0 = max(ax, 0), max(ay, 0)
                sx1, sy1 = min(ax + gf.TILE, img.shape[1]), min(ay + gf.TILE, img.shape[0])
                if sx1 > sx0 and sy1 > sy0:
                    img[sy0:sy1, sx0:sx1] = np.clip(t[0][sy0 - ay:sy1 - ay, sx0 - ax:sx1 - ax], 0, 255)
        im = Image.fromarray(img).convert("RGB")
        im = im.resize((int(im.width * scale), int(im.height * scale)))
        dr = ImageDraw.Draw(im)

        def draw(geom, col, width=1):
            c = (shapely.get_coordinates(shapely.get_exterior_ring(geom)) - [x0, y0]) * scale
            dr.line([tuple(q) for q in c], fill=col, width=width)
        alive = ex[(ex.start_year.values <= year + gf.AFTER_GAP) & (ex.end_year.values > year - gf.BEFORE_GAP)]
        for gm in alive.g.values:
            for q in (gm.geoms if hasattr(gm, "geoms") else [gm]):
                if q.geom_type == "Polygon":
                    draw(q, (0, 255, 0))
        for gm, ev, a, b in zip(rg, rows.evidence.values, rows.start_year.values, rows.end_year.values):
            if a <= year < b:
                draw(gm, {EVID[1]: (255, 60, 60), EVID[2]: (255, 230, 0), EVID[3]: (0, 220, 255)}[ev], 2)
        draw(s.gpx if s.gpx.geom_type == "Polygon" else max(s.gpx.geoms, key=lambda q: q.area), (255, 255, 255))
        out = gf.WORK / "look" / f"site_{sid}_{year}.png"
        im.save(out)
        print(out, im.size)


if __name__ == "__main__":
    a = sys.argv[1:]
    if "look" in a:
        for q in ONLY:
            step_look(q)
    elif "report" in a:
        step_report()
    else:
        step_build()
        step_report()
