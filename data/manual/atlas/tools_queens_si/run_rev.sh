#!/bin/sh
# like run_hyde.sh but one worker taking the plates from the END of the list, skipping any that already have a trace:  sh run_rev.sh <layer>
cd "$(dirname "$0")/../../../.." || exit 1
L=$1
T=data/manual/atlas/tools_queens_si/atlas.py
for id in $(.venv/bin/python -I -c "
import json
print(' '.join(str(x['id']) for x in json.load(open('data/manual/atlas/tools_queens_si/layers.json'))['$L']['plates'][::-1] if not x.get('skip')))"); do
  [ -f data/interim/atlas_queens_si/$L/$id.pkl ] && continue
  .venv/bin/python -I $T refine $L $id
  .venv/bin/python -I $T trace $L $id
  .venv/bin/python -I $T refine_buildings $L $id --search 6 --q 0.2
done >> data/interim/atlas_queens_si/$L/run_rev.log 2>&1
