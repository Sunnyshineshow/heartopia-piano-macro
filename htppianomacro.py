"""
midi_to_heartopia.py
--------------------
Converts AND plays a .mid (MIDI) file on the Heartopia in-game piano.
No AutoHotkey needed — uses pydirectinput which sends DirectX-level
keystrokes that work with most games.

Usage:
    # Convert only — saves a standalone playback script
    python midi_to_heartopia.py input.mid

    # Convert + play immediately
    python midi_to_heartopia.py input.mid --play

    # Slow down to 80% speed
    python midi_to_heartopia.py input.mid --play --bpm-scale 0.8

Requirements:
    pip install mido pydirectinput

Heartopia key mapping:
  Row 1 (C5-C6): Q W E R T Y U I  | black: 2 3 5 6 7
  Row 2 (C4-B4): Z X C V B N M    | black: S D G H J
  Row 3 (C3-B3): , . / O P [ ]   | black: L ; 0 - =
"""

import sys
import os
import time
import argparse
import mido

# ---------------------------------------------------------------------------
# Key mapping: semitone (0=C..11=B) -> [row3_key, row2_key, row1_key]
# ---------------------------------------------------------------------------
SEMITONE_TO_ROW = {
    #        row0(C3)  row1(C4)  row2(C5)
    0:  [',',    'z',    'q'],   # C
    1:  ['l',    's',    '2'],   # C#
    2:  ['.',    'x',    'w'],   # D
    3:  [';',    'd',    '3'],   # D#
    4:  ['/',    'c',    'e'],   # E
    5:  ['o',    'v',    'r'],   # F
    6:  ['0',    'g',    '5'],   # F#
    7:  ['p',    'b',    't'],   # G
    8:  ['-',    'h',    '6'],   # G#
    9:  ['[',    'n',    'y'],   # A
    10: ['=',    'j',    '7'],   # A#
    11: [']',    'm',    'u'],   # B
}

HIGH_C_KEY = 'i'  # C6 = MIDI 84
# Row index matches SEMITONE_TO_ROW: 0=low(C3), 1=mid(C4), 2=high(C5)
ROW_MIDI_BASE = {0: 48, 1: 60, 2: 72}

# pydirectinput accepts these special keys directly by their character —
# no remapping needed. This map is intentionally empty but kept for clarity.
SPECIAL_KEY_MAP = {}


def midi_note_to_key(midi_note: int):
    """Return the raw key character for a given MIDI note."""
    # Transpose into playable range (C3=48 to C6=84) first
    while midi_note > 84:
        midi_note -= 12
    while midi_note < 48:
        midi_note += 12

    if midi_note == 84:
        return HIGH_C_KEY

    # Try each row in order; if a row owns this note but key is None (no black key
    # on that row), fall back to the same semitone on the next row up
    semitone = midi_note % 12
    for row_idx in [0, 1, 2]:
        base = ROW_MIDI_BASE[row_idx]
        if base <= midi_note <= base + 11:
            key = SEMITONE_TO_ROW[semitone][row_idx]
            if key is not None:
                return key
            # This row has no key for this semitone - try same semitone on rows above
            for fallback_row in [1, 2]:
                fallback_key = SEMITONE_TO_ROW[semitone][fallback_row]
                if fallback_key is not None:
                    return fallback_key

    # Should never reach here
    return 'z'


def to_directinput_key(key: str) -> str:
    """Convert raw character to pydirectinput key name."""
    if key is None:
        return None
    return SPECIAL_KEY_MAP.get(key, key)


def parse_midi(midi_path: str, bpm_scale: float = 1.0):
    """Parse MIDI and return list of (abs_time_seconds, key) tuples."""
    mid = mido.MidiFile(midi_path)
    tempo = 500000
    ticks_per_beat = mid.ticks_per_beat

    events = []
    abs_time = 0.0

    for msg in mido.merge_tracks(mid.tracks):
        abs_time += mido.tick2second(msg.time, ticks_per_beat, tempo)
        if msg.type == 'set_tempo':
            tempo = msg.tempo
        if msg.type == 'note_on' and msg.velocity > 0:
            raw_key = midi_note_to_key(msg.note)
            key = to_directinput_key(raw_key)
            if key:
                events.append((abs_time / bpm_scale, key))

    return events


