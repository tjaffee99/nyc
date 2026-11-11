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
const ALEXANDER = P(-17.2, -21.7, -14.3, -23.6, -11.3, -21.6, 22.9, -9.2, 24.5, -7.1, 24.3, -4.7, 22.3, -3.4, 20.3, -3.4, 17.9, -4.2, 14.9, 4.6, 12.3, 8.5, 7.4, 12.5, 8.7, 14.0, 8.4, 15.9, 6.6, 17.5, 4.8, 17.7, 2.5, 14.6, -2.1, 14.9, -7.3, 13.5, -11.7, 10.8, -14.3, 7.3, -16.2, 8.7, -18.4, 8.2, -19.5, 6.2, -18.8, 3.9, -15.9, 3.5, -17.0, -3.9, -25.3, -7.1, -20.4, -19.7, -17.0, -18.4);
const ALEXANDER_ANCHOR: V2 = [-74.660584, 40.348373];
const EAST_PYNE = P(-36.9, -14.4, -34.4, -22.0, -35.6, -24.0, -34.8, -25.9, -33.1, -26.3, -30.3, -34.8, -21.1, -31.8, -21.7, -30.2, 3.3, -22.0, 4.9, -24.7, 6.7, -23.6, 7.2, -21.9, 13.4, -19.8, 10.5, -11.4, 12.0, -9.8, 11.4, -7.8, 9.2, -7.4, 1.6, 14.9, 2.8, 16.5, 2.1, 18.6, 0.1, 19.2, -2.7, 27.9, -9.0, 25.9, -11.7, 27.2, -12.7, 25.1, -12.0, 22.9, -20.8, 20.1, -22.5, 25.5, -19.1, 26.5, -20.4, 30.5, -23.9, 29.4, -25.6, 34.7, -33.3, 32.3, -31.7, 27.1, -35.0, 26.1, -33.5, 21.3, -29.7, 22.5, -28.1, 17.7, -35.9, 15.2, -37.3, 17.0, -39.7, 16.4, -40.5, 14.7, -46.5, 12.6, -43.6, 4.3, -44.4, 2.5, -43.8, 0.7, -42.3, 0.3, -40.0, -7.0, -41.7, -7.6, -39.3, -15.2);
const EAST_PYNE_H0 = P(-3.0, -10.8, -24.7, -18.1, -32.1, 3.6, -10.4, 10.8);
const EAST_PYNE_ANCHOR: V2 = [-74.658207, 40.348679];
const CHANCELLOR = P(8.1, -8.5, 13.0, -0.1, 12.5, 1.1, 17.4, 3.1, 18.5, 0.3, 21.4, -1.0, 24.4, 0.1, 26.0, 3.1, 22.7, 12.4, 19.8, 14.0, 16.2, 12.8, 15.2, 9.9, 15.9, 7.6, 10.9, 6.0, 10.3, 8.0, 2.6, 12.0, -6.1, 9.2, -10.7, 0.8, -15.3, -0.7, -18.1, 1.3, -22.2, -0.1, -22.7, -3.3, -19.9, -11.9, -16.8, -14.0, -13.5, -12.7, -12.2, -9.7, -12.7, -8.2, -7.1, -6.3, -6.7, -7.4, 0.4, -10.9);
const CHANCELLOR_ANCHOR: V2 = [-74.658605, 40.34907];
const HOLDER = P(-0.7, -13.4, -43.5, -29.9, -39.1, -41.1, -30.1, -37.6, -30.4, -36.7, 3.2, -23.7, 3.3, -24.9, 13.4, -21.0, 11.6, -16.5, 13.5, -15.7, 10.9, -9.0, 9.7, -9.5, -8.1, 35.9, -6.3, 36.6, -9.1, 43.6, -10.8, 43.0, -12.7, 47.9, -23.3, 43.8, -22.6, 41.9, -64.8, 25.5, -61.1, 16.0, -18.5, 32.3);
const HOLDER_ANCHOR: V2 = [-74.661223, 40.348601];
const FIRESTONE = P(23.6, -34.4, 30.1, -32.1, 29.8, -34.0, 33.8, -38.8, 40.0, -38.3, 42.7, -32.1, 38.9, -27.0, 37.2, -27.0, 35.7, -22.1, 47.3, -18.5, 42.0, -3.4, 43.9, -2.7, 40.9, 5.7, 42.8, 9.0, 41.7, 12.3, 38.8, 13.5, 36.8, 12.8, 31.4, 27.4, 14.8, 22.2, 12.8, 28.1, 32.6, 34.1, 30.4, 42.2, 23.6, 53.6, 21.4, 52.8, 21.0, 54.6, 22.0, 55.6, 22.7, 57.4, 22.5, 59.6, 20.7, 60.9, 18.9, 61.2, 16.9, 60.7, 15.8, 59.3, 15.6, 57.2, 13.5, 56.5, 12.6, 59.0, -49.7, 37.2, -48.2, 33.1, -37.0, 37.0, -34.9, 31.1, -45.4, 27.4, -41.6, 16.7, -31.6, 20.2, -27.4, 8.4, -43.8, 2.6, -41.1, -5.2, -67.2, -14.4, -57.9, -40.4, -60.5, -41.3, -59.0, -45.6, -56.3, -44.7, -53.7, -52.1, -27.7, -43.0, -24.8, -51.1, -20.1, -49.5, -18.9, -52.8, -6.1, -48.3, -5.6, -49.7, -2.9, -48.8, 0.8, -59.3, 28.9, -49.5);
const FIRESTONE_ANCHOR: V2 = [-74.657345, 40.349611];
const ROBERTSON = P(19.3, 30.6, -36.2, -3.0, -19.6, -30.3, 36.2, 2.9);
const ROBERTSON_ANCHOR: V2 = [-74.65471, 40.348419];
const LEWIS = P(-35.5, -31.1, -19.7, -29.8, -18.7, -20.9, -7.7, -21.8, -7.2, -13.6, -3.9, -13.9, -3.8, -18.4, 9.3, -16.5, 19.6, -15.9, 18.8, -10.6, 20.6, -10.4, 19.8, -1.3, 30.5, -3.6, 31.3, 3.4, 32.2, 4.4, 38.7, 1.3, 40.9, 5.4, 45.7, 4.4, 49.3, 14.3, 46.0, 15.1, 41.9, 18.6, 39.2, 17.5, 32.8, 22.7, 31.3, 22.3, 27.2, 23.3, 24.9, 29.5, -1.7, 19.8, 1.0, 12.5, 2.1, 12.9, 3.0, 10.3, -5.9, 10.0, -10.6, 3.9, -20.5, 5.0, -29.4, 4.6, -30.9, 1.3, -30.9, -4.6, -33.9, -4.5, -40.2, -16.7, -42.4, -17.1, -34.4, -27.5);
const LEWIS_ANCHOR: V2 = [-74.652764, 40.346205];
const FINE = P(38.3, 4.9, 27.0, 24.0, -14.2, 9.2, -11.5, 1.7, -24.0, -2.8, -23.4, -1.7, -24.3, -1.1, -26.0, -1.7, -26.3, -2.6, -27.5, -3.1, -28.6, -2.5, -29.1, -1.3, -28.6, -0.6, -29.1, 1.0, -30.0, 1.6, -30.8, 0.7, -31.3, 1.8, -41.2, -1.9, -40.7, -3.1, -42.2, -2.9, -42.7, -4.1, -42.2, -5.3, -41.2, -5.8, -40.8, -6.9, -41.3, -7.9, -44.7, -8.4, -45.0, -9.3, -44.1, -10.0, -45.9, -10.6, -42.3, -20.7, -40.5, -20.1, -40.8, -21.6, -39.7, -22.0, -36.9, -20.2, -35.9, -20.7, -35.6, -21.8, -36.0, -22.6, -35.4, -24.0, -34.3, -24.3, -33.8, -23.5, -33.3, -24.8, -23.3, -21.2, -23.7, -19.9, -22.3, -19.8, -21.8, -19.0, -23.5, -16.2, -23.1, -15.2, -19.8, -14.6, -19.4, -13.7, -20.3, -13.0, 11.6, -1.6, 11.8, -3.8, 10.6, -4.3, 11.9, -7.8, 13.1, -7.4, 13.4, -8.5, 17.2, -7.2, 16.8, -6.0, 17.8, -5.7, 16.5, -2.1, 15.6, -2.5, 14.2, -0.6, 22.6, 2.4, 25.6, -2.7, 22.4, -4.5, 30.6, -18.3, 49.7, -7.0, 41.5, 6.7);
const FINE_ANCHOR: V2 = [-74.652416, 40.345795];
const JADWIN = P(-60.2, 23.0, -53.3, 8.8, -59.4, 5.6, -39.3, -29.7, -44.0, -31.8, -33.1, -51.3, -24.7, -56.8, -12.6, -62.9, 0.7, -66.0, 11.8, -66.0, 27.7, -62.2, 39.3, -55.0, 48.4, -45.7, 54.9, -32.6, 59.2, -21.1, 58.2, -5.7, 52.9, 8.7, 48.5, 6.8, 36.7, 47.0, 30.9, 45.0, 23.9, 60.2, 15.2, 61.1, 5.3, 60.1, -45.0, 38.5, -54.3, 31.7);
const JADWIN_ANCHOR: V2 = [-74.648647, 40.343409];
const MCCARTER = P(3.7, 45.8, 3.8, 43.8, 1.3, 42.9, 0.7, 44.6, -23.1, 36.7, -22.5, 35.0, -24.9, 34.1, -24.9, 35.0, -26.4, 36.4, -28.4, 36.3, -29.7, 34.8, -29.6, 32.9, -28.2, 31.5, -26.2, 31.6, -25.4, 28.4, -26.3, 28.1, -16.7, -1.8, -13.7, -1.2, -7.4, -18.2, -11.9, -19.8, -4.5, -40.0, 0.9, -38.0, 3.7, -45.5, 24.5, -37.5, 23.5, -30.4, 25.7, -31.4, 28.0, -30.6, 29.0, -28.4, 28.2, -26.1, 25.9, -25.1, 20.3, -2.1, 18.3, -2.8, 16.8, 1.1, 20.9, 2.7, 7.2, 42.6, 8.5, 44.0, 8.5, 46.0, 7.0, 47.3, 5.0, 47.2);
const MCCARTER_ANCHOR: V2 = [-74.660534, 40.344013];
const WHIG = P(-12.9, 3.6, -7.6, -11.0, 5.6, -6.2, 4.8, -8.1, 5.7, -9.8, 7.5, -10.1, 8.8, -8.9, 8.5, -7.0, 6.6, -6.0, 12.9, -3.7, 7.7, 10.7, 2.6, 8.8, -0.0, 16.0, -11.1, 12.0, -8.6, 5.2);
const WHIG_ANCHOR: V2 = [-74.658629, 40.347799];
const CLIO = P(-12.3, 3.9, -7.5, -10.3, -3.8, -9.1, -2.1, -14.2, 10.9, -9.9, 9.2, -4.9, 12.3, -3.9, 7.3, 10.8, 3.5, 9.6, 1.1, 16.5, -10.9, 12.5, -8.4, 5.2);
const CLIO_ANCHOR: V2 = [-74.659147, 40.347662];
const ART = P(-27.7, 38.6, -28.6, 41.0, -58.1, 30.7, -50.9, 10.3, -46.6, 11.8, -39.7, -8.1, -41.1, -8.6, -34.2, -28.8, -17.4, -23.2, -12.5, -36.3, -27.0, -41.2, -19.6, -62.3, 3.9, -54.2, -0.0, -43.0, 8.7, -40.2, 13.8, -54.6, 36.6, -46.6, 31.7, -32.6, 45.8, -27.9, 48.6, -36.3, 71.3, -28.7, 64.1, -7.3, 43.9, -14.0, 42.3, -9.3, 45.5, -8.1, 39.5, 7.8, 36.0, 6.4, 34.4, 11.2, 36.1, 11.8, 29.5, 19.1, 40.8, 32.6, 34.5, 52.7, 11.0, 45.5, 19.9, 19.2, 9.8, 15.9, -2.0, 47.9);
const ART_H0 = P(1.5, -27.9, -0.9, -21.6, 6.2, -19.1, 8.5, -25.4);
const ART_H1 = P(24.0, -8.3, 29.9, -6.4, 34.5, -20.4, 28.6, -22.3);
const ART_H2 = P(12.3, -14.7, -1.9, -19.6, -4.5, -12.3, 9.7, -7.4);
const ART_ANCHOR: V2 = [-74.657962, 40.347218];
const NPC = P(12.9, 8.0, 3.7, 34.1, -15.8, 27.3, -13.9, 21.8, -15.4, 21.3, -16.0, 22.9, -19.2, 21.8, -20.9, 22.0, -22.4, 21.7, -23.9, 20.1, -28.4, 18.5, -19.0, -8.1, -14.2, -10.7, -10.1, -9.3, -5.5, -22.5, 26.0, -11.5, 18.4, 9.9);
const NPC_ANCHOR: V2 = [-74.660719, 40.348883];

