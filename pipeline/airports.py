"""Stage: airports — runways, taxiways, aprons and heliport decks (Overture
base/infrastructure, OpenStreetMap) as dated ground features, and airfield outlines for
the terrain (airfield grass instead of city ground, from the opening year).

Dates: data/tables/airports.csv (researched opening / closing years per airport, `name` =
the OpenStreetMap name, source per row). Single runways / taxiways built later than their
airport take their own years from data/manual/airports/pavement_dates.csv (by Overture id;
README there). Airfields gone from today's map (Floyd Bennett Field, Flushing Airport ...)
come from data/manual/airports/extra_pavement.geojson + extra_outlines.geojson, each piece
with its own start_year / end_year. Nothing is laid before its ground exists (Jamaica Bay
and Flushing Bay fill under JFK and LaGuardia): each feature waits for the terrain's land
year (median over the piece). Runways and taxiways are OSM centrelines: buffered to the
usual width (45 m runways / 23 m taxiways at the international airports, 23 / 15 m
elsewhere, taxilanes 10 m), or to the airport's cited runway width where airports.csv
gives one (optional column `runway_width_m`; taxiways 23 m where it is 45 m or more).

The map box is common.REGION_BBOX: the airfields of the counties around the city come from
the same extract and the same tables (Newark, Teterboro, Westchester County ...); an airfield
is drawn if it lies inside the map outline (extent.in_extent) and airports.csv dates it.
Made land: the pieces wait for their ground as in the city, but a researched opening year is
never moved — data/interim/airports/ground_conflicts.csv lists each airfield with the latest
land year under its outline (ground_rule.ground_year) and the pieces that wait.

Outputs: viewer/public/data/airports.bin.gz (BAYT: start_indices, positions f32[3] offsets
from ORIGIN with z = ground + 0.35, kind u8 (0 runway, 1 taxiway, 2 apron), years f32[2]),
viewer/public/data/airport-lines.bin.gz (runway centre lines with their width, for far zooms),
data/interim/airports.parquet (airfield outlines: name, class, opened, closed),
data/interim/airport_pavement.parquet (every dated pavement polygon: start, end, kind).
"""
from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

from common import INTERIM, MANUAL, NYC_CRS, OVERTURE_RELEASE, RAW, TABLES, VIEWER_DATA, log
from export_columnar import write_columnar
from extent import in_extent

UTM = NYC_CRS
ORIGIN = (-73.97, 40.75)   # as ground_detail.py; the file header carries it
AIRPORT_CLASSES = ["airport", "international_airport", "military_airport", "municipal_airport", "private_airport",
                   "heliport"]
BIG = {"international_airport", "military_airport"}
KIND = {"runway": 0, "stopway": 0, "taxiway": 1, "taxilane": 1, "apron": 2, "helipad": 2}
EXTRA = MANUAL / "airports"


def point_airport_outlines(g, reach=1500.0, margin=40.0):
    """Outlines for airports OSM maps only as a point: the convex hull of the runways /
    taxiways / aprons around the point that belong to it (nearer to it than to any other
    airport, within `reach` m), plus a margin. Points within 300 m of a polygon outline are
    duplicates of it and skipped; a point with no pavement around it (the seaplane bases)
    gets no outline (nothing to draw)."""
    none = gpd.GeoDataFrame(columns=["name", "class", "geometry"], geometry="geometry", crs=4326)
    ports = g[g["class"].isin(AIRPORT_CLASSES + ["seaplane_airport"])].to_crs(UTM)
    poly = ports[ports.geom_type.isin(["Polygon", "MultiPolygon"])]
    pts = ports[ports.geom_type == "Point"]
    if not poly.empty:
        pts = pts[pts.geometry.distance(shapely.union_all(poly.geometry.values)) > 300]
    feats = g[g["class"].isin(["runway", "stopway", "taxiway", "taxilane", "apron"])].to_crs(UTM)
    if pts.empty or feats.empty:
        return none
    # distance of every feature to every airport (polygon outlines first, then the points)
    anchors = list(poly.geometry.values) + list(pts.geometry.values)
    d = np.stack([feats.geometry.distance(a).values for a in anchors])
    nearest = d.argmin(0)
    out = []
    for i, (_, p) in enumerate(pts.iterrows(), start=len(poly)):
        mine = (nearest == i) & (d[i] <= reach)
        if not mine.any():
            continue
        parts = [geom.buffer(12) for geom in feats.geometry.values[mine]] + [p.geometry.buffer(30)]
        hull = shapely.union_all(parts).convex_hull.buffer(margin)
        out.append({"name": p["name"], "class": "airport", "geometry": hull})
        log(f"airports: outline for point-only {p['name']} from {int(mine.sum())} runway / taxiway / apron features "
            f"({hull.area / 1e4:.1f} ha)")
    return gpd.GeoDataFrame(out, geometry="geometry", crs=UTM).to_crs(4326) if out else none


