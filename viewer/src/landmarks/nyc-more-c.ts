/**
 * New York landmarks, round "more C": Riverbank State Park and the North River Wastewater Treatment
 * Plant under it (Manhattan, Hudson River, West 137th-145th Street).
 * Research, sources and numeric checks: data/research/landmarks_more_c.md.
 *
 * The plant's roof IS the park: the city's footprint of the plant (BIN 1084789, 108,250 m2) is the whole
 * deck, 21.2 m above the river (the city measures the roof at 21.21 m; State Parks: the park "rises 69 feet
 * above the Hudson River" = 21.03 m). Two models with consecutive lifespans share that footprint: the plant
 * of 1986 with its bare roof, and from 1993 the same deck carrying the park. Park features are the
 * OpenStreetMap ways named in the data comments (c) OpenStreetMap contributors, ODbL, map API read
 * 2026-11-11), re-expressed in metres around the anchor (x east, y north); building heights are the city's
 * measured roof heights read as above the deck (estimated). Generator: data/interim/landmarks_more_c/gen.py.
 */
import {MeshBuilder, type V2} from './kit';
import type {Landmark} from './types';

const WIKI = 'https://en.wikipedia.org/wiki/';
const OSM = 'https://www.openstreetmap.org/way/';

/** Local frame: the centroid of the plant's official footprint (BIN 1084789). */
const ANCHOR: V2 = [-73.956775, 40.825532];
/** Deck level above the terrain at the anchor (m): city roof height 21.21; State Parks 69 ft = 21.03. */
const H = 21.2;

type Piece = [V2[], V2[][]?];

// <data> (data/interim/landmarks_more_c/gen_ts.py)
const PLANT: V2[] = [[45.7,260.5],[147.5,209.1],[175.7,264.8],[182.4,261.4],[180.8,258.2],[245.0,225.9],[249.0,233.0],[240.6,237.5],[240.5,238.7],[241.3,240.2],[243.4,241.1],[256.3,234.5],[256.6,232.0],[255.7,230.7],[254.2,230.4],[251.4,231.9],[249.1,227.5],[253.3,225.3],[207.3,143.6],[197.8,136.3],[172.1,101.1],[126.8,20.2],[119.3,9.4],[98.7,-5.5],[10.0,-158.3],[-64.8,-285.5],[-230.9,-201.6],[-186.6,-114.3],[-184.0,-115.7],[-92.5,64.6],[-95.6,66.1],[-90.2,76.6],[-84.8,73.8],[-80.7,82.0],[-50.2,66.6],[-8.8,148.3],[-19.5,153.7],[-14.6,163.3],[-12.6,162.3],[40.5,267.0],[47.2,263.6]];
const BRIDGE: V2[] = [[70.0,-283.7],[65.0,-279.1],[58.8,-276.1],[48.1,-271.5],[40.2,-268.6],[31.0,-266.7],[-42.2,-253.5],[-53.5,-252.8]];
/** Footprints of the park buildings the city also draws on the deck (BIN 1090423-1090431), replaced by the park. */
const DECK_FOOTPRINTS: V2[][] = [[[-69.2,-186.0],[-38.7,-200.4],[-52.1,-228.6],[-82.6,-214.1]],[[53.3,-65.8],[-0.4,-156.4],[-11.0,-150.3],[37.0,-56.8]],[[59.6,-11.8],[79.0,-22.1],[57.2,-62.4],[53.7,-60.4],[51.5,-64.8],[39.5,-58.1],[41.4,-54.7],[38.0,-52.6]],[[-99.7,11.5],[-74.6,-1.5],[-76.1,-4.5],[-72.3,-6.4],[-71.0,-3.2],[-62.7,-7.8],[-60.2,-15.0],[-84.7,-65.5],[-92.6,-68.3],[-97.2,-66.4],[-100.0,-72.7],[-101.4,-74.2],[-98.7,-80.7],[-103.1,-87.0],[-145.4,-67.2],[-134.5,-47.2],[-130.5,-49.4]],[[82.2,63.0],[113.7,47.5],[82.7,-12.7],[52.0,3.2]],[[-15.2,113.2],[16.4,96.8],[15.1,94.5],[17.0,93.4],[18.3,95.9],[31.8,89.4],[8.2,43.7],[-4.9,49.9],[-3.2,53.3],[-5.6,54.4],[-7.1,51.1],[-38.5,66.9]],[[46.9,119.6],[57.4,114.7],[62.3,124.3],[82.8,113.8],[78.2,104.2],[87.7,99.4],[80.3,83.9],[77.4,84.8],[76.4,83.4],[79.5,81.3],[76.6,76.0],[74.5,75.7],[75.0,73.0],[78.3,73.8],[79.7,68.2],[77.4,67.6],[78.1,64.7],[68.2,61.1],[63.9,72.8],[38.9,85.9],[34.8,97.1],[39.6,97.9],[41.4,102.0],[38.7,104.6]],[[68.2,61.1],[80.6,64.1],[53.3,12.3],[44.8,16.1]],[[107.7,212.3],[145.1,193.2],[142.4,187.3],[141.3,187.8],[139.8,187.5],[140.5,185.4],[139.8,183.4],[136.7,182.9],[135.2,184.0],[134.9,185.3],[133.2,185.4],[128.6,176.6],[107.3,187.8],[109.2,192.1],[108.3,195.8],[106.6,196.0],[105.3,196.8],[104.8,199.1],[105.4,200.6],[106.8,201.7],[105.9,205.4],[104.8,206.5]]];
/** Slabs on the deck, by kind. OSM ways: path = layer-2 footways, road = Riverbank Park Access Road (46568279, 118524657, 910522621, 1443589781),
 *  garden = 943557524, 1237672046, 1237673788, 943557533, 118527542, 1291178511, 1291178523; play = 1553756149, 1553756164;
 *  track = 118527547 minus 386500083; infield = 386500083 minus the pitch; pitch = 118527528 (soccer;american_football);
 *  ball = 367236669 (baseball / softball); tennis = 367235360, 367235363, 367235365, 367235369; court (basketball) = 367235358, 367235362,
 *  367236664, 367236666; handball = 118527555; pool = 118527521 (Riverbank Outdoor Pool); wade = 1067987926 (paddling pool). */
