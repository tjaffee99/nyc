/**
 * New Haven, Connecticut: the second round of landmarks (the first, ct.ts, has Harkness Tower, the
 * Green's churches, Sterling, Beinecke, Payne Whitney, the Bowl, Union Station, the Knights of
 * Columbus tower). Research, ids of the footprints and numeric checks:
 * data/research/landmarks_new_haven.md.
 *
 * Conventions as ct.ts: the anchor is the lon/lat of the footprint (data/interim/counties/
 * ct_south_central_connecticut.parquet, Overture Maps 2026-10-21.0, ODbL-compatible) a model
 * replaces, rounded to 6 decimals; plans are that footprint in anchor-local metres (x east, y
 * north; the kit's lngLatToLocal), simplified to 0.25 m. `b.frame(x, y, z, bearing)` puts a
 * model's +y on a compass bearing. Heights are cited figures where one was read, otherwise named
 * as estimates in the `Model:` fact.
 */
import {MeshBuilder, circle, rect, rotRect, roundedRect, type V2} from './kit';
import type {Landmark} from './types';

const WIKI = 'https://en.wikipedia.org/wiki/';
const OVERTURE = 'https://docs.overturemaps.org/guides/buildings/';
const TALLEST = WIKI + 'List_of_tallest_buildings_in_New_Haven';

/** Flat list of numbers -> ring. */
function P(...n: number[]): V2[] {
  const o: V2[] = [];
  for (let i = 0; i < n.length; i += 2) o.push([n[i], n[i + 1]]);
  return o;
}

/** Ring scaled about its vertex mean: kx across, ky along an axis at `bearing` (deg clockwise from north). */
function scale(ring: V2[], kx: number, ky = kx, bearing = 0): V2[] {
  const cx = ring.reduce((s, p) => s + p[0], 0) / ring.length;
  const cy = ring.reduce((s, p) => s + p[1], 0) / ring.length;
  const a = (bearing * Math.PI) / 180;
  const ux = Math.sin(a); // unit vector along the axis (east, north)
  const uy = Math.cos(a);
  return ring.map(([x, y]) => {
    const dx = x - cx;
    const dy = y - cy;
    const along = dx * ux + dy * uy;
    const across = dx * uy - dy * ux;
    const na = along * ky;
    const nc = across * kx;
    return [cx + na * ux + nc * uy, cy + na * uy - nc * ux] as V2;
  });
}

export const NEW_HAVEN: Landmark[] = [];

// ====================================================================== Connecticut Financial Center (1990)
// Cited (Wikipedia, List of tallest buildings in New Haven): 383 ft (117 m), 26 floors, 1990, the
// tallest building in New Haven; postmodern, Crang and Boake of Toronto. Footprint height 116 m.
// Overture building aae0fa32-43d6-4593-9f1d-0ad4fd97db4c
const R_cfc: V2[] = P(-29.1, 17.7, -36.3, 4.2, -35.5, 1.2, 11.1, -24.4, 13.9, -23.6, 15.8, -20.3, 17.8, -21.4, 21.6, -20.3, 23.4, -17.0, 25.6, -18.2, 29.0, -17.2, 36.0, -3.6, 35.3, -1.2, -11.2, 24.8, -14.1, 24.0, -16.1, 20.4, -18.3, 21.6, -21.5, 20.6, -23.5, 17.1, -26.1, 18.5);
function buildCfc(b: MeshBuilder) {
  const stone = '#B9A58E';
  const roof = '#5F7F73';
  b.color('#8E8A86').prism(R_cfc, 0, 8);
  b.color(stone).prism(scale(R_cfc, 0.97, 0.98, 118.8), 8, 96);
  b.color('#A89684').prism(scale(R_cfc, 0.93, 0.95, 118.8), 96, 106);
  b.color(stone).prism(scale(R_cfc, 0.84, 0.88, 118.8), 106, 111);
  b.color(roof).loft([scale(R_cfc, 0.84, 0.88, 118.8), scale(R_cfc, 0.5, 0.58, 118.8), scale(R_cfc, 0.08, 0.2, 118.8)], [111, 114.5, 116.7]);
}
NEW_HAVEN.push({
  id: 'connecticut_financial_center',
  name: 'Connecticut Financial Center',
  kind: 'tower',
  built: [1988, 1990.5],
  end: 9999,
  anchor: [-72.924338, 41.306951],
  build: buildCfc,
  replaces: [R_cfc],
  facts: {
    Built: 'completed 1990, Crang and Boake of Toronto; postmodern; on the site of the Powell Building; the tallest building in New Haven',
    Height: '383 ft (117 m), 26 floors',
    Model: 'plan from the footprint (67.8 x 32.4 m); roof height cited (116.7 m); the set-backs, the pyramidal roof and the colours estimated; start of building (1988) estimated'
  },
  sources: [TALLEST, WIKI + 'Connecticut_Financial_Center', OVERTURE]
});

