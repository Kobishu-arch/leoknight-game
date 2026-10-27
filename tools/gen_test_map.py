"""Writes maps/forchach_test.txt: a small test area loosely after Forchach.

The Lech with gravel banks on the left, spruce forest beyond it, a road curving
through the meadow from the south-west to the north-east, forest along the edges.
Run from the project root:  python3 tools/gen_test_map.py

Legend:  . grass   * flowers   = path   : gravel   ~ water   T spruce   r rock   P player start
"""
import math
import random

W, H = 56, 36
r = random.Random(7)
g = [['.'] * W for _ in range(H)]


def river_x(y):
    return 8 + 2.2 * math.sin(y / 5.5) + 1.2 * math.sin(y / 2.3)


for y in range(H):
    c = river_x(y)
    for x in range(W):
        d = x - c
        if -2.2 <= d <= 2.2:
            g[y][x] = '~'
        elif -3.6 - r.random() <= d <= 3.4 + r.random() * 1.5:
            g[y][x] = ':'

# road: quadratic curve from the south-west to the north-east, two tiles wide
p0, p1, p2 = (15, H + 1), (20, 9), (W + 1, 6)
for i in range(400):
    t = i / 399
    x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
    y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
    for dx in (0, 1):
        for dy in (0, 1):
            X, Y = int(x) + dx, int(y) + dy
            if 0 <= X < W and 0 <= Y < H and g[Y][X] == '.':
                g[Y][X] = '='


def free(x, y):
    return 0 <= x < W and 0 <= y < H and g[y][x] in '.*'


def forest(x, y):
    left = x < river_x(y) - 4.5
    edge = x < 1 or y < 2 or x >= W - 2 or y >= H - 2
    south_east = x > 38 and y > 22 + (x - 38) * -0.4 + 2
    north = y < 5 and x < 40
    return left or edge or south_east or north


for y in range(H):
    for x in range(W):
        if not free(x, y): continue
        if forest(x, y):
            if (x + y) % 2 == 0 and r.random() < 0.85: g[y][x] = 'T'
        elif r.random() < 0.025:
            g[y][x] = 'T'
        elif r.random() < 0.015:
            g[y][x] = 'r'
        elif r.random() < 0.05:
            g[y][x] = '*'

# a few flower patches in the meadow
for (cx, cy) in ((30, 20), (22, 26), (44, 14)):
    for _ in range(14):
        x, y = cx + r.randrange(-3, 4), cy + r.randrange(-2, 3)
        if free(x, y): g[y][x] = '*'

# player start on the road; keep the way west to the river open (tests rely on it)
sy = 18
sx = next(x for x in range(W) if g[sy][x] == '=')
for x in range(int(river_x(sy)) + 3, sx):
    if g[sy][x] in 'Tr': g[sy][x] = '.'
g[sy][sx] = 'P'

open('maps/forchach_test.txt', 'w').write('\n'.join(''.join(row) for row in g) + '\n')
print('\n'.join(''.join(row) for row in g))
