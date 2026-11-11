"""Real construction years for the outer counties that the State's parcel polygons do not carry.

    python county_years.py download dutchess|suffolk|nassau   NYS Tax Parcel Centroid Points -> data/raw/county_years/centroids_<county>/
    python county_years.py apply dutchess                     match the points to the county file's footprints, write year_raw

Source: NYS ITS Geospatial Services, "NYS Tax Parcel Centroid Points" (statewide, every county, 2025 roll),
https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Tax_Parcel_Centroid_Points/FeatureServer/0 .
Notes: data/research/county_years.md. Resumable; one process; small memory.
"""
from __future__ import annotations

import gzip
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import requests

from common import RAW, log

URL = "https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Tax_Parcel_Centroid_Points/FeatureServer/0/query"
FIELDS = "OBJECTID,COUNTY_NAME,MUNI_NAME,CITYTOWN_NAME,SWIS,PRINT_KEY,PROP_CLASS,YR_BLT,SQFT_LIVING,USED_AS_CODE,SQ_FT,ACRES"
CACHE = RAW / "county_years"
UA = "NYCThroughTime-research/0.1"
PAGE = 1000


def post(params, tries=6, timeout=200):
    for k in range(tries):
        try:
            r = requests.post(URL, data=params, headers={"User-Agent": UA}, timeout=timeout)
            if r.status_code == 200:
                d = r.json()
                if "error" not in d:
                    return d
                err = d["error"]
            else:
                err = f"HTTP {r.status_code}"
        except (requests.RequestException, ValueError) as e:
            err = repr(e)
        log(f"  retry {k + 1}: {err}")
        time.sleep(5 * (k + 1))
    raise RuntimeError(err)


def object_ids(county, where=None):
    f = CACHE / f"ids_{county}.json"
    if f.exists() and f.stat().st_size > 1000:
        return json.loads(f.read_text())["objectIds"]
    d = post({"where": where or f"COUNTY_NAME='{county.title()}'", "returnIdsOnly": "true", "f": "json"}, timeout=290)
    f.write_text(json.dumps(d))
    return d["objectIds"]


def download(county, where=None, ids=None):
    ids = sorted(ids if ids is not None else object_ids(county, where))
    d = CACHE / f"centroids_{county}"
    d.mkdir(parents=True, exist_ok=True)
    pages = [ids[i:i + PAGE] for i in range(0, len(ids), PAGE)]
    todo = [(i, p) for i, p in enumerate(pages) if not (d / f"p{i:05d}.json.gz").exists()]
    log(f"{county}: {len(ids)} points, {len(todo)} of {len(pages)} pages to fetch")

    def one(a):
        i, p = a
        r = post({"objectIds": ",".join(map(str, p)), "outFields": FIELDS, "outSR": 4326, "geometryPrecision": 6, "f": "json"})
        tmp = d / f"p{i:05d}.part"
        with gzip.open(tmp, "wt") as fh:
            json.dump(r["features"], fh)
        tmp.rename(d / f"p{i:05d}.json.gz")
        return len(r["features"])
    n = 0
    with ThreadPoolExecutor(3) as ex:
        for j, k in enumerate(ex.map(one, todo)):
            n += k
            if j % 10 == 9:
                log(f"  {county}: {j + 1}/{len(todo)} pages, {n} points")


def main(argv):
    if argv and argv[0] == "download":
        for c in argv[1:]:
            download(c)


if __name__ == "__main__":
    main(sys.argv[1:])
