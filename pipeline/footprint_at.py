"""Tool: list the city's building footprints around a point, for landmark modelling and checks.

  python footprint_at.py <lon> <lat> [radius_m=80] [--rings] [--anchor lon,lat]

Prints, nearest first: BIN, name, recorded year, roof height (m, measured), ground elevation
(m), area (m2), the bearing of the longest edge, and (--rings) the outline in local metres
(x east, y north) around the anchor (default: the query point) — the frame the landmark kit
uses (kit.ts lngLatToLocal).
"""
from __future__ import annotations

import math
import sys

import duckdb
import numpy as np
import shapely

from common import INTERIM

SRC = INTERIM / "nyc_footprints_raw.parquet"


def local(anchor, lon, lat):
    kx = 111_320 * math.cos(math.radians(anchor[1]))
    return (lon - anchor[0]) * kx, (lat - anchor[1]) * 110_574


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    lon, lat = float(args[0]), float(args[1])
    rad = float(args[2]) if len(args) > 2 else 80.0
    rings = "--rings" in sys.argv
    anchor = (lon, lat)
    if "--anchor" in sys.argv:
        anchor = tuple(float(v) for v in sys.argv[sys.argv.index("--anchor") + 1].split(","))
    dx = rad / (111_320 * math.cos(math.radians(lat))) * 1.5
    dy = rad / 110_574 * 1.5
    con = duckdb.connect()
    rows = con.execute(f"""SELECT bin, name, year_raw, height_m, ground_m, feature_code, lon, lat, geometry
        FROM '{SRC}' WHERE lon BETWEEN {lon - dx} AND {lon + dx} AND lat BETWEEN {lat - dy} AND {lat + dy}""").fetchall()
    out = []
    for bin_, name, yr, h, gnd, fc, clon, clat, wkb in rows:
        g = shapely.from_wkb(bytes(wkb))
        poly = max(getattr(g, "geoms", [g]), key=lambda p: p.area)
        xy = np.array([local(anchor, x, y) for x, y in np.asarray(poly.exterior.coords)[:, :2]])
        q = np.array(local(anchor, lon, lat))
        d = float(shapely.Polygon(xy).distance(shapely.Point(q)))
        if d > rad:
            continue
        e = np.diff(xy, axis=0)
        k = int(np.argmax(np.hypot(e[:, 0], e[:, 1])))
        bearing = (math.degrees(math.atan2(e[k, 0], e[k, 1])) + 360) % 180
        area = float(shapely.Polygon(xy).area)
        out.append((d, bin_, name, yr, h, gnd, fc, area, bearing, xy, clon, clat))
    out.sort(key=lambda r: r[0])
    for d, bin_, name, yr, h, gnd, fc, area, bearing, xy, clon, clat in out:
        print(f"d={d:6.1f} m  BIN {bin_}  {name or '-'}  year {yr}  roof {h} m  ground {gnd} m  area {area:.0f} m2  "
              f"long edge bearing {bearing:.1f} deg  code {fc}  centroid {clon:.6f},{clat:.6f}")
        if rings:
            print("   ring: " + " ".join(f"[{x:.1f},{y:.1f}]" for x, y in xy[:-1]))


if __name__ == "__main__":
    main()
