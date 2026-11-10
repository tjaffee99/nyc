"""Manhattan B: Hudson shore north of Gansevoort St, East River north of E 34th St, Harlem River,
ship canal and Marble Hill, ponds and marshes, reservoirs on Manhattan."""
from zonelib import *
import duckdb, traceback
from shapely import wkb
from shapely.geometry import box

S = mn(); isl = S.island; R = Registry(); X = lambda a, b: XX(S, a, b)
WIKI = 'https://en.wikipedia.org/wiki/'
BPCA = 'https://media.bpca.ny.gov/wp-content/uploads/2024/08/06043742/Appendix-D-Historic-and-Cultural-Resources.pdf'


def zone(fn):
    try:
        fn()
    except Exception as e:
        print('!! FAILED', fn.__name__, repr(e)[:200]); traceback.print_exc(limit=1)


# ---------------------------------------------------------------- Gansevoort peninsula and Thirteenth Avenue
A = S.x('West Street', 'Gansevoort Street'); B14 = S.x('West Street', 'West 14th Street')
A11 = S.x('West Street', 'West 11th Street')
nb2 = nb_line(S, 'West Street', A11, B14)
inl = S.x('Greenwich Street', 'Gansevoort Street')
bulk2 = line_offset(nb2, 62.0, inl)
pen = biggest(band(line_offset(nb2, 72.0, inl), line_offset(nb2, 420.0, inl)).intersection(isl))
mrr = pen.minimum_rotated_rectangle
edges = list(zip(mrr.exterior.coords[:-1], mrr.exterior.coords[1:]))
far_edge = max(edges, key=lambda e: LineString(e).centroid.distance(LineString(bulk2)))
w13 = LineString(far_edge).centroid.distance(LineString(bulk2))
print('Gansevoort peninsula %.2f ha; its outer edge is %.0f m beyond the bulkhead line' % (pen.area / 1e4, w13))
W22 = end_of(S, 'West 22nd Street', 'W'); W23 = end_of(S, 'West 23rd Street', 'W')
a13, b13 = far_edge if far_edge[0][1] < far_edge[1][1] else far_edge[::-1]          # south -> north
l13 = LineString([extend(b13, a13, 900), extend(a13, b13, 1500)])                      # line of 13th Avenue
east13 = Polygon([l13.coords[0], l13.coords[1], offset(l13.coords[1], extend(l13.coords[0], l13.coords[1], 1), -700),
                  offset(l13.coords[0], l13.coords[1], -700)])                         # east (right) side of it
lat_s = A11[1] - 40; lat_n = W22[1]
corr = box(A11[0] - 900, lat_s, A11[0] + 900, lat_n)
strip = east13.intersection(corr).difference(isl.buffer(0.5)).intersection(isl.buffer(260))
strip_all = unary_union([strip, pen]).buffer(3).buffer(-3)
pieces = sorted([g for g in getattr(strip, 'geoms', [strip]) if g.area > 2000], key=lambda g: g.centroid.y)
print('13th Ave strip pieces (ha):', [round(g.area / 1e4, 2) for g in pieces])
T13 = WIKI + 'Thirteenth_Avenue_(Manhattan)'
zone(lambda: R.add('mn_hr_13th_avenue_fill', 'Thirteenth Avenue fill (W 11th St to W 22nd St), including the Gansevoort peninsula', 1837, 1860,
      biggest(strip_all), 'fill', 'precise',
      'Thirteenth Avenue "was built in 1837 on landfill" west of West St / 11th Avenue, from 11th St to about 29th St. The ring is the '
      'made land that is water again today plus the surviving Gansevoort peninsula: east edge today\'s bulkhead, west edge the line of '
      'the peninsula\'s outer face carried north and south. End year estimated (the fill went on for some decades).', T13))
