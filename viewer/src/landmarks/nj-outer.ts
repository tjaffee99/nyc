/**
 * New Jersey landmarks outside the core: Trenton, Princeton, Rutgers, Morristown, the
 * shore's lighthouses, Lakehurst, Menlo Park, Asbury Park and High Point.
 * Research: data/research/landmarks_nj_outer.md.
 *
 * Conventions: the anchor is a point on the building; plans are the real outline taken from
 * Overture's building footprints (OpenStreetMap, ODbL) of `outer_building.parquet`, re-expressed
 * in anchor-local metres (x east, y north). Heights are cited figures where the research note
 * gives one, otherwise estimates named in each model's `Model:` fact.
 */
import {MeshBuilder, circle, rect, rotRect, lngLatToLocal, type V2, type V3} from './kit';
import type {Landmark} from './types';

const WIKI = 'https://en.wikipedia.org/wiki/';
const OSM = 'https://www.openstreetmap.org/';
const OVERTURE = 'https://docs.overturemaps.org/guides/buildings/';

export const NJ_OUTER: Landmark[] = [];

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

/** Ring scaled about its vertex mean. */
function scaled(r: V2[], f: number): V2[] {
  const [cx, cy] = centroid(r);
  return r.map(([x, y]) => [cx + (x - cx) * f, cy + (y - cy) * f] as V2);
}

