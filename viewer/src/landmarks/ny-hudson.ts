/**
 * Landmarks of Westchester, Rockland and the Hudson valley (Putnam, Orange, Dutchess, Ulster):
 * houses and churches of Tarrytown / Pocantico, West Point, Hyde Park, Poughkeepsie, Pollepel
 * Island, the Croton dam and the Hudson bridges from the Tappan Zee to the Walkway.
 * Research: data/research/landmarks_ny_hudson.md.
 *
 * Conventions as in nyc-civic.ts / nyc-bridges.ts: plans are building footprints from Overture
 * Maps 2026-10-21.0 (OpenStreetMap, (c) OpenStreetMap contributors, ODbL; Westchester and
 * Rockland also in the county building file) re-expressed in metres east / north of the anchor
 * (the anchor is the point the footprint was read around); heights are cited figures or are
 * named as estimates in each model's "Model" fact. Bridges are modelled from sea level in
 * their own path frame, deck ends from the Overture bridge flags.
 */
import {MeshBuilder, circle, rect, parabola, lngLatToLocal, type V2, type V3} from './kit';
import type {Landmark} from './types';

const WIKI = 'https://en.wikipedia.org/wiki/';
const OVT = 'https://docs.overturemaps.org/guides/buildings/ (release 2026-10-21.0, OpenStreetMap ODbL)';
const OSM = 'https://www.openstreetmap.org/';

export const NY_HUDSON: Landmark[] = [];

// ------------------------------------------------------------------ helpers

/** Flat list of numbers -> ring. */
function P(...n: number[]): V2[] {
  const o: V2[] = [];
  for (let i = 0; i < n.length; i += 2) o.push([n[i], n[i + 1]]);
  return o;
}

function centroid(r: V2[]): V2 {
  let x = 0;
  let y = 0;
  for (const p of r) {
    x += p[0];
    y += p[1];
  }
  return [x / r.length, y / r.length];
}

function scaleAbout(r: V2[], k: number, c: V2 = centroid(r)): V2[] {
  return r.map(p => [c[0] + (p[0] - c[0]) * k, c[1] + (p[1] - c[1]) * k] as V2);
}

/** Minimum-area bounding rectangle: centre, short side `w` (frame x), long side `l` (frame y), bearing of the long side. */
function mrr(r: V2[]) {
  let best = {area: Infinity, cx: 0, cy: 0, w: 0, l: 0, bearing: 0};
  for (let a = 0; a < 180; a += 1) {
    const t = (a * Math.PI) / 180;
    const ux = Math.cos(t);
    const uy = Math.sin(t);
    let u0 = Infinity;
    let u1 = -Infinity;
    let v0 = Infinity;
    let v1 = -Infinity;
    for (const [x, y] of r) {
      const u = x * ux + y * uy;
      const v = -x * uy + y * ux;
      u0 = Math.min(u0, u);
      u1 = Math.max(u1, u);
      v0 = Math.min(v0, v);
      v1 = Math.max(v1, v);
    }
    const du = u1 - u0;
    const dv = v1 - v0;
    if (du * dv < best.area) {
      const cu = (u0 + u1) / 2;
      const cv = (v0 + v1) / 2;
      const longU = du >= dv;
      const dx = longU ? ux : -uy;
      const dy = longU ? uy : ux;
      best = {area: du * dv, cx: cu * ux - cv * uy, cy: cu * uy + cv * ux, w: Math.min(du, dv), l: Math.max(du, dv), bearing: ((Math.atan2(dx, dy) * 180) / Math.PI + 360) % 360};
    }
  }
  return best;
}

/** Hipped roof over the (inset) bounding rectangle of a ring. */
function hipOver(b: MeshBuilder, ring: V2[], z0: number, rise: number, k = 0.85) {
  const m = mrr(ring);
  b.frame(m.cx, m.cy, 0, m.bearing, () => b.hip(0, 0, m.w * k, m.l * k, z0, rise));
}

/** Gabled roof over the bounding rectangle of a ring (ridge along its long side). */
function gableOver(b: MeshBuilder, ring: V2[], z0: number, rise: number, k = 1) {
  const m = mrr(ring);
  b.frame(m.cx, m.cy, 0, m.bearing, () => b.gable(0, 0, m.w * k, m.l * k, z0, rise, true));
}

/** Box with a pyramid roof (towers, turrets). */
function tower(b: MeshBuilder, cx: number, cy: number, s: number, z0: number, z1: number, apex: number, wall: string, roof: string) {
  b.color(wall).box(cx, cy, z0, s, s, z1 - z0);
  b.color(roof).pyramid(rect(cx, cy, s * 1.08, s * 1.08), z1, [cx, cy, apex]);
}

function addLM(l: Landmark) {
  NY_HUDSON.push(l);
}

// ====================================================================== Kykuit (1906-1913)
// Anchor: the footprint of 'Kykuit' (Overture daca3c93; OSM height 17.07 m) — 40.1 x 23.7 m bounding
// rectangle, 868 m2. Wikipedia (Kykuit): designed by Delano & Aldrich as a steep-roofed three-storey
// mansion, rebuilt into the present four-storey Classical Revival (Georgian) house for John D.
// Rockefeller; "completed in 1913"; Bosworth's terraces and gardens from 1906; 40 rooms.
const KY_RING = P(-0.6, 12.3, -3.8, 14.7, -3.3, 15.5, -7.1, 18.4, -19.9, 1.3, -13.2, -3.7, -14.2, -5.1, -7.6, -10.0, -7.0, -9.3, 11.8, -23.3, 24.5, -6.2, 5.6, 7.8, 6.6, 9.0, 0.4, 13.6);

