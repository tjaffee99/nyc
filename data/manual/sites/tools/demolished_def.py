"""Documented structures inside (or being) the sites that are gone: definitions for build_demolished.py.

D(id, name, start, end, lat, lon, height_m, storeys, material, shape, shape_note, src)
  shape   ("outline", [(lon, lat), ...])        a real outline (traced on the cited map, or a mapped block)
          ("local", cx, cy, [(x, y), ...])      the same, in metres east / north of (cx, cy) as read on the sheet
          ("circle", lon, lat, radius_m)        a gas holder read on the sheet
          ("rect", w, d, rotation_deg)          no outline known: footprint_m = WxD at lat / lon; w runs east-west
                                                at 0 and turns clockwise (the convention of pipeline/nyc_extras._rect)
  Everything not stated in the source says "estimated" in shape_note.
Sheets (USGS Historical Topographic Map Collection, public domain, read through tools/topo.py;
positions +-10 m):
  NARROWS54  The Narrows, NY 1:24,000, 1955 edition (aerial photographs 1954)
  BROOKLYN56 Brooklyn, NY 1:24,000, 1956 survey          BROOKLYN40  Brooklyn, NY 1:24,000, 1947 edition (photographs 1940)
  CPARK66    Central Park, NY 1:24,000, 1966
"""
T = "https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/NY/"
DEMOLISHED = []


def D(id, name, start, end, lat, lon, height_m, storeys, material, shape, shape_note, src):
    DEMOLISHED.append(dict(id=id, name=name, start=start, end=end, lat=lat, lon=lon, height_m=height_m, storeys=storeys,
                           material=material, shape=shape, shape_note=shape_note, src=src))


# ------------------------------------------------------------------ forts
D("fort_lafayette", "Fort Lafayette (Fort Diamond)", 1822, 1960, None, None, 14, "", "stone",
  ("local", -74.03861, 40.60833, [(17.5, 15), (77.5, 0), (65, -59), (6, -42.5)]),
  "Square casemated island fort (about 61 m a side, open parade), traced on the USGS The Narrows 1:24,000 sheet of "
  "1955 (photographs 1954), +-10 m; begun 1812, completed 1822, demolished 1960; height estimated (three tiers).",
  "Fort_Lafayette")
D("fort_gansevoort", "Fort Gansevoort (White Fort)", 1812, 1854, 40.73972, -74.00889, 6, "", "stone",
  ("rect", 60, 35, 28), "In use 1812-1849, demolished 1854 (the article's coordinates); size, shape, height and "
  "material estimated.", "Fort_Gansevoort")
D("fort_washington_1776", "Fort Washington (Fort Knyphausen)", 1776, 1783, 40.85278, -73.93806, 3, "", "earthwork",
  ("rect", 110, 80, 20), "Pentagonal earthwork of 1776 on the site of Bennett Park (West 183rd-185th Street, Fort "
  "Washington Avenue); taken 16 November 1776; end year estimated (the British evacuation); outline and height "
  "estimated.", "Fort_Washington_(Manhattan)")
D("fort_tryon_1776", "Fort Tryon (Forest Hill redoubt)", 1776, 1783, 40.86083, -73.9325, 3, "", "earthwork",
  ("rect", 50, 35, 20), "Outwork of Fort Washington (16 November 1776), named Fort Tryon by the British; end year, "
  "position within the park, outline and height estimated.", "Fort_Tryon_Park")
D("fort_putnam_1776", "Fort Putnam (Fort Greene)", 1776, 1847, 40.6919, -73.97547, 3, "", "earthwork",
  ("rect", 80, 60, 0), "Earthwork fort on the hill of today's Fort Greene Park, built under Nathanael Greene (the year 1776 is from "
  "the Fort Defiance article's account of Greene's forts, not stated in this one), refortified in the War of 1812 "
  "as Fort Greene; the hill became Washington Park in 1847 (end year = the park); outline and height estimated.",
  "Fort_Greene_Park")
D("fort_defiance_1776", "Fort Defiance (Red Hook)", 1776, 1783, 40.6763, -74.0157, 3, "", "earthwork",
  ("rect", 70, 50, 30), "Redoubt of 1776 at today's Conover and Van Dyke Streets; end year (the British "
  "evacuation), outline and height estimated.", "Fort_Defiance_(Brooklyn)")
D("cobble_hill_fort_1776", "Cobble Hill Fort (Corkscrew Fort; Fort Swift in 1812)", 1776, 1783, 40.6898, -73.9926, 3, "",
  "earthwork", ("rect", 40, 40, 0), "Fort on the conical hill at Atlantic Avenue, Pacific and Court Streets; the "
  "British cut off its top during the occupation (end year estimated); refortified as Fort Swift in the War of "
  "1812; outline and height estimated.", "Cobble_Hill,_Brooklyn")

# ------------------------------------------------------------------ gas holders
D("elmhurst_gas_holder_north", "Elmhurst gas tank (north holder, Newtown Holder Station)", 1910, 1996, None, None, 61, "",
  "steel", ("circle", -73.885220, 40.730351, 42),
  "Holder 200 ft tall (cited); circle of 84 m read on the USGS Brooklyn 1:24,000 sheet of 1956, +-10 m; the pair "
  "was built between 1910 and 1921 - which holder came first is estimated; dismantling began 1996.",
  "Elmhurst_gas_tanks")
D("elmhurst_gas_holder_south", "Elmhurst gas tank (south holder, Newtown Holder Station)", 1921, 1996, None, None, 61, "",
  "steel", ("circle", -73.884846, 40.729515, 42),
  "Holder 200 ft tall (cited); circle of 84 m read on the USGS Brooklyn 1:24,000 sheet of 1956, +-10 m; start "
  "year estimated (the pair was built between 1910 and 1921); dismantling began 1996.", "Elmhurst_gas_tanks")
