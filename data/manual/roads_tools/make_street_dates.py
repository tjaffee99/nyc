"""Builds data/tables/street_dates.csv: researched street years (see the notes), with the stretch each row
applies to given as a box whose edges are computed from Overture's street centre lines (the crossing of the
named cross street), not typed in.
columns: street (Overture name, upper-cased; "re:<regex>" = every name matching), year_start, note, source_url,
rule (blank = not before; set = replaces the estimate), boro (the boroughs 1-5 and / or county FIPS codes the
row is about, separated by spaces; blank = the five boroughs, never the counties), bbox ("lon0 lat0 lon1 lat1":
by the segment's middle; blank = the whole street)."""
import csv
import sys

from shapely.ops import nearest_points

import os  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_routes as M  # noqa: E402

W = "https://en.wikipedia.org/wiki/"
MAN = (-73.985, 40.76)


def crossing(street, cross, hint):
    """(lon, lat) where `cross` meets `street` (nearest points of their centre lines near `hint`)"""
    a = M.street_geom(street, hint=hint)
    b = M.street_geom(cross, hint=hint)
    if a is None or b is None:
        raise ValueError(f"{street} x {cross}: not found near {hint}")
    p = nearest_points(a, b)[0]
    return M.TO_LL.transform(p.x, p.y)


def lat_box(street, south, north, hint_s, hint_n, pad=0.0002):
    y0 = crossing(street, south, hint_s)[1] if south else 40.60
    y1 = crossing(street, north, hint_n)[1] if north else 40.95
    return f"-74.05 {y0 + pad:.5f} -73.88 {y1 - pad:.5f}"


def lon_box(street, west, east, hint_w, hint_e, pad=0.0002):
    x0 = crossing(street, west, hint_w)[0] if west else -74.30
    x1 = crossing(street, east, hint_e)[0] if east else -73.60
    return f"{x0 + pad:.5f} 40.45 {x1 - pad:.5f} 40.95"


R = []
add = lambda street, year, note, url, rule="", boro="", bbox="": R.append([street, year, note, url, rule, boro, bbox])

# ---- Manhattan: streets cut through older blocks (not before)
add("re:^((EAST|WEST) )?[0-9]+(ST|ND|RD|TH) (STREET|AVENUE)$|^AVENUE [A-D]$", 1811.22,
    "The numbered streets and avenues (and Avenues A-D) are the grid of the Commissioners' Plan, adopted 1811-03-22: none was opened before it (most were opened decades later, block by block, as the building rule dates them).",
    W + "Commissioners%27_Plan_of_1811", "", "1")
add("7TH AVENUE SOUTH", 1914, "Seventh Avenue was extended southward, as Seventh Avenue South, to link up with Varick Street in 1914, cutting through the older blocks of Greenwich Village (buildings in its path were demolished); Varick Street was widened at the same time (1917).",
    W + "Seventh_Avenue_(Manhattan)", "", "1")
add("6TH AVENUE", 1930, "Sixth Avenue was widened and extended from Minetta Lane to Canal Street from 1926 (with the Holland Tunnel); the extension opened to traffic in 1930.",
    W + "Sixth_Avenue", "", "1", lat_box("6th Avenue", "Canal Street", "Minetta Lane", (-74.005, 40.722), (-74.001, 40.730)))
add("KENMARE STREET", 1911, "Kenmare Street was created in 1911 (the extension of Delancey Street toward Lafayette Street, cut through the blocks).",
    W + "Delancey_Street", "", "1")
add("LAFAYETTE STREET", 1825, "Lafayette Place: cut through the Vauxhall Gardens site by John Jacob Astor in 1825, from Astor Place to Great Jones Street.",
    W + "Lafayette_Street", "", "1", lat_box("Lafayette Street", "Great Jones Street", "Astor Place", (-73.993, 40.727), (-73.991, 40.730)))
# ---- Manhattan: roads older than the buildings along them, drives without any (set)
add("BROADWAY", 1703, "Bloomingdale Road, opened in 1703 from about 23rd Street north: Broadway follows it (widened and paved as the Boulevard above 59th Street from 1868; the name Broadway since 1899).",
    W + "Broadway_(Manhattan)", "set", "1", lat_box("Broadway", "West 23rd Street", "West 86th Street", (-73.989, 40.742), (-73.977, 40.788)))
add("BROADWAY", 1868, "The Boulevard: in 1868 the Bloomingdale Road between 59th and 155th Streets was laid out anew as a wide avenue; above 86th Street it left the old road's line (drawn from OpenHistoricalMap's trace until then, routes.csv).",
    W + "Broadway_(Manhattan)", "set", "1", lat_box("Broadway", "West 86th Street", "West 155th Street", (-73.977, 40.788), (-73.945, 40.832)))
add("BOWERY", 1654, "The oldest thoroughfare of Manhattan: a Lenape footpath, then the Dutch road to the bouweries; colonists settled along it at Chatham Square in 1654 (the year used: the road is older).",
    W + "Bowery", "set", "1")
add("RIVERSIDE DRIVE", 1880, "Riverside Avenue (Drive) opened in 1880 from 72nd Street to the site of Grant's Tomb.",
    W + "Riverside_Drive_(Manhattan)", "set", "1", lat_box("Riverside Drive", None, "West 122nd Street", None, (-73.963, 40.813)))
add("RIVERSIDE DRIVE", 1902.5, "Manhattan Valley Viaduct (125th - 135th Street), completed mid-1902.",
    W + "Riverside_Drive_(Manhattan)", "set", "1", lat_box("Riverside Drive", "West 122nd Street", "West 135th Street", (-73.963, 40.813), (-73.957, 40.822)))
