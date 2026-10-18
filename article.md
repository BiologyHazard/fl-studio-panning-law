# FL Studio 混音台轨道 Pan Rule 测量报告

## 摘要

本文通过实验反解 FL Studio 混音台轨道 Pan 旋钮对立体声信号的实际增益规律。被测版本为 FL Studio 20.8.3.2304，项目 Panning law 设为 Circular。

结论：FL 的立体声 pan 是一个分段 $2\times2$ 增益矩阵。$p=0$ 时为单位矩阵；$p<0$ 时右声道按 $B$ 线性淡出，左声道先按随 pan 变化的权重混合左右输入，再整体乘增益 $A$；$p>0$ 为镜像。硬声像输入（$L=1,R=0$）的左输出在 $p\approx-0.2553$ 处出现 $+0.4229\,\text{dB}$ 的峰值。

官方文档（手册 Project General Settings、Mixer Explained、Mixing Advice，以及更新日志与 UI 字符串表）给出的定量约定只有「中心与极值相差 3 dB」和「100% pan 为左右声道单声道和」两条，未给出闭式公式（详见第 2 节）。

验证结果：反解实际 pan 位置后，$L'$ 通道残差最大 $7.44\times10^{-8}$，达到 float32 精度；右半区一个不含自由参数的恒等式在 192000 帧上最大误差 $8.41\times10^{-6}$；Circular 模型在 Triangular 对照数据上残差增大数千倍，形状不匹配。剩余误差（峰峰值 $1.2\times10^{-4}$）可归因于自动化时间轴的非线性，与增益规则无关。

## 1. 研究范围与动机

对单声道输入，Pan 旋钮表现为标准等功率法则：中心 $0\,\text{dB}$，两端各 $+3.01\,\text{dB}$。但对立体声输入，其行为决定以下量：

- 素材 pan 到极端时是否退化为单声道和，反相成分是否抵消；
- 自动化扫过特定位置时是否产生电平突起；
- 总线预留余量是否足以覆盖增益变化；
- 感知到的宽度与定位来自素材本身还是 pan law。

FL 官方手册对 pan law 的描述仅涉及 Circular 与 Triangular 两个名称，以及「Circular 为等功率，最多增加 3 dB」「100% pan 为左右声道单声道和」等端点与单声道性质，未给出中间区段的函数形式（原文见第 2 节）。同时 FL 为闭源软件，静态分析未获结果（详见第 8 节）。因此本文采用黑箱测量方法：输入已知信号，线性扫描 pan，逐样本读取输出并反解增益。

本文仅讨论混音台轨道的 Pan；通道机架（Sampler）与插件内部的 pan 不在范围内。

## 2. 官方文档记载

### 2.1 文档来源

| 文档                                               | 位置                               | 本文引用内容                                                                      |
| -------------------------------------------------- | ---------------------------------- | --------------------------------------------------------------------------------- |
| FL Studio Online Manual — Project General Settings | `songsettings_settings.htm`        | Panning law 的定义、两个选项、补偿曲线图                                          |
| FL Studio Online Manual — Mixer Explained          | `mixer.htm`                        | 混音台轨道 Pan 的作用方式                                                         |
| FL Studio Online Manual — Mixing Advice            | `mixer_levelsandmixing.htm`        | Sampler Channel / Audio Clip 的 −3 dB 说明                                        |
| FL Studio Online Manual — Fruity Stereo Shaper     | `plugins/Fruity Stereo Shaper.htm` | 不做交叉混合的替代声像方案                                                        |
| FL Studio 更新日志                                 | What's New（`WhatsNew.rtf`）       | Triangular 修改记录、pyramid panning 加入记录                                     |
| 引擎字符串表与中文语言包                           | `FLEngine_x64.dll`、`zh_CN.mo`     | `PanLawLabel`、`PanLawSelect`、`Circular`、`Triangular`；`Panning law → 声像法则` |

对应 20.8 的版本化镜像为 `support.image-line.com/redirect/FLStudio20Help/html/` 下的同名页面。本文引用的 Panning law 段落与 Mixer 的 Pan 条目，在 20.8 镜像与当前在线手册中文字一致；FL 版本间若出现差异，以被测版本的镜像为准。

### 2.2 Project General Settings — Panning law

