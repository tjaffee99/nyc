#!/bin/sh
# usage: run_check.sh [id-substring ...]
cd /home/user/nyc/viewer && npx esbuild /home/user/nyc/data/interim/landmarks_bridges/check_entry.ts --bundle --format=esm --log-level=warning --outfile=/home/user/nyc/data/interim/landmarks_bridges/bridges_bundle.mjs && node /home/user/nyc/data/interim/landmarks_bridges/check.mjs "$@"