// ====================================================================== Alexander Hall
{
  const o = obb(ALEXANDER);
  PRINCETON.push({
    id: 'pr_alexander_hall',
    name: 'Alexander Hall (Richardson Auditorium)',
    kind: 'building',
    built: [1892, 1894.45],
    end: 9999,
    anchor: ALEXANDER_ANCHOR,
    build: b => {
      block(b, ALEXANDER, 0, 13, '#8B5A45', '#5A4F49');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // great roof over the hall; ridge along the long axis
        b.color('#4F4A46').gable(0, 0, o.W * 0.7, o.L * 0.72, 13, 8, true);
        b.color('#8B5A45').box(0, 0, 13, o.W * 0.7 - 0.4, o.L * 0.72, 0.05);
        // four round corner turrets with conical caps
        for (const sx of [-1, 1]) {
          for (const sy of [-1, 1]) {
            const x = sx * o.W * 0.3;
            const y = sy * o.L * 0.34;
            b.color('#9A6A52').cylinder(x, y, 2.0, 0, 18, 10, {top: false});
            b.color('#4F4A46');
            spire(b, x, y, 2.3, 18, 25, 10);
          }
        }
      });
    },
    replaces: [ALEXANDER],
    facts: {
      Built: 'groundbreaking 1892, completed 1894 and opened 9 June 1894; William Appleton Potter; Richardsonian Romanesque in rusticated brownstone and red granite; 900 seats',
      Model: 'plan is the real outline (Overture, 1,136 m2); dates, style, materials and seating are cited; no height is published: the 13 m eave, the 21 m ridge and the four conical turrets (25 m) are estimated'
    },
    sources: [WIKI + 'Alexander_Hall_(Princeton_University)', WIKI + 'Princeton_Historic_District_(Princeton,_New_Jersey)', OVERTURE]
  });
}

