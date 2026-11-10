"""Bergen, Essex, Union and Passaic counties: the dated landfills of the Meadowlands, the Sports Complex,
Teterboro and Newark airports, Port Newark - Elizabeth, Overpeck, and the reservoirs."""
from zonelib import *
R = Registry(); WIKI = 'https://en.wikipedia.org/wiki/'; MERI = 'https://meri.njmeadowlands.gov/mesic/sites/existingpotential-remediation-sites/'
UH = 'https://www.urbanhabitats.org/v02n01/3centuries_full.html'

# ---------------------------------------------------------------- Bergen
def sports_complex():
    box = (-74.11, 40.79, -74.05, 40.83)
    pts = [p for pat in ('%MetLife Stadium%', '%Meadowlands Arena%', '%Izod Center%', '%American Dream%', '%Meadowlands Racetrack%', '%Meadowlands Racing%', '%Quest Diagnostics Training%')
           for _, p in bldg(pat, box)]
    print('   sports complex anchors:', len(pts))
    from shapely.geometry import MultiPoint
    g = MultiPoint(pts).convex_hull.buffer(450) if len(pts) >= 3 else any_named('MetLife Stadium').buffer(800)
    R.add('ber_meadowlands_sports_complex', 'Meadowlands Sports Complex (East Rutherford)', 1972.88, 1976.77, g, 'fill', 'coarse',
          '"Ground was broken on Giants Stadium and the Meadowlands Racetrack on November 19, 1972"; "Giants Stadium opened on October 10, 1976" (the racetrack '
          '1 September 1976, the arena 2 July 1981). Both dates documented. Ring = the hull of the stadium, arena, racetrack and mall footprints + 450 m: an '
          'estimated outline, it contains marsh that was never filled.', WIKI + 'Meadowlands_Sports_Complex', tol=8)
run_zone(sports_complex)

def teterboro():
    g = any_named('Teterboro Airport')
    R.add('ber_teterboro_airport', 'Teterboro Airport', 1917, 1949, g, 'fill', 'coarse',
          'Walter C. Teter "acquired the property in 1917, and North American Aviation operated a manufacturing plant on the site during World War I. The first '
          'flight from the present airport site was made in 1919"; the Port Authority bought the airport on 2 April 1949. The field lies on the Hackensack meadow at '
          '8.4 ft. Start documented; end year estimated (the purchase stands for the runway extensions, which no source at hand dates). Ring = the airport outline.',
          WIKI + 'Teterboro_Airport', tol=6)
run_zone(teterboro)

def overpeck():
    u = unary_union([named('Overpeck Park', all_parts=True), named('Overpeck Golf Course')])
    R.add('ber_overpeck_park', 'Overpeck County Park: the landfill on Overpeck Creek', 1954, 2010, u.convex_hull, 'fill', 'coarse',
          '"During the 1950s, tide gates were installed on the creek that largely cut off the tidal flow"; from 1954 the towns gave the meadow for a county park; '
          'the undeveloped areas "were used as dumping sites for garbage"; "the project began in 2003 and the expanded park opened in 2010" on the closed landfill. '
          'Both years documented; the progress between them is not. Ring = the hull of the park and golf course outlines; it spans the creek.',
          WIKI + 'Overpeck_County_Park', tol=8)
run_zone(overpeck)

def bergen_landfills():
    R.add('ber_kingsland_landfill', 'Kingsland Landfill (Lyndhurst / North Arlington)', 1957, 1988, named('Kingsland Landfill', table='base_land'), 'fill', 'coarse',
          '"Size: 150 acres ... Landfill closed in 1988." End documented; start year estimated (dumping in the Meadowlands grew quickly after 1957, Marshall 2004). '
          'Ring = the Overture outline named Kingsland Landfill (136 ha: larger than the 150 acres, it takes in part of the 1-E landfill, which has no date).',
          MERI + 'kingsland-landfill-2/', tol=6)
    R.add('ber_avon_landfill', 'Avon Landfill (Lyndhurst)', 1957, 1980, named('Avon Landfill'), 'fill', 'coarse',
          '"Size: 91 acres ... Closed to operations in 1980." End documented; start year estimated. Ring = the Overture outline.', MERI + 'avon-landfill-2/', tol=5,
          minus=['ber_kingsland_landfill'])
    R.add('ber_erie_landfill', 'Erie Landfill (North Arlington)', 1950, 1969, named('Erie Landfill', table='base_land'), 'fill', 'coarse',
          '"Size: 38 acres ... The Erie Landfill was closed to operations prior to 1970." End = "prior to 1970"; start year estimated. Ring = the Overture outline.',
          MERI + 'erie-landfill-2/', tol=5, minus=['ber_kingsland_landfill', 'ber_avon_landfill'])
