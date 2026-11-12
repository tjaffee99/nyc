#!/bin/bash
cd /home/user/nyc/pipeline
while read pid n; do
  [ -f ../data/interim/census_fill/rows_$pid.npz ] && continue
  while pgrep -f "venv/bin/python -W ignore census_fill.py" > /dev/null; do sleep 5; done
  ./run_cf.sh $pid $n
done < ../data/interim/census_fill/queue.txt
echo queue-finished > ../data/interim/census_fill/queue.done