// ====================================================================== East Pyne Hall
{
  const o = obb(EAST_PYNE);
  const bR = (o.bearing * Math.PI) / 180;
  const westX = -Math.cos(bR) > 0 ? 1 : -1; // sign of local +x pointing west
  PRINCETON.push({
    id: 'pr_east_pyne_hall',
    name: 'East Pyne Hall (Pyne Library)',
    kind: 'building',
    built: [1896, 1897.9],
    end: 9999,
    anchor: EAST_PYNE_ANCHOR,
    build: b => {
      block(b, EAST_PYNE, 0, 14, '#9C8F77', '#6A655C', [EAST_PYNE_H0]);
      // crenellated parapet round the outer wall
      b.color('#9C8F77').prism(EAST_PYNE, 14, 15, {top: false});
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        const tx = westX * (o.W / 2 - 4.2);
        // the large tower over the western arch
        b.color('#A59A82').box(tx, 0, 14, 8.6, 8.6, 20);
        b.color('#8F846D').box(tx, 0, 34, 9.6, 9.6, 1.2);
        b.color('#A59A82').box(tx, 0, 35.2, 7.6, 7.6, 3);
        b.color('#6A655C');
        spire(b, tx, 0, 5.4, 38.2, 44, 4);
        for (const sx of [-1, 1]) {
          for (const sy of [-1, 1]) b.color('#A59A82').box(tx + sx * 4.3, sy * 4.3, 34, 1.2, 1.2, 6);
        }
        // the lower, battlemented tower over the eastern arch
        const ex = -westX * (o.W / 2 - 4.2);
        b.color('#A59A82').box(ex, 0, 14, 7.2, 7.2, 9);
        b.color('#8F846D').box(ex, 0, 23, 8, 8, 1);
        for (const sx of [-1, 1]) {
          for (const sy of [-1, 1]) b.box(ex + sx * 3.5, sy * 3.5, 24, 1.1, 1.1, 1.2);
        }
      });
    },
    replaces: [EAST_PYNE],
    facts: {
      Built: '1896-97 as Pyne Library, William Appleton Potter; the first explicitly Collegiate Gothic building at Princeton; the university\'s main library until 1948',
      Plan: 'a quadrangle of 216 x 155 ft (65.8 x 47.2 m) with a large tower over the western arch and a shorter, battlemented one over the eastern arch',
      Model: 'plan and courtyard are the real outline (Overture; the quadrangle size is cited and matches it); no height is published: the 14 m wall, the 44 m western tower and the 24 m eastern tower are estimated'
    },
    sources: [MUSEUM + 'artifact/252ecfae-9f12-4bf4-ae94-647a29375c32', WIKI + 'William_Appleton_Potter', OVERTURE]
  });
}

