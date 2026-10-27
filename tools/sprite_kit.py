"""Shared drawing helpers for the generated character sprites (see bard_frames.py, warrior_frames.py).

A Kit holds the frame size, where the figure sits in it and the palette. Figures are drawn in
design coordinates for a 20 px wide figure; the kit moves them DX/DY px into the frame. Each
colour ramp has a dark outline key, used for the outline pixels around that colour.
"""
from PIL import Image, ImageDraw


class Kit:
    def __init__(self, w, h, dx, dy):
        self.W, self.H, self.DX, self.DY = w, h, dx, dy
        self.PAL = {'-': '#00000000'}
        self.OUTLINE_OF = {}
        self.default_outline = None

    def ramp(self, keys, cols, outline):
        for k, c in zip(keys, cols):
            self.PAL[k] = c
            self.OUTLINE_OF[k] = outline[0]
        self.PAL[outline[0]] = outline[1]
        self.default_outline = self.default_outline or outline[0]
        return list(keys)

    def color(self, key, col, outline_key):
        self.PAL[key] = col
        self.OUTLINE_OF[key] = outline_key

    def frame(self):
        return Frame(self)

    def write(self, frames, tags, out, bg=(88, 168, 72, 255)):
        """frames: [{'rows', 'duration'}]; writes anim.json, tags.json and a preview strip."""
        import json
        json.dump({'palette': self.PAL, 'frames': frames}, open(f'{out}/anim.json', 'w'))
        json.dump(tags, open(f'{out}/tags.json', 'w'))
        sheet = Image.new('RGBA', (self.W * len(frames), self.H), bg)
        for i, fr in enumerate(frames):
            for y, r in enumerate(fr['rows']):
                for x, c in enumerate(r):
                    if c != '-':
                        h = self.PAL[c]
                        sheet.putpixel((i * self.W + x, y), tuple(int(h[k:k + 2], 16) for k in (1, 3, 5)) + (255,))
        sheet.save(f'{out}/anim_sheet.png')


class _Shifted:
    def __init__(self, d, dx, dy): self.d, self.dx, self.dy = d, dx, dy
    def ellipse(self, b, **kw): self.d.ellipse((b[0] + self.dx, b[1] + self.dy, b[2] + self.dx, b[3] + self.dy), **kw)
    def line(self, p, **kw): self.d.line([(x + self.dx, y + self.dy) for x, y in p], **kw)
    def polygon(self, p, **kw): self.d.polygon([(x + self.dx, y + self.dy) for x, y in p], **kw)


class Frame:
    def __init__(f, kit):
        f.k = kit
        f.c = [[None] * kit.W for _ in range(kit.H)]
        f.o = [[None] * kit.W for _ in range(kit.H)]

    def mask(f, fn):
        k = f.k
        m = Image.new('1', (k.W, k.H), 0); fn(_Shifted(ImageDraw.Draw(m), k.DX, k.DY))
        return {(x, y) for y in range(k.H) for x in range(k.W) if m.getpixel((x, y))}

    def ell(f, *boxes, mirror=False):
        s = f.mask(lambda d: [d.ellipse(b, fill=1) for b in boxes])
        axis2 = 2 * f.k.DX + 19   # mirror about the figure's centre (design x 9.5)
        return s | {(axis2 - x, y) for (x, y) in s} if mirror else s

    def poly(f, pts):
        return f.mask(lambda d: d.polygon(pts, fill=1))

    def thick(f, pts, w=1): return f.mask(lambda d: d.line(pts, fill=1, width=w))

    def paint(f, name, pts, r, inner=True):
        """Three tones: light on the top-left edge, dark on the bottom-right edge."""
        W, H = f.k.W, f.k.H
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
        x += f.k.DX; y += f.k.DY
        if 0 <= x < f.k.W and 0 <= y < f.k.H: f.c[y][x] = c

    def rod(f, a, b, r):
        """A thin rod (flute, spear shaft) from a to b: light top, dark underside, dark middle mark."""
        f.flat('rod', f.thick([a, b], 1), r[1])
        (x0, y0), (x1, y1) = a, b
        if abs(x1 - x0) >= abs(y1 - y0):   # horizontal-ish: second row underneath
            f.flat('rod2', f.thick([(x0, y0 + 1), (x1, y1 + 1)], 1), r[0])
            f.px(min(x0, x1) + abs(x1 - x0) // 2, y0, r[0])
            f.px(min(x0, x1) + 1, y0, r[2])
        else:
            f.px(x0, y0, r[2])

    def rows(f):
        k = f.k
        out = [r[:] for r in f.c]
        for y in range(k.H):
            for x in range(k.W):
                if f.c[y][x] is not None: continue
                for dx, dy in ((0, 1), (1, 0), (-1, 0), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < k.W and 0 <= ny < k.H and f.c[ny][nx] is not None:
                        out[y][x] = k.OUTLINE_OF.get(f.c[ny][nx], k.default_outline); break
        return [''.join(c or '-' for c in r) for r in out]


def animations():
    """Collects frames and tags: add(tag, frames, durations); mirror(frames) flips left to right."""
    frames, tags = [], []

    def add(tag, fs, dur):
        start = len(frames) + 1
        for i, fr in enumerate(fs):
            frames.append({'rows': fr.rows() if isinstance(fr, Frame) else fr,
                           'duration': dur[i] if isinstance(dur, list) else dur})
        tags.append((tag, start, len(frames)))

    mirror = lambda fs: [[r[::-1] for r in fr.rows()] for fr in fs]
    return frames, tags, add, mirror
