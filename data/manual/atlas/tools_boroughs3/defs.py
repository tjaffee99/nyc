BRX = (-73.93, 40.78, -73.74, 40.93)
lay["bronx_east_1905"] = layer(1905, "Atlas of the borough of the Bronx, city of New York, Volume A (G. W. Bromley & Co., Philadelphia, 1905): the district east of the Bronx River (Unionport, Westchester, Castle Hill, Clason Point, Throgs Neck, Pelham Parkway)", "bromley_bronx_1905", pick(r"Bronx, V\. A, Plate.*From Vol\. A$", box=BRX), BRONX_SO)
lay["bronx_north_1905"] = layer(1905, "Atlas of the borough of the Bronx, city of New York, Volume B (G. W. Bromley & Co., Philadelphia, 1905): Williamsbridge, Wakefield, Eastchester, Baychester, Pelham Bay and City Island", "bromley_bronx_1905", pick(r"Bronx, V\. B, Plate.*From Vol\. B$", box=BRX), BRONX_SO)
SI_SO = {"frame": {"db_min": 4.0, "hue": 0.42, "L_min": 45, "L_max": 88}, "outline": 0.2, "stone": None, "street_min_q": 0.2, "street_win_m": 300.0}
lay["staten_island_south_1917"] = layer(1917, "Atlas of the city of New York, borough of Richmond, Staten Island (G. W. Bromley & Co., 1917): the plates of Wards 1-5 outside the layer staten_island_north_1917", "bromley_richmond_1917", pick(r"^Part of Wards?|Nelson Ave, Cleveland Ave, 2nd St", box=(-74.30, 40.45, -74.03, 40.66), minnew=0.3), SI_SO)
lay["staten_island_south_1917"]["plates"] = [q for q in lay["staten_island_south_1917"]["plates"] if 15367 <= q["id"] <= 15460]
for q in lay["staten_island_south_1917"]["plates"]:
    if q["id"] in (15395, 15426):
        q["skip"] = "street match only 9 windows with a constant shift and 5.5-6.7 m left after it, no outline on a standing building: registration not good enough"
Q09 = "Atlas of the borough of Queens, city of New York (G. W. Bromley & Co., Philadelphia, 1909)"
Q_SO = {"frame": {"db_min": 4.0, "hue": 0.42, "L_min": 45, "L_max": 88}, "outline": 0.25, "stone": None, "street_min_q": 0.2, "street_win_m": 300.0}
def q09(pat, box, minnew=0.3):
    return [q for q in pick(pat, box=box, minnew=minnew) if 8096 <= q["id"] <= 8147]
QB = (-73.97, 40.54, -73.70, 40.82)
H07 = "Atlas of the borough of Queens, city of New York (E. Belcher Hyde, 1907)"
def hyde(lo, hi, box, minnew=0.3, exclude=()):
    return [q for q in pick(r"Queens, [Vv]ol\. [12], Double Page", box=box, minnew=minnew) if lo <= q["id"] <= hi and q["id"] not in exclude]
lay["queens_jamaica_1907"] = layer(1907, H07 + ", volume 1 (Fourth ward: Jamaica outskirts, Richmond Hill, Woodhaven, Ozone Park, Hollis, Queens Village)", "queens_wards45_1907", hyde(15594, 15631, QB, exclude=(15621, 15624, 15625, 15628)), Q_SO)
lay["queens_rockaway_beach_1907"] = layer(1907, H07 + ", volume 1 (Fifth ward: the Rockaway peninsula plates 33, 36, 37, 40 not in queens_rockaway_1907)", "queens_wards45_1907", hyde(15621, 15628, QB, minnew=0.3, exclude=(15622, 15623, 15626, 15627)), Q_SO)
lay["queens_newtown_1907"] = layer(1907, H07 + ", volume 2 (Second ward: Newtown, Elmhurst, Corona, Maspeth, Middle Village, Glendale, Woodside, North Beach; First ward north shore)", "queens_wards12_1907", hyde(15642, 15701, QB), Q_SO)
