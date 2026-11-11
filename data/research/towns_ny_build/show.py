import re,sys
# usage: show.py Title [maxchars]  -> cleaned wikitext without infobox noise
t=open('/home/user/nyc/data/interim/towns_ny_raw/wp/%s.txt'%sys.argv[1]).read()
n=int(sys.argv[2]) if len(sys.argv)>2 else 3000
t=re.sub(r'<ref[^>]*?/>|<ref.*?</ref>|<!--.*?-->','',t,flags=re.S)
t=re.sub(r'\[\[(?:File|Image)[^\]]*\]\]','',t)
t=re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]',r'\1',t)
# keep infobox key lines of interest
info=[l for l in t.split('\n') if re.match(r'\|\s*(built|completed|completion_date|opened|open|construction_start_date|inauguration_date|coordinates|architect|height|floor_count|floors|style|architecture|year_built|established|founded|dedicated|groundbreaking|extra_height|roof|top|length|width|floor_area)\b',l) and l.split('=')[-1].strip()]
print('\n'.join(info))
body=t[t.find("'''"):] if "'''" in t else t
print(body[:n])