原文（节选）：

> Panning law - The purpose is to maintain a constant apparent volume as a sound is panned. For example, if a sound is panned hard left or right, only one speaker will be active. This will sound quieter than the center position where both speakers are active, unless steps are taken to counteract this effect. Circular panning maintains a constant apparent volume by progressively lowering the combined volume of the L+R channels by -3 dB as the pan passes dead center. Triangular panning does not apply this compensation, so the apparent loudness will increase as the sound passes the center position. … Circular - Level compensation is applied when panning (orange). Level drops 3 dB at center pan. Triangular - No level compensation is used as a function of pan position (green). The overall level is 3 dB lower, across the pan range, compared to the extreme pan positions for circular mode.

同页关于 Audio Clip 电平读数：

> Also note that for audio clips, at default Channel Sampler settings the level readout will be identical to the recorded level, so when using Circular panning, a maximum of 3 dB can be added. It still works exactly the same way (extreme pan position and center have a 3 dB difference), but in this case volume is being added at extremes instead of subtracted at the center position.

同页关于工程共享与分轨：

> Changing the panning law after a project is mixed will change relative volumes and apparent stereo locations … If you are sharing track stems (audio from individual mixer tracks) then the panning law used by the project is 'rendered' into each stereo track, so is not a factor to worry about.

归纳：

1. 该设置以「感知响度恒定」为目标，不描述波形层面的增益结构。
2. Circular 的补偿量为 3 dB：中心相对极值低 3 dB（或在 Audio Clip 情形下极值相对中心高 3 dB）。
3. Triangular 不做补偿，且手册以「整体比 Circular 的极值低 3 dB」的相对方式描述。
4. 手册给出的定量约束只有「中心与极值相差 3 dB」这一条，未给出中间位置的函数形式。

![官方手册中的 Panning law 补偿曲线](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/img_shot/songsettings_panning.png)

图：纵轴 Compensation，横轴 Left–Center–Right。Circular（橙）在两端为 0 dB、中心为 −3 dB；Triangular（绿）在全范围为 −3 dB。手册未给出任一曲线的解析式。

### 2.3 Mixer Explained — 轨道 Pan

原文：

> Panning - Pan controls the position of the sound in the stereo field (left to right) and is often overlooked as a control for creating an interesting and spacious mix. The pan works by mixing one side of the stereo track into the other, so a 100% pan is the mono-sum of the Left and Right channels. If you would like to pan using independent Left & Right level changes with no cross channel mixing use Fruity Stereo Shaper. By default a 'Circular Panning Law' is used.

要点：

- 手册明确 pan 的行为是「把立体声轨道的一侧混入另一侧」，与本文测得的交叉混合结构定性一致，但未给出混合权重。
- 「100% pan 即 L+R 的单声道和」与实测 $R'=(L+R)/\sqrt2$ 相差常数因子 $1/\sqrt2$，不改变左右关系与反相抵消行为。
- 手册将 Fruity Stereo Shaper 列为不做交叉混合的替代方案，反证轨道 Pan 属于交叉混合一类。

### 2.4 Mixing Advice — Sampler Channel 与 Audio Clip

原文：

> Panning Law - While both Sampler Channels and Audio Clips adhere to the default 'Circular Panning' law. This reduces sample gain by -3 dB when panned to the center, to maintain apparent loudness compared to hard panning and so can be another source of unexpected level changes compared to careful inspection of the originally recorded levels.

要点：手册把 −3 dB 表述为「中心处对采样增益的衰减」，即电平差体现于中心而非极值。该表述与实测「中心为单位增益、单声道极值为 $\sqrt2$」等价。

### 2.5 Fruity Stereo Shaper

原文：

> The Stereo Shaper is a multi-purpose stereo shaping tool, it can: Provide control of individual Left/Right Mixer channels & how they're inter-mixed. Affect panning/balance (with or without Left/Right channel inter-mixing) …

要点：官方对「含交叉混合」与「不含交叉混合」两类声像实现分别提供入口，佐证混音台轨道 Pan 采用前者。

### 2.6 变更记录与当前可选项

