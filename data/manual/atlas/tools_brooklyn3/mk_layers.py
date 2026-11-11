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
HOP = dict(brick=dict(da_min=5.5, db_max=9.0, L_min=42), street_empty=True, street_min_q=0.2, street_win_m=300.0, street_search=[30.0, 15.0])
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
SANB = dict(frame=dict(db_min=8.0, hue=0.42, L_min=50, L_max=88), brick=dict(da_min=2.0, db_max=3.0, L_min=45),
            stone=dict(da_abs=3.5, db_min=-14.0, db_max=-3.5, dL_min=-22.0, dL_max=-4.0), front_px=0, street_empty=True,
            street_min_q=0.2, street_win_m=300.0, street_search=[30.0, 15.0])
lay['brooklyn_old_1868'] = L(1868, "Insurance maps of the city of Brooklyn, L.I., vol. 4 (Williamsburgh and Greenpoint; W. Perris, 1868), NYPL Map Division, 50 ft to the inch", 'perris_brooklyn_1868',
     'bromley_city', [15776, 15777, 15778, 15779, 15780, 15781, 15782, 15783, 15784, 15785, 15786, 15787, 15789, 15790, 15791, 15792, 15793, 15794, 15795], SANB, None, 'P68')
for _p in lay['brooklyn_old_1880']['plates']:
    if _p['id'] == 8015: _p['skip'] = 'street match left 5.2 m after a 20 m correction (control points CV rms 40 m); 18 outlines outside the Sanborn layers'
if __name__ == '__main__':
    json.dump(lay, open('data/manual/atlas/tools_brooklyn3/layers.json', 'w'), indent=1)
    print({k: len(v['plates']) for k, v in lay.items()})
