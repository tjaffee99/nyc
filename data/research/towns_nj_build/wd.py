import sys,urllib.request,urllib.parse,json
w,s,e,n,out=sys.argv[1:6]
q=f"""SELECT ?i ?l ?c ?inc ?op ?h ?art WHERE {{ SERVICE wikibase:box {{ ?i wdt:P625 ?c . bd:serviceParam wikibase:cornerSouthWest "Point({w} {s})"^^geo:wktLiteral . bd:serviceParam wikibase:cornerNorthEast "Point({e} {n})"^^geo:wktLiteral }} OPTIONAL{{?i wdt:P571 ?inc}} OPTIONAL{{?i wdt:P1619 ?op}} OPTIONAL{{?i wdt:P2048 ?h}} OPTIONAL{{?art schema:about ?i; schema:isPartOf <https://en.wikipedia.org/>}} ?i rdfs:label ?l FILTER(LANG(?l)='en') }}"""
r=urllib.request.Request('https://query.wikidata.org/sparql?format=json&query='+urllib.parse.quote(q),headers={'User-Agent':'NYCThroughTime-research/0.1'})
d=json.load(urllib.request.urlopen(r,timeout=90))
json.dump(d,open(out,'w'))
for b in d['results']['bindings']:
    g=lambda k:b.get(k,{}).get('value','')
    print(g('l'),'|',g('c'),'|',g('inc')[:10],g('op')[:10],g('h'),'|',g('art').split('/')[-1])