// ====================================================================== Chancellor Green
{
  const o = obb(CHANCELLOR);
  PRINCETON.push({
    id: 'pr_chancellor_green',
    name: 'Chancellor Green Library',
    kind: 'building',
    built: [1872, 1873.4],
    end: 9999,
    anchor: CHANCELLOR_ANCHOR,
    build: b => {
      block(b, CHANCELLOR, 0, 10, '#8C6B55', '#4F4A46');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // the central octagon: 64 ft across, 50 ft (15.2 m) high (1905 library history)
        const r = 9.75 / Math.cos(Math.PI / 8);
        b.color('#8C6B55').prism(circle(0, 0, r, 8), 10, 15.2, {top: false});
        b.color('#4F4A46');
        b.pyramid(circle(0, 0, r + 0.4, 8), 15.2, [0, 0, 22]);
        b.color('#8C6B55').cylinder(0, 0, 1.4, 22, 24, 8);
        b.color('#4F4A46');
        spire(b, 0, 0, 1.7, 24, 27, 8);
        // pitched roofs over the two wings
        for (const s of [-1, 1]) {
          b.color('#4F4A46').gable(0, s * (o.L / 2 - 6), 10, 11, 10, 3.6, false);
        }
      });
    },
    replaces: [CHANCELLOR],
    facts: {
      Built: 'erected 1872, dedicated May 1873 as the University Library; William A. Potter; the most pronounced High Victorian Gothic building on the campus',
      Size: 'central octagon 64 ft (19.5 m) across and 50 ft (15.2 m) high; 160 ft (48.8 m) from wing to wing',
      Model: 'plan is the real outline (Overture, 661 m2; its 48 m length matches the cited 160 ft); octagon width and height are cited; the wings\' 10 m, the steep roof (22 m) and the lantern (27 m) are estimated'
    },
    sources: ['https://static-prod.lib.princeton.edu/scsites/libraryhistory/1905_Williams.html', MUSEUM, WIKI + 'Princeton_Historic_District_(Princeton,_New_Jersey)', OVERTURE]
  });
}

