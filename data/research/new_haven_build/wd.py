import requests,json
q='''SELECT ?i ?l ?c ?inc ?op ?sd WHERE {
SERVICE wikibase:box { ?i wdt:P625 ?c . bd:serviceParam wikibase:cornerSouthWest "Point(-72.9906 41.2345)"^^geo:wktLiteral . bd:serviceParam wikibase:cornerNorthEast "Point(-72.8612 41.3497)"^^geo:wktLiteral }
OPTIONAL{?i wdt:P571 ?inc} OPTIONAL{?i wdt:P1619 ?op} OPTIONAL{?i wdt:P580 ?sd}
FILTER(BOUND(?inc)||BOUND(?op))
?i rdfs:label ?l FILTER(lang(?l)='en') }'''
r=requests.get('https://query.wikidata.org/sparql',params={'query':q,'format':'json'},headers={'User-Agent':'NYCThroughTime-research/0.1'},timeout=120)
print(r.status_code)
rows=[]
for b in r.json()['results']['bindings']:
    g=lambda k:b.get(k,{}).get('value','')
    rows.append((g('i').split('/')[-1],g('l'),g('c'),g('inc')[:10],g('op')[:10]))
json.dump(rows,open('wd.json','w'))
print(len(rows))
for x in sorted(rows,key=lambda x:x[1]):print(x[0],x[1],x[2][6:-1],x[3],x[4])
