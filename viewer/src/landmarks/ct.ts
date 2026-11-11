/**
 * South-west Connecticut landmarks: New Haven (Yale, the Green, Union Station, the Knights of
 * Columbus tower), Bridgeport, Norwalk and New Canaan. Research and numeric checks:
 * data/research/landmarks_ct.md.
 *
 * Conventions as nyc-civic.ts: the anchor is the centre of the Overture Maps footprint the model
 * replaces (the footprint's own lon/lat), plans are that footprint in anchor-local metres
 * (x east, y north), `b.frame(ox, oy, 0, bearing)` puts the model's +y on a compass bearing.
 * Heights are cited figures where one was read, otherwise named as estimates in the facts.
 * Footprints: Overture Maps buildings 2026-10-21.0 (ODbL-compatible; OpenStreetMap + Microsoft ML).
 */
import {MeshBuilder, circle, rect, type V2} from './kit';
import type {Landmark} from './types';

const WIKI = 'https://en.wikipedia.org/wiki/';
const OVERTURE = 'https://docs.overturemaps.org/guides/buildings/';

// Overture building bfef1cb3-f600-40fa-ab11-028e963e9202
const R_conn_hall: V2[] = P(-13.6, -9.9, -1.9, -16.6, 13.6, 10.5, 2.1, 17.1);
// Overture building 0063d69c-2642-4a09-9c96-2ccb906023a8
const R_center: V2[] = P(17.0, 3.2, -9.4, 17.7, -20.9, -3.0, 5.6, -17.6, 6.6, -16.1, 10.8, -18.2, 20.6, -0.5, 16.2, 1.9);
// Overture building 78c58b1f-5a4d-4c5a-b226-a7245cd3b078
const R_united: V2[] = P(-16.4, 1.7, -18.7, -2.6, 6.8, -16.4, 8.9, -12.4, 12.8, -14.5, 19.6, -2.1, 15.4, 0.2, 17.2, 3.5, -7.9, 17.1, -10.1, 13.1, -11.5, 13.9, -17.8, 2.4);
// Overture building e159be96-067f-4c80-8c2b-6153d51bffa9
const R_trinity: V2[] = P(19.2, -5.6, 22.8, 1.0, -11.8, 19.1, -22.3, -0.7, 12.8, -19.1, 15.9, -13.2, 18.2, -14.4, 22.1, -7.1);
// Overture building 709f04fc-19a2-41f9-be47-f3d3668f7141
const R_sterling: V2[] = P(-49.5, -21.6, -45.4, -14.2, 4.4, -41.6, -4.9, -58.3, 16.0, -69.8, 30.9, -43.1, 29.6, -42.4, 32.2, -37.8, 23.6, -33.1, 32.3, -17.4, 40.8, -22.1, 43.1, -17.9, 44.4, -18.7, 59.3, 8.2, 62.1, 6.7, 66.9, 15.2, 56.8, 20.7, 56.3, 19.8, 34.1, 32.0, 37.0, 37.3, -21.5, 69.5, -22.5, 67.7, -23.6, 68.3, -27.3, 61.9, -26.0, 61.2, -43.5, 29.9, -44.6, 30.5, -48.1, 24.3, -46.7, 23.5, -52.1, 13.9, -53.4, 14.6, -56.9, 8.3, -55.5, 7.6, -66.5, -12.2);
// Overture building 730f8e24-ba0d-4ae8-8b26-bb073af7b5d2
const R_beinecke: V2[] = P(-21.3, -11.2, 2.7, -24.2, 22.3, 11.6, -1.7, 24.5);
// Overture building c5b49d4e-65ac-4137-bb55-7cef8326e851
const R_payne: V2[] = P(-89.8, -75.0, -87.1, -79.1, -79.7, -74.3, -80.9, -72.4, -63.7, -61.3, -61.4, -64.9, -53.7, -59.9, -54.9, -58.2, -51.2, -55.8, -52.2, -54.3, -40.0, -46.5, -39.3, -47.5, -35.1, -44.7, -34.3, -46.0, -33.3, -45.4, -30.4, -49.7, 8.2, -24.8, 9.5, -26.7, 20.7, -19.4, 17.5, -14.5, 42.8, 1.8, 45.5, -2.2, 56.8, 5.1, 55.8, 6.6, 96.8, 33.1, 65.8, 79.2, 25.2, 52.5, 22.5, 56.4, -25.1, 26.5, -20.5, 19.4, -59.7, -5.9, -38.8, -37.9, -42.8, -40.5, -48.0, -32.6, -96.9, -64.1, -94.5, -67.8, -97.0, -69.4, -92.2, -76.6);
// Overture building a819bc51-b5b9-4d79-bbb4-e52a607d813e
const R_union: V2[] = P(-37.4, -31.3, -15.4, -45.4, 37.9, 29.4, 14.6, 45.6);
// Overture building f5e3e826-e093-40d3-ae74-913609134aca
const R_kofc: V2[] = P(-7.3, -18.1, -7.9, -17.1, 15.2, -10.8, 15.4, -12.7, 16.2, -14.5, 18.1, -15.9, 20.4, -16.2, 22.2, -15.7, 23.7, -14.6, 24.7, -13.0, 24.8, -11.4, 24.4, -9.2, 23.2, -7.7, 21.0, -6.6, 18.7, -6.6, 17.1, -7.6, 10.9, 15.7, 12.8, 15.8, 14.6, 17.3, 15.8, 19.4, 15.6, 22.2, 14.0, 24.3, 11.6, 25.2, 9.2, 24.9, 7.3, 23.5, 6.3, 21.5, 6.2, 19.5, 7.3, 17.8, -15.9, 10.9, -16.0, 12.5, -16.5, 13.9, -18.7, 15.6, -20.9, 16.0, -22.8, 15.3, -24.3, 14.4, -25.4, 12.9, -25.4, 10.4, -24.2, 8.0, -22.4, 7.0, -19.4, 6.5, -17.5, 7.3, -11.1, -15.7, -14.4, -16.1, -16.1, -18.1, -16.6, -20.4, -16.2, -22.3, -14.9, -24.3, -12.1, -25.2, -9.2, -24.5, -7.3, -22.5, -6.8, -20.0);
// Overture building f664901d-1d61-4e3b-9a68-381877f74908
const R_bowl: V2[] = P(-85.4, 112.4, -84.4, 109.5, -90.2, 104.7, -92.6, 106.5, -107.1, 90.5, -105.7, 87.7, -109.6, 82.1, -112.3, 83.2, -121.6, 63.5, -119.2, 61.3, -121.2, 54.7, -124.4, 54.6, -127.3, 33.1, -124.0, 32.2, -124.1, 24.6, -127.0, 24.1, -124.5, 5.9, -121.1, 5.8, -119.4, -2.2, -121.9, -3.5, -117.8, -16.2, -114.7, -15.5, -112.2, -22.7, -114.5, -24.6, -108.4, -36.3, -105.1, -36.5, -101.2, -42.3, -103.9, -44.7, -97.3, -55.9, -94.1, -54.7, -90.7, -59.1, -95.3, -62.8, -82.6, -77.0, -79.1, -74.1, -75.9, -78.0, -77.9, -80.8, -68.6, -89.9, -65.4, -88.6, -60.5, -92.9, -61.7, -95.6, -51.2, -104.1, -48.7, -102.3, -42.8, -106.2, -43.3, -109.8, -32.8, -116.7, -30.3, -114.4, -23.9, -117.7, -24.0, -121.6, -7.5, -128.4, -4.6, -125.8, 1.4, -127.6, 2.6, -131.1, 23.6, -133.5, 24.7, -130.3, 31.0, -129.3, 32.7, -132.5, 53.8, -128.3, 54.1, -125.3, 60.2, -122.6, 62.9, -125.1, 81.8, -115.5, 80.9, -112.5, 86.5, -108.2, 89.0, -109.8, 104.7, -94.2, 103.1, -91.2, 106.6, -86.4, 110.7, -86.4, 120.6, -66.4, 118.4, -64.1, 119.6, -58.4, 123.5, -58.0, 127.5, -36.0, 124.2, -33.9, 124.2, -28.5, 127.5, -26.8, 125.7, -6.6, 121.6, -6.8, 119.6, -0.3, 122.9, 2.5, 118.9, 15.1, 115.5, 14.8, 113.0, 21.5, 115.8, 23.7, 107.1, 41.6, 99.6, 37.7, 88.7, 53.5, 86.6, 51.6, 70.6, 71.5, 73.3, 73.8, 69.4, 77.7, 74.3, 83.5, 49.9, 105.7, 47.9, 103.3, 41.3, 107.7, 42.0, 110.5, 30.0, 117.7, 28.3, 115.3, 21.4, 119.1, 22.1, 121.5, 4.2, 128.8, 2.9, 125.7, -4.4, 127.7, -4.7, 130.4, -27.1, 132.8, -27.3, 129.1, -34.6, 128.5, -36.5, 132.2, -58.4, 126.9, -57.8, 123.8, -64.9, 121.3, -66.6, 123.7);
// Overture building a3d062a4-b552-451e-a792-d7b1cbf6e23e
const R_barnum: V2[] = P(-11.7, -7.5, -10.8, -12.5, 7.9, -9.0, 8.5, -8.1, 9.6, -8.7, 11.0, -8.6, 12.2, -8.3, 13.1, -7.4, 13.4, -6.1, 13.0, -3.8, 11.3, -2.7, 9.7, -2.1, 7.3, 12.2, -0.6, 10.8, -0.5, 9.2, -4.0, 8.5, -5.3, 9.1, -8.5, 9.2, -10.7, 8.2, -12.1, 6.5, -13.0, 4.6, -13.1, 2.1, -12.8, 0.5, -10.5, -2.0, -9.7, -7.2);
// Overture building fc9de249-656e-4063-ae7f-709b373fda54
const R_lockwood: V2[] = P(14.8, -8.5, 14.9, -5.9, 15.5, -5.9, 15.6, -4.1, 18.2, -4.2, 18.2, -2.7, 18.8, -2.7, 20.3, -1.3, 20.3, 0.8, 18.9, 2.0, 18.3, 2.1, 18.4, 3.9, 15.9, 4.0, 16.0, 5.8, 15.1, 5.9, 15.2, 9.0, 15.6, 9.0, 15.7, 12.4, 20.0, 12.3, 20.1, 13.0, 21.1, 12.9, 22.5, 14.3, 22.5, 14.7, 23.1, 14.6, 23.1, 16.1, 22.5, 16.1, 22.5, 16.5, 21.2, 17.9, 20.1, 17.9, 20.1, 18.5, 14.9, 18.7, 14.9, 19.9, 7.0, 20.2, 6.7, 13.0, 5.2, 13.1, 5.2, 15.5, -3.0, 15.8, -3.1, 13.4, -4.7, 13.5, -4.5, 20.5, -12.4, 20.8, -12.7, 13.4, -13.6, 13.4, -13.6, 11.5, -14.1, 11.5, -15.3, 10.2, -15.4, 8.6, -14.0, 6.8, -14.5, 6.8, -14.5, 5.0, -17.9, 5.1, -17.9, 4.3, -23.1, 4.5, -23.4, -2.3, -18.0, -2.5, -18.0, -3.0, -14.9, -3.1, -15.0, -4.3, -15.9, -4.3, -16.0, -5.3, -17.4, -5.7, -18.2, -7.4, -17.5, -9.5, -16.1, -10.3, -16.1, -10.9, -14.5, -10.9, -14.5, -11.8, -13.5, -11.8, -13.6, -14.7, -6.7, -15.0, -6.5, -16.6, -5.6, -18.4, -4.2, -19.9, -2.1, -21.1, 0.7, -21.4, 1.9, -21.1, 3.7, -20.3, 5.7, -18.3, 6.5, -16.5, 6.7, -15.3, 11.5, -15.4, 12.4, -16.5, 15.8, -16.6, 18.3, -14.3, 18.4, -10.9, 16.4, -8.5);
// Overture building 609368a6-a596-4bb3-947d-6814ba6712a6
const R_glass: V2[] = P(4.7, -7.9, 3.9, 8.3, -5.6, 7.8, -4.8, -8.4);