// ====================================================================== Holder Hall
{
  const o = obb(HOLDER);
  const [tx, ty, td] = roomiest(HOLDER, o);
  const s = Math.min(4.8, td * 0.95);
  PRINCETON.push({
    id: 'pr_holder_hall',
    name: 'Holder Hall and Holder Tower',
    kind: 'building',
    built: [1909, 1911],
    end: 9999,
    anchor: HOLDER_ANCHOR,
    build: b => {
      block(b, HOLDER, 0, 15, '#A19882', '#5F5C57');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // Holder Tower: 145 ft (44.2 m) above the campus
        b.color('#A9A08A').box(tx, ty, 15, 2 * s, 2 * s, 17);
        b.color('#928973').box(tx, ty, 32, 2 * s + 1, 2 * s + 1, 0.9);
        b.color('#A9A08A').box(tx, ty, 32.9, 2 * s - 0.8, 2 * s - 0.8, 4.5);
        b.color('#5F5C57').pyramid(rect(tx, ty, 2 * s - 0.4, 2 * s - 0.4), 37.4, [tx, ty, 44.2]);
        for (const sx of [-1, 1]) {
          for (const sy of [-1, 1]) b.color('#A9A08A').box(tx + sx * (s - 0.2), ty + sy * (s - 0.2), 32.9, 1, 1, 6);
        }
      });
    },
    replaces: [HOLDER],
    facts: {
      Built: 'commissioned 1909, the dormitory opened in 1910 and the tower was completed in 1911; Day & Klauder; Collegiate Gothic',
      Height: 'Holder Memorial Tower rises 145 ft (44.2 m) (most sources; a few say 140 ft)',
      Model: 'plan is the real outline (Overture, 1,826 m2); the tower\'s height and the dates are cited; the 15 m eave, the tower\'s plan (about 9.6 m) and where it stands (the outline\'s deepest part) are estimated'
    },
    sources: [MUSEUM + 'artifact/e6c46c30-f5d3-4757-b41d-59ea1d1c4645', 'https://dspace.njstatelib.org/items/741726e8-a7ae-41b5-ac55-2677a78c18b9', 'https://pjcarlino.blogspot.com/2008/04/holder-hall-prinecton.html', OVERTURE]
  });
}

// ====================================================================== Firestone Library
{
  const o = obb(FIRESTONE);
  PRINCETON.push({
    id: 'pr_firestone_library',
    name: 'Firestone Library',
    kind: 'building',
    built: [1946.5, 1948.5],
    end: 9999,
    anchor: FIRESTONE_ANCHOR,
    build: b => {
      block(b, FIRESTONE, 0, 14.5, '#B1A78F', '#6A675F');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // slate roof: a hip over the deepest part of the plan, and a pitched entrance bay
        const [hx, hy, hd] = roomiest(FIRESTONE, o);
        const s = Math.min(hd * 0.95, 22);
        b.color('#5C5A57').hip(hx, hy, 2 * s, 2 * s, 14.5, 3.2);
        b.color('#B8AE96').box(hx, hy - s - 1, 0, 12, 2, 16.5);
        b.color('#5C5A57').gable(hx, hy - s - 1, 12.4, 2.2, 16.5, 2.2, false);
      });
    },
    replaces: [FIRESTONE],
    facts: {
      Built: 'opened 1948 (extended 1971 and 1988); Robert B. O\'Connor and Walter H. Kilham Jr.; Collegiate Gothic; four floors above ground and three partly below',
      Model: 'plan is the real outline (Overture, 8,526 m2, which includes the later extensions); the opening year and the four floors are cited; the 14.5 m eave, the hip roof and the entrance bay are estimated; construction start (1946) is an estimate'
    },
    sources: [WIKI + 'Firestone_Library', OVERTURE]
  });
}

