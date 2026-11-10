// dump.ts
import { writeFileSync } from "node:fs";

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
    const R2 = (r * r + h * h) / (2 * h);
    const zc = z0 + h - R2;
    const ringsArr = [];
    const zs = [];
    for (let k = 0; k < rings; k++) {
      const z = z0 + h * k / rings;
      const rr = Math.sqrt(Math.max(R2 * R2 - (z - zc) * (z - zc), 0));
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
  const out2 = [];
  for (let i = 0; i < segs; i++) {
    const a = i / segs * Math.PI * 2;
    out2.push([cx + Math.cos(a) * rx, cy + Math.sin(a) * ry]);
  }
  return out2;
}

// ../../../viewer/src/landmarks/nyc-towers.ts
var M = {
  esb: {
    anchor: [-73.985705, 40.748453],
    B: 28.9,
    foot: [[[-59.7, 29.9], [68.4, 29.9], [68.3, -28.2], [-59.8, -28.2], [-59.8, -25.1], [-80.4, -25.1], [-80.3, -2.9], [-61.3, -2.9], [-61.3, -0.7], [-59.8, -0.7]]],
    levels: [
      [0, 17, [[-53.1, 29.9], [68.4, 29.9], [68.4, 14.9], [68.3, -6.2], [68.3, -28.2], [-59.8, -28.2], [-59.8, -25.1], [-80.4, -25.1], [-80.3, -2.9], [-61.3, -2.9], [-61.3, -0.7], [-59.8, -0.7], [-59.8, 2.3], [-59.7, 29.9]]],
      [17, 75, [[-42.9, -19.5], [-42.6, 21.6], [-31.5, 21.6], [-31.3, 25.9], [-9.9, 25.9], [-9.7, 21.5], [17.9, 21.4], [18.2, 25.9], [39.6, 25.9], [39.7, 21.4], [51.3, 21.4], [51, -19.7], [39.4, -19.7], [39.2, -24.4], [17.8, -24.3], [17.6, -19.6], [-10, -19.6], [-10.3, -24.4], [-31.7, -24.3], [-31.9, -19.5]]],
      [75, 90, [[-31.7, -24.3], [-31.6, -6.3], [-30, -6.1], [-29.9, 7.7], [-31.5, 8], [-31.3, 25.9], [-9.9, 25.9], [-9.7, 21.5], [17.9, 21.4], [18.2, 25.9], [39.6, 25.9], [39.4, 7.8], [37.9, 7.6], [37.7, -6.6], [39.4, -6.9], [39.2, -24.4], [17.8, -24.3], [17.6, -19.6], [-10, -19.6], [-10.3, -24.4]]],
      [90, 115, [[-30.1, -12.9], [-29.9, 15.3], [-23.9, 15.3], [-23.8, 21.5], [31.9, 21.4], [31.9, 15.1], [37.9, 15], [37.7, -13.1], [31.6, -13.2], [31.5, -19.7], [-24.1, -19.5], [-24.2, -13]]],
      [115, 255, [[-24.1, -19.5], [-23.8, 21.5], [-4.9, 21.5], [-4.6, 15.2], [13, 15.2], [13.2, 21.4], [31.9, 21.4], [31.5, -19.7], [12.8, -19.6], [12.7, -13.5], [-4.9, -13.5], [-5.3, -19.6]]],
      [255, 290, [[-22.1, -17.6], [-21.8, 19.5], [-6.9, 19.5], [-6.6, 15.2], [13.2, 15.2], [15.2, 15.3], [15.2, 19.4], [29.8, 19.4], [29.5, -17.7], [14.8, -17.7], [14.6, -13.5], [-6.9, -13.4], [-7.3, -17.6]]],
      [290, 310, [[-18.5, -11.5], [-18.3, 13.4], [-16.2, 15.2], [24.3, 15.1], [26.8, 12.8], [26.5, -11.9], [24.6, -13.6], [-16.7, -13.4]]],
      [310, 320, [[-17.5, -11.1], [-17.3, 12.8], [-15.6, 14.3], [23.1, 14.1], [25.8, 11.5], [25.6, -11.3], [24.1, -12.6], [-16.2, -12.4]]]
    ]
  },
  chrysler: {
    anchor: [-73.975366, 40.751644],
    B: 29,
    foot: [[[24.7, -13.7], [22.2, -31.5], [-28.3, -31.5], [-28.1, 29], [33.5, 29], [33.5, 20.8], [26.9, -3.5]]],
    levels: [
      [0, 15, [[24.7, -13.7], [22.2, -31.5], [5, -31.5], [-27.2, -31.5], [-28.3, -31.5], [-28.2, -12.8], [-28.1, 29], [-26.8, 29], [2.6, 29], [33.5, 29], [33.5, 20.8], [26.9, -3.5], [26.8, -3.7]]],
      [15, 50, [[-28.7, -14], [-11.3, -13.6], [-11.2, 11.3], [-28.7, 11.5], [-28.4, 29.4], [33.9, 29.3], [34, 20.7], [31.5, 11.6], [17.4, 11.2], [17.3, -13.6], [25.2, -13.8], [22.5, -31.9], [-28.4, -31.9]]],
      [50, 70, [[-23.4, 24.3], [28.8, 24], [28.9, 11.5], [17.4, 11.2], [17.3, -13.6], [25.2, -13.8], [23.4, -26.4], [-23.2, -26.4], [-23.4, -14], [-11.3, -13.7], [-11.2, 11.2], [-23.3, 11.5]]],
      [70, 80, [[-20.6, -23.9], [-20.5, -14], [-11.3, -13.7], [-11.2, 11.2], [-20.6, 11.4], [-20.5, 21.5], [26.1, 21.6], [26.1, 11.5], [17.4, 11.2], [17.3, -13.6], [25.2, -13.8], [23.8, -23.4]]],
      [80, 91, [[-11.3, -20.8], [-11.1, 18.5], [17.4, 18.6], [17.2, -20.7]]],
      [91, 185, [[-11.3, -18.1], [-11.1, 16.8], [17.4, 16.8], [17.3, -18.1]]],
      [185, 199, [[-11.3, -9.9], [-11.2, 9.2], [-6.7, 11.8], [-6.8, 16.8], [12.4, 16.8], [12.7, 12.1], [17.4, 9], [17.3, -10.3], [12.4, -12.7], [12.5, -18.1], [-6.4, -18.1], [-6.6, -13.1], [-9.5, -10]]]
    ]
  },
  onewtc: {
    anchor: [-74.013174, 40.713009],
    B: 29.3,
    foot: [[[31.2, -30.9], [-31.1, -30.9], [-30.8, 31.1], [30.8, 31]]],
    levels: []
  },
  wtc7: {
    anchor: [-74.012075, 40.713414],
    B: 10.8,
    foot: [[[24.5, 21.9], [24.5, -39.3], [-24.6, -21.9], [-24.6, 39.2]]],
    levels: []
  },
  wtc3: {
    anchor: [-74.01166, 40.710978],
    B: 26.4,
    foot: [[[-14.9, 24.5], [-11.8, 24.5], [-11.8, 25.9], [-10.1, 25.9], [-10.1, 30.2], [28.9, 30.2], [28.9, 28.9], [41.6, 28.9], [41.6, 15.6], [45.6, 15.6], [45.5, -16.7], [42.9, -16.7], [42.9, -27], [40.7, -27], [40.7, -31], [-10.6, -31.1], [-10.6, -26.9], [-12.2, -26.9], [-12.2, -25.2], [-15.2, -25.2], [-15.2, -28.9], [-40.1, -28.9], [-50.3, 28.1], [-14.9, 28.1]]],
    levels: []
  },
  wtc4: {
    anchor: [-74.011994, 40.710316],
    B: 29.3,
    foot: [[[-31.5, -30.4], [-44.9, 25.2], [-31.6, 25.1], [-31.6, 29.7], [36.6, 29.6], [39.4, -30.4]]],
    levels: []
  },
  woolworth: {
    anchor: [-74.008315, 40.712451],
    B: 31,
    foot: [[[-31.6, -21.9], [-31.6, -5.8], [-2.8, -5.8], [-2.8, 6], [-31.6, 6], [-31.5, 21.9], [27, 21.9], [26.9, -21.9]]],
    levels: [
      [0, 120, [[-31.6, -21.9], [-31.6, -5.8], [-23.3, -5.8], [-2.8, -5.8], [-2.8, 6], [-31.6, 6], [-31.6, 18.2], [-31.5, 21.9], [12.6, 21.9], [27, 21.9], [27, -8.3], [26.9, -21.9], [21.1, -21.9], [9.1, -21.9]]],
      [120, 170, [[-2, -11.7], [-1.9, 10.5], [1.7, 14], [23.8, 14.1], [27.6, 10.6], [27.4, -11.7], [23.6, -15.2], [1.5, -15.3]]],
      [170, 194, [[0.6, -9.2], [0.6, 8.1], [4.1, 11.5], [21.4, 11.5], [24.7, 8.3], [24.7, -9.2], [21.2, -12.6], [4.1, -12.7]]]
    ]
  },
  flatiron: {
    anchor: [-73.989652, 40.741016],
    B: 6.1,
    foot: [[[3.8, 32.7], [6.6, 39.3], [7.7, 39.5], [8.1, 39], [8, 32.3], [8.8, 31.5], [9.5, 29.6], [9.5, -24.7], [8.6, -26.1], [6.7, -26.9], [-15.4, -17.6], [-16.5, -16.6], [-17.2, -14.8], [-16.8, -13], [2.3, 31.4]]],
    levels: []
  },
  rock30: {
    anchor: [-73.979651, 40.759166],
    B: 29.2,
    foot: [[[-60.5, 29.1], [79.2, 29], [79.1, 16.3], [81, 16.3], [80.9, -15.8], [79.1, -15.8], [79, -28], [-61.6, -28], [-61.6, -30.6], [-81.6, -30.6], [-81.5, 22.3], [-60.6, 22.3]]],
    levels: [
      [0, 10, [[-60.5, 29.1], [-41.5, 29.1], [26.2, 29.1], [32.5, 29.1], [79.2, 29], [79.1, 16.3], [81, 16.3], [80.9, -15.8], [79.1, -15.8], [79, -28], [77.7, -28], [77, -28], [68.1, -28], [52.7, -28], [9.8, -28], [-61.6, -28], [-61.6, -30.6], [-71.1, -30.6], [-81.6, -30.6], [-81.5, 22.3], [-69.1, 22.3], [-60.6, 22.3]]],
      [10, 20, [[-81, -24.4], [-81, 21.6], [-60.4, 21.7], [-60.1, 23.3], [66.5, 23.9], [66.5, 15], [76.8, 15], [76.9, 9.1], [81.6, 9], [81.5, -10.1], [76.9, -10.3], [76.8, -16.1], [66.6, -16.3], [66.6, -24.6]]],
      [20, 40, [[-81, -24.4], [-81, 21.6], [-60.4, 21.7], [-60.1, 23.3], [42.3, 23.8], [42.4, 14.8], [76.8, 15], [76.9, 9.1], [81.6, 9], [81.5, -10.1], [76.9, -10.3], [76.8, -16.1], [42.5, -16.4], [42.2, -24.4]]],
      [40, 45, [[-81, -24.4], [-81, 21.6], [-60.4, 21.7], [-60.1, 23.3], [16.8, 23.6], [17, 14.6], [76.8, 15], [76.9, 9.1], [81.6, 9], [81.5, -10.1], [76.9, -10.3], [76.8, -16.1], [17.1, -16.5], [16.8, -24.4]]],
      [45, 70, [[-18.6, 8.4], [-1.4, 8.5], [-1.2, 14.5], [72.2, 14.9], [72.3, 9], [81.6, 9], [81.5, -10.1], [72.3, -10.2], [72.2, -16.1], [-1.2, -16.6], [-1.4, -10.6], [-18.6, -10.7]]],
      [45, 70, [[-81, -24.4], [-81, 21.6], [-60.4, 21.7], [-60.2, 23.3], [-55.3, 23.4], [-55.4, -24.3]]],
      [70, 125, [[-18.6, 8.4], [-1.4, 8.5], [-1.2, 14.5], [72.2, 14.9], [72.3, 9], [81.6, 9], [81.5, -10.1], [72.3, -10.2], [72.2, -16.1], [-1.2, -16.6], [-1.4, -10.6], [-18.6, -10.7]]],
      [125, 175, [[-18.6, 8.4], [-1.4, 8.5], [-1.2, 14.5], [66.5, 14.9], [66.6, 9], [81.6, 9], [81.5, -10.1], [66.6, -10.3], [66.5, -16.2], [-1.2, -16.6], [-1.4, -10.6], [-18.6, -10.7]]],
      [175, 220, [[-18.6, 8.4], [-1.4, 8.5], [-1.2, 14.5], [59.3, 14.9], [59.6, 8.9], [79.1, 9], [79.1, -10.2], [59.7, -10.3], [59.5, -16.3], [-1.2, -16.6], [-1.4, -10.6], [-18.6, -10.7]]],
      [220, 235, [[-18.6, 8.4], [-1.4, 8.5], [-1.2, 14.5], [51.3, 14.8], [51.5, 8.9], [76.8, 9], [76.8, -10.2], [51.4, -10.3], [51.2, -16.3], [-1.2, -16.6], [-1.4, -10.6], [-18.6, -10.7]]],
      [235, 245, [[-18.6, 8.4], [-1.4, 8.5], [-1.2, 14.5], [51.3, 14.8], [51.5, 8.9], [72.2, 9], [72.2, -10.2], [51.4, -10.3], [51.2, -16.3], [-1.2, -16.6], [-1.4, -10.6], [-18.6, -10.7]]]
    ]
  },
  metlife_tower: {
    anchor: [-73.987358, 40.741276],
    B: 28.9,
    foot: [[[12.5, 11], [13.2, -10.8], [-13, -10.8], [-13, 11]]],
    levels: []
  },
  wall40: {
    anchor: [-74.009731, 40.707024],
    B: 38,
    foot: [[[23.7, 26.8], [29.6, -32.5], [-14.5, -31.8], [-17.6, 5.9], [-38.8, 5], [-39.4, 26.8]]],
    levels: [
      [0, 30, [[23.7, 26.8], [24.1, 23.7], [25.9, 4.8], [27.8, -14.4], [29.6, -32.5], [13.5, -32.2], [-13.3, -31.8], [-14.5, -31.8], [-14.6, -30.9], [-15.6, -18.5], [-16.5, -7.7], [-17.4, 3.3], [-17.6, 5.9], [-27.8, 5.5], [-38.8, 5], [-39.2, 22], [-39.4, 26.8], [-39.4, 26.8], [-31, 26.8], [-10.4, 26.8]]],
      [30, 40, [[-40.3, 26.4], [-6.2, 26.4], [-5.5, 21.6], [10.5, 22.1], [10.5, 26.3], [23.6, 26.2], [24.6, -9.9], [29.6, -10.1], [30.3, -33], [15.2, -32.7], [14.5, -26.3], [1, -26.5], [0.7, -32.2], [-15, -32], [-15.5, 4.5], [-39.8, 4]]],
      [40, 64, [[-40, 20.7], [23.9, 22.5], [24.6, -9.9], [29.6, -10.1], [30.3, -33], [15.2, -32.7], [14.5, -26.3], [1, -26.5], [0.7, -32.2], [-15, -32], [-15.2, -13.9], [-7.5, -13.5], [-7.8, 4.7], [-39.8, 4]]],
      [64, 75, [[-40.1, 17.9], [24, 20.1], [24.6, -9.9], [29.6, -10.1], [30.2, -26.2], [28.5, -26.3], [28.4, -28.6], [16.9, -28.7], [16.8, -26.4], [14.8, -26.3], [-1, -26.5], [-1.3, -28.9], [-12.8, -29], [-12.9, -26.7], [-15, -26.6], [-15.2, -13.9], [-7.5, -13.5], [-7.8, 4.7], [-39.8, 4]]],
      [75, 90, [[-40, 15.1], [24, 16.9], [24.6, -9.9], [29.6, -10.1], [30.2, -26.2], [-15, -26.6], [-15.2, -13.9], [-7.5, -13.5], [-7.8, 4.7], [-39.8, 4]]],
      [90, 100, [[-39.9, 12.7], [-12.8, 13.4], [-12.6, 9.6], [-8.3, 9.7], [-8.3, 15.9], [14.8, 16.6], [14.5, 11.5], [24.1, 11.7], [24.6, -9.9], [27.2, -10.1], [27, -20.4], [-12.4, -21.3], [-12.5, -13.8], [-7.5, -13.5], [-7.9, 4.8], [-39.8, 4]]],
      [100, 112, [[-12.7, 9.5], [-8.1, 9.8], [-8.2, 15.9], [14.8, 16.6], [14.5, 11.5], [24.1, 11.7], [24.6, -9.9], [27.2, -10.1], [27, -20.4], [-12.4, -21.3], [-12.5, -13.8], [-7.5, -13.4], [-7.8, 4.7], [-12.6, 4.8]]],
      [112, 123, [[-12.7, 9.5], [-8.2, 9.7], [-8, 10.9], [24.1, 11.7], [24.6, -9.9], [27.2, -10.1], [27, -20.4], [-12.4, -21.3], [-12.5, -13.8], [-7.5, -13.4], [-7.8, 4.7], [-12.6, 4.8]]],
      [123, 130, [[-12.7, 9.5], [-8.2, 9.7], [-8, 10.9], [24.1, 11.7], [24.6, -9.9], [27.2, -10.1], [27, -18.8], [-12.4, -19.7], [-12.5, -13.8], [-7.5, -13.4], [-7.8, 4.7], [-12.6, 4.8]]],
      [130, 212, [[-8, 10.9], [20.4, 11.6], [20.8, -16.7], [-7.5, -17.3]]],
      [212, 230, [[-6.7, 9.8], [19.6, 10.4], [20, -15.9], [-6.3, -16.5]]]
    ]
  },
  pine70: {
    anchor: [-74.007723, 40.706481],
    B: 39.4,
    foot: [[[39.4, -17], [-36.5, -21.1], [-36.8, 2], [-38.8, 1.9], [-38.9, 19.2], [39.4, 18.2]]],
    levels: [
      [0, 45, [[18.9, -18.1], [14.8, -18.4], [14.9, -18.3], [14.8, -18.3], [0.6, -19.1], [-15.6, -20], [-34, -21], [-36.5, -21.1], [-36.6, -11.1], [-36.8, 2], [-38.8, 1.9], [-38.9, 19.2], [-31.4, 19.1], [6.9, 18.6], [29, 18.4], [39.4, 18.2], [39.4, 16.1], [39.4, -17], [22.1, -17.9], [19, -18.1]]],
      [45, 50, [[-38.2, 15.2], [-1.2, 14.8], [-0.9, 18.1], [12.5, 17.9], [12.9, 15.3], [37.4, 15.9], [37.9, -15.9], [13.7, -17.2], [13.5, -19], [0.1, -19.8], [-0.3, -17.6], [-35.8, -19.3], [-36.2, 2.7], [-38, 2.9]]],
      [50, 60, [[-38.1, 12.3], [-1.1, 12.3], [-0.9, 14.8], [37.4, 15.9], [37.9, -15.9], [-0, -17.6], [-0.4, -14.9], [-35.9, -16.9], [-36.2, 2.7], [-38, 2.9]]],
      [60, 65, [[-38.1, 12.3], [-1.1, 12.3], [-0.9, 14.8], [12.6, 15.3], [12.9, 12.7], [35, 13.4], [35.5, -13.7], [13.7, -14.5], [13.5, -17.2], [-0, -17.6], [-0.4, -14.9], [-35.9, -16.9], [-36.2, 2.7], [-38, 2.9]]],
      [65, 70, [[-38.1, 12.3], [-1.1, 12.3], [-0.9, 14.8], [12.6, 15.3], [13, 10.4], [32.5, 11.2], [33.1, -11.8], [13.6, -12.3], [13.5, -17.2], [-0, -17.6], [-0.4, -14.9], [-35.9, -16.9], [-36.2, 2.7], [-38, 2.9]]],
      [70, 75, [[-38.1, 10], [-1, 10], [-0.8, 13.1], [12.6, 13.5], [13, 10.4], [32.5, 11.2], [33.1, -11.8], [13.6, -12.3], [13.4, -15.4], [-0.1, -15.8], [-0.4, -12.7], [-35.9, -14.6], [-36.2, 2.7], [-38, 2.9]]],
      [75, 80, [[-38.1, 7.8], [-6.9, 7.2], [-5.1, 10], [-0.8, 10.1], [-0.8, 13.1], [12.7, 13.5], [13, 10.4], [32.5, 11.2], [33.1, -11.8], [13.6, -12.3], [13.4, -15.4], [-0.1, -15.8], [-0.2, -12.8], [-4.5, -13], [-6.4, -10.3], [-35.9, -12.2], [-36.2, 2.7], [-38, 2.9]]],
      [80, 90, [[-38.1, 7.8], [-6.9, 7.2], [-5.1, 10], [-1, 10], [-0.8, 11.2], [12.7, 11.7], [13, 10.4], [17.1, 10.7], [19, 8], [30.4, 8.6], [30.9, -9.4], [19.5, -9.5], [17.7, -12.2], [13.6, -12.3], [13.4, -13.6], [-0.1, -14], [-0.4, -12.7], [-4.5, -13], [-6.5, -10.3], [-35.9, -12.2], [-36.2, 2.7], [-38, 2.9]]],
      [90, 100, [[-38, 5.6], [-13.2, 5.6], [-11.7, 7.3], [-6.8, 7.2], [-5.1, 10], [-1, 10], [-0.8, 11.2], [12.7, 11.7], [13, 10.4], [17.1, 10.7], [19, 8], [25.1, 7.4], [25.3, 3.9], [27.8, 3.9], [28.1, -4.7], [25.6, -5], [24.3, -9.6], [19.4, -9.5], [17.7, -12.2], [13.6, -12.3], [13.4, -13.6], [-0.1, -14], [-0.4, -12.7], [-4.5, -13], [-6.3, -10.3], [-11.2, -10.8], [-12.8, -9.2], [-36, -10], [-36.2, 2.7], [-38, 2.9]]],
      [100, 112, [[-36.2, 3], [-13.2, 3.2], [-11.7, 7.3], [-6.8, 7.2], [-5.1, 10], [12.7, 11.7], [13, 10.4], [17.1, 10.7], [19, 8], [25.1, 7.4], [25.3, 3.9], [27.8, 3.9], [28.1, -4.7], [25.6, -5], [24.3, -9.6], [19.4, -9.5], [17.7, -12.2], [-0.1, -14], [-0.4, -12.7], [-4.5, -13], [-6.4, -10.3], [-11.2, -10.8], [-12.9, -6.7], [-36, -7.6]]],
      [112, 210, [[-13.8, 2], [-11.7, 7.3], [-6.8, 7.2], [-5.1, 10], [-1, 10], [-0.8, 11.2], [17.1, 10.7], [19, 8], [25.1, 7.4], [25.6, -8.5], [19.4, -9.5], [17.7, -12.2], [13.6, -12.3], [13.4, -13.6], [-4.5, -13], [-6.3, -10.3], [-12.5, -9.7]]],
      [210, 220, [[-13.8, 2], [-10.5, 2.2], [-9.1, 4.9], [-6.8, 5.1], [-6.7, 8.6], [-5.1, 10], [12.7, 11.7], [12.9, 10.4], [18.7, 9.4], [18.9, 5.9], [21.3, 5.9], [22.9, 3.2], [26.2, 3.3], [26.4, -4.4], [23.1, -4.5], [21.7, -7.3], [19.4, -7.4], [19.3, -11], [17.7, -12.2], [-0.1, -14], [-0.3, -12.7], [-6.1, -11.8], [-6.3, -8.3], [-8.7, -8.2], [-10.3, -5.6], [-13.6, -5.7]]],
      [220, 224, [[-10.1, -7.1], [-10.4, 3.7], [-6.7, 5.2], [-6.7, 8.6], [-5.1, 10], [12.7, 11.7], [13, 10.4], [17.1, 10.7], [18.7, 9.4], [19, 5.9], [22.7, 4.7], [23.5, -2.9], [23, -6.1], [19.3, -7.5], [19.3, -11], [17.7, -12.2], [-0.1, -14], [-0.4, -12.7], [-4.5, -13], [-6.1, -11.8], [-6.3, -8.3]]],
      [224, 234, [[-10.9, 0.6], [-9.1, 4.9], [-5.1, 5.1], [-3.6, 8.4], [-0.8, 8.6], [-0.8, 11.2], [12.7, 11.7], [12.8, 9], [15.7, 9], [17.3, 5.8], [22.7, 4.7], [23.5, -2.9], [21.7, -7.3], [17.7, -7.4], [16.3, -10.7], [13.4, -10.9], [13.4, -13.6], [-0.1, -14], [-0.2, -11.4], [-3.1, -11.4], [-4.7, -8.2], [-10.1, -7.1]]],
      [234, 238, [[-10.9, 0.6], [-7.1, 0.8], [-3.6, 8.4], [2.3, 8.6], [2.4, 11.3], [9.5, 11.6], [9.8, 8.9], [15.7, 9], [17.1, 7.8], [17.3, 4], [19.4, 3.9], [19.6, 1.6], [23.4, 1.7], [23.5, -2.9], [19.7, -3.1], [16.3, -10.7], [10.3, -10.9], [10.2, -13.7], [3.1, -13.9], [2.8, -11.2], [-3.1, -11.4], [-4.5, -10.1], [-4.7, -6.4], [-6.8, -6.3], [-7, -3.9], [-10.8, -4]]],
      [238, 242, [[-5, 7], [-3.6, 8.4], [8.5, 7.5], [9.6, 8.8], [15.7, 9], [17.1, 7.8], [16, -1.9], [17.4, -3.1], [17.6, -9.4], [16.3, -10.7], [4.1, -9.8], [3, -11.2], [-3.1, -11.4], [-4.5, -10.1], [-3.4, -0.4], [-4.8, 0.8]]],
      [242, 252.4, [[-1.3, 3], [-0, 4.5], [12, 4.9], [13.4, 3.6], [13.6, -5.4], [12.4, -6.8], [0.3, -7.2], [-1, -5.9]]]
    ]
  },
  citigroup: {
    anchor: [-73.969938, 40.75838],
    B: 29.2,
    foot: [[[-42.2, 23.9], [-17.7, 24.1], [-17.8, 26.4], [60.7, 27.1], [60.9, -3.6], [32.4, -3.9], [32.6, -33.6], [1.3, -33.9], [1.3, -31.6], [-44.9, -32], [-45.2, 9.9], [-57.1, 9.8], [-62.8, 14.4], [-62.8, 24.8], [-60.5, 26.9], [-45.3, 27.1]]],
    levels: []
  },
  park432: {
    anchor: [-73.971802, 40.761511],
    B: 28.7,
    foot: [[[3.5, 38.3], [3.8, -3.3], [50.8, -1.9], [50.3, -22.8], [-32.8, -22.9], [-32.9, 7.7], [-25.7, 7.6], [-25.4, 38.3]], [[-25.7, 7.6], [-32.9, 7.7], [-33, 38.3], [-25.4, 38.3]]],
    levels: []
  },
  vanderbilt1: {
    anchor: [-73.97855, 40.752973],
    B: 29,
    foot: [[[-32.9, -30.4], [-32.7, 30.5], [32.9, 30.5], [32.7, -30.5]]],
    levels: [
      [0, 75, [[-32.9, -30.4], [-32.7, 30.5], [32.9, 30.5], [32.7, -30.5]]],
      [75, 315, [[-29.4, -24.2], [-26.8, -24], [-26.7, 19.7], [-17, 19.8], [-16.9, 25.7], [16.7, 26.5], [17, 27.6], [23.8, 27.7], [24.1, 25.1], [33, 25.2], [33.4, -20.4], [29.5, -20.6], [29.6, -29.7], [-29.4, -30.4]]],
      [315, 330, [[-16.9, 25.7], [16.7, 26.5], [17, 27.6], [23.8, 27.7], [24.1, 25.1], [33, 25.2], [33.4, -20.4], [29.5, -20.4], [13.2, -15.2], [1.4, -15.2], [2.5, -14.5], [2.3, -9], [-12.8, -9.6], [-12.7, 15.8], [-16.8, 19.8]]],
      [330, 350, [[-16.9, 25.7], [16.7, 26.5], [17, 27.6], [23.8, 27.7], [23.8, 25.1], [7.7, 17.9], [7.7, 14.1], [14.2, 14], [14, -3.4], [6.5, -3.2], [6.3, -7.5], [7.5, -8.6], [-12.8, -9.6], [-12.7, 15.8], [-16.8, 19.8]]],
      [350, 396.5, [[-2.9, -2.9], [-2.5, 13.9], [14.2, 14], [14, -3.4]]]
    ]
  },
  cpt: {
    anchor: [-73.981011, 40.76643],
    B: 28.6,
    foot: [[[28.7, -31.7], [-16.8, -31.7], [-16.7, -17], [-46.3, -16.8], [-46, -1.4], [-30.3, -1.4], [-30.2, 29.5], [29.2, 29.9], [29.1, 16.4], [37.6, 16.5], [37.4, -8.5], [28.9, -8.4]]],
    levels: [
      [0, 23, [[-30.1, -17.6], [-29.7, 28.2], [29.8, 27.9], [29.3, -32.7], [-16.2, -32.4], [-16.2, -17.8]]],
      [23, 44, [[-30.1, -17.6], [-29.8, 23.4], [29.7, 23.1], [29.3, -32.7], [-16.2, -32.4], [-16.2, -17.8]]],
      [44, 89, [[-11.8, 8.5], [-11.8, 20.3], [29.7, 20.6], [29.4, -17.3], [7.1, -17.1], [7.1, 8.4]]],
      [89, 127, [[-11.8, 8.5], [-11.8, 20.3], [38, 20.2], [38, -8.5], [29.6, -8.5], [29.4, -17.3], [7.1, -17.1], [7.1, 8.4]]],
      [127, 163, [[-11.8, 8.5], [-11.8, 20.3], [38, 20.2], [38, -8.5], [7.2, -9], [7.1, 8.4]]],
      [163, 237, [[7.2, -9], [7.2, 20.4], [38, 20.2], [38, -8.5]]],
      [237, 332, [[7.2, -4.2], [7.2, 16.7], [10.3, 16.8], [10.3, 20.5], [29.7, 20.6], [29.9, 17.6], [38, 17.7], [38, -8.5], [10.3, -9], [10.2, -4.3]]],
      [332, 342, [[7.2, -4.2], [7.2, 15.7], [11.9, 15.9], [12, 20.5], [29.7, 20.6], [29.8, 15.4], [38, 15.5], [38, -8.5], [10.3, -9], [10.2, -4.3]]],
      [342, 433, [[7.2, -4.2], [7.2, 15.7], [11.9, 15.9], [12, 20.5], [29.7, 20.6], [29.8, 15.4], [38, 15.5], [38, -1.7], [33.2, -1.9], [33.1, -8.4], [10.3, -9], [10.2, -4.3]]],
      [433, 466, [[7.2, -4.2], [7.2, 15.7], [11.9, 15.9], [12, 20.5], [29.7, 20.6], [29.5, -8.9], [10.3, -9], [10.2, -4.3]]],
      [466, 472, [[7.2, -4.2], [7.2, 15.7], [11.9, 15.9], [12, 20.5], [29.7, 20.6], [29.5, -8.9], [10.3, -9], [10.2, -4.3]]],
      [466, 472, [[16.9, 9.4], [23.3, 9.5], [23.4, -1.7], [17, -1.8]]]
    ]
  },
  w57_111: {
    anchor: [-73.97756, 40.764957],
    B: 29.2,
    foot: [[[15.2, 30.6], [15.2, -30.5], [-15.2, -30.6], [-15.2, 30.5]]],
    levels: [
      [0, 30, [[-2.2, 11.1], [15.9, 11.3], [16.1, -31.1], [1.9, -31.3], [1.8, -13.9], [-2.1, -13.7]]],
      [30, 200, [[-2.2, 11.1], [15.9, 11.3], [16, -13.4], [-2.1, -13.7]]],
      [200, 248, [[-2.2, 11.1], [15.9, 11.3], [16, -11.7], [-2.1, -12]]],
      [248, 283, [[-2.2, 11.1], [15.9, 11.3], [16, -10], [-2.1, -10.2]]],
      [283, 308, [[-2.2, 11.1], [15.9, 11.3], [16, -8.3], [-2.1, -8.5]]],
      [308, 328, [[-2.2, 11.1], [15.9, 11.3], [16, -6.6], [-2.1, -6.8]]],
      [328, 343, [[-2.2, 11.1], [15.9, 11.3], [16, -4.9], [-2.1, -5.1]]],
      [343, 358, [[-2.2, 11.1], [15.9, 11.3], [16, -3.2], [-2.2, -3.4]]],
      [358, 373, [[-2.2, 11.1], [15.9, 11.3], [16, -1.5], [-2.2, -1.7]]],
      [373, 383, [[-2.2, 11.1], [15.9, 11.3], [15.9, 0.2], [-2.2, 0]]],
      [383, 393, [[-2.2, 11.1], [15.9, 11.3], [15.9, 1.9], [-2.2, 1.7]]],
      [393, 405, [[-2.2, 11.1], [15.9, 11.3], [15.9, 3.6], [-2.2, 3.4]]],
      [405, 417, [[-2.2, 11.1], [15.9, 11.3], [15.9, 5.3], [-2.2, 5.1]]],
      [417, 435, [[-2.2, 11.1], [15.9, 11.3], [15.9, 7], [-2.2, 6.8]]]
    ]
  },
  hy30: {
    anchor: [-74.00091, 40.753522],
    B: 29.6,
    foot: [[[-52.2, -64], [-61, -64.4], [-52.4, 78.4], [14.9, 81.3], [15, 79.8], [23.7, 80.9], [24.5, 83.1], [55.9, 83.1], [55.8, -79.3], [-50.5, -79.8], [-50.2, -77.2], [-55.1, -77.1]]],
    levels: [
      [0, 10, [[-55.4, 36.6], [-52.6, 78.8], [-2.3, 81.1], [15.7, 80.4], [29.9, 81.9], [30.1, 83.6], [56.4, 83.3], [56.4, 72.2], [53.6, 69.2], [53.8, 67.2], [55.5, 67.1], [55.9, 42.6], [50.6, 42.5], [50.4, 26], [-49.3, 24.4], [-49.5, 36.6]]],
      [10, 133, [[-55.4, 36.6], [-52.6, 78.8], [52.5, 82.2], [38.6, 67.7], [55.5, 67.1], [55.9, 42.6], [50.6, 42.5], [50.4, 26], [-49.3, 24.4], [-49.5, 36.6]]],
      [133, 140, [[-55.4, 36.6], [-52.6, 78.8], [-2.3, 81.1], [22.9, 80.9], [23, 65.8], [17.7, 65.4], [17.6, 25.5], [-49.3, 24.4], [-49.5, 36.6]]],
      [140, 310, [[-55.4, 36.6], [-52.6, 78.8], [10.6, 81], [10.7, 74.3], [17.8, 74.2], [17.6, 25.5], [-49.3, 24.4], [-49.5, 36.6]]],
      [310, 335, [[-55.4, 36.6], [-52.7, 78.8], [10.6, 81], [10.7, 74.2], [-14.4, 74], [-14.8, 38.9], [-49.2, 39.3], [-49.4, 36.8]]],
      [335, 340, [[-55.4, 36.6], [-52.7, 78.8], [10.6, 81], [10.7, 74.2], [-14.3, 74.1], [-14.5, 66.9], [-10.7, 70], [10.5, 34.9], [-46.1, 34.2], [-41.9, 39.2], [-49.2, 39.3], [-49.4, 36.8]]],
      [340, 387.1, [[-55.4, 36.6], [-52.7, 78.8], [10.6, 81], [10.7, 74.2], [-14.4, 74], [-14.8, 38.9], [-49.2, 39.3], [-49.4, 36.8]]]
    ]
  },
  boa: {
    anchor: [-73.984707, 40.755566],
    B: 29.3,
    foot: [[[-65.2, -27.1], [-65.1, 30.3], [64.6, 30.3], [64.4, -30.6], [-54.2, -30.6], [-54.2, -27.1]]],
    levels: [
      [0, 15, [[-65.2, -27.1], [-65.1, 12.3], [-65.1, 30.3], [-44.7, 30.3], [2.9, 30.3], [26.3, 30.3], [64.6, 30.3], [64.4, -30.6], [28.9, -30.6], [-31.6, -30.6], [-54.2, -30.6], [-54.2, -27.1]]],
      [15, 30, [[-65.5, 29], [44.5, 29.5], [44.8, 26.3], [63.6, 26], [63.1, 1.3], [58.2, 1.1], [57.8, -25.1], [27.6, -24.7], [27.3, -31.6], [-65.3, -32.3]]],
      [30, 236, [[-11.7, -24.3], [-11.3, 2.2], [-7.6, 2.4], [-7.2, 26.8], [63.6, 26], [63.1, 1.3], [58.2, 1.1], [57.8, -25.1]]],
      [236, 240, [[-11.7, -24.3], [-11.3, 2.2], [-7.6, 2.4], [-7.2, 26.8], [63.6, 26], [63.1, 1.3], [58.2, 1.1], [57.8, -25.1]]],
      [240, 245, [[-11.7, -24.3], [-11.3, 2.2], [-7.6, 2.4], [-7.2, 26.8], [5.4, 26.7], [-7, 2.5], [53.8, 2], [51.2, 16.4], [63.6, 26], [63.1, 1.3], [58.2, 1.1], [57.8, -25.1]]],
      [240, 245, [[24.1, -4.8], [29.6, -4.8], [29.6, -9.3], [24.1, -9.4]]],
      [245, 250, [[-11.7, -24.3], [-11.3, 2.2], [-7.6, 2.4], [-7.2, 26.8], [5.4, 26.7], [-7.1, 2.5], [58.3, 1.4], [57.8, -25.1]]],
      [245, 250, [[24.1, -4.8], [29.6, -4.8], [29.6, -9.3], [24.1, -9.4]]],
      [250, 257, [[-11.7, -24.3], [-11.3, 2.2], [58.3, 1.4], [57.8, -25.1]]],
      [250, 257, [[24.1, -4.8], [29.6, -4.8], [29.6, -9.3], [24.1, -9.4]]],
      [257, 262, [[-11.7, -24.3], [0.9, -13.7], [44.4, -24.9], [57.7, 0.9], [2.5, 2], [58.3, 1.4], [57.8, -25.1]]],
      [257, 262, [[24.1, -4.8], [29.6, -4.8], [29.6, -9.3], [24.1, -9.4]]],
      [262, 279, [[2.4, 1.6], [58.3, 1.4], [57.8, -25.1], [44.5, -24.9], [57.6, 0.9]]],
      [262, 279, [[24.1, -4.8], [29.6, -4.8], [29.6, -9.3], [24.1, -9.4]]],
      [279, 366, [[24.1, -4.8], [29.6, -4.8], [29.6, -9.3], [24.1, -9.4]]]
    ]
  },
  nyt: {
    anchor: [-73.989691, 40.755922],
    B: 28.9,
    foot: [[[58.6, 27.3], [58.6, -28.3], [44.7, -28.4], [44.7, -27.1], [38.8, -27.1], [38.8, -29.6], [-13.6, -29.8], [-13.6, -20.2], [-29.5, -20.2], [-29.5, -29.1], [-47.8, -29.1], [-47.8, -21.3], [-62.3, -21.4], [-62.3, 23.9], [-48.5, 23.9], [-48.5, 29.2], [-30.3, 29.3], [-30.3, 23.6], [-14.8, 23.6], [-14.8, 28.2], [57.7, 28.5], [57.7, 27.3]]],
    levels: [
      [0, 25, [[58.6, 27.3], [58.6, 10.3], [58.6, 2.2], [58.6, -4.3], [58.6, -28.3], [57.7, -28.3], [44.7, -28.4], [44.7, -27.1], [38.8, -27.1], [38.8, -28.4], [38.8, -29.6], [11.9, -29.7], [-13.6, -29.8], [-13.6, -29], [-13.6, -20.2], [-14.8, -20.2], [-29.5, -20.2], [-29.5, -29.1], [-31.5, -29.1], [-47.8, -29.1], [-47.8, -21.3], [-62.3, -21.4], [-62.3, -7.7], [-62.3, 17.3], [-62.3, 23.9], [-48.5, 23.9], [-48.5, 29.2], [-30.3, 29.3], [-30.3, 23.6], [-14.8, 23.6], [-14.8, 24.9], [-14.8, 28.2], [34, 28.4], [57.7, 28.5], [57.7, 27.3]]],
      [25, 227, [[-62.8, 21.3], [-52.6, 21.3], [-52.4, 24.4], [-49.1, 24.5], [-49, 27.1], [-29.8, 27.1], [-29.7, 24.2], [-26.8, 24.1], [-26.7, 21.3], [-14.1, 21.3], [-13.7, -24.3], [-14.3, -20.7], [-28.8, -20.7], [-29.3, -29.5], [-47.8, -29.6], [-48.5, -21.9], [-62.7, -21.7]]],
      [227, 232, [[-49.1, -17.3], [-49, 12.5], [-42.6, 12.6], [-42.5, 20.4], [-35.5, 20.5], [-35.5, 12.7], [-28.4, 12.6], [-28.5, -17.2], [-35.5, -17.3], [-35.6, -25.3], [-42.6, -25.3], [-42.6, -17.3]]]
    ]
  },
  spruce8: {
    anchor: [-74.005612, 40.710907],
    B: -38.8,
    foot: [[[-20, -32.1], [-25.9, -33.2], [-25.9, 26.3], [-21.3, 26.3], [-21.3, 27.6], [28.9, 25.5], [28.8, -18.5]]],
    levels: [
      [0, 26, [[-20, -32.1], [-25.9, -33.2], [-25.9, 26.3], [-21.3, 26.3], [-21.3, 27.6], [28.9, 25.5], [28.8, -18.5]]],
      [26, 29, [[-20.3, 25.4], [23.9, 24.9], [24.4, -20.3], [-19.5, -32.6]]],
      [29, 32.5, [[-20.3, 25.4], [0.1, 25.5], [0.4, 12], [24, 12.1], [24.4, -20.3], [-19.5, -32.6]]],
      [32.5, 37, [[-20.3, 25.4], [0.1, 25.5], [0.4, 12], [24, 12.1], [24.3, -6.2], [20.7, -6.5], [20.9, -17.3], [-0.6, -17.9], [-0.8, -26.7], [-19.7, -26.8]]],
      [37, 90, [[-20.3, 25.4], [0.1, 25.5], [0.4, 12], [24, 12.1], [24.3, -6.2], [-1, -6.5], [-0.8, -26.7], [-19.7, -26.8]]],
      [90, 140, [[-20.3, 23.3], [0.1, 23.4], [0.4, 12], [24, 12.1], [24.3, -6.2], [-0.8, -6.4], [-0.8, -21.9], [-19.8, -22]]],
      [140, 180, [[-20.3, 21.3], [0.1, 21.4], [0.5, 12], [22.5, 12.1], [22.8, -6.2], [-0.8, -6.4], [-0.9, -19], [-19.8, -19.1]]],
      [180, 265.2, [[-20.3, 21.3], [0.1, 21.4], [0.4, 12], [20.4, 12.1], [20.6, -6.2], [-0.8, -6.4], [-0.9, -15.5], [-19.8, -15.6]]]
    ]
  },
  hearst: {
    anchor: [-73.983624, 40.766572],
    B: 29.1,
    foot: [[[29.8, 25.5], [29.8, -25.7], [26.3, -29], [4.5, -29.1], [4.5, -30.4], [-29.4, -30.5], [-29.3, 29.9], [26.3, 30]]],
    levels: []
  },
  leonard56: {
    anchor: [-74.0063, 40.717657],
    B: 30.7,
    foot: [[[7.1, -12.7], [7.1, -17.6], [-22.3, -17.2], [-21.8, 12.1], [-15.6, 12], [-15.5, 16.5], [22.7, 16.6], [22.7, -12.6]]],
    levels: []
  },
  hy10: {
    anchor: [-74.001525, 40.752686],
    B: 28.9,
    foot: [[[-35.9, 26.8], [35.1, 26.7], [35.1, 22], [39.5, 22], [39.3, -26], [-35.1, -26], [-49, 1.5], [-31.4, 0.3], [-32.2, 4.8], [-36.5, 5.9]]],
    levels: [
      [0, 105, [[-35.9, 26.8], [35.1, 26.7], [35.1, 22], [39.5, 22], [39.3, -26], [-35.1, -26], [-49, 1.5], [-31.4, 0.3], [-32.2, 4.8], [-36.5, 5.9]]],
      [105, 120, [[-39.5, 26.7], [35.3, 26.2], [35.4, 16.9], [40.1, 16.8], [40.1, -8.7], [21.5, -27.3], [-16.9, -27.2], [-17, -20.6], [-29.2, -20.7], [-29.7, 0.3], [-39.5, 0.3]]],
      [120, 165, [[-39.5, 26.7], [35.3, 26.2], [35.4, 16.9], [40.1, 16.8], [40, -23.6], [36.1, -27.1], [-16.9, -27.2], [-17, -20.6], [-29.2, -20.7], [-29.6, 0.2], [-39.5, 0.3]]],
      [165, 240, [[-16.9, -27.2], [-16.8, -20.5], [-10.9, -20.2], [-10.5, 16.5], [-5.1, 16.6], [-4.2, 26.5], [35.3, 26.2], [35.4, 16.9], [40.1, 16.8], [40, -23.6], [36.1, -27.1]]],
      [240, 267.6, [[-16.9, -27.2], [-16.8, -20.5], [-10.9, -20.2], [-10.5, 16.5], [-5.1, 16.5], [4, 14], [35.1, 14.6], [35.3, 16.7], [40.1, 16.8], [40, -23.6], [36.1, -27.1]]]
    ]
  },
  vessel: {
    anchor: [-74.002161, 40.753803],
    B: -15.8,
    foot: [[[-5.4, -22.1], [0.2, -4], [-1.1, -3.3], [-1.8, -3.5], [-8.2, -21.3], [-9, -21], [-14.6, -17.8], [-18.9, -13.3], [-20.4, -10.9], [-22.2, -6], [-22.8, -1.9], [-22.6, 3.5], [-21.7, 7.3], [-20.1, 11.1], [-17, 15.4], [-12.7, 19.1], [-7.1, 21.8], [-2.9, 22.8], [1.2, 23], [6.4, 22.1], [11.7, 19.8], [17.2, 15.4], [20.9, 9.9], [22.8, 3.7], [22.9, -3.3], [20.4, -10.9], [15.8, -16.8], [10.5, -20.5], [3.5, -22.7], [-3.2, -22.7]], [[-5.4, -22.1], [-8.2, -21.3], [-1.8, -3.5], [-1.1, -3.3], [0.2, -4.3]]],
    levels: []
  },
  un_secretariat: {
    anchor: [-73.968101, 40.748928],
    B: 29.2,
    foot: [[[10.5, 43.1], [10.5, -43], [-10.4, -43.1], [-10.5, 43]]],
    levels: []
  },
  lever: {
    anchor: [-73.972873, 40.759615],
    B: 29,
    foot: [[[-19.5, -33.2], [-19.4, -5], [-31.4, -5], [-31.3, 27.3], [27.2, 27.3], [27.1, -33.2]]],
    levels: [
      [0, 15, [[-30.9, -5.7], [-30.8, 26.5], [27.8, 26.6], [27.7, -33.9], [-18.9, -34], [-18.9, -5.9]]],
      [15, 93.6, [[-23.7, 9.9], [-19, 10], [-18.9, 13.5], [27.3, 13.8], [27.3, -2.6], [-18.8, -3], [-19, 0.5], [-23.6, 0.5]]]
    ]
  },
  seagram: {
    anchor: [-73.971977, 40.758387],
    B: 28.7,
    foot: [[[27.6, 30], [27.6, -30.2], [2.3, -30.3], [2.3, -12.6], [1.7, -13.2], [-6.2, -13.2], [-6.2, -21.2], [-6.9, -21.5], [-31.9, -21.6], [-32.6, -20.9], [-32.6, 21.3], [-31.8, 21.8], [-6.5, 21.8], [-5.9, 21.2], [-5.9, 13.4], [1.8, 13.4], [2.3, 12.9], [2.3, 29.9]]],
    levels: [
      [0, 20, [[27.6, -0.4], [27.6, -30.2], [21, -30.2], [2.3, -30.3], [2.3, -12.6], [1.7, -13.2], [-5.5, -13.2], [-6.2, -13.2], [-6.2, -21.2], [-6.9, -21.5], [-31.9, -21.6], [-32.6, -20.9], [-32.6, 21.3], [-31.8, 21.8], [-20.2, 21.8], [-6.5, 21.8], [-5.9, 21.2], [-5.9, 13.4], [1.8, 13.4], [2.3, 12.9], [2.3, 29.9], [11.1, 29.9], [27.6, 30], [27.6, 24]]],
      [20, 40, [[-32.3, -22.7], [-32, 20.3], [-5.9, 20.3], [-5.7, 11.3], [29, 11], [28.9, -0.9], [30.6, -1.2], [30.6, -7.4], [28.3, -7.6], [28.2, -15.1], [-6.1, -14.8], [-6.4, -22.7]]],
      [40, 161.7, [[-32.3, -22.7], [-32, 20.3], [-5.9, 20.3], [-5.9, 11.4], [2.4, 11.3], [2.3, -14.8], [-6.3, -14.9], [-6.4, -22.7]]]
    ]
  },
  metlife_bldg: {
    anchor: [-73.976653, 40.753522],
    B: 29.2,
    foot: [[[-44.7, 55.3], [44.6, 55.6], [44.6, 54.8], [45.3, 54.8], [45.3, -40.6], [39.3, -40.6], [39.3, -57.2], [-39.4, -57.4], [-39.4, -41], [-44.2, -41], [-44.2, -40.6], [-45.2, -40.6], [-45.3, 54.6], [-44.7, 54.6]]],
    levels: [
      [0, 30, [[-44.7, 55.3], [-36.4, 55.3], [-5.4, 55.4], [18.5, 55.5], [42.2, 55.6], [44.6, 55.6], [44.6, 54.8], [44.7, 54.8], [44.8, 54.8], [45.3, 54.8], [45.3, 42.3], [45.3, 14.4], [45.3, -12.5], [45.3, -39.2], [45.3, -40.6], [45.2, -40.6], [45.1, -40.6], [43.6, -40.6], [39.3, -40.6], [39.3, -41.1], [39.3, -41.1], [39.3, -46.5], [39.3, -56], [39.3, -56.5], [39.3, -56.5], [39.3, -57.1], [39.3, -57.2], [39.3, -57.2], [39.3, -57.2], [6.1, -57.3], [-28, -57.4], [-39.4, -57.4], [-39.4, -57.3], [-39.4, -41], [-40.1, -41], [-40.2, -41], [-44.2, -41], [-44.2, -41], [-44.2, -40.9], [-44.2, -40.6], [-45.2, -40.6], [-45.2, -35.8], [-45.2, -3.5], [-45.3, 31.2], [-45.3, 54.6], [-44.7, 54.6]]],
      [30, 38, [[-38.9, -33.8], [-38.7, 42.1], [39.3, 42.3], [39.1, -33.8], [31.3, -33.9], [31.1, -40.3], [-32.4, -40.5], [-32.5, -33.9]]],
      [38, 246, [[-44.9, 0.3], [-18.3, 8], [23.5, 8.3], [45.9, 1.6], [45.9, -27.7], [22.1, -33.8], [-18.5, -34.1], [-44.9, -27.3]]]
    ]
  },
  municipal: {
    anchor: [-74.003634, 40.712968],
    B: 35.5,
    foot: [[[26.9, 16.2], [26.9, -12.4], [25.5, -12.4], [25.5, -24.6], [23.9, -24.6], [-0.6, -58.7], [-0.6, -59.7], [-27.2, -59.8], [-27.2, -33.2], [-16.9, -33.1], [-10.8, -24.7], [-10.8, 23.4], [-16.9, 31.9], [-27.2, 31.9], [-27.2, 58.3], [-0.1, 58.4], [-0.1, 57], [24, 28.6], [25.7, 28.6], [25.7, 16.2]]],
    levels: [
      [0, 107, [[26.9, 8.2], [26.9, -4], [26.9, -12.4], [25.5, -12.4], [25.5, -24.6], [23.9, -24.6], [10.4, -43.4], [-0.6, -58.7], [-0.6, -59.7], [-27.2, -59.8], [-27.2, -43.1], [-27.2, -33.2], [-16.9, -33.1], [-10.8, -24.7], [-10.8, -6.6], [-10.8, -4.8], [-10.8, 6.6], [-10.8, 23.4], [-15.9, 30.5], [-16.9, 31.9], [-24.8, 31.9], [-27.2, 31.9], [-27.2, 40.3], [-27.2, 40.3], [-27.2, 58.3], [-26.7, 58.3], [-21.9, 58.4], [-0.1, 58.4], [-0.1, 57], [7.2, 48.3], [16.1, 37.9], [24, 28.6], [25.7, 28.6], [25.7, 16.2], [26.9, 16.2], [26.9, 12.5]]],
      [107, 113, [[-10.8, 12.3], [14.9, 14.4], [14.9, 6.8], [14, 6.4], [14.8, -12.2], [-10.8, -14]]],
      [107, 113, [[-23.6, -56.7], [-23.6, -36.7], [-4.3, -36.6], [-4.4, -56.6]]],
      [107, 113, [[-23.7, 34.7], [-23.7, 54.8], [-4.4, 54.9], [-4.4, 34.8]]],
      [113, 123, [[-10.8, 12.3], [14.9, 14.4], [14.9, 6.8], [14, 6.4], [14.8, -12.2], [-10.8, -14]]],
      [123, 135, [[8.4, -7.8], [10.2, -5.9], [12.8, -5.8], [14.6, -7.5], [14.6, -10.1], [13.2, -12], [10.1, -12.1], [8.5, -10.4]]],
      [123, 135, [[8, 11.6], [9.9, 13.5], [12.5, 13.6], [14.3, 11.9], [14.3, 9.6], [12.6, 7.6], [9.9, 7.2], [8.1, 9]]],
      [123, 135, [[-10.5, -9.2], [-8.6, -7.3], [-5.7, -7], [-7.3, -5.4], [-5.4, -3.3], [-5.4, 2.9], [-7, 4.4], [-5.7, 6], [-8.2, 6], [-9.9, 7.6], [-10, 10.3], [-8.2, 12.2], [-5.6, 12.3], [-3.8, 10.6], [-3.7, 8.2], [-1.7, 7.3], [4.9, 7.9], [6.5, 9.5], [10.7, 5.7], [9.5, 4.2], [10.6, -4.6], [6.6, -8.7], [5.5, -7.6], [-1.4, -7.5], [-3.1, -9.3], [-5.3, -7.4], [-4.4, -11.4], [-5.9, -13.3], [-8.5, -13.4], [-10.4, -11.9]]],
      [135, 144, [[-7.3, -5.4], [-5.4, -3.3], [-5.4, 2.9], [-7, 4.4], [-3, 8.5], [-1.6, 7.3], [4.8, 7.8], [6.5, 9.5], [10.7, 5.7], [9.5, 4.2], [10.6, -4.6], [6.6, -8.7], [5.5, -7.6], [-1.4, -7.5], [-3.1, -9.3]]],
      [144, 149, [[-7.3, -5.4], [-5.4, -3.3], [-5.4, 2.9], [-7, 4.4], [-3, 8.5], [-1.6, 7.3], [4.8, 7.8], [6.5, 9.5], [10.7, 5.7], [9.5, 4.2], [10.6, -4.6], [6.6, -8.7], [5.5, -7.6], [-1.4, -7.5], [-3.1, -9.3]]],
      [149, 164.8, [[-4.3, -0.8], [-3.2, 3.7], [2.8, 6.6], [7.1, 4.8], [9.1, 0.7], [7.9, -3.8], [1.9, -6.8], [-2.3, -4.9]]],
      [164.8, 176.8, [[-2.3, -0.6], [-1.6, 2.5], [0.9, 4.4], [5.4, 3.3], [6.8, 0.5], [6.1, -2.5], [2, -4.6], [-0.9, -3.4]]]
    ]
  },
  parkrow: {
    anchor: [-74.007777, 40.71118],
    B: -18.8,
    foot: [[[14.2, 22.2], [14.4, -23.5], [0.6, -29.5], [-3.5, -23.1], [-1.8, -22], [-1.9, -8], [-4.6, -9.8], [-5.3, -8.7], [-13.2, -13.8], [-12.5, -14.9], [-17.6, -18.2], [-21.1, -12.9], [-18.1, -10.5], [-18.1, 1.1], [-2.5, 1.1], [-2.5, 8.9], [-18.1, 8.9], [-18.2, 22.2]]],
    levels: []
  },
  nylife: {
    anchor: [-73.985584, 40.742754],
    B: 29,
    foot: [[[62.7, -29.5], [-62.8, -29.5], [-62.7, 29.6], [62.8, 29.6]]],
    levels: [
      [0, 22, [[62.7, -29.5], [62.7, -29.5], [44.3, -29.5], [38.8, -29.5], [-24.6, -29.5], [-39.5, -29.5], [-62.8, -29.5], [-62.8, -29.2], [-62.8, -1.1], [-62.7, 29.6], [-41.7, 29.6], [29.6, 29.6], [37, 29.6], [50.6, 29.6], [62.8, 29.6], [62.8, 25.2]]],
      [22, 60, [[-57.7, -25.1], [-57.4, 21.6], [-35, 21.6], [-34.8, 15.9], [-24.4, 15.8], [-24.1, 21.8], [24, 21.8], [24.3, 15.9], [35.3, 15.9], [35.5, 21.7], [56.2, 21.7], [56, -24.9], [35.1, -24.9], [35, -19.3], [24.1, -19.2], [23.7, -25], [-24.2, -25], [-24.4, -19.3], [-34.9, -19.2], [-35.2, -25.1]]],
      [60, 115, [[-35.2, -12.3], [-35.1, 8.9], [-16.7, 9], [-16.5, 15.9], [16.3, 16], [16.5, 9.1], [35.3, 9.1], [35.2, -12.4], [16.4, -12.4], [16.1, -19], [-16.6, -19.1], [-16.8, -12.3]]],
      [115, 148, [[-16.6, -19.1], [-16.5, 15.9], [16.3, 16], [16.1, -19]]],
      [148, 187.5, [[-12.2, 3.4], [-5.1, 10.5], [5, 10.4], [11.7, 3.2], [11.3, -6.5], [4.7, -13.3], [-5, -13.4], [-12.1, -6.4]]]
    ]
  },
  williamsburgh: {
    anchor: [-73.977718, 40.685517],
    B: -6.3,
    foot: [[[13.7, 29.9], [13.7, -18.5], [14.8, -18.5], [14.8, -29.5], [-13.9, -29.5], [-13.9, 26.8], [-12.7, 26.8], [-12.7, 30]]],
    levels: [
      [0, 10, [[13.7, 19.9], [13.7, 5.9], [13.7, -18.5], [14.8, -18.5], [14.8, -29.5], [-13.9, -29.5], [-13.9, -28], [-13.9, -7.9], [-13.9, 26.8], [-12.7, 26.8], [-12.7, 30], [-1.7, 29.9], [13.7, 29.9]]],
      [10, 24, [[-14.6, 26.5], [-13.4, 26.7], [-13.4, 29.5], [9.1, 29.7], [9.8, -19.3], [14.8, -19.5], [14.9, -30.5], [-14.3, -30.7]]],
      [24, 60, [[-14.6, 26.5], [-13.4, 26.7], [-13.4, 29.5], [6.9, 29.7], [7, 14.9], [9.2, 14.6], [9.8, -19.3], [14.8, -19.5], [14.9, -30.5], [-7.4, -29.6], [-7.7, -30.7], [-14.3, -30.7], [-14.4, -19.4], [-11.6, -19.1], [-12.1, 14.7], [-14.6, 15]]],
      [60, 69, [[-14.6, 26.5], [-13.4, 26.7], [-13.4, 29.5], [6.9, 29.7], [8.7, -19.3], [14.8, -19.5], [14.9, -30.5], [-7.4, -29.6], [-7.7, -30.7], [-14.3, -30.7], [-14.4, -19.4], [-11.6, -19.1], [-12.1, 14.7], [-14.6, 15]]],
      [69, 80, [[-10.7, 20.9], [-8.5, 21.1], [-8.5, 28.3], [6.9, 29.7], [6.9, 25.1], [4.6, 24.9], [4.7, 14.9], [8.1, 14.6], [8.7, -19.3], [14.8, -19.5], [14.9, -25.1], [4, -25.3], [3.8, -28.8], [-7.8, -28.8], [-7.9, -25.3], [-10.1, -25.1]]],
      [80, 85, [[-10.5, 3.7], [-8.3, 4], [-8.5, 20.9], [-6.3, 21], [-6.3, 23.5], [-0.3, 23.5], [-0.2, 29.6], [6.9, 29.7], [6.9, 25.1], [4.6, 24.8], [4.7, 14.8], [7, 14.6], [7.5, -19.3], [14.8, -19.5], [14.9, -23.4], [4, -23.6], [3.8, -25.2], [-7.8, -25.2], [-8, -8.9], [-10.4, -8.7]]],
      [85, 110, [[-10.5, 3.7], [-8.3, 4], [-8.4, 10.6], [3.3, 10.7], [3.4, 4], [5.9, 3.9], [6.1, -8.5], [3.6, -8.8], [3.7, -15], [-7.9, -15.2], [-8.1, -8.9], [-10.4, -8.7]]],
      [110, 115, [[-10.5, 3.7], [-8.3, 4], [-8.4, 10.6], [3.3, 10.7], [3.4, 4], [5.9, 3.9], [6.1, -8.5], [3.6, -8.8], [3.7, -15], [-7.9, -15.2], [-8.1, -8.9], [-10.4, -8.7]]],
      [115, 140, [[-8.2, 3.3], [3.4, 3.5], [3.6, -8.2], [-8, -8.4]]],
      [140, 145, [[-8.2, 0.3], [-5.6, 3.4], [-0.1, 3.5], [3.4, 0.6], [3.5, -5.1], [0.7, -8.2], [-4.7, -8.3], [-8, -5.4]]],
      [145, 156, [[-7.6, -2], [-5.8, 1.6], [-2, 2.9], [1.4, 1.3], [2.9, -1.9], [2, -5.3], [-2.7, -7.5], [-6.3, -5.8]]]
    ]
  },
  courtsq: {
    anchor: [-73.943869, 40.747013],
    B: 14.1,
    foot: [[[-30.9, -3.4], [-30.9, 3.4], [-25.2, 3.4], [-25.2, 16.4], [-20.5, 16.4], [-20.5, 21], [-16, 21], [-15.9, 25.6], [17, 25.5], [17, 21], [21.8, 21], [21.8, 16.4], [26.2, 16.4], [26.1, -16.5], [21.5, -16.5], [21.5, -21.1], [17.1, -21.1], [17.1, -25.6], [-16.1, -25.6], [-16.1, -21.2], [-20.8, -21.2], [-20.8, -16.3], [-25.3, -16.3], [-25.3, -3.4]]],
    levels: [
      [0, 170, [[-30.9, -3.4], [-30.9, 3.4], [-25.2, 3.4], [-25.2, 8], [-25.2, 16.4], [-20.5, 16.4], [-20.5, 21], [-16, 21], [-15.9, 25.6], [17, 25.5], [17, 21], [21.8, 21], [21.8, 16.4], [26.2, 16.4], [26.2, 13.5], [26.1, -16.5], [21.5, -16.5], [21.5, -21.1], [17.1, -21.1], [17.1, -25.6], [-16.1, -25.6], [-16.1, -21.2], [-20.8, -21.2], [-20.8, -16.3], [-25.3, -16.3], [-25.3, -3.4]]],
      [170, 177.5, [[-24.9, -12.5], [-24.9, 10.8], [-20.4, 10.9], [-20.3, 15.5], [-15.7, 15.6], [-15.6, 20.3], [-11.1, 20.4], [-11, 25], [13, 25], [13, 20.4], [17.6, 20.3], [17.6, 15.7], [22, 15.6], [22.2, 10.8], [26.5, 10.8], [26.5, -12.5], [22.1, -12.6], [21.9, -17.3], [17.5, -17.4], [17.4, -22], [12.9, -22.1], [12.8, -26.7], [-11.1, -26.8], [-11.1, -22.2], [-15.7, -22], [-15.8, -17.3], [-20.3, -17.3], [-20.4, -12.6]]],
      [177.5, 185, [[-20.3, -12.5], [-20.3, 10.8], [-15.7, 10.9], [-15.6, 15.5], [-11.1, 15.7], [-11.1, 20.3], [12.9, 20.3], [13.1, 15.6], [17.5, 15.6], [17.6, 10.9], [22, 10.8], [22, -12.5], [17.5, -12.6], [17.4, -17.3], [12.9, -17.4], [12.8, -22], [-11.1, -22], [-11.2, -17.3], [-15.7, -17.3], [-15.8, -12.6]]],
      [185, 192.5, [[-15.7, -12.5], [-15.6, 10.8], [-11.2, 10.8], [-11.1, 15.5], [13, 15.5], [13, 10.8], [17.5, 10.8], [17.4, -12.5], [12.9, -12.6], [12.8, -17.2], [-11.1, -17.3], [-11.2, -12.6]]],
      [192.5, 200, [[-11.1, -12.5], [-11.1, 10.8], [13, 10.7], [12.8, -12.5]]]
    ]
  },
  un_ga: {
    anchor: [-73.967464, 40.749842],
    B: 17,
    foot: [[[37.4, 97.6], [36.3, 92.8], [34.4, 93.2], [16.6, 10.7], [59.6, 1.6], [60.3, 4.9], [72.1, 2.3], [35.9, -134.6], [-1.6, -126.6], [-1.3, -125.2], [-13.3, -122.7], [4.8, -38.7], [-15.3, -34.4], [-17.3, -44.1], [-64.8, -34], [-57.8, -3.4], [-53.5, 23.2], [-50.3, 54.4], [-49.3, 81], [-62, 83.7], [-60.6, 90.5], [-64.7, 91.3], [-58.9, 118.2]]],
    levels: [
      [0, 20, [[-65.3, -34.1], [-54.2, 23.6], [-50.5, 81], [17.1, 67.2], [3.5, 36], [-6.4, 6], [-9.8, -8.8], [7.4, -12.5], [9.7, -2], [20.2, -4.2], [21.2, -0.9], [56.1, -8.1], [55.6, -11.4], [64.2, -13.2], [33.7, -128.2], [-12.2, -119.7], [-1.9, -70.8], [-4.1, -70], [2.1, -37.9], [-15.2, -34.3], [-17, -44.2]]],
      [20, 25, [[-10.7, -112.5], [8.8, -17], [12.6, -17.7], [14.7, -10.3], [48.8, -16.7], [26, -120.6]]],
      [20, 25, [[-65.3, -34.1], [-54.2, 23.6], [-50.5, 81], [17.1, 67.2], [3.5, 36], [-6.4, 6], [-17, -44.2]]]
    ]
  },
  rc_international: {
    anchor: [-73.977617, 40.75914],
    B: 28.9,
    foot: [[[46.7, 28.8], [46.7, 7.9], [33.5, 7.9], [33.5, -10.4], [46.6, -10.4], [46.5, -31.3], [-13.7, -31.3], [-13.7, -26.7], [-23.7, -26.7], [-23.7, -21.7], [-46.5, -21.7], [-46.4, 24.7], [-41.6, 28.7]]],
    levels: [
      [0, 8, [[46.7, 28.8], [46.7, 7.9], [33.5, 7.9], [33.5, -10.4], [46.6, -10.4], [46.5, -31.3], [20.1, -31.3], [-13.7, -31.3], [-13.7, -26.7], [-23.7, -26.7], [-23.7, -21.7], [-37.6, -21.7], [-46.5, -21.7], [-46.4, 24.7], [-41.6, 28.7], [-34.4, 28.7], [8.3, 28.8]]],
      [8, 17, [[-48.3, -24.2], [-48.1, 19.2], [-23.4, 19.2], [-23.2, 23.8], [-14.8, 23.8], [-14.6, 26.4], [47, 26.6], [46.9, 6.4], [34.9, 6.2], [34.8, -10.6], [47, -10.9], [47, -31.1], [-13.6, -31.2], [-13.8, -28.6], [-23.2, -28.7], [-23.4, -24.2]]],
      [17, 20, [[-48.3, -24.2], [-48.1, 19.2], [-23.4, 19.2], [-23.2, 23.8], [-14.8, 23.8], [-14.6, 26.4], [47, 26.6], [46.9, 6.4], [24.1, 5.6], [23.9, -9.7], [27.3, -10.9], [47, -10.9], [47, -31.1], [-13.6, -31.2], [-13.8, -28.6], [-23.2, -28.7], [-23.4, -24.2]]],
      [20, 25, [[-48.3, -24.2], [-48.1, 19.2], [-23.4, 19.2], [-23.2, 23.8], [47, 23.9], [46.9, 9.5], [27.2, 9.4], [26.9, 5.7], [24, 5.5], [23.9, -9.7], [27, -10], [27.2, -14.1], [47, -14], [47, -28.5], [-23.2, -28.7], [-23.4, -24.2]]],
      [25, 28, [[-48.3, -24.2], [-48.1, 19.2], [16.7, 18.5], [16.7, 9.4], [24, 9.3], [23.9, -14], [16.9, -14.1], [16.8, -23.1]]],
      [28, 35, [[-48.3, -24.2], [-48.1, 19.2], [-23.2, 19.2], [-22.9, 15], [9.7, 15.1], [9.9, 9.3], [24, 9.3], [23.9, -14], [10, -14.1], [9.8, -19.8], [-22.9, -19.9], [-23.2, -24.2]]],
      [35, 60, [[-48.3, -20], [-48.2, 15], [9.7, 15.1], [9.9, 9.3], [24, 9.3], [23.9, -14], [10, -14.1], [9.8, -19.8]]],
      [60, 110, [[-48.3, -20], [-48.2, 15], [3.5, 15.1], [3.7, 9.3], [24, 9.3], [23.9, -14], [3.7, -14.1], [3.5, -19.8]]],
      [110, 145, [[-48.3, -20], [-48.2, 15], [-2.8, 15.1], [-2.6, 9.3], [24, 9.3], [23.9, -14], [-2.5, -14.1], [-2.8, -19.9]]],
      [145, 156, [[-48.3, -14.2], [-48.2, 9.2], [24, 9.3], [23.9, -14]]]
    ]
  },
  rc_1rock: {
    anchor: [-73.978904, 40.757989],
    B: 29,
    foot: [[[11.4, 29.2], [11.4, -3.8], [19.4, -3.7], [19.4, -25.6], [-15, -25.7], [-15.1, 29.1]]],
    levels: [
      [0, 25, [[11.4, 29.2], [11.4, 18.9], [11.4, 9.1], [11.4, -3.8], [19.4, -3.7], [19.4, -12.9], [19.4, -25.6], [-10.8, -25.7], [-15, -25.7], [-15, 8.1], [-15.1, 29.1], [4.7, 29.2]]],
      [25, 29, [[-14.5, 28.4], [5, 28.4], [4.9, -19.6], [11.7, -19.8], [11.7, -26.3], [-14.5, -26.4]]],
      [29, 138, [[-14.5, 28.4], [5, 28.4], [4.9, -19.8], [-14.3, -19.9]]],
      [138, 149, [[-7.5, -19.9], [-7.5, 28.4], [5, 28.4], [4.9, -19.8]]]
    ]
  },
  rc_1270: {
    anchor: [-73.979837, 40.760062],
    B: 29,
    foot: [[[18.9, 30.4], [18.9, -30.3], [-18.9, -30.4], [-18.9, 30.3]]],
    levels: [
      [0, 26, [[18.9, 30.4], [18.9, -30.3], [18.8, -30.3], [-15, -30.4], [-18.9, -30.4], [-18.9, -29], [-18.9, -24.7], [-18.9, 30.3], [8.8, 30.4]]],
      [26, 30, [[-18.4, -20.9], [-18.3, 19.3], [-9.9, 19.4], [-9.8, 24.7], [1.6, 24.8], [1.8, 29.6], [19.5, 29.7], [19.3, -31.1], [1.7, -31.1], [1.6, -26.3], [-10.1, -26.3], [-10.2, -20.9]]],
      [30, 110, [[-15.8, -20.9], [-15.6, 19.3], [-9.9, 19.4], [-9.8, 24.7], [14.6, 24.8], [14.5, -26.2], [-10.1, -26.3], [-10.1, -21]]],
      [110, 116.7, [[-15.8, -20.9], [-15.6, 19.3], [14.6, 19.4], [14.5, -20.8]]],
      [116.7, 124.7, [[-10.2, -15.3], [-10.1, 13], [8.4, 13.1], [8.3, -15.3]]]
    ]
  },
  rc_10rock: {
    anchor: [-73.979707, 40.758363],
    B: 28.8,
    foot: [[[-27.6, 30.8], [-26, 31.4], [45.4, 31.4], [45.2, -29.2], [-48.6, -29.2], [-48.5, 19.9], [-26, 19.9], [-26, 23.9], [-28.1, 25], [-29.2, 27.2], [-28.9, 29.1]]],
    levels: [
      [0, 13, [[-27.6, 30.8], [-27.3, 30.9], [-26.9, 31.1], [-26.4, 31.3], [-26, 31.4], [-24.5, 31.4], [18.8, 31.4], [33.6, 31.4], [43.6, 31.4], [45.4, 31.4], [45.4, 30.4], [45.4, 16.7], [45.3, -11.3], [45.2, -29.2], [9.5, -29.2], [-48.6, -29.2], [-48.5, 19.9], [-26, 19.9], [-26, 23.9], [-26.5, 24], [-26.9, 24.1], [-27.4, 24.4], [-27.8, 24.6], [-28.1, 25], [-28.5, 25.3], [-28.7, 25.8], [-29, 26.2], [-29.1, 26.7], [-29.2, 27.2], [-29.2, 27.6], [-29.2, 28.1], [-29.1, 28.6], [-28.9, 29.1], [-28.7, 29.5], [-28.5, 29.9], [-28.1, 30.3], [-27.8, 30.7]]],
      [13, 20, [[-55.3, 9], [-55.3, 16.3], [-53.2, 16.4], [-53.1, 19.2], [-25.8, 19.2], [-25.5, 23.3], [35.7, 23.4], [35.7, 9.7], [45.9, 9.6], [45.9, -8.9], [36, -9], [35.8, -22.8], [-48.1, -23.3], [-48, 8.8]]],
      [20, 24, [[-55.3, 9], [-55.3, 16.3], [-53.2, 16.4], [-53.1, 19.2], [-50, 19.2], [-22.8, 19.2], [-22.7, 9.4], [45.9, 9.6], [45.9, -8.9], [-22.3, -9], [-22.8, -16.1], [-48, -16.2], [-48, 8.8]]],
      [24, 61, [[-24.3, -9.1], [-24.2, 9.4], [45.9, 9.6], [45.9, -8.9]]],
      [61, 67, [[-24.3, -6.6], [-24.2, 6.7], [45.9, 6.8], [45.9, -6.4]]]
    ]
  },
  rc_50rock: {
    anchor: [-73.978626, 40.759553],
    B: 29,
    foot: [[[-27.4, -30.4], [-27.4, 30.3], [29.6, 30.4], [29.6, 13.1], [24.4, 13.1], [24.4, -13.2], [29.6, -13.2], [29.6, -30.3]]],
    levels: [
      [0, 20, [[-27.4, -30.4], [-27.4, 30.3], [-21.2, 30.3], [15.2, 30.4], [29.6, 30.4], [29.6, 13.1], [24.4, 13.1], [24.4, -13.2], [29.6, -13.2], [29.6, -30.3], [10.5, -30.4], [-16.6, -30.4]]],
      [20, 55, [[-26.8, 9.5], [-3.5, 9.8], [-2.7, 24.9], [24, 25.1], [25, 12.4], [24, -26], [-2.7, -26.1], [-3.5, -12], [-26.8, -12.2]]],
      [55, 60, [[-2.7, -26.1], [-2.7, 24.9], [24, 25.1], [25, 12.4], [24, -26]]],
      [60, 70, [[-3.3, 18.4], [25, 18.6], [25, -20.4], [-3.3, -20.5]]],
      [70, 73.7, [[17.9, 14.9], [23.7, 14.9], [23.7, -17], [17.9, -17.1]]]
    ]
  },
  rc_british: {
    anchor: [-73.977797, 40.758586],
    B: 28.9,
    foot: [[[30.1, 10.5], [30, -10.4], [-30.1, -10.5], [-30.1, 10.5]]],
    levels: [
      [0, 20, [[30.1, 10.5], [30, -10.4], [14.8, -10.4], [-10.2, -10.5], [-20.6, -10.5], [-30.1, -10.5], [-30.1, 4.7], [-30.1, 8.8], [-30.1, 10.5], [-29.9, 10.5], [6.1, 10.5]]],
      [20, 25, [[-29.6, 6.6], [29.6, 7.2], [29.7, -7.8], [-29.6, -8.4]]],
      [25, 30, [[-29.6, 6.6], [-1.3, 6.9], [-1.2, -8.1], [-29.6, -8.4]]],
      [30, 35, [[-29.6, -5.6], [-29.6, 3.7], [-1.3, 4], [-1.2, -5.3]]]
    ]
  },
  rc_maison: {
    anchor: [-73.978023, 40.758277],
    B: 28.8,
    foot: [[[30, 10.5], [30, -10.4], [-30, -10.5], [-29.9, 10.5]]],
    levels: [
      [0, 20, [[30, -3.3], [30, -10.4], [-8.8, -10.5], [-30, -10.5], [-30, -10.1], [-29.9, 10.5], [-17.3, 10.5], [-3.4, 10.5], [23.3, 10.5], [30, 10.5]]],
      [20, 25, [[-29.3, -8.4], [-29.3, 6.6], [29.9, 7.1], [30, -7.9]]],
      [25, 30, [[-29.3, -8.4], [-29.3, 6.6], [-1, 6.9], [-1, -8.1]]],
      [30, 35, [[-29.3, -5.5], [-29.3, 3.8], [-1, 4], [-1, -5.3]]]
    ]
  },
  rc_radiocity: {
    anchor: [-73.979276, 40.759826],
    B: 28.9,
    foot: [[[35.2, 30.4], [35.1, -30.3], [-35.2, -30.4], [-35.1, 30.4]]],
    levels: [
      [0, 30, [[35.2, 30.4], [35.1, -30.3], [32.5, -30.3], [16.8, -30.3], [-35.2, -30.4], [-35.1, 30.4], [-8.8, 30.4]]],
      [30, 35, [[-34.7, -26.5], [-34.5, 23.7], [35.8, 23.5], [35.7, -26.3]]]
    ]
  }
};
function toLocal(B, ring) {
  const a = -B * Math.PI / 180;
  const c = Math.cos(a);
  const s = Math.sin(a);
  return ring.map(([u, v]) => [c * u - s * v, s * u + c * v]);
}
function grow(ring, d) {
  const n = ring.length;
  let area2 = 0;
  for (let i = 0; i < n; i++) {
    const [x0, y0] = ring[i];
    const [x1, y1] = ring[(i + 1) % n];
    area2 += x0 * y1 - x1 * y0;
  }
  const sgn = area2 > 0 ? 1 : -1;
  const out2 = [];
  for (let i = 0; i < n; i++) {
    const p = ring[(i + n - 1) % n];
    const q = ring[i];
    const r = ring[(i + 1) % n];
    const l0 = Math.hypot(q[0] - p[0], q[1] - p[1]) || 1;
    const l1 = Math.hypot(r[0] - q[0], r[1] - q[1]) || 1;
    const n0 = [sgn * (q[1] - p[1]) / l0, -sgn * (q[0] - p[0]) / l0];
    const n1 = [sgn * (r[1] - q[1]) / l1, -sgn * (r[0] - q[0]) / l1];
    const k = 1 + n0[0] * n1[0] + n0[1] * n1[1];
    const m = Math.min(d / Math.max(k, 0.35), d * 2.5);
    out2.push([q[0] + (n0[0] + n1[0]) * m, q[1] + (n0[1] + n1[1]) * m]);
  }
  return out2;
}
function R(u0, v0, u1, v1) {
  return [
    [u0, v0],
    [u1, v0],
    [u1, v1],
    [u0, v1]
  ];
}
function ngon(cu, cv, r, n = 8, rot = 0.5) {
  const out2 = [];
  for (let i = 0; i < n; i++) {
    const a = (i + rot) / n * Math.PI * 2;
    out2.push([cu + Math.cos(a) * r, cv + Math.sin(a) * r]);
  }
  return out2;
}
function stack(b, levels, zTop = Infinity) {
  for (const [z0, z1, ring] of levels) {
    if (z0 >= zTop) continue;
    b.prism(ring, z0, Math.min(z1, zTop), { bottom: z0 > 0 });
  }
}
function outline(m, d = 1, rings) {
  return m.foot.filter((_, i) => !rings || rings.includes(i)).map((r) => toLocal(m.B, grow(r, d)));
}
function extrudeProfile(b, prof, cu, cv, len, alongU) {
  const P = (s, t, z) => alongU ? [cu + t, cv + s, z] : [cu + s, cv + t, z];
  const h = len / 2;
  for (let i = 0; i < prof.length - 1; i++) {
    b.quad(P(prof[i][0], -h, prof[i][1]), P(prof[i + 1][0], -h, prof[i + 1][1]), P(prof[i + 1][0], h, prof[i + 1][1]), P(prof[i][0], h, prof[i][1]));
  }
  for (const t of [-h, h]) {
    for (let i = 1; i < prof.length - 1; i++) b.tri(P(prof[0][0], t, prof[0][1]), P(prof[i][0], t, prof[i][1]), P(prof[i + 1][0], t, prof[i + 1][1]));
  }
}
function arch(w, z0, zSpring, rise, n = 8) {
  const out2 = [[-w / 2, z0]];
  for (let i = 0; i <= n; i++) {
    const a = Math.PI - i / n * Math.PI;
    out2.push([Math.cos(a) * w / 2, zSpring + Math.sin(a) * rise]);
  }
  out2.push([w / 2, z0]);
  return out2;
}
function withTop(levels, zTop) {
  const zMax = Math.max(...levels.map((l) => l[1]));
  return levels.filter((l) => l[0] < zTop).map(([z0, z1, ring]) => [z0, z1 === zMax || z1 > zTop ? zTop : z1, ring]);
}
function tower(s) {
  const { m, draw, replaces, end, pad, rings, hide, ...rest } = s;
  return {
    ...rest,
    end: end ?? 9999,
    anchor: m.anchor,
    build: (b) => {
      b.frame(0, 0, 0, m.B, () => draw(b, m));
    },
    replaces: replaces === false ? void 0 : hide ? hide.map((r) => toLocal(m.B, r)) : outline(m, pad ?? 1, rings)
  };
}
var WP = "https://en.wikipedia.org/wiki/";
var OSM = "https://www.openstreetmap.org/copyright";
var CTBUH = "https://www.skyscrapercenter.com/city/new-york-city";
var FOOT = "https://data.cityofnewyork.us/City-Government/BUILDING/5zhs-2jue";
var LIMESTONE = "#D3CCBB";
var STEEL = "#C3CAD0";
var DARK = "#59616A";
var ESB_C = [4.2, 0.85];
function drawEmpireState(b, m) {
  const [cu, cv] = ESB_C;
  b.color(LIMESTONE);
  stack(b, m.levels);
  b.color("#C9C2B2").prism(R(-80.4, -25.1, -59.8, -2.9), 17, 23.8);
  b.color("#A9A79F");
  for (const s of [-1, 1]) b.prism(R(cu - 9, cv + s * 14.6 - 0.45, cu + 9, cv + s * 14.6 + 0.45), 115, 255, { top: false });
  b.color("#BFC3C4").prism(R(cu - 18.65, cv - 10.45, cu + 18.65, cv + 10.45), 320, 330);
  b.color("#C8CDD0");
  for (const [du, dv] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
    b.prism(R(cu + du * 7.4 - 1.6 - Math.abs(du) * 1.4, cv + dv * 7.4 - 1.6 - Math.abs(dv) * 1.4, cu + du * 7.4 + 1.6 + Math.abs(du) * 1.4, cv + dv * 7.4 + 1.6 + Math.abs(dv) * 1.4), 330, 343);
    b.prism(R(cu + du * 6.4 - 1.4 - Math.abs(du) * 0.9, cv + dv * 6.4 - 1.4 - Math.abs(dv) * 0.9, cu + du * 6.4 + 1.4 + Math.abs(du) * 0.9, cv + dv * 6.4 + 1.4 + Math.abs(dv) * 0.9), 343, 352);
  }
  b.color("#B4BBC0").loft([ngon(cu, cv, 6.6, 16), ngon(cu, cv, 5.9, 16)], [330, 368]);
  b.color("#C8CDD0").loft([ngon(cu, cv, 5, 16), ngon(cu, cv, 4.6, 16)], [368, 373.1]);
  b.color("#AEB4B8").loft([ngon(cu, cv, 4.6, 16), ngon(cu, cv, 1.7, 16)], [373.1, 381]);
}
function drawEmpireStateAntenna(b) {
  const [cu, cv] = ESB_C;
  const sq = (h) => R(cu - h, cv - h, cu + h, cv + h);
  b.color("#8C9399").loft([sq(1.7), sq(1.2), sq(0.6)], [381, 405, 428], { top: false });
  b.color("#D9DCDF").loft([sq(0.6), sq(0.25)], [428, 443.2]);
  b.color("#8C9399");
  for (const z of [392, 404, 416]) b.prism(sq(2.3), z, z + 0.6);
}
var CHRYSLER_T = [3.05, -0.65];
function drawChrysler(b, m) {
  const [cu, cv] = CHRYSLER_T;
  b.color("#3E4144").prism(m.foot[0], 0, 5, { top: false });
  b.color("#DCDCD6");
  stack(b, m.levels.map(([z02, z1, r]) => [Math.max(z02, 5), z1, r]));
  b.color(STEEL);
  for (const su of [-1, 1]) {
    for (const sv of [-1, 1]) {
      const ku = cu + su * 14.35;
      const kv = cv + sv * 17.45;
      b.prism(ngon(ku + su * 1.6, kv + sv * 1.6, 1.5, 8), 90, 93.5);
      b.beam([ku + su * 1.6, kv + sv * 1.6, 92], [ku + su * 3.2, kv - sv * 0, 92.6], 0.7);
      b.beam([ku + su * 1.6, kv + sv * 1.6, 92], [ku - su * 0, kv + sv * 3.2, 92.6], 0.7);
      const d = 3.2 / Math.SQRT2;
      b.beam([ku, kv - sv * 7.8, 199.3], [ku + su * d, kv - sv * 7.8 + sv * d, 199.9], 1);
      b.beam([ku - su * 4.8, kv, 199.3], [ku - su * 4.8 + su * d, kv + sv * d, 199.9], 1);
    }
  }
  b.color("#D5D7D6");
  b.prism(R(cu - 14.3, cv - 7, cu + 14.3, cv + 7), 199, 224);
  b.prism(R(cu - 7, cv - 14.8, cu + 7, cv + 14.8), 199, 224);
  const tiers = [
    [22.2, 235],
    [20.5, 242],
    [17.3, 249],
    [13.9, 256],
    [9.9, 262],
    [8.1, 267],
    [5.9, 272]
  ];
  let z0 = 222;
  tiers.forEach(([w, zt], k) => {
    const rise = Math.min(7, w * 0.55);
    b.color(k % 2 ? "#B9C1C8" : "#CDD3D8");
    for (const alongU of [true, false]) extrudeProfile(b, arch(w, z0, zt - rise, rise, 8), cu, cv, w, alongU);
    b.color("#4E5963");
    const n = w > 12 ? 7 : w > 7 ? 5 : 3;
    const zs = zt - rise;
    for (let j = 0; j < n; j++) {
      const a = Math.PI * (j + 0.5) / n;
      const da = Math.PI * 0.3 / n;
      const pt = (f, ang) => [f * w / 2 * Math.cos(ang), zs + f * rise * Math.sin(ang)];
      const tri = [pt(0.6, a - da), pt(0.6, a + da), pt(0.93, a)];
      for (const sgn of [-1, 1]) {
        const d = sgn * (w / 2 + 0.35);
        b.tri([cu + d, cv + tri[0][0], tri[0][1]], [cu + d, cv + tri[1][0], tri[1][1]], [cu + d, cv + tri[2][0], tri[2][1]]);
        b.tri([cu + tri[0][0], cv + d, tri[0][1]], [cu + tri[1][0], cv + d, tri[1][1]], [cu + tri[2][0], cv + d, tri[2][1]]);
      }
    }
    z0 = zs;
  });
  const sq = (h) => R(cu - h, cv - h, cu + h, cv + h);
  b.color(STEEL).loft([sq(2.6), sq(1.22)], [270, 282], { top: false });
  b.pyramid(sq(1.22), 282, [cu, cv, 318.9]);
}
function drawOneWTC(b, m) {
  const c = m.foot[0];
  const mid = c.map((p, i) => [(p[0] + c[(i + 1) % 4][0]) / 2, (p[1] + c[(i + 1) % 4][1]) / 2]);
  const Z0 = 56.4;
  const Z1 = 417;
  b.color("#A8BCCB").prism(c, 0, Z0, { top: false });
  b.color("#8EAFCB");
  for (let i = 0; i < 4; i++) {
    const mPrev = mid[(i + 3) % 4];
    b.tri([c[i][0], c[i][1], Z0], [c[(i + 1) % 4][0], c[(i + 1) % 4][1], Z0], [mid[i][0], mid[i][1], Z1]);
    b.color("#9DBAD2").tri([mPrev[0], mPrev[1], Z1], [mid[i][0], mid[i][1], Z1], [c[i][0], c[i][1], Z0]);
    b.color("#8EAFCB");
  }
  const t = (Z1 - 10.16 - Z0) / (Z1 - Z0);
  const deck = [];
  for (let i = 0; i < 4; i++) {
    for (const q of [mid[(i + 3) % 4], mid[i]]) deck.push([c[i][0] + t * (q[0] - c[i][0]), c[i][1] + t * (q[1] - c[i][1])]);
  }
  b.color(DARK).cap(deck, Z1 - 10.16);
  b.color("#D8DCDF").prism(circle(0, 0, 17.7, 24), 417, 420, { holes: [circle(0, 0, 15.2, 24)] });
  for (let k = 0; k < 8; k++) {
    const a = k / 8 * Math.PI * 2;
    b.beam([Math.cos(a) * 3, Math.sin(a) * 3, 407], [Math.cos(a) * 16.4, Math.sin(a) * 16.4, 418], 0.6);
  }
  b.color("#E3E6E8").loft([ngon(0, 0, 2.9, 8), ngon(0, 0, 2.2, 8), ngon(0, 0, 0.9, 8), ngon(0, 0, 0.3, 8)], [406.8, 440, 510, 541.3]);
}
function drawWoolworth(b, m) {
  const cu = 27 - 12.8;
  const cv = 0;
  const FT = 0.3048;
  const stage = (eu, nv) => R(cu - eu * FT / 2, cv - nv * FT / 2, cu + eu * FT / 2, cv + nv * FT / 2);
  b.color("#E4DDC8");
  stack(b, m.levels.slice(0, 1));
  b.prism(stage(84, 86), 120, 170);
  b.prism(stage(69, 71), 170, 194);
  const hu = 69 * FT / 2;
  const hv = 61 * FT / 2;
  const oct = (f, ch) => [
    [cu - hu * f + ch, cv - hv * f],
    [cu + hu * f - ch, cv - hv * f],
    [cu + hu * f, cv - hv * f + ch],
    [cu + hu * f, cv + hv * f - ch],
    [cu + hu * f - ch, cv + hv * f],
    [cu - hu * f + ch, cv + hv * f],
    [cu - hu * f, cv + hv * f - ch],
    [cu - hu * f, cv - hv * f + ch]
  ];
  const EAVE = 241.4 - 105 * FT;
  const GALLERY = 730 * FT;
  b.prism(oct(1, 4.5), 194, EAVE);
  for (const su of [-1, 1]) {
    for (const sv of [-1, 1]) {
      const tu = cu + su * (69 * FT / 2 - 1.2);
      const tv = cv + sv * (71 * FT / 2 - 1.2);
      b.color("#E4DDC8").prism(ngon(tu, tv, 2.3, 8), 170, 203);
      b.color("#86A894").pyramid(ngon(tu, tv, 2.3, 8), 203, [tu, tv, 212]);
    }
  }
  b.color("#86A894").loft([oct(1, 4.5), oct(0.3, 1.2)], [EAVE, GALLERY]);
  b.color("#DAD5BF").prism(ngon(cu, cv, 2.6, 8), GALLERY, GALLERY + 6);
  b.color("#86A894").pyramid(ngon(cu, cv, 2.8, 8), GALLERY + 6, [cu, cv, 241.4]);
}
var FLATIRON_BODY = [[2.3, 31.4], [3.8, 32.7], [8, 32.3], [9.5, 29.6], [9.5, -24.7], [8.6, -26.1], [6.7, -26.9], [-15.4, -17.6], [-17.2, -14.8], [-16.8, -13]];
var FLATIRON_CAPITAL = [[2.1, 31.6], [3.7, 33], [8.2, 32.5], [9.8, 29.7], [9.8, -24.8], [8.8, -26.3], [6.7, -27.2], [-15.6, -17.8], [-17.5, -14.8], [-17, -12.9]];
var FLATIRON_CORNICE = [[1.1, 32.3], [3.3, 34.3], [8.9, 33.7], [11, 30], [11, -25.1], [9.6, -27.3], [6.7, -28.5], [-16.4, -18.8], [-18.8, -15.1], [-18.2, -12.5]];
var FLATIRON_PENTHOUSE = [[-14.5, -14.3], [4.6, 30.1], [6.5, 29.9], [7, 29], [7, -24], [6.7, -24.2], [-13.7, -15.6]];
var FLATIRON_PROW = [[3.8, 32.7], [6.6, 39.3], [7.7, 39.5], [8, 32.3]];
function drawFlatiron(b) {
  b.color("#CFC5AD").prism(FLATIRON_BODY, 0, 16);
  b.color("#D9CFB7").prism(FLATIRON_BODY, 16, 70, { top: false });
  b.color("#D2C7AE").prism(FLATIRON_CAPITAL, 70, 84, { top: false, bottom: true });
  b.color("#C4B99F").prism(FLATIRON_CORNICE, 84, 86.9, { bottom: true });
  b.color("#D2C7AE").prism(FLATIRON_PENTHOUSE, 86.9, 93.6);
  b.color("#8FA3A6").prism(FLATIRON_PROW, 0, 5.5);
}
function drawRock30(b, m) {
  b.color("#D6CFBF");
  stack(b, m.levels);
  b.prism(R(1.9, -10.6, 72.2, 9), 245, 259.1);
}
function drawWTC7(b, m) {
  b.color("#9CA6AD").prism(m.foot[0], 0, 36, { top: false });
  b.color("#A9C6DB").prism(m.foot[0], 36, 225.9, { top: false });
  b.color("#7F8C96").cap(m.foot[0], 225.9);
  b.color("#BCD3E3").prism(m.foot[0], 225.9, 226.5, { top: false });
}
function drawWTC3(b) {
  b.color("#A5B4BF").prism([[-14.9, 28.1], [-50.3, 28.1], [-40.2, -28.9], [-15.2, -28.9], [-15.2, -25.2], [-11.8, -25.2], [-11.8, 24.5], [-14.9, 24.5]], 0, 75);
  b.color("#A3C0D6");
  b.prism(R(-10.6, -31, 40.7, -19.9), 0, 220).prism(R(-12.2, -27, 42.9, -19.9), 0, 220);
  b.prism(R(-10.1, 18.8, 28.9, 30.2), 0, 281).prism(R(-11.8, 18.8, 41.6, 28.9), 0, 281);
  b.color("#9AB9D1").prism(R(-11.9, -19.9, 45.6, 18.8), 0, 328.9);
  b.color("#DADFE3");
  for (const u of [-12.1, 45.8]) {
    for (let z = 80; z < 320; z += 60) {
      b.beam([u, -19.9, z], [u, -0.5, z + 30], 0.9).beam([u, -0.5, z + 30], [u, 18.8, z], 0.9);
      b.beam([u, -19.9, z + 60], [u, -0.5, z + 30], 0.9).beam([u, -0.5, z + 30], [u, 18.8, z + 60], 0.9);
    }
  }
}
function drawWTC4(b, m) {
  b.color("#A9B7C0").prism(m.foot[0], 0, 25);
  b.color("#A7C5DA").prism([[-44.6, 24.6], [-31.6, -30.4], [29, -30.4], [16.1, 20.6], [11.8, 19.5], [11.9, 24.4]], 25, 220);
  b.color("#B2CDDF").prism([[-15, 24.4], [-32.4, -25.5], [-28.1, -25], [-28, -30.4], [29, -30.4], [16.1, 20.6], [11.8, 19.5], [11.9, 24.4]], 220, 297.7);
}
function drawMetLifeTower(b, m) {
  const f = m.foot[0];
  b.color("#D9D5CA").prism(f, 0, 18, { top: false });
  b.color("#E4E1D9").prism(f, 18, 150);
  b.color("#D2CEC2").prism(grow(f, 0.9), 146, 150, { bottom: true });
  b.color("#E4E1D9").prism(R(-11.35, -10.35, 11.55, 10.55), 150, 165);
  b.color("#8D9698").loft([R(-11.35, -10.35, 11.55, 10.55), R(-5.35, -4.3, 5.55, 4.5)], [165, 190]);
  b.color("#E4E1D9").prism(ngon(0.1, 0.1, 3.8, 8), 190, 200);
  b.color("#D8B24C").dome(0.1, 0.1, 3.8, 200, 6, 8, 4);
  b.color("#D8B24C").prism(ngon(0.1, 0.1, 0.9, 8), 205, 213.4);
  b.color("#F4F1E6");
  const disc = [];
  for (let k = 0; k < 16; k++) disc.push([Math.cos(k / 16 * Math.PI * 2) * 4.05, 95 + Math.sin(k / 16 * Math.PI * 2) * 4.05]);
  extrudeProfile(b, disc, 0.1, 11, 0.9, false);
  extrudeProfile(b, disc, 0.1, -10.8, 0.9, false);
  extrudeProfile(b, disc, 13.1, 0.1, 0.9, true);
  extrudeProfile(b, disc, -13, 0.1, 0.9, true);
}
function drawWall40(b, m) {
  const cu = 6.65;
  const cv = -3.05;
  const sq = (h) => R(cu - h, cv - h, cu + h, cv + h);
  b.color("#D8D2C3");
  stack(b, m.levels);
  b.color("#7FA694").loft([sq(11.65), sq(2.2)], [230, 259]);
  b.color("#9DB8A8").prism(ngon(cu, cv, 2, 8), 259, 264);
  b.color("#7FA694").pyramid(ngon(cu, cv, 2, 8), 264, [cu, cv, 282.5]);
}
function drawPine70(b, m) {
  const cu = 6.25;
  const cv = -1.2;
  b.color("#D5CDBD");
  stack(b, m.levels);
  b.color("#C2CBD0").prism(ngon(cu, cv, 3.6, 8), 252.4, 260.6);
  b.color("#D9DDE0").loft([ngon(cu, cv, 1.6, 8), ngon(cu, cv, 0.5, 8)], [260.6, 275]);
  b.pyramid(ngon(cu, cv, 0.5, 8), 275, [cu, cv, 290.2]);
}
function drawCitigroup(b) {
  const [u0, v0, u1, v1] = [-45.05, -31.8, 2.85, 16.1];
  const cu = (u0 + u1) / 2;
  const cv = (v0 + v1) / 2;
  const ZS = 34.1;
  const ZE = 278.9 - (v1 - v0);
  b.color("#C9CED2");
  b.prism(R(cu - 3.65, v0, cu + 3.65, v0 + 7.3), 0, ZS, { top: false });
  b.prism(R(cu - 3.65, v1 - 7.3, cu + 3.65, v1), 0, ZS, { top: false });
  b.prism(R(u0, cv - 3.65, u0 + 7.3, cv + 3.65), 0, ZS, { top: false });
  b.prism(R(u1 - 7.3, cv - 3.65, u1, cv + 3.65), 0, ZS, { top: false });
  b.prism(ngon(cu, cv, 9, 8), 0, ZS, { top: false });
  b.color("#D3D8DC").prism(R(u0, v0, u1, v1), ZS, ZE, { bottom: true, top: false });
  b.color("#BFC6CC").quad([u0, v0, ZE], [u1, v0, ZE], [u1, v1, 278.9], [u0, v1, 278.9]);
  b.color("#D3D8DC").quad([u0, v1, ZE], [u1, v1, ZE], [u1, v1, 278.9], [u0, v1, 278.9]);
  for (const u of [u0, u1]) b.tri([u, v0, ZE], [u, v1, ZE], [u, v1, 278.9]);
  b.color("#C4C9CD").prism([[1.3, -33.9], [32.5, -33.6], [32.4, -3.9], [60.9, -3.7], [60.7, 27.1], [1.3, 26.6]], 0, 26);
  b.prism([[18, -19.1], [31.9, -19.3], [31.7, -4.6], [46.7, -4.4], [46.9, 16.8], [18.2, 16.5]], 26, 30);
  const steps = [[-2.9, 1.3, 22], [-5.9, -2.9, 18], [-9, -5.9, 14], [-17.7, -9, 10]];
  for (const [a, c, z] of steps) b.prism(R(a, 16.5, c, 26.4), 0, z);
  b.prism(R(-42.2, 9.9, -17.7, 24), 0, 7);
  const church = [[-57, 9.8], [-62.8, 14.5], [-62.8, 24.8], [-60.4, 27], [-45.3, 27.1], [-42.2, 23.9], [-45.2, 9.9]];
  b.color("#8E8F8C").prism(church, 0, 9, { top: false });
  b.loft([church, church.map(([u, v]) => [-53 + (u + 53) * 0.45, 18.5 + (v - 18.5) * 0.45])], [9, 17]);
}
function drawPark432(b) {
  const T = R(-22.9, -5.85, 5.6, 22.65);
  b.color("#DCDAD3").prism(T, 0, 425.5);
  b.color("#6E7378");
  for (let k = 0; k < 5; k++) {
    const zt = 425.5 - 12 * 4.43 - k * 14 * 4.43;
    b.prism(grow(T, 0.4), zt - 8.86, zt, { top: false });
  }
  b.color("#CFCDC6").prism([[-33, -5.8], [-23, -5.8], [-23, 22.6], [3.6, 22.6], [3.6, 38.3], [-33, 38.3]], 0, 30);
  b.color("#BFC2C2").prism(R(-32.8, -22.9, 3.8, -5.8), 0, 1.2);
  b.color("#D6D9DA").prism([[3.8, -22.9], [50.2, -22.9], [50.8, -2], [3.8, -3.3]], 0, 12);
}
function drawVanderbilt(b, m) {
  b.color("#A9C0D2");
  stack(b, m.levels);
  b.color("#DDE2E6").loft([ngon(5.65, 5.3, 1.6, 8), ngon(5.65, 5.3, 0.25, 8)], [396.5, 427]);
}
var CPT_BASE = [[28.7, -31.7], [-16.8, -31.7], [-16.7, -17], [-46.3, -16.8], [-46, -1.4], [-30.3, -1.4], [-30.2, 29.5], [29.2, 29.9]];
function drawCentralParkTower(b, m) {
  b.color("#B7C2CA").prism(CPT_BASE, 0, 23);
  stack(b, m.levels.slice(1, 2));
  b.color("#A3BACD");
  stack(b, withTop(m.levels.slice(2), 472.4));
}
function drawSteinwayHall(b) {
  const S = 67 / 16;
  b.color("#D8D0BD").prism(R(-15.2, -30.6, -2.2, 4), 0, 12 * S);
  b.prism(R(-13.6, -28.6, -3.8, -12), 12 * S, 67);
  b.color("#CDB89A").prism([[-15.2, 4], [-2.2, 4], [-2.2, 11.3], [15.2, 11.3], [15.2, 30.5], [-15.2, 30.5]], 0, 9 * S);
  b.prism(R(-13.2, 13.3, 13.2, 27.5), 9 * S, 12 * S);
}
function drawW57(b, m) {
  b.color("#CFC2AC");
  stack(b, withTop(m.levels, 435.3));
}
function drawHY30(b, m) {
  b.color("#C9CDCF").prism(m.foot[0], 0, 45);
  b.color("#9FB7CA");
  stack(b, m.levels);
}
function drawHY10(b, m) {
  b.color("#A6BCCD");
  stack(b, m.levels);
}
function drawVessel(b) {
  const H = 45.7;
  const r = (z, inner) => 7.6 + (23 - 7.6) * z / H - (inner ? 2.6 : 0);
  const zs = [0, H / 4, H / 2, 3 * H / 4, H];
  b.color("#A8643C").loft(zs.map((z) => circle(0, 0, r(z, false), 16)), zs, { top: false });
  b.color("#8C4F2E").loft(zs.map((z) => circle(0, 0, r(z, true), 16)), zs, { top: false });
  b.color("#C98B5E");
  for (let k = 1; k <= 8; k++) {
    const z = k * H / 8;
    b.prism(circle(0, 0, r(z, false) + 0.2, 16), z - 0.5, z, { holes: [circle(0, 0, r(z, true) - 0.2, 16)], bottom: true });
  }
}
function drawBoA(b, m) {
  const f = (z) => z <= 236 ? z : 236 + (z - 236) * (288 - 236) / (279 - 236);
  b.color("#A9C2D4");
  const body = m.levels.filter(([z0, , ring]) => z0 < 279 && !ring.every(([u, v]) => u > 23 && u < 31 && v > -10.5 && v < -4));
  stack(b, body.map(([z0, z1, ring]) => [f(z0), f(z1), ring]));
  b.color("#DADFE3").loft([ngon(26.85, -7.1, 2.6, 8), ngon(26.85, -7.1, 1.4, 8), ngon(26.85, -7.1, 0.25, 8)], [245, 300, 365.8]);
}
function drawNYT(b, m) {
  b.color("#C3C9CC");
  stack(b, m.levels.slice(0, 1));
  b.color("#B4BEC6");
  stack(b, m.levels.slice(1));
  const ring = m.levels[1][2];
  b.color("#E1E4E5");
  for (let i = 0; i < ring.length; i++) {
    const p = ring[i];
    const q = ring[(i + 1) % ring.length];
    if (Math.hypot(q[0] - p[0], q[1] - p[1]) > 18) b.quad([p[0], p[1], 227], [q[0], q[1], 227], [q[0], q[1], 256], [p[0], p[1], 256]);
  }
  b.color("#D5D9DC").loft([ngon(-38.9, -2.4, 1.3, 8), ngon(-38.9, -2.4, 0.2, 8)], [232, 318.8]);
}
function drawSpruce8(b, m) {
  b.color("#B98463");
  stack(b, m.levels.slice(0, 1));
  b.color("#C9CED2");
  stack(b, m.levels.slice(1));
}
var HEARST_T = { cu: 0.2, cv: -0.25, hu: 24.4, hv: 18.3 };
function drawHearstBase(b, m) {
  b.color("#D8D0BC").prism(m.foot[0], 0, 30);
}
function drawHearstTower(b) {
  const { cu, cv, hu, hv } = HEARST_T;
  const Z1 = 182;
  const h = 16.27;
  const Z0 = Z1 - 8 * h;
  b.color("#6F7F8C").prism(R(cu - hu + 2, cv - hv + 2, cu + hu - 2, cv + hv - 2), 30, Z0, { top: false });
  b.color("#93ADC2").prism(R(cu - hu, cv - hv, cu + hu, cv + hv), Z0, Z1, { bottom: true });
  b.color("#DCE0E3");
  const w = 12.2;
  const face = (len, P) => {
    const rows = (Z1 - Z0) / h;
    for (let k = -Math.ceil(rows / 2) - 1; k <= len / w + 1; k++) {
      for (const dir of [1, -1]) {
        const t0 = dir > 0 ? k * w : k * w + rows * w / 2;
        const ta = Math.max(0, Math.min(len, t0));
        const za = Z0 + (ta - t0) * dir * 2 * h / w;
        const zEnd = Math.min(Z1, Math.max(Z0, za));
        const tEnd0 = t0 + dir * (Z1 - Z0) * w / (2 * h);
        const tb = Math.max(0, Math.min(len, tEnd0));
        const zb = Z0 + (tb - t0) * dir * 2 * h / w;
        if (Math.abs(tb - ta) < 0.5) continue;
        b.beam(P(ta, Math.min(zEnd, Z1 - 0.5)), P(tb, Math.min(Z1 - 0.5, Math.max(Z0, zb))), 0.9);
      }
    }
  };
  face(2 * hu, (t, z) => [cu - hu + t, cv - hv - 0.3, z]);
  face(2 * hu, (t, z) => [cu - hu + t, cv + hv + 0.3, z]);
  face(2 * hv, (t, z) => [cu - hu - 0.3, cv - hv + t, z]);
  face(2 * hv, (t, z) => [cu + hu + 0.3, cv - hv + t, z]);
}
function drawLeonard56(b, m) {
  b.color("#B4C2CC").prism(m.foot[0], 0, 30);
  b.color("#B9C7D1").prism(R(-13.5, -12.5, 17.5, 12.5), 30, 250.2);
  let seed = 56;
  const rnd = () => ((seed = seed * 16807 % 2147483647) - 1) / 2147483646;
  b.color("#D9DDDF");
  const slab = (z, t, amp) => {
    const du = (rnd() - 0.5) * amp;
    const dv = (rnd() - 0.5) * amp;
    b.prism(R(-15 + du - rnd() * amp * 0.4, -13.5 + dv, 19 + du + rnd() * amp * 0.4, 13.5 + dv + rnd() * amp * 0.3), z, z + t, { bottom: true });
  };
  for (let z = 36; z < 200; z += 8.2) slab(z, 0.5, 2.5);
  for (let z = 202; z < 246; z += 5.4) slab(z, 3.6, 7);
}
function drawSecretariat(b, m) {
  const f = m.foot[0];
  const us = f.map((p) => p[0]);
  const vs = f.map((p) => p[1]);
  const [u0, u1, v0, v1] = [Math.min(...us), Math.max(...us), Math.min(...vs), Math.max(...vs)];
  const H = 153.9;
  b.color("#E7E4DB");
  b.quad([u0, v0, 0], [u1, v0, 0], [u1, v0, H], [u0, v0, H]).quad([u0, v1, 0], [u1, v1, 0], [u1, v1, H], [u0, v1, H]);
  b.color("#86B5AC");
  b.quad([u0, v0, 0], [u0, v1, 0], [u0, v1, H], [u0, v0, H]).quad([u1, v0, 0], [u1, v1, 0], [u1, v1, H], [u1, v0, H]);
  b.color("#C9CCC6").cap(R(u0, v0, u1, v1), H);
  b.color("#5F7F7A");
  for (const z of [21, 60, 107, 149]) {
    for (const u of [u0 - 0.4, u1 + 0.4]) b.quad([u, v0 + 1.2, z], [u, v1 - 1.2, z], [u, v1 - 1.2, z + 4], [u, v0 + 1.2, z + 4]);
  }
}
function drawUNGA(b, m) {
  b.color("#C9C8C2").prism(m.foot[0], 0, 1.2);
  b.color("#E2DFD6");
  stack(b, m.levels);
  b.color("#9AA7A4").dome(-27.6, 18.6, 17.2, 22, 10, 16, 4);
}
function drawLever(b, m) {
  const court = R(-6.9, -19.9, 13.5, -1.6);
  const t = m.levels[1][2];
  b.color("#C9CDD0");
  for (let u = -28; u <= 25; u += 8.8) {
    for (let v = -30; v <= 25; v += 8.8) {
      if (u < -19 && v < -5) continue;
      if (u > -7.5 && u < 14.1 && v > -20.5 && v < -1) continue;
      b.box(u, v, 0, 0.7, 0.7, 5.2, { top: false });
    }
  }
  b.color("#8DB3AE").prism(m.foot[0], 5.2, 10.4, { holes: [court], bottom: true });
  b.color("#6F908D").prism(R(-20, -0.8, 24, 12), 0, 5.2, { top: false });
  b.prism(R(-22.5, -1.6, 26, 12.8), 10.4, 15, { top: false });
  b.color("#86B0AC").prism(t, 15, 84, { bottom: true, top: false });
  b.color("#5F8E8B").prism(t, 84, 93.6);
}
function drawSeagram(b, m) {
  b.color("#5A4937");
  stack(b, withTop(m.levels, 157));
}
function drawMetLifeBuilding(b, m) {
  b.color("#C6C1B4");
  stack(b, withTop(m.levels, 246.3));
}
function drawMunicipal(b, m) {
  b.color("#DBD6C9");
  stack(b, withTop(m.levels, 170.7));
  b.color("#D8B24C").loft([ngon(2.2, -0.1, 1, 8), ngon(2.2, -0.1, 0.5, 8)], [170.7, 176.8]);
}
function drawParkRow(b, m) {
  b.color("#D3C3A6").prism(m.foot[0], 0, 102.1);
  for (const v of [-4.7, 15.5]) {
    b.color("#D3C3A6").prism(ngon(-13.2, v, 4.3, 12), 102.1, 113.5);
    b.color("#7FA694").dome(-13.2, v, 4.3, 113.5, 4.2, 12, 3);
    b.color("#D3C3A6").prism(ngon(-13.2, v, 0.9, 8), 117.5, 119.2);
  }
}
function drawNYLife(b, m) {
  const top = m.levels[m.levels.length - 1];
  b.color("#D9D3C4");
  stack(b, m.levels.slice(0, -1));
  const cu = -0.25;
  const cv = -1.45;
  b.prism(top[2], 148, 160.7);
  b.color("#D9B54A").loft([top[2], ngon(cu, cv, 1.2, 8, 0)], [160.7, 184.5]);
  b.color("#E8CF7A").pyramid(ngon(cu, cv, 1.2, 8, 0), 184.5, [cu, cv, 187.5]);
}
function drawWilliamsburgh(b, m) {
  const cu = -2.3;
  const cv = -2.4;
  b.color("#D6C6A4");
  stack(b, m.levels.filter((l) => l[0] < 145));
  b.color("#C79A3F").dome(cu, cv, 5.4, 145, 8, 12, 4);
  b.color("#D6C6A4").prism(ngon(cu, cv, 0.9, 8), 152.5, 156);
  b.color("#F1ECDD");
  const disc = [];
  for (let k = 0; k < 16; k++) disc.push([Math.cos(k / 16 * Math.PI * 2) * 4.1, 131 + Math.sin(k / 16 * Math.PI * 2) * 4.1]);
  extrudeProfile(b, disc, cu, 3.5, 0.9, false);
  extrudeProfile(b, disc, cu, -8.4, 0.9, false);
  extrudeProfile(b, disc, 3.6, cv, 0.9, true);
  extrudeProfile(b, disc, -8.2, cv, 0.9, true);
}
function drawCourtSquare(b, m) {
  b.color("#78AFA3");
  stack(b, withTop(m.levels, COURT_SQ_H));
}
var COURT_SQ_H = 205.1;
function rockefellerBlock(o) {
  const k = o.scale ?? 1;
  return tower({
    id: o.id,
    name: o.name,
    kind: "building",
    built: o.built,
    m: o.m,
    draw: (b, m) => {
      const lv = m.levels.map(([z0, z1, ring]) => [z0 * k, z1 * k, ring]);
      b.color("#D6CFBF");
      stack(b, o.top ? withTop(lv, o.top) : lv);
    },
    facts: { ...o.facts, Architects: "Associated Architects (Raymond Hood and others)" },
    sources: [WP + o.wiki, ...o.ctbuh === false ? [] : [CTBUH], FOOT, OSM]
  });
}
var TOWERS = [
  tower({
    id: "empire_state_building",
    name: "Empire State Building",
    kind: "tower",
    built: [1930.21, 1931.33],
    m: M.esb,
    draw: drawEmpireState,
    facts: {
      Construction: "17 Mar 1930 \u2013 opened 1 May 1931",
      Height: "381 m (1,250 ft) roof; 443.2 m (1,454 ft) with the antenna",
      Floors: "102",
      Architects: "Shreve, Lamb & Harmon",
      "Set-backs": "21st, 25th, 30th, 72nd, 81st, 85th storeys",
      Model: "plan from the city footprint; set-back heights from OpenStreetMap parts (re-centred on the lot); mast widths and the buttress heights estimated from photos"
    },
    sources: [WP + "Empire_State_Building", CTBUH, "https://s-media.nyc.gov/agencies/lpc/lp/2000.pdf", FOOT, OSM]
  }),
  tower({
    id: "empire_state_antenna",
    name: "Empire State Building antenna",
    kind: "tower",
    built: [1950.57, 1953],
    m: M.esb,
    draw: (b) => drawEmpireStateAntenna(b),
    replaces: false,
    facts: {
      Construction: "begun 27 Jul 1950, completed 1953",
      Height: "tip 443.2 m (1,454 ft); pinnacle 62 m (203 ft)",
      Model: "drawn as today's pinnacle for its whole life; lattice widths estimated"
    },
    sources: [WP + "Empire_State_Building", CTBUH]
  }),
  tower({
    id: "chrysler_building",
    name: "Chrysler Building",
    kind: "tower",
    built: [1928.87, 1930.4],
    m: M.chrysler,
    draw: drawChrysler,
    facts: {
      Construction: "excavation Nov 1928, steel from 27 Mar 1929 \u2013 opened 27 May 1930",
      Height: "318.9 m (1,046 ft) spire; roof 282 m (925 ft)",
      Floors: "77",
      Architect: "William Van Alen",
      Crown: "seven terraced arches of Nirosta steel; eagles at the 61st floor",
      Model: "plan from the city footprint; set-back and crown-tier heights from OpenStreetMap parts; ornament sizes estimated"
    },
    sources: [WP + "Chrysler_Building", CTBUH, "https://s-media.nyc.gov/agencies/lpc/lp/0992.pdf", FOOT, OSM]
  }),
  tower({
    id: "one_world_trade_center",
    name: "One World Trade Center",
    kind: "tower",
    built: [2006.32, 2014.84],
    m: M.onewtc,
    draw: drawOneWTC,
    facts: {
      Construction: "27 Apr 2006 \u2013 opened 3 Nov 2014 (spire complete 10 May 2013)",
      Height: "541.3 m (1,776 ft); roof 417.0 m (1,368 ft)",
      Floors: "94 (numbered to 104)",
      Architect: "David Childs, Skidmore, Owings & Merrill",
      Form: "61 m square base, 56 m podium, eight isosceles triangles",
      Model: "base from the city footprint; mast taper and ring width estimated (ring radius from OpenStreetMap)"
    },
    sources: [WP + "One_World_Trade_Center", "https://www.skyscrapercenter.com/building/one-world-trade-center/98", FOOT, OSM]
  }),
  tower({
    id: "woolworth_building",
    name: "Woolworth Building",
    kind: "tower",
    built: [1910.84, 1913.31],
    m: M.woolworth,
    draw: drawWoolworth,
    facts: {
      Construction: "Nov 1910 \u2013 opened 24 Apr 1913",
      Height: "241.4 m (792 ft)",
      Floors: "55 (60 counting the pyramid)",
      Architect: "Cass Gilbert",
      Model: "base from the city footprint; tower plan, pyramid and gallery heights from the LPC report; stage heights from OpenStreetMap parts; tourelle and lantern sizes estimated"
    },
    sources: [WP + "Woolworth_Building", CTBUH, "https://s-media.nyc.gov/agencies/lpc/lp/1273.pdf", FOOT, OSM]
  }),
  tower({
    id: "flatiron_building",
    name: "Flatiron Building",
    kind: "building",
    built: [1901.45, 1902.75],
    m: M.flatiron,
    draw: (b) => drawFlatiron(b),
    facts: {
      Construction: "1901 \u2013 opened 1 Oct 1902",
      Height: "93.6 m (307 ft) with the 1905 penthouse; 86.9 m (285 ft) as built",
      Floors: "22",
      Architect: "D. H. Burnham & Co.",
      Model: "triangle from the city footprint; base and capital levels and the penthouse outline estimated from photos; the penthouse is drawn from the start"
    },
    sources: [WP + "Flatiron_Building", CTBUH, "https://s-media.nyc.gov/agencies/lpc/lp/0219.pdf", FOOT]
  }),
  tower({
    id: "rockefeller_30",
    name: "30 Rockefeller Plaza (RCA Building)",
    kind: "tower",
    built: [1931.6, 1933.35],
    m: M.rock30,
    draw: drawRock30,
    facts: {
      Construction: "1931 (steel from Mar 1932) \u2013 opened 1933",
      Height: "259.1 m (850 ft)",
      Floors: "66",
      Architects: "Associated Architects (Raymond Hood)",
      Model: "plan from the city footprint; set-backs from OpenStreetMap parts; nothing estimated but the colours"
    },
    sources: [WP + "30_Rockefeller_Plaza", CTBUH, "https://s-media.nyc.gov/agencies/lpc/lp/1446.pdf", FOOT, OSM]
  }),
  rockefellerBlock({
    id: "rockefeller_international_building",
    name: "International Building (Rockefeller Center)",
    m: M.rc_international,
    built: [1933.5, 1935.33],
    top: 156.1,
    wiki: "International_Building_(Rockefeller_Center)",
    facts: {
      Construction: "1933 \u2013 1 May 1935",
      Height: "156.1 m (512 ft)",
      Floors: "41",
      Model: "plan from the city footprint (tower and the two Fifth Avenue wings); set-backs from OpenStreetMap parts"
    }
  }),
  rockefellerBlock({
    id: "rockefeller_plaza_1",
    name: "1 Rockefeller Plaza (Time & Life Building of 1937)",
    m: M.rc_1rock,
    built: [1936.5, 1937.9],
    top: 149,
    wiki: "1_Rockefeller_Plaza",
    facts: {
      Construction: "1936 \u2013 1937",
      Height: "149 m (CTBUH)",
      Floors: "34",
      Model: "plan from the city footprint; set-backs from OpenStreetMap parts"
    }
  }),
  rockefellerBlock({
    id: "rockefeller_1270_sixth",
    name: "1270 Avenue of the Americas (RKO Building)",
    m: M.rc_1270,
    built: [1931.7, 1932.9],
    top: 124.7,
    wiki: "Rockefeller_Center",
    facts: {
      Construction: "completed 1932",
      Height: "124.7 m (CTBUH)",
      Floors: "31",
      Model: "plan from the city footprint; set-backs from OpenStreetMap parts; start of construction estimated (late 1931)"
    }
  }),
  rockefellerBlock({
    id: "rockefeller_plaza_10",
    name: "10 Rockefeller Plaza (Eastern Air Lines Building)",
    m: M.rc_10rock,
    built: [1939.5, 1940.9],
    top: 69.5,
    wiki: "10_Rockefeller_Plaza",
    facts: {
      Construction: "1939 \u2013 1940",
      Height: "69.5 m (CTBUH)",
      Floors: "17",
      Model: "plan from the city footprint; set-backs from OpenStreetMap parts"
    }
  }),
  rockefellerBlock({
    id: "rockefeller_plaza_50",
    name: "50 Rockefeller Plaza (Associated Press Building)",
    m: M.rc_50rock,
    built: [1937.5, 1938.9],
    top: 69.5,
    wiki: "50_Rockefeller_Plaza",
    facts: {
      Construction: "completed 1938",
      Height: "69.5 m (CTBUH)",
      Floors: "17",
      Model: "plan from the city footprint; set-backs from OpenStreetMap parts, cut at the cited height (the roof bulkhead is left out); start of construction estimated (1937)"
    }
  }),
  rockefellerBlock({
    id: "rockefeller_british_empire_building",
    name: "British Empire Building",
    m: M.rc_british,
    built: [1932.3, 1933.5],
    scale: 27.4 / 25,
    wiki: "British_Empire_Building",
    ctbuh: false,
    facts: {
      Construction: "completed 1933",
      Height: "roof 27.4 m (90 ft) without the penthouse",
      Floors: "6 and a penthouse",
      Model: "plan from the city footprint; set-back and penthouse outlines from OpenStreetMap parts, their heights stretched so that the main roof meets the cited 90 ft; start of construction estimated (1932)"
    }
  }),
  rockefellerBlock({
    id: "rockefeller_maison_francaise",
    name: "La Maison Fran\xE7aise",
    m: M.rc_maison,
    built: [1932.3, 1933.5],
    scale: 27.4 / 25,
    wiki: "La_Maison_Francaise_(Rockefeller_Center)",
    ctbuh: false,
    facts: {
      Construction: "completed 1933",
      Height: "roof 27.4 m (90 ft) without the penthouse",
      Floors: "6 and a penthouse",
      Model: "plan from the city footprint; set-back and penthouse outlines from OpenStreetMap parts, their heights stretched so that the main roof meets the cited 90 ft; start of construction estimated (1932)"
    }
  }),
  rockefellerBlock({
    id: "radio_city_music_hall",
    name: "Radio City Music Hall",
    m: M.rc_radiocity,
    built: [1931.9, 1932.99],
    wiki: "Radio_City_Music_Hall",
    ctbuh: false,
    facts: {
      Construction: "opened 27 Dec 1932",
      Height: "35 m (OpenStreetMap; the city measures 35.1 m)",
      Model: "plan from the city footprint; the two levels from OpenStreetMap parts; start of construction estimated (end of 1931); the marquee is not modelled"
    }
  }),
  tower({
    id: "wtc_7",
    name: "7 World Trade Center",
    kind: "tower",
    built: [2002.35, 2006.39],
    m: M.wtc7,
    draw: drawWTC7,
    facts: {
      Construction: "2002 \u2013 opened 23 May 2006",
      Height: "226.5 m (743 ft)",
      Floors: "52",
      Architect: "David Childs, Skidmore, Owings & Merrill",
      Model: "prism on the city footprint; height of the ten-storey louvred base estimated"
    },
    sources: [WP + "7_World_Trade_Center", CTBUH, FOOT]
  }),
  tower({
    id: "wtc_3",
    name: "3 World Trade Center",
    kind: "tower",
    built: [2008.05, 2018.44],
    m: M.wtc3,
    draw: (b) => drawWTC3(b),
    facts: {
      Construction: "groundbreaking Jan 2008 (podium by 2012) \u2013 opened 11 Jun 2018",
      Height: "328.9 m (1,079 ft)",
      Floors: "80",
      Architect: "Rogers Stirk Harbour + Partners",
      Model: "outlines from the city footprint; podium and set-back heights (75, 220, 281 m) from OpenStreetMap parts, unverified; bracing pattern schematic"
    },
    sources: [WP + "3_World_Trade_Center", CTBUH, FOOT, OSM]
  }),
  tower({
    id: "wtc_4",
    name: "4 World Trade Center",
    kind: "tower",
    built: [2008.05, 2013.87],
    m: M.wtc4,
    draw: drawWTC4,
    facts: {
      Construction: "groundbreaking Jan 2008 \u2013 opened 13 Nov 2013",
      Height: "297.7 m (977 ft)",
      Floors: "72 above ground",
      Architect: "Fumihiko Maki",
      Model: "outlines from the city footprint and OpenStreetMap parts; podium (25 m) and section break (220 m) from OpenStreetMap"
    },
    sources: [WP + "4_World_Trade_Center", CTBUH, FOOT, OSM]
  }),
  tower({
    id: "metlife_tower",
    name: "Metropolitan Life Insurance Company Tower",
    kind: "tower",
    built: [1907, 1909.5],
    m: M.metlife_tower,
    draw: drawMetLifeTower,
    facts: {
      Construction: "1907 \u2013 1909",
      Height: "213.4 m (700 ft)",
      Floors: "49",
      Architect: "Napoleon LeBrun & Sons",
      Model: "shaft on the city footprint; loggia, roof and cupola levels from OpenStreetMap parts; clock level estimated"
    },
    sources: [WP + "Metropolitan_Life_Insurance_Company_Tower", CTBUH, "https://s-media.nyc.gov/agencies/lpc/lp/1530.pdf", FOOT, OSM]
  }),
  tower({
    id: "wall_40",
    name: "40 Wall Street",
    kind: "tower",
    built: [1929.35, 1930.33],
    m: M.wall40,
    draw: drawWall40,
    pad: -3,
    // 23 Wall St's tall neighbour (BIN 1001017) stands 14 m east of the outline
    facts: {
      Construction: "1929 \u2013 1 May 1930",
      Height: "282.5 m (927 ft)",
      Floors: "70",
      Architects: "H. Craig Severance, Yasuo Matsui",
      Model: "plan from the city footprint; set-backs and pyramid base from OpenStreetMap parts; lantern and spire proportions estimated"
    },
    sources: [WP + "40_Wall_Street", CTBUH, "https://s-media.nyc.gov/agencies/lpc/lp/1936.pdf", FOOT, OSM]
  }),
  tower({
    id: "pine_70",
    name: "70 Pine Street",
    kind: "tower",
    built: [1930.37, 1932.37],
    m: M.pine70,
    draw: drawPine70,
    facts: {
      Construction: "May 1930 \u2013 1932",
      Height: "290.2 m (952 ft) with the 37.8 m (124 ft) spire",
      Floors: "67",
      Architects: "Clinton & Russell, Holton & George",
      Model: "plan from the city footprint; set-backs from OpenStreetMap parts; lantern and pinnacle widths estimated"
    },
    sources: [WP + "70_Pine_Street", CTBUH, "https://s-media.nyc.gov/agencies/lpc/lp/2441.pdf", FOOT, OSM]
  }),
  tower({
    id: "citigroup_center",
    name: "Citigroup Center (601 Lexington Avenue)",
    kind: "tower",
    built: [1974.3, 1977.8],
    m: M.citigroup,
    draw: (b) => drawCitigroup(b),
    facts: {
      Construction: "groundbreaking Apr 1974 \u2013 1977",
      Height: "278.9 m (915 ft)",
      Floors: "59",
      Architects: "Hugh Stubbins, Emery Roth & Sons; engineer William LeMessurier",
      Form: "raised 34 m (112 ft) on four mid-face stilts over St Peter\u2019s Church; 45\xB0 roof",
      Model: "tower placed from the city footprint (47.9 m square, from the 45\xB0 roof\u2019s cited 160 ft rise); core width, wing and church heights from OpenStreetMap parts; church form schematic"
    },
    sources: [WP + "Citigroup_Center", CTBUH, "https://s-media.nyc.gov/agencies/lpc/lp/2582.pdf", FOOT, OSM]
  }),
  tower({
    id: "park_432",
    name: "432 Park Avenue",
    kind: "tower",
    built: [2012.1, 2015.98],
    m: M.park432,
    draw: (b) => drawPark432(b),
    // the main lot only: the 7.6 m strip BIN 1035787 (recorded at 425.5 m) goes by the
    // viewer's tall-sliver rule; a wider outline would also hide 111 E 56th St's tower
    rings: [0],
    pad: -0.5,
    facts: {
      Construction: "excavation early 2012 \u2013 23 Dec 2015",
      Height: "425.5 m (1,396 ft)",
      Floors: "85",
      Architect: "Rafael Vi\xF1oly",
      Model: "tower square from OpenStreetMap (28.5 m); windbreak heights, plaza and pavilion heights estimated"
    },
    sources: [WP + "432_Park_Avenue", CTBUH, FOOT, OSM]
  }),
  tower({
    id: "one_vanderbilt",
    name: "One Vanderbilt",
    kind: "tower",
    built: [2016.8, 2020.7],
    m: M.vanderbilt1,
    draw: drawVanderbilt,
    facts: {
      Construction: "Oct 2016 \u2013 opened 14 Sep 2020",
      Height: "427 m (1,401 ft) spire; roof 396.5 m (1,301 ft)",
      Floors: "62 (numbered to 73)",
      Architect: "Kohn Pedersen Fox",
      Model: "base from the city footprint; stepped volumes from OpenStreetMap parts (the real faces taper between the steps); spire width estimated"
    },
    sources: [WP + "One_Vanderbilt", CTBUH, FOOT, OSM]
  }),
  tower({
    id: "central_park_tower",
    name: "Central Park Tower",
    kind: "tower",
    built: [2014.37, 2020.9],
    m: M.cpt,
    draw: drawCentralParkTower,
    // official outline less the cantilever's shadow, held 14 m off the centroid of the
    // 85 m neighbour in the lot's south-west notch (BIN 1024901)
    hide: [[[28.2, -31.2], [-16.3, -31.2], [-16.2, -17], [-18.5, -10], [-45.8, -10], [-45.5, -1.9], [-29.8, -1.9], [-29.7, 29], [28.7, 29.4]]],
    facts: {
      Construction: "excavation May 2014 \u2013 2020",
      Height: "472.4 m (1,550 ft)",
      Floors: "98 (numbered to 136)",
      Architect: "Adrian Smith + Gordon Gill",
      Model: "base from the city footprint; tower outlines and levels from OpenStreetMap parts; 8.5 m (28 ft) cantilever from 89 m"
    },
    sources: [WP + "Central_Park_Tower", CTBUH, FOOT, OSM]
  }),
  tower({
    id: "steinway_hall",
    name: "Steinway Hall",
    kind: "building",
    built: [1924.5, 1925.82],
    m: M.w57_111,
    draw: (b) => drawSteinwayHall(b),
    facts: {
      Construction: "1924 \u2013 opened 27 Oct 1925",
      Height: "67 m (OpenStreetMap), 16 storeys",
      Architects: "Warren & Wetmore",
      Model: "schematic L-plan after the LPC description: 57th Street front of twelve storeys with the four-storey tower, 58th Street portion stepping back above the ninth and twelfth; the split of the lot between the two wings and the 4.2 m storey are estimated; the tower of 2022 on the same official footprint is a separate model"
    },
    sources: [WP + "111_West_57th_Street", "https://s-media.nyc.gov/agencies/lpc/lp/2100.pdf", FOOT, OSM]
  }),
  tower({
    id: "west_57th_111",
    name: "111 West 57th Street (Steinway Tower)",
    kind: "tower",
    built: [2014.5, 2021.9],
    m: M.w57_111,
    draw: drawW57,
    replaces: false,
    facts: {
      Construction: "2014 \u2013 2021 (CTBUH; Wikipedia: 2022)",
      Height: "435.3 m (1,428 ft)",
      Floors: "84",
      Width: "18 m (60 ft)",
      Architect: "SHoP Architects",
      Model: "tower, its 30 m base and the thirteen set-backs of the south face from OpenStreetMap parts"
    },
    sources: [WP + "111_West_57th_Street", CTBUH, OSM]
  }),
  tower({
    id: "hudson_yards_30",
    name: "30 Hudson Yards and the Shops",
    kind: "tower",
    built: [2014.5, 2019.2],
    m: M.hy30,
    draw: drawHY30,
    facts: {
      Construction: "2014 \u2013 opened 15 Mar 2019 (ceremony for the yards 4 Dec 2012)",
      Height: "387.1 m (1,270 ft)",
      Floors: "73",
      Architect: "Kohn Pedersen Fox",
      Edge: "triangular outdoor deck at 335 m (1,100 ft), opened Mar 2020",
      Model: "tower and deck from OpenStreetMap parts; the Shops on the official outline at an estimated 45 m"
    },
    sources: [WP + "30_Hudson_Yards", CTBUH, FOOT, OSM]
  }),
  tower({
    id: "hudson_yards_10",
    name: "10 Hudson Yards",
    kind: "tower",
    built: [2012.92, 2016.41],
    m: M.hy10,
    draw: drawHY10,
    facts: {
      Construction: "Dec 2012 \u2013 31 May 2016",
      Height: "267.6 m (878 ft)",
      Floors: "52",
      Architect: "Kohn Pedersen Fox",
      Model: "base from the city footprint; levels from OpenStreetMap parts"
    },
    sources: [WP + "10_Hudson_Yards", CTBUH, FOOT, OSM]
  }),
  tower({
    id: "vessel",
    name: "Vessel",
    kind: "monument",
    built: [2017.3, 2019.2],
    m: M.vessel,
    draw: (b) => drawVessel(b),
    hide: [circle(0, 0, 24.5, 24)],
    facts: {
      Construction: "Apr 2017 \u2013 opened 15 Mar 2019",
      Height: "45.7 m (150 ft), 16 levels",
      Width: "15 m (50 ft) at the base, 46 m (150 ft) at the top",
      Designer: "Thomas Heatherwick",
      Model: "two shells and eight landings stand for the 154 flights of stairs"
    },
    sources: [WP + "Vessel_(structure)", FOOT]
  }),
  tower({
    id: "bank_of_america_tower",
    name: "Bank of America Tower",
    kind: "tower",
    built: [2004.58, 2009.33],
    m: M.boa,
    draw: drawBoA,
    facts: {
      Construction: "2004 \u2013 2009",
      Height: "365.8 m (1,200 ft) spire; roof 288 m (945 ft)",
      Floors: "55",
      Architect: "Cookfox",
      Model: "base from the city footprint; shaft and crown facets from OpenStreetMap parts, the crown stretched to the cited roof; spire widths estimated"
    },
    sources: [WP + "Bank_of_America_Tower_(Manhattan)", CTBUH, FOOT, OSM]
  }),
  tower({
    id: "new_york_times_building",
    name: "The New York Times Building",
    kind: "tower",
    built: [2004.8, 2007.88],
    m: M.nyt,
    draw: drawNYT,
    facts: {
      Construction: "late 2004 \u2013 opened 19 Nov 2007",
      Height: "318.8 m (1,046 ft) mast; roof 228 m (748 ft)",
      Floors: "52",
      Architect: "Renzo Piano Building Workshop, FXFowle",
      Model: "base from the city footprint; tower from OpenStreetMap parts; screens to the cited 256 m (840 ft); mast width estimated"
    },
    sources: [WP + "The_New_York_Times_Building", CTBUH, FOOT, OSM]
  }),
  tower({
    id: "spruce_8",
    name: "8 Spruce Street (New York by Gehry)",
    kind: "tower",
    built: [2006.5, 2011.1],
    m: M.spruce8,
    draw: drawSpruce8,
    facts: {
      Construction: "2006 \u2013 opened Feb 2011",
      Height: "265.2 m (870 ft)",
      Floors: "76",
      Architect: "Frank Gehry",
      Model: "base from the city footprint; set-backs from OpenStreetMap parts; the rippled steel skin is not modelled"
    },
    sources: [WP + "8_Spruce_Street", CTBUH, FOOT, OSM]
  }),
  tower({
    id: "hearst_magazine_building",
    name: "Hearst Magazine Building",
    kind: "building",
    built: [1927.45, 1928.5],
    m: M.hearst,
    draw: drawHearstBase,
    facts: {
      Construction: "excavation by Jun 1927 \u2013 1928",
      Height: "six storeys (30 m in OpenStreetMap)",
      Architect: "Joseph Urban",
      Model: "official outline extruded to the OpenStreetMap height; the tower of 2006 is a separate model"
    },
    sources: [WP + "Hearst_Tower_(Manhattan)", "https://s-media.nyc.gov/agencies/lpc/lp/1625.pdf", FOOT, OSM]
  }),
  tower({
    id: "hearst_tower",
    name: "Hearst Tower",
    kind: "tower",
    built: [2003.33, 2006.75],
    m: M.hearst,
    draw: (b) => drawHearstTower(b),
    replaces: false,
    facts: {
      Construction: "30 Apr 2003 \u2013 2006",
      Height: "182 m (597 ft)",
      Floors: "46",
      Architect: "Foster + Partners",
      Model: "tower plan 48.8 \xD7 36.6 m centred on the base (40 ft skylight set-backs; OpenStreetMap gives 51 \xD7 39 m); eight diagrid tiers measured down from the roof; the chamfered corners are not modelled"
    },
    sources: [WP + "Hearst_Tower_(Manhattan)", CTBUH]
  }),
  tower({
    id: "leonard_56",
    name: "56 Leonard Street",
    kind: "tower",
    built: [2012.8, 2016.9],
    m: M.leonard56,
    draw: drawLeonard56,
    facts: {
      Construction: "foundations 2008, resumed Oct 2012 \u2013 2016 (CTBUH; Wikipedia: 2017)",
      Height: "250.2 m (821 ft)",
      Floors: "60",
      Architect: "Herzog & de Meuron",
      Model: "schematic: a 30 m base zone on the official outline (height estimated), a 775 m\xB2 shaft (gross floor area over 60 floors) and staggered slabs standing for the cantilevered floors; only the outline and the height are measured"
    },
    sources: [WP + "56_Leonard_Street", CTBUH, FOOT]
  }),
  tower({
    id: "un_secretariat",
    name: "United Nations Secretariat Building",
    kind: "tower",
    built: [1948.7, 1951.45],
    m: M.un_secretariat,
    draw: drawSecretariat,
    facts: {
      Construction: "Sep 1948 \u2013 Jun 1951",
      Height: "153.9 m (505 ft)",
      Floors: "39",
      Architects: "UN Board of Design (Wallace Harrison, Oscar Niemeyer, Le Corbusier and others)",
      Model: "slab on the city footprint; mechanical-band heights estimated"
    },
    sources: [WP + "United_Nations_Secretariat_Building", CTBUH, FOOT]
  }),
  tower({
    id: "un_general_assembly",
    name: "United Nations General Assembly and Conference buildings",
    kind: "building",
    built: [1950.1, 1952.78],
    m: M.un_ga,
    draw: drawUNGA,
    // official outline, its edge beside the Secretariat pulled 5 m east so that the slab's
    // own footprint (a separate model) is not caught by the viewer's tall-sliver rule
    hide: [M.un_ga.foot[0].map(([u, v]) => u > -14 && u < 6 && v < -36 && v > -124 ? [u + 5, v] : [u, v])],
    facts: {
      Construction: "1950 \u2013 opened Oct 1952",
      Height: "about 25 m; dome to 32 m (OpenStreetMap)",
      Architects: "UN Board of Design",
      Model: "outlines and heights from OpenStreetMap parts; flat roofs (the Assembly roof really sweeps up to the north); terrace height estimated"
    },
    sources: [WP + "United_Nations_General_Assembly_Building", FOOT, OSM]
  }),
  tower({
    id: "lever_house",
    name: "Lever House",
    kind: "building",
    built: [1950.5, 1952.33],
    m: M.lever,
    draw: drawLever,
    facts: {
      Construction: "1950 \u2013 opened 29 Apr 1952",
      Height: "93.6 m (307 ft)",
      Floors: "21",
      Architects: "Gordon Bunshaft and Natalie de Blois, Skidmore, Owings & Merrill",
      Model: "lot and garden court from the city footprint, tower from OpenStreetMap; storey heights of the raised slab and the column grid estimated"
    },
    sources: [WP + "Lever_House", CTBUH, "https://s-media.nyc.gov/agencies/lpc/lp/1277.pdf", FOOT, OSM]
  }),
  tower({
    id: "seagram_building",
    name: "Seagram Building",
    kind: "tower",
    built: [1955.7, 1958.39],
    m: M.seagram,
    draw: drawSeagram,
    facts: {
      Construction: "Sep 1955 \u2013 opened 22 May 1958",
      Height: "157 m (515 ft)",
      Floors: "38",
      Architects: "Ludwig Mies van der Rohe, Philip Johnson",
      Model: "plan from the city footprint; wing heights from OpenStreetMap parts"
    },
    sources: [WP + "Seagram_Building", CTBUH, "https://s-media.nyc.gov/agencies/lpc/lp/1664.pdf", FOOT, OSM]
  }),
  tower({
    id: "metlife_building",
    name: "MetLife Building (Pan Am Building)",
    kind: "tower",
    built: [1960.9, 1963.18],
    m: M.metlife_bldg,
    draw: drawMetLifeBuilding,
    facts: {
      Construction: "1960 \u2013 opened 7 Mar 1963",
      Height: "246.3 m (808 ft)",
      Floors: "59",
      Architects: "Emery Roth & Sons, Pietro Belluschi, Walter Gropius",
      Model: "base from the city footprint; tower outline from OpenStreetMap parts"
    },
    sources: [WP + "MetLife_Building", CTBUH, FOOT, OSM]
  }),
  tower({
    id: "municipal_building",
    name: "Manhattan Municipal Building",
    kind: "building",
    built: [1909.54, 1914.5],
    m: M.municipal,
    draw: drawMunicipal,
    facts: {
      Construction: "17 Jul 1909 \u2013 1914",
      Height: "176.8 m (580 ft) with the 25 ft statue Civic Fame",
      Floors: "40",
      Architect: "William M. Kendall, McKim, Mead & White",
      Model: "plan from the city footprint; tiers from OpenStreetMap parts; the central arch over Chambers Street is not cut out; statue schematic"
    },
    sources: [WP + "Manhattan_Municipal_Building", CTBUH, "https://s-media.nyc.gov/agencies/lpc/lp/0079.pdf", FOOT, OSM]
  }),
  tower({
    id: "park_row_building",
    name: "Park Row Building",
    kind: "tower",
    built: [1896.8, 1899.55],
    m: M.parkrow,
    draw: drawParkRow,
    facts: {
      Construction: "1896 \u2013 1899",
      Height: "119.2 m (391 ft)",
      Floors: "31 (26 full floors, a partial 27th and two four-storey cupolas)",
      Architect: "R. H. Robertson",
      Model: "official outline to the cited 102.1 m roof; the cupolas\u2019 size and position are estimated from photos within the cited height"
    },
    sources: [WP + "Park_Row_Building", CTBUH, "https://s-media.nyc.gov/agencies/lpc/lp/2024.pdf", FOOT]
  }),
  tower({
    id: "new_york_life_building",
    name: "New York Life Building",
    kind: "tower",
    built: [1926.5, 1928.95],
    m: M.nylife,
    draw: drawNYLife,
    facts: {
      Construction: "1926 \u2013 1928 (foundations from Aug 1925)",
      Height: "187.5 m (615 ft)",
      Floors: "40",
      Architect: "Cass Gilbert",
      Model: "plan from the city footprint; set-backs and the octagon from OpenStreetMap parts; pyramid height cited; finial estimated"
    },
    sources: [WP + "New_York_Life_Building", CTBUH, "https://s-media.nyc.gov/agencies/lpc/lp/2067.pdf", FOOT, OSM]
  }),
  tower({
    id: "williamsburgh_savings_bank_tower",
    name: "Williamsburgh Savings Bank Tower",
    kind: "tower",
    built: [1927.5, 1929.25],
    m: M.williamsburgh,
    draw: drawWilliamsburgh,
    facts: {
      Construction: "1927 \u2013 opened 1 Apr 1929 (cornerstone 9 Apr 1928)",
      Height: "156 m (512 ft)",
      Floors: "41",
      Architects: "Halsey, McCormack & Helmer",
      Model: "plan from the city footprint; set-backs from OpenStreetMap parts; dome proportions estimated"
    },
    sources: [WP + "Williamsburgh_Savings_Bank_Tower", CTBUH, "https://s-media.nyc.gov/agencies/lpc/lp/0971.pdf", FOOT, OSM]
  }),
  tower({
    id: "one_court_square",
    name: "One Court Square (Citicorp Building)",
    kind: "tower",
    built: [1987, 1990],
    m: M.courtsq,
    draw: drawCourtSquare,
    facts: {
      Construction: "1987 \u2013 1990 (CTBUH; Wikipedia: opened 1989)",
      Height: "205 m (673 ft)",
      Floors: "50",
      Architect: "Skidmore, Owings & Merrill",
      Model: "plan from the city footprint; stepped top from OpenStreetMap parts, raised to the cited height"
    },
    sources: [WP + "One_Court_Square", CTBUH, FOOT, OSM]
  })
];

// dump.ts
var only = process.argv.slice(2);
var out = [];
for (const lm of TOWERS) {
  if (only.length && !only.some((o) => lm.id.includes(o))) continue;
  const b = new MeshBuilder();
  lm.build(b);
  const m = b.build();
  out.push({ id: lm.id, name: lm.name, kind: lm.kind, facts: lm.facts, sources: lm.sources, built: lm.built, end: lm.end, anchor: lm.anchor, replaces: lm.replaces ?? [], pos: Array.from(m.positions.value).map((v) => Math.round(v * 100) / 100), col: Array.from(m.colors.value).map((v) => Math.round(v * 255)) });
}
writeFileSync(new URL("./mesh.json", import.meta.url), JSON.stringify(out));
console.log(out.map((o) => `${o.id}:${o.pos.length / 3}`).join(" "));
