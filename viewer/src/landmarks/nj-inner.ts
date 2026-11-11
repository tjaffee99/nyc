/**
 * New Jersey landmarks of the five counties on the map (Hudson, Essex, Bergen, Passaic, Union).
 * Research and numeric checks: data/research/landmarks_nj_inner.md.
 *
 * Conventions as nyc-civic.ts: the anchor is a point on (or beside) the building; plans are
 * the footprints of data/interim/county_buildings.parquet (Overture / state footprints)
 * re-expressed in a model frame (`b.frame(ox, oy, 0, bearing)`, +y pointing at `bearing`,
 * origin at the footprint's vertex mean); heights are cited figures where one exists, and
 * everything else is named as an estimate in each model's `Model:` fact.
 */
import {MeshBuilder, rect, roundedRect, type V2} from './kit';
import type {Landmark} from './types';

const WIKI = 'https://en.wikipedia.org/wiki/';
const OVERTURE = 'https://docs.overturemaps.org/guides/buildings/';

export const NJ_INNER: Landmark[] = [];

/** Flat list of numbers -> ring. */
function P(...n: number[]): V2[] {
  const o: V2[] = [];
  for (let i = 0; i < n.length; i += 2) o.push([n[i], n[i + 1]]);
  return o;
}

/** Ring given in a model frame (origin ox, oy; +y at `bearing`) -> anchor-local metres. */
function place(ring: V2[], ox: number, oy: number, bearing: number): V2[] {
  const a = (-bearing * Math.PI) / 180;
  const c = Math.cos(a);
  const s = Math.sin(a);
  return ring.map(([x, y]) => [ox + c * x - s * y, oy + s * x + c * y] as V2);
}

/** Ring scaled about its vertex mean (a set-back). */
function scaled(ring: V2[], sx: number, sy = sx): V2[] {
  const cx = ring.reduce((a, p) => a + p[0], 0) / ring.length;
  const cy = ring.reduce((a, p) => a + p[1], 0) / ring.length;
  return ring.map(([x, y]) => [cx + (x - cx) * sx, cy + (y - cy) * sy] as V2);
}

// ====================================================================== Cathedral Basilica of the Sacred Heart, Newark
// Footprint (Overture, named "Cathedral Basilica of the Sacred Heart", 4,564 m2). Frame at the
// vertex mean (1.0, 4.0), +y at 17.5° = the façade end (the narrow end with the two towers,
// toward Branch Brook Park); the chevet with its chapels is at -y. Cited (Wikipedia): length 365 ft
// (111 m), width 165 ft (50 m) at the transept, towers 232 ft (71 m) with no spires after the
// 1913 redesign. The footprint's long axis is longer (about 150 m: it includes attached
// structures) and its nave is narrower than the cited width; the model follows the footprint.
const CATH_RING = P(
  12.6, 36.1, 10.2, 38.5, 11.0, 50.7, 7.5, 50.9, 7.2, 47.3, -0.4, 47.8, 1.9, 74.8, -15.9, 76.2, -19.6, 31.5, -18.7, 31.4, -19.0, 26.7, -21.6, 26.9, -23.5, 3.6,
  -15.9, 3.0, -17.2, -1.9, -18.5, -19.1, -12.1, -19.5, -14.9, -55.4, -23.5, -62.7, -13.9, -72.3, -5.4, -64.1, 6.7, -65.0, 14.9, -73.3, 23.7, -66.3, 15.5, -58.5,
  18.4, -21.7, 26.5, -22.3, 27.9, -5.2, 25.4, 13.6, 19.1, 23.2, 11.5, 25.2
);

