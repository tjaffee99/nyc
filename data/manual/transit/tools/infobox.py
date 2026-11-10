"""Parse the station infoboxes ({{Infobox NYCS}}, {{Infobox station}}) out of downloaded article
wikitext: one dict per infobox with name, line(s), opened, closed, structure, coordinates."""
from __future__ import annotations

import re

MONTHS = {m: i + 1 for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november",
     "december"])}
MONTHS.update({m[:3]: i for m, i in list(MONTHS.items())})
MONTHS["sept"] = 9


def _balanced(txt: str, start: int) -> int:
    """Index just past the template that opens at `start` ('{{')."""
    depth, i = 0, start
    while i < len(txt) - 1:
        two = txt[i:i + 2]
        if two == "{{":
            depth += 1
            i += 2
        elif two == "}}":
            depth -= 1
            i += 2
            if depth == 0:
                return i
        else:
            i += 1
    return len(txt)


def _fields(body: str) -> dict[str, str]:
    """Top-level |key = value pairs of a template body."""
    out, depth, cur, parts = {}, 0, [], []
    i = 0
    while i < len(body):
        two = body[i:i + 2]
        if two in ("{{", "[["):
            depth += 1
            cur.append(two)
            i += 2
        elif two in ("}}", "]]"):
            depth -= 1
            cur.append(two)
            i += 2
        elif body[i] == "|" and depth == 0:
            parts.append("".join(cur))
            cur = []
            i += 1
        else:
            cur.append(body[i])
            i += 1
    parts.append("".join(cur))
    for p in parts[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            out[k.strip().lower()] = v.strip()
    return out


def parse_date(s: str) -> tuple[str, str]:
    """-> (ISO date or '', precision 'day' | 'month' | 'year' | '')."""
    if not s:
        return "", ""
    s = re.sub(r"<ref[^>]*/>", "", s)
    s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    m = re.search(r"\{\{\s*(?:start date and age|start date|end date|end date and age|dts|date|opening date)\s*\|([^}]*)\}\}", s, re.I)
    if m:
        a = [x.strip() for x in m.group(1).split("|") if "=" not in x and x.strip()]
        if a and re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", a[0]):
            y, mo, d = a[0].split("-")
            return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}", "day"
        nums = []
        for x in a[:3]:
            if x.isdigit():
                nums.append(int(x))
            elif x.lower() in MONTHS:
                nums.append(MONTHS[x.lower()])
            else:
                break
        if len(nums) == 3:
            return f"{nums[0]:04d}-{nums[1]:02d}-{nums[2]:02d}", "day"
        if len(nums) == 2:
            return f"{nums[0]:04d}-{nums[1]:02d}-15", "month"
        if len(nums) == 1:
            return f"{nums[0]:04d}-07-01", "year"
    m = re.search(r"([A-Z][a-z]+)\s+(\d{1,2}),?\s+(\d{4})", s)
    if m and m.group(1).lower() in MONTHS:
        return f"{int(m.group(3)):04d}-{MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}", "day"
    m = re.search(r"(\d{1,2})\s+([A-Z][a-z]+)\s+(\d{4})", s)
    if m and m.group(2).lower() in MONTHS:
        return f"{int(m.group(3)):04d}-{MONTHS[m.group(2).lower()]:02d}-{int(m.group(1)):02d}", "day"
    m = re.search(r"([A-Z][a-z]+)\s+(\d{4})", s)
    if m and m.group(1).lower() in MONTHS:
        return f"{int(m.group(2)):04d}-{MONTHS[m.group(1).lower()]:02d}-15", "month"
    m = re.search(r"\b(1[6-9]\d\d|20[0-2]\d)\b", s)
    if m:
        return f"{m.group(1)}-07-01", "year"
    return "", ""


def links(s: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"\[\[([^\]|#]+)", s or "")]


def infoboxes(txt: str) -> list[dict]:
    out = []
    for m in re.finditer(r"\{\{\s*Infobox (NYCS|New York City Subway station|station)\b", txt, re.I):
        end = _balanced(txt, m.start())
        f = _fields(txt[m.start() + 2:end - 2])
        op, opp = parse_date(f.get("opened", "") or f.get("open", ""))
        cl, clp = parse_date(f.get("closed", ""))
        coord = re.search(r"\{\{coord\|([-\d.]+)\|([-\d.]+)\|", f.get("coordinates", "") + f.get("coords", ""), re.I)
        out.append({"name": re.sub(r"<[^>]*>|\{\{[^}]*\}\}", "", f.get("name", "")).strip(), "lines": links(f.get("line", "")) or [f.get("line", "")],
                    "opened": op, "opened_prec": opp, "opened_raw": f.get("opened", "")[:160], "closed": cl, "closed_prec": clp,
                    "structure": re.sub(r"<[^>]*>.*", "", f.get("structure", "")).strip(), "rebuilt": f.get("rebuilt", "")[:120],
                    "other_name": f.get("other_name", ""), "former": f.get("former", ""), "pos": m.start(),
                    "lat": float(coord.group(1)) if coord else None, "lon": float(coord.group(2)) if coord else None})
    return out
