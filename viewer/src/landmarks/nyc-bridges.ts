/**
 * New York landmarks: bridges. Research: data/research/landmarks_bridges.md, data/tables/landmarks_bridges.csv.
 *
 * Every bridge is modelled from z = 0 = sea level in a frame whose origin is the middle of the
 * main span and whose +y axis runs from one tower (or main pier) to the other. Tower and pier
 * positions are the centroids of OpenStreetMap's `bridge:support` outlines (© OpenStreetMap
 * contributors, ODbL), checked against the cited span lengths; approach ends are the ends of
 * the bridge-flagged road / rail segments in Overture (2026-10-21.0), and the height there is
 * the terrain grid's. Dimensions are cited in the research note; whatever is estimated is
 * named in each model's "Model" fact.
 */
import {lngLatToLocal, parabola, rect, rotRect, type V2, type V3, MeshBuilder} from './kit';
import type {Landmark} from './types';

const WIKI = 'https://en.wikipedia.org/wiki/';
const DOT = 'https://www.nyc.gov/html/dot/html/infrastructure/';
const FT = 0.3048;
const ROAD = '#55524E';
const GRANITE = '#A69A88';

// ------------------------------------------------------------------ helpers

type Axis = {anchor: V2; bearing: number; half: number; ux: number; uy: number; along: (p: V2) => number; across: (p: V2) => number};

/** Bridge frame from two tower (or pier) positions: origin at their midpoint, +y from a to c, +x to the right. */
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
    ux,
    uy,
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

/** Rectangle at station s of an axis (sx across, sy along) in the anchor's north-up metres — for `replaces`. */
function plot(ax: Axis, s: number, sx: number, sy: number): V2[] {
  return rotRect(s * ax.ux, s * ax.uy, sx, sy, ax.bearing);
}

/** Piecewise-linear interpolation through (s, value) pairs sorted by s. */
function lerpAt(pts: [number, number][], s: number): number {
  if (s <= pts[0][0]) return pts[0][1];
  for (let i = 0; i < pts.length - 1; i++) {
    if (s <= pts[i + 1][0]) return pts[i][1] + ((pts[i + 1][1] - pts[i][1]) * (s - pts[i][0])) / (pts[i + 1][0] - pts[i][0] || 1);
  }
  return pts[pts.length - 1][1];
}

/** Thin member as two crossed quads (half the triangles of a beam): suspenders, stays, truss webs. */
function wire(b: MeshBuilder, a: V3, c: V3, w: number) {
  const dx = c[0] - a[0];
  const dy = c[1] - a[1];
  const dz = c[2] - a[2];
  const L = Math.hypot(dx, dy, dz);
  if (L < 1e-6) return;
  let ux = -dy;
  let uy = dx;
  const ul = Math.hypot(ux, uy);
  if (ul < 1e-6) {
    ux = 1;
    uy = 0;
  } else {
    ux /= ul;
    uy /= ul;
  }
  const vx = (-dz * uy) / L;
  const vy = (dz * ux) / L;
  const vz = (dx * uy - dy * ux) / L;
  const h = w / 2;
  b.quad([a[0] - ux * h, a[1] - uy * h, a[2]], [a[0] + ux * h, a[1] + uy * h, a[2]], [c[0] + ux * h, c[1] + uy * h, c[2]], [c[0] - ux * h, c[1] - uy * h, c[2]]);
  b.quad([a[0] - vx * h, a[1] - vy * h, a[2] - vz * h], [a[0] + vx * h, a[1] + vy * h, a[2] + vz * h], [c[0] + vx * h, c[1] + vy * h, c[2] + vz * h], [c[0] - vx * h, c[1] - vy * h, c[2] - vz * h]);
}

/** Height of a polyline (in a plane x = const) at station y. */
function zOn(pts: V3[], y: number): number | null {
  for (let i = 0; i < pts.length - 1; i++) {
    const a = pts[i];
    const c = pts[i + 1];
    if ((y - a[1]) * (y - c[1]) <= 0) return a[2] + ((c[2] - a[2]) * (y - a[1])) / (c[1] - a[1] || 1);
  }
  return null;
}

/** Deck slice between stations y0 and y1 (frame coordinates): side faces `depth` deep, underside, road surface at z. */
function deckSeg(b: MeshBuilder, y0: number, y1: number, z0: number, z1: number, hw: number, depth: number, side: string, road = ROAD, cx = 0) {
  b.color(side);
  for (const x of [cx - hw, cx + hw]) b.quad([x, y0, z0 - depth], [x, y1, z1 - depth], [x, y1, z1], [x, y0, z0]);
  b.quad([cx - hw, y0, z0 - depth], [cx + hw, y0, z0 - depth], [cx + hw, y1, z1 - depth], [cx - hw, y1, z1 - depth]);
  b.color(road).quad([cx - hw, y0, z0], [cx + hw, y0, z0], [cx + hw, y1, z1], [cx - hw, y1, z1]);
}

/** Deck between two stations following a height function, cut into n slices. */
function deckRun(b: MeshBuilder, y0: number, y1: number, n: number, zf: (y: number) => number, hw: number, depth: number, side: string, road = ROAD, cx = 0) {
  for (let i = 0; i < n; i++) {
    const a = y0 + ((y1 - y0) * i) / n;
    const c = y0 + ((y1 - y0) * (i + 1)) / n;
    deckSeg(b, a, c, zf(a), zf(c), hw, depth, side, road, cx);
  }
}

/** Truss in the plane x between y0 and y1: chords at zb(y) and zt(y), verticals and alternating diagonals every `panel` m. */
function trussWall(b: MeshBuilder, x: number, y0: number, y1: number, zb: (y: number) => number, zt: (y: number) => number, panel: number, chord = 0.8, web = 0.4, bottom = true) {
  const n = Math.max(1, Math.round(Math.abs(y1 - y0) / panel));
  const y = (i: number) => y0 + ((y1 - y0) * i) / n;
  for (let i = 0; i < n; i++) {
    const a = y(i);
    const c = y(i + 1);
    b.beam([x, a, zt(a)], [x, c, zt(c)], chord);
    if (bottom) b.beam([x, a, zb(a)], [x, c, zb(c)], chord);
    if (web > 0) {
      wire(b, [x, a, zb(a)], [x, a, zt(a)], web);
      if (i % 2 === 0) wire(b, [x, a, zb(a)], [x, c, zt(c)], web);
      else wire(b, [x, a, zt(a)], [x, c, zb(c)], web);
    }
  }
  if (web > 0) wire(b, [x, y1, zb(y1)], [x, y1, zt(y1)], web);
}

/** Approach viaduct in the bridge frame: deck slices from station y0 to y1 following zf, each on a wall pier. */
function arcade(b: MeshBuilder, y0: number, y1: number, zf: (y: number) => number, hw: number, color: string, every: number, pierLen: number, depth = 1.5, pierW = 2 * hw - 1) {
  const n = Math.max(1, Math.round(Math.abs(y1 - y0) / every));
  for (let i = 0; i < n; i++) {
    const a = y0 + ((y1 - y0) * i) / n;
    const c = y0 + ((y1 - y0) * (i + 1)) / n;
    deckSeg(b, a, c, zf(a), zf(c), hw, depth, color);
    const zp = zf((a + c) / 2) - depth;
    if (zp > 0.5) b.color(color).box(0, (a + c) / 2, 0, pierW, pierLen, zp, {top: false});
  }
}

/** Portal strut across the frame at station y between x = ±hw: flat top at zt, arched soffit rising `rise` from zs at the legs, d thick. */
function archStrut(b: MeshBuilder, y: number, hw: number, zs: number, rise: number, zt: number, d: number, n = 8) {
  const sof = (x: number) => zs + rise * Math.sqrt(Math.max(0, 1 - (x / hw) ** 2));
  for (let i = 0; i < n; i++) {
    const x0 = -hw + (2 * hw * i) / n;
    const x1 = -hw + (2 * hw * (i + 1)) / n;
    for (const yy of [y - d / 2, y + d / 2]) b.quad([x0, yy, sof(x0)], [x1, yy, sof(x1)], [x1, yy, zt], [x0, yy, zt]);
    b.quad([x0, y - d / 2, sof(x0)], [x1, y - d / 2, sof(x1)], [x1, y + d / 2, sof(x1)], [x0, y + d / 2, sof(x0)]);
  }
  b.quad([-hw, y - d / 2, zt], [hw, y - d / 2, zt], [hw, y + d / 2, zt], [-hw, y + d / 2, zt]);
}

/** Braced steel leg: four corner columns through the rings at the given heights, X-braced on every face. */
function latticeLeg(b: MeshBuilder, ring: (z: number) => V2[], zs: number[], col: number, web: number) {
  const at = (z: number, i: number): V3 => {
    const r = ring(z);
    return [r[i][0], r[i][1], z];
  };
  for (let i = 0; i < 4; i++) b.beam(at(zs[0], i), at(zs[zs.length - 1], i), col);
  for (let k = 0; k < zs.length - 1; k++) {
    for (let i = 0; i < 4; i++) {
      const j = (i + 1) % 4;
      wire(b, at(zs[k], i), at(zs[k + 1], j), web);
      wire(b, at(zs[k], j), at(zs[k + 1], i), web);
      b.beam(at(zs[k + 1], i), at(zs[k + 1], j), web * 1.3);
    }
  }
}

type Path = {pts: V2[]; cum: number[]; len: number};

/** A lon/lat centre line as local metres about an anchor, with cumulative distances. */
function pathOf(anchor: V2, ll: V2[]): Path {
  const pts = ll.map(p => lngLatToLocal(anchor, p));
  const cum = [0];
  for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  return {pts, cum, len: cum[cum.length - 1]};
}

/** Point and bearing of a path at distance d. */
function pathAt(p: Path, d: number): [number, number, number] {
  let i = 0;
  while (i < p.pts.length - 2 && p.cum[i + 1] < d) i++;
  const t = (d - p.cum[i]) / (p.cum[i + 1] - p.cum[i] || 1);
  const a = p.pts[i];
  const c = p.pts[i + 1];
  return [a[0] + (c[0] - a[0]) * t, a[1] + (c[1] - a[1]) * t, (Math.atan2(c[0] - a[0], c[1] - a[1]) * 180) / Math.PI];
}

/** Girder deck along a path between distances d0 and d1 (top at zf(d)); piers every `every` m, drawn by `pier` in a frame facing along the line. */
function pathDeck(b: MeshBuilder, p: Path, d0: number, d1: number, zf: (d: number) => number, width: number, depth: number, side: string, road: string, every = 0, pier?: (zTop: number) => void) {
  const ds = [d0];
  for (let i = 0; i < p.cum.length; i++) if (p.cum[i] > d0 + 0.5 && p.cum[i] < d1 - 0.5) ds.push(p.cum[i]);
  ds.push(d1);
  for (let i = 0; i < ds.length - 1; i++) {
    const n = Math.max(1, Math.ceil((ds[i + 1] - ds[i]) / 60));
    for (let k = 0; k < n; k++) {
      const da = ds[i] + ((ds[i + 1] - ds[i]) * k) / n;
      const dc = ds[i] + ((ds[i + 1] - ds[i]) * (k + 1)) / n;
      const a = pathAt(p, da + 1e-6);
      const c = pathAt(p, dc - 1e-6);
      b.color(side).beam([a[0], a[1], zf(da) - depth / 2], [c[0], c[1], zf(dc) - depth / 2], width, depth);
      b.color(road).beam([a[0], a[1], zf(da) + 0.06], [c[0], c[1], zf(dc) + 0.06], width * 0.92, 0.12);
    }
  }
  if (!every || !pier) return;
  const n = Math.max(1, Math.round((d1 - d0) / every));
  for (let i = 0; i < n; i++) {
    const d = d0 + ((d1 - d0) * (i + 0.5)) / n;
    const [x, y, brg] = pathAt(p, d);
    const zt = zf(d) - depth;
    if (zt > 1) b.frame(x, y, 0, brg, () => pier(zt));
  }
}

/** Run fn in a frame whose origin is the path point at d0 and whose +y points at the path point at d1 (L = their distance). */
function onPath(b: MeshBuilder, p: Path, d0: number, d1: number, fn: (L: number) => void) {
  const a = pathAt(p, d0);
  const c = pathAt(p, d1);
  b.frame(a[0], a[1], 0, (Math.atan2(c[0] - a[0], c[1] - a[1]) * 180) / Math.PI, () => fn(Math.hypot(c[0] - a[0], c[1] - a[1])));
}

/** Through truss between y0 and y1: low steel at zl(y), top chord depth(t) above it (0 at an end = inclined end post), n panels, w between truss planes. */
function throughTruss(b: MeshBuilder, y0: number, y1: number, zl: (y: number) => number, depth: (t: number) => number, w: number, n: number, chord = 0.9, web = 0.45) {
  const y = (i: number) => y0 + ((y1 - y0) * i) / n;
  const zt = (i: number) => zl(y(i)) + depth(i / n);
  for (const x of [-w / 2, w / 2]) {
    for (let i = 0; i < n; i++) {
      b.beam([x, y(i), zl(y(i))], [x, y(i + 1), zl(y(i + 1))], chord);
      b.beam([x, y(i), zt(i)], [x, y(i + 1), zt(i + 1)], chord);
      if (i > 0) wire(b, [x, y(i), zl(y(i))], [x, y(i), zt(i)], web);
      if (i > 0 && i < n - 1) {
        if (i < n / 2) wire(b, [x, y(i), zt(i)], [x, y(i + 1), zl(y(i + 1))], web);
        else wire(b, [x, y(i), zl(y(i))], [x, y(i + 1), zt(i + 1)], web);
      }
    }
  }
  for (let i = 1; i < n; i++) if (depth(i / n) > 6.5) b.beam([-w / 2, y(i), zt(i)], [w / 2, y(i), zt(i)], web);
}

/** Top-chord profile of a parallel-chord truss with inclined end posts. */
const flatTop = (d: number) => (t: number) => (t < 1e-6 || t > 1 - 1e-6 ? 0 : d);

type Susp = {
  /** towers at y = ±half */
  half: number;
  /** cable height at the towers and at the middle of the main span */
  top: number;
  low: number;
  /** stations and heights where the cables enter the anchorages */
  ends: [number, number];
  zEnds: [number, number];
  /** cable planes */
  xs: number[];
  /** drawn cable thickness */
  w: number;
  deckZ: (y: number) => number;
  /** suspender spacing (0 or absent: none), their planes (default: the cable planes), drawn thickness */
  every?: number;
  hangXs?: number[];
  hangW?: number;
  /** side spans hang from the cables (false: straight backstays) */
  sideHung?: boolean;
  sideSag?: number;
};

/** Main cables (parabolic main span, side spans to the anchorages) and vertical suspenders. */
function cables(b: MeshBuilder, s: Susp) {
  const prof = (x: number): V3[][] => {
    const side = (y0: number, z0: number, y1: number, z1: number) => parabola([x, y0, z0], [x, y1, z1], (z0 + z1) / 2 - (s.sideSag ?? 0), 8);
    return [parabola([x, -s.half, s.top], [x, s.half, s.top], s.low, 32), side(s.ends[0], s.zEnds[0], -s.half, s.top), side(s.half, s.top, s.ends[1], s.zEnds[1])];
  };
  for (const x of s.xs) for (const p of prof(x)) b.polyline(p, s.w);
  if (!s.every) return;
  for (const x of s.hangXs ?? s.xs) {
    const [main, sa, sb] = prof(x);
    const runs: [V3[], number, number][] = [[main, -s.half, s.half]];
    if (s.sideHung) runs.push([sa, s.ends[0], -s.half], [sb, s.half, s.ends[1]]);
    for (const [pts, y0, y1] of runs) {
      const n = Math.max(2, Math.round((y1 - y0) / s.every));
      for (let i = 1; i < n; i++) {
        const y = y0 + ((y1 - y0) * i) / n;
        const z = zOn(pts, y);
        const zd = s.deckZ(y);
        if (z !== null && z - zd > 1.2) wire(b, [x, y, zd], [x, y, z], s.hangW ?? 0.35);
      }
    }
  }
}

// =================================================================== EAST RIVER

// ------------------------------------------------------------ Brooklyn Bridge (1870–1883)
// Wikipedia (Brooklyn Bridge): main span 1,595.5 ft, side spans 930 ft, deck 85 ft wide; towers
// 278.25 ft above mean high water, 140 × 59 ft at the high-water line, two pointed arch openings
// 117 ft tall and 33.75 ft wide whose floors are 119.25 ft above mean water; four 15.75 in main
// cables; diagonal stays 138–449 ft long; promenade 18 ft above the roadways; anchorages 129 × 119 ft
// at the base, 117 × 104 ft at the top; 127 ft clear above mean high water (NYC DOT: 135 ft).
// OSM tower outlines (ways 1255363983, 317352708): centroids 485.1 m apart (cited 486.3 m), bearing
// 136.2°; the deck outline (way 375157262) ends 527 / 524 m from mid-span (cited 242.5 + 283.5 = 526 m).
// Overture's bridge flag runs from 947 m (Manhattan) to 811 m (Brooklyn) from mid-span on the same line.
const BB = axisOf([-73.998334, 40.707269], [-73.994354, 40.704104]);
const BB_FLOOR = 119.25 * FT;
const BB_TOP = 278.25 * FT;
const BB_MID = 127 * FT + 1.8; // floor at mid-span: the cited clearance plus a 1.8 m floor (estimated)
const BB_ANCH = BB_FLOOR - 0.0325 * 930 * FT; // roadway on the anchorages (3.25 % side-span grade, estimated)
const BB_A = BB.half + 930 * FT; // anchorage face
const BB_ENDS: [number, number] = [-947, 811];
const BB_HW = (85 * FT) / 2;
const BB_STEEL = '#B5A791';

function bbDeckZ(y: number) {
  const a = Math.abs(y);
  if (a <= BB.half) return BB_MID - (BB_MID - BB_FLOOR) * (a / BB.half) ** 2;
  if (a <= BB_A) return BB_FLOOR - ((BB_FLOOR - BB_ANCH) * (a - BB.half)) / (BB_A - BB.half);
  // approaches: down to the terrain at the ends (9.1 m at the Manhattan end, 20.0 m at the Brooklyn end)
  return y < 0 ? lerpAt([[BB_A, BB_ANCH], [-BB_ENDS[0], 9.1]], a) : lerpAt([[BB_A, BB_ANCH], [BB_ENDS[1], 20.0]], a);
}

function brooklynTower(b: MeshBuilder, y: number) {
  const W0 = 140 * FT;
  const D0 = 59 * FT;
  const W1 = 41.5; // plan at the top estimated (OSM outline 42.8 × 16.6 m)
  const D1 = 16.2;
  const w = (z: number) => W0 + ((W1 - W0) * z) / BB_TOP;
  const d = (z: number) => D0 + ((D1 - D0) * z) / BB_TOP;
  const OPEN = 33.75 * FT;
  const CROWN = BB_FLOOR + 117 * FT;
  const SPRING = CROWN - (OPEN * Math.sqrt(3)) / 2; // equilateral pointed arch (shape estimated)
  const xc = (W1 - 2 * OPEN) / 6 + OPEN / 2; // centre line of each opening
  const h = (z: number) => (z <= SPRING ? OPEN / 2 : Math.max(0, Math.sqrt(Math.max(OPEN * OPEN - (z - SPRING) ** 2, 0)) - OPEN / 2));
  b.color(GRANITE);
  b.box(0, y, -3, W0 + 4, D0 + 4, 4.5);
  b.loft([rect(0, y, w(0), d(0)), rect(0, y, w(BB_FLOOR), d(BB_FLOOR))], [0, BB_FLOOR]);
  const zs = [BB_FLOOR, SPRING];
  for (let k = 1; k <= 6; k++) zs.push(SPRING + ((CROWN - SPRING) * k) / 6);
  b.loft(zs.map(z => rect(0, y, 2 * (xc - h(z)), d(z))), zs, {top: false});
  for (const s of [-1, 1]) {
    b.loft(zs.map(z => rect((s * (xc + h(z) + w(z) / 2)) / 2, y, w(z) / 2 - xc - h(z), d(z))), zs, {top: false});
  }
  b.loft([rect(0, y, w(CROWN), d(CROWN)), rect(0, y, w(BB_TOP - 4), d(BB_TOP - 4))], [CROWN, BB_TOP - 4], {top: false});
  b.box(0, y, BB_TOP - 4, W1 + 1.6, D1 + 1.6, 1.6);
  b.box(0, y, BB_TOP - 2.4, W1, D1, 2.4);
}

function brooklynBuild(b: MeshBuilder) {
  const H = BB.half;
  const PROM = 18 * FT;
  const XS = [-13.4, -2.6, 2.6, 13.4]; // cable planes (estimated: outside the roadways and beside the promenade)
  const SADDLE = BB_TOP - 2.5;
  const top = (y: number) => bbDeckZ(y) + PROM;
  b.frame(0, 0, 0, BB.bearing, () => {
    brooklynTower(b, -H);
    brooklynTower(b, H);
    deckRun(b, -BB_A, -H, 8, bbDeckZ, BB_HW, 1.8, BB_STEEL);
    deckRun(b, -H, H, 20, bbDeckZ, BB_HW, 1.8, BB_STEEL);
    deckRun(b, H, BB_A, 8, bbDeckZ, BB_HW, 1.8, BB_STEEL);
    // stiffening trusses (outer pair with webs, the pair beside the promenade as chords) and the promenade
    b.color(BB_STEEL);
    for (const x of [-BB_HW, BB_HW]) trussWall(b, x, -BB_A, BB_A, bbDeckZ, top, 15, 0.7, 0.35, false);
    for (const x of [-2.6, 2.6]) trussWall(b, x, -BB_A, BB_A, bbDeckZ, top, 35, 0.6, 0, false);
    b.color('#8C7B66');
    const N = 36;
    for (let i = 0; i < N; i++) {
      const a = -BB_A + (2 * BB_A * i) / N;
      const c = -BB_A + (2 * BB_A * (i + 1)) / N;
      b.quad([-2.4, a, top(a) + 0.1], [2.4, a, top(a) + 0.1], [2.4, c, top(c) + 0.1], [-2.4, c, top(c) + 0.1]);
    }
    for (const s of [-1, 1]) b.quad([-2.4, s * BB_A, top(BB_A) + 0.1], [2.4, s * BB_A, top(BB_A) + 0.1], [2.4, s * (BB_A + 70), bbDeckZ(s * (BB_A + 70)) + 0.3], [-2.4, s * (BB_A + 70), bbDeckZ(s * (BB_A + 70)) + 0.3]);
    // four main cables, suspenders, and the diagonal stays fanning from the tower tops
    b.color('#C9BFAE');
    cables(b, {half: H, top: SADDLE, low: top(0) + 0.6, ends: [-BB_A - 12, BB_A + 12], zEnds: [BB_ANCH + 1, BB_ANCH + 1], xs: XS, w: 0.7, deckZ: top, every: 11, sideHung: true, sideSag: 5, hangW: 0.25});
    for (const t of [-H, H]) {
      for (const dir of [-1, 1]) {
        for (const x of XS) {
          for (let k = 1; k <= 8; k++) wire(b, [x, t, SADDLE], [x, t + dir * k * 16, top(t + dir * k * 16)], 0.25);
        }
      }
    }
    // anchorages and the masonry approaches
    b.color(GRANITE);
    for (const s of [-1, 1]) b.loft([rect(0, s * (BB_A + 17.7), 119 * FT, 129 * FT), rect(0, s * (BB_A + 17.7), 104 * FT, 117 * FT)], [0, BB_ANCH - 0.2]);
    arcade(b, -BB_A, BB_ENDS[0], bbDeckZ, BB_HW, GRANITE, 30, 14);
    arcade(b, BB_A, BB_ENDS[1], bbDeckZ, BB_HW, GRANITE, 30, 14);
  });
}

