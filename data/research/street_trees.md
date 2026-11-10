# Street and park trees — sources, rules, counts, checks

Stage: `pipeline/street_trees.py` (one stage, both outputs). Built 2026-11-10 from downloads of the same day.
Numbers below are from that build (`data/interim/street_trees/report.json`, `check.json`); the
inventory changes every two weeks, so a later download gives slightly different counts.

## What is drawn

**884,188 living trees** of NYC Parks' inventory, each where the inventory puts it
(positions stored to 5e-6 degrees: 0.42 m east-west, 0.56 m north-south).

| borough | trees | of them park | recorded | after-2015 bracket | diameter (species eq.) | diameter (other eq.) | output |
|---|---|---|---|---|---|---|---|
| Manhattan | 97,143 | 29,765 | 11,417 | 4,240 | 57,545 | 23,941 | street-trees.bin.gz |
| Bronx | 135,662 | 40,016 | 22,297 | 4,743 | 69,082 | 39,540 | region-trees/ tiles |
| Brooklyn | 233,776 | 40,766 | 36,132 | 8,194 | 135,160 | 54,290 | region-trees/ tiles |
| Queens | 293,223 | 46,498 | 36,850 | 10,661 | 180,040 | 65,672 | region-trees/ tiles |
| Staten Island | 124,384 | 15,711 | 9,871 | 5,850 | 80,364 | 28,299 | region-trees/ tiles |
| **all** | **884,188** | 172,756 | 116,567 | 33,688 | 522,191 | 211,742 | |

`site` of the planting space: Street 709,128, Park 172,756, unknown 2,304.
Forms: 856,836 broadleaf, 27,352 conifer, 0 palm.

Left out: 11,767 dead trees with structure "Full"; stumps, shafts and retired points (not
downloaded: 227,394 of the 1,125,266 tree points); 578 points outside the five boroughs (bad
coordinates); 720 second records on one stored position (the thicker trunk stays); 619 trees with
neither a planting date nor a usable trunk diameter (nothing dates them). **Nothing was thinned.**

## Sources

