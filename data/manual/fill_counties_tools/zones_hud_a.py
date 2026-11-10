"""Hudson County, part A: the Jersey City and Hoboken waterfront.  Rings from Marin Boulevard
(Henderson Street), Grand Street, the municipal outlines and today's shore; dates in the notes."""
from zonelib import *
R = Registry(); WIKI = 'https://en.wikipedia.org/wiki/'
BB = (-74.17, 40.63, -73.96, 40.87)
S, LAND = window('hud', BB)
JCm, HOBm = muni('Jersey City'), muni('Hoboken')
JC, HOB = clip_streets(S, JCm), clip_streets(S, HOBm)
MB = 'Marin Boulevard'
mS, mN = end_of(JC, MB, 'S'), end_of(JC, MB, 'N')
marin = JC.along(MB, mS, mN, bridge=300)
pG, pC = XX(JC, MB, 'Grand Street'), XX(JC, MB, 'Christopher Columbus Drive')
try:
    p6 = XX(JC, MB, '6th Street')
except Exception as e:
    print('6th St:', e); p6 = XX(JC, MB, 'Thomas Gangemi Drive')
W, E = offset(pC, p6, 300), offset(pC, p6, -300)          # reference points west / east of Marin Boulevard
print('Marin Blvd %.0f m; S end %.5f %.5f, N end %.5f %.5f; Grand %.5f %.5f, Columbus %.5f %.5f, 6th %.5f %.5f'
      % ((LineString(marin).length,) + ll(mS) + ll(mN) + ll(pG) + ll(pC) + ll(p6)))

# Hoboken Terminal first: the rings around it keep clear of it
def hoboken_terminal():
    g = any_named('Hoboken Terminal and Yard').buffer(40).intersection(LAND)
    R.add('hud_hoboken_terminal', 'Hoboken Terminal and its yard (Delaware, Lackawanna & Western)', 1860, 1907, g, 'fill', 'coarse',
          'The first terminal opened 14 November 1862 (Morris and Essex Railroad), the second 15 January 1868, the fourth in 1885; '
          '"the rail and ferry terminal buildings were constructed in 1907". The yard and slips stand in the cove between Hoboken and Jersey City. '
          'Start year estimated (two years before the first terminal). Ring = the Overture outline of the terminal and yard + 40 m.',
          WIKI + 'Hoboken_Terminal', tol=3)
run_zone(hoboken_terminal)

def paulus_hook():
    line = [extend(marin[1], marin[0], 300)] + cut(marin, mS, pC)
    g = part_at(strip(line, 0, 1700, W, LAND), offset(pG, pC, -300))
    R.add('hud_paulus_hook', 'Paulus Hook: the island, the marsh behind it and the fill out to the pier line (Columbus Drive to the Morris Canal basin)',
          1804, 1892, g, 'fill', 'coarse',
          '"The first settlement at Paulus Hook was in 1633 when the area was an island at high tide." The Associates of the Jersey Company, chartered '
          '10 November 1804, laid out the town on it; rail service to the Hook began in 1834 and the Pennsylvania Railroad rebuilt its Exchange Place '
          'terminal in 1876 and 1888-1892. Start = the charter; end = the last terminal: both ends are stated events, the progress between them is estimated '
          '(estimated bracket: no source dates the fill itself). Ring = today\'s land east of Marin Boulevard (Henderson St) and south of Columbus Drive; '
          'it contains the natural island.', WIKI + 'Paulus_Hook', tol=3)
run_zone(paulus_hook)

def harsimus():
    seg = cut(marin, pC, p6)
    g1 = strip(seg, 0, 402, W, LAND)
    R.add('hud_harsimus_cove_inner', 'Harsimus Cove, the first quarter mile east of Henderson Street (Marin Boulevard), Columbus Drive to 6th Street',
          1850, 1870, g1, 'fill', 'coarse',
          '"By 1870 much of the estuary flood zone was land-filled for the development of railyards, extending a quarter mile from Henderson Street." '
          'Ring = 402 m (a quarter mile) east of Marin Boulevard. Start year estimated.', WIKI + 'Harsimus', minus=['hud_paulus_hook'], tol=3)
    g2 = part_at(strip(seg, 402, 1700, W, LAND), offset(pC, p6, -700))
    R.add('hud_harsimus_cove_outer', 'Harsimus Cove beyond the first quarter mile: the Pennsylvania Railroad\'s Harsimus Yards',
          1870, 1875, g2, 'fill', 'coarse',
          'The landfilling of the remainder of Harsimus Cove "in the early 1870s" created the Harsimus Yards of the Pennsylvania Railroad '
          '(Jersey City Landmarks Conservancy, Warehouse Historic District); the Pennsylvania took over the line in 1871. End year estimated from "early 1870s". '
          'Ring = today\'s land more than a quarter mile east of Marin Boulevard, Columbus Drive to 6th Street; piers of later date are inside.',
          'https://jclandmarks.org/?p=1950', minus=['hud_paulus_hook', 'hud_harsimus_cove_inner'], tol=3)