function buildCathedral(b: MeshBuilder) {
  const stone = '#B9B3A6';
  const slate = '#5C6670';
  b.frame(1.0, 4.0, 0, 17.5, () => {
    b.color(stone).prism(CATH_RING, 0, 24, {top: false});
    b.color(slate).cap(CATH_RING, 24);
    // nave roof (estimated ridge 10 m over the eaves) and transept roof
    b.color(slate).gable(-9, 52, 18, 46, 24, 10);
    b.gable(0.5, 2.5, 47, 46, 24, 12, false);
    // twin towers of the façade, 71 m to the parapet, no spires (the 1913 redesign)
    b.color(stone);
    for (const cx of [-15.5, -3.5]) {
      b.box(cx, 69, 0, 8.6, 8.6, 70);
      b.color('#9A958A').box(cx, 69, 70, 9.4, 9.4, 1.0);
      b.color(stone);
    }
    // rose window block between the towers (36 ft = 11 m across, estimated centre height)
    b.color('#8E8A80').box(-9.5, 74.4, 18, 6, 1.2, 12);
  });
}

NJ_INNER.push({
  id: 'newark_cathedral_basilica',
  name: 'Cathedral Basilica of the Sacred Heart',
  kind: 'building',
  built: [1898.0, 1954.8],
  end: 9999,
  anchor: [-74.17841, 40.75501],
  build: buildCathedral,
  replaces: [place(CATH_RING, 1.0, 4.0, 17.5)],
  facts: {
    Built: 'ground broken January 1898, cornerstone June 11, 1899; redesigned in French Gothic 1913; roof complete November 1919; dedicated October 19, 1954',
    Architects: 'Jeremiah O\'Rourke, then Mr. Waldron from 1910 (Wikipedia gives no first name)',
    Note: 'the twin towers were cut from 332 ft (101 m) to 232 ft (71 m) and the spires dropped in the 1913 redesign',
    Model: 'plan from the Overture footprint; towers 71 m cited; wall height 24 m, roof ridges and tower positions estimated; towers sit on the footprint\'s narrow end (facade end assumed, not verified); the footprint is longer (about 150 m) than the cited 111 m'
  },
  sources: [WIKI + 'Cathedral_Basilica_of_the_Sacred_Heart_(Newark)', OVERTURE]
});

// ====================================================================== Newark Penn Station (1935)
// Footprint (Overture, 27,310 m2, "Newark Penn Station"); frame at the vertex mean (-41.0, -26.8),
// +y at 46.5° along the headhouse's long axis. Cited: dedicated March 23, 1935, McKim, Mead &
// White, Classical Revival with Art Deco; no height in the article.
const PENN_RING = P(
  46.0, -6.2, 50.3, 215.9, -20.9, 220.9, -24.8, 170.8, -27.3, 120.1, -49.5, 120.7, -50.6, 28.8, -25.6, 28.5, -21.6, -37.9, -8.4, -133.6, -6.4, -143.3, -3.3, -142.7,
  -3.1, -144.3, 50.4, -137.0, 45.4, -81.6, 49.1, -79.0
);
const PENN_HEAD = P(-50.6, 28.8, -49.5, 120.7, -27.3, 120.1, -24.8, 170.8, -20.9, 220.9, 50.3, 215.9, 46.0, -6.2, 49.1, -79.0, 45.4, -81.6, -25.6, 28.5);

function buildPenn(b: MeshBuilder) {
  const lime = '#D8D2C2';
  b.frame(-41.0, -26.8, 0, 46.5, () => {
    // low track-side building and platform stairs (estimated 9 m)
    b.color('#A9A59B').prism(PENN_RING, 0, 9, {top: false});
    b.color('#8C8F90').cap(PENN_RING, 9);
    // headhouse block (estimated 22 m) with a raised central hall
    b.color(lime).prism(PENN_HEAD, 9, 22, {top: false});
    b.color('#8C8F90').cap(PENN_HEAD, 22);
    b.color('#CFC9B9').box(0, 170, 22, 70, 40, 7);
  });
}

