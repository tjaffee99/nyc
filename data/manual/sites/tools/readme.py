"""Write data/manual/sites/README.md (prose + tables generated from the built files).

  cd data/manual/sites && ../../../.venv/bin/python -I tools/readme.py
"""
import collections
import json
import re
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
S = HERE.parent


def flags(p):
    n = p["note"]
    out = []
    if p["date_basis"] != "text" or re.search(r"start (year )?(= that year: by then|estimated)|\(start[^)]*estimated|year estimated: 'around", n):
        out.append("start")
    if re.search(r"[Ee]nd year[^.;]*estimated|closing year[^.;]*estimated|end year =", n):
        out.append("end")
    if "utline estimated" in n or "outline estimate" in n or "(estimated)" in n:
        out.append("outline")
    return out


def outline_src(p):
    n = p["note"]
    if "utline estimated" in n or "outline estimate" in n or "(estimated)" in n:
        return "estimated"
    if "USGS" in n:
        return "USGS sheet"
    if "LPC" in n:
        return "LPC district"
    if "street block" in n:
        return "street blocks"
    return "OpenStreetMap"


def main():
    g = json.loads((S / "sites.geojson").read_text())
    P = [f["properties"] for f in g["features"]]
    k = pd.read_csv(ROOT / "data/tables/known_building_dates.sites.csv")
    d = pd.read_csv(ROOT / "data/tables/notable_demolished.sites.csv")
    br = pd.read_csv(S / "edition_brackets.csv")
    sys.path.insert(0, str(HERE))
    import buildings_def
    n_def = len(buildings_def.BUILDINGS)
    kinds = collections.Counter(p["kind"] for p in P)
    fl = [flags(p) for p in P]
    n_text = sum(1 for p, f in zip(P, fl) if "start" not in f)
    n_start_est = sum(1 for f in fl if "start" in f)
    n_end = sum(1 for p in P if p["end_year"] < 9999)
    n_end_est = sum(1 for f in fl if "end" in f)
    n_out_est = sum(1 for f in fl if "outline" in f)
    kt = k[~k.id.str.startswith("site_")]
    km = k[k.id.str.startswith("site_map:")]
    kf = k[k.id.str.startswith("site_floor:")]
    ks = k[k.id.str.startswith("site_stamp:")]
    two = int(km.note.str.contains("absent on").sum())
    L = []
    A = L.append
    A("# Military and industrial sites (`data/manual/sites/`)\n")
    A("Forts, navy yards, bases, rail yards, gasworks, power plants, refineries, shipyards, works, markets, landfills and "
      "the island institutions shaped the city, and today's data dates them badly: exempt and industrial property carries "
      "the lot's year on every building (Rikers Island: 201 buildings at 1933; Fort Tilden: 50 at 1900-01), an imputed "
      "year, or - where the site is gone - nothing at all. This folder holds the researched sites: their outlines and "
      "years, the years of standing buildings inside them, and the structures that are gone. Ported from the Bay "
      "project's `data/manual/industrial_sites/` (its decisions 38 and 42), with one difference that matters: the "
      "map-edition brackets, which dated 984 footprints there, were tested against independent records here and mostly "
      "failed (see \"What the map brackets are worth\").\n")
    A("## Files\n")
    A("| file | what |\n|---|---|")
    A(f"| `sites.geojson` | {len(P)} site features (one per site and name period), WGS84 |")
    A(f"| `../../tables/known_building_dates.sites.csv` | {len(k)} rows: {len(kt)} researched years of standing buildings "
      f"(text), {len(km)} years from USGS map editions (`site_map:` ids, estimated), {len(ks)} lot-stamp fixes "
      f"(`site_stamp:` ids, estimated), {len(kf)} site floors (`site_floor:` ids, not dates) |")
    A(f"| `../../tables/notable_demolished.sites.csv` | {len(d)} structures that are gone ({int(d.outline.notna().sum())} "
      "with an outline, the rest as `footprint_m` + `rotation_deg`) |")
    A(f"| `edition_brackets.csv` | every footprint read on the USGS editions ({len(br)} rows, {br.site.nunique()} sites): "
      "EVIDENCE ONLY - do not apply it beyond the rows already in the building table |")
    A("| `tools/` | `sites_def.py`, `sites_def2.py` (the sites), `buildings_def.py`, `demolished_def.py`, `build.py`, "
      "`build_buildings.py`, `build_demolished.py`, `readme.py`; `geom.py` (outlines), `fetch_wp.py` + `wp_titles.txt` + "
      "`wp_facts.py` (source text), `topo.py`, `trace_ink.py`, `date_editions.py`, `run_editions.py`, "
      "`validate_brackets.py` (USGS editions), `audit.py` |")
    A("| `traced/` | outlines vectorised from USGS sheets (`trace_ink.py`) |")
    A("\nDownloads are in `data/raw/sites/` (`wp/` article text, `usgs/` sheet crops and metadata), scratch in "
      "`data/interim/sites/` (`audit.csv`, `editions/`). Rebuild (a few minutes; `run_editions.py` about 30 minutes "
      "cold, each process under 1 GB):\n")
    A("```\ncd data/manual/sites\n../../../.venv/bin/python -I tools/fetch_wp.py          # cached; one request a second\n"
      "../../../.venv/bin/python -I tools/build.py --check       # sites.geojson; lists years the source text lacks\n"
      "../../../.venv/bin/python -I tools/run_editions.py        # edition_brackets.csv (--rebracket: from saved readings)\n"
      "../../../.venv/bin/python -I tools/build_buildings.py     # known_building_dates.sites.csv\n"
      "../../../.venv/bin/python -I tools/build_demolished.py    # notable_demolished.sites.csv\n"
      "../../../.venv/bin/python -I tools/audit.py               # the built file's years inside each site\n"
      "../../../.venv/bin/python -I tools/readme.py              # this file\n```\n")
    A("### `sites.geojson` properties\n")
    A("`id`, `name` (the name in use over `start_year`..`end_year`; a renamed site has one feature per name), `kind` "
      "(`fort` | `military_base` | `navy_yard` | `rail_yard` | `gasworks` | `power_plant` | `refinery` | `shipyard` | "
      "`factory` | `terminal` | `landfill` | `quarry` | `prison` | `hospital_campus` | `asylum` | `other`), `start_year`, "
      "`end_year` (9999 = still that), `after` (`park` | `city` | `vacant` | `same` = the ground stays as `ground` under "
      "its next name), `ground` (`paved` | `yard` | `open`: how the terrain should show it), `label`, `source_url`, "
      "`note` (says \"estimated\" for every year or outline that is), plus `date_basis` (`text` | `estimated` for the "
      "start year), `floor` (a floor row exists), `area_ha`, `lon`, `lat` (a point inside).\n")
    A("Features overlap on purpose where a site was renamed (Fort Columbus / Fort Jay, Blackwell's / Welfare Island, "
      "Morse / Bethlehem). An outline is today's or the last mapped one: where the ground is made land (Governors "
      "Island's south, the Navy Yard's east, Rikers, Ellis Island, the yards on fill) the terrain's land year decides "
      "when the ground exists - paint a site cell only once it is land. Fort Lafayette's island is water today.\n")
    A("## Method\n")
    A("**Years** are from text: the Wikipedia article named in `source_url` (CC BY-SA; facts only), whose wikitext is "
      "cached in `data/raw/sites/wp/` and was searched for each year (`tools/wp_facts.py grep`; `build.py --check` fails "
      "a year the article does not contain unless the note calls it estimated). A year the article gives only loosely "
      "('around 1851', 'by 1880', 'until the 1970s') is in the table as estimated. No founding year of a site comes "
      "from a map bracket. A site without a citable founding year was left out (list at the end).\n")
    A("**Outlines**: OpenStreetMap land-use and island polygons (Overture 2026-10-21.0 `region5_land_use`, `base_land`; "
      "ODbL) where the site, or the park or estate that took its ground, is mapped; Landmarks Preservation Commission "
      "historic districts (Governors Island, Fort Totten, Sea View, Eberhard Faber; the city's file is in State Plane "
      "feet although its header says CRS84 - `geom.lpc` reprojects it); street blocks polygonized from today's streets "
      "(`geom.block`); Fort Lafayette's island traced on the USGS The Narrows sheet. Everything else is a circle or a "
      "hand-given ring around the cited location and says \"Outline estimated\" - the tax lots on disk have no "
      "geometry, so no site is outlined from its lots.\n")
    A("**Standing buildings** (`buildings_def.py`): the footprint is found from the name OpenStreetMap gives a building "
      "inside the site, or from the article's coordinates, and its BIN read from `nyc_footprints_raw.parquet`. A row is "
      f"not written where the built file already has an LPC year within five years ({n_def - len(kt)} of the {n_def} "
      "buildings checked: most armories, the IRT powerhouse, Castle Williams, Liggett Hall ...).\n")
    A("**Site floors**: one `site_floor:<site id>` row per site whose outline is a mapped one and whose founding is "
      "from text: no building inside the outline predates the founding. Meant for estimated years only (LPC and "
      "recorded years stand: Governors Island, Fort Totten and Welfare Island keep buildings older than a later name). "
      f"Where the assessor's year is the lot's year stamped on the site's buildings and older than the site, the floor "
      f"is written out as rows ({len(ks)} `site_stamp:` rows, all in " + ", ".join(sorted(set(ks.id.str.split(":").str[1]))) +
      "), because the pipeline's floor does not reach recorded years.\n")
    A("**Structures that are gone** (`demolished_def.py`): outlines of Fort Lafayette, the two Elmhurst gas holders, "
      "five holders of the Gas House District were read on USGS 1:24,000 sheets in a metre grid (`topo.py render`), "
      "Goldwater Memorial Hospital and City Hospital are the sheet's own ink, vectorised (`trace_ink.py`, "
      "`traced/welfare_island_1966.json`); NAD27 by PROJ's three-parameter shift, +-10 m; Waterside is its two "
      "street blocks; the rest are rectangles from cited or estimated dimensions.\n")
    A("### What the map brackets are worth\n")
    A("`date_editions.py` reads every footprint of a site on each USGS 1:24,000 edition (1947 editions from 1940-42 "
      "photographs, 1954-57, 1966, 1977-81 photorevisions, 1995-98) and on the calibrated 1890s 1:62,500 sheets: "
      "*drawn* when black (or revision purple) ink, opened by 6 m, or hatching, covers 30 % of the footprint. The first "
      "sheet that draws a footprint after a sheet that leaves it empty brackets its year. Tested on the "
      f"{len(br)} footprints of {br.site.nunique()} sites:\n")
    A("* 319 footprints have an independent year (LPC exact, or an assessor year not shared by the lot). 49 of them "
      "got a clean absent-then-drawn bracket. **The independent year lay inside the bracket for 3.** For 35 the "
      "building is older than the bracket (Governors Island's 1870s houses 'absent 1940, drawn 1954'), for 11 newer.\n"
      "* Of 180 footprints independently dated to 1935 or earlier, 129 (72 %) are drawn on the first 1:24,000 sheet. "
      "Military posts are the worst (Governors Island 33 of 59, Fort Totten 27 of 39): the 1947 editions leave most "
      "buildings of a reservation off. Elsewhere about one old building in six is missed on a sheet, and the misses "
      "repeat on the next sheet (Sea View: 4 of 37 old pavilions bracketed 30-40 years late).\n"
      "* The 1947 editions fill built-up blocks solid black and rail-yard track fans read as buildings, so *drawn* is "
      "not evidence for a single footprint there (seen on the Coney Island and 207th Street yards).\n"
      "* `tools/validate_brackets.py` prints these numbers.\n")
    A(f"So the brackets are **not** used as the Bay project used them. `build_buildings.py` writes a map year only for "
      f"{km.id.str.split(':').str[1].nunique()} isolated civil campuses and plants founded after 1925 ({len(km)} rows): "
      f"{len(km) - two} footprints drawn on the first sheet after the site's founding take the founding year (the true "
      f"year lies between the founding and that sheet), and {two} absent-then-drawn brackets on Rikers Island, where the "
      "1966 and 1997 sheets were also looked at (the 1997 revision prints jails that the 1966 sheet lacks in purple; "
      "the 1977 photorevision, which carries six of the eight brackets, was read by the tool only). These rows could not be "
      "checked against records - no building in those sites has an independent year inside a bracket - and all say "
      "\"estimated\". Everything else stays in `edition_brackets.csv` as readings, not dates.\n")
    A("## Sites\n")
    A(f"{len(P)} features: " + ", ".join(f"{v} {k_}" for k_, v in kinds.most_common()) + ". Start years: "
      f"{n_text} from text, {n_start_est} estimated, 0 from map brackets. End years: {n_end} sites have ended, "
      f"{n_end_est} of those years are estimated. Outlines: {len(P) - n_out_est} mapped, {n_out_est} estimated.\n")
    A("| id | name | kind | years | estimated | outline | source (en.wikipedia.org/wiki/...) |\n|---|---|---|---|---|---|---|")
    for p, f in zip(P, fl):
        e = "" if p["end_year"] == 9999 else str(p["end_year"])
        A(f"| `{p['id']}` | {p['name']} | {p['kind']} | {p['start_year']}-{e} | {', '.join(f) or '-'} | {outline_src(p)} | "
          f"{p['source_url'].split('/wiki/')[-1]} |")
    A("\nThe `note` of each feature says how its years were obtained and what is estimated.\n")
    A("## Standing buildings with a researched year\n")
    A("| id | name | BIN | year | note |\n|---|---|---|---|---|")
    for r in kt.itertuples():
        A(f"| `{r.id}` | {r.name} | {int(r.bin)} | {int(r.start_year)} | {r.note} |")
    A("\nMap years (`site_map:<site>:<BIN>`): " + ", ".join(
        f"{s} {n}" for s, n in km.id.str.split(":").str[1].value_counts().items()) + ".\n")
    A("## Structures that are gone\n")
    A("| id | name | years | shape | height m | note |\n|---|---|---|---|---|---|")
    for r in d.itertuples():
        shp = "outline" if isinstance(r.outline, str) else f"{r.footprint_m} m, {r.rotation_deg} deg"
        A(f"| `{r.id}` | {r.name} | {r.start_year}-{r.end_year} | {shp} | {r.height_m} | {r.shape_note} |")
    A("\nNot duplicated: the lost landmarks already modelled in `viewer/src/landmarks/nyc-lost.ts` (none of the above is "
      "among them; Castle Williams, Battery Weed, Fort Tompkins and the Fort Hamilton casemate fort are civic models).\n")
    A("## Not done\n")
    A("* **No citable year found in the budget, so left out:** the Maspeth holders and the Brooklyn Union works in "
      "Greenpoint, the Astoria, Hunts Point, Citizens (Gowanus) and Coney Island gas works; Hudson Avenue, Hell Gate, "
      "Sherman Creek, Kent Avenue, Arthur Kill and Astoria generating stations (the outlines of four of them are in "
      "OpenStreetMap); Oak Point, Fresh Pond, Mott Haven, Highbridge, Arlington, St. George, Long Island City, "
      "Vanderbilt, Westchester, Lenox, Jerome, 240th Street and 36th-38th Street yards; the Harlem River yard before "
      "1991; Jay Street Connecting and New York Dock terminals; Port Mobil; Webb's and the other East River shipyards, "
      "Novelty and Delamater iron works; S.S. White, Atlantic Terra Cotta, the breweries, National Sugar; Wallabout "
      "Market (dated 1884-1941, no outline); the Brooklyn Terminal Market; St. Albans Naval Hospital; the Staten "
      "Island and the lost 71st Regiment armories; Great Kills and Soundview fills; Fort Stirling, Fort Number Eight, "
      "Fort Independence, Fort George, the North Battery.\n"
      "* **Not researched:** navy-yard ship houses, grain elevators, coal trestles and float bridges, brewhouses; "
      "Rikers Island's jails by name (the article has no opening years: 8 are bracketed, 193 keep the lot's 1933); "
      "the pavilions of North Brother, Randall's, Wards and Hart islands; Bush Terminal's lofts one by one "
      "(warehouses 1892-1910, lofts 1905-1925).\n"
      "* **Outlines** of 30-odd sites are circles or rings around a cited location, and site outlines do not grow "
      "(the Navy Yard's stages, Fresh Kills' mounds): one outline per name period.\n"
      "* Nothing was looked at in the viewer.\n")
    A("## Sources and licences\n")
    A("* Wikipedia (en), CC BY-SA 4.0 - facts and coordinates; one article per row in `source_url`; text cache "
      "`data/raw/sites/wp/` (titles in `tools/wp_titles.txt`).\n"
      "* OpenStreetMap via Overture Maps 2026-10-21.0 (`region5_land_use`, `base_land`, `base_water`, `building` "
      "names, roads), ODbL - outlines and building names.\n"
      "* NYC Landmarks Preservation Commission historic districts, NYC Parks properties, NYC building footprints "
      "(NYC Open Data, public).\n"
      "* USGS Historical Topographic Map Collection, public domain - 1:24,000 and 1:62,500 quadrangles read through "
      "the TNM Access API listing (`data/raw/natural/usgs/tnm_all.json`) and "
      "`https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/`.\n")
    (S / "README.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("README.md", len(L), "blocks;", f"start text {n_text}, start est {n_start_est}, end est {n_end_est}, outline est {n_out_est}")


if __name__ == "__main__":
    main()
