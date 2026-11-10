"""Checks on the OHM building files (run from anywhere):  .venv/bin/python data/manual/ohm/tools/check_outputs.py

  a. both committed GeoJSON files parse; ids unique; geometry valid; no start >= end
  b. overlap_today recomputed independently (UTM 18N areas, union of today's footprints) for a random sample
  c. how the OHM copy of the NYPL "layer 861 / 1854" import relates to the project's own NYPL Building
     Inspector download (data/raw/nypl/building-inspector.objects.ndjson, which has no layer 861)
"""
import json
import sys
from collections import Counter
from pathlib import Path

import duckdb
import geopandas as gpd
import numpy as np
import shapely

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "data" / "manual" / "ohm"
FOOT = ROOT / "data" / "interim" / "nyc_footprints_raw.parquet"
NDJSON = ROOT / "data" / "raw" / "nypl" / "building-inspector.objects.ndjson"
UTM = "EPSG:32618"

main = gpd.read_file(OUT / "nyc_buildings.geojson")
nypl = gpd.read_file(OUT / "nyc_buildings_nypl1854.geojson")
for name, g in (("nyc_buildings", main), ("nyc_buildings_nypl1854", nypl)):
    bad = (g.start_year.notna() & g.end_year.notna() & (g.start_year >= g.end_year)).sum()
    print(f"a. {name}: {len(g)} features, {g.ohm_id.nunique()} ids, geometry null {g.geometry.isna().sum()}, "
          f"invalid {(~g.geometry.is_valid).sum()}, types {dict(Counter(g.geom_type))}, start>=end {bad}, "
          f"extinct {int(g.extinct.sum())}, columns {len(g.columns)}")
print("a. ids shared by the two files:", len(set(main.ohm_id) & set(nypl.ohm_id)))
x = main[main.start_year.notna() & main.end_year.notna() & (main.start_year >= main.end_year)]
print("a. start >= end in OHM itself:", [(r.ohm_id, r.name, r.start_raw, r.end_raw) for r in x.itertuples()])

# b. independent overlap check
rng = np.random.default_rng(7)
both = gpd.GeoDataFrame(np.concatenate([main[main.extinct & main.overlap_today.notna()].sample(150, random_state=1).values,
                                         nypl[nypl.extinct].sample(150, random_state=1).values]),
                        columns=main.columns, crs=4326).set_geometry("geometry")
con = duckdb.connect()
diffs = []
for r in both.itertuples():
    w, s, e, n = r.geometry.bounds
    fp = con.execute(f"SELECT geometry FROM read_parquet('{FOOT}') WHERE lon BETWEEN {w - .005} AND {e + .005} "
                     f"AND lat BETWEEN {s - .005} AND {n + .005}").fetchall()
    fg = gpd.GeoSeries(shapely.from_wkb([bytes(x[0]) for x in fp]), crs=4326).to_crs(UTM) if fp else gpd.GeoSeries([], crs=UTM)
    g = gpd.GeoSeries([r.geometry], crs=4326).to_crs(UTM).iloc[0]
    hit = fg[fg.intersects(g)]
    frac = g.intersection(shapely.union_all(shapely.make_valid(hit.values))).area / g.area if len(hit) else 0.0
    diffs.append(frac - float(r.overlap_today))
d = np.array(diffs)
print(f"b. overlap_today, 300 extinct sampled: max |stored - recomputed (UTM, union)| = {np.abs(d).max():.4f}, "
      f"mean {np.abs(d).mean():.5f}, over 0.02: {(np.abs(d) > 0.02).sum()}")

# c. NYPL layer 861 (OHM) against the project's NYPL download (layers 859 ...)
layers = Counter()
polys, lay = [], []
w, s, e, n = nypl.total_bounds
with open(NDJSON) as f:
    for line in f:
        if '"st:Building"' not in line:
            continue
        o = json.loads(line)
        layers[(o["data"].get("layerId"), o.get("validSince"))] += 1
        if (o.get("geometry") or {}).get("type") != "Polygon":
            continue
        c = o["geometry"]["coordinates"][0]
        if len(c) >= 4 and w <= c[0][0] <= e and s <= c[0][1] <= n:
            polys.append(shapely.Polygon(c))
            lay.append(o["data"].get("layerId"))
print("c. project NYPL download, buildings by (layerId, validSince):", dict(layers.most_common(12)))
polys = np.array(polys, dtype=object)
ok = shapely.is_valid(polys)
polys[~ok] = shapely.make_valid(polys[~ok])
tree = shapely.STRtree(polys)
samp = nypl.sample(6000, random_state=2).geometry.values
a, b = tree.query(samp, predicate="intersects")
inter = shapely.area(shapely.intersection(samp[a], polys[b]))
iou = inter / (shapely.area(samp[a]) + shapely.area(polys[b]) - inter)
best = np.zeros(len(samp))
np.maximum.at(best, a, iou)
print(f"c. of 6000 OHM 'layer 861 / 1854' footprints, inside their bbox the project's download has {len(polys)} "
      f"buildings; best IoU >= 0.9: {(best >= .9).mean():.3f}, >= 0.5: {(best >= .5).mean():.3f}, "
      f"no overlap at all: {(best == 0).mean():.3f}")
print("c. OHM layer-861 extent (w, s, e, n):", [round(float(x), 4) for x in nypl.total_bounds])
