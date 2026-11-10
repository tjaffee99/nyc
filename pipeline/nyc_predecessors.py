"""What stood before today's buildings: footprints traced from historical maps and
documented lost buildings, each with a lifespan.

Sources (best first — documented > traced > generated):
  * documented lost buildings: OpenHistoricalMap (CC0) buildings with their own end date
    (data/manual/ohm/nyc_buildings.geojson, rows without a map year whose end is `dated`);
  * traced map layers, each a set of outlines standing in its map year:
      - NYPL Building Inspector (CC0): Perris atlas of Manhattan 1857-62 (Battery to ~86th
        St), Brooklyn 1855, later atlases (Midtown 1890, below Houston St 1894, parts
        1887-1915) — data/raw/nypl; wall material from the atlas colour (pink = brick or
        stone, yellow = frame);
      - NYPL's 1854 footprints of Manhattan to 42nd St, via OpenHistoricalMap
        (data/manual/ohm/nyc_buildings_nypl1854.geojson, 61,637 outlines);
      - volunteers' tracings in OpenHistoricalMap with a map year: the Castello Plan
        (New Amsterdam, 1660), the 1728 survey, Grim 1742, Maerschalck 1755, Dripps 1852,
        Sanborn 1888 / 1890 / 1894, Bromley 1902 / 1930.
    Outlines are real; years and heights are estimated here (`estimated`), by these rules:

  survivors   a traced outline that coincides with a building standing today (IoU >= 0.6,
              or the two cover most of each other) IS that building and is not drawn
              twice; if today's year was only an estimate later than the map, today's
              building is re-dated to before the map (the map shows it standing).
  one each    the same structure on several maps is emitted once, from the first map that
              shows it (later maps extend its life). Two tracings of maps less than 8 years
              apart that overlap are one building drawn twice: the earlier map's outline stays.
  start       a researched start if OHM has one; else between the earlier COMPLETE layer
              covering the block (1660, 1854) that does not show it and the map that does;
              else between the built-up extent snapshots around the site
              (data/manual/extents), else up to 30 (at most 60) years before the map; never
              before the settlement (1625).
  end         a researched end if OHM has one; else when a different structure appears on
              the spot on a later map; else when today's building on the spot went up;
              under a park, when the park was made; with nothing on the ground today, when
              the big building beside it went up, else a spread after the map. The traced
              layers are incomplete, so absence from a later map is NOT evidence. A fire
              outline (data/manual/extents/fire_<year>.geojson) ends what stood inside it.
              Structures first mapped before 1800 with no other evidence are given 50-110
              years of life.
  storeys     by material, size, date and district (era-typical; the atlases give storeys
              but the data does not carry them); documented buildings keep OHM's height.
  overlaps    no two structures on one spot at once (documented > traced; among traced the
              later one starts when the earlier ends, or goes).

Called by nyc_buildings.py: add_predecessors(g) -> g with the vanished structures appended
and the survivors re-dated.
"""
from __future__ import annotations

import json
import zlib

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
import shapely.affinity
from scipy.spatial import cKDTree

from building_binary import (M_BARK, M_BRICK, M_BROWNSTONE, M_DUTCH, M_EARLY, M_FRAME, M_MASONRY, R_FLAT, R_SHINGLE, R_TILE,
                             R_WALL)
from common import MANUAL, NYC_CRS, RAW, YEAR_MIN, log

UTM = NYC_CRS
BI = RAW / "nypl" / "building-inspector.objects.ndjson"
OHM = MANUAL / "ohm"
BORO_CODE = {"Manhattan": "1", "Bronx": "2", "Brooklyn": "3", "Queens": "4", "Staten Island": "5"}
SETTLED = 1625.5            # nothing European stands before Fort Amsterdam was begun
COMPLETE = {1660, 1854}     # layers that show every building of their area
SAME_SURVEY = 8             # tracings of maps closer than this are one survey drawn twice
COLS = ["id", "map_year", "boro", "colors", "name", "start_doc", "end_doc", "h_doc", "cls", "geometry"]


def h01(key) -> float:
    return (zlib.crc32(str(key).encode()) % 100003) / 100003.0


def hashes(keys, salt=""):
    return np.array([h01(f"{salt}{k}") for k in keys])


def load_bi():
    rows = []
    if not BI.exists():
        return rows
    with open(BI) as f:
        for line in f:
            o = json.loads(line)
            if o.get("type") != "st:Building" or (o.get("geometry") or {}).get("type") != "Polygon":
                continue
            d = o["data"]
            ring = o["geometry"]["coordinates"][0]
            if len(ring) < 4:
                continue
            rows.append((f"bi:{o['id']}", int(o["validSince"]), BORO_CODE.get(d.get("borough"), ""),
                         ",".join(d.get("colors") or []), None, np.nan, np.nan, np.nan, "traced", shapely.Polygon(ring)))
    return rows


