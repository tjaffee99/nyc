/**
 * New York landmarks: civic — monuments, civic buildings, churches, stations, museums and
 * stadiums that stand today and whose shape a flat footprint extrusion gets wrong.
 * Research: data/research/landmarks_civic.md, data/tables/landmarks_civic.csv.
 *
 * Conventions: the anchor is a point on the building; plans are the city's official
 * footprint (NYC Building Footprints) re-expressed in a model frame (`b.frame(ox, oy, 0,
 * bearing)`, +y pointing at `bearing`); heights are cited figures, the city's measured roof
 * height, or OpenStreetMap 3D parts; anything else is named as an estimate in the facts.
 */
import {MeshBuilder, circle, rect, parabola, type V2, type V3} from './kit';
import type {Landmark} from './types';

const WIKI = 'https://en.wikipedia.org/wiki/';
const LPC = (n: string) => `https://s-media.nyc.gov/agencies/lpc/lp/${n}.pdf`;
const FOOTPRINTS = 'https://data.cityofnewyork.us/d/5zhs-2jue';
const OSM = 'https://www.openstreetmap.org/';

/** Flat list of numbers -> ring. */
function P(...n: number[]): V2[] {
  const o: V2[] = [];
  for (let i = 0; i < n.length; i += 2) o.push([n[i], n[i + 1]]);
  return o;
}

/** Ring given in a model frame (origin ox, oy; +y at `bearing`) -> anchor-local metres. */
function place(ring: V2[], ox: number, oy: number, bearing: number): V2[] {
  const a = (-bearing * Math.PI) / 180;
  const c = Math.cos(a);
  const s = Math.sin(a);
  return ring.map(([x, y]) => [ox + c * x - s * y, oy + s * x + c * y] as V2);
}

/** Row of n round columns from (x0, y0) to (x1, y1). */
function columns(b: MeshBuilder, x0: number, y0: number, x1: number, y1: number, n: number, d: number, z0: number, z1: number, segs = 6) {
  for (let i = 0; i < n; i++) {
    const t = n === 1 ? 0.5 : i / (n - 1);
    b.cylinder(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, d / 2, z0, z1, segs);
  }
}

/** Polygonal spire: ring of radius r at z0 to an apex at z1. */
function spire(b: MeshBuilder, cx: number, cy: number, r: number, z0: number, z1: number, segs = 8) {
  b.pyramid(circle(cx, cy, r, segs), z0, [cx, cy, z1]);
}

/** Ellipse ring with `segs` vertices (for lofted figures). */
const oval = (cx: number, cy: number, rx: number, ry: number, segs = 10): V2[] => circle(cx, cy, 1, segs, rx, ry);

export const CIVIC: Landmark[] = [];

// ====================================================================== Statue of Liberty
// Anchor on the pedestal; the pedestal centre is (-2.5, 0.4) and its faces bear 146.7° /
// 56.7° (OSM 3D parts) — the statue faces 146.7° (south-east, down the harbour).
// Heights above the ground (NPS statistics): foundation top 19.81 m (65 ft), pedestal top
// 46.94 m (154 ft), torch 92.99 m (305 ft 1 in); the copper statue is 46.05 m (151 ft 1 in),
// heel to top of head 33.86 m, head 5.26 m chin to cranium and 3.05 m ear to ear, right arm
// 12.8 m long, waist 10.67 m, tablet 7.19 x 4.14 x 0.61 m, rays up to 2.74 m.
const FORT_WOOD = P(
  5.9, 46.2, 14.7, 32.6, 27.5, 34.7, 25.1, 19.1, 40.7, 16.7, 33.9, 3.6, 44.8, -12.1, 30.0, -18.5, 24.8, -42.7, -0.8, -37.2, -12.6, -48.1, -23.1,
  -31.8, -37.4, -34.0, -33.8, -19.1, -49.3, -15.3, -41.6, -3.2, -50.0, 10.2, -36.3, 19.0, -38.7, 32.7, -27.1, 30.7, -22.4, 34.0, -20.4, 45.2, -7.8,
  37.5
);

function buildLiberty(b: MeshBuilder) {
  const granite = '#CBBFAA';
  const copper = '#7DB3A0';
  // Fort Wood (1807–11): eleven-pointed star, terreplein at ~10 m (OSM part)
  b.color('#B7AE9E').prism(FORT_WOOD, 0, 10, {top: false});
  b.color('#8DA671').cap(FORT_WOOD, 10);
  b.frame(-2.5, 0.4, 0, 146.7, () => {
    const sq = (s: number) => rect(0, 0, s, s);
    // upper terrace (OSM part, 39.6 x 40.2 m, 10–14 m) and the visible top of the foundation
    b.color('#C2B8A6').box(0, 0, 10, 39.9, 39.9, 4);
    b.color('#BDB2A0').box(0, 0, 14, 25.4, 25.4, 5.81);
    // pedestal (R. M. Hunt): truncated pyramid 62 ft square at the base, 39.4 ft at the top, 89 ft high
    b.color(granite).box(0, 0, 19.81, 18.9, 18.9, 4.2);
    b.loft([sq(16.4), sq(14.6)], [24.01, 39], {top: false});
    b.color('#8B8375');
    for (const s of [-1, 1]) {
      b.box(0, s * 7.72, 31, 7.4, 0.5, 6.8, {top: false});
      b.box(s * 7.72, 0, 31, 0.5, 7.4, 6.8, {top: false});
    }
    b.color('#BFB39C').box(0, 0, 39, 16.2, 16.2, 1);
    b.color(granite).loft([sq(13.4), sq(12.0)], [40, 45.4], {top: false});
    b.color('#BFB39C').box(0, 0, 45.4, 13.2, 13.2, 1.54);
    // the statue, standing on the pedestal top (46.94 m), facing +y
    b.frame(0, 0, 46.94, 0, () => {
      b.color(copper);
      // robed body: hem, waist (10.67 m across), shoulders, neck
      b.loft(
        [oval(0, 0, 5.2, 4.3), oval(0, 0.1, 5.0, 4.0), oval(0, 0.2, 5.0, 3.8), oval(0, 0.2, 5.33, 3.6), oval(0, 0.1, 5.0, 3.3), oval(0, 0, 4.6, 2.8), oval(0, 0, 2.6, 2.0), oval(0, 0.2, 1.2, 1.25)],
        [0, 6, 12, 17.5, 22, 25.5, 27.4, 28.3],
        {top: false}
      );
      // head: chin 28.6 m, crown of the head 33.86 m
      b.loft([oval(0, 0.3, 1.2, 1.3), oval(0, 0.3, 1.52, 1.75), oval(0, 0.2, 1.52, 1.9), oval(0, 0, 1.15, 1.45)], [28.3, 30, 32, 33.3], {top: false});
      b.pyramid(oval(0, 0, 1.15, 1.45), 33.3, [0, 0, 33.86]);
      // diadem and its seven rays
      b.loft([oval(0, 0.1, 1.85, 2.15), oval(0, 0.1, 1.95, 2.25)], [31.6, 32.5], {top: false});
      for (let k = 0; k < 7; k++) {
        const a = ((20 + (k * 140) / 6) * Math.PI) / 180;
        const dir: V3 = [Math.cos(a), -0.12, Math.sin(a)];
        const at = (r: number): V3 => [dir[0] * r, 0.1 + dir[1] * r, 32.0 + dir[2] * r * 0.9];
        b.beam(at(1.7), at(1.7 + 2.74), 0.34);
      }
      // right arm raised with the torch (arm 12.8 m)
      b.beam([3.5, 0, 26.0], [4.4, 0.2, 32.4], 3.0);
      b.beam([4.4, 0.2, 32.0], [5.0, 0.4, 38.6], 2.1);
      b.beam([5.0, 0.4, 38.2], [5.1, 0.4, 41.6], 0.8);
      b.frustum(5.1, 0.4, 0.7, 1.6, 41.6, 42.3, 8, false);
      b.cylinder(5.1, 0.4, 1.9, 42.3, 42.8, 8);
      b.color('#E2B13C');
      b.loft([circle(5.1, 0.4, 1.2, 8), circle(5.1, 0.4, 1.45, 8), circle(5.2, 0.5, 0.9, 8)], [42.8, 44, 45.2], {top: false});
      b.pyramid(circle(5.2, 0.5, 0.9, 8), 45.2, [5.3, 0.6, 46.05]);
      // left arm cradling the tablet
      b.color(copper);
      b.beam([-3.8, 0.2, 25.6], [-4.9, 1.2, 20.8], 2.6);
      b.beam([-4.9, 1.2, 20.8], [-3.4, 3.0, 21.6], 2.0);
      b.frame(-3.7, 3.3, 18.8, -18, () => b.box(0, 0, 0, 4.14, 0.61, 7.19));
    });
  });
}

CIVIC.push({
  id: 'statue_of_liberty',
  name: 'Statue of Liberty',
  kind: 'monument',
  built: [1883.3, 1886.82],
  end: 9999,
  anchor: [-74.044502, 40.689249],
  build: buildLiberty,
  replaces: [FORT_WOOD],
  facts: {
    Dedicated: 'October 28, 1886 (pedestal begun 1883; the statue assembled on it in 1886)',
    Height: '93 m (305 ft 1 in) ground to torch; the copper statue 46.05 m (151 ft 1 in)',
    Pedestal: 'granite-faced concrete by Richard Morris Hunt, 27.1 m (89 ft) on a 19.8 m (65 ft) foundation, 62 ft square at its base and 39.4 ft at the top',
    Base: 'the eleven-pointed star of Fort Wood (1807–1811)',
    Sculptor: 'Frédéric Auguste Bartholdi; iron frame by Gustave Eiffel',
    Model: 'star from the city footprint, terrace levels from OpenStreetMap 3D parts; the taper of the pedestal between its cited base and top, and the pose of the figure (built to the NPS body dimensions), estimated from photographs'
  },
  sources: ['https://www.nps.gov/stli/learn/historyculture/statue-statistics.htm', WIKI + 'Statue_of_Liberty', FOOTPRINTS, OSM]
});

// ====================================================================== Ellis Island — Main Building
// Frame at the centre of the main building, +y at 44.6° (north-east, the rear); the front
// faces the ferry slip. Main block 118.4 x 50.6 m (footprint); the registry room on the second
// floor of the centre section is 200 x 100 ft with a 56 ft ceiling (Wikipedia). The city
// footprint merges every connected building of Island 1 into one polygon: the others
// (kitchen & laundry, baggage & dormitory, bakery & carpentry, powerhouse) are plain blocks.
const ELLIS_REST: {outer: V2[]; holes: V2[][]} = {
  outer: P(
    -152.7, -127.6, -152.8, -100.5, -168.2, -100.6, -168.2, -112.3, -171.5, -112.4, -171.5, -119.6, -159.7, -119.6, -159.6, -128.6, -194.5, -128.7,
    -194.5, -119.7, -183.9, -119.7, -183.9, -112.5, -186.3, -112.5, -186.3, -84.8, -183.9, -84.8, -183.9, -77.4, -194.6, -77.4, -194.6, -68.7, -159.8,
    -68.5, -159.8, -77.3, -171.5, -77.4, -171.5, -84.6, -168.2, -84.6, -168.2, -96.0, -152.7, -96.0, -152.7, -60.3, -154.0, -60.3, -155.2, -51.6, -149.7,
    -41.5, -138.2, -34.9, -138.3, -17.2, -149.2, -17.2, -149.3, 21.5, -139.4, 21.6, -139.4, 18.2, -137.2, 18.2, -138.3, 19.8, -137.3, 61.6, -138.3,
    61.6, -138.3, 75.7, -113.7, 75.8, -113.7, 62.0, -116.8, 62.0, -116.8, 33.8, -113.6, 33.8, -113.6, 20.0, -132.2, 19.9, -132.2, 15.7, -105.0, 16.1,
    -96.6, 21.1, -92.8, 29.5, -93.3, 38.3, -95.4, 38.3, -94.3, 99.7, -24.2, 99.3, -22.9, 83.9, -23.5, 54.9, -19.3, 55.0, -19.3, 41.5, -59.3, 41.5,
    -59.3, 36.3, -70.3, 36.3, -70.3, 1.9, -59.5, 1.9, -59.3, 25.0, -59.3, -3.0, -73.9, -3.0, -73.9, -16.7, -96.2, -16.8, -96.2, -12.8, -116.5, -12.8,
    -116.5, -16.8, -127.6, -16.8, -127.6, -7.3, -131.9, -7.3, -130.8, -43.7, -136.7, -43.7, -136.7, -42.3, -141.9, -44.0, -146.4, -48.2, -148.6, -54.4,
    -146.9, -54.4, -148.1, -69.2, -141.0, -69.1, -140.9, -127.6
  ),
  holes: [P(-89.6, 26.7, -96.8, 16.0, -75.5, 16.0, -75.4, 39.3, -88.8, 38.7), P(-101.3, 8.3, -101.3, 13.8, -105.8, 12.4, -132.1, 12.4, -132.2, 3.4, -129.5, 3.4, -129.5, 8.3)]
};
const ELLIS_FRAME: [number, number, number] = [14.7, 12.55, 44.6];

function buildEllis(b: MeshBuilder) {
  const brick = '#A65A44';
  const stone = '#DDD3BF';
  const roof = '#7B8A84';
  const copper = '#7FA596';
  b.frame(ELLIS_FRAME[0], ELLIS_FRAME[1], 0, ELLIS_FRAME[2], () => {
    // wings (two storeys in 1900, the third added in the early 1910s)
    for (const s of [-1, 1]) {
      b.color(brick).box(s * 44.85, 0, 0, 28.7, 50.6, 16.5, {top: false});
      b.color(stone).box(s * 44.85, 0, 16.5, 29.3, 51.2, 0.8);
      b.color(roof).hip(s * 44.85, 0, 28.7, 50.6, 17.3, 4);
    }
    // centre section around the registry room (61 x 30.5 m, 17 m ceiling)
    b.color(brick).box(0, 3.4, 0, 61, 43.6, 19.5, {top: false});
    b.color(stone).box(0, 3.4, 19.5, 61.6, 44.2, 0.8);
    b.color(roof).gable(0, 3.4, 61, 43.6, 20.3, 6.2, false);
    // three great arches front and rear
    b.color('#3F4B53');
    for (const x of [-11.5, 0, 11.5]) {
      b.box(x, -18.5, 3.5, 8.2, 0.6, 12.5, {top: false});
      b.box(x, 25.3, 9, 8.2, 0.6, 7, {top: false});
    }
    // four corner towers with copper cupolas
    for (const sx of [-1, 1])
      for (const sy of [-1, 1]) {
        const x = sx * 25.5;
        const y = sy < 0 ? -20.4 : 20.6;
        b.color(brick).box(x, y, 0, 9.4, 9.4, 24.5, {top: false});
        b.color(stone).box(x, y, 24.5, 10, 10, 0.8);
        b.color(brick).box(x, y, 25.3, 7.4, 7.4, 6.2, {top: false});
        b.color('#3F4B53');
        b.box(x, y, 26.4, 7.6, 3, 4, {top: false}).box(x, y, 26.4, 3, 7.6, 4, {top: false});
        b.color(stone).box(x, y, 31.5, 8.2, 8.2, 0.7);
        b.color(copper).dome(x, y, 3.9, 32.2, 4.3, 8, 4);
        b.cylinder(x, y, 0.9, 36.3, 38, 6);
        spire(b, x, y, 0.9, 38, 40.5, 6);
      }
    // railroad ticket office annex (1905–06) behind the centre section
    b.color(brick).box(0, 33.2, 0, 37, 15.4, 6.5);
    // the other Island 1 buildings, as plain blocks from the merged city footprint
    b.color('#A8614C').prism(ELLIS_REST.outer, 0, 12, {holes: ELLIS_REST.holes});
    b.box(-39.3, 33.4, 0, 40, 16.2, 12);
  });
}

CIVIC.push({
  id: 'ellis_island_main_building',
  name: 'Ellis Island — Main Building',
  kind: 'building',
  built: [1898.6, 1900.96],
  end: 9999,
  anchor: [-74.0397, 40.699],
  build: buildEllis,
  replaces: [
    place(rect(0, 7.7, 118.8, 67.6), ...ELLIS_FRAME),
    place(ELLIS_REST.outer, ...ELLIS_FRAME),
    place(rect(-65, 19, 13, 37), ...ELLIS_FRAME)
  ],
  facts: {
    Opened: 'December 17, 1900 (Boring & Tilton), replacing the wooden station of 1892 that burned on June 15, 1897',
    Plan: '118 x 51 m; registry room 200 x 100 ft with a 56 ft ceiling',
    Processed: 'about 12 million immigrants, 1892–1954; museum since 1990',
    Model: 'plan from the city footprint, roof ridge at the city-measured 26.5 m; storey and tower heights (about 40 m to the finials) estimated from photographs; the adjoining buildings of Island 1 (1901–1909) are plain 12 m blocks'
  },
  sources: [WIKI + 'Ellis_Island', 'https://www.nps.gov/elis/learn/historyculture/index.htm', FOOTPRINTS]
});

// ====================================================================== Grand Central Terminal
// Frame at the footprint centroid, +y at 29.1° (north, up Park Avenue); the 42nd Street
// front is the -y side. Main Concourse 275 x 120 x 125 ft; the building "about 125 ft
// tall"; clock 13 ft; Glory of Commerce group 48 ft (Wikipedia). City-measured top 45.8 m.
const GCT_ANCHOR: V2 = [-73.97725, 40.7527];
const GCT_RING = P(45.7, 42.8, 45.4, -23.5, 43.1, -23.5, 43.0, -43.8, -42.7, -43.7, -42.6, -23.7, -45.7, -23.7, -45.5, 42.9);

function buildGrandCentral(b: MeshBuilder) {
  const stone = '#D9D2C0';
  const glass = '#48565E';
  b.frame(1.2, 3.3, 0, 29.1, () => {
    b.color(stone).prism(GCT_RING, 0, 27);
    // 42nd Street front: three 60 x 30 ft arched windows between ten Doric columns, entablature
    b.color(glass);
    for (const x of [-17, 0, 17]) b.box(x, -43.9, 9, 9.1, 0.6, 18.3, {top: false});
    b.color('#E3DDCC');
    for (const x of [-25.5, -8.5, 8.5, 25.5]) columns(b, x - 1.4, -44.7, x + 1.4, -44.7, 2, 1.7, 9, 27);
    columns(b, -29.6, -44.7, 29.6, -44.7, 2, 1.7, 9, 27);
    b.box(0, -44, 27, 62, 3.4, 3.5);
    // side elevations: the great end windows of the concourse
    b.color(glass);
    for (const s of [-1, 1]) for (const y of [-14, -4, 6]) b.box(s * 45.6, y, 9, 0.6, 7.5, 16, {top: false});
    // clock (13 ft) and the Glory of Commerce group above it
    b.color('#E3DDCC').box(0, -43.6, 30.5, 20, 2.6, 3.5);
    b.color('#2F3A40').box(0, -45, 30.3, 3.96, 0.3, 3.96);
    b.color('#CFC8B6').loft([rect(0, -43.4, 14.6, 3), rect(0, -43.4, 7, 2.4), rect(0, -43.4, 2.2, 1.6)], [34, 39, 43.5], {top: false});
    b.box(0, -43.4, 43.5, 1.2, 1, 2.3);
    // Main Concourse: 83.8 x 36.6 m hall, copper roof ridge at 38.1 m (125 ft)
    b.color(stone).box(0, -4, 27, 83.8, 36.6, 5, {top: false});
    b.color(glass);
    for (const x of [-30, -15, 0, 15, 30]) for (const s of [-1, 1]) b.box(x, -4 + s * 18.3, 27.6, 9, 0.5, 3.8, {top: false});
    b.color('#7FA596').gable(0, -4, 84.8, 37.6, 32, 6.1, false);
  });
}

CIVIC.push({
  id: 'grand_central_terminal',
  name: 'Grand Central Terminal',
  kind: 'building',
  built: [1903.6, 1913.09],
  end: 9999,
  anchor: GCT_ANCHOR,
  build: buildGrandCentral,
  replaces: [place(GCT_RING, 1.2, 3.3, 29.1)],
  facts: {
    Opened: 'February 2, 1913 (construction 1903–1913, built in stages around the working station)',
    Architects: 'Reed & Stem; Warren & Wetmore',
    'Main Concourse': '275 x 120 ft, 125 ft high (84 x 37 x 38 m)',
    'South front': 'three 60 by 30 ft arched windows between ten Doric columns; 13 ft clock under the 48 ft Glory of Commerce group (Jules-Félix Coutan, 1914)',
    Predecessors: 'Grand Central Depot (1871), rebuilt as Grand Central Station (1900)',
    Model: 'plan from the city footprint; concourse roof ridge at the cited 125 ft, top of the sculpture at the city-measured 45.8 m; the 27 m cornice and the window levels estimated from photographs'
  },
  sources: [WIKI + 'Grand_Central_Terminal', LPC('0266'), FOOTPRINTS]
});

// ---------------------------------------------------------------------- Park Avenue Viaduct
// Road centrelines from OpenStreetMap (via Overture), in metres around the terminal anchor.
// Wikipedia: 600 ft from 40th to 42nd Street, deck 60 ft wide; western leg 35 ft, eastern
// leg 33 ft, the roadway across the 42nd Street front 40 ft. Deck level ~8 m: estimated.
const VIADUCT_Z = 8;
function viaductRun(b: MeshBuilder, pts: V2[], w: number, solid: boolean) {
  for (let i = 0; i < pts.length - 1; i++) {
    const p = pts[i];
    const q = pts[i + 1];
    const L = Math.hypot(q[0] - p[0], q[1] - p[1]);
    const n: V2 = [(-(q[1] - p[1]) / L) * (w / 2 - 0.2), ((q[0] - p[0]) / L) * (w / 2 - 0.2)];
    if (solid) b.color('#CFC8B8').beam([p[0], p[1], (VIADUCT_Z - 1) / 2], [q[0], q[1], (VIADUCT_Z - 1) / 2], w - 0.8, VIADUCT_Z - 1);
    b.color('#8C8980').beam([p[0], p[1], VIADUCT_Z - 0.5], [q[0], q[1], VIADUCT_Z - 0.5], w, 1);
    b.color('#D6D0C0');
    for (const s of [-1, 1]) b.beam([p[0] + s * n[0], p[1] + s * n[1], VIADUCT_Z + 0.5], [q[0] + s * n[0], q[1] + s * n[1], VIADUCT_Z + 0.5], 0.4, 1);
    if (i > 0) b.color('#8C8980').cylinder(p[0], p[1], w / 2, VIADUCT_Z - 1, VIADUCT_Z, 10);
  }
}

function buildViaduct1919(b: MeshBuilder) {
  const S0: V2 = [-109.1, -194.7];
  const S1: V2 = [-84.5, -150.9];
  const S2: V2 = [-31.4, -55.8];
  // granite approach ramp from 40th Street
  b.color('#CFC8B8').beam([S0[0], S0[1], 3.2], [S1[0], S1[1], 3.5], 17.5, 7);
  b.color('#8C8980').beam([S0[0], S0[1], 6.6], [S1[0], S1[1], VIADUCT_Z - 0.5], 18.3, 1);
  // Pershing Square Viaduct: three steel-arch spans on granite piers, 60 ft deck
  const at = (t: number): V2 => [S1[0] + (S2[0] - S1[0]) * t, S1[1] + (S2[1] - S1[1]) * t];
  const L = Math.hypot(S2[0] - S1[0], S2[1] - S1[1]);
  const nx = -(S2[1] - S1[1]) / L;
  const ny = (S2[0] - S1[0]) / L;
  b.color('#8C8980').beam([S1[0], S1[1], VIADUCT_Z - 0.5], [S2[0], S2[1], VIADUCT_Z - 0.5], 18.3, 1);
  for (let k = 0; k <= 3; k++) {
    const c = at(k / 3);
    b.color('#CFC8B8').beam([c[0] - nx * 9, c[1] - ny * 9, 3.5], [c[0] + nx * 9, c[1] + ny * 9, 3.5], 3, 7);
    if (k === 3) break;
    const d = at((k + 1) / 3);
    b.color('#4F6B5B');
    for (const s of [-8.4, 0, 8.4]) {
      const arch = parabola([c[0] + nx * s, c[1] + ny * s, 2.2], [d[0] + nx * s, d[1] + ny * s, 2.2], 6.6, 10);
      b.polyline(arch, 0.9);
    }
    b.color('#D6D0C0');
    for (const s of [-9, 9]) b.beam([c[0] + nx * s, c[1] + ny * s, VIADUCT_Z + 0.5], [d[0] + nx * s, d[1] + ny * s, VIADUCT_Z + 0.5], 0.4, 1);
  }
  // roadway across the 42nd Street front (40 ft) and the western leg (35 ft); the solid
  // base carries the sidewalks to the building wall
  viaductRun(b, [S2, [-24.3, -48.5], [-18.9, -46.8], [-14.8, -48.0], [11.9, -62.5], [17.5, -63.5], [24.0, -61.9]], 15, true);
  viaductRun(b, [S2, [-29.2, -45.1], [-33.2, -38.7], [-53.7, -27.6], [-60.9, -22.8], [-65.3, -17.8], [-66.7, -11.4], [-64.7, -3.2], [-21.5, 73.9], [37.0, 179.1]], 14, true);
}

