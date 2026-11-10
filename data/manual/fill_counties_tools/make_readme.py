"""Write data/manual/fill_counties_README.md: fixed text + tables generated from fill_zones_counties.csv."""
import collections, csv, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from zonelib import ROOT, parse_ring

rd = list(csv.DictReader(open(os.path.join(ROOT, 'data', 'manual', 'fill_zones_counties.csv'), encoding='utf-8')))
WHOLE = re.compile(r'[Ee]stimated bracket')
ONE = re.compile(r'[Ss]tart year estimated|[Ee]nd year estimated')


def conf(r):
    return 'estimated bracket' if WHOLE.search(r['note']) else ('one end estimated' if ONE.search(r['note']) else 'documented')


for r in rd:
    r['conf'] = conf(r); r['ha'] = parse_ring(r['ring']).area / 1e4
CTY = ['Hudson', 'Bergen', 'Essex', 'Union', 'Passaic', 'Westchester', 'Nassau', 'Rockland']
KIND = ['fill', 'pond_fill', 'water_fill', 'excavation', 'reservoir']
CONF = ['documented', 'one end estimated', 'estimated bracket']
cnt = collections.Counter((r['borough'], r['kind']) for r in rd)
cf = collections.Counter((r['borough'], r['conf']) for r in rd)
cc = collections.Counter(r['conf'] for r in rd)
pc = collections.Counter(r['precision'] for r in rd)
t1 = '| county | ' + ' | '.join(KIND) + ' | rows | ' + ' | '.join(CONF) + ' |\n|---|' + '---|' * (len(KIND) + 1 + len(CONF)) + '\n'
for b in CTY:
    t1 += (f'| {b} | ' + ' | '.join(str(cnt[(b, k)] or '') for k in KIND) + f' | {sum(cnt[(b, k)] for k in KIND)} | '
           + ' | '.join(str(cf[(b, c)] or '') for c in CONF) + ' |\n')
t1 += ('| **all** | ' + ' | '.join(str(sum(cnt[(b, k)] for b in CTY)) for k in KIND) + f' | {len(rd)} | ' + ' | '.join(str(cc[c]) for c in CONF) + ' |\n')
t2 = '| zone_id | county | years | kind | ring | dates | ha |\n|---|---|---|---|---|---|---|\n'
for r in rd:
    t2 += f"| `{r['zone_id']}` | {r['borough']} | {r['year_start']}–{r['year_end']} | {r['kind']} | {r['precision']} | {r['conf']} | {r['ha']:.1f} |\n"
urls = collections.Counter(r['source_url'] for r in rd)
t3 = ''.join(f'- <{u}> ({n} row{"s" if n > 1 else ""})\n' for u, n in sorted(urls.items(), key=lambda x: (-x[1], x[0])))
TEXT = open(os.path.join(os.path.dirname(__file__), 'README_body.md'), encoding='utf-8').read()
out = (TEXT.replace('{{ROWS}}', str(len(rd))).replace('{{TABLE_COUNTS}}', t1).replace('{{TABLE_ZONES}}', t2).replace('{{SOURCES}}', t3)
       .replace('{{N_DOC}}', str(cc['documented'])).replace('{{N_ONE}}', str(cc['one end estimated'])).replace('{{N_EST}}', str(cc['estimated bracket']))
       .replace('{{N_PRECISE}}', str(pc['precise'])).replace('{{N_COARSE}}', str(pc['coarse'])))
open(os.path.join(ROOT, 'data', 'manual', 'fill_counties_README.md'), 'w', encoding='utf-8').write(out)
print('README written;', dict(cc), dict(pc))
print(t1)
for k in CONF:
    print(k.upper() + ':', ' '.join(r['zone_id'] for r in rd if r['conf'] == k))