- 更新日志（2.5.0，2000-04-13）：`Added support for pyramid panning shape (circular is good but can generate clipping).`
- 更新日志：`Updated triangle panning law not to sound louder (uncompatible).` 该条表明 Triangular 的绝对电平曾在校正中被修改，不同版本的 Triangular 数据不可直接比较。
- 当前引擎字符串表中与本项相关的字符串仅有 `Panning law`、`PanLawLabel`、`PanLawSelect`、`Circular`、`Triangular`；中文语言包对应条目为 `Panning law → 声像法则`。即当前版本暴露两个选项，pyramid 未出现在字符串表中。

### 2.7 文档记载与实测的对应

| 文档表述                                                      | 实测 / 模型                                                                                 | 判定                                   |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | -------------------------------------- |
| Circular 中心相对极值 −3 dB                                   | 单声道输入：中心 $\lvert L'\rvert=\lvert R'\rvert=1$，极值 $\sqrt2$，相差 $3.01\,\text{dB}$ | 一致                                   |
| Circular 下「a maximum of 3 dB can be added」（相对中心）     | 单声道输入极值 $+3.01\,\text{dB}$                                                           | 一致                                   |
| 「a 100% pan is the mono-sum of the Left and Right channels」 | $p=+1$：$L'=0$，$R'=(L+R)/\sqrt2$                                                           | 一致（相差常数因子 $1/\sqrt2$）        |
| 「mixing one side of the stereo track into the other」        | 近端增益 $=\big((1+B)L+(1-B)R\big)/2$，权重随 pan 变化                                      | 定性一致；定量为本文补充               |
| Triangular「no level compensation」                           | 实测第一列呈分段线性（$p\le0$：$L'=1+p/2$；$p\ge0$：$L'=1-p$，$R'=p/2$），无 $>1$ 增益      | 形态可区分；绝对增益不能由手册文字推出 |
| 「中心与极值相差 3 dB」为唯一定量约束                         | 模型另给出中间区段函数、交叉项与 $>1$ 的峰值                                                | 超出文档                               |

### 2.8 文档未覆盖的内容

1. 未给出 $g_{LL},g_{LR},g_{RL},g_{RR}$ 的任何闭式表达，仅有端点处的 3 dB 约束。
2. 未区分单声道输入与立体声输入的规则差异；「mixing one side into the other」只说明定性方向。
3. 未说明 $p=0$ 处的分支结构，也未给出交叉混合权重 $(1\pm B)/2$、$(1\pm A)/2$ 的形式。
4. 未提及不对称立体声输入（$L=1,R=0$）时增益可超过 1（峰值 $+0.42\,\text{dB}$，$p\approx-0.2553$）；该现象在 3 dB 端点约束内不可见。
5. 未给出 Triangular 的绝对电平定义，故无法由文档推断 $L=1,R=0$ 时的第一列数值。

## 3. 测量方法

### 3.1 测试信号

测试素材为 32-bit float 立体声 WAV，左声道恒为 $1.0$（$0\,\text{dB}$ 直流），右声道恒为 $0$。

选择依据：

- **使用直流**：pan 在每一采样点上等效为静态增益，输出即等于增益，无需包络估计、相位对齐或频率响应校正。
- **使用 $L=1,R=0$**：输出直接暴露增益矩阵第一列，即 $L'=g_{LL}$、$R'=g_{RL}$。再由左右对称性

$$
M(p)=J\,M(-p)\,J,\qquad J=\begin{pmatrix}0&1\\1&0\end{pmatrix},
$$

可得 $g_{LR}(p)=g_{RL}(-p)$、$g_{RR}(p)=g_{LL}(-p)$，一次扫描即可还原四个元素。

- **使用 float32**：中间结果存在大于 1 的样本（峰值 1.0499），定点格式会削波，float 渲染可原样保留。

![左声道直流素材](<images/Left Channel DC.png>)

### 3.2 采集流程

素材置于一条混音台轨道，通过 `Link to controller...` 将轨道 Pan 绑定到自动化控制器，使其在 8 秒内从 $-100\%$ 线性移到 $+100\%$。项目 Panning law 设为 Circular，48 kHz 渲染，长度 8 秒，共 384000 帧。第 $i$ 帧对应名义 pan

$$
p_i=\frac{2i}{N-1}-1,\qquad N=384000.
$$

![FL Studio 工程](<images/FL Studio.png>)

