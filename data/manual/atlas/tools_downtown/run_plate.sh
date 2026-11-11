#!/bin/bash
# one plate at a time: trace, then fine registration on standing buildings:  bash run_plate.sh <plate id> ...
cd "$(dirname "$0")/../../../.." || exit 1
L=manhattan_downtown_1897
for id in "$@"; do
  .venv/bin/python -I data/manual/atlas/tools_downtown/atlas.py trace $L $id
  .venv/bin/python -I data/manual/atlas/tools_downtown/atlas.py refine_buildings $L $id
  echo "plate $id done $(date +%T)"
done >> data/interim/atlas_downtown/$L/run.log 2>&1
