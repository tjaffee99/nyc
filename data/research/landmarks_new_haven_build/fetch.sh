#!/bin/bash
# fetch wikitext for titles (arguments), skipping cached
cd "$(dirname "$0")/wp"
for t in "$@"; do
  f="$t.txt"; [ -s "$f" ] && continue
  curl -s -m 30 -A "NYCThroughTime-research/0.1" "https://en.wikipedia.org/w/index.php?title=$t&action=raw" -o "$f"
  echo "$t $(wc -c < "$f")"; sleep 2
done