NJ_INNER.push({
  id: 'newark_penn_station',
  name: 'Newark Penn Station',
  kind: 'building',
  built: [1930.0, 1935.2],
  end: 9999,
  anchor: [-74.16433, 40.73423],
  build: buildPenn,
  replaces: [place(PENN_RING, -41.0, -26.8, 46.5)],
  facts: {
    Built: 'dedicated March 23, 1935; first regular train March 24, 1935 (Wikipedia). Start year 1930 is an estimate',
    Architects: 'McKim, Mead & White',
    Note: 'Classical Revival with Art Deco details; the Dock Bridge beside it is a 230 ft three-track lift span',
    Model: 'plan from the Overture footprint; no height is cited in the article: headhouse 22 m, central hall 29 m, track-side building 9 m are estimates (LOW confidence)'
  },
  sources: [WIKI + 'Newark_Penn_Station', OVERTURE]
});

// ====================================================================== National Newark Building (1931)
// Footprint 8 vertices (Overture, named, 3,331 m2). Frame at (2.8, -7.4), +y at 117.1°.
// Cited: 466 ft (142 m) to the roof, 35 storeys, top "inspired by the Mausoleum at Halicarnassus"
// (Wikipedia); the steel pole added in the 2000s (113 ft) is not modelled.
const NATL_RING = P(-14.4, 30.6, -32.1, 30.0, -32.0, -37.5, 25.0, -35.4, 23.5, -15.2, 22.8, -15.1, 21.3, 22.3, -14.1, 20.3);

function buildNational(b: MeshBuilder) {
  b.frame(2.8, -7.4, 0, 117.1, () => {
    b.color('#CDBF9F').prism(NATL_RING, 0, 58, {top: false});
    const s1 = scaled(NATL_RING, 0.88, 0.9);
    b.color('#CDBF9F').cap(NATL_RING, 58);
    b.prism(s1, 58, 100, {top: false});
    b.cap(s1, 100);
    const s2 = scaled(NATL_RING, 0.66, 0.66);
    b.prism(s2, 100, 124, {top: false});
    // colonnaded temple stage and stepped pyramid, top at the cited roof height
    b.color('#B9AB8A');
    const s3 = scaled(NATL_RING, 0.5, 0.5);
    b.prism(s3, 124, 132, {top: false});
    b.cap(s3, 132);
    const s4 = scaled(NATL_RING, 0.34, 0.34);
    b.prism(s4, 132, 137, {top: false});
    b.cap(s4, 137);
    const s5 = scaled(NATL_RING, 0.18, 0.18);
    b.prism(s5, 137, 142);
  });
}

NJ_INNER.push({
  id: 'national_newark_building',
  name: 'National Newark Building',
  kind: 'tower',
  built: [1930.0, 1931.5],
  end: 9999,
  anchor: [-74.17081, 40.73668],
  build: buildNational,
  replaces: [place(NATL_RING, 2.8, -7.4, 117.1)],
  facts: {
    Built: 'construction began 1930; "Newark\'s tallest building since 1931" (Wikipedia, whose infobox says 1933 — the sources disagree)',
    Architects: 'John H. and Wilson C. Ely',
    Note: '35 storeys, tan brick and limestone, 16 elevators; the roof stage is inspired by the Mausoleum at Halicarnassus',
    Model: 'plan from the Overture footprint; roof 142 m (466 ft) cited; set-back heights and sizes (58 / 100 / 124 / 132 / 137 m) are estimates; the antenna pole of the 2000s is not modelled'
  },
  sources: [WIKI + 'National_Newark_Building', OVERTURE]
});

// ====================================================================== Newark City Hall (1902-06)
// Footprint (Overture, named, 3,366 m2); frame at (3.4, -1.4), +y at 14.6°; the main front faces
// Broad Street, the +x side of this frame. Cited: five storeys, gilded dome, Ely and Mowbray &
// Uffinger. Heights and dome are estimates.
const CH_RING = P(
  -30.6, -18.3, -32.9, -31.7, -19.7, -33.9, -19.5, -32.5, -1.9, -35.5, -2.1, -36.8, 11.3, -39.1, 13.5, -26.0, 11.4, -25.7, 13.7, -12.3, 21.7, -13.6, 22.4, -9.7,
  26.2, -10.3, 27.5, -2.9, 28.2, 1.3, 24.4, 1.9, 25.1, 5.9, 17.2, 7.2, 19.3, 19.8, 21.4, 19.5, 23.7, 33.2, 10.2, 35.5, 9.9, 34.0, -8.3, 37.1, -8.0, 38.5, -21.3, 40.7,
  -23.7, 27.2, -21.7, 26.9, -23.7, 15.3, -26.4, 15.7, -30.2, -6.3, -27.6, -6.8, -29.6, -18.4
);

