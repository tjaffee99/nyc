# Streets of the outer counties (`pipeline/roads_outer.py`)

Run: `fetch` (2 s), `build` (about 1 minute, resumable per z12 tile; delete `data/interim/roads_outer/` and
`viewer/public/data/outer-streets/` to redo), `check`.

- Extract: `roads_local.parquet` (whole region box already; the brief's "inner box only" was not true of
  this file) filtered to residential / living_street / unclassified, middle of the street outside the inner
  box (-74.52, 40.47, -73.40, 41.38): `outer_roads_local.parquet`, 533,426 rows, 76 MB. Cross-checked with
  a live Overture query on two boxes (Suffolk 12,008 vs 12,012; Princeton 6,740 vs 6,773 rows).
- Kept: middle inside the map's outline (`extent.in_extent`), 3 m simplification: 268,542 streets.
- Year: 45 m rule (`roads._second_earliest`, year - 1) 91.4 %; else earliest building within 250 m (year - 1)
  5.9 %; else left out 2.6 %. Then `roads.after_ground`. Buildings: `county_points_outer` plus the inner
  counties' points within 0.012 deg of the inner box edge.
- Set: 573 z12 tiles 8.7 MB + 58 z10 tiles 4.6 MB = 13.3 MB (budget 60). No stubs dropped.
- Warning: `roads.py` keeps every street whose middle is in a map county (`extent.map_counties`, which now
  lists the outer counties); a rerun of `roads.py` therefore writes the outer streets into `region-streets`
  as well. Either that set stays as built, or `roads.py` must keep only inner-county rows.
