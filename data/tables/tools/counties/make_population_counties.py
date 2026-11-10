"""Writes data/tables/population_counties.csv: the eight counties around the city, PRESENT areas.

Figures were read off the cited sources (see the notes written into each row):
  FORSTALL  Census Bureau 1996, Population of States and Counties of the United States 1790-1990
            (county tables; New York notes 3 and 11 for the present areas of Westchester and Nassau)
  NJC       New Jersey Department of State 1906, Compendium of Censuses 1726-1905 (township returns
            1810-1860; read from the page images, each year's townships add up to the county total)
  CPG       Census Bureau 1909, A Century of Population Growth (colonial censuses, tables 88-102)
  SMITH     Samuel Smith 1765, History of the Colony of Nova-Caesaria (the 1682 account of East Jersey)
Boundary changes are handled here, not ignored: see places_counties_README.md / the final report.
"""
import csv

OUT = '/home/user/nyc/data/tables/population_counties.csv'
FORSTALL = 'https://www2.census.gov/library/publications/decennial/1990/population-of-states-and-counties-us-1790-1990/population-of-states-and-counties-of-the-united-states-1790-1990.pdf'
NJC = 'https://archive.org/details/101270621.nlm.nih.gov'
CPG = 'https://archive.org/details/centuryofpopulat00unit'
SMITH = 'https://archive.org/details/historyofcolonyo00smit'
C1790 = 'https://www.census.gov/library/publications/1793/dec/number-of-persons.html'
C2000 = 'https://www2.census.gov/programs-surveys/popest/datasets/2000-2009/counties/totals/co-est2009-alldata.csv'
C2010 = 'https://www2.census.gov/programs-surveys/popest/datasets/2010-2019/counties/totals/co-est2019-alldata.csv'
C2020 = 'https://www.census.gov/quickfacts/fact/table/bergencountynewjersey,essexcountynewjersey,hudsoncountynewjersey,passaiccountynewjersey,unioncountynewjersey,westchestercountynewyork/POP010220'
C2020B = 'https://www.census.gov/quickfacts/fact/table/nassaucountynewyork,rocklandcountynewyork/POP010220'
EST = 'https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/counties/totals/co-est2025-alldata.csv'
HEMP = 'https://en.wikipedia.org/wiki/Hempstead_(village),_New_York'
AREAS = ('hudson', 'bergen', 'essex', 'union', 'passaic', 'westchester', 'nassau', 'rockland')
rows = []
def add(year, area, pop, url, note):
    assert area in AREAS
    rows.append((year, area, int(round(pop)), url, note))
f = lambda n: f'{int(round(n)):,}'
r10 = lambda n: int(round(n, -1))

# ------------------------------------------------------------------ county tables as counted (Forstall 1996)
bergen_co = {1790: 12601, 1800: 15156, 1810: 16603, 1820: 18178, 1830: 22412, 1840: 13223, 1850: 14725, 1860: 21618, 1870: 30122, 1880: 36786, 1890: 47226,
             1900: 78441, 1910: 138002, 1920: 210703, 1930: 364977, 1940: 409646, 1950: 539139, 1960: 780255, 1970: 898012, 1980: 845385, 1990: 825380}
essex_co = {1790: 17785, 1800: 22269, 1810: 25984, 1820: 30793, 1830: 41911, 1840: 44621, 1850: 73950, 1860: 98877, 1870: 143839, 1880: 189929, 1890: 256098,
            1900: 359053, 1910: 512886, 1920: 652089, 1930: 833513, 1940: 837340, 1950: 905949, 1960: 923545, 1970: 929986, 1980: 851116, 1990: 778206}
hudson_co = {1840: 9483, 1850: 21822, 1860: 62717, 1870: 129067, 1880: 187944, 1890: 275126, 1900: 386048, 1910: 537231, 1920: 629154, 1930: 690730,
             1940: 652040, 1950: 647437, 1960: 610734, 1970: 609266, 1980: 556972, 1990: 553099}
passaic_co = {1840: 16734, 1850: 22569, 1860: 29013, 1870: 46416, 1880: 68860, 1890: 105046, 1900: 155202, 1910: 215902, 1920: 259174, 1930: 302129,
              1940: 309353, 1950: 337093, 1960: 406618, 1970: 460782, 1980: 447585, 1990: 453060}
