"""Publish viewer/dist to the gh-pages branch (served at https://nyc.theojaffee.net, see
viewer/public/CNAME).

The branch holds one generated commit, replaced on each deploy, so built data doesn't pile
up in history. The commit is made in a temporary git directory with viewer/dist as its work
tree; the repository itself is not touched. Prints the size of the published site (GitHub
Pages cancels a deployment whose file sync runs over ten minutes: see HEAVY below).

  python pipeline/deploy.py [--dry-run]     (DEPLOY_DIST=<dir> to publish another build)
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# DEPLOY_DIST: publish another build directory (a clean copy of the viewer built elsewhere)
DIST = Path(os.environ.get("DEPLOY_DIST") or ROOT / "viewer" / "dist")
# GitHub Pages cancelled this site's deployment twice at 147 MB (ten-minute limit) and
# published 104 MB in under a minute. These tile sets are therefore pushed to the branch but
# left out of the Pages build by a Jekyll `exclude`; the published page reads them through
# raw.githubusercontent.com (viewer/src/remote.ts).
HEAVY = ["data/region-buildings", "data/county-buildings", "tiles/terrain/13"]
LIMIT_MB = 100          # the part Pages builds


def run(args, **kw):
    return subprocess.run(args, check=True, text=True, capture_output=True, **kw).stdout.strip()


def main():
    if not (DIST / "index.html").exists():
        sys.exit("viewer/dist/index.html is missing: run `make build` first")
    total = sum(f.stat().st_size for f in DIST.rglob("*") if f.is_file()) / 1e6
    heavy = sum(f.stat().st_size for h in HEAVY for f in (DIST / h).rglob("*") if f.is_file()) / 1e6
    n = sum(1 for f in DIST.rglob("*") if f.is_file())
    size = total - heavy
    print(f"deploy: {n} files, {total:.0f} MB in the branch: {size:.0f} MB built by Pages, {heavy:.0f} MB read from the branch")
    if size > LIMIT_MB:
        sys.exit(f"deploy: the Pages part is over {LIMIT_MB} MB; GitHub Pages will cancel the deployment")
    url = run(["git", "remote", "get-url", "origin"], cwd=ROOT)
    sha = run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT)
    # Jekyll runs only to leave the heavy sets out; nothing else in the build has front matter
    (DIST / ".nojekyll").unlink(missing_ok=True)
    (DIST / "_config.yml").write_text("# written by pipeline/deploy.py\nexclude:\n" + "".join(f"  - {h}\n" for h in HEAVY))
    if "--dry-run" in sys.argv:
        print(f"deploy: dry run, would push {sha} to {url} gh-pages")
        return
    with tempfile.TemporaryDirectory() as gd:
        env = dict(os.environ, GIT_DIR=gd, GIT_WORK_TREE=str(DIST))
        for args in (["git", "init", "-q", "-b", "gh-pages"], ["git", "add", "-A"],
                     ["git", "commit", "-q", "-m", f"Deploy {sha}"]):
            subprocess.run(args, check=True, cwd=DIST, env=env)
        delay = 2
        for attempt in range(5):
            r = subprocess.run(["git", "push", "-f", url, "gh-pages"], cwd=DIST, env=env)
            if r.returncode == 0:
                print(f"deploy: pushed {sha} to gh-pages")
                return
            if attempt < 4:
                import time
                time.sleep(delay)
                delay *= 2
        sys.exit("deploy: push failed")


if __name__ == "__main__":
    main()
