# Where people lived before and outside the mapped town, 1600–1700

Research notes for `data/tables/early_nyc.csv` (179 rows, made 2026-11-10). The table covers two things the
map did not draw: the **Lenape settlements and seasonal stations** of the five boroughs as they stood at
contact, and the **Dutch and English colony outside the walled town** from 1624 to 1700 (bouweries,
plantations, villages, mills, churches). The town of New Amsterdam inside the wall is not repeated.

| | rows | buildings (sum of `count`) | high | medium | low |
|---|---|---|---|---|---|
| Lenape | 86 | 624 | 7 | 42 | 37 |
| Dutch / English | 93 | 411 | 6 | 31 | 56 |

| borough | Lenape settlement | Lenape camp | Lenape fort | farm | house / village | church | mill | other |
|---|---|---|---|---|---|---|---|---|
| Manhattan | 7 | 8 | – | 23 | 5 | 1 | 1 | 1 |
| The Bronx | 14 | 10 | 1 | 5 | 4 | – | 1 | 1 |
| Brooklyn | 10 | 3 | – | 4 | 17 | 3 | 1 | 1 |
| Queens | 7 | 3 | – | 3 | 6 | 1 | 1 | – |
| Staten Island | 7 | 16 | – | 2 | 10 | 1 | – | – (+1 Dutch blockhouse, `fort`) |

Buildings standing by year (sum of `count` of the rows alive): 1609 — 622 Lenape, 0 colonial; 1630 — 603 / 10;
1640 — 577 / 40; 1650 — 431 / 168; 1660 — 314 / 277; 1680 — 65 / 332; 1700 — 18 / 333.

**What is real and what is not.** The *sites* come from sources (below). The *house type* comes from
eyewitnesses and excavations. The *number of houses* is from a source in 12 rows (marked "COUNT FROM …" or
"MEASURED …" in `shape_note`) and an estimate everywhere else (marked ESTIMATE). The *position of each single
house inside a cluster* is not known for any row: the pipeline scatters `count` buildings within `spread_m`,
and that scatter is procedural.

---

## 1. Sources

| short | source | licence | used for |
|---|---|---|---|
| Bolton 1922 | R. P. Bolton, *Indian Paths in the Great Metropolis* (Museum of the American Indian, Heye Foundation, Indian Notes and Monographs, 1922). <https://archive.org/details/indianpathsingre00bolt> — full text read: the "Index of stations on the maps" (stations 1–122a) and the Kings and Queens chapters | public domain (US, 1922) | the list of Lenape sites and their locations in today's streets; several colonial facts (Hutchinson's house, Schenck on Mill Island, Gerritsen's mill, Anthony Jansen's plantation, Wessel's mill) |
| Bolton 1920 | R. P. Bolton, *New York City in Indian Possession* (same series, vol. II no. 7, 1920). <https://archive.org/details/newyorkcityinind00bolt> — chapters II, IV, VI, VII and the station index read | public domain | the deeds and dates that end each site (section 4); who lived where |
| Parker 1922 | A. C. Parker, *The Archeological History of New York*, part 2 (New York State Museum Bulletin 237–238, 1922). <https://archive.org/details/archeologicalhis02parkrich> — the site lists of Bronx, Kings, New York, Queens and Richmond counties read (Richmond is Alanson Skinner's list from *The Lenape Indians of Staten Island*, 1909) | public domain | archaeological sites, what was found in them, which had trade goods |
| Danckaerts | *Journal of Jasper Danckaerts, 1679–1680* (ed. James & Jameson, 1913). <https://archive.org/details/journalofjasperd00danc> | public domain | the measured longhouse at Najack; Gowanus, New Utrecht, Breukelen, the Bowery, New Harlem, Sappokanikke, Oude Dorp (seven houses) in 1679 |
| Stokes | I. N. Phelps Stokes, *The Iconography of Manhattan Island*, vol. 2 (1916), "The Manatus Maps". <https://archive.org/details/iconographyofma_02stok> | public domain | the key of the 1639 Manatus map, entry by entry, with the place of each bouwery and plantation in today's streets |
| Wikipedia | articles named in `source_url` (text fetched 2026-11-10 as wikitext) | CC BY-SA 4.0; facts only | town foundings, dated houses, the Achtervelt inventory of 1638, Bronck's inventory of 1643, Land of the Blacks, Konaande Kongh, Nayack, Snakapins |
| city data | building footprints, LPC individual landmarks, parks properties (project files) | NYC Open Data, public | anchors for landmark and park points; the BIN of each standing house |
| Overture roads | project file `data/raw/overture/2026-10-21.0/roads_*.parquet` | ODbL | street intersections (geocoding only) |