const brooklynBridge: Landmark = {
  id: 'brooklyn_bridge',
  name: 'Brooklyn Bridge',
  kind: 'bridge',
  built: [1870.0, 1883.39],
  end: 9999,
  anchor: BB.anchor,
  build: brooklynBuild,
  replaces: [plot(BB, -BB.half, 48, 24), plot(BB, BB.half, 48, 24), plot(BB, -BB_A - 18, 40, 44), plot(BB, BB_A + 18, 40, 44)],
  facts: {
    Construction: 'Jan 2, 1870 – May 1883; opened May 24, 1883 (John A. Roebling, then Washington and Emily Warren Roebling)',
    'Main span': '1,595.5 ft (486.3 m), the longest suspension span in the world when it opened; side spans 930 ft',
    Towers: 'granite and limestone, 278 ft (84.8 m) above mean high water, 140 × 59 ft at the water line; two pointed arches 117 ft tall and 33.75 ft wide, their floors 119 ft above the water',
    Cables: 'four main cables 15.75 in across, with vertical suspenders and about 400 diagonal stays from the tower tops',
    Deck: '85 ft wide; promenade 18 ft above the roadways; 127 ft clear above mean high water (135 ft when built)',
    Model: 'towers placed on the OpenStreetMap outlines (485.1 m apart against the cited 486.3 m); tower plan at the top, arch curve, cable planes, saddle height and sag, deck heights between the cited tower floor and mid-span clearance, truss depth and the approach arcades are estimated; stays and suspenders thinned out'
  },
  sources: [WIKI + 'Brooklyn_Bridge', DOT + 'brooklyn-bridge.shtml']
};

// ------------------------------------------------------------ Manhattan Bridge (1901–1909)
// NYC DOT: main span 1,470 ft; Wikipedia (Manhattan Bridge): main span 1,470 ft (infobox 1,480),
// side spans 725 ft, deck 120 ft wide, towers 336 ft, 135 ft clear, four stiffening trusses 24 ft
// deep flanking the tracks, lower roadway 35 ft. OSM tower outlines (ways 1255353996, 317352033)
// are 443.9 m apart, 0.9 % short of the cited 448.1 m: the towers are set 448.1 m apart about the
// same midpoint on the same bearing (157.0°). OSM anchorage blocks: 58 × 49 m centred 471 m from
// mid-span. Overture's bridge flag (named 'Canal Street' / 'Chrystie Street' there) runs from
// 944 m (Manhattan) to 909 m (Brooklyn) from mid-span.
const MB = axisOf([-73.991488, 40.708812], [-73.989436, 40.705115]);
const MB_H = (1470 * FT) / 2;
const MB_A = MB_H + 725 * FT;
const MB_ENDS: [number, number] = [-940, 905];
const MB_TOP = 336 * FT;
const MB_HW = (120 * FT) / 2;
const MB_TRUSS = 24 * FT;
const MB_XS = [-14.6, -5.6, 5.6, 14.6]; // truss / cable planes from the cited 35 ft lower roadway and 120 ft deck (estimated)
const MB_BLUE = '#5F7389';

/** Lower-deck floor: 135 ft clear + 1.5 m at mid-span; a 3 % grade at the towers (estimated). */
function mbDeckZ(y: number) {
  const a = Math.abs(y);
  const mid = 135 * FT + 1.5;
  const twr = mid - 0.015 * MB_H;
  if (a <= MB_H) return mid - (mid - twr) * (a / MB_H) ** 2;
  const anch = twr - 0.03 * (MB_A - MB_H);
  return y < 0 ? lerpAt([[MB_H, twr], [MB_A, anch], [-MB_ENDS[0], 12.5]], a) : lerpAt([[MB_H, twr], [MB_A, anch], [MB_ENDS[1], 20.5]], a);
}

function manhattanTower(b: MeshBuilder, y: number) {
  const PIER = 9; // masonry pier height (estimated)
  const CAP = MB_TOP - 4.4;
  const zd = mbDeckZ(y);
  b.color(GRANITE).box(0, y, -3, 44, 16, 3 + PIER);
  b.color(MB_BLUE);
  for (const x of MB_XS) b.loft([rect(x, y, 1.9, 7.5), rect(x, y, 1.9, 3.2)], [PIER, CAP]);
  b.box(0, y, CAP, 33, 3.6, 2.4);
  for (const x of MB_XS) b.dome(x, y, 1.3, CAP + 2.4, 2.0, 8, 3);
  // transverse bracing: below the deck in every bay; above it the roadway and track bays stay open to a portal strut
  const bays: [number, number][] = [[MB_XS[0], MB_XS[1]], [MB_XS[1], MB_XS[2]], [MB_XS[2], MB_XS[3]]];
  const portal = zd + MB_TRUSS + 7;
  const levels = [PIER + 0.5, (PIER + zd) / 2, zd - 2];
  for (let z = portal; z < CAP - 1; z += (CAP - portal) / 5) levels.push(z);
  levels.push(CAP);
  for (const [x0, x1] of bays) {
    for (let i = 0; i < levels.length - 1; i++) {
      if (i === 2) continue; // the deck passes through
      b.beam([x0, y, levels[i]], [x1, y, levels[i]], 0.7);
      wire(b, [x0, y, levels[i]], [x1, y, levels[i + 1]], 0.4);
      wire(b, [x1, y, levels[i]], [x0, y, levels[i + 1]], 0.4);
    }
    b.beam([x0, y, portal], [x1, y, portal], 1.2);
  }
}

function manhattanBuild(b: MeshBuilder) {
  const up = (y: number) => mbDeckZ(y) + MB_TRUSS;
  b.frame(0, 0, 0, MB.bearing, () => {
    manhattanTower(b, -MB_H);
    manhattanTower(b, MB_H);
    // lower deck (roadway, four tracks, walkways) and the upper roadways over the tracks
    for (const [y0, y1, n] of [[-MB_A, -MB_H, 8], [-MB_H, MB_H, 18], [MB_H, MB_A, 8]] as [number, number, number][]) {
      deckRun(b, y0, y1, n, mbDeckZ, MB_HW, 1.5, MB_BLUE);
      for (const s of [-1, 1]) deckRun(b, y0, y1, n, y => up(y) + 0.4, 4.5, 0.6, MB_BLUE, ROAD, s * 10.1);
    }
    b.color(MB_BLUE);
    for (const x of [MB_XS[0], MB_XS[3]]) trussWall(b, x, -MB_A, MB_A, mbDeckZ, up, 16, 0.7, 0.35, false);
    for (const x of [MB_XS[1], MB_XS[2]]) trussWall(b, x, -MB_A, MB_A, mbDeckZ, up, 32, 0.6, 0, false);
    cables(b, {half: MB_H, top: MB_TOP - 3, low: up(0) + 1, ends: [-MB_A - 14, MB_A + 14], zEnds: [up(MB_A) + 1, up(MB_A) + 1], xs: MB_XS, w: 0.8, deckZ: up, every: 12, sideHung: true, sideSag: 4, hangW: 0.25});
    // anchorages (OSM: 58 m along × 49 m across) and approach viaducts
    b.color(GRANITE);
    for (const s of [-1, 1]) {
      b.box(0, s * (MB_A + 28), 0, 49, 58, up(MB_A) - 0.2);
      for (const x of [-22.5, 22.5]) b.box(x, s * (MB_A + 28), up(MB_A) - 0.2, 4, 58, 3);
    }
    arcade(b, -MB_A, MB_ENDS[0], y => Math.min(up(MB_A), mbDeckZ(y) + MB_TRUSS * Math.min(1, (940 - Math.abs(y)) / 250)), MB_HW, GRANITE, 32, 12);
    arcade(b, MB_A, MB_ENDS[1], y => Math.min(up(MB_A), mbDeckZ(y) + MB_TRUSS * Math.min(1, (905 - Math.abs(y)) / 250)), MB_HW, GRANITE, 32, 12);
  });
}

const manhattanBridge: Landmark = {
  id: 'manhattan_bridge',
  name: 'Manhattan Bridge',
  kind: 'bridge',
  built: [1901.75, 1909.99],
  end: 9999,
  anchor: MB.anchor,
  build: manhattanBuild,
  replaces: [plot(MB, -MB_H, 44, 16), plot(MB, MB_H, 44, 16), plot(MB, -MB_A - 28, 52, 60), plot(MB, MB_A + 28, 52, 60)],
  facts: {
    Construction: '1901 – 1909; opened Dec 31, 1909 (Leon Moisseiff, the first suspension bridge designed by deflection theory); arch and colonnade by Carrère and Hastings, 1915',
    'Main span': '1,470 ft (448 m); side spans 725 ft, hung from the cables',
    Towers: 'steel, 336 ft (102 m), four columns each',
    Deck: '120 ft wide on two levels: a roadway and four subway tracks below, two roadways above the tracks; four stiffening trusses 24 ft deep; 135 ft clear',
    Cables: 'four main cables, one above each truss',
    Model: 'towers set the cited 448.1 m apart about the midpoint of the OpenStreetMap tower outlines (443.9 m apart there); truss and cable planes, pier height, tower bracing, saddle height and sag, deck heights (from the cited clearance and a 3 % grade) and the anchorage height are estimated; anchorage plan from OpenStreetMap; the arch, colonnade and approach arcades are simplified'
  },
  sources: [WIKI + 'Manhattan_Bridge', DOT + 'manhattan-bridge.shtml']
};

// ------------------------------------------------------------ Williamsburg Bridge (1896–1903)
// Wikipedia (Williamsburg Bridge): main span 1,600 ft, deck 118 ft wide, 135 ft clear at the
// middle and about 122 ft above mean high water at the shores; steel towers 333–335 ft above mean
// high water on masonry piers 23 ft high, the legs slanting inward above the deck (14 ft narrower
// at the top); two stiffening trusses 67 ft apart and 40 ft deep; four 18 in cables (NYC DOT);
// the side spans are not hung from the cables. OSM tower outlines (ways 1016434034, 1016434035):
// 487.3 m apart (cited 487.7 m), bearing 111.8°; anchorages (49 m across × 41 m along) centred
// 442 m from mid-span; deck outline from 1,096 m (Manhattan) to 947 m (Brooklyn) from mid-span.
const WB = axisOf([-73.97482, 40.714395], [-73.969458, 40.712758]);
const WB_A = 421.5; // anchorage face (OSM)
const WB_ENDS: [number, number] = [-1096, 947];
const WB_TOP = 333 * FT;
const WB_HW = (118 * FT) / 2;
const WB_TX = (67 * FT) / 2;
const WB_TRUSS = 40 * FT;
const WB_GREY = '#8B8F8E';

/** Roadway: 135 ft clear + the 5 ft floor beams at mid-span, 122 ft at the towers (cited); 3 % on the side spans (estimated). */
function wbDeckZ(y: number) {
  const a = Math.abs(y);
  const mid = 140 * FT;
  const twr = 122 * FT;
  if (a <= WB.half) return mid - (mid - twr) * (a / WB.half) ** 2;
  const anch = twr - 0.03 * (WB_A - WB.half);
  return y < 0 ? lerpAt([[WB.half, twr], [WB_A, anch], [-WB_ENDS[0], 7.7]], a) : lerpAt([[WB.half, twr], [WB_A, anch], [WB_ENDS[1], 15.7]], a);
}

function williamsburgTower(b: MeshBuilder, y: number) {
  const PIER = 23 * FT;
  const zd = wbDeckZ(y);
  // each leg: four columns, (centre x, half-width across, half-length along) by height
  const leg = (z: number): [number, number, number] => {
    const t = (z - PIER) / (WB_TOP - PIER);
    return [lerpAt([[PIER, 13.2], [zd, WB_TX + 2.1], [WB_TOP, WB_TX]], z), 4.6 - 2.8 * t, 5.2 - 3.0 * t];
  };
  const levels = [PIER];
  for (let i = 1; i <= 8; i++) levels.push(PIER + ((WB_TOP - 2 - PIER) * i) / 8);
  for (const s of [-1, 1]) {
    b.color(GRANITE).box(s * 13.2, y, -3, 13, 13.5, 3 + PIER);
    b.color(WB_GREY);
    const corner = (z: number, i: number): V3 => {
      const [cx, hx, hy] = leg(z);
      return [s * (cx + (i % 2 ? hx : -hx)), y + (i < 2 ? -hy : hy), z];
    };
    for (let i = 0; i < 4; i++) b.beam(corner(PIER, i), corner(WB_TOP - 2, i), 1.1);
    for (let k = 0; k < levels.length - 1; k++) {
      for (const [i, j] of [[0, 1], [2, 3], [0, 2], [1, 3]]) {
        wire(b, corner(levels[k], i), corner(levels[k + 1], j), 0.4);
        wire(b, corner(levels[k], j), corner(levels[k + 1], i), 0.4);
        b.beam(corner(levels[k + 1], i), corner(levels[k + 1], j), 0.5);
      }
    }
    const [cx, hx, hy] = leg(WB_TOP - 2);
    b.box(s * cx, y, WB_TOP - 2, 2 * hx + 1.2, 2 * hy + 1.2, 2);
  }
  // portal trusses between the legs: two above the deck (45 ft high, cited), one below it
  b.color(WB_GREY);
  const inner = (z: number) => leg(z)[0] - leg(z)[1];
  for (const [z0, z1] of [[WB_TOP - 2 - 45 * FT, WB_TOP - 2], [zd + WB_TRUSS + 3, zd + WB_TRUSS + 3 + 45 * FT], [zd - 16, zd - 4]]) {
    b.beam([-inner(z0), y, z0], [inner(z0), y, z0], 0.9);
    b.beam([-inner(z1), y, z1], [inner(z1), y, z1], 0.9);
    wire(b, [-inner(z0), y, z0], [0, y, z1], 0.5);
    wire(b, [inner(z0), y, z0], [0, y, z1], 0.5);
    wire(b, [-inner(z1), y, z1], [0, y, z0], 0.5);
    wire(b, [inner(z1), y, z1], [0, y, z0], 0.5);
  }
}

function williamsburgBuild(b: MeshBuilder) {
  const H = WB.half;
  const zb = (y: number) => wbDeckZ(y) - 5 * FT;
  const zt = (y: number) => zb(y) + WB_TRUSS;
  b.frame(0, 0, 0, WB.bearing, () => {
    williamsburgTower(b, -H);
    williamsburgTower(b, H);
    deckRun(b, -WB_A, -H, 6, wbDeckZ, WB_HW, 5 * FT, WB_GREY);
    deckRun(b, -H, H, 18, wbDeckZ, WB_HW, 5 * FT, WB_GREY);
    deckRun(b, H, WB_A, 6, wbDeckZ, WB_HW, 5 * FT, WB_GREY);
    b.color(WB_GREY);
    for (const x of [-WB_TX, WB_TX]) trussWall(b, x, -WB_A, WB_A, zb, zt, 12.2, 0.9, 0.4);
    for (let y = -WB_A; y <= WB_A; y += (2 * WB_A) / 28) b.beam([-WB_TX, y, zt(y)], [WB_TX, y, zt(y)], 0.5);
    // cables in two pairs above the trusses; suspenders on the main span only, straight backstays
    cables(b, {half: H, top: WB_TOP - 1, low: zt(0) + 0.8, ends: [-WB_A - 12, WB_A + 12], zEnds: [zt(WB_A), zt(WB_A)], xs: [-WB_TX - 0.7, -WB_TX + 0.7, WB_TX - 0.7, WB_TX + 0.7], w: 0.6, deckZ: zt, every: 12.2, hangXs: [-WB_TX, WB_TX], hangW: 0.3});
    // intermediate steel towers under the side spans, anchorages, steel approach viaducts
    for (const s of [-1, 1]) {
      const y = s * (H + (WB_A - H) / 2);
      b.color(WB_GREY);
      for (const x of [-WB_TX, WB_TX]) {
        for (const dy of [-4, 4]) b.beam([x, y + dy, 0], [x, y + dy, zb(y)], 1.0);
        wire(b, [x, y - 4, 0], [x, y + 4, zb(y)], 0.4);
        wire(b, [x, y + 4, 0], [x, y - 4, zb(y)], 0.4);
      }
      wire(b, [-WB_TX, y, 2], [WB_TX, y, zb(y)], 0.5);
      wire(b, [WB_TX, y, 2], [-WB_TX, y, zb(y)], 0.5);
      b.color(GRANITE).box(0, s * (WB_A + 20.5), 0, 49, 41, zt(WB_A) + 1.5);
    }
    arcade(b, -WB_A - 41, WB_ENDS[0], wbDeckZ, WB_HW, WB_GREY, 30, 2.2, 2.4, 2 * WB_TX);
    arcade(b, WB_A + 41, WB_ENDS[1], wbDeckZ, WB_HW, WB_GREY, 30, 2.2, 2.4, 2 * WB_TX);
  });
}

const williamsburgBridge: Landmark = {
  id: 'williamsburg_bridge',
  name: 'Williamsburg Bridge',
  kind: 'bridge',
  built: [1896.46, 1903.97],
  end: 9999,
  anchor: WB.anchor,
  build: williamsburgBuild,
  replaces: [plot(WB, -WB.half, 40, 16), plot(WB, WB.half, 40, 16), plot(WB, -WB_A - 20.5, 52, 44), plot(WB, WB_A + 20.5, 52, 44)],
  facts: {
    Construction: 'Jun 19, 1896 – Dec 1903; opened Dec 19, 1903 (Leffert L. Buck, chief engineer; Henry Hornbostel, architect)',
    'Main span': '1,600 ft (487.7 m), the longest suspension span in the world until 1924; side spans carried on steel towers, not hung from the cables',
    Towers: 'steel, 333 ft (101.5 m) above mean high water (NYC DOT: 310 ft), on masonry piers 23 ft high',
    Deck: '118 ft wide; two stiffening trusses 40 ft deep and 67 ft apart; 135 ft clear at mid-span, the deck about 122 ft above the water at the shores',
    Cables: 'four main cables 18 in across',
    Model: 'towers on the OpenStreetMap outlines (487.3 m apart against the cited 487.7 m); anchorage position and plan from OpenStreetMap; tower leg sections, bracing, saddle height and sag, side-span and approach grades and the intermediate towers are estimated; the 1952 connector to the Brooklyn–Queens Expressway beyond the Brooklyn plaza is not modelled'
  },
  sources: [WIKI + 'Williamsburg_Bridge', DOT + 'williamsburg-bridge.shtml']
};

// =================================================================== HUDSON RIVER

// ------------------------------------------------------------ George Washington Bridge (1927–1931; lower deck 1962)
// Wikipedia (George Washington Bridge): main span 3,500 ft, 4,760 ft between anchorages, 119 ft
// wide (upper roadway 90 ft), towers 604 ft above the water; 212 ft clear at mid-span and 195 ft
// under the New York anchorage with the lower deck; the 1931 deck was 12 ft thick with no
// stiffening truss, the 1962 lower-deck sections 30 ft thick; four 36 in cables. Side spans
// 610 ft (New Jersey) and 650 ft (New York): the split is remembered from the Port Authority's
// fact sheet, whose page could not be re-read (script-rendered); 3,500 + 610 + 650 = the cited 4,760 ft. OSM tower outlines (ways 741784699, 741784700): 1,064.5 m apart (cited
// 1,066.8 m), bearing 104.4°, 72.5 × 28 m; New York anchorage 85 × 55 m centred 748 m from mid-span.
const GW = axisOf([-73.958774, 40.852866], [-73.946531, 40.850467]); // New Jersey tower → New York tower
const GW_TOP = 604 * FT;
const GW_NJ = -(GW.half + 610 * FT);
const GW_NY = GW.half + 650 * FT;
const GW_CX = 16.2; // cable pairs and tower legs about 106 ft apart (estimated)
const GW_HW = (119 * FT) / 2;
const GW_GREY = '#9AA0A3';
const CONC = '#BDB8AE';

/** Upper roadway: 212 ft clearance + 30 ft at mid-span, 195 + 30 ft at the New York anchorage (cited), parabolic between. */
const gwRoadZ = (y: number) => 242 * FT - 17 * FT * (y / GW_NY) ** 2;