function buildCityHall(b: MeshBuilder) {
  b.frame(3.4, -1.4, 0, 14.6, () => {
    b.color('#D9D4C6').prism(CH_RING, 0, 27, {top: false});
    b.color('#8C9794').cap(CH_RING, 27);
    // attic storey, cornice and the gilded dome over the central court
    b.color('#CFC9B8').box(0, 0, 27, 36, 36, 4);
    b.color('#D9D4C6').cylinder(0, 0, 9, 31, 38, 16);
    b.color('#E0B23A').dome(0, 0, 9.2, 38, 9, 16, 5);
    b.cylinder(0, 0, 1.2, 47, 52, 8);
  });
}

NJ_INNER.push({
  id: 'newark_city_hall',
  name: 'Newark City Hall',
  kind: 'building',
  built: [1902.0, 1906.0],
  end: 9999,
  anchor: [-74.17358, 40.73177],
  build: buildCityHall,
  replaces: [place(CH_RING, 3.4, -1.4, 14.6)],
  facts: {
    Built: 'Wikipedia says only "built in 1902"; the 1906 completion year is the commonly stated date and was not verified here',
    Architects: 'John H. and Wilson C. Ely; Mowbray and Uffinger',
    Note: 'Beaux-Arts, five storeys, carved marble and stained-glass skylights; the dome was gilded in 24-carat gold in 1986',
    Model: 'plan from the Overture footprint; five storeys cited, heights (27 m eaves, 52 m dome top) and dome shape are estimates (LOW confidence)'
  },
  sources: [WIKI + 'Newark_City_Hall', OVERTURE]
});

// ====================================================================== Central Railroad of New Jersey Terminal (1889)
// Footprint (Overture, named, 4,739 m2); frame at (-1.8, -0.5), +y at 8.5°. The L-shaped head
// house of Peabody & Stearns and William H. Peddle (Richardsonian Romanesque), closed 1967 and
// standing in Liberty State Park. The Bush train shed (12 platforms, 20 tracks; no size cited)
// is not modelled. Heights are estimates.
const CRRNJ_RING = P(-5.7, 51.6, -24.0, 51.6, -23.9, -60.6, -5.2, -60.6, -5.2, -28.4, 34.7, -28.7, 34.9, 37.5, -5.8, 37.6);

function buildCrrnj(b: MeshBuilder) {
  b.frame(-1.8, -0.5, 0, 8.5, () => {
    const brick = '#A6755A';
    b.color(brick).prism(CRRNJ_RING, 0, 14, {top: false});
    b.color('#6E6A66').cap(CRRNJ_RING, 14);
    // waiting-room block and its hipped roof
    b.color(brick).box(15, 4.5, 14, 36, 54, 6, {top: false});
    b.color('#5E5A56').hip(15, 4.5, 36, 54, 20, 7);
    // long wing: hipped roof
    b.hip(-14.6, -4.5, 18.8, 112, 14, 5);
  });
}

NJ_INNER.push({
  id: 'crrnj_terminal',
  name: 'Central Railroad of New Jersey Terminal',
  kind: 'building',
  built: [1888.0, 1889.5],
  end: 9999,
  anchor: [-74.03521, 40.70723],
  build: buildCrrnj,
  replaces: [place(CRRNJ_RING, -1.8, -0.5, 8.5)],
  facts: {
    Built: '1889; closed April 30, 1967; the head house and the abandoned Bush-type shed stand in Liberty State Park',
    Architects: 'William H. Peddle; Peabody & Stearns',
    Note: 'Richardsonian Romanesque; the ferry slips were restored, the structure that housed them is gone',
    Model: 'plan from the Overture footprint; the building\'s height is not cited anywhere in the sources read: 14 m wing, 20-27 m central block and the roofs are estimates (LOW confidence); the train shed is not modelled; start year 1888 is an estimate'
  },
  sources: [WIKI + 'Central_Railroad_of_New_Jersey_Terminal', OVERTURE]
});

