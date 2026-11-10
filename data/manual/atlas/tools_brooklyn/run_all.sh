#!/bin/sh
# fetch then trace + register every plate of the given layers, 2 workers each:  sh run_all.sh <layer> [<layer> ...]
cd "$(dirname "$0")/../../../.." || exit 1
for L in "$@"; do
  .venv/bin/python -I data/manual/atlas/tools_brooklyn/atlas.py fetch $L
  sh data/manual/atlas/tools_brooklyn/run_city.sh $L 2 street
done
