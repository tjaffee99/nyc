/**
 * Long Island landmarks (Nassau and Suffolk counties): the country houses of the Gold Coast,
 * the lighthouses, Jones Beach's water tower, the Coliseum and the Big Duck.
 * Research and numeric checks: data/research/landmarks_ny_long_island.md.
 *
 * Conventions: the anchor is a point on the building. Plans are the Overture / OpenStreetMap
 * building outline (ODbL, (c) OpenStreetMap contributors) re-expressed in a model frame
 * (`b.frame(0, 0, 0, bearing)`, +y pointing at `bearing`); the frame's bearing and the roof
 * blocks are fitted to the outline by data/interim/landmarks_ny_long_island/decomp.py (the
 * largest axis-aligned rectangles that fit inside the outline). Heights are cited figures
 * where one exists; every other height, colour and roof is an estimate named in `Model:`.
 */
import {MeshBuilder, circle, type V2} from './kit';
import type {Landmark} from './types';

const WIKI = 'https://en.wikipedia.org/wiki/';
const OVERTURE = 'https://docs.overturemaps.org/guides/buildings/ (release 2026-10-21.0)';
const FT = 0.3048;

type Site = {bearing: number; ring: V2[]; rects: [number, number, number, number][]};

/** Outlines in the frame of their own bearing, metres around the anchor (see header). */
const SITES: Record<string, Site> = {
  oheka: {bearing: 27, ring: [[-0.8,-42.3],[0.3,-40.4],[18.6,-39.9],[18.7,-36.5],[41.6,-35.9],[41.7,-40.8],[50.3,-40.6],[50.0,-26.7],[41.4,-26.9],[41.0,-28.7],[18.6,-28.8],[17.2,28.0],[10.4,27.9],[10.3,32.8],[3.4,32.7],[3.4,28.3],[-4.4,28.2],[-4.4,30.8],[-9.4,30.7],[-9.3,27.0],[-26.2,26.8],[-26.2,14.9],[-18.8,14.9],[-19.2,4.5],[-21.2,4.6],[-21.4,-17.2],[-19.4,-17.3],[-19.4,-24.6],[-20.7,-24.4],[-20.3,-28.1],[-26.4,-28.2],[-26.3,-40.5],[-6.8,-40.0],[-6.2,-41.3],[-4.4,-42.8],[-2.4,-43.1]], rects: [[-0.9,-6.6,36.0,67.0],[33.6,-32.4,33.0,7.5],[-22.7,-34.1,7.5,12.0],[-22.7,20.9,7.5,12.0]]},
  hempstead: {bearing: 27, ring: [[-7.3,-23.0],[2.7,-23.0],[2.8,-11.8],[13.3,-11.8],[13.4,-3.0],[20.8,-3.0],[20.8,-9.7],[34.6,-9.8],[34.7,10.4],[21.9,10.5],[21.9,8.4],[6.9,8.4],[7.0,11.4],[-1.0,11.4],[-0.9,15.2],[-22.7,15.3],[-22.7,11.7],[-31.2,11.7],[-31.3,5.8],[-33.7,5.8],[-33.7,2.1],[-32.0,2.1],[-32.1,-4.8],[-33.8,-4.7],[-33.9,-9.0],[-32.3,-9.1],[-32.3,-15.6],[-7.3,-15.7]], rects: [[-14.4,-2.0,34.0,27.0],[18.6,2.7,32.0,11.5],[7.9,-7.5,10.5,9.0],[27.6,-6.3,14.0,6.5]]},
  gould: {bearing: 84, ring: [[22.9,21.0],[-5.2,21.0],[-5.1,42.1],[23.3,42.1],[23.3,60.3],[-22.5,60.3],[-22.6,8.0],[-23.8,6.5],[-24.3,4.5],[-23.7,2.7],[-22.9,1.7],[-21.9,1.2],[-20.4,1.2],[-18.9,2.0],[-17.9,1.7],[-17.5,1.0],[-15.9,1.4],[-14.9,2.8],[14.0,2.8],[10.3,-1.0],[9.9,-4.4],[11.8,-8.5],[13.3,-10.0],[13.3,-11.8],[7.8,-11.6],[6.3,-58.8],[5.3,-60.0],[5.4,-63.5],[9.4,-65.1],[12.8,-63.0],[22.7,-63.0]], rects: [[-13.8,31.7,17.0,57.5],[15.2,-37.3,15.0,51.5],[9.0,51.2,28.5,18.5],[8.7,11.9,28.0,18.0]]},
  coe: {bearing: 69, ring: [[-16.7,-25.5],[-17.1,-37.3],[-14.1,-37.6],[-12.9,-38.7],[-7.8,-38.9],[-8.1,-46.1],[0.9,-46.4],[1.2,-38.3],[1.6,-38.3],[1.8,-35.4],[3.2,-34.2],[3.4,-31.4],[2.0,-29.9],[2.1,-27.2],[0.2,-27.4],[0.4,-25.3],[-1.7,-22.7],[-3.7,-22.7],[-3.5,-6.5],[-0.2,-6.5],[2.1,-4.6],[15.9,-5.3],[16.8,-3.8],[16.7,-3.0],[15.8,-2.7],[15.9,-1.3],[16.9,-1.4],[17.3,2.9],[23.3,3.0],[23.4,4.7],[24.2,5.9],[24.3,7.2],[23.7,8.4],[23.9,10.0],[21.7,10.3],[21.8,11.6],[35.5,24.8],[31.9,29.1],[35.1,31.9],[30.8,37.0],[8.8,17.7],[9.8,15.4],[9.0,7.8],[-22.9,8.3],[-22.9,7.5],[-24.2,6.4],[-24.3,4.7],[-23.0,3.5],[-23.3,-2.6],[-15.8,-2.9],[-15.9,-3.8],[-17.3,-5.1],[-17.5,-7.5],[-16.1,-9.1],[-16.3,-12.0],[-17.7,-13.1],[-17.8,-15.9],[-16.5,-17.2],[-16.6,-20.2],[-18.0,-21.4],[-18.1,-24.2]], rects: [[-9.8,-14.7,12.0,45.5],[5.9,1.8,19.5,12.5],[15.9,13.6,11.5,11.0],[-1.3,-36.9,5.0,19.0]]},
  vanderbilt: {bearing: 114, ring: [[-18.2,-18.3],[-16.8,-18.5],[-18.7,-31.0],[10.0,-35.6],[11.2,-28.0],[19.9,-29.3],[20.2,-27.5],[28.0,-28.8],[28.5,-25.6],[27.3,-25.5],[27.6,-23.9],[27.0,-21.9],[28.2,-22.1],[28.7,-19.0],[23.0,-18.2],[23.9,-11.9],[31.9,-13.0],[33.7,0.3],[22.6,1.8],[23.6,10.0],[20.6,10.4],[21.1,13.9],[15.6,14.6],[15.2,11.8],[-3.9,14.5],[-3.3,19.2],[-6.1,19.6],[-5.1,26.3],[-7.4,26.6],[-7.2,28.0],[-22.8,30.3],[-24.5,18.7],[-14.5,17.2],[-16.6,2.6],[-18.2,2.9],[-20.0,-8.9],[-15.3,-9.6],[-15.7,-12.3],[-17.2,-12.1]], rects: [[3.5,-8.6,38.0,38.0],[-15.2,23.2,15.5,9.5],[27.3,-5.8,9.5,12.5]]},
  westbury: {bearing: 84, ring: [[-2.0,2.4],[-3.4,-27.6],[1.5,-27.8],[1.2,-35.3],[13.1,-35.8],[13.5,-27.0],[17.0,-27.1],[17.3,-19.1],[13.8,-19.0],[14.3,-6.7],[17.4,-6.8],[17.8,1.6],[13.3,1.8],[13.5,4.8],[14.8,4.7],[15.5,18.5],[10.0,18.7],[10.1,20.9],[6.4,21.1],[6.6,26.8],[7.3,26.7],[7.6,34.2],[-15.2,35.2],[-15.5,27.3],[-1.9,26.8],[-2.6,9.6],[-0.3,9.5],[-0.6,2.4]], rects: [[6.5,-4.5,14.0,46.5],[-3.8,30.7,22.5,7.0],[7.2,-31.5,11.5,7.5],[2.2,23.0,8.5,8.5]]},
  sagamore: {bearing: 87, ring: [[-17.9,-0.5],[-18.2,-12.5],[-7.7,-12.9],[-7.6,-9.8],[-3.8,-9.9],[-3.8,-18.3],[-0.0,-20.9],[4.8,-20.9],[6.2,-19.7],[12.2,-19.8],[12.5,-8.1],[18.2,-8.1],[18.2,-2.9],[12.9,-2.9],[12.9,4.1],[12.2,4.5],[12.2,6.6],[9.1,6.7],[9.0,5.1],[7.9,5.2],[7.8,20.0],[-1.4,20.2],[-1.5,4.4],[-4.2,4.5],[-4.3,-0.8]], rects: [[4.3,-6.9,16.0,23.0],[3.3,12.4,9.0,15.5],[-10.7,-5.4,14.0,9.0]]},
  coliseum: {bearing: 75, ring: [[65.1,-16.2],[68.1,-1.5],[73.5,-2.1],[72.9,7.9],[67.0,8.5],[63.4,22.1],[57.0,35.1],[49.6,42.3],[39.2,48.9],[28.1,52.2],[17.1,52.9],[-23.0,50.7],[-35.6,49.2],[-47.6,45.3],[-57.1,38.5],[-64.7,28.2],[-70.0,18.0],[-71.9,4.9],[-71.6,-8.4],[-68.6,-20.9],[-62.9,-30.8],[-54.4,-39.9],[-44.4,-47.1],[-31.5,-51.5],[29.5,-48.4],[38.8,-45.8],[45.8,-42.5],[55.6,-34.7],[63.0,-24.1]], rects: [[-2.4,0.5,105.0,80.0],[1.3,45.0,73.5,9.0],[-5.4,-44.0,71.0,9.0],[56.6,-0.5,13.0,48.0]]}
};

