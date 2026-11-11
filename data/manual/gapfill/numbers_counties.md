# gap_fill.py counties: checks

Rows: 71321. Made 2026-11-11 01:04 from the snapshot of the county buildings taken 2026-11-11 00:08.

## Rows by county and evidence

| county | evidence | rows | median start | median end |
|---|---|---|---|---|
| Bergen | parcel_neighbourhood | 6054 | 1931 | 1994 |
| Bergen | parcel_neighbourhood+usgs1943_blocks | 372 | 1925 | 1986 |
| Bergen | parcel_neighbourhood+usgs1947_blocks | 222 | 1930 | 2005 |
| Bergen | usgs1897_builtup | 1517 | 1882 | 1920 |
| Bergen | usgs1897_builtup+parcel_neighbourhood | 143 | 1876 | 1986 |
| Bergen | usgs1897_builtup+parcel_neighbourhood+usgs1943_blocks | 6 | 1866 | 1995 |
| Bergen | usgs1897_builtup+parcel_neighbourhood+usgs1947_blocks | 12 | 1878 | 1998 |
| Bergen | usgs1897_builtup+usgs1943_blocks | 78 | 1876 | 1973 |
| Bergen | usgs1897_builtup+usgs1947_blocks | 182 | 1881 | 1998 |
| Bergen | usgs1897_builtup+usgs1947_tint | 7 | 1891 | 1961 |
| Bergen | usgs1943_blocks | 1686 | 1924 | 1965 |
| Bergen | usgs1944_tint | 720 | 1927 | 1953 |
| Bergen | usgs1947_blocks | 3736 | 1925 | 1977 |
| Bergen | usgs1947_tint | 463 | 1928 | 1952 |
| Essex | parcel_neighbourhood | 8878 | 1926 | 1968 |
| Essex | parcel_neighbourhood+usgs1947_blocks | 917 | 1924 | 1952 |
| Essex | usgs1897_builtup | 3138 | 1878 | 1916 |
| Essex | usgs1897_builtup+parcel_neighbourhood | 346 | 1878 | 1980 |
| Essex | usgs1897_builtup+parcel_neighbourhood+usgs1947_blocks | 52 | 1876 | 1996 |
| Essex | usgs1897_builtup+usgs1947_blocks | 1181 | 1882 | 1990 |
| Essex | usgs1897_builtup+usgs1947_tint | 674 | 1875 | 1970 |
| Essex | usgs1947_blocks | 5910 | 1913 | 1978 |
| Essex | usgs1947_tint | 1535 | 1924 | 1957 |
| Passaic | parcel_neighbourhood | 1759 | 1926 | 1985 |
| Passaic | parcel_neighbourhood+usgs1943_blocks | 3 | 1928 | 1981 |
| Passaic | usgs1897_builtup | 715 | 1885 | 1926 |
| Passaic | usgs1897_builtup+parcel_neighbourhood | 28 | 1886 | 1974 |
| Passaic | usgs1897_builtup+usgs1943_blocks | 51 | 1885 | 1977 |
| Passaic | usgs1897_builtup+usgs1944_tint | 50 | 1886 | 1968 |
| Passaic | usgs1897_builtup+usgs1947_tint | 47 | 1880 | 1959 |
| Passaic | usgs1943_blocks | 344 | 1920 | 1971 |
| Passaic | usgs1944_tint | 1157 | 1925 | 1955 |
| Passaic | usgs1947_tint | 487 | 1923 | 1958 |
| Rockland | parcel_neighbourhood | 2010 | 1929 | 1989 |
| Rockland | parcel_neighbourhood+usgs1943_blocks | 185 | 1895 | 1987 |
| Rockland | usgs1943_blocks | 1444 | 1921 | 1971 |
| Union | parcel_neighbourhood | 5208 | 1930 | 1992 |
| Union | parcel_neighbourhood+usgs1947_blocks | 409 | 1923 | 1998 |
| Union | usgs1897_builtup | 598 | 1880 | 1912 |
| Union | usgs1897_builtup+parcel_neighbourhood | 102 | 1877 | 1981 |
| Union | usgs1897_builtup+parcel_neighbourhood+usgs1947_blocks | 40 | 1880 | 2005 |
| Union | usgs1897_builtup+usgs1947_blocks | 261 | 1883 | 1999 |
| Union | usgs1947_blocks | 1263 | 1920 | 1976 |
| Westchester | parcel_neighbourhood | 8958 | 1929 | 1985 |
| Westchester | parcel_neighbourhood+usgs1947_blocks | 1173 | 1925 | 1983 |
| Westchester | usgs1897_builtup | 1478 | 1890 | 1922 |
| Westchester | usgs1897_builtup+parcel_neighbourhood | 421 | 1881 | 1971 |
| Westchester | usgs1897_builtup+parcel_neighbourhood+usgs1947_blocks | 112 | 1870 | 1972 |
| Westchester | usgs1897_builtup+usgs1947_blocks | 235 | 1870 | 1968 |
| Westchester | usgs1943_blocks | 38 | 1926 | 1968 |
| Westchester | usgs1947_blocks | 4916 | 1926 | 1965 |

