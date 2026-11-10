"""Writes data/tables/population.csv from figures read off the cited sources (see notes)."""
import csv, math
OUT = '/home/user/nyc/data/tables/population.csv'
FORSTALL = 'https://www2.census.gov/library/publications/decennial/1990/population-of-states-and-counties-us-1790-1990/population-of-states-and-counties-of-the-united-states-1790-1990.pdf'
DCP = 'https://www.nyc.gov/assets/planning/download/pdf/data-maps/nyc-population/historical-population/nyc_total_pop_1900-2010.pdf'
C2020 = 'https://www.census.gov/quickfacts/fact/table/newyorkcitynewyork,bronxcountynewyork,kingscountynewyork,newyorkcountynewyork,queenscountynewyork,richmondcountynewyork/POP010220'
EST = 'https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/counties/totals/co-est2025-alldata.csv'
CPG = 'https://archive.org/details/centuryofpopulat00unit'
MCNY = 'https://www.mcny.org/node/6995'
NNI = 'https://newnetherlandinstitute.org/history-and-heritage/digital-exhibitions/a-tour-of-new-netherland/manhattan/new-amsterdam/'
WPM = 'https://en.wikipedia.org/wiki/Manhattan#Demographics'
WPL = 'https://en.wikipedia.org/wiki/History_of_New_York_City_(prehistory%E2%80%931664)'
FIRE = 'https://en.wikipedia.org/wiki/Great_Fire_of_New_York_(1776)'
OCC = 'https://newyorkslavery.blogspot.com/2007/08/chapter-eleven.html'
ROS = 'https://archive.org/details/populationhistor00irar'
rows = []
def add(year, area, pop, url, note): rows.append((year, area, int(round(pop)), url, note))

# ---- c.1609
add(1609, 'nyc', 15000, WPL, 'estimate: about 15,000 Lenape in roughly 80 settlement sites around the New York City area at European contact (Burrows & Wallace, Gotham, 1998, pp. 5-6, as cited by Wikipedia). No count exists; until the 1698 census the line between this row and the next is an interpolation while the people counted change from Lenape to colonists')

# ---- New Amsterdam / New York before the first census (Manhattan = the town at its southern tip)
add(1628, 'manhattan', 270, MCNY, 'estimate: 270 colonists and enslaved Africans at New Amsterdam by 1628 (contemporary report, Museum of the City of New York); colonists only, Lenape not counted')
add(1643, 'manhattan', 500, NNI, 'estimate: "barely 500 people" in New Amsterdam in 1643, when Kieft told Isaac Jogues 18 languages were spoken (New Netherland Institute); colonists only')
add(1656, 'manhattan', 1000, WPM, 'estimate: first survey of New Amsterdam, 1656 - 120 houses and 1,000 inhabitants (Rosenwaike, Population History of New York City, 1972, p. 3, as cited by Wikipedia); a round figure')
add(1664, 'manhattan', 1500, MCNY, 'estimate: about 1,500 people in New Amsterdam at the English takeover (Museum of the City of New York); Jaap Jacobs gives 2,500 for the town and almost 9,000 for all New Netherland')

# ---- colonial censuses of New York province by county (Census Bureau 1909, A Century of Population Growth, tables 88-99)
col = {  # year: (New York, Kings, Richmond, Queens County incl. Nassau, Westchester County)
 1698: (4937, 2017, 727, 3565, 1063),
 1703: (4375, 1912, 504, 4392, 1946),
 1723: (7248, 2218, 1506, 7191, 4409),
 1731: (8622, 2150, 1817, 7995, 6033),
 1737: (10664, 2348, 1889, 9059, 6745),
 1746: (11717, 2331, 2073, 9640, 9235),
 1749: (13294, 2283, 2154, 7940, 10703),
 1756: (13046, 2707, 2132, 10786, 13257),
 1771: (21863, 3623, 2847, 10980, 21745),
 1786: (23614, 3986, 3152, 13084, 20554),
}
tbl = {1698: 'table 88', 1703: 'table 89', 1723: 'table 92', 1731: 'table 93', 1737: 'table 94', 1746: 'table 95', 1749: 'table 96', 1756: 'table 97', 1771: 'table 98', 1786: 'table 99'}
QSHARE = 6159 / 16014      # present Queens / old Queens County at the 1790 census (Forstall note 11)
BSHARE = 1781 / (1781 + 22222)  # present Bronx / (Bronx + present Westchester) at the 1790 census (Forstall note 3)
extra = {1703: '; a 1712 letter to the Lords of Trade gives slightly different totals (New York 4,436, Kings 1,915, Richmond 503)',
         1749: '; white and black totals of the table added (10,926 + 2,368 etc.)',
         1756: '; white and black totals of the table added',
         1786: '; state census of 1786'}
