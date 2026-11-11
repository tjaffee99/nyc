# Round of 2026-11-12, second: fill what is still missing — generated where it must be

Read `CLAUDE.md` (the owner's rules; decisions 8, 34, 38, 54, 55 and "What is not done"),
`docs/ROUND4.md` (what a "hole" is; the tracing rules — they still hold) first.

## What the owner said (verbatim), quoting the list of what was still missing

> > Brooklyn before 1880, Coney Island, Bay Ridge, Inwood, the east and north Bronx, Flushing's
> > centre, the Rockaways, and most of Staten Island.
> > Paterson and Newark have no traced atlas at all; Paterson is thin before 1920.
> > Several lost works could not be placed from opened sources: Western Electric and the coke
> > works at Kearny, the Singer works at Elizabeth, Colgate, Stevens Castle, the
> > Hamburg-American piers.
>
> bro go do it. procedurally generate it based off your best guess if you need to

## What that changes

- **Generation is allowed where nothing better can be had**, and so is a best guess for a
  position, a size or a year — on two conditions that do not bend (decision 38): a generated
  or guessed thing is **marked** (`procedural`; the words "generated" or "best guess" in the
  text the popup shows, with what the guess rests on), and it **gives way** to anything real
  (a traced outline, a record, a standing building). A real traced atlas is still better
  than a generated block: trace where a plate can be opened and registered, generate the rest.
- "Missing" is measured: `pipeline/holes.py` → `data/interim/reports/holes.csv` (built-up
  ground with nothing standing within 60 m, per place and year), and persons per building
  standing on the map against the census (`data/tables/population_towns.csv` for the 559
  municipalities, `population.csv` for the boroughs, `population_counties.csv`,
  `population_outer.csv`).

## Machine (six agents and the lead share it; a process was killed for memory last round)

- One process of yours at a time, **under 1.5 GB**. Before a heavy step run `free -m`: if less
  than 3 GB is available, wait a minute and look again. Work in tiles, plates or towns, never
  a whole region in memory (DuckDB: `SET memory_limit='1200MB'`).
- Disk: 6 GB free for everybody; **under 600 MB for your part at any moment**; delete scans
  and downloads as soon as they are used.
- Resumable steps, results written as you go. No git, no pipeline stage other than your own
  new script, no deploy, no edits outside the files your brief names.
- Outbound requests: User-Agent `NYCThroughTime-research/0.1`; never the owner's name, e-mail
  or the repository name. Wikipedia: raw wikitext, one page every 4 seconds. The Library of
  Congress's Sanborn volumes opened on the second try last round (`data/research/hoboken_atlas.md`
  says how the image addresses are found). NYPL's Map Warper dump and scans: the atlas README.
