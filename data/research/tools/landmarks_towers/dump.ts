import {writeFileSync} from 'node:fs';
import {MeshBuilder} from '../../../viewer/src/landmarks/kit';
import {TOWERS} from '../../../viewer/src/landmarks/nyc-towers';

const only = process.argv.slice(2);
const out: any[] = [];
for (const lm of TOWERS) {
  if (only.length && !only.some(o => lm.id.includes(o))) continue;
  const b = new MeshBuilder();
  lm.build(b);
  const m = b.build();
  out.push({id: lm.id, name: lm.name, kind: lm.kind, facts: lm.facts, sources: lm.sources, built: lm.built, end: lm.end, anchor: lm.anchor, replaces: lm.replaces ?? [], pos: Array.from(m.positions.value).map(v => Math.round(v * 100) / 100), col: Array.from(m.colors.value).map(v => Math.round(v * 255))});
}
writeFileSync(new URL('./mesh.json', import.meta.url), JSON.stringify(out));
console.log(out.map(o => `${o.id}:${o.pos.length / 3}`).join(' '));