// ====================================================================== 360 State Street (2008-10)
// Cited: 338 ft (103 m), 31 floors, completed 2010, 500 apartments, construction started 1 Dec 2008
// (Wikipedia). Footprint 83.8 x 61.4 m (Overture height 91 m).
// Overture building 56eba437-a7ae-4545-a498-4ff714bace68
const R_360: V2[] = P(49.5, 6.7, -19.8, 44.4, -50.1, -7.6, 22.9, -48.7, 25.7, -43.1, 22.2, -41.4);
function build360(b: MeshBuilder) {
  b.color('#8E96A0').prism(R_360, 0, 27, {top: false});
  b.color('#6B7480').cap(R_360, 27);
  // the tall slab stands on the long side toward the Green (north-west), a second lower block beside it
  b.frame(1.4, -1.4, 0, 119.4, () => {
    b.color('#A3ADB8').box(-8, 0, 27, 23, 52, 76.0, {top: true});
    b.color('#8E96A0').box(14, 6, 27, 22, 38, 39, {top: true});
    b.color('#6B7480').box(-8, 0, 103, 15, 30, 0.0);
  });
}
NEW_HAVEN.push({
  id: 'state_street_360',
  name: '360 State Street',
  kind: 'tower',
  built: [2008.9, 2010.2],
  end: 9999,
  anchor: [-72.923214, 41.305442],
  build: build360,
  replaces: [R_360],
  facts: {
    Built: 'construction began 1 December 2008, completed 2010 (Becker + Becker; 500 apartments, a LEED Platinum building); on the site of Shartenberg’s department store (1915-62)',
    Height: '338 ft (103 m), 31 floors; the second-tallest building in New Haven',
    Model: 'plan from the footprint (83.8 x 61.4 m, the podium and the towers together); top cited (103 m); podium height (27 m), which part is the tall slab and the second block, and the glass colours estimated: LOW'
  },
  sources: [TALLEST, WIKI + '360_State_Street', OVERTURE]
});

// ====================================================================== Union and New Haven Trust Building (1927)
// Cited: 242 ft (74 m), 13 floors (Wikipedia: 12 in the list), Cross and Cross, Georgian / Colonial
// Revival, red brick, golden cupola echoing the Green's United Church; opened 1927.
// Overture building 1612ac6e-548e-4f56-a37c-dc6b47ba7974 (Wells Fargo, h 74 m)
const R_union_trust: V2[] = P(13.3, -26.2, 29.1, 3.1, 25.5, 5.0, 26.8, 7.3, -11.0, 27.7, -14.2, 21.8, -16.4, 23.0, -24.5, 8.3, -26.6, 7.7, -28.6, 4.0, -26.5, -3.1, -23.3, -4.8, -22.7, -6.8);
function buildUnionTrust(b: MeshBuilder) {
  const brick = '#A9553F';
  const trim = '#E4DFD0';
  b.color('#CFC8B6').prism(R_union_trust, 0, 9);
  b.color(brick).prism(scale(R_union_trust, 0.97, 0.97, 118.4), 9, 52);
  b.color(trim).prism(scale(R_union_trust, 0.99, 0.99, 118.4), 52, 53.2);
  b.color(brick).prism(scale(R_union_trust, 0.8, 0.78, 118.4), 53.2, 64);
  b.color(trim).prism(scale(R_union_trust, 0.82, 0.8, 118.4), 64, 65);
  b.frame(0, 0, 65, 118.4, () => {
    b.color(brick).box(0, 0, 0, 8.6, 8.6, 3.4);
    b.color(trim).cylinder(0, 0, 3.0, 3.4, 5.6, 8);
    b.color('#C9A24A').dome(0, 0, 3.0, 5.6, 2.2, 8, 3);
    b.color('#C9A24A').pyramid(circle(0, 0, 0.5, 6), 7.8, [0, 0, 8.8]);
  });
}
NEW_HAVEN.push({
  id: 'union_new_haven_trust',
  name: 'Union and New Haven Trust Building',
  kind: 'tower',
  built: [1925.5, 1927.5],
  end: 9999,
  anchor: [-72.923612, 41.308296],
  build: buildUnionTrust,
  replaces: [R_union_trust],
  facts: {
    Built: '1927, Cross and Cross, Georgian / Colonial Revival, on the corner of Church and Elm streets; the tallest building in New Haven until 1938; flats (The Union) since 2014',
    Height: '242 ft (74 m), 13 floors; the golden cupola echoes the dome of United Church on the Green',
    Model: 'plan from the footprint (51 x 36 m); top cited (73.8 m = 242 ft); the base, the set-back stages and the cupola’s proportions estimated; start of building (1925.5) estimated'
  },
  sources: [WIKI + 'Union_and_New_Haven_Trust_Building', TALLEST, OVERTURE]
});

