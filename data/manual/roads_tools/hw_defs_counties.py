"""Researched opening years of the highways and parkways of the counties around the city (Hudson, Bergen,
Essex, Union, Passaic NJ; Westchester, Rockland NY), section by section. Same tuples as hw_defs.py:
(route_id, name, mode, Overture names, anchor A, anchor B, year_start, year_end, elevated, note, source_url).

Names: an Overture road name, or "ref:<network> <number>" = the segments of a numbered route ("ref0:" = only
its unnamed segments; fetch_refs.py) — most New Jersey highways have no name in Overture.
Anchors: ("x", cross street / highway [, (lon, lat) hint]) | ("end", N/S/E/W) | ("endof", names, N/S/E/W) =
that end of another highway | ("border", county FIPS, N/S/E/W) = where the highway crosses the county line |
"far" (end to end) | "all" (every mainline segment with the name; CLIP = inside the counties listed).
Every year is from the page in source_url; `estimated` in a note marks a year or a section end that the
source does not state as such (a bound, a single year for a stretch opened in stages, an end taken at the
nearest crossing road). make_routes.py adds the other carriageway of each path.

REPLACED: rows of hw_defs.py that these rows supersede (they were cut at the edge of the old city extract)."""
W = "https://en.wikipedia.org/wiki/"
NR = "http://www.nycroads.com/roads/"
x = lambda s, hint=None: ("x", s, hint) if hint else ("x", s)
end = lambda d: ("end", d)
endof = lambda names, d: ("endof", names, d)
border = lambda fips, d: ("border", fips, d)
S = 9999
G = "ground"
HUDSON, BERGEN, ESSEX, UNION, PASSAIC, WESTCHESTER, ROCKLAND = "34017", "34003", "34013", "34039", "34031", "36119", "36087"

NJTP = {"New Jersey Turnpike"}
EAST = {"New Jersey Turnpike Eastern Spur"}
GSP = {"Garden State Parkway"}
PIP = {"Palisades Interstate Parkway"}
I78 = {"Phillipsburg–Newark Expressway", "Phillipsburg-Newark Expressway", "ref0:US:I:Express 78"}
I80 = {"Christopher Columbus Highway"}
I280 = {"Essex Freeway"}
THR = {"New York State Thruway"}
SMP = {"Saw Mill River Parkway"}
SBP = {"Sprain Brook Parkway"}
HUT = {"Hutchinson River Parkway"}
NJ19 = {"ref:US:NJ 19"}
NJ21 = {"ref:US:NJ 21"}
NJ24 = {"ref:US:NJ 24"}
NJ208 = {"ref:US:NJ 208"}
NJ495 = {"ref0:US:NJ 495"}
I684 = {"ref:US:I 684"}
US46 = "ref:US:US 46"

REPLACED = ["nj_turnpike", "palisades_parkway", "nys_thruway"]

# `all` rows: the stretch inside these counties
CLIP = {
    "taconic_westchester": [WESTCHESTER],
    "us1_9_newark": [ESSEX],
    "nj17_bergen": [BERGEN],
    "i287_nj_north": [PASSAIC, BERGEN],
}

