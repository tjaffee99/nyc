"""write layers.json (run from the repo root: python -I data/manual/atlas/tools_brooklyn3/mk_layers.py)"""
import json
SRC = 'https://digitalcollections.nypl.org/ (NYPL Map Division, public domain); control points: https://s3.amazonaws.com/spacetime-nypl-org/datasets/mapwarper/mapwarper.objects.ndjson (CC0)'
names = {}
for l in open('data/raw/extents/spacetime/mapwarper.objects.ndjson'):
    o = json.loads(l)
    if isinstance(o.get('id'), (int, str)) and str(o['id']).isdigit():
        names[int(o['id'])] = (o.get('name') or '').replace('\r\n', ' ').replace('\n', ' ')
SAN = ['brooklyn_downtown_1887', 'brooklyn_southwest_1886', 'brooklyn_williamsburg_1887', 'brooklyn_greenpoint_1887', 'brooklyn_bedstuy_1888',
       'brooklyn_bushwick_1888', 'brooklyn_crownheights_1888', 'brooklyn_browns_1887', 'brooklyn_parkslope_1888']
HOP = dict(brick=dict(da_min=7.0, db_max=9.0, L_min=42), street_empty=True, street_min_q=0.2, street_win_m=300.0, street_search=[30.0, 15.0])
def L(year, atlas, source, style, ids, so=None, outside=None, prefix='H80'):
    d = dict(map_year=year, atlas=atlas, source=source, style=style, require_match=8.0, source_url=SRC,
             plates=[dict(id=i, sheet='%s-%d' % (prefix, i), name=names.get(i, '')) for i in ids])
    if so: d['style_override'] = so
    if outside: d['clip'] = dict(outside_layers=outside)
    return d
lay = {
 'brooklyn_old_1880': L(1880, "Atlas of the entire city of Brooklyn, complete in one volume (Hopkins, 1880), NYPL Map Division, scale 300 ft to the inch", 'hopkins_brooklyn_1880',
     'robinson_300ft', [7984, 7985, 7986, 7987, 7990, 7991, 7992, 7993, 7994, 7996, 8003, 8008, 8010, 8011, 8014, 8015, 8016], HOP, SAN),
}
if __name__ == '__main__':
    json.dump(lay, open('data/manual/atlas/tools_brooklyn3/layers.json', 'w'), indent=1)
    print({k: len(v['plates']) for k, v in lay.items()})
