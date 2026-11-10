"""Rows for the counties around the city in data/tables/park_names.csv (parks, reservations,
cemeteries, vanished airfields: the first listed name dates the park — see
pipeline/ground_detail.py), data/tables/golf_courses.csv and data/tables/airports.csv.
Facts were read on 2026-11-10 from the English Wikipedia (wikitext, CC BY-SA: facts only, the
article URL per row), Wikidata (CC0, where a row says so) and Abandoned & Little-Known
Airfields (airfields-freeman.com: facts only, page URL per row). Points come from the
OpenStreetMap outline of that name in that county (Overture land-use extract; the largest
outline, plus one row per further outline of the name more than 1.2 km away).
Idempotent: rows with the same key are replaced, every other line of the tables is kept as is.
Run: .venv/bin/python data/manual/airports/tools/counties_tables.py"""
import csv, io, sys
from pathlib import Path
import numpy as np, pandas as pd, shapely
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "pipeline"))
from extent import in_extent  # noqa: E402
W = "https://en.wikipedia.org/wiki/"
FREEMAN = "https://www.airfields-freeman.com/"
idx = pd.read_parquet(ROOT / "data/interim/ground/lu_index.parquet")   # written by data/interim/ground/explore2.py
idx = idx[~idx.city & idx.cname.notna() & idx.name.notna()]
GREEN = ["park", "cemetery", "grave_yard", "zoo", "nature_reserve", "state_park", "national_park", "garden", "recreation_ground",
         "protected_landscape_seascape", "village_green", "theme_park"]

def points(name, county, classes):
    d = idx[(idx.name.str.strip() == name) & (idx.cname == county) & idx["class"].isin(classes)].sort_values("area", ascending=False)
    if d.empty:
        print("  !! no outline:", name, county); return []
    out = []
    for lo, la in zip(d.lon, d.lat):
        if all(np.hypot((lo - a) * 84.0, (la - b) * 111.0) > 1.2 for a, b in out):
            out.append((round(float(lo), 5), round(float(la), 5)))
    return out

