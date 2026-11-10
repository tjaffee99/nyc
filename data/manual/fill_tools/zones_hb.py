"""Harbour and river islands.  Outlines are Overture base_land / land_use polygons (today's islands)."""
from zonelib import *
from shapely import wkb
import traceback

R = Registry(); WIKI = 'https://en.wikipedia.org/wiki/'
c = con()


def land(name, cls=None):
    q = f"select ST_AsWKB(geometry) from '{OV}/base_land.parquet' where name='{name}'" + (f" and class='{cls}'" if cls else '')
    return biggest(unary_union([to_utm(wkb.loads(bytes(g))).buffer(0) for g, in c.execute(q).fetchall()]))


def use(name):
    q = f"select ST_AsWKB(geometry) from '{OV}/region5_land_use.parquet' where name='{name}' order by ST_Area(geometry) desc limit 1"
    return biggest(to_utm(wkb.loads(bytes(c.execute(q).fetchone()[0]))).buffer(0))


def zone(fn):
    try: fn()
    except Exception as e:
        print('!! FAILED', repr(e)[:200]); traceback.print_exc(limit=1)


gov = use('Governors Island')
zone(lambda: R.add('hb_governors_island_fill', 'Governors Island: the southern extension', 1901, 1913.0, gov, 'fill', 'coarse',
     'The Army Corps of Engineers added 4.787 million cubic yards of fill south of the original island, using material from the first '
     'subway line: 103 acres, "mostly finished by 1909-1910 and declared complete by January 1913". Start year estimated from the '
     'subway excavation. Ring = the whole island (69.6 ha); the original island is the part north of Division Road / Liggett Hall.',
     WIKI + 'Governors_Island', tol=3))

ell = land('Ellis Island')
hull_gap = biggest(ell.convex_hull.difference(ell))            # the ferry basin
mouth = hull_gap.boundary.difference(ell.buffer(0.5))
M = (mouth.centroid.x, mouth.centroid.y)
I = max(hull_gap.exterior.coords, key=lambda q: math.dist(q, M))      # closed end of the basin
p0 = extend(I, M, 600); p1 = extend(M, I, 900)
left = Polygon([p0, p1, offset(p1, extend(p0, p1, 1), 900), offset(p0, p1, 900)])
a, b = ell.intersection(left), ell.difference(left)
north, south = (a, b) if a.centroid.y > b.centroid.y else (b, a)
print('Ellis: basin %.2f ha, north side %.2f ha, south side %.2f ha' % (hull_gap.area / 1e4, north.area / 1e4, south.area / 1e4))
EI = WIKI + 'Ellis_Island'
zone(lambda: R.add('hb_ellis_island_north', 'Ellis Island, north side (island 1: the original island and the fill round it)', 1890, 1896,
     north, 'fill', 'coarse',
     'The original island was about 3.3 acres; the magazine was ordered torn down 11 April 1890 for the immigration station and the '
     'island "was expanded to 14 acres by 1896". Ring = the island north-east of the ferry basin; the natural core inside it is not fill.', EI))
zone(lambda: R.add('hb_ellis_island_south', 'Ellis Island, south side (islands 2 and 3 and the fill between them)', 1898, 1934,
     south, 'fill', 'coarse',
     'Island 2 (3.33 acres) was finished December 1898, island 3 (4.75 acres) contracted April 1905 and complete 1906 (20.25 acres in '
     'all); the basin between islands 2 and 3 was filled in the 1920s; the island reached 27.5 acres in the 1930s (end year 1934 '
     'estimated from "between the late 1890s and the 1930s").', EI))