union_co = {1860: 27780, 1870: 41859, 1880: 55571, 1890: 72467, 1900: 99353, 1910: 140197, 1920: 200157, 1930: 305209, 1940: 328344, 1950: 398138,
            1960: 504255, 1970: 543116, 1980: 504094, 1990: 493819}
west_co = {1790: 24003, 1800: 27373, 1810: 30272, 1820: 32638, 1830: 36456, 1840: 48686, 1850: 58263, 1860: 99497, 1870: 131348, 1880: 108988, 1890: 146772,
           1900: 184257, 1910: 283055, 1920: 344436, 1930: 520947, 1940: 573558, 1950: 625816, 1960: 808891, 1970: 894104, 1980: 866599, 1990: 874866}
west_present = {1790: 22222, 1800: 25618, 1810: 28005, 1820: 29856, 1830: 33433, 1840: 43340, 1850: 50231, 1860: 75904, 1870: 93955, 1880: 98634, 1890: 131949}  # Forstall note 3
bronx = {1790: 1781, 1800: 1755, 1810: 2267, 1820: 2782, 1830: 3023, 1840: 5346, 1850: 8032, 1860: 23593, 1870: 37393, 1880: 51980, 1890: 88908}            # Forstall note 3 (the city's bronx rows)
queens_co = {1790: 16014, 1800: 16916, 1810: 19336, 1820: 21519, 1830: 22460, 1840: 30324, 1850: 36833, 1860: 57391, 1870: 73803, 1880: 90574, 1890: 128059}
nassau_present = {1790: 9855, 1800: 10274, 1810: 11892, 1820: 13273, 1830: 13411, 1840: 15844, 1850: 18240, 1860: 24488, 1870: 28335, 1880: 34015, 1890: 41009}  # Forstall note 11
nassau_co = {1900: 55448, 1910: 83930, 1920: 126120, 1930: 303053, 1940: 406748, 1950: 672765, 1960: 1300171, 1970: 1428080, 1980: 1321582, 1990: 1287348}
rockland_co = {1800: 6353, 1810: 7758, 1820: 8837, 1830: 9388, 1840: 11975, 1850: 16962, 1860: 22492, 1870: 25213, 1880: 27690, 1890: 35162, 1900: 38298,
               1910: 46873, 1920: 45548, 1930: 59599, 1940: 74261, 1950: 89276, 1960: 136803, 1970: 229903, 1980: 259530, 1990: 265475}
# the three towns of today's Nassau in the Queens County returns (as given in the towns' Wikipedia tables; 1820 not at hand)
towns3 = {1790: (3828, 2696, 4097), 1800: (4141, 2413, 4548), 1840: (7609, 3891, 5865), 1850: (8811, 4291, 6900), 1860: (12376, 5419, 9168),
          1870: (13999, 6540, 10595), 1880: (18164, 7560, 11923), 1890: (23756, 8134, 13870)}

