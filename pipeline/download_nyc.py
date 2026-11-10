"""Stage: raw downloads for New York City (all public; see SOURCES.md for licences).

Each file is fetched once into data/raw/<group>/ and never modified in place.
Run `python download_nyc.py` (everything) or `python download_nyc.py <name> ...`.
"""
from __future__ import annotations

import sys
import time

from common import RAW, log, session

SODA = "https://data.cityofnewyork.us"

PLUTO_COLS = ("bbl,borough,block,lot,address,bldgclass,landuse,ownertype,ownername,lotarea,bldgarea,"
              "numbldgs,numfloors,unitsres,unitstotal,yearbuilt,yearalter1,yearalter2,histdist,landmark,"
              "latitude,longitude,proxcode,lotfront,bldgfront,bldgdepth,ext,lottype")

FILES = {
    # NYC OTI building footprints: outline, construction year, roof height (ft), ground elevation (ft), BIN, BBL
    "footprints": ("nyc/building_footprints.csv", f"{SODA}/api/views/5zhs-2jue/rows.csv?accessType=DOWNLOAD"),
    # DCP PLUTO: tax-lot year built, floors, class, alteration years
    "pluto": ("nyc/pluto_lots.csv", f"{SODA}/resource/64uk-42ks.csv?$select={PLUTO_COLS}&$limit=2000000&$order=bbl"),
    # LPC: per-building database of the landmarks and historic districts (construction date ranges, style, architect)
    "lpc_buildings": ("nyc/lpc_buildings.geojson", f"{SODA}/resource/gpmc-yuvp.geojson?$limit=100000"),
    "lpc_landmarks": ("nyc/lpc_individual_landmarks.geojson", f"{SODA}/resource/buis-pvji.geojson?$limit=100000"),
    "lpc_districts": ("nyc/lpc_historic_districts.geojson", f"{SODA}/resource/skyk-mpzq.geojson?$limit=100000"),
    # NYC Parks properties with acquisition dates
    "parks": ("nyc/parks_properties.geojson", f"{SODA}/resource/enfh-gkve.geojson?$limit=100000"),
    # NYPL Building Inspector: footprints read from the Perris fire-insurance atlases of the 1850s
    "building_inspector": ("nypl/building-inspector.objects.ndjson",
                           "http://spacetime-nypl-org.s3.amazonaws.com/datasets/building-inspector/building-inspector.objects.ndjson"),
    # MTA subway GTFS (stations, shapes)
    "gtfs_subway": ("mta/gtfs_subway.zip", "https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip"),
    # Census TIGER 2024 counties (borough outlines incl. their water) and places
    "tiger_county": ("tiger/tl_2024_us_county.zip", "https://www2.census.gov/geo/tiger/TIGER2024/COUNTY/tl_2024_us_county.zip"),
}


def fetch(name: str):
    rel, url = FILES[name]
    path = RAW / rel
    if path.exists() and path.stat().st_size > 0:
        log(f"{name}: cached ({path.stat().st_size / 1e6:.1f} MB)")
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    s = session()
    for attempt in range(5):
        try:
            t0 = time.time()
            with s.get(url, stream=True, timeout=600) as r:
                r.raise_for_status()
                n = 0
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
                        n += len(chunk)
            tmp.rename(path)
            log(f"{name}: {n / 1e6:.1f} MB in {time.time() - t0:.0f} s -> {path}")
            return path
        except Exception as e:  # noqa: BLE001 - network errors of any kind are retried
            log(f"{name}: {e!r} (attempt {attempt + 1})")
            time.sleep(4 * (attempt + 1))
    raise RuntimeError(f"failed to fetch {name}")


if __name__ == "__main__":
    for n in (sys.argv[1:] or FILES):
        fetch(n)
