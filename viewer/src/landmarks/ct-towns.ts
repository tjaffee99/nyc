/**
 * Stamford and Bridgeport, Connecticut: landmark models (the towns round, second pass). Research, ids
 * of the footprints and numeric checks: data/research/towns_ct.md.
 *
 * Conventions as new-haven.ts: the anchor is the lon/lat of the footprint (data/interim/counties/
 * ct_western_connecticut.parquet and ct_greater_bridgeport.parquet, Overture Maps 2026-10-21.0) a model
 * replaces, to 6 decimals; plans are that footprint in anchor-local metres (x east, y north), simplified;
 * `b.frame(x, y, z, bearing)` puts a model's +y on a compass bearing. Heights are cited figures where one
 * was read on an opened page, otherwise the footprint's measured height or an estimate named in the
 * `Model:` fact.
 */
import {MeshBuilder, rect, type V2} from './kit';
import type {Landmark} from './types';

const WIKI = 'https://en.wikipedia.org/wiki/';
const OVERTURE = 'https://docs.overturemaps.org/guides/buildings/';

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
  const ux = Math.sin(a);
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

function mean(ring: V2[]): V2 {
  return [ring.reduce((s, p) => s + p[0], 0) / ring.length, ring.reduce((s, p) => s + p[1], 0) / ring.length];
}

export const CT_TOWNS: Landmark[] = [];

// ====================================================================== STAMFORD

// ---------------------------------------------------------------------- One Landmark Square (1973)
// Cited (Wikipedia, One Landmark Square): 22 floors, roof 295 ft (89.9 m), Victor H. Bisharat, built
// 1970-73, neo-futurist, scalloped entrances. Footprint height 89.92 m.
// Overture building 4781c690-1365-4e53-802d-7bbd3acb1ee7
const R_landmark: V2[] = P(9.0, 25.6, 6.6, 28.1, 4.6, 28.3, 3.0, 25.3, -0.8, 25.3, -2.2, 28.8, -6.5, 26.5, -18.2, 25.9, -23.0, 22.5, -24.7, 17.6, -25.3, 9.2, -27.6, 5.1, -26.3, 4.5, -26.6, -0.4, -28.2, -1.1, -27.9, -3.4, -25.8, -5.5, -26.3, -12.8, -25.3, -17.9, -22.1, -22.1, -16.1, -24.3, -8.1, -24.6, -5.3, -27.0, -3.0, -23.2, -0.6, -23.3, 4.0, -28.4, 5.6, -25.5, 17.1, -25.0, 23.0, -21.3, 25.0, -15.3, 25.3, -7.9, 27.9, -4.0, 26.5, -1.9, 26.6, 1.9, 28.1, 3.2, 28.0, 5.0, 26.0, 6.8, 26.4, 13.6, 25.4, 19.3, 23.4, 22.5, 20.8, 24.2, 15.9, 25.5);
function buildLandmark(b: MeshBuilder) {
  const concrete = '#CFC8BA';
  const dark = '#7E7A72';
  b.color(dark).prism(R_landmark, 0, 5.5);
  b.color(concrete).loft([scale(R_landmark, 0.985), scale(R_landmark, 0.975), scale(R_landmark, 0.96)], [5.5, 35, 62]);
  b.color('#6D737A').prism(scale(R_landmark, 0.96), 62, 64);
  b.color(concrete).loft([scale(R_landmark, 0.96), scale(R_landmark, 0.93)], [64, 86]);
  b.color(dark).prism(scale(R_landmark, 0.93), 86, 87.6);
  b.color('#A9A59C').box(0, 0, 87.6, 13, 13, 2.32);
}
CT_TOWNS.push({
  id: 'one_landmark_square',
  name: 'One Landmark Square',
  kind: 'tower',
  built: [1970, 1973.5],
  end: 9999,
  anchor: [-73.538058, 41.054713],
  build: buildLandmark,
  replaces: [R_landmark],
  facts: {
    Built: 'construction began 1970, completed 1973 for F. D. Rich Company (Victor H. Bisharat; neo-futurist, scalloped entrances); the centrepiece of Stamford’s urban renewal, tallest building between New York and Boston until 1990',
    Height: '295 ft (89.9 m), 22 floors',
    Model: 'plan from the footprint (about 56 x 56 m); roof height cited (295 ft); the podium (5.5 m), the slight taper and the window bands are estimated; start of building (1970) cited'
  },
  sources: [WIKI + 'One_Landmark_Square', WIKI + 'Downtown_Stamford', OVERTURE]
});