# ------------------------------------------------------------------ New Jersey township returns (Compendium of Censuses 1726-1905)
BT = {  # Bergen County
 1810: {'Bergen': 2690, 'Franklin': 2839, 'Hackensack': 1918, 'Harrington': 2087, 'New Barbadoes': 2835, 'Pompton': 2060, 'Saddle River': 2174},
 1820: {'Bergen': 3137, 'Franklin': 2968, 'Hackensack': 2076, 'Harrington': 2296, 'New Barbadoes': 2592, 'Pompton': 2818, 'Saddle River': 2291},
 1830: {'Bergen': 4651, 'Franklin': 3449, 'Hackensack': 2200, 'Harrington': 2581, 'Lodi': 1356, 'New Barbadoes': 1693, 'Pompton': 3085, 'Saddle River': 3399},
}
ET = {  # Essex County
 1810: {'Acquackanonk': 2023, 'Caldwell': 2235, 'Elizabeth': 2977, 'Newark': 8008, 'New Providence': 756, 'Orange': 2266, 'Rahway': 1779, 'Springfield': 2360, 'Union': 1428, 'Westfield': 2152},
 1820: {'Acquackanonk': 3338, 'Bloomfield': 3085, 'Caldwell': 2020, 'Elizabeth': 3515, 'Livingston': 1056, 'Newark': 6507, 'New Providence': 768, 'Orange': 2830, 'Rahway': 1945,
        'Springfield': 1804, 'Union': 1567, 'Westfield': 2358},
 1830: {'Acquackanonk': 7731, 'Bloomfield': 4309, 'Caldwell': 2004, 'Elizabeth': 3451, 'Livingston': 1150, 'Newark': 10953, 'New Providence': 903, 'Orange': 3887, 'Rahway': 1983,
        'Springfield': 1656, 'Union': 1409, 'Westfield': 2492},
 1840: {'Belleville': 2466, 'Bloomfield': 2528, 'Caldwell': 2184, 'Clinton': 1976, 'Elizabeth': 4184, 'Livingston': 1081, 'Newark': 17290, 'New Providence': 832, 'Orange': 3264,
        'Rahway': 2533, 'Springfield': 1651, 'Union': 1482, 'Westfield': 3150},
 1850: {'Belleville': 3514, 'Bloomfield': 3385, 'Caldwell': 2377, 'Clinton': 2508, 'Elizabeth': 5583, 'Livingston': 1151, 'Newark': 38894, 'New Providence': 1216, 'Orange': 4385,
        'Plainfield': 2447, 'Rahway': 3306, 'Springfield': 1945, 'Union': 1662, 'Westfield': 1577},
}
assert sum(BT[1810].values()) == 16603 and sum(BT[1820].values()) == 18178 and sum(BT[1830].values()) == 22414      # the census volume prints 22,412 for 1830
assert sum(ET[1810].values()) == 25984 and sum(ET[1820].values()) == 30793 and sum(ET[1830].values()) == 41928      # the census volume prints 41,911 for 1830
assert sum(ET[1840].values()) == 44621 and sum(ET[1850].values()) == 73950
HUD1840 = {'Bergen': 5255, 'Jersey City': 3072, 'Harrison': 1156}; assert sum(HUD1840.values()) == 9483
PAS1840 = {'Acquackanonk': 2483, 'Manchester': 3110, 'Paterson': 7596, 'Pompton': 1437, 'West Milford': 2108}; assert sum(PAS1840.values()) == 16734
HARRISON = {1840: 1156, 1850: 1345}          # Harrison township, Hudson County, while it still held today's Lyndhurst / Rutherford / North Arlington
# shares used where a township was later cut by a county line (each from the first count after the cut)
U_SHARE = 748 / (748 + 1516)                 # Union township (Bergen) : Harrison township (Hudson) at the 1855 state census, three years after the cut of 1852
M_SHARE = 3110 / (3110 + 828)                # Manchester (Passaic) : Saddle River (Bergen) in 1840, three years after the cut of 1837
H_LODI = 1156 / (1156 + 687)                 # Harrison : rest of Lodi township in 1840 (Lodi of 1830 = both)
H_NEWB = 1156 / (1156 + 687 + 2104)          # Harrison : Lodi + New Barbadoes in 1840 (New Barbadoes of 1810-1820 = all three)
MIL_SHARE = 1630 / (1630 + 1020)             # Millburn (Essex) : Springfield (Union) in 1860, three years after the cut of 1857
UNION_TOWNS = ('Elizabeth', 'New Providence', 'Plainfield', 'Rahway', 'Union', 'Westfield')

nj = {a: {} for a in ('hudson', 'bergen', 'passaic', 'essex', 'union')}
parts = {}
for y in (1810, 1820, 1830):
    b = BT[y]
    neck = b['Lodi'] * H_LODI if 'Lodi' in b else b['New Barbadoes'] * H_NEWB        # the Harrison township of 1840, inside Lodi / New Barbadoes
    hud_neck = neck * (1 - U_SHARE)                                                  # its part in today's Hudson (Harrison, Kearny, East Newark)
    man = b['Saddle River'] * M_SHARE                                                # the later Manchester township, to Passaic in 1837
    hudson = b['Bergen'] + hud_neck
    pas_b = b['Pompton'] + man
    bergen = sum(b.values()) - b['Bergen'] - hud_neck - pas_b
    parts[y] = dict(neck=hud_neck, man=man, pas_b=pas_b)
    nj['hudson'][y] = hudson; nj['bergen'][y] = bergen
    e = ET[y]
    spr_union = e['Springfield'] * (1 - MIL_SHARE) if y != 1810 else ET[1820]['Springfield'] * (1 - MIL_SHARE)
    union = sum(e.get(t, 0) for t in UNION_TOWNS) + spr_union
    essex = sum(e.values()) - e['Acquackanonk'] - union
    nj['union'][y] = union; nj['essex'][y] = essex; nj['passaic'][y] = pas_b + e['Acquackanonk']
    parts[y].update(spr_union=spr_union, union_towns=sum(e.get(t, 0) for t in UNION_TOWNS))
    tot = sum(b.values()) + sum(e.values())
    assert abs(sum(nj[a][y] for a in nj) - tot) < 1e-6
