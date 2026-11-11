/**
 * New York landmarks, second pass B: towers and apartment houses that stand today and were missing.
 * Research, sources and numeric checks: data/research/landmarks_more_b.md.
 *
 * Same conventions as nyc-towers.ts: each model is drawn in the building's own frame (origin =
 * centroid of the city's official footprint, +v along the bearing `B` of the long edge); plans
 * come from the official footprint (NYC building footprints), set-back levels from OpenStreetMap
 * building parts where volunteers mapped them (© OpenStreetMap contributors, ODbL, via Overture
 * 2026-10-21.0); total heights from the cited sources. What is estimated is named in each
 * model's `Model:` fact.
 */
import {MeshBuilder, type V2} from './kit';
import type {Landmark} from './types';

type Level = [number, number, V2[]];
type Massing = {anchor: V2; B: number; foot: V2[][]; levels: Level[]};

// <massing> (data/interim/landmarks_more_b/gen.py; hand-set entries below the generated ones)
const M: Record<string, Massing> = {
  one57: {
    anchor: [-73.979016, 40.765515],
    B: 29.1,
    foot: [[[-17.0, -24.9], [-17.0, 12.1], [-22.5, 11.9], [-22.0, 35.8], [0.9, 36.2], [0.9, 5.5], [11.5, 5.6], [11.5, -3.5], [31.5, -3.5], [31.5, -24.8]]],
    levels: [
      [0, 30, [[-17.0, -24.9], [-17.0, 3.3], [-17.0, 10.1], [-17.0, 12.1], [-22.1, 11.9], [-22.5, 11.9], [-22.0, 35.8], [0.9, 36.2], [0.9, 24.4], [0.9, 5.5], [11.5, 5.6], [11.5, -3.5], [29.5, -3.5], [31.5, -3.5], [31.5, -6.5], [31.5, -22.6], [31.5, -22.8], [31.5, -24.8], [29.3, -24.8]]],
      [30, 35, [[-20.3, -25.9], [-20.2, 19.8], [0.5, 19.9], [0.7, -3.6], [30.9, -3.4], [30.8, -25.7]]],
      [35, 45, [[-20.3, -25.9], [-20.2, 19.8], [0.5, 19.9], [0.7, -3.6], [30.9, -3.4], [30.8, -22.1], [-7.3, -22.2], [-7.6, -25.8]]],
      [45, 95, [[-20.3, -22.2], [-20.2, 19.8], [0.5, 19.9], [0.7, -3.6], [30.9, -3.4], [30.8, -22.1]]],
      [95, 119.8, [[-20.2, -15.3], [-20.2, 19.8], [0.5, 19.9], [0.7, -3.6], [30.9, -3.4], [30.8, -22.1], [6.0, -22.2], [5.9, -18.6], [-5.1, -18.6], [-5.3, -15.3]]],
      [119.8, 125, [[-20.2, -15.3], [-20.2, 19.8], [0.5, 19.9], [0.7, -3.6], [30.9, -3.4], [30.8, -15.3], [22.2, -15.3], [22.0, -18.5], [-5.1, -18.6], [-5.4, -15.3]]],
      [125, 226.8, [[-20.2, -15.3], [-20.2, 19.8], [0.5, 19.9], [0.6, -3.6], [22.0, -3.4], [22.0, -18.5], [-5.1, -18.6], [-5.4, -15.3]]],
      [226.8, 230, [[-20.2, -15.3], [-20.2, 19.8], [0.5, 19.9], [0.6, -3.6], [22.0, -3.4], [22.0, -15.3]]],
      [230, 298.6, [[-20.2, -15.3], [-20.2, 19.8], [0.5, 19.9], [0.5, -3.4], [9.1, -3.5], [9.1, -15.2]]],
      [298.6, 306, [[-20.2, -3.7], [-20.2, 19.8], [0.5, 19.9], [0.5, -3.6]]],
    ]
  },

  twc: {
    anchor: [-73.983098, 40.768476],
    B: 29.0,
    foot: [[[50.2, 37.7], [45.7, 23.6], [41.5, 23.7], [41.0, -2.8], [45.6, -2.9], [47.7, -10.6], [51.5, -19.8], [56.8, -28.3], [61.9, -34.5], [66.1, -38.6], [72.4, -43.6], [79.3, -47.7], [86.5, -51.0], [85.2, -54.7], [94.5, -55.9], [94.5, -59.3], [-54.2, -59.4], [-53.9, 67.7], [32.8, 67.8]]],
    levels: [
      [0, 45, [[50.2, 37.7], [45.7, 23.6], [41.5, 23.7], [41.0, -2.8], [45.6, -2.9], [46.0, -4.9], [46.5, -6.8], [47.0, -8.7], [47.7, -10.6], [48.3, -12.5], [49.0, -14.4], [49.8, -16.2], [50.6, -18.0], [50.8, -18.3], [51.5, -19.8], [52.5, -21.6], [53.5, -23.3], [54.5, -25.0], [55.6, -26.7], [56.8, -28.3], [58.0, -29.9], [59.2, -31.5], [60.5, -33.0], [61.9, -34.5], [63.2, -35.9], [64.7, -37.3], [66.1, -38.6], [67.7, -39.9], [69.2, -41.2], [70.8, -42.4], [72.4, -43.6], [74.1, -44.7], [75.8, -45.7], [76.0, -45.9], [77.5, -46.8], [79.3, -47.7], [81.0, -48.6], [82.9, -49.5], [84.7, -50.3], [86.5, -51.0], [86.1, -52.2], [85.3, -54.3], [85.2, -54.7], [94.5, -55.9], [94.5, -59.1], [94.5, -59.3], [64.5, -59.3], [47.9, -59.3], [17.0, -59.3], [6.8, -59.3], [0.3, -59.3], [-28.4, -59.3], [-54.2, -59.4], [-54.2, -57.6], [-54.1, -43.5], [-54.1, -24.1], [-54.0, 29.7], [-53.9, 51.7], [-53.9, 58.0], [-53.9, 63.1], [-53.9, 67.7], [-13.0, 67.7], [32.8, 67.8], [49.5, 39.0]]],
      [45, 55, [[-44.8, -3.4], [-44.0, 59.8], [-31.0, 59.7], [-30.9, 64.6], [30.1, 63.1], [11.9, 23.8], [16.1, -3.8], [16.9, -5.0], [20.5, -5.1], [59.8, -46.3], [-40.1, -45.7], [-40.3, -3.7]]],
      [55, 80, [[-40.3, -3.4], [16.1, -3.9], [16.9, -5.0], [20.5, -5.1], [59.8, -46.3], [-40.1, -45.7]]],
      [55, 80, [[-44.3, 25.3], [-44.0, 59.8], [-31.0, 59.7], [-30.9, 64.6], [30.1, 63.1], [11.9, 23.7]]],
      [80, 105, [[-40.3, -3.4], [16.1, -3.9], [16.9, -5.0], [20.5, -5.1], [59.8, -46.3], [-40.1, -45.7]]],
      [80, 105, [[-44.3, 25.3], [-44.0, 59.8], [20.9, 59.3], [11.9, 23.7]]],
      [105, 125, [[-40.3, -3.4], [16.1, -3.9], [36.8, -38.3], [-40.1, -38.2]]],
      [105, 125, [[-44.0, 59.8], [-19.4, 59.0], [0.5, 24.5], [-24.0, 25.0]]],
      [125, 230, [[-13.1, -3.6], [16.1, -3.9], [36.8, -38.3], [7.0, -38.2]]],
      [125, 230, [[-44.0, 59.8], [-19.4, 59.0], [0.5, 24.5], [-24.0, 25.0]]],
    ]
  },

  hy35: {
    anchor: [-74.000108, 40.75453],
    B: 28.7,
    foot: [[[46.7, -23.3], [-46.6, -23.2], [-46.6, 23.2], [46.6, 23.2]]],
    levels: [
      [0, 33, [[46.7, -23.3], [-46.6, -23.2], [-46.6, 23.2], [46.6, 23.2]]],
      [33, 160, [[-45.7, -25.0], [-45.6, 23.6], [48.5, 23.8], [48.4, -24.7]]],
      [160, 308, [[-27.3, -24.9], [-27.2, 23.6], [48.5, 23.8], [48.4, -24.7]]],
    ]
  },

  w53: {anchor: [-73.978162, 40.761825], B: 29.0, foot: [[[-12.0, 29.0], [20.9, 29.1], [20.8, 10.8], [13.1, 10.8], [13.1, 5.9], [20.8, 5.9], [20.8, -1.4], [8.5, -1.4], [8.5, -31.9], [-18.0, -32.0], [-18.0, -1.5], [-12.0, -1.5]]], levels: []},
  plaza: {anchor: [-73.974449, 40.764456], B: 28.1, foot: [[[-48.4, -28.3], [-48.3, 1.0], [-33.9, 1.0], [-33.9, 21.4], [-36.3, 21.4], [-36.3, 33.8], [39.1, 33.8], [41.9, 30.5], [41.8, -29.6], [39.0, -31.4], [-42.9, -31.4], [-42.9, -28.3]]], levels: [[58, 64, [[-46.9, -26.8], [-46.8, -0.5], [-32.4, -0.5], [-32.4, 22.9], [-34.8, 22.9], [-34.8, 32.3], [38.4, 32.3], [40.4, 30.0], [40.3, -28.8], [38.6, -29.9], [-41.4, -29.9], [-41.4, -26.8]]], [64, 70, [[-45.2, -25.1], [-45.1, -2.2], [-30.7, -2.2], [-30.7, 24.6], [-33.1, 24.6], [-33.1, 30.6], [37.6, 30.6], [38.7, 29.3], [38.6, -27.9], [38.1, -28.2], [-39.7, -28.2], [-39.7, -25.1]]], [70, 76.8, [[-43.4, -23.3], [-43.3, -4.0], [-28.9, -4.0], [-28.9, 26.4], [-31.3, 26.4], [-31.3, 28.8], [36.9, 28.7], [36.8, -26.4], [-37.9, -26.4], [-37.9, -23.3]]]]},
  carnegie: {anchor: [-73.979914, 40.765004], B: 29.2, foot: [[[-22.9, 30.5], [23.0, 30.6], [22.9, -30.0], [16.6, -30.1], [16.6, -30.7], [-22.9, -30.7]]], levels: []},
  ansonia: {anchor: [-73.980849, 40.780515], B: 28.7, foot: [[[28.6, -23.5], [-21.5, -23.5], [-35.1, 21.7], [28.6, 21.7]]], levels: [[61, 67, [[27.4, -22.3], [-20.6, -22.3], [-33.5, 20.5], [27.4, 20.5]]], [67, 73, [[25.6, -20.5], [-19.3, -20.5], [-31.1, 18.7], [25.6, 18.7]]], [73, 78, [[23.6, -18.5], [-17.8, -18.5], [-28.4, 16.7], [23.6, 16.7]]]]},
  dakota: {anchor: [-73.97615, 40.776784], B: 29.1, foot: [[[-31.3, 31.3], [30.3, 31.3], [30.2, -8.0], [29.1, -8.0], [29.1, -16.5], [30.1, -16.5], [30.1, -31.6], [-31.2, -31.6], [-31.1, -15.2], [-28.9, -15.2], [-28.8, 14.8], [-31.3, 14.8]]], levels: [[0, 36, [[-7.2, 8.2], [-7.3, -8.8], [-12.8, -8.8], [-12.8, -15.5], [12.1, -15.5], [12.1, -8.2], [5.7, -8.2], [5.8, 8.1], [12.2, 8.1], [12.2, 14.5], [-11.9, 14.5], [-13.3, 12.6], [-11.9, 8.2]]]]},
};
// </massing>