### 3.3 对照与独立数据

- **负对照**：同一素材、同一自动化曲线，仅将 Panning law 改为 Triangular 后重新渲染，用于检验模型是否具备区分能力。
- **独立验证**：另一份单声道正弦渲染（不同素材、独立导出），按 10 ms 窗口取包络，用于验证等功率性质。

## 4. 结果：增益模型

### 4.1 参数化

记 $p\in[-1,1]$ 为 pan 位置，定义

$$
\theta=\frac{(p+1)\pi}{4},\qquad A=\sqrt{2}\cos\theta,\qquad B=\sqrt{2}\sin\theta .
$$

对应关系：$p=-1\Rightarrow\theta=0$，$p=0\Rightarrow\theta=\pi/4$，$p=+1\Rightarrow\theta=\pi/2$。且 $A^2+B^2=2$，故中心 $A=B=1$，极左 $A=\sqrt 2,\ B=0$，极右 $A=0,\ B=\sqrt 2$。

### 4.2 分段增益

对立体声输入 $(L,R)$，输出为

$$
\begin{aligned}
p\le 0:&\quad L'=A\left[\frac{1+B}{2}L+\frac{1-B}{2}R\right],\qquad R'=BR,\\[4pt]
p\ge 0:&\quad L'=AL,\qquad R'=B\left[\frac{1+A}{2}R+\frac{1-A}{2}L\right].
\end{aligned}
$$

即 $[L',R']^{\mathrm T}=M(p)[L,R]^{\mathrm T}$，其中

$$
M(p)=
\begin{cases}
\begin{pmatrix}
\dfrac{A(1+B)}{2} & \dfrac{A(1-B)}{2}\\[8pt]
0 & B
\end{pmatrix}, & p\le 0,\\[16pt]
\begin{pmatrix}
A & 0\\[8pt]
\dfrac{B(1-A)}{2} & \dfrac{B(1+A)}{2}
\end{pmatrix}, & p\ge 0.
\end{cases}
$$

两支在 $p=0$ 处均退化为单位矩阵，因此中心为原样直通。

### 4.3 对称形式

令 $\varphi=p\pi/4$，则 $A=\cos\varphi-\sin\varphi$、$B=\cos\varphi+\sin\varphi$，记 $\cos2\varphi=\cos^2\varphi-\sin^2\varphi$，四个增益元素可写为

$$
\begin{aligned}
p\le 0:&\quad g_{LL}=\frac{A+\cos2\varphi}{2},\quad g_{LR}=\frac{A-\cos2\varphi}{2},\quad g_{RL}=0,\quad g_{RR}=B,\\[4pt]
p\ge 0:&\quad g_{LL}=A,\quad g_{LR}=0,\quad g_{RL}=\frac{B-\cos2\varphi}{2},\quad g_{RR}=\frac{B+\cos2\varphi}{2}.
\end{aligned}
$$

### 4.4 特例

- **单声道输入** $L=R=s$：两支均退化为 $(L',R')=\sqrt{2}s(\cos\theta,\sin\theta)$，即 $L'^2+R'^2=2s^2$ 与 pan 无关，端点为 $\sqrt 2 s$（$+3.01\,\text{dB}$）。此即手册中 Circular 的单声道描述。
- **100% 极右** $p=+1$：$L'=0$，$R'=(L+R)/\sqrt 2$；极左对称。此即手册所述「100% pan 为单声道和」。
- **中心** $p=0$：$L'=L$，$R'=R$；实测左声道为精确的 $1.0000000$。
- **硬声像输入** $L=1,R=0$：增益在 $p\in[-0.519251,0]$ 内大于 1，最大值位于 $p=-0.2553184$，理论值 $1.0498988$（$+0.4229\,\text{dB}$）；实测最大 $1.04989886$，偏差 $7.4\times 10^{-8}$。

### 4.5 峰值的解析解

$p\le0$ 支在 $L=1,R=0$ 时为

$$
L'(\theta)=\frac{A(1+B)}{2}=\frac{\sqrt 2\cos\theta+\sin2\theta}{2}.
$$

令 $\mathrm dL'/\mathrm d\theta=0$：

