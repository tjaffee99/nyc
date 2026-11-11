"""Buildings of the New York counties next to the city, with the assessor's construction year.

    python counties_ny.py download [westchester|rockland|nassau ...]   cached downloads only
    python counties_ny.py build    [westchester|rockland|nassau ...]   -> data/interim/counties/ny_<county>.parquet
    python counties_ny.py check    [westchester|rockland ...]          well-known buildings against their known dates
    python counties_ny.py                                              all three, every county

Sources, licences, what was found per county and the verdicts: data/research/counties_ny.md.
Westchester and Rockland are in the State's public parcel layer; Nassau is not and has no
public year built anywhere: it is reported and not built.

Rules (the owner's: real years only, nothing generated):
  * Footprints: Overture's (the lead's region extract), inner point in the TIGER county
    outline, >= 12 m2; where Overture has no building, the State's footprint (county
    planimetrics of 2007 / 2013) fills the gap. `footprint_src` says which.
  * footprint -> the tax parcel that contains its centre -> that parcel's year built
    (`YR_BLT` of the 2025 assessment roll). Stacked parcels (condominium units) count as one
    parcel with their most frequent year.
  * On a parcel with several footprints the year belongs to the main building (the largest
    outline); the others get the same year and `secondary` = True.
  * Nothing is spread, imputed or refined here. `year_raw` is the assessor's year as recorded
    (NaN where the parcel carries none), `heap` flags the placeholder years
    (nyc_buildings.find_heaps, per assessing town or city, residential records and the rest
    separately; a year that is one development is not a heap).
  * `year_hist` is the year the State Historic Preservation Office's building inventory (CRIS)
    gives at the end of the surveyed building's name ("Glenview Mansion (1876)"), where the
    inventory point falls inside the footprint; "ca." years go to `year_hist_ca`. The public
    CRIS layer has no date field.
  * `muni_year_share` = share of the municipality's main residential buildings that carry a
    year: 1.0 where the assessor's inventory is published, 0.0 where it is not (22 of
    Westchester's 43 municipalities). Use it to leave undated ground off the map.

Outputs (data/interim/counties/): ny_<county>.parquet (one row per footprint, EPSG:4326),
ny_<county>_report.json / .txt (coverage per municipality, heap years with their evidence,
decades), ny_<county>_munis.geojson (municipal outlines with `dated` = yes / partly / no),
ny_<county>_checks.txt; caches parcels_<county>.parquet, state_fp_<county>.parquet.

Every download is cached under data/raw/counties_ny/ and never modified; a rerun only fetches
what is missing. The build peaks at about 1.3 GB (Westchester).
"""
from __future__ import annotations

import gc
import gzip
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from common import INTERIM, RAW, log

UA = "NYCThroughTime-research/0.1"
CACHE = RAW / "counties_ny"
OUT = INTERIM / "counties"
REGION_FOOTPRINTS = RAW / "overture" / "2026-10-21.0" / "region_building.parquet"
OUTER_FOOTPRINTS = RAW / "overture" / "2026-10-21.0" / "outer_building.parquet"
TIGER = RAW / "tiger" / "tl_2024_us_county.zip"

# county key -> (name, state+county FIPS)
COUNTIES = {"westchester": ("Westchester", "36119"), "nassau": ("Nassau", "36059"), "rockland": ("Rockland", "36087"),
            # the outer round (2026-11-11): footprints from the outer extract, see data/research/counties_ny_outer.md
            "putnam": ("Putnam", "36079"), "sullivan": ("Sullivan", "36105"), "ulster": ("Ulster", "36111"),
            "dutchess": ("Dutchess", "36027"), "orange": ("Orange", "36071"), "suffolk": ("Suffolk", "36103")}
OUTER = ("putnam", "sullivan", "ulster", "dutchess", "orange", "nassau", "suffolk")   # footprints from OUTER_FOOTPRINTS
REGION_ONLY = ("westchester", "rockland")

# NYS ITS Geospatial Services, "NYS Tax Parcels Public" (2025 assessment rolls, published May 2026)
PARCELS = "https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Tax_Parcels_Public/FeatureServer/1/query"
PARCEL_FIELDS = ("OBJECTID,COUNTY_NAME,MUNI_NAME,SWIS,CITYTOWN_NAME,PRINT_KEY,SBL,PARCEL_ADDR,PROP_CLASS,"
                 "ROLL_SECTION,YR_BLT,BLDG_STYLE,BLDG_STYLE_DESC,SQFT_LIVING,GFA,USED_AS_CODE,USED_AS_DESC,"
                 "ROLL_YR,SPATIAL_YR,OWNER_TYPE,NYS_NAME,DUP_GEO,CALC_ACRES")
PAGE = 2000  # OBJECTIDs per request
# NYS ITS Geospatial Services, "NYS Building Footprints" (county planimetrics collected for NYSERDA; no heights)
STATE_FP = "https://gisservices.its.ny.gov/arcgis/rest/services/BuildingFootprints/FeatureServer/2/query"
# a state footprint fills a gap if Overture's footprints cover less than this share of it and less than FILL_AREA m2
FILL_OVERLAP = 0.10
FILL_AREA = 5.0
# NYS ITS Geospatial Services, "NYS Civil Boundaries" (layer 6 cities and towns, 7 villages)
CIVIL = "https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Civil_Boundaries/FeatureServer"
# State Historic Preservation Office, Cultural Resource Information System: inventoried buildings
CRIS_USN = "https://services.arcgis.com/1xFZPtKn1wKC6POA/arcgis/rest/services/Building_USN_Points/FeatureServer/2/query"
UTM = "EPSG:32618"  # common.NYC_CRS
MIN_AREA = 12.0     # m2: smaller outlines are sheds
YEAR_LO, YEAR_HI = 1650, 2026

_session = None


def session():
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers["User-Agent"] = UA
    return _session


def get_json(url, params, tries=5, timeout=180):
    for k in range(tries):
        try:
            r = session().get(url, params=params, timeout=timeout)
            if r.status_code == 200:
                d = r.json()
                if "error" not in d:
                    return d
                err = d["error"]
            else:
                err = f"HTTP {r.status_code}"
        except (requests.RequestException, ValueError) as e:  # noqa: PERF203
            err = repr(e)
        log(f"  retry {k + 1}/{tries}: {err}")
        time.sleep(4 * (k + 1))
    raise RuntimeError(f"{url}: {err}")


# ---------------------------------------------------------------------------------------------
# downloads