function kykuitBuild(b: MeshBuilder) {
  const TOP = 17.07; // OSM / Overture height of the footprint
  const EAVE = 13.6; // estimated: four storeys, hipped roof above
  // terraces of the forecourt and gardens (Bosworth, 1906-): one stepped platform, estimated
  b.color('#B9B09B').prism(scaleAbout(KY_RING, 1.5), -1.2, 0.6, {top: true});
  b.color('#D8D2C2').prism(KY_RING, 0, EAVE);
  b.color('#8A8F93');
  hipOver(b, KY_RING, EAVE, TOP - EAVE, 0.78);
  // chimney stacks (estimated)
  b.color('#A98F7B');
  for (const [x, y] of [[-6, -2], [4, -9], [2, 4]]) b.box(x, y, TOP - 2, 1.4, 1.4, 4.2);
}

addLM({
  id: 'kykuit',
  name: 'Kykuit (Rockefeller estate house)',
  kind: 'building',
  built: [1906.0, 1913.0],
  end: 9999,
  anchor: [-73.84444, 41.08961],
  build: kykuitBuild,
  replaces: [KY_RING],
  facts: {
    Construction: 'Delano & Aldrich for John D. Rockefeller, grounds by William Welles Bosworth from 1906; completed in 1913',
    Form: 'four-storey Classical Revival (Georgian) stone house, 40 rooms, Pocantico Hills',
    Height: 'roof 17.07 m (Overture / OpenStreetMap height of the footprint)',
    Model: 'plan from the footprint (868 m2); eaves at 13.6 m, hipped roof, chimneys and the garden terrace are estimated; start year 1906 is the date of the grounds design, the house itself began earlier in the decade (estimated)'
  },
  sources: [WIKI + 'Kykuit', OVT]
});

// ====================================================================== Old Dutch Church of Sleepy Hollow (1685-1697)
// Anchor (-73.86167, 41.09028). Footprint 'Old Dutch Church' (Overture 5d9028bb): 18.3 x 11.2 m,
// long axis east-west, apse at the east end. Wikipedia: fieldstone walls two feet (60 cm) thick,
// built "between 1685 (the date on its bell) and 1697" (congregation organised), an octagonal wooden
// open belfry at the west end of the roof; renovated after a fire in 1837, restored 1897.
const ODC_RING = P(-28.4, 8.5, -14.0, 9.5, -10.4, 12.8, -10.9, 17.7, -15.0, 20.7, -29.2, 19.7, -28.9, 15.4);

function odcBuild(b: MeshBuilder) {
  b.color('#8D8576').prism(ODC_RING, 0, 5.2); // fieldstone walls (height estimated)
  b.color('#6B5F52');
  b.frame(-19.5, 14.6, 0, 90, () => b.gable(0, 0, 11.4, 19.4, 5.2, 5.0, true)); // steep roof, ridge east-west
  // belfry at the west end: octagon on the ridge, wooden, bell-shaped cap (estimated)
  const bx = -26.6;
  const by = 14.6;
  b.color('#D9D3C4').cylinder(bx, by, 1.5, 9.0, 11.8, 8);
  b.color('#5B5048').dome(bx, by, 1.8, 11.8, 2.4, 8, 3);
  b.color('#3F3A34').beam([bx, by, 14.2], [bx, by, 15.6], 0.2);
}

addLM({
  id: 'old_dutch_church_sleepy_hollow',
  name: 'Old Dutch Church of Sleepy Hollow',
  kind: 'building',
  built: [1685.0, 1697.0],
  end: 9999,
  anchor: [-73.86167, 41.09028],
  build: odcBuild,
  replaces: [ODC_RING],
  facts: {
    Construction: 'between 1685 (the date on its bell) and 1697, when the congregation was organised; fieldstone, local timber and yellow Dutch bricks',
    Form: 'stone church with a steep roof and an octagonal wooden open belfry at the west end; walls 60 cm thick',
    Model: 'plan from the footprint (18.3 x 11.2 m); wall height 5.2 m, roof pitch, belfry size and height (top 15.6 m) are estimated; the church was repaired after a fire in 1837 and restored in 1897, not modelled; start and completion are the cited bounds'
  },
  sources: [WIKI + 'Old_Dutch_Church_of_Sleepy_Hollow', OVT]
});

// ====================================================================== Philipsburg Manor, Upper Mills (house and mill)
// Anchor (-73.86361, 41.08853). 'Philipsburg Manor' (Overture 3b50d982): 11.0 x 10.6 m, 117 m2;
// 'Upper Mills' (0dd4154f), the mill: 123 m2. Wikipedia (Philipsburg Manor House): Frederick Philipse
// built a stone manor house, a mill and a wharf at the confluence of the Pocantico and the Hudson
// within the 1693 manor grant; Adolphus Philipse doubled the house; by the 1750 probate the complex
// held a stone gristmill, bakehouse and workshops.
const PM_HOUSE = P(-3.4, 7.0, 2.7, 15.7, -6.4, 21.9, -12.5, 13.2);
const PM_MILL = P(-1.5, -12.8, -9.3, -7.2, -12.3, -11.3, 0.9, -20.7, 7.5, -11.5, 2.1, -7.7);

function pmBuild(b: MeshBuilder) {
  b.color('#9A9588').prism(PM_HOUSE, 0, 4.6); // fieldstone house, one and a half storeys (estimated)
  b.color('#6D5A48');
  gableOver(b, PM_HOUSE, 4.6, 3.6, 1.04);
  b.color('#7A7466').prism(PM_MILL, 0, 6.2); // stone gristmill
  b.color('#6D5A48');
  gableOver(b, PM_MILL, 6.2, 4.4, 1.04);
  // mill pond dam / sluice stub (estimated)
  b.color('#8C867A').box(2, -26, -0.5, 9, 1.6, 1.7);
}

