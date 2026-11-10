import {MeshBuilder} from '/home/user/nyc/viewer/src/landmarks/kit';
import * as L from '/home/user/nyc/viewer/src/landmarks/nyc-lost';
type V2 = [number, number];
const mods: any = L;
const all: any[] = mods.LOST ?? Object.keys(mods).filter(k => Array.isArray(mods[k])).flatMap(k => mods[k]);
const area = (r: V2[]) => Math.abs(r.reduce((a, p, i) => a + p[0] * r[(i + 1) % r.length][1] - r[(i + 1) % r.length][0] * p[1], 0)) / 2;
const inside = (x: number, y: number, r: V2[]) => { let c = false; for (let i = 0, j = r.length - 1; i < r.length; j = i++) { const [xi, yi] = r[i], [xj, yj] = r[j]; if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c; } return c; };
const dseg = (x: number, y: number, a: V2, b: V2) => { const dx = b[0] - a[0], dy = b[1] - a[1]; const t = Math.max(0, Math.min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / (dx * dx + dy * dy || 1))); return Math.hypot(x - a[0] - t * dx, y - a[1] - t * dy); };
const only = process.argv[2];
const ids = new Set<string>();
for (const lm of all) {
  if (ids.has(lm.id)) console.log('DUPLICATE ID', lm.id); ids.add(lm.id);
  if (only && !lm.id.includes(only)) continue;
  const b = new MeshBuilder(); lm.build(b); const m = b.build(); const p = m.positions.value; const n = p.length / 3;
  let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9, z0 = 1e9, z1 = -1e9, bad = 0, out = 0, dmax = 0;
  const reps: V2[][] = lm.replaces ?? [];
  for (let i = 0; i < n; i++) {
    const x = p[i * 3], y = p[i * 3 + 1], z = p[i * 3 + 2];
    if (!isFinite(x) || !isFinite(y) || !isFinite(z)) { bad++; continue; }
    x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); z0 = Math.min(z0, z); z1 = Math.max(z1, z);
    if (reps.length && !reps.some(r => inside(x, y, r))) { let d = 1e9; for (const r of reps) for (let k = 0; k < r.length; k++) d = Math.min(d, dseg(x, y, r[k], r[(k + 1) % r.length])); if (d > 1.0) out++; dmax = Math.max(dmax, d); }
  }
  const f = (v: number) => v.toFixed(1);
  console.log(`${lm.id.padEnd(34)} ${lm.kind.padEnd(8)} ${lm.built[0]}-${lm.built[1]} end ${lm.end} | verts ${String(n).padStart(6)} | x ${f(x0)}..${f(x1)} y ${f(y0)}..${f(y1)} | z ${f(z0)}..${f(z1)} | site ${reps.map(r => area(r).toFixed(0)).join('+') || '-'} m2 | outside>1m ${out} (max ${f(dmax)} m)${bad ? ' NaN ' + bad : ''}${lm.built[0] >= lm.built[1] || lm.built[1] > lm.end ? ' BAD DATES' : ''}${Object.keys(lm.facts).length < 3 ? ' FEW FACTS' : ''}`);
}
console.log('landmarks', all.length);