function toLocal(B: number, ring: V2[]): V2[] {
  const a = (-B * Math.PI) / 180;
  const c = Math.cos(a);
  const s = Math.sin(a);
  return ring.map(([u, v]) => [c * u - s * v, s * u + c * v] as V2);
}

/** Outline grown by about d metres (scaled about its centroid) for `replaces`. */
function grow(ring: V2[], d: number): V2[] {
  const cx = ring.reduce((a, p) => a + p[0], 0) / ring.length;
  const cy = ring.reduce((a, p) => a + p[1], 0) / ring.length;
  const r = ring.reduce((a, p) => a + Math.hypot(p[0] - cx, p[1] - cy), 0) / ring.length;
  const k = 1 + d / r;
  return ring.map(([x, y]) => [cx + (x - cx) * k, cy + (y - cy) * k] as V2);
}

function scaleV(ring: V2[], f: number, vc: number): V2[] {
  return ring.map(([u, v]) => [u, vc + (v - vc) * f] as V2);
}

type Spec = Omit<Landmark, 'anchor' | 'build' | 'replaces' | 'end'> & {
  m: Massing;
  end?: number;
  draw: (b: MeshBuilder, m: Massing) => void;
  pad?: number;
};

function lm(s: Spec): Landmark {
  const {m, draw, end, pad, ...rest} = s;
  return {
    ...rest,
    end: end ?? 9999,
    anchor: m.anchor,
    build: b => {
      b.frame(0, 0, 0, m.B, () => draw(b, m));
    },
    replaces: m.foot.map(r => toLocal(m.B, grow(r, pad ?? 1)))
  };
}