function gwTower(b: MeshBuilder, y: number) {
  const zd = gwRoadZ(y);
  b.color(CONC).box(0, y, -3, 72, 28, 8);
  b.color(GW_GREY);
  const zs: number[] = [];
  for (let i = 0; i <= 12; i++) zs.push(5 + ((GW_TOP - 3 - 5) * i) / 12);
  const half = (z: number): [number, number] => {
    const t = (z - 5) / (GW_TOP - 8);
    return [6.6 - 1.2 * t, 10.5 - 5 * t];
  };
  for (const s of [-1, 1]) {
    latticeLeg(b, z => rect(s * GW_CX, y, 2 * half(z)[0], 2 * half(z)[1]), zs, 2.2, 0.6);
    b.box(s * GW_CX, y, GW_TOP - 3, 2 * half(GW_TOP)[0] + 2, 2 * half(GW_TOP)[1] + 2, 3);
  }
  // portals between the legs: an arch under the top, another under the roadway (both faces)
  const inner = (z: number) => GW_CX - half(z)[0];
  for (const [zs0, rise, zt] of [[GW_TOP - 48, 26, GW_TOP - 6], [zd - 44, 18, zd - 14]]) {
    for (const dy of [-1, 1]) {
      const yy = y + dy * (half(zt)[1] - 0.5);
      const hw = inner(zs0);
      const arch: V3[] = [];
      for (let i = 0; i <= 12; i++) {
        const x = -hw + (2 * hw * i) / 12;
        arch.push([x, yy, zs0 + rise * Math.sqrt(Math.max(0, 1 - (x / hw) ** 2))]);
      }
      b.polyline(arch, 1.5);
      b.beam([-hw, yy, zt], [hw, yy, zt], 1.5);
      for (let i = 0; i < 12; i += 2) {
        wire(b, arch[i], [arch[i + 2][0], yy, zt], 0.6);
        wire(b, arch[i + 2], [arch[i][0], yy, zt], 0.6);
      }
    }
  }
}

function gwBuild(b: MeshBuilder, lower: boolean) {
  const H = GW.half;
  const depth = lower ? 30 * FT : 12 * FT;
  const zb = (y: number) => gwRoadZ(y) - depth;
  b.frame(0, 0, 0, GW.bearing, () => {
    gwTower(b, -H);
    gwTower(b, H);
    for (const [y0, y1, n] of [[GW_NJ, -H, 6], [-H, H, 28], [H, GW_NY, 6]] as [number, number, number][]) {
      deckRun(b, y0, y1, n, gwRoadZ, GW_HW, lower ? 2.4 : depth, GW_GREY);
      if (lower) deckRun(b, y0, y1, n, y => zb(y) + 1.4, GW_HW - 2.5, 1.4, GW_GREY);
    }
    b.color(GW_GREY);
    if (lower) for (const x of [-GW_CX, GW_CX]) trussWall(b, x, GW_NJ, GW_NY, zb, y => gwRoadZ(y) - 2.4, 18.3, 0.9, 0.45, false);
    // four cables in two pairs; suspenders in the plane of each pair
    cables(b, {half: H, top: GW_TOP - 3, low: gwRoadZ(0) + 8, ends: [GW_NJ, GW_NY + 8], zEnds: [gwRoadZ(GW_NJ) + 6, gwRoadZ(GW_NY) + 3], xs: [-GW_CX - 1.4, -GW_CX + 1.4, GW_CX - 1.4, GW_CX + 1.4], w: 1.0, deckZ: gwRoadZ, every: 18.3, hangXs: [-GW_CX, GW_CX], hangW: 0.35, sideHung: true, sideSag: 3});
    // New York anchorage (the New Jersey cables are anchored in the rock of the Palisades)
    b.color(CONC).box(0, 748, 0, 55, 85, gwRoadZ(748) - 0.3);
    deckRun(b, GW_NY, 790, 2, gwRoadZ, GW_HW, 2.4, CONC);
    b.color(CONC).box(0, GW_NJ - 6, gwRoadZ(GW_NJ) - 14, 46, 12, 14);
    // 1962: the lower level runs on from the anchorage to the Trans-Manhattan Expressway cut
    if (lower) arcade(b, 790, 975, y => lerpAt([[790, zb(790) + 1.4], [975, 53]], y), 13, CONC, 30, 3, 1.6, 20);
  });
}

const GW_FACTS = {
  Construction: 'Sep 21, 1927 – Oct 1931; opened Oct 25, 1931 (Othmar Ammann, chief engineer; Cass Gilbert, architect); lower level built Jun 1959 – Aug 29, 1962',
  'Main span': '3,500 ft (1,067 m), nearly double the previous record; 4,760 ft between anchorages',
  Towers: 'braced steel, 604 ft (184 m) above the water; the planned stone cladding was never added',
  Cables: 'four main cables 36 in across, in two pairs'
};
const GW_SRC = [WIKI + 'George_Washington_Bridge'];
const GW_PLOTS = [plot(GW, -GW.half, 76, 32), plot(GW, GW.half, 76, 32), plot(GW, 748, 58, 88)];

const gwBridge1931: Landmark = {
  id: 'george_washington_bridge_1931',
  name: 'George Washington Bridge (single deck, 1931–1962)',
  kind: 'bridge',
  built: [1927.72, 1931.82],
  end: 1962.66,
  anchor: GW.anchor,
  build: b => gwBuild(b, false),
  facts: {
    ...GW_FACTS,
    Deck: 'one level, 119 ft wide and only 12 ft thick, with no stiffening truss: six lanes in 1931, eight from 1946',
    Model: 'towers on the OpenStreetMap outlines (1,064.5 m apart against the cited 1,066.8 m); side spans 610 and 650 ft (the split of the cited 4,760 ft is not re-verified); roadway heights from the clearances cited for the two-level bridge (212 and 195 ft plus the 30 ft lower deck); leg sections, cable planes, saddle height, sag and the tower bracing pattern are estimated; only the New York half lies inside the map'
  },
  sources: GW_SRC
};

const gwBridge: Landmark = {
  id: 'george_washington_bridge',
  name: 'George Washington Bridge',
  kind: 'bridge',
  built: [1962.6, 1962.66],
  end: 9999,
  anchor: GW.anchor,
  build: b => gwBuild(b, true),
  replaces: GW_PLOTS,
  facts: {
    ...GW_FACTS,
    Deck: 'two levels since Aug 29, 1962 (fourteen lanes): upper roadway 90 ft wide, the lower deck hung 30 ft below it between stiffening trusses; 212 ft clear at mid-span, 195 ft at the New York anchorage',
    Model: 'towers on the OpenStreetMap outlines (1,064.5 m apart against the cited 1,066.8 m); side spans 610 and 650 ft (the split of the cited 4,760 ft is not re-verified); anchorage plan from OpenStreetMap; leg sections, cable planes, saddle height, sag, tower bracing pattern and the lower-level approach are estimated; the terrain grid does not carry the New York anchorage and plaza fill, so the roadway ends above it; only the New York half lies inside the map'
  },
  sources: GW_SRC
};

// =================================================================== EAST RIVER (continued)

// ------------------------------------------------------------ Queensboro (Ed Koch) Bridge (1901–1909)
// Wikipedia (Queensboro Bridge): five steel spans, 3,725 ft: 469.5 (Manhattan anchor span), 1,182
// (west channel), 630 (Roosevelt Island), 984 (east channel), 459 ft (Queens anchor span); approach
// viaducts 1,052 ft (Manhattan) and 2,588 ft (Queens); two lines of trusses 60 ft apart, 45 to 118 ft
// deep, the towers 185 ft above the lower chords; 350 ft to the top; lower level 86 ft wide, upper
// 67 ft; at least 118 ft and at most 135–140 ft above mean high water (infobox: 130 ft clear);
// piers 130 × 40 ft at the base with a 50 ft arch. OSM pier outlines (ways 1016487161, …159, …155,
// …154, …157, …170) stand at −322.0, −180.1, 180.1, 370.9, 671.0 and 810.3 m from the middle of
// the west channel span: spans of 141.9, 360.2, 190.8, 300.1, 139.3 m against the cited 143.1,
// 360.3, 192.0, 299.9, 139.9 m. Bearing 119.6°.
const QB = axisOf([-73.95913, 40.758877], [-73.955417, 40.757267]); // Manhattan pier → Roosevelt Island western pier
const QB_P = [-322.0, -180.1, 180.1, 370.9, 671.0, 810.3];
const QB_ENDS: [number, number] = [QB_P[0] - 1052 * FT, QB_P[5] + 2588 * FT];
const QB_TX = 30 * FT;
const QB_STEEL = '#8D8676';

/** Lower chord: 135 ft at the middle of the bridge, 118 ft at the anchor piers (cited limits; the curve between is estimated). */
function qbChordZ(s: number) {
  const mid = (QB_P[0] + QB_P[5]) / 2;
  const a = (QB_P[5] - QB_P[0]) / 2;
  if (s < QB_P[0]) return lerpAt([[QB_ENDS[0], 18.8 - 1.5], [QB_P[0], 118 * FT]], s);
  if (s > QB_P[5]) return lerpAt([[QB_P[5], 118 * FT], [QB_ENDS[1], 6.4 - 1.5]], s);
  return 135 * FT - 17 * FT * ((s - mid) / a) ** 2;
}

/** Panel points (station, truss depth): 185 ft at the towers, 45 ft at the anchor piers and mid-channel, 118 ft over the island. */
function qbNodes(): [number, number][] {
  const out: [number, number][] = [];
  const PEAK = 185 * FT;
  const LOW = 45 * FT;
  const ISL = 118 * FT;
  const seg = (s0: number, s1: number, n: number, f: (t: number) => number, last = false) => {
    for (let i = 0; i < n + (last ? 1 : 0); i++) out.push([s0 + ((s1 - s0) * i) / n, f(i / n)]);
  };
  const up = (lo: number) => (t: number) => lo + (PEAK - lo) * Math.pow(t, 1.7);
  const down = (lo: number) => (t: number) => lo + (PEAK - lo) * Math.pow(1 - t, 1.7);
  seg(QB_P[0], QB_P[1], 6, up(LOW));
  seg(QB_P[1], 0, 8, down(LOW));
  seg(0, QB_P[2], 8, up(LOW));
  seg(QB_P[2], (QB_P[2] + QB_P[3]) / 2, 4, down(ISL));
  seg((QB_P[2] + QB_P[3]) / 2, QB_P[3], 4, up(ISL));
  seg(QB_P[3], (QB_P[3] + QB_P[4]) / 2, 7, down(LOW));
  seg((QB_P[3] + QB_P[4]) / 2, QB_P[4], 7, up(LOW));
  seg(QB_P[4], QB_P[5], 6, down(LOW), true);
  return out;
}

function queensboroBuild(b: MeshBuilder) {
  const nodes = qbNodes();
  const zb = qbChordZ;
  const floor = (s: number) => zb(s) + 1.5;
  const upper = (s: number) => zb(s) + 9; // upper roadway (height above the lower level estimated)
  b.frame(0, 0, 0, QB.bearing, () => {
    // two decks through the trusses
    deckRun(b, QB_P[0], QB_P[5], 30, floor, 43 * FT, 1.5, QB_STEEL);
    deckRun(b, QB_P[0], QB_P[5], 30, upper, 33.5 * FT, 1.0, QB_STEEL);
    b.color(QB_STEEL);
    for (const x of [-QB_TX, QB_TX]) {
      b.beam([x, QB_P[0], zb(QB_P[0])], [x, QB_P[5], zb(QB_P[5])], 1.2);
      for (let i = 0; i < nodes.length; i++) {
        const [s, h] = nodes[i];
        const tower = QB_P.slice(1, 5).some(p => Math.abs(p - s) < 0.01);
        if (tower) b.beam([x, s, zb(s)], [x, s, zb(s) + h], 2.0);
        else wire(b, [x, s, zb(s)], [x, s, zb(s) + h], 0.6);
        if (i === nodes.length - 1) break;
        const [s1, h1] = nodes[i + 1];
        b.beam([x, s, zb(s) + h], [x, s1, zb(s1) + h1], 1.0);
        if (h1 > h) wire(b, [x, s, zb(s)], [x, s1, zb(s1) + h1], 0.5);
        else wire(b, [x, s, zb(s) + h], [x, s1, zb(s1)], 0.5);
      }
    }
    for (let i = 0; i < nodes.length; i += 2) {
      const [s, h] = nodes[i];
      b.beam([-QB_TX, s, zb(s) + h], [QB_TX, s, zb(s) + h], 0.6);
    }
    // towers on the four river piers: portal bracing and finials to 350 ft
    for (const s of QB_P.slice(1, 5)) {
      const top = zb(s) + 185 * FT;
      for (const z of [top, top - 12, top - 24]) b.beam([-QB_TX, s, z], [QB_TX, s, z], 1.0);
      wire(b, [-QB_TX, s, top - 12], [QB_TX, s, top], 0.5);
      wire(b, [QB_TX, s, top - 12], [-QB_TX, s, top], 0.5);
      wire(b, [-QB_TX, s, top - 24], [QB_TX, s, top - 12], 0.5);
      wire(b, [QB_TX, s, top - 24], [-QB_TX, s, top - 12], 0.5);
      for (const x of [-QB_TX, QB_TX]) b.pyramid(rect(x, s, 2.6, 2.6), top, [x, s, 350 * FT]);
    }
    // masonry piers: two columns joined above a 50 ft arch (130 × 40 ft at the base)
    b.color(GRANITE);
    for (const s of QB_P) {
      const end = s === QB_P[0] || s === QB_P[5];
      for (const sx of [-1, 1]) b.loft([rect(sx * 13.7, s, 12.2, 12.2), rect(sx * 12.6, s, 9.8, end ? 8 : 9.5)], [-3, zb(s) - 0.6]);
      archStrut(b, s, 7.7, zb(s) - 16, 7.5, zb(s) - 0.6, end ? 7 : 8.5);
    }
    // approaches: the stone-vaulted Manhattan viaduct and the steel viaduct to Queens Plaza
    arcade(b, QB_P[0], QB_ENDS[0], floor, 43 * FT, GRANITE, 27, 12);
    arcade(b, QB_P[5], QB_ENDS[1], floor, 43 * FT, QB_STEEL, 30, 2.2, 2.2, 2 * QB_TX);
  });
}

const queensboroBridge: Landmark = {
  id: 'queensboro_bridge',
  name: 'Queensboro Bridge (Ed Koch Queensboro Bridge)',
  kind: 'bridge',
  built: [1901.5, 1909.24],
  end: 9999,
  anchor: QB.anchor,
  build: queensboroBuild,
  replaces: QB_P.map(s => plot(QB, s, 42, 14)),
  facts: {
    Construction: '1901 – 1909; opened Mar 30, 1909 (Gustav Lindenthal, engineer; Henry Hornbostel, architect)',
    Form: 'double cantilever with no suspended spans, 3,725 ft in five spans: 469.5, 1,182 (west channel), 630 (Roosevelt Island), 984 (east channel) and 459 ft; approach viaducts 1,052 ft (Manhattan) and 2,588 ft (Queens)',
    Trusses: 'two lines 60 ft apart, 45 to 118 ft deep; towers 185 ft above the lower chords, 350 ft to the top of the finials',
    Deck: 'two levels: lower 86 ft wide, upper 67 ft; about 130 ft clear',
    Model: 'pier positions from OpenStreetMap (spans within 1.2 m of the cited lengths); the lower-chord curve between the cited 118 and 135 ft, the top-chord curve between the cited depths, the level of the upper deck, pier taper and the approach grades are estimated; the upper-level ramps in Queens and Manhattan are not modelled; the Manhattan approach is drawn its cited 1,052 ft to Second Avenue'
  },
  sources: [WIKI + 'Queensboro_Bridge', DOT + 'queensboro-bridge.shtml']
};

// =================================================================== THE NARROWS

// ------------------------------------------------------------ Verrazzano-Narrows Bridge (1959–1964)
// Wikipedia (Verrazzano–Narrows Bridge): main span 4,260 ft, towers 693 ft, 103 ft wide, 228 ft
// clear at mean high water, anchorages 229 × 129 ft; construction from Aug 13/14, 1959; upper
// level opened Nov 21, 1964, lower level Jun 28, 1969. OSM tower outlines (ways 1016642058,
// 1016642060): 1,296.3 m apart (cited 1,298.4 m), bearing 67.1°, about 41 × 13 m; anchorages
// (87–89 m × 48–49 m) centred 1,037 m (Staten Island) and 1,048 m (Brooklyn) from mid-span.
// Overture's bridge flag runs from 1,270 m (Staten Island) to 1,255 m (Brooklyn) from mid-span.
const VZ = axisOf([-74.052506, 40.604056], [-74.038377, 40.608619]); // Staten Island tower → Brooklyn tower
const VZ_TOP = 693 * FT;
const VZ_A = 1018; // cable entry at the anchorages (OSM)
const VZ_ENDS: [number, number] = [-1270, 1255];
const VZ_HW = (103 * FT) / 2;
const VZ_TRUSS = 24 * FT; // depth between the two decks (estimated)
const VZ_STEEL = '#8E99A0';

/** Upper roadway: 228 ft clear + the truss at mid-span (cited clearance); tower, anchorage and end heights estimated. */
function vzRoadZ(y: number) {
  const mid = 228 * FT + VZ_TRUSS;
  const a = Math.abs(y);
  if (a <= VZ.half) return mid - 7 * (a / VZ.half) ** 2;
  return y < 0 ? lerpAt([[VZ.half, mid - 7], [VZ_A, 57], [-VZ_ENDS[0], 36.6]], a) : lerpAt([[VZ.half, mid - 7], [VZ_A, 57], [VZ_ENDS[1], 45]], a);
}

function vzTower(b: MeshBuilder, y: number) {
  const zd = vzRoadZ(y);
  const cx = 15.7;
  b.color(CONC).box(0, y, -3, 70, 40, 6.5);
  b.color(VZ_STEEL);
  for (const s of [-1, 1]) b.loft([rect(s * cx, y, 9.4, 13), rect(s * cx, y, 7.6, 9)], [3.5, VZ_TOP]);
  archStrut(b, y, cx - 3.8, VZ_TOP - 30, 12, VZ_TOP - 6, 7);
  archStrut(b, y, cx - 4.5, zd - VZ_TRUSS - 26, 10, zd - VZ_TRUSS - 6, 9);
}

function verrazzanoBuild(b: MeshBuilder) {
  const H = VZ.half;
  const zb = (y: number) => vzRoadZ(y) - VZ_TRUSS;
  b.frame(0, 0, 0, VZ.bearing, () => {
    vzTower(b, -H);
    vzTower(b, H);
    for (const [y0, y1, n] of [[-VZ_A, -H, 6], [-H, H, 30], [H, VZ_A, 6]] as [number, number, number][]) {
      deckRun(b, y0, y1, n, vzRoadZ, VZ_HW, 1.6, VZ_STEEL);
      deckRun(b, y0, y1, n, y => zb(y) + 1.2, VZ_HW, 1.2, VZ_STEEL);
    }
    b.color(VZ_STEEL);
    for (const x of [-VZ_HW, VZ_HW]) trussWall(b, x, -VZ_A, VZ_A, zb, y => vzRoadZ(y) - 1.6, 30, 0.9, 0.45, false);
    cables(b, {half: H, top: VZ_TOP - 2, low: vzRoadZ(0) + 4, ends: [-VZ_A - 10, VZ_A + 10], zEnds: [vzRoadZ(VZ_A) + 2, vzRoadZ(VZ_A) + 2], xs: [-VZ_HW - 0.9, -VZ_HW + 0.9, VZ_HW - 0.9, VZ_HW + 0.9], w: 1.0, deckZ: vzRoadZ, every: 30, hangXs: [-VZ_HW, VZ_HW], hangW: 0.35, sideHung: true, sideSag: 9});
    // anchorages (229 × 129 ft) and the approach viaducts
    b.color(CONC);
    for (const [yc, len] of [[-1037, 87], [1048, 89]]) {
      b.box(0, yc, 0, 129 * FT, len, vzRoadZ(yc) - 0.4);
      deckRun(b, yc - len / 2, yc + len / 2, 2, vzRoadZ, VZ_HW, 1.6, CONC);
    }
    arcade(b, -1080, VZ_ENDS[0], vzRoadZ, VZ_HW, CONC, 38, 3, 2.4, 24);
    arcade(b, 1092, VZ_ENDS[1], vzRoadZ, VZ_HW, CONC, 38, 3, 2.4, 24);
  });
}

const verrazzanoBridge: Landmark = {
  id: 'verrazzano_narrows_bridge',
  name: 'Verrazzano-Narrows Bridge',
  kind: 'bridge',
  built: [1959.62, 1964.89],
  end: 9999,
  anchor: VZ.anchor,
  build: verrazzanoBuild,
  replaces: [plot(VZ, -VZ.half, 74, 44), plot(VZ, VZ.half, 74, 44), plot(VZ, -1037, 44, 92), plot(VZ, 1048, 44, 92)],
  facts: {
    Construction: 'Aug 13, 1959 – Nov 1964; upper level opened Nov 21, 1964, lower level Jun 28, 1969 (Othmar Ammann)',
    'Main span': '4,260 ft (1,298 m), the longest in the world until 1981',
    Towers: 'steel, 693 ft (211 m) above mean high water',
    Deck: '103 ft wide on two levels between stiffening trusses; 228 ft clear at mean high water',
    Anchorages: '229 × 129 ft each',
    Model: 'shown with both decks (the lower roadway opened in 1969 inside trusses built in 1964); towers on the OpenStreetMap outlines (1,296.3 m apart against the cited 1,298.4 m); anchorage positions from OpenStreetMap; leg sections, portal struts, truss depth (24 ft), cable planes, saddle height, sag and the roadway heights away from mid-span are estimated; the approach viaducts are straight and end 45 m up at the Brooklyn end, where the Belt Parkway ramps take over'
  },
  sources: [WIKI + 'Verrazzano%E2%80%93Narrows_Bridge']
};

// =================================================================== HELL GATE AND THE TRIBOROUGH

