from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

sample_rate = 48000
duration = 8

path = Path('output.txt')


def sine_func(x, A, B, C, D):
    return A * (np.sin(B * np.pi * (x + C)) + D)
    # return A + B * x + C * x ** 2 + D * x ** 3


text = path.read_text()
lines = text.strip().splitlines()[0:384001]
ts, l2l, l2r = np.zeros(len(lines)), np.zeros(len(lines)), np.zeros(len(lines))
for i, line in enumerate(lines):
    t, l, r = line.split()
    ts[i] = int(t) / sample_rate / duration * 2 - 1
    l2l[i] = float(l)
    l2r[i] = float(r)

r2l = l2r[::-1]
r2r = l2l[::-1]

after_l = l2l + r2l
after_r = l2r + r2r
P = after_l ** 2 + after_r ** 2
# print(*P, sep='\n')
# exit()


# 使用curve_fit进行拟合z
initial_guess = (0.1, 0.1, 0.1, 0)  # 初始猜测值
params, covariance = curve_fit(sine_func, ts[192000:], l2r[192000:])

# 输出拟合得到的参数
A_fit, B_fit, C_fit, D_fit = params
print(f"Fit Parameters: A={A_fit}, B={B_fit}, C={C_fit}, D={D_fit}")

# 计算拟合后的y值
y_fit = sine_func(ts[192000:], *params)

# 可视化原始数据与拟合曲线
# plt.figure()

# ts = np.sin((ts - 1) * np.pi / 4)
# plt.plot(ts[192000:], y_fit, 'b.', label=f"fit: A={A_fit}, B={B_fit}, C={C_fit}, D={D_fit}")
plt.plot(ts, l2l, label="l2l")
plt.plot(ts, l2r, label="l2r")
plt.plot(ts, r2l, label="r2l")
plt.plot(ts, r2r, label="r2r")
# plt.plot(ts, after_l, label='after_l')
# plt.plot(ts, after_r, label='after_r')

# plt.plot(ts, l2l ** 2, label='l2l^2')
# plt.plot(ts, l2r ** 2, label='l2r^2')
# plt.plot(ts, r2l ** 2, label='r2l^2')
# plt.plot(ts, r2r ** 2, label='r2r^2')
# plt.plot(ts, after_l ** 2, label='after_l^2')
# plt.plot(ts, after_r ** 2, label='after_r^2')

# plt.plot(ts, P, label='P')
# plt.plot(ts, y_fit, 'r-', label=f"fit: A={A_fit}, B={B_fit}, C={C_fit}, D={D_fit}")
# plt.plot(ts, np.arcsin(l2l / np.sqrt(2)) * 2 / np.pi, 'g-', label='arcsin')
plt.xlabel('p')
plt.ylabel('v')
plt.minorticks_on()
plt.grid(which='both')
plt.legend()
plt.show()