// ====================================================================== Robertson Hall
{
  const o = obb(ROBERTSON);
  PRINCETON.push({
    id: 'pr_robertson_hall',
    name: 'Robertson Hall',
    kind: 'building',
    built: [1963.5, 1966.4],
    end: 9999,
    anchor: ROBERTSON_ANCHOR,
    build: b => {
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        const wd = o.W;
        const ln = o.L;
        const set = 3.6;
        // ground floor, 28 ft (8.5 m) high, set back inside the colonnade
        b.color('#CFC7B2').box(0, 0, 0, wd - 2 * set, ln - 2 * set, 8.5);
        // the upper floor and flat roof on the full outline
        b.color('#E7E3D6').box(0, 0, 8.5, wd, ln, 4.2);
        b.color('#D8D3C4').box(0, 0, 12.7, wd + 0.4, ln + 0.4, 0.3);
        // 58 tapered white columns round the perimeter
        const per = 2 * (wd + ln);
        const step = per / 58;
        for (let i = 0; i < 58; i++) {
          let t = i * step;
          let x = 0;
          let y = 0;
          if (t < ln) {
            x = -wd / 2 + 0.4;
            y = -ln / 2 + t;
          } else if ((t -= ln) < wd) {
            x = -wd / 2 + t;
            y = ln / 2 - 0.4;
          } else if ((t -= wd) < ln) {
            x = wd / 2 - 0.4;
            y = ln / 2 - t;
          } else {
            t -= ln;
            x = wd / 2 - t;
            y = -ln / 2 + 0.4;
          }
          b.color('#F3F1EA').loft([rect(x, y, 0.5, 0.5), rect(x, y, 0.9, 0.9)], [0, 12.7], {top: false});
        }
      });
    },
    replaces: [ROBERTSON],
    facts: {
      Built: 'gift of 1961, dedicated May 1966; Minoru Yamasaki, for the Woodrow Wilson School',
      Design: 'three levels (one below ground); 58 tapered white quartz-faced columns carry the top floor over a ground storey 28 ft (8.5 m) high with non-bearing travertine walls; reflecting pool on the plaza',
      Model: 'plan is the real outline (Overture, 2,096 m2); the column count and the 28 ft ground storey are cited; the 4.2 m upper floor (12.7 m top), the 3.6 m setback of the ground storey and the column taper are estimated; construction start (1963.5) is an estimate'
    },
    sources: [MUSEUM + 'artifact/432444fe-2157-4704-92f6-a6d54d8ef1f1', OVERTURE]
  });
}

// ====================================================================== Lewis Library
{
  const o = obb(LEWIS);
  const [tx, ty, td] = roomiest(LEWIS, o);
  const s = Math.min(6.5, td * 0.95);
  PRINCETON.push({
    id: 'pr_lewis_library',
    name: 'Lewis Library (Frank Gehry)',
    kind: 'building',
    built: [2006, 2008.7],
    end: 9999,
    anchor: LEWIS_ANCHOR,
    build: b => {
      block(b, LEWIS, 0, 9.5, '#8F5F49', '#B4B9BC');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // the tower: 105 ft (32.0 m) to the parapet; brick below, stainless-steel lid above
        b.color('#8F5F49').box(tx, ty, 9.5, 2 * s, 2 * s, 18);
        b.color('#B4B9BC').loft([rect(tx, ty, 2 * s, 2 * s), rect(tx, ty, 2 * s - 2.6, 2 * s - 2.6)], [27.5, 32.004]);
      });
    },
    replaces: [LEWIS],
    facts: {
      Opened: '11 September 2008; Frank Gehry; brick and stainless steel; 87,000 gross sq ft; four storeys in the tower, three in the Ivy Lane wing, two in the Washington Road wing',
      Height: 'highest point 105 ft (32.0 m), from grade to the top of the parapet coping (the university\'s fact sheet; earlier coverage said 103 ft)',
      Model: 'plan is the real outline (Overture, 2,463 m2); the 32.0 m top is cited; the wings\' height (9.5 m), the tower\'s plan and place (the outline\'s deepest part) and the steel lid are estimated; construction start (2006) is an estimate'
    },
    sources: ['https://www.princeton.edu/news/2008/09/03/lewis-library-fact-sheet', OVERTURE]
  });
}

// ====================================================================== Fine Hall
{
  const o = obb(FINE);
  // the tower stands at the western end of the base
  const westSign = Math.sin((o.bearing * Math.PI) / 180) > 0 ? -1 : 1; // sign of local y that points west
  const [tx, ty, td] = roomiest(FINE, o, (_x, y) => y * westSign > o.L * 0.1);
  const s = Math.min(8.5, td * 0.95);
  PRINCETON.push({
    id: 'pr_fine_hall',
    name: 'Fine Hall (mathematics tower)',
    kind: 'tower',
    built: [1966.5, 1970.2],
    end: 9999,
    anchor: FINE_ANCHOR,
    build: b => {
      block(b, FINE, 0, 11, '#8D8574', '#6F6B62');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // 170 ft (51.8 m) tower of ten floors on the three-storey base
        b.color('#99917F').box(tx, ty, 11, 2 * s, 2 * s, 40.816);
        b.color('#6F6B62').box(tx, ty, 51.816, 2 * s + 0.4, 2 * s + 0.4, 0.001);
        // continuous bands of windows read as dark strips
        for (let z = 14; z < 50; z += 3.6) b.color('#3F4A52').box(tx, ty, z, 2 * s + 0.12, 2 * s + 0.12, 1.4);
      });
    },
    replaces: [FINE],
    facts: {
      Built: 'commissioned 1966, occupied and dedicated 17 March 1970; Warner, Burns, Toan and Lunde; a long three-storey base topped by a tower of ten more floors, for the departments of mathematics and statistics',
      Height: 'the tower is 170 ft (51.8 m), 17 stories as counted by the university when it won the zoning variance of 1965',
      Model: 'plan is the real outline (Overture, 1,922 m2); the 170 ft height and the 3 + 10 floors are cited; the base height (11 m), the tower\'s plan and its place at the western end are estimated'
    },
    sources: [MUSEUM + 'artifact/80804cbc-2146-4bad-913c-12a3569d090d', MUSEUM + 'reference/188787d5-d55e-4260-97ed-5c54f37a70ad', OVERTURE]
  });
}