$$
2\cos2\theta=\sqrt 2\sin\theta
\;\Longrightarrow\;
4\sin^2\theta+\sqrt 2\sin\theta-2=0
\;\Longrightarrow\;
\sin\theta=\frac{\sqrt{34}-\sqrt 2}{8}.
$$

代回得

$$
L'_{\max}=\frac{\sqrt{142+34\sqrt{17}}}{16}=1.0498987884\ldots
$$

对应 $\theta=33.5107^\circ$，即 $p=-0.2553184$。

该结果排除了「两声道各自按等功率衰减」的 balance 模型：若为纯 balance，$L=1,R=0$ 时左输出上界为 1。实测达到 1.0499，说明 pan 内部先进行交叉混合，再施加增益。官方 Circular / Triangular 描述均未包含这一层。

### 4.6 数值表

$M(p)$ 的四个元素：

| $p$       | $g_{LL}$ | $g_{LR}$ | $g_{RL}$ | $g_{RR}$ |
| --------- | -------- | -------- | -------- | -------- |
| -1        | 0.707107 | 0.707107 | 0        | 0        |
| -0.5      | 1.006835 | 0.299728 | 0        | 0.541196 |
| -0.255318 | 1.049899 | 0.129248 | 0        | 0.780776 |
| 0         | 1        | 0        | 0        | 1        |
| +0.5      | 0.541196 | 0        | 0.299728 | 1.006835 |
| +1        | 0        | 0        | 0.707107 | 0.707107 |

$g_{LL}$ 在 $p\in[-1,0]$ 上由 $0.707$ 升至 $1.05$ 后回落至 $1$；$g_{RR}$ 在 $p\in[0,+1]$ 上形态对称。峰值出现在 pan 的目标一侧。

![Circular Panning Law 渲染结果](<images/Circular Panning Law.png>)

图中上为左声道、下为右声道。左声道由 $0.707$ 上升，约 3 秒处越过 $0\,\text{dB}$ 并达到峰值后回落；右声道在 $p<0$ 区间恒为零，至 4 秒（$p=0$）方开始变化。两条曲线分别对应 $g_{LL}$ 与 $g_{RL}$。

## 5. 模型结构

以 $p\le0$ 支为例：

$$
L'=A\left[\frac{1+B}{2}L+\frac{1-B}{2}R\right].
$$

括号内为权重和为 1 的混合：$B=1$ 时权重为 $(1,0)$，左输出仅取左声道；$B$ 减小，右声道混入比例上升；$B=0$ 时权重为 $(1/2,1/2)$。外部增益 $A$ 由 $1$ 升至 $\sqrt2$。两者反向变化，乘积在区间内部出现极大值，即前述 $0.42\,\text{dB}$ 突起。另一侧 $R'=BR$ 仅为淡出。

因此该 pan law 的结构是：**将远端信号按随 pan 变化的权重混入近端，再对近端整体施加增益**，而非对两声道分别施加独立系数。100% 时混合权重为 50/50，近端输出为 $(L+R)/\sqrt2$，远端为 0。

该结构同时解释单声道退化为等功率：两支括号内权重和均为 1，故 $L=R=s$ 时括号内等于 $s$，仅余 $(A,B)$。

## 6. 验证

### 6.1 名义 pan 的前向残差

直接以名义线性斜坡代入模型：

| 通道 | 最大误差            | rms                 |
| ---- | ------------------- | ------------------- |
| $L'$ | $6.46\times10^{-5}$ | $2.39\times10^{-5}$ |
| $R'$ | $5.38\times10^{-5}$ | $1.55\times10^{-5}$ |

该量级高于 float32 精度。原因在于自动化时间轴并非数学上严格的线性斜坡，每帧实际 pan 与名义值偏差约 $1\times10^{-4}$（见 6.5）。

### 6.2 反解实际 $\theta$

由实测 $L'$ 反解每帧的实际 $\theta$ 后重算：

| 通道 | 最大误差            | rms                 |
| ---- | ------------------- | ------------------- |
| $L'$ | $7.44\times10^{-8}$ | $1.90\times10^{-9}$ |
| $R'$ | $8.41\times10^{-6}$ | $1.35\times10^{-6}$ |