// ---------------------------------------------------------------------- Park Tower Stamford (2009)
// Cited (Wikipedia, Park Tower Stamford): 36-story / 34-floor glass condominium tower, 350 ft (106.7 m),
// opened September 2009, groundbreaking 15 May 2007, 6-story parking podium. Footprint height 106.68 m.
// Overture building 3021f176-a56d-47a9-b62a-39160279efd4
const R_park: V2[] = P(10.6, -22.2, 16.3, -22.3, 19.7, 11.3, 19.0, 11.4, 19.9, 20.3, 15.3, 20.3, 15.9, 25.0, -14.9, 26.4, -15.5, 21.2, -12.8, 21.7, -16.2, 12.2, -18.1, 3.3, -19.0, -6.5, -19.3, -6.6, -21.4, -23.0, -20.5, -23.2, -20.9, -26.7, 10.7, -27.0);
function buildPark(b: MeshBuilder) {
  b.color('#8D887C').prism(R_park, 0, 17.5);
  b.color('#6F93AB').loft([scale(R_park, 0.84, 0.8, 5.7), scale(R_park, 0.82, 0.78, 5.7)], [17.5, 100]);
  b.color('#5E7F96').loft([scale(R_park, 0.82, 0.78, 5.7), scale(R_park, 0.66, 0.6, 5.7)], [100, 106.68]);
}
CT_TOWNS.push({
  id: 'park_tower_stamford',
  name: 'Park Tower Stamford',
  kind: 'tower',
  built: [2007.4, 2009.7],
  end: 9999,
  anchor: [-73.542802, 41.05526],
  build: buildPark,
  replaces: [R_park],
  facts: {
    Built: 'groundbreaking 15 May 2007, opened September 2009 (Costas Kondylis and Lessard Design; as Trump Parc Stamford until 2013); the tallest building in Stamford',
    Height: '350 ft (106.7 m), 34 floors above a 6-story parking podium',
    Model: 'plan from the footprint (55 x 37 m); height cited (350 ft); the podium height (17.5 m) and the glass colour estimated'
  },
  sources: [WIKI + 'Park_Tower_Stamford', WIKI + 'Downtown_Stamford', OVERTURE]
});

// ---------------------------------------------------------------------- Atlantic Station (2017)
// Cited (Wikipedia, Downtown Stamford): completed 2017 by RXR Realty, 26 stories, 315 ft (96.0 m), the
// second tallest building in Stamford. Footprint height 93.0 m (3 % lower).
// Overture building 0eb7f9bf-886f-4a2c-bf9e-6f088b99f5f0
const R_atlantic: V2[] = P(28.2, 20.0, -26.9, 21.8, -28.9, -40.6, 26.2, -42.3);
function buildAtlantic(b: MeshBuilder) {
  b.color('#A39B8D').prism(R_atlantic, 0, 15);
  b.color('#7C98AD').loft([scale(R_atlantic, 0.76, 0.72, 1.9), scale(R_atlantic, 0.75, 0.71, 1.9)], [15, 88]);
  b.color('#9AA2A8').prism(scale(R_atlantic, 0.6, 0.55, 1.9), 88, 96);
}
CT_TOWNS.push({
  id: 'atlantic_station_stamford',
  name: 'Atlantic Station',
  kind: 'tower',
  built: [2015, 2017],
  end: 9999,
  anchor: [-73.540051, 41.050507],
  build: buildAtlantic,
  replaces: [R_atlantic],
  facts: {
    Built: 'completed 2017 by RXR Realty; 325 apartments, retail and a 333-space garage; a second tower was under construction beside it',
    Height: '315 ft (96.0 m), 26 stories; the second tallest building in Stamford',
    Model: 'plan from the footprint (62 x 55 m); height cited (315 ft; the footprint’s mapped height is 93 m); the podium (15 m), the set-back crown and the colours estimated; start of building (2015) estimated'
  },
  sources: [WIKI + 'Downtown_Stamford', OVERTURE]
});

