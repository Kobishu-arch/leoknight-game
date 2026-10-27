"""Generates the warrior enemy's frames (32x36): feather headdress, black braids, red face
paint, bead necklace, leaf skirt and a stone-tipped spear. Simple, like the bard.
Animations: idle_down (2 frames); walk_down / walk_up / walk_left (4 frames); attack_down /
attack_up / attack_left (3 frames: wind up, thrust, recover); *_right = *_left mirrored.
Run:  python3 tools/warrior_frames.py <out-dir>   (tools/build_sprite.py warrior builds it all)
"""
import sys
from sprite_kit import Kit, animations

# Drawing coordinates are for a 20x26 figure; it lands 6 px right/down in the 32x36 frame,
# which leaves room for the feathers above the head and the spear thrust on every side.
kit = Kit(32, 36, 6, 6)
SKIN = kit.ramp('abc', ['#7a3e24', '#a8603a', '#cc8452'], ('"', '#3a1a10'))
HAIR = kit.ramp('123', ['#141018', '#26202c', '#3e3444'], ('!', '#08060a'))
FEATHER = kit.ramp('wxy', ['#b0a89c', '#ece6da', '#ffffff'], ('(', '#4a4238'))
BAND = kit.ramp('nop', ['#7a1a1a', '#b83030', '#e05a4a'], ('%', '#300808'))
LEAF = kit.ramp('efg', ['#2c4a1c', '#46702c', '#6a9a3c'], ('#', '#14240c'))
WOOD = kit.ramp('ABC', ['#5a3418', '#8a5a2a', '#b88444'], ("'", '#26140a'))
STONE = kit.ramp('EFG', ['#606878', '#a0a8b8', '#d8e0e8'], (')', '#262a34'))
kit.color('K', '#0e0a0e', '"')
kit.color('R', '#e03a3a', '%')     # face paint, feather tips
kit.color('T', '#3aa0a0', '"')     # teal beads
kit.color('U', '#f0e6c8', '"')     # bone beads
Frame = kit.frame


def spear(f, a, b):
    """Shaft from a (back end) to b (tip end), with a little stone point beyond b."""
    f.rod(a, b, WOOD)
    (x0, y0), (x1, y1) = a, b
    dx, dy = (x1 > x0) - (x1 < x0), (y1 > y0) - (y1 < y0)
    if abs(x1 - x0) >= abs(y1 - y0):   # pointing sideways
        f.paint('tip', f.poly([(x1, y1 - 1), (x1 + 3 * dx, y1), (x1 + 3 * dx, y1 + 1), (x1, y1 + 2)]) | f.thick([(x1, y1), (x1 + 2 * dx, y1)], 2), STONE)
    else:                              # pointing up or down
        f.paint('tip', f.poly([(x1 - 1, y1), (x1, y1 + 3 * dy), (x1 + 1, y1 + 3 * dy), (x1 + 2, y1)]) | f.thick([(x1, y1), (x1, y1 + 2 * dy)], 2), STONE)


def feathers(f, b, tips, base=(9.5, 4)):
    for (tx, ty) in tips:
        f.paint('feather', f.thick([(base[0], base[1] + b), (tx, ty + b)], 2), FEATHER, inner=False)
        f.px(round(tx), ty + b, 'R'); f.px(round(tx + (1 if tx > base[0] else 0)), ty + b, 'R')


def skirt(f, pts):
    f.paint('skirt', pts, LEAF)
    bottom = max(y for _, y in pts)
    for (x, y) in pts:   # leaf points along the hem
        if y == bottom and x % 2: f.c[y][x] = None
        elif (x, y + 1) not in pts and x % 3 == 0: f.c[y][x] = LEAF[2]


def face_front(f, b):
    f.paint('face', f.ell((5, 4 + b, 14, 12 + b)), SKIN)
    f.paint('band', f.ell((4, 4 + b, 15, 6 + b)), BAND, inner=False)
    for x in (7, 12): f.px(x, 7 + b, 'K'); f.px(x, 8 + b, 'K')
    for x in (6, 7, 8, 11, 12, 13): f.px(x, 9 + b, 'R')   # war paint under the eyes


