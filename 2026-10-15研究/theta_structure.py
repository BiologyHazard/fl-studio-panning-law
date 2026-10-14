"""Refine: recover theta(i) with correct branch continuity, then characterise
the small deviation from a perfectly linear ramp.

Deviation magnitude ~5e-5 rad suggests either
  (a) FL evaluates automation per audio block and interpolates,
  (b) the pan parameter is quantised then smoothed,
  (c) a genuine tiny non-linearity in the knob law.
A fine-resolution look at the deviation distinguishes them.
"""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from wavlib import Wav

ROOT = Path(r"D:\BioHazard\Documents\FL Studio Pan Rule")
K = 1.0 / np.sqrt(2.0)
N = 384000
MID = 192000
TH_MID = np.pi / 4

w = Wav(ROOT / "2024-09-19测试" / "test_pan_2024-09-19.wav")
L = w.samples()[:N, 0]

thetas = np.zeros(N)

# right half is monotonic: theta = arccos(L/sqrt2)
thetas[MID:] = np.arccos(np.clip(L[MID:] / np.sqrt(2.0), -1.0, 1.0))

# left half: forward pass with branch continuity (function rises then falls)
prev = 0.0
for i in range(MID):
    lo, hi = 0.0, TH_MID
    for _ in range(60):
        m = 0.5 * (lo + hi)
        f = np.cos(m) * (K + np.sin(m))
        if f < L[i]:
            lo = m
        else:
            hi = m
    root_small = 0.5 * (lo + hi)
    # the other root lies in (theta_peak, pi/4]; solve on that bracket too
    lo2, hi2 = 0.585, TH_MID   # peak of cos(t)(k+sin t) is near t=0.5853
    for _ in range(60):
        m = 0.5 * (lo2 + hi2)
        f = np.cos(m) * (K + np.sin(m))
        if f > L[i]:
            lo2 = m
        else:
            hi2 = m
    root_big = 0.5 * (lo2 + hi2)
    cands = [root_small, root_big]
    pick = min(cands, key=lambda t: abs(t - prev))
    thetas[i] = pick
    prev = pick

np.save(Path(__file__).parent / "theta_from_data.npy", thetas)

print("=== theta at landmarks ===")
for i in [0, 1, 2, 1000, 48000, 96000, 143000, 191998, 191999, 192000,
          192001, 192002, 240000, 288000, 336000, 383998, 383999]:
    print(f"  i={i:7d}  theta={thetas[i]:.12f}")

# best linear ramp fitted to the right half only (unambiguous branch)
idx = np.arange(N, dtype=np.float64)
slope = (thetas[N - 1] - thetas[MID]) / (N - 1 - MID)
lin = thetas[MID] + slope * (idx - MID)
dev = thetas - lin
print(f"\nslope (right half) = {slope:.15e}   theta span = "
      f"{slope * (N - 1 - MID):.12f}  (pi/4 = {TH_MID:.12f})")
print(f"deviation: max {np.abs(dev).max():.3e}  rms {np.sqrt((dev**2).mean()):.3e}")
print(f"  in pan units: max {np.abs(dev).max() * 4 / np.pi:.3e}")

print("\n=== fine structure: deviation at consecutive frames (i = 0..40) ===")
for i in range(0, 41):
    print(f"  {i:4d}  theta={thetas[i]:.14f}  dev={dev[i]:+.4e}")

print("\n=== deviation sampled every 2000 frames across the file ===")
for i in range(0, N, 2000):
    print(f"  {i:7d}  dev={dev[i]:+.5e}")

print("\n=== histogram of frame-to-frame d(theta) on the right half ===")
d = np.diff(thetas[MID:])
print(f"  min {d.min():.4e} max {d.max():.4e} mean {d.mean():.6e} "
      f"median {np.median(d):.6e}")
h, edges = np.histogram(d, bins=12)
for cnt, e0, e1 in zip(h, edges[:-1], edges[1:]):
    print(f"  [{e0:.4e}, {e1:.4e}) {cnt}")
print(f"  unique d values: {len(np.unique(np.round(d, 15)))}")