const DECK: Record<string, Piece[]> = {"garden":[[[[0.9,-156.3],[-10.8,-149.4],[30.1,-70.3],[45.0,-79.0]]],[[[55.8,58.3],[39.0,25.8],[16.7,37.2],[33.6,69.7]]],[[[-51.8,0.8],[-51.0,-1.3],[-58.1,-15.2],[-60.7,-8.1],[-58.2,-1.6]]],[[[-94.0,-82.5],[-95.5,-76.3],[-91.6,-69.6],[-84.8,-67.1],[-92.0,-81.1]]]],"play":[[[[-85.3,-225.8],[-73.5,-231.8],[-72.4,-234.8],[-72.4,-238.5],[-73.4,-242.1],[-75.5,-245.2],[-78.4,-247.7],[-82.2,-248.9],[-94.0,-243.0]]],[[[-87.8,38.1],[-88.5,40.6],[-88.3,44.8],[-86.8,48.6],[-84.4,51.6],[-81.2,53.8],[-77.5,54.9],[-73.7,54.9],[-70.0,53.8],[-66.8,51.6],[-64.3,48.6],[-63.4,46.2],[-60.3,47.1],[-67.9,32.2],[-73.2,34.9],[-76.0,29.5],[-91.0,37.1]]]],"track":[[[[-8.2,16.4],[-1.2,17.0],[5.4,16.5],[11.5,15.2],[14.3,14.3],[17.0,13.1],[22.3,10.1],[25.0,8.0],[27.2,5.8],[29.7,3.2],[31.6,0.7],[35.1,-5.4],[39.0,-8.8],[49.0,-14.1],[-10.4,-129.7],[-14.1,-135.4],[-19.1,-140.8],[-21.8,-143.1],[-25.0,-145.2],[-31.9,-148.6],[-39.5,-150.7],[-43.7,-151.2],[-47.8,-151.1],[-52.2,-150.6],[-56.3,-149.8],[-61.0,-148.3],[-65.2,-146.4],[-69.2,-143.9],[-72.7,-140.9],[-75.9,-137.8],[-78.3,-134.9],[-80.7,-131.4],[-83.9,-124.5],[-85.6,-117.4],[-85.9,-113.8],[-85.6,-106.8],[-84.2,-100.0],[-81.8,-93.8],[-23.2,22.3],[-13.5,17.6]],[[[30.2,-27.1],[30.4,-20.6],[30.0,-17.2],[28.6,-11.8],[27.4,-9.0],[24.6,-4.2],[21.1,-0.1],[17.3,3.1],[13.9,5.2],[11.1,6.5],[6.8,7.7],[1.6,8.5],[-4.0,8.5],[-9.5,7.5],[-15.1,5.4],[-20.6,1.9],[-23.1,-0.5],[-27.8,-6.3],[-74.0,-97.2],[-76.0,-102.4],[-77.2,-107.8],[-77.4,-110.6],[-77.2,-116.2],[-76.6,-119.0],[-74.7,-124.5],[-73.2,-126.9],[-71.5,-129.8],[-69.5,-132.2],[-67.0,-134.6],[-64.3,-136.8],[-61.0,-138.9],[-57.9,-140.3],[-54.1,-141.6],[-51.1,-142.2],[-47.3,-142.7],[-44.3,-142.6],[-40.9,-142.3],[-37.7,-141.6],[-32.0,-139.4],[-26.9,-136.3],[-22.5,-132.4],[-20.0,-129.3],[-17.8,-125.5],[28.4,-34.0],[29.5,-30.5]]]]],"infield":[[[[-20.0,-129.3],[-22.5,-132.4],[-26.9,-136.3],[-32.0,-139.4],[-37.7,-141.6],[-40.9,-142.3],[-47.3,-142.7],[-54.1,-141.6],[-57.9,-140.3],[-61.0,-138.9],[-64.3,-136.8],[-67.0,-134.6],[-69.5,-132.2],[-71.5,-129.8],[-74.7,-124.5],[-76.6,-119.0],[-77.2,-116.2],[-77.4,-110.6],[-76.7,-105.1],[-76.0,-102.4],[-74.0,-97.2],[-27.8,-6.3],[-25.4,-3.1],[-20.6,1.9],[-15.1,5.4],[-9.5,7.5],[-4.0,8.5],[1.6,8.5],[6.8,7.7],[11.1,6.5],[13.9,5.2],[17.3,3.1],[21.1,-0.1],[24.6,-4.2],[27.4,-9.0],[28.6,-11.8],[29.4,-14.5],[30.4,-20.6],[30.2,-27.1],[29.5,-30.5],[28.4,-34.0],[-17.8,-125.5]],[[[-20.2,-127.1],[27.8,-33.0],[-25.2,-6.4],[-73.1,-100.5]]]]],"pitch":[[[[27.8,-33.0],[-20.2,-127.1],[-73.1,-100.5],[-25.2,-6.4]]]],"tennis":[[[[-91.2,-175.4],[-81.3,-180.4],[-92.3,-201.8],[-102.1,-196.9]]],[[[-106.7,-206.7],[-96.9,-211.6],[-107.9,-233.2],[-117.7,-228.2]]],[[[-119.8,-200.2],[-110.0,-205.1],[-120.9,-226.6],[-130.8,-221.7]]],[[[-104.1,-169.0],[-94.3,-173.9],[-105.3,-195.4],[-115.1,-190.5]]]],"court":[[[[-52.4,-196.1],[-39.4,-202.7],[-51.8,-226.9],[-64.9,-220.2]]],[[[-67.0,-188.6],[-53.9,-195.2],[-66.4,-219.4],[-79.5,-212.8]]],[[[-174.5,-212.2],[-180.7,-223.9],[-202.8,-212.5],[-196.6,-200.7]]],[[[-143.9,-227.2],[-150.1,-238.9],[-172.1,-227.5],[-165.9,-215.7]]]],"handball":[[[[-135.9,-234.7],[-84.9,-260.5],[-91.0,-272.2],[-142.0,-246.5]]]],"ball":[[[[-213.9,-187.6],[-196.2,-152.4],[-192.3,-154.6],[-181.4,-131.8],[-175.3,-129.6],[-145.3,-144.8],[-144.2,-142.6],[-105.9,-160.4],[-139.1,-224.9]]]],"pool":[[[[-110.2,-64.5],[-116.4,-77.0],[-137.5,-66.6],[-131.2,-54.1]]]],"wade":[[[[-104.8,-81.5],[-106.4,-82.2],[-107.3,-82.1],[-108.8,-81.1],[-109.3,-79.4],[-108.7,-77.8],[-108.1,-77.2],[-106.4,-76.8],[-105.5,-77.0],[-104.2,-78.2],[-103.9,-80.0],[-104.2,-80.8]]]],"path":[[[[-84.8,-253.6],[-85.6,-253.6],[-105.7,-245.6],[-218.9,-189.1],[-219.5,-188.6],[-219.5,-187.8],[-187.8,-122.3],[-187.2,-121.7],[-186.4,-121.8],[-164.7,-132.4],[-164.4,-131.4],[-177.5,-124.9],[-176.5,-122.9],[-162.5,-129.9],[-120.6,-149.6],[-115.6,-138.9],[-141.6,-126.3],[-149.9,-106.9],[-155.4,-104.0],[-166.4,-124.7],[-168.3,-123.7],[-157.3,-102.9],[-169.2,-95.5],[-169.6,-94.9],[-169.5,-94.2],[-81.5,77.3],[-80.8,77.7],[-80.1,77.6],[-50.5,61.9],[-21.5,119.5],[17.4,132.2],[1.8,180.4],[39.7,255.5],[40.4,255.9],[41.1,255.8],[93.5,228.3],[104.4,227.6],[147.2,206.9],[174.1,257.2],[174.8,257.7],[175.5,257.6],[244.1,223.0],[247.9,229.8],[249.8,228.8],[245.5,220.9],[244.9,220.5],[244.2,220.5],[175.5,255.2],[149.2,205.9],[184.8,188.5],[201.2,194.0],[201.9,191.9],[40.1,137.8],[131.9,91.1],[139.5,87.6],[138.6,85.6],[131.4,88.9],[75.8,68.4],[75.1,70.5],[128.7,90.3],[37.2,136.9],[20.2,130.9],[31.5,96.2],[29.4,95.5],[18.1,130.2],[-19.9,117.8],[-49.1,59.9],[-49.5,59.4],[-50.6,59.4],[-80.1,75.1],[-167.1,-94.2],[-155.3,-101.5],[-148.1,-105.4],[-140.0,-124.6],[-114.7,-137.0],[-35.2,22.6],[-34.5,23.1],[9.4,34.8],[33.4,83.4],[30.8,91.2],[32.9,91.9],[35.4,84.1],[62.6,70.3],[63.1,69.7],[63.8,66.3],[65.4,66.9],[66.2,64.8],[64.2,64.1],[64.9,60.0],[43.8,17.2],[53.2,-16.9],[-6.8,-141.4],[-10.4,-146.7],[-14.5,-150.8],[-17.2,-152.7],[-0.1,-161.8],[52.5,-73.3],[86.2,-13.6],[88.1,-14.7],[54.4,-74.4],[1.3,-163.8],[-52.5,-253.4],[-53.5,-252.8],[-53.9,-253.8],[-68.9,-247.8]],[[[-69.2,-230.7],[-68.9,-231.3],[-68.2,-235.2],[-67.8,-245.9],[-53.9,-251.4],[-25.3,-203.8],[-70.8,-181.8],[-90.8,-219.7]],[[-92.5,-104.9],[-92.8,-112.6],[-91.0,-128.3],[-87.1,-138.3],[-79.6,-145.3],[-70.7,-152.4],[-61.4,-157.2],[-50.0,-160.2],[-34.1,-158.0],[-25.2,-154.5],[-19.9,-151.9],[-16.0,-149.1],[-12.0,-145.2],[-8.7,-140.4],[50.9,-16.5],[41.7,16.5],[10.1,32.7],[-33.5,21.1],[-90.1,-92.6]],[[-93.1,-128.8],[-95.0,-112.6],[-94.7,-104.7],[-93.8,-100.1],[-112.7,-137.9],[-98.5,-144.8],[-89.3,-138.5]],[[-119.2,-151.7],[-119.8,-152.1],[-120.5,-152.0],[-162.4,-132.4],[-162.7,-133.4],[-71.7,-178.9],[-70.4,-176.7],[-68.5,-177.8],[-69.7,-179.9],[-24.1,-201.9],[-1.2,-163.7],[-19.3,-154.1],[-24.3,-156.6],[-33.5,-160.2],[-50.0,-162.5],[-62.2,-159.2],[-68.3,-156.1],[-76.1,-173.9],[-78.2,-173.0],[-70.3,-155.0],[-72.0,-154.1],[-81.0,-147.0],[-88.1,-140.3],[-97.8,-147.0],[-98.4,-147.2],[-113.7,-139.9]],[[-70.4,-235.3],[-71.0,-232.2],[-91.8,-221.6],[-103.7,-244.0],[-85.1,-251.4],[-70.0,-245.9]],[[-217.0,-187.6],[-105.7,-243.1],[-72.8,-180.9],[-186.3,-124.3]],[[36.9,139.1],[181.8,187.5],[103.7,225.5],[92.7,226.3],[41.1,253.4],[4.1,180.2],[19.5,133.0]],[[11.6,34.4],[42.1,18.8],[62.7,60.5],[61.1,68.6],[35.0,81.8]]]]],"road":[[[[136.6,87.6],[140.0,97.2],[134.5,95.1],[127.4,94.2],[127.1,96.7],[125.9,94.4],[111.7,102.2],[104.5,107.9],[103.9,108.7],[103.7,109.5],[103.7,115.6],[104.0,116.7],[112.9,135.3],[115.3,134.2],[112.9,135.3],[123.4,157.1],[127.3,163.0],[128.6,163.9],[167.6,175.1],[198.0,186.4],[215.6,191.3],[231.9,193.5],[232.5,188.4],[216.8,186.3],[199.5,181.4],[169.3,170.2],[160.1,167.6],[166.7,140.4],[166.6,138.9],[146.7,100.6],[141.4,85.4],[89.4,-15.3],[84.8,-12.9]],[[[133.2,100.2],[142.4,103.7],[161.4,140.1],[155.1,166.1],[131.0,159.1],[128.0,154.7],[108.9,115.0],[108.9,111.0],[114.5,106.5],[127.6,99.4]]]]]};
/** Park buildings (OSM ways): pool_bldg 118527498, athletic 118527506, rink 118527530, cultural 118527501, restaurant 118527538,
 *  pavilion 118527504, greenhouse 1271574699. */