def oid_range(url, where, cache):
    """min / max / count of OBJECTID for a filter (cached)."""
    if cache.exists():
        return json.loads(cache.read_text())
    d = get_json(url, {"where": where, "f": "json", "outStatistics": json.dumps([
        {"statisticType": "min", "onStatisticField": "OBJECTID", "outStatisticFieldName": "lo"},
        {"statisticType": "max", "onStatisticField": "OBJECTID", "outStatisticFieldName": "hi"},
        {"statisticType": "count", "onStatisticField": "OBJECTID", "outStatisticFieldName": "n"}])})
    a = {k.lower(): v for k, v in d["features"][0]["attributes"].items()}
    out = {"lo": int(a["lo"] or 0), "hi": int(a["hi"] or -1), "n": int(a["n"] or 0), "fetched": time.strftime("%Y-%m-%d")}
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(out))
    return out


def fetch_page(url, where, fields, f):
    """One OBJECTID window of a feature layer as GeoJSON (WGS84, 1e-6 degrees) -> f (gzip)."""
    if f.exists():
        return 0
    d = get_json(url, {"where": where, "outFields": fields, "outSR": 4326, "geometryPrecision": 6,
                       "orderByFields": "OBJECTID", "f": "geojson"})
    if d.get("exceededTransferLimit") or (d.get("properties") or {}).get("exceededTransferLimit"):
        raise RuntimeError(f"{f.name}: transfer limit exceeded")
    tmp = f.with_suffix(".part")
    with gzip.open(tmp, "wt") as fh:
        json.dump(d, fh)
    tmp.rename(f)
    return len(d["features"])


def download_layer(what, name, url, field, fields, page):
    """Every feature of a county from a statewide layer, in OBJECTID windows (idempotent)."""
    rng = oid_range(url, f"{field}='{name}'", CACHE / "meta" / f"{what}_oid_{name}.json")
    if rng["n"] == 0:
        log(f"{what} {name}: not in the statewide public layer")
        return False
    d = CACHE / what / name
    d.mkdir(parents=True, exist_ok=True)
    pages = [(a, min(a + page, rng["hi"] + 1)) for a in range(rng["lo"], rng["hi"] + 1, page)]
    todo = [p for p in pages if not (d / f"oid_{p[0]}_{p[1]}.geojson.gz").exists()]
    log(f"{what} {name}: {rng['n']} features, OBJECTID {rng['lo']}-{rng['hi']}, {len(todo)} of {len(pages)} pages to fetch")
    got = 0
    with ThreadPoolExecutor(3) as ex:
        jobs = ex.map(lambda p: fetch_page(url, f"{field}='{name}' AND OBJECTID >= {p[0]} AND OBJECTID < {p[1]}", fields,
                                           d / f"oid_{p[0]}_{p[1]}.geojson.gz"), todo)
        for i, n in enumerate(jobs):
            got += n
            if i % 20 == 19:
                log(f"  {name}: {i + 1}/{len(todo)} pages, {got} features")
    return True


def download_parcels(key):
    return download_layer("parcels", COUNTIES[key][0], PARCELS, "COUNTY_NAME", PARCEL_FIELDS, PAGE)


def download_state_footprints(key):
    return download_layer("state_footprints", COUNTIES[key][0], STATE_FP, "COUNTYNAME",
                          "OBJECTID,MUNINAME,NYSGEO_SOURCE,SOURCE,SOURCEDATE", 2 * PAGE)


def download_cris(key):
    """SHPO's building inventory points (CRIS "Building USN Points": name, address, eligibility;
    the public layer carries no construction date) inside the county's bounding box."""
    name, fips = COUNTIES[key]
    d = CACHE / "cris" / name
    if (d / "done.json").exists():
        return
    d.mkdir(parents=True, exist_ok=True)
    w, s, e, n = county_outline(fips).bounds
    off, total = 0, 0
    while True:
        f = d / f"usn_{off:06d}.geojson.gz"
        if f.exists():
            with gzip.open(f, "rt") as fh:
                page = json.load(fh)
        else:
            page = get_json(CRIS_USN, {"where": "1=1", "geometry": f"{w},{s},{e},{n}", "geometryType": "esriGeometryEnvelope",
                                       "inSR": 4326, "spatialRel": "esriSpatialRelIntersects", "outFields": "*", "outSR": 4326,
                                       "orderByFields": "OBJECTID", "resultOffset": off, "resultRecordCount": 2000, "f": "geojson"})
            tmp = f.with_suffix(".part")
            with gzip.open(tmp, "wt") as fh:
                json.dump(page, fh)
            tmp.rename(f)
        k = len(page["features"])
        total += k
        off += k
        if k < 2000:
            break
    (d / "done.json").write_text(json.dumps({"points": total, "bbox": [w, s, e, n], "fetched": time.strftime("%Y-%m-%d")}))
    log(f"cris {name}: {total} inventoried buildings in the county's box")


def download_civil(key):
    """City, town and village outlines of the county (NYS Civil Boundaries)."""
    name = COUNTIES[key][0]
    for layer, what in ((6, "cities_towns"), (7, "villages")):
        f = CACHE / "civil" / f"{name}_{what}.geojson"
        if f.exists():
            continue
        f.parent.mkdir(parents=True, exist_ok=True)
        d = get_json(f"{CIVIL}/{layer}/query", {"where": f"COUNTY LIKE '%{name}%'", "outFields": "*", "outSR": 4326,
                                                 "geometryPrecision": 6, "f": "geojson"})
        f.write_text(json.dumps(d))
        log(f"civil {name}: {len(d['features'])} {what}")


def muni_outlines(key, g):
    """One outline per municipality of the built file (a village; a town outside its villages; a
    city) with the share of its main homes that carry a year -> ny_<county>_munis.geojson.
    The pieces are named by the footprints inside them, not by matching names."""
    import geopandas as gpd
    import shapely
    name = COUNTIES[key][0]
    fs = [CACHE / "civil" / f"{name}_{w}.geojson" for w in ("cities_towns", "villages")]
    if not all(f.exists() for f in fs):
        return
    towns, villages = (gpd.read_file(f).to_crs(UTM) for f in fs)
    towns = towns[towns.COUNTY.fillna("").str.contains(name)]
    vu = shapely.union_all(villages.geometry.values) if len(villages) else None
    rest = towns.geometry.difference(vu) if vu is not None else towns.geometry
    pieces = gpd.GeoDataFrame(geometry=list(villages.geometry.values) + [x for x in rest.values if not x.is_empty], crs=UTM)
    pieces = pieces.explode(index_parts=False).reset_index(drop=True)
    pieces = pieces[pieces.area > 1e4].reset_index(drop=True)
    pts = gpd.GeoDataFrame({"muni": g.muni.values}, geometry=gpd.points_from_xy(g.lon, g.lat), crs=4326).to_crs(UTM)
    j = gpd.sjoin(pts[pts.muni != ""], pieces, predicate="within")
    pieces["muni"] = j.groupby("index_right").muni.agg(lambda v: v.value_counts().index[0]).reindex(pieces.index)
    out = pieces.dropna(subset=["muni"]).dissolve("muni").reset_index()
    st = g.groupby("muni").agg(footprints=("id", "size"), with_year=("year_raw", "count"), muni_year_share=("muni_year_share", "first"),
                               town=("town", lambda v: v.value_counts().index[0])).reset_index()
    out = out.merge(st, on="muni", how="left")
    out["dated"] = np.where(out.muni_year_share >= 0.9, "yes", np.where(out.muni_year_share >= 0.5, "partly", "no"))
    out["county"] = name
    out["geometry"] = out.geometry.simplify(5).to_crs(4326)
    out = out.set_crs(4326, allow_override=True)
    f = OUT / f"ny_{key}_munis.geojson"
    f.write_text(out.to_json(drop_id=True))
    log(f"munis {name}: {len(out)} outlines -> {f.name} ({out.dated.value_counts().to_dict()})")


