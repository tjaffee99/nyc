"""Fetch the raw inputs of the eight counties' natural layer into data/raw/natural_counties/ (cached).
 - SSURGO survey areas NJ003 Bergen, NJ013 Essex, NJ017 Hudson, NJ031 Passaic, NJ039 Union, NY059 Nassau,
   NY087 Rockland, NY119 Westchester from Web Soil Survey (file date = the area's "saverest" in Soil Data Access)
 - sixteen USGS Historical Topographic Map Collection GeoTIFFs (15-minute sheets, earliest print of each quad);
   the six sheets the city's layer already fetched are copied from data/raw/natural/usgs when present.
Both are US Government works (public domain).
"""
import os
import shutil
import zipfile

import requests

import sda

ROOT = "/home/user/nyc/data/raw/natural_counties"
CITY = "/home/user/nyc/data/raw/natural/usgs"
UA = {"User-Agent": "NYCThroughTime-research/0.1"}
USGS = "https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/"
AREAS = ["NJ003", "NJ013", "NJ017", "NJ031", "NJ039", "NY059", "NY087", "NY119"]
SHEETS = [
    "NY/NJ_Harlem_472515_1891_62500_geo.tif", "NY/NY_Brooklyn_123118_1897_62500_geo.tif",
    "NY/NJ_Staten%20Island_255388_1898_62500_geo.tif", "NJ/NJ_Paterson_255310_1888_62500_geo.tif",
    "NY/NY_Hempstead_129886_1897_62500_geo.tif", "NY/NY_Oyster%20Bay_136363_1897_62500_geo.tif",
    "NY/NY_Babylon_123382_1901_62500_geo.tif", "NY/NY_Northport_128788_1901_62500_geo.tif",
    "NY/NY_Tarrytown_144340_1892_62500_geo.tif", "CT/NY_Stamford_144254_1892_62500_geo.tif",
    "NY/NY_West%20Point_144447_1892_62500_geo.tif", "NY/NY_Carmel_140433_1892_62500_geo.tif",
    "NY/NJ_Ramapo_148251_1891_62500_geo.tif", "NY/NY_Greenwood%20Lake_255191_1891_62500_geo.tif",
    "NJ/NJ_Morristown_255268_1888_62500_geo.tif", "NJ/NJ_Plainfield_255320_1888_62500_geo.tif",
]


def get(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    r = requests.get(url, headers=UA, timeout=900)
    r.raise_for_status()
    open(path, "wb").write(r.content)
    print("fetched", path, len(r.content), flush=True)


def main():
    syms = ",".join(f"'{a}'" for a in AREAS)
    cols, rows = sda.query(f"SELECT areasymbol, CONVERT(varchar, saverest, 23) AS d FROM sacatalog WHERE areasymbol IN ({syms})")
    for sym, d in rows:
        z = f"{ROOT}/ssurgo/wss_SSA_{sym}_{d}.zip"
        get(f"https://websoilsurvey.sc.egov.usda.gov/DSD/Download/Cache/SSA/wss_SSA_{sym}_%5B{d}%5D.zip", z)
        out = z[:-4]
        if not os.path.isdir(out):
            zipfile.ZipFile(z).extractall(out)
    for s in SHEETS:
        name = s.split("/")[-1].replace("%20", "_")
        dst = f"{ROOT}/usgs/{name}"
        if not os.path.exists(dst) and os.path.exists(f"{CITY}/{name}"):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(f"{CITY}/{name}", dst)
            continue
        try:
            get(USGS + s, dst)
        except Exception as e:  # one missing sheet must not stop the rest
            print("FAILED", s, e, flush=True)


if __name__ == "__main__":
    main()