for i, g in enumerate(pieces[:2]):
    zone(lambda g=g, i=i: R.add('mn_hr_13th_avenue_cut_' + ('s', 'n')[i],
      'Thirteenth Avenue fill removed for the ' + ('Gansevoort piers (W 11th St to Gansevoort St)', 'Chelsea Piers (Gansevoort peninsula to W 22nd St)')[i],
      1902, 1910, g, 'excavation', 'precise',
      'The city removed the landfill on which Thirteenth Avenue ran south of 22nd St so that longer piers could be built without '
      'passing the federal pierhead line; the Chelsea Piers opened in 1910. Start year estimated. Same outline as the matching part of '
      'mn_hr_13th_avenue_fill; the Gansevoort peninsula (West Washington Market) stayed.', T13))

# ---------------------------------------------------------------- Hudson shore, coarse
Wa_gv = S.x('Washington Street', 'Gansevoort Street')
T14 = X('10th Avenue', 'West 14th Street'); T23 = X('10th Avenue', 'West 23rd Street'); T59 = X('10th Avenue', 'West 59th Street')
zone(lambda: R.add('mn_hr_chelsea', 'Chelsea waterfront: Washington St / 10th Avenue to the bulkhead, Gansevoort St to W 23rd St', 1825, 1855,
      biggest(seaward([Wa_gv, T14, T23], 700, S.x('8th Avenue', 'West 23rd Street'), isl).difference(pen.buffer(2))), 'fill', 'coarse',
      'The bank was at Washington St at Gansevoort St; Thirteenth Avenue beyond was filled from 1837. Inner line only brackets the '
      'area; dates estimated (no source found that dates the fill between 10th and 11th Avenues).', WIKI + 'Meatpacking_District,_Manhattan'))
zone(lambda: R.add('mn_hr_23_59', 'Hudson shore W 23rd St to W 59th St: 10th Avenue to the bulkhead', 1837, 1880,
      seaward([T23, T59], 900, S.x('8th Avenue', 'West 42nd Street'), isl), 'fill', 'coarse',
      'Includes the Thirteenth Avenue fill of 1837 onward north of 22nd St and the bay at the foot of 42nd St (Great Kill). '
      'Estimated bracket; bulkhead wall 1871-1935.', T13))
E59 = X('West End Avenue', 'West 59th Street'); E72 = X('West End Avenue', 'West 72nd Street')
zone(lambda: R.add('mn_hr_59_72', 'Hudson shore W 59th St to W 72nd St (former 60th Street rail yard, Riverside South)', 1870, 1890,
      seaward([E59, E72], 700, S.x('Amsterdam Avenue', 'West 66th Street'), isl), 'fill', 'coarse',
      'The 57 acres "just south of Riverside Park that had been the Penn Central freight rail yard". Estimated bracket; no source found '
      'that dates the fill.', WIKI + 'Riverside_Park_(Manhattan)'))
rd = [near_on(S, 'Riverside Drive', end_of(S, n, 'W')) for n in
      ['West 72nd Street', 'West 79th Street', 'West 86th Street', 'West 96th Street', 'West 106th Street', 'West 116th Street', 'West 122nd Street']
      if n in S.by]
rd2 = [near_on(S, 'Riverside Drive', end_of(S, n, 'W')) for n in
       ['West 122nd Street', 'West 135th Street', 'West 145th Street', 'West 155th Street'] if n in S.by]
rd3 = [near_on(S, 'Riverside Drive', end_of(S, n, 'W')) for n in
       ['West 155th Street', 'West 165th Street', 'West 181st Street', 'Dyckman Street'] if n in S.by]
print('Riverside Drive anchor points', len(rd), len(rd2), len(rd3))
inl_w = S.x('Broadway', 'West 96th Street')
zone(lambda: R.add('mn_riverside_park_fill', 'Riverside Park fill west of Riverside Drive, W 72nd St to W 122nd St', 1934, 1937,
      seaward(rd, 500, inl_w, isl), 'fill', 'coarse',
      'West Side Improvement: the parkway "was to be built on newly filled land along the shore", approved June 1935, completed 1937, '
      'adding 132 acres to the park and covering the railroad. City-owned underwater land had already been filled in 1911-12 with rock '
      'from the Catskill Aqueduct. The ring runs from Riverside Drive; only the part west of the 1609 shore is made land.',
      WIKI + 'Riverside_Park_(Manhattan)'))
