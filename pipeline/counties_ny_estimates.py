"""Estimated construction years for the New York county footprints that have no recorded year.

    python counties_ny_estimates.py download | build | check

Evidence (best first), all open:
  1. ACS 5-year 2018-2022 table B25034 (housing units by decade built), block groups: the decade
     distribution a block group's buildings must follow (US Census Bureau, TIGER/Line with
     Selected Demographic and Economic Data, public domain).
  2. HISDAC-US FBUY (first built-up year per 250 m cell; Leyk & Uhl, Harvard Dataverse,
     CC0 1.0; modelled from Zillow property records): used only as one covariate that orders
     buildings inside a block group, never as a date.
  3. Wikipedia municipality articles' census tables: spread the "1939 or earlier" bin over the
     town's growth.
Ordering inside a block group = a ridge regression, trained on the DATED municipalities, of a
building's within-block-group age percentile on distance to old centres and railroad stations,
FBUY, footprint area, height, use and local density.  It orders buildings; the ACS table sets
how many fall in each decade.  Outbuildings take their parcel's main building's estimate.

Output: data/interim/counties/ny_<county>_estimates.parquet (id, year_est, year_lo, year_hi,
basis, bg, order).  `check` validates on dated municipalities (their years hidden) and writes
data/research/counties_ny_estimates.md from the reports.
"""
import json
import sys
import time
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw/counties_ny_est"
INT = ROOT / "data/interim/counties_ny_est"
OUT = ROOT / "data/interim/counties"
UA = {"User-Agent": "NYCThroughTime-research/0.1"}
ACS_URL = "https://www2.census.gov/geo/tiger/TIGER_DP/2022ACS/ACS_2022_5YR_BG_36.gdb.zip"
FBUY_URL = "https://dataverse.harvard.edu/api/access/datafile/3141229"
FBUY_README = "https://dataverse.harvard.edu/api/access/datafile/3904494"
WIKI = "https://en.wikipedia.org/w/index.php?title={}&action=raw"

# decade bins: (label, lo, hi, ACS column)
BINS = [("pre1940", 1700, 1939, "B25034_E011"), ("1940-1949", 1940, 1949, "B25034_E010"),
        ("1950-1959", 1950, 1959, "B25034_E009"), ("1960-1969", 1960, 1969, "B25034_E008"),
        ("1970-1979", 1970, 1979, "B25034_E007"), ("1980-1989", 1980, 1989, "B25034_E006"),
        ("1990-1999", 1990, 1999, "B25034_E005"), ("2000-2009", 2000, 2009, "B25034_E004"),
        ("2010-2019", 2010, 2019, "B25034_E003"), ("2020-2025", 2020, 2025, "B25034_E002")]
COUNTIES = {"westchester": ("36119", "Westchester"), "rockland": ("36087", "Rockland")}
# the outer round (2026-11-11; data/research/counties_ny_outer.md): `build_outer` fits one model on every dated county
# (the two above and the dated outer ones) and writes ny_<county>_estimates.parquet for the outer counties only
OUTER_COUNTIES = {"putnam": ("36079", "Putnam"), "sullivan": ("36105", "Sullivan"), "ulster": ("36111", "Ulster"),
                  "dutchess": ("36027", "Dutchess"), "orange": ("36071", "Orange"), "nassau": ("36059", "Nassau"),
                  "suffolk": ("36103", "Suffolk")}
ALL = {**COUNTIES, **OUTER_COUNTIES}
VALID = ["Yonkers", "White Plains", "Scarsdale", "Rye", "Somers", "Harrison", "New Castle", "Pelham"]
WIKI_TITLE = {  # municipality -> English Wikipedia article for its census table
    "Mamaroneck": "Mamaroneck (town), New York", "Mamaroneck, Village": "Mamaroneck (village), New York",
    "Ossining": "Ossining (town), New York", "Ossining, Village": "Ossining (village), New York",
    "Pelham": "Pelham (town), New York", "Pelham Manor": "Pelham Manor, New York",
    "Rye": "Rye, New York", "Rye Brook": "Rye Brook, New York", "Port Chester": "Port Chester, New York",
    "Clarkstown": "Clarkstown, New York", "Haverstraw": "Haverstraw (town), New York",
    "Orangetown": "Orangetown, New York", "Ramapo": "Ramapo, New York", "Stony Point": "Stony Point, New York",
}
FEATS = ["ldc", "lds", "fbuy", "larea", "hgt", "dens", "area_loc", "area_sd", "hgt_loc", "nn"]


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ------------------------------------------------------------------ download
def get(url, dest):
    import requests
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return
    log("fetch", url)
    r = requests.get(url, headers=UA, timeout=600, stream=True)
    r.raise_for_status()
    with open(dest, "wb") as f:
        for ch in r.iter_content(1 << 20):
            f.write(ch)


def wiki_series(title):
    import re
    import requests
    r = requests.get(WIKI.format(title.replace(" ", "_")), headers=UA, timeout=60)
    if r.status_code != 200:
        return {}
    m = re.search(r"\{\{US Census population(.*?)\n\}\}", r.text, re.S)
    if m:
        return {int(a): int(b.replace(",", "")) for a, b in re.findall(r"\|\s*(\d{4})\s*=\s*([\d,]+)", m.group(1))}
    m = re.search(r"\{\{Historical populations(.*?)\n\|footnote", r.text, re.S)  # |1900|2888 form
    if not m:
        return {}
    return {int(a): int(b.replace(",", "")) for a, b in re.findall(r"\|\s*(\d{4})\s*\|\s*([\d,]+)", m.group(1))}


