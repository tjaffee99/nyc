"""How good are the map-edition brackets? Compare edition_brackets.csv with the built file's
independent years (LPC exact, or an assessor year not stamped on five or more buildings of the
site). The README's "What the map brackets are worth" quotes this output.

  cd data/manual/sites && ../../../.venv/bin/python -I tools/validate_brackets.py
"""
from pathlib import Path

import pandas as pd

if __name__ == "__main__":
    t = pd.read_csv(Path(__file__).resolve().parent.parent / "edition_brackets.csv")
    ind = ((t.built_src == "lpc") & (t.built_conf == "exact")) | (
        (t.built_src == "assessor") & (t.built_conf == "exact") & (~t.stamped))
    v = t[ind & t.built_year.notna()]
    print(f"{len(t)} footprints read in {t.site.nunique()} sites; {len(v)} with an independent year")
    two = v[v.last_absent.notna() & v.first_drawn.notna() & ((v.first_drawn - v.last_absent) <= 25)]
    hit = (two.built_year >= two.last_absent - 1) & (two.built_year <= two.first_drawn + 1)
    print(f"clean absent-then-drawn brackets among them: {len(two)}; independent year inside the bracket: {int(hit.sum())}; "
          f"building older than the bracket: {int((two.built_year < two.last_absent - 1).sum())}; "
          f"newer: {int((two.built_year > two.first_drawn + 1).sum())}")
    old = v[v.built_year <= 1935]
    first = old.sheets.fillna("").str.split(" ").str[0].str[-1]
    print(f"independently dated to 1935 or earlier: {len(old)}; drawn on the first 1:24,000 sheet: {int((first == 'd').sum())}")
    print(old.assign(s=first).groupby("site").s.apply(lambda x: f"{(x == 'd').sum()} of {len(x)}").to_string())
