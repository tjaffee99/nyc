"""Ferries with documented routes and years -> rows for data/manual/routes.csv (mode `ferry`).
Terminals come from the data, not from memory: the foot of the named street (its end vertex toward the water,
or the point where it meets the waterfront street: Overture street centre lines) or the centroid of the named
terminal building (Overture buildings). The course over the water is schematic: a straight line, bent once
where the straight line would cross land on the terrain grid."""
import sys

import duckdb
import numpy as np
from shapely.geometry import LineString, Point

W = "https://en.wikipedia.org/wiki/"
HUD = W + "List_of_ferries_across_the_Hudson_River_to_New_York_City"
EAST = W + "List_of_ferries_across_the_East_River"
foot = lambda s, d, hint=None: ("foot", s, d, hint)
meet = lambda a, b, hint=None: ("meet", a, b, hint)
bldg = lambda n: ("bldg", n)
MAN_W, MAN_E = (-74.012, 40.715), (-74.003, 40.707)
WHITEHALL = bldg("Staten Island Ferry Whitehall Terminal")
HOBOKEN = bldg("Hoboken Terminal")
EXCHANGE = foot("Exchange Place", "E", (-74.033, 40.716))
WEEHAWKEN = foot("Pershing Road", "E", (-74.012, 40.776))
FULTON_BK = foot("Old Fulton Street", "W", (-73.994, 40.703))
BROADWAY_BK = foot("Broadway", "W", (-73.967, 40.711))
BORDEN = foot("Borden Avenue", "W", (-73.958, 40.742))
E34 = foot("East 34th Street", "E", (-73.972, 40.744))
WALL = meet("Wall Street", "South Street", MAN_E)
FERRIES = [
 ("ferry_staten_island", "Staten Island Ferry (Whitehall - St. George)", [WHITEHALL, bldg("St. George Ferry Terminal")], 1817, 9999,
  "Steam ferry of the Richmond Turnpike Company from 1817 (to its landing at Tompkinsville, 1 km south of St. George until the St. George terminal opened in March 1886); municipal since 1905-10-25.", W + "Staten_Island_Ferry"),
 ("ferry_fulton_colonial", "The Brooklyn ferry (before steam)", [meet("Maiden Lane", "Pearl Street", MAN_E), FULTON_BK], 1642, 1814.36,
  "First ferry grant to Cornelis Dircksen, 1642. The Manhattan landing moved (Broad St, then Maiden Lane at the old Pearl St shore): its place here is estimated.", W + "Fulton_Ferry_(ferry)"),
 ("ferry_fulton", "Fulton Ferry (Fulton St, Manhattan - Fulton St, Brooklyn)", [meet("Fulton Street", "South Street", MAN_E), FULTON_BK], 1814.36, 1924.05,
  "First trip of the steamboat Nassau 1814-05-10; ceased 1924-01-19.", W + "Fulton_Ferry_(ferry)"),
 ("ferry_wall_street", "Wall Street Ferry (Wall St - Montague St, Brooklyn)", [WALL, meet("Montague Street", "Furman Street", (-73.998, 40.695))], 1853, 1912,
  "Operated 1853-1912.", EAST),
 ("ferry_peck_slip", "Peck Slip Ferry (Peck Slip - Broadway, Williamsburg)", [meet("Peck Slip", "South Street", MAN_E), BROADWAY_BK], 1836, 1860,
  "Operated 1836-1860.", EAST),
 ("ferry_42nd_broadway", "42nd Street Ferry (E 42nd St - Broadway, Williamsburg)", [foot("East 42nd Street", "E", (-73.969, 40.749)), BROADWAY_BK], 1901, 1909,
  "Operated 1901-1909.", EAST),
 ("ferry_34th_street", "34th Street Ferry (E 34th St - Hunters Point)", [E34, BORDEN], 1859.3, 1925.17,
  "East River Ferry Company from 1859-04-20, Long Island Rail Road from 1892; last day 1925-03-03.", EAST),
 ("ferry_34th_street_vehicular", "East 34th Street Vehicular Ferry (E 34th St - Hunters Point)", [E34, BORDEN], 1927.71, 1936.54,
  "1927-09-16 to 1936-07-15.", EAST),
 ("ferry_communipaw", "Communipaw Ferry (Liberty St - Communipaw, Central Railroad of New Jersey)", [meet("Liberty Street", "West Street", MAN_W), bldg("Central Railroad of New Jersey Terminal")], 1661, 1967,
  "Listed 1661-1967: a ferry to Communipaw was chartered by Stuyvesant in 1661; the Central Railroad of New Jersey's steam ferry to its terminal ran until 1967. The Manhattan terminal stood at Liberty St and West St (the shore before Battery Park City).", HUD),
 ("ferry_jersey_city", "Jersey City Ferry (Cortlandt St - Paulus Hook / Exchange Place, Pennsylvania Railroad)", [meet("Cortlandt Street", "West Street", MAN_W), EXCHANGE], 1764, 1949,
  "Operated 1764-1949.", HUD),
 ("ferry_west_shore", "West Shore Ferry (Cortlandt St - Weehawken Terminal)", [meet("Cortlandt Street", "West Street", MAN_W), WEEHAWKEN], 1885, 1959,
  "Operated 1885-1959. Weehawken Terminal is taken at the foot of Pershing Road (estimated).", HUD),
 ("ferry_hoboken_barclay", "Hoboken Ferry (Barclay St - Hoboken Terminal)", [meet("Barclay Street", "West Street", MAN_W), HOBOKEN], 1821, 1967,
  "Operated 1821-1967 (Delaware, Lackawanna and Western, later Erie Lackawanna); no Hudson ferry ran between 1967 and 1989.", HUD),
 ("ferry_pavonia", "Pavonia Ferry (Chambers St - Pavonia Terminal, Erie Railroad)", [meet("Chambers Street", "West Street", MAN_W), foot("Pavonia Avenue", "E", (-74.036, 40.727))], 1856, 1958,
  "Operated 1856-1958. Pavonia Terminal is taken at the foot of Pavonia Avenue (estimated).", HUD),
 ("ferry_desbrosses", "Desbrosses Street Ferry (Desbrosses St - Exchange Place)", [meet("Desbrosses Street", "West Street", (-74.011, 40.724)), EXCHANGE], 1862, 1930,
  "Operated 1862-1930.", HUD),
 ("ferry_christopher", "Christopher Street Ferry (Christopher St - Hoboken Terminal)", [meet("Christopher Street", "West Street", (-74.010, 40.733)), HOBOKEN], 1838, 1955,
  "Operated 1838-1955.", HUD),
 ("ferry_weehawken_42nd", "Weehawken Ferry (W 42nd St - Weehawken Terminal)", [meet("West 42nd Street", "12th Avenue", (-74.001, 40.762)), WEEHAWKEN], 1884, 1959,
  "Operated 1884-1959. Weehawken Terminal is taken at the foot of Pershing Road (estimated).", HUD),
 ("ferry_125th_edgewater", "125th Street Ferry (W 125th St - Edgewater)", [foot("West 125th Street", "W", (-73.958, 40.817)), foot("Dempsey Avenue", "E", (-73.977, 40.827))], 1903, 1941,
  "Operated 1903-1941. The Edgewater slip is taken at the foot of Dempsey Avenue (estimated).", HUD),
 ("ferry_nyc_east_river", "NYC Ferry: East River route", [WALL, FULTON_BK, foot("South 9th Street", "W", (-73.967, 40.709)), foot("North 6th Street", "W", (-73.962, 40.720)),
  foot("India Street", "W", (-73.960, 40.732)), BORDEN, E34], 2017.33, 9999,
  "NYC Ferry launched in 2017 with service along the East River (May 2017). Landings are taken at the feet of Wall St, Old Fulton St, S 9th St, N 6th St, India St, Borden Ave and E 34th St (estimated).", W + "NYC_Ferry"),
]