/** Smallest oriented rectangle: centre, long-axis bearing (deg from north), length, width. */
function obb(r: V2[]) {
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
      // the long axis direction in x/y, as a compass bearing
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

/** n points of a star-shaped ring at equal angles about its vertex mean (farthest crossing). */
function radial(r: V2[], n: number): V2[] {
  const [cx, cy] = centroid(r);
  const out: V2[] = [];
  for (let i = 0; i < n; i++) {
    const t = (i / n) * Math.PI * 2;
    const dx = Math.cos(t);
    const dy = Math.sin(t);
    let best = 0;
    for (let k = 0; k < r.length; k++) {
      const a = r[k];
      const c = r[(k + 1) % r.length];
      const ex = c[0] - a[0];
      const ey = c[1] - a[1];
      const den = dx * ey - dy * ex;
      if (Math.abs(den) < 1e-9) continue;
      const tt = ((a[0] - cx) * ey - (a[1] - cy) * ex) / den;
      const uu = ((a[0] - cx) * dy - (a[1] - cy) * dx) / den;
      if (tt > 0 && uu >= 0 && uu <= 1) best = Math.max(best, tt);
    }
    out.push([cx + dx * best, cy + dy * best]);
  }
  return out;
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

/** Offset along an oriented box's long axis (between s0 and s1) where the ring is deepest. */
function deepest(r: V2[], o: {cx: number; cy: number; bearing: number}, s0: number, s1: number): number {
  const a = (-o.bearing * Math.PI) / 180;
  let best = s0;
  let bd = -Infinity;
  for (let s = s0; s <= s1; s += 0.5) {
    const d = clearance(r, o.cx - Math.sin(a) * s, o.cy + Math.cos(a) * s);
    if (d > bd) {
      bd = d;
      best = s;
    }
  }
  return best;
}

/** Ring walls + flat roof. */
function block(b: MeshBuilder, ring: V2[], z0: number, z1: number, wall: string, roof = wall) {
  b.color(wall).walls(ring, z0, z1);
  b.color(roof).cap(ring, z1);
}

/** Tapered shaft on a regular polygon. */
function shaft(b: MeshBuilder, cx: number, cy: number, r0: number, r1: number, z0: number, z1: number, segs: number, rot = 0) {
  const ring = (r: number) => circle(cx, cy, r, segs).map(([x, y]) => {
    const dx = x - cx;
    const dy = y - cy;
    const c = Math.cos(rot);
    const s = Math.sin(rot);
    return [cx + dx * c - dy * s, cy + dx * s + dy * c] as V2;
  });
  b.loft([ring(r0), ring(r1)], [z0, z1], {top: false});
}

/** Hipped roof over a rectangle given by its oriented frame. */
function hippedOver(b: MeshBuilder, cx: number, cy: number, W: number, L: number, bearing: number, z0: number, h: number, color: string) {
  b.color(color).frame(cx, cy, 0, bearing, () => b.hip(0, 0, W, L, z0, h));
}

// ====================================================================== State House, Trenton
// Anchor: the dome (Wikipedia 40.220437 N, 74.769902 W). Plan: Overture footprint
// ff03393a (OSM way), 7,578 m2.
const STATE_HOUSE = P(
  -20.9, 47.9, -33.3, 52.2, -40.1, 33.3, -34.5, 31.3, -43.8, 5.1, -39.7, 3.7, -40.4, 1.7, -45.0, 3.3, -58.1, -33.3, -53.2, -35.0, -53.7, -36.4,
  -41.3, -40.8, -40.8, -39.4, -35.1, -41.4, -39.3, -52.9, -52.0, -48.4, -59.3, -68.8, -2.2, -89.0, 4.9, -69.5, -2.7, -66.8, 22.0, 1.9, 20.6, 2.4,
  21.4, 4.8, 16.1, 6.7, 15.5, 5.0, 9.0, 7.2, 10.9, 12.5, 0.7, 16.0, 2.1, 19.7, 11.2, 16.5, 10.7, 15.1, 19.2, 12.2, 19.6, 13.4, 32.1, 9.1, 38.4, 27.1,
  26.4, 31.2, 26.8, 32.6, 16.9, 36.0, 16.6, 35.0, 10.2, 37.2, 10.7, 38.6, -3.8, 43.6, -4.3, 42.1, -11.0, 44.4, -10.5, 45.5, -20.8, 49.1
);
const SH_ANCHOR: V2 = [-74.7699, 40.2204];

NJ_OUTER.push({
  id: 'nj_state_house_1792',
  name: 'New Jersey State House (1792 building)',
  kind: 'building',
  built: [1792, 1793],
  end: 1885.2,
  anchor: SH_ANCHOR,
  build: b => {
    // 150 x 50 ft = 45.7 x 15.2 m stuccoed block (Wikipedia). Placement and orientation: under
    // the present central pavilion, long axis parallel to the main street front (bearing 110°).
    b.frame(0, 0, 0, 110, () => {
      b.color('#D9CDB4').box(0, 0, 0, 15.2, 45.7, 9.5);
      b.color('#7A5A48').hip(0, 0, 15.2, 45.7, 9.5, 3.5);
      b.color('#E8E2D2').box(0, 0, 13, 3.4, 3.4, 3.2);
      b.color('#7A5A48').pyramid(rect(0, 0, 3.4, 3.4), 16.2, [0, 0, 18.5]);
    });
  },
  facts: {
    Built: 'begun 1792 to a design by Jonathan Doane; 150 x 50 ft (46 x 15 m), stucco',
    Later: 'John Notman added a rotunda, dome and cupola in 1845; fire of 21 March 1885; the present rotunda and dome date from 1889 (see the next model)',
    Model: 'the 150 x 50 ft size is cited; the storey height (9.5 m eaves), roof, cupola and the block\'s position and orientation within today\'s footprint are estimated; the 1845 additions are not modelled'
  },
  sources: [WIKI + 'New_Jersey_State_House']
});

NJ_OUTER.push({
  id: 'nj_state_house',
  name: 'New Jersey State House',
  kind: 'building',
  built: [1885.2, 1889.5],
  end: 9999,
  anchor: SH_ANCHOR,
  build: b => {
    block(b, STATE_HOUSE, 0, 14, '#CFC6B0', '#8A8478');
    // drum, dome and lantern: the dome is 145 ft (44 m) high (Wikipedia); copper over cast iron, gilded
    b.color('#CFC6B0').cylinder(0, 0, 8.6, 14, 23, 20);
    b.color('#9CA89A').frustum(0, 0, 9.0, 8.6, 23, 24, 20, false);
    b.color('#D8B24A').dome(0, 0, 8.6, 24, 11, 20, 6);
    b.color('#D8B24A').cylinder(0, 0, 1.8, 35, 40.2, 8);
    b.color('#D8B24A').pyramid(circle(0, 0, 1.8, 8), 40.2, [0, 0, 44.2]);
  },
  replaces: [STATE_HOUSE],
  facts: {
    Dome: '145 ft (44 m), cast iron covered with copper and gold leaf; rotunda and dome by Lewis Broome, 1889',
    Wings: 'Moylan 1891, Moses 1903, east wing and extensions 1906-1912; the oldest state house in use after Maryland\'s and Annapolis\' (see article)',
    Model: 'plan is the real outline (OpenStreetMap via Overture); dome height cited; the wings\' eave height (14 m), the drum and the dome\'s profile are estimated; all wings are drawn from 1885 although they were added in stages to 1912'
  },
  sources: [WIKI + 'New_Jersey_State_House', OSM + 'way/ (Overture ff03393a)']
});

// ====================================================================== Old Barracks, Trenton
const BARRACKS = P(-19.2, -0.1, -3.4, -4.3, -1.6, 2.4, -10.8, 4.8, -3.7, 31.7, 19.5, 25.6, 21.7, 34.0, 9.3, 37.3, 8.9, 36.0, -8.4, 40.5);
NJ_OUTER.push({
  id: 'nj_old_barracks',
  name: 'Old Barracks, Trenton',
  kind: 'building',
  built: [1758, 1759.5],
  end: 9999,
  anchor: [-74.76861, 40.21972],
  build: b => {
    block(b, BARRACKS, 0, 8.4, '#9C9384', '#6E6258');
  },
  replaces: [BARRACKS],
  facts: {
    Built: '1758, stone, Georgian, a U-shaped barracks for about 300 soldiers',
    Model: 'U-shaped plan is the real outline; the height (8.4 m to a flat-drawn roof; the Overture/OpenStreetMap height is 7.7 m) and the roof form are estimated'
  },
  sources: [WIKI + 'Old_Barracks_Museum', OVERTURE]
});

// ====================================================================== Trenton Battle Monument
NJ_OUTER.push({
  id: 'nj_trenton_battle_monument',
  name: 'Trenton Battle Monument',
  kind: 'monument',
  built: [1891.99, 1893.8],
  end: 9999,
  anchor: [-74.76472, 40.22583],
  build: b => {
    // square base from the Overture outline (9.1 x 9.0 m), centred (-5.1, 2.0)
    b.color('#8F8A82').box(-5.1, 2.0, 0, 9.2, 9.0, 1.2);
    b.color('#A29C92').box(-5.1, 2.0, 1.2, 6.6, 6.6, 4.0);
    // fluted granite column to the statue (total 150 ft = 45.7 m including the 13 ft statue)
    b.color('#B7B0A4');
    shaft(b, -5.1, 2.0, 2.3, 1.6, 5.2, 40.9, 12);
    b.color('#A29C92').cylinder(-5.1, 2.0, 2.0, 40.9, 41.7, 12);
    // statue of Washington, 13 ft (4.0 m): plinth, figure, head
    b.color('#6F7468');
    b.frustum(-5.1, 2.0, 0.9, 0.7, 41.7, 43.6, 8);
    b.frustum(-5.1, 2.0, 0.55, 0.25, 43.6, 45.2, 8);
    b.frustum(-5.1, 2.0, 0.25, 0.01, 45.2, 45.72, 8);
  },
  facts: {
    Built: 'cornerstone 26 December 1891; capstone raised 31 August 1893; statue placed 5 September 1893; dedicated 19 October 1893',
    Height: '150 ft (46 m) above street level including the 13 ft (4.0 m) bronze statue of Washington',
    Model: 'height cited; the base is the real 9 m square outline, the column\'s taper (4.6 m to 3.2 m across), the pedestal stages and the statue\'s silhouette are estimated'
  },
  sources: [WIKI + 'Trenton_Battle_Monument', OVERTURE]
});

// ====================================================================== Lower Trenton Bridge
{
  const A: V2 = [-74.7683, 40.2105];
  const w0 = lngLatToLocal(A, [-74.77033, 40.21024]); // Trenton Makes bridge, west (Pennsylvania) end of the OSM outline
  const e0 = lngLatToLocal(A, [-74.76621, 40.21069]); // east (New Jersey) end
  NJ_OUTER.push({
    id: 'nj_lower_trenton_bridge',
    name: 'Lower Trenton Bridge ("Trenton Makes")',
    kind: 'bridge',
    built: [1927, 1928.9],
    end: 9999,
    anchor: A,
    build: b => {
      const dx = e0[0] - w0[0];
      const dy = e0[1] - w0[1];
      const L = Math.hypot(dx, dy);
      const bearing = (Math.atan2(dx, dy) * 180) / Math.PI;
      const mid = [(w0[0] + e0[0]) / 2, (w0[1] + e0[1]) / 2];
      const n = 6; // spans: estimated (the article gives only the 1,022 ft length)
      const span = L / n;
      const W = 10.8; // deck outline width from the OSM way
      b.frame(mid[0], mid[1], 0, bearing, () => {
        // deck, 4 m above the river's surface (estimated)
        b.color('#6F7A82').box(0, 0, 3.4, W, L, 0.9);
        // piers
        b.color('#9A968C');
        for (let i = 1; i < n; i++) b.box(0, -L / 2 + i * span, 0, 4.0, 1.6, 3.4);
        // through trusses, 7 m deep, one each side
        for (const s of [-1, 1]) {
          const x = s * (W / 2 - 0.3);
          b.color('#5E666B');
          for (let i = 0; i < n; i++) {
            const y0 = -L / 2 + i * span;
          const y1 = y0 + span;
            const top = (y: number): V3 => [x, y, 4.3 + 7.0];
            b.beam([x, y0, 4.3], [x, y1, 4.3], 0.5, 0.7);
            b.beam(top(y0 + 3), top(y1 - 3), 0.5, 0.7);
            b.beam([x, y0, 4.3], top(y0 + 3), 0.4);
            b.beam([x, y1, 4.3], top(y1 - 3), 0.4);
            b.beam([x, y0, 4.3], [x, (y0 + y1) / 2, 11.3], 0.3);
            b.beam([x, y1, 4.3], [x, (y0 + y1) / 2, 11.3], 0.3);
          }
        }
        // portal bracing
        b.color('#5E666B');
        for (const y of [-L / 2 + 1, L / 2 - 1]) b.beam([-W / 2 + 0.3, y, 11.3], [W / 2 - 0.3, y, 11.3], 0.4);
        // "TRENTON MAKES THE WORLD TAKES" sign on the south truss: a board of letters 2.2 m high
        b.color('#E8E4D8').box(-(W / 2 - 0.1), 0, 8.2, 0.3, 58, 2.4);
      });
    },
    facts: {
      Opened: '30 November 1928, replacing the 1806 bridge (rebuilt 1875, 1876, 1892, 1898)',
      Type: 'two-lane Pennsylvania (Petit) through truss, 1,022 ft (312 m) long, over the Delaware River',
      Sign: '"Trenton Makes, The World Takes" in large letters on the south side',
      Model: 'deck outline and alignment are the OpenStreetMap way 561300664 (ODbL); the length matches the cited 312 m; the 6 spans, the truss depth (7 m), the deck height above water and the sign\'s size and side are estimated; the 1806 bridge is not modelled'
    },
    sources: [WIKI + 'Lower_Trenton_Bridge', OSM + 'way/561300664']
  });
}

// ====================================================================== War Memorial, Trenton
const WAR_MEMORIAL = P(40.0, -32.7, 52.1, 6.7, 36.1, 11.5, 35.5, 9.4, -9.5, 23.0, -8.7, 25.6, -21.1, 29.4, -33.3, -10.3, -20.9, -14.0, -20.1, -11.3, 25.5, -25.1, 24.6, -28.0);
NJ_OUTER.push({
  id: 'nj_trenton_war_memorial',
  name: 'Trenton War Memorial (Patriots Theater)',
  kind: 'building',
  built: [1930, 1932.4],
  end: 9999,
  anchor: [-74.76833, 40.21833],
  build: b => {
    block(b, WAR_MEMORIAL, 0, 14.5, '#D9D1BC', '#8F887A');
    // stage house, over the western third
    const o = obb(WAR_MEMORIAL);
    b.color('#CFC7B0').frame(o.cx, o.cy, 0, o.bearing, () => {
      b.box(0, deepest(WAR_MEMORIAL, o, 0, 0.35 * o.L), 14.5, o.W * 0.5, o.L * 0.3, 6.5);
    });
    b.color('#B8AF98').cap(scaled(WAR_MEMORIAL, 0.92), 14.9);
  },
  replaces: [WAR_MEMORIAL],
  facts: {
    Built: '1930-1932 (opened 1932), by Louis S. Kaplan; buff Indiana limestone; Italian Renaissance Revival with Art Deco; Patriots Theater of 1,833 seats',
    Model: 'plan is the real outline; the heights (cornice 14.5 m, stage house 21 m) and the stage house\'s position are estimated (OpenStreetMap lists 9.8 m)'
  },
  sources: [WIKI + 'Trenton_War_Memorial', OVERTURE]
});

// ====================================================================== Nassau Hall, Princeton
const NASSAU = P(
  -21.7, -20.2, -2.2, -13.4, 3.6, -29.8, 17.5, -24.9, 11.7, -8.4, 31.3, -1.5, 29.5, 3.6, 33.1, 4.8, 30.2, 13.0, 26.0, 11.5, 24.7, 15.2, 5.7, 8.5, 5.3, 9.6,
  -7.5, 5.1, -6.9, 3.6, -26.8, -3.4, -24.9, -8.6, -29.3, -10.2, -27.1, -16.3, -23.5, -15.0
);
const NASSAU_ANCHOR: V2 = [-74.65935, 40.34874];
{
  const o = obb(NASSAU);
  NJ_OUTER.push({
    id: 'nj_nassau_hall_1756',
    name: 'Nassau Hall (original building)',
    kind: 'building',
    built: [1754, 1756.7],
    end: 1855.2,
    anchor: NASSAU_ANCHOR,
    build: b => {
      // the original hall: 176 x 54 ft (53.6 x 16.5 m) [from memory, not re-read]; centred on the long block of today's plan
      const L = 53.6;
      const W = 16.5;
      const ring = rotRect(o.cx, o.cy, W, L, o.bearing);
      block(b, ring, 0, 14.5, '#B79E7A', '#6F6A62');
      hippedOver(b, o.cx, o.cy, W, L, o.bearing, 14.5, 3.5, '#5E5B58');
      b.color('#E6E1D2').frame(o.cx, o.cy, 0, o.bearing, () => {
        b.box(0, 0, 18, 3.4, 3.4, 3.2);
      });
      b.color('#5E5B58').pyramid(rotRect(o.cx, o.cy, 3.4, 3.4, o.bearing), 21.2, [o.cx, o.cy, 24]);
    },
    facts: {
      Built: 'begun 1754, finished 1756; the largest academic building in colonial America. Gutted by fire on 6 March 1802 (rebuilt under B. H. Latrobe) and again in March 1855',
      Model: 'a brownstone block of three and a half storeys; the size (176 x 54 ft) is recalled and not re-read, the eave height, roof and cupola are estimated; the wings of 1905 are not shown'
    },
    sources: [WIKI + 'Nassau_Hall']
  });
  NJ_OUTER.push({
    id: 'nj_nassau_hall',
    name: 'Nassau Hall',
    kind: 'building',
    built: [1855.2, 1856.4],
    end: 9999,
    anchor: NASSAU_ANCHOR,
    build: b => {
      block(b, NASSAU, 0, 14.5, '#B79E7A', '#6F6A62');
      // hipped roof, cupola and Notman's two towers of 1855, each placed where the outline is deepest
      const sc = deepest(NASSAU, o, -0.15 * o.L, 0.15 * o.L);
      const s1 = deepest(NASSAU, o, 0.2 * o.L, 0.5 * o.L);
      const s2 = deepest(NASSAU, o, -0.5 * o.L, -0.2 * o.L);
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        b.color('#5E5B58').hip(0, sc, 7, 20, 14.5, 2.8);
        b.color('#E6E1D2').box(0, sc, 16.5, 3.4, 3.4, 3.4);
        b.color('#5E5B58').pyramid(rect(0, sc, 3.6, 3.6), 19.9, [0, sc, 23.6]);
        for (const t of [s1, s2]) {
          b.color('#E6E1D2').box(0, t, 14.5, 3.6, 3.6, 4.4);
          b.color('#5E5B58').pyramid(rect(0, t, 3.8, 3.8), 18.9, [0, t, 22]);
        }
      });
    },
    replaces: [NASSAU],
    facts: {
      Rebuilt: 'after the fires of 1802 and 1855; John Notman\'s 1855 reconstruction added the cupola and towers; the Capitol of the United States for four months in 1783',
      Model: 'plan is the real outline (including the 1905 wings); eave height (14.5 m), roof, cupola and tower sizes are estimated (no height is given by the article; OpenStreetMap lists 7.4 m)'
    },
    sources: [WIKI + 'Nassau_Hall', OVERTURE]
  });
}

