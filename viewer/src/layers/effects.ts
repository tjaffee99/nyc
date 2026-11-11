/**
 * Events in motion: fires, explosions, collapses, troops on the march, fighting, fleets.
 * data/tables/effects.csv says what happened where (researched: one row per effect, several per
 * event); here each is drawn while the year stands at it, and moves on the wall clock — flames
 * and smoke over a burning area, a blast's ring, a column advancing along its route, powder
 * smoke where it fights. Nothing of this is on the map at any other year, and nothing is
 * computed while no effect is in view of the year: the caller asks `effectsActive` first.
 */
import type {Layer} from '@deck.gl/core';
import {PathLayer, ScatterplotLayer} from '@deck.gl/layers';
import {parseCsv} from '../data/tables';
import {elevationAt} from './elevation';

const files = import.meta.glob('../../../data/tables/effects.csv', {query: '?raw', import: 'default', eager: true}) as Record<string, string>;

type Kind = 'fire' | 'explosion' | 'move' | 'clash' | 'fleet' | 'collapse';
type Effect = {
  id: string;
  kind: Kind;
  side: string;
  y0: number;
  y1: number;
  lon: number;
  lat: number;
  radius: number;
  path: [number, number][];
  /** cumulative length along the path, 0..1 */
  along: number[];
  /** fixed particle positions (lon, lat) and seeds */
  pts: [number, number, number][];
  /** place among its event's moves, 0..1 (they set off one after another) */
  order: number;
};

/** years an effect stays on screen after it ended, by kind: a fire smoulders, a march is over */
const HOLD: Record<Kind, number> = {fire: 0.35, explosion: 0.2, move: 0.25, clash: 0.25, fleet: 0.25, collapse: 0.3};
/** ... and before it starts (a stop of the tour is rarely set to the very day) */
const BEFORE = 0.08;

const SIDE: Record<string, [number, number, number]> = {
  american: [44, 92, 172],
  union: [44, 70, 140],
  british: [200, 44, 44],
  english: [200, 44, 44],
  hessian: [36, 112, 66],
  dutch: [228, 132, 24],
  french: [236, 236, 236],
  lenape: [124, 84, 44],
  mob: [84, 84, 84],
  police: [30, 34, 84]
};
const sideColor = (s: string): [number, number, number] => SIDE[s] ?? [70, 70, 70];

const num = (v: string | undefined, d: number) => (v !== undefined && v !== '' && Number.isFinite(+v) ? +v : d);
const KX = 84_400; // metres per degree of longitude at 40.7 N
const KY = 110_574;