| county | rows |
|---|---|
| Bergen | 15198 |
| Essex | 22631 |
| Passaic | 4641 |
| Rockland | 3639 |
| Union | 7881 |
| Westchester | 17331 |

## What dates the end

| end basis | rows |
|---|---|
| replaced_by_standing | 62111 |
| estimated | 7130 |
| highway | 2080 |

Parcels 1082760, with some evidence 227868. Rows anchored by: the parcel rule 37418, a 1940s sheet's block fronts 21341, a 1940s tint 5140, the built-up ground of 1897 alone 7446 (before the last guards). Outlines read on a 1940s sheet 296018, of them on heavy ink with built neighbours 26991. Dropped at the last guard: 25 on a map building, 24 on another row. Rows that wait for their ground: 474. Blocks that failed: 0.

## Test places: buildings standing on the map, before -> after the fill

| place | 1850 | 1880 | 1900 | 1925 | 1950 | 1975 | fill rows by evidence |
|---|---|---|---|---|---|---|---|
| Newark, downtown (Broad and Market) | 76 -> 104 | 431 -> 717 | 557 -> 872 | 749 -> 1143 | 810 -> 1291 | 829 -> 1072 | usgs1947_blocks 403, usgs1897_builtup+usgs1947_blocks 67, usgs1897_builtup 16, parcel_neighbourhood 12, parcel_neighbourhood+usgs1947_blocks 4 |
| Newark, the Ironbound | 114 -> 180 | 1130 -> 1440 | 2040 -> 2561 | 3518 -> 4103 | 3970 -> 4618 | 4247 -> 4734 | usgs1947_blocks 463, usgs1897_builtup 197, usgs1897_builtup+usgs1947_blocks 108, parcel_neighbourhood+usgs1947_blocks 37, parcel_neighbourhood 32, usgs1897_builtup+parcel_neighbourhood+usgs1947_blocks 14, usgs1897_builtup+parcel_neighbourhood 8 |
| Paterson, centre | 31 -> 31 | 336 -> 370 | 605 -> 707 | 997 -> 1091 | 1480 -> 1515 | 1687 -> 1716 | usgs1897_builtup 60, usgs1897_builtup+usgs1944_tint 17, usgs1944_tint 16, parcel_neighbourhood 9, usgs1897_builtup+parcel_neighbourhood 1 |
| Elizabeth, centre | 68 -> 80 | 357 -> 615 | 1052 -> 1493 | 2061 -> 2597 | 2366 -> 2950 | 2635 -> 3079 | usgs1947_blocks 278, usgs1897_builtup 238, usgs1897_builtup+usgs1947_blocks 117, parcel_neighbourhood 95, parcel_neighbourhood+usgs1947_blocks 60, usgs1897_builtup+parcel_neighbourhood 24, usgs1897_builtup+parcel_neighbourhood+usgs1947_blocks 15 |
| Elizabethport | 13 -> 13 | 65 -> 84 | 659 -> 811 | 1246 -> 1495 | 1380 -> 1651 | 1411 -> 1634 | usgs1947_blocks 222, usgs1897_builtup 81, usgs1897_builtup+usgs1947_blocks 70, parcel_neighbourhood 13, parcel_neighbourhood+usgs1947_blocks 7, usgs1897_builtup+parcel_neighbourhood 1 |
| Hackensack | 2 -> 3 | 12 -> 116 | 45 -> 234 | 1017 -> 1185 | 1572 -> 1767 | 2131 -> 2295 | parcel_neighbourhood 144, usgs1897_builtup 128, usgs1897_builtup+parcel_neighbourhood 59 |
| Yonkers (Getty Square) | 4 -> 41 | 36 -> 173 | 520 -> 967 | 1043 -> 1693 | 1424 -> 2001 | 1738 -> 1975 | parcel_neighbourhood 247, usgs1897_builtup 195, usgs1947_blocks 144, usgs1897_builtup+parcel_neighbourhood 89, parcel_neighbourhood+usgs1947_blocks 76, usgs1897_builtup+parcel_neighbourhood+usgs1947_blocks 37, usgs1897_builtup+usgs1947_blocks 34 |
| Mount Vernon | 0 -> 5 | 0 -> 34 | 44 -> 170 | 646 -> 796 | 3018 -> 3185 | 4130 -> 4219 | usgs1947_blocks 106, usgs1897_builtup+usgs1947_blocks 49, usgs1897_builtup 37, parcel_neighbourhood 10, parcel_neighbourhood+usgs1947_blocks 6, usgs1897_builtup+parcel_neighbourhood 1 |
| New Rochelle | 0 -> 12 | 311 -> 377 | 653 -> 788 | 1510 -> 1712 | 2190 -> 2415 | 2638 -> 2751 | usgs1947_blocks 126, parcel_neighbourhood 51, usgs1897_builtup 49, usgs1897_builtup+usgs1947_blocks 43, parcel_neighbourhood+usgs1947_blocks 8, usgs1897_builtup+parcel_neighbourhood 6, usgs1897_builtup+parcel_neighbourhood+usgs1947_blocks 1 |
| White Plains | 1 -> 1 | 1 -> 1 | 6 -> 6 | 262 -> 297 | 905 -> 1052 | 1291 -> 1364 | usgs1947_blocks 110, parcel_neighbourhood 30, parcel_neighbourhood+usgs1947_blocks 8 |
| Nyack | 70 -> 75 | 332 -> 370 | 731 -> 1003 | 1290 -> 1643 | 1729 -> 2203 | 2013 -> 2293 | parcel_neighbourhood 261, usgs1943_blocks 125, parcel_neighbourhood+usgs1943_blocks 109 |
| Haverstraw | 23 -> 28 | 189 -> 233 | 408 -> 535 | 602 -> 771 | 778 -> 958 | 1040 -> 1121 | usgs1943_blocks 95, parcel_neighbourhood 76, parcel_neighbourhood+usgs1943_blocks 21 |

