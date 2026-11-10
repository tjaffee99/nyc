"""Fetch the raw inputs into data/raw/natural/ (cached; nothing is re-downloaded if present).
 - SSURGO survey areas NY005 / NY047 / NY061 / NY081 / NY085 from Web Soil Survey (the date in the file name is the
   survey area's "saverest" date, read from Soil Data Access)
 - six USGS Historical Topographic Map Collection GeoTIFFs
 - the Library of Congress scan of the Viele 1865 map (IIIF, half size)
"""
import os
import zipfile

import requests

import sda

ROOT = "/home/user/nyc/data/raw/natural"
UA = {"User-Agent": "NYCThroughTime-research/0.1"}
USGS = "https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/"
SHEETS = ["NY/NJ_Harlem_472515_1891_62500_geo.tif", "NY/NY_Brooklyn_123118_1897_62500_geo.tif", "NY/NJ_Staten%20Island_255388_1898_62500_geo.tif",
          "NJ/NJ_Paterson_255310_1888_62500_geo.tif", "NY/NY_Hempstead_129886_1897_62500_geo.tif", "NY/NY_Oyster%20Bay_136363_1897_62500_geo.tif"]
VIELE = "https://tile.loc.gov/image-services/iiif/service:gmd:gmd380:g3804:g3804n:ct002003/full/pct:50/0/default.jpg"


def get(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    r = requests.get(url, headers=UA, timeout=900)
    r.raise_for_status()
    open(path, "wb").write(r.content)
    print("fetched", path, len(r.content))


def main():
    cols, rows = sda.query("SELECT areasymbol, CONVERT(varchar, saverest, 23) AS d FROM sacatalog WHERE areasymbol IN ('NY005','NY047','NY061','NY081','NY085')")
    for sym, d in rows:
        z = f"{ROOT}/ssurgo/wss_SSA_{sym}_{d}.zip"
        get(f"https://websoilsurvey.sc.egov.usda.gov/DSD/Download/Cache/SSA/wss_SSA_{sym}_%5B{d}%5D.zip", z)
        out = z[:-4]
        if not os.path.isdir(out):
            zipfile.ZipFile(z).extractall(out)
    for s in SHEETS:
        get(USGS + s, f"{ROOT}/usgs/" + s.split("/")[-1].replace("%20", "_"))
    get(VIELE, f"{ROOT}/viele/viele_1865_pct50.jpg")


if __name__ == "__main__":
    main()