for y in (1840, 1850):
    upart = HARRISON[y] * U_SHARE
    nj['hudson'][y] = hudson_co[y] - upart; nj['bergen'][y] = bergen_co[y] + upart; nj['passaic'][y] = passaic_co[y]
    e = ET[y]; spr_union = e['Springfield'] * (1 - MIL_SHARE)
    nj['union'][y] = sum(e.get(t, 0) for t in UNION_TOWNS) + spr_union; nj['essex'][y] = sum(e.values()) - nj['union'][y]
    parts[y] = dict(upart=upart, spr_union=spr_union, union_towns=sum(e.get(t, 0) for t in UNION_TOWNS))
# shares of the two old counties in 1810, the first census with township returns
SH_B = {a: (nj[a][1810] if a != 'passaic' else parts[1810]['pas_b']) / 16603 for a in ('hudson', 'bergen', 'passaic')}
SH_E = {a: (nj[a][1810] if a != 'passaic' else ET[1810]['Acquackanonk']) / 25984 for a in ('essex', 'union', 'passaic')}
assert abs(sum(SH_B.values()) - 1) < 1e-9 and abs(sum(SH_E.values()) - 1) < 1e-9
pct = lambda v: f'{100 * v:.1f}%'
SPLIT_B = f'present Bergen {pct(SH_B["bergen"])}, Hudson {pct(SH_B["hudson"])}, the Bergen part of Passaic {pct(SH_B["passaic"])}'
SPLIT_E = f'present Essex {pct(SH_E["essex"])}, Union {pct(SH_E["union"])}, the Essex part of Passaic (Acquackanonk) {pct(SH_E["passaic"])}'

# ------------------------------------------------------------------ before the censuses: the 1682 account of East Jersey, Hempstead 1644
add(1644, 'nassau', 175, HEMP, 'estimate: "thirty to forty families" from Stamford, Connecticut, founded Hempstead in the spring of 1644 (Wikipedia, Hempstead village); taken as 35 families '
    'of five, the reckoning the 1682 East Jersey account uses. Colonists only (Lenape not counted); Oyster Bay was settled in 1653. No count of the town exists before the Queens County census of 1698')
add(1682, 'hudson', 730, SMITH, 'estimate: the account of East Jersey published in 1682 (Samuel Smith, History of Nova-Caesaria, 1765, pp. 159-161) gives Bergen, "a compact town", about 70 families, '
    'and on Bergen Neck a village of 20 families, another 16 or 18, and "about forty families" seated opposite New York - about 146 families, reckoned at five to a family as the account does. '
    'Constable Hook, Hobuck (Hoboken) and the scattered plantations are not counted. Colonists only')
add(1682, 'essex', 500, SMITH, 'estimate: Newark "a compact town, consisting of about one hundred families" in the 1682 account of East Jersey (Smith 1765, p. 159), which reckons five to a family; '
    'the plantations up the Passaic are not counted. In 1673 the Dutch listed 86 men at Newark (New Jersey Compendium of Censuses, p. 9)')
add(1682, 'union', 750, SMITH, 'estimate: Elizabeth-Town "supposed to consist of one hundred and fifty families" in the 1682 account of East Jersey (Smith 1765, p. 159), which reckons five to a family. '
    'In 1673 the Dutch listed 80 men at Elizabeth-Town (New Jersey Compendium of Censuses, p. 9)')