/** Frame ring -> anchor-local metres. */
function place(ring: V2[], bearing: number): V2[] {
  const a = (-bearing * Math.PI) / 180;
  const c = Math.cos(a);
  const s = Math.sin(a);
  return ring.map(([x, y]) => [c * x - s * y, s * x + c * y] as V2);
}

function centroidShift(ring: V2[], k: number): V2[] {
  let sx = 0;
  let sy = 0;
  for (const p of ring) {
    sx += p[0];
    sy += p[1];
  }
  sx /= ring.length;
  sy /= ring.length;
  return ring.map(([x, y]) => [sx + (x - sx) * k, sy + (y - sy) * k] as V2);
}

type HouseOpts = {
  wall: string;
  roof: string;
  eave: number;
  /** roof rise per block, in the order of the site's rects (0 = flat / none) */
  rise: number[];
  /** 'hip' or 'gable' per block (default hip) */
  gable?: boolean[];
  skip?: number[];
  extra?: (b: MeshBuilder) => void;
};

/** Walls of the whole outline to the eave, roofs over the fitted blocks, optional extras. */
function house(b: MeshBuilder, s: Site, o: HouseOpts, ring: V2[] = s.ring) {
  b.frame(0, 0, 0, s.bearing, () => {
    b.color(o.wall).prism(ring, 0, o.eave, {top: false});
    b.color(o.roof).cap(ring, o.eave);
    s.rects.forEach(([cx, cy, sx, sy], i) => {
      const h = o.rise[i] ?? 0;
      if (!h || o.skip?.includes(i)) return;
      b.color(o.wall).box(cx, cy, o.eave - 0.01, sx, sy, 0.02, {top: false});
      b.color(o.roof);
      if (o.gable?.[i]) b.gable(cx, cy, sx, sy, o.eave, h, sy >= sx);
      else b.hip(cx, cy, sx, sy, o.eave, h);
    });
    o.extra?.(b);
  });
}

