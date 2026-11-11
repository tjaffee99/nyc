"""Census population of every municipality on the map, by decade (round 3).

Stages (python town_population.py <stage>):
  outlines  TIGER 2024 county subdivisions of the 26 counties -> data/interim/towns/towns.parquet
            (+ order.csv: building counts per municipality, used only to order the fetch)
  fetch     walk the municipalities largest first, one Wikipedia page every ~4.5 s (back-off on
            429), cache raw wikitext under data/raw/wikipedia_towns/, append rows to
            data/tables/population_towns.csv. Resumable: a geoid already in
            data/interim/towns/done.csv is skipped. `fetch N` stops after N municipalities.
  checks    print series of well-known places, 2020 sanity, county sums vs the county tables.

Join with the outlines on `geoid` (TIGER GEOID = state 2 + county 3 + cousub 5).
Connecticut: the "county" is the planning region (09120 Greater Bridgeport ...).
Opened sources only: Wikipedia raw wikitext ({{US Census population}} template).
"""
from __future__ import annotations

import csv
import json
import re
import sys
import time
import urllib.parse
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
TIGER = ROOT / "data/raw/tiger"
TOWNS = ROOT / "data/interim/towns"
CACHE = ROOT / "data/raw/wikipedia_towns"
OUT = ROOT / "data/tables/population_towns.csv"
DONE = TOWNS / "done.csv"
UA = "NYCThroughTime-research/0.1"
DELAY = 4.5
COLS = ["year", "geoid", "name", "county", "state", "population", "source_url", "note"]
NOTE = "census count as tabulated in the article's US Census population template"
STATE_NAME = {"34": "New Jersey", "36": "New York", "09": "Connecticut", "42": "Pennsylvania"}
STATE_AB = {"34": "NJ", "36": "NY", "09": "CT", "42": "PA"}
# the map's counties: fips -> name (TIGER county FIPS; Connecticut = planning region)
COUNTIES = {
    "34017": "Hudson", "34003": "Bergen", "34013": "Essex", "34039": "Union", "34031": "Passaic",
    "36119": "Westchester", "36087": "Rockland", "36059": "Nassau", "36103": "Suffolk",
    "36079": "Putnam", "36071": "Orange", "36027": "Dutchess", "36111": "Ulster", "36105": "Sullivan",
    "34023": "Middlesex", "34025": "Monmouth", "34029": "Ocean", "34035": "Somerset",
    "34027": "Morris", "34037": "Sussex", "34019": "Hunterdon", "34021": "Mercer",
    "09120": "Greater Bridgeport", "09190": "Western Connecticut", "09170": "South Central Connecticut",
    "42103": "Pike",
}


# ---------------------------------------------------------------- outlines
def say_name(r) -> str:
    st, lsad, name, lsadname = r["STATEFP"], r["LSAD"], r["NAME"], r["NAMELSAD"]
    if st == "36":
        return name if lsad == "25" else f"{name} town"
    if st == "09":
        return name
    # NJ / PA: townships keep the suffix, boroughs / cities / towns do not
    return lsadname if lsad == "44" else name