// ---------------------------------------------------------------------- First Presbyterian "Fish Church" (1958)
// Cited (Wikipedia, Fish Church): Wallace K. Harrison, sanctuary dedicated March 1958, 60-ft (18 m) nave,
// 260-ft (79.2 m) Maguire Memorial Tower with a 56-bell carillon. Footprint height 6.6 m (low parts).
// Overture building 74f16290-e606-4069-ae58-b18f39479e67
const R_fish: V2[] = P(20.7, -0.2, 24.8, 0.4, 25.3, 2.3, 36.6, 1.2, 35.2, 9.0, 25.1, 6.3, 23.1, 19.1, 29.8, 20.1, 29.3, 23.3, 59.8, 28.0, 63.8, 2.4, 62.8, 2.3, 64.8, -10.8, 79.2, -11.1, 78.9, -9.6, 91.3, -7.7, 94.5, -31.8, 99.4, -32.7, 98.0, -40.0, 112.0, -42.6, 124.8, -35.8, 121.2, -29.1, 127.4, -25.9, 119.5, -10.9, 113.2, -14.1, 112.5, -12.8, 102.7, -14.5, 102.5, -16.0, 96.6, -15.0, 93.1, 7.0, 78.3, 4.7, 72.4, 42.6, 61.2, 40.8, 61.3, 40.2, 20.9, 33.9, 22.5, 23.3, 17.8, 22.6, 19.7, 10.0, -4.5, 13.4, -4.1, 16.5, -16.4, 18.3, -16.9, 15.1, -22.4, 15.9, -28.6, 13.0, -22.3, -0.5, -31.8, -2.3, -32.2, -8.8, -18.3, -8.3, 8.8, -6.4);
const R_fish_nave: V2[] = P(61.0, 20.0, 61.2, 40.8, 72.4, 42.6, 78.3, 4.7, 93.1, 7.0, 96.6, -15.0, 102.5, -16.0, 102.7, -14.5, 112.5, -12.8, 113.2, -14.1, 119.5, -10.9, 127.4, -25.9, 121.2, -29.1, 124.8, -35.8, 112.0, -42.6, 98.0, -40.0, 99.4, -32.7, 94.5, -31.8, 91.3, -7.7, 78.9, -9.6, 79.2, -11.1, 64.8, -10.8, 62.8, 2.3, 63.8, 2.4);
function buildFish(b: MeshBuilder) {
  b.color('#8B7F72').prism(R_fish, 0, 6.6);
  b.color('#A89C8C').prism(R_fish_nave, 6.6, 18.3);
  b.color('#4D4B49').prism(scale(R_fish_nave, 0.9), 18.3, 19.2);
  b.frame(16.6, 4.4, 0, 0, () => {
    b.color('#BDB5A5').box(0, 0, 0, 6.6, 6.6, 66);
    b.color('#9A937F').box(0, 0, 66, 7.4, 7.4, 8);
    b.color('#5F6B66').pyramid(rect(0, 0, 7.4, 7.4), 74, [0, 0, 79.25]);
  });
}
CT_TOWNS.push({
  id: 'fish_church_stamford',
  name: 'First Presbyterian Church (Fish Church)',
  kind: 'building',
  built: [1956, 1958.2],
  end: 9999,
  anchor: [-73.539071, 41.062947],
  build: buildFish,
  replaces: [R_fish],
  facts: {
    Built: 'sanctuary dedicated March 1958, Wallace K. Harrison (architect of the United Nations headquarters); the fish shape is in both profile and plan; 20,000 pieces of faceted stained glass',
    Height: 'nave 60 ft (18 m); Maguire Memorial Tower 260 ft (79.2 m) with a 56-bell carillon',
    Model: 'footprint from the map (L-shaped, 3,400 m2); tower and nave heights cited; WHICH PART of the footprint is the sanctuary and WHERE the tower stands are guesses (LOW), as are the colours and the lid of the nave; start of building estimated'
  },
  sources: [WIKI + 'Fish_Church', WIKI + 'Downtown_Stamford', OVERTURE]
});

// ---------------------------------------------------------------------- Old Town Hall (1907)
// Cited (Wikipedia, Old Town Hall (Stamford)): Beaux-Arts, Mellon and Josselyn, built 1905-07, opened
// 20 March 1907, limestone facade with a clock tower, five levels across three stories. No height published.
// Overture building aca65a09-7cfb-4948-a687-c807e584c5dd (no mapped height)
const R_oth: V2[] = P(-10.4, -22.0, -18.1, -21.9, -18.5, -29.4, -2.6, -30.1, -2.8, -22.4, 19.1, 11.0, -7.5, 29.0, -14.7, 29.1, -17.0, 0.6, -7.0, -0.5, -8.9, -3.5);
function buildOth(b: MeshBuilder) {
  b.color('#D8D2C2').prism(R_oth, 0, 15.5);
  b.color('#C6BFAC').prism(R_oth, 15.5, 16.6);
  b.color('#5A6068').loft([scale(R_oth, 0.97), scale(R_oth, 0.85)], [16.6, 21]);
  b.frame(12.3, 9.6, 0, 0, () => {
    b.color('#D8D2C2').box(0, 0, 14, 7, 7, 17);
    b.color('#E6E1D2').box(0, 0, 31, 8, 8, 4);
    b.color('#6E8F7E').pyramid(rect(0, 0, 8.6, 8.6), 35, [0, 0, 41]);
  });
}
CT_TOWNS.push({
  id: 'old_town_hall_stamford',
  name: 'Old Town Hall',
  kind: 'building',
  built: [1905, 1907.2],
  end: 9999,
  anchor: [-73.540631, 41.052827],
  build: buildOth,
  replaces: [R_oth],
  facts: {
    Built: 'built 1905-07, opened 20 March 1907 (Mellon and Josselyn, Beaux-Arts); Stamford’s seat of government until 1963; the Stamford Innovation Center since 2012',
    Height: 'three stories on five levels, a limestone facade and a clock tower; no height published',
    Model: 'plan from the footprint (the triangular block at Main and Atlantic streets, 1,170 m2); the wall height (15.5 m), the mansard, and the clock tower’s place and height (41 m) are estimated (LOW); the footprint has no mapped height'
  },
  sources: [WIKI + 'Old_Town_Hall_(Stamford,_Connecticut)', WIKI + 'Downtown_Stamford', OVERTURE]
});

