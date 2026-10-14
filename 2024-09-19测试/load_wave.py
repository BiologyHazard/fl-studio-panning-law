from argparse import ArgumentParser
from pathlib import Path

import numpy as np
import soundfile


def load_wave(path: str | Path):
    audio_data, sample_rate = soundfile.read(path, always_2d=True)
    if audio_data.shape[1] == 1:
        audio_data = np.column_stack((audio_data, audio_data))
    assert audio_data.ndim == 2 and audio_data.shape[1] == 2, (
        "Only support stereo wave file"
    )
    samples = audio_data.shape[0]
    length = samples / sample_rate
    l, r = audio_data[:, 0], audio_data[:, 1]
    mean = (l + r) / 2

    for i in range(sample_rate * 8 + 1):
        ls = l[i]
        rs = r[i]
        print(i, ls, rs)


parser = ArgumentParser()
parser.add_argument("path", type=str, help="Path to wave file")

args = parser.parse_args()
load_wave(args.path)