// ====================================================================== University Chapel, Princeton
const CHAPEL = P(
  -15.6, 3.4, -48.0, -11.6, -40.3, -28.3, -39.2, -30.4, -0.5, -12.5, 1.7, -17.3, 21.4, -8.1, 18.3, -1.5, 31.6, 4.6, 25.3, 18.3, 12.5, 12.4, 11.6, 14.3,
  8.7, 12.8, 7.3, 16.0, 4.6, 17.2, 4.0, 16.9, 2.6, 17.8, 0.7, 17.6, 0.2, 15.6, -9.6, 11.1, -11.3, 11.8, -13.0, 11.1, -13.6, 9.3, -17.4, 7.7
);
NJ_OUTER.push({
  id: 'nj_princeton_chapel',
  name: 'Princeton University Chapel',
  kind: 'building',
  built: [1924.5, 1928.4],
  end: 9999,
  anchor: [-74.656889, 40.348889],
  build: b => {
    const o = obb(CHAPEL);
    block(b, CHAPEL, 0, 19, '#A89A80', '#6F6A5E');
    // nave roof: ridge 121 ft = 36.9 m above the ground (Wikipedia, exterior height); no tower
    const W = 13.5;
    b.color('#6F7468').frame(o.cx, o.cy, 0, o.bearing, () => {
      b.gable(0, 0, W, o.L * 0.96, 19, 17.9, true);
      b.box(0, 0, 0, W - 0.2, o.L * 0.96, 19.02, {top: false});
    });
    // transept roof across the crossing
    b.color('#6F7468').frame(o.cx, o.cy, 0, o.bearing, () => {
      b.gable(o.L * 0.07, 0, 11, 23, 19, 9, false);
    });
  },
  replaces: [CHAPEL],
  facts: {
    Dedicated: '31 May 1928 (groundbreaking 1924, cornerstone 1925), Ralph Adams Cram; Collegiate Gothic in Pennsylvania sandstone with Indiana limestone trim; almost 2,000 seats',
    Size: '277 ft (84 m) long, 76 ft (23 m) across the transepts, 121 ft (37 m) high; its crossing carries no tower',
    Model: 'plan is the real outline; length, height and the absence of a tower are cited; the aisle wall height (19 m), nave width (13.5 m) and the transept roof are estimated'
  },
  sources: [WIKI + 'Princeton_University_Chapel', OVERTURE]
});

