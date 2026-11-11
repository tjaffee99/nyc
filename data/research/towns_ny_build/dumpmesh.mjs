import {build} from '/home/user/nyc/viewer/node_modules/esbuild/lib/main.js';
import {writeFileSync} from 'node:fs';
const dir='/home/user/nyc/data/research/towns_ny_build';
const out = '/tmp/claude-0/-home-user-nyc/f18fa0a8-84a0-5e93-b4be-330efeee9c33/scratchpad/_bundle_ny.mjs';
await build({stdin: {contents: "export {NY_TOWNS} from './ny-towns'; export {MeshBuilder} from './kit';", resolveDir: '/home/user/nyc/viewer/src/landmarks', loader: 'ts'}, bundle: true, format: 'esm', outfile: out, logLevel: 'error'});
const {NY_TOWNS, MeshBuilder} = await import(out + '?t=' + Date.now());
const res = NY_TOWNS.map(lm => {
  const b = new MeshBuilder(); lm.build(b); const m = b.build(); const p = m.positions.value;
  let bad = 0; for (const v of p) if (!Number.isFinite(v)) bad++;
  return {id: lm.id, anchor: lm.anchor, built: lm.built, end: lm.end, replaces: lm.replaces ?? [], nverts: p.length / 3, bad, pos: Array.from(p, v => Math.round(v * 100) / 100)};
});
writeFileSync(dir+'/meshes.json', JSON.stringify(res));
console.log(res.length, 'landmarks', res.map(r => r.id + ':' + r.nverts / 3 + 'f' + (r.bad?' BAD':'')).join(' '));
