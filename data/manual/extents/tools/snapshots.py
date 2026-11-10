"""Definitions of the extent snapshots: which map, how it was georeferenced, and the traced rings.
Vertices: ("Street A", "Street B", (x, y) hint) or (x, y) local metres (X = UTM18N E - 580000, Y = N - 4500000)."""

NYPL = "https://digitalcollections.nypl.org/items/"
WARPER = "NYPL Map Warper control points (NYC Space/Time Directory dump mapwarper.objects.ndjson, map %s), thin-plate spline; residual = cross-validated RMS"

SNAPSHOTS = {}

SNAPSHOTS["manhattan_1767"] = dict(
    place="manhattan", year=1767, map_id=15264,
    map="Plan of the City of New York in North America, surveyed in the years 1766 & 1767 — Bernard Ratzer (engr. T. Kitchin, publ. Jefferys & Faden, London 1776)",
    map_url=NYPL + "510d47da-f071-a3d9-e040-e00a18064a99",
    scan_url="https://images.nypl.org/index.php?id=434801&t=u",
    georef=WARPER % 15264 + " over 150 of 153 points", residual_m=9.2,
    confidence="medium-high",
    method="hand-traced on the warped map; vertices at today's street intersections where the edge follows a street",
    note="Built-up = the blocks Ratzer stipples dark (blocks drawn in outline with field pattern, e.g. Delancey's grid, are laid out, not built). "
         "Edges: Hudson shore of the map (about Greenwich St), Reade St, Broadway, the Common (open, left out), Park Row, the blocks between Park Row and the Fresh Water, "
         "Baxter / Bayard St, Madison St, Catherine St, the East River wharf line of the map (between today's Water and Front Sts). Includes Fort George. "
         "Ring bowery: building rows drawn along Bowery Lane up to Broome St (frontage only, 35 m either side). Edge uncertainty about one block.",
    rings={
        "city": [
            (3255, 6115), (3200, 6280), (3207, 6480), (3227, 6600), (3264, 6712), (3298, 6880), (3314, 7034),
            (3334, 7160), (3368, 7300), (3417, 7398), (3472, 7440), (3522, 7540),
            ("Greenwich Street", "Reade Street", (3564, 7794)),
            ("Broadway", "Reade Street", (3994, 7550)),
            ("Broadway", "Vesey Street", (3720, 7200)),
            ("Park Row", "Beekman Street", (3900, 7250)),
            (4110, 7335), (4125, 7422), (4235, 7422), (4300, 7400),
            ("Park Row", "Pearl Street", (4395, 7382)),
            ("Baxter Street", "Worth Street", (4455, 7560)),
            ("Mulberry Street", "Bayard Street", (4530, 7680)),
            ("Bowery", "Bayard Street", (4745, 7630)),
            ("Bowery", "Division Street", (4640, 7440)),
            ("Madison Street", "Oliver Street", (4640, 7270)),
            ("Madison Street", "Catherine Street", (4755, 7290)),
            ("Cherry Street", "Catherine Street", (4745, 7095)),
            (4760, 7040), (4640, 7005), (4600, 6955), (4520, 6985), (4450, 6895), (4335, 6795), (4225, 6695),
            (4115, 6595), (4005, 6488), (3895, 6425), (3725, 6268), (3595, 6188), (3475, 6128), (3415, 6115),
        ],
        "bowery": {"buffer": [("Bowery", "Bayard Street", (4745, 7630)), ("Bowery", "Grand Street", (4880, 7930)), ("Bowery", "Broome Street", (4910, 8010))], "width": 35},
    },
)

LOC = "https://www.loc.gov/item/"
CLS = "built blocks classified by tone on the warped map (tools/classify.py, parameters in tools/classify_runs.py), clipped to a hand-drawn envelope"

