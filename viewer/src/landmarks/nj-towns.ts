/**
 * Trenton and New Brunswick, New Jersey: landmarks added in the towns round (2026-11-11, second pass).
 * Research, sources, ids of the footprints and numeric checks: data/research/towns_nj.md.
 *
 * Conventions as princeton.ts: the anchor is a point inside the footprint; plans are the real outlines
 * of data/interim/counties/nj_mercer.parquet (Trenton) and nj_middlesex.parquet (New Brunswick)
 * (Overture / OpenStreetMap, ODbL) re-expressed in anchor-local metres (x east, y north). Heights are
 * cited figures where the note gives one; otherwise estimates, named in each model's `Model:` fact.
 */
import {MeshBuilder, circle, lngLatToLocal, type V2} from './kit';
import type {Landmark} from './types';

const WIKI = 'https://en.wikipedia.org/wiki/';
const OVERTURE = 'https://docs.overturemaps.org/guides/buildings/';

export const NJ_TOWNS: Landmark[] = [];

function P(...n: number[]): V2[] {
  const o: V2[] = [];
  for (let i = 0; i < n.length; i += 2) o.push([n[i], n[i + 1]]);
  return o;
}

type Obb = {cx: number; cy: number; bearing: number; L: number; W: number};

/** Smallest oriented rectangle: centre, long-axis bearing (deg from north, 0-180), length, width. */
function obb(r: V2[]): Obb {
  let best = {area: Infinity, cx: 0, cy: 0, bearing: 0, L: 0, W: 0};
  for (let a = 0; a < 180; a += 0.5) {
    const t = (a * Math.PI) / 180;
    const c = Math.cos(t);
    const s = Math.sin(t);
    let u0 = Infinity;
    let u1 = -Infinity;
    let v0 = Infinity;
    let v1 = -Infinity;
    for (const [x, y] of r) {
      const u = x * c + y * s;
      const v = -x * s + y * c;
      u0 = Math.min(u0, u);
      u1 = Math.max(u1, u);
      v0 = Math.min(v0, v);
      v1 = Math.max(v1, v);
    }
    const area = (u1 - u0) * (v1 - v0);
    if (area < best.area) {
      const um = (u0 + u1) / 2;
      const vm = (v0 + v1) / 2;
      const long = u1 - u0 >= v1 - v0;
      const ax = long ? c : -s;
      const ay = long ? s : c;
      best = {
        area,
        cx: um * c - vm * s,
        cy: um * s + vm * c,
        bearing: ((Math.atan2(ax, ay) * 180) / Math.PI + 360) % 180,
        L: Math.max(u1 - u0, v1 - v0),
        W: Math.min(u1 - u0, v1 - v0)
      };
    }
  }
  return best;
}

/** Signed distance from a point to a ring's edges: positive inside. */
function clearance(r: V2[], x: number, y: number): number {
  let inside = false;
  let d = Infinity;
  for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
    const [ax, ay] = r[j];
    const [bx, by] = r[i];
    if (by > y !== ay > y && x < ((ax - bx) * (y - by)) / (ay - by) + bx) inside = !inside;
    const ex = bx - ax;
    const ey = by - ay;
    const t = Math.max(0, Math.min(1, ((x - ax) * ex + (y - ay) * ey) / (ex * ex + ey * ey)));
    d = Math.min(d, Math.hypot(x - ax - t * ex, y - ay - t * ey));
  }
  return inside ? d : -d;
}

/** Frame point -> world. */
function toWorld(o: Obb, x: number, y: number): V2 {
  const b = (o.bearing * Math.PI) / 180;
  return [o.cx + x * Math.cos(b) + y * Math.sin(b), o.cy - x * Math.sin(b) + y * Math.cos(b)];
}

/** The point of the box frame (x, y) with the most room inside `r`, among those `ok` accepts. Returns frame x, y and clearance. */
function roomiest(r: V2[], o: Obb, ok: (x: number, y: number) => boolean = () => true, holes: V2[][] = []): [number, number, number] {
  let best: [number, number, number] = [0, 0, -Infinity];
  for (let y = -o.L / 2; y <= o.L / 2; y += 1) {
    for (let x = -o.W / 2; x <= o.W / 2; x += 1) {
      if (!ok(x, y)) continue;
      const [wx, wy] = toWorld(o, x, y);
      let d = clearance(r, wx, wy);
      for (const h of holes) d = Math.min(d, -clearance(h, wx, wy));
      if (d > best[2]) best = [x, y, d];
    }
  }
  return best;
}

/** Ring walls + flat roof. */
function block(b: MeshBuilder, ring: V2[], z0: number, z1: number, wall: string, roof = wall, holes: V2[][] = []) {
  b.color(wall).prism(ring, z0, z1, {top: false, holes});
  b.color(roof).cap(ring, z1, holes);
}

/** Cone-ish spire: a regular n-gon pyramid. */
function spire(b: MeshBuilder, cx: number, cy: number, r: number, z0: number, apexZ: number, n = 8) {
  b.pyramid(circle(cx, cy, r, n), z0, [cx, cy, apexZ]);
}

