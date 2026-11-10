# New York City Through Time

An interactive 3D map of New York City with a year slider, 1609 → today: drag the year and
see what stood then — buildings, shoreline and made land, streets, railways, bridges, parks
and landmarks — with a year counter and a population counter.

**Live:** https://nyc.theojaffee.net

Built from public records wherever they exist: the city's building footprints with measured
heights, tax-lot and Landmarks Preservation Commission construction dates, fire-insurance
atlases of the 1850s–1890s traced by the New York Public Library's Building Inspector,
OpenHistoricalMap, USGS elevation, census counts back to 1698. Whatever is estimated or
generated says so: click a building to see where its year comes from. `SOURCES.md` lists
every source with its licence; `CLAUDE.md` explains how the project is put together and the
decisions behind it.

```
make setup      # python venv + npm install
make data       # downloads + every pipeline stage
make dev        # viewer at http://localhost:5173
make deploy     # build and publish to GitHub Pages
```

A port of the Bay Area map (https://bay.theojaffee.net).