SNAPSHOTS["manhattan_1660"] = dict(
    place="manhattan", year=1660, map_id="castello1660",
    map="Afbeeldinge van de Stadt Amsterdam in Nieuw Neederlandt (the Castello Plan), after Jacques Cortelyou's survey of 1660; copy of c. 1665-70 in the Biblioteca Medicea Laurenziana, Florence (NYPL photograph, Stokes 1660-B-42A)",
    map_url="https://commons.wikimedia.org/wiki/File:Afbeeldinge_van_de_Stadt_Amsterdam_in_Nieuw_Neederlandt_(NYPL_Hades-118555-54682).tif",
    scan_url="https://images.nypl.org/index.php?id=54682&t=u",
    georef="13 control points picked here on the plan against today's street intersections (tools/gcps_own.json, castello1660), thin-plate spline; "
           "the plan is a bird's-eye drawing, not a survey to scale", residual_m=24.5,
    confidence="medium",
    method="edges set on today's streets after reading the warped plan: every block inside these edges carries houses on the plan",
    note="The whole town below the wall: Wall St (the palisade), Pearl St (the East River shore of 1660: the houses stood on its landward side), "
         "State St (the shore behind the fort), Broadway. Includes Fort Amsterdam (today's Custom House block). West of Broadway the plan shows gardens, "
         "the Company's garden and the burial ground down to the Hudson shore (about Greenwich St / Trinity Place) with houses only along Broadway: "
         "ring broadway_west is that frontage (35 m deep, Beaver St to Morris St; the row thins out north of it and is left out). "
         "Block interiors east of Broadway are gardens and orchards on the plan; about 340 houses stood in the town.",
    rings={
        "town": [
            ("Broadway", "Wall Street", (3482, 6776)),
            ("William Street", "Wall Street", (3672, 6635)),
            ("Pearl Street", "Wall Street", (3805, 6544)),
            ("Pearl Street", "Beaver Street", (3797, 6532)),
            ("Pearl Street", "Hanover Square", (3675, 6433)),
            ("Pearl Street", "Broad Street", (3498, 6310)),
            ("Pearl Street", "Whitehall Street", (3379, 6270)),
            ("Pearl Street", "State Street", (3259, 6273)),
            ("State Street", "Bridge Street", (3261, 6324)),
            ("State Street", "Battery Place", (3272, 6426)),
            ("Broadway", "Beaver Street", (3350, 6479)),
            ("Broadway", "Exchange Place", (3415, 6673)),
        ],
        "broadway_west": {"buffer": [("Broadway", "Beaver Street", (3350, 6479)), ("Broadway", "Morris Street", (3353, 6577))], "width": 35},
    },
)

SNAPSHOTS["manhattan_1797"] = dict(
    place="manhattan", year=1797, map_id=15327,
    map="A New & Accurate Plan of the City of New York in the State of New York in North America, published in 1797 — Benjamin Taylor, engraved by John Roberts (the Taylor-Roberts plan)",
    map_url=NYPL + "510d47e4-7374-a3d9-e040-e00a18064a99",
    scan_url="https://images.nypl.org/index.php?id=psnypl_map_303&t=u",
    georef=WARPER % 15327 + " over 30 points", residual_m=15.8,
    confidence="medium-high", method=CLS,
    note="Built-up = the blocks and parts of blocks the plan hatches (it leaves laid-out but empty blocks in outline and hatches a half-built block in part). "
         "The envelope keeps out the meadows, orchards and hill hachures north of the town and the plan's wharf line; the Park (the Common) is left out. "
         "East of about Rutgers St the plan was read to x = 5750 only.",
    rings={"city": {"file": "manhattan_1797_cls.json"}},
)