// ====================================================================== St. Mary's Church (1874; spire 1982)
// Cited: James Murphy of Providence, land bought 1868, dedicated 1874; "the spire was never
// completed" until the Knights of Columbus' renovation of 1982 (Wikipedia). 230 ft (70 m) tall with
// the spire (tall-buildings list).
// Overture building 4b5f3877-ecbb-4f06-adf5-e5e83989e45f
const R_stmary: V2[] = P(19.7, 13.1, -23.2, 25.9, -30.7, 2.5, 9.3, -8.9, 6.7, -17.7, -1.8, -15.0, -1.4, -13.8, -27.0, -6.4, -31.3, -21.2, -5.8, -28.4, -2.7, -18.3, 8.9, -21.6, 12.1, -9.9, 13.2, -10.1, 14.7, -4.7, 18.2, -4.2, 21.5, -1.8, 22.5, 1.8, 21.4, 5.4, 18.0, 7.8);
function buildStMary(b: MeshBuilder, spire: boolean) {
  const stone = '#9C8D7B';
  const slate = '#4E5258';
  b.color(stone).prism(R_stmary, 0, 11);
  // the nave is the wing 44.8 x 24.6 m on the bearing 106.6 deg; the front (tower) is at its west end
  b.frame(-6.5, 7.9, 0, 106.6, () => {
    b.color(stone).box(0, 0, 0, 24.0, 44.0, 16);
    b.color(slate).gable(0, 0, 24.6, 44.8, 16, 10, true);
    b.color(stone).box(0, -17, 0, 10, 10, 32);
    if (!spire) b.color(slate).pyramid(rect(0, -17, 10.4, 10.4), 32, [0, -17, 36]);
    else b.color(slate).loft([rect(0, -17, 8.6, 8.6), rect(0, -17, 5.8, 5.8), rect(0, -17, 1.2, 1.2)], [32, 44, 70.1]);
  });
}
NEW_HAVEN.push({
  id: 'st_marys_new_haven',
  name: 'St. Mary’s Church',
  kind: 'building',
  built: [1869, 1874.9],
  end: 1981.5,
  anchor: [-72.923654, 41.311839],
  build: b => buildStMary(b, false),
  replaces: [R_stmary],
  facts: {
    Built: 'dedicated 1874 (James Murphy of Providence; ground bought 1868): the first Catholic parish church of New Haven; the Knights of Columbus were founded here in 1882',
    Model: 'plan from the footprint (51 x 47 m, cruciform); wall height (14 m), nave (wall 16 m, ridge 26 m) and the tower (32 m, hipped) estimated; which end is the front is inferred from Hillhouse Avenue; start of building (1869) estimated: LOW. The spire of the original design was never built until 1982 (separate model)'
  },
  sources: [WIKI + "St._Mary's_Church_(New_Haven,_Connecticut)", OVERTURE]
});
NEW_HAVEN.push({
  id: 'st_marys_spire_new_haven',
  name: 'St. Mary’s Church (with its spire)',
  kind: 'tower',
  built: [1981.5, 1982.9],
  end: 9999,
  anchor: [-72.923654, 41.311839],
  build: b => buildStMary(b, true),
  replaces: [R_stmary],
  facts: {
    Built: 'the spire of James Murphy’s plan of the 1870s was never built; it was added in the 1982 renovation, a gift of the Knights of Columbus',
    Height: '230 ft (70 m) to the tip: the tallest church in New Haven',
    Model: 'tip height cited (70.1 m); the plan, tower top (32 m) and the spire’s taper as the 1874 model, estimated'
  },
  sources: [WIKI + "St._Mary's_Church_(New_Haven,_Connecticut)", TALLEST]
});

// ====================================================================== Kline Tower (1962-66)
// Cited: Philip Johnson, 250 ft (76 m) roof, 16 floors, built 1962-66, $12 million, the tallest
// building on Yale's campus (Wikipedia). Footprint height 77 m.
// Overture building 8c16abc7-49b1-42e6-b4d6-56f562241192
const R_kline: V2[] = P(16.6, 26.3, 0.3, 30.8, -2.5, 20.6, -6.6, 21.7, -14.6, -7.2, -11.5, -8.0, -14.0, -17.1, 3.4, -21.9, 6.0, -12.8, 8.9, -13.6, 17.1, 15.8, 13.9, 16.7);
NEW_HAVEN.push({
  id: 'kline_tower',
  name: 'Kline Tower (Kline Biology Tower)',
  kind: 'tower',
  built: [1962, 1966.5],
  end: 9999,
  anchor: [-72.922549, 41.317239],
  build: b => {
    b.color('#8F8272').prism(R_kline, 0, 72);
    b.color('#7B6F62').prism(scale(R_kline, 0.985, 0.99, 15.5), 72, 76.2);
  },
  replaces: [R_kline],
  facts: {
    Built: '1962–1966, Philip Johnson, $12 million; the tallest building in New Haven 1966–69 and still the tallest on Yale’s campus; Kline Biology Tower until 2023',
    Height: '250 ft (76 m) to the roof, 16 floors',
    Model: 'plan from the footprint (50 x 24 m); roof cited (76.2 m); the darker top band (4 m) and the brick colour estimated'
  },
  sources: [WIKI + 'Kline_Biology_Tower', TALLEST, OVERTURE]
});

