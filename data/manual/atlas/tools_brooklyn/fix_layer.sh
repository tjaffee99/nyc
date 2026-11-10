#!/bin/sh
# plates left out by export: robust control points (fix_gcps.py), then trace + register them again:  sh fix_layer.sh <layer>
cd "$(dirname "$0")/../../../.." || exit 1
L=$1
ids=$(.venv/bin/python -I -c "
import json
s=json.load(open('data/manual/atlas/${L}_stats.json'))
print(' '.join(p['plate'] for p in s['plates'] if str(p.get('status','')).startswith('left out: not placed')))")
[ -z "$ids" ] && exit 0
.venv/bin/python -I data/manual/atlas/tools_brooklyn/fix_gcps.py $L $ids | tee data/interim/atlas_brooklyn/$L/fix_gcps.log
for id in $ids; do
  if grep -q "^$id kept" data/interim/atlas_brooklyn/$L/fix_gcps.log; then
    rm -f data/interim/atlas_brooklyn/$L/$id.pkl data/interim/atlas_brooklyn/$L/${id}_corr.json
  fi
done
sh data/manual/atlas/tools_brooklyn/run_city.sh $L 2 street