SNAPSHOTS["manhattan_1836"] = dict(
    place="manhattan", year=1836, map_id="colton1836",
    map="Topographical Map of the City and County of New-York, and the adjacent Country — J. H. Colton & Co., New York 1836 (engr. S. Stiles & Co.)",
    map_url=LOC + "2007627512/",
    scan_url="https://tile.loc.gov/image-services/iiif/service:gmd:gmd380:g3804:g3804n:wd000155/2800,3300,5200,5000/full/0/default.jpg",
    georef="georeferenced here: six points read by eye, then 60 control points found by matching the map's street strips to today's centrelines in 700 m windows "
           "(tools/autoalign.py; tools/gcps_own.json, colton1836), thin-plate spline; residual = cross-validated RMS", residual_m=7.7,
    confidence="high", method=CLS,
    note="Built-up = the parts of blocks Colton shades (unbuilt blocks and the unbuilt parts of a block are left white). Envelope = the map's bulkhead line, drawn about "
         "30 m inside it (the water is ruled dark near the shore), so the outermost waterfront strip can be missing; the Battery, the Park and Tompkins Square "
         "(drawn with trees) are left out; the hachured grounds of Bellevue and Murray Hill were not read. Shaded pieces narrower than about 25 m are dropped.",
    rings={"city": {"file": "manhattan_1836_cls.json"}},
)

SNAPSHOTS["manhattan_1852"] = dict(
    place="manhattan", year=1852, map_id=14758,
    map="Map of the City of New-York extending northward to Fiftieth St., surveyed and drawn by John F. Harrison, C.E. — published by M. Dripps, New York (first published 1852)",
    map_url=NYPL + "510d47e2-63a9-a3d9-e040-e00a18064a99",
    scan_url="https://images.nypl.org/index.php?id=1528179&t=u",
    georef=WARPER % 14758 + " over 36 points", residual_m=6.1,
    confidence="medium", method=CLS,
    note="The map draws every building south of 50th St. Built-up = where the drawn buildings (hatched footprints) make the sheet darker than its local paper tone "
         "(threshold calibrated on fully built and on empty parts of the sheet: fully built blocks come out 88-94 % covered, farmland under 8 %), closed across streets, "
         "yards and squares under 0.6 ha filled. NYPL's copy is varnished and dark, so thinly built blocks at the edge can be missed or over-read by a block. "
         "The Map Warper record of this copy is dated 1857; which state of the plate it is was not checked (the map was first issued in 1852). "
         "North of 50th St the map shows nothing.",
    rings={"city": {"file": "manhattan_1852_cls.json"}},
)

SNAPSHOTS["manhattan_1743"] = dict(
    place="manhattan", year=1743, map_id=15328,
    map="A Plan of the City and Environs of New York as they were in the years 1742-1743 and 1744 — drawn by David Grim in 1813, in the 76th year of his age, from recollection (lithograph for Valentine's Manual, 1854)",
    map_url="https://digitalcollections.nypl.org/items/510d47e4-7375-a3d9-e040-e00a18064a99",
    scan_url="https://images.nypl.org/index.php?id=psnypl_map_304&t=u",
    georef=WARPER % 15328 + " over 13 points; the plan is a recollection, not a survey", residual_m=13.4,
    confidence="low-medium",
    method="hand-traced: the northern edge at today's street intersections after reading the warped plan; the waterfront edges are not Grim's "
           "(his shoreline is schematic) but Ratzer's Hudson shore of 1767 and the line of Water St",
    note="Built-up = the blocks Grim draws with shaded house fronts. Northern edge: Fulton St west of Broadway (St Paul's, 1766, was built in a field north of it), "
         "Ann St, Nassau St, Beekman St (the tan yards of the Swamp beyond are left out), Pearl St to Peck Slip. East River edge on Water St "
         "(Lyne's survey of 1728-30 and Grim both have the built front on Water / Dock St; the slips beyond were open water). "
         "Edge uncertainty one to two blocks; the plan was drawn seventy years after the date it shows.",
    rings={
        "city": [
            (3255, 6115), (3200, 6280), (3207, 6480), (3227, 6600), (3264, 6712), (3298, 6880), (3312, 7010),
            ("Church Street", "Fulton Street", (3560, 7080)),
            ("Broadway", "Fulton Street", (3690, 7150)),
            ("Broadway", "Ann Street", (3720, 7180)),
            ("Nassau Street", "Ann Street", (3830, 7120)),
            ("Nassau Street", "Beekman Street", (3900, 7200)),
            ("William Street", "Beekman Street", (4000, 7130)),
            ("Gold Street", "Beekman Street", (4080, 7090)),
            ("Pearl Street", "Beekman Street", (4180, 7010)),
            ("Pearl Street", "Peck Slip", (4290, 7090)),
            ("Water Street", "Peck Slip", (4330, 7040)),
            ("Water Street", "Beekman Street", (4230, 6950)),
            ("Water Street", "Fulton Street", (4150, 6880)),
            ("Water Street", "Maiden Lane", (4010, 6720)),
            ("Water Street", "Wall Street", (3860, 6500)),
            ("Water Street", "Old Slip", (3740, 6400)),
            ("Water Street", "Broad Street", (3530, 6270)),
            ("Water Street", "Whitehall Street", (3410, 6220)),
            ("State Street", "Whitehall Street", (3395, 6195)),
            (3400, 6125),
        ],
    },
)