$7.44\times10^{-8}$ 约为 $1.0$ 附近 float32 的一个 ULP（$2^{-24}\approx6\times10^{-8}$）。即在给定实际 pan 位置的条件下，模型与渲染结果在 float32 精度内一致；5.1 中的 $6.5\times10^{-5}$ 全部来自名义 pan 与实际 pan 的偏差。

需注意，峰值附近 $\mathrm dL'/\mathrm d\theta=0$，由 $L'$ 反解 $\theta$ 为病态，float32 舍入会被放大。故反解仅用于规则验证；衡量自动化时间轴抖动须使用前向残差。

本节验证的是矩阵第一列（$L=1,R=0$ 直接测得）。$g_{LR}$ 与 $g_{RR}$ 由左右对称性导出，属推论，见第 8 节。

### 6.3 无自由参数的恒等式

右半区 $L'=A$，由 $A^2+B^2=2$ 得 $B=\sqrt{2-L'^2}$，代入 $R'=B(1-A)/2$：

$$
R'=\frac{(1-L')\sqrt{2-L'^2}}{2}.
$$

右侧仅含实测 $L'$，无拟合常数。192000 帧上最大误差 $8.41\times10^{-6}$（相对峰值 $0.707$ 约 $1.2\times10^{-5}$）。若模型形状有误（例如缺少 $(1-A)/2$ 因子，或 $B\neq\sqrt{2-L'^2}$），该式将立即失配。

### 6.4 负对照：Triangular

同法应用于 Triangular 渲染：

| 量                    | Triangular 实测 | Circular 模型预测 |
| --------------------- | --------------- | ----------------- |
| $L'_{\max}/R'_{\max}$ | 2.000007        | 1.484781          |
| $L$ 通道残差 rms      | —               | 0.1549            |
| $R$ 通道残差 rms      | —               | 0.0686            |
| $L$ 通道最大残差      | —               | 0.2670            |

残差较主实验增大约三个数量级，峰值比不符，属形状级别的失配，而非参数拟合偏差。

![Triangular Panning Law 渲染结果](<images/Triangular Panning Law.png>)

Triangular 下左声道在中点达到 $0\,\text{dB}$ 后线性折返，右声道自中点线性上升，与 Circular 的圆顶曲线形态不同。

作为旁证，Triangular 第一列实测为

$$
\begin{aligned}
p\le0:&\quad L'=1+\frac{p}{2},\qquad R'=0,\\
p\ge0:&\quad L'=1-p,\qquad R'=\frac{p}{2},
\end{aligned}
$$

即近端保持满电平、远端线性淡出。二者为不同曲线，本方法具备区分能力。

### 6.5 自动化时间轴的残差

前向残差（实测值减模型在名义线性斜坡上的预测值）呈周期性起伏：

- 峰峰值 $1.213\times10^{-4}$（约 $-78.3\,\text{dB}$），rms $2.4\times10^{-5}$；
- 周期 750 帧，48 kHz 下为 15.625 ms；8 秒内共 512 个周期；
- 左右半区同相，仅与帧序号有关，与 pan 位置无关。

该分量属于 FL 自动化时间轴相对理想线性的偏差，可能源于 750 帧周期的控制率，不属于 pan 增益规则。

### 6.6 单声道等功率的独立验证

模型对单声道输入预测 $L'^2+R'^2=2s^2$ 与 pan 无关。独立渲染的单声道正弦按 10 ms 窗口取包络，共 779 个有效窗口：

| 量                                          | 值                        |
| ------------------------------------------- | ------------------------- |
| $\min(\mathrm{peak}_L^2+\mathrm{peak}_R^2)$ | 0.999999                  |
| $\max(\mathrm{peak}_L^2+\mathrm{peak}_R^2)$ | 1.001971                  |
| 均值                                        | 1.001219                  |
| 标准差                                      | $5.80\times10^{-4}$       |
| 相对离散度                                  | $1.97\times10^{-3}$       |
| 隐含源幅度 $s$                              | $0.707538\approx1/\sqrt2$ |
| 输出峰值 $\sqrt2 s$                         | 1.0000                    |

该数据与主实验来自两次独立渲染。

### 6.7 误差来源汇总

