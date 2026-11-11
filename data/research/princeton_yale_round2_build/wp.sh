#!/bin/bash
# usage: wp.sh Title...   (cached, 4s apart)
cd /home/user/nyc/data/interim/princeton_yale_round2_raw
for t in "$@"; do
 f="wp_$(echo "$t"|tr ' /' '__').txt"
 [ -s "$f" ] && continue
 curl -sS -m 40 -A 'NYCThroughTime-research/0.1' "https://en.wikipedia.org/w/index.php?title=$(echo "$t"|tr ' ' '_')&action=raw" -o "$f" -w "$t %{http_code} %{size_download}\n"
 sleep 4
done
