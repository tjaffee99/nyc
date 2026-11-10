"""Boroughs for the population counter.

Outlines: US Census TIGER/Line 2024 counties (the five boroughs), simplified to ~40 m.
Populations: data/tables/population.csv (year, area, population, source_url, note; area is
`nyc` for the five boroughs' area or a borough: manhattan, bronx, brooklyn, queens,
staten_island). Zoomed in, the viewer shows the borough under the centre of the map from
its first row on; otherwise the whole city.

Output: viewer/public/data/cities.json
  {"places": [], "counties": [{name, geoid, rings}], "pop": {"county:<name>": [[year, population], ...]},
   "region": [[year, population], ...], "region_label": "New York City"}
"""
from __future__ import annotations

import json

import geopandas as gpd
import numpy as np
import pandas as pd

from common import BORO_COUNTY, RAW, TABLES, VIEWER_DATA, log
from extent import POLY

AREAS = {"manhattan": "Manhattan", "bronx": "The Bronx", "brooklyn": "Brooklyn", "queens": "Queens",
         "staten_island": "Staten Island"}
NAMES = {"Manhattan": "Manhattan", "Bronx": "The Bronx", "Brooklyn": "Brooklyn", "Queens": "Queens",
         "Staten Island": "Staten Island"}


def rings_of(geom, tol=0.0004):
    g = geom.simplify(tol, preserve_topology=True)
    out = []
    for p in getattr(g, "geoms", [g]):
        if p.geom_type != "Polygon" or p.is_empty:
            continue
        out.append([[round(x, 5), round(y, 5)] for x, y in np.asarray(p.exterior.coords)[:, :2]])
    return out


def main():
    co = gpd.read_file(f"zip://{RAW / 'tiger' / 'tl_2024_us_county.zip'}")
    co = co[(co.STATEFP == "36") & co.COUNTYFP.isin(list(BORO_COUNTY))].to_crs(4326)
    counties = [{"name": NAMES[BORO_COUNTY[r.COUNTYFP]], "geoid": r.GEOID,
                 "rings": rings_of(r.geometry.intersection(POLY.buffer(0.02)))} for r in co.itertuples()]
    pop, region = {}, []
    p = TABLES / "population.csv"
    if p.exists():
        t = pd.read_csv(p)
        t["population"] = pd.to_numeric(t.population.astype(str).str.replace(",", ""), errors="coerce")
        t["year"] = pd.to_numeric(t.year, errors="coerce")
        t = t.dropna(subset=["population", "year"])
        for area, grp in t.groupby(t.area.astype(str).str.lower().str.strip()):
            series = sorted({float(y): float(v) for y, v in zip(grp.year, grp.population)}.items())
            if area == "nyc":
                region = series
            elif area in AREAS:
                pop[f"county:{AREAS[area]}"] = series
        log(f"cities: {len(region)} citywide points, boroughs {sorted(pop)}")
    else:
        log("cities: no data/tables/population.csv yet - outlines only")
    out = {"places": [], "counties": counties, "pop": pop, "region": region, "region_label": "New York City"}
    (VIEWER_DATA / "cities.json").write_text(json.dumps(out, separators=(",", ":")))
    log(f"cities: {len(counties)} boroughs -> cities.json ({(VIEWER_DATA / 'cities.json').stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
