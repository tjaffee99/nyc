/**
 * West Point and Poughkeepsie: the towns round of 2026-11-11 (the owner: "there are no landmarks").
 * Research, sources, ids of the footprints and numeric checks: data/research/towns_ny.md.
 *
 * Conventions as new-haven.ts: the anchor is the lon/lat of the footprint a model replaces
 * (data/interim/counties/ny_orange.parquet / ny_dutchess.parquet, Overture Maps 2026-10-21.0,
 * ODbL-compatible), rounded to 6 decimals; plans are that footprint in anchor-local metres (x east,
 * y north), simplified to 0.25 m. The walls always stand on the real ring; roofs and towers are
 * estimates unless a `Model:` fact says a figure is cited. Footprint heights (`height_m`, Overture)
 * serve as the check where no height is published.
 */
import {MeshBuilder, circle, rect, type V2} from './kit';
import type {Landmark} from './types';

const WIKI = 'https://en.wikipedia.org/wiki/';
const OVT = 'https://docs.overturemaps.org/guides/buildings/';
const GROUNDS = WIKI + 'United_States_Military_Academy_grounds_and_facilities';

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
    return [cx + along * ky * ux + across * kx * uy, cy + along * ky * uy - across * kx * ux] as V2;
  });
}

/** Ridge roof over any ring: the ring shrinks across its long axis (bearing) to a ridge. */
function ridge(b: MeshBuilder, ring: V2[], bearing: number, z0: number, rise: number, across = 0.2, along = 0.96) {
  b.loft([ring, scale(ring, across, along, bearing)], [z0, z0 + rise]);
}

/** Hipped roof over any ring (uniform shrink). */
function hipOver(b: MeshBuilder, ring: V2[], z0: number, rise: number, k = 0.55) {
  b.loft([ring, scale(ring, k)], [z0, z0 + rise]);
}

/** Square pinnacle: a pyramid on a small square. */
function pinnacle(b: MeshBuilder, x: number, y: number, s: number, z0: number, z1: number) {
  b.pyramid(rect(x, y, s, s), z0, [x, y, z1]);
}

export const NY_TOWNS: Landmark[] = [];

// ====================================================================== WEST POINT

// ---------------------------------------------------------------- Taylor Hall (1910)
// Cited (grounds and facilities article): the Administration Building, Cram, Goodhue & Ferguson, 1910, "With its
// 180 ft tower, it is the tallest all-stone masonry building in the world". Footprint 01f229a7 (Overture, h 13.7 m).
const R_taylor: V2[] = P(2.4, -30.2, 15.9, -30.5, 16.1, -22.8, 23.0, -22.9, 23.4, -5.1, 18.7, -4.8, 19.8, 21.4, -15.6, 22.3, -16.0, 4.7, -18.9, 4.7, -19.0, -7.3, -15.8, -7.6, -16.0, -24.4, 2.3, -25.1);
function buildTaylor(b: MeshBuilder) {
  const stone = '#8D8B85';
  b.color(stone).prism(R_taylor, 0, 10.7);
  b.color('#4E5258');
  ridge(b, R_taylor, 1, 10.7, 3.0, 0.3, 0.96);
  // the tower at the hub of the plan (position estimated)
  b.color(stone).box(1.0, -1.2, 10.7, 9.6, 9.6, 23.5);
  b.color('#7E7C76').box(1.0, -1.2, 34.2, 8.2, 8.2, 12.8);
  b.color('#6F6D68').box(1.0, -1.2, 47.0, 9.4, 9.4, 2.4);
  for (const [dx, dy] of [[-3.7, -3.7], [3.7, -3.7], [3.7, 3.7], [-3.7, 3.7]]) {
    b.color(stone).box(1.0 + dx, -1.2 + dy, 49.4, 1.6, 1.6, 2.2);
    b.color('#5E5C58');
    pinnacle(b, 1.0 + dx, -1.2 + dy, 1.6, 51.6, 54.86);
  }
}
NY_TOWNS.push({
  id: 'taylor_hall_west_point',
  name: 'Taylor Hall (Administration Building), West Point',
  kind: 'tower',
  built: [1908, 1910],
  end: 9999,
  anchor: [-73.955902, 41.390024],
  build: buildTaylor,
  replaces: [R_taylor],
  facts: {
    Built: 'completed 1910 by Cram, Goodhue & Ferguson as the Administration Building (named for Maxwell Taylor later); collegiate Gothic granite; it replaced the headquarters of 1870',
    Height: 'tower 180 ft (54.9 m), "the tallest all-stone masonry building in the world"',
    Model: 'plan from the footprint (1,814 m2); tower top cited (54.86 m = 180 ft); the tower\'s position on the plan, its stages, the corner turrets and the eave height (10.7 m; footprint roof 13.7 m) are estimated; start of work (1908) estimated: LOW for the tower\'s position'
  },
  sources: [GROUNDS, OVT]
});

