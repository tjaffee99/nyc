#!/bin/bash
# usage: fetch.sh file-with-titles ; saves raw wikitext, 4.5s apart
out=/home/user/nyc/data/interim/towns_nj_raw
while read t; do
  [ -z "$t" ] && continue
  f="$out/wp_$(echo "$t" | tr -c 'A-Za-z0-9\n' '_').txt"
  [ -s "$f" ] && continue
  curl -s -m 60 -A 'NYCThroughTime-research/0.1' -o "$f" -w "%{http_code} $t\n" "https://en.wikipedia.org/w/index.php?title=$(python3 -c 'import sys,urllib.parse;print(urllib.parse.quote(urllib.parse.unquote(sys.argv[1])))' "$t")&action=raw"
  sleep 4.5
done < "$1"
