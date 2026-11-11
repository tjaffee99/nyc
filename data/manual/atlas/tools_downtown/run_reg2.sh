#!/bin/bash
# a second pass of the building match on plates already traced:  bash run_reg2.sh <plate id> ...
cd "$(dirname "$0")/../../../.." || exit 1
L=manhattan_downtown_1897
for id in "$@"; do
  .venv/bin/python -I data/manual/atlas/tools_downtown/atlas.py refine_buildings $L $id
  echo "reg2 $id done"
done >> data/interim/atlas_downtown/$L/run2.log 2>&1
