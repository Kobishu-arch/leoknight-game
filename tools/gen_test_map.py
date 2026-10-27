"""Writes maps/forchach_test.txt: a 16 px test area loosely after Forchach.

The Lech with gravel banks and a wooden bridge in the west, a clearing in the spruce forest
beyond it, a road along the foot of a raised meadow (cliffs, stairs up), a fenced pasture.
Run from the project root:  python3 tools/gen_test_map.py

The file holds two grids of the same size, separated by an empty line:
  terrain:  . grass  * flowers  = path  : gravel  ~ water  H bridge  ^ raised meadow  S stairs
  objects:  . none  T spruce  o leafy tree  b bush  r rock  u stump  f fence  @ player start
"""
import math
import random

W, H = 80, 50
r = random.Random(11)
ter = [['.'] * W for _ in range(H)]
obj = [['.'] * W for _ in range(H)]


def river_x(y):
    return 13 + 3 * math.sin(y / 9) + 1.5 * math.sin(y / 4)


for y in range(H):
    c = river_x(y)
    for x in range(W):
        d = x - c
        if abs(d) <= 3.2:
            ter[y][x] = '~'
        elif -5.2 - r.random() <= d <= 5.0 + r.random() * 1.5:
            ter[y][x] = ':'
BY = 24  # bridge rows BY, BY+1
for y in (BY, BY + 1):
    for x in range(W):
        if ter[y][x] == '~': ter[y][x] = 'H'


def road(points, width=1):
    for (a, b) in zip(points, points[1:]):
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 3) + 1
        for i in range(n + 1):
            t = i / n
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            for dx in range(-width, width + 1):
                for dy in range(-width, width + 1):
                    if abs(dx) + abs(dy) > width: continue
                    X, Y = int(round(x)) + dx, int(round(y)) + dy
                    if 0 <= X < W and 0 <= Y < H and ter[Y][X] == '.': ter[Y][X] = '='


bx = int(river_x(BY))
road([(bx + 5, BY + 0.5), (30, BY + 1), (40, 26), (52, 24), (64, 25), (79, 24)])   # main road east
road([(31, BY + 1), (32, 12), (36, 0)])                                              # north
road([(40, 26), (38, 38), (40, 49)])                                                 # south
road([(bx - 6, BY + 0.5), (bx - 11, BY + 1)], width=0)                               # into the clearing

# raised meadow in the north-east; its south edge is a cliff wall with stairs in it
plateau = {(x, y) for y in range(H) for x in range(W)
           if ((x - 60) / 15.5) ** 2 + ((y - 11) / 8.2) ** 2 <= 1 and ter[y][x] == '.'}
for (x, y) in plateau: ter[y][x] = '^'
# the cliff front is two cells tall: the last two cells of each column
face = sorted((x, y) for (x, y) in plateau if (x, y + 1) not in plateau or (x, y + 2) not in plateau)
stairs = [(x, y) for (x, y) in face if x in (54, 55)]
for (x, y) in stairs: ter[y][x] = 'S'


def free(x, y, ok='.*^'):
    return 0 <= x < W and 0 <= y < H and ter[y][x] in ok and obj[y][x] == '.'


def blocked_near_stairs(x, y):
    return any(abs(x - sx) <= 1 and sy - 2 <= y <= sy + 3 for (sx, sy) in stairs)


# fenced pasture in the south-east with a gate at the top
for x in range(50, 71):
    for y in (32, 44):
        if not (y == 32 and x in (59, 60)) and free(x, y): obj[y][x] = 'f'
for y in range(33, 44):
    for x in (50, 70):
        if free(x, y): obj[y][x] = 'f'

# forest: spruces along the map edges and west of the river, a clearing by the bridge
for y in range(H):
    for x in range(W):
        if not free(x, y, '.*'): continue
        west = x < river_x(y) - 6.5
        clearing = west and abs(y - (BY + 0.5)) < 5 and x > river_x(y) - 15
        edge = x < 2 or y < 2 or x >= W - 2 or y >= H - 2
        if (west and not clearing) or edge:
            if (x + 2 * y) % 3 == 0 and r.random() < 0.9: obj[y][x] = 'T'
        elif clearing:
            if r.random() < 0.04: obj[y][x] = 'u'
            elif r.random() < 0.03: obj[y][x] = 'r'

# clover bushes along the foot of the cliff, like in Hyrule
for (x, y) in face:
    if (x, y) in stairs or blocked_near_stairs(x, y) or (x, y + 1) in plateau: continue
    if free(x, y + 1, '.*') and x % 3 != 0: obj[y + 1][x] = 'b'

# meadow: trees, bushes, rocks and flower patches
for y in range(3, H - 3):
    for x in range(3, W - 3):
        if not free(x, y, '.^') or blocked_near_stairs(x, y): continue
        if 50 <= x <= 70 and 32 <= y <= 44:   # pasture: open grass with a few flowers and stones
            if r.random() < 0.08: ter[y][x] = '*'
            elif r.random() < 0.01: obj[y][x] = 'r'
            continue
        p = r.random()
        if p < 0.012: obj[y][x] = 'o'
        elif p < 0.03: obj[y][x] = 'b'
        elif p < 0.036: obj[y][x] = 'r'
        elif p < 0.07 and ter[y][x] == '.': ter[y][x] = '*'
for (cx, cy) in ((24, 34), (44, 17), (62, 9)):
    for _ in range(22):
        x, y = cx + r.randrange(-4, 5), cy + r.randrange(-2, 3)
        if free(x, y, '.') : ter[y][x] = '*'

# player start on the main road; keep her way west to the river clear (the tests walk it)
sy = BY + 4
sx = next(x for x in range(int(river_x(sy)) + 4, W) if ter[sy][x] == '=')
for x in range(int(river_x(sy)) + 2, sx + 1): obj[sy][x] = '.'
obj[sy][sx] = '@'

text = '\n'.join(''.join(row) for row in ter) + '\n\n' + '\n'.join(''.join(row) for row in obj) + '\n'
open('maps/forchach_test.txt', 'w').write(text)
print('\n'.join(''.join(o if o != '.' else t for t, o in zip(tr, orow)) for tr, orow in zip(ter, obj)))
