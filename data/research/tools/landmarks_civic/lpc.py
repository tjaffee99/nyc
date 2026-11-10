import json,re,sys
d=json.load(open('/home/user/nyc/data/raw/nyc/lpc_individual_landmarks.geojson'))
seen=set()
for w in sys.argv[1:]:
    for f in d['features']:
        p=f['properties']; n=(p.get('lpc_name') or '')+' / '+(p.get('lpc_altern') or '')
        if re.search(w,n,re.I) and (n,p['lpc_lpnumb']) not in seen:
            seen.add((n,p['lpc_lpnumb'])); print(f"{p['lpc_lpnumb']} | {n[:80]} | {p['landmarkty']} | {p['desdate']} | {p['borough']} {p['address']}")