// ---------------------------------------------------------------------- Basilica of St. John the Evangelist (1868)
// Cited (Wikipedia, Basilica of Saint John the Evangelist): present church built 1868 (James Murphy),
// seats 1,600, exterior dimensions 100 x 180 ft (30.5 x 54.9 m). Footprint height 23.0 m (ridge).
// Overture building 991737d5-e22c-449b-be49-aacbb8994e27 (named Saint Johns Catholic Church)
const R_basilica: V2[] = P(22.6, -14.7, 22.9, -11.9, 24.6, -12.0, 24.8, -9.5, 24.2, -9.4, 25.4, 5.6, 26.3, 5.5, 26.9, 12.6, 19.9, 13.2, 19.7, 10.8, 5.9, 12.0, 6.2, 15.7, -10.2, 17.1, -10.5, 13.5, -14.5, 13.9, -15.0, 15.9, -17.3, 18.1, -20.2, 18.3, -22.6, 16.8, -23.7, 14.1, -25.8, -9.6, -16.6, -10.3, -16.4, -7.8, -12.2, -8.1, -12.5, -11.4, 3.9, -12.7, 4.1, -9.8, 8.5, -10.5, 8.5, -10.0, 12.7, -10.3, 13.3, -10.9, 13.1, -13.5, 17.0, -13.9, 17.2, -11.2, 18.1, -11.3, 17.9, -14.2);
function buildBasilica(b: MeshBuilder) {
  b.color('#9A9183').prism(R_basilica, 0, 12.5);
  b.frame(0.5, 1.9, 12.5, 95.4, () => {
    b.color('#4C5057').gable(0, 0, 23.5, 44, 0, 10.5, true);
  });
}
CT_TOWNS.push({
  id: 'st_john_basilica_stamford',
  name: 'Basilica of St. John the Evangelist',
  kind: 'building',
  built: [1866.5, 1868.5],
  end: 9999,
  anchor: [-73.540016, 41.051743],
  build: buildBasilica,
  replaces: [R_basilica],
  facts: {
    Built: 'the present church was built in 1868 (James Murphy of Providence; the first church on Meadow Street dated from 1851); a minor basilica',
    Height: 'ridge 23 m (the footprint’s mapped height); no spire height published; exterior 100 x 180 ft',
    Model: 'plan from the footprint (50.6 x 28.9 m); ridge height is the mapped one; the eave height (12.5 m), the slate roof and the stone colour are estimated and NO tower or spire is modelled (none could be placed from an opened page); start of building estimated'
  },
  sources: [WIKI + 'Basilica_of_Saint_John_the_Evangelist', OVERTURE]
});

// ====================================================================== BRIDGEPORT

