/**
 * Story mode: a guided tour of the map. data/tables/story.csv lists the stops in order
 * (year, camera, seconds, title, text); the tour flies from stop to stop, eases the year
 * slider to the stop's year, shows the caption and turns the camera slowly while it stands.
 * A stop with `year_to` lets the years run while it is on screen. Touching the map, the
 * slider or the play button pauses the tour; it resumes at the stop it was on.
 * `?story` (or `?story=12`) in the address starts it at load.
 */
import type {Map as MlMap} from 'maplibre-gl';
import {parseCsv} from './data/tables';

const files = import.meta.glob('../../data/tables/story.csv', {query: '?raw', import: 'default', eager: true}) as Record<string, string>;

type Stop = {
  year: number;
  yearTo: number | null;
  lon: number;
  lat: number;
  zoom: number;
  pitch: number;
  bearing: number;
  seconds: number;
  title: string;
  text: string;
  url: string;
};

const num = (v: string | undefined, d: number) => (v !== undefined && v !== '' && Number.isFinite(+v) ? +v : d);

const stops: Stop[] = Object.values(files)
  .flatMap(t => parseCsv(t))
  .map(r => ({
    year: num(r.year, NaN),
    yearTo: r.year_to ? num(r.year_to, NaN) : null,
    lon: num(r.lon, NaN),
    lat: num(r.lat, NaN),
    zoom: num(r.zoom, 14.5),
    pitch: num(r.pitch, 58),
    bearing: num(r.bearing, 29),
    seconds: Math.max(4, num(r.seconds, 14)),
    title: r.title ?? '',
    text: r.text ?? '',
    url: r.source_url ?? ''
  }))
  .filter(s => Number.isFinite(s.year) && Number.isFinite(s.lon) && Number.isFinite(s.lat) && s.title);

export type StoryHost = {getYear: () => number; setYear: (y: number) => void; onStart: () => void};
export type Story = {active: () => boolean; pause: () => void; toggle: () => void; exit: () => void; step: (d: number) => void};

const esc = (s: string) => s.replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'})[c]!);
const clock = (s: number) => `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, '0')}`;

