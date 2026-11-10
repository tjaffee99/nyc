// Scratch: bundle nyc-civic.ts with esbuild, build every landmark mesh, write meshes.json
import {build} from '/home/user/nyc/viewer/node_modules/esbuild/lib/main.js';
import {writeFileSync} from 'node:fs';
const out = '/home/user/nyc/data/interim/landmarks_civic/_bundle.mjs';
await build({stdin: {contents: "export {CIVIC} from './nyc-civic'; export {MeshBuilder} from './kit';", resolveDir: '/home/user/nyc/viewer/src/landmarks', loader: 'ts'}, bundle: true, format: 'esm', outfile: out, logLevel: 'error'});
const {CIVIC, MeshBuilder} = await import(out + '?t=' + Date.now());
const res = CIVIC.map(lm => {
  const b = new MeshBuilder(); lm.build(b); const m = b.build(); const p = m.positions.value;
  let bad = 0; for (const v of p) if (!Number.isFinite(v)) bad++;
  return {id: lm.id, name: lm.name, kind: lm.kind, built: lm.built, end: lm.end, anchor: lm.anchor, replaces: lm.replaces ?? [], nverts: p.length / 3, bad, pos: Array.from(p, v => Math.round(v * 100) / 100), facts: lm.facts, sources: lm.sources};
});
writeFileSync('/home/user/nyc/data/interim/landmarks_civic/meshes.json', JSON.stringify(res));
console.log(res.length, 'landmarks', res.reduce((a, r) => a + r.nverts, 0), 'vertices');
