/**
 * New York landmarks: lost. Research: data/research/landmarks_lost.md, data/tables/landmarks_lost.csv.
 *
 * Hand-built low-poly reconstructions of buildings that are gone. Every plan is placed on
 * its real site: outlines traced in OpenHistoricalMap (CC0, from Sanborn / Bromley / Castello
 * Plan sheets), today's lot lines (city footprints) or street lines (Overture roads); heights
 * and room sizes come from the sources listed with each model. Anything estimated is named
 * in the model's facts ("Model: …").
 */
import {MeshBuilder, rect, rotRect, circle, type V2, type V3} from './kit';
import type {Landmark} from './types';

const FT = 0.3048;
const WP = 'https://en.wikipedia.org/wiki/';
const OHMW = 'https://www.openhistoricalmap.org/way/';
const OHMR = 'https://www.openhistoricalmap.org/relation/';
/** Manhattan's street grid: avenues run 29° east of north. */
const GRID = 29;

// ------------------------------------------------------------------ helpers

function norm(v: V2): V2 {
  const l = Math.hypot(v[0], v[1]) || 1;
  return [v[0] / l, v[1] / l];
}

/** Ring offset outward (d > 0) or inward (d < 0) by d metres (mitred corners). */
function offset(r: V2[], d: number): V2[] {
  let a = 0;
  for (let i = 0; i < r.length; i++) {
    const p = r[i];
    const q = r[(i + 1) % r.length];
    a += p[0] * q[1] - q[0] * p[1];
  }
  const s = a > 0 ? 1 : -1;
  const n = r.length;
  return r.map((p, i) => {
    const p0 = r[(i + n - 1) % n];
    const p1 = r[(i + 1) % n];
    const e0 = norm([p[0] - p0[0], p[1] - p0[1]]);
    const e1 = norm([p1[0] - p[0], p1[1] - p[1]]);
    const n0: V2 = [e0[1] * s, -e0[0] * s];
    const n1: V2 = [e1[1] * s, -e1[0] * s];
    const mx = n0[0] + n1[0];
    const my = n0[1] + n1[1];
    const ml = Math.max(mx * n0[0] + my * n0[1], 0.25);
    return [p[0] + (mx * d) / ml, p[1] + (my * d) / ml] as V2;
  });
}

/** Storey bands: n thin dark hoops just proud of the walls of `ring` between z0 and z1. */
function hoops(b: MeshBuilder, ring: V2[], z0: number, z1: number, n: number, color: string, frac = 0.42) {
  const fh = (z1 - z0) / n;
  const out = offset(ring, 0.22);
  b.color(color);
  for (let i = 0; i < n; i++) b.walls(out, z0 + fh * (i + 0.3), z0 + fh * (i + 0.3 + frac));
}

/** Row of n square piers between two points. */
function piers(b: MeshBuilder, x0: number, y0: number, x1: number, y1: number, n: number, w: number, z0: number, h: number) {
  for (let i = 0; i < n; i++) {
    const t = n === 1 ? 0.5 : i / (n - 1);
    b.box(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, z0, w, w, h);
  }
}

/** Barrel vault (half-ellipse section) over a rectangle; the ridge runs along local y when `alongY`. */
function vault(b: MeshBuilder, cx: number, cy: number, sx: number, sy: number, z0: number, rise: number, alongY = true, segs = 8) {
  const half = (alongY ? sx : sy) / 2;
  const len = (alongY ? sy : sx) / 2;
  const P = (u: number, v: number, z: number): V3 => (alongY ? [cx + u, cy + v, z] : [cx + v, cy + u, z]);
  for (let i = 0; i < segs; i++) {
    const a0 = (Math.PI * i) / segs;
    const a1 = (Math.PI * (i + 1)) / segs;
    const u0 = -Math.cos(a0) * half;
    const u1 = -Math.cos(a1) * half;
    const w0 = z0 + Math.sin(a0) * rise;
    const w1 = z0 + Math.sin(a1) * rise;
    b.quad(P(u0, -len, w0), P(u1, -len, w1), P(u1, len, w1), P(u0, len, w0));
    for (const e of [-len, len]) b.tri(P(0, e, z0), P(u0, e, w0), P(u1, e, w1));
  }
}

/** Vertical half-disc (lunette window) on a wall: centre of the diameter at (x, y, z0); the wall runs along local x when `alongX`. */
function lunette(b: MeshBuilder, x: number, y: number, z0: number, r: number, alongX: boolean, segs = 10) {
  const p = (a: number): V3 => (alongX ? [x + Math.cos(a) * r, y, z0 + Math.sin(a) * r] : [x, y + Math.cos(a) * r, z0 + Math.sin(a) * r]);
  for (let i = 0; i < segs; i++) b.tri([x, y, z0], p((Math.PI * i) / segs), p((Math.PI * (i + 1)) / segs));
}

/** Sphere of radius r centred at height zc. */
function sphere(b: MeshBuilder, cx: number, cy: number, zc: number, r: number, segs = 20, rings = 12) {
  const R: V2[][] = [];
  const Z: number[] = [];
  for (let k = 1; k < rings; k++) {
    const a = -Math.PI / 2 + (Math.PI * k) / rings;
    R.push(circle(cx, cy, Math.cos(a) * r, segs));
    Z.push(zc + Math.sin(a) * r);
  }
  b.loft(R, Z, {top: false});
  b.pyramid(R[0], Z[0], [cx, cy, zc - r]);
  b.pyramid(R[R.length - 1], Z[Z.length - 1], [cx, cy, zc + r]);
}

/** Plain block: walls + roof of `ring` to height H with storey bands. */
function block(b: MeshBuilder, ring: V2[], H: number, floors: number, wall: string, band: string, roof?: string) {
  b.color(wall).prism(ring, 0, H);
  if (roof) b.color(roof).cap(offset(ring, -0.8), H + 0.05);
  if (floors > 0) hoops(b, ring, 1.5, H - 0.8, floors, band);
}

// ================================================================== 1. World Trade Center (1973–2001)
// Tower centres: OpenHistoricalMap ways 198201501 / 198201503, equal to the centroids of
// the 9/11 Memorial pools (Overture base_water "Memorial North Pool" / "South Pool").
// Plan: 208 ft square (Wikipedia; "about 210 ft on a side ... corners beveled 9 ft 9 in",
// 59 columns on each face: NIST NCSTAR 1, sec. 1.2.2). Roofs 1,368 ft and 1,362 ft; antenna
// mast 360 ft (NIST) / 362 ft (Wikipedia) on 1 WTC. Faces turned 29.3° east of north (OHM
// outline, memorial pools).
const WTC1: V2 = [-74.013175, 40.712139];
const WTC2: V2 = [-74.013082, 40.71103];
const WTC_BRG = 29.3;
const TOWER_SIDE = 208 * FT;
const TOWER_CHAMFER = (9.75 * FT) / Math.SQRT2; // 9 ft 9 in bevel face
const WTC_SRC = [WP + 'World_Trade_Center_(1973%E2%80%932001)', OHMW + '198201501', 'https://doi.org/10.6028/NIST.NCSTAR.1'];

function towerRing(inset = 0): V2[] {
  const h = TOWER_SIDE / 2 - inset;
  const c = TOWER_CHAMFER;
  return [
    [-h + c, -h],
    [h - c, -h],
    [h, -h + c],
    [h, h - c],
    [h - c, h],
    [-h + c, h],
    [-h, h - c],
    [-h, -h + c]
  ];
}

function buildTwinTower(b: MeshBuilder, H: number) {
  const alu = '#C6CACC';
  const dark = '#555B60';
  const win = '#8E979D';
  const zL = 72 * FT; // six 12-ft storeys of lobby behind the "trident" columns (estimated)
  const h = TOWER_SIDE / 2;
  b.frame(0, 0, 0, WTC_BRG, () => {
    b.color('#3B4045').prism(towerRing(1.4), 0, zL, {top: false});
    // 19 lobby columns a face at 10 ft centres; above them three columns spring from each
    b.color(alu);
    for (let i = -9; i <= 9; i++) {
      const u = i * 10 * FT;
      for (const s of [-1, 1]) {
        b.box(u, s * (h - 0.45), 0, 0.9, 0.9, zL);
        b.box(s * (h - 0.45), u, 0, 0.9, 0.9, zL);
      }
    }
    const ring = towerRing();
    b.color(alu).prism(ring, zL, H);
    // narrow windows between the 59 columns of each face: every other bay drawn
    b.color(win);
    for (let i = -14; i <= 14; i++) {
      const u = i * 80 * 0.0254;
      for (const s of [-1, 1]) {
        b.quad([u - 0.28, s * (h + 0.12), zL + 4], [u + 0.28, s * (h + 0.12), zL + 4], [u + 0.28, s * (h + 0.12), H - 4], [u - 0.28, s * (h + 0.12), H - 4]);
        b.quad([s * (h + 0.12), u - 0.28, zL + 4], [s * (h + 0.12), u + 0.28, zL + 4], [s * (h + 0.12), u + 0.28, H - 4], [s * (h + 0.12), u - 0.28, H - 4]);
      }
    }
    // mechanical floors 7–8, 41–42, 75–76, 108–110: dark louvre bands (levels from the floor count)
    const fl = (H - zL) / 104;
    const zf = (n: number) => zL + (n - 7) * fl;
    const out = offset(ring, 0.25);
    b.color(dark);
    for (const [f0, f1] of [
      [7, 9],
      [41, 43],
      [75, 77],
      [108, 110.7]
    ])
      b.walls(out, zf(f0), Math.min(zf(f1), H - 0.6));
    b.color('#7E8589').cap(towerRing(2.5), H + 0.05);
  });
}

const wtc1: Landmark = {
  id: 'wtc_1_north_tower',
  name: 'One World Trade Center (North Tower, 1972–2001)',
  kind: 'tower',
  built: [1968.6, 1972.0],
  end: 2001.69,
  anchor: WTC1,
  build: b => buildTwinTower(b, 1368 * FT),
  replaces: [rotRect(0, 0, TOWER_SIDE + 2, TOWER_SIDE + 2, WTC_BRG)],
  facts: {
    Construction: 'steel from 6 Aug 1968; topped out 23 Dec 1970; first tenants Dec 1970; complex dedicated 4 Apr 1973',
    Destroyed: '11 Sep 2001',
    Height: '1,368 ft (417 m) roof; 1,730 ft (527 m) with the 1979 antenna; 110 storeys',
    Plan: '208 ft (63.4 m) square, corners bevelled 9 ft 9 in; 59 columns on each face',
    Architect: 'Minoru Yamasaki with Emery Roth & Sons; engineers Skilling, Helle, Christiansen, Robertson',
    Model: 'plan, height and position cited; lobby height (72 ft) and mechanical-floor levels derived from the floor count'
  },
  sources: WTC_SRC
};

const wtc2: Landmark = {
  id: 'wtc_2_south_tower',
  name: 'Two World Trade Center (South Tower, 1973–2001)',
  kind: 'tower',
  built: [1969.05, 1973.0],
  end: 2001.69,
  anchor: WTC2,
  build: b => buildTwinTower(b, 1362 * FT),
  replaces: [rotRect(0, 0, TOWER_SIDE + 2, TOWER_SIDE + 2, WTC_BRG)],
  facts: {
    Construction: 'Jan 1969; topped out 19 Jul 1971; occupied from Jan 1972',
    Destroyed: '11 Sep 2001',
    Height: '1,362 ft (415 m); 110 storeys; observation deck on the roof',
    Plan: '208 ft (63.4 m) square, corners bevelled 9 ft 9 in',
    Architect: 'Minoru Yamasaki with Emery Roth & Sons',
    Model: 'plan, height and position cited; lobby height and mechanical-floor levels derived from the floor count'
  },
  sources: [WTC_SRC[0], OHMW + '198201503', WTC_SRC[2]]
};

const wtc1Antenna: Landmark = {
  id: 'wtc_1_antenna',
  name: 'One World Trade Center antenna mast',
  kind: 'tower',
  built: [1978.4, 1979.45],
  end: 2001.69,
  anchor: WTC1,
  build: b => {
    const z0 = 1368 * FT;
    const top = 1730 * FT;
    b.frame(0, 0, 0, WTC_BRG, () => {
      b.color('#8B9195').box(0, 0, z0, 9, 9, 5);
      const zs = [z0 + 5, z0 + 30, z0 + 60, z0 + 85, top];
      const ws = [3.6, 2.8, 2.0, 1.2, 0.5];
      for (let i = 0; i < zs.length - 1; i++) {
        b.color(i % 2 ? '#C9473B' : '#E9E9E6').loft([rect(0, 0, ws[i], ws[i]), rect(0, 0, ws[i + 1], ws[i + 1])], [zs[i], zs[i + 1]]);
      }
    });
  },
  facts: {
    Built: 'installed 1978; broadcasting from 1979 (late May – early June)',
    Height: '362 ft (110 m) mast on the 1,368 ft roof: tip at 1,730 ft (527 m); NIST gives the mast as 360 ft',
    Destroyed: '11 Sep 2001',
    Model: 'height cited; mast widths estimated from photographs'
  },
  sources: [WTC_SRC[0]]
};

// The superblock: convex hull of the OHM outlines of 1–6 WTC (58,700 m² = 14.5 acres; the
// site is cited as 16 acres). Cleared of Radio Row from 21 March 1966.
const WTC_SITE: V2[] = [
  [114.6, -213.9],
  [68.0, -201.3],
  [-67.9, -125.8],
  [-32.1, 90.3],
  [-9.4, 128.9],
  [49.3, 94.0],
  [165.1, 17.9],
  [215.5, -19.7],
  [134.1, -180.2]
];
const wtcPlaza: Landmark = {
  id: 'wtc_tobin_plaza',
  name: 'World Trade Center plaza (Austin J. Tobin Plaza)',
  kind: 'park',
  built: [1966.22, 1973.26],
  end: 2001.69,
  anchor: WTC1,
  build: b => {
    // OHM relation 2965688: the paved plaza and its fountain ring (The Sphere at the centre)
    const paving: V2[] = [
      [44.9, 19.1],
      [-10.2, -77.7],
      [89.3, -134.7],
      [144.3, -39.1]
    ];
    b.color('#B9B4AA').prism(paving, 0, 0.4);
    b.color('#8E8A82').prism(circle(80.7, -51.3, 12.4, 24), 0.4, 1.0);
    b.color('#6F8FA0').cap(circle(80.7, -51.3, 11.6, 24), 1.05);
    b.color('#5A5E63').cylinder(80.7, -51.3, 1.6, 1.0, 2.6, 10);
    sphere(b, 80.7, -51.3, 2.6 + 3.2, 3.2, 12, 8);
  },
  replaces: [WTC_SITE],
  facts: {
    Site: '16-acre superblock (Vesey, Church, Liberty, West streets); Radio Row cleared from 21 Mar 1966',
    Plaza: 'five acres, dedicated 4 Apr 1973; Fritz Koenig\'s bronze Sphere in the fountain',
    Destroyed: '11 Sep 2001',
    Model: 'plaza and fountain outline from OpenHistoricalMap; the Sphere is a plain globe'
  },
  sources: [WP + 'Austin_J._Tobin_Plaza', OHMR + '2965688', WTC_SRC[0]]
};

function wtcLow(id: string, name: string, built: [number, number], anchor: V2, ring: V2[], H: number, floors: number, wall: string, band: string, facts: Record<string, string>, sources: string[], kind: Landmark['kind'] = 'building'): Landmark {
  return {id, name, kind, built, end: 2001.69, anchor, build: b => block(b, ring, H, floors, wall, band, '#6A6C6E'), replaces: [ring], facts, sources};
}

const wtc4 = wtcLow(
  'wtc_4_1975',
  'Four World Trade Center (Southeast Plaza Building, 1975–2001)',
  [1972.5, 1975.5],
  [-74.012132, 40.710661],
  [
    [52.5, 33.3],
    [17.3, 54.6],
    [-6.6, 14.6],
    [-35.0, 31.9],
    [-42.5, 19.7],
    [-45.4, 21.4],
    [-55.0, 6.2],
    [-51.8, 4.3],
    [-62.2, -12.5],
    [-20.1, -37.9],
    [-13.2, -26.6],
    [26.5, -50.4],
    [46.1, -16.8],
    [28.7, -6.6]
  ],
  118 * FT,
  9,
  '#3B3835',
  '#1F2224',
  {
    Built: 'c. 1972–1975; opened Jan 1977; commodities exchanges',
    Destroyed: '11 Sep 2001',
    Height: '118 ft (36 m), nine storeys',
    Model: 'outline OpenHistoricalMap way 198590237 (6,310 m²); height cited'
  },
  [WP + '4_World_Trade_Center_(1975%E2%80%932001)', OHMW + '198590237']
);