# ------------------------------------------------------------------ colonial censuses of New Jersey by county (CPG tables 100-102; 1784 from the Compendium)
njcol = {  # year: (Bergen County, Essex County, what)
 1726: (2673, 4230, 'census of 1726 sent to the Lords of Trade by Governor Burnet (Century of Population Growth, table 100)'),
 1738: (4095, 6326, 'census of 1737-38 (Century of Population Growth, table 101)'),
 1745: (3006, 6988, 'census of 1745 taken for Governor Morris (Century of Population Growth, table 102)'),
 1784: (9356, 13430, 'state enumeration of 1784 (New Jersey Compendium of Censuses 1726-1905, county table; the Census Bureau classes the 1784 total as an estimate)'),
}
for y, (bc, ec, what) in njcol.items():
    url = NJC if y == 1784 else CPG
    ex = ' The return as transmitted gave Essex 7,019; 6,326 is the sum of its columns (the bureau\'s corrected figure).' if y == 1738 else ''
    for a in ('hudson', 'bergen'):
        add(y, a, r10(bc * SH_B[a]), url, f'estimate: Bergen County counted {bc:,} in the {what}; the old county also covered today\'s Hudson and part of Passaic. No township returns survive before 1810: '
            f'split by the 1810 shares ({SPLIT_B})' + ('. The 1682 account suggests that Bergen Neck (Hudson) held a larger share in the first decades than this split gives it' if a == 'hudson' else ''))
    for a in ('essex', 'union'):
        add(y, a, r10(ec * SH_E[a]), url, f'estimate: Essex County counted {ec:,} in the {what}; the old county also covered today\'s Union and part of Passaic. No township returns survive before 1810: '
            f'split by the 1810 shares ({SPLIT_E}).' + ex)
    add(y, 'passaic', r10(bc * SH_B['passaic'] + ec * SH_E['passaic']), url, f'estimate: {pct(SH_B["passaic"])} of Bergen County ({bc:,}) plus {pct(SH_E["passaic"])} of Essex County ({ec:,}) in the {what} - '
        f'the 1810 shares of Pompton, the later Manchester and Acquackanonk, the townships that became Passaic County in 1837.' + ex)

# ------------------------------------------------------------------ colonial censuses of New York by county (CPG tables 88-99, as in the city's population.csv)
nycol = {  # year: (Queens County incl. Nassau, Westchester County incl. the Bronx, Orange County)
 1698: (3565, 1063, 219), 1703: (4392, 1946, 268), 1723: (7191, 4409, None), 1731: (7995, 6033, None), 1737: (9059, 6745, None), 1746: (9640, 9235, None),
 1749: (7940, 10703, None), 1756: (10786, 13257, None), 1771: (10980, 21745, None), 1786: (13084, 20554, None),
}
tbl = {1698: 'table 88', 1703: 'table 89', 1723: 'table 92', 1731: 'table 93', 1737: 'table 94', 1746: 'table 95', 1749: 'table 96', 1756: 'table 97', 1771: 'table 98', 1786: 'table 99'}
QSHARE = 6159 / 16014; BSHARE = 1781 / 24003
for y, (q, w, o) in nycol.items():
    what = ('state census of 1786' if y == 1786 else f'colonial census of {y}') + f' (Century of Population Growth, {tbl[y]})'
    add(y, 'nassau', r10(q - q * QSHARE), CPG, f'estimate: Queens County counted {q:,} in the {what}; the county then covered today\'s Queens and Nassau. Scaled by the share of the present Nassau '
        f'in the old county at the 1790 census (9,855 of 16,014 = 61.5%), the complement of the city\'s queens row')
    add(y, 'westchester', r10(w - w * BSHARE), CPG, f'estimate: Westchester County counted {w:,} in the {what}; the county then included today\'s Bronx. Scaled by the share of the present county '
        f'at the 1790 census (22,222 of 24,003 = 92.6%), the complement of the Bronx share used in the city\'s rows' + ('; the old towns of Westchester and Eastchester (now the Bronx) probably held a larger share this early' if y <= 1731 else ''))
    if o:
        add(y, 'rockland', o, CPG, f'estimate: Orange County counted {o:,} in the {what}. The county then ran from the New Jersey line to Murderers Creek, but its settlers lived at Tappan (Orangetown) and '
            'Haverstraw, in today\'s Rockland; Goshen and the country north of the Highlands were settled after 1712. The whole county count is taken (not checked against the name list). '
            'For 1723-1786 the Rockland share of Orange County is not known and no row is given')