// ====================================================================== Ingalls Rink, "the Whale" (1953-58)
// Cited: Eero Saarinen, built 1953-58 (opened 3 December 1958), a 90 m reinforced-concrete arch with
// a cable net and a timber roof, maximum ceiling height 23 m (Wikipedia). Footprint 95 x 60 m.
// Overture building 246ac9b8-808e-4ad0-884f-e839cbf37273
const R_ingalls: V2[] = P(18.0, 38.8, 18.4, 42.1, 5.9, 46.4, -9.6, 45.9, -9.9, 41.6, -10.5, 40.3, -11.9, 38.1, -18.0, 31.0, -21.5, 25.9, -26.1, 16.5, -28.3, 10.6, -29.8, 1.6, -30.3, -5.2, -29.6, -12.6, -29.1, -15.5, -26.1, -24.7, -23.7, -30.3, -20.7, -35.7, -19.5, -38.6, -18.9, -41.7, -19.3, -44.6, -4.9, -48.5, 8.6, -46.5, 9.7, -42.2, 20.4, -29.0, 23.8, -23.4, 26.1, -18.2, 28.6, -10.0, 29.9, -1.7, 29.3, 9.6, 28.6, 13.5, 26.2, 20.8, 23.6, 27.0, 18.4, 36.7);
NEW_HAVEN.push({
  id: 'ingalls_rink',
  name: 'Ingalls Rink (“the Whale”)',
  kind: 'building',
  built: [1953.5, 1958.9],
  end: 9999,
  anchor: [-72.925003, 41.31681],
  build: b => {
    const kAcross = [1, 0.86, 0.69, 0.49, 0.28, 0.05];
    const kAlong = [1, 0.995, 0.98, 0.95, 0.9, 0.84];
    const zs = [4, 9, 14, 18.5, 21.8, 23];
    b.color('#C4BFB2').prism(R_ingalls, 0, 4, {top: false});
    b.color('#8E918C').loft(kAcross.map((k, i) => scale(R_ingalls, k, kAlong[i], 11.5)), zs);
    // the concrete arch along the ridge
    b.frame(0, 0, 0, 11.5, () => {
      b.color('#D4D0C4').box(0, 0, 22.2, 1.6, 78, 0.8);
    });
  },
  replaces: [R_ingalls],
  facts: {
    Built: '1953–1958 (opened 3 December 1958), Eero Saarinen, $1.5 million: a concrete arch and cable net under a timber roof; seats 3,500; renovated 2009',
    Height: 'maximum ceiling height 23 m; the main arch is 90 m long',
    Model: 'plan from the footprint (95 x 60 m); the roof is a lofted hump to the cited ceiling height (23 m, used as the roof height), with a ridge line for the arch; the 4 m wall and the section of the roof estimated'
  },
  sources: [WIKI + 'Ingalls_Rink', OVERTURE]
});

// ====================================================================== Woolsey Hall (1901)
// Cited: Carrere and Hastings, Beaux-Arts, built for Yale's bicentennial, opened 1901, about 2,650
// seats (Wikipedia). No height read.
// Overture building 32000413-42df-414c-8c74-6022016265d2
const R_woolsey: V2[] = P(24.8, 25.7, -4.9, 25.8, -23.7, -5.8, 6.8, -22.9, 30.1, 17.0, 23.3, 20.5, 26.0, 25.2);
NEW_HAVEN.push({
  id: 'woolsey_hall',
  name: 'Woolsey Hall (Yale)',
  kind: 'building',
  built: [1899.5, 1901.5],
  end: 9999,
  anchor: [-72.926176, 41.311244],
  build: b => {
    const lime = '#D2C8B2';
    b.color(lime).prism(R_woolsey, 0, 18);
    b.color('#B8AE98').prism(scale(R_woolsey, 1.02, 1.01, 30.3), 18, 19.6);
    b.color('#6F8577').loft([scale(R_woolsey, 0.98, 0.98, 30.3), scale(R_woolsey, 0.78, 0.9, 30.3), scale(R_woolsey, 0.36, 0.7, 30.3)], [19.6, 24.5, 27.6]);
    // columned front at the south-west end, a pediment above
    b.frame(4.5, 7.8, 0, 30.3, () => {
      b.color('#E4DCCB').box(0, -24.6, 0, 22, 3.2, 0.8);
      for (let i = 0; i < 6; i++) b.cylinder(-9.6 + i * 3.84, -24.2, 0.7, 0.8, 16.2, 8);
      b.box(0, -24.2, 16.2, 22.8, 3.2, 1.6);
      b.color('#CFC5AE').gable(0, -24.2, 22.8, 3.2, 17.8, 3.2, false);
    });
  },
  replaces: [R_woolsey],
  facts: {
    Built: '1901 for Yale’s bicentennial (Carrère and Hastings, who designed the New York Public Library a decade later); the university’s largest auditorium, about 2,650 seats',
    Model: 'plan from the footprint (46 x 36 m); every height (walls 18 m, roof 27.6 m), the green hipped roof and the six-column front on the south-west end estimated; no published height read: LOW'
  },
  sources: [WIKI + 'Woolsey_Hall', OVERTURE]
});