/** Parabolic barrel vault over a rectangle in the current frame (axis along y), eave at z0, rise at the crown. */
function vault(b: MeshBuilder, cx: number, cy: number, w: number, len: number, z0: number, rise: number, n = 6) {
  const xs: number[] = [];
  for (let i = 0; i <= n; i++) xs.push(-w / 2 + (w * i) / n);
  const zOf = (x: number) => z0 + rise * (1 - Math.pow((2 * x) / w, 2));
  for (let i = 0; i < n; i++) {
    const a = xs[i];
    const c = xs[i + 1];
    b.quad([cx + a, cy - len / 2, zOf(a)], [cx + c, cy - len / 2, zOf(c)], [cx + c, cy + len / 2, zOf(c)], [cx + a, cy + len / 2, zOf(a)]);
    for (const s of [-1, 1]) {
      const y = cy + (s * len) / 2;
      b.quad([cx + a, y, z0], [cx + c, y, z0], [cx + c, y, zOf(c)], [cx + a, y, zOf(a)]);
    }
  }
}

/** A row of columns along the x axis of the current frame at y, from x0 to x1. */
function colonnade(b: MeshBuilder, x0: number, x1: number, y: number, z0: number, z1: number, n: number, r: number) {
  for (let i = 0; i < n; i++) {
    const x = n === 1 ? (x0 + x1) / 2 : x0 + ((x1 - x0) * i) / (n - 1);
    b.cylinder(x, y, r, z0, z1, 8, {top: false});
    b.box(x, y, z1, r * 2.8, r * 2.8, 0.5);
  }
}

/** Extent of a ring along the compass bearing `bear` (deg from north) measured from (cx, cy): [min, max] of the projection. */
function extent(r: V2[], cx: number, cy: number, bear: number): [number, number] {
  const t = (bear * Math.PI) / 180;
  let lo = Infinity;
  let hi = -Infinity;
  for (const [x, y] of r) {
    const d = (x - cx) * Math.sin(t) + (y - cy) * Math.cos(t);
    lo = Math.min(lo, d);
    hi = Math.max(hi, d);
  }
  return [lo, hi];
}

/** World point -> box frame (inverse of toWorld). */
function toFrame(o: Obb, wx: number, wy: number): V2 {
  const b = (o.bearing * Math.PI) / 180;
  const dx = wx - o.cx;
  const dy = wy - o.cy;
  return [dx * Math.cos(b) - dy * Math.sin(b), dx * Math.sin(b) + dy * Math.cos(b)];
}