function buildViaduct1928(b: MeshBuilder) {
  viaductRun(b, [[24.0, -61.9], [29.4, -56.2], [72.3, 21.3], [106.9, 84.3], [118.0, 104.6], [122.0, 115.3], [122.6, 122.8], [121.0, 139.3]], 14, true);
}

const VIADUCT_SOURCES = [WIKI + 'Park_Avenue_Viaduct', LPC('1127'), OSM];
CIVIC.push(
  {
    id: 'park_avenue_viaduct',
    name: 'Park Avenue Viaduct (Pershing Square Viaduct and western leg)',
    kind: 'building',
    built: [1917.5, 1919.3],
    end: 9999,
    anchor: GCT_ANCHOR,
    build: buildViaduct1919,
    // the restaurant building under the Pershing Square spans (its own city footprint)
    replaces: [place(rect(0, 0, 16, 36), -57.3, -102.8, 29.2)],
    facts: {
      Opened: 'April 1919: 40th Street to 42nd Street and around the west side of the terminal',
      Form: 'granite approach, three steel-arch spans over Pershing Square and 42nd Street, a roadway at second-storey level around Grand Central',
      Dimensions: '600 ft from 40th to 42nd Street; deck 60 ft wide; western leg 35 ft; 40 ft across the 42nd Street front',
      Model: 'alignment from OpenStreetMap road centrelines; deck level (8 m) and span lengths estimated'
    },
    sources: VIADUCT_SOURCES
  },
  {
    id: 'park_avenue_viaduct_east',
    name: 'Park Avenue Viaduct (eastern leg)',
    kind: 'building',
    built: [1927.0, 1928.7],
    end: 9999,
    anchor: GCT_ANCHOR,
    build: buildViaduct1928,
    facts: {
      Opened: '1928: the eastern leg along Depew Place, making the viaduct a one-way loop',
      Dimensions: '33 ft wide between 42nd and 44th Streets',
      Model: 'alignment from OpenStreetMap road centrelines; deck level (8 m) estimated'
    },
    sources: VIADUCT_SOURCES
  }
);

// ====================================================================== New York Public Library
// Frame at the footprint centroid, +y at 299.1° (west, Bryant Park); Fifth Avenue is -y.
// 390 ft on its north–south axis by 270 ft; Main Reading Room 78 x 297 ft, 52 ft high;
// courts 80 x 80 ft; six 11 ft attic figures (Wikipedia). Roof levels from OSM 3D parts.
const NYPL_RING = P(58.6, 41.5, 58.9, -40.1, 15.0, -40.1, 15.0, -46.3, -14.2, -46.3, -14.3, -39.8, -58.9, -39.8, -59.1, 41.5);

function buildNYPL(b: MeshBuilder) {
  const marble = '#E5E0D4';
  const roof = '#98A39C';
  b.frame(0.5, 0.1, 0, 299.1, () => {
    const body = rect(0, 0.75, 117.8, 81.5);
    const courts = [rect(-31, -2, 24.4, 24.4), rect(31, -2, 24.4, 24.4)];
    b.color(marble).prism(body, 0, 20, {top: false, holes: courts});
    b.color(roof).cap(body, 20, courts);
    b.loft([body, rect(0, 0.75, 111.8, 75.5)], [20, 22], {top: false});
    b.color('#B9B4A8');
    for (const c of courts) b.cap(c, 0.4);
    // rear range: seven floors of stacks under the Main Reading Room
    b.color(marble).box(0, 26.2, 0, 96.9, 30.6, 29, {top: false});
    b.color(roof).hip(0, 26.2, 97.9, 31.6, 29, 6);
    b.color('#56636A');
    for (let x = -42; x <= 42; x += 7) b.box(x, 41.6, 19, 3.2, 0.5, 8.5, {top: false});
    // central pavilion: Astor Hall to the McGraw Rotunda
    b.color(marble).box(0, -14.5, 0, 30.5, 51, 29, {top: false});
    b.color(roof).gable(0, -14.5, 31.3, 51, 29, 6, true);
    // Fifth Avenue portico: three arches behind six columns, attic with six 11 ft figures
    b.color(marble).box(0, -43.2, 0, 29.2, 6.3, 4);
    b.color('#56636A');
    for (const x of [-8.6, 0, 8.6]) b.box(x, -40.3, 4, 5.2, 0.6, 10.5, {top: false});
    b.color('#EEEAE0');
    columns(b, -13, -45.3, 13, -45.3, 6, 1.5, 4, 17);
    b.color(marble).box(0, -43.2, 17, 29.6, 6.6, 2.6).box(0, -42.6, 19.6, 28.6, 5, 5.4);
    b.color('#D6D0C2');
    for (const x of [-12, -7.2, -2.4, 2.4, 7.2, 12]) b.box(x, -45, 19.6, 1.1, 0.9, 3.35);
    // pedimented end pavilions on Fifth Avenue
    for (const s of [-1, 1]) {
      b.color(marble).box(s * 52.5, -39.6, 0, 13, 1.6, 20, {top: false});
      b.color('#EEEAE0');
      columns(b, s * 52.5 - 4.5, -40.7, s * 52.5 + 4.5, -40.7, 4, 1.2, 4, 17);
      b.color(marble).gable(s * 52.5, -39.9, 13.6, 2.2, 20, 3.2, true);
    }
  });
}

CIVIC.push({
  id: 'new_york_public_library',
  name: 'New York Public Library — Stephen A. Schwarzman Building',
  kind: 'building',
  built: [1902.4, 1911.39],
  end: 9999,
  anchor: [-73.98225, 40.7532],
  build: buildNYPL,
  replaces: [place(NYPL_RING, 0.5, 0.1, 299.1)],
  facts: {
    Opened: 'May 23, 1911 (cornerstone November 1902), on the site of the Croton Distributing Reservoir (1842–1900)',
    Architects: 'Carrère and Hastings',
    Plan: '390 x 270 ft (119 x 82 m); two 80 ft courts',
    'Main Reading Room': '78 x 297 ft, 52 ft high, above seven floors of stacks',
    Model: 'plan from the city footprint; roof levels (22 m, 35 m) from OpenStreetMap 3D parts; portico heights estimated from photographs'
  },
  sources: [WIKI + 'New_York_Public_Library_Main_Branch', LPC('0246'), FOOTPRINTS, OSM]
});

// ====================================================================== St. Patrick's Cathedral
// Frame at the footprint centroid, +y at 118.4° (east, the apse); Fifth Avenue is -y.
// 332 ft long (396.7 ft with the Lady Chapel), towers 32 ft wide with spires 329.5 ft
// (Wikipedia); roof ridge at the city-measured 42 m.
const STPAT_RING = P(
  -19.2, -51.9, -19.2, -8.9, -22.9, -8.9, -22.9, 22.0, -18.1, 22.0, -18.1, 42.8, -12.0, 42.8, -11.1, 44.0, -11.6, 45.2, -11.0, 48.2, -8.3, 50.1, -4.8, 49.5,
  -4.8, 62.1, -1.8, 64.9, 2.9, 64.8, 5.7, 62.0, 5.7, 49.4, 9.3, 49.8, 11.8, 47.9, 12.2, 44.5, 11.7, 44.1, 12.9, 42.5, 18.6, 42.5, 18.6, 21.3, 22.9, 21.3, 22.9,
  -9.2, 18.8, -9.2, 18.8, -52.0
);
const STPAT_RING_1879 = STPAT_RING.filter(p => p[1] < 55);
const STPAT_FRAME: [number, number, number] = [-16.6, 8.9, 118.4];

function buildStPatricks(spires: boolean, ladyChapel: boolean) {
  return (b: MeshBuilder) => {
    const marble = '#E8E5DC';
    const slate = '#7C8388';
    b.frame(STPAT_FRAME[0], STPAT_FRAME[1], 0, STPAT_FRAME[2], () => {
      // aisles, side chapels and ambulatory
      b.color(marble).prism(ladyChapel ? STPAT_RING : STPAT_RING_1879, 0, 15, {top: false});
      b.color(slate).cap(ladyChapel ? STPAT_RING : STPAT_RING_1879, 15);
      // nave and choir clerestory, transept
      b.color(marble).box(-0.2, 0.2, 15, 14.8, 84.6, 16, {top: false});
      b.color(slate).gable(-0.2, 0.2, 15.8, 84.6, 31, 11, true);
      b.color(marble).box(0, 6.3, 15, 45.8, 14.8, 16, {top: false});
      b.color(slate).gable(0, 6.3, 45.8, 15.8, 31, 11, false);
      const apse = P(-7.6, 42.5, -7.6, 46.5, -3.8, 49.8, 3.4, 49.8, 7.2, 46.5, 7.2, 42.5);
      b.color(marble).prism(apse, 15, 31, {top: false});
      b.color(slate).pyramid(apse, 31, [-0.2, 42.5, 42]);
      // buttress pinnacles along the aisles
      b.color(marble);
      for (let y = -38; y <= -12; y += 6.5)
        for (const s of [-1, 1]) {
          b.box(-0.2 + s * 18.6, y, 15, 1.1, 1.1, 3);
          spire(b, -0.2 + s * 18.6, y, 0.8, 18, 21.5, 4);
        }
      if (ladyChapel) {
        b.color(marble).box(0.45, 56.5, 15, 8.4, 13, 3, {top: false});
        b.color(slate).gable(0.45, 56.5, 9.2, 13, 18, 5, true);
      }
      // Fifth Avenue front: central gable with the rose window between the towers
      b.color(marble).box(-0.2, -47.3, 15, 18.6, 9.4, 21, {top: false});
      b.gable(-0.2, -47.3, 18.6, 9.4, 36, 11.5, true);
      b.color('#3D4A5C').box(-0.2, -52.15, 24, 7.9, 0.4, 7.9, {top: false});
      b.color('#5B4A36').box(-0.2, -52.2, 0, 8, 0.5, 12, {top: false});
      b.color(marble).gable(-0.2, -52.4, 10.5, 0.8, 12, 5, true);
      for (const s of [-1, 1]) {
        const x = -0.2 + s * 14.1;
        const y = -47.1;
        b.color(marble).box(x, y, 0, 9.75, 9.75, 44, {top: !spires});
        if (!spires) continue;
        for (const dx of [-1, 1])
          for (const dy of [-1, 1]) {
            b.box(x + dx * 4.2, y + dy * 4.2, 44, 1.3, 1.3, 6);
            spire(b, x + dx * 4.2, y + dy * 4.2, 0.9, 50, 56, 4);
          }
        b.loft([circle(x, y, 4.7, 8), circle(x, y, 4.2, 8)], [44, 62], {top: false});
        spire(b, x, y, 4.2, 62, 100.4, 8);
      }
    });
  };
}

const STPAT_SOURCES = [WIKI + "St._Patrick's_Cathedral_(Midtown_Manhattan)", LPC('0267'), FOOTPRINTS];
const STPAT_FACTS = {
  Built: 'cornerstone August 15, 1858; dedicated May 25, 1879; spires 1885–1888; Lady Chapel 1901–1906',
  Architect: 'James Renwick Jr.',
  Dimensions: '332 ft long (396.7 ft with the Lady Chapel); towers 32 ft wide; spires 329.5 ft (100.4 m)',
  Model: 'plan from the city footprint; roof ridge at the city-measured 42 m; aisle, clerestory and tower-stage heights estimated from photographs'
};
CIVIC.push(
  {
    id: 'st_patricks_cathedral_1879',
    name: "St. Patrick's Cathedral (as dedicated in 1879, before the spires)",
    kind: 'building',
    built: [1858.62, 1879.4],
    end: 1888.8,
    anchor: [-73.976, 40.75845],
    build: buildStPatricks(false, false),
    facts: STPAT_FACTS,
    sources: STPAT_SOURCES
  },
  {
    id: 'st_patricks_cathedral_1888',
    name: "St. Patrick's Cathedral (with the spires of 1888, before the Lady Chapel)",
    kind: 'building',
    built: [1885.7, 1888.8],
    end: 1906.5,
    anchor: [-73.976, 40.75845],
    build: buildStPatricks(true, false),
    facts: STPAT_FACTS,
    sources: STPAT_SOURCES
  },
  {
    id: 'st_patricks_cathedral',
    name: "St. Patrick's Cathedral",
    kind: 'building',
    built: [1901.5, 1906.5],
    end: 9999,
    anchor: [-73.976, 40.75845],
    build: buildStPatricks(true, true),
    replaces: [place(STPAT_RING, ...STPAT_FRAME)],
    facts: STPAT_FACTS,
    sources: STPAT_SOURCES
  }
);

// ====================================================================== Trinity Church (third)
// Frame on the nave (OSM part centre), +y at 301.7° (west, the chancel); the tower stands
// on Broadway at -y. Spire and cross 281 ft (Wikipedia); nave 25 m and aisles from OSM parts.
const TRINITY_RING = P(
  15.6, 31.8, 15.6, 27.3, 19.5, 27.3, 19.5, 9.5, 12.9, 9.5, 12.9, -18.3, 17.6, -18.3, 17.6, -23.5, 6.6, -23.5, 6.6, -33.3, -5.3, -33.2, -5.3, -23.4, -15.0,
  -22.8, -15.1, -17.9, -10.8, -18.0, -10.8, 9.1, -14.9, 9.1, -14.9, 6.0, -24.3, 6.0, -24.4, 28.8, -14.9, 28.8, -14.9, 26.8, 7.1, 26.7, 7.1, 29.9, 12.7, 29.9,
  12.7, 34.3, 18.4, 34.3, 18.4, 31.8
);

function buildTrinity(b: MeshBuilder) {
  const stone = '#6E5644';
  const roof = '#4E5357';
  b.frame(-6.8, -8.6, 0, 301.7, () => {
    b.color(stone).prism(TRINITY_RING, 0, 8);
    b.box(1.05, 1.9, 8, 23.7, 49.6, 4, {top: false});
    b.color(roof).box(1.05, 1.9, 12, 23.7, 49.6, 0.3);
    b.color(stone).box(1.05, 1.9, 12, 13.7, 49.6, 9, {top: false});
    b.color(roof).gable(1.05, 1.9, 14.5, 49.6, 21, 4, true);
    b.color(stone);
    for (let y = -17; y <= 23; y += 5.7)
      for (const s of [-1, 1]) {
        b.box(1.05 + s * 11.9, y, 12, 1, 1, 2.5);
        spire(b, 1.05 + s * 11.9, y, 0.7, 14.5, 17, 4);
      }
    // All Saints' Chapel (1913)
    b.box(16.2, 18.4, 8, 6.6, 17.8, 5, {top: false});
    b.color(roof).gable(16.2, 18.4, 7, 17.8, 13, 4, true);
    // tower and spire
    const tx = 0.65;
    const ty = -28.4;
    b.color(stone).box(tx, ty, 0, 10.4, 9.8, 42, {top: false});
    b.color('#33383D');
    for (const s of [-1, 1]) b.box(tx, ty + s * 4.8, 29, 3, 0.5, 9, {top: false}).box(tx + s * 5.1, ty, 29, 0.5, 3, 9, {top: false});
    b.color(stone);
    for (const dx of [-1, 1])
      for (const dy of [-1, 1]) {
        b.box(tx + dx * 4.6, ty + dy * 4.3, 42, 1.4, 1.4, 5);
        spire(b, tx + dx * 4.6, ty + dy * 4.3, 1, 47, 53, 4);
      }
    b.loft([circle(tx, ty, 4.9, 8), circle(tx, ty, 4.4, 8)], [42, 47], {top: false});
    spire(b, tx, ty, 4.4, 47, 83.6, 8);
    b.color('#C9B037').box(tx, ty, 83.2, 0.3, 0.3, 2.4).box(tx, ty, 84.4, 1.3, 0.3, 0.3);
  });
}

CIVIC.push({
  id: 'trinity_church',
  name: 'Trinity Church (third building)',
  kind: 'building',
  built: [1839.5, 1846.39],
  end: 9999,
  anchor: [-74.0121, 40.7081],
  build: buildTrinity,
  replaces: [place(TRINITY_RING, -6.8, -8.6, 301.7)],
  facts: {
    Consecrated: 'May 21, 1846 (begun 1839) — the third Trinity Church on the site (1698–1776, 1790–1839)',
    Architect: 'Richard Upjohn',
    Spire: '281 ft (85.6 m) with its cross — the tallest structure in New York until 1890',
    Model: 'plan from the city footprint; nave (25 m) and aisles from OpenStreetMap 3D parts; the height at which the spire springs from the tower (42 m) estimated from photographs; All Saints’ Chapel (1913) and the later vestries are shown from 1846'
  },
  sources: [WIKI + 'Trinity_Church_(Manhattan)', LPC('0048'), FOOTPRINTS, OSM]
});

// ====================================================================== St. Paul's Chapel
// Frame on the body of the chapel (OSM part centre), +y at 302.9° (west, the tower);
// the portico faces Broadway at -y. No published height was verified: the steeple top is the
// city-measured 60.7 m, the body 15 m from the OSM part.
const STPAUL_RING = P(12.3, 18.0, 12.2, -22.0, -9.6, -21.9, -9.6, -16.8, -10.8, -16.8, -10.8, 18.1, -3.0, 18.0, -3.0, 20.3, 4.3, 20.2, 4.3, 18.0);

function buildStPauls(steeple: boolean) {
  return (b: MeshBuilder) => {
    const schist = '#8B7B68';
    const brown = '#7A5C48';
    b.frame(-0.9, 2.5, 0, 302.9, () => {
      b.color(schist).box(0.75, 0.6, 0, 23.1, 34.8, 11, {top: false});
      b.color('#5E5F60').gable(0.75, 0.6, 23.9, 34.8, 11, 4, true);
      // Broadway portico: four Ionic columns and a pediment
      b.color(brown).box(1.3, -19.4, 0, 21.8, 5.2, 0.8);
      b.color('#E6DFD0');
      columns(b, -7.6, -21.2, 10.2, -21.2, 4, 1.2, 0.8, 9.2);
      b.box(1.3, -19.4, 9.2, 21.8, 5.2, 1.2);
      b.gable(1.3, -19.4, 21.8, 5.2, 10.4, 3.4, true);
      // tower at the west end; the wooden steeple was added in 1794
      b.color(brown).box(0.65, 17, 0, 7.3, 6.6, steeple ? 24 : 16);
      if (!steeple) return;
      b.color('#E6DFD0').box(0.65, 17, 24, 6, 6, 6.5);
      b.loft([circle(0.65, 17, 3.0, 8), circle(0.65, 17, 2.8, 8)], [30.5, 38], {top: true});
      b.loft([circle(0.65, 17, 2.3, 8), circle(0.65, 17, 2.1, 8)], [38, 45], {top: true});
      b.color('#7D8A86');
      spire(b, 0.65, 17, 1.8, 45, 60.7, 8);
    });
  };
}

const STPAUL_SOURCES = [WIKI + "St._Paul's_Chapel", LPC('0075'), FOOTPRINTS, OSM];
const STPAUL_FACTS = {
  Built: '1764–1766 (opened October 30, 1766); steeple 1794 (James Crommelin Lawrence)',
  Note: 'the oldest surviving church building in Manhattan; George Washington worshipped here on his inauguration day, 1789',
  Model: 'plan from the city footprint; body 15 m from OpenStreetMap; steeple top at the city-measured 60.7 m (no published height verified); steeple stages estimated from photographs'
};
CIVIC.push(
  {
    id: 'st_pauls_chapel_1766',
    name: "St. Paul's Chapel (before the steeple)",
    kind: 'building',
    built: [1764.4, 1766.83],
    end: 1794.5,
    anchor: [-74.0092, 40.7113],
    build: buildStPauls(false),
    facts: STPAUL_FACTS,
    sources: STPAUL_SOURCES
  },
  {
    id: 'st_pauls_chapel',
    name: "St. Paul's Chapel",
    kind: 'building',
    built: [1793.5, 1794.5],
    end: 9999,
    anchor: [-74.0092, 40.7113],
    build: buildStPauls(true),
    replaces: [place(STPAUL_RING, -0.9, 2.5, 302.9)],
    facts: STPAUL_FACTS,
    sources: STPAUL_SOURCES
  }
);

// ====================================================================== Cathedral of St. John the Divine
// Frame at the footprint centroid, +y at 119.9° (east, the apse); the west front on
// Amsterdam Avenue is -y, +x is south. 601 ft long; narthex 50 x 207 ft; nave 248 x 146 ft,
// vault 124 ft, roof 177 ft; crossing 100 x 100 ft under a 93 ft tile dome; the western
// towers reached the roof of the nave, the south tower 50 ft more (Wikipedia).
const STJOHN_RING = P(
  -17.5, -75.1, -19.3, -13.6, -15.7, -13.5, -16.2, -5.2, -24.5, -5.5, -24.3, -10.8, -34.7, -11.1, -35.4, -3.1, -39.5, -3.5, -39.7, 3.5, -45.0, 4.2, -45.1,
  7.1, -38.0, 9.2, -38.3, 18.2, -45.1, 20.4, -45.2, 23.1, -40.9, 23.2, -38.7, 31.4, -25.8, 32.3, -26.1, 41.2, -29.7, 41.1, -30.2, 58.0, -29.6, 60.4, -18.5,
  63.6, -25.5, 70.5, -23.1, 74.6, -18.4, 75.0, -15.6, 77.5, -15.7, 82.2, -10.9, 85.2, -3.5, 82.8, -3.7, 88.3, 7.4, 88.6, 7.6, 83.1, 15.0, 85.7, 19.7, 82.9,
  19.9, 78.0, 26.6, 76.1, 29.8, 71.0, 27.8, 66.7, 34.9, 64.4, 35.7, 42.5, 25.9, 42.2, 24.3, 24.6, 21.2, 24.6, 23.3, -3.6, 18.4, -3.9, 18.6, -12.7, 25.0,
  -12.6, 26.7, -73.1, 35.7, -75.0, 35.7, -87.4, 32.6, -91.7, 29.4, -89.3, 21.2, -89.5, 18.4, -92.0, 16.2, -88.6, -9.2, -88.9, -11.5, -91.0, -11.6, -89.0,
  -20.2, -89.2, -22.5, -91.3, -24.8, -88.8, -23.1, -86.2, -25.0, -75.3, -20.2, -72.7, -20.1, -75.2
);
const STJOHN_RING_1911 = STJOHN_RING.filter(p => p[1] > -14);
const STJOHN_FRAME: [number, number, number] = [21.0, -4.4, 119.9];

