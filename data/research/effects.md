# Effects table: sources and gaps (2026-11-11)

Method: the table was written from the events tables (`data/tables/events.csv`, `events_counties.csv`: coordinates of Pavonia, Black Tom, Bowling Green, Fort Amsterdam, the 1776 and 1835 fires, ...) and from knowledge of the accounts. The web was not read for this table: Wikipedia answered with HTTP 429 (rate limit) during link checks, and its battle articles were not opened. So every date, hour and route comes from recall of the standard accounts (Wikipedia battle articles, NPS and American Battlefield Trust pages), NOT from a page read in this session. The lead should treat times of day and the routes between named places as unverified until someone opens the articles.

## Sources (all facts only, no text copied; Wikipedia text is CC BY-SA 4.0, facts are free)
Each row's `source_url` is the article for the event. HTTP 200 checked 2026-11-11 for all but: 429 (rate limit, not checked) for Paulus Hook, General Slocum, Great Fire of 1835, Henry Hudson, Leisler's Rebellion, New Amsterdam, Peach War. Titles I could not confirm (404) were replaced by the town's article: Fairfield, Norwalk, New Haven (Tryon's raid of July 1779), Paterson (fire of 1902), Hoboken (pier fire of 1900), Bowling Green (statue of George III). Better pages exist; find them.

- Revolution: Battle of Long Island (incl. evacuation), Landing at Kip's Bay, Battle of Harlem Heights, Great Fire of New York (1776) [+ `fire_1776.geojson`], Battle of Pell's Point, Battle of Mamaroneck, Battle of White Plains, Battle of Fort Washington, New York and New Jersey campaign (Fort Lee, retreat), Washington's crossing of the Delaware, Battle of Trenton, Second Battle of Trenton, Battle of Princeton, Danbury Raid, Battle of Ridgefield, Battle of Fort Montgomery, Burning of Kingston, Battle of Paulus Hook, Battle of Stony Point, Battle of Connecticut Farms, Battle of Springfield, Evacuation Day (New York).
- Earlier: Kieft's War, Peach War, New Amsterdam / Second Anglo-Dutch War, New Orange, Leisler's Rebellion, New York Slave Revolt of 1712, New York Conspiracy of 1741.
- Fires and disasters: Great Fires of 1835 [+ `fire_1835.geojson`] and 1845, New York Crystal Palace, Barnum's American Museum, Brooklyn Theatre fire, Hell Gate, New York City draft riots, General Slocum, Triangle Shirtwaist fire, Black Tom explosion, Wall Street bombing, Hindenburg disaster, 1945 Empire State Building B-25 crash, 1960 New York mid-air collision, 1977 blackout, September 11 attacks, 7 World Trade Center, Effects of Hurricane Sandy in New York, Breezy Point, 1967 Newark riots.
- Arrivals: Henry Hudson, First inauguration of George Washington, Lafayette's Farewell Tour, Erie Canal, Ticker-tape parade.

## What could not be placed / was left out
- **Ranges of the 1776 fire and 1835 fire**: only the existing estimated rings; the 1845 ring is a hand-drawn estimate.
- **1741 fires** other than Fort George (Warren's house, Van Zandt's store, others): lots not known to me.
- **Newark's fire of 1836**: no source known to me; not added. Newark 1967 and Paterson 1902 are centre points with a radius, not outlines. Jersey City: none. Hoboken 1900: a point.
- **Croton celebration 1842**: no account of the parade's route in hand; not drawn. **V-J Day 1945**: a crowd, not a movement; not drawn. **Lindbergh 1927**: only the Battery - City Hall leg on Broadway.
- **Pound Ridge massacre (1644)**, Anne Hutchinson (1643), Lenape reprisals of 1643: date or place not certain enough; left out. Kieft's War has only the Pavonia and Corlears Hook attacks.
- **Lafayette 1824, Washington 1789**: the water legs are known; the parades' street routes are not drawn except Washington's last leg (schematic).
- **Pell's Point / Fort Washington / Fort Lee / Harlem Heights**: stand positions are approximate to a few hundred metres.
- **Aircraft tracks (9/11, Hindenburg, B-25, 1960)**: schematic, 3-6 points, not radar data.
- **Troop numbers, ship counts** are not in the table.
- Sides: `french` unused (no French action in the area covered); Hessians have their own side; Lenape only in 1655.

## To check before the lead trusts it
1. Fleet and boat points over water: any fleet point on land in the pipeline's water layer (esp. Eastchester Bay 1776, Harlem River 1776, East River 1904, Closter landing, Sound routes).
2. Time-of-day values are not used by the slider unless the viewer widens durations.
3. Open the Wikipedia pages listed and correct hours/places.