const HG_LINE: V2[] = [[-73.907857, 40.805192], [-73.912460, 40.800604], [-73.913074, 40.800000], [-73.913369, 40.799743], [-73.918099, 40.796544], [-73.918713, 40.796088], [-73.919287, 40.795621], [-73.919988, 40.794999], [-73.920418, 40.794575], [-73.924173, 40.790576], [-73.924778, 40.789895], [-73.925106, 40.789418], [-73.925343, 40.788964], [-73.925543, 40.788437], [-73.925650, 40.787991], [-73.925709, 40.787472], [-73.925694, 40.786992], [-73.925627, 40.786518], [-73.925478, 40.786048], [-73.925240, 40.785564], [-73.924960, 40.785102], [-73.924658, 40.784696], [-73.924263, 40.784280], [-73.923828, 40.783907], [-73.923137, 40.783365], [-73.921418, 40.782081], [-73.920254, 40.781244], [-73.915382, 40.777609], [-73.914646, 40.777001], [-73.913479, 40.775923], [-73.912729, 40.775151], [-73.911985, 40.774305], [-73.911415, 40.773596], [-73.910689, 40.772578], [-73.908541, 40.769083]]; // Overture rail segment fb010fe0 (Northeast Corridor, bridge flag) moved 7 m to the middle of the four-track deck; Bronx end → Queens end
const RFK_Q: V2[][] = [
  [[-73.924246, 40.776331], [-73.923170, 40.774888], [-73.922697, 40.774335], [-73.921962, 40.773678], [-73.921552, 40.773375], [-73.920903, 40.772942]],
  [[-73.924104, 40.776394], [-73.922895, 40.774814], [-73.922400, 40.774278], [-73.922037, 40.773948], [-73.921637, 40.773635], [-73.920324, 40.772709]]
]; // Queens approach, both carriageways, from the anchorage outward
const RFK_W: V2[][] = [
  [[-73.929287, 40.782945], [-73.929688, 40.783479], [-73.929862, 40.783758], [-73.929999, 40.784070], [-73.930101, 40.784416], [-73.930150, 40.784701], [-73.930151, 40.785177], [-73.930074, 40.785625], [-73.929951, 40.785979], [-73.929724, 40.786418], [-73.929541, 40.786676], [-73.926591, 40.790027]],
  [[-73.929147, 40.783007], [-73.929536, 40.783535], [-73.929714, 40.783836], [-73.929850, 40.784142], [-73.929931, 40.784440], [-73.929991, 40.784941], [-73.929962, 40.785302], [-73.929872, 40.785670], [-73.929737, 40.785976], [-73.929564, 40.786290], [-73.929342, 40.786601], [-73.928576, 40.787506], [-73.924592, 40.791983]]
]; // Wards / Randalls Island viaduct, both carriageways, from the anchorage to the junction
const RFK_W2: V2[] = [[-73.926591, 40.790027], [-73.924842, 40.791957]]; // southbound link at the junction (Overture f69b3055), from the viaduct to the junction
const RFK_B: V2[][] = [
  [[-73.918756, 40.799360], [-73.917151, 40.801560]],
  [[-73.919295, 40.798381], [-73.919426, 40.798203]],
  [[-73.918618, 40.799302], [-73.917156, 40.801293]],
  [[-73.919404, 40.798428], [-73.920549, 40.796886], [-73.921447, 40.795772], [-73.924392, 40.792411], [-73.924842, 40.791957]],
  [[-73.919426, 40.798203], [-73.920539, 40.796721], [-73.921139, 40.795972], [-73.924275, 40.792391], [-73.924592, 40.791983]]
]; // Bronx Kill approaches and the Randalls Island viaduct to the junction, from the truss outward
const RFK_BK: [V2, V2] = [[-73.919357, 40.798408], [-73.918687, 40.799331]]; // ends of the Bronx Kill truss span (383 ft) on the carriageways' centre line

// ------------------------------------------------------------ Hell Gate Bridge (1912–1917)
// Wikipedia (Hell Gate Bridge): main span 1,017 ft between the outer faces of the towers, 977.5 ft
// clear between their inner faces; deck 145 ft above mean high water at mid-span with 135 ft clear
// below; the arch reaches 300–305 ft; towers 220 ft high, concrete clad in granite; lower chords
// 7–11 ft thick on hinges at the tower bases; Wards Island viaduct about 2,650 ft (30 plate-girder
// spans of 86–93 ft on concrete arch piers up to 120 ft high, 20 × 65 ft at the base); Randalls
// Island viaduct about 1,965 ft, 75–80 ft high; four inverted bowstring spans (1,154 ft) over
// Little Hell Gate; a 350 ft two-span truss over the Bronx Kill; 17,000 ft in all; begun 1912,
// finished 1916, dedicated Mar 9, 1917. OSM tower outlines (ways 1016643613, 1016643614): centroids
// 328.5 m apart, 42–44 m across × 27–28 m along, outer faces 357 m apart; the model keeps their
// midpoint, bearing (134.6°) and outer faces and sets the inner faces the cited 977.5 ft apart.
// Along HG_LINE (5,048 m, Bronx → Queens): OSM's Bronx Kill piers at 1,086 and 1,213 m; the low
// ground of the filled Little Hell Gate from 1,811 to 2,163 m (= the Bronx Kill pier + the cited
// 1,965 ft of Randalls Island viaduct, then the cited 1,154 ft); the arch towers at 2,991 and 3,320 m.
const HG = axisOf([-73.923383, 40.783592], [-73.920608, 40.781506]); // Wards Island tower → Queens tower
const HG_S = (977.5 * FT) / 2;
const HG_RAIL = 145 * FT;
const HG_CROWN = 305 * FT;
const HG_TOWER = 220 * FT;
const HG_RED = '#8A413D';
const HG_STONE = '#C6BFB0';
const BALLAST = '#6B6660';
const HG_MID = 3155.3; // the arch's mid-span on HG_LINE

/** Rail level along HG_LINE: 145 ft through the arch (cited); the grades down to the embankments at both ends are estimated. */
const hgRailZ = (d: number) => lerpAt([[0, 12.8], [HG_MID - 178, HG_RAIL], [HG_MID + 178, HG_RAIL], [5048, 22]], d);

function hgPier(b: MeshBuilder, zTop: number) {
  b.color(HG_STONE);
  for (const s of [-1, 1]) b.box(s * 6.7, 0, 0, 4.6, 5.5, zTop, {top: false});
  archStrut(b, 0, 4.4, Math.max(2, zTop - 9), Math.min(6, zTop - 3), zTop, 5.5);
}

function hgTower(b: MeshBuilder, y: number, out: number) {
  const yc = y + out * 14.5;
  b.color(HG_STONE);
  b.box(0, yc, -3, 46, 31, 5);
  for (const s of [-1, 1]) b.loft([rect(s * 15.3, yc, 12.4, 29), rect(s * 14.6, yc, 10.4, 26)], [0, HG_TOWER - 4]);
  b.box(0, yc, 0, 18.4, 29, HG_RAIL - 3.2);
  archStrut(b, yc, 9.4, HG_RAIL + 9, 5, HG_TOWER - 4, 26);
  b.box(0, yc, HG_TOWER - 4, 41, 27.5, 1.5);
  b.box(0, yc, HG_TOWER - 2.5, 38.5, 25.5, 2.5);
}

function hellGateBuild(b: MeshBuilder) {
  const path = pathOf(HG.anchor, HG_LINE);
  const S = HG_S;
  const HINGE = 8; // hinge height (estimated)
  const LOWC = HG_CROWN - 0.7 - 40 * FT; // truss depth 40 ft at the crown, 140 ft at the hinges (estimated)
  const zl = (y: number) => LOWC - (LOWC - HINGE) * (y / S) ** 2;
  const zu = (y: number) => zl(y) + 40 * FT + 100 * FT * Math.abs(y / S) ** 2.2;
  const X = 30 * FT; // arch ribs 60 ft apart (estimated)
  const N = 22;
  b.frame(0, 0, 0, HG.bearing, () => {
    hgTower(b, -S, -1);
    hgTower(b, S, 1);
    b.color(HG_RED);
    for (const x of [-X, X]) {
      for (let i = 0; i < N; i++) {
        const a = -S + (2 * S * i) / N;
        const c = -S + (2 * S * (i + 1)) / N;
        b.beam([x, a, zl(a)], [x, c, zl(c)], 2.6);
        b.beam([x, a, zu(a)], [x, c, zu(c)], 1.4);
        wire(b, [x, a, zl(a)], [x, a, zu(a)], 0.7);
        if (i < N / 2) wire(b, [x, a, zu(a)], [x, c, zl(c)], 0.6);
        else wire(b, [x, a, zl(a)], [x, c, zu(c)], 0.6);
        // hangers where the arch is above the deck, posts where it is below
        if (i > 0 && Math.abs(zl(a) - HG_RAIL + 3) > 2.5) wire(b, [x, a, Math.min(zl(a), HG_RAIL - 3)], [x, a, Math.max(zl(a), HG_RAIL - 3)], 0.5);
      }
      wire(b, [x, S, zl(S)], [x, S, zu(S)], 0.7);
    }
    for (let i = 0; i <= N; i++) {
      const a = -S + (2 * S * i) / N;
      if (zu(a) > HG_RAIL + 9) b.beam([-X, a, zu(a)], [X, a, zu(a)], 0.6);
      if (zl(a) > HG_RAIL + 9) b.beam([-X, a, zl(a)], [X, a, zl(a)], 0.6);
    }
    deckRun(b, -S - 29, S + 29, 10, () => HG_RAIL, 9.3, 3.0, HG_RED, BALLAST);
  });
  // plate-girder viaducts on concrete arch piers (a pier drawn for every second real one)
  const pier = (zTop: number) => hgPier(b, zTop);
  for (const [d0, d1] of [[0, 1096], [1203, 1811], [2163, HG_MID - 178], [HG_MID + 178, 5048]]) pathDeck(b, path, d0, d1, hgRailZ, 18.3, 2.7, HG_RED, BALLAST, 54, pier);
  // Bronx Kill: two fixed truss spans (350 ft together) between the big piers
  for (let k = 0; k < 2; k++) {
    onPath(b, path, 1096 + k * 53.3, 1096 + (k + 1) * 53.3, L => {
      const z0 = hgRailZ(1096 + k * 53.3);
      const z1 = hgRailZ(1096 + (k + 1) * 53.3);
      const zf = (y: number) => z0 + ((z1 - z0) * y) / L;
      deckSeg(b, 0, L, z0, z1, 8.8, 1.6, HG_RED, BALLAST);
      b.color(HG_RED);
      throughTruss(b, 0, L, y => zf(y) - 1.6, flatTop(10), 18.6, 6);
      b.color(HG_STONE).box(0, k === 0 ? -5 : L / 2, -3, 22, k === 0 ? 10 : 0.01, z0 + 1);
      b.box(0, L + (k === 1 ? 5 : 0), -3, 22, k === 1 ? 10 : 5, z1 + 1.4);
    });
  }
  // Little Hell Gate: four inverted bowstring spans (1,154 ft)
  const span = (1154 * FT) / 4;
  for (let k = 0; k < 4; k++) {
    onPath(b, path, 1811 + k * span, 1811 + (k + 1) * span, L => {
      const z0 = hgRailZ(1811 + k * span);
      const z1 = hgRailZ(1811 + (k + 1) * span);
      const zt = (y: number) => z0 + ((z1 - z0) * y) / L - 2.4;
      deckSeg(b, 0, L, z0, z1, 9.2, 2.4, HG_RED, BALLAST);
      b.color(HG_RED);
      for (const x of [-8.6, 8.6]) {
        for (let i = 0; i < 8; i++) {
          const a = (L * i) / 8;
          const c = (L * (i + 1)) / 8;
          const sag = (y: number) => zt(y) - 12 * 4 * (y / L) * (1 - y / L);
          b.beam([x, a, sag(a)], [x, c, sag(c)], 1.0);
          if (i > 0) wire(b, [x, a, sag(a)], [x, a, zt(a)], 0.5);
        }
      }
      b.color(HG_STONE);
      for (const y of k === 3 ? [0, L] : [0]) b.box(0, y, 0, 20, 5, (y === 0 ? z0 : z1) - 2.6, {top: false});
    });
  }
}

const hellGateBridge: Landmark = {
  id: 'hell_gate_bridge',
  name: 'Hell Gate Bridge',
  kind: 'bridge',
  built: [1912.5, 1917.19],
  end: 9999,
  anchor: HG.anchor,
  build: hellGateBuild,
  replaces: [plot(HG, -HG_S - 14.5, 48, 32), plot(HG, HG_S + 14.5, 48, 32)],
  facts: {
    Construction: '1912 – 1916; dedicated Mar 9, 1917 (Gustav Lindenthal, with Othmar Ammann and David Steinman; Henry Hornbostel, architect) for the New York Connecting Railroad',
    'Main span': 'two-hinged steel arch, 1,017 ft between the outer faces of the towers and 977.5 ft clear: the longest steel arch in the world until 1931',
    Heights: 'deck 145 ft above mean high water, 135 ft clear; arch 305 ft; towers 220 ft, concrete faced with granite',
    Viaducts: '17,000 ft in all: plate girders on concrete arch piers across Wards and Randalls Islands, four inverted bowstring spans (1,154 ft) over Little Hell Gate, a 350 ft two-span truss over the Bronx Kill',
    Tracks: 'built for four (two passenger, two freight); three today',
    Model: 'follows the Overture track moved 7 m to the middle of the deck; tower faces set 977.5 ft apart about the OpenStreetMap towers; rib spacing, truss depth of the arch (40 ft at the crown, 140 ft at the hinges), hinge height, tower plan above the base, the rail grades away from the arch and the embankment heights at both ends are estimated; one pier is drawn for every two real ones; the Little Hell Gate spans are placed on the filled channel (low ground), which agrees with the cited viaduct lengths'
  },
  sources: [WIKI + 'Hell_Gate_Bridge']
};

// ------------------------------------------------------------ Triborough (Robert F. Kennedy) Bridge (1929–1936)
// Wikipedia (Robert F. Kennedy Bridge): East River suspension span: main span 1,380 ft, side spans
// 700 ft, 2,780 ft in all, deck 98 ft wide, towers 315 ft above mean high water, 143 ft clear, two
// 20 in cables. Harlem River lift span: movable span 310 ft long and 92 ft wide, side spans 195 ft,
// towers 210 ft above mean high water, 55 ft clear closed and 135 ft raised. Bronx Kill: truss span
// 383 ft with 1,217 ft of approaches, 55 ft clear. Viaduct on concrete piers 60–140 ft apart, 62 ft
// above mean high water at Little Hell Gate. Groundbreaking Oct 25, 1929; opened Jul 11, 1936.
// OSM: suspension towers (ways 1016642595, 1016642596) 419.1 m apart (cited 420.6 m), bearing 149.8°;
// lift towers (ways 1016646459, 1016646456) 104.0 m apart centre to centre, 34.6 × 7.2 m: the model
// keeps their midpoint and bearing (119.0°) and sets their faces the cited 310 ft apart. The Bronx
// Kill truss is centred on the kill where Overture's two carriageways cross it (base water layer).
const RK = axisOf([-73.927945, 40.781308], [-73.925444, 40.778032]); // Wards Island tower → Queens tower
const RK_A = RK.half + 700 * FT;
const RK_TOP = 315 * FT;
const RK_HW = (98 * FT) / 2;
const RK_TRUSS = 20 * FT; // stiffening truss under the roadway (depth estimated)
const RK_VIA = 62 * FT; // viaduct roadway on the islands
const RK_GREY = '#8F9B9A';

function rkRoadZ(y: number) {
  const a = Math.abs(y);
  const mid = 143 * FT + RK_TRUSS;
  if (a <= RK.half) return mid - 3.2 * (a / RK.half) ** 2;
  return lerpAt([[RK.half, mid - 3.2], [RK_A, 40]], a); // height at the anchorages estimated
}

function rkPier(b: MeshBuilder, zTop: number) {
  b.color(CONC);
  for (const s of [-1, 1]) b.box(s * 4.2, 0, 0, 1.8, 1.8, zTop - 1.4, {top: false});
  b.box(0, 0, zTop - 1.4, 11.5, 2, 1.4);
}

/** Both carriageways of a viaduct: paths in lon/lat, height by distance from the first point. */
function rkViaduct(b: MeshBuilder, anchor: V2, lines: V2[][], zf: (d: number, len: number) => number) {
  for (const ll of lines) {
    const p = pathOf(anchor, ll);
    pathDeck(b, p, 0, p.len, d => zf(d, p.len), 13.5, 2, CONC, ROAD, 42, zTop => rkPier(b, zTop));
  }
}

function rkSuspensionBuild(b: MeshBuilder) {
  const H = RK.half;
  const CX = RK_HW + 0.8;
  b.frame(0, 0, 0, RK.bearing, () => {
    for (const y of [-H, H]) {
      const zd = rkRoadZ(y);
      b.color(CONC).box(0, y, -3, 42, 13, 9);
      b.color(RK_GREY);
      for (const s of [-1, 1]) {
        b.loft([rect(s * CX, y, 4.4, 5.4), rect(s * CX, y, 3.2, 3.8)], [6, RK_TOP - 2]);
        b.box(s * CX, y, RK_TOP - 2, 4.2, 4.8, 2);
      }
      archStrut(b, y, CX - 1.8, RK_TOP - 14, 3, RK_TOP - 5, 3);
      archStrut(b, y, CX - 2.1, zd - RK_TRUSS - 12, 3, zd - RK_TRUSS - 4, 3.6);
    }
    for (const [y0, y1, n] of [[-RK_A, -H, 5], [-H, H, 14], [H, RK_A, 5]] as [number, number, number][]) deckRun(b, y0, y1, n, rkRoadZ, RK_HW, 1.5, RK_GREY);
    b.color(RK_GREY);
    for (const x of [-RK_HW + 1.2, RK_HW - 1.2]) trussWall(b, x, -RK_A, RK_A, y => rkRoadZ(y) - RK_TRUSS, y => rkRoadZ(y) - 1.5, 12, 0.7, 0.35);
    cables(b, {half: H, top: RK_TOP - 1.5, low: rkRoadZ(0) + 2.5, ends: [-RK_A - 8, RK_A + 8], zEnds: [41, 41], xs: [-CX, CX], w: 0.7, deckZ: rkRoadZ, every: 12, sideHung: true, sideSag: 4, hangW: 0.3});
    b.color(CONC);
    for (const s of [-1, 1]) b.box(0, s * (RK_A + 22), 0, 38, 46, 39.6);
  });
  // Queens approach (ends about 10 m above the terrain grid, on the embankment to the Grand Central Parkway: estimated)
  rkViaduct(b, RK.anchor, RFK_Q, (d, len) => 40 - (20 * d) / len);
  // Wards Island viaduct: down from the anchorage to the cited 62 ft, then level to the junction
  rkViaduct(b, RK.anchor, RFK_W, d => Math.max(RK_VIA + 1.5, 40 - 0.035 * d));
  rkViaduct(b, RK.anchor, [RFK_W2], () => RK_VIA + 1.5);
}

const RK_SRC = [WIKI + 'Robert_F._Kennedy_Bridge'];
const RK_BUILT: [number, number] = [1929.82, 1936.53];

const rfkSuspension: Landmark = {
  id: 'rfk_bridge_suspension',
  name: 'Triborough (Robert F. Kennedy) Bridge: East River suspension span',
  kind: 'bridge',
  built: RK_BUILT,
  end: 9999,
  anchor: RK.anchor,
  build: rkSuspensionBuild,
  replaces: [plot(RK, -RK.half, 44, 14), plot(RK, RK.half, 44, 14), plot(RK, -RK_A - 22, 40, 48), plot(RK, RK_A + 22, 40, 48)],
  facts: {
    Construction: 'Oct 25, 1929 – Jul 1936 (work stopped in the Depression and resumed in 1933; Allston Dana, design engineer, with Othmar Ammann; Aymar Embury II, architect); opened Jul 11, 1936',
    'Main span': '1,380 ft (420.6 m); side spans 700 ft; 2,780 ft between anchorages',
    Towers: 'steel, 315 ft (96 m) above mean high water',
    Deck: '98 ft wide; 143 ft clear at mid-span; two cables 20 in across',
    Viaducts: 'steel girders on concrete piers 60–140 ft apart across Wards and Randalls Islands, 62 ft above mean high water at Little Hell Gate',
    Model: 'towers on the OpenStreetMap outlines (419.1 m apart against the cited 420.6 m); viaducts follow Overture\'s two carriageways from the anchorages to Astoria and to the junction on Randalls Island; stiffening-truss depth, tower leg sections and struts, saddle height and sag, anchorage blocks, roadway heights other than the cited clearance and the viaduct height, and the Queens end height are estimated'
  },
  sources: RK_SRC
};

// Harlem River lift span
const RL = axisOf([-73.928721, 40.800717], [-73.92764, 40.800262]); // Manhattan-side tower → Randalls Island-side tower
const RL_T = (310 * FT) / 2 + 3.6; // tower centres: faces 310 ft apart, towers 7.2 m deep (OSM)
const RL_END = RL_T + 3.6 + 195 * FT;
const RL_LOW = 55 * FT;
const RL_TOP = 210 * FT;

function rkLiftBuild(b: MeshBuilder) {
  const road = RL_LOW + 1.8;
  const zf = (y: number) => lerpAt([[RL_END, road], [476, 11]], y);
  b.frame(0, 0, 0, RL.bearing, () => {
    // lift span and the two side spans (through trusses; depths estimated)
    deckSeg(b, -RL_END, RL_END, road, road, 46 * FT, 1.8, RK_GREY);
    b.color(RK_GREY);
    throughTruss(b, -RL_T + 3.6, RL_T - 3.6, () => RL_LOW, flatTop(12), 92 * FT, 8);
    for (const s of [-1, 1]) throughTruss(b, s * (RL_T + 3.6), s * RL_END, () => RL_LOW, flatTop(8), 92 * FT, 5);
    // towers: two braced legs each, sheave girders on top, counterweights hanging near the top
    for (const s of [-1, 1]) {
      const y = s * RL_T;
      b.color(CONC).box(0, y, -3, 40, 11, RL_LOW + 2);
      b.color(RK_GREY);
      const zs: number[] = [];
      for (let i = 0; i <= 6; i++) zs.push(RL_LOW - 1 + ((RL_TOP - 3 - RL_LOW + 1) * i) / 6);
      for (const sx of [-1, 1]) latticeLeg(b, () => rect(sx * 15.5, y, 3.6, 7.2), zs, 1.0, 0.4);
      for (const z of zs.slice(2)) b.beam([-13.7, y, z], [13.7, y, z], 0.7);
      for (let i = 2; i < zs.length - 1; i++) {
        wire(b, [-13.7, y, zs[i]], [13.7, y, zs[i + 1]], 0.4);
        wire(b, [13.7, y, zs[i]], [-13.7, y, zs[i + 1]], 0.4);
      }
      b.box(0, y, RL_TOP - 3, 36, 8, 3);
      b.color('#8F8A80').box(0, y + s * 5.2, RL_TOP - 16, 27, 2.4, 9);
    }
    // Randalls Island viaduct to the toll plaza
    arcade(b, RL_END, 476, zf, 46 * FT, CONC, 36, 2, 2, 22);
  });
}

