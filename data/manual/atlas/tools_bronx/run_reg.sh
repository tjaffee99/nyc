#!/bin/sh
# registration only, for plates already traced: street match (replacing any correction), then the building match
# and the recomputed ground geometry:  sh run_reg.sh <layer> [workers]
cd "$(dirname "$0")/../../../.." || exit 1
L=$1; N=${2:-2}
.venv/bin/python -I -c "
import json,os
p=[str(x['id']) for x in json.load(open('data/manual/atlas/tools_bronx/layers.json'))['$L']['plates']]
p=[x for x in p if os.path.exists('data/interim/atlas_bronx/$L/%s.pkl'%x)]
n=$N
for k in range(n): print(' '.join(p[k::n]))
" | { k=0; while read ids; do
  ( for id in $ids; do
      .venv/bin/python -I data/manual/atlas/tools_bronx/atlas.py refine $L $id
      .venv/bin/python -I data/manual/atlas/tools_bronx/atlas.py refine_buildings $L $id
    done > data/interim/atlas_bronx/$L/reg_$k.log 2>&1 ) &
  k=$((k+1)); done; wait; }