// ---------------------------------------------------------------- Thayer Hall (the riding hall, 1909-11)
// Cited: grounds article: Cram, Goodhue & Ferguson's riding hall, "completed along the cliffs of the Hudson in 1909"
// (the hall list says 1911), "The massive riding hall rises from the cliffs along the river to the level of the Plain";
// converted to an academic hall in 1958. Footprint bc16b66a (Overture, no height).
const R_thayer: V2[] = P(70.7, 98.6, 27.5, 114.2, 2.4, 46.0, -3.3, 48.1, -8.9, 32.9, -12.0, 34.0, -22.4, 5.7, -31.3, 8.9, -36.6, -5.6, -29.0, -8.4, -31.7, -15.7, -35.8, -14.2, -42.4, -32.2, -28.7, -37.2, -32.0, -46.1, -36.3, -44.5, -39.0, -51.7, -24.6, -57.0, -24.0, -55.4, -3.3, -62.9, -6.0, -70.3, 2.0, -73.2, 0.2, -78.1, -22.0, -70.1, -32.2, -97.7, -9.5, -105.9, -13.5, -116.7, 9.1, -124.9, 11.6, -118.1, 6.7, -116.3, 20.1, -79.7, 7.0, -74.9);
NY_TOWNS.push({
  id: 'thayer_hall_west_point',
  name: 'Thayer Hall (the riding hall), West Point',
  kind: 'building',
  built: [1907.5, 1911],
  end: 9999,
  anchor: [-73.954766, 41.390318],
  build: b => {
    b.color('#8A8883').prism(R_thayer, 0, 16);
    b.color('#4F5A5E');
    ridge(b, R_thayer, 15.3, 16, 6.5, 0.28, 0.97);
    // the cliff-side buttress piers along the long face
    b.color('#777570');
    for (let i = 0; i < 8; i++) b.box(-34 + (i % 2) * 2, -100 + i * 26, 0, 3, 3, 19);
  },
  replaces: [R_thayer],
  facts: {
    Built: 'riding hall completed 1909-11 by Cram, Goodhue & Ferguson on the cliffs above the Hudson; the largest equestrian hall of its time was on this site from 1855; converted in 1958 into the academic hall named for Sylvanus Thayer',
    Model: 'plan from the footprint (10,975 m2, 235 x 76 m); no height is published: wall 16 m and roof ridge 22.5 m, the buttress piers and the colours are estimated; start of work (1907.5) estimated: LOW'
  },
  sources: [GROUNDS, OVT]
});

// ---------------------------------------------------------------- Pershing Barracks (West Academic Building, 1891-95)
// Cited: grounds article: the West Academic Building, Richard Morris Hunt, "took four years to complete", 1895 (the barracks
// list: built 1895), a barracks and renamed Pershing in 1950/59. Footprint 6ed3648d (Overture h 14.7 m).
const R_pershing: V2[] = P(-18.8, 54.7, -27.3, 54.9, -27.4, 48.9, -24.9, 48.9, -25.2, 34.8, -8.3, 34.5, -9.2, -11.6, -25.0, -11.4, -25.4, -32.9, 8.3, -33.5, 9.8, 46.2, 13.1, 46.1, 13.3, 54.6, 5.1, 54.8, 5.0, 51.2, -18.9, 51.7);
NY_TOWNS.push({
  id: 'pershing_barracks_west_point',
  name: 'Pershing Barracks (West Academic Building), West Point',
  kind: 'building',
  built: [1891, 1895],
  end: 9999,
  anchor: [-73.956557, 41.390648],
  build: b => {
    b.color('#8E8B84').prism(R_pershing, 0, 11.2);
    b.color('#8A877F').prism(scale(R_pershing, 0.995, 0.995), 11.2, 11.9);
    b.color('#4A4F55');
    ridge(b, R_pershing, 1, 11.9, 2.8, 0.3, 0.96);
  },
  replaces: [R_pershing],
  facts: {
    Built: 'built 1891-95 as the West Academic Building (Richard Morris Hunt) on the site of the academic building of 1839; the main academic hall until 1950, then a barracks named for General Pershing',
    Height: '14.7 m (the footprint record, Overture)',
    Model: 'plan from the footprint (2,220 m2); top 14.7 m is the footprint\'s height, the wall/roof split and the colours are estimated; no towers or turrets are modelled'
  },
  sources: [GROUNDS, OVT]
});

