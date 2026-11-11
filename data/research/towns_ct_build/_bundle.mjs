// ../../../viewer/node_modules/@math.gl/polygon/dist/polygon-utils.js
var DimIndex = {
  x: 0,
  y: 1,
  z: 2
};
function getPolygonSignedArea(points, options = {}) {
  const { start = 0, end = points.length, plane = "xy" } = options;
  const dim = options.size || 2;
  let area2 = 0;
  const i0 = DimIndex[plane[0]];
  const i1 = DimIndex[plane[1]];
  for (let i = start, j = end - dim; i < end; i += dim) {
    area2 += (points[i + i0] - points[j + i0]) * (points[i + i1] + points[j + i1]);
    j = i;
  }
  return area2 / 2;
}

// ../../../viewer/node_modules/@math.gl/polygon/dist/earcut.js
function earcut(positions, holeIndices, dim = 2, areas, plane = "xy") {
  const hasHoles = holeIndices && holeIndices.length;
  const outerLen = hasHoles ? holeIndices[0] * dim : positions.length;
  let outerNode = linkedList(positions, 0, outerLen, dim, true, areas && areas[0], plane);
  const triangles = [];
  if (!outerNode || outerNode.next === outerNode.prev)
    return triangles;
  let invSize;
  let maxX;
  let maxY;
  let minX;
  let minY;
  let x;
  let y;
  if (hasHoles)
    outerNode = eliminateHoles(positions, holeIndices, outerNode, dim, areas, plane);
  if (positions.length > 80 * dim) {
    minX = maxX = positions[0];
    minY = maxY = positions[1];
    for (let i = dim; i < outerLen; i += dim) {
      x = positions[i];
      y = positions[i + 1];
      if (x < minX)
        minX = x;
      if (y < minY)
        minY = y;
      if (x > maxX)
        maxX = x;
      if (y > maxY)
        maxY = y;
    }
    invSize = Math.max(maxX - minX, maxY - minY);
    invSize = invSize !== 0 ? 32767 / invSize : 0;
  }
  earcutLinked(outerNode, triangles, dim, minX, minY, invSize, 0);
  return triangles;
}
function linkedList(data, start, end, dim, clockwise, area2, plane) {
  let i;
  let last;
  if (area2 === void 0) {
    area2 = getPolygonSignedArea(data, { start, end, size: dim, plane });
  }
  let i0 = DimIndex[plane[0]];
  let i1 = DimIndex[plane[1]];
  if (clockwise === area2 < 0) {
    for (i = start; i < end; i += dim)
      last = insertNode(i, data[i + i0], data[i + i1], last);
  } else {
    for (i = end - dim; i >= start; i -= dim)
      last = insertNode(i, data[i + i0], data[i + i1], last);
  }
  if (last && equals(last, last.next)) {
    removeNode(last);
    last = last.next;
  }
  return last;
}
function filterPoints(start, end) {
  if (!start)
    return start;
  if (!end)
    end = start;
  let p = start;
  let again;
  do {
    again = false;
    if (!p.steiner && (equals(p, p.next) || area(p.prev, p, p.next) === 0)) {
      removeNode(p);
      p = end = p.prev;
      if (p === p.next)
        break;
      again = true;
    } else {
      p = p.next;
    }
  } while (again || p !== end);
  return end;
}
function earcutLinked(ear, triangles, dim, minX, minY, invSize, pass) {
  if (!ear)
    return;
  if (!pass && invSize)
    indexCurve(ear, minX, minY, invSize);
  let stop = ear;
  let prev;
  let next;
  while (ear.prev !== ear.next) {
    prev = ear.prev;
    next = ear.next;
    if (invSize ? isEarHashed(ear, minX, minY, invSize) : isEar(ear)) {
      triangles.push(prev.i / dim | 0);
      triangles.push(ear.i / dim | 0);
      triangles.push(next.i / dim | 0);
      removeNode(ear);
      ear = next.next;
      stop = next.next;
      continue;
    }
    ear = next;
    if (ear === stop) {
      if (!pass) {
        earcutLinked(filterPoints(ear), triangles, dim, minX, minY, invSize, 1);
      } else if (pass === 1) {
        ear = cureLocalIntersections(filterPoints(ear), triangles, dim);
        earcutLinked(ear, triangles, dim, minX, minY, invSize, 2);
      } else if (pass === 2) {
        splitEarcut(ear, triangles, dim, minX, minY, invSize);
      }
      break;
    }
  }
}
function isEar(ear) {
  const a = ear.prev;
  const b = ear;
  const c = ear.next;
  if (area(a, b, c) >= 0)
    return false;
  const ax = a.x;
  const bx = b.x;
  const cx = c.x;
  const ay = a.y;
  const by = b.y;
  const cy = c.y;
  const x0 = ax < bx ? ax < cx ? ax : cx : bx < cx ? bx : cx;
  const y0 = ay < by ? ay < cy ? ay : cy : by < cy ? by : cy;
  const x1 = ax > bx ? ax > cx ? ax : cx : bx > cx ? bx : cx;
  const y1 = ay > by ? ay > cy ? ay : cy : by > cy ? by : cy;
  let p = c.next;
  while (p !== a) {
    if (p.x >= x0 && p.x <= x1 && p.y >= y0 && p.y <= y1 && pointInTriangle(ax, ay, bx, by, cx, cy, p.x, p.y) && area(p.prev, p, p.next) >= 0)
      return false;
    p = p.next;
  }
  return true;
}
function isEarHashed(ear, minX, minY, invSize) {
  const a = ear.prev;
  const b = ear;
  const c = ear.next;
  if (area(a, b, c) >= 0)
    return false;
  const ax = a.x;
  const bx = b.x;
  const cx = c.x;
  const ay = a.y;
  const by = b.y;
  const cy = c.y;
  const x0 = ax < bx ? ax < cx ? ax : cx : bx < cx ? bx : cx;
  const y0 = ay < by ? ay < cy ? ay : cy : by < cy ? by : cy;
  const x1 = ax > bx ? ax > cx ? ax : cx : bx > cx ? bx : cx;
  const y1 = ay > by ? ay > cy ? ay : cy : by > cy ? by : cy;
  const minZ = zOrder(x0, y0, minX, minY, invSize);
  const maxZ = zOrder(x1, y1, minX, minY, invSize);
  let p = ear.prevZ;
  let n = ear.nextZ;
  while (p && p.z >= minZ && n && n.z <= maxZ) {
    if (p.x >= x0 && p.x <= x1 && p.y >= y0 && p.y <= y1 && p !== a && p !== c && pointInTriangle(ax, ay, bx, by, cx, cy, p.x, p.y) && area(p.prev, p, p.next) >= 0)
      return false;
    p = p.prevZ;
    if (n.x >= x0 && n.x <= x1 && n.y >= y0 && n.y <= y1 && n !== a && n !== c && pointInTriangle(ax, ay, bx, by, cx, cy, n.x, n.y) && area(n.prev, n, n.next) >= 0)
      return false;
    n = n.nextZ;
  }
  while (p && p.z >= minZ) {
    if (p.x >= x0 && p.x <= x1 && p.y >= y0 && p.y <= y1 && p !== a && p !== c && pointInTriangle(ax, ay, bx, by, cx, cy, p.x, p.y) && area(p.prev, p, p.next) >= 0)
      return false;
    p = p.prevZ;
  }
  while (n && n.z <= maxZ) {
    if (n.x >= x0 && n.x <= x1 && n.y >= y0 && n.y <= y1 && n !== a && n !== c && pointInTriangle(ax, ay, bx, by, cx, cy, n.x, n.y) && area(n.prev, n, n.next) >= 0)
      return false;
    n = n.nextZ;
  }
  return true;
}
function cureLocalIntersections(start, triangles, dim) {
  let p = start;
  do {
    const a = p.prev;
    const b = p.next.next;
    if (!equals(a, b) && intersects(a, p, p.next, b) && locallyInside(a, b) && locallyInside(b, a)) {
      triangles.push(a.i / dim | 0);
      triangles.push(p.i / dim | 0);
      triangles.push(b.i / dim | 0);
      removeNode(p);
      removeNode(p.next);
      p = start = b;
    }
    p = p.next;
  } while (p !== start);
  return filterPoints(p);
}
function splitEarcut(start, triangles, dim, minX, minY, invSize) {
  let a = start;
  do {
    let b = a.next.next;
    while (b !== a.prev) {
      if (a.i !== b.i && isValidDiagonal(a, b)) {
        let c = splitPolygon(a, b);
        a = filterPoints(a, a.next);
        c = filterPoints(c, c.next);
        earcutLinked(a, triangles, dim, minX, minY, invSize, 0);
        earcutLinked(c, triangles, dim, minX, minY, invSize, 0);
        return;
      }
      b = b.next;
    }
    a = a.next;
  } while (a !== start);
}
function eliminateHoles(data, holeIndices, outerNode, dim, areas, plane) {
  const queue = [];
  let i;
  let len;
  let start;
  let end;
  let list;
  for (i = 0, len = holeIndices.length; i < len; i++) {
    start = holeIndices[i] * dim;
    end = i < len - 1 ? holeIndices[i + 1] * dim : data.length;
    list = linkedList(data, start, end, dim, false, areas && areas[i + 1], plane);
    if (list === list.next)
      list.steiner = true;
    queue.push(getLeftmost(list));
  }
  queue.sort(compareX);
  for (i = 0; i < queue.length; i++) {
    outerNode = eliminateHole(queue[i], outerNode);
  }
  return outerNode;
}
function compareX(a, b) {
  return a.x - b.x;
}
function eliminateHole(hole, outerNode) {
  const bridge = findHoleBridge(hole, outerNode);
  if (!bridge) {
    return outerNode;
  }
  const bridgeReverse = splitPolygon(bridge, hole);
  filterPoints(bridgeReverse, bridgeReverse.next);
  return filterPoints(bridge, bridge.next);
}
function findHoleBridge(hole, outerNode) {
  let p = outerNode;
  const hx = hole.x;
  const hy = hole.y;
  let qx = -Infinity;
  let m;
  do {
    if (hy <= p.y && hy >= p.next.y && p.next.y !== p.y) {
      const x = p.x + (hy - p.y) * (p.next.x - p.x) / (p.next.y - p.y);
      if (x <= hx && x > qx) {
        qx = x;
        m = p.x < p.next.x ? p : p.next;
        if (x === hx)
          return m;
      }
    }
    p = p.next;
  } while (p !== outerNode);
  if (!m)
    return null;
  const stop = m;
  const mx = m.x;
  const my = m.y;
  let tanMin = Infinity;
  let tan;
  p = m;
  do {
    if (hx >= p.x && p.x >= mx && hx !== p.x && pointInTriangle(hy < my ? hx : qx, hy, mx, my, hy < my ? qx : hx, hy, p.x, p.y)) {
      tan = Math.abs(hy - p.y) / (hx - p.x);
      if (locallyInside(p, hole) && (tan < tanMin || tan === tanMin && (p.x > m.x || p.x === m.x && sectorContainsSector(m, p)))) {
        m = p;
        tanMin = tan;
      }
    }
    p = p.next;
  } while (p !== stop);
  return m;
}
function sectorContainsSector(m, p) {
  return area(m.prev, m, p.prev) < 0 && area(p.next, m, m.next) < 0;
}
function indexCurve(start, minX, minY, invSize) {
  let p = start;
  do {
    if (p.z === 0)
      p.z = zOrder(p.x, p.y, minX, minY, invSize);
    p.prevZ = p.prev;
    p.nextZ = p.next;
    p = p.next;
  } while (p !== start);
  p.prevZ.nextZ = null;
  p.prevZ = null;
  sortLinked(p);
}
function sortLinked(list) {
  let e;
  let i;
  let inSize = 1;
  let numMerges;
  let p;
  let pSize;
  let q;
  let qSize;
  let tail;
  do {
    p = list;
    list = null;
    tail = null;
    numMerges = 0;
    while (p) {
      numMerges++;
      q = p;
      pSize = 0;
      for (i = 0; i < inSize; i++) {
        pSize++;
        q = q.nextZ;
        if (!q)
          break;
      }
      qSize = inSize;
      while (pSize > 0 || qSize > 0 && q) {
        if (pSize !== 0 && (qSize === 0 || !q || p.z <= q.z)) {
          e = p;
          p = p.nextZ;
          pSize--;
        } else {
          e = q;
          q = q.nextZ;
          qSize--;
        }
        if (tail)
          tail.nextZ = e;
        else
          list = e;
        e.prevZ = tail;
        tail = e;
      }
      p = q;
    }
    tail.nextZ = null;
    inSize *= 2;
  } while (numMerges > 1);
  return list;
}
function zOrder(x, y, minX, minY, invSize) {
  x = (x - minX) * invSize | 0;
  y = (y - minY) * invSize | 0;
  x = (x | x << 8) & 16711935;
  x = (x | x << 4) & 252645135;
  x = (x | x << 2) & 858993459;
  x = (x | x << 1) & 1431655765;
  y = (y | y << 8) & 16711935;
  y = (y | y << 4) & 252645135;
  y = (y | y << 2) & 858993459;
  y = (y | y << 1) & 1431655765;
  return x | y << 1;
}
function getLeftmost(start) {
  let p = start;
  let leftmost = start;
  do {
    if (p.x < leftmost.x || p.x === leftmost.x && p.y < leftmost.y)
      leftmost = p;
    p = p.next;
  } while (p !== start);
  return leftmost;
}
function pointInTriangle(ax, ay, bx, by, cx, cy, px, py) {
  return (cx - px) * (ay - py) >= (ax - px) * (cy - py) && (ax - px) * (by - py) >= (bx - px) * (ay - py) && (bx - px) * (cy - py) >= (cx - px) * (by - py);
}
function isValidDiagonal(a, b) {
  return a.next.i !== b.i && a.prev.i !== b.i && !intersectsPolygon(a, b) && // dones't intersect other edges
  (locallyInside(a, b) && locallyInside(b, a) && middleInside(a, b) && // locally visible
  (area(a.prev, a, b.prev) || area(a, b.prev, b)) || // does not create opposite-facing sectors
  equals(a, b) && area(a.prev, a, a.next) > 0 && area(b.prev, b, b.next) > 0);
}
function area(p, q, r) {
  return (q.y - p.y) * (r.x - q.x) - (q.x - p.x) * (r.y - q.y);
}
function equals(p1, p2) {
  return p1.x === p2.x && p1.y === p2.y;
}
function intersects(p1, q1, p2, q2) {
  const o1 = sign(area(p1, q1, p2));
  const o2 = sign(area(p1, q1, q2));
  const o3 = sign(area(p2, q2, p1));
  const o4 = sign(area(p2, q2, q1));
  if (o1 !== o2 && o3 !== o4)
    return true;
  if (o1 === 0 && onSegment(p1, p2, q1))
    return true;
  if (o2 === 0 && onSegment(p1, q2, q1))
    return true;
  if (o3 === 0 && onSegment(p2, p1, q2))
    return true;
  if (o4 === 0 && onSegment(p2, q1, q2))
    return true;
  return false;
}
function onSegment(p, q, r) {
  return q.x <= Math.max(p.x, r.x) && q.x >= Math.min(p.x, r.x) && q.y <= Math.max(p.y, r.y) && q.y >= Math.min(p.y, r.y);
}
function sign(num) {
  return num > 0 ? 1 : num < 0 ? -1 : 0;
}
function intersectsPolygon(a, b) {
  let p = a;
  do {
    if (p.i !== a.i && p.next.i !== a.i && p.i !== b.i && p.next.i !== b.i && intersects(p, p.next, a, b))
      return true;
    p = p.next;
  } while (p !== a);
  return false;
}
function locallyInside(a, b) {
  return area(a.prev, a, a.next) < 0 ? area(a, b, a.next) >= 0 && area(a, a.prev, b) >= 0 : area(a, b, a.prev) < 0 || area(a, a.next, b) < 0;
}
function middleInside(a, b) {
  let p = a;
  let inside = false;
  const px = (a.x + b.x) / 2;
  const py = (a.y + b.y) / 2;
  do {
    if (p.y > py !== p.next.y > py && p.next.y !== p.y && px < (p.next.x - p.x) * (py - p.y) / (p.next.y - p.y) + p.x)
      inside = !inside;
    p = p.next;
  } while (p !== a);
  return inside;
}
function splitPolygon(a, b) {
  const a2 = new Vertex(a.i, a.x, a.y);
  const b2 = new Vertex(b.i, b.x, b.y);
  const an = a.next;
  const bp = b.prev;
  a.next = b;
  b.prev = a;
  a2.next = an;
  an.prev = a2;
  b2.next = a2;
  a2.prev = b2;
  bp.next = b2;
  b2.prev = bp;
  return b2;
}
function insertNode(i, x, y, last) {
  const p = new Vertex(i, x, y);
  if (!last) {
    p.prev = p;
    p.next = p;
  } else {
    p.next = last.next;
    p.prev = last;
    last.next.prev = p;
    last.next = p;
  }
  return p;
}
function removeNode(p) {
  p.next.prev = p.prev;
  p.prev.next = p.next;
  if (p.prevZ)
    p.prevZ.nextZ = p.nextZ;
  if (p.nextZ)
    p.nextZ.prevZ = p.prevZ;
}
var Vertex = class {
  constructor(i, x, y) {
    this.prev = null;
    this.next = null;
    this.z = 0;
    this.prevZ = null;
    this.nextZ = null;
    this.steiner = false;
    this.i = i;
    this.x = x;
    this.y = y;
  }
};