const wtc5 = wtcLow(
  'wtc_5_1972',
  'Five World Trade Center (Northeast Plaza Building, 1972–2001)',
  [1970.0, 1972.2],
  [-74.011413, 40.711974],
  [
    [-37.8, 68.2],
    [16.4, 36.1],
    [13.2, 30.4],
    [66.8, -1.5],
    [44.4, -39.8],
    [38.4, -36.2],
    [16.0, -74.9],
    [-22.0, -52.3],
    [0.3, -13.7],
    [-16.9, -3.4],
    [-21.4, -10.8],
    [-68.1, 17.1]
  ],
  118 * FT,
  9,
  '#3B3835',
  '#1F2224',
  {
    Built: '1970–1972',
    Destroyed: '11 Sep 2001 (ruin cleared Jan 2002)',
    Height: '118 ft (36 m), nine storeys',
    Plan: 'L-shaped, 330 × 420 ft overall (101 × 128 m)',
    Model: 'outline OpenHistoricalMap way 198590239 (126 × 96 m bounding box, 8,435 m²); height cited'
  },
  [WP + '5_World_Trade_Center', OHMW + '198590239']
);

const wtc6 = wtcLow(
  'wtc_6_1973',
  'Six World Trade Center (US Custom House, 1973–2001)',
  [1969.0, 1973.5],
  [-74.012858, 40.71278],
  [
    [-36.2, 58.0],
    [22.6, 23.0],
    [18.2, 15.5],
    [66.4, -13.3],
    [43.6, -52.1],
    [4.9, -29.0],
    [-2.1, -40.7],
    [-47.0, -14.0],
    [-35.7, 5.2],
    [-58.9, 19.4]
  ],
  110 * FT,
  8,
  '#3B3835',
  '#1F2224',
  {
    Built: '1969–1973',
    Destroyed: '11 Sep 2001',
    Height: '110 ft (33.5 m), eight storeys (OpenHistoricalMap gives 28 m)',
    Model: 'outline OpenHistoricalMap way 198590240 (6,680 m²); height cited'
  },
  [WTC_SRC[0], OHMW + '198590240']
);

const wtc3 = wtcLow(
  'wtc_3_marriott',
  'Marriott World Trade Center (Three World Trade Center; Vista International Hotel, 1981–2001)',
  [1979.2, 1981.5],
  [-74.01369, 40.711354],
  [
    [6.8, 60.6],
    [7.5, 60.8],
    [22.5, 52.6],
    [22.8, 51.9],
    [6.4, 21.2],
    [3.7, 7.8],
    [28.7, 2.1],
    [29.0, 1.5],
    [1.7, -46.4],
    [0.5, -46.7],
    [-6.8, -44.9],
    [-7.4, -48.0],
    [-8.1, -48.5],
    [-24.1, -39.7],
    [-24.5, -39.0],
    [-11.5, 28.4]
  ],
  73.7,
  22,
  '#C9CCCD',
  '#59626A',
  {
    Built: 'Mar 1979 – 1 Jul 1981 (Vista International; Marriott from 1995)',
    Destroyed: '11 Sep 2001',
    Height: '73.7 m (242 ft), 22 storeys',
    Architect: 'Skidmore, Owings & Merrill',
    Model: 'outline OpenHistoricalMap way 198590238 (2,925 m²); height cited'
  },
  [WP + 'Marriott_World_Trade_Center', OHMW + '198590238']
);

const wtc7 = wtcLow(
  'wtc_7_1987',
  'Seven World Trade Center (1987–2001)',
  [1984.75, 1987.2],
  [-74.0119, 40.713286],
  [
    [-30.6, 41.6],
    [51.3, -6.9],
    [20.1, -37.5],
    [-42.5, -0.5]
  ],
  610 * FT,
  47,
  '#8D5B52',
  '#3F2F2E',
  {
    Built: '2 Oct 1984 – Mar 1987; opened May 1987, over the Con Edison substation',
    Destroyed: '11 Sep 2001, 5:21 pm',
    Height: '610 ft (186 m), 47 storeys, red granite',
    Plan: 'trapezoid 330 ft long and 140 ft wide (101 × 43 m)',
    Architect: 'Emery Roth & Sons',
    Model: 'outline OpenHistoricalMap way 198590241 (95 × 42 m, 3,550 m²); height cited'
  },
  [WP + '7_World_Trade_Center_(1987%E2%80%932001)', OHMW + '198590241'],
  'tower'
);

// ================================================================== 2. Pennsylvania Station (1910–1963)
// McKim, Mead & White. 788.75 × 430.5 ft (1929 measurement) on the two blocks between
// Seventh and Eighth avenues, 31st and 33rd streets: the street lines (Overture centre
// lines less half of the 100 ft avenues and 60 ft streets) leave a block of 243.1 × 138.7 m,
// and the OHM outline (way 198645203, Bromley land book) measures 237 × 133 m.
// Local frame: +x toward Seventh Avenue (bearing 118.9°), +y toward 33rd Street.
const PENN_L = 788.75 * FT;
const PENN_W = 430.5 * FT;
function buildPennStation(b: MeshBuilder) {
  const granite = '#D8CDC3';
  const shade = '#BFB3A8';
  const roof = '#8F918E';
  const glass = '#9DB2B6';
  const dark = '#4C4F52';
  const hx = PENN_L / 2;
  const hy = PENN_W / 2;
  const H = 69 * FT; // "average height of 69 ft above the street"
  const D = 17; // depth of the perimeter ranges (estimated from the plan)
  b.frame(-2.0, 2.07, 0, 28.9, () => {
    // perimeter ranges around the carriage drives and light courts
    b.color(granite).prism(rect(0, 0, PENN_L, PENN_W), 0, H, {holes: [rect(0, 0, PENN_L - 2 * D, PENN_W - 2 * D)]});
    b.color(roof).cap(rect(0, 0, PENN_L - 1.6, PENN_W - 1.6), H + 0.05, [rect(0, 0, PENN_L - 2 * D + 1.6, PENN_W - 2 * D + 1.6)]);
    // sunken drives and low roofs inside
    b.color('#77736E').cap(rect(0, 0, PENN_L - 2 * D, PENN_W - 2 * D), 2.0);
    // Seventh Avenue front: Doric colonnade (columns 35 ft high, 4.5 ft across)
    const colH = 35 * FT;
    const colW = 4.5 * FT;
    b.color(shade).box(hx - 2.2, 0, 1.2, 0.6, PENN_W - 40, colH + 0.6, {top: false});
    b.color(granite);
    piers(b, hx + 0.9, 22, hx + 0.9, hy - 23, 11, colW, 1.2, colH);
    piers(b, hx + 0.9, -22, hx + 0.9, -hy + 23, 11, colW, 1.2, colH);
    // central entrance pavilion with the clock (61 ft above the sidewalk) and attic
    b.box(hx - 6, 0, 0, 14, 36, H + 3.4);
    piers(b, hx + 1.6, -13.5, hx + 1.6, 13.5, 6, colW, 1.2, colH);
    b.color(dark).box(hx + 1.15, 0, 1.2, 0.3, 24, colH - 1);
    b.color('#F1EEE6').box(hx + 1.3, 0, 61 * FT - 1.07, 0.4, 2.13, 2.13);
    // carriageway pavilions at the two Seventh Avenue corners (63 ft wide, after the Brandenburg Gate)
    for (const s of [-1, 1]) {
      const cy = s * (hy - (63 * FT) / 2);
      b.color(granite).box(hx - 8, cy, 0, 16, 63 * FT, H + 1.5);
      b.gable(hx - 8, cy, 16, 63 * FT, H + 1.5, 2.6, false);
      piers(b, hx + 0.9, cy - 7.5, hx + 0.9, cy + 7.5, 4, colW, 1.2, colH);
      b.color(dark).box(hx + 0.45, cy, 1.2, 0.3, 15, colH - 1);
      // 230 ft colonnades along the eastern ends of the 31st and 33rd Street fronts
      b.color(shade).box(hx - 16 - 35, s * (hy - 2.2), 1.2, 70 - 2, 0.6, colH + 0.6, {top: false});
      b.color(granite);
      piers(b, hx - 18, s * (hy + 0.9), hx - 16 - 70, s * (hy + 0.9), 16, colW, 1.2, colH);
      // side entrance pavilions on the waiting-room axis
      b.box(13.4, s * (hy - 7), 0, 30, 14, H + 2.4);
      piers(b, 13.4 - 10, s * (hy + 0.9), 13.4 + 10, s * (hy + 0.9), 5, colW, 1.2, colH);
    }
    // Eighth Avenue front: central pavilion with three great openings
    b.color(granite).box(-hx + 7, 0, 0, 14, 45 * FT + 16, H + 2.4);
    b.color(dark);
    for (const k of [-1, 0, 1]) b.box(-hx - 0.1, k * 6.2, 1.0, 0.3, 4.4, 13);
    // arcade of shops from the Seventh Avenue entrance: 225 ft long, 45 ft wide
    const arcE = hx - 13;
    const arcW = arcE - 225 * FT;
    b.color(granite).box((arcE + arcW) / 2, 0, 0, arcE - arcW, 45 * FT + 3, 17);
    b.color(glass);
    vault(b, (arcE + arcW) / 2, 0, arcE - arcW, 45 * FT, 17, 5, false, 6);
    // loggia and stair hall between the arcade and the waiting room
    const wrE = 30;
    b.color(granite).box((arcW + wrE) / 2, 0, 0, arcW - wrE, 34, H + 2);
    // General Waiting Room: 314 ft 4 in × 108 ft 8 in inside, 150 ft high; 153 ft maximum outside
    const wrL = 314 * FT + 4 * 0.0254 + 5;
    const wrB = 108 * FT + 8 * 0.0254 + 5;
    const wrX = wrE - wrB / 2;
    const eave = 37.5;
    b.color(granite).box(wrX, 0, 0, wrB, wrL, eave);
    b.color(roof).gable(wrX, 0, wrB + 1.2, wrL + 1.2, eave, 153 * FT - eave, true);
    // thermal windows: lunettes of 38 ft 4 in radius, three a side and one in each gable end
    const lr = 38 * FT + 4 * 0.0254;
    b.color(dark);
    for (const k of [-1, 0, 1]) {
      lunette(b, wrX + wrB / 2 + 0.15, k * 30.5, 23.5, lr, false);
      lunette(b, wrX - wrB / 2 - 0.15, k * 30.5, 23.5, lr, false);
    }
    for (const s of [-1, 1]) lunette(b, wrX, s * (wrL / 2 + 0.15), 23.5, lr, true);
    // lower men's and women's waiting rooms (100 × 58 ft) on either side
    for (const s of [-1, 1]) b.color(granite).box(wrX, s * (wrL / 2 + 6), 0, 58 * FT + 4, 12, H + 4);
    // Concourse: glass roof 210 × 340 ft on steel arches, three parallel vaults
    const cE = wrX - wrB / 2;
    const cB = 210 * FT;
    const cL = 340 * FT;
    b.color('#6D6F70').box(cE - cB / 2, 0, 0, cB, cL, 15, {top: false});
    b.color(glass);
    for (const k of [-1, 0, 1]) vault(b, cE - cB / 2 + (k * cB) / 3, 0, cB / 3 - 0.6, cL, 15, k === 0 ? 14.5 : 12, true, 8);
    b.color('#6D6F70');
    for (let i = -4; i <= 4; i++) for (const k of [-1.5, -0.5, 0.5, 1.5]) b.box(cE - cB / 2 + (k * cB) / 3, i * 12.4, 0, 0.7, 0.7, 15);
    // exit concourse (60 ft) and the Eighth Avenue offices beyond
    const exW = cE - cB;
    b.color(shade).box((exW - hx + D) / 2, 0, 0, exW + hx - D, cL * 0.8, 13);
  });
}

const pennStation: Landmark = {
  id: 'penn_station_1910',
  name: 'Pennsylvania Station (1910–1963)',
  kind: 'building',
  built: [1904.5, 1910.9],
  end: 1963.83,
  anchor: [-73.992949, 40.750298],
  build: buildPennStation,
  replaces: [rotRect(-2.0, 2.07, 243.1, 138.7, 28.9)],
  facts: {
    Built: 'excavation from June 1904; opened 8 Sep 1910 (Long Island) and 27 Nov 1910 (Pennsylvania)',
    Demolished: 'from 28 Oct 1963; gone by 1966 (Madison Square Garden and Penn Plaza above the tracks)',
    Architect: 'McKim, Mead & White (Charles F. McKim)',
    Size: '788.75 × 430.5 ft (240 × 131 m), eight acres; average height 69 ft, 153 ft at the waiting-room roof',
    Rooms: 'General Waiting Room 314 ft 4 in × 108 ft 8 in × 150 ft; Concourse under a 210 × 340 ft glass roof; arcade 225 × 45 ft',
    Model: 'plan dimensions and heights cited; positions of the rooms along the axis, depth of the outer ranges and the concourse roof height (about 27–30 m) estimated from the published plan and photographs'
  },
  sources: [WP + 'Pennsylvania_Station_(1910%E2%80%931963)', OHMW + '198645203']
};

// ================================================================== 3. Singer Building and City Investing Building
// Outlines: OpenHistoricalMap ways 198552870 (from Sanborn 1905 vol. 1) and 198552871.
// Singer Tower: 65 ft square, set back 30 ft from Broadway, 10 ft from the City Investing
// Building on the north lot line; lantern top 612 ft; flagpole 62 ft more.
const SINGER_RING: V2[] = [
  [39.0, 0.1],
  [12.2, 16.1],
  [8.0, 9.2],
  [-25.8, 29.6],
  [-40.6, 5.6],
  [19.8, -30.7]
];
function buildSinger(b: MeshBuilder) {
  const brick = '#9C4A3B';
  const stone = '#D8CFBF';
  const slate = '#56645F';
  // 14-storey base (the 1899 Singer and Bourne buildings raised and joined), about 200 ft
  const baseH = 200 * FT;
  b.color(brick).prism(SINGER_RING, 0, baseH - 7);
  b.color(slate).loft([SINGER_RING, offset(SINGER_RING, -3.2)], [baseH - 7, baseH]);
  hoops(b, SINGER_RING, 6, baseH - 8, 12, stone, 0.3);
  b.color(stone).walls(offset(SINGER_RING, 0.25), 0, 6);
  // tower: centre 12.95 m in from the north lot line and 19.05 m back from Broadway
  b.frame(15.8, -1.1, 0, 32.4, () => {
    const s = 65 * FT;
    const zBal = 144; // 36th-floor balcony (level estimated from the storey count)
    const zDome = (612 - 63.75 - 50) * FT;
    const zLan = (612 - 63.75) * FT;
    const top = 612 * FT;
    b.color(brick).prism(rect(0, 0, s, s), baseH - 8, zBal);
    // glazed centre bays (three of five 12-ft bays) between brick corner piers
    b.color('#3F474B');
    for (const [cx, cy, sx, sy] of [
      [0, s / 2 + 0.1, 36 * FT, 0.3],
      [0, -s / 2 - 0.1, 36 * FT, 0.3],
      [s / 2 + 0.1, 0, 0.3, 36 * FT],
      [-s / 2 - 0.1, 0, 0.3, 36 * FT]
    ])
      b.box(cx, cy, baseH, sx, sy, zBal - baseH - 3, {top: false});
    hoops(b, rect(0, 0, s, s), baseH, zBal - 2, 21, stone, 0.22);
    // balcony cantilevered 8.5 ft, then the bulging upper stage and the mansard dome
    b.color(stone).box(0, 0, zBal, s + 17 * FT, s + 17 * FT, 1.2);
    b.color(brick).prism(rect(0, 0, s + 1.6, s + 1.6), zBal + 1.2, zDome);
    const sq = (w: number) => rect(0, 0, w, w);
    b.color(slate).loft([sq(s + 1.6), sq(s + 0.6), sq(s - 2), sq(s - 6.5), sq(8.5)], [zDome, zDome + 4, zDome + 8, zDome + 12, zLan]);
    // lantern: 63.75 ft tall, 9 ft across at its base
    b.color(stone).box(0, 0, zLan, 5.2, 5.2, 3.2);
    b.box(0, 0, zLan + 3.2, 9 * FT, 9 * FT, 10);
    b.color(slate).pyramid(sq(9 * FT + 0.6), zLan + 13.2, [0, 0, top]);
    b.color('#D8D8D4').beam([0, 0, top], [0, 0, top + 62 * FT], 0.3);
  });
}

const singer: Landmark = {
  id: 'singer_building_1908',
  name: 'Singer Building (1908–1968)',
  kind: 'tower',
  built: [1906.7, 1908.35],
  end: 1968.0,
  anchor: [-74.010797, 40.709581],
  build: buildSinger,
  replaces: [SINGER_RING],
  facts: {
    Built: 'tower 1906–1908 over the 1899 Singer and Bourne buildings; world\'s tallest 1908–09',
    Demolished: 'Aug 1967 – 1968, for One Liberty Plaza: the tallest building ever demolished by its owner until 2019',
    Architect: 'Ernest Flagg',
    Height: '612 ft (186.5 m) to the top of the lantern, 674 ft with the flagpole; 41 storeys',
    Tower: '65 × 65 ft, set back 30 ft from Broadway; 50 ft dome under a 63.75 ft lantern; 14-storey base about 200 ft',
    Model: 'site outline OpenHistoricalMap (Sanborn 1905); heights cited; the balcony level and the dome profile estimated from photographs'
  },
  sources: [WP + 'Singer_Building', OHMW + '198552870']
};

