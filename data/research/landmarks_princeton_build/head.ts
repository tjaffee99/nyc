/**
 * Princeton, New Jersey: the campus and town landmarks added in the towns round
 * (2026-11-11). Research: data/research/landmarks_princeton.md (dimensions, sources, checks).
 *
 * Conventions as nj-outer.ts: the anchor is a point inside the footprint; plans are the real
 * outlines of data/interim/counties/nj_mercer.parquet (Overture / OpenStreetMap, ODbL)
 * re-expressed in anchor-local metres (x east, y north). Heights are cited figures where the
 * note gives one; otherwise estimates, named in each model's `Model:` fact.
 */
import {MeshBuilder, circle, rect, type V2} from './kit';
import type {Landmark} from './types';

const WIKI = 'https://en.wikipedia.org/wiki/';
const OVERTURE = 'https://docs.overturemaps.org/guides/buildings/';
const MUSEUM = 'https://princetonianamuseum.org/';

export const PRINCETON: Landmark[] = [];

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

/** Frame whose +y points at the compass bearing `fb` (the building's front), with depth along it. */
function frontFrame(o: Obb, fb: number) {
  let d = Math.abs(((fb - o.bearing) % 180) + 180) % 180;
  if (d > 90) d = 180 - d;
  return d < 45 ? {depth: o.L, width: o.W} : {depth: o.W, width: o.L};
}