/** Flat list of numbers -> ring. */
function P(...n: number[]): V2[] {
  const o: V2[] = [];
  for (let i = 0; i < n.length; i += 2) o.push([n[i], n[i + 1]]);
  return o;
}

/** Row of n round columns from (x0, y0) to (x1, y1). */
function columns(b: MeshBuilder, x0: number, y0: number, x1: number, y1: number, n: number, d: number, z0: number, z1: number, segs = 6) {
  for (let i = 0; i < n; i++) {
    const t = n === 1 ? 0.5 : i / (n - 1);
    b.cylinder(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, d / 2, z0, z1, segs);
  }
}

export const CT: Landmark[] = [];

// ====================================================================== Harkness Tower (1917-21)
// Cited: 216 ft (66 m), 284 steps, square base rising in stages to a double stone crown on an
// octagonal base with finials (Wikipedia). Plan and stage heights estimated from photographs.
// Anchor: on the High Street front of Branford College, from the Wikipedia coordinate
// (41.3093, -72.9294, four decimals) moved onto the college's footprint frontage.
function buildHarkness(b: MeshBuilder) {
  const stone = '#B3A58C';
  const dark = '#8E836F';
  b.frame(0, 0, 0, 29, () => {
    b.color(stone).box(0, 0, 0, 11.6, 11.6, 30, {top: false});
    // corner buttresses
    for (const sx of [-1, 1]) for (const sy of [-1, 1]) b.box(sx * 5.8, sy * 5.8, 0, 1.6, 1.6, 31.5);
    // second stage with four corner turrets
    b.color(stone).box(0, 0, 30, 9.6, 9.6, 14, {top: false});
    for (const sx of [-1, 1]) for (const sy of [-1, 1]) {
      b.box(sx * 4.9, sy * 4.9, 30, 2.2, 2.2, 22);
      b.color(dark).pyramid(rect(sx * 4.9, sy * 4.9, 2.4, 2.4), 52, [sx * 4.9, sy * 4.9, 56.5]);
      b.color(stone);
    }
    // belfry: octagon
    b.color(stone).cylinder(0, 0, 4.1, 44, 53, 8, {top: false});
    // double crown: tapered octagonal lantern then spire
    b.color(dark).loft([circle(0, 0, 4.4, 8), circle(0, 0, 3.4, 8)], [53, 56], {top: false});
    b.color(stone).cylinder(0, 0, 2.6, 56, 60, 8, {top: false});
    b.color(dark).pyramid(circle(0, 0, 3, 8), 60, [0, 0, 66]);
  });
}
CT.push({
  id: 'harkness_tower',
  name: 'Harkness Tower (Yale)',
  kind: 'tower',
  built: [1917.5, 1921.9],
  end: 9999,
  anchor: [-72.929515, 41.309354],
  build: buildHarkness,
  facts: {
    Built: '1917–1921 for the Memorial Quadrangle (James Gamble Rogers); named for Charles W. Harkness; part of Branford College since 1933',
    Height: '66 m (216 ft, one foot for each year since Yale’s founding); 284 steps',
    Model: 'height cited; square base 11.6 m, the stage heights, corner turrets and crown estimated from photographs; position estimated (about ±8 m) from the Wikipedia coordinate and the frontage of Branford College’s footprint'
  },
  sources: [WIKI + 'Harkness_Tower', OVERTURE]
});

