"""Generates the environment art: a cozy, round, Zelda-like (A Link to the Past) tileset at 16 px.

  art/tiles/terrain.png  (16 columns x 7 rows of 16x16 tiles)
    row 0  ground, one per map cell: 0-3 grass, 4-5 flowers, 6-7 grass tufts
    row 1  gravel bank      \
    row 2  dirt path         |  dual-grid overlays: the layer is shifted by half a tile, each tile
    row 3  water             |  sits between four map cells and the column is the mask of those
    row 4  cliff wall        |  cells that have the terrain (top-left 1, top-right 2,
    row 5  cliff top grass  /   bottom-left 4, bottom-right 8)
    row 6  0 bridge (upper half), 1 bridge (lower half), stairs: 2 single, 3 left end, 4 right end, 5 middle
  art/props/*.png  bush, rock, stump, fence (4 variants side by side), tree, spruce

Every overlay shape is rounded at its corners and wobbles a little along its edges; the wobble
repeats every 16 px, so neighbouring tiles always line up.
Run from the project root:  python3 tools/gen_map_art.py
"""
import math
import random
from PIL import Image, ImageDraw

T = 16
hx = lambda h, a=255: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (a,)
ramp = lambda *cs: [hx(c) for c in cs]
# palettes, dark -> light (sampled from A Link to the Past and warmed up a little)
GRASS = ramp('#2c6a30', '#3c8840', '#58a848', '#78c060', '#a0d878')
DIRT = ramp('#8a6438', '#a87c48', '#c89a60', '#dcb478', '#f0d098')
GRAVEL = ramp('#7c7058', '#9c9070', '#c8bc98', '#e0d8bc', '#f4eed8')
WATER = ramp('#2c4c9c', '#3a64c0', '#4c80d8', '#78a8ec', '#b8dcfc')
FOAM = hx('#e8f8ff')
ROCKW = ramp('#483020', '#6a4828', '#8a6034', '#a87c44', '#c89a5c')
WOOD = ramp('#5a3418', '#80502a', '#a87038', '#c89050', '#e0b070')
BUSH = ramp('#184828', '#24683a', '#348848', '#58a858', '#80c870')
STONE = ramp('#406858', '#5c8870', '#7cac90', '#a8d4b4', '#d0f0d8')
PINE = ramp('#163e30', '#1f5a3c', '#2c7646', '#46985a', '#6cb86c')
LEAF = ramp('#1c5a32', '#2a7a40', '#3e9a4c', '#62bc5c', '#8ed872')
EDGE_GREEN = hx('#245a2c')
OUT_GREEN, OUT_BROWN, OUT_BLUE = hx('#102818'), hx('#2a1a10'), hx('#1c2c5c')
FLOWERS = ramp('#f8f8f8', '#f8d848', '#ff9ab8', '#b0c8ff')


