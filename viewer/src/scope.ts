/**
 * How much of the map the page loads.
 *
 * By default: the five boroughs and Hudson County (the "core": pipeline/extent.py core_ring ->
 * data/core-extent.json). The 26 counties around them are six million buildings more, and on a
 * telephone the whole map was very slow (the owner, 2026-11-11). They are loaded when asked:
 * the button in the corner, a link to a place outside the core, or `wide=1` in the link.
 * The choice is kept on the device. Switching reloads the page: every layer reads its extent
 * once, at load.
 */
const KEY = 'nyc-through-time-wide';
/** the core outline's box, with a margin */
export const CORE_BOX: [number, number, number, number] = [-74.29, 40.45, -73.67, 40.95];
/** the box of everything that is built (pipeline/common.py REGION_BBOX) */
export const WIDE_BOX: [number, number, number, number] = [-75.37, 39.47, -71.85, 42.2];

function inCore(lon: number, lat: number) {
  return lon >= CORE_BOX[0] && lon <= CORE_BOX[2] && lat >= CORE_BOX[1] && lat <= CORE_BOX[3];
}

function decide(): boolean {
  if (typeof location === 'undefined') return true;
  const h = location.hash;
  if (/[#&]wide=1\b/.test(h)) return true;
  if (/[#&]wide=0\b/.test(h)) return false;
  const m = /[#&]c=(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)/.exec(h);
  if (m && !inCore(+m[1], +m[2])) return true; // a link to somewhere in the counties
  try {
    return localStorage.getItem(KEY) === '1';
  } catch {
    return false;
  }
}

/** true: the whole region is loaded; false: the core only */
export const WIDE = decide();
/** the box the tiled layers ask for tiles in */
export const VIEW_BOX = WIDE ? WIDE_BOX : CORE_BOX;

/** Remember the choice and load the page again with it. */
export function setWide(on: boolean) {
  try {
    localStorage.setItem(KEY, on ? '1' : '0');
  } catch {
    /* private mode: the link carries it instead */
  }
  const h = location.hash.replace(/[#&]wide=[01]\b/g, '').replace(/^#?&?/, '');
  location.hash = (h ? h + '&' : '') + `wide=${on ? 1 : 0}`;
  location.reload();
}
