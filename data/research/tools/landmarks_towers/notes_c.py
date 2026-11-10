"""Hand-written research notes per landmark (part C: Rockefeller Center's lower buildings)."""
from notes_a import N, WP

RC = 'Rockefeller Center, lower building: base on the official footprint, set-backs from OSM parts, top at the cited height'


def rc(key, h, wiki, csv, est, cited, measured, estimated, bin_):
    N[key] = dict(h=h, url=WP + wiki, csv=csv, est=est, src=[WP + wiki, f'city footprint BIN {bin_}', 'OSM parts'], cited=cited, measured=measured, estimated=estimated)


rc('rockefeller_international_building', 156.1, 'International_Building_(Rockefeller_Center)', 'start 1933 (CTBUH), completed 1 May 1935; 512 ft', 'month of the 1933 start',
   ['roof 512 ft (156.1 m), 41 floors, completed 1 May 1935 — Wikipedia infobox'],
   ['official footprint 5,075 m²: the tower and the two six-storey wings on Fifth Avenue', 'OSM part tops 8, 17, 20, 25, 28, 35, 60, 110, 145, 156 m with their outlines'],
   ['`built` starts at 1933.5 (year from CTBUH)'], 1083860)
rc('rockefeller_plaza_1', 149.0, '1_Rockefeller_Plaza', 'built 1936-1937 (CTBUH; Wikipedia: completed 1937); 149 m (CTBUH)', 'months within 1936-37',
   ['"Completed in 1937" — Wikipedia'],
   ['official footprint 1,625 m² (the city records 128.9 m for it)', 'OSM part tops 25, 29, 138, 149 m with their outlines'],
   ['`built` 1936.5–1937.9: years only'], 1077286)
rc('rockefeller_1270_sixth', 124.7, 'Rockefeller_Center', 'completed 1932 (CTBUH); start late 1931 estimated; 124.7 m (CTBUH)', 'start of construction (late 1931)',
   ['the RKO Building has no article of its own (Wikipedia redirects to Rockefeller Center); height and year are CTBUH\'s'],
   ['official footprint 2,297 m²; city roof 123.7 m', 'OSM part tops 26, 30, 110, 117, 125 m with their outlines'],
   ['`built` starts at 1931.7: no start date found'], 1083861)
rc('rockefeller_plaza_10', 69.5, '10_Rockefeller_Plaza', 'built 1939-1940 (CTBUH; Wikipedia: completed 1940); 69.5 m (CTBUH)', 'months within 1939-40',
   ['"Completed in 1940" — Wikipedia'],
   ['official footprint 5,447 m² (slab and the garage block); city roof 67.0 m', 'OSM part tops 13, 20, 24, 61, 67 m with their outlines; top drawn at the cited 69.5 m'],
   ['`built` 1939.5–1940.9: years only'], 1077284)
rc('rockefeller_plaza_50', 69.5, '50_Rockefeller_Plaza', 'completed 1938 (Wikipedia, CTBUH); start 1937 estimated; 69.5 m (CTBUH)', 'start of construction (1937); roof bulkhead left out',
   ['"Completed in 1938" — Wikipedia'],
   ['official footprint 3,324 m²; city roof 73.7 m', 'OSM part tops 20, 55, 60, 70, 74 m with their outlines; the stack is cut at the cited 69.5 m, which leaves out the 185 m² bulkhead'],
   ['`built` starts at 1937.5: no start date found'], 1083859)
for key, wiki, bin_, nm in [('rockefeller_british_empire_building', 'British_Empire_Building', 1075692, 'British Empire Building'), ('rockefeller_maison_francaise', 'La_Maison_Francaise_(Rockefeller_Center)', 1082656, 'La Maison Française')]:
    rc(key, 38.4, wiki, 'completed 1933 (Wikipedia); start 1932 estimated; roof 90 ft (27.4 m) without the penthouse, model top 38.4 m', 'start of construction (1932); OSM heights stretched by 1.096',
       ['completed 1933; roof 90 ft (27.4 m) excluding the penthouse; six storeys and a 1½-storey penthouse — Wikipedia infobox'],
       ['official footprint about 1,260 m²; the city measures the top at 38.9 / 39.6 m', 'OSM part tops 20, 25 (main roof), 30, 35 m with their outlines'],
       ['the OSM heights are multiplied by 27.4 / 25 so that the main roof meets the cited 90 ft; the penthouse top then comes to 38.4 m, close to the city\'s measurement', '`built` starts at 1932.3: no start date found'], bin_)
rc('radio_city_music_hall', 35.0, 'Radio_City_Music_Hall', 'opened 27 Dec 1932 (Wikipedia); start end of 1931 estimated; height from OpenStreetMap', 'start of construction (end of 1931); no cited height',
   ['opened 27 Dec 1932 — Wikipedia'],
   ['official footprint 4,270 m²; city roof 35.1 m', 'OSM part tops 30 and 35 m'],
   ['`built` starts at 1931.9: no start date found', 'no cited height: the model is the OSM massing; marquee not modelled'], 1083862)