USGS_NOTE = ("Built-up = where heavy black ink (block fronts drawn as bands at least 15 m thick, solid blocks; not road casings, thin block outlines, railways, lettering) "
             "covers more than 22 % of the ground within 80 m: about 40 % of a block's frontage built. Fully built blocks read 0.55-0.65, Central Park 0.01. "
             "Closed across streets (40 m); parts under 1.5 ha dropped, holes under 1 ha filled; piers beyond 60 m from a street of today and ink on today's railways left out. "
             "The sheets were used as georeferenced by USGS (NAD27 polyconic -> UTM 18N): against today's streets they sit within about 20-40 m (read by eye on four crops; "
             "automatic matching did not converge on these sheets), so edges are good to about one short block. ")
USGS_URL = "https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/"
USGS97 = ("USGS 1:62,500 topographic quadrangles: Harlem, N.Y.-N.J. (edition of 1897), Brooklyn, N.Y. (1897), Staten Island, N.J.-N.Y. (1898), Paterson, N.J.-N.Y. (1898) — U.S. Geological Survey")
USGS97_URL = " ".join(USGS_URL + f for f in ("NY/NY_Harlem_129718_1897_62500_geo.tif", "NY/NY_Brooklyn_123118_1897_62500_geo.tif", "NY/NJ_Staten%20Island_255388_1898_62500_geo.tif", "NJ/NJ_Paterson_255300_1898_62500_geo.tif"))
USGS89 = ("USGS 1:62,500 topographic quadrangles: Harlem, N.Y.-N.J. (edition of 1891), Brooklyn, N.Y. (edition of 1891) — U.S. Geological Survey")
USGS89_URL = " ".join(USGS_URL + f for f in ("NY/NJ_Harlem_472515_1891_62500_geo.tif", "NY/NY_Brooklyn_8033120_1891_62500_geo.tif"))
Y97 = "Year: the editions of 1897-98 (USGS record: content 1897); the sheets were first surveyed about 1888-89 and revised for these editions; which culture was revised was not checked on the collars. "
Y89 = "Year: USGS record gives 1889 as the start of the content date range of the 1891 editions (first survey); the collar was not read. "
WEST = "West of 74 deg 00' W (the lower west side) this survey's Paterson and Staten Island sheets were not read: there the polygon is the earlier snapshots only. "


def usgs(place, year, extra="", conf="medium", also=None):
    d = dict(place=place, year=year, map_id=None,
             map=USGS97 if year == 1897 else USGS89, map_url=USGS97_URL if year == 1897 else USGS89_URL,
             scan_url="https://tnmaccess.nationalmap.gov/api/v1/products?datasets=Historical%20Topographic%20Maps&bbox=-74.05,40.68,-73.90,40.88",
             georef="the sheets' own georeference (USGS GeoTIFF, NAD27), no further fit; offset against today's streets about 20-40 m (by eye)", residual_m=30,
             confidence=conf, method="heavy black ink share on the sheet (tools/usgs_extent.py), clipped to the borough (TIGER 2024 county + 150 m)",
             note=USGS_NOTE + (Y97 if year == 1897 else Y89) + extra,
             licence="public domain (USGS); reading CC0",
             rings={"sheet": {"file": f"usgs_{place}_{year}.json"}})
    if also:
        d["also_contains"] = also
    return d


