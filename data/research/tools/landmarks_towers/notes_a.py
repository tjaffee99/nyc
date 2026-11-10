"""Hand-written research notes per landmark (part A). Each entry:
height_m, year_source_url, csv note, short 'estimated' text (report table), and the note blocks."""
WP = 'https://en.wikipedia.org/wiki/'
LPC = 'https://s-media.nyc.gov/agencies/lpc/lp/'

N = {}

N['empire_state_building'] = dict(
    h=381.0, url=WP + 'Empire_State_Building',
    csv='construction started 17 Mar 1930, opened 1 May 1931; height to the roof (102nd floor); 443.2 m with the antenna',
    est='mast widths, buttress heights (343, 352 m), window bands',
    src=[WP + 'Empire_State_Building', LPC + '2000.pdf (LP-2000, 1981)', 'city footprint BIN 1015862', 'OSM parts'],
    cited=[
        'roof 1,250 ft (381.0 m), tip 1,454 ft (443.2 m), top floor 1,224 ft (373.1 m) — Wikipedia infobox; LPC: "1250-foot high"',
        '86th-floor deck at 1,050 ft (320 m) — Wikipedia',
        'five-storey base on the whole lot; set-backs at the 21st, 25th, 30th, 72nd, 81st and 85th storeys; "symmetrical massing" — Wikipedia',
        'tower nine bays wide from the 6th to the 25th floor, seven to the 72nd, six to the 81st, five to the mast — LPC',
        'mooring mast: a 158 ft (48 m) steel shaft above the 86th floor — Wikipedia (→ 320 + 48 = 368 m, drum to the 373.1 m top floor, cap to the 381.0 m roof)',
        'lot 425 × 200 ft — Wikipedia (official footprint: 128.3 × 58.1 m)',
        'construction started 17 Mar 1930; opened 1 May 1931 — Wikipedia',
    ],
    measured=[
        'OSM part tops 17 m (5 floors), 75 (20), 90 (24), 115 (29), 255 (71), 290 (80), 310, 320 and 330 m, with the plan of each level (H-plan recesses of the shaft included)',
        'the OSM tower parts are drawn 2.6 m south of the lot axis; because the building is symmetrical they are moved 2.6 m north onto the axis of the official footprint (centre u 4.2, v 0.85)',
        'the official footprint carries a 453 m² annex west of the lot on 33rd St; its height, 23.8 m, is that of the unnamed OSM/Overture building at that spot',
    ],
    estimated=['mast diameter (13.2 m at its foot is the OSM part; the taper to 11.8 m is estimated), the 102nd-floor drum (radius 4.6–5 m), the four buttresses and their tops (343 and 352 m)', 'the dark window bands in the shaft recesses are decoration'],
)

N['empire_state_antenna'] = dict(
    h=443.2, url=WP + 'Empire_State_Building',
    csv="broadcast tower begun 27 Jul 1950, completed 1953; drawn as today's 62 m pinnacle",
    est="lattice widths; drawn as today's pinnacle for its whole life",
    src=[WP + 'Empire_State_Building'],
    cited=['construction of the broadcast tower began 27 Jul 1950; "the 200-foot (60 m) broadcast tower was completed in 1953" — Wikipedia', "today's pinnacle: 203 ft (61.9 m) in the text, 204 ft in the infobox; tip 1,454 ft (443.2 m) — Wikipedia"],
    measured=['rides on the Empire State Building model (same anchor, no `replaces`)'],
    estimated=['simplification: one model, 381 → 443.2 m, for 1950 to today (the first tower differed slightly in height)', 'lattice widths (3.4 m at the foot, 0.5 m at the tip) and the three platforms'],
)