def body_front(f, b, lift=(0, 0), back=False):
    for side in (-1, 1):   # bare legs with moccasins
        d = -(lift[0] if side < 0 else lift[1])
        xs = (6, 8) if side < 0 else (11, 13)
        f.paint('leg%d' % side, f.ell((xs[0], 18 + d, xs[1], 23 + d)), SKIN)
        f.paint('moc%d' % side, f.ell((xs[0], 21 + d, xs[1], 23 + d)), WOOD)
    f.paint('chest', f.ell((6, 11 + b, 13, 18 + b)), SKIN)
    if not back:
        for i, x in enumerate(range(7, 13)): f.px(x, 12 + b + (1 if x in (8, 11) else 0) + (1 if x in (9, 10) else 0), 'T' if i % 2 else 'U')
    skirt(f, f.ell((5, 15 + b, 14, 21 + b)))


def front(b=0, lift=(0, 0), swing=(0, 0), back=False):
    f = Frame()
    feathers(f, b, [(2, 1), (5, -3), (9.5, -5), (14, -3), (17, 1)])
    f.paint('braids', f.ell((3, 6 + b, 5, 16 + b), mirror=True), HAIR)
    body_front(f, b, lift, back)
    for side in (-1, 1):
        sw = swing[0] if side < 0 else swing[1]
        xs = (4, 6) if side < 0 else (13, 15)
        f.paint('arm%d' % side, f.ell((xs[0], 12 + b, xs[1], 17 + b + sw)), SKIN)
    f.paint('crown', f.ell((4, 1 + b, 15, 11 + b)), HAIR)
    if back:
        f.paint('hairback', f.ell((5, 4 + b, 14, 14 + b)), HAIR, inner=False)
        f.paint('band', f.ell((4, 4 + b, 15, 6 + b)), BAND, inner=False)
        spear(f, (5, 22 + b + swing[0]), (5, -2 + b + swing[0]))
    else:
        face_front(f, b)
        spear(f, (14, 22 + b + swing[1]), (14, -2 + b + swing[1]))
    return f


