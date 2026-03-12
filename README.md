# 🎹 Heartopia Piano Macro

Automatically play any MIDI song on the Heartopia in-game piano. No AutoHotkey needed — uses DirectX-level keystrokes that work reliably with the game.

---

## Requirements

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

Install dependencies:

```bash
pip install mido pydirectinput
```

---

## Usage

### Play immediately
```bash
python midi_to_heartopia.py input.mid --play
```
You have **5 seconds** to switch into the Heartopia game window before playback starts.

### Convert only (saves a reusable playback script)
```bash
python midi_to_heartopia.py input.mid
# Generates: input_heartopia.py
```

Then play it later anytime:
```bash
python input_heartopia.py
```

### Adjust speed
```bash
# Slower (80% speed)
python midi_to_heartopia.py input.mid --play --bpm-scale 0.8

# Faster (120% speed)
python midi_to_heartopia.py input.mid --play --bpm-scale 1.2
```

### Custom output filename
```bash
python midi_to_heartopia.py input.mid mysong.py --play
```

---

## Keyboard Mapping

The script maps MIDI notes to Heartopia's 3-row piano layout:

```
Row 1 (C5–C6)  White: Q  W  E  R  T  Y  U  I
               Black: 2  3     5  6  7

Row 2 (C4–B4)  White: Z  X  C  V  B  N  M
               Black: S  D     G  H  J

Row 3 (C3–B3)  White: ,  .  /  O  P  [  ]
               Black: L  ;     0  -  =
```

| Note | C3 | C4 | C5 |
|------|----|----|-----|
| C    | ,  | Z  | Q  |
| C#   | L  | S  | 2  |
| D    | .  | X  | W  |
| D#   | ;  | D  | 3  |
| E    | /  | C  | E  |
| F    | O  | V  | R  |
| F#   | 0  | G  | 5  |
| G    | P  | B  | T  |
| G#   | -  | H  | 6  |
| A    | [  | N  | Y  |
| A#   | =  | J  | 7  |
| B    | ]  | M  | U  |
| C6   | —  | —  | I  |

Notes outside the C3–C6 range are automatically transposed into the nearest available octave.

---

## How It Works

1. Parses the `.mid` file using `mido`, merging all tracks into a single timeline
2. Handles tempo change events for accurate timing
3. Maps each MIDI note to its corresponding Heartopia keyboard key
4. Uses `pydirectinput` to send DirectX scan codes — the same low-level input method as a real physical keyboard, which games cannot filter out

---

## Tips

- **Wrong octave?** Open the MIDI in a browser editor like [Signal](https://signal.vercel.app) or [Flat.io](https://flat.io) and shift notes into the C3–C6 range
- **Song too fast?** Use `--bpm-scale 0.8` to slow it down
- **Where to find MIDIs?** [MuseScore.com](https://musescore.com) has thousands of free piano arrangements ready to download
- **Make sure the game window is focused** when playback starts — if another window is active, keystrokes will go there instead

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Nothing plays | Make sure Heartopia is the active window during the countdown |
| Some notes missing | Check that your MIDI has notes in the C3–C6 range |
| Playback is off-tempo | Try adjusting `--bpm-scale` |
| `pydirectinput` error | Run `pip install pydirectinput` |
| `mido` not found | Run `pip install mido` |