// ---------------------------------------------------------------- Cullum Hall (1894-98)
// Cited: grounds article: McKim, Mead & White, begun 1894, "Completed in 1898", classical design in white marble.
// Footprint 9961f828 (Overture h 12.9 m): a rectangle 21.3 x 46 m on a long axis of 35.6 degrees.
const R_cullum: V2[] = P(22.0, 12.5, 4.7, 24.8, -22.1, -12.5, -4.7, -24.8);
NY_TOWNS.push({
  id: 'cullum_hall_west_point',
  name: 'Cullum Hall, West Point',
  kind: 'building',
  built: [1894, 1898],
  end: 9999,
  anchor: [-73.953883, 41.392113],
  build: b => {
    b.color('#CFCABD').prism(R_cullum, 0, 1.3);
    b.frame(0, 0, 0, 35.6, () => {
      b.color('#E6E2D8').box(0, 0, 1.3, 21.3, 46, 8.2);
      b.color('#D8D3C6').box(0, 0, 9.5, 22.0, 46.8, 0.6);
      b.color('#5E6A66').hip(0, 0, 21.3, 46, 10.1, 2.78);
      // the order of the river front: six columns and a pediment (estimated)
      b.color('#F0ECE2');
      for (let i = 0; i < 6; i++) b.cylinder(9.3, -7.5 + i * 3, 0.5, 1.3, 9.5, 8);
      b.color('#E6E2D8').gable(9.6, 0, 3.0, 17, 9.5, 2.2, true);
    });
  },
  replaces: [R_cullum],
  facts: {
    Built: 'begun 1894, completed 1898 (McKim, Mead & White; the gift of George W. Cullum); neoclassical white marble among the grey granite of the Plain',
    Height: '12.9 m (the footprint record, Overture)',
    Model: 'plan from the footprint (976 m2); top 12.9 m is the footprint\'s height; the podium, the eave, the six-column front and its side are estimated; start of work (1894) cited'
  },
  sources: [GROUNDS, OVT]
});

// ---------------------------------------------------------------- The Thayer Hotel (1925-26)
// Cited (Thayer Hotel article): Caughey and Evans of New York, Gothic Revival granite, 5 floors (main building) and 3
// (the executive wing of 2012), construction 1925, opened 27 May 1926. Footprint 6c36759d (no height).
const R_hotel: V2[] = P(34.8, 35.6, 25.2, 54.6, 18.3, 51.2, 20.0, 47.9, -12.8, 31.6, -10.2, 26.4, -14.1, 14.9, -19.1, 16.5, -22.0, 7.7, -17.2, 6.1, -21.3, -6.2, -24.7, -7.9, -21.2, -14.7, -25.0, -16.7, -26.6, -13.7, -68.4, -35.1, -62.2, -47.0, -22.6, -26.8, -24.1, -23.9, -17.3, -20.4, -8.6, -37.4, -13.2, -39.8, -10.9, -44.3, -9.4, -43.6, -6.7, -48.7, 17.3, -36.5, 6.6, -15.8, 16.2, -10.8, 22.3, 11.3, 18.3, 19.4, 33.9, 27.2, 30.7, 33.5);
NY_TOWNS.push({
  id: 'thayer_hotel_west_point',
  name: 'The Thayer Hotel, West Point',
  kind: 'building',
  built: [1925, 1926.4],
  end: 9999,
  anchor: [-73.961155, 41.377141],
  build: b => {
    b.color('#8F8C86').prism(R_hotel, 0, 18.5);
    b.color('#7C7973').prism(scale(R_hotel, 0.99, 0.99), 18.5, 19.4);
    b.color('#4B5258');
    hipOver(b, R_hotel, 19.4, 4.0, 0.62);
  },
  replaces: [R_hotel],
  facts: {
    Built: 'built 1925-26 (opened 27 May 1926, Caughey and Evans) to replace the West Point Hotel of 1829 on Trophy Point; Gothic Revival granite',
    Height: 'five floors in the main building (executive wing: three)',
    Model: 'plan from the footprint (3,723 m2, main building and wing); floor height (3.7 m, 18.5 m wall), the roof (4 m) and the colours are estimated; no tower or entrance is modelled; start of work (1925) cited: LOW'
  },
  sources: [WIKI + 'Thayer_Hotel', OVT]
});