export const NY_LONG_ISLAND: Landmark[] = [];

// ====================================================================== Oheka Castle
// Delano & Aldrich, 1914-1919, reinforced steel and concrete (Wikipedia; oheka.com). 109,000
// sq ft / 127 rooms (Wikipedia); the outline is 3,102 m2 (33,400 sq ft): 109,000 / 33,400 = 3.3
// full floors, which fixes the number of storeys at about 3 plus an attic.
NY_LONG_ISLAND.push({
  id: 'oheka_castle',
  name: 'Oheka Castle',
  kind: 'building',
  built: [1914, 1919],
  end: 9999,
  anchor: [-73.44849, 40.82902],
  build: (b) =>
    house(b, SITES.oheka, {wall: '#D9D0BC', roof: '#4E5358', eave: 15, rise: [7.5, 4, 4, 4], extra: (bb) => {
      // the main block's pavilion: a second, higher hip over the central 20 x 40 m
      bb.color('#D9D0BC').box(-0.9, -6.6, 15, 20, 40, 3, {top: false});
      bb.color('#4E5358').hip(-0.9, -6.6, 20, 40, 18, 5.5);
    }}),
  replaces: [place(SITES.oheka.ring, SITES.oheka.bearing)],
  facts: {
    Built: '1914-1919 for Otto Hermann Kahn (OHEKA = O-He-Ka)',
    Architects: 'Delano & Aldrich; grounds by Olmsted Brothers',
    Construction: 'reinforced steel and concrete, fireproof; 127 rooms, over 109,000 sq ft as built',
    Model: 'plan from the building outline (3,102 m2, OSM way via Overture); no height is published in the sources read, so the eave at 15 m (about three storeys, from 109,000 sq ft over the 33,400 sq ft outline) and the roofs (top 23.5 m) are estimated; the stone colour and slate roofs are estimated from photographs; the wings and pavilion are the outline\'s largest rectangles, not surveyed'
  },
  sources: [WIKI + 'Oheka_Castle', 'https://www.oheka.com/history', OVERTURE]
});