| 来源         | 量级                               | 说明                                   |
| ------------ | ---------------------------------- | -------------------------------------- |
| float32 舍入 | $1\times10^{-8}\sim1\times10^{-6}$ | $1.0$ 附近一个 ULP 约 $6\times10^{-8}$ |
| $R'$ 重构    | $8.4\times10^{-6}$                 | 由 $L'$ 推 $R'$ 的误差放大             |
| 自动化时间轴 | $1.2\times10^{-4}$ ptp             | 主残差，$-78\,\text{dB}$，750 帧周期   |
| 模型形状误差 | $<1\times10^{-7}$                  | 反解实际 $\theta$ 后仅余舍入           |

误差均已逐项归因，且无一项指向增益公式本身。

## 7. 对混音的影响

1. **单声道素材**：与常规等功率法则一致，中心 $0\,\text{dB}$，两端 $+3.01\,\text{dB}$。
2. **立体声素材**：并非 balance，而是交叉混合加增益。远端信号会混入近端；100% 时近端为 $(L+R)/\sqrt2$ 的单声道和。含反相成分的素材硬 pan 后可能部分抵消、听感变薄，单声道兼容性检查时应予考虑。
3. **$0.42\,\text{dB}$ 突起**：在两种情形下有实际影响。素材接近 $0\,\text{dBFS}$ 且自动化扫过 $p\approx-0.26$ 时，可能多出 $0.42\,\text{dB}$；做增益分配时，最大值不在端点而在 $p\approx-0.26$。FL 内部为 float 不会立即削波，但导出至定点格式或经限幅器时该增益真实存在。
4. **立体声宽度**：该法则在端点将立体声折叠为单声道和。若需保持左右关系整体平移，应使用 Mid/Side、双 pan 或专用立体声定位插件，而非混音台轨道 Pan。
5. **通道机架与混音台 Pan 不同**：通道（Sampler）的 Pan 位于送插件之前，与混音台轨道 Pan 为两套独立控件。手册说明 Sampler Channel 与 Audio Clip 同样遵循 Circular 法则，但本文未测量通道 pan，故不对二者是否完全一致下结论，也不应以通道 pan 的数据验证本文公式。

## 8. 适用范围与局限

- 被测版本为 FL Studio 20.8.3.2304（`FLEngine_x64.dll`，2021-03-25），项目 Panning law = Circular。其他版本或设置不保证一致，需按本文方法重新测量。
- 公式由实验反解得到，未经源码确认。静态分析尝试结果：UI 字符串经本地化字符串池按 ID 取值；$1/\sqrt2$ 在 52 MB 镜像中精确匹配 0 次；未发现预计算增益表。代码级确认尚缺。
- 主实验仅使用 $L=1,R=0$ 单一输入，四个增益元素由左右对称性补全。对称性已写入模型，实测形状与之一致；如需严格验证，可追加 $L=0,R=1$ 与 $L=R=1$ 的交叉渲染。
- 本文讨论混音台轨道 Pan，不含通道机架与插件内部 pan。

## 9. 数据与复现

- 完整推导与证据表：[docs/结论_FL_Studio_Pan_Rule.md](<docs/结论_FL_Studio_Pan_Rule.md>)
- 主实验渲染：[Mixer Circular Panning.wav](<output-wav-files/Mixer Circular Panning.wav>)
- 负对照渲染：[Mixer Triangular Panning.wav](<output-wav-files/Mixer Triangular Panning.wav>)
- 输入素材：[Left Channel DC.wav](<input-wav-file/Left Channel DC.wav>)
- 绘图与计算脚本：[main.py](scripts/main.py)

官方文档：

- Project General Settings（Panning law 定义与补偿曲线）：<https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/songsettings_settings.htm>
- Mixer Explained（轨道 Pan 的作用方式）：<https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/mixer.htm>
- Mixing Advice（Panning Law 注记）：<https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/mixer_levelsandmixing.htm>
- Fruity Stereo Shaper（不做交叉混合的声像方案）：<https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/plugins/Fruity%20Stereo%20Shaper.htm>
- 20.8 版本手册镜像：`https://support.image-line.com/redirect/FLStudio20Help/html/<页面名>.htm`
- 手册补偿曲线原图：<https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/img_shot/songsettings_panning.png>

复现结果不一致时，优先核对：FL 版本、项目 Panning law 设置、轨道上是否存在其他增益或限幅处理。
