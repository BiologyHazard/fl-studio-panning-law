"""Dense extraction of the pan-law transfer curves from the DC render.

Input signal: L_in = 1, R_in = 0 (constant).
Assumed sweep: p = 2*i/(N_in-1) - 1  with N_in = 384000 (8 s @ 48 kHz).
So out_L(p) = mLL(p) and out_R(p) = mRL(p) directly.
"""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from wavlib import Wav

ROOT = Path(r"D:\BioHazard\Documents\FL Studio Pan Rule")

w = Wav(ROOT / "2024-09-19测试" / "test_pan_2024-09-19.wav")
s = w.samples()
L, R = s[:, 0], s[:, 1]
NIN = 384000

# --- 1. locate structural features exactly -------------------------------
print("== structure ==")
nzR = np.nonzero(R != 0.0)[0]
print(f"R == 0 exactly for first {nzR[0]} frames; R nonzero frames: {len(nzR)}")
print(f"imax L = {L.argmax()}  Lmax = {L.max():.15g}   (p_max = {2*L.argmax()/(NIN-1)-1:.9f})")
print(f"last nonzero L = {np.nonzero(L != 0.0)[0][-1]}")
print(f"first zero L after start = {np.nonzero(L == 0.0)[0][0]}")
print(f"L[0] = {L[0]:.15g}   1/sqrt2 = {1/np.sqrt(2):.15g}   diff = {L[0]-1/np.sqrt(2):.3e}")
print(f"R[383999] = {R[383999]:.15g}")

# --- 2. derivative structure to find kinks ------------------------------
dL = np.diff(L)
print("\n== derivative of L (per frame) at key points ==")
for i in [0, 50000, 100000, 143000, 170000, 190000, 191000, 192000, 193000, 200000,
          240000, 288000, 336000, 383000]:
    print(f"  i={i:7d} p={2*i/(NIN-1)-1:+.6f}  L={L[i]:.10f}  dL={dL[i]:.6e}  dL*NIN/2={dL[i]*NIN/2:.6f}")

# --- 3. dense table ------------------------------------------------------
print("\n== dense table (p, L, R) ==")
xs, ls, rs = [], [], []
for p10 in range(-100, 101, 5):
    p = p10 / 100.0
    i = int(round((p + 1) / 2 * (NIN - 1)))
    i = min(max(i, 0), NIN - 1)
    print(f"  p={p:+.3f}  i={i:7d}  L={L[i]:.10f}  R={R[i]:.10f}  L+R={L[i]+R[i]:.10f}  L-R={L[i]-R[i]:.10f}")
    xs.append(p); ls.append(L[i]); rs.append(R[i])

np.save(Path(__file__).parent / "curve_L.npy", L[:NIN])
np.save(Path(__file__).parent / "curve_R.npy", R[:NIN])
print("\nsaved curve_L.npy / curve_R.npy")
