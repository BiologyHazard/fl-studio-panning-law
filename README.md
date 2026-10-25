# FL Studio Panning Law 实验研究

正式报告：[FL Studio Panning Law](REPORT.md)。

本项目研究 Mixer Master 与 Audio Clip Channel panning 在 Circular / Triangular 设置下的双声道变换。实验使用的软件版本为 FL Studio 20.8.3.2304；每种条件使用同一份左声道单位直流输入，进行 8 秒的全范围声像扫描。

代码仓库：[BiologyHazard/fl-studio-panning-law](https://github.com/BiologyHazard/fl-studio-panning-law)。

## 目录

| 路径                                           | 用途                                                           |
| ---------------------------------------------- | -------------------------------------------------------------- |
| `REPORT.md`                                    | 正式报告：官方文档摘录、实验设置、四种完整公式、数据验证与结论 |
| `fl-studio-projects/`                          | 四个 FL Studio 实验工程                                        |
| `input-wav-file/`                              | 左声道单位直流输入 WAV                                         |
| `output-wav-files/`                            | 四种条件的原始输出 WAV                                         |
| `images/*.png`                                 | 八张原始实验截图，均已嵌入报告                                 |
| `images/figures/`                              | 五张程序生成的分析图，每图包含 PNG 与 SVG                      |
| `results/statistics.json`                      | 全精度残差、输出极值、端点约定比较及原始文件 SHA-256           |
| `scripts/`                                     | 数据分析、单图绘制及输入生成代码                               |
| `pyproject.toml`、`uv.lock`、`.python-version` | Python 环境与锁定依赖                                          |

原始 WAV、FLP 和截图属于实验资料。`images/figures/` 与 `results/statistics.json` 是可由脚本重新生成的研究产物；保留它们便于直接阅读报告、复核数字及核对数据版本。`.venv/` 是本地 Python 环境，隐藏工具配置目录独立于研究资料。

## 完整复现

在项目根目录运行：

```powershell
uv sync
uv run python scripts/build.py
```

该命令读取原始 WAV，重算 `results/statistics.json`，并生成 `images/figures/` 下全部图件。各脚本按自身路径定位项目，亦可从其他工作目录以绝对路径调用。

## 分析与单图入口

| 脚本                              | 功能                                       |
| --------------------------------- | ------------------------------------------ |
| `scripts/build.py`                | 统一入口，运行统计与全部绘图               |
| `scripts/analyze.py`              | 统计、输出关系检验、峰值解析量及文件哈希   |
| `scripts/common.py`               | WAV 读取、声像坐标、矩阵模型与公共绘图样式 |
| `scripts/fig_response.py`         | 报告图 9：实测响应与公式对比               |
| `scripts/fig_matrix.py`           | 报告图 10：四个矩阵系数                    |
| `scripts/fig_residual.py`         | 报告图 11：全样本残差包络及局部波形        |
| `scripts/fig_identity.py`         | 报告图 12：消去声像参数的输出关系          |
| `scripts/fig_consequences.py`     | 报告图 13：功率关系与内部峰值              |
| `scripts/make_left_channel_dc.py` | 生成单位左声道直流输入材料                 |

例如：

```powershell
uv run python scripts/analyze.py
uv run python scripts/fig_response.py
```

图中的显示抽样只影响绘图，所有统计和残差包络均使用完整数据。`statistics.json` 中 `residual` 采用 `p[n] = -1 + 2n/N`，`endpoint_convention_residual` 采用 `p[n] = -1 + 2n/(N-1)`；两者的最大绝对残差和 RMS 均分别按左右声道保存。

## 重新生成输入

```powershell
uv run python scripts/make_left_channel_dc.py
```

输出为 48 kHz、8 s、双声道 float32 WAV，左声道为 1，右声道为 0。此命令会写入默认输入路径；分析和绘图通常只需使用现存输入文件。

## 官方参考

- [Project General Settings — Panning law](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/songsettings_settings.htm#Panning_Law)
- [Mixer — Panning](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/mixer.htm)