def load_ohm():
    rows = []
    for fn in ("nyc_buildings_nypl1854.geojson", "nyc_buildings.geojson"):
        p = OHM / fn
        if not p.exists():
            continue
        for f in json.load(open(p))["features"]:
            pr = f["properties"]
            if str(pr.get("campaign") or "").startswith("NYC Building Footprints import") or pr.get("today") == "no_data":
                continue
            if pr.get("survivor_suspect"):
                continue
            g = shapely.geometry.shape(f["geometry"])
            g = max(getattr(g, "geoms", [g]), key=lambda q: q.area)
            if g.geom_type != "Polygon":
                continue
            s_doc = float(pr["start_year"]) if pr.get("start_quality") == "dated" and pr.get("start_year") is not None else np.nan
            e_doc = float(pr["end_year"]) if pr.get("end_quality") == "dated" and pr.get("end_year") is not None else np.nan
            if np.isfinite(e_doc) and e_doc >= 2026:
                e_doc = np.nan
            h = pr.get("height_m")
            lv = pr.get("levels")
            try:
                h_doc = float(h) if h else (float(lv) * 3.4 + 1.0 if lv else np.nan)
            except (TypeError, ValueError):
                h_doc = np.nan
            my = pr.get("map_year")
            if my is not None:
                cls, my = "traced", int(my)
            elif np.isfinite(e_doc):
                cls, my = "documented", int(np.floor(e_doc)) - 1
            else:
                continue   # a standing or undated building: today's data has it
            rows.append((f"ohm:{pr['ohm_id']}", my, BORO_CODE.get(pr.get("borough"), ""), "", pr.get("name"),
                         s_doc, e_doc, h_doc, cls, g))
    return rows


def load_structures():
    rows = load_bi() + load_ohm()
    t = gpd.GeoDataFrame(pd.DataFrame(rows, columns=COLS), geometry="geometry", crs=4326).to_crs(UTM)
    t["conf_doc"] = None
    t["mat_doc"] = ""
    # researched extras (nyc_extras.py): early sites, documented lost buildings, the city's
    # record of removed buildings, atlas layers traced for this map
    import nyc_extras
    extra = []
    for fn in (nyc_extras.early_sites, nyc_extras.notable, nyc_extras.demolished, nyc_extras.atlas_layers):
        try:
            extra += fn()
        except Exception as e:  # noqa: BLE001
            log(f"predecessors: {fn.__name__} not used ({type(e).__name__}: {e})")
    if extra:
        x = gpd.GeoDataFrame(pd.DataFrame(extra), geometry="geometry", crs=UTM)
        x["boro"] = nyc_extras.boro_of(x.geometry.representative_point().to_crs(4326).values)
        t = gpd.GeoDataFrame(pd.concat([t, x[list(t.columns)]], ignore_index=True), geometry="geometry", crs=UTM)
    t["mat_doc"] = t.mat_doc.fillna("").astype(str)
    t["geometry"] = t.geometry.buffer(0)
    t = t[t.geometry.geom_type == "Polygon"]
    t["area"] = t.geometry.area
    t = t[(t["area"] > 14) & ((t["area"] < 8000) | (t.cls == "documented"))].reset_index(drop=True)
    # within one map layer, overlapping outlines are one building drawn twice: keep the larger
    drop = np.zeros(len(t), bool)
    tr = t[t.cls == "traced"]
    for _, grp in tr.groupby([tr.id.str.rsplit(":", n=1).str[0], "map_year"]):
        ii, jj = grp.sindex.query(grp.geometry.values, predicate="intersects")
        m = ii < jj
        ii, jj = ii[m], jj[m]
        inter = shapely.area(shapely.intersection(grp.geometry.values[ii], grp.geometry.values[jj]))
        a, b = grp["area"].values[ii], grp["area"].values[jj]
        dup = inter > 0.5 * np.minimum(a, b)
        drop[grp.index.values[np.where(a >= b, jj, ii)[dup]]] = True
    t = t[~drop].reset_index(drop=True)
    by = t[t.cls == "traced"].groupby("map_year").size().to_dict()
    log(f"predecessors: {int((t.cls == 'traced').sum())} traced outlines by map year {by}; "
        f"{int((t.cls == 'documented').sum())} documented lost buildings; {int(drop.sum())} duplicates dropped")
    return t


def overlaps(a_geoms, b_gdf):
    """Pairs (i, j, intersection area) between an array of polygons and a GeoDataFrame."""
    ii, jj = b_gdf.sindex.query(a_geoms, predicate="intersects")
    inter = shapely.area(shapely.intersection(a_geoms[ii], b_gdf.geometry.values[jj]))
    keep = inter > 1.0
    return ii[keep], jj[keep], inter[keep]


PLACE_BORO = {"manhattan": "1", "bronx": "2", "brooklyn": "3", "williamsburgh": "3", "queens": "4", "staten_island": "5"}
# the fires' days (the outlines in data/manual/extents/fire_<year>.geojson are estimated from text)
FIRE_DATES = {1776: 1776.72, 1835: 1835.96, 1845: 1845.55}


