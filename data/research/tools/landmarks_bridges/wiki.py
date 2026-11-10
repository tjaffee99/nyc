import requests, re, time, os, sys
T=['Brooklyn_Bridge','Manhattan_Bridge','Williamsburg_Bridge','George_Washington_Bridge','Queensboro_Bridge','Verrazzano-Narrows_Bridge','Hell_Gate_Bridge','Robert_F._Kennedy_Bridge','High_Bridge_(New_York_City)','Bronx–Whitestone_Bridge','Throgs_Neck_Bridge','Bayonne_Bridge','Goethals_Bridge','Outerbridge_Crossing','Macombs_Dam_Bridge','Washington_Bridge','University_Heights_Bridge','Broadway_Bridge_(Manhattan)','Henry_Hudson_Bridge','Kosciuszko_Bridge','Marine_Parkway–Gil_Hodges_Memorial_Bridge','Roosevelt_Island_Bridge','Pulaski_Bridge']
S=requests.Session(); S.headers['User-Agent']='NYCThroughTime-research/0.1'
for t in T:
    fn=f'data/raw/landmarks_bridges/wiki/{t}.txt'
    if not os.path.exists(fn):
        r=S.get('https://en.wikipedia.org/w/index.php',params={'title':t,'action':'raw'},timeout=60)
        if r.status_code!=200: print('FAIL',t,r.status_code); time.sleep(3); continue
        txt=r.text
        open(fn,'w').write(txt); time.sleep(1.2)
    txt=open(fn).read()
    print('=====',t,len(txt))
    m=re.search(r'\{\{Infobox bridge(.*?)\n\}\}',txt,re.S|re.I)
    box=m.group(1) if m else txt[:3000]
    for line in box.split('\n'):
        l=line.strip()
        if re.match(r'\|\s*(length|mainspan|width|height|clearance_below|clearance_above|spans|begin|complete|open|closed|rebuilt|design|material|below|pierswater|coordinates|replaces|replaced_by|extra)\s*=',l):
            l=re.sub(r'<ref[^>]*?/>','',l); l=re.sub(r'<ref.*?</ref>','',l,flags=re.S); l=re.sub(r'<ref.*','',l)
            print('  ',l[:330])
