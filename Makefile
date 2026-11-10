# New York City Through Time — build targets. Each pipeline stage is idempotent and caches
# its outputs (data/raw, data/interim); delete an output to force a rebuild. Heavy stages
# (buildings, terrain) run one at a time: the build machine has 16 GB.

PY := .venv/bin/python
P  := cd pipeline &&

.PHONY: setup data download overture footprints extent grid evidence land ohm aerial farmsteads counties buildings county-buildings street-trees airports terrain ground-detail cities transit roads labels audit dev build deploy

setup:
	python3 -m venv .venv
	$(PY) -m pip install -q -r pipeline/requirements.txt
	cd viewer && npm install

# everything, in dependency order
data: download overture footprints extent grid ohm aerial farmsteads counties evidence land buildings county-buildings street-trees airports terrain ground-detail labels cities transit roads audit

# NYC Open Data (footprints, PLUTO, LPC, parks), NYPL Building Inspector, MTA GTFS, TIGER
download:
	$(P) ../$(PY) download_nyc.py

# Overture extracts: buildings + OSM 3D parts of the city box; land / water, land use, roads,
# rail and every footprint of the wider box (the counties)
overture:
	$(P) ../$(PY) download_overture.py
	$(P) ../$(PY) download_overture.py region
	$(P) ../$(PY) download_overture.py region_buildings

footprints: download
	$(P) ../$(PY) footprints_raw.py

# the map's outline (the five boroughs + the counties of data/manual/extent_counties.json)
#   -> viewer/public/data/map-extent.json.  To change the counties:
#   cd pipeline && ../.venv/bin/python extent.py counties 34017 34003 ...   (state + county FIPS)
extent: download
	$(P) ../$(PY) extent.py

# elevation (USGS 3DEP) + present land cover (ESA WorldCover) on the tile lattice
grid:
	$(P) ../$(PY) terrain_grid.py

# dated outlines that prove their ground existed (landmark records, recorded years, traced maps)
evidence: footprints
	$(P) ../$(PY) nyc_buildings.py evidence

# year each cell of made land became land (natural 1609 layer + fill zones, moved back where
# dated buildings prove the ground) -> used by buildings, roads, ground detail
land: grid overture evidence
	$(P) ../$(PY) terrain_tiles.py land

# is each footprint standing on the 1924 / 1951 aerial photographs? (cached under
# data/raw/aerial; the result, data/manual/aerial/presence.parquet, is committed)
aerial: footprints
	$(P) ../$(PY) aerial_presence.py

# building marks of the 1890s USGS sheets -> data/manual/farmsteads (committed)
farmsteads: footprints
	$(P) ../$(PY) topo_farmsteads.py

# the counties' footprints with parcel years (NJ MOD-IV, NY assessment rolls)
#   -> data/interim/counties/<state>_<county>.parquet
counties:
	$(P) ../$(PY) counties_nj.py
	$(P) ../$(PY) counties_ny.py

# OpenHistoricalMap buildings of the map box -> data/manual/ohm/ (committed; only needs the
# network when data/raw/ohm is empty)
ohm: footprints
	$(P) ../$(PY) ohm_nyc.py

# 1.1 M buildings: years (LPC > assessor, heaps spread), measured heights, OSM parts;
# what stood before them (nyc_predecessors.py: atlases, OpenHistoricalMap, generated fill)
#   -> viewer/public/data/core-buildings.bin.gz (Manhattan) + region-buildings/ tiles
buildings: footprints overture grid land
	$(P) ../$(PY) nyc_buildings.py

# the counties on the map -> viewer/public/data/county-buildings/ tiles
county-buildings: land
	$(P) ../$(PY) county_buildings.py

# the city's tree inventory (884 k street and park trees): recorded planting dates, else the
# age of the trunk by species (data/research/street_trees.md); run before `terrain`
street-trees: buildings land
	$(P) ../$(PY) street_trees.py

# runways, taxiways, aprons with researched years (data/tables/airports.csv); airfield outlines
# for the terrain
airports: land
	$(P) ../$(PY) airports.py

# terrain tiles: 1609 cover -> farms -> city ground -> parks, made land, forest and today's trees
terrain: grid overture buildings airports
	$(P) ../$(PY) terrain_tiles.py

# pitches, tracks, golf, playgrounds, plazas draped on the ground + park labels
ground-detail: terrain buildings
	$(P) ../$(PY) ground_detail.py

# labels of military and industrial sites (data/manual/sites) -> park-labels.json
labels: ground-detail
	$(P) ../$(PY) nyc_extras.py

# borough and county outlines + census series for the population counter
cities: download
	$(P) ../$(PY) cities.py

# subway, elevated lines, railroads with stations and trains
transit: overture grid
	$(P) ../$(PY) transit.py

# streets dated by the buildings along them, highways in 3D, researched routes and ferries
roads: buildings terrain
	$(P) ../$(PY) roads.py

# invariants on the built building files (no start >= end, no stacked years, no doubles)
audit:
	$(P) ../$(PY) audit.py

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
