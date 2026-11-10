#!/bin/sh
# re-run the street match of the plates of a layer; plates it corrects are traced and building-matched again
cd "$(dirname "$0")/../../../.." || exit 1
L=$1
for f in data/interim/atlas_brooklyn/$L/*.pkl; do
  id=$(basename $f .pkl)
  .venv/bin/python -I data/manual/atlas/tools_brooklyn/atlas.py refine $L $id >> data/interim/atlas_brooklyn/$L/redo.log 2>&1
  if [ -f data/interim/atlas_brooklyn/$L/${id}_corr.json ]; then
    .venv/bin/python -I data/manual/atlas/tools_brooklyn/atlas.py trace $L $id >> data/interim/atlas_brooklyn/$L/redo.log 2>&1
    .venv/bin/python -I data/manual/atlas/tools_brooklyn/atlas.py refine_buildings $L $id >> data/interim/atlas_brooklyn/$L/redo.log 2>&1
  fi
done
