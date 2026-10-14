# FL Studio Pan Rule

逆向 FL Studio 混音台（Mixer track）Pan 旋钮对**立体声**信号的规则。

被测版本：FL Studio 20.8.3.2304（`FLEngine_x64.dll`，未加壳 x64 PE）。
方法：把一个"左声道 DC 偏移 100%"的素材导入 FL，用自动化控制器把 Mixer 轨道的 Pan
从 −100% 线性推到 +100%（项目 Panning law = Circular），导出 32-bit float 渲染，
然后逐帧反解传递函数。

完整推导、验证数据与证据来源见 **[`docs/结论_FL_Studio_Pan_Rule.md`](docs/结论_FL_Studio_Pan_Rule.md)**。

## 结论

记 pan `p ∈ [-1, 1]`，`θ = (p + 1)·π/4`（极左 θ=0、中心 θ=π/4、极右 θ=π/2），

```
A = √2·cos θ
B = √2·sin θ
```

| | 左声道输出 | 右声道输出 |
|---|---|---|
| **p ≤ 0**（向左） | `L' = A·[ ((1+B)/2)·L + ((1−B)/2)·R ]` | `R' = B·R` |
| **p ≥ 0**（向右） | `L' = A·L` | `R' = B·[ ((1+A)/2)·R + ((1−A)/2)·L ]` |

写成矩阵，`[L', R']ᵀ = M(p)·[L, R]ᵀ`：

```
p ≤ 0 :  M = [[ A(1+B)/2 , A(1−B)/2 ] ,  [ 0 , B ]]
p ≥ 0 :  M = [[ A , 0 ] ,  [ B(1−A)/2 , B(1+A)/2 ]]
```

`p = 0` 时两支都退化为单位矩阵，即中心是原样直通。

### 性质

- **单声道输入**（`L = R = s`）退化为 `(L', R') = s·√2·(cos θ, sin θ)`：严格等功率，
  硬极点 **+3.01 dB**。这正是官方手册描述的 Circular 形态。
- **100% 极端 pan**：panned 声道得到 `(L+R)/√2`，另一声道为 0 —— 官方手册所说的
  "a 100% pan is the mono-sum of the Left and Right channels"。
- **硬声像输入会被抬到 1 以上**：`L=1, R=0` 时左输出在
  `sin θ = (√34 − √2)/8`（约 `p = −0.255318408`）处取极大值
  **1.049898788409（+0.4229 dB）**；增益 >1 的区间是 `p ∈ [−0.519251, 0]`。
  这是官方文档没有、且与文档中两条法则（Circular / Triangular）都无法产生的东西。

## 使用

```bash
uv sync                       # 建环境
uv run fl-studio-pan-rule verify     # 重新跑全部验证（读 data 里的渲染）
uv run fl-studio-pan-rule table      # 打印增益表
uv run fl-studio-pan-rule eval 0.5   # 求某个 pan 位置的输出与矩阵
```

作为库：

```python
from fl_studio_pan_rule import process, matrix, PEAK_GAIN

left_out, right_out = process(0.5, 1.0, 0.0)  # -> (0.5411961, 0.2997281)
```

`verify` 会跑四项独立检查，任一不成立都会 FAIL：

| 检查 | 内容 | 实测结果 |
|---|---|---|
| `rule_fit` | 规则复现 `test_pan_2024-09-19.wav` | 用真实 θ 时 L 最大误差 **7.4e-08**（相对 1.0e-07）；另有**无自由参数**的闭合式检验 `R = (1−L)·√(2−L²)/2`，R 最大误差 8.4e-06 |
| `mono_power` | 单声道输入保持等功率 | `L'²+R'²` 恒定，相对离散 1.97e-03（16-bit 量化量级） |
| `rejection` | 另一条 pan 法则的渲染必须被否决 | `test_dc.wav` 残差 rms 0.0791，峰比 1.414388 落在"无驼峰"预测上 → **REJECTED** |
| `ripple` | 量化自动化时间轴自身的偏差 | 前向残差 ptp 1.21e-04（−78.3 dB），主周期 750 帧 = 15.625 ms |

`ripple` 那一项不是规则的一部分：它是 FL 自动化时间轴相对"理想线性"的偏差，
也是此前用正弦/多项式拟合永远拿不到完美结论的原因。

## 目录结构

```
docs/结论_FL_Studio_Pan_Rule.md   推导、验证、证据来源矩阵
src/fl_studio_pan_rule/
    rule.py         ★ 规则本身（纯函数，无副作用）
    analysis.py     四项验证：rule_fit / mono_power / rejection / ripple
    wav.py          零依赖 RIFF/WAVE 读取（按 float32 原样解码）
    cli.py          verify / table / eval
references/         官方手册摘录、论坛帖、引擎 UI 字符串、中文语言包条目
tools/
    scan_engine_for_pan_law.py   在 FLEngine_x64.dll 里找 pan 代码（未成功，见文件头）
2023-06-21测试/      早期素材与渲染（含 16-bit 版本、正弦与 DC 素材、FLP）
2024-09-19测试/      2024 年的素材、渲染、FLP，以及当年的拟合尝试 拟合.py
```

## 证据强度（请按此理解结论）

- **实验**：规则的闭式形式（曲线中段、驼峰、立体声交叉项）目前的全部证据来源。
- **官方文档**：能交叉验证的只有**端点行为**（中心直通、极值=单声道和、单声道 +3 dB）和
  "通道机架 Pan ≠ 混音台 Pan"这一点；文档从未给出任何闭式，且其描述的 Circular/Triangular
  都不可能产生 >1 的中间增益。
- **论坛**：查了 19 个 Image-Line 论坛帖，没有任何公式可供核对。
- **源代码**：**没有取得**。本机 Ghidra provider 未配置（缺 `GHIDRA_INSTALL_DIR`，只有 JDK 17
  而要求 JDK 21+），自建 capstone/pefile 扫描也 0 命中（FL 的 UI 字符串走本地化字符串池，
  代码按 ID 取值，不引用地址；`1/√2` 在整个 52 MB 镜像里精确出现 0 次，也没有预计算增益表）。
  这是唯一的缺口。

要补上源代码这一层，需要装 Ghidra + JDK 21（或 IDA / radare2）：

```bash
uv sync --extra reverse-engineering
uv run python tools/scan_engine_for_pan_law.py --dll "C:\Program Files\Image-Line\FL Studio 20\FLEngine_x64.dll"
```

## 数据说明

`2023-06-21测试/` 与 `2024-09-19测试/` 是原始实验数据，保持原样未动。其中

- `test_pan_2024-09-19.wav` —— 本结论的主证据（32-bit float，输入 L=1/R=0，8 s 线性扫描）
- `test_sinewave.wav` —— 单声道等功率的独立佐证
- `test_dc.wav` —— 另一条 pan 法则的渲染，充当负对照
- `output.txt` / `P.txt` —— 2024 年拟合尝试的原始输出（约 14 MB 各一份），
  `拟合.py` 依赖它们，故保留
