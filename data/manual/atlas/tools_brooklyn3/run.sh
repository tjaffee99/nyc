#!/bin/sh
# sequential (one process at a time, memory): refine (street match) + trace each plate of a layer
# usage: sh run.sh <layer> [plate ...]
cd "$(dirname "$0")/../../../.." || exit 1
L=$1; shift
P="$@"; [ -z "$P" ] && P=$(.venv/bin/python -I -c "import json;print(' '.join(str(p['id']) for p in json.load(open('data/manual/atlas/tools_brooklyn3/layers.json'))['$L']['plates']))")
mkdir -p data/interim/atlas_brooklyn3/$L
for id in $P; do
  [ -f data/interim/atlas_brooklyn3/$L/$id.pkl ] && continue
  .venv/bin/python -I data/manual/atlas/tools_brooklyn3/atlas.py fetch $L $id
  [ -f data/interim/atlas_brooklyn3/$L/${id}_corr.json ] || .venv/bin/python -I data/manual/atlas/tools_brooklyn3/atlas.py refine $L $id
  .venv/bin/python -I data/manual/atlas/tools_brooklyn3/atlas.py trace $L $id
  rm -f data/raw/atlas/brooklyn3/*.jpg
done >> data/interim/atlas_brooklyn3/$L/run.log 2>&1
echo done >> data/interim/atlas_brooklyn3/$L/run.log
