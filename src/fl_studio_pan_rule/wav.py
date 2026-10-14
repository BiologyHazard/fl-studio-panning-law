"""Minimal dependency-free RIFF/WAVE reader.

FL Studio renders 32-bit float WAVs and the analysis needs the exact stored
sample values, so the data chunk is decoded straight from the file rather than
through an audio library that might resample or convert.
"""

from __future__ import annotations

import struct
from pathlib import Path

import numpy as np

FORMAT_PCM = 0x0001
FORMAT_IEEE_FLOAT = 0x0003
FORMAT_EXTENSIBLE = 0xFFFE

__all__ = ["Wav"]


class Wav:
    """A parsed WAVE file, exposing :meth:`samples` as float64."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        raw = self.path.read_bytes()
        if raw[0:4] != b"RIFF" or raw[8:12] != b"WAVE":
            raise ValueError(f"{self.path}: not a RIFF/WAVE file")

        pos, fmt, data, chunks = 12, None, None, []
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
            raise ValueError(f"{self.path}: missing fmt/data chunk")

        (
            self.audio_format,
            self.channels,
            self.sample_rate,
            self.byte_rate,
            self.block_align,
            self.bits,
        ) = struct.unpack_from("<HHIIHH", fmt, 0)
        self.chunks = chunks
        self.sub_format = (
            struct.unpack_from("<H", fmt, 24)[0]
            if self.audio_format == FORMAT_EXTENSIBLE
            else self.audio_format
        )
        self.n_frames = len(data) // self.block_align
        self.data = data

    def samples(self) -> np.ndarray:
        """Return an ``(n_frames, channels)`` float64 array of sample values."""
        n, ch = self.n_frames, self.channels
        if self.sub_format == FORMAT_IEEE_FLOAT and self.bits == 32:
            return np.frombuffer(self.data, dtype="<f4", count=n * ch).reshape(n, ch)
        if self.sub_format == FORMAT_IEEE_FLOAT and self.bits == 64:
            return np.frombuffer(self.data, dtype="<f8", count=n * ch).reshape(n, ch)
        if self.sub_format == FORMAT_PCM and self.bits == 16:
            raw = np.frombuffer(self.data, dtype="<i2", count=n * ch)
            return raw.reshape(n, ch) / 32768.0
        if self.sub_format == FORMAT_PCM and self.bits == 24:
            b = np.frombuffer(self.data, dtype=np.uint8, count=n * ch * 3).reshape(
                -1, 3
            )
            v = (
                b[:, 0].astype(np.int32)
                | (b[:, 1].astype(np.int32) << 8)
                | (b[:, 2].astype(np.int32) << 16)
            )
            v = np.where(v >= 1 << 23, v - (1 << 24), v)
            return v.reshape(n, ch) / 8388608.0
        if self.sub_format == FORMAT_PCM and self.bits == 32:
            raw = np.frombuffer(self.data, dtype="<i4", count=n * ch)
            return raw.reshape(n, ch) / 2147483648.0
        raise ValueError(f"unsupported format {self.sub_format}/{self.bits}")

    def __repr__(self) -> str:
        return (
            f"Wav({self.path.name!r}, ch={self.channels}, sr={self.sample_rate}, "
            f"bits={self.bits}, frames={self.n_frames}, "
            f"dur={self.n_frames / self.sample_rate:.4f}s)"
        )