const BLD: Record<string, V2[]> = {"pool_bldg":[[-98.9,11.0],[-60.7,-8.1],[-57.7,-16.4],[-83.5,-66.7],[-91.6,-69.6],[-129.9,-50.5]],"athletic":[[-16.9,112.5],[-40.1,66.5],[6.4,43.3],[29.6,89.3]],"rink":[[52.0,3.3],[82.6,63.4],[113.1,48.0],[82.5,-12.0]],"cultural":[[60.7,124.5],[55.7,114.9],[45.8,119.8],[37.4,104.4],[40.8,103.0],[39.0,99.0],[22.4,92.9],[27.8,90.2],[35.8,92.9],[37.9,85.7],[63.8,71.8],[67.5,61.0],[46.1,16.1],[55.8,10.8],[82.6,63.4],[77.6,63.1],[73.5,75.0],[75.8,75.2],[78.5,80.8],[75.2,82.5],[76.3,84.8],[79.7,83.5],[87.3,98.7],[77.2,104.1],[82.1,113.8]],"restaurant":[[104.0,208.3],[109.5,194.8],[107.0,189.0],[129.1,178.2],[133.0,187.2],[134.8,187.4],[135.7,185.4],[137.5,185.2],[139.3,186.0],[140.4,189.0],[142.2,189.6],[144.9,195.5],[107.0,214.8]],"pavilion":[[58.5,-13.4],[36.9,-54.1],[55.1,-63.6],[76.7,-22.9]],"greenhouse":[[34.4,-69.0],[45.4,-74.6],[52.9,-60.0],[41.9,-54.4]]};
/** Height above the deck (m): the city's measured roof heights of BINs 1090426, 1090428, 1090427, 1090429, 1090431, 1090425;
 *  the greenhouse has none (estimated). */