function stack(b: MeshBuilder, levels: Level[], zTop = Infinity) {
  for (const [z0, z1, ring] of levels) {
    if (z0 >= zTop) continue;
    b.prism(ring, z0, Math.min(z1, zTop), {bottom: z0 > 0});
  }
}

const WP = 'https://en.wikipedia.org/wiki/';
const OSM = 'https://www.openstreetmap.org/copyright';
const FOOT = 'https://data.cityofnewyork.us/City-Government/BUILDING/5zhs-2jue';
const CTBUH = 'https://www.skyscrapercenter.com/city/new-york-city';

// ---------------------------------------------------------------- One57
function drawOne57(b: MeshBuilder, m: Massing) {
  b.color('#6E8CA6');
  stack(b, m.levels, 306);
}

// ------------------------------------------------- Time Warner Center
function drawTWC(b: MeshBuilder, m: Massing) {
  b.color('#7E98AB');
  const lv = m.levels;
  // the curved base (mall, hotel, Jazz at Lincoln Center) and the two towers' stacks
  stack(b, lv, 230);
  // the two 55-storey towers end in 18 m lanterns (cited)
  b.color('#A9BAC5');
  b.prism(rect(11.7, -21, 22, 22), 230, 248, {});
  b.prism(rect(-21.8, 42.1, 22, 22), 230, 248, {});
}