// ====================================================================== Sagamore Hill
// Lamb & Rich for Theodore Roosevelt, built May 1884 - March 1885 (22 rooms); C. Grant LaFarge's
// North Room, 40 x 30 ft (12.2 x 9.1 m), added 1905 (23 rooms). Overture's roof height 12 m, 3 floors.
const SAG_RING: V2[] = [[-1.5, 17.9], [-13.4, 17.5], [-13.3, 7.0], [-10.2, 7.0], [-10.1, 3.2], [-18.4, 2.8], [-20.8, -1.1], [-20.6, -5.8], [-19.3, -7.2], [-19.1, -13.2], [-7.4, -12.9], [-7.2, -18.6], [-2.0, -18.3], [-2.2, -13.0], [4.7, -12.7], [5.1, -11.9], [7.2, -11.9], [7.2, -8.8], [5.6, -8.7], [5.6, -7.6], [20.4, -6.7], [20.1, 2.5], [4.4, 1.7], [4.3, 4.5], [-1.0, 4.2]];
// without the North Room (x > 8 m): the east wall runs straight from (5.6, -7.6) to (4.4, 1.7)
const SAG_1885: V2[] = SAG_RING.filter((p) => !(p[0] > 8)).filter((p) => !(p[0] === 4.4 && p[1] === 1.7));
NY_LONG_ISLAND.push({
  id: 'sagamore_hill_1885',
  name: 'Sagamore Hill (as built, 1885)',
  kind: 'building',
  built: [1884.37, 1885.2],
  end: 1905,
  anchor: [-73.50107, 40.88558],
  build: (b) => {
    house(b, SITES.sagamore, {wall: '#6F5B47', roof: '#4B4F47', eave: 8, rise: [4, 0, 3.5]}, SITES.sagamore.ring.map(([x, y]) => [x, y] as V2).length ? SAG_1885.map((p) => frameOf(p, SITES.sagamore.bearing)) : []);
  },
  replaces: [SAG_1885],
  facts: {
    Built: 'May 1884 - March 1885, John A. Wood and Son of Lawrence, $16,975',
    Architects: 'Lamb & Rich (New York); Theodore Roosevelt\'s home from 1885',
    Rooms: '22',
    Model: 'outline = the present building outline without the North Room (the 40 x 30 ft room is the 12.2 x 9.1 m east wing of the outline); eave 8 m and roof ridge 12 m from Overture\'s 12 m roof height (3 floors), colours and roofs estimated; the piazza (porch) is not modelled'
  },
  sources: [WIKI + 'Sagamore_Hill', OVERTURE]
});
NY_LONG_ISLAND.push({
  id: 'sagamore_hill',
  name: 'Sagamore Hill',
  kind: 'building',
  built: [1905, 1905.5],
  end: 9999,
  anchor: [-73.50107, 40.88558],
  build: (b) => {
    house(b, SITES.sagamore, {wall: '#6F5B47', roof: '#4B4F47', eave: 8, rise: [4, 3, 3.5], gable: [false, false, false]}, SAG_RING.map((p) => frameOf(p, SITES.sagamore.bearing)));
  },
  replaces: [SAG_RING],
  facts: {
    'North Room': 'added 1905 (C. Grant LaFarge, $19,000), 40 x 30 ft; the house then had 23 rooms; now a National Historic Site',
    Model: 'plan from the building outline (746 m2); eave 8 m and ridge 12 m from Overture\'s 12 m roof height (3 floors); the month of the addition (1905) is not given, mid-year assumed; colours and roofs estimated; the piazza is not modelled'
  },
  sources: [WIKI + 'Sagamore_Hill', OVERTURE]
});

/** Anchor-local point -> frame of `bearing` (inverse of `place`). */
function frameOf(p: V2, bearing: number): V2 {
  const a = (bearing * Math.PI) / 180;
  const c = Math.cos(a);
  const s = Math.sin(a);
  return [c * p[0] - s * p[1], s * p[0] + c * p[1]];
}

// ====================================================================== lighthouses
/** Octagonal tower of apothem a0 -> a1 (flats facing the axes, as the outline's 8.2 x 8.3 m box) with lantern. */
function octagon(cx: number, cy: number, apothem: number): V2[] {
  const r = apothem / Math.cos(Math.PI / 8);
  const out: V2[] = [];
  for (let i = 0; i < 8; i++) {
    const a = Math.PI / 8 + (i * Math.PI) / 4;
    out.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]);
  }
  return out;
}