// ====================================================================== Connecticut Hall (1750-52)
function gambrelHall(b: MeshBuilder, w: number, l: number, eave: number, mid: number, ridge: number) {
  b.color('#9C5A45').box(0, 0, 0, w, l, eave, {top: false});
  b.color('#5E5A55').loft([rect(0, 0, w + 0.6, l + 0.6), rect(0, 0, w * 0.6, l + 0.6), rect(0, 0, 0.3, l + 0.6)], [eave, mid, ridge]);
}
CT.push({
  id: 'connecticut_hall',
  name: 'Connecticut Hall (Yale)',
  kind: 'building',
  built: [1750.3, 1752.9],
  end: 9999,
  anchor: [-72.928852, 41.308174],
  build: b => {
    b.frame(0, 0.3, 0, 29.9, () => {
      gambrelHall(b, 13.4, 31.2, 8.4, 11.2, 13.0);
      b.color('#8A5A48');
      b.box(0, -8, 11, 1.2, 1.2, 3.4).box(0, 8, 11, 1.2, 1.2, 3.4);
      b.color('#E8E2D0').box(0, 0, 13, 2.2, 2.2, 1.4); // cupola base
    });
  },
  replaces: [R_conn_hall],
  facts: {
    Built: '1750–1752 (the oldest surviving Yale building; a dormitory, Georgian, brick)',
    Model: 'plan (31.2 x 13.4 m) from the footprint; eave 8.4 m after the footprint’s height of 8.8 m, gambrel roof levels, chimneys and cupola estimated; no published height read'
  },
  sources: [WIKI + 'Connecticut_Hall', OVERTURE]
});

