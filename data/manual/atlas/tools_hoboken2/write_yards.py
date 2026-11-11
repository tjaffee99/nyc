"""Writes data/manual/ports/yards_historic.geojson (hand-placed outlines; see data/research/hudson_waterfront.md).
python -I write_yards.py"""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
WP = "https://en.wikipedia.org/wiki/"
Y = []
def add(id, name, a, b, ya, yb, basis, source, outline, ring, bearing, kind="rail"):
    ring = list(ring) + [ring[0]]
    Y.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[list(p) for p in ring]]},
              "properties": dict(id=id, name=name, start_year=a, end_year=b, year_basis=dict(start=ya, end=yb), source=source, basis=basis,
                                 outline=outline, kind=kind, track_bearing_deg=bearing, track_gap_m=4.6, historic=True)})
add("prr_exchange_place_terminal_tracks", "Pennsylvania Railroad Exchange Place terminal, train shed and approach tracks, Jersey City", 1873, 1961, "source", "source",
    "Twelve-track, six-platform ferry terminal on wooden piers built by the PRR in 1873 (timeline); burnt 4 Aug 1884, rebuilt 1888-92 and raised 15-20 ft in 1891; the last PRR passenger train used it on 17 Nov 1961 and the last buildings were demolished in 1963 (Wikipedia 'Exchange Place (PRR station)': station point 40.71648 N 74.03238 W).",
    WP + "Exchange_Place_(PRR_station) ; " + WP + "Timeline_of_Jersey_City,_New_Jersey-area_railroads",
    "Hand-drawn polygon about the station point (east of Hudson Street, between Montgomery St and Exchange Place's present foot); no plan of the track layout was opened. +-60 m.",
    [(-74.0378, 40.7165), (-74.0325, 40.7150), (-74.0312, 40.7168), (-74.0325, 40.7182), (-74.0370, 40.7178)], 93)
add("prr_harsimus_cove_yard", "Pennsylvania Railroad Harsimus Cove freight yards, stockyards, abattoir and car floats, Jersey City", 1868, 1976, "source", "estimated",
    "PRR freight terminal at Harsimus Cove opened 1868 (timeline); cove filled by 1870 'for railyards' and 'extending a quarter mile from Henderson Street' (Marin Boulevard); 'huge stockyards dominated the waterfront between the train terminals', PRR abattoir to the south (Wikipedia 'Harsimus'); served by the Harsimus Stem Embankment. End year ESTIMATED: ports 'abandoned by the 1970s', Newport redevelopment began 1986.",
    WP + "Harsimus ; " + WP + "Timeline_of_Jersey_City,_New_Jersey-area_railroads ; " + WP + "Pavonia_Terminal",
    "Hand-drawn polygon: west edge Marin Boulevard / Henderson St line (-74.0405), north edge 6th Street's east end (lat 40.7250, from Overture's street lines), south edge about Christopher Columbus Drive, east edge the 1919-era shore. +-80 m.",
    [(-74.0408, 40.7195), (-74.0340, 40.7192), (-74.0330, 40.7215), (-74.0335, 40.7250), (-74.0405, 40.7250)], 93)
add("harsimus_stem_embankment", "Harsimus Stem Embankment (PRR, seven tracks), Jersey City", 1905, 9999, "source", "estimated",
    "Embankment built 1901-1905 (National Register nomination, via search snippet; the Wikipedia page gives no year); 27 ft high, seven tracks, south side of Sixth Street from Marin Boulevard west to Brunswick Street (Wikipedia 'Harsimus Stem Embankment'). Disused but still standing: end 9999.",
    WP + "Harsimus_Stem_Embankment",
    "Strip 35 m wide along the south side of 6th Street, using Overture's 6th Street centreline (-74.0404 40.7251 to -74.0488 40.7258). +-15 m. Track lines should be generated: no rail line is in today's data for it.",
    [(-74.0404, 40.7247), (-74.0498, 40.7254), (-74.0498, 40.7250), (-74.0404, 40.7243)], 93)
add("erie_pavonia_terminal_yard", "Erie Railroad Pavonia Terminal and yards, Jersey City", 1861, 1959, "source", "estimated",
    "Pavonia terminal opened 1 May 1861 (Wikipedia infobox; Erie began developing the site in 1856); new terminal 4 Dec 1887; closed 12 Dec 1958, demolished 1961. Built on the northern part of the filled Harsimus Cove; the Long Slip separated it from Hoboken Terminal. End year ESTIMATED as 1959 (cars gone after the passenger closing; demolition 1961).",
    WP + "Pavonia_Terminal",
    "Hand-drawn polygon about the terminal point (40.726676 N 74.034757 W): south edge the PRR yard's north edge, north edge the Long Slip, west edge the viaduct at the foot of the Palisades cut. +-80 m.",
    [(-74.0420, 40.7262), (-74.0335, 40.7255), (-74.0322, 40.7285), (-74.0325, 40.7305), (-74.0400, 40.7312), (-74.0425, 40.7290)], 93)
