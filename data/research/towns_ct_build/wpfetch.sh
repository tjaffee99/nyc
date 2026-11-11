#!/bin/bash
# fetch wikitext for titles (args), cached in towns_ct_raw/wp, 4 s apart
cd /home/user/nyc/data/interim/towns_ct_raw/wp
for t in "$@"; do
  f="$t.txt"; [ -s "$f" ] && continue
  curl -s -m 30 -A "NYCThroughTime-research/0.1" "https://en.wikipedia.org/w/index.php?title=$t&action=raw" -o "$f"
  grep -q "Wikimedia Error" "$f" && { echo "$t FAIL"; rm "$f"; } || echo "$t $(wc -c < "$f")"; sleep 4
done
