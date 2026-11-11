"""Fetch Library of Congress Sanborn sheets at 50 % (public domain). Needs the item JSON (https://www.loc.gov/item/<id>/?fo=json) in data/interim/atlas_nj_cities/.
python -I fetch.py list <loc item id>          -> sheet names
python -I fetch.py get <loc item id> <tag> <name> ...   -> data/raw/atlas/nj_cities/<tag>_<name>.jpg   (pct = env PCT, default 50)"""
import io, json, os, re, sys, time
from pathlib import Path
import requests
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
ROOT = Path(__file__).resolve().parents[4]
UA = {"User-Agent": "NYCThroughTime-research/0.1"}
def names(item):
    p = ROOT / f"data/interim/atlas_nj_cities/{item}.json"
    if not p.exists():
        r = requests.get(f"https://www.loc.gov/item/{item}/?fo=json", headers=UA, timeout=60); r.raise_for_status(); p.write_bytes(r.content)
    d = json.loads(p.read_text()); out = {}
    for x in d["resources"][0]["files"]:
        u = [y["url"] for y in x if "iiif" in y["url"]][0]
        m = re.search(r"(iiif/service:[^/]*?:[^:/]+)/full", u)
        base, nm = m.group(1).rsplit("-", 1)[0], m.group(1).rsplit("-", 1)[1]
        out[nm] = "https://tile.loc.gov/image-services/" + m.group(1)
    return out
if __name__ == "__main__":
    a = sys.argv[1:]; N = names(a[1])
    if a[0] == "list": print(" ".join(N))
    else:
        pct = os.environ.get("PCT", "50")
        for nm in a[3:]:
            out = ROOT / f"data/raw/atlas/nj_cities/{a[2]}_{nm}.jpg"
            if out.exists(): continue
            url = N[nm] + f"/full/pct:{pct}/0/default.jpg"
            for tr in range(6):
                try:
                    r = requests.get(url, headers=UA, timeout=240); r.raise_for_status()
                    Image.open(io.BytesIO(r.content)).convert("RGB").save(out, quality=92); print(nm, flush=True); break
                except Exception as e:
                    print("retry", nm, str(e)[:60], flush=True); time.sleep(3 + 3 * tr)
