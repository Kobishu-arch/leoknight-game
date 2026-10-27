"""Generates the UI art in art/ui/:
  portrait_leo.png, portrait_krieger.png  dialogue portraits, cleaned up from the concept art in
                                          art/reference/ui/ (reduced to a real pixel-art palette,
                                          loose edge pixels removed)
  item_flute.png, item_lion.png           16x16 item icons, redrawn in the game's style after the
                                          concept icons
Run from the project root:  python3 tools/gen_ui.py
"""
import math
from PIL import Image, ImageDraw

hx = lambda h, a=255: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (a,)


def clean_portrait(src, dst, colors=32):
    im = Image.open(src).convert('RGBA')
    alpha = im.getchannel('A').point(lambda a: 255 if a >= 128 else 0)
    rgb = im.convert('RGB').quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert('RGB')
    out = Image.merge('RGBA', (*rgb.split(), alpha))
    px = out.load(); w, h = out.size
    # cut-out leftovers: loose pixels, and the light fringe of the old background along the edge
    for _ in range(2):
        edge = []
        for y in range(h):
            for x in range(w):
                if not px[x, y][3]: continue
                n = [(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                solid = sum(1 for (a, b) in n if 0 <= a < w and 0 <= b < h and px[a, b][3])
                light = sum(px[x, y][:3]) / 3 > 170
                if solid <= 1 or (solid < 4 and light): edge.append((x, y))
        for (x, y) in edge: px[x, y] = (0, 0, 0, 0)
    out.save(dst)
    return len({px[x, y][:3] for y in range(h) for x in range(w) if px[x, y][3]})


def outline(im, dark):
    w, h = im.size; src = im.load(); out = im.copy(); o = out.load()
    for y in range(h):
        for x in range(w):
            if src[x, y][3] == 0 and any(0 <= x + dx < w and 0 <= y + dy < h and src[x + dx, y + dy][3]
                                         for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                o[x, y] = dark
    return out


# silver transverse flute, lying diagonally (bottom left to top right), like the bard's
FLUTE = [hx('#6a7494'), hx('#b4bcd8'), hx('#ffffff')]
GOLD = [hx('#c8902c'), hx('#f8d860')]
im = Image.new('RGBA', (16, 16), (0, 0, 0, 0)); px = im.load()
for i in range(12):
    x, y = 2 + i, 13 - i
    px[x, y] = FLUTE[1]; px[x + 1, y] = FLUTE[0]; px[x, y - 1] = FLUTE[2] if i % 3 else FLUTE[1]
for i in (4, 6, 8):                       # finger holes
    px[2 + i, 13 - i] = FLUTE[0]
for i in (1, 10):                         # gold joint rings
    px[2 + i, 13 - i] = GOLD[1]; px[3 + i, 13 - i] = GOLD[0]
px[12, 2] = GOLD[1]                       # end cap
outline(im, hx('#262a44')).save('art/ui/item_flute.png')

# golden lion head: spiky mane, ears, stern brows, a muzzle with a dark nose
MANE = [hx('#7a3e0c'), hx('#b86c14'), hx('#e09a2c'), hx('#f8c858')]
FACE = [hx('#c08a3c'), hx('#ecc070'), hx('#fff0c0')]
DARK = hx('#2a1408')
im = Image.new('RGBA', (16, 16), (0, 0, 0, 0)); px = im.load()
for y in range(16):
    for x in range(16):
        dx, dy = x - 7.5, y - 8.0
        ang = math.atan2(dy, dx)
        if math.hypot(dx, dy) <= 6.3 + 0.9 * math.cos(ang * 9):      # nine spikes
            l = -0.5 * dx / 7 - 0.6 * dy / 7
            px[x, y] = MANE[3] if l > 0.45 else MANE[2] if l > -0.15 else MANE[1]
            if math.hypot(dx, dy) > 6.0: px[x, y] = MANE[1] if l > 0 else MANE[0]
d = ImageDraw.Draw(im)
for ex in (4, 10):                                                     # ears
    d.ellipse((ex, 2, ex + 2, 4), fill=FACE[1]); px[ex + 1, 3] = MANE[0]
d.ellipse((4, 4, 11, 13), fill=FACE[1])
for (x, y) in [(5, 5), (6, 5), (5, 6)]: px[x, y] = FACE[2]
for y in range(6, 13): px[11, y] = FACE[0]
d.line([(5, 12), (10, 12)], fill=FACE[0])
for (x, y) in [(5, 6), (6, 7), (10, 6), (9, 7)]: px[x, y] = MANE[0]      # brows
for (x, y) in [(6, 8), (9, 8)]: px[x, y] = DARK                         # eyes
for (x, y) in [(7, 9), (8, 9)]: px[x, y] = FACE[0]                      # nose bridge
for (x, y) in [(7, 10), (8, 10)]: px[x, y] = DARK                       # nose
for (x, y) in [(6, 11), (7, 11), (8, 11), (9, 11)]: px[x, y] = FACE[2]  # muzzle
px[7, 12] = FACE[0]; px[8, 12] = FACE[0]
outline(im, hx('#3a1a08')).save('art/ui/item_lion.png')

for name in ('leo', 'krieger'):
    n = clean_portrait(f'art/reference/ui/portrait_{name}.png', f'art/ui/portrait_{name}.png')
    print(f'portrait_{name}: {n} colours')
print('ui written')
