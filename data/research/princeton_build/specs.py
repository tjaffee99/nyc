SPEC=[]
def add(pre,name,year,url,note): SPEC.append((pre,name,year,url,note))
# --- NRHP contributing-property table, Princeton Historic District article (year column) ---
for pre,name,y,note in [
 ('0bcd3398','Joseph Henry House',1838,None),
 ('dc6477ab','Morven',1730,None),
 ('868ab9ba','University Cottage Club',1906,None),
 ('e80ed614','Bainbridge House',1766,None),
 ('3bdb1d0d','Beatty House',1780,'estimate: "ca. 1780"'),
 ('54b2c191','Nassau Club',1814,'"1813-14" in the table; completion year used'),
 ('2f325cb4','Palmer House',1823,None),
 ('8fa0669a','12 Morven Place',1830,'estimate: "c. 1830"'),
 ('aa0ce00e','Miller Chapel',1834,None),
 ('47ef9115','John Breckenridge House',1836,None),
 ('d3aaadcd','Nassau Presbyterian Church',1836,None),
 ('1ae9177e','40-42 Mercer Street',1839,None),
 ('bbdd4b69','Walter Lowrie House',1845,None),
 ('319d5e63','Ivy Hall',1846,None),
 ('2643e95e','Springdale',1851,None),
 ('33671818','Guernsey Hall',1855,'estimate: "1850s"'),
 ('213a06a2','Nassau Christian Center',1868,None),
 ('64f137c9','Trinity Church',1870,None),
 ('fbd721cc','Stuart Hall',1876,None),
 ('e2331a71','Murray Theater (Murray-Dodge Hall)',1879,'estimate: table gives Murray-Dodge Hall 1879; which wing is meant is not stated'),
 ('05aa5911','Dodge Hall (Murray-Dodge Hall)',1879,'estimate: table gives Murray-Dodge Hall 1879; which wing is meant is not stated'),
 ('63267d3c','32 Wiggins Street',1880,'estimate: "c. 1880"'),
 ('939a0c71','William Berryman Scott House',1888,None),
 ('ab20e57e','Tiger Inn',1895,None),
 ('0ecf825a','Old Princeton Bank and Trust',1896,None),
 ('d17714c4','Ivy Club',1897,None),
 ('9c590f2f','Thanet Lodge',1902,None),
 ('24ef0f31','Colonial Club',1906,None),
 ('aa6461e6','Cap and Gown Club',1908,None),
 ('32c72b43','Campus Club',1909,None),
 ('2b655ac1','Frist Campus Center',1909,'estimate: table dates the Palmer Physical Laboratory 1909; this footprint is that lab joined to the 2000-01 Frist addition'),
 ('a8564236','Cannon Dial Elm Club',1910,'table: Cannon Club 1910'),
 ('918361f7','Princeton United Methodist Church',1911,None),
 ('64d7e87a','Princeton University Press',1911,'estimate: table gives the 1911 building at 41 William St; the footprint is larger than that building'),
 ('03443d8b','Charter Club',1914,None),
 ('f9e5c681','Madison Hall',1916,'estimate: table row "University Dining Halls, Madison Hall, 1916"'),
 ('9308318a','Quadrangle Club',1916,None),
 ('f4a76b5b','Tower Club',1917,None),
 ('2885f3a6','Terrace Club',1920,None),
 ('d89e27e4','Princeton Battle Monument',1922,None),
 ('e3364d2d','Cloister Inn',1924,None),
 ('5f5551a0','Nassau Inn',1938,None),
 ('aeb82ebf','Nassau Inn (annex)',1938,'estimate: small annex footprint taken with the Nassau Inn of the table'),
]:
    add(pre,name,y,H,(note if note and note.startswith('estimate') else 'exact: '+(note+'; ' if note else '')+f'{y} in the contributing-properties table'))