// ---------------------------------------------------------------- Battle Monument, Trophy Point (1897)
// Cited (Battle Monument article): designed by Stanford White, unveiled 30 May 1897; the granite column stands 46 ft
// (14.0 m) tall and 5 ft (1.5 m) in diameter, quarried at Branford, Connecticut; eight "cannon balls" belted with bronze
// straps; Fame by Frederick MacMonnies on top. Coordinate 41 23 40.93 N 73 57 24.66 W.
NY_TOWNS.push({
  id: 'battle_monument_west_point',
  name: 'Battle Monument, Trophy Point, West Point',
  kind: 'monument',
  built: [1895, 1897.41],
  end: 9999,
  anchor: [-73.95685, 41.394703],
  build: b => {
    const base = 3.4;
    b.color('#9C9890').frustum(0, 0, 4.2, 3.2, 0, 1.6, 8).frustum(0, 0, 3.2, 2.6, 1.6, base, 8);
    b.color('#A6A39B').cylinder(0, 0, 0.8, base, base + 14.02, 16);
    b.color('#8A8780').frustum(0, 0, 1.0, 1.35, base + 14.02, base + 14.9, 12);
    // the eight cannon balls at the foot of the shaft (estimated height and radius)
    b.color('#6D6B66');
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * Math.PI * 2;
      b.cylinder(Math.cos(a) * 2.0, Math.sin(a) * 2.0, 0.6, base, base + 1.2, 6);
    }
    // Fame (estimated)
    b.color('#6B5B3E').box(0, 0, base + 14.9, 1.4, 1.0, 3.9);
  },
  facts: {
    Built: 'site dedicated 15 June 1864 by General McClellan; the monument unveiled 30 May 1897 (Stanford White; Fame by Frederick MacMonnies), paid for by the Regular Army\'s officers and soldiers; 2,230 names of the Civil War dead on the bronze straps',
    Height: 'the granite column 46 ft (14.0 m) high and 5 ft (1.5 m) across, "the largest column of polished granite in the Western Hemisphere"',
    Model: 'shaft length (14.02 m) and diameter (1.52 m) cited; the plinth (3.4 m), the capital, the eight balls and Fame (3.9 m) are estimated, so the overall top (22 m) is an estimate; the position is the article\'s coordinate; start of work (1895) estimated'
  },
  sources: [WIKI + 'Battle_Monument_(West_Point)']
});

// ---------------------------------------------------------------- Old Cadet Chapel (the building moved to the cemetery, 1910)
// Cited: Old Cadet Chapel article: built 1836 in the cadet area, Greek Revival, "disassembled brick-by-brick and moved to
// the West Point Cemetery when the current Cadet Chapel opened in 1910"; infobox "dedicated 1910 (in current location)".
// Footprint 01bd39d8 (Overture h 8.0 m): 29.6 x 15.5 m, long axis 160 degrees.
const R_ocadet: V2[] = P(0.3, 15.9, -8.2, 12.9, -6.7, 8.8, -10.9, 7.3, -3.6, -12.7, -1.2, -11.9, 0.2, -15.6, 10.0, -12.0, 8.6, -8.1, 10.9, -7.3, 3.9, 12.1, 2.0, 11.4);
NY_TOWNS.push({
  id: 'old_cadet_chapel_west_point',
  name: 'Old Cadet Chapel, West Point Cemetery',
  kind: 'building',
  built: [1910, 1910.9],
  end: 9999,
  anchor: [-73.967065, 41.397932],
  build: b => {
    b.color('#B8B2A4').prism(R_ocadet, 0, 5.8);
    b.frame(0, 0, 0, 160, () => {
      b.color('#5A5550').gable(0, 0, 11.4, 21.0, 5.8, 2.2, true);
      // portico at the south-west end (the end the footprint steps in; estimated)
      b.color('#EFEBE0');
      for (const x of [-3.9, -1.3, 1.3, 3.9]) b.cylinder(x, -13.2, 0.38, 0, 5.8, 8);
      b.color('#E6E2D8').gable(0, -13.2, 10.6, 3.0, 5.8, 2.2, true);
    });
  },
  replaces: [R_ocadet],
  facts: {
    Built: 'built 1836 in the cadet area (near today\'s Bartlett Hall), Greek Revival; taken down and rebuilt in the cemetery in 1910-11 when the Cadet Chapel opened',
    Height: '8.0 m (the footprint record, Overture)',
    Model: 'plan from the footprint (409 m2); top 8.0 m is the footprint\'s height; the wall/roof split, the portico and which end it stands on, and the colours are estimated; the model starts at the move (1910): the chapel of 1836 stood elsewhere and is not modelled'
  },
  sources: [WIKI + 'Old_Cadet_Chapel_(West_Point)', GROUNDS, OVT]
});

// ====================================================================== POUGHKEEPSIE

// ---------------------------------------------------------------- Vassar Chapel (1904)
// Cited: Vassar Chapel article: "built in 1904", Norman style, 'seamed' Cape Ann granite with sandstone trimmings, the
// largest religious edifice in Poughkeepsie. Footprint 6f97eb26 (Overture h 11.9 m).
const R_vchapel: V2[] = P(14.8, -16.0, 11.2, 26.8, -27.6, 24.1, -26.6, 16.0, -14.1, 17.6, -12.8, -20.6, -5.6, -19.3, -2.9, -23.5, 1.3, -23.5, 5.9, -21.9, 6.9, -16.7);
NY_TOWNS.push({
  id: 'vassar_chapel',
  name: 'Vassar Chapel',
  kind: 'building',
  built: [1902.5, 1904.5],
  end: 9999,
  anchor: [-73.896964, 41.685458],
  build: b => {
    b.color('#8F8E8A').prism(R_vchapel, 0, 8.4);
    b.color('#B39A78').prism(scale(R_vchapel, 0.99, 0.99), 8.4, 8.9);
    b.color('#4F5256');
    ridge(b, R_vchapel, 175.2, 8.9, 3.0, 0.35, 0.95);
  },
  replaces: [R_vchapel],
  facts: {
    Built: 'built 1904, Norman style in seamed Cape Ann granite with sandstone trim; the largest religious building in Poughkeepsie',
    Height: '11.9 m (the footprint record, Overture)',
    Model: 'plan from the footprint (1,333 m2); top 11.9 m is the footprint\'s height; the wall/roof split, the colours and the single ridge over an L-shaped plan are estimated; no tower or apse is modelled; start of work (1902.5) estimated: LOW'
  },
  sources: [WIKI + 'Vassar_Chapel', OVT]
});