const CITY_INV_RING: V2[] = [
  [34.8, -35.5],
  [40.5, -26.4],
  [13.3, -10.3],
  [22.6, 5.1],
  [-19.3, 30.3],
  [-34.2, 5.9]
];
const cityInvesting: Landmark = {
  id: 'city_investing_building_1908',
  name: 'City Investing Building (1908–1968)',
  kind: 'tower',
  built: [1906.5, 1908.3],
  end: 1968.0,
  anchor: [-74.010747, 40.709903],
  build: b => {
    const terra = '#D9D3C4';
    const copper = '#6E8F80';
    const bulk = 103; // 26 storeys of the 33 (486 ft): estimated from the storey count
    b.color(terra).prism(CITY_INV_RING, 0, bulk);
    hoops(b, CITY_INV_RING, 16, bulk - 2, 22, '#7B7468', 0.3);
    b.color('#B9B2A2').walls(offset(CITY_INV_RING, 0.25), 0, 16);
    // seven-storey central portion with gable roofs, to 486 ft above Broadway
    b.frame(-6.5, 9.5, 0, 30.9, () => {
      const top = 486 * FT;
      b.color(terra).box(0, 0, bulk, 30, 20, top - 9 - bulk);
      hoops(b, rect(0, 0, 30, 20), bulk, top - 9, 6, '#7B7468', 0.3);
      b.color(copper).gable(0, 0, 31, 21, top - 9, 9, false);
      b.gable(-8, 0, 9, 23, top - 9, 6.5, true);
      b.gable(8, 0, 9, 23, top - 9, 6.5, true);
    });
  },
  replaces: [CITY_INV_RING],
  facts: {
    Built: '1906–1908 (Francis H. Kimball); 12 acres of floor space',
    Demolished: '1968, with the Singer Building, for One Liberty Plaza',
    Height: '486 ft (148 m) above Broadway; 26-storey bulk with a seven-storey gabled centre',
    Frontage: '209 ft on Cortlandt Street, 109 ft on Church Street, 37.5 ft on Broadway; 313 ft deep',
    Model: 'LOW CONFIDENCE in plan: outline OpenHistoricalMap way 198552871 (1,735 m²), about 30 % smaller than the cited frontages imply and without the light courts; height of the bulk (103 m) and the form of the top estimated from the storey count and photographs'
  },
  sources: [WP + 'City_Investing_Building', OHMW + '198552871']
};

const LOST_PART1: Landmark[] = [wtc1, wtc2, wtc1Antenna, wtcPlaza, wtc3, wtc4, wtc5, wtc6, wtc7, pennStation, singer, cityInvesting];

// ================================================================== 4. Reservoir Square: Crystal Palace, Latting Observatory, Croton reservoir
// New York Crystal Palace (1853–1858). Dimensions from the architects' own description
// (Carstensen & Gildemeister, "New York Crystal Palace", 1854): Greek cross of four naves
// 41 ft 5 in wide and 67 ft to the ridge, aisles 54 ft wide on both sides and 50 ft high in
// two storeys (arms 149 ft 5 in wide), triangular one-storey lean-tos (24 ft) filling the
// angles to an octagon, an octagonal tower 8 ft across and 71 ft high at each angle, a
// dome 100 ft in diameter springing 71 ft above the floor, entrance halls 27 ft deep on
// three sides. The cross measures 111 m (364 ft) across on the OpenHistoricalMap outline
// (way 198109868), whose east strip is the two-storey machinery annex against the reservoir.
const CP_ANCHOR: V2 = [-73.983646, 40.753781];
function buildCrystalPalace(b: MeshBuilder) {
  const iron = '#DAD4BF';
  const glass = '#A9C6C8';
  const roofc = '#C8C2AC';
  const R = 55.5; // half of the cross (OHM outline; contemporary accounts give 365 ft 5 in)
  const a = (149 * FT + 5 * 0.0254) / 2;
  const nave = 41 * FT + 5 * 0.0254;
  b.frame(-6.12, 3.39, 0, GRID, () => {
    const oct: V2[] = [
      [-R, -a],
      [-a, -R],
      [a, -R],
      [R, -a],
      [R, a],
      [a, R],
      [-a, R],
      [-R, a]
    ];
    // lean-tos: one storey, 24 ft
    b.color(glass).prism(oct, 0, 24 * FT, {top: false});
    b.color(roofc).cap(oct, 24 * FT);
    // aisles of the cross: two storeys, 50 ft
    for (const [sx, sy] of [
      [2 * R, 2 * a],
      [2 * a, 2 * R]
    ] as V2[]) {
      b.color(glass).box(0, 0, 0, sx, sy, 50 * FT, {top: false});
      b.color(roofc).cap(rect(0, 0, sx, sy), 50 * FT);
      hoops(b, rect(0, 0, sx, sy), 0, 50 * FT, 2, iron, 0.12);
    }
    // naves: 41 ft 5 in wide, 67 ft to the ridge of the arched roof
    b.color(glass).box(0, 0, 50 * FT, 2 * R, nave, 9 * FT, {top: false});
    b.box(0, 0, 50 * FT, nave, 2 * R, 9 * FT, {top: false});
    b.color(roofc);
    vault(b, 0, 0, 2 * R, nave, 59 * FT, 8 * FT, false, 6);
    vault(b, 0, 0, nave, 2 * R, 59 * FT, 8 * FT, true, 6);
    // dome: 100 ft across, springing 71 ft above the floor; lantern to 123 ft
    b.color(iron).cylinder(0, 0, 50 * FT + 0.6, 50 * FT, 71 * FT, 16, {top: false});
    b.color('#C4CDC6').dome(0, 0, 50 * FT, 71 * FT, 50 * FT, 16, 6);
    b.color(iron).cylinder(0, 0, 1.8, 120 * FT, 123 * FT, 8);
    // eight octagonal towers, 8 ft across and 71 ft high, with 24 ft flagstaffs
    for (const [x, y] of oct) {
      b.color(iron).prism(circle(x, y, 4 * FT + 0.4, 8), 0, 71 * FT);
      b.beam([x, y, 71 * FT], [x, y, 95 * FT], 0.15);
    }
    // entrance halls on Sixth Avenue, 40th and 42nd streets: nave width, 27 ft deep, offices 27 × 18 ft beside them
    for (const [dx, dy] of [
      [-1, 0],
      [0, 1],
      [0, -1]
    ] as V2[]) {
      const cx = dx * (R + 13.5 * FT);
      const cy = dy * (R + 13.5 * FT);
      b.color(glass).box(cx, cy, 0, dx ? 27 * FT : nave, dx ? nave : 27 * FT, 50 * FT, {top: false});
      b.color(roofc).cap(rect(cx, cy, dx ? 27 * FT : nave, dx ? nave : 27 * FT), 50 * FT);
      for (const s of [-1, 1]) {
        const ox = dx ? dx * (R + 9 * FT) : s * (nave / 2 + 13.5 * FT);
        const oy = dx ? s * (nave / 2 + 13.5 * FT) : dy * (R + 9 * FT);
        b.color(iron).box(ox, oy, 0, dx ? 18 * FT : 27 * FT, dx ? 27 * FT : 18 * FT, 30 * FT);
      }
    }
    // machinery arcade and picture gallery added along the reservoir side (OHM outline: 14 × 137 m)
    b.color(iron).box(56.5, 0, 0, 14, 136.7, 10);
    hoops(b, rect(56.5, 0, 14, 136.7), 0.5, 10, 2, glass, 0.3);
  });
}

const crystalPalace: Landmark = {
  id: 'crystal_palace_1853',
  name: 'New York Crystal Palace (1853–1858)',
  kind: 'building',
  built: [1852.83, 1853.53],
  end: 1858.76,
  anchor: CP_ANCHOR,
  build: buildCrystalPalace,
  replaces: [
    [
      [-37.2, 100.8],
      [100.9, 24.1],
      [34.9, -95.4],
      [-105.2, -20.6]
    ]
  ],
  facts: {
    Built: '1852–1853; opened 14 Jul 1853 for the Exhibition of the Industry of All Nations',
    Destroyed: 'burned in under half an hour, 5 Oct 1858',
    Architects: 'Georg Carstensen and Charles Gildemeister',
    Plan: 'Greek cross of iron and glass, arms 149 ft 5 in wide, about 365 ft across; lean-tos fill the angles to an octagon with eight 71 ft towers',
    Dome: '100 ft in diameter, springing 71 ft above the floor (crown about 123 ft)',
    Site: 'Reservoir Square (Bryant Park), Sixth Avenue between 40th and 42nd streets',
    Model: 'dimensions from the architects\' 1854 description; position and the annex along the reservoir from the OpenHistoricalMap outline; the annex height (10 m) is estimated'
  },
  sources: ['https://archive.org/details/newyorkcrystalp00carsa', WP + 'New_York_Crystal_Palace', OHMW + '198109868']
};

// Latting Observatory (1853–1856): 315 ft, base 75 ft square, octagonal timber tower
// tapering to 6–8 ft, landings at 125, 225 and 300 ft; the top 75 ft was removed in 1855.
function buildLatting(b: MeshBuilder, H: number) {
  const timber = '#8A6A49';
  const light = '#B79670';
  const full = 315 * FT;
  const w = (z: number) => 21 - (21 - 2.1) * (z / full); // width across at height z
  b.frame(0, 0, 0, GRID, () => {
    b.color(light).box(0, 0, 0, 75 * FT, 75 * FT, 9);
    b.color('#6E6A63').hip(0, 0, 75 * FT + 0.8, 75 * FT + 0.8, 9, 2.2);
    const zs = [9, 125 * FT, 225 * FT, Math.min(300 * FT, H), H].filter((z, i, arr) => i === 0 || z > arr[i - 1]);
    b.color(timber).loft(
      zs.map(z => circle(0, 0, w(z) / 2, 8)),
      zs
    );
    // landings with telescopes at 125, 225 and 300 ft
    for (const ft of [125, 225, 300]) {
      const z = ft * FT;
      if (z > H - 1) continue;
      b.color(light).prism(circle(0, 0, w(z) / 2 + 1.6, 8), z, z + 1.1);
    }
  });
}
const LATTING_ANCHOR: V2 = [-73.983074, 40.754698];
const LATTING_FACTS = {
  Built: 'opened 1 Jul 1853 beside the Crystal Palace exhibition; Waring Latting, architect William Naugle',
  Height: '315 ft (96 m): the tallest structure in the city; octagonal iron-braced timber tower on a 75 ft square base, tapering to 6–8 ft; landings at 125, 225 and 300 ft',
  Fate: 'top 75 ft removed in 1855 by the Hydeville Marble Works; burned 30 Aug 1856',
  Model: 'LOW CONFIDENCE in position: sources give only "north side of 42nd Street between Fifth and Sixth avenues, opposite the Crystal Palace"; placed on the palace\'s cross axis. Dimensions cited; base building height (9 m) estimated'
};
const latting: Landmark = {
  id: 'latting_observatory_1853',
  name: 'Latting Observatory (1853–1855, full height)',
  kind: 'tower',
  built: [1853.0, 1853.5],
  end: 1855.5,
  anchor: LATTING_ANCHOR,
  build: b => buildLatting(b, 315 * FT),
  replaces: [rotRect(0, 0, 75 * FT + 2, 75 * FT + 2, GRID)],
  facts: LATTING_FACTS,
  sources: [WP + 'Latting_Observatory']
};
const lattingShort: Landmark = {
  id: 'latting_observatory_1855',
  name: 'Latting Observatory (1855–1856, shortened)',
  kind: 'tower',
  built: [1855.49, 1855.5],
  end: 1856.66,
  anchor: LATTING_ANCHOR,
  build: b => buildLatting(b, 240 * FT),
  replaces: [rotRect(0, 0, 75 * FT + 2, 75 * FT + 2, GRID)],
  facts: LATTING_FACTS,
  sources: [WP + 'Latting_Observatory']
};

// Croton Distributing Reservoir (1842–1900): OHM relation 2689733 — outer wall 137 × 115 m
// (15,700 m²; cited as four acres = 16,190 m²) and the two basins. Walls 50 ft high, 25 ft thick.
const CROTON_RING: V2[] = [
  [-17.1, 87.8],
  [83.3, 31.6],
  [16.8, -87.9],
  [-83.1, -31.7]
];
const crotonReservoir: Landmark = {
  id: 'croton_distributing_reservoir',
  name: 'Croton Distributing Reservoir (1842–1900)',
  kind: 'building',
  built: [1839.0, 1842.5],
  end: 1899.5,
  anchor: [-73.982246, 40.753205],
  build: b => {
    const granite = '#8B8782';
    const H = 50 * FT;
    const top = offset(CROTON_RING, -2.4); // battered Egyptian walls
    const basins: V2[][] = [
      [
        [-21.7, -47.8],
        [8.0, -64.5],
        [60.5, 31.6],
        [31.2, 46.6]
      ],
      [
        [-61.0, -25.0],
        [-31.3, -41.8],
        [21.2, 54.4],
        [-8.0, 69.4]
      ]
    ];
    b.color(granite).loft([CROTON_RING, top], [0, H], {top: false});
    b.color('#A9A49B').cap(top, H, basins);
    b.color('#77736E').walls(offset(top, 0.7), H - 1.6, H + 1.0);
    for (const basin of basins) {
      b.color('#6C6964').walls(basin, H - 5, H);
      b.color('#5C7F93').cap(basin, H - 1.4);
    }
    // corner pylons and the Fifth Avenue entrance pavilion
    b.frame(0, 0, 0, GRID, () => {
      b.color(granite);
      for (const sx of [-1, 1]) for (const sy of [-1, 1]) b.loft([rect(sx * 51.6, sy * 62.6, 11, 11), rect(sx * 51.6, sy * 62.6, 8.5, 8.5)], [0, H + 2.2]);
      b.loft([rect(54.3, 0, 6, 18), rect(53.4, 0, 5, 15)], [0, H + 3]);
      b.color('#3F3E3C').box(57.4, 0, 0, 0.3, 4.5, 7.5);
    });
  },
  replaces: [CROTON_RING],
  facts: {
    Built: '1839–1842; first filled 4 Jul 1842 with water from the Croton Aqueduct; 20 million gallons',
    Demolished: '1899–1900 for the New York Public Library, which reuses part of its foundations',
    Size: 'four acres (OpenHistoricalMap: 137 × 115 m), two basins; granite walls 50 ft high and 25 ft thick in an Egyptian style, with a public promenade on top',
    Site: 'Fifth Avenue between 40th and 42nd streets',
    Model: 'outline and basins from OpenHistoricalMap; wall height cited; batter of the walls and the corner pylons estimated from engravings'
  },
  sources: [WP + 'Croton_Distributing_Reservoir', OHMR + '2689733']
};