function buildStJohn(nave: boolean) {
  return (b: MeshBuilder) => {
    const granite = '#B9B3A6';
    const roof = '#6F7C78';
    b.frame(STJOHN_FRAME[0], STJOHN_FRAME[1], 0, STJOHN_FRAME[2], () => {
      b.color(granite).prism(nave ? STJOHN_RING : STJOHN_RING_1911, 0, 14);
      // crossing under the Guastavino tile dome (1909), rough granite piers
      b.color('#A8A294').box(3.7, 2.5, 14, 32, 31, 26, {top: false});
      b.color('#8C8C84').cap(rect(3.7, 2.5, 32, 31), 40).dome(3.7, 2.5, 14.2, 40, 8, 12, 4);
      // choir (1911) and apse with the seven Chapels of the Tongues around it
      b.color(granite).box(3.7, 39.5, 14, 17, 43, 22, {top: false});
      b.color(roof).gable(3.7, 39.5, 18, 43, 36, 8, true);
      b.color(granite).cylinder(3.7, 61, 8.5, 14, 36, 12, {top: false});
      b.color(roof);
      spire(b, 3.7, 61, 8.5, 36, 44, 12);
      if (!nave) return;
      // nave (1925–1941): outer walls the full height, roof ridge 177 ft
      b.color(granite).box(3.7, -44, 14, 44.4, 62, 24, {top: false});
      b.color(roof).gable(3.7, -44, 45.4, 62, 38, 15.95, true);
      // west front: narthex 207 ft wide, tower stumps; the south tower 50 ft higher
      b.color(granite).box(5.4, -83, 14, 60.6, 16, 24, {top: true});
      b.gable(5.4, -83, 26.6, 16, 38, 15.95, true);
      b.box(-16.4, -83, 38, 17, 16, 2).box(27.2, -83, 38, 17, 16, 15.2);
      b.color('#3D4A5C').box(5.4, -91.2, 26, 12.2, 0.4, 12.2, {top: false});
      b.color('#5B4A36');
      for (const x of [-16.4, 5.4, 27.2]) b.box(x, -91.9, 0, x === 5.4 ? 9 : 6, 0.6, x === 5.4 ? 15 : 11, {top: false});
    });
  };
}

const STJOHN_SOURCES = [WIKI + 'Cathedral_of_St._John_the_Divine', LPC('2585'), FOOTPRINTS];
const STJOHN_FACTS = {
  Built: 'cornerstone December 27, 1892; choir and crossing consecrated April 1911; nave and west front 1925–1941 (opened November 30, 1941); tower work 1982–1992; unfinished',
  Architects: 'Heins & LaFarge; Ralph Adams Cram',
  Dimensions: '601 ft (183 m) long; nave 248 x 146 ft with a 124 ft vault and a roof 177 ft high; crossing 100 ft square under a 93 ft tile dome',
  Model: 'plan from the city footprint; nave roof at the cited 177 ft (city-measured 51.4 m); chapel, choir, crossing and tower-stump levels estimated from photographs; the 1911 state is the part of the plan east of the nave'
};
CIVIC.push(
  {
    id: 'st_john_the_divine_1911',
    name: 'Cathedral of St. John the Divine (choir and crossing, before the nave)',
    kind: 'building',
    built: [1892.99, 1911.3],
    end: 1941.91,
    anchor: [-73.9619, 40.8038],
    build: buildStJohn(false),
    facts: STJOHN_FACTS,
    sources: STJOHN_SOURCES
  },
  {
    id: 'st_john_the_divine',
    name: 'Cathedral of St. John the Divine',
    kind: 'building',
    built: [1925.0, 1941.91],
    end: 9999,
    anchor: [-73.9619, 40.8038],
    build: buildStJohn(true),
    replaces: [place(STJOHN_RING, ...STJOHN_FRAME)],
    facts: STJOHN_FACTS,
    sources: STJOHN_SOURCES
  }
);

// ====================================================================== Riverside Church
// Frame at the footprint centroid, +y at 29.9° (north, the chancel); Riverside Drive is -x.
// Tower 392 ft; nave 100 ft high, 89 ft wide, 215 ft long, 60 ft between the clerestory
// walls (Wikipedia). City-measured top 118.0 m.
const RIVERSIDE_RING = P(
  10.6, 48.8, 11.1, -9.4, 23.6, -9.3, 23.7, -17.8, 41.6, -17.6, 41.6, -23.3, 19.5, -23.6, 19.6, -43.3, 14.0, -43.4, 14.0, -41.3, -15.2, -41.6, -15.3, -29.6,
  -17.4, -29.6, -17.4, -23.1, -18.5, -23.1, -18.6, -18.9, -17.5, -18.9, -17.6, -8.1, -18.4, -8.1, -18.6, 47.2, -11.1, 47.3, -6.3, 49.3, -1.2, 48.6
);

function buildRiverside(b: MeshBuilder) {
  const ls = '#D2CBB8';
  const roof = '#7E8A86';
  b.frame(10.1, 17.1, 0, 29.9, () => {
    const body = P(
      10.6, 48.8, 11.1, -9.4, 19.55, -9.4, 19.6, -43.3, 14.0, -43.4, 14.0, -41.3, -15.2, -41.6, -15.3, -29.6, -17.4, -29.6, -17.4, -23.1, -18.5, -23.1, -18.6, -18.9, -17.5,
      -18.9, -17.6, -8.1, -18.4, -8.1, -18.6, 47.2, -11.1, 47.3, -6.3, 49.3, -1.2, 48.6
    );
    b.color(ls).prism(body, 0, 15);
    // cloister passage to Claremont Avenue
    b.prism(P(19.55, -9.3, 23.6, -9.3, 23.7, -17.8, 41.6, -17.6, 41.6, -23.3, 19.55, -23.6), 0, 7);
    // nave: clerestory walls 60 ft apart
    b.box(-3.8, 20, 15, 18.3, 57, 16, {top: false});
    b.color(roof).gable(-3.8, 20, 19.3, 57, 31, 6, true);
    // the 22-storey tower over the narthex
    const tx = 2.2;
    const ty = -26.4;
    b.color(ls).box(tx, ty, 15, 34.8, 34, 17);
    b.box(tx, ty, 32, 22, 22, 50, {top: false});
    b.box(tx, ty, 82, 20.5, 20.5, 22, {top: false});
    b.color('#4A5257');
    for (const s of [-1, 1])
      for (const o of [-5.5, 0, 5.5]) {
        b.box(tx + o, ty + s * 10.2, 85, 3, 0.5, 16, {top: false});
        b.box(tx + s * 10.2, ty + o, 85, 0.5, 3, 16, {top: false});
      }
    b.color(ls);
    for (const dx of [-1, 1])
      for (const dy of [-1, 1]) {
        b.cylinder(tx + dx * 9.6, ty + dy * 9.6, 2.3, 82, 108, 8);
        spire(b, tx + dx * 9.6, ty + dy * 9.6, 2.3, 108, 113, 8);
      }
    b.box(tx, ty, 104, 15, 15, 4);
    b.cylinder(tx, ty, 6, 108, 113, 8);
    b.color(roof);
    spire(b, tx, ty, 6, 113, 119.5, 8);
  });
}

CIVIC.push({
  id: 'riverside_church',
  name: 'Riverside Church',
  kind: 'building',
  built: [1927.0, 1930.76],
  end: 9999,
  anchor: [-73.96315, 40.81185],
  build: buildRiverside,
  replaces: [place(RIVERSIDE_RING, 10.1, 17.1, 29.9)],
  facts: {
    Built: '1927–1930 (first service October 5, 1930); the Martin Luther King Jr. wing to the south (1959) is a separate building and is not part of this model',
    Architects: 'Allen & Collens with Henry C. Pelton',
    Tower: '392 ft (119.5 m), 22 storeys, with a 74-bell carillon — the tallest church in the United States',
    Nave: '100 ft high, 89 ft wide, 215 ft long',
    Model: 'plan from the city footprint; the plan of the tower shaft (22 m square, centred on its base block) and the stage heights, and the height of the passage to Claremont Avenue (7 m), estimated from photographs'
  },
  sources: [WIKI + 'Riverside_Church', LPC('2037'), FOOTPRINTS]
});

// ====================================================================== Grant's Tomb
// Frame at the footprint centre, +y at 21° (north); the portico faces south (-y).
// 150 ft tall; base 90 x 90 ft and 72 ft high; stairs 70 ft wide (Wikipedia).
function buildGrantsTomb(b: MeshBuilder) {
  const g = '#E4E1D9';
  b.frame(-0.2, 6.9, 0, 21, () => {
    b.color(g).box(0, 0, 0, 26.8, 26.8, 20.4, {top: false});
    b.box(0, 0, 20.4, 27.6, 27.6, 1.55);
    // portico of six Doric columns above the 70 ft flight of steps
    b.color('#D8D4CA').box(0, -17.6, 0, 21.3, 8.4, 2.4);
    b.color(g);
    columns(b, -8.5, -16.4, 8.5, -16.4, 6, 1.5, 2.4, 11.5);
    b.box(0, -15.4, 11.5, 19.6, 4.4, 2.2).box(0, -15.0, 13.7, 15, 3.4, 1.6);
    b.color('#4B4B48').box(0, -13.5, 2.4, 3, 0.4, 6.5, {top: false});
    // stepped attic, circular colonnade of Ionic columns, stepped cone
    b.color(g).box(0, 0, 21.95, 22, 22, 1.95);
    b.color('#D5D2C9').cylinder(0, 0, 8.4, 23.9, 34, 16, {top: false});
    b.color(g);
    for (let k = 0; k < 20; k++) {
      const a = (k / 20) * Math.PI * 2;
      b.cylinder(Math.cos(a) * 10.1, Math.sin(a) * 10.1, 0.6, 23.9, 34, 6, {top: false});
    }
    b.cylinder(0, 0, 10.9, 34, 36.2, 20);
    b.frustum(0, 0, 10.4, 7.6, 36.2, 39.6, 20).frustum(0, 0, 7.4, 4.6, 39.6, 43, 20).frustum(0, 0, 4.4, 1.6, 43, 45.72, 20);
  });
}

CIVIC.push({
  id: 'grants_tomb',
  name: "General Grant National Memorial (Grant's Tomb)",
  kind: 'monument',
  built: [1891.32, 1897.32],
  end: 9999,
  anchor: [-73.96305, 40.8134],
  build: buildGrantsTomb,
  replaces: [place(rect(0, 0, 27.6, 27.6), -0.2, 6.9, 21)],
  facts: {
    Built: 'ground broken April 27, 1891; dedicated April 27, 1897',
    Architect: 'John H. Duncan',
    Height: '150 ft (45.7 m); the base 90 ft square and 72 ft high',
    Note: 'the largest mausoleum in North America',
    Model: 'base from the city footprint; the drum, its colonnade and the stepped cone are proportioned from photographs between the cited 72 ft and 150 ft levels'
  },
  sources: [WIKI + "Grant's_Tomb", 'https://www.nps.gov/gegr/index.htm', LPC('0900'), FOOTPRINTS]
});

// ====================================================================== City Hall
// Frame at the footprint centroid, +y at 33.6° (north, the rear); the front faces the park
// (-y). Levels from OpenStreetMap 3D parts (walls 13.7 m, attic 17 m, roof 20 m, cupola
// stages to 31.5 m); the top of the figure of Justice is the city-measured 36.6 m.
const CITYHALL_RING = P(
  -33.1, 14.1, -9.2, 14.1, -9.2, 17.5, 9.0, 17.5, 9.0, 14.1, 33.2, 14.1, 33.1, -18.2, 21.3, -18.2, 21.3, -11.3, 8.8, -11.3, 8.8, -15.1, -8.6, -15.1, -8.6, -11.3,
  -21.1, -11.3, -21.1, -18.2, -33.2, -18.2
);

function buildCityHall(b: MeshBuilder) {
  const stone = '#E8E4DA';
  const roof = '#8C9794';
  b.frame(4.8, 0.3, 0, 33.6, () => {
    b.color(stone).prism(CITYHALL_RING, 0, 13.7, {top: false});
    b.color(roof).cap(CITYHALL_RING, 13.7);
    // central attic storey and hipped roof
    b.color(stone).box(0, 2.75, 13.7, 18, 29.4, 3.3, {top: false});
    b.color(roof).hip(0, 2.75, 18, 29.4, 17, 3);
    // one-storey Ionic portico with a balustraded balcony, at the head of the steps
    b.color('#D9D5CA').box(0, -16.6, 0, 17.4, 3, 1.6);
    b.color(stone);
    columns(b, -7.6, -14.5, 7.6, -14.5, 6, 0.8, 1.6, 7);
    b.box(0, -13.2, 7, 17.4, 3.8, 0.8);
    // cupola: octagonal base, colonnaded drum, dome, the figure of Justice
    const cx = -0.1;
    const cy = -3.2;
    b.cylinder(cx, cy, 3.7, 13.7, 20, 8);
    b.cylinder(cx, cy, 2.7, 20, 27, 8, {top: false});
    for (let k = 0; k < 8; k++) {
      const a = ((k + 0.5) / 8) * Math.PI * 2;
      b.cylinder(cx + Math.cos(a) * 3.2, cy + Math.sin(a) * 3.2, 0.3, 20, 26, 5, {top: false});
    }
    b.cylinder(cx, cy, 3.5, 26, 27, 8);
    b.color('#B7C4BE').dome(cx, cy, 2.6, 27, 4.5, 8, 4);
    b.color('#D8D4C6').cylinder(cx, cy, 0.5, 31.5, 33, 6);
    b.loft([circle(cx, cy, 0.55, 6), circle(cx, cy, 0.3, 6)], [33, 36.6]);
  });
}

CIVIC.push({
  id: 'new_york_city_hall',
  name: 'New York City Hall',
  kind: 'building',
  built: [1803.4, 1812.5],
  end: 9999,
  anchor: [-74.00605, 40.71275],
  build: buildCityHall,
  replaces: [place(CITYHALL_RING, 4.8, 0.3, 33.6)],
  facts: {
    Built: 'cornerstone May 26, 1803; occupied 1811–1812 — the oldest city hall in the United States still housing its government',
    Architects: 'Joseph-François Mangin and John McComb Jr.',
    Note: 'the marble front faced the city; the rear was brownstone until the 1954–56 refacing in limestone; cupola rebuilt after the fires of 1858 and 1917',
    Model: 'plan from the city footprint; wall, attic, roof and cupola levels from OpenStreetMap 3D parts; top of the figure of Justice at the city-measured 36.6 m; portico heights estimated'
  },
  sources: [WIKI + 'New_York_City_Hall', LPC('0080'), FOOTPRINTS, OSM]
});

// ====================================================================== Federal Hall National Memorial
// The Custom House of 1842. Frame at the footprint centre, +y at 36.5° (north, Pine
// Street); Wall Street is -y. 28.4 x 55.5 m (footprint); cella 46.5 m long and 12 m to the
// eaves, ridge 19.3 m (OSM parts, city-measured); columns 32 ft high and 5 ft 8 in across;
// rotunda 60 ft in diameter (Wikipedia).
function buildFederalHall(b: MeshBuilder) {
  const marble = '#E6E2D8';
  b.frame(0, 3.9, 0, 36.5, () => {
    // stepped base rising from Wall Street
    b.color('#D4D0C5').box(0, 0, 0, 28.4, 55.5, 2.6);
    b.color(marble).box(0, 0, 2.6, 26.6, 46.5, 12.3, {top: false});
    // octastyle Doric porticoes at both ends
    for (const s of [-1, 1]) columns(b, -12.4, s * 26.4, 12.4, s * 26.4, 8, 1.73, 2.6, 12.35, 8);
    b.box(0, 0, 12.35, 28.4, 55.5, 2.6);
    b.color('#B9C0BC').gable(0, 0, 28.4, 55.5, 14.95, 4.35, true);
    // pilasters along the flanks
    b.color('#D9D5CA');
    for (let y = -20; y <= 20; y += 5.7) for (const s of [-1, 1]) b.box(s * 13.5, y, 2.6, 0.5, 1.5, 9.75, {top: false});
    // J. Q. A. Ward's George Washington (1883) on the Wall Street steps
    b.color('#5A5F52').box(0, -29.2, 0, 1.6, 1.6, 2.4).box(0, -29.2, 2.4, 0.9, 0.7, 3.4);
  });
}

CIVIC.push({
  id: 'federal_hall_national_memorial',
  name: 'Federal Hall National Memorial (U.S. Custom House of 1842)',
  kind: 'building',
  built: [1834.5, 1842.5],
  end: 9999,
  anchor: [-74.01025, 40.7073],
  build: buildFederalHall,
  replaces: [place(rect(0, 0, 29, 56), 0, 3.9, 36.5)],
  facts: {
    Built: '1834–1842 as the U.S. Custom House (Town & Davis, John Frazee); Sub-Treasury 1862–1920',
    Site: 'the City Hall of 1703, remodelled in 1789 as Federal Hall — where Washington was inaugurated — and demolished in 1812',
    Dimensions: 'Doric columns 32 ft high and 5 ft 8 in across, each a single block of marble; rotunda 60 ft in diameter',
    Model: 'plan from the city footprint; eaves 12 m and ridge 19.3 m from OpenStreetMap 3D parts and the city-measured roof height; base and entablature levels estimated'
  },
  sources: [WIKI + 'Federal_Hall', 'https://www.nps.gov/feha/index.htm', LPC('0047'), FOOTPRINTS, OSM]
});

// ====================================================================== Alexander Hamilton U.S. Custom House
// Frame at the footprint centroid, +y at 181.4° (south, Bridge Street); the main front on
// Bowling Green is -y. Front 200 ft, sides 300 ft, rear 290 ft; rusticated base 20 ft;
// attic statues 11 ft; light court 80–120 ft wide and 200 ft deep (Wikipedia). OSM parts:
// walls 29 m, elliptical rotunda skylight 24.4 x 38.7 m.
const CUSTOM_RING = P(
  -28.4, -46.2, -28.3, -44.9, -30.6, -44.9, -32.7, -30.6, -31.5, -30.4, -40.0, 27.6, -41.5, 27.6, -43.5, 42.5, -17.3, 42.5, -17.5, 38.9, 16.5, 39.1, 17.0, 42.5,
  42.8, 42.4, 40.7, 27.8, 39.6, 27.9, 32.3, -29.8, 33.6, -29.9, 31.7, -44.4, 29.6, -44.1, 29.4, -45.5
);

function buildCustomHouse(b: MeshBuilder) {
  const granite = '#C9C3B5';
  const court = P(-9.7, -17, 11.9, -17, 16.5, 33, -14.5, 33);
  const inset = CUSTOM_RING.map(([x, y]) => [x * 0.93, y * 0.93] as V2);
  b.frame(-3.8, -10.8, 0, 181.4, () => {
    b.color('#BDB7A9').prism(CUSTOM_RING, 0, 6.1, {top: false});
    b.color(granite).prism(CUSTOM_RING, 6.1, 29, {top: false, holes: [court]});
    // seventh storey in the mansard
    b.color('#8E9A97').loft([CUSTOM_RING, inset], [29, 34], {top: false});
    b.cap(inset, 34, [court]);
    // light court over the elliptical rotunda
    b.color('#AFA99C').cap(court, 12);
    b.color('#9FB3B8').loft([oval(0.8, 6, 11.5, 17.5, 16), oval(0.8, 6, 8.5, 13, 16), oval(0.8, 6, 4, 6, 16)], [12, 14, 15]);
    // Bowling Green front: twelve Corinthian columns under twelve 11 ft statues of
    // seafaring nations; the stair and Daniel Chester French's Four Continents
    b.color('#D6D0C2');
    columns(b, -25.5, -46.9, 26.5, -46.9, 12, 1.5, 6.1, 23);
    b.box(0.5, -46.4, 23, 56, 2.2, 3);
    for (let i = 0; i < 12; i++) b.box(-25.5 + (52 * i) / 11, -46.6, 29, 1.1, 0.9, 3.35);
    b.color('#BDB7A9').box(0.5, -50, 0, 16, 7, 5);
    b.color('#E3DFD3');
    for (const x of [-25, -12, 13, 26]) b.box(x, -50.5, 0, 3.4, 4.6, 2.6).box(x, -50.5, 2.6, 2.2, 3, 3);
  });
}

CIVIC.push({
  id: 'us_custom_house_bowling_green',
  name: 'Alexander Hamilton U.S. Custom House',
  kind: 'building',
  built: [1900.9, 1907.75],
  end: 9999,
  anchor: [-74.0137, 40.70415],
  build: buildCustomHouse,
  replaces: [place(CUSTOM_RING, -3.8, -10.8, 181.4)],
  facts: {
    Built: '1900–1907 (Cass Gilbert) on the site of Fort Amsterdam and Government House',
    Dimensions: 'front on Bowling Green 200 ft, sides 300 ft, rear 290 ft; seven storeys',
    Sculpture: 'the Four Continents by Daniel Chester French; twelve 11 ft statues of seafaring nations on the attic',
    Model: 'plan from the city footprint; wall height 29 m and the rotunda skylight from OpenStreetMap 3D parts; mansard (34 m) and column levels estimated; the city-measured 39.8 m is rooftop plant, not modelled'
  },
  sources: [WIKI + 'Alexander_Hamilton_U.S._Custom_House', LPC('0020'), FOOTPRINTS, OSM]
});

// ====================================================================== Tweed Courthouse
// Frame at the footprint centroid, +y at 211.2° (south, towards City Hall); Chambers
// Street is -y. 258 x 149 ft; octagonal rotunda 53 ft across and 85 ft high (Wikipedia).
// OSM parts: walls 17 m, roofs 20 m, rotunda skylight to 25 m (the city-measured top).
const TWEED_RING = P(
  20.2, -24.7, 20.2, -19.4, 8.3, -19.4, 8.3, -24.2, -8.2, -24.2, -8.2, -19.5, -20.0, -19.5, -20.0, -25.2, -38.4, -25.2, -38.4, -9.9, -39.1, -9.9, -38.3, 22.1,
  -20.2, 22.1, -20.3, 16.9, -8.7, 16.9, -8.7, 31.2, 8.3, 31.2, 8.3, 17.0, 19.7, 17.0, 19.7, 22.7, 38.3, 22.7, 38.3, 7.3, 39.0, 7.3, 38.3, -24.7
);

function buildTweed(b: MeshBuilder) {
  const marble = '#DAD6CC';
  const roof = '#7E8785';
  b.frame(4.2, -6.4, 0, 211.2, () => {
    b.color(marble).prism(TWEED_RING, 0, 17);
    b.color(roof);
    for (const s of [-1, 1]) b.hip(s * 29.3, -1.3, 18.2, 47.6, 17, 3);
    b.gable(0, -1.3, 40.4, 36.4, 17, 3, false);
    b.gable(-0.2, 24, 17, 14.4, 17, 3, true);
    // Chambers Street portico: four Corinthian columns and a pediment over the great stair
    b.color('#CFCBC0').box(0, -27.4, 0, 14, 6.4, 5.5);
    b.color(marble);
    columns(b, -6.6, -23.7, 6.6, -23.7, 4, 1.3, 5.5, 14.6);
    b.box(0, -21.9, 14.6, 16.5, 4.8, 2.4);
    b.gable(0, -21.9, 16.5, 4.8, 17, 3.3, true);
    // octagonal rotunda skylight
    b.color('#B9C4C4').cylinder(-0.5, -1, 8.2, 17, 22, 8, {top: false});
    b.color(roof);
    spire(b, -0.5, -1, 8.2, 22, 25, 8);
  });
}

CIVIC.push({
  id: 'tweed_courthouse',
  name: 'Tweed Courthouse (Old New York County Courthouse)',
  kind: 'building',
  built: [1861.7, 1881.9],
  end: 9999,
  anchor: [-74.0056, 40.71345],
  build: buildTweed,
  replaces: [place(TWEED_RING, 4.2, -6.4, 211.2)],
  facts: {
    Built: '1861–1881 (John Kellum; finished by Leopold Eidlitz, who added the south wing 1877–1881)',
    Dimensions: '258 x 149 ft; octagonal rotunda 53 ft across, 85 ft high',
    Note: 'the building through which the Tweed Ring stole millions; the Chambers Street stair, removed in 1942, was rebuilt in 2001',
    Model: 'plan from the city footprint; walls 17 m, roofs 20 m and the rotunda skylight (25 m) from OpenStreetMap 3D parts; portico levels estimated; the building is shown complete from 1881'
  },
  sources: [WIKI + 'Tweed_Courthouse', LPC('1437'), FOOTPRINTS, OSM]
});