def extent_snapshots():
    """({borough code: [(year, polygon)]}, [(decimal year, polygon)] of the fires). The
    snapshots of one borough and year (Brooklyn and Williamsburgh 1836) are one polygon."""
    d = MANUAL / "extents"
    per, fires = {}, []
    for f in sorted(d.glob("*_[0-9][0-9][0-9][0-9].geojson")) if d.exists() else []:
        try:
            g = gpd.read_file(f).to_crs(UTM)
            poly = shapely.union_all(list(g.geometry.buffer(0)))
            place, year = f.stem.rsplit("_", 1)
            year = int(year)
            if place == "fire":
                fires.append((FIRE_DATES.get(year, year + 0.5), poly))
            elif place in PLACE_BORO:
                per.setdefault(PLACE_BORO[place], {}).setdefault(year, []).append(poly)
        except Exception as e:  # noqa: BLE001
            log(f"predecessors: skip {f.name} ({e})")
    snaps = {b: sorted((y, shapely.union_all(ps)) for y, ps in ys.items()) for b, ys in per.items()}
    return snaps, sorted(fires, key=lambda s: s[0])


def extent_bounds(xy, boro, snaps):
    """Per site, from its own borough's snapshots: the last year that leaves it out (lo) and
    the first that has it (hi). NaN where the borough has no snapshot (or none before / after)."""
    lo = np.full(len(xy), np.nan)
    hi = np.full(len(xy), np.nan)
    pts = shapely.points(xy)
    for b, series in snaps.items():
        sel = np.asarray(boro) == b
        if not sel.any():
            continue
        lo_b = np.full(int(sel.sum()), np.nan)
        hi_b = np.full(int(sel.sum()), np.nan)
        for year, poly in series:
            shapely.prepare(poly)
            inside = shapely.contains(poly, pts[sel])
            hi_b[inside & np.isnan(hi_b)] = year
            lo_b[~inside & np.isnan(hi_b)] = year
        lo[sel], hi[sel] = lo_b, hi_b
    return lo, hi


def storeys_of(colors, area, my, y_utm, boro, hsh):
    """Era-typical storeys: estimated."""
    frame = np.array([c == "yellow" for c in colors])
    st = np.where(frame, np.where(area < 55, 1.5, np.where(hsh < 0.6, 2, 3)),
                  np.where(area < 45, 2, np.where(area < 130, np.where(hsh < 0.55, 3, 4), np.where(hsh < 0.5, 4, 5))))
    # the commercial city below Canal St (UTM northing of Canal St at Broadway ~ 4,508,300 m)
    core = (boro == "1") & (y_utm < 4_508_300)
    st = np.where(core & ~frame & (my >= 1830), st + 1, st)
    st = np.where((my >= 1885) & ~frame, np.maximum(st, np.where(area > 150, 5 + (hsh < 0.4), 4)), st)
    # the colonial town: one to three storeys under steep roofs
    st = np.where(my < 1700, np.where(area < 60, 1.5, 2 + (hsh < 0.3)), st)
    st = np.where((my >= 1700) & (my < 1800), np.where(area < 60, 2, 2.5 + (hsh < 0.4)), st)
    return st.astype(float), frame


