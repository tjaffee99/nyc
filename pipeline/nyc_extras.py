"""Researched extras that are not footprints of today's data and not tracings of whole maps:

  * early_sites()   data/tables/early_nyc.csv — Lenape settlements and camps, and the farms,
                    mills and houses of the colony outside the mapped town. One row is one
                    building or a cluster (`count` buildings within `spread_m` of a
                    documented site): the site, the kind of dwelling and the count are
                    researched; where each dwelling of a cluster stands is not known and is
                    placed by a hash (`procedural`). Dwellings are drawn at twice their
                    size, like the trees, or a wigwam four metres across would not be seen.
  * notable()       data/tables/notable_demolished*.csv — documented buildings that are gone,
                    with a real outline or a rectangle from cited dimensions.
  * demolished()    data/manual/demolished/demolished_footprints.geojson — outlines of
                    buildings removed in recent decades (city records).
  * atlas_layers()  data/manual/atlas/<area>_<year>.geojson — outlines traced from atlases.
  * piers()         data/manual/piers/piers.geojson — pier decks and sheds with lifespans,
                    as low platforms over the water (not subject to the ground rule).
  * site_labels()   data/manual/sites/sites.geojson — labels of military and industrial
                    sites over their years, appended to viewer/public/data/park-labels.json.

The first four return rows for nyc_predecessors.load_structures (same columns); piers()
returns finished building rows for nyc_buildings.
"""
from __future__ import annotations

import json
import math
import zlib

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
import shapely.affinity

from building_binary import M_BARK, M_EARLY, R_SHINGLE, R_WALL
from common import BORO_COUNTY, INTERIM, MANUAL, NYC_CRS, RAW, TABLES, VIEWER_DATA, log

UTM = NYC_CRS
BORO_OF_COUNTY = {"061": "1", "005": "2", "047": "3", "081": "4", "085": "5"}
VILLAGE_SCALE = 2.0   # early dwellings are drawn at twice their size (as the trees are)
_boro_polys = None


def h01(key) -> float:
    return (zlib.crc32(str(key).encode()) % 100003) / 100003.0


def boro_of(points_4326):
    """Borough code ("1".."5", "" outside the city) of shapely points (EPSG:4326)."""
    global _boro_polys
    if _boro_polys is None:
        co = gpd.read_file(f"zip://{RAW / 'tiger' / 'tl_2024_us_county.zip'}")
        co = co[(co.STATEFP == "36") & co.COUNTYFP.isin(list(BORO_COUNTY))].to_crs(4326)
        _boro_polys = [(BORO_OF_COUNTY[r.COUNTYFP], r.geometry) for r in co.itertuples()]
        for _, poly in _boro_polys:
            shapely.prepare(poly)
    pts = np.asarray(points_4326, dtype=object)
    out = np.full(len(pts), "", dtype=object)
    for code, poly in _boro_polys:
        out[shapely.contains(poly, pts) & (out == "")] = code
    return out


def _rect(w, d, rot_deg):
    r = shapely.box(-w / 2, -d / 2, w / 2, d / 2)
    return shapely.affinity.rotate(r, -rot_deg, origin=(0, 0))   # bearing: clockwise from north


def _round(diam, n=8):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False) + np.pi / n
    return shapely.Polygon(np.column_stack([np.cos(a), np.sin(a)]) * diam / 2)


def _to_utm(lon, lat):
    p = gpd.GeoSeries(gpd.points_from_xy(lon, lat), crs=4326).to_crs(UTM)
    return p.x.values, p.y.values


def _num(v, default=np.nan):
    try:
        f = float(v)
        return f if np.isfinite(f) else default
    except (TypeError, ValueError):
        return default


def _wxd(text, default=(8.0, 6.0)):
    try:
        w, d = str(text).lower().replace("×", "x").split("x")[:2]
        return float(w), float(d)
    except (ValueError, AttributeError):
        return default


_wet = None


