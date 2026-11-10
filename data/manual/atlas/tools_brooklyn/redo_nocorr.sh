#!/bin/sh
# plates of a layer without a correction file: trace and building-match again
cd "$(dirname "$0")/../../../.." || exit 1
L=$1
for f in data/interim/atlas_brooklyn/$L/*.pkl; do
  id=$(basename $f .pkl)
  [ -f data/interim/atlas_brooklyn/$L/${id}_corr.json ] && continue
  .venv/bin/python -I data/manual/atlas/tools_brooklyn/atlas.py trace $L $id >> data/interim/atlas_brooklyn/$L/redo.log 2>&1
  .venv/bin/python -I data/manual/atlas/tools_brooklyn/atlas.py refine_buildings $L $id >> data/interim/atlas_brooklyn/$L/redo.log 2>&1
done
