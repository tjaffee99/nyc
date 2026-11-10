"""Builds data/tables/places_counties.csv from places_ca..cd.txt (hand-written rows) + Wikipedia article coordinates / incorporation years.
Run from this folder: ../../../.venv/bin/python make_places_counties.py   (needs network for articles not yet cached)"""
import csv, json, os, re, sys, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import wpc
OUT = '/home/user/nyc/data/tables/places_counties.csv'
CO = {'H': ('Hudson', 'hud'), 'B': ('Bergen', 'ber'), 'E': ('Essex', 'ess'), 'U': ('Union', 'uni'), 'P': ('Passaic', 'pas'), 'W': ('Westchester', 'wes'), 'N': ('Nassau', 'nas'), 'R': ('Rockland', 'roc'), '': ('', '')}
# municipalities whose present name is younger than their incorporation, or whose article gives several dates: explicit year + note
OVERRIDE = {
 'Saddle Brook, New Jersey': (1955, 'Saddle River Township, formed in 1716, was renamed Saddle Brook in 1955.'),
 'Rochelle Park, New Jersey': (1929, 'Midland Township, formed in 1871, was renamed Rochelle Park in 1929.'),
 'South Hackensack, New Jersey': (1935, 'What was left of Lodi Township was renamed South Hackensack in 1935.'),
 'Wyckoff, New Jersey': (1926, 'Franklin Township was renamed Wyckoff in 1926; the name of the neighbourhood is far older.'),
 'Fairfield Township, Essex County, New Jersey': (1963, 'Caldwell Township, formed in 1798, was renamed Fairfield in 1963.'),
 'Berkeley Heights, New Jersey': (1951, 'New Providence Township, formed in 1809, was renamed Berkeley Heights in 1951.'),
 'Cedar Grove, New Jersey': (1908, 'Verona Township, formed in 1892, was renamed Cedar Grove in 1908.'),
 'East Rutherford, New Jersey': (1894, 'Boiling Springs Township (1889) became the borough of East Rutherford in 1894.'),
 'Woodcliff Lake, New Jersey': (1894, 'Incorporated in 1894 as the borough of Woodcliff; Woodcliff Lake since 1910.'),
 'South Nyack, New York': (1878, 'Incorporated as a village in 1878 and dissolved on 31 Mar 2022; the name remains for the hamlet in Orangetown.'),
}
def slug(s): return re.sub(r'[^a-z0-9]+', '_', s.lower().replace("'", '')).strip('_')
def full(t): return re.sub(r', NJ$', ', New Jersey', re.sub(r', NY$', ', New York', t.strip()))
rows = []
for fn in ('places_ca.txt', 'places_cb.txt', 'places_cc.txt', 'places_cd.txt'):
    for ln in open(os.path.join(HERE, fn), encoding='utf-8'):
        ln = ln.rstrip('\n')
        if not ln.strip() or ln.startswith('#'): continue
        if ln.startswith('+'):
            p = [x.strip() for x in ln[1:].split('|')]
            assert 3 <= len(p) <= 5, ln
            c, tier, title = p[0], p[1], full(p[2])
            name = re.sub(r'\s*\(.*?\)', '', title.split(',')[0]).strip()
            if name.endswith(' Township') and not name.startswith('Washington'): name = name[:-9]
            y0 = p[3] if len(p) > 3 and p[3] else '?'
            note = p[4] if len(p) > 4 else ''
            if title in OVERRIDE and y0 == '?': y0, note = str(OVERRIDE[title][0]), OVERRIDE[title][1]
            rows.append(dict(id=f'{CO[c][1]}_{slug(name)}', name=name, tier=tier, coord='', y0=y0, y1='9999', repl='', c=c, title=title, note=note))
        else:
            p = [x.strip() for x in ln.split('|')]
            assert len(p) == 10, (fn, len(p), ln[:90])
            r = dict(zip(['id', 'name', 'tier', 'coord', 'y0', 'y1', 'repl', 'c', 'title', 'note'], p)); r['title'] = full(r['title'])
            if r['coord'].startswith('@'): r['coord'] = '@' + full(r['coord'][1:])
            rows.append(r)
ids = [r['id'] for r in rows]
dup = sorted({i for i in ids if ids.count(i) > 1}); assert not dup, dup
city_ids = {r['id'] for r in csv.DictReader(open('/home/user/nyc/data/tables/places.csv', encoding='utf-8'))}
assert not (set(ids) & city_ids), set(ids) & city_ids
# ---- article texts: incorporation year for '?' rows, year check for the others
def clean(x):
    x = re.sub(r'<ref[^>]*?/>', '', x); x = re.sub(r'<ref.*?</ref>', '', x, flags=re.S); x = re.sub(r'<!--.*?-->', '', x, flags=re.S)
    return re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', x)
def inc_year(x):
    m = re.search(r'incorporated as (?:a |an )?(borough|township|city|town|village)[^.]*?\b(1[6-9]\d\d|20[012]\d)\b', x)
    if m: return int(m.group(2)), m.group(1), m.group(0)[:140]
    m = re.search(r'established_title\d?\s*=\s*[^\n]*[Ii]ncorporat[^\n]*\n\s*\|\s*established_date\d?\s*=\s*[^\n]*?\b(1[6-9]\d\d|20[012]\d)\b', x)
    if m: return int(m.group(1)), 'village', m.group(0)[-80:].replace('\n', ' ')
    m = re.search(r'\b[Ii]ncorporated[^.\n]{0,90}?\b(1[6-9]\d\d|20[012]\d)\b', x)
    if m: return int(m.group(1)), 'village', m.group(0)[-110:]
    return None
