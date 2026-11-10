"""Stage: real street and park trees of the five boroughs -> the viewer's two tree sets.

Every tree stands where NYC Parks' inventory puts it. Sources, licences, rules, the
equations, counts and checks: data/research/street_trees.md.

Base: the living inventory, Forestry Tree Points (ForMS 2.0, NYC Open Data `hn5i-inap`,
refreshed every two weeks): tree points with structure "Full" that are not dead, joined to
Forestry Planting Spaces (`82zj-84is`) for street / park. ForMS was seeded from the 2015
street tree census (`uvpi-gqnh`) and has been kept since: it has the trees planted after the
census, with their planting dates, has dropped the ones removed (one census tree in six),
and has the trees of the landscaped parks, which no census counted. The 2015 census is
evidence for the dates (the trunk as counted then; what stood on a spot), not the base.
The 2005 and 1995 censuses (`29bw-z7pj`, `kyad-zm4j`) are downloaded but NOT used: their
trees were recorded by address and stand on the address point, not where the tree is (a
2015 tree of 20 in or more, certainly there in 2005, has a 2005 record within 3 m in 0.3 %
of cases and on its own tax lot in 76 %), so "no tree here in 2005" proves nothing.

Planting year, best first (the `source` column of the outputs says which):
  0 recorded    a planting date in ForMS that is believable: not a bulk date (a day with
                thousands of records, or a year far above the years around it) and not
                contradicted by the trunk                                      -> exact
  1 after 2015  a street tree whose ForMS record was made after the census, with a young
                trunk, where the census counted no tree within 3 m, or a dead tree / stump,
                or a thicker tree (its predecessor): planted between the census passing
                (the date of its nearest record) and the ForMS record. A trunk still at
                planting size (<= 3.5 in) -> the day the record was made (records with
                both dates were made a median 9 days after planting); else by the trunk,
                inside the bracket                                             -> estimated
  2 diameter    age from the trunk diameter with the US Forest Service Urban Tree Database
                (McPherson, van Doorn & Peper 2016, RDS-2016-0005; PSW-GTR-253), Northeast
                region "NoEast" (reference city: Queens, New York): the species' own
                age-from-DBH equation                                          -> estimated
  3 diameter    no equation for the species in Queens: its genus' median there, else the
                species / genus in Indianapolis, Charlotte or Minneapolis, else the median
                of all Queens species                                          -> estimated
  (no planting date and no usable trunk: left out, about 400 trees — the Bay's "ten years
  after the street" put park trees of Lower Manhattan in 1668)
The trunk is the one the 2015 census measured where the ForMS record is that census tree
(same spot within 1.5 m, record of the census period), at the census date; else ForMS's, at
its last update. A whole-inch reading is a range: each tree takes a stable point in it.
Bounds: a diameter-dated tree is not planted more than 3 years before the 2nd-earliest
building within 45 m (standing or vanished, data/interim/nyc_building_points.parquet; the
rule that dates the streets) — except trunks of 75 cm or more of species native here, and
of park trees, kept as remnants of the land before the houses; no tree stands before the
ground under it (data/interim/grid_detail_landyear.npy, + 1 year) or after its record.
Dead trees, stumps, shafts and retired points are left out. The viewer's tree format has no
end year, so nothing removed is drawn.

Size: height and crown from today's trunk with the same database's equations (same order
of fall-backs), clamped to the Bay's ranges (3-24 m, crown radius 1-7 m), in steps of 0.5 m
and 0.25 m. Form: conifer by genus, else broadleaf (no palms here; the Bay's name patterns
would have made palms of Acer palmatum and conifers of Carpinus).

Outputs (the formats of the Bay's trees.py / region_trees.py, read by viewer/src/layers/
trees.ts and region-trees.ts; positions in 5e-6 degrees = 0.4-0.6 m, see position_scale):
  viewer/public/data/street-trees.bin.gz        Manhattan, always loaded
  viewer/public/data/region-trees/index.json    + 12/<x>/<y>.bin.gz: the other four boroughs
  data/interim/street_trees/trees.parquet       one row per tree, for audits
  data/interim/street_trees/grid_detail_streettrees.npy   inventory trees per 29 m terrain cell
  data/interim/street_trees/report.json, check.json       counts, shares, histogram, checks
`inventory_mask()` is for terrain_tiles.py (canopy pixels the real trees already stand for).

Usage: python street_trees.py [download|build|check|all]   (default: all). The downloads
(400 MB, 6 minutes) are cached per table: delete data/raw/street_trees/<table> to refresh.
`build` takes under 2 minutes and 1.4 GB and ends with `check` (the invariants read back
from the built files; exit 1 if one fails). Re-run `build` whenever the buildings
(nyc_building_points.parquet) or the land years (grid_detail_landyear.npy) change.
"""
from __future__ import annotations

import json
import re
import sys
import time
import zipfile

import numpy as np
import pandas as pd

from common import CURRENT_YEAR, INTERIM, RAW, VIEWER_DATA, YEAR_MIN, log

OUT_RAW = RAW / "street_trees"
WORK = INTERIM / "street_trees"
UTD = OUT_RAW / "usfs_utd"
UTD_URL = "https://www.fs.usda.gov/rds/archive/products/RDS-2016-0005/RDS-2016-0005.zip"
SODA = "https://data.cityofnewyork.us/resource"
UA = "NYCThroughTime-research/0.1"
PAGE = 100_000

# NYC Open Data tables: only the columns the stage reads, as published (no edits)
TABLES = {
    "forms_tree_points": dict(
        id="hn5i-inap", where="tpstructure = 'Full'",
        select="objectid,plantingspaceglobalid,dbh,tpstructure,tpcondition,genusspecies,createddate,"
               "updateddate,planteddate,geometry"),
    "forms_planting_spaces": dict(
        id="82zj-84is", where=None, select="globalid,pssite,psstatus,jurisdiction"),
    "census_2015": dict(
        id="uvpi-gqnh", where=None,
        select="tree_id,created_at,tree_dbh,stump_diam,curb_loc,status,spc_latin,borocode,latitude,longitude,bbl,address"),
    "census_2005": dict(
        id="29bw-z7pj", where=None,
        select="objectid,cen_year,tree_dbh,tree_loc,status,spc_latin,borocode,latitude,longitude,bbl,address"),
    "census_1995": dict(
        id="kyad-zm4j", where=None,
        select="recordid,site,diameter,condition,borough,longitude,latitude,spc_latin,bbl,address"),
}