SNAPSHOTS["manhattan_1889"] = usgs("manhattan", 1889, WEST + "The 1891 Harlem scan is faded brown; its ink threshold is set per sheet.", conf="low-medium")
SNAPSHOTS["manhattan_1897"] = usgs("manhattan", 1897, "Includes Harlem, Manhattanville, Carmansville and the built parts of Washington Heights and Inwood as separate parts where they are not yet joined to the city.")

SNAPSHOTS["brooklyn_1767"] = dict(
    place="brooklyn", year=1767, map_id=15264,
    map=SNAPSHOTS["manhattan_1767"]["map"], map_url=SNAPSHOTS["manhattan_1767"]["map_url"], scan_url=SNAPSHOTS["manhattan_1767"]["scan_url"],
    georef=SNAPSHOTS["manhattan_1767"]["georef"] + " (few of them on the Long Island side)", residual_m=9.2,
    confidence="medium",
    method="hand-traced on the warped map (free vertices: none of today's street lines existed except the ferry road, today's Old Fulton St)",
    note="The ferry village only ('Brookland Ferry'): the houses Ratzer draws at the landing and along the ferry road for about 400 m, and the group south-west of the landing under the Heights. "
         "The church village of Brooklyn (about Fulton St and Hoyt St, 1.5 km inland), Bedford and the farms are scattered houses, not built-up blocks, and are left out. "
         "A sheet join crosses the map just south of the village.",
    rings={"ferry": [(5060, 6300), (5110, 6285), (5140, 6250), (5200, 6200), (5290, 6100), (5345, 6010), (5310, 5990), (5235, 6075), (5150, 6150),
                     (5080, 6120), (5010, 6080), (4960, 6090), (4925, 6130), (4960, 6180), (5010, 6230), (5040, 6270)]},
)

COLTON_BK = dict(
    map=SNAPSHOTS["manhattan_1836"]["map"], map_url=SNAPSHOTS["manhattan_1836"]["map_url"], scan_url=SNAPSHOTS["manhattan_1836"]["scan_url"],
    georef="as manhattan_1836, refined over Brooklyn and Williamsburgh with 19 windows matched to today's streets (tools/gcps_own.json, colton1836_bk), thin-plate spline", residual_m=9.1,
    confidence="medium-high", method=CLS)
SNAPSHOTS["brooklyn_1836"] = dict(
    place="brooklyn", year=1836, map_id="colton1836_bk", **COLTON_BK,
    note="The City of Brooklyn (chartered 1834) as Colton shades it: the parts of blocks built on, from the Heights and the ferry to about Bridge / Gold St and south to about Atlantic St, "
         "with outlying built pieces towards Fort Greene and South Brooklyn. The Navy Yard (drawn with buildings but not shaded as blocks) is left out. "
         "Colton's map shows Brooklyn only as far as the sheet reaches (about Bergen St in the south, Clinton Av in the east).",
    rings={"city": {"file": "brooklyn_1836_cls.json"}},
)
SNAPSHOTS["williamsburgh_1836"] = dict(
    place="williamsburgh", year=1836, map_id="colton1836_bk", **COLTON_BK,
    note="The village of Williamsburgh (incorporated 1827) as Colton shades it: built pieces along Grand St, the ferry and the First-Fourth Sts (today Kent to Bedford Avs); "
         "most of the laid-out grid is white (unbuilt) on the map. The east edge of the sheet cuts the village at about today's Union Av.",
    rings={"village": {"file": "williamsburgh_1836_cls.json"}},
)
SNAPSHOTS["brooklyn_1889"] = usgs("brooklyn", 1889, "The whole of Kings County on the sheet (Brooklyn, Williamsburgh, Bushwick, and the towns of Flatbush, New Lots, Gravesend, New Utrecht, Flatlands as separate parts). "
                                  "West of 74 deg 00' W (the Red Hook and Bay Ridge shore) nothing was read.", also=["williamsburgh_1836"])