def natural_wet(x_utm, y_utm):
    """True where the 1609 layer has water, flats, marsh, wetland or a pond at the point (the
    detail grid's natural cover, written by terrain_tiles.py; False where it is not known)."""
    global _wet
    if _wet is None:
        try:
            from terrain_grid import grid_def
            from terrain_tiles import COVER_NAMES
            gd = grid_def("detail")
            cov = np.load(INTERIM / "grid_detail_covers.npy", mmap_mode="r")[0]
            wet_codes = [COVER_NAMES.index(c) for c in ("deep_water", "shallow_water", "tidal_flat", "tidal_marsh", "wetland",
                                                        "reservoir", "salt_pond")]
            _wet = (gd, np.isin(cov, wet_codes)) if cov.shape == (gd["rows"], gd["cols"]) else (None, None)
        except Exception:  # noqa: BLE001
            _wet = (None, None)
    gd, wet = _wet
    x_utm = np.atleast_1d(np.asarray(x_utm, float))
    out = np.zeros(len(x_utm), bool)
    if gd is None:
        return out
    ll = gpd.GeoSeries(gpd.points_from_xy(x_utm, np.atleast_1d(np.asarray(y_utm, float))), crs=UTM).to_crs(4326)
    X = np.radians(ll.x.values) * 6378137.0
    Y = 6378137.0 * np.log(np.tan(np.pi / 4 + np.radians(ll.y.values) / 2))
    c = (X - gd["X0"]) / gd["res"]
    r = (gd["Y0"] - Y) / gd["res"]
    ok = (c >= 0) & (r >= 0) & (c < gd["cols"] - 1) & (r < gd["rows"] - 1)
    c0, r0 = np.floor(c[ok]).astype(int), np.floor(r[ok]).astype(int)
    out[ok] = wet[r0, c0] | wet[r0, c0 + 1] | wet[r0 + 1, c0] | wet[r0 + 1, c0 + 1]
    return out


def early_sites():
    """Rows (in UTM) for the Lenape settlements and the colony's outlying buildings."""
    p = TABLES / "early_nyc.csv"
    rows = []
    if not p.exists():
        return rows
    t = pd.read_csv(p)
    # (a row without an end is a house that still stands: it dates today's footprint — early_standing)
    t = t[pd.to_numeric(t.end_year, errors="coerce") < 9000].reset_index(drop=True)
    X, Y = _to_utm(t.lon.values, t.lat.values)
    skipped = 0
    for k, r in enumerate(t.itertuples()):
        w, d = _wxd(getattr(r, "footprint_m", ""))
        n = int(_num(getattr(r, "count", 1), 1) or 1)
        spread = _num(getattr(r, "spread_m", 0), 0.0)
        rot = _num(getattr(r, "rotation_deg", 0), 0.0)
        mat = str(getattr(r, "material", "")).strip().lower()
        kind = str(getattr(r, "kind", "")).strip().lower()
        lenape = kind.startswith("lenape") or mat == "bark"
        h = _num(getattr(r, "height_m", np.nan), 3.0 if lenape else 5.0)
        scale = VILLAGE_SCALE if lenape else 1.0
        # the Dutch and English villages were single streets (Midwout, Nieuw Haarlem, Vlissingen):
        # their houses are set along the row's bearing (the nearest road of today: an estimate)
        street = kind == "house" and n >= 6 and spread >= 150
        placed = []
        for i in range(max(n, 1)):
            if i == 0 and n == 1:
                dx = dy = 0.0
            else:
                # a hashed spot inside the site; a few tries to keep the dwellings apart
                # (and off the water and marsh of the time: a dwelling that finds no dry spot is left out)
                found = False
                for t_ in range(24):
                    if street:
                        # a street village: houses on both sides of one street (bearing rot)
                        along = (2 * h01(f"{r.id}a{i}_{t_}") - 1) * spread
                        across = (14 + 16 * h01(f"{r.id}r{i}_{t_}")) * (1 if h01(f"{r.id}s{i}") < 0.5 else -1)
                        br = math.radians(rot)
                        dx = along * math.sin(br) + across * math.cos(br)
                        dy = along * math.cos(br) - across * math.sin(br)
                    else:
                        ang = 2 * math.pi * h01(f"{r.id}a{i}_{t_}")
                        rad = max(spread, 3 * max(w, d)) * math.sqrt(h01(f"{r.id}r{i}_{t_}"))
                        dx, dy = rad * math.sin(ang), rad * math.cos(ang)
                    if all(math.hypot(dx - px, dy - py) > 1.6 * scale * max(w, d) for px, py in placed) \
                            and not natural_wet(X[k] + dx, Y[k] + dy)[0]:
                        found = True
                        break
                if not found:
                    skipped += 1
                    continue
            placed.append((dx, dy))
            if lenape and abs(w - d) < 1.5 and max(w, d) <= 8:
                shape = _round(max(w, d) * scale)                      # a wigwam
            else:
                shape = _rect(w * scale, d * scale, rot if (n == 1 or street) else rot + 180 * h01(f"{r.id}o{i}"))
            poly = shapely.affinity.translate(shape, X[k] + dx, Y[k] + dy)
            rows.append({"id": f"early:{r.id}:{i}" if n > 1 else f"early:{r.id}", "map_year": int(_num(r.end_year, 1700)) - 1,
                         "boro": "", "colors": "", "name": r.name if n == 1 else f"{r.name} (one of {n} dwellings; position generated)",
                         "start_doc": _num(r.start_year), "end_doc": _num(r.end_year), "h_doc": h * (1.5 if scale > 1 else 1.0),
                         "cls": "documented", "conf_doc": "procedural" if n > 1 else "estimated",
                         "mat_doc": "bark" if lenape else mat, "geometry": poly})
    log(f"extras: {len(rows)} early dwellings from {len(t)} researched rows (early_nyc.csv); "
        f"{skipped} of a cluster found no dry ground and were left out")
    return rows