/** Shrink a w x l box centred at frame (x, y) until its corners lie inside the ring `r`. */
function fit(r: V2[], o: Obb, x: number, y: number, w: number, l: number): [number, number] {
  for (let k = 0; k < 60; k++) {
    let ok = true;
    for (const sx of [-1, 1]) {
      for (const sy of [-1, 1]) {
        const [wx, wy] = toWorld(o, x + (sx * w) / 2, y + (sy * l) / 2);
        if (clearance(r, wx, wy) < -0.2) ok = false;
      }
    }
    if (ok) return [w, l];
    w *= 0.96;
    l *= 0.96;
  }
  return [w, l];
}
const HUGHES = P(47.6, -56.9, 35.9, 73.7, 2.9, 34.0, 4.3, 18.5, -5.6, 17.7, -6.3, 23.4, -44.3, 20.0, -40.8, -18.3, -34.3, -17.7, -34.1, -27.2, -49.6, -28.7, -83.6, -69.1);
const HUGHES_ANCHOR: V2 = [-74.763942, 40.213673];
const STMARY = P(27.9, 7.8, 28.6, 14.7, 22.4, 15.3, 22.3, 14.0, 3.8, 15.9, 4.1, 18.1, -12.4, 19.8, -12.6, 17.6, -30.9, 19.6, -30.7, 21.3, -36.9, 22.0, -39.4, -1.1, -33.4, -1.7, -33.1, 0.8, -17.9, -0.8, -18.2, -3.3, 1.1, -5.3, 1.4, -2.7, 15.9, -4.2, 15.0, -12.8, 2.3, -11.5, 1.3, -21.1, 23.1, -23.4, 26.4, 7.9);
const STMARY_ANCHOR: V2 = [-74.765989, 40.222639];
const BANK = P(8.0, 52.2, -24.0, 47.4, -11.5, -21.8, 18.0, -17.4);
const BANK_ANCHOR: V2 = [-74.762041, 40.219782];
const COURTHOUSE = P(18.9, 1.9, -16.0, 44.8, -40.2, 26.4, -18.3, -1.9, -40.7, -19.6, -20.6, -43.7, 18.4, -14.0, 21.0, -9.0, 21.4, -3.1);
const COURTHOUSE_ANCHOR: V2 = [-74.763796, 40.217039];
const CITYHALL = P(30.8, 16.4, -33.2, 5.8, -32.2, 0.2, -34.5, -0.2, -32.9, -9.8, -30.6, -9.4, -29.5, -16.3, -15.9, -14.0, -16.7, -9.4, -7.2, -7.9, -6.5, -11.8, -2.7, -11.2, -2.3, -13.4, 8.2, -11.7, 7.9, -9.9, 12.4, -9.2, 11.8, -5.4, 21.3, -3.9, 21.9, -7.3, 34.3, -5.3, 33.3, 0.9, 34.8, 1.1, 33.4, 9.8, 31.9, 9.6);
const CITYHALL_ANCHOR: V2 = [-74.758899, 40.220343];
const ROEBLING = P(40.0, -12.6, 52.4, -9.6, 41.6, 33.8, -52.4, 9.5, -39.3, -43.3, -14.4, -37.1, -10.7, -51.8, 33.8, -40.8, 30.6, -28.2, 43.1, -25.0);
const ROEBLING_ANCHOR: V2 = [-74.753578, 40.209743];
const CURE = P(30.6, 55.1, -56.5, 24.6, -55.6, 22.0, -61.1, 10.6, -64.7, 9.5, -46.9, -44.8, -44.0, -43.8, -32.6, -49.3, -31.3, -53.1, 57.2, -23.5, 56.1, -20.1, 60.6, -10.8, 64.9, -9.4, 46.3, 45.4, 42.8, 44.3, 32.3, 50.1);
const CURE_ANCHOR: V2 = [-74.757587, 40.212692];
const JJ = P(-49.7, -27.3, -55.5, -24.0, -44.5, -59.8, -32.8, -55.3, -26.9, -58.5, -26.0, -61.1, -23.4, -60.2, -16.5, -63.3, -20.1, -52.0, -9.7, -48.6, -4.1, -51.3, -3.2, -54.0, -0.3, -53.0, 6.4, -56.2, 2.6, -44.7, 13.2, -41.3, 19.4, -43.1, 20.5, -46.9, 23.2, -45.8, 28.9, -48.0, 40.1, -45.3, 44.1, -57.3, 57.9, -52.7, 60.1, -50.2, 59.6, -44.5, 64.8, -43.9, 59.8, -26.7, 40.5, -31.4, 42.4, -35.8, 26.2, -40.8, 5.8, 20.9, 17.8, 24.8, 24.0, 21.5, 24.7, 18.9, 27.8, 19.9, 33.1, 16.8, 25.7, 40.0, 37.9, 43.6, 43.6, 40.5, 44.9, 37.5, 47.9, 38.8, 53.2, 35.5, 45.9, 58.9, 57.5, 62.2, 63.1, 59.5, 63.8, 56.3, 67.0, 57.4, 72.6, 54.1, 61.7, 88.7, 50.0, 85.1, 43.8, 88.3, 43.1, 91.0, 40.4, 90.4, 34.7, 93.7, 41.6, 69.9, 30.5, 67.2, 24.7, 69.6, 24.0, 72.5, 21.6, 71.2, 15.5, 74.2, 22.3, 51.6, 11.3, 47.8, 4.9, 50.8, 4.6, 53.5, 1.7, 52.4, -4.6, 55.5, 3.4, 32.6, -8.2, 29.1, -14.5, 31.8, -15.3, 34.7, -18.1, 33.5, -24.4, 37.1, -5.6, -21.8, -16.5, -25.0, -23.1, -21.9, -23.8, -19.1, -26.8, -19.9, -32.5, -16.7, -28.6, -28.7, -38.9, -32.4, -45.5, -29.8, -46.9, -26.6);
const JJ_ANCHOR: V2 = [-74.443092, 40.497888];
const NBPAC = P(-37.6, -3.3, 0.1, -33.9, 38.5, 3.2, 18.9, 20.0, 5.5, 30.1, -14.7, 26.1);
const NBPAC_ANCHOR: V2 = [-74.444369, 40.493611];
const GATEWAY = P(2.9, 41.8, -45.8, 21.8, -46.9, 16.9, 20.8, -45.6, 27.3, -38.6, 27.8, -39.0, 34.0, -32.8, 33.6, -32.3, 41.5, -23.6, 36.6, -11.3, 26.5, -1.8, 30.2, 1.8, 13.3, 44.3, 3.4, 40.1);
const GATEWAY_ANCHOR: V2 = [-74.446931, 40.497213];
const KIRKPATRICK = P(0.2, -11.4, 1.4, -14.4, 8.5, -11.5, 7.3, -8.8, 11.7, -7.0, -1.5, 25.6, -16.7, 19.4, -3.6, -13.0);
const KIRKPATRICK_ANCHOR: V2 = [-74.445817, 40.498872];
const WINANTS = P(-0.0, 23.3, -18.4, 15.2, -12.4, 1.5, -13.2, 1.2, -8.0, -10.6, -6.8, -10.1, -0.6, -24.2, 4.5, -22.0, 6.2, -22.4, 8.8, -22.0, 10.9, -20.4, 11.7, -18.8, 18.0, -16.1, 11.7, -1.8, 13.1, -1.2, 8.1, 10.3, 6.1, 9.4);
const WINANTS_ANCHOR: V2 = [-74.4468, 40.498209];
const STATETHEATRE = P(36.0, -13.5, -6.4, 21.8, -4.4, 24.1, -10.8, 29.4, -16.3, 26.9, -19.8, 34.5, -45.0, 22.9, -41.9, 16.4, -44.9, 15.0, -37.2, -1.7, -31.6, 5.0, -27.5, 1.7, -25.2, 4.5, 19.8, -32.8);
const STATETHEATRE_ANCHOR: V2 = [-74.444746, 40.493345];
const VOORHEES = P(-9.6, 0.2, -7.1, -6.1, -12.4, -8.1, -1.3, -36.4, 5.0, -34.0, 6.6, -39.5, 23.3, -32.6, 19.8, -24.5, 25.5, -22.5, 24.9, -20.5, 15.8, 2.3, 9.6, -0.3, 6.6, 9.2, 5.4, 8.9, 0.8, 20.1, 2.0, 20.6, 1.8, 21.4, 6.7, 23.2, 0.0, 39.4, -4.7, 37.6, -5.1, 38.2, -10.4, 35.7, -11.1, 37.5, -21.9, 32.7, -24.5, 33.9, -26.9, 32.9, -27.8, 30.5, -25.8, 24.8, -27.1, 24.1, -28.3, 21.3, -26.2, 15.8, -23.5, 14.7, -22.2, 15.2, -16.2, -0.5, -13.8, -1.6);
const VOORHEES_ANCHOR: V2 = [-74.446292, 40.500016];

