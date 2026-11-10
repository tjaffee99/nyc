"""Tiny client for the USDA NRCS Soil Data Access (SDA) tabular service.
https://sdmdataaccess.sc.egov.usda.gov/  (public domain, US Government work)
usage: python sda.py "SELECT ..."   -> prints rows as TSV
"""
import json
import sys

import requests

URL = "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest"
UA = {"User-Agent": "NYCThroughTime-research/0.1"}


def query(sql, timeout=300):
    r = requests.post(URL, data={"query": sql, "format": "JSON+COLUMNNAME"}, headers=UA, timeout=timeout)
    if r.status_code != 200 or not r.text.lstrip().startswith("{"):
        raise RuntimeError(f"SDA error {r.status_code}: {r.text[:600]}")
    t = json.loads(r.text).get("Table", [])
    if not t:
        return [], []
    return t[0], t[1:]


if __name__ == "__main__":
    cols, rows = query(sys.argv[1])
    print("\t".join(cols))
    for row in rows:
        print("\t".join("" if v is None else str(v) for v in row))
