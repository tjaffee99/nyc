"""Researched years of standing buildings inside the sites (text sources).

B(id, name, year, src, note, locator)
  locator  ("osm", site_feature_id, name)  the building OpenStreetMap names so inside the site
           ("pt", lon, lat)                the footprint at / nearest to the point (within 60 m, largest)
  src      Wikipedia article title (cached in data/raw/sites/wp/) or URL
A row is not written where the built file already carries an LPC year within 5 years (the lead's
evidence order keeps LPC); build_buildings.py lists those.
Left out on purpose: Fort Jay's ramparts (no footprint of their own; the footprint at the point is
an 1830s barracks), the Squadron A Armory (only its front survives: the footprint is the 1970s
school behind it), the Army Terminal annex (same footprint as Building A in the city's data).
"""
BUILDINGS = []


def B(id, name, year, src, note, locator):
    BUILDINGS.append(dict(id=id, name=name, year=year, src=src, note=note, loc=locator))


GI = "governors_island_army_1904"
B("gi_castle_williams", "Castle Williams", 1811, "Castle_Williams", "Built 1807-1811.", ("osm", GI, "Castle Williams"))
B("gi_liggett_hall", "Liggett Hall (Building 400)", 1928, "Governors_Island", "Barracks built 1928 (photo caption and text).",
  ("osm", GI, "Liggett Hall"))
B("gi_admirals_house", "Admiral's House (Commanding Officer's Quarters)", 1843, "Governors_Island", "Completed 1843.",
  ("osm", GI, "Commanding Officer's Quarters"))

BAT = "brooklyn_army_base"
B("bat_building_a", "Brooklyn Army Terminal Building A", 1919, "Brooklyn_Army_Terminal", "Built May 1918 - September 1919.",
  ("osm", BAT, "Brooklyn Army Terminal Building A"))
B("bat_building_b", "Brooklyn Army Terminal Building B", 1919, "Brooklyn_Army_Terminal", "Built May 1918 - September 1919.",
  ("osm", BAT, "Brooklyn Army Terminal Building B"))

FW = "fort_wadsworth"
B("fw_battery_weed", "Battery Weed (Fort Richmond)", 1861, "Battery_Weed", "Built 1845-1861.", ("osm", FW, "Battery Weed"))
B("fh_casemate_fort", "Fort Hamilton casemate fort (Community Club)", 1831, "Fort_Hamilton",
  "Cornerstone 1825, completed 1831.", ("osm", "fort_hamilton", "Fort Hamilton Community Club"))
B("fh_caponier", "Fort Hamilton caponier (Harbor Defense Museum)", 1831, "Fort_Hamilton",
  "Part of the fort completed 1831 (estimated: the article dates the fort).", ("osm", "fort_hamilton", "Harbor Defense Museum"))
B("fs_fort_schuyler", "Fort Schuyler", 1856, "Fort_Schuyler", "Begun 1833, dedicated 1856.",
  ("osm", "fort_schuyler", "Fort Schuyler"))
B("bnh_main_building", "Brooklyn Naval Hospital, main building", 1838, "Brooklyn_Naval_Hospital",
  "Completed 1838, wings added 1840.", ("osm", "brooklyn_naval_hospital", "U.S. Naval Hospital"))
B("ssh_chapel", "Sailors' Snug Harbor chapel (Veterans Memorial Hall)", 1856, "Sailors'_Snug_Harbor",
  "Purpose-built chapel constructed 1856.", ("osm", "sailors_snug_harbor", "Veteran’s Memorial Hall Playhouse"))
B("ssh_music_hall", "Sailors' Snug Harbor Music Hall", 1892, "Sailors'_Snug_Harbor", "Music hall of 1892 (R. W. Gibson).",
  ("osm", "sailors_snug_harbor", "Music Hall"))

# Roosevelt Island (Blackwell's / Welfare Island)
RI = "welfare_island"
B("ri_smallpox_hospital", "Smallpox Hospital (ruin)", 1856, "Smallpox_Hospital",
  "Opened 1856 (wings 1903-05); a ruin since the 1950s, still standing.", ("osm", RI, "Smallpox Hospital"))