// ====================================================================== Hoboken Terminal (1907)
// Footprint (Overture, named, 33,929 m2: head house, concourse and the shed); frame at (47.9, 2.5),
// +y at 76.4° (toward the river). The head house is the footprint clipped at y < -150, the
// Hudson Place end; the sheds are the rest. Cited: opened February 25, 1907, Kenneth M. Murchison,
// clock tower 225 ft (69 m) (the original taken down in 1942; a replica built in 2006),
// copper-clad on a rusticated Indiana limestone base, Bush train shed, four storeys.
const HOB_RING = P(
  -44.7, -21.4, -85.1, -197.2, 16.0, -219.9, 50.1, -64.1, 63.5, -66.9, 66.6, -54.7, 53.6, -51.0, 68.0, 10.0, 58.8, 12.2, 61.8, 23.3, 67.1, 21.5, 74.6, 29.1, 53.4, 48.0,
  59.4, 54.1, 21.9, 87.8, -14.5, 116.1, -54.5, 142.1, -69.3, 117.8, -85.2, 88.6, -15.0, 19.3, -20.5, -6.1, -51.5, 0.4, -58.6, -13.9, -56.7, -15.2, -58.7, -18.6,
  -51.3, -22.9, -49.4, -18.4
);
const HOB_HEAD = P(16.0, -219.9, -85.1, -197.2, -74.3, -150.0, 31.3, -150.0);

function buildHoboken(b: MeshBuilder) {
  b.frame(47.9, 2.5, 0, 76.4, () => {
    b.color('#8E9C8F').prism(HOB_RING, 0, 11, {top: false});
    b.color('#76817A').cap(HOB_RING, 11);
    // head house: four storeys, limestone base and copper-clad upper floors
    b.color('#C9C2B0').prism(HOB_HEAD, 0, 7, {top: false});
    b.color('#6FA08C').prism(scaled(HOB_HEAD, 0.98, 0.98), 7, 24, {top: false});
    b.color('#58806F').cap(HOB_HEAD, 24);
    // clock tower over the middle of the Hudson Place front, 225 ft = 68.6 m
    const tx = -34;
    const ty = -196;
    b.color('#6FA08C').box(tx, ty, 24, 11, 11, 24);
    b.color('#E4E0D0').box(tx, ty, 48, 12, 12, 1);
    b.color('#6FA08C').box(tx, ty, 49, 9, 9, 10);
    b.color('#58806F').pyramid(rect(tx, ty, 9.6, 9.6), 59, [tx, ty, 68.6]);
  });
}

NJ_INNER.push({
  id: 'hoboken_terminal',
  name: 'Hoboken Terminal',
  kind: 'building',
  built: [1905.0, 1907.15],
  end: 9999,
  anchor: [-74.0282, 40.73502],
  build: buildHoboken,
  replaces: [place(HOB_RING, 47.9, 2.5, 76.4)],
  facts: {
    Built: 'opened February 25, 1907 by the Delaware, Lackawanna and Western; electrified 1930; National Register 1973. Start year 1905 is an estimate',
    Architects: 'Kenneth M. Murchison (Beaux-Arts); Lincoln Bush designed the train shed',
    Note: 'the 225 ft clock tower was removed in 1942 for its copper; a radio tower stood in its place until a replica was built in 2006 (the model shows the tower throughout, a simplification)',
    Model: 'plan from the Overture footprint; clock tower height 225 ft (69 m) cited; head-house height (24 m), shed height (11 m), the tower\'s plan and position at the middle of the Hudson Place front are estimates (LOW confidence)'
  },
  sources: [WIKI + 'Hoboken_Terminal', OVERTURE]
});