outer = {}
for y, (ny, k, r, q, w) in col.items():
    src = f'colonial census of New York province, {y} (US Census Bureau 1909, A Century of Population Growth, {tbl[y]})' + extra.get(y, '')
    add(y, 'manhattan', ny, CPG, f'{src}; City and County of New York')
    add(y, 'brooklyn', k, CPG, f'{src}; Kings County')
    add(y, 'staten_island', r, CPG, f'{src}; Richmond County')
    qe = round(q * QSHARE, -1)
    add(y, 'queens', qe, CPG, f'estimate: Queens County counted {q:,} in {y}, but colonial Queens included today\'s Nassau County; scaled by the present borough\'s share of the old county at the 1790 census (6,159 of 16,014 = 38.5%)')
    be = w * BSHARE
    outer[y] = k + r + q * QSHARE + be
    add(y, 'nyc', round(ny + outer[y], -1), CPG, f'estimate: New York {ny:,} + Kings {k:,} + Richmond {r:,} counted in {y} ({tbl[y]}), plus the 1790 shares of Queens County ({q:,} x 38.5%, the rest is today\'s Nassau) and of Westchester County ({w:,} x 7.4%, for today\'s Bronx); Native people not counted')

# ---- the Revolution: occupation and evacuation (Manhattan = the city; nyc = city + the outer counties interpolated 1771-1786)
def outer_at(y):
    a, b = outer[1771], outer[1786]
    return math.exp(math.log(a) + (math.log(b) - math.log(a)) * (y - 1771) / (1786 - 1771))
war = [
 (1775, 25000, FIRE, 'estimate: about 25,000 in the city on the eve of the war (Wikipedia, Great Fire of New York 1776)'),
 (1776.75, 5000, OCC, 'estimate: "only from 3 to 5,000 inhabitants remained" when the British took the city in September 1776 (Wertenbaker, Father Knickerbocker Rebels, pp. 76-77, 98, as cited); upper figure shown; troops not counted'),
 (1777.15, 11000, OCC, 'estimate: 11,000 by the end of February 1777 as Loyalists arrived (Wertenbaker p. 103; Abbott p. 248, as cited)'),
 (1779, 30000, OCC, 'estimate: 30,000 by 1779 with Loyalist refugees (Wertenbaker p. 103; Abbott p. 248, as cited); Burrows & Wallace give 33,000'),
 (1783.9, 12000, ROS, 'estimate, NOT VERIFIED against the source text: about 12,000 left in the city after the British evacuation of 25 November 1783, when some 29,000-35,000 Loyalists sailed (figure usually attributed to Rosenwaike 1972); the 1786 state census then counted 23,614'),
]
for y, p, url, note in war:
    add(y, 'manhattan', p, url, note)
    add(y, 'nyc', round(p + outer_at(y), -2), url, note.replace('estimate', 'estimate: city figure plus about %s for Kings, Richmond and the present Queens and Bronx (interpolated between the 1771 and 1786 censuses). City' % f'{round(outer_at(y), -2):,.0f}', 1))