// ../../../viewer/src/landmarks/kit.ts
function toRgb(c) {
  if (Array.isArray(c)) return [c[0] / 255, c[1] / 255, c[2] / 255];
  const h = c.replace("#", "");
  return [parseInt(h.slice(0, 2), 16) / 255, parseInt(h.slice(2, 4), 16) / 255, parseInt(h.slice(4, 6), 16) / 255];
}
var MeshBuilder = class {
  constructor() {
    this.pos = [];
    this.col = [];
    this.rgb = [1, 1, 1];
    this.stack = [{ tx: 0, ty: 0, tz: 0, cos: 1, sin: 0 }];
  }
  color(c) {
    this.rgb = toRgb(c);
    return this;
  }
  /** Run `fn` in a frame translated to (x, y, z) and rotated so local +y points at `bearing` (deg clockwise from north). */
  frame(x, y, z, bearing, fn) {
    const parent = this.stack[this.stack.length - 1];
    const a = -bearing * Math.PI / 180;
    const ca = Math.cos(a);
    const sa = Math.sin(a);
    const [wx, wy] = [parent.tx + parent.cos * x - parent.sin * y, parent.ty + parent.sin * x + parent.cos * y];
    this.stack.push({
      tx: wx,
      ty: wy,
      tz: parent.tz + z,
      cos: parent.cos * ca - parent.sin * sa,
      sin: parent.sin * ca + parent.cos * sa
    });
    fn();
    this.stack.pop();
    return this;
  }
  xf(p) {
    const f = this.stack[this.stack.length - 1];
    return [f.tx + f.cos * p[0] - f.sin * p[1], f.ty + f.sin * p[0] + f.cos * p[1], f.tz + p[2]];
  }
  tri(a, b, c) {
    for (const p of [a, b, c]) {
      const w = this.xf(p);
      this.pos.push(w[0], w[1], w[2]);
      this.col.push(this.rgb[0], this.rgb[1], this.rgb[2]);
    }
    return this;
  }
  quad(a, b, c, d) {
    this.tri(a, b, c);
    this.tri(a, c, d);
    return this;
  }
  /** Flat polygon at height z (earcut), optional holes. */
  cap(outer, z, holes = []) {
    const flat = [];
    const holeIdx = [];
    for (const p of outer) flat.push(p[0], p[1]);
    for (const h of holes) {
      holeIdx.push(flat.length / 2);
      for (const p of h) flat.push(p[0], p[1]);
    }
    const t = earcut(flat, holeIdx.length ? holeIdx : void 0, 2);
    for (let i = 0; i < t.length; i += 3) {
      const v = (k) => [flat[t[k] * 2], flat[t[k] * 2 + 1], z];
      this.tri(v(i), v(i + 1), v(i + 2));
    }
    return this;
  }
  /** Vertical walls of a closed ring between z0 and z1. */
  walls(ring, z0, z1) {
    for (let i = 0; i < ring.length; i++) {
      const a = ring[i];
      const b = ring[(i + 1) % ring.length];
      this.quad([a[0], a[1], z0], [b[0], b[1], z0], [b[0], b[1], z1], [a[0], a[1], z1]);
    }
    return this;
  }
  /** Extruded polygon. */
  prism(ring, z0, z1, opts = {}) {
    const { top = true, bottom = false, holes = [] } = opts;
    this.walls(ring, z0, z1);
    for (const h of holes) this.walls(h, z0, z1);
    if (top) this.cap(ring, z1, holes);
    if (bottom) this.cap(ring, z0, holes);
    return this;
  }
  /** Axis-aligned box centred at (cx, cy) in the current frame. */
  box(cx, cy, z0, sx, sy, h, opts = {}) {
    return this.prism(rect(cx, cy, sx, sy), z0, z0 + h, opts);
  }
  /** Lofted solid between two rings with equal vertex counts (tapers, twists). */
  loft(rings, zs, opts = {}) {
    const { top = true, bottom = false } = opts;
    for (let k = 0; k < rings.length - 1; k++) {
      const A = rings[k];
      const B = rings[k + 1];
      for (let i = 0; i < A.length; i++) {
        const j = (i + 1) % A.length;
        this.quad([A[i][0], A[i][1], zs[k]], [A[j][0], A[j][1], zs[k]], [B[j][0], B[j][1], zs[k + 1]], [B[i][0], B[i][1], zs[k + 1]]);
      }
    }
    if (top) this.cap(rings[rings.length - 1], zs[zs.length - 1]);
    if (bottom) this.cap(rings[0], zs[0]);
    return this;
  }
  /** Pyramid / cone from a ring up to an apex. */
  pyramid(ring, z0, apex) {
    for (let i = 0; i < ring.length; i++) {
      const a = ring[i];
      const b = ring[(i + 1) % ring.length];
      this.tri([a[0], a[1], z0], [b[0], b[1], z0], apex);
    }
    return this;
  }
  cylinder(cx, cy, r, z0, z1, segs = 16, opts = {}) {
    return this.prism(circle(cx, cy, r, segs), z0, z1, { top: opts.top ?? true });
  }
  frustum(cx, cy, r0, r1, z0, z1, segs = 16, top = true) {
    return this.loft([circle(cx, cy, r0, segs), circle(cx, cy, r1, segs)], [z0, z1], { top });
  }
  /** Spherical-cap dome (rise h) on a circle of radius r at height z0. */
  dome(cx, cy, r, z0, h, segs = 16, rings = 5) {
    const R = (r * r + h * h) / (2 * h);
    const zc = z0 + h - R;
    const ringsArr = [];
    const zs = [];
    for (let k = 0; k < rings; k++) {
      const z = z0 + h * k / rings;
      const rr = Math.sqrt(Math.max(R * R - (z - zc) * (z - zc), 0));
      ringsArr.push(circle(cx, cy, rr, segs));
      zs.push(z);
    }
    this.loft(ringsArr, zs, { top: false });
    this.pyramid(ringsArr[rings - 1], zs[rings - 1], [cx, cy, z0 + h]);
    return this;
  }
  /** Gabled roof over a rectangle (ridge along the local y axis when `alongY`). */
  gable(cx, cy, sx, sy, z0, h, alongY = true) {
    const hx = sx / 2;
    const hy = sy / 2;
    if (alongY) {
      const r0 = [cx, cy - hy, z0 + h];
      const r1 = [cx, cy + hy, z0 + h];
      this.quad([cx - hx, cy - hy, z0], [cx - hx, cy + hy, z0], r1, r0);
      this.quad([cx + hx, cy - hy, z0], [cx + hx, cy + hy, z0], r1, r0);
      this.tri([cx - hx, cy - hy, z0], [cx + hx, cy - hy, z0], r0);
      this.tri([cx - hx, cy + hy, z0], [cx + hx, cy + hy, z0], r1);
    } else {
      const r0 = [cx - hx, cy, z0 + h];
      const r1 = [cx + hx, cy, z0 + h];
      this.quad([cx - hx, cy - hy, z0], [cx + hx, cy - hy, z0], r1, r0);
      this.quad([cx - hx, cy + hy, z0], [cx + hx, cy + hy, z0], r1, r0);
      this.tri([cx - hx, cy - hy, z0], [cx - hx, cy + hy, z0], r0);
      this.tri([cx + hx, cy - hy, z0], [cx + hx, cy + hy, z0], r1);
    }
    return this;
  }
  /** Hipped roof over a rectangle: ridge length = longer side - shorter side. */
  hip(cx, cy, sx, sy, z0, h) {
    const hx = sx / 2;
    const hy = sy / 2;
    const c = [cx - hx, cy - hy, cx + hx, cy + hy];
    if (sx >= sy) {
      const r0 = [cx - hx + hy, cy, z0 + h];
      const r1 = [cx + hx - hy, cy, z0 + h];
      this.quad([c[0], c[1], z0], [c[2], c[1], z0], r1, r0);
      this.quad([c[0], c[3], z0], [c[2], c[3], z0], r1, r0);
      this.tri([c[0], c[1], z0], [c[0], c[3], z0], r0);
      this.tri([c[2], c[1], z0], [c[2], c[3], z0], r1);
    } else {
      const r0 = [cx, cy - hy + hx, z0 + h];
      const r1 = [cx, cy + hy - hx, z0 + h];
      this.quad([c[0], c[1], z0], [c[0], c[3], z0], r1, r0);
      this.quad([c[2], c[1], z0], [c[2], c[3], z0], r1, r0);
      this.tri([c[0], c[1], z0], [c[2], c[1], z0], r0);
      this.tri([c[0], c[3], z0], [c[2], c[3], z0], r1);
    }
    return this;
  }
  /** Square beam (w × w) from a to b — struts, cables, suspenders. */
  beam(a, b, w, hgt = w) {
    const dx = b[0] - a[0];
    const dy = b[1] - a[1];
    const dz = b[2] - a[2];
    const L = Math.hypot(dx, dy, dz);
    if (L < 1e-6) return this;
    let ux = -dy;
    let uy = dx;
    let uz = 0;
    let ul = Math.hypot(ux, uy, uz);
    if (ul < 1e-6) {
      ux = 1;
      uy = 0;
      uz = 0;
      ul = 1;
    }
    ux /= ul;
    uy /= ul;
    uz /= ul;
    let vx = dy * uz - dz * uy;
    let vy = dz * ux - dx * uz;
    let vz = dx * uy - dy * ux;
    const vl = Math.hypot(vx, vy, vz);
    vx /= vl;
    vy /= vl;
    vz /= vl;
    const hw = w / 2;
    const hh = hgt / 2;
    const corners = (p) => [
      [p[0] - ux * hw - vx * hh, p[1] - uy * hw - vy * hh, p[2] - uz * hw - vz * hh],
      [p[0] + ux * hw - vx * hh, p[1] + uy * hw - vy * hh, p[2] + uz * hw - vz * hh],
      [p[0] + ux * hw + vx * hh, p[1] + uy * hw + vy * hh, p[2] + uz * hw + vz * hh],
      [p[0] - ux * hw + vx * hh, p[1] - uy * hw + vy * hh, p[2] - uz * hw + vz * hh]
    ];
    const A = corners(a);
    const B = corners(b);
    for (let i = 0; i < 4; i++) {
      const j = (i + 1) % 4;
      this.quad(A[i], A[j], B[j], B[i]);
    }
    return this;
  }
  /** Polyline of beams (cables). */
  polyline(pts, w) {
    for (let i = 0; i < pts.length - 1; i++) this.beam(pts[i], pts[i + 1], w);
    return this;
  }
  /** Surface between two matching polylines (e.g. a sloped seating bowl). */
  ribbon(a, b, closed = false) {
    const n = a.length;
    for (let i = 0; i < (closed ? n : n - 1); i++) {
      const j = (i + 1) % n;
      this.quad(a[i], a[j], b[j], b[i]);
    }
    return this;
  }
  /** Vertical wall along a path with per-vertex bottom/top heights. */
  wallProfile(path, z0, z1, closed = false) {
    const n = path.length;
    const lo = (i) => Array.isArray(z0) ? z0[i] : z0;
    const hi = (i) => Array.isArray(z1) ? z1[i] : z1;
    for (let i = 0; i < (closed ? n : n - 1); i++) {
      const j = (i + 1) % n;
      this.quad([path[i][0], path[i][1], lo(i)], [path[j][0], path[j][1], lo(j)], [path[j][0], path[j][1], hi(j)], [path[i][0], path[i][1], hi(i)]);
    }
    return this;
  }
  get vertexCount() {
    return this.pos.length / 3;
  }
  build() {
    return {
      positions: { value: new Float32Array(this.pos), size: 3 },
      colors: { value: new Float32Array(this.col), size: 3 }
    };
  }
};
function rect(cx, cy, sx, sy) {
  return [
    [cx - sx / 2, cy - sy / 2],
    [cx + sx / 2, cy - sy / 2],
    [cx + sx / 2, cy + sy / 2],
    [cx - sx / 2, cy + sy / 2]
  ];
}
function circle(cx, cy, r, segs = 16, rx = r, ry = r) {
  void r;
  const out = [];
  for (let i = 0; i < segs; i++) {
    const a = i / segs * Math.PI * 2;
    out.push([cx + Math.cos(a) * rx, cy + Math.sin(a) * ry]);
  }
  return out;
}