# ---------------------------------------------------------------------------------------------
# build

_outlines = {}


def county_outline(fips):
    """The TIGER county outline (WGS84 polygon)."""
    if fips not in _outlines:
        import geopandas as gpd
        g = gpd.read_file(f"zip://{TIGER}", where=f"GEOID='{fips}'").to_crs(4326)
        _outlines[fips] = g.geometry.iloc[0]
    return _outlines[fips]


def pages_gdf(folder, columns=None):
    """Every cached GeoJSON page of a folder as one GeoDataFrame (WGS84), or None."""
    import geopandas as gpd
    parts = []
    for p in sorted(folder.glob("oid_*.geojson.gz")):
        with gzip.open(p, "rt") as fh:
            feats = [f for f in json.load(fh)["features"] if f["geometry"]]
        if feats:
            part = gpd.GeoDataFrame.from_features(feats, crs=4326)
            parts.append(part[columns + ["geometry"]] if columns else part)
        del feats
    if not parts:
        return None
    g = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), geometry="geometry", crs=4326)
    return g.drop_duplicates("OBJECTID").reset_index(drop=True)


def in_county(g, poly):
    """Valid polygons whose inner point lies in the county outline."""
    import shapely
    geom = g.geometry.values
    bad = ~shapely.is_valid(geom)
    if bad.any():
        geom = geom.copy()
        geom[bad] = shapely.make_valid(geom[bad])
        g = g.set_geometry(geom)
    g = g[g.geom_type.isin(["Polygon", "MultiPolygon"]) & ~g.geometry.is_empty]
    rep = g.geometry.representative_point()
    shapely.prepare(poly)
    return g[shapely.contains_xy(poly, rep.x.values, rep.y.values)].reset_index(drop=True), int(bad.sum())


def load_footprints(key):
    """Overture footprints whose inner point lies in the county, >= MIN_AREA m2, and the State's
    footprints where Overture has none (Overture's footprints cover < FILL_OVERLAP of the outline
    and < FILL_AREA m2: neighbours that touch)."""
    import duckdb
    import geopandas as gpd
    import shapely
    name, fips = COUNTIES[key]
    poly = county_outline(fips)
    w, s, e, n = poly.bounds
    con = duckdb.connect()
    con.execute("SET memory_limit='1000MB'")
    con.execute("SET enable_progress_bar=false")
    df = con.execute(
        f"SELECT id, name, height, num_floors, source_dataset, ST_AsWKB(geometry) AS wkb FROM read_parquet('{OUTER_FOOTPRINTS if key in OUTER else REGION_FOOTPRINTS}') "
        f"WHERE lon BETWEEN {w - 0.01} AND {e + 0.01} AND lat BETWEEN {s - 0.01} AND {n + 0.01}").df()
    con.close()
    g = gpd.GeoDataFrame(df.drop(columns="wkb"), geometry=shapely.from_wkb(df.wkb.apply(bytes).values), crs=4326)
    g, bad = in_county(g, poly)
    n_all = len(g)
    area = g.geometry.to_crs(UTM).area.values
    g["area_m2"] = np.round(area, 1)
    g = g[area >= MIN_AREA].reset_index(drop=True)
    log(f"footprints {name}: Overture {n_all} in the county, {n_all - len(g)} under {MIN_AREA} m2 dropped, {bad} repaired, {len(g)} kept")
    del df
    gc.collect()
    st = state_footprints(key)
    n_state = n_fill = 0
    if st is not None:
        st, _ = in_county(st, poly)
        su = st.geometry.to_crs(UTM)
        sarea = su.area.values
        keep = sarea >= MIN_AREA
        st, su, sarea = st[keep].reset_index(drop=True), su[keep].reset_index(drop=True), sarea[keep]
        n_state = len(st)
        ou = g.geometry.to_crs(UTM)
        og = gpd.GeoDataFrame({"oi": np.arange(len(g))}, geometry=ou.values, crs=UTM)
        covered = np.zeros(len(st))
        for a in range(0, len(st), 40000):   # in chunks: the machine is shared
            b = min(a + 40000, len(st))
            j = gpd.sjoin(gpd.GeoDataFrame({"si": np.arange(a, b)}, geometry=su.values[a:b], crs=UTM), og, predicate="intersects")
            inter = shapely.area(shapely.intersection(su.values[j.si.values], ou.values[j.oi.values]))
            np.add.at(covered, j.si.values, inter)
            del j, inter
        del og, ou
        fill = (covered < FILL_OVERLAP * sarea) & (covered < FILL_AREA)
        n_fill = int(fill.sum())
        fs = st[fill]
        add = gpd.GeoDataFrame({"id": "nysbf:" + fs.OBJECTID.astype(int).astype(str), "name": None, "height": np.nan,
                                "num_floors": np.nan,
                                "source_dataset": np.where(fs.NYSGEO_SOURCE.fillna("").eq("NYSERDA"),
                                                           "NYS " + fs.SOURCEDATE.fillna("").astype(str).str[-4:], "NYS microsoft"),
                                "area_m2": np.round(sarea[fill], 1)}, geometry=fs.geometry.values, crs=4326)
        del st, su, fs
        g = gpd.GeoDataFrame(pd.concat([g, add], ignore_index=True), geometry="geometry", crs=4326)
        log(f"footprints {name}: the State's layer has {n_state} of {MIN_AREA} m2 or more; {n_fill} stand where Overture has none -> added, {len(g)} in all")
    return g, {"overture_in_county": n_all, "state_layer": n_state, "state_fill": n_fill}


def state_footprints(key):
    """The State's footprints of the county (WGS84; OBJECTID, source, source date), cached as one GeoParquet."""
    import geopandas as gpd
    name = COUNTIES[key][0]
    out = OUT / f"state_fp_{key}.parquet"
    pages = sorted((CACHE / "state_footprints" / name).glob("oid_*.geojson.gz"))
    if not pages:
        return None
    if not (out.exists() and out.stat().st_mtime > max(p.stat().st_mtime for p in pages)):
        g = pages_gdf(CACHE / "state_footprints" / name, ["OBJECTID", "NYSGEO_SOURCE", "SOURCEDATE"])
        OUT.mkdir(parents=True, exist_ok=True)
        g.to_parquet(out)
        del g
        gc.collect()
    return gpd.read_parquet(out)