addLM({
  id: 'philipsburg_manor_upper_mills',
  name: 'Philipsburg Manor: manor house and mill (Upper Mills)',
  kind: 'building',
  built: [1685.0, 1693.0],
  end: 9999,
  anchor: [-73.86361, 41.08853],
  build: pmBuild,
  replaces: [PM_HOUSE, PM_MILL],
  facts: {
    Construction: 'stone manor house, mill and wharf of Frederick Philipse within the 1693 royal grant; the house doubled by Adolphus Philipse; a stone gristmill stood by the 1750 probate',
    Form: 'fieldstone manor house and gristmill at the mill pond of the Pocantico River, Sleepy Hollow',
    Model: 'plans from the footprints (house 117 m2, mill 123 m2); heights and roofs are estimated; the start year is estimated (the article dates the manor to 1693, not the house), the present mill is a later reconstruction on the footprint of the old one (its date was not verified here)'
  },
  sources: [WIKI + 'Philipsburg_Manor_House', OVT]
});

// ====================================================================== Lyndhurst (1838-1842, enlarged 1864-65)
// Anchor (-73.86728, 41.05397). Footprint 'Lyndhurst Mansion' (Overture 47e37d7f): 45.7 x 22.2 m, 710 m2,
// OSM height 21.03 m. Wikipedia (Lyndhurst (estate)): Gothic Revival house designed 1838 by Alexander
// Jackson Davis, completed 1842; in 1864-65 Davis doubled it for George Merritt with a north wing
// and a four-storey tower. The seam in the footprint at y = 7 m splits the original block (south)
// from the north wing (estimated division).
const LY_RING = P(-1.3, 18.2, -0.7, 24.0, -7.9, 24.6, -8.4, 18.8, -9.5, 18.9, -9.6, 17.2, -11.1, 17.4, -11.5, 12.9, -12.6, 13.0, -13.2, 6.7, -17.0, 7.1, -19.2, -17.1, -15.2, -17.5, -12.1, -20.9, -6.8, -21.2, -3.2, -18.3, 2.0, -18.7, 2.9, -9.2, 3.8, -9.1, 4.4, -3.3, 3.4, -3.2, 3.9, 2.7, -0.4, 3.0, -0.0, 6.6, -3.3, 6.9, -2.9, 10.8, -0.8, 10.6, -0.1, 18.1);
const LY_OLD = P(-17.0, 7.0, -19.2, -17.1, -15.2, -17.5, -12.1, -20.9, -6.8, -21.2, -3.2, -18.3, 2.0, -18.7, 2.9, -9.2, 3.8, -9.1, 4.4, -3.3, 3.4, -3.2, 3.9, 2.7, -0.4, 3.0, 0.0, 7.0);

function lyBlock(b: MeshBuilder, ring: V2[], withTower: boolean) {
  const EAVE = 10.2;
  b.color('#BDB6A6').prism(ring, 0, EAVE); // marble-faced walls (grey-white)
  b.color('#6F6A64');
  hipOver(b, ring, EAVE, 4.2, 0.8);
  // pinnacled corner turrets (estimated)
  b.color('#A7A092');
  for (const [x, y] of [[-17.5, -15.5], [3, -17], [-17, 5.5]]) b.cylinder(x, y, 0.9, EAVE, EAVE + 3.2, 6);
  if (withTower) tower(b, -4.5, 21.3, 6.6, EAVE, 17.0, 21.03, '#BDB6A6', '#5B5651');
}

addLM({
  id: 'lyndhurst_1838',
  name: 'Lyndhurst (Knoll), original house',
  kind: 'building',
  built: [1838.0, 1842.0],
  end: 1864.0,
  anchor: [-73.86728, 41.05397],
  build: b => lyBlock(b, LY_OLD, false),
  replaces: [LY_RING],
  facts: {
    Construction: 'designed in 1838 by Alexander Jackson Davis for William Paulding, completed in 1842; Gothic Revival',
    Model: 'the south block of today\'s footprint (the seam at y = 7 m is where the 1864-65 wing meets it: estimated division); eaves 10.2 m, roof and turrets estimated'
  },
  sources: [WIKI + 'Lyndhurst_(estate)', OVT]
});

addLM({
  id: 'lyndhurst',
  name: 'Lyndhurst (enlarged 1864-65)',
  kind: 'building',
  built: [1864.0, 1865.9],
  end: 9999,
  anchor: [-73.86728, 41.05397],
  build: b => lyBlock(b, LY_RING, true),
  replaces: [LY_RING],
  facts: {
    Construction: 'in 1864-65 Davis doubled the house for George Merritt (a north wing, a four-storey tower, a new porte-cochere); later the Jay Gould estate',
    Height: 'tower top 21.03 m (Overture / OpenStreetMap height of the footprint)',
    Model: 'plan from the footprint (710 m2); eave height 10.2 m, roofs, turrets and the tower\'s stage heights are estimated; completion date 1865.9 is estimated within the cited 1864-65'
  },
  sources: [WIKI + 'Lyndhurst_(estate)', OVT]
});

