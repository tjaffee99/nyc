"""Manhattan A: East River bands (Whitehall -> E 34th St), the Battery, Hudson bands up to
Gansevoort St, Battery Park City.  Lines are street centre lines from Overture; see fill_README."""
from zonelib import *

S = mn(); isl = S.island; R = Registry(); X = S.x
WIKI = 'https://en.wikipedia.org/wiki/'
LR = WIKI + 'Land_reclamation_in_Lower_Manhattan'
BPCA = 'https://media.bpca.ny.gov/wp-content/uploads/2024/08/06043742/Appendix-D-Historic-and-Cultural-Resources.pdf'
ESCR = 'https://www.nyc.gov/assets/escr/downloads/pdf/FEIS/ESCR-EIS-Chapter-5.4-Historic-and-Cultural-Resources.pdf'


def halfplane(a, b, side, far=6000.0):
    """Big polygon on the LEFT (side=+1) or RIGHT (-1) of the line a -> b."""
    a2, b2 = extend(b, a, far), extend(a, b, far)
    return Polygon([a2, b2, offset(a2, b2, side * far) if False else offset(b2, extend(a2, b2, 1), side * far),
                    offset(a2, b2, side * far)])

# ---------------------------------------------------------------- East River, Whitehall -> Dover
P_st = X('Pearl Street', 'State Street'); P_dv = X('Pearl Street', 'Dover Street')
W_wh = X('Water Street', 'Whitehall Street'); W_dv = X('Water Street', 'Dover Street')
F_os = X('Front Street', 'Old Slip'); F_dv = X('Front Street', 'Dover Street')
S_wh = X('South Street', 'Whitehall Street'); S_dv = X('South Street', 'Dover Street')
W_os = X('Water Street', 'Old Slip')
pearl = S.along('Pearl Street', P_st, P_dv, bridge=150)
water = S.along('Water Street', W_wh, W_dv, bridge=150)
# today's Pearl St is bent to meet Water St at Fulton St (1970s widening): drop that spike, keep the old straight line
pearl = [p for p in pearl if LineString(water).distance(Point(p)) > 30]
state_s = S.along('State Street', W_wh, P_st, bridge=150)
front = S.along('Front Street', F_os, F_dv, bridge=200)
south = S.along('South Street', S_wh, S_dv, bridge=200)
# Front St is demapped south-west of Old Slip: carry it on parallel to Water St at the same spacing
d_wf = math.dist(W_os, F_os)
water_sw = S.along('Water Street', W_wh, W_os, bridge=150)
front_sw = line_offset(water_sw, d_wf, P_dv)
front_full = front_sw[:-1] + front
print('Water-Front spacing at Old Slip %.0f m' % d_wf)

R.add('mn_er_1_pearl_water', 'East River band 1: Pearl St to Water St (State St to Dover St)', 1686, 1730,
      poly(pearl, list(reversed(water)), state_s), 'fill', 'precise',
      'Inner edge Pearl St = the shoreline before fill (it approximates the 1609 high-water line; where the mapped '
      '1609 shore differs, that wins). Water lots between high and low water were sold under the Dongan Charter of '
      '1686 (first grant on the Fraunces Tavern block 19 Nov 1686); the waterfront had moved to Water St by 1730. '
      'Start and end documented; progress inside the span is not.', LR)
R.add('mn_er_2_water_front', 'East River band 2: Water St to Front St (Whitehall St to Dover St)', 1731, 1788,
      band(water, front_full), 'fill', 'precise',
      'Water lots to 400 ft beyond low water came with the Montgomerie Charter (1731); waterfront at Front St "in 1780"; '
      'the slips between Water and Front St at Burling/Beekman Slip were filled by 1788 (Schermerhorn Row). Front St is '
      'demapped south-west of Old Slip: there the outer line is Water St offset by the Water-Front spacing at Old Slip '
      '(estimated line).', LR)
e3 = band(front_full, south).union(seaward(south, 80, P_dv, isl)).intersection(isl)
R.add('mn_er_3_front_south', 'East River band 3: Front St to South St and the bulkhead (Whitehall St to Dover St)', 1798, 1815,
      e3, 'fill', 'precise',
      'The city began to grade South St in 1798; South St "created by 1810"; at Schermerhorn Row the shore did not reach '
      'South St until the 1810s. Outer edge = today\'s bulkhead (Overture water, at most 80 m beyond the South St centre line); the few metres outboard of old South St '
      'belong to the Department of Docks bulkhead wall of 1871 onward and are not split off.',
      WIKI + 'Front_Street_(Manhattan)')

