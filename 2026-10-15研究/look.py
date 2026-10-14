"""First look at the measured pan-ramp renders."""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from wavlib import Wav

ROOT = Path(r"D:\BioHazard\Documents\FL Studio Pan Rule")

FILES = {
    "test_pan_2023": ROOT / "2023-06-21测试" / "test_pan.wav",
    "test_pan_2024": ROOT / "2024-09-19测试" / "test_pan_2024-09-19.wav",
    "untitled": ROOT / "untitled.wav",
}

for name, path in FILES.items():
    if not path.exists():
        print(f"--- {name}: MISSING {path}")
        continue
    w = Wav(path)
    print(f"=== {name} ===")
    print(" ", w.info())
    s = w.samples()
    l, r = s[:, 0], s[:, 1]
    print(f"  L: min={l.min():.10f} max={l.max():.10f} mean={l.mean():.10f} "
          f"first={l[0]:.10f} unique={len(np.unique(np.round(l, 12)))}")
    print(f"  R: min={r.min():.10f} max={r.max():.10f} mean={r.mean():.10f} "
          f"first={r[0]:.10f} unique={len(np.unique(np.round(r, 12)))}")
    # how many samples are constant (DC) at the very start
    d = np.abs(np.diff(l))
    nz = np.nonzero(d > 0)[0]
    print(f"  L first change at sample {nz[0] if len(nz) else 'none'}")
    d = np.abs(np.diff(r))
    nz = np.nonzero(d > 0)[0]
    print(f"  R first change at sample {nz[0] if len(nz) else 'none'}")
    print()
