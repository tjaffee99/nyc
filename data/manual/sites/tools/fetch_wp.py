"""Fetch the wikitext of the Wikipedia articles cited for the sites (CC BY-SA 4.0; facts only).

  python -I fetch_wp.py            # every title in wp_titles.txt not yet cached
  python -I fetch_wp.py Title ...  # the given titles

Cache: data/raw/sites/wp/<Title>.wiki (redirects are followed once and noted on line 1).
One request a second, generic User-Agent.
"""
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[3] / "data" / "raw" / "sites" / "wp"
OUT.mkdir(parents=True, exist_ok=True)
UA = "NYCThroughTime-research/0.1"


def get(title):
    u = "https://en.wikipedia.org/w/index.php?action=raw&title=" + urllib.parse.quote(title.replace(" ", "_"), safe="")
    r = subprocess.run(["curl", "-sS", "-m", "40", "-A", UA, "-w", "\n%{http_code}", u], capture_output=True)
    body, _, code = r.stdout.decode("utf-8", "replace").rpartition("\n")
    return code.strip(), body


def fetch(title):
    f = OUT / (title.replace("/", "_") + ".wiki")
    if f.exists() and f.stat().st_size > 0:
        return "cached"
    code, body = get(title)
    time.sleep(1.0)
    if code == "429" or "too many requests" in body[:200].lower():
        time.sleep(20)
        code, body = get(title)
    if code != "200":
        return f"HTTP {code}"
    if body.lstrip().upper().startswith("#REDIRECT"):
        tgt = body.split("[[", 1)[1].split("]]", 1)[0].split("#")[0].split("|")[0]
        code, b2 = get(tgt)
        time.sleep(1.0)
        if code != "200":
            return f"redirect to {tgt}: HTTP {code}"
        body = f"<!-- redirected from {title} to {tgt} -->\n" + b2
    f.write_text(body, encoding="utf-8")
    return f"ok {len(body)}"


if __name__ == "__main__":
    titles = sys.argv[1:] or [t.strip() for t in (HERE / "wp_titles.txt").read_text().splitlines()
                              if t.strip() and not t.startswith("#")]
    bad = []
    for t in titles:
        s = fetch(t)
        if not s.startswith(("ok", "cached")):
            bad.append((t, s))
    print(len(titles), "titles;", len(bad), "failed")
    for t, s in bad:
        print("  FAILED", t, s)