function rnd(seed: number) {
  let x = (seed | 0) + 0x6d2b79f5;
  return () => {
    x = Math.imul(x ^ (x >>> 15), x | 1);
    x ^= x + Math.imul(x ^ (x >>> 7), x | 61);
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
}

function inside(p: [number, number][], x: number, y: number): boolean {
  let c = false;
  for (let i = 0, j = p.length - 1; i < p.length; j = i++) {
    if (p[i][1] > y !== p[j][1] > y && x < ((p[j][0] - p[i][0]) * (y - p[i][1])) / (p[j][1] - p[i][1]) + p[i][0]) c = !c;
  }
  return c;
}

function parse(): Effect[] {
  const rows = Object.values(files).flatMap(t => parseCsv(t));
  const out: Effect[] = [];
  const byEvent = new Map<string, Effect[]>();
  rows.forEach((r, k) => {
    const kind = (r.kind ?? '').trim() as Kind;
    if (!(kind in HOLD)) return;
    const path = (r.path ?? '')
      .split(';')
      .map(q => q.trim().split(/\s+/).map(Number))
      .filter(q => q.length >= 2 && Number.isFinite(q[0]) && Number.isFinite(q[1]))
      .map(q => [q[0], q[1]] as [number, number]);
    const y0 = num(r.year, NaN);
    if (!Number.isFinite(y0)) return;
    let lon = num(r.lon, NaN);
    let lat = num(r.lat, NaN);
    if ((!Number.isFinite(lon) || !Number.isFinite(lat)) && path.length) [lon, lat] = path[0];
    if (!Number.isFinite(lon) || !Number.isFinite(lat)) return;
    const radius = Math.max(15, num(r.radius_m, kind === 'explosion' ? 250 : 120));
    const rand = rnd(k * 7919 + 13);
    // where the particles stand: inside the burned area's ring, else inside the circle
    const pts: [number, number, number][] = [];
    const ring = kind === 'fire' && path.length >= 3 ? path : null;
    let area = Math.PI * radius * radius;
    let bx0 = lon - radius / KX, bx1 = lon + radius / KX, by0 = lat - radius / KY, by1 = lat + radius / KY;
    if (ring) {
      bx0 = Math.min(...ring.map(q => q[0])); bx1 = Math.max(...ring.map(q => q[0]));
      by0 = Math.min(...ring.map(q => q[1])); by1 = Math.max(...ring.map(q => q[1]));
      area = (bx1 - bx0) * KX * (by1 - by0) * KY * 0.6;
    }
    const want = kind === 'fire' ? Math.max(24, Math.min(420, Math.round(area / 650))) : kind === 'clash' ? 22 : kind === 'collapse' ? 30 : 0;
    for (let tries = 0; pts.length < want && tries < want * 12; tries++) {
      const x = bx0 + rand() * (bx1 - bx0);
      const y = by0 + rand() * (by1 - by0);
      if (ring ? !inside(ring, x, y) : Math.hypot((x - lon) * KX, (y - lat) * KY) > radius) continue;
      pts.push([x, y, rand()]);
    }
    // the route's running length
    const along = [0];
    for (let i = 1; i < path.length; i++) {
      along.push(along[i - 1] + Math.hypot((path[i][0] - path[i - 1][0]) * KX, (path[i][1] - path[i - 1][1]) * KY));
    }
    const total = along[along.length - 1] || 1;
    const e: Effect = {id: r.id ?? `e${k}`, kind, side: (r.side ?? '').trim().toLowerCase(), y0, y1: Math.max(y0, num(r.year_end, y0)), lon, lat, radius, path,
      along: along.map(a => a / total), pts, order: 0};
    if ((kind === 'move' || kind === 'fleet') && path.length < 2) return;
    out.push(e);
    const ev = (r.event ?? '').trim() || e.id;
    if (!byEvent.has(ev)) byEvent.set(ev, []);
    byEvent.get(ev)!.push(e);
  });
  // the moves of one event set off in the order of their dates
  for (const list of byEvent.values()) {
    const mv = list.filter(e => e.kind === 'move' || e.kind === 'fleet').sort((a, b) => a.y0 - b.y0);
    mv.forEach((e, i) => (e.order = mv.length > 1 ? i / mv.length : 0));
  }
  return out;
}

const EFFECTS = parse();
const on = (e: Effect, year: number) => year >= e.y0 - BEFORE && year <= e.y1 + HOLD[e.kind];

/** Is anything to animate at this year? (cheap: called every frame) */
export function effectsActive(year: number): boolean {
  for (const e of EFFECTS) if (on(e, year)) return true;
  return false;
}

function pointAlong(e: Effect, f: number): [number, number] {
  const a = e.along;
  let i = 1;
  while (i < a.length - 1 && a[i] < f) i++;
  const t = a[i] > a[i - 1] ? (f - a[i - 1]) / (a[i] - a[i - 1]) : 0;
  const p = e.path[i - 1], q = e.path[i];
  return [p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t];
}

type Dot = {p: [number, number, number]; r: number; c: [number, number, number, number]};
type Line = {path: [number, number, number][]; c: [number, number, number, number]; w: number};

/** The layers of the effects standing at `year`, at wall-clock time `t` (ms). */
export function effectLayers(year: number, t: number): Layer[] {
  const dots: Dot[] = [];
  const lines: Line[] = [];
  const rings: Dot[] = [];
  const s = t / 1000;
  for (const e of EFFECTS) {
    if (!on(e, year)) continue;
    const z0 = elevationAt(e.lon, e.lat);
    // how far the event has burnt down: 1 while it happens, fading over its hold
    const fade = year <= e.y1 ? 1 : Math.max(0, 1 - (year - e.y1) / HOLD[e.kind]);
    if (e.kind === 'fire') {
      for (const [x, y, sd] of e.pts) {
        const ph = (s * (0.55 + sd * 0.5) + sd * 9) % 1;
        const z = elevationAt(x, y);
        if (sd < 0.7 && fade > 0.35) {
          // flame: flickers, rises a little
          const fl = 0.55 + 0.45 * Math.sin(s * (9 + sd * 7) + sd * 40);
          dots.push({p: [x, y, z + 4 + ph * 14], r: 5 + 6 * fl, c: [255, 120 + Math.round(110 * fl * sd), 20, Math.round(215 * fade * (1 - ph * 0.6))]});
        } else {
          // smoke: drifts up and thins
          const g = 70 + Math.round(60 * sd);
          dots.push({p: [x + ph * 0.0004, y, z + 12 + ph * 130], r: 12 + ph * 34, c: [g, g, g, Math.round(150 * (0.35 + 0.65 * fade) * (1 - ph))]});
        }
      }
    } else if (e.kind === 'explosion') {
      const ph = (s * 0.45) % 1;
      rings.push({p: [e.lon, e.lat, z0 + 6], r: e.radius * (0.15 + 0.85 * ph), c: [255, 180, 60, Math.round(230 * (1 - ph) * fade)]});
      dots.push({p: [e.lon, e.lat, z0 + 14], r: e.radius * 0.22 * (1 - ph * 0.5), c: [255, 235, 170, Math.round(240 * (1 - ph) * fade)]});
      dots.push({p: [e.lon, e.lat, z0 + 40 + ph * 160], r: e.radius * (0.2 + 0.35 * ph), c: [90, 90, 90, Math.round(150 * (1 - ph * 0.7) * fade)]});
    } else if (e.kind === 'collapse') {
      for (const [x, y, sd] of e.pts) {
        const ph = (s * 0.3 + sd) % 1;
        const g = 150 + Math.round(60 * sd);
        dots.push({p: [x, y, z0 + 4 + ph * 90 * sd], r: 14 + ph * 46, c: [g, g - 6, g - 14, Math.round(190 * (1 - ph) * fade)]});
      }
    } else if (e.kind === 'clash') {
      for (const [x, y, sd] of e.pts) {
        const ph = (s * (0.5 + sd * 0.6) + sd * 7) % 1;
        const z = elevationAt(x, y);
        if (ph < 0.12) dots.push({p: [x, y, z + 3], r: 4.5, c: [255, 215, 120, Math.round(255 * fade)]}); // the flash
        dots.push({p: [x, y, z + 3 + ph * 16], r: 5 + ph * 15, c: [236, 236, 232, Math.round(170 * (1 - ph) * fade)]}); // powder smoke
      }
    } else {
      // a column or a fleet moving along its route: it sets off after the moves before it,
      // advances, stands a moment at the end and starts again
      const cyc = (s / 9 - e.order * 0.55) % 1;
      const f = Math.max(0, Math.min(1, ((cyc + 1) % 1) / 0.78));
      const col = sideColor(e.side);
      const lift = e.kind === 'fleet' ? 2 : 5;
      const done: [number, number, number][] = [];
      for (let i = 0; i < e.path.length && e.along[i] <= f; i++) done.push([e.path[i][0], e.path[i][1], elevationAt(e.path[i][0], e.path[i][1]) + lift]);
      const head = pointAlong(e, f);
      done.push([head[0], head[1], elevationAt(head[0], head[1]) + lift]);
      const whole = e.path.map(q => [q[0], q[1], elevationAt(q[0], q[1]) + lift - 1] as [number, number, number]);
      lines.push({path: whole, c: [col[0], col[1], col[2], Math.round(60 * fade)], w: 3});
      if (done.length >= 2) lines.push({path: done, c: [col[0], col[1], col[2], Math.round(235 * fade)], w: e.kind === 'fleet' ? 5 : 6});
      // the column itself: blocks strung out behind the head
      const n = e.kind === 'fleet' ? 4 : 6;
      for (let k = 0; k < n; k++) {
        const fk = f - k * 0.035;
        if (fk < 0) break;
        const q = pointAlong(e, fk);
        dots.push({p: [q[0], q[1], elevationAt(q[0], q[1]) + lift + 2], r: e.kind === 'fleet' ? 16 : 9, c: [col[0], col[1], col[2], Math.round(245 * fade)]});
      }
    }
  }
  const params = {depthCompare: 'always', depthWriteEnabled: false} as any;
  const out: Layer[] = [];
  if (lines.length) {
    out.push(
      new PathLayer<Line>({
        id: 'fx-lines',
        data: lines,
        getPath: d => d.path,
        getColor: d => d.c,
        getWidth: d => d.w,
        widthUnits: 'pixels',
        capRounded: true,
        jointRounded: true,
        parameters: params,
        pickable: false
      })
    );
  }
  if (rings.length) {
    out.push(
      new ScatterplotLayer<Dot>({
        id: 'fx-rings',
        data: rings,
        getPosition: d => d.p,
        getRadius: d => d.r,
        getLineColor: d => d.c,
        stroked: true,
        filled: false,
        lineWidthUnits: 'pixels',
        getLineWidth: 4,
        radiusUnits: 'meters',
        parameters: params,
        pickable: false
      })
    );
  }
  if (dots.length) {
    out.push(
      new ScatterplotLayer<Dot>({
        id: 'fx-dots',
        data: dots,
        getPosition: d => d.p,
        getRadius: d => d.r,
        getFillColor: d => d.c,
        radiusUnits: 'meters',
        radiusMinPixels: 1.5,
        billboard: true,
        parameters: params,
        pickable: false
      })
    );
  }
  return out;
}