def load_parcels(key):
    """The county's tax parcels (UTM 18N), cached as one GeoParquet."""
    import geopandas as gpd
    import shapely
    name = COUNTIES[key][0]
    out = OUT / f"parcels_{key}.parquet"
    pages = sorted((CACHE / "parcels" / name).glob("oid_*.geojson.gz"))
    if not pages:
        return None
    if out.exists() and out.stat().st_mtime > max(p.stat().st_mtime for p in pages):
        return gpd.read_parquet(out)
    g = pages_gdf(CACHE / "parcels" / name, ["OBJECTID", "MUNI_NAME", "SWIS", "CITYTOWN_NAME", "PRINT_KEY", "PARCEL_ADDR", "PROP_CLASS",
                                             "YR_BLT", "OWNER_TYPE", "NYS_NAME", "DUP_GEO"]).to_crs(UTM)
    bad = ~g.geometry.is_valid.values
    if bad.any():
        g.loc[bad, "geometry"] = shapely.make_valid(g.geometry.values[bad])
    OUT.mkdir(parents=True, exist_ok=True)
    g.to_parquet(out)
    log(f"parcels {name}: {len(g)} parcels, {int(bad.sum())} repaired -> {out.name}")
    return g


def mode_or_nan(s):
    """Most frequent value (ties: the smallest); NaN for an empty series."""
    s = s.dropna()
    if not len(s):
        return np.nan
    c = s.value_counts()
    return c[c == c.iloc[0]].index.min()


def parcel_stacks(par):
    """One row per distinct parcel outline. Condominium units and other stacked records share
    an outline (DUP_GEO = 'Y'): the stack's year is the most frequent recorded year of its
    members (ties: the earliest), its class the most frequent class."""
    import geopandas as gpd
    c = par.geometry.representative_point()
    key = (np.round(c.x.values, 0).astype(np.int64).astype(str) + "_" + np.round(c.y.values, 0).astype(np.int64).astype(str)
           + "_" + np.round(par.geometry.area.values, 0).astype(np.int64).astype(str))
    par = par.assign(stk=pd.factorize(key)[0])
    yr = pd.to_numeric(par.YR_BLT, errors="coerce").where(lambda v: (v >= YEAR_LO) & (v <= YEAR_HI))
    par = par.assign(yr=yr)
    first = par.drop_duplicates("stk").set_index("stk")
    multi = par.stk.value_counts()
    multi = set(multi[multi > 1].index)
    m = par[par.stk.isin(multi)]
    st = first[["geometry", "MUNI_NAME", "CITYTOWN_NAME", "SWIS", "PRINT_KEY", "PROP_CLASS", "yr", "OWNER_TYPE", "NYS_NAME"]].copy()
    if len(m):
        st.loc[sorted(multi), "yr"] = m.groupby("stk").yr.apply(mode_or_nan)
        st.loc[sorted(multi), "PROP_CLASS"] = m.groupby("stk").PROP_CLASS.apply(lambda s: mode_or_nan(s) if s.notna().any() else None)
    # the assessing unit is the city or town (SWIS digits 1-4); a city and a town can share a name (Rye)
    unit = st.SWIS.fillna("").astype(str).str[:4]
    nm = st.CITYTOWN_NAME.fillna("").astype(str)
    shared = nm.map(pd.DataFrame({"n": nm, "u": unit}).drop_duplicates().groupby("n").u.nunique()) > 1
    kindname = np.where(pd.to_numeric(unit.str[2:4], errors="coerce").fillna(99) < 20, " (city)", " (town)")
    st["CITYTOWN_NAME"] = np.where(shared, nm + kindname, nm)
    st["members"] = par.stk.value_counts().reindex(st.index).values
    st["parea"] = st.geometry.area.values
    return gpd.GeoDataFrame(st, geometry="geometry", crs=par.crs).reset_index()


def use_of(cls):
    """NYS property class (three digits) -> 0 unknown, 1 single-family home, 2 residential,
    3 commercial, 4 office, 5 industrial, 6 government / civic, 7 other.
    https://www.tax.ny.gov/research/property/assess/manuals/prclas.htm"""
    try:
        c = int(str(cls)[:3])
    except (TypeError, ValueError):
        return 0
    if c in (210, 215):
        return 1
    if 200 <= c < 300 or c == 411:      # 411 apartments
        return 2
    if 460 <= c <= 465:                 # banks, office and professional buildings
        return 4
    if 400 <= c < 500:
        return 3
    if 600 <= c < 700:                  # community services: schools, churches, hospitals, government
        return 6
    if 700 <= c < 800:
        return 5
    if 100 <= c < 1000:                 # farms, vacant land, recreation, utilities, parks
        return 7
    return 0


def find_heaps(year, unit, min_count):
    """nyc_buildings.find_heaps with the minimum count as a parameter: a placeholder year is
    one, up to 1990, carrying more than 3x the median of the non-round, not-yet-flagged years
    within +/- 4 and at least `min_count(unit)` buildings. Round years are tested first."""
    heaps = {}
    for b in pd.unique(unit):
        y = year[(unit == b) & np.isfinite(year)].astype(int)
        cnt = dict(zip(*np.unique(y, return_counts=True)))
        need = min_count(len(y))
        flagged: set[int] = set()
        for rnd in (True, False, False):
            for v in sorted(cnt):
                if v > 1990 or v in flagged or (v % 5 == 0) != rnd or cnt[v] < need:
                    continue
                nb = [cnt.get(u, 0) for u in range(v - 4, v + 5) if u != v and u % 5 and u not in flagged]
                if nb and cnt[v] > 3 * max(float(np.median(nb)), 1.0):
                    flagged.add(v)
        heaps[b] = flagged
    return heaps