def play(events: list, countdown: int = 5):
    """Play events using pydirectinput with a countdown."""
    try:
        import pydirectinput
    except ImportError:
        print("pydirectinput not installed. Run:  pip install pydirectinput")
        sys.exit(1)

    pydirectinput.PAUSE = 0  # disable built-in inter-call delay

    print(f"\nStarting in {countdown} seconds — switch to Heartopia now!")
    for i in range(countdown, 0, -1):
        print(f"  {i}...")
        time.sleep(1)
    print("Playing!\n")

    start = time.perf_counter()
    for abs_time, key in events:
        # Busy-wait for precise timing
        while time.perf_counter() - start < abs_time:
            pass
        try:
            pydirectinput.keyDown(key)
            time.sleep(0.03)
            pydirectinput.keyUp(key)
        except Exception as e:
            print(f"  Warning: could not send key '{key}': {e}")

    print("Done!")


def save_playback_script(events: list, out_path: str, bpm_scale: float):
    """Save a standalone Python playback script."""
    lines = [
        '"""',
        'Heartopia piano playback — generated by midi_to_heartopia.py',
        f'BPM scale: {bpm_scale}',
        'Requirements: pip install pydirectinput',
        'Run this script, then switch to Heartopia within 5 seconds.',
        '"""',
        'import time, sys',
        'try:',
        '    import pydirectinput',
        'except ImportError:',
        '    print("Run:  pip install pydirectinput"); sys.exit(1)',
        '',
        'pydirectinput.PAUSE = 0',
        'COUNTDOWN = 5',
        '',
        'print(f"Switch to Heartopia within {COUNTDOWN} seconds!")',
        'for i in range(COUNTDOWN, 0, -1):',
        '    print(f"  {i}..."); time.sleep(1)',
        'print("Playing!")',
        '',
        'events = [',
    ]

    for t, k in events:
        lines.append(f'    ({t:.4f}, {repr(k)}),')

    lines += [
        ']',
        '',
        'start = time.perf_counter()',
        'for abs_time, key in events:',
        '    while time.perf_counter() - start < abs_time:',
        '        pass',
        '    try:',
        '        pydirectinput.keyDown(key)',
        '        time.sleep(0.03)',
        '        pydirectinput.keyUp(key)',
        '    except Exception as e:',
        '        print(f"Warning: key {key!r} failed: {e}")',
        '',
        'print("Done!")',
    ]

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Saved: {out_path}")
    print(f"Notes   : {len(events)}")
    print(f"Duration: {events[-1][0]:.1f}s")
    print(f"\nTo play: python {os.path.basename(out_path)}")


def main():
    parser = argparse.ArgumentParser(
        description='Convert a MIDI file for Heartopia piano (no AHK needed).'
    )
    parser.add_argument('midi', help='Path to input .mid file')
    parser.add_argument('output', nargs='?', help='Output playback .py script (optional)')
    parser.add_argument('--play', action='store_true', help='Play immediately after converting')
    parser.add_argument('--bpm-scale', type=float, default=1.0,
                        help='Speed multiplier (0.8=slower, 1.2=faster). Default: 1.0')
    args = parser.parse_args()

    if not os.path.isfile(args.midi):
        print(f"File not found: {args.midi}")
        sys.exit(1)

    print(f"Parsing {args.midi}...")
    events = parse_midi(args.midi, args.bpm_scale)

    if not events:
        print("No playable notes found in MIDI file.")
        sys.exit(1)

    print(f"Found {len(events)} notes, duration {events[-1][0]:.1f}s")

    out_path = args.output or os.path.splitext(args.midi)[0] + '_heartopia.py'
    save_playback_script(events, out_path, args.bpm_scale)

    if args.play:
        play(events)


if __name__ == '__main__':
    main()