# ---------------------------------------------------------------- download
def download(only: list[str] | None = None):
    """Each table in pages of 100,000 rows (ordered by the row id, so pages are stable) to
    data/raw/street_trees/<name>/page-NNN.csv, and the Urban Tree Database. Cached: a
    table with a source.json is complete."""
    import requests
    s = requests.Session()
    s.headers["User-Agent"] = UA
    OUT_RAW.mkdir(parents=True, exist_ok=True)
    if not (UTD / "done").exists():
        UTD.mkdir(parents=True, exist_ok=True)
        z = UTD / "RDS-2016-0005.zip"
        r = s.get(UTD_URL, timeout=600)
        r.raise_for_status()
        z.write_bytes(r.content)
        zipfile.ZipFile(z).extractall(UTD)
        (UTD / "done").write_text(time.strftime("%Y-%m-%d"))
        log(f"street trees: Urban Tree Database -> {UTD}")
    for name, t in TABLES.items():
        if only and name not in only:
            continue
        d = OUT_RAW / name
        if (d / "source.json").exists():
            log(f"street trees: {name} cached")
            continue
        d.mkdir(parents=True, exist_ok=True)
        n, page = 0, 0
        while True:
            p = d / f"page-{page:03d}.csv"
            if not p.exists():
                params = {"$select": t["select"], "$order": ":id", "$limit": PAGE, "$offset": page * PAGE}
                if t["where"]:
                    params["$where"] = t["where"]
                for attempt in range(6):
                    try:
                        r = s.get(f"{SODA}/{t['id']}.csv", params=params, timeout=600)
                        r.raise_for_status()
                        break
                    except Exception as e:  # network hiccup / throttling
                        log(f"  {name} page {page}: retry {attempt}: {e!r}")
                        time.sleep(5 * 2 ** attempt)
                else:
                    raise RuntimeError(f"{name}: page {page} failed")
                tmp = p.with_suffix(".part")
                tmp.write_bytes(r.content)
                tmp.rename(p)
            rows = len(pd.read_csv(p, dtype=str, usecols=[0]))   # (a quoted address may hold a line break)
            n += rows
            log(f"  {name}: page {page}, {n} rows")
            if rows < PAGE:
                break
            page += 1
        (d / "source.json").write_text(json.dumps({
            "dataset": t["id"], "url": f"https://data.cityofnewyork.us/d/{t['id']}", "select": t["select"],
            "where": t["where"], "rows": n, "downloaded": time.strftime("%Y-%m-%d")}, indent=1))
        log(f"street trees: {name}: {n} rows -> {d}")


# ---------------------------------------------------------------- growth equations
# Urban Tree Database regions, best first: the city itself (reference city Queens), then the
# humid eastern / midwestern reference cities (Indianapolis, Charlotte, Minneapolis). The
# western, desert and tropical regions are not used (irrigated or frost-free growth).
HOME = "NoEast"
NEIGHBOURS = ["LoMidW", "Piedmt", "MidWst"]
SYNONYM = {"platanus hispanica": "platanus acerifolia", "platanus hybrida": "platanus acerifolia",
           "gleditsia triacanthos": "gleditsia triacanthos", "prunus kwanzan": "prunus serrulata",
           "malus spp": "malus", "prunus spp": "prunus", "morus spp": "morus"}
SP_WORDS = re.compile(r"[a-z]+")
DBH_GRID = np.arange(0.0, 251.0, 0.5)  # cm


def sci_key(name: str) -> str:
    """'Platanus x acerifolia' / "Prunus serrulata 'Green leaf'" / 'Gleditsia triacanthos var.
    inermis' / 'Malus spp.' -> 'platanus acerifolia' / 'prunus serrulata' / 'gleditsia
    triacanthos' / 'malus' (genus + epithet, lower case; the Bay stage's rule)."""
    s = str(name or "").strip()
    s = re.sub(r"'[^']*'|\"[^\"]*\"|\bcvs?\.?|\bvar\..*$|\bssp\..*$|\bsubsp\..*$|\bspp?\.?$|\bspp?\.?\s|×|\s[xX]\s", " ", s).lower()
    w = [x for x in SP_WORDS.findall(s) if x not in ("x", "cv", "cvs", "var", "spp", "sp", "species", "hybrid", "and")]
    key = " ".join(w[:2])
    return SYNONYM.get(key, key)


def load_utd() -> dict:
    """{(region, species key, predicts): (eq, a, b, c, d, e, sigma, x_lo, x_hi, y_lo, y_hi)} from
    the Urban Tree Database (TS6_Growth_coefficients.csv): dbh in cm -> age in years after
    planting, tree height in m, crown diameter in m."""
    t = pd.read_csv(UTD / "Data" / "TS6_Growth_coefficients.csv", encoding="latin-1")
    t.columns = [c.strip() for c in t.columns]
    t["Region"] = t.Region.astype(str).str.strip()
    t = t[t.Region.isin([HOME] + NEIGHBOURS)].copy()
    t["key"] = t["Scientific Name"].map(sci_key)
    # the dbh range an equation applies to comes from the species' age -> dbh fit
    rng = t[(t["Independent variable"] == "age") & (t["Predicts component"] == "dbh")]
    rng = {(r.Region, r.key): (float(r["Apps min"]), float(r["Apps max"])) for _, r in rng.iterrows()}
    out = {}
    for _, r in t[t["Independent variable"] == "dbh"].iterrows():
        pred = {"age": "age", "tree ht": "height", "crown dia": "crown"}.get(r["Predicts component"])
        if not pred or (r.Region, r.key) not in rng:
            continue
        f = lambda c: float(r[c]) if pd.notna(r[c]) else 0.0  # noqa: E731
        out[(r.Region, r.key, pred)] = (str(r.EqName).strip(), f("a"), f("b"), f("c"), f("d"), f("e"), f("Sigma"),
                                        *rng[(r.Region, r.key)], f("Apps min"), f("Apps max"))
    return out


