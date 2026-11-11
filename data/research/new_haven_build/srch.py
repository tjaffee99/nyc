import json,re,sys
from wm import jget
for q in ["Schwarzman Center Yale Commons Woolsey Hall 1901","Q House Dixwell Community House New Haven","Yale Science Building 260 Whitney Avenue","101 College Street New Haven Alexion","Yale Central Power Plant Grove Street","Celentano School New Haven"]:
    J=jget('https://en.wikipedia.org/w/api.php',{'action':'query','list':'search','srsearch':q,'srlimit':3,'format':'json'})
    print('##',q)
    for r in J['query']['search']:print('  ',r['title'],'|',re.sub('<[^>]+>','',r['snippet'])[:200])