// ================================================================== 5. Madison Square Garden II and III
// MSG II (1890–1925): the block between Madison and Fourth (Park) avenues, 26th and 27th
// streets, today filled by the New York Life Building (city footprint BIN 1016880:
// 125.6 × 59.2 m = 412 × 194 ft). Wikipedia's "200 by 485 ft" cannot fit this block.
const MSG2_RING: V2[] = [
  [40.5, -56.2],
  [-69.3, 4.6],
  [-40.5, 56.3],
  [69.3, -4.6]
];
function buildMsg2(b: MeshBuilder) {
  const brick = '#E2D2A8';
  const terra = '#EFE6CC';
  const roofc = '#8C908C';
  const L = 125.6;
  const W = 59.2;
  b.frame(0, 0, 0, GRID, () => {
    const hx = L / 2;
    const hy = W / 2;
    // front section on Madison Avenue (theatre, concert hall, restaurant, roof garden)
    b.color(brick).box(-hx + 9.5, 0, 0, 19, W, 21);
    b.color('#B7B19C').cap(rect(-hx + 9.5, 0, 18, W - 1), 21.05);
    // amphitheatre: 200 × 350 ft hall under a pitched, skylit roof
    const aL = L - 19;
    b.color(brick).box(-hx + 19 + aL / 2, 0, 0, aL, W, 18);
    b.color(roofc).gable(-hx + 19 + aL / 2, 0, aL, W, 18, 6.5, false);
    b.color('#A9C0C4').box(-hx + 19 + aL / 2, 0, 24.2, aL - 16, 7, 0.9);
    hoops(b, rect(0, 0, L, W), 1, 17, 3, '#7F6F52', 0.3);
    // arcade over the Madison Avenue sidewalk and round the corners
    b.color(terra).box(-hx - 2.2, 0, 6.2, 4.4, W, 1.0);
    piers(b, -hx - 4, -hy + 1, -hx - 4, hy - 1, 14, 0.8, 0, 6.2);
    // roof-garden cupolas: two large at the Madison Avenue corners, smaller ones along the sides
    for (const s of [-1, 1]) {
      b.color(terra).cylinder(-hx + 5, s * (hy - 5), 3.2, 21, 27, 8);
      b.color('#B9A36A').dome(-hx + 5, s * (hy - 5), 3.4, 27, 3.4, 8, 3);
      for (const x of [-hx + 30, -hx + 62, hx - 6]) {
        b.color(terra).cylinder(x, s * (hy - 3), 1.8, 18, 22.5, 8);
        b.color('#B9A36A').dome(x, s * (hy - 3), 2.0, 22.5, 2, 8, 3);
      }
    }
    // tower on the 26th Street side, after the Giralda of Seville: 304 ft
    const T = 304 * FT;
    const tx = -hx + 36;
    const ty = -hy + 6.2;
    const tw = 11.6;
    b.color(brick).box(tx, ty, 0, tw, tw, 62);
    hoops(b, rect(tx, ty, tw, tw), 22, 61, 9, '#7F6F52', 0.25);
    b.color(terra).box(tx, ty, 62, tw + 2.2, tw + 2.2, 1.2);
    b.box(tx, ty, 63.2, tw - 2.4, tw - 2.4, 9.5);
    b.box(tx, ty, 72.7, tw - 0.8, tw - 0.8, 0.9);
    b.cylinder(tx, ty, 3.4, 73.6, 81.5, 8);
    b.cylinder(tx, ty, 2.5, 81.5, 87.5, 8);
    b.color('#B9A36A').dome(tx, ty, 2.7, 87.5, T - 87.5, 8, 4);
    for (const sx of [-1, 1]) for (const sy of [-1, 1]) b.color(terra).cylinder(tx + sx * (tw / 2 - 1), ty + sy * (tw / 2 - 1), 1.1, 63.2, 69, 6);
    // Saint-Gaudens's Diana (second version, 13 ft)
    b.color('#D8B648').beam([tx, ty, T], [tx, ty, T + 13 * FT], 0.5);
  });
}
const msg2: Landmark = {
  id: 'madison_square_garden_1890',
  name: 'Madison Square Garden II (1890–1925)',
  kind: 'building',
  built: [1889.5, 1890.46],
  end: 1925.4,
  anchor: [-73.985583, 40.742754],
  build: buildMsg2,
  replaces: [MSG2_RING],
  facts: {
    Built: '1889–1890; opened 16 Jun 1890; Stanford White (McKim, Mead & White)',
    Demolished: '1925–1926 for the New York Life Building',
    Tower: '304 ft (93 m) to the observation deck, modelled on the Giralda of Seville, crowned by Saint-Gaudens\'s Diana (18 ft in 1891, 13 ft from 1893)',
    Hall: 'amphitheatre 200 × 350 ft, 8,000 permanent seats; theatre, concert hall, restaurant and roof garden',
    Site: 'the whole block, Madison to Fourth Avenue, 26th to 27th Street: 412 × 194 ft measured on today\'s lot (Wikipedia gives 200 × 485 ft, longer than the block)',
    Model: 'LOW CONFIDENCE in heights: only the tower height is cited; wall and roof heights (18–24 m), the tower\'s width (11.6 m) and its stages are estimated from photographs'
  },
  sources: [WP + 'Madison_Square_Garden_(1890)', 'https://thearchitectureprofessor.com/2021/09/16/1-6-madison-square-garden/']
};

// MSG III (1925–1968): OHM way 198759004 (Bromley 1930): 147.3 × 61.0 m lot from Eighth
// Avenue west between 49th and 50th streets; the arena itself was 200 × 375 ft.
const MSG3_RING: V2[] = [
  [-49.3, 62.2],
  [79.2, -9.0],
  [49.4, -62.2],
  [-79.2, 9.0]
];
const msg3: Landmark = {
  id: 'madison_square_garden_1925',
  name: 'Madison Square Garden III (1925–1968)',
  kind: 'building',
  built: [1925.03, 1925.95],
  end: 1968.5,
  anchor: [-73.987253, 40.762362],
  build: b => {
    const brick = '#B49A7E';
    const L = 147.3;
    const W = 61.0;
    const aL = 375 * FT;
    b.frame(0, 0, 0, GRID, () => {
      // arena box, 200 × 375 ft, at the west end of the lot
      const ax = -L / 2 + aL / 2;
      b.color(brick).box(ax, 0, 0, aL, W, 21);
      b.color('#70757A');
      vault(b, ax, 0, aL - 2, W - 2, 21, 5.5, false, 6);
      hoops(b, rect(ax, 0, aL, W), 2, 20, 3, '#6B5A49', 0.25);
      // entrance building and marquee on Eighth Avenue
      const fx = (-L / 2 + aL + L / 2) / 2;
      b.color('#C5B299').box(fx, 0, 0, L - aL, 30, 17);
      b.color(brick).box(fx, 22.75, 0, L - aL, 15.5, 12).box(fx, -22.75, 0, L - aL, 15.5, 12);
      b.color('#3B3F45').box(L / 2 + 2, 0, 5, 5, 26, 1.6);
    });
  },
  replaces: [MSG3_RING],
  facts: {
    Built: 'begun 9 Jan 1925; opened 15 Dec 1925 (Tex Rickard; architect Thomas W. Lamb)',
    Closed: '11 Feb 1968; demolished 1968–1969',
    Size: 'arena 200 × 375 ft (61 × 114 m), three tiers of seats, 18,496 for boxing',
    Site: 'west side of Eighth Avenue between 49th and 50th streets; lot 147 × 61 m (OpenHistoricalMap, Bromley 1930)',
    Model: 'LOW CONFIDENCE in heights: plan cited, wall and roof heights (21–27 m) estimated from photographs'
  },
  sources: [WP + 'Madison_Square_Garden_(1925)', OHMW + '198759004']
};

// ================================================================== 6. Ballparks
// Sites and playing fields from OpenHistoricalMap; fence distances from the Wikipedia
// articles. No published heights were found for any of the grandstands: they are
// estimated from the number of decks and named so in each model's facts.

/** A ring given in metres around the landmark anchor, expressed in the frame at `o` whose +y points at `bearing`. */
function toFrame(ring: V2[], o: V2, bearing: number): V2[] {
  const a = (-bearing * Math.PI) / 180;
  const c = Math.cos(a);
  const s = Math.sin(a);
  return ring.map(([x, y]) => {
    const dx = x - o[0];
    const dy = y - o[1];
    return [c * dx + s * dy, -s * dx + c * dy] as V2;
  });
}

function densify(r: V2[], step: number): V2[] {
  const out: V2[] = [];
  for (let i = 0; i < r.length; i++) {
    const a = r[i];
    const c = r[(i + 1) % r.length];
    const n = Math.max(1, Math.ceil(Math.hypot(c[0] - a[0], c[1] - a[1]) / step));
    for (let k = 0; k < n; k++) out.push([a[0] + ((c[0] - a[0]) * k) / n, a[1] + ((c[1] - a[1]) * k) / n]);
  }
  return out;
}

/** Distance along the ray p + t·d to the outline `poly` (Infinity if it misses). */
function rayHit(p: V2, d: V2, poly: V2[]): number {
  let best = Infinity;
  for (let i = 0; i < poly.length; i++) {
    const a = poly[i];
    const c = poly[(i + 1) % poly.length];
    const ex = c[0] - a[0];
    const ey = c[1] - a[1];
    const den = d[0] * ey - d[1] * ex;
    if (Math.abs(den) < 1e-9) continue;
    const t = ((a[0] - p[0]) * ey - (a[1] - p[1]) * ex) / den;
    const u = ((a[0] - p[0]) * d[1] - (a[1] - p[1]) * d[0]) / den;
    if (t > 0.05 && u >= -1e-6 && u <= 1 + 1e-6) best = Math.min(best, t);
  }
  return best;
}

/** Fair-territory fence from home (field frame: +y = centre field, +x = right field); distances LF, LC, CF, RC, RF. */
function fenceArc(f: number[], n = 24): V2[] {
  const angs = [-45, -22.5, 0, 22.5, 45];
  const pts: V2[] = [];
  for (let i = 0; i <= n; i++) {
    const a = -45 + (90 * i) / n;
    let k = 0;
    while (k < 3 && a > angs[k + 1]) k++;
    const t = (a - angs[k]) / (angs[k + 1] - angs[k]);
    const r = f[k] + (f[k + 1] - f[k]) * (0.5 - 0.5 * Math.cos(Math.PI * t));
    const rad = (a * Math.PI) / 180;
    pts.push([Math.sin(rad) * r, Math.cos(rad) * r]);
  }
  return pts;
}

/** Edge of foul territory `off` metres outside the foul lines: down the LF line, behind home, up the RF line. */
function foulPath(off: number, lfEnd: number, rfEnd: number, n = 10): V2[] {
  const s2 = Math.SQRT1_2;
  const pts: V2[] = [];
  for (let i = 0; i <= n; i++) {
    const s = lfEnd * (1 - i / n);
    pts.push([-s2 * s - s2 * off, s2 * s - s2 * off]);
  }
  for (let i = 1; i < n; i++) {
    const a = (-135 + (90 * i) / n) * (Math.PI / 180);
    pts.push([Math.cos(a) * off, Math.sin(a) * off]);
  }
  for (let i = 0; i <= n; i++) {
    const s = (rfEnd * i) / n;
    pts.push([s2 * s + s2 * off, s2 * s - s2 * off]);
  }
  return pts;
}

/** Pull the points of a field ring that fall outside the site back toward home plate (the origin), `margin` inside the outline. */
function clipToSite(field: V2[], site: V2[], margin: number): V2[] {
  return field.map(p => {
    const l = Math.hypot(p[0], p[1]);
    if (l < 1e-6) return p;
    const d: V2 = [p[0] / l, p[1] / l];
    const t = rayHit([0, 0], d, site);
    return l > t - margin ? ([d[0] * (t - margin), d[1] * (t - margin)] as V2) : p;
  });
}

type Tier = {top: number; roof?: number; depth?: number};
type ParkColors = {seats: string; wall: string; roof: string};

/**
 * Stands between the edge of the playing field and the site outline (both in the field
 * frame: home plate at the origin, +y to centre field). `tierAt` gives, for a point of the
 * field edge and its angle from the centre-field axis (degrees, + toward right field), the
 * height of the back row, the roof height if roofed and the greatest depth of the stand.
 */
function bowl(b: MeshBuilder, field: V2[], site: V2[], tierAt: (ang: number, p: V2) => Tier | null, c: ParkColors) {
  const F = densify(field, 7);
  const N = offset(F, 1);
  const n = F.length;
  const O: V2[] = [];
  const T: (Tier | null)[] = [];
  for (let i = 0; i < n; i++) {
    const d = norm([N[i][0] - F[i][0], N[i][1] - F[i][1]]);
    const t = tierAt((Math.atan2(F[i][0], F[i][1]) * 180) / Math.PI, F[i]);
    const hit = rayHit(F[i], d, site);
    const depth = Math.min(isFinite(hit) ? hit - 0.3 : 0, t?.depth ?? 1e9);
    T.push(t && depth > 3 ? t : null);
    O.push([F[i][0] + d[0] * depth, F[i][1] + d[1] * depth]);
  }
  const at = (i: number, f: number, z: number): V3 => [F[i][0] + (O[i][0] - F[i][0]) * f, F[i][1] + (O[i][1] - F[i][1]) * f, z];
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    const ti = T[i];
    const tj = T[j];
    if (!ti || !tj) {
      const k = ti ? i : tj ? j : -1;
      const t = ti ?? tj;
      if (k >= 0 && t) b.color(c.wall).quad(at(k, 0, 0), at(k, 1, 0), at(k, 1, t.roof ?? t.top), at(k, 0, 2.5));
      continue;
    }
    const decked = ti.top > 14 && tj.top > 14;
    b.color(c.wall).quad(at(i, 0, 0), at(j, 0, 0), at(j, 0, 2.5), at(i, 0, 2.5));
    b.quad(at(i, 1, 0), at(j, 1, 0), at(j, 1, tj.roof ?? tj.top), at(i, 1, ti.roof ?? ti.top));
    b.color(c.seats);
    if (decked) {
      b.quad(at(i, 0, 2.5), at(j, 0, 2.5), at(j, 0.6, tj.top * 0.45), at(i, 0.6, ti.top * 0.45));
      b.quad(at(i, 0.32, ti.top * 0.52), at(j, 0.32, tj.top * 0.52), at(j, 1, tj.top), at(i, 1, ti.top));
      b.color(c.wall).quad(at(i, 0.32, ti.top * 0.52 - 2.2), at(j, 0.32, tj.top * 0.52 - 2.2), at(j, 0.32, tj.top * 0.52), at(i, 0.32, ti.top * 0.52));
    } else b.quad(at(i, 0, 2.5), at(j, 0, 2.5), at(j, 1, tj.top), at(i, 1, ti.top));
    if (ti.roof && tj.roof) {
      b.color(c.roof).quad(at(i, 0.3, ti.roof), at(j, 0.3, tj.roof), at(j, 1, tj.roof), at(i, 1, ti.roof));
      b.color(c.wall).quad(at(i, 0.3, ti.roof - 1.6), at(j, 0.3, tj.roof - 1.6), at(j, 0.3, tj.roof), at(i, 0.3, ti.roof));
    }
  }
}

function diamond(b: MeshBuilder, field: V2[], grass: string, dirt: string) {
  b.color(grass).cap(field, 0.3);
  const d = 90 * FT * Math.SQRT1_2;
  b.color(dirt).cap(
    [
      [0, -4],
      [d + 5, d - 2],
      [0, 2 * d + 7],
      [-d - 5, d - 2]
    ],
    0.4
  );
  b.color(grass).cap(
    [
      [0, 3],
      [d - 4, d],
      [0, 2 * d - 3],
      [-d + 4, d]
    ],
    0.5
  );
  b.color(dirt).cylinder(0, 60.5 * FT, 2.7, 0.4, 0.75, 10);
}

const GRASS = '#4E8B3A';
const DIRT = '#B9906A';

// ---- Polo Grounds (1911 steel-and-concrete stand; double deck carried round in 1923; demolished 1964)
// OHM way 198180427 (the horseshoe of stands) and way 198180426 (the field). Home plate
// lies on the horseshoe's axis (bearing 119°: Coogan's Bluff behind, the Harlem River and
// Yankee Stadium beyond centre field), 16 m in front of the backstop.
const POLO_ANCHOR: V2 = [-73.936967, 40.831549];
const POLO_HOME: V2 = [-71.9, 35.3];
const POLO_CF = 119;
const POLO_FIELD: V2[] = [
  [8.9, -61.4],
  [-1.8, -59.3],
  [-75.8, -18.6],
  [-81.6, -11.5],
  [-88.7, 4.6],
  [-91.0, 23.5],
  [-90.2, 35.1],
  [-80.6, 52.9],
  [-72.0, 61.0],
  [-62.6, 66.5],
  [-52.7, 68.3],
  [-39.5, 68.0],
  [-25.8, 65.5],
  [48.9, 24.2],
  [51.7, 19.4],
  [52.7, 13.6],
  [50.7, 6.9],
  [16.5, -54.5]
];
const POLO_SITE: V2[] = [
  [108.5, 17.4],
  [-14.8, 85.7],
  [-27.7, 90.0],
  [-39.2, 91.4],
  [-67.1, 86.4],
  [-87.2, 75.8],
  [-106.6, 53.0],
  [-113.0, 33.7],
  [-113.0, 10.2],
  [-110.9, -0.4],
  [-96.5, -28.2],
  [-88.2, -34.8],
  [39.0, -108.0],
  [58.3, -71.7],
  [78.4, -36.0]
];
function buildPoloGrounds(b: MeshBuilder, full: boolean) {
  const c: ParkColors = {seats: '#3D6B4F', wall: '#B9B2A2', roof: '#5E6B62'};
  b.frame(POLO_HOME[0], POLO_HOME[1], 0, POLO_CF, () => {
    const field = toFrame(POLO_FIELD, POLO_HOME, POLO_CF);
    const site = toFrame(POLO_SITE, POLO_HOME, POLO_CF);
    diamond(b, field, GRASS, DIRT);
    bowl(
      b,
      field,
      site,
      ang => {
        const a = Math.abs(ang);
        if (full) return a < 22 ? (Math.abs(ang - 3) < 7 ? null : {top: 10}) : {top: 19, roof: 23};
        return a < 55 ? {top: 6, depth: 14} : {top: 19, roof: 23};
      },
      c
    );
    if (full) {
      // centre-field clubhouse between the bleachers, its front 483 ft from the plate
      b.color('#5A7A62').box(6, 483 * FT + 9, 0, 34, 18, 17);
      b.color('#2F3F35').box(6, 483 * FT - 0.2, 9, 30, 0.4, 7);
    }
  });
}
const POLO_FACTS = {
  Site: 'Coogan\'s Hollow, Eighth Avenue at 155th–159th streets, under Coogan\'s Bluff',
  Field: 'left 279 ft, right 258 ft, 450 ft to the gaps, 483 ft to the clubhouse in centre; "the Bathtub"',
  Teams: 'Giants (to 1957), Yankees (1913–22), Mets (1962–63), football Giants and Jets'
};
const poloGrounds1911: Landmark = {
  id: 'polo_grounds_1911',
  name: 'Polo Grounds (1911–1923)',
  kind: 'stadium',
  built: [1911.3, 1911.5],
  end: 1923.3,
  anchor: POLO_ANCHOR,
  build: b => buildPoloGrounds(b, false),
  replaces: [POLO_SITE],
  facts: {
    Built: 'steel-and-concrete double-deck stand built after the fire of 14 Apr 1911; reopened 28 Jun 1911',
    ...POLO_FACTS,
    Model: 'LOW CONFIDENCE: outlines from OpenHistoricalMap (field 98 m wide where the cited foul lines imply about 115 m); extent of the 1911 deck, the wooden outfield bleachers and all heights (roof about 23 m) estimated'
  },
  sources: [WP + 'Polo_Grounds', OHMW + '198180427', OHMW + '198180426']
};
const poloGrounds1923: Landmark = {
  id: 'polo_grounds_1923',
  name: 'Polo Grounds (1923–1964)',
  kind: 'stadium',
  built: [1923.29, 1923.3],
  end: 1964.27,
  anchor: POLO_ANCHOR,
  build: b => buildPoloGrounds(b, true),
  replaces: [POLO_SITE],
  facts: {
    Built: 'double deck extended around the field in 1923, with new bleachers and clubhouse across centre field',
    Demolished: 'from 10 Apr 1964, for the Polo Grounds Towers',
    ...POLO_FACTS,
    Model: 'LOW CONFIDENCE: outlines from OpenHistoricalMap (field 98 m wide where the cited foul lines imply about 115 m); home plate placed on the horseshoe axis; all heights (roof about 23 m, clubhouse 17 m) estimated'
  },
  sources: [WP + 'Polo_Grounds', OHMW + '198180427', OHMW + '198180426']
};