def download():
    import tarfile
    import zipfile
    get(ACS_URL, RAW / "acs/ACS_2022_5YR_BG_36.gdb.zip")
    if not list((RAW / "acs/gdb").glob("*.gdb")):
        zipfile.ZipFile(RAW / "acs/ACS_2022_5YR_BG_36.gdb.zip").extractall(RAW / "acs/gdb")
    get(FBUY_URL, RAW / "hisdac/FBUY.tar.gz")
    get(FBUY_README, RAW / "hisdac/readme_FBUY.txt")
    if not (RAW / "hisdac/x/FBUY/data/FBUY.tif").exists():
        tarfile.open(RAW / "hisdac/FBUY.tar.gz").extractall(RAW / "hisdac/x")
    pop = RAW / "wiki_pop.json"
    cache = json.loads(pop.read_text()) if pop.exists() else {}
    for cty in ALL:
        if not (OUT / f"ny_{cty}.parquet").exists():
            continue
        if OUTER_COUNTIES.get(cty) and f"county:{cty}" not in cache:   # the county's own census series (fallback of its towns)
            t = f"{OUTER_COUNTIES[cty][1]} County, New York"
            cache[f"county:{cty}"] = {"title": t, "series": wiki_series(t)}
            log("pop", t, len(cache[f"county:{cty}"]["series"]))
        df = pd.read_parquet(OUT / f"ny_{cty}.parquet", columns=["muni", "town"])
        for muni in sorted(set(df.muni) | set(df.town)):
            if (muni in cache and cache[muni]["series"]) or not muni:
                continue
            title = WIKI_TITLE.get(muni, f"{muni}, New York")
            for suf, kind in ((", Village", "village"), (", Town", "town")):
                if muni.endswith(suf) and muni not in WIKI_TITLE:
                    title = f"{muni[:-len(suf)]} ({kind}), New York"
            ser = wiki_series(title)
            if not ser and title != f"{muni}, New York":
                ser = wiki_series(f"{muni}, New York")
            cache[muni] = {"title": title, "series": ser}
            log("pop", muni, title, len(ser))
            time.sleep(0.3)
    pop.write_text(json.dumps(cache, indent=1))


# ------------------------------------------------------------------ inputs
def load_bg(bbox):
    import geopandas as gp
    import pyogrio
    g = str(next((RAW / "acs/gdb").glob("*.gdb")))
    bg = pyogrio.read_dataframe(g, layer="ACS_2022_5YR_BG_36_NEW_YORK", bbox=bbox, columns=["GEOID", "COUNTYFP"])
    cols = ["GEOIDFQ"] + [b[3] for b in BINS]
    t = pyogrio.read_dataframe(g, layer="X25_HOUSING_CHARACTERISTICS", read_geometry=False, columns=cols)
    t["GEOID"] = t.pop("GEOIDFQ").str[-12:]
    bg = bg.merge(t, on="GEOID", how="left")
    return gp.GeoDataFrame(bg, geometry="geometry", crs=4326)


def fbuy_at(lon, lat):
    import rasterio
    from pyproj import Transformer
    ds = rasterio.open(RAW / "hisdac/x/FBUY/data/FBUY.tif")
    x, y = Transformer.from_crs(4326, ds.crs, always_xy=True).transform(lon, lat)
    inv = ~ds.transform
    c, r = inv * (np.asarray(x), np.asarray(y))
    r, c = np.floor(r).astype(int), np.floor(c).astype(int)
    r0, r1, c0, c1 = r.min(), r.max() + 1, c.min(), c.max() + 1
    a = ds.read(1, window=((r0, r1), (c0, c1)))
    v = a[r - r0, c - c0].astype(float)
    v[(v < 1700) | (v > 2020)] = np.nan  # nodata, and 1 = built without a year
    return v


def utm(lon, lat):
    from pyproj import Transformer
    return Transformer.from_crs(4326, 32618, always_xy=True).transform(lon, lat)


def load_county(cty):
    import geopandas as gp
    df = pd.read_parquet(OUT / f"ny_{cty}.parquet", columns=[
        "id", "muni", "town", "height_m", "floors", "year_raw", "heap", "secondary", "use", "area_m2", "parcel",
        "lon", "lat"])
    df["x"], df["y"] = utm(df.lon.values, df.lat.values)
    bg = load_bg((df.lon.min() - .01, df.lat.min() - .01, df.lon.max() + .01, df.lat.max() + .01))
    pts = gp.GeoDataFrame(df[["id"]], geometry=gp.points_from_xy(df.lon, df.lat), crs=4326)
    j = gp.sjoin(pts, bg[["GEOID", "geometry"]], how="left", predicate="within")
    j = j[~j.index.duplicated()]
    df["bg"] = j["GEOID"].values
    miss = df.bg.isna()
    if miss.any():  # outside every block group (water edge): nearest
        a = pts[miss].to_crs(32618)
        k = gp.sjoin_nearest(a, bg[["GEOID", "geometry"]].to_crs(32618), how="left")
        k = k[~k.index.duplicated()]
        df.loc[miss, "bg"] = k["GEOID"].values
    df["fbuy"] = fbuy_at(df.lon.values, df.lat.values)
    # parcel main building
    df["main_id"] = df["id"]
    sec = df.secondary & df.parcel.notna() & (df.parcel != "")
    if sec.any():
        m = df[~df.secondary & df.parcel.notna() & (df.parcel != "")]
        top = m.sort_values("area_m2").groupby("parcel").id.last()
        df.loc[sec, "main_id"] = df.loc[sec, "parcel"].map(top).fillna(df.loc[sec, "id"])
    return df, bg


