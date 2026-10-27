"""Generates the bard's frames: a simple, Link-like hero for 16 px tiles (24x28 frames).

Long dark hair, teal tunic with a red scarf, a silver transverse flute in her hand.
Animations: idle_down; walk_down / walk_up / walk_left (4 frames each); play_down / play_up /
play_left (3 frames: raise the flute, play, play); *_right = *_left mirrored.

Writes <out>/anim.json (frames for the Aseprite bridge's aseprite_animation tool),
<out>/tags.json and a preview strip <out>/anim_sheet.png.
Run:  python3 tools/bard_frames.py <out-dir>
The finished frames live in art/bard/bard_animations.aseprite; small fixes go there directly.
"""
import json
import sys
from PIL import Image, ImageDraw

W, H = 24, 28
# Drawing coordinates are for a 20x26 figure; it lands DX/DY px further right/down in the frame,
# which leaves room above the head for the walk bob and to the left for the flute in profile.
DX, DY = 2, 2
PAL = {'-': '#00000000'}
OUTLINE_OF = {}


def ramp(keys, cols, outline):
    for k, c in zip(keys, cols):
        PAL[k] = c
        OUTLINE_OF[k] = outline[0]
    PAL[outline[0]] = outline[1]
    return list(keys)


HAIR = ramp('123', ['#2a1612', '#462418', '#6a3a26'], ('!', '#140a0a'))
SKIN = ramp('abc', ['#c07a5c', '#f0b088', '#ffd8b4'], ('"', '#5a2e24'))
TUNIC = ramp('efg', ['#1e4e5c', '#2e7484', '#4ea0a8'], ('#', '#0e2830'))
SCARF = ramp('nop', ['#8a1c2c', '#c43240', '#e8606a'], ('%', '#3a0a14'))
BOOT = ramp('ABC', ['#3a2214', '#5e3a22', '#86562e'], ("'", '#1e100a'))
FLUTE = ramp('EFG', ['#6a7494', '#b4bcd8', '#ffffff'], (')', '#262a44'))
GOLD = ramp('ij', ['#c8902c', '#f8d860'], ('$', '#4a2c10'))
PAL['K'] = '#1a0e14'; OUTLINE_OF['K'] = '"'


class _Shifted:
    def __init__(self, d): self.d = d
    def ellipse(self, b, **kw): self.d.ellipse((b[0] + DX, b[1] + DY, b[2] + DX, b[3] + DY), **kw)
    def line(self, p, **kw): self.d.line([(x + DX, y + DY) for x, y in p], **kw)


