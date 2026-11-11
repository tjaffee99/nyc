"""Real construction years for the outer counties that the State's parcel polygons do not carry.

    python county_years.py download dutchess|suffolk|nassau   NYS Tax Parcel Centroid Points -> data/raw/county_years/centroids_<county>/
    python county_years.py apply dutchess                     match the points to the county file's footprints, write year_raw

Source: NYS ITS Geospatial Services, "NYS Tax Parcel Centroid Points" (statewide, every county, 2025 roll),
https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Tax_Parcel_Centroid_Points/FeatureServer/0 .
Notes: data/research/county_years.md. Resumable; one process; small memory.
"""
from __future__ import annotations

import gzip
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import requests

from common import RAW, log

URL = "https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Tax_Parcel_Centroid_Points/FeatureServer/0/query"
FIELDS = "OBJECTID,COUNTY_NAME,MUNI_NAME,CITYTOWN_NAME,SWIS,PRINT_KEY,PROP_CLASS,YR_BLT,SQFT_LIVING,USED_AS_CODE,SQ_FT,ACRES"
CACHE = RAW / "county_years"
UA = "NYCThroughTime-research/0.1"
PAGE = 1000


def post(params, tries=6, timeout=200):
    for k in range(tries):
        try:
            r = requests.post(URL, data=params, headers={"User-Agent": UA}, timeout=timeout)
            if r.status_code == 200:
                d = r.json()
                if "error" not in d:
                    return d
                err = d["error"]
            else:
                err = f"HTTP {r.status_code}"
        except (requests.RequestException, ValueError) as e:
            err = repr(e)
        log(f"  retry {k + 1}: {err}")
        time.sleep(5 * (k + 1))
    raise RuntimeError(err)


def object_ids(county, where=None):
    f = CACHE / f"ids_{county}.json"
    if f.exists() and f.stat().st_size > 1000:
        return json.loads(f.read_text())["objectIds"]
    d = post({"where": where or f"COUNTY_NAME='{county.title()}'", "returnIdsOnly": "true", "f": "json"}, timeout=290)
    f.write_text(json.dumps(d))
    return d["objectIds"]


def download(county, where=None, ids=None):
    ids = sorted(ids if ids is not None else object_ids(county, where))
    d = CACHE / f"centroids_{county}"
    d.mkdir(parents=True, exist_ok=True)
    pages = [ids[i:i + PAGE] for i in range(0, len(ids), PAGE)]
    todo = [(i, p) for i, p in enumerate(pages) if not (d / f"p{i:05d}.json.gz").exists()]
    log(f"{county}: {len(ids)} points, {len(todo)} of {len(pages)} pages to fetch")

    def one(a):
        i, p = a
        r = post({"where": f"OBJECTID >= {p[0]} AND OBJECTID <= {p[-1]} AND COUNTY_NAME='{county.title()}'", "orderByFields": "OBJECTID", "outFields": FIELDS, "outSR": 4326, "geometryPrecision": 6, "f": "json"})
        tmp = d / f"p{i:05d}.part"
        with gzip.open(tmp, "wt") as fh:
            json.dump(r["features"], fh)
        tmp.rename(d / f"p{i:05d}.json.gz")
        return len(r["features"])
    n = 0
    with ThreadPoolExecutor(3) as ex:
        for j, k in enumerate(ex.map(one, todo)):
            n += k
            if j % 10 == 9:
                log(f"  {county}: {j + 1}/{len(todo)} pages, {n} points")


def download_window(name, bbox):
    """Points of an envelope (lon0, lat0, lon1, lat1), paged by offset -> centroids_<name>/ (validation windows)."""
    d = CACHE / f"centroids_{name}"
    d.mkdir(parents=True, exist_ok=True)
    k = 0
    while True:
        f = d / f"p{k:05d}.json.gz"
        if not f.exists():
            r = post({"geometry": ",".join(map(str, bbox)), "geometryType": "esriGeometryEnvelope", "inSR": 4326, "spatialRel": "esriSpatialRelIntersects",
                      "orderByFields": "OBJECTID", "resultOffset": k * PAGE, "resultRecordCount": PAGE, "outFields": FIELDS, "outSR": 4326,
                      "geometryPrecision": 6, "f": "json"})
            with gzip.open(f, "wt") as fh:
                json.dump(r["features"], fh)
            more = r.get("exceededTransferLimit")
            if not more:
                return
        k += 1