SNAPSHOTS["brooklyn_1897"] = usgs("brooklyn", 1897, "The whole borough, the old towns as separate parts where not yet joined.")
SNAPSHOTS["queens_1889"] = usgs("queens", 1889, "Long Island City, Astoria, Flushing, College Point, Jamaica, Newtown ... as separate parts.", conf="low-medium")
SNAPSHOTS["queens_1897"] = usgs("queens", 1897, "Long Island City, Astoria, Flushing, College Point, Whitestone, Jamaica, Newtown, Woodhaven ... as separate parts. East of 73 deg 45' W (Hempstead and Oyster Bay sheets) nothing was read.")
SNAPSHOTS["bronx_1889"] = usgs("bronx", 1889, "Mott Haven, Melrose, Morrisania, Tremont, Fordham, West Farms ... (the 23rd and 24th wards) as parts.", conf="low-medium")
SNAPSHOTS["bronx_1897"] = usgs("bronx", 1897, "Mott Haven, Morrisania, Tremont, Fordham, West Farms, Williamsbridge, Wakefield, Westchester, Unionport, City Island ... as parts. "
                               "Platted tracts with houses drawn block by block (Unionport, Wakefield) read as partly built-up.")
SNAPSHOTS["staten_island_1897"] = usgs("staten_island", 1897, "The north and east shore villages (New Brighton, Tompkinsville, Stapleton, Port Richmond, West New Brighton ...) as parts. "
                                       "South of 40 deg 30' N (Tottenville) nothing was read.", conf="low-medium")

WIKI = "https://en.wikipedia.org/wiki/"
SNAPSHOTS["fire_1776"] = dict(
    place="fire_1776", year=1776, kind="burned_district", no_nest=True, map_id=15264,
    map="no map traced: outline constructed from the written description in Wikipedia, 'Great Fire of New York (1776)'",
    map_url=WIKI + "Great_Fire_of_New_York_(1776)", scan_url=None,
    georef="today's street intersections; Hudson shore from the Ratzer plan of 1767 (manhattan_1767)", residual_m=None,
    confidence="low",
    method="ESTIMATED outline from a text, not from a map of the burned district",
    note="Fire of 21 September 1776. Source text: 'the fire began in the Fighting Cocks Tavern, near Whitehall Slip ... the flames spread north and west ... "
         "The fire crossed Broadway near Beaver Street and then burned most of the city between Broadway and the Hudson River ... It may also have been stopped by "
         "the relatively undeveloped property of King\'s College, located at the northern end of the fire-damaged area ... Estimates for the number of buildings destroyed "
         "range from 400 to 1,000 ... Among the buildings destroyed was Trinity Church ...; St. Paul\'s Chapel survived.' "
         "Drawn from that: ring south = Whitehall St to Broad St, Pearl St to Beaver St (ESTIMATED: the text gives only the start and the crossing point); "
         "ring west = Broadway to the Hudson shore of 1767 from Beaver St to Barclay St (King's College stood between Barclay and Murray Sts), "
         "without the St Paul's block (Broadway - Church St, north of Fulton St). The article reproduces a 1776 map with the burned blocks marked in red "
         "('over 20 city blocks'); it was not traced here. Not a retreat of the built-up area: do not subtract it from the extents, end the buildings inside it in 1776.",
    rings={
        "south": [("Pearl Street", "Whitehall Street", (3379, 6270)), ("Pearl Street", "Broad Street", (3498, 6310)),
                  ("Broad Street", "Beaver Street", (3501, 6479)), ("Broadway", "Beaver Street", (3350, 6479))],
        "west": [("Broadway", "Beaver Street", (3350, 6479)), ("Broadway", "Fulton Street", (3690, 7150)), ("Church Street", "Fulton Street", (3560, 7080)),
                 ("Church Street", "Barclay Street", (3640, 7300)), ("Greenwich Street", "Barclay Street", (3450, 7380)),
                 (3334, 7160), (3314, 7034), (3298, 6880), (3264, 6712), (3227, 6600), (3250, 6500)],
    },
)
SNAPSHOTS["fire_1835"] = dict(
    place="fire_1835", year=1835, kind="burned_district", no_nest=True, map_id="colton1836",
    map="no map traced: outline constructed from the written description in Wikipedia, 'Great Fire of New York' (1835)",
    map_url=WIKI + "Great_Fire_of_New_York", scan_url=None,
    georef="today's street intersections", residual_m=None,
    confidence="low",
    method="ESTIMATED outline from a text, not from a map of the burnt district",
    note="Fire of 16-17 December 1835. Source text: 'The fire began ... in a five-story warehouse at 25 Merchant Street, now known as Beaver Street, at the intersection of "
         "Hanover Street and Wall Street ... The fire covered 17 city blocks and destroyed between 530 and 700 buildings. This part of the city is now known as Coenties Slip, "
         "an area between the East River and Maiden Lane in the north and William Street in the west.' Drawn from that: William St on the west, the East River (South St) on the east, "
         "Broad St / Coenties Slip on the south. North edge ESTIMATED at Wall St, not Maiden Lane: the area up to Maiden Lane holds about twice 17 blocks, the Merchants' Exchange "
         "on the south side of Wall St burned, and the usual account has the north side of Wall St saved; this was not checked against the 1836 maps of the burnt district. "
         "Colton's map of 1836 (manhattan_1836) already shades these blocks as built: rebuilding was immediate. Not a retreat: end the buildings inside it in 1835.",
    rings={
        "district": [("Wall Street", "William Street", (3672, 6635)), ("Wall Street", "South Street", (3930, 6460)), ("South Street", "Broad Street", (3560, 6180)),
                     ("Pearl Street", "Broad Street", (3498, 6310)), ("William Street", "Beaver Street", (3633, 6500))],
    },
)