zone(lambda: R.add('mn_hr_122_155', 'Hudson shore W 122nd St to W 155th St (Manhattanville, Riverbank)', 1850, 1937,
      seaward(rd2, 600, S.x('Broadway', 'West 135th Street'), isl), 'fill', 'coarse',
      'Railroad along the water\'s edge, the Manhattanville waterfront, then the parkway fill of the 1930s. Estimated bracket; no source found with dates.',
      WIKI + 'Henry_Hudson_Parkway'))
zone(lambda: R.add('mn_hr_155_dyckman', 'Hudson shore W 155th St to Dyckman St (Fort Washington Park)', 1934, 1937,
      seaward(rd3, 600, S.x('Broadway', 'West 181st Street'), isl), 'fill', 'coarse',
      'Parkway and park fill outside the railroad. Estimated bracket, taken from the years of the Riverside Park parkway fill (approved 1935, '
      'completed 1937); no source found for this reach.', WIKI + 'Riverside_Park_(Manhattan)'))

# ---------------------------------------------------------------- East River north of E 34th St
P = {n: end_of(S, f'East {n} Street', 'E') for n in ['34th', '42nd', '49th', '59th', '96th', '125th']}
F = {n: X('1st Avenue', f'East {n} Street') for n in ['34th', '42nd', '49th']}
S49 = X('2nd Avenue', 'East 49th Street'); S42 = X('2nd Avenue', 'East 42nd Street')
FDR = fdr_segments(S)
fdr_34_49 = FDR[('34th', '42nd')] + FDR[('42nd', '49th')][1:]
fdr_49_96 = FDR[('49th', '96th')]
fdr_96_125 = FDR[('96th', '125th')]
print('FDR 34-49 %.0f m, 49-96 %.0f m, 96-125 %.0f m' % tuple(LineString(x).length for x in (fdr_34_49, fdr_49_96, fdr_96_125)))
inl_e = X('3rd Avenue', 'East 42nd Street')
zone(lambda: R.add('mn_er_34_42_kips_bay', 'Kips Bay: 1st Avenue to the old bulkhead, E 34th to E 42nd St', 1850, 1880,
      band([F['34th'], F['42nd']], FDR[('34th', '42nd')]), 'fill', 'coarse',
      'Kips Bay was an inlet of the East River from about 32nd to 37th St. No source found for when it was filled; estimated bracket.',
      WIKI + 'Kips_Bay,_Manhattan'))
zone(lambda: R.add('mn_er_42_49_turtle_bay', 'Turtle Bay: 2nd Avenue to the old bulkhead, E 42nd to E 49th St', 1850, 1868,
      band([F['42nd'], S42, S49], FDR[('42nd', '49th')]), 'fill', 'coarse',
      'Cove of the East River between 45th and 48th St. "By 1868 the bay had been entirely filled in"; start year estimated.',
      WIKI + 'Turtle_Bay,_Manhattan'))
FD = WIKI + 'FDR_Drive'
zone(lambda: R.add('mn_fdr_34_49', 'East River Drive, E 34th to E 49th St: made land and deck outboard of the old shore', 1940, 1942.4,
      seaward(fdr_34_49, 300, inl_e, isl, back=15), 'fill', 'coarse',
      'Last part of the original drive, opened May 1942. Partly fill, partly deck over the river; start year estimated.', FD))
zone(lambda: R.add('mn_fdr_49_96', 'East River Drive, E 49th to E 96th St: made land and deck outboard of the old shore', 1938, 1940.5,
      seaward(fdr_49_96, 300, X('3rd Avenue', 'East 72nd Street'), isl, back=15), 'fill', 'coarse',
      'Opened June 1940. Much of this shore is rock bluff with the drive on a shelf or in tunnels (Sutton Place, Carl Schurz Park), so '
      'only the part outside the 1609 shore is made land. Start year estimated.', FD))
zone(lambda: R.add('mn_fdr_96_125', 'East River Drive, E 96th to E 125th St: fill outboard of the old bulkhead', 1934, 1936.9,
      seaward(fdr_96_125, 300, X('3rd Avenue', 'East 110th Street'), isl, back=15), 'fill', 'coarse',
      'Section from 125th St south to 92nd St "completed in 1936". Start year estimated.', FD))