def early_standing():
    """The rows of early_nyc.csv that still stand (no end year), in the format of
    known_building_dates.csv: they date the standing footprint their point lies in."""
    p = TABLES / "early_nyc.csv"
    if not p.exists():
        return None
    t = pd.read_csv(p)
    t = t[pd.to_numeric(t.end_year, errors="coerce") >= 9000]
    conf = t.confidence.astype(str).str.lower() if "confidence" in t else pd.Series("", index=t.index)
    return pd.DataFrame({"id": "early:" + t.id.astype(str), "name": t.name.values, "lat": t.lat.values, "lon": t.lon.values,
                         "bin": np.nan, "start_year": t.start_year.values, "end_year": np.nan, "source_url": t.source_url.values,
                         "note": np.where(conf.values == "high", "", "estimated (early_nyc.csv: confidence " + conf.values + ")")})


def notable():
    """Rows (UTM) from data/tables/notable_demolished*.csv."""
    rows = []
    for p in sorted(TABLES.glob("notable_demolished*.csv")):
        t = pd.read_csv(p)
        X, Y = _to_utm(t.lon.values, t.lat.values)
        n0 = len(rows)
        for k, r in enumerate(t.itertuples()):
            outline = str(getattr(r, "outline", "") or "").strip()
            poly = None
            if outline and outline.lower() != "nan":
                pts = [tuple(float(v) for v in q.split()) for q in outline.split(";") if q.strip()]
                if len(pts) >= 3:
                    poly = gpd.GeoSeries([shapely.Polygon(pts)], crs=4326).to_crs(UTM).iloc[0]
            if poly is None:
                fp = getattr(r, "footprint_m", "")
                if not isinstance(fp, str) or "x" not in fp.lower().replace("×", "x"):
                    continue
                w, d = _wxd(fp)
                poly = shapely.affinity.translate(_rect(w, d, _num(getattr(r, "rotation_deg", 0), 0.0)), X[k], Y[k])
            h = _num(getattr(r, "height_m", np.nan))
            st = _num(getattr(r, "storeys", np.nan))
            rows.append({"id": f"notable:{r.id}", "map_year": int(_num(r.end_year, 1900)) - 1, "boro": "", "colors": "",
                         "name": r.name, "start_doc": _num(r.start_year), "end_doc": _num(r.end_year),
                         "h_doc": h if np.isfinite(h) else (st * 3.4 + 1.0 if np.isfinite(st) else np.nan),
                         "cls": "documented", "conf_doc": None, "mat_doc": str(getattr(r, "material", "") or "").lower(),
                         "geometry": poly})
        log(f"extras: {len(rows) - n0} documented lost buildings from {p.name}")
    return rows


