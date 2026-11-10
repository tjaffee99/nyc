import {MeshBuilder} from '/home/user/nyc/viewer/src/landmarks/kit';
import {LOST} from '/home/user/nyc/viewer/src/landmarks/nyc-lost';
import {writeFileSync} from 'fs';
const out: any = {};
for (const lm of LOST) {
  const b = new MeshBuilder(); lm.build(b); const m = b.build();
  out[lm.id] = {name: lm.name, kind: lm.kind, built: lm.built, end: lm.end, anchor: lm.anchor, facts: lm.facts, sources: lm.sources, replaces: lm.replaces ?? [],
    pos: Array.from(m.positions.value).map(v => Math.round(v * 100) / 100), col: Array.from(m.colors.value).map(v => Math.round(v * 255))};
}
writeFileSync('/home/user/nyc/data/interim/landmarks_lost/meshes.json', JSON.stringify(out));
console.log('dumped', Object.keys(out).length);