// ---------------------------------------------------------------- Thompson Memorial Library (1905)
// Cited: Thompson Memorial Library article: completed 1905 (Francis R. Allen and Charles Collens), Perpendicular Gothic,
// Germantown stone with Indiana limestone trim, "three wings built about a central tower ... crowned with battlements and
// pinnacles"; additions 1918, 1937 (Van Ingen), 2001 (Ingram). Footprint b63d7c9b (Overture h 8.9 m) holds the additions.
const R_thompson: V2[] = P(-9.3, 79.0, -47.1, 74.3, -42.6, 39.1, -28.6, 40.9, -17.6, -45.3, -20.5, -45.7, -19.1, -56.9, -12.5, -56.1, -9.1, -82.9, 7.8, -80.8, 4.5, -55.4, 9.8, -54.7, 7.2, -33.9, 20.5, -32.2, 17.1, -5.2, 24.0, -4.3, 21.9, 11.9, 14.3, 10.9, 11.6, 32.3, -3.1, 30.4);
NY_TOWNS.push({
  id: 'thompson_library_vassar',
  name: 'Thompson Memorial Library, Vassar College',
  kind: 'building',
  built: [1903.5, 1905.5],
  end: 9999,
  anchor: [-73.897778, 41.687295],
  build: b => {
    const stone = '#7E7A72';
    b.color(stone).prism(R_thompson, 0, 6.4);
    b.color('#58595C');
    ridge(b, R_thompson, 166.2, 6.4, 2.5, 0.3, 0.97);
    // the central tower (position at the hub of the plan, height estimated)
    b.color(stone).box(-2.7, -0.7, 6.4, 10.2, 10.2, 18.0);
    b.color('#8C887F').box(-2.7, -0.7, 24.4, 8.6, 8.6, 8.0);
    b.color('#6E6A63').box(-2.7, -0.7, 32.4, 9.8, 9.8, 1.4);
    for (const [dx, dy] of [[-4.2, -4.2], [4.2, -4.2], [4.2, 4.2], [-4.2, 4.2]]) {
      b.color(stone).box(-2.7 + dx, -0.7 + dy, 33.8, 1.3, 1.3, 1.4);
      b.color('#5E5B55');
      pinnacle(b, -2.7 + dx, -0.7 + dy, 1.3, 35.2, 37.2);
    }
  },
  replaces: [R_thompson],
  facts: {
    Built: 'completed 1905 as a memorial to Frederick Ferris Thompson (Allen and Collens); Perpendicular Gothic; enlarged 1918, 1937 and 2001',
    Height: 'wings 8.9 m (the footprint record, Overture); no tower height is published',
    Model: 'plan from the footprint (5,358 m2, with the later additions); wing height is the footprint\'s; the tower (37 m), its stages and pinnacles, its position at the hub of the plan and the colours are estimated: LOW; start of work (1903.5) estimated'
  },
  sources: [WIKI + 'Thompson_Memorial_Library', OVT]
});

// ---------------------------------------------------------------- Rockefeller Hall (1897)
// Cited: Vassar College article: "Rockefeller Hall, built in 1897"; Wikidata Q131149493 inception 19 Nov 1897. Footprint
// 16301305 (Overture h 10.8 m): 46 x 28 m, long axis 84 degrees.
const R_rock: V2[] = P(24.1, -8.3, 21.7, 15.3, 12.7, 14.4, 12.9, 11.8, 6.6, 11.1, 3.8, 15.2, 0.3, 16.1, -3.8, 15.8, -7.9, 13.2, -9.3, 9.6, -13.9, 9.1, -14.1, 11.3, -24.4, 10.3, -21.9, -14.2, -12.4, -13.3, -12.9, -8.3, 14.8, -5.6, 15.1, -9.2);
NY_TOWNS.push({
  id: 'rockefeller_hall_vassar',
  name: 'Rockefeller Hall, Vassar College',
  kind: 'building',
  built: [1895.5, 1897.9],
  end: 9999,
  anchor: [-73.896821, 41.687836],
  build: b => {
    b.color('#8E8A80').prism(R_rock, 0, 8.3);
    b.color('#56575B');
    ridge(b, R_rock, 84.3, 8.3, 2.5, 0.3, 0.95);
  },
  replaces: [R_rock],
  facts: {
    Built: 'built 1897 (Wikidata: 19 November 1897), a gift of John D. Rockefeller; it houses the college\'s classrooms and offices',
    Height: '10.8 m (the footprint record, Overture)',
    Model: 'plan from the footprint (1,003 m2); top 10.8 m is the footprint\'s height; the wall/roof split and colours are estimated; no towers or gables are modelled; start of work (1895.5) estimated: LOW'
  },
  sources: [WIKI + 'Vassar_College', OVT]
});