# outlines of the city's retired-footprint layer that are not buildings that stood: the World
# Trade Center site's construction phases (data/research/building_records.md)
DEMO_SKIP = {"oti-h79828", "oti-h1108000", "oti-h996388", "oti-h1078803", "oti-h1054572", "oti-h1037035"}
# Shea Stadium and the old Yankee Stadium: the record says 2004, they came down in 2009-10
# (the outline's retirement date is used)
DEMO_RETIRED = {"oti-h560134", "oti-h72245"}


def demolished():
    """Rows (UTM) from the city's record of removed buildings (building_records.py: the
    footprints the city retired since the 1990s, each with the year it was removed).
    start_doc: a recorded construction year; start_est: the assessor's rounded year (an
    estimate); neither: dated from the buildings around (nyc_predecessors)."""
    p = MANUAL / "demolished" / "demolished_footprints.geojson"
    rows = []
    if not p.exists():
        return rows
    g = gpd.read_file(p).to_crs(UTM)
    sq = g.start_quality.fillna("").astype(str).str.lower().values if "start_quality" in g else np.full(len(g), "")
    sy = pd.to_numeric(g.start_year, errors="coerce").values if "start_year" in g else np.full(len(g), np.nan)
    ey = pd.to_numeric(g.end_year, errors="coerce").values
    hm = pd.to_numeric(g.height_m, errors="coerce").values if "height_m" in g else np.full(len(g), np.nan)
    st = pd.to_numeric(g.storeys, errors="coerce").values if "storeys" in g else np.full(len(g), np.nan)
    names = g["name"].values if "name" in g else np.full(len(g), None, dtype=object)
    eq = g.end_quality.fillna("").astype(str).str.lower().values if "end_quality" in g else np.full(len(g), "recorded")
    retired = pd.to_numeric(g.retired, errors="coerce").values if "retired" in g else np.full(len(g), np.nan)
    ids = g.id.astype(str).values
    for k, geom in enumerate(g.geometry.values):
        if geom is None or geom.is_empty or not np.isfinite(ey[k]) or ids[k] in DEMO_SKIP:
            continue
        if ids[k] in DEMO_RETIRED and np.isfinite(retired[k]):
            ey[k] = retired[k]
        if geom.geom_type != "Polygon":
            geom = max(getattr(geom, "geoms", [geom]), key=lambda q: q.area)
        # the measured height unless it is impossible for the storeys (measured in mid-demolition)
        ok_h = np.isfinite(hm[k]) and hm[k] > 2 and not (np.isfinite(st[k]) and st[k] > 0 and hm[k] / st[k] < 2.2)
        h = hm[k] if ok_h else (st[k] * 3.3 + 1.0 if np.isfinite(st[k]) and st[k] > 0 else np.nan)
        rows.append({"id": f"demo:{g.id.values[k]}", "map_year": int(ey[k]) - 1, "boro": "", "colors": "",
                     "name": names[k] if isinstance(names[k], str) else None,
                     "start_doc": sy[k] if sq[k] == "recorded" else np.nan, "start_est": sy[k] if sq[k] == "estimated" else np.nan,
                     "end_doc": ey[k], "h_doc": h, "cls": "documented",
                     "conf_doc": None if (sq[k] == "recorded" and eq[k] == "recorded") else "estimated", "mat_doc": "", "geometry": geom})
    log(f"extras: {len(rows)} removed buildings from the city's records")
    return rows


