# Leoknight

A Zelda-like adventure through Forchach (Lech valley, Tyrol), starring a bard who
fights with her transverse flute. Made with Godot 4.7, in the style of *A Link to the Past*:
16×16 tiles, a Link-sized hero, soft round shapes.

This is an early prototype: a small test map, the bard walking around in it and playing her flute.

## Run it

Open the folder in Godot 4.7 and press **F5**, or from the terminal:

```bash
godot4 --path .
```

| Key | Action |
|---|---|
| W A S D / arrow keys | walk |
| Space | play the flute: a glowing note flies out in the direction she faces |

The game renders at 320×180 and scales up 4× (1280×720 window).

## What is here

| Path | What |
|---|---|
| `scenes/main.tscn` | the test map; `scripts/world.gd` builds it from `maps/forchach_test.txt` |
| `scenes/player.tscn`, `scripts/player.gd` | the bard: movement, facing, animations, flute attack, ground / raised-meadow level |
| `scenes/note.tscn`, `scripts/note.gd` | the flute's glowing note: halo, sparkle trail, wobble; fades out or bursts (`note_burst.tscn`) on what it hits |
| `scenes/sound_wave.tscn`, `scripts/sound_wave.gd` | the golden sound wave that sweeps out of the flute |
| `scripts/canopy.gd` | makes treetops see-through while the bard is behind them |
| `shaders/grade.gdshader` | colour grade over the whole picture: warm light, cool shadows, soft vignette |
| `art/bard/bard_animations.aseprite` | bard sprite (24×28): `idle_down`, `walk_*` and `play_*` for down, up, left, right |
| `art/fx/` | notes (12×12), their halo, the sparkle and the sound wave |
| `art/bard/bard_sheet.png` + `.json` | sheet exported from Aseprite; `bard_frames.tres` is built from it |
| `art/tiles/terrain.png` | 16×16 tileset: grass, flowers, gravel, path, water, cliff wall and top, bridge, stairs |
| `art/props/` | clover bush, stone, stump, fence (4 variants), round tree, spruce |
| `art/bard/earlier/` | earlier sprite versions (not imported by Godot) |
| `tools/` | scripts that generate the bard frames, the tileset and props, the map and the SpriteFrames |
| `tests/` | headless movement test, a motion check and a screenshot helper |

## The map

`maps/forchach_test.txt` holds two grids of the same size, separated by an empty line:

- **terrain:** `.` grass, `*` flowers, `=` path, `:` gravel, `~` water, `H` bridge, `^` raised meadow, `S` stairs
- **objects:** `.` none, `T` spruce, `o` leafy tree, `b` bush, `r` stone, `u` stump, `f` fence, `@` player start

Gravel, path, water and cliffs are drawn on half-tile-shifted layers, so their borders are round
(see `tools/gen_map_art.py`). The last two rows of a raised meadow show as a cliff wall; stairs
(`S`) in the wall lead up. Edit the file directly, or change and rerun `python3 tools/gen_test_map.py`.

## Changing the art

- **Bard sprite:** the frames come from `tools/bard_frames.py`; `python3 tools/build_bard.py` rebuilds the
  `.aseprite` file, the sheet, Godot's SpriteFrames and the preview GIFs from it. For a hand fix,
  edit `art/bard/bard_animations.aseprite` instead, then export the sheet and rebuild the frames:

  ```bash
  aseprite -b art/bard/bard_animations.aseprite --list-tags --sheet art/bard/bard_sheet.png --sheet-type rows --sheet-columns 4 --data art/bard/bard_sheet.json --format json-array
  python3 tools/make_spriteframes.py
  ```

- **Flute effects** (notes, halo, sparkle, sound wave): `python3 tools/gen_fx.py`.

- **Tiles and props:** `python3 tools/gen_map_art.py` (needs Pillow), then let Godot re-import
  (`godot4 --headless --path . --import`, or just open the editor). The PNGs can also be edited in
  Aseprite directly, but rerunning the script overwrites them.
- **Look at a spot of the map:** `godot4 --path . -s tests/shot.gd --write-movie /tmp/shot.png --fixed-fps 60 -- 57 20`
  writes frames of the view around map cell (57, 20); the last one shows it. Add `down`, `up`,
  `left` or `right` after the numbers to see her play the flute that way.

## Test

```bash
godot4 --headless --path . -s tests/test_movement.gd
```

To check that movement is smooth on your monitor (opens a window, prints how far the bard
and the view move per frame; even steps mean smooth motion):

```bash
godot4 --path . -s tests/diag_motion.gd
```