# ---------------------------------------------------------------------------------------------
# reading and matching the points

UTM = "EPSG:32618"


def read_points(name):
    import glob

    import numpy as np
    import pandas as pd
    from pyproj import Transformer
    rows = []
    for f in sorted(glob.glob(str(CACHE / f"centroids_{name}" / "p*.json.gz"))):
        with gzip.open(f, "rt") as fh:
            for ft in json.load(fh):
                a = ft["attributes"]
                g = ft.get("geometry") or {}
                a["lon"], a["lat"] = g.get("x"), g.get("y")
                rows.append(a)
    p = pd.DataFrame(rows).drop_duplicates("OBJECTID")
    p = p.dropna(subset=["lon", "lat"]).reset_index(drop=True)
    x, y = Transformer.from_crs(4326, UTM, always_xy=True).transform(p.lon.values, p.lat.values)
    p["x"], p["y"] = x, y
    yb = pd.to_numeric(p.YR_BLT, errors="coerce")
    p["yr"] = yb.where((yb >= 1650) & (yb <= 2026))
    ac = pd.to_numeric(p.ACRES, errors="coerce").fillna(0.25).clip(0.02, 500)
    p["rad"] = (0.8 * np.sqrt(ac * 4046.9) + 10).clip(25, 200)   # how far a building may stand from its parcel's point
    return p


def match(p, lon, lat, mode="nearest"):
    """Index of the point each footprint belongs to (-1: none). mode 'nearest': the nearest point whose radius reaches the
    footprint; 'dated': the nearest such point that carries a year, if there is one within the radius, else the nearest."""
    import numpy as np
    from pyproj import Transformer
    from scipy.spatial import cKDTree
    fx, fy = Transformer.from_crs(4326, UTM, always_xy=True).transform(lon, lat)
    tree = cKDTree(np.c_[p.x.values, p.y.values])
    d, i = tree.query(np.c_[fx, fy], k=5, distance_upper_bound=200)
    n = len(p)
    ok = np.isfinite(d)
    ii = np.where(ok, i, 0)
    reach = ok & (d <= p.rad.values[ii])
    hasyr = p.yr.notna().values[ii]
    out = np.full(len(fx), -1)
    for k in range(4, -1, -1):
        sel = reach[:, k] & (hasyr[:, k] if mode == "dated" else True)
        out = np.where(sel, ii[:, k], out)
    if mode == "dated":   # nothing dated in reach: the nearest point at all
        for k in range(4, -1, -1):
            out = np.where((out < 0) & reach[:, k], ii[:, k], out)
    return out


# ---------------------------------------------------------------------------------------------
# recorded years from the points (Dutchess)

OUTDIR = None


def backup(name):
    """The county file and its estimates as they were before this stage (the base of every re-run)."""
    import shutil
    from common import INTERIM
    d = INTERIM / "county_years"
    d.mkdir(parents=True, exist_ok=True)
    out = INTERIM / "counties"
    for suf in ("", "_estimates"):
        src, bak = out / f"{name}{suf}.parquet", d / f"orig_{name}{suf}.parquet"
        if not bak.exists() and src.exists():
            shutil.copy(src, bak)
    return d / f"orig_{name}.parquet"


