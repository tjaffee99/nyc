// ASCII elevations of a model: side view (along the main axis vs z) and front view (across vs z) in a window.
const {BRIDGES, MeshBuilder} = await import('./bridges_bundle.mjs');
const [id, brgS, a0S, a1S, colsS, mode, c0S, c1S] = process.argv.slice(2);
const lm = BRIDGES.find(l => l.id === id);
const b = new MeshBuilder(); lm.build(b); const pos = b.build().positions.value; const n = pos.length / 3;
const brg = Number(brgS) * Math.PI / 180; const ux = Math.sin(brg), uy = Math.cos(brg);
const a0 = Number(a0S), a1 = Number(a1S), cols = Number(colsS);
const front = mode === 'front'; const c0 = Number(c0S ?? -40), c1 = Number(c1S ?? 40);
let zmax = 0; for (let i = 2; i < pos.length; i += 3) zmax = Math.max(zmax, pos[i]);
const h0 = front ? c0 : a0, h1 = front ? c1 : a1;
const sx = (h1 - h0) / cols; const sz = sx * 2.0; const rows = Math.ceil((zmax + 4) / sz);
const grid = Array.from({length: rows}, () => new Array(cols).fill(0));
const P = i => { const x = pos[i*3], y = pos[i*3+1]; return [x*ux + y*uy, x*uy - y*ux, pos[i*3+2]]; };
for (let t = 0; t < n; t += 3) {
  const A = P(t), B = P(t+1), C = P(t+2);
  if (front) { if (A[0] < a0 || A[0] > a1) continue; } 
  const q = v => front ? [v[1], v[2]] : [v[0], v[2]];
  const [p, r, s] = [q(A), q(B), q(C)];
  // sample the triangle
  const m = 16;
  for (let i = 0; i <= m; i++) for (let j = 0; j <= m - i; j++) {
    const u = i / m, v = j / m, w = 1 - u - v;
    const hx = p[0]*u + r[0]*v + s[0]*w, hz = p[1]*u + r[1]*v + s[1]*w;
    const cx = Math.floor((hx - h0) / sx), cz = Math.floor(hz / sz);
    if (cx >= 0 && cx < cols && cz >= 0 && cz < rows) grid[cz][cx]++;
  }
}
console.log(`${id} ${front ? 'front' : 'side'} view, ${sx.toFixed(1)} m per column, ${sz.toFixed(1)} m per row`);
for (let r = rows - 1; r >= 0; r--) console.log(grid[r].map(v => v === 0 ? ' ' : v < 12 ? "." : v < 120 ? "+" : "#").join('').replace(/\s+$/, ''));