def outlines():
    import geopandas as gpd
    import pandas as pd
    TOWNS.mkdir(parents=True, exist_ok=True)
    if (TOWNS / "towns.parquet").exists() and (TOWNS / "order.csv").exists():
        print("towns.parquet exists")
        return
    parts = []
    for st in STATE_NAME:
        g = gpd.read_file(TIGER / f"tl_2024_{st}_cousub.zip")
        g["county_fips"] = g["STATEFP"] + g["COUNTYFP"]
        g = g[g.county_fips.isin(COUNTIES)]
        # (Princeton's LSAD is "00" in TIGER 2024: keep it; "Bridgewater" contains "water")
        g = g[(g.ALAND > 0) & (g.LSAD != "86") & ~g.NAME.str.contains("not defined", case=False)]
        parts.append(g)
    g = pd.concat(parts, ignore_index=True)
    g["name"] = g.apply(say_name, axis=1)
    g["state"] = g.STATEFP.map(STATE_AB)
    g = g.rename(columns={"GEOID": "geoid", "NAMELSAD": "namelsad"})
    g = g.to_crs(32618)
    g["geometry"] = g.geometry.simplify(40, preserve_topology=True)
    g = g.to_crs(4326)[["geoid", "name", "namelsad", "county_fips", "state", "geometry"]]
    g.to_parquet(TOWNS / "towns.parquet")
    print(len(g), "municipalities")
    # order: number of buildings in each (proxy for population; the Census API wants a key)
    import pyarrow.parquet as pq
    counts = pd.Series(0, index=g.geoid)
    for f in ("county_points_inner", "county_points_outer"):
        pf = pq.ParquetFile(ROOT / f"data/interim/{f}.parquet")
        for b in pf.iter_batches(batch_size=500_000, columns=["lon", "lat"]):
            d = b.to_pandas()
            pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(d.lon, d.lat), crs=4326)
            j = gpd.sjoin(pts, g[["geoid", "geometry"]], predicate="within")
            counts = counts.add(j.geoid.value_counts(), fill_value=0)
    counts.rename("n_buildings").astype(int).sort_values(ascending=False).to_csv(TOWNS / "order.csv")


# ---------------------------------------------------------------- wikipedia
_last = [0.0]


def http(params: dict) -> requests.Response:
    """One polite request: spaced, with back-off on 429/5xx."""
    wait = 30
    for _ in range(8):
        dt = DELAY - (time.time() - _last[0])
        if dt > 0:
            time.sleep(dt)
        _last[0] = time.time()
        try:
            r = requests.get("https://en.wikipedia.org/w/index.php" if "action" in params and params["action"] == "raw"
                             else "https://en.wikipedia.org/w/api.php", params=params,
                             headers={"User-Agent": UA}, timeout=60)
        except requests.RequestException:
            time.sleep(wait); wait *= 2; continue
        if r.status_code in (429, 500, 502, 503, 504):
            ra = r.headers.get("Retry-After")
            time.sleep(int(ra) if ra and ra.isdigit() else wait); wait = min(wait * 2, 600); continue
        return r
    raise RuntimeError("wikipedia keeps refusing")


def safe(t: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.,()-]", "_", t)


def raw_page(title: str):
    """Raw wikitext of a title, following #REDIRECT; None if absent. Cached."""
    for _ in range(4):
        p = CACHE / (safe(title) + ".txt")
        if p.exists():
            txt = p.read_text()
        else:
            r = http({"title": title, "action": "raw"})
            if r.status_code == 404:
                p.write_text("")  # remember absence
                return None, title
            r.raise_for_status()
            txt = r.text
            p.write_text(txt)
        if not txt:
            return None, title
        m = re.match(r"\s*#REDIRECT\s*\[\[([^\]#|]+)", txt, re.I)
        if m:
            title = m.group(1).strip()
            continue
        return txt, title
    return None, title


# a township whose plain title is a borough's article (found by the duplicate-series check)
OVERRIDE = {
    "3402133180": "Hopewell Township, Mercer County, New Jersey",
    "3402777240": "Washington Township, Morris County, New Jersey",
    "3400377135": "Washington Township, Bergen County, New Jersey",
    "4210349408": "Milford Township, Pike County, Pennsylvania",
}


