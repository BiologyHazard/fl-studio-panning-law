"""Cross-check the rule with renders that use a different input, and do a
bounded binary search for a precomputed pan-gain table.

Independent check: for a MONO input (L == R == s) the rule predicts
    L' = sqrt(2)*cos(theta)*s      R' = sqrt(2)*sin(theta)*s
so the L/R output ratio must equal cot(theta) = cot((p+1)*pi/4) exactly.
That constrains A and B *independently* of the (L=1,R=0) render, and then
gLL = A*(1+B)/2, gRL = B, gLR = A*(1-B)/2, gRR = 0 must reproduce the first
render.
"""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from wavlib import Wav

ROOT = Path(r"D:\BioHazard\Documents\FL Studio Pan Rule")
SQ2 = np.sqrt(2.0)

for name, path in [
    ("2023 test_sinewave.wav", ROOT / "2023-06-21测试" / "test_sinewave.wav"),
    ("2023 test_dc.wav", ROOT / "2023-06-21测试" / "test_dc.wav"),
    ("2024 untitled.wav", ROOT / "untitled.wav"),
]:
    w = Wav(path)
    S = w.samples()
    L, R = S[:, 0], S[:, 1]
    n = w.n_frames
    print(f"=== {name}: frames={n} sr={w.sample_rate} bits={w.bits}")
    print(f"    L range [{L.min():+.6f},{L.max():+.6f}]  "
          f"R range [{R.min():+.6f},{R.max():+.6f}]")
    # ratio R/L should be tan(theta) if the input is mono
    m = (np.abs(L) > 0.05) & (np.abs(R) > 0.05)
    if m.sum() > 100:
        ratio = (R[m] / L[m])
        theta_pred = 2.0 * np.arange(n)[m] / (n - 1) * 0.0  # placeholder
        # derive theta from the ratio and compare with the linear ramp
        th_from_ratio = np.arctan(ratio)
        idx = np.arange(n)[m]
        # linear ramp hypothesis over the same span as the 2024 render
        nref = 384000
        th_lin = (2.0 * idx / (nref - 1)) * (np.pi / 4)
        d = th_from_ratio - th_lin
        print(f"    mono hypothesis: R/L = tan(theta) -> theta vs linear ramp")
        print(f"      residual max {np.abs(d).max():.3e}  rms "
              f"{np.sqrt((d**2).mean()):.3e} rad   (n={m.sum()})")
        print(f"      theta_from_ratio range [{th_from_ratio.min():.5f}, "
              f"{th_from_ratio.max():.5f}]  linear range "
              f"[{th_lin.min():.5f}, {th_lin.max():.5f}]")
    print()

# ---------------------------------------------------------------- table scan
print("=== binary scan: monotone float32 tables that could be pan gains ===")
import pefile

DLL = Path(r"C:\Program Files\Image-Line\FL Studio 20\FLEngine_x64.dll")
pe = pefile.PE(str(DLL), fast_load=True)
raw = DLL.read_bytes()
fl = np.frombuffer(raw[: len(raw) // 4 * 4], dtype="<f4").astype(np.float64)
print(f"  float32 count = {len(fl)}")

# a circular-pan table: starts at ~sqrt2 and decreases monotonically to ~0
starts = np.nonzero((fl > 1.4130) & (fl < 1.4155) & (np.isfinite(fl)))[0]
print(f"  candidates starting near sqrt2: {len(starts)}")
hits = 0
for s0 in starts[:4000]:
    seg = fl[s0: s0 + 600]
    if len(seg) < 600:
        continue
    if not np.all(np.isfinite(seg)):
        continue
    d = np.diff(seg)
    if np.all(d <= 0) and seg[-1] < 0.02 and seg[0] > 1.4:
        print(f"  monotone-decreasing sqrt2-start table at float index {s0} "
              f"(file off {s0*4:#x}) len>=600, end {seg[-1]:.6f}")
        hits += 1
        if hits > 8:
            break
if hits == 0:
    print("  none found")

# a table matching the MEASURED hard-panned curve (peaks at 1.0499 then falls)
peaks = np.nonzero((fl > 1.0495) & (fl < 1.0505))[0]
print(f"  float32 values near the observed peak 1.0499: {len(peaks)}")
shown = 0
for s0 in peaks:
    if s0 >= len(fl) - 40:
        continue
    nb = fl[max(0, s0 - 12): s0 + 28]
    if np.all(np.isfinite(nb)) and nb.min() > 0.5 and nb.max() < 1.06:
        print(f"    {s0} {np.round(fl[max(0,s0-6):s0+10], 6)}")
        shown += 1
        if shown > 6:
            break
if shown == 0:
    print("    no monotone neighbourhoods")
