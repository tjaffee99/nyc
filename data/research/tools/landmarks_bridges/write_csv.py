import json, csv
d=json.load(open('data/interim/landmarks_bridges/bridges_dump.json'))
OV={
 'brooklyn_bridge':"road segments named 'Brooklyn Bridge' (trunk and secondary, bridge flag); the model runs from 947 m to 811 m either side of mid-span",
 'manhattan_bridge':"Overture carries no 'Manhattan Bridge' road name: the bridge-flagged roadways are named 'Canal Street' (primary, id 1519d579…), 'Canal Street (lower level)' (primary, f684cf92…) and 'Chrystie Street' (secondary, 9a02cc89…); subway tracks 'BMT Brighton Line' (rail, bridge flag)",
 'williamsburg_bridge':"'Williamsburg Bridge' (motorway, bridge flag) between the Manhattan plaza and the Brooklyn plaza; the segments east of -73.9617 (ids 9eedf4e9…, 85ec9159…) are the 1952 connector to the Brooklyn-Queens Expressway, not modelled: keep their generic deck; subway 'BMT Jamaica Line' (rail, bridge flag)",
 'george_washington_bridge_1931':"'George Washington Bridge Upper Level' (motorway, bridge flag)",
 'george_washington_bridge':"'George Washington Bridge Upper Level' and 'George Washington Bridge Lower Level' (motorway, bridge flag)",
 'queensboro_bridge':"'Ed Koch Queensboro Bridge Lower Level', 'Ed Koch Queensboro Bridge Lower Roadway' and 'Ed Koch Queensboro Bridge Upper Level' (trunk, bridge flag); the upper-level ramps in Queens (ids 6d11b67e…, dce1b8f7…, 8eda181e…) are not modelled: keep their generic deck",
 'verrazzano_narrows_bridge':"'Verrazzano-Narrows Bridge' (motorway, bridge flag)",
 'hell_gate_bridge':"rail segments 'Northeast Corridor' (ids fb010fe0…, d3eac7d7…) and 'Fremont Industrial Track' (68e73931…), their long bridge-flagged parts between 40.7691 N and 40.8052 N; the name is shared with the rest of the line",
 'rfk_bridge_suspension':"'Robert F. Kennedy Bridge' (motorway, bridge flag): ids c6f25955…, 255396ef…, f69b3055…",
 'rfk_bridge_harlem_river_lift':"'Robert F. Kennedy Bridge' (motorway, bridge flag): ids eca98056…, 68b53186…",
 'rfk_bridge_bronx_kill':"'Robert F. Kennedy Bridge' (motorway, bridge flag): ids 51c3eda8…, 40775599…, fa5cdb4c…, 41aa5b56…",
 'high_bridge':"not in the Overture road extracts (footpath)",
 'high_bridge_river_arches':"not in the Overture road extracts (footpath)",
 'high_bridge_steel_arch':"not in the Overture road extracts (footpath)",
 'washington_bridge':"'Washington Bridge' (primary, bridge flag)",
 'bronx_whitestone_bridge':"'Bronx-Whitestone Bridge' (motorway, bridge flag)",
 'throgs_neck_bridge':"'Throgs Neck Bridge' (motorway, bridge flag)",
 'bayonne_bridge_1931':"'Bayonne Bridge' (motorway, bridge flag)",
 'bayonne_bridge':"'Bayonne Bridge' (motorway, bridge flag)",
 'outerbridge_crossing':"'Outerbridge Crossing' (motorway, bridge flag)",
 'goethals_bridge_1928':"none today (demolished); it stood beside today's 'Goethals Bridge' segments",
 'goethals_bridge_eastbound':"'Goethals Bridge' (motorway, bridge flag): ids 7b6c0da8…, 8e15418d…",
 'goethals_bridge_westbound':"'Goethals Bridge' (motorway, bridge flag): id ea015728…",
 'macombs_dam_bridge':"'Macombs Dam Bridge' (primary / secondary, bridge flag) and the bridge-flagged part of 'West 155th Street' (primary, id fffb1161…: the 155th Street viaduct)",
 'university_heights_bridge':"'University Heights Bridge' (primary, bridge flag)",
 'broadway_bridge':"bridge-flagged segments named 'Broadway' at the Harlem River Ship Canal (primary, ids 6926ea84…, 1c19f3b6…); subway 'IRT Broadway–Seventh Avenue Line' (rail, bridge flag: the whole elevated line, only the canal crossing is modelled)",
 'henry_hudson_bridge':"bridge-flagged segments named 'Henry Hudson Parkway' at Spuyten Duyvil (motorway, ids d6042242…, b8d3d9ec…)",
 'kosciuszko_bridge_1939':"none today (demolished); drawn on the line of segment 8f4b1e93… ('Brooklyn-Queens Expressway')",
 'kosciuszko_bridge_eastbound':"bridge-flagged segment named 'Brooklyn-Queens Expressway' (motorway, id e2ac78e7…); a third carriageway line over the creek (1d3162ff…) is not modelled",
 'kosciuszko_bridge_westbound':"bridge-flagged segment named 'Brooklyn-Queens Expressway' (motorway, id 8f4b1e93…)",
 'marine_parkway_bridge':"'Marine Parkway–Gil Hodges Memorial Bridge' (primary, bridge flag)",
 'roosevelt_island_bridge':"'Roosevelt Island Bridge' (secondary, bridge flag); its western 100 m (the ramp into the Motorgate garage) is not modelled",
 'pulaski_bridge':"'Pulaski Bridge' (primary, bridge flag)",
}
rows=[]
for lm in d:
    notes='; '.join(f"{k}: {v}" for k,v in lm['facts'].items())+'; Overture names.primary: '+OV[lm['id']]
    rows.append([lm['id'],lm['name'],lm['kind'],int(lm['built'][1]),int(lm['end']) if lm['end']<9000 else 9999,f"{lm['anchor'][1]:.6f}",f"{lm['anchor'][0]:.6f}",f"{lm['zmax']:.1f}",lm['sources'][0],notes])
with open('data/tables/landmarks_bridges.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['id','name','kind','start_year','end_year','lat','lon','height_m','year_source_url','notes']); w.writerows(rows)
print(len(rows),'rows'); assert set(OV)==set(l['id'] for l in d)
for r in rows: print(r[0],r[3],r[4],r[5],r[6],r[7])
