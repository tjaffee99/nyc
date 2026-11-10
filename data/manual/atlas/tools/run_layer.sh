#!/bin/sh
# refine (street match; skipped with a third argument "nostreet" or when the plate has a correction) + trace every plate of a layer that has no
# trace yet, in N parallel workers:  sh run_layer.sh <layer> [workers] [nostreet]
# logs: data/interim/atlas/<layer>/run_<k>.log (appended)
cd "$(dirname "$0")/../../../.." || exit 1
L=$1; N=${2:-2}; MODE=${3:-street}
mkdir -p data/interim/atlas/$L
.venv/bin/python -I -c "
import json,os
p=[str(x['id']) for x in json.load(open('data/manual/atlas/tools/layers.json'))['$L']['plates']]
p=[x for x in p if not os.path.exists('data/interim/atlas/$L/%s.pkl'%x)]
n=$N
for k in range(n): print(' '.join(p[k::n]))
" | { k=0; while read ids; do
  ( for id in $ids; do
      [ "$MODE" = street ] && [ ! -f data/interim/atlas/$L/${id}_corr.json ] && .venv/bin/python -I data/manual/atlas/tools/atlas.py refine $L $id
      .venv/bin/python -I data/manual/atlas/tools/atlas.py trace $L $id
    done >> data/interim/atlas/$L/run_$k.log 2>&1 ) &
  k=$((k+1)); done; wait; }