def apply_points(county, source_tag="nys_centroids_2025"):
    import geopandas as gpd
    import numpy as np
    import pandas as pd

    import counties_ny as cn
    from common import INTERIM
    name = f"ny_{county}"
    base = gpd.read_parquet(backup(name))
    p = read_points(county)
    log(f"{county}: {len(p)} points, {int(p.yr.notna().sum())} with a year; {len(base)} footprints")
    m = match(p, base.lon.values, base.lat.values, "nearest")
    has = m >= 0
    mi = np.maximum(m, 0)
    year = np.where(has, p.yr.values[mi], np.nan)
    cls = np.where(has, p.PROP_CLASS.fillna("").astype(str).values[mi], "")
    pid = np.where(has, (p.SWIS.fillna("").astype(str) + " " + p.PRINT_KEY.fillna("").astype(str)).values[mi], "")
    # the main building of a parcel point = its largest outline
    area = base.area_m2.values
    o = pd.DataFrame({"s": np.where(has, m, -1), "a": area}).sort_values(["s", "a"], ascending=[True, False])
    first = o[o.s >= 0].drop_duplicates("s").index
    secondary = has.copy()
    secondary[first] = False
    n_on = pd.Series(np.where(has, m, -1 - np.arange(len(m)))).map(pd.Series(m[has]).value_counts()).fillna(0).astype(int).values
    cnum = pd.to_numeric(pd.Series(cls).str[:3], errors="coerce").values
    kind = np.where((cnum >= 200) & (cnum < 300), "homes", "other")
    unit = base.town.fillna("").values
    main_year = np.where(secondary, np.nan, year)
    x, y = base.geometry.representative_point().x.values, base.geometry.representative_point().y.values
    from pyproj import Transformer
    ux, uy = Transformer.from_crs(4326, UTM, always_xy=True).transform(x, y)
    heap_rows = []
    for k, need in (("homes", cn.heap_min), ("other", cn.heap_min_other)):
        my = np.where(kind == k, main_year, np.nan)
        heap_rows += cn.heap_evidence(cn.find_heaps(my, unit, need), my, unit, ux, uy, k)
    heap = np.zeros(len(base), bool)
    for r in heap_rows:
        if r["heap"]:
            heap |= (unit == r["town"]) & (kind == r["kind"]) & (year == r["year"])
    mm = pd.DataFrame({"muni": base.muni.fillna("").values, "ok": np.isfinite(year)})[(kind == "homes") & ~secondary]
    share = mm.groupby("muni").ok.mean()
    out = base.copy()
    out["year_raw"] = year
    out["year_src"] = np.where(np.isfinite(year), source_tag, "")
    out["heap"] = heap
    out["secondary"] = secondary
    out["prop_class"] = cls
    out["use"] = np.array([cn.use_of(c) for c in cls], dtype=np.int8)
    out["muni_year_share"] = base.muni.fillna("").map(share).fillna(0.0).round(3).values
    out["parcel"] = pid
    out["n_on_parcel"] = n_on
    f = INTERIM / "counties" / f"{name}.parquet"
    out.to_parquet(f.with_suffix(".part"), index=False)
    f.with_suffix(".part").rename(f)
    log(f"{county}: {int(np.isfinite(year).sum())} footprints with a recorded year ({np.isfinite(year).mean():.1%}), "
        f"{int(heap.sum())} on placeholder years, {int(secondary.sum())} secondary")
    rep = {"county": county, "footprints": len(out), "points": len(p), "points_with_year": int(p.yr.notna().sum()),
           "matched": int(has.sum()), "with_year": int(np.isfinite(year).sum()), "on_heap": int(heap.sum()),
           "heaps": [r for r in heap_rows if r["heap"]],
           "top_years": {int(k): int(v) for k, v in pd.Series(year[np.isfinite(year)]).value_counts().head(10).items()}}
    (INTERIM / "county_years" / f"{county}_apply_report.json").write_text(json.dumps(rep, indent=1, default=str))
    return out


# ---------------------------------------------------------------------------------------------
# HISDAC-US BUPR: the count of dated property records per 250 m cell and five-year step (cumulative)

EPOCHS = None
MIN_REC = 12        # dated records a cell (or its 3 x 3 block) needs before its own curve is used
GATE_LO, GATE_HI = 0.4, 2.5   # records per main building: outside, the cell's counts do not describe its buildings
COMPLETE = 0.75     # dated records / all records of the block (HISDAC's own completeness): below it the census model stays


def bupr():
    import numpy as np
    import rasterio.transform as rt
    from common import INTERIM
    z = np.load(INTERIM / "county_years" / "bupr_window.npz")
    names = [str(n) for n in z["names"]]
    k = [i for i, n in enumerate(names) if n.isdigit()]
    A = z["A"].astype(np.float32)
    A[A >= 65535] = 0
    return A[k], [int(names[i]) for i in k], A[names.index("contemporary")], rt.Affine(*z["transform"])


def outbuildings(df, small=60.0, ratio=1.8, reach=35.0):
    """Footprints without a parcel: a small one near a clearly larger one is its outbuilding. -> main id per row (own id for mains)."""
    import numpy as np
    from pyproj import Transformer
    from scipy.spatial import cKDTree
    x, y = Transformer.from_crs(4326, UTM, always_xy=True).transform(df.lon.values, df.lat.values)
    a = df.area_m2.values
    main = df.id.values.astype(object).copy()
    cand = np.flatnonzero(df.parcel.values == "")
    t = cKDTree(np.c_[x[cand], y[cand]])
    sm = cand[a[cand] < small]
    nb = t.query_ball_point(np.c_[x[sm], y[sm]], reach)
    ids = df.id.values
    for i, lst in zip(sm, nb):
        best, ba = None, 0
        for j in lst:
            c = cand[j]
            if a[c] >= ratio * a[i] and a[c] >= small and a[c] > ba:
                best, ba = c, a[c]
        if best is not None:
            main[i] = ids[best]
    return main


