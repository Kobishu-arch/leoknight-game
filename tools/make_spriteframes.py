"""Builds art/<name>/<name>_frames.tres (Godot SpriteFrames) from the Aseprite sheet export.

Export the sheet first (from the project root):
  aseprite -b art/bard/bard_animations.aseprite --list-tags --sheet art/bard/bard_sheet.png \
      --sheet-type rows --sheet-columns 4 --data art/bard/bard_sheet.json --format json-array
then run:  python3 tools/make_spriteframes.py [name]   (default: bard)
Each Aseprite tag becomes one animation (looping, except the attacks play_* and attack_*);
frame durations are kept.
"""
import json
import sys

FPS = 10  # animation speed; each frame's duration is a multiple of 1/FPS seconds
name = sys.argv[1] if len(sys.argv) > 1 else 'bard'
sheet = json.load(open(f'art/{name}/{name}_sheet.json'))
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
    loop = 'false' if tag['name'].startswith(('play', 'attack')) else 'true'   # attacks play once
    anims.append('{\n"frames": [' + ', '.join(entries) + f'],\n"loop": {loop},\n"name": &"{tag["name"]}",\n"speed": {FPS}.0\n}}')
out = (f'[gd_resource type="SpriteFrames" load_steps={len(subs) + 2} format=3]\n\n'
       f'[ext_resource type="Texture2D" path="res://art/{name}/{name}_sheet.png" id="sheet"]\n\n'
       + '\n'.join(subs) + '\n[resource]\nanimations = [' + ', '.join(anims) + ']\n')
open(f'art/{name}/{name}_frames.tres', 'w').write(out)
print(f'{len(anims)} animations, {len(subs)} frames')