// ====================================================================== TRENTON
// ---------------------------------------------------------------------- Richard J. Hughes Justice Complex
{
  const o = obb(HUGHES);
  NJ_TOWNS.push({
    id: 'trn_hughes_justice',
    name: 'Richard J. Hughes Justice Complex',
    kind: 'building',
    built: [1979.5, 1982.5],
    end: 9999,
    anchor: HUGHES_ANCHOR,
    build: b => {
      block(b, HUGHES, 0, 30, '#A9A294', '#6E6A64');
      b.color('#8C877E').prism(HUGHES, 30, 30.9, {top: false});
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // the cube that holds the court, rising out of the two eight-storey office wings
        const [x, y, d] = roomiest(HUGHES, o);
        const h = Math.min(d * 0.92, 21);
        b.color('#B9B2A4').box(x, y, 30, 2 * h, 2 * h, 41.62 - 30);
        b.color('#6E6A64').box(x, y, 41.55, 2 * h - 1, 2 * h - 1, 0.07);
      });
    },
    replaces: [HUGHES],
    facts: {
      Built: 'completed and dedicated 1982 (the Justice Center complex); modernist, eleven storeys, about 1,080,000 sq ft; two eight-storey office buildings around a cube that houses the court, an atrium lobby open through ten storeys',
      Model: 'plan is the real outline (Overture, 9,192 m2); the date, the eleven storeys and the height of 41.62 m (the cube) are cited; the 30 m of the office wings, the cube\'s side and its position (the roomiest point of the plan) and the colours are estimated; construction start (1979.5) is an estimate'
    },
    sources: [WIKI + 'Richard_J._Hughes_Justice_Complex', OVERTURE]
  });
}

// ---------------------------------------------------------------------- Cathedral of St. Mary of the Assumption
{
  const o = obb(STMARY);
  NJ_TOWNS.push({
    id: 'trn_st_mary_cathedral',
    name: 'Cathedral of St. Mary of the Assumption',
    kind: 'building',
    built: [1957, 1959.2],
    end: 9999,
    anchor: STMARY_ANCHOR,
    build: b => {
      block(b, STMARY, 0, 10.5, '#B9A58B', '#7A6F63');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // nave under a gable roof; a modern Romanesque bell tower at the front end
        const [gw, gl] = fit(STMARY, o, 0, -o.L * 0.06, o.W * 0.72, o.L * 0.74);
        b.color('#7A6F63').gable(0, -o.L * 0.06, gw, gl, 10.5, 5.5, true);
        const [tx, ty, td] = roomiest(STMARY, o, (_x, y) => y > o.L * 0.22);
        const ts = Math.min(6.6, td * 1.25);
        b.color('#B9A58B').box(tx, ty, 0, ts, ts, 25.5);
        b.color('#8F8068').box(tx, ty, 25.5, ts + 0.6, ts + 0.6, 0.5);
        b.color('#6B6258');
        spire(b, tx, ty, ts * 0.7, 26, 29.87, 4);
      });
    },
    replaces: [STMARY],
    facts: {
      Built: 'church dedicated 1871, cathedral from 1881; the spire came down in early 1956 and a fire of 14 March 1956 destroyed it; the second cathedral was dedicated 14 March 1959 (a modern interpretation of the Romanesque); the bell tower rises 98 ft',
      Model: 'plan is the real outline (Overture, 1,640 m2); the dates and the 98 ft (29.87 m) tower are cited; the 10.5 m walls, the nave roof, the tower\'s corner and its cap are estimated, and which end is the front is a guess; construction start (1957) is an estimate. The church of 1871 is not modelled'
    },
    sources: [WIKI + 'Cathedral_of_St._Mary_of_the_Assumption_(Trenton,_New_Jersey)', OVERTURE]
  });
}

