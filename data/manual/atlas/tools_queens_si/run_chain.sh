#!/bin/sh
# trace + coarse (search 14 m) + fine (6 m) building registration of every plate of a layer without a trace yet
# usage: sh run_chain.sh <layer> [workers]
cd "$(dirname "$0")/../../../.." || exit 1
L=$1; N=${2:-2}
mkdir -p data/interim/atlas_queens_si/$L
.venv/bin/python -I -c "
import json,os
p=[str(x['id']) for x in json.load(open('data/manual/atlas/tools_queens_si/layers.json'))['$L']['plates'] if not x.get('skip')]
p=[x for x in p if not os.path.exists('data/interim/atlas_queens_si/$L/%s.pkl'%x)]
n=$N
for k in range(n): print(' '.join(p[k::n]))
" | { k=0; while read ids; do
  ( for id in $ids; do
      T=data/manual/atlas/tools_queens_si/atlas.py
      .venv/bin/python -I $T trace $L $id
      .venv/bin/python -I $T refine_buildings $L $id --search 14 --q 0.2
      .venv/bin/python -I $T refine_buildings $L $id --search 6 --q 0.2
    done >> data/interim/atlas_queens_si/$L/run_$k.log 2>&1 ) &
  k=$((k+1)); done; wait; }
