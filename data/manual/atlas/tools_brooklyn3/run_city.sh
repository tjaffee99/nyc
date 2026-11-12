#!/bin/sh
# one process at a time: street match, trace, building match, regeo, per plate. usage: sh run_city.sh <layer> [plate ...]
cd "$(dirname "$0")/../../../.." || exit 1
L=$1; shift
P="$@"; [ -z "$P" ] && P=$(.venv/bin/python -I -c "import json;print(' '.join(str(p['id']) for p in json.load(open('data/manual/atlas/tools_brooklyn3/layers.json'))['$L']['plates']))")
T=data/manual/atlas/tools_brooklyn3/atlas.py
mkdir -p data/interim/atlas_brooklyn3/$L
for id in $P; do
  [ -f data/interim/atlas_brooklyn3/$L/$id.done ] && continue
  .venv/bin/python -I $T fetch $L $id
  [ -f data/interim/atlas_brooklyn3/$L/${id}_corr.json ] || .venv/bin/python -I $T refine $L $id
  .venv/bin/python -I $T trace $L $id
  .venv/bin/python -I $T refine_buildings $L $id
  .venv/bin/python -I $T regeo $L $id
  touch data/interim/atlas_brooklyn3/$L/$id.done
  rm -f data/raw/atlas/brooklyn3/*.jpg
done >> data/interim/atlas_brooklyn3/$L/run.log 2>&1
echo ALLDONE >> data/interim/atlas_brooklyn3/$L/run.log
