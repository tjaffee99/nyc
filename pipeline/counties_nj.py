"""New Jersey counties around the city: every building footprint with the construction year of
the property tax record (MOD-IV) of the parcel it stands on.

    ../.venv/bin/python counties_nj.py                # all five counties, cached steps skipped
    ../.venv/bin/python counties_nj.py hudson bergen  # some
    ../.venv/bin/python counties_nj.py --force hudson # rebuild the output from the cached downloads

Sources (details, licences and extract dates: data/research/counties_nj.md)
  footprints  data/raw/overture/<release>/region_building.parquet (OpenStreetMap, Microsoft ML
              Buildings, Esri Community Maps), clipped to the TIGER county outline, >= 12 m2
  years       "Parcels and MOD-IV Composite of NJ" (NJ Office of GIS), ArcGIS feature service
              Parcels_Composite_NJ_WM, layer 0: parcel polygons with the matched MOD-IV tax-list
              record (YR_CONSTR, PROP_CLASS, BLDG_DESC, DWELL ...). Paged by OBJECTID per county
              (PCL_MUN = county code + municipality code) into data/raw/counties_nj/parcels/.
  historic    NJ Historic Preservation Office "Historic Properties of New Jersey" (NJDEP): used
              for names and register status only - the layer carries no construction date.

Method
  footprint -> the parcel containing its representative point -> that parcel's YR_CONSTR.
  Where parcel polygons overlap (condominium units and duplicate lots are stacked) the parcel
  with a year wins, then the smallest. On a parcel with several footprints the year belongs to
  the main building, taken to be the largest footprint: the others get the same year and
  `secondary` = True (garages, sheds - or the other buildings of a campus / an estate).
  Nothing is imputed here: `year_raw` is the tax list's year (NaN where it has none or 0),
  `heap` flags the years that are placeholders in that county (nyc_buildings.find_heaps'
  rule), and the building stage decides what to do with them.

Output  data/interim/counties/nj_<county>.parquet  (GeoParquet, EPSG:4326, one row per footprint)
        data/interim/counties/nj_<county>_report.json  (counts, heaps, histogram - the numbers
        of data/research/counties_nj.md)
"""
from __future__ import annotations

import gzip
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from common import CURRENT_YEAR, INTERIM, NYC_CRS, OVERTURE_RELEASE, RAW, log

UA = "NYCThroughTime-research/0.1"
PARCEL_SERVICE = ("https://services2.arcgis.com/XVOqAjTOJ5P6ngMu/arcgis/rest/services/"
                  "Parcels_Composite_NJ_WM/FeatureServer/0")
PARCEL_FIELDS = ("OBJECTID,PAMS_PIN,PCL_MUN,PCLBLOCK,PCLLOT,PCLQCODE,PROP_CLASS,COUNTY,MUN_NAME,PROP_LOC,"
                 "BLDG_DESC,LAND_DESC,FAC_NAME,PROP_USE,BLDG_CLASS,YR_CONSTR,DWELL,COMM_DWELL,IMPRVT_VAL,"
                 "CALC_ACRE,ADD_LOTS1,PCLLASTUPD,PCL_PBDATE")
HPO_SERVICE = "https://mapsdep.nj.gov/arcgis/rest/services/Features/Land/MapServer/55"

# key -> (name, state+county FIPS, MOD-IV county code = first two digits of PCL_MUN)
COUNTIES = {
    "hudson": ("Hudson", "34017", "09"),
    "bergen": ("Bergen", "34003", "02"),
    "essex": ("Essex", "34013", "07"),
    "union": ("Union", "34039", "20"),
    "passaic": ("Passaic", "34031", "16"),
    # the outer round (2026-11-11): footprints from outer_building.parquet
    "hunterdon": ("Hunterdon", "34019", "10"),
    "mercer": ("Mercer", "34021", "11"),
    "middlesex": ("Middlesex", "34023", "12"),
    "monmouth": ("Monmouth", "34025", "13"),
    "morris": ("Morris", "34027", "14"),
    "ocean": ("Ocean", "34029", "15"),
    "somerset": ("Somerset", "34035", "18"),
    "sussex": ("Sussex", "34037", "19"),
}
LEGACY = ("hudson", "bergen", "essex", "union", "passaic")   # footprints from region_building.parquet
RAWDIR = RAW / "counties_nj"
OUTDIR = INTERIM / "counties"
MIN_AREA = 12.0          # m2: smaller outlines are dropped
YEAR_LO, YEAR_HI = 1650, CURRENT_YEAR
# a municipality's heap year: at least this many main buildings and this share of its dated ones
HEAP_MIN, HEAP_SHARE = 25, 0.005


def _get(url, params, tries=6, timeout=180):
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=timeout)
            if r.status_code == 200:
                d = r.json()
                if "error" not in d:
                    return d
                err = d["error"]
            else:
                err = r.status_code
        except (requests.RequestException, ValueError) as e:  # noqa: PERF203
            err = e
        time.sleep(3 * (i + 1))
    raise RuntimeError(f"{url}: {err}")