## Against the census (an upper check)

| area | year | population | map | fill | persons per building before -> after |
|---|---|---|---|---|---|
| Bergen County | 1850 | 15,169 | 488 | 127 | 31.1 -> 24.7 |
| Bergen County | 1880 | 36,786 | 2015 | 1120 | 18.3 -> 11.7 |
| Bergen County | 1900 | 78,441 | 7332 | 2515 | 10.7 -> 8.0 |
| Bergen County | 1920 | 210,703 | 31187 | 4660 | 6.8 -> 5.9 |
| Bergen County | 1950 | 539,139 | 121726 | 12446 | 4.4 -> 4.0 |
| Essex County | 1850 | 57,410 | 1018 | 471 | 56.4 -> 38.6 |
| Essex County | 1880 | 189,929 | 7966 | 3852 | 23.8 -> 16.1 |
| Essex County | 1900 | 359,053 | 17343 | 7298 | 20.7 -> 14.6 |
| Essex County | 1920 | 652,089 | 46000 | 10897 | 14.2 -> 11.5 |
| Essex County | 1950 | 905,949 | 116225 | 17845 | 7.8 -> 6.8 |
| Passaic County | 1850 | 22,569 | 221 | 60 | 102.1 -> 80.3 |
| Passaic County | 1880 | 68,860 | 1610 | 458 | 42.8 -> 33.3 |
| Passaic County | 1900 | 155,202 | 6269 | 1388 | 24.8 -> 20.3 |
| Passaic County | 1920 | 259,174 | 17638 | 2104 | 14.7 -> 13.1 |
| Passaic County | 1950 | 337,093 | 57006 | 3284 | 5.9 -> 5.6 |
| Union County | 1850 | 16,540 | 705 | 45 | 23.5 -> 22.1 |
| Union County | 1880 | 55,571 | 2714 | 601 | 20.5 -> 16.8 |
| Union County | 1900 | 99,353 | 8058 | 1309 | 12.3 -> 10.6 |
| Union County | 1920 | 200,157 | 21764 | 2416 | 9.2 -> 8.3 |
| Union County | 1950 | 398,138 | 77440 | 6949 | 5.1 -> 4.7 |
| Westchester County | 1850 | 50,231 | 1271 | 202 | 39.5 -> 34.1 |
| Westchester County | 1880 | 98,634 | 4484 | 1100 | 22.0 -> 17.7 |
| Westchester County | 1900 | 184,257 | 12060 | 3057 | 15.3 -> 12.2 |
| Westchester County | 1920 | 344,436 | 32362 | 5545 | 10.6 -> 9.1 |
| Westchester County | 1950 | 625,816 | 109478 | 14992 | 5.7 -> 5.0 |
| Rockland County | 1850 | 16,962 | 1021 | 166 | 16.6 -> 14.3 |
| Rockland County | 1880 | 27,690 | 3078 | 426 | 9.0 -> 7.9 |
| Rockland County | 1900 | 38,298 | 5848 | 934 | 6.5 -> 5.6 |
| Rockland County | 1920 | 45,548 | 9040 | 1491 | 5.0 -> 4.3 |
| Rockland County | 1950 | 89,276 | 19109 | 3534 | 4.7 -> 3.9 |
| Yonkers | 1880 | 18,892 | 241 | 399 | 78.4 -> 29.5 |
| Yonkers | 1900 | 47,931 | 2497 | 1626 | 19.2 -> 11.6 |
| Yonkers | 1920 | 100,176 | 9873 (1925) | 2979 | 10.1 -> 7.8 |
| Yonkers | 1950 | 152,798 | 19699 | 5196 | 7.8 -> 6.1 |
| Mount Vernon | 1880 | 4,586 | 2 | 54 | 2293.0 -> 81.9 |
| Mount Vernon | 1900 | 21,228 | 80 | 170 | 265.4 -> 84.9 |
| Mount Vernon | 1920 | 42,726 | 1591 (1925) | 212 | 26.9 -> 23.7 |
| Mount Vernon | 1950 | 71,899 | 7675 | 300 | 9.4 -> 9.0 |
| New Rochelle | 1880 | 5,276 | 535 | 130 | 9.9 -> 7.9 |
| New Rochelle | 1900 | 14,720 | 1406 | 311 | 10.5 -> 8.6 |
| New Rochelle | 1920 | 36,213 | 4680 (1925) | 428 | 7.7 -> 7.1 |
| New Rochelle | 1950 | 59,725 | 9641 | 809 | 6.2 -> 5.7 |
| White Plains | 1880 | 2,381 | 11 | 0 | 216.5 -> 216.5 |
| White Plains | 1900 | 7,899 | 50 | 0 | 158.0 -> 158.0 |
| White Plains | 1920 | 21,031 | 1411 (1925) | 34 | 14.9 -> 14.6 |
| White Plains | 1950 | 43,366 | 6691 | 704 | 6.5 -> 5.9 |
| Port Chester | 1880 | 3,254 | 357 | 4 | 9.1 -> 9.0 |
| Port Chester | 1900 | 7,440 | 1351 | 8 | 5.5 -> 5.5 |
| Port Chester | 1920 | 16,573 | 2652 (1925) | 47 | 6.2 -> 6.1 |
| Port Chester | 1950 | 23,970 | 4151 | 325 | 5.8 -> 5.4 |
| Ossining, Village | 1880 | 6,578 | 0 | 0 | 6578.0 -> 6578.0 |
| Ossining, Village | 1900 | 7,939 | 21 | 0 | 378.0 -> 378.0 |
| Ossining, Village | 1920 | 10,739 | 1226 (1925) | 0 | 8.8 -> 8.8 |
| Ossining, Village | 1950 | 16,098 | 2467 | 0 | 6.5 -> 6.5 |
| Peekskill | 1880 | 6,893 | 9 | 0 | 765.9 -> 765.9 |
| Peekskill | 1900 | 10,358 | 23 | 0 | 450.3 -> 450.3 |
| Peekskill | 1920 | 15,868 | 1192 (1925) | 0 | 13.3 -> 13.3 |
| Peekskill | 1950 | 17,731 | 2265 | 0 | 7.8 -> 7.8 |
| Tarrytown | 1880 | 3,025 | 0 | 0 | 3025.0 -> 3025.0 |
| Tarrytown | 1900 | 4,770 | 0 | 0 | 4770.0 -> 4770.0 |
| Tarrytown | 1920 | 5,807 | 560 (1925) | 6 | 10.4 -> 10.3 |
| Tarrytown | 1950 | 8,851 | 1167 | 26 | 7.6 -> 7.4 |
| Nyack | 1880 | 3,881 | 181 | 15 | 21.4 -> 19.8 |
| Nyack | 1900 | 4,275 | 494 | 203 | 8.7 -> 6.1 |
| Nyack | 1920 | 4,444 | 878 (1925) | 247 | 5.1 -> 4.0 |
| Nyack | 1950 | 5,889 | 1235 | 359 | 4.8 -> 3.7 |
| Suffern | 1900 | 1,619 | 389 | 1 | 4.2 -> 4.2 |
| Suffern | 1920 | 3,154 | 717 (1925) | 22 | 4.4 -> 4.3 |
| Suffern | 1950 | 4,010 | 1169 | 131 | 3.4 -> 3.1 |

## Invariants (recomputed from the written rows)

- rows that share ground (> 0.5 m2) with a building of the map while both stand: **0** pairs
- rows that share ground (> 0.5 m2) with another row while both stand, whole file: **0** pairs
- rows within 5.5 m of a street centre line of today: **0**
- rows on today's water: **0**
- rows with start >= end: **0**; duplicate ids: **0**
- most rows starting in one year: 2798 (1927); next: 2759 (1928), 2652 (1929), 2599 (1926), 2356 (1930)
- most rows ending in one year: 1344 (1953); next: 1338 (2004), 1325 (1950), 1322 (1952), 1317 (1949)
- start years: 5 % 1868, median 1924, 95 % 1943; end years: 5 % 1917, median 1973, 95 % 2016
- standing rows by year: 1800: 200, 1850: 1071, 1880: 7557, 1900: 16501, 1925: 32837, 1950: 59050, 1975: 33746, 2000: 16158