N['chrysler_building'] = dict(
    h=318.9, url=WP + 'Chrysler_Building',
    csv='excavation mid-Nov 1928, steel 27 Mar 1929, opened 27 May 1930; roof 282 m',
    est='arch profile, spire-base taper, eagle and radiator-cap sizes, 5 m granite band',
    src=[WP + 'Chrysler_Building', LPC + '0992.pdf (LP-0992, 1978)', 'city footprint BIN 1036156', 'OSM parts'],
    cited=[
        'roof 925 ft (282 m), top floor 899 ft, spire 1,046 ft (318.9 m) — Wikipedia infobox; LPC: 1046 feet',
        'the needle: 185 ft long, 8 ft square at its base — Wikipedia (Architectural Forum 1930); LPC: "185-foot spire"',
        'trapezoid lot: 201 ft on Lexington, 167 ft on 42nd St, 205 ft on 43rd St — Wikipedia (official footprint: 60.5 / 50.5 / 61.6 m)',
        '"Above the fourth story, the building is penetrated on the east and west sides by light courts extending to the face of the tower, while on the north and south the structure gradually rises in a series of setbacks" — LPC',
        'set-backs at storeys 16, 18, 23, 28 and 31; none between the 31st and 60th — Wikipedia; LPC: first set-back at the 16th storey, the fourth "to the thirty-first story marks the emergence of the tower shaft"',
        'radiator caps at the 31st-floor corners "spanning about 15 feet" — LPC; eagles at the 61st floor — Wikipedia',
        'Maltese-cross plan above the 60th floor; the crown "a cruciform groin vault" of seven concentric members in Nirosta steel — Wikipedia',
        'excavation mid-Nov 1928 to mid-Jan 1929; first steel 27 Mar 1929; opened 27 May 1930 — Wikipedia',
    ],
    measured=[
        'OSM part tops: base 15 m, set-backs 50, 70, 80, 90 m; shaft 28.7 × 34.9 m to 199 m (61st floor), corners chamfered above 185 m',
        'cross arms 13–16 m wide to 224 m; crown tier tops 235, 242, 249, 256, 262, 267, 272 m with widths 22.2, 20.5, 17.3, 13.9, 9.9, 8.1, 5.9 m and a 7 m arch rise (OSM roof heights)',
        'the OSM parts overhang the official outline by 2–3 m to the south: they are shifted onto the official centroid and clipped to the official outline',
    ],
    estimated=['arches drawn as half-ellipses, each tier a cross of two barrel vaults; the number of triangular windows per arch (7, 5 or 3) is schematic', 'spire base tapering from 5.2 m at 270 m to the cited 8 ft at the 282 m roof', 'eagle length 3.2 m, radiator-cap ornaments, 5 m black granite ground storey'],
)

N['one_world_trade_center'] = dict(
    h=541.3, url=WP + 'One_World_Trade_Center',
    csv='construction 27 Apr 2006, opened 3 Nov 2014; roof 417.0 m',
    est='mast taper, ring width, struts',
    src=[WP + 'One_World_Trade_Center', 'https://www.skyscrapercenter.com/building/one-world-trade-center/98 (CTBUH; listed, figures taken from Wikipedia)', 'city footprint BIN 1088469', 'OSM parts'],
    cited=[
        'roof 1,368 ft (417.0 m); glass parapet 33 ft 4 in (10.16 m); architectural height 1,776 ft (541.3 m); spire 407.9 ft (124.3 m) — Wikipedia',
        '200 ft (61 m) square footprint; windowless base 185 ft (56 m) covering floors 1–19; from the 20th floor the edges are chamfered into eight isosceles triangles, a perfect octagon near the middle, a parapet square turned 45° at the top — Wikipedia',
        'construction began 27 Apr 2006; spire complete 10 May 2013; opened 3 Nov 2014 — Wikipedia',
    ],
    measured=['base square from the official footprint: 62.1 × 62.3 m (3,836 m²)', 'communications ring radius 17.7 m at 417–420 m — OSM part'],
    estimated=['the top square is taken with its corners over the mid-points of the base edges (side 44.0 m = 144 ft), which makes the four upright triangles vertical; CTBUH describes the parapet as "a 150-foot-by-150-foot square, rotated 45 degrees from the base"', 'mast taper (radius 2.9 → 0.3 m), ring width 2.5 m, eight struts'],
)