# municipalities whose article coordinates fall in woods, marsh or an airport: label moved to the centre named here
ANCHOR_FIX = {
 'hud_kearny': ('40.7650,-74.1500', 'on Kearny Avenue at the town hall'),
 'hud_secaucus': ('40.7893,-74.0567', 'at the Plaza on Paterson Plank Road'),
 'ber_mahwah': ('41.0935,-74.1460', 'at the railroad station'),
 'ber_alpine': ('40.9558,-73.9313', 'at the borough hall on Closter Dock Road'),
 'ber_east_rutherford': ('40.8339,-74.0971', 'at the borough hall'),
 'ber_englewood_cliffs': ('40.8850,-73.9500', 'on Sylvan Avenue'),
 'ber_norwood': ('40.9982,-73.9618', 'on Broadway at the borough hall'),
 'ess_west_orange': ('40.7986,-74.2391', 'on Main Street at the town hall'),
 'uni_springfield': ('@Springfield (CDP), New Jersey', ''),
 'pas_ringwood': ('@Ringwood Manor', ''),
 'pas_west_milford': ('41.1312,-74.3673', 'at the township hall on Union Valley Road'),
 'pas_bloomingdale': ('41.0020,-74.3265', 'on Main Street'),
 'roc_chestnut_ridge': ('41.0840,-74.0550', 'near the village hall on Old Nyack Turnpike'),
 'roc_bear_mountain': ('41.3105,-73.9920', 'on the east slope above Hessian Lake (the summit stands just over the Orange County line)'),
}
for r in rows:
    if r['id'] in ANCHOR_FIX:
        c, what = ANCHOR_FIX[r['id']]; r['coord'] = c
        if what: r['_anchor_note'] = f' Label hand-placed {what}.'
# ---- coordinates
CACHE = '/home/user/nyc/data/raw/tables_counties/wp_coords.json'
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
want = sorted({r['title'] for r in rows} | {r['coord'][1:] for r in rows if r['coord'].startswith('@')})
need = [t for t in want if t not in cache]
if need:
    got = wpc.coords(need)
    for t in need: cache[t] = got.get(t)
    json.dump(cache, open(CACHE, 'w'), indent=0)
problems = []; auto = []; flagged = []
out = []; src = {}
for r in rows:
    t = r['title']; x = wpc.text(t)
    if x is None or x == '': problems.append(('NO ARTICLE', r['id'], t)); x = ''
    x = clean(x)
    if r['y0'] == '?':
        got = inc_year(x)
        if not got: problems.append(('NO INCORPORATION YEAR', r['id'], t)); continue
        y, kind, snip = got
        how = 'Incorporated as a village' if r['c'] in ('W', 'N', 'R') else (f'Incorporated as a {kind}' if snip.startswith('incorporated as') or 'incorporated as' in snip else 'Incorporated')
        r['y0'] = str(y); r['note'] = f'{how} in {y} (year read from the cited article); the first use of the name was not researched - nominal start.'
        auto.append((r['id'], y, kind, snip.replace('\n', ' ')))
    else:
        ys = [r['y0']] + ([r['y1']] if r['y1'] != '9999' else [])
        miss = [y for y in ys if y != '1609' and y not in x]
        if miss and not re.search(r'estimated|nominal|approximate', r['note'], re.I):
            r['note'] = r['note'].rstrip() + f' Year {" / ".join(miss)} not found in the cited article: estimated.'
            flagged.append((r['id'], miss))
    r['note'] = r['note'].rstrip() + r.get('_anchor_note', '')
    c = r['coord']
    if c.startswith('@'):
        v = cache.get(c[1:])
        if not v or v == 'MISSING': problems.append(('NO COORDS FOR ANCHOR', r['id'], c)); v = cache.get(t); s = 'wp-article (anchor article has no coordinates)'
        else: s = 'wp-anchor: ' + c[1:]
    elif c:
        v = [float(z) for z in c.split(',')]; s = 'hand'
    else:
        v = cache.get(t); s = 'wp-article'
    if not v or v == 'MISSING': problems.append(('NO COORDS', r['id'], t)); continue
    lat, lon = float(v[0]), float(v[1])
    y0, y1 = int(r['y0']), int(r['y1'])
    assert r['tier'] in ('region', 'city', 'town', 'neighborhood', 'historic', 'landscape'), r
    assert 1609 <= y0 < y1 <= 9999, r
    if not (40.47 <= lat <= 41.38 and -74.52 <= lon <= -73.40): problems.append(('OUT OF BOX', r['id'], f'{lat:.4f},{lon:.4f}'))
    url = 'https://en.wikipedia.org/wiki/' + urllib.parse.quote(t.replace(' ', '_'), safe="_,()'-.–:")
    out.append([r['id'], r['name'], r['tier'], f'{lat:.5f}', f'{lon:.5f}', y0, y1, r['repl'], CO[r['c']][0], r['note'], url]); src[r['id']] = s
oid = {o[0] for o in out}; byid = {o[0]: o for o in out}
for o in out:
    if o[7] and o[7] not in oid: problems.append(('BAD replaced_by', o[0], o[7]))
    elif o[7] and byid[o[7]][5] != o[6]: problems.append(('chain gap', o[0], f'{o[6]} -> {o[7]} {byid[o[7]][5]}'))
with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['id', 'name', 'tier', 'lat', 'lon', 'year_start', 'year_end', 'replaced_by', 'county', 'note', 'source_url']); w.writerows(out)
json.dump(src, open(os.path.join(HERE, 'places_counties_coordsrc.json'), 'w'), indent=0)
json.dump({'auto': auto, 'flagged': flagged, 'problems': problems}, open(os.path.join(HERE, 'places_build_report.json'), 'w'), indent=0)
print('rows in', len(rows), 'written', len(out), '| auto years', len(auto), '| flagged estimated', len(flagged), '| problems', len(problems))
for p in problems: print('  PROBLEM', p)