// ====================================================================== New York Stock Exchange
// The 1903 building at 8–18 Broad Street. Frame at the footprint centroid, +y at 295.8°
// (west, New Street); Broad Street is -y. Roof 156 ft above the sidewalk; six Corinthian
// columns 52 ft tall and 5.5 ft across; windows 96 x 50 ft; pediment about 110 ft wide
// and about 100 ft above the sidewalk (Wikipedia).
const NYSE_RING = P(18.6, -21.3, -22.7, -21.3, -21.1, 0.2, -16.3, 0, -16.6, 23.1, 19.8, 22.7);

function buildNYSE(b: MeshBuilder) {
  const marble = '#E9E6DE';
  b.frame(-9.0, 3.7, 0, 295.8, () => {
    b.color(marble).prism(NYSE_RING, 0, 36, {top: true});
    // upper floors set back behind the front
    b.prism(P(18.9, -13, -22.1, -13, -21.1, 0.2, -16.3, 0, -16.6, 23.1, 19.8, 22.7), 36, 47.55);
    // Broad Street front: two-storey podium, colonnade before the trading-floor window
    b.color('#D9D5CA').box(-2.05, -21.8, 0, 35, 1.4, 9);
    b.color('#3F4A52').box(-2.05, -21.5, 9, 29.3, 0.5, 15.24, {top: false});
    b.color('#F1EEE6');
    columns(b, -15.9, -22.3, 11.8, -22.3, 6, 1.68, 9, 24.85, 8);
    b.box(-2.05, -22, 24.85, 33.5, 2.4, 3.2);
    b.gable(-2.05, -22, 33.5, 2.4, 28.05, 4.6, true);
  });
}

CIVIC.push({
  id: 'new_york_stock_exchange',
  name: 'New York Stock Exchange Building',
  kind: 'building',
  built: [1901.3, 1903.31],
  end: 9999,
  anchor: [-74.01115, 40.7069],
  build: buildNYSE,
  replaces: [place(NYSE_RING, -9.0, 3.7, 295.8)],
  facts: {
    Opened: 'April 22, 1903 (George B. Post); the 23-storey annex at 11 Wall Street followed in 1922',
    Front: 'six Corinthian columns 52 ft tall before a 96 x 50 ft window; pediment by J. Q. A. Ward and Paul Wayland Bartlett, about 110 ft wide',
    Height: 'roof 156 ft (47.5 m) above the sidewalk; trading floor ceiling 72 ft',
    Model: 'plan from the city footprint; podium, entablature and setback levels estimated from photographs (city-measured roof 44.5 m)'
  },
  sources: [WIKI + 'New_York_Stock_Exchange_Building', LPC('1529'), FOOTPRINTS]
});

// ====================================================================== Castle Clinton
// Ring = the city footprint about its centroid (x east, y north); the flat side with the
// gate faces north-east. Walls 8 ft thick (Wikipedia); city-measured top 7.8 m.
const CASTLE_RING = P(
  16.1, 22.8, 26.6, -0.5, 30.0, -2.2, 31.7, -5.1, 28.0, -16.0, 20.5, -23.9, 8.2, -29.3, -4.8, -29.1, -16.1, -23.8, -24.0, -15.6, -28.6, -3.6, -28.3, 7.3, -23.1,
  19.1, -11.9, 28.6, -0.8, 31.9, 12.9, 30.4, 15.8, 27.4
);
// courtyard: 1,114 m2 in the city footprint (ring 2,753 m2 less the 1,639 m2 of walls and casemates)
const CASTLE_INNER = CASTLE_RING.map(([x, y]) => [1 + (x - 1) * 0.636, 1 + (y - 1) * 0.636] as V2);

function buildCastleClinton(b: MeshBuilder) {
  b.frame(0.8, -4.5, 0, 0, () => {
    b.color('#9C6B52').prism(CASTLE_RING, 0, 6.5, {top: false, holes: [CASTLE_INNER]});
    b.color('#8A8478').cap(CASTLE_RING, 6.5, [CASTLE_INNER]);
    b.color('#B9B1A1').cap(CASTLE_INNER, 0.2);
    // gun embrasures
    b.color('#3E342E');
    for (let k = 0; k < 28; k++) {
      const a = ((113 + (k * 286) / 27) * Math.PI) / 180;
      b.frame(1 + Math.cos(a) * 30.2, 1 + Math.sin(a) * 30.2, 0, 90 - (a * 180) / Math.PI, () => b.box(0, 0, 2.2, 1.6, 0.7, 1.3, {top: false}));
    }
    // gatehouse on the landward side
    b.frame(21.4, 11.2, 0, 66, () => {
      b.color('#9C6B52').box(0, 0, 0, 8, 3, 7.8);
      b.color('#3E342E').box(0, 1.4, 0, 3, 0.6, 4.2, {top: false});
    });
  });
}

function buildCastleGarden(b: MeshBuilder) {
  // the roofed hall of Castle Garden / the Aquarium, standing on the fort walls
  const mid = CASTLE_RING.map(([x, y]) => [1 + (x - 1) * 0.97, 1 + (y - 1) * 0.97] as V2);
  const top = CASTLE_RING.map(([x, y]) => [1 + (x - 1) * 0.3, 1 + (y - 1) * 0.3] as V2);
  b.frame(0.8, -4.5, 0, 0, () => {
    b.color('#C9BBA2').prism(mid, 6.5, 10.5, {top: false});
    b.color('#6E6A64').loft([mid, top], [10.5, 16], {top: false});
    b.color('#C9BBA2').prism(top, 16, 18.5, {top: false});
    b.color('#6E6A64').pyramid(top, 18.5, [1, 1, 21.5]);
  });
}

const CASTLE_SOURCES = [WIKI + 'Castle_Clinton', 'https://www.nps.gov/cacl/learn/historyculture/index.htm', LPC('0029'), FOOTPRINTS];
CIVIC.push(
  {
    id: 'castle_clinton',
    name: 'Castle Clinton (West Battery)',
    kind: 'monument',
    built: [1808.5, 1811.9],
    end: 9999,
    anchor: [-74.0168, 40.7035],
    build: buildCastleClinton,
    replaces: [place(CASTLE_RING, 0.8, -4.5, 0)],
    facts: {
      Built: '1808–1811 as the West Battery, on an artificial island 200 ft off the Battery; renamed Castle Clinton in 1815',
      Later: 'Castle Garden, a resort and theatre (1824); immigrant landing depot (1855–1890); the New York Aquarium (1896–1941); stripped to its walls in the 1940s and restored 1970–1975',
      Walls: 'red sandstone, 8 ft thick, with 28 gun embrasures',
      Model: 'outline and courtyard area from the city footprint, top at the city-measured 7.8 m; wall-walk level (6.5 m) estimated'
    },
    sources: CASTLE_SOURCES
  },
  {
    id: 'castle_garden_hall',
    name: 'Castle Garden / New York Aquarium (the roofed hall on Castle Clinton)',
    kind: 'building',
    built: [1844.0, 1845.5],
    end: 1941.8,
    anchor: [-74.0168, 40.7035],
    build: buildCastleGarden,
    facts: {
      Use: 'roofed over in the 1840s as a concert hall (Jenny Lind sang here in 1850); immigrant depot 1855–1890, receiving some eight million people; aquarium 1896–1941',
      Model: 'the form and height of the roof are estimated from nineteenth-century views — no measured drawing was found; the Aquarium’s added storeys (1920s) are not shown'
    },
    sources: CASTLE_SOURCES
  }
);

// ====================================================================== memorial arches
/** A wall along x (width w, depth d) from z0 to zTop pierced by a round arch of half-width r springing at zs. */
function archWall(b: MeshBuilder, w: number, d: number, r: number, zs: number, zTop: number) {
  const pw = w / 2 - r;
  for (const s of [-1, 1]) b.box(s * (r + pw / 2), 0, 0, pw, d, zTop);
  const n = 10;
  const pts: [number, number][] = [];
  for (let k = 0; k <= n; k++) {
    const a = (k / n) * Math.PI;
    pts.push([r * Math.cos(a), zs + r * Math.sin(a)]);
  }
  for (let k = 0; k < n; k++) {
    const [x0, z0] = pts[k];
    const [x1, z1] = pts[k + 1];
    for (const y of [-d / 2, d / 2]) b.quad([x0, y, z0], [x1, y, z1], [x1, y, zTop], [x0, y, zTop]);
    b.quad([x0, -d / 2, z0], [x1, -d / 2, z1], [x1, d / 2, z1], [x0, d / 2, z0]);
  }
  b.cap(rect(0, 0, 2 * r, d), zTop);
}

// Washington Square Arch: 77 ft high, piers 30 ft apart, opening 47 ft high (Wikipedia);
// 19.4 x 7.1 m in plan (city footprint). Frame +y at 32.7° (north, up Fifth Avenue).
function buildWashingtonArch(b: MeshBuilder) {
  b.frame(4.4, 4.3, 0, 32.7, () => {
    b.color('#EDEAE2');
    archWall(b, 19.4, 7.1, 4.57, 9.76, 17.4);
    b.box(0, 0, 17.4, 19.9, 7.6, 0.9);
    b.box(0, 0, 18.3, 19.4, 7.1, 5.17);
    // Washington at War (1916) and at Peace (1918) against the north face of the piers
    b.color('#DCD8CE');
    for (const s of [-1, 1]) b.box(s * 7.1, 3.75, 0, 3, 0.7, 3.2).box(s * 7.1, 3.75, 3.2, 1.3, 0.7, 4.9);
  });
}

CIVIC.push({
  id: 'washington_square_arch',
  name: 'Washington Square Arch',
  kind: 'monument',
  built: [1890.41, 1892.3],
  end: 9999,
  anchor: [-73.99715, 40.7312],
  build: buildWashingtonArch,
  replaces: [place(rect(0, 0, 20.4, 8.1), 4.4, 4.3, 32.7)],
  facts: {
    Built: 'cornerstone May 30, 1890; completed 1892, dedicated 1895 (Stanford White) — in marble, after the wooden arch of 1889 raised for the centennial of Washington’s inauguration',
    Dimensions: '77 ft (23.5 m) high; piers 30 ft apart; opening 47 ft high',
    Model: 'plan from the city footprint; cornice level estimated; the statues of Washington (1916, 1918) are shown from 1892'
  },
  sources: [WIKI + 'Washington_Square_Arch', FOOTPRINTS]
});

// Soldiers' and Sailors' Arch: 80 ft tall, 80 ft wide, opening 50 ft tall and 35 ft wide
// (Wikipedia); 23.4 x 7.5 m in plan (city footprint). Frame +y at 350.9°; the quadriga faces south (-y).
function buildSoldiersArch(b: MeshBuilder) {
  b.frame(3.8, 10.7, 0, 350.9, () => {
    b.color('#CFC9BD');
    // piers 5.1 x 7.5 m joined by a 5.3 m deep vault (city footprint)
    archWall(b, 13.4, 5.3, 5.33, 9.91, 18.6);
    for (const s of [-1, 1]) b.box(s * 9.15, 0, 0, 5.1, 7.5, 18.6).box(s * 9.15, 0, 18.6, 5.5, 7.9, 0.9);
    b.box(0, 0, 18.6, 13.6, 5.7, 0.9);
    b.box(0, 0, 19.5, 23.4, 5.3, 4.88);
    for (const s of [-1, 1]) b.box(s * 9.15, 0, 19.5, 5.1, 7.5, 4.88);
    // MacMonnies's quadriga (1898): Columbia in a chariot between two winged Victories
    b.color('#5E7265').box(0, -0.6, 24.38, 10.5, 5, 0.6);
    for (const x of [-3.3, -1.1, 1.1, 3.3]) b.box(x, -2, 24.98, 0.9, 2.6, 2.4).box(x, -3, 27.0, 0.6, 0.9, 1.3);
    b.box(0, 0.9, 24.98, 2.4, 2, 2).box(0, 0.9, 26.98, 0.9, 0.8, 3.6);
    for (const s of [-1, 1]) b.box(s * 5.6, -1.6, 24.98, 0.9, 0.9, 3.4);
  });
}

CIVIC.push({
  id: 'soldiers_and_sailors_arch',
  name: "Soldiers' and Sailors' Memorial Arch (Grand Army Plaza)",
  kind: 'monument',
  built: [1889.83, 1892.8],
  end: 9999,
  anchor: [-73.96995, 40.6729],
  build: buildSoldiersArch,
  replaces: [place(rect(0, 0, 25.2, 8.3), 3.8, 10.7, 350.9)],
  facts: {
    Built: 'cornerstone October 30, 1889; dedicated October 21, 1892 (John H. Duncan); bronze groups by Frederick MacMonnies 1894–1901',
    Dimensions: '80 ft (24.4 m) tall and 80 ft wide; opening 50 ft tall and 35 ft wide',
    Model: 'depth from the city footprint (7.5 m); cornice level and the height of the quadriga (about 6 m) estimated; the sculpture is shown from 1892'
  },
  sources: [WIKI + "Soldiers'_and_Sailors'_Arch", LPC('0821'), FOOTPRINTS]
});

// ====================================================================== Metropolitan Museum of Art
// Frame at the footprint centroid, +y at 298.9° (west, into Central Park); Fifth Avenue is
// -y, +x is north. The city footprint is one polygon for the whole complex. It is divided
// here — an estimate from the shape of the outline, not a surveyed phase plan — into the
// Fifth Avenue building as it stood by 1926 (Hunt's central pavilion of 1902, McKim, Mead &
// White's wings of 1909–1926, the older buildings they enclose) and the three park-side
// wings of the 1970–1991 master plan (Roche Dinkeloo).
const MET_FRAME: [number, number, number] = [-19.8, -1.8, 298.9];
const MET_RING = P(
  140.0, 84.0, 139.8, 28.6, 153.8, 29.9, 153.8, 23.6, 144.6, 23.7, 144.6, 21.8, 146.7, 21.8, 146.4, -38.6, 143.9, -38.6, 143.9, -40.2, 152.8, -40.2, 151.2,
  -83.3, 89.2, -82.9, 89.2, -72.0, 31.6, -71.5, 31.6, -73.0, -88.8, -70.8, -88.9, -82.9, -151.0, -83.0, -152.2, -39.2, -139.7, -39.3, -139.7, -37.1, -146.0,
  -37.0, -145.7, 24.0, -143.5, 23.9, -143.5, 26.0, -152.6, 26.0, -152.6, 32.5, -144.8, 32.5, -144.8, 30.6, -141.0, 30.5, -140.7, 86.6, -89.3, 86.2, -89.4,
  64.7, -15.6, 63.2, -15.5, 69.6, -19.6, 73.8, -28.3, 73.9, -28.3, 82.6, -5.3, 106.1, 5.2, 106.1, 28.1, 83.1, 28.1, 73.8, 19.1, 73.8, 15.5, 69.4, 15.4, 63.3,
  88.4, 62.2, 88.5, 84.3, 90.8, 86.8, 137.7, 86.5
);
const MET_1926 = P(
  144.6, 29.5, 144.6, 21.8, 146.7, 21.8, 146.4, -38.6, 143.9, -38.6, 143.9, -40.2, 152.8, -40.2, 151.2, -83.3, 89.2, -82.9, 89.2, -72.0, 31.6, -71.5, 31.6,
  -73.0, -88.8, -70.8, -88.9, -82.9, -151.0, -83.0, -152.2, -39.2, -139.7, -39.3, -139.7, -37.1, -146.0, -37.0, -145.7, 24.0, -143.5, 23.9, -143.5, 30.5,
  -89.4, 30.5, -89.4, 64.7, -15.6, 63.2, 15.4, 63.3, 88.4, 62.2, 88.4, 29.5
);
const MET_LEHMAN = P(-15.6, 63.2, -15.5, 69.6, -19.6, 73.8, -28.3, 73.9, -28.3, 82.6, -5.3, 106.1, 5.2, 106.1, 28.1, 83.1, 28.1, 73.8, 19.1, 73.8, 15.5, 69.4, 15.4, 63.3);
const MET_NORTH = P(88.4, 29.5, 139.8, 29.5, 140.0, 84.0, 137.7, 86.5, 90.8, 86.8, 88.5, 84.3);
const MET_SOUTH = P(-89.4, 30.5, -141.0, 30.5, -140.7, 86.6, -89.3, 86.2);
const MET_LS = '#DAD4C6';
const MET_GLASS = '#9DB7C2';

function buildMet(b: MeshBuilder) {
  const roof = '#8E9692';
  b.frame(MET_FRAME[0], MET_FRAME[1], 0, MET_FRAME[2], () => {
    b.color(MET_LS).prism(MET_1926, 0, 18, {top: false});
    b.color(roof).cap(MET_1926, 18);
    // gallery skylights along the Fifth Avenue wings
    b.color(MET_GLASS);
    for (const s of [-1, 1]) b.gable(s * 60, -57, 52, 9, 18, 2.5, false);
    b.color(MET_LS);
    for (const s of [-1, 1]) b.box(s * 120.3, -61.6, 18, 61, 42.6, 2.5);
    // Richard Morris Hunt's central pavilion (1902): three arches between paired
    // Corinthian columns carrying uncarved blocks; three saucer domes over the Great Hall
    b.box(0, -59.5, 18, 63, 27, 6.5, {top: false});
    b.color(roof).cap(rect(0, -59.5, 63, 27), 24.5);
    b.color(MET_GLASS);
    for (const x of [-17.5, 0, 17.5]) b.dome(x, -60, 7.5, 24.5, 2.3, 10, 3);
    b.color('#4A555C');
    for (const x of [-17.2, 0, 17.2]) b.box(x, -73.2, 5.5, 9, 0.5, 12, {top: false});
    b.color('#E6E1D4');
    for (const x of [-25.8, -8.6, 8.6, 25.8]) {
      b.box(x, -74.3, 0, 5, 2.4, 5.5);
      columns(b, x - 1.5, -74.3, x + 1.5, -74.3, 2, 1.5, 5.5, 19.5);
      b.box(x, -74.1, 22, 4.2, 2, 2.5);
    }
    b.box(0, -73.7, 19.5, 64, 2.8, 2.5);
    b.color('#CFC9BB').box(0, -80, 0, 36, 12, 2.8).box(0, -77.5, 2.8, 30, 5, 2.7);
  });
}

function buildMetWing(which: 'lehman' | 'north' | 'south') {
  return (b: MeshBuilder) => {
    b.frame(MET_FRAME[0], MET_FRAME[1], 0, MET_FRAME[2], () => {
      if (which === 'lehman') {
        b.color(MET_LS).prism(MET_LEHMAN, 0, 13);
        const base = P(-28.3, 74, -28.3, 82.6, -5.3, 106.1, 5.2, 106.1, 28.1, 83.1, 28.1, 74).map(([x, y]) => [x * 0.9, 86 + (y - 86) * 0.9] as V2);
        b.color(MET_GLASS).pyramid(base, 13, [0, 86, 25]);
      } else {
        const s = which === 'north' ? 1 : -1;
        b.color(MET_LS).prism(which === 'north' ? MET_NORTH : MET_SOUTH, 0, 12);
        // glass wall and roof leaning in from the park side
        b.color(MET_GLASS).loft([rect(s * 114.6, 58, 47, 52), rect(s * 114.6, 52, 43, 36)], [12, 19]);
      }
    });
  };
}

const MET_SOURCES = [WIKI + 'Metropolitan_Museum_of_Art_Fifth_Avenue', LPC('0410'), FOOTPRINTS];
const MET_MODEL = 'outline from the city footprint (one polygon for the whole complex); its division into the building of 1926 and the three park-side wings is an estimate from the shape of the outline; roof levels estimated except the city-measured 26.8 m at the Great Hall domes';
CIVIC.push(
  {
    id: 'metropolitan_museum_of_art',
    name: 'Metropolitan Museum of Art — Fifth Avenue building',
    kind: 'building',
    built: [1895.9, 1902.96],
    end: 9999,
    anchor: [-73.9632, 40.77945],
    build: buildMet,
    replaces: [place(MET_RING, ...MET_FRAME)],
    facts: {
      Opened: 'the museum moved to Central Park on March 30, 1880 (Vaux & Mould’s building, now enclosed); Richard Morris Hunt’s Fifth Avenue pavilion and Great Hall opened in December 1902',
      Wings: 'McKim, Mead & White’s Fifth Avenue wings 1909–1926 (shown here from 1902); the brick buildings of 1880–1894 survive inside',
      Model: MET_MODEL
    },
    sources: MET_SOURCES
  },
  {
    id: 'metropolitan_museum_lehman_wing',
    name: 'Metropolitan Museum of Art — Robert Lehman Wing',
    kind: 'building',
    built: [1972.5, 1975.4],
    end: 9999,
    anchor: [-73.9632, 40.77945],
    build: buildMetWing('lehman'),
    facts: {Opened: '1975 (Kevin Roche John Dinkeloo & Associates): a glass pyramid over a court on the park side', Model: MET_MODEL},
    sources: MET_SOURCES
  },
  {
    id: 'metropolitan_museum_north_wings',
    name: 'Metropolitan Museum of Art — Sackler Wing and American Wing',
    kind: 'building',
    built: [1975.0, 1980.4],
    end: 9999,
    anchor: [-73.9632, 40.77945],
    build: buildMetWing('north'),
    facts: {Opened: 'Sackler Wing with the Temple of Dendur 1978; the American Wing and its glazed court 1980 (Roche Dinkeloo)', Model: MET_MODEL},
    sources: MET_SOURCES
  },
  {
    id: 'metropolitan_museum_south_wings',
    name: 'Metropolitan Museum of Art — Rockefeller and Wallace Wings',
    kind: 'building',
    built: [1978.0, 1987.1],
    end: 9999,
    anchor: [-73.9632, 40.77945],
    build: buildMetWing('south'),
    facts: {Opened: 'Michael C. Rockefeller Wing 1982; Lila Acheson Wallace Wing 1987 (Roche Dinkeloo)', Model: MET_MODEL},
    sources: MET_SOURCES
  }
);

// ====================================================================== American Museum of Natural History
// Frame +y at 29° (north, 81st Street); the 77th Street front is -y, Central Park West +x.
// Two city footprints: A (the 77th Street and Central Park West ranges, the Rose Center)
// and B (the inner ranges and the Gilder Center). The 77th Street front is 215 m (700 ft)
// long in the footprint; the corner towers are taken to be the city-measured 44.8 m.
const AMNH_FRAME: [number, number, number] = [-5.8, -36.9, 29.0];
const AMNH_A = P(
  49.0, 104.9, 55.5, 104.9, 55.5, 113.7, 63.9, 113.7, 63.9, 119.4, 69.6, 119.4, 69.6, 113.7, 75.6, 113.7, 75.5, 66.0, 81.3, 66.4, 81.3, 55.8, 88.8, 55.8, 88.8,
  20.4, 81.2, 20.4, 81.2, 9.5, 75.6, 9.5, 75.4, -36.5, 79.3, -40.5, 79.3, -58.6, 84.1, -59.4, 86.8, -62.7, 85.4, -69.1, 79.1, -71.0, 75.2, -68.1, 74.5, -63.3,
  56.5, -63.3, 52.7, -59.5, 5.6, -59.5, 5.5, -67.1, 2.5, -70.2, -1.8, -69.7, -4.3, -65.9, -13.0, -65.9, -13.0, -71.6, -6.5, -74.1, -3.8, -83.2, -13.0, -83.4,
  -11.9, -78.3, -28.9, -78.3, -27.8, -83.3, -37.1, -83.4, -34.4, -74.1, -27.8, -71.6, -27.8, -65.9, -36.9, -65.9, -39.4, -69.7, -43.7, -70.2, -46.7, -67.1,
  -46.8, -59.2, -93.8, -59.2, -97.7, -63.3, -115.6, -63.3, -116.4, -68.2, -119.8, -70.9, -126.3, -69.4, -127.9, -63.0, -125.3, -59.5, -120.5, -58.6, -120.7,
  -40.7, -116.4, -37.0, -116.1, 11.6, -95.9, 11.8, -95.9, 6.1, -89.5, 4.5, -87.8, 4.6, -87.9, 11.1, -57.3, 11.1, -57.3, -4.0, -31.4, -4.1, -31.1, 12.3, -34.3,
  12.6, -35.9, 48.5, -33.0, 51.3, -7.0, 51.3, -4.1, 47.3, 45.2, 47.3, 45.2, 52.5, 41.5, 52.5, 41.6, 58.3, 45.2, 58.3, 45.1, 71.2, 49.0, 71.2
);
const AMNH_B = P(
  12.0, 108.5, 12.4, 70.7, 45.2, 71.2, 45.2, 58.4, 41.6, 58.3, 41.6, 52.7, 45.1, 52.6, 45.1, 47.3, -4.0, 46.9, -6.9, 51.2, -33.1, 51.4, -36.0, 48.6, -34.0, 12.4,
  -30.9, 12.4, -31.0, -4.6, -57.3, -4.3, -57.3, 11.2, -87.7, 11.1, -87.8, 4.6, -96.0, 6.1, -96.0, 11.8, -115.9, 11.2, -115.7, 27.5, -109.9, 29.2, -107.2, 34.8,
  -98.4, 36.3, -96.7, 42.5, -98.2, 55.7, -93.7, 57.2, -90.4, 61.7, -80.7, 63.9, -80.8, 68.7, -87.2, 69.5, -87.7, 104.8
);
const ROSE_CUBE = rect(30.6, 89.6, 36.8, 37.4);

