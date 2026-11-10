import csv
W='https://en.wikipedia.org/wiki/'
E=[
(1609,1624,"Lenapehoking","Lenape homeland; Henry Hudson enters the harbor, 1609","Lenapehoking"),
(1624,1664,"New Amsterdam","The Dutch West India Company's town at the tip of Manhattan","New_Amsterdam"),
(1664,1775,"Colonial New York","English province and seaport; the Dutch return for fifteen months in 1673–74","History_of_New_York_City_(1665–1783)"),
(1775,1783,"Revolution and Occupation","Battle of Long Island, the great fire of 1776, seven years as British headquarters","New_York_and_New_Jersey_campaign"),
(1783,1811,"The Federal Seaport","First capital of the United States, 1785–1790; the largest American city by 1790","History_of_New_York_City_(1784–1854)"),
(1811,1842,"The Grid and the Canal","Commissioners' Plan, 1811; Erie Canal, 1825; the great fire of 1835","Commissioners'_Plan_of_1811"),
(1842,1865,"Croton Water and Central Park","Aqueduct, railroads, mass immigration; Brooklyn becomes the third city of the country","Croton_Aqueduct"),
(1865,1898,"The Gilded Age","Elevated railways, the Brooklyn Bridge, tenements and the first skyscrapers","History_of_New_York_City_(1855–1897)"),
(1898,1916,"Greater New York","Five boroughs consolidated; the subway, the East River bridges, Penn Station and Grand Central","City_of_Greater_New_York"),
(1916,1929,"The Setback City","The 1916 zoning law steps the towers back; subways build out the Bronx, Brooklyn and Queens","1916_Zoning_Resolution"),
(1929,1945,"Depression and New Deal","Empire State and Rockefeller Center; Robert Moses's parkways, bridges and pools; two airports and a World's Fair","History_of_New_York_City_(1898–1945)"),
(1945,1975,"Postwar City","Expressways, public housing and urban renewal; the United Nations and Lincoln Center; Penn Station lost, the landmarks law won","History_of_New_York_City_(1946–1977)"),
(1975,2001,"Crisis and Recovery","Near-bankruptcy in 1975 and a burning Bronx; Battery Park City and a record population by 2000","History_of_New_York_City_(1978–present)"),
(2001,9999,"The Twenty-First Century","After September 11: rebuilding, rezoned waterfronts, the High Line, Hurricane Sandy, supertall towers","History_of_New_York_City_(1978–present)"),
]
for a,b in zip(E,E[1:]): assert a[1]==b[0]
assert E[0][0]==1609 and E[-1][1]==9999
with open('/home/user/nyc/data/tables/eras.csv','w',newline='',encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['start_year','end_year','title','subtitle','source_url'])
    for s,e,t,sub,u in E: w.writerow([s,e,t,sub,W+u])
print(len(E),'eras')