def heap_evidence(heaps, year, unit, x, y, kind, tracts=True, cell=400.0):
    """One row per flagged year: its count, the median of its non-round neighbours, and how
    widely its buildings are scattered — the number of 400 m cells they occupy against the
    number an equal draw from the unit's buildings dated within 15 years occupies. A
    placeholder year is scattered like its era (ratio near 1); a subdivision or a condominium
    complex finished in one year sits in a few cells. With `tracts`, a flagged year after 1945
    with at least 30 buildings and a ratio under 0.5 is such a development and is NOT a heap."""
    rows = []
    cid = (np.floor(x / cell).astype(np.int64) << 32) + np.floor(y / cell).astype(np.int64)
    rng = np.random.default_rng(1609)
    for b, hs in sorted(heaps.items()):
        m = (unit == b) & np.isfinite(year)
        yy, cc = year[m].astype(int), cid[m]
        cnt = dict(zip(*np.unique(yy, return_counts=True)))
        for v in sorted(hs):
            nb = [cnt.get(k, 0) for k in range(v - 4, v + 5) if k != v and k % 5 and k not in hs]
            med = float(np.median(nb)) if nb else 0.0
            h = cc[yy == v]
            era = cc[(np.abs(yy - v) <= 15) & (yy != v)]
            spread = np.nan
            if len(era) >= len(h):
                spread = len(np.unique(h)) / float(np.mean([len(np.unique(rng.choice(era, len(h), replace=False))) for _ in range(7)]))
            # (no era to compare with: a year with more buildings than its whole era is one development
            # if they stand ten or more to a cell)
            close = spread < 0.5 if not np.isnan(spread) else 10 * len(np.unique(h)) <= len(h)
            tract = bool(tracts and v > 1945 and len(h) >= 30 and close)
            rows.append({"town": b, "kind": kind, "year": int(v), "n": int(len(h)), "median_neighbours": med,
                         "strength": round(len(h) / max(med, 1.0), 1), "spread": None if np.isnan(spread) else round(spread, 2),
                         "heap": not tract})
    return rows


def heap_min(n_dated):
    """Minimum size of a heap in an assessing unit with `n_dated` dated main buildings: the
    city's 300 per borough (150-330 thousand buildings) scaled down, never under 40."""
    return max(40, int(round(0.002 * n_dated)))


def heap_min_other(n_dated):
    """The same for the few thousand non-residential buildings of a unit: 1 %, never under 10."""
    return max(10, int(round(0.01 * n_dated)))


# a year at the end of an inventory name: "Glenview Mansion (1876)", "PROCTOR'S THEATER, 1913", "Queen Anne house ca 1890"
CRIS_YEAR = re.compile(r"(?<!\d)(1[6-9]\d\d|20[0-2]\d)\s*\)?\s*$")
CRIS_CIRCA = re.compile(r"(\bca?\.?|\bcirca)\s*$", re.I)
CRIS_DATED = re.compile(r"[(,]\s*$|\b(built|erected)(\s+in)?\s*$", re.I)
CRIS_NOT_BUILT = re.compile(r"\b(demolish\w*|razed|burn(ed|t)|destroy\w*|moved|site of|ruins?|remodel\w*|alter(ed|ations?)|rebuilt|additions?|landmark)\b", re.I)
# inventory names that describe instead of naming: "residential bldg ca. 1890", "PRIVATE RESIDENCE, 1955", "BLDG 69/GARAGE (1936)"
CRIS_GENERIC = re.compile(r"(?i)^\W*((private|former|vernacular|brick|frame|stone|wood|mixed|multi|single|two|three|\d[\d\-/ ]*(story|sty)?"
                          r"|queen anne|second empire|italianate|classical rev\w*|colonial rev\w*|tudor\w*|shingle style|greek rev\w*|gothic rev\w*)\W+)*"
                          r"(residen\w*|house|comm'?l\w*|commercial|apartment|apt|row ?house|duplex|garage|barn|shed|store|building|bldg|cottage|dwelling|outbuilding)\b")


def cris_name_year(name):
    """(year, circa) from the end of an inventory name that holds exactly one year and no word
    of demolition or alteration: "(1876)" and ", 1913" are the surveyor's dates, "ca 1890" the
    surveyor's estimate; (NaN, False) otherwise."""
    if not name or CRIS_NOT_BUILT.search(name) or len(re.findall(r"(?<!\d)(?:1[6-9]\d\d|20[0-2]\d)(?!\d)", name)) != 1:
        return np.nan, False
    m = CRIS_YEAR.search(name)
    if not m:
        return np.nan, False
    pre = name[:m.start()].rstrip(" (,")
    if CRIS_CIRCA.search(pre):
        return float(m.group(1)), True
    if CRIS_DATED.search(name[:m.start()]):
        return float(m.group(1)), False
    return np.nan, False


def cris_points(key):
    import geopandas as gpd
    name = COUNTIES[key][0]
    feats = []
    for p in sorted((CACHE / "cris" / name).glob("usn_*.geojson.gz")):
        with gzip.open(p, "rt") as fh:
            feats += [f for f in json.load(fh)["features"] if f["geometry"]]
    if not feats:
        return None
    return gpd.GeoDataFrame.from_features(feats, crs=4326).to_crs(UTM)