# ------------------------------------------------------------------ dual-grid shapes
def sdf_for(mask, r=6):
    """Signed distance (negative inside) of the mask's quadrants, with every corner rounded
    (closing rounds the inner corners, opening the outer ones). Quadrants continue past the
    tile edges, so the rounding only ever happens at the tile centre."""
    P = 20
    N = T + 2 * P
    inside = [[(mask >> ((1 if X - P >= T // 2 else 0) + (2 if Y - P >= T // 2 else 0))) & 1
               for X in range(N)] for Y in range(N)]

    def dist_to(val):
        R = r + 4
        d = [[0.0 if inside[y][x] == val else float(R) for x in range(N)] for y in range(N)]
        for y in range(P - R, P + T + R):
            for x in range(P - R, P + T + R):
                if inside[y][x] == val: continue
                best = R
                for dy in range(-R, R + 1):
                    for dx in range(-R, R + 1):
                        if inside[y + dy][x + dx] == val:
                            best = min(best, math.hypot(dx, dy))
                d[y][x] = best
        return d

    def grow():
        d = dist_to(1)
        return [[1 if inside[y][x] or d[y][x] <= r else 0 for x in range(N)] for y in range(N)]

    def shrink():
        d = dist_to(0)
        return [[1 if inside[y][x] and d[y][x] > r else 0 for x in range(N)] for y in range(N)]

    for step in (grow, shrink, shrink, grow):
        inside = step()
    din, dout = dist_to(0), dist_to(1)
    return [[(-din[y + P][x + P] if inside[y + P][x + P] else dout[y + P][x + P]) for x in range(T)] for y in range(T)]


def wobble(x, y):
    t = 2 * math.pi / T
    return 0.55 * math.sin(t * x + 0.7) * math.cos(t * y) + 0.45 * math.sin(t * y + 1.9) * math.cos(t * x + 0.4)


def sdf_of(m):
    if m == 0 or m == 15:
        return [[(-20.0 if m else 20.0)] * T for _ in range(T)]
    if m in (6, 9):  # diagonal: two separate round corners, never a thin bridge
        a, b = [sdf_for(q) for q in (1, 2, 4, 8) if m & q]
        raw = [[min(a[y][x], b[y][x]) for x in range(T)] for y in range(T)]
    else:
        raw = sdf_for(m)
    return [[raw[y][x] + wobble(x, y) for x in range(T)] for y in range(T)]


SDF = {m: sdf_of(m) for m in range(16)}


def overlay(mask, paint, shift=0.0):
    """paint(x, y, d) -> colour or None; d is the signed distance to the edge (negative inside)."""
    im = Image.new('RGBA', (T, T), (0, 0, 0, 0)); px = im.load()
    for y in range(T):
        for x in range(T):
            c = paint(x, y, SDF[mask][y][x] + shift)
            if c: px[x, y] = c
    return im


chance = lambda x, y, seed, p: random.Random((x * 92837 + y * 6113 + seed * 7919) & 0xffffffff).random() < p


def grass_px(x, y, seed=0):
    # mottled grass with little "v" tufts on a 8x8 lattice (repeats seamlessly every 16 px)
    c = GRASS[2]
    gx, gy = x // 8, y // 8
    rr = random.Random(gx * 131 + gy * 977 + seed * 17)
    tx, ty = gx * 8 + rr.randrange(1, 6), gy * 8 + rr.randrange(2, 7)
    if rr.random() < 0.7:
        if (x, y) in ((tx, ty), (tx + 2, ty)): c = GRASS[1]
        elif (x, y) == (tx + 1, ty + 1): c = GRASS[1]
        elif (x, y) in ((tx, ty - 1), (tx + 2, ty - 1)): c = GRASS[3]
    if c == GRASS[2] and chance(x, y, 3 + seed, 0.05): c = GRASS[3]
    return c


def path_paint(x, y, d):
    if d >= 1.0: return None
    if d >= 0: return EDGE_GREEN                        # dark grass lip
    if d > -1.2: return DIRT[1]                         # rim
    c = DIRT[2]
    gx, gy = x // 5, y // 5
    rr = random.Random(gx * 31 + gy * 73 + 1)
    cx, cy = gx * 5 + rr.randrange(1, 4), gy * 5 + rr.randrange(1, 4)
    if rr.random() < 0.35:
        if (x, y) == (cx, cy): c = DIRT[3]
        elif (x, y) == (cx + 1, cy) or (x, y) == (cx, cy + 1): c = DIRT[0] if (x, y) == (cx + 1, cy + 1) else DIRT[1]
    elif chance(x, y, 4, 0.06): c = DIRT[3]
    return c


def gravel_paint(x, y, d):
    if d >= 1.0: return None
    if d >= 0: return EDGE_GREEN
    if d > -1.2: return GRAVEL[1]
    c = GRAVEL[2]
    gx, gy = x // 4, y // 4
    rr = random.Random(gx * 53 + gy * 97 + 2)
    cx, cy = gx * 4 + rr.randrange(0, 3), gy * 4 + rr.randrange(0, 3)
    if (x, y) == (cx, cy): c = GRAVEL[4]
    elif (x, y) in ((cx + 1, cy), (cx, cy + 1)): c = GRAVEL[3]
    elif (x, y) == (cx + 1, cy + 1): c = GRAVEL[0]
    return c


def water_paint(x, y, d):
    if d >= 1.0: return None
    if d >= 0: return OUT_BLUE
    if d > -1.1: return FOAM
    if d > -2.4: return WATER[3]
    t = 2 * math.pi / T
    v = math.sin(t * (2 * x + 3 * math.sin(t * y)) + y * 0.8)
    if v > 0.92: return WATER[4]
    if v > 0.75: return WATER[3]
    if v < -0.9: return WATER[1]
    return WATER[2]


def cliff_wall_paint(x, y, d):
    if d >= 1.0: return None
    if d >= 0: return OUT_BROWN
    if d > -1.2: return ROCKW[0]
    # layered rock: a dark crack every 5 rows with a light ledge above it, short vertical joints
    wave = round(0.8 * math.sin(2 * math.pi * x / T))
    band = (y + wave) % 5
    c = ROCKW[2]
    if band == 0: c = ROCKW[0]
    elif band == 4: c = ROCKW[3]
    elif band == 1: c = ROCKW[1]
    if band in (2, 3) and (x + 5 * ((y + wave) // 5)) % 8 == 0: c = ROCKW[1]
    if band == 3 and (x + 5 * ((y + wave) // 5)) % 8 == 2: c = ROCKW[4]
    return c


def cliff_top_paint(x, y, d):
    if d >= 1.0: return None
    if d >= 0: return OUT_GREEN
    if d > -1.1: return GRASS[4]                        # sunny lip
    return grass_px(x, y, 5)


atlas = Image.new('RGBA', (16 * T, 7 * T), (0, 0, 0, 0))


def ground_tile(seed, flowers=0, tufts=0):
    im = Image.new('RGBA', (T, T)); px = im.load()
    for y in range(T):
        for x in range(T): px[x, y] = grass_px(x, y, seed)
    r = random.Random(seed)
    for _ in range(tufts):
        x, y = r.randrange(1, T - 3), r.randrange(2, T - 1)
        for dx in (0, 2): px[x + dx, y] = GRASS[0]; px[x + dx, y - 1] = GRASS[1]
        px[x + 1, y] = GRASS[1]; px[x + 1, y - 1] = GRASS[4]
    spots = [(4, 4), (11, 10), (10, 3), (3, 11)]
    for i in range(flowers):  # little white/yellow flowers like in Hyrule
        x, y = spots[i]
        c = FLOWERS[0] if i % 2 == 0 else FLOWERS[2 + (seed % 2)]
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)): px[x + dx, y + dy] = c
        px[x, y] = FLOWERS[1]; px[x + 1, y + 1] = GRASS[1]; px[x, y + 2] = GRASS[1]
    return im


for i, t in enumerate([ground_tile(0), ground_tile(1), ground_tile(2), ground_tile(3),
                       ground_tile(4, flowers=2), ground_tile(5, flowers=4), ground_tile(6, tufts=2), ground_tile(7, tufts=3)]):
    atlas.paste(t, (i * T, 0))
for m in range(1, 16):
    atlas.paste(overlay(m, gravel_paint), (m * T, T))
    atlas.paste(overlay(m, path_paint), (m * T, 2 * T))
    atlas.paste(overlay(m, water_paint), (m * T, 3 * T))
    atlas.paste(overlay(m, cliff_wall_paint), (m * T, 4 * T))
    atlas.paste(overlay(m, cliff_top_paint, shift=2.0), (m * T, 5 * T))   # inset: a rim of rock shows


def bridge(lower):
    im = Image.new('RGBA', (T, T), (0, 0, 0, 0)); px = im.load()
    for y in range(T):
        for x in range(T):
            k = x % 4  # planks across the bridge
            c = WOOD[3] if k == 0 else WOOD[2] if k < 3 else WOOD[1]
            if (x // 4 + y // 6) % 3 == 0 and y % 6 == 3: c = WOOD[1]   # nail / knot
            px[x, y] = c
    rail = range(12, 16) if lower else range(0, 4)
    for y in rail:
        for x in range(T):
            px[x, y] = [WOOD[4], WOOD[3], WOOD[2], WOOD[0]][y - rail.start] if not lower else [WOOD[0], WOOD[4], WOOD[2], OUT_BROWN][y - rail.start]
    for x0 in (1, 9):  # rail posts
        for y in rail:
            px[x0, y] = WOOD[1]; px[x0 + 1, y] = WOOD[0] if y != rail.start else WOOD[3]
    shade = 4 if not lower else 11
    for x in range(T): px[x, shade] = WOOD[0] if not lower else WOOD[1]
    return im


def stairs(left_wall, right_wall):
    im = Image.new('RGBA', (T, T), (0, 0, 0, 0)); px = im.load()
    for y in range(T):
        for x in range(T):
            step = y % 4
            c = [GRAVEL[4], GRAVEL[3], GRAVEL[2], GRAVEL[0]][step]
            if left_wall and x in (0, 1): c = ROCKW[0] if x == 0 else ROCKW[1]
            if right_wall and x in (14, 15): c = ROCKW[1] if x == 14 else ROCKW[0]
            px[x, y] = c
    return im


atlas.paste(bridge(False), (0, 6 * T)); atlas.paste(bridge(True), (T, 6 * T))
for i, (l, r_) in enumerate([(True, True), (True, False), (False, True), (False, False)]):
    atlas.paste(stairs(l, r_), ((2 + i) * T, 6 * T))
atlas.save('art/tiles/terrain.png')


# ------------------------------------------------------------------ props
def blob(size, circles):
    m = Image.new('1', size, 0); d = ImageDraw.Draw(m)
    for (x, y, r) in circles: d.ellipse((x - r, y - r, x + r, y + r), fill=1)
    return {(x, y) for y in range(size[1]) for x in range(size[0]) if m.getpixel((x, y))}


def sphere(im, region, rmp, cx, cy, rad):
    px = im.load()
    for (x, y) in region:
        nx, ny = (x - cx) / rad, (y - cy) / rad
        nz = math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
        l = -0.45 * nx - 0.6 * ny + 0.66 * nz
        px[x, y] = rmp[4] if l > 0.92 else rmp[3] if l > 0.62 else rmp[2] if l > 0.3 else rmp[1] if l > 0.0 else rmp[0]


def puffs(im, circles, rmp):
    """Round leafy puffs, back to front, each with a dark seam where it overlaps the ones behind."""
    px = im.load()
    for (x, y, r) in sorted(circles, key=lambda c: c[1]):
        region = blob(im.size, [(x, y, r)])
        sphere(im, region, rmp, x - r * 0.2, y - r * 0.25, r * 1.1)
        for (qx, qy) in region:
            for dx, dy in ((0, 1), (1, 0)):
                X, Y = qx + dx, qy + dy
                if (X, Y) not in region and 0 <= X < im.width and 0 <= Y < im.height and px[X, Y][3] > 0 and Y > y:
                    px[X, Y] = rmp[0]


def outline(im, dark):
    w, h = im.size; src = im.load(); out = im.copy(); o = out.load()
    for y in range(h):
        for x in range(w):
            if src[x, y][3] < 200 and any(0 <= x + dx < w and 0 <= y + dy < h and src[x + dx, y + dy][3] >= 200
                                          for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                o[x, y] = dark
    return out


def with_shadow(im, box):
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse(box, fill=(16, 40, 24, 90))
    sh.alpha_composite(im); return sh


# clover bush, 16x16, base at (8, 14)
im = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
puffs(im, [(5, 6, 3.6), (10, 6, 3.6), (5, 10, 3.6), (10, 10, 3.6), (7.5, 8, 3.2)], BUSH)
px = im.load()
for (x, y) in [(7, 3), (3, 8), (12, 8), (7, 13)]: px[x, y] = BUSH[1]   # gaps between the leaves
with_shadow(outline(im, OUT_GREEN), (2, 12, 13, 15)).save('art/props/bush.png')

# octagonal stone, 16x16, base at (8, 14)
im = Image.new('RGBA', (16, 16), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
oct_ = [(5, 2), (10, 2), (13, 5), (13, 10), (10, 13), (5, 13), (2, 10), (2, 5)]
d.polygon(oct_, fill=STONE[2])
d.polygon([(5, 3), (10, 3), (11, 6), (4, 6)], fill=STONE[4])        # top facet
d.polygon([(3, 5), (4, 6), (4, 10), (3, 10)], fill=STONE[3])       # left facet
d.polygon([(11, 6), (12, 5), (12, 10), (11, 10)], fill=STONE[1])   # right facet
d.polygon([(4, 11), (11, 11), (10, 12), (5, 12)], fill=STONE[0])   # bottom facet
d.line([(4, 6), (11, 6)], fill=STONE[3]); d.line([(4, 10), (11, 10)], fill=STONE[1])
with_shadow(outline(im, hx('#1c3028')), (2, 12, 13, 15)).save('art/props/rock.png')

# tree stump, 16x16, base at (8, 14)
im = Image.new('RGBA', (16, 16), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
d.rectangle((3, 6, 12, 12), fill=WOOD[1]); d.ellipse((3, 9, 12, 14), fill=WOOD[1])
for x in (5, 8, 11): d.line([(x, 8), (x, 12)], fill=WOOD[0])
d.ellipse((3, 3, 12, 9), fill=WOOD[3]); d.ellipse((5, 4, 10, 8), fill=WOOD[4]); d.ellipse((7, 5, 8, 7), fill=WOOD[2])
d.line([(4, 7), (11, 7)], fill=WOOD[2])
with_shadow(outline(im, OUT_BROWN), (2, 11, 14, 15)).save('art/props/stump.png')

# fence, 4 variants of 16x16: none, rail to the left, rail to the right, both; base at (8, 14)
fence = Image.new('RGBA', (64, 16), (0, 0, 0, 0))
for v in range(4):
    im = Image.new('RGBA', (16, 16), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for (y0, y1) in ((5, 6), (9, 10)):
        x0 = 0 if v & 1 else 6; x1 = 15 if v & 2 else 9
        d.rectangle((x0, y0, x1, y1), fill=WOOD[2]); d.line([(x0, y0), (x1, y0)], fill=WOOD[4]); d.line([(x0, y1), (x1, y1)], fill=WOOD[1])
    d.rectangle((6, 3, 9, 13), fill=WOOD[2]); d.ellipse((6, 2, 9, 5), fill=WOOD[3])
    d.line([(6, 4), (6, 13)], fill=WOOD[3]); d.line([(9, 4), (9, 13)], fill=WOOD[0]); d.point((7, 3), fill=WOOD[4])
    fence.alpha_composite(with_shadow(outline(im, OUT_BROWN), (5, 12, 10, 15)), (v * 16, 0))
fence.save('art/props/fence.png')

# round tree, 32x32, base at (16, 30)
im = Image.new('RGBA', (32, 32), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
d.rectangle((13, 22, 18, 29), fill=WOOD[1]); d.line([(13, 22), (13, 29)], fill=WOOD[2]); d.line([(18, 22), (18, 29)], fill=WOOD[0])
d.line([(12, 29), (19, 29)], fill=WOOD[0])
puffs(im, [(16, 7, 6), (9, 10, 6), (23, 10, 6), (6, 16, 5), (26, 16, 5), (16, 14, 7), (11, 19, 6), (21, 19, 6)], LEAF)
with_shadow(outline(im, OUT_GREEN), (5, 25, 27, 31)).save('art/props/tree.png')

# spruce, 24x32, base at (12, 30)
im = Image.new('RGBA', (24, 32), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
d.rectangle((10, 24, 13, 29), fill=WOOD[1]); d.line([(13, 24), (13, 29)], fill=WOOD[0])
for (y, n, r) in [(5, 1, 3), (9, 2, 3.2), (14, 3, 3.5), (19, 4, 3.6), (23, 4, 3.8)]:
    span = (n - 1) * r * 1.15
    puffs(im, [(12 - span / 2 + i * (span / max(1, n - 1)), y + (1 if i % 2 else 0), r) for i in range(n)] if n > 1 else [(12, y, r)], PINE)
with_shadow(outline(im, OUT_GREEN), (3, 26, 21, 31)).save('art/props/spruce.png')
print('art written')