def _in_city(points):
    from ground_detail import inside_city
    return inside_city(points)


def land_year(lon, lat):
    """Year the ground at each point became dry land (terrain land-year grids), NaN if always land."""
    from terrain_grid import grid_def
    lon = np.asarray(lon, float)
    lat = np.asarray(lat, float)
    out = np.full(len(lon), np.nan)
    for name in ("detail", "region"):
        p = INTERIM / f"grid_{name}_landyear.npy"
        if not p.exists():
            continue
        g = grid_def(name)
        ly = np.load(p)
        X = np.radians(lon) * 6378137.0
        Y = 6378137.0 * np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))
        c = np.rint((X - g["X0"]) / g["res"]).astype(int)
        r = np.rint((g["Y0"] - Y) / g["res"]).astype(int)
        ok = np.isnan(out) & (c >= 0) & (r >= 0) & (c < g["cols"]) & (r < g["rows"])
        out[ok] = ly[r[ok], c[ok]]
    return out


def dated_pavement(f):
    """Pavement dated feature by feature (data/manual/airports/pavement_dates.csv, by Overture
    id): a whole feature takes its own years, a runway can be cut into construction phases
    (`axis_interval`: the part between two points on its axis), taxiways / aprons crossing a
    phase boundary are clipped by dated zones (pavement_zones.geojson); runways gone from
    today's airports are added from vanished_pavement.geojson."""
    pp, zp, vp = EXTRA / "pavement_dates.csv", EXTRA / "pavement_zones.geojson", EXTRA / "vanished_pavement.geojson"
    if not pp.exists():
        return f
    pav = pd.read_csv(pp)
    zones = {}
    if zp.exists():
        z = gpd.read_file(zp).to_crs(UTM)
        zones = dict(zip(z["zone"].astype(str), z.geometry.values))
    to_utm = lambda lon, lat: gpd.GeoSeries(gpd.points_from_xy([lon], [lat]), crs=4326).to_crs(UTM).iloc[0]  # noqa: E731

    def band(r, half=250.0):
        a, b = to_utm(r.part_lon0, r.part_lat0), to_utm(r.part_lon1, r.part_lat1)
        d = np.array([b.x - a.x, b.y - a.y]); L = np.hypot(*d)
        if L < 1:
            return None
        u = d / L; n = np.array([-u[1], u[0]]) * half
        P0, P1 = np.array([a.x, a.y]), np.array([b.x, b.y])
        return shapely.Polygon([P0 + n, P1 + n, P1 - n, P0 - n])

    by_id = {k: g_ for k, g_ in pav.groupby("overture_id")}
    out = []
    n_dated = 0
    # (records, not itertuples: "class" is a keyword and would be renamed)
    for d in f.to_dict("records"):
        rows = by_id.get(d.get("id"))
        if rows is None:
            out.append(d)
            continue
        n_dated += 1
        geom = d["geometry"]
        used = []
        for q in rows.itertuples():
            if q.part == "whole":
                piece = geom
            elif q.part == "axis_interval":
                bd = band(q)
                piece = geom.intersection(bd) if bd is not None else None
            else:
                zg = zones.get(str(q.clip_zone))
                piece = geom.intersection(zg) if zg is not None else None
            if piece is None or piece.is_empty or piece.area < 20:
                continue
            for u_ in used:
                piece = piece.difference(u_)
            if piece.is_empty or piece.area < 20:
                continue
            used.append(piece)
            out.append(dict(d, geometry=piece, opened=float(q.start_year),
                            closed=float(q.end_year) if pd.notna(q.end_year) else 9999.0))
        rest = geom.difference(shapely.union_all(used)) if used else geom
        if not rest.is_empty and rest.area > 200:
            first = float(rows.start_year.min())
            out.append(dict(d, geometry=rest, opened=first))
    f2 = gpd.GeoDataFrame(out, geometry="geometry", crs=UTM)
    if vp.exists():
        v = gpd.read_file(vp).to_crs(UTM)
        vg = [gm.buffer(float(w) / 2, cap_style="flat") if gm.geom_type == "LineString" else gm
              for gm, w in zip(v.geometry, pd.to_numeric(v.get("width_m", 45), errors="coerce").fillna(45))]
        extra = gpd.GeoDataFrame({"class": v["kind"].astype(str).replace({"": "runway"}), "name": v["name"],
                                  "opened": pd.to_numeric(v.start_year, errors="coerce"),
                                  "closed": pd.to_numeric(v.end_year, errors="coerce").fillna(9999.0),
                                  "aclass": "aerodrome"}, geometry=vg, crs=UTM)
        f2 = gpd.GeoDataFrame(pd.concat([f2, extra], ignore_index=True), geometry="geometry", crs=UTM)
    log(f"airports: {n_dated} pavement features dated on their own, + {len(f2) - len(f)} pieces / removed runways")
    return f2