def farmsteads():
    """Rows (UTM) for the building marks of the 1889 / 1897 USGS sheets (topo_farmsteads.py ->
    data/manual/farmsteads/farmsteads.geojson) that are not a building standing today: the
    position is the map's (to about 40 m), the outline is generated (`procedural`): a house
    9 x 7 m, a large building 20 x 12 m. A mark missing from a later sheet ended in between;
    one that appears between the two surveys was built in between. Left out: marks the tool
    rates low, marks in the sheets' built-up tint, marks on marsh, and marks whose standing
    building is recorded as old as the map (that building is the one on the map)."""
    p = MANUAL / "farmsteads" / "farmsteads.geojson"
    rows = []
    if not p.exists():
        return rows
    g = gpd.read_file(p).to_crs(UTM)
    basis = g.standing_basis.fillna("").astype(str).values if "standing_basis" in g else np.full(len(g), "")
    keep = (g.confidence.astype(str).values != "low") & ~g.builtup.fillna(False).astype(bool).values \
        & ~np.isin(g.ground.fillna("").astype(str).values, ["tidal_flat", "tidal_marsh", "wetland"]) \
        & ~np.isin(basis, ["recorded", "by_then"])
    fy = pd.to_numeric(g.first_year, errors="coerce").values
    ly = pd.to_numeric(g.last_year, errors="coerce").values
    gb = pd.to_numeric(g.gone_by, errors="coerce").values
    ns = pd.to_numeric(g.new_since, errors="coerce").values
    for k in np.nonzero(keep & np.isfinite(fy))[0]:
        pt = g.geometry.values[k]
        big = str(g.kind.values[k]) == "large"
        w, d = (20.0, 12.0) if big else (9.0, 7.0)
        h1, h2 = h01(f"fa{g.id.values[k]}"), h01(f"fb{g.id.values[k]}")
        poly = shapely.affinity.translate(_rect(w, d, 180.0 * h1), pt.x, pt.y)
        rows.append({"id": f"farm:{g.id.values[k]}", "map_year": int(fy[k]), "boro": "", "colors": "yellow", "name": None,
                     "start_doc": ns[k] + 0.5 + (fy[k] - ns[k] - 1.0) * h2 if np.isfinite(ns[k]) and fy[k] > ns[k] else np.nan,
                     "end_doc": ly[k] + 1.0 + (gb[k] - ly[k] - 1.5) * (0.15 + 0.8 * h2) if np.isfinite(gb[k]) and gb[k] > ly[k] + 2 else np.nan,
                     "h_doc": 8.0 if big else np.nan, "cls": "traced", "conf_doc": "procedural", "mat_doc": "frame",
                     "geometry": poly})
    log(f"extras: {len(rows)} building marks of the 1889 / 1897 USGS sheets drawn as farmsteads ({len(g) - len(rows)} left out)")
    return rows


def atlas_layers():
    """Rows (UTM) from data/manual/atlas/<area>_<year>.geojson (not the *_coverage files)."""
    d = MANUAL / "atlas"
    rows = []
    colour = {"brick": "pink", "frame": "yellow", "stone": "blue"}
    for p in sorted(d.glob("*_[0-9][0-9][0-9][0-9].geojson")) if d.exists() else []:
        g = gpd.read_file(p).to_crs(UTM)
        year = int(p.stem.rsplit("_", 1)[1])
        n0 = len(rows)
        for i, r in enumerate(g.itertuples()):
            geom = r.geometry
            if geom is None or geom.is_empty:
                continue
            geom = max(getattr(geom, "geoms", [geom]), key=lambda q: q.area)
            st = _num(getattr(r, "storeys", np.nan))
            rows.append({"id": f"atlas:{p.stem}:{i}", "map_year": int(_num(getattr(r, "map_year", year), year)), "boro": "",
                         "colors": colour.get(str(getattr(r, "material", "") or "").lower(), ""), "name": None,
                         "start_doc": np.nan, "end_doc": np.nan, "h_doc": st * 3.3 + 1.0 if np.isfinite(st) and st > 0 else np.nan,
                         "cls": "traced", "conf_doc": None, "mat_doc": "", "geometry": geom})
        log(f"extras: {len(rows) - n0} outlines from the atlas layer {p.name}")
    return rows


