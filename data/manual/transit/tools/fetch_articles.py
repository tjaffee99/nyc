"""Research helper: download the wikitext of Wikipedia articles (one file per title) into
data/raw/transit/wikipedia/articles/. Titles come from a text file (one per line) or from the
station match (data/interim/transit/station_match.csv, column `title`). Redirects are followed.

    ../../.venv/bin/python fetch_articles.py [titles.txt]
"""
from __future__ import annotations

import re
import sys
import time
import urllib.parse
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "data" / "raw" / "transit" / "wikipedia" / "articles"
OUT.mkdir(parents=True, exist_ok=True)
S = requests.Session()
S.headers["User-Agent"] = "NYCThroughTime-research/0.1"
CA = Path("/root/.ccr/ca-bundle.crt")
if CA.exists():
    S.verify = str(CA)


def fname(title: str) -> Path:
    return OUT / (re.sub(r"[^A-Za-z0-9_.()\-–,']", "_", title.replace(" ", "_")) + ".wiki")


def fetch(title: str, depth=0) -> str | None:
    p = fname(title)
    if p.exists():
        return p.read_text()
    url = "https://en.wikipedia.org/w/index.php?action=raw&title=" + urllib.parse.quote(title.replace(" ", "_"))
    for attempt in range(4):
        r = S.get(url, timeout=60)
        if r.status_code == 200:
            break
        if r.status_code == 404:
            p.write_text("")
            return None
        time.sleep(2 + 3 * attempt)
    else:
        return None
    txt = r.text
    m = re.match(r"\s*#REDIRECT\s*\[\[([^\]#|]+)", txt, re.I)
    if m and depth < 3:
        txt = fetch(m.group(1).strip(), depth + 1) or ""
        txt = f"<!-- redirected from {title} to {m.group(1).strip()} -->\n" + txt
    p.write_text(txt)
    time.sleep(0.15)
    return txt


def main():
    if len(sys.argv) > 1:
        titles = [t.strip() for t in Path(sys.argv[1]).read_text().splitlines() if t.strip()]
    else:
        m = pd.read_csv(ROOT / "data" / "interim" / "transit" / "station_match.csv", dtype=str, keep_default_na=False)
        titles = sorted(set(m.title))
    ok = miss = 0
    for t in titles:
        txt = fetch(t)
        if txt:
            ok += 1
        else:
            miss += 1
            print("missing:", t, file=sys.stderr)
    print(f"{ok} articles, {miss} missing", file=sys.stderr)


if __name__ == "__main__":
    main()
