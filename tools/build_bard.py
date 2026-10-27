"""Rebuilds everything for the bard from tools/bard_frames.py, without the Aseprite bridge:
art/bard/bard_animations.aseprite (Shadow + Bard layers, frame durations, one tag per
animation), the sheet art/bard/bard_sheet.png/.json, art/bard/bard_frames.tres and the
preview GIFs in art/bard/bard_previews/.
Run from the project root:  python3 tools/build_bard.py   (set ASEPRITE to the aseprite binary)
"""
import json
import os
import subprocess
import sys
import tempfile
from PIL import Image, ImageDraw

ASEPRITE = os.environ.get('ASEPRITE', os.path.expanduser('~/.local/share/Steam/steamapps/common/Aseprite/aseprite'))
root = os.getcwd()
tmp = tempfile.mkdtemp(prefix='bard_')
subprocess.run([sys.executable, 'tools/bard_frames.py', tmp], check=True)
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
    im.save(f'{tmp}/bard_{i + 1:02d}.png')
# soft shadow under her feet (the figure's feet end 2 px above the frame bottom)
sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
ImageDraw.Draw(sh).ellipse((W // 2 - 5, H - 4, W // 2 + 4, H - 1), fill=(0, 0, 0, 64))
sh.save(f'{tmp}/shadow.png')

lua = f'''
local spr = Sprite({W}, {H})
local shadow = spr.layers[1]; shadow.name = "Shadow"
local bard = spr:newLayer(); bard.name = "Bard"
local shadowImg = Image{{ fromFile = "{tmp}/shadow.png" }}
local durs = {{ {", ".join(str(f["duration"]) for f in anim["frames"])} }}
for i = 1, #durs do
  if i > 1 then spr:newEmptyFrame() end
  spr.frames[i].duration = durs[i]
  spr:newCel(shadow, i, shadowImg, Point(0, 0))
  spr:newCel(bard, i, Image{{ fromFile = string.format("{tmp}/bard_%02d.png", i) }}, Point(0, 0))
end
for _, t in ipairs({{ {", ".join('{"%s",%d,%d}' % (n, a, b) for n, a, b in tags)} }}) do
  local tag = spr:newTag(t[2], t[3]); tag.name = t[1]
end
spr:saveAs("{root}/art/bard/bard_animations.aseprite")
'''
open(f'{tmp}/build.lua', 'w').write(lua)
subprocess.run([ASEPRITE, '-b', '--script', f'{tmp}/build.lua'], check=True)
cols = max(b - a + 1 for _, a, b in tags)
subprocess.run([ASEPRITE, '-b', 'art/bard/bard_animations.aseprite', '--list-tags', '--sheet', 'art/bard/bard_sheet.png',
                '--sheet-type', 'rows', '--sheet-columns', str(cols), '--data', 'art/bard/bard_sheet.json',
                '--format', 'json-array'], check=True, stdout=subprocess.DEVNULL)
subprocess.run([sys.executable, 'tools/make_spriteframes.py'], check=True)

os.makedirs('art/bard/bard_previews', exist_ok=True)
for f in os.listdir('art/bard/bard_previews'):
    if f.endswith('.gif'): os.remove(f'art/bard/bard_previews/{f}')
sheet = json.load(open('art/bard/bard_sheet.json')); img = Image.open('art/bard/bard_sheet.png').convert('RGBA')
for t in sheet['meta']['frameTags']:
    frames, durs = [], []
    for i in range(t['from'], t['to'] + 1):
        fr = sheet['frames'][i]; r = fr['frame']
        bg = Image.new('RGBA', (r['w'], r['h']), (88, 168, 72, 255))
        bg.alpha_composite(img.crop((r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h'])))
        frames.append(bg.convert('RGB').resize((r['w'] * 6, r['h'] * 6), Image.NEAREST)); durs.append(fr['duration'])
    frames[0].save(f"art/bard/bard_previews/{t['name']}.gif", save_all=True, append_images=frames[1:], duration=durs, loop=0)
print(f'bard rebuilt: {len(anim["frames"])} frames of {W}x{H}, tags:', ', '.join(n for n, _, _ in tags))