// ---- Ebbets Field (1913–1960): the block Bedford Avenue / Sullivan Place / McKeever Place /
// Montgomery Street (OHM relation 2690259, 22,100 m²). Right-field line parallel to
// Sullivan Place, 297 ft to the Bedford Avenue wall; rotunda at the Sullivan–McKeever corner.
const EBBETS_SITE: V2[] = [
  [-87.8, -70.8],
  [-44.3, 80.0],
  [-18.0, 93.0],
  [77.6, 66.0],
  [86.6, 50.3],
  [54.5, -72.6],
  [-78.7, -83.8],
  [-84.2, -81.1],
  [-87.3, -77.1]
];
const EBBETS_HOME: V2 = [-25.1, -39.3];
const EBBETS_CF = 40.3;
const ebbetsField: Landmark = {
  id: 'ebbets_field_1913',
  name: 'Ebbets Field (1913–1960)',
  kind: 'stadium',
  built: [1912.2, 1913.27],
  end: 1960.15,
  anchor: [-73.958047, 40.665028],
  build: b => {
    const c: ParkColors = {seats: '#3F5F7A', wall: '#C2A98A', roof: '#59645F'};
    b.frame(EBBETS_HOME[0], EBBETS_HOME[1], 0, EBBETS_CF, () => {
      const site = toFrame(EBBETS_SITE, EBBETS_HOME, EBBETS_CF);
      // 356 ft to left and 406 ft to centre after the 1931 stands, 297 ft to right; the gaps are interpolated
      const fence = clipToSite(fenceArc([356 * FT, 370 * FT, 406 * FT, 352 * FT, 297 * FT]), site, 1.2);
      const field = clipToSite([...foulPath(15, 356 * FT, 297 * FT), ...fence.slice().reverse()], site, 1.2);
      diamond(b, field, GRASS, DIRT);
      bowl(b, field, site, ang => (ang > 4 && ang < 52 ? null : {top: 19, roof: 23}), c);
      // right field: the Bedford Avenue wall with its screen, and the scoreboard
      const rf = fence.filter(([x, y]) => Math.atan2(x, y) > 0.12);
      b.color('#6F7F74').wallProfile(rf, 0, 38 * FT);
      const sb = rf[Math.floor(rf.length / 2)];
      b.color('#2E3A36').box(sb[0] - 1, sb[1] - 1, 0, 3, 14, 12.5);
    });
    // rotunda at the home-plate corner
    b.color('#C2A98A').cylinder(-71.5, -67.5, 11.5, 0, 24.5, 14);
    b.color('#59645F').dome(-71.5, -67.5, 11.7, 24.5, 2.5, 14, 3);
  },
  replaces: [EBBETS_SITE],
  facts: {
    Built: 'groundbreaking 4 Mar 1912; opened 9 Apr 1913 (Charles Ebbets; architect Clarence Van Buskirk)',
    Demolished: 'from 23 Feb 1960, for the Ebbets Field Apartments',
    Field: 'right 297 ft to the Bedford Avenue wall; left 419 ft and centre 508 ft in 1913, 356 ft and 406 ft after the 1931 double deck across left and centre',
    Site: 'the block Bedford Avenue, Sullivan Place, McKeever Place, Montgomery Street (OpenHistoricalMap, 22,100 m²)',
    Model: 'LOW CONFIDENCE: block outline and cited fence distances are real; home plate is placed from the right-field distance and the street lines (± 8 m); deck and roof heights (about 23 m), the wall height (38 ft) and the rotunda (23 m across) are estimated; shown throughout in its form after 1931'
  },
  sources: [WP + 'Ebbets_Field', OHMR + '2690259']
};

// ---- Yankee Stadium (1923–1973; rebuilt 1974–76; demolished 2009–10): OHM relation 2690448.
// Home plate on the bisector of the mapped field, 82 ft from the backstop, centre field due
// east (91°): the cited foul lines (281 ft left, 295 ft right) then end on the mapped stands
// within 5 m, and 490 ft to centre reaches the bleacher wall.
const YANKEE_SITE: V2[] = [
  [23.8, 100.3],
  [-94.6, 47.4],
  [-117.7, 21.4],
  [-120.8, -3.3],
  [-111.3, -35.2],
  [-101.4, -51.4],
  [10.7, -105.7],
  [26.5, -108.4],
  [41.4, -103.0],
  [59.5, -92.2],
  [111.0, 37.1],
  [107.4, 53.2],
  [99.2, 69.4],
  [92.0, 77.0],
  [78.4, 86.0],
  [55.4, 96.8]
];
const YANKEE_FIELD: V2[] = [
  [-68.4, 17.5],
  [23.8, 58.8],
  [50.9, 58.8],
  [67.2, 43.6],
  [75.3, 30.1],
  [50.9, -57.0],
  [34.6, -68.6],
  [12.9, -68.6],
  [-71.1, -27.3],
  [-81.1, -13.0],
  [-81.1, 1.4]
];
const YANKEE_HOME: V2 = [-56.1, -6.2];
const YANKEE_CF = 91;
function buildYankeeStadium(b: MeshBuilder, rebuilt: boolean) {
  const c: ParkColors = {seats: rebuilt ? '#2B4C7E' : '#4F7A5C', wall: '#D8D2C2', roof: '#6F8F84'};
  b.frame(YANKEE_HOME[0], YANKEE_HOME[1], 0, YANKEE_CF, () => {
    const field = toFrame(YANKEE_FIELD, YANKEE_HOME, YANKEE_CF);
    const site = toFrame(YANKEE_SITE, YANKEE_HOME, YANKEE_CF);
    diamond(b, field, GRASS, DIRT);
    bowl(b, field, site, ang => (Math.abs(ang) > 36 ? (rebuilt ? {top: 117 * FT} : {top: 31.5, roof: 117 * FT}) : {top: 11}), c);
  });
}
const YANKEE_SRC = [WP + 'Yankee_Stadium_(1923)', OHMR + '2690448'];
const yankeeStadium1923: Landmark = {
  id: 'yankee_stadium_1923',
  name: 'Yankee Stadium (1923–1973)',
  kind: 'stadium',
  built: [1922.35, 1923.3],
  end: 1973.75,
  anchor: [-73.928003, 40.826893],
  build: b => buildYankeeStadium(b, false),
  replaces: [YANKEE_SITE],
  facts: {
    Built: 'begun 5 May 1922; opened 18 Apr 1923 (Osborn Engineering); the first three-tiered ballpark',
    Grandstand: 'triple deck with a 15 ft copper frieze along the roof; carried round left field in 1927–28 and right field in 1937',
    Field: 'right 295 ft, left 281 ft, 490 ft to deepest centre ("Death Valley"); backstop 82 ft',
    Site: 'River Avenue and East 161st Street, the Bronx (OpenHistoricalMap, 32,900 m²)',
    Model: 'LOW CONFIDENCE in heights: outlines from OpenHistoricalMap and the cited field distances fix the plan; the roof is set at the 117 ft given for the frieze by one magazine account, the decks below it are estimated; shown throughout with the 1937 extent of the decks'
  },
  sources: [...YANKEE_SRC, 'https://www.americanheritage.com/node/133629']
};
const yankeeStadium1976: Landmark = {
  id: 'yankee_stadium_1976',
  name: 'Yankee Stadium (rebuilt 1976–2009)',
  kind: 'stadium',
  built: [1973.76, 1976.29],
  end: 2010.0,
  anchor: [-73.928003, 40.826893],
  build: b => buildYankeeStadium(b, true),
  replaces: [YANKEE_SITE],
  facts: {
    Rebuilt: '30 Sep 1973 – 15 Apr 1976: roof and its frieze removed, upper deck rebuilt nine rows higher, field lowered about 7 ft',
    Closed: 'last game 21 Sep 2008; demolished Nov 2009 – May 2010; the site is Heritage Field',
    Site: 'River Avenue and East 161st Street, the Bronx (OpenHistoricalMap outline)',
    Model: 'LOW CONFIDENCE in heights: same outline as the 1923 stadium; the height of the rebuilt upper deck is estimated (drawn at the old roof line, 117 ft)'
  },
  sources: YANKEE_SRC
};

// ---- Shea Stadium (1964–2009): OHM relation 2691041, a circle 233 m across. Orientation
// estimated: the left-field bleachers mapped in OHM (way 201437224, 1980–2009) put centre
// field at about bearing 60° and home plate about 50 m from the centre of the circle.
const SHEA_HOME: V2 = [-43.3, -25.0];
const SHEA_CF = 60;
const sheaStadium: Landmark = {
  id: 'shea_stadium_1964',
  name: 'Shea Stadium (1964–2009)',
  kind: 'stadium',
  built: [1961.82, 1964.29],
  end: 2009.13,
  anchor: [-73.847767, 40.755688],
  build: b => {
    const c: ParkColors = {seats: '#C7623A', wall: '#C9CCCB', roof: '#8C9498'};
    b.frame(SHEA_HOME[0], SHEA_HOME[1], 0, SHEA_CF, () => {
      const site = circle(0, 50, 116.5, 48);
      const fence = fenceArc([341 * FT, 371 * FT, 410 * FT, 371 * FT, 341 * FT]);
      const field = [...foulPath(18, 341 * FT, 341 * FT), ...fence.slice().reverse()];
      diamond(b, field, GRASS, DIRT);
      bowl(b, field, site, ang => (Math.abs(ang) > 46 ? {top: 34} : null), c);
      b.color('#31508A').wallProfile(fence, 0, 2.5);
      // scoreboard beyond right-centre
      b.color('#2E3338').box(52, 128, 0, 26, 3, 24);
    });
  },
  replaces: [circle(0, 0, 117, 40)],
  facts: {
    Built: 'groundbreaking 28 Oct 1961; opened 17 Apr 1964 (Praeger-Kavanagh-Waterbury)',
    Demolished: 'Oct 2008 – 18 Feb 2009; the site is Citi Field\'s parking',
    Field: '341 ft down both lines, 410 ft to centre (338 ft lines from 1978)',
    Plan: 'circular, 233 m across (OpenHistoricalMap), open beyond the outfield; five seating levels',
    Model: 'LOW CONFIDENCE: outline and fence distances cited; the direction of centre field (about 60°) and home plate are inferred from the mapped left-field bleachers (± 10°); the height of the stands (about 34 m) is estimated'
  },
  sources: [WP + 'Shea_Stadium', OHMR + '2691041', OHMW + '201437224']
};

const LOST_PART2: Landmark[] = [crystalPalace, latting, lattingShort, crotonReservoir, msg2, msg3, poloGrounds1911, poloGrounds1923, ebbetsField, yankeeStadium1923, yankeeStadium1976, sheaStadium];

// ================================================================== 7. New Amsterdam and colonial New York
/** Walls of `ring` to the eaves and a hipped roof rising to a ring inset by `inset`. */
function roofed(b: MeshBuilder, ring: V2[], eave: number, rise: number, inset: number, wall: string, roof: string) {
  b.color(wall).prism(ring, 0, eave, {top: false});
  b.color(roof).loft([ring, offset(ring, -inset)], [eave, eave + rise]);
}

// Fort Amsterdam (1625/35–1790; Fort James, Fort George): OHM relation 2690942, traced from
// the Castello Plan of 1660 (mapwarper 4625): the bastioned trace (5,730 m², 105 m across
// the bastion points, curtains about 62 × 55 m) and the parade inside it, with the
// barracks, the secretary's house, the governor's house and the church.
const FORT_OUTER: V2[] = [
  [-33.7, -28.7],
  [-35.1, -39.4],
  [-59.6, -42.7],
  [-49.3, -22.2],
  [-34.2, -23.1],
  [-27.7, 26.1],
  [-39.3, 28.7],
  [-44.3, 60.7],
  [-20.7, 46.3],
  [-21.4, 34.0],
  [32.4, 28.4],
  [34.2, 37.4],
  [58.9, 41.4],
  [45.2, 18.2],
  [37.0, 19.4],
  [29.7, -28.7],
  [38.7, -29.9],
  [38.5, -56.5],
  [16.9, -43.7],
  [16.7, -36.0]
];
const FORT_INNER: V2[] = [
  [-27.2, -17.8],
  [-25.1, -24.3],
  [19.6, -31.7],
  [24.7, -27.6],
  [31.3, 20.5],
  [29.0, 24.5],
  [9.4, 26.2],
  [-19.5, 30.1],
  [-23.3, 24.2]
];
function dutchHouse(b: MeshBuilder, cx: number, cy: number, bearing: number, w: number, l: number, eave: number, ridge: number) {
  b.frame(cx, cy, 0, bearing, () => {
    b.color('#B89A7C').box(0, 0, 0, w, l, eave, {top: false});
    b.color('#8E4B36').gable(0, 0, w, l, eave, ridge - eave, true);
  });
}
const fortAmsterdam: Landmark = {
  id: 'fort_amsterdam',
  name: 'Fort Amsterdam (Fort James, Fort George; 1625–1790)',
  kind: 'building',
  built: [1625.5, 1635.0],
  end: 1790.0,
  anchor: [-74.014026, 40.704149],
  build: b => {
    const H = 4.5; // rampart height: estimated
    b.color('#8F8A72').loft([FORT_OUTER, offset(FORT_OUTER, -0.9)], [0, H], {top: false});
    b.color('#A39C80').cap(offset(FORT_OUTER, -0.9), H, [FORT_INNER]);
    b.color('#8F8A72').walls(FORT_INNER, 0.3, H);
    b.color('#9B9273').cap(FORT_INNER, 0.3);
    b.color('#7E7A66').walls(offset(FORT_OUTER, -1.3), H, H + 1.1);
    // gate in the north curtain, toward the Bowling Green
    b.color('#6B5A45').box(5.4, 28.2, 0, 4.2, 5.0, H + 2.6);
    // barracks, secretary's house and governor's house as on the Castello Plan
    dutchHouse(b, -18.1, -7.0, 6.0, 10.9, 24.3, 5.5, 9);
    dutchHouse(b, -8.3, 20.8, 96.0, 8.8, 21.2, 5.5, 8.5);
    dutchHouse(b, 21.1, 3.3, 7.6, 9.9, 17.1, 6, 9.5);
    // flagstaff on the south-west bastion
    b.color('#D8D2C0').beam([-45, -34, H], [-45, -34, H + 16], 0.3);
    b.color('#E8842C').box(-43.6, -34, H + 13, 2.8, 0.1, 1.6);
  },
  replaces: [FORT_OUTER],
  facts: {
    Built: 'laid out 1625 by Cryn Fredericks for the West India Company; the four-bastioned fort finished about 1635',
    Names: 'Fort Amsterdam; Fort James (1664); Willem Hendrick (1673); Fort William Henry, Fort Anne, Fort George (to 1783)',
    Demolished: '1790, for the Government House; the Custom House stands on the site',
    Plan: 'four sides with a bastion at each corner; barracks, church, the director\'s house and a warehouse inside',
    Model: 'LOW CONFIDENCE in heights: plan and the buildings inside from OpenHistoricalMap\'s tracing of the Castello Plan (1660); rampart (4.5 m) and house heights are estimated'
  },
  sources: [WP + 'Fort_Amsterdam', OHMR + '2690942', WP + 'Castello_Plan']
};