// ---------------------------------------------------------------------- Broad Street National Bank
{
  const o = obb(BANK);
  NJ_TOWNS.push({
    id: 'trn_broad_street_bank',
    name: 'Broad Street National Bank',
    kind: 'tower',
    built: [1899, 1900.5],
    end: 9999,
    anchor: BANK_ANCHOR,
    build: b => {
      block(b, BANK, 0, 10, '#B8AF9A', '#B8AF9A');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        b.color('#DCD6C6').box(0, 0, 10, o.W - 0.8, o.L - 0.8, 41.2);
        b.color('#C9C2AE').box(0, 0, 51.2, o.W + 0.6, o.L + 0.6, 1.4);
        b.color('#D2CBB8').box(0, 0, 52.6, o.W - 2.6, o.L - 2.6, 2.2);
        b.color('#8C8578').box(0, 0, 54.7, o.W - 2.6, o.L - 2.6, 0.1);
      });
    },
    replaces: [BANK],
    facts: {
      Built: 'built 1900, William A. Poland, Beaux Arts, a skyscraper; listed on the National Register 17 January 2008; stands at 143 East State Street beside the Motor Vehicles Building',
      Model: 'plan is the real outline (Overture, 2,199 m2, a rectangle); the date, architect and style are cited; no height is published: the 54.8 m top is the footprint\'s measured roof height, and the base, shaft, cornice and attic bands are estimated; construction start (1899) is an estimate'
    },
    sources: [WIKI + 'Broad_Street_National_Bank', WIKI + 'Downtown_Trenton_Commercial_Historic_District', OVERTURE]
  });
}

// ---------------------------------------------------------------------- Mercer County Courthouse
{
  const o = obb(COURTHOUSE);
  NJ_TOWNS.push({
    id: 'trn_mercer_courthouse',
    name: 'Mercer County Courthouse',
    kind: 'building',
    built: [1902.4, 1903.5],
    end: 9999,
    anchor: COURTHOUSE_ANCHOR,
    build: b => {
      block(b, COURTHOUSE, 0, 19, '#D9D3C3', '#8A857B');
      b.color('#C7C0AE').prism(COURTHOUSE, 19, 20.2, {top: false});
      const [e0, e1] = extent(COURTHOUSE, o.cx, o.cy, 90);
      // front to Broad Street (east): a columned portico under a pediment
      b.frame(o.cx, o.cy, 0, 90, () => {
        const wd = Math.min(o.W, o.L) * 0.55;
        b.color('#EDE8DA');
        colonnade(b, -wd / 2 + 0.8, wd / 2 - 0.8, e1 - 0.3, 0, 17, 6, 0.55);
        b.color('#8A857B').gable(0, e1 - 1.3, wd, 3.2, 17, 2.6, true);
        // a central drum and dome: the measured roof reaches 27.1 m
        b.color('#D9D3C3').cylinder(0, 0, 7.5, 20.2, 23.2, 20, {top: false});
        b.color('#8FA79A').dome(0, 0, 7.5, 23.2, 3.9, 20, 5);
      });
      void e0;
    },
    replaces: [COURTHOUSE],
    facts: {
      Built: 'cornerstone laid 14 May 1902, the classical Beaux Arts building by William Slack replaced a Greek Revival courthouse that served until 1903; 209 South Broad Street; the Criminal Courthouse of 2013 stands behind',
      Model: 'plan is the real outline (Overture, 2,970 m2); the cornerstone, architect and style are cited; no height is published: the 27.1 m top is the footprint\'s measured roof height, taken here as a central drum and dome (the form is an estimate), and the 19 m walls, the east-facing portico and the colours are estimated; completion (1903.5) is an estimate'
    },
    sources: [WIKI + 'Mercer_County_Courthouse_(New_Jersey)', OVERTURE]
  });
}

// ---------------------------------------------------------------------- Trenton City Hall
{
  const o = obb(CITYHALL);
  NJ_TOWNS.push({
    id: 'trn_city_hall',
    name: 'Trenton City Hall',
    kind: 'building',
    built: [1907.5, 1910],
    end: 9999,
    anchor: CITYHALL_ANCHOR,
    build: b => {
      block(b, CITYHALL, 0, 15.5, '#E7E3D8', '#8C8A82');
      b.color('#D5D0C2').prism(CITYHALL, 15.5, 16.5, {top: false});
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // hipped roof over the main block, a columned centre
        const [hw, hl] = fit(CITYHALL, o, 0, 0, o.W * 0.86, o.L * 0.8);
        b.color('#7C9A86').hip(0, 0, hw, hl, 16.5, 4.7);
        b.color('#EFEBDF');
        colonnade(b, -o.L * 0.18, o.L * 0.18, o.W / 2 - 0.2, 0, 13.5, 6, 0.5);
      });
    },
    replaces: [CITYHALL],
    facts: {
      Built: 'designed 1907 by Spencer Roberts, opened to the public 1910; white marble, Renaissance; murals by Everett Shinn; listed on the National Register 30 January 1978',
      Model: 'plan is the real outline (Overture, 1,416 m2); the design year, opening, architect, style and material are cited; no height is published: the 21.2 m top is the footprint\'s measured roof height, reached by an estimated hipped roof over estimated 15.5 m walls; the columned centre and its side are estimated; construction start (1907.5) is an estimate'
    },
    sources: [WIKI + 'Trenton_City_Hall', WIKI + 'Trenton,_New_Jersey', OVERTURE]
  });
}

