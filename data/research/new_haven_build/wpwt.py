import json,re,time,os,sys
from wm import jget
T=["Old Campus","Science Hill (Yale University)","Davenport College","Pierson College","Silliman College","Berkeley College, Yale University","Jonathan Edwards College","Grace Hopper College","Trumbull College","Pauli Murray College","Yale School of Medicine","Yale New Haven Hospital","Yale Divinity School","Kroon Hall","Sage Hall (Yale University)","Sloane Physics Laboratory","Kline Biology Tower","Schwarzman Center","Hendrie Hall","Hall of Graduate Studies","Cross Campus","Yale School of Architecture","Yale Peabody Museum of Natural History","Peabody Museum of Natural History","Sterling Divinity Quadrangle","Yale Bowl","Hillhouse Avenue","New Haven City Hall and County Courthouse","Connecticut Financial Center","Shubert Theatre (New Haven)","Hotel Taft (New Haven)","Wooster Square","Winchester Repeating Arms Company","Hillhouse High School","Wilbur Cross High School","Yale School of Management","Yale School of Music","Yale University Art Gallery","Smilow Cancer Hospital","Skull and Bones","Scroll and Key","Wolf's Head Society","Ives Memorial Library","Pirelli Building (New Haven)","Yale Law School","Yale School of Nursing","List of Yale University buildings","Yale University campus","Architecture of Yale University","Yale Physics Laboratory","New Haven Union Station","Church of the Redeemer, New Haven","St. Mary's Church (New Haven)","Grove Street Cemetery","National Register of Historic Places listings in New Haven, Connecticut","Yale Science Building","Yale West Campus"]
out=json.load(open('wt.json')) if os.path.exists('wt.json') else {}
for t in T:
    if t in out:continue
    J=jget('https://en.wikipedia.org/w/api.php',{'action':'parse','page':t,'prop':'wikitext','format':'json','redirects':1})
    out[t]=J.get('parse',{}).get('wikitext',{}).get('*','') if 'parse' in J else ''
    json.dump(out,open('wt.json','w'));time.sleep(1.5)
print('done',len(out))