const fortChurch: Landmark = {
  id: 'fort_amsterdam_church_1642',
  name: 'Church in the Fort (St. Nicholas, 1642–1741)',
  kind: 'building',
  built: [1642.33, 1643.5],
  end: 1741.21,
  anchor: [-74.013806, 40.704013],
  build: b => {
    b.frame(0, 0, 0, 7.7, () => {
      // 1642 contract: 72 ft long, 52 ft broad, 16 ft high above the ground; the Castello Plan
      // draws it with twin gabled roofs and a turret (its tracing measures 20.1 × 9.9 m)
      const w = 52 * FT;
      const l = 72 * FT;
      const h = 16 * FT;
      b.color('#A79C8C').box(0, 0, 0, w, l, h, {top: false});
      b.color('#6E5A48').gable(-w / 4, 0, w / 2, l, h, 5, true).gable(w / 4, 0, w / 2, l, h, 5, true);
      b.color('#A79C8C').box(0, l / 2 - 2.2, h, 2.6, 2.6, 8);
      b.color('#6E5A48').pyramid(rect(0, l / 2 - 2.2, 3, 3), h + 8, [0, l / 2 - 2.2, h + 12.5]);
    });
  },
  replaces: [rotRect(0, 0, 52 * FT, 72 * FT, 7.7)],
  facts: {
    Built: 'stone church contracted by Director Kieft with John and Richard Ogden of Stamford on 1 May 1642 for 2,500 guilders, for the Dutch Reformed congregation',
    Destroyed: 'burned with the fort\'s buildings in the fires of 1741',
    Size: '72 ft long, 52 ft broad and 16 ft high above the ground, by the contract (New York State Archives)',
    Model: 'contract dimensions on the position and axis of OpenHistoricalMap\'s tracing of the Castello Plan (which draws it 20.1 × 9.9 m); the twin gabled roofs (5 m) and the turret are estimated from the plan\'s drawing'
  },
  sources: ['https://encyclopedia.nahc-mapping.org/document/contract-john-and-richard-ogden-stamford-connecticut-build-stone-church-fort-amsterdam', OHMW + '198590262', WP + 'Castello_Plan']
};

const stadtHuys: Landmark = {
  id: 'stadt_huys_1642',
  name: 'Stadt Huys (City Tavern 1642; city hall 1653–1699)',
  kind: 'building',
  built: [1641.5, 1642.5],
  end: 1699.5,
  anchor: [-74.010705, 40.703813],
  build: b => {
    b.frame(0, 0, 0, 62.3, () => {
      // foundations found in 1979–80: about 42 × 52 ft; five storeys (three under the eaves, two in the roof)
      const w = 42 * FT;
      const l = 52 * FT;
      b.color('#A8987E').box(0, 0, 0, w, l, 10, {top: false});
      b.color('#8E4B36').gable(0, 0, w, l, 10, 7, true);
      // stepped gable ends and the bell cupola
      b.color('#A8987E');
      for (const s of [-1, 1]) for (let k = 0; k < 5; k++) b.box(0, s * (l / 2 - 0.2), 10, w - k * 2.6, 0.4, 1.45 * (k + 1));
      b.box(0, 0, 17, 1.4, 1.4, 2.4);
      hoops(b, rect(0, 0, w, l), 0.5, 10, 3, '#4A3F36', 0.3);
    });
  },
  replaces: [rotRect(0, 0, 42 * FT, 52 * FT, 62.3)],
  facts: {
    Built: 'the West India Company\'s stone City Tavern, 1642, on the East River shore at Pearl Street',
    Use: 'Stadt Huys (city hall) of New Amsterdam from 1653, when a cupola was added and the entrance turned to the river; seat of government to 1699',
    Size: 'foundations of about 42 × 52 ft found in the 1979–80 excavation (85 Broad Street); five storeys',
    Model: 'LOW CONFIDENCE: position and axis from OpenHistoricalMap\'s tracing of the Castello Plan (which draws it only 11.8 × 6.5 m); the footprint is from a single popular account of the excavation, its long side set along Pearl Street; heights (10 m eaves, 17 m ridge) estimated from the storey count and the 1679 Danckaerts view'
  },
  sources: [WP + 'Stadt_Huys_Site', 'https://www.waymarking.com/waymarks/WM31V1_Unearthing_Gotham_Stadt_Huys', OHMW + '198590337']
};

// The wall of 1653 along the north side of Wall Street: OHM ways 198538378 (Broadway to
// the East River, with its bastions) and 198538377 (Broadway to the Hudson).
const WALL_EAST: V2[] = [
  [-161.6, 136.8],
  [-131.2, 111.9],
  [-126.4, 118.7],
  [-117.4, 118.9],
  [-118.7, 106.7],
  [-120.3, 104.3],
  [-64.3, 49.3],
  [-62.0, 52.5],
  [-50.9, 55.4],
  [-52.7, 45.0],
  [-56.6, 41.0],
  [-1.4, -12.0],
  [2.1, -7.9],
  [13.7, -4.3],
  [12.1, -16.9],
  [9.8, -21.0],
  [71.4, -62.1],
  [75.3, -56.9],
  [83.2, -57.4],
  [86.1, -69.5],
  [84.5, -72.2],
  [140.1, -111.1],
  [156.2, -121.6],
  [159.0, -116.8],
  [161.4, -121.6],
  [161.6, -125.1],
  [160.1, -129.5],
  [157.6, -133.1],
  [152.4, -136.8]
];
const WALL_WEST: V2[] = [
  [-161.6, 136.9],
  [-190.6, 161.8],
  [-188.0, 166.6],
  [-190.1, 177.7],
  [-199.4, 174.5],
  [-202.3, 170.1],
  [-235.5, 191.7],
  [-265.4, 211.4],
  [-263.8, 215.5],
  [-273.5, 234.5],
  [-279.8, 215.3],
  [-274.6, 210.7]
];
const wallStreetWall: Landmark = {
  id: 'wall_street_palisade_1653',
  name: 'The wall of New Amsterdam (Wall Street, 1653–1699)',
  kind: 'building',
  built: [1653.2, 1653.55],
  end: 1699.5,
  anchor: [-74.009665, 40.706639],
  build: b => {
    const H = 9 * FT;
    b.color('#7A5E40');
    for (const path of [WALL_EAST, WALL_WEST]) {
      for (let i = 0; i < path.length - 1; i++) b.beam([path[i][0], path[i][1], H / 2], [path[i + 1][0], path[i + 1][1], H / 2], 0.5, H);
    }
    // the Land Gate at Broadway and the Water Gate at Pearl Street
    b.color('#5E4830');
    for (const [x, y] of [
      [-161.6, 136.8],
      [140.1, -111.1]
    ] as V2[]) {
      b.box(x - 2.2, y - 1.6, 0, 0.9, 0.9, 4.6).box(x + 2.2, y + 1.6, 0, 0.9, 0.9, 4.6);
      b.beam([x - 2.2, y - 1.6, 4.4], [x + 2.2, y + 1.6, 4.4], 0.5);
    }
  },
  facts: {
    Built: 'March–July 1653 on Stuyvesant\'s order, by the Company\'s enslaved Africans, soldiers and the burghers',
    Size: '2,340 ft long, of 15 ft planks standing 9 ft above ground, with a ditch; river to river',
    Later: 'strengthened by the English and Dutch (two stone bastions, Hollandia and Zeelandia, in the 1690s); pulled down 1699, its stone used for the new City Hall',
    Model: 'line and bastions from OpenHistoricalMap (Castello Plan and later plans): 713 m (2,339 ft) including the bastions; height cited; the gates are symbolic'
  },
  sources: [WP + 'Wall_Street', OHMW + '198538378', OHMW + '198538377']
};

