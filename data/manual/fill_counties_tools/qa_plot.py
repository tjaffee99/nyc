"""QA plots (scratch, not committed): the counties' zones over today's land, streets and railways.
  python qa_plot.py name w s e n [prefixes] [label_min_m] [rows_json ...]
Zones are read from fill_zones_counties.csv, or from rows_<tag>.json files given at the end."""
import csv, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from zonelib import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely import wkb
from shapely.geometry import box

name, w, s, e, n = sys.argv[1], *map(float, sys.argv[2:6])
pref = tuple(sys.argv[6].split(',')) if len(sys.argv) > 6 and sys.argv[6] != '-' else ('',)
lab = float(sys.argv[7]) if len(sys.argv) > 7 else 1e9
if len(sys.argv) > 8:
    rd = [r for f in sys.argv[8:] for r in json.load(open(os.path.join(INTERIM, f)))]
else:
    p = os.path.join(ROOT, 'data', 'manual', 'fill_zones_counties.csv')
    rd = list(csv.DictReader(open(p, encoding='utf-8'))) if os.path.exists(p) else []
land = land_of((w, s, e, n)); bb = to_utm(box(w, s, e, n))
fig, ax = plt.subplots(figsize=(14, 14 * (bb.bounds[3] - bb.bounds[1]) / (bb.bounds[2] - bb.bounds[0])))
ax.set_facecolor('#cfe3f5')
for g in getattr(land, 'geoms', [land]):
    if g.geom_type != 'Polygon': continue
    ax.fill(*g.exterior.xy, color='#f2f0e6', zorder=1)
    for h in g.interiors:
        ax.fill(*h.xy, color='#cfe3f5', zorder=1)
S = Streets((w, s, e, n)) if not os.environ.get('NOSTREETS') else type('E', (), {'by': {}})()
for nm, gs in S.by.items():
    for g in gs:
        ax.plot(*g.xy, color='#bbbbbb', lw=0.4, zorder=2)
    u = unary_union(gs).intersection(bb)
    if u.length >= lab and not u.is_empty:
        big = max(getattr(u, 'geoms', [u]), key=lambda t: t.length)
        q = big.interpolate(0.5, normalized=True)
        ax.text(q.x, q.y, nm[:26], fontsize=5, color='#555555', zorder=4, ha='center')
for g, in con().execute(f"select ST_AsWKB(geometry) from '{OV}/rail.parquet' where ST_XMax(geometry) >= {w} and ST_XMin(geometry) <= {e} "
                        f"and ST_YMax(geometry) >= {s} and ST_YMin(geometry) <= {n}").fetchall():
    g = to_utm(wkb.loads(bytes(g)))
    for l in getattr(g, 'geoms', [g]):
        ax.plot(*l.xy, color='#a05050', lw=0.5, zorder=2)
if os.environ.get('NAMED'):          # outlines of named land-use / land / water polygons (to choose outlines by name)
    mn = float(os.environ['NAMED'])
    for t in ('region5_land_use', 'base_land', 'base_water'):
        for nm, g in con().execute(f"select name, ST_AsWKB(geometry) from '{OV}/{t}.parquet' where name is not null and ST_XMax(geometry) >= {w} "
                                   f"and ST_XMin(geometry) <= {e} and ST_YMax(geometry) >= {s} and ST_YMin(geometry) <= {n}").fetchall():
            g = to_utm(wkb.loads(bytes(g)))
            if g.geom_type not in ('Polygon', 'MultiPolygon') or g.area < mn * 1e4 or g.area > 4e7:
                continue
            for q in getattr(g, 'geoms', [g]):
                ax.plot(*q.exterior.xy, color={'region5_land_use': '#1a7f37', 'base_land': '#8a5a00', 'base_water': '#0050b0'}[t], lw=0.7, ls=':', zorder=4)
            q = g.representative_point()
            if bb.contains(q):
                ax.text(q.x, q.y, nm[:28], fontsize=5.5, color={'region5_land_use': '#0f5f27', 'base_land': '#8a5a00', 'base_water': '#0050b0'}[t], zorder=6, ha='center')
cm = plt.get_cmap('turbo')
col = {'fill': None, 'pond_fill': '#2e8b57', 'excavation': '#0033cc', 'water_fill': '#8a2be2', 'reservoir': '#00bfff'}
for r in rd:
    if not r['zone_id'].startswith(pref):
        continue
    g = parse_ring(r['ring'])
    if not g.intersects(bb):
        continue
    y = float(r['year_end']) if float(r['year_end']) < 9000 else float(r['year_start'])
    c = col[r['kind']] or cm(min(1, max(0, (y - 1780) / 220)))
    ax.fill(*g.exterior.xy, facecolor=c, alpha=0.42, edgecolor='k', lw=1.0 if r['precision'] == 'precise' else 0.5,
            ls='-' if r['precision'] == 'precise' else '--', zorder=3)
    p = g.intersection(bb).representative_point()
    ax.text(p.x, p.y, f"{r['zone_id'].split('_', 1)[1][:24]}\n{r['year_start']}-{r['year_end']}", fontsize=6, ha='center', va='center', zorder=5)
ax.set_xlim(bb.bounds[0], bb.bounds[2]); ax.set_ylim(bb.bounds[1], bb.bounds[3]); ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
out = os.path.join(INTERIM, f'qa_{name}.png')
fig.savefig(out, dpi=int(os.environ.get('DPI', 100)), bbox_inches='tight'); print(out)
