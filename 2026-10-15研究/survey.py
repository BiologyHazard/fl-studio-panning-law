"""Survey every audio file in the project: inputs vs renders, key stats."""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from wavlib import Wav

ROOT = Path(r"D:\BioHazard\Documents\FL Studio Pan Rule")

FILES = sorted(ROOT.rglob("*.wav"))
for p in FILES:
    if ".mimocode" in str(p):
        continue
    try:
        w = Wav(p)
    except Exception as e:
        print(f"{p.name}: ERROR {e}")
        continue
    s = w.samples()
    l, r = s[:, 0], s[:, 1]
    print(f"{p.parent.name}/{p.name}")
    print(f"    ch={w.channels} sr={w.sample_rate} bits={w.bits} fmt={w.sub_format} "
          f"frames={w.n_frames} dur={w.n_frames/w.sample_rate:.5f}s")
    print(f"    L: [{l.min():+.10f}, {l.max():+.10f}] mean={l.mean():+.10f} uniq={len(np.unique(l))}")
    print(f"    R: [{r.min():+.10f}, {r.max():+.10f}] mean={r.mean():+.10f} uniq={len(np.unique(r))}")