// ====================================================================== the churches on the Green
// Walls follow the footprint; roof, portico and steeple are placed in a frame on the footprint's
// long axis (+y at the front). Which end is the front is taken from the street each church
// addresses (Center Church 311 and United Church 323 Temple Street face each other across it;
// Trinity, 243 Church Street, faces west): an inference, named in the facts.
const BRICK = '#B9654F';
const GREY = '#6A6560';
const WHITE = '#EDEAE0';

function steeple(b: MeshBuilder, cy: number, towerW: number, zBase: number, zOct: number, zLantern: number, zTop: number) {
  b.color(BRICK).box(0, cy, 0, towerW, towerW, zBase);
  b.color(WHITE).cylinder(0, cy, towerW * 0.4, zBase, zOct, 8).cylinder(0, cy, towerW * 0.29, zOct, zLantern, 8);
  b.color(GREY).dome(0, cy, towerW * 0.32, zLantern, 3, 8, 3);
  b.pyramid(circle(0, cy, 0.7, 8), zLantern + 3, [0, cy, zTop]);
}
function portico(b: MeshBuilder, y: number, w: number, zTop: number, n: number) {
  b.color(WHITE).box(0, y, 0, w, 3.6, 0.5);
  columns(b, -w / 2 + 0.8, y + 1, w / 2 - 0.8, y + 1, n, 0.9, 0.5, zTop - 0.6);
  b.box(0, y, zTop - 0.6, w + 0.4, 3.8, 0.6).gable(0, y, w + 0.4, 3.8, zTop, 2.6, true);
}