function church(b: MeshBuilder, bearing: number, nave: [number, number, number, number], eave: number, ridge: number, tower: [number, number, number], towerTop: number, spireTop: number, wall: string, roof: string) {
  // local +x along `bearing` + 90°; nave = [x0, x1, y0, y1]; tower = [cx, cy, width]
  b.frame(0, 0, 0, bearing, () => {
    const [x0, x1, y0, y1] = nave;
    b.color(wall).box((x0 + x1) / 2, (y0 + y1) / 2, 0, x1 - x0, y1 - y0, eave, {top: false});
    b.color(roof).gable((x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0, eave, ridge - eave, false);
    const [tx, ty, tw] = tower;
    b.color(wall).box(tx, ty, 0, tw, tw, towerTop);
    b.color(roof).pyramid(circle(tx, ty, tw * 0.52, 8), towerTop, [tx, ty, spireTop]);
  });
}

const trinity1: Landmark = {
  id: 'trinity_church_1698',
  name: 'Trinity Church (first, 1698–1776)',
  kind: 'building',
  built: [1696.5, 1698.2],
  end: 1776.72,
  anchor: [-74.012092, 40.707874],
  build: b => church(b, 16.9, [-13.6, 23.3, -(73 * FT) / 2, (73 * FT) / 2], 11, 17, [-23.3 + 16 * FT, 0, 32 * FT], 27, 180 * FT, '#9C8F80', '#5F5A55'),
  replaces: [
    [
      [-13.7, 16.7],
      [17.3, 7.3],
      [25.5, -4.9],
      [19.9, -14.8],
      [9.9, -12.3],
      [7.8, -15.6],
      [-8.0, -10.8],
      [-10.1, -5.4],
      [-15.5, -3.1],
      [-16.8, -6.7],
      [-23.7, -4.4],
      [-22.4, -0.6],
      [-27.5, 1.4],
      [-22.6, 11.1],
      [-16.0, 9.1]
    ]
  ],
  facts: {
    Built: 'chartered 1697; first service 13 Mar 1698; enlarged 1735–37',
    Destroyed: 'Great Fire of 21 Sep 1776',
    Form: 'a rectangular church with its tall steeple toward the Hudson',
    Size: 'as enlarged in 1737: body 105 ft, chancel 16 ft, steeple 32 ft square — 153 ft in all — by 73 ft broad; spire 180 ft (OpenHistoricalMap\'s outline is 53 × 25 m)',
    Model: 'shown throughout as enlarged in 1737 (the steeple was not finished before 1711); plan and spire height from one published description; site outline from OpenHistoricalMap (way 198588234); eaves (11 m) and the tower\'s masonry height (27 m) estimated'
  },
  sources: ['https://geographicguide.com/united-states/nyc/antique/trinity-church/first-temple.htm', WP + 'Trinity_Church_(Manhattan)', OHMW + '198588234']
};

const trinity2: Landmark = {
  id: 'trinity_church_1790',
  name: 'Trinity Church (second, 1790–1839)',
  kind: 'building',
  built: [1788.6, 1790.23],
  end: 1839.6,
  anchor: [-74.0121, 40.70796],
  build: b => church(b, 33.6, [-21, 13.4, -10.3, 10.3], 12, 17.5, [17.2, 0, 7.6], 31, 200 * FT, '#A39A8D', '#5F5A55'),
  replaces: [
    [
      [-11.7, 20.2],
      [23.2, -3.0],
      [11.7, -20.2],
      [-23.2, 3.0]
    ]
  ],
  facts: {
    Built: '1788–1790; consecrated 25 Mar 1790, President Washington attending',
    Demolished: '1839, after the snows of 1838–39 weakened it; Upjohn\'s church (1846) stands on the site',
    Form: 'faced Wall Street; 200 ft (61 m) tall; longer and wider than the first church',
    Model: 'height cited; plan 42 × 20.6 m from OpenHistoricalMap (way 198782077); eaves, tower width and stages estimated'
  },
  sources: [WP + 'Trinity_Church_(Manhattan)', OHMW + '198782077']
};

// ================================================================== 8. The early republic
// Old City Hall / Federal Hall, Wall Street at Nassau (1703–1812): OHM way 198588178
// (mapwarper 49065): 27.4 × 15 m, facing down Broad Street.
const FEDERAL_RING: V2[] = [
  [-6.2, 14.1],
  [-15.4, 2.2],
  [-1.3, -9.2],
  [-0.8, -8.6],
  [6.5, -14.2],
  [15.4, -2.6],
  [8.4, 2.7],
  [8.9, 3.4],
  [0.1, 10.2],
  [-0.3, 9.6]
];
function buildFederalHall(b: MeshBuilder, lEnfant: boolean) {
  const wall = lEnfant ? '#D9D2C2' : '#B9A78D';
  const roof = '#5C5A58';
  const eave = lEnfant ? 13 : 9.5;
  b.color(wall).prism(FEDERAL_RING, 0, eave);
  b.frame(0, 0, 0, 37.4, () => {
    b.color(roof).hip(0.1, -0.1, 27.9, 15.7, eave, 3.5);
    // open arcade at street level (the front faces south, down Broad Street)
    b.color('#3A3632');
    for (const k of [-1, 0, 1]) b.box(k * 3.2, -7.7, 0.3, 2.2, 0.3, 3.6);
    if (lEnfant) {
      // balcony on four Tuscan piers, four Doric columns and the eagle pediment above
      b.color(wall).box(0, -9.0, 4.6, 13, 2.8, 0.5);
      piers(b, -5.4, -10.0, 5.4, -10.0, 4, 0.9, 0, 4.6);
      piers(b, -5.4, -10.0, 5.4, -10.0, 4, 0.7, 5.1, 6.4);
      b.box(0, -9.0, 11.5, 13, 2.8, 1.0);
      b.gable(0, -9.0, 13, 2.8, 12.5, 2.4, true);
    }
    // cupola
    const z0 = eave + 3.5;
    b.color(wall).cylinder(0, 0, 2.2, z0, z0 + (lEnfant ? 6 : 4), 8);
    b.color(roof).dome(0, 0, 2.4, z0 + (lEnfant ? 6 : 4), 2.4, 8, 3);
    b.beam([0, 0, z0 + (lEnfant ? 8.4 : 6.4)], [0, 0, z0 + (lEnfant ? 11 : 8.5)], 0.15);
  });
}
const cityHall1703: Landmark = {
  id: 'city_hall_wall_street_1703',
  name: 'City Hall on Wall Street (1703–1789)',
  kind: 'building',
  built: [1699.5, 1703.0],
  end: 1789.17, // stands while L'Enfant remodels it
  anchor: [-74.010541, 40.707249],
  build: b => buildFederalHall(b, false),
  replaces: [FEDERAL_RING],
  facts: {
    Built: '1699–1703 at the head of Broad Street, partly with stone from the wall\'s bastions',
    Events: 'trial of John Peter Zenger (1735); Stamp Act Congress (1765); Congress of the Confederation (1785–89)',
    Model: 'LOW CONFIDENCE in heights: plan 27.4 × 15 m from OpenHistoricalMap (way 198588178); two storeys and attic with a cupola, heights (9.5 m eaves) estimated from engravings'
  },
  sources: [WP + 'Federal_Hall', OHMW + '198588178']
};
const federalHall: Landmark = {
  id: 'federal_hall_1789',
  name: 'Federal Hall (1789–1812)',
  kind: 'building',
  built: [1788.76, 1789.17],
  end: 1812.5,
  anchor: [-74.010541, 40.707249],
  build: b => buildFederalHall(b, true),
  replaces: [FEDERAL_RING],
  facts: {
    Built: 'the old City Hall remodelled by Pierre Charles L\'Enfant, Oct 1788 – Mar 1789, as the first Capitol of the United States',
    Events: 'first Congress, 4 Mar 1789; Washington inaugurated on the balcony, 30 Apr 1789; Bill of Rights proposed here',
    Demolished: '1812; the Custom House of 1842 (Federal Hall National Memorial) stands on the site',
    Form: 'arcaded base with four Tuscan piers under the balcony, four Doric columns and a pediment with an eagle; a third storey with hip roof and cupola; House chamber 60 × 60 ft',
    Model: 'LOW CONFIDENCE in heights: plan from OpenHistoricalMap (the 1703 outline, without L\'Enfant\'s rear extension); heights (13 m eaves, cupola to about 27 m) estimated from the Doolittle engraving'
  },
  sources: [WP + 'Federal_Hall', OHMW + '198588178']
};

const governmentHouse: Landmark = {
  id: 'government_house_1790',
  name: 'Government House (1790–1815)',
  kind: 'building',
  built: [1790.4, 1791.5],
  end: 1815.5,
  anchor: [-74.013737, 40.704284],
  build: b => {
    const ring: V2[] = [
      [-18.7, 10.9],
      [-19.1, -10.2],
      [18.7, -10.9],
      [19.1, 10.2]
    ];
    roofed(b, ring, 11, 3, 6, '#B5604A', '#5C5A58');
    hoops(b, ring, 1.5, 10.5, 2, '#E6DFD0', 0.45);
    b.frame(0, 0, 0, 1, () => {
      // columned portico toward the Bowling Green (from engravings)
      b.color('#E6DFD0').box(0, 12.2, 0, 13, 3.4, 1.4);
      piers(b, -5.2, 13.2, 5.2, 13.2, 4, 0.8, 1.4, 8.4);
      b.box(0, 12.2, 9.8, 13, 3.4, 1.0);
      b.gable(0, 12.2, 13, 3.4, 10.8, 2.3, true);
    });
  },
  replaces: [
    [
      [-18.7, 10.9],
      [-19.1, -10.2],
      [18.7, -10.9],
      [19.1, 10.2]
    ]
  ],
  facts: {
    Built: '1790–91 on the site of Fort George, facing the Bowling Green, as a house for President Washington, who never lived in it',
    Use: 'governors Clinton and Jay; custom house from 1799',
    Demolished: '1815',
    Form: 'an "elegant two-story brick building"',
    Model: 'LOW CONFIDENCE in heights: plan 37.8 × 21.1 m from OpenHistoricalMap (way 198589844); heights (11 m eaves) estimated from the storey count; the columned portico toward the Bowling Green is drawn from engravings'
  },
  sources: [WP + 'Government_House_(New_York_City)', OHMW + '198589844']
};

// The Tombs (Halls of Justice, 1838–1902): 253 ft 3 in × 200 ft 5 in, the block Centre /
// Franklin / Elm (Lafayette) / Leonard — today Collect Pond Park. Placed against the
// Centre Street line (Overture centre line less 40 ft); street centre lines Franklin–
// Leonard are 72.2 m apart, which leaves 60 m for the 61.1 m building with 40 ft streets.
const tombs: Landmark = {
  id: 'the_tombs_1838',
  name: 'The Tombs (Halls of Justice, 1838–1902)',
  kind: 'building',
  built: [1835.5, 1838.5],
  end: 1902.0,
  anchor: [-74.001969, 40.716285],
  build: b => {
    const L = 253 * FT + 3 * 0.0254;
    const W = 200 * FT + 5 * 0.0254;
    const g = '#8C8A86';
    b.frame(0, 0, 0, 32, () => {
      const out = rect(0, 0, L, W);
      const inn = rect(0, 0, L - 26, W - 26);
      b.color(g).loft([out, offset(out, -1.0)], [0, 11], {top: false});
      b.color('#A39F98').cap(offset(out, -1.0), 11, [inn]);
      b.color('#7E7C78').walls(inn, 0, 11).walls(offset(out, -0.2), 10.2, 11.6);
      b.color('#77736E').cap(inn, 0.2);
      // Egyptian portico on Centre Street
      b.color(g).loft([rect(L / 2 - 9, 0, 12, 27), rect(L / 2 - 9, 0, 10.5, 25)], [0, 14]);
      piers(b, L / 2 - 1.2, -7.5, L / 2 - 1.2, 7.5, 4, 1.8, 0, 10);
      b.box(L / 2 - 1.8, 0, 10, 3.4, 20, 2.2);
      // men's prison in the yard, joined to the courts by the "Bridge of Sighs"
      b.color('#96928B').box(-8, 0, 0, 14, 43, 14);
      b.color(g).box(4, 0, 6, 12, 2.4, 2.6);
      hoops(b, rect(-8, 0, 14, 43), 1, 13.5, 4, '#4E4C49', 0.3);
    });
  },
  replaces: [rotRect(0, 0, 253 * FT + 3 * 0.0254, 200 * FT + 5 * 0.0254, 32)],
  facts: {
    Built: '1835–1838, John Haviland, on the filled Collect Pond; Egyptian Revival granite',
    Demolished: '1902 (replaced by the second Tombs on the same block)',
    Size: '253 ft 3 in × 200 ft 5 in (77.2 × 61.1 m), the full block of Centre, Franklin, Elm and Leonard streets',
    Model: 'LOW CONFIDENCE in heights: plan dimensions cited and set on today\'s block (Collect Pond Park); wall height (11 m), the courtyard and the prison block are estimated from engravings'
  },
  sources: [WP + 'The_Tombs', OHMW + '198158994']
};

const bridewell: Landmark = {
  id: 'bridewell_1775',
  name: 'Bridewell (1775–1838)',
  kind: 'building',
  built: [1775.2, 1776.2],
  end: 1838.5,
  anchor: [-74.006543, 40.713148],
  build: b => {
    const ring: V2[] = [
      [-15.7, 15.7],
      [-8.3, 10.9],
      [-8.5, 9.6],
      [-2.9, 5.6],
      [-0.9, 6.2],
      [5.5, 1.6],
      [5.6, 0.2],
      [11.6, -3.9],
      [13.8, -3.3],
      [20.5, -7.8],
      [15.8, -15.9],
      [8.1, -11.1],
      [7.8, -9.5],
      [-12.3, 3.8],
      [-14.3, 3.5],
      [-20.8, 8.2]
    ];
    b.color('#8F8C86').prism(ring, 0, 10.5);
    b.color('#5C5A58').loft([offset(ring, 0.3), offset(ring, -2.6)], [10.5, 12.6]);
    hoops(b, ring, 1.2, 10, 2, '#3F3D3A', 0.35);
  },
  replaces: [
    [
      [-15.7, 15.7],
      [5.5, 1.6],
      [20.5, -7.8],
      [15.8, -15.9],
      [-14.3, 3.5],
      [-20.8, 8.2]
    ]
  ],
  facts: {
    Built: '1775, on the Common west of the later City Hall; used unfinished by the British for prisoners of war',
    Demolished: '1838; its dressed stone went into the Tombs',
    Model: 'LOW CONFIDENCE: plan 43.8 m long with centre and end pavilions from OpenHistoricalMap (way 198751651, "Map of City Hall Park"); height (two storeys on a basement, 10.5 m) estimated'
  },
  sources: [WP + 'Bridewell_(New_York_City_jail)', OHMW + '198751651']
};

const almshouse: Landmark = {
  id: 'almshouse_1797',
  name: 'Second Almshouse (1797–1857; New York Institution from 1816)',
  kind: 'building',
  built: [1795.5, 1797.0],
  end: 1857.0,
  anchor: [-74.005408, 40.713452],
  build: b => {
    const ring: V2[] = [
      [-28.6, 28.6],
      [-19.7, 23.3],
      [-21.8, 19.7],
      [29.1, -10.3],
      [31.6, -6.0],
      [39.3, -10.5],
      [30.0, -26.1],
      [-37.6, 13.6]
    ];
    b.color('#A6553F').prism(ring, 0, 13);
    b.color('#5C5A58').loft([offset(ring, 0.3), offset(ring, -3.5)], [13, 15.8]);
    hoops(b, ring, 2.5, 12.6, 3, '#E2DACB', 0.35);
  },
  replaces: [
    [
      [-28.6, 28.6],
      [39.3, -10.5],
      [30.0, -26.1],
      [-37.6, 13.6]
    ]
  ],
  facts: {
    Built: 'about 1796–97 along Chambers Street, behind the site of City Hall (OpenHistoricalMap dates it 1796)',
    Use: 'almshouse to 1816, then the New York Institution (museums and learned societies)',
    Demolished: '1857 — from memory; OpenHistoricalMap ends its use as an almshouse in 1830',
    Model: 'LOW CONFIDENCE: plan 78.5 × 18.2 m from OpenHistoricalMap (way 198751661, LPC African Burial Ground and the Commons report); three storeys on a basement, height (13 m) estimated'
  },
  sources: [OHMW + '198751661', OHMR + '2697412']
};

const collegeHall: Landmark = {
  id: 'kings_college_hall_1760',
  name: 'College Hall, King\'s College / Columbia College (1760–1857)',
  kind: 'building',
  built: [1756.64, 1760.4],
  end: 1857.4,
  anchor: [-74.009715, 40.713708],
  build: b => {
    b.frame(0, 0, 0, 30.8, () => {
      const ring = rect(0, 0, 57.3, 10.0);
      roofed(b, ring, 11.5, 3.2, 4.2, '#9A9288', '#5C5A58');
      hoops(b, ring, 1, 11.2, 3, '#3F3D3A', 0.35);
      b.color('#D8D2C4').cylinder(0, 0, 2.0, 14.7, 19.5, 8);
      b.color('#5C5A58').dome(0, 0, 2.2, 19.5, 2.4, 8, 3);
    });
  },
  replaces: [rotRect(0, 0, 57.3, 10.0, 30.8)],
  facts: {
    Built: 'occupied 1760 by King\'s College (chartered 1754); Columbia College from 1784',
    Site: 'Park Place (Church, Barclay, Murray streets and College Place), on Trinity Church land',
    Demolished: '1857, when the college moved to 49th Street',
    Model: 'LOW CONFIDENCE in heights: plan 57.3 × 10.0 m from OpenHistoricalMap (way 198103779; the usual description is 180 × 30 ft, three storeys, with a cupola); heights estimated from the storey count; the start of building (1756) is from memory'
  },
  sources: [OHMW + '198103779', WP + 'History_of_Columbia_University']
};

const PARK_THEATRE_RING: V2[] = [
  [-17.1, 16.1],
  [4.0, 23.4],
  [16.7, -10.4],
  [-2.2, -27.5]
];
const parkTheatre: Landmark = {
  id: 'park_theatre_1798',
  name: 'Park Theatre (1798–1848)',
  kind: 'building',
  built: [1795.4, 1798.08],
  end: 1848.96,
  anchor: [-74.007496, 40.711261],
  build: b => {
    roofed(b, PARK_THEATRE_RING, 15, 3.5, 7, '#B7AE9E', '#5C5A58');
    hoops(b, PARK_THEATRE_RING, 1, 14.5, 3, '#4A4640', 0.35);
  },
  replaces: [PARK_THEATRE_RING],
  facts: {
    Built: '1795–98 as the New Theatre (Joseph-François Mangin); opened 29 Jan 1798; rebuilt 1821 after the fire of 1820',
    Destroyed: 'burned 16 Dec 1848',
    Size: 'three storeys of plain dressed stone, 80 ft wide by 165 ft deep, on Park Row backing on Theatre Alley',
    Model: 'plan from OpenHistoricalMap (way 198589840: 46 × 23 m); height (15 m to the eaves) estimated from the storey count'
  },
  sources: [WP + 'Park_Theatre_(Manhattan)', OHMW + '198589840']
};

const LOST_PART3: Landmark[] = [fortAmsterdam, fortChurch, stadtHuys, wallStreetWall, trinity1, trinity2, cityHall1703, federalHall, governmentHouse, tombs, bridewell, almshouse, collegeHall, parkTheatre];

// ================================================================== 9. Theatres, Newspaper Row, the Equitable, Grand Central's predecessors
// New York Hippodrome (1905–1939): the lot is today's 1120 Sixth Avenue (city footprint
// BIN 1034202: 72.8 × 60.8 m = 239 × 200 ft), the whole Sixth Avenue front from 43rd to 44th.
const HIPPODROME_RING: V2[] = [
  [46.6, 9.1],
  [17.1, -44.1],
  [-46.5, -9.0],
  [-17.1, 44.1]
];
const hippodrome: Landmark = {
  id: 'hippodrome_1905',
  name: 'New York Hippodrome (1905–1939)',
  kind: 'building',
  built: [1904.5, 1905.28],
  end: 1939.65,
  anchor: [-73.982854, 40.755606],
  build: b => {
    const brick = '#A5553F';
    const ivory = '#E6DCC3';
    b.frame(0, 0, 0, 28.8, () => {
      const hx = 36.4;
      const hy = 30.4;
      // Sixth Avenue front with its two corner towers and electric globes
      b.color(brick).box(-hx + 8, 0, 0, 16, 2 * hy, 24);
      hoops(b, rect(-hx + 8, 0, 16, 2 * hy), 6, 23, 4, ivory, 0.3);
      b.color(ivory).box(-hx - 0.1, 0, 0, 0.4, 2 * hy - 16, 6);
      for (const s of [-1, 1]) {
        b.color(brick).box(-hx + 4, s * (hy - 4), 0, 8, 8, 31);
        b.color(ivory).box(-hx + 4, s * (hy - 4), 31, 9, 9, 1.0);
        b.color('#C9A24A');
        sphere(b, -hx + 4, s * (hy - 4), 35.4, 3.2, 10, 6);
      }
      // auditorium (5,300 seats) and the stage house (stage 100 × 200 ft)
      b.color(brick).box(-hx + 16 + 19, 0, 0, 38, 2 * hy, 22);
      b.color('#7B7F80');
      vault(b, -hx + 16 + 19, 0, 38, 2 * hy - 3, 22, 4.5, true, 6);
      b.color(brick).box(hx - (100 * FT) / 2, 0, 0, 100 * FT - 0.6, 2 * hy, 30);
      b.color('#6B6E70').cap(rect(hx - (100 * FT) / 2, 0, 100 * FT - 2, 2 * hy - 1.4), 30.05);
    });
  },
  replaces: [HIPPODROME_RING],
  facts: {
    Built: '1904–05 by Frederick Thompson and Elmer Dundy of Luna Park (Frederick Thompson, Jay H. Morgan); opened 12 Apr 1905',
    Demolished: 'Aug–Sep 1939',
    Size: 'the Sixth Avenue block front, 43rd to 44th Street: lot 239 × 200 ft; 5,300 seats; stage 100 × 200 ft with a 60 ft tank 14 ft deep',
    Model: 'LOW CONFIDENCE in heights: lot from today\'s footprint, stage size cited; wall heights (22–30 m) and the corner towers with their globes (about 39 m) estimated from photographs'
  },
  sources: [WP + 'New_York_Hippodrome']
};

// Metropolitan Opera House (1883–1967): OHM way 198759005 (Bromley 1930): the block
// Broadway / Seventh Avenue / 39th / 40th streets.
const MET_RING: V2[] = [
  [-20.2, 45.3],
  [41.7, 11.9],
  [27.9, -47.4],
  [-48.1, -5.9]
];
const metOpera: Landmark = {
  id: 'metropolitan_opera_house_1883',
  name: 'Metropolitan Opera House (1883–1967)',
  kind: 'building',
  built: [1881.3, 1883.81],
  end: 1967.05,
  anchor: [-73.987516, 40.754193],
  build: b => {
    const brick = '#D8C690';
    b.color(brick).prism(MET_RING, 0, 27);
    b.color('#77797A').cap(offset(MET_RING, -1), 27.05);
    hoops(b, MET_RING, 5, 26.5, 6, '#7F7354', 0.3);
    b.color('#B9AD86').walls(offset(MET_RING, 0.25), 0, 5);
    b.frame(0, 0, 0, 28.6, () => {
      // auditorium roof and the stage house toward Seventh Avenue (raised in 1903)
      b.color('#77797A').box(8, 0, 27, 44, 36, 3.5);
      b.color(brick).box(-27, 0, 27, 23, 44, 10);
      b.color('#77797A').cap(rect(-27, 0, 22, 43), 37.05);
    });
  },
  replaces: [MET_RING],
  facts: {
    Built: '1881–1883, J. Cleaveland Cady; opened 22 Oct 1883; rebuilt after the fire of 1892; auditorium remodelled 1903 by Carrère & Hastings',
    Demolished: 'Jan 1967, for 1411 Broadway',
    Site: 'the whole block, Broadway to Seventh Avenue, 39th to 40th Street (OpenHistoricalMap: 86.6 × 58.7 m, 4,590 m²)',
    Model: 'LOW CONFIDENCE in heights: outline from OpenHistoricalMap (Bromley 1930); no published heights found — seven storeys (27 m) and the stage house (37 m) estimated from photographs'
  },
  sources: [WP + 'Metropolitan_Opera_House_(39th_Street)', OHMW + '198759005']
};

// New York World (Pulitzer) Building (1890–1955): OHM way 198589815 (with the 1908 annex).
// Flat roof 191 ft, dome to 310 ft, pinnacle 350 ft.
const WORLD_RING: V2[] = [
  [-8.6, 27.4],
  [17.4, 5.5],
  [32.4, -11.1],
  [17.0, -31.8],
  [-33.7, 9.8],
  [-33.8, 11.0],
  [-35.5, 12.7],
  [-35.2, 14.5],
  [-33.7, 15.3],
  [-33.8, 16.5]
];
const worldBuilding: Landmark = {
  id: 'world_building_1890',
  name: 'New York World Building (Pulitzer Building, 1890–1955)',
  kind: 'tower',
  built: [1889.77, 1890.94],
  end: 1955.5,
  anchor: [-74.004737, 40.711848],
  build: b => {
    const stone = '#B58B6A';
    const roofH = 191 * FT;
    b.color(stone).prism(WORLD_RING, 0, roofH);
    hoops(b, WORLD_RING, 9, roofH - 1, 11, '#5E4A3C', 0.3);
    b.color('#8F6E55').walls(offset(WORLD_RING, 0.25), 0, 9);
    // six-storey drum and the gilded dome over the Park Row front
    const cx = -14.3;
    const cy = 8.8;
    b.color(stone).cylinder(cx, cy, 8.2, roofH, roofH + 17, 16);
    hoops(b, circle(cx, cy, 8.2, 16), roofH, roofH + 17, 4, '#5E4A3C', 0.3);
    b.color('#B9A05A').dome(cx, cy, 8.4, roofH + 17, 14.5, 16, 5);
    b.color(stone).cylinder(cx, cy, 1.6, roofH + 31.5, 310 * FT, 8);
    b.color('#B9A05A').beam([cx, cy, 310 * FT], [cx, cy, 350 * FT], 0.4);
  },
  replaces: [WORLD_RING],
  facts: {
    Built: 'cornerstone 10 Oct 1889; opened 10 Dec 1890 (George B. Post, for Joseph Pulitzer); annex to North William Street 1907–08',
    Demolished: '1955, for the widened Brooklyn Bridge approach',
    Height: 'flat roof 191 ft (58 m); dome 310 ft (94 m); pinnacle 350 ft (107 m): the first building taller than Trinity\'s spire',
    Frontage: '115 ft on Park Row, 136 ft on Frankfort Street (237 ft with the annex)',
    Model: 'outline from OpenHistoricalMap (way 198589815, with the annex throughout); heights cited; the dome\'s diameter (16.5 m) and position are estimated from photographs'
  },
  sources: [WP + 'New_York_World_Building', OHMW + '198589815']
};

// New-York Tribune Building (1875–1966): OHM way 198589816. Roof 155 ft and clock tower
// 260 ft as built; enlarged 1903–05 to nineteen storeys: roof 231 ft, tower 273 ft, finial 335 ft.
const TRIBUNE_RING: V2[] = [
  [-5.9, 13.9],
  [-17.0, 4.4],
  [-10.3, -0.8],
  [2.6, 10.1],
  [3.5, 9.0],
  [10.4, 14.7],
  [9.3, 16.0],
  [13.4, 19.8],
  [33.8, 3.3],
  [12.5, -19.7],
  [-1.0, -8.5],
  [-15.0, -20.4],
  [-33.6, 3.6],
  [-24.4, 12.0],
  [-13.1, 20.3]
];
function buildTribune(b: MeshBuilder, roofFt: number, towerFt: number, finialFt: number, floors: number) {
  const brick = '#9B4A3A';
  const granite = '#C9C2B4';
  const roofH = roofFt * FT;
  b.color(brick).prism(TRIBUNE_RING, 0, roofH - 6);
  b.color('#4F5654').loft([TRIBUNE_RING, offset(TRIBUNE_RING, -2.2)], [roofH - 6, roofH]);
  hoops(b, TRIBUNE_RING, 5, roofH - 7, floors, granite, 0.25);
  // clock tower, 17 ft square, in the second bay of the Nassau Street front
  b.frame(-25.8, 6.7, 0, 50.8, () => {
    const w = 17 * FT;
    const shaft = (towerFt - 16) * FT;
    b.color(brick).box(0, 0, 0, w, w, shaft);
    b.color(granite).box(0, 0, shaft - 9, w + 1.2, w + 1.2, 0.8);
    b.color('#EDEAE0').cylinder(0, -w / 2 - 0.1, 2.2, shaft - 6.5, shaft - 6.2, 12);
    b.color('#4F5654').pyramid(rect(0, 0, w + 0.4, w + 0.4), shaft, [0, 0, towerFt * FT]);
    b.color('#3F4543').beam([0, 0, towerFt * FT], [0, 0, finialFt * FT], 0.25);
  });
}
const tribune1875: Landmark = {
  id: 'tribune_building_1875',
  name: 'New-York Tribune Building (1875–1905, as built)',
  kind: 'tower',
  built: [1873.0, 1875.3],
  end: 1905.5, // stands while the enlargement of 1903–05 rises over it
  anchor: [-74.005345, 40.711643],
  build: b => buildTribune(b, 155, 240, 260, 8),
  replaces: [TRIBUNE_RING],
  facts: {
    Built: '1873–1875, Richard Morris Hunt, on Printing House Square (Nassau and Spruce streets)',
    Height: 'main roof 155 ft (47 m); clock tower 260 ft (79 m) with its 16 ft pyramid roof and iron finial: second only to Trinity\'s spire',
    Plan: 'about 90 ft on Nassau Street and 98–100 ft on Spruce Street; tower 17 ft square',
    Model: 'heights cited; outline from OpenHistoricalMap (way 198589816), which includes the later extensions; the finial\'s length (20 ft) is estimated'
  },
  sources: [WP + 'New_York_Tribune_Building', OHMW + '198589816']
};
const tribune1905: Landmark = {
  id: 'tribune_building_1905',
  name: 'New-York Tribune Building (enlarged, 1905–1966)',
  kind: 'tower',
  built: [1903.5, 1905.5],
  end: 1966.5,
  anchor: [-74.005345, 40.711643],
  build: b => buildTribune(b, 231, 273, 335, 16),
  replaces: [TRIBUNE_RING],
  facts: {
    Enlarged: '1903–1905 from ten to nineteen storeys (D\'Oench & Yost and L. Thouvard), the tower and mansard rebuilt on top',
    Demolished: '1966, for Pace University',
    Height: 'flat roof 231 ft (70 m); clock tower 273 ft; finial 335 ft (102 m)',
    Model: 'heights cited; outline from OpenHistoricalMap (way 198589816)'
  },
  sources: [WP + 'New_York_Tribune_Building', OHMW + '198589816']
};

// Equitable Life Building (1870–1912): OHM way 198592110 — the whole block (Broadway,
// Cedar, Nassau, Pine: 96.3 × 50.5 m) that it filled after the enlargement of 1885–87.
const EQUITABLE_RING: V2[] = [
  [-21.3, 50.4],
  [49.4, -11.5],
  [22.9, -48.9],
  [-48.9, 7.9]
];
const equitable: Landmark = {
  id: 'equitable_life_building_1870',
  name: 'Equitable Life Building (1870–1912)',
  kind: 'building',
  built: [1868.5, 1870.33],
  end: 1912.02,
  anchor: [-74.010522, 40.708218],
  build: b => {
    const granite = '#B9B4AA';
    b.color(granite).prism(EQUITABLE_RING, 0, 142 * FT);
    b.color('#4F5654').loft([EQUITABLE_RING, offset(EQUITABLE_RING, -2.5)], [142 * FT, 155 * FT]);
    hoops(b, EQUITABLE_RING, 4, 142 * FT, 7, '#55524C', 0.35);
    // mansard pavilion over the Broadway entrance
    b.frame(-28.4, 24.8, 0, 33, () => {
      b.color(granite).box(0, 0, 142 * FT, 14, 16, 7);
      b.color('#4F5654').loft([rect(0, 0, 14.6, 16.6), rect(0, 0, 9, 11)], [142 * FT + 7, 172 * FT]);
    });
  },
  replaces: [EQUITABLE_RING],
  facts: {
    Built: '1868–1870 at 120 Broadway (Gilman & Kendall, George B. Post): the first office building with passenger elevators',
    Height: '130–142 ft and seven storeys in 1870; 155 ft and nine storeys after 1885–87; perhaps 172 ft in the end',
    Destroyed: 'fire of 9 Jan 1912; the present Equitable Building (1915) fills the block',
    Model: 'shown throughout in its enlarged form of 1887 filling the block (OpenHistoricalMap way 198592110) — in 1870–1885 it covered only the Broadway–Cedar Street part; heights cited, the entrance pavilion estimated'
  },
  sources: [WP + 'Equitable_Life_Building_(Manhattan)', OHMW + '198592110']
};

// Grand Central Depot (1871) and Grand Central Station (1900). Train shed 530 × 200 ft,
// 100 ft high; 695 ft along Vanderbilt Avenue. Set against today's street lines: the east
// line of Vanderbilt Avenue (centre line + 30 ft) and the north line of 42nd Street
// (centre line + 50 ft); the head house's 42nd Street leg is then 695 − 530 = 165 ft deep.
function buildGrandCentral(b: MeshBuilder, station: boolean) {
  const brick = station ? '#C9C2B2' : '#A6503C';
  const trim = station ? '#E2DCCE' : '#D8D2C2';
  const slate = '#4F5654';
  const x0 = -62.1;
  const y0 = -60.0;
  const shedW = 200 * FT;
  const shedL = 530 * FT;
  const y1 = y0 + 695 * FT;
  const wing = 49 * FT; // depth of the Vanderbilt Avenue wing: estimated (249 ft front on 42nd Street)
  const x1 = x0 + wing + shedW;
  const sy0 = y1 - shedL;
  const hh = station ? 30 : 17;
  b.frame(0, 0, 0, GRID, () => {
    // head house on 42nd Street and the wing along Vanderbilt Avenue
    b.color(brick).box((x0 + x1) / 2, (y0 + sy0) / 2, 0, x1 - x0, sy0 - y0, hh);
    b.box(x0 + wing / 2, (sy0 + y1) / 2, 0, wing, y1 - sy0, hh - 2);
    hoops(b, rect((x0 + x1) / 2, (y0 + sy0) / 2, x1 - x0, sy0 - y0), 1, hh - 0.5, station ? 6 : 3, station ? '#6E6A62' : trim, 0.3);
    hoops(b, rect(x0 + wing / 2, (sy0 + y1) / 2, wing, y1 - sy0), 1, hh - 2.5, station ? 6 : 3, station ? '#6E6A62' : trim, 0.3);
    // mansard pavilions: three on 42nd Street, three along Vanderbilt Avenue
    const pav = (cx: number, cy: number, w: number, top: number) => {
      b.color(brick).box(cx, cy, hh - 2, w, w, 4);
      if (station) b.color(slate).dome(cx, cy, w * 0.55, hh + 2, top - hh - 2, 8, 4);
      else b.color(slate).loft([rect(cx, cy, w + 0.6, w + 0.6), rect(cx, cy, w * 0.45, w * 0.45)], [hh + 2, top]);
    };
    const tall = station ? 46 : 36;
    pav((x0 + x1) / 2, y0 + 7, 14, tall);
    pav(x0 + 7, y0 + 7, 12, tall - 6);
    pav(x1 - 7, y0 + 7, 12, tall - 6);
    pav(x0 + wing / 2, (sy0 + y1) / 2, 12, tall - 8);
    pav(x0 + wing / 2, y1 - 7, 12, tall - 8);
    // train shed: 530 ft long, 200 ft span, 100 ft to the crown
    b.color('#9FB0B2');
    vault(b, x0 + wing + shedW / 2, (sy0 + y1) / 2, shedW, shedL, 0, 100 * FT, true, 10);
    b.color('#5F6668');
    for (let i = 0; i <= 8; i++) {
      const y = sy0 + (shedL * i) / 8;
      b.box(x0 + wing + 0.3, y, 0, 0.6, 0.6, 6).box(x1 - 0.3, y, 0, 0.6, 0.6, 6);
    }
  });
}
const GC_SITE = [rotRect(1.13, 51.85, (49 + 200) * FT, 695 * FT, GRID)];
const gcDepot: Landmark = {
  id: 'grand_central_depot_1871',
  name: 'Grand Central Depot (1871–1900)',
  kind: 'building',
  built: [1869.87, 1871.8],
  end: 1900.8, // in use throughout the rebuilding of 1898–1900
  anchor: [-73.9772, 40.7527],
  build: b => buildGrandCentral(b, false),
  replaces: GC_SITE,
  facts: {
    Built: 'Nov 1869 – Oct 1871 for Commodore Vanderbilt (John B. Snook; shed by Isaac Buckhout)',
    Size: 'L-shaped head house, 695 ft along Vanderbilt Avenue; train shed 530 × 200 ft, 100 ft high at the crown, on 32 arched trusses; 12 tracks',
    Later: 'annex of seven tracks added on the east in 1885; rebuilt as Grand Central Station 1898–1900',
    Model: 'LOW CONFIDENCE in heights: shed and Vanderbilt Avenue length cited and set on today\'s street lines; the 42nd Street frontage (249 ft), the three-storey head house (17 m) and its mansard towers (to 36 m) are estimated'
  },
  sources: [WP + 'History_of_Grand_Central_Terminal']
};
const gcStation: Landmark = {
  id: 'grand_central_station_1900',
  name: 'Grand Central Station (1900–1910)',
  kind: 'building',
  built: [1898.5, 1900.8],
  end: 1910.45,
  anchor: [-73.9772, 40.7527],
  build: b => buildGrandCentral(b, true),
  replaces: GC_SITE,
  facts: {
    Built: '1898–1900: the depot\'s head house raised from three to six storeys with a new stone-coloured front (Bradford Gilbert), waiting rooms and concourse enlarged',
    Demolished: 'in stages 1903–1910 as the Terminal was built around it; the shed came down in 1908, the head house in June 1910',
    Size: 'the 1871 footprint: 695 ft on Vanderbilt Avenue; shed 530 × 200 ft, 100 ft high',
    Model: 'LOW CONFIDENCE in heights: footprint as the depot; six storeys (30 m) and the domed towers (to 46 m) estimated from photographs'
  },
  sources: [WP + 'History_of_Grand_Central_Terminal']
};

// ================================================================== 10. Trylon and Perisphere (1939–1941)
// Perisphere: 180 ft sphere on the piling ring the Unisphere reuses — centre = centroid of
// the Unisphere's pool (Overture base_water "Fountain of the Continents"). Trylon: 610 ft,
// south-east of the sphere (fair map of 1939: about 68 m away at bearing 139°).
const TRYLON: V2 = [44.6, -51.3];
const trylonPerisphere: Landmark = {
  id: 'trylon_perisphere_1939',
  name: 'Trylon and Perisphere (1939–1941)',
  kind: 'monument',
  built: [1938.27, 1939.33],
  end: 1941.0,
  anchor: [-73.845071, 40.746398],
  build: b => {
    const white = '#F1EFE8';
    const r = 90 * FT;
    const zc = r + 2.5;
    b.color('#6F93A8').cap(circle(0, 0, 38, 32), 0.15);
    b.color('#BEBCB5');
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * Math.PI * 2;
      b.cylinder(Math.cos(a) * 9, Math.sin(a) * 9, 0.9, 0, zc - r + 1.6, 8);
    }
    b.color(white);
    sphere(b, 0, 0, zc, r, 24, 14);
    // Trylon: three-sided spire, 610 ft
    const tri = circle(TRYLON[0], TRYLON[1], 11, 3).map(([x, y]) => [x, y] as V2);
    b.pyramid(tri, 0, [TRYLON[0], TRYLON[1], 610 * FT]);
    // bridge from the Trylon into the sphere, and the Helicline ramp winding down round it
    const zb = 15.2;
    const d = norm(TRYLON);
    b.color('#E4E1D8').beam([d[0] * (r - 4), d[1] * (r - 4), zb + 1], [TRYLON[0] - d[0] * 3, TRYLON[1] - d[1] * 3, zb + 1], 4.5, 2.6);
    const inner: V3[] = [];
    const outer: V3[] = [];
    const n = 40;
    for (let i = 0; i <= n; i++) {
      const brg = ((150 + (230 * i) / n) * Math.PI) / 180;
      const z = zb * (1 - i / n);
      inner.push([Math.sin(brg) * 43.2, Math.cos(brg) * 43.2, z]);
      outer.push([Math.sin(brg) * 48.8, Math.cos(brg) * 48.8, z]);
      if (i % 4 === 0 && z > 1.5) b.color('#BEBCB5').box(Math.sin(brg) * 46, Math.cos(brg) * 46, 0, 0.8, 0.8, z);
    }
    b.color('#E4E1D8').ribbon(inner, outer);
    b.ribbon(
      inner.map(p => [p[0], p[1], p[2] + 1.1] as V3),
      inner
    );
    b.ribbon(
      outer.map(p => [p[0], p[1], p[2] + 1.1] as V3),
      outer
    );
    b.beam([TRYLON[0] - d[0] * 6, TRYLON[1] - d[1] * 6, zb + 0.3], [outer[0][0], outer[0][1], zb + 0.3], 5.5, 0.6);
  },
  replaces: [circle(0, 0, 52, 24), circle(TRYLON[0], TRYLON[1], 16, 12)],
  facts: {
    Built: 'Apr 1938 – Apr 1939 (Wallace Harrison and J. André Fouilhoux): the Theme Center of the 1939–40 New York World\'s Fair',
    Demolished: 'after the fair closed on 27 Oct 1940; razed by 1941 and the steel scrapped',
    Size: 'Perisphere 180 ft (55 m) in diameter; Trylon 610 ft (186 m); Helicline ramp 950 ft',
    Site: 'the Unisphere (1964) stands on the Perisphere\'s foundation ring',
    Model: 'heights and the sphere\'s position cited; LOW CONFIDENCE for the Trylon\'s spot (read off a 1939 newspaper map, ± 15 m) and base (19 m sides), the height of the sphere above its pool and the Helicline\'s course (modelled 230 m long)'
  },
  sources: [WP + 'Trylon_and_Perisphere', WP + 'Unisphere', 'https://commons.wikimedia.org/wiki/File:Worlds-fair-map.jpg']
};

const LOST_PART4: Landmark[] = [hippodrome, metOpera, worldBuilding, tribune1875, tribune1905, equitable, gcDepot, gcStation, trylonPerisphere];

export const LOST: Landmark[] = [...LOST_PART1, ...LOST_PART2, ...LOST_PART3, ...LOST_PART4];