def add_predecessors(g):
    if not BI.exists() and not OHM.exists():
        log("predecessors: no traced layers on disk - nothing added")
        return g
    t = load_structures()
    gu = gpd.GeoDataFrame({"start": g.start_year.values, "src": g.year_src.values, "area": g["area"].values},
                          geometry=g.geometry.to_crs(UTM).values, crs=UTM)
    # ---- survivors: the traced outline is a building that stands today
    ii, jj, inter = overlaps(t.geometry.values, gu)
    df = pd.DataFrame({"i": ii, "j": jj, "inter": inter})
    df["fa"] = df.inter / t["area"].values[df.i]
    df["fb"] = df.inter / gu["area"].values[df.j]
    df["iou"] = df.inter / (t["area"].values[df.i] + gu["area"].values[df.j] - df.inter)
    df["tstart"] = gu.start.values[df.j]
    df["texact"] = np.isin(gu.src.values[df.j], ["lpc", "assessor", "known"])
    df["my"] = t.map_year.values[df.i]
    df["traced"] = t.cls.values[df.i] == "traced"
    same = (df.iou >= 0.6) | ((df.fa >= 0.75) & (df.fb >= 0.6))
    # a recorded year after the map says today's building replaced the one on the map
    df["survivor"] = df.traced & same & ~(df.texact & (df.tstart > df.my + 2))
    surv_i = set(df.i[df.survivor])
    redate = df[df.survivor & ~df.texact & (df.tstart > df.my)].sort_values("my").drop_duplicates("j")
    start = g.start_year.values.copy()
    conf = g.year_confidence.values.copy()
    src = g.year_src.values.copy()
    start[redate.j.values] = redate.my.values - 2.0 - 22.0 * hashes(redate.j.values, "s")
    conf[redate.j.values] = "estimated"
    src[redate.j.values] = "on_map"
    g = g.assign(start_year=start, year_confidence=conf, year_src=src)
    gu["start"] = start
    # also not drawn: an outline inside a standing building recorded as older than the map (a wing of it)
    inside_old = set(df.i[df.traced & (df.fa >= 0.6) & df.texact & (df.tstart <= df.my + 2)])
    keep = np.array([k not in surv_i and k not in inside_old for k in range(len(t))])
    log(f"predecessors: {len(surv_i)} traced outlines are buildings standing today ({len(redate)} of those re-dated "
        f"to before their map), {len(inside_old - surv_i)} lie inside older standing buildings")
    v = t[keep].reset_index(drop=True)

    # ---- one structure per building across maps
    v["last_seen"] = v.map_year.astype(float)
    v["first"] = True
    v["repl_by"] = np.nan     # map year of a different structure that took the spot
    tr_years = sorted(v.map_year[v.cls == "traced"].unique())
    for y2 in tr_years[1:]:
        late = v[(v.map_year == y2) & v["first"] & (v.cls == "traced")]
        early = v[(v.map_year < y2) & v["first"] & (v.cls == "traced")]
        if not len(late) or not len(early):
            continue
        i2, j2, it = overlaps(late.geometry.values, early)
        a, b = late["area"].values[i2], early["area"].values[j2]
        gap = y2 - early.map_year.values[j2]
        match = (it / (a + b - it) >= 0.45) | ((it / a >= 0.6) & (it / b >= 0.6))
        touch = it > 0.4 * np.minimum(a, b)
        # the same building on a later map (or the same survey traced twice): the earlier outline stays
        same_b = match | (touch & (gap < SAME_SURVEY))
        li, ei = late.index.values[i2], early.index.values[j2]
        v.loc[np.unique(li[same_b]), "first"] = False
        ext = pd.DataFrame({"e": ei[match], "y": float(y2)}).groupby("e").y.max()
        v.loc[ext.index.values, "last_seen"] = np.maximum(v.loc[ext.index.values, "last_seen"].values, ext.values)
        # a different structure on the spot a survey later: the earlier one was replaced before it
        rep = touch & ~same_b
        rp = pd.DataFrame({"e": ei[rep], "y": float(y2)}).groupby("e").y.min()
        cur = v.loc[rp.index.values, "repl_by"].values
        v.loc[rp.index.values, "repl_by"] = np.where(np.isnan(cur), rp.values, np.minimum(cur, rp.values))
    v = v[v["first"]].reset_index(drop=True)
    # documented buildings win: a traced outline mostly inside one is that building
    doc = v[v.cls == "documented"]
    if len(doc):
        trc = v[v.cls == "traced"]
        i4, j4, it4 = overlaps(trc.geometry.values, doc)
        hit = it4 > 0.5 * trc["area"].values[i4]
        v = v.drop(index=np.unique(trc.index.values[i4[hit]])).reset_index(drop=True)
    n = len(v)
    cen = v.geometry.representative_point()
    xy = np.column_stack([cen.x.values, cen.y.values])
    my = v.map_year.values.astype(float)
    hsh, hsh2, h3 = hashes(v.id), hashes(v.id, "e"), hashes(v.id, "w")
    hb = np.array([h01(f"b{int(a)}_{int(b)}") for a, b in zip(np.floor(xy[:, 0] / 80), np.floor(xy[:, 1] / 80))])
    hk = (hb + 0.35 * hsh) % 1.0   # uniform; neighbours in an ~80 m block get dates close together

    # ---- start
    prev_map = np.full(n, np.nan)
    for y in sorted(COMPLETE):
        pts = t[(t.map_year == y) & (t.cls == "traced")].geometry.representative_point()
        if len(pts) < 4:
            continue
        d, _ = cKDTree(np.column_stack([pts.x.values, pts.y.values])).query(xy, k=4, distance_upper_bound=70.0)
        # (not from a map of the same survey years: tracing differences are not new buildings)
        prev_map = np.where(np.isfinite(d[:, 3]) & (y <= my - SAME_SURVEY), y, prev_map)
    snaps, fires = extent_snapshots()
    lo, hi = extent_bounds(xy, v.boro.values, snaps)
    start = np.where(np.isfinite(prev_map), prev_map + 0.5 + (my - prev_map - 1.0) * hk, np.nan)
    # (a snapshot only a few years older than the map is no lower bound: the outlines are
    # generalised and leave scattered houses out — keep at least a 15-year window)
    a = np.maximum(np.maximum(np.where(np.isfinite(lo), np.minimum(lo, my - 15.0), my - 30.0), my - 60.0), SETTLED)
    b = np.maximum(my - 1.0, a + 0.5)
    # (a snapshot within 5 years of the map cannot separate a first building from a rebuild)
    has_hi = np.isfinite(hi) & (hi < b - 5.0) & (hi > a)
    first_gen = has_hi & (h3 < 0.55)
    est = np.where(first_gen, a + (hi - a) * hk, np.where(has_hi, hi + (b - hi) * hk, a + (b - a) * np.sqrt(hk)))
    start = np.where(np.isnan(start), est, start)
    sdoc = v.start_doc.values.astype(float)
    start = np.where(np.isfinite(sdoc), sdoc, start)
    documented_start = np.isfinite(sdoc)

    # ---- end
    i3, j3, it3 = overlaps(v.geometry.values, gu)
    ov = pd.DataFrame({"i": i3, "j": j3, "f": it3 / v["area"].values[i3], "fb": it3 / gu["area"].values[j3],
                       "tstart": gu.start.values[j3]})
    # today's building took the spot: it covers a good part of the old outline, or lies mostly inside it
    ov["iou"] = it3 / (v["area"].values[i3] + gu["area"].values[j3] - it3)
    ov2 = ov[(ov.f >= 0.3) | (ov.fb >= 0.5)].sort_values("tstart").drop_duplicates("i").set_index("i")
    t_today = ov2.tstart.reindex(range(n)).values.astype(float)
    j_today = ov2.j.reindex(range(n)).fillna(-1).values.astype(int)
    iou_today = ov2.iou.reindex(range(n)).fillna(0).values
    end = t_today - 0.8 - 1.2 * hsh2
    rb = v.repl_by.values.astype(float)
    by_map = v.last_seen.values + 1.0 + (rb - v.last_seen.values - 1.5) * hsh2
    end = np.where(np.isfinite(rb) & (np.isnan(end) | (end > by_map)), by_map, end)
    bare = np.isnan(end)
    if bare.any():
        end_bare = np.full(n, np.nan)
        try:
            pk = gpd.read_file(RAW / "nyc" / "parks_properties.geojson").to_crs(UTM)
            yr = pd.to_datetime(pk.acquisitiondate, errors="coerce").dt.year.values.astype(float)
            pk = pk.assign(y=yr)[np.isfinite(yr)]
            pi, pj = pk.sindex.query(cen.values[bare], predicate="within")
            end_bare[np.nonzero(bare)[0][pi]] = pk.y.values[pj]
        except Exception as e:  # noqa: BLE001
            log(f"predecessors: parks not used ({e})")
        big = gu[gu["area"] > 600]
        bp = big.geometry.representative_point()
        d, j = cKDTree(np.column_stack([bp.x.values, bp.y.values])).query(xy, k=1, distance_upper_bound=70.0)
        near = np.where(np.isfinite(d), big.start.values[np.minimum(j, len(big) - 1)], np.nan) - 1.5
        end_bare = np.where(np.isnan(end_bare), near, end_bare)
        end_bare = np.where(np.isnan(end_bare), np.maximum(v.last_seen.values + 20.0, 1900.0) + 50.0 * hsh2, end_bare)
        end = np.where(bare, end_bare, end)
    # structures first mapped before 1800: without other evidence, 50-110 years of life
    old = (my < 1800) & ~np.isfinite(rb)
    end = np.where(old, np.minimum(end, np.maximum(start, v.last_seen.values) + 50.0 + 60.0 * hsh2 - (v.last_seen.values - start).clip(0, 40)), end)
    # fires: what stood inside the burned district ends with it (unless a later map still shows it)
    pts = shapely.points(xy)
    for when, poly in fires:
        shapely.prepare(poly)
        burned = shapely.contains(poly, pts) & (start < when) & (end > when) & (v.last_seen.values < when)
        end = np.where(burned, when, end)
    # never before the last map that shows it
    end = np.maximum(end, v.last_seen.values + 0.5 + 3.0 * hsh2)
    edoc = v.end_doc.values.astype(float)
    end = np.where(np.isfinite(edoc), edoc, end)
    # ---- against the building standing on the spot today
    traced_ = v.cls.values == "traced"
    t_exact = (j_today >= 0) & np.isin(gu.src.values[np.maximum(j_today, 0)], ["lpc", "assessor", "known"])
    late_map = traced_ & np.isfinite(t_today) & (t_today <= v.last_seen.values + 1.0)
    # the map shows a clearly different building where today's stands, and today's year is only
    # an estimate: today's building is later than the map (estimated)
    redate2 = late_map & ~t_exact & (iou_today < 0.4)
    if redate2.any():
        rd = pd.DataFrame({"j": j_today[redate2], "y": v.last_seen.values[redate2] + 1.0 + 5.0 * hsh2[redate2]}).groupby("j").y.max()
        gs = g.start_year.values.copy()
        gc = g.year_confidence.values.copy()
        gsrc = g.year_src.values.copy()
        gs[rd.index.values] = np.maximum(gs[rd.index.values], rd.values)
        gc[rd.index.values] = "estimated"
        gsrc[rd.index.values] = "after_map"
        g = g.assign(start_year=gs, year_confidence=gc, year_src=gsrc)
        t_today = np.where(redate2, rd.reindex(j_today).values, t_today)
        log(f"predecessors: {len(rd)} standing buildings re-dated to after the map that shows another building on their spot")
    # today's building is recorded as older than the last map (or has much the same outline):
    # the traced outline is that building drawn differently, not a second building
    conflict = late_map & ~redate2
    # nothing vanished outlasts the start of the building standing on its spot (a documented
    # building that starts no earlier than today's is that building under an old name: it goes)
    end = np.where(np.isfinite(t_today), np.minimum(end, t_today - 0.3), end)
    start = np.where(documented_start, start, np.minimum(start, end - 1.0))
    # (the researched early sites — Lenape settlements, the first Dutch landings — are older than the fort)
    early_site = v.id.str.startswith("early:").values
    start = np.maximum(start, np.where(early_site & documented_start, float(YEAR_MIN), SETTLED))

    # ---- shape and material
    st, frame = storeys_of(v.colors.values, v["area"].values, my, xy[:, 1], v.boro.values, hsh)
    H = st * np.where(frame, 3.0, 3.3) + 1.0
    hdoc = v.h_doc.values.astype(float)
    H = np.where(np.isfinite(hdoc) & (hdoc > 2), hdoc, H)
    st = np.where(np.isfinite(hdoc) & (hdoc > 2), np.maximum(1, np.round(hdoc / 3.4)), st)
    stone = np.array([("blue" in c) or ("gray" in c) for c in v.colors.values])
    brown = (my >= 1885) & ~frame & (v["area"].values < 160) & (xy[:, 1] > 4_509_500) & (hsh2 < 0.5)
    mat = np.where(frame, M_FRAME, np.where(stone, M_MASONRY, np.where(brown, M_BROWNSTONE, M_BRICK)))
    mat = np.where(start < 1700, M_DUTCH, np.where((start < 1790) & (hsh2 < 0.5), M_EARLY, mat)).astype(np.uint8)
    roof = np.where(frame, R_SHINGLE, R_FLAT)
    roof = np.where(start < 1700, R_TILE, np.where(start < 1830, R_SHINGLE, roof)).astype(np.uint8)
    # a researched wall material (lost buildings, early sites) beats the era's
    md = v.mat_doc.values.astype(str)
    for words, code, rf in ((("bark",), M_BARK, R_WALL), (("frame", "wood", "timber", "clapboard", "log"), M_FRAME, R_SHINGLE),
                            (("brownstone",), M_BROWNSTONE, None), (("brick",), M_BRICK, None),
                            (("stone", "granite", "marble", "limestone", "masonry"), M_MASONRY, None)):
        hit = np.array([any(w in m for w in words) for m in md]) & (md != "")
        mat = np.where(hit, code, mat).astype(np.uint8)
        if rf is not None:
            roof = np.where(hit, rf, roof).astype(np.uint8)
        md = np.where(hit, "", md)
    is_doc = v.cls.values == "documented"
    pre = v.id.str.split(":").str[0].values
    lenape = early_site & (v.mat_doc.values == "bark")
    srcs = np.where(lenape, "lenape_site", np.where(pre == "early", "early_site", np.where(pre == "notable", "lost_researched",
            np.where(pre == "demo", "city_demolition", np.where(is_doc, "ohm_documented",
            np.where(pre == "ohm", "map_", np.where(pre == "atlas", "traced_", "atlas_")).astype(object) + v.map_year.astype(str).values)))))
    conf_out = np.where(is_doc & documented_start, "exact", "estimated").astype(object)
    cd = v.conf_doc.values
    has_cd = np.array([isinstance(c, str) and c != "" for c in cd])
    conf_out = np.where(has_cd, cd, conf_out)
    # a dwelling placed by a hash inside its site gives way to any outline that is real
    rank = np.where(conf_out == "procedural", 0, is_doc.astype(int) + 1)
    out = gpd.GeoDataFrame({"start_year": start, "end_year": end, "height_m": H, "year_confidence": conf_out,
                            "use": np.uint8(0), "raw_year": 0.0, "stories": st, "mat": mat, "roof": roof,
                            "fid_key": v.id.values, "boro": v.boro.values, "year_src": srcs, "name": v.name.values,
                            "area": v["area"].values, "part_base": 0.0, "doitt_id": v.id.values, "rank": rank,
                            "map_year": my},
                           geometry=v.geometry.values, crs=UTM)[~conflict & (end > start + 0.5)]
    gen = generate_earlier(out, snaps, fires)
    if len(gen):
        out = gpd.GeoDataFrame(pd.concat([out, gen], ignore_index=True), geometry="geometry", crs=UTM)
    out = out.drop(columns=["map_year"]).to_crs(4326)
    # nothing stands before its ground (ground_rule.py): traced, documented and generated alike
    from ground_rule import earliest_start
    es = earliest_start(out.geometry.values, out.height_m.values.astype(float))
    wet = np.isfinite(es) & (out.start_year.values < es)
    st2 = np.where(wet, es + 0.5 * hashes(out.fid_key.values, "gr"), out.start_year.values)
    gone = st2 > out.end_year.values - 1.0
    log(f"predecessors: {int(wet.sum())} vanished structures moved to after their ground was made, "
        f"{int((wet & gone).sum())} of them dropped (the ground came after they were gone)")
    out = out.assign(start_year=st2)[~(wet & gone)]
    out = resolve_overlaps(out)
    from nyc_buildings import Ground, ring_ground
    gmin, gmean = ring_ground(Ground(), out.geometry.values)
    out = out.assign(height=out.height_m.values + (gmean - gmin) + 1.0, base=gmin - 1.0).drop(columns=["rank"])
    log(f"predecessors: + {len(out)} vanished structures ({int(np.isin(out.year_src, ['ohm_documented', 'lost_researched', 'city_demolition']).sum())} documented, "
        f"{int(np.isin(out.year_src, ['lenape_site', 'early_site']).sum())} at early sites, "
        f"{int((out.year_src == 'generated').sum())} generated; "
        f"{int(conflict.sum())} dropped as redrawn standing buildings; snapshots {sum(len(v_) for v_ in snaps.values())}, fires {len(fires)}); "
        f"start {np.percentile(out.start_year, [5, 50, 95]).round(0).tolist()}, end {np.percentile(out.end_year, [5, 50, 95]).round(0).tolist()}; "
        f"standing 1660 {int(((out.start_year <= 1660) & (out.end_year > 1660)).sum())}, 1750 {int(((out.start_year <= 1750) & (out.end_year > 1750)).sum())}, "
        f"1850 {int(((out.start_year <= 1850) & (out.end_year > 1850)).sum())}")
    both = pd.concat([g, out], ignore_index=True)
    return gpd.GeoDataFrame(both, geometry="geometry", crs=4326)


