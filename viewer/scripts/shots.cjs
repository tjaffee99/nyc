// Small screenshots of the map, taken through the DevTools protocol (page.screenshot waits
// for an idle page and never returns under software rendering). The sets that make a frame
// slow are not loaded: street and canopy trees, the street tiles, traffic. Add BLOCK=<regexp>
// to leave out more (BLOCK='core-buildings' when the view is not Manhattan's).
// usage: node scripts/shots.cjs <url> <out prefix> "<year=..&c=lon,lat&z=..&p=..&b=..>" [more views]
const {chromium} = require('playwright');
const fs = require('fs');
(async () => {
  const [base, out, ...views] = process.argv.slice(2);
  const browser = await chromium.launch({args: ['--enable-unsafe-swiftshader', '--use-angle=swiftshader', '--ignore-gpu-blocklist']});
  const page = await browser.newPage({viewport: {width: +(process.env.W || 760), height: +(process.env.H || 480)}, deviceScaleFactor: 1});
  // STREETS=1 loads the street tiles too (slower)
  const heavy = new RegExp('region-trees|street-trees|traffic' + (process.env.STREETS ? '' : '|region-streets|outer-streets') + (process.env.BLOCK ? '|' + process.env.BLOCK : ''));
  await page.route('**/*', r => (heavy.test(r.request().url()) ? r.abort() : r.continue()));
  const q0 = Object.fromEntries(views[0].split('&').map(kv => kv.split('=')));
  await page.goto(`${base}#${views[0]}`, {waitUntil: 'load'});
  try { await page.waitForFunction(() => window.__ready === true, null, {timeout: 90000}); } catch (e) { /* a blocked file keeps the loading note up */ }
  await page.addStyleTag({content: '#loading{display:none !important}'});
  const cdp = await page.context().newCDPSession(page);
  for (let i = 0; i < views.length; i++) {
    const q = Object.fromEntries(views[i].split('&').map(kv => kv.split('=')));
    const [lon, lat] = q.c.split(',').map(Number);
    await page.evaluate(({lon, lat, z, p, b, y}) => { window.__map.jumpTo({center: [lon, lat], zoom: z, pitch: p, bearing: b}); window.__setYear(y); }, {lon, lat, z: +q.z, p: +q.p, b: +q.b, y: +q.year});
    await page.waitForTimeout(+(process.env.WAIT || 22000));
    const {data} = await cdp.send('Page.captureScreenshot', {format: 'png'});
    fs.writeFileSync(`${out}_${i}.png`, Buffer.from(data, 'base64'));
    console.log('shot', i, views[i]);
  }
  await browser.close();
})();
