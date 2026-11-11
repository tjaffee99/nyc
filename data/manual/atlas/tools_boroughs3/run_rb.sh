#!/bin/sh
# building match on traced plates, sequential: sh run_rb.sh <layer> [extra args e.g. --search 14]
cd "$(dirname "$0")/../../../.." || exit 1
L=$1; shift
for f in data/interim/atlas_boroughs3/$L/*.pkl; do
  id=$(basename $f .pkl)
  .venv/bin/python -I data/manual/atlas/tools_boroughs3/atlas.py refine_buildings $L $id "$@"
done > data/interim/atlas_boroughs3/$L/rb.log 2>&1
echo done >> data/interim/atlas_boroughs3/$L/rb.log