const rfkLift: Landmark = {
  id: 'rfk_bridge_harlem_river_lift',
  name: 'Triborough (Robert F. Kennedy) Bridge: Harlem River lift span',
  kind: 'bridge',
  built: RK_BUILT,
  end: 9999,
  anchor: RL.anchor,
  build: rkLiftBuild,
  replaces: [plot(RL, -RL_T, 42, 12), plot(RL, RL_T, 42, 12)],
  facts: {
    Opened: 'Jul 11, 1936, with the rest of the Triborough Bridge (construction from 1929)',
    'Lift span': '310 ft long and 92 ft wide, the largest lift-bridge deck in the world when built; side spans 195 ft',
    Towers: '210 ft (64 m) above mean high water',
    Clearance: '55 ft closed, 135 ft raised',
    Model: 'shown closed; tower faces set 310 ft apart about the midpoint of the OpenStreetMap tower outlines (104.0 m centre to centre there); truss depths, tower bracing, counterweights, pier sizes and the roadway height above the cited clearance are estimated; the ramps to 125th Street and the Harlem River Drive beyond the Manhattan side span are not modelled'
  },
  sources: RK_SRC
};

// Bronx Kill truss and the Randalls Island viaduct to the junction
const RB = axisOf(RFK_BK[0], RFK_BK[1]);

function rkBronxBuild(b: MeshBuilder) {
  const road = RL_LOW + 2;
  b.frame(0, 0, 0, RB.bearing, () => {
    deckSeg(b, -RB.half, RB.half, road, road, 14, 2, RK_GREY);
    b.color(RK_GREY);
    throughTruss(b, -RB.half, RB.half, () => RL_LOW, t => 18 * Math.pow(Math.sin(Math.PI * t), 0.7), 28, 10);
    b.color(CONC);
    for (const s of [-1, 1]) b.box(0, s * (RB.half + 2), -3, 32, 5, RL_LOW + 2.6);
  });
  RFK_B.forEach((ll, i) => {
    const bronx = i === 0 || i === 2; // the two pieces that run north to the Bronx shore
    rkViaduct(b, RB.anchor, [ll], (d, len) => (bronx ? road - (2.8 * d) / len : road + ((RK_VIA + 1.5 - road) * d) / len));
  });
}

const rfkBronxKill: Landmark = {
  id: 'rfk_bridge_bronx_kill',
  name: 'Triborough (Robert F. Kennedy) Bridge: Bronx Kill span',
  kind: 'bridge',
  built: RK_BUILT,
  end: 9999,
  anchor: RB.anchor,
  build: rkBronxBuild,
  facts: {
    Opened: 'Jul 11, 1936, with the rest of the Triborough Bridge (construction from 1929)',
    'Truss span': '383 ft (116.7 m) across the Bronx Kill; 1,217 ft of approaches',
    Clearance: '55 ft above mean high water',
    Model: 'truss centred on the Bronx Kill where Overture\'s carriageways cross it; truss depth and width, pier sizes and the roadway heights are estimated; the viaduct follows Overture\'s two carriageways to the junction on Randalls Island and to the Bronx shore, where it ends about 10 m above the terrain grid (the Bruckner interchange ramps take over)'
  },
  sources: RK_SRC
};

// =================================================================== HARLEM RIVER: THE HIGH BRIDGES

// ------------------------------------------------------------ High Bridge (1839–1848; steel arch 1927–1928)
// Wikipedia (High Bridge): 1,450 ft long, 138–140 ft above the river; fifteen round stone arches,
// eight of 80 ft and seven of 50 ft, on piers 20 × 40 ft at ground level, springing about 84 ft
// above mean high water; the five arches over the river were replaced in 1926–28 by one steel
// arch of 450 ft, 114 ft clear; begun Aug 13, 1839, water May 30, 1848. OSM: deck outline (way
// 393767161) 357 m long and 7.5 m wide; the steel arch's end piers (ways 1016652745, 1016656588)
// 142.2 m apart centre to centre, bearing 97.0°. Five 80 ft arches on 10 ft piers make exactly the
// 450 ft of the steel arch, so the arch piers are set 450 ft apart about the OSM midpoint; one
// 50 ft arch to the west and three 80 ft plus six 50 ft arches to the east (60 ft apart) then end
// 87 m west and 261 m east of mid-span, where the OSM outline ends (91 and 266 m).
const HB = axisOf([-73.931345, 40.842428], [-73.929669, 40.842271]); // west (Manhattan) pier → east pier of the steel arch
const HB_S = 225 * FT;
const HB_TOP = 140 * FT;
const HB_W = 21 * FT; // width of the structure (estimated; OSM outline 7.5 m)
const HB_ENDS: [number, number] = [-140, 302]; // the cited 1,450 ft, placed to meet both valley sides
const HB_STONE = '#A8A193';

/** Masonry arch along the frame between y0 and y1: semi-elliptical soffit (crown `rise` above the springing zs), solid up to zt, w wide. */
function vault(b: MeshBuilder, y0: number, y1: number, zs: number, rise: number, zt: number, w: number, n = 8) {
  const c = (y0 + y1) / 2;
  const r = (y1 - y0) / 2;
  const sof = (y: number) => zs + rise * Math.sqrt(Math.max(0, 1 - ((y - c) / r) ** 2));
  for (let i = 0; i < n; i++) {
    const a = y0 + ((y1 - y0) * i) / n;
    const d = y0 + ((y1 - y0) * (i + 1)) / n;
    for (const x of [-w / 2, w / 2]) b.quad([x, a, sof(a)], [x, d, sof(d)], [x, d, zt], [x, a, zt]);
    b.quad([-w / 2, a, sof(a)], [w / 2, a, sof(a)], [w / 2, d, sof(d)], [-w / 2, d, sof(d)]);
  }
  b.quad([-w / 2, y0, zt], [w / 2, y0, zt], [w / 2, y1, zt], [-w / 2, y1, zt]);
}

/** A run of equal stone arches from station y0: n arches `pitch` apart (clear span = pitch − 10 ft), piers at both ends optional. */
function hbArcade(b: MeshBuilder, y0: number, n: number, pitch: number, first: boolean, last: boolean) {
  const T = 10 * FT;
  const rise = (pitch - T) / 2;
  const crown = 84 * FT + 40 * FT; // 80 ft arches spring at 84 ft (cited); the smaller arches share their crown level (estimated)
  const zs = crown - rise;
  b.color(HB_STONE);
  for (let i = 0; i <= n; i++) {
    const y = y0 + i * pitch;
    if ((i === 0 && !first) || (i === n && !last)) continue;
    b.loft([rect(0, y, 40 * FT, 20 * FT), rect(0, y, HB_W, T)], [0, zs]);
    b.box(0, y, zs, HB_W, T, HB_TOP - 1 - zs);
  }
  for (let i = 0; i < n; i++) vault(b, y0 + i * pitch + T / 2, y0 + (i + 1) * pitch - T / 2, zs, rise, HB_TOP - 1, HB_W);
}

/** Walkway over the old pipe chamber, with parapets. */
function hbWalk(b: MeshBuilder, y0: number, y1: number, color: string) {
  b.color(color).box(0, (y0 + y1) / 2, HB_TOP - 1, HB_W, Math.abs(y1 - y0), 1);
  for (const x of [-HB_W / 2 + 0.2, HB_W / 2 - 0.2]) b.box(x, (y0 + y1) / 2, HB_TOP, 0.4, Math.abs(y1 - y0), 1.1);
}

const HB_E80 = HB_S + 3 * 90 * FT; // east end of the three surviving 80 ft arches
const HB_SRC = [WIKI + 'High_Bridge_(New_York_City)'];

const highBridgeStone: Landmark = {
  id: 'high_bridge',
  name: 'High Bridge (Croton Aqueduct): the surviving stone arches',
  kind: 'bridge',
  built: [1839.62, 1848.41],
  end: 9999,
  anchor: HB.anchor,
  build: b => {
    b.frame(0, 0, 0, HB.bearing, () => {
      hbArcade(b, -HB_S - 60 * FT, 1, 60 * FT, true, true);
      hbArcade(b, HB_S, 3, 90 * FT, true, true);
      hbArcade(b, HB_E80, 6, 60 * FT, false, true);
      // abutments running into the valley sides
      b.color(HB_STONE);
      b.box(0, (HB_ENDS[0] - HB_S - 60 * FT) / 2, 0, HB_W, -HB_S - 60 * FT - HB_ENDS[0], HB_TOP - 1);
      b.box(0, (HB_E80 + 360 * FT + HB_ENDS[1]) / 2, 0, HB_W, HB_ENDS[1] - HB_E80 - 360 * FT, HB_TOP - 1);
      hbWalk(b, HB_ENDS[0], -HB_S, HB_STONE);
      hbWalk(b, HB_S, HB_ENDS[1], HB_STONE);
    });
  },
  facts: {
    Built: 'Aug 13, 1839 – 1848 to carry the Croton Aqueduct over the Harlem River (John B. Jervis, chief engineer); water crossed on May 30, 1848; walkway 1864: the city’s oldest major bridge',
    Form: 'fifteen round stone arches as built, eight of 80 ft over the river and seven of 50 ft on the banks, 1,450 ft long and 138–140 ft above the river; the arches spring about 84 ft above mean high water from piers 20 × 40 ft at the ground',
    Later: 'the five arches over the river gave way to a steel arch in 1927–28; water supply ended 1958; closed in the 1970s, reopened to walkers and cyclists in 2015',
    Model: 'the ten arches that still stand: one 50 ft arch on the Manhattan side, three 80 ft and six 50 ft arches on the Bronx side; arch spacing (80 ft arches on 10 ft piers: five of them make the 450 ft of the steel arch), the crown level of the 50 ft arches, the 21 ft width and the two ends in the valley sides are estimated; the run of arches ends where the OpenStreetMap outline ends (within 5 m)'
  },
  sources: HB_SRC
};

const highBridgeRiverArches: Landmark = {
  id: 'high_bridge_river_arches',
  name: 'High Bridge: the five river arches (1848–1927)',
  kind: 'bridge',
  built: [1839.62, 1848.41],
  end: 1927.0,
  anchor: HB.anchor,
  build: b => {
    b.frame(0, 0, 0, HB.bearing, () => {
      hbArcade(b, -HB_S, 5, 90 * FT, false, false);
      hbWalk(b, -HB_S, HB_S, HB_STONE);
    });
  },
  facts: {
    Built: '1839 – 1848 with the rest of the High Bridge: five of its eight 80 ft arches stood in the Harlem River',
    Removed: 'the piers left barges less than 8 ft to spare; in 1926–28 the five arches were taken down and one steel arch put in their place',
    Model: 'five 80 ft arches on 10 ft piers between the two piers that carry the steel arch today (450 ft); pier taper and width estimated; the year the demolition began (1927) is from the rebuilding dates 1926–1928'
  },
  sources: HB_SRC
};

const highBridgeSteelArch: Landmark = {
  id: 'high_bridge_steel_arch',
  name: 'High Bridge: steel arch (1928)',
  kind: 'bridge',
  built: [1927.0, 1928.5],
  end: 9999,
  anchor: HB.anchor,
  build: b => {
    const STEEL = '#6F7F86';
    const S = HB_S - 10 * FT; // springing at the faces of the two stone piers
    const crown = 114 * FT + 1.2; // rib centre at the crown: 114 ft clear under ribs 2.4 m deep (depth estimated)
    const SPRING = 13; // springing height (estimated)
    const rib = (y: number) => crown - (crown - SPRING) * (y / S) ** 2;
    b.frame(0, 0, 0, HB.bearing, () => {
      b.color(STEEL);
      for (const x of [-2.5, 2.5]) {
        for (let i = 0; i < 16; i++) {
          const a = -S + (2 * S * i) / 16;
          const c = -S + (2 * S * (i + 1)) / 16;
          b.beam([x, a, rib(a)], [x, c, rib(c)], 0.9, 2.4);
          if (i > 0 && HB_TOP - 2.6 - rib(a) > 1.5) wire(b, [x, a, rib(a)], [x, a, HB_TOP - 2.6], 0.5);
        }
      }
      for (let i = 1; i < 16; i += 3) {
        const a = -S + (2 * S * i) / 16;
        b.beam([-2.5, a, rib(a)], [2.5, a, rib(a)], 0.5);
      }
      b.box(0, 0, HB_TOP - 2.6, HB_W - 0.6, 2 * HB_S, 1.6);
      hbWalk(b, -HB_S, HB_S, STEEL);
    });
  },
  facts: {
    Built: '1927 – 1928: one steel arch of 450 ft in place of five stone arches, to open the Harlem River to shipping',
    Clearance: '114 ft at mean high water',
    Model: 'arch piers set 450 ft apart about the OpenStreetMap piers (142.2 m centre to centre there); rib depth and spacing, springing height and the spandrel columns are estimated; the months of the work are not known'
  },
  sources: HB_SRC
};

// ------------------------------------------------------------ Washington Bridge (1886–1888)
// Wikipedia (Washington Bridge (Harlem River)): two steel arches of 510 ft, 134 ft clear at mean
// high water, 2,375 ft long, deck 80 ft wide; six ribs 13 ft deep and 14 ft apart; main piers 40 ft
// wide and 98 ft long at the skewbacks, rising nearly 100 ft above them to the deck; masonry
// approaches: semicircular arches of 60 ft on piers 13 ft thick (three on each side, with a 56 ft
// elliptical arch on the Bronx side); work began Jul 1886, opened Dec 1, 1888. OSM: two main piers
// (ways 1016657081, 1016657082) 167.2 m apart (510 ft + a 40 ft pier = 167.6 m), 29–30 m across,
// bearing 120.4°; deck outline from 161 m west to 351 m east of the middle of the river arch.
const WA = axisOf([-73.928737, 40.847155], [-73.927024, 40.846389]); // west pier → middle pier
const WA_P = [-WA.half, WA.half, WA.half + 550 * FT];
const WA_ENDS: [number, number] = [-161, 351];
const WA_ROAD = 134 * FT + 13 * FT + 1.2; // crown clearance + rib + floor (floor depth estimated)
const WA_STEEL = '#7B8A88';

const waRoadZ = (y: number) => lerpAt([[WA_P[2] + 6.1, WA_ROAD], [WA_ENDS[1], 40.5]], y); // down to the terrain at the Bronx end (estimated)

function washingtonBuild(b: MeshBuilder) {
  const SKEW = WA_ROAD - 1.2 - 100 * FT; // skewbacks nearly 100 ft below the deck
  b.frame(0, 0, 0, WA.bearing, () => {
    for (let k = 0; k < 2; k++) {
      const y0 = WA_P[k] + 20 * FT;
      const y1 = WA_P[k + 1] - 20 * FT;
      const c = (y0 + y1) / 2;
      const r = (y1 - y0) / 2;
      const top = 134 * FT + 13 * FT; // top of the ribs at the crown
      const rib = (y: number) => top - 6.5 * FT - (top - 6.5 * FT - SKEW - 2) * ((y - c) / r) ** 2;
      b.color(WA_STEEL);
      for (const x of [-35, -21, -7, 7, 21, 35]) {
        for (let i = 0; i < 14; i++) {
          const a = y0 + ((y1 - y0) * i) / 14;
          const d = y0 + ((y1 - y0) * (i + 1)) / 14;
          b.beam([x * FT, a, rib(a)], [x * FT, d, rib(d)], 0.9, 13 * FT);
          if (i > 0 && Math.abs(x) !== 21 && WA_ROAD - 1.2 - rib(a) > 3) wire(b, [x * FT, a, rib(a) + 1.9], [x * FT, a, WA_ROAD - 1.2], 0.5);
        }
      }
    }
    deckRun(b, WA_ENDS[0], WA_P[2] + 6.1, 4, () => WA_ROAD, 40 * FT, 1.2, WA_STEEL);
    deckRun(b, WA_P[2] + 6.1, WA_ENDS[1], 3, waRoadZ, 40 * FT, 1.2, GRANITE);
    // main piers: 40 × 98 ft to the skewbacks, cellular shafts above
    b.color(GRANITE);
    for (const y of WA_P) {
      b.loft([rect(0, y, 100 * FT, 42 * FT), rect(0, y, 98 * FT, 40 * FT)], [-3, SKEW + 2]);
      b.box(0, y, SKEW + 2, 84 * FT, 22 * FT, WA_ROAD - 1.2 - SKEW - 2);
    }
    // masonry approaches: 60 ft semicircular arches on 13 ft piers
    const PITCH = 73 * FT;
    const arches = (from: number, dir: number, n: number, zf: (y: number) => number) => {
      for (let i = 0; i < n; i++) {
        const a = from + dir * i * PITCH;
        const d = a + dir * PITCH;
        const zt = Math.min(zf(a), zf(d)) - 1.2;
        vault(b, Math.min(a, d) + 6.5 * FT, Math.max(a, d) - 6.5 * FT, zt - 2.2 - 30 * FT, 30 * FT, zt, 80 * FT);
        b.box(0, d, 0, 80 * FT, 13 * FT, zt);
      }
    };
    arches(WA_P[0] - 20 * FT, -1, 3, () => WA_ROAD);
    arches(WA_P[2] + 20 * FT, 1, 3, waRoadZ);
    const e0 = WA_P[2] + 20 * FT + 3 * PITCH;
    vault(b, e0 + 6.5 * FT, WA_ENDS[1] - 3, waRoadZ(WA_ENDS[1]) - 12, 7.5, waRoadZ(WA_ENDS[1]) - 1.2, 80 * FT);
    b.box(0, WA_ENDS[1] - 1.5, 0, 80 * FT, 3, waRoadZ(WA_ENDS[1]) - 1.2);
  });
}

const washingtonBridge: Landmark = {
  id: 'washington_bridge',
  name: 'Washington Bridge (Harlem River)',
  kind: 'bridge',
  built: [1886.5, 1888.92],
  end: 9999,
  anchor: WA.anchor,
  build: washingtonBuild,
  facts: {
    Construction: 'Jul 1886 – 1888; opened Dec 1, 1888 (design of Charles C. Schneider and Wilhelm Hildenbrand, changed during construction under chief engineer William R. Hutton)',
    Form: 'two steel arches of 510 ft, one over the Harlem River and one over the railroad on the Bronx bank, each of six ribs 13 ft deep and 14 ft apart; granite-faced piers and round-arched masonry approaches; 2,375 ft long, deck 80 ft wide',
    Clearance: '134 ft at mean high water',
    Model: 'main piers on the OpenStreetMap outlines (167.2 m apart; the cited arch and pier make 167.6 m), the third pier one arch further east; rib curve (parabola), skewback height from the cited 100 ft of pier above it, floor depth, the height of the Bronx end and the approach arches’ springing are estimated'
  },
  sources: [WIKI + 'Washington_Bridge_(Harlem_River)']
};

// =================================================================== UPPER EAST RIVER

// ------------------------------------------------------------ Bronx–Whitestone Bridge (1937–1939)
// Wikipedia (Bronx–Whitestone Bridge): main span 2,300 ft, side spans 735 ft, 3,770 ft between
// anchorages; towers 377 ft above mean high water; the span rises 150 ft above mean high water
// (134 ft 10 in clear); 74 ft between the cables; anchorages 180 × 110 ft; stiffening trusses
// added in the 1940s, removed 2003–05; opened Apr 29, 1939. OSM tower outlines (ways 1016686393,
// 1016686394): 698.5 m apart (cited 701.0 m), bearing 153.9°; anchorages centred 581–582 m from
// mid-span. Overture's bridge flag: 1,175 m (Bronx) to 899 m (Queens) from mid-span, straight.
const WS = axisOf([-73.831573, 40.804887], [-73.827927, 40.799214]); // Bronx tower → Queens tower
const WS_A = WS.half + 735 * FT;
const WS_TOP = 377 * FT;
const WS_CX = 37 * FT;
const WS_ENDS: [number, number] = [-1175, 899];
const WS_STEEL = '#8E9AA0';

/** Roadway: 150 ft at mid-span (cited); tower, anchorage and end heights estimated (ends 2 m above the terrain grid). */
function wsRoadZ(y: number) {
  const a = Math.abs(y);
  if (a <= WS.half) return 150 * FT - 3.2 * (a / WS.half) ** 2;
  return y < 0 ? lerpAt([[WS.half, 150 * FT - 3.2], [WS_A, 33], [-WS_ENDS[0], 6.2]], a) : lerpAt([[WS.half, 150 * FT - 3.2], [WS_A, 33], [WS_ENDS[1], 13.8]], a);
}

/** Plain two-legged suspension tower with arched portal struts under the top and under the deck. */
function portalTower(b: MeshBuilder, y: number, cx: number, top: number, zd: number, leg: [number, number, number, number], color: string, pier: [number, number, number]) {
  b.color(CONC).box(0, y, -3, pier[0], pier[1], 3 + pier[2]);
  b.color(color);
  for (const s of [-1, 1]) b.loft([rect(s * cx, y, leg[0], leg[1]), rect(s * cx, y, leg[2], leg[3])], [pier[2], top]);
  archStrut(b, y, cx - leg[2] / 2, top - 22, 6, top - 6, leg[3] * 0.8);
  archStrut(b, y, cx - leg[0] / 2, zd - 22, 5, zd - 9, leg[1] * 0.8);
}

function whitestoneBuild(b: MeshBuilder) {
  const H = WS.half;
  const DEPTH = (150 - 134.83) * FT;
  b.frame(0, 0, 0, WS.bearing, () => {
    for (const y of [-H, H]) portalTower(b, y, WS_CX, WS_TOP, wsRoadZ(y), [3.8, 5.6, 3.0, 4.2], WS_STEEL, [32, 12, 6]);
    for (const [y0, y1, n] of [[-WS_A, -H, 5], [-H, H, 20], [H, WS_A, 5]] as [number, number, number][]) deckRun(b, y0, y1, n, wsRoadZ, WS_CX, DEPTH, WS_STEEL);
    b.color(WS_STEEL);
    cables(b, {half: H, top: WS_TOP - 1.5, low: wsRoadZ(0) + 2.5, ends: [-WS_A - 8, WS_A + 8], zEnds: [34, 34], xs: [-WS_CX, WS_CX], w: 0.75, deckZ: wsRoadZ, every: 15, sideHung: true, sideSag: 5, hangW: 0.3});
    b.color(CONC);
    for (const s of [-1, 1]) b.box(0, s * 581.5, 0, 110 * FT, 180 * FT, 32.6);
    arcade(b, -WS_A, WS_ENDS[0], wsRoadZ, 13, CONC, 40, 2.4, 2.2, 20);
    arcade(b, WS_A, WS_ENDS[1], wsRoadZ, 13, CONC, 40, 2.4, 2.2, 20);
  });
}

