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
  hipOver(b, PM_MILL, 6.2, 3.6, 0.92);
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
  // The ring is the west stand with its north and south end structures; the east stand is a separate
  // footprint (Overture fbe0064e, 121 x 27.5 m centred 50.5, 5.6). The field lies between them.
  const y0 = -54;
  const y1 = 68;
  const bank = (xf: number, xb: number, top: number) => {
    const a: V3[] = [];
    const c: V3[] = [];
    for (let i = 0; i <= 6; i++) {
      const t = i / 6;
      a.push([xf + (xb - xf) * t, y0, 1 + (top - 1) * t * t]);
      c.push([xf + (xb - xf) * t, y1, 1 + (top - 1) * t * t]);
    }
    b.color('#8C8F94').ribbon(a, c);
    b.color('#6E7176');
    b.quad([xb, y0, -1], [xb, y1, -1], [xb, y1, top], [xb, y0, top]); // back wall
    b.tri([xf, y0, 0], [xb, y0, 0], [xb, y0, top]); // ends of the bank
    b.tri([xf, y1, 0], [xb, y1, 0], [xb, y1, top]);
  };
  bank(-30, -82, 22); // west stand (1924; upper deck 1969)
  bank(37, 64, 14); // east stand (1962)
  b.color('#5C8A4D').quad([-30, y0 - 3, 0.2], [37, y0 - 3, 0.2], [37, y1 + 3, 0.2], [-30, y1 + 3, 0.2]);
  // north and south end structures (field house, tunnel): low blocks (estimated)
  b.color('#7B7E83').box(-11, 88, -1, 88, 33, 9);
  b.color('#7B7E83').box(-48, -90, -1, 49, 60, 8);
  // press box on the west rim (2003)
  b.color('#6E7176').box(-80, 7, 22, 5, 38, 4.5);
}