// ------------------------------------------------------------ 53 West 53
function draw53(b: MeshBuilder, m: Massing) {
  const ring = m.foot[0];
  const vc = ring.reduce((a, p) => a + p[1], 0) / ring.length;
  b.color('#8D8A84');
  b.prism(ring, 0, 30, {});
  // the diagrid tower: north and south faces lean in, east and west faces stay vertical
  const zs = [30, 90, 150, 210, 270, 320];
  const f = (z: number) => 1 - 0.4 * ((z - 30) / 290);
  b.loft(zs.map(z => scaleV(ring, f(z), vc)), zs, {top: true});
}

// --------------------------------------------------- 35 Hudson Yards
function draw35HY(b: MeshBuilder, m: Massing) {
  b.color('#8FA2AD');
  stack(b, m.levels, 300);
  b.color('#6A7A84');
  b.prism(rect(10, 0, 40, 22), 300, 308, {});
}

// -------------------------------------------------------- The Plaza
function drawPlaza(b: MeshBuilder, m: Massing) {
  b.color('#E4DAC6');
  b.prism(m.foot[0], 0, 58, {});
  b.color('#4E7D6C'); // green tiled mansard, three storeys
  stack(b, m.levels);
}

// -------------------------------------------------------- Carnegie Hall
function drawCarnegie(b: MeshBuilder, m: Massing, withTower: boolean) {
  b.color('#B07A5A');
  b.prism(m.foot[0], 0, 34, {});
  if (withTower) {
    b.color('#A66F52');
    b.prism(rect(-11.5, -19.2, 22.8, 23), 34, 55.2, {});
  }
}

// -------------------------------------------------------- The Dakota
function drawDakota(b: MeshBuilder, m: Massing) {
  const hole = m.levels[0][2];
  b.color('#B8A074');
  b.prism(m.foot[0], 0, 36, {holes: [hole]});
  b.color('#4C5459');
  for (const [z0, z1, ring, h] of DAKOTA_ROOF) b.prism(ring, z0, z1, {holes: [h], bottom: true});
}

// ---------------------------------------------------------- The Ansonia
function drawAnsonia(b: MeshBuilder, m: Massing) {
  b.color('#DCD0B8');
  b.prism(m.foot[0], 0, 61, {});
  b.color('#40504A');
  stack(b, m.levels);
  // corner cupolas
  for (const [x, y] of m.foot[0]) {
    const k = 0.9;
    const cx = x + (x > 0 ? -3.2 : 3.2) * k;
    const cy = y + (y > 0 ? -3.2 : 3.2) * k;
    b.color('#DCD0B8');
    b.cylinder(cx, cy, 3.3, 61, 78, 12);
    b.color('#40504A');
    b.dome(cx, cy, 3.5, 78, 7.3, 12, 4);
  }
}

function rect(cx: number, cy: number, sx: number, sy: number): V2[] {
  return [[cx - sx / 2, cy - sy / 2], [cx + sx / 2, cy - sy / 2], [cx + sx / 2, cy + sy / 2], [cx - sx / 2, cy + sy / 2]];
}