// ---------------------------------------------------------------------- Bridgeport Center (1989)
// Cited (Wikipedia, Bridgeport Center): Richard Meier & Partners, built 1984-89, 18 floors, red wing roof
// 248 ft (75.6 m), main roof 267 ft (81.4 m), 7-story garage on the east base. Footprint height 76.0 m.
// Overture building 6f9ff273-8632-4336-ba5d-9bed6bba2ce0
const R_bc: V2[] = P(29.1, -67.6, 4.5, -14.5, 17.9, -6.1, 27.3, 4.5, 31.7, 14.5, 33.7, 22.2, 34.2, 36.4, 32.5, 46.1, 29.8, 52.4, 45.8, 59.7, 40.8, 82.2, 38.5, 81.4, 36.2, 91.4, -48.4, 73.9, -44.8, 53.1, -27.0, 57.0, -22.8, 46.9, -18.6, 48.0, -17.5, 43.0, -13.8, 43.1, -7.5, 40.6, -3.9, 35.3, -3.3, 31.3, -4.3, 26.4, -6.9, 22.8, -12.4, 20.2, -10.3, 10.4, -19.5, 8.5, -22.6, 5.8, -23.6, 1.3, -21.8, -3.2, -17.0, -6.2, -16.4, -7.7, -14.5, -8.4, -6.7, -6.5, 5.8, -64.8, -5.0, -66.8, -3.7, -73.3, -6.9, -73.9, -4.3, -85.0, -3.0, -86.9, -1.3, -87.9, 5.4, -87.9, 11.2, -90.2, 15.7, -88.9);
const R_bc_red: V2[] = P(27.3, 4.5, 17.9, -6.1, 4.5, -14.5, 29.1, -67.6, 19.5, -83.5, 15.7, -88.9, 11.2, -90.2, 8.2, -89.5, 5.4, -87.9, -1.3, -87.9, -3.0, -86.9, -4.3, -85.0, -6.9, -73.9, -3.7, -73.3, -5.0, -66.8, 5.8, -64.8, -6.7, -6.5, -14.5, -8.4, -16.4, -7.7, -17.0, -6.2, -21.8, -3.2, -23.0, -1.3, -23.6, 1.3, -23.4, 3.5, -22.6, 5.8, -19.5, 8.5, -13.8, 10.0, 29.7, 10.0);
const R_bc_white: V2[] = P(-10.3, 10.4, -12.4, 20.2, -6.9, 22.8, -4.3, 26.4, -3.3, 31.3, -3.9, 35.3, -5.3, 38.1, -7.5, 40.6, -10.7, 42.3, -13.8, 43.1, -17.5, 43.0, -18.6, 48.0, -22.8, 46.9, -27.0, 57.0, -44.8, 53.1, -48.4, 73.9, 36.2, 91.4, 38.5, 81.4, 40.8, 82.2, 45.8, 59.7, 29.8, 52.4, 32.5, 46.1, 34.2, 36.4, 33.7, 22.2, 31.7, 14.5, 29.7, 10.0, -13.8, 10.0);
function buildBc(b: MeshBuilder) {
  b.color('#B4AFA5').prism(R_bc, 0, 21);
  b.color('#9B5B50').prism(R_bc_red, 21, 75.6);
  b.color('#9B5B50').prism(scale(R_bc_red, 0.78), 75.6, 81.4);
  b.color('#E3E1DB').prism(R_bc_white, 21, 58);
}
CT_TOWNS.push({
  id: 'bridgeport_center',
  name: 'Bridgeport Center (People’s Bank Building)',
  kind: 'tower',
  built: [1984, 1989.5],
  end: 9999,
  anchor: [-73.18804, 41.176162],
  build: buildBc,
  replaces: [R_bc],
  facts: {
    Built: 'construction began 1984, completed 1989 (Richard Meier & Partners) as the headquarters of People’s Bank, later People’s United, now M&T Bank; replaced the Bridgeport National Bank building',
    Height: '18 floors; red wing 248 ft (75.6 m), main roof 267 ft (81.4 m)',
    Model: 'plan from the footprint (6,850 m2); red-wing roof and main roof cited; the split between red and white parts (cut at the footprint’s middle), the 21 m base and the 58 m height of the white block are estimated (LOW)'
  },
  sources: [WIKI + 'Bridgeport_Center', OVERTURE]
});

// ---------------------------------------------------------------------- City Trust Apartments (1929)
// Cited (Wikipedia, City Trust Apartments): Art Deco, Dennison & Hirons, 955 Main Street, completed 1929,
// 10 floors, roof 165 ft (50.3 m). No mapped footprint height.
// Overture building 685c1597-2266-4352-b4f2-6fad089a80c4 (found by the article coordinates, 0 m)
const R_trust: V2[] = P(11.8, 10.6, -44.4, -12.5, -39.0, -26.1, 0.2, -10.7, 2.2, -15.0, 16.5, -11.6);
function buildTrust(b: MeshBuilder) {
  b.color('#C9BC9F').prism(R_trust, 0, 14);
  b.color('#D8CDB4').loft([scale(R_trust, 0.97, 0.97, 68.4), scale(R_trust, 0.94, 0.95, 68.4)], [14, 36]);
  b.color('#CFC3A8').loft([scale(R_trust, 0.8, 0.9, 68.4), scale(R_trust, 0.72, 0.84, 68.4)], [36, 45]);
  b.color('#B7AA8C').loft([scale(R_trust, 0.55, 0.7, 68.4), scale(R_trust, 0.4, 0.55, 68.4)], [45, 50.3]);
}
CT_TOWNS.push({
  id: 'city_trust_bridgeport',
  name: 'City Trust Apartments',
  kind: 'tower',
  built: [1927, 1929.5],
  end: 9999,
  anchor: [-73.189279, 41.177649],
  build: buildTrust,
  replaces: [R_trust],
  facts: {
    Built: 'completed 1929 (Dennison & Hirons of New York, Art Deco) as the City Trust Company’s tower at 955 Main Street; apartments and offices today',
    Height: '165 ft (50.3 m), 10 floors',
    Model: 'plan from the footprint (about 61 x 22 m, matched to the article’s coordinates); roof cited (165 ft); the base height (14 m), the set-backs and the stone colour estimated (LOW); start of building estimated'
  },
  sources: [WIKI + 'City_Trust_Apartments', OVERTURE]
});

