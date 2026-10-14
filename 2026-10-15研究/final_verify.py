"""Final verification of the derived FL Studio mixer pan rule.

    theta = (pan + 1) * pi/4          pan in [-1, 1]
    A = sqrt(2)*cos(theta)            # the "left" circular gain
    B = sqrt(2)*sin(theta)            # the "right" circular gain

    pan <= 0 :  L' = A * ( ((1+B)/2)*L + ((1-B)/2)*R )
                R' = B * R
    pan >= 0 :  L' = A * L
                R' = B * ( ((1+A)/2)*R + ((1-A)/2)*L )

For a mono input (L == R) this collapses to (L', R') = L * sqrt2 * (cos, sin),
i.e. the documented equal-power "Circular" law at +3 dB.
"""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from wavlib import Wav

ROOT = Path(r"D:\BioHazard\Documents\FL Studio Pan Rule")
SQ2 = np.sqrt(2.0)


def pan_matrix(p):
    """Return gLL, gLR, gRL, gRR (arrays) for pan values p."""
    p = np.asarray(p, dtype=np.float64)
    th = (p + 1.0) * (np.pi / 4.0)
    A = SQ2 * np.cos(th)
    B = SQ2 * np.sin(th)
    left = p <= 0.0
    wT = np.where(left, (1.0 + B) / 2.0, (1.0 + A) / 2.0)   # target-channel blend
    gLL = np.where(left, A * wT, A)
    gLR = np.where(left, A * (1.0 - wT), 0.0)
    gRL = np.where(left, 0.0, B * (1.0 - wT))
    gRR = np.where(left, B, B * wT)
    return gLL, gLR, gRL, gRR


def apply_pan(p, L, R):
    gLL, gLR, gRL, gRR = pan_matrix(p)
    return gLL * L + gLR * R, gRL * L + gRR * R


print("=" * 72)
print("1. full-render check: test_pan_2024-09-19.wav  (input L=1, R=0)")
print("=" * 72)
w = Wav(ROOT / "2024-09-19测试" / "test_pan_2024-09-19.wav")
S = w.samples()
NIN = 384000
Lm, Rm = S[:NIN, 0], S[:NIN, 1]

th_data = np.load(Path(__file__).parent / "theta_from_data.npy")
p_from_theta = th_data * 4.0 / np.pi - 1.0

for name, p in [("pan = 2i/383999 - 1 (nominal linear ramp)",
                 2.0 * np.arange(NIN) / 383999.0 - 1.0),
                ("pan recovered from theta(i) (data-driven)",
                 p_from_theta)]:
    lo, ro = apply_pan(p, 1.0, 0.0)
    el, er = np.abs(lo - Lm), np.abs(ro - Rm)
    rel = np.maximum(np.abs(Lm), np.abs(Rm))
    print(f"  {name}")
    print(f"    L: max|err| {el.max():.3e}  rms {np.sqrt((el**2).mean()):.3e}  "
          f"max rel {np.max(el/np.maximum(np.abs(Lm),1e-9)):.2e} (L>0.1 region: "
          f"{np.max(el[np.abs(Lm)>0.1]/np.abs(Lm[np.abs(Lm)>0.1])):.2e})")
    print(f"    R: max|err| {er.max():.3e}  rms {np.sqrt((er**2).mean()):.3e}  "
          f"max rel {np.max(er[np.abs(Rm)>0.1]/np.abs(Rm[np.abs(Rm)>0.1])):.2e}")

print()
print("=" * 72)
print("2. the rule as a function of pan (matrix rows for unit inputs)")
print("=" * 72)
print("   pan      theta     A=√2cos   B=√2sin |   gLL      gLR      gRL      gRR")
for pv in [-1.0, -0.75, -0.5, -0.2552, 0.0, 0.25, 0.5, 0.75, 1.0]:
    g = pan_matrix(np.array([pv]))
    th = (pv + 1) * np.pi / 4
    print(f"  {pv:+.4f}  {th:.6f}  {SQ2*np.cos(th):+.6f}  {SQ2*np.sin(th):+.6f} | "
          f"{g[0][0]:+.6f} {g[1][0]:+.6f} {g[2][0]:+.6f} {g[3][0]:+.6f}")

print()
print("=" * 72)
print("3. sanity laws")
print("=" * 72)
pp = np.linspace(-1, 1, 200001)
gLL, gLR, gRL, gRR = pan_matrix(pp)
lo, ro = apply_pan(pp, 1.0, 1.0)
print(f"  mono input (L=R=1): L'^2+R'^2 min {np.min(lo**2+ro**2):.10f} "
      f"max {np.max(lo**2+ro**2):.10f}   (2.0 == +3 dB constant power)")
print(f"  mono input: L' max {lo.max():.9f}, R' max {ro.max():.9f} "
      f"(= sqrt2 = {SQ2:.9f})")
print(f"  pan=0 identity: max|gLL-1| {np.abs(gLL[np.argmin(np.abs(pp))]-1):.2e}, "
      f"max|gLR| {np.max(np.abs(gLR[100000:100001])):.2e}")
lo, ro = apply_pan(pp, 1.0, 0.0)
i = lo.argmax()
print(f"  hard-panned input (L=1,R=0): L' peak {lo.max():.12f} at pan "
      f"{pp[i]:.9f} (theta { (pp[i]+1)*np.pi/4:.9f})")
print(f"  hard left  (pan=-1): L'={lo[0]:.12f}  R'={ro[0]:.12f}")
print(f"  hard right (pan=+1): L'={lo[-1]:.12f}  R'={ro[-1]:.12f}  "
      f"(= 1/sqrt2 = {1/SQ2:.12f})")
print(f"  max gain any channel : {max(gLL.max(), gLR.max(), gRL.max(), gRR.max()):.12f}")
print(f"  min gain any channel : {min(gLL.min(), gLR.min(), gRL.min(), gRR.min()):.12f}")

print()
print("=" * 72)
print("4. independent check on the 2023 render (same law at -3 dB)"
      " test_pan.wav")
print("=" * 72)
w3 = Wav(ROOT / "2023-06-21测试" / "test_pan.wav")
S3 = w3.samples()
print(f"  frames={w3.n_frames} sr={w3.sample_rate} bits={w3.bits}")
L3, R3 = S3[:, 0], S3[:, 1]
nl, nr = np.abs(L3).max(), np.abs(R3).max()
print(f"  measured peaks: L {nl:.8f}  R {nr:.8f}   ratio {nl/nr:.6f}")
lo, ro = apply_pan(pp, 1.0, 0.0)
print(f"  model  peaks: L {lo.max():.8f}  R {ro.max():.8f}   ratio "
      f"{lo.max()/ro.max():.6f}")
print(f"  model ratio x 0.7071 = {lo.max()/ro.max()*1/SQ2:.6f}")
print(f"  measured L peak / model L peak = {nl/lo.max():.8f}")
print(f"  measured R peak / model R peak = {nr/ro.max():.8f}")
print(f"  -> common scale factor {nl/lo.max():.9f}  "
      f"(1/sqrt2 = {1/SQ2:.9f}, 16-bit quantum = {1/32768:.9f})")