// ====================================================================== Jadwin Gymnasium
{
  const o = obb(JADWIN);
  PRINCETON.push({
    id: 'pr_jadwin_gymnasium',
    name: 'Jadwin Gymnasium',
    kind: 'stadium',
    built: [1964.5, 1969.4],
    end: 9999,
    anchor: JADWIN_ANCHOR,
    build: b => {
      block(b, JADWIN, 0, 8, '#9A958B', '#7B7870');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // three interlocking shells of unequal height over the arena
        const bw = (o.W * 0.86) / 3;
        const rise = [10, 7, 4.5];
        b.color('#8E918F');
        for (let i = 0; i < 3; i++) vault(b, -o.W * 0.43 + bw * (i + 0.5), 0, bw, o.L * 0.82, 8, rise[i]);
      });
    },
    replaces: [JADWIN],
    facts: {
      Built: 'groundbreaking 1964, opened 1969, $6.5 million; Walker O. Cain & Associates; 250,000 sq ft on five levels; 6,854 seats',
      Roof: 'a roof of three interlocking shells',
      Model: 'plan is the real outline (Overture, 10,907 m2); the dates, seating and the three shells are cited; no height is published: the 8 m wall and the shells (18, 15 and 12.5 m) are estimated, and the shells are drawn as parabolic vaults'
    },
    sources: [WIKI + 'Jadwin_Gymnasium', OVERTURE]
  });
}

// ====================================================================== McCarter Theatre
{
  const o = obb(MCCARTER);
  const stageEnd = clearance(MCCARTER, ...toWorld(o, 0, o.L * 0.3)) > clearance(MCCARTER, ...toWorld(o, 0, -o.L * 0.3)) ? 1 : -1;
  PRINCETON.push({
    id: 'pr_mccarter_theatre',
    name: 'McCarter Theatre',
    kind: 'building',
    built: [1928, 1930.15],
    end: 9999,
    anchor: MCCARTER_ANCHOR,
    build: b => {
      block(b, MCCARTER, 0, 11, '#B0734F', '#5E5A55');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // auditorium roof
        b.color('#4F4C49').gable(0, -stageEnd * o.L * 0.1, o.W * 0.55, o.L * 0.5, 11, 5, true);
        // the stage house at one end
        b.color('#A66A49').box(0, stageEnd * o.L * 0.3, 11, o.W * 0.6, o.L * 0.3, 13);
        b.color('#5E5A55').box(0, stageEnd * o.L * 0.3, 24, o.W * 0.6 + 0.4, o.L * 0.3 + 0.4, 0.4);
      });
    },
    replaces: [MCCARTER],
    facts: {
      Opened: '21 February 1930 with the Triangle Club show The Golden Dog; Collegiate Gothic; a 40-foot proscenium stage (the Berlind Theatre of 2003 was added later)',
      Model: 'plan is the real outline (Overture, 2,945 m2, including the later additions); the opening date and style are cited; no height or architect was found: the 11 m wall, the auditorium roof, the 24 m stage house and its end are estimated; construction start (1928) is an estimate'
    },
    sources: [WIKI + 'McCarter_Theatre', MUSEUM + 'artifact/aef55632-fd7b-4d93-84ce-16e7f3eaadc3', OVERTURE]
  });
}

// ====================================================================== Whig Hall and Clio Hall
function temple(id: string, name: string, ring: V2[], anchor: V2, frontBearing: number, other: string) {
  const o = obb(ring);
  const fd = frontFrame(o, frontBearing);
  PRINCETON.push({
    id,
    name,
    kind: 'building',
    built: [1891, 1893],
    end: 9999,
    anchor,
    build: b => {
      const sc = 0.8;
      block(b, ring, 0, 9.6, '#E9E6DC', '#D9D5C8');
      b.frame(o.cx, o.cy, 0, frontBearing, () => {
        const wd = fd.width * sc;
        const dp = fd.depth * sc;
        b.color('#D4D0C2').box(0, 0, 9.6, wd, dp, 0.5);
        b.color('#C9C5B7').gable(0, 0, wd, dp, 10.1, 3.4, true);
        // Ionic portico on the front: six columns carrying the pediment
        colonnade(b, -wd / 2 + 0.8, wd / 2 - 0.8, dp / 2 - 0.3, 0, 9.6, 6, 0.5);
        b.color('#E9E6DC').box(0, dp / 2 - 0.3, 9.9, wd, 1.6, 0.8);
      });
    },
    replaces: [ring],
    facts: {
      Built: 'marble Greek-revival temples of 1893 for the two literary societies (the Ionic form of a Greek temple, replacing wood-and-stucco buildings of 1838); Arthur Page Brown; Whig Hall and ' + other + ' are identical',
      Model: 'plan is the real outline; the date, material and style are cited; no height is published: the 9.6 m wall, the 3.4 m pediment, the six-column portico and the front (the two halls face each other) are estimated; construction start (1891) is an estimate'
    },
    sources: ['https://lostnewengland.com/2021/03/clio-and-whig-halls-princeton-new-jersey/', 'https://dspace.njstatelib.org/items/cd452971-f61c-432f-a2dd-ab49f3883507', OVERTURE]
  });
}
// Whig (east) faces west, Clio (west) faces east
temple('pr_whig_hall', 'Whig Hall', WHIG, WHIG_ANCHOR, 270, 'Clio Hall');
temple('pr_clio_hall', 'Clio Hall', CLIO, CLIO_ANCHOR, 90, 'Whig Hall');