def utd_curve(eq):
    """An equation evaluated on DBH_GRID (the database's forms, TS4): polynomials, and
    exp(a + b ln(ln(dbh + 1)) + w mse / 2), exp(a + b dbh + w mse / 2). Made usable everywhere:
    monotonic, clamped to the published application range (the Bay stage's rule)."""
    name, a, b, c, d, e, sigma, x_lo, x_hi, y_lo, y_hi = eq
    x = np.clip(DBH_GRID, x_lo, x_hi)
    mse = sigma ** 2
    if name.startswith("loglog"):
        w = {"1": 1.0, "2": np.sqrt(x), "3": x, "4": x ** 2}[name[-1]]
        y = np.exp(a + b * np.log(np.log(x + 1)) + w * mse / 2)
    elif name.startswith("expow"):
        w = {"1": 1.0, "2": np.sqrt(x), "3": x, "4": x ** 2}[name[-1]]
        y = np.exp(a + b * x + w * mse / 2)
    else:
        y = a + b * x + c * x ** 2 + d * x ** 3 + e * x ** 4
    return np.maximum.accumulate(np.clip(y, max(y_lo, 0.0), y_hi)), x_hi


def growth_tables(utd):
    """Curves over DBH_GRID per (region, species key, what) and per (region, genus, what) —
    the median of the genus' species — and the pooled curve per what: the median of every
    NoEast species. Beyond the trunk range a species' equation was fitted to, its age keeps
    growing at the pooled rate: the median years-per-cm of the NoEast species whose
    equations do reach that trunk (at least three; the last such rate beyond them). A
    species' own end slope is not used: the exponential fits run away (a 117 cm silver
    linden came out 250 years old). A height or crown stays at its maximum."""
    import warnings
    raw = {k: utd_curve(eq) + (eq[7],) for k, eq in utd.items()}
    rates = []
    for (region, key, pred), (y, x_hi, x_lo) in raw.items():
        if region == HOME and pred == "age":
            r = np.gradient(y, DBH_GRID)
            rates.append(np.where((DBH_GRID >= x_lo) & (DBH_GRID <= x_hi) & (r > 0), r, np.nan))
    rates = np.stack(rates)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        rate = np.where(np.isfinite(rates).sum(axis=0) >= 3, np.nanmedian(rates, axis=0), np.nan)
    rate = pd.Series(rate).ffill().bfill().to_numpy()
    cum = np.cumsum(rate) * (DBH_GRID[1] - DBH_GRID[0])
    curves = {}
    for (region, key, pred), (y, x_hi, _) in raw.items():
        if pred == "age":
            i_hi = min(np.searchsorted(DBH_GRID, x_hi), len(DBH_GRID) - 1)
            y = np.where(DBH_GRID > x_hi, y[i_hi] + (cum - cum[i_hi]), y)
        curves[(region, key, pred)] = y
    growth_tables.pooled_rate = {int(v): round(float(rate[np.searchsorted(DBH_GRID, v)]), 2) for v in (25, 50, 75, 100, 125, 150)}
    genus, allsp = {}, {}
    for (region, key, pred), y in curves.items():
        genus.setdefault((region, key.split()[0], pred), []).append(y)
        if region == HOME:
            allsp.setdefault(pred, []).append(y)
    gcurves = {k: np.median(np.stack(v), axis=0) for k, v in genus.items()}
    pooled = {k: np.median(np.stack(v), axis=0) for k, v in allsp.items()}
    return curves, gcurves, pooled


def pick_curve(curves, gcurves, pooled, key: str, pred: str):
    """Species in Queens > its genus in Queens > the species in a neighbouring region > its
    genus there > every Queens species pooled."""
    g = key.split()[0] if key else ""
    if (HOME, key, pred) in curves:
        return curves[(HOME, key, pred)], "species"
    if (HOME, g, pred) in gcurves:
        return gcurves[(HOME, g, pred)], "genus"
    for region in NEIGHBOURS:
        if (region, key, pred) in curves:
            return curves[(region, key, pred)], f"species:{region}"
    for region in NEIGHBOURS:
        if (region, g, pred) in gcurves:
            return gcurves[(region, g, pred)], f"genus:{region}"
    return pooled[pred], "pooled"


# ---------------------------------------------------------------- inputs
DECO_ORIGIN = (-73.97, 40.72)   # viewer/src/layers/deco-layer.ts: the tiles share it, so they merge
TILE_Z = 12
POS_SCALE = 5e-6                # degrees per position unit: 0.42 m east-west, 0.56 m north-south
UTM = 32618
STREET_LEAD = 3.0               # a street tree may stand this long before the 2nd building of its street
STREET_M = 45.0
REMNANT_CM = 75.0               # trunks this thick may be older than the houses (native species / park trees)
REMNANT_ANY_SPECIES = False     # True: the brief's wider reading (every trunk over 75 cm, planes included)
CENSUS_SAME_M = 1.5             # a ForMS record of the census period this close to a 2015 record is that tree
CENSUS_NEAR_M = 3.0             # "the census counted a tree here"
PLANTING_IN = 3.5               # ForMS records a newly planted tree at about 3 in (median of dated plantings)
CENSUS_IMPORT = 2016.9          # the census was loaded into ForMS on 2 Nov 2016
EVIDENCE = ["recorded planting date (ForMS)", "planted after the 2015 census (census + ForMS record)",
            "trunk diameter, species equation (Urban Tree Database, NoEast)",
            "trunk diameter, genus / neighbouring-region / pooled equation"]
CONIFER_GENERA = {"pinus", "picea", "abies", "tsuga", "pseudotsuga", "thuja", "juniperus", "cedrus", "chamaecyparis",
                  "cupressus", "cupressocyparis", "cuprocyparis", "taxus", "taxodium", "metasequoia", "larix",
                  "cryptomeria", "sequoia", "sequoiadendron", "sciadopitys", "platycladus", "calocedrus",
                  "cunninghamia", "araucaria", "pseudolarix"}
