"""Fetch plain-text extracts of Wikipedia articles (cached under data/raw/roads/wiki) and
print the sentences that carry a year and an opening word. Usage: wiki.py [-n MAX] [-k regex] Title ..."""
import json, os, re, sys, time, requests
import os as _os
RAW = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "raw", "roads", "wiki"))
S = requests.Session(); S.headers["User-Agent"] = "NYCThroughTime-research/0.1"
ca = "/root/.ccr/ca-bundle.crt"
if os.path.exists(ca): S.verify = ca
def get(title):
    p = os.path.join(RAW, re.sub(r"[^A-Za-z0-9_.()-]", "_", title) + ".txt")
    if os.path.exists(p): return open(p).read()
    for _ in range(3):
        try:
            r = S.get("https://en.wikipedia.org/w/api.php", params={"action": "query", "prop": "extracts", "explaintext": 1,
                      "format": "json", "redirects": 1, "titles": title.replace("_", " ")}, timeout=40)
            pg = list(r.json()["query"]["pages"].values())[0]
            txt = pg.get("extract", "")
            open(p, "w").write(txt); time.sleep(2.5); return txt
        except Exception as e:
            err = e; time.sleep(6)
    print("FAILED", title, err); return ""
def sentences(txt):
    txt = re.sub(r"\n+", " ¶ ", txt)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z¶=])", txt)]
if __name__ == "__main__":
    a = sys.argv[1:]; n = 14; key = r"open|complet|dedicat|finish|extended|built"
    while a and a[0] in ("-n", "-k"):
        if a[0] == "-n": n = int(a[1])
        else: key = a[1]
        a = a[2:]
    for t in a:
        txt = get(t); out = [s for s in sentences(txt) if re.search(r"\b1[6-9]\d\d|20[0-2]\d\b", s) and re.search(key, s, re.I)]
        print(f"=== {t} ({len(txt)} chars, {len(out)} hits)")
        for s in out[:n]: print("  -", s[:330])
