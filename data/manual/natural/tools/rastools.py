"""Small raster helpers shared by the natural-landscape tools: disk structuring elements, Zhang-Suen thinning,
skeleton -> polylines, mask -> polygons."""
import numpy as np
from rasterio import features
from scipy import ndimage
from shapely.geometry import LineString, shape
from shapely.ops import unary_union


def disk(r):
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return (x * x + y * y) <= r * r


def thin(mask, max_iter=60):
    """Zhang-Suen thinning (numpy)."""
    m = np.pad(mask.astype(bool), 1)
    for _ in range(max_iter):
        changed = False
        for step in (0, 1):
            p2, p3, p4 = m[:-2, 1:-1], m[:-2, 2:], m[1:-1, 2:]
            p5, p6, p7 = m[2:, 2:], m[2:, 1:-1], m[2:, :-2]
            p8, p9 = m[1:-1, :-2], m[:-2, :-2]
            c = m[1:-1, 1:-1]
            nb = [p2, p3, p4, p5, p6, p7, p8, p9]
            B = sum(n.astype(np.uint8) for n in nb)
            A = sum(((~nb[i]) & nb[(i + 1) % 8]).astype(np.uint8) for i in range(8))
            if step == 0:
                cond = c & (B >= 2) & (B <= 6) & (A == 1) & ~(p2 & p4 & p6) & ~(p4 & p6 & p8)
            else:
                cond = c & (B >= 2) & (B <= 6) & (A == 1) & ~(p2 & p4 & p8) & ~(p2 & p6 & p8)
            if cond.any():
                m[1:-1, 1:-1] &= ~cond
                changed = True
        if not changed:
            break
    return m[1:-1, 1:-1]


def strict_thin(sk):
    """Remove the redundant corner pixels of an 8-connected skeleton (Yokoi connectivity number 1, not an end
    point), so that only true junctions have more than two neighbours.  Done in four parity passes so that no
    two neighbours go in the same pass."""
    m = np.pad(sk.astype(bool), 1)
    H, W = m.shape
    yy, xx = np.mgrid[1:H - 1, 1:W - 1]
    for _ in range(3):
        changed = False
        for py in (0, 1):
            for pxx in (0, 1):
                c = m[1:-1, 1:-1]
                x = [m[1:-1, 2:], m[:-2, 2:], m[:-2, 1:-1], m[:-2, :-2], m[1:-1, :-2], m[2:, :-2], m[2:, 1:-1], m[2:, 2:]]
                nb = sum(v.astype(np.uint8) for v in x)
                n8 = np.zeros(c.shape, np.int8)
                for k in (0, 2, 4, 6):
                    a_, b_, c_ = ~x[k], ~x[(k + 1) % 8], ~x[(k + 2) % 8]
                    n8 += a_.astype(np.int8) - (a_ & b_ & c_).astype(np.int8)
                rem = c & (n8 == 1) & (nb >= 2) & ((yy % 2) == py) & ((xx % 2) == pxx)
                if rem.any():
                    m[1:-1, 1:-1] &= ~rem
                    changed = True
        if not changed:
            break
    return m[1:-1, 1:-1]


def prune(sk, k):
    """Drop skeleton spurs shorter than k pixels: peel end points k times, then grow the surviving ends back."""
    K = np.ones((3, 3), int)
    sk = sk.copy()
    removed = np.zeros_like(sk)
    for _ in range(k):
        ends = sk & (ndimage.convolve(sk.astype(np.uint8), K, mode="constant") == 2)
        if not ends.any():
            break
        removed |= ends
        sk &= ~ends
    for _ in range(k):
        ends = sk & (ndimage.convolve(sk.astype(np.uint8), K, mode="constant") == 2)
        grow = removed & ndimage.binary_dilation(ends, structure=np.ones((3, 3), bool))
        if not grow.any():
            break
        sk |= grow
        removed &= ~grow
    return sk


def trace(skel, transform, min_len, spur_px=14):
    """Skeleton pixels -> list of LineStrings (map units), split at junctions, chains shorter than min_len dropped."""
    sk = strict_thin(prune(strict_thin(skel.astype(bool)), spur_px))
    H, W = sk.shape
    ys, xs = np.nonzero(sk)
    idx = -np.ones((H, W), np.int32)
    idx[ys, xs] = np.arange(len(ys))
    nbrs = [[] for _ in range(len(ys))]
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue
            yy, xx = ys + dy, xs + dx
            ok = (yy >= 0) & (yy < H) & (xx >= 0) & (xx < W)
            j = np.full(len(ys), -1, np.int32)
            j[ok] = idx[yy[ok], xx[ok]]
            for i in np.nonzero(j >= 0)[0]:
                nbrs[i].append(int(j[i]))
    deg = np.array([len(n) for n in nbrs])
    node = deg != 2
    visited = set()
    lines = []

    def walk(a, b):
        path = [a, b]
        visited.add((a, b)); visited.add((b, a))
        while not node[path[-1]]:
            cur, prev = path[-1], path[-2]
            nxt = [k for k in nbrs[cur] if k != prev]
            if not nxt:
                break
            visited.add((cur, nxt[0])); visited.add((nxt[0], cur))
            path.append(nxt[0])
            if nxt[0] == path[0]:
                break
        return path

    for a in np.nonzero(node)[0]:
        for b in nbrs[a]:
            if (a, b) not in visited:
                lines.append(walk(int(a), b))
    for a in np.nonzero(~node)[0]:  # closed loops without nodes
        for b in nbrs[a]:
            if (a, b) not in visited:
                lines.append(walk(int(a), b))
                break
    # pieces -> merged lines per connected skeleton component; components shorter than min_len are dropped
    from shapely.ops import linemerge
    comp, _ = ndimage.label(sk, structure=np.ones((3, 3), bool))
    groups = {}
    for p in lines:
        if len(p) < 2:
            continue
        cx, cy = transform * (xs[p] + 0.5, ys[p] + 0.5)
        ls = LineString(list(zip(np.atleast_1d(cx), np.atleast_1d(cy))))
        groups.setdefault(int(comp[ys[p[0]], xs[p[0]]]), []).append(ls)
    out = []
    for k, parts in groups.items():
        if sum(l.length for l in parts) < min_len:
            continue
        m = linemerge(parts)
        for l in (m.geoms if hasattr(m, "geoms") else [m]):
            if l.length >= 12.0:
                out.append(l)
    return out


def polygons(mask, transform, min_area=0.0, simplify=4.0):
    """Boolean mask -> list of shapely polygons (map units), lightly simplified."""
    out = []
    for geom, v in features.shapes(mask.astype("uint8"), mask=mask, transform=transform, connectivity=4):
        g = shape(geom)
        if g.area < min_area:
            continue
        g = g.simplify(simplify).buffer(0)
        if not g.is_empty and g.area >= min_area:
            out.append(g)
    return out