def cells_assign(df, is_main, new, order_key):
    """Years from the cell curves for the main buildings `is_main` (not `new`), ordered by order_key inside a cell."""
    import numpy as np
    import pandas as pd
    from pyproj import Transformer
    A, ep, contemp, tr = bupr()
    cum = A                                # (epochs, rows, cols)
    D = cum[-1]
    Cc = contemp
    t = Transformer.from_crs(4326, "ESRI:102039", always_xy=True)
    ax, ay = t.transform(df.lon.values, df.lat.values)
    col = np.floor((ax - tr.c) / tr.a).astype(int)
    row = np.floor((ay - tr.f) / tr.e).astype(int)
    H, W = D.shape
    inside = (row >= 1) & (row < H - 1) & (col >= 1) & (col < W - 1)
    cand = is_main & inside & ~new
    cell = np.where(cand, row * W + col, -1)
    m_in = pd.Series(1, index=np.flatnonzero(cand)).groupby(cell[cand]).sum()
    # curves: own cell, else 3 x 3
    def blk(a, r, c):
        return a[..., r - 1:r + 2, c - 1:c + 2].sum(axis=(-1, -2))
    res_year = np.full(len(df), np.nan)
    res_basis = np.full(len(df), "", object)
    res_lo = np.zeros(len(df), int)
    res_hi = np.zeros(len(df), int)
    stats = {"cells": 0, "own": 0, "pooled": 0, "gated_out": 0, "incomplete": 0, "too_few": 0}
    edges = np.array([ep[0] - 60] + ep)         # 1750 = the lump built by 1810
    ci = pd.Series(np.flatnonzero(cand)).groupby(cell[cand])
    for cid, ixs in ci:
        r, c = divmod(int(cid), W)
        ix = ixs.values
        stats["cells"] += 1
        curve, d15, c15 = cum[:, r, c], D[r, c], Cc[r, c]
        kind = "own"
        if d15 < MIN_REC:
            curve, d15, c15 = blk(cum, r, c), blk(D, r, c), blk(Cc, r, c)
            kind = "pooled"
        if d15 < MIN_REC:
            stats["too_few"] += 1
            continue
        if c15 > 0 and d15 / c15 < COMPLETE:
            stats["incomplete"] += 1
            continue
        mb = len(ix) if kind == "own" else sum(m_in.get(r2 * W + c2, 0) for r2 in (r - 1, r, r + 1) for c2 in (c - 1, c, c + 1))
        if not (GATE_LO <= d15 / max(mb, 1) <= GATE_HI):
            stats["gated_out"] += 1
            continue
        stats[kind] += 1
        F = np.r_[0.0, curve / curve[-1]]       # F at edges (1750, 1810, 1815 ... 2015)
        o = np.argsort(order_key[ix], kind="stable")
        u = (np.arange(len(ix)) + 0.5) / len(ix)
        k = np.clip(np.searchsorted(F, u, side="left") - 1, 0, len(F) - 2)
        lo_f, hi_f = F[k], F[k + 1]
        frac = np.clip((u - lo_f) / np.maximum(hi_f - lo_f, 1e-9), 0, 0.9999)
        span = edges[k + 1] - edges[k]
        yr = edges[k] + 1 + np.floor(frac * span)
        yr = np.where(k == 0, edges[1] - np.floor((1 - frac) * 60), yr)
        res_year[ix[o]] = yr
        res_lo[ix[o]] = np.where(k == 0, 1750, edges[k] + 1)
        res_hi[ix[o]] = edges[k + 1]
        res_basis[ix[o]] = [f"hisdac_bupr:{int(e)}" for e in edges[k + 1]]
    return res_year, res_lo, res_hi, res_basis, stats


