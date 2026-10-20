"""2x upscale that smooths staircases but keeps real corners square.

The bitmap outline is traced into loops of straight segments. A vertex is
part of a staircase when both of its segments are short (at most MAX_STEP
pixels, at least one of them a single pixel) and both neighboring vertices
turn the opposite way. Runs of such steps are cut into straight lines through
the midpoints of their steps and the outline is rasterized at 2x. A lone 1x1
bevel between long edges (the rounded corners of o, S, 0, ...) instead gets
its corner quarter-pixels toggled, which keeps round shapes symmetric. So do
the corners around a 1px notch (the waist of 8, B, 3). Stroke ends, serifs,
brackets and other square corners stay square.
"""

MAX_STEP = 2
END_CUT = 0.5  # how far a staircase cut reaches into an adjacent long edge


def trace(grid):
    """Closed outline loops as lists of vertices, interior on the right (y down)."""
    h, w = len(grid), len(grid[0])

    def on(x, y):
        return 0 <= x < w and 0 <= y < h and grid[y][x]

    edges = {}
    for y in range(h + 1):
        for x in range(w + 1):
            # horizontal edge from (x,y) to (x+1,y)
            if x < w:
                if on(x, y) and not on(x, y - 1):
                    edges.setdefault((x, y), []).append((x + 1, y))
                if on(x, y - 1) and not on(x, y):
                    edges.setdefault((x + 1, y), []).append((x, y))
            if y < h:
                if on(x - 1, y) and not on(x, y):
                    edges.setdefault((x, y), []).append((x, y + 1))
                if on(x, y) and not on(x - 1, y):
                    edges.setdefault((x, y + 1), []).append((x, y))
    pinches = {v for v, outs in edges.items() if len(outs) > 1}
    loops = []
    while edges:
        start = next(iter(edges))
        loop = [start]
        cur = start
        prev_dir = None
        while True:
            outs = edges[cur]
            if len(outs) > 1 and prev_dir is not None:
                # at a pinch, turn right so 4-connected regions stay separate
                rx, ry = -prev_dir[1], prev_dir[0]
                nxt = next((o for o in outs if (o[0] - cur[0], o[1] - cur[1]) == (rx, ry)), outs[0])
            else:
                nxt = outs[0]
            outs.remove(nxt)
            if not outs:
                del edges[cur]
            prev_dir = (nxt[0] - cur[0], nxt[1] - cur[1])
            cur = nxt
            if cur == start and (start not in edges):
                break
            if cur == start:
                break
            loop.append(cur)
        loops.append(loop)
    return loops, pinches


def corners(loop):
    """Reduce a loop of unit steps to direction-change vertices."""
    n = len(loop)
    out = []
    for i in range(n):
        a, b, c = loop[i - 1], loop[i], loop[(i + 1) % n]
        d1 = (b[0] - a[0], b[1] - a[1])
        d2 = (c[0] - b[0], c[1] - b[1])
        if d1 != d2:
            out.append((b, d1, d2))
    return out


def classify(vs, pinches):
    """Per vertex of one loop: 'stair', 'bevel' or None.

    'stair' vertices belong to a run of at least two steps and are smoothed
    as an outline. A lone 1x1 step between long edges is a 'bevel' (the
    rounded corners of o, S, ...); it and its two corners get quarter-pixel
    rounding, which stays symmetric.
    """
    n = len(vs)
    pos = [v[0] for v in vs]
    # turn sign: cross product, >0 means right turn = convex (interior on right, y down)
    turn = [d1[0] * d2[1] - d1[1] * d2[0] for _, d1, d2 in vs]

    def seglen(i, j):
        return abs(pos[i][0] - pos[j][0]) + abs(pos[i][1] - pos[j][1])

    def step(i):
        j, k = (i - 1) % n, (i + 1) % n
        a, b = seglen(j, i), seglen(i, k)
        return (pos[i] not in pinches and max(a, b) <= MAX_STEP and min(a, b) == 1
                and turn[j] != turn[i] != turn[k])

    steps = [step(i) for i in range(n)]
    kinds = [None] * n
    # notch: the outline steps in 1px, runs at most MAX_STEP, and steps back
    # out (the waist of 8, B, 3). Round the two convex corners around it.
    for i in range(n):
        a, b, c, d = i, (i + 1) % n, (i + 2) % n, (i + 3) % n
        if (turn[a] > 0 and turn[d] > 0 and turn[b] < 0 and turn[c] < 0
                and seglen(a, b) == 1 and seglen(c, d) == 1 and seglen(b, c) <= MAX_STEP
                and seglen((a - 1) % n, a) > MAX_STEP and seglen(d, (d + 1) % n) > MAX_STEP):
            for m in (a, d):
                if pos[m] not in pinches:
                    kinds[m] = "bevel"
    for i in range(n):
        if not steps[i] or kinds[i]:
            continue
        j, k = (i - 1) % n, (i + 1) % n
        if steps[j] or steps[k]:
            kinds[i] = "stair"
        else:
            kinds[i] = "bevel"
            # round the corners on both ends of a 1x1 step too
            if seglen(j, i) == 1 and seglen(i, k) == 1:
                for m in (j, k):
                    if pos[m] not in pinches:
                        kinds[m] = "bevel"
    return kinds


def smooth_polygon(vs, kinds):
    """Cut each smoothable vertex: replace it with points part-way along its edges.

    Between two smoothable vertices the cuts meet at the edge midpoint, so a
    staircase becomes a straight line through the midpoints of its steps.
    """
    n = len(vs)
    pos = [v[0] for v in vs]
    flags = [k == "stair" for k in kinds]
    out = []
    for i in range(n):
        p = pos[i]
        if not flags[i]:
            out.append(p)
            continue
        for k in ((i - 1) % n, (i + 1) % n):
            q = pos[k]
            length = abs(q[0] - p[0]) + abs(q[1] - p[1])
            t = length / 2 if flags[k] else min(END_CUT, length / 2)
            ux, uy = (q[0] - p[0]) / length, (q[1] - p[1]) / length
            out.append((p[0] + ux * t, p[1] + uy * t))
    return out


# Sample slightly off the subpixel center so points exactly on a 45° edge
# resolve the same way everywhere.
BIAS = (0.013, 0.031)


def inside(polys, x, y):
    crossings = 0
    for poly in polys:
        n = len(poly)
        for i in range(n):
            (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
            if (y1 > y) != (y2 > y):
                if x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                    crossings += 1
    return crossings % 2 == 1


def upscale(grid):
    h, w = len(grid), len(grid[0])
    loops, pinches = trace(grid)
    polys = []
    bevels = []
    for loop in loops:
        vs = corners(loop)
        kinds = classify(vs, pinches) if len(vs) >= 4 else [None] * len(vs)
        polys.append(smooth_polygon(vs, kinds))
        bevels += [v for v, kind in zip(vs, kinds) if kind == "bevel"]
    out = [[inside(polys, (sx + 0.5) / 2 + BIAS[0], (sy + 0.5) / 2 + BIAS[1])
            for sx in range(2 * w)] for sy in range(2 * h)]
    for p, d1, d2 in bevels:
        concave = d1[0] * d2[1] - d1[1] * d2[0] < 0
        qx, qy = -d1[0] + d2[0], -d1[1] + d2[1]
        sx = 2 * p[0] + (0 if qx > 0 else -1)
        sy = 2 * p[1] + (0 if qy > 0 else -1)
        if 0 <= sx < 2 * w and 0 <= sy < 2 * h:
            out[sy][sx] = concave
    return out