def build(key):
    import geopandas as gpd
    name, fips = COUNTIES[key]
    if not any((CACHE / "parcels" / name).glob("oid_*.geojson.gz")):
        log(f"{name}: no parcels with construction years -> not built (see data/research/counties_ny.md)")
        return None
    fp, counts = load_footprints(key)
    gc.collect()
    st = parcel_stacks(load_parcels(key))
    gc.collect()
    u = fp.geometry.to_crs(UTM)
    cen = u.centroid
    inside = u.contains(cen).values
    pt = gpd.GeoSeries(np.where(inside, cen.values, u.representative_point().values), crs=UTM)
    j = gpd.sjoin(gpd.GeoDataFrame({"fi": np.arange(len(fp))}, geometry=pt, crs=UTM),
                  st[["stk", "yr", "parea", "geometry"]], predicate="within")
    # the smallest parcel around the centre that carries a year, else the smallest
    j["noyr"] = j.yr.isna()
    j = j.sort_values(["fi", "noyr", "parea"]).drop_duplicates("fi")
    sidx = pd.Series(j.stk.values, index=j.fi.values).reindex(np.arange(len(fp)))
    sp = st.set_index("stk").reindex(sidx.values)
    has = sidx.notna().values
    year = sp.yr.values.astype(float)
    # footprints outside every parcel (on a road bed, over water, parcel gaps): the municipality of the nearest parcel
    muni = sp.MUNI_NAME.values.astype(object)
    town = sp.CITYTOWN_NAME.values.astype(object)
    if (~has).any():
        nn = gpd.sjoin_nearest(gpd.GeoDataFrame({"fi": np.flatnonzero(~has)}, geometry=pt[~has].values, crs=UTM),
                               st[["MUNI_NAME", "CITYTOWN_NAME", "geometry"]], max_distance=300).drop_duplicates("fi")
        muni[nn.fi.values] = nn.MUNI_NAME.values
        town[nn.fi.values] = nn.CITYTOWN_NAME.values
    # main building of a parcel = its largest outline
    area = fp.area_m2.values
    order = pd.DataFrame({"s": sidx.values, "a": area}).sort_values(["s", "a"], ascending=[True, False])
    first = order.dropna(subset=["s"]).drop_duplicates("s").index
    secondary = has.copy()
    secondary[first] = False
    n_on = pd.Series(sidx.values).map(pd.Series(sidx.values).value_counts()).fillna(0).astype(int).values
    # placeholder years, on main buildings only, per assessing unit (city / town) and kind of
    # inventory: the assessor's residential records (classes 200-299) and everything else
    # (commercial records, exempt property), whose years are mostly round estimates
    cls = sp.PROP_CLASS.values.astype(object)
    cnum = pd.to_numeric(pd.Series(cls).str[:3], errors="coerce").values
    kind = np.where((cnum >= 200) & (cnum < 300), "homes", "other")
    main_year = np.where(secondary, np.nan, year)
    unit = pd.Series(town).fillna("").values
    heap_rows = []
    for k, need in (("homes", heap_min), ("other", heap_min_other)):
        my = np.where(kind == k, main_year, np.nan)
        heap_rows += heap_evidence(find_heaps(my, unit, need), my, unit, pt.x.values, pt.y.values, k)
    county_heaps = {k: sorted(int(v) for v in find_heaps(np.where(kind == k, main_year, np.nan), np.full(len(fp), name), need)[name])
                    for k, need in (("homes", heap_min), ("other", heap_min_other))}
    heap = np.zeros(len(fp), bool)
    for r in heap_rows:
        if r["heap"]:
            heap |= (unit == r["town"]) & (kind == r["kind"]) & (year == r["year"])
    # names and surveyed years from the State Historic Preservation Office's inventory
    names = fp.name.where(fp.name.notna(), None).values.astype(object)
    usn = np.full(len(fp), None, object)
    year_hist = np.full(len(fp), np.nan)
    year_hist_ca = np.full(len(fp), np.nan)
    cr = cris_points(key)
    if cr is not None:
        cr = cr.assign(USNName=cr.USNName.fillna("").str.strip())
        hy = [cris_name_year(n) for n in cr.USNName]
        cr["hy"] = [h[0] for h in hy]
        cr["ca"] = [h[1] for h in hy]
        jc = gpd.sjoin(cr[["USNNum", "USNName", "EligibilityDesc", "hy", "ca", "geometry"]],
                       gpd.GeoDataFrame({"fi": np.arange(len(fp))}, geometry=u.values, crs=UTM), predicate="within")
        jc = jc[~jc.EligibilityDesc.fillna("").str.contains("Demolished")]
        jc = jc.assign(dated=jc.hy.notna(), named=jc.USNName.ne(""), listed=jc.EligibilityDesc.eq("Listed"))
        jc = jc.sort_values(["fi", "dated", "listed", "named"], ascending=[True, False, False, False]).drop_duplicates("fi")
        usn[jc.fi.values] = jc.USNNum.values
        year_hist[jc.fi.values] = np.where(jc.ca.values, np.nan, jc.hy.values)
        year_hist_ca[jc.fi.values] = np.where(jc.ca.values, jc.hy.values, np.nan)
        fill = jc[jc.named & pd.isna(names[jc.fi.values]) & ~jc.USNName.str.match(CRIS_GENERIC)]
        names[fill.fi.values] = fill.USNName.values
        log(f"cris {name}: {len(cr)} points in the box, {len(jc)} footprints carry an inventory number, "
            f"{int(np.isfinite(year_hist).sum())} a year and {int(np.isfinite(year_hist_ca).sum())} a 'circa' year from the inventory name, "
            f"{len(fill)} names added")
    # how much of a municipality the assessor's published inventory covers: the share of its
    # main residential buildings (classes 200-299) that carry a year
    mm = pd.DataFrame({"muni": pd.Series(muni).fillna("").values, "ok": np.isfinite(year)})[(kind == "homes") & ~secondary]
    share = mm.groupby("muni").ok.mean()
    muni_share = pd.Series(muni).fillna("").map(share).fillna(0.0).round(3).values
    ll = fp.geometry.representative_point()
    height = fp.height.values.astype(float)
    height = np.where(height > 0, height, np.nan)   # Overture carries a few zero heights
    out = gpd.GeoDataFrame({
        "id": fp.id.values,
        "county": name,
        "muni": pd.Series(muni).fillna("").values,
        "town": pd.Series(town).fillna("").values,
        "height_m": height,
        "height_src": np.where(np.isfinite(height), "overture", ""),
        "floors": fp.num_floors.values.astype(float),
        "year_raw": year,
        "year_src": np.where(np.isfinite(year), "nys_parcels_2025", ""),
        "heap": heap,
        "secondary": secondary,
        "prop_class": pd.Series(cls).fillna("").astype(str).values,
        "use": np.array([use_of(c) for c in cls], dtype=np.int8),
        "year_hist": year_hist,
        "hist_src": np.where(np.isfinite(year_hist), "cris_name", ""),
        "year_hist_ca": year_hist_ca,
        "muni_year_share": muni_share,
        "lon": np.round(ll.x.values, 6),
        "lat": np.round(ll.y.values, 6),
        "name": pd.Series(names).fillna("").values,
        "usn": pd.Series(usn).fillna("").values,
        "parcel": np.where(has, sp.SWIS.fillna("").astype(str).values + " " + sp.PRINT_KEY.fillna("").astype(str).values, ""),
        "n_on_parcel": n_on,
        "area_m2": area,
        "footprint_src": fp.source_dataset.replace({"OpenStreetMap": "overture:osm", "Microsoft ML Buildings": "overture:microsoft",
                                                    "Esri Community Maps": "overture:esri"}).str.replace("NYS ", "nys_bf_").fillna("").values,
    }, geometry=fp.geometry.values, crs=4326)
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / f"ny_{key}.parquet"
    out.to_parquet(f.with_suffix(".part"), index=False)
    f.with_suffix(".part").rename(f)
    report(key, out, heap_rows, county_heaps, counts)
    muni_outlines(key, out)
    return out