// ====================================================================== Cleveland Tower, Princeton
NJ_OUTER.push({
  id: 'nj_cleveland_tower',
  name: 'Cleveland Tower (Graduate College)',
  kind: 'tower',
  built: [1911, 1913.4],
  end: 9999,
  anchor: [-74.664627, 40.3405974],
  build: b => {
    // 173 ft = 52.7 m (Princeton Graduate College history page). Plan 9 m square (estimated), aligned
    // with the east wall of the Old Graduate College outline (bearing 336.5°).
    b.frame(0, 0, 0, 336.5, () => {
      b.color('#B5A88F').box(0, 0, 0, 9.4, 9.4, 8);
      b.color('#B8AC93').box(0, 0, 8, 8.6, 8.6, 27);
      b.color('#A89B82').box(0, 0, 35, 9.0, 9.0, 1.0);
      b.color('#B8AC93').box(0, 0, 36, 7.4, 7.4, 8.4);
      for (const s of [-1, 1]) {
        b.box(s * 3.9, 0, 36, 1.4, 7.4, 11.5);
        b.box(0, s * 3.9, 36, 7.4, 1.4, 11.5);
      }
      b.color('#9C9078').box(0, 0, 44.4, 8.0, 8.0, 0.8);
      b.color('#6F7468').pyramid(rect(0, 0, 7.4, 7.4), 45.2, [0, 0, 52.7]);
    });
  },
  facts: {
    Height: '173 ft (52.7 m); memorial to Grover Cleveland by Ralph Adams Cram, dedicated with the Graduate College in 1913',
    Bells: 'Class of 1892 Bells, 67 bells (the carillon was installed in the 1920s)',
    Model: 'height cited; position from OpenStreetMap node 367681826; the 9 m square plan, the stages and the roof are estimated'
  },
  sources: [WIKI + 'Cleveland_Tower', 'https://www.princeton.edu/~gradcol/perm/hist.htm', OSM + 'node/367681826']
});

