import sys,urllib.request,urllib.parse,json
q=open(sys.argv[1]).read()
req=urllib.request.Request('https://query.wikidata.org/sparql?format=json&query='+urllib.parse.quote(q),headers={'User-Agent':'NYCThroughTime-research/0.1'})
d=json.load(urllib.request.urlopen(req,timeout=90))
for b in d['results']['bindings']: print(' | '.join(b[k]['value'].replace('http://www.wikidata.org/entity/','') for k in b))