def candidates(row, cname: str):
    n, st, sname = row["name"], row["STATE"], STATE_NAME[row["STATE"]]
    lsadname = re.sub(r" (township|borough|city|town|village)$", lambda m: " " + m.group(1).title(), row["namelsad"])
    base = row["NAME"]
    cs = []
    if st == "36":
        if row["LSAD"] == "25":
            cs += [f"{base}, New York", f"{base} (city), New York", f"{base}, {cname} County, New York"]
        else:
            cs += [f"{base} (town), New York", f"{base}, New York", f"{base} (town), {cname} County, New York",
                   f"{base}, {cname} County, New York"]
    elif st == "09":
        cs += [f"{base}, Connecticut"]
    else:
        cs += [f"{lsadname}, {sname}", f"{base}, {sname}", f"{lsadname}, {cname} County, {sname}",
               f"{base}, {cname} County, {sname}", f"{base} Township, {sname}"]
        if row["LSAD"] == "21":
            cs += [f"{base} Borough, {sname}"]
    seen = []
    for c in cs:
        if c not in seen:
            seen.append(c)
    return seen


def acceptable(txt: str, row, cname: str) -> bool:
    head = txt[:6000]
    if re.search(r"\{\{\s*(disambig|dab|geodis|hndis)", txt[:3000], re.I):
        return False
    i = txt.find("\n\'\'\'")
    lead, box = (txt[i:i + 400].lower(), txt[:i]) if i > 0 else ("", txt[:3000])
    if row["STATE"] == "09":
        return True
    if row["STATE"] == "36" and row["LSAD"] == "43" and re.search(r"is a (\[\[)?(village|hamlet|census|city)", lead[:200]):
        return False
    return cname.lower() in box.lower() or (row["STATE"] == "42" and "pike" in box.lower())


def balanced_templates(txt: str, name_re: str):
    """Yield the body of every {{name ...}} template (balanced braces)."""
    for m in re.finditer(r"\{\{\s*(" + name_re + r")\b", txt, re.I):
        i, depth = m.start(), 0
        j = i
        while j < len(txt) - 1:
            if txt[j:j + 2] == "{{":
                depth += 1; j += 2
            elif txt[j:j + 2] == "}}":
                depth -= 1; j += 2
                if depth == 0:
                    yield txt[i + 2:j - 2]
                    break
            else:
                j += 1


def split_args(body: str):
    out, depth, cur = [], 0, ""
    i = 0
    while i < len(body):
        two = body[i:i + 2]
        if two in ("{{", "[["):
            depth += 1; cur += two; i += 2
        elif two in ("}}", "]]"):
            depth -= 1; cur += two; i += 2
        elif body[i] == "|" and depth == 0:
            out.append(cur); cur = ""; i += 1
        else:
            cur += body[i]; i += 1
    out.append(cur)
    return out


def num(s: str):
    s = re.sub(r"<ref[^>]*?/>|<ref.*?</ref>|\{\{.*?\}\}|<!--.*?-->|<[^>]+>", "", s, flags=re.S)
    s = s.replace("&nbsp;", "")
    m = re.match(r"\s*(?:\[\[[^\]]*\]\])?\s*([\d][\d,\s]*)", s)
    if not m:
        return None
    d = re.sub(r"[,\s]", "", m.group(1))
    return int(d) if d else None


def positional(args):
    """{{Historical populations |1790|4487 |1800|5772 ...}}: year, count pairs."""
    vals = [a.strip() for a in args if "=" not in a.split("{{")[0]]
    d = {}
    for i in range(len(vals) - 1):
        if re.fullmatch(r"1[6-9]\d0|20[0-3]0", vals[i]):
            n = num(vals[i + 1])
            if n is not None and not re.fullmatch(r"1[6-9]\d\d|20[0-3]\d", vals[i + 1].strip()):
                d[int(vals[i])] = n
    return d


def parse_series(txt: str):
    """{year: population} from {{US Census population}} templates (also |1790=1,234 style)."""
    best = {}
    for body in balanced_templates(txt, r"US Census population|USCensusPop|US Census pop|Census population|Historical populations|Historical population|Population table"):
        args = split_args(body)[1:]
        d = {}
        for a in args:
            if "=" not in a:
                continue
            k, v = a.split("=", 1)
            k = k.strip()
            if re.fullmatch(r"1[6-9]\d0|20[0-2]0", k):
                n = num(v)
                if n is not None:
                    d[int(k)] = n
        d.update(positional(args))
        # keep the template with most years (an article can show a 'by decade' and an 'estimates' one)
        if len(d) > len(best):
            best = d
    return best