def attack_front(stage, back=False):
    """Facing down (or up from behind): a straight poke with both hands on the shaft."""
    f = Frame()
    feathers(f, 0, [(2, 1), (5, -3), (9.5, -5), (14, -3), (17, 1)])
    f.paint('braids', f.ell((3, 6, 5, 16), mirror=True), HAIR)
    body_front(f, 0, back=back)
    reach = [0, 5, 2][stage]
    f.paint('crown', f.ell((4, 1, 15, 11)), HAIR)
    if back:  # from behind: thrust upwards on her right side
        f.paint('hairback', f.ell((5, 4, 14, 14)), HAIR, inner=False)
        f.paint('band', f.ell((4, 4, 15, 6)), BAND, inner=False)
        f.paint('arm', f.ell((13, 11 - reach // 2, 16, 15)), SKIN)
        spear(f, (15, 22 - reach), (15, 2 - reach))
        f.paint('hand', f.ell((14, 12 - reach // 2, 16, 14 - reach // 2)), SKIN)
        return f
    face_front(f, 0)   # facing down: from the chest towards the viewer
    f.paint('arms', f.ell((6, 12, 13, 16 + reach // 2)), SKIN)
    spear(f, (10, 12 + reach), (10, 23 + reach))
    f.paint('hands', f.ell((9, 14 + reach // 2, 11, 16 + reach // 2)), SKIN)
    return f


# ---------------------------------------------------------------- side (facing left)
def head_side(f, b):
    feathers(f, b, [(12, -3), (15, -2), (17, 1)], base=(11, 4))
    f.paint('hairback', f.ell((9, 3 + b, 15, 13 + b), (11, 10 + b, 13, 17 + b)), HAIR)
    f.paint('crown', f.ell((4, 1 + b, 15, 11 + b)), HAIR)
    f.paint('face', f.ell((3, 4 + b, 11, 12 + b)), SKIN)
    f.paint('lock', f.ell((9, 3 + b, 14, 11 + b)), HAIR, inner=False)
    f.paint('band', f.ell((3, 4 + b, 14, 6 + b)), BAND, inner=False)
    f.px(5, 7 + b, 'K'); f.px(5, 8 + b, 'K')
    for x in (4, 5, 6): f.px(x, 9 + b, 'R')
    f.px(2, 8 + b, SKIN[1])


def body_side(f, b, na, fa, nh=False, fh=False):
    def leg(name, ankle, r, heel_up):
        ax, ay = ankle
        f.paint(name, f.ell((ax - 2, ay - 4, ax + 1, ay + 1) if not heel_up else (ax - 1, ay - 4, ax + 1, ay)), r)
        f.paint(name + 'm', f.ell((ax - 2, ay - 1, ax + 1, ay + 1) if not heel_up else (ax - 1, ay - 2, ax + 1, ay)), [WOOD[0], WOOD[0], WOOD[1]] if r[0] == SKIN[0] and r is not SKIN else WOOD)
    dark = lambda r: [r[0], r[0], r[1]]
    leg('fleg', fa, dark(SKIN), fh)
    leg('nleg', na, SKIN, nh)
    f.paint('chest', f.ell((5, 11 + b, 12, 18 + b)), SKIN)
    for i, x in enumerate(range(5, 9)): f.px(x, 12 + b + (1 if x in (6, 7) else 0), 'T' if i % 2 else 'U')
    skirt(f, f.ell((4, 15 + b, 13, 21 + b)))


def side(b, na, fa, nh, fh, hand):
    f = Frame()
    body_side(f, b, na, fa, nh, fh)
    head_side(f, b)
    hx, hy = hand
    spear(f, (hx + 4, hy + b + 5), (hx - 6, hy + b - 9))
    f.paint('narm', f.thick([(9, 13 + b), (hx, hy + b)], 2), SKIN)
    return f


def attack_side(stage):
    f = Frame()
    body_side(f, 0, (6, 24), (11, 24))
    head_side(f, 0)
    reach = [-3, 4, 1][stage]
    spear(f, (14 - reach, 14), (1 - reach, 14))
    f.paint('narm', f.thick([(9, 13), (6 - reach // 2, 14)], 2), SKIN)
    f.paint('hand', f.ell((5 - reach // 2, 13, 7 - reach // 2, 15)), SKIN)
    return f


frames, tags, add, mirror = animations()
add('idle_down', [front(), front(b=1)], 0.5)
add('walk_down', [front(lift=(0, 1), swing=(-1, 1)), front(b=-1), front(lift=(1, 0), swing=(1, -1)), front(b=-1)], 0.13)
add('walk_up', [front(lift=(0, 1), swing=(1, -1), back=True), front(b=-1, back=True),
                front(lift=(1, 0), swing=(-1, 1), back=True), front(b=-1, back=True)], 0.13)
left = [side(0, (5, 24), (12, 23), False, True, (12, 16)), side(-1, (8, 24), (9, 23), False, False, (9, 17)),
        side(0, (12, 23), (5, 24), True, False, (6, 16)), side(-1, (9, 23), (8, 24), False, False, (9, 17))]
add('walk_left', left, 0.13)
add('walk_right', mirror(left), 0.13)
POKE = [0.22, 0.12, 0.16]
add('attack_down', [attack_front(i) for i in range(3)], POKE)
add('attack_up', [attack_front(i, back=True) for i in range(3)], POKE)
al = [attack_side(i) for i in range(3)]
add('attack_left', al, POKE)
add('attack_right', mirror(al), POKE)

out = sys.argv[1] if len(sys.argv) > 1 else '.'
kit.write(frames, tags, out)
print(len(frames), 'frames', tags)
