"""Extra cross-checks on the other 2023 renders.

(a) test_sinewave.wav - assumed mono input: the rule then predicts
    L'^2 + R'^2 = 2*s^2 with NO pan dependence, i.e. perfectly constant power.
    That independently fixes the magnitude sqrt(2) (= +3 dB) of A and B.
(b) test_dc.wav - seems to lack the >1 bump. Check whether it is a different
    law (e.g. Triangular) on the same kind of input.
"""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from wavlib import Wav

ROOT = Path(r"D:\BioHazard\Documents\FL Studio Pan Rule")
SQ2 = np.sqrt(2.0)

# ------------------------------------------------------------------ (a)
print("=" * 70)
print("(a) test_sinewave.wav : mono-input constant-power test")
print("=" * 70)
w = Wav(ROOT / "2023-06-21测试" / "test_sinewave.wav")
S = w.samples()
L, R = S[:, 0].astype(np.float64), S[:, 1].astype(np.float64)
n = len(L)
WIN = 480                      # 10 ms
nw = n // WIN
pl = np.abs(L[: nw * WIN].reshape(nw, WIN)).max(axis=1)
pr = np.abs(R[: nw * WIN].reshape(nw, WIN)).max(axis=1)
p2 = pl ** 2 + pr ** 2
good = (pl > 0.02) & (pr > 0.02)
print(f"  windows={nw}  usable={good.sum()}")
print(f"  peakL^2+peakR^2 : min {p2[good].min():.6f} max {p2[good].max():.6f} "
      f"mean {p2[good].mean():.6f} std {p2[good].std():.3e}")
print(f"  => relative spread {(p2[good].max()-p2[good].min())/p2[good].mean():.3e}")
print(f"  sqrt(mean/2) = implied source amplitude "
      f"{np.sqrt(p2[good].mean()/2):.6f}")
th = np.arctan2(pr[good], pl[good])            # = theta if the law is A,B
idx = np.arange(nw)[good] * WIN
th_lin = (idx / (n - 1)) * (np.pi / 2)
print(f"  theta range recovered [{th.min():.5f},{th.max():.5f}]  "
      f"linear [{th_lin.min():.5f},{th_lin.max():.5f}]")
print(f"  theta - linear: max {np.abs(th-th_lin).max():.3e} "
      f"rms {np.sqrt(((th-th_lin)**2).mean()):.3e}")

# ------------------------------------------------------------------ (b)
print()
print("=" * 70)
print("(b) test_dc.wav : does it show the bump?")
print("=" * 70)
w2 = Wav(ROOT / "2023-06-21测试" / "test_dc.wav")
S2 = w2.samples()
L2, R2 = S2[:, 0].astype(np.float64), S2[:, 1].astype(np.float64)
n2 = len(L2)
nzr = np.nonzero(R2 != 0)[0]
nzl = np.nonzero(L2 == 0)[0]
print(f"  frames={n2}")
print(f"  R!=0 : first {nzr[0] if len(nzr) else None} "
      f"last {nzr[-1] if len(nzr) else None}")
print(f"  L==0 : first {nzl[0] if len(nzl) else None} "
      f"last {nzl[-1] if len(nzl) else None}")
print(f"  L max {L2.max():.6f} at {L2.argmax()}   R max {R2.max():.6f} at "
      f"{R2.argmax()}")
print(f"  L max / R max = {L2.max()/R2.max():.6f}")
print(f"  (rule with bump would give 1.049899/0.707107 = "
      f"{1.0498988/0.7071068:.6f};  without bump 1/0.707107 = "
      f"{1/0.7071068:.6f})")

print("\n  30-point dump of the test_dc curves:")
for k in range(0, n2, n2 // 30):
    print(f"    i={k:7d}  L={L2[k]:.6f}  R={R2[k]:.6f}")

# is L monotone in the first half (no bump)?
half = n2 // 2
d = np.diff(L2[:half])
print(f"\n  first half: dL min {d.min():+.3e} max {d.max():+.3e}  "
      f"monotone-decreasing? {bool(np.all(d <= 0))}")
print(f"  L[0]={L2[0]:.6f}  L[half]={L2[half]:.6f}  L[half-1]={L2[half-1]:.6f}")

# does the (1,0)-input rule fit if we allow an arbitrary pan timeline?
print("\n  fit of the Derived rule with input (a, 0), free linear ramp:")
best = None
for NIN in (n2, 384000):
    p = 2.0 * np.arange(n2) / (NIN - 1) - 1.0
    th2 = (p + 1.0) * (np.pi / 4.0)
    A = SQ2 * np.cos(th2)
    B = SQ2 * np.sin(th2)
    left = p <= 0
    gLL = np.where(left, A * (1 + B) / 2, A)
    gRL = np.where(left, 0.0, B * (1 - A) / 2)
    a = (L2 * gLL + R2 * gRL).sum() / (gLL ** 2 + gRL ** 2).sum()
    res = a * gLL - L2
    resr = a * gRL - R2
    print(f"    NIN={NIN}: best a={a:.6f}  L rms {np.sqrt((res**2).mean()):.3e}"
          f"  R rms {np.sqrt((resr**2).mean()):.3e}")
