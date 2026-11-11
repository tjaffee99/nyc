"""Connecticut's historic resources inventory (ConnCRIS) as evidence for construction years.

The towns' assessors write a placeholder for old buildings (New Haven: 1900 for 8,264 of
29,261 buildings, 1920 for 2,777, 1910 for 1,719). The State Historic Preservation Office's
inventory - "CT Public Above Ground Resources", a public point layer - carries a construction
date (`ConstructD`: "1912", "1910 CIRCA") for the buildings its surveys covered.

  python conncris.py fetch    -> data/raw/conncris/<town>.json (one request per 2,000 points)
  python conncris.py build    -> data/interim/counties/ct_<region>_inventory.parquet
                                 (id, year_inv, circa, n_points, name_inv)

`county_buildings.load()` reads the side file: a footprint whose assessor year is a
placeholder or missing takes the inventory's year - `year_hist` when it is a plain year
(`exact`, source `historic_register`), `year_hist_ca` when it is "circa" or a round decade
(`estimated`, spread over six years). A recorded assessor year is never replaced: where both
exist they agree within two years only two times in three (the inventory's points sometimes
sit on the neighbour's building, and its own years are rounded too).

Rules: a point dates the footprint it lies in; several points in one footprint must agree
within five years (the earliest is taken), otherwise the footprint is left alone.

Licence of the layer: CC BY-NC-ND (Connecticut SHPO). Used with attribution on a
non-commercial map by the owner's decision of 2026-11-11 (CLAUDE.md, decision 52); only the
year enters the map, the layer itself is not republished.
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

from common import INTERIM, RAW, log

URL = "https://services3.arcgis.com/3FL1kr7L4LvwA2Kb/arcgis/rest/services/CT_Public_Above_Ground_Resources/FeatureServer/1/query"
UA = "NYCThroughTime-research/0.1"
OUT = INTERIM / "counties"
CACHE = RAW / "conncris"
REGIONS = ["ct_greater_bridgeport", "ct_western_connecticut", "ct_south_central_connecticut"]
AGREE = 5.0


def munis(stem):
    import duckdb
    return [r[0] for r in duckdb.connect().execute(f"select distinct muni from '{OUT / (stem + '.parquet')}' where muni is not null order by 1").fetchall()]


def fetch_one(muni):
    rows, off = [], 0
    while True:
        q = {"where": f"MUNICIP2='{muni}'", "outFields": "UNIQUE_ID,NAME,ConstructD", "outSR": 4326, "returnGeometry": "true",
             "resultOffset": off, "resultRecordCount": 2000, "orderByFields": "OBJECTID", "f": "json"}
        req = urllib.request.Request(URL + "?" + urllib.parse.urlencode(q), headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as r:
            j = json.loads(r.read().decode())
        f = j.get("features", [])
        rows += [{"id": x["attributes"].get("UNIQUE_ID"), "name": x["attributes"].get("NAME"), "d": x["attributes"].get("ConstructD"),
                  "x": x["geometry"]["x"], "y": x["geometry"]["y"]} for x in f if x.get("geometry")]
        off += len(f)
        if not f or not j.get("exceededTransferLimit"):
            return rows
        time.sleep(0.5)


def fetch():
    CACHE.mkdir(parents=True, exist_ok=True)
    total = 0
    for stem in REGIONS:
        for m in munis(stem):
            p = CACHE / f"{m.replace(' ', '_')}.json"
            if not p.exists():
                rows = fetch_one(m)
                p.write_text(json.dumps(rows))
                time.sleep(0.5)
            n = len(json.loads(p.read_text()))
            total += n
            log(f"conncris: {m}: {n} points")
    log(f"conncris: {total} points in the map's Connecticut towns")


def build():
    for stem in REGIONS:
        g = gpd.read_parquet(OUT / f"{stem}.parquet", columns=["id", "muni", "year_raw", "heap", "geometry"])
        pts = []
        for m in munis(stem):
            p = CACHE / f"{m.replace(' ', '_')}.json"
            if p.exists():
                pts += json.loads(p.read_text())
        t = pd.DataFrame(pts)
        t["yr"] = pd.to_numeric(t.d.fillna("").astype(str).str.extract(r"^\s*(\d{4})")[0], errors="coerce")
        t = t[t.yr.between(1620, 2026)].reset_index(drop=True)
        circa = t.d.astype(str).str.upper().str.contains("CIRCA|C\\.|CA\\.|ABOUT|\\?") | (t.yr % 10 == 0)
        tree = shapely.STRtree(g.geometry.values)
        qi, gi = tree.query(shapely.points(t.x.values, t.y.values), predicate="within")
        j = pd.DataFrame({"fi": gi, "yr": t.yr.values[qi], "circa": circa.values[qi], "name": t.name.values[qi]})
        a = j.groupby("fi").agg(lo=("yr", "min"), hi=("yr", "max"), n=("yr", "size"), circa=("circa", "max"),
                                name=("name", lambda s: "; ".join(sorted({str(v) for v in s if isinstance(v, str) and v.strip()}))[:120]))
        ok = a[(a.hi - a.lo) <= AGREE]
        out = pd.DataFrame({"id": g["id"].values[ok.index.values], "year_inv": ok.lo.values.astype(float), "circa": ok.circa.values.astype(bool),
                            "n_points": ok.n.values, "name_inv": ok.name.values})
        out.to_parquet(OUT / f"{stem}_inventory.parquet", index=False)
        raw = pd.to_numeric(g.year_raw, errors="coerce").values
        need = (g.heap.fillna(False).astype(bool).values | ~np.isfinite(raw))[ok.index.values]
        both = np.isfinite(raw[ok.index.values]) & ~g.heap.fillna(False).astype(bool).values[ok.index.values] & ~ok.circa.values
        agree = float((np.abs(raw[ok.index.values][both] - ok.lo.values[both]) <= 2).mean()) if both.any() else float("nan")
        log(f"conncris: {stem}: {len(t)} dated points, {len(a)} footprints hold one, {len(ok)} with agreeing dates; "
            f"{int(need.sum())} of them have a placeholder or no assessor year ({int((need & ~ok.circa.values).sum())} plain years, "
            f"{int((need & ok.circa.values).sum())} circa); where both are recorded they agree within 2 years in {agree:.0%}")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "build"
    {"fetch": fetch, "build": build}[what]()