// ====================================================================== Battell Chapel (1874-76)
// Cited: Russell Sturgis Jr., High Victorian Gothic, completed 1876 (Wikipedia). No height read.
// Overture building c501f924-19b2-416a-9f9c-587654d85f38
const R_battell: V2[] = P(8.9, -13.4, 11.1, -9.9, 14.2, -11.6, 18.5, -11.4, 21.2, -9.8, 22.6, -7.2, 22.6, -4.0, 21.0, -1.0, 17.2, 1.0, 19.7, 5.5, 9.5, 11.6, 7.7, 8.7, -7.1, 16.7, -7.7, 17.7, -9.3, 18.4, -10.9, 18.1, -11.9, 16.5, -11.5, 15.0, -10.2, 14.1, -8.9, 14.1, -13.8, 6.0, -14.5, 6.9, -15.7, 7.4, -17.4, 6.6, -17.8, 4.8, -17.3, 3.4, -20.0, -2.0, -19.3, -2.8, -14.0, -5.1, 10.3, -17.7, 11.8, -15.2);
NEW_HAVEN.push({
  id: 'battell_chapel',
  name: 'Battell Chapel (Yale)',
  kind: 'building',
  built: [1874.5, 1876.9],
  end: 9999,
  anchor: [-72.927581, 41.309421],
  build: b => {
    b.color('#A4503C').prism(R_battell, 0, 12);
    // the nave (26 x 13 m, east-west) under a gable; the tower on the north-west corner
    b.frame(5, -0.5, 0, 90, () => {
      b.color('#4B4F55').gable(0, 0, 13, 26, 12, 7, true);
    });
    b.color('#A4503C').box(-13, 1, 0, 6, 6, 28);
    b.color('#4B4F55').pyramid(rect(-13, 1, 6.6, 6.6), 28, [-13, 1, 40]);
  },
  replaces: [R_battell],
  facts: {
    Built: '1874–1876 (completed 1876), Russell Sturgis Jr., High Victorian Gothic, polychrome brick and stone; Yale’s college chapel on the Old Campus',
    Model: 'plan from the footprint (42 x 26 m); every height (walls 12 m, ridge 19 m, tower 40 m), the nave’s extent and the position of the tower estimated; no published dimension read: LOW'
  },
  sources: [WIKI + 'Battell_Chapel', OVERTURE]
});

// ====================================================================== Rudolph Hall, the Art and Architecture Building (1958-63)
// Cited: Paul Rudolph, Brutalist, ribbed bush-hammered concrete, seven storeys with more than 30
// floor levels, dedicated 8 November 1963 (Wikipedia). No height read.
// Overture building a499f893-2d87-444c-aabe-a8060ccdbed2
const R_rudolph: V2[] = P(-23.8, -0.3, -19.7, -2.6, -22.7, -7.9, -16.5, -11.4, -13.4, -5.9, 3.3, -15.1, 2.0, -17.2, 7.3, -20.1, 8.5, -18.0, 14.1, -21.1, 17.5, -14.8, 12.5, -11.8, 16.6, -4.5, 20.1, -6.5, 24.1, 0.9, 20.8, 2.7, 21.2, 3.6, 17.0, 5.9, 18.3, 8.3, 26.5, 3.9, 26.9, 4.7, 28.3, 4.0, 30.1, 7.7, 13.7, 17.2, 11.1, 12.4, 11.8, 12.0, 9.8, 8.8, -2.3, 15.2, -0.8, 18.7, -1.8, 19.4, -6.0, 21.2, -7.2, 18.1, -11.7, 20.5, -12.1, 19.8, -12.7, 20.1, -13.2, 19.1, -14.1, 19.5, -15.7, 16.6, -14.8, 16.1, -15.5, 14.9, -14.9, 14.6, -15.2, 14.0, -11.3, 12.4, -16.2, 3.5, -20.6, 5.9, -21.0, 5.3, -21.6, 5.6, -22.1, 4.5, -23.0, 4.9, -24.4, 2.1, -23.5, 1.7, -24.0, 0.6, -23.5, 0.3);
NEW_HAVEN.push({
  id: 'rudolph_hall',
  name: 'Rudolph Hall (Art and Architecture Building)',
  kind: 'building',
  built: [1958, 1963.85],
  end: 9999,
  anchor: [-72.931886, 41.308769],
  build: b => {
    b.color('#B3AEA2').prism(R_rudolph, 0, 11);
    b.color('#A7A296').prism(scale(R_rudolph, 0.74, 0.8, 119.2), 11, 19);
    b.color('#9C978B').prism(scale(R_rudolph, 0.44, 0.5, 119.2), 19, 28);
    b.color('#8A857A').prism(scale(R_rudolph, 0.2, 0.24, 119.2), 28, 31);
  },
  replaces: [R_rudolph],
  facts: {
    Built: 'dedicated 8 November 1963 (Paul Rudolph): one of the earliest and best-known Brutalist buildings in the United States; seven storeys with more than 30 floor levels; named for Rudolph in 2007',
    Model: 'plan from the footprint (45 x 40 m); the stepped massing and every height (31 m at the tallest tower) estimated, ribbed concrete only as a colour; start of work (1958) estimated: LOW'
  },
  sources: [WIKI + 'Rudolph_Hall', OVERTURE]
});