// Montauk Point Light: sandstone, 80 ft when lit in 1796 (Wikipedia), raised to 110 ft 6 in (33.68 m)
// in 1860 with two new levels and a larger lantern. Overture's outline of the base is 8.2 x 8.3 m
// (27 ft: matches the 28 ft base diameter in a lighthouse-history source) centred (-0.4, -0.3).
function montaukTower(b: MeshBuilder, total: number, walls: number, bands: boolean) {
  const cx = -0.4;
  const cy = -0.3;
  const a0 = 4.1;
  const a1 = 2.6;
  const rings = (z0: number, z1: number) => [octagon(cx, cy, a0 + (a1 - a0) * (z0 / walls)), octagon(cx, cy, a0 + (a1 - a0) * (z1 / walls))];
  const steps: [number, number, string][] = bands
    ? [[0, walls * 0.34, '#F1EEE6'], [walls * 0.34, walls * 0.62, '#8A4B35'], [walls * 0.62, walls, '#F1EEE6']]
    : [[0, walls, '#F1EEE6']];
  for (const [z0, z1, c] of steps) b.color(c).loft(rings(z0, z1), [z0, z1], {top: false});
  // gallery, lantern and roof
  b.color('#2B2B2B').cylinder(cx, cy, a1 + 0.9, walls, walls + 0.5, 8);
  b.color('#9FB5BD').cylinder(cx, cy, 1.7, walls + 0.5, total - 0.9, 8, {top: false});
  b.color('#2B2B2B').pyramid(circle(cx, cy, 1.9, 8), total - 0.9, [cx, cy, total]);
}
NY_LONG_ISLAND.push({
  id: 'montauk_point_light_1796',
  name: 'Montauk Point Light (1796 tower)',
  kind: 'tower',
  built: [1796.43, 1796.85],
  end: 1860,
  anchor: [-71.85709, 41.07098],
  build: (b) => montaukTower(b, 80 * FT, 80 * FT - 3.2, false),
  facts: {
    Built: 'authorised April 12, 1792; begun June 7, 1796, finished November 5, 1796; first lit April 1797',
    Height: '80 ft (24.4 m), octagonal sandstone pyramid on a 13 ft deep, 9 ft thick foundation; eight whale-oil lamps',
    Model: 'height cited; the 80 ft is taken to include the lantern (3.2 m, estimated); base from the outline (8.2 m across flats), top 5.2 m across flats and white paint estimated (the tower is described as originally all white)'
  },
  sources: [WIKI + 'Montauk_Point_Light', OVERTURE]
});
NY_LONG_ISLAND.push({
  id: 'montauk_point_light',
  name: 'Montauk Point Light',
  kind: 'tower',
  built: [1860, 1860.1],
  end: 9999,
  anchor: [-71.85709, 41.07098],
  build: (b) => montaukTower(b, 33.68, 33.68 - 4.4, true),
  facts: {
    Height: '110 ft 6 in (33.68 m); two levels and a larger lantern added in 1860 to the 80 ft tower; first-order Fresnel lens installed',
    Colour: 'white; a broad band midway (a single brown stripe was added in 1899; the infobox gives red)',
    Automated: 'February 3, 1987; the restored 3.5-order lens returned in November 2023',
    Model: 'height cited (the overall 33.68 m taken as top of the lantern roof, lantern 4.4 m estimated); base 8.2 m across flats from the outline; top width, the band\'s extent and colour estimated; the 1860 work is shown as complete on 1 January 1860 (the month is not given)'
  },
  sources: [WIKI + 'Montauk_Point_Light', OVERTURE]
});

// Fire Island Light: 168 ft (51 m), conical, brick encased in cement, first lit 1858; cream until
// black and white daymarks were painted in 1892 (NPS). Position: Wikipedia's coordinates.
function fireIsland(b: MeshBuilder, banded: boolean) {
  const H = 51.2;
  const base = 9.75 / 2;
  const top = 4.6 / 2;
  const shaft = H - 5.5;
  const r = (z: number) => base + (top - base) * (z / shaft);
  const bandsN = 4;
  for (let i = 0; i < (banded ? bandsN : 1); i++) {
    const z0 = banded ? (shaft * i) / bandsN : 0;
    const z1 = banded ? (shaft * (i + 1)) / bandsN : shaft;
    b.color(banded ? (i % 2 === 0 ? '#F2F0EA' : '#26282B') : '#E8DDBB').loft([circle(0, 0, r(z0), 20), circle(0, 0, r(z1), 20)], [z0, z1], {top: false});
  }
  b.color('#26282B').cylinder(0, 0, top + 1.0, shaft, shaft + 0.5, 20);
  b.color('#A8BCC4').cylinder(0, 0, 1.9, shaft + 0.5, H - 1.2, 12, {top: false});
  b.color('#26282B').pyramid(circle(0, 0, 2.2, 12), H - 1.2, [0, 0, H]);
}
const FIL_FACTS = {
  Height: '168 ft (51 m) tower, first-order Fresnel lens of 1856; focal plane 166 ft (NPS) above sea level',
  Model: 'height cited; base 32 ft and top 15 ft diameter from a historical marker (the same 32 ft base is given for the 1826 tower by NPS, so treat as unverified); anchor at the Wikipedia coordinates (the building outline does not include the tower); the lantern (5.5 m) and the order of the four bands (white at the bottom) are estimated'
};
NY_LONG_ISLAND.push({
  id: 'fire_island_light_1858',
  name: 'Fire Island Light (cream tower, 1858)',
  kind: 'tower',
  built: [1858, 1858.9],
  end: 1892,
  anchor: [-73.218583, 40.632444],
  build: (b) => fireIsland(b, false),
  facts: {...FIL_FACTS, Built: 'replaced the 74 ft tower of 1826; in service 1858; cream until 1892; the start of construction (1857) is not sourced here and 1858 is used'},
  sources: [WIKI + 'Fire_Island_Light', 'https://home.nps.gov/fiis/learn/historyculture/fire-island-lighthouse-history.htm']
});
NY_LONG_ISLAND.push({
  id: 'fire_island_light',
  name: 'Fire Island Light',
  kind: 'tower',
  built: [1892, 1892.1],
  end: 9999,
  anchor: [-73.218583, 40.632444],
  build: (b) => fireIsland(b, true),
  facts: {...FIL_FACTS, Colour: 'four black and white bands (daymarks painted 1892)'},
  sources: [WIKI + 'Fire_Island_Light', 'https://home.nps.gov/fiis/learn/historyculture/fire-island-lighthouse-history.htm']
});