# ---------------------------------------------------------------- Two Bridges, Dover -> Corlears Hook
C_ct = X('Cherry Street', 'Catherine Street'); C_jk = X('Cherry Street', 'Jackson Street')
W_jk = X('Water Street', 'Jackson Street'); S_jk = X('South Street', 'Jackson Street')
cherry = [P_dv] + S.along('Cherry Street', C_ct, C_jk, bridge=700)
water2 = S.along('Water Street', W_dv, W_jk, bridge=900)
south2 = S.along('South Street', S_dv, S_jk, bridge=250)
R.add('mn_er_4_cherry_water', 'Two Bridges: Cherry St to Water St (Dover St to Jackson St)', 1780, 1810,
      band(cherry, water2), 'fill', 'coarse',
      'The pre-fill shore "generally ran along Pearl and Cherry streets"; fill here began at the end of the 18th century '
      '(ESCR Phase 1A). Dates are an estimated bracket, not a documented progression; Cherry St is demapped between '
      'Dover and Catherine St (straight line used).', LR)
t2 = band(water2, south2).union(seaward(south2, 90, C_ct, isl)).intersection(isl)
R.add('mn_er_5_water_south_two_bridges', 'Two Bridges: Water St to South St and the bulkhead (Dover St to Jackson St)', 1800, 1850,
      t2, 'fill', 'precise',
      'South St created by 1810 at its lower end; between Montgomery and Rivington St the strip along the river was '
      'filled "at various times between the 1810s and about 1850" (ESCR Phase 1A). Estimated bracket.', ESCR, minus=['mn_er_3_front_south'])

# ---------------------------------------------------------------- Corlears Hook -> E 14th St
P14 = end_of(S, 'East 14th Street', 'E')
FDR = fdr_segments(S)
fdr1 = FDR[('Jackson', '14th')]
print('FDR Jackson-14th %.0f m' % LineString(fdr1).length)
A1_14 = X('1st Avenue', 'East 14th Street')
AvD_14 = LineString([end_of(S, 'Avenue D', 'S'), extend(end_of(S, 'Avenue D', 'S'), end_of(S, 'Avenue D', 'N'), 500)]).intersection(
    LineString([A1_14, extend(A1_14, fdr1[-1], 300)]))
AvD_14 = (AvD_14.x, AvD_14.y)              # Avenue D carried north to the line of E 14th St
inner1 = [C_jk, end_of(S, 'Jackson Street', 'N'), end_of(S, 'Columbia Street', 'S'), end_of(S, 'Columbia Street', 'N'),
          end_of(S, 'Avenue D', 'S'), AvD_14]
R.add('mn_er_corlears_14th', 'Lower East Side waterfront: Columbia St / Avenue D to the old bulkhead (FDR Drive), Corlears Hook to E 14th St',
      1810, 1850, band(inner1, fdr1), 'fill', 'coarse',
      'Whole strip was under the East River and was filled "at various times between the 1810s and about 1850"; the '
      'corner at Corlears St / Water St (East River Park amphitheatre) only in the 1870s-80s (not split off). Inner line '
      'Jackson St - Columbia St - Avenue D only brackets the area. North of Rivington St the same bracket is assumed (estimated).', ESCR)
R.add('mn_east_river_park', 'East River Park fill outboard of the old bulkhead (Jackson St to E 14th St)', 1936, 1939.57,
      seaward(fdr1, 450, X('1st Avenue', 'East Houston Street'), isl), 'fill', 'precise',
      'Between the historic bulkhead line and the present bulkhead "landfilled in the 20th century in conjunction with '
      'the creation of East River Park"; present bulkhead 1930s; park opened 27 July 1939. Start year estimated. '
      'Inner edge = FDR Drive centre line standing for the old bulkhead.', ESCR, minus=['mn_er_5_water_south_two_bridges'])
A1_h = X('1st Avenue', 'East Houston Street')
R.add('mn_stuyvesant_meadows', 'Stuyvesant salt meadows (1st Avenue to Avenue D, Houston St to E 14th St)', 1820, 1845,
      poly(A1_h, A1_14, AvD_14, end_of(S, 'Avenue D', 'S')), 'pond_fill', 'coarse',
      '"Most of present-day Alphabet City was a salt marsh" (Tompkins Square Park stands on it). The debate about grading and draining '
      'its streets "went round and round for over a decade, even as filling proceeded" (committee of 1823); in 1832 "no amount of fill '
      'seemed to stem periodic flooding". Ring only brackets the marsh; both years estimated from those statements.', WIKI + 'Alphabet_City,_Manhattan')

