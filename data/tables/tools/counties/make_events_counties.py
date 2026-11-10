"""Writes data/tables/events_counties.csv (columns of events.csv): events that changed the map in the eight counties around the city.
Years are checked against the cited Wikipedia article; a month or day that the article does not give in full is left blank."""
import csv, os, re, sys, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import wpc
OUT = '/home/user/nyc/data/tables/events_counties.csv'
MONTHS = ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
# year, month, day, title, description, lat, lon, zoom, Wikipedia title
R = [
 (1630, '', '', 'Pavonia', 'Michiel Pauw, a director of the West India Company, buys the west bank of the North River from the Lenape - Hoboken, then Ahasimus and Aressick - for the patroonship he calls Pavonia. The first houses rise at Communipaw and Harsimus within a few years.', 40.7170, -74.0400, 13, 'Pavonia, New Netherland'),
 (1644, 11, 16, 'Hempstead', 'English families from Stamford, Connecticut, settle on the great plains of Long Island under a patent from Director Kieft; their town will hold the south half of today\'s Nassau County.', 40.7065, -73.6200, 13, 'Hempstead (village), New York'),
 (1653, '', '', 'Oyster Bay', 'Peter Wright, Samuel Mayo and William Leverich buy land from the Matinecock sachem Assiapum and found Oyster Bay, on the harbour that the Hartford treaty of 1650 made the border between New Netherland and New England.', 40.8720, -73.5310, 13, 'Oyster Bay (hamlet), New York'),
 (1660, '', '', 'Bergen', 'Stuyvesant orders a palisaded village laid out on the ridge behind Communipaw. Bergen, with its square and four gates, is the first permanent town in New Jersey and gets its own court the next year.', 40.7303, -74.0653, 15, 'Bergen, New Netherland'),
 (1664, 10, 28, 'The Elizabethtown Purchase', 'Weeks after the English take New Netherland, men from Long Island buy the land between the Raritan and the Passaic from the Lenape. Elizabethtown becomes the first English town and the first capital of New Jersey.', 40.6628, -74.2150, 13, 'Elizabeth, New Jersey'),
 (1666, 5, '', 'Newark', 'Puritans from Milford, Branford and New Haven, led by Robert Treat, land on the Passaic and lay out a town along a broad street with a training place and a market place.', 40.7357, -74.1724, 14, 'Newark, New Jersey'),
 (1683, 3, '', 'East Jersey\'s Four Counties', 'The assembly of East Jersey divides the province into Bergen, Essex, Middlesex and Monmouth counties. Bergen and Essex later give up Passaic (1837), Hudson (1840) and Union (1857).', 40.8787, -74.0437, 10, 'Bergen County, New Jersey'),
 (1686, 3, 24, 'The Tappan Patent', 'Governor Dongan grants the valley of the Sparkill to sixteen Dutch families from Manhattan; Tappan becomes the seat of Orange County.', 41.0223, -73.9475, 13, 'Orangetown, New York'),
 (1688, '', '', 'New Rochelle', 'Huguenot refugees settle on 6,000 acres that Jacob Leisler buys for them from John Pell, lord of Pelham Manor.', 40.9115, -73.7824, 13, 'New Rochelle, New York'),
 (1693, '', '', 'Philipsburg Manor', 'A royal charter makes Frederick Philipse lord of a manor that runs from Spuyten Duyvil to the Croton River, with tenant farms and mills at Yonkers and on the Pocantico.', 41.0895, -73.8640, 12, 'Philipsburg Manor'),
 (1791, 11, 22, 'The Society for Useful Manufactures', 'Alexander Hamilton\'s Society for Establishing Useful Manufactures is chartered by New Jersey and chooses the Great Falls of the Passaic for a planned industrial city, Paterson. Its raceways drive cotton, locomotive and silk mills for 150 years.', 40.9160, -74.1810, 15, 'Society for Establishing Useful Manufactures'),
 (1798, 2, 23, 'Rockland County', 'The part of Orange County south of the Highlands becomes Rockland County, with its court house at New City.', 41.1476, -73.9893, 10, 'Rockland County, New York'),
 (1804, '', '', 'The Town of Jersey', 'The Associates of the Jersey Company buy Paulus Hook and lay out a town opposite Manhattan, the beginning of Jersey City. The same year John Stevens sells the first lots of Hoboken.', 40.7155, -74.0360, 15, 'Jersey City, New Jersey'),
 (1811, 10, 11, 'Stevens\'s Steam Ferry', 'John Stevens puts the Juliana on the run between Hoboken and Manhattan, the first steam ferry in regular service anywhere.', 40.7365, -74.0270, 14, 'Hoboken, New Jersey'),
 (1831, '', '', 'The Morris Canal', 'The canal from the Delaware reaches tidewater at Newark, lifting Lehigh coal over 23 inclined planes; it is carried across Bergen Neck to Jersey City in 1836.', 40.7330, -74.1640, 13, 'Morris Canal'),
 (1832, '', '', 'The Paterson and Hudson River Railroad', 'Horse-drawn cars begin running between Paterson and Acquackanonk; within a few years the line crosses the meadows to Jersey City behind steam locomotives.', 40.9140, -74.1670, 12, 'Paterson and Hudson River Railroad'),
 (1837, 3, 1, 'The Long Island Rail Road at Hicksville', 'The railroad from Brooklyn, meant as a short cut to Boston, stops for four years at Valentine Hicks\'s new village on the Hempstead Plains before pushing on to Greenport in 1844.', 40.7670, -73.5250, 12, 'Hicksville, New York'),
 (1840, 2, 22, 'Hudson County', 'The southern end of Bergen County - Jersey City and the townships of Bergen and Harrison - becomes Hudson County, the smallest county of New Jersey and soon the most crowded.', 40.7303, -74.0653, 11, 'Hudson County, New Jersey'),
 (1841, 9, 23, 'The Erie\'s Pier at Piermont', 'The New York and Erie Railroad, kept inside New York State by its charter, opens its first section, to Goshen, from the mile-long pier it built in the Tappan Zee in 1839, where passengers change to steamboats for the city.', 41.0420, -73.9000, 14, 'Erie Railroad'),
 (1846, 6, 19, 'Base Ball at the Elysian Fields', 'The Knickerbocker Base Ball Club plays the New York Nine on the Stevens family\'s pleasure grounds at Hoboken, the first recorded match under the Knickerbocker rules. The fields are built over by the 1890s.', 40.7497, -74.0270, 16, 'Elysian Fields (Hoboken, New Jersey)'),
 (1849, 9, 29, 'The Hudson River Railroad', 'Trains run from Manhattan up the east bank to Peekskill on a causeway that cuts off the river coves from Yonkers to Croton; the line reaches the Albany shore in 1851.', 41.2850, -73.9310, 11, 'Hudson River Railroad'),
 (1857, '', '', 'Llewellyn Park', 'Llewellyn Haskell and the architect Alexander Jackson Davis lay out a gated residential park on the slope of Orange Mountain, the first planned garden suburb in the country.', 40.7860, -74.2400, 14, 'Llewellyn Park'),
 (1869, '', '', 'Garden City', 'The merchant Alexander T. Stewart buys 7,000 acres of the Hempstead Plains from the town and builds a planned town with its own railroad.', 40.7268, -73.6343, 13, 'Garden City, New York'),
 (1870, '', '', 'Jersey City Takes the Ridge', 'Voters join Hudson City and the City of Bergen to Jersey City; Greenville follows in 1873. The Dutch town of 1660 becomes a neighbourhood.', 40.7282, -74.0776, 12, 'Jersey City, New Jersey'),
 (1889, '', '', 'The Communipaw Terminal', 'The Central Railroad of New Jersey opens its terminal on land made in Communipaw Cove. With the Erie, Pennsylvania, Lackawanna and West Shore terminals it lines the Hudson County shore with ferry houses and rail yards.', 40.7070, -74.0340, 14, 'Central Railroad of New Jersey Terminal'),
 (1895, '', '', 'The First County Park', 'Essex County creates the first county park commission in the United States and takes over Newark\'s reservoir tract as Branch Brook Park; South Mountain and Eagle Rock reservations follow.', 40.7650, -74.1750, 14, 'Branch Brook Park'),
 (1899, 1, 1, 'Nassau County', 'The three towns of Queens County left outside Greater New York - Hempstead, North Hempstead and Oyster Bay - become Nassau County, with its seat at Mineola.', 40.7407, -73.6410, 10, 'Nassau County, New York'),
 (1900, '', '', 'Saving the Palisades', 'New York and New Jersey create the Palisades Interstate Park Commission, which buys out the quarries that are blasting the cliffs.', 40.8900, -73.9390, 12, 'Palisades Interstate Park Commission'),
 (1906, '', '', 'New Croton Dam', 'The tallest dam in the world when it is finished drowns the Croton Dam of 1842 and stretches the city\'s reservoir far up the valley.', 41.2260, -73.8560, 13, 'New Croton Dam'),
 (1910, '', '', 'Harriman\'s Gift', 'Mary Averell Harriman gives 10,000 acres and a million dollars for a park in the Highlands on condition that the state give up the prison it is building at Bear Mountain.', 41.3120, -73.9890, 11, 'Harriman State Park (New York)'),
 (1915, 10, 20, 'Port Newark', 'Newark opens a ship channel and docks dredged out of the meadows on Newark Bay; the Port Authority takes them over in 1948.', 40.6900, -74.1500, 12, 'Port Newark–Elizabeth Marine Terminal'),
 (1916, 7, 30, 'Black Tom', 'German agents blow up the munitions depot on Black Tom Island at the Lehigh Valley Railroad\'s piers. The blast breaks windows across Manhattan and scars the Statue of Liberty.', 40.6920, -74.0550, 14, 'Black Tom explosion'),
 (1924, 11, 27, 'Bear Mountain Bridge', 'The first road bridge across the Hudson south of Albany, briefly the longest suspension span in the world, opens at the gate of the Highlands.', 41.3200, -73.9830, 13, 'Bear Mountain Bridge'),
 (1925, 11, 5, 'Bronx River Parkway', 'A landscaped motor road in a cleaned-up river valley opens from the Bronx to Kensico Dam, the first parkway of its kind. Westchester builds the Saw Mill, Hutchinson and Cross County parkways on its model.', 40.9900, -73.8070, 11, 'Bronx River Parkway'),
 (1927, 5, 20, 'Lindbergh Takes Off', 'Charles Lindbergh lifts the Spirit of St. Louis off the muddy runway of Roosevelt Field on the Hempstead Plains and lands in Paris 33 and a half hours later.', 40.7400, -73.6130, 13, 'Roosevelt Field (airport)'),
 (1928, 10, 1, 'Newark Airport', 'Newark opens an airfield on filled meadow beside its port; through the 1930s it is the busiest commercial airport in the world.', 40.6925, -74.1687, 12, 'Newark Liberty International Airport'),
 (1928, 10, '', 'Hutchinson River Parkway', 'The parkway is open from Pelham Manor to White Plains. Like the Saw Mill River Parkway begun in the same years, it follows a stream valley bought up as park land.', 40.9400, -73.8050, 11, 'Hutchinson River Parkway'),
 (1929, 8, 4, 'Jones Beach', 'Robert Moses opens a state park on a barrier beach raised with sand pumped from the bay, reached by the Wantagh causeway and, from the city, by the Southern State Parkway.', 40.5960, -73.5100, 12, 'Jones Beach State Park'),
 (1931, 11, 15, 'Bayonne Bridge', 'The longest steel arch in the world joins Bergen Point to Staten Island across the Kill Van Kull.', 40.6480, -74.1400, 14, 'Bayonne Bridge'),
 (1932, 11, 24, 'Pulaski Skyway', 'A viaduct five and a half kilometres long carries the highway from the Holland Tunnel over the Hackensack and Passaic rivers and the meadows between Jersey City and Newark.', 40.7370, -74.0920, 12, 'Pulaski Skyway'),
 (1937, 12, 22, 'Lincoln Tunnel', 'The first tube opens between Weehawken and Midtown, its looping approach cut into the Palisades. A second tube follows in 1945 and a third in 1957.', 40.7660, -74.0220, 14, 'Lincoln Tunnel'),
 (1947, 10, 1, 'Levittown', 'The first families move into Levitt and Sons\' houses on the potato fields of Island Trees. By 1951 there are 17,447 of them, the model of the post-war suburb.', 40.7259, -73.5143, 12, 'Levittown, New York'),
 (1951, 11, 5, 'New Jersey Turnpike', 'The toll road opens section by section from the Delaware; its northern end across the Newark and Hackensack meadows is finished in January 1952.', 40.7400, -74.1250, 11, 'New Jersey Turnpike'),
 (1954, 1, 13, 'Garden State Parkway', 'The first toll section opens in Union County; by 1957 the parkway runs from Cape May to the New York line through Union, Essex, Passaic and Bergen counties.', 40.6900, -74.2800, 10, 'Garden State Parkway'),
 (1955, 12, 15, 'Tappan Zee Bridge', 'The New York Thruway crosses the Hudson at its widest point, between Nyack and Tarrytown, and opens Rockland County to the suburbs.', 41.0700, -73.8900, 12, 'Tappan Zee Bridge (1955–2017)'),
 (1958, 8, 28, 'Palisades Interstate Parkway', 'The parkway along the top of the cliffs is finished from the George Washington Bridge to Bear Mountain, on land John D. Rockefeller Jr. bought up and gave in 1933.', 40.9500, -73.9300, 11, 'Palisades Interstate Parkway'),
 (1956, 4, 26, 'The First Container Ship', 'Malcom McLean\'s converted tanker Ideal X sails from Port Newark with 58 trailer boxes on deck. The Port Authority builds the Elizabeth terminal next door for his Sea-Land line, and within two decades the piers of Manhattan and Brooklyn stand empty.', 40.6850, -74.1500, 12, 'Port Newark–Elizabeth Marine Terminal'),
 (1976, 10, 10, 'The Meadowlands', 'Giants Stadium opens beside the new racetrack on filled marsh at East Rutherford, the centrepiece of the state\'s plan for the Hackensack Meadowlands; the arena follows in 1981.', 40.8135, -74.0745, 13, 'Meadowlands Sports Complex'),
 (2017, 8, 26, 'A New Tappan Zee Bridge', 'The first span of the Governor Mario M. Cuomo Bridge opens beside the bridge of 1955, which is taken down by 2019.', 41.0710, -73.8850, 12, 'Tappan Zee Bridge (2017–present)'),
]
def clean(x):
    x = re.sub(r'<ref[^>]*?/>', '', x); x = re.sub(r'<ref.*?</ref>', '', x, flags=re.S)
    return re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', x)
