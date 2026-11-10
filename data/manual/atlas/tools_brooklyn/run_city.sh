#!/bin/sh
# city atlases (no street tint): trace, then fine registration on standing buildings, for every plate of a layer
# without a trace yet, in N workers:  sh run_city.sh <layer> [workers] [street]
# ("street": first the street match of run_layer.sh, for atlases that tint their streets)
cd "$(dirname "$0")/../../../.." || exit 1
L=$1; N=${2:-2}; MODE=${3:-nostreet}
mkdir -p data/interim/atlas_brooklyn/$L
.venv/bin/python -I -c "
import json,os
p=[str(x['id']) for x in json.load(open('data/manual/atlas/tools_brooklyn/layers.json'))['$L']['plates']]
p=[x for x in p if not os.path.exists('data/interim/atlas_brooklyn/$L/%s.pkl'%x)]
n=$N
for k in range(n): print(' '.join(p[k::n]))
" | { k=0; while read ids; do
  ( for id in $ids; do
      [ "$MODE" = street ] && .venv/bin/python -I data/manual/atlas/tools_brooklyn/atlas.py refine $L $id
      .venv/bin/python -I data/manual/atlas/tools_brooklyn/atlas.py trace $L $id
      .venv/bin/python -I data/manual/atlas/tools_brooklyn/atlas.py refine_buildings $L $id
    done >> data/interim/atlas_brooklyn/$L/run_$k.log 2>&1 ) &
  k=$((k+1)); done; wait; }