def resolve_overlaps(out):
    """No two vanished structures on one spot at once: where two overlap in space (> 40 % of
    the smaller) and time, a documented one wins; otherwise the later-starting one begins
    when the earlier ends, or goes."""
    u = out.to_crs(UTM)
    ii, jj = u.sindex.query(u.geometry.values, predicate="intersects")
    m = ii < jj
    ii, jj = ii[m], jj[m]
    inter = shapely.area(shapely.intersection(u.geometry.values[ii], u.geometry.values[jj]))
    a = u.geometry.area.values
    hit = inter > 0.4 * np.minimum(a[ii], a[jj])
    s = out.start_year.values.copy()
    e = out.end_year.values.copy()
    rank = out["rank"].values
    drop = np.zeros(len(out), bool)
    for i, j in zip(ii[hit], jj[hit]):
        if drop[i] or drop[j] or s[i] >= e[j] or s[j] >= e[i]:
            continue
        if rank[i] != rank[j]:
            lose, win = (i, j) if rank[i] < rank[j] else (j, i)
            # the weaker evidence gives way: it ends when the better one starts, starts when
            # that one is gone, or goes
            if s[lose] < s[win] - 2.0:
                e[lose] = s[win] - 0.5
            elif e[lose] > e[win] + 2.0:
                s[lose] = e[win] + 0.5
            else:
                drop[lose] = True
            continue
        first, second = (i, j) if s[i] <= s[j] else (j, i)
        if e[second] - e[first] > 2.0:
            s[second] = e[first] + 0.3
        else:
            drop[second if a[second] <= a[first] else first] = True
    out = out.assign(start_year=s, end_year=e)[~drop]
    log(f"predecessors: {int(drop.sum())} overlapping vanished structures dropped")
    return out


