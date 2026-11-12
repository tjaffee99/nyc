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
# Perris 1868 vol. 4 (plates 66-85, Williamsburgh) was tried and left out: see data/research/brooklyn_atlas3.md
B98 = json.load(open('data/manual/atlas/tools_brooklyn2/layers.json'))['brooklyn_sunsetpark_1898']['style_override']
HYDE = dict(wall_px=60, line_depth=3.5, fig_open=5, stone_min_m2=200.0, stone_min_width_m=6.0, stone_max_aspect=4.0, street_min_q=0.25, street_win_m=300.0, street_search=[30.0, 15.0], front_px=0, max_m2=20000.0)
HY05 = [15992, 15993, 15995, 15997, 15998, 15999, 16000, 16001, 16002, 16003, 16004, 16005, 16006, 16007, 16008, 16009, 16010, 16011, 16012, 16013,
        16014, 16015, 16016, 16017, 16018, 16019, 16020, 16021, 16023, 16024, 16025, 16026]
lay['brooklyn_bayridge_1905'] = L(1905, "Atlas of the borough of Brooklyn, vol. 6, Ward 30 (E. Belcher Hyde, 1905), NYPL Map Division, 100 ft to the inch", 'hyde_brooklyn_1905_v6',
     'bromley_city', HY05, HYDE, None, 'H05')
# tried and left out (could not be registered): Bromley 1899 vol. 3 plates 5-8, 15 (Coney Island), Hopkins 1880 Coney Island map, Hyde plate 19 (NYPL atlas 'Section 21')
CONEY = [16048, 16051, 16052, 16053, 16054, 16055, 16056, 16057, 16058, 16059, 16060, 16061, 16065, 16066, 16067, 16068, 16069, 16073]
lay['brooklyn_coney_1907'] = L(1907, "Atlas of the borough of Brooklyn, vol. 7, Ward 31 (E. Belcher Hyde, 1907), NYPL Map Division, 100 ft to the inch", 'hyde_brooklyn_1907_v7',
     'bromley_city', CONEY, HYDE, None, 'H07')
for _p in lay['brooklyn_old_1880']['plates']:
    if _p['id'] == 8015: _p['skip'] = 'street match left 5.2 m after a 20 m correction (control points CV rms 40 m); 18 outlines outside the Sanborn layers'
if __name__ == '__main__':
    json.dump(lay, open('data/manual/atlas/tools_brooklyn3/layers.json', 'w'), indent=1)
    print({k: len(v['plates']) for k, v in lay.items()})