add("cnj_communipaw_terminal_yard", "Central Railroad of New Jersey Communipaw terminal and yards, Jersey City", 1864, 1967, "source", "source",
    "Terminal of 1864 replaced 1889 (headhouse still stands); Bush trainsheds 1914; passenger service ended 30 April 1967; yards on filled land, 63 acres on the National Register (Wikipedia 'Central Railroad of New Jersey Terminal', point 40 42 26 N 74 02 07 W). End year is the passenger closing; freight use after 1967 not checked.",
    WP + "Central_Railroad_of_New_Jersey_Terminal",
    "Hand-drawn polygon on today's Liberty State Park north end: the headhouse point, the surviving track block (-74.039..-74.036, 40.7068-40.7080) and the park's flat made ground west of it to the old Johnston Avenue line. +-100 m.",
    [(-74.0545, 40.7078), (-74.0450, 40.7108), (-74.0375, 40.7098), (-74.0355, 40.7078), (-74.0380, 40.7058), (-74.0470, 40.7048), (-74.0560, 40.7040)], 85)
add("lehigh_valley_black_tom_national_docks", "Lehigh Valley Railroad Black Tom terminal and National Docks yards, Jersey City", 1883, 1976, "source", "estimated",
    "National Docks Railway of 1883 connected the National Storage Company docks at Black Tom with the PRR (timeline); the Lehigh Valley ran the Black Tom terminal (blown up 30 July 1916: 'over one hundred railroad cars and warehouses', Wikipedia 'Black Tom explosion', point 40 41 32 N 74 03 20 W). End year ESTIMATED (Liberty State Park, opened 1976); the LV's 1889 South Cove freight terminal is not outlined.",
    WP + "Black_Tom_explosion ; " + WP + "Timeline_of_Jersey_City,_New_Jersey-area_railroads",
    "Hand-drawn polygon about the Black Tom point on today's filled peninsula of Liberty State Park (Caven Point road area). No plan opened. +-150 m.",
    [(-74.0625, 40.6955), (-74.0525, 40.6975), (-74.0505, 40.6925), (-74.0555, 40.6905), (-74.0640, 40.6925)], 60)
add("dlw_hoboken_terminal_yard", "Delaware, Lackawanna & Western Hoboken terminal and yard", 1862, 9999, "source", "source",
    "First terminal 14 Nov 1862 (Morris & Essex), second 15 Jan 1868, burnt June 1873, fourth 1885, burnt 1905, present terminal 1907 (Wikipedia 'Hoboken Terminal', point 40.735 N 74.0275 W). The yard is still in use (NJ Transit): today's tracks are in rail.parquet already; this outline only widens the area to the old yard.",
    WP + "Hoboken_Terminal",
    "Hand-drawn polygon over today's yard throat (rail.parquet track fan) to the foot of the Bergen Hill cut. +-50 m.",
    [(-74.0440, 40.7352), (-74.0400, 40.7338), (-74.0320, 40.7328), (-74.0285, 40.7335), (-74.0278, 40.7362), (-74.0300, 40.7375), (-74.0345, 40.7378), (-74.0400, 40.7370)], 97)
add("west_shore_weehawken_terminal_yard", "West Shore (New York Central) Weehawken terminal and yards", 1884, 1959, "source", "source",
    "Terminal opened 1884, closed 1959 (last ferry 25 March 1959); sixteen passenger tracks, five ferry slips, car-float facilities and 'extensive yards' (Wikipedia 'Weehawken Terminal', point 40.771639 N 74.01275 W).",
    WP + "Weehawken_Terminal",
    "Hand-drawn strip 100-250 m wide between the West Shore line's surviving curve (today's Hudson-Bergen Light Rail, from the Weehawken Tunnel mouth) and today's shore, 40.763-40.775 N. The yard's length is not in the sources opened. +-100 m.",
    [(-74.0212, 40.7628), (-74.0185, 40.7662), (-74.0160, 40.7690), (-74.0138, 40.7722), (-74.0122, 40.7752), (-74.0112, 40.7752), (-74.0125, 40.7720), (-74.0150, 40.7685), (-74.0170, 40.7660), (-74.0180, 40.7635)], 35)
add("greenville_yard_prr", "Pennsylvania Railroad Greenville Yard and car-float bridges, Jersey City", 1904, 9999, "source", "source",
    "Developed 1904 by the PRR with three car-float bridges (Nos. 11-13), No. 14 in 1910, No. 10 in 1924; fire 1 Jan 1931 destroyed the wooden bridges; yard still in use (Wikipedia 'Greenville Yard').",
    WP + "Greenville_Yard",
    "Hand-drawn polygon around today's yard track fan in rail.parquet (-74.093..-74.074, 40.676-40.688) read off a base map. +-60 m. Today's tracks cover most of it.",
    [(-74.0905, 40.6878), (-74.0820, 40.6868), (-74.0745, 40.6805), (-74.0745, 40.6790), (-74.0780, 40.6762), (-74.0840, 40.6768), (-74.0900, 40.6800)], 120)
out = ROOT / "data/manual/ports/yards_historic.geojson"
out.write_text(json.dumps({"type": "FeatureCollection", "features": Y}, indent=0))
print(len(Y), "yards ->", out)