city = {r['title'] for r in csv.DictReader(open('/home/user/nyc/data/tables/events.csv', encoding='utf-8'))}
out = []; rep = []
for y, m, d, title, desc, lat, lon, zoom, wt in R:
    assert title not in city, title
    x = clean(wpc.text(wt) or '')
    if not x: rep.append(('NO ARTICLE', title, wt))
    if str(y) not in x: rep.append(('YEAR NOT IN ARTICLE', title, y))
    if m and d:
        full = [f'{MONTHS[m]} {d}, {y}', f'{d} {MONTHS[m]} {y}', f'{y}|{m}|{d}', f'{y}|{m:02d}|{d:02d}']
        if not any(s in x for s in full): rep.append(('day dropped', title, f'{y}-{m}-{d}')); d = ''
    if m and not d:
        if not re.search(rf'{MONTHS[m]}( \d{{1,2}},)? {y}|\d{{1,2}} {MONTHS[m]} {y}|{y}\|0?{m}\|', x): rep.append(('month dropped', title, f'{y}-{m}')); m = ''
    assert 40.47 <= lat <= 41.38 and -74.52 <= lon <= -73.40 and 9 <= zoom <= 18
    url = 'https://en.wikipedia.org/wiki/' + urllib.parse.quote(wt.replace(' ', '_'), safe="_,()'-.–:")
    out.append([y, m, d, title, desc, f'{lat:.4f}', f'{lon:.4f}', zoom, url])
out.sort(key=lambda o: (o[0], o[1] or 0, o[2] or 0))
assert len({o[3] for o in out}) == len(out)
with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['year', 'month', 'day', 'title', 'description', 'lat', 'lon', 'zoom', 'source_url']); w.writerows(out)
print(len(out), 'events; full date', sum(1 for o in out if o[2]), '; month', sum(1 for o in out if o[1] and not o[2]), '; year only', sum(1 for o in out if not o[1]))
for r in rep: print('  ', r)