// ---------------------------------------------------------------- The quadrangle dormitories (Raymond 1897, Lathrop 1901, Davison 1902)
// Cited: each article gives "five floors" / "five stories" (Raymond 'five floors', Lathrop 'five stories tall', Davison
// 'five-story'), the year of completion and Allen & Collens / Allen & Vance; Elizabethan style (Vassar College article).
const R_raymond: V2[] = P(-2.2, -41.8, 10.9, -40.5, 5.0, 15.9, 12.1, 16.6, 11.8, 19.7, 16.0, 20.2, 15.0, 29.9, -12.5, 27.1, -11.3, 16.3, -8.5, 16.6);
const R_lathrop: V2[] = P(-7.4, -28.1, -12.7, -28.8, -11.5, -37.3, 11.6, -34.2, 2.5, 32.8, -11.2, 31.0, -3.5, -24.9, -7.8, -25.4);
const R_davison: V2[] = P(-4.5, -28.5, 25.2, -24.3, 23.8, -14.5, 18.7, -15.2, 18.4, -13.2, 10.6, -14.3, 4.0, 32.4, 6.8, 32.8, 4.9, 45.7, -14.6, 42.9);
function dorm(ring: V2[], bearing: number) {
  return (b: MeshBuilder) => {
    b.color('#9A5B45').prism(ring, 0, 17.0);
    b.color('#D8D0BE').prism(scale(ring, 1.01, 1.0, bearing), 17.0, 17.5);
    b.color('#4A4E54');
    ridge(b, ring, bearing, 17.5, 3.0, 0.25, 0.95);
  };
}
const DORM_MODEL =
  'plan from the footprint; five floors cited, so the eave (17 m = 5 x 3.4 m), the roof (3 m) and the brick colour are estimated; no gables or chimneys: LOW';
NY_TOWNS.push(
  {
    id: 'raymond_house_vassar',
    name: 'Raymond House, Vassar College',
    kind: 'building',
    built: [1895.5, 1897.3],
    end: 9999,
    anchor: [-73.897577, 41.688535],
    build: dorm(R_raymond, 174.1),
    replaces: [R_raymond],
    facts: {
      Built: 'completed 1897 (Francis R. Allen), the second quadrangle dormitory, named for the college\'s second president; paid for by the college',
      Height: 'five floors',
      Model: DORM_MODEL + '; plan 1,086 m2; start of work estimated'
    },
    sources: [WIKI + 'Raymond_House_(Vassar_College)', OVT]
  },
  {
    id: 'lathrop_house_vassar',
    name: 'Lathrop House, Vassar College',
    kind: 'building',
    built: [1899.5, 1901.3],
    end: 9999,
    anchor: [-73.896441, 41.689444],
    build: dorm(R_lathrop, 172.3),
    replaces: [R_lathrop],
    facts: {
      Built: 'constructed 1901 (Allen & Vance of Boston), the third quadrangle dormitory; brick, five stories',
      Height: 'five floors',
      Model: DORM_MODEL + '; plan 1,029 m2; start of work estimated'
    },
    sources: [WIKI + 'Lathrop_House_(Vassar_College)', OVT]
  },
  {
    id: 'davison_house_vassar',
    name: 'Davison House, Vassar College',
    kind: 'building',
    built: [1900.5, 1902.3],
    end: 9999,
    anchor: [-73.897713, 41.689241],
    build: dorm(R_davison, 171.9),
    replaces: [R_davison],
    facts: {
      Built: 'built 1902 (Allen & Vance of Boston), the fourth quadrangle dormitory; five stories',
      Height: 'five floors',
      Model: DORM_MODEL + '; plan 1,403 m2; start of work estimated'
    },
    sources: [WIKI + 'Davison_House', OVT]
  }
);