def hisdac(county):
    import geopandas as gpd
    import numpy as np
    import pandas as pd
    from pyproj import Transformer
    from common import INTERIM
    name = f"ny_{county}"
    bak = backup(name)
    cur = INTERIM / "counties" / f"{name}_estimates.parquet"
    if "bupr_cell" not in set(pd.read_parquet(cur, columns=["order"])["order"]):   # estimates rebuilt by counties_ny_estimates: the new base
        import shutil
        shutil.copy(cur, INTERIM / "county_years" / f"orig_{name}_estimates.parquet")
    cols = ["id", "muni", "town", "year_raw", "parcel", "secondary", "area_m2", "lon", "lat"]
    base = pd.read_parquet(bak, columns=cols)
    est0 = pd.read_parquet(INTERIM / "county_years" / f"orig_{name}_estimates.parquet")
    df = base.merge(est0[["id", "year_est", "basis"]], on="id", how="inner")
    log(f"{county}: {len(df)} footprints with a modelled year")
    main_id = outbuildings(df)
    is_main = main_id == df.id.values
    is_main &= ~df.basis.str.contains("outbuilding", regex=False).values
    h = (pd.util.hash_array(df.id.astype(str).values) % 10_000) / 10_000.0
    new = df.year_est.values >= 2016   # the model's own post-2015 buildings: HISDAC (compiled 2016) cannot see them
    res_year, res_lo, res_hi, res_basis, stats = cells_assign(df, is_main, new, df.year_est.values + h * 0.99)
    got = np.isfinite(res_year)
    # outbuildings follow their main
    mp = pd.Series(np.flatnonzero(got), index=df.id.values[got])
    follow = (~is_main) & pd.Series(main_id).isin(mp.index).values
    src = mp.reindex(main_id[follow]).values.astype(int)
    res_year[np.flatnonzero(follow)] = res_year[src]
    res_lo[np.flatnonzero(follow)] = res_lo[src]
    res_hi[np.flatnonzero(follow)] = res_hi[src]
    res_basis[np.flatnonzero(follow)] = np.array([b + "+outbuilding_of_main" for b in res_basis[src]], object)
    # suffolk's parcel-bound outbuildings (basis has outbuilding_of_main, main on the parcel): follow the parcel's main
    pm = df.basis.str.contains("outbuilding", regex=False).values & ~got
    if pm.any():
        pid = df.parcel.values
        mains_by_parcel = pd.Series(np.flatnonzero(got & is_main), index=pid[got & is_main])
        mains_by_parcel = mains_by_parcel[mains_by_parcel.index != ""]
        mains_by_parcel = mains_by_parcel[~mains_by_parcel.index.duplicated()]
        s2 = mains_by_parcel.reindex(pid[pm]).values
        ok = np.isfinite(s2)
        tgt = np.flatnonzero(pm)[ok]
        sidx = s2[ok].astype(int)
        res_year[tgt], res_lo[tgt], res_hi[tgt] = res_year[sidx], res_lo[sidx], res_hi[sidx]
        res_basis[tgt] = np.array([b + "+outbuilding_of_main" for b in res_basis[sidx]], object)
    got = np.isfinite(res_year)
    log(f"{county}: {stats}; {int(got.sum())} of {len(df)} footprints take a year from the cell curves")
    out = est0.copy()
    p = pd.Series(np.arange(len(out)), index=out.id.values).reindex(df.id.values[got]).values.astype(int)
    for col, v in (("year_est", res_year[got]), ("year_lo", res_lo[got]), ("year_hi", res_hi[got])):
        a_ = out[col].values.astype(np.int32)
        a_[p] = v.astype(np.int32)
        out[col] = a_
    bs = out.basis.values.astype(object)
    bs[p] = res_basis[got]
    out["basis"] = bs
    od = out["order"].values.astype(object)
    od[p] = "bupr_cell"
    out["order"] = od
    out["year_est"] = out.year_est.astype("int16")
    out[["year_lo", "year_hi"]] = out[["year_lo", "year_hi"]].astype("int16")
    f = INTERIM / "counties" / f"{name}_estimates.parquet"
    out.to_parquet(f.with_suffix(".part"), index=False)
    f.with_suffix(".part").rename(f)
    json.dump({"county": county, **stats, "taken": int(got.sum()), "of": len(df), "mains": int(is_main.sum())},
              open(INTERIM / "county_years" / f"{county}_hisdac_report.json", "w"), indent=1)
    return out


