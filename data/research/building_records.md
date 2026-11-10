# Recorded construction and demolition dates (official datasets)

Stage: `pipeline/building_records.py` (downloads cached under `data/raw/records/`, fetched
2026-11-10). Every number below is in `data/interim/records/report.json`, rewritten by each run.

| Output | Rows | What |
|---|---|---|
| `data/tables/known_building_dates.records.csv` | 9,523 | standing buildings: a recorded year, by BIN |
| `data/manual/demolished/demolished_footprints.geojson` | 42,031 (27.4 MB) | buildings demolished 1996-2026, real outlines |
| `data/manual/demolished/flagged.csv` | 8,977 | historic outlines **not** written, with the reason |
| `data/interim/records/year_bounds.csv` | 88,453 | HPD legal class → not-before / not-after per BIN (not committed; rebuilt by the stage) |
| `data/interim/records/*.csv`, `records_by_bin.parquet` | | side lists described at the end |

## What the city's open records can and cannot do

- **Demolitions since 1996 exist as a layer** (source 1). It is the valuable file.
- **Construction dates before 1989 do not exist as open records per building**, except public
  housing (NYCHA) and the owner-reported years of large buildings (Local Law 84). The Department
  of Buildings' open job data starts in 1989; certificates of occupancy in July 2012. So the
  four fifths of the city on placeholder years cannot be re-dated from recorded years. What
  the records give instead for old buildings is **bounds**: the legal class of 88,453 multiple
  dwellings (old-law tenement = before April 1901, new-law = 1901-1929, …), which the pipeline's
  estimates break for 22,675 buildings — see "Bounds".
- For buildings since 1989 the assessor's year is nearly always there and is **the year of
  the permit, not of completion** — see the quality table.

## Sources

