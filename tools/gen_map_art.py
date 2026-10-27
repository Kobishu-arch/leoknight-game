"""Generates the prototype map art: art/tiles/terrain.png and the props in art/props/.

Run from the project root:  python3 tools/gen_map_art.py
Tiles are 32x32. Atlas layout (column, row):
  row 0: 0-2 grass, 3 flowers, 4-5 gravel
  row 1: path, column = bitmask of grass neighbours (N=1, E=2, S=4, W=8)
  row 2: water, column = bitmask of land neighbours (N=1, E=2, S=4, W=8)
"""
import random
from PIL import Image, ImageDraw

T = 32
rgb = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
OUT = rgb('#24141e')
GRASS = [rgb(c) for c in ('#2f6e26', '#3f8a2e', '#5ca83c', '#7cc44e')]
PATH = [rgb(c) for c in ('#7c5a36', '#a07c48', '#c8a064', '#e0bc80')]
GRAVEL = [rgb(c) for c in ('#7a766c', '#a8a498', '#c8c4b8', '#e4e0d8')]
WATER = [rgb(c) for c in ('#1f5e96', '#2a78b0', '#3c9ad0', '#6cc0e8')]
FOAM = rgb('#d8f0ff')
FLOWERS = [rgb(c) for c in ('#f4e04c', '#f8f8f0', '#e86a8a', '#9ab8f0')]


def tile(fill, seed):
    im = Image.new('RGBA', (T, T), fill)
    return im, random.Random(seed)


def grass(seed, tufts=10):
    im, r = tile(GRASS[2], seed)
    for _ in range(40):  # soft mottling
        im.putpixel((r.randrange(T), r.randrange(T)), GRASS[1] if r.random() < 0.6 else GRASS[3])
    for _ in range(tufts):  # little "v" tufts, dark under light
        x, y = r.randrange(1, T - 2), r.randrange(1, T - 1)
        im.putpixel((x, y), GRASS[0]); im.putpixel((x + 2, y), GRASS[0]); im.putpixel((x + 1, y), GRASS[1])
        im.putpixel((x, y - 1), GRASS[3]); im.putpixel((x + 2, y - 1), GRASS[3])
    return im


def flowers(seed):
    im = grass(seed, 5)
    r = random.Random(seed + 99)
    for _ in range(6):
        x, y = r.randrange(2, T - 2), r.randrange(2, T - 2)
        c = r.choice(FLOWERS)
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)): im.putpixel((x + dx, y + dy), c)
        im.putpixel((x, y), FLOWERS[0] if c != FLOWERS[0] else rgb('#c86a1c'))
        im.putpixel((x, y + 2), GRASS[0])
    return im


def speckle(base, ramp, seed, n_dark, n_light, stones=0):
    im, r = tile(ramp[2], seed)
    for _ in range(n_dark): im.putpixel((r.randrange(T), r.randrange(T)), ramp[1])
    for _ in range(n_light): im.putpixel((r.randrange(T), r.randrange(T)), ramp[3])
    for _ in range(stones):  # small round stones: light top, dark bottom
        x, y = r.randrange(1, T - 3), r.randrange(1, T - 3)
        for dx in (0, 1):
            im.putpixel((x + dx, y), ramp[3]); im.putpixel((x + dx, y + 1), ramp[1])
        im.putpixel((x, y + 2), ramp[0]); im.putpixel((x + 1, y + 2), ramp[0])
    return im


def edge_noise(r, i):
    return 2 + (1 if r.random() < 0.45 else 0) + (1 if r.random() < 0.15 else 0)


def path(mask):
    im = speckle(PATH[2], PATH, 300 + mask, 30, 14, stones=3)
    gr = grass(500 + mask, 4)
    r = random.Random(700 + mask)
    px, gp = im.load(), gr.load()
    # grass creeps onto the path from every side that borders grass, with a dark rim
    for side in range(4):
        if not mask & (1 << side): continue
        for i in range(T):
            d = edge_noise(r, i)
            for k in range(d + 1):
                x, y = {0: (i, k), 1: (T - 1 - k, i), 2: (i, T - 1 - k), 3: (k, i)}[side]
                px[x, y] = gp[x, y] if k < d else PATH[0]
    return im


