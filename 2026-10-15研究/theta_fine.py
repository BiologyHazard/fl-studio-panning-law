import numpy as np
from pathlib import Path

th = np.load(Path(__file__).parent / "theta_from_data.npy")
N = len(th); MID = 192000
slope = (th[N-1] - th[MID]) / (N-1-MID)
lin = th[MID] + slope * (np.arange(N, dtype=np.float64) - MID)
dev = th - lin

print("=== dev at FULL resolution, i = 192000..192120 ===")
for i in range(192000, 192121):
    print(f"  {i:7d}  dev={dev[i]:+.6e}   d(dev)={dev[i]-dev[i-1]:+.3e}")

print("\n=== autocorrelation for SHORT lags (1..60) ===")
d = dev[MID:200000] - dev[MID:200000].mean()
ac = np.correlate(d, d, mode="full")[len(d)-1:]
ac /= ac[0]
for lag in range(1, 61):
    bar = "#" * max(0, int(ac[lag] * 40))
    print(f"  lag {lag:3d}  r={ac[lag]:+.4f} {bar}")