function buildAMNH(b: MeshBuilder) {
  const granite = '#B08F80';
  const roof = '#6E5A52';
  b.frame(AMNH_FRAME[0], AMNH_FRAME[1], 0, AMNH_FRAME[2], () => {
    b.color('#B5A99A').prism(AMNH_B, 0, 20);
    b.color(granite).prism(AMNH_A, 0, 22);
    // 77th Street front (1890–1908, Cady, Berg & See): 700 ft of pink granite
    b.box(-20.6, -48.6, 22, 199, 21.4, 4, {top: false});
    b.color(roof).hip(-20.6, -48.6, 199, 21.4, 26, 5);
    for (const x of [-121.6, 80.9]) {
      b.color(granite).cylinder(x, -64.8, 6.6, 0, 35, 12, {top: false});
      b.color(roof);
      spire(b, x, -64.8, 7, 35, 44.8, 12);
    }
    b.color(granite).box(-20.6, -64.5, 22, 52.4, 10.5, 8);
    for (const x of [-32.5, -8.4]) {
      b.color(granite).cylinder(x, -78.7, 4.7, 0, 30, 10, {top: false});
      b.color(roof);
      spire(b, x, -78.7, 5, 30, 37, 10);
    }
    b.color(granite).box(-20.4, -77, 0, 15, 9, 7);
    b.color('#3F4347').box(-20.4, -81.6, 0, 6, 0.4, 5, {top: false});
    // Central Park West range and the Theodore Roosevelt Memorial (John Russell Pope, 1936)
    b.color('#C4A898').box(70, 38.6, 22, 22, 150, 3);
    b.box(76, 38.1, 22, 25.6, 35.4, 10);
    b.color('#3F4347').box(88.9, 38.1, 5, 0.5, 10, 16.5, {top: false});
    b.color('#D9C7BA');
    columns(b, 89.7, 26.5, 89.7, 49.7, 4, 1.7, 5, 21.5);
    b.box(88.7, 38.1, 21.5, 2.6, 35.4, 3.5);
    for (const y of [26.5, 34.2, 42, 49.7]) b.box(89.7, y, 25, 1.1, 1.1, 3.4);
  });
}

function buildRoseCenter(b: MeshBuilder) {
  b.frame(AMNH_FRAME[0], AMNH_FRAME[1], 0, AMNH_FRAME[2], () => {
    const cx = 30.6;
    const cy = 89.6;
    const hx = 18.4;
    const hy = 18.7;
    const H = 28.96;
    b.color('#8A8F94').box(cx, cy, 0, 36.8, 37.4, 1.2);
    // the glass cube, drawn as its frame and mullions so that the sphere shows
    b.color('#C9D6DC');
    const edge = (a: V3, c: V3, w: number) => b.beam(a, c, w);
    for (const sx of [-1, 1]) for (const sy of [-1, 1]) edge([cx + sx * hx, cy + sy * hy, 0], [cx + sx * hx, cy + sy * hy, H], 0.6);
    for (let i = 0; i <= 6; i++) {
      const tx = -hx + (2 * hx * i) / 6;
      const ty = -hy + (2 * hy * i) / 6;
      const z = (H * i) / 6;
      for (const s of [-1, 1]) {
        if (i > 0 && i < 6) {
          edge([cx + tx, cy + s * hy, 0], [cx + tx, cy + s * hy, H], 0.18);
          edge([cx + s * hx, cy + ty, 0], [cx + s * hx, cy + ty, H], 0.18);
        }
        if (i > 0) {
          edge([cx - hx, cy + s * hy, z], [cx + hx, cy + s * hy, z], i === 6 ? 0.6 : 0.18);
          edge([cx + s * hx, cy - hy, z], [cx + s * hx, cy + hy, z], i === 6 ? 0.6 : 0.18);
        }
      }
      if (i > 0 && i < 6) edge([cx + tx, cy - hy, H], [cx + tx, cy + hy, H], 0.18);
    }
    // the Hayden Sphere, 87 ft across
    const R = 13.26;
    const zc = 1.6 + R;
    const rings: V2[][] = [];
    const zs: number[] = [];
    for (let k = 0; k <= 10; k++) {
      const phi = (-80 + 16 * k) * (Math.PI / 180);
      rings.push(circle(cx, cy, R * Math.cos(phi), 16));
      zs.push(zc + R * Math.sin(phi));
    }
    b.color('#EEF0F0').loft(rings, zs, {top: true, bottom: true});
  });
}

CIVIC.push(
  {
    id: 'american_museum_of_natural_history',
    name: 'American Museum of Natural History',
    kind: 'building',
    built: [1874.42, 1877.97],
    end: 9999,
    anchor: [-73.974, 40.7813],
    build: buildAMNH,
    replaces: [place(AMNH_A, ...AMNH_FRAME), place(AMNH_B, ...AMNH_FRAME), place(ROSE_CUBE, ...AMNH_FRAME)],
    facts: {
      Built: 'cornerstone June 2, 1874; the first building (Vaux & Mould) opened December 22, 1877 and is now enclosed by later ranges',
      Phases: '77th Street front 1890–1908 (Cady, Berg & See); Theodore Roosevelt Memorial on Central Park West 1936 (John Russell Pope); Hayden Planetarium 1935–1997; Rose Center 2000; Gilder Center 2023',
      Model: 'outlines from the two city footprints, shown at today’s extent from 1877 — the phases are not separated; range heights estimated, the corner towers taken to be the city-measured 44.8 m'
    },
    sources: [WIKI + 'American_Museum_of_Natural_History', LPC('0282'), FOOTPRINTS]
  },
  {
    id: 'rose_center_for_earth_and_space',
    name: 'Rose Center for Earth and Space (Hayden Planetarium)',
    kind: 'building',
    built: [1997.0, 2000.13],
    end: 9999,
    anchor: [-73.974, 40.7813],
    build: buildRoseCenter,
    facts: {
      Opened: 'February 19, 2000 (Polshek Partnership), on the site of the Hayden Planetarium of 1935',
      Form: 'a six-storey glass cube enclosing the 87 ft (26.5 m) Hayden Sphere',
      Model: 'cube plan from the city footprint (36.8 x 37.4 m); its height (95 ft) is from memory of published figures and was not re-verified; the glass is drawn as frame only'
    },
    sources: [WIKI + 'Rose_Center_for_Earth_and_Space', FOOTPRINTS]
  }
);

// ====================================================================== Solomon R. Guggenheim Museum
// Frame at the footprint centroid, +y at 119.2° (east, the rear); Fifth Avenue is -y, +x is
// south (88th Street). Oculus about 95 ft high; annex tower 32 ft wide and 135 ft tall
// (Wikipedia). The great rotunda is 37 m across at the top (city footprint).
const GUGG_RING = P(
  -1.2, 19.5, 18.1, 19.5, 18.1, 15.9, 29.2, 15.6, 29.3, -3.1, 27.2, -9.2, 26.7, -13.8, 25.2, -16.2, 20.3, -19.0, 17.8, -18.2, 10.0, -19.5, 4.4, -18.5, -1.6, -15.2,
  -30.8, -15.5, -31.3, 14.6, -1.2, 14.6
);
const GUGG_WRIGHT = P(
  -1.2, 19.5, 18.1, 19.5, 18.1, 15.9, 29.2, 15.6, 29.3, -3.1, 27.2, -9.2, 26.7, -13.8, 25.2, -16.2, 20.3, -19.0, 17.8, -18.2, 10.0, -19.5, 4.4, -18.5, -1.6, -15.2,
  -30.8, -15.5, -31.1, 4.85, -1.2, 4.85
);

function buildGuggenheim(b: MeshBuilder) {
  const cream = '#EDE8DC';
  b.frame(4.9, 0.4, 0, 119.2, () => {
    b.color('#5F686E').prism(GUGG_WRIGHT, 0, 4.2, {top: false});
    b.color(cream).prism(GUGG_WRIGHT, 4.2, 7.6);
    // great rotunda: the four turns of the ramp lean outwards as they rise
    const cx = 11.5;
    const cy = -1;
    for (let k = 0; k < 4; k++) {
      const z0 = 7.6 + k * 4.9;
      const r0 = 13.4 + k * 1.3;
      b.color(cream).frustum(cx, cy, r0, r0 + 1.15, z0, z0 + 4.1, 24, false);
      b.color('#59636A').cylinder(cx, cy, r0 + 0.5, z0 + 4.1, z0 + 4.9, 24, {top: false});
    }
    b.color('#D9D4C8').cap(circle(cx, cy, 18.4, 24), 26.4);
    b.color('#A9C0C8').dome(cx, cy, 9, 26.4, 2.56, 12, 3);
    // the small rotunda (the "monitor") at the north end
    b.color(cream).cylinder(-17, -5, 9.4, 7.6, 12.5, 16, {top: false});
    b.frustum(-17, -5, 9.4, 10.2, 12.5, 16.8, 16);
  });
}

function buildGuggenheimAnnex(h: number, color: string) {
  return (b: MeshBuilder) => {
    b.frame(4.9, 0.4, 0, 119.2, () => b.color(color).box(-16.2, 9.75, 0, 30, 9.7, h));
  };
}

const GUGG_SOURCES = [WIKI + 'Solomon_R._Guggenheim_Museum', LPC('1774'), FOOTPRINTS];
CIVIC.push(
  {
    id: 'guggenheim_museum',
    name: 'Solomon R. Guggenheim Museum',
    kind: 'building',
    built: [1956.6, 1959.8],
    end: 9999,
    anchor: [-73.95895, 40.783],
    build: buildGuggenheim,
    replaces: [place(GUGG_RING, 4.9, 0.4, 119.2)],
    facts: {
      Opened: 'October 21, 1959 (Frank Lloyd Wright; construction from 1956)',
      Form: 'a spiral ramp of six turns around an atrium, widening as it rises; the oculus is about 95 ft (29 m) above the floor',
      Model: 'outline from the city footprint (rotunda 37 m across at the top); the heights of the ramp bands and of the small rotunda estimated from photographs'
    },
    sources: GUGG_SOURCES
  },
  {
    id: 'guggenheim_annex_1968',
    name: 'Guggenheim Museum — annex of 1968',
    kind: 'building',
    built: [1966.5, 1968.5],
    end: 1990.0,
    anchor: [-73.95895, 40.783],
    build: buildGuggenheimAnnex(8.5, '#E3DED2'),
    facts: {Built: '1968 (William Wesley Peters, Taliesin Associated Architects), cut down to two storeys in 1966 after neighbours objected; its steel frame was reused for the tower of 1992', Model: 'plan from the city footprint of today’s tower; height (two storeys, 8.5 m) estimated'},
    sources: GUGG_SOURCES
  },
  {
    id: 'guggenheim_annex_tower',
    name: 'Guggenheim Museum — annex tower',
    kind: 'building',
    built: [1990.0, 1992.5],
    end: 9999,
    anchor: [-73.95895, 40.783],
    build: buildGuggenheimAnnex(41.15, '#DDD8C8'),
    facts: {Built: '1990–1992 (Gwathmey Siegel & Associates): a limestone slab 32 ft wide and 135 ft (41 m) tall behind the small rotunda', Model: 'plan from the city footprint; height cited (city-measured 41.6 m)'},
    sources: GUGG_SOURCES
  }
);

// ====================================================================== Madison Square Garden (IV)
// The drum above Pennsylvania Station: 128.3 m across (OpenStreetMap 3D part, centre
// (-1.1, 1.7)), top at the city-measured 44.4 m; the lower structure is the city footprint.
const MSG_RING = P(
  -8.5, 68.0, -9.4, 65.9, 11.6, 65.1, 28.9, 58.9, 44.3, 47.6, 57.1, 29.4, 66.0, 30.1, 70.7, 13.5, 62.8, 9.3, 63.2, 0.2, 72.7, -0.3, 71.0, -10.5, 99.6, -26.3, 76.2,
  -68.3, 47.7, -52.5, 40.1, -59.1, 34.7, -51.3, 26.4, -55.9, 27.3, -64.9, 10.8, -69.5, 8.0, -62.3, -16.5, -60.3, -34.9, -52.7, -48.2, -41.9, -60.5, -25.1, -68.6,
  -26.1, -74.0, 0.1, -81.7, 6.7, -47.8, 67.8, -40.1, 63.6, -12.4, 73.4
);

function buildMSG(b: MeshBuilder) {
  const cx = -1.1;
  const cy = 1.7;
  const R = 64.15;
  b.color('#8F8C86').prism(MSG_RING, 0, 11);
  b.color('#C7B69B').cylinder(cx, cy, R, 11, 40.4, 48, {top: false});
  b.color('#A99A82');
  for (let k = 0; k < 48; k++) {
    const a = ((k + 0.5) / 48) * Math.PI * 2;
    b.frame(cx + Math.cos(a) * (R + 0.1), cy + Math.sin(a) * (R + 0.1), 0, 90 - (a * 180) / Math.PI, () => b.box(0, 0, 11, 1.2, 0.8, 29.4, {top: false}));
  }
  b.color('#6F6C66').cylinder(cx, cy, R - 0.8, 40.4, 42.4, 48, {top: false});
  b.color('#C7B69B').cylinder(cx, cy, R, 42.4, 44.4, 48, {top: false});
  // cable-hung roof, slightly dished
  b.color('#9A9892').loft([circle(cx, cy, R, 48), circle(cx, cy, 10, 48)], [44.4, 42.9]);
}

CIVIC.push({
  id: 'madison_square_garden_iv',
  name: 'Madison Square Garden (the fourth)',
  kind: 'stadium',
  built: [1964.8, 1968.11],
  end: 9999,
  anchor: [-73.99345, 40.7505],
  build: buildMSG,
  replaces: [MSG_RING],
  facts: {
    Opened: 'February 11, 1968 (Charles Luckman Associates), on the site of the head house of Pennsylvania Station (1910–1963); the station continues beneath it',
    Form: 'a precast-concrete drum with a cable-suspended roof',
    Model: 'drum 128 m across from OpenStreetMap, top at the city-measured 44.4 m, lower structure from the city footprint; the level of the lower structure (11 m) and the roof dish estimated'
  },
  sources: [WIKI + 'Madison_Square_Garden', FOOTPRINTS, OSM]
});

// ====================================================================== Low Memorial Library
// Frame at the footprint centre, +y at 29° (north); the portico faces south (-y).
// Greek cross 59.5 x 60.8 m (city footprint); granite base 12 ft; dome radius 52 ft
// (Wikipedia); walls 20 m and attic 25 m (OSM parts); top of the dome city-measured 40.9 m.
const LOW_RING = P(
  17.4, 30.2, 17.4, 21.4, 21.3, 17.2, 29.7, 17.2, 29.7, -17.2, 21.3, -17.2, 17.4, -21.4, 17.4, -30.2, -17.4, -30.2, -17.4, -21.4, -21.3, -17.2, -29.7, -17.2, -29.7,
  17.2, -21.3, 17.2, -17.4, 21.4, -17.4, 30.2
);

function buildLow(b: MeshBuilder) {
  const ls = '#E0DACB';
  const walls = LOW_RING.map(([x, y]) => [x, Math.max(y, -26.6)] as V2);
  b.frame(-0.1, 0.8, 0, 29, () => {
    b.color('#BDB6A8').prism(LOW_RING, 0, 3.66);
    b.color(ls).prism(walls, 3.66, 20);
    // south portico: ten Ionic columns in front of the recessed entrance wall
    b.color('#EAE5D8');
    columns(b, -15.6, -28.9, 15.6, -28.9, 10, 1.6, 3.66, 16.4);
    b.color(ls).box(0, -28.4, 16.4, 34.8, 3.6, 3.6);
    // octagonal attic with lunettes, stepped rings, saucer dome
    b.frame(0, 0, 0, 22.5, () => b.color(ls).cylinder(0, 0, 18.5, 20, 29, 8));
    b.color('#4A555C');
    for (const s of [-1, 1]) b.box(0, s * 17.15, 22, 9, 0.4, 5, {top: false}).box(s * 17.15, 0, 22, 0.4, 9, 5, {top: false});
    b.color(ls).cylinder(0, 0, 16.9, 29, 30.5, 24).cylinder(0, 0, 16.4, 30.5, 32, 24);
    b.color('#C9C5BA').dome(0, 0, 15.85, 32, 8.9, 24, 5);
  });
}

CIVIC.push({
  id: 'low_memorial_library',
  name: 'Low Memorial Library (Columbia University)',
  kind: 'building',
  built: [1895.93, 1897.75],
  end: 9999,
  anchor: [-73.961835, 40.808223],
  build: buildLow,
  replaces: [place(LOW_RING, -0.1, 0.8, 29)],
  facts: {
    Built: 'cornerstone December 7, 1895; completed 1897 (Charles Follen McKim) — the centrepiece of the Morningside Heights campus; the university’s offices since 1934',
    Dome: 'radius 52 ft (15.8 m), the largest granite dome in the United States; granite base 12 ft high',
    Model: 'Greek-cross plan from the city footprint; wall (20 m) and attic levels from OpenStreetMap 3D parts; top of the dome at the city-measured 40.9 m; the springing of the dome (32 m) estimated'
  },
  sources: [WIKI + 'Low_Memorial_Library', LPC('0304'), FOOTPRINTS, OSM]
});

// ====================================================================== Brooklyn Borough Hall
// Frame at the footprint centroid, +y at 184° (south, the rear); the portico faces north
// (-y) to the plaza. Top of the cupola figure at the city-measured 41.3 m.
const BKBH_RING = P(-9.0, -18.6, -9.0, -14.1, -24.4, -14.0, -24.4, 17.1, -7.3, 17.1, -7.4, 13.6, 8.5, 13.6, 8.4, 16.8, 24.5, 16.9, 24.5, -14.3, 9.1, -14.3, 9.1, -18.5);

function buildBrooklynBoroughHall(b: MeshBuilder) {
  const marble = '#E3DFD5';
  const body = P(-24.4, -14.1, -24.4, 17.1, -7.3, 17.1, -7.4, 13.6, 8.5, 13.6, 8.4, 16.8, 24.5, 16.9, 24.5, -14.2);
  b.frame(0.2, -3.7, 0, 184, () => {
    b.color(marble).prism(body, 0, 16.5, {top: false});
    b.color('#8C9794').cap(body, 16.5).hip(0, -0.3, 48.9, 27.8, 16.5, 2.5);
    // portico: six Ionic columns at the head of the great stair, pediment
    b.color('#D4D0C5').box(0.05, -16.4, 0, 18.1, 4.4, 4.5);
    b.color(marble);
    columns(b, -7.9, -17.6, 8.0, -17.6, 6, 1.2, 4.5, 14.2);
    b.box(0.05, -16.4, 14.2, 18.1, 4.4, 1.8).gable(0.05, -16.4, 18.1, 4.4, 16, 3, true);
    // cast-iron cupola of 1898 with the figure of Justice
    b.color('#D9D5CA').box(0, -1, 19, 9, 9, 3.5).cylinder(0, -1, 3.5, 22.5, 29.5, 8, {top: false});
    for (let k = 0; k < 8; k++) {
      const a = ((k + 0.5) / 8) * Math.PI * 2;
      b.cylinder(Math.cos(a) * 4.1, -1 + Math.sin(a) * 4.1, 0.35, 22.5, 29.5, 5, {top: false});
    }
    b.cylinder(0, -1, 4.7, 29.5, 30.5, 8);
    b.color('#9AA8A2').dome(0, -1, 3.9, 30.5, 4.5, 8, 4);
    b.color('#D9D5CA').cylinder(0, -1, 1.2, 35, 37.8, 8);
    b.color('#B8A04A').loft([circle(0, -1, 0.6, 6), circle(0, -1, 0.3, 6)], [37.8, 41.3]);
  });
}

CIVIC.push({
  id: 'brooklyn_borough_hall',
  name: 'Brooklyn Borough Hall (Brooklyn City Hall)',
  kind: 'building',
  built: [1846.0, 1848.5],
  end: 9999,
  anchor: [-73.9903, 40.6928],
  build: buildBrooklynBoroughHall,
  replaces: [place(BKBH_RING, 0.2, -3.7, 184)],
  facts: {
    Built: '1846–1848 as the City Hall of Brooklyn (Gamaliel King); Borough Hall since consolidation in 1898',
    Cupola: 'the wooden cupola burned in 1895; the cast-iron cupola dates from 1898 (shown here from 1848)',
    Model: 'plan from the city footprint; top of the figure of Justice at the city-measured 41.3 m; wall, portico and cupola-stage heights estimated from photographs'
  },
  sources: [WIKI + 'Brooklyn_Borough_Hall', LPC('0147'), FOOTPRINTS]
});

// ====================================================================== Unisphere
// 140 ft high, 120 ft in diameter, on a 20 ft base; pool 310 ft in diameter (Wikipedia).
const UNISPHERE_LAND = [
  '......XXXX..............',
  '.XXXXXXXXX..XXXXXXXXXXXX',
  '...XXXXX...XXXXXXXXXXXX.',
  '....XXX....XXXXXXXXXXX..',
  '....XX.....XXXXXXXXX....',
  '......XX...XXXX..XXXX...',
  '.......XXX...XX....XXX..',
  '.......XX....XXX...XXX..',
  '.......X.....X.......X.X',
  '.......X................',
  'XXXXXXXXXXXXXXXXXXXXXXXX'
];