// ====================================================================== West Point
// Cadet Chapel (1910). Anchor (-73.960003, 41.390172) = the article's coordinates (41 23 24.62 N 73 57 36.01 W).
// Footprint 'Westpoint Cadet Chapel' (Overture 97dc5973): Latin cross, nave 12 m wide running north
// 54 m from the crossing. Wikipedia: groundbreaking 1906, completed and dedicated 1910; Goodhue (Cram,
// Goodhue & Ferguson), Gothic Revival; houses the largest chapel organ in the world.
const CC_RING = P(-2.5, -7.1, -2.4, -11.8, 9.4, -11.3, 9.6, -17.7, 11.2, -18.9, 13.0, -18.5, 14.7, -20.0, 11.9, -23.1, 18.5, -29.0, 27.3, -19.3, 11.6, -5.3, 11.3, 3.5, 13.1, 3.6, 12.7, 15.1, 6.6, 14.8, 5.2, 54.2, -6.5, 53.8, -5.1, 15.2, -10.3, 15.1, -9.9, 3.0, -7.1, 3.0, -6.7, -7.3);

function ccBuild(b: MeshBuilder) {
  const W = 8.5;
  b.color('#8E8C86').prism(CC_RING, 0, W);
  // nave: gable, ridge along the long arm (estimated height)
  b.color('#5C5A57').frame(0, 34.5, 0, 0, () => b.gable(0, 0, 12.0, 39.4, W, 7.2, true));
  // transept
  b.color('#5C5A57').frame(1.5, 9.3, 0, 90, () => b.gable(0, 0, 11.8, 21.6, W, 6.0, true));
  // chancel and the southern wings: lower hips
  b.color('#5C5A57');
  hipOver(b, P(-2.5, -11.8, 9.4, -11.3, 9.6, -17.7, 18.5, -29, 27.3, -19.3, 11.6, -5.3, 11.3, -5), W, 3.4, 0.9);
  // crossing tower (estimated top 36 m) with pinnacles
  tower(b, 1.5, 9.3, 8.0, W, 28.0, 36.0, '#8E8C86', '#4C4B49');
  b.color('#8E8C86');
  for (const [x, y] of [[-2.2, 5.6], [5.2, 5.6], [-2.2, 13], [5.2, 13]]) b.box(x, y, 28, 1.1, 1.1, 2.4);
}

addLM({
  id: 'cadet_chapel_west_point',
  name: 'Cadet Chapel, West Point',
  kind: 'building',
  built: [1906.0, 1910.0],
  end: 9999,
  anchor: [-73.960003, 41.390172],
  build: ccBuild,
  replaces: [CC_RING],
  facts: {
    Construction: 'groundbreaking 1906, completed and dedicated 1910; Cram, Goodhue & Ferguson; Gothic Revival granite',
    Form: 'cruciform chapel above the Plain; home of the largest chapel pipe organ in the world',
    Model: 'plan from the footprint (1,185 m2); wall height 8.5 m, nave and transept roofs, crossing-tower height (36 m) are estimated (no height is cited in the article; the OSM height of 8.3 m is for the low walls only)'
  },
  sources: [WIKI + 'West_Point_Cadet_Chapel', OVT]
});

// Washington Hall (1925-1929). Anchor (-73.95860, 41.39117). Footprint 'Washington Hall' (Overture 2bb5350f):
// 8,290 m2 including the 1971 expansion. USMA grounds article: started 1925, completed 1929, Arnold
// Brunner, cadet mess hall; the mess-hall expansion was completed in 1971.
const WH_RING = P(31.7, -0.2, 61.9, -0.3, 61.9, 22.3, 56.0, 22.3, 28.7, 22.4, 45.9, 43.1, 50.6, 48.7, 51.5, 49.8, 44.7, 55.3, 44.0, 54.4, 34.5, 62.2, 35.4, 63.3, 30.4, 67.6, 29.7, 66.7, 24.8, 61.2, 26.6, 59.5, 8.5, 37.8, 1.9, 67.5, 0.9, 71.8, -19.0, 67.8, -10.9, 28.1, -17.3, 20.0, -61.2, 10.3, -56.3, -11.5, -25.6, -4.7, -47.4, -30.0, -49.0, -28.7, -51.4, -31.4, -56.2, -37.0, -30.4, -59.0, -29.2, -57.6, -27.8, -56.0, -23.8, -55.8, -19.7, -50.8, -28.5, -43.8, -9.4, -20.3, -10.4, -75.1, 15.7, -75.7, 16.9, -14.3, 24.0, -14.4, 31.7, -5.9);

function whBuild(b: MeshBuilder) {
  const W = 19.0;
  b.color('#A79F90').prism(WH_RING, 0, W);
  b.color('#6C6862').prism(scaleAbout(WH_RING, 0.985), W, W + 1.6); // parapet band
  // the mess hall's gabled roof ridges (estimated), over the two large wings
  b.color('#58575A');
  b.frame(0, -45, 0, 0, () => b.gable(0, 0, 24, 54, W + 1.6, 6.5, true));
  b.frame(-35, 2, 0, 90, () => b.gable(0, 0, 24, 44, W + 1.6, 6.5, true));
  // central pavilion (estimated)
  b.color('#A79F90').box(-3, 49, 0, 14, 4, W + 5);
}

addLM({
  id: 'washington_hall_west_point',
  name: 'Washington Hall (Cadet Mess), West Point',
  kind: 'building',
  built: [1925.0, 1929.0],
  end: 9999,
  anchor: [-73.9586, 41.39117],
  build: whBuild,
  replaces: [WH_RING],
  facts: {
    Construction: 'started in 1925, completed in 1929 (Arnold Brunner); named for George Washington; the cadet mess hall, expanded to the present size by 1971',
    Model: 'plan is the footprint of today (8,290 m2), which includes the 1971 expansion: the 1929 plan was smaller and is not known here; the wall height (19 m), parapet, roof ridges and pavilion are estimated'
  },
  sources: [WIKI + 'United_States_Military_Academy_grounds_and_facilities', OVT]
});