// ====================================================================== Yale Center for British Art (1969-77)
// Cited: Louis Kahn (died 1974), four floors, matte steel and reflective glass, opened 15 April 1977
// (Wikipedia). Height 16.7 m is the footprint's.
// Overture building 6605d564-c884-4545-a836-933e3a326cf5
const R_ycba: V2[] = P(-35.7, -1.3, 18.1, -30.6, 35.8, 1.4, -18.0, 30.7);
NEW_HAVEN.push({
  id: 'yale_center_british_art',
  name: 'Yale Center for British Art',
  kind: 'building',
  built: [1969, 1977.3],
  end: 9999,
  anchor: [-72.930861, 41.307896],
  build: b => {
    b.color('#B9B5AA').prism(R_ycba, 0, 5.5, {top: false});
    b.color('#A5ABAE').prism(scale(R_ycba, 0.995, 0.995, 118.6), 5.5, 16.7, {holes: [rotRect(-14, 0, 10, 10, 118.6), rotRect(12, 2, 8, 8, 118.6)]});
  },
  replaces: [R_ycba],
  facts: {
    Built: 'opened to the public on 15 April 1977; designed by Louis Kahn, who died in 1974 before it was finished, at York and Chapel streets; four floors, matte steel panels and reflective glass',
    Height: '16.7 m (the footprint’s height)',
    Model: 'plan from the footprint (61.6 x 36.6 m); top at the footprint’s 16.7 m; the base band (5.5 m) and the two courtyards (positions and sizes) estimated; start of work (1969) estimated'
  },
  sources: [WIKI + 'Yale_Center_for_British_Art', OVERTURE]
});

// ====================================================================== Pirelli (Armstrong Rubber) Building, today Hotel Marcel (1968-70)
// Cited: Marcel Breuer and Robert Gatje, nine storeys: a two-storey base, a two-storey air gap with
// three massive piers and a five-storey upper block; built 1968-70 for the Armstrong Rubber
// Company, Pirelli's until 1999 (Wikipedia, Hotel Marcel). No height read.
// Overture building 2ac069d8-b56d-4ce0-95cc-bbee467be17f
const R_marcel: V2[] = P(-30.3, -20.4, -7.2, -35.7, 24.7, 11.8, 1.5, 27.1);
NEW_HAVEN.push({
  id: 'pirelli_building_hotel_marcel',
  name: 'Armstrong Rubber (Pirelli) Building, Hotel Marcel',
  kind: 'building',
  built: [1968, 1970.5],
  end: 9999,
  anchor: [-72.918681, 41.296554],
  build: b => {
    b.frame(-2.8, -4.3, 0, 33.8, () => {
      b.color('#B9B5AA').box(0, 0, 0, 24, 54, 8);
      // three piers of the air gap
      for (const y of [-19, 0, 19]) b.color('#C9C5BB').box(0, y, 8, 12, 7, 8);
      b.color('#CFCBC0').box(0, 0, 16, 27.7, 57.4, 18.6);
      b.color('#9E9A90').box(0, 0, 34.6, 24, 50, 1.4);
    });
  },
  replaces: [R_marcel],
  facts: {
    Built: 'built 1968–1970 for the Armstrong Rubber Company (Marcel Breuer and Robert Gatje); Pirelli’s from 1988 (Pirelli moved out in May 1999); today the Hotel Marcel; nine storeys with concrete panels',
    Model: 'plan from the footprint (57 x 28 m); the two-storey base, the two-storey gap on three piers and the five-storey upper block as described; every height (about 4 m a storey, 36 m in all) and the pier sizes estimated: LOW'
  },
  sources: [WIKI + 'Hotel_Marcel', OVERTURE]
});

// ====================================================================== Crown Towers (1967)
// Cited: 8 High Street, completed 1967, 22 floors, 222 ft (68 m) (Wikipedia); the tallest
// residential building in New Haven until 360 State Street.
// Overture building d1084d5f-5af6-4474-bd36-6edfa8da217e
const R_crown: V2[] = P(-25.3, -28.0, -9.3, -36.4, 25.7, 28.7, 9.8, 37.2);
NEW_HAVEN.push({
  id: 'crown_towers',
  name: 'Crown Towers',
  kind: 'tower',
  built: [1965.5, 1967.5],
  end: 9999,
  anchor: [-72.932558, 41.306719],
  build: b => {
    b.color('#B7B0A0').prism(R_crown, 0, 4.5);
    b.color('#A79F8E').prism(scale(R_crown, 0.985, 0.97, 28.3), 4.5, 66);
    b.color('#8D8678').prism(scale(R_crown, 0.9, 0.9, 28.3), 66, 67.7);
  },
  replaces: [R_crown],
  facts: {
    Built: 'completed 1967 at 8 High Street; 22 floors; the tallest residential building in New Haven until 360 State Street (2010)',
    Height: '222 ft (68 m)',
    Model: 'plan from the footprint (74 x 18 m); top cited (67.7 m = 222 ft); the base and parapet and the colour estimated; start of work (1965.5) estimated'
  },
  sources: [WIKI + 'Crown_Towers_(New_Haven,_Connecticut)', TALLEST, OVERTURE]
});