// ====================================================================== 30 Hudson Street (2004)
// Footprint (Overture, parcel-named, 5,660 m2); frame at (14.9, -8.4), +y at 99.2°. Cited:
// 781 ft (238 m) to the roof, 42 floors, 2001-04, Pelli Clarke Pelli with Adamson Associates.
// The Overture height (140 m) is not used. Set-backs are estimates.
const GS_RING = P(-35.2, -64.2, 24.2, -63.7, 23.5, -26.8, 21.7, -26.8, 23.8, -17.3, 24.8, -3.1, 22.2, 20.8, 19.1, 30.2, 11.4, 32.4, -4.4, 33.2, -25.8, 31.7, -33.5, 29.0, -35.5, 19.5, -36.4, 5.1);

function buildGoldman(b: MeshBuilder) {
  b.frame(14.9, -8.4, 0, 99.2, () => {
    b.color('#8DA3AE').prism(GS_RING, 0, 150, {top: false});
    b.cap(GS_RING, 150);
    const s1 = scaled(GS_RING, 0.9, 0.94);
    b.color('#93A9B4').prism(s1, 150, 205, {top: false});
    b.cap(s1, 205);
    const s2 = scaled(GS_RING, 0.78, 0.86);
    b.color('#9CB1BB').prism(s2, 205, 238);
  });
}

NJ_INNER.push({
  id: 'thirty_hudson_street',
  name: '30 Hudson Street (Goldman Sachs Tower)',
  kind: 'tower',
  built: [2001.0, 2004.5],
  end: 9999,
  anchor: [-74.03399, 40.71304],
  build: buildGoldman,
  replaces: [place(GS_RING, 14.9, -8.4, 99.2)],
  facts: {
    Built: 'construction 2001-2004',
    Architects: 'Pelli Clarke Pelli; Adamson Associates (architect of record)',
    Note: '42 floors, 1.6 million sq ft, 36 elevators; tallest building in New Jersey',
    Model: 'plan from the Overture footprint; roof 238 m (781 ft) cited; the two set-backs (at 150 m and 205 m) are estimates; the Overture height of 140 m is wrong and was not used'
  },
  sources: [WIKI + '30_Hudson_Street', OVERTURE]
});

// ====================================================================== Loew's Jersey Theatre (1929)
// Footprint (Overture, named, 2,344 m2); frame at (-1.2, 8.5), +y at 135.9°. Cited: opened
// September 28, 1929, Rapp and Rapp, Baroque Revival. No building dimension is cited; the 27.7 m
// height is the footprint data's own value (unverified).
const LOEWS_RING = P(-8.2, -28.4, 14.9, -34.7, 26.0, 1.4, 25.4, 10.4, 3.7, 51.4, -12.1, 47.6, -9.6, 26.5, -10.7, -9.2, -12.0, -18.8, -8.2, -19.2, -9.2, -27.0);

function buildLoews(b: MeshBuilder) {
  b.frame(-1.2, 8.5, 0, 135.9, () => {
    b.color('#D8CFB8').prism(LOEWS_RING, 0, 18, {top: false});
    b.color('#8A8279').cap(LOEWS_RING, 18);
    // fly tower over the stage end (estimated), auditorium roof
    b.color('#CFC6AE').box(8, -12, 18, 26, 30, 9.7);
  });
}

NJ_INNER.push({
  id: 'loews_jersey_theatre',
  name: "Loew's Jersey Theatre",
  kind: 'building',
  built: [1928.0, 1929.75],
  end: 9999,
  anchor: [-74.06456, 40.73233],
  build: buildLoews,
  replaces: [place(LOEWS_RING, -1.2, 8.5, 135.9)],
  facts: {
    Built: 'opened September 28, 1929 on Journal Square',
    Architects: 'Rapp and Rapp (Baroque Revival, "Italian rococo" exterior)',
    Note: 'about 3,021-3,600 seats on two levels; stage 33 by 72 ft; the vertical sign was removed in the 1960s',
    Model: 'plan from the Overture footprint; no height is cited: 27.7 m is the footprint dataset\'s value, split here into an 18 m house and a 9.7 m fly tower (estimates, LOW confidence); start year 1928 is an estimate'
  },
  sources: [WIKI + "Loew%27s_Jersey_Theatre", OVERTURE]
});