// ====================================================================== Blair Hall and Arch, Princeton
const BLAIR = P(-39.3, 11.9, -49.9, 7.6, -33.9, -21.6, 35.2, 5.0, 37.5, 4.3, 38.7, 5.4, 42.5, 3.8, 48.5, 17.2, 44.7, 18.8, 44.4, 20.9, 42.6, 21.6, 40.3, 20.9, 39.5, 18.7, -28.2, -7.1);
NJ_OUTER.push({
  id: 'nj_blair_hall',
  name: 'Blair Hall and Blair Arch',
  kind: 'building',
  built: [1896, 1897.8],
  end: 9999,
  anchor: [-74.66148, 40.34745],
  build: b => {
    block(b, BLAIR, 0, 14.5, '#A89B82', '#6F6A5E');
    // tower over the arch: 26.8 m top (OpenStreetMap), position estimated at the middle of the long block
    b.color('#B0A38A').frame(-5, -2, 0, 5, () => {
      b.box(0, 0, 14.5, 9, 9, 8.8);
      b.color('#6F7468').pyramid(rect(0, 0, 9.2, 9.2), 23.3, [0, 0, 26.8]);
    });
    // the arch itself is a dark opening: a slab suggesting the portal on the south face
    b.color('#2F2C28').frame(-5, -2, 0, 5, () => b.box(0, -4.6, 0, 4.6, 0.3, 7));
  },
  replaces: [BLAIR],
  facts: {
    Built: '1897, by Cope & Stewardson; Collegiate Gothic dormitory with Blair Arch and its tower',
    Model: 'plan is the real outline (Overture, 1,287 m2); the tower\'s top (26.8 m) is the OpenStreetMap height; the eave height (14.5 m), the tower\'s plan (9 m) and its position along the building are estimated; the construction years are from memory and not re-read'
  },
  sources: [OVERTURE, OSM]
});

// ====================================================================== Princeton Stadium
const STADIUM = P(
  -63.1, 75.3, -58.8, 58.9, -62.8, 57.1, -72.0, 34.3, -70.1, 29.7, -84.6, 21.0, -41.5, -78.9, -24.5, -75.2, -23.2, -77.6, 0.6, -86.3, 70.0, -55.8,
  80.0, -33.2, 78.7, -30.4, 93.5, -20.5, 50.0, 78.6, 32.8, 75.1, 31.1, 78.4, 8.3, 87.6, 3.6, 86.3, -4.8, 100.2
);
// the playing field: the footprint's courtyard (Overture interior ring)
const STADIUM_FIELD = P(2.0, -64.5, -7.5, -59.4, -49.6, 35.4, -45.3, 43.4, 8.2, 66.7, 17.3, 63.1, 59.2, -33.5, 56.5, -41.0);
NJ_OUTER.push({
  id: 'nj_princeton_stadium',
  name: 'Princeton Stadium',
  kind: 'stadium',
  built: [1996.8, 1998.7],
  end: 9999,
  anchor: [-74.65003, 40.345755],
  build: b => {
    // outer wall at the OSM height 15.5 m; the seating rakes from the field's edge (1 m) to the rim
    const N = 48;
    const lo = radial(STADIUM_FIELD, N).map(([x, y]) => [x, y, 1.0] as V3);
    const hi = radial(STADIUM, N).map(([x, y]) => [x, y, 14.5] as V3);
    b.color('#8A8F93').ribbon(lo, hi, true);
    b.color('#D07A2C').walls(STADIUM, 0, 15.5);
    b.color('#D07A2C').ribbon(hi, hi.map(([x, y]) => [x, y, 15.5] as V3), true);
    b.color('#6B7B4E').cap(STADIUM_FIELD, 0.6);
  },
  replaces: [STADIUM],
  facts: {
    Opened: '19 September 1998 on the site of Palmer Stadium (1914-1996); 27,800 seats; the grandstands are four-sided',
    Model: 'outline and the field are the real ones (Overture: 21,905 m2 outer ring, 8,398 m2 field); the wall height is OpenStreetMap\'s 15.5 m; the rake of the seating (1 m at the field to 14.5 m at the rim) is estimated; Palmer Stadium is not modelled'
  },
  sources: [WIKI + 'Princeton_Stadium', OVERTURE]
});

// ====================================================================== Old Queens, Rutgers
const OLD_QUEENS = P(-17.9, -6.9, -15.1, -13.7, -8.3, -11.0, -8.7, -10.0, 11.7, -1.7, 12.2, -2.9, 18.7, -0.3, 12.1, 15.8, 5.7, 13.1, 6.0, 12.4, -14.3, 4.2, -14.7, 5.0, -21.2, 2.3, -18.7, -3.9, -20.3, -4.5, -19.1, -7.4);
NJ_OUTER.push({
  id: 'nj_old_queens',
  name: 'Old Queens, Rutgers',
  kind: 'building',
  built: [1809, 1825.5],
  end: 9999,
  anchor: [-74.44625, 40.49875],
  build: b => {
    const o = obb(OLD_QUEENS);
    block(b, OLD_QUEENS, 0, 12, '#A0583F', '#6E6860');
    hippedOver(b, o.cx, o.cy, o.W * 0.7, o.L * 0.75, o.bearing, 12, 3.2, '#4E4A48');
    // cupola of 1825
    b.color('#EDEAE0').frame(o.cx, o.cy, 0, o.bearing, () => {
      b.box(0, 0, 13.5, 3.6, 3.6, 3.4);
    });
    b.color('#4E4A48').pyramid(rotRect(o.cx, o.cy, 3.8, 3.8, o.bearing), 16.9, [o.cx, o.cy, 20.6]);
  },
  replaces: [OLD_QUEENS],
  facts: {
    Built: 'cornerstone 1809, completed 1825 (cupola raised 1825); John McComb Jr.; Federal style, brownstone and brick',
    Model: 'plan is the real outline (Overture, 584 m2); heights (eaves 12 m, cupola top 20.6 m) and the roof are estimated (the article gives none; OpenStreetMap lists 9.6 m); the pitch of the roof and the cupola are drawn from photographs of the Federal type'
  },
  sources: [WIKI + 'Old_Queens', OVERTURE]
});

