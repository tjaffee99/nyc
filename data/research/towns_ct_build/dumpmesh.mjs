import {build} from '/home/user/nyc/viewer/node_modules/esbuild/lib/main.js';
import {writeFileSync} from 'node:fs';
const dir='/home/user/nyc/data/research/towns_ct_build';
const out = dir+'/_bundle.mjs';
await build({stdin: {contents: "export {CT_TOWNS} from './ct-towns'; export {MeshBuilder} from './kit';", resolveDir: '/home/user/nyc/viewer/src/landmarks', loader: 'ts'}, bundle: true, format: 'esm', outfile: out, logLevel: 'error'});
const {CT_TOWNS, MeshBuilder} = await import(out + '?t=' + Date.now());
const res = CT_TOWNS.map(lm => {
  const b = new MeshBuilder(); lm.build(b); const m = b.build(); const p = m.positions.value;
  let bad = 0; for (const v of p) if (!Number.isFinite(v)) bad++;
  return {id: lm.id, anchor: lm.anchor, built: lm.built, end: lm.end, replaces: lm.replaces ?? [], nverts: p.length / 3, bad, pos: Array.from(p, v => Math.round(v * 100) / 100)};
});
writeFileSync(dir+'/meshes.json', JSON.stringify(res));
console.log(res.length, 'landmarks', res.map(r => r.id + ':' + r.nverts / 3 + 'f' + (r.bad?' BAD':'')).join(' '));