for k, (lon, lat, r) in enumerate([(-73.978581, 40.734653, 25), (-73.977976, 40.734422, 18), (-73.977176, 40.734992, 12),
                                   (-73.977176, 40.734789, 12), (-73.974544, 40.733025, 18)], 1):
    D(f"gashouse_district_holder_{k}", "Gas holder, Gas House District (Consolidated Gas)", 1890, 1945, None, None, 30, "",
      "steel", ("circle", lon, lat, r),
      "Holder symbol read on the USGS Brooklyn 1:24,000 sheet of 1947 (photographs 1940), +-15 m and generalised; "
      "start year estimated (the district's tanks date from 1842 on and were many 'by the late 19th century'), end "
      "year estimated (clearance for Stuyvesant Town, 1945); height estimated.",
      "Stuyvesant_Town–Peter_Cooper_Village")

# ------------------------------------------------------------------ island institutions
D("goldwater_memorial_hospital", "Goldwater Memorial Hospital (Welfare Hospital for Chronic Diseases)", 1939, 2014, None,
  None, 20, "", "brick",
  ("local", -73.9575, 40.7535, [(-16.5, 66), (49.5, 165), (132, 275), (170.5, 297), (225.5, 264), (154, 187), (110, 110),
                                (49.5, 27.5), (11, 16.5)]),
  "Opened July 1939, closed 2013 (demolition year 2014 estimated); hull of the chevron pavilions traced on the USGS "
  "Central Park 1:24,000 sheet of 1966, +-10 m; height estimated.", "Roosevelt_Island")
D("city_hospital_roosevelt_island", "City Hospital (Charity Hospital)", 1861, 1994, None, None, 18, "", "stone",
  ("local", -73.9575, 40.7535, [(-115.5, -11), (-60.5, 0), (0, -66), (-5.5, -110), (-55, -110), (-121, -49.5)]),
  "Renwick's hospital completed 1861, closed 1957, demolished 1994; outline traced on the USGS Central Park "
  "1:24,000 sheet of 1966, +-10 m; height estimated.", "City_Hospital_(Roosevelt_Island)")
D("blackwells_island_penitentiary", "Blackwell's Island Penitentiary", 1830, 1936, 40.7549, -73.9563, 15, "", "stone",
  ("rect", 180, 18, -60), "Opened 3 August 1830; the inmates left and the jail was demolished by 1936, Goldwater "
  "hospital taking the ground; position, footprint and height estimated.", "Roosevelt_Island")

# ------------------------------------------------------------------ power, rail, works
D("pearl_street_station", "Pearl Street Station (Edison Electric Illuminating Company)", 1882, 1895, 40.70778, -74.00472,
  15, "", "brick", ("rect", 15, 30, -50), "255-257 Pearl Street on a lot of 50 by 100 ft (cited); generating from "
  "4 September 1882, burned 1890 and rebuilt, decommissioned 1895 (end = that year; the building's demolition was "
  "not researched); orientation, height and material estimated.", "Pearl_Street_Station")
D("waterside_station_buildings", "Waterside Generating Station (Nos. 1 and 2)", 1901, 2007, None, None, 40, "", "brick",
  ("blocks", [(-73.9719, 40.7455), (-73.9712, 40.7462)]),
  "No. 1 (38th-39th Street) October 1901, No. 2 (39th-40th Street) November 1906; decommissioned 2005 (demolition "
  "year estimated); outline: the two street blocks; height estimated.", "Waterside_Generating_Station")
D("st_johns_park_freight_depot", "St. John's Park Freight Depot (Hudson River Railroad)", 1868, 1927, 40.7212, -74.0075,
  15, "3", "brick", ("rect", 130, 125, 28), "Four-acre depot on the former park: construction began 1867 (start "
  "1868 estimated: the opening), demolished 1927; footprint from the 4 acres, storeys and height estimated.",
  "St._John's_Park")
D("havemeyers_elder_refinery_1856", "Havemeyers & Elder sugar refinery (first)", 1856, 1882, 40.7144, -73.9675, 25, "",
  "brick", ("rect", 100, 60, 28), "First Williamsburg refinery of 1856, replaced by the complex built 1882-83 on the "
  "west side of Kent Avenue between South 2nd and South 6th Streets; footprint, height and material estimated.",
  "Domino_Sugar_Refinery")
D("admirals_row", "Admiral's Row (ten officers' houses, Brooklyn Navy Yard)", 1864, 2016, 40.6979, -73.9792, 12, "3",
  "brick", ("rect", 220, 25, 8), "Ten houses built between 1864 and 1901, demolished 2016 but for one; the footprint "
  "is the row along Flushing Avenue: position, extent, storeys and height estimated.", "Admiral's_Row")

# ------------------------------------------------------------------ amusement
D("steeplechase_pavilion_of_fun", "Pavilion of Fun (Steeplechase Park)", 1908, 1966, 40.5745, -73.9843, 20, "", "steel",
  ("rect", 137, 85, 0), "Steel-and-glass hall of 450 by 280 ft (cited), opened in the 1908 season, demolished "
  "September 1966; position inside the park, orientation and height estimated.", "Steeplechase_Park")
D("dreamland_tower", "Dreamland tower (Beacon Tower)", 1904, 1911, 40.57444, -73.97694, 114, "", "steel",
  ("rect", 15, 15, 0), "Tower 375 ft high (cited; some sources 370 ft), opened 15 May 1904, burned 27 May 1911; "
  "position (the article's coordinates of the park), footprint and material estimated.", "Dreamland_(Coney_Island,_1904)")
