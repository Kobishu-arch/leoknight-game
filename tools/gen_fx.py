"""Generates the flute's effect art in art/fx/:
  notes.png    two glowing golden music notes (12x12 each, side by side) that the flute shoots
  glow.png     16x16 soft halo in stepped rings, drawn additively behind each note
  sparkle.png  5x5 sparkle for the notes' trail and the burst when a note hits something
  wave.png     golden sound wave sweeping out of the flute, 3 frames of 32x32, facing right
  puff.png     10x8 little smoke cloud, for enemies vanishing
  alert.png    6x10 exclamation mark that pops up when an enemy spots the bard
Run from the project root:  python3 tools/gen_fx.py
"""
import math
from PIL import Image

hx = lambda h, a=255: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (a,)
DARK, MID, LIGHT, WHITE = hx('#a86818'), hx('#f0b830'), hx('#fff080'), hx('#ffffff')
GLOW = hx('#fff4a0', 110)
GLOW2 = hx('#fff4a0', 50)

# '#' note body, 'l' highlight; everything is drawn inside a 12x12 cell
EIGHTH = [
    "............",
    "......##....",
    "......#l#...",
    "......#..#..",
    "......#...#.",
    "......#...#.",
    "......#..#..",
    "...####.....",
    "..#l###.....",
    "..#####.....",
    "...###......",
    "............",
]
BEAMED = [
    "............",
    "...########.",
    "...#lllll##.",
    "...#.....#..",
    "...#.....#..",
    "...#.....#..",
    ".###...###..",
    "#l###.#l###.",
    "#####.#####.",
    ".###...###..",
    "............",
    "............",
]


def note(rows):
    im = Image.new('RGBA', (12, 12), (0, 0, 0, 0)); px = im.load()
    solid = {(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c in '#l'}
    for (x, y) in solid:
        c = rows[y][x]
        below_right = (x + 1, y) not in solid or (x, y + 1) not in solid
        px[x, y] = LIGHT if c == 'l' else (DARK if below_right else MID)
    for y in range(12):  # soft glow: two rings around the note
        for x in range(12):
            if (x, y) in solid: continue
            near = min((abs(x - a) + abs(y - b) for (a, b) in solid), default=9)
            if near == 1: px[x, y] = GLOW
            elif near == 2: px[x, y] = GLOW2
    for (x, y) in solid:
        if rows[y][x] == 'l' and (x - 1, y) not in solid: px[x, y] = WHITE
    return im


sheet = Image.new('RGBA', (24, 12), (0, 0, 0, 0))
sheet.paste(note(EIGHTH), (0, 0)); sheet.paste(note(BEAMED), (12, 0))
sheet.save('art/fx/notes.png')

# halo: stepped rings (pixel-art glow), brightest in the middle
glow = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
for y in range(16):
    for x in range(16):
        d = math.hypot(x - 7.5, y - 7.5)
        a = 150 if d < 3 else 90 if d < 5 else 45 if d < 6.5 else 18 if d < 8 else 0
        if a: glow.putpixel((x, y), hx('#ffe890', a))
glow.save('art/fx/glow.png')

# sparkle: a little four-pointed star
sp = Image.new('RGBA', (5, 5), (0, 0, 0, 0))
for (x, y, c) in [(2, 2, WHITE), (1, 2, LIGHT), (3, 2, LIGHT), (2, 1, LIGHT), (2, 3, LIGHT),
                  (0, 2, MID), (4, 2, MID), (2, 0, MID), (2, 4, MID)]:
    sp.putpixel((x, y), c)
sp.save('art/fx/sparkle.png')

# sound wave: a crescent bulging in the direction it travels; grows thinner and fainter
wave = Image.new('RGBA', (96, 32), (0, 0, 0, 0))
for f, (radius, width, alpha) in enumerate([(8, 3.0, 255), (11, 2.4, 220), (14, 1.6, 150)]):
    for y in range(32):
        for x in range(32):
            dx, dy = x - 6.5, y - 15.5   # centre of the arc, left of the frame middle
            r = math.hypot(dx, dy); ang = math.degrees(math.atan2(dy, dx))
            if abs(ang) > 62 or abs(r - radius) > width / 2 + 0.5: continue
            edge = abs(r - radius) > width / 2 - 0.5 or abs(ang) > 50
            c = MID if edge else (WHITE if abs(r - radius) < 0.6 and abs(ang) < 25 else LIGHT)
            wave.putpixel((f * 32 + x, y), c[:3] + (alpha if not edge else alpha * 2 // 3,))
wave.save('art/fx/wave.png')

# smoke puff: a little cloud of three round bumps, light on the upper left
puff = Image.new('RGBA', (10, 8), (0, 0, 0, 0))
bumps = [(3.0, 4.2, 2.8), (6.5, 4.4, 2.6), (4.8, 2.6, 2.4)]
inside = lambda x, y: any(math.hypot(x - cx, y - cy) <= r for cx, cy, r in bumps)
for y in range(8):
    for x in range(10):
        if not inside(x, y): continue
        edge = not all(inside(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        lit = not inside(x - 1, y - 1)
        shade = not inside(x + 1, y + 1)
        c = '#c8c0c4' if edge and shade else '#ffffff' if lit else '#a8a0a8' if shade else '#ece8ec'
        puff.putpixel((x, y), hx(c, 235))
puff.save('art/fx/puff.png')

# alert mark: a bold white "!" with a dark outline, like an enemy spotting you in Zelda
ALERT = [
    ".kkkk.",
    "kwwwwk",
    "kwwwwk",
    ".kwwk.",
    ".kwwk.",
    "..kk..",
    "......",
    "..kk..",
    ".kwwk.",
    "..kk..",
]
al = Image.new('RGBA', (6, 10), (0, 0, 0, 0))
for y, row in enumerate(ALERT):
    for x, c in enumerate(row):
        if c in 'kw': al.putpixel((x, y), hx('#3a1018' if c == 'k' else '#ffffff'))
al.save('art/fx/alert.png')
print('fx written')