addLM({
  id: 'michie_stadium',
  name: 'Michie Stadium, West Point',
  kind: 'stadium',
  built: [1924.0, 1924.8],
  end: 9999,
  anchor: [-73.96417, 41.3875],
  build: msBuild,
  replaces: [MS_RING, rect(50.5, 5.6, 27.5, 121)],
  facts: {
    Construction: 'opened in 1924 (16,000 seats); east grandstand 1962, west upper deck 1969, press box 2003; named for Dennis Michie, who started the football team in 1890',
    Setting: 'north-south field at 335 ft above sea level, west of Lusk Reservoir',
    Model: 'a west and an east stand either side of the field (67 m between the stands, 124 m long) on the footprints of today (west stand with end structures 14,603 m2; east stand 3,335 m2); stand heights (22 m, 14 m), the slope and the end blocks are estimated; the 1924 stadium was smaller and is not reconstructed'
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
  b.frame(-6.65, -8.6, 0, 0, () => b.gable(0, 0, 12.4, 39.4, EAVE, 3.6, true)); // main block, ridge north-south
  b.frame(-1.6, 18.2, 0, 90, () => b.hip(0, 0, 13.0, 21.4, EAVE, 2.8)); // north wing
  b.frame(6.0, -22.2, 0, 0, () => b.hip(0, 0, 12.4, 11.8, EAVE, 2.4)); // south-east wing
  b.color('#8A826F').prism(P(-12.2, 12, 9.0, 12, 9.0, 24.4, -12.2, 24.8), 0, EAVE + 0.2, {top: false}); // north fieldstone wing (estimated extent)
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
  b.frame(-36.1, 34.2, 0, 0, () => b.hip(0, 0, 19.2, 52.4, EAVE + 1.0, 2.6)); // roof over the main block
  // columned portico in the river (west) bay (estimated)
  b.color('#E4DCC8');
  for (let i = 0; i < 4; i++) b.cylinder(-53.2, 28.6 + i * 4.3, 0.55, 0, 9.5, 8);
  b.color('#D6CDB6').box(-52.2, 34.2, 9.5, 5, 15, 1.4);
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
  b.color('#6F6B63').prism(CD_RING, 2.5, 3.6); // parapet band
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

// ====================================================================== bridges
// Bridges are modelled from sea level (the viewer does not lift them onto the terrain). Deck paths
// are the centre lines of the bridge-flagged road segments in Overture 2026-10-21.0 (OpenStreetMap
// data, ODbL), or the OpenStreetMap way named in each comment.

type Pth = {pts: V2[]; cum: number[]; len: number};
type PP = {x: number; y: number; tx: number; ty: number};

function mkPath(pts: V2[]): Pth {
  const cum = [0];
  for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  return {pts, cum, len: cum[cum.length - 1]};
}

function ptAt(p: Pth, d: number): PP {
  const dd = Math.min(Math.max(d, 0), p.len);
  let i = 0;
  while (i < p.pts.length - 2 && p.cum[i + 1] < dd) i++;
  const [x0, y0] = p.pts[i];
  const [x1, y1] = p.pts[i + 1];
  const L = p.cum[i + 1] - p.cum[i] || 1;
  const t = (dd - p.cum[i]) / L;
  return {x: x0 + (x1 - x0) * t, y: y0 + (y1 - y0) * t, tx: (x1 - x0) / L, ty: (y1 - y0) / L};
}

/** Point `o` metres to the left of the direction of travel. */
function side(q: PP, o: number): V2 {
  return [q.x - q.ty * o, q.y + q.tx * o];
}

function bearingOf(q: PP) {
  return (Math.atan2(q.tx, q.ty) * 180) / Math.PI;
}

/** The path shifted `o` metres to its left. */
function shifted(pts: V2[], o: number): V2[] {
  return pts.map((_, i) => {
    const a = pts[Math.max(i - 1, 0)];
    const c = pts[Math.min(i + 1, pts.length - 1)];
    const L = Math.hypot(c[0] - a[0], c[1] - a[1]) || 1;
    return [pts[i][0] - ((c[1] - a[1]) / L) * o, pts[i][1] + ((c[0] - a[0]) / L) * o] as V2;
  });
}

/** Distance along the path at which its x coordinate first reaches `x` (paths run west to east). */
function dAtX(p: Pth, x: number) {
  for (let i = 0; i < p.pts.length - 1; i++) {
    if (p.pts[i][0] <= x && p.pts[i + 1][0] >= x) return p.cum[i] + ((x - p.pts[i][0]) / (p.pts[i + 1][0] - p.pts[i][0] || 1)) * (p.cum[i + 1] - p.cum[i]);
  }
  return x < p.pts[0][0] ? 0 : p.len;
}

/** A deck ribbon along a path between two stations, `zf(d)` the top height. */
function deckStrip(b: MeshBuilder, p: Pth, d0: number, d1: number, step: number, zf: (d: number) => number, hw: number, thick: number, col: string, off = 0) {
  const n = Math.max(1, Math.ceil((d1 - d0) / step));
  b.color(col);
  for (let i = 0; i < n; i++) {
    const a = d0 + ((d1 - d0) * i) / n;
    const c = d0 + ((d1 - d0) * (i + 1)) / n;
    const qa = ptAt(p, a);
    const qc = ptAt(p, c);
    const za = zf(a);
    const zc = zf(c);
    const L0 = side(qa, off + hw);
    const R0 = side(qa, off - hw);
    const L1 = side(qc, off + hw);
    const R1 = side(qc, off - hw);
    b.quad([L0[0], L0[1], za], [R0[0], R0[1], za], [R1[0], R1[1], zc], [L1[0], L1[1], zc]);
    b.quad([L0[0], L0[1], za - thick], [L1[0], L1[1], zc - thick], [R1[0], R1[1], zc - thick], [R0[0], R0[1], za - thick]);
    b.quad([L0[0], L0[1], za - thick], [L1[0], L1[1], zc - thick], [L1[0], L1[1], zc], [L0[0], L0[1], za]);
    b.quad([R0[0], R0[1], za - thick], [R1[0], R1[1], zc - thick], [R1[0], R1[1], zc], [R0[0], R0[1], za]);
  }
}

/** A pier (box across the deck) under a path station. */
function pier(b: MeshBuilder, p: Pth, d: number, off: number, across: number, along: number, zTop: number, zBot: number, col: string) {
  const q = ptAt(p, d);
  const c = side(q, off);
  b.color(col);
  b.frame(c[0], c[1], 0, bearingOf(q), () => b.box(0, 0, zBot, across, along, zTop - zBot));
}

// ====================================================================== Tappan Zee Bridge (1952-1955; demolished 2017-2019)
// Anchor (-73.88096, 41.07112), midway between the towers of the new bridge's main span; x east, y north.
// New-bridge paths: Overture's bridge-flagged 'New York State Thruway' segments (the two roadways of the
// 2017/2018 twin spans), sampled every ~70 m; the main-span pylons (bridge:support=pylon, height 128 m)
// are the four OpenStreetMap ways 1005972999, 1005973000, 1005973001, 1005973002 at x = -181.5 / +181.5 m.
// The old bridge is not in any dataset at hand: its line is the new south (eastbound) roadway shifted
// 78 m south (the new eastbound span stood 160 ft from the old bridge, Wikipedia; plus half the two
// widths), which is an estimate.
const TZ_ANCHOR: V2 = [-73.88096, 41.07112];
const TZ_N = P(-3198, 337, -3153, 284, -3105, 235, -3052, 190, -2996, 150, -2936, 115, -2874, 85, -2810, 60, -2743, 41, -2676, 27, -2607, 19, -2538, 17, -2400, 18, -2261, 18, -2123, 18, -1985, 18, -1847, 18, -1709, 18, -1570, 18, -1432, 18, -1294, 18, -1156, 18, -1017, 19, -879, 21, -741, 23, -603, 25, -465, 26, -326, 26, -188, 26, -50, 26, 88, 26, 226, 26, 365, 26, 503, 24, 571, 16, 639, 3, 706, -16, 770, -40, 833, -70, 893, -104, 950, -143, 1003, -187, 1053, -235, 1099, -287, 1143, -340, 1186, -394, 1229, -448);
const TZ_S = P(-3216, 309, -3173, 255, -3125, 205, -3073, 160, -3019, 117, -2960, 81, -2899, 50, -2834, 25, -2768, 5, -2701, -9, -2632, -18, -2563, -20, -2425, -20, -2287, -20, -2149, -20, -2011, -20, -1873, -20, -1735, -20, -1597, -20, -1459, -20, -1321, -20, -1183, -20, -1045, -20, -907, -22, -769, -25, -630, -27, -492, -28, -354, -28, -216, -28, -78, -28, 60, -28, 198, -28, 336, -28, 474, -29, 543, -34, 611, -45, 678, -62, 743, -84, 806, -112, 867, -145, 924, -183, 979, -226, 1029, -273, 1075, -324, 1118, -378, 1161, -432, 1203, -487);
const TZ_CLEAR = 139 * 0.3048; // 42.4 m above the water (new bridge, Wikipedia)
const TZ_TOWER = 419 * 0.3048; // 127.7 m (OSM 128 m)

/** Deck top height at east coordinate x: clearance over the channel, 2.7 % grades down to the low trestle, a ramp at each shore. */
function tzDeckZ(x: number, high: number, low: number) {
  const a = Math.abs(x);
  const core = a <= 190 ? high : Math.max(low, high - (a - 190) * 0.027);
  return x < -3150 ? Math.max(5, core - (-3150 - x) * 0.05) : x > 1150 ? Math.max(5, core - (x - 1150) * 0.05) : core;
}

/** One span of the new bridge: a deck on the path, piers, two inverted-Y pylons with their stays. */
function cuomoSpan(b: MeshBuilder, pts: V2[], width: number, towerOff: number) {
  const p = mkPath(pts);
  const zf = (d: number) => tzDeckZ(ptAt(p, d).x, TZ_CLEAR + 3, 14);
  const hw = width / 2;
  deckStrip(b, p, 0, p.len, 18, zf, hw, 3.0, '#B8B4AC');
  // piers every ~70 m under the trestle, none under the channel span
  b.color('#9A968E');
  for (let d = 35; d < p.len - 10; d += 69) {
    const q = ptAt(p, d);
    if (Math.abs(q.x) < 175) continue;
    pier(b, p, d, 0, Math.min(8, hw), 3.4, zf(d) - 3, -6, '#9A968E');
  }
  // pylons
  for (const sx of [-1, 1]) {
    const d = dAtX(p, sx * 181.5);
    const q = ptAt(p, d);
    const zd = zf(d);
    b.frame(q.x, q.y, 0, bearingOf(q), () => {
      b.color('#C9C5BC');
      for (const s of [-1, 1]) b.beam([s * 7, 0, -6], [s * 1.2, 0, 62], 3.4, 4.2);
      b.box(0, 0, 62, 3.4, 4.2, TZ_TOWER - 62);
      // stays: two planes at the deck edges' inside, 8 stays each way
      b.color('#D8D6D0');
      for (const dir of [-1, 1]) {
        for (let k = 1; k <= 8; k++) {
          const dist = 24 + k * 19.5;
          const yy = dir * dist;
          const dd = Math.min(Math.max(d + yy, 0), p.len);
          void dd;
          for (const xo of [-hw + 1.5, hw - 1.5]) b.beam([0, 0, TZ_TOWER - 4 - (k - 1) * 1.6], [xo, yy, zd + 0.3], 0.28);
        }
      }
    });
  }
  void towerOff;
}

function cuomoBuild(north: boolean) {
  return (b: MeshBuilder) => {
    if (north) cuomoSpan(b, TZ_N, 26.5, 0);
    else cuomoSpan(b, TZ_S, 29.3, 0);
  };
}

addLM({
  id: 'cuomo_bridge_north_span',
  name: 'Governor Mario M. Cuomo Bridge, northbound / westbound span',
  kind: 'bridge',
  built: [2013.8, 2017.65],
  end: 9999,
  anchor: TZ_ANCHOR,
  build: cuomoBuild(true),
  facts: {
    Construction: 'construction began in 2013; the northbound / westbound span opened on August 26, 2017 (Tappan Zee Bridge (2017-present))',
    Design: 'twin cable-stayed spans, main span 1,200 ft (366 m), towers 419 ft (128 m), 139 ft (42 m) above the water; this deck 87 ft (26.5 m) wide',
    Model: 'deck line and pylon positions from OpenStreetMap / Overture (towers 363 m apart against the cited 366 m); deck heights on the trestle (14 m), the grades, the pier spacing (~70 m) and the stay fan are estimated; the four lower pylons of the side spans are not modelled; construction start 2013.8 is estimated within 2013'
  },
  sources: [WIKI + 'Tappan_Zee_Bridge_(2017–present)', OSM + 'way/1005973000', OVT]
});

addLM({
  id: 'cuomo_bridge_south_span',
  name: 'Governor Mario M. Cuomo Bridge, southbound / eastbound span',
  kind: 'bridge',
  built: [2014.5, 2018.7],
  end: 9999,
  anchor: TZ_ANCHOR,
  build: cuomoBuild(false),
  facts: {
    Construction: 'the southbound / eastbound span opened on September 11, 2018, after traffic had moved to the new northbound span on October 6, 2017 (Tappan Zee Bridge (2017-present))',
    Design: 'twin cable-stayed spans, main span 1,200 ft (366 m), towers 419 ft (128 m), 139 ft (42 m) above the water; this deck 96 ft (29.3 m) wide',
    Model: 'as the northbound span; construction start 2014.5 is estimated (the article gives only 2013 for the project)'
  },
  sources: [WIKI + 'Tappan_Zee_Bridge_(2017–present)', OSM + 'way/1005972999', OVT]
});

// Old bridge (cantilever through-truss): Wikipedia: construction March 1952, opened December 15, 1955; 16,013 ft long,
// cantilever span 1,212 ft (369 m), 138 ft (42 m) clearance, 90 ft (27.4 m) wide; all traffic moved to the new bridge on
// October 6, 2017, the east half blown up on January 15, 2019, the west half removed by May 2019.
function oldTzBuild(b: MeshBuilder) {
  const pts = shifted(TZ_S, 78 * -1); // 78 m south of the new eastbound roadway
  const p = mkPath(pts);
  const hw = 13.7;
  const zf = (d: number) => tzDeckZ(ptAt(p, d).x, 42.1 + 2.5, 12);
  deckStrip(b, p, 0, p.len, 18, zf, hw, 2.6, '#7E7D78');
  // approach piers every ~46 m (estimated)
  for (let d = 23; d < p.len - 10; d += 46) {
    const q = ptAt(p, d);
    if (Math.abs(q.x) < 372) pier(b, p, d, 0, 18, 2.6, zf(d) - 2.6, -6, '#8A8984');
    else pier(b, p, d, 0, 18, 2.6, zf(d) - 2.6, -6, '#8A8984');
  }
  // the cantilever through-truss between x = -370 and +370: top chord peaks over the two main piers at x = +-185
  const ptsTop = (xo: number) => {
    const out: V3[] = [];
    for (let x = -370; x <= 370; x += 18.5) {
      const d = dAtX(p, x);
      const q = ptAt(p, d);
      const c = side(q, xo);
      const h = 14 + 16 * (1 - ((Math.abs(x) - 185) / 185) ** 2);
      out.push([c[0], c[1], zf(d) + h]);
    }
    return out;
  };
  b.color('#6E6D69');
  for (const xo of [-hw + 1, hw - 1]) {
    const top = ptsTop(xo);
    b.polyline(top, 1.1);
    for (let i = 0; i < top.length; i++) {
      const d = dAtX(p, -370 + i * 18.5);
      const q = ptAt(p, d);
      const c = side(q, xo);
      b.beam([c[0], c[1], zf(d)], top[i], 0.7); // posts
      if (i < top.length - 1) {
        const d2 = dAtX(p, -370 + (i + 1) * 18.5);
        const c2 = side(ptAt(p, d2), xo);
        b.beam(i % 2 === 0 ? [c[0], c[1], zf(d)] : top[i], i % 2 === 0 ? top[i + 1] : [c2[0], c2[1], zf(d2)], 0.5); // diagonals
      }
    }
  }
  // portal bracing at three stations
  b.color('#6E6D69');
  for (const x of [-370, -185, 0, 185, 370]) {
    const d = dAtX(p, x);
    const q = ptAt(p, d);
    const h = 14 + 16 * (1 - ((Math.abs(x) - 185) / 185) ** 2);
    const l = side(q, -hw + 1);
    const r = side(q, hw - 1);
    b.beam([l[0], l[1], zf(d) + h], [r[0], r[1], zf(d) + h], 0.7);
  }
}

addLM({
  id: 'tappan_zee_bridge',
  name: 'Tappan Zee Bridge (1955-2019)',
  kind: 'bridge',
  built: [1952.2, 1955.96],
  end: 2019.4,
  anchor: TZ_ANCHOR,
  build: oldTzBuild,
  facts: {
    Construction: 'construction began in March 1952; opened on December 15, 1955 (the longest bridge of the New York State Thruway); traffic left it on October 6, 2017; demolished in 2018-2019',
    Dimensions: '16,013 ft (4.9 km) long, cantilever span 1,212 ft (369 m), 138 ft (42 m) above the water, 90 ft (27.4 m) wide',
    Model: 'the line of the bridge is an estimate: the new eastbound roadway shifted 78 m south (the old bridge is in no dataset at hand); the cantilever through-truss, its panel length (18.5 m) and top-chord heights (30 m above the deck at the main piers), the deck heights on the trestle (12 m) and the pier spacing (46 m) are estimated; end year 2019.4 is the May 2019 removal of the western half'
  },
  sources: [WIKI + 'Tappan_Zee_Bridge_(1955–2017)']
});

// ====================================================================== suspension bridges
type Axis = {anchor: V2; bearing: number; half: number; along: (p: V2) => number; across: (p: V2) => number};

/** Frame from two end points: origin at their midpoint, +y from a to c. */
function axisOf(a: V2, c: V2): Axis {
  const anchor: V2 = [(a[0] + c[0]) / 2, (a[1] + c[1]) / 2];
  const pa = lngLatToLocal(anchor, a);
  const pc = lngLatToLocal(anchor, c);
  const dx = pc[0] - pa[0];
  const dy = pc[1] - pa[1];
  const len = Math.hypot(dx, dy);
  const ux = dx / len;
  const uy = dy / len;
  return {
    anchor,
    bearing: (Math.atan2(dx, dy) * 180) / Math.PI,
    half: len / 2,
    along: p => {
      const l = lngLatToLocal(anchor, p);
      return l[0] * ux + l[1] * uy;
    },
    across: p => {
      const l = lngLatToLocal(anchor, p);
      return l[0] * uy - l[1] * ux;
    }
  };
}

type Susp = {
  half: number; // half the main span
  side: number; // side span length
  towerTop: number;
  deckMid: number;
  deckTower: number;
  deckEnd: number;
  hw: number; // half deck width
  legX: number; // tower legs at +-legX
  legW: number;
  legD: number;
  struts: number[]; // heights of the cross struts
  truss: number; // stiffening truss depth
  steel: string;
  towerCol: string;
  hangEvery: number;
  midClear: number; // cable height above the deck at mid-span
};

function suspBridge(b: MeshBuilder, o: Susp) {
  const H = o.half;
  const A = o.half + o.side;
  const deckZ = (y: number) => {
    const a = Math.abs(y);
    if (a <= H) return o.deckMid + (o.deckTower - o.deckMid) * (a / H) ** 2;
    return o.deckTower + ((o.deckEnd - o.deckTower) * (a - H)) / o.side;
  };
  // deck and stiffening trusses
  const N = 36;
  for (let i = 0; i < N; i++) {
    const y0 = -A + (2 * A * i) / N;
    const y1 = -A + (2 * A * (i + 1)) / N;
    const z0 = deckZ(y0);
    const z1 = deckZ(y1);
    b.color('#55524E').quad([-o.hw, y0, z0], [o.hw, y0, z0], [o.hw, y1, z1], [-o.hw, y1, z1]);
    b.color(o.steel);
    for (const x of [-o.hw, o.hw]) {
      b.quad([x, y0, z0 - o.truss], [x, y1, z1 - o.truss], [x, y1, z1 + 1.1], [x, y0, z0 + 1.1]);
    }
    b.quad([-o.hw, y0, z0 - o.truss], [o.hw, y0, z0 - o.truss], [o.hw, y1, z1 - o.truss], [-o.hw, y1, z1 - o.truss]);
  }
  // towers: two legs, cross struts, a cap
  b.color(o.towerCol);
  for (const ty of [-H, H]) {
    for (const x of [-o.legX, o.legX]) b.box(x, ty, -8, o.legW, o.legD, o.towerTop + 8);
    for (const zs of o.struts) b.box(0, ty, zs, 2 * o.legX - o.legW, o.legD * 0.8, 3.2);
    b.box(0, ty, o.towerTop - 2.5, 2 * o.legX + o.legW, o.legD, 2.5);
  }
  // cables (two, over the legs), suspenders and the side spans
  b.color('#3F3D3A');
  for (const x of [-o.legX, o.legX]) {
    const main = parabola([x, -H, o.towerTop - 1], [x, H, o.towerTop - 1], deckMidCable(o), 24);
    b.polyline(main, 0.55);
    const sl = [[x, -H, o.towerTop - 1], [x, -A, o.deckEnd + 2]] as V3[];
    const sr = [[x, H, o.towerTop - 1], [x, A, o.deckEnd + 2]] as V3[];
    b.polyline(parabola(sl[0], sl[1], (sl[0][2] + sl[1][2]) / 2 - 2.5, 8), 0.55);
    b.polyline(parabola(sr[0], sr[1], (sr[0][2] + sr[1][2]) / 2 - 2.5, 8), 0.55);
    b.color('#6A6762');
    for (let y = -H + o.hangEvery; y < H - 1; y += o.hangEvery) {
      const t = y / H;
      const zc = o.towerTop - 1 - (o.towerTop - 1 - deckMidCable(o)) * (1 - t * t);
      b.beam([x, y, zc], [x, y, deckZ(y) + 1], 0.16);
    }
    b.color('#3F3D3A');
  }
  // anchorages
  b.color('#8C887E');
  for (const s of [-1, 1]) b.box(0, s * (A + 12), -10, 2 * o.hw + 12, 26, o.deckEnd + 12);
}

function deckMidCable(o: Susp) {
  return o.deckMid + o.midClear;
}

// ====================================================================== Bear Mountain Bridge (1923-1924)
// Wikipedia: opened November 27, 1924, then the longest suspension span in the world and the first with a
// concrete deck; main span 1,632 ft (497.4 m), length 2,255 ft (687 m), 48 ft (14.6 m) wide, towers 360 ft
// (110 m), 155 ft (47 m) above the water. Axis: the ends of the bridge-flagged 'Bear Mountain Bridge' road in
// Overture (-73.98795, 41.32002) to (-73.97966, 41.31986), 694 m (cited 687 m); the towers sit symmetrically at
// +-248.7 m. Construction began under the 1922 charter (the article: March 1922 act); start 1923.0 is estimated.
const BM = axisOf([-73.98795, 41.32002], [-73.97966, 41.31986]);

addLM({
  id: 'bear_mountain_bridge',
  name: 'Bear Mountain Bridge',
  kind: 'bridge',
  built: [1923.0, 1924.9],
  end: 9999,
  anchor: BM.anchor,
  build: b =>
    b.frame(0, 0, 0, BM.bearing, () =>
      suspBridge(b, {
        half: 248.7,
        side: 94.8,
        towerTop: 360 * 0.3048,
        deckMid: 155 * 0.3048 + 2,
        deckTower: 56,
        deckEnd: 66,
        hw: 7.3,
        legX: 7.8,
        legW: 2.4,
        legD: 3.4,
        struts: [60, 84],
        truss: 3.2,
        steel: '#7C8A92',
        towerCol: '#6D7F8A',
        hangEvery: 15,
        midClear: 3.5
      })
    ),
  facts: {
    Construction: 'authorised in March 1922 (Bear Mountain Hudson River Bridge Company), opened November 27, 1924; the longest suspension span in the world then and the first with a concrete deck',
    Dimensions: 'main span 1,632 ft (497 m), length 2,255 ft (687 m), 48 ft (14.6 m) wide, towers 360 ft (110 m), 155 ft (47 m) clear above the water',
    Model: 'axis from the ends of the bridge-flagged road (694 m long against the cited 687 m), towers placed symmetrically 497 m apart; deck heights at the towers and ends (56 / 66 m), tower leg sizes, cross-strut heights, cable sag and truss depth are estimated; start 1923.0 is estimated'
  },
  sources: [WIKI + 'Bear_Mountain_Bridge', OVT]
});

// ====================================================================== Mid-Hudson Bridge (1925-1930)
// Wikipedia: opened August 25, 1930; construction began 1925; Ralph Modjeski; main span 457.3 m (1,500 ft), length
// 3,000 ft (914 m), steel Gothic towers 315 ft (96 m), 135 ft (41 m) above the Hudson. Axis: through the article's
// coordinates (41 42 11 N 73 56 46 W) at the bearing of the bridge-flagged 'Mid-Hudson Bridge' road (98.1°).
const MH_AX: V2 = [-73.94611, 41.70306];

addLM({
  id: 'mid_hudson_bridge',
  name: 'Mid-Hudson Bridge',
  kind: 'bridge',
  built: [1925.0, 1930.65],
  end: 9999,
  anchor: MH_AX,
  build: b =>
    b.frame(0, 0, 0, 98.1, () =>
      suspBridge(b, {
        half: 228.65,
        side: 228.55,
        towerTop: 315 * 0.3048,
        deckMid: 135 * 0.3048 + 2.5,
        deckTower: 48,
        deckEnd: 44,
        hw: 5.8,
        legX: 6.6,
        legW: 2.2,
        legD: 3.0,
        struts: [58, 78],
        truss: 3.5,
        steel: '#7B8A8F',
        towerCol: '#6D7F85',
        hangEvery: 15,
        midClear: 3.0
      })
    ),
  facts: {
    Construction: 'proposed in 1923, begun in 1925, towers raised in April 1929, opened August 25, 1930 (Ralph Modjeski)',
    Dimensions: 'main span 1,500 ft (457 m), 3,000 ft (914 m) of suspension spans, Gothic steel towers 315 ft (96 m), 135 ft (41 m) above the river',
    Model: 'placed on the article\'s coordinates at the bearing of the bridge-flagged road (98.1°), the side spans are the cited 3,000 ft total less the main span; deck width (11.6 m), deck heights at the towers and ends, tower leg sizes, strut heights and the cable sag are estimated; opening 1930.65 is the date of August 25'
  },
  sources: [WIKI + 'Mid-Hudson_Bridge', OVT]
});

// ====================================================================== Poughkeepsie Railroad Bridge / Walkway Over the Hudson (1886-1889)
// OpenStreetMap way 24185107 (Walkway Over the Hudson, 14 nodes, 2,070 m; the article: 6,768 ft = 2,063 m). Anchor
// (-73.94181, 41.71075), the point it was converted around. Wikipedia: multispan cantilever deck truss, 7 main spans
// (two of 548 ft), deck 212 ft (64.6 m) above the river, 35 ft (10.7 m) wide, begun 1886, opened January 1, 1889 for
// rail; the railroad ended after the fire of May 8, 1974; reopened October 3, 2009 as the Walkway.
const WK = mkPath(P(-1035.1, -8.8, -241.7, -16.3, 142.1, -20.0, 821.3, -26.4, 845.4, -25.3, 867.9, -24.1, 891.3, -22.4, 913.7, -19.8, 935.9, -16.5, 957.7, -12.5, 981.4, -7.4, 1006.5, -0.9, 1032.5, 7.1, 1034.8, 7.7));

function walkwayBuild(b: MeshBuilder) {
  const Z = 212 * 0.3048;
  const hw = 5.35;
  deckStrip(b, WK, 0, WK.len, 20, () => Z, hw, 1.4, '#5E4B3E');
  // seven main spans of ~160 m (estimated equal spans) across the river, x = -560 .. +560 (estimated)
  const spanL = 160;
  const x0 = -560;
  const xs: number[] = [];
  for (let i = 0; i <= 7; i++) xs.push(x0 + spanL * i);
  const depth = (t: number) => 7 + 21 * (2 * t - 1) ** 2; // deepest over the piers (estimated)
  b.color('#6A5848');
  for (const off of [-hw + 0.4, hw - 0.4]) {
    const top: V2[] = [];
    const bot: number[] = [];
    for (let i = 0; i < 7; i++) {
      for (let k = 0; k < 10; k++) {
        const x = xs[i] + (spanL * k) / 10;
        const q = ptAt(WK, dAtX(WK, x));
        top.push(side(q, off));
        bot.push(Z - depth(k / 10));
      }
    }
    const q = ptAt(WK, dAtX(WK, xs[7]));
    top.push(side(q, off));
    bot.push(Z - 7);
    b.wallProfile(top, bot, Z);
    // diagonals every panel
    for (let i = 0; i < top.length - 1; i += 1) {
      b.beam(i % 2 === 0 ? [top[i][0], top[i][1], bot[i]] : [top[i][0], top[i][1], Z], i % 2 === 0 ? [top[i + 1][0], top[i + 1][1], Z] : [top[i + 1][0], top[i + 1][1], bot[i + 1]], 0.45);
    }
  }
  // river piers (masonry) and approach trestle towers
  b.color('#8E8A80');
  for (const x of xs) {
    const q = ptAt(WK, dAtX(WK, x));
    b.frame(q.x, q.y, 0, bearingOf(q), () => b.box(0, 0, -8, 12, 5.5, Z - 8 - 1.5));
  }
  b.color('#5E5A55');
  for (let x = x0 - 40; x > -1035; x -= 40) {
    const q = ptAt(WK, dAtX(WK, x));
    b.frame(q.x, q.y, 0, bearingOf(q), () => {
      for (const s of [-1, 1]) b.beam([s * 4.5, 0, -2], [s * 3, 0, Z - 1.4], 0.9);
    });
  }
  for (let x = xs[7] + 40; x < 1000; x += 40) {
    const q = ptAt(WK, dAtX(WK, x));
    b.frame(q.x, q.y, 0, bearingOf(q), () => {
      for (const s of [-1, 1]) b.beam([s * 4.5, 0, -2], [s * 3, 0, Z - 1.4], 0.9);
    });
  }
}

addLM({
  id: 'poughkeepsie_railroad_bridge',
  name: 'Poughkeepsie Railroad Bridge (Walkway Over the Hudson)',
  kind: 'bridge',
  built: [1886.0, 1889.0],
  end: 9999,
  anchor: [-73.94181, 41.71075],
  build: walkwayBuild,
  facts: {
    Construction: 'begun in 1886 (Union Bridge Company), opened for rail on January 1, 1889; the rail line ended after the fire of May 8, 1974; reopened as a pedestrian walkway on October 3, 2009',
    Dimensions: 'cantilever deck truss, 6,768 ft (2,063 m) long with approaches, 7 main spans (two of 548 ft), deck 212 ft (64.6 m) above the river, 35 ft (10.7 m) wide',
    Model: 'deck line from the OpenStreetMap way 24185107 (2,070 m); the positions of the seven main spans (equal 160 m spans, x = -560 to +560), truss depths (7 to 28 m), pier sizes and the approach trestle are estimated (only the total length, deck height, width and the two 548 ft spans are cited)'
  },
  sources: [WIKI + 'Walkway_over_the_Hudson', OSM + 'way/24185107']
});

// ====================================================================== Newburgh-Beacon Bridge (1960-1963; 1977-1980)
// Wikipedia: twin continuous-truss spans carrying I-84; main span 1,000 ft (305 m), 7,789 ft / 7,855 ft long, 135 ft
// (41 m) clear; the northern (westbound) span opened November 2, 1963, the southern (eastbound) span November 1, 1980.
// Axis: centre of the two bridge-flagged roadways' ends (-74.01047, 41.52103) to (-73.98193, 41.51825), 97.4°,
// 2,388 m; the main span is centred 159 m east of the midpoint (the article's coordinates, -73.99429 41.51925).
const NB_AX = axisOf([-74.01047, 41.52103], [-73.98193, 41.51825]);

function nbBuild(off: number) {
  return (b: MeshBuilder) =>
    b.frame(0, 0, 0, NB_AX.bearing, () => {
      const H = NB_AX.half;
      const C = 159; // main span centre (along-axis)
      const hw = 7.4;
      const zk: [number, number][] = [[-H, 38], [-600, 44], [C - 152.4, 43.6], [C, 42.4], [C + 152.4, 43.6], [700, 30], [H, 13]];
      const deckZ = (y: number) => {
        if (y <= zk[0][0]) return zk[0][1];
        for (let i = 0; i < zk.length - 1; i++) if (y <= zk[i + 1][0]) return zk[i][1] + ((zk[i + 1][1] - zk[i][1]) * (y - zk[i][0])) / (zk[i + 1][0] - zk[i][0]);
        return zk[zk.length - 1][1];
      };
      const truss = (y: number) => {
        const t = (y - (C - 152.4)) / 304.8;
        return t >= 0 && t <= 1 ? 8 + 16 * (2 * t - 1) ** 2 : 8;
      };
      const N = 60;
      const ys: number[] = [];
      for (let i = 0; i <= N; i++) ys.push(-H + (2 * H * i) / N);
      for (const [a, c] of ys.slice(0, -1).map((y, i) => [y, ys[i + 1]])) {
        const za = deckZ(a);
        const zc = deckZ(c);
        b.color('#55524E').quad([off - hw, a, za], [off + hw, a, za], [off + hw, c, zc], [off - hw, c, zc]);
        b.color('#6F7479');
        for (const x of [off - hw, off + hw]) {
          // through truss: lower chord at the deck, top chord above it (deeper over the channel piers)
          b.quad([x, a, za - 1.5], [x, c, zc - 1.5], [x, c, zc + truss((a + c) / 2)], [x, a, za + truss((a + c) / 2)]);
        }
        b.quad([off - hw, a, za - 1.5], [off + hw, a, za - 1.5], [off + hw, c, zc - 1.5], [off - hw, c, zc - 1.5]);
      }
      // top bracing and diagonals over the main span, piers every ~76 m
      b.color('#6F7479');
      for (let y = C - 152.4; y < C + 152.4; y += 19) {
        for (const x of [off - hw, off + hw]) b.beam([x, y, deckZ(y)], [x, y + 19, deckZ(y + 19) + truss(y + 19)], 0.5);
        b.beam([off - hw, y, deckZ(y) + truss(y)], [off + hw, y, deckZ(y) + truss(y)], 0.5);
      }
      b.color('#9A968E');
      const piersAt = [C - 152.4, C + 152.4];
      for (let y = C - 152.4 - 76; y > -H + 20; y -= 76) piersAt.push(y);
      for (let y = C + 152.4 + 76; y < H - 20; y += 76) piersAt.push(y);
      for (const y of piersAt) b.box(off, y, -8, 11, 4.2, deckZ(y) - 1.6 + 8);
      b.color('#8C887E');
      for (const s of [-1, 1]) b.box(off, s * (H + 6), -10, 2 * hw + 4, 12, deckZ(s * H) + 10);
    });
}

addLM({
  id: 'newburgh_beacon_bridge_1963',
  name: 'Newburgh-Beacon Bridge, northern (westbound) span',
  kind: 'bridge',
  built: [1960.0, 1963.84],
  end: 9999,
  anchor: NB_AX.anchor,
  build: nbBuild(21),
  facts: {
    Construction: 'the westbound span opened on November 2, 1963 (designed by Modjeski & Masters, built by Frederick Snare, Drave and Bethlehem Steel)',
    Dimensions: 'continuous truss, main span 1,000 ft (305 m), 7,855 ft long, 135 ft (41 m) clear above the Hudson',
    Model: 'axis from the ends of the two bridge-flagged roadways (97.4°, 2,388 m against the cited 2,374-2,394 m); deck heights along the bridge (13 to 44 m), truss depths (8 to 24 m), the pier spacing (76 m) and the 42 m spacing of the two spans are estimated; construction start 1960.0 is estimated'
  },
  sources: [WIKI + 'Newburgh–Beacon_Bridge', OVT]
});

addLM({
  id: 'newburgh_beacon_bridge_1980',
  name: 'Newburgh-Beacon Bridge, southern (eastbound) span',
  kind: 'bridge',
  built: [1977.0, 1980.84],
  end: 9999,
  anchor: NB_AX.anchor,
  build: nbBuild(-21),
  facts: {
    Construction: 'the eastbound span opened on November 1, 1980, after planning for added capacity began in 1972',
    Dimensions: 'continuous truss, main span 1,000 ft (305 m), 7,789 ft long, 135 ft (41 m) clear above the Hudson',
    Model: 'a twin of the 1963 span 42 m to its south (estimated spacing); same estimates; construction start 1977.0 is estimated'
  },
  sources: [WIKI + 'Newburgh–Beacon_Bridge', OVT]
});
