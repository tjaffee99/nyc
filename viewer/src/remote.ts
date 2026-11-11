/**
 * Where the heaviest tile sets are read from.
 *
 * GitHub Pages cancels a deployment whose sync runs over ten minutes; on this site that
 * happened twice at 147 MB while 104 MB went through in under a minute (CLAUDE.md, decision
 * 33). So the published site leaves the regional sets out of the Pages build (pipeline/deploy.py
 * writes a Jekyll `exclude` for them, its list HEAVY): the building tiles of the outer boroughs,
 * of the counties and of the outer counties, the z13 terrain tiles, and the region's streets,
 * trees and ground detail. They stay in the same `gh-pages` branch and the
 * published page reads them through GitHub's raw file host, which allows cross-origin reads.
 * Anywhere else (the dev server, a local build) everything is read from the page's own origin.
 */
const PUBLISHED_HOST = 'nyc.theojaffee.net';
const RAW_BRANCH = 'https://raw.githubusercontent.com/tjaffee99/nyc/gh-pages/';

export const HEAVY_BASE = typeof location !== 'undefined' && location.hostname === PUBLISHED_HOST ? RAW_BRANCH : '';