Raw texts are under `data/raw/early_nyc/` (gitignored). Suggested `SOURCES.md` ids: `bolton1922`, `bolton1920`,
`parker1922`, `danckaerts1679`, `stokes_manatus`, `wikipedia`.

**Named in the brief and not used:** the LPC archaeological reports (s-media.nyc.gov index), the LPC designation
reports (Ward's Point Conservation Area, Aqueduct), the National Park Service, the Welikia text, the New
Netherland Institute and the New Amsterdam History Center were **not opened** — the tool budget went to the four
books above, which give locations. Grumet is used only as quoted by Wikipedia. Skinner and Finch's papers of 1909
(*The Indians of Greater New York and the Lower Hudson*, <https://archive.org/details/indiansofgreater00wiss>)
were downloaded and not read; Skinner's *Exploration of Aboriginal Sites at Throgs Neck and Clasons Point* (1919)
did not download. These are the first places to go to raise confidence.

---

## 2. Who lived where (Bolton 1920)

- **Manhattan**: the Reckgawawanc (under the sachem Rechewac) held the upper half and the west Bronx; the lower
  end was probably used by Canarsee people of Marechkawick, who later withdrew to Nayack. "The absence of any
  important residential station in the middle part of the island" is Bolton's own remark — the table has none there.
- **The Bronx**: Reckgawawanc west of the Bronx River (Ranachqua, Keskeskick, Nipnichsen, Paparinemin); Siwanoy
  east of it (Snakapins, Castle Hill, Throgs Neck, Pelham Bay).
- **Brooklyn**: Canarsee, with Marechkawick (downtown Brooklyn), Keskaechquerem (Flatlands), Canarsee,
  Shanscomacocke (Gerritsen Creek), Nayack (the Narrows).
- **Queens**: Rockaway from Maspeth to the Rockaways ("In the interior few traces of native life have been
  recorded"; their chief village lay outside the city at Rockville Centre); Matinecock on the north shore
  (Flushing, College Point, Little Neck).
- **Staten Island**: Hackensack in the north-west, Raritan in the south (Ward's Point), Canarsee from Nayack
  after 1652; "Few traces have been found of native occupancy on the eastern side of the island."

`data/tables/population.csv` carries 15,000 Lenape "in approximately 80 settlement sites" around the city at
contact (Burrows & Wallace as cited by Wikipedia). The table has 86 sites; its 622 dwellings of 1609 would house
about 5,000 people at 8 a house. The gap is expected: the 15,000 covers a wider area, the counts here are cautious
estimates, and many camps were seasonal stations of the same people. If the lead wants the houses to carry the
population figure, scale the ESTIMATE counts — not the twelve documented ones.

---

## 3. What Lenape dwellings looked like

| evidence | what it says | source |
|---|---|---|
| Najack (Fort Hamilton), 30 Sept 1679, eyewitness | "seven or eight families, and twenty or twenty-two persons … Their house was low and long, about **sixty feet long and fourteen or fifteen feet wide**. The bottom was earth, the sides and roof were made of reed and the bark of chestnut trees; the posts, or columns, were limbs of trees stuck in the ground, and all fastened together. The top, or ridge of the roof was open about half a foot wide, from one end to the other, in order to let the smoke escape … On the sides … the roof was so low that you could hardly stand under it. The entrances, or doors, which were at both ends, were so small and low that they had to stoop". One fire per family down the middle; mats on either side. | Danckaerts, pp. 55–56 |
| De Vries, 1643 (Long Island south shore) | the chief "and two or three hundred Indians, and about thirty houses" — 7 to 10 people a house | quoted by Bolton 1920 |
| Snakapins (Clason Point), excavated 1918 | "The site was covered by about sixty lodges"; Wikipedia: "more than seventy dwellings" | Bolton 1922 station 8, after Skinner |
| Bowmans Brook (Mariners Harbor), 1903–07 | "from fifty to one hundred pits", bowl-shaped, 4–6 ft deep and wide; a cemetery beside the village | Parker / Skinner |
| Long Neck, Kreischerville (Staten Island) | "scattered lodges" along the shore | Parker / Skinner |
| Forts | Castle Hill: "a palisaded enclosure, or fort, on the high mound"; Fort Neck (Long Island): "two palisaded enclosures of about half an acre" with the village spread around them; Nipnichsen "a palisaded station" | Bolton 1922, 1920 |
| Matinecock, 1650 | "about thirty families", and "great numbers of Indian plantations now lie waste and vacant" | Van Tienhoven, quoted by Bolton 1920 |
| general | wigwams and longhouses are both frames "of arched poles … covered with some sort of bark roofing material … grass, brush, bark, rushes, mats, reeds"; the Lenape built longhouses | Wikipedia, *Wigwam*; *Longhouses of the Indigenous peoples of North America* |

**Sizes used in the table**

| `kind` | footprint | height | basis |
|---|---|---|---|
| `lenape_settlement` | 5 × 5 m (round or oval wigwam) | 2.5 m | ESTIMATE, the middle of the 3–6 m range given in the brief. **No source read gives a measured round house from the five boroughs.** |
| `lenape_camp` | 4 × 4 m | 2.2 m | ESTIMATE (smaller seasonal shelters) |
| `bk_nayack_1679` | 18.3 × 4.4 m (one longhouse) | 3 m | measured by Danckaerts (60 × 14–15 ft); height estimated from "low" |
| `bx_castle_hill_fort` | 45 × 45 m | 3 m | ESTIMATE: half an acre, the size Bolton gives for the Long Island forts; a log palisade, to be drawn as a fence outline |

Van der Donck's "a hundred feet long and twenty wide" for the largest houses is the figure usually quoted; it was
**not** verified in the sources read. Villages certainly mixed long multi-family houses with small round ones; only
Najack has a documented longhouse, so only that row draws one. A reasonable drawing rule for the lead: in a
`lenape_settlement` cluster, draw one house in six as a 12–18 × 4.5 m longhouse (procedural, mark it so).

**Counts.** Documented: Snakapins 60, Najack 1. Estimated by class: a principal village named in the deeds 12–25
(Werpoes, Marechkawick, Keskaechquerem, Canarsee, Shanscomacocke, Keskeskick, Flushing, Ward's Point, Bowmans
Brook, Old Place); a village site 5–10; a station or camp 2–5. Spread: about 6–8 m of radius per house, wider
where the source says "scattered" or "over many acres".

---

## 4. Start and end years of the Lenape rows

`start_year` is 1600 for every site (the map opens in 1609); it is not a founding date. Forty rows are **undated
archaeological sites** — the source names a village site, shell heap or camp but not its period — and say so
("Period of use NOT established … shown as in use at contact — ESTIMATE"). The other 46 are tied to the contact
period by a deed, a Dutch record, or trade goods in the ground (Old Place: brass point, gun flints, trade pipes;
Sandy Ground: iron axes, glass beads; Rossville: brass thimbles; New Springville: an iron arrowhead; Dyckman hill:
glass; Weir Creek: "in use by the Siwanoy after their contact with white men").

| end | rows | event (source) |
|---|---|---|
| 1626 | Werpoes, Shepmoes | the Manhattan purchase; the Company's bouweries laid out (ESTIMATE — no record of when either was left) |
| 1629 | Sapohanikan | the land "was engaged to" Van Twiller "before 7 June, 1629" (Stokes) |
| 1636 | Gowanus, Bennywater | the Gowanus purchase (Wikipedia) |
| 1637 | Rinnegaconck | Indian deed to Joris Rapalje, 16 June 1637 (Stokes) |
| 1639 | Ranachqua | Jonas Bronck's purchase (Bolton) |
| c.1640 | Werpos | Lubbertsen's farm (not verified) |
| 1642 | Mespaetches | the Mespat patent to Francis Doughty |
| 1643 | Rechtauck; Snakapins, Clason Point | the massacre of 25 Feb 1643; Thomas Cornell farming the neck from 1643 (Wikipedia) |
| 1645 | Keskaechquerem, Indian Pond, College Point | the end of Kieft's War; the Gravesend deed ("an old Indian field"); the Flushing patent |
| 1646 | Marechkawick, Winippague, Keskeskick, Riverdale | Breuckelen organised; Bergen Island granted to Underhill; Van der Donck's patent |
| 1652 | Nayack, New Utrecht station | sale of 22 Nov 1652 to Van Werckhoven (Bolton) |
| 1654 | the Siwanoy sites east of Westchester Creek; Bowery Bay | Thomas Pell's purchase; the Riker grant |
| 1656 | Jameco, Little Neck, Douglass Point | Rustdorp founded; Hicks drives the Matinecock from Madnan's Neck (the date 1656 is the usual one and was not verified) |
| 1658 | Conykeekst | Nieuw Haarlem founded |
| 1663–64 | Quinnahung; Woodlawn, Eastchester; Sunwick, Sanford's Point, Flushing | West Farms deed 1663; Eastchester settled 1664; the Sint Sinck tract sold 1664; Tackapousha last named at Flushing 1664 |
| 1669 | Konaande Kongh, Rechewanis, the Inwood and Kingsbridge stations, Nipnichsen | deed of 20 Aug 1669; "probably occupied until" 1669, when the Mohawk drove the Reckgawawanc to the Tappan (Bolton 1920) |
| 1670 | all Staten Island | the last deed, 13 April 1670 |
| 1684–85 | Shanscomacocke, Canarsee; Hook Creek | "to which the natives clung … at least until 1684" (Bolton); the Rockaway sale of 1685 |
| 1690 | the Najack longhouse | "persisted until the late 17th century" (Wikipedia) |
| 1715 | Shorakapkok | the last claims to upper Manhattan settled 1715 — residence probably ended earlier |
| 1782 | Bear Swamp | "they continued to occupy it until 1782" (Bolton) |

These differ from `places.csv` in two labels: Keskachauge ends 1636 there (the deed) and 1645 here (its
sachems still signed in 1638), and Sapohanikan ends 1630 there and 1629 here. The Matinecock band label runs
to 1684; the Flushing village row stops at 1664, its last mention. The rest agree or have no counterpart.

---

## 5. Which sites rest on what

- **Excavated or collected, with a published spot** (Skinner, Harrington, Pepper, Calver, Bolton, Austin, Blackie,
  Secor): all Staten Island rows; in the Bronx Snakapins, Clason Point, Weir Creek, Keskeskick, Anns Hook,
  Laaphawachking, Mishow, Maninketsuck, the shell heaps; in Manhattan every Inwood row, Tubby Hook, Jeffreys Hook,
  Conykeekst; in Brooklyn Shanscomacocke, Canarsee, Winippague, Rinnegaconck (Furman, 1826), Gowanus, Bennywater;
  in Queens Sunwick, Sanford's Point, Bowery Bay, College Point, Little Neck, Douglass Point, Hook Creek, Flushing
  (burials of 1841).
- **Named in deeds and Dutch records, placed by Bolton's reading**: Werpoes, Rechtauck, Sapohanikan, Shepmoes,
  Konaande Kongh, Rechewanis, Ranachqua, Quinnahung, Nipnichsen, Paparinemin, Marechkawick, Werpos,
  Keskaechquerem, Nayack, Mespaetches, Jameco.
- **Bolton's "probable" only**: New Utrecht station, Winippague's exact spot, Nayack's spot, the Eastchester castle.
- **High confidence (7)**: Shorakapkok, Seaman Avenue / Isham Street, Dyckman hill, Snakapins, Keskeskick,
  Shanscomacocke, Ward's Point — an excavated site whose spot is fixed to a street corner or a park.

Left out on purpose: names that are not dwellings (Kapsee, Muscoota as a tract, Ihpetonga, Minnahanonck, Pagganck,
Acqueegenom, Cowangongh, Muskyttehool, Seton Falls, Pudding Rock); burial-only finds (Duryea farm, Crescent
Street, Bayshore Beach, St Raymond's cemetery, Burial Point on Staten Island); sites the sources call very
ancient or cannot place (Arrochar, Stapleton, Harbor Hill golf links, Chelsea, Massabarkem, Narrioch, the
Washington Heights rock shelters, West Farms shell heaps, Woods of Arden).

---

## 6. The colony outside the town

**The Manatus map of 1639** (Library of Congress g3804n.ct000050; key in Wikipedia, commentary in Stokes) is the
census of the farms: 45 numbered entries. In the table: 1 (Great Bouwery), 2–6 (the five other Company bouweries),
7 (Sanders, at Smith's Hill), 10, 11, 14 (the Great Kill house), 15, 17, 18/19 (De Forest's house and the
Otterspoor), 20, 21, 34, 36, 37, 40, 41, 42, 43, 44, 45, E, F and the Noten Island sawmill. Not in the table: 8, 9,
12, 13, 23 (no usable location), 14's lower farm, 16 (the same farm as No. 2), 22 and 26 (inside the town), 24
(Provoost, Park Row to Pearl Street) and 25 (Hendrick the tailor, Pine Street to Maiden Lane) — **both just
outside the later wall and worth adding**, 27–33 (New Jersey), 35 and 38 (Long Island, "practically no records"),
39 (Claes the Norman at Williamsburgh, no spot). Stokes shows that the map's own numbers 2–5 are misplaced; the
positions of those four houses along the Bowery are estimates. **Tracing the Manatus map and Stokes's Land Mark
Map would replace most low-confidence Manhattan positions.**

**Measured buildings.** Achtervelt (Flatlands), inventory of 1638: "one house surrounded by long, round palisades;
the house is 26 feet long, 22 feet wide, 40 feet high with the roof, covered above and all around with boards",
and "a 40 by 18-foot barn". Bronck's farm, inventory of 6 May 1643: "a stone house with a tile roof, a barn, two
barracks for farm employees, and a tobacco house". Najack longhouse (above). Everything else is sized by analogy.

**Sizes used**

| what | footprint | height | basis |
|---|---|---|---|
| farmhouse (`farm`) | 7.9 × 6.7 m | 6 m | the Achtervelt house (26 × 22 ft); its "40 feet high" is quoted but 8 m is used for that row |
| barn (`other`) | 12.2 × 5.5 m | 6 m | the Achtervelt barn (40 × 18 ft) |
| village house (`house`, count > 1) | 8 × 6 m | 5.5 m | ESTIMATE; one storey and garret |
| freed Africans' farms, Company quarter | 6 × 5 m | 4.5 m | ESTIMATE |
| stone houses (New Utrecht 1676, Cortelyou, Lawrence, Bronck) | 9–11 × 7 m | 6–7 m | ESTIMATE |
| churches | 9 × 7 to 19.8 × 8.5 m | 7–10 m | ESTIMATE, except Midwout (65 × 28 ft, the figure usually quoted from Stuyvesant's order — not verified) |
| mills | 9 × 7 m (10 × 8 Gerritsen) | 7–9 m | ESTIMATE |
| Dutch blockhouse | 6 × 6 m | 6 m | ESTIMATE |

**Counts from a source**: Land of the Blacks 30 farms; Gravesend 4 squares × 10 lots; Fordham 16 families; Oude
Dorp 7 houses (1679, three lived in); Bronck's 4 outbuildings; Achtervelt house and barn. All other village counts
(Harlem 25, Flatbush 20, Flushing 18, Breuckelen, Boswijck, Middelburgh, Rustdorp, Oostdorp 15 each, the New
Utrechts and Amersfoort 12, Nieuwe Dorp and the Bowery village 10 …) are estimates.

**End years.** Documented ends: Stuyvesant's house 1778, Kuyter's 1644, Jan van Rotterdam 1643, Kip's house
1851, Land of the Blacks 1716, Old Stone House 1897, Britton Cottage (moved) 1967, Poillon house 1996, New Utrecht
church 1828, Gerritsen's mill 1938, Hutchinson and Throckmorton 1643, Mespat 1643. Where nothing is recorded
(43 rows) the note says "END ESTIMATE …": the row ends when the city's buildings reach the spot — the
second-earliest building within 60 m in `nyc_building_points.parquet`, not later than 1900 (21 rows hit that cap).
That is the same rule the roads and the city ground use; it keeps farms from vanishing in 1700, but a first-generation
timber house did not stand for two centuries — read those rows as "a farmstead stood here".

**Standing buildings (8 rows, `end_year` 9999).** They are not to be drawn; the row dates the city footprint. Each
point lies inside the footprint (`footprint_at.py` returns d = 0.0 m) and the footprint's tax lot equals the LPC
landmark's lot:

| row | start | BIN | city's recorded year | LPC |
|---|---|---|---|---|
| `bk_wyckoff` | 1652 | 3221967 | 1652 | LP-00001 |
| `qn_bowne` | 1661 | 4113403 | 1661 | LP-00143 |
| `qn_friends` | 1694 | 4112345 | 1694 | LP-00141 |
| `qn_riker` | 1656 | 4014161 | 1729 (the additions) | LP-00135 |
| `si_billiou` | 1662 | 5107516 | 1900 (a heap) | LP-00380 |
| `si_conference_house` | 1675 | 5087656 | 1680 | LP-00393 |
| `si_manee` | 1690 | 5082720 | 1825 | LP-01398 |
| `si_austen` | 1690 | 5042188 | 1690 | LP-00371 |

The Alice Austen House year dates the oldest part of the present house ("originally built in the 1690s/early 1700s
as a one-room Dutch Colonial House", enlarged in the 1800s), not an earlier house; the year is soft (the land was
bought in 1698). Three more old houses are **not** standing originals and have end years: the Old Stone House
(destroyed 1897; the building in the park is a reconstruction of 1933), the Britton Cottage (moved to Richmondtown
in 1967) and the Poillon house (demolished 1996). The Voorlezer's House is left out: Wikipedia now dates it to the
1760s. Lott (1720), Lefferts (1783), Kingsland (1785) and the Treasure House (c.1700) fall outside or on the edge
of the period and are left to the building dates table.

---

## 7. How the CSV was built

- Rows are written by hand in `data/interim/early_nyc/rows_lenape.py` and `rows_colonial.py`; `build.py` beside
  them places them and writes the CSV (scratch folder, gitignored — copy it if it should be kept).
- **Position**: a street intersection from the Overture roads where the source names two streets (89 rows; for 7
  of them the two streets no longer meet and the point is a coordinate from memory: Werpoes, Rechewanis,
  Conykeekst, Dyckman hill, the Century House site, Bouwerie No. 6, the Snyder plantation), an LPC landmark or a park
  property (23 rows), or a stated coordinate (the rest). Every `shape_note` says how good the position is.
- **1609 layer**: each point is tested against `natural_1609.geojson` and today's water. 29 points fell in water,
  tidal marsh, flats, a pond or a wetland and were moved to the nearest dry ground, in 20 m rings; the note gives
  the distance. Six moved 100 m or more: `si_old_place` 340, `si_princes_bay` 320, `bx_burial_point` 200,
  `bx_anns_hook` 120, `mn_dominies_bouwerie` 120, `si_silver_lake` 100 — these were weak positions to begin with.
- **Footprints**: the number of city footprints within 150 m of every point was listed (the same file
  `footprint_at.py` reads); `footprint_at.py` itself was run on the eight standing rows.
- **`rotation_deg`** (compass bearing of the long side, 0 = north–south): for a single building, the bearing of
  the nearest present-day road — an ESTIMATE with no historical basis in Manhattan, where the roads of 1640 are
  gone; for standing buildings, the long side of the city footprint; 0 for clusters.
- **`end_year`** is exclusive, as in the viewer. `storeys` is whole numbers (1 = one storey and garret).
- **`material`**: a log palisade and a log blockhouse are `wood frame` (the list has no better word); the Lenape
  fort row says "draw as a fence outline".

---

## 8. Weak spots and what was not checked

1. **Nothing was looked at on a map image.** Positions "from memory" (13 rows say so): Hunts Point's old tip, the
   mouth of Weir Creek, the Bear Swamp crossing, Roosevelts Brook, Bowmans Brook, Old Place Neck, Lake's Island,
   Ketchum's pond, the Split Rock, the Rutgers mansion block, Het Dorp of Bushwick, the Schenck house, and that
   the Indian Pond lay at Seth Low Playground and Ravenswood Park is Rainey Park. Bolton's own maps (plates in the
   1922 volume) and the 1890s USGS sheets would settle most of them.
2. **Statements marked "not verified"** in the notes (13 rows): the end of Stuyvesant's chapel; the Peach War end
   of De Forest's house; the Midwout church size; the dates of the Breuckelen church; the octagonal plan of the
   New Utrecht church; the Schenck house dates; the Van Cortlandt mill's end; De Vries's 1641; Werpos c.1640; the
   1656 date at Little Neck; whether the Eastchester "castle" lies inside the city line.
3. **Queens is thin** (10 Lenape rows) because the sources are: Bolton says exploration there was still to be
   done. The Rockaway peninsula, Jamaica Bay's north shore (Aqueduct, Old Fort Pond) and Bayside have nothing
   usable in the books read; the LPC reports should.
4. **Colonial villages are clusters of estimated size** placed at the label point of `places.csv`. Flatbush,
   Jamaica and Harlem were street villages; a round scatter has the wrong shape. Village churches other than those
   listed, the mills of Gowanus, West Farms, Harlem and Alley Creek, the Poor Bouwery, Dongan's manor house, Stony
   Brook, the Lakeman house and the West Farms and Eastchester farms are **not in the table** — no source read
   gave a usable fact for them.
5. **Staten Island's first three colonies** (De Vries 1639, Melyn 1641 and 1650) are in the table because they
   existed, but no source read says where they stood; their points are good to 2–3 km and their counts are guesses.
6. **Overlaps the pipeline must handle**: (a) Lenape and colonial rows share ground in successive years
   (Keskaechquerem → Amersfoort, Marechkawick → Breuckelen, Flushing village beside Vlissingen 1645–64); (b) the
   colonial clusters run to as late as 1900 and will meet today's footprints and the generated pre-atlas town —
   documented > traced > generated applies, and the scatter should skip any spot that already has a building in
   the same year; (c) `mn_land_of_the_blacks` (spread 450 m) covers the Minetta marsh — keep the scatter on dry cells.
