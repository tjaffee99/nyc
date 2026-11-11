"""Encode building footprints into the viewer's BAYT building format (as sf_export.py
does for San Francisco): delta-coded integer rings (POSITION_SCALE degrees) with ring-end markers, plus
per-feature columns. Shared by the region tiles (region_buildings.py)."""
from __future__ import annotations

import zlib

import numpy as np
import shapely

from export_columnar import write_columnar


# coordinates are stored as integer steps of this many degrees (about 11 cm north-south,
# 8 cm east-west: the footprints are good to 60 cm) — the published site must stay small
POSITION_SCALE = 1e-6


def encode(geoms, origin, scale=None):
    """geoms: shapely Polygons (EPSG:4326). Returns (positions int32 flat, starts u32, valid u8, n_vertices)."""
    scale = scale or POSITION_SCALE
    pos_chunks, valid_chunks = [], []
    starts = np.zeros(len(geoms) + 1, np.uint32)
    vcount = 0
    ox, oy = origin
    for i, geom in enumerate(geoms):
        g = shapely.geometry.polygon.orient(geom, 1.0)  # CCW outer, CW holes
        rings = [np.asarray(g.exterior.coords)[:, :2]] + [np.asarray(r.coords)[:, :2] for r in g.interiors]
        closed = np.concatenate(rings)
        valid = np.ones(len(closed), np.uint8)
        e = 0
        for r in rings:
            e += len(r)
            valid[e - 1] = 0
        q = np.rint((closed - (ox, oy)) / scale).astype(np.int64)
        d = np.diff(q, axis=0, prepend=np.zeros((1, 2), np.int64))  # first vertex relative to the origin
        pos_chunks.append(d.astype(np.int32))
        valid_chunks.append(valid)
        vcount += len(closed)
        starts[i + 1] = vcount
    if not pos_chunks:
        return np.zeros(0, np.int32), starts, np.zeros(0, np.uint8), 0
    return np.concatenate(pos_chunks).ravel(), starts, np.concatenate(valid_chunks), vcount


COMPACT_SCALE = 5e-6     # the outer tier: corners to half a metre


def write_buildings(path, df, origin, conf_codes, use_categories, extra_meta=None, compact=False):
    """df: GeoDataFrame (EPSG:4326, Polygons) with start_year, end_year, height, base,
    year_confidence, use, raw_year, stories, mat, roof, fid_key.
    compact (the outer counties' tier: the same format, fewer bits): corners to half a metre,
    years to a quarter, heights to half a metre, and an id of one byte (the id only varies the
    colour a little)."""
    scale = COMPACT_SCALE if compact else POSITION_SCALE
    positions, starts, valid, vcount = encode(df.geometry.values, origin, scale)
    fid = np.array([zlib.crc32(str(k).encode()) for k in df.fid_key.astype(str)], dtype=np.uint32)
    stories = np.nan_to_num(df.stories.astype(float).values, nan=0).clip(0, 255).astype(np.uint8)
    sy, hh, bb = df.start_year.astype(np.float32).values, df.height.astype(np.float32).values, df.base.astype(np.float32).values
    if compact:
        fid = fid & np.uint32(0xFF)
        sy = (np.round(sy * 4) / 4).astype(np.float32)
        hh = (np.round(hh * 2) / 2).astype(np.float32)
        bb = (np.round(bb * 2) / 2).astype(np.float32)
    cols = {
        "positions_delta|shuffle": positions,
        "start_indices|shuffle": starts,
        "vertex_valid": valid,
        "start_year": sy,
        "end_year": df.end_year.astype(np.float32).values,
        "height": hh,
        "base": bb,
        "confidence": df.year_confidence.map(conf_codes).fillna(1).astype(np.uint8).values,
        "use": df.use.astype(np.uint8).values,
        "raw_year": df.raw_year.fillna(0).astype(np.int16).values,
        "stories": stories,
        "mat": df.mat.astype(np.uint8).values,
        "roof": df.roof.astype(np.uint8).values,
        "fid|shuffle": fid,
    }
    meta = {"position_scale": scale, "use_categories": use_categories, "confidence": list(conf_codes)}
    # where the year comes from (shown in the click popup), and the names of named buildings
    if "year_src" in df:
        labels = [source_label(v) for v in df.year_src.fillna("").astype(str).values]
        cats = sorted(set(labels))
        code = {c: i for i, c in enumerate(cats)}
        cols["src"] = np.array([code[v] for v in labels], dtype=np.uint8)
        meta["sources"] = cats
    if "name" in df:
        nm = df["name"].values
        meta["names"] = {str(i): str(v) for i, v in enumerate(nm) if isinstance(v, str) and v.strip()}
    meta.update(extra_meta or {})
    return write_columnar(path, cols, origin=origin, counts={"features": len(df), "vertices": int(vcount)}, meta=meta)