# species that grew here before the town (a thick trunk of one of these can be a remnant)
NATIVE = re.compile(r"^(quercus (alba|rubra|velutina|palustris|bicolor|coccinea|montana|prinus|stellata|phellos)|"
                    r"liriodendron tulipifera|fagus grandifolia|carya( \w+)?|liquidambar styraciflua|nyssa sylvatica|"
                    r"platanus occidentalis|acer (rubrum|saccharum|saccharinum)|ulmus americana|"
                    r"fraxinus (americana|pennsylvanica)|tilia americana|prunus serotina|sassafras albidum|"
                    r"juglans nigra|betula (lenta|nigra|populifolia)|pinus (strobus|rigida)|tsuga canadensis|"
                    r"populus (deltoides|grandidentata)|celtis occidentalis|castanea dentata|salix nigra|"
                    r"diospyros virginiana|juniperus virginiana)$")


def _pages(name):
    ps = sorted((OUT_RAW / name).glob("page-*.csv"))
    if not ps or not (OUT_RAW / name / "source.json").exists():
        raise SystemExit(f"street trees: {name} is not downloaded — run `python street_trees.py download`")
    return ps


def _year(s: pd.Series) -> np.ndarray:
    """'2018-11-07 11:11:11' -> decimal year (NaN if none / not a date)."""
    d = pd.to_datetime(s.astype("string").str.slice(0, 19), errors="coerce", format="mixed")
    return (d.dt.year + (d.dt.day_of_year - 1) / 365.25).to_numpy(float)


def load_forms() -> pd.DataFrame:
    """The living trees of ForMS: structure Full, not dead, with a position; street / park
    from the planting space."""
    site = {}
    for p in _pages("forms_planting_spaces"):
        t = pd.read_csv(p, dtype=str, usecols=["globalid", "pssite"])
        site.update(zip(t.globalid.values, t.pssite.values))
    parts = []
    for p in _pages("forms_tree_points"):
        t = pd.read_csv(p, dtype=str)
        t = t[(t.tpstructure == "Full") & (t.tpcondition != "Dead")]
        xy = t.geometry.str.extract(r"POINT\s*\(\s*(-?[\d.]+)\s+(-?[\d.]+)\s*\)").astype(float)
        nm = t.genusspecies.fillna("").str.split(" - ", n=1, expand=True)
        parts.append(pd.DataFrame({
            "objectid": pd.to_numeric(t.objectid, errors="coerce").fillna(0).astype(np.int64).values,
            "lon": xy[0].values, "lat": xy[1].values,
            "dbh_forms": pd.to_numeric(t.dbh, errors="coerce").astype(np.float32).values,
            "species": nm[0].str.strip().values,
            "created": _year(t.createddate), "updated": _year(t.updateddate), "planted": _year(t.planteddate),
            "created_stamp": t.createddate.values,
            "site": t.plantingspaceglobalid.map(site).fillna("").values,
        }))
    d = pd.concat(parts, ignore_index=True)
    # a creation stamp shared by hundreds of records is a bulk load, not the day a tree was entered
    d["bulk_created"] = (d.created_stamp.map(d.created_stamp.value_counts()) >= 500).values
    d = d.drop(columns="created_stamp")
    d["species"] = d.species.astype("category")
    return d[np.isfinite(d.lon) & np.isfinite(d.lat)].reset_index(drop=True)


def load_census_2015() -> pd.DataFrame:
    parts = []
    for p in _pages("census_2015"):
        t = pd.read_csv(p, dtype=str, usecols=["created_at", "tree_dbh", "status", "latitude", "longitude"])
        parts.append(pd.DataFrame({
            "lon": pd.to_numeric(t.longitude, errors="coerce").values, "lat": pd.to_numeric(t.latitude, errors="coerce").values,
            "dbh": pd.to_numeric(t.tree_dbh, errors="coerce").astype(np.float32).values,
            "alive": (t.status == "Alive").values, "date": _year(t.created_at)}))
    c = pd.concat(parts, ignore_index=True)
    return c[c.lat.between(40.4, 41.0) & c.lon.between(-74.3, -73.6)].reset_index(drop=True)


def boroughs_of(lon, lat) -> np.ndarray:
    """Borough code 1-5 of each point (TIGER county outlines, which include the water), 0 outside."""
    import geopandas as gpd
    import shapely
    from common import BORO_COUNTY, BOROUGHS
    co = gpd.read_file(f"zip://{RAW / 'tiger' / 'tl_2024_us_county.zip'}")
    co = co[(co.STATEFP == "36") & co.COUNTYFP.isin(list(BORO_COUNTY))].to_crs(4326)
    code = {v: int(k) for k, v in BOROUGHS.items()}
    out = np.zeros(len(lon), np.uint8)
    for _, r in co.iterrows():
        g = r.geometry
        shapely.prepare(g)
        out[shapely.contains_xy(g, lon, lat)] = code[BORO_COUNTY[r.COUNTYFP]]
    return out


def land_year(lon, lat) -> np.ndarray:
    """Year the ground at each point became land (29 m detail grid), NaN if always land."""
    from terrain_grid import grid_def
    g = grid_def("detail")
    ly = np.load(INTERIM / "grid_detail_landyear.npy")
    X = np.radians(lon) * 6378137.0
    Y = 6378137.0 * np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))
    c = np.rint((X - g["X0"]) / g["res"]).astype(int)
    r = np.rint((g["Y0"] - Y) / g["res"]).astype(int)
    ok = (c >= 0) & (r >= 0) & (c < g["cols"]) & (r < g["rows"])
    out = np.full(len(lon), np.nan)
    out[ok] = ly[r[ok], c[ok]]
    return out


def street_year(x, y) -> np.ndarray:
    """Year of the 2nd-earliest building within 45 m (standing or vanished; the only one if
    there is one), NaN if none — the rule that dates the streets (roads.py)."""
    from pyproj import Transformer
    from scipy.spatial import cKDTree
    b = pd.read_parquet(INTERIM / "nyc_building_points.parquet", columns=["lon", "lat", "start_year"])
    b = b[np.isfinite(b.start_year)]
    bx, by = Transformer.from_crs(4326, UTM, always_xy=True).transform(b.lon.values, b.lat.values)
    yr = b.start_year.to_numpy(float)
    tree = cKDTree(np.column_stack([bx, by]))
    out = np.full(len(x), np.nan)
    for i in range(0, len(x), 200_000):
        dist, idx = tree.query(np.column_stack([x[i:i + 200_000], y[i:i + 200_000]]), k=8, distance_upper_bound=STREET_M)
        ys = np.where(np.isfinite(dist), yr[np.minimum(idx, len(yr) - 1)], np.nan)
        ys.sort(axis=1)
        out[i:i + 200_000] = np.where(np.isfinite(ys[:, 1]), ys[:, 1], ys[:, 0])
    return out


