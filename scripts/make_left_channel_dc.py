"""Generate the left-channel-DC test material.

Output: 8 s, 48 kHz, stereo, 32-bit float WAV with the left channel held at a
constant ``1.0`` and the right channel at ``0.0``.  This is the input used to
measure FL Studio's mixer-track pan rule: a DC input makes the pan law act as a
static gain, so the rendered output reads back directly as the gain matrix.

Usage::

    uv run python scripts/make_left_channel_dc.py
    uv run python scripts/make_left_channel_dc.py -o "input-wav-file/Left Channel DC.wav"
"""

from __future__ import annotations

import argparse
import array
import sys
import wave
from pathlib import Path

SAMPLE_RATE = 48000
DURATION_S = 8
LEFT_DC = 1
RIGHT_DC = 0
DEFAULT_OUTPUT = Path("input-wav-file") / "Left Channel DC.wav"

CHANNELS = 2
SAMPLE_WIDTH = 4  # bytes; 32-bit float


def build_frames(
    sample_rate: int = SAMPLE_RATE,
    duration_s: float = DURATION_S,
    left: float = LEFT_DC,
    right: float = RIGHT_DC,
) -> array.array:
    """Return interleaved float32 frames: ``left, right, left, right, ...``."""
    n_frames = round(sample_rate * duration_s)
    frames = array.array("f", [left, right]) * n_frames
    if sys.byteorder == "big":
        frames.byteswap()
    return frames


def write_float_wav(path: Path, frames: array.array, sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(path, "wb") as wav_file:
        wav_file.setnchannels(CHANNELS)
        wav_file.setsampwidth(SAMPLE_WIDTH)
        wav_file.setframerate(sample_rate)
        wav_file.setformat(wave.WAVE_FORMAT_IEEE_FLOAT)
        wav_file.writeframes(frames.tobytes())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"output path (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    frames = build_frames()
    write_float_wav(args.output, frames, SAMPLE_RATE)
    print(
        f"wrote {args.output} "
        f"({len(frames) // CHANNELS / SAMPLE_RATE:.3f} s, {SAMPLE_RATE} Hz, "
        f"stereo float32, L={LEFT_DC}, R={RIGHT_DC})"
    )


if __name__ == "__main__":
    main()