// ====================================================================== Princeton University Art Museum
{
  const o = obb(ART);
  const holes = [ART_H0, ART_H1, ART_H2];
  PRINCETON.push({
    id: 'pr_art_museum',
    name: 'Princeton University Art Museum (2025)',
    kind: 'building',
    built: [2021.5, 2025.83],
    end: 9999,
    anchor: ART_ANCHOR,
    build: b => {
      block(b, ART, 0, 12.5, '#BDB29A', '#A59B86', holes);
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // nine interlocking pavilions: the taller ones as raised volumes over a 3 x 3 grid
        const hs = [5, 2.5, 4, 3, 6, 3.5, 4.5, 2.5, 5];
        let k = 0;
        for (let iy = 0; iy < 3; iy++) {
          for (let ix = 0; ix < 3; ix++, k++) {
            const x = (ix - 1) * (o.W / 3);
            const y = (iy - 1) * (o.L / 3);
            const [wx, wy] = toWorld(o, x, y);
            let d = clearance(ART, wx, wy);
            for (const h of holes) d = Math.min(d, -clearance(h, wx, wy));
            if (d < 5) continue;
            const s = Math.min(d * 0.9, o.W / 3 * 0.8);
            b.color(k % 2 ? '#C9BEA6' : '#AFA58E').box(x, y, 12.5, 2 * s, 2 * s, hs[k]);
          }
        }
      });
    },
    replaces: [ART],
    facts: {
      Built: 'construction began summer 2021 after the old museum was demolished; opened 31 October 2025; Adjaye Associates with Cooper Robertson; about 145,000 sq ft; three storeys of nine interlocking pavilions in alternating rough and polished stone',
      Model: 'plan is the real outline with its three courtyards (Overture, 7,474 m2); the dates, three storeys and nine pavilions are cited; no height is published: the 12.5 m body and the raised pavilion volumes (to 18 m) are estimated. The museum of 1890 / 1966 on this ground is not modelled'
    },
    sources: [WIKI + 'Princeton_University_Art_Museum', 'https://www.dezeen.com/2025/10/31/adjaye-associates-princeton-university-art-museum/amp/', OVERTURE]
  });
}

// ====================================================================== Nassau Presbyterian Church
{
  const o = obb(NPC);
  PRINCETON.push({
    id: 'pr_nassau_presbyterian',
    name: 'Nassau Presbyterian Church',
    kind: 'building',
    built: [1835, 1836.5],
    end: 9999,
    anchor: NPC_ANCHOR,
    build: b => {
      const fd = frontFrame(o, 0);
      block(b, NPC, 0, 9, '#E4DCC8', '#8F8A80');
      b.frame(o.cx, o.cy, 0, 0, () => {
        const wd = fd.width * 0.62;
        const dp = fd.depth * 0.8;
        // Greek Revival front to Nassau Street (north), pedimented, with a steeple behind the front
        b.color('#8F8A80').gable(0, 0, wd, dp, 9, 4.2, true);
        b.color('#EFEADB');
        colonnade(b, -wd / 2 + 0.8, wd / 2 - 0.8, dp / 2 - 0.3, 0, 9, 4, 0.5);
        const ty = dp / 2 - 4.5;
        b.color('#E4DCC8').box(0, ty, 9, 5.6, 5.6, 11);
        b.color('#EFEADB').box(0, ty, 20, 4.8, 4.8, 5);
        b.color('#6F6B66');
        spire(b, 0, ty, 3.4, 25, 34, 8);
      });
    },
    replaces: [NPC],
    facts: {
      Built: 'the church burned in 1835 and its replacement was completed in 1836; Charles Steadman; Greek Revival in stuccoed brick (fires also in 1813)',
      Model: 'plan is the real outline (Overture, 1,748 m2, including later additions); the date, architect and style are cited; no height is published: the 9 m walls, the portico, the steeple (34 m) and its position are estimated; the front is assumed to face Nassau Street (north); construction start (1835) is an estimate'
    },
    sources: [WIKI + 'Nassau_Presbyterian_Church', WIKI + 'Princeton_Historic_District_(Princeton,_New_Jersey)', OVERTURE]
  });
}