run_zone(bergen_landfills)

run_zone(lambda: add_reservoir(R, 'ber_oradell_reservoir', 'Oradell Reservoir', 'Oradell Reservoir', 1923,
    '"Construction on the Oradell Reservoir began in 1901 by the dredging of a mill pond. The mill pond dam was replaced in 1911 by a low timber-crib dam ... '
    'In 1921, a 22 ft high concrete Oradell Reservoir Dam was built ... The reservoir was completed in 1923." Start = completion; a smaller pond stood here from 1901.',
    WIKI + 'Oradell_Reservoir', tol=8))
run_zone(lambda: add_reservoir(R, 'ber_lake_tappan', 'Lake Tappan (Bergen and Rockland counties)', 'Lake Tappan', 1967,
    '"The reservoir was formed in 1967", impounded by the Tappan Dam on the Hackensack River, straddling the state line.', WIKI + 'Lake_Tappan', tol=8))
run_zone(lambda: add_reservoir(R, 'ber_woodcliff_lake', 'Woodcliff Lake reservoir', 'Woodcliff Lake Resevoir', 1905,
    'The borough was renamed Woodcliff Lake on 1 March 1910, "after the creation of the reservoir". Start year estimated: the article only bounds it '
    '(before March 1910); the usual date of about 1903-05 was not verified.', WIKI + 'Woodcliff_Lake,_New_Jersey', tol=6))

# ---------------------------------------------------------------- Essex / Union
def ports():
    pg = named('Port Newark-Elizabeth'); NWK, ELZ = muni('Newark'), muni('Elizabeth')
    a, b = biggest(pg.intersection(NWK)), biggest(pg.intersection(ELZ))
    print('   port outline %.0f ha: Newark %.0f ha, Elizabeth %.0f ha' % (pg.area / 1e4, a.area / 1e4, b.area / 1e4))
    R.add('ess_port_newark', 'Port Newark', 1914, 1930, a, 'fill', 'coarse',
          '"The city of Newark started constructing Port Newark in 1914, dredging a ship channel one mile long from Newark Bay into the Meadowlands. The city mixed '
          'the dredged fill with garbage and ashes and dumped it on the wetlands on the north side of the channel. Additional portions of the Newark Meadows were '
          'similarly reclaimed during the 1920s for the expansion of Port Newark" (Marshall 2004). Start documented; end year estimated from "during the 1920s"; the '
          'Port Authority (from 1948) extended the port southward (not dated separately). Ring = the Newark part of the Overture outline Port Newark-Elizabeth.', UH, tol=8)
    R.add('uni_port_elizabeth', 'Elizabeth Marine Terminal (Port Elizabeth)', 1958, 1974, b, 'fill', 'coarse',
          '"In 1958, the port authority dredged another shipping channel" (the Elizabeth Channel); the first terminal on it was Sea-Land\'s. "Between 1914 and 1974, '
          'the Newark Meadows portion of the Meadowlands was totally filled in and covered by the Port Newark/Elizabeth marine terminal, Newark ... Airport, and the '
          'New Jersey Turnpike" (Marshall 2004). Start documented; end = the end of that bracket. Ring = the Elizabeth part of the Overture outline.',
          WIKI + 'Port_Newark%E2%80%93Elizabeth_Marine_Terminal', tol=8)
    ap = any_named('Newark Liberty International Airport')
    R.add('ess_newark_airport', 'Newark Liberty International Airport', 1928, 1974, ap, 'fill', 'coarse',
          '"The City of Newark started building the airport in 1928 on 68 acre of marshland"; "a land reclamation project to create 68 acre of level ground, 6 ft '
          'above sea level"; opened 1 October 1928; the Port Authority took over in 1948 and enlarged it; the Newark Meadows were "totally filled in" between 1914 '
          'and 1974 (Marshall 2004). Start documented; end = the end of that bracket; the stages between are not dated. Ring = the airport outline (797 ha).',
          WIKI + 'Newark_Liberty_International_Airport', tol=8, minus=['ess_port_newark', 'uni_port_elizabeth'])
run_zone(ports)

