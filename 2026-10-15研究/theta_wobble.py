"""Characterise the ~4e-5 rad wobble in theta(i) - the automation timeline.

Question: is the wobble periodic in frame index (a timeline / control-rate
artefact) or a function of theta (which would mean the law itself needs a
correction)?  Answer by comparing the same index range on the left and right
halves, where theta is very different.
"""

import numpy as np
from pathlib import Path

th = np.load(Path(__file__).parent / "theta_from_data.npy")
N = len(th)
MID = 192000
slope = (th[N - 1] - th[MID]) / (N - 1 - MID)
idx = np.arange(N, dtype=np.float64)
lin = th[MID] + slope * (idx - MID)
dev = th - lin

print(f"slope = {slope:.15e} rad/frame")

print("\n=== dev(i) over the first cycle, step 125 ===")
for i in range(0, 6125, 125):
    print(f"  i={i:5d}  dev={dev[i]:+.5e}")

print("\n=== dev(i) over the same phase on the RIGHT half (i-192000 in 0..6000) ===")
for i in range(192000, 198125, 250):
    print(f"  i={i:7d}  (phase {i-192000:5d})  dev={dev[i]:+.5e}")

print("\n=== is dev a function of (i mod 6000)? ===")
for phase in [500, 1000, 2000, 3000, 4000, 5000]:
    vals = [dev[k * 6000 + phase] for k in range(0, N // 6000)]
    print(f"  phase {phase:5d}: mean {np.mean(vals):+.4e}  std {np.std(vals):.3e}  "
          f"n={len(vals)}")

print("\n=== autocorrelation of dev (period search, right half) ===")
d = dev[MID:] - dev[MID:].mean()
ac = np.correlate(d, d, mode="full")[len(d) - 1:]
ac /= ac[0]
best = []
for lag in range(100, 20000):
    if ac[lag] > ac[lag - 1] and ac[lag] >= ac[lag + 1]:
        best.append((ac[lag], lag))
best.sort(reverse=True)
for v, lag in best[:8]:
    print(f"  lag {lag:6d} frames ({lag/48000*1000:.4f} ms @48k)  r={v:.4f}")

print("\n=== amplitude of the wobble ===")
print(f"  dev: min {dev.min():+.4e} max {dev.max():+.4e} "
      f"ptp {dev.max()-dev.min():.4e} rad")
print(f"  in pan units: ptp {(dev.max()-dev.min())*4/np.pi:.4e}")
print(f"  in L units  : ptp {(dev.max()-dev.min())*np.sqrt(2):.4e}")

print("\n=== residual if we use a per-750-frame (15.625 ms) piecewise fit ===")
# FL mixes in blocks; check whether a fine piecewise-linear theta removes it
for blk in [64, 128, 256, 512, 1024, 6000]:
    nb = N // blk
    t = th[: nb * blk].reshape(nb, blk)
    j = np.arange(blk)
    t0 = t[:, 0:1]
    t1 = t[:, -1:]
    fit = t0 + (t1 - t0) * (j / (blk - 1))
    err = np.abs(t - fit)
    print(f"  block={blk:5d}  max|err| {err.max():.3e}  rms "
          f"{np.sqrt((err**2).mean()):.3e}")