# ---- federal censuses 1790-1890, present-day areas (Forstall 1996: county table and New York notes 3, 8, 11, 12)
man = {1790: 33131, 1800: 60515, 1810: 96373, 1820: 123706, 1830: 202589, 1840: 312710, 1850: 515547, 1860: 813669, 1870: 942292, 1880: 1164673, 1890: 1441216}
bkn = {1790: 4495, 1800: 5740, 1810: 8303, 1820: 11187, 1830: 20535, 1840: 47613, 1850: 138882, 1860: 279122, 1870: 419921, 1880: 599495, 1890: 838547}
sti = {1790: 3835, 1800: 4564, 1810: 5347, 1820: 6135, 1830: 7082, 1840: 10965, 1850: 15061, 1860: 25492, 1870: 33029, 1880: 38991, 1890: 51693}
bx = {1790: 1781, 1800: 1755, 1810: 2267, 1820: 2782, 1830: 3023, 1840: 5346, 1850: 8032, 1860: 23593, 1870: 37393, 1880: 51980, 1890: 88908}
qco = {1790: 16014, 1800: 16916, 1810: 19336, 1820: 21519, 1830: 22460, 1840: 30324, 1850: 36833, 1860: 57391, 1870: 73803, 1880: 90574, 1890: 128059}
nas = {1790: 9855, 1800: 10274, 1810: 11892, 1820: 13273, 1830: 13411, 1840: 15844, 1850: 18240, 1860: 24488, 1870: 28335, 1880: 34015, 1890: 41009}
nyco = {1880: 1206299, 1890: 1515301}
for y in sorted(man):
    q = qco[y] - nas[y]
    mnote = 'US census; New York County, then conterminous with the city and with today\'s Manhattan'
    if y in nyco:
        mnote = f'US census; present area of New York County (Forstall note 12). The county counted {nyco[y]:,} including the Bronx district annexed in 1874'
    add(y, 'manhattan', man[y], FORSTALL, mnote)
    add(y, 'bronx', bx[y], FORSTALL, 'US census returns of the Westchester County towns re-allocated to the present Bronx by the Census Bureau in 1900 (Forstall note 3)')
    add(y, 'brooklyn', bkn[y], FORSTALL, 'US census; Kings County (same area as the borough)')
    add(y, 'queens', q, FORSTALL, f'US census; old Queens County {qco[y]:,} less the part that became Nassau County in 1899 ({nas[y]:,}), as re-allocated by the Census Bureau in 1900 (Forstall note 11)')
    add(y, 'staten_island', sti[y], FORSTALL, 'US census; Richmond County (same area as the borough)')
    add(y, 'nyc', man[y] + bx[y] + bkn[y] + q + sti[y], FORSTALL, 'US census; sum of the five present boroughs\' areas (before the 1898 consolidation). The City of New York proper is the manhattan row' + ('' if y < 1880 else ' plus the annexed Bronx district'))

# ---- 1900-2010 (NYC Department of City Planning, Total Population New York City & Boroughs 1900 to 2010)
dcp = {  # year: (nyc, bronx, brooklyn, manhattan, queens, staten island)
 1900: (3437202, 200507, 1166582, 1850093, 152999, 67021),
 1910: (4766883, 430980, 1634351, 2331542, 284041, 85969),
 1920: (5620048, 732016, 2018356, 2284103, 469042, 116531),
 1930: (6930446, 1265258, 2560401, 1867312, 1079129, 158346),
 1940: (7454995, 1394711, 2698285, 1889924, 1297634, 174441),
 1950: (7891957, 1451277, 2738175, 1960101, 1550849, 191555),
 1960: (7781984, 1424815, 2627319, 1698281, 1809578, 221991),
 1970: (7894862, 1471701, 2602012, 1539233, 1986473, 295443),
 1980: (7071639, 1168972, 2230936, 1428285, 1891325, 352121),
 1990: (7322564, 1203789, 2300664, 1487536, 1951598, 378977),
 2000: (8008278, 1332650, 2465326, 1537195, 2229379, 443728),
 2010: (8175133, 1385108, 2504700, 1585873, 2230722, 468730),
}
names = ('nyc', 'bronx', 'brooklyn', 'manhattan', 'queens', 'staten_island')
for y, vals in dcp.items():
    assert vals[0] == sum(vals[1:]), y
    for a, v in zip(names, vals):
        add(y, a, v, DCP, 'US census (NYC Department of City Planning, Total Population New York City & Boroughs 1900-2010; 1900-1990 agree with the Census Bureau county table)' + (' - first census after the consolidation of 1 January 1898' if y == 1900 else ''))
c20 = (8804190, 1472654, 2736074, 1694251, 2405464, 495747)
assert c20[0] == sum(c20[1:])
for a, v in zip(names, c20):
    add(2020, a, v, C2020, 'US census, 1 April 2020')
e25 = (8584629, 1406332, 2653963, 1664862, 2358182, 501290)
assert e25[0] == sum(e25[1:])
for a, v in zip(names, e25):
    add(2025.5, a, v, EST, 'estimate: Census Bureau Vintage 2025 population estimate for 1 July 2025 (county totals file' + ('; sum of the five counties)' if a == 'nyc' else ')'))

order = {a: i for i, a in enumerate(('nyc', 'manhattan', 'bronx', 'brooklyn', 'queens', 'staten_island'))}
rows.sort(key=lambda r: (r[0], order[r[1]]))
with open(OUT, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['year', 'area', 'population', 'source_url', 'note'])
    for y, a, p, u, n in rows:
        w.writerow([('%g' % y), a, p, u, n])
print(len(rows), 'rows')