// ====================================================================== Stadiums of the Meadowlands
// MetLife Stadium: the Overture outline (44,965 m2, a ring with the pitch as its hole), frame at
// (0.4, 0.2), +y at 171.2° = the long axis (about 280 x 230 m). Giants Stadium stood about 215 m
// south-west (Wikipedia 40°48'44"N 74°4'37"W, DMS to the second, so +-30 m) and is gone, so its
// outline comes from the cited size (756 x 592 ft = 230 x 180 m) with the same orientation.
const MET_RING = P(
  27.5, 137.0, -7.2, 139.7, -35.9, 135.3, -51.1, 130.4, -80.4, 114.9, -105.8, 93.6, -113.5, 49.6, -115.1, 22.6, -114.4, -7.9, -107.8, -51.4, -97.9, -85.9, -89.5, -105.8,
  -74.7, -118.0, -44.5, -133.5, -5.4, -140.5, 27.3, -138.8, 57.0, -128.5, 74.8, -119.1, 105.5, -95.7, 113.7, -47.5, 115.1, -3.3, 111.8, 30.3, 99.6, 82.4, 92.4, 103.6,
  81.1, 114.9, 64.2, 124.8
);

/** A bowl: outer wall to `rim`, a raked seating ribbon down to the field, the field itself. */
function bowl(b: MeshBuilder, outer: V2[], rim: number, inner: V2[], low: number, colors: {wall: string; seats: string; field: string}) {
  b.color(colors.wall).prism(outer, 0, rim, {top: false});
  b.color(colors.seats);
  const n = outer.length;
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    b.quad([outer[i][0], outer[i][1], rim], [outer[j][0], outer[j][1], rim], [inner[j][0], inner[j][1], low], [inner[i][0], inner[i][1], low]);
  }
  b.color(colors.field).cap(inner, low);
}

function buildMetLife(b: MeshBuilder) {
  b.frame(0.4, 0.2, 0, 171.2, () => {
    bowl(b, MET_RING, 46, scaled(MET_RING, 0.62, 0.66), 4, {wall: '#9AA0A6', seats: '#5F6F86', field: '#3F7D3A'});
    // solar ring of the upper rim, the entrance pylons (54 ft = 16.5 m)
    b.color('#2E3A4A').prism(scaled(MET_RING, 0.995), 46, 48, {top: false});
    b.color('#C9CCD0');
    for (const [x, y] of [[-92, 112], [92, 112], [-92, -112], [92, -112]] as V2[]) b.box(x, y, 0, 9, 9, 16.5);
  });
}

NJ_INNER.push({
  id: 'metlife_stadium',
  name: 'MetLife Stadium',
  kind: 'stadium',
  built: [2007.7, 2010.3],
  end: 9999,
  anchor: [-74.07435, 40.81352],
  build: buildMetLife,
  replaces: [place(MET_RING, 0.4, 0.2, 171.2)],
  facts: {
    Built: 'groundbreaking September 5, 2007; opened April 10, 2010',
    Architects: '360 Architecture, EwingCole, Rockwell Group, Bruce Mau Design',
    Note: '82,500 seats, open air; replaced Giants Stadium beside it',
    Model: 'outline from the Overture footprint; no roof or rim height is cited (the article says the stadium has no roof): rim 46 m, the seating rake and the field level are estimates (LOW confidence); pylons 54 ft cited'
  },
  sources: [WIKI + 'MetLife_Stadium', OVERTURE]
});

const GIANTS_RING = roundedRect(0, 0, 180, 230, 55, 6);

function buildGiants(b: MeshBuilder) {
  b.frame(0, 0, 0, 171.2, () => {
    bowl(b, GIANTS_RING, 44, scaled(GIANTS_RING, 0.6, 0.64), 4, {wall: '#8E8B86', seats: '#3F5C8C', field: '#3F7D3A'});
    // the south ramp tower, the stadium's highest point (54 m, cited)
    b.color('#8E8B86').box(0, -122, 0, 16, 14, 54);
    b.color('#B7B4AE').box(0, 118, 40, 30, 8, 6);
  });
}

