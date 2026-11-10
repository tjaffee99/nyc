"""Run the edition dating (date_editions.py) over the sites and write

  data/interim/sites/editions/<site>.csv      every footprint x edition (state, score)
  data/manual/sites/edition_brackets.csv      one row per footprint with a usable bracket

  python -I tools/run_editions.py [site_id ...]      (default: the sites in RUN below)
  python -I tools/run_editions.py --rebracket        (re-derive the brackets from the saved readings)

A bracket becomes a row of known_building_dates.sites.csv (build_buildings.py) only where the
built file's year is an estimate, or an assessor year stamped on five or more buildings of the
site (the lot's year, not the building's), and never against an LPC date.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from shapely.geometry import shape

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import date_editions as D  # noqa: E402
import geom as G  # noqa: E402

OUTD = G.ROOT / "data" / "interim" / "sites" / "editions"
OUTD.mkdir(parents=True, exist_ok=True)
# site feature id -> founding year used as the lower bound (None: no bound)
RUN = {
    "rikers_island_jails": 1932, "fort_tilden": 1917, "fort_wadsworth": 1806, "fort_hamilton": 1825, "hart_island": 1868,
    "north_brother_island": 1885, "sailors_snug_harbor": 1831, "creedmoor_state_hospital": 1912,
    "brooklyn_navy_yard": 1801, "brooklyn_naval_hospital": 1838, "randalls_island_institutions": 1845,
    "manhattan_state_hospital": 1847, "kings_county_hospital": 1831, "long_island_state_hospital": 1855,
    "bronx_state_hospital": 1963, "bronx_municipal_hospital": 1955, "nas_new_york": 1928, "miller_field": 1919,
    "fort_totten": 1862, "governors_island_army_1904": 1794, "willowbrook_state_school": 1942,
    "fresh_kills_landfill": 1948, "coney_island_yard": 1926, "morris_park_shops": 1889, "sunnyside_yard": 1910,
    "yard_207th_street": 1932, "jamaica_yard": 1936, "corona_yard": 1928, "hunts_point_produce_market": 1967,
    "hunts_point_meat_market": 1974, "ravenswood_station": 1963, "east_river_station": 1926, "poletti_power_project": 1977,
    "seaview_hospital": 1905, "new_york_city_farm_colony": 1829, "fort_schuyler": 1833, "welfare_island": 1828,
    "bush_terminal": 1895, "brooklyn_army_base": 1919, "hillside_facility": 1991, "concourse_yard": 1933,
    "pitkin_yard": 1948, "livonia_yard": 1923, "canarsie_yard": 1917, "yard_239th_street": 1916, "unionport_yard": 1918,
    "east_new_york_yard": 1885, "kingsbridge_veterans_hospital": 1922, "naval_station_new_york": 1990,
    "harlem_river_yard": None, "ellis_island_station": 1892, "fort_wood": 1806,
}


def run(ids):
    d = json.loads((HERE.parent / "sites.geojson").read_text())
    feats = {f["properties"]["id"]: f for f in d["features"]}
    allrows = []
    for sid in ids:
        g = shape(feats[sid]["geometry"])
        founded = RUN.get(sid)
        fp = G.footprints(g, min_area=120.0)
        if not len(fp):
            continue
        print(f"== {sid}: {len(fp)} footprints", flush=True)
        if REBRACKET and (OUTD / f"{sid}.csv").exists():
            pres = pd.read_csv(OUTD / f"{sid}.csv")      # the sheets as read last time (same footprint order)
        else:
            pres = D.presence(fp, log=lambda *a: None)
            if not len(pres):
                continue
            pres.to_csv(OUTD / f"{sid}.csv", index=False)
        br = D.bracket(pres, founded)
        states = (pres[pres.scale <= 31680].sort_values("year").groupby("fi")
                  .apply(lambda t: " ".join(f"{int(y)}:{s[0]}" for y, s in zip(t.year, t.state))))
        bl = G.built(g)
        cur = {int(b): (y, c, s, r) for b, y, c, s, r in zip(bl.bin.fillna(0), bl.start_year, bl.year_confidence,
                                                             bl.year_src, bl.raw_year)}
        stamped = bl.raw_year.round().value_counts()
        stamped = set(stamped[stamped >= 5].index)
        for fi, r in br.iterrows():
            b = int(fp.bin[fi]) if pd.notna(fp.bin[fi]) else 0
            y, c, s, raw = cur.get(b, (np.nan, "", "", np.nan))
            allrows.append(dict(site=sid, bin=b, lon=round(float(fp.geometry[fi].representative_point().x), 6),
                                lat=round(float(fp.geometry[fi].representative_point().y), 6),
                                area_m2=round(float(fp.area_m2[fi])), built_year=None if pd.isna(y) else round(float(y), 1),
                                built_conf=c, built_src=s, stamped=bool(raw in stamped), last_absent=r.last_absent,
                                first_drawn=r.first_drawn, est_start=r.est_start, evidence=r.evidence,
                                sheets=states.get(fi, "")))
        n2 = sum(1 for x in allrows if x["site"] == sid and pd.notna(x["last_absent"]) and pd.notna(x["first_drawn"]))
        print(f"   two-sided brackets: {n2}", flush=True)
    return pd.DataFrame(allrows)


REBRACKET = "--rebracket" in sys.argv

if __name__ == "__main__":
    sys.argv = [a for a in sys.argv if a != "--rebracket"]
    ids = sys.argv[1:] or list(RUN)
    t = run(ids)
    out = HERE.parent / "edition_brackets.csv"
    if sys.argv[1:] and out.exists():
        old = pd.read_csv(out)
        t = pd.concat([old[~old.site.isin(ids)], t])
    t.to_csv(out, index=False)
    print(len(t), "rows ->", out)
