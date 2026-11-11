/**
 * Small committed tables from data/tables/*.csv (eras, events, population).
 * Imported at build time; missing files simply yield empty tables.
 */
// only the tables the viewer shows (the research tables are pipeline inputs: don't bundle them)
const files = import.meta.glob(['../../../data/tables/eras.csv', '../../../data/tables/events.csv', '../../../data/tables/events_counties.csv', '../../../data/tables/population.csv'], {
  query: '?raw',
  import: 'default',
  eager: true
}) as Record<string, string>;

function table(name: string): Record<string, string>[] {
  const key = Object.keys(files).find(k => k.endsWith(`/${name}.csv`));
  return key ? parseCsv(files[key]) : [];
}

/** Minimal RFC-4180 CSV parser (quoted fields, embedded commas/newlines). */
export function parseCsv(text: string): Record<string, string>[] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = '';
  let quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i++;
        } else quoted = false;
      } else field += c;
    } else if (c === '"') quoted = true;
    else if (c === ',') {
      row.push(field);
      field = '';
    } else if (c === '\n' || c === '\r') {
      if (c === '\r' && text[i + 1] === '\n') i++;
      row.push(field);
      field = '';
      if (row.some(f => f !== '')) rows.push(row);
      row = [];
    } else field += c;
  }
  if (field !== '' || row.length) {
    row.push(field);
    if (row.some(f => f !== '')) rows.push(row);
  }
  const [header, ...body] = rows;
  if (!header) return [];
  const keys = header.map(h => h.trim());
  return body.map(r => Object.fromEntries(keys.map((k, i) => [k, (r[i] ?? '').trim()])));
}

export type Era = {start: number; end: number; title: string; subtitle: string};
export type HistEvent = {
  year: number;
  month?: number;
  day?: number;
  title: string;
  description: string;
  lat?: number;
  lon?: number;
  zoom?: number;
};

export const eras: Era[] = table('eras')
  .map(r => ({start: +r.start_year, end: +r.end_year, title: r.title, subtitle: r.subtitle}))
  .filter(e => Number.isFinite(e.start))
  .sort((a, b) => a.start - b.start);

// (events of a county that is not on the map yet — Nassau, east of the city line — are left out)
const offMap = (r: Record<string, string>) => r.county === 'Nassau' || (+r.lon > -73.745 && +r.lat < 40.93);
export const events: HistEvent[] = [...table('events'), ...table('events_counties').filter(r => !offMap(r))]
  .map(r => ({
    year: +r.year,
    month: r.month ? +r.month : undefined,
    day: r.day ? +r.day : undefined,
    title: r.title,
    description: r.description,
    lat: r.lat ? +r.lat : undefined,
    lon: r.lon ? +r.lon : undefined,
    zoom: r.zoom ? +r.zoom : undefined
  }))
  .filter(e => Number.isFinite(e.year))
  .sort((a, b) => a.year - b.year);

/** Fractional year of an event (mid-month if the day is unknown). */
export function eventTime(e: HistEvent): number {
  if (!e.month) return e.year + 0.5;
  const day = e.day ?? 15;
  return e.year + (e.month - 1) / 12 + (day - 1) / 365;
}

type PopPoint = {year: number; pop: number; estimate: boolean};
const popRows = table('population');

function series(match: (area: string) => boolean): PopPoint[] {
  return popRows
    .filter(r => match((r.area || '').toLowerCase()))
    .map(r => ({year: +r.year, pop: +String(r.population).replace(/[, ]/g, ''), estimate: /estim/i.test(r.note || '')}))
    .filter(p => Number.isFinite(p.year) && p.pop > 0)
    .sort((a, b) => a.year - b.year);
}

/** The five boroughs' area (data/tables/population.csv, area `nyc`): the fallback when cities.json is missing. */
export const cityPopulation = series(a => a === 'nyc');

export function populationLabelAt(year: number): {value: number; label: string} | null {
  const v = populationAt(year, cityPopulation);
  return v == null ? null : {value: v, label: 'New York City'};
}

export function eraAt(year: number): Era | undefined {
  return eras.find(e => year >= e.start && year < e.end);
}

/** Log-linear interpolation between census points (populations grow ~exponentially). */
export function populationAt(year: number, pts: PopPoint[] = cityPopulation): number | null {
  if (!pts.length || year < pts[0].year) return null;
  const last = pts[pts.length - 1];
  if (year >= last.year) return last.pop;
  for (let i = 0; i < pts.length - 1; i++) {
    const a = pts[i];
    const b = pts[i + 1];
    if (year >= a.year && year < b.year) {
      const t = (year - a.year) / (b.year - a.year);
      return Math.exp(Math.log(a.pop) * (1 - t) + Math.log(b.pop) * t);
    }
  }
  return last.pop;
}

