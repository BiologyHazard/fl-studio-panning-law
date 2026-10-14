"""Dump the DC-offset pan-ramp render as (time, L, R) so we can see the law."""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from wavlib import Wav

ROOT = Path(r"D:\BioHazard\Documents\FL Studio Pan Rule")

# the source DC files, to confirm the exact input
for src in [ROOT / "2024-09-19测试" / "DC偏移100%_左声道.wav",
            ROOT / "2024-09-19测试" / "DC偏移100%_右声道.wav",
            ROOT / "2023-06-21测试" / "DC偏移100%.wav"]:
    w = Wav(src)
    s = w.samples()
    print(f"--- INPUT {w.path.name}: {w.info()}")
    print(f"    L[0..3]={s[:4,0]}  R[0..3]={s[:4,1]}")
    print(f"    L unique={np.unique(s[:,0])[:8]}  R unique={np.unique(s[:,1])[:8]}")
    print()

w = Wav(ROOT / "2024-09-19测试" / "test_pan_2024-09-19.wav")
s = w.samples()
l, r = s[:, 0], s[:, 1]
n = w.n_frames
sr = w.sample_rate
print(f"OUTPUT {w.path.name}: frames={n} sr={sr} dur={n/sr}")

# print the curve every 1/32 of the file
print("\n  idx      t(s)         L                 R")
for i in range(0, n, n // 64):
    print(f"{i:8d} {i/sr:9.5f}  {l[i]:.12f}  {r[i]:.12f}")

# where does R become nonzero / where does it peak
nzr = np.nonzero(np.abs(r) > 1e-12)[0]
print(f"\nR nonzero: first={nzr[0] if len(nzr) else None} last={nzr[-1] if len(nzr) else None}")
nzl = np.nonzero(np.abs(l) > 1e-12)[0]
print(f"L nonzero: first={nzl[0] if len(nzl) else None} last={nzl[-1] if len(nzl) else None}")
print(f"L argmax={l.argmax()} = {l.max():.12f}   R argmax={r.argmax()} = {r.max():.12f}")
print(f"L argmin={l.argmin()} = {l.min():.12f}   R argmin={r.argmin()} = {r.min():.12f}")
print(f"\nL tail: {l[-4:]}   R tail: {r[-4:]}")
print(f"L head: {l[:8]}")