# ---------------------------------------------------------------------------------------------
# 1. parcels + MOD-IV (cached pages of the feature service)
# ---------------------------------------------------------------------------------------------
def download_parcels(key: str) -> Path:
    """Page the county's parcels (keyset paging on OBJECTID) into gzipped GeoJSON pages.
    Parcels without a matched MOD-IV record have COUNTY = NULL, so the county is selected by
    the parcel's own municipality code."""
    name, _, code = COUNTIES[key]
    d = RAWDIR / "parcels" / key
    d.mkdir(parents=True, exist_ok=True)
    done = d / "done.json"
    if done.exists():
        return d
    where = f"PCL_MUN LIKE '{code}%'"
    total = _get(PARCEL_SERVICE + "/query", {"where": where, "returnCountOnly": "true", "f": "json"})["count"]
    meta = _get(PARCEL_SERVICE, {"f": "json"})
    pages = sorted(d.glob("p_*.geojson.gz"))
    last, n = 0, 0
    for p in pages:  # resume: the last page's highest OBJECTID
        with gzip.open(p, "rt") as f:
            feats = json.load(f)["features"]
        n += len(feats)
        last = max(last, max(x["properties"]["OBJECTID"] for x in feats))
    while True:
        g = _get(PARCEL_SERVICE + "/query", {
            "where": f"{where} AND OBJECTID > {last}", "outFields": PARCEL_FIELDS, "orderByFields": "OBJECTID",
            "resultRecordCount": 2000, "outSR": 4326, "geometryPrecision": 7, "f": "geojson"})
        feats = g.get("features", [])
        if not feats:
            break
        first = feats[0]["properties"]["OBJECTID"]
        last = feats[-1]["properties"]["OBJECTID"]
        with gzip.open(d / f"p_{first:09d}.geojson.gz", "wt") as f:
            json.dump(g, f)
        n += len(feats)
        if (n // 2000) % 10 == 0:
            log(f"parcels {name}: {n} / {total}")
    if n != total:
        raise RuntimeError(f"parcels {name}: got {n}, the service counts {total}")
    ei = meta.get("editingInfo", {})
    done.write_text(json.dumps({
        "county": name, "where": where, "parcels": n, "service": PARCEL_SERVICE,
        "downloaded": time.strftime("%Y-%m-%d"),
        "service_data_last_edit": time.strftime("%Y-%m-%d", time.gmtime(ei.get("dataLastEditDate", 0) / 1000)),
        "service_last_edit": time.strftime("%Y-%m-%d", time.gmtime(ei.get("lastEditDate", 0) / 1000)),
    }, indent=1))
    log(f"parcels {name}: {n} parcels cached in {d}")
    return d


def load_parcels(key: str):
    """The cached pages as one GeoDataFrame (EPSG:4326), kept as a GeoParquet beside them."""
    import geopandas as gpd
    out = RAWDIR / f"parcels_{key}.parquet"
    d = download_parcels(key)
    if out.exists() and out.stat().st_mtime >= (d / "done.json").stat().st_mtime:
        return gpd.read_parquet(out)
    parts = []
    for p in sorted(d.glob("p_*.geojson.gz")):
        with gzip.open(p, "rt") as f:
            feats = json.load(f)["features"]
        feats = [x for x in feats if x.get("geometry")]
        if feats:
            parts.append(gpd.GeoDataFrame.from_features(feats, crs=4326))
    g = pd.concat(parts, ignore_index=True)
    g = gpd.GeoDataFrame(g, geometry="geometry", crs=4326)
    for c in ("YR_CONSTR", "DWELL", "COMM_DWELL", "IMPRVT_VAL", "CALC_ACRE"):
        g[c] = pd.to_numeric(g[c], errors="coerce").astype("float32" if c != "IMPRVT_VAL" else "float64")
    for c in ("PCLLASTUPD", "PCL_PBDATE"):
        g[c] = pd.to_datetime(pd.to_numeric(g[c], errors="coerce"), unit="ms")
    g = g.drop_duplicates("OBJECTID").reset_index(drop=True)
    g.to_parquet(out)
    log(f"parcels {COUNTIES[key][0]}: {len(g)} polygons -> {out.name}")
    return g


def county_outlines():
    """TIGER 2024 outlines of the counties (EPSG:4326), indexed by key."""
    import geopandas as gpd
    fips = {v[1][2:]: k for k, v in COUNTIES.items()}
    c = gpd.read_file(f"zip://{RAW / 'tiger' / 'tl_2024_us_county.zip'}",
                      where="STATEFP='34' AND COUNTYFP IN ({})".format(",".join(f"'{f}'" for f in fips)))
    c["key"] = c.COUNTYFP.map(fips)
    return c.set_index("key").geometry.to_crs(4326)


# ---------------------------------------------------------------------------------------------
# 2. where each Overture height comes from (the region extract keeps only the first source)
# ---------------------------------------------------------------------------------------------
def download_height_sources(key: str, outline) -> Path:
    """id -> dataset behind Overture's `height` (USGS Lidar | Microsoft ML Buildings |
    OpenStreetMap ...) for the county's bounding box, read from the Overture release on S3."""
    out = RAWDIR / f"overture_height_src_{key}.parquet"
    if out.exists():
        return out
    import duckdb
    RAWDIR.mkdir(parents=True, exist_ok=True)
    b = outline.bounds
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs; SET memory_limit='1500MB'; SET threads=4;")
    con.execute("CREATE OR REPLACE SECRET overture (TYPE s3, PROVIDER config, KEY_ID '', SECRET '', REGION 'us-west-2');")
    src = f"s3://overturemaps-us-west-2/release/{OVERTURE_RELEASE}/theme=buildings/type=building/*"
    stage = out.with_name(f"_stage_{out.name}")
    con.execute(f"""
    COPY (
      SELECT id, sources[1].record_id AS record_id,
             CASE WHEN height IS NULL THEN NULL
                  ELSE coalesce(list_filter(sources, lambda x: x.property = '/properties/height')[1].dataset,
                                sources[1].dataset) END AS height_ds,
             CASE WHEN num_floors IS NULL THEN NULL
                  ELSE coalesce(list_filter(sources, lambda x: x.property = '/properties/num_floors')[1].dataset,
                                sources[1].dataset) END AS floors_ds
      FROM read_parquet('{src}', hive_partitioning=1)
      WHERE bbox.xmin < {b[2]} AND bbox.xmax > {b[0]} AND bbox.ymin < {b[3]} AND bbox.ymax > {b[1]}
    ) TO '{stage}' (FORMAT parquet);""")
    stage.replace(out)
    log(f"height sources {COUNTIES[key][0]}: {con.execute(f'SELECT count(*) FROM {chr(39)}{out}{chr(39)}').fetchone()[0]} rows")
    return out


# ---------------------------------------------------------------------------------------------
# 3. footprints of one county
# ---------------------------------------------------------------------------------------------
HEIGHT_SRC = {"USGS Lidar": "usgs_lidar", "Microsoft ML Buildings": "ms_ml", "OpenStreetMap": "osm",
              "Esri Community Maps": "esri"}
FOOTPRINT_SRC = {"OpenStreetMap": "osm", "Microsoft ML Buildings": "ms_ml", "Esri Community Maps": "esri"}


def _polygonal(g):
    """A valid polygon / multipolygon from an invalid outline (None if nothing is left)."""
    import shapely
    v = shapely.make_valid(g)
    if v.geom_type in ("Polygon", "MultiPolygon"):
        return v
    parts = [p for p in shapely.get_parts(v) if p.geom_type in ("Polygon", "MultiPolygon")]
    return shapely.union_all(parts) if parts else None


def load_footprints(key: str, outline):
    """Overture footprints whose inside point lies in the county, >= MIN_AREA, valid."""
    import geopandas as gpd
    import pyarrow.parquet as pq
    import shapely
    b = outline.bounds
    path = RAW / "overture" / OVERTURE_RELEASE / ("region_building.parquet" if key in LEGACY else "outer_building.parquet")
    t = pq.read_table(path, filters=[("lon", ">=", b[0] - 0.01), ("lon", "<=", b[2] + 0.01),
                                     ("lat", ">=", b[1] - 0.01), ("lat", "<=", b[3] + 0.01)])
    df = t.to_pandas()
    geom = shapely.from_wkb(df.pop("geometry").values)
    stats = {"overture_in_bbox": len(df)}
    bad = ~shapely.is_valid(geom)
    stats["invalid_repaired"] = int(bad.sum())
    for i in np.flatnonzero(bad):
        geom[i] = _polygonal(geom[i])
    ok = ~(shapely.is_missing(geom) | shapely.is_empty(geom))
    pt = shapely.point_on_surface(geom)
    shapely.prepare(outline)
    ok &= shapely.contains(outline, pt)
    df, geom, pt = df[ok].reset_index(drop=True), geom[ok], pt[ok]
    stats["in_county"] = len(df)
    g = gpd.GeoDataFrame(df, geometry=geom, crs=4326)
    g["area_m2"] = g.geometry.to_crs(NYC_CRS).area.round(1).values
    small = g.area_m2 < MIN_AREA
    stats["dropped_under_12m2"] = int(small.sum())
    g, pt = g[~small].reset_index(drop=True), pt[~small.values]
    g["px"], g["py"] = shapely.get_x(pt), shapely.get_y(pt)
    try:
        hs = pd.read_parquet(download_height_sources(key, outline)).drop_duplicates("id").set_index("id")
    except Exception as e:  # noqa: BLE001  the S3 read is optional in the outer tier
        log(f"height sources {key}: skipped ({str(e)[:80]})")
        hs = pd.DataFrame({"height_ds": [], "record_id": []}, index=pd.Index([], name="id"))
    g["height_src"] = g.id.map(hs.height_ds).map(HEIGHT_SRC).where(g.height.notna(), "").fillna("overture")
    g["osm_id"] = g.id.map(hs.record_id).where(g.source_dataset == "OpenStreetMap")
    return g, stats


# ---------------------------------------------------------------------------------------------
# 4. the parcel under each footprint
# ---------------------------------------------------------------------------------------------
def valid_year(y):
    y = pd.to_numeric(y, errors="coerce").astype("float64")
    return y.where((y >= YEAR_LO) & (y <= YEAR_HI))


STOREYS = r"^\s*(\d{1,3}(?:\.\d)?)\s*-?\s*S(?:T|TY|TORY|TORIES)?(?=$|[-\s/,.&]|[A-Z])"


def _mode(df, key, col, name):
    """Most frequent non-null value of `col` per `key` (ties: the smallest)."""
    c = df[df[col].notna()].groupby([key, col]).size().rename("n").reset_index()
    c = c.sort_values([key, "n", col], ascending=[True, False, True]).drop_duplicates(key)
    return c.set_index(key)[col].rename(name)


def lot_table(par):
    """One row per tax lot (municipality + block + lot). A condominium is one lot with a
    record - and a small symbolic polygon - per unit (qualifier C0001 ...): the lot's year is
    the units' most frequent valid year."""
    p = pd.DataFrame(par.drop(columns="geometry"))
    p["lot"] = p.PCL_MUN.fillna("") + "_" + p.PCLBLOCK.fillna("") + "_" + p.PCLLOT.fillna("")
    p["year"] = valid_year(p.YR_CONSTR)
    p["unit"] = p.PCLQCODE.fillna("").str.strip() != ""
    p["desc_st"] = p.BLDG_DESC.where(p.BLDG_DESC.fillna("").str.upper().str.match(STOREYS))
    gb = p.groupby("lot")
    t = pd.DataFrame({"lot_records": gb.size(), "lot_units": gb.unit.sum(), "lot_year_min": gb.year.min(),
                      "lot_year_max": gb.year.max(), "lot_dwell": gb.DWELL.sum(min_count=1)})
    t = t.join(_mode(p, "lot", "year", "lot_year")).join(_mode(p, "lot", "PROP_CLASS", "lot_class"))
    t = t.join(_mode(p, "lot", "desc_st", "lot_desc_st")).join(_mode(p, "lot", "BLDG_DESC", "lot_desc"))
    t = t.join(_mode(p, "lot", "FAC_NAME", "lot_fac"))
    return t, p


def join_parcels(g, par):
    """For every footprint the tax lot of the parcel polygon containing its inside point
    (the smallest polygon where several overlap) and that lot's year:
      modiv        the record of the polygon itself
      modiv_condo  the lot is a condominium: the most frequent valid year of its unit records
      modiv_lot    the polygon's record has no year but another record of the same lot has"""
    import shapely
    pgeom = par.geometry.values.copy()
    for i in np.flatnonzero(~shapely.is_valid(pgeom)):
        pgeom[i] = _polygonal(pgeom[i])
    keep = ~(shapely.is_missing(pgeom) | shapely.is_empty(pgeom))
    par = par[keep].reset_index(drop=True)
    pgeom = pgeom[keep]
    lots, p = lot_table(par)
    parea = par.set_geometry(pgeom).geometry.to_crs(NYC_CRS).area.values
    tree = shapely.STRtree(pgeom)
    fi, pi = tree.query(shapely.points(g.px.values, g.py.values), predicate="within")
    pr = pd.DataFrame({"fp": fi, "par": pi, "parea": parea[pi], "oid": par.OBJECTID.values[pi]})
    win = pr.sort_values(["fp", "parea", "oid"]).drop_duplicates("fp").set_index("fp")
    rec = p.iloc[win.par.values].reset_index(drop=True)
    rec.index = win.index
    rec = rec.join(lots, on="lot")
    condo = rec.lot_units >= 1
    year = rec.year.where(~condo, rec.lot_year)
    src = pd.Series(np.where(condo, "modiv_condo", "modiv"), index=rec.index).where(year.notna(), "")
    fill = year.isna() & rec.lot_year.notna()
    year = year.where(~fill, rec.lot_year)
    src = src.where(~fill, "modiv_lot")
    mun = _mode(p, "PCL_MUN", "MUN_NAME", "mun")          # unmatched parcels have no name
    out = pd.DataFrame(index=np.arange(len(g)))
    out["year_raw"] = year.reindex(out.index)
    out["year_src"] = src.reindex(out.index).fillna("")
    out["PROP_CLASS"] = rec.PROP_CLASS.where(~condo, rec.lot_class).fillna(rec.lot_class).reindex(out.index)
    out["MUN_NAME"] = rec.PCL_MUN.map(mun).reindex(out.index)
    out["BLDG_DESC"] = rec.BLDG_DESC.where(~condo, rec.lot_desc_st.fillna(rec.lot_desc)).reindex(out.index)
    out["FAC_NAME"] = rec.FAC_NAME.where(~condo, rec.lot_fac).reindex(out.index)
    out["DWELL"] = rec.DWELL.where(~condo, rec.lot_dwell).reindex(out.index)
    out["YR_CONSTR"] = rec.YR_CONSTR.reindex(out.index)
    out["PAMS_PIN"] = rec.PAMS_PIN.reindex(out.index)
    out["lot"] = rec.lot.reindex(out.index).fillna("")
    out["condo_units"] = rec.lot_units.where(condo, 0).reindex(out.index).fillna(0).astype(int)
    out["year_spread"] = (rec.lot_year_max - rec.lot_year_min).where(condo).reindex(out.index)
    out["in_parcel"] = out.lot != ""
    return out


def find_heaps_scaled(year, min_count):
    """nyc_buildings.find_heaps' rule for one group, with the minimum count as a parameter
    (the city's 300 suits a borough, not a town of 3,000 buildings): a year up to 1990 whose
    count is at least `min_count` and more than 3x the median of the non-round, not yet
    flagged years within +/- 4; round years first, then the others, twice."""
    y = np.asarray(year, float)
    y = y[np.isfinite(y)].astype(int)
    cnt = dict(zip(*np.unique(y, return_counts=True)))
    flagged: set[int] = set()
    for rnd in (True, False, False):
        for v in sorted(cnt):
            if v > 1990 or v in flagged or (v % 5 == 0) != rnd or cnt[v] < min_count:
                continue
            nb = [cnt.get(u, 0) for u in range(v - 4, v + 5) if u != v and u % 5 and u not in flagged]
            if nb and cnt[v] > 3 * max(float(np.median(nb)), 1.0):
                flagged.add(v)
    return flagged


def use_codes(cls, dwell, stack_n, fac, ov_class, ov_subtype):
    """building_binary.USE_CATEGORIES (0 unknown, 1 single-family home, 2 residential,
    3 commercial, 4 office, 5 industrial, 6 government / civic, 7 other) from the MOD-IV
    property class, Overture's class where the tax list says nothing."""
    cls = pd.Series(cls).fillna("").str.strip().str.upper().values
    fac = pd.Series(fac).fillna("").str.upper()
    oc = pd.Series(ov_class).fillna("").values
    osub = pd.Series(ov_subtype).fillna("").values
    use = np.zeros(len(cls), np.uint8)
    ov = np.zeros(len(cls), np.uint8)
    ov[np.isin(osub, ["residential"])] = 2
    ov[np.isin(oc, ["house", "detached", "bungalow", "semidetached_house", "cabin", "farm"])] = 1
    ov[np.isin(oc, ["apartments", "residential", "terrace", "dormitory"])] = 2
    ov[np.isin(osub, ["commercial"]) | np.isin(oc, ["retail", "commercial", "hotel", "supermarket", "kiosk"])] = 3
    ov[oc == "office"] = 4
    ov[np.isin(osub, ["industrial"]) | np.isin(oc, ["industrial", "warehouse", "factory", "manufacture"])] = 5
    ov[np.isin(osub, ["civic", "education", "religious", "medical"])
       | np.isin(oc, ["school", "church", "hospital", "university", "college", "civic", "government", "public",
                      "fire_station", "library", "kindergarten", "chapel", "cathedral", "synagogue", "mosque",
                      "temple", "train_station"])] = 6
    ov[np.isin(osub, ["outbuilding", "transportation", "agricultural", "service", "entertainment", "military"])
       | np.isin(oc, ["garage", "garages", "shed", "carport", "parking", "roof", "hangar", "barn", "greenhouse"])] = 7
    use[cls == "2"] = 2
    use[(cls == "2") & (np.asarray(dwell, float) == 1) & (np.asarray(stack_n) <= 1)] = 1
    use[cls == "4C"] = 2
    use[cls == "4A"] = 3
    use[(cls == "4A") & (ov == 4)] = 4
    use[cls == "4B"] = 5
    use[np.isin(cls, ["15A", "15B", "15C", "15D", "15E"])] = 6
    use[(cls == "15C") & fac.str.contains("HOUSING|APARTMENT|RESIDEN").values] = 2
    other = np.isin(cls, ["1", "3A", "3B", "5A", "5B", "6A", "6B", "6C", "15F"])
    use[other] = np.where(ov[other] > 0, ov[other], 7)
    none = cls == ""
    use[none] = ov[none]
    return use


# ---------------------------------------------------------------------------------------------
# 5. Wikidata: inception / opening year of buildings (the tax list has none for most exempt
#    property - stations, courthouses, churches). Goes to `year_hist`, never into `year_raw`.
# ---------------------------------------------------------------------------------------------
WD_SPARQL = "https://query.wikidata.org/sparql"


def _sparql(q, tries=4):
    for i in range(tries):
        try:
            r = requests.post(WD_SPARQL, data={"query": q}, timeout=200,
                              headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
            if r.status_code == 200:
                return r.json()["results"]["bindings"]
            err = r.status_code
        except (requests.RequestException, ValueError) as e:  # noqa: PERF203
            err = e
        log(f"wikidata: {err}, retrying")
        time.sleep(15 * (i + 1))
    raise RuntimeError(f"wikidata: {err}")


def download_wikidata(key: str, outline) -> Path:
    """Every Wikidata item with coordinates in the county's box and an inception (P571) or
    opening (P1619) date."""
    out = RAWDIR / "wikidata" / f"{key}.json"
    if out.exists():
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    b = [round(v, 4) for v in outline.bounds]
    rows = _sparql(f"""SELECT ?item ?label ?coord ?inception ?opened ?nrhp ?class ?gone WHERE {{
      SERVICE wikibase:box {{ ?item wdt:P625 ?coord .
        bd:serviceParam wikibase:cornerSouthWest "Point({b[0]} {b[1]})"^^geo:wktLiteral .
        bd:serviceParam wikibase:cornerNorthEast "Point({b[2]} {b[3]})"^^geo:wktLiteral . }}
      {{ ?item wdt:P571 ?inception }} UNION {{ ?item wdt:P1619 ?opened }}
      OPTIONAL {{ ?item wdt:P649 ?nrhp }} OPTIONAL {{ ?item wdt:P576 ?gone }} OPTIONAL {{ ?item wdt:P31 ?class }}
      OPTIONAL {{ ?item rdfs:label ?label FILTER(LANG(?label) = "en") }} }}""")
    out.write_text(json.dumps({"downloaded": time.strftime("%Y-%m-%d"), "bbox": b, "rows": rows}))
    log(f"wikidata {COUNTIES[key][0]}: {len({r['item']['value'] for r in rows})} dated items in the box")
    return out


# words in a Wikidata class label that mean "this item is a building, and its inception is the
# building's" (a school, a museum, a hospital or a company is an institution: left out)
WD_BUILDING_WORDS = ("building", "skyscraper", "high-rise", "house", "mansion", "villa", "cottage", "tower",
                     "cathedral", "chapel", "synagogue", "mosque", "temple", "theatre", "theater", "cinema",
                     "courthouse", "city hall", "town hall", "hotel", "shopping mall", "shopping center",
                     "arena", "armory", "lighthouse", "castle", "barn", "mill", "factory", "warehouse",
                     "fire station", "power station", "condominium", "meetinghouse", "inn", "tavern",
                     "church", "basilica", "detached home", "tenement", "police station", "post office",
                     "department store", "movie palace", "stadium", "venue", "dormitory", "rathaus",
                     "parking garage")


def _wd_classes(classes):
    """Wikidata class -> {b: is a building (subclass of Q41176), s: is an architectural
    structure (Q811979), label}, cached across counties in
    data/raw/counties_nj/wikidata/classes.json."""
    p = RAWDIR / "wikidata" / "classes.json"
    known = json.loads(p.read_text()) if p.exists() else {}
    todo = sorted(c for c in classes if c.startswith("Q") and c not in known)
    for i in range(0, len(todo), 60):
        chunk = todo[i:i + 60]
        vals = " ".join("wd:" + c for c in chunk)
        hit = {}
        for root in ("Q41176", "Q811979"):
            got = _sparql(f"SELECT ?c WHERE {{ VALUES ?c {{ {vals} }} ?c wdt:P279* wd:{root} }}")
            hit[root] = {r["c"]["value"].rsplit("/", 1)[-1] for r in got}
        lab = _sparql(f'SELECT ?c ?l WHERE {{ VALUES ?c {{ {vals} }} ?c rdfs:label ?l FILTER(LANG(?l) = "en") }}')
        lab = {r["c"]["value"].rsplit("/", 1)[-1]: r["l"]["value"] for r in lab}
        for c in chunk:
            known[c] = {"b": c in hit["Q41176"], "s": c in hit["Q811979"], "label": lab.get(c, "")}
        p.write_text(json.dumps(known))
    return known


def _norm(s):
    import re
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower().replace("saint", "st")).replace("the ", " ").strip()


def join_wikidata(g, key, outline):
    """year_wd / wd_id / hist_name per footprint (and year_hist / hist_nrhp where the item is on
    the National Register), from a Wikidata item that
      - is on the National Register of Historic Places (P649) and is an architectural structure, or
      - has a class that is a building by Wikidata's class tree and by its label (a skyscraper,
        a church building, a house: yes; a school, a museum, a hospital, a company: no - their
        inception is the institution's, not the building's; WD_BUILDING_WORDS),
    is not marked demolished, and whose point lies inside the footprint - or whose English label
    equals the footprint's name within 150 m. The year is the item's earliest inception (P571)
    or opening (P1619) year: not checked building by building."""
    import shapely
    d = json.loads(download_wikidata(key, outline).read_text())
    cls = _wd_classes({r["class"]["value"].rsplit("/", 1)[-1] for r in d["rows"] if "class" in r})
    bld = {c for c, v in cls.items() if v["b"] and any(w in v["label"].lower() for w in WD_BUILDING_WORDS)}
    struct = {c for c, v in cls.items() if v["s"]}
    items = {}
    for r in d["rows"]:
        q = r["item"]["value"].rsplit("/", 1)[-1]
        it = items.setdefault(q, {"qid": q, "label": "", "years": [], "classes": set(), "nrhp": "", "gone": False, "pt": None})
        it["label"] = r.get("label", {}).get("value", it["label"])
        for k in ("inception", "opened"):
            v = r.get(k, {}).get("value", "")
            if v[:4].isdigit():
                it["years"].append(int(v[:4]))
        if "class" in r:
            it["classes"].add(r["class"]["value"].rsplit("/", 1)[-1])
        it["nrhp"] = r.get("nrhp", {}).get("value", it["nrhp"])
        it["gone"] |= "gone" in r
        try:
            lon, lat = r["coord"]["value"].split("(")[1].rstrip(")").split()
            it["pt"] = (float(lon), float(lat))
        except (IndexError, ValueError):
            pass
    rows = []
    for it in items.values():
        ys = [y for y in it["years"] if YEAR_LO <= y <= YEAR_HI]
        ok = bool(it["classes"] & bld) or (bool(it["classes"] & struct) and it["nrhp"] != "")
        if ys and ok and not it["gone"] and it["pt"] and it["label"]:
            rows.append((it["qid"], it["label"], min(ys), it["nrhp"], it["pt"][0], it["pt"][1]))
    w = pd.DataFrame(rows, columns=["qid", "label", "year", "nrhp", "lon", "lat"])
    res = pd.DataFrame({"year_hist": np.nan, "year_wd": np.nan, "wd_id": "", "hist_nrhp": "", "hist_name": ""}, index=g.index)
    stats = {"wikidata_items_dated_buildings_in_box": len(w)}
    if not len(w):
        return res, stats
    pts = shapely.points(w.lon.values, w.lat.values)
    shapely.prepare(outline)
    w = w[shapely.contains(outline, pts)].reset_index(drop=True)
    stats["wikidata_items_in_county"] = len(w)
    pts = shapely.points(w.lon.values, w.lat.values)
    tree = shapely.STRtree(g.geometry.values)
    wi, fi = tree.query(pts, predicate="within")
    m = pd.DataFrame({"w": wi, "fp": fi, "area": g.area_m2.values[fi], "how": 0})
    m = m.sort_values(["w", "area"], ascending=[True, False]).drop_duplicates("w")
    # by name, for points that miss the outline
    named = g[g.name.fillna("") != ""]
    nn = named.name.map(_norm)
    extra = []
    for i in np.setdiff1d(np.arange(len(w)), m.w.values):
        c = named[nn.values == _norm(w.label[i])]
        if len(c):
            dist = np.hypot((c.px.values - w.lon[i]) * 84300, (c.py.values - w.lat[i]) * 111100)
            j = int(np.argmin(dist))
            if dist[j] <= 150:
                extra.append((i, c.index[j], c.area_m2.values[j], 1))
    m = pd.concat([m, pd.DataFrame(extra, columns=m.columns)], ignore_index=True)
    m = m.join(w, on="w")
    m["reg"] = (m.nrhp != "").astype(int)
    m = m.sort_values(["fp", "how", "reg", "year"], ascending=[True, True, False, True]).drop_duplicates("fp")
    res.loc[m.fp.values, "year_wd"] = m.year.values.astype(float)
    res.loc[m.fp.values, "year_hist"] = m.year.where(m.reg == 1).values.astype(float)
    res.loc[m.fp.values, "wd_id"] = m.qid.values
    res.loc[m.fp.values, "hist_name"] = m.label.values
    res.loc[m.fp.values, "hist_nrhp"] = m.nrhp.values
    stats["wikidata_matched_inside"] = int((m.how == 0).sum())
    stats["wikidata_matched_by_name"] = int((m.how == 1).sum())
    stats["wikidata_on_national_register"] = int(m.reg.sum())
    return res, stats


def build(key: str, outline):
    """The county's footprints with their tax-list year. Returns (GeoDataFrame, report)."""
    import geopandas as gpd
    from nyc_buildings import find_heaps
    name = COUNTIES[key][0]
    g, stats = load_footprints(key, outline)
    par = load_parcels(key)
    j = join_parcels(g, par)
    g = pd.concat([g, j], axis=1)
    # main building of a lot = its largest footprint
    g["secondary"] = False
    on = g.lot != ""
    order = g[on].sort_values(["lot", "area_m2"], ascending=[True, False])
    g.loc[order.index[order.lot.duplicated().values], "secondary"] = True
    g["lot_buildings"] = g.lot.map(g[on].lot.value_counts()).fillna(1).astype(int)
    # heap years, one count per lot (main buildings):
    #   heap         per municipality - every New Jersey municipality has its own assessor and
    #                its own placeholder years (North Bergen 1916, Hoboken 1901, Bayonne 1920)
    #   heap_county  the city's rule unchanged on the whole county (>= 300 buildings)
    main = g.year_raw.notna() & ~g.secondary
    hc = find_heaps(g.year_raw[main].values, np.full(int(main.sum()), name))[name]
    g["heap_county"] = g.year_raw.isin(list(hc))
    g["heap"] = False
    hm = {}
    for m, idx in g[main].groupby("MUN_NAME").groups.items():
        yy = g.year_raw.loc[idx].values
        hs = find_heaps_scaled(yy, max(HEAP_MIN, HEAP_SHARE * len(yy)))
        hm[m] = {int(v): int((yy == v).sum()) for v in sorted(hs)}
        g.loc[(g.MUN_NAME == m) & g.year_raw.isin(list(hs)), "heap"] = True
    # storeys: OpenStreetMap's levels, else the tax list's building description (main building)
    st = pd.to_numeric(g.BLDG_DESC.fillna("").str.upper().str.extract(STOREYS)[0], errors="coerce")
    st = st.where((st >= 1) & (st <= 110) & ~g.secondary)
    g["floors"] = g.num_floors.astype("float64").where(g.num_floors.notna(), st)
    g["floors_src"] = np.where(g.num_floors.notna(), "osm", np.where(st.notna(), "modiv", ""))
    g["use"] = use_codes(g.PROP_CLASS, g.DWELL, g.condo_units, g.FAC_NAME, g["class"], g.subtype)
    wd, wstats = join_wikidata(g, key, outline)
    g = pd.concat([g, wd], axis=1)
    stats.update(wstats)
    out = gpd.GeoDataFrame({
        "id": g.id, "county": name, "muni": g.MUN_NAME.fillna(""), "geometry": g.geometry,
        "height_m": g.height.astype("float64"), "height_src": g.height_src,
        "floors": g.floors, "floors_src": g.floors_src,
        "year_raw": g.year_raw, "year_src": g.year_src, "heap": g.heap, "heap_county": g.heap_county,
        "secondary": g.secondary,
        "prop_class": g.PROP_CLASS.fillna(""), "use": g.use, "year_hist": g.year_hist,
        "name": g.name.fillna("").where(g.name.fillna("") != "", g.hist_name),
        # beyond the brief: for the building stage and for checking
        "hist_nrhp": g.hist_nrhp, "year_wd": g.year_wd, "wd_id": g.wd_id,
        "area_m2": g.area_m2, "lot_buildings": g.lot_buildings, "condo_units": g.condo_units,
        "year_spread": g.year_spread,
        "footprint_src": g.source_dataset.map(FOOTPRINT_SRC).fillna("overture"), "osm_id": g.osm_id.fillna(""),
        "pin": g.PAMS_PIN.fillna(""), "bldg_desc": g.BLDG_DESC.fillna(""), "fac_name": g.FAC_NAME.fillna(""),
        "modiv_year": pd.to_numeric(g.YR_CONSTR, errors="coerce"),
        "lon": g.px.round(7), "lat": g.py.round(7),
    }, geometry="geometry", crs=4326)
    report = make_report(key, out, g, par, stats, hc, hm)
    return out, report


def _agreement(d):
    diff = (d.year_raw - d.year_wd).abs()
    return {"n": int(len(d)), "within_2": int((diff <= 2).sum()), "within_10": int((diff <= 10).sum()),
            "tax_year_later_by_over_10": int(((d.year_raw - d.year_wd) > 10).sum()),
            "tax_year_earlier_by_over_10": int(((d.year_wd - d.year_raw) > 10).sum())}


def _lot_coverage(par, g):
    """How complete the footprints are, measured against the tax list: residential lots
    (class 2, not a condominium unit, improvement value > 0) with at least one footprint."""
    p = par[(par.PROP_CLASS == "2") & (par.PCLQCODE.fillna("").str.strip() == "") & (par.IMPRVT_VAL > 0)]
    lots = (p.PCL_MUN.fillna("") + "_" + p.PCLBLOCK.fillna("") + "_" + p.PCLLOT.fillna("")).drop_duplicates()
    have = lots.isin(set(g.lot.values))
    return {"improved_residential_lots": int(len(lots)), "improved_residential_lots_with_footprint": int(have.sum()),
            "share_improved_residential_lots_with_footprint": round(float(have.mean()), 4)}


def make_report(key, out, g, par, stats, heaps_county, heaps_muni):
    n = len(out)
    y = out.year_raw
    has = y.notna()
    main = ~out.secondary
    either = out.heap | out.heap_county
    py = pd.to_numeric(par.YR_CONSTR, errors="coerce")
    outside = py[py.notna() & ((py < YEAR_LO) | (py > YEAR_HI))].astype(int).value_counts()
    dec = (y[has & main] // 10 * 10).astype(int).value_counts().sort_index()
    dec_real = (y[has & main & ~either] // 10 * 10).astype(int).value_counts().sort_index()
    cls = out.assign(has=has).groupby(out.prop_class.replace("", "(no tax record)")).agg(n=("has", "size"), with_year=("has", "sum"))
    mun = out.assign(has=has, e=either).groupby(out.muni.replace("", "(no parcel)")).agg(
        n=("has", "size"), with_year=("has", "sum"), on_heap=("heap", "sum"), either=("e", "sum"))
    big = main & (out.area_m2 >= 1000)
    tall = main & (out.height_m >= 40)
    r = {
        "county": COUNTIES[key][0], "built": time.strftime("%Y-%m-%d"), **stats,
        "parcel_polygons": int(len(par)), "parcels_without_tax_record": int(par.PROP_CLASS.isna().sum()),
        "parcels_condo_units": int((par.PCLQCODE.fillna("").str.strip() != "").sum()),
        "parcels_with_year": int(valid_year(par.YR_CONSTR).notna().sum()),
        "parcel_years_outside_range": {int(k): int(v) for k, v in outside.items()},
        "footprints": n, "footprints_by_source": out.footprint_src.value_counts().to_dict(),
        "in_a_parcel": int(g.in_parcel.sum()), "with_year": int(has.sum()), "share_with_year": round(float(has.mean()), 4),
        "year_src": out.year_src.replace("", "(none)").value_counts().to_dict(),
        "main_buildings": int(main.sum()), "main_with_year": int((has & main).sum()),
        "share_main_with_year": round(float((has & main).sum() / max(main.sum(), 1)), 4),
        "secondary": int(out.secondary.sum()), "secondary_over_100m2": int((out.secondary & (out.area_m2 >= 100)).sum()),
        "on_heap": int(out.heap.sum()), "share_on_heap_of_dated": round(float(out.heap.sum() / max(has.sum(), 1)), 4),
        "on_heap_county_rule": int(out.heap_county.sum()), "on_either_heap": int(either.sum()),
        "share_either_heap_of_dated": round(float(either.sum() / max(has.sum(), 1)), 4),
        "share_year_not_heap": round(float((has & ~out.heap).mean()), 4),
        "share_year_not_either_heap": round(float((has & ~either).mean()), 4),
        "heap_years_county_rule": {int(v): int((y[main] == v).sum()) for v in sorted(heaps_county)},
        "heap_years_by_municipality": heaps_muni,
        "years_before_1800": {int(k): int(v) for k, v in y[has & main & (y < 1800)].astype(int).value_counts().sort_index().items()},
        "large_main_1000m2": int(big.sum()), "large_main_with_year": int((big & has).sum()),
        "large_main_year_not_heap": int((big & has & ~either).sum()),
        "tall_main_40m": int(tall.sum()), "tall_main_with_year": int((tall & has).sum()),
        "with_height": int(out.height_m.notna().sum()), "share_with_height": round(float(out.height_m.notna().mean()), 4),
        "height_by_source": out.height_src.replace("", "(none)").value_counts().to_dict(),
        "with_floors": out.floors_src.replace("", "(none)").value_counts().to_dict(),
        "condo_buildings": int((out.condo_units > 0).sum()),
        "condo_buildings_year_spread_over_5": int((out.year_spread > 5).sum()),
        "use": {int(k): int(v) for k, v in out.use.value_counts().sort_index().items()},
        "decades_main_buildings": {int(k): int(v) for k, v in dec.items()},
        "decades_main_buildings_not_heap": {int(k): int(v) for k, v in dec_real.items()},
        "by_class": {k: [int(v.n), int(v.with_year)] for k, v in cls.sort_values("n", ascending=False).iterrows()},
        "by_municipality": {k: [int(v.n), int(v.with_year), int(v.on_heap), int(v.either)] for k, v in mun.iterrows()},
        "with_year_hist": int(out.year_hist.notna().sum()), "with_year_wd": int(out.year_wd.notna().sum()),
        "year_wd_without_tax_year": int((out.year_wd.notna() & ~has).sum()),
        "year_wd_vs_tax_year_not_heap": _agreement(out[out.year_wd.notna() & has & ~either]),
        "year_wd_vs_tax_year_heap": _agreement(out[out.year_wd.notna() & has & either]),
        **_lot_coverage(par, g),
        "geometry_invalid": int((~out.geometry.is_valid).sum()),
        "year_min": float(y.min()), "year_max": float(y.max()),
    }
    return r


def run(key: str, outline, force=False):
    OUTDIR.mkdir(parents=True, exist_ok=True)
    out_p = OUTDIR / f"nj_{key}.parquet"
    rep_p = OUTDIR / f"nj_{key}_report.json"
    src = [RAW / "overture" / OVERTURE_RELEASE / ("region_building.parquet" if key in LEGACY else "outer_building.parquet"),
           RAWDIR / "parcels" / key / "done.json"] + ([] if key in LEGACY else [Path(__file__)])
    if out_p.exists() and rep_p.exists() and not force and all(
            not s.exists() or s.stat().st_mtime <= out_p.stat().st_mtime for s in src):
        log(f"counties_nj {key}: cached")
        return json.loads(rep_p.read_text())
    out, rep = build(key, outline)
    tmp = out_p.with_name(f"_stage_{out_p.name}")
    out.to_parquet(tmp, compression="zstd")
    tmp.replace(out_p)
    rep_p.write_text(json.dumps(rep, indent=1))
    log(f"counties_nj {rep['county']}: {rep['footprints']} footprints, {rep['with_year']} with a year "
        f"({rep['share_with_year']:.1%}), {rep['on_heap']} on a municipal heap year, {rep['on_either_heap']} with the county rule too, "
        f"{rep['with_height']} with a height -> {out_p}")
    return rep


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    keys = [a.lower() for a in args] or list(LEGACY)
    if "--download" in sys.argv:
        with ThreadPoolExecutor(3) as ex:
            list(ex.map(download_parcels, keys))
        sys.exit(0)
    if "--heights" in sys.argv:
        outl = county_outlines()
        for k in keys:
            download_height_sources(k, outl[k])
        sys.exit(0)
    outl = county_outlines()
    for k in keys:   # one county at a time: the machine is shared
        download_parcels(k)
        run(k, outl[k], force="--force" in sys.argv)