const DAKOTA_ROOF: [number, number, V2[], V2[]][] = [
  [36, 42, [[-29.8, 29.8], [28.8, 29.8], [28.7, -6.5], [27.6, -6.5], [27.6, -18.0], [28.6, -18.0], [28.6, -30.1], [-29.7, -30.1], [-29.6, -16.7], [-27.4, -16.7], [-27.3, 16.3], [-29.8, 16.3]], [[-8.7, 6.7], [-13.0, 6.7], [-15.0, 12.9], [-12.7, 16.0], [13.7, 16.0], [13.7, 6.6], [7.3, 6.6], [7.2, -6.7], [13.6, -6.7], [13.6, -17.0], [-14.3, -17.0], [-14.3, -7.3], [-8.8, -7.3]]],
  [42, 47, [[-28.3, 17.8], [-28.3, 28.3], [27.3, 28.3], [27.2, -5.0], [26.1, -5.0], [26.1, -19.5], [27.1, -19.5], [27.1, -28.6], [-28.2, -28.6], [-28.1, -18.2], [-25.9, -18.2], [-25.8, 17.8]], [[-10.2, 5.2], [-14.1, 5.2], [-16.6, 13.1], [-13.4, 17.5], [15.2, 17.5], [15.2, 5.1], [8.8, 5.1], [8.7, -5.2], [15.1, -5.2], [15.1, -18.5], [-15.8, -18.5], [-15.8, -5.8], [-10.3, -5.8]]],
  [47, 50.9, [[-26.8, 19.3], [-26.8, 26.8], [25.8, 26.8], [25.7, -3.5], [24.6, -3.5], [24.6, -21.0], [25.6, -21.0], [25.6, -27.1], [-26.7, -27.1], [-26.6, -19.7], [-24.4, -19.7], [-24.3, 19.3]], [[-11.7, 3.7], [-15.2, 3.7], [-18.3, 13.4], [-14.2, 19.0], [16.7, 19.0], [16.7, 3.6], [10.3, 3.6], [10.2, -3.7], [16.6, -3.7], [16.6, -20.0], [-17.3, -20.0], [-17.3, -4.3], [-11.8, -4.3]]]
];

