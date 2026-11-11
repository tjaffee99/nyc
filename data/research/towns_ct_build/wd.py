import sys, json, urllib.request, urllib.parse
# usage: wd.py out.json west south east north
w,s,e,n=sys.argv[2:6]
q=f"""SELECT ?i ?l ?c ?inc ?op ?h ?art WHERE {{
SERVICE wikibase:box {{ ?i wdt:P625 ?c . bd:serviceParam wikibase:cornerSouthWest "Point({w} {s})"^^geo:wktLiteral . bd:serviceParam wikibase:cornerNorthEast "Point({e} {n})"^^geo:wktLiteral }}
OPTIONAL {{?i wdt:P571 ?inc}} OPTIONAL {{?i wdt:P1619 ?op}} OPTIONAL {{?i wdt:P2048 ?h}}
OPTIONAL {{?art schema:about ?i; schema:isPartOf <https://en.wikipedia.org/>}}
?i rdfs:label ?l . FILTER(lang(?l)='en') }}"""
r=urllib.request.Request("https://query.wikidata.org/sparql?format=json&query="+urllib.parse.quote(q),headers={'User-Agent':'NYCThroughTime-research/0.1'})
d=json.load(urllib.request.urlopen(r,timeout=60))['results']['bindings']
json.dump(d,open(sys.argv[1],'w'))
seen=set()
for b in d:
    g=lambda k:b.get(k,{}).get('value','')
    key=(g('l'),g('inc'),g('op'))
    if key in seen: continue
    seen.add(key)
    print(g('l'),'|',g('c').replace('Point',''),'|inc',g('inc')[:10],'|op',g('op')[:10],'|h',g('h'),'|',g('art').split('/')[-1])
