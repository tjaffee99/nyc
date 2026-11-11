#!/bin/bash
cd /home/user/nyc/data/interim/towns_ny_raw/wp
for t in "$@"; do
  f="$t.txt"; [ -s "$f" ] && continue
  curl -s -m 40 -A "NYCThroughTime-research/0.1" "https://en.wikipedia.org/w/index.php?title=$t&action=raw" -o "$f"
  echo "$t $(wc -c < "$f")"; sleep 7
done