V96 = X('5th Avenue', 'East 96th Street'); V110 = X('5th Avenue', 'East 110th Street'); V125 = X('5th Avenue', 'East 125th Street')
zone(lambda: R.add('mn_east_harlem_flats', 'Harlem Creek marsh and the East Harlem flats: 5th Avenue to the East River, E 96th to E 125th St', 1870, 1890,
      band([V96, V110, V125], fdr_96_125), 'pond_fill', 'coarse',
      'Harlem Creek ran into Harlem Marsh, a partly tidal wetland between about 106th and 110th St draining to the East River, later '
      '"buried beneath the city\'s expanding street grid". Dates estimated (1870s-80s, when the grid was built out here); the ring only '
      'brackets the marsh and the shore flats.', WIKI + 'Harlem_Meer'))

# ---------------------------------------------------------------- Harlem River
H155 = end_of(S, 'West 155th Street', 'E'); Hdy = end_of(S, 'Dyckman Street', 'E')
zone(lambda: R.add('mn_harlem_river_125_155', 'Harlem River flats: 5th / 8th Avenue to the river, 125th to 155th St', 1870, 1900,
      seaward([V125, X('5th Avenue', 'East 135th Street'), X('Frederick Douglass Boulevard', 'West 145th Street'), X('Frederick Douglass Boulevard', 'West 155th Street')],
              900, X('Broadway', 'West 145th Street'), isl), 'fill', 'coarse',
      'Low shore and marsh along the Harlem River filled as the grid and the rail yards were built. Estimated bracket; no source found with dates.',
      WIKI + 'Harlem_River'))
zone(lambda: R.add('mn_harlem_river_speedway', 'Harlem River Speedway shelf, W 155th St to Dyckman St', 1894, 1898.5,
      seaward(S.along('Harlem River Drive', near_on(S, 'Harlem River Drive', H155), near_on(S, 'Harlem River Drive', Hdy), bridge=600),
              200, X('Broadway', 'West 181st Street'), isl, back=25), 'fill', 'coarse',
      'The Speedway was built along the riverbank from W 155th St to Dyckman St: construction started 1894, opened July 1898. '
      'Ring = from 25 m inland of today\'s Harlem River Drive to the river.', WIKI + 'Harlem_River_Drive'))
D10 = X('10th Avenue', 'Dyckman Street'); N218 = X('10th Avenue', 'West 218th Street')
zone(lambda: R.add('mn_sherman_creek_flats', 'Sherman Creek and the Inwood flats: 10th Avenue to the Harlem River, Dyckman St to W 218th St', 1900, 1935,
      seaward([D10, X('10th Avenue', 'West 207th Street'), N218], 700, X('Broadway', 'West 207th Street'), isl), 'fill', 'coarse',
      'Tidal inlet (Sherman Creek) and its marsh, now rail yards and housing. Estimated bracket; no source found with dates.',
      WIKI + 'Harlem_River'))

# ---------------------------------------------------------------- Ship canal, Marble Hill
c = duckdb.connect()
lots = c.execute(f"select longitude, latitude from read_csv_auto('{ROOT}/data/raw/nyc/pluto.csv', sample_size=-1, ignore_errors=true) "
                 "where borough='MN' and latitude>40.868 and longitude is not null").fetchall()
mh = [utm(lo, la) for lo, la in lots if not isl.buffer(30).contains(Point(utm(lo, la)))]
from shapely.geometry import MultiPoint
MH = MultiPoint(mh).convex_hull
print('Marble Hill lots', len(mh), 'hull ha %.1f' % (MH.area / 1e4), 'centroid %.5f %.5f' % ll((MH.centroid.x, MH.centroid.y)))
bb = (-73.935, 40.865, -73.900, 40.890)
land_n = land_of(bb); wbox = to_utm(box(*bb)); water_n = wbox.difference(land_n)
SD = WIKI + 'Spuyten_Duyvil_Creek'
canal = water_n.intersection(isl.buffer(190)).intersection(MH.buffer(230))
zone(lambda: R.add('mn_ship_canal_1895', 'Harlem River Ship Canal: the cut between Inwood and Marble Hill', 1888, 1895.46,
      biggest(canal).buffer(15), 'excavation', 'coarse',
      'Upland of Manhattan cut through: construction started January 1888, the cut at Marble Hill opened 17 June 1895 (a 30 ft '
      '"Dyckman canal" had run here since 1817). Ring = today\'s water lying between Manhattan Island and the Marble Hill tax lots, '
      'buffered 15 m; clip to water.', SD))
