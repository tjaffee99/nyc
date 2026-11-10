"""QA plots (not committed): zones over today's land.  python qa_plot.py name w s e n [prefixes]"""
import csv, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from zonelib import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import box

name, w, s, e, n = sys.argv[1], *map(float, sys.argv[2:6])
pref = tuple(sys.argv[6].split(',')) if len(sys.argv) > 6 else ('',)
rd = list(csv.DictReader(open(os.path.join(ROOT, 'data', 'manual', 'fill_zones.csv'), encoding='utf-8')))
land = land_of((w, s, e, n)); bb = to_utm(box(w, s, e, n))
fig, ax = plt.subplots(figsize=(13, 13 * (bb.bounds[3] - bb.bounds[1]) / (bb.bounds[2] - bb.bounds[0])))
ax.set_facecolor('#cfe3f5')
for g in getattr(land, 'geoms', [land]):
    ax.fill(*g.exterior.xy, color='#f2f0e6', zorder=1)
    for h in g.interiors:
        ax.fill(*h.xy, color='#cfe3f5', zorder=1)
S = Streets((w, s, e, n))
for nm, gs in S.by.items():
    for g in gs:
        ax.plot(*g.xy, color='#bbbbbb', lw=0.4, zorder=2)
cm = plt.get_cmap('turbo')
col = {'fill': None, 'pond_fill': '#2e8b57', 'excavation': '#0033cc', 'water_fill': '#8a2be2', 'reservoir': '#00bfff'}
for r in rd:
    if not r['zone_id'].startswith(pref):
        continue
    g = parse_ring(r['ring'])
    if not g.intersects(bb):
        continue
    y = float(r['year_end']) if float(r['year_end']) < 9000 else float(r['year_start'])
    c = col[r['kind']] or cm(min(1, max(0, (y - 1680) / 320)))
    ax.fill(*g.exterior.xy, facecolor=c, alpha=0.45, edgecolor='k', lw=1.0 if r['precision'] == 'precise' else 0.5,
            ls='-' if r['precision'] == 'precise' else '--', zorder=3)
    p = g.intersection(bb).representative_point()
    ax.text(p.x, p.y, f"{r['zone_id'].split('_', 1)[1][:22]}\n{r['year_start']}-{r['year_end']}", fontsize=6, ha='center', va='center', zorder=5)
ax.set_xlim(bb.bounds[0], bb.bounds[2]); ax.set_ylim(bb.bounds[1], bb.bounds[3]); ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
out = os.path.join(INTERIM, f'qa_{name}.png')
fig.savefig(out, dpi=110, bbox_inches='tight'); print(out)