// ====================================================================== Jones Beach water tower
// 188 ft (57 m), 1930, after the campanile of St Mark's, Venice (Wikipedia). Outline 8.4 x 8.8 m.
{
  const W = 188 * FT;
  const ring: V2[] = [[-5.0, 4.5], [-5.0, -4.3], [3.4, -4.3], [3.4, 4.5]];
  const c: V2 = [-0.8, 0.1];
  const frame = 84;
  NY_LONG_ISLAND.push({
    id: 'jones_beach_water_tower',
    name: 'Jones Beach Water Tower',
    kind: 'tower',
    built: [1930, 1930.9],
    end: 9999,
    anchor: [-73.50808, 40.59645],
    build: (b) => {
      b.frame(c[0], c[1], 0, frame, () => {
        const sq = (s: number) => [[-s / 2, -s / 2], [s / 2, -s / 2], [s / 2, s / 2], [-s / 2, s / 2]] as V2[];
        b.color('#B9643F').loft([sq(8.6), sq(7.2)], [0, 41], {top: false});
        b.color('#C9C2B0').box(0, 0, 41, 8, 8, 0.8);
        // belfry: four piers at the corners with open arches between
        b.color('#B9643F');
        for (const [x, y] of [[-3.1, -3.1], [3.1, -3.1], [3.1, 3.1], [-3.1, 3.1]]) b.box(x, y, 41.8, 1.8, 1.8, 6);
        b.color('#C9C2B0').box(0, 0, 47.8, 8, 8, 0.7);
        b.color('#4C8A6B').pyramid(sq(7.6), 48.5, [0, 0, W]);
      });
    },
    replaces: [ring],
    facts: {
      Built: '1930, for the Long Island State Park Commission (Robert Moses)',
      Height: '188 ft (57 m); an Italianate tower modelled on the bell tower of St Mark\'s Basilica, Venice; restored 2010',
      Model: 'height cited (Overture\'s 70.5 m is not used: it disagrees with the cited 57 m); plan 8.6 m square at the base from the 8.4 x 8.8 m outline; brick colour, taper, belfry and the copper-green spire are estimated from the Venice model'
    },
    sources: [WIKI + 'Jones_Beach_State_Park', OVERTURE]
  });
}

// ====================================================================== Gold Coast houses
NY_LONG_ISLAND.push({
  id: 'westbury_house',
  name: 'Westbury House (Old Westbury Gardens)',
  kind: 'building',
  built: [1903, 1906],
  end: 9999,
  anchor: [-73.59478, 40.77377],
  build: (b) => house(b, SITES.westbury, {wall: '#9C5B44', roof: '#43474B', eave: 9.5, rise: [4.5, 3.5, 3.5, 3.5]}),
  replaces: [place(SITES.westbury.ring, SITES.westbury.bearing)],
  facts: {
    Built: 'estate begun 1903, house ready 1906, for John S. Phipps',
    Architect: 'George A. Crawley with Grosvenor Atterbury; Carolean Revival (Charles II style), 23 rooms',
    Model: 'plan from the building outline (1,174 m2); the storeys, eave 9.5 m, roofs and the red brick are estimated (no height read in the sources; Overture\'s 6.7 m is a terrain-derived value and is not used); the wings are the outline\'s largest rectangles'
  },
  sources: [WIKI + 'Old_Westbury_Gardens', OVERTURE]
});