const whitestoneBridge: Landmark = {
  id: 'bronx_whitestone_bridge',
  name: 'Bronx–Whitestone Bridge',
  kind: 'bridge',
  built: [1937.45, 1939.33],
  end: 9999,
  anchor: WS.anchor,
  build: whitestoneBuild,
  replaces: [plot(WS, -WS.half, 34, 14), plot(WS, WS.half, 34, 14), plot(WS, -581.5, 36, 58), plot(WS, 581.5, 36, 58)],
  facts: {
    Construction: 'Jun 1937 – Apr 1939; opened Apr 29, 1939, in time for the World’s Fair (Othmar Ammann, with design engineer Allston Dana)',
    'Main span': '2,300 ft (701 m); side spans 735 ft; 3,770 ft between anchorages',
    Towers: 'steel, 377 ft (115 m) above mean high water',
    Deck: 'plate girders, 74 ft between the cables; the span rises 150 ft above mean high water (134 ft 10 in clear)',
    Trusses: 'after the Tacoma Narrows collapse of 1940, stiffening trusses were added above the girders; they were removed in 2003–05',
    Model: 'shown without the stiffening trusses, as built in 1939 and as it has looked again since 2005 (the trusses of the 1940s–2003 are not modelled); towers on the OpenStreetMap outlines (698.5 m apart against the cited 701.0 m); leg sections, portal struts, saddle height and sag, the roadway heights away from mid-span and the approach viaducts’ piers are estimated'
  },
  sources: [WIKI + 'Bronx%E2%80%93Whitestone_Bridge']
};

// ------------------------------------------------------------ Throgs Neck Bridge (1957–1961)
// Wikipedia (Throgs Neck Bridge): centre span 1,800 ft, 555 ft from each tower to its anchorage,
// 2,910 ft between anchorages, 11,250 ft in all; towers 346 ft above mean high water on concrete
// islands 20 ft above it, flattened segmental arches under the struts; 142 ft clear; groundbreaking
// Oct 22, 1957, opened Jan 11, 1961. OSM tower outlines (ways 1016661640, 1016661642): 547.0 m apart
// (cited 548.6 m), bearing 179.6°; anchorages (60 × 42 m) centred 450 m from mid-span. Overture:
// straight from 1,100 m north to 820 m south of mid-span, then the Bronx viaduct curves away.
const TN_PATHS: V2[][] = [
  [[-73.793812, 40.810227], [-73.793981, 40.811170], [-73.794181, 40.811810], [-73.794348, 40.812218], [-73.794788, 40.813059], [-73.795121, 40.813556], [-73.795463, 40.813987], [-73.796143, 40.814709], [-73.796542, 40.815062], [-73.797196, 40.815570], [-73.797656, 40.815880], [-73.798396, 40.816307], [-73.799002, 40.816603], [-73.799562, 40.816838]],
  [[-73.793566, 40.792864], [-73.793381, 40.792059], [-73.793066, 40.791208]],
  [[-73.793406, 40.792865], [-73.793320, 40.792414], [-73.793201, 40.791982], [-73.792923, 40.791249]],
  [[-73.793659, 40.810228], [-73.793822, 40.811154], [-73.793945, 40.811580], [-73.794184, 40.812210], [-73.794496, 40.812830], [-73.794859, 40.813422], [-73.795450, 40.814178], [-73.796129, 40.814873], [-73.796509, 40.815204], [-73.797096, 40.815654], [-73.797881, 40.816162], [-73.798214, 40.816350], [-73.798826, 40.816659], [-73.799478, 40.816942]]
]; // Overture carriageways beyond the straight viaducts (Bronx curve, Queens end), from the bridge outward
const TN = axisOf([-73.793647, 40.802753], [-73.793599, 40.797806]); // Bronx tower → Queens tower
const TN_A = TN.half + 555 * FT;
const TN_TOP = 346 * FT;
const TN_TRUSS = 28 * FT; // stiffening truss under the roadway (depth estimated)
const TN_HW = 14;
const TN_STEEL = '#94A09C';

/** Roadway: 142 ft clear + the truss at mid-span (cited clearance); the rest estimated. */
function tnRoadZ(y: number) {
  const a = Math.abs(y);
  const mid = 142 * FT + TN_TRUSS;
  if (a <= TN.half) return mid - 2.4 * (a / TN.half) ** 2;
  return y < 0 ? lerpAt([[TN.half, mid - 2.4], [TN_A, 45], [1100, 29.1]], a) : lerpAt([[TN.half, mid - 2.4], [TN_A, 45], [820, 29.6]], a);
}

function throgsNeckBuild(b: MeshBuilder) {
  const H = TN.half;
  b.frame(0, 0, 0, TN.bearing, () => {
    for (const y of [-H, H]) {
      portalTower(b, y, 15.5, TN_TOP - 4, tnRoadZ(y) - TN_TRUSS, [4.8, 5.8, 3.8, 4.4], TN_STEEL, [62, 30, 20 * FT]);
      b.color(TN_STEEL);
      for (const s of [-1, 1]) b.box(s * 15.5, y, TN_TOP - 4, 3.2, 3.8, 4);
    }
    for (const [y0, y1, n] of [[-TN_A, -H, 4], [-H, H, 16], [H, TN_A, 4]] as [number, number, number][]) deckRun(b, y0, y1, n, tnRoadZ, TN_HW, 1.6, TN_STEEL);
    b.color(TN_STEEL);
    for (const x of [-TN_HW + 1, TN_HW - 1]) trussWall(b, x, -TN_A, TN_A, y => tnRoadZ(y) - TN_TRUSS, y => tnRoadZ(y) - 1.6, 15, 0.8, 0.4);
    cables(b, {half: H, top: TN_TOP - 5, low: tnRoadZ(0) + 2.5, ends: [-TN_A - 8, TN_A + 8], zEnds: [46, 46], xs: [-15.5, 15.5], w: 0.75, deckZ: tnRoadZ, every: 15, sideHung: true, sideSag: 4, hangW: 0.3});
    b.color(CONC);
    for (const s of [-1, 1]) b.box(0, s * 450, 0, 42, 60, 44.6);
    arcade(b, -TN_A, -1100, tnRoadZ, TN_HW, CONC, 44, 2.6, 2.4, 22);
    arcade(b, TN_A, 820, tnRoadZ, TN_HW, CONC, 44, 2.6, 2.4, 22);
  });
  // beyond the straight: the curved viaduct over the bay to the Bronx shore, and the Queens end
  for (const ll of TN_PATHS) {
    const p = pathOf(TN.anchor, ll);
    const north = lngLatToLocal(TN.anchor, ll[0])[1] > 0;
    pathDeck(b, p, 0, p.len, d => (north ? 29.1 - (22.1 * d) / p.len : 29.6 - (7.6 * d) / p.len), 13, 2.2, CONC, ROAD, 44, zTop => rkPier(b, zTop));
  }
}

const throgsNeckBridge: Landmark = {
  id: 'throgs_neck_bridge',
  name: 'Throgs Neck Bridge',
  kind: 'bridge',
  built: [1957.81, 1961.03],
  end: 9999,
  anchor: TN.anchor,
  build: throgsNeckBuild,
  replaces: [plot(TN, -TN.half, 64, 32), plot(TN, TN.half, 64, 32), plot(TN, -450, 46, 64), plot(TN, 450, 46, 64)],
  facts: {
    Construction: 'Oct 22, 1957 – Jan 1961; opened Jan 11, 1961 (Othmar Ammann)',
    'Main span': '1,800 ft (548.6 m); 555 ft from each tower to its anchorage; 2,910 ft between anchorages, 11,250 ft with the viaducts',
    Towers: 'steel, 346 ft (105.5 m) above mean high water, on concrete islands 20 ft above the water',
    Clearance: '142 ft',
    Model: 'towers on the OpenStreetMap outlines (547.0 m apart against the cited 548.6 m); anchorage plan from OpenStreetMap; the curved Bronx viaduct follows Overture’s two carriageways; truss depth (28 ft), deck width, leg sections, cable planes, saddle height and sag, and the roadway heights away from mid-span are estimated; the Queens end stops about 22 m up, where the Clearview and Cross Island ramps take over'
  },
  sources: [WIKI + 'Throgs_Neck_Bridge']
};

// =================================================================== STATEN ISLAND – NEW JERSEY

const BY_PATHS: V2[][] = [
  [[-74.137484, 40.651009], [-74.137062, 40.651614]],
  [[-74.141268, 40.644371], [-74.140240, 40.646853], [-74.139716, 40.647860], [-74.139199, 40.648644], [-74.137484, 40.651009]],
  [[-74.143314, 40.639364], [-74.145006, 40.635209], [-74.145189, 40.634576], [-74.145485, 40.633154]],
  [[-74.143193, 40.639335], [-74.144825, 40.635345], [-74.145079, 40.634495], [-74.145361, 40.633152]],
  [[-74.141145, 40.644341], [-74.140182, 40.646672], [-74.139895, 40.647283], [-74.139561, 40.647889], [-74.139043, 40.648656], [-74.137406, 40.650879]]
]; // Overture carriageways of the Bayonne and Port Richmond viaducts, from the arch abutments outward
const OB_PATHS: V2[][] = [
  [[-74.255153, 40.524315], [-74.256252, 40.524307], [-74.257474, 40.524380], [-74.266207, 40.525327], [-74.266633, 40.525384], [-74.267871, 40.525663], [-74.269231, 40.526124]],
  [[-74.255160, 40.524384], [-74.256379, 40.524383], [-74.257459, 40.524449], [-74.266188, 40.525397], [-74.267019, 40.525525], [-74.267447, 40.525621], [-74.268118, 40.525813], [-74.269184, 40.526188]]
]; // Overture carriageways of the New Jersey approach beyond the straight, from the bridge outward
const GO_PATHS: V2[][] = [
  [[-74.205221, 40.640491], [-74.205681, 40.640860], [-74.206245, 40.641267], [-74.207153, 40.641847]],
  [[-74.193132, 40.633406], [-74.190258, 40.631881], [-74.189063, 40.631281], [-74.187840, 40.630710], [-74.185819, 40.629832]],
  [[-74.201289, 40.637751], [-74.201979, 40.638182], [-74.202815, 40.638784], [-74.203392, 40.639261], [-74.205320, 40.640954], [-74.205798, 40.641334], [-74.206512, 40.641836]],
  [[-74.201497, 40.637522], [-74.202402, 40.638112], [-74.203016, 40.638572], [-74.205221, 40.640491]],
  [[-74.193345, 40.633172], [-74.191002, 40.631933], [-74.189806, 40.631342], [-74.188820, 40.630885], [-74.185942, 40.629637]]
]; // Overture carriageways of the approach viaducts, from the cable-stayed spans outward

/** Both carriageways of an approach viaduct on paths from the bridge outward: height from z0 down to z1 at the far end. */
function approachPaths(b: MeshBuilder, anchor: V2, lines: V2[][], z0: number, z1: (i: number) => number, width: number, color: string, every = 42, zStart?: (i: number) => number) {
  lines.forEach((ll, i) => {
    const p = pathOf(anchor, ll);
    const a = zStart ? zStart(i) : z0;
    pathDeck(b, p, 0, p.len, d => a + ((z1(i) - a) * d) / p.len, width, 2.2, color, ROAD, every, zTop => rkPier(b, zTop));
  });
}

// ------------------------------------------------------------ Bayonne Bridge (1928–1931; roadway raised 2013–2019)
// Wikipedia (Bayonne Bridge): steel through arch, main span 1,675 ft, 85 ft wide; the lower chord
// rises 266 ft above the Kill Van Kull, the upper 325 ft; 151 ft clear as built, 215 ft since the
// roadway was raised (reached Jun 8, 2017; finished May 2019); Port Richmond viaduct 2,010 ft,
// Bayonne viaduct 3,010 ft; opened Nov 15, 1931. OSM abutment outlines (ways 1013440560,
// 1016686886): centroids 533.1 m apart, about 40 × 33 m, bearing 197.5°: the arch bearings are set
// the cited 1,675 ft (510.5 m) apart about their midpoint. Viaducts: Overture's two carriageways.
const BY = axisOf([-74.141287, 40.644153], [-74.143182, 40.639554]); // Bayonne abutment → Staten Island abutment
const BY_S = (1675 * FT) / 2;
const BY_STEEL = '#8D9499';

function bayonneBuild(b: MeshBuilder, clear: number) {
  const road = clear + 2.6; // floor depth estimated
  const HINGE = 9; // bearing height (estimated)
  const zl = (y: number) => 266 * FT - (266 * FT - HINGE) * (y / BY_S) ** 2;
  const zu = (y: number) => zl(y) - 0.7 + 59 * FT + 8.5 * FT * (y / BY_S) ** 2; // 59 ft between the cited chord heights at the crown; 67.5 ft at the ends (estimated)
  const X = 37 * FT; // arch trusses 74 ft apart (estimated)
  const N = 20;
  b.frame(0, 0, 0, BY.bearing, () => {
    b.color(BY_STEEL);
    for (const x of [-X, X]) {
      for (let i = 0; i < N; i++) {
        const a = -BY_S + (2 * BY_S * i) / N;
        const c = -BY_S + (2 * BY_S * (i + 1)) / N;
        b.beam([x, a, zl(a)], [x, c, zl(c)], 2.2);
        b.beam([x, a, zu(a)], [x, c, zu(c)], 1.4);
        wire(b, [x, a, zl(a)], [x, a, zu(a)], 0.6);
        if (i < N / 2) wire(b, [x, a, zu(a)], [x, c, zl(c)], 0.55);
        else wire(b, [x, a, zl(a)], [x, c, zu(c)], 0.55);
        if (i > 0 && Math.abs(zl(a) - road + 2.6) > 2.5) wire(b, [x, a, Math.min(zl(a), road - 2.6)], [x, a, Math.max(zl(a), road - 2.6)], 0.45);
      }
      wire(b, [x, BY_S, zl(BY_S)], [x, BY_S, zu(BY_S)], 0.6);
    }
    for (let i = 0; i <= N; i++) {
      const a = -BY_S + (2 * BY_S * i) / N;
      if (zu(a) > road + 8) b.beam([-X, a, zu(a)], [X, a, zu(a)], 0.6);
      if (zl(a) > road + 8) b.beam([-X, a, zl(a)], [X, a, zl(a)], 0.6);
    }
    deckRun(b, -290, 290, 8, () => road, 42.5 * FT, 2.6, BY_STEEL);
    b.color(CONC);
    for (const s of [-1, 1]) b.box(0, s * 270, -3, 40, 30, 3 + Math.min(road - 2.6, 44));
    if (road > 50) for (const s of [-1, 1]) for (const x of [-9, 9]) b.box(x, s * 272, 44, 4, 6, road - 2.6 - 44);
  });
  approachPaths(b, BY.anchor, BY_PATHS, road, i => (lngLatToLocal(BY.anchor, BY_PATHS[i][0])[1] > 0 ? 8.5 : 17), 12.5, CONC, 42, i => (i === 0 ? 8.5 : road));
}

const BY_FACTS = {
  Construction: '1928 – Nov 1931; opened Nov 15, 1931 (Othmar Ammann; Cass Gilbert, architect)',
  Arch: 'steel through arch of 1,675 ft (510.5 m), the longest steel arch in the world when built; lower chord 266 ft and upper chord 325 ft above the Kill Van Kull',
  Viaducts: 'Port Richmond viaduct 2,010 ft, Bayonne viaduct 3,010 ft'
};
const BY_SRC = [WIKI + 'Bayonne_Bridge'];
const BY_MODEL = 'arch bearings set 1,675 ft apart about the midpoint of the OpenStreetMap abutments (533.1 m between their centroids); truss spacing, bearing height, the depth of the arch at its ends, the floor depth and the month the work began in 1928 are estimated; the viaducts follow Overture’s two carriageways with estimated grades; the Bayonne (New Jersey) half lies outside the map';

const bayonneBridge1931: Landmark = {
  id: 'bayonne_bridge_1931',
  name: 'Bayonne Bridge (roadway as built, 1931–2017)',
  kind: 'bridge',
  built: [1928.7, 1931.87],
  end: 2017.44,
  anchor: BY.anchor,
  build: b => bayonneBuild(b, 151 * FT),
  facts: {...BY_FACTS, Deck: '85 ft wide, hung 151 ft above the water', Model: BY_MODEL},
  sources: BY_SRC
};

const bayonneBridge: Landmark = {
  id: 'bayonne_bridge',
  name: 'Bayonne Bridge',
  kind: 'bridge',
  built: [2017.4, 2017.44],
  end: 9999,
  anchor: BY.anchor,
  build: b => bayonneBuild(b, 215 * FT),
  facts: {...BY_FACTS, Deck: 'raised 64 ft inside the same arch for larger container ships: 215 ft clear since Jun 8, 2017; new roadways finished May 24, 2019', Model: BY_MODEL + '; the new deck’s 2013–2017 construction above the old one is not shown'},
  sources: BY_SRC
};

// ------------------------------------------------------------ Outerbridge Crossing (1928) and the first Goethals Bridge (1928–2017)
// Wikipedia (Outerbridge Crossing): steel cantilever, main span 750 ft, 143 ft clear, 62 ft wide,
// 8,800 ft long, opened Jun 29, 1928. Wikipedia (Goethals Bridge (1928–2017)): cantilever, main span
// 672 ft, 135 ft clear (infobox 140), 62 ft wide, 7,109 ft long, opened Jun 29, 1928, closed Jun 9,
// 2017, demolished from Jan 2018. OSM (Outerbridge): main piers (ways 1016687789, 1016687791)
// 228.3 m apart (cited 228.6 m), bearing 85.9°; anchor piers 114 m beyond them; next piers at 319 m.
type Canti = {half: number; arm: number; susp: number; peak: number; low: number; w: number; chord: (y: number) => number; color: string};

/** Cantilever through truss: anchor arms, towers over the main piers, cantilever arms and a suspended span. */
function cantilever(b: MeshBuilder, o: Canti) {
  const nodes: [number, number][] = [];
  const seg = (y0: number, y1: number, n: number, f: (t: number) => number, last = false) => {
    for (let i = 0; i < n + (last ? 1 : 0); i++) nodes.push([y0 + ((y1 - y0) * i) / n, f(i / n)]);
  };
  const hip = o.low + 2;
  const up = (a: number, c: number) => (t: number) => a + (c - a) * Math.pow(t, 1.5);
  const down = (a: number, c: number) => (t: number) => c + (a - c) * Math.pow(1 - t, 1.5);
  seg(-o.half - o.arm, -o.half, 6, up(o.low, o.peak));
  seg(-o.half, -o.susp / 2, 4, down(o.peak, hip));
  seg(-o.susp / 2, o.susp / 2, 6, t => hip + 4 * (1 - (2 * t - 1) ** 2));
  seg(o.susp / 2, o.half, 4, up(hip, o.peak));
  seg(o.half, o.half + o.arm, 6, down(o.peak, o.low), true);
  const zb = o.chord;
  b.color(o.color);
  for (const x of [-o.w / 2, o.w / 2]) {
    for (let i = 0; i < nodes.length; i++) {
      const [s, h] = nodes[i];
      wire(b, [x, s, zb(s)], [x, s, zb(s) + h], Math.abs(Math.abs(s) - o.half) < 0.01 ? 1.4 : 0.55);
      if (i === nodes.length - 1) break;
      const [s1, h1] = nodes[i + 1];
      b.beam([x, s, zb(s)], [x, s1, zb(s1)], 1.0);
      b.beam([x, s, zb(s) + h], [x, s1, zb(s1) + h1], 1.0);
      if (h1 > h) wire(b, [x, s, zb(s)], [x, s1, zb(s1) + h1], 0.5);
      else wire(b, [x, s, zb(s) + h], [x, s1, zb(s1)], 0.5);
    }
  }
  for (let i = 0; i < nodes.length; i += 2) {
    const [s, h] = nodes[i];
    b.beam([-o.w / 2, s, zb(s) + h], [o.w / 2, s, zb(s) + h], 0.5);
  }
  b.color(CONC);
  for (const s of [-o.half - o.arm, -o.half, o.half, o.half + o.arm]) b.loft([rect(0, s, o.w + 10, 9), rect(0, s, o.w + 4, 5)], [-3, zb(s) - 0.5]);
}

const OB = axisOf([-74.24943, 40.524669], [-74.246739, 40.524818]); // New Jersey-side main pier → Staten Island-side main pier
const OB_STEEL = '#7F8B8E';
/** Roadway: 143 ft clear + floor at mid-span (cited clearance); grades and end heights estimated (ends on the terrain grid). */
const obRoadZ = (y: number) => (Math.abs(y) <= 228.2 ? 143 * FT + 2.2 - 1.4 * (y / 228.2) ** 2 : y > 0 ? lerpAt([[228.2, 44.4], [924, 13]], y) : lerpAt([[-600, 39.8], [-228.2, 44.4]], y));

function outerbridgeBuild(b: MeshBuilder) {
  b.frame(0, 0, 0, OB.bearing, () => {
    cantilever(b, {half: OB.half, arm: 114.1, susp: 114, peak: 36, low: 12, w: 14, chord: y => obRoadZ(y) - 2.2, color: OB_STEEL});
    deckRun(b, -228.2, 228.2, 10, obRoadZ, 31 * FT, 2.2, OB_STEEL);
    arcade(b, 228.2, 924, obRoadZ, 31 * FT, CONC, 40, 2.4, 2.2, 14);
    arcade(b, -228.2, -600, obRoadZ, 31 * FT, CONC, 40, 2.4, 2.2, 14);
  });
  approachPaths(b, OB.anchor, OB_PATHS, 39.8, () => 25.5, 9.5, CONC);
}