All from NYC Open Data (https://data.cityofnewyork.us), Socrata API `/resource/<id>.csv`.
Licence: none of the datasets declares one in its metadata; all fall under the NYC Open Data
terms of use (https://opendata.cityofnewyork.us/overview/#termsofuse — public data, free to
use, no warranty), the wording `SOURCES.md` already uses. Rows = rows downloaded.

| # | Dataset (id, publisher) | Rows | Fields used | Used for |
|---|---|---|---|---|
| 1 | **BUILDING_HISTORIC** `ipkp-snf6`, Office of Technology and Innovation — https://data.cityofnewyork.us/d/ipkp-snf6 ; metadata https://github.com/CityOfNewYork/nyc-geo-metadata/blob/main/Metadata/Metadata_BuildingHistoric.md | 51,008 | the_geom, BIN, DOITT_ID, BASE_BBL, CONSTRUCTION YEAR, DEMOLITION YEAR, HEIGHT ROOF (ft), FEATURE CODE, LAST_STATUS_TYPE, LAST_EDITED_DATE, NAME | demolished outlines |
| 2a | DOB Job Application Filings `ic3t-wcy2`, Dept. of Buildings — https://data.cityofnewyork.us/d/ic3t-wcy2 (job types NB, DM only) | 310,956 filings = 111,988 new-building and 56,860 demolition jobs, 1989-2023 | job__, bin__, job_type, signoff_date, pre__filing_date, fully_permitted, proposed / existing stories and height, proposed_occupancy, job_description | completion of new buildings; demolition dates and storeys |
| 2b | DOB NOW: Build – Job Application Filings `w9ak-ipjd` — https://data.cityofnewyork.us/d/w9ak-ipjd (New Building, Full Demolition) | 84,101 filings | job_filing_number, bin, signoff_date, first_permit_date, filing_date, stories, height | same, jobs since 2016 |
| 2c | DOB Certificate Of Occupancy `bs8b-p36w` — https://data.cityofnewyork.us/d/bs8b-p36w (NB jobs) | 53,526 | job_number, c_o_issue_date | first certificate, from July 2012 |
| 2d | DOB NOW: Certificate of Occupancy `pkdm-hqz6` — https://data.cityofnewyork.us/d/pkdm-hqz6 (new buildings) | 35,816 | job_filing_name, c_of_o_issuance_date | first certificate, from 2021 |
| 2e | Historical DOB Permit Issuance `bty7-2jhb` and DOB Permit Issuance `ipu4-2q9a` (NB and DM permits) — https://data.cityofnewyork.us/d/bty7-2jhb , https://data.cityofnewyork.us/d/ipu4-2q9a | 221,473 + 326,745 | job, issuance_date | first permit of a job (a building is not older than its permit) |
| 3 | NYCHA Development Data Book `evjd-dqpz` + NYCHA Residential Addresses `3ub5-4ph8`, NYC Housing Authority — https://data.cityofnewyork.us/d/evjd-dqpz , https://data.cityofnewyork.us/d/3ub5-4ph8 | 346 developments; 2,955 addresses = 1,891 BINs of 216 developments | tds_, type, completion_date; tds, bin, development | public housing |
| 4 | NYC Building Energy and Water Data Disclosure for Local Law 84, 2023 to present `5zyy-y8am`, DOB — https://data.cityofnewyork.us/d/5zyy-y8am | 103,297 (three report years) | nyc_building_identification, year_built, number_of_buildings, primary_property_type_self | owner-reported year of large buildings, incl. city property (schools `DOE_…`, CUNY, parks) |
| 5 | Housing Database Project Level Files `br6q-ssj3`, Dept. of City Planning — https://data.cityofnewyork.us/d/br6q-ssj3 | 111,909 | job_number, job_type, datecomplt ("the date of the earliest certificate of occupancy") | first certificate of residential new buildings completed since 2010 |
| 6a | Property Valuation and Assessment Data, Tax Class 1 `m8p6-tp4b` and Tax Classes 2-4 `kevu-8hby`, Dept. of Finance (fiscal years 2010-2017) — https://data.cityofnewyork.us/d/m8p6-tp4b , https://data.cityofnewyork.us/d/kevu-8hby | FY2017: 708,678 + 407,914; FY2010: 707,902 + 372,100 | bble, yrb, **yrb_flag** (`E` = estimated), bldgs, story | the assessor's own estimate flag; year and storeys of lots cleared after 2010 |
| 6b | Buildings Subject to HPD Jurisdiction `kj4p-ruqc`, Housing Preservation and Development — https://data.cityofnewyork.us/d/kj4p-ruqc | 381,934 | bin, dobbuildingclass, lifecycle, recordstatus | legal class of multiple dwellings → bounds |

Looked at and **not used**:
- NYC Parks Structures `n8q6-i44s` (2,860 rows): its construction year equals the footprint's
  year for 1,875 of 1,885 structures — a copy of OTI's field, no new evidence.
- Affordable Housing Production by Building `hg8x-zxpr` (HPD, 2014 →): 2,559 new-construction
  BINs; 2,079 already have a DOB record (HPD's date is a median 0.5 years after the first
  certificate). The other 480 have no height to check the BIN against; left out.
- NYC Municipal Building Energy Benchmarking Results `vvj6-d5qx` (DCAS): the published
  columns are shifted (the `year_built` column holds emission figures); unusable.
- City Owned and Leased Property `fn4k-qyk2`, DCAS Managed Public Buildings `xx2p-4jnq`,
  DOE Building Space Usage `wavz-fkw8`, Enrollment Capacity and Utilization `gkd7-3vk7`: no year.
- **Schools, CUNY, hospitals:** no School Construction Authority / DOE / Health + Hospitals
  table with a year built exists on NYC Open Data (catalogue searched for "school building
  year built", "BCAS", "building condition assessment survey", "SCA building", "hospital
  building year"). The SCA's Building Condition Assessment Survey is published per building
  as PDF, not as data. The only official per-building year for them is Local Law 84 (1,600
  single-building K-12 properties; 145 of them told the pipeline something new).
- MapPLUTO archives 2002 → : not downloaded. The Finance rolls of FY2010 / FY2017 (6a) carry
  the same assessor's year per lot, with the estimate flag PLUTO drops.
- The current roll `8y4t-faws` no longer carries the flag (68 `E` in 2.3 M rows).

## 1. Demolished footprints

OTI moves a footprint to BUILDING_HISTORIC "when [it is] demolished or significantly
altered". 51,008 rows; 47,789 with status `Demolition`; demolition years 1996-2026.

Rules (in order; a row is written only if it passes all):

| Not written (in `flagged.csv`) | Rows | Why |
|---|---|---|
| `superseded_outline` | 2,953 | status Alteration / Merged / Split / Correction / Constructed … and no demolition year: an earlier outline of a building that mostly still stands |
| `coincides_with_older_standing` | 1,537 | IoU > 0.6 with a standing footprint whose year is earlier than the demolition (the brief's check) |
| `inside_older_standing` | 2,688 | more than half of the outline lies under standing footprints older than the demolition |
| `same_outline_unconfirmed` | 1,314 | no DOB demolition job on the BIN and IoU > 0.6 with a standing footprint: probably the standing building redrawn |
| `same_building_redrawn` | 196 | no DOB demolition job, IoU > 0.4 and the same roof height (± 15 %) as the standing building |
| `short_lived_unconfirmed` | 28 | no DOB demolition job, built five years or less before its "demolition", under a standing building: an outline drawn during construction |
| `duplicate_outline` | 185 | the same outline twice in the layer (IoU > 0.6): the record with a year / height / later edit kept |
| `tiny` | 76 | under 12 m² (the pipeline's own floor) |

The "year of the standing footprint" is the year of a fitting DOB new-building job when there
is one, else the assessor's year (footprint, else PLUTO).

**end_year** — OTI's DEMOLITION YEAR. Where a DOB demolition job exists for the BIN the two
agree: OTI year = DOB sign-off year in 24,495 of 29,784 comparable rows (82 %), within one
year in 90 %. So: the day of the sign-off when it falls in OTI's year (20,125 features,
`end_src = oti_year+dob_signoff`); a sign-off up to three years *before* OTI's year wins
(1,932; the building was certified gone); otherwise OTI's year + 0.5 (19,651). No demolition
year on the record (323 rows): the DOB sign-off (114), else the date the outline was retired
(209, `estimated`: "demolished by then").
`end_check` says what confirms the year: `dob_signoff_same_year` 20,125 · `dob_signoff_earlier`
1,932 · `dob_job` 1,908 (OTI's year lies between permit and sign-off) · `dob_signoff` 114 ·
**`none` 17,952** (no DOB demolition job found for the BIN, or no BIN). Of the unconfirmed,
4,083 were retired from the map three or more years after the year on the record; those carry
`end_quality = estimated` (4,292 in all) and the retirement date in `retired`.

**start_year** — CONSTRUCTION YEAR on the record is the assessor's year of the lot. In records
edited before 2017 it is often the year of the building that *replaced* the demolished one
(year minus demolition year: -1 → 2,380 rows, 0 → 4,176, +1 → 991, … +6 → 79, +7 → 44), so
there a year less than six years before the demolition is not used (10,559 years rejected;
after 2017 the year only has to precede the demolition). Then: the FY2010 assessment roll for
lots cleared from 2010 on with one building (2,114); a fitting DOB new-building job on the BIN
(188). `start_quality`: `recorded` 3,728 (assessor's year, not a placeholder and not flagged
`E` by Finance; or the DOB job) · `estimated` 18,509 (a placeholder year: treat it as the
pipeline treats heaps) · null 19,794 (no usable year: the lead must estimate).

**height_m** — HEIGHT ROOF (measured, ft → m): 23,394 features (none for records edited
before 2009). **storeys** — "existing stories" of the DOB demolition job, else the FY2010
roll: 27,603. Both: 17,477; neither: 8,495. Where they contradict each other the implausible
one is dropped (more than 8 m per storey → height dropped; under 2 m → storeys dropped; 2,941
cases).

Demolitions written per year: 1996 195 · 1997 271 · 1998 500 · 1999 442 · 2000 1,013 · 2001
1,035 · 2002 1,362 · 2003 1,839 · 2004 2,470 · 2005 2,831 · 2006 3,019 · 2007 2,693 · 2008
1,075 · 2009 567 · 2010 546 · 2011 1,467 · 2012 555 · 2013 1,563 · 2014 1,303 · 2015 1,926 ·
2016 1,771 · 2017 1,822 · 2018 1,777 · 2019 1,366 · 2020 1,409 · 2021 1,347 · 2022 1,821 ·
2023 1,256 · 2024 1,098 · 2025 1,136 · 2026 553. 17,507 stand on ground with no building
today; 9,835 carry a BIN that a standing building reuses.

### How complete the layer is

DOB demolition jobs signed off, by period, against the layer (by BIN):

| Sign-off | BINs | in BUILDING_HISTORIC | BIN still in today's footprints | in neither |
|---|---|---|---|---|
| 1990-94 | 822 | 2 % | 73 % | 26 % |
| 1995-99 | 2,180 | 45 % | 77 % | 13 % |
| 2000-04 | 6,853 | 60 % | 81 % | 5 % |
| 2005-09 | 10,421 | 45 % | 72 % | 10 % |
| 2010-14 | 4,988 | 37 % | 59 % | 17 % |
| 2015-19 | 8,842 | 60 % | 50 % | 6 % |
| 2020-24 | 6,423 | 87 % | 10 % | 7 % |
| 2025-26 | 2,230 | 79 % | 15 % | 8 % |

A BIN "still in today's footprints" is either a partial demolition (a garage, a rear
building) or a replacement that kept the number, so the share of whole buildings missing from
the layer cannot be read off exactly — but between 2005 and 2014 it is large. 3,809
signed-off demolitions have a BIN in neither layer: buildings certainly gone, with no outline
in the city's data (`data/interim/records/dob_demolitions_without_outline.csv`: address, lot,
date, storeys, point). Nothing before 1996 is in the layer.

## 2. Standing buildings

One row per BIN, best record first: NYCHA > first certificate of occupancy > sign-off > Local
Law 84. A DOB job counts only if it **fits the footprint**: proposed height (or storeys ×
3.3 m) within 0.55-1.5 × the measured roof height, and not a garage / shed job on a house's
BIN (72,850 BINs fit, 5,269 do not). Completion of a job = the first certificate of
occupancy where the open data can know it (the Housing Database for residential jobs since
2010; the certificate tables only for jobs permitted from July 2011, because they start in
July 2012), else the sign-off.

A row is written when:

| Tag at the end of `note` | Rows | Rule |
|---|---|---|
| `[no_recorded_year]` | 1,323 (NYCHA 447, LL84 816, DOB 60) | the assessor's year is a placeholder or missing |
| `[first_co_later]` | 6,478 | first certificate of occupancy two or more years after the assessor's year |
| `[replaced_building]` | 600 | a fitting new-building job on a lot whose year is more than ten years older, **and** PLUTO's year agrees with the job or OTI records a demolition on the lot before it |
| `[signoff_after_demolition]` | 586 | sign-off later than the assessor's year, and OTI records a demolition on the lot after the assessor's year: the building cannot be as old as the assessor says |
| `[nycha_earlier]` | 174 | NYCHA's date two or more years before the assessor's year (the assessor's year is impossible) |
| `[nycha_later]` | 362 | NYCHA's date two or more years after it |

Not written (all in `records_by_bin.parquet`, column `decision`): 41,714 DOB + 675 NYCHA +
16,615 LL84 records that agree with the assessor within a year; **21,799 sign-offs that are
merely later** than an assessor's year lying between permit and sign-off (a sign-off is an
upper bound); 1,054 new-building jobs on a much older lot that nothing corroborates; 386 where
the assessor's year is later than the record; 2,992 buildings the Landmarks Commission dates
(left alone); LL84 years that repeat the placeholder (6,076), contradict a recorded assessor's
year (3,529), are after 1988 without a new-building job (315; "if your property has undergone a
complete renovation … you can indicate the date of this renovation") or more than 15 years
from the placeholder (511).

NYCHA: the Data Book's `completion_date` is "the Initial Occupancy Completion Date: the date
when the development was at least 95 % occupied" — one date per development, its buildings
finished up to about two years earlier. Only developments of type NEW CONST are used (224
BINs of REHAB developments skipped: their date is the renovation). The addresses table covers
216 of the 346 developments (those converted to private management are missing from it).
Spot checks against published histories: Marcy 1949, Ravenswood 1951, Sumner 1958, Redfern
1959, Ingersoll 1944 agree.

Local Law 84 rows say "estimated" in the note (so the pipeline marks them `estimated`): the
year is typed in by the owner.

## Quality: how far the assessor's year is from the record

Buildings with both a record and an assessor's year that is **not** a placeholder (record
year minus assessor's year):

| Record | n | same year | within 1 | within 2 | record 2+ later | record 2+ earlier | 10+ apart | median | 10 % … 90 % |
|---|---|---|---|---|---|---|---|---|---|
| DOB first certificate of occupancy (Housing Database) | 20,508 | 39 % | 68 % | 81 % | 31 % | 1 % | 2.6 % | +1 | 0 … +4 |
| DOB first certificate (certificate tables) | 1,629 | 52 % | 81 % | 91 % | 17 % | 2 % | 2.0 % | 0 | 0 … +2 |
| DOB sign-off | 49,220 | 12 % | 54 % | 78 % | 46 % | 0.3 % | 2.3 % | +1 | 0 … +4 |
| NYCHA (95 % occupied) | 1,211 | 18 % | 56 % | 72 % | 30 % | 14 % | 6.7 % | +1 | -4 … +4 |
| Local Law 84 (owner) | 20,144 | 76 % | 83 % | 87 % | 8 % | 10 % | 7.1 % | 0 | -2 … +1 |

Why the DOB records run later: the assessor's year is the **permit** year. Assessor's year
minus the year of the job's first permit (71,357 buildings): same year 44 %, +1 33 %, +2 11 %,
earlier 3 %. Sign-off / first certificate minus permit: +1 year 30 %, +2 32 %, +3 15 %, later
17 %. So for buildings since 1989 the assessor's non-placeholder year is about one year before
the building was finished, and 2-3 % are a previous building's year (10+ years off).
For public housing of 1936-2005 the assessor's "exact" years are much worse: only 56 % within
a year, 7 % ten or more years off.

Placeholder years, where a real date exists (NYCHA buildings on a heap year, n = 447): the
pipeline's estimate is within 3 years in 59 %, median error +0.5 years, 10 %-90 % -10.7 … +10.4
years — unbiased, ± 10 years. DOB records on placeholder-year lots are replacements (the
record is 70-93 years later): those are the `[replaced_building]` rows.

## Bounds from the legal class (not years; `data/interim/records/year_bounds.csv`)

HPD records the Department of Buildings' class of every multiple dwelling. Multiple Dwelling
Law § 4 (https://newyork.public.law/laws/n.y._multiple_dwelling_law_section_4 ; official text
https://www.nysenate.gov/legislation/laws/MDW/4, which did not load through the proxy): a
"tenement" was "erected before April eighteenth, nineteen hundred twenty-nine"; an "old-law
tenement" is one "existing before April twelfth, nineteen hundred one"; "heretofore" erected
or converted means before 18 April 1929. A new-law tenement is the tenement that is not
old-law (built under the Tenement House Act of 1901) — the usual reading, not a sentence of
the statute.

| Class | BINs | not before | not after | agrees with LPC's exact dates (± 3 y) |
|---|---|---|---|---|
| OLD LAW TENEMENT | 24,692 | | 1901.28 | 98.6 % of 1,695 |
| NEW LAW TENEMENT | 42,490 | 1901.28 | 1929.3 | 89.9 % of 2,028 |
| HERETOFORE CONVERTED CLASS A / B | 20,701 | | 1929.3 | 99.6 % of 3,074 / 100 % of 405 |
| HERETOFORE ERECTED EXISTING CLASS A / B | 570 | | 1929.3 | 100 % of 123 / 98.5 % of 65 |

Left out because they fail the same test: "hereafter erected class A / B" (31 % / 62 %
older than 1929 by LPC's date — buildings reclassified after an alteration), "converted …
law tenement", the single-room-occupancy classes.

Against the pipeline as built on 2026-11-10: **22,675 estimated years lie outside their
bound** by more than a year (13,165 old-law tenements dated after 1902, median 1920; 7,579
new-law tenements, mostly 1930-31 placeholders two to three years late; 2,061 "heretofore"
buildings). And the assessor's *non-placeholder* years break the bounds too: 1,513 of 1,760
old-law tenements with an "exact" assessor's year are dated three or more years after 1901
(median 27 years), 318 of 1,100 "heretofore converted class A", 838 of 15,087 new-law. Those
years are alterations, not construction.

Also: `dof_flagged_estimates.csv` — 20,883 buildings whose year the pipeline treats as exact
(not a heap year) but which Finance itself flags `E` (1985: 2,067, 1986, 1987, 1984, 1978 …).
The flag is one-way: of 825 k placeholder years 738 k carry it, but years without the flag
still heap (Brooklyn tax class 1: 2,269 unflagged on 1931 against a median of 51 on the
neighbouring years), so its absence proves nothing.

## Checks run on the outputs (2026-11-10)

- `known_building_dates.records.csv`: 9,523 rows, every BIN in today's footprints, one row
  per BIN, years 1893.0-2026.82, no end_year; "estimate" appears only in the LL84 notes.
- `demolished_footprints.geojson`: 42,031 polygons / multipolygons, all valid, ids unique,
  end 1991.5-2026.8, no start ≥ end, starts 1800-2023. Independent re-check of the brief's
  rule (IoU > 0.6 with a standing footprint whose *assessor's* year is before the end year):
  120 pairs remain, and in all 120 the standing BIN has a fitting DOB new-building job
  completed in or after the demolition year (a rebuild whose assessor's year is stale; 102 of
  them are in the known-dates rows or agree already).
- Known demolitions looked up by hand: 270 Park Avenue (1958-2021.4, 215.8 m, 52 storeys),
  5 Pointz (2014-15), Drake Hotel (2008.5, 75 m), 130 Liberty Street — right. **Shea Stadium
  (`oti-h560134`) and the old Yankee Stadium (`oti-h72245`) carry 2004 on the record and were
  retired in 2009** (really 2009 and 2010): no DOB job, so `end_check = none`,
  `end_quality = estimated`, `retired = 2009.46`.

Not checked: nothing was looked at on screen; no rebuild was run with the files merged; the
stage was not re-run against a pipeline that already contains its rows (the decisions use
only the assessor's raw year, the placeholder list and the LPC table so that they should not
change — reasoned, not tested).

## Known weak spots

- 17,952 demolition years rest on OTI's field alone. `big_unconfirmed_demolitions.csv`
  lists the 83 over 4,000 m² (airport terminals, the two stadiums, Kings Plaza …).
- The layer is incomplete (table above). Hotel Pennsylvania (2023) is not in it; St
  Vincent's Hospital has two small outlines only.
- Outlines drawn during construction survive at large sites without a standing building of
  the same shape — the World Trade Center site has six (`oti-h79828`, `oti-h1108000`,
  `oti-h996388`, `oti-h1078803`, `oti-h1054572`, `oti-h1037035`).
- A height measured during demolition is too low (130 Liberty Street: 58.8 m for 26 storeys).
- 47 % of the demolished footprints have no start year, 44 % a placeholder.
- `[first_co_later]` and `[nycha_later]` move a building later than a recorded assessor's
  year on the strength of an occupancy record. If the lead prefers "the structure stands" to
  "the building is occupied", drop those two tags.
- 42 footprints still drawn today are marked for demolition by OTI and have a signed-off DOB
  demolition (`standing_marked_for_demolition.csv`); not written to the known-dates file,
  which needs a start year.

## Side lists (`data/interim/records/`, rebuilt by the stage)

| File | Rows | Use |
|---|---|---|
| `records_by_bin.parquet` | 105,201 | every candidate record per BIN, with `decision` |
| `year_bounds.csv` | 88,453 | bin, not_before, not_after, class, the pipeline's year and whether it violates |
| `dof_flagged_estimates.csv` | 20,883 | bin, year: assessor's estimates the pipeline treats as exact |
| `standing_after_demolition.csv` | 4,639 | standing BIN, `not_before` = end of the demolished building on its ground, where the pipeline starts the standing building earlier (4,281 of them on a recorded assessor's year — mostly the same calendar year) |
| `standing_marked_for_demolition.csv` | 42 | bin, sign-off date |
| `dob_demolitions_without_outline.csv` | 3,809 | demolitions with no outline in the city's data |
| `big_unconfirmed_demolitions.csv` | 83 | to check by hand |
| `flagged_outlines.geojson` | 8,977 | the outlines behind `flagged.csv` |

## Rows for `SOURCES.md` (the lead's file)

| id | What | From | Licence | Used for |
|---|---|---|---|---|
| `oti_building_historic` | Building Footprints Historic: outlines of buildings demolished since 1996, construction and demolition year, roof height | NYC Office of Technology and Innovation, NYC Open Data `ipkp-snf6` — https://data.cityofnewyork.us/d/ipkp-snf6 | NYC Open Data terms of use | Demolished buildings (`data/manual/demolished/`) |
| `dob_jobs` | Job filings, permits and certificates of occupancy: new-building and demolition jobs since 1989 | NYC Department of Buildings, NYC Open Data `ic3t-wcy2`, `w9ak-ipjd`, `bs8b-p36w`, `pkdm-hqz6`, `bty7-2jhb`, `ipu4-2q9a`; DCP Housing Database `br6q-ssj3` | NYC Open Data terms of use | Recorded completion of buildings since 1989; day and storeys of demolitions |
| `nycha` | Development Data Book and Residential Addresses | NYC Housing Authority, NYC Open Data `evjd-dqpz`, `3ub5-4ph8` | NYC Open Data terms of use | Completion of public-housing developments |
| `ll84` | Local Law 84 energy benchmarking disclosure (owner-reported year built) | NYC Department of Buildings, NYC Open Data `5zyy-y8am` | NYC Open Data terms of use | Year of large buildings on a placeholder year (`estimated`) |
| `dof_roll` | Property Valuation and Assessment Data FY2010 / FY2017 (year built with the estimate flag) | NYC Department of Finance, NYC Open Data `m8p6-tp4b`, `kevu-8hby` | NYC Open Data terms of use | Year and storeys of lots cleared after 2010; which assessor's years are estimates |
| `hpd_buildings` | Buildings Subject to HPD Jurisdiction (legal class of multiple dwellings) | NYC Housing Preservation and Development, NYC Open Data `kj4p-ruqc` | NYC Open Data terms of use | Not-before / not-after bounds for tenements |
