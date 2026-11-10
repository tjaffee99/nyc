"""Facts from the cached Wikipedia articles (data/raw/sites/wp/*.wiki).

  python -I wp_facts.py                 # one line per article: coordinates + dated infobox fields
  python -I wp_facts.py grep REGEX [TITLE-REGEX] [--w 160]   # sentences matching REGEX
  python -I wp_facts.py years TITLE Y1 Y2 ...   # is each year mentioned in the article?
"""
import re
import sys
from pathlib import Path

WP = Path(__file__).resolve().parents[4] / "data" / "raw" / "sites" / "wp"
KEYS = ("built", "opened", "open", "closed", "close", "demolished", "established", "founded", "defunct", "used", "in_use",
        "inuse", "formed", "dissolved", "start", "end", "years", "date_opened", "date_closed", "commissioned",
        "decommissioned", "commission", "decommission", "construction_began", "completion_date", "opening", "closing",
        "status", "fate", "area", "th_fuel_primary", "ps_units_operational", "bed", "inaugurated", "abandoned", "construction")


def clean(s):
    s = re.sub(r"<ref[^>]*?/>", "", s)
    s = re.sub(r"<ref.*?</ref>", "", s, flags=re.S)
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    s = re.sub(r"\{\{(?:convert|cvt)\|([^|}]*)\|([^|}]*)[^}]*\}\}", r"\1 \2", s)
    s = re.sub(r"\{\{(?:start date(?: and age)?|end date|dts|date)\|([^}]*)\}\}", lambda m: "-".join(x for x in m.group(1).split("|") if x[:1].isdigit()), s, flags=re.I)
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"'{2,}", "", s)
    return s


def coord(t):
    m = re.search(r"\{\{[Cc]oord\|([^}]*)\}\}", t)
    if not m:
        return None
    p = [x.strip() for x in m.group(1).split("|")]
    try:
        if len(p) >= 8 and p[3] in "NS" and p[7] in "EW":
            la = float(p[0]) + float(p[1]) / 60 + float(p[2]) / 3600
            lo = float(p[4]) + float(p[5]) / 60 + float(p[6]) / 3600
            return round(-lo if p[7] == "W" else lo, 5), round(-la if p[3] == "S" else la, 5)
        if len(p) >= 6 and p[2] in "NS" and p[5] in "EW":
            la = float(p[0]) + float(p[1]) / 60
            lo = float(p[3]) + float(p[4]) / 60
            return round(-lo if p[5] == "W" else lo, 5), round(-la if p[2] == "S" else la, 5)
        if len(p) >= 4 and p[1] in "NS" and p[3] in "EW":
            return round(-float(p[2]) if p[3] == "W" else float(p[2]), 5), round(float(p[0]), 5)
        return round(float(p[1]), 5), round(float(p[0]), 5)
    except (ValueError, IndexError):
        return None


def facts(t):
    out = []
    for k, v in re.findall(r"^\s*\|\s*([a-z_0-9 ]+?)\s*=\s*(.+)$", t, flags=re.M):
        k = k.strip().lower().replace(" ", "_")
        if k in KEYS and re.search(r"\d{4}", v):
            out.append(f"{k}={clean(v).strip()[:90]}")
    return out


def sentences(t):
    t = clean(t)
    t = re.sub(r"\{\{[^{}]*\}\}", "", t)
    t = re.sub(r"\{\{[^{}]*\}\}", "", t)
    return re.split(r"(?<=[.!?])\s+|\n+", t)


if __name__ == "__main__":
    a = sys.argv[1:]
    files = sorted(WP.glob("*.wiki"))
    if not a:
        for f in files:
            t = f.read_text(encoding="utf-8")
            print(f"{f.stem} | {coord(t)} | " + "; ".join(facts(t))[:420])
    elif a[0] == "grep":
        w = int(a[a.index("--w") + 1]) if "--w" in a else 220
        rx = re.compile(a[1], re.I)
        trx = re.compile(a[2], re.I) if len(a) > 2 and not a[2].startswith("--") else None
        for f in files:
            if trx and not trx.search(f.stem):
                continue
            for s in sentences(f.read_text(encoding="utf-8")):
                m = rx.search(s)
                if m and len(s) > 25:
                    i = max(0, m.start() - w // 2)
                    print(f"[{f.stem}] {s[i:i + w].strip()}")
    elif a[0] == "years":
        t = clean((WP / (a[1] + ".wiki")).read_text(encoding="utf-8"))
        print(a[1], {y: len(re.findall(r"\b" + y + r"\b", t)) for y in a[2:]})