# (OpenStreetMap name, county, [(label, from, to)], source, note)
PARKS = [
 ("Branch Brook Park", "Essex", [("Branch Brook Park", 1895, 9999)], W + "Branch_Brook_Park", "'The park was formally created ... in 1895, by the newly created Essex County Parks Commission, making it the nation's first county park.'"),
 ("Weequahic Park", "Essex", [("Weequahic Park", 1899, 9999)], W + "Weequahic_Park", "'In 1896, the Essex County Park Commission purchased a 28-acre tract ... By 1899, a total of 265 acres ... had been acquired, and what was then called Weequahic Reservation was established.' Labelled by today's name (the year of the change was not found)."),
 ("South Mountain Reservation", "Essex", [("South Mountain Reservation", 1895, 9999)], W + "South_Mountain_Reservation", "'The reservation was built from land purchases begun in 1895' (infobox: established 1895). The purchases ran on for years: the whole outline from 1895 is an estimate."),
 ("Orange Park", "Essex", [("Orange Park", 1900, 2006), ("Monte Irvin Orange Park", 2006, 9999)], W + "Orange_Park_(New_Jersey)", "'The property that became Orange Park was acquired in 1897'; 'the park informally opened to the public on August 25, 1900'; 'renamed in May 2006 for Orange resident and Hall of Famer Monte Irvin'."),
 ("Riverfront Park", "Essex", [("Newark Riverfront Park", 2012, 9999)], W + "Newark_Riverfront_Park", "'a groundbreaking took place in 2008, and the first phase of the park opened in 2012' (later phases 2013 and 2017 are not separated: estimated for those parts)."),
 ("Mills Reservation", "Essex", [("Mills Reservation", 1954, 9999)], W + "Mills_Reservation", "Infobox: created 1954; 'In 1952, David and Ella Mills of the Davella Mills Foundation purchased 118 acres of the land in order to preserve it, and donated it to Essex County.'"),
 ("Warinanco Park", "Union", [("Warinanco Park", 1925, 9999)], W + "Warinanco_Park", "Infobox: opened 1925; 'In 1923 ... the Olmsted Brothers ... completed its design plans for \"Elizabeth Park,\" now known as \"Warinanco.\"'"),
 ("Watchung Reservation", "Union", [("Watchung Reservation", 1921, 9999)], W + "Watchung_Reservation", "ESTIMATED: 'Soon after the Union County Park System was formed in 1921 ... this area was incorporated into the Watchung Reservation' — the year of the first purchase was not found; dated to the park commission's year."),
 ("Lincoln Park", "Hudson", [("West Side Park", 1905, 1930), ("Lincoln Park", 1930, 9999)], W + "Lincoln_Park_(Jersey_City)", "'Part of the Hudson County Park System, it opened in 1905 and was originally known as West Side Park.' The year of the renaming was not found in the article: the change of label in 1930 is ESTIMATED."),
 ("Liberty State Park", "Hudson", [("Liberty State Park", 1976, 9999)], W + "Liberty_State_Park", "'The park opened in 1976 to coincide with bicentennial celebrations' (infobox: open June 14, 1976), on the Central Railroad of New Jersey's yards."),
 ("Washington Park", "Hudson", [("Washington Park", 1917, 9999)], W + "Washington_Park_(Hudson_County)", "'Land for the park was acquired in 1917, which was further developed during the Works Progress Administration in the 1930s.'"),
 ("Pershing Field", "Hudson", [("Pershing Field", 1919, 9999)], W + "Pershing_Field", "'The park, originally planned in 1918 as Reservoir Park, opened for track and field events in 1919'."),
 ("Berry Lane Park", "Hudson", [("Berry Lane Park", 2016, 9999)], W + "Berry_Lane_Park", "'Construction of the park ... began in 2012 and the park officially opened in June 2016.'"),
 ("Stephen R. Gregg Bayonne Park", "Hudson", [("Bayonne Park", 1910, 9999)], W + "Stephen_R._Gregg_Park", "'The park was created in 1910 and encompasses an area of 167 acre.' Labelled Bayonne Park, the name the OpenStreetMap outline still carries (the year the county added Stephen R. Gregg's name was not found)."),
 ("Overpeck Park", "Bergen", [("Overpeck County Park", 1959, 9999)], W + "Overpeck_County_Park", "ESTIMATED: 'In 1954, the president of the Bergen County Park Commission ... proposed a plan to build a county park ... In the 1950s, Leonia, Palisades Park, Ridgefield Park, and Teaneck donated municipal land'; no opening year in the article — dated to the end of that decade. 'The project began in 2003 and the expanded park opened in 2010' (the Ridgefield Park area, not separated)."),
 ("Palisades Interstate Park", "Bergen", [("Palisades Interstate Park", 1900, 9999)], W + "Palisades_Interstate_Park_Commission", "Palisades Interstate Park Commission, 1900 (the article's register box: built 1900). The cliff-top and shore parcels were bought over the following decades: the whole outline from 1900 is an estimate."),
 ("Campgaw Mountain Reservation", "Bergen", [("Campgaw Mountain Reservation", 1961, 9999)], W + "Campgaw_Mountain_Reservation", "Infobox: created 1961."),
 ("Van Saun County Park", "Bergen", [("Van Saun County Park", 1960, 9999)], W + "Van_Saun_County_Park", "'In 1957, Bergen County purchased the farm from the Van Saun family'; infobox: created 1960."),
 ("High Mountain Park Preserve", "Passaic", [("High Mountain Park Preserve", 1993, 9999)], W + "High_Mountain_Park_Preserve", "'Established in 1993, it comprises 1153 acre of woodlands and wetlands'."),
 ("Eastside Park", "Passaic", [("Eastside Park", 1888, 9999)], W + "Eastside_Park_(Paterson,_New_Jersey)", "'occupied by the Van Buren family until 1888 when the property was purchased by the city' — dated by that purchase."),
 ("Goffle Brook Park", "Passaic", [("Goffle Brook Park", 1932, 9999)], W + "Goffle_Brook_Park", "Infobox: created 1932 (National Register box: built 1932; Olmsted Brothers for the Passaic County Park Commission)."),
 ("Rye Playland", "Westchester", [("Playland", 1928, 9999)], W + "Playland_(New_York)", "'The park began operation on May 26, 1928' (Westchester County's amusement park; the old Rye Beach amusement buildings were wrecked from Labor Day 1927)."),
 ("Tibbetts Brook Park", "Westchester", [("Tibbetts Brook Park", 1927, 9999)], W + "Tibbetts_Brook_Park", "'Opened in 1927, it was one of the first developed parks in Westchester County'."),
 ("Willsons Woods Park", "Westchester", [("Willson's Woods Park", 1924, 9999)], W + "Willson%27s_Woods_Park", "'Acquired in 1924, Willson's Woods is one of the oldest parks in the County's parks system' (pool and bathhouse 1927-28)."),
 ("Ward Pound Ridge Reservation", "Westchester", [("Pound Ridge Reservation", 1925, 1938), ("Ward Pound Ridge Reservation", 1938, 9999)], W + "Ward_Pound_Ridge_Reservation", "'In 1925, Westchester County acquired over 4,000 acres to form Pound Ridge Reservation. It was renamed in 1938 to honor William L. Ward'."),
 ("Rockefeller State Park Preserve", "Westchester", [("Rockefeller State Park Preserve", 1983, 9999)], W + "Rockefeller_State_Park_Preserve", "'the land was donated to the state of New York over time by the Rockefeller family beginning in 1983' (last parcel 2019: the whole outline from 1983 is an estimate)."),
 ("Croton Gorge Park", "Westchester", [("Croton Gorge Park", 1964, 9999)], W + "Croton_Gorge_Park", "Infobox: created 1964 (category: protected areas established in 1964), below the New Croton Dam."),
 ("Glen Island Park", "Westchester", [("Glen Island", 1881, 9999)], W + "Glen_Island_Park", "'The park, which opened in 1881, attracted thousands of people daily' — John H. Starin's summer resort; the year Westchester County made it a county park was not found (the resort's decline in between is not shown). Labelled Glen Island."),
 ("Teatown Lake Reservation", "Westchester", [("Teatown Lake Reservation", 1963, 9999)], W + "Teatown_Lake_Reservation", "'What began as a gift of 190 acre in 1963 has more than quintupled in size' (the article also says 'began in 1962, when 245 acres were donated'): later additions are not separated (estimated)."),
 ("Angle Fly Preserve", "Westchester", [("Angle Fly Preserve", 2006, 9999)], W + "Angle_Fly_Preserve", "'The land was purchased from a real estate developer in May 2006'; 'officially opened on October 3, 2009'."),
 ("Marshlands Conservancy", "Westchester", [("Marshlands Conservancy", 1972, 9999)], W + "Marshlands_Conservancy", "'the property reopened as Marshlands Park on June 7, 1972, during the dedication of the preserve'. Labelled by today's name."),
 ("Otter Creek Preserve", "Westchester", [("Otter Creek Preserve", 1974, 9999)], W + "Otter_Creek_Preserve", "Infobox: established 1974."),
 ("Ward Acres Park", "Westchester", [("Ward Acres Park", 1962, 9999)], W + "Ward_Acres_Nature_Preserve", "'New Rochelle purchased the land in 1962 with help from the New York State Park and Recreation Land Acquisition Bond Act.'"),
 ("Franklin D. Roosevelt State Park", "Westchester", [("Mohansic Park", 1922, 1982), ("Franklin D. Roosevelt State Park", 1982, 9999)], W + "Franklin_D._Roosevelt_State_Park", "'It was created in 1922 on the former site of the Mohansic State Hospital' (as Mohansic Park; the state 'first acquired the park land between 1909 and 1922'). The year of the present name was not found in the article: the change of label in 1982 is ESTIMATED."),
 ("Alfred B. DelBello Muscoot Farm", "Westchester", [("Muscoot Farm", 1975, 9999)], W + "Muscoot_Farm", "'Westchester County opened Muscoot Farm as an open-air interpretive museum and park in 1975.'"),
 ("Baxter Preserve, The Racetrack", "Westchester", [("Baxter Preserve", 1979, 9999)], W + "Baxter_Preserve", "'Baxter South land was donated to the North Salem Open Land Foundation (NSOLF) in 1979'."),
 ("Bear Mountain State Park", "Rockland", [("Bear Mountain State Park", 1913, 9999)], W + "Bear_Mountain_State_Park", "'in January 1909, the state purchased the 740 acre Bear Mountain tract ... The park opened in June 1913' (infobox: established 1913; the Palisades Interstate Park Commission took the land with the Harriman gift of 1910)."),
 ("Rockland Lake State Park", "Rockland", [("Rockland Lake State Park", 1958, 9999)], W + "Rockland_Lake_State_Park", "'Development of the park as part of the Palisades Interstate Park system began in 1958' (infobox: created 1958); the village was bought and cleared in the 1960s (not separated)."),
 ("Tallman Mountain State Park", "Rockland", [("Tallman Mountain State Park", 1928, 9999)], W + "Tallman_Mountain_State_Park", "Infobox: created 1928 (Palisades Interstate Park Commission)."),
 ("High Tor State Park", "Rockland", [("High Tor State Park", 1943, 9999)], W + "High_Tor_State_Park", "Infobox: created 1943 (category: protected areas established in 1943)."),
 ("Hook Mountain State Park", "Rockland", [("Hook Mountain State Park", 1911, 9999)], W + "Hook_Mountain_State_Park", "'the property was acquired to be a part of the Palisades Interstate Park in 1911' (infobox: created 1911; the quarries were bought out over the following years)."),
 ("Blauvelt State Park", "Rockland", [("Blauvelt State Park", 1913, 9999)], W + "Blauvelt_State_Park", "Category: protected areas established in 1913 (the former Camp Bluefields rifle range, to the Palisades Interstate Park Commission)."),
 ("Nyack Beach State Park", "Rockland", [("Nyack Beach State Park", 1911, 9999)], W + "Nyack_Beach_State_Park", "'The Palisades Interstate Park Commission purchased what was to become Nyack Beach State Park in 1911'."),
]
WD = "https://www.wikidata.org/wiki/"
CEMS = [
 ("Holy Cross Cemetery", "Bergen", [("Holy Cross Cemetery", 1915, 9999)], W + "Holy_Cross_Cemetery_(North_Arlington,_New_Jersey)", "'The cemetery was established in 1915 and now has 168 acre used for graves or developed for interment.'"),
 ("Kensico Cemetery", "Westchester", [("Kensico Cemetery", 1889, 9999)], W + "Kensico_Cemetery", "'It was founded in 1889, when many New York City cemeteries were becoming full'."),
 ("Sleepy Hollow Cemetery", "Westchester", [("Tarrytown Cemetery", 1849, 1865), ("Sleepy Hollow Cemetery", 1865, 9999)], W + "Sleepy_Hollow_Cemetery", "'Incorporated in 1849 as Tarrytown Cemetery, it was renamed Sleepy Hollow Cemetery in 1865.'"),
 ("Gate of Heaven Cemetery", "Westchester", [("Gate of Heaven Cemetery", 1917, 9999)], W + "Gate_of_Heaven_Cemetery_(Hawthorne,_New_York)", "'was established in 1917 at 10 West Stevens Avenue in Hawthorne'."),
 ("Ferncliff Cemetery", "Westchester", [("Ferncliff Cemetery", 1902, 9999)], W + "Ferncliff_Cemetery", "'It was founded in 1902, and is non-sectarian.'"),
 ("Rural Cemetery", "Westchester", [("White Plains Rural Cemetery", 1854, 9999)], W + "White_Plains_Rural_Cemetery", "'The cemetery was organized in 1854 and designed in 1855.'"),
 ("Beechwoods Cemetery", "Westchester", [("Beechwoods Cemetery", 1854, 9999)], W + "Beechwoods_Cemetery_(New_Rochelle,_New_York)", "'The cemetery was incorporated in 1854.'"),
 ("Oakland Cemetery", "Westchester", [("Oakland Cemetery", 1882, 9999)], W + "Oakland_Cemetery_(Yonkers,_New_York)", "'It was incorporated in 1875 and named Oakland Cemetery in 1882.' The older churchyard on the ground ('established around 1783') is not labelled."),
 ("Dale Cemetery", "Westchester", [("Dale Cemetery", 1851, 9999)], W + "Dale_Cemetery", "'the Dale Cemetery Association ... was incorporated on January 16, 1851; it was dedicated in October 1851.'"),
 ("Holy Sepulchre Cemetery", "Westchester", [("Holy Sepulchre Cemetery", 1886, 9999)], W + "Holy_Sepulchre_Cemetery_(New_Rochelle,_New_York)", "'maintained by the Blessed Sacrament Church, whose pastor, Father McLoughlin, established it in 1886.'"),
 ("Greenwood Union Cemetery", "Westchester", [("Union Cemetery of Rye", 1837, 1902), ("Greenwood Union Cemetery", 1902, 9999)], W + "Greenwood_Union_Cemetery", "'The first cemetery on this site was established in 1837 and it was known as \"Union Cemetery of Rye\"'; 'Methodist Episcopal Church operated the cemetery from 1855 until 1902, when it transferred management to a Rural Cemetery Corporation' — the change of label in 1902 is ESTIMATED from that transfer."),
 ("Woodland Cemetery", "Essex", [("Woodland Cemetery", 1855, 9999)], W + "Woodland_Cemetery_(Newark,_New_Jersey)", "'Established in 1855 and active until the 1980s'."),
 ("Mount Olivet Cemetery", "Essex", [("Mount Olivet Cemetery", 1871, 9999)], W + "Mount_Olivet_Cemetery_(Newark)", "'founded in 1871'."),
 ("Mount Hebron Cemetery", "Essex", [("Mount Hebron Cemetery", 1863, 9999)], W + "Mount_Hebron_Cemetery_(Montclair,_New_Jersey)", "'Founded in February 1863 by citizens of Cranetown and Speertown (now Montclair and Upper Montclair)'."),
 ("Rosedale Cemetery", "Essex", [("Rosedale Cemetery", 1840, 9999)], W + "Rosedale_Cemetery_(Orange,_New_Jersey)", "Infobox: established 1840."),
 ("Fairmount Cemetery", "Essex", [("Fairmount Cemetery", 1855, 9999)], W + "Fairmount_Cemetery_(Newark,_New_Jersey)", "'It opened in 1855, shortly after the Newark City Council banned burials in the central city'."),
 ("Mount Pleasant Cemetery", "Essex", [("Mount Pleasant Cemetery", 1844, 9999)], W + "Mount_Pleasant_Cemetery_(Newark,_New_Jersey)", "'The cemetery itself was opened and incorporated in 1844'."),
 ("Holy Sepulchre Cemetery", "Essex", [("Holy Sepulchre Cemetery", 1859, 9999)], W + "Holy_Sepulchre_Cemetery_(East_Orange,_New_Jersey)", "'The cemetery was established in 1859 and is maintained by the Roman Catholic Archdiocese of Newark.'"),
 ("Flower Hill Cemetery", "Hudson", [("Flower Hill Cemetery", 1873, 9999)], W + "Flower_Hill_Cemetery_(North_Bergen,_New_Jersey)", "Infobox: established 1873."),
 ("Grove Church Cemetery", "Hudson", [("Grove Church Cemetery", 1847, 9999)], W + "Grove_Church_Cemetery", "Infobox: established 1847 (the Grove Reformed Church dates from 1843)."),
 ("Bayview Cemetery", "Hudson", [("Bayview Cemetery", 1848, 9999)], W + "Bayview_%E2%80%93_New_York_Bay_Cemetery", "Infobox: established 1848 (New York Bay Cemetery; today Bayview - New York Bay Cemetery)."),
 ("Brookside Cemetery", "Bergen", [("Brookside Cemetery", 1876, 9999)], W + "Brookside_Cemetery_(Englewood,_New_Jersey)", "'It was started in May 1876, by a group of Englewood residents who purchased 6 acre of land for a cemetery.'"),
 ("George Washington Memorial Park", "Bergen", [("George Washington Memorial Park", 1939, 9999)], W + "George_Washington_Memorial_Park_(Paramus,_New_Jersey)", "'It was established in 1939'."),
 ("Hillside Cemetery", "Bergen", [("Hillside Cemetery", 1882, 9999)], W + "Hillside_Cemetery_(Lyndhurst,_New_Jersey)", "'It was established in 1882.'"),
 ("Mount Moriah Cemetery", "Bergen", [("Mount Moriah Cemetery", 1910, 9999)], W + "Mount_Moriah_Cemetery_(Fairview,_New_Jersey)", "Infobox: established 1910."),
 ("Maryrest Cemetery", "Bergen", [("Maryrest Cemetery", 1935, 9999)], WD + "Q45576658", "Wikidata inception (P571) 1935; not checked against a second source."),
 ("Fairview Cemetery", "Union", [("Fairview Cemetery", 1868, 9999)], W + "Fairview_Cemetery_%26_Arboretum_(Westfield,_New_Jersey)", "'The cemetery was founded in 1868 and is 105 acres.'"),
 ("Rahway Cemetery", "Union", [("Rahway Cemetery", 1724, 9999)], W + "Rahway_Cemetery", "'the first burial in 1724 of John Frazee'; 'the First Presbyterian Cemetery ... was established circa 1741-1742' — dated by the first burial (the family ground: estimated extent)."),
 ("Cedar Lawn Cemetery", "Passaic", [("Cedar Lawn Cemetery", 1867, 9999)], W + "Cedar_Lawn_Cemetery", "'Cedar Lawn Cemetery officially opened in September 1867, and recorded its first burial on September 27, 1867.'"),
 ("Oak Hill Cemetery", "Rockland", [("Oak Hill Cemetery", 1848, 9999)], WD + "Q3880350", "Wikidata inception (P571) 1848; not checked against a second source."),
 ("Rockland Cemetery", "Rockland", [("Rockland Cemetery", 1847, 9999)], WD + "Q63366396", "Wikidata inception (P571) 1847; not checked against a second source."),
]
# rows with their own point (no outline of that name on the map): (key, label, from, to, lon, lat, ha, source, note)
POINTS = [
 ("Harriman State Park (Rockland County)", "Harriman State Park", 1910, 9999, -74.085, 41.215, 19650, W + "Harriman_State_Park_(New_York)", "Infobox: established 1910 (48,556 acres in Rockland and Orange counties). The park's OpenStreetMap outline centres outside the map (Orange County): label at a point in its Rockland part near Lake Welch, chosen by hand."),
 ("Newark Liberty International Airport", "Newark Metropolitan Airport", 1928, 1973, -74.1749, 40.6912, "", W + "Newark_Liberty_International_Airport", "'The airport opened on October 1, 1928, dubbed the Newark Metropolitan Airport.' (also plain Newark Airport; the article dates no change before 1973)"),
 ("Newark Liberty International Airport", "Newark International Airport", 1973, 2002, -74.1749, 40.6912, "", W + "Newark_Liberty_International_Airport", "'In 1973, the airport was renamed Newark International Airport.'"),
 ("Newark Liberty International Airport", "Newark Liberty International Airport", 2002, 9999, -74.1749, 40.6912, "", W + "Newark_Liberty_International_Airport", "'the airport's name was changed from Newark International Airport to Newark Liberty International Airport in 2002.'"),
 # vanished airfields: label only (no outline traced; positions as given by the source, to 2-3 decimals)
 ("Rockland Airport (New City)", "Rockland Airport", 1928, 1950, -73.97, 41.13, "", FREEMAN + "NY/Airfields_NY_Rockland.htm", "'The first official airport in Rockland County was opened officially on Memorial Day in 1928'; 'no longer depicted on the July 1950 NY Sectional Chart' — closing year ESTIMATED (by mid-1950). Position 41.13, -73.97 as given: approximate."),
 ("Miller Airport (West Nyack)", "Miller Airport", 1940, 1952, -73.95, 41.10, "", FREEMAN + "NY/Airfields_NY_Rockland.htm", "'Miller Airport was opened in 1940'; 'in 1952 after much pressure from the town, it closed' (site of the Palisades Center mall). Position as given: approximate."),
 ("Christie Airport (New City)", "Christie Airport", 1938, 1970, -73.98, 41.17, 24, FREEMAN + "NY/Airfields_NY_Rockland.htm", "Start ESTIMATED ('by then'): 'The 1938 Aviation Facilities in NY State ... described Christie Airport as having 2 sod runways'; 'In December 1969, the final flight out of the airport was taken'; '60 acre rectangular property'. Position as given: approximate."),
 ("Spring Valley Airport", "Spring Valley Airport", 1946, 1986, -74.02, 41.11, "", FREEMAN + "NY/Airfields_NY_Rockland.htm", "County Airpark, later Ramapo Valley Airport (N24): 'it formally opened in 1946'; 'regular operations ended in 1985, we still had a few planes operating there until March 1986'. Position as given: approximate."),
 ("Orangeburg Civil Air Patrol Airport", "Orangeburg Airport", 1953, 1966, -73.99, 41.04, "", FREEMAN + "NY/Airfields_NY_Rockland.htm", "Start ESTIMATED: leased 'When Millers Airport closed in 1952'; 'The field closed in the fall of 1966 due to the construction of Lake Tappan.' Position as given: approximate."),
 ("Ramapo Valley Airport (Mahwah)", "Ramapo Valley Airport", 1946, 1953, -74.162, 41.102, "", FREEMAN + "NJ/Airfields_NJ_NE.htm", "'Ramapo Valley Airport began operating in 1946'; 'evidently closed at some point in 1953' (a Ford plant took the site)."),
 ("Totowa-Wayne Airport", "Totowa-Wayne Airport", 1950, 1970, -74.247, 40.909, "", FREEMAN + "NJ/Airfields_NJ_NE.htm", "ESTIMATED both ends: 'The earliest reference ... was on the 1950 NY Sectional Chart'; 'A 1970 aerial view showed that a large industrial building had been constructed over the eastern portion of the runway'."),
 ("Westfield Airport (Clark)", "Westfield Airport", 1931, 1956, -74.319, 40.61, "", FREEMAN + "NJ/Airfields_NJ_Newark.htm", "Start ESTIMATED ('by then'): 'A 1931 aerial view depicted Westfield Airport as having 3 unpaved runways'; 'The last aeronautical chart depiction ... was on the June 1956 NY Sectional Chart' (houses and the Garden State Parkway took the site)."),
 ("Reynolds Field (Valhalla)", "Reynolds Field", 1937, 1955, -73.766, 41.10, "", FREEMAN + "NY/Airfields_NY_Westchester.htm", "'In 1937 Frank Reynolds opened some of the flat fields on his dairy farm as an airfield'; 'evidently closed at some point between 1954-55'."),
 ("Armonk Airport", "Armonk Airport", 1938, 1966, -73.71, 41.12, 29, FREEMAN + "NY/Airfields_NY_Westchester.htm", "Start ESTIMATED ('by then'): 'Arents Air Service began operating at Armonk Airport in November 1938'; 'closed at some point between 1965-66'; 72 acres. Position as given: approximate."),
 ("Croton Airpark", "Croton Airpark", 1947, 1974, -73.85, 41.235, "", FREEMAN + "NY/Airfields_NY_Westchester.htm", "ESTIMATED both ends: 'evidently established at some point between 1946-47'; 'evidently closed (again) at some point between 1972-75'."),
 ("Somers Airport", "Somers Airport", 1941, 1952, -73.68, 41.32, "", FREEMAN + "NY/Airfields_NY_Westchester.htm", "Stewart Airways Airport: 'evidently established at some point in 1941'; 'evidently closed ... at some point between 1951-52' (closed for part of the war: not shown). Position as given: approximate."),
 ("La Roe Airport (Bedford)", "La Roe Airport", 1929, 1932, -73.65, 41.20, 50, FREEMAN + "NY/Airfields_NY_Westchester.htm", "ESTIMATED both ends: 'evidently established at some point between 1925-29'; 'no longer depicted on the August 1932 NY Sectional Chart'; 124 acres. Position as given: approximate."),
 ("Peekskill Seaplane Base", "Peekskill Seaplane Base", 1941, 2007, -73.96, 41.248, "", FREEMAN + "NY/Airfields_NY_Westchester.htm", "Start ESTIMATED: 'evidently established at some point between 1940-41'; 'The seaplane base was removed from FAA records in 2007.'"),
]
# (OpenStreetMap name, county, year_open, source, note)
GOLF = [
 ("Shady Rest Country Club", "Union", 1900, W + "Shady_Rest_Country_Club", "'In 1900, the Westfield Country Club was organized as a golf club. It leased the land ..., built a 9-hole golf course'; 'opened the Shady Rest Country Club on July 28, 1921'; public course since 1964."),
 ("Canoe Brook Country Club", "Essex", 1902, W + "Canoe_Brook_Country_Club", "'founded in 1901'; 'The first nine holes opened for play in 1902; the second nine in 1905.' The second course is not dated in the article: the whole club from 1902 (ESTIMATED for the later holes)."),
 ("Canoe Brook Country Club North Course", "Essex", 1902, W + "Canoe_Brook_Country_Club", "'The first nine holes opened for play in 1902; the second nine in 1905.'"),
 ("Canoe Brook Country Club South Course", "Union", 1902, W + "Canoe_Brook_Country_Club", "ESTIMATED: the club's first course opened in 1902; the year of the South Course is not in the article."),
 ("Baltusrol Golf Course", "Union", 1895, W + "Baltusrol_Golf_Club", "'The club's original 9-hole course was designed by George Hunter in 1895 and expanded to 18 holes in 1898'; today's Upper and Lower courses 'officially opened for play in June 1922' (not separated)."),
 ("Galloping Hill Golf Course", "Union", 1928, W + "Galloping_Hill_Golf_Course", "Infobox: established 1928 (Union County's public course, Willard G. Wilkinson)."),
 ("Weequahic Golf Course", "Essex", 1914, W + "Weequahic_Golf_Course", "'the first nine holes were designed in 1913 by George Low, with the course opening for play in 1914' (the oldest public course in New Jersey; later holes not separated)."),
 ("Essex County Country Club", "Essex", 1916, W + "Essex_County_Country_Club", "ESTIMATED: 'In 1916, A.W. Tillinghast designed a new 18-hole course, called the \"Upper Course,\" on a 180 acres site on top of First Mountain, a few miles away from the original course' (club founded 1887); the opening year of that course is not in the article."),
 ("Upper Montclair Country Club", "Essex", 1928, W + "Upper_Montclair_Country_Club", "'The original 18-hole golf course and a new clubhouse opened in 1928' (club established 1901; rebuilt to 27 holes in the 1950s)."),
 ("East Orange Golf Course", "Essex", 1923, W + "Tom_Bendelow", "ESTIMATED: Tom Bendelow's list of designs gives 'East Orange GC ... 1923 ... East Orange, New Jersey'; the opening year was not checked."),
 ("Liberty National Golf Club", "Hudson", 2006, W + "Liberty_National_Golf_Club", "Infobox: established 2006 (on a former oil terminal)."),
 ("Bayonne Golf Club", "Hudson", 2006, WD + "Q141791189", "Wikidata inception (P571) 2006; not checked against a second source."),
 ("The Ridgewood Country Club", "Bergen", 1929, W + "Ridgewood_Country_Club", "'founded in 1890 in neighboring Ho-Ho-Kus, but has been at its current location since 1926'; course by A. W. Tillinghast, 1929 (infobox: established 1929)."),
 ("White Beeches Golf and Country Club", "Bergen", 1918, W + "White_Beeches_Country_Club", "'The course was built in 1918 and designed by Walter Travis.'"),
 ("Preakness Valley Golf Course", "Passaic", 1931, W + "Preakness_Valley", "ESTIMATED lower bound: 'Made public in 1931, this full service course is considered the first public golf course in Passaic County' — the private course the county took over is older (year not found)."),
 ("Dellwood Country Club", "Rockland", 1920, W + "Paramount_Country_Club", "Adolph Zukor's Mountain View Farm: A. W. Tillinghast's 'eighteen-hole golf course on the property, which opened in 1920'; a club since 1936 (Dellwood from 1948, Paramount Country Club today)."),
 ("Rockland Country Club", "Rockland", 1907, W + "Rockland_Country_Club", "'The club was incorporated in 1906 and commissioned Henry Stark to design a 9-hole course that was ready the following year'; 'an entirely new golf course that opened in 1930' (not separated)."),
 ("Sleepy Hollow Country Club", "Westchester", 1911, W + "Sleepy_Hollow_Country_Club", "'The country club was incorporated on May 11, 1911'; 'the club had Charles B. Macdonald and Seth Raynor design the first golf course in 1911'."),
 ("Trump National Golf Club Westchester", "Westchester", 1922, W + "Trump_National_Golf_Club_Westchester", "'In 1922, Devereux Emmet designed a course ... with eighteen holes, and thus Briarcliff Country Club was founded that year'; rebuilt for 'its 2002 reopening' (the closure before it is not shown)."),
 ("The Saint Andrew's Golf Club", "Westchester", 1897, W + "Saint_Andrew%27s_Golf_Club_(New_York)", "'The current site, the club's home since 1897' (club founded 1888 in Yonkers)."),
 ("Wykagyl Golf Club", "Westchester", 1905, W + "Wykagyl_Country_Club", "'Lawrence Van Etten ... laid out the original golf course when the club moved to New Rochelle in 1905.'"),
 ("Scarsdale Country Club", "Westchester", 1898, W + "Scarsdale_Golf_Club", "Scarsdale Golf Club, Hartsdale: 'The club contains the Scarsdale Golf Course, founded in 1898'."),
 ("Westchester Country Club", "Westchester", 1922, W + "Westchester_Country_Club", "'Founded in 1922 as a destination for sportsmen' (Walter Travis's courses)."),
 ("Rye Golf Club", "Westchester", 1921, W + "Rye_Golf_Club_(Rye,_New_York)", "'originally organized on July 1, 1921, as the Rye Country Club' (course by Devereux Emmet, 1921)."),
 ("Quaker Ridge Golf Club", "Westchester", 1916, W + "Quaker_Ridge_Golf_Club", "'The club was formed ... in 1916 by a group of businessmen who had acquired the land a year earlier from a smaller, financially strained club. The course was completed in 1918'."),
 ("Winged Foot Golf Club", "Westchester", 1923, W + "Winged_Foot_Golf_Club", "'The club was founded in 1921 ... and opened in June 1923.'"),
 ("Pelham Country Club", "Westchester", 1921, W + "Pelham_Country_Club", "Infobox: established 1921 (Devereux Emmet; Emmet's own list of courses in his article says 1908 for the club)."),
 ("Bedford Golf and Tennis Club", "Westchester", 1891, W + "Devereux_Emmet", "Devereux Emmet's list of courses: 'Bedford Golf and Tennis Club Bedford, New York, 1891' (the club's year; the present holes are not dated)."),
 ("Harrison Meadows Country Club", "Westchester", 1917, W + "Devereux_Emmet", "'Green Meadow Club, Rye, New York, 1917 - known today as Harrison Meadows Country Club ... formed in 1917 directly adjacent to Apawamis'."),
 ("Hampshire Country Club", "Westchester", 1927, W + "Devereux_Emmet", "Devereux Emmet's list of courses: 'Hampshire Country Club, Mamaroneck, New York, 1927'."),
 ("Leewood Golf Club", "Westchester", 1922, W + "Devereux_Emmet", "Devereux Emmet's list of courses: 'Leewood Golf Club (Eastchester (town), New York) 1922'."),
 ("Apawamis Golf Club", "Westchester", 1899, W + "Tom_Bendelow", "Tom Bendelow's list of designs: 'The Apawamis Club ... 1899 ... Rye, New York' (the club's present course)."),
]
# name (OpenStreetMap), opened, closed, source, notes, runway width m
AIRPORTS = [
 ("Newark Liberty International Airport", 1928, "", W + "Newark_Liberty_International_Airport", "'Construction ... began on April 1, 1928 ... a land reclamation project to create 68 acre of level ground ... upon which a 1600 ft runway was to be laid. The airport opened on October 1, 1928, dubbed the Newark Metropolitan Airport.' Army 1941-46, Port Authority from 1948. Runways, taxiways and terminal aprons by period: data/manual/airports/pavement_dates.csv (airport EWR, tools/ewr.py): 4R/22L November 1952, 4L/22R 1970, 11/29 by 1951 (ESTIMATED), Terminals A / B 1973, C 1988, new A 2022; the runways of 1928-1952 (the first 1,600 ft runway, 1/19, 6/24) are gone and NOT traced. Runways 150 ft wide ('4L/22R: 11,000 x 150 ft').", 46),
 ("Teterboro Airport", 1919, "", W + "Teterboro_Airport", "'Walter C. Teter (1863-1929) acquired the property in 1917 ... The first flight from the present airport site was made in 1919' (marked citation needed in the article; category: airports established in 1919). Port Authority from 1949. Today's two runways ('Runway 6-24 is 6,013 ft long and 150 ft wide') are drawn from 1919: their years were not found (ESTIMATED).", 46),
 ("Westchester County Airport", 1942, "", W + "Westchester_County_Airport", "'Westchester County Airport was built during World War II in 1942 as a home to an Air National Guard unit'; 'The first scheduled airline flights were by American Airlines in late 1949'. Runways '16/34 is 6,549 by 150 ft and 11/29 is 4,451 by 150 ft', both from 1942 (ESTIMATED: later lengthenings and the 1995 terminal apron are not separated).", 46),
 ("Essex County Airport", 1929, "", W + "Essex_County_Airport", "ESTIMATED: 'In April 1929 Essex Airport Corporation was formed by Walter Marvin and six other individuals. The intention of the company was to open an airport to serve Montclair' (Marvin Airport); the opening day is not in the article. Today's paved runways are drawn from 1929 (their years were not found).", ""),
 ("Linden Airport", 1942, "", W + "Linden_Airport", "'Construction of Linden Airport was started in the spring of 1942 and completed by October 1942' (Eastern Aircraft's Wildcat plant). 'The original airport with its intersecting runways and large hangar remained intact until 1998' — the runways removed in 1998 are not traced; 'runway, 9/27, is 4,140 by 100 feet'.", 30),
 # not drawn: no outline on today's map and none traced (labels: data/tables/park_names.csv)
 ("Rockland Airport (New City)", 1928, 1950, FREEMAN + "NY/Airfields_NY_Rockland.htm", "Vanished, label only (park_names.csv): 'opened officially on Memorial Day in 1928'; gone from the July 1950 chart (closing ESTIMATED). No outline traced: not drawn.", ""),
 ("Miller Airport (West Nyack)", 1940, 1952, FREEMAN + "NY/Airfields_NY_Rockland.htm", "Vanished, label only: 'opened in 1940'; 'in 1952 ... it closed'. No outline traced: not drawn.", ""),
 ("Christie Airport (New City)", 1938, 1970, FREEMAN + "NY/Airfields_NY_Rockland.htm", "Vanished, label only: in the 1938 state directory (start ESTIMATED), last flight December 1969. No outline traced: not drawn.", ""),
 ("Spring Valley Airport", 1946, 1986, FREEMAN + "NY/Airfields_NY_Rockland.htm", "Vanished (County Airpark / Ramapo Valley Airport N24), label only: 'formally opened in 1946'; last planes March 1986. It had paved runways; no outline traced: not drawn.", ""),
 ("Orangeburg Civil Air Patrol Airport", 1953, 1966, FREEMAN + "NY/Airfields_NY_Rockland.htm", "Vanished, label only: after 1952 (start ESTIMATED) to autumn 1966 (Lake Tappan). Turf strip; not drawn.", ""),
 ("Ramapo Valley Airport (Mahwah)", 1946, 1953, FREEMAN + "NJ/Airfields_NJ_NE.htm", "Vanished, label only: 'began operating in 1946', closed 1953. Unpaved; not drawn.", ""),
 ("Totowa-Wayne Airport", 1950, 1970, FREEMAN + "NJ/Airfields_NJ_NE.htm", "Vanished, label only: on the 1950 chart, built over by 1970 (both ESTIMATED); 'a single 2,850' paved Runway 11/29' by 1958-60. No outline traced: not drawn.", ""),
 ("Westfield Airport (Clark)", 1931, 1956, FREEMAN + "NJ/Airfields_NJ_Newark.htm", "Vanished, label only: on a 1931 air photo (start ESTIMATED), last charted June 1956. Unpaved; not drawn.", ""),
 ("Reynolds Field (Valhalla)", 1937, 1955, FREEMAN + "NY/Airfields_NY_Westchester.htm", "Vanished, label only: opened 1937, closed 1954-55. Unpaved; not drawn.", ""),
 ("Armonk Airport", 1938, 1966, FREEMAN + "NY/Airfields_NY_Westchester.htm", "Vanished, label only: in use by November 1938 (start ESTIMATED), closed 1965-66. Unpaved; not drawn.", ""),
 ("Croton Airpark", 1947, 1974, FREEMAN + "NY/Airfields_NY_Westchester.htm", "Vanished, label only: 1946-47 to 1972-75 (both ESTIMATED); a 1,400 ft paved runway, now Longview Road. No outline traced: not drawn.", ""),
 ("Somers Airport", 1941, 1952, FREEMAN + "NY/Airfields_NY_Westchester.htm", "Vanished, label only: 1941 to 1951-52. Unpaved; not drawn.", ""),
 ("La Roe Airport (Bedford)", 1929, 1932, FREEMAN + "NY/Airfields_NY_Westchester.htm", "Vanished, label only: 1925-29 to 1932 (both ESTIMATED). Unpaved; not drawn.", ""),
 ("Peekskill Seaplane Base", 1941, 2007, FREEMAN + "NY/Airfields_NY_Westchester.htm", "Vanished seaplane base, label only: 1940-41 (ESTIMATED) to 2007. No pavement.", ""),
]