def infobox_pop(txt: str):
    """2020-ish figure from the infobox as a fallback: (year, n) or None."""
    m = re.search(r"\|\s*population_total\s*=\s*([^\n|]+)", txt)
    if not m:
        return None
    n = num(m.group(1))
    y = re.search(r"\|\s*population_as_of\s*=[^\n]*?(\d{4})", txt)
    return (int(y.group(1)) if y else None, n) if n else None


def load_done():
    return {r[0]: r for r in csv.reader(DONE.open())} if DONE.exists() else {}


def fetch(limit: int | None = None):
    import geopandas as gpd
    import pandas as pd
    outlines()
    g = gpd.read_parquet(TOWNS / "towns.parquet")
    tg = {st: gpd.read_file(TIGER / f"tl_2024_{st}_cousub.zip", columns=["GEOID", "NAME", "LSAD"]) for st in STATE_NAME}
    tl = pd.concat(tg.values()).set_index("GEOID")
    order = pd.read_csv(TOWNS / "order.csv", dtype={"geoid": str}, index_col=0).n_buildings
    g = g.set_index("geoid").join(order).sort_values("n_buildings", ascending=False)
    done = load_done()
    new_file = not OUT.exists()
    CACHE.mkdir(parents=True, exist_ok=True)
    fo = OUT.open("a", newline="")
    w = csv.writer(fo)
    if new_file:
        w.writerow(COLS)
    fd = DONE.open("a", newline="")
    wd = csv.writer(fd)
    n_done = 0
    for geoid, r in g.iterrows():
        if geoid in done:
            continue
        if limit is not None and n_done >= limit:
            break
        cname = COUNTIES[r.county_fips]
        row = {"name": r["name"], "namelsad": r.namelsad, "STATE": geoid[:2], "NAME": tl.loc[geoid, "NAME"],
               "LSAD": tl.loc[geoid, "LSAD"]}
        status, used, series = "failed", "", {}
        for t in ([OVERRIDE[geoid]] if geoid in OVERRIDE else candidates(row, cname)):
            txt, final = raw_page(t)
            if txt is None or not acceptable(txt, row, cname):
                continue
            s = parse_series(txt)
            used = final
            if s:
                series, status = s, "ok"
                break
            status = "no_template"
        url = "https://en.wikipedia.org/wiki/" + urllib.parse.quote(used.replace(" ", "_"), safe="_,()") if used else ""
        for y in sorted(series):
            w.writerow([y, geoid, r["name"], cname, r["state"], series[y], url, NOTE])
        fo.flush()
        wd.writerow([geoid, r["name"], status, used, len(series), min(series) if series else ""])
        fd.flush()
        n_done += 1
        if n_done % 20 == 0:
            print(n_done, geoid, r["name"], status, flush=True)
    print("fetched", n_done)