const BLD_H: Record<string, number> = {pool_bldg: 11.89, athletic: 8.84, rink: 13.11, cultural: 8.84, restaurant: 7.62, pavilion: 6.1, greenhouse: 3.5};

// [colour, height above the deck (m)]: slabs a few centimetres thick, painted in draw order
const SLAB: Record<string, [string, number]> = {
  garden: ['#5d8f46', 0.04],
  path: ['#d3ccbb', 0.06],
  road: ['#5a5e63', 0.07],
  play: ['#b4573f', 0.08],
  infield: ['#4f9a49', 0.08],
  track: ['#b5503a', 0.1],
  ball: ['#5a9c52', 0.1],
  tennis: ['#3f7fa8', 0.1],
  court: ['#c2652d', 0.1],
  handball: ['#8f959b', 0.1],
  pitch: ['#5fae52', 0.12],
  pool: ['#3aa3dc', 0.12],
  wade: ['#79cdf1', 0.14]
};
const WALL = '#cfc8b8';
const ROOF = '#7f8890';

function plantBody(b: MeshBuilder, roof: string) {
  b.color('#9b9a93').walls(PLANT, 0, H);
  b.color(roof).cap(PLANT, H);
}

function buildPlant(b: MeshBuilder) {
  plantBody(b, '#a9a8a1');
}

