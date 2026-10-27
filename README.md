# Leoknight

A Zelda-like adventure through Forchach (Lech valley, Tyrol), starring a bard who
fights with her transverse flute. Made with Godot 4.7.

This is an early prototype: a small test map and the bard walking around in it.

## Run it

Open the folder in Godot 4.7 and press **F5**, or from the terminal:

```bash
godot4 --path .
```

| Key | Action |
|---|---|
| W A S D / arrow keys | walk |

## What is here

| Path | What |
|---|---|
| `scenes/main.tscn` | the test map; `scripts/world.gd` builds it from `maps/forchach_test.txt` |
| `scenes/player.tscn`, `scripts/player.gd` | the bard: movement, facing, animations |
| `art/bard/bard_animations.aseprite` | bard sprite (48×64): `idle_down`, `walk_down`, `walk_up`, `walk_left`, `walk_right` |
| `art/bard/bard_sheet.png` + `.json` | sheet exported from Aseprite; `bard_frames.tres` is built from it |
| `art/tiles/terrain.png`, `art/props/` | 32×32 ground tiles, spruce and rock |
| `art/bard/earlier/` | earlier sprite versions (not imported by Godot) |
| `tools/` | scripts that generate the map art, the map layout and the SpriteFrames |
| `tests/test_movement.gd` | headless test of movement, animations and collisions |

## Changing things

- **Map layout:** edit `maps/forchach_test.txt` (legend in `tools/gen_test_map.py`), or change and rerun
  `python3 tools/gen_test_map.py`.
- **Bard sprite:** edit `art/bard/bard_animations.aseprite`, export the sheet and rebuild the frames:

  ```bash
  aseprite -b art/bard/bard_animations.aseprite --list-tags --sheet art/bard/bard_sheet.png --sheet-type rows --sheet-columns 4 --data art/bard/bard_sheet.json --format json-array
  python3 tools/make_spriteframes.py
  ```

- **Tiles and props:** `python3 tools/gen_map_art.py` (needs Pillow).

## Test

```bash
godot4 --headless --path . -s tests/test_movement.gd
```