// ---------------------------------------------------------------------- Roebling Machine Shop
{
  const o = obb(ROEBLING);
  NJ_TOWNS.push({
    id: 'trn_roebling_machine_shop',
    name: 'Roebling Machine Shop',
    kind: 'building',
    built: [1889.6, 1890.8],
    end: 9999,
    anchor: ROEBLING_ANCHOR,
    build: b => {
      block(b, ROEBLING, 0, 11, '#9B5B45', '#5E5953');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // the high clerestory bay of a wire-rope machine shop
        const [gw, gl] = fit(ROEBLING, o, 0, 0, o.W * 0.5, o.L * 0.86);
        b.color('#5E5953').gable(0, 0, gw, gl, 11, 5.2, true);
      });
    },
    replaces: [ROEBLING],
    facts: {
      Built: 'built 1890 (further work 1901), the oldest surviving building of John A. Roebling\'s Sons Company in Chambersburg; listed on the National Register 4 September 1997; now a museum space',
      Model: 'plan is the real outline (Overture, 5,950 m2); the date is cited; no height is published: the 16.2 m top is the footprint\'s measured roof height, reached by an estimated clerestory gable over estimated 11 m brick walls; construction start (1889.6) is an estimate'
    },
    sources: [WIKI + 'Roebling_Machine_Shop', WIKI + 'Chambersburg,_Trenton,_New_Jersey', OVERTURE]
  });
}

// ---------------------------------------------------------------------- CURE Insurance Arena
{
  const o = obb(CURE);
  NJ_TOWNS.push({
    id: 'trn_cure_arena',
    name: 'CURE Insurance Arena (Sun National Bank Center)',
    kind: 'stadium',
    built: [1997.92, 1999.76],
    end: 9999,
    anchor: CURE_ANCHOR,
    build: b => {
      block(b, CURE, 0, 12, '#B7B3AB', '#8A8780');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // the arena roof: a shallow barrel vault over the bowl
        b.color('#6F7A82');
        vault(b, 0, 0, o.W * 0.84, o.L * 0.8, 12, 6, 8);
        b.color('#C9C5BC').box(0, 0, 0, o.W * 0.2, o.L * 0.02, 0.01);
      });
    },
    replaces: [CURE],
    facts: {
      Built: 'groundbreaking 2 December 1997, opened 6 October 1999 as Sovereign Bank Arena (Sun National Bank Center 2009-2017, CURE Insurance Arena since); $53 million; Mercer County Improvement Authority; Trenton Titans / Devils until 2013',
      Model: 'plan is the real outline (Overture, 9,216 m2); the dates are cited; no height is published: the footprint\'s measured roof height is 11.9 m (an average over the building); the 12 m walls and the 6 m barrel roof (top 18 m) are estimated'
    },
    sources: [WIKI + 'CURE_Insurance_Arena', OVERTURE]
  });
}

// ====================================================================== NEW BRUNSWICK
// ---------------------------------------------------------------------- Johnson & Johnson World Headquarters
{
  const o = obb(JJ);
  NJ_TOWNS.push({
    id: 'nb_jj_headquarters',
    name: 'Johnson & Johnson World Headquarters',
    kind: 'tower',
    built: [1980, 1983.5],
    end: 9999,
    anchor: JJ_ANCHOR,
    build: b => {
      block(b, JJ, 0, 11.5, '#E3E8EA', '#C7CED2');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // the white 16-storey tower of Pei Cobb Freed, standing up out of the three-storey modules
        const [x, y, d] = roomiest(JJ, o);
        const tw = Math.min(d * 1.5, 34);
        const tl = Math.min(d * 1.8, 46);
        b.color('#F1F4F5').box(x, y, 11.5, tw, tl, 70 - 11.5);
        b.color('#B9C3C8').box(x, y, 40, tw + 0.4, tl + 0.4, 0.6);
        b.color('#9AA5AB').box(x, y, 69.8, tw, tl, 0.2);
      });
    },
    replaces: [JJ],
    facts: {
      Built: 'opened 1983 (Wikipedia\'s infobox says completed 1982); Pei Cobb Freed and Partners (I. M. Pei took part in the plan); a 16-storey tower and seven connecting three-storey modules sheathed in glass and white enameled aluminum on a 12-acre site',
      Model: 'plan is the real outline of the whole complex (Overture, 6,346 m2); the opening year, the 16 storeys and the 70 m roof are cited; the tower\'s position and plan (the roomiest part of the outline), the 11.5 m modules and the band at the 9th storey are estimated; construction start (1980) is an estimate'
    },
    sources: [WIKI + 'Johnson_and_Johnson_Plaza', OVERTURE]
  });
}

