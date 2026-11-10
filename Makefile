# New York City Through Time — build targets. Each pipeline stage is idempotent and caches
# its outputs (data/raw, data/interim); delete an output to force a rebuild. Heavy stages
# (buildings, terrain) run one at a time: the build machine has 16 GB.

PY := .venv/bin/python
P  := cd pipeline &&

.PHONY: setup data download overture footprints extent grid land buildings terrain cities transit dev build deploy

setup:
	python3 -m venv .venv
	$(PY) -m pip install -q -r pipeline/requirements.txt
	cd viewer && npm install

# everything, in dependency order
data: download overture footprints extent grid buildings terrain cities transit

# NYC Open Data (footprints, PLUTO, LPC, parks), NYPL Building Inspector, MTA GTFS, TIGER
download:
	$(P) ../$(PY) download_nyc.py

# Overture extracts of the map box: buildings + OSM 3D parts, land / water, land use, roads, rail
overture:
	$(P) ../$(PY) download_overture.py

footprints: download
	$(P) ../$(PY) footprints_raw.py

# the map's outline (five boroughs) -> viewer/public/data/map-extent.json
extent: download
	$(P) ../$(PY) extent.py

# elevation (USGS 3DEP) + present land cover (ESA WorldCover) on the tile lattice
grid:
	$(P) ../$(PY) terrain_grid.py

# year each cell of made land became land (natural 1609 layer + fill zones) -> used by buildings
land: grid overture
	$(P) ../$(PY) terrain_tiles.py land

# 1.1 M buildings: years (LPC > assessor, heaps spread), measured heights, OSM parts
#   -> viewer/public/data/core-buildings.bin.gz (Manhattan) + region-buildings/ tiles
buildings: footprints overture grid land
	$(P) ../$(PY) nyc_buildings.py

# terrain tiles: 1609 cover -> farms -> city ground -> parks, made land, forest and today's trees
terrain: grid overture buildings
	$(P) ../$(PY) terrain_tiles.py

# borough outlines + census series for the population counter
cities: download
	$(P) ../$(PY) cities.py

# subway, elevated lines, railroads with stations and trains
transit: overture grid
	$(P) ../$(PY) transit.py

# ---- viewer ----------------------------------------------------------------
dev:
	cd viewer && npm run dev

build:
	cd viewer && npm run build

# Publish viewer/dist to the gh-pages branch, served at https://nyc.theojaffee.net
# (viewer/public/CNAME). The branch holds one generated commit, replaced on each
# deploy, so built data doesn't pile up in history: pipeline/deploy.py makes that
# commit in a temporary git directory; nothing in the repo is touched.
deploy: build
	$(PY) pipeline/deploy.py