// ---------------------------------------------------------------- Poughkeepsie station (1918)
// Cited: Poughkeepsie station article: "Built in 1918", Warren & Wetmore, Beaux Arts, "a smaller version of Grand Central
// Terminal"; a four-story building built into a rockface, the top two levels the waiting room, a five-bay facade with five
// high arched windows. Footprint 0559131f (Overture, named 'Poughkeepsie', height 0.1 m = no value).
const R_station: V2[] = P(-11.9, 36.5, -7.8, -36.5, 11.3, -35.4, 10.8, -26.8, 11.3, -26.8, 10.6, -14.7, 13.1, -14.5, 12.7, -6.7, 10.2, -6.8, 9.5, 6.1, 8.9, 6.1, 8.5, 13.8, -0.6, 13.3, -1.9, 37.0);
NY_TOWNS.push({
  id: 'poughkeepsie_station',
  name: 'Poughkeepsie Railroad Station',
  kind: 'building',
  built: [1916.5, 1918],
  end: 9999,
  anchor: [-73.937689, 41.707159],
  build: b => {
    b.color('#B07A5A').prism(R_station, 0, 14.5);
    b.color('#E4DFD0').prism(scale(R_station, 1.01, 1.0, 176.8), 14.5, 15.8);
    b.color('#5A5550').prism(scale(R_station, 0.9, 0.97, 176.8), 15.8, 16.4);
  },
  replaces: [R_station],
  facts: {
    Built: 'built 1918 by Warren & Wetmore in the Beaux-Arts style as a small Grand Central; four storeys built into the rockface (platforms below, the waiting room above); listed on the National Register in 1976',
    Height: 'four storeys',
    Model: 'plan from the footprint (1,216 m2; the record carries no height); the 16.4 m top (the waiting-room block over the street), the trim band and the colours are estimated; the arched windows are not modelled: LOW; start of work (1916.5) estimated'
  },
  sources: [WIKI + 'Poughkeepsie_station', OVT]
});

// ---------------------------------------------------------------- Bardavon 1869 Opera House
// Cited: Bardavon article: "built in 1869", J. A. Wood, the oldest continuously operating theater in New York State,
// "an unusual two-stage dome"; renovated 1905. Footprint bb649847 (Overture h 19.4 m): 62 x 25 m, long axis 108 degrees.
const R_bardavon: V2[] = P(23.4, -19.8, 31.5, 3.5, 6.1, 12.2, 5.9, 11.7, 1.5, 12.5, -0.6, 12.1, -2.4, 10.9, -6.7, 12.3, -5.4, 16.4, -23.0, 22.1, -26.2, 12.5, -30.2, 13.8, -33.7, 3.1, -29.7, 1.8, -30.9, -1.8, -13.2, -7.6, -12.0, -3.7, -7.6, -5.2, -6.5, -7.1, -5.0, -8.6, -1.7, -10.4, -2.0, -11.1);
NY_TOWNS.push({
  id: 'bardavon_poughkeepsie',
  name: 'Bardavon 1869 Opera House',
  kind: 'building',
  built: [1868, 1869.5],
  end: 9999,
  anchor: [-73.928788, 41.703087],
  build: b => {
    b.color('#A0583F').prism(R_bardavon, 0, 15.4);
    b.color('#D9D2C0').prism(scale(R_bardavon, 1.01, 1.0, 108.3), 15.4, 16.2);
    b.color('#575B60');
    ridge(b, R_bardavon, 108.3, 16.2, 3.2, 0.3, 0.95);
  },
  replaces: [R_bardavon],
  facts: {
    Built: 'built 1869 as the Collingwood Opera House (J. A. Wood), renovated 1905, a cinema 1923-75 and a performing-arts theater since 1976; the oldest continuously operating theater in New York State',
    Height: '19.4 m (the footprint record, Overture)',
    Model: 'plan from the footprint (1,414 m2); top 19.4 m is the footprint\'s height; the cornice, the wall/roof split and the colours are estimated; the facade and the dome are not modelled: LOW; start of work (1868) estimated'
  },
  sources: [WIKI + 'Bardavon_1869_Opera_House', OVT]
});

// ---------------------------------------------------------------- Dutchess County Court House (1903)
// Cited: Dutchess County Courthouse article: "Built in 1903", the third on the site, William J. Beardsley, "a four-story
// Classical Revival ... faced with red brick ... Palladian windows", opened and dedicated just before the end of 1903.
// Footprint 4643fb5d (Overture, no height).
const R_court: V2[] = P(-13.0, 11.3, -18.9, -7.9, 11.2, -17.0, 23.3, 22.3, 5.3, 31.4, -1.9, 8.0);
NY_TOWNS.push({
  id: 'dutchess_county_courthouse',
  name: 'Dutchess County Court House, Poughkeepsie',
  kind: 'building',
  built: [1902, 1903.95],
  end: 9999,
  anchor: [-73.929311, 41.70392],
  build: b => {
    b.color('#A8573D').prism(R_court, 0, 17.6);
    b.color('#DCD6C6').prism(scale(R_court, 1.02, 1.02), 17.6, 19.0);
    b.color('#8E8A80').prism(scale(R_court, 0.96, 0.96), 19.0, 19.5);
  },
  replaces: [R_court],
  facts: {
    Built: 'built 1903 (William J. Beardsley), the third courthouse on the site (the first, of 1720, hosted the 1788 convention that ratified the Constitution); red brick, Classical Revival; listed 1982',
    Height: 'four storeys',
    Model: 'plan from the footprint (1,084 m2); four storeys cited; storey height (4.4 m, 17.6 m to the cornice), the cornice and parapet (19.5 m) and the colours are estimated; the Palladian windows are not modelled: LOW'
  },
  sources: [WIKI + 'Dutchess_County_Court_House', OVT]
});

