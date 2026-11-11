import re,sys
WIKI='https://en.wikipedia.org/wiki/'
P={
'pr_lewis_library':(' Round 2: the Daily Princetonian of Sept 2008 (opened) gives the main portion as a tower of four stories above grade, with the tower reaching more than 100 feet, the Ivy Lane wing three stories and the Washington Road wing two; 32.0 m fits that, but the fact-sheet page behind the exact figure could not be opened. Footprint height (9.8 m, ms_ml) is a machine-learned value and is the wings level, so no change.',['https://www.dailyprincetonian.com/article/2008/09/lewis-library-makes-a-grand-debut']),
'pr_fine_hall':(' Round 2: the Wikipedia article on the mathematics department (opened) confirms three stories of classrooms plus ten floors of offices (13); the 170 ft figure is from the Museum page, not re-opened. Footprint height 15.4 m (ms_ml, machine-learned) is the base, no change.',[WIKI+'Department_of_Mathematics_(Princeton_University)']),
'pr_art_museum':(' Round 2: Wikipedia (opened) confirms the reopening on 31 Oct 2025, three stories and nine pavilions, 144,000-145,000 sq ft of floor; no height in metres appears on any opened page, and the footprint has no height, so 12.5 m and 18 m stay estimates.',[]),
'pr_chancellor_green':(' Round 2: the footprint carries a USGS lidar roof height of 19.7 m; the model ridge (22 m) is 12 percent above it, within the 20 percent tolerance, so no change.',[]),
'pr_holder_hall':(' Round 2: the footprint carries a USGS lidar roof height of 20.2 m for the hall, to be compared with the model eave and ridge above; no change.',[]),
'pr_jadwin_gymnasium':(' Round 2: no height appears in the Wikipedia article (opened); the footprint height (9.1 m) is machine-learned (ms_ml) and below the 12.5-18 m shells, so the shell heights remain estimates.',[]),
'pr_east_pyne_hall':(' Round 2: no opened page gives a height; the footprint height (10.8 m) is machine-learned (ms_ml) and was not used.',[]),
'pr_alexander_hall':(' Round 2: no opened page gives a height; OpenStreetMap gives three levels; the footprint height (7.5 m) is machine-learned (ms_ml) and was not used.',[]),
'connecticut_financial_center':(' Round 2: OpenStreetMap (map API, opened) has height 116 and 26 levels for this building and Overture 116.0 m, which agrees with the cited 116.7 m.',[]),
'state_street_360':(' Round 2: Wikipedia infobox (opened) gives roof 103 m and 31 floors, so the top is now cited; OpenStreetMap has height 91 (13 percent lower) and was not preferred.',[WIKI+'360_State_Street']),
'union_new_haven_trust':(' Round 2: OpenStreetMap height 74 m and Overture 74.0 m agree with the cited 73.8 m.',[]),
'kline_tower':(' Round 2: OpenStreetMap height 77 m and 16 levels agree with the cited 76.2 m.',[]),
'ingalls_rink':(' Round 2: Wikipedia (opened) confirms a maximum ceiling height of 23 m; the footprint height (7.5 m, Overture) is the wall, consistent with the 4 m wall estimate within the rim.',[WIKI+'Ingalls_Rink']),
'rudolph_hall':(' Round 2: Wikipedia (opened): seven stories with more than 30 floor levels; no height in metres on any opened page; 31 m stays an estimate.',[WIKI+'Rudolph_Hall']),
'pirelli_building_hotel_marcel':(' Round 2: Wikipedia (opened, citing the National Park Service nomination): the building is nine stories including the two-storey gap, seven excluding it; this matches the model storey count. The 36 m total remains 4 m a storey, estimated.',[WIKI+'Hotel_Marcel']),
'yale_center_british_art':(' Round 2: the footprint height (16.7 m, Overture) is what the model uses; no other height read.',[]),
'woolsey_hall':(' Round 2: no height on Wikipedia (opened), OpenStreetMap or the footprint; stays an estimate (LOW).',[]),
'battell_chapel':(' Round 2: no height on Wikipedia (opened), OpenStreetMap or the footprint; stays an estimate (LOW).',[]),
}
for fn in ['viewer/src/landmarks/princeton.ts','viewer/src/landmarks/new-haven.ts']:
    s=open(fn).read(); n=0
    for k,(suf,srcs) in P.items():
        i=s.find(f"id: '{k}'")
        if i<0: continue
        j=s.find("Model: '",i)+8
        e=j
        while True:
            if s[e]=="\\": e+=2; continue
            if s[e]=="'": break
            e+=1
        assert '\n' not in s[j:e]
        suf2=suf.replace("'","\\'")
        s=s[:e]+suf2+s[e:]
        if srcs:
            a=s.find("sources: [",e)
            b=s.find("]",a)
            s=s[:b]+''.join(f", '{u}'" for u in srcs)+s[b:]
        n+=1
    open(fn,'w').write(s); print(fn,n)