add("RIVERSIDE DRIVE", 1911.1, "Extension north of the viaduct, begun December 1903; the section between 145th and 158th Streets formally opened February 1911 (the stretch from 135th Street is assumed to have opened by then: estimated).",
    W + "Riverside_Drive_(Manhattan)", "set", "1", lat_box("Riverside Drive", "West 135th Street", "West 158th Street", (-73.957, 40.822), (-73.948, 40.836)))
add("65TH STREET TRANSVERSE", 1859.95, "Central Park's 66th Street transverse road was the first finished, opened December 1859.", W + "Central_Park", "set", "1")
add("79TH STREET TRANSVERSE", 1860.95, "Central Park's 79th Street transverse road (under Vista Rock) opened December 1860.", W + "Central_Park", "set", "1")
add("86TH STREET TRANSVERSE", 1862.9, "Central Park's 86th and 97th Street transverse roads opened in late 1862.", W + "Central_Park", "set", "1")
add("97TH STREET TRANSVERSE", 1862.9, "Central Park's 86th and 97th Street transverse roads opened in late 1862.", W + "Central_Park", "set", "1")
# ---- Harlem River and other road bridges that are not landmark models
add("THIRD AVENUE BRIDGE", 1898, "The first steel swing bridge was built in 1898 (replaced 1955-56 and 2004-05).", W + "Third_Avenue_Bridge_(New_York_City)", "set")
add("WILLIS AVENUE BRIDGE", 1901, "Opened in 1901 (replaced 2010).", W + "Willis_Avenue_Bridge", "set")
add("MADISON AVENUE BRIDGE", 1884, "A swing bridge was built here in 1884; today's bridge of 1910 doubled its capacity.", W + "Madison_Avenue_Bridge", "set")
add("145TH STREET BRIDGE", 1905.65, "Opened to traffic 1905-08-24.", W + "145th_Street_Bridge", "set")
add("CROSS BAY BRIDGE", 1925, "The first Cross Bay bridge opened in 1925 (replaced 1939-06-03 and 1970).", W + "Cross_Bay_Veterans_Memorial_Bridge", "set")
add("RIKERS ISLAND BRIDGE", 1966.89, "Opened 1966-11-22.", W + "Rikers_Island_Bridge", "set")
# ---- the Bronx
add("GRAND CONCOURSE", 1909.85, "Built from 1894, opened to traffic November 1909 (161st Street to Mosholu Parkway; the stretch south of 161st Street, the former Mott Avenue, is left to the building rule).",
    W + "Grand_Concourse_(Bronx)", "set", "2", lat_box("Grand Concourse", "East 161st Street", None, (-73.923, 40.827), None))
add("PELHAM PARKWAY", 1912, "The original Pelham Parkway was built in 1911 and opened in 1912 as a two-lane road (today's westbound lanes); today's parkway dates from 1935-37.",
    W + "Pelham_Parkway", "set", "2")
add("SHERIDAN BOULEVARD", 1963.1, "Opened 1963-02-06 as the Sheridan Expressway (a boulevard since 2019-12-11).", W + "New_York_State_Route_895", "set", "2")
# ---- Queens
add("QUEENS BOULEVARD", 1913, "The new boulevard (Thomson Avenue and Hoffman Boulevard widened after the Queensboro Bridge) carried a trolley line from 1913; widened again in the 1920s-30s with the subway. One year for the whole boulevard: estimated (the roads it absorbed are older).",
    W + "Queens_Boulevard", "set", "4")
# ---- Brooklyn
add("OCEAN PARKWAY", 1876.88, "The parkway's northern half was completed in May 1874; the extension to Coney Island was finished 1876-11-11 and opened 1876-11-18 (the later date is used for the whole parkway).",
    W + "Ocean_Parkway_(Brooklyn)", "set", "3")
add("EASTERN PARKWAY", 1874, "Graded between Washington and Ralph Avenues by August 1871, almost completed by 1874.",
    W + "Eastern_Parkway", "set", "3", lon_box("Eastern Parkway", None, "Ralph Avenue", None, (-73.922, 40.669)))
add("EASTERN PARKWAY", 1897, "The extension to Bushwick Avenue had been completed by 1897.",
    W + "Eastern_Parkway", "set", "3", lon_box("Eastern Parkway", "Ralph Avenue", None, (-73.922, 40.669), None))
add("KINGS HIGHWAY", 1704, "An Indian trail ('the ancient pathway' in a 1652 deed, the 'wagon path' in 1682), made the King's Highway in 1704. Today's boulevard was widened and straightened in the 1920s: where it left the old line the year is estimated (OpenHistoricalMap's trace of the old line is in routes.csv).",
    W + "Kings_Highway_(Brooklyn)", "set", "3")
# ---- the counties (boro = county FIPS: 36119 Westchester, 34017 Hudson, 34003 Bergen, 34031 Passaic)
add("BOSTON POST ROAD", 1673, "The first ride to lay out the post road between New York and Boston started 1673-01-01 (the road follows older trails: the year the post route was laid out is used; today's US 1 was widened and in places straightened: estimated where it left the old line).",
    W + "Boston_Post_Road", "set", "36119")
add("PATERSON PLANK ROAD", 1851.2, "Estimated: the company which built the Paterson and New York Plank Road received its charter 1851-03-14 (the charter date is used; the plank road across the meadows opened soon after).",
    W + "Paterson_Plank_Road", "set", "34017 34003 34031")

with open(os.path.join(M.ROOT, "data", "tables", "street_dates.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["street", "year_start", "note", "source_url", "rule", "boro", "bbox"])
    w.writerows(R)
for r in R:
    print(r[0][:40], r[1], r[4], r[5], r[6])
print(len(R), "rows -> data/tables/street_dates.csv")