function buildUnisphere(b: MeshBuilder) {
  const R = 18.29;
  const zc = 6.1 + R;
  const tilt = (23.5 * Math.PI) / 180;
  const ct = Math.cos(tilt);
  const st = Math.sin(tilt);
  const pt = (lat: number, lon: number, r = R): V3 => {
    const p = (lat * Math.PI) / 180;
    const l = (lon * Math.PI) / 180;
    const x = r * Math.cos(p) * Math.cos(l);
    const y = r * Math.cos(p) * Math.sin(l);
    const z = r * Math.sin(p);
    return [x, y * ct - z * st, zc + y * st + z * ct];
  };
  // reflecting pool and the three-pronged base
  b.color('#7FA7B5').cylinder(0, 0, 47.24, 0, 0.15, 48);
  b.color('#9FA5A8');
  for (let k = 0; k < 3; k++) {
    const a = ((90 + k * 120) * Math.PI) / 180;
    b.beam([Math.cos(a) * 7.5, Math.sin(a) * 7.5, 0.15], [Math.cos(a) * 2.5, Math.sin(a) * 2.5, 7.6], 1.7);
  }
  // meridians and parallels of stainless steel
  b.color('#C5CBCF');
  for (let lon = 0; lon < 360; lon += 30) {
    const line: V3[] = [];
    for (let lat = -90; lat <= 90; lat += 15) line.push(pt(lat, lon));
    b.polyline(line, 0.3);
  }
  for (const lat of [-60, -30, 0, 30, 60]) {
    const line: V3[] = [];
    for (let lon = 0; lon <= 360; lon += 15) line.push(pt(lat, lon));
    b.polyline(line, 0.3);
  }
  // land masses (a coarse 15° mask)
  b.color('#A9B2B8');
  UNISPHERE_LAND.forEach((row, i) => {
    const lat1 = 90 - i * 15;
    for (let j = 0; j < 24; j++) {
      if (row[j] !== 'X') continue;
      const lon0 = -180 + j * 15;
      b.quad(pt(lat1, lon0, R + 0.1), pt(lat1, lon0 + 15, R + 0.1), pt(lat1 - 15, lon0 + 15, R + 0.1), pt(lat1 - 15, lon0, R + 0.1));
    }
  });
  // three orbit rings (Gagarin, Glenn, Telstar)
  b.color('#D5DADD');
  for (const [inc, node, r] of [
    [35, 0, 1.2],
    [-50, 70, 1.28],
    [70, 140, 1.36]
  ]) {
    const line: V3[] = [];
    const ci = Math.cos((inc * Math.PI) / 180);
    const si = Math.sin((inc * Math.PI) / 180);
    const cn = Math.cos((node * Math.PI) / 180);
    const sn = Math.sin((node * Math.PI) / 180);
    for (let u = 0; u <= 360; u += 10) {
      const x = R * r * Math.cos((u * Math.PI) / 180);
      const y0 = R * r * Math.sin((u * Math.PI) / 180);
      const y = y0 * ci;
      const z = y0 * si * 0.72;
      line.push([x * cn - y * sn, x * sn + y * cn, zc + z]);
    }
    b.polyline(line, 0.22);
  }
}

CIVIC.push({
  id: 'unisphere',
  name: 'Unisphere',
  kind: 'monument',
  built: [1963.2, 1964.3],
  end: 9999,
  anchor: [-73.84505, 40.7464],
  build: buildUnisphere,
  facts: {
    Built: '1963–1964 by U.S. Steel for the 1964–65 World’s Fair (Gilmore D. Clarke), on the foundation of the Perisphere of 1939',
    Dimensions: '140 ft (43 m) high; the globe 120 ft (37 m) in diameter on a 20 ft base; reflecting pool 310 ft across',
    Model: 'built to the cited dimensions; the land masses are a coarse 15° mask and the facing of the globe and its orbit rings are not surveyed'
  },
  sources: [WIKI + 'Unisphere', LPC('1925')]
});

// ====================================================================== New York State Pavilion
// Tent of Tomorrow: ellipse 76 x 98.7 m over the columns (city footprint; "250 by 350 ft"),
// long axis 157.4°, columns to the city-measured 29.6 m. Observation towers: west 226 ft,
// north 150 ft, south 60 ft (Wikipedia).
function buildNYSPavilion(b: MeshBuilder) {
  const concrete = '#CFCBC0';
  b.frame(-4.2, -41.4, 0, 157.4, () => {
    const ell = (s: number, n: number): V2[] => circle(0, 0, 1, n, 36.2 * s, 47.5 * s);
    b.color('#B9B3A5').cap(ell(0.96, 48), 0.3);
    b.color(concrete);
    for (const [x, y] of ell(1, 16)) b.cylinder(x, y, 1.83, 0, 29.6, 10);
    // steel compression ring on the columns, cable roof to a central tension ring
    b.color('#B8452E');
    const outer = ell(1, 48);
    const inner = ell(0.22, 48);
    for (let i = 0; i < 48; i++) {
      const j = (i + 1) % 48;
      b.beam([outer[i][0], outer[i][1], 27.6], [outer[j][0], outer[j][1], 27.6], 1.6, 2.2);
      b.beam([inner[i][0], inner[i][1], 22], [inner[j][0], inner[j][1], 22], 0.8, 1.2);
    }
    b.color('#8E9396');
    for (let i = 0; i < 48; i++) b.beam([outer[i][0], outer[i][1], 28.4], [inner[i][0], inner[i][1], 22.4], 0.22);
  });
  // three observation towers
  const tc: V2 = [-50.4, 8.2];
  const towers: [number, number][] = [
    [180, 68.88],
    [60, 45.72],
    [300, 18.29]
  ];
  for (const [ang, h] of towers) {
    const x = tc[0] + Math.cos((ang * Math.PI) / 180) * 7.4;
    const y = tc[1] + Math.sin((ang * Math.PI) / 180) * 7.4;
    b.color(concrete).cylinder(x, y, 1.9, 0, h - 0.6, 12, {top: false});
    b.color('#D8D4C8').cylinder(x, y, 8.2, h - 5, h - 3.9, 20).cylinder(x, y, 8.2, h - 0.6, h, 20);
  }
  // Theaterama (now the Queens Theatre), a concrete drum with later additions
  b.color(concrete).prism(NYSP_THEATERAMA, 0, 7);
  b.cylinder(-7, 31.5, 15.2, 7, 17.7, 24);
}
const NYSP_THEATERAMA = P(
  7.8, 46.3, 3.1, 38.3, 8.1, 30.6, 8.0, 21.5, 3.5, 14.8, -3.7, 11.1, -13.2, 12.2, -21.9, 22.1, -28.1, 22.0, -25.6, 31.9, -27.1, 33.2, -30.7, 26.8, -40.9, 24.8, -40.2,
  27.5, -45.8, 34.8, -43.8, 42.3, -38.3, 46.0, -37.1, 42.9, -28.6, 39.4, -27.1, 34.8, -24.8, 36.3, -20.3, 34.4, -19.1, 35.9, -24.2, 40.8, -13.3, 47.0, -15.4, 52.6,
  -11.8, 53.3, 3.5, 51.7
);

CIVIC.push({
  id: 'new_york_state_pavilion',
  name: 'New York State Pavilion (Tent of Tomorrow and observation towers)',
  kind: 'monument',
  built: [1962.8, 1964.3],
  end: 9999,
  anchor: [-73.8443, 40.7439],
  build: buildNYSPavilion,
  replaces: [place(circle(0, 0, 1, 24, 41, 52.5), -4.2, -41.4, 157.4), circle(-50.4, 8.2, 17, 16), NYSP_THEATERAMA],
  facts: {
    Built: '1962–1964 for the World’s Fair (Philip Johnson and Richard Foster; Lev Zetlin, engineer)',
    'Tent of Tomorrow': 'an ellipse of sixteen concrete columns, 250 by 350 ft, that carried a cable roof of coloured panels (removed in the 1970s) over a terrazzo road map of New York State',
    Towers: 'three observation towers: 226 ft (69 m, west), 150 ft (north) and 60 ft (south)',
    Model: 'tent and tower positions from the city footprints, columns to the city-measured 29.6 m; the exact spacing of the three towers within their footprint, the size of their platforms and the roof geometry are estimates; the Theaterama drum is city-measured (17.7 m)'
  },
  sources: [WIKI + 'New_York_State_Pavilion', FOOTPRINTS]
});

// ====================================================================== Lincoln Center
// Metropolitan Opera House: frame on the 52.9 x 137 m body (OSM part), +y at 298.8° (west,
// the rear); the plaza front is -y. "Five concrete arches ... towering 96 feet above the
// plaza" (Wikipedia); body 25 m (OSM), stage house city-measured 37.7 m.
const METOPERA_RING = P(27.1, 67.4, 26.5, -69.1, -25.0, -68.6, -24.7, 9.2, -34.6, 9.3, -34.4, 59.7, -25.8, 59.6, -25.7, 67.8);
const TRAVERTINE = '#E6DFD0';

function buildMetOpera(b: MeshBuilder) {
  b.frame(0.2, -0.2, 0, 298.8, () => {
    b.color(TRAVERTINE).prism(P(27.1, 67.4, 26.6, -62, -25.0, -62, -24.7, 9.2, -34.6, 9.3, -34.4, 59.7, -25.8, 59.6, -25.7, 67.8), 0, 25);
    b.color('#D8D1C2').box(-0.2, 28.8, 25, 32.8, 43.4, 12.7);
    b.color(TRAVERTINE).box(0.75, -59.2, 25, 51.5, 5.6, 4.26);
    for (let k = 0; k < 5; k++) b.frame(0.75 + (k - 2) * 10.3, -65.6, 0, 0, () => archWall(b, 10.3, 7, 4.35, 24.2, 29.26));
    b.color('#6E6558').box(0.75, -62.3, 0, 51.5, 0.5, 28.5, {top: false});
  });
}

// David Geffen Hall (Philharmonic Hall): 59.0 x 78.7 m (city footprint), colonnade 24 m and
// auditorium 27.4 m (OSM parts, city-measured); frame +y at 29.2° (north), plaza front -y.
function buildGeffenHall(b: MeshBuilder) {
  b.frame(-1.6, -8.1, 0, 29.2, () => {
    b.color('#CFC8B8').box(0, 0, 0, 59, 78.7, 1);
    b.color('#55636B').box(0, 0, 1, 50.6, 70.3, 20, {top: false});
    // peristyle of 44 tapered travertine columns
    b.color(TRAVERTINE);
    const col = (x: number, y: number) => b.loft([rect(x, y, 1.1, 1.1), rect(x, y, 1.7, 1.7), rect(x, y, 1.1, 1.1)], [1, 11, 21], {top: false});
    for (let i = 0; i < 10; i++) {
      const x = -28.3 + (56.6 * i) / 9;
      col(x, -38.1);
      col(x, 38.1);
    }
    for (let i = 1; i <= 12; i++) {
      const y = -38.1 + (76.2 * i) / 13;
      col(-28.3, y);
      col(28.3, y);
    }
    b.box(0, 0, 21, 59, 78.7, 3);
    b.color('#D8D1C2').box(0.3, 6.2, 24, 40.8, 54.5, 3.4);
  });
}

// David H. Koch Theater (New York State Theater): 59.1 x 79.3 m (city footprint), 24 m and
// 27 m (OSM parts), stage house city-measured 31.7 m; frame +y at 209.1° (south), plaza front -y.
function buildKochTheater(b: MeshBuilder) {
  b.frame(-14.3, -10.9, 0, 209.1, () => {
    b.color('#CFC8B8').box(0, 0, 0, 59.1, 79.3, 1);
    b.color(TRAVERTINE).box(0, 2.5, 1, 59.1, 74.3, 23);
    // plaza front: four pairs of travertine piers before the glass wall of the promenade
    b.color('#55636B').box(0, -34.9, 1, 50, 0.5, 20, {top: false});
    b.color(TRAVERTINE);
    for (const x of [-25.5, -8.5, 8.5, 25.5]) for (const d of [-1.5, 1.5]) b.box(x + d, -38.6, 1, 1.1, 1.6, 20);
    b.box(0, -37.15, 21, 59.1, 5, 3);
    b.color('#D8D1C2').box(0, 4.6, 24, 42.3, 58.6, 3).box(0, 24, 27, 42.3, 20, 4.7);
  });
}

const LC_SOURCES = [WIKI + 'Lincoln_Center', FOOTPRINTS, OSM];
CIVIC.push(
  {
    id: 'lincoln_center_geffen_hall',
    name: 'David Geffen Hall (Philharmonic Hall), Lincoln Center',
    kind: 'building',
    built: [1959.37, 1962.73],
    end: 9999,
    anchor: [-73.983, 40.7729],
    build: buildGeffenHall,
    replaces: [place(rect(0, 0, 60, 79.7), -1.6, -8.1, 29.2)],
    facts: {
      Opened: 'September 23, 1962 as Philharmonic Hall (Max Abramovitz) — the first building of Lincoln Center; ground broken May 14, 1959',
      Form: 'a glass box within a peristyle of 44 tapered travertine columns',
      Model: 'plan from the city footprint; colonnade 24 m and auditorium 27.4 m from OpenStreetMap and the city-measured roof; column spacing estimated'
    },
    sources: [WIKI + 'David_Geffen_Hall', ...LC_SOURCES]
  },
  {
    id: 'lincoln_center_koch_theater',
    name: 'David H. Koch Theater (New York State Theater), Lincoln Center',
    kind: 'building',
    built: [1961.9, 1964.31],
    end: 9999,
    anchor: [-73.9836, 40.7719],
    build: buildKochTheater,
    replaces: [place(rect(0, 0, 60.1, 80.3), -14.3, -10.9, 209.1)],
    facts: {
      Opened: 'April 23, 1964 as the New York State Theater (Philip Johnson), built for the World’s Fair',
      Model: 'plan from the city footprint; 24 m and 27 m levels from OpenStreetMap, stage house at the city-measured 31.7 m; the front piers estimated from photographs'
    },
    sources: [WIKI + 'David_H._Koch_Theater', ...LC_SOURCES]
  },
  {
    id: 'lincoln_center_metropolitan_opera',
    name: 'Metropolitan Opera House, Lincoln Center',
    kind: 'building',
    built: [1963.0, 1966.71],
    end: 9999,
    anchor: [-73.984696, 40.772855],
    build: buildMetOpera,
    replaces: [place(METOPERA_RING, 0.2, -0.2, 298.8)],
    facts: {
      Opened: 'September 16, 1966 (Wallace K. Harrison), replacing the opera house of 1883 on Broadway at 39th Street',
      Front: 'five concrete arches and a glass-and-bronze wall, 96 ft (29 m) above the plaza',
      Model: 'plan from the city footprint; body 25 m from OpenStreetMap, stage house at the city-measured 37.7 m; the springing of the arches estimated'
    },
    sources: [WIKI + 'Metropolitan_Opera_House_(Lincoln_Center)', ...LC_SOURCES]
  }
);

// ====================================================================== Gould Memorial Library and the Hall of Fame
// Frame at the library's footprint centroid, +y at 294.3° (west, the rear, above the
// Harlem River); the portico faces the campus (-y). The dome is centred (0, 6.5); its top
// is the city-measured 29.9 m. Hall of Fame colonnade 630 ft long (Wikipedia): an arc of
// radius 25–30 m about the dome centre with straight links (city footprint of its south half).
const GOULD_FRAME: [number, number, number] = [16.0, 14.3, 294.3];
const GOULD_RING = P(
  16.7, 15.9, 16.7, -2.9, 12.5, -2.9, 9.4, -5.9, 8.8, -28.3, -8.6, -28.2, -8.6, -10.6, -9.4, -10.6, -9.4, -5.8, -12.3, -2.9, -16.7, -2.9, -16.7, 15.9, -11.4, 16.3,
  -9.4, 18.9, -9.4, 23.3, 9.5, 23.3, 9.5, 18.8, 11.5, 16.3
);
const HOF_SOUTH_RING = P(
  0.2, 31.8, -10.2, 29.6, -19.1, 22.9, -24.2, 13.1, -24.2, 3.6, -43.9, 3.6, -43.9, -1.6, -41.5, -1.6, -41.5, -5.7, -31.5, -5.7, -31.5, -23.3, -60.3, -23.2, -60.3,
  -5.7, -50.7, -5.7, -50.7, -1.6, -48.4, -1.6, -48.9, 9.4, -30.1, 9.0, -26.1, 21.0, -18.3, 30.3, -10.0, 34.8, -2.0, 36.4, 0.4, 36.5
);

function buildGould(b: MeshBuilder) {
  const brick = '#D8C690';
  const copper = '#8FAE9E';
  const walls = GOULD_RING.map(([x, y]) => [x, Math.max(y, -25.4)] as V2);
  b.frame(GOULD_FRAME[0], GOULD_FRAME[1], 0, GOULD_FRAME[2], () => {
    b.color('#CFC7B4').prism(GOULD_RING, 0, 2.4);
    b.color(brick).prism(walls, 2.4, 14);
    b.color(copper).gable(0.1, -14, 17.4, 22.8, 14, 3, true).gable(0, 6.5, 33.4, 18.8, 14, 3, false);
    // rotunda drum and dome
    b.color(brick).cylinder(0, 6.5, 12.6, 14, 20, 20, {top: false});
    b.color(copper).dome(0, 6.5, 12.6, 20, 9.9, 20, 5);
    // Corinthian portico
    b.color('#E6DFCB');
    columns(b, -7, -27.3, 7.2, -27.3, 6, 1.1, 2.4, 11.6);
    b.box(0.1, -26.85, 11.6, 17.4, 2.9, 2.4).gable(0.1, -26.85, 17.4, 2.9, 14, 3.2, true);
  });
}

function buildHallOfFame(b: MeshBuilder) {
  const stone = '#D9D2C0';
  b.frame(GOULD_FRAME[0], GOULD_FRAME[1], 0, GOULD_FRAME[2], () => {
    const arc = (r: number): V2[] => {
      const pts: V2[] = [];
      for (let i = 0; i <= 28; i++) {
        const a = ((187 - (194 * i) / 28) * Math.PI) / 180;
        pts.push([r * Math.cos(a), 6.5 + r * Math.sin(a)]);
      }
      return pts;
    };
    const outer = arc(30);
    const inner = arc(25);
    const ring = [...outer, ...inner.slice().reverse()];
    b.color(stone).prism(ring, 0, 1.2).prism(ring, 5.2, 6.2, {bottom: true});
    for (const [x, y] of [...arc(29.5), ...arc(25.5)]) b.cylinder(x, y, 0.32, 1.2, 5.2, 5, {top: false});
    // straight links to the end halls
    for (const s of [-1, 1]) {
      b.box(s * 36.5, 6.5, 0, 24.7, 5.8, 1.2).box(s * 36.5, 6.5, 5.2, 24.7, 5.8, 1);
      for (let x = 25.5; x <= 48; x += 3.2) for (const y of [4.1, 8.9]) b.cylinder(s * x, y, 0.32, 1.2, 5.2, 5, {top: false});
    }
    // the halls at either end share the colonnade's two city footprints: plain blocks
    b.color('#D8C690').box(-45.9, -14.5, 0, 28.8, 17.6, 19.5).box(45.9, -14.5, 0, 28.8, 17.6, 20.7);
  });
}

CIVIC.push(
  {
    id: 'gould_memorial_library',
    name: 'Gould Memorial Library (Bronx Community College, formerly New York University)',
    kind: 'building',
    built: [1895.8, 1899.5],
    end: 9999,
    anchor: [-73.9141, 40.8586],
    build: buildGould,
    replaces: [place(GOULD_RING, ...GOULD_FRAME)],
    facts: {
      Built: '1895–1899 (Stanford White, of McKim, Mead & White) for New York University’s University Heights campus',
      'Reading room': 'a rotunda ringed by sixteen Connemara-marble columns, 54 ft 3 in across inside the colonnade',
      Model: 'plan from the city footprint; top of the dome at the city-measured 29.9 m; wall and drum levels and the size of the dome above the roof (25 m across) estimated from photographs'
    },
    sources: [WIKI + 'Gould_Memorial_Library', LPC('0112'), FOOTPRINTS]
  },
  {
    id: 'hall_of_fame_for_great_americans',
    name: 'Hall of Fame for Great Americans (colonnade)',
    kind: 'monument',
    built: [1900.3, 1901.41],
    end: 9999,
    anchor: [-73.9141, 40.8586],
    build: buildHallOfFame,
    replaces: [place(HOF_SOUTH_RING, ...GOULD_FRAME), place(rect(-38.1, -1.8, 8, 8), ...GOULD_FRAME), place(rect(43.4, -3.2, 8, 8), ...GOULD_FRAME)],
    facts: {
      Dedicated: 'May 30, 1901 (Stanford White): an open-air colonnade 630 ft (192 m) long, holding bronze busts, curving behind the library above the Harlem River',
      Model: 'the south half is from the city footprint (arc of radius 25–30 m about the dome); the north half is drawn as its mirror image; the height of the colonnade estimated; the halls at its two ends are plain blocks at the city-measured 19.5 m and 20.7 m'
    },
    sources: [WIKI + 'Hall_of_Fame_for_Great_Americans', WIKI + 'Gould_Memorial_Library', LPC('0113'), FOOTPRINTS]
  }
);

// ====================================================================== Brooklyn Museum
// Frame at the footprint centroid, +y at 195° (south, the rear); the Eastern Parkway
// front is -y, centred on x = 29. The front is 510 ft wide with 12 ft cornice figures
// (Wikipedia). Only about a quarter of McKim, Mead & White's plan was built.
const BKM_RING = P(
  -45.1, 35.5, -47.1, 35.5, -47.1, 48.0, 18.0, 48.0, 18.0, 28.6, 14.8, 28.6, 14.8, 21.9, 17.6, 21.9, 17.5, -7.0, 25.0, -7.0, 25.0, -1.4, 32.4, -1.4, 32.4, -9.9, 40.2,
  -9.9, 40.2, -9.0, 52.5, -9.7, 52.5, -12.2, 55.1, -12.2, 55.1, -17.5, 81.2, -17.5, 81.2, -16.7, 83.1, -16.0, 83.2, -11.4, 89.6, -11.4, 89.6, -9.5, 91.9, -9.5, 91.9,
  -11.4, 103.0, -11.4, 103.7, -32.4, 87.7, -32.4, 87.7, -31.4, 82.5, -30.9, 44.5, -31.2, 44.5, -32.3, 43.0, -32.3, 43.0, -44.2, 15.2, -44.2, 15.2, -31.2, -25.2,
  -30.5, -30.2, -30.8, -30.2, -31.5, -46.2, -31.5, -46.2, -15.6, -45.0, -15.6, -45.0, -11.1, -61.9, -11.2, -62.2, 30.1, -45.1, 29.7
);

function buildBrooklynMuseum(b: MeshBuilder) {
  const ls = '#D9D3C4';
  const walls = BKM_RING.map(([x, y]) => [x, Math.max(y, -38.6)] as V2);
  const cx = 29.1;
  b.frame(0.6, 0.7, 0, 195, () => {
    b.color(ls).prism(walls, 0, 24, {top: false});
    b.color('#8E9692').cap(walls, 24);
    // central pavilion: six Ionic columns and a pediment; saucer dome behind
    b.color('#CFC9BB').box(cx, -41.4, 0, 27.8, 5.6, 6);
    b.color('#E6E1D4');
    columns(b, cx - 11.6, -42.9, cx + 11.6, -42.9, 6, 1.7, 6, 20);
    b.color(ls).box(cx, -41.4, 20, 27.8, 5.6, 3).gable(cx, -41.4, 27.8, 5.6, 23, 4.5, true);
    b.box(cx, -22, 24, 24, 19, 4);
    b.color('#9FB0AA').dome(cx, -22, 9.5, 28, 6, 16, 4);
    // 12 ft figures on the cornice of the wings
    b.color('#E6E1D4');
    for (let i = 0; i < 10; i++) {
      b.box(-43 + i * 6.1, -30.4, 24, 1.1, 0.9, 3.66);
      b.box(46.5 + i * 6.1, -30.4, 24, 1.1, 0.9, 3.66);
    }
  });
}

CIVIC.push({
  id: 'brooklyn_museum',
  name: 'Brooklyn Museum (Brooklyn Institute of Arts and Sciences)',
  kind: 'building',
  built: [1895.7, 1897.75],
  end: 9999,
  anchor: [-73.963496, 40.670903],
  build: buildBrooklynMuseum,
  replaces: [place(BKM_RING, 0.6, 0.7, 195)],
  facts: {
    Built: 'first section opened October 1897 (McKim, Mead & White); central pavilion 1905, east wing 1907, rear additions 1911–1927 — about a quarter of the intended building; the great stair was removed in 1934–35 and the glass entrance pavilion added in 2004',
    Front: '510 ft (155 m) on Eastern Parkway; 12 ft cornice figures',
    Model: 'outline from the city footprint, shown at today’s extent from 1897; wall (24 m), pediment and dome heights estimated from photographs — the city-measured roof height of 50.0 m for this footprint was not understood and is not matched'
  },
  sources: [WIKI + 'Brooklyn_Museum', LPC('0155'), FOOTPRINTS]
});