// ====================================================================== Hall of Graduate Studies, Swensen Tower (1930-32)
// Cited: James Gamble Rogers, Collegiate Gothic, opened 29 September 1932, a 14-storey tower
// (208 ft, 63 m in the tallest-buildings list; "a 200-foot tower" in the article) (Wikipedia).
// Position: the list's coordinate (41 deg 18' 43" N, 72 deg 55' 46" W) put on the Humanities
// Quadrangle footprint cae0084c-906d-4806-8b76-13786ddd7c70 (anchor -72.929127, 41.312309).
NEW_HAVEN.push({
  id: 'swensen_tower_hgs',
  name: 'Hall of Graduate Studies tower (Swensen Tower)',
  kind: 'tower',
  built: [1930, 1932.75],
  end: 9999,
  anchor: [-72.929127, 41.312309],
  build: b => {
    b.frame(-26, -41, 0, 28.6, () => {
      const stone = '#A89C86';
      b.color(stone).box(0, 0, 0, 13, 13, 46);
      for (const sx of [-1, 1]) for (const sy of [-1, 1]) b.box(sx * 6.5, sy * 6.5, 0, 1.8, 1.8, 49);
      b.color('#B6AA93').box(0, 0, 46, 11, 11, 11);
      for (const sx of [-1, 1]) for (const sy of [-1, 1]) {
        b.color('#B6AA93').box(sx * 5.1, sy * 5.1, 57, 1.6, 1.6, 3.4);
        b.color('#5E6A66').pyramid(rect(sx * 5.1, sy * 5.1, 1.8, 1.8), 60.4, [sx * 5.1, sy * 5.1, 62.6]);
      }
      b.color('#5E6A66').pyramid(rect(0, 0, 9.6, 9.6), 57, [0, 0, 63.4]);
    });
  },
  facts: {
    Built: 'opened 29 September 1932 as the Hall of Graduate Studies (James Gamble Rogers, Collegiate Gothic); the tower was named for David Swensen in 2015; the quadrangle reopened as the Humanities Quadrangle in 2021',
    Height: '208 ft (63 m), 14 floors (the article says "a 200-foot tower")',
    Model: 'top cited (63.4 m = 208 ft); the tower’s plan (13 m square), stages, corner turrets and roof, and its position (about ±20 m, from a coordinate to the second) estimated: LOW'
  },
  sources: [WIKI + 'Humanities_Quadrangle', TALLEST]
});

// ====================================================================== New Haven Coliseum (1968-72, imploded 2007)
// Cited: Kevin Roche (Roche-Dinkeloo); construction 1968, completed 1972, first event 4 October 1972;
// 11,497 seats; 4.5 acres (18,000 m2) of land; the parking garage was built on top of the arena;
// closed 1 September 2002; imploded 20 January 2007 (Wikipedia). Coordinate 41.302490, -72.925454.
// No footprint is left in the modern data: the plan and heights are estimated.
NEW_HAVEN.push({
  id: 'new_haven_coliseum',
  name: 'New Haven Veterans Memorial Coliseum',
  kind: 'building',
  built: [1968, 1972.75],
  end: 2007.05,
  anchor: [-72.925454, 41.30249],
  build: b => {
    b.frame(0, 0, 0, 28, () => {
      b.color('#9A968D').prism(roundedPlan(120, 92), 0, 14);
      // the garage decks on top: four levels of open concrete floors
      for (let k = 0; k < 4; k++) {
        b.color('#B1ADA3').prism(roundedPlan(116, 88), 14 + k * 3.6, 14 + k * 3.6 + 0.7);
        b.color('#7F7B73').prism(roundedPlan(116, 88), 14.7 + k * 3.6, 17.6 + k * 3.6, {top: false});
      }
      b.color('#B1ADA3').prism(roundedPlan(116, 88), 28.4, 29.1);
    });
  },
  facts: {
    Built: 'construction began 1968, completed 1972 (Kevin Roche of Roche-Dinkeloo, who also designed the Knights of Columbus tower beside it): 11,497 seats, the parking garage built on top of the arena',
    Gone: 'closed 1 September 2002; imploded 20 January 2007',
    Model: 'position from Wikipedia’s coordinate; the plan (120 x 92 m, inside the 4.5-acre site) and every height (arena 14 m, garage to 29 m) estimated, no plan or height read: LOW'
  },
  sources: [WIKI + 'New_Haven_Coliseum']
});

// ====================================================================== Soldiers and Sailors Monument, East Rock (1886-87)
// Cited: neoclassical design by Moffit and Doyle, red granite shaft, an observatory and bronze
// statuary, the Angel of Peace on top; work began 1886, dedicated 17 June 1887; 112 ft (34 m)
// (the East Rock article; East Rock Park says 122 ft) on the 366 ft summit; inscribed on its
// south-west, south-east, north-east and north-west faces (Wikipedia). Coordinate 41.32725, -72.90462.
NEW_HAVEN.push({
  id: 'soldiers_sailors_monument_east_rock',
  name: 'Soldiers’ and Sailors’ Monument (East Rock)',
  kind: 'monument',
  built: [1886, 1887.46],
  end: 9999,
  anchor: [-72.90462, 41.32725],
  build: b => {
    b.frame(0, 0, 0, 45, () => {
      b.color('#9C968C').box(0, 0, 0, 20, 20, 0.8).box(0, 0, 0.8, 16.4, 16.4, 0.8).box(0, 0, 1.6, 13, 13, 0.8);
      b.color('#B0A99B').box(0, 0, 2.4, 9.2, 9.2, 7);
      b.color('#5F6F5A');
      for (const sx of [-1, 1]) for (const sy of [-1, 1]) b.box(sx * 5.6, sy * 5.6, 2.4, 2.4, 2.4, 3.4);
      b.color('#9C3B34').frustum(0, 0, 3.0, 2.2, 9.4, 26.4, 8);
      b.color('#B0A99B').box(0, 0, 26.4, 6.6, 6.6, 1.2);
      b.color('#B0A99B').box(0, 0, 27.6, 4.6, 4.6, 2.2);
      b.color('#5F6F5A').frustum(0, 0, 1.3, 0.7, 29.8, 33.2, 8);
      b.pyramid(circle(0, 0, 0.7, 8), 33.2, [0, 0, 34.1]);
    });
  },
  facts: {
    Built: 'work began 1886, dedicated 17 June 1887 before 175,000 people (Moffit and Doyle; bronzes cast by the Ames Manufacturing Company); it honours New Haven’s dead of the Revolution, 1812, the Mexican and Civil wars',
    Height: '112 ft (34 m) on the 366 ft (112 m) summit of East Rock (East Rock Park’s page says 122 ft)',
    Model: 'top cited (34.1 m = 112 ft); the stepped base, the pedestal with four bronze groups, the tapering red granite shaft, the observatory and the Angel of Peace as proportions only, all dimensions estimated; faces turned 45 degrees after the inscriptions’ compass faces'
  },
  sources: [WIKI + "Soldiers'_and_Sailors'_Monument_(New_Haven)", WIKI + 'East_Rock', WIKI + 'East_Rock_Park']
});