NY_LONG_ISLAND.push({
  id: 'hempstead_house',
  name: 'Hempstead House (Sands Point)',
  kind: 'building',
  built: [1901, 1912],
  end: 9999,
  anchor: [-73.70074, 40.86328],
  build: (b) =>
    house(b, SITES.hempstead, {wall: '#CFC7B3', roof: '#4B5257', eave: 12.3, rise: [5.5, 4.5, 0, 3.5], extra: (bb) => {
      // the tower (80 ft = 24.4 m, placed on the block at the outline's south-west bump)
      bb.color('#CFC7B3').box(-2.3, -19.3, 12.3, 8.4, 6.6, 8.4);
      bb.color('#4B5257').hip(-2.3, -19.3, 8.4, 6.6, 20.7, 3.7);
    }}),
  replaces: [place(SITES.hempstead.ring, SITES.hempstead.bearing)],
  facts: {
    Built: 'begun after Howard Gould bought the land in 1900; finished by 1912 for Daniel Guggenheim (Wikipedia is inconsistent: 1909 in the infobox, 1917 for the sale)',
    Size: 'about 225 ft long, 135 ft wide, three floors, 40 rooms, an 80 ft tower (Wikipedia); the outline measures 68 x 38 m = 224 x 125 ft',
    Model: 'plan from the building outline (1,700 m2, which matches the 225 ft length); eave at Overture\'s measured 12.3 m; the tower stands at the outline\'s south-west bump by assumption (its place is not documented); roofs, colour and the start year 1901 are estimated'
  },
  sources: [WIKI + 'Sands_Point_Preserve', OVERTURE]
});
NY_LONG_ISLAND.push({
  id: 'castle_gould',
  name: 'Castle Gould (Sands Point)',
  kind: 'building',
  built: [1901, 1909],
  end: 9999,
  anchor: [-73.69782, 40.8612],
  build: (b) => house(b, SITES.gould, {wall: '#B8B09D', roof: '#4B5257', eave: 12.2, rise: [4.5, 4.5, 4, 4]}),
  replaces: [place(SITES.gould.ring, SITES.gould.bearing)],
  facts: {
    Note: 'the castellated stables and servants\' quarters of the Gould estate, built of limestone; still called Castle Gould',
    Model: 'LOW confidence: plan from the building outline (3,030 m2, an L-shaped courtyard range); eave at Overture\'s measured 12.2 m; the dates (1901-1909, the estate\'s start and the infobox year) and the roofs are estimates; no towers or battlements are modelled'
  },
  sources: [WIKI + 'Sands_Point_Preserve', OVERTURE]
});

NY_LONG_ISLAND.push({
  id: 'coe_hall',
  name: 'Coe Hall (Planting Fields)',
  kind: 'building',
  built: [1918.3, 1921],
  end: 9999,
  anchor: [-73.55736, 40.8649],
  build: (b) => house(b, SITES.coe, {wall: '#C9C1AC', roof: '#4C5156', eave: 11, rise: [6, 5, 5, 4], gable: [true, true, true, true]}),
  replaces: [place(SITES.coe.ring, SITES.coe.bearing)],
  facts: {
    Built: '1918-1921 for William Robertson Coe, after the first house burned on March 19, 1918',
    Architect: 'Walker & Gillette; Tudor Revival, faced in Indiana limestone; 67 rooms',
    Model: 'plan from the building outline (1,544 m2); no height is published in the sources read (Overture\'s 7 m is not used): eave 11 m and gabled roofs to 16-17 m estimated; the wings are the outline\'s largest rectangles, not surveyed; no chimneys or half-timbering'
  },
  sources: [WIKI + 'Planting_Fields_Arboretum', OVERTURE]
});

NY_LONG_ISLAND.push({
  id: 'vanderbilt_eagles_nest',
  name: 'Eagle\'s Nest (Vanderbilt Museum)',
  kind: 'building',
  built: [1910, 1936],
  end: 9999,
  anchor: [-73.36877, 40.90648],
  build: (b) => house(b, SITES.vanderbilt, {wall: '#E6D9BD', roof: '#B4573C', eave: 8.5, rise: [4.5, 3.5, 3.5]}),
  replaces: [place(SITES.vanderbilt.ring, SITES.vanderbilt.bearing)],
  facts: {
    Built: 'three phases, 1910-1936, for William K. Vanderbilt II (Warren & Wetmore)',
    Style: '24-room Spanish Revival mansion; now the Suffolk County Vanderbilt Museum (the planetarium of 1971 is a separate building)',
    Model: 'the 1936 plan from the building outline (2,264 m2) shown from 1910 (the phases are not dated separately here); height, stucco colour and tiled roofs estimated (no height in the sources read); no tower is modelled'
  },
  sources: [WIKI + 'Vanderbilt_Museum', OVERTURE]
});