// Michie Stadium (1924). Anchor (-73.96417, 41.38750). Footprint (Overture bfa4acd0): 14,603 m2 bowl outline
// (228 x 127 m, long axis north-south). Wikipedia: opened 1924 (16,000 seats), east grandstand 1962,
// west upper deck 1969, press box 2003, field at 335 ft above sea level, north-south configuration.
const MS_RING = P(37.9, -99.2, 44.4, -97.0, 38.5, -82.4, 27.9, -82.0, 28.7, -58.5, -24.1, -56.6, -28.2, -54.2, -30.4, -51.7, -32.0, -48.0, -30.4, 62.8, -29.3, 66.6, -26.6, 69.4, -23.5, 71.1, -19.9, 72.0, 33.4, 70.3, 34.1, 88.2, 34.4, 94.5, 26.9, 94.7, 26.8, 103.6, -10.5, 104.9, -20.3, 104.7, -29.1, 102.2, -37.3, 99.0, -44.9, 94.2, -52.3, 85.6, -56.9, 76.8, -58.9, 70.9, -79.7, 71.7, -82.2, 15.0, -82.4, 10.9, -82.6, 6.2, -85.0, -50.0, -73.9, -50.3, -72.1, -58.0, -69.5, -65.1, -64.7, -74.0, -57.2, -83.3, -50.7, -89.0, -51.9, -91.5, -51.9, -94.7, -50.4, -99.3, -48.2, -102.6, -45.5, -105.1, -41.7, -106.6, -35.9, -107.2, -32.9, -107.4, -33.6, -119.0, 28.3, -121.1, 28.8, -107.3, 38.2, -105.0);

function msBuild(b: MeshBuilder) {
  // The field lies between the two stands: 110 x 49 m (120 x 53 yd), long axis north-south, centred on the bowl.
  const fx = -29;
  const fy = -26;
  // west stand and east stand as sloped seating banks; the south and north ends open (estimated)
  const bank = (x0: number, x1: number, lowX: number) => {
    b.color('#8C8F94');
    const a: V3[] = [];
    const c: V3[] = [];
    for (let i = 0; i <= 6; i++) {
      const t = i / 6;
      a.push([x0 + (x1 - x0) * t, fy - 62, 1 + 20 * t * t]);
      c.push([x0 + (x1 - x0) * t, fy + 62, 1 + 20 * t * t]);
    }
    b.ribbon(a, c);
    b.color('#6E7176').quad([lowX, fy - 62, 0], [lowX, fy + 62, 0], [lowX, fy + 62, 1], [lowX, fy - 62, 1]);
    b.color('#6E7176').quad([x1, fy - 62, 0], [x1, fy + 62, 0], [x1, fy + 62, 21], [x1, fy - 62, 21]);
  };
  bank(fx - 26, fx - 52, fx - 26);
  bank(fx + 26, fx + 52, fx + 26);
  b.color('#5C8A4D').quad([fx - 26, fy - 62, 0.2], [fx + 26, fy - 62, 0.2], [fx + 26, fy + 62, 0.2], [fx - 26, fy + 62, 0.2]);
  // press box on the west rim (2003: the present form, estimated)
  b.color('#6E7176').box(fx - 53, fy, 21, 6, 40, 5);
}

addLM({
  id: 'michie_stadium',
  name: 'Michie Stadium, West Point',
  kind: 'stadium',
  built: [1924.0, 1924.8],
  end: 9999,
  anchor: [-73.96417, 41.3875],
  build: msBuild,
  replaces: [MS_RING],
  facts: {
    Construction: 'opened in 1924 (16,000 seats); east grandstand 1962, west upper deck 1969, press box 2003; named for Dennis Michie, who started the football team in 1890',
    Setting: 'north-south field at 335 ft above sea level, west of Lusk Reservoir',
    Model: 'two sloped stands either side of a 52 x 124 m field, placed on the bowl outline of today (14,603 m2, which includes the later expansions); stand height 21 m and the pitch are estimated; the 1924 stadium was smaller and is not reconstructed'
  },
  sources: [WIKI + 'Michie_Stadium', OVT]
});

// Fort Putnam (1778). Anchor (-73.963923, 41.390089) = the article's coordinates. Footprint 'Fort Putnam'
// (Overture 0ba30d8e): 98.7 x 68.7 m. Wikipedia: built by Colonel Rufus Putnam's 5th Massachusetts
// Regiment at West Point in the Revolutionary War; the fort fell to ruin and was restored from 1907.
const FP_RING = P(-9.7, 38.1, -24.4, 12.5, -38.9, 7.3, -29.0, -6.3, -19.3, -35.8, -5.5, -34.5, -2.4, -46.3, 3.4, -53.2, 21.1, -55.1, 26.5, -53.9, 30.7, -51.8, 33.7, -49.3, 35.7, -46.1, 36.3, -41.2, 22.2, -16.1, 29.5, -3.1, 23.3, 3.7, 20.8, 6.4, 31.7, 17.9, 20.2, 25.2, 15.7, 45.4, 3.2, 36.2);

