"""Shared helpers for pipeline stages.

Every stage is idempotent: it checks whether its outputs exist (and are newer
than its inputs where that matters) and skips work otherwise. Raw downloads in
data/raw are never modified in place.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
MANUAL = ROOT / "data" / "manual"
TABLES = ROOT / "data" / "tables"
VIEWER_DATA = ROOT / "viewer" / "public" / "data"

USER_AGENT = "NYCThroughTime-pipeline/0.1"

# Feature lifespans: end_year of a feature that still exists.
STILL_EXISTS = 9999
# The "present" for the slider.
CURRENT_YEAR = 2026

for d in (RAW, INTERIM, VIEWER_DATA):
    d.mkdir(parents=True, exist_ok=True)

OVERTURE_RELEASE = "2026-10-21.0"

# The map: the five boroughs of New York City. One box (lon_min, lat_min, lon_max, lat_max)
# for the terrain grids and every bounding-box download; the outline itself is extent.py.
NYC_BBOX = (-74.29, 40.47, -73.67, 40.94)
# The wider map: the city and the inner ring of counties around it (those for which real
# construction years exist; see CLAUDE.md "Counties"). One box for the region terrain grid
# and the region extracts; the 29 m detail grid stays on NYC_BBOX.
REGION_BBOX = (-74.52, 40.47, -73.40, 41.38)
# state + county FIPS -> name (candidates; extent.py keeps the ones that were built)
REGION_COUNTIES = {"34017": "Hudson", "34003": "Bergen", "34013": "Essex", "34039": "Union", "34031": "Passaic",
                   "36119": "Westchester", "36059": "Nassau", "36087": "Rockland"}
# year the slider starts: Hudson's Half Moon enters the harbour
YEAR_MIN = 1609
# metric CRS for all distance / area work
NYC_CRS = "EPSG:32618"  # UTM 18N
BOROUGHS = {"1": "Manhattan", "2": "Bronx", "3": "Brooklyn", "4": "Queens", "5": "Staten Island"}
BORO_COUNTY = {"061": "Manhattan", "005": "Bronx", "047": "Brooklyn", "081": "Queens", "085": "Staten Island"}


def region_overture_files(typ: str = "building") -> list[Path]:
    """Overture extracts of the map box (download_overture.py), as a list so more batches
    (a wider metro area) can be added later."""
    d = RAW / "overture" / OVERTURE_RELEASE
    return [f for f in (d / f"{typ}.parquet",) if f.exists()]


def read_region_overture(typ: str = "building", columns=None, filters=None):
    """All batches as one pyarrow Table (pq.read_table arguments)."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    return pa.concat_tables([pq.read_table(f, columns=columns, filters=filters) for f in region_overture_files(typ)])


def read_region_overture_gdf(typ: str = "building", columns=None):
    """All batches as one GeoDataFrame (EPSG:4326)."""
    import geopandas as gpd
    import pandas as pd
    parts = [gpd.read_parquet(f, columns=columns) for f in region_overture_files(typ)]
    parts = [g if g.crs is not None else g.set_crs(4326) for g in parts]
    return parts[0] if len(parts) == 1 else gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), geometry="geometry", crs=parts[0].crs)


def log(*args):
    print(f"[{time.strftime('%H:%M:%S')}]", *args, file=sys.stderr, flush=True)


def session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    ca = "/root/.ccr/ca-bundle.crt"
    if os.path.exists(ca) and not os.environ.get("REQUESTS_CA_BUNDLE"):
        s.verify = ca
    return s


def get_with_retry(s: requests.Session, url: str, params=None, tries: int = 5, **kw):
    delay = 2.0
    for attempt in range(tries):
        try:
            r = s.get(url, params=params, timeout=300, **kw)
            if r.status_code == 200:
                return r
            log(f"HTTP {r.status_code} for {url} (attempt {attempt + 1})")
        except requests.RequestException as e:  # network hiccup
            log(f"error {e!r} for {url} (attempt {attempt + 1})")
        time.sleep(delay)
        delay *= 2
    raise RuntimeError(f"failed to fetch {url}")


def socrata_pages(dataset: str, out_dir: Path, select: str | None = None,
                  where: str | None = None, order: str = ":id",
                  page_size: int = 50000, fmt: str = "json") -> list[Path]:
    """Download a Socrata dataset page by page into out_dir/page-XXXX.<fmt>.

    Pages already on disk are skipped, so an interrupted download resumes.
    A `_complete` marker is written when the last (short) page has arrived.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    marker = out_dir / "_complete"
    if marker.exists():
        return sorted(out_dir.glob(f"page-*.{fmt}"))
    s = session()
    base = f"https://data.sf.gov/resource/{dataset}.{fmt}"
    page = 0
    while True:
        path = out_dir / f"page-{page:04d}.{fmt}"
        if path.exists():
            n = _count(path, fmt)
        else:
            params = {"$limit": page_size, "$offset": page * page_size, "$order": order}
            if select:
                params["$select"] = select
            if where:
                params["$where"] = where
            r = get_with_retry(s, base, params=params)
            tmp = path.with_suffix(".part")
            tmp.write_bytes(r.content)
            n = _count(tmp, fmt)
            tmp.rename(path)
            log(f"{dataset}: page {page} -> {n} rows")
        if n < page_size:
            break
        page += 1
    marker.write_text(time.strftime("%Y-%m-%dT%H:%M:%S"))
    return sorted(out_dir.glob(f"page-*.{fmt}"))


def _count(path: Path, fmt: str) -> int:
    data = json.loads(path.read_bytes())
    if fmt == "geojson":
        return len(data["features"])
    return len(data)


def download_file(url: str, path: Path) -> Path:
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    s = session()
    log(f"downloading {url}")
    r = get_with_retry(s, url, stream=False)
    tmp = path.with_suffix(path.suffix + ".part")
    tmp.write_bytes(r.content)
    tmp.rename(path)
    return path