// ====================================================================== Ford Mansion, Morristown
const FORD = P(10.0, 3.1, -16.6, -3.6, -13.7, -15.0, -6.2, -13.1, -5.8, -14.6, -2.6, -13.8, -3.1, -12.2, 3.8, -10.5, 3.1, -8.0, 12.3, -5.7);
NJ_OUTER.push({
  id: 'nj_ford_mansion',
  name: 'Ford Mansion (Washington\'s Headquarters)',
  kind: 'building',
  built: [1773, 1774.8],
  end: 9999,
  anchor: [-74.4667, 40.7964],
  build: b => {
    const o = obb(FORD);
    block(b, FORD, 0, 7.4, '#EDE9DC', '#5F4B42');
    // hipped roof on the main block; chimneys
    const sc = deepest(FORD, o, -0.2 * o.L, 0.2 * o.L);
    b.color('#5F4B42').frame(o.cx, o.cy, 0, o.bearing, () => b.hip(0, sc, o.W * 0.6, o.L * 0.55, 7.4, 2.6));
    b.color('#8E5A47').frame(o.cx, o.cy, 0, o.bearing, () => {
      for (const s of [-1, 1]) b.box(s * o.W * 0.28, o.L * 0.3, 7.4, 1.0, 1.0, 4.4);
      for (const s of [-1, 1]) b.box(s * o.W * 0.28, -o.L * 0.3, 7.4, 1.0, 1.0, 4.4);
    });
  },
  replaces: [FORD],
  facts: {
    Built: '1774 by Jacob Ford Jr.; Georgian, painted wood siding; Washington\'s headquarters from December 1779 to June 1780',
    Model: 'plan is the real outline (Overture, 303 m2); heights (eaves 7.4 m, roof 3.2 m) and chimneys are estimated; the construction start (1773) is estimated, only 1774 is cited'
  },
  sources: [WIKI + 'Ford_Mansion', OVERTURE]
});

// ====================================================================== Sandy Hook Light
NJ_OUTER.push({
  id: 'nj_sandy_hook_light',
  name: 'Sandy Hook Light',
  kind: 'tower',
  built: [1763, 1764.45],
  end: 9999,
  anchor: [-74.002, 40.4617],
  build: b => {
    // octagonal rubble tower, centred (-2.0, 2.9) on the OSM outline (9.6 m across at the foot)
    const cx = -2.0;
    const cy = 2.9;
    b.color('#CFC9B8');
    shaft(b, cx, cy, 4.9, 3.0, 0, 25.4, 8, Math.PI / 8);
    b.color('#2B2E30').frustum(cx, cy, 3.4, 3.4, 25.4, 26.0, 8, true);
    // lantern, 31.4 m (103 ft) to the top
    b.color('#2B2E30').cylinder(cx, cy, 2.0, 26.0, 29.0, 8);
    b.color('#8FB3B8').cylinder(cx, cy, 1.85, 26.3, 29.0, 8);
    b.color('#2B2E30').pyramid(circle(cx, cy, 2.3, 8), 29.0, [cx, cy, 31.4]);
  },
  replaces: [circle(-2.0, 2.9, 4.9, 8)],
  facts: {
    Lit: '11 June 1764 (Isaac Conro); the oldest working lighthouse in the United States; national historic landmark 1964',
    Size: 'octagonal stone tower, 103 ft (31 m) tall; focal height 89 ft (27 m)',
    Model: 'height cited; the foot (9.6 m across) is the OpenStreetMap outline; the taper to 6 m at the gallery, the gallery and lantern proportions are estimated; today\'s tower is 1764\'s (not rebuilt), the keeper\'s house is not modelled'
  },
  sources: [WIKI + 'Sandy_Hook_Light', OVERTURE]
});

// ====================================================================== Navesink Twin Lights
const TWIN_QUARTERS = P(
  0.8, 28.9, -0.0, 28.5, -4.5, 37.2, -10.2, 34.4, -3.0, 20.7, 1.5, 11.8, -0.6, 10.8, -1.4, 12.3, -4.0, 10.9, 3.6, -4.0, 6.4, -2.5, 5.6, -0.8, 7.4, 0.1,
  18.9, -22.7, 21.2, -21.5, 20.9, -21.0, 24.4, -19.0, 20.1, -10.7, 20.9, -10.2, 18.1, -4.5, 17.3, -4.9, 13.3, 3.1, 14.5, 3.7, 8.4, 15.8, 6.9, 15.0, 2.7, 23.3, 3.5, 23.6
);
NJ_OUTER.push({
  id: 'nj_twin_lights',
  name: 'Navesink Twin Lights',
  kind: 'tower',
  built: [1861, 1862.9],
  end: 9999,
  anchor: [-73.98578, 40.39622],
  build: b => {
    // keepers' quarters on the real outline, brownstone; towers 73 ft (22.3 m)
    block(b, TWIN_QUARTERS, 0, 8.2, '#9B7B63', '#5D5A56');
    // south tower: square, on the OSM outline "South Tower" (6.6 m)
    const sx = 25.5;
    const sy = -22.1;
    b.color('#A68A72').frame(sx, sy, 0, 30, () => {
      b.box(0, 0, 0, 6.6, 6.6, 20);
    });
    b.color('#2B2E30').frame(sx, sy, 0, 30, () => b.box(0, 0, 20, 7.2, 7.2, 0.6));
    b.color('#2B2E30').cylinder(sx, sy, 1.9, 20.6, 22.25, 8);
    // north tower: octagonal, at the north end of the building (placement estimated)
    const nx = -4.5;
    const ny = 33.5;
    b.color('#A68A72');
    shaft(b, nx, ny, 3.6, 3.2, 0, 20, 8, Math.PI / 8);
    b.color('#2B2E30').frustum(nx, ny, 3.9, 3.9, 20, 20.6, 8);
    b.color('#2B2E30').cylinder(nx, ny, 2.2, 20.6, 22.25, 8);
  },
  replaces: [TWIN_QUARTERS],
  facts: {
    Built: '1862 (Joseph Lederle); non-identical towers, the north octagonal and the south square, joined by the keepers\' quarters, 246 ft (75 m) above the sea on the Navesink Highlands; earlier towers of 1828',
    Model: 'quarters\' outline and the south tower\'s position are real (Overture); the tower height (73 ft, Coast Guard) is cited; the north tower\'s position (the north end of the outline), the sizes of both towers, the quarters\' height (8.2 m) and the lantern are estimated; the start year is estimated'
  },
  sources: [WIKI + 'Navesink_Twin_Lights', 'https://www.history.uscg.mil/Browse-by-Topic/Assets/Land/All/Article/1963532/navesink-twin-lights/', OVERTURE]
});