B("ri_strecker_laboratory", "Strecker Memorial Laboratory", 1892, "Strecker_Memorial_Laboratory", "Built 1892.",
  ("osm", RI, "Strecker Memorial Laboratory"))
B("ri_chapel_good_shepherd", "Chapel of the Good Shepherd", 1889, "Chapel_of_the_Good_Shepherd_(Roosevelt_Island)",
  "Built 1888, opened 1889.", ("osm", RI, "Church of the Good Shepherd"))
B("ri_blackwell_house", "Blackwell House", 1796, "Blackwell_House", "Built 1796-1804.", ("osm", RI, "Blackwell House"))

# armories (the article's coordinates; the drill hall is the footprint there)
for i, n, y, s, note, lon, lat in [
    ("armory_7th_regiment", "Seventh Regiment Armory (Park Avenue Armory)", 1880, "Seventh_Regiment_Armory", "Built 1877-1880.", -73.96611, 40.7675),
    ("armory_69th_regiment", "69th Regiment Armory", 1906, "69th_Regiment_Armory", "Built 1906.", -73.98417, 40.74139),
    ("armory_fort_washington_avenue", "Fort Washington Avenue Armory (22nd Regiment)", 1911, "Fort_Washington_Avenue_Armory", "Built 1911.", -73.94134, 40.84213),
    ("armory_369th_regiment", "369th Regiment Armory", 1924, "369th_Regiment_Armory", "Drill shed built 1921-1924; administration building 1930-1933.", -73.93472, 40.8175),
    ("armory_23rd_regiment", "23rd Regiment Armory (Bedford Atlantic Armory)", 1895, "23rd_Regiment_Armory", "Built 1891-1895.", -73.95444, 40.67861),
    ("armory_13th_regiment", "13th Regiment Armory (Sumner Armory)", 1894, "13th_Regiment_Armory", "Completed 1894.", -73.9375, 40.685),
    ("armory_14th_regiment", "14th Regiment Armory (Park Slope Armory)", 1895, "14th_Regiment_Armory", "Built 1891-1895.", -73.98333, 40.66278),
    ("armory_kingsbridge", "Kingsbridge Armory (Eighth Regiment)", 1917, "Kingsbridge_Armory", "Completed 1917.", -73.89856, 40.86791),
    ("armory_first_battery", "First Battery Armory", 1904, "First_Battery_Armory", "Built 1901-1904.", -73.9807, 40.773),
    ("armory_flushing", "Flushing Armory", 1906, "Flushing_Armory", "Built 1906.", -73.82889, 40.76306),
]:
    B(i, n, y, s, note, ("pt", lon, lat))

# works, power houses, terminals
B("irt_powerhouse", "IRT Powerhouse (59th Street)", 1905, "IRT_Powerhouse", "Constructed 1902-1905 (annex 1950).",
  ("pt", -73.99222, 40.77194))
B("american_bank_note_plant", "American Bank Note Company Printing Plant", 1911, "American_Bank_Note_Company_Printing_Plant",
  "Completed 1911.", ("pt", -73.89056, 40.81694))
B("starrett_lehigh_building", "Starrett-Lehigh Building", 1931, "Starrett–Lehigh_Building", "Completed 1931.",
  ("pt", -74.00667, 40.75167))
B("empire_stores", "Empire Stores", 1869, "Empire_Stores", "Completed 1869, additions 1885.", ("pt", -73.99165, 40.70361))
B("red_hook_grain_terminal", "Red Hook Grain Terminal", 1922, "Red_Hook_Grain_Terminal", "Built 1922 (opened 1 September).",
  ("pt", -74.00611, 40.66944))
B("domino_refinery_building", "Domino Sugar Refinery (filter, pan and finishing house)", 1883, "Domino_Sugar_Refinery",
  "Rebuilt 1882-1883 (complete by July 1883).", ("pt", -73.9675, 40.71444))
B("east_river_station_building", "East River Generating Station", 1926, "East_River_Generating_Station",
  "Began operating 23 November 1926.", ("pt", -73.97389, 40.72806))
