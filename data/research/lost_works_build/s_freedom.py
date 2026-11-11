import sys
sys.path.insert(0, "/home/user/nyc/data/research/lost_works_build"); from lwlib import *
U = "https://en.wikipedia.org/wiki/Freedomland_U.S.A."
C = (40.8655, -74.8255 + 1.0)    # -73.8255
B = ("BEST GUESS: {w}. Freedomland U.S.A., 1960-64 (opened 19 June 1960; 85 acres of park in the shape of a map of the United States, beside 125 acres of parking; closed 1964, mostly razed by early 1965 - Wikipedia 'Freedomland U.S.A.'). "
     "The article names the sections and says where they lay in the park ('Little Old New York' at the north end by the entrance, 'San Francisco' at the south end, 'Satellite City' in the south-east) but gives no plan, no dimensions and no coordinates of any structure: "
     "the sections are put at those compass places inside the park's ground (the ground the holes report calls 'freedomland_remnant', about -73.8266 40.8661), position good to about 150 m, size and height ESTIMATED as a movie-set building.")
spec = [("lony", "Little Old New York street of 1890s facades (north end, by the entrance)", 0, 270, 130, 40, 14, "wood"),
        ("lony2", "Little Old New York, second street range", 15, 230, 100, 30, 12, "wood"),
        ("santa_fe", "Santa Fe Railroad station and engine shed", 0, 150, 50, 16, 8, "wood"),
        ("chicago", "Old Chicago: the Chicago Fire theatre and street sets", -170, 60, 70, 45, 12, "wood"),
        ("plains", "Great Plains: the stockade (fort) and cavalry corral", -250, 130, 55, 55, 8, "wood"),
        ("sanfran", "San Francisco: the earthquake show theatre and Barbary Coast streets", -40, -250, 70, 45, 14, "wood"),
        ("moon", "Satellite City: the 'Moon Bubble' dome", 250, -120, 45, 45, 20, "steel"),
        ("satellite", "Satellite City: the exhibition hall", 215, -60, 60, 30, 10, "steel")]
rows = []
for k, nm, dx, dy, w, d, h, mat in spec:
    la, lo = off(40.8660, -73.8270, dx, dy)
    rows.append(mk(f"bg_freedomland_{k}", f"Freedomland U.S.A.: {nm}", 1960, 1965, la, lo, h, mat, w, d, 0, B.format(w=nm), U))
add(rows)
