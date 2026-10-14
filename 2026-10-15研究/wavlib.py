"""Minimal dependency-free WAV reader + rounded-float decoding helper.

FL Studio renders 32-bit float WAVs. We need bit-exact float values, so we read
the data chunk manually instead of going through any resampling decoder.
"""

from __future__ import annotations

import struct
from pathlib import Path

import numpy as np

FORMAT_PCM = 0x0001
FORMAT_IEEE_FLOAT = 0x0003
FORMAT_EXTENSIBLE = 0xFFFE


class Wav:
    def __init__(self, path):
        self.path = Path(path)
        raw = self.path.read_bytes()
        self.raw = raw
        if raw[0:4] != b"RIFF" or raw[8:12] != b"WAVE":
            raise ValueError(f"{path}: not a RIFF/WAVE file")

        pos = 12
        fmt = None
        data = None
        chunks = []
        while pos + 8 <= len(raw):
            cid = raw[pos : pos + 4]
            (csize,) = struct.unpack_from("<I", raw, pos + 4)
            body = raw[pos + 8 : pos + 8 + csize]
            chunks.append((cid.decode("latin-1"), csize))
            if cid == b"fmt ":
                fmt = body
            elif cid == b"data":
                data = body
            pos += 8 + csize + (csize & 1)

        if fmt is None or data is None:
            raise ValueError(f"{path}: missing fmt/data chunk")

        (self.audio_format, self.channels, self.sample_rate, self.byte_rate,
         self.block_align, self.bits) = struct.unpack_from("<HHIIHH", fmt, 0)
        self.chunks = chunks
        self.fmt_raw = fmt

        if self.audio_format == FORMAT_EXTENSIBLE:
            (self.sub_format,) = struct.unpack_from("<H", fmt, 24)
        else:
            self.sub_format = self.audio_format

        self.n_frames = len(data) // self.block_align
        self.data = data

    def samples(self):
        """Return (n_frames, channels) float64 array of exact sample values."""
        n, ch = self.n_frames, self.channels
        if self.sub_format == FORMAT_IEEE_FLOAT and self.bits == 32:
            arr = np.frombuffer(self.data, dtype="<f4", count=n * ch)
            return arr.reshape(n, ch).astype(np.float64)
        if self.sub_format == FORMAT_IEEE_FLOAT and self.bits == 64:
            arr = np.frombuffer(self.data, dtype="<f8", count=n * ch)
            return arr.reshape(n, ch)
        if self.sub_format == FORMAT_PCM and self.bits == 16:
            arr = np.frombuffer(self.data, dtype="<i2", count=n * ch)
            return arr.reshape(n, ch).astype(np.float64) / 32768.0
        if self.sub_format == FORMAT_PCM and self.bits == 24:
            b = np.frombuffer(self.data, dtype=np.uint8, count=n * ch * 3)
            b = b.reshape(n * ch, 3)
            v = (b[:, 0].astype(np.int32)
                 | (b[:, 1].astype(np.int32) << 8)
                 | (b[:, 2].astype(np.int32) << 16))
            v = np.where(v >= 1 << 23, v - (1 << 24), v)
            return v.reshape(n, ch).astype(np.float64) / 8388608.0
        if self.sub_format == FORMAT_PCM and self.bits == 32:
            arr = np.frombuffer(self.data, dtype="<i4", count=n * ch)
            return arr.reshape(n, ch).astype(np.float64) / 2147483648.0
        raise ValueError(f"unsupported format {self.sub_format}/{self.bits}")

    def info(self):
        return (f"{self.path.name}: fmt={self.audio_format}/sub={self.sub_format} "
                f"ch={self.channels} sr={self.sample_rate} bits={self.bits} "
                f"frames={self.n_frames} dur={self.n_frames / self.sample_rate:.4f}s "
                f"chunks={self.chunks}")


def f32(v):
    """Round a float64 value to the nearest float32 (what FL wrote to disk)."""
    return np.float32(v)


if __name__ == "__main__":
    import sys

    for p in sys.argv[1:]:
        w = Wav(p)
        print(w.info())