function buildPark(b: MeshBuilder) {
  plantBody(b, '#bdb8aa');
  for (const [k, pieces] of Object.entries(DECK)) {
    const [col, dz] = SLAB[k];
    b.color(col);
    for (const [ring, holes] of pieces) b.cap(ring, H + dz, holes ?? []);
  }
  for (const [k, ring] of Object.entries(BLD)) {
    const h = BLD_H[k];
    b.color(WALL).walls(ring, H, H + h);
    b.color(ROOF).cap(ring, H + h);
  }
  // the 138th Street footbridge (OSM way 46568274): a 4 m deck at deck level on piers where it leaves the plant
  b.color('#8d8f92');
  for (let i = 0; i < BRIDGE.length - 1; i++) b.beam([BRIDGE[i][0], BRIDGE[i][1], H - 0.45], [BRIDGE[i + 1][0], BRIDGE[i + 1][1], H - 0.45], 4, 0.9);
  b.color('#6f7479');
  for (const i of [2, 5]) b.box(BRIDGE[i][0], BRIDGE[i][1], 0, 1.4, 1.4, H - 0.9);
}

const SOURCES = [
  WIKI + 'Riverbank_State_Park',
  'https://parks.ny.gov/visit/state-parks/riverbank-state-park-denny-farrell-riverbank-state-park',
  'https://data.cityofnewyork.us/d/5zhs-2jue',
  OSM + '118524694',
  OSM + '275080368'
];


