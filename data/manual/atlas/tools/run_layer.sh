#!/bin/sh
# refine + trace every plate of a layer, in N parallel workers:  sh run_layer.sh <layer> [workers]
# logs: data/interim/atlas/<layer>/run_<k>.log
cd "$(dirname "$0")/../../../.." || exit 1
L=$1; N=${2:-2}
mkdir -p data/interim/atlas/$L
.venv/bin/python -I -c "
import json,sys
p=[str(x['id']) for x in json.load(open('data/manual/atlas/tools/layers.json'))['$L']['plates']]
n=$N
for k in range(n): print(' '.join(p[k::n]))
" | { k=0; while read ids; do
  ( for id in $ids; do
      .venv/bin/python -I data/manual/atlas/tools/atlas.py refine $L $id
      .venv/bin/python -I data/manual/atlas/tools/atlas.py trace $L $id
    done > data/interim/atlas/$L/run_$k.log 2>&1 ) &
  k=$((k+1)); done; wait; }