N['woolworth_building'] = dict(
    h=241.4, url=WP + 'Woolworth_Building',
    csv='construction began 4 Nov 1910, opened 24 Apr 1913; 792 ft',
    est='axis of the 84 vs 86 ft sides, tourelle and lantern sizes, top-stage chamfer',
    src=[WP + 'Woolworth_Building', LPC + '1273.pdf (LP-1273, 1983)', 'city footprint BIN 1087167', 'OSM parts'],
    cited=[
        '792 ft (241.4 m) — Wikipedia, LPC',
        '"The 30-story tower rises above a 30-story base"; the tower is "84\' X 86\' at its base; setbacks on all sides at the 45th floor reduce its dimensions to 69\' X 71\', and again at the 50th floor to 69\' X 61\'"; a tourelle at each corner — LPC',
        'above the 53rd storey a pyramid 105 ft high, the observation gallery above the 55th floor at 730 ft — LPC (→ eave 209.4 m, gallery 222.5 m)',
        'construction officially began 4 Nov 1910; opened 24 Apr 1913 — Wikipedia',
    ],
    measured=[
        'U-shaped base from the official footprint (2,224 m², light court 11.8 m wide open to the west), to 120 m (OSM part top)',
        'stage heights 170 and 194 m — OSM part tops (cross-check: a uniform storey between 120 m and the 209.4 m eave puts the 45th and 50th floors at 174.4 and 193.9 m)',
        'the OSM "tower" parts (29.7 and 24.1 m wide) are wider than the LPC dimensions; the LPC dimensions are used',
    ],
    estimated=['84 ft is taken east–west and 86 ft along Broadway; the tower stands flush with the Broadway front and the upper stages are centred on it', 'top stage drawn with 4.5 m chamfers (OSM draws an octagon)', 'tourelles: radius 2.3 m, tops 203 and 212 m; lantern 5.2 m across'],
)

N['flatiron_building'] = dict(
    h=93.6, url=WP + 'Flatiron_Building',
    csv='completed June 1902, opened 1 Oct 1902 at 285 ft (86.9 m); 307 ft (93.6 m) with the penthouse added afterwards',
    est='start mid-1901, base/capital levels, cornice overhang, penthouse outline, prow height',
    src=[WP + 'Flatiron_Building', LPC + '0219.pdf (LP-0219, 1966; no dimensions)', 'city footprint BIN 1016278'],
    cited=[
        '"it originally stood 285 ft tall"; the article now gives 307 ft (93.6 m) and 22 floors; "originally 20 floors; a cowcatcher retail space and penthouse were added shortly after the building\'s opening" — Wikipedia',
        'completed June 1902, opened 1 Oct 1902 — Wikipedia infobox',
    ],
    measured=['triangle and prow from the official footprint (1,019 m²); the city measures the roof at 91.5 m'],
    estimated=[
        'construction start 1901.45 (the site was bought in May 1901; no start date found)',
        'main roof at 86.9 m and the penthouse to 93.6 m: CTBUH gives roof 86.87 m and architectural height 93.57 m',
        'base, shaft and capital levels (16, 70, 84 m), the 1.5 m cornice, the penthouse outline, the 5.5 m prow',
        'simplification: penthouse and prow are drawn from 1902 although they were added a few years later',
    ],
)

N['rockefeller_30'] = dict(
    h=259.1, url=WP + '30_Rockefeller_Plaza',
    csv='start 1931 (CTBUH), steelwork from Mar 1932, opened 1933; 850 ft',
    est='nothing but colours; month of the 1931 start',
    src=[WP + '30_Rockefeller_Plaza', LPC + '1446.pdf (LP-1446, Rockefeller Center, 1985; not mined)', 'city footprint BIN 1076262', 'OSM parts'],
    cited=['roof 850 ft (259.1 m), 66 floors, completed 1933 — Wikipedia infobox', '"work on its superstructure started in March 1932" — Wikipedia'],
    measured=[
        'official footprint 9,137 m²: the slab, the studio wings and the 16-storey building on Sixth Avenue are one footprint',
        'OSM part tops: base 10 m, wings 20 / 40 / 43 m, west building 70 m, slab steps 45 / 125 / 133 / 175 / 190 / 220 / 235 / 245 m, top stage (70.3 × 19.6 m) to 260 m — drawn to the cited 259.1 m',
    ],
    estimated=['none in the geometry; `built` starts at 1931.6: CTBUH gives the year 1931, the month is a guess'],
)

N['wtc_7'] = dict(
    h=226.5, url=WP + '7_World_Trade_Center',
    csv='construction began 7 May 2002, opened 23 May 2006; architectural 743 ft, roof 741 ft',
    est='height of the louvred base (36 m)',
    src=[WP + '7_World_Trade_Center', 'city footprint BIN 1086510'],
    cited=['architectural 743 ft (226.5 m), roof 741 ft (225.9 m), 52 floors — Wikipedia infobox', 'the first ten floors hold a substation behind stainless-steel louvres — Wikipedia', 'construction began 7 May 2002; opened 23 May 2006 — Wikipedia'],
    measured=['parallelogram footprint 3,002 m²; city roof 226.7 m'],
    estimated=['the height of the ten-storey louvred base, 36 m'],
)