CT.push({
  id: 'center_church_new_haven',
  name: 'Center Church on the Green',
  kind: 'building',
  built: [1812.4, 1814.9],
  end: 9999,
  anchor: [-72.92659, 41.307898],
  build: b => {
    b.color(BRICK).prism(R_center, 0, 10.5);
    b.frame(0.2, -1.1, 0, 118.8, () => {
      b.color(GREY).gable(0, -0.5, 21.6, 29.6, 10.5, 5, true);
      portico(b, 16.6, 14, 10, 6);
      steeple(b, 11, 7.6, 24, 33, 38, 46);
    });
  },
  replaces: [R_center],
  facts: {
    Built: '1812–1814 by Ithiel Town with David Hoadley: Georgian / Federal, the Congregational church of the colony, above the crypt of the old burying ground',
    Model: 'plan from the footprint; every height (walls 10.5 m, ridge 15.5 m, steeple about 46 m), the portico, and the front side (toward Temple Street) estimated — no published dimension read'
  },
  sources: [WIKI + 'Center_Church_on_the_Green', OVERTURE]
});

CT.push({
  id: 'united_church_new_haven',
  name: 'United Church on the Green',
  kind: 'building',
  built: [1813.4, 1815.9],
  end: 9999,
  anchor: [-72.926048, 41.308653],
  build: b => {
    b.color(BRICK).prism(R_united, 0, 10);
    b.frame(0.7, -0.3, 0, 298.3, () => {
      b.color(GREY).gable(0, 0, 20.4, 29, 10, 4.8, true);
      portico(b, 16.2, 12, 9.6, 4);
      steeple(b, 11.6, 6.8, 20, 28, 33, 40);
    });
  },
  replaces: [R_united],
  facts: {
    Built: '1813–1815 (Asher Benjamin’s design after David Hoadley); the Congregational church was the “New Haven North”, today United Church',
    Model: 'plan from the footprint; heights (walls 10 m, ridge 14.8 m, steeple 40 m), the portico and the front side (toward Temple Street, west) estimated — no published dimension read'
  },
  sources: [WIKI + 'United_Church_on_the_Green', OVERTURE]
});

// Trinity Church (Ithiel Town, 1814-16): Gothic Revival, trap-rock walls. Cited (Wikipedia): nave
// 103 x 74 ft, walls 38 ft above the ground, tower 25 ft square and 100 ft high with corner
// pinnacles 30 ft above the tower roof, whole length 115.5 ft. In 1871 the wooden top of the tower
// was replaced with stone, a chancel was added in 1884 and a pyramid roof sat on the tower 1893-1930.
CT.push({
  id: 'trinity_church_new_haven',
  name: 'Trinity Church on the Green',
  kind: 'building',
  built: [1814.4, 1816.5],
  end: 9999,
  anchor: [-72.927296, 41.307035],
  build: b => {
    b.color('#8E6B55').prism(R_trinity, 0, 11.6);
    b.frame(1.6, -0.6, 0, 297.6, () => {
      // nave 31.4 x 22.6 m under a shallow roof; the tower at the front (+y)
      b.color(GREY).box(-0.0, -2.5, 11.6, 22.6, 31.4, 0.5);
      b.color('#8E6B55').box(0, 15.4, 0, 7.6, 7.6, 30.5);
      b.color(GREY).box(0, 15.4, 30.5, 8.0, 8.0, 0.5);
      for (const sx of [-1, 1]) for (const sy of [-1, 1]) {
        b.color('#8E6B55').box(sx * 3.4, 15.4 + sy * 3.4, 31, 1.2, 1.2, 9.1);
        b.color(GREY).pyramid(rect(sx * 3.4, 15.4 + sy * 3.4, 1.4, 1.4), 40.1, [sx * 3.4, 15.4 + sy * 3.4, 42.4]);
      }
    });
  },
  replaces: [R_trinity],
  facts: {
    Built: '1814–1816 by Ithiel Town: the first Gothic Revival church of any size in the United States, of local trap rock',
    Later: 'tower top rebuilt in stone 1871; chancel 1884; pyramid roof on the tower 1893–1930; exit wings 1961–62 (the footprint extrusion shows the chancel from 1816)',
    Model: 'walls 11.6 m (38 ft), nave 31.4 x 22.6 m, tower 7.6 m square and 30.5 m (100 ft) high with pinnacles 9.1 m (30 ft) above, all cited; plan from the footprint; the front side (west, toward Church Street) and the flat roof estimated'
  },
  sources: [WIKI + 'Trinity_Church_on_the_Green', OVERTURE]
});