def _hash01(oid: np.ndarray, salt: int) -> np.ndarray:
    """A stable number in [0, 1) per tree (from its ForMS object id)."""
    h = (oid.astype(np.uint64) + np.uint64(salt)) * np.uint64(0x9E3779B97F4A7C15)
    h ^= h >> np.uint64(29)
    h *= np.uint64(0xBF58476D1CE4E5B9)
    return ((h >> np.uint64(40)) & np.uint64(0xFFFF)).astype(float) / 65536.0


# ---------------------------------------------------------------- build
def build():
    from pyproj import Transformer
    from scipy.spatial import cKDTree

    WORK.mkdir(parents=True, exist_ok=True)
    d = load_forms()
    n_living = len(d)
    # positions as the viewer will read them (0.5 m): everything below uses the stored position
    q = np.rint((d[["lon", "lat"]].to_numpy() - DECO_ORIGIN) / POS_SCALE).astype(np.int64)
    d["qx"], d["qy"] = q[:, 0], q[:, 1]
    d["lon"], d["lat"] = DECO_ORIGIN[0] + q[:, 0] * POS_SCALE, DECO_ORIGIN[1] + q[:, 1] * POS_SCALE
    d["boro"] = boroughs_of(d.lon.values, d.lat.values)
    n_outside = int((d.boro == 0).sum())
    d = d[d.boro > 0]
    # two records on one spot: the thicker trunk stays
    d = d.sort_values("dbh_forms", ascending=False, na_position="last").drop_duplicates(["qx", "qy"])
    d = d.sort_values("objectid").reset_index(drop=True)
    n_dupe = n_living - n_outside - len(d)
    log(f"street trees: {n_living} living ForMS trees, {n_outside} outside the five boroughs, {n_dupe} doubles dropped")
    to_utm = Transformer.from_crs(4326, UTM, always_xy=True)
    x, y = to_utm.transform(d.lon.values, d.lat.values)
    oid = d.objectid.to_numpy()
    park = (d.site == "Park").to_numpy()
    street = (d.site == "Street").to_numpy()
    created = d.created.to_numpy(float)
    updated = d.updated.to_numpy(float)
    today = float(np.nanmax(created))              # the inventory's own date
    created = np.where(np.isfinite(created), created, today)

    # ---- the 2015 census: the same tree (trunk as counted then), or what stood on the spot
    c = load_census_2015()
    cx, cy = to_utm.transform(c.lon.values, c.lat.values)
    dist, idx = cKDTree(np.column_stack([cx, cy])).query(np.column_stack([x, y]), k=1)
    c_alive, c_dbh, c_date = c.alive.values[idx], c.dbh.to_numpy(float)[idx], c.date.to_numpy(float)[idx]
    del c, cx, cy
    same = (dist <= CENSUS_SAME_M) & (created <= CENSUS_IMPORT) & c_alive
    dbh_forms = d.dbh_forms.to_numpy(float)
    okd = lambda v: np.where((v > 0) & (v <= 90), v, np.nan)  # noqa: E731  inches; 0 and typing errors are no trunk
    dbh_forms, c_dbh = okd(dbh_forms), okd(c_dbh)
    use15 = same & np.isfinite(c_dbh)
    dbh_meas = np.where(use15, c_dbh, dbh_forms)                       # the trunk used for the date ...
    asof = np.where(use15, c_date, np.where(np.isfinite(updated), np.fmax(updated, created), created))  # ... and when
    asof = np.clip(asof, 2015.0, today)
    dbh_now = np.where(np.isfinite(dbh_forms), np.fmax(dbh_forms, np.where(same, np.nan_to_num(c_dbh), 0)), c_dbh)

    # ---- species: growth curves, form
    names = pd.Series(d.species.cat.categories)
    keys = names.map(sci_key)
    d["key"] = keys.to_numpy(dtype=object)[d.species.cat.codes]
    curves, gcurves, pooled = growth_tables(load_utd())
    # a whole-inch reading stands for anything within half an inch of it: each tree takes a
    # stable point inside, so one species' trees of one reading are not all planted in one year
    dbh_j = np.maximum(dbh_meas + (_hash01(oid, 1) - 0.5), 0.5)    # (NaN where there is no trunk)
    cm, cm_now = dbh_j * 2.54, np.where(np.isfinite(dbh_now), dbh_now, 6.0) * 2.54
    age = np.full(len(d), np.nan)
    age_plant = np.full(len(d), np.nan)
    hgt, crn = np.full(len(d), np.nan), np.full(len(d), np.nan)
    how = np.full(len(d), "", dtype=object)
    form = np.zeros(len(d), np.uint8)
    for key, ix in d.groupby("key", observed=True).indices.items():
        ca, h = pick_curve(curves, gcurves, pooled, key, "age")
        ok = np.isfinite(cm[ix])
        age[ix[ok]] = np.interp(cm[ix][ok], DBH_GRID, ca)
        how[ix] = h
        hgt[ix] = np.interp(cm_now[ix], DBH_GRID, pick_curve(curves, gcurves, pooled, key, "height")[0])
        crn[ix] = np.interp(cm_now[ix], DBH_GRID, pick_curve(curves, gcurves, pooled, key, "crown")[0]) / 2
        if key.split(" ")[0] in CONIFER_GENERA:
            form[ix] = 1
    key_arr = d.key.to_numpy()
    native = pd.Series(key_arr).str.match(NATIVE).to_numpy()
    remnant = (dbh_meas * 2.54 >= REMNANT_CM) & (native | park | REMNANT_ANY_SPECIES)
    age = np.minimum(age, np.where(remnant, 250.0, 150.0))
    from_dbh = asof - age

    # ---- 0: recorded planting dates, believable ones only
    planted = d.planted.to_numpy(float)
    planted = np.where((planted >= 1900) & (planted <= today + 0.02), planted, np.nan)
    day = pd.Series(np.round(planted, 3)).where(np.isfinite(planted))
    bulk = day.map(day.value_counts()).fillna(0).to_numpy() >= max(1000, 0.02 * np.isfinite(planted).sum())
    py = np.floor(planted)
    cnt = pd.Series(py[np.isfinite(py)]).value_counts()
    for yv, cn in cnt.items():      # a year far above the years around it is when records were entered
        around = [cnt.get(yv + k, 0) for k in range(-5, 6) if k and yv + k <= np.floor(today)]
        if cn >= 100 and cn > 5 * max(np.median(around), 1):
            bulk |= py == yv
    # a tree planted in year P cannot have a trunk much thicker than its species grows by the measurement
    too_thick = np.isfinite(from_dbh) & (from_dbh < planted - np.maximum(8.0, 0.5 * (asof - planted)))
    rec_ok = np.isfinite(planted) & ~bulk & ~too_thick
    log(f"street trees: {int(np.isfinite(planted).sum())} planting dates, {int((np.isfinite(planted) & bulk).sum())} bulk, "
        f"{int((np.isfinite(planted) & ~bulk & too_thick).sum())} contradicted by the trunk, {int(rec_ok.sum())} used")

    # ---- 1: planted after the 2015 census — a street tree whose record was made after the
    # census, with a young trunk, where the census counted no tree within 3 m, or a dead tree
    # / stump, or a tree thicker than this one is now (its predecessor)
    near = dist <= CENSUS_NEAR_M
    spot_free = ~near | ~c_alive | (np.nan_to_num(c_dbh, nan=0.0) >= np.nan_to_num(dbh_now, nan=99.0) + 3.0)
    young = np.isfinite(age) & (age <= (asof - 2015.4) + 4.0)
    after15 = street & ~rec_ok & (created > CENSUS_IMPORT) & young & spot_free
    lo = np.where(dist <= 100.0, c_date, 2016.0)             # when the census passed (its nearest record)
    lo = np.where(np.isfinite(lo), lo, 2016.0)
    at_planting = (dbh_meas <= PLANTING_IN) & ~d.bulk_created.to_numpy()   # record made at planting
    y_after = np.where(at_planting, created, np.clip(from_dbh, lo, np.fmax(created, lo)))

    # ---- the street and the ground
    st = street_year(x, y)
    ly = land_year(d.lon.values, d.lat.values)

    src = np.select([rec_ok, after15, np.isfinite(from_dbh) & (how == "species"), np.isfinite(from_dbh)], [0, 1, 2, 3], 4)
    # (4: no planting date and no trunk — nothing dates the tree; "ten years after the street",
    # the Bay rule, put park trees of Lower Manhattan in 1668. They are left out.)
    year = np.select([src == 0, src == 1, src >= 4], [planted, y_after, np.nan], from_dbh)
    undated = ~np.isfinite(year)                      # no planting date and no trunk
    bound = st - STREET_LEAD
    bounded = (src >= 2) & np.isfinite(bound) & (year < bound) & ~remnant
    year = np.where(bounded, bound, year)
    on_fill = np.isfinite(ly) & np.isfinite(year) & (year < ly + 1.0)
    year = np.where(on_fill, ly + 1.0, year)
    year = np.minimum(year, np.minimum(asof, today))
    d["year"], d["src"] = year, src.astype(np.uint8)
    d["confidence"] = np.where((src == 0) & ~on_fill, 0, 1).astype(np.uint8)
    d["bounded_by"] = np.select([on_fill, bounded], ["ground", "street"], "")
    d["street_year"], d["land_year"], d["remnant"], d["park"] = st, ly, remnant, park
    d["dbh_in"], d["dbh_measured"], d["asof"], d["curve"] = dbh_now, dbh_meas, asof, how
    d["height_m"] = np.clip(np.rint(np.clip(hgt, 3.0, 24.0) * 2) / 2, 3.0, 24.0)      # 0.5 m steps
    d["crown_m"] = np.clip(np.rint(np.clip(crn, 1.0, 7.0) * 4) / 4, 1.0, 7.0)         # 0.25 m steps
    d["form"] = form
    d["x"], d["y"] = x, y
    n_undated = int(undated.sum())
    n_bulk, n_thick = int((np.isfinite(planted) & bulk).sum()), int((np.isfinite(planted) & ~bulk & too_thick).sum())
    n_big_bounded = int((bounded & (dbh_meas * 2.54 >= REMNANT_CM)).sum())
    d = d[~undated].reset_index(drop=True)
    log(f"street trees: {n_undated} trees with neither planting date nor trunk left out; {len(d)} trees dated")

    # the year as stored: a recorded date to a tenth of a year, an estimate to the whole year;
    # this year's plantings show (as saplings) at the end of the slider
    yr = np.where(d.src.values == 0, np.floor(d.year.values * 10) / 10, np.floor(d.year.values))
    d["start_year"] = np.clip(yr, YEAR_MIN, CURRENT_YEAR - 0.05).astype(np.float32)
    assert np.isfinite(d.start_year.values).all()
    # the stored (floored) year never precedes the ground
    late = np.isfinite(d.land_year.values) & (d.start_year.values < d.land_year.values)
    d.loc[late, "start_year"] = np.ceil(d.land_year.values[late]).astype(np.float32)

    d.drop(columns=["x", "y"]).to_parquet(WORK / "trees.parquet", compression="zstd")
    sizes = write_outputs(d)
    coverage_grid(d)
    report(d, sizes, dict(living=n_living, outside=n_outside, doubles=n_dupe, undated=n_undated,
                          planting_dates=int(np.isfinite(planted).sum()), planting_dates_bulk=n_bulk,
                          planting_dates_too_thick=n_thick, counted_in_2015=int(same.sum()),
                          big_trunks_not_remnant_bounded=n_big_bounded, today=round(today, 2)))


