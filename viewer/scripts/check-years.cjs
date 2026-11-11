// Headless check across years and views (software GL: slow, no screenshots): the page
// boots, the counters read sensibly, and nothing but missing optional files is logged.
// usage: cd viewer && node scripts/check-years.cjs http://localhost:5173/   (or the live URL)
const {chromium} = require('playwright');
const VIEWS = [
  ['1609 harbour', 'year=1609&c=-74.01,40.71&z=12.2&p=45&b=29'],
  ['1660 New Amsterdam', 'year=1660&c=-74.0125,40.7045&z=15.2&p=55&b=29'],
  ['1776 lower Manhattan', 'year=1776&c=-74.009,40.709&z=14.2&p=55&b=29'],
  ['1855 downtown', 'year=1855&c=-74.004,40.715&z=14&p=55&b=29'],
  ['1931 Midtown', 'year=1931&c=-73.9857,40.7484&z=13.6&p=60&b=29'],
  ['1975 WTC', 'year=1975&c=-74.0125,40.7115&z=14.5&p=60&b=29'],
  ['2026 Brooklyn', 'year=2026&c=-73.975,40.69&z=13.2&p=50&b=10'],
  ['2026 city', 'year=2026&c=-73.95,40.72&z=10.2&p=30&b=0'],
  ['1900 Jersey City', 'year=1900&c=-74.045,40.722&z=13.6&p=55&b=20'],
  ['1960 Yonkers', 'year=1960&c=-73.88,40.94&z=13.2&p=50&b=0'],
  ['2026 region', 'year=2026&c=-74.0,40.9&z=9.2&p=20&b=0'],
  // years at which the effects layer is on (a battle's columns, a fire)
  ['1776 battle', 'year=1776.655&c=-73.985,40.665&z=12.6&p=50&b=0'],
  ['1835 fire', 'year=1835.97&c=-74.009,40.705&z=15&p=55&b=29'],
  ['2001 towers', 'year=2001.70&c=-74.0125,40.7115&z=14.5&p=60&b=29'],
  // the outer counties (the compact tier)
  ['2026 New Haven', 'year=2026&c=-72.927,41.308&z=13.4&p=50&b=0'],
  ['1900 Trenton', 'year=1900&c=-74.765,40.22&z=13.2&p=50&b=0'],
  ['1960 Levittown', 'year=1960&c=-73.515,40.725&z=13.2&p=45&b=0'],
  ['2026 Poughkeepsie', 'year=2026&c=-73.93,41.705&z=12.6&p=50&b=0'],
  ['2026 whole map', 'year=2026&c=-73.7,40.9&z=7.6&p=0&b=0'],
];
(async () => {
  const base = process.argv[2];
  const browser = await chromium.launch({args: ['--enable-unsafe-swiftshader', '--use-angle=swiftshader', '--ignore-gpu-blocklist']});
  const page = await browser.newPage({viewport: {width: 800, height: 520}, deviceScaleFactor: 1});
  const msgs = [];
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') msgs.push(`${m.type()}: ${m.text().slice(0, 200)}`); });
  page.on('pageerror', e => msgs.push(`pageerror: ${e.message.slice(0, 300)}`));
  // (counted from the responses: the browser's resource log keeps only its first 250 entries)
  const got = {regionBuildingTiles: 0, countyBuildingTiles: 0, outerBuildingTiles: 0, terrain13: 0, fromRawHost: 0, failed: 0};
  page.on('response', r => {
    const u = r.url();
    const hit = /region-buildings\/1[13]\//.test(u) ? 'regionBuildingTiles' : /county-buildings\/1[13]\//.test(u) ? 'countyBuildingTiles'
      : /outer-buildings\/\d+\//.test(u) ? 'outerBuildingTiles'
      : /tiles\/terrain\/13\//.test(u) ? 'terrain13' : null;
    if (/raw\.githubusercontent\.com/.test(u)) got.fromRawHost++;
    if (hit) { if (r.ok()) got[hit]++; else got.failed++; }
  });
  await page.goto(`${base}#${VIEWS[0][1]}`, {waitUntil: 'load'});
  let ready = true;
  try { await page.waitForFunction(() => window.__ready === true, null, {timeout: 240000}); } catch (e) { ready = false; }
  console.log(`ready=${ready}`);
  for (const [name, hash] of VIEWS) {
    const q = Object.fromEntries(hash.split('&').map(kv => kv.split('=')));
    const [lon, lat] = q.c.split(',').map(Number);
    await page.evaluate(({lon, lat, z, p, b, y}) => { window.__map.jumpTo({center: [lon, lat], zoom: z, pitch: p, bearing: b}); window.__setYear(y); },
      {lon, lat, z: +q.z, p: +q.p, b: +q.b, y: +q.year});
    await page.waitForTimeout(7000);
    const info = await page.evaluate(() => ({year: document.getElementById('year-label').textContent, pop: document.getElementById('population-value').textContent,
      area: document.getElementById('population-area').textContent, layers: (window.__overlay._deck?.layerManager?.getLayers() || []).length}));
    console.log(`${name}: ${JSON.stringify(info)}`);
  }
  // story mode: starts, shows a caption, steps on, ends
  const story = await page.evaluate(async () => {
    const wait = ms => new Promise(r => setTimeout(r, ms));
    const btn = document.getElementById('story');
    const panel = document.getElementById('story-panel');
    if (!btn || btn.hidden) return {present: false};
    btn.click();
    await wait(9000);
    const read = () => ({shown: !panel.hidden, year: panel.querySelector('.story-year')?.textContent, title: panel.querySelector('.story-title')?.textContent,
      text: (panel.querySelector('.story-text')?.textContent || '').length, count: panel.querySelector('.story-count')?.textContent,
      slider: document.getElementById('year-label').textContent});
    const first = read();
    panel.querySelector('.story-next').click();
    await wait(9000);
    const second = read();
    panel.querySelector('.story-pp').click();
    await wait(300);
    const paused = panel.querySelector('.story-pp').textContent;
    panel.querySelector('.story-x').click();
    await wait(300);
    return {present: true, first, second, paused, closed: panel.hidden};
  });
  console.log(`story: ${JSON.stringify(story)}`);
  // the heavy tile sets: read from the page's own origin locally, from the branch on the published site
  console.log(`heavy tiles fetched: ${JSON.stringify(got)}`);
  const uniq = [...new Set(msgs)].filter(m => !/404|503|bad magic|Failed to load resource/.test(m));
  console.log(`${uniq.length} messages other than missing optional files`);
  for (const m of uniq.slice(0, 25)) console.log('  ' + m);
  await browser.close();
})();