// ---------------------------------------------------------------------- St. Augustine Cathedral (1868)
// Cited (Wikipedia, St. Augustine Cathedral (Bridgeport)): cornerstone 28 Aug 1865, dedicated 17 March 1868,
// Patrick C. Keely, Gothic Revival, height 180.5 ft (55.0 m). Footprint height 9.8 m.
// Overture building 449d69c0-e40f-49e0-b986-e8d0874066ab (named Saint Augustine Cathedral)
const R_staug: V2[] = P(-3.7, 12.8, -3.6, 14.8, -4.9, 17.3, -18.9, 22.2, -28.6, -6.6, -19.4, -9.7, -19.1, -8.9, -15.2, -10.2, -12.2, -9.6, -11.2, -8.5, 20.0, -18.9, 21.6, -14.1, 22.5, -14.4, 23.4, -11.7, 25.2, -12.3, 27.3, -6.1, 25.4, -5.5, 26.4, -2.8, 25.5, -2.5, 27.2, 2.5);
function buildStAug(b: MeshBuilder) {
  b.color('#8F8A82').prism(R_staug, 0, 13);
  b.frame(1.3, -0.6, 13, 108.6, () => {
    b.color('#4B4E52').gable(0, 0, 19, 46, 0, 8.5, true);
  });
  b.frame(-20.6, 4.5, 0, 108.6, () => {
    b.color('#8F8A82').box(0, 0, 0, 8, 8, 34);
    b.color('#9A958D').box(0, 0, 34, 6.6, 6.6, 6);
    b.color('#4B4E52').pyramid(rect(0, 0, 6.6, 6.6), 40, [0, 0, 55.02]);
  });
}
CT_TOWNS.push({
  id: 'st_augustine_cathedral_bridgeport',
  name: 'St. Augustine Cathedral',
  kind: 'building',
  built: [1865.65, 1868.2],
  end: 9999,
  anchor: [-73.195703, 41.180251],
  build: buildStAug,
  replaces: [R_staug],
  facts: {
    Built: 'cornerstone laid 28 August 1865, dedicated 17 March 1868 (Patrick C. Keely, Gothic Revival); seat of the Diocese of Bridgeport; renovated 2003-04',
    Height: '180.5 ft (55.0 m)',
    Model: 'plan from the footprint (53 x 30 m); the height of the tallest part is cited, but the tower’s place (west end) and its stages, the nave eave (13 m) and roof are estimated (LOW)'
  },
  sources: [WIKI + 'St._Augustine_Cathedral_(Bridgeport,_Connecticut)', OVERTURE]
});

// ---------------------------------------------------------------------- Fairfield County Courthouse (1888)
// Cited (Wikipedia): Richardsonian Romanesque, brick with brownstone and terra cotta, Warren R. Briggs,
// built 1888, three stories on an ashlar granite base, a six-story central tower with a pyramidal roof.
// Footprint height 15.9 m (the main roof). 172 Golden Hill Street.
// Overture building 3a230949-3e5b-45ba-9f58-d5d9ac2450a2
const R_ch: V2[] = P(14.3, 31.0, 8.3, 29.1, 9.1, 26.4, -8.7, 20.9, -9.4, 23.1, -14.0, 21.7, -13.3, 19.4, -27.2, 15.1, -28.0, 17.8, -35.4, 15.5, -27.0, -11.0, -23.3, -9.9, -20.8, -18.2, -21.4, -19.8, -20.8, -21.8, -18.8, -23.2, -15.7, -22.7, -14.3, -19.7, -1.1, -15.4, -0.5, -16.9, 1.1, -17.5, 4.5, -17.0, 5.9, -15.5, 5.7, -13.6, 20.4, -8.9, 20.7, -10.2, 22.8, -11.5, 25.9, -10.6, 27.2, -8.3, 26.9, -6.9, 32.2, -5.2, 28.9, 5.3, 31.1, 6.0, 27.1, 18.6, 24.9, 18.0, 21.1, 30.1, 15.2, 28.3);
function buildCh(b: MeshBuilder) {
  b.color('#7A6C60').prism(R_ch, 0, 2.4);
  b.color('#9E4B3B').prism(R_ch, 2.4, 12.6);
  b.color('#4D4A49').loft([scale(R_ch, 0.99), scale(R_ch, 0.5)], [12.6, 15.9]);
  b.frame(1.4, -11.0, 0, 72.7, () => {
    b.color('#9E4B3B').box(0, 0, 8, 9, 9, 19);
    b.color('#B4A590').box(0, 0, 27, 9.6, 9.6, 1.4);
    b.color('#4D4A49').pyramid(rect(0, 0, 9.6, 9.6), 28.4, [0, 0, 37]);
  });
}
CT_TOWNS.push({
  id: 'fairfield_county_courthouse_bridgeport',
  name: 'Fairfield County Courthouse',
  kind: 'building',
  built: [1886.5, 1888.5],
  end: 9999,
  anchor: [-73.190901, 41.180536],
  build: buildCh,
  replaces: [R_ch],
  facts: {
    Built: 'built 1888 (Warren R. Briggs) when the old city hall and courthouse (McLevy Hall) proved too small; Richardsonian Romanesque in brick, brownstone and terra cotta; National Register 1982',
    Height: 'three stories with a six-story central tower under a pyramidal roof; no tower height published',
    Model: 'plan from the footprint (60 x 43 m); the main roof is the mapped 15.9 m; the tower’s place on the Golden Hill Street front and its height (37 m), the eave height and the colours are estimated (LOW)'
  },
  sources: [WIKI + 'Fairfield_County_Courthouse_(Bridgeport,_Connecticut)', OVERTURE]
});