N['wtc_3'] = dict(
    h=328.9, url=WP + '3_World_Trade_Center',
    csv='groundbreaking Jan 2008, podium complete Nov 2012, opened 11 Jun 2018; 1,079 ft',
    est='podium and set-back heights are OSM, unverified; bracing schematic',
    src=[WP + '3_World_Trade_Center', 'city footprint BIN 1088797', 'OSM parts'],
    cited=['1,079 ft (328.9 m), 80 floors — Wikipedia infobox', 'groundbreaking January 2008; lower podium completed November 2012; opened 11 Jun 2018; K-bracing on the facade — Wikipedia'],
    measured=['outlines from the official footprint (5,262 m²)', 'OSM part tops: podium 75 m, south section 220 m, north section 281 m. OSM\'s own top (352 m) is 23 m above the cited height, so these levels are weak'],
    estimated=['K-bracing drawn schematically on the east and west faces'],
)

N['wtc_4'] = dict(
    h=297.7, url=WP + '4_World_Trade_Center',
    csv='groundbreaking Jan 2008, opened 13 Nov 2013; 297.7 m (CTBUH; Wikipedia roof 978 ft)',
    est='podium 25 m is OSM, unverified; plan areas 20 % under the cited floor areas',
    src=[WP + '4_World_Trade_Center', 'city footprint BIN 1088795', 'OSM parts'],
    cited=['roof 978 ft (298.1 m) — Wikipedia infobox', 'floors 7–46 are parallelograms of 44,000 sq ft, floors 48–63 trapezoids of 36,000 sq ft — Wikipedia', 'groundbreaking January 2008; opened 13 Nov 2013 — Wikipedia'],
    measured=['podium on the official footprint (4,547 m²), 25 m (OSM)', 'lower parallelogram and upper trapezoid outlines and the 220 m break — OSM parts'],
    estimated=['weak spot: the OSM plans (3,281 and 2,547 m²) are about 20 % smaller than the cited floor areas; the OSM outlines are kept', 'the 220 m break is OSM; CTBUH lists a deck at 218.0 m, which supports it (the floor numbers at a uniform storey would give about 190 m)'],
)

N['metlife_tower'] = dict(
    h=213.4, url=WP + 'Metropolitan_Life_Insurance_Company_Tower',
    csv='tower built 1907-1909 (LPC); 700 ft',
    est='clock height (95 m), base band, cornice, dome and lantern radii',
    src=[WP + 'Metropolitan_Life_Insurance_Company_Tower', LPC + '1530.pdf (LP-1530, 1989)', 'city footprint BIN 1016741', 'OSM parts'],
    cited=[
        'roof 700 ft (213.4 m) — Wikipedia; LPC: the lantern is "700 feet above the sidewalk"',
        'plan 75 ft on Madison Avenue by 85 ft on 24th Street — Wikipedia, LPC (official footprint: 21.8 × 26.2 m)',
        '"from within the arcaded capital rises a setback capped with a pyramidal spire, cupola and lantern" — LPC',
        'clock faces 26.5 ft in diameter on the 25th–27th floors — Wikipedia',
        'built 1907–09 — LPC',
    ],
    measured=['OSM part tops: shaft 150 m, set-back stage 150–165 m (22.9 × 20.9 m), pyramid 165–190 m, cupola 190–206 m, top 213 m'],
    estimated=['clock centre at 95 m (26th of about 41 shaft storeys)', 'the cupola top at 200 m (OSM) agrees with CTBUH\'s roof height of 200.26 m', '18 m base band, cornice, cupola radius 3.8 m, lantern radius 0.9 m'],
)

N['wall_40'] = dict(
    h=282.5, url=WP + '40_Wall_Street',
    csv='construction began May 1929, completed 1 May 1930; 927 ft',
    est='lantern and spire proportions',
    src=[WP + '40_Wall_Street', LPC + '1936.pdf (LP-1936, 1995)', 'city footprint BIN 1001018', 'OSM parts'],
    cited=[
        '927 ft (282.5 m) — Wikipedia, LPC; 70 floors (LPC: 71)',
        '"crowned by a pyramidal roof capped by a spire"; roof of lead-coated copper with a spire and flagpole; set-backs atop the 12th, 19th, 23rd, 26th, 28th and 29th storeys — LPC',
        'construction began May 1929; completed 1 May 1930 — Wikipedia',
    ],
    measured=['OSM levels 30, 40, 64, 75, 90, 100, 112, 123, 130, 212, 230 m with their outlines; pyramid base 23.3 m square at 230 m, pyramid part to 262 m'],
    estimated=['pyramid drawn to a 4.4 m platform at 259 m, lantern to 264 m, spire to the cited 282.5 m', '`replaces` is the official outline shrunk 3 m so that the 100 m neighbour (BIN 1001017) is not hidden by the viewer\'s tall-sliver rule'],
)

