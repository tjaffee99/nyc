"""Writes data/tables/parks_counties.csv (columns of parks.csv). `name` is the OpenStreetMap name of the outline
(checked against the Overture land-use extract of the region); the year is checked against the cited Wikipedia article:
a start year that is not in the article is written as `estimated`."""
import csv, os, re, sys, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import wpc
OUT = '/home/user/nyc/data/tables/parks_counties.csv'
E, X, Q = 'estimated', 'exact', 'exact if the year is in the article'
# name (OSM), start, end, start_event, planting_note, Wikipedia title, confidence wanted
R = [
 # ---------------------------------------------------------------- Essex County
 ('Branch Brook Park', 1895, 9999, 'The Essex County Park Commission, created in 1895 as the first county park commission in the country, took over Newark\'s reservoir tract that year: the first county park in the United States',
  'Swamp and old reservoir on the Morris Canal bank; Olmsted Brothers plan of 1900; extended north to Belleville in the 1920s; the cherry trees were given by Caroline Bamberger Fuld in 1927', 'Branch Brook Park', X),
 ('Weequahic Park', 1899, 9999, 'The Essex County Park Commission bought its first tract here in 1896 and by 1899 had the 265 acres of the Weequahic Reservation (the Waverly fairground and its lake); Olmsted Brothers design',
  'State agricultural fairground and trotting track (Waverly Fair) from 1866; 32 ha lake, the largest in the county; golf course 1913', 'Weequahic Park', Q),
 ('South Mountain Reservation', 1895, 9999, 'Land bought by the Essex County Park Commission from 1895, the largest of its reservations',
  'Second-growth oak forest between First and Second Watchung mountains, logged for the paper mills of Millburn before; Olmsted Brothers plan; Hemlock Falls; Washington Rock, a beacon site of 1780', 'South Mountain Reservation', X),
 ('Eagle Rock Reservation', 1895, 9999, 'Acquired by the Essex County Park Commission from 1895 on the crest of First Mountain',
  'Wooded ridge with the lookout over Newark and Manhattan; Olmsted Brothers; casino 1911; hill climb course of 1901-04', 'Eagle Rock Reservation', E),
 ('Verona Park', 1920, 9999, 'The Essex County Park Commission made its first purchases around the mill pond (Verona Lake) in 1920; Olmsted Brothers design',
  'Mill pond on the Peckman River dammed in 1814, a boating resort from the 1890s', 'Verona Park', Q),
 ('Military Park', 1667, 9999, 'Laid out as the Training Place, the militia drill ground of the Newark town plan of 1667; a town park from 1869',
  'Triangle on Broad Street; Wars of America monument by Gutzon Borglum 1926; underground garage 1960; restored 2014', 'Military Park (Newark)', E),
 ('Mount Pleasant Cemetery', 1844, 9999, 'Newark\'s rural cemetery on the Passaic, opened in 1844 (the outline of that name in Newark; another Mount Pleasant Cemetery lies in Westchester)',
  'Farmland above the river; Gothic gate 1877', 'Mount Pleasant Cemetery (Newark, New Jersey)', X),
 ('Fairmount Cemetery', 1855, 9999, 'Opened in 1855 on the western edge of Newark', 'Farmland on the South Orange road', 'Fairmount Cemetery (Newark, New Jersey)', X),
 # ---------------------------------------------------------------- Hudson County
 ('Liberty State Park', 1976, 9999, 'Opened on Flag Day, 14 Jun 1976, as New Jersey\'s bicentennial gift to the nation, on the abandoned yards of the Central Railroad of New Jersey and the Lehigh Valley',
  'Made land: tidal flats of Communipaw Cove filled for the railroad terminals between the 1860s and the 1920s (Black Tom lies inside it); terminal of 1889 restored; the interior was fenced off for decades because of chromium fill', 'Liberty State Park', X),
 ('Lincoln Park', 1905, 9999, 'West Side Park, the first park of the Hudson County Park Commission, opened in 1905 in Jersey City; renamed Lincoln Park in 1930 (several outlines in the region carry this name: this row is the one in Jersey City)',
  'Upland on the Bergen ridge and, across the highway, marsh of the Hackensack filled from the 1900s; designed by Daniel W. Langton and Charles N. Lowrie; Lincoln statue by James Earle Fraser 1930', 'Lincoln Park (Jersey City)', X),
 ('Stephen R. Gregg Bayonne Park', 1916, 9999, 'Hudson County park on Newark Bay (Bayonne Park), laid out by Charles N. Lowrie and opened about 1916 - year from memory, not in the cited article',
  'Bluff and filled shore of Newark Bay', 'Hudson County Park System', E),
 ('North Hudson Park', 1910, 9999, 'Hudson County park in North Bergen, created in 1910 (James J. Braddock North Hudson County Park since 1977)',
  'Wooded top of the Palisades with the 6 ha Woodcliff Lake', 'Hudson County Park System', Q),
 ('Holy Name Cemetery', 1866, 9999, 'Catholic cemetery of Jersey City, opened in 1866', 'Farmland on the west slope of Bergen Hill', 'Holy Name Cemetery (Jersey City, New Jersey)', X),
 # ---------------------------------------------------------------- Bergen County
 ('Palisades Interstate Park', 1900, 9999, 'The Palisades Interstate Park Commission was formed in 1900 to stop the quarrying of the cliffs and bought the first quarries at once; the park was dedicated on 27 Sep 1909 during the Hudson-Fulton Celebration (the dedication is not in the cited article)',
  'Cliff foot and talus woods; the trap-rock quarries were bought out from 1900 with J. P. Morgan\'s help; bathing beaches and boat basins 1910s-1940s; the Palisades Interstate Parkway runs along the top on land given by John D. Rockefeller Jr. in 1933', 'Palisades Interstate Park', X),
 ('Overpeck Park', 1954, 9999, 'Bergen County park on Overpeck Creek, on meadow given by Teaneck, Leonia, Palisades Park and Ridgefield Park in the 1950s; the last areas opened on a capped landfill in 2010',
  'Tidal marsh of Overpeck Creek, diked, dredged into a lake and filled with refuse from the 1950s', 'Overpeck County Park', Q),
 ('Van Saun County Park', 1957, 9999, 'Bergen County bought the Van Saun farm in 1957; the park and its zoo opened in 1960',
  'Farm on the Paramus-River Edge line; Washington Spring, where the Continental Army camped in September 1780', 'Van Saun County Park', Q),
 ('Saddle River County Park', 1965, 9999, 'Chain of parks along the Saddle River from Ridgewood to Rochelle Park assembled by Bergen County from the 1960s',
  'Flood plain of the Saddle River; mill ponds; Easton Tower (1900)', 'Saddle River County Park', E),
 # ---------------------------------------------------------------- Passaic County
 ('Garret Mountain Reservation', 1930, 9999, 'Acquired by the Passaic County Park Commission (created in 1927) around 1930; Olmsted Brothers plan',
  'Summit of First Watchung Mountain above Paterson; Lambert Castle (1892-93) and its tower (1896) stand on the slope', 'Garret Mountain Reservation', E),
 ('Eastside Park', 1888, 9999, 'Paterson bought the Van Buren property for its first large park in 1888 (the outline of that name in Paterson)',
  'Hillside above the Passaic; the mansion district of the silk manufacturers grew around it', 'Eastside Park (Paterson, New Jersey)', Q),
 ('Ringwood State Park', 1936, 9999, 'The Hewitt family gave Ringwood Manor and its grounds to the state in 1936; Skylands and Shepherd Lake were added in the 1960s',
  'Ironworks and charcoal woods from 1742 (Ringwood Company, Peter Hasenclever, Robert Erskine, then Cooper and Hewitt); the forest has grown back since the furnaces went out', 'Ringwood State Park', E),
 ('Cedar Lawn Cemetery', 1867, 9999, 'Paterson\'s rural cemetery, opened in 1867', 'Farmland on the Passaic below Dundee Lake', 'Cedar Lawn Cemetery', X),
 # ---------------------------------------------------------------- Union County
 ('Warinanco Park', 1925, 9999, 'First large park of the Union County Park Commission (created in 1921), designed by Olmsted Brothers; built 1923-1925',
  'Farmland and brook hollow on the Elizabeth-Roselle line; lake dug for the park', 'Warinanco Park', E),
 ('Watchung Reservation', 1921, 9999, 'The Union County Park Commission began buying the valley between First and Second Watchung mountains in the early 1920s',
  'Second-growth forest; mill village of Feltville (1845, the Deserted Village) and Lake Surprise on Blue Brook inside it; copper mine of the 18th century', 'Watchung Reservation', E),
 ('Evergreen Cemetery', 1853, 9999, 'Rural cemetery on the Elizabeth-Hillside line, opened in 1853 (two outlines in the region carry this name: this row is the one in Hillside)',
  'Farmland', 'Evergreen Cemetery (Hillside, New Jersey)', X),
 # ---------------------------------------------------------------- Westchester County
 ('Rye Playland', 1928, 9999, 'Opened on 26 May 1928 by the Westchester County Park Commission, which had bought out the Rye Beach and Paradise Park amusement resorts: the first planned amusement park in the country',
  'Beach and salt marsh of Manursing; Art Deco plan by Walker and Gillette with an 80-acre lake and boardwalk; Dragon Coaster 1929', 'Playland (New York)', X),
 ('Saxon Woods Park', 1925, 9999, 'Woodland bought by the Westchester County Park Commission in the mid-1920s along the Mamaroneck River and the Hutchinson River Parkway - year from memory; the cited county page gives no date',
  'Second-growth forest; golf course 1931, the large pool 1933', 'https://parks.westchestergov.com/saxon-woods-park', E),
 ('Tibbetts Brook Park', 1927, 9999, 'Opened in 1927, one of the first developed parks of the Westchester County park system',
  'Valley of Tibbetts Brook in Yonkers, with the Old Croton Aqueduct on its west side and the Putnam Division railroad through it; lakes and pool of 1927', 'Tibbetts Brook Park', X),
 ('Kensico Dam Plaza', 1917, 9999, 'Plaza laid out below the Kensico Dam, finished in 1917; a Westchester County park since 1963',
  'Valley of the Bronx River; the granite for the dam came from a quarry beside it; the village of Kensico lies under the reservoir', 'Kensico Dam', E),
 ('Rockefeller State Park Preserve', 1983, 9999, 'Given to the state by the Rockefeller family in 1983 out of their Pocantico Hills estate',
  'Fields and woods of the estate bought up by John D. Rockefeller from 1893, with his carriage roads; Swan Lake', 'Rockefeller State Park Preserve', X),
 ('Croton Point Park', 1923, 9999, 'Westchester County bought the point in 1923-24',
  'Peninsula of the Hudson: Kitchawank village site, 19th-century vineyards and brickyards of the Underhill family; the county\'s landfill covered its marsh from 1927 to 1986 and was capped as a meadow', 'Croton Point', E),
 ('Ward Pound Ridge Reservation', 1925, 9999, 'Westchester County bought the farms of the reservation in 1925; it was opened in 1938 after Civilian Conservation Corps work',
  'Some thirty abandoned hill farms reverting to forest; named in 1938 for William L. Ward', 'Ward Pound Ridge Reservation', Q),
 ('Glen Island Park', 1923, 9999, 'Westchester County bought the island in 1923-24; the Glen Island Casino opened in 1930',
  'John H. Starin\'s summer resort from 1879 to 1904, on five islands joined by fill; the castle of his "Little Germany" survives', 'Glen Island Park', Q),
 ('Sleepy Hollow Cemetery', 1849, 9999, 'Founded in 1849 as Tarrytown Cemetery beside the Old Dutch Church burying ground; renamed at Washington Irving\'s wish',
  'Hillside above the Pocantico River', 'Sleepy Hollow Cemetery', X),
 ('Kensico Cemetery', 1889, 9999, 'Founded in 1889 on the Harlem Railroad, when Manhattan\'s cemeteries were filling up', 'Farmland at Valhalla', 'Kensico Cemetery', X),
 ('Gate of Heaven Cemetery', 1917, 9999, 'Catholic cemetery opened in 1917 at Hawthorne, next to Kensico Cemetery (several outlines in the region carry this name: this row is the one in Mount Pleasant, Westchester)',
  'Farmland', 'Gate of Heaven Cemetery (Hawthorne, New York)', X),
 ('Ferncliff Cemetery', 1902, 9999, 'Founded in 1902 at Hartsdale', 'Farmland on Secor Road', 'Ferncliff Cemetery', X),
 ('Untermyer Park and Gardens', 1946, 9999, 'The core of Samuel Untermyer\'s Greystone gardens became a Yonkers city park in 1946, six years after his death',
  'Gardens designed from 1916 by William Welles Bosworth on the Tilden estate above the Hudson; walled Persian garden restored since 2011', 'Untermyer Park', Q),
 # ---------------------------------------------------------------- Rockland County
 ('Harriman State Park', 1910, 9999, 'Mary Averell Harriman gave 10,000 acres and one million dollars in 1910 on condition that the state give up the prison it was building at Bear Mountain',
  'Cut-over iron-furnace woods of the Ramapo Highlands; thirty-odd lakes, most of them dammed by the park; the Rockland part is the south-east of the park', 'Harriman State Park (New York)', X),
 ('Bear Mountain State Park', 1913, 9999, 'Opened in 1913 on the site cleared for the prison, with a steamboat dock; Bear Mountain Inn 1915, Bear Mountain Bridge 1924',
  'Hessian Lake and the ruins of Fort Clinton (1777); the hamlet of Doodletown inside it was bought out by 1965', 'Bear Mountain State Park', E),
 ('Hook Mountain State Park', 1911, 9999, 'The Palisades Interstate Park Commission began buying out the quarries of Hook Mountain in 1911',
  'Trap-rock quarries along the river, the last closed about 1920; ice-house landing of Rockland Lake', 'Hook Mountain State Park', Q),
 ('Nyack Beach State Park', 1911, 9999, 'Bought by the Palisades Interstate Park Commission in 1911 to stop the quarrying', 'Quarry and stone-crusher landing under Hook Mountain', 'Nyack Beach State Park', Q),
 ('Rockland Lake State Park', 1958, 9999, 'The Palisades Interstate Park Commission bought the lake and the village around it in 1958; the park opened in the 1960s',
  'Ice-harvesting village of the Knickerbocker Ice Company (1831-1924), cleared for the park', 'Rockland Lake State Park', Q),
 ('High Tor State Park', 1943, 9999, 'Bought in 1943 by public subscription to save the summit from quarrying, after Maxwell Anderson\'s play High Tor',
  'Summit of the Palisades ridge; Revolutionary beacon site; the Van Orden farm and vineyards on its slope', 'High Tor State Park', X),
 ('Tallman Mountain State Park', 1928, 9999, 'Bought by the Palisades Interstate Park Commission in 1928',
  'Palisades cliff above the Piermont marsh; the berms in the woods were built for an oil tank farm of the 1920s that was never finished', 'Tallman Mountain State Park', X),
 ('Blauvelt State Park', 1913, 9999, 'The state rifle range of 1910 (Camp Bluefields) was given up and handed to the Palisades Interstate Park Commission in 1913',
  'The concrete walls and tunnels of the rifle range stand in the woods', 'Blauvelt State Park', Q),
 ('Stony Point Battlefield State Historic Site', 1902, 9999, 'Opened as a state reservation in 1902 on the site of the fort stormed by Anthony Wayne in 1779',
  'Rocky point with the lighthouse of 1826; earthworks of the British fort', 'Stony Point Battlefield', X),
 # ---------------------------------------------------------------- Nassau County
 ('Jones Beach State Park', 1929, 9999, 'Opened on 4 Aug 1929, the showpiece of Robert Moses\'s Long Island State Park Commission',
  'Barrier beach raised some four metres with forty million cubic yards of sand pumped from the bay; planted with beach grass by hand; water tower and two bathhouses of 1929-31', 'Jones Beach State Park', X),
 ('Eisenhower Park', 1944, 9999, 'Nassau County took over the Salisbury Country Club for unpaid taxes in 1944 and dedicated it as Salisbury Park in 1949; renamed for Dwight D. Eisenhower in 1969',
  'Remnant of the Hempstead Plains; five golf courses of the Salisbury club (1917-1920s), where the PGA Championship was played in 1926', 'Eisenhower Park', Q),
 ('Bethpage State Park', 1934, 9999, 'The Long Island State Park Commission took over the Lenox Hills Country Club in 1934; four new golf courses by A. W. Tillinghast were built as relief work, the Black Course opening in 1936',
  'Yoakum estate and the club\'s golf course of 1923, on the moraine', 'Bethpage State Park', Q),
 ('Hempstead Lake State Park', 1925, 9999, 'One of the first Long Island state parks, on reservoir land transferred by New York City in 1925',
  'Storage reservoir of the Brooklyn Water Works, dammed 1873; the largest lake in Nassau County', 'Hempstead Lake State Park', Q),
 ('Valley Stream State Park', 1928, 9999, 'Opened in 1928 with the Southern State Parkway, on Brooklyn Water Works land transferred to the Long Island State Park Commission in 1925; the south part became a village park in 1958',
  'Watts Pond and the stream of the old water supply', 'Valley Stream State Park', Q),
 ('Old Westbury Gardens', 1959, 9999, 'Opened to the public in 1959', 'Westbury House (1906) of John S. Phipps, by George Crawley, with its walled garden and allees on the Hempstead Plains edge', 'Old Westbury Gardens', X),
 ('Planting Fields Arboretum', 1949, 9999, 'William Robertson Coe deeded the estate to the State of New York in 1949; open to the public after his death in 1955',
  'Estate laid out from 1913 (Olmsted Brothers from 1918): Coe Hall 1918-21, greenhouses, beeches moved from Massachusetts by barge', 'Planting Fields Arboretum State Historic Park', Q),
 ('Sagamore Hill National Historic Site', 1953, 9999, 'Theodore Roosevelt\'s house (1884-85) was opened to the public in 1953 by the Theodore Roosevelt Association and became a National Historic Site in 1962',
  'Farm and woods on Cove Neck', 'Sagamore Hill', E),
 ('Sands Point Preserve', 1971, 9999, 'Nassau County received the Guggenheim estate from the federal government in 1971',
  'Howard Gould\'s Castle Gould (1904) and Hempstead House (1912), then Daniel Guggenheim\'s estate; Navy training-device centre 1946-1967', 'Sands Point Preserve', Q),
]
def clean(x):
    x = re.sub(r'<ref[^>]*?/>', '', x); x = re.sub(r'<ref.*?</ref>', '', x, flags=re.S)
    return re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', x)
