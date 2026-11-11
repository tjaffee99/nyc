# Town specification for early_counties.csv.  One line per town:
# key|name|county|place id or lat,lon|t0|H0|P30|pop area|style|anchors|basis
# style: S Dutch stone (Bergen, Hudson, Rockland, Ulster), F frame, C city (frame, brick from 1800), N New England (frame saltbox)
# anchors: year:houses[:D] separated by ';' (D = documented in a source quoted in basis)
SPEC = """
hud_bergen|Bergen (Jersey City)|Hudson|hud_bergen|1660|15|900|hudson|S|1682:70:D|Smith 1765 (via population_counties.csv, 1682 hudson): Bergen 'a compact town', about 70 families
hud_communipaw|Communipaw|Hudson|hud_communipaw_t|1664|6|450|hudson|S|1682:20|Smith 1765 gives a village of 20 families on Bergen Neck without naming it (taken as Communipaw)
hud_harsimus|Harsimus (Paulus Hook)|Hudson|hud_harsimus|1700|3|700|hudson|S||founding of the hamlet at Harsimus; Jersey City was laid out 1804
hud_hoboken|Hoboken|Hudson|hud_hoboken_t|1784|6|350|hudson|F||Hoboken Bouwerie, Stevens' purchase 1784
ber_hackensack|Hackensack|Bergen|ber_hackensack|1686|8|700|bergen|S||Dutch church of 1686, courthouse square; Hackensack Township
ber_english_neighborhood|English Neighborhood (Ridgefield)|Bergen|ber_english_neighborhood|1668|5|180|bergen|S||settled 1668
ber_paramus|Paramus|Bergen|ber_paramus|1725|5|180|bergen|S||settled 1725
ber_schraalenburgh|Schraalenburgh (Bergenfield)|Bergen|ber_schraalenburgh|1724|6|200|bergen|S||church 1724
ber_closter|Closter|Bergen|ber_closter|1704|5|200|bergen|S||settled 1704
ess_newark|Newark|Essex|ess_newark_t|1666|30|10953|essex|N|1682:100:D|Smith 1765 (via population_counties.csv, 1682 essex): Newark 'a compact town, consisting of about one hundred families'; 1673 Dutch list of 86 men; founding cluster of 1666 about thirty families (recalled, ESTIMATE)
ess_orange|Orange (Mountain Society)|Essex|ess_orange|1730|6|1200|essex|F||Mountain Society, church 1719-1730
ess_camptown|Camptown (Irvington)|Essex|ess_camptown|1700|4|200|essex|F||settled about 1700
ess_bloomfield|Bloomfield|Essex|ess_bloomfield|1750|8|900|essex|F||Wardsesson, Presbyterian church 1796
ess_cranetown|Cranetown (Montclair)|Essex|ess_cranetown|1694|5|250|essex|F||Cranetown, settled 1694
ess_second_river|Second River (Belleville)|Essex|ess_second_river|1700|6|600|essex|F||Second River, settled about 1700
ess_caldwell|Caldwell|Essex|ess_caldwell|1750|4|400|essex|F||Horseneck, settled 1740s
uni_elizabethtown|Elizabethtown|Union|uni_elizabethtown|1664|20|3500|union|N|1682:150:D|Smith 1765 (via population_counties.csv, 1682 union): Elizabeth-Town 'supposed to consist of one hundred and fifty families'; 1673 Dutch list of 80 men
uni_connecticut_farms|Connecticut Farms (Union)|Union|uni_connecticut_farms|1667|8|300|union|F||settled 1667
uni_springfield|Springfield|Union|uni_springfield|1717|8|350|union|F||settled 1717
uni_westfield|Westfield|Union|uni_westfield|1720|6|300|union|F||settled 1720
uni_scotch_plains|Scotch Plains|Union|uni_scotch_plains|1684|5|300|union|F||settled 1684
uni_plainfield|Plainfield|Union|uni_plainfield|1750|8|500|union|F||Quaker meeting at Plainfield, village from 1788
uni_rahway|Rahway|Union|40.6080,-74.2776|1720|8|1300|union|F||Rahway, settled about 1720 (coordinates from the present town centre)
pas_acquackanonk|Acquackanonk Landing (Passaic)|Passaic|pas_acquackanonk_landing|1679|8|500|passaic|S||Acquackanonk patent 1679
pas_paterson|Paterson|Passaic|pas_paterson_t|1792|10|7596|passaic|C||Society for Useful Manufactures, 1791
pas_ringwood|Ringwood|Passaic|pas_ringwood|1742|8|300|passaic|F||Ringwood ironworks 1742
wes_yonkers|Yonkers (Philipse manor)|Westchester|wes_yonkers_t|1682|6|900|westchester|S||Philipse Manor Hall, 1682
wes_philipsburg|Philipsburg Manor, Upper Mills|Westchester|41.0905,-73.8650|1683|12|400|westchester|S||Upper Mills of Philipsburg Manor, from 1680s (position approximate)
wes_white_plains|White Plains|Westchester|wes_white_plains_t|1683|15|700|westchester|F||settled 1683
wes_new_rochelle|New Rochelle|Westchester|wes_new_rochelle_t|1688|20|600|westchester|F||Huguenot settlement 1688
wes_rye|Rye|Westchester|wes_rye|1665|15|600|westchester|N||settled 1660s
wes_eastchester|Eastchester|Westchester|wes_eastchester|1664|15|500|westchester|F||settled 1664
wes_tarrytown|Tarrytown|Westchester|wes_tarrytown|1680|3|1200|westchester|S||Philipse manor, village from 1700s
wes_dobbs_ferry|Dobbs Ferry|Westchester|wes_dobbs_ferry|1698|3|300|westchester|F||ferry from 1698
wes_peekskill|Peekskill|Westchester|wes_peekskill|1684|4|1000|westchester|F||settled 1684
wes_mamaroneck|Mamaroneck|Westchester|wes_mamaroneck|1661|5|300|westchester|F||settled 1661
wes_bedford|Bedford|Westchester|wes_bedford|1680|12|350|westchester|N||settled 1680
wes_scarsdale|Scarsdale|Westchester|wes_scarsdale|1701|3|150|westchester|F||manor 1701
wes_harrison|Harrison|Westchester|wes_harrison|1696|8|300|westchester|F||settled 1696
wes_saw_pit|Saw Pit (Port Chester)|Westchester|wes_saw_pit|1732|4|350|westchester|F||settled 1730s
wes_chappaqua|Chappaqua|Westchester|wes_chappaqua|1753|3|150|westchester|F||Quaker settlement 1753
roc_tappan|Tappan|Rockland|roc_tappan|1686|10|350|rockland|S||Tappan patent 1686
roc_haverstraw|Haverstraw|Rockland|roc_haverstraw|1700|6|700|rockland|S||Haverstraw, settled 1660s-1700s
roc_nyack|Nyack|Rockland|roc_nyack|1700|3|400|rockland|S||settled 1675
roc_tappan_slote|Tappan Slote (Piermont)|Rockland|roc_tappan_slote|1700|3|200|rockland|S||landing on the Hudson
roc_snedens_landing|Sneden's Landing|Rockland|roc_snedens_landing|1745|4|150|rockland|S||ferry from 1745
roc_new_city|New City|Rockland|roc_new_city|1798|4|200|rockland|F||county seat 1798
roc_doodletown|Doodletown|Rockland|roc_doodletown|1762|4|100|rockland|F||Doodletown, settled 1762
nas_hempstead|Hempstead|Nassau|nas_hempstead|1644|35|800|nassau|N|1644:35:D|Wikipedia (Hempstead village) via population_counties.csv: 'thirty to forty families' from Stamford founded Hempstead in 1644
nas_oyster_bay|Oyster Bay|Nassau|nas_oyster_bay|1653|12|600|nassau|N||settled 1653
nas_musketa_cove|Musketa Cove (Glen Cove)|Nassau|nas_musketa_cove|1668|5|300|nassau|F||settled 1668
nas_hempstead_harbor|Hempstead Harbor (Roslyn)|Nassau|nas_hempstead_harbor_v|1700|4|400|nassau|F||settled about 1700
nas_westbury|Westbury|Nassau|nas_westbury|1658|5|200|nassau|F||Quaker settlement 1658
nas_jericho|Jericho|Nassau|nas_jericho|1692|5|200|nassau|F||settled 1692
nas_merrick|Merrick|Nassau|nas_merrick|1643|3|150|nassau|F||settled 1643
suf_southampton|Southampton|Suffolk|suf_southampton|1640|15|800|suffolk|N||planted 1640
suf_southold|Southold|Suffolk|suf_southold|1640|15|600|suffolk|N||planted 1640
suf_east_hampton|East Hampton|Suffolk|suf_east_hampton|1648|15|700|suffolk|N||planted 1648
suf_huntington|Huntington|Suffolk|suf_huntington|1653|12|800|suffolk|N||settled 1653
suf_cold_spring_harbor|Cold Spring Harbor|Suffolk|suf_cold_spring_harbor|1653|4|300|suffolk|F||settled 1650s
suf_smithtown|Smithtown|Suffolk|suf_smithtown|1665|4|200|suffolk|F||patent 1665
suf_setauket|Setauket|Suffolk|suf_setauket|1655|12|500|suffolk|N||planted 1655
suf_stony_brook|Stony Brook|Suffolk|suf_stony_brook|1655|4|250|suffolk|F||settled 1655
suf_shelter_island|Shelter Island|Suffolk|suf_shelter_island|1652|4|200|suffolk|F||Sylvester's plantation 1652
suf_islip|Islip|Suffolk|suf_islip|1683|4|200|suffolk|F||Islip, 1683
suf_riverhead|Riverhead|Suffolk|suf_riverhead|1792|6|400|suffolk|F||county seat 1792
suf_sag_harbor|Sag Harbor|Suffolk|suf_sag_harbor|1707|3|1600|suffolk|N||whaling port
suf_port_jefferson|Port Jefferson|Suffolk|suf_port_jefferson|1682|3|300|suffolk|F||Drowned Meadow 1682
suf_bridgehampton|Bridgehampton|Suffolk|suf_bridgehampton|1656|5|300|suffolk|F||Sagaponack/Bridgehampton 1656
suf_cutchogue|Cutchogue|Suffolk|suf_cutchogue|1661|6|300|suffolk|N||settled 1661
suf_mattituck|Mattituck|Suffolk|suf_mattituck|1661|4|250|suffolk|F||Mattituck 1661
suf_brookhaven|Brookhaven (Setauket Neck)|Suffolk|suf_brookhaven|1655|4|250|suffolk|F||Brookhaven 1655
put_carmel|Carmel|Putnam|put_carmel|1795|4|250|putnam|F||Carmel, county seat later
put_garrison|Garrison (Philipstown)|Putnam|put_garrison|1738|4|200|putnam|F||Philipse patent
put_southeast|Southeast|Putnam|put_southeast|1730|4|200|putnam|F||Southeast, 1730
put_patterson|Patterson|Putnam|put_patterson|1720|4|200|putnam|F||Fredericksburgh, 1720
ora_newburgh|Newburgh|Orange|ora_newburgh|1709|6|4000|orange_ny|S||Palatine settlers 1709
ora_new_windsor|New Windsor|Orange|ora_new_windsor|1685|4|600|orange_ny|S||New Windsor, 1685
ora_goshen|Goshen|Orange|ora_goshen|1714|6|1500|orange_ny|F||Goshen 1714
ora_warwick|Warwick|Orange|ora_warwick|1712|5|600|orange_ny|F||Warwick 1712
ora_middletown|Middletown (Orange)|Orange|ora_middletown|1756|3|600|orange_ny|F||Middletown 1756
ora_port_jervis|Port Jervis (Mine Holes)|Orange|ora_port_jervis|1690|3|250|orange_ny|S||Minisink
ora_cornwall|Cornwall|Orange|ora_cornwall|1731|4|300|orange_ny|F||Cornwall 1731
ora_montgomery|Montgomery|Orange|ora_montgomery|1710|5|400|orange_ny|F||Montgomery 1710
ora_chester|Chester|Orange|ora_chester|1750|4|300|orange_ny|F||Chester 1750
dut_poughkeepsie|Poughkeepsie|Dutchess|dut_poughkeepsie|1687|6|7222|dutchess|C||Poughkeepsie 1687
dut_beacon|Fishkill Landing (Beacon)|Dutchess|dut_beacon|1709|3|1000|dutchess|F||Rombout patent 1709
dut_rhinebeck|Rhinebeck|Dutchess|dut_rhinebeck|1686|6|800|dutchess|S||Rhinebeck 1686
dut_fishkill|Fishkill|Dutchess|dut_fishkill|1714|8|800|dutchess|S||Fishkill 1714
dut_hyde_park|Hyde Park|Dutchess|dut_hyde_park|1745|4|300|dutchess|F||Hyde Park 1745
dut_pawling|Pawling|Dutchess|dut_pawling|1740|4|250|dutchess|F||Pawling 1740
dut_amenia|Amenia|Dutchess|dut_amenia|1703|3|250|dutchess|F||Amenia 1703
uls_kingston|Kingston (Esopus)|Ulster|uls_kingston|1652|25|3000|ulster|S||Esopus, stockade 1658
uls_new_paltz|New Paltz|Ulster|uls_new_paltz|1678|12|600|ulster|S|1678:12|twelve patentees (Huguenot Street), taken as one house each (recalled, ESTIMATE)
uls_saugerties|Saugerties|Ulster|uls_saugerties|1685|3|800|ulster|S||Saugerties 1685
uls_hurley|Hurley (Nieuw Dorp)|Ulster|uls_hurley|1662|20|350|ulster|S||Nieuw Dorp 1662
uls_marlborough|Marlborough|Ulster|uls_marlborough|1740|3|250|ulster|F||Marlborough 1740
uls_marbletown|Marbletown|Ulster|uls_marbletown|1669|6|250|ulster|S||Marbletown 1669
mid_perth_amboy|Perth Amboy|Middlesex|mid_perth_amboy|1683|20|1400|middlesex_nj|C||capital of East Jersey 1683
mid_new_brunswick|New Brunswick|Middlesex|mid_new_brunswick|1681|4|7800|middlesex_nj|C||Inian's Ferry 1681
mid_woodbridge|Woodbridge|Middlesex|mid_woodbridge|1666|25|700|middlesex_nj|N||Woodbridge 1666
mid_piscataway|Piscataway|Middlesex|mid_piscataway|1666|12|400|middlesex_nj|N||Piscataway 1666
mid_south_amboy|South Amboy|Middlesex|mid_south_amboy|1684|3|250|middlesex_nj|F||1684
mid_cranbury|Cranbury|Middlesex|mid_cranbury|1697|6|450|middlesex_nj|F||Cranbury 1697
mid_spotswood|Spotswood|Middlesex|mid_spotswood|1685|3|200|middlesex_nj|F||1685
mon_freehold|Freehold|Monmouth|mon_freehold|1693|4|600|monmouth|F||Freehold 1693
mon_middletown|Middletown (Monmouth)|Monmouth|mon_middletown|1664|20|500|monmouth|N||Monmouth patent 1664
mon_shrewsbury|Shrewsbury|Monmouth|mon_shrewsbury|1665|20|500|monmouth|N||Monmouth patent 1665
mon_red_bank|Red Bank|Monmouth|mon_red_bank|1736|3|700|monmouth|F||Shrewsbury Ferry 1736
mon_long_branch|Long Branch|Monmouth|mon_long_branch|1788|3|500|monmouth|F||1788
mon_allentown|Allentown|Monmouth|mon_allentown|1706|4|400|monmouth|F||1706
mon_holmdel|Holmdel|Monmouth|mon_holmdel|1700|3|150|monmouth|F||1700
mon_englishtown|Englishtown|Monmouth|mon_englishtown|1730|3|250|monmouth|F||1730
mon_tinton_falls|Tinton Falls|Monmouth|mon_tinton_falls|1672|8|300|monmouth|F||ironworks 1672
oce_toms_river|Toms River|Ocean|oce_toms_river|1740|3|400|ocean|F||1740
oce_barnegat|Barnegat|Ocean|oce_barnegat|1720|3|300|ocean|F||1720
oce_tuckerton|Tuckerton|Ocean|oce_tuckerton|1698|3|400|ocean|F||1698
som_bound_brook|Bound Brook|Somerset|som_bound_brook|1681|4|400|somerset|F||1681
som_basking_ridge|Basking Ridge|Somerset|som_basking_ridge|1717|4|300|somerset|F||1717
som_pluckemin|Pluckemin|Somerset|som_pluckemin|1730|3|150|somerset|F||1730
mor_morristown|Morristown|Morris|mor_morristown|1715|8|1500|morris|N||Morristown 1715
mor_dover|Dover (Morris)|Morris|mor_dover|1722|4|400|morris|F||Dover ironworks 1722
mor_mendham|Mendham|Morris|mor_mendham|1710|4|250|morris|F||1710
mor_madison|Madison (Bottle Hill)|Morris|mor_madison|1685|4|300|morris|F||1685
mor_boonton|Boonton|Morris|mor_boonton|1747|3|250|morris|F||ironworks 1747
mor_whippany|Whippany|Morris|mor_whippany|1710|4|250|morris|F||1710
sus_newton|Newton|Sussex|sus_newton|1751|5|900|sussex|F||Newton 1751
sus_sparta|Sparta|Sussex|sus_sparta|1715|3|200|sussex|F||1715
hun_flemington|Flemington|Hunterdon|hun_flemington|1756|4|700|hunterdon|F||Flemington 1756
hun_lambertville|Lambertville|Hunterdon|hun_lambertville|1732|3|900|hunterdon|F||Coryell's Ferry 1732
hun_clinton|Clinton|Hunterdon|hun_clinton|1730|3|450|hunterdon|F||1730
hun_high_bridge|High Bridge|Hunterdon|hun_high_bridge|1742|4|350|hunterdon|F||ironworks 1742
mer_trenton|Trenton|Mercer|mer_trenton|1679|5|3925|hunterdon|C||Stacy's mill 1679, Trent's town 1714
mer_princeton|Princeton|Mercer|mer_princeton|1683|5|1300|hunterdon|N||Stony Brook settlement 1683
mer_hightstown|Hightstown|Mercer|mer_hightstown|1721|3|450|hunterdon|F||1721
mer_hopewell|Hopewell|Mercer|mer_hopewell|1699|3|350|hunterdon|F||1699
mer_pennington|Pennington|Mercer|mer_pennington|1700|3|300|hunterdon|F||1700
mer_lawrenceville|Lawrenceville|Mercer|mer_lawrenceville|1697|3|300|hunterdon|F||1697
brg_bridgeport|Bridgeport (Pequonnock)|Greater Bridgeport|brg_bridgeport|1700|4|2800|fairfield_ct|N||Pequonnock farms 1639
brg_fairfield|Fairfield|Greater Bridgeport|brg_fairfield|1639|25|1200|fairfield_ct|N||Fairfield 1639
brg_stratford|Stratford|Greater Bridgeport|brg_stratford|1639|20|1000|fairfield_ct|N||Stratford 1639
brg_southport|Southport|Greater Bridgeport|brg_southport|1700|3|500|fairfield_ct|N||Mill River 1700
wct_greenwich|Greenwich|Western Connecticut|wct_greenwich|1640|15|800|fairfield_ct|N||Greenwich 1640
wct_stamford|Stamford|Western Connecticut|wct_stamford|1641|30|1500|fairfield_ct|N||Stamford 1641
wct_norwalk|Norwalk|Western Connecticut|wct_norwalk|1649|15|2500|fairfield_ct|N||Norwalk 1649
wct_danbury|Danbury|Western Connecticut|wct_danbury|1685|8|2500|fairfield_ct|N||Danbury 1685
wct_ridgefield|Ridgefield|Western Connecticut|wct_ridgefield|1708|10|500|fairfield_ct|N||Ridgefield 1708
wct_redding|Redding|Western Connecticut|wct_redding|1714|4|200|fairfield_ct|N||1714
wct_newtown|Newtown|Western Connecticut|wct_newtown|1705|8|450|fairfield_ct|N||Newtown 1705
scc_new_haven|New Haven|South Central Connecticut|scc_new_haven|1638|80|10180|new_haven_ct|N||Eaton-Davenport colony 1638; nine squares of 1641
scc_milford|Milford (CT)|South Central Connecticut|scc_milford|1639|25|1000|new_haven_ct|N||Milford 1639
scc_west_haven|West Haven|South Central Connecticut|scc_west_haven|1648|6|350|new_haven_ct|N||1648
scc_branford|Branford|South Central Connecticut|scc_branford|1644|20|600|new_haven_ct|N||Branford 1644
scc_guilford|Guilford|South Central Connecticut|scc_guilford|1639|30|900|new_haven_ct|N||Guilford 1639
scc_madison|Madison (CT)|South Central Connecticut|scc_madison|1650|4|350|new_haven_ct|N||Hammonasset 1650
scc_wallingford|Wallingford|South Central Connecticut|scc_wallingford|1670|30|1000|new_haven_ct|N||Wallingford 1670
scc_east_haven|East Haven|South Central Connecticut|scc_east_haven|1707|6|350|new_haven_ct|N||East Haven 1707
scc_cheshire|Cheshire|South Central Connecticut|scc_cheshire|1694|5|450|new_haven_ct|N||Cheshire 1694
pik_milford|Milford (PA)|Pike|pik_milford|1796|6|250|sussex|F||Milford PA 1796
pik_dingmans_ferry|Dingmans Ferry|Pike|pik_dingmans_ferry|1735|3|100|sussex|F||1735
"""