N['pine_70'] = dict(
    h=290.2, url=WP + '70_Pine_Street',
    csv='construction May 1930, 24 months, completed 1932; 952 ft incl. the 124 ft spire',
    est='lantern and pinnacle widths',
    src=[WP + '70_Pine_Street', LPC + '2441.pdf (LP-2441, 2011)', 'city footprint BIN 1001007', 'OSM parts'],
    cited=[
        'architectural 952 ft (290.2 m), roof 850 ft, top floor 800 ft, 67 floors — Wikipedia infobox',
        'spire 124 ft above the observation deck: a glass lantern 27 ft and a stainless-steel pinnacle 97 ft — Wikipedia; LPC: "27-foot-tall tiered glass lantern, and a 97-foot-tall stainless steel spire" (→ deck 252.4 m, lantern to 260.6 m)',
        'construction started May 1930 and took 24 months — Wikipedia',
    ],
    measured=['OSM levels from 45 m to 252 m (18 steps) with their outlines'],
    estimated=['lantern radius 3.6 m, pinnacle 3.2 → 1 m'],
)

N['citigroup_center'] = dict(
    h=278.9, url=WP + 'Citigroup_Center',
    csv='groundbreaking Apr 1974 (work a year later), topped out 6 Oct 1976, completed 1977; 915 ft',
    est='church form, plaza structures; tower side derived from the 45° roof',
    src=[WP + 'Citigroup_Center', LPC + '2582.pdf (LP-2582, 2016)', 'city footprint BIN 1036474', 'OSM parts'],
    cited=[
        '915 ft (278.9 m), 59 floors — Wikipedia, LPC',
        '"it rises on four 24-foot-square super columns and a massive octagonal elevator core"; each column "centered beneath one facade", "more than 100 feet tall"; roof "cut off at a 45-degree angle"; the church set at 45° to the tower — LPC',
        'stilts rising 112 ft; the roof "rises 160 ft above the top story and faces south, sloping at a 45-degree angle" — Wikipedia',
        'groundbreaking April 1974, work twelve months later; topped out 6 Oct 1976; completed 1977 — Wikipedia',
    ],
    measured=[
        'official footprint 5,686 m²: tower, St Peter\'s Church and the east wing in one polygon; the tower is placed with its west and south faces on the footprint edges',
        'OSM parts: east wing 26 m with a 30 m centre, terraces 22 / 18 / 14 / 10 m, church 15–17 m, core 16.5 m across',
    ],
    estimated=[
        'tower side 47.9 m: a 45° roof with a 160 ft (48.8 m) rise spans the whole depth (OSM draws 49.4 m); eave at 231 m',
        'church drawn as a granite prism with a tapered top; plaza structures 7 m',
        'plan check by projection (the tower stands on stilts)',
    ],
)

N['park_432'] = dict(
    h=425.5, url=WP + '432_Park_Avenue',
    csv='excavation early 2012, topped out 10 Oct 2014, completed 23 Dec 2015; 1,396 ft',
    est='windbreak heights, plaza (1.2 m) and pavilion (12 m) heights',
    src=[WP + '432_Park_Avenue', 'city footprints BIN 1088817 and 1035787', 'OSM parts'],
    cited=['architectural 1,396 ft (425.5 m), 85 floors numbered to 96 — Wikipedia infobox', '"Five two-story windbreaks, spaced every 12 floors from the top, are unenclosed" — Wikipedia', 'excavation early 2012; topped out 10 Oct 2014; completed 23 Dec 2015 — Wikipedia'],
    measured=['tower square 28.7 × 28.2 m (OSM part; the 93 ft / 28.5 m of the brief agrees)', 'retail building on 57th St 30 m (OSM part); lot outline from the official footprint'],
    estimated=[
        'windbreak heights from a uniform 4.43 m level (425.5 m over 96 numbered levels)',
        'the plaza on 56th St (1.2 m) and the Park Avenue pavilion (12 m) have no measured height',
        '`replaces` is the main lot only: the 7.6 m strip BIN 1035787 (recorded at 425.5 m) is hidden by the viewer\'s tall-sliver rule; an outline wide enough to contain it would also hide the 80 m neighbour BIN 1035788',
    ],
)