// ====================================================================== Brooklyn Academy of Music
// Frame at the footprint centroid, +y at 171.4° (south); the Lafayette Avenue front is -y.
// City-measured roof 21.7 m.
const BAM_RING = P(-27.7, -29.9, -27.7, 30.6, -5.5, 30.6, -5.5, -11.0, -0.7, -11.0, -0.7, 30.6, 28.4, 30.6, 26.4, -29.9);

function buildBAM(b: MeshBuilder) {
  b.frame(17.0, 2.6, 0, 171.4, () => {
    b.color('#D8C9A8').prism(BAM_RING, 0, 20.2);
    b.box(-0.6, -29.2, 20.2, 54.4, 1.4, 1.5);
    // Lafayette Avenue front: five entrances under five tall arched windows
    b.color('#3F4A52');
    for (let k = -2; k <= 2; k++) {
      b.box(-0.6 + k * 8.6, -30.05, 0, 4.6, 0.4, 4.6, {top: false});
      b.box(-0.6 + k * 8.6, -30.05, 6.8, 5, 0.4, 9.5, {top: false});
    }
    b.color('#C9B58F').box(-0.6, -30.9, 5, 44, 2.2, 0.5);
  });
}

CIVIC.push({
  id: 'brooklyn_academy_of_music',
  name: 'Brooklyn Academy of Music (Peter Jay Sharp Building)',
  kind: 'building',
  built: [1906.5, 1908.87],
  end: 9999,
  anchor: [-73.9779, 40.68645],
  build: buildBAM,
  replaces: [place(BAM_RING, 17.0, 2.6, 171.4)],
  facts: {
    Opened: 'November 1908 (Herts & Tallant), after the academy of 1861 on Montague Street burned in 1903',
    Model: 'plan from the city footprint, parapet at the city-measured 21.7 m; the front (five entrances under five arched windows) is drawn from photographs, its levels estimated'
  },
  sources: [WIKI + 'Brooklyn_Academy_of_Music', FOOTPRINTS]
});

// ====================================================================== stadiums
/** Distance from c along the direction `ang` (radians, from +x) to the farthest crossing of a closed ring. */
function rayHit(ring: V2[], c: V2, ang: number): number {
  const dx = Math.cos(ang);
  const dy = Math.sin(ang);
  let best = 0;
  for (let i = 0; i < ring.length; i++) {
    const a = ring[i];
    const q = ring[(i + 1) % ring.length];
    const ex = q[0] - a[0];
    const ey = q[1] - a[1];
    const den = dx * ey - dy * ex;
    if (Math.abs(den) < 1e-9) continue;
    const t = ((a[0] - c[0]) * ey - (a[1] - c[1]) * ex) / den;
    const u = ((a[0] - c[0]) * dy - (a[1] - c[1]) * dx) / den;
    if (t > 0 && u >= 0 && u <= 1) best = Math.max(best, t);
  }
  return best;
}

/**
 * Seating bowl between a field outline and the stadium's outer wall, sampled radially about
 * c: seats rise from the field edge to `rim(ang)` at 80 % of the depth, a deck runs to the
 * outer wall. Returns the inner edge of the deck (for friezes and roofs).
 */
function bowl(
  b: MeshBuilder,
  field: V2[],
  outer: V2[],
  c: V2,
  rim: (ang: number) => number,
  col: {seats: string; wall: string; deck: string},
  n = 96,
  margin = 3
): V3[] {
  const lo: V3[] = [];
  const mid: V3[] = [];
  const top: V3[] = [];
  const path: V2[] = [];
  const zs: number[] = [];
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2;
    const rOut = rayHit(outer, c, a);
    const rIn = Math.min(rayHit(field, c, a) + margin, rOut - 1);
    const h = rim(a);
    const rMid = rIn + (rOut - rIn) * 0.8;
    const p = (r: number): V2 => [c[0] + Math.cos(a) * r, c[1] + Math.sin(a) * r];
    lo.push([...p(rIn), 1.5]);
    mid.push([...p(rMid), h]);
    top.push([...p(rOut), h]);
    path.push(p(rOut));
    zs.push(h);
  }
  b.color(col.wall).ribbon(
    lo.map(v => [v[0], v[1], 0] as V3),
    lo,
    true
  );
  b.color(col.seats).ribbon(lo, mid, true);
  b.color(col.deck).ribbon(mid, top, true);
  b.color(col.wall).wallProfile(path, 0, zs, true);
  return mid;
}

/** Rim height: `hi` within `a0` degrees of the direction `home` (radians), easing to `lo` beyond `a1` degrees. */
function rimProfile(home: number, hi: number, lo: number, a0: number, a1: number) {
  return (ang: number) => {
    let d = Math.abs(((ang - home) * 180) / Math.PI) % 360;
    if (d > 180) d = 360 - d;
    const t = Math.min(1, Math.max(0, (d - a0) / (a1 - a0)));
    const s = t * t * (3 - 2 * t);
    return hi + (lo - hi) * s;
  };
}

// ---------------------------------------------------------------------- Yankee Stadium (2009)
// Outer wall: city footprint; field and infield: OpenStreetMap pitch polygons (home plate
// near (-50, -15), centre field bearing ~75°). Fences 318 / 399 / 408 / 385 / 314 ft
// (Wikipedia). Rim behind the plate at the city-measured 36.6 m.
const YANKEE_RING = P(
  -3.7, 138.8, 100.7, 92.1, 92.1, 72.2, 116.2, 61.4, 112.1, 52.0, 119.1, 30.7, 125.7, 27.6, 57.0, -128.1, 28.2, -134.2, 7.0, -132.6, -98.7, -82.4, -127.1, -46.4,
  -131.7, -47.5, -138.0, -23.1, -130.3, -21.1, -129.7, -3.6, -119.1, 19.6, -39.3, 127.2
);
const YANKEE_FIELD = P(4, 64, -5, 50, -30, 28, -56, -7, -57, -16, -51, -24, -12, -41, 21, -48, 34, -56, 64, -8, 68, 2, 67, 18, 61, 34, 51, 45, 19, 64);

function buildYankeeStadium(b: MeshBuilder) {
  const c: V2 = [5, 5];
  const home = Math.atan2(-15 - c[1], -50 - c[0]);
  b.color('#8D8A82').cap(YANKEE_RING, 0.2);
  b.color('#4F8A3C').cap(YANKEE_FIELD, 0.5);
  b.color('#B58A5E').cap(P(-44, -9, -42, -15, -26, -25, -20, -21, -12, -6, -13, -2, -27, 6, -34, 7), 0.6);
  const rim = rimProfile(home, 36.6, 13, 95, 125);
  const mid = bowl(b, YANKEE_FIELD, YANKEE_RING, c, rim, {seats: '#1F3A64', wall: '#D6CDB8', deck: '#9A9C9E'});
  // the frieze along the front of the upper-deck roof
  b.color('#F2F1EC');
  for (let i = 0; i < mid.length; i++) {
    const p = mid[i];
    const q = mid[(i + 1) % mid.length];
    if (p[2] > 34 && q[2] > 34) b.quad([p[0], p[1], p[2]], [q[0], q[1], q[2]], [q[0], q[1], q[2] + 3], [p[0], p[1], p[2] + 3]);
  }
  // centre-field scoreboard
  b.frame(72, 26, 0, 75, () => b.color('#2B2F36').box(0, 0, 13, 33, 3, 17));
}

CIVIC.push({
  id: 'yankee_stadium_2009',
  name: 'Yankee Stadium (2009)',
  kind: 'stadium',
  built: [2006.63, 2009.25],
  end: 9999,
  anchor: [-73.9264, 40.8296],
  build: buildYankeeStadium,
  replaces: [YANKEE_RING],
  facts: {
    Opened: 'April 2009 (Populous; ground broken August 16, 2006), across 161st Street from the stadium of 1923, demolished 2009–2010',
    Field: 'fences 318 ft (left), 399, 408 (centre), 385 and 314 ft (right)',
    Model: 'outer wall from the city footprint; field and infield from OpenStreetMap; the upper deck behind the plate at the city-measured 36.6 m, with the frieze above it; outfield stand heights, the slope of the seating and the scoreboard estimated'
  },
  sources: [WIKI + 'Yankee_Stadium', FOOTPRINTS, OSM]
});

// ---------------------------------------------------------------------- Citi Field (2009)
// Outer wall: city footprint; field: OpenStreetMap pitch polygon (home plate near
// (-23, -60), centre field bearing ~13°). Jackie Robinson Rotunda floor 160 ft across (Wikipedia).
const CITI_RING = P(
  61.0, 145.7, 125.7, -20.5, 97.8, -28.9, 93.1, -33.1, 98.4, -38.9, 104.3, -33.7, 109.1, -39.1, -28.1, -160.0, -46.9, -165.1, -66.0, -150.7, -120.6, -11.6, -114.4,
  -8.9, -140.2, 57.1, -130.2, 60.9, -126.2, 50.0, -101.0, 60.0, -92.7, 69.5, -4.9, 102.0, -10.4, 116.1, 20.7, 128.2, 17.5, 136.6, 41.0, 145.8, 44.0, 139.0
);
const CITI_FIELD = P(-7, -69, 23, -43, 33, -25, 63, -6, 52, 27, 42, 34, 14, 62, -3, 66, -64, 44, -77, 28, -58, -2, -57, -24, -41, -62, -27, -70, -19, -71);

function buildCitiField(b: MeshBuilder) {
  const c: V2 = [-5, 5];
  const home = Math.atan2(-60 - c[1], -23 - c[0]);
  b.color('#8D8A82').cap(CITI_RING, 0.2);
  b.color('#4F8A3C').cap(CITI_FIELD, 0.5);
  b.color('#B58A5E').cap(P(-25, -53, -19, -54, -2, -44, -15, -22, -36, -35), 0.6);
  bowl(b, CITI_FIELD, CITI_RING, c, rimProfile(home, 36, 14, 100, 130), {seats: '#2E5A3E', wall: '#A8573F', deck: '#9A9C9E'});
  // Jackie Robinson Rotunda at the home-plate entrance
  b.color('#A8573F').cylinder(-46, -140, 24.4, 0, 21, 24, {top: false});
  b.color('#C9C2B2').cylinder(-46, -140, 25, 21, 22.5, 24);
  b.color('#3F4A52');
  for (let k = 0; k < 7; k++) {
    const a = ((195 + k * 25) * Math.PI) / 180;
    b.frame(-46 + Math.cos(a) * 24.5, -140 + Math.sin(a) * 24.5, 0, 90 - (a * 180) / Math.PI, () => b.box(0, 0, 3, 5.5, 0.5, 13, {top: false}));
  }
  // centre-field scoreboard
  b.frame(18, 92, 0, 13, () => b.color('#2B2F36').box(0, 0, 14, 36, 3, 20));
}

CIVIC.push({
  id: 'citi_field',
  name: 'Citi Field',
  kind: 'stadium',
  built: [2006.87, 2009.25],
  end: 9999,
  anchor: [-73.84575, 40.7571],
  build: buildCitiField,
  replaces: [CITI_RING],
  facts: {
    Opened: 'April 2009 (Populous; ground broken November 13, 2006), beside Shea Stadium (1964–2009), whose site is now its parking',
    Rotunda: 'the Jackie Robinson Rotunda, recalling Ebbets Field, with a floor 160 ft (49 m) across',
    Model: 'outer wall from the city footprint; field from OpenStreetMap; the heights of the stands (36 m behind the plate — the city-measured roof height of this footprint is 24.3 m), of the rotunda and of the scoreboard are estimated from photographs'
  },
  sources: [WIKI + 'Citi_Field', FOOTPRINTS, OSM]
});

// ---------------------------------------------------------------------- Barclays Center (2012)
// City footprint; top at the city-measured 42.1 m. The canopy over the plaza holds an
// oculus of 117 by 56 ft (Wikipedia).
const BARCLAYS_RING = P(-50.9, 75.1, 61.4, 45.0, 68.8, 19.5, 67.3, -20.2, 85.1, -25.2, 79.2, -46.0, 59.4, -40.4, 43.8, -90.8, 0.6, -79.3, 2.8, -71.2, -54.7, -55.9, -96.4, 24.6, -70.0, 45.5);

function buildBarclays(b: MeshBuilder) {
  const steel = '#6E4B38';
  const body = P(-50.9, 75.1, 61.4, 45.0, 68.8, 19.5, 67.3, -20.2, 85.1, -25.2, 79.2, -46.0, 59.4, -40.4, 43.8, -90.8, 0.6, -79.3, 2.8, -71.2, -54.7, -55.9, -72, -20, -66, 40);
  const scale = (s: number): V2[] => body.map(([x, y]) => [-3 + (x + 3) * s, -6 + (y + 6) * s] as V2);
  b.color('#4A5A63').prism(body, 0, 8, {top: false});
  // three bands of weathering-steel lattice, leaning in and out
  b.color(steel).loft([scale(1.0), scale(1.03), scale(0.98)], [8, 14, 20], {top: false});
  b.color('#7A5541').loft([scale(0.98), scale(0.95), scale(0.9)], [20, 26, 32], {top: false});
  b.color('#5E6468').loft([scale(0.9), scale(0.6), scale(0.25)], [32, 39, 42.1], {top: true});
  // canopy over the plaza at Flatbush and Atlantic Avenues, with its oculus
  b.frame(-76, 18, 0, 197, () => {
    b.color(steel).prism(circle(0, 0, 1, 24, 27, 17), 9, 12.5, {bottom: true, holes: [circle(0, 0, 1, 24, 17.83, 8.53)]});
  });
}

CIVIC.push({
  id: 'barclays_center',
  name: 'Barclays Center',
  kind: 'stadium',
  built: [2010.19, 2012.72],
  end: 9999,
  anchor: [-73.9752, 40.68265],
  build: buildBarclays,
  replaces: [BARCLAYS_RING],
  facts: {
    Opened: 'September 21, 2012 (SHoP Architects with Ellerbe Becket; ground broken March 11, 2010), over the Vanderbilt rail yard at Atlantic Terminal',
    Form: 'bands of pre-weathered steel lattice; a canopy over the plaza with an oculus of 117 by 56 ft',
    Model: 'outline from the city footprint, top at the city-measured 42.1 m; the profile of the bands and the size and place of the canopy are estimated from photographs'
  },
  sources: [WIKI + 'Barclays_Center', FOOTPRINTS]
});

// ---------------------------------------------------------------------- Arthur Ashe Stadium
// Octagon 138 m across (city footprint); court from OpenStreetMap (long axis 337.8°).
// No height was verified: the bowl and the roof of 2016 are proportioned from photographs.
const ASHE_RING = P(47.3, -50.7, -15.2, -77.9, -61.9, -59.9, -89.2, 2.4, -71.4, 47.3, -8.1, 75.6, 36.4, 58.5, 64.2, -3.6);
const ASHE_C: V2 = [-12.2, -1.3];

function buildAshe(b: MeshBuilder) {
  const court = place(rect(0, 0, 22, 40), -11.5, -1.2, 337.8);
  b.color('#8D8A82').cap(ASHE_RING, 0.2);
  b.color('#3E7A5A').cap(place(rect(0, 0, 26, 46), -11.5, -1.2, 337.8), 0.5);
  b.color('#2F5D9E').cap(place(rect(0, 0, 10.97, 23.77), -11.5, -1.2, 337.8), 0.6);
  bowl(b, court, ASHE_RING, ASHE_C, () => 36, {seats: '#2B4C7E', wall: '#B9B4A8', deck: '#9A9C9E'}, 64, 2);
}

function buildAsheRoof(b: MeshBuilder) {
  // octagonal steel ring on eight columns outside the bowl, a square opening over the court
  const out = ASHE_RING.map(([x, y]) => [ASHE_C[0] + (x - ASHE_C[0]) * 1.06, ASHE_C[1] + (y - ASHE_C[1]) * 1.06] as V2);
  const open = place(rect(0, 0, 76.2, 76.2), -11.5, -1.2, 337.8);
  b.color('#E8EAEA').prism(out, 52, 58, {bottom: true, holes: [open]});
  b.color('#C9CED2');
  for (const [x, y] of out) b.beam([x, y, 0], [ASHE_C[0] + (x - ASHE_C[0]) * 0.97, ASHE_C[1] + (y - ASHE_C[1]) * 0.97, 52], 2.6);
  // the two fabric panels, drawn closed
  b.color('#F4F5F3').loft([open, place(rect(0, 0, 76.2, 6), -11.5, -1.2, 337.8)], [58, 62]);
}

const ASHE_SOURCES = [WIKI + 'Arthur_Ashe_Stadium', FOOTPRINTS, OSM];
CIVIC.push(
  {
    id: 'arthur_ashe_stadium',
    name: 'Arthur Ashe Stadium',
    kind: 'stadium',
    built: [1995.3, 1997.65],
    end: 9999,
    anchor: [-73.8469, 40.7499],
    build: buildAshe,
    replaces: [ASHE_RING],
    facts: {
      Opened: 'August 25, 1997 (Rossetti Associates) — the largest tennis stadium in the world, main court of the US Open',
      Model: 'octagon from the city footprint, court from OpenStreetMap; the height of the bowl (36 m) is an estimate from photographs — no published figure was verified, and the city-measured roof height of this footprint (17.7 m) is not the top of the stands'
    },
    sources: ASHE_SOURCES
  },
  {
    id: 'arthur_ashe_stadium_roof',
    name: 'Arthur Ashe Stadium — retractable roof',
    kind: 'stadium',
    built: [2013.6, 2016.6],
    end: 9999,
    anchor: [-73.8469, 40.7499],
    build: buildAsheRoof,
    facts: {
      Completed: '2016 (Rossetti): a 5,000-ton steel superstructure standing on its own columns around the stadium, with two 800-ton fabric panels (210,000 sq ft) closing over the court',
      Model: 'entirely proportioned from photographs: the height (about 62 m), the 76 m opening and the column positions are estimates, not cited figures'
    },
    sources: ASHE_SOURCES
  }
);

// ====================================================================== Coney Island
// Wonder Wheel: 150 ft tall (Wikipedia); the plane of the wheel follows the long axis of its
// loading platform (city footprint, 96.1°). Wheel diameter (42.6 m) estimated.
function buildWonderWheel(b: MeshBuilder) {
  const R = 21.3;
  const hz = 45.72 - R;
  b.frame(-4.3, -19.8, 0, 6.1, () => {
    b.color('#8E8A80').box(0, 0, 0, 23.4, 12.5, 2.2);
    b.color('#3E6FA3');
    for (const y of [-3.4, 3.4]) for (const x of [-10, 10]) b.beam([x, y * 1.6, 2.2], [0, y, hz], 0.9);
    b.beam([0, -3.6, hz], [0, 3.6, hz], 1.4);
    for (const y of [-1.5, 1.5]) {
      b.color('#C8563C');
      const ring = (r: number): V3[] => {
        const pts: V3[] = [];
        for (let k = 0; k <= 32; k++) pts.push([r * Math.cos((k / 32) * Math.PI * 2), y, hz + r * Math.sin((k / 32) * Math.PI * 2)]);
        return pts;
      };
      b.polyline(ring(R), 0.5).polyline(ring(R * 0.55), 0.35);
      for (let k = 0; k < 16; k++) {
        const a = (k / 16) * Math.PI * 2;
        b.beam([0, y, hz], [R * Math.cos(a), y, hz + R * Math.sin(a)], 0.25);
      }
    }
    // 8 fixed cars on the rim, 16 swinging cars on the inner tracks
    for (let k = 0; k < 24; k++) {
      const a = ((k + 0.5) / 24) * Math.PI * 2;
      const r = k % 3 === 0 ? R : R * 0.72;
      b.color(k % 3 === 0 ? '#F1EEE6' : k % 3 === 1 ? '#C73B32' : '#2E5FA8').box(r * Math.cos(a), 0, hz + r * Math.sin(a) - 2.5, 2, 2.4, 2.2);
    }
  });
}

CIVIC.push({
  id: 'wonder_wheel',
  name: 'Wonder Wheel',
  kind: 'monument',
  built: [1918.5, 1920.4],
  end: 9999,
  anchor: [-73.9791, 40.5742],
  build: buildWonderWheel,
  replaces: [place(rect(0, 0, 24.4, 13.5), -4.3, -19.8, 6.1)],
  facts: {
    Opened: 'Memorial Day 1920 (Charles Hermann; Eccentric Ferris Wheel Company, built 1918–1920)',
    Dimensions: '150 ft (45.7 m) tall, 200 tons; 24 cars, 16 of which slide on curved inner tracks',
    Model: 'position and orientation from the city footprint of its platform; wheel diameter (about 42.6 m) and the support frame estimated from photographs'
  },
  sources: [WIKI + 'Wonder_Wheel', LPC('1708'), FOOTPRINTS]
});

// Cyclone: 2,640 ft of track with six fan turns and twelve drops; 75 ft high (Wikipedia,
// which notes that some sources give 85 ft). The site is the city footprint; the
// course drawn inside it is schematic.
const CYCLONE_RING = P(
  3.0, 38.4, 10.9, 38.1, 17.4, 31.0, 17.6, 5.2, 15.3, 5.1, 6.7, -76.0, 4.3, -75.7, 4.2, -99.6, -1.5, -103.8, -8.8, -104.1, -16.0, -98.0, -15.9, -82.7, -12.2, -58.7,
  0.9, -33.7, 1.8, -24.0, -6.3, 16.7, -6.3, 27.6, -5.3, 33.6
);

function buildCyclone(b: MeshBuilder) {
  b.frame(1.4, -32.8, 0, 5, () => {
    // x across (the frame leans with the plot: shift west towards the south end)
    const sh = (y: number) => (y < -10 ? ((y + 10) / 60) * 9 : 0);
    const course: V3[] = [
      [8, 62, 3], [8.5, 20, 8], [8, -55, 22.2], [4, -64, 21.6], [-1, -62, 22], [-3, -30, 3.5], [-3.5, 5, 17.5], [-4, 40, 7], [-3, 60, 15], [1, 66, 16], [4.5, 60, 15],
      [4.5, 30, 4], [4, 0, 14.5], [3.5, -28, 5], [3, -48, 12.5], [0.5, -55, 13], [-1.5, -48, 12.5], [0.5, -22, 4], [1, 6, 10.5], [1.5, 34, 4], [3, 50, 8.5], [6, 52, 8], [8, 62, 3]
    ].map(([x, y, z]) => [x + sh(y), y, z] as V3);
    b.color('#EDEAE0').polyline(course, 1.3);
    // timber and steel trestle under the track
    b.color('#D9D5CA');
    for (let i = 0; i < course.length - 1; i++) {
      const p = course[i];
      const q = course[i + 1];
      const n = Math.max(1, Math.round(Math.hypot(q[0] - p[0], q[1] - p[1]) / 5));
      for (let k = 0; k < n; k++) {
        const t = k / n;
        const x = p[0] + (q[0] - p[0]) * t;
        const y = p[1] + (q[1] - p[1]) * t;
        const z = p[2] + (q[2] - p[2]) * t;
        b.beam([x - 0.9, y, 0], [x - 0.9, y, z], 0.3).beam([x + 0.9, y, 0], [x + 0.9, y, z], 0.3);
        if (z > 9) b.beam([x - 0.9, y, z * 0.5], [x + 0.9, y, z * 0.5], 0.25);
      }
    }
    b.color('#B9B4A8').box(8, 60, 0, 6, 16, 3);
  });
}

CIVIC.push({
  id: 'coney_island_cyclone',
  name: 'Coney Island Cyclone',
  kind: 'monument',
  built: [1927.1, 1927.49],
  end: 9999,
  anchor: [-73.9777, 40.5749],
  build: buildCyclone,
  replaces: [CYCLONE_RING],
  facts: {
    Opened: 'June 26, 1927 (Vernon Keenan, designer; Harry C. Baker, builder)',
    Track: '2,640 ft (805 m), six fan turns and twelve drops; 75 ft (23 m) high — some sources give 85 ft',
    Model: 'site from the city footprint, top of the lift hill at the cited 75 ft; the course of the track inside it is schematic, not surveyed'
  },
  sources: [WIKI + 'Coney_Island_Cyclone', LPC('1636'), FOOTPRINTS]
});

