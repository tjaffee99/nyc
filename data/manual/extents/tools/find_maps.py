"""List NYPL Map Warper maps (NYC Space/Time Directory dump, mapwarper.objects.ndjson) by name
pattern, year range and warped area (km2).
usage: python -I find_maps.py <regex> [ymin] [ymax] [min_km2] [max_km2]"""
import json, re, sys
pat = re.compile(sys.argv[1], re.I)
ymin = int(sys.argv[2]) if len(sys.argv) > 2 else 0
ymax = int(sys.argv[3]) if len(sys.argv) > 3 else 9999
amin = float(sys.argv[4]) if len(sys.argv) > 4 else 0
amax = float(sys.argv[5]) if len(sys.argv) > 5 else 1e12
P = "/home/user/nyc/data/raw/extents/spacetime/mapwarper.objects.ndjson"
for line in open(P):
    o = json.loads(line)
    d = o.get("data", {})
    txt = (o.get("name") or "") + " | " + (d.get("description") or "")
    y = o.get("validSince") or 0
    a = d.get("area") or 0
    if pat.search(txt) and ymin <= y <= ymax and amin <= a <= amax:
        g = o.get("geometry")
        bb = ""
        if g:
            cs = g["coordinates"][0] if g["type"] == "Polygon" else g["coordinates"][0][0]
            xs = [c[0] for c in cs]; ys = [c[1] for c in cs]
            bb = "%.3f,%.3f,%.3f,%.3f" % (min(xs), min(ys), max(xs), max(ys))
            cx = (min(xs) + max(xs)) / 2; cy = (min(ys) + max(ys)) / 2
            if not (-74.3 < cx < -73.65 and 40.45 < cy < 40.95):
                continue
        print(o["id"], y, d.get("imageId"), "g=%d" % len(d.get("gcps") or []), "a=%.1f" % a, bb, "|", txt[:120].replace("\n", " "))