def validate():
    """Where the assessor's year is known: the cell curves against the census model (counties_ny_estimates, years hidden), the
    same ordering inside a cell. Truth = main buildings, placeholder years excluded."""
    import numpy as np
    import pandas as pd
    from common import INTERIM
    rows = pd.read_parquet(INTERIM / "counties_ny_est" / "validation_rows.parquet")
    bc = INTERIM / "counties"
    cols = ["id", "muni", "year_raw", "heap", "secondary", "area_m2", "lon", "lat"]
    res = {}
    wc = pd.read_parquet(bc / "ny_westchester.parquet", columns=cols)
    VALID = ["Yonkers", "White Plains", "Scarsdale", "Rye", "Somers", "Harrison", "New Castle", "Pelham"]
    out = []
    for m in VALID:
        sel = (wc.muni == m) & wc.year_raw.notna() & ~wc.secondary
        r = rows[rows.muni == m]
        if sel.sum() != len(r):
            log(f"{m}: validation rows do not line up ({sel.sum()} vs {len(r)}); skipped")
            continue
        d = wc[wc.muni == m].copy()
        d["parcel"] = ""
        d["basis"] = ""
        d["year_est"] = np.nan
        d.loc[sel[sel].index, "year_est"] = r.est.values
        d = d[~d.secondary].reset_index(drop=True)
        d = d[d.year_est.notna()].reset_index(drop=True)
        truth = d.year_raw.values
        ok = ~d.heap.values
        rng = np.random.default_rng(7)
        h = (pd.util.hash_array(d.id.astype(str).values) % 10_000) / 10_000.0
        for name, key in (("census_order", d.year_est.values + h * .99), ("random_order", rng.random(len(d))), ("oracle_order", truth + h * .99)):
            ry, _, _, _, st = cells_assign(d, np.ones(len(d), bool), np.zeros(len(d), bool), key)
            g = np.isfinite(ry) & ok
            out.append(pd.DataFrame({"muni": m, "variant": name, "true": truth[g], "cell": ry[g], "census": d.year_est.values[g]}))
    V = pd.concat(out)

    def stat(a, b):
        e = np.abs(a - b)
        return {"n": int(len(e)), "median_abs_error": float(np.median(e)), "within_10": round(float((e <= 10).mean()), 3),
                "within_5": round(float((e <= 5).mean()), 3), "same_decade": round(float((a // 10 == b // 10).mean()), 3)}
    for name, g in V.groupby("variant"):
        res[name] = {"cell_curve": stat(g.true.values, g.cell.values)}
        if name == "census_order":
            res[name]["census_model_same_buildings"] = stat(g.true.values, g.census.values)
            res[name]["by_town"] = {m: {"cell_curve": stat(x.true.values, x.cell.values)["median_abs_error"],
                                        "census_model": stat(x.true.values, x.census.values)["median_abs_error"], "n": len(x)}
                                    for m, x in g.groupby("muni")}
    # counties with a recorded year everywhere: random and oracle order only
    for c in ("rockland", "orange", "putnam"):
        d = pd.read_parquet(bc / f"ny_{c}.parquet", columns=cols)
        d = d[~d.secondary & d.year_raw.notna()].reset_index(drop=True)
        d["parcel"] = ""
        d["year_est"] = 0.0
        d["basis"] = ""
        h = (pd.util.hash_array(d.id.astype(str).values) % 10_000) / 10_000.0
        ok = ~d.heap.values
        for name, key in (("random_order", np.random.default_rng(3).random(len(d))), ("oracle_order", d.year_raw.values + h * .99)):
            ry, _, _, _, st = cells_assign(d, np.ones(len(d), bool), np.zeros(len(d), bool), key)
            g = np.isfinite(ry) & ok
            res.setdefault(c, {})[name] = {**stat(d.year_raw.values[g], ry[g]), "share_with_cell_year": round(float(np.isfinite(ry).mean()), 3), **st}
    (INTERIM / "county_years" / "validation.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


def main(argv):
    if argv and argv[0] == "window":
        download_window(argv[1], [float(v) for v in argv[2:6]])
    elif argv and argv[0] == "apply":
        for c in argv[1:]:
            apply_points(c)
    elif argv and argv[0] == "hisdac":
        for c in argv[1:]:
            hisdac(c)
    elif argv and argv[0] == "validate":
        validate()
    elif argv and argv[0] == "download":
        for c in argv[1:]:
            download(c)


if __name__ == "__main__":
    main(sys.argv[1:])