def _columns(t: pd.DataFrame) -> dict:
    return {
        "position_q|shuffle": np.column_stack([t.qx.values, t.qy.values]).astype(np.int32).ravel(),
        "start_year": t.start_year.values.astype(np.float32),
        "height": t.height_m.values.astype(np.float32),
        "crown": t.crown_m.values.astype(np.float32),
        "form": t.form.values.astype(np.uint8),
        "confidence": t.confidence.values.astype(np.uint8),
        "source": t.src.values.astype(np.uint8),
        "park": t.park.values.astype(np.uint8),
    }


META = {"position_scale": POS_SCALE, "forms": ["broadleaf", "conifer", "palm"], "sources": EVIDENCE,
        "source": "NYC Parks Forestry Tree Points (ForMS 2.0, NYC Open Data hn5i-inap) + 2015 Street Tree Census (uvpi-gqnh)"}
ATTRIBUTION = {"forms": "NYC Department of Parks & Recreation, Forestry Tree Points and Planting Spaces (ForMS 2.0), NYC Open Data",
               "census_2015": "NYC Department of Parks & Recreation, TreesCount! 2015 Street Tree Census, NYC Open Data",
               "growth": "McPherson, van Doorn & Peper 2016, Urban Tree Database, USDA Forest Service RDS-2016-0005"}