def water(mask, seed=0):
    im, r = tile(WATER[2], 900 + mask + seed)
    px = im.load()
    for _ in range(5):  # wave highlights
        x, y = r.randrange(2, T - 6), r.randrange(2, T - 2)
        for k in range(r.randrange(3, 6)): px[x + k, y] = WATER[3]
        px[x + 1, y + 1] = WATER[1]
    for _ in range(25): px[r.randrange(T), r.randrange(T)] = WATER[1]
    # shore: dark line, then foam, wherever the water touches land
    for side in range(4):
        if not mask & (1 << side): continue
        for i in range(T):
            d = 1 + (1 if r.random() < 0.3 else 0)
            for k in range(d + 2):
                x, y = {0: (i, k), 1: (T - 1 - k, i), 2: (i, T - 1 - k), 3: (k, i)}[side]
                px[x, y] = GRAVEL[2] if k < d else (OUT if k == d else FOAM)
    return im


atlas = Image.new('RGBA', (16 * T, 3 * T), (0, 0, 0, 0))
row0 = [grass(1), grass(2, 14), grass(3, 6), flowers(4),
        speckle(GRAVEL[2], GRAVEL, 5, 40, 30, stones=6), speckle(GRAVEL[2], GRAVEL, 6, 30, 40, stones=4)]
for i, t in enumerate(row0): atlas.paste(t, (i * T, 0))
for m in range(16):
    atlas.paste(path(m), (m * T, T))
    atlas.paste(water(m), (m * T, 2 * T))
atlas.save('art/tiles/terrain.png')


def outline(im):
    w, h = im.size; src = im.load(); out = im.copy(); o = out.load()
    for y in range(h):
        for x in range(w):
            if src[x, y][3] == 0 and any(0 <= x + dx < w and 0 <= y + dy < h and src[x + dx, y + dy][3] > 128
                                         for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                o[x, y] = OUT
    return out


# Spruce (64x96), trunk base at (32, 90): stacked jagged tiers, lit from the upper left
SP = [rgb(c) for c in ('#143c26', '#1e5a32', '#2c7640', '#44964e')]
im = Image.new('RGBA', (64, 96), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
d.ellipse((14, 84, 50, 95), fill=(0, 0, 0, 70))
d.rectangle((29, 76, 35, 90), fill=rgb('#5a3820')); d.line((29, 76, 29, 90), fill=rgb('#7a5030'))
r = random.Random(42)
tiers = [(80, 30, 26), (64, 26, 24), (49, 21, 22), (35, 16, 20), (22, 11, 18), (11, 6, 14)]
for (base, half, height) in tiers:
    top = base - height
    pts = [(32, top - 2)]
    for k in range(9):  # jagged lower edge
        x = 32 - half + k * half * 2 // 8
        pts.append((x, base - (2 if k % 2 else 0)))
    pts.insert(1, (32 + half, base)); pts.append((32 - half, base))
    d.polygon([(32, top - 2), (32 + half, base), *[(32 + half - k * half // 4, base - (3 if k % 2 else 0)) for k in range(9)], (32 - half, base)], fill=SP[2])
    for y in range(top, base + 1):  # shading: dark right, light left edge
        for x in range(64):
            p = im.getpixel((x, y))
            if p[:3] != SP[2][:3]: continue
            rel = (x - 32) / max(1, half)
            if rel > 0.35: im.putpixel((x, y), SP[1])
            elif rel < -0.45 and r.random() < 0.7: im.putpixel((x, y), SP[3])
    for x in range(32 - half + 2, 32 + half - 1, 2):  # needle texture along the tier
        y = base - 2 - r.randrange(0, 3)
        if im.getpixel((x, y))[3]: im.putpixel((x, y), SP[0])
im = outline(im)
im.save('art/props/spruce.png')

# Rock (32x28), base at (16, 24)
im = Image.new('RGBA', (32, 28), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
d.ellipse((4, 18, 28, 27), fill=(0, 0, 0, 70))
d.polygon([(5, 22), (7, 12), (13, 6), (21, 7), (26, 13), (27, 22), (20, 25), (10, 25)], fill=GRAVEL[1])
d.polygon([(8, 13), (13, 8), (20, 8), (17, 13), (10, 16)], fill=GRAVEL[2])
d.line([(12, 9), (17, 9)], fill=GRAVEL[3]); d.line([(18, 14), (25, 20)], fill=GRAVEL[0]); d.line([(8, 22), (20, 24)], fill=GRAVEL[0])
outline(im).save('art/props/rock.png')
print('art written')