function fpBuild(b: MeshBuilder) {
  const H = 5.2;
  b.color('#8A8478').prism(FP_RING, 0, H, {holes: [scaleAbout(FP_RING, 0.93)]}); // stone rampart wall (estimated thickness 2-3 m)
  b.color('#6F6A5F').prism(scaleAbout(FP_RING, 0.93), 0, 1.2, {top: true}); // inner floor
  // bomb-proof barracks and the magazine (estimated)
  b.color('#8A8478').box(8, -20, 0, 14, 7, 3.4);
  b.color('#5D5A52').gable(8, -20, 14.8, 7.8, 3.4, 1.6, false);
  b.color('#8A8478').box(-12, 6, 0, 6, 6, 2.8);
}

addLM({
  id: 'fort_putnam_west_point',
  name: 'Fort Putnam, West Point',
  kind: 'monument',
  built: [1778.0, 1779.5],
  end: 9999,
  anchor: [-73.963923, 41.390089],
  build: fpBuild,
  replaces: [FP_RING],
  facts: {
    Construction: 'built in 1778 by Colonel Rufus Putnam\'s 5th Massachusetts Regiment on the hill above West Point; fell into ruin, restored from 1907 (the stone fort seen today)',
    Model: 'rampart outline from the footprint of the restored fort (98.7 x 68.7 m); wall height 5.2 m, thickness and the interior buildings are estimated; the footprint is that of the restoration, so the 1778 plan is approximated by it; the end of the log-and-earth works of the 1780s is not modelled'
  },
  sources: [WIKI + 'Fort_Putnam', OVT]
});

// ====================================================================== Bannerman's Castle, Pollepel Island (1901-)
// Anchor (-73.98887, 41.455314) (article coordinates). Footprints 'Bannerman Castle' (Overture 080f421b,
// 1,648 m2, 53 x 45 m) and 'Bannerman Family Residence' (498d6628, 103 m2). Wikipedia (Pollepel Island):
// Bannerman bought the island in November 1900 and began to build an arsenal in spring 1901; a smaller
// castle built as his residence; a fire in 1969 left the ruins.
const BC_RING = P(77.9, 103.0, 77.0, 96.6, 50.4, 84.3, 52.0, 72.9, 60.9, 73.7, 62.6, 58.2, 68.2, 59.5, 70.1, 48.3, 81.5, 50.2, 82.8, 51.6, 89.2, 51.3, 90.8, 53.0, 101.6, 53.4, 100.6, 59.4, 89.0, 57.7, 88.1, 65.2, 97.7, 71.1, 91.8, 104.1);
const BR_RING = P(7.0, 5.8, 6.1, 5.8, -1.7, 3.2, 1.3, -6.7, 2.3, -7.9, 3.3, -7.9, 4.2, -7.3, 4.5, -6.3, 4.3, -5.8, 7.7, -4.8, 8.3, -5.4, 9.2, -5.5, 10.0, -5.1, 10.3, -4.2, 10.1, -3.4, 9.3, -2.8, 8.4, -2.9, 7.4, 0.6, 8.5, 1.2, 9.2, 2.7, 9.0, 4.4, 7.8, 5.5);

function bcBuild(b: MeshBuilder) {
  // arsenal: stepped masonry blocks of a Scottish castle (estimated heights)
  b.color('#8F8A7E').prism(BC_RING, 0, 22);
  b.color('#6E695F').prism(scaleAbout(BC_RING, 0.97), 22, 23.2);
  // corner turrets
  const c = centroid(BC_RING);
  b.color('#8F8A7E');
  for (const [x, y] of [[53.5, 74], [91, 102], [100, 55], [71, 50]]) {
    b.cylinder(x, y, 2.4, 0, 27, 8);
    b.color('#5E5A52').pyramid(circle(x, y, 2.9, 8), 27, [x, y, 31]);
    b.color('#8F8A7E');
  }
  void c;
  // residence: round tower with conical roof, two storeys (estimated)
  b.color('#A19A8B').prism(BR_RING, 0, 7.5);
  b.color('#5E5A52').pyramid(BR_RING, 7.5, [5.3, 0, 12.5]);
}

addLM({
  id: 'bannermans_castle',
  name: "Bannerman's Castle (Pollepel Island arsenal)",
  kind: 'building',
  built: [1901.3, 1918.0],
  end: 9999,
  anchor: [-73.98887, 41.455314],
  build: bcBuild,
  replaces: [BC_RING, BR_RING],
  facts: {
    Construction: 'Francis Bannerman VI bought the island in November 1900 and began to build the arsenal in spring 1901, adding to it for years; a smaller castle beside it as his residence',
    Use: 'storage of army surplus, advertisement of the Bannerman business; roofs lost to a fire in 1969',
    Model: 'plans from the footprints (arsenal 1,648 m2, residence 103 m2); heights (arsenal wall 22 m, turrets 31 m, residence 12.5 m) and the stepped massing are estimated; completion 1918 is estimated (the building grew in stages); the fire-damaged state after 1969 is not modelled'
  },
  sources: [WIKI + 'Pollepel_Island', OVT]
});