NJ_INNER.push({
  id: 'giants_stadium',
  name: 'Giants Stadium',
  kind: 'stadium',
  built: [1972.9, 1976.8],
  end: 2010.6,
  anchor: [-74.07694, 40.81222],
  build: buildGiants,
  replaces: [place(GIANTS_RING, 0, 0, 171.2)],
  facts: {
    Built: 'ground broken November 19, 1972; opened October 10, 1976; last game January 3, 2010; demolished February 4 to August 10, 2010',
    Architects: 'Kivett and Myers; Ewing Cole Erdman & Eubank; Clauss & Nolan',
    Note: '80,242 seats; the Giants, Jets and Cosmos played here; Wikipedia gives the field axis as northwest to southeast with the press box on the south-west sideline',
    Model: 'size 230 x 180 m and heights 44 m (bowl) and 54 m (south tower) cited; position from Wikipedia\'s coordinates (+-30 m), orientation assumed parallel to MetLife Stadium (+-20 deg), rounded-rectangle outline, rake and tower position estimated (LOW confidence)'
  },
  sources: [WIKI + 'Giants_Stadium']
});

// ====================================================================== Union County Courthouse, Elizabeth
// Footprint (Overture, named, 4,019 m2); frame at (6.1, -1.1), +y at 94.5°. Cited: built 1925-31,
// Oakley and Son, Neoclassical, 17-storey tower 238 ft (72.54 m), a 3-storey portion, annexes of
// 1927, 1932 and 1964. Which wing carries the tower is not in the sources: it is placed on the
// cross-shaped plan's central block (estimated).
const UC_RING = P(
  5.5, 6.8, 5.5, 10.8, 18.0, 10.8, 18.0, 37.7, 5.7, 37.7, 5.7, 49.5, -11.9, 49.5, -11.9, 37.9, -24.0, 37.9, -24.0, 10.9, -12.1, 10.9, -12.1, 7.2, -20.6, 7.2,
  -20.6, -21.8, -5.0, -21.8, -5.0, -12.3, -0.4, -12.3, -0.4, -29.2, -30.8, -29.2, -30.8, -51.2, 14.5, -51.3, 14.5, -40.2, 31.3, -40.2, 31.3, -11.6, 18.1, -11.6,
  18.1, 5.4, 11.6, 5.4, 11.6, 6.8
);

function buildUnion(b: MeshBuilder) {
  b.frame(6.1, -1.1, 0, 94.5, () => {
    b.color('#D6D0C0').prism(UC_RING, 0, 15, {top: false});
    b.color('#8C8F90').cap(UC_RING, 15);
    // tower: 17 storeys to the cited 72.54 m, set back twice
    b.color('#D6D0C0').box(-3, 24, 15, 24, 20, 33);
    b.box(-3, 24, 48, 18, 15, 17);
    b.color('#CFC8B5').box(-3, 24, 65, 12, 10, 7.54);
  });
}

NJ_INNER.push({
  id: 'union_county_courthouse',
  name: 'Union County Courthouse',
  kind: 'building',
  built: [1925.0, 1931.0],
  end: 9999,
  anchor: [-74.2161, 40.66218],
  build: buildUnion,
  replaces: [place(UC_RING, 6.1, -1.1, 94.5)],
  facts: {
    Built: 'construction 1925-1931, cost $1.2 million; annexes 1927, 1932 and 1964',
    Architects: 'Oakley and Son (Neoclassical)',
    Note: '17-storey tower, 238 ft; three elevators',
    Model: 'plan from the Overture footprint; tower top 72.54 m (238 ft) cited; the 15 m base height, the tower\'s position on the plan and its set-backs are estimates (LOW confidence)'
  },
  sources: [WIKI + 'Union_County_Courthouse_(New_Jersey)', OVERTURE]
});