rw = land('Randalls and Wards Islands'); ra = land('Randalls Island'); wa = land('Wards Island')
gap = rw.difference(ra.buffer(1)).difference(wa.buffer(1))
print('Randalls %.1f Wards %.1f combined %.1f gap %.1f ha' % (ra.area / 1e4, wa.area / 1e4, rw.area / 1e4, gap.area / 1e4))
lhg = ra.buffer(160).intersection(wa.buffer(160)).intersection(rw)
RW = WIKI + 'Randalls_and_Wards_Islands'
zone(lambda: R.add('hb_little_hell_gate', 'Little Hell Gate, the channel between Randalls and Wards islands', 1955, 1962,
     biggest(lhg), 'water_fill', 'coarse',
     '"Infilling took place beginning in the mid-1950s"; the channel "was filled by the early 1960s" (a short inlet remains on the east). '
     'Ring = the land within 160 m of both islands as OpenStreetMap divides them; it brackets the old channel.', RW))
for nm, pgx, extra in (('Randalls', ra, ' Sunken Meadow Island (about 20 acres, to the east) was joined in 1955 and the Hammock "was subsumed through filling operations".'),
                      ('Wards', wa, ' Wards Island was about 145 acres, with marsh on its western and northern shores.')):
    zone(lambda nm=nm, pgx=pgx, extra=extra: R.add(f'hb_{nm.lower()}_island_shore', f'{nm} Island: shore and marsh fill', 1934, 1962,
         pgx.difference(lhg.buffer(1)), 'fill', 'coarse',
         'Bracket estimated from the park works of the 1930s to the filling of Little Hell Gate in the early 1960s.' + extra +
         ' Ring = the island as OpenStreetMap divides it, less the Little Hell Gate ring; the natural core is not fill.', RW, tol=4))
zone(lambda: R.add('hb_rikers_island', 'Rikers Island enlargement', 1884, 1943, land('Rikers Island'), 'fill', 'coarse',
     'Sold to the city in 1884; the original island of about 90 acres was enlarged to 415 acres, first with ashes hauled by convict '
     'labour, and "landfill continued to be added until 1943". Ring = the whole island; the natural core is not fill.',
     WIKI + 'Rikers_Island', tol=4))
zone(lambda: R.add('hb_roosevelt_island_shore', 'Roosevelt (Blackwell\'s) Island: shore fill', 1830, 1975, land('Roosevelt Island'), 'fill', 'coarse',
     '"The island was 107 acres prior to the 18th century but has been expanded to 147 acres"; fill added "since the 19th century". '
     'No dated stages found: the bracket is estimated. Ring = the whole island.', WIKI + 'Roosevelt_Island', tol=3))
zone(lambda: R.add('hb_u_thant_island', 'U Thant (Belmont) Island', 1905, 1907, land('U Thant Island').buffer(4), 'fill', 'precise',
     'Artificial islet: spoil from a shaft sunk on Man-o\'-War Reef for the Steinway Tunnel built the reef up into an island; the tunnel '
     'was completed between 1905 and 1907 (work first started and stopped in 1892).', WIKI + 'U_Thant_Island', tol=1))
zone(lambda: R.add('hb_mill_rock', 'Mill Rock: Great and Little Mill Rock joined', 1890, 1890.9, land('Mill Rock'), 'fill', 'coarse',
     '"In 1890 the Flood Island remnants were used to fill the space between Great and Little Mill Rocks." Ring = today\'s islet; the '
     'two rocks themselves are natural.', WIKI + 'Mill_Rock', tol=1))
zone(lambda: R.add('hb_hoffman_island', 'Hoffman Island (Upper Quarantine)', 1860, 1873, use('Hoffman Island'), 'fill', 'precise',
     'Artificial island on Orchard Shoal: sand dredged from the harbour was dumped from 1860; the island was "created in 1873".',
     WIKI + 'Hoffman_Island', tol=2))
zone(lambda: R.add('hb_swinburne_island', 'Swinburne Island (Dix Island, Lower Quarantine)', 1860, 1870, use('Swinburne Island'), 'fill', 'precise',
     'Artificial island made of dredged sand from 1860; renamed in 1869 and fitted out as a quarantine station in 1870.',
     WIKI + 'Swinburne_Island', tol=2))
R.save('hb')
