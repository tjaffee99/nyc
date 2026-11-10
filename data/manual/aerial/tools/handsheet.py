"""Hand-check sheets: a fixed stratified sample of footprints, shown on each mosaic without their
years, to be judged by eye (P building on the outline / A open ground / U unclear / X no photo).
  handsheet.py sample                 -> hand_sample.csv (44 per borough: 30 placeholder-year, 14 recorded)
  handsheet.py sheet YEAR K           -> hand_YEAR_K.png (56 thumbnails, rows of 8, numbered)"""
import sys, numpy as np, pandas as pd, shapely, duckdb
sys.path.insert(0, '/home/user/nyc/pipeline')
import aerial_presence as ap
from PIL import Image, ImageDraw
D = '/home/user/nyc/data/interim/aerial/'
if sys.argv[1] == 'sample':
    con = duckdb.connect()
    df = con.execute(f"select doitt_id, boro, lon, lat, start_year, year_src, year_confidence, area from '{ap.SNAPSHOT}' where area >= 50").fetchdf()
    rec = df.year_src.isin(['lpc', 'assessor']) & (df.year_confidence == 'exact')
    parts = []
    for b in ap.BORO_ORDER:
        parts.append(df[(df.boro == b) & ~rec].sample(30, random_state=5))
        parts.append(df[(df.boro == b) & rec].sample(14, random_state=5))
    s = pd.concat(parts).reset_index(drop=True)
    # shuffle within borough so that a sheet mixes recorded and placeholder years
    s['k'] = np.random.default_rng(5).random(len(s)); s['o'] = s.boro.map({b: i for i, b in enumerate(ap.BORO_ORDER)})
    s = s.sort_values(['o', 'k']).drop(columns=['k', 'o']).reset_index(drop=True)
    s.to_csv(D + 'hand_sample.csv', index=False); print(len(s), s.boro.value_counts().to_dict())
else:
    year, k = int(sys.argv[2]), int(sys.argv[3])
    s = pd.read_csv(D + 'hand_sample.csv', dtype={'doitt_id': str, 'boro': str})
    PER, NCOL, S, half = 56, 8, 4, 26
    sub = s.iloc[k * PER:(k + 1) * PER]
    con = duckdb.connect()
    ids = "','".join(sub.doitt_id)
    wk = dict(con.execute(f"select doitt_id, wkb from '{ap.SNAPSHOT}' where doitt_id in ('{ids}')").fetchall())
    W = Image.new('RGB', (NCOL * half * 2 * S, ((len(sub) + NCOL - 1) // NCOL) * half * 2 * S), (40, 0, 60))
    for n, (i, r) in enumerate(sub.iterrows()):
        geom = shapely.from_wkb(bytes(wk[r.doitt_id]))
        geom = shapely.transform(geom, lambda c: np.column_stack(ap.lonlat_to_pixel(c[:, 0], c[:, 1])))
        c = geom.centroid; cx, cy = int(c.x), int(c.y)
        x0, y0 = cx - half, cy - half
        crop = np.zeros((2 * half, 2 * half), 'float32'); ok = np.zeros((2 * half, 2 * half), bool)
        for tx in range(x0 // 256, (x0 + 2 * half - 1) // 256 + 1):
            for ty in range(y0 // 256, (y0 + 2 * half - 1) // 256 + 1):
                t = ap.read_tile(year, ap.Z, tx, ty)
                if t is None: continue
                xa, xb = max(x0, tx * 256), min(x0 + 2 * half, tx * 256 + 256); ya, yb = max(y0, ty * 256), min(y0 + 2 * half, ty * 256 + 256)
                crop[ya - y0:yb - y0, xa - x0:xb - x0] = t[0][ya - ty * 256:yb - ty * 256, xa - tx * 256:xb - tx * 256]
                ok[ya - y0:yb - y0, xa - x0:xb - x0] = t[1][ya - ty * 256:yb - ty * 256, xa - tx * 256:xb - tx * 256]
        im = Image.fromarray(crop.clip(0, 255).astype('uint8')).resize((2 * half * S, 2 * half * S), Image.BICUBIC).convert('RGB')
        if not ok.any(): im = Image.new('RGB', im.size, (90, 0, 0))
        d = ImageDraw.Draw(im)
        for poly in (geom.geoms if geom.geom_type == 'MultiPolygon' else [geom]):
            d.line([((x - x0) * S, (y - y0) * S) for x, y in np.asarray(poly.exterior.coords)], fill=(0, 255, 0), width=1)
        d.rectangle((0, 0, 30, 13), fill=(0, 0, 0)); d.text((2, 1), str(i), fill=(255, 255, 0))
        W.paste(im, ((n % NCOL) * half * 2 * S, (n // NCOL) * half * 2 * S))
    out = D + f'hand_{year}_{k}.png'; W.save(out); print(out, W.size)
