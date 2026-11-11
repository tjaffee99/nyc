/**
 * Buildings of the counties around San Francisco (pipeline/region_buildings.py):
 * ~2 M footprints in z13 map tiles (BAYT, same format as the SF file) loaded on demand
 * when zoomed in, decoded and triangulated in a small worker pool, and drawn with the
 * same time-aware BuildingLayer as San Francisco (construction frames, removal).
 */
import {TileLayer} from '@deck.gl/geo-layers';
import {HEAVY_BASE} from '../remote';
import type {Layer} from '@deck.gl/core';
import {buildingsLayer, fromBinary, loadTileInWorker, type BuildingSet} from './buildings';
import {occupiedMask, replacedMask, type LandmarkSet} from '../landmarks';
import {extentDistance, MAP_BOX} from './extent';

// landmarks standing on region footprints (Apple Park, Stanford, stadiums…): the
// footprints under a landmark are hidden, older buildings on the site stand until its
// construction starts — same rule as in San Francisco
let landmarks: LandmarkSet | null = null;
export function setRegionLandmarks(set: LandmarkSet | null) {
  landmarks = set;
}

type Index = {
  z: number;
  tiles: {x: number; y: number; n: number}[];
  /** zoomed-out set: only buildings big enough to see at city scale */
  low?: {z: number; tiles: {x: number; y: number; n: number}[]};
};

/** Tile sets: the city's outer boroughs (nyc_buildings.py) and the counties around the city
 *  (county_buildings.py). Same format, separate folders, so each can be rebuilt alone. */
type TileSet = {id: string; dir: string; index: Index; have: Set<string>; haveLow: Set<string>};
const SETS: {id: string; dir: string}[] = [
  {id: 'region-buildings', dir: `${HEAVY_BASE}data/region-buildings`},
  {id: 'region-buildings-county', dir: `${HEAVY_BASE}data/county-buildings`},
  // the outer counties: the same format, houses as rectangles (county_buildings.py outer)
  {id: 'region-buildings-outer', dir: `${HEAVY_BASE}data/outer-buildings`}
];
let sets: TileSet[] = [];

export async function loadRegionIndex() {
  const loaded = await Promise.all(
    SETS.map(async ({id, dir}) => {
      try {
        const r = await fetch(`${dir}/index.json`);
        if (!r.ok) return null; // not built yet
        // (by content, not by content type: a dev server answers a missing file with
        // index.html, and GitHub's raw host serves JSON as text/plain)
        const text = await r.text();
        if (!text.trimStart().startsWith('{')) return null;
        const index = JSON.parse(text) as Index;
        return {
          id,
          dir,
          index,
          have: new Set(index.tiles.map(t => `${t.x}/${t.y}`)),
          haveLow: new Set((index.low?.tiles ?? []).map(t => `${t.x}/${t.y}`))
        } as TileSet;
      } catch (e) {
        console.warn('building tiles index', dir, e);
        return null;
      }
    })
  );
  sets = loaded.filter((s): s is TileSet => !!s);
}

// every footprint from city scale on, like San Francisco (whose buildings are always all
// drawn): z13 tiles requested two levels up from zoom 11
const FULL_FROM = 11;

function tileLayer(
  id: string,
  dir: string,
  z: number,
  set: Set<string>,
  zoomOffset: number,
  year: number,
  quality: boolean,
  show: boolean,
  loadFrom: number,
  loadTo: number | null
) {
  return new TileLayer<BuildingSet | null>({
    id,
    minZoom: z,
    maxZoom: z,
    tileSize: 256,
    zoomOffset,
    // the layer stays in the scene at every zoom (removing it would throw its tiles
    // away and zooming back would download and triangulate them again: buildings
    // blinking out); it loads tiles over [loadFrom, loadTo] — a little beyond the zoom
    // where it is drawn, so the set is ready when the view crosses over — and keeps a
    // large cache
    visibleMinZoom: loadFrom,
    visibleMaxZoom: loadTo,
    maxCacheSize: 900,
    extent: MAP_BOX,
    getTileData: async ({index: t}: any) => {
      if (!set.has(`${t.x}/${t.y}`)) return null;
      // outside the map's extent (Morgan Hill, Antioch, …): not drawn
      const n = 2 ** t.z;
      const lon = ((t.x + 0.5) / n) * 360 - 180;
      const lat = (Math.atan(Math.sinh(Math.PI * (1 - (2 * (t.y + 0.5)) / n))) * 180) / Math.PI;
      if (extentDistance(lon, lat) < -3) return null;
      const file = await loadTileInWorker(new URL(`${dir}/${z}/${t.x}/${t.y}.bin.gz`, document.baseURI).href);
      return fromBinary(file);
    },
    renderSubLayers: (props: any) => {
      const s = props.data as (BuildingSet & {lmDone?: boolean}) | null;
      if (!s || !show) return null;
      if (landmarks && !s.lmDone) {
        s.replaced = replacedMask(landmarks, s.centroids, s.count, s.height);
        s.occupied = occupiedMask(landmarks, s.centroids, s.count);
        s.lmDone = true;
      }
      return buildingsLayer(s, year, quality, true, `${props.id}-b`) as any;
    },
    updateTriggers: {renderSubLayers: [year, quality, show]}
  } as any);
}

/** Region buildings: every footprint in z13 tiles from zoom 11; further out, only the
 *  large / tall ones (z11 tiles) — houses are below a pixel there and the suburban ground
 *  colour stands for them. */
export function regionBuildingLayers(year: number, zoom: number, quality: boolean): Layer[] {
  const out: Layer[] = [];
  for (const s of sets) {
    if (s.index.low)
      out.push(tileLayer(`${s.id}-low`, s.dir, s.index.low.z, s.haveLow, 2, year, quality, zoom >= 9 && zoom < FULL_FROM, 8.6, FULL_FROM + 0.8) as any);
    out.push(tileLayer(s.id, s.dir, s.index.z, s.have, 2, year, quality, zoom >= FULL_FROM, FULL_FROM - 0.3, null) as any);
  }
  return out;
}