def rewrite(path, header_add, key_cols, new_rows, ncol):
    lines = path.read_text().splitlines()
    head = lines[0]
    cols = next(csv.reader([head]))
    if header_add and header_add not in cols:
        head += "," + header_add; cols.append(header_add)
    ki = [cols.index(c) for c in key_cols]
    keys = {tuple(str(r[i]) for i in ki) for r in new_rows}
    keep = [ln for ln in lines[1:] if ln.strip() and tuple((next(csv.reader([ln])) + [""] * ncol)[i] for i in ki) not in keys]
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(new_rows)
    path.write_text("\n".join([head] + keep) + "\n" + buf.getvalue())
    return len(keep), len(new_rows)

pn = []
for osm, county, periods, url, note in PARKS + CEMS:
    for lo, la in points(osm, county, GREEN):
        for label, a, b in periods:
            pn.append([osm, label, a, b, lo, la, url, note, ""])
for key, label, a, b, lo, la, ha, url, note in POINTS:
    if not in_extent(np.array([shapely.Point(lo, la)]))[0]:
        print("  !! outside the map outline, left out:", key); continue
    pn.append([key, label, a, b, lo, la, url, note, ha])
print("park_names.csv (kept, added):", rewrite(ROOT / "data/tables/park_names.csv", "ha", ["park", "name", "from_year", "lon", "lat"], pn, 9))
gr = []
for osm, county, year, url, note in GOLF:
    d = idx[(idx.name.str.strip() == osm) & (idx.cname == county) & (idx["class"] == "golf_course")].sort_values("area", ascending=False)
    if d.empty:
        print("  !! no golf outline:", osm, county); continue
    for lo, la in zip(d.lon, d.lat):
        gr.append([osm, year, 9999, url, note, round(float(lo), 4), round(float(la), 4)])
print("golf_courses.csv (kept, added):", rewrite(ROOT / "data/tables/golf_courses.csv", "", ["name", "lon", "lat"], gr, 7))
ar = [[n, o, c, u, t, w] for n, o, c, u, t, w in AIRPORTS]
print("airports.csv (kept, added):", rewrite(ROOT / "data/tables/airports.csv", "runway_width_m", ["name"], ar, 6))