SNAPSHOTS["manhattan_1867"] = dict(
    place="manhattan", year=1867, map_id=8578,
    map="Plan of New York City, from the Battery to Spuyten Duyvil Creek, showing every lot and building thereon — M. Dripps, New York 1867 (based on the surveys of Randel & Blackwell and J. F. Harrison), sheets 9-18 of 20",
    map_url="https://digitalcollections.nypl.org/items/510d47e2-49f3-a3d9-e040-e00a18064a99 (sheet 9; the other sheets follow in the same NYPL item series)",
    scan_url="https://images.nypl.org/index.php?id=1520732&t=u (sheet 9; sheets 10-18: ids 1520733-1520741)",
    georef="NYPL Map Warper control points, one fit per sheet (maps 8575-8584; 3 to 5 points each, affine); cross-validated residual by sheet 0-27 m, median 8 m; "
           "sheet 12 sits about 25 m off today's streets by eye; a street-matching refinement found too few windows and was not applied", residual_m=10,
    confidence="medium",
    method="every sheet read by tone inside its Map Warper mask (tools/mosaic.py), the readings merged",
    note="The plan hatches every building and leaves empty lots as outlines. Built-up = hatched ground (darker than the local paper tone by 0.11 after a 10 m median), "
         "closed across streets (16 m), yards under 0.6 ha filled, groups under 0.5 ha dropped. Only sheets 9-18 were read: 20th St to the Harlem River, 3,432 ha; "
         "south of 20th St the polygon is the 1852 extent (the city there was solid). Central Park is cut out (its planting is drawn as dark as blocks). "
         "North of 59th St this is the first snapshot that reaches Yorkville, Bloomingdale, Manhattanville and Harlem: there the built pieces are villages and house rows, "
         "and rock hachures or stains may be read as built in places. Sheet edges: 25 m inside each neat line, so a strip along a sheet join can be missing.",
    rings={"sheets": {"file": "manhattan_1867_cls.json"}},
)