// ====================================================================== Nassau Veterans Memorial Coliseum
NY_LONG_ISLAND.push({
  id: 'nassau_coliseum',
  name: 'Nassau Veterans Memorial Coliseum',
  kind: 'stadium',
  built: [1969.05, 1972.12],
  end: 9999,
  anchor: [-73.59071, 40.72287],
  build: (b) => {
    const s = SITES.coliseum;
    b.frame(0, 0, 0, s.bearing, () => {
      b.color('#B9B4AA').prism(s.ring, 0, 20, {top: false});
      b.color('#6E7378').cap(s.ring, 20);
      b.color('#8C9196').loft([s.ring, centroidShift(s.ring, 0.8)], [20, 23], {top: false});
      b.color('#6E7378').cap(centroidShift(s.ring, 0.8), 23);
    });
  },
  replaces: [place(SITES.coliseum.ring, SITES.coliseum.bearing)],
  facts: {
    Built: 'groundbreaking January 20, 1969; opened February 11, 1972; $32 million',
    Team: 'Welton Becket and Associates (architect), Severud Associates (structure), Irwin Schlef (contractor)',
    Capacity: 'about 16,000 for concerts, 14,500 for basketball, 13,900 for ice hockey (13,917 after the 2015-2017 renovation)',
    Model: 'LOW confidence: plan from the building outline (12,291 m2); no height was found in the sources read, so the 20 m wall and 23 m roof are estimated; the 2015-2017 aluminium-fin facade is not modelled (the model shows the original concrete drum)'
  },
  sources: [WIKI + 'Nassau_Veterans_Memorial_Coliseum', OVERTURE]
});

// ====================================================================== Big Duck
// 15 x 30 ft in plan, 20 ft high to the head (Wikipedia); ferrocement on a wooden frame, built
// in Riverhead 1931, moved to Flanders in 1937, to Sears Bellows County Park in 1988 and back to
// Flanders on October 6, 2007. The Riverhead and Sears Bellows sites are not modelled.
function bigDuck(b: MeshBuilder) {
  b.frame(-1, 0, 0, 61, () => {
    const body = (z: number) => {
      const t = Math.min(Math.max((z - 0.3) / 3.2, 0), 1);
      const k = Math.sqrt(Math.max(1 - Math.pow(2 * t - 1, 2) * 0.85, 0.05));
      return circle(0, 0, 1, 14, 2.3 * k, 3.4 * k);
    };
    const zs = [0.3, 0.9, 1.8, 2.7, 3.5];
    b.color('#F2F0E8').loft(zs.map(body), zs, {top: true});
    // tail
    b.pyramid(circle(0, -3.1, 1.0, 6, 1.4, 1.0), 1.4, [0, -4.55, 3.6]);
    // neck and head
    b.frustum(0, 2.7, 1.3, 0.9, 2.8, 5.0, 10);
    b.frustum(0, 3.0, 0.95, 0.85, 4.8, 6.1, 10);
    b.color('#E39A2D').box(0, 4.3, 5.0, 1.0, 1.5, 0.5);
    b.color('#B3261E').box(-0.8, 3.2, 5.6, 0.25, 0.25, 0.25).box(0.8, 3.2, 5.6, 0.25, 0.25, 0.25);
  });
}
const DUCK_FACTS = {
  Size: '15 x 30 ft in plan (4.6 x 9.1 m), 20 ft (6.1 m) to the top of the head; wooden frame, wire mesh and four coats of cement (ferrocement); eyes are Ford Model T tail lights',
  Model: 'overall size cited; the body, neck and beak proportions are estimated from photographs and the direction the duck faces (here east-north-east along the outline\'s long axis) is assumed; the outline (7.7 x 4.7 m) is smaller than the cited 9.1 x 4.6 m, so the cited size is used'
};
NY_LONG_ISLAND.push({
  id: 'big_duck_1937',
  name: 'The Big Duck (Flanders, 1937-1988)',
  kind: 'building',
  built: [1937, 1937.1],
  end: 1988,
  anchor: [-72.62238, 40.9072],
  build: bigDuck,
  facts: {...DUCK_FACTS, History: 'built 1931 by Martin Maurer in Riverhead (Upper Mills); moved about four miles to his duck ranch in Flanders in 1937; his store closed in 1984; Suffolk County Parks took it in 1988'},
  sources: [WIKI + 'Big_Duck', OVERTURE]
});
NY_LONG_ISLAND.push({
  id: 'big_duck',
  name: 'The Big Duck (Flanders)',
  kind: 'building',
  built: [2007.76, 2007.77],
  end: 9999,
  anchor: [-72.62238, 40.9072],
  build: bigDuck,
  facts: {...DUCK_FACTS, History: 'returned to Flanders on October 6, 2007 after 1988-2007 at Sears Bellows County Park; a gift shop and Long Island icon'},
  sources: [WIKI + 'Big_Duck', OVERTURE]
});