class Frame:
    def __init__(f):
        f.c = [[None] * W for _ in range(H)]
        f.o = [[None] * W for _ in range(H)]

    def mask(f, fn):
        m = Image.new('1', (W, H), 0); fn(_Shifted(ImageDraw.Draw(m)))
        return {(x, y) for y in range(H) for x in range(W) if m.getpixel((x, y))}

    def ell(f, *boxes, mirror=False):
        s = f.mask(lambda d: [d.ellipse(b, fill=1) for b in boxes])
        return s | {(2 * (DX + 9) + 1 - x, y) for (x, y) in s} if mirror else s   # mirror about the figure's centre

    def thick(f, pts, w=1): return f.mask(lambda d: d.line(pts, fill=1, width=w))

    def paint(f, name, pts, r, inner=True):
        """Three tones: light on the top-left edge, dark on the bottom-right edge."""
        for (x, y) in pts:
            out = lambda dx, dy: (x + dx, y + dy) not in pts
            c = r[1]
            if out(1, 0) or out(0, 1): c = r[0]
            elif out(-1, 0) or out(0, -1): c = r[2]
            f.c[y][x] = c; f.o[y][x] = name
        if inner:  # dark line where this part overlaps another one
            for (x, y) in pts:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and (nx, ny) not in pts and f.o[ny][nx] not in (None, name):
                        f.c[y][x] = r[0]; break
        return pts

    def flat(f, name, pts, color):
        for (x, y) in pts: f.c[y][x] = color; f.o[y][x] = name

    def px(f, x, y, c):
        x += DX; y += DY
        if 0 <= x < W and 0 <= y < H: f.c[y][x] = c

    def flute(f, a, b):
        """Silver flute from a to b: light top, dark bottom, a dark joint in the middle."""
        f.flat('flute', f.thick([a, b], 1), FLUTE[1])
        (x0, y0), (x1, y1) = a, b
        if abs(x1 - x0) >= abs(y1 - y0):   # horizontal-ish: second row underneath
            f.flat('flute2', f.thick([(x0, y0 + 1), (x1, y1 + 1)], 1), FLUTE[0])
            f.px(min(x0, x1) + abs(x1 - x0) // 2, y0, FLUTE[0])
            f.px(min(x0, x1) + 1, y0, FLUTE[2])
        else:
            f.px(x0, y0, FLUTE[2])

    def rows(f):
        out = [r[:] for r in f.c]
        for y in range(H):
            for x in range(W):
                if f.c[y][x] is not None: continue
                for dx, dy in ((0, 1), (1, 0), (-1, 0), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and f.c[ny][nx] is not None:
                        out[y][x] = OUTLINE_OF.get(f.c[ny][nx], '!'); break
        return [''.join(c or '-' for c in r) for r in out]


def head_front(f, b, eyes='open', back=False):
    f.paint('crown', f.ell((3, 0 + b, 16, 11 + b)), HAIR)
    if back:
        f.paint('hairback', f.ell((4, 4 + b, 15, 15 + b), (5, 10 + b, 14, 19)), HAIR, inner=False)
        f.line_hair = None
        for (x, y) in [(6, 2), (7, 2), (5, 3), (12, 2)]: f.px(x, y + b, HAIR[2])
        f.px(9, 12 + b, HAIR[0]); f.px(9, 13 + b, HAIR[0]); f.px(10, 15 + b, HAIR[0]); f.px(10, 16 + b, HAIR[0])
        return
    f.paint('face', f.ell((5, 4 + b, 14, 12 + b)), SKIN)
    f.paint('bangs', f.ell(*[(5 + 3 * i, 2 + b, 8 + 3 * i, 5 + b + (i % 2)) for i in range(3)]), HAIR, inner=False)
    f.paint('lock', f.ell((3, 4 + b, 5, 12 + b), mirror=True), HAIR, inner=False)
    for (x, y) in [(6, 2), (7, 2), (5, 3), (12, 2)]: f.px(x, y + b, HAIR[2])     # shine
    if eyes == 'open':
        for x in (7, 12): f.px(x, 7 + b, 'K'); f.px(x, 8 + b, 'K')
    else:  # closed, happily playing
        for x in (7, 12): f.px(x, 8 + b, 'K'); f.px(x - 1, 7 + b, 'K') if x == 7 else f.px(x + 1, 7 + b, 'K')


def body_front(f, b, lift=(0, 0), back=False):
    for side in (-1, 1):   # boots
        d = -(lift[0] if side < 0 else lift[1])
        xs = (6, 8) if side < 0 else (11, 13)
        f.paint('boot%d' % side, f.ell((xs[0], 19 + d, xs[1], 23 + d)), BOOT)
    f.paint('tunic', f.ell((6, 11 + b, 13, 18 + b), (5, 14 + b, 14, 21 + b)), TUNIC)
    for x in range(6, 14): f.px(x, 16 + b, BOOT[0])
    if not back:
        f.px(9, 16 + b, GOLD[1]); f.px(10, 16 + b, GOLD[0])
        f.paint('scarf', f.ell((7, 11 + b, 12, 13 + b)), SCARF)


def front(b=0, lift=(0, 0), swing=(0, 0), blink=False, back=False):
    f = Frame()
    if not back:
        f.paint('hairback', f.ell((3, 7 + b, 5, 17 + b), mirror=True), HAIR)
    body_front(f, b, lift, back)
    for side in (-1, 1):   # arms at the sides; the flute hangs from her left hand
        sw = swing[0] if side < 0 else swing[1]
        xs = (4, 6) if side < 0 else (13, 15)
        f.paint('arm%d' % side, f.ell((xs[0], 12 + b, xs[1], 17 + b + sw)), TUNIC)
        f.paint('hand%d' % side, f.ell((xs[0], 16 + b + sw, xs[1], 18 + b + sw)), SKIN)
    fx, fy = (14, 17 + b + swing[1]) if not back else (5, 17 + b + swing[0])
    f.flute((fx, fy), (fx + (1 if not back else -1), fy + 6))
    head_front(f, b, 'closed' if blink else 'open', back)
    return f


def play_front(stage, b=0):
    """Facing down: the flute goes up to her lips, held out to her right (the viewer's left)."""
    f = Frame()
    f.paint('hairback', f.ell((3, 7 + b, 5, 17 + b), mirror=True), HAIR)
    body_front(f, b)
    if stage == 0:   # raising it
        f.paint('arm-1', f.ell((3, 12 + b, 6, 16 + b)), TUNIC)
        f.paint('arm1', f.ell((12, 12 + b, 15, 16 + b)), TUNIC)
        f.flute((2, 15 + b), (9, 13 + b))
        f.paint('hand-1', f.ell((3, 14 + b, 5, 16 + b)), SKIN); f.paint('hand1', f.ell((8, 12 + b, 10, 14 + b)), SKIN)
        head_front(f, b)
        return f
    f.paint('arm-1', f.ell((2, 11 + b, 6, 14 + b)), TUNIC)
    f.paint('arm1', f.thick([(13, 13 + b), (10, 11 + b)], 3), TUNIC)
    head_front(f, b, 'closed')
    f.flute((-1, 10 + b), (11, 10 + b))
    f.paint('hand-1', f.ell((2, 10 + b, 4, 12 + b)), SKIN); f.paint('hand1', f.ell((7, 10 + b, 9, 12 + b)), SKIN)
    return f


def play_back(stage, b=0):
    """Facing up: from behind, the flute sticks out to her right side."""
    f = Frame()
    body_front(f, b, back=True)
    f.paint('arm-1', f.ell((4, 12 + b, 6, 16 + b)), TUNIC)
    f.paint('arm1', f.ell((13, 11 + b, 16, 14 + b)), TUNIC)
    head_front(f, b, back=True)
    if stage == 0:
        f.flute((12, 14 + b), (19, 12 + b))
    else:
        f.flute((11, 10 + b), (21, 10 + b))
    f.paint('hand1', f.ell((15, 10 + b, 17, 12 + b) if stage else (15, 12 + b, 17, 14 + b)), SKIN)
    return f


# ---------------------------------------------------------------- side (facing left)
def head_side(f, b, eyes='open'):
    f.paint('hairback', f.ell((9, 3 + b, 15, 12 + b), (10, 9 + b, 14, 18), (11, 14, 14, 19)), HAIR)
    f.paint('crown', f.ell((4, 0 + b, 15, 11 + b)), HAIR)
    f.paint('face', f.ell((3, 4 + b, 11, 12 + b)), SKIN)
    f.paint('bangs', f.ell((3, 2 + b, 6, 5 + b), (6, 2 + b, 9, 6 + b)), HAIR, inner=False)
    f.paint('lock', f.ell((9, 2 + b, 14, 11 + b)), HAIR, inner=False)
    for (x, y) in [(6, 2), (7, 2), (8, 1)]: f.px(x, y + b, HAIR[2])
    if eyes == 'open':
        f.px(5, 7 + b, 'K'); f.px(5, 8 + b, 'K')
    else:
        f.px(5, 8 + b, 'K'); f.px(4, 7 + b, 'K')
    f.px(2, 8 + b, SKIN[1])   # tip of the nose


def body_side(f, b, na, fa, nh=False, fh=False):
    def leg(name, ankle, r, heel_up):
        ax, ay = ankle
        f.paint(name, f.ell((ax - 2, ay - 3, ax + 1, ay + 1) if not heel_up else (ax - 1, ay - 3, ax + 1, ay)), r)
    dark = lambda r: [r[0], r[0], r[1]]
    leg('fleg', fa, dark(BOOT), fh)
    leg('nleg', na, BOOT, nh)
    f.paint('tunic', f.ell((5, 11 + b, 12, 18 + b), (4, 14 + b, 13, 21 + b)), TUNIC)
    for x in range(5, 13): f.px(x, 16 + b, BOOT[0])
    f.px(5, 16 + b, GOLD[1])
    f.paint('scarf', f.ell((5, 11 + b, 9, 13 + b)), SCARF)


def side(b, na, fa, nh, fh, hand):
    f = Frame()
    body_side(f, b, na, fa, nh, fh)
    hx, hy = hand
    f.paint('narm', f.thick([(9, 13 + b), (hx, hy + b)], 2), TUNIC)
    f.flute((hx + 1, hy + b + 1), (hx + 3, hy + b + 6))
    f.paint('nhand', f.ell((hx - 1, hy + b - 1, hx + 1, hy + b + 1)), SKIN)
    head_side(f, b)
    return f


def play_side(stage, b=0):
    """Facing left: the flute points forward from her lips, both hands under it."""
    f = Frame()
    body_side(f, b, (8, 24), (9, 24))
    if stage == 0:
        f.paint('narm', f.thick([(9, 13 + b), (5, 15 + b)], 2), TUNIC)
        head_side(f, b)
        f.flute((-2, 14 + b), (6, 12 + b))
        f.paint('nhand', f.ell((4, 13 + b, 6, 15 + b)), SKIN)
        return f
    f.paint('narm', f.thick([(9, 13 + b), (4, 11 + b)], 2), TUNIC)
    head_side(f, b, 'closed')
    f.flute((-2, 10 + b), (5, 10 + b))
    f.paint('nhand', f.ell((-1, 10 + b, 1, 12 + b)), SKIN); f.paint('nhand2', f.ell((3, 10 + b, 5, 12 + b)), SKIN)
    return f


frames, tags = [], []


def add(tag, fs, dur):
    start = len(frames) + 1
    for i, fr in enumerate(fs):
        frames.append({'rows': fr.rows() if isinstance(fr, Frame) else fr, 'duration': dur[i] if isinstance(dur, list) else dur})
    tags.append((tag, start, len(frames)))


mirror = lambda fs: [[r[::-1] for r in fr.rows()] for fr in fs]
add('idle_down', [front(), front(b=1), front(), front(blink=True)], [0.6, 0.6, 0.5, 0.12])
add('walk_down', [front(lift=(0, 1), swing=(-1, 1)), front(b=-1), front(lift=(1, 0), swing=(1, -1)), front(b=-1)], 0.15)
add('walk_up', [front(lift=(0, 1), swing=(1, -1), back=True), front(b=-1, back=True),
                front(lift=(1, 0), swing=(-1, 1), back=True), front(b=-1, back=True)], 0.15)
left = [side(0, (5, 24), (12, 23), False, True, (12, 16)), side(-1, (8, 24), (9, 23), False, False, (9, 17)),
        side(0, (12, 23), (5, 24), True, False, (6, 16)), side(-1, (9, 23), (8, 24), False, False, (9, 17))]
add('walk_left', left, 0.15)
add('walk_right', mirror(left), 0.15)
PLAY = [0.06, 0.15, 0.15]
add('play_down', [play_front(0), play_front(1), play_front(1, b=-1)], PLAY)
add('play_up', [play_back(0), play_back(1), play_back(1, b=-1)], PLAY)
pl = [play_side(0), play_side(1), play_side(1, b=-1)]
add('play_left', pl, PLAY)
add('play_right', mirror(pl), PLAY)

out = sys.argv[1] if len(sys.argv) > 1 else '.'
json.dump({'palette': PAL, 'frames': frames}, open(f'{out}/anim.json', 'w'))
json.dump(tags, open(f'{out}/tags.json', 'w'))
sheet = Image.new('RGBA', (W * len(frames), H), (88, 168, 72, 255))
for i, fr in enumerate(frames):
    for y, r in enumerate(fr['rows']):
        for x, c in enumerate(r):
            if c != '-': h = PAL[c]; sheet.putpixel((i * W + x, y), tuple(int(h[k:k + 2], 16) for k in (1, 3, 5)) + (255,))
sheet.save(f'{out}/anim_sheet.png')
print(len(frames), 'frames', tags)
