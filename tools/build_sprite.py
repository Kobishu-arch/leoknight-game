"""Rebuilds everything for a character from tools/<name>_frames.py, without the Aseprite bridge:
art/<name>/<name>_animations.aseprite (Shadow + figure layers, frame durations, one tag per
animation), the sheet art/<name>/<name>_sheet.png/.json, art/<name>/<name>_frames.tres and the
preview GIFs in art/<name>/<name>_previews/.
Run from the project root:  python3 tools/build_sprite.py bard   (or warrior; set ASEPRITE to
the aseprite binary if it is not the Steam one)
"""
import json
import os
import subprocess
import sys
import tempfile
from PIL import Image, ImageDraw

ASEPRITE = os.environ.get('ASEPRITE', os.path.expanduser('~/.local/share/Steam/steamapps/common/Aseprite/aseprite'))
root = os.getcwd()
name = sys.argv[1] if len(sys.argv) > 1 else 'bard'
art = f'art/{name}'
os.makedirs(art, exist_ok=True)
tmp = tempfile.mkdtemp(prefix=f'{name}_')
subprocess.run([sys.executable, f'tools/{name}_frames.py', tmp], check=True)
anim = json.load(open(f'{tmp}/anim.json'))
tags = json.load(open(f'{tmp}/tags.json'))
pal = anim['palette']
H = len(anim['frames'][0]['rows']); W = len(anim['frames'][0]['rows'][0])
rgba = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + ((int(h[7:9], 16),) if len(h) > 7 else (255,))

for i, fr in enumerate(anim['frames']):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for y, row in enumerate(fr['rows']):
        for x, c in enumerate(row):
            if c != '-': im.putpixel((x, y), rgba(pal[c]))
    im.save(f'{tmp}/frame_{i + 1:02d}.png')
# soft shadow under the feet: the lowest drawn row of the first frame is the outline below them
feet = max(y for y, row in enumerate(anim['frames'][0]['rows']) if row.strip('-'))
sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
ImageDraw.Draw(sh).ellipse((W // 2 - 5, feet - 2, W // 2 + 4, feet + 1), fill=(0, 0, 0, 64))
sh.save(f'{tmp}/shadow.png')

lua = f'''
local spr = Sprite({W}, {H})
local shadow = spr.layers[1]; shadow.name = "Shadow"
local fig = spr:newLayer(); fig.name = "{name.capitalize()}"
local shadowImg = Image{{ fromFile = "{tmp}/shadow.png" }}
local durs = {{ {", ".join(str(f["duration"]) for f in anim["frames"])} }}
for i = 1, #durs do
  if i > 1 then spr:newEmptyFrame() end
  spr.frames[i].duration = durs[i]
  spr:newCel(shadow, i, shadowImg, Point(0, 0))
  spr:newCel(fig, i, Image{{ fromFile = string.format("{tmp}/frame_%02d.png", i) }}, Point(0, 0))
end
for _, t in ipairs({{ {", ".join('{"%s",%d,%d}' % (n, a, b) for n, a, b in tags)} }}) do
  local tag = spr:newTag(t[2], t[3]); tag.name = t[1]
end
spr:saveAs("{root}/{art}/{name}_animations.aseprite")
'''
open(f'{tmp}/build.lua', 'w').write(lua)
subprocess.run([ASEPRITE, '-b', '--script', f'{tmp}/build.lua'], check=True)
cols = max(b - a + 1 for _, a, b in tags)
subprocess.run([ASEPRITE, '-b', f'{art}/{name}_animations.aseprite', '--list-tags', '--sheet', f'{art}/{name}_sheet.png',
                '--sheet-type', 'rows', '--sheet-columns', str(cols), '--data', f'{art}/{name}_sheet.json',
                '--format', 'json-array'], check=True, stdout=subprocess.DEVNULL)
subprocess.run([sys.executable, 'tools/make_spriteframes.py', name], check=True)

previews = f'{art}/{name}_previews'
os.makedirs(previews, exist_ok=True)
for t in tags:  # replace only this character's animation previews
    if os.path.exists(f'{previews}/{t[0]}.gif'): os.remove(f'{previews}/{t[0]}.gif')
sheet = json.load(open(f'{art}/{name}_sheet.json')); img = Image.open(f'{art}/{name}_sheet.png').convert('RGBA')
for t in sheet['meta']['frameTags']:
    frames, durs = [], []
    for i in range(t['from'], t['to'] + 1):
        fr = sheet['frames'][i]; r = fr['frame']
        bg = Image.new('RGBA', (r['w'], r['h']), (88, 168, 72, 255))
        bg.alpha_composite(img.crop((r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h'])))
        frames.append(bg.convert('RGB').resize((r['w'] * 6, r['h'] * 6), Image.NEAREST)); durs.append(fr['duration'])
    frames[0].save(f"{previews}/{t['name']}.gif", save_all=True, append_images=frames[1:], duration=durs, loop=0)
print(f'{name} rebuilt: {len(anim["frames"])} frames of {W}x{H}, tags:', ', '.join(n for n, _, _ in tags))