// ---------------------------------------------------------------------- New Brunswick Performing Arts Center
{
  const o = obb(NBPAC);
  NJ_TOWNS.push({
    id: 'nb_performing_arts_center',
    name: 'New Brunswick Performing Arts Center',
    kind: 'tower',
    built: [2017.5, 2019.67],
    end: 9999,
    anchor: NBPAC_ANCHOR,
    build: b => {
      block(b, NBPAC, 0, 22, '#B3AFA6', '#8E8B84');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // the residential tower above the theatres: 23 storeys in all
        const [x, y, d] = roomiest(NBPAC, o);
        const s = Math.min(d * 1.7, 34);
        b.color('#C5CED3').box(x, y, 22, s, s * 1.1, 89.61 - 22);
        b.color('#8E99A0').box(x, y, 89.3, s, s * 1.1, 0.31);
      });
    },
    replaces: [NBPAC],
    facts: {
      Built: 'construction began 2017, completed 2019, officially opened 4 September 2019; US$172 million, 23 storeys (18 of them residential, 207 apartments, 30,000 sq ft of offices); Elkus Manfredi Architects; two theatres and rehearsal studios beside the State Theatre',
      Model: 'plan is the real outline (Overture, 2,694 m2); the dates, 23 storeys and the 89.61 m roof are cited; the 22 m podium, the tower\'s plan and position (the roomiest part) and the colours are estimated; construction start (2017.5) is an estimate'
    },
    sources: [WIKI + 'New_Brunswick_Performing_Arts_Center', OVERTURE]
  });
}

// ---------------------------------------------------------------------- The Gateway
{
  const o = obb(GATEWAY);
  const tgt = lngLatToLocal(GATEWAY_ANCHOR, [-74.44775, 40.49741]);
  const [fx, fy] = toFrame(o, tgt[0], tgt[1]);
  NJ_TOWNS.push({
    id: 'nb_gateway',
    name: 'The Gateway',
    kind: 'tower',
    built: [2010, 2012.5],
    end: 9999,
    anchor: GATEWAY_ANCHOR,
    build: b => {
      block(b, GATEWAY, 0, 18, '#B7A99B', '#8E857B');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // the tower stands over the west end beside the station (Wikipedia's coordinates)
        const [px, py, pd] = roomiest(GATEWAY, o, (qx, qy) => Math.hypot(qx - fx, qy - fy) < 22);
        const [x, y, d] = [px, py, pd];
        const [tw, tl] = fit(GATEWAY, o, x, y, Math.min(26, d * 1.3), Math.min(22, d * 1.3));
        b.color('#D2D7DA').box(x, y, 18, tw, tl, 90.83 - 18);
        b.color('#8E99A0').box(x, y, 90.5, tw, tl, 0.33);
      });
    },
    replaces: [GATEWAY],
    facts: {
      Built: 'proposed February 2005 by DEVCO (Easton-Somerset redevelopment); completed 2012; a mixed-use tower of 23 storeys beside the Northeast Corridor station, the tallest building in New Brunswick',
      Model: 'plan is the real outline of the complex (Overture, 3,952 m2); the completion year, the 23 storeys and the 298 ft (90.83 m) roof are cited; the 18 m podium, the tower\'s plan and its position (placed near Wikipedia\'s coordinates, inside the outline) are estimated; construction start (2010) is an estimate'
    },
    sources: [WIKI + 'The_Gateway_(New_Brunswick,_New_Jersey)', OVERTURE]
  });
}

// ---------------------------------------------------------------------- Kirkpatrick Chapel
{
  const o = obb(KIRKPATRICK);
  NJ_TOWNS.push({
    id: 'nb_kirkpatrick_chapel',
    name: 'Kirkpatrick Chapel',
    kind: 'building',
    built: [1872, 1873.4],
    end: 9999,
    anchor: KIRKPATRICK_ANCHOR,
    build: b => {
      block(b, KIRKPATRICK, 0, 9.1, '#7A5A48', '#3F3A38');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        b.color('#4A4541').gable(0, 0, o.W, o.L, 9.1, 7.66, true);
        // buttresses along the nave
        for (const sx of [-1, 1]) {
          for (let i = -2; i <= 2; i++) b.color('#6B4F40').box(sx * (o.W / 2 + 0.1), i * (o.L * 0.17), 0, 0.9, 1.0, 7.5);
        }
        // a pinnacle on each gable end
        for (const sy of [-1, 1]) b.color('#7A5A48').box(0, sy * (o.L / 2 - 0.4), 15.2, 0.8, 0.8, 1.5);
      });
    },
    replaces: [KIRKPATRICK],
    facts: {
      Built: 'built 1872, consecrated 1873; Henry Janeway Hardenbergh\'s High Victorian Gothic Revival chapel in brownstone, 116 ft long and 57.5 ft wide, 55 ft high; four windows from the Tiffany studios',
      Model: 'plan is the real outline (Overture, 602 m2; the cited 116 x 57.5 ft is 620 m2); the dates, material, style, the 55 ft (16.76 m) height and the dimensions are cited; the 9.1 m eave (the footprint\'s measured height), the buttresses and the pinnacles are estimated'
    },
    sources: [WIKI + 'Kirkpatrick_Chapel', OVERTURE]
  });
}