// ---------------------------------------------------------------------- McLevy Hall (1854)
// Cited (Wikipedia, McLevy Hall): built 1854 (A. J. Davis, J. W. Northrop) for the City Hall and the county
// courthouse, 202 State Street, Greek Revival / Classical Revival; city hall until the 1930s.
// Footprint height 9.7 m. Overture building aa06abd4-2bdc-4b60-80ad-62ac60d948d1 (named McLevy Hall)
const R_mclevy: V2[] = P(-15.6, 13.7, -1.4, -20.6, 15.6, -13.6, 1.4, 20.6);
function buildMcLevy(b: MeshBuilder) {
  b.color('#D6CDB6').prism(R_mclevy, 0, 7.6);
  b.frame(0, 0, 7.6, 157.5, () => {
    b.color('#59595C').gable(0, 0, 19.6, 38.6, 0, 2.1, true);
    // the portico at the +y end: four columns and a pediment
    for (const x of [-6.6, -2.2, 2.2, 6.6]) b.color('#EEE9DA').cylinder(x, 20.4, 0.5, -7.6, 7.0, 8);
    b.color('#EEE9DA').gable(0, 20.4, 15.4, 3.4, 7.0, 2.4, false);
    b.color('#E9E3D0').box(0, 0, 9.7, 3.6, 3.6, 2.8);
    b.color('#59595C').pyramid(rect(0, 0, 3.8, 3.8), 12.5, [0, 0, 14.6]);
  });
}
CT_TOWNS.push({
  id: 'mclevy_hall_bridgeport',
  name: 'McLevy Hall (old City Hall)',
  kind: 'building',
  built: [1852, 1854.5],
  end: 9999,
  anchor: [-73.189868, 41.176816],
  build: buildMcLevy,
  replaces: [R_mclevy],
  facts: {
    Built: 'built 1854 (Alexander Jackson Davis and J. W. Northrop) to house both the City Hall and the Fairfield County Courthouse; Bridgeport’s city hall into the 1930s; renamed for Mayor Jasper McLevy in 1966',
    Height: 'footprint height 9.7 m (mapped); no other height published',
    Model: 'plan from the footprint (37 x 18 m); the walls (7.6 m) and the ridge (9.7 m, the mapped height) follow the footprint; the portico (which end), the cupola and its height (14.6 m) are estimated (LOW)'
  },
  sources: [WIKI + 'McLevy_Hall', OVERTURE]
});

// ---------------------------------------------------------------------- Total Mortgage Arena (2001)
// Cited (Wikipedia, Total Mortgage Arena): 10,000 seats, opened 10 October 2001, cost $56.3 m. No
// published height; the footprint's mapped height is 12.0 m. Overture building b271ff84-1a78-42bd-bfa1-64f3b4f7b051
const R_arena: V2[] = P(7.2, -35.1, 12.2, -53.4, 27.8, -65.1, 40.0, -61.8, 35.0, -43.3, 25.2, -37.9, 23.2, -30.7, 62.7, -20.2, 52.1, 33.1, 43.6, 62.6, 15.2, 54.3, 16.4, 49.9, 2.3, 45.8, 3.6, 40.3, -26.1, 32.1, -27.7, 38.2, -44.2, 32.5, -42.3, 27.7, -50.3, 21.7, -58.1, 27.2, -62.9, 21.7, -55.9, 16.4, -58.4, 4.8, -58.9, -4.7, -53.5, -23.0, -47.7, -28.4, -57.9, -30.9, -52.6, -50.6, -23.1, -42.9, -23.0, -43.5);
function buildArena(b: MeshBuilder) {
  b.color('#9C6D5A').prism(R_arena, 0, 9);
  b.color('#8E969D').prism(R_arena, 9, 12);
  b.color('#7C858C').loft([scale(R_arena, 0.66), scale(R_arena, 0.58)], [12, 17]);
}
CT_TOWNS.push({
  id: 'total_mortgage_arena',
  name: 'Total Mortgage Arena',
  kind: 'stadium',
  built: [1999.6, 2001.78],
  end: 9999,
  anchor: [-73.186896, 41.173235],
  build: buildArena,
  replaces: [R_arena],
  facts: {
    Built: 'opened 10 October 2001 as The Arena at Harbor Yard (later Webster Bank Arena); 10,000 seats; home of the Bridgeport Islanders (AHL) 2001-2026',
    Height: 'no published height; the footprint’s mapped height is 12.0 m',
    Model: 'plan from the footprint (about 123 x 119 m); the 12 m is the mapped height; the raised bowl roof (17 m) and the brick base are estimated; start of building estimated'
  },
  sources: [WIKI + 'Total_Mortgage_Arena', OVERTURE]
});

