
import fs from 'node:fs';
const {BRIDGES, MeshBuilder, localToLngLat} = await import('./bridges_bundle.mjs');
const out = BRIDGES.map(lm => { const b = new MeshBuilder(); lm.build(b); const pos = b.build().positions.value; let zmax = -1e9; for (let i = 2; i < pos.length; i += 3) if (pos[i] > zmax) zmax = pos[i];
  return {id: lm.id, name: lm.name, kind: lm.kind, built: lm.built, end: lm.end, anchor: lm.anchor, zmax, verts: pos.length / 3, facts: lm.facts, sources: lm.sources, replaces: (lm.replaces || []).map(poly => poly.map(q => localToLngLat(lm.anchor, q)))}; });
fs.writeFileSync(new URL('./bridges_dump.json', import.meta.url), JSON.stringify(out, null, 1));
console.log('dumped', out.length);
