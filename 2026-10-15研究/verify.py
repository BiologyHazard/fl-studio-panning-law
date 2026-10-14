"""Verify the closed-form pan rule against all 384000 rendered frames.

Derived model (pan p in [-1, 1]):

    theta = (p + 1) * pi/4        # 0 at hard left, pi/4 at centre, pi/2 at hard right
    c = cos(theta);  s = sin(theta);  k = 1/sqrt(2)

    p <= 0 :  L' = L*c*(k + s) + R*c*(k - s)
              R' = R*(s/k)                  # s/k == sqrt(2)*s
    p >= 0 :  L' = L*(c/k)                  # c/k == sqrt(2)*c
              R' = L*s*(k - c) + R*s*(k + c)
"""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from wavlib import Wav

OUT = Path(__file__).parent
ROOT = Path(r"D:\BioHazard\Documents\FL Studio Pan Rule")

K = 1.0 / np.sqrt(2.0)


def model(p, L, R):
    th = (p + 1.0) * (np.pi / 4.0)
    c = np.cos(th)
    s = np.sin(th)
    left = p <= 0.0
    lo = np.where(left, L * c * (K + s) + R * c * (K - s), L * (c / K))
    ro = np.where(left, R * (s / K), L * s * (K - c) + R * s * (K + c))
    return lo, ro


w = Wav(ROOT / "2024-09-19测试" / "test_pan_2024-09-19.wav")
samples = w.samples()
Lm = samples[:384000, 0]
Rm = samples[:384000, 1]

for label, p in [
    ("p = 2i/383999 - 1", 2.0 * np.arange(384000) / 383999.0 - 1.0),
    ("p = 2i/384000 - 1", 2.0 * np.arange(384000) / 384000.0 - 1.0),
]:
    lo, ro = model(p, 1.0, 0.0)
    el = np.abs(lo - Lm)
    er = np.abs(ro - Rm)
    print(f"=== {label}")
    print(f"  L: max err {el.max():.3e}  rms {np.sqrt((el**2).mean()):.3e}  "
          f"argmax {el.argmax()}")
    print(f"  R: max err {er.max():.3e}  rms {np.sqrt((er**2).mean()):.3e}  "
          f"argmax {er.argmax()}")
    print(f"  max |L| = {np.abs(Lm).max():.9f}  -> worst rel err L "
          f"{(el/np.maximum(np.abs(Lm),1e-6)).max():.3e}")

# now with full 2x2 (both input channels) - use the R-channel-input render if it exists
right_src = ROOT / "2024-09-19测试" / "DC偏移100%_右声道.wav"
print("\n=== sanity: identity at p=0, mono-sum at p=+1 ===")
for pv in [-1.0, -0.5, -0.255206394, 0.0, 0.5, 1.0]:
    lo, ro = model(np.array([pv]), np.array([1.0]), np.array([0.0]))
    print(f"  p={pv:+.4f}  L'={lo[0]:.9f}  R'={ro[0]:.9f}")

print("\n=== matrix at both extremes (general stereo input) ===")
for pv in [-1.0, -0.5, 0.0, 0.5, 1.0]:
    a = model(np.array([pv]), np.array([1.0]), np.array([0.0]))
    b = model(np.array([pv]), np.array([0.0]), np.array([1.0]))
    print(f"  p={pv:+.2f}  [[{a[0][0]:+.9f}, {b[0][0]:+.9f}], "
          f"[{a[1][0]:+.9f}, {b[1][0]:+.9f}]]")

# float32 arithmetic variant, to see whether FL's precision explains residuals
print("\n=== same model evaluated in float32 ===")
def model32(p, L, R):
    p = np.float32(p); L = np.float32(L); R = np.float32(R)
    th = (p + np.float32(1.0)) * np.float32(np.pi / 4.0)
    c = np.cos(th, dtype=np.float32)
    s = np.sin(th, dtype=np.float32)
    k = np.float32(K)
    return c, s

p = 2.0 * np.arange(384000) / 383999.0 - 1.0
lo64, ro64 = model(p, 1.0, 0.0)
lo32, ro32 = model32(p.astype(np.float32), np.float32(1.0), np.float32(0.0))[0], None
print("  (informational) theta granularity at 48k:", np.pi / 4 / 384000)
