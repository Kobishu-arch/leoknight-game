"""Builds art/bard/bard_frames.tres (Godot SpriteFrames) from the Aseprite sheet export.

Export the sheet first (from the project root):
  aseprite -b art/bard/bard_animations.aseprite --list-tags --sheet art/bard/bard_sheet.png \
      --sheet-type rows --sheet-columns 4 --data art/bard/bard_sheet.json --format json-array
then run:  python3 tools/make_spriteframes.py
Each Aseprite tag becomes one looping animation; frame durations are kept.
"""
import json

FPS = 10  # animation speed; each frame's duration is a multiple of 1/FPS seconds
sheet = json.load(open('art/bard/bard_sheet.json'))
frames = sheet['frames']
subs, anims = [], []
for tag in sheet['meta']['frameTags']:
    entries = []
    for i in range(tag['from'], tag['to'] + 1):
        r = frames[i]['frame']
        sid = f'frame_{i}'
        subs.append(f'[sub_resource type="AtlasTexture" id="{sid}"]\natlas = ExtResource("sheet")\n'
                    f'region = Rect2({r["x"]}, {r["y"]}, {r["w"]}, {r["h"]})\n')
        entries.append(f'{{"duration": {frames[i]["duration"] / 1000 * FPS:g}, "texture": SubResource("{sid}")}}')
    anims.append('{\n"frames": [' + ', '.join(entries) + f'],\n"loop": true,\n"name": &"{tag["name"]}",\n"speed": {FPS}.0\n}}')
out = (f'[gd_resource type="SpriteFrames" load_steps={len(subs) + 2} format=3]\n\n'
       '[ext_resource type="Texture2D" path="res://art/bard/bard_sheet.png" id="sheet"]\n\n'
       + '\n'.join(subs) + '\n[resource]\nanimations = [' + ', '.join(anims) + ']\n')
open('art/bard/bard_frames.tres', 'w').write(out)
print(f'{len(anims)} animations, {len(subs)} frames')