// ====================================================================== Vassar College Main Building (1861-1865)
// Anchor (-73.895831, 41.686675). Footprint 'Main Building' (Overture 2921f630): 146 x 99 m, 5,839 m2.
// Wikipedia (Main Building (Vassar College)): James Renwick Jr., Second Empire, brick, four storeys with
// a fifth under the mansard roof, U-shaped: central portion 500 ft (152 m) long, wings 164 ft (50 m);
// built from 1861 (the college's first classes were in 1865).
const VM_RING = P(80.3, 48.1, 78.8, 47.9, 78.1, 53.0, 77.4, 58.1, 71.2, 57.3, 71.9, 52.2, 72.6, 47.1, 71.2, 46.9, 71.4, 45.7, 55.5, 43.7, 56.3, 36.9, 51.4, 36.3, 50.7, 42.4, 48.7, 42.2, 44.6, 77.4, 48.9, 77.9, 47.4, 91.1, 43.1, 90.6, 11.9, 87.0, 11.8, 88.4, -5.3, 86.4, -4.0, 75.4, -3.0, 66.8, 14.0, 68.8, 13.4, 73.8, 27.1, 75.4, 27.8, 69.5, 34.1, 70.2, 37.5, 40.9, 26.8, 39.7, 27.8, 31.0, 29.9, 31.3, 31.0, 22.1, 28.5, 21.8, 29.2, 16.1, 29.9, 10.4, 33.0, 10.8, 34.1, 1.4, 31.0, 1.1, 31.9, -7.5, 44.0, -6.2, 47.4, -35.5, 40.5, -36.3, 41.2, -42.3, 25.2, -44.1, 24.7, -39.5, 12.1, -40.9, 13.2, -50.0, 14.1, -57.8, 26.6, -56.4, 26.6, -55.7, 61.5, -51.7, 63.9, -51.5, 62.5, -39.9, 60.2, -40.1, 56.1, -4.8, 55.4, 1.0, 56.9, 1.1, 60.9, 1.4, 61.5, -5.5, 73.5, -4.5, 73.6, -5.3, 85.6, -4.3, 102.3, -3.0, 102.1, -0.1, 99.7, -0.3, 99.2, 5.5, 96.5, 5.3, 96.2, 9.2, 98.6, 9.4, 98.0, 16.8, 99.4, 16.9, 100.0, 17.8, 101.3, 17.3, 103.4, 19.7, 100.5, 22.2, 102.2, 24.1, 99.9, 26.2, 102.1, 28.6, 99.4, 31.0, 96.2, 30.6, 95.1, 38.9, 93.0, 38.7, 92.7, 40.8, 95.2, 41.2, 94.1, 48.7, 88.2, 47.9, 88.1, 49.1, 87.4, 54.2, 86.7, 59.3, 80.5, 58.5, 81.2, 53.4, 81.9, 48.3);

function vmBuild(b: MeshBuilder) {
  const EAVE = 17.0; // four storeys of ~4.2 m (estimated)
  b.color('#A4553F').prism(VM_RING, 0, EAVE);
  b.color('#4F5256').loft([VM_RING, scaleAbout(VM_RING, 0.95, [52, 20])], [EAVE, EAVE + 5.0], {top: true}); // mansard
  // central pavilion with its higher mansard (estimated)
  b.color('#A4553F').box(52, 20, EAVE, 24, 20, 3);
  b.color('#4F5256').pyramid(rect(52, 20, 24, 20), EAVE + 3, [52, 20, EAVE + 9]);
}

addLM({
  id: 'vassar_main_building',
  name: 'Main Building, Vassar College',
  kind: 'building',
  built: [1861.0, 1865.7],
  end: 9999,
  anchor: [-73.895831, 41.686675],
  build: vmBuild,
  replaces: [VM_RING],
  facts: {
    Construction: 'built from 1861 to the design of James Renwick Jr.; the college opened in 1865',
    Form: 'Second Empire brick building, four storeys and a fifth under a mansard roof; U-shaped, 500 ft (152 m) central block with 164 ft (50 m) wings',
    Model: 'plan from the footprint (5,839 m2, which includes later additions); eave height 17 m, the mansard (5 m), the central pavilion are estimated; completion 1865.7 is estimated within the opening year'
  },
  sources: [WIKI + 'Main_Building_(Vassar_College)', WIKI + 'Vassar_College', OVT]
});

// ====================================================================== Springwood, Hyde Park (1915 form)
// Anchor (-73.93556, 41.76722) (41 46 2 N 73 56 8 W, article). Footprint (Overture d920e1d8): 53 x 25 m,
// 933 m2. Wikipedia (Home of Franklin D. Roosevelt NHS): the centre of the house is a Federal farmhouse
// of about 1800; bought in 1866 by James Roosevelt; "in 1915 Franklin, with his mother, undertook a final
// major enlargement and remodeling" (fieldstone wings, a south tower).
const SW_RING = P(-0.7, -11.6, -0.2, 11.2, 8.7, 11.0, 9.0, 24.4, -12.2, 24.8, -12.8, -28.0, -0.2, -28.4, 1.3, -25.5, 5.4, -25.7, 5.9, -28.4, 9.6, -28.6, 12.2, -25.6, 12.0, -16.1, 6.5, -16.0, 6.7, -11.7);

function swBuild(b: MeshBuilder) {
  const EAVE = 7.4;
  b.color('#D9D2BF').prism(SW_RING, 0, EAVE); // stucco central block (estimated colour)
  b.color('#6B6862');
  hipOver(b, SW_RING, EAVE, 3.4, 0.7);
  b.color('#8A826F').prism(P(-12.2, 12, 9.0, 12, 9.0, 24.4, -12.2, 24.8), 0, EAVE + 0.2, {top: true}); // north fieldstone wing (estimated extent)
  tower(b, -6.5, -23.5, 6.5, EAVE - 0.2, 11.8, 14.6, '#D9D2BF', '#5E5B56'); // south tower (the cited tower bedroom)
}

