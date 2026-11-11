# Industrial sites: researched building dates and lost structures (round 3, industry part)

Scope reached: Bush Terminal / Industry City (standing lofts) and the Maspeth gas holders (lost). Everything else on the brief's list was not reached (see the end).

## Bush Terminal / Industry City
Sources
- HAER NY-201, "Bush Terminal Company (Bush Terminal)", Raber and Flagg, 1988, Library of Congress (public domain): https://tile.loc.gov/storage-services/master/pnp/habshaer/ny/ny1500/ny1593/data/ny1593data.pdf (cached in data/raw/industry/). Gave: warehouses c. 1892-1910; factory lofts c. 1905-1925; Loft 1 c. 1904; lofts 2-8 built in succession c. 1904-15 and completed by 1914; lofts 9-10 1916-18; lofts 19 and 20 built 1912 on Second Avenue between 39th and 41st; lofts 22-26 in the 1920s; piers 1-5 begun 1903-1909 (150 ft x 1,330-1,351 ft, sheds 1,325 x 144 ft), pier 6 rebuilt 1913 (1,261 x 276 ft), pier 7 c. 1902-05 (1,213 x 157 ft); office c. 1895-1902, steam plant c. 1917-25 (2nd Ave and 32nd St), water tower c. 1920.
- Wikipedia, Industry City (CC BY-SA, facts only), cached in data/raw/sites/wp/: three lofts complete and a fourth under construction in early 1909; fifth and sixth announced mid-1909; Bush Terminal Company Building (Buildings 19-20) begun about 1911, eight storeys, U-shaped, wings 335 ft along 39th and 40th Streets.
- LPC Sunset Park South Historic District report (LP-2622) was fetched: it covers the residential blocks only and has no Bush Terminal building dates.

Result: 6 standing footprints dated (known_building_dates.industry.csv), all `estimated`. Which numbered loft each footprint is was inferred from street-address order (639, 627, 607, 581 Second Avenue run south to north), not documented; the rows therefore name addresses, not loft numbers.

Found in passing: five lofts of the "1-10 Bush Terminal Owner" lot carry starts of 1932-1935 in the built file (heap years or the ground rule's waiting for land), against HAER's 1904-14. The lofts are inland (Second-Third Avenues): the made-land year under them should be checked by the lead (grid_detail_landyear around 40.657, -74.007). BINs 3336893 and 3336894 (882 Third Avenue, lot year 1906, one 52 m tall) were not dated: no source names them.

Not found: warehouse-by-warehouse years (units A-G 1895-1905; one-storey sheds c. 1906) could not be matched to footprints; the pier sheds' positions (only "foot of 41st St" for pier 7) were not found, so no lost-structure rows for piers 1-8 (the USGS-traced piers in data/manual/piers cover 1888 onward).

## Maspeth gas holders (Greenpoint, Brooklyn Union Gas)
Sources
- Controlled Demolition Inc., https://www.controlled-demolition.com/keyspan-energy-gas-holders : Holder 1 "401' tall, 15 million cubic feet"; Holder 2 "385' tall, 17 million cubic feet"; felled 7:00 am Sunday 15 July 2001.
- Wikipedia, Maspeth Gas Holders: built 1927 and 1948; decommissioned 1992 and 1997; one coordinate for the pair, 40.71861, -73.93389.
Estimated: diameter (67 m and 72 m, from capacity / height as a cylinder, a lower bound), the position of each holder (the pair's single coordinate; No. 2 placed 75 m west), rotation irrelevant. Two rows in notable_demolished.industry.csv. No built-file building overlaps either in time.
Not found: a published diameter, the holders' footprints on a plan.

## Not reached or without result
Domino/Havemeyer (only the Pan, Filter and Finishing House stands; the 1882-83 storehouse, machine shop, seven-storey refinery and one-storey storehouse, demolished mid-2014 per Wikipedia, have no outline source here and the built file holds no vanished building there), Pfizer, Eberhard Faber (already LPC-dated in the built file, nothing to add), Steinway, Standard Oil / Astral works, American Sugar, Arbuckle, breweries, Atlantic Terra Cotta, Port Ivory, other gas works (the web search found no HAER record of a New York City holder; Elmhurst and the Gas House holders were done by the sites agent), the power stations (Hudson Avenue: built in stages 1924-32 per a blog/real-estate source, retired by 2011, demolition from January 2024; not used, weak sources), shipyards, grain elevators other than the Red Hook Grain Terminal (BIN 3008877, 1922, already dated "known"), rail terminals.