def report(key, g, heaps, county_heaps, counts):
    """Coverage per municipality, heap years and the decade histogram -> ny_<county>_report.json / .txt"""
    name = COUNTIES[key][0]
    dated = g.year_raw.notna()
    main = ~g.secondary
    rows = []
    for m, d in g.groupby("muni"):
        dm = d[~d.secondary]
        rows.append({"muni": m or "(no parcel within 300 m)", "town": mode_or_nan(d.town) if len(d) else "", "footprints": len(d),
                     "on_parcel": int((d.parcel != "").sum()), "with_year": int(d.year_raw.notna().sum()),
                     "share_year": round(float(d.year_raw.notna().mean()), 3),
                     "muni_year_share": float(d.muni_year_share.iloc[0]),
                     "main": len(dm), "main_with_year": int(dm.year_raw.notna().sum()),
                     "homes": int((d.use == 1).sum()), "homes_with_year": int(((d.use == 1) & d.year_raw.notna()).sum()),
                     "on_heap": int(d.heap.sum()), "with_height": int(d.height_m.notna().sum())})
    dec = (g.year_raw[dated & main] // 10 * 10).astype(int).value_counts().sort_index()
    dec_all = (g.year_raw[dated] // 10 * 10).astype(int).value_counts().sort_index()
    heap_counts = {}
    for r in heaps:
        if r["heap"]:
            heap_counts.setdefault(r["town"], {}).setdefault(r["kind"], {})[r["year"]] = r["n"]
    rep = {"county": name, "built": time.strftime("%Y-%m-%d"), **counts, "footprints": len(g),
           "with_year": int(dated.sum()), "main_buildings": int(main.sum()), "main_with_year": int((dated & main).sum()),
           "secondary": int(g.secondary.sum()), "on_heap": int(g.heap.sum()), "with_height": int(g.height_m.notna().sum()),
           "with_floors": int(g.floors.notna().sum()), "with_year_hist": int(g.year_hist.notna().sum()),
           "with_year_hist_ca": int(g.year_hist_ca.notna().sum()),
           "named": int((g.name != "").sum()), "no_parcel": int((g.parcel == "").sum()),
           "invalid_geometry": int((~g.geometry.is_valid).sum()),
           "year_min": float(g.year_raw.min()), "year_max": float(g.year_raw.max()),
           "heaps_by_assessing_unit": heap_counts, "heap_evidence": heaps, "county_level_heaps": county_heaps,
           "decades_main": {int(k): int(v) for k, v in dec.items()}, "decades_all": {int(k): int(v) for k, v in dec_all.items()},
           "municipalities": rows}
    (OUT / f"ny_{key}_report.json").write_text(json.dumps(rep, indent=1))
    lines = [f"{name}: {len(g)} footprints ({counts['state_fill']} from the State's layer), {rep['with_year']} with a year "
             f"({rep['with_year'] / len(g):.1%}), {rep['on_heap']} on heap years, {rep['with_height']} with a height, "
             f"{rep['secondary']} secondary, {rep['no_parcel']} outside every parcel",
             "muni | assessing unit | footprints | with year | share | main homes with year (muni_year_share) | on heap | with height"]
    for r in sorted(rows, key=lambda r: r["muni"]):
        lines.append(f"{r['muni']} | {r['town']} | {r['footprints']} | {r['with_year']} | {r['share_year']:.0%} | {r['muni_year_share']:.0%} | {r['on_heap']} | {r['with_height']}")
    lines.append("heaps: " + json.dumps(heap_counts))
    lines.append("flagged by count but one development (not heaps): " + json.dumps([(r["town"], r["kind"], r["year"], r["n"], r["spread"]) for r in heaps if not r["heap"]]))
    lines.append("county-level heaps: " + str(rep["county_level_heaps"]))
    lines.append("decades (main buildings): " + json.dumps(rep["decades_main"]))
    (OUT / f"ny_{key}_report.txt").write_text("\n".join(lines) + "\n")
    log(lines[0])


# ---------------------------------------------------------------------------------------------
# check: well-known buildings against their known dates
# (label, (lat, lon) or a regular expression on the footprint's name, known year, where the year is from)
#   brief   = the date given in this part's brief
#   wp-list = read on 2026-11-10 from https://en.wikipedia.org/wiki/List_of_Registered_Historic_Places_in_Rockland_County,_New_York
#             or https://en.wikipedia.org/wiki/National_Register_of_Historic_Places_listings_in_southern_Westchester_County,_New_York
#   wd      = Wikidata P571 of the building's item, read on 2026-11-10
#   cris    = the year in the State Historic Preservation Office's inventory name
#   memory  = the commonly published date (the building's Wikipedia article), NOT re-read on 2026-11-10
KNOWN = {
    "westchester": [
        ("Yonkers City Hall", (40.93211, -73.89790), 1910, "brief"),
        ("Philipse Manor Hall, Yonkers", (40.93574, -73.89940), 1682, "memory"),
        ("Kykuit, Pocantico Hills", (41.08960, -73.84443), 1913, "memory"),
        ("Westchester County Courthouse, White Plains", (41.02978, -73.76999), 1974, "wd"),
        ("Old Dutch Church of Sleepy Hollow", (41.09041, -73.86190), 1685, "memory"),
        ("John Jay Homestead, Katonah", (41.25158, -73.66037), 1801, "memory"),
        ("Glenview Mansion (Hudson River Museum), Yonkers", (40.95448, -73.89621), 1876, "cris"),
        ("Sherwood House, Yonkers", (40.95205, -73.85497), 1740, "memory"),
        ("Thomas Paine Cottage, New Rochelle", (40.93449, -73.79117), 1793, "memory"),
        ("Leland Castle, New Rochelle", (40.90055, -73.78101), 1859, "memory"),
        ("Jacob Purdy House, White Plains", (41.03689, -73.77309), 1721, "memory"),
        ("White Plains Armory", (41.03131, -73.76250), 1910, "memory"),
        ("Wayside Cottage, Scarsdale", (40.99225, -73.79398), 1720, "memory"),
        ("Playland bathhouse, Rye", (40.96416, -73.67775), 1928, "memory"),
        ("Peter Augustus Jay House (Jay Estate), Rye", (40.95728, -73.70606), 1838, "memory"),
        ("Timothy Knapp House, Rye", (40.96496, -73.68623), 1670, "wp-list"),
        ("Capitol Theatre, Port Chester", (41.00168, -73.66505), 1926, "memory"),
        ("Life Savers Building, Port Chester", (41.00579, -73.65969), 1920, "memory"),
        ("Bolton Priory, Pelham Manor", (40.88610, -73.79430), 1838, "wd"),
        ("Pelhamdale, Pelham Manor", (40.90099, -73.81501), 1750, "memory"),
        ("PepsiCo headquarters, Purchase", (41.03486, -73.69283), 1970, "memory"),
        ("Union Church of Pocantico Hills", (41.09563, -73.83229), 1921, "wd"),
        ("Reader's Digest headquarters, Chappaqua", (41.17950, -73.75587), 1939, "memory"),
        ("Horace Greeley House, Chappaqua", (41.15912, -73.77133), 1820, "memory"),
        ("IBM Watson Research Center, Yorktown", (41.20978, -73.80416), 1961, "memory"),
        ("Alder Manor, Yonkers", (40.97288, -73.88451), 1912, "memory"),
        ("St. Joseph's Seminary, Dunwoodie", (40.93107, -73.86430), 1896, "memory"),
        ("Yonkers station", (40.93560, -73.90234), 1911, "memory"),
        ("Yonkers Main Post Office", (40.93505, -73.90207), 1927, "memory"),
        ("Proctor's Theater, Yonkers", (40.93223, -73.89957), 1916, "memory"),
        ("Proctor's Theater, Mount Vernon", (40.91248, -73.83769), 1913, "cris"),
        ("Lyndhurst, Tarrytown", (41.05397, -73.86736), 1838, "memory"),
        ("Sunnyside, Tarrytown", (41.04760, -73.86987), 1835, "memory"),
        ("Manor House, Larchmont", (40.92531, -73.75184), 1797, "memory"),
        ("Bar Building, White Plains", (41.03262, -73.76753), 1926, "memory"),
        ("Scarsdale station", (40.99000, -73.80814), 1904, "memory"),
        ("Boyce Thompson Institute, Yonkers", (40.97208, -73.88197), 1924, "memory"),
        ("Mamaroneck Methodist Church", (40.95159, -73.72907), 1859, "memory"),
        ("Holy Trinity Church, Mamaroneck", r"Holy Trinity Roman Catholic", 1886, "wd"),
        ("Trump Plaza, New Rochelle", (40.91270, -73.78160), 2007, "wd"),
    ],
    "rockland": [
        ("Edward Hopper House, Nyack", (41.09325, -73.91800), 1858, "memory"),
        ("DeWint House, Tappan", (41.01994, -73.94612), 1700, "memory"),
        ("Tappan Reformed Church", (41.02257, -73.94766), 1835, "memory"),
        ("Nyack Library", (41.08863, -73.91848), 1903, "memory"),
        ("Rockland County Courthouse, New City", (41.14702, -73.99073), 1928, "memory"),
        ("Stony Point Lighthouse", (41.24135, -73.97176), 1826, "memory"),
        ("Lafayette Theatre, Suffern", (41.11469, -74.15018), 1924, "memory"),
        ("Palisades Center, West Nyack", (41.09751, -73.95645), 1998, "memory"),
        ("Old Stone Church, Upper Nyack", (41.10367, -73.91701), 1813, "memory"),
        ("Bear Mountain Inn", (41.31308, -73.98980), 1915, "wp-list"),
        ("Blauvelt-Cropsey Farm, New City (1790s)", (41.13235, -74.00166), 1795, "wp-list"),
        ("First Reformed Church, Piermont", (41.03628, -73.91680), 1946, "wp-list"),
        ("Kings Daughters Public Library, Haverstraw", (41.19661, -73.96071), 1903, "wp-list"),
        ("Jacob Sloat House, Sloatsburg", (41.15551, -74.19487), 1848, "wp-list"),
        ("US Post Office, Haverstraw", (41.19624, -73.96078), 1934, "wp-list"),
        ("US Post Office, Spring Valley", (41.11308, -74.04571), 1936, "wp-list"),
        ("US Post Office, Pearl River", r"POST OFFICE.*PEARL RIVER|PEARL RIVER.*POST OFFICE", 1935, "wp-list"),
        ("North Main Street School, Spring Valley", r"NORTH MAIN STREET SCHOOL", 1916, "wp-list"),
        ("Camp Hill School, Pomona", r"CAMP HILL SCHOOL", 1923, "wp-list"),
        ("Pig Knoll School, Pomona", r"PIG KNOLL", 1915, "wp-list"),
        ("English Church, New City", r"ENGLISH CHURCH", 1827, "wp-list"),
        ("John Green House, Nyack", r"JOHN GREEN HOUSE", 1819, "wp-list"),
        ("The Homestead, Haverstraw (c. 1800)", r"^(?:THE )?HOMESTEAD\b", 1800, "wp-list"),
        ("Edward Salyer House, Pearl River", r"EDWARD SALYER", 1765, "wp-list"),
        ("Michael Salyer Stone House, Orangetown", r"MICHAEL SALYER", 1790, "wp-list"),
        ("McCready House, Sloatsburg", r"MCCREADY", 1889, "wp-list"),
        ("William H. Rose House, Stony Point (c. 1862)", r"ROSE HOUSE", 1862, "wp-list"),
        ("Sloat House, Sloatsburg", r"^SLOAT HOUSE", 1755, "wp-list"),
        ("H. R. Stevens House, New City", r"STEVENS HOUSE", 1775, "wp-list"),
        ("Tallman-Budke House, Clarkstown", r"TALLMAN.?BUDKE", 1790, "wp-list"),
        ("House at 352 Piermont Avenue", r"352 PIERMONT", 1780, "wp-list"),
    ],
}


def check(key):
    import geopandas as gpd
    import shapely
    f = OUT / f"ny_{key}.parquet"
    if key not in KNOWN or not f.exists():
        return
    g = gpd.read_parquet(f)
    u = g.geometry.to_crs(UTM)
    tree = shapely.STRtree(u.values)
    to_utm = __import__("pyproj").Transformer.from_crs(4326, UTM, always_xy=True)
    lines, tally = [], {}
    for label, where, known, src in KNOWN[key]:
        i = None
        if isinstance(where, tuple):
            pt = shapely.Point(*to_utm.transform(where[1], where[0]))
            i = tree.nearest(pt)
            if u.values[i].distance(pt) > 40:
                i = None
        else:
            m = g.index[g.name.str.contains(where, case=False, regex=True)]
            if len(m):
                i = g.area_m2.loc[m].idxmax()
        if i is None:
            verdict, detail = "no footprint found", ""
        else:
            r = g.iloc[i]
            best = r.year_hist if np.isfinite(r.year_hist) else r.year_raw
            if not np.isfinite(best):
                verdict = "no year"
            else:
                d = abs(best - known)
                verdict = "hit" if d <= 3 else "near (<= 10 y)" if d <= 10 else "miss"
                if np.isfinite(r.year_hist):
                    verdict += " by the inventory year"
                elif r.heap:
                    verdict += " (flagged heap)"
            detail = (f"assessor {'-' if not np.isfinite(r.year_raw) else int(r.year_raw)}{' heap' if r.heap else ''}"
                      f"{' secondary' if r.secondary else ''}, inventory {'-' if not np.isfinite(r.year_hist) else int(r.year_hist)}, "
                      f"class {r.prop_class or '-'}, {r.muni}, \"{r['name'][:40]}\"")
        tally[verdict.split(" (")[0].split(" by")[0]] = tally.get(verdict.split(" (")[0].split(" by")[0], 0) + 1
        lines.append(f"{label} | {known} ({src}) | {verdict} | {detail}")
    lines.append("tally: " + json.dumps(tally))
    (OUT / f"ny_{key}_checks.txt").write_text("\n".join(lines) + "\n")
    log(f"check {COUNTIES[key][0]}: {tally}")


def main(argv):
    cmd = argv[0] if argv and argv[0] in ("download", "build", "check") else "all"
    keys = [a.lower() for a in argv if a.lower() in COUNTIES] or list(COUNTIES)
    for key in keys:
        if cmd in ("download", "all"):
            if download_parcels(key):
                download_state_footprints(key)
                download_cris(key)
                download_civil(key)
        if cmd in ("build", "all"):
            build(key)
        if cmd in ("check", "all"):
            check(key)


if __name__ == "__main__":
    main(sys.argv[1:])