# --- individual articles / Wikidata ---
SPEC[:] = [s for s in SPEC if s[0] != '0bcd3398']
add('0bcd3398','Joseph Henry House',1838,W('Joseph_Henry_House'),'exact: "designed the house in 1836 and lived there from its completion in 1838"')
add('35939728','Robertson Hall',1965,W('Princeton_School_of_Public_and_International_Affairs'),'exact: "completed in the fall of 1965" (Yamasaki; first named Woodrow Wilson Hall)')
add('3ffdf3a8','Hobey Baker Memorial Ice Rink',1923,W('Hobey_Baker_Memorial_Rink'),'exact: opened January 5, 1923 (infobox; Wikidata Q5875017 agrees)')
add('e1cca83e','Jadwin Gymnasium',1969,W('Jadwin_Gymnasium'),'exact: "The arena opened in 1969" (groundbreaking 1964)')
add('8113c576','McCarter Theater Center',1930,W('McCarter_Theatre'),'exact: "McCarter Theatre opened on February 21, 1930"; the Berlind Theater of 2003 is a later addition')
add('39096cd1','Mudd Library',1976,W('Seeley_G._Mudd_Manuscript_Library'),'exact: "dedicated on October 16, 1976"')
add('0e9f53b0','Garden Theater',1920,W('Princeton_Garden_Theatre'),'exact: "opened on September 20, 1920"')
add('c5d07c7b','Drumthwacket',1835,W('Drumthwacket'),'exact: "The mansion was built in 1835 and expanded in 1893 and 1900"')
add('f606bb7d','Tusculum',1773,W('Tusculum_(Princeton,_New_Jersey)'),'exact: infobox built 1773')
add('aa2ab999','Colross',1800,W('Colross'),'exact: "built in the Georgian architectural style between 1799 and 1800"')
add('08d85257','Fuld Hall',1939,W('Institute_for_Advanced_Study'),'exact: "moved into the newly built Fuld Hall in 1939"')
add('16c838d6','Princeton Public Library',2004,W('Princeton_Public_Library'),'exact: new library "opened at 65 Witherspoon Street in April 2004"')
add('81c40e94','Alexander Hall (Seminary)',1817,W('Princeton_Theological_Seminary'),'exact: "Alexander Hall ... opened in 1817" (built from 1814; the Historic District table says 1814)')
add('7c9d3762','Princeton Theological Seminary Library',2013,W('Princeton_Theological_Seminary'),'exact: "The current library building was completed in 2013"')
add('1065eb9f','Forbes College',1924,W('Forbes_College'),'estimate: Princeton Inn built 1923-24; the footprint also holds the New Wing (1946) and the Addition (after 1970)')
add('4020eba9','Witherspoon Hall',1877,W('Rockefeller_College'),'exact: "Witherspoon Hall, built in 1877"')
add('b9efa900','Bloomberg Hall (Butler College)',2004,W('Butler_College'),'exact: "Bloomberg Hall opened in 2004"')
add('856a3656','Fisher Hall (Whitman College)',2007,W('Whitman_College,_Princeton_University'),'exact: Whitman College "completed in the fall of 2007"; Fisher Hall is one of its seven dormitories')
add('693c7715','Whitman College quadrangle',2007,W('Whitman_College,_Princeton_University'),'estimate: matched by position (21 m from the article\'s coordinates for Whitman College, completed fall 2007); the footprint is not named')
add('40400b2f','Butler College new quad (a)',2009,W('Butler_College'),'estimate: matched by position (Butler quad; "the other dormitories opened in 2009"); not named')
add('04335862','Butler College new quad (b)',2009,W('Butler_College'),'estimate: matched by position (Butler quad; "the other dormitories opened in 2009"); not named')
for pre,nm in [('e196d038','Hariri'),('57976a0c','Fu'),('9a0c75c7','Addy & Aliya Kanji'),('7c6fbf65','Grousbeck'),('2b51393e','Kwanza Jones')]:
    add(pre,nm+' (Yeh / New College West)',2022,W('Yeh_College'),'estimate: matched by position inside Yeh College / New College West, "completed in 2022", opened September 2022')
add('ed67075a','Clio Hall',1893,WD('Q129116544'),'exact: Wikidata inception 1893 for the building (no article opened)')
add('510f804d','T.I.G.E.R.',2024,WD('Q133815721'),'exact: Wikidata inception 2024 (OpenStreetMap wikidata tag)')
add('04f9b306','Stone Hill Church of Princeton',2013,W('Stone_Hill_Church_of_Princeton'),'exact: new LEED facility "opened in December 2013" (dedicated March 9, 2014)')
add('4144a4d4','Stuart Country Day School',1963,W('Stuart_Country_Day_School'),'estimate: school established 1963 and its campus built at $2 million then; later additions not separated')
add('f9f6b328','Dinky Bar & Kitchen (1918 Princeton station)',1918,W('Princeton_station_(NJ_Transit)'),'exact: "The historic 1918 station was constructed ..."; the Dinky Bar opened in the old station in 2016')
for pre in ['c62be5fe','660c0b48','fec53d80']:
    add(pre,'Princeton Shopping Center ('+pre[:4]+')',1954,W('Princeton_Shopping_Center'),'estimate: the centre "opened on September 9, 1954"; matched by position (18-25 m from its coordinates); later additions not separated')
add('076ffd0c','Thomas Clarke House',1772,WD('Q124959558'),'exact: Wikidata inception 1772')
add('9534bd9d','Old Kingston Mill',1888,WD('Q110846840'),'exact: Wikidata inception 1888')
add('426e2cee','East Pyne Hall',1897,WD('Q121290057'),'exact: Wikidata inception 1897')
add('33dd14f3','Green Hall (John C. Green School of Science)',1874,WD('Q16997805'),'exact: Wikidata inception 1874 for the John C. Green School of Science; matched by position (0 m)')
add('39c37110','New Graduate College',1962,W('Princeton_University_Graduate_School'),'exact: "New Graduate College was built adjacent to the Old Graduate College in 1962"')
add('bb7b8e4d','Maybury Hill',1725,W('Maybury_Hill'),'estimate: "built about 1725"; matched by Wikidata coordinates (0 m)')
add('43458799','Marion Buckelew Cullen Center',2015,W('Westminster_Choir_College'),'estimate: article says "Opened in 2014" and elsewhere "completed by spring 2015"')
