"""Build data/tables/early_nyc.csv from rows_lenape.py + rows_colonial.py (scratch generator, not a stage).

Geocodes each row (street intersections from the Overture roads, LPC landmark and park anchors, or a
stated point), moves a point that falls in 1609 water / marsh / pond or in today's water to the nearest
dry ground (and says so in the note), estimates open end years from the built data, and prints checks.
"""
import csv, math, sys
import duckdb, shapely
from shapely import wkb
from shapely.geometry import Point
import geo
from rows_lenape import LEN
from rows_colonial import COL

OUT = '/home/user/nyc/data/tables/early_nyc.csv'
COLS = 'id,name,kind,start_year,end_year,lat,lon,height_m,footprint_m,rotation_deg,storeys,material,count,spread_m,confidence,shape_note,source_url,borough'.split(',')
BORO = {'Bronx': 'The Bronx'}
START = {'bk_nayack_1679': 1652}
WET = ('water', 'tidal_marsh', 'tidal_flat', 'pond', 'freshwater_wetland')
con = duckdb.connect()
PTS = '/home/user/nyc/data/interim/nyc_building_points.parquet'
FPS = '/home/user/nyc/data/interim/nyc_footprints_raw.parquet'
warn = []


def locate(loc, rid):
    t = loc[0]
    de = dn = 0
    how = ''
    if t == 'X':
        a, b, hint = loc[1], loc[2], loc[3]
        if len(loc) > 4: de, dn = loc[4], loc[5]
        try:
            p = geo.X(a, b, hint)
            d = math.hypot((p[0] - hint[0]) * 84400, (p[1] - hint[1]) * 110574)
            how = f'X ok ({d:.0f} m from hint)'
            if d > 400: warn.append(f'{rid}: {a} x {b} is {d:.0f} m from the hint - check')
        except KeyError as e:
            p = hint; how = f'X FAILED -> hint ({e})'; warn.append(f'{rid}: {e} -> used hint')
    elif t == 'P':
        p = (loc[1], loc[2]); how = 'P'
    elif t == 'LM':
        p = geo.LM(loc[1]); how = 'LM'
        if len(loc) > 2: de, dn = loc[2], loc[3]
    elif t == 'PK':
        p = geo.PK(loc[1]); how = 'PK'
        if len(loc) > 2: de, dn = loc[2], loc[3]
    if de or dn: p = geo.off(p, de, dn)
    return p, how


def dry(lon, lat):
    c = geo.cover1609(lon, lat)
    return not any(w in c.split(',') for w in WET) and not geo.water_today(lon, lat)


def nudge(lon, lat):
    """nearest dry point on rings of 20 m, up to 400 m"""
    if dry(lon, lat): return lon, lat, 0
    for r in range(20, 420, 20):
        best = None
        for k in range(24):
            a = 2 * math.pi * k / 24
            q = geo.off((lon, lat), r * math.sin(a), r * math.cos(a))
            if dry(*q):
                # prefer the candidate with the most dry neighbours (not a sliver)
                score = sum(dry(*geo.off(q, 25 * math.sin(b), 25 * math.cos(b))) for b in (0, 1.57, 3.14, 4.71))
                if best is None or score > best[0]: best = (score, q)
        if best: return best[1][0], best[1][1], r
    return lon, lat, -1


def city_year(lon, lat, start, r=60):
    dx = r / (111320 * math.cos(math.radians(lat))); dy = r / 110574
    rows = con.execute(f"select start_year from '{PTS}' where lon between {lon-dx} and {lon+dx} and lat between {lat-dy} and {lat+dy} and start_year > {start + 5} order by 1").fetchall()
    ys = [int(x[0]) for x in rows]
    if len(ys) >= 2: return ys[1], len(ys)
    if len(ys) == 1: return ys[0], 1
    return None, 0


def road_bearing(lon, lat):
    """bearing (0-180, compass) of the nearest named road within ~200 m"""
    p = Point(lon, lat); best = None
    for name, geoms in geo.roads().items():
        for g in geoms:
            d = g.distance(p)
            if d < 0.002 and (best is None or d < best[0]): best = (d, g)
    if not best: return 0
    g = best[1]
    s = g.project(p); a = g.interpolate(max(0, s - 0.0002)); b = g.interpolate(min(g.length, s + 0.0002))
    kx = math.cos(math.radians(lat))
    return round(math.degrees(math.atan2((b.x - a.x) * kx, b.y - a.y)) % 180)


