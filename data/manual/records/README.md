# City records used as bounds (written by pipeline/building_records.py)

Snapshots of three side lists of `building_records.py` (sources, rules and quality tables:
`data/research/building_records.md`), kept here because `nyc_buildings.py` reads them:

- `year_bounds.csv` — bin, not_before, not_after, cls: the legal class of 88,453 tenements in
  the housing department's building file (NYC Open Data `kj4p-ruqc`). An old-law tenement was
  built by April 1901 (Tenement House Act), a new-law one between then and April 1929
  (Multiple Dwelling Law), a "heretofore" erected or converted one by April 1929. Against
  exact landmark dates the classes hold in 98.6 %, 89.9 % and 99.6 % of cases.
- `dof_flagged_estimates.csv` — BINs whose year the Department of Finance's FY2017 roll flags
  as an estimate (the flag is one-way: its absence proves nothing).
- `standing_marked_for_demolition.csv` — footprints still in the city's file with a signed-off
  demolition: they get that end year.

To refresh: `cd pipeline && ../.venv/bin/python building_records.py`, then copy the lists from
`data/interim/records/` (the stage compares against the built building file).