# ------------------------------------------------------------------ federal censuses 1790-1890, present areas
for y in (1790, 1800):
    for a in ('hudson', 'bergen'):
        add(y, a, r10(bergen_co[y] * SH_B[a]), FORSTALL, f'estimate: US census, Bergen County {bergen_co[y]:,}; Hudson (1840) and Passaic (1837) had not been set off and the {y} returns give no townships. '
            f'Split by the 1810 township shares ({SPLIT_B})')
    for a in ('essex', 'union'):
        add(y, a, r10(essex_co[y] * SH_E[a]), FORSTALL, f'estimate: US census, Essex County {essex_co[y]:,}; Union (1857) and Passaic (1837) had not been set off and the {y} returns give no townships. '
            f'Split by the 1810 township shares ({SPLIT_E})')
    add(y, 'passaic', r10(bergen_co[y] * SH_B['passaic'] + essex_co[y] * SH_E['passaic']), FORSTALL, f'estimate: US census; {pct(SH_B["passaic"])} of Bergen County ({bergen_co[y]:,}) plus '
        f'{pct(SH_E["passaic"])} of Essex County ({essex_co[y]:,}), the 1810 shares of the townships that became Passaic County in 1837 (no township returns in {y})')
for y in (1810, 1820, 1830):
    b, e, p = BT[y], ET[y], parts[y]
    nb = 'Lodi township' if 'Lodi' in b else 'New Barbadoes township'
    nbv = b['Lodi'] if 'Lodi' in b else b['New Barbadoes']
    tot_note = ' (the townships add up to 22,414; the census volume prints 22,412 for the county)' if y == 1830 else ''
    add(y, 'hudson', nj['hudson'][y], NJC, f'estimate: US census, township returns (New Jersey Compendium of Censuses): Bergen township {b["Bergen"]:,}, counted, the whole county east of the Hackensack '
        f'(Jersey City included), plus about {f(p["neck"])} for today\'s Harrison, Kearny and East Newark, then part of {nb} ({nbv:,}) - its share from the counts of 1840 and 1855. Hudson County was set off from Bergen in 1840')
    add(y, 'bergen', nj['bergen'][y], NJC, f'estimate: US census, township returns (New Jersey Compendium of Censuses): Bergen County {sum(b.values()):,}{tot_note} less Bergen township ({b["Bergen"]:,}, Hudson since 1840), '
        f'Pompton ({b["Pompton"]:,}, Passaic since 1837), and two estimated parts: the later Manchester township, {pct(M_SHARE)} of Saddle River ({b["Saddle River"]:,}), about {f(p["man"])}, '
        f'and the Hudson part of {nb}, about {f(p["neck"])}')
    add(y, 'passaic', nj['passaic'][y], NJC, f'estimate: US census, township returns (New Jersey Compendium of Censuses): Acquackanonk {e["Acquackanonk"]:,} (Essex County; Paterson included) + Pompton {b["Pompton"]:,} '
        f'(Bergen County; West Milford included), both counted, + about {f(p["man"])} for the later Manchester township, {pct(M_SHARE)} of Saddle River ({b["Saddle River"]:,}) as in 1840. Passaic County was created in 1837')
    spr = (f'Springfield\'s Union part, about {f(p["spr_union"])} (the township, {e["Springfield"]:,}, then also covered Millburn and part of Livingston; the 1820 estimate is carried back)' if y == 1810 else
           f'{pct(1 - MIL_SHARE)} of Springfield ({e["Springfield"]:,}), about {f(p["spr_union"])} - the township also covered today\'s Millburn, split as in 1860')
    twn = ', '.join(f'{t} {e[t]:,}' for t in UNION_TOWNS if t in e)
    add(y, 'union', nj['union'][y], NJC, f'estimate: US census, township returns (New Jersey Compendium of Censuses), counted: {twn} = {p["union_towns"]:,}; plus {spr}. Union County was set off from Essex in 1857')
    add(y, 'essex', nj['essex'][y], NJC, f'estimate: US census, township returns (New Jersey Compendium of Censuses): Essex County {sum(e.values()):,}' + (' (the census volume prints 41,911)' if y == 1830 else '') +
        f' less Acquackanonk ({e["Acquackanonk"]:,}, Passaic since 1837) and the townships of today\'s Union County ({p["union_towns"]:,} counted + about {f(p["spr_union"])} of Springfield); '
        'the part of Springfield that is now Millburn stays with Essex')
