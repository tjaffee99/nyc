"""Wikipedia article as text when the extracts API is rate-limited: the raw wikitext (index.php?action=raw),
templates, references and link markup stripped; tables stay as wikitext rows. Cached beside the API extracts
(data/raw/roads/wiki/<title>.txt, the unstripped text as .wikitext).
Usage: wraw.py [-n MAX] [-k regex] Title ...   (prints sentences / table rows that carry a year and match)"""
import os
import re
import sys
import time

import requests

import os as _os
RAW = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "raw", "roads", "wiki"))
S = requests.Session()
S.headers["User-Agent"] = "NYCThroughTime-research/0.1"
if os.path.exists("/root/.ccr/ca-bundle.crt"):
    S.verify = "/root/.ccr/ca-bundle.crt"
Q3, Q2 = "'" * 3, "'" * 2


def strip(txt):
    txt = re.sub(r"(?is)<ref[^>/]*/>|<ref.*?</ref>|<!--.*?-->", "", txt)
    for _ in range(5):
        txt = re.sub(r"\{\{(?:[Cc]onvert|cvt)\|([^|}]+)\|([^|}]+)[^}]*\}\}", r"\1 \2", txt)
        txt = re.sub(r"\{\{[^{}]*\}\}", "", txt)
    txt = re.sub(r"\[\[(?:File|Image):[^\]]*\]\]", "", txt)
    txt = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", txt)
    return txt.replace(Q3, "").replace(Q2, "")


def get(title, force=False):
    p = os.path.join(RAW, re.sub(r"[^A-Za-z0-9_.()-]", "_", title) + ".txt")
    if os.path.exists(p) and os.path.getsize(p) > 500 and not force:
        return open(p).read()
    err = None
    for _ in range(3):
        try:
            r = S.get("https://en.wikipedia.org/w/index.php", params={"title": title, "action": "raw"}, timeout=40)
            if r.status_code == 200 and len(r.text) > 50:
                raw = r.text
                m = re.match(r"\s*#REDIRECT\s*\[\[([^\]|#]+)", raw, re.I)
                if m:
                    r = S.get("https://en.wikipedia.org/w/index.php",
                              params={"title": m.group(1).strip().replace(" ", "_"), "action": "raw"}, timeout=40)
                    raw = r.text
                open(p[:-4] + ".wikitext", "w").write(raw)
                txt = strip(raw)
                open(p, "w").write(txt)
                time.sleep(1.5)
                return txt
            err = f"HTTP {r.status_code}"
        except Exception as e:  # noqa: BLE001
            err = e
        time.sleep(6)
    print("FAILED", title, err)
    return ""


def sentences(txt):
    txt = re.sub(r"\n+", " ¶ ", txt)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z¶=|])", txt)]


if __name__ == "__main__":
    a = sys.argv[1:]
    n, key = 10, r"open|complet|built|laid out|extended"
    while a and a[0] in ("-n", "-k"):
        if a[0] == "-n":
            n = int(a[1])
        else:
            key = a[1]
        a = a[2:]
    for t in a:
        txt = get(t)
        out = [s for s in sentences(txt) if re.search(r"\b1[6-9]\d\d\b|\b20[0-2]\d\b", s) and re.search(key, s, re.I)]
        print(f"=== {t} ({len(txt)} chars, {len(out)} hits)")
        for s in out[:n]:
            print("  -", s[:380])