// ---------------------------------------------------------------- United States Post Office (1937-39)
// Cited: Post Office article: New Deal post office, fieldstone in the Dutch Colonial manner, architect Eric Kebbon,
// cornerstone laid by Roosevelt 13 October 1937, built over the next two years, 63,000 sq ft (5,670 m2), a cupola. The
// footprint 1,880 m2 x 3 floors = 5,640 m2. Footprint e32aa3d7 (Overture h 0.1 m = no value).
const R_po: V2[] = P(-25.2, 4.5, -28.2, -13.0, -10.2, -16.0, -11.0, -20.5, 5.4, -23.3, 6.2, -18.8, 23.8, -21.7, 26.8, -4.3, 25.3, -4.1, 27.1, 6.5, 16.1, 8.4, 17.8, 18.1, -17.0, 24.0, -18.6, 14.3, -20.9, 14.7, -22.7, 4.1);
NY_TOWNS.push({
  id: 'poughkeepsie_post_office',
  name: 'United States Post Office, Poughkeepsie',
  kind: 'building',
  built: [1937.78, 1939.5],
  end: 9999,
  anchor: [-73.927655, 41.707405],
  build: b => {
    b.color('#9A8F7D').prism(R_po, 0, 10.8);
    b.color('#D9D3C4').prism(scale(R_po, 1.005, 1.005), 10.8, 11.4);
    b.color('#4B4F52');
    hipOver(b, R_po, 11.4, 3.4, 0.5);
    // the cupola (estimated)
    b.color('#E8E3D6').cylinder(0.6, -0.7, 2.3, 14.5, 17.4, 8);
    b.color('#6F8F86').dome(0.6, -0.7, 2.5, 17.4, 1.8, 8, 3);
    b.color('#6F8F86').pyramid(circle(0.6, -0.7, 0.3, 6), 19.2, [0.6, -0.7, 20.6]);
  },
  replaces: [R_po],
  facts: {
    Built: 'cornerstone laid by President Roosevelt on 13 October 1937, finished two years later (Eric Kebbon); irregular fieldstone in the Dutch Colonial manner, after the county courthouse of 1809; five murals; on the National Register since 1989',
    Height: 'three floors (63,000 sq ft over a 1,880 m2 footprint)',
    Model: 'plan from the footprint (1,880 m2); the three floors follow from the cited floor area, but the eave (10.8 m), the hipped roof, the cupola (to 20.6 m) and the colours are estimated: LOW; the start follows the cornerstone'
  },
  sources: [WIKI + 'United_States_Post_Office_(Poughkeepsie,_New_York)', OVT]
});

// ---------------------------------------------------------------- Luckey, Platt & Company (1923)
// Cited: Luckey, Platt article: "The massive, gray, five-story Classical Revival structure ... opened in 1923" (Edward C.
// Smith), Main and Academy streets, closed 1981. Footprint 350fcd54 (Overture h 26 m = the five stories).
const R_luckey: V2[] = P(-25.8, -3.1, -34.1, -20.0, -25.7, -24.2, -20.9, -14.9, -11.2, -18.9, -14.3, -27.7, 10.0, -37.5, 33.3, 18.7, -2.2, 39.3, -13.6, 17.7, 4.0, 9.3, 0.3, 3.1, -16.5, 12.2, -20.5, 4.6, -22.6, 5.6, -27.3, -3.4);
NY_TOWNS.push({
  id: 'luckey_platt_poughkeepsie',
  name: 'Luckey, Platt & Company Department Store, Poughkeepsie',
  kind: 'building',
  built: [1921.5, 1923.5],
  end: 9999,
  anchor: [-73.926093, 41.702609],
  build: b => {
    b.color('#A6A59F').prism(R_luckey, 0, 24.0);
    b.color('#C9C6BC').prism(scale(R_luckey, 1.01, 1.01), 24.0, 26.0);
  },
  replaces: [R_luckey],
  facts: {
    Built: 'opened 1923 (Edward C. Smith) at Main and Academy streets; for most of the century the department store of the Hudson Valley; closed 1981; Classical Revival, gray, five stories',
    Height: '26 m (the footprint record, Overture) = the five cited stories',
    Model: 'plan from the footprint (2,609 m2); top 26 m is the footprint\'s height; the cornice band (2 m) and the colour are estimated; start of work (1921.5) estimated'
  },
  sources: [WIKI + 'Luckey,_Platt_%26_Company_Department_Store', OVT]
});
