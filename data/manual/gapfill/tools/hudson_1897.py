"""Built-up ground of Hudson County on the USGS 15-minute sheets of 1898 (surveyed about 1897).

The reading is the extents part's own (data/manual/extents/tools/usgs_extent.py: heavy black ink of the
built block fronts -> share within 80 m -> polygons), run on the two sheets that cover the county
(Staten Island, N.J.-N.Y., edition of 1898; Paterson, N.J.-N.Y., edition of 1898) and clipped to the
county instead of the boroughs. Nothing of that tool is changed.

    .venv/bin/python -I data/manual/gapfill/tools/hudson_1897.py     # -> data/manual/gapfill/hudson_builtup_1897.geojson
"""
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import shapely
import shapely.geometry as sg

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "data" / "manual" / "extents" / "tools"))
import classify            # noqa: E402
import streets as S        # noqa: E402
import usgs_extent as U    # noqa: E402

OUT = ROOT / "data" / "manual" / "gapfill" / "hudson_builtup_1897.geojson"
SHEETS = [s for s in U.SHEETS if s[0] in ("StatenIsland_1898.tif", "NJ_Paterson_255300_1898_62500_geo.tif")]
URL = {"StatenIsland_1898.tif": "https://ngmdb.usgs.gov/topoview/ (Staten Island, N.J.-N.Y., 1:62,500, edition of 1898)",
       "NJ_Paterson_255300_1898_62500_geo.tif": "https://ngmdb.usgs.gov/topoview/ (Paterson, N.J.-N.Y., 1:62,500, edition of 1898)"}


def main():
    g = gpd.read_file("zip://" + str(ROOT / "data/raw/tiger/tl_2024_us_county.zip"), where="STATEFP = '34' AND COUNTYFP = '017'")
    county = classify.to_local(g.geometry.iloc[0])
    feats = []
    for fn, year, q, title, *rest in SHEETS:
        env = U.quad_local(q).intersection(county.buffer(150))
        if env.is_empty:
            continue
        poly, _, _, _ = U.sheet_mask(fn, env, open_m=rest[0] if rest else 7.5)
        poly = poly.intersection(county.buffer(150)).buffer(0)
        print(f"{title}: built-up {poly.area / 1e4:.0f} ha in Hudson County", flush=True)
        for part in (poly.geoms if hasattr(poly, "geoms") else [poly]):
            if part.geom_type != "Polygon" or part.area < 1e4:
                continue
            ll = shapely.transform(part, lambda c: np.column_stack(S.lonlat(c[:, 0], c[:, 1])))
            feats.append({"type": "Feature", "geometry": sg.mapping(shapely.set_precision(ll, 1e-6)),
                          "properties": {"place": "hudson", "year": 1897, "kind": "built_up", "map": title, "map_url": URL[fn],
                                         "method": "heavy black ink of built block fronts, share within 80 m (extents/tools/usgs_extent.py)",
                                         "confidence": "low-medium", "area_ha": round(part.area / 1e4, 1),
                                         "licence": "public domain (USGS)"}})
    feats.sort(key=lambda f: -f["properties"]["area_ha"])
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    print(f"{OUT}: {len(feats)} polygons, {sum(f['properties']['area_ha'] for f in feats):.0f} ha")


if __name__ == "__main__":
    main()