def rows(G):
    sys.path.insert(0, G["ROOT"] + "/pipeline")
    from nyc_buildings import Ground
    from roads import land_year
    ground0 = Ground()
    era = [1609.0]

    def ground(lon, lat):
        """terrain height, with the land made after the ferry began counted as water"""
        z = ground0(lon, lat)
        ly = land_year(lon, lat)
        return np.where(np.isfinite(ly) & (ly > era[0]), 0.9, z)
    to_utm, to_ll = G["TO_UTM"], G["TO_LL"]
    con = duckdb.connect()
    con.execute("install spatial; load spatial;")

    def resolve(spec):
        if spec[0] == "bldg":
            r = con.execute("select st_x(st_centroid(geometry)), st_y(st_centroid(geometry)) from "
                            f"'{G['OV']}/building.parquet' where name = ? order by st_area(geometry) desc limit 1",
                            [spec[1]]).fetchone()
            if r is None:
                raise ValueError(f"no building {spec[1]!r}")
            return Point(to_utm.transform(*r))
        if spec[0] == "foot":
            g = G["street_geom"](spec[1], hint=spec[3])
            if g is None:
                raise ValueError(f"no street {spec[1]!r}")
            c = np.array([p for part in getattr(g, "geoms", [g]) for p in part.coords])[:, :2]
            k = {"N": c[:, 1].argmax(), "S": c[:, 1].argmin(), "E": c[:, 0].argmax(), "W": c[:, 0].argmin()}[spec[2]]
            return Point(c[k])
        if spec[0] == "meet":
            b = G["street_geom"](spec[2], hint=spec[3])
            if b is None:
                raise ValueError(f"no street {spec[2]!r}")
            return G["anchor"](("x", spec[1], spec[3]) if spec[3] else ("x", spec[1]), set(), b)
        raise ValueError(spec)

    def water(line):
        L = line.length
        d = np.arange(200, L - 200, 50.0)
        if not len(d):
            return True
        pts = [line.interpolate(v) for v in d]
        lon, lat = to_ll.transform([p.x for p in pts], [p.y for p in pts])
        return bool((ground(np.array(lon), np.array(lat)) <= 1.0).all())

    def leg(a, b):
        line = LineString([a.coords[0], b.coords[0]])
        if water(line):
            return [a.coords[0], b.coords[0]]
        m = np.array(line.interpolate(0.5, normalized=True).coords[0])
        v = np.array(b.coords[0]) - np.array(a.coords[0])
        nrm = np.array([-v[1], v[0]]) / max(np.hypot(*v), 1e-6)
        for k in range(1, 30):
            for sgn in (1, -1):
                w = m + sgn * k * 150.0 * nrm
                if water(LineString([a.coords[0], tuple(w)])) and water(LineString([tuple(w), b.coords[0]])):
                    return [a.coords[0], tuple(w), b.coords[0]]
        return [a.coords[0], b.coords[0]]

    out = []
    for rid, name, stops, y0, y1, note, url in FERRIES:
        era[0] = float(y0)
        try:
            pts = [resolve(s) for s in stops]
        except Exception as e:  # noqa: BLE001
            print(f"!! {rid}: {e}")
            continue
        coords = []
        for a, b in zip(pts[:-1], pts[1:]):
            c = leg(a, b)
            coords += c if not coords else c[1:]
        # a ferry line ends at today's shore: where the old slip now lies inland (made land), the end is
        # pulled back to 40 m behind the first water on its last leg
        for end in (0, -1):
            a, b = np.array(coords[end]), np.array(coords[1 if end == 0 else -2])
            L = float(np.hypot(*(b - a)))
            d = np.arange(0, min(L, 1500.0), 20.0)
            p = a + (b - a) * (d / L)[:, None]
            lo_, la_ = to_ll.transform(p[:, 0], p[:, 1])
            wet = np.nonzero(ground(np.array(lo_), np.array(la_)) <= 1.0)[0]
            if len(wet) and d[wet[0]] > 120:
                coords[end] = tuple(a + (b - a) * (d[wet[0]] - 40) / L)
        lon, lat = to_ll.transform([c[0] for c in coords], [c[1] for c in coords])
        gz = ground(np.array(lon), np.array(lat))
        print(f"{rid:30s} {y0:8.2f}-{y1:8.2f} {LineString(coords).length / 1000:5.2f} km " +
              " -> ".join(f"{a:.4f},{b:.4f} ({z:.0f} m)" for a, b, z in zip(lon, lat, gz)))
        out.append([rid, name, "ferry", y0, y1, "ground", 1, "lonlat", "; ".join(f"{a:.5f} {b:.5f}" for a, b in zip(lon, lat)),
                    note, url])
    return out