addLM({
  id: 'springwood_hyde_park',
  name: 'Springwood (Home of Franklin D. Roosevelt)',
  kind: 'building',
  built: [1915.0, 1916.0],
  end: 9999,
  anchor: [-73.93556, 41.76722],
  build: swBuild,
  replaces: [SW_RING],
  facts: {
    Construction: 'a Federal farmhouse of about 1800, bought by James Roosevelt in 1866, enlarged and remodelled in 1915 with a tower and wings by Franklin D. Roosevelt and his mother',
    Model: 'the house of today and of the 1915 remodelling, from the footprint (933 m2); the earlier farmhouse alone is not modelled; heights (eave 7.4 m, tower 14.6 m), the roof and the wing extents are estimated; 1915-16 is the cited remodelling year with an estimated duration'
  },
  sources: [WIKI + 'Home_of_Franklin_D._Roosevelt_National_Historic_Site', OVT]
});

// ====================================================================== Vanderbilt Mansion, Hyde Park (1896-1899)
// Anchor (-73.94194, 41.79611) (article coordinates 41 47 46 N 73 56 31 W). Footprint (Overture 4d9f67c8):
// 53 x 31 m, 1,153 m2, three storeys, OSM height 11 m. Wikipedia: McKim, Mead & White for Frederick and
// Louise Vanderbilt, 54 rooms, "built between 1896 and 1899"; the property was bought in May 1895.
const VD_RING = P(-26.6, 37.9, -26.9, 60.7, -46.0, 60.5, -45.7, 42.3, -50.5, 41.2, -54.6, 37.8, -55.5, 34.0, -54.1, 30.0, -50.4, 26.8, -45.5, 25.5, -45.3, 7.5, -26.3, 7.7, -26.5, 28.4, -24.3, 28.6, -24.4, 38.0);

function vdBuild(b: MeshBuilder) {
  const EAVE = 11.0;
  b.color('#D6CDB6').prism(VD_RING, 0, EAVE); // limestone-coloured walls (estimated colour)
  b.color('#B9AF98').prism(scaleAbout(VD_RING, 1.01), EAVE, EAVE + 1.0, {top: true}); // balustrade band
  b.color('#6B6A68');
  hipOver(b, VD_RING, EAVE + 1.0, 2.6, 0.7);
  // columned portico on the river (west) front (estimated)
  b.color('#E4DCC8');
  for (let i = 0; i < 4; i++) b.cylinder(-57.5, 14 + i * 3.4, 0.55, 0, 9.5, 8);
  b.color('#D6CDB6').box(-57.5, 18.5, 9.5, 3.4, 13, 1.4);
}

addLM({
  id: 'vanderbilt_mansion_hyde_park',
  name: 'Vanderbilt Mansion, Hyde Park',
  kind: 'building',
  built: [1896.0, 1899.0],
  end: 9999,
  anchor: [-73.94194, 41.79611],
  build: vdBuild,
  replaces: [VD_RING],
  facts: {
    Construction: 'McKim, Mead & White for Frederick W. and Louise Vanderbilt, built between 1896 and 1899; 54 rooms',
    Height: 'footprint height 11 m (OpenStreetMap)',
    Model: 'plan from the footprint (1,153 m2); eave height 11 m, the roof, balustrade and the portico are estimated'
  },
  sources: [WIKI + 'Vanderbilt_Mansion_National_Historic_Site', OVT]
});

// ====================================================================== New Croton Dam (1892-1906)
// Anchor (-73.8567, 41.2275). Plan: the OpenStreetMap way 177603533 'New Croton Dam' (waterway=dam,
// height 91, start_date 1906), thinned to 48 of 96 nodes. Wikipedia: masonry gravity dam, construction
// began 1892 and was completed in 1906; 2,188 ft (667 m) long, 297 ft (90.5 m) high from base to crest,
// 266 ft (81 m) wide at the base.
const CD_RING = P(-4, 8, 9, -6, 69, -99, 121, -159, 125, -164, 167, -212, 171, -217, 191, -239, 185, -244, 170, -249, 166, -250, 160, -245, 161, -237, 163, -234, 164, -230, 163, -228, 162, -224, 159, -223, 156, -217, 110, -176, 103, -172, 96, -163, 85, -149, 71, -136, 51, -120, 26, -93, -16, -43, -29, -30, -34, -36, -43, -25, -50, -10, -55, 0, -55, 16, -51, 28, -22, 69, 14, 95, 61, 137, 97, 169, 128, 196, 150, 225, 149, 234, 132, 194, 8, 77, -8, 62, -16, 48, -21, 29, -19, 21, -16, 20);

function cdBuild(b: MeshBuilder) {
  // The anchor is on the crest ground; the masonry reaches down 90.5 m, hidden below the terrain
  // (the 297 ft is base to crest, the valley floor under the dam is not in the terrain grid).
  b.color('#8C887E').prism(CD_RING, -88, 2.5);
  b.color('#6F6B63').prism(scaleAbout(CD_RING, 0.97), 2.5, 3.6); // parapet band
}

addLM({
  id: 'new_croton_dam',
  name: 'New Croton Dam',
  kind: 'building',
  built: [1892.0, 1906.0],
  end: 9999,
  anchor: [-73.8567, 41.2275],
  build: cdBuild,
  replaces: [CD_RING],
  facts: {
    Construction: 'begun in 1892, completed in 1906 (Alphonse Fteley); masonry gravity dam of the New York City water supply',
    Dimensions: '2,188 ft (667 m) long, 297 ft (90.5 m) from base to crest, 266 ft (81 m) thick at the base',
    Model: 'the crest and spillway outline of the OpenStreetMap way (about 300 m of masonry, the earth embankments are not drawn); crest 2.5 m above the ground at the anchor and the parapet are estimated; the body is a straight-sided prism (the real section tapers); the old dam of 1842 is not modelled'
  },
  sources: [WIKI + 'New_Croton_Dam', OSM + 'way/177603533']
});

// ----- bridges follow (part B)