def footprint_info(lon, lat, r=130):
    dx = r / (111320 * math.cos(math.radians(lat))); dy = r / 110574
    rows = con.execute(f"select bin, name, year_raw, height_m, geometry, lon, lat from '{FPS}' where lon between {lon-dx} and {lon+dx} and lat between {lat-dy} and {lat+dy}").fetchall()
    out = []
    kx = 111320 * math.cos(math.radians(lat))
    for b, n, y, h, g, x, yy in rows:
        geom = wkb.loads(bytes(g))
        d = geom.distance(Point(lon, lat)) * 96000
        xy = shapely.transform(geom, lambda c: [[(u - lon) * kx, (v - lat) * 110574] for u, v in c])
        mrr = xy.minimum_rotated_rectangle
        cs = list(mrr.exterior.coords)
        e = [(math.hypot(cs[i+1][0]-cs[i][0], cs[i+1][1]-cs[i][1]), math.degrees(math.atan2(cs[i+1][0]-cs[i][0], cs[i+1][1]-cs[i][1])) % 180) for i in range(2)]
        e.sort(reverse=True)
        rp = geom.representative_point()
        out.append((d, b, n, y, h, round(e[0][0], 1), round(e[1][0], 1), round(e[0][1]), round(xy.area), rp.x, rp.y))
    out.sort()
    return out


def main():
    rows = []
    specs = []
    for (rid, name, kind, end, loc, count, spread, conf, note, url) in LEN:
        camp = kind == 'lenape_camp'
        fp, h = ('4x4', 2.2) if camp else ('5x5', 2.5)
        if kind == 'fort': fp, h = '45x45', 3
        if rid == 'bk_nayack_1679': fp, h = '18.3x4.4', 3
        mat = 'wood frame' if kind == 'fort' else 'bark'
        specs.append((rid, name, kind, START.get(rid, 1600), end, loc, fp, h, 1, mat, count, spread, conf, note, url))
    specs += COL
    ids = set()
    for (rid, name, kind, start, end, loc, fp, h, st, mat, count, spread, conf, note, url) in specs:
        assert rid not in ids, rid; ids.add(rid)
        (lon, lat), how = locate(loc, rid)
        standing = note.startswith('STANDING')
        moved = 0
        if not standing:
            lon2, lat2, moved = nudge(lon, lat)
            if moved > 0:
                note += f' Point moved {moved} m to the nearest dry ground of the 1609 layer (the source\'s spot is water, marsh or pond there, or water today).'
                lon, lat = lon2, lat2
            elif moved < 0:
                warn.append(f'{rid}: no dry ground within 400 m')
        rot = 0
        if standing:
            fi = footprint_info(lon, lat)
            if fi:
                d, b, n, y, hh, L, Wd, brg, area, fx, fy = fi[0]
                lon, lat = fx, fy
                fp = f'{L}x{Wd}'; rot = brg
                note += f' City footprint: BIN {b}' + (f' ("{n}")' if n else '') + f', recorded year {y}, measured roof {hh:.1f} m, {area} m2 today (later wings included); lat / lon is a point inside that footprint; footprint_m and rotation_deg are its bounding rectangle.'
                if hh and hh > 2: h = round(hh, 1)
                print('   STANDING', rid, [(round(t[0]), t[1], t[2], t[3], t[8]) for t in fi[:4]])
            else:
                warn.append(f'{rid}: STANDING but no footprint within 60 m')
        elif count == 1:
            rot = road_bearing(lon, lat)
        cy = ''
        if end == 'city':
            y, n = city_year(lon, lat, start)
            if y is None or y > 1900:
                cy = f'capped ({y})' ; y = 1900
            end = max(y, start + 20)
        chk = geo.check(lon, lat)
        boro = chk['boro']
        if boro.endswith('?') or boro == 'OUTSIDE': warn.append(f'{rid}: borough {boro}')
        boro = BORO.get(boro.rstrip('?'), boro.rstrip('?'))
        if not (-74.27 <= lon <= -73.69 and 40.48 <= lat <= 40.93): warn.append(f'{rid}: outside box')
        rows.append(dict(id=rid, name=name, kind=kind, start_year=start, end_year=end, lat=f'{lat:.5f}', lon=f'{lon:.5f}', height_m=h,
                         footprint_m=fp, rotation_deg=rot, storeys=st, material=mat, count=count, spread_m=spread, confidence=conf,
                         shape_note=' '.join(note.split()), source_url=url, borough=boro))
        print(f"{rid:26s} {how[:34]:34s} {lon:.5f},{lat:.5f} mv={moved:<4} c1609={chk['c1609']:<12} wet={chk['wet_m']:<5} n150={chk['n150']:<4} end={end} {cy} {boro}")
    with open(OUT, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(rows)
    print(len(rows), 'rows ->', OUT)
    print('\nWARNINGS'); [print(' ', x) for x in warn]


if __name__ == '__main__':
    main()