// ====================================================================== Sterling Memorial Library (1927-31)
// Cited: 150 ft (45.7 m) tower, sixteen levels, 441,651 sq ft; Gothic Revival (James Gamble Rogers).
CT.push({
  id: 'sterling_memorial_library',
  name: 'Sterling Memorial Library (Yale)',
  kind: 'building',
  built: [1927.0, 1931.3],
  end: 9999,
  anchor: [-72.928749, 41.311228],
  build: b => {
    const lime = '#BDB5A3';
    b.color(lime).prism(R_sterling, 0, 20, {top: false});
    b.color('#6A6560').cap(R_sterling, 20);
    // the stacks tower; centre from the Wikipedia coordinate (41.3113, -72.9291), four decimals
    b.frame(-26, 9, 0, 29, () => {
      b.color(lime).box(0, 0, 20, 17, 11, 25.7);
      b.color('#9E968A').box(0, 0, 45.7, 17.6, 11.6, 0.5);
      for (const sx of [-1, 1]) for (const sy of [-1, 1]) {
        b.color(lime).box(sx * 8.2, sy * 5.2, 45.7, 1.4, 1.4, 3);
      }
    });
  },
  replaces: [R_sterling],
  facts: {
    Built: 'designed by James Gamble Rogers after Bertram Goodhue’s design; finished 1930, opened April 1931; twenty buildings were cleared for it',
    Height: 'tower 150 ft (45.7 m), 16 levels of stacks',
    Model: 'plan from the footprint; tower height cited; the nave height (20 m), tower plan and tower position (about ±8 m, from a four-decimal coordinate) estimated; no buttresses, windows or pinnacles'
  },
  sources: [WIKI + 'Sterling_Memorial_Library', OVERTURE]
});

// ====================================================================== Beinecke Library (1960-63)
CT.push({
  id: 'beinecke_library',
  name: 'Beinecke Rare Book & Manuscript Library (Yale)',
  kind: 'building',
  built: [1960.5, 1963.5],
  end: 9999,
  anchor: [-72.92733, 41.311596],
  build: b => {
    b.frame(0.5, 0.2, 0, 28.7, () => {
      b.color('#C9C2B4').box(0, 0, 0, 41, 27.3, 1.1);
      // windowless shell of Vermont marble, carried on four corner piers
      b.color('#D8D2C6').box(0, 0, 4.2, 40.6, 26.9, 8.8, {bottom: true});
      b.color('#9A948A');
      for (const sx of [-1, 1]) for (const sy of [-1, 1]) b.box(sx * 19.4, sy * 12.7, 1.1, 2.2, 2.2, 3.1);
      // glass book tower seen through the mezzanine
      b.color('#8FA7A3').box(0, 0, 1.1, 12, 7, 3.1);
    });
  },
  replaces: [R_beinecke],
  facts: {
    Built: '1960–1963 (Gordon Bunshaft, Skidmore, Owings & Merrill): a windowless marble-and-granite shell on four corner piers around a six-storey glass tower of book stacks',
    Model: 'plan (41 x 27.3 m) from the footprint; the height of the shell (13 m) and the pier and mezzanine proportions estimated — no published height read'
  },
  sources: [WIKI + 'Beinecke_Rare_Book_and_Manuscript_Library', OVERTURE]
});

// ====================================================================== Payne Whitney Gymnasium (1930-32)
// Cited: one of the largest athletic facilities ever built, a nine-storey tower, opened 1932
// (John Russell Pope). Heights are estimates.
CT.push({
  id: 'payne_whitney_gymnasium',
  name: 'Payne Whitney Gymnasium (Yale)',
  kind: 'building',
  built: [1930.0, 1932.5],
  end: 9999,
  anchor: [-72.931019, 41.313725],
  build: b => {
    const lime = '#BDB5A3';
    b.color(lime).prism(R_payne, 0, 17, {top: false});
    b.color('#6A6560').cap(R_payne, 17);
    // the nine-storey tower, centre from the Wikipedia coordinate (41°18'49"N 72°55'50"W)
    b.frame(38, -12, 0, 57, () => {
      b.color(lime).box(0, 0, 17, 15, 15, 33);
      b.color('#9E968A').box(0, 0, 50, 16, 16, 0.6);
      for (const sx of [-1, 1]) for (const sy of [-1, 1]) b.color(lime).box(sx * 7.2, sy * 7.2, 50, 1.6, 1.6, 2.8);
    });
  },
  replaces: [R_payne],
  facts: {
    Built: '1930–1932 (John Russell Pope): twelve acres of interior space and a nine-storey tower holding a third-floor pool, fencing and polo rooms',
    Model: 'plan from the footprint; heights (block 17 m, tower 50 m), tower plan and position (±8 m, from a coordinate rounded to the second) estimated — no published height read; LOW confidence'
  },
  sources: [WIKI + 'Payne_Whitney_Gymnasium', OVERTURE]
});