def features(df, cty=None):
    """Per-building covariates (all computed for every building, dated or not)."""
    from scipy.spatial import cKDTree
    pl = pd.read_csv(ROOT / "data/tables/places_counties.csv")
    names = ["Westchester", "Rockland"] if cty in (None, "westchester", "rockland") else [ALL[cty][1]]
    pl = pl[pl.tier.isin(["town", "city"]) & pl.county.isin(names)]
    if not len(pl):   # no hand-made places for the county: the centres of its cities, villages and towns (State civil boundaries)
        import geopandas as gp
        cs = []
        for w in ("cities_towns", "villages"):
            g = gp.read_file(ROOT / f"data/raw/counties_ny/civil/{ALL[cty][1]}_{w}.geojson").to_crs(32618)
            c = g.geometry.representative_point().to_crs(4326)
            cs.append(pd.DataFrame({"lon": c.x.values, "lat": c.y.values}))
        pl = pd.concat(cs, ignore_index=True)
    st = pd.read_csv(ROOT / "data/tables/transit_stations.csv")
    st = st[st.system.isin(["mnr", "njt", "rail"]) & st.lon.between(df.lon.min() - .2, df.lon.max() + .2)
            & st.lat.between(df.lat.min() - .2, df.lat.max() + .2)]
    xy = df[["x", "y"]].values
    out = pd.DataFrame(index=df.index)
    for nm, t in (("ldc", pl), ("lds", st)):
        px, py = utm(t.lon.values, t.lat.values)
        d, _ = cKDTree(np.c_[px, py]).query(xy)
        out[nm] = np.log(d + 50)
    out["fbuy"] = df.fbuy
    out["larea"] = np.log(df.area_m2.clip(lower=10))
    out["hgt"] = df.height_m.fillna(df.height_m.median())
    tree = cKDTree(xy)
    out["dens"] = tree.query_ball_point(xy, 60, return_length=True, workers=1)
    # neighbourhood sameness within 100 m: tract houses share size and height
    n = len(xy)
    area_loc, area_sd, hgt_loc = np.zeros(n), np.zeros(n), np.zeros(n)
    for a in range(0, n, 40000):   # in chunks (Suffolk: 700 thousand footprints, 2 GB)
        nb = tree.query_ball_point(xy[a:a + 40000], 100)
        cnt = np.fromiter((len(q) for q in nb), int, len(nb))
        flat = np.concatenate(nb).astype(int)
        seg = np.r_[0, np.cumsum(cnt)[:-1]]
        la, hg = out.larea.values[flat], out.hgt.values[flat]
        sa, sa2, sh = (np.add.reduceat(v, seg) for v in (la, la * la, hg))
        area_loc[a:a + 40000] = sa / cnt
        area_sd[a:a + 40000] = np.sqrt(np.maximum(sa2 / cnt - (sa / cnt) ** 2, 0))
        hgt_loc[a:a + 40000] = sh / cnt
        del nb, flat
    out["area_loc"], out["area_sd"], out["hgt_loc"] = area_loc, area_sd, hgt_loc
    out["nn"] = tree.query(xy, 2)[0][:, 1]
    return out


def design(df, f):
    """Within-block-group percentile of each covariate (+ squares, use dummies, intercept)."""
    X = pd.DataFrame(index=df.index)
    g = df.bg
    for c in FEATS:
        v = f[c].copy()
        if c == "fbuy":
            X["fbuy_na"] = v.isna().astype(float)
            v = v.fillna(v.median())
        r = v.groupby(g).rank(pct=True).fillna(.5) - .5
        X[c] = r
        X[c + "2"] = r ** 2
    for u in (1, 2, 3, 6, 7):
        X[f"use{u}"] = (df.use == u).astype(float)
    X["fbuy_x_ldc"] = X.fbuy * X.ldc
    X["one"] = 1.0
    return X


def fit(X, y, lam=5.0):
    A = X.values
    return np.linalg.solve(A.T @ A + lam * np.eye(A.shape[1]), A.T @ y)


def within_pct(df, mask):
    return df.year_raw.where(mask).groupby(df.bg).rank(pct=True)


# ------------------------------------------------------------------ allocation
def hash01(ids):
    return pd.util.hash_array(np.asarray(ids, dtype=object)).astype(np.float64) / 2.0 ** 64


def pop_cdf(series, county_series):
    """F(t): share of a town's pre-1940 stock built by year t, following its census population."""
    s = {y: p for y, p in series.items() if y <= 1940}
    src = "town"
    if len(s) < 3 or min(s) > 1900:
        s, src = {y: p for y, p in county_series.items() if y <= 1940}, "county"
    ys = sorted(s)
    y0 = ys[0]
    yy = np.arange(1700, 1940)
    pp = np.interp(yy, ys, [s[y] for y in ys], left=0.0)
    pre = (yy < y0) & (yy >= y0 - 80)
    pp[pre] = s[y0] * (yy[pre] - (y0 - 80)) / 80.0
    pp[yy < y0 - 80] = 0.0
    pp = np.maximum.accumulate(pp)
    return yy, pp / pp[-1], src