def write_outputs(d: pd.DataFrame) -> dict:
    """Manhattan -> street-trees.bin.gz (always loaded); the other boroughs -> z12 tiles.
    Trees are written west to east (the position column then gzips best)."""
    import shutil
    from export_columnar import write_columnar
    d = d.sort_values(["qx", "qy"])
    m = d[d.boro == 1]
    out = VIEWER_DATA / "street-trees.bin.gz"
    _, gz_m = write_columnar(out, _columns(m), origin=DECO_ORIGIN, counts={"features": int(len(m))}, meta=META)
    log(f"street trees: {out.name}: {len(m)} trees, {gz_m / 1e6:.2f} MB")
    r = d[d.boro != 1]
    root = VIEWER_DATA / "region-trees"
    if root.exists():
        shutil.rmtree(root)
    n = 2 ** TILE_Z
    tx = np.floor((r.lon.values + 180) / 360 * n).astype(int)
    lat = np.radians(r.lat.values)
    ty = np.floor((1 - np.log(np.tan(lat) + 1 / np.cos(lat)) / np.pi) / 2 * n).astype(int)
    index, total = [], 0
    for (tx_, ty_), ix in pd.DataFrame({"x": tx, "y": ty}).groupby(["x", "y"]).indices.items():
        t = r.iloc[ix]
        _, gz = write_columnar(root / str(TILE_Z) / str(tx_) / f"{ty_}.bin.gz", _columns(t), origin=DECO_ORIGIN,
                               counts={"features": int(len(t))}, meta=META)
        index.append({"x": int(tx_), "y": int(ty_), "n": int(len(t)), "bytes": int(gz)})
        total += gz
    (root / "index.json").write_text(json.dumps({
        "z": TILE_Z, "origin": list(DECO_ORIGIN), "position_scale": POS_SCALE,
        "forms": ["broadleaf", "conifer", "palm"], "sources": EVIDENCE, "attribution": ATTRIBUTION,
        "tiles": index}, separators=(",", ":")))
    total += (root / "index.json").stat().st_size
    log(f"street trees: region-trees/: {len(r)} trees in {len(index)} z{TILE_Z} tiles, {total / 1e6:.2f} MB "
        f"(largest {max(i['n'] for i in index)} trees, {max(i['bytes'] for i in index) / 1e3:.0f} kB); "
        f"both outputs {(total + gz_m) / 1e6:.2f} MB")
    return {"manhattan_bytes": int(gz_m), "tiles_bytes": int(total), "tiles": len(index)}


def _fine_cells(lon, lat, transform):
    X = np.radians(lon) * 6378137.0
    Y = 6378137.0 * np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))
    c = np.floor((X - transform.c) / transform.a).astype(int)
    r = np.floor((transform.f - Y) / -transform.e).astype(int)
    return r, c


def coverage_grid(d: pd.DataFrame):
    """Inventory trees per cell of the 29 m terrain grid (uint8, shape of grid_detail_*.npy)."""
    from terrain_grid import grid_def
    g = grid_def("detail")
    r, c = _fine_cells(d.lon.values, d.lat.values, g["transform"])
    ok = (c >= 0) & (r >= 0) & (c < g["cols"]) & (r < g["rows"])
    cnt = np.zeros((g["rows"], g["cols"]), np.uint16)
    np.add.at(cnt, (r[ok], c[ok]), 1)
    np.save(WORK / "grid_detail_streettrees.npy", np.minimum(cnt, 255).astype(np.uint8))
    log(f"street trees: {int((cnt > 0).sum())} terrain cells hold inventory trees -> {WORK / 'grid_detail_streettrees.npy'}")


def inventory_mask(transform, shape, reach: int = 1) -> np.ndarray:
    """For the terrain stage: True where a cell of the grid (`transform`: its affine in web
    mercator, `shape`) holds an inventory tree or lies within `reach` cells of one — canopy
    pixels the real trees already stand for. Empty if this stage has not run."""
    out = np.zeros(shape, bool)
    p = WORK / "trees.parquet"
    if not p.exists():
        return out
    t = pd.read_parquet(p, columns=["lon", "lat"])
    r, c = _fine_cells(t.lon.values, t.lat.values, transform)
    ok = (c >= 0) & (r >= 0) & (c < shape[1]) & (r < shape[0])
    out[r[ok], c[ok]] = True
    if reach > 0:
        from scipy.ndimage import binary_dilation
        out = binary_dilation(out, structure=np.ones((2 * reach + 1, 2 * reach + 1), bool))
    return out


def _whole(years: np.ndarray) -> np.ndarray:
    """The calendar year of a stored year (this year's plantings are stored at CURRENT_YEAR - 0.05,
    the end of the slider)."""
    return np.floor(np.asarray(years, float) + 0.051)


def _histogram(years: np.ndarray) -> dict:
    dec = (np.floor(_whole(years) / 10) * 10).astype(int)
    return {int(k): int(v) for k, v in zip(*np.unique(dec, return_counts=True))}


def _spikes(years: np.ndarray) -> list:
    """Years holding more than 2.5 times the median of the five years on either side."""
    cnt = pd.Series(_whole(years).astype(int)).value_counts()
    out = []
    for yv, cn in cnt.items():
        around = [cnt.get(yv + k, 0) for k in range(-5, 6) if k and yv + k <= CURRENT_YEAR]
        if cn >= 2000 and cn > 2.5 * max(np.median(around), 1):
            out.append([int(yv), int(cn), int(np.median(around))])
    return sorted(out)


