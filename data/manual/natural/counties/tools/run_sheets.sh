#!/bin/sh
# Classify the sixteen sheets one after the other (one process, under 1 GB). The eight coastal sheets come first:
# they have enough soil-survey labels for their own marsh / water discriminant, and their samples are pooled for
# the eight inland sheets that follow.
cd /home/user/nyc/data/manual/natural/counties/tools
/home/user/nyc/.venv/bin/python sheets.py > /home/user/nyc/data/interim/natural_counties/sheets.log 2>&1
echo "exit $?" >> /home/user/nyc/data/interim/natural_counties/sheets.log