// ------------------------------------------------------------------ city populations
// pipeline/cities.py -> data/cities.json: the borough outlines with their census series
// (data/tables/population.csv). Zoomed in, the counter shows the borough under the centre
// of the map; zoomed out, the whole city (the five boroughs' area, also before 1898).
type Ring = [number, number][];
type Place = {name: string; geoid: string; kind: string; rings: Ring[]; bbox?: [number, number, number, number]};
/** 8 September 1664: New Amsterdam becomes New York. */
const ENGLISH = 1664.69;
const FIRST_CENSUS = 1698;
const CITY_BOROUGHS = new Set(['Manhattan', 'The Bronx', 'Brooklyn', 'Queens', 'Staten Island']);
let cities: {places: Place[]; counties: Place[]; pop: Record<string, [number, number][]>; region: [number, number][]; region_label: string} | null =
  null;

export async function loadCities() {
  try {
    const r = await fetch('data/cities.json');
    if (!r.ok || !(r.headers.get('content-type') ?? '').includes('json')) return;
    cities = await r.json();
    for (const p of [...cities!.places, ...cities!.counties]) {
      const xs = p.rings.flat().map(q => q[0]);
      const ys = p.rings.flat().map(q => q[1]);
      p.bbox = [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
    }
  } catch (e) {
    console.warn('cities', e);
  }
}

function inRings(x: number, y: number, rings: Ring[]) {
  let inside = false;
  for (const ring of rings)
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const [xi, yi] = ring[i];
      const [xj, yj] = ring[j];
      if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
    }
  return inside;
}

function placeAt(list: Place[], x: number, y: number) {
  return list.find(p => p.bbox && x >= p.bbox[0] && x <= p.bbox[2] && y >= p.bbox[1] && y <= p.bbox[3] && inRings(x, y, p.rings));
}

function seriesAt(year: number, s: [number, number][] | undefined) {
  if (!s || !s.length || year < s[0][0]) return null;
  return populationAt(year, s.map(([y, v]) => ({year: y, pop: v, estimate: false})));
}

// Connecticut's planning regions replaced its counties in 2022; the census series the counter
// shows there are the old counties' (cities.py OUTER_AREAS), so the label names the county
const COUNTY_LABEL: Record<string, string> = {
  'Greater Bridgeport': 'Fairfield County',
  'Western Connecticut': 'Fairfield County',
  'South Central Connecticut': 'New Haven County'
};

/** The population to show for the year at this map centre and zoom. */
export function localPopulationAt(year: number, lon: number, lat: number, zoom: number): {value: number; label: string} | null {
  if (!cities) return populationLabelAt(year);
  // outside the city: the county under the centre of the map, at any zoom
  const outer = placeAt(cities.counties, lon, lat);
  if (outer && !CITY_BOROUGHS.has(outer.name)) {
    const v = seriesAt(year, cities.pop[`county:${outer.name}`]);
    if (v != null) return {value: v, label: COUNTY_LABEL[outer.name] ?? `${outer.name} County`};
  }
  if (zoom >= 11.5) {
    const city = placeAt(cities.places, lon, lat);
    if (city) {
      const v = seriesAt(year, cities.pop[city.geoid] ?? cities.pop[city.name]);
      if (v != null) return {value: v, label: city.name};
    }
    const county = placeAt(cities.counties, lon, lat);
    if (county) {
      const v = seriesAt(year, cities.pop[`county:${county.name.replace(/ County$/, '')}`] ?? cities.pop[`county:${county.name}`]);
      if (v != null) return {value: v, label: county.name === 'Manhattan' && year < ENGLISH ? 'New Amsterdam' : county.name};
    }
  }
  // Before the first census of the whole area (1698) there is no count of it: the counter
  // shows the Lenape estimate until the Dutch settle (1626), then the town on Manhattan.
  if (year < FIRST_CENSUS) {
    const town = seriesAt(year, cities.pop['county:Manhattan']);
    if (town != null) return {value: town, label: year < ENGLISH ? 'New Amsterdam' : 'New York'};
    const first = cities.region[0];
    if (first) return {value: first[1], label: 'Lenape around the harbour (estimate)'};
  }
  const v = seriesAt(year, cities.region);
  if (v != null) return {value: v, label: cities.region_label};
  return populationLabelAt(year);
}