// ---------------------------------------------------------------------------------------------
// Pier decks that carry sports fields (the generic deck / shed of the city hides them)
// <piers> (data/interim/landmarks_more_c/gen_piers.py)
type Field = [string, string, V2[], number?]; // OSM way, kind, outline, 1 = on the courtyard floor / deck, not on the roof
type PierData = {anchor: V2; ring: V2[]; holes?: V2[][]; deck?: V2[]; fields: Field[]};
const PIERS: Record<string, PierData> = {"p40":{"anchor":[-74.012727,40.729427],"ring":[[131.2,107.6],[114.2,-125.8],[-174.7,-95.1],[-173.7,-86.0],[-131.0,-91.5],[-107.1,132.6]],"deck":[[131.3,114.1],[121.7,-21.6],[118.2,-61.0],[113.2,-131.3],[68.9,-126.7],[68.6,-130.7],[66.6,-130.4],[66.9,-126.5],[-179.3,-100.8],[-181.7,-97.8],[-180.1,-86.1],[-177.6,-84.1],[-137.0,-88.4],[-113.2,137.1],[-110.4,139.4]],"fields":[["23529474","american_football",[[-50.6,40.6],[-55.7,-7.6],[53.5,-19.0],[58.6,29.3]],1],["65223814","soccer",[[68.2,-119.4],[112.0,-123.5],[118.7,-51.4],[75.3,-46.7]]],["576166509","multi",[[-3.7,-77.0],[-7.0,-109.2],[55.2,-115.5],[58.5,-83.3]]]]},"p5":{"anchor":[-74.00168,40.69488],"ring":[[112.8,-1.3],[97.0,5.8],[84.3,-22.5],[100.1,-29.5],[61.8,-90.3],[-112.3,-11.8],[-61.1,91.6],[117.7,9.5]],"fields":[["328277180","soccer",[[-10.6,54.1],[-47.3,-27.0],[-93.0,-6.6],[-56.2,74.5]]],["328277282","soccer",[[-5.6,51.9],[40.5,31.3],[3.8,-49.8],[-42.3,-29.3]]],["328277283","soccer",[[45.5,29.0],[92.1,8.2],[55.4,-72.9],[8.8,-52.1]]]]},"p2":{"anchor":[-73.998828,40.699567],"ring":[[109.8,-0.8],[94.1,6.6],[55.6,-78.2],[72.8,-91.1],[69.0,-100.8],[35.7,-75.4],[35.7,-73.3],[-102.4,-11.9],[-56.4,84.2],[113.1,8.0]],"fields":[["328274771","basketball",[[-22.0,-13.9],[-9.9,12.0],[4.0,5.8],[-7.9,-20.3]]],["328274772","multi",[[-53.9,74.4],[-21.1,59.7],[-36.2,26.2],[-49.6,-3.7],[-54.2,-1.6],[-82.5,11.0]]],["328275677","pickleball",[[16.2,-33.3],[8.4,-50.4],[-61.9,-18.8],[-54.2,-1.6]]],["328275678","american_handball",[[52.5,24.0],[49.7,17.5],[82.7,3.0],[85.6,9.6]]],["328275679","playground",[[-54.2,-1.6],[-61.9,-18.8],[-90.3,-6.1],[-82.5,11.0]]],["328275680","roller_skating",[[34.2,31.8],[-14.0,53.6],[-16.6,54.4],[-18.9,54.0],[-20.8,52.6],[-21.9,50.5],[-28.3,36.6],[-28.9,34.3],[-28.4,32.0],[-27.0,30.2],[-25.2,29.2],[23.0,7.4],[24.9,6.7],[27.3,6.8],[29.3,8.0],[30.7,9.9],[37.0,23.8],[37.9,26.0],[37.7,28.4],[36.4,30.4]]],["675333781","basketball",[[-44.2,-3.9],[-32.2,22.0],[-18.2,15.8],[-30.1,-10.2]]],["675333783","basketball",[[0.2,-24.5],[12.2,1.8],[26.3,-4.3],[14.7,-30.7]]],["979905190","basketball",[[40.3,-41.7],[52.1,-15.2],[66.4,-21.5],[54.7,-48.0]]],["979905191","basketball",[[21.2,-33.7],[33.2,-7.3],[47.4,-13.4],[35.7,-40.0]]]]}};

const FIELD_COLOR: Record<string, string> = {
  soccer: '#5fae52', multi: '#4f9a49', basketball: '#c2652d', pickleball: '#3f7fa8', american_handball: '#8f959b',
  roller_skating: '#b5503a', playground: '#b4573f'
};