// ====================================================================== Yale Bowl (1913-14)
function scaled(ring: V2[], s: number): V2[] {
  let cx = 0;
  let cy = 0;
  for (const [x, y] of ring) {
    cx += x;
    cy += y;
  }
  cx /= ring.length;
  cy /= ring.length;
  return ring.map(([x, y]) => [cx + (x - cx) * s, cy + (y - cy) * s] as V2);
}
CT.push({
  id: 'yale_bowl',
  name: 'Yale Bowl',
  kind: 'stadium',
  built: [1913.6, 1914.9],
  end: 9999,
  anchor: [-72.960487, 41.313238],
  build: b => {
    b.color('#B7B2A4').loft([R_bowl, scaled(R_bowl, 0.96), scaled(R_bowl, 0.58)], [0, 11, 0.6], {top: false});
    b.color('#6F8F5A').cap(scaled(R_bowl, 0.58), 0.6);
  },
  replaces: [R_bowl],
  facts: {
    Opened: 'November 21, 1914 (first game, 68,000 spectators); the first bowl-shaped stadium in the country, a National Historic Landmark since 1987',
    Capacity: '61,446 today (Charles A. Ferry, class of 1871; fill from the excavated field built the berm)',
    Model: 'outer rim from the footprint (281 x 225 m); the rim height (11 m) and the inner slope estimated, and the field is drawn level with the ground (the real field lies below it; the terrain cannot be dug) — LOW confidence'
  },
  sources: [WIKI + 'Yale_Bowl', OVERTURE]
});

// ====================================================================== New Haven Union Station (1918-20)
CT.push({
  id: 'union_station_new_haven',
  name: 'New Haven Union Station',
  kind: 'building',
  built: [1918.0, 1920.0],
  end: 9999,
  anchor: [-72.926624, 41.297522],
  build: b => {
    const lime = '#CFC8B8';
    b.frame(0.4, -0.8, 0, 34, () => {
      b.color(lime).box(0, 0, 0, 28.4, 46, 15);
      b.color('#8D8678').box(0, 0, 15, 29, 46.6, 0.5);
      // the wings, lower
      for (const s of [-1, 1]) {
        b.color(lime).box(0, s * 34.5, 0, 28.4, 23, 10.5);
        b.color('#8D8678').box(0, s * 34.5, 10.5, 28.8, 23.4, 0.4);
      }
      // the great arched windows of the waiting hall, as dark panels on both long sides
      b.color('#5C6670');
      for (const sx of [-1, 1]) for (const k of [-1, 0, 1]) b.box(sx * 14.25, k * 11, 3, 0.4, 7, 9);
    });
  },
  replaces: [R_union],
  facts: {
    Built: 'designed by Cass Gilbert (architect also of the Woolworth Building), Beaux-Arts, opened 1920; the third station of the city, replacing that of 1879',
    Model: 'plan (92.8 x 28.4 m) from the footprint; the heights (hall block 15 m, wings 10.5 m, after the footprint’s 9 m) and the window panels estimated — no published height read'
  },
  sources: [WIKI + 'Union_Station_(New_Haven)', OVERTURE]
});

// ====================================================================== Knights of Columbus Building (1965-69)
// Cited: 23 floors, finished 1969 (Kevin Roche John Dinkeloo & Associates), four cylindrical corner
// towers; Overture's height 98 m.
CT.push({
  id: 'knights_of_columbus_tower',
  name: 'Knights of Columbus Building, New Haven',
  kind: 'tower',
  built: [1966.0, 1969.5],
  end: 9999,
  anchor: [-72.927578, 41.302778],
  build: b => {
    b.frame(-0.3, 0.1, 0, 74.3, () => {
      b.color('#A39484');
      for (const sx of [-1, 1]) for (const sy of [-1, 1]) b.cylinder(sx * 13.75, sy * 13.75, 7.6, 0, 98, 14);
      b.color('#7C8A91').box(0, 0, 0, 27.5, 27.5, 82);
      b.color('#A39484').box(0, 0, 82, 28, 28, 1.2);
    });
  },
  replaces: [R_kofc],
  facts: {
    Built: '1965–1969 (Kevin Roche John Dinkeloo and Associates): 23 floors, the Supreme Council headquarters of the Knights of Columbus, four granite-faced cylindrical towers',
    Height: '98 m (Overture Maps height for the footprint)',
    Model: 'footprint (42.7 m square, rotated 74°); tower radius 7.6 m, the glazed core’s plan and its height (82 m) estimated'
  },
  sources: [WIKI + 'Knights_of_Columbus_Building_(New_Haven,_Connecticut)', OVERTURE]
});