// ====================================================================== Barnegat Light
NJ_OUTER.push({
  id: 'nj_barnegat_light',
  name: 'Barnegat Lighthouse ("Old Barney")',
  kind: 'tower',
  built: [1857.5, 1859.0],
  end: 9999,
  anchor: [-74.10624, 39.76434],
  build: b => {
    const H = 49.7; // 163 ft
    b.color('#EDEAE0').frustum(0, 0, 4.0, 2.7, 0, 24, 16, false);
    b.color('#B2342A').frustum(0, 0, 2.7, 2.1, 24, 43.5, 16, false);
    b.color('#2B2E30').cylinder(0, 0, 3.4, 43.5, 44.3, 16);
    b.color('#2B2E30').cylinder(0, 0, 2.4, 44.3, 48.1, 12);
    b.color('#9FC0C4').cylinder(0, 0, 2.2, 44.8, 48.1, 12);
    b.color('#B2342A').pyramid(circle(0, 0, 2.6, 12), 48.1, [0, 0, H]);
  },
  replaces: [circle(0, 0, 4, 16)],
  facts: {
    Lit: '1 January 1859 (George G. Meade\'s design; the 1835 tower fell into the sea in 1857); 163 ft (50 m), a first-order Fresnel lens; automated 1927, deactivated 1944, state park 1957; relit 2009',
    Model: 'height cited; the foot (8 m across) is the OpenStreetMap outline; the taper to 5.4 m at the gallery, the proportions of gallery and lantern, and the red-above-white colouring are estimated from photographs; the construction start (1857.5) is estimated'
  },
  sources: [WIKI + 'Barnegat_Lighthouse', OSM + 'way/704069002']
});

// ====================================================================== Hangar No. 1, Lakehurst
const HANGAR1 = P(176.2, -21.1, -33.7, 84.1, -80.5, -8.0, 129.4, -113.2);
NJ_OUTER.push({
  id: 'nj_lakehurst_hangar_1',
  name: 'Hangar No. 1, Lakehurst',
  kind: 'building',
  built: [1919.5, 1921.6],
  end: 9999,
  anchor: [-74.3166, 40.029],
  build: b => {
    // arched steel hangar: an elliptic cross-section 68 m high (224 ft) over the 105 m outline width
    const o = obb(HANGAR1);
    const W = o.W;
    const L = o.L;
    const H = 68.3;
    const zs = 9; // vertical side wall height before the arch springs (estimated)
    const prof: V2[] = [];
    const N = 16;
    for (let i = 0; i <= N; i++) {
      const u = -W / 2 + (W * i) / N;
      const t = (2 * u) / W;
      prof.push([u, zs + (H - zs) * Math.sqrt(Math.max(1 - t * t, 0))]);
    }
    b.color('#A9AEB0').frame(o.cx, o.cy, 0, o.bearing, () => {
      for (let i = 0; i < N; i++) {
        const [u0, z0] = prof[i];
        const [u1, z1] = prof[i + 1];
        b.quad([u0, -L / 2, z0], [u1, -L / 2, z1], [u1, L / 2, z1], [u0, L / 2, z0]);
        b.tri([u0, -L / 2, 0], [u0, -L / 2, z0], [u1, -L / 2, z1]);
      }
      b.color('#8E9396');
      // side walls and end doors
      b.quad([-W / 2, -L / 2, 0], [-W / 2, L / 2, 0], [-W / 2, L / 2, zs], [-W / 2, -L / 2, zs]);
      b.quad([W / 2, -L / 2, 0], [W / 2, L / 2, 0], [W / 2, L / 2, zs], [W / 2, -L / 2, zs]);
      for (const y of [-L / 2, L / 2]) {
        for (let i = 0; i < N; i++) {
          const [u0, z0] = prof[i];
          const [u1, z1] = prof[i + 1];
          b.quad([u0, y, 0], [u1, y, 0], [u1, y, z1], [u0, y, z0]);
        }
      }
    });
  },
  replaces: [HANGAR1],
  facts: {
    Built: '1921, for the Navy\'s airships (Lord Construction Company; trusses by Bethlehem Steel); the Hindenburg\'s destination on 6 May 1937; national historic landmark 1968',
    Size: '966 ft x 350 ft x 224 ft (294 x 110 x 68 m) in the article; the Overture outline is 235 x 105 m',
    Model: 'height cited (matches the 68 m of OpenStreetMap); the plan is the real outline, which is shorter than the cited length; the arch\'s profile (elliptic, springing at 9 m) and the doors are estimated; the start year is estimated'
  },
  sources: [WIKI + 'Lakehurst_Hangar_No._1', OVERTURE]
});