def piers():
    """Finished building rows (EPSG:4326) for pier decks and their sheds: low platforms over
    the water, standing over their years. Not land-checked (they are over water by nature)."""
    p = MANUAL / "piers" / "piers.geojson"
    if not p.exists():
        return None
    g = gpd.read_file(p).to_crs(UTM)
    out = []
    for r in g.itertuples():
        geom = r.geometry
        if geom is None or geom.is_empty:
            continue
        s, e = _num(getattr(r, "start_year", np.nan)), _num(getattr(r, "end_year", 9999), 9999.0)
        if not np.isfinite(s) or e <= s:
            continue
        deck = _num(getattr(r, "deck_m", 2.5), 2.5)
        rec = str(getattr(r, "start_quality", "")).lower() == "recorded"
        name = getattr(r, "name", None)
        for part in getattr(geom, "geoms", [geom]):
            if part.geom_type != "Polygon" or part.area < 40:
                continue
            base = {"end_year": e, "year_confidence": "exact" if rec else "estimated", "use": np.uint8(5), "raw_year": 0.0,
                    "stories": 1.0, "boro": "", "year_src": "pier", "name": name if isinstance(name, str) else None}
            out.append(dict(base, start_year=s, height=deck + 1.0, base=-1.0, mat=M_EARLY, roof=R_WALL,
                            fid_key=f"pier:{r.id}", geometry=part))
            shed = str(getattr(r, "shed", "none") or "none").lower()
            if shed in ("shed", "headhouse"):
                inner = part.buffer(-2.5)
                inner = max(getattr(inner, "geoms", [inner]), key=lambda q: q.area) if not inner.is_empty else None
                if inner is not None and inner.geom_type == "Polygon" and inner.area > 60:
                    ss = _num(getattr(r, "shed_start", np.nan), s)
                    se = _num(getattr(r, "shed_end", np.nan), e)
                    hm = _num(getattr(r, "shed_m", 10.0), 10.0)
                    if se > ss:
                        out.append(dict(base, start_year=max(ss, s), end_year=min(se, e), height=max(hm - deck, 3.0), base=deck,
                                        mat=M_EARLY, roof=R_SHINGLE, fid_key=f"pier:{r.id}:shed", geometry=inner))
    if not out:
        return None
    gdf = gpd.GeoDataFrame(out, geometry="geometry", crs=UTM).to_crs(4326)
    gdf["boro"] = boro_of(gdf.geometry.representative_point().values)
    # piers inside the map (Manhattan's go into the core file with boro "1"; the New Jersey
    # shore's, boro "", into the tiles)
    from extent import in_extent
    gdf = gdf[in_extent(gdf.geometry.representative_point().values)]
    gdf["area"] = gdf.geometry.to_crs(UTM).area.values
    gdf["height_m"] = gdf.height.values
    gdf["part_base"] = 0.0
    gdf["doitt_id"] = gdf.fid_key.values
    log(f"extras: {len(gdf)} pier decks and sheds ({int((gdf.end_year < 9000).sum())} gone)")
    return gdf


def _norm(name):
    return "".join(ch for ch in str(name).lower() if ch.isalnum())


def site_labels():
    """Append the labels of military / industrial sites (tier `site`) to park-labels.json."""
    p = MANUAL / "sites" / "sites.geojson"
    out = VIEWER_DATA / "park-labels.json"
    if not p.exists() or not out.exists():
        return
    g = gpd.read_file(p)
    labels = [x for x in json.loads(out.read_text()) if x.get("tier") != "site"]
    # names that already have a label near by (a park, an airfield, a place of places.csv)
    have = [(_norm(x["name"]), x["lon"], x["lat"]) for x in labels]
    for f in ("places.csv", "places_counties.csv"):
        if (TABLES / f).exists():
            pl = pd.read_csv(TABLES / f)
            have += [(_norm(nm), lo, la) for nm, lo, la in zip(pl.name, pl.lon, pl.lat)]
    n = 0
    area = g.to_crs(UTM).geometry.area.values / 1e4
    for r, ha in zip(g.itertuples(), area):
        if r.geometry is None or r.geometry.is_empty or str(getattr(r, "label", True)).lower() in ("false", "0", "no"):
            continue
        s = _num(getattr(r, "start_year", np.nan))
        if not np.isfinite(s):
            continue
        c = r.geometry.representative_point()
        key = _norm(r.name)
        if any((key == k or key in k or k in key) and abs(lo - c.x) < 0.012 and abs(la - c.y) < 0.009 for k, lo, la in have if k):
            continue
        e = _num(getattr(r, "end_year", 9999), 9999.0)
        row = {"name": r.name, "lon": round(c.x, 5), "lat": round(c.y, 5), "start": s, "ha": round(float(ha), 1), "tier": "site"}
        if e < 9000:
            row["end"] = e
        labels.append(row)
        n += 1
    out.write_text(json.dumps(labels, separators=(",", ":")))
    log(f"extras: {n} site labels -> park-labels.json")


if __name__ == "__main__":
    site_labels()
