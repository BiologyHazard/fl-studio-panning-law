"""Invert the pan angle theta out of the render, frame by frame.

If the derived law is correct, then per frame:
    left half  (theta <= pi/4):  L = cos(theta) * (k + sin(theta))
    right half (theta >= pi/4):  L = sqrt(2) * cos(theta)
Both are monotonic, so theta(i) is recoverable exactly (up to float32 storage).
Then we can see whether theta is a clean linear ramp, a staircase (quantised
parameter), or something curved.
"""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from wavlib import Wav

ROOT = Path(r"D:\BioHazard\Documents\FL Studio Pan Rule")
K = 1.0 / np.sqrt(2.0)

w = Wav(ROOT / "2024-09-19测试" / "test_pan_2024-09-19.wav")
Lm = w.samples()[:384000, 0]

MID = 192000
th = np.zeros(384000)

# --- left half: solve cos(t)*(k+sin(t)) = L for t in [0, pi/4] --------------
lo, hi = np.zeros(MID), np.full(MID, np.pi / 4)
for _ in range(80):
    mid = 0.5 * (lo + hi)
    f = np.cos(mid) * (K + np.sin(mid))
    lo = np.where(f < Lm[:MID], mid, lo)
    hi = np.where(f < Lm[:MID], hi, mid)
th[:MID] = 0.5 * (lo + hi)

# --- right half: theta = arccos(L / sqrt(2)) -------------------------------
th[MID:] = np.arccos(np.clip(Lm[MID:] / np.sqrt(2.0), -1.0, 1.0))

# --- is theta linear in frame index? --------------------------------------
i = np.arange(384000)
A = np.vstack([i, np.ones_like(i)]).T
coef, *_ = np.linalg.lstsq(A, th, rcond=None)
res = th - A @ coef
print(f"linear fit: theta = {coef[0]:.15e} * i + {coef[1]:.9f}")
print(f"  slope*384000 = {coef[0]*384000:.12f}   (pi/2 = {np.pi/2:.12f})")
print(f"  residual: max {np.abs(res).max():.3e}  rms {np.sqrt((res**2).mean()):.3e}")
print(f"  as pan:   max {np.abs(res).max()*4/np.pi:.3e}")

print("\n  i        th_measured        th_linear        diff")
for kk in [0, 1, 2, 3, 4, 5, 1000, 10000, 60000, 120000, 191999,
           192000, 192001, 192002, 200000, 250000, 300000, 350000, 383998, 383999]:
    print(f"  {kk:7d}  {th[kk]:.12f}  {(A@coef)[kk]:.12f}  {res[kk]:+.3e}")

# --- staircase detection: how many distinct theta values? -----------------
ths = np.round(th, 12)
print(f"\ndistinct theta values (12dp): {len(np.unique(ths))} of 384000")
d = np.diff(th)
print(f"d(theta)/di : min {d.min():.3e} max {d.max():.3e} "
      f"median {np.median(d):.3e}")
print(f"  (pure linear ramp over 384000 frames would give "
      f"{np.pi/2/384000:.3e} everywhere)")

# --- float32 quantisation of theta ---------------------------------------
th32 = th.astype(np.float32)
print(f"\nfloat32(theta) distinct: {len(np.unique(th32))}")
print(f"theta value near p=0: {th[MID]:.12f}")

# --- save for reuse -------------------------------------------------------
np.save(Path(__file__).parent / "theta_from_data.npy", th)
print("\nsaved theta_from_data.npy")