// ====================================================================== Edison Memorial Tower
NJ_OUTER.push({
  id: 'nj_edison_tower',
  name: 'Thomas Edison Memorial Tower',
  kind: 'tower',
  built: [1937.4, 1938.1],
  end: 9999,
  anchor: [-74.339, 40.56319],
  build: b => {
    // octagonal concrete tower: 118 ft column + a 13 ft 8 in Pyrex bulb = 131 ft (40 m)
    const cx = 0.0;
    const cy = 0.0;
    b.color('#CFC9BB').cylinder(cx, cy, 6.4, 0, 1.0, 8);
    b.color('#D8D2C3');
    shaft(b, cx, cy, 3.9, 2.4, 1.0, 35.97, 8, Math.PI / 8);
    b.color('#C8C2B3').cylinder(cx, cy, 2.9, 35.97, 36.5, 8);
    // the bulb: widest 2.3 m, 4.17 m high
    b.color('#F4E9B4');
    b.loft([circle(cx, cy, 1.0, 12), circle(cx, cy, 2.0, 12), circle(cx, cy, 2.3, 12), circle(cx, cy, 1.5, 12)], [36.5, 37.8, 39.0, 40.1], {top: false});
    b.pyramid(circle(cx, cy, 1.5, 12), 40.1, [cx, cy, 40.67]);
  },
  facts: {
    Dedicated: '11 February 1938 (construction began 17 May 1937), at Edison\'s Menlo Park laboratory site; Massena & DuPont, concrete by John Joseph Earley',
    Size: '131 ft (40 m) above its terrace; the bulb of Corning Pyrex is 13 ft 8 in (4.2 m)',
    Model: 'height cited (a 118 ft column and the bulb); the foot (OpenStreetMap circle, 7.8 m across), the octagonal section and the taper are estimated; the terrace is not modelled'
  },
  sources: [WIKI + 'Thomas_Alva_Edison_Memorial_Tower_and_Museum', OSM + 'way/427497491']
});

// ====================================================================== Asbury Park Convention Hall
const ASBURY_HALL = P(109.9, 40.3, 47.4, 55.2, 31.1, -12.4, 93.6, -27.2);
const ASBURY_ARCADE = P(20.7, -10.2, 31.1, -12.4, 47.4, 55.2, 45.5, 55.6, 27.8, 60.6, 11.3, -7.7);
const ASBURY_THEATRE = P(-18.9, -0.5, 11.3, -7.7, 27.8, 60.6, -2.4, 67.8);
NJ_OUTER.push({
  id: 'nj_asbury_convention_hall',
  name: 'Asbury Park Convention Hall and Paramount Theatre',
  kind: 'building',
  built: [1928, 1930.6],
  end: 9999,
  anchor: [-73.99889, 40.22361],
  build: b => {
    // hall (over the beach) with an arched roof, arcade and theatre block
    const o = obb(ASBURY_HALL);
    const W = o.W;
    const L = o.L;
    const zs = 12;
    const H = 20;
    const N = 12;
    const prof: V2[] = [];
    for (let i = 0; i <= N; i++) {
      const u = -W / 2 + (W * i) / N;
      const t = (2 * u) / W;
      prof.push([u, zs + (H - zs) * Math.sqrt(Math.max(1 - t * t, 0))]);
    }
    b.color('#D9D2C0').frame(o.cx, o.cy, 0, o.bearing, () => {
      b.box(0, 0, 0, W, L, zs, {top: false});
      b.color('#8E9AA0');
      for (let i = 0; i < N; i++) {
        const [u0, z0] = prof[i];
        const [u1, z1] = prof[i + 1];
        b.quad([u0, -L / 2, z0], [u1, -L / 2, z1], [u1, L / 2, z1], [u0, L / 2, z0]);
      }
      b.color('#D9D2C0');
      for (const y of [-L / 2, L / 2]) {
        for (let i = 0; i < N; i++) {
          const [u0, z0] = prof[i];
          const [u1, z1] = prof[i + 1];
          b.quad([u0, y, zs], [u1, y, zs], [u1, y, z1], [u0, y, z0]);
        }
      }
    });
    block(b, ASBURY_ARCADE, 0, 9, '#D9D2C0', '#8E9AA0');
    block(b, ASBURY_THEATRE, 0, 15, '#CFC7B2', '#8E9AA0');
    b.color('#CFC7B2').cap(scaled(ASBURY_THEATRE, 0.8), 19);
    b.color('#CFC7B2').walls(scaled(ASBURY_THEATRE, 0.8), 15, 19);
  },
  replaces: [ASBURY_HALL, ASBURY_ARCADE, ASBURY_THEATRE],
  facts: {
    Built: '1928-1930 by Warren & Wetmore (Grand Central Terminal\'s architects); Italian-French style with nautical themes; the hall reaches 215 ft (66 m) over the beach on steel-encased concrete piles; 3,600 seats; the 1,600-seat Paramount Theatre is joined by an arcade over the boardwalk',
    Model: 'the three plans are the real outlines (Overture); the heights (hall 12 m with an arched roof to 20 m, arcade 9 m, theatre 15-19 m) are estimated, none is cited'
  },
  sources: [WIKI + 'Asbury_Park_Convention_Hall', OVERTURE]
});

// ====================================================================== High Point Monument
NJ_OUTER.push({
  id: 'nj_high_point_monument',
  name: 'High Point Monument',
  kind: 'monument',
  built: [1928, 1930.9],
  end: 9999,
  anchor: [-74.6613, 41.3208],
  build: b => {
    // centre of the OSM outline (-27.1, 16.9), rotated 22° east of north (the outline's edges)
    b.frame(-27.1, 16.9, 0, 22, () => {
      b.color('#B8B3A6').box(0, 0, 0, 11.0, 11.0, 2.0);
      b.color('#A9A396').box(0, 0, 2.0, 8.0, 8.0, 3.0);
      // granite obelisk: 220 ft = 67.06 m to the tip
      b.color('#C9C4B6');
      b.loft([rect(0, 0, 6.2, 6.2), rect(0, 0, 3.2, 3.2)], [5.0, 61.6], {top: false});
      b.pyramid(rect(0, 0, 3.2, 3.2), 61.6, [0, 0, 67.06]);
    });
  },
  replaces: [P(-19.9, 20.0, -30.0, 24.1, -34.3, 13.8, -24.1, 9.7)],
  facts: {
    Built: '1928-1930, a war veterans\' memorial given by Colonel Anthony R. Kuser; granite and quartz obelisk, 220 ft (67 m) tall with 291 steps, on the highest point of New Jersey (1,803 ft)',
    Model: 'height cited (the OpenStreetMap height is 67.0 m); the footprint is the real outline; the base stages and the taper from 6.2 m to 3.2 m are estimated'
  },
  sources: [WIKI + 'High_Point,_New_Jersey', OVERTURE]
});