# persons per building (dwellings, stores, workshops together), from the counts that exist:
# 1656 first survey 120 houses / 1,000 people; 1660 Castello Plan ~340 houses / ~1,500;
# 1766 ~3,200 houses / ~20,000; 1850 census 37,700 dwellings / 515,500 (Manhattan)
PPB = [(1626, 5.0), (1660, 4.5), (1730, 6.0), (1770, 6.3), (1800, 8.0), (1830, 11.0), (1850, 13.5)]


def population_series(area):
    from common import TABLES
    p = TABLES / "population.csv"
    if not p.exists():
        return None
    t = pd.read_csv(p)
    t = t[t.area.astype(str).str.lower().str.strip() == area]
    y = pd.to_numeric(t.year, errors="coerce").values
    v = pd.to_numeric(t.population.astype(str).str.replace(",", ""), errors="coerce").values
    ok = np.isfinite(y) & np.isfinite(v) & (v > 0)
    if ok.sum() < 3:
        return None
    o = np.argsort(y[ok])
    return y[ok][o], v[ok][o]


def generate_earlier(out, snaps, fires):
    """The buildings before the first atlases, where no outline survives (`procedural`).

    Evidence: the built-up extent snapshots (which blocks were built on, and when), the fire
    outlines, the census counts, and the lots themselves — the outlines of the 1852-57
    atlases stand in for the lots of the earlier town (lot lines in the old city mostly
    predate them). For an atlas structure that the snapshots say is a rebuild (its block was
    built on before it was), earlier buildings are generated on its outline backwards in
    time: each lasts 45-105 years, a fire ends what stood in its district, the first one
    starts between the snapshot that leaves the block out and the first that has it. The
    set is thinned so the number of buildings standing follows the population counts
    (persons per building: PPB). Traced and documented structures always win."""
    if not snaps:
        return out.iloc[0:0]
    lots = out[(out.map_year >= 1850) & (out.map_year <= 1860) & (out["rank"] == 1)]
    if not len(lots):
        return out.iloc[0:0]
    cen = lots.geometry.representative_point()
    xy = np.column_stack([cen.x.values, cen.y.values])
    lo, hi = extent_bounds(xy, lots.boro.values, snaps)
    first_of = {b: series[0][0] for b, series in snaps.items()}
    first_snap_arr = np.array([first_of.get(b, np.nan) for b in lots.boro.values])
    pts = shapely.points(xy)
    fire_at = []
    for when, poly in fires:
        shapely.prepare(poly)
        fire_at.append((when, shapely.contains(poly, pts)))
    ids = lots.fid_key.values
    s1 = lots.start_year.values
    rows = []
    for k in np.nonzero(np.isfinite(hi) & (s1 > hi + 5.0))[0]:
        hk, hr = h01(f"g{ids[k]}"), h01(f"r{ids[k]}")
        # first built on between the snapshot without the block and the first with it; before
        # the earliest snapshot, during the 35 years before it (and never before the settlement)
        a = lo[k] if np.isfinite(lo[k]) else max(first_snap_arr[k] - 35.0, SETTLED)
        first_built = max(a + (hi[k] - a) * h01(f"f{ids[k]}"), SETTLED)
        cur, gen_i = s1[k], 0
        while cur > first_built + 4.0 and gen_i < 6:
            g_end = cur - 0.5
            life = 45.0 + 60.0 * h01(f"l{ids[k]}{gen_i}")
            g_start = max(g_end - life, first_built)
            # a fire in between: this one was built after it, the one before burned
            for when, inside in fire_at:
                if inside[k] and g_start < when < g_end - 2.0:
                    g_start = when + 0.4 + 2.0 * hk
            rows.append((k, gen_i, g_start, g_end, hr))
            cur, gen_i = g_start, gen_i + 1
            for when, inside in fire_at:
                if inside[k] and abs(cur - when) < 3.0:
                    cur = when + 0.5   # the next one back ends in the fire
    if not rows:
        return out.iloc[0:0]
    r = pd.DataFrame(rows, columns=["k", "gen", "start", "end", "rank_h"])
    r["end"] = np.where(r.end - r.start < 1.0, r.start + 1.0, r.end)
    r["boro"] = lots.boro.values[r.k.values]
    # thin to the documented number of buildings
    keep = np.ones(len(r), bool)
    grid = np.arange(1630, 1851, 10.0)
    ppb = np.interp(grid, [p[0] for p in PPB], [p[1] for p in PPB])
    for boro, area in (("1", "manhattan"), ("3", "brooklyn")):
        sel = (r.boro == boro).values
        if not sel.any():
            continue
        ps = population_series(area)
        if ps is None:
            continue
        target = np.exp(np.interp(grid, ps[0], np.log(ps[1]), left=np.log(ps[1][0]))) / ppb * 1.15
        target = np.where(grid < ps[0][0], 0.0, target)
        ob = out[out.boro == boro]
        have = np.array([((ob.start_year.values <= t) & (ob.end_year.values > t)).sum() for t in grid])
        cand = np.array([((r.start.values[sel] <= t) & (r.end.values[sel] > t)).sum() for t in grid])
        frac = np.clip((target - have) / np.maximum(cand, 1), 0.0, 1.0)
        mid = 0.5 * (r.start.values[sel] + r.end.values[sel])
        keep[sel] = r.rank_h.values[sel] < np.interp(mid, grid, frac)
        log(f"predecessors: generated fill {area}: target buildings {dict(zip(grid[::4].astype(int).tolist(), target[::4].round(0).astype(int).tolist()))}, "
            f"traced standing {dict(zip(grid[::4].astype(int).tolist(), have[::4].tolist()))}, kept share {dict(zip(grid[::4].astype(int).tolist(), frac[::4].round(2).tolist()))}")
    r = r[keep]
    if not len(r):
        return out.iloc[0:0]
    k = r.k.values
    geom = shapely.affinity.scale  # earlier buildings were smaller than the atlas ones on the lot
    polys = [geom(lots.geometry.values[i], 0.88, 0.88, origin="centroid") for i in k]
    st_y = r.start.values
    hh = hashes(ids[k], "gh") 
    area = lots["area"].values[k] * 0.77
    st = np.where(st_y < 1700, np.where(area < 60, 1.5, 2.0 + (hh < 0.3)),
                  np.where(st_y < 1790, np.where(area < 60, 2.0, 2.5 + (hh < 0.4)), np.where(area < 50, 2.0, 3.0 + (hh < 0.35))))
    H = st * 3.1 + 1.0
    mat = np.where(st_y < 1700, M_DUTCH, np.where((st_y < 1790) & (hh < 0.5), M_EARLY, M_BRICK)).astype(np.uint8)
    roof = np.where(st_y < 1700, R_TILE, np.where(st_y < 1830, R_SHINGLE, R_FLAT)).astype(np.uint8)
    key = np.array([f"gen:{ids[i]}:{g}" for i, g in zip(k, r.gen.values)], dtype=object)
    return gpd.GeoDataFrame({"start_year": st_y, "end_year": r.end.values, "height_m": H, "year_confidence": "procedural",
                             "use": np.uint8(0), "raw_year": 0.0, "stories": st, "mat": mat, "roof": roof,
                             "fid_key": key, "boro": r.boro.values, "year_src": "generated", "name": None,
                             "area": area, "part_base": 0.0, "doitt_id": key, "rank": 0, "map_year": np.nan},
                            geometry=polys, crs=UTM)
