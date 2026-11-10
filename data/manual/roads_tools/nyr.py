"""Fetch nycroads.com road pages (cached, text only) and print sentences with a year and an opening word.
Usage: nyr.py [-n MAX] [-k regex] slug ..."""
import html, os, re, sys, time, requests
import os as _os
RAW = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "raw", "roads", "nycroads"))
S = requests.Session(); S.headers["User-Agent"] = "NYCThroughTime-research/0.1"
def get(slug):
    p = os.path.join(RAW, slug.strip("/").replace("/", "_") + ".txt")
    if os.path.exists(p): return open(p).read()
    try:
        r = S.get(f"http://www.nycroads.com/{slug.strip('/')}/", timeout=40)
        t = r.content.decode("latin-1")
        if r.status_code != 200: print("HTTP", r.status_code, slug); return ""
    except Exception as e:
        print("FAILED", slug, e); return ""
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"(?i)<(br|p|/p|/tr|/h\d)[^>]*>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r"[ \t\r\xa0]+", " ", t); t = re.sub(r"\n\s*\n+", "\n", t)
    open(p, "w").write(t); time.sleep(1.0); return t
if __name__ == "__main__":
    a = sys.argv[1:]; n = 14; key = r"open|complet|dedicat|finish|extended"
    while a and a[0] in ("-n", "-k"):
        if a[0] == "-n": n = int(a[1])
        else: key = a[1]
        a = a[2:]
    for sl in a:
        txt = get(sl)
        ss = [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\"])", txt.replace("\n", " "))]
        out = [s for s in ss if re.search(r"\b(18|19|20)\d\d\b", s) and re.search(key, s, re.I)]
        print(f"=== {sl} ({len(txt)} chars, {len(out)} hits)")
        for s in out[:n]: print("  -", s[:270])