run_zone(harsimus)

def long_dock():
    line = cut(marin, p6, mN) + [extend(marin[-2], marin[-1], 250)]
    g = part_at(strip(line, 0, 1700, W, LAND).intersection(JCm), offset(p6, mN, -400))
    R.add('hud_pavonia_long_dock', 'Pavonia: the Long Dock Company\'s fill for the Erie terminal (6th Street to the Hoboken line)', 1856, 1861, g, 'fill', 'coarse',
          'The Erie reached the river through the Long Dock Tunnel, "started in 1856 and opened in 1861"; its Pavonia Terminal, "built on the northern portion '
          'of landfilled Harsimus Cove", "opened in 1861". Both years documented for the works; piers and yard extensions of later years are inside the ring and '
          'not dated separately. Ring = today\'s land east of Marin Boulevard from 6th Street to the city line (Newport).',
          WIKI + 'Pavonia_Terminal', minus=['hud_hoboken_terminal', 'hud_harsimus_cove_inner', 'hud_harsimus_cove_outer'], tol=3)
run_zone(long_dock)

def meadows():
    seg = cut(marin, pG, mN)
    g = strip(seg, 0, 1000, E, LAND).intersection(JCm)
    R.add('hud_harsimus_meadows', 'Downtown Jersey City west of Henderson Street: the salt meadow between Harsimus and Bergen Hill', 1835, 1880, g, 'fill', 'coarse',
          'Harsimus was upland in a tidal marsh ("Crow\'s Marsh"); Van Vorst Township, laid out on it, was annexed by Jersey City in 1851. No source dates the '
          'filling of the meadow: estimated bracket. Ring = 1 km west of Marin Boulevard from Grand Street to the city line; it contains the Harsimus upland and the '
          'foot of Bergen Hill.', WIKI + 'Harsimus', minus=['hud_hoboken_terminal'], tol=4)
run_zone(meadows)

def south_cove():
    line = [extend(marin[1], marin[0], 120)] + cut(marin, mS, pG)
    g = part_at(strip(line, 0, 1000, E, LAND), offset(pG, pC, 400))
    R.add('hud_south_cove', 'South Cove: the Morris Canal basins and Liberty Harbor (Grand Street to the Tidewater Basin)', 1836, 1900, g, 'fill', 'coarse',
          'The Morris Canal was "extended eastward to Jersey City between 1834 and 1836" and ended in basins in South Cove; the Lehigh Valley leased the canal '
          '"which includes the canal basin at South Cove" in 1871. Liberty Harbor "consists primarily of landfill"; "tidal creeks, marshes, and shallow coves '
          '- portions of which were later filled". Start = the canal; end year estimated (estimated bracket). Ring = today\'s land south of Grand Street, '
          'up to 1 km west of Marin Boulevard.', WIKI + 'Liberty_Harbor', minus=['hud_paulus_hook', 'hud_harsimus_meadows'], tol=3)
run_zone(south_cove)

def hoboken():
    g = part_at(HOBm.intersection(LAND), HOB.x('Washington Street', '6th Street'))
    R.add('hud_hoboken_meadows', 'Hoboken: the island round Castle Point, the Hoboken Meadows west of it and the river front', 1820, 1910, g, 'fill', 'coarse',
          '"In the 1700s, Hoboken was an island"; "the island, the elevated area around Castle Point, comprised about 25 percent of Hoboken\'s current land mass. '
          'The remainder of Hoboken was a wetland, a salt marsh - The Hoboken Meadows"; "continued dumping of fill into the Hoboken Meadows allowed the city to '
          'eventually expand west to the Palisades and north to 16th Street" (Fund for a Better Waterfront on the Hoboken Historical Museum\'s exhibition). '
          '"In the 1820s, the Stevens family began to drain the swamp and fill nearby marshes" (Wikipedia, Elysian Fields). Start = 1820s; end year estimated '
          '(the west side was built up at the turn of the 20th century). Ring = the whole city on today\'s land; the natural island is inside.',
          'https://betterwaterfront.org/in-the-1700s-hoboken-was-an-island-in-2012-during-superstorm-sandy-75-of-hoboken-was-again-under-water/',
          minus=['hud_hoboken_terminal'], tol=4)
run_zone(hoboken)
R.save('hud_a')