bx_main = max([g for g in getattr(land_n, 'geoms', [land_n])], key=lambda g: g.intersection(MH).area)
creek = MH.buffer(230).difference(MH.buffer(-25)).intersection(bx_main).difference(isl.buffer(260))
zone(lambda: R.add('mn_marble_hill_creek_bed', 'Old bed of Spuyten Duyvil Creek round Marble Hill', 1913, 1914,
      biggest(creek), 'water_fill', 'coarse',
      'After the canal Marble Hill was an island; "in 1914 the original creekbed was filled in with rock from the excavation of Grand '
      'Central Terminal" (another article says joined to the Bronx in 1913). Ring = a 230 m collar round the hull of the Manhattan tax '
      'lots north of the canal: it brackets the bed (west, north and east of the hill), it is not its outline.', SD))
west_cut = water_n.intersection(isl.buffer(230)).intersection(bx_main.buffer(230)).difference(MH.buffer(260))
west_cut = west_cut.intersection(box(MH.bounds[0] - 1100, MH.bounds[1] - 500, MH.bounds[0] - 150, MH.bounds[3] + 300))
zone(lambda: R.add('mn_spuyten_duyvil_cut_1938', 'Spuyten Duyvil Creek straightened west of Marble Hill', 1937, 1938,
      biggest(west_cut).buffer(15), 'excavation', 'coarse',
      'The western end of the creek was straightened: plans final 1935, "the channel was excavated from 1937 to 1938". The flat north end of '
      'Inwood Hill Park "is on a peninsula that was formerly connected to the Bronx mainland"; the filling of the old loop behind it is not '
      'mapped (no outline on disk, no date found). Ring = today\'s channel '
      'between Inwood Hill Park and the Bronx west of Marble Hill; only the part that was land before 1937 was dug.', SD))

# ---------------------------------------------------------------- Ponds and marshes
CP = WIKI + 'Collect_Pond'
zone(lambda: R.add('mn_collect_pond', 'Collect Pond (Fresh Water Pond) and its margin', 1803, 1811,
      poly(X('Lafayette Street', 'Worth Street'), X('Lafayette Street', 'Walker Street'), X('Baxter Street', 'Walker Street'),
           X('Mulberry Street', 'Bayard Street'), X('Mulberry Street', 'Worth Street')).buffer(100, join_style=2), 'pond_fill', 'coarse',
      'Fresh-water pond of about 48 acres, up to 60 ft deep. The Common Council ordered it filled in 1803; drained through a canal '
      '(1807) and filled with the earth of Bayard\'s Mount; "the landfill was completed in 1811". Ring of streets brackets the pond '
      '(Lafayette - Walker - Baxter - Mulberry - Worth, widened by 100 m); it is not the outline.', CP))
zone(lambda: R.add('mn_lispenard_meadows', 'Lispenard Meadows and the canal along Canal St', 1805, 1819,
      poly(X('Broadway', 'Lispenard Street'), X('Broadway', 'Grand Street'), X('West Broadway', 'Grand Street'), X('Varick Street', 'Spring Street'),
           S.x('Greenwich Street', 'Spring Street'), S.x('Greenwich Street', 'Laight Street'), X('West Broadway', 'Lispenard Street')), 'pond_fill', 'coarse',
      'Salt marsh draining the Collect to the Hudson, drained by the 40 ft ditch that became Canal St (canal dug 1807, "drained by 1813 '
      'or 1815", ditch covered 1819). Start year estimated. Ring of streets brackets the meadows.', WIKI + 'Canal_Street_(Manhattan)'))