| id | what | where | licence / terms | used for |
|---|---|---|---|---|
| `forms_tree_points` | Forestry Tree Points (ForMS 2.0, NYC Parks' working inventory, refreshed every two weeks; rows updated 4 Nov 2026, newest record 3 Nov 2026): 1,125,266 tree points, 897,872 with structure "Full" downloaded. Fields: `objectid`, `dbh` (in), `tpstructure`, `tpcondition`, `genusspecies`, `createddate`, `updateddate`, `planteddate`, `geometry`, `plantingspaceglobalid` | NYC Department of Parks & Recreation, NYC Open Data `hn5i-inap` — https://data.cityofnewyork.us/d/hn5i-inap | NYC Open Data terms of use (the wording of SOURCES.md: public, no restriction on reuse). The Socrata record of the table names no licence | the base: position, species, trunk, planting date |
| `forms_planting_spaces` | Forestry Planting Spaces: 1,130,942 spaces; `globalid`, `pssite` (Street 914,806 / Park 214,126), `psstatus`, `jurisdiction` | NYC Parks, NYC Open Data `82zj-84is` — https://data.cityofnewyork.us/d/82zj-84is | as above | street / park per tree (join `plantingspaceglobalid` = `globalid`) |
| `census_2015` | TreesCount! 2015 Street Tree Census: 683,788 records (652,173 alive, 17,654 stumps, 13,961 dead), surveyed 19 May 2015 - 5 Oct 2016, each tree at its own position; `tree_dbh` (in), `status`, `created_at`, `latitude`, `longitude` | NYC Parks, NYC Open Data `uvpi-gqnh` — https://data.cityofnewyork.us/d/uvpi-gqnh | as above | the trunk as measured in 2015; what stood on a spot in 2015 |
| `census_2005` | 2005 Street Tree Census: 592,372 records | NYC Parks, NYC Open Data `29bw-z7pj` — https://data.cityofnewyork.us/d/29bw-z7pj | as above | examined, **not used** (see below) |
| `census_1995` | 1995 Street Tree Census: 516,989 records | NYC Parks, NYC Open Data `kyad-zm4j` — https://data.cityofnewyork.us/d/kyad-zm4j | as above | examined, **not used** |
| `usfs_utd` | Urban Tree Database: growth equations of street and park trees in 17 US reference cities (Northeast: Queens, New York, measured 2005), table `TS6_Growth_coefficients.csv`, equation forms `TS4` | McPherson, E. Gregory; van Doorn, Natalie S.; Peper, Paula J. 2016. *Urban tree database*. Fort Collins, CO: Forest Service Research Data Archive. Updated 21 January 2020. https://doi.org/10.2737/RDS-2016-0005 ; methods: McPherson, van Doorn & Peper 2016, *Urban tree database and allometric equations*, Gen. Tech. Rep. PSW-GTR-253, https://www.fs.usda.gov/treesearch/pubs/52933 | US Government work; the archive's metadata: "can be used without additional permissions or fees", cite as given | age, height and crown from the trunk diameter |

Downloads: `python street_trees.py download` -> `data/raw/street_trees/<id>/page-NNN.csv` (the columns
the stage reads, as published, 100,000 rows a page, with a `source.json`: dataset, query, rows, date).
Not verified: the text of the NYC Open Data terms of use could not be read in this session (the
page is rendered by script); ForMS's user guide and data dictionary (linked from the dataset pages)
were not read — field meanings are taken from the dataset descriptions and from the data itself.

## Why the living inventory is the base, not the 2015 census

- ForMS **is** the 2015 census, kept up: 91 % of the street-tree records made during the census
  period stand within 0.5 m of a 2015 census record (95 % within 3 m).
- It is current (to 3 Nov 2026): 16 % of the trees the census found alive have no living ForMS tree within
  3 m any more (removed), and ForMS has what was planted since, with **122,241 planting dates**
  (2015-2026).
- It has the trees of the landscaped parks (172,756), which no street census counted.
- Trees the census counted and that are gone today cannot be drawn: the viewer's tree format has no
  end year (`decodeTrees` writes 9999). See "Not done".

## Dates

| evidence (`source` column) | trees | share | `confidence` |
|---|---|---|---|
| 0 recorded planting date (ForMS) | 116,567 | 13.2 % | exact (0) |
| 1 planted after the 2015 census (census + ForMS record) | 33,688 | 3.8 % | estimated (1) |
| 2 trunk diameter, species equation (Urban Tree Database, NoEast) | 522,191 | 59.1 % | estimated (1) |
| 3 trunk diameter, genus / neighbouring-region / pooled equation | 211,742 | 23.9 % | estimated (1) |

Order of evidence, per tree:

0. **Recorded planting date** (`planteddate`). Used when it lies between 1900 and the inventory date,
   is not a bulk date and is not contradicted by the trunk. Checks made: the busiest day holds about 540
   trees (15 May 2023), all young (median trunk 2 in, 95th percentile 3 in) — planting days, not
   data-entry stamps; no year stands out against the years around it (rule: 5 times their median);
   0 dates rejected as bulk. 5,674 dates rejected because the trunk is far too thick for the
   date (the trunk-age is more than max(8 years, half the tree's recorded life) older than the date):
   those are records of old trees that carry the date of something else. Stored to a tenth of a year.
   Garbage years in the table (0202, 1207, 2030, 2108) fall outside the range.
1. **Planted after the 2015 census** (census bracketing, estimated). A street tree whose ForMS record
   was made after the census was loaded (2 Nov 2016), whose trunk is a young tree's (trunk-age no
   more than the time since mid-2015 plus 4 years), and where the census — which recorded every tree at
   its own position — counted no tree within 3 m, or a dead tree / stump, or a tree at least 3 in
   thicker than this one is now (its predecessor). The tree was planted between the day the census
   passed (the date of its nearest census record within 100 m, else 2016.0) and the day its record was
   made. Inside that bracket: a trunk still at planting size (<= 3.5 in; ForMS records a newly
   planted tree at 3 in, the median of every year's dated plantings) -> the day the record was made
   (records that have both dates were made a median 9 days after the planting; not applied to
   records made in bulk loads, i.e. creation stamps shared by 500 records or more); else the trunk-age,
   clipped into the bracket. The same holds for 2,324 census-period records whose ForMS trunk is
   now much thinner than the census counted (60 % of it or less, and at least 3 in less): the tree
   was replaced; its bracket ends at the record's last update.
2. **Trunk diameter, species equation** and 3. **trunk diameter, other equation** (estimated): see
   "Growth equations". The trunk used is the one the 2015 census measured when the ForMS record is
   that census tree (same spot within 1.5 m, record of the census period, 494,596 trees), dated at the
   census record's date; otherwise ForMS's `dbh`, dated at the record's last update (else its
   creation). A whole-inch reading stands for anything within half an inch of it: each tree takes a
   stable point inside (hash of its object id), so one species' trees of one reading are not all
   planted in the same year. Stored as whole years.

Bounds, applied after the estimate:

- **The street** (diameter-dated trees only): not more than 3 years before the 2nd-earliest building
  within 45 m (the only one if there is one; standing or vanished, `data/interim/nyc_building_points.parquet`,
  eight nearest) — the rule that dates the streets in `roads.py`. 26,561 trees were moved later by it.
  Recorded dates and the census bracket are records and are not moved.
- **Remnants**: trunks of 75 cm or more are exempt from the street bound when the species grew here
  before the town (oaks, tulip tree, beech, hickories, sweetgum, black gum, American sycamore, red /
  sugar / silver maple, American elm, ashes, basswood, black cherry, sassafras, black walnut, birches,
  white / pitch pine, hemlock, cottonwood, hackberry, chestnut, black willow, persimmon, red cedar:
  `NATIVE` in the stage) or when the tree stands in a park: 25,513 trees (15,844 in parks), ages capped at 250
  years (others at 150). **Deviation from the brief**, which exempts every trunk over 75 cm: a London
  plane or Norway maple is always planted, never a remnant, so thick trunks of planted species stay
  bound to their street — this moved 2,222 trees. `REMNANT_ANY_SPECIES = True` in the stage gives
  the wider reading.
- **The ground**: no tree before the land under it (`data/interim/grid_detail_landyear.npy`, the cell of
  the stored position, + 1 year). 88,895 trees stand on made land; 1,634 were moved later (2 of them
  recorded dates, then marked estimated).
- Never after the measurement / record date. Plantings of 2026 are stored at 2025.95 (the slider ends
  at 2026), as the Bay stage did.

### Why the 1995 and 2005 censuses do not bracket anything

The brief asked for "in the 2015 census but not within ~3 m in the 2005 census, small trunk ->
planted between them". The data does not support it: both older censuses recorded trees **by
address** and the published coordinates are the geocoded address, not the tree.

- 2005: 592,372 records stand on 268,077 distinct points (8,840 have no position); 1995: 516,989
  records on 260,972 points (32,387 without position). 2015: 683,788 records on 683,352 points.
- Test on trees that were certainly there: the 112,063 trees alive in 2015 with a trunk of 20-60 in.
  A 2005 record lies within 3 m of 0.3 % of them, within 10 m of 39 %, within 30 m of 75 %
  (1995: 1.1 % / 40 % / 73 %). "No 2005 tree within 3 m" is true of 99.7 % of trees that were there.
- Test by tax lot (`bbl`, in all three tables): of the 61,880 lots whose 2015 trees all measure 20 in
  or more, 24 % have no 2005 tree at all (and 62 % no 1995 tree — only half of the 1995 records carry a
  lot). Lots with only young trees (all <= 4 in, 60,880 lots): 74 % have no 2005 tree. So absence
  from the 2005 census is wrong one time in four for a tree that was certainly standing; as evidence
  about a single tree it adds little to what the trunk already says.

They are therefore downloaded (for a later, coarser use: block-level counts) and not used. The one
bracket that is real is census 2015 -> ForMS, where both sides record the tree's own position.

## Growth equations (Urban Tree Database, Northeast region "NoEast", reference city Queens NY)

Age (years after planting), tree height (m) and crown diameter (m) as functions of the trunk
diameter at breast height `x` in cm. Forms (database table TS4): `lin` a + b x; `quad` + c x^2;
`cub` + d x^3; `loglogw1` exp(a + b ln(ln(x + 1)) + sigma^2 / 2); `expow1` exp(a + b x + sigma^2 / 2)
(w2-w4 multiply the sigma^2 / 2 term by sqrt(x), x, x^2). Each equation is used inside the trunk range
its species was fitted on and clamped to its published range of results ("Apps min / max").

Which equation a tree gets (species: 580,779, genus: 134,089, pooled: 117,528, species:LoMidW: 29,454, species:Piedmt: 11,528, genus:Piedmt: 7,925, genus:LoMidW: 2,885):

1. the species' own equation in Queens (21 species; trees: platanus acerifolia 99,633, gleditsia triacanthos 77,258, quercus palustris 66,191, pyrus calleryana 51,497, zelkova serrata 40,319, prunus serrulata 30,643, tilia cordata 28,810, acer platanoides 28,247, acer rubrum 24,730, ginkgo biloba 24,325, liquidambar styraciflua 19,077, quercus rubra 15,690, ulmus americana 15,511, fraxinus pennsylvanica 15,201, tilia tomentosa 11,415, malus 9,354, acer saccharinum 9,341, quercus phellos 5,932, pinus strobus 3,853, acer saccharum 2,373, aesculus hippocastanum 1,379);
2. else the median of its genus' equations in Queens (Acer, Quercus, Tilia, Prunus, Ulmus, Fraxinus, Pinus ...);
3. else the species' equation in a humid eastern / midwestern reference city: Indianapolis (`LoMidW`),
   Charlotte (`Piedmt`), Minneapolis (`MidWst`), in that order; then its genus there;
4. else the pooled curve: the median of the 21 Queens species.
The western, desert and tropical regions of the database are not used.

Beyond the trunk range of its fit a species' age keeps growing at the pooled rate — the median
years-per-cm of the Queens species whose equations reach that trunk (at least three; years per cm at
25 / 50 / 75 / 100 / 125 / 150 cm: 1.03 / 0.83 / 0.86 / 0.59 / 0.71 / 0.71). The Bay stage's rule (the species' own end slope) was dropped:
exponential fits run away (a 117 cm silver linden came out 250 years old). Heights and crowns stay
at their maximum beyond the range.

Trunk ranges of the fits:

| species | trunk range of the fit (cm) |
|---|---|
| Acer platanoides | 5.6-114.7 |
| Acer rubrum | 2.6-105.2 |
| Acer saccharinum | 2.2-58.5 |
| Acer saccharum | 2.2-105.5 |
| Aesculus hippocastanum | 3.4-90.0 |
| Fraxinus pennsylvanica | 2.4-123.5 |
| Ginkgo biloba | 1.9-82.6 |
| Gleditsia triacanthos | 3.2-71.9 |
| Liquidambar styraciflua | 3.4-80.1 |
| Malus spp. | 2.9-46.1 |
| Pinus strobus | 3.0-96.1 |
| Platanus x acerifolia | 2.4-61.8 |
| Prunus serrulata | 3.6-92.5 |
| Pyrus calleryana | 4.1-54.9 |
| Quercus palustris | 2.9-127.6 |
| Quercus phellos | 4.2-121.0 |
| Quercus rubra | 2.9-139.6 |
| Tilia cordata | 2.7-131.1 |
| Tilia tomentosa | 3.0-45.3 |
| Ulmus americana | 5.3-133.0 |
| Zelkova serrata | 2.2-81.6 |

Age from trunk (years):

| species | form | a | b | c | d | sigma | years range |
|---|---|---|---|---|---|---|---|
| Acer platanoides | cub | 2.7544 | 0.28615 | 0.01875 | -0.00013 |  | 0-119 |
| Acer rubrum | cub | 0.93244 | 0.02113 | 0.05658 | -0.00055 |  | 0-119 |
| Acer saccharinum | cub | 1.655 | 0.22698 | 0.05987 | -0.0008 |  | 1-150 |
| Acer saccharum | loglogw1 | -0.54715 | 3.2265 |  |  | 0.2657 | 0-121 |
| Aesculus hippocastanum | quad | -1.3217 | 1.3828 | -0.00555 |  |  | 0-80 |
| Fraxinus pennsylvanica | quad | 0.15398 | 0.50207 | 0.01235 |  |  | 0-107 |
| Ginkgo biloba | quad | 2.0063 | 0.94391 | 8e-05 |  |  | 0-104 |
| Gleditsia triacanthos | lin | -2.0848 | 0.69231 |  |  |  | 1-150 |
| Liquidambar styraciflua | lin | -2.2088 | 1.3256 |  |  |  | 0-150 |
| Malus spp. | lin | -0.77187 | 1.1447 |  |  |  | 0-58 |
| Pinus strobus | quad | 0.51428 | 0.55776 | 0.0201 |  |  | 1-131 |
| Platanus x acerifolia | cub | 0.58171 | 0.30204 | 0.03224 | -0.00037 |  | 0-92 |
| Prunus serrulata | lin | -1.6058 | 0.62144 |  |  |  | 0-58 |
| Pyrus calleryana | lin | -1.0614 | 0.61303 |  |  |  | 0-40 |
| Quercus palustris | lin | 1.7665 | 0.68508 |  |  |  | 0-96 |
| Quercus phellos | cub | -0.46592 | 0.39042 | 0.01441 | -0.0001 |  | 0-102 |
| Quercus rubra | lin | 0.01607 | 1.0168 |  |  |  | 0-150 |
| Tilia cordata | cub | -0.31291 | 0.44918 | 0.0172 | -0.00011 |  | 0-143 |
| Tilia tomentosa | expow1 | 1.2918 | 0.06238 |  |  | 0.68442 | 1-150 |
| Ulmus americana | lin | -1.2487 | 0.70723 |  |  |  | 0-97 |
| Zelkova serrata | cub | -1.109 | 1.1192 | -0.0227 | 0.00025 |  | 0-60 |

Height from trunk (m):

| species | form | a | b | c | d | sigma | m range |
|---|---|---|---|---|---|---|---|
| Acer platanoides | lin | 3.1683 | 0.19507 |  |  |  | 4.26-25.54 |
| Acer rubrum | quad | 3.217 | 0.24941 | -0.00065 |  |  | 3.87-22.24 |
| Acer saccharinum | loglogw2 | 0.42084 | 1.6891 |  |  | 0.06943 | 2.01-16.72 |
| Acer saccharum | lin | 3.1413 | 0.23463 |  |  |  | 3.65-27.9 |
| Aesculus hippocastanum | quad | 1.366 | 0.31715 | -0.00145 |  |  | 2.41-18.15 |
| Fraxinus pennsylvanica | loglogw1 | -0.00104 | 2.0008 |  |  | 0.20436 | 1.56-23.48 |
| Ginkgo biloba | quad | 1.5039 | 0.44055 | -0.00251 |  |  | 2.34-20.74 |
| Gleditsia triacanthos | quad | 2.7257 | 0.40207 | -0.00231 |  |  | 4-19.7 |
| Liquidambar styraciflua | cub | 1.2271 | 0.4387 | -0.00425 | 2e-05 |  | 2.68-20.52 |
| Malus spp. | expow1 | 1.0323 | 0.02559 |  |  | 0.27694 | 3.14-9.48 |
| Pinus strobus | loglogw1 | -0.28182 | 2.2593 |  |  | 0.22345 | 1.63-23.72 |
| Platanus x acerifolia | quad | 3.2952 | 0.30021 | -0.00109 |  |  | 4.01-17.69 |
| Prunus serrulata | loglogw2 | 0.20839 | 1.3442 |  |  | 0.09405 | 2.19-9.82 |
| Pyrus calleryana | loglogw1 | 0.39228 | 1.559 |  |  | 0.15221 | 3.22-13.03 |
| Quercus palustris | lin | 2.9795 | 0.24435 |  |  |  | 3.68-34.17 |
| Quercus phellos | loglogw1 | 0.20016 | 1.8524 |  |  | 0.13634 | 3.09-22.45 |
| Quercus rubra | quad | 2.9826 | 0.30808 | -0.00105 |  |  | 3.87-25.59 |
| Tilia cordata | quad | 2.9153 | 0.27146 | -0.00098 |  |  | 3.64-21.74 |
| Tilia tomentosa | loglogw1 | 0.2228 | 1.6943 |  |  | 0.1065 | 2.2-12.22 |
| Ulmus americana | quad | 2.7235 | 0.31773 | -0.00119 |  |  | 4.37-23.9 |
| Zelkova serrata | loglogw1 | 0.01056 | 1.9345 |  |  | 0.19026 | 1.38-18.01 |

Crown diameter from trunk (m):

| species | form | a | b | c | d | sigma | m range |
|---|---|---|---|---|---|---|---|
| Acer platanoides | quad | 1.0578 | 0.25365 | -0.00083 |  |  | 2.46-19.19 |
| Acer rubrum | quad | 0.20703 | 0.32103 | -0.00152 |  |  | 1.04-17.15 |
| Acer saccharinum | cub | 0.73372 | 0.3504 | -0.00296 | 1e-05 |  | 1.51-13.41 |
| Acer saccharum | quad | 0.79563 | 0.28114 | -0.0013 |  |  | 1.4-15.95 |
| Aesculus hippocastanum | cub | 0.16411 | 0.36854 | -0.00599 | 4e-05 |  | 1.33-16.29 |
| Fraxinus pennsylvanica | cub | -0.55792 | 0.48266 | -0.00527 | 2e-05 |  | 0.58-23.38 |
| Ginkgo biloba | quad | 0.56506 | 0.23562 | -0.00074 |  |  | 1.01-15 |
| Gleditsia triacanthos | loglogw1 | -0.48922 | 2.3254 |  |  | 0.12384 | 1.46-18.19 |
| Liquidambar styraciflua | quad | 0.20226 | 0.2869 | -0.0009 |  |  | 1.17-17.39 |
| Malus spp. | quad | 0.44624 | 0.33986 | -0.00342 |  |  | 1.39-8.84 |
| Pinus strobus | quad | 0.26428 | 0.28611 | -0.00132 |  |  | 1.11-15.57 |
| Platanus x acerifolia | loglogw1 | -0.75195 | 2.4142 |  |  | 0.14059 | 0.78-14.63 |
| Prunus serrulata | cub | 1.5732 | 0.29639 | -0.00543 | 4e-05 |  | 2.57-17.14 |
| Pyrus calleryana | lin | 0.41182 | 0.28531 |  |  |  | 1.59-16.08 |
| Quercus palustris | cub | 0.58861 | 0.37575 | -0.00351 | 2e-05 |  | 1.63-28.44 |
| Quercus phellos | quad | 0.87983 | 0.27243 | -0.00077 |  |  | 2-22.61 |
| Quercus rubra | quad | 1.1373 | 0.27575 | -0.00076 |  |  | 1.93-24.89 |
| Tilia cordata | cub | -1.1498 | 0.44387 | -0.00442 | 2e-05 |  | 0.61-18.82 |
| Tilia tomentosa | loglogw2 | -1.1445 | 2.5911 |  |  | 0.09648 | 0.75-10.7 |
| Ulmus americana | cub | 2.3857 | 0.12102 | 0.0024 | -2e-05 |  | 3.09-24.36 |
| Zelkova serrata | loglogw1 | -0.6785 | 2.399 |  |  | 0.07648 | 0.72-17.91 |

Largest groups without a species equation in Queens:

| species (as keyed) | trees | equation used |
|---|---|---|
| styphnolobium japonicum | 20,463 | pooled |
| tilia americana | 16,948 | genus |
| quercus bicolor | 14,962 | genus |
| celtis occidentalis | 9,564 | species:LoMidW |
| cercis canadensis | 9,372 | species:LoMidW |
| gymnocladus dioicus | 9,229 | pooled |
| prunus | 8,299 | genus |
| syringa reticulata | 7,611 | pooled |
| morus | 7,594 | species:LoMidW |
| carpinus betulus | 6,608 | pooled |
| koelreuteria paniculata | 6,157 | pooled |
| prunus cerasifera | 6,055 | genus |
| prunus serotina | 5,919 | genus |
| robinia pseudoacacia | 5,610 | pooled |
| crataegus | 5,472 | pooled |
| metasequoia glyptostroboides | 5,261 | pooled |
| ulmus parvifolia | 4,679 | genus |
| acer | 4,587 | genus |
| maackia amurensis | 4,282 | pooled |
| quercus acutissima | 4,024 | genus |
| juniperus virginiana | 3,713 | species:Piedmt |
| ulmus pumila | 3,700 | genus |

## Size and form

Height and crown radius from today's trunk (ForMS `dbh`; the census trunk if ForMS has none) with the equations above, clamped to the Bay's ranges (height 3-24 m, crown radius 1-7 m) and
stored in steps of 0.5 m and 0.25 m. Form: conifer if the genus is one (abies, araucaria, calocedrus, cedrus, chamaecyparis, cryptomeria, cunninghamia, cupressocyparis, cupressus, cuprocyparis, juniperus, larix ...;
dawn redwood, bald cypress and larch included), else broadleaf; ginkgo is drawn as a broadleaf. No
palms: the Bay's name patterns would have turned *Acer palmatum* into palms and *Carpinus* into
conifers ("pinus"), so they are not used.

## Outputs and size

| file | trees | bytes |
|---|---|---|
| `viewer/public/data/street-trees.bin.gz` (Manhattan, always loaded; `loadTrees`) | 97,143 | 623,051 |
| `viewer/public/data/region-trees/index.json` + `12/<x>/<y>.bin.gz` (28 tiles; Bronx, Brooklyn, Queens, Staten Island) | 787,045 | 5,099,222 |
| both | 884,188 | 5,722,273 (5.72 MB; budget 9 MB) |

Format: BAYT columnar, the columns of the Bay's `sf-trees.bin.gz` / `region-trees` tiles —
`position_q` (int32 pairs, byte-shuffled, relative to the viewer's `DECO_ORIGIN` (-73.97, 40.72) in
units of `meta.position_scale` = 5e-6 degrees), `start_year` (float32), `height`, `crown` (float32, m),
`form` (0 broadleaf, 1 conifer, 2 palm), `confidence` (0 exact, 1 estimated), `source` (index into
`sources`: the evidence classes above), `park` (1 = park tree). `index.json`: `z`, `origin`,
`position_scale`, `forms`, `sources`, `attribution`, `tiles` [x, y, n, bytes]. Quantisation used to fit
the budget: positions 0.5 m, estimated years whole, sizes in steps; trees written west to east. No
tree was dropped for size.

Interim: `data/interim/street_trees/trees.parquet` (one row per tree: object id, species, trunks,
dates, evidence, bounds, street and land year), `grid_detail_streettrees.npy` (inventory trees per
29 m terrain cell, uint8, shape of `grid_detail_*.npy`), `report.json`, `check.json`.

## Checks on the built files (`python street_trees.py check`, run at the end of every build)

Read back from the files the viewer loads (29 files, 884,188 trees):

- per borough (TIGER county outlines): Manhattan 97,143, Bronx 135,662, Brooklyn 233,776, Queens 293,223, Staten Island 124,384; outside the boroughs: 0;
  Manhattan trees in the tiles / other boroughs' trees in the Manhattan file: [0, 0]
- years outside 1609-2026: 0; start >= end: 0 (the format has no end year)
- trees before their ground: 0 (of 88,895 on made land)
- heights outside 3-24 m / crowns outside 1-7 m: [0, 0]; doubles on one stored position: 0
- every tile's `n` equals its file's count, every tile shares the index origin; every tile centre
  passes the viewer's extent test (`extentDistance >= -8 km`; the farthest is 2.7 km outside the line)
- spikes (a year with 2,000 trees or more and over 2.5 times the median of the five years on either
  side): none
- trees per year since 2000: 2000: 15,833, 2001: 16,478, 2002: 17,798, 2003: 19,190, 2004: 20,744, 2005: 22,355, 2006: 24,584, 2007: 27,484, 2008: 28,391, 2009: 29,655, 2010: 30,324, 2011: 25,735, 2012: 20,286, 2013: 15,428, 2014: 9,938, 2015: 15,912, 2016: 12,520, 2017: 14,526, 2018: 10,036, 2019: 10,346, 2020: 10,920, 2021: 11,274, 2022: 14,849, 2023: 18,615, 2024: 20,871, 2025: 21,509, 2026: 12,375

Planting decades:

| decade | trees |
|---|---|
| 1830s | 1 |
| 1850s | 5 |
| 1860s | 22 |
| 1870s | 51 |
| 1880s | 194 |
| 1890s | 341 |
| 1900s | 865 |
| 1910s | 1,965 |
| 1920s | 4,156 |
| 1930s | 11,202 |
| 1940s | 22,054 |
| 1950s | 33,842 |
| 1960s | 59,333 |
| 1970s | 55,414 |
| 1980s | 75,013 |
| 1990s | 121,754 |
| 2000s | 222,512 |
| 2010s | 165,051 |
| 2020s | 110,413 |

The rise to 2010 and the fall after it is what diameter dating of the 2015 census gives (most
trees were measured in 2015-16); the MillionTreesNYC planting campaign falls in those years
(2007-2015 per https://en.wikipedia.org/wiki/MillionTreesNYC — from memory, not re-read here). Recorded dates
start in 2015 and are thin until 2019 (2015: 1,852; 2016: 4,801; 2017: 7,813; 2018: 4,622; 2019: 5,929; 2020: 8,030; 2021: 8,299; 2022: 12,321; 2023: 16,082; 2024: 17,737; 2025: 18,943; 2026: 10,133) — the bracket class fills part of that gap.

## The terrain's canopy trees and the inventory

Measured on the built z14 terrain tiles: of 2,315,082 present-day terrain trees (WorldCover canopy
pixels), 96,330 (4 %) stand within 10 m of an inventory tree and 139,334 within 15 m; 16 % of the
inventory trees have a terrain tree within 10 m (10 % of the street trees, 41 % of the park trees).
The two sets are mostly complementary (the canopy trees are woods, yards and park interiors); the
doubles are along tree-lined streets and in landscaped parks. `street_trees.inventory_mask(transform,
shape, reach=1)` returns the canopy cells the real trees already stand for (cells of the terrain's
7 m canopy grid holding an inventory tree: 813,965; with their eight neighbours: 3,919,092; 3 s).

## Not done, weak spots

- **83 % of the trees are dated from the trunk alone.** The equations give the typical age of a
  trunk; single trees are off by ten to twenty years either way, more for big trunks beyond the fitted
  ranges. Census trunks were measured by volunteers.
- A ForMS trunk is dated at the record's last update; if the update did not re-measure the trunk the
  tree comes out too young by up to the years since the census (of the census trees still in ForMS,
  28 % carry the census trunk unchanged, 61 % a thicker one, 10 % a thinner one).
- Typing errors and multi-stem sums in `dbh` (a crabapple of 74 in) are dated as given, up to the cap.
- **Removed trees are not drawn**: the format has no end year. ForMS holds 177,028 retired points and
  the 2015 census about 107,000 live trees that are gone; with an end year in `decodeTrees` they could
  stand until their removal. Trees of the 1995 / 2005 censuses have no usable position.
- Park trees are the ones ForMS inventories (landscaped parks); natural areas and woods are not in it.
  Coverage per park was not examined.
- Trees appear at their planting year and grow to today's size in six years (the viewer's rule), so a
  plane of 1935 has its 2026 size from 1941.
- Not looked at on screen. The viewer draws a crown at twice its stored radius (at least 4 m) and a
  height at 1.45 times: along New York's closely planted streets that may read as a closed hedge.
- New Jersey and the other counties of the wider map have no inventory here.

## Wiring (for the lead; nothing outside the stage's own files was edited)

Run: `cd pipeline && ../.venv/bin/python street_trees.py` (download, build, check). Downloads: 460 MB in
`data/raw/street_trees/`, about 6 minutes, cached per table (delete a table's folder to refresh it).
`build`: under 3 minutes, 1.4 GB peak. Inputs from other stages: `data/interim/nyc_building_points.parquet`,
`data/interim/grid_detail_landyear.npy`, `terrain_grid.grid_def`, the TIGER county outlines. Re-run
`street_trees.py build` after every rebuild of the buildings or of the land years.

Makefile (after `buildings`; before `terrain` if the mask below is used):

```
# real street and park trees: NYC Parks' living inventory (ForMS) + the 2015 census, dated by planting
# records, the census and trunk diameter -> viewer/public/data/street-trees.bin.gz (Manhattan) + region-trees/
street-trees: buildings land
	$(P) ../$(PY) street_trees.py
```

Terrain (`terrain_tiles.decorations`, after `tree_fine &= ~block`): canopy pixels that an inventory tree
already stands for give way to it —

```
    if name == "detail":
        from street_trees import inventory_mask
        tree_fine &= ~inventory_mask(t, shape, reach=1)
```

(`t`, `shape`: the canopy grid's affine and shape as already defined there; an empty mask if the tree
stage has not run.) This removes about 100,000-140,000 of the terrain's 2.3 million present-day trees.

SOURCES.md rows: the table under "Sources" above (ids `forms_tree_points`, `forms_planting_spaces`,
`census_2015`, `usfs_utd`; `census_2005` / `census_1995` as examined and not used).

Viewer (not edited): `decodeTrees` could read an `end_year` column to draw removed trees, and the
`source` / `park` columns for a click popup ("planted 2019, NYC Parks record" / "about 1950, from a
36 in trunk").
