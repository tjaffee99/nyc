"""Hoboken, Sanborn vol. 7 (re-issue of 1930, corrected to 1951): fetch sheets at 50 %. python -I fetch30.py <sheet> ...  (LoC IIIF, public domain)"""
import io, sys, time
from pathlib import Path
import requests
from PIL import Image
ROOT = Path(__file__).resolve().parents[4]
B = "https://tile.loc.gov/image-services/iiif/service:gmd:gmd381m:g3814m:g3814hm:g3814hm_g05511195107:05511_07_1951"
for k in sys.argv[1:]:
    key = "%04d" % int(k); out = ROOT / f"data/raw/atlas/hoboken/loc_hob1930_{key}.jpg"
    if out.exists(): continue
    for tr in range(8):
        try:
            r = requests.get(f"{B}-{key}/full/pct:50/0/default.jpg", headers={"User-Agent": "NYCThroughTime-research/0.1"}, timeout=240); r.raise_for_status()
            Image.open(io.BytesIO(r.content)).convert("RGB").save(out, quality=92); print(key, flush=True); break
        except Exception as e:
            print("retry", key, str(e)[:50], flush=True); time.sleep(3 + 3 * tr)