for y in (1840, 1850):
    e, p = ET[y], parts[y]
    add(y, 'hudson', nj['hudson'][y], NJC, f'estimate: US census, Hudson County {hudson_co[y]:,} less about {f(p["upart"])} for the part of Harrison township ({HARRISON[y]:,}) returned to Bergen County in 1852 as Union township '
        f'(Lyndhurst, Rutherford, North Arlington) - {pct(U_SHARE)} of the township, the split of the 1855 state census (Union 748, Harrison 1,516)')
    add(y, 'bergen', nj['bergen'][y], NJC, f'estimate: US census, Bergen County {bergen_co[y]:,} plus about {f(p["upart"])} for Union township (Lyndhurst, Rutherford, North Arlington), counted in {y} in Harrison township, '
        f'Hudson County ({HARRISON[y]:,}), and returned to Bergen in 1852 - {pct(U_SHARE)} of that township, the split of the 1855 state census')
    add(y, 'passaic', passaic_co[y], FORSTALL, 'US census; Passaic County, created in 1837 from Bergen and Essex counties, same area as today' +
        (' (Acquackanonk 2,483, Manchester 3,110, Paterson 7,596, Pompton 1,437, West Milford 2,108)' if y == 1840 else ''))
    twn = ', '.join(f'{t} {e[t]:,}' for t in UNION_TOWNS if t in e)
    add(y, 'union', nj['union'][y], NJC, f'estimate: US census, township returns (New Jersey Compendium of Censuses), counted: {twn} = {p["union_towns"]:,}; plus {pct(1 - MIL_SHARE)} of Springfield ({e["Springfield"]:,}), '
        f'about {f(p["spr_union"])} - the township also covered today\'s Millburn, split as in 1860. Union County was set off from Essex in 1857')
    add(y, 'essex', nj['essex'][y], NJC, f'estimate: US census, Essex County {essex_co[y]:,} less the townships of today\'s Union County ({p["union_towns"]:,} counted + about {f(p["spr_union"])} of Springfield); '
        'the part of Springfield that is now Millburn stays with Essex')
for y in range(1860, 1900, 10):
    add(y, 'hudson', hudson_co[y], FORSTALL, 'US census; Hudson County, same area as today (set off from Bergen in 1840; Union township returned to Bergen in 1852)')
    add(y, 'bergen', bergen_co[y], FORSTALL, 'US census; Bergen County, same area as today')
    add(y, 'passaic', passaic_co[y], FORSTALL, 'US census; Passaic County, same area as today')
    add(y, 'union', union_co[y], FORSTALL, 'US census; Union County' + (', first census after it was set off from Essex in 1857 (a strip of Woodbridge, Middlesex County, joined Rahway in 1860)' if y == 1860 else ''))
    add(y, 'essex', essex_co[y], FORSTALL, 'US census; Essex County, same area as today but for small later changes on the Union line (Millburn - Springfield, 1891)')
for y in range(1790, 1900, 10):
    add(y, 'westchester', west_present[y], FORSTALL, f'Census Bureau estimate of the present area (Forstall, New York note 3): Westchester County counted {west_co[y]:,}' +
        (', still including the East Bronx (annexed by the city in 1895) but no longer the West Bronx (1874)' if y >= 1880 else ', including the towns now in the Bronx') +
        f'; the present-area figure leaves out the Bronx part, {west_co[y] - west_present[y]:,}' + (f' (the city\'s bronx row, {bronx[y]:,}, also holds the West Bronx)' if y >= 1880 else ' (the city\'s bronx row)') +
        ' - the bureau\'s 1900 re-allocation of the town returns, an estimate where a town was later divided (Yonkers, Eastchester, Pelham)')
    t3 = towns3.get(y)
    if t3:
        s = sum(t3)
        tn = (f'the three towns were counted at Hempstead {t3[0]:,} + North Hempstead {t3[1]:,} + Oyster Bay {t3[2]:,} = {s:,} (town figures as given in the towns\' Wikipedia tables); the bureau leaves out {s - nassau_present[y]:,}, '
              'one fifth of Hempstead, for the Rockaway peninsula, which went to the city in 1898 - that fifth is the bureau\'s estimate')
    else:
        tn = 'the towns of Hempstead, North Hempstead and Oyster Bay less the bureau\'s allowance for the Rockaway part of Hempstead, which went to the city in 1898 (one fifth of the town at the other censuses; the town figures were not at hand for this year)'
    add(y, 'nassau', nassau_present[y], FORSTALL, f'Census Bureau estimate of the present area (Forstall, New York note 11): Nassau County was set off from Queens County in 1899; Queens County counted {queens_co[y]:,}, and {tn}. '
        'The city\'s queens row is the rest of the old county')