# ---------------------------------------------------------------- fill
def fill():
    """Add a 2020 row from the article's infobox where the template lacks 2020 (the Census API
    answers only with a key, which this project does not have); report 2020 template/infobox
    disagreements. Rows are appended once (note says 'infobox')."""
    import pandas as pd
    t = pd.read_csv(OUT, dtype={"geoid": str}) if OUT.exists() else pd.DataFrame(columns=COLS)
    t = t.drop_duplicates(["geoid", "year"])
    import geopandas as gpd
    g = gpd.read_parquet(TOWNS / "towns.parquet").set_index("geoid")
    have = {(r.geoid, r.year) for r in t.itertuples()}
    add, bad = [], []
    for row in csv.reader(DONE.open()):
        geoid, name, status, title = row[0], row[1], row[2], row[3]
        if not title:
            continue
        txt, final = raw_page(title)
        if not txt:
            continue
        ib = infobox_pop(txt)
        if not ib:
            continue
        y, n = ib
        if y not in (2020, 2021, None) and y != 2020:
            continue
        url = "https://en.wikipedia.org/wiki/" + urllib.parse.quote(final.replace(" ", "_"), safe="_,()")
        if (geoid, 2020) in have:
            tv = int(t[(t.geoid == geoid) & (t.year == 2020)].population.iloc[0])
            if abs(tv - n) / n > 0.005:
                bad.append((name, geoid, tv, n))
        elif y == 2020:
            add.append([2020, geoid, name, COUNTIES[g.loc[geoid, "county_fips"]], g.loc[geoid, "state"], n, url,
                        "2020 census count from the article's infobox (the template has none)"])
    t = t.drop_duplicates()
    with OUT.open("w", newline="") as f:
        w = csv.writer(f); w.writerow(COLS)
        for r in t.itertuples(index=False):
            w.writerow(list(r))
        for r in add:
            if (r[1], 2020) not in have:
                w.writerow(r)
    print("added", len(add), "2020 rows; template vs infobox disagreements:", bad)


# ---------------------------------------------------------------- checks
def checks():
    import pandas as pd
    t = pd.read_csv(OUT, dtype={"geoid": str})
    for nm, st in [("Newark", "NJ"), ("Jersey City", "NJ"), ("Paterson", "NJ"), ("Elizabeth", "NJ"), ("Yonkers", "NY"),
                   ("New Rochelle", "NY"), ("White Plains", "NY"), ("Hoboken", "NJ"), ("Bayonne", "NJ"),
                   ("Princeton", "NJ"), ("Trenton", "NJ"), ("New Brunswick", "NJ"), ("Stamford", "CT"),
                   ("Bridgeport", "CT"), ("New Haven", "CT"), ("Hempstead town", "NY"), ("Poughkeepsie", "NY")]:
        s = t[(t.name == nm) & (t.state == st)]
        if s.empty:
            print(nm, st, "MISSING"); continue
        for gid, ss in s.groupby("geoid"):
            ss = ss.sort_values("year")
            print(f"\n{nm} {gid} {ss.county.iloc[0]}: {len(ss)} yrs {ss.year.min()}-{ss.year.max()}")
            print(" ".join(f"{y}:{p}" for y, p in zip(ss.year, ss.population)))
    print("\nSUSPECT (ratio to neighbours > 6 or < 1/6, or gap > 20 years)")
    for gid, ss in t.groupby("geoid"):
        ss = ss.sort_values("year")
        y, p = ss.year.tolist(), ss.population.tolist()
        for i in range(1, len(y)):
            a, b = p[i - 1], p[i]
            if (a > 300 and b / max(a, 1) > 6 and b > 3000) or (b > 300 and a / max(b, 1) > 6 and a > 3000) or y[i] - y[i - 1] > 20:
                print(gid, ss.name.iloc[0], y[i - 1], a, y[i], b)
    print("\nCOUNTY SUMS vs county tables")
    cty = pd.concat([pd.read_csv(ROOT / f"data/tables/population_{k}.csv") for k in ("counties", "outer")])
    for county, sub in t.groupby("county"):
        for yr in (1950, 2020):
            s = sub[sub.year == yr]
            c = cty[(cty.area.str.lower() == county.lower().replace(" ", "_")) & (cty.year == yr)]
            if len(c):
                print(f"{county:28s} {yr}: towns {s.population.sum():>9,} ({s.geoid.nunique()}) vs county {int(c.population.iloc[0]):>9,}"
                      f"  ratio {s.population.sum() / c.population.iloc[0]:.3f}")


if __name__ == "__main__":
    st = sys.argv[1] if len(sys.argv) > 1 else "fetch"
    if st == "outlines":
        outlines()
    elif st == "fetch":
        fetch(int(sys.argv[2]) if len(sys.argv) > 2 else None)
    elif st == "fill":
        fill()
    elif st == "checks":
        checks()