export const MORE_B: Landmark[] = [
  lm({
    id: 'one57',
    name: 'One57 (Carnegie 57)',
    kind: 'tower',
    built: [2009.3, 2014.62],
    m: M.one57,
    draw: drawOne57,
    facts: {
      Construction: '17 Apr 2009 – completed 13 Aug 2014',
      Height: '306 m (1,004 ft) to the roof',
      Floors: '73 above ground',
      Architects: 'Christian de Portzamparc; SLCE Architects (of record)',
      Model: 'plan from the city footprint; set-back levels from OpenStreetMap parts, capped at the cited roof; the curved cascade on 57th Street is drawn as steps; glazing colour estimated'
    },
    sources: [WP + 'One57', CTBUH, FOOT, OSM]
  }),
  lm({
    id: 'time_warner_center',
    name: 'Time Warner Center (Deutsche Bank Center)',
    kind: 'tower',
    built: [2000.85, 2004.1],
    m: M.twc,
    draw: drawTWC,
    facts: {
      Construction: '14 Nov 2000 – opened 5 Feb 2004',
      Height: '230 m (750 ft) to the roof, two towers with 18 m lanterns',
      Floors: '55 each',
      Architect: 'David Childs, Skidmore, Owings & Merrill',
      Model: 'curved base and tower plans from the city footprint and OpenStreetMap parts; the glass atrium and the Columbus Circle facade are not cut out; lantern size estimated'
    },
    sources: [WP + 'Deutsche_Bank_Center', CTBUH, FOOT, OSM]
  }),
  lm({
    id: 'w53',
    name: '53 West 53',
    kind: 'tower',
    built: [2014.9, 2020.12],
    m: M.w53,
    draw: draw53,
    facts: {
      Construction: 'late 2014 – completed Feb 2020',
      Height: '320 m (1,050 ft)',
      Floors: '77',
      Architects: 'Jean Nouvel; Adamson Associates (of record)',
      Model: 'plan from the city footprint; the 30 m base height and the lean (north and south faces taper to 60 % of the depth at the top) are estimated from photographs; diagrid and the five spires not drawn'
    },
    sources: [WP + '53_West_53', CTBUH, FOOT]
  }),
  lm({
    id: 'hudson_yards_35',
    name: '35 Hudson Yards',
    kind: 'tower',
    built: [2015.0, 2019.2],
    m: M.hy35,
    draw: draw35HY,
    facts: {
      Construction: '2015 – opened 15 Mar 2019',
      Height: '300 m (1,000 ft) to the roof; the city footprint measures 308 m with the rooftop mechanical',
      Floors: '72',
      Architect: 'David Childs, Skidmore, Owings & Merrill',
      Model: 'plan from the city footprint; three stepped levels from OpenStreetMap parts; the sloped faces and the Edge platform are not drawn; mechanical block estimated'
    },
    sources: [WP + '35_Hudson_Yards', CTBUH, FOOT, OSM]
  }),
  lm({
    id: 'plaza_hotel',
    name: 'The Plaza',
    kind: 'building',
    built: [1905.5, 1907.75],
    m: M.plaza,
    draw: drawPlaza,
    facts: {
      Construction: '1 Jul 1905 – opened 1 Oct 1907',
      Height: '76.8 m (252 ft) to the roof; the footprint file measures 85 m with the turrets',
      Floors: '18',
      Architect: 'Henry J. Hardenbergh',
      Model: 'plan from the city footprint; cornice at 58 m and the three-storey mansard stepped in, both estimated; turrets and dormers not drawn'
    },
    sources: [WP + 'The_Plaza_Hotel', 'https://s-media.nyc.gov/agencies/lpc/lp/0868.pdf', FOOT]
  }),
  lm({
    id: 'carnegie_hall_1891',
    name: 'Carnegie Hall (as opened, 1891–1894)',
    kind: 'building',
    built: [1889.4, 1891.35],
    end: 1894.5,
    m: M.carnegie,
    draw: (b, m) => drawCarnegie(b, m, false),
    facts: {
      Construction: 'excavation 1889, cornerstone 13 May 1890 – opened 5 May 1891',
      Height: 'eight storeys (about 34 m, estimated)',
      Architect: 'William B. Tuthill',
      Model: 'plan from the city footprint; one block, height estimated from eight storeys'
    },
    sources: [WP + 'Carnegie_Hall', FOOT]
  }),
  lm({
    id: 'carnegie_hall',
    name: 'Carnegie Hall',
    kind: 'building',
    built: [1894.0, 1896.5],
    m: M.carnegie,
    draw: (b, m) => drawCarnegie(b, m, true),
    facts: {
      Construction: 'hall 1889–91; studio tower at Seventh Avenue and 56th Street 1894–96',
      Height: '55 m (the city footprint) at the studio tower',
      Floors: '13 at the tower, 8 at the hall',
      Architect: 'William B. Tuthill',
      Model: 'plan and tower height from the city footprint; the position and plan of the tower on the south-west corner and the hall block height are estimated'
    },
    sources: [WP + 'Carnegie_Hall', 'https://s-media.nyc.gov/agencies/lpc/lp/0264.pdf', FOOT]
  }),
  lm({
    id: 'dakota',
    name: 'The Dakota',
    kind: 'building',
    built: [1880.8, 1884.8],
    m: M.dakota,
    draw: drawDakota,
    facts: {
      Construction: 'Oct 1880 – Oct 1884',
      Height: '56 m (185 ft) with finials; the model ends at the footprint file’s 50.9 m roof',
      Floors: '7 with gables and garrets',
      Architect: 'Henry J. Hardenbergh',
      Model: 'outline and courtyard from the city footprint; wall height (36 m) and the stepped roof are estimated; gables, turrets and dormers not drawn'
    },
    sources: [WP + 'The_Dakota', 'https://s-media.nyc.gov/agencies/lpc/lp/0071.pdf', FOOT]
  }),
  lm({
    id: 'ansonia',
    name: 'The Ansonia',
    kind: 'building',
    built: [1899.87, 1904.3],
    m: M.ansonia,
    draw: drawAnsonia,
    facts: {
      Construction: '15 Nov 1899 – hotel dedicated Apr 1904',
      Height: '85 m (the city footprint’s roof, with the cupolas)',
      Floors: '17',
      Architect: 'Paul E. Duboy',
      Model: 'plan and roof height from the city footprint; wall/mansard split and the four corner cupolas are estimated; the light courts and the rounded corner towers are not drawn'
    },
    sources: [WP + 'Ansonia_(Manhattan)', 'https://s-media.nyc.gov/agencies/lpc/lp/0951.pdf', FOOT]
  })
];