const outerbridgeCrossing: Landmark = {
  id: 'outerbridge_crossing',
  name: 'Outerbridge Crossing',
  kind: 'bridge',
  built: [1925.5, 1928.49],
  end: 9999,
  anchor: OB.anchor,
  build: outerbridgeBuild,
  facts: {
    Opened: 'Jun 29, 1928, the same day as the Goethals Bridge: the Port Authority’s first crossings; built 1925–1928 (John Alexander Low Waddell, designer); named for Eugenius Outerbridge, the authority’s first chairman',
    Form: 'steel cantilever truss, main span 750 ft (228.6 m), 143 ft clear, 62 ft wide, 8,800 ft with the viaducts',
    Model: 'main piers on the OpenStreetMap outlines (228.3 m apart against the cited 228.6 m), anchor piers 114 m beyond them (OpenStreetMap); truss heights, suspended-span length, truss spacing, the roadway grades and the month the work began in 1925 are estimated; the New Jersey approach follows Overture’s two carriageways; the New Jersey half lies outside the map'
  },
  sources: [WIKI + 'Outerbridge_Crossing']
};

// ------------------------------------------------------------ Goethals Bridge: cantilever (1928–2017), cable-stayed twin spans (2017 / 2018)
// Wikipedia (Goethals Bridge): two cable-stayed bridges, main span 900 ft, towers not above 272 ft
// and slanting outward (flight paths), 135 ft clear; ground broken May 2014; eastbound opened
// Jun 10, 2017, westbound May 21, 2018. OSM tower footings (ways 1016689046/47 west, 1016689044/45
// east): 273.6 m apart (cited 274.3 m), bearing 124.9°, the two bridges' axes 15–16 m either side
// of the common centre line. The 1928 bridge stood just north of the westbound span.
const GO = axisOf([-74.198648, 40.636167], [-74.195991, 40.634751]); // west (New Jersey) towers → east (Staten Island) towers
const GO_TOP = 272 * FT;
const GO_ROAD = 135 * FT + 3;

function goethalsNewBuild(b: MeshBuilder, cx: number, paths: V2[][], flat: number) {
  const zf = (y: number) => GO_ROAD - 2 * (y / 420) ** 2;
  b.frame(0, 0, 0, GO.bearing, () => {
    deckRun(b, -420, 420, 12, zf, 9.5, 3, CONC, ROAD, cx);
    for (const y of [-GO.half, GO.half]) {
      b.color(CONC).box(cx, y, -3, 30, 9, 6);
      for (const s of [-1, 1]) {
        // legs lean outward; stays fan to the deck edge on both sides of the tower
        const foot: V3 = [cx + s * 10.5, y, 3];
        const head: V3 = [cx + s * 15.5, y, GO_TOP];
        b.color('#C9CCCB').beam(foot, head, 3.2, 4.2);
        b.color('#D8DADA');
        for (let k = 1; k <= 12; k++) {
          const t = 0.62 + (0.36 * k) / 12;
          const from: V3 = [foot[0] + (head[0] - foot[0]) * t, y, foot[2] + (head[2] - foot[2]) * t];
          for (const dir of [-1, 1]) {
            const yy = y + dir * k * 10.6;
            wire(b, from, [cx + s * 9.3, yy, zf(yy)], 0.3);
          }
        }
      }
    }
  });
  approachPaths(b, GO.anchor, paths, zf(420), i => (i === 2 ? flat + 1.8 : flat), 19, CONC, 45, i => (i === 2 ? flat : zf(420)));
}

const GO_SRC = [WIKI + 'Goethals_Bridge'];
const GO_MODEL = 'towers on the OpenStreetMap footings (273.6 m apart against the cited 274.3 m); tower shape (legs leaning outward to the cited 272 ft), stay pattern, back-span length, deck width (62 ft) and depth, and the roadway heights are estimated; the approach viaducts follow Overture’s carriageways down to the terrain grid; the New Jersey half lies outside the map';

const goethalsEastbound: Landmark = {
  id: 'goethals_bridge_eastbound',
  name: 'Goethals Bridge (eastbound span, 2017)',
  kind: 'bridge',
  built: [2014.4, 2017.44],
  end: 9999,
  anchor: GO.anchor,
  build: b => goethalsNewBuild(b, 15.6, [GO_PATHS[3], GO_PATHS[4], GO_PATHS[0]], 5.2),
  facts: {
    Construction: 'May 2014 – 2017; opened Jun 10, 2017 (it carried both directions until the westbound span opened)',
    Form: 'cable-stayed, main span 900 ft (274 m); towers no higher than 272 ft and leaning outward, because of the flight paths of Newark Airport; 135 ft clear',
    Model: GO_MODEL
  },
  sources: GO_SRC
};

const goethalsWestbound: Landmark = {
  id: 'goethals_bridge_westbound',
  name: 'Goethals Bridge (westbound span, 2018)',
  kind: 'bridge',
  built: [2016.0, 2018.39],
  end: 9999,
  anchor: GO.anchor,
  build: b => goethalsNewBuild(b, -16, [GO_PATHS[1], GO_PATHS[2]], 4.5),
  facts: {
    Construction: 'opened May 21, 2018, completing the replacement of the 1928 bridge',
    Form: 'cable-stayed twin of the eastbound span: main span 900 ft, towers no higher than 272 ft, 135 ft clear; with a path for walkers and cyclists',
    Model: GO_MODEL + '; the start of its construction (2016) is estimated'
  },
  sources: GO_SRC
};

const goethalsBridge1928: Landmark = {
  id: 'goethals_bridge_1928',
  name: 'Goethals Bridge (1928 cantilever)',
  kind: 'bridge',
  built: [1925.5, 1928.49],
  end: 2018.0,
  anchor: GO.anchor,
  build: b => {
    const road = (y: number) => 135 * FT + 2.2 - 1.2 * (y / 180) ** 2;
    const zf = (y: number) => (Math.abs(y) <= 180 ? road(y) : lerpAt([[180, road(180)], [1080, 5]], Math.abs(y)));
    b.frame(-45 * GO.uy, 45 * GO.ux, 0, GO.bearing, () => {
      cantilever(b, {half: (672 * FT) / 2, arm: 77.6, susp: 100, peak: 32, low: 11, w: 13, chord: y => road(y) - 2.2, color: OB_STEEL});
      deckRun(b, -180, 180, 8, road, 31 * FT, 2.2, OB_STEEL);
      arcade(b, 180, 1080, zf, 31 * FT, CONC, 40, 2.4, 2.2, 13);
      arcade(b, -180, -1080, zf, 31 * FT, CONC, 40, 2.4, 2.2, 13);
    });
  },
  facts: {
    Opened: 'Jun 29, 1928, with the Outerbridge Crossing (John Alexander Low Waddell, designer); named for George W. Goethals, builder of the Panama Canal and the Port Authority’s first consulting engineer',
    Form: 'steel cantilever truss, main span 672 ft, 135 ft clear, 62 ft wide (four 10 ft lanes), 7,109 ft with the viaducts',
    Removed: 'closed Jun 9, 2017, when the first new span opened; taken down from Jan 2018',
    Model: 'placed parallel to the new spans, 45 m north of their common centre line: its exact line was not found in the sources (estimated); anchor-arm length, truss heights and spacing, the straight viaducts (the cited 7,109 ft centred on the main span) and the construction start (taken as the Outerbridge Crossing’s, 1925) are estimated; one end date for all spans'
  },
  sources: [WIKI + 'Goethals_Bridge_(1928%E2%80%932017)', WIKI + 'Goethals_Bridge']
};

// =================================================================== HARLEM RIVER: THE MOVABLE BRIDGES AND THE HENRY HUDSON

// ------------------------------------------------------------ Macombs Dam Bridge (1890–1895)
// Wikipedia (Macombs Dam Bridge): swing span variously cited as 408 or 415 ft, 25 ft clear closed,
// 2,540 ft long with a camelback truss over the railroad on the Bronx bank; 155th Street viaduct
// 1,600 ft, begun Dec 1890; the bridge opened May 1, 1895. OSM: the four rest-pier ends of the
// swing span (ways 1016651857–60) give its axis: 126.6 m long (415 ft = 126.5 m), bearing 84.3°,
// with the round pivot pier (way 1016651861, 14.5 m across) at its middle; deck outline 21 m wide.
const MD_PATHS: V2[][] = [
  [[-73.934587, 40.828048], [-73.934978, 40.828187], [-73.939461, 40.830093]],
  [[-73.931454, 40.828289], [-73.931161, 40.828327]],
  [[-73.931161, 40.828327], [-73.930511, 40.828454], [-73.929986, 40.828609], [-73.929433, 40.828825], [-73.929040, 40.829025]]
]; // 155th Street viaduct (Overture West 155th Street, bridge flag) and the Bronx end beyond Jerome Avenue, from the bridge outward
const MD = axisOf([-73.934587, 40.828048], [-73.933092, 40.828162]); // Manhattan end → Bronx end of the swing span
const MD_STEEL = '#A69E8B';

function macombsBuild(b: MeshBuilder) {
  const LOW = 25 * FT;
  const road = LOW + 1.6;
  const H = MD.half;
  b.frame(0, 0, 0, MD.bearing, () => {
    deckSeg(b, -H, 202, road, road - 4, 10, 1.6, MD_STEEL);
    b.color(MD_STEEL);
    throughTruss(b, -H, H, () => LOW, t => (t < 1e-6 || t > 1 - 1e-6 ? 0 : 7 + 9 * (1 - Math.abs(2 * t - 1))), 13, 10);
    for (const x of [-6.5, 6.5]) b.pyramid(rect(x, 0, 1.6, 1.6), LOW + 16, [x, 0, LOW + 21]);
    throughTruss(b, 66, 133, y => LOW - (4 * (y - -H)) / (202 + H), t => 11 * Math.pow(Math.sin(Math.PI * t), 0.7), 13, 6);
    b.color(GRANITE).cylinder(0, 0, 7.2, -3, LOW - 0.5, 14);
    for (const y of [-H - 1.5, H + 1.5, 133]) b.box(0, y, -3, 22, 3, 3 + LOW - 1.2);
    for (const y of [150, 168, 186]) b.color(MD_STEEL).box(0, y, 0, 14, 1.2, LOW - 3);
  });
  // 155th Street viaduct up to Coogan's Bluff, and the Bronx end to Jerome Avenue
  MD_PATHS.forEach((ll, i) => {
    const p = pathOf(MD.anchor, ll);
    pathDeck(b, p, 0, p.len, d => (i === 0 ? road + ((20.6 - road) * d) / p.len : 5.2 + (1.3 * i * d) / p.len / 2), i === 0 ? 18 : 14, 1.6, MD_STEEL, ROAD, 30, zTop => rkPier(b, zTop));
  });
}

const macombsDamBridge: Landmark = {
  id: 'macombs_dam_bridge',
  name: 'Macombs Dam Bridge',
  kind: 'bridge',
  built: [1890.95, 1895.33],
  end: 9999,
  anchor: MD.anchor,
  build: macombsBuild,
  facts: {
    Construction: 'viaduct from Dec 1890, river span from May 1892; opened May 1, 1895 (Alfred Pancoast Boller): the third-oldest major bridge in the city',
    Form: 'swing span of 408–415 ft on a round masonry pivot pier, a camelback truss over the railroad on the Bronx bank, and the 1,600 ft 155th Street viaduct up to Coogan’s Bluff; 2,540 ft long; 25 ft clear when closed',
    Model: 'swing span on the OpenStreetMap rest piers (126.6 m) and pivot pier; truss depths and width, the camelback span’s length (220 ft), the pier sizes, the roadway heights and the viaduct’s height at the bluff (the terrain grid there reads 20 m) are estimated; the viaduct and the Bronx end follow Overture’s roadway; the four stone shelter houses are not modelled'
  },
  sources: [WIKI + 'Macombs_Dam_Bridge']
};

// ------------------------------------------------------------ University Heights Bridge (span of 1895, here since 1908)
// Wikipedia (University Heights Bridge): swing span 264–270 ft, 50 ft wide, two 100 ft approach
// spans; opened Jan 1, 1895 as the Harlem Ship Canal Bridge at Broadway, floated here in 1906,
// opened Jan 8, 1908. OSM: the movable span of the roadway runs from 42.6 m west to 38.5 m east
// of the midpoint of the rest piers (ways 1016657433, 1016657432): 81.1 m; pivot pier (way
// 1016657434) 12.6 m across; bearing 119.0°. Overture's bridge flag: 98.6 m west to 70.2 m east.
const UH = axisOf([-73.915305, 40.862939], [-73.914385, 40.862551]); // Manhattan-side rest pier → Bronx-side rest pier
const UH_STEEL = '#7D8B84';

function universityBuild(b: MeshBuilder) {
  const LOW = 25 * FT; // closed clearance (as at the other Harlem River swing bridges; estimated)
  const road = LOW + 1.5;
  const zf = (y: number) => lerpAt([[-98.6, 7], [-42.6, road], [38.5, road], [70.2, 7]], y);
  b.frame(0, 0, 0, UH.bearing, () => {
    deckRun(b, -98.6, 70.2, 6, zf, 25 * FT, 1.5, UH_STEEL);
    b.color(UH_STEEL);
    throughTruss(b, -42.6, 38.5, () => LOW, t => (t < 1e-6 || t > 1 - 1e-6 ? 0 : 6.5 + 7 * (1 - Math.abs(2 * t - 1))), 10.5, 8);
    for (const [y0, y1] of [[-73.1, -42.6], [38.5, 69]]) throughTruss(b, y0, y1, y => zf(y) - 1.5, flatTop(6.8), 10.5, 4, 0.7, 0.35);
    b.color(GRANITE).cylinder(0, -2.05, 6.3, -3, LOW - 0.5, 14);
    for (const y of [-73.1, -44.3, 40.2, 69]) b.box(0, y, -3, 21, 3.2, 3 + zf(y) - 1.6);
  });
}

const universityHeightsBridge: Landmark = {
  id: 'university_heights_bridge',
  name: 'University Heights Bridge',
  kind: 'bridge',
  built: [1906.45, 1908.02],
  end: 9999,
  anchor: UH.anchor,
  build: universityBuild,
  facts: {
    History: 'the swing span opened Jan 1, 1895 as the Harlem Ship Canal Bridge at Broadway (William H. Burr, with Alfred P. Boller); when the subway needed a stronger bridge there it was floated down the river in 1906 and reopened here on Jan 8, 1908',
    Form: 'swing span of 264–270 ft, 50 ft wide, with two 100 ft approach spans',
    Model: 'swing span as OpenStreetMap maps it (81.1 m) between the rest piers; truss depths and spacing, the closed clearance (25 ft), pier sizes and end heights are estimated; the span’s first site at Broadway (1895–1905) is not modelled'
  },
  sources: [WIKI + 'University_Heights_Bridge']
};

// ------------------------------------------------------------ Broadway Bridge (1957–1960 lift span)
// Wikipedia (Broadway Bridge (Manhattan)): double-deck vertical lift, lift span 304 ft, 25 ft clear
// closed and 136 ft raised, towers 160 ft above mean water, 558 ft long; six lanes below, three
// subway tracks above; subway Dec 26, 1960, roadway Jan 1961. OSM tower piers (ways 1016658464,
// 1016658466): 94.3 m apart, 32 × 5.5 m, bearing 44.6°; deck outline 175 m long. The towers are set
// the cited 304 ft apart about the OSM midpoint.
const BW = axisOf([-73.911493, 40.873327], [-73.910708, 40.873935]); // Inwood tower → Marble Hill tower
const BW_T = (304 * FT) / 2;
const BW_STEEL = '#78867F';

function broadwayBuild(b: MeshBuilder) {
  const LOW = 25 * FT;
  const DEPTH = 10; // truss depth between the roadway and the tracks (estimated)
  const TOP = 160 * FT;
  const road = (y: number) => lerpAt([[-88, 9.2], [-BW_T, LOW + 1.5], [BW_T, LOW + 1.5], [86, 7.5]], y);
  b.frame(0, 0, 0, BW.bearing, () => {
    deckRun(b, -88, 86, 6, road, 12.5, 1.5, BW_STEEL);
    deckRun(b, -88, 86, 6, y => road(y) + DEPTH - 1.2, 7.6, 1.0, BW_STEEL, '#4A4744');
    b.color(BW_STEEL);
    throughTruss(b, -BW_T + 2.75, BW_T - 2.75, () => LOW, flatTop(DEPTH), 17, 8);
    throughTruss(b, -88, -BW_T - 2.75, y => road(y) - 1.5, flatTop(DEPTH), 17, 4, 0.8, 0.4);
    throughTruss(b, BW_T + 2.75, 86, y => road(y) - 1.5, flatTop(DEPTH), 17, 4, 0.8, 0.4);
    for (const s of [-1, 1]) {
      const y = s * BW_T;
      b.color(CONC).box(0, y, -3, 32, 5.5, 3 + LOW - 0.6);
      b.color(BW_STEEL);
      const zs: number[] = [];
      for (let i = 0; i <= 5; i++) zs.push(LOW + ((TOP - 3 - LOW) * i) / 5);
      for (const sx of [-1, 1]) latticeLeg(b, () => rect(sx * 11.3, y, 3, 5.5), zs, 0.9, 0.35);
      for (const z of zs.slice(3)) b.beam([-9.8, y, z], [9.8, y, z], 0.7);
      wire(b, [-9.8, y, zs[3]], [9.8, y, zs[4]], 0.4);
      wire(b, [9.8, y, zs[3]], [-9.8, y, zs[4]], 0.4);
      b.box(0, y, TOP - 3, 26, 6.5, 3);
      b.color('#8F8A80').box(0, y + s * 4.4, TOP - 14, 20, 2.2, 8);
    }
  });
}

const broadwayBridge: Landmark = {
  id: 'broadway_bridge',
  name: 'Broadway Bridge (Harlem River Ship Canal)',
  kind: 'bridge',
  built: [1957.5, 1960.98],
  end: 9999,
  anchor: BW.anchor,
  build: broadwayBuild,
  replaces: [plot(BW, -BW_T, 34, 8), plot(BW, BW_T, 34, 8)],
  facts: {
    Built: '1957 – 1962, the third bridge here: subway trains crossed from Dec 26, 1960, road traffic from Jan 1961',
    Form: 'double-deck vertical lift: Broadway below, three tracks of the Broadway–Seventh Avenue subway above; lift span 304 ft; towers 160 ft above the water; 558 ft long',
    Clearance: '25 ft closed, 136 ft raised',
    Earlier: 'the 1895 swing span (now the University Heights Bridge) and the double-deck swing bridge of 1905–1960 are not modelled',
    Model: 'shown closed; towers set 304 ft apart about the midpoint of the OpenStreetMap piers (94.3 m apart there); truss depth and spacing, tower bracing, counterweights, flanking spans and end heights are estimated; the month the work began in 1957 is not known'
  },
  sources: [WIKI + 'Broadway_Bridge_(Manhattan)']
};

// ------------------------------------------------------------ Henry Hudson Bridge (1935–1936; upper level 1938)
// Wikipedia (Henry Hudson Bridge): steel arch, main span 841 ft, 2,208 ft long, 143 ft clear;
// opened Dec 12, 1936; upper level May 7, 1938. OSM: the arch abutments (ways 1016658825,
// 1016658823) are 258.6 m apart (841 ft = 256.3 m) and the tall end piers (ways 1016658824,
// 1016658822) 278.8 m, bearing 49.1°; deck outline 502 m long, 15.5 m wide. Overture's bridge
// flags: one roadway from 323 m south to 321 m north of mid-span, the other from 237 to 251 m.
const HH = axisOf([-73.923207, 40.877095], [-73.920703, 40.878745]); // Inwood end pier → Spuyten Duyvil end pier
const HH_S = (841 * FT) / 2;
const HH_STEEL = '#7E8B92';

function henryHudsonBuild(b: MeshBuilder) {
  const RIB = 12.5 * FT; // rib depth (estimated)
  const crown = 143 * FT + RIB / 2;
  const SPRING = 6; // springing height (estimated)
  const rib = (y: number) => crown - (crown - SPRING) * (y / HH_S) ** 2;
  const lower = (y: number) => lerpAt([[HH_S, crown + RIB / 2 + 2], [244, 43.5]], Math.abs(y));
  const upper = (y: number) => lerpAt([[HH_S, crown + RIB / 2 + 8], [322, 50]], Math.abs(y)); // deck spacing estimated
  b.frame(0, 0, 0, HH.bearing, () => {
    b.color(HH_STEEL);
    for (const x of [-7.6, 7.6]) {
      for (let i = 0; i < 18; i++) {
        const a = -HH_S + (2 * HH_S * i) / 18;
        const c = -HH_S + (2 * HH_S * (i + 1)) / 18;
        b.beam([x, a, rib(a)], [x, c, rib(c)], 1.2, RIB);
        if (i > 0 && lower(a) - 1.8 - rib(a) > 3) b.beam([x, a, rib(a) + 1.6], [x, a, lower(a) - 1.8], 0.8);
      }
    }
    for (let i = 1; i < 18; i += 2) {
      const a = -HH_S + (2 * HH_S * i) / 18;
      b.beam([-7.6, a, rib(a)], [7.6, a, rib(a)], 0.6);
    }
    deckRun(b, -237, 251, 12, lower, 7.2, 1.8, HH_STEEL);
    deckRun(b, -322, 321, 14, upper, 7.2, 1.6, HH_STEEL);
    for (let y = -322 + 14; y < 321; y += 20.3) {
      if (Math.abs(y) < 244) for (const x of [-6.4, 6.4]) wire(b, [x, y, lower(y)], [x, y, upper(y) - 1.6], 0.5);
      if (Math.abs(y) > HH_S + 4) for (const x of [-6.4, 6.4]) b.beam([x, y, 0], [x, y, (Math.abs(y) < 244 ? lower(y) : upper(y)) - 1.6], 0.9);
    }
    b.color(CONC);
    for (const s of [-1, 1]) {
      b.box(0, s * (HH_S + 3), -3, 22, 9, 3 + SPRING + 2);
      b.color(HH_STEEL);
      for (const x of [-7.6, 7.6]) b.beam([x, s * 139.4, SPRING], [x, s * 139.4, lower(139.4) - 1.8], 1.8);
      b.color(CONC);
    }
  });
}

const henryHudsonBridge: Landmark = {
  id: 'henry_hudson_bridge',
  name: 'Henry Hudson Bridge',
  kind: 'bridge',
  built: [1935.45, 1936.95],
  end: 9999,
  anchor: HH.anchor,
  build: henryHudsonBuild,
  facts: {
    Opened: 'Dec 12, 1936 (David B. Steinman); upper level added May 7, 1938',
    Form: 'fixed steel plate-girder arch of 841 ft (256 m) over Spuyten Duyvil, the longest of its kind when built; 2,208 ft long with its viaducts; 143 ft clear',
    Model: 'shown with both levels (the upper one dates from 1938); arch springings set 841 ft apart about the OpenStreetMap abutments (258.6 m apart there); rib depth and spacing, springing height, the spacing of the two decks, the spandrel columns and viaduct bents, and the roadway heights toward the ends are estimated; the start of construction (mid-1935) is estimated'
  },
  sources: [WIKI + 'Henry_Hudson_Bridge']
};