out = []; rep = []
for name, y0, y1, ev, plant, title, conf in R:
    web = title.startswith('http')
    x = '' if web else clean(wpc.text(title) or '')
    found = str(y0) in x
    if not x and not web: rep.append(('NO ARTICLE', name, title))
    if conf == Q: conf = X if found else E
    if conf == X and not found:
        conf = E; ev = ev + ' (year not found in the cited article)'; rep.append(('exact -> estimated', name, y0))
    if '--probe' in sys.argv and not found and x:
        ss = [s.strip().replace('\n', ' ') for s in re.split(r'(?<=[.!?])\s+', x) if re.search(r'open|establish|acquir|purchas|bought|dedicat|creat|founded|donat|deeded', s) and re.search(r'\b1[6-9]\d\d\b', s) and len(s) < 500 and '|' not in s[:30]]
        print('??', name, y0, '::', ' // '.join(s[:230] for s in ss[:3]))
    url = title if web else 'https://en.wikipedia.org/wiki/' + urllib.parse.quote(title.replace(' ', '_'), safe="_,()'-.–:")
    out.append([name, y0, y1, ev, plant, url, conf])
assert len({o[0] for o in out}) == len(out)
with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['name', 'start_year', 'end_year', 'start_event', 'planting_note', 'source_url', 'confidence']); w.writerows(out)
print(len(out), 'parks;', sum(o[6] == X for o in out), 'exact,', sum(o[6] == E for o in out), 'estimated')
for r in rep: print('  ', r)
