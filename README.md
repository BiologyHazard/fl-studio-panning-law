# FL Studio Panning Law 实验研究

正式报告：[FL Studio Panning Law](REPORT.md)。

本项目研究 Mixer 与 Audio Clip Channel panning 在 Circular / Triangular 设置下的双声道变换。实验使用的软件版本为 FL Studio 20.8.3.2304；每种条件使用同一份左声道单位直流输入，进行 8 秒的全范围声像扫描。

## 目录

| 路径                                           | 用途                                   |
| ---------------------------------------------- | -------------------------------------- |
| `REPORT.md`                                    | 正式报告                               |
| `fl-studio-projects/`                          | FL Studio 实验工程                     |
| `input-wav-file/`                              | 左声道单位直流输入 WAV                 |
| `output-wav-files/`                            | 4 种条件的原始输出 WAV                 |
| `images/screenshots/`                          | 软件截图                               |
| `images/figures/`                              | 程序生成的分析图表                     |
| `results/statistics.json`                      | 全精度残差、输出极值、原始文件 SHA-256 |
| `scripts/`                                     | 数据分析、单图绘制及生成输入文件的代码 |
| `pyproject.toml`、`uv.lock`、`.python-version` | Python 环境与锁定依赖                  |

原始 WAV、FLP 和截图属于实验资料。`images/figures/` 与 `results/statistics.json` 是可由脚本重新生成的研究产物；保留它们便于直接阅读报告、复核数字及核对数据版本。

## 完整复现

在项目根目录运行：

```sh
uv sync
uv run python scripts/build.py
```

该命令读取原始 WAV，重算 `results/statistics.json`，并生成 `images/figures/` 下全部图表。

## 分析与单图入口

| 脚本                              | 功能                                       |
| --------------------------------- | ------------------------------------------ |
| `scripts/build.py`                | 统一入口，运行统计与全部绘图               |
| `scripts/analyze.py`              | 统计、输出关系检验、峰值解析量及文件哈希   |
| `scripts/common.py`               | WAV 读取、声像坐标、矩阵模型与公共绘图样式 |
| `scripts/fig_response.py`         | 报告图 10：实测响应与公式对比              |
| `scripts/fig_matrix.py`           | 报告图 11：四个矩阵系数                    |
| `scripts/fig_residual.py`         | 报告图 12：全样本残差包络及局部波形        |
| `scripts/fig_identity.py`         | 报告图 13：消去声像参数的输出关系          |
| `scripts/fig_power.py`            | 报告图 14：两种输入条件下的功率关系        |
| `scripts/fig_peak.py`             | 报告图 15：Mixer Circular 的内部幅度峰值   |
| `scripts/make_left_channel_dc.py` | 生成单位左声道直流输入音频文件             |

例如：

```sh
uv run python scripts/analyze.py
uv run python scripts/fig_response.py
```

## 重新生成输入

```powershell
uv run python scripts/make_left_channel_dc.py
```

输出为 48 kHz、8 s、双声道 float32 WAV，左声道为 1，右声道为 0。此命令会写入默认输入路径；分析和绘图通常只需使用现存输入文件。

## 官方参考

- [Project General Settings — Panning law](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/songsettings_settings.htm#Panning_Law)
- [Mixer — Panning](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/mixer.htm)