# ---------------------------------------------------------------- E 14th -> E 34th
P23 = end_of(S, 'East 23rd Street', 'E'); P34 = end_of(S, 'East 34th Street', 'E')
fdr2 = FDR[('14th', '23rd')]; fdr3 = FDR[('23rd', '34th')]
print('FDR 14-23 %.0f m, 23-34 %.0f m' % (LineString(fdr2).length, LineString(fdr3).length))
A1_23 = X('1st Avenue', 'East 23rd Street'); A1_34 = X('1st Avenue', 'East 34th Street')
R.add('mn_er_stuyvesant_cove', 'Stuyvesant Cove / Gas House district: 1st Avenue to the old bulkhead, E 14th to E 23rd St', 1830, 1880,
      band([A1_14, A1_23], fdr2), 'fill', 'coarse',
      'Cove of the East River north of the meadows, later the Gas House district. Estimated bracket (no source found with dates for '
      'these blocks; the blocks just north were filled from the late 1830s through the second half of the 19th century).', ESCR)
R.add('mn_er_23_34', 'Bellevue waterfront: 1st Avenue to the old bulkhead, E 23rd to E 34th St', 1835, 1900,
      band([A1_23, A1_34], fdr3), 'fill', 'coarse',
      'E 23rd and E 25th St began as piers in the late 1830s, E 24th in the 1870s; the blocks were filled in stages through '
      'the second half of the 19th century, the block E 24th-25th (Asser Levy) only in the 1890s. Documented bracket.', ESCR)
R.add('mn_fdr_14_23', 'East River Drive fill outboard of the old bulkhead, E 14th to E 23rd St', 1938, 1940.4,
      seaward(fdr2, 300, A1_14, isl), 'fill', 'precise',
      'Land east of the drive (Stuyvesant Cove Park, Con Edison pier side). The drive opened from 12th to 18th St in 1939 and '
      'was continuous from Montgomery to 30th St in May 1940; the area E 23rd-25th was "landfilled between the 1830s and the 1940s". '
      'Start year estimated.', WIKI + 'FDR_Drive', minus=['mn_east_river_park'])
R.add('mn_bristol_basin', 'Bristol Basin: East River Drive fill, E 23rd to E 34th St', 1940, 1941.8,
      seaward(fdr3, 300, A1_23, isl, back=20), 'fill', 'precise',
      'This section of the drive was built on rubble from bombed Bristol, brought back as ballast by ships returning from '
      'England; the 23rd-34th St section was completed in October 1941 (plaque dedicated 29 June 1942). Start year estimated. Inner edge 20 m west of the drive centre line.',
      WIKI + 'FDR_Drive', minus=['mn_fdr_14_23'])

# ---------------------------------------------------------------- Hudson bands, Battery Place -> Gansevoort St
G_bp = X('Greenwich Street', 'Battery Place'); G_ch = X('Greenwich Street', 'Chambers Street'); G_gv = X('Greenwich Street', 'Gansevoort Street')
Wa_bp = X('Washington Street', 'Battery Place'); Wa_gv = X('Washington Street', 'Gansevoort Street')
We_ch = X('West Street', 'Chambers Street')
greenwich = S.along('Greenwich Street', G_bp, G_gv, bridge=400)
washington = S.along('Washington Street', Wa_bp, Wa_gv, bridge=1200)
# south of Rector St the mapped "Washington Street" wanders round the Battery tunnel plaza: use the straight street line there
Wa_re = X('Washington Street', 'Rector Street')
k_re = min(range(len(washington)), key=lambda i: math.dist(washington[i], Wa_re))
washington = [Wa_bp] + washington[k_re:]
nb = pickle.load(open(os.path.join(INTERIM, 'west_st_nb.pkl'), 'rb'))     # northbound carriageway of West St
inland = G_ch
west_w = line_offset(nb, 10.7, inland)       # west side of the 70 ft street of 1836
bulk = line_offset(nb, 62.0, inland)         # Department of Docks bulkhead (measured: today's wall is 61-63 m out)
south_of_chambers = halfplane(extend(We_ch, G_ch, 300), extend(G_ch, We_ch, 900), 1)
h1 = band(greenwich, washington)
R.add('mn_hr_1_greenwich_washington', 'Hudson band 1: Greenwich St to Washington St (Battery Place to Chambers St)', 1739, 1797,
      h1.intersection(south_of_chambers), 'fill', 'precise',
      'High-water mark of the 1873 Department of Docks map lay about Greenwich St between the Battery and Chambers St, low '
      'water east of Washington St (it approximates the 1609 line; where the mapped 1609 shore differs, that wins). A ship '
      'of the 1770s-80s found at the World Trade Center was in the fill by the 1790s. Start year estimated (water lots '
      'after the Montgomerie Charter); end = the 1797 Taylor-Roberts plan.', BPCA)