// ====================================================================== Barnum Museum, Bridgeport (1891-93)
CT.push({
  id: 'barnum_museum',
  name: 'Barnum Museum (Barnum Institute of Science and History)',
  kind: 'building',
  built: [1891.0, 1893.1],
  end: 9999,
  anchor: [-73.188152, 41.175673],
  build: b => {
    b.color('#B58A6B').prism(R_barnum, 0, 14, {top: false});
    b.color('#8E6A52').cap(R_barnum, 14);
    b.color('#D9B98A').prism(scaled(R_barnum, 1.0), 13.2, 14.6, {top: false});
  },
  replaces: [R_barnum],
  facts: {
    Built: 'opened February 18, 1893 (Longstaff & Hurd), funded by P. T. Barnum: a three-storey building of stone and terra cotta in Byzantine, Romanesque and Gothic forms, with a frieze by Henri Plasschaert',
    Model: 'plan from the footprint; the height (14 m for three storeys) and the cornice are estimated, and the roof, turret and frieze are not modelled — LOW confidence'
  },
  sources: [WIKI + 'Barnum_Museum', OVERTURE]
});

// ====================================================================== The Glass House, New Canaan (1949)
CT.push({
  id: 'glass_house_new_canaan',
  name: 'The Glass House (Philip Johnson)',
  kind: 'building',
  built: [1948.5, 1949.9],
  end: 9999,
  anchor: [-73.529259, 41.142397],
  build: b => {
    b.frame(-0.4, 0, 0, 177.1, () => {
      b.color('#6E6A64').box(0, 0, 0, 16.2, 9.6, 0.4);
      b.color('#2B2B2B').box(0, 0, 3.6, 16.4, 9.8, 0.35);
      b.color('#9DB8BF');
      b.walls(rect(0, 0, 16.0, 9.4), 0.4, 3.6);
      // steel corner and mullion posts
      b.color('#1E1E1E');
      for (const x of [-8, -4, 0, 4, 8]) for (const y of [-4.7, 4.7]) b.box(x, y, 0.4, 0.25, 0.25, 3.2);
      for (const y of [-1.6, 1.6]) for (const x of [-8, 8]) b.box(x, y, 0.4, 0.25, 0.25, 3.2);
      // the brick cylinder (bathroom and hearth) rises through the roof
      b.color('#7A3E2E').cylinder(1.6, 0.6, 1.5, 0.4, 4.4, 14);
    });
  },
  replaces: [R_glass],
  facts: {
    Built: '1949, Philip Johnson’s own house: a steel-framed glass pavilion on a brick platform, with a brick cylinder',
    Model: 'plan (16.2 x 9.6 m) from the footprint; roof at Overture’s 3.6 m, the cylinder’s position and height (4.4 m) and the post spacing estimated'
  },
  sources: [WIKI + 'Glass_House', OVERTURE]
});

// ====================================================================== Lockwood–Mathews Mansion, Norwalk (1864-68)
CT.push({
  id: 'lockwood_mathews_mansion',
  name: 'Lockwood–Mathews Mansion',
  kind: 'building',
  built: [1864.5, 1868.9],
  end: 9999,
  anchor: [-73.41716, 41.108879],
  build: b => {
    b.color('#8D7C68').prism(R_lockwood, 0, 12, {top: false});
    // Second Empire mansard roof
    b.color('#4F5358').loft([scaled(R_lockwood, 1.02), scaled(R_lockwood, 0.8)], [12, 17.5], {top: false});
    b.cap(scaled(R_lockwood, 0.8), 17.5);
    // the central rotunda lantern and dome
    b.color('#8D7C68').cylinder(0, 0, 5, 17.5, 21, 12, {top: false});
    b.color('#4F5358').dome(0, 0, 5.2, 21, 3.6, 12, 3);
  },
  replaces: [R_lockwood],
  facts: {
    Built: '1864–1868 for LeGrand Lockwood (Detlef Lienau): a 62-room Second Empire country house of 44,000 sq ft, a National Historic Landmark',
    Model: 'plan from the footprint; every height (walls 12 m, mansard to 17.5 m, lantern and dome to 24.6 m) estimated — no published height read; LOW confidence'
  },
  sources: [WIKI + 'Lockwood-Mathews_Mansion', OVERTURE]
});