// ---------------------------------------------------------------------- Hartford HealthCare Amphitheater (2021)
// Cited (Wikipedia, The Ballpark at Harbor Yard): the ballpark (1998-2017) was converted to a concert
// amphitheater, groundbreaking July 2018, opened 28 July 2021. Footprint height 20.7 m (the roof).
// Overture building f2721da2-cf30-4ddb-a943-d38e967d208c
const R_amph: V2[] = P(66.3, 35.6, 45.7, 56.2, 33.1, 65.2, 11.5, 38.9, 9.8, 35.4, 27.2, 20.5, 13.8, 7.0, -7.0, 12.1, -11.9, 22.6, -8.9, 30.1, -14.8, 50.2, -30.2, 51.1, -35.6, 37.7, -44.6, 39.2, -55.0, -25.1, -52.8, -32.2, -54.0, -32.6, -50.3, -46.4, -48.7, -46.0, -47.2, -51.2, -44.1, -56.8, -29.9, -70.3, -18.2, -72.7, -18.8, -74.9, -4.9, -78.3, -4.4, -76.1, 2.7, -77.8, 32.3, -71.9, 30.7, -63.9, 58.7, -58.4, 65.6, -58.2, 61.6, -44.6, 63.2, -38.5, 61.1, -34.7, 60.2, -24.9, 72.8, -11.5, 68.6, -6.9, 62.2, -11.1, 41.2, 9.6);
function buildAmph(b: MeshBuilder) {
  const c = mean(R_amph);
  b.color('#A5A7A9').prism(R_amph, 0, 7);
  b.color('#EAE9E3').pyramid(scale(R_amph, 0.82), 7, [c[0], c[1], 20.7]);
}
CT_TOWNS.push({
  id: 'hartford_healthcare_amphitheater',
  name: 'Hartford HealthCare Amphitheater',
  kind: 'stadium',
  built: [2018.6, 2021.6],
  end: 9999,
  anchor: [-73.187612, 41.171988],
  build: buildAmph,
  replaces: [R_amph],
  facts: {
    Built: 'the Ballpark at Harbor Yard (opened 21 May 1998, closed after the 2017 season) was rebuilt as a concert amphitheater: groundbreaking July 2018, opened 28 July 2021',
    Height: 'no published height; the footprint’s mapped height is 20.7 m',
    Model: 'plan from the footprint (134 x 131 m); the tent’s apex is the mapped 20.7 m; the concourse height (7 m) and the tent’s shape (a single pyramid) are estimated (LOW)'
  },
  sources: [WIKI + 'The_Ballpark_at_Harbor_Yard', OVERTURE]
});

// ---------------------------------------------------------------------- Palace and Majestic Theaters (1922)
// Cited (Wikipedia, Palace and Majestic Theaters): built 1921-22 by Sylvester Z. Poli, Thomas W. Lamb,
// five stories, steel and reinforced concrete, Beaux-Arts, 1315-1357 Main Street; closed 1971 / 1975.
// No mapped height. Overture building 639ab9c5-0c03-40eb-a4c0-3b1e9c2f85ab
const R_palace: V2[] = P(-31.0, -22.9, -14.5, -48.3, 49.1, -12.4, 14.7, 41.9, -45.8, 10.9, -36.7, -10.8);
function buildPalace(b: MeshBuilder) {
  b.color('#B8A888').prism(R_palace, 0, 6);
  b.color('#DAD0B8').prism(R_palace, 6, 22.5);
  b.color('#C8BEA4').prism(R_palace, 22.5, 24);
}
CT_TOWNS.push({
  id: 'palace_majestic_bridgeport',
  name: 'Palace and Majestic Theaters',
  kind: 'building',
  built: [1921, 1922.5],
  end: 9999,
  anchor: [-73.191178, 41.182409],
  build: buildPalace,
  replaces: [R_palace],
  facts: {
    Built: 'built 1921-22 by Sylvester Z. Poli to the design of Thomas W. Lamb: two theaters and a hotel in one block of Main Street; the Majestic closed in 1971, the Palace in 1975; vacant since; National Register 1979',
    Height: 'five stories; no height published',
    Model: 'plan from the footprint (75 x 67 m, the whole block); the height (24 m from five stories of about 4.5 m), the base band and the colours are estimated; no stage house or sign is modelled'
  },
  sources: [WIKI + 'Palace_and_Majestic_Theaters', OVERTURE]
});
