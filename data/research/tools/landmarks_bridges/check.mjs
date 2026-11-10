// Numeric check of the bridge models against expect.json (cited spans, heights, real road ends).
import fs from 'node:fs';
const {BRIDGES, MeshBuilder, lngLatToLocal} = await import('./bridges_bundle.mjs');
const expect = JSON.parse(fs.readFileSync(new URL('./expect.json', import.meta.url)));
const only = process.argv.slice(2);
const ids = new Set();
let total = 0;
for (const lm of BRIDGES) {
  if (ids.has(lm.id)) console.log('DUPLICATE ID', lm.id);
  ids.add(lm.id);
  const b = new MeshBuilder();
  lm.build(b);
  const pos = b.build().positions.value;
  const n = pos.length / 3;
  total += n;
  if (only.length && !only.some(o => lm.id.includes(o))) continue;
  let zmax = -1e9, zmin = 1e9, bad = 0;
  for (let i = 0; i < n; i++) { const z = pos[i*3+2]; if (!Number.isFinite(z) || !Number.isFinite(pos[i*3]) || !Number.isFinite(pos[i*3+1])) bad++; if (z > zmax) zmax = z; if (z < zmin) zmin = z; }
  const e = expect[lm.id] || {};
  const out = [`${lm.id}: ${n} verts, built ${lm.built} end ${lm.end}, z ${zmin.toFixed(1)}..${zmax.toFixed(1)}${bad ? ' NaN:' + bad : ''}`];
  if (e.top) out.push(`  top: model ${zmax.toFixed(1)} vs cited ${e.top} (${(100*(zmax-e.top)/e.top).toFixed(1)} %)`);
  if (e.span) {
    // towers: clusters of the highest vertices (or of vertices above e.spanZ)
    const zt = e.spanZ ?? zmax - 1.0;
    const pts = [];
    for (let i = 0; i < n; i++) if (e.spanBand ? (pos[i*3+2] >= e.spanBand[0] && pos[i*3+2] <= e.spanBand[1]) : pos[i*3+2] >= zt) pts.push([pos[i*3], pos[i*3+1]]);
    // split along the principal direction (farthest pair heuristic)
    let A = pts[0], B = pts[0], dmax = 0;
    for (const p of pts) { const d = Math.hypot(p[0]-pts[0][0], p[1]-pts[0][1]); if (d > dmax) { dmax = d; A = p; } }
    dmax = 0; for (const p of pts) { const d = Math.hypot(p[0]-A[0], p[1]-A[1]); if (d > dmax) { dmax = d; B = p; } }
    const ca = [0,0,0], cb = [0,0,0];
    for (const p of pts) { const da = Math.hypot(p[0]-A[0], p[1]-A[1]), db = Math.hypot(p[0]-B[0], p[1]-B[1]); const c = da < db ? ca : cb; c[0]+=p[0]; c[1]+=p[1]; c[2]++; }
    const d = Math.hypot(ca[0]/ca[2]-cb[0]/cb[2], ca[1]/ca[2]-cb[1]/cb[2]);
    out.push(`  span: model ${d.toFixed(1)} vs cited ${e.span} (${(100*(d-e.span)/e.span).toFixed(2)} %)`);
  }
  if (e.clear !== undefined) {
    // lowest surface above the water on the vertical through the anchor (or clearAt)
    const [cx, cy] = e.clearAt ? lngLatToLocal(lm.anchor, e.clearAt) : [0.37, 0.41];
    let lo = 1e9;
    for (let t = 0; t < n; t += 3) {
      const mx = (pos[t*3] + pos[t*3+3] + pos[t*3+6]) / 3 - cx, my = (pos[t*3+1] + pos[t*3+4] + pos[t*3+7]) / 3 - cy;
      if (Math.hypot(mx, my) > (e.clearR ?? 16)) continue;
      for (const k of [2, 5, 8]) { const z = pos[t*3+k]; if (z > 1 && z < lo) lo = z; }
    }
    out.push(`  clearance: model ${lo.toFixed(1)} vs cited ${e.clear}`);
  }
  for (const [k, p] of Object.entries(e.ends || {})) {
    const [ex, ey] = lngLatToLocal(lm.anchor, p);
    const L = Math.hypot(ex, ey); let smax = -1e9;
    const lat = e.lat ?? 40;
    for (let i = 0; i < n; i++) { const s = (pos[i*3]*ex + pos[i*3+1]*ey) / L; const off = Math.abs(pos[i*3]*ey - pos[i*3+1]*ex) / L; if (off < lat && s > smax) smax = s; }
    let zt = -1e9, off = 0, m = 0;
    for (let i = 0; i < n; i++) { const s = (pos[i*3]*ex + pos[i*3+1]*ey) / L; const o = (pos[i*3]*ey - pos[i*3+1]*ex) / L; if (Math.abs(o) < lat && s > smax - 2) { zt = Math.max(zt, pos[i*3+2]); off += o; m++; } }
    out.push(`  end ${k}: model reaches ${(smax - L).toFixed(1)} m past the real end (lateral ${(off/m).toFixed(1)} m), deck z ${zt.toFixed(1)}${p[2] !== undefined ? ' vs ground ' + p[2] : ''}`);
  }
  console.log(out.join('\n'));
}
console.log('TOTAL', BRIDGES.length, 'models,', total, 'vertices');