// ====================================================================== 195 Church Street (1974)
// Cited: 270 ft (82 m) roof, 18 floors, completed 1974, postmodern, William Pederson; formerly the
// New Haven Savings Bank Tower (Wikipedia). Footprint (today KeyBank) height 80 m.
// Overture building 7a060433-f11e-4697-97b7-93526b5a35e7
const R_195: V2[] = P(30.6, 4.0, -4.5, 23.5, -17.1, 22.1, -25.8, 27.4, -24.9, 19.0, -34.0, 1.5, -7.4, -13.2, -4.4, -7.4, -1.1, -6.3, -0.3, -7.9, 0.0, -10.3, 1.9, -11.1, 3.2, -9.0, 2.2, -6.7, 3.1, -5.1, 16.1, -11.7, 9.9, -22.6, 23.6, -30.2, 33.1, -13.4);
NEW_HAVEN.push({
  id: 'church_street_195',
  name: '195 Church Street (New Haven Savings Bank Tower)',
  kind: 'tower',
  built: [1972, 1974.5],
  end: 9999,
  anchor: [-72.923875, 41.3078],
  build: b => {
    b.color('#A7A29A').prism(R_195, 0, 6);
    b.color('#B8B3AA').prism(scale(R_195, 0.985, 0.985, 118.8), 6, 76);
    b.color('#8F8A82').prism(scale(R_195, 0.93, 0.93, 118.8), 76, 82.3);
  },
  replaces: [R_195],
  facts: {
    Built: 'completed 1974 (William Pederson), as the New Haven Savings Bank Tower; 18 floors, postmodern; the second-tallest building in New Haven when it was completed',
    Height: '270 ft (82 m)',
    Model: 'plan from the footprint (71 x 34 m, irregular); top cited (82.3 m = 270 ft); the base (6 m), the top stage and the colours estimated; start of work (1972) estimated'
  },
  sources: [WIKI + '195_Church_Street', TALLEST, OVERTURE]
});

// ====================================================================== Smilow Cancer Hospital (2008)
// Cited: 237 ft (72 m), 13 floors, 2008 (Wikipedia, List of tallest buildings in New Haven).
// Overture building 1b782bfc-a004-4684-af76-217d9fb1b703
const R_smilow: V2[] = P(31.9, -29.3, 34.5, -24.1, 20.2, -16.1, 37.9, 16.1, 1.3, 36.5, 2.5, 38.6, -5.4, 42.9, -38.4, -16.8, -33.9, -19.4, -33.0, -17.4, -29.6, -19.8, -30.7, -22.0, -12.3, -32.0, -14.2, -35.1, -5.0, -40.0, -0.9, -31.7, 8.2, -37.2, 17.4, -21.3);
NEW_HAVEN.push({
  id: 'smilow_cancer_hospital',
  name: 'Smilow Cancer Hospital (Yale New Haven Hospital)',
  kind: 'building',
  built: [2006, 2009.2],
  end: 9999,
  anchor: [-72.93584, 41.3051],
  build: b => {
    b.color('#B9B4AA').prism(R_smilow, 0, 22);
    b.color('#9FAAB3').prism(scale(R_smilow, 0.74, 0.74, 28.9), 22, 72);
  },
  replaces: [R_smilow],
  facts: {
    Built: 'completed 2008 (the list’s year; the footprint’s record says 2009): 13 floors, on the campus of Yale New Haven Hospital',
    Height: '237 ft (72 m)',
    Model: 'plan from the footprint (72 x 68 m); top cited (72 m = 237 ft); the split into a 22 m podium and a set-back tower, and the colours estimated, no plan of the tower read; start of work (2006) estimated: LOW'
  },
  sources: [TALLEST, WIKI + 'Yale_New_Haven_Hospital', OVERTURE]
});

/** Rounded rectangle plan, w across and l along. */
function roundedPlan(w: number, l: number): V2[] {
  return roundedRect(0, 0, w, l, 12, 4);
}
