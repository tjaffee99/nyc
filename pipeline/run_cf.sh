#!/bin/bash
# runs one place at a time: cands then select. usage: run_cf.sh pid [slabs]
cd /home/user/nyc/pipeline
pid=$1; n=${2:-1}
for ((k=0;k<n;k++)); do
  if [ "$n" = 1 ]; then ../.venv/bin/python -W ignore census_fill.py cands $pid > ../data/interim/census_fill/log_$pid.txt 2>&1
  else ../.venv/bin/python -W ignore census_fill.py cands $pid $k $n >> ../data/interim/census_fill/log_$pid.txt 2>&1; fi
done
../.venv/bin/python -W ignore census_fill.py select $pid >> ../data/interim/census_fill/log_$pid.txt 2>&1
echo finished $pid >> ../data/interim/census_fill/log_$pid.txt