add(1790, 'rockland', 4826 + 1175, C1790, 'US census, town returns summed: Haverstraw 4,826 + Orangetown 1,175, the two towns of Orange County south of the Highlands that became Rockland County in 1798 '
    '(the published return of 1791, whose towns add up to Orange County\'s 18,492; the Census Bureau\'s 1909 re-tally of the schedules gives 4,824 + 1,163)')
for y in range(1800, 1900, 10):
    add(y, 'rockland', rockland_co[y], FORSTALL, 'US census; Rockland County, same area as today' + (' (set off from Orange County in 1798)' if y == 1800 else ''))

# ------------------------------------------------------------------ 1900-1990 (Forstall), 2000, 2010, 2020, latest estimate
for y in range(1900, 2000, 10):
    rev = ' (as published in 1996; later revisions of the 1970 count differ by a few hundred to a few thousand)' if y == 1970 else ''
    add(y, 'hudson', hudson_co[y], FORSTALL, 'US census; Hudson County' + rev)
    add(y, 'bergen', bergen_co[y], FORSTALL, 'US census; Bergen County' + rev)
    add(y, 'essex', essex_co[y], FORSTALL, 'US census; Essex County' + rev)
    add(y, 'union', union_co[y], FORSTALL, 'US census; Union County' + rev)
    add(y, 'passaic', passaic_co[y], FORSTALL, 'US census; Passaic County' + rev)
    add(y, 'westchester', west_co[y], FORSTALL, 'US census; Westchester County' + (', first census within today\'s lines (the East Bronx went to the city in 1895)' if y == 1900 else '') + rev)
    add(y, 'nassau', nassau_co[y], FORSTALL, 'US census; Nassau County' + (', first census of the county created on 1 January 1899 from the towns of Hempstead, North Hempstead and Oyster Bay' if y == 1900 else '') + rev)
    add(y, 'rockland', rockland_co[y], FORSTALL, 'US census; Rockland County' + rev)
c2000 = dict(bergen=884118, essex=793633, hudson=608975, passaic=489049, union=522541, nassau=1334544, rockland=286753, westchester=923459)
c2010 = dict(bergen=905116, essex=783969, hudson=634266, passaic=501226, union=536499, nassau=1339532, rockland=311687, westchester=949113)
c2020 = dict(bergen=955732, essex=863728, hudson=724854, passaic=524118, union=575345, nassau=1395774, rockland=338329, westchester=1004457)
e2025 = dict(bergen=977026, essex=896379, hudson=735033, passaic=531624, union=601863, nassau=1398939, rockland=357397, westchester=1015743)
for a in AREAS:
    add(2000, a, c2000[a], C2000, 'US census, 1 April 2000 (CENSUS2000POP in the Census Bureau county totals file)')
    add(2010, a, c2010[a], C2010, 'US census, 1 April 2010 (CENSUS2010POP in the Census Bureau county totals file)')
    add(2020, a, c2020[a], C2020B if a in ('nassau', 'rockland') else C2020, 'US census, 1 April 2020 (figure checked against the county\'s Wikipedia table, not against the QuickFacts page itself)')
    add(2025.5, a, e2025[a], EST, 'estimate: Census Bureau Vintage 2025 population estimate for 1 July 2025 (county totals file)')

order = {a: i for i, a in enumerate(AREAS)}
rows.sort(key=lambda r: (r[0], order[r[1]]))
with open(OUT, 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['year', 'area', 'population', 'source_url', 'note'])
    for y, a, p, u, n in rows:
        w.writerow([('%g' % y), a, p, u, n])
print(len(rows), 'rows')
for a in AREAS:
    print(a, ' '.join(f'{("%g" % y)}:{p}' for y, aa, p, u, n in rows if aa == a))