DEFS = [
 # ---- New Jersey Turnpike (I-95) and its extensions
 ("njtp_main_15e", "New Jersey Turnpike: Woodbridge (exit 11) - Newark (exit 15E)", "freeway", NJTP | EAST, end("S"), x("Pulaski Skyway"), 1951.97, S, G,
  "Exit 11 in Woodbridge north to exit 15E in Newark opened 1951-12-20 (south of exit 11, outside the map, 1951-11-30). Exit 15E is taken where the turnpike passes under the Pulaski Skyway: estimated to a few hundred metres.", W + "New_Jersey_Turnpike"),
 ("njtp_east_15e_18", "New Jersey Turnpike (Eastern Spur): Newark (exit 15E) - Ridgefield (exit 18)", "freeway", EAST, x("Pulaski Skyway"), end("N"), 1952.04, S, G,
  "The fourth and final stretch, exit 15E north to exit 18 in Ridgefield, opened 1952-01-15 (with its bridges over the Passaic and the Hackensack).", W + "New_Jersey_Turnpike"),
 ("njtp_west_spur", "New Jersey Turnpike: Western Spur", "freeway", {"New Jersey Turnpike Western Spur"}, "far", None, 1970, S, G,
  "The Western Spur opened in 1970.", W + "New_Jersey_Turnpike"),
 ("njtp_i95_extension", "Interstate 95 (New Jersey Turnpike extension): US 46 - Interstate 80", "freeway", NJTP, endof(EAST, "N"), end("N"), 1971, S, G,
  "The portion of I-95 between the north end of the New Jersey Turnpike and I-80 opened in 1971.", W + "Interstate_95_in_New_Jersey"),
 ("i95_gwb_approach", "Interstate 95: Interstate 80 - George Washington Bridge (express and local roadways)", "freeway", {"New Jersey Turnpike Local Roadway", "New Jersey Turnpike Express Roadway"}, "all", None, 1964, S, G,
  "In 1964 the approach to the George Washington Bridge, shared with US 1-9 and US 46, was rebuilt into a freeway that became part of I-95 (connecting to I-80 in Teaneck).", W + "U.S._Route_46"),
 ("njtp_newark_bay_extension", "New Jersey Turnpike: Newark Bay (Hudson County) Extension, with the Newark Bay Bridge", "freeway", {"New Jersey Turnpike Newark Bay Extension"}, "far", None, 1956.26, S, G,
  "The 8.2-mile extension with the Newark Bay Bridge was completed 1956-04-04 (the Pulaski Skyway article has it open through to the Holland Tunnel in September 1956: the earlier date is used for the whole extension, estimated for its Jersey City end).", W + "New_Jersey_Turnpike"),
 # ---- Garden State Parkway
 ("gsp_27_cranford", "Garden State Parkway: Route 27 - Cranford", "highway", GSP, end("S"), x("North Avenue East"), 1950.49, S, G,
  "The first section, Route 27 north to Cranford, opened 1950-06-29 (the line starts at the edge of the map extract; south of Route 27, outside the map, 1954). The Cranford end is taken at Route 28 (North Avenue): estimated.", W + "Garden_State_Parkway"),
 ("gsp_cranford_22", "Garden State Parkway: Cranford - US 22 (Union)", "highway", GSP, x("North Avenue East"), x("ref:US:US 22"), 1953.54, S, G,
  "Extended north to Union Township 1953-07-16.", W + "Garden_State_Parkway"),
 ("gsp_22_irvington", "Garden State Parkway: US 22 - Mill Road (Irvington)", "highway", GSP, x("ref:US:US 22"), x("Mill Road", (-74.238, 40.716)), 1954.04, S, G,
  "The first tolled segment, US 22 to Mill Road, opened 1954-01-13.", W + "Garden_State_Parkway"),
 ("gsp_irvington_east_orange", "Garden State Parkway: Irvington - Central Avenue (East Orange)", "highway", GSP, x("Mill Road", (-74.238, 40.716)), x("Central Avenue", (-74.211, 40.753)), 1954.94, S, G,
  "Irvington to Central Avenue in East Orange opened 1954-12-09.", W + "Garden_State_Parkway"),
 ("gsp_east_orange_46", "Garden State Parkway: East Orange - US 46 (Clifton)", "highway", GSP, x("Central Avenue", (-74.211, 40.753)), x(US46, (-74.160, 40.878)), 1955.05, S, G,
  "Opened in pieces 1955-01-03 to 01-08 (Route 3 - Hazel Street in Clifton 01-04) and fully to US 46 on 1955-01-19.", W + "Garden_State_Parkway"),
 ("gsp_passaic_river", "Garden State Parkway: Clifton - US 46 in Elmwood Park (Passaic River bridge)", "highway", GSP, x(US46, (-74.160, 40.878)), x(US46, (-74.115, 40.897)), 1955.40, S, G,
  "The bridge over the Passaic River opened 1955-05-26, extending the parkway to US 46 in Elmwood Park.", W + "Garden_State_Parkway"),
 ("gsp_46_paramus", "Garden State Parkway: Elmwood Park - Route 17 (Paramus)", "highway", GSP, x(US46, (-74.115, 40.897)), x("ref:US:NJ 17"), 1955.50, S, G,
  "US 46 to Route 17 in Paramus opened 1955-07-01.", W + "Garden_State_Parkway"),
 ("gsp_paramus_state_line", "Garden State Parkway: Paramus - New York state line", "highway", GSP, x("ref:US:NJ 17"), end("N"), 1957.65, S, G,
  "The 12-mile extension through Bergen County opened 1957-08-25 (Wikipedia has a first part open on 1957-07-03).", NR + "garden-state/"),
 ("gsp_connector", "Garden State Parkway Connector (New York State Thruway)", "highway", {"Garden State Parkway Connector"}, "far", None, 1957.66, S, G,
  "The Thruway's Garden State Parkway Connector opened 1957-08-29.", W + "Garden_State_Parkway"),
 # ---- Palisades Interstate Parkway
 ("pip_new_jersey", "Palisades Interstate Parkway: George Washington Bridge - state line", "highway", PIP, end("S"), border(ROCKLAND, "S"), 1957.47, S, G,
  "The final section in New Jersey was completed at Alpine on 1957-06-22; the parkway opened section by section from the late 1940s and the earlier dates were not found: one year for the New Jersey stretch, estimated.", NR + "palisades/"),
 ("pip_exits_5_9", "Palisades Interstate Parkway: state line - New York State Thruway (exit 9)", "highway", PIP, border(ROCKLAND, "S"), x("New York State Thruway"), 1958.65, S, G,
  "The final five-mile section, exit 5 (NY 303) in Tappan to exit 9 (Thruway) in Nanuet, opened 1958-08-28; the two miles from the state line to exit 5 are given the same date: estimated.", NR + "palisades/"),
 ("pip_north", "Palisades Interstate Parkway: New York State Thruway - Bear Mountain", "highway", PIP, x("New York State Thruway"), end("N"), 1958.65, S, G,
  "Estimated, an upper bound: built from 1947-04-01 and opened section by section through the 1950s (dates not found); the whole parkway was open on 1958-08-28.", NR + "palisades/"),
 # ---- Interstate 78
 ("i78_41_48", "Interstate 78: Watchung (exit 41) - Route 24 (Springfield, exit 48)", "freeway", I78, border(UNION, "W"), x("ref:US:NJ 24"), 1986.6, S, G,
  "Exit 41 to exit 48 opened in 1986 (the five miles through the Watchung Reservation completed August 1986).", NR + "I-78_NJ/"),
 ("i78_48_turnpike", "Interstate 78: Route 24 (exit 48) - New Jersey Turnpike (Newark)", "freeway", I78, x("ref:US:NJ 24"), end("E"), 1977, S, G,
  "Exit 48 to exit 59 opened between 1974 and 1977 (the later year for the whole stretch: estimated).", NR + "I-78_NJ/"),
 # ---- Interstate 80
 ("i80_280_23", "Interstate 80: Interstate 280 (Parsippany) - Route 23 (Wayne)", "freeway", I80, x("Essex Freeway"), x("ref:US:NJ 23"), 1968, S, G,
  "Exit 47 (I-280) to exit 53 (Route 23 / US 46) in Wayne opened in 1968.", NR + "I-80_NJ/"),
 ("i80_23_paterson", "Interstate 80: Route 23 (Wayne) - Paterson", "freeway", I80, x("ref:US:NJ 23"), x("McLean Boulevard"), 1971, S, G,
  "By 1971 the section between Wayne and Paterson was completed. Its Paterson end is taken at Route 20 (McLean Boulevard): estimated.", W + "Interstate_80_in_New_Jersey"),
 ("i80_paterson_gsp", "Interstate 80: Paterson - Garden State Parkway (Saddle Brook)", "freeway", I80, x("McLean Boulevard"), x("Garden State Parkway"), 1966, S, G,
  "By 1966 I-80 had been completed from Paterson to I-95 (nycroads.com: exit 53 - exit 62 opened in stages between 1965 and 1971). Estimated: 'by 1966'; the Paterson end is taken at Route 20 (McLean Boulevard).", W + "Interstate_80_in_New_Jersey"),
 ("i80_gsp_95", "Interstate 80: Garden State Parkway - Interstate 95 (Teaneck)", "freeway", I80, x("Garden State Parkway"), end("E"), 1964, S, G,
  "Exit 62 to exit 68 (I-95) opened in 1964.", NR + "I-80_NJ/"),
 # ---- Interstate 280
 ("i280_west", "Interstate 280: Interstate 80 (Parsippany) - Clifton Avenue (Newark)", "freeway", I280, end("W"), x("Clifton Avenue"), 1973, S, G,
  "Opened in stages between 1966 and 1973; fully open west from Newark to I-80 in 1973 (the later year for the whole stretch: estimated).", W + "Interstate_280_(New_Jersey)"),
 ("i280_route58_west", "Interstate 280 (Route 58): Clifton Avenue - Broad Street (Newark)", "freeway", I280, x("Clifton Avenue"), x("Broad Street"), 1954, S, G,
  "In 1954 an extension of Route 58 opened west beyond Clifton Avenue to Orange Street (the freeway took over its line).", W + "Interstate_280_(New_Jersey)"),
 ("i280_stickel_bridge", "Interstate 280 (Route 25A / 58): Broad Street - Harrison Avenue (Stickel Bridge over the Passaic)", "freeway", I280, x("Broad Street"), x("Harrison Avenue"), 1949, S, G,
  "The Stickel Memorial Bridge opened in 1949, with approaches east to Harrison Avenue in Harrison and west beyond Route 21 to Broad Street.", W + "Interstate_280_(New_Jersey)"),
 ("i280_east", "Interstate 280: Harrison - New Jersey Turnpike", "freeway", I280, x("Harrison Avenue"), end("E"), 1980, S, G,
  "The portion east of Newark to the New Jersey Turnpike opened in 1980.", W + "Interstate_280_(New_Jersey)"),
 # ---- Interstate 287
 ("i287_nj_north", "Interstate 287: Montville - New York state line (Passaic and Bergen counties)", "freeway", {"Middlesex Freeway", "ref0:US:I 287"}, "all", None, 1993.88, S, G,
  "The missing section between US 202 in Montville and the New York State Thruway in Suffern opened 1993-11-19.", W + "Interstate_287"),
 ("cross_westchester", "Cross Westchester Expressway (Interstate 287)", "freeway", {"Cross Westchester Expressway"}, "far", None, 1960.92, S, G,
  "The entire 11.3-mile expressway, Thruway (Elmsford) to the New England Thruway, was completed in December 1960.", NR + "cross-westchester/"),
 # ---- New York State Thruway (I-87 / I-287) and the Tappan Zee Bridge
 ("thruway_north_of_suffern", "New York State Thruway: Orange County line - Suffern", "freeway", THR, end("N"), x("Orange Avenue"), 1955.50, S, G,
  "Harriman - Hillburn opened 1955-05-27 and Hillburn - Suffern (one mile) 1955-07-01: the later date for the stretch (estimated for the part north of Hillburn); Suffern is taken at US 202 (Orange Avenue).", NR + "thruway/"),
 ("thruway_suffern_nyack", "New York State Thruway: Suffern - Nyack", "freeway", THR, x("Orange Avenue"), x("South Highland Avenue"), 1955.96, S, G,
  "Suffern - Yonkers (27 miles), with the Tappan Zee Bridge, opened 1955-12-15.", NR + "thruway/"),
 ("tappan_zee_bridge", "Tappan Zee Bridge (replaced by the Governor Mario M. Cuomo Bridge)", "bridge", THR, x("South Highland Avenue"), x("South Broadway", (-73.862, 41.063)), 1955.96, S, G,
  "The first Tappan Zee Bridge opened 1955-12-15. Its replacement, on a parallel line just to the north, opened to westbound traffic 2017-08-26 and its second span 2018-09-11; the line drawn is today's bridge (the crossing is shown from 1955).", W + "Tappan_Zee_Bridge_(1955–2017)"),
 ("thruway_tarrytown_yonkers", "New York State Thruway: Tarrytown - Yonkers", "freeway", THR, x("South Broadway", (-73.862, 41.063)), x("Cross County Parkway (express lanes)"), 1955.96, S, G,
  "Suffern - Yonkers opened 1955-12-15. The Yonkers end ('three miles from the Bronx') is taken at the Cross County Parkway: estimated.", NR + "thruway/"),
 ("thruway_yonkers_bronx", "New York State Thruway: Yonkers - Bronx line", "freeway", THR, x("Cross County Parkway (express lanes)"), end("S"), 1956.67, S, G,
  "The last segment, Yonkers south to the Bronx, was completed 1956-08-31.", W + "New_York_State_Thruway"),
 ("new_england_thruway", "New England Thruway", "freeway", {"New England Thruway"}, "far", None, 1958.79, S, G,
  "Opened 1958-10-15 from Pelham Parkway to the Connecticut line.", NR + "new-england/"),
 # ---- Interstate 684
 ("i684_287_armonk", "Interstate 684: White Plains (I-287) - Armonk", "freeway", I684, end("S"), x("Bedford Road", (-73.704, 41.124)), 1968.79, S, G,
  "The southernmost section, White Plains - Armonk, opened in October 1968.", W + "Interstate_684"),
 ("i684_armonk_bedford_hills", "Interstate 684: Armonk - Bedford Hills (Saw Mill River Parkway)", "freeway", I684, x("Bedford Road", (-73.704, 41.124)), x("Saw Mill River Parkway"), 1970, S, G,
  "The segment between Armonk and Bedford Hills opened in 1970.", W + "Interstate_684"),
 ("i684_north", "Interstate 684: Bedford Hills - Brewster", "freeway", I684, x("Saw Mill River Parkway"), end("N"), 1974.95, S, G,
  "Estimated: the final segment was completed in December 1974 (the article has Purdys - Brewster open in 1969 in one sentence and Goldens Bridge - Brewster completed December 1974 in another; Katonah - Goldens Bridge was Route 22's four-lane highway before): the completion date is used north of Bedford Hills.", W + "Interstate_684"),
 # ---- Westchester parkways
 ("bronx_river_1925", "Bronx River Parkway: Bronx Park - Kensico Dam", "highway", {"Bronx River Parkway"}, x("Allerton Avenue"), end("N"), 1925, S, G,
  "Completed 1925 (the first sections 1922); the split from the 1950-52 extension at Allerton Ave, the north end of Bronx Park, is estimated.", NR + "bronx-river/"),
 ("hutchinson_westchester", "Hutchinson River Parkway: Boston Post Road - Westchester Avenue (White Plains)", "highway", HUT, x("Boston Post Road"), x("Westchester Avenue", (-73.727, 41.024)), 1928.8, S, G,
  "Pelham (US 1) - Westchester Avenue in White Plains, 11 miles, completed by October 1928 (a first two miles in Pelham December 1927).", NR + "hutchinson/"),
 ("hutchinson_north", "Hutchinson River Parkway: White Plains - King Street (Connecticut line)", "highway", HUT, x("Westchester Avenue", (-73.727, 41.024)), end("N"), 1937, S, G,
  "Extended north from White Plains to King Street in Rye Brook, on the Connecticut line, in 1937.", NR + "hutchinson/"),
 ("saw_mill_yonkers", "Saw Mill River Parkway: Bronx line - Tuckahoe Road (Yonkers)", "highway", SMP, end("S"), x("Tuckahoe Road"), 1926, S, G,
  "The first section, a short bypass of downtown Yonkers, was completed in 1926. Estimated: the source does not give its ends; the stretch from the city line to Tuckahoe Road (where the 1929 section began) is given that year.", NR + "saw-mill/"),
 ("saw_mill_tuckahoe_ashford", "Saw Mill River Parkway: Tuckahoe Road - Ashford Avenue (Dobbs Ferry)", "highway", SMP, x("Tuckahoe Road"), x("Ashford Avenue"), 1929.7, S, G,
  "Tuckahoe Road in Yonkers to Ashford Avenue in Dobbs Ferry, four miles, completed September 1929.", NR + "saw-mill/"),
 ("saw_mill_ashford_elmsford", "Saw Mill River Parkway: Dobbs Ferry - Elmsford (NY 119)", "highway", SMP, x("Ashford Avenue"), x("Cross Westchester Expressway"), 1930, S, G,
  "Dobbs Ferry to NY 119 (Tarrytown Road) in Elmsford completed in 1930 (the end is taken at the Cross Westchester Expressway, which crosses beside NY 119).", NR + "saw-mill/"),
 ("saw_mill_elmsford_chappaqua", "Saw Mill River Parkway: Elmsford - Chappaqua", "highway", SMP, x("Cross Westchester Expressway"), x("Quaker Road"), 1940, S, G,
  "Extended north to Chappaqua in 1940 (one year for a stretch built through the 1930s: estimated; Chappaqua is taken at Quaker Road, NY 120).", NR + "saw-mill/"),
 ("saw_mill_chappaqua_katonah", "Saw Mill River Parkway: Chappaqua - Katonah", "highway", SMP, x("Quaker Road"), end("N"), 1954, S, G,
  "World War II delayed completion to Katonah until 1954 (Wikipedia: the full length was opened in 1955).", NR + "saw-mill/"),
 ("sprain_south", "Sprain Brook Parkway: Bronx River Parkway - Tuckahoe Road", "highway", SBP, end("S"), x("Tuckahoe Road"), 1961.6, S, G,
  "The first leg, from the Bronx River Parkway to just north of Tuckahoe Road, was completed in 1961 (slated to open in August: month estimated).", W + "Sprain_Brook_Parkway"),
 ("sprain_tuckahoe_jackson", "Sprain Brook Parkway: Tuckahoe Road - Jackson Avenue", "highway", SBP, x("Tuckahoe Road"), x("Jackson Avenue"), 1963.98, S, G,
  "Opened 1963-12-23.", W + "Sprain_Brook_Parkway"),
 ("sprain_jackson_287", "Sprain Brook Parkway: Jackson Avenue - Cross Westchester Expressway", "highway", SBP, x("Jackson Avenue"), x("Cross Westchester Expressway"), 1969.90, S, G,
  "The 5.2-mile section from Jackson Avenue in Greenburgh to the Cross Westchester Expressway in Elmsford opened 1969-11-27.", W + "Sprain_Brook_Parkway"),
 ("sprain_north", "Sprain Brook Parkway: Cross Westchester Expressway - Taconic State Parkway", "highway", SBP, x("Cross Westchester Expressway"), end("N"), 1980.82, S, G,
  "The last piece of the parkway opened 1980-10-28.", W + "Sprain_Brook_Parkway"),
 ("taconic_westchester", "Taconic State Parkway (Bronx Parkway Extension): Kensico Dam - Putnam County line", "highway", {"Taconic State Parkway"}, "all", None, 1932, S, G,
  "The Bronx Parkway Extension from the Kensico Dam Plaza to the Bear Mountain Parkway and the spur north to the Westchester - Putnam line were completed in 1932 (Wikipedia has the ribbon cut at the Croton Reservoir bridge in December 1931).", NR + "taconic/"),
 ("bear_mountain_parkway", "Bear Mountain State Parkway", "highway", {"Bear Mountain Parkway"}, "all", None, 1932, S, G,
  "Built between 1929 and 1932 by the Westchester County Parks Commission; opened in 1932.", NR + "bear-mountain/"),
 ("bear_mountain_bridge", "Bear Mountain Bridge", "bridge", {"Bear Mountain Bridge"}, "all", None, 1924.91, S, G,
  "Formally opened 1924-11-27.", W + "Bear_Mountain_Bridge"),
 ("bear_mountain_bridge_road", "Bear Mountain Bridge Road (the bridge's approach from the Albany Post Road)", "highway", {"Bear Mountain Bridge Road"}, "all", None, 1924.91, S, G,
  "The bridge, formally opened 1924-11-27, included a three-mile approach road from the Albany Post Road north of Peekskill.", W + "Bear_Mountain_Bridge"),
 ("cross_county_parkway", "Cross County Parkway", "highway", {"Cross County Parkway", "Cross County Parkway (local lanes)", "Cross County Parkway (express lanes)"}, "all", None, 1932, S, G,
  "Estimated: construction began in 1929 and the northern wye to the Hutchinson River Parkway opened in 1932 (the year used for the mainline); the final portion was completed in 1947, the Wartburg connection in 1949, and the parkway was widened 1964-1984.", NR + "cross-county/"),
 # ---- New Jersey routes
 ("pulaski_skyway", "Pulaski Skyway", "freeway", {"Pulaski Skyway"}, "far", None, 1932.90, S, G,
  "Opened 1932-11-24 as the last part of the Route 1 Extension.", W + "Pulaski_Skyway"),
 ("us1_9_newark", "US 1/9 (Route 1 Extension): Newark, Elizabeth line - Pulaski Skyway", "freeway", {"ref0:US:US 1", "ref0:US:US:Express 1"}, "all", None, 1928.96, S, G,
  "The eastern and western sections of the Route 1 Extension, with the embankments in eastern Newark, opened 1928-12-16. Estimated for the stretch along the airport (rebuilt since with express and local roadways).", W + "Pulaski_Skyway"),
 ("nj139_lower", "Route 139 (Route 1 Extension): the covered roadway, lower level", "freeway", {"NJ 139 Lower Level"}, "all", None, 1928.96, S, G,
  "The viaduct leading to the covered roadway and the sections in Jersey City opened 1928-12-16.", W + "Pulaski_Skyway"),
 ("nj139_12th_street_viaduct", "Route 139: 12th Street Viaduct", "bridge", {"12th Street Viaduct"}, "all", None, 1927.50, S, G,
  "The 12th Street Viaduct from Jersey Avenue to the top of Bergen Hill opened 1927-07-04.", W + "New_Jersey_Route_139"),
 ("nj139_14th_street_viaduct", "Route 139: 14th Street Viaduct", "bridge", {"14th Street Viaduct"}, "all", None, 1951.12, S, G,
  "The westbound 14th Street Viaduct opened 1951-02-13.", W + "New_Jersey_Route_139"),
 ("nj495_approach", "Route 495 (Lincoln Tunnel approach): Route 3 - the Helix", "freeway", NJ495, x("ref:US:NJ 3"), end("E"), 1939, S, G,
  "In 1939 the Port Authority opened the rest of the approach, up the Helix and west to Route 3.", W + "New_Jersey_Route_495"),
 ("nj495_west", "Route 495: New Jersey Turnpike - Route 3", "freeway", NJ495, end("W"), x("ref:US:NJ 3"), 1952.04, S, G,
  "The final section, west of Route 3, opened 1952-01-15 with the completion of the New Jersey Turnpike.", W + "New_Jersey_Route_495"),
 ("nj3_freeway", "Route 3 freeway: Clifton - North Bergen", "highway", {"ref:US:NJ 3"}, "far", None, 1949.58, S, G,
  "The entire 10.8-mile Route 3 freeway opened 1949-07-31 (Wikipedia: a first section between Route 17 and today's Route 120 in 1942; the later date is used for the whole).", NR + "NJ-3/"),
 ("nj4", "Route 4: Paterson line - George Washington Bridge", "highway", {"ref:US:NJ 4"}, "far", None, 1932.57, S, G,
  "Built from 1930 to connect Paterson and the George Washington Bridge; completed and opened 1932-07-28.", W + "New_Jersey_Route_4"),
 ("nj17_bergen", "Route 17 (Route 2): Bergen County", "highway", {"ref0:US:NJ 17", "Route 17 North", "Route 17 South", "N.J. State Route 17"}, "all", None, 1937, S, G,
  "Estimated: Route 2 (Route 17 since 1942) was moved to a multilane divided highway alignment north of Rutherford by 1937 (rebuilt to higher standards 1953-1960).", W + "New_Jersey_Route_17"),
 ("nj19_south", "Route 19 (Paterson Peripheral): Garden State Parkway - Valley Road", "freeway", NJ19, end("S"), x("Valley Road"), 1969, S, G,
  "Completed between the Garden State Parkway and Valley Road by 1969.", W + "New_Jersey_Route_19"),
 ("nj19_valley_80", "Route 19: Valley Road - Interstate 80", "freeway", NJ19, x("Valley Road"), x("Christopher Columbus Highway"), 1975, S, G,
  "Completed north to I-80 in 1975.", W + "New_Jersey_Route_19"),
 ("nj19_paterson", "Route 19: Interstate 80 - Main Street (Paterson)", "freeway", NJ19, x("Christopher Columbus Highway"), end("N"), 1992, S, G,
  "The extension to Main Street in downtown Paterson, with the completed I-80 interchange, was finished in 1992.", W + "New_Jersey_Route_19"),
 ("nj21_newark_nutley", "Route 21 freeway: Newark - Park Avenue (Nutley)", "freeway", NJ21, x("Chester Avenue"), x("Park Avenue", (-74.140, 40.811)), 1958, S, G,
  "The first section of the freeway, from Chester Avenue in Newark to Park Avenue in Nutley, opened in 1958.", W + "New_Jersey_Route_21"),
 ("nj21_nutley_passaic_park", "Route 21 freeway: Nutley - Passaic Park", "freeway", NJ21, x("Park Avenue", (-74.140, 40.811)), x("ref:US:NJ 3"), 1962, S, G,
  "Extended to the Passaic Park interchange in 1962. Its end is taken at Route 3, about a kilometre short of Passaic Park: estimated.", W + "New_Jersey_Route_21"),
 ("nj21_passaic_park_main", "Route 21 freeway: Passaic Park - River Drive / Main Avenue (Passaic)", "freeway", NJ21, x("ref:US:NJ 3"), x("River Drive", (-74.122, 40.856)), 1968, S, G,
  "Extended to Main Avenue (exit 11, River Drive - Main Avenue) in 1968.", W + "New_Jersey_Route_21"),
 ("nj21_main_monroe", "Route 21 freeway: Main Avenue - Monroe Street (Passaic)", "freeway", NJ21, x("River Drive", (-74.122, 40.856)), x("Monroe Street"), 1973, S, G,
  "Extended to Monroe Street in 1973.", W + "New_Jersey_Route_21"),
 ("nj21_extension", "Route 21 freeway: Monroe Street - US 46 (Clifton)", "freeway", NJ21, x("Monroe Street"), end("N"), 2000.97, S, G,
  "The northern extension to US 46 opened 2000-12-20.", W + "New_Jersey_Route_21"),
 ("nj24_east", "Route 24 freeway: Interstate 78 - John F. Kennedy Parkway", "freeway", NJ24, end("E"), x("John F. Kennedy Parkway"), 1976, S, G,
  "The freeway between JFK Parkway and I-78 was built from 1967 and finished in 1976.", W + "New_Jersey_Route_24"),
 ("nj24_west", "Route 24 freeway: John F. Kennedy Parkway - Interstate 287", "freeway", NJ24, x("John F. Kennedy Parkway"), end("W"), 1992.88, S, G,
  "Completed through to I-287 in Hanover and opened 1992-11-17 (outside the map's counties).", W + "New_Jersey_Route_24"),
 ("nj208_south", "Route 208: Route 4 - Maple Avenue (Fair Lawn)", "highway", NJ208, end("E"), x("Maple Avenue"), 1953, S, G,
  "Estimated: by 1953 the portion between Route 4 and Maple Avenue in Fair Lawn was completed.", W + "New_Jersey_Route_208"),
 ("nj208_north", "Route 208: Maple Avenue - Oakland", "highway", NJ208, x("Maple Avenue"), end("W"), 1960, S, G,
  "Estimated: by 1960 the road was extended to US 202 in Oakland, as a two-lane road (a divided highway by the 1980s).", W + "New_Jersey_Route_208"),
 ("nj440_bayonne", "Route 440 (Route 169): Bayonne Bridge - New Jersey Turnpike extension", "highway", {"ref0:US:NJ 440"}, x("Bayonne Bridge"), x("New Jersey Turnpike Newark Bay Extension"), 1992, S, G,
  "Route 169, a four-lane arterial along the Bayonne waterfront, was completed in 1992 (Route 440 since 2001).", W + "New_Jersey_Route_440"),
 ("us46_clifton_hasbrouck", "US 46 (Route 6): Passaic River at Clifton - Hasbrouck Heights", "highway", {US46}, x("ref:US:NJ 21"), x("ref:US:NJ 17"), 1937.95, S, G,
  "In December 1937 a section of Route 6 was opened from the Passaic River at Clifton to Hasbrouck Heights (the ends are taken at Route 21 and Route 17: estimated).", W + "U.S._Route_46"),
 ("wittpenn_bridge", "Wittpenn Bridge (Route 7, Hackensack River)", "bridge", {"New Wittpenn Bridge"}, "all", None, 1930.85, S, G,
  "The first Wittpenn Bridge opened 1930-11-05; its replacement, on a parallel line, opened 2021-10-02 (the line drawn is today's bridge; the crossing is shown from 1930).", W + "Wittpenn_Bridge"),
]
