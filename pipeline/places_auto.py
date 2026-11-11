"""Labels for the outer counties' villages, hamlets and neighbourhoods.

data/tables/places_outer.csv holds 230 researched towns and cities for 19 counties: zoomed in,
most of the map out there carried no name at all. This stage adds every named place of
OpenStreetMap (Overture's divisions theme: localities and neighbourhoods, the position of the
place node) that the researched tables do not already hold:

  name, position   real (OpenStreetMap)
  from which year  estimated: the year a twentieth of today's buildings within 600 m (at
                   least five; 1,500 m in open country) stand on this map - a name appears
                   when there is a place to name; fewer than five buildings: left out

-> data/tables/places_outer_auto.csv (same columns as places_outer.csv; committed: the viewer
reads the tables at build time). Run after county_buildings.py outer; the divisions extract is
fetched by data/tables/tools/recentre_places.py fetch.
"""
from __future__ import annotations

import re

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from common import INTERIM, RAW, TABLES, log

RELEASE = "2026-10-21.0"
OUTER_FIPS = ["36059", "36103", "36079", "36071", "36027", "36111", "36105",
              "34023", "34025", "34029", "34035", "34027", "34037", "34019", "34021",
              "09120", "09190", "09170", "42103"]
NEAR_M, FAR_M, NEED = 600.0, 1500.0, 5
SAME_NAME_M = 2500.0


def key(name):
    s = str(name).lower()
    s = re.sub(r"\b(township|borough|village|city|town) of\b|\b(township|borough|village|cdp)\b", "", s)
    return re.sub(r"[^a-z0-9]", "", s)


def xy(lon, lat):
    return np.c_[np.asarray(lon, float) * 111320.0 * np.cos(np.radians(41.0)), np.asarray(lat, float) * 110540.0]


def main():
    d = pd.read_parquet(RAW / "overture" / RELEASE / "outer_divisions.parquet")
    d = d[d.subtype.isin(["locality", "neighborhood"]) & d.name.notna()].copy()
    d = d[~d.name.str.contains(r"Historic District|Census Designated|\(historical\)", regex=True)]   # outlines, not places
    d = d[~(((d.lat * 100).round(6) % 1 == 0) & ((d.lon * 100).round(6) % 1 == 0))]       # stand-in points
    cty = gpd.read_file(RAW / "tiger" / "tl_2024_us_county.zip")
    cty = cty[cty.GEOID.isin(OUTER_FIPS)][["GEOID", "NAME", "geometry"]].to_crs(4326)
    g = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d.lon, d.lat), crs=4326)
    g = gpd.sjoin(g, cty, predicate="within", how="inner").drop(columns="index_right")
    log(f"places auto: {len(d)} named places in the box, {len(g)} in the outer counties")
    # not the ones the researched tables hold
    known = pd.concat([pd.read_csv(TABLES / f) for f in ("places.csv", "places_counties.csv", "places_outer.csv")], ignore_index=True)
    known = known[pd.to_numeric(known.lon, errors="coerce").notna()]
    kt = cKDTree(xy(known.lon, known.lat))
    kk = known.name.map(key).values
    gk = g.name.map(key).values
    P = xy(g.lon, g.lat)
    dup = np.zeros(len(g), bool)
    for i, near in enumerate(kt.query_ball_point(P, SAME_NAME_M)):
        dup[i] = any(kk[j] == gk[i] for j in near)
    g = g[~dup].copy()
    # one row per name and spot: a locality before a neighbourhood of the same name
    g["k"] = g.name.map(key)
    g = g.sort_values(["k", "subtype"]).reset_index(drop=True)
    P = xy(g.lon, g.lat)
    t = cKDTree(P)
    keep = np.ones(len(g), bool)
    for i, near in enumerate(t.query_ball_point(P, 1000.0)):
        if keep[i]:
            for j in near:
                if j > i and g.k.values[j] == g.k.values[i]:
                    keep[j] = False
    g = g[keep].reset_index(drop=True)
    # the year a name appears: the fifth building around
    import duckdb
    b = duckdb.connect().execute(f"select lon, lat, start_year from '{INTERIM / 'county_points_outer.parquet'}' where end_year > 9000").df()
    bt = cKDTree(xy(b.lon, b.lat))
    sy = b.start_year.values
    P = xy(g.lon, g.lat)
    year = np.full(len(g), np.nan)
    for r in (NEAR_M, FAR_M):
        todo = np.flatnonzero(np.isnan(year))
        for i, near in zip(todo, bt.query_ball_point(P[todo], r)):
            if len(near) >= NEED:
                # (in a dense district the fifth building is an outlier: a twentieth of them)
                k = max(NEED - 1, int(0.05 * len(near)))
                year[i] = np.partition(sy[near], k)[k]
    g = g[np.isfinite(year)].copy()
    year = year[np.isfinite(year)]
    cls = g["class"].fillna("").values
    tier = np.where(g.subtype.values == "neighborhood", "neighborhood", np.where(np.isin(cls, ["city", "town"]), "town", "hamlet"))
    out = pd.DataFrame({
        "id": "auto_" + g.id.astype(str).str.replace("-", "").str[:10],
        "name": g.name.values, "tier": tier, "lat": g.lat.round(5).values, "lon": g.lon.round(5).values,
        "year_start": np.floor(year).astype(int), "year_end": 9999, "replaced_by": "", "county": g.NAME.values,
        "note": "name and position: OpenStreetMap's place point; shown from the year the first twentieth of the buildings around stand on this map (estimated)",
        "source_url": "https://docs.overturemaps.org/guides/divisions/"})
    out = out.drop_duplicates("id").sort_values(["county", "name"])
    out.to_csv(TABLES / "places_outer_auto.csv", index=False)
    log(f"places auto: {len(out)} labels -> places_outer_auto.csv; tiers {out.tier.value_counts().to_dict()}; "
        f"first shown, by half century: {(out.year_start // 50 * 50).value_counts().sort_index().to_dict()}")


if __name__ == "__main__":
    main()