def report(d, sizes, counts):
    from common import BOROUGHS
    rep = {"trees": int(len(d)), **counts, **sizes,
           "boroughs": {BOROUGHS[str(b)]: {"trees": int(len(t)), "park": int(t.park.sum()),
                                           "evidence": np.bincount(t.src, minlength=len(EVIDENCE)).tolist()}
                        for b, t in d.groupby("boro")},
           "evidence": dict(zip(EVIDENCE, np.bincount(d.src, minlength=len(EVIDENCE)).tolist())),
           "exact": int((d.confidence == 0).sum()),
           "bounded_by": d.bounded_by.value_counts().to_dict(),
           "remnants": int(d.remnant.sum()),
           "curve": d.curve.value_counts().to_dict(),
           "forms": np.bincount(d.form, minlength=3).tolist(),
           "decades": _histogram(d.start_year.values), "spikes": _spikes(d.start_year.values),
           "years": {int(k): int(v) for k, v in zip(*np.unique(_whole(d.start_year.values[d.start_year.values >= 1990]).astype(int), return_counts=True))},
           "pooled_years_per_cm_at_cm": getattr(growth_tables, "pooled_rate", {}),
           "year_percentiles": [round(float(v), 1) for v in np.percentile(d.start_year, [1, 5, 25, 50, 75, 95, 99])]}
    (WORK / "report.json").write_text(json.dumps(rep, indent=1))
    log(f"street trees: report -> {WORK / 'report.json'}")


# ---------------------------------------------------------------- checks on the built files
def check() -> bool:
    """The invariants, read back from the files the viewer loads."""
    from common import BOROUGHS
    from export_columnar import read_bayt
    files = [VIEWER_DATA / "street-trees.bin.gz"]
    idx = json.loads((VIEWER_DATA / "region-trees" / "index.json").read_text())
    files += [VIEWER_DATA / "region-trees" / str(idx["z"]) / str(t["x"]) / f"{t['y']}.bin.gz" for t in idx["tiles"]]
    lon, lat, yr, src, conf, hg, cr, fm, where = [], [], [], [], [], [], [], [], []
    size = (VIEWER_DATA / "region-trees" / "index.json").stat().st_size
    need = {"position_q", "start_year", "height", "crown", "form", "confidence"}
    for k, f in enumerate(files):
        h, c = read_bayt(f)
        assert need <= set(c), f"{f}: columns {sorted(c)}"
        n = h["counts"]["features"]
        assert all(len(c[k_]) == n for k_ in need - {"position_q"}) and len(c["position_q"]) == 2 * n, f
        assert c["position_q"].dtype == np.dtype("<i4") and c["start_year"].dtype == np.dtype("<f4"), f
        if k:
            assert h["origin"] == idx["origin"] and idx["tiles"][k - 1]["n"] == n, f
        s = h["meta"]["position_scale"]
        lon.append(h["origin"][0] + c["position_q"][0::2] * s)
        lat.append(h["origin"][1] + c["position_q"][1::2] * s)
        assert int(c["source"].max(initial=0)) < len(h["meta"]["sources"]) and int(c["form"].max(initial=0)) < 3, f
        yr.append(c["start_year"]); src.append(c["source"]); conf.append(c["confidence"])
        hg.append(c["height"]); cr.append(c["crown"]); fm.append(c["form"])
        where.append(np.full(n, 0 if k == 0 else 1, np.uint8))
        size += f.stat().st_size
    lon, lat, yr, src, conf = map(np.concatenate, (lon, lat, yr, src, conf))
    hg, cr, fm, where = map(np.concatenate, (hg, cr, fm, where))
    boro = boroughs_of(lon, lat)
    ly = land_year(lon, lat)
    n = len(yr)
    res = {
        "trees": n, "files": len(files), "megabytes": round(size / 1e6, 2),
        "boroughs": {BOROUGHS[str(b)]: int((boro == b).sum()) for b in range(1, 6)},
        "outside the boroughs": int((boro == 0).sum()),
        "Manhattan trees in the tiles / others in the Manhattan file": [int(((boro == 1) & (where == 1)).sum()),
                                                                       int(((boro != 1) & (where == 0)).sum())],
        "years outside 1609-2026": int(((yr < YEAR_MIN) | (yr > CURRENT_YEAR) | ~np.isfinite(yr)).sum()),
        "start >= end": 0,   # the format has no end year: every tree stands to the present
        "before its ground": int((np.isfinite(ly) & (yr < ly)).sum()),
        "on made land": int(np.isfinite(ly).sum()),
        "height outside 3-24 m / crown outside 1-7 m": [int(((hg < 3) | (hg > 24)).sum()), int(((cr < 1) | (cr > 7)).sum())],
        "forms": np.bincount(fm, minlength=3).tolist(),
        "evidence": {e: [int(c_), round(100 * c_ / n, 1)] for e, c_ in zip(EVIDENCE, np.bincount(src, minlength=len(EVIDENCE)))},
        "exact": int((conf == 0).sum()),
        "decades": _histogram(yr), "spikes (year, trees, median of the years around)": _spikes(yr),
        "per year since 2000": {int(k): int(v) for k, v in zip(*np.unique(_whole(yr[yr >= 2000]).astype(int), return_counts=True))},
        "doubles (same stored position)": int(n - len(np.unique(np.round(lon / POS_SCALE).astype(np.int64) * 1_000_003
                                                                  + np.round(lat / POS_SCALE).astype(np.int64)))),
    }
    print(json.dumps(res, indent=1))
    bad = (res["years outside 1609-2026"] or res["before its ground"] or res["outside the boroughs"]
           or any(res["Manhattan trees in the tiles / others in the Manhattan file"])
           or any(res["height outside 3-24 m / crown outside 1-7 m"]) or size > 9e6)
    log("street trees: checks " + ("FAILED" if bad else "passed"))
    (WORK / "check.json").write_text(json.dumps(res, indent=1))
    return not bad


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in ("download", "all"):
        download(sys.argv[2:] or None)
    if cmd in ("build", "all"):
        build()
    if cmd in ("build", "check", "all"):
        if not check():
            raise SystemExit(1)


if __name__ == "__main__":
    main()