// Parachute Jump: 250 ft (Wikipedia); position and base from OpenStreetMap / the city
// footprint of the base pavilion. Leg spread and the reach of the twelve arms estimated.
function buildParachuteJump(b: MeshBuilder) {
  const cx = 2.3;
  const cy = 2.5;
  b.color('#9A968C').prism(P(-3.8, 9.0, 4.9, 10.4, 11.0, 3.0, 8.3, -3.8, -1.0, -5.2, -6.1, 1.6), 0, 4);
  b.color('#C23B2E');
  const hex = (r: number, z: number): V3[] => circle(cx, cy, r, 6).map(([x, y]) => [x, y, z] as V3);
  const levels: [number, number][] = [];
  for (let z = 0; z <= 70; z += 7) levels.push([z, 6 - (4.5 * z) / 70]);
  for (let i = 0; i < levels.length; i++) {
    const ring = hex(levels[i][1], levels[i][0]);
    b.polyline([...ring, ring[0]], 0.3);
    if (i === levels.length - 1) break;
    const up = hex(levels[i + 1][1], levels[i + 1][0]);
    for (let k = 0; k < 6; k++) b.beam(ring[k], up[k], 0.45).beam(ring[k], up[(k + 1) % 6], 0.2);
  }
  // crown of twelve drop arms
  const tips: V3[] = [];
  for (let k = 0; k < 12; k++) {
    const a = (k / 12) * Math.PI * 2;
    const tip: V3 = [cx + Math.cos(a) * 14.5, cy + Math.sin(a) * 14.5, 72.5];
    tips.push(tip);
    b.beam([cx + Math.cos(a) * 1.5, cy + Math.sin(a) * 1.5, 70], tip, 0.4).beam([cx, cy, 76.2], tip, 0.2);
  }
  b.polyline([...tips, tips[0]], 0.3);
  b.beam([cx, cy, 70], [cx, cy, 76.2], 0.8);
}

CIVIC.push({
  id: 'parachute_jump',
  name: 'Parachute Jump',
  kind: 'tower',
  built: [1941.0, 1941.4],
  end: 9999,
  anchor: [-73.984397, 40.572977],
  build: buildParachuteJump,
  replaces: [P(-4.8, 10, 5.4, 11.6, 12.4, 3.2, 9.2, -4.9, -1.4, -6.4, -7.4, 1.4)],
  facts: {
    History: 'built for the 1939–40 World’s Fair in Flushing Meadows (the Life Savers Parachute Jump); re-erected at Steeplechase Park in 1941; closed in 1964',
    Height: '250 ft (76 m), 170 tons; twelve cantilevered arms',
    Model: 'position from OpenStreetMap and the city footprint of the base pavilion; the taper of the six-sided tower and the reach of the arms estimated from photographs; its years at the fair are not modelled'
  },
  sources: [WIKI + 'Parachute_Jump', LPC('1638'), FOOTPRINTS, OSM]
});

// ====================================================================== lighthouses
/** Tapering round or polygonal light tower: shaft r0 -> r1 up to zg, gallery, lantern and roof to zTop. */
function lightTower(b: MeshBuilder, x: number, y: number, r0: number, r1: number, zg: number, zTop: number, shaft: string, segs = 12) {
  b.color(shaft).frustum(x, y, r0, r1, 0, zg, segs, false);
  b.color('#2B2D30').cylinder(x, y, r1 + 0.55, zg, zg + 0.3, segs);
  b.color('#DCE6EA').cylinder(x, y, r1 * 0.72, zg + 0.3, zTop - (zTop - zg) * 0.35, segs, {top: false});
  b.color('#2B2D30');
  spire(b, x, y, r1 * 0.85, zTop - (zTop - zg) * 0.35, zTop, segs);
}

CIVIC.push(
  {
    id: 'little_red_lighthouse',
    name: "Little Red Lighthouse (Jeffrey's Hook Light)",
    kind: 'tower',
    built: [1921.0, 1921.8],
    end: 9999,
    anchor: [-73.946963, 40.850255],
    build: b => lightTower(b, 0, 0, 2.7, 1.9, 8.5, 12.0, '#B5302A', 12),
    replaces: [circle(0, 0, 4.5, 12)],
    facts: {
      History: 'cast in 1880 as the North Hook Beacon at Sandy Hook; re-erected at Jeffrey’s Hook in 1921; dark since 1948, saved by public protest in 1951 and relit in 2002',
      Height: '12.0 m (OpenStreetMap; usually described as 40 ft)',
      Model: 'position and height from OpenStreetMap; base diameter and stages estimated'
    },
    sources: [WIKI + 'Little_Red_Lighthouse', LPC('1654'), OSM]
  },
  {
    id: 'coney_island_light',
    name: 'Coney Island Light',
    kind: 'tower',
    built: [1889.5, 1890.58],
    end: 9999,
    anchor: [-74.011763, 40.576605],
    build: b => {
      b.color('#F1F0EA');
      for (const sx of [-1, 1]) for (const sy of [-1, 1]) b.beam([sx * 3.3, sy * 3.3, 0], [sx * 1.3, sy * 1.3, 18.6], 0.35);
      for (const z of [4.6, 9.2, 13.9]) {
        const h = 3.3 - (2 * z) / 18.6;
        b.polyline([[-h, -h, z], [h, -h, z], [h, h, z], [-h, h, z], [-h, -h, z]], 0.22);
      }
      b.cylinder(0, 0, 0.9, 0, 18.6, 8, {top: false});
      b.color('#2B2D30').cylinder(0, 0, 2.3, 18.6, 19, 8).cylinder(0, 0, 1.5, 19, 21.4, 8, {top: false});
      spire(b, 0, 0, 1.7, 21.4, 22.9, 8);
    },
    replaces: [rect(0, 0, 4, 4)],
    facts: {
      Lit: 'August 1, 1890, at Norton’s Point: a skeletal white tower with black trim; the last civilian-kept light in the United States (Frank Schubert, to 2003)',
      Height: 'focal plane 75 ft (23 m) above the water (OpenStreetMap gives the tower 22.9 m)',
      Model: 'position and height from OpenStreetMap; the spread of the legs estimated'
    },
    sources: [WIKI + 'Coney_Island_Light', OSM]
  },
  {
    id: 'blackwell_island_light',
    name: 'Blackwell Island Light (Roosevelt Island Lighthouse)',
    kind: 'tower',
    built: [1872.0, 1872.8],
    end: 9999,
    anchor: [-73.9402, 40.7727],
    build: b => lightTower(b, 1.4, 15.1, 2.16, 1.8, 11, 15.24, '#8E8E86', 8),
    replaces: [circle(1.4, 15.1, 3.2, 8)],
    facts: {
      Built: '1872 (James Renwick Jr.), of grey gneiss quarried on the island by convict labour',
      Height: 'about 50 ft (15 m); octagonal, 4 m across (city footprint; city-measured top 17.4 m)',
      Model: 'position and plan from the city footprint; gallery and lantern stages estimated'
    },
    sources: [WIKI + 'Blackwell_Island_Light', LPC('0911'), FOOTPRINTS]
  }
);

// ====================================================================== harbour forts
/** A casemated wall ring: `ring` outside, the same ring shrunk by k about (cx, cy) inside. */
function fortRing(b: MeshBuilder, ring: V2[], cx: number, cy: number, k: number, h: number, stone: string, top: string) {
  const inner = ring.map(([x, y]) => [cx + (x - cx) * k, cy + (y - cy) * k] as V2);
  b.color(stone).prism(ring, 0, h, {top: false, holes: [inner]});
  b.color(top).cap(ring, h, [inner]);
  b.color('#A9A594').cap(inner, 0.2);
  return inner;
}

// Castle Williams: the city footprint is 61.5–61.9 m across with a 972 m2 courtyard
// (Overture's ring area 2,125 m2); top at the city-measured 14.9 m.
const CWILLIAMS_RING = P(24.3, 19.3, 29.6, 7.5, 31.3, -23.1, -3.9, -29.0, -15.7, -25.3, -26.1, -16.2, -31.1, -4.9, -31.3, 7.5, -26.7, 18.2, -18.6, 26.6, -8.1, 31.6, 4.5, 31.8, 16.2, 27.1);
const BATTERY_WEED_RING = P(
  -21.7, 49.5, 13.1, 38.4, 16.4, 41.4, 21.5, 40.1, 24.8, 36.1, 25.1, 31.5, 21.8, 28.2, 31.6, -18.2, 36.0, -19.5, 36.2, -28.9, 32.0, -32.2, 28.0, -30.1, -8.0, -62.5, -7.1,
  -67.0, -15.4, -75.6, -19.6, -52.9, -15.4, -49.3, -17.9, -33.9, -7.6, -31.7, -4.8, -44.9, 15.0, -25.5, 16.3, -22.6, 14.4, -20.5, 15.0, -18.5, 18.1, -18.0, 18.6, -8.4,
  12.4, 17.9, 10.8, 20.8, 5.0, 23.2, 1.9, 29.4, -23.0, 38.0, -20.3, 24.9, -30.1, 22.9, -31.8, 30.8, -36.5, 31.7, -44.9, 61.2, -23.0, 55.8
);
const TOMPKINS_RING = P(-33.4, 94.6, 84.5, -50.9, 22.2, -85.4, -40.2, -31.4, -80.4, 40.8);
const FORT_HAMILTON_RING = P(
  -9.3, 51.7, 46.1, -45.0, 45.7, -52.4, 42.3, -59.0, 19.6, -77.6, 9.8, -65.9, 12.6, -63.6, 10.4, -61.0, 25.9, -45.9, 10.3, -18.0, 7.1, -19.8, -5.2, 2.2, -9.8, -0.4, -18.1,
  14.4, -11.2, 18.2, -12.1, 19.9, -15.0, 18.4, -22.6, 31.9, -55.4, 20.3, -62.0, 39.1, -59.9, 39.9, -61.0, 43.0, -21.6, 55.8
);

CIVIC.push(
  {
    id: 'castle_williams',
    name: 'Castle Williams (Governors Island)',
    kind: 'monument',
    built: [1807.5, 1811.9],
    end: 9999,
    anchor: [-74.01934, 40.692826],
    build: b => {
      const inner = fortRing(b, CWILLIAMS_RING, -0.5, 1.5, 0.56, 12.2, '#8E5A45', '#7C7A70');
      b.color('#8E5A45').wallProfile(CWILLIAMS_RING, 12.2, 14.9, true);
      void inner;
      // three tiers of casemate embrasures towards the harbour
      b.color('#3E2F28');
      for (const z of [2.4, 6, 9.6])
        for (let k = 0; k < 26; k++) {
          const a = ((75 + (k * 250) / 25) * Math.PI) / 180;
          b.frame(-0.5 + Math.cos(a) * 31, 1.5 + Math.sin(a) * 31, 0, 90 - (a * 180) / Math.PI, () => b.box(0, 0, z, 1.3, 0.8, 1.1, {top: false}));
        }
    },
    replaces: [CWILLIAMS_RING],
    facts: {
      Built: '1807–1811 (Lt. Col. Jonathan Williams) — the first casemated fort in the United States, a near-circle of red sandstone facing the harbour; later a military prison',
      Dimensions: '210 ft across, walls 40 ft high and 7 to 8 ft thick (61.5–61.9 m across in the city footprint; city-measured top 14.9 m)',
      Model: 'outline and courtyard area from the city footprint and OpenStreetMap; wall top at the cited 40 ft with the parapet to the city-measured 14.9 m; embrasure positions schematic'
    },
    sources: [WIKI + 'Castle_Williams', 'https://www.nps.gov/gois/learn/historyculture/castle-williams.htm', LPC('0542'), FOOTPRINTS, OSM]
  },
  {
    id: 'battery_weed',
    name: 'Battery Weed (Fort Richmond), Fort Wadsworth',
    kind: 'monument',
    built: [1847.5, 1864.0],
    end: 9999,
    anchor: [-74.054172, 40.605511],
    build: b => {
      b.color('#B9B4A8').prism(BATTERY_WEED_RING, 0, 15, {top: false});
      b.color('#8E9486').cap(BATTERY_WEED_RING, 15);
      b.color('#B9B4A8').wallProfile(BATTERY_WEED_RING, 15, 17.1, true);
    },
    replaces: [BATTERY_WEED_RING, rect(0, 0, 30, 60)],
    facts: {
      Built: '1847–1864 as Fort Richmond, at the water’s edge of the Narrows: three tiers of granite casemates under a barbette tier; renamed for Gen. Stephen Weed in 1865',
      Model: 'wall outline from the city footprint, top at the city-measured 17.1 m (OpenStreetMap gives 13.6 m); no tier heights were verified'
    },
    sources: [WIKI + 'Fort_Wadsworth', 'https://www.nps.gov/gate/learn/historyculture/fort-wadsworth.htm', LPC('0379'), FOOTPRINTS]
  },
  {
    id: 'fort_tompkins',
    name: 'Fort Tompkins, Fort Wadsworth',
    kind: 'monument',
    built: [1859.0, 1876.0],
    end: 9999,
    anchor: [-74.056521, 40.60503],
    build: b => {
      fortRing(b, TOMPKINS_RING, -3.9, -1.9, 0.663, 15.5, '#B5AFA2', '#8E9486');
    },
    replaces: [TOMPKINS_RING],
    facts: {
      Built: '1859–1876 on the bluff above Battery Weed, on the site of a fort of the War of 1812: a five-sided granite work with casemated barracks around a parade',
      Model: 'outline from the city footprint, parade area from OpenStreetMap (5,910 m2), top at the city-measured 15.5 m; no wall heights were verified'
    },
    sources: [WIKI + 'Fort_Wadsworth', LPC('0824'), FOOTPRINTS, OSM]
  },
  {
    id: 'fort_hamilton_casemate_fort',
    name: 'Fort Hamilton (the casemate fort of 1831)',
    kind: 'monument',
    built: [1825.45, 1831.85],
    end: 9999,
    anchor: [-74.032489, 40.608817],
    build: b => {
      b.color('#A9A294').prism(FORT_HAMILTON_RING, 0, 8, {top: false});
      b.color('#8E9486').cap(FORT_HAMILTON_RING, 8);
    },
    replaces: [FORT_HAMILTON_RING],
    facts: {
      Built: 'cornerstone June 11, 1825; garrisoned November 1, 1831 — the granite fort on the Brooklyn side of the Narrows; the surviving part became the officers’ club',
      Model: 'the surviving structure as the city footprint shows it, drawn as a plain 8 m block (the city-measured roof height is 15.2 m; no wall height was verified)'
    },
    sources: [WIKI + 'Fort_Hamilton', LPC('0953'), FOOTPRINTS]
  }
);

// ====================================================================== colonial and Federal houses
/** Gable-roofed house: walls w x l to zEave, ridge along y to zRidge, end chimneys. */
function gableHouse(b: MeshBuilder, cx: number, cy: number, w: number, l: number, zEave: number, zRidge: number, wall: string, roof: string, chimneys = true) {
  b.color(wall).box(cx, cy, 0, w, l, zEave, {top: false});
  b.color(roof).gable(cx, cy, w + 0.8, l + 0.4, zEave, zRidge - zEave, true);
  if (chimneys) b.color('#8A5A48').box(cx, cy - l / 2 + 0.7, zEave, 1, 1, zRidge - zEave + 0.9).box(cx, cy + l / 2 - 0.7, zEave, 1, 1, zRidge - zEave + 0.9);
}

CIVIC.push(
  {
    id: 'wyckoff_house',
    name: 'Pieter Claesen Wyckoff House',
    kind: 'building',
    built: [1651.0, 1652.5],
    end: 9999,
    anchor: [-73.9208, 40.6444],
    build: b => {
      b.frame(-0.2, -5.1, 0, 118.7, () => {
        gableHouse(b, -0.1, 4.3, 12.2, 11.1, 2.7, 7.5, '#8B7355', '#5E5346');
        gableHouse(b, 0.45, -5.55, 8.1, 8.5, 2.3, 5.6, '#8B7355', '#5E5346', false);
      });
    },
    replaces: [P(-7.0, 2.8, 0.4, -1.3, 1.6, 0.9, 11.4, -4.4, 5.5, -15.1, -4.2, -9.8, -3.5, -8.4, -11.0, -4.4)],
    facts: {
      Built: 'about 1652, enlarged in the eighteenth and nineteenth centuries — the oldest surviving building in New York City and the city’s first designated landmark (LP-0001)',
      Form: 'a shingled Dutch farmhouse with flared spring eaves',
      Model: 'plan from the city footprint, ridge at the city-measured 7.5 m; eaves and the lower wing estimated; shown at today’s extent from 1652'
    },
    sources: [WIKI + 'Wyckoff_House', LPC('0001'), FOOTPRINTS]
  },
  {
    id: 'conference_house',
    name: 'Conference House (Billopp House)',
    kind: 'building',
    built: [1675.0, 1680.0],
    end: 9999,
    anchor: [-74.25322, 40.503129],
    build: b => {
      b.frame(-0.2, 1.2, 0, 158.2, () => gableHouse(b, 0, 0, 13.5, 14.1, 6.6, 11.8, '#8A7F70', '#5A5148'));
    },
    replaces: [place(rect(0, 0, 14.5, 15.1), -0.2, 1.2, 158.2)],
    facts: {
      Built: 'about 1680 for Capt. Christopher Billopp: a two-storey fieldstone manor above the Arthur Kill',
      History: 'on September 11, 1776 Benjamin Franklin, John Adams and Edward Rutledge met Lord Howe here in a failed peace conference',
      Model: 'plan from the city footprint (13.5 x 14.1 m), ridge at the city-measured 11.8 m; eaves height estimated'
    },
    sources: [WIKI + 'Conference_House', LPC('0393'), FOOTPRINTS]
  },
  {
    id: 'morris_jumel_mansion',
    name: 'Morris–Jumel Mansion',
    kind: 'building',
    built: [1765.0, 1765.9],
    end: 9999,
    anchor: [-73.938574, 40.83445],
    build: b => {
      const white = '#EDEAE0';
      b.frame(-0.55, -1.45, 0, 9.2, () => {
        b.color(white).box(0, 0, 0, 16.9, 12.4, 7.6, {top: false});
        b.color('#6E6A64').hip(0, 0, 17.7, 13.2, 7.6, 2.6);
        b.color('#8A5A48').box(-4.5, 0, 9, 1.1, 1.1, 2.6).box(4.5, 0, 9, 1.1, 1.1, 2.6);
        // two-storey portico of four Tuscan columns
        b.color(white).box(0, -7.4, 0, 9.9, 2.4, 0.6);
        columns(b, -4.3, -8.1, 4.3, -8.1, 4, 0.7, 0.6, 7.2);
        b.box(0, -7.4, 7.2, 9.9, 2.4, 0.6).gable(0, -7.4, 9.9, 2.4, 7.8, 2, true);
        // octagonal drawing-room wing at the rear
        b.cylinder(0.25, 11.85, 3.9, 0, 6.6, 8, {top: false}).box(0.25, 7.6, 0, 5, 3, 6.6);
        b.color('#6E6A64');
        spire(b, 0.25, 11.85, 4.2, 6.6, 8.6, 8);
      });
    },
    replaces: [P(4.5, 15.7, 5.7, 13.7, 4.2, 4.0, 8.8, 3.3, 6.8, -8.9, 2.9, -10.6, -6.9, -9.0, -9.9, -6.2, -8.0, 6.0, -2.9, 5.2, -1.4, 14.9, 0.8, 16.3)],
    facts: {
      Built: '1765 for Col. Roger Morris — the oldest surviving house in Manhattan; Washington’s headquarters in the autumn of 1776; home of Eliza Jumel from 1810',
      Form: 'a Palladian house with a two-storey portico and an octagonal wing — one of the first octagonal rooms in the colonies',
      Model: 'plan from the city footprint, chimney tops at the city-measured 11.6 m; eaves and roof levels estimated'
    },
    sources: [WIKI + 'Morris%E2%80%93Jumel_Mansion', LPC('0308'), FOOTPRINTS]
  },
  {
    id: 'dyckman_farmhouse',
    name: 'Dyckman Farmhouse',
    kind: 'building',
    built: [1783.5, 1785.0],
    end: 9999,
    anchor: [-73.9228, 40.8674],
    build: b => {
      b.frame(-7.2, -2.4, 0, 68.5, () => {
        b.color('#B9AD98').box(0, 0, 0, 9.6, 18, 3.6, {top: false});
        // gambrel roof with spring eaves over the porches
        b.color('#5E5346').loft([rect(0, 0, 13.4, 18.4), rect(0, 0, 6.6, 18.2), rect(0, 0, 0.3, 18)], [3.6, 6.9, 8.6]);
        b.color('#EDEAE0');
        for (const s of [-1, 1]) columns(b, s * 6.2, -8, s * 6.2, 8, 6, 0.25, 0.4, 3.6, 4);
        b.color('#8A5A48').box(0, -8.2, 8, 1, 1, 1.4).box(0, 8.2, 8, 1, 1, 1.4);
      });
    },
    replaces: [place(rect(0, 0, 14.6, 19), -7.2, -2.4, 68.5)],
    facts: {
      Built: 'about 1783–1785 by William Dyckman — the last farmhouse in Manhattan; a museum since 1916',
      Form: 'Dutch Colonial: fieldstone, brick and clapboard under a gambrel roof with spring eaves and full-width porches',
      Model: 'plan from the city footprint (13.6 x 18.0 m with the porches), ridge at the city-measured 8.6 m; roof profile estimated'
    },
    sources: [WIKI + 'Dyckman_House', LPC('0309'), FOOTPRINTS]
  },
  {
    id: 'gracie_mansion',
    name: 'Gracie Mansion',
    kind: 'building',
    built: [1799.0, 1799.9],
    end: 9999,
    anchor: [-73.943054, 40.776104],
    build: b => {
      const cream = '#E9DFA9';
      const ring = P(11.9, 16.9, 21.1, -6.4, 4.1, -13.2, 0.2, -3.2, -4.2, -5.0, -3.9, -5.8, -18.5, -11.6, -24.3, 3.0, -1.6, 11.6, -1.8, 12.2, 4.6, 14.7, 4.8, 14.1);
      b.color(cream).prism(ring, 0, 7.4, {top: false});
      b.color('#7B7F7C').cap(ring, 7.4);
      b.frame(8.0, 1.85, 0, 68.3, () => {
        b.color('#7B7F7C').hip(0, 0, 25, 18.3, 7.4, 3.2);
        b.color('#EDEAE0').box(0, 0, 10.2, 12, 8, 0.9);
        b.color('#8A5A48').box(-6, 0, 9.5, 1, 1, 3.1).box(6, 0, 9.5, 1, 1, 3.1);
        // porch along the river front
        b.color('#EDEAE0');
        columns(b, -12.2, 9.0, 12.2, 9.0, 9, 0.3, 0.6, 3.8, 4);
        b.box(0, 8.7, 3.8, 25, 1.2, 0.3);
      });
      b.frame(-10.05, 0, 0, 68.3, () => b.color('#7B7F7C').hip(0, 0, 15.4, 24, 7.4, 2.6));
    },
    replaces: [P(11.9, 16.9, 21.1, -6.4, 4.1, -13.2, 0.2, -3.2, -4.2, -5.0, -18.5, -11.6, -24.3, 3.0, -1.6, 11.6, 4.6, 14.7)],
    facts: {
      Built: '1799 for the merchant Archibald Gracie, enlarged about 1804–1811; the mayor’s residence since 1942; the Susan E. Wagner Wing was added in 1966 (shown here from 1799)',
      Model: 'plan from the city footprint, chimney tops at the city-measured 12.6 m; eaves, roofs and the porch estimated'
    },
    sources: [WIKI + 'Gracie_Mansion', LPC('0179'), FOOTPRINTS]
  }
);