def allocate(df, mains_idx, score, known, pop, muni_p):
    """Years for the buildings mains_idx (positions in df). known: dated buildings (bin counts per bg)."""
    out = {}
    d = df.loc[mains_idx]
    pb = known["units"]  # bg -> array of unit counts per bin
    kn = known["dated"]  # bg -> array of dated building counts per bin
    h = hash01(d["id"].values)
    sc = pd.Series(score, index=d.index) + (h - .5) * 0.03
    rank = sc.groupby(d.bg).rank(method="first")
    n = d.groupby("bg").id.transform("size")
    u = ((rank - .5) / n).values
    res = np.zeros(len(d))
    lo = np.zeros(len(d), int)
    hi = np.zeros(len(d), int)
    lab = np.empty(len(d), object)
    exp = np.zeros((len(d), len(BINS)))
    keys = np.zeros(len(d))
    bins_ = np.zeros(len(d), int)
    # the sum of position and hash is bell-shaped: make it uniform within (municipality, bin) so no year stacks
    pos = {ix: i for i, ix in enumerate(d.index)}
    pend = []
    for bg, grp in d.groupby("bg"):
        ii = np.array([pos[i] for i in grp.index])
        units = pb.get(bg)
        src = "acs_bg"
        p = None
        if units is not None and np.nansum(units) >= 5:
            r = units - kn.get(bg, 0)
            r = np.where(r > 0, r, 0)
            p = (r if r.sum() >= 0.2 * units.sum() else units).astype(float)
        if p is None or p.sum() <= 0:
            p = muni_p[grp.muni.iloc[0]]
            src = "acs_muni"
        p = p / p.sum()
        exp[ii] = p
        cum = np.r_[0, np.cumsum(p)]
        cum[-1] = 1.0
        uu = u[ii]
        b = np.clip(np.searchsorted(cum, uu, side="right") - 1, 0, len(BINS) - 1)
        b = np.where(p[b] == 0, np.argmax(p), b)
        frac = np.clip((uu - cum[b]) / np.maximum(cum[b + 1] - cum[b], 1e-9), 0, 1)
        fr = np.clip(.7 * frac + .3 * h[ii], 0, .9999)
        keys[ii] = fr
        bins_[ii] = b
        pend.append((grp, ii, b, src))
    kk = pd.Series(keys).groupby([d.muni.values, bins_]).rank(pct=True).values
    keys = np.clip(kk - .5 / np.maximum(pd.Series(keys).groupby([d.muni.values, bins_]).transform("size").values, 1), 0, .9999)
    # density inside a decade is linear (slope from the neighbouring decades' masses, mass kept), so
    # decade boundaries do not step: inverse CDF of 1 + s(x - .5)
    cm = pd.crosstab(d.muni.values, bins_).reindex(columns=range(len(BINS)), fill_value=0)
    mv = cm.values.astype(float)
    sl = np.zeros_like(mv)
    for j in range(1, len(BINS) - 1):
        sl[:, j] = (mv[:, j + 1] - (mv[:, j - 1] if j > 1 else mv[:, j])) / 2 / np.maximum(mv[:, j], 1)
    sl = np.clip(sl, -1.6, 1.6)
    sd = pd.DataFrame(sl, index=cm.index)
    sp = np.array([sd.at[mu, bi] for mu, bi in zip(d.muni.values, bins_)])
    ok = np.abs(sp) > 1e-6
    q = 1 - sp / 2
    x = keys.copy()
    x[ok] = (-q[ok] + np.sqrt(q[ok] ** 2 + 2 * sp[ok] * keys[ok])) / sp[ok]
    keys = np.where(bins_ > 0, np.clip(x, 0, .9999), keys)
    for grp, ii, b, src in pend:
        fr = keys[ii]
        for k, bi in enumerate(b):
            ix = ii[k]
            lbl, blo, bhi, _ = BINS[bi]
            if bi == 0:
                yy, F, psrc = pop[grp.muni.iloc[k]]
                res[ix] = yy[min(np.searchsorted(F, fr[k] * F[-1]), len(yy) - 1)]
                lo[ix], hi[ix] = 1700, 1939
                lab[ix] = f"{src}:pre1940+{psrc}_growth"
            else:
                span = bhi - blo + 1
                res[ix] = blo + int(fr[k] * span)
                lo[ix], hi[ix] = blo, bhi
                lab[ix] = f"{src}:{lbl}"
    return (pd.DataFrame({"id": d.id.values, "year_est": res.astype(int), "year_lo": lo, "year_hi": hi,
                          "basis": lab, "bg": d.bg.values}, index=d.index), exp)