# ---------------------------------------------------------------- Reservoirs on Manhattan
wrows = [(n, to_utm(wkb.loads(bytes(g)))) for n, g in con().execute(
    f"select name, ST_AsWKB(geometry) from '{OV}/base_water.parquet' where name in ('Jacqueline Kennedy Onassis Reservoir','Turtle Pond')").fetchall()]
jko = [g for n, g in wrows if n.startswith('Jacqueline')][0]
turtle = min([g for n, g in wrows if n == 'Turtle Pond'], key=lambda g: g.distance(jko))        # the one in Central Park
ws = {'Jacqueline Kennedy Onassis Reservoir': jko, 'Turtle Pond': turtle}
lu = con().execute(f"select name, class, ST_AsWKB(geometry) from '{OV}/region5_land_use.parquet' where name in ('Great Lawn','The Great Lawn')").fetchall()
print('Turtle Pond is %.0f m from the reservoir; Great Lawn polygons: %d' % (turtle.distance(jko), len(lu)))
zone(lambda: R.add('mn_central_park_reservoir', 'Central Park Reservoir (Upper Reservoir, Jacqueline Kennedy Onassis Reservoir)', 1862, 9999,
      ws['Jacqueline Kennedy Onassis Reservoir'], 'reservoir', 'precise',
      'Second Croton reservoir in the park, "completed in 1862"; decommissioned 1993, still holds water. Outline = Overture water.',
      WIKI + 'Jacqueline_Kennedy_Onassis_Reservoir', tol=3.0))
gl = [to_utm(wkb.loads(bytes(g))) for n, k, g in lu if 'Great Lawn' in n]
gl = [g for g in gl if g.distance(turtle) < 500]
if gl and 'Turtle Pond' in ws:
    mrr = unary_union(gl + [ws['Turtle Pond']]).minimum_rotated_rectangle
    cs = list(mrr.exterior.coords); c0 = (mrr.centroid.x, mrr.centroid.y)
    e = max((cs[0], cs[1]), (cs[1], cs[2]), key=lambda s: math.dist(*s))          # long side gives the axis
    ux, uy = (e[1][0] - e[0][0]) / math.dist(*e), (e[1][1] - e[0][1]) / math.dist(*e)
    L, Wd = 1826 * 0.3048 / 2, 836 * 0.3048 / 2                                   # documented size of the basin
    rect = Polygon([(c0[0] + sx * ux * L - sy * uy * Wd, c0[1] + sx * uy * L + sy * ux * Wd) for sx, sy in ((1, 1), (1, -1), (-1, -1), (-1, 1))])
    print('Great Lawn + Turtle Pond rectangle %.1f ha -> basin rectangle %.1f ha' % (mrr.area / 1e4, rect.area / 1e4))
    zone(lambda: R.add('mn_croton_receiving_reservoir', 'Croton receiving reservoir (Yorkville or Lower Reservoir), now the Great Lawn and Turtle Pond', 1842.49, 1930.0,
      rect, 'reservoir', 'coarse',
      'Built 1842, filled from 27 June 1842; decommissioned 1903, "began to be drained in January 1930" and filled in for the Great Lawn. '
      'Ring = a rectangle of the documented size of the basin (1826 x 836 ft, %.1f ha), centred on and aligned with today\'s Great Lawn '
      'and Turtle Pond; the walls were not traced, and the size is quoted from memory of the usual figure (estimated).' % (rect.area / 1e4), WIKI + 'Great_Lawn_and_Turtle_Pond'))
V40 = X('5th Avenue', 'West 40th Street'); V42 = X('5th Avenue', 'West 42nd Street')
zone(lambda: R.add('mn_croton_distributing_reservoir', 'Croton Distributing Reservoir, Fifth Avenue 40th-42nd St (site of the Public Library)', 1842, 1899,
      Polygon([V40, V42, offset(V42, extend(V40, V42, 1), 128), offset(V40, V42, 128)]), 'reservoir', 'coarse',
      'Walled basin of 4 acres on Murray Hill, in service from 1842, "torn down in the 1890s" (demolished 1899). Ring = square on the '
      'Fifth Avenue front between 40th and 42nd St, 128 m deep (4 acres); the walls were not surveyed.', WIKI + 'Croton_Distributing_Reservoir'))
R.save('mn_b')
