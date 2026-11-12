import sys
sys.path.insert(0, "/home/user/nyc/data/research/lost_works_build"); from lwlib import *
rows = []
U = "https://en.wikipedia.org/wiki/Newark_Housing_Authority"
def grp(key, nm, n, c, w, d, h, y0, ends, note, url, spacing=(70, 55), cols=3):
    for i in range(n):
        dx = (i % cols - (cols - 1) / 2) * spacing[0]; dy = -(i // cols) * spacing[1]
        la, lo = off(c[0], c[1], dx, dy)
        rows.append(mk(f"bg_newark_{key}_{i+1}", f"{nm}, building {i+1}", y0, ends[i] if isinstance(ends, list) else ends, la, lo, h, "brick", w, d, 0, note, url))
grp("brick", "Brick Towers (Newark)", 3, (40.7286, -74.18256), 55, 16, 48, 1969, 2008,
    "BEST GUESS: Brick Towers, Central Ward public housing, 324 units, completed 1969, demolished 2008 (Wikipedia 'Brick Towers': 40.7286 N 74.18256 W). The article's point is used for the group (+-100 m); the three slab blocks, their size and 14 storeys are ESTIMATED from the 324 units.", "https://en.wikipedia.org/wiki/Brick_Towers")
grp("stellawright", "Stella Wright Homes (Newark)", 7, (40.7398, -74.1838), 48, 16, 42, 1959, [1996, 1996, 1998, 1998, 2000, 2000, 2002],
    "BEST GUESS: Stella Wright Homes, seven 13-storey towers on Waverly Avenue in the Central Ward, 1959, imploded in phases up to 2002 (Wikipedia 'Newark Housing Authority', search snippet only). Waverly Avenue is not on today's map and no outline was found: "
    "the group is put in the Central Ward's cleared district with the position uncertain by about 500 m; size, layout, storeys and the order of the implosions are ESTIMATED.", U)
grp("kretchmer", "Kretchmer Homes (Newark)", 5, (40.7385, -74.1925), 50, 14, 28, 1953, 1996,
    "BEST GUESS: Kretchmer Homes, five 8-storey blocks, 1953, imploded 21 April 1996 (Wikipedia 'Newark Housing Authority', search snippet only). No outline or street was found: "
    "the group is put in the Central Ward's cleared district with the position uncertain by about 500 m; size and layout ESTIMATED.", U)
grp("columbus", "Columbus Homes (Newark)", 4, (40.7330, -74.1800), 55, 16, 48, 1955, 1994,
    "BEST GUESS: Columbus Homes, Central Ward public-housing high-rises, 1955, imploded 1994 (search snippets only; the number of towers is NOT known). No outline or street was found: "
    "four 14-storey slabs are put in the Central Ward's cleared district with the position uncertain by about 500 m; everything but the years is ESTIMATED.", U)
add(rows)
