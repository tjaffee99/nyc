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

from common import INTERIM, BORO_COUNTY, RAW, TABLES, VIEWER_DATA, log
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


OUTER_AREAS = {"fairfield_ct": ["Greater Bridgeport", "Western Connecticut"], "new_haven_ct": ["South Central Connecticut"]}


def main():
    import re
    from extent import map_counties
    extra = map_counties()   # {fips: name} of the counties around the city that are on the map
    allco = gpd.read_file(f"zip://{RAW / 'tiger' / 'tl_2024_us_county.zip'}")
    co = allco[(allco.STATEFP == "36") & allco.COUNTYFP.isin(list(BORO_COUNTY))].to_crs(4326)
    counties = [{"name": NAMES[BORO_COUNTY[r.COUNTYFP]], "geoid": r.GEOID,
                 "rings": rings_of(r.geometry.intersection(POLY.buffer(0.02)))} for r in co.itertuples()]
    oc = allco[(allco.STATEFP + allco.COUNTYFP).isin(list(extra))].to_crs(4326)
    counties += [{"name": extra[r.STATEFP + r.COUNTYFP], "geoid": r.GEOID,
                  "rings": rings_of(r.geometry.intersection(POLY.buffer(0.02)), 0.0008)} for r in oc.itertuples()]
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
    pc = TABLES / "population_counties.csv"
    if pc.exists():
        t = pd.read_csv(pc)
        t["population"] = pd.to_numeric(t.population.astype(str).str.replace(",", ""), errors="coerce")
        t["year"] = pd.to_numeric(t.year, errors="coerce")
        t = t.dropna(subset=["population", "year"])
        for area, grp in t.groupby(t.area.astype(str).str.lower().str.strip()):
            name = area.replace("_", " ").title()
            if name in set(extra.values()):
                pop[f"county:{name}"] = sorted({float(y): float(v) for y, v in zip(grp.year, grp.population)}.items())
    else:
        log("cities: no data/tables/population.csv yet - outlines only")
    # the outer counties (population_outer.csv): its area keys carry the state where a name
    # repeats, and Connecticut's series are of the old counties (one series, two planning regions)
    po = TABLES / "population_outer.csv"
    if po.exists():
        t = pd.read_csv(po)
        t["population"] = pd.to_numeric(t.population.astype(str).str.replace(",", ""), errors="coerce")
        t["year"] = pd.to_numeric(t.year, errors="coerce")
        t = t.dropna(subset=["population", "year"])
        names = set(extra.values())
        for area, grp in t.groupby(t.area.astype(str).str.lower().str.strip()):
            series = sorted({float(y): float(v) for y, v in zip(grp.year, grp.population)}.items())
            for name in OUTER_AREAS.get(area, [re.sub(r"_(ny|nj|ct|pa)$", "", area).replace("_", " ").title()]):
                if name in names:
                    pop[f"county:{name}"] = series
    # ---- the whole metropolitan area (the counter's figure when the map is zoomed all the way
    # out): the five boroughs and every county on the map, at the census years from 1790. A
    # county created later was counted inside its parent before (Nassau in Queens, Mercer in
    # Hunterdon and Middlesex, Ocean in Monmouth, Putnam in Dutchess, Sullivan in Ulster), so
    # the sum of the series that exist in a year is the area's count (a little short before
    # 1840: the part of Mercer that came from Burlington). Connecticut's two Fairfield regions
    # share one series: counted once.
    def at(series, y):
        if not series or y < series[0][0]:
            return 0.0
        ys = [q[0] for q in series]
        return float(np.interp(y, ys, [q[1] for q in series]))

    uniq = {tuple(map(tuple, v)) for k, v in pop.items() if k.startswith("county:")}
    last = max((sv[-1][0] for sv in uniq), default=2020)
    metro = [[float(y), round(sum(at(list(sv), y) for sv in uniq))] for y in list(range(1790, 2021, 10)) + ([last] if last > 2020 else [])]
    # ---- the towns (town_population.py: the municipalities' outlines and census counts):
    # the counter names the town under the middle of the map when zoomed in
    places = []
    tp, tt = INTERIM / "towns" / "towns.parquet", TABLES / "population_towns.csv"
    if tp.exists() and tt.exists():
        towns = gpd.read_parquet(tp).to_crs(4326)
        t = pd.read_csv(tt, dtype={"geoid": str})
        t["population"] = pd.to_numeric(t.population, errors="coerce")
        t["year"] = pd.to_numeric(t.year, errors="coerce")
        t = t.dropna(subset=["population", "year"])
        series = {g: sorted({float(y): float(v) for y, v in zip(grp.year, grp.population)}.items()) for g, grp in t.groupby("geoid")}
        keep = POLY.buffer(0.02)
        for r in towns.itertuples():
            sv = series.get(str(r.geoid))
            if not sv or len(sv) < 3 or r.geometry is None or r.geometry.is_empty:
                continue
            rr = rings_of(r.geometry.intersection(keep), 0.0008)
            if not rr:
                continue
            places.append({"name": str(r.name), "geoid": str(r.geoid), "rings": rr})
            pop[str(r.geoid)] = sv
        log(f"cities: {len(places)} towns with a census series of their own")
    out = {"places": places, "counties": counties, "pop": pop, "region": region, "region_label": "New York City",
           "metro": metro, "metro_label": f"New York metropolitan area ({len(counties)} counties)"}
    (VIEWER_DATA / "cities.json").write_text(json.dumps(out, separators=(",", ":")))
    log(f"cities: {len(counties)} boroughs -> cities.json ({(VIEWER_DATA / 'cities.json').stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