// =================================================================== NEWTOWN CREEK, ROCKAWAY INLET, EAST RIVER EAST CHANNEL

// ------------------------------------------------------------ Kosciuszko Bridge: 1939 truss, cable-stayed spans of 2017 and 2019
// Wikipedia (Kosciuszko Bridge): cable-stayed, main span 624 ft, 90 ft clear; each deck 1,001 ft
// long on 56 stays from two pylons 287 ft high; eastbound opened Apr 27, 2017, westbound Aug 29,
// 2019. The 1939 truss bridge: main span 300 ft, 125 ft clear, 6,021 ft long, opened Aug 23, 1939,
// on the site of the westbound span; its main span was lowered in Jul 2017, the approaches
// demolished Oct 1, 2017. Lines: Overture's bridge-flagged Brooklyn-Queens Expressway carriageways;
// Newtown Creek on them from Overture's water layer (eastbound 454–537 m, westbound 356–442 m from
// the Brooklyn end). OpenStreetMap has no pylon outlines here, but it splits the eastbound roadway into a
// way of 307 m (the 1,001 ft deck) from 326 to 633 m along the line: with the cited 624 ft main span
// and 377 ft back span the pylons stand 441 m along it, on the Brooklyn bank 13 m from the water
// (the other way round they would stand in the creek). The westbound pylons are placed alike.
const KZ_EB: V2[] = [[-73.933619, 40.724953], [-73.932740, 40.725178], [-73.932092, 40.725398], [-73.931479, 40.725674], [-73.930915, 40.725994], [-73.930600, 40.726211], [-73.930213, 40.726515], [-73.927917, 40.728502], [-73.927250, 40.729180], [-73.926966, 40.729509], [-73.926675, 40.729889], [-73.924947, 40.732491]]; // Overture e2ac78e7 (Brooklyn-Queens Expressway, bridge flag): eastbound bridge, Brooklyn → Queens
const KZ_WB: V2[] = [[-73.932755, 40.725384], [-73.932373, 40.725505], [-73.932091, 40.725615], [-73.931706, 40.725786], [-73.931349, 40.725974], [-73.930790, 40.726328], [-73.930503, 40.726540], [-73.930178, 40.726814], [-73.927844, 40.728865], [-73.927487, 40.729212], [-73.927242, 40.729488], [-73.926873, 40.729971], [-73.926035, 40.731226]]; // Overture 8f4b1e93: westbound bridge, drawn Brooklyn → Queens
const KZ_EB_MID: V2 = [-73.928668, 40.727852]; // middle of the main span: 442 + 95.1 m along the line
const KZ_OLD_MID: V2 = [-73.929188, 40.727684]; // middle of Newtown Creek on the westbound line (399 m along it): mid-span of the 1939 bridge
const KZ_WB_MID: V2 = [-73.928877, 40.727958]; // middle of the main span: 344 + 95.1 m along the line

function kzBuild(b: MeshBuilder, anchor: V2, line: V2[], dT: number, hw: number, z0: number, z1: number) {
  const p = pathOf(anchor, line);
  const MAIN = 624 * FT;
  const BACK = 377 * FT;
  const TOP = 287 * FT;
  const road = 90 * FT + 2.6; // girder depth estimated
  onPath(b, p, dT, dT + MAIN, L => {
    deckSeg(b, -BACK, L, road, road, hw, 2.6, CONC);
    for (const s of [-1, 1]) {
      const x = s * (hw + 1.6);
      b.color(CONC).loft([rect(x, 0, 4.2, 6.5), rect(x, 0, 3, 4.2)], [0, TOP]);
      b.color('#D8DADA');
      for (let k = 1; k <= 14; k++) {
        const zt = TOP - 3 - (14 - k) * 2.6;
        wire(b, [x, 0, zt], [s * (hw - 0.4), (k * L) / 14.6, road], 0.3);
        wire(b, [x, 0, zt], [s * (hw - 0.4), (-k * BACK) / 14.6, road], 0.3);
      }
    }
    b.color(CONC).box(0, 0, 0, 2 * hw + 7, 5, road - 8);
  });
  pathDeck(b, p, 0, dT - BACK, d => z0 + ((road - z0) * d) / (dT - BACK), 2 * hw, 2.6, CONC, ROAD, 45, zTop => rkPier(b, zTop));
  pathDeck(b, p, dT + MAIN, p.len, d => road + ((z1 - road) * (d - dT - MAIN)) / (p.len - dT - MAIN), 2 * hw, 2.6, CONC, ROAD, 45, zTop => rkPier(b, zTop));
}

const KZ_SRC = [WIKI + 'Kosciuszko_Bridge'];
const KZ_MODEL = 'follows Overture’s carriageway; pylons on the Brooklyn bank of Newtown Creek, where the 1,001 ft deck mapped in OpenStreetMap (eastbound roadway) puts them, with the 624 ft main span toward Queens and the 377 ft back span behind; pylon section, stay pattern (14 pairs each way), deck width and girder depth are estimated; approach viaducts down to the terrain grid at the ends of the bridge-flagged roadway';

const kosciuszkoEastbound: Landmark = {
  id: 'kosciuszko_bridge_eastbound',
  name: 'Kosciuszko Bridge (eastbound span, 2017)',
  kind: 'bridge',
  built: [2014.9, 2017.32],
  end: 9999,
  anchor: KZ_EB_MID,
  build: b => kzBuild(b, KZ_EB_MID, KZ_EB, 441, 13.5, 14.1, 18.7),
  facts: {
    Opened: 'Apr 27, 2017 (Queens-bound; it carried both directions until 2019); construction from 2014',
    Form: 'cable-stayed, the city’s first road bridge of the kind since the Brooklyn Bridge: main span 624 ft, deck 1,001 ft on 56 stays, pylons 287 ft, 90 ft clear',
    Model: KZ_MODEL + '; the month construction began in 2014 is estimated'
  },
  sources: KZ_SRC
};

const kosciuszkoWestbound: Landmark = {
  id: 'kosciuszko_bridge_westbound',
  name: 'Kosciuszko Bridge (westbound span, 2019)',
  kind: 'bridge',
  built: [2017.8, 2019.66],
  end: 9999,
  anchor: KZ_WB_MID,
  build: b => kzBuild(b, KZ_WB_MID, KZ_WB, 343, 12.5, 10.6, 14),
  facts: {
    Opened: 'Aug 29, 2019 (Brooklyn-bound, with a path for walkers and cyclists), on the site of the 1939 bridge',
    Form: 'cable-stayed twin of the eastbound span: main span 624 ft, pylons 287 ft, 90 ft clear',
    Model: KZ_MODEL + '; this span’s pylons are placed like the eastbound ones, 13 m behind the Brooklyn water edge (estimated)'
  },
  sources: KZ_SRC
};

const kosciuszkoBridge1939: Landmark = {
  id: 'kosciuszko_bridge_1939',
  name: 'Kosciuszko Bridge (1939 truss)',
  kind: 'bridge',
  built: [1938.0, 1939.64],
  end: 2017.75,
  anchor: KZ_OLD_MID,
  build: b => {
    const p = pathOf(KZ_OLD_MID, KZ_WB);
    const C = 399; // middle of Newtown Creek on the line
    const S = 150 * FT;
    const STEEL = '#6F7B80';
    const road = 125 * FT + 2;
    const zf = (d: number) => road - 0.04 * Math.max(0, Math.abs(d - C) - S); // 4 % approaches (estimated)
    onPath(b, p, C - S, C + S, L => {
      deckSeg(b, 0, L, road, road, 11, 2, STEEL);
      b.color(STEEL);
      throughTruss(b, 0, L, () => road - 2, t => 13 * Math.pow(Math.sin(Math.PI * t), 0.7), 20, 8);
      for (const y of [0, L]) for (const x of [-9, 9]) latticeLeg(b, () => rect(x, y, 3, 3), [0, 13, 26, road - 2], 0.8, 0.35);
    });
    const bent = (zTop: number) => {
      b.color(STEEL);
      for (const x of [-8, 8]) b.beam([x, 0, 0], [x * 0.8, 0, zTop], 1.0);
      wire(b, [-8, 0, 0], [6.4, 0, zTop], 0.4);
      wire(b, [8, 0, 0], [-6.4, 0, zTop], 0.4);
    };
    pathDeck(b, p, 0, C - S, zf, 22, 2.4, STEEL, ROAD, 38, bent);
    pathDeck(b, p, C + S, p.len, zf, 22, 2.4, STEEL, ROAD, 38, bent);
  },
  facts: {
    Opened: 'Aug 23, 1939 as the Meeker Avenue Bridge; renamed for Tadeusz Kościuszko in 1940; later part of the Brooklyn–Queens Expressway',
    Form: 'steel truss bridge, main span 300 ft over Newtown Creek, 125 ft clear, 6,021 ft long with its viaducts',
    Removed: 'closed Apr 2017; the main span was lowered onto barges in Jul 2017 and the approaches brought down with explosives on Oct 1, 2017',
    Model: 'drawn on the line of today’s westbound span, which stands on its site, with the main span centred on the creek; truss depth and width, the 4 % approach grade, the bents and the construction start (1938) are estimated; only the 875 m of today’s bridge-flagged roadway is modelled, so the old viaducts (6,021 ft) stop about 23–26 m up at both ends; one end date for all spans'
  },
  sources: KZ_SRC
};

// ------------------------------------------------------------ Marine Parkway–Gil Hodges Memorial Bridge (1936–1937)
// Wikipedia: vertical lift, centre span 540 ft, normally 55 ft above the water and 150 ft when
// raised; three main spans of 1,500 ft together; 4,022 ft long; main span floated in Jan 13, 1937,
// opened Jul 3, 1937. Overture's bridge-flagged carriageways: 1,236 m; OpenStreetMap's movable
// span is centred 9.5 m south of their middle. Tower outlines are not mapped.
const MP_T: V2[] = [[-73.885340, 40.574180], [-73.884489, 40.572771]]; // lift-tower centres: the cited 540 ft span centred on OpenStreetMap's movable span, on the line midway between Overture's two carriageways
const MP = axisOf(MP_T[0], MP_T[1]); // Brooklyn-side tower → Rockaway-side tower

function marineBuild(b: MeshBuilder) {
  const LOW = 55 * FT;
  const T = MP.half; // tower centres
  const SIDE = 480 * FT; // flanking truss spans: (1,500 − 540) / 2
  const TOP = 215 * FT; // tower height (not in the sources: estimated)
  const STEEL = '#8C9690';
  const road = (y: number) => lerpAt([[-627.5, 6], [-T - SIDE, LOW + 2], [T + SIDE, LOW + 2], [608.7, 4.8]], y);
  b.frame(0, 0, 0, MP.bearing, () => {
    deckRun(b, -T - SIDE, T + SIDE, 3, road, 8, 2, STEEL);
    b.color(STEEL);
    throughTruss(b, -T + 3.5, T - 3.5, () => LOW, t => 20 * Math.pow(Math.sin(Math.PI * t), 0.6), 16, 12);
    for (const s of [-1, 1]) {
      throughTruss(b, s * (T + 3.5), s * (T + SIDE), () => LOW, t => 17 * Math.pow(Math.sin(Math.PI * t), 0.6), 16, 10);
      const y = s * T;
      b.color(CONC).box(0, y, -3, 24, 9, 3 + LOW - 0.8);
      b.box(0, s * (T + SIDE), -3, 22, 6, 3 + LOW - 0.8);
      b.color(STEEL);
      const zs: number[] = [];
      for (let i = 0; i <= 6; i++) zs.push(LOW + ((TOP - 5 - LOW) * i) / 6);
      for (const sx of [-1, 1]) latticeLeg(b, () => rect(sx * 9.5, y, 3.2, 7), zs, 1.0, 0.4);
      for (const z of zs.slice(3)) b.beam([-7.9, y, z], [7.9, y, z], 0.7);
      for (let i = 3; i < zs.length - 1; i++) {
        wire(b, [-7.9, y, zs[i]], [7.9, y, zs[i + 1]], 0.4);
        wire(b, [7.9, y, zs[i]], [-7.9, y, zs[i + 1]], 0.4);
      }
      // curved tower heads
      b.box(0, y, TOP - 5, 22.5, 8, 2.4);
      for (const sx of [-1, 1]) b.dome(sx * 9.5, y, 3.4, TOP - 2.6, 2.6, 8, 3);
      b.color('#8F8A80').box(0, y + s * 5.4, TOP - 22, 15, 2.4, 12);
    }
    arcade(b, -T - SIDE, -627.5, road, 8, CONC, 38, 2.2, 2, 13);
    arcade(b, T + SIDE, 608.7, road, 8, CONC, 38, 2.2, 2, 13);
  });
}

const marineParkwayBridge: Landmark = {
  id: 'marine_parkway_bridge',
  name: 'Marine Parkway–Gil Hodges Memorial Bridge',
  kind: 'bridge',
  built: [1936.5, 1937.5],
  end: 9999,
  anchor: MP.anchor,
  build: marineBuild,
  facts: {
    Construction: 'contracts let in mid-1936, the lift span floated into place Jan 13, 1937; opened Jul 3, 1937 (Marine Parkway Authority; David B. Steinman, principal designer; Emil Praeger, chief engineer)',
    Form: 'vertical lift bridge: centre span 540 ft, the longest highway lift span in the world when built, between two fixed truss spans (1,500 ft together); 4,022 ft long',
    Clearance: '55 ft closed, 150 ft raised',
    Model: 'shown closed; lift span centred where OpenStreetMap maps the movable span, on the line midway between Overture’s two carriageways; tower positions (no outlines mapped), tower height (215 ft), truss depths and spacing, the flanking spans’ equal lengths, pier sizes and the approach grades are estimated; the month the work began in 1936 is estimated'
  },
  sources: [WIKI + 'Marine_Parkway%E2%80%93Gil_Hodges_Memorial_Bridge']
};

// ------------------------------------------------------------ Roosevelt Island Bridge (1952–1955)
// Wikipedia (Roosevelt Island Bridge): vertical lift, main span 418 ft, 40 ft wide, 2,877 ft long,
// 100 ft clear when open; construction from Mar 17, 1952, opened May 18, 1955. OSM tower piers
// (ways 1016496518, 1016496519): 134.2 m apart centre to centre (= the 418 ft span between tower
// faces with towers 6.8 m deep), bearing 122.3°; deck outline from 89 m west to 178 m east.
const RI = axisOf([-73.946532, 40.763784], [-73.945187, 40.763134]); // Roosevelt Island tower → Queens tower

function rooseveltBuild(b: MeshBuilder) {
  const LOW = 40 * FT; // closed clearance (not in the sources: estimated)
  const TOP = 170 * FT; // tower height (estimated)
  const STEEL = '#8E8F8A';
  const T = RI.half;
  const road = (y: number) => lerpAt([[T + 3.4, LOW + 1.8], [182.4, 5.3]], y);
  b.frame(0, 0, 0, RI.bearing, () => {
    deckRun(b, -89, T + 3.4, 2, road, 20 * FT, 1.8, STEEL);
    b.color(STEEL);
    throughTruss(b, -T + 3.4, T - 3.4, () => LOW, flatTop(13), 14, 10);
    for (const s of [-1, 1]) {
      const y = s * T;
      b.color(CONC).box(0, y, -3, 26, 9, 3 + LOW - 0.6);
      b.color(STEEL);
      const zs: number[] = [];
      for (let i = 0; i <= 5; i++) zs.push(LOW + ((TOP - 3 - LOW) * i) / 5);
      for (const sx of [-1, 1]) latticeLeg(b, () => rect(sx * 8.6, y, 3, 6.8), zs, 0.9, 0.35);
      for (const z of zs.slice(2)) b.beam([-7.1, y, z], [7.1, y, z], 0.7);
      for (let i = 2; i < zs.length - 1; i++) {
        wire(b, [-7.1, y, zs[i]], [7.1, y, zs[i + 1]], 0.4);
        wire(b, [7.1, y, zs[i]], [-7.1, y, zs[i + 1]], 0.4);
      }
      b.box(0, y, TOP - 3, 20.5, 7.6, 3);
      b.color('#8F8A80').box(0, y + s * 5, TOP - 16, 13, 2.2, 9);
    }
    arcade(b, T + 3.4, 182.4, road, 20 * FT, CONC, 28, 2, 1.8, 11);
    b.color(CONC);
    for (const y of [-89, -78]) b.box(0, y, 0, 12, 2, LOW);
  });
}

const rooseveltIslandBridge: Landmark = {
  id: 'roosevelt_island_bridge',
  name: 'Roosevelt Island Bridge',
  kind: 'bridge',
  built: [1952.21, 1955.38],
  end: 9999,
  anchor: RI.anchor,
  build: rooseveltBuild,
  replaces: [plot(RI, -RI.half, 30, 12), plot(RI, RI.half, 30, 12)],
  facts: {
    Construction: 'Mar 17, 1952 – May 1955; opened May 18, 1955 as the Welfare Island Bridge, the island’s only road link',
    Form: 'vertical lift bridge over the East River’s east channel: lift span 418 ft, roadway 40 ft wide, 2,877 ft long with its approaches; 100 ft clear when raised',
    Model: 'shown closed; towers on the OpenStreetMap piers (134.2 m centre to centre: the cited 418 ft between tower faces); closed clearance (40 ft), tower height (170 ft), truss depth, counterweights and the Queens approach grade are estimated; the ramp into the Motorgate garage on the island is not modelled'
  },
  sources: [WIKI + 'Roosevelt_Island_Bridge']
};

// ------------------------------------------------------------ Pulaski Bridge (1954)
// Wikipedia (Pulaski Bridge): four-leaf (double-leaf, twin) bascule, main span 177 ft, 39 ft clear,
// 2,810 ft long, opened Sep 10, 1954. OSM bascule piers (ways 1054539113, 992001660): 52.4 m apart
// (177 ft = 54.0 m), 34–38 m across, bearing 10.8°: the piers are set 177 ft apart about their
// midpoint. Approaches: Overture's two carriageways (bridge flag).
const PK_PATHS: V2[][] = [
  [[-73.952621, 40.738989], [-73.952854, 40.738293], [-73.952926, 40.737957], [-73.952915, 40.737648], [-73.952767, 40.736745]],
  [[-73.952461, 40.739463], [-73.951497, 40.742326]],
  [[-73.952578, 40.739480], [-73.951620, 40.742353]],
  [[-73.952737, 40.739005], [-73.952969, 40.738315], [-73.953046, 40.737951], [-73.953034, 40.737637], [-73.952886, 40.736737]]
]; // Overture carriageways of the approach viaducts, from the bascule piers outward
const PK = axisOf([-73.952698, 40.739007], [-73.952582, 40.739473]); // Brooklyn pier → Queens pier

function pulaskiBuild(b: MeshBuilder) {
  const S = (177 * FT) / 2;
  const road = 39 * FT + 2.6; // 39 ft clear under girders 1.4 m deep at mid-span below a 1.2 m floor (depths estimated)
  const RED = '#A8483F';
  b.frame(0, 0, 0, PK.bearing, () => {
    deckSeg(b, -S, S, road, road, 12.5, 1.2, RED, ROAD, 3.5);
    // haunched bascule girders: deep at the piers, shallow where the leaves meet
    b.color(RED);
    for (const x of [-7, 0, 7, 14]) {
      for (let i = 0; i < 6; i++) {
        const a = -S + (2 * S * i) / 6;
        const c = -S + (2 * S * (i + 1)) / 6;
        const dep = (y: number) => 1.4 + 3.2 * (Math.abs(y) / S) ** 2;
        b.quad([x, a, road - 1.2], [x, c, road - 1.2], [x, c, road - 1.2 - dep(c)], [x, a, road - 1.2 - dep(a)]);
      }
    }
    b.color(CONC);
    for (const s of [-1, 1]) {
      b.box(3.5, s * (S + 4), -3, 36, 9, 3 + road);
      for (const x of [-12.5, 19.5]) b.box(x, s * (S + 4), road, 5, 5, 6.5);
    }
  });
  approachPaths(b, PK.anchor, PK_PATHS, road, i => (lngLatToLocal(PK.anchor, PK_PATHS[i][PK_PATHS[i].length - 1])[1] > 0 ? 5.8 : 3.4), 11, CONC, 30);
}

const pulaskiBridge: Landmark = {
  id: 'pulaski_bridge',
  name: 'Pulaski Bridge',
  kind: 'bridge',
  built: [1952.0, 1954.69],
  end: 9999,
  anchor: PK.anchor,
  build: pulaskiBuild,
  facts: {
    Opened: 'Sep 10, 1954 (Frederick Zurmuhlen, Department of Public Works), replacing the Vernon Avenue Bridge over Newtown Creek',
    Form: 'double-leaf bascule with twin leaves each way, main span 177 ft, 39 ft clear, 2,810 ft long with its approach viaducts',
    Model: 'shown closed; bascule piers set 177 ft apart about the midpoint of the OpenStreetMap piers (52.4 m apart there); girder depths, pier and operator-house sizes and the construction start (1952) are estimated; the approaches follow Overture’s two carriageways down to the terrain grid'
  },
  sources: [WIKI + 'Pulaski_Bridge']
};

export const BRIDGES: Landmark[] = [brooklynBridge, manhattanBridge, williamsburgBridge, gwBridge1931, gwBridge, queensboroBridge, verrazzanoBridge, hellGateBridge, rfkSuspension, rfkLift, rfkBronxKill, highBridgeStone, highBridgeRiverArches, highBridgeSteelArch, washingtonBridge, whitestoneBridge, throgsNeckBridge, bayonneBridge1931, bayonneBridge, outerbridgeCrossing, goethalsBridge1928, goethalsEastbound, goethalsWestbound, macombsDamBridge, universityHeightsBridge, broadwayBridge, henryHudsonBridge, kosciuszkoBridge1939, kosciuszkoEastbound, kosciuszkoWestbound, marineParkwayBridge, rooseveltIslandBridge, pulaskiBridge];