/** mode 0: bare; 1: the fields on the roof only; 2: all fields. A pier with a courtyard (Pier 40) stands on its deck slab. */
function pierBody(key: string, top: number, wall: string, roof: string, mode: number) {
  return (b: MeshBuilder) => {
    const P = PIERS[key];
    const holes = P.holes ?? [];
    if (P.deck) {
      b.color('#8f8d86').walls(P.deck, 0, DECK_H);
      b.color('#b9b7ad').cap(P.deck, DECK_H);
    }
    b.color(wall).prism(P.ring, 0, top, {top: false, holes});
    b.color(roof).cap(P.ring, top, holes);
    if (!mode) return;
    P.fields.forEach(([, kind, ring, low], i) => {
      if (low ? mode < 2 : false) return;
      b.color(FIELD_COLOR[kind] ?? '#4f9a49').cap(ring, (low ? DECK_H : top) + 0.06 + 0.01 * (i % 3));
    });
  };
}

const P40_SOURCES = [WIKI + 'Pier_40', WIKI + 'Hudson_River_Park', 'https://data.cityofnewyork.us/d/5zhs-2jue', OSM + '65223814', OSM + '576166509'];
const BBP_SOURCES = [WIKI + 'Brooklyn_Bridge_Park', 'https://www.openstreetmap.org/relation/56469108'];
const P40_H = 14.7;
const DECK_H = 3.0;
const BBP_H = 3.0;