// ../../../viewer/src/landmarks/ct-towns.ts
var WIKI = "https://en.wikipedia.org/wiki/";
var OVERTURE = "https://docs.overturemaps.org/guides/buildings/";
function P(...n) {
  const o = [];
  for (let i = 0; i < n.length; i += 2) o.push([n[i], n[i + 1]]);
  return o;
}
function scale(ring, kx, ky = kx, bearing = 0) {
  const cx = ring.reduce((s, p) => s + p[0], 0) / ring.length;
  const cy = ring.reduce((s, p) => s + p[1], 0) / ring.length;
  const a = bearing * Math.PI / 180;
  const ux = Math.sin(a);
  const uy = Math.cos(a);
  return ring.map(([x, y]) => {
    const dx = x - cx;
    const dy = y - cy;
    const along = dx * ux + dy * uy;
    const across = dx * uy - dy * ux;
    const na = along * ky;
    const nc = across * kx;
    return [cx + na * ux + nc * uy, cy + na * uy - nc * ux];
  });
}
function mean(ring) {
  return [ring.reduce((s, p) => s + p[0], 0) / ring.length, ring.reduce((s, p) => s + p[1], 0) / ring.length];
}
var CT_TOWNS = [];
var R_landmark = P(9, 25.6, 6.6, 28.1, 4.6, 28.3, 3, 25.3, -0.8, 25.3, -2.2, 28.8, -6.5, 26.5, -18.2, 25.9, -23, 22.5, -24.7, 17.6, -25.3, 9.2, -27.6, 5.1, -26.3, 4.5, -26.6, -0.4, -28.2, -1.1, -27.9, -3.4, -25.8, -5.5, -26.3, -12.8, -25.3, -17.9, -22.1, -22.1, -16.1, -24.3, -8.1, -24.6, -5.3, -27, -3, -23.2, -0.6, -23.3, 4, -28.4, 5.6, -25.5, 17.1, -25, 23, -21.3, 25, -15.3, 25.3, -7.9, 27.9, -4, 26.5, -1.9, 26.6, 1.9, 28.1, 3.2, 28, 5, 26, 6.8, 26.4, 13.6, 25.4, 19.3, 23.4, 22.5, 20.8, 24.2, 15.9, 25.5);
function buildLandmark(b) {
  const concrete = "#CFC8BA";
  const dark = "#7E7A72";
  b.color(dark).prism(R_landmark, 0, 5.5);
  b.color(concrete).loft([scale(R_landmark, 0.985), scale(R_landmark, 0.975), scale(R_landmark, 0.96)], [5.5, 35, 62]);
  b.color("#6D737A").prism(scale(R_landmark, 0.96), 62, 64);
  b.color(concrete).loft([scale(R_landmark, 0.96), scale(R_landmark, 0.93)], [64, 86]);
  b.color(dark).prism(scale(R_landmark, 0.93), 86, 87.6);
  b.color("#A9A59C").box(0, 0, 87.6, 13, 13, 2.32);
}
CT_TOWNS.push({
  id: "one_landmark_square",
  name: "One Landmark Square",
  kind: "tower",
  built: [1970, 1973.5],
  end: 9999,
  anchor: [-73.538058, 41.054713],
  build: buildLandmark,
  replaces: [R_landmark],
  facts: {
    Built: "construction began 1970, completed 1973 for F. D. Rich Company (Victor H. Bisharat; neo-futurist, scalloped entrances); the centrepiece of Stamford\u2019s urban renewal, tallest building between New York and Boston until 1990",
    Height: "295 ft (89.9 m), 22 floors",
    Model: "plan from the footprint (about 56 x 56 m); roof height cited (295 ft); the podium (5.5 m), the slight taper and the window bands are estimated; start of building (1970) cited"
  },
  sources: [WIKI + "One_Landmark_Square", WIKI + "Downtown_Stamford", OVERTURE]
});
var R_park = P(10.6, -22.2, 16.3, -22.3, 19.7, 11.3, 19, 11.4, 19.9, 20.3, 15.3, 20.3, 15.9, 25, -14.9, 26.4, -15.5, 21.2, -12.8, 21.7, -16.2, 12.2, -18.1, 3.3, -19, -6.5, -19.3, -6.6, -21.4, -23, -20.5, -23.2, -20.9, -26.7, 10.7, -27);
function buildPark(b) {
  b.color("#8D887C").prism(R_park, 0, 17.5);
  b.color("#6F93AB").loft([scale(R_park, 0.84, 0.8, 5.7), scale(R_park, 0.82, 0.78, 5.7)], [17.5, 100]);
  b.color("#5E7F96").loft([scale(R_park, 0.82, 0.78, 5.7), scale(R_park, 0.66, 0.6, 5.7)], [100, 106.68]);
}
CT_TOWNS.push({
  id: "park_tower_stamford",
  name: "Park Tower Stamford",
  kind: "tower",
  built: [2007.4, 2009.7],
  end: 9999,
  anchor: [-73.542802, 41.05526],
  build: buildPark,
  replaces: [R_park],
  facts: {
    Built: "groundbreaking 15 May 2007, opened September 2009 (Costas Kondylis and Lessard Design; as Trump Parc Stamford until 2013); the tallest building in Stamford",
    Height: "350 ft (106.7 m), 34 floors above a 6-story parking podium",
    Model: "plan from the footprint (55 x 37 m); height cited (350 ft); the podium height (17.5 m) and the glass colour estimated"
  },
  sources: [WIKI + "Park_Tower_Stamford", WIKI + "Downtown_Stamford", OVERTURE]
});
var R_atlantic = P(28.2, 20, -26.9, 21.8, -28.9, -40.6, 26.2, -42.3);
function buildAtlantic(b) {
  b.color("#A39B8D").prism(R_atlantic, 0, 15);
  b.color("#7C98AD").loft([scale(R_atlantic, 0.76, 0.72, 1.9), scale(R_atlantic, 0.75, 0.71, 1.9)], [15, 88]);
  b.color("#9AA2A8").prism(scale(R_atlantic, 0.6, 0.55, 1.9), 88, 96);
}
CT_TOWNS.push({
  id: "atlantic_station_stamford",
  name: "Atlantic Station",
  kind: "tower",
  built: [2015, 2017],
  end: 9999,
  anchor: [-73.540051, 41.050507],
  build: buildAtlantic,
  replaces: [R_atlantic],
  facts: {
    Built: "completed 2017 by RXR Realty; 325 apartments, retail and a 333-space garage; a second tower was under construction beside it",
    Height: "315 ft (96.0 m), 26 stories; the second tallest building in Stamford",
    Model: "plan from the footprint (62 x 55 m); height cited (315 ft; the footprint\u2019s mapped height is 93 m); the podium (15 m), the set-back crown and the colours estimated; start of building (2015) estimated"
  },
  sources: [WIKI + "Downtown_Stamford", OVERTURE]
});
var R_fish = P(20.7, -0.2, 24.8, 0.4, 25.3, 2.3, 36.6, 1.2, 35.2, 9, 25.1, 6.3, 23.1, 19.1, 29.8, 20.1, 29.3, 23.3, 59.8, 28, 63.8, 2.4, 62.8, 2.3, 64.8, -10.8, 79.2, -11.1, 78.9, -9.6, 91.3, -7.7, 94.5, -31.8, 99.4, -32.7, 98, -40, 112, -42.6, 124.8, -35.8, 121.2, -29.1, 127.4, -25.9, 119.5, -10.9, 113.2, -14.1, 112.5, -12.8, 102.7, -14.5, 102.5, -16, 96.6, -15, 93.1, 7, 78.3, 4.7, 72.4, 42.6, 61.2, 40.8, 61.3, 40.2, 20.9, 33.9, 22.5, 23.3, 17.8, 22.6, 19.7, 10, -4.5, 13.4, -4.1, 16.5, -16.4, 18.3, -16.9, 15.1, -22.4, 15.9, -28.6, 13, -22.3, -0.5, -31.8, -2.3, -32.2, -8.8, -18.3, -8.3, 8.8, -6.4);
var R_fish_nave = P(61, 20, 61.2, 40.8, 72.4, 42.6, 78.3, 4.7, 93.1, 7, 96.6, -15, 102.5, -16, 102.7, -14.5, 112.5, -12.8, 113.2, -14.1, 119.5, -10.9, 127.4, -25.9, 121.2, -29.1, 124.8, -35.8, 112, -42.6, 98, -40, 99.4, -32.7, 94.5, -31.8, 91.3, -7.7, 78.9, -9.6, 79.2, -11.1, 64.8, -10.8, 62.8, 2.3, 63.8, 2.4);
function buildFish(b) {
  b.color("#8B7F72").prism(R_fish, 0, 6.6);
  b.color("#A89C8C").prism(R_fish_nave, 6.6, 18.3);
  b.color("#4D4B49").prism(scale(R_fish_nave, 0.9), 18.3, 19.2);
  b.frame(16.6, 4.4, 0, 0, () => {
    b.color("#BDB5A5").box(0, 0, 0, 6.6, 6.6, 66);
    b.color("#9A937F").box(0, 0, 66, 7.4, 7.4, 8);
    b.color("#5F6B66").pyramid(rect(0, 0, 7.4, 7.4), 74, [0, 0, 79.25]);
  });
}
CT_TOWNS.push({
  id: "fish_church_stamford",
  name: "First Presbyterian Church (Fish Church)",
  kind: "building",
  built: [1956, 1958.2],
  end: 9999,
  anchor: [-73.539071, 41.062947],
  build: buildFish,
  replaces: [R_fish],
  facts: {
    Built: "sanctuary dedicated March 1958, Wallace K. Harrison (architect of the United Nations headquarters); the fish shape is in both profile and plan; 20,000 pieces of faceted stained glass",
    Height: "nave 60 ft (18 m); Maguire Memorial Tower 260 ft (79.2 m) with a 56-bell carillon",
    Model: "footprint from the map (L-shaped, 3,400 m2); tower and nave heights cited; WHICH PART of the footprint is the sanctuary and WHERE the tower stands are guesses (LOW), as are the colours and the lid of the nave; start of building estimated"
  },
  sources: [WIKI + "Fish_Church", WIKI + "Downtown_Stamford", OVERTURE]
});
var R_oth = P(-10.4, -22, -18.1, -21.9, -18.5, -29.4, -2.6, -30.1, -2.8, -22.4, 19.1, 11, -7.5, 29, -14.7, 29.1, -17, 0.6, -7, -0.5, -8.9, -3.5);
function buildOth(b) {
  b.color("#D8D2C2").prism(R_oth, 0, 15.5);
  b.color("#C6BFAC").prism(R_oth, 15.5, 16.6);
  b.color("#5A6068").loft([scale(R_oth, 0.97), scale(R_oth, 0.85)], [16.6, 21]);
  b.frame(12.3, 9.6, 0, 0, () => {
    b.color("#D8D2C2").box(0, 0, 14, 7, 7, 17);
    b.color("#E6E1D2").box(0, 0, 31, 8, 8, 4);
    b.color("#6E8F7E").pyramid(rect(0, 0, 8.6, 8.6), 35, [0, 0, 41]);
  });
}
CT_TOWNS.push({
  id: "old_town_hall_stamford",
  name: "Old Town Hall",
  kind: "building",
  built: [1905, 1907.2],
  end: 9999,
  anchor: [-73.540631, 41.052827],
  build: buildOth,
  replaces: [R_oth],
  facts: {
    Built: "built 1905-07, opened 20 March 1907 (Mellon and Josselyn, Beaux-Arts); Stamford\u2019s seat of government until 1963; the Stamford Innovation Center since 2012",
    Height: "three stories on five levels, a limestone facade and a clock tower; no height published",
    Model: "plan from the footprint (the triangular block at Main and Atlantic streets, 1,170 m2); the wall height (15.5 m), the mansard, and the clock tower\u2019s place and height (41 m) are estimated (LOW); the footprint has no mapped height"
  },
  sources: [WIKI + "Old_Town_Hall_(Stamford,_Connecticut)", WIKI + "Downtown_Stamford", OVERTURE]
});
var R_basilica = P(22.6, -14.7, 22.9, -11.9, 24.6, -12, 24.8, -9.5, 24.2, -9.4, 25.4, 5.6, 26.3, 5.5, 26.9, 12.6, 19.9, 13.2, 19.7, 10.8, 5.9, 12, 6.2, 15.7, -10.2, 17.1, -10.5, 13.5, -14.5, 13.9, -15, 15.9, -17.3, 18.1, -20.2, 18.3, -22.6, 16.8, -23.7, 14.1, -25.8, -9.6, -16.6, -10.3, -16.4, -7.8, -12.2, -8.1, -12.5, -11.4, 3.9, -12.7, 4.1, -9.8, 8.5, -10.5, 8.5, -10, 12.7, -10.3, 13.3, -10.9, 13.1, -13.5, 17, -13.9, 17.2, -11.2, 18.1, -11.3, 17.9, -14.2);
function buildBasilica(b) {
  b.color("#9A9183").prism(R_basilica, 0, 12.5);
  b.frame(0.5, 1.9, 12.5, 95.4, () => {
    b.color("#4C5057").gable(0, 0, 23.5, 44, 0, 10.5, true);
  });
}
CT_TOWNS.push({
  id: "st_john_basilica_stamford",
  name: "Basilica of St. John the Evangelist",
  kind: "building",
  built: [1866.5, 1868.5],
  end: 9999,
  anchor: [-73.540016, 41.051743],
  build: buildBasilica,
  replaces: [R_basilica],
  facts: {
    Built: "the present church was built in 1868 (James Murphy of Providence; the first church on Meadow Street dated from 1851); a minor basilica",
    Height: "ridge 23 m (the footprint\u2019s mapped height); no spire height published; exterior 100 x 180 ft",
    Model: "plan from the footprint (50.6 x 28.9 m); ridge height is the mapped one; the eave height (12.5 m), the slate roof and the stone colour are estimated and NO tower or spire is modelled (none could be placed from an opened page); start of building estimated"
  },
  sources: [WIKI + "Basilica_of_Saint_John_the_Evangelist", OVERTURE]
});
var R_bc = P(29.1, -67.6, 4.5, -14.5, 17.9, -6.1, 27.3, 4.5, 31.7, 14.5, 33.7, 22.2, 34.2, 36.4, 32.5, 46.1, 29.8, 52.4, 45.8, 59.7, 40.8, 82.2, 38.5, 81.4, 36.2, 91.4, -48.4, 73.9, -44.8, 53.1, -27, 57, -22.8, 46.9, -18.6, 48, -17.5, 43, -13.8, 43.1, -7.5, 40.6, -3.9, 35.3, -3.3, 31.3, -4.3, 26.4, -6.9, 22.8, -12.4, 20.2, -10.3, 10.4, -19.5, 8.5, -22.6, 5.8, -23.6, 1.3, -21.8, -3.2, -17, -6.2, -16.4, -7.7, -14.5, -8.4, -6.7, -6.5, 5.8, -64.8, -5, -66.8, -3.7, -73.3, -6.9, -73.9, -4.3, -85, -3, -86.9, -1.3, -87.9, 5.4, -87.9, 11.2, -90.2, 15.7, -88.9);
var R_bc_red = P(27.3, 4.5, 17.9, -6.1, 4.5, -14.5, 29.1, -67.6, 19.5, -83.5, 15.7, -88.9, 11.2, -90.2, 8.2, -89.5, 5.4, -87.9, -1.3, -87.9, -3, -86.9, -4.3, -85, -6.9, -73.9, -3.7, -73.3, -5, -66.8, 5.8, -64.8, -6.7, -6.5, -14.5, -8.4, -16.4, -7.7, -17, -6.2, -21.8, -3.2, -23, -1.3, -23.6, 1.3, -23.4, 3.5, -22.6, 5.8, -19.5, 8.5, -13.8, 10, 29.7, 10);
var R_bc_white = P(-10.3, 10.4, -12.4, 20.2, -6.9, 22.8, -4.3, 26.4, -3.3, 31.3, -3.9, 35.3, -5.3, 38.1, -7.5, 40.6, -10.7, 42.3, -13.8, 43.1, -17.5, 43, -18.6, 48, -22.8, 46.9, -27, 57, -44.8, 53.1, -48.4, 73.9, 36.2, 91.4, 38.5, 81.4, 40.8, 82.2, 45.8, 59.7, 29.8, 52.4, 32.5, 46.1, 34.2, 36.4, 33.7, 22.2, 31.7, 14.5, 29.7, 10, -13.8, 10);
function buildBc(b) {
  b.color("#B4AFA5").prism(R_bc, 0, 21);
  b.color("#9B5B50").prism(R_bc_red, 21, 75.6);
  b.color("#9B5B50").prism(scale(R_bc_red, 0.78), 75.6, 81.4);
  b.color("#E3E1DB").prism(R_bc_white, 21, 58);
}
CT_TOWNS.push({
  id: "bridgeport_center",
  name: "Bridgeport Center (People\u2019s Bank Building)",
  kind: "tower",
  built: [1984, 1989.5],
  end: 9999,
  anchor: [-73.18804, 41.176162],
  build: buildBc,
  replaces: [R_bc],
  facts: {
    Built: "construction began 1984, completed 1989 (Richard Meier & Partners) as the headquarters of People\u2019s Bank, later People\u2019s United, now M&T Bank; replaced the Bridgeport National Bank building",
    Height: "18 floors; red wing 248 ft (75.6 m), main roof 267 ft (81.4 m)",
    Model: "plan from the footprint (6,850 m2); red-wing roof and main roof cited; the split between red and white parts (cut at the footprint\u2019s middle), the 21 m base and the 58 m height of the white block are estimated (LOW)"
  },
  sources: [WIKI + "Bridgeport_Center", OVERTURE]
});
var R_trust = P(11.8, 10.6, -44.4, -12.5, -39, -26.1, 0.2, -10.7, 2.2, -15, 16.5, -11.6);
function buildTrust(b) {
  b.color("#C9BC9F").prism(R_trust, 0, 14);
  b.color("#D8CDB4").loft([scale(R_trust, 0.97, 0.97, 68.4), scale(R_trust, 0.94, 0.95, 68.4)], [14, 36]);
  b.color("#CFC3A8").loft([scale(R_trust, 0.8, 0.9, 68.4), scale(R_trust, 0.72, 0.84, 68.4)], [36, 45]);
  b.color("#B7AA8C").loft([scale(R_trust, 0.55, 0.7, 68.4), scale(R_trust, 0.4, 0.55, 68.4)], [45, 50.3]);
}
CT_TOWNS.push({
  id: "city_trust_bridgeport",
  name: "City Trust Apartments",
  kind: "tower",
  built: [1927, 1929.5],
  end: 9999,
  anchor: [-73.189279, 41.177649],
  build: buildTrust,
  replaces: [R_trust],
  facts: {
    Built: "completed 1929 (Dennison & Hirons of New York, Art Deco) as the City Trust Company\u2019s tower at 955 Main Street; apartments and offices today",
    Height: "165 ft (50.3 m), 10 floors",
    Model: "plan from the footprint (about 61 x 22 m, matched to the article\u2019s coordinates); roof cited (165 ft); the base height (14 m), the set-backs and the stone colour estimated (LOW); start of building estimated"
  },
  sources: [WIKI + "City_Trust_Apartments", OVERTURE]
});
var R_staug = P(-3.7, 12.8, -3.6, 14.8, -4.9, 17.3, -18.9, 22.2, -28.6, -6.6, -19.4, -9.7, -19.1, -8.9, -15.2, -10.2, -12.2, -9.6, -11.2, -8.5, 20, -18.9, 21.6, -14.1, 22.5, -14.4, 23.4, -11.7, 25.2, -12.3, 27.3, -6.1, 25.4, -5.5, 26.4, -2.8, 25.5, -2.5, 27.2, 2.5);
function buildStAug(b) {
  b.color("#8F8A82").prism(R_staug, 0, 13);
  b.frame(1.3, -0.6, 13, 108.6, () => {
    b.color("#4B4E52").gable(0, 0, 19, 46, 0, 8.5, true);
  });
  b.frame(-20.6, 4.5, 0, 108.6, () => {
    b.color("#8F8A82").box(0, 0, 0, 8, 8, 34);
    b.color("#9A958D").box(0, 0, 34, 6.6, 6.6, 6);
    b.color("#4B4E52").pyramid(rect(0, 0, 6.6, 6.6), 40, [0, 0, 55.02]);
  });
}
CT_TOWNS.push({
  id: "st_augustine_cathedral_bridgeport",
  name: "St. Augustine Cathedral",
  kind: "building",
  built: [1865.65, 1868.2],
  end: 9999,
  anchor: [-73.195703, 41.180251],
  build: buildStAug,
  replaces: [R_staug],
  facts: {
    Built: "cornerstone laid 28 August 1865, dedicated 17 March 1868 (Patrick C. Keely, Gothic Revival); seat of the Diocese of Bridgeport; renovated 2003-04",
    Height: "180.5 ft (55.0 m)",
    Model: "plan from the footprint (53 x 30 m); the height of the tallest part is cited, but the tower\u2019s place (west end) and its stages, the nave eave (13 m) and roof are estimated (LOW)"
  },
  sources: [WIKI + "St._Augustine_Cathedral_(Bridgeport,_Connecticut)", OVERTURE]
});
var R_ch = P(14.3, 31, 8.3, 29.1, 9.1, 26.4, -8.7, 20.9, -9.4, 23.1, -14, 21.7, -13.3, 19.4, -27.2, 15.1, -28, 17.8, -35.4, 15.5, -27, -11, -23.3, -9.9, -20.8, -18.2, -21.4, -19.8, -20.8, -21.8, -18.8, -23.2, -15.7, -22.7, -14.3, -19.7, -1.1, -15.4, -0.5, -16.9, 1.1, -17.5, 4.5, -17, 5.9, -15.5, 5.7, -13.6, 20.4, -8.9, 20.7, -10.2, 22.8, -11.5, 25.9, -10.6, 27.2, -8.3, 26.9, -6.9, 32.2, -5.2, 28.9, 5.3, 31.1, 6, 27.1, 18.6, 24.9, 18, 21.1, 30.1, 15.2, 28.3);
function buildCh(b) {
  b.color("#7A6C60").prism(R_ch, 0, 2.4);
  b.color("#9E4B3B").prism(R_ch, 2.4, 12.6);
  b.color("#4D4A49").loft([scale(R_ch, 0.99), scale(R_ch, 0.5)], [12.6, 15.9]);
  b.frame(1.4, -11, 0, 72.7, () => {
    b.color("#9E4B3B").box(0, 0, 8, 9, 9, 19);
    b.color("#B4A590").box(0, 0, 27, 9.6, 9.6, 1.4);
    b.color("#4D4A49").pyramid(rect(0, 0, 9.6, 9.6), 28.4, [0, 0, 37]);
  });
}
CT_TOWNS.push({
  id: "fairfield_county_courthouse_bridgeport",
  name: "Fairfield County Courthouse",
  kind: "building",
  built: [1886.5, 1888.5],
  end: 9999,
  anchor: [-73.190901, 41.180536],
  build: buildCh,
  replaces: [R_ch],
  facts: {
    Built: "built 1888 (Warren R. Briggs) when the old city hall and courthouse (McLevy Hall) proved too small; Richardsonian Romanesque in brick, brownstone and terra cotta; National Register 1982",
    Height: "three stories with a six-story central tower under a pyramidal roof; no tower height published",
    Model: "plan from the footprint (60 x 43 m); the main roof is the mapped 15.9 m; the tower\u2019s place on the Golden Hill Street front and its height (37 m), the eave height and the colours are estimated (LOW)"
  },
  sources: [WIKI + "Fairfield_County_Courthouse_(Bridgeport,_Connecticut)", OVERTURE]
});
var R_mclevy = P(-15.6, 13.7, -1.4, -20.6, 15.6, -13.6, 1.4, 20.6);
function buildMcLevy(b) {
  b.color("#D6CDB6").prism(R_mclevy, 0, 7.6);
  b.frame(0, 0, 7.6, 157.5, () => {
    b.color("#59595C").gable(0, 0, 19.6, 38.6, 0, 2.1, true);
    for (const x of [-6.6, -2.2, 2.2, 6.6]) b.color("#EEE9DA").cylinder(x, 20.4, 0.5, -7.6, 7, 8);
    b.color("#EEE9DA").gable(0, 20.4, 15.4, 3.4, 7, 2.4, false);
    b.color("#E9E3D0").box(0, 0, 9.7, 3.6, 3.6, 2.8);
    b.color("#59595C").pyramid(rect(0, 0, 3.8, 3.8), 12.5, [0, 0, 14.6]);
  });
}
CT_TOWNS.push({
  id: "mclevy_hall_bridgeport",
  name: "McLevy Hall (old City Hall)",
  kind: "building",
  built: [1852, 1854.5],
  end: 9999,
  anchor: [-73.189868, 41.176816],
  build: buildMcLevy,
  replaces: [R_mclevy],
  facts: {
    Built: "built 1854 (Alexander Jackson Davis and J. W. Northrop) to house both the City Hall and the Fairfield County Courthouse; Bridgeport\u2019s city hall into the 1930s; renamed for Mayor Jasper McLevy in 1966",
    Height: "footprint height 9.7 m (mapped); no other height published",
    Model: "plan from the footprint (37 x 18 m); the walls (7.6 m) and the ridge (9.7 m, the mapped height) follow the footprint; the portico (which end), the cupola and its height (14.6 m) are estimated (LOW)"
  },
  sources: [WIKI + "McLevy_Hall", OVERTURE]
});
var R_arena = P(7.2, -35.1, 12.2, -53.4, 27.8, -65.1, 40, -61.8, 35, -43.3, 25.2, -37.9, 23.2, -30.7, 62.7, -20.2, 52.1, 33.1, 43.6, 62.6, 15.2, 54.3, 16.4, 49.9, 2.3, 45.8, 3.6, 40.3, -26.1, 32.1, -27.7, 38.2, -44.2, 32.5, -42.3, 27.7, -50.3, 21.7, -58.1, 27.2, -62.9, 21.7, -55.9, 16.4, -58.4, 4.8, -58.9, -4.7, -53.5, -23, -47.7, -28.4, -57.9, -30.9, -52.6, -50.6, -23.1, -42.9, -23, -43.5);
function buildArena(b) {
  b.color("#9C6D5A").prism(R_arena, 0, 9);
  b.color("#8E969D").prism(R_arena, 9, 12);
  b.color("#7C858C").loft([scale(R_arena, 0.66), scale(R_arena, 0.58)], [12, 17]);
}
CT_TOWNS.push({
  id: "total_mortgage_arena",
  name: "Total Mortgage Arena",
  kind: "stadium",
  built: [1999.6, 2001.78],
  end: 9999,
  anchor: [-73.186896, 41.173235],
  build: buildArena,
  replaces: [R_arena],
  facts: {
    Built: "opened 10 October 2001 as The Arena at Harbor Yard (later Webster Bank Arena); 10,000 seats; home of the Bridgeport Islanders (AHL) 2001-2026",
    Height: "no published height; the footprint\u2019s mapped height is 12.0 m",
    Model: "plan from the footprint (about 123 x 119 m); the 12 m is the mapped height; the raised bowl roof (17 m) and the brick base are estimated; start of building estimated"
  },
  sources: [WIKI + "Total_Mortgage_Arena", OVERTURE]
});
var R_amph = P(66.3, 35.6, 45.7, 56.2, 33.1, 65.2, 11.5, 38.9, 9.8, 35.4, 27.2, 20.5, 13.8, 7, -7, 12.1, -11.9, 22.6, -8.9, 30.1, -14.8, 50.2, -30.2, 51.1, -35.6, 37.7, -44.6, 39.2, -55, -25.1, -52.8, -32.2, -54, -32.6, -50.3, -46.4, -48.7, -46, -47.2, -51.2, -44.1, -56.8, -29.9, -70.3, -18.2, -72.7, -18.8, -74.9, -4.9, -78.3, -4.4, -76.1, 2.7, -77.8, 32.3, -71.9, 30.7, -63.9, 58.7, -58.4, 65.6, -58.2, 61.6, -44.6, 63.2, -38.5, 61.1, -34.7, 60.2, -24.9, 72.8, -11.5, 68.6, -6.9, 62.2, -11.1, 41.2, 9.6);
function buildAmph(b) {
  const c = mean(R_amph);
  b.color("#A5A7A9").prism(R_amph, 0, 7);
  b.color("#EAE9E3").pyramid(scale(R_amph, 0.82), 7, [c[0], c[1], 20.7]);
}
CT_TOWNS.push({
  id: "hartford_healthcare_amphitheater",
  name: "Hartford HealthCare Amphitheater",
  kind: "stadium",
  built: [2018.6, 2021.6],
  end: 9999,
  anchor: [-73.187612, 41.171988],
  build: buildAmph,
  replaces: [R_amph],
  facts: {
    Built: "the Ballpark at Harbor Yard (opened 21 May 1998, closed after the 2017 season) was rebuilt as a concert amphitheater: groundbreaking July 2018, opened 28 July 2021",
    Height: "no published height; the footprint\u2019s mapped height is 20.7 m",
    Model: "plan from the footprint (134 x 131 m); the tent\u2019s apex is the mapped 20.7 m; the concourse height (7 m) and the tent\u2019s shape (a single pyramid) are estimated (LOW)"
  },
  sources: [WIKI + "The_Ballpark_at_Harbor_Yard", OVERTURE]
});
var R_palace = P(-31, -22.9, -14.5, -48.3, 49.1, -12.4, 14.7, 41.9, -45.8, 10.9, -36.7, -10.8);
function buildPalace(b) {
  b.color("#B8A888").prism(R_palace, 0, 6);
  b.color("#DAD0B8").prism(R_palace, 6, 22.5);
  b.color("#C8BEA4").prism(R_palace, 22.5, 24);
}
CT_TOWNS.push({
  id: "palace_majestic_bridgeport",
  name: "Palace and Majestic Theaters",
  kind: "building",
  built: [1921, 1922.5],
  end: 9999,
  anchor: [-73.191178, 41.182409],
  build: buildPalace,
  replaces: [R_palace],
  facts: {
    Built: "built 1921-22 by Sylvester Z. Poli to the design of Thomas W. Lamb: two theaters and a hotel in one block of Main Street; the Majestic closed in 1971, the Palace in 1975; vacant since; National Register 1979",
    Height: "five stories; no height published",
    Model: "plan from the footprint (75 x 67 m, the whole block); the height (24 m from five stories of about 4.5 m), the base band and the colours are estimated; no stage house or sign is modelled"
  },
  sources: [WIKI + "Palace_and_Majestic_Theaters", OVERTURE]
});
export {
  CT_TOWNS,
  MeshBuilder
};