# ---- codes shared with the viewer (viewer/src/palette.ts MATERIALS, CONFIDENCE) -------------
CONF = {"exact": 0, "estimated": 1, "procedural": 2, "reconstructed": 3}
USE_CATEGORIES = ["unknown", "single-family home", "residential", "commercial", "office",
                  "industrial", "government / civic", "other"]
# facade materials
M_GENERIC, M_EARLY, M_FRAME, M_BRICK, M_MASONRY, M_STUCCO, M_MIDCENTURY, M_TOWER70, M_GLASS, M_CONTEMP, M_CIVIC, \
    M_INDUSTRIAL, M_DUTCH, M_BARK, M_BROWNSTONE, M_WHITEBRICK, M_CONTAINERS = range(17)
# roof codes: 0 flat (tar / gravel / membrane), 1 clay tile, 2 shingle / slate (pitched), 3 same as walls
R_FLAT, R_TILE, R_SHINGLE, R_WALL = range(4)


def source_label(src: str) -> str:
    """Plain words for a year_src code (nyc_buildings.py, nyc_predecessors.py)."""
    if src == "known":
        return "researched or official record (building permits, housing authority, cited history)"
    if src == "known_est":
        return "researched, but the year is an estimate"
    if src == "owner_reported":
        return "year reported by the owner (energy benchmarking filing): estimated"
    if src == "lot_year":
        return "city records: the year of the tax lot, shared by its buildings (an estimate for this one)"
    if src == "lpc":
        return "Landmarks Preservation Commission database"
    if src == "assessor":
        return "city records (footprint / tax lot year)"
    if src.startswith("heap_by"):
        return "assessor: 'by 1900' placeholder, estimated from the buildings around"
    if src.startswith("heap_about"):
        return "assessor: rounded year, spread over its range"
    if src == "neighbours":
        return "no recorded year: estimated from the buildings around"
    if src == "on_map":
        return "standing on a 19th-century atlas (year estimated)"
    if src == "evidence_by:law_old":
        return "an old-law tenement in the city's housing records: built by April 1901 (the assessor's year is later)"
    if src == "evidence_by:law_1929":
        return "a tenement class of before 1929 in the city's housing records: built by then (the assessor's year is later)"
    if src == "evidence_after:law_new":
        return "a new-law tenement in the city's housing records: built after April 1901"
    if src == "assessor_flagged":
        return "city records: a year the Department of Finance marks as its own estimate"
    if src.startswith("evidence_by:site") or src.startswith("evidence_after:site"):
        return "inside a site with a founding year: not older than the site (no year of its own on record)"
    if src.startswith("evidence_by:aerial"):
        return f"standing on the {src[-4:]} aerial photograph: built by then (no reliable year of its own on record)"
    if src.startswith("evidence_after:aerial"):
        return f"not yet on the {src[-4:]} aerial photograph: built after it (no reliable year of its own on record)"
    if src.startswith("evidence_by:topo"):
        return f"drawn on the USGS map surveyed in {src[-4:]}: built by then"
    if src == "modelled_cells":
        return ("no public construction year for this building: assigned from the assessor's own counts of buildings "
                "by five-year period in its 250 m cell (HISDAC-US; typically within about 10 years; not a record)")
    if src == "modelled":
        return ("no public construction year: modelled from the census's count of homes by decade built in the block "
                "group and the town's growth (typically within about 20 years; not a record)")
    if src.startswith("gapfill"):
        ev = src.split(":", 1)[1] if ":" in src else ""
        if ev.startswith("port+") or ev.startswith("yard+"):      # port_fill.py
            what = "shipping containers stacked in a container terminal" if "container" in ev else \
                   ("railroad cars standing in a yard" if "rail" in ev else "what stands on a working yard")
            return (f"generated: {what} (the terminal or yard and its opening year are real; "
                    "the positions, sizes and colours are generated)")
        if ev.startswith("site+"):      # site_fill.py: a roof read off the photograph inside a yard, fort or institution
            seen = ("the 1924 and 1951 aerial photographs show" if "1924+1951" in ev else
                    f"the {ev[-4:]} aerial photograph shows")
            return (f"generated: {seen} a roof here, inside a yard, fort or institution that no atlas mapped "
                    "(outline read off the photograph by a program: approximate; years and height estimated)")
        says = []
        ext = [p for p in ev.split("+") if p.startswith("extent")]
        if ext:
            says.append(f"the built-up area of the {ext[0][6:]} map covers this block")
        if "usgs1897" in ev:
            says.append("the USGS map of 1898 shows this ground built up")
        if "usgs194" in ev:
            says.append("the USGS map of the 1940s draws this block front as built")
        if "parcel" in ev or "neighbourhood" in ev:
            says.append("the lot's building is much younger than the neighbourhood around it")
        if "1924+1951" in ev:
            says.append("the 1924 and 1951 aerial photographs show a building on this lot")
        elif "aerial1924" in ev:
            says.append("the 1924 aerial photograph shows a building on this lot")
        elif "aerial1951" in ev:
            says.append("the 1951 aerial photograph shows a building on this lot")
        return "generated: " + ("; ".join(says) or "maps of the time show this ground built on") + " (no outline survives: lot-sized outline, years estimated)"
    if src == "parcel":
        return "property tax record (parcel year)"
    if src == "parcel_secondary":
        return "property tax record of the lot's main building (an outbuilding: estimated)"
    if src == "historic_register":
        return "state historic-resource inventory"
    if src == "historic_register_ca":
        return "state historic-resource inventory: an approximate ('circa') year (the assessor has only a placeholder)"
    if src == "after_demolition":
        return "city records: the building before it was removed that year; built after (year estimated)"
    if src == "after_map":
        return "a 19th-century atlas shows another building here: year estimated after it"
    if src.startswith("atlas_"):
        return f"outline traced from the {src[6:]} fire-insurance atlas (NYPL Building Inspector); years estimated"
    if src.startswith("map_"):
        return f"outline traced from a {src[4:]} map (OpenHistoricalMap); years estimated"
    if src == "ohm_documented":
        return "OpenHistoricalMap (documented lost building)"
    if src == "lenape_site":
        return "a documented Lenape site; the dwellings and where each stands are generated (drawn at twice their size)"
    if src == "early_site":
        return "a documented site of the colony (researched); outline from the kind of building, not a survey"
    if src == "lost_researched":
        return "researched record of a lost building"
    if src == "city_demolition":
        return "city records: a building removed since the 1990s (outline from the city's footprints)"
    if src.startswith("traced_"):
        return f"outline traced from a {src[7:]} atlas for this map; years estimated"
    if src == "pier":
        return "pier: outline and years researched (deck height estimated)"
    if src == "farmstead":
        return "a building mark on an 1890s USGS map (position real; outline and years estimated)"
    if src.startswith("evidence_after:site"):
        return "inside a site with a founding year: not older than the site"
    if src == "generated":
        return "generated from the built-up extent of the time (no outline survives)"
    return src or "unknown"