// ---------------------------------------------------------------------- Winants Hall
{
  const o = obb(WINANTS);
  NJ_TOWNS.push({
    id: 'nb_winants_hall',
    name: 'Winants Hall',
    kind: 'building',
    built: [1888.5, 1890.5],
    end: 9999,
    anchor: WINANTS_ANCHOR,
    build: b => {
      block(b, WINANTS, 0, 13, '#9A5A44', '#4F4A46');
      b.color('#B39A82').prism(WINANTS, 12.2, 13.4, {top: false});
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        const [hw, hl] = fit(WINANTS, o, 0, 0, o.W * 0.92, o.L * 0.94);
        b.color('#4F4A46').hip(0, 0, hw, hl, 13.4, 4.6);
        for (const sy of [-1, 1]) b.color('#7B4A38').box(0, sy * (o.L * 0.3), 13.4, 2.0, 2.0, 4.0);
      });
    },
    replaces: [WINANTS],
    facts: {
      Built: 'designed by Van Campen Taylor and completed in 1890; Rutgers College\'s first full-scale dormitory (a dormitory 1890-1947); four storeys; a contributing building of the Queens Campus historic district (National Register, 2 July 1973)',
      Model: 'plan is the real outline (Overture, 925 m2); the completion year, architect and four storeys are cited; no height is published: the 13 m walls are the footprint\'s measured height, and the hipped roof (top 18 m), the two chimneys and the string course are estimated; construction start (1888.5) is an estimate'
    },
    sources: [WIKI + 'Winants_Hall', OVERTURE]
  });
}

// ---------------------------------------------------------------------- State Theatre
{
  const o = obb(STATETHEATRE);
  NJ_TOWNS.push({
    id: 'nb_state_theatre',
    name: 'State Theatre',
    kind: 'building',
    built: [1920.5, 1921.99],
    end: 9999,
    anchor: STATETHEATRE_ANCHOR,
    build: b => {
      block(b, STATETHEATRE, 0, 15, '#C9B79A', '#8A7F70');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // lobby front at one end, the auditorium under a gable roof, the stage house at the other
        const [gw, gl] = fit(STATETHEATRE, o, 0, 0, o.W * 0.9, o.L * 0.46);
        b.color('#6F675C').gable(0, 0, gw, gl, 15, 4.2, true);
        const [sw, sl] = fit(STATETHEATRE, o, 0, -o.L * 0.33, o.W * 0.9, o.L * 0.26);
        b.color('#B6A486').box(0, -o.L * 0.33, 15, sw, sl, 8.5);
        b.color('#8A7F70').box(0, -o.L * 0.33, 23.5, sw, sl, 0.1);
        const [mw] = fit(STATETHEATRE, o, 0, o.L / 2 - 1.2, o.W * 0.55, 1.4);
        b.color('#A0452F').box(0, o.L / 2 - 0.9, 6.2, mw, 1.4, 0.4);
      });
    },
    replaces: [STATETHEATRE],
    facts: {
      Built: 'opened 26 December 1921; Thomas W. Lamb; one of the oldest theatres in New Jersey; seats 1,850; a new blade marquee in 2021',
      Model: 'plan is the real outline (Overture, 2,212 m2); the opening date, architect and seating are cited; no height is published: the 15 m walls, the auditorium roof, the 23.5 m stage house, the marquee and which end is the front are estimated; construction start (1920.5) is an estimate'
    },
    sources: [WIKI + 'State_Theatre_(New_Brunswick,_New_Jersey)', OVERTURE]
  });
}

// ---------------------------------------------------------------------- Voorhees Hall
{
  const o = obb(VOORHEES);
  NJ_TOWNS.push({
    id: 'nb_voorhees_hall',
    name: 'Voorhees Hall (Rutgers library)',
    kind: 'building',
    built: [1902, 1903.9],
    end: 9999,
    anchor: VOORHEES_ANCHOR,
    build: b => {
      block(b, VOORHEES, 0, 12, '#B4795C', '#4F4A46');
      b.color('#D2C3A8').prism(VOORHEES, 11.2, 12.4, {top: false});
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        const [hw, hl] = fit(VOORHEES, o, 0, 0, o.W * 0.8, o.L * 0.9);
        b.color('#4F4A46').hip(0, 0, hw, hl, 12.4, 4.4);
      });
    },
    replaces: [VOORHEES],
    facts: {
      Built: '1903, built to house the Rutgers College library; named for Ralph and Elizabeth Rodman Voorhees; the library moved to Alexander Library (1956); the University Art Gallery (the Zimmerli Art Museum from 1983) was here; an addition of 2002 houses the Art History Library',
      Model: 'plan is the real outline (Overture, 2,082 m2, including the addition of 2002); the 1903 date and the use are cited; no height is published and no photograph was opened: the 12 m walls, the hipped roof (top 16.8 m) and the stone band are estimated; construction start (1902) is an estimate'
    },
    sources: [WIKI + 'Voorhees_Mall', OVERTURE]
  });
}