export function initStory(map: MlMap, host: StoryHost, yearMin: number, yearMax: number): Story {
  const btn = document.getElementById('story') as HTMLButtonElement | null;
  const panel = document.getElementById('story-panel');
  const none: Story = {active: () => false, pause() {}, toggle() {}, exit() {}, step() {}};
  if (!btn || !panel) return none;
  if (!stops.length) {
    btn.hidden = true;
    return none;
  }
  panel.innerHTML =
    '<div class="story-head"><span class="story-year"></span><span class="story-title"></span>' +
    '<button class="story-x" aria-label="End the tour" title="End the tour">✕</button></div>' +
    '<div class="story-text"></div>' +
    '<div class="story-bar"><div class="story-fill"></div></div>' +
    '<div class="story-ctl"><button class="story-prev" aria-label="Previous stop" title="Previous stop">⏮</button>' +
    '<button class="story-pp" aria-label="Pause the tour" title="Pause">❚❚</button>' +
    '<button class="story-next" aria-label="Next stop" title="Next stop">⏭</button>' +
    '<button class="story-say" aria-pressed="false" aria-label="Read the captions aloud" title="Read aloud">🔈</button>' +
    '<span class="story-count"></span><a class="story-src" target="_blank" rel="noopener">source</a></div>';
  const q = <T extends HTMLElement>(c: string) => panel.querySelector(c) as T;
  const elYear = q('.story-year');
  const elTitle = q('.story-title');
  const elText = q('.story-text');
  const elFill = q('.story-fill');
  const elCount = q('.story-count');
  const elSrc = q<HTMLAnchorElement>('.story-src');
  const elPP = q<HTMLButtonElement>('.story-pp');
  const elSay = q<HTMLButtonElement>('.story-say');

  const FLY_MIN = 2600;
  let on = false;
  let paused = false;
  let idx = 0;
  let phase: 'fly' | 'dwell' = 'fly';
  let t0 = 0;
  let flyMs = FLY_MIN;
  let fromYear = 0;
  let raf = 0;
  let say = false;
  let spoken = true;
  const speech = 'speechSynthesis' in window ? window.speechSynthesis : null;
  if (!speech) elSay.hidden = true;
  const clampYear = (y: number) => Math.max(yearMin, Math.min(yearMax, y));

  function remaining(): number {
    let s = 0;
    for (let i = idx; i < stops.length; i++) s += stops[i].seconds + 4;
    return s;
  }

  function show(s: Stop) {
    elYear.textContent = String(Math.floor(s.year));
    elTitle.textContent = s.title;
    elText.innerHTML = esc(s.text);
    elCount.textContent = `${idx + 1} / ${stops.length} · ${clock(remaining())} left`;
    elSrc.hidden = !s.url;
    if (s.url) elSrc.href = s.url;
    elFill.style.width = '0%';
  }

  function speak(s: Stop) {
    if (!speech) return;
    speech.cancel();
    spoken = true;
    if (!say) return;
    const u = new SpeechSynthesisUtterance(`${s.title}. ${s.text}`);
    u.rate = 1;
    spoken = false;
    u.onend = u.onerror = () => (spoken = true);
    speech.speak(u);
  }

  function goTo(i: number) {
    idx = Math.max(0, Math.min(stops.length - 1, i));
    const s = stops[idx];
    const c = map.getCenter();
    const km = Math.hypot((c.lng - s.lon) * 84.4, (c.lat - s.lat) * 110.6);
    flyMs = Math.min(7500, FLY_MIN + km * 380);
    fromYear = host.getYear();
    phase = 'fly';
    t0 = performance.now();
    paused = false;
    elPP.textContent = '❚❚';
    elPP.setAttribute('aria-label', 'Pause the tour');
    show(s);
    speak(s);
    map.flyTo({center: [s.lon, s.lat], zoom: s.zoom, pitch: s.pitch, bearing: s.bearing, duration: flyMs, essential: true});
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(frame);
  }

  function frame(t: number) {
    if (!on || paused) return;
    const s = stops[idx];
    const el = t - t0;
    if (phase === 'fly') {
      const k = Math.min(1, el / flyMs);
      const e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
      host.setYear(clampYear(fromYear + (s.year - fromYear) * e));
      if (k >= 1) {
        phase = 'dwell';
        t0 = t;
        // a slow turn while the caption stands
        map.easeTo({bearing: s.bearing + 10, duration: s.seconds * 1000, easing: x => x, essential: true});
      }
    } else {
      const k = Math.min(1, el / (s.seconds * 1000));
      if (s.yearTo != null && Number.isFinite(s.yearTo)) host.setYear(clampYear(s.year + (s.yearTo - s.year) * k));
      elFill.style.width = `${(k * 100).toFixed(1)}%`;
      // (read aloud: wait for the voice, at most 20 s over)
      if (k >= 1 && (spoken || el > s.seconds * 1000 + 20000)) {
        if (idx + 1 < stops.length) goTo(idx + 1);
        else pause();
        return;
      }
    }
    raf = requestAnimationFrame(frame);
  }

  function pause() {
    if (!on || paused) return;
    paused = true;
    cancelAnimationFrame(raf);
    map.stop();
    speech?.cancel();
    elPP.textContent = '▶';
    elPP.setAttribute('aria-label', 'Resume the tour');
  }

  function start(i = idx) {
    host.onStart();
    on = true;
    panel!.hidden = false;
    btn!.classList.add('on');
    btn!.setAttribute('aria-pressed', 'true');
    goTo(i);
  }

  function exit() {
    if (!on) return;
    on = false;
    paused = false;
    cancelAnimationFrame(raf);
    map.stop();
    speech?.cancel();
    panel!.hidden = true;
    btn!.classList.remove('on');
    btn!.setAttribute('aria-pressed', 'false');
  }

  const toggle = () => (paused ? goTo(idx) : pause());
  const step = (d: number) => on && goTo(idx + d);
  btn.addEventListener('click', () => (on ? exit() : start(idx >= stops.length - 1 ? 0 : idx)));
  q('.story-x').addEventListener('click', exit);
  q('.story-prev').addEventListener('click', () => step(-1));
  q('.story-next').addEventListener('click', () => step(1));
  elPP.addEventListener('click', toggle);
  elSay.addEventListener('click', () => {
    say = !say;
    elSay.textContent = say ? '🔊' : '🔈';
    elSay.setAttribute('aria-pressed', String(say));
    if (!say) {
      speech?.cancel();
      spoken = true;
    } else if (on && !paused) speak(stops[idx]);
  });
  // taking the map in hand pauses the tour
  const cc = map.getCanvasContainer();
  for (const ev of ['pointerdown', 'wheel', 'touchstart'] as const) cc.addEventListener(ev, pause, {passive: true});

  const param = new URLSearchParams(location.search).get('story');
  if (param !== null) map.once('load', () => start(Math.max(0, (parseInt(param, 10) || 1) - 1)));
  return {active: () => on, pause, toggle, exit, step};
}
