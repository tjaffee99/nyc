const {BRIDGES, MeshBuilder} = await import('./bridges_bundle.mjs');
for (const lm of BRIDGES) {
  const b = new MeshBuilder(); lm.build(b); const pos = b.build().positions.value; const n = pos.length / 3;
  let mx = 0, my = 0; for (let i = 0; i < n; i++) { mx += pos[i*3]; my += pos[i*3+1]; } mx /= n; my /= n;
  let sxx = 0, sxy = 0, syy = 0; for (let i = 0; i < n; i++) { const x = pos[i*3]-mx, y = pos[i*3+1]-my; sxx += x*x; sxy += x*y; syy += y*y; }
  const th = 0.5 * Math.atan2(2*sxy, sxx - syy); const c = Math.cos(th), s = Math.sin(th);
  let a0 = 1e9, a1 = -1e9, c0 = 1e9, c1 = -1e9;
  for (let i = 0; i < n; i++) { const x = pos[i*3]-mx, y = pos[i*3+1]-my; const al = x*c + y*s, ac = -x*s + y*c; if (al < a0) a0 = al; if (al > a1) a1 = al; if (ac < c0) c0 = ac; if (ac > c1) c1 = ac; }
  console.log(lm.id.padEnd(32), 'length', (a1-a0).toFixed(0).padStart(5), 'width', (c1-c0).toFixed(0).padStart(4), 'axis bearing', (((90 - th*180/Math.PI) % 180 + 180) % 180).toFixed(1));
}