def main():
    from nyc_buildings import Ground
    d = pd.read_parquet(RAW / "overture" / OVERTURE_RELEASE / "region_airports.parquet")
    g = gpd.GeoDataFrame(d, geometry=gpd.GeoSeries.from_wkb(d.geometry), crs=4326)
    g = g[in_extent(g.geometry.representative_point())]
    # airports OSM has only as a point (no aerodrome outline): outline from their pavement
    po = point_airport_outlines(g)
    if len(po):
        g = gpd.GeoDataFrame(pd.concat([g, po], ignore_index=True), geometry="geometry", crs=4326)
    # a heliport's deck is its pavement: the outline is also drawn as an apron
    hp = g[(g["class"] == "heliport") & (g.geom_type == "Polygon")].copy()
    hp["class"] = "apron"
    hp["id"] = None
    g = gpd.GeoDataFrame(pd.concat([g, hp], ignore_index=True), geometry="geometry", crs=4326)
    # airfields gone from today's map: researched pavement polygons (already at their real
    # width; each piece keeps its own start_year / end_year) + the airfield outline
    extra_f, extra_o = EXTRA / "extra_pavement.geojson", EXTRA / "extra_outlines.geojson"
    add = []
    if extra_f.exists():
        ef = gpd.read_file(extra_f).to_crs(4326).rename(columns={"airport": "name"})
        ef["class"] = ef["kind"]
        for c in ("start_year", "end_year"):
            ef["piece_" + c] = pd.to_numeric(ef[c], errors="coerce") if c in ef else np.nan
        add.append(ef[["name", "class", "piece_start_year", "piece_end_year", "geometry"]])
    if extra_o.exists():
        add.append(gpd.read_file(extra_o).to_crs(4326)[["name", "class", "geometry"]])
    if add:
        g = gpd.GeoDataFrame(pd.concat([g] + add, ignore_index=True), geometry="geometry", crs=4326)
        log(f"airports: + {sum(len(a) for a in add)} researched pavement polygons / outlines of vanished airfields")
    ports = g[g["class"].isin(AIRPORT_CLASSES) & (g.geom_type == "Polygon")].copy()
    t = pd.read_csv(TABLES / "airports.csv")
    if (TABLES / "airports_outer.csv").exists():              # the outer counties' airfields (same columns)
        t = pd.concat([t, pd.read_csv(TABLES / "airports_outer.csv")], ignore_index=True)
    if "runway_width_m" not in t:
        t["runway_width_m"] = np.nan
    ports = ports.merge(t[["name", "opened", "closed", "runway_width_m"]].drop_duplicates("name"), on="name", how="left")
    ports["opened"] = pd.to_numeric(ports.opened, errors="coerce")
    ports["closed"] = pd.to_numeric(ports.closed, errors="coerce").fillna(9999.0)
    undated = sorted(ports[ports.opened.isna()].name.fillna("(unnamed)").tolist())
    log(f"airports: {len(ports)} airfield / heliport outlines, {ports.opened.notna().sum()} dated"
        + (f" (undated, left out: {undated})" if undated else ""))
    ports = ports[ports.opened.notna()]
    pu = ports.to_crs(UTM)
    INTERIM.mkdir(parents=True, exist_ok=True)
    pu[["name", "class", "opened", "closed", "geometry"]].to_crs(4326).to_parquet(INTERIM / "airports.parquet")

    f = g[g["class"].isin(list(KIND)) & (g.geom_type != "Point")].copy().to_crs(UTM)
    # features belong to the airport they touch, else the nearest one within 1.5 km (aprons
    # just outside a drawn boundary); helipads only on an airfield / heliport itself (the
    # rest are hospital and office roofs)
    # (ties — a heliport inside a larger airfield — go to the smaller outline)
    pu = pu.assign(parea=pu.geometry.area.values)
    j = gpd.sjoin_nearest(f, pu[["name", "class", "opened", "closed", "parea", "runway_width_m", "geometry"]]
                          .rename(columns={"class": "aclass", "name": "aname", "runway_width_m": "rw"}),
                          how="left", max_distance=1500, distance_col="dist")
    j = j.sort_values(["dist", "parea"])
    j = j[~j.index.duplicated()].reindex(f.index)
    # align by row label (sjoin_nearest returns its rows in its own order)
    f["aclass"] = j.aclass.reindex(f.index).values
    f["aname"] = j.aname.reindex(f.index).values
    f["rw"] = pd.to_numeric(j.rw.reindex(f.index), errors="coerce").values
    f["opened"] = j.opened.reindex(f.index).values
    # pavement on today's map is there today, whatever became of the airfield (Floyd Bennett
    # Field's runways are park roads now): only researched pieces of vanished fields end
    f["closed"] = 9999.0
    f["aclosed"] = j.closed.values
    far_pad = f["class"].eq("helipad").values & ~(j.dist.reindex(f.index).values <= 30)
    f = f[~far_pad]
    if "piece_start_year" in f:
        # researched pieces of vanished airfields carry their own years
        f["opened"] = f.piece_start_year.where(f.piece_start_year.notna() & f.opened.notna(), f.opened)
        is_piece = f.piece_start_year.notna().values
        f["closed"] = np.where(is_piece, f.piece_end_year.fillna(f.aclosed).fillna(9999.0), f.closed)
    f = f[f.opened.notna()]
    big = f.aclass.isin(list(BIG)).values
    rw = f.rw.values.astype(float)   # the airport's cited runway width, where airports.csv has one
    wide = np.where(np.isfinite(rw), rw >= 45, big)
    width = np.select([f["class"].isin(["runway", "stopway"]).values, f["class"].eq("taxiway").values,
                       f["class"].eq("taxilane").values],
                      [np.where(np.isfinite(rw), rw, np.where(big, 45, 23)), np.where(wide, 23, 15), 10], 0)
    geoms = []
    for geom, w in zip(f.geometry.values, width):
        if geom.geom_type == "LineString":
            geoms.append(geom.buffer(w / 2, cap_style="flat", join_style="round"))
        else:
            geoms.append(geom)
    f = f.set_geometry(gpd.GeoSeries(geoms, index=f.index, crs=UTM))  # same row labels as f
    f = dated_pavement(f)
    # vertices every 25 m so the flat polygons follow the terrain (earcut joins the long
    # edges of a runway across its width, so the inside follows too); segmentize can turn
    # a clipped piece with a pinched ring into a MultiPolygon, so explode afterwards
    # holes (the grass between Floyd Bennett Field's runways, mapped as one apron with 15
    # holes) are cut open: the binary format carries simple rings
    from ground_detail import cut_holes
    f = f.set_geometry(f.geometry.make_valid())
    f = f.explode(index_parts=False).reset_index(drop=True)
    f = f[f.geometry.geom_type == "Polygon"].reset_index(drop=True)
    cut = [cut_holes(geom) for geom in f.geometry.values]
    f = f.loc[np.repeat(np.arange(len(f)), [len(c) for c in cut])].reset_index(drop=True)
    f = f.set_geometry(gpd.GeoSeries([p for c in cut for p in c], crs=UTM).segmentize(25).make_valid())
    f = f.explode(index_parts=False).reset_index(drop=True)
    f = f[(f.geometry.geom_type == "Polygon") & (f.geometry.area > 20)].reset_index(drop=True)
    f = f.set_geometry(gpd.GeoSeries([shapely.Polygon(g_.exterior) for g_ in f.geometry.values], crs=UTM))
    ll = f.to_crs(4326)
    # ground year of a piece = median over its representative point and up to 24 of its
    # vertices ("always land" counts as earliest): one cell of a ditch or pond that only
    # became land with a later building does not hold back a whole taxiway
    smp = []
    for geom in ll.geometry.values:
        xy = np.asarray(geom.exterior.coords)[:-1, :2]
        xy = xy[np.linspace(0, len(xy) - 1, min(len(xy), 24)).astype(int)]
        rp = geom.representative_point()
        smp.append(np.vstack([[rp.x, rp.y], xy]))
    n_s = np.array([len(s) for s in smp])
    allp = np.vstack(smp)
    lys = land_year(allp[:, 0], allp[:, 1])
    lys = np.where(np.isfinite(lys), lys, -1e4)
    ly = np.array([np.median(v) for v in np.split(lys, np.cumsum(n_s)[:-1])])
    ly = np.where(ly < 0, np.nan, ly)
    start = np.where(np.isfinite(ly), np.maximum(f.opened.values, ly + 0.5), f.opened.values)
    log(f"airports: {int((np.isfinite(ly) & (ly + 0.5 > f.opened.values)).sum())} of {len(f)} pieces wait for made land")
    # made land under each airfield: reported, never forced on the researched opening year
    from ground_rule import ground_year
    gy = ground_year(pu.to_crs(4326).geometry.values)
    aname = f.aname.values if "aname" in f else np.full(len(f), None)
    conf = []
    for nm, cls_, op, cl, g_y in zip(pu["name"], pu["class"], pu.opened, pu.closed, gy):
        m = aname == nm
        w = m & np.isfinite(ly) & (ly + 0.5 > f.opened.values)
        conf.append({"airfield": nm, "class": cls_, "opened": op, "closed": cl,
                     "latest_land_year_under_outline": g_y, "outline_predates_ground": bool(np.isfinite(g_y) and g_y > op),
                     "pieces": int(m.sum()), "pieces_waiting": int(w.sum()),
                     "latest_piece_start": float(start[m].max()) if m.any() else np.nan,
                     "max_delay_years": float((start[w] - f.opened.values[w]).max()) if w.any() else 0.0,
                     "in_city": bool(_in_city(shapely.points([(shapely.centroid(pg).x, shapely.centroid(pg).y)]))[0])
                     if (pg := pu.to_crs(4326).geometry.values[list(pu["name"]).index(nm)]) is not None else False})
    (INTERIM / "airports").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(conf).to_csv(INTERIM / "airports" / "ground_conflicts.csv", index=False)
    log(f"airports: {sum(c['outline_predates_ground'] for c in conf)} of {len(conf)} airfields open before the latest made land "
        f"under their outline (data/interim/airports/ground_conflicts.csv)")
    # dated pavement for the terrain: the airfield's grass can follow its pavement phases,
    # not the whole of today's outline from the opening year
    kind_arr = f["class"].map(KIND).values
    gpd.GeoDataFrame({"start": start, "end": f.closed.values, "kind": kind_arr, "airport_class": f.aclass.values},
                     geometry=f.geometry.values, crs=UTM).to_crs(4326).to_parquet(INTERIM / "airport_pavement.parquet")
    ground = Ground()
    starts, pos, kinds, years = [0], [], [], []
    # drawn in this order without depth writes (viewer DrapeExtension): aprons, then
    # taxiways, then runways on top; big pieces before small ones
    order = np.lexsort((-f.geometry.area.values, -kind_arr))
    for i in order:
        geom, k, y0, y1 = ll.geometry.values[i], kind_arr[i], start[i], f.closed.values[i]
        ring = np.asarray(geom.exterior.coords)[:, :2]
        z = ground(ring[:, 0], ring[:, 1]) + 0.35
        pos.append(np.column_stack([ring[:, 0] - ORIGIN[0], ring[:, 1] - ORIGIN[1], z]).ravel())
        starts.append(starts[-1] + len(ring))
        kinds.append(k)
        years.extend((float(y0), float(y1)))
    # centre lines of runways (long axis of each piece): drawn with a minimum pixel width
    # so the airfields still read when zoomed far out
    lstarts, lpos, lkind, lwidth, lyears = [0], [], [], [], []
    fu = f.geometry.values
    for geom, k, y0, y1 in zip(fu, kind_arr, start, f.closed.values):
        # runways only (taxiway pieces are curved / L-shaped), and only pieces that are
        # close to a rectangle; width = area / length (the true mean width)
        if k != 0:
            continue
        mrr = geom.minimum_rotated_rectangle
        if geom.area < 0.8 * mrr.area:
            continue
        rect = np.asarray(mrr.exterior.coords)[:4]
        e1, e2 = rect[1] - rect[0], rect[2] - rect[1]
        if np.hypot(*e1) >= np.hypot(*e2):
            a, b = (rect[0] + rect[3]) / 2, (rect[1] + rect[2]) / 2
        else:
            a, b = (rect[0] + rect[1]) / 2, (rect[2] + rect[3]) / 2
        L = np.hypot(*(b - a))
        w = geom.area / max(L, 1.0)
        if L < 3 * w:
            continue
        pl = gpd.GeoSeries(gpd.points_from_xy([a[0], b[0]], [a[1], b[1]]), crs=UTM).to_crs(4326)
        lon, lat = pl.x.values, pl.y.values
        z = ground(lon, lat) + 0.45
        lpos.append(np.column_stack([lon - ORIGIN[0], lat - ORIGIN[1], z]).ravel())
        lstarts.append(lstarts[-1] + 2)
        lkind.append(k)
        lwidth.append(min(255, max(1, round(w))))
        lyears.extend((float(y0), float(y1)))
    write_columnar(VIEWER_DATA / "airport-lines.bin.gz", {
        "start_indices|shuffle": np.asarray(lstarts, np.uint32),
        "positions|shuffle": (np.concatenate(lpos) if lpos else np.zeros(0)).astype(np.float32),
        "kind": np.asarray(lkind, np.uint8),
        "width": np.asarray(lwidth, np.uint8),
        "years": np.asarray(lyears, np.float32),
    }, origin=ORIGIN, counts={"paths": len(lkind), "vertices": lstarts[-1]})
    write_columnar(VIEWER_DATA / "airports.bin.gz", {
        "start_indices|shuffle": np.asarray(starts, np.uint32),
        "positions|shuffle": (np.concatenate(pos) if pos else np.zeros(0)).astype(np.float32),
        "kind": np.asarray(kinds, np.uint8),
        "years": np.asarray(years, np.float32),
    }, origin=ORIGIN, counts={"polygons": len(kinds), "vertices": starts[-1]})
    log(f"airports: {len(kinds)} runway / taxiway / apron polygons ({np.bincount(kinds, minlength=3).tolist()}), "
        f"{len(lkind)} runway centre lines")


if __name__ == "__main__":
    main()
