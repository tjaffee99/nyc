import sys, json, urllib.parse, urllib.request
# usage: wd.py west south east north
w,s,e,n=sys.argv[1:5]
q=f'''SELECT ?i ?iLabel ?c ?inc ?op ?h ?art WHERE {{ SERVICE wikibase:box {{ ?i wdt:P625 ?c . bd:serviceParam wikibase:cornerSouthWest "Point({w} {s})"^^geo:wktLiteral . bd:serviceParam wikibase:cornerNorthEast "Point({e} {n})"^^geo:wktLiteral }}
 OPTIONAL{{?i wdt:P571 ?inc}} OPTIONAL{{?i wdt:P1619 ?op}} OPTIONAL{{?i wdt:P2048 ?h}} OPTIONAL{{?art schema:about ?i; schema:isPartOf <https://en.wikipedia.org/>}} SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }} }}'''
u='https://query.wikidata.org/sparql?format=json&query='+urllib.parse.quote(q)
r=urllib.request.Request(u,headers={'User-Agent':'NYCThroughTime-research/0.1'})
d=json.load(urllib.request.urlopen(r,timeout=60))
for b in d['results']['bindings']:
    g=lambda k:b.get(k,{}).get('value','')
    print(g('i').split('/')[-1],'|',g("iLabel"),'|',g('c'),'|inc',g('inc')[:10],'|op',g('op')[:10],'|h',g('h'),'|',g('art').split('/')[-1])