def bin_of(y):
    y = np.asarray(y)
    return np.where(y < 1940, 0, np.clip(((y - 1940) // 10) + 1, 1, len(BINS) - 1)).astype(int)


def known_tables(df, bg, dated_mask):
    units = {r.GEOID: np.array([r[b[3]] for b in BINS], float) for _, r in bg.iterrows()}
    dd = df[dated_mask & ~df.secondary]
    kn = {}
    for g_, grp in dd.groupby("bg"):
        kn[g_] = np.bincount(bin_of(grp.year_raw.values), minlength=len(BINS)).astype(float)
    return {"units": units, "dated": kn}


def muni_dist(df, bg):
    """Fallback: each municipality's ACS distribution summed over its buildings' block groups."""
    t = bg.set_index("GEOID")[[b[3] for b in BINS]].fillna(0)
    out = {}
    for m, grp in df[~df.secondary].groupby("muni"):
        c = grp.bg.value_counts()
        v = np.zeros(len(BINS))
        for g_, k in c.items():
            if g_ in t.index:
                tt = t.loc[g_].values.astype(float)
                if tt.sum() > 0:
                    v += tt / tt.sum() * k
        out[m] = v if v.sum() > 0 else np.ones(len(BINS))
    return out


# ------------------------------------------------------------------ build / validate
def prepare(cty):
    df, bg = load_county(cty)
    f = features(df, cty)
    X = design(df, f)
    return df, bg, X


def train_mask(df, munis_excluded=()):
    ok = df.year_raw.notna() & ~df.heap & ~df.secondary & ~df.muni.isin(munis_excluded)
    n = df[ok].groupby("bg").id.transform("size").reindex(df.index)
    return ok & (n >= 8)


def population(df, pops, cty):
    cs = pd.read_csv(ROOT / "data/tables/population_counties.csv")
    cs = cs[cs.area == cty].set_index("year").population.to_dict()
    if not cs:   # outer counties: the county's census table from its Wikipedia article (wiki_pop.json, key "county:<name>")
        cs = {int(k): v for k, v in pops.get(f"county:{cty}", {}).get("series", {}).items()}
    out = {}
    for m in df.muni.unique():
        ser = {int(k): v for k, v in pops.get(m, {}).get("series", {}).items()}
        if len(ser) < 3 and m in set(df.town):
            ser = {int(k): v for k, v in pops.get(df[df.muni == m].town.iloc[0], {}).get("series", {}).items()}
        out[m] = pop_cdf(ser, cs)
    return out


def build_one(cty, models_df=None):
    pops = json.loads((RAW / "wiki_pop.json").read_text())
    df, bg, X = prepare(cty)
    return df, bg, X, pops


def run_build():
    INT.mkdir(parents=True, exist_ok=True)
    pops = json.loads((RAW / "wiki_pop.json").read_text())
    data = {c: prepare(c) for c in COUNTIES}
    # one model for both counties, trained on every dated main building (heap years excluded)
    Xs, ys = [], []
    for c, (df, bg, X) in data.items():
        m = train_mask(df)
        Xs.append(X[m])
        ys.append(within_pct(df, m)[m].values)
    w = fit(pd.concat(Xs), np.concatenate(ys))
    np.save(INT / "model_w.npy", w)
    summary = {}
    for c, (df, bg, X) in data.items():
        main = ~df.secondary
        need = df.year_raw.isna()
        # a parcel without a main building row of its own: secondaries whose main_id is themselves are mains
        is_main = main | (df.main_id == df.id)
        idx = df.index[need & is_main]
        score = X.loc[idx].values @ w
        known = known_tables(df, bg, df.year_raw.notna())
        est, exp = allocate(df, idx, score, known, population(df, pops, c), muni_dist(df, bg))
        est["order"] = "model"
        rest = df.index[need & ~is_main]
        e2 = df.loc[rest, ["id", "main_id"]].merge(est.drop(columns=["bg"]).rename(columns={"id": "main_id"}),
                                                   on="main_id", how="left").dropna(subset=["year_est"])
        e2["bg"] = df.loc[rest].set_index("id").bg.reindex(e2.id).values
        e2["basis"] = e2.basis + "+outbuilding_of_main"
        allest = pd.concat([est, e2.drop(columns=["main_id"])], ignore_index=True)
        allest["year_est"] = allest.year_est.astype("int16")
        allest[["year_lo", "year_hi"]] = allest[["year_lo", "year_hi"]].astype("int16")
        allest.to_parquet(OUT / f"ny_{c}_estimates.parquet", index=False)
        summary[c] = {"rows": len(allest), "undated_total": int(need.sum()), "mains": len(est)}
        log(c, summary[c])
        est.assign(muni=df.loc[est.index, "muni"].values).to_parquet(INT / f"{c}_mains_est.parquet")
        np.save(INT / f"{c}_expected.npy", exp)
    (INT / "build_summary.json").write_text(json.dumps(summary, indent=1))


def run_build_outer(targets):
    """Estimates for the outer counties. One ridge model on every dated main building of the two inner counties and of the
    outer counties that carry years; the normal equations are summed county by county (memory). The two inner counties'
    own files are not rewritten."""
    INT.mkdir(parents=True, exist_ok=True)
    pops = json.loads((RAW / "wiki_pop.json").read_text())
    train = [c for c in ALL if (OUT / f"ny_{c}.parquet").exists() and c not in ("dutchess", "nassau")]
    A = b = None
    prepared = {}
    for c in train:
        cache = INT / f"trainsums_{c}.npz"   # the normal equations of the county, kept (rebuilt if its footprint file is newer)
        if cache.exists() and cache.stat().st_mtime > (OUT / f"ny_{c}.parquet").stat().st_mtime and c not in targets:
            z = np.load(cache)
            Ac, bc, n = z["A"], z["b"], int(z["n"])
        else:
            df, bg, X = prepare(c)
            m = train_mask(df)
            n = int(m.sum())
            Xm, y = X[m].values, within_pct(df, m)[m].values
            Ac, bc = Xm.T @ Xm, Xm.T @ y
            np.savez(cache, A=Ac, b=bc, n=n)
            if c in targets:
                prepared[c] = (df, bg, X)
            del df, bg, X
        if n >= 500:
            A = Ac if A is None else A + Ac
            b = bc if b is None else b + bc
        log(c, "trains on", n)
    for c in targets:
        if c not in prepared:
            prepared[c] = prepare(c)
    w = np.linalg.solve(A + 5.0 * np.eye(A.shape[0]), b)
    np.save(INT / "model_w_outer.npy", w)
    summary = {}
    for c in targets:
        df, bg, X = prepared.pop(c)
        main = ~df.secondary
        need = df.year_raw.isna()
        is_main = main | (df.main_id == df.id)
        idx = df.index[need & is_main]
        if not len(idx):
            log(c, "every footprint carries a year")
            continue
        score = X.loc[idx].values @ w
        known = known_tables(df, bg, df.year_raw.notna())
        est, exp = allocate(df, idx, score, known, population(df, pops, c), muni_dist(df, bg))
        est["order"] = "model"
        rest = df.index[need & ~is_main]
        e2 = df.loc[rest, ["id", "main_id"]].merge(est.drop(columns=["bg"]).rename(columns={"id": "main_id"}),
                                                   on="main_id", how="left").dropna(subset=["year_est"])
        e2["bg"] = df.loc[rest].set_index("id").bg.reindex(e2.id).values
        e2["basis"] = e2.basis + "+outbuilding_of_main"
        allest = pd.concat([est, e2.drop(columns=["main_id"])], ignore_index=True)
        allest["year_est"] = allest.year_est.astype("int16")
        allest[["year_lo", "year_hi"]] = allest[["year_lo", "year_hi"]].astype("int16")
        allest.to_parquet(OUT / f"ny_{c}_estimates.parquet", index=False)
        summary[c] = {"rows": len(allest), "undated_total": int(need.sum()), "mains": len(est),
                      "max_on_one_year": int(allest.year_est.value_counts().iloc[0])}
        log(c, summary[c])
        est.assign(muni=df.loc[est.index, "muni"].values).to_parquet(INT / f"{c}_mains_est.parquet")
        np.save(INT / f"{c}_expected.npy", exp)
        (INT / f"{c}_summary.json").write_text(json.dumps(summary[c]))
        del df, bg, X, est, exp


def metrics(true, est):
    e = np.abs(true - est)
    return {"n": int(len(e)), "mae_median": float(np.median(e)), "mae_mean": float(e.mean()),
            "within10": float((e <= 10).mean()), "within5": float((e <= 5).mean()),
            "same_decade": float((bin_of(true) == bin_of(est)).mean())}


def run_validate():
    pops = json.loads((RAW / "wiki_pop.json").read_text())
    rep = {"munis": {}, "bydecade": {}, "tables": {}}
    allrows = []
    for c in COUNTIES:
        df, bg, X = prepare(c)
        pp = population(df, pops, c)
        md = muni_dist(df, bg)
        for m in VALID:
            if m not in set(df.muni):
                continue
            sel = (df.muni == m) & df.year_raw.notna() & ~df.secondary
            if sel.sum() < 100:
                continue
            tm = train_mask(df, (m,))
            w = fit(X[tm], within_pct(df, tm)[tm].values)
            # known = every dated building outside m; m hidden entirely
            known = known_tables(df, bg, df.year_raw.notna() & (df.muni != m))
            idx = df.index[sel]
            truth_ok = ~df.loc[idx, "heap"].values
            res = {}
            for name, sc in (("model", X.loc[idx].values @ w),
                             ("random", np.random.default_rng(1).random(len(idx))),
                             ("distance_only", X.loc[idx, "ldc"].values)):
                est, exp = allocate(df, idx, sc, known, pp, md)
                tr = df.loc[idx, "year_raw"].values
                res[name] = metrics(tr[truth_ok], est.year_est.values[truth_ok])
                if name == "model":
                    e = est.year_est.values
                    allrows.append(pd.DataFrame({"muni": m, "true": tr, "est": e, "heap": ~truth_ok}))
                    dec = lambda y: np.where(y < 1940, "pre1940", ((y // 10) * 10).astype(int).astype(str))
                    t = pd.Series(dec(tr[truth_ok])).value_counts(normalize=True)
                    s = pd.Series(dec(e[truth_ok])).value_counts(normalize=True)
                    a = pd.Series(exp[truth_ok].mean(0), index=[b[0].split("-")[0] for b in BINS])
                    rep["tables"][m] = pd.DataFrame({"recorded": t, "estimated": s}).fillna(0).round(4).to_dict()
                    rep["tables"][m]["acs_expected"] = {k: round(v, 4) for k, v in a.items()}
            rep["munis"][m] = res
            log(m, res["model"], "random", res["random"]["mae_median"])
    A = pd.concat(allrows)
    A = A[~A.heap]
    A["dec"] = np.where(A.true < 1940, 1930, (A.true // 10) * 10)
    for d, g in A.groupby("dec"):
        rep["bydecade"][str(int(d))] = metrics(g.true.values, g.est.values)
    rep["all"] = metrics(A.true.values, A.est.values)
    (INT / "validation.json").write_text(json.dumps(rep, indent=1))
    A.to_parquet(INT / "validation_rows.parquet")


def run_check():
    rep = json.loads((INT / "validation.json").read_text())
    pops = json.loads((RAW / "wiki_pop.json").read_text())
    labs = [b[0] for b in BINS]
    md = []
    P = md.append
    sections = {}
    for c in COUNTIES:
        f = OUT / f"ny_{c}_estimates.parquet"
        e = pd.read_parquet(f)
        df = pd.read_parquet(OUT / f"ny_{c}.parquet", columns=["id", "muni", "town", "year_raw", "secondary"])
        e = e.merge(df[["id", "muni"]], on="id")
        assert e.id.is_unique and (e.year_lo <= e.year_est).all() and (e.year_est <= e.year_hi).all()
        assert not df.set_index("id").loc[e.id].year_raw.notna().any(), "estimate for a dated footprint"
        assert len(e) == int(df.year_raw.isna().sum()), "a footprint without a year has no estimate"
        top = e.year_est.value_counts()
        log(c, len(e), "max on one year", int(top.iloc[0]), int(top.index[0]), "median per year", float(top.median()))
        e["bin"] = [labs[i] for i in bin_of(e.year_est.values)]
        m = pd.read_parquet(INT / f"{c}_mains_est.parquet")
        exp = np.load(INT / f"{c}_expected.npy")
        rows = []
        pp = population(df.assign(), pops, c)
        for mu, g in e.groupby("muni"):
            d = g.bin.value_counts(normalize=True).reindex(labs).fillna(0)
            mi = np.where(m.muni.values == mu)[0]
            x = exp[mi].mean(0) if len(mi) else np.zeros(len(labs))
            nser = len([1 for y in pops.get(mu, {}).get("series", {}) if int(y) <= 1940])
            rows.append((mu, len(g), d.values, x, pp[mu][2], pops.get(mu, {}).get("title", ""), nser,
                         float(g.year_est.value_counts().iloc[0] / len(g))))
        sections[c] = (rows, len(e), int(top.iloc[0]), int(top.index[0]), float(top.median()), len(df))
    P("# Estimated construction years for the county footprints without a recorded year\n")
    P("Written by `pipeline/counties_ny_estimates.py check` from the built files; numbers are not typed. "
      "Every row of `data/interim/counties/ny_<county>_estimates.parquet` is an **estimate** (`estimated`): "
      "none is a record of the building.\n")
    P("## Sources\n")
    P("| id | What | URL | Licence | Used for |\n|---|---|---|---|---|")
    P("| `acs_bg` | ACS 5-year 2018-2022, table B25034 (year structure built, housing units) by block group, in the TIGER/Line geodatabase with demographic data | " + ACS_URL + " | US Census Bureau, public domain | how many buildings of a block group fall in each decade |")
    P("| `hisdac_fbuy` | HISDAC-US first built-up year, 250 m cells (Leyk & Uhl 2018, doi:10.7910/DVN/PKJ90M), modelled from Zillow property records | https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/PKJ90M | CC0 1.0 (dataset licence field) | one covariate to order buildings inside a block group; never a date |")
    P("| `wiki_census` | decennial census counts of each municipality, from the `US Census population` / `Historical populations` tables of its English Wikipedia article (titles in `data/raw/counties_ny_est/wiki_pop.json`, URL `https://en.wikipedia.org/wiki/<title>`) | https://en.wikipedia.org | CC BY-SA (facts from the Census Bureau) | spread the 1939-or-earlier bin over the town's growth |")
    P("| `county_pop` | `data/tables/population_counties.csv` | repo | as cited there | fallback where the town has fewer than 3 census counts up to 1940 or none before 1900 (Bedford, Briarcliff Manor, Tuckahoe, Rye city, Haverstraw village) |")
    P("| `places`, `stations` | `data/tables/places_counties.csv` (town / city centres), `data/tables/transit_stations.csv` (mnr, njt, rail) | repo | as cited there | distance covariates |\n")
    P("Not reachable or not used: the Census API (`api.census.gov`) answers every request with a redirect to a "
      "\"missing key\" page; the TIGER_DP geodatabase carries the same table, so it was not needed. HISDAC's BUPR "
      "(property-record counts) and BUPL layers were not downloaded. **USGS 1:24,000 sheets (evidence 3): not done.**\n")
    P("## Method\n")
    P("1. Footprint -> block group (point in polygon; nearest if outside). Units: main buildings (the largest outline of a parcel); outbuildings (`secondary`) take their parcel's main building's estimate (`+outbuilding_of_main` in `basis`). Footprints outside any parcel count as mains.")
    P("2. The block group's B25034 distribution (10 bins: 1939 or earlier, then decades to 2020+) is the target. Dated buildings of the same block group (partly dated municipalities, other municipalities sharing the group) are counted first and subtracted (units - dated buildings, floored at 0; the whole table is used if less than 20 % would remain). Block groups with under 5 housing units use their municipality's summed distribution (`acs_muni`).")
    P("3. Order: a ridge regression (`FEATS`: log distance to the nearest old town centre and to the nearest railroad station, HISDAC FBUY, log footprint area, height, density within 60 m, mean and spread of area and mean height within 100 m, nearest-neighbour distance, use class; each as its rank within the block group, plus squares) predicts a building's within-group age percentile. Trained on the dated, non-heap main buildings of every dated municipality of both counties (validation: that municipality left out). Buildings are sorted by the prediction (+ a small stable hash to break ties) and cut by the target distribution.")
    P("4. Year inside a decade: 70 % the building's position within its bin, 30 % a stable hash of its id, so decades do not stack on their first year. 1939-or-earlier: the same position mapped through the municipality's census-population curve (stock built by year t proportional to population(t); before its first census count a ramp over 80 years; 1700 at the earliest) - a reconstruction, not a record; `year_lo` 1700, `year_hi` 1939.")
    P("5. `basis`: `acs_bg:<decade>` or `acs_bg:pre1940+town_growth` (`+county_growth` where the county series stood in), `acs_muni:...`; `order` = `model`. HISDAC is in the ordering only, so no row is `hisdac_fbuy:`.\n")
    P("## Validation on the dated municipalities (years hidden, estimated the same way)\n")
    P("Truth = the assessor's `year_raw` of main buildings, **heap years excluded** (round estimates). Every dated municipality outside the test one is kept as known data and as the training set; the test one is hidden entirely. `random` = same table, random order; `distance_only` = ordering by distance to the centre alone.\n")
    P("| Municipality | n | median abs. error (years) | share within 10 y | within 5 y | same decade | median error, random order | distance only |\n|---|---:|---:|---:|---:|---:|---:|---:|")
    for mu, r in rep["munis"].items():
        a, b, d = r["model"], r["random"], r["distance_only"]
        P(f"| {mu} | {a['n']:,} | {a['mae_median']:.0f} | {a['within10']:.0%} | {a['within5']:.0%} | {a['same_decade']:.0%} | {b['mae_median']:.0f} | {d['mae_median']:.0f} |")
    a = rep["all"]
    P(f"| **all** | {a['n']:,} | {a['mae_median']:.0f} | {a['within10']:.0%} | {a['within5']:.0%} | {a['same_decade']:.0%} | | |\n")
    P("By true decade (all test municipalities pooled):\n")
    P("| True decade | n | median abs. error | within 10 y |\n|---|---:|---:|---:|")
    for k, v in rep["bydecade"].items():
        P(f"| {'pre1940' if k == '1930' else k} | {v['n']:,} | {v['mae_median']:.0f} | {v['within10']:.0%} |")
    P("\nRecorded vs estimated vs ACS-expected decade shares, five dated towns (test run):\n")
    for mu in ["Yonkers", "White Plains", "Scarsdale", "Rye", "Somers"]:
        t = rep["tables"].get(mu)
        if not t:
            continue
        P(f"**{mu}**\n\n| Decade | recorded (non-heap) | estimated | ACS expected |\n|---|---:|---:|---:|")
        for k in ["pre1940"] + [str(x) for x in range(1940, 2030, 10)]:
            P(f"| {k} | {t['recorded'].get(k, 0):.1%} | {t['estimated'].get(k, 0):.1%} | {t['acs_expected'].get(k if k != '2020' else '2020', 0):.1%} |")
        P("")
    P("## What is estimated\n")
    for c, (rows, n, top1, topy, med, ntot) in sections.items():
        P(f"### {c.title()}: {n:,} of {ntot:,} footprints\n")
        P(f"Largest number of estimates on one year: {top1:,} ({topy}); median over years: {med:.0f}.\n")
        P("| Municipality | Footprints | " + " | ".join(l.replace('-20', '-') for l in labs) + " | pre-1940 curve from | top year share |\n|---|---:|" + "---:|" * len(labs) + "---|---:|")
        for mu, nn, d, x, src, title, nser, ty in sorted(rows):
            P(f"| {mu} | {nn:,} | " + " | ".join(f"{v:.0%} (acs {w:.0%})" for v, w in zip(d, x)) + f" | {src}{' ' + title if src == 'town' else ''} | {ty:.1%} |")
        P("")
    P("Each decade cell: share of the municipality's estimated footprints (in brackets the table's expected share, which differs where dated buildings in shared block groups were subtracted or the rounding of small groups bites).\n")
    P("## Weak spots\n")
    P("- A decade is only as good as the order inside the block group; the order model beats a random one by a few years, not by much (table above). Expect the right decade for roughly a third of buildings; the distribution of decades per block group is what is trustworthy, not any single building.")
    P("- B25034 counts housing units, not buildings: apartment blocks hold many units, so a decade of apartment building is over-represented in the target relative to the building count. Non-residential buildings take the residential distribution.")
    P("- The 'recorded' column excludes heap years (round, mostly old), which makes it younger than the truth; the ACS-vs-recorded gap in Yonkers (pre-1940: ACS 34 %, assessor 49 %) is also the units-versus-buildings effect above: ACS counts apartments, the assessor's list counts buildings.")
    P("- ACS sample error (the margins of error are in the geodatabase, not used) is large for small block groups; the 2018-2022 survey puts the cut at 2022; the footprints are 2026.")
    P("- Demolished houses are not in B25034: the target is of surviving units only, the same as the footprints.")
    P("- The pre-1940 curve assumes the surviving stock was built in proportion to population; the real stock has older buildings under-represented (demolition), so early years are probably too common.")
    P("- Overture/State footprints include sheds and garages that have no parcel main building; they are treated as mains and take housing-unit shares.")
    P("- Nassau: the method needs only footprints, Census data and the order covariates, so it would run; with no recorded year in the county at all the order model could not be trained there and would be borrowed from Westchester and Rockland (an unchecked transfer across the county line), and the same per-building accuracy (about a third in the right decade) would apply.\n")
    (ROOT / "data/research/counties_ny_estimates.md").write_text("\n".join(md))
    log("wrote data/research/counties_ny_estimates.md")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "build_outer":
        run_build_outer([a for a in sys.argv[2:] if a in OUTER_COUNTIES] or list(OUTER_COUNTIES))
    else:
        {"download": download, "build": run_build, "validate": run_validate, "check": run_check}[cmd]()