export const MORE_C: Landmark[] = [
  {
    id: 'north_river_plant_1986',
    name: 'North River Wastewater Treatment Plant',
    kind: 'building',
    built: [1978.0, 1986.0],
    end: 1992.0,
    anchor: ANCHOR,
    build: buildPlant,
    replaces: [PLANT, ...DECK_FOOTPRINTS],
    facts: {
      Built: 'foundation of 2,300 caissons pinned into bedrock (up to 230 ft below the river) finished in 1978; the treatment works built in two phases, 1986 to 1991 (in service from 1986)',
      Size: 'a 108,250 m2 deck 21 m (69 ft) above the Hudson, the river running on beneath it; West 137th to 145th Street',
      Model: 'the whole official footprint (BIN 1084789) extruded to the city-measured roof, 21.2 m, with a bare roof: the plant hall and tanks under the deck are not modelled; the dates 1978 (foundation) and 1986 are the sources\' (the model stands for the plant from 1978 on), its end in 1992 is when the park deck was laid (estimated)'
    },
    sources: SOURCES
  },
  {
    id: 'riverbank_state_park',
    name: 'Riverbank State Park (Denny Farrell Riverbank State Park)',
    kind: 'park',
    built: [1991.2, 1993.4],
    end: 9999,
    anchor: ANCHOR,
    build: buildPark,
    replaces: [PLANT, ...DECK_FOOTPRINTS],
    facts: {
      Built: 'opened 27 May 1993; designed by Dattner Architects and Abel Bainnson Butz; built on the roof of the North River Wastewater Treatment Plant (renamed for Denny Farrell in 2017)',
      Facilities: '28 acres; five buildings (50 m indoor pool, covered rink, 800-seat cultural theater, 2,500-seat athletic complex, 150-seat restaurant); 400 m eight-lane running track around a football / soccer field, softball field, 4 tennis, 4 basketball and 4 handball courts, 25-yard outdoor pool, wading pool, playgrounds, gardens',
      Model: 'the plant\'s deck (21.2 m) with every slab at its OpenStreetMap position and size (listed in the source comments); buildings are the OSM outlines at the city-measured heights read as above the deck (estimated: the city gives no deck level), flat roofs and the greenhouse height (3.5 m) estimated; colours estimated; the 138th Street footbridge (OSM way 46568274) at deck level on two estimated piers; the 145th Street approach and the plant hall below the deck are not modelled; construction 1991-1993 is estimated (deck complete 1991, opening May 1993)'
    },
    sources: SOURCES
  },
  {
    id: 'pier40_terminal_1962',
    name: 'Pier 40 (Holland America terminal)',
    kind: 'building',
    built: [1958.0, 1962.0],
    end: 1998.0,
    anchor: PIERS.p40.anchor,
    build: pierBody('p40', P40_H, '#a39e92', '#8e8c86', 0),
    replaces: [PIERS.p40.ring],
    facts: {
      Built: 'construction began in 1958 and the terminal opened in 1962 (Holland America Line, a 20-year lease); a three-level shed, the roof used as a car park',
      Size: '14.5 acres, the largest structure in Hudson River Park; the outer decks (the shed) 175 ft wide',
      Model: "the city's footprint of the shed (BIN 1012249, 57,300 m2) extruded to 14.7 m above the water (the city's measured roof 13.11 m plus its ground elevation 1.6 m); the courtyard, the garage at the east end, the ramps and the cargo levels are not modelled; start 1958 and opening 1962 are the source's"
    },
    sources: P40_SOURCES
  },
  {
    id: 'pier40_roof_fields',
    name: 'Pier 40 with its roof fields',
    kind: 'park',
    built: [1997.5, 1998.5],
    end: 2005.4,
    anchor: PIERS.p40.anchor,
    build: pierBody('p40', P40_H, '#a39e92', '#8e8c86', 1),
    replaces: [PIERS.p40.ring],
    facts: {
      Built: 'the upper-level recreation area opened in 1998 on the shed roof (two fields, one small and one soccer, and a flying trapeze); Hudson River Park Trust; the pier was redesignated as parkland in 1998',
      Fields: 'the two roof fields at their OpenStreetMap outlines (ways 65223814, soccer, 3,185 m2; 576166509, 2,023 m2) as turf slabs on the roof',
      Model: "as the terminal, plus the two roof fields; the courtyard of the shed (14,300 m2, a hole in the city's footprint BIN 1012249) stands on the pier deck, 2.5 m above the water; the 1998 opening is the source's, its month is not given: the 1997.5-1998.5 window is estimated"
    },
    sources: P40_SOURCES
  },
  {
    id: 'pier40_main_field',
    name: 'Pier 40 with its roof fields and main field',
    kind: 'park',
    built: [2004.0, 2005.4],
    end: 9999,
    anchor: PIERS.p40.anchor,
    build: pierBody('p40', P40_H, '#a39e92', '#8e8c86', 2),
    replaces: [PIERS.p40.ring],
    facts: {
      Built: 'the main field, in the courtyard on the former cargo level, was built from 2004 and opened in May 2005; the roof fields of 1998 remain',
      Fields: 'the two roof fields at their OpenStreetMap outlines (ways 65223814, soccer, 3,185 m2; 576166509, 2,023 m2) as turf slabs on the roof',
      Model: "as the terminal, plus the two roof fields; the main turf field of 2005 (OSM way 23529474, 5,323 m2) lies on the former cargo level inside the shed and is not drawn; the roof level is the city's, the 1998 opening taken as the date of both fields (the source says 'opened in 1998'; the month is not given: the model's 1997.5-1998.5 is estimated)"
    },
    sources: P40_SOURCES
  },
  {
    id: 'bbp_pier5_fields',
    name: 'Brooklyn Bridge Park, Pier 5 (three turf fields)',
    kind: 'park',
    built: [2011.0, 2012.95],
    end: 9999,
    anchor: PIERS.p5.anchor,
    build: pierBody('p5', BBP_H, '#a39e92', '#b9b7ad', 2),
    replaces: [PIERS.p5.ring],
    facts: {
      Built: 'Pier 5 opened in December 2012 (Michael Van Valkenburgh Associates), after the sheds of the piers were taken down when construction began in 2008',
      Fields: 'three artificial-turf soccer fields, OSM ways 328277180, 328277282, 328277283 (4,450-4,540 m2 each)',
      Model: "the pier's outline from the city's pier layer (21,900 m2) as a deck 2.5 m above the water; the three fields at their OpenStreetMap outlines; the uplands, picnic peninsula and the fences are not modelled; the start of construction (2011) is estimated"
    },
    sources: BBP_SOURCES.concat([OSM + '328277180', OSM + '328277282', OSM + '328277283'])
  },
  {
    id: 'bbp_pier2_courts',
    name: 'Brooklyn Bridge Park, Pier 2 (courts and play turf)',
    kind: 'park',
    built: [2013.0, 2014.4],
    end: 9999,
    anchor: PIERS.p2.anchor,
    build: pierBody('p2', BBP_H, '#a39e92', '#b9b7ad', 2),
    replaces: [PIERS.p2.ring],
    facts: {
      Built: 'Pier 2 opened in May 2014',
      Fields: 'basketball (5 courts), handball, bocce and shuffleboard courts, artificial turf, swings, fitness bars (Wikipedia); the model draws the OpenStreetMap pitches: 5 basketball (ways 328274771, 675333781, 675333783, 979905190, 979905191), pickleball (328275677), handball (328275678), the play turf (328274772), the roller rink (328275680) and a playground (328275679)',
      Model: "the pier's outline from the city's pier layer (18,500 m2) as a deck 2.5 m above the water; fields as slabs at OpenStreetMap outlines (the pickleball polygon of 1,449 m2 is as mapped, probably several courts); bocce, shuffleboard, tables and the roof structure (OSM way 328275185) are not modelled; the start of construction (2013) is estimated"
    },
    sources: BBP_SOURCES.concat([OSM + '328274772', OSM + '328275680'])
  }
];
