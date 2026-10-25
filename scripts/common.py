"""Shared data, explicit candidate models, and publication plot styling.

Run the individual fig_*.py files directly, or run build.py for all outputs.
No coefficients or time offsets are fitted to the recordings.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import wave

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "images" / "figures"
RESULTS = ROOT / "results"
COLORS = ("#1967a3", "#c05228")


@dataclass(frozen=True)
class Case:
    control: str
    law: str

    @property
    def name(self) -> str:
        return f"{self.control} {self.law}"

    @property
    def path(self) -> Path:
        return ROOT / "output-wav-files" / f"{self.name} Panning.wav"


CASES = tuple(Case(c, law) for c in ("Mixer", "Audio Clip")
              for law in ("Circular", "Triangular"))


@lru_cache(maxsize=8)
def read_wav(path: Path) -> tuple[int, np.ndarray]:
    with wave.open(str(path), "rb") as stream:
        if (stream.getnchannels(), stream.getsampwidth(), stream.getformat()) != (2, 4, 3):
            raise ValueError(f"Expected stereo IEEE float32: {path}")
        rate, count = stream.getframerate(), stream.getnframes()
        data = np.frombuffer(stream.readframes(count), dtype="<f4").reshape(-1, 2)
    if len(data) != count or not np.isfinite(data).all():
        raise ValueError(f"Invalid sample data: {path}")
    data = data.astype(np.float64)
    data.flags.writeable = False
    return rate, data


def nominal_pan(count: int, *, endpoint: bool = False) -> np.ndarray:
    """t=n/fs, T=N/fs: nominal p=-1+2t/T. Endpoint=True is a sensitivity check."""
    return -1 + 2 * np.arange(count, dtype=np.float64) / (count - int(endpoint))


def gains(pan: np.ndarray, law: str) -> tuple[np.ndarray, np.ndarray]:
    p = np.asarray(pan, dtype=np.float64)
    if law == "Circular":
        angle = (p + 1) * np.pi / 4
        return np.sqrt(2) * np.cos(angle), np.sqrt(2) * np.sin(angle)
    if law == "Triangular":
        return 1 - np.maximum(p, 0), 1 + np.minimum(p, 0)
    raise ValueError(law)


def matrix(pan: np.ndarray, case: Case) -> np.ndarray:
    p = np.asarray(pan, dtype=np.float64)
    u, v = gains(p, case.law)
    a = np.zeros(p.shape + (2, 2))
    if case.control == "Audio Clip":
        a[..., 0, 0], a[..., 1, 1] = u, v
    elif case.control == "Mixer":
        a[..., 0, 0] = np.where(p <= 0, u * (1 + v) / 2, u)
        a[..., 0, 1] = np.where(p <= 0, u * (1 - v) / 2, 0)
        a[..., 1, 0] = np.where(p <= 0, 0, v * (1 - u) / 2)
        a[..., 1, 1] = np.where(p <= 0, v, v * (1 + u) / 2)
    else:
        raise ValueError(case.control)
    return a


def measured(case: Case) -> tuple[np.ndarray, np.ndarray]:
    _, data = read_wav(case.path)
    return nominal_pan(len(data)), data


def errors(values: np.ndarray) -> dict[str, float]:
    return {"max_abs": float(np.max(np.abs(values))),
            "rms": float(np.sqrt(np.mean(values ** 2)))}


def style() -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                        "axes.spines.top": False, "axes.spines.right": False,
                        "axes.grid": True, "grid.alpha": .18,
                        "axes.axisbelow": True, "legend.frameon": False,
                        "figure.constrained_layout.use": True,
                        "savefig.dpi": 180, "svg.fonttype": "none"})


def save(fig: plt.Figure, stem: str) -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "svg"):
        fig.savefig(DEST / f"{stem}.{extension}")
    plt.close(fig)
    print(f"Saved {stem} (PNG, SVG)")