def park_lakes():
    wq = water_in(named('Weequahic Park'))[0]
    add_reservoir(R, 'ess_weequahic_lake', 'Weequahic Lake', None, 1903,
        'The reservation took in "265 acres of saltwater wetland"; "in 1903, a dam was built across the northern end of the lake to arrest the flow of Bound Creek '
        'from Newark Bay, causing the water level to rise and creating the depth now seen in the lake". Before 1903 the basin was tidal marsh and creek.',
        WIKI + 'Weequahic_Park', close=0, tol=4, geom=wq)
    bb = water_in(named('Branch Brook Park'))[0]
    add_reservoir(R, 'ess_branch_brook_lake', 'Branch Brook Park lake', None, 1898,
        '"In 1898, a public appropriation financed the conversion of the swamp into a landscaped lake." Largest water outline inside the park.',
        WIKI + 'Branch_Brook_Park', close=0, tol=3, geom=bb)
run_zone(park_lakes)
run_zone(lambda: add_reservoir(R, 'uni_lake_surprise', 'Lake Surprise (Watchung Reservation)', 'Lake Surprise', 1845,
    '"The lake was created in 1845 for David Felt\'s papermill."', WIKI + 'Lake_Surprise_(Watchung_Reservation)', close=0, tol=4))

# ---------------------------------------------------------------- Passaic
run_zone(lambda: add_reservoir(R, 'pas_wanaque_reservoir', 'Wanaque Reservoir', 'Wanaque Reservior', 1928,
    '"The reservoir came into being in 1928 by the construction of the Raymond Dam along the river in Wanaque. After eight years of construction, water was '
    'delivered to customers for the first time in 1930."', WIKI + 'Wanaque_Reservoir', tol=10))
run_zone(lambda: add_reservoir(R, 'pas_monksville_reservoir', 'Monksville Reservoir', 'Monksville Reservoir', 1987.6,
    '"Construction of the reservoir was started in 1985. Building of the actual dam started in March 1987 and was completed in August 1987. The reservoir filled '
    'quickly and was full by October 1987."', WIKI + 'Monksville_Reservoir', tol=8))
run_zone(lambda: add_reservoir(R, 'pas_pompton_lake', 'Pompton Lake', 'Pompton Lake', 1908,
    '"The lake was formed by the construction of the Pompton Lake Dam in 1908 after a prior wooden dam was destroyed by a flood in 1903": a mill pond stood here '
    'before 1903 (not drawn).', WIKI + 'Pompton_Lake', tol=6))
run_zone(lambda: add_reservoir(R, 'pas_greenwood_lake', 'Greenwood Lake (New Jersey and New York): the lake as raised by the dam of 1837', 'Greenwood Lake', 1837,
    '"In 1837, the lake was again dammed, but at the location of the current dam, this time by the Morris Canal & Banking Company to supply water to the Pompton '
    'Feeder of the Morris Canal." A natural lake (Long Pond), dammed before, lay in the valley: only the margins and the ends were flooded in 1837. The terrain '
    'stage must keep water inside this ring before 1837 as well.', WIKI + 'Greenwood_Lake', tol=10))
run_zone(lambda: add_reservoir(R, 'pas_packanack_lake', 'Packanack Lake (Wayne)', 'Packanack Lake', 1928,
    '"A valley of marshland that in 1928 would be cleared of trees and brush; blocked at the south with an earth and clay dam to form Packanack Lake."',
    WIKI + 'Packanack_Lake,_New_Jersey', close=0, tol=5))
run_zone(lambda: add_reservoir(R, 'pas_charlotteburg_reservoir', 'Charlotteburg Reservoir (Passaic and Morris counties)', 'Charlotteburg Reservoir', 1957,
    'City of Newark, Department of Water and Sewer Utilities: "In 1957 the City of Newark constructed the Charlotteburg reservoir/dam and the Pequannock Screen '
    'Building, located immediately downstream from the reservoir intake." The Pequannock River here is the county line.',
    'https://water.newarknj.gov/completed-projects/valve-replacement-at-the-pequannock-screen-building-9b8h8', tol=6))
run_zone(lambda: add_reservoir(R, 'ess_orange_reservoir', 'Orange Reservoir (South Mountain Reservation)', 'Orange Reservoir', 1885,
    '"In the 1880s, Orange bought the land and built dams, creating the Orange Reservoir and Campbell\'s Pond in Millburn." Start year estimated inside "the 1880s".',
    'https://thefouroranges.com/orange-and-west-orange-nearly-merged-over-this-reservoir', close=0, tol=4))
R.save('nj')