R.add('mn_hr_1n_greenwich_washington', 'Hudson band 1 north: Greenwich St to Washington St (Chambers St to Gansevoort St)', 1760, 1800,
      h1.difference(south_of_chambers), 'fill', 'coarse',
      'North of Chambers St fast land reached west of Greenwich St in places (Vesey to North Moore St) and the bank was at '
      'Washington St at Gansevoort St, so only part of this band is made land: intersect with the 1609 shore. Dates estimated; '
      'the 1797 and 1808 plans show the shore near Washington St at North Moore St.', BPCA)
R.add('mn_hr_2_washington_west', 'Hudson band 2: Washington St to West St (Battery Place to Gansevoort St)', 1795, 1836,
      band(washington, west_w), 'fill', 'precise',
      'Landfilling "intensified at the turn of the 19th century"; water lots at North Moore / Harrison / Jay St granted 1805-07 '
      'and not yet filled on the 1808 plan; the bed of West St "largely filled" by the 1836 Colton map. Outer edge = west side of '
      'the 70 ft West St (northbound carriageway centre line + 10.7 m). Washington St is closed between Barclay and Hubert St '
      '(straight line used).', BPCA)
R.add('mn_hr_3_west_bulkhead', 'Hudson band 3: West St to the Department of Docks bulkhead (Battery Place to Gansevoort St)', 1871, 1903,
      band(west_w, bulk).intersection(isl), 'fill', 'precise',
      'Bulkhead line of 1871, 250 ft west of the line of West St; the masonry bulkhead wall and the marginal street behind it were '
      'built 1871-1935 over the whole Hudson front, here c.1890s-1903. Measured on the data: today\'s wall is 61-63 m west of the '
      'northbound carriageway from Tribeca to Gansevoort St.', BPCA)
bpc = band(bulk, line_offset(nb, 520, inland)).intersection(isl).buffer(-4).buffer(4)
R.add('mn_battery_park_city', 'Battery Park City', 1967, 1976.5, bpc, 'fill', 'precise',
      'Fill between the 1871 bulkhead and the pierhead line: the southern part from the World Trade Center excavation '
      '(from 1966-68), the rest with dredged sand and other spoil; "landfill construction was finished" July 1976. '
      'Start year estimated from the WTC excavation; the south-to-north order is not split.', WIKI + 'Battery_Park_City')

# ---------------------------------------------------------------- The Battery
St_bp = X('State Street', 'Battery Place'); A = X('West Street', 'Battery Place')
state_n = S.along('State Street', W_wh, St_bp, bridge=150)
A_w = extend(St_bp, A, 420); S_ext = extend(W_wh, S_wh, 350)
batt = poly(state_n, A, A_w, (A_w[0], A_w[1] - 950), (S_ext[0] + 60, A_w[1] - 950), S_ext, S_wh).buffer(0).intersection(isl)
batt = biggest(batt.difference(bpc.buffer(1)))
# the strip of Battery Place itself, between the south ends of the Hudson bands and the park
patch = LineString([G_bp, A, A_w]).buffer(45, cap_style=2).intersection(isl)
for zid in ('mn_hr_1_greenwich_washington', 'mn_hr_2_washington_west', 'mn_hr_3_west_bulkhead', 'mn_battery_park_city'):
    patch = patch.difference(R.geom[zid].buffer(0.3))
batt = biggest(unary_union([batt, patch.buffer(0.5)]))
core = LineString(state_n + [S_wh])
lo, hi = 5.0, 400.0
for _ in range(40):
    mid = (lo + hi) / 2
    if batt.intersection(core.buffer(mid)).area > 4.05e4: hi = mid
    else: lo = mid
early = batt.intersection(core.buffer(hi))
print('early Battery: within %.0f m of State St / Whitehall St' % hi)
R.add('mn_battery_early', 'The Battery before 1855 (about 10 acres next to State St and Whitehall St)', 1683, 1826,
      early, 'fill', 'coarse',
      'State St approximates the original waterline. Earth platforms were built off the tip in 1683 and 1735, the rubble of Fort '
      'George was added after 1788, and by the 1820s the park was about 10 acres. The ring is the 10 acres of today\'s Battery '
      'nearest State St / Whitehall St (estimated outline, real area).', LR)
R.add('mn_battery_1855', 'Battery extension that joined Castle Garden\'s island', 1855, 1870,
      batt.difference(early.buffer(0.5)), 'fill', 'precise',
      'Castle Clinton (West Battery, 1808-11) stood on an artificial island 200 ft offshore. The park was enlarged with spoil '
      'from street widening "starting from 1855", and about 1869 the island was joined to Manhattan; by 1870 the enlarged park was complete enough to need "improvement" '
      '(end year estimated). Outer edge = today\'s sea wall; inner edge is the estimated limit of the earlier Battery.',
      WIKI + 'The_Battery_(Manhattan)')
R.save('mn_a')
