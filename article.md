# FL Studio 立体声 Pan 规则测量报告

## 摘要

本文通过黑箱测量反解 FL Studio 的 Pan 旋钮对**立体声**信号的增益规律。被测版本为 FL Studio 20.8.3.2304，测了 Pan 的四种组合：Circular / Triangular 两个 Pan law，分别在**混音台轨道**与**通道**上各渲染一次。

结论可以写成两层：**Pan law** 只决定单声道增益 $(g_L,g_R)$，**实现**决定立体声如何交叉混合。混音台轨道 Pan 把远端声道按随 pan 变化的权重混入近端，$100\%$ 时折叠为单声道和；通道（Audio Clip）Pan 是纯 balance，左右各自乘增益，不交叉混合。四种组合在 $p=0$ 处都退化为单位矩阵。

四种组合的形态差异明显：

- 只有 **Mixer × Circular** 会在中间出现大于 $1$ 的增益。$L=1,R=0$ 时左输出在 $p=-0.2553184$ 处取极大值 $\dfrac{\sqrt{142+34\sqrt{17}}}{16}=1.0498988$（$+0.4229\,\text{dB}$），且增益 $>1$ 的区间为 $p\in[-0.519251,0]$。
- **Channel × Circular** 的最大增益是 $\sqrt2$（$+3.01\,\text{dB}$），出现在极值；曲线单调，无突起。
- 两种 **Triangular** 的最大增益都是 $1$，远端起于 $p=0$ 线性淡出。

官方文档（Project General Settings、Mixer Explained、Channel Rack、Mixing Advice，以及更新日志与 UI 字符串表）给出的定量约定只有"中心与极值相差 $3\,\text{dB}$"这一条，未给出任何闭式；也**没有说明混音台 Pan 与通道 Pan 在结构上的差别**——手册的「$100\%$ pan 是左右声道单声道和」只对混音台成立。

验证：反解实际 pan 位置后，Mixer×Circular 的 $L'$ 残差最大 $7.44\times10^{-8}$，达到 float32 精度；四组各有一个不含自由参数的恒等式，最大误差在 $10^{-6}$ 量级。剩余误差（峰峰值 $1.2\times10^{-4}$）可归因于自动化时间轴的非线性，与增益规则无关。

## 1. 研究范围与动机

对单声道输入，Pan 旋钮表现为标准等功率法则：中心 $0\,\text{dB}$，两端各 $+3.01\,\text{dB}$。但对立体声输入，其行为决定以下量：

- 素材 pan 到极端时是否退化为单声道和，反相成分是否抵消；
- 自动化扫过特定位置时是否产生电平突起；
- 总线预留余量是否足以覆盖增益变化；
- 感知到的宽度与定位来自素材本身还是 pan law。

FL 官方手册对 pan law 的描述仅涉及 Circular 与 Triangular 两个名称，以及端点与单声道性质，未给出中间区段的函数形式（原文见第 2 节）。同时 FL 为闭源软件，静态分析未获结果（详见第 8 节）。因此本文采用黑箱测量方法：输入已知信号，线性扫描 pan，逐样本读取输出并反解增益。

被测的四条通路是同一个旋钮语义的四种落地方式：项目设置里的 **Panning law** 两档，以及 **混音台轨道 Pan** 与 **通道（Channel Rack / Audio Clip）Pan** 两个控件。后两者是独立控件，自动化目标分别是 `Master - Panning` 与 `Left Channel DC - Channel panning`。

## 2. 官方文档记载

### 2.1 文档来源

| 文档                                               | 位置                               | 本文引用内容                                                                      |
| -------------------------------------------------- | ---------------------------------- | --------------------------------------------------------------------------------- |
| FL Studio Online Manual — Project General Settings | `songsettings_settings.htm`        | Panning law 的定义、两个选项、补偿曲线图                                          |
| FL Studio Online Manual — Mixer Explained          | `mixer.htm`                        | 混音台轨道 Pan 的作用方式                                                         |
| FL Studio Online Manual — Channel Rack             | `channelrack.htm`                  | Channel Panning 是送入插件的 pan 信息                                             |
| FL Studio Online Manual — Mixing Advice            | `mixer_levelsandmixing.htm`        | Sampler Channel / Audio Clip 的 $-3\,\text{dB}$ 说明                              |
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
2. Circular 的补偿量为 $3\,\text{dB}$：中心相对极值低 $3\,\text{dB}$（或在 Audio Clip 情形下极值相对中心高 $3\,\text{dB}$）。
3. Triangular 不做补偿，且手册以「整体比 Circular 的极值低 $3\,\text{dB}$」的相对方式描述。
4. 手册给出的定量约束只有「中心与极值相差 $3\,\text{dB}$」这一条，未给出中间位置的函数形式。

![官方手册中的 Panning law 补偿曲线](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/img_shot/songsettings_panning.png)

图：纵轴 Compensation，横轴 Left–Center–Right。Circular（橙）在两端为 $0\,\text{dB}$、中心为 $-3\,\text{dB}$；Triangular（绿）在全范围为 $-3\,\text{dB}$。手册未给出任一曲线的解析式。

### 2.3 Mixer Explained — 混音台轨道 Pan

原文：

> Panning - Pan controls the position of the sound in the stereo field (left to right) … The pan works by mixing one side of the stereo track into the other, so a 100% pan is the mono-sum of the Left and Right channels. If you would like to pan using independent Left & Right level changes with no cross channel mixing use Fruity Stereo Shaper. By default a 'Circular Panning Law' is used.

要点：

- 手册明确混音台 pan 的行为是「把立体声轨道的一侧混入另一侧」，与实测的交叉混合结构定性一致，但未给出混合权重。
- 「$100\%$ pan 即 L+R 的单声道和」与实测 $R'=(L+R)/\sqrt2$ 相差常数因子 $1/\sqrt2$，不改变左右关系与反相抵消行为。
- 手册把 Fruity Stereo Shaper 列为不做交叉混合的替代方案，反证混音台轨道 Pan 属于交叉混合一类。

### 2.4 Channel Rack — 通道 Pan

原文（Channel Settings 第 7 项 Channel Panning）：

> This is pan information sent to the plugin, so what this does will depend entirely on the plugin loaded in the Channel. All native plugins will pan, some VST/AU plugins won't respond to this parameter. Normally you would use the Mixer track Pan controls.

要点：

- 通道 Pan 被描述为「送进插件的 pan 信息」，手册**不承诺**任何波形层面的结构，也没有说它与混音台 Pan 相同。
- 手册建议「通常应使用混音台轨道 Pan」，说明二者的作用位置不同：通道 Pan 在插件之前，混音台 Pan 在效果之后。

### 2.5 Mixing Advice — Sampler Channel 与 Audio Clip

原文：

> Panning Law - While both Sampler Channels and Audio Clips adhere to the default 'Circular Panning' law. This reduces sample gain by -3 dB when panned to the center, to maintain apparent loudness compared to hard panning and so can be another source of unexpected level changes compared to careful inspection of the originally recorded levels.

要点：手册把 $-3\,\text{dB}$ 表述为「中心处对采样增益的衰减」。该表述与实测「中心为单位增益、单声道极值为 $\sqrt2$」等价，属于**电平**层面的承诺。

### 2.6 变更记录与当前可选项

- 更新日志（2.5.0，2000-04-13）：`Added support for pyramid panning shape (circular is good but can generate clipping).`
- 更新日志：`Updated triangle panning law not to sound louder (uncompatible).` 该条表明 Triangular 的绝对电平曾在校正中被修改，不同版本的 Triangular 数据不可直接比较。
- 当前引擎字符串表中与本项相关的字符串仅有 `Panning law`、`PanLawLabel`、`PanLawSelect`、`Circular`、`Triangular`；中文语言包对应条目为 `Panning law → 声像法则`。即当前版本暴露两个选项，pyramid 未出现在字符串表中。

### 2.7 文档记载与实测的对应

| 文档表述                                                      | 实测 / 模型                                                                                 | 判定                     |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------ |
| Circular 中心相对极值 $-3\,\text{dB}$                         | 单声道输入：中心 $\lvert L'\rvert=\lvert R'\rvert=1$，极值 $\sqrt2$，相差 $3.01\,\text{dB}$ | 一致                     |
| Circular 下「a maximum of 3 dB can be added」                 | 单声道输入极值 $+3.01\,\text{dB}$                                                           | 一致                     |
| 「a 100% pan is the mono-sum of the Left and Right channels」 | $p=+1$：$L'=0$，$R'=(L+R)/\sqrt2$（仅混音台）                                               | 一致（相差常数因子）     |
| 「mixing one side of the stereo track into the other」        | 近端增益 $=\big((1+g_R)L+(1-g_R)R\big)/2$，权重随 pan 变化                                  | 定性一致；定量为本文补充 |
| Triangular「no level compensation」                           | $g_L=1-\max(p,0)$、$g_R=1+\min(p,0)$，无 $>1$ 增益                                          | 形态可区分               |
| Channel Panning「pan information sent to the plugin」         | 通道 Pan 为纯 balance，与混音台的交叉混合结构不同                                           | 一致（手册未明说结构）   |
| 「中心与极值相差 3 dB」为唯一定量约束                         | 模型另给出中间区段函数、交叉项与 $>1$ 的峰值                                                | 超出文档                 |

### 2.8 文档查不到的部分

1. 未给出 $g_{LL},g_{LR},g_{RL},g_{RR}$ 的任何闭式表达，仅有端点处的 $3\,\text{dB}$ 约束。
2. **未说明混音台 Pan 与通道 Pan 的结构差异**；「$100\%$ pan is the mono-sum」只对混音台成立，通道 Pan 在极值只保留近端声道。
3. 未区分单声道输入与立体声输入的规则差异；「mixing one side into the other」只说明定性方向。
4. 未说明 $p=0$ 处的分支结构，也未给出交叉混合权重 $(1\pm g_R)/2$、$(1\pm g_L)/2$ 的形式。
5. 未提及不对称立体声输入（$L=1,R=0$）时增益可超过 $1$（峰值 $+0.42\,\text{dB}$，$p\approx-0.2553$）；该现象在 $3\,\text{dB}$ 端点约束内不可见。
6. 未给出 Triangular 的绝对电平定义，故无法由文档推断 $L=1,R=0$ 时的第一列数值。

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

- **使用 float32**：中间结果存在大于 $1$ 的样本（峰值 $1.0499$），定点格式会削波，float 渲染可原样保留。

![左声道直流素材](<images/Left Channel DC.png>)

### 3.2 四份渲染

素材分别置于混音台轨道与 Audio Clip 通道，通过 `Link to controller...` 将对应 Pan 绑定到自动化控制器，使其在 $8$ 秒内从 $-100\%$ 线性移到 $+100\%$。每个 law 各渲染一次，共四份，均为 48 kHz、$8$ 秒、384000 帧。第 $i$ 帧对应名义 pan

$$
p_i=\frac{2i}{N-1}-1,\qquad N=384000 .
$$

| 渲染文件                            | 自动化目标                          | 组合                |
| ----------------------------------- | ----------------------------------- | ------------------- |
| `Mixer Circular Panning.wav`        | `Master - Panning`                  | Mixer × Circular    |
| `Mixer Triangular Panning.wav`      | `Master - Panning`                  | Mixer × Triangular  |
| `Audio Clip Circular Panning.wav`   | `Left Channel DC - Channel panning` | Channel × Circular  |
| `Audio Clip Triangular Panning.wav` | `Left Channel DC - Channel panning` | Channel × Triangular |

![FL Studio 工程](<images/FL Studio.png>)

### 3.3 反解流程

1. **前向残差**：直接把名义 $p_i$ 代入模型，与实测逐帧相减。该量级反映自动化时间轴相对理想斜坡的偏差。
2. **反解实际 pan**：用实测 $L'$（必要时配合 $R'$）逐帧反解实际 $\theta$，再重算另一通道，可把时间轴抖动从模型误差中分离。
3. **无自由参数的恒等式**：用实测的一个通道直接预言另一个通道，不含任何拟合常数，可直接证伪模型形状。

## 4. 分层模型

四种组合可以写成同一套结构的两种参数化结果。

### 4.1 Pan law：单声道增益

记 pan $p\in[-1,1]$，定义

$$
\theta=\frac{(p+1)\pi}{4},
$$

对应关系：$p=-1\Rightarrow\theta=0$，$p=0\Rightarrow\theta=\pi/4$，$p=+1\Rightarrow\theta=\pi/2$。两条 law 给出的单声道增益为

$$
\text{Circular:}\quad g_L=\sqrt2\cos\theta,\quad g_R=\sqrt2\sin\theta,
$$

$$
\text{Triangular:}\quad g_L=1-\max(p,0),\quad g_R=1+\min(p,0).
$$

Circular 满足 $g_L^2+g_R^2=2$，即严格等功率：中心 $g_L=g_R=1$，极左 $(g_L,g_R)=(\sqrt2,0)$，极右 $(0,\sqrt2)$。Triangular 不做补偿，近端恒为 $1$，远端从 $1$ 线性降到 $0$。

### 4.2 实现：交叉混合与 balance

**混音台轨道 Pan**：远端声道按 $(1-g_{\text{远端}})/2$ 的权重混入近端，再对近端整体施加 $g_{\text{近端}}$：

$$
p\le 0:\quad L'=g_L\left[\frac{1+g_R}{2}L+\frac{1-g_R}{2}R\right],\quad R'=g_RR,
$$

$$
p\ge 0:\quad L'=g_LL,\quad R'=g_R\left[\frac{1+g_L}{2}R+\frac{1-g_L}{2}L\right].
$$

**通道 Pan**：左右各自乘增益，互不串扰：

$$
L'=g_LL,\qquad R'=g_RR.
$$

两者的结构差异只在交叉项。单声道输入 $L=R=s$ 时，混音台括号内权重和为 $1$，故两种实现都退化为

$$
(L',R')=s\,(g_L,g_R),
$$

即**单声道响应完全由 law 决定**，与实现无关。这正是官方文档只能谈"$3\,\text{dB}$"的原因，也是通道 Pan 与混音台 Pan 的差异不会在单声道素材上暴露的原因。

### 4.3 四种组合的矩阵

写成 $[L',R']^{\mathrm T}=M(p)[L,R]^{\mathrm T}$。记 $A=\sqrt2\cos\theta$、$B=\sqrt2\sin\theta$：

$$
M_{\text{Mixer}\times\text{Circ}}(p)=
\begin{cases}
\begin{pmatrix}
\dfrac{A(1+B)}{2} & \dfrac{A(1-B)}{2}\\[8pt]
0 & B
\end{pmatrix}, & p\le 0,\\[16pt]
\begin{pmatrix}
A & 0\\[8pt]
\dfrac{B(1-A)}{2} & \dfrac{B(1+A)}{2}
\end{pmatrix}, & p\ge 0,
\end{cases}
\qquad
M_{\text{Channel}\times\text{Circ}}(p)=
\begin{pmatrix}
A & 0\\
0 & B
\end{pmatrix},
$$

$$
M_{\text{Mixer}\times\text{Tri}}(p)=
\begin{cases}
\begin{pmatrix}
\dfrac{2+p}{2} & -\dfrac{p}{2}\\[8pt]
0 & 1+p
\end{pmatrix}, & p\le 0,\\[16pt]
\begin{pmatrix}
1-p & 0\\[8pt]
\dfrac{p}{2} & 1-\dfrac{p}{2}
\end{pmatrix}, & p\ge 0,
\end{cases}
\qquad
M_{\text{Channel}\times\text{Tri}}(p)=
\begin{pmatrix}
1-\max(p,0) & 0\\
0 & 1+\min(p,0)
\end{pmatrix}.
$$

四者在 $p=0$ 处都退化为单位矩阵，因此中心为原样直通。

### 4.4 统一形式与特例

令 $\varphi=p\pi/4$，则 $A=\cos\varphi-\sin\varphi$、$B=\cos\varphi+\sin\varphi$，四种组合的非零元素可统一写成

$$
\begin{aligned}
\text{Mixer}\times\text{Circ},\ p\le 0:\quad & g_{LL}=\frac{A+\cos2\varphi}{2},\quad g_{LR}=\frac{A-\cos2\varphi}{2},\quad g_{RL}=0,\quad g_{RR}=B,\\
\text{Mixer}\times\text{Circ},\ p\ge 0:\quad & g_{LL}=A,\quad g_{LR}=0,\quad g_{RL}=\frac{B-\cos2\varphi}{2},\quad g_{RR}=\frac{B+\cos2\varphi}{2},\\
\text{Channel}\times\text{Circ}:\quad & g_{LL}=A,\quad g_{LR}=0,\quad g_{RL}=0,\quad g_{RR}=B,\\
\text{Mixer}\times\text{Tri},\ p\le 0:\quad & g_{LL}=1+\frac{p}{2},\quad g_{LR}=-\frac{p}{2},\quad g_{RL}=0,\quad g_{RR}=1+p,\\
\text{Mixer}\times\text{Tri},\ p\ge 0:\quad & g_{LL}=1-p,\quad g_{LR}=0,\quad g_{RL}=\frac{p}{2},\quad g_{RR}=1-\frac{p}{2},\\
\text{Channel}\times\text{Tri}:\quad & g_{LL}=1-\max(p,0),\quad g_{LR}=0,\quad g_{RL}=0,\quad g_{RR}=1+\min(p,0).
\end{aligned}
$$

共同性质：

- **中心直通**：$p=0$ 时 $M=I$，实测中心帧的 $L'$ 为精确的 $1.0000000$。
- **左右镜像**：$M(p)=J\,M(-p)\,J$，四种组合均成立。
- **两端对称**：$p=\pm1$ 时非零元素相同，只是 $L$ 与 $R$ 互换。

$L=1,\ R=0$ 时的数值（即矩阵第一列）：

| $p$   | Mixer×Circ $L'/R'$ | Channel×Circ $L'$ | Mixer×Tri $L'/R'$ | Channel×Tri $L'$ |
| ----- | ------------------ | ----------------- | ----------------- | ---------------- |
| −1    | 0.707107 / 0       | 1.414214          | 0.5 / 0           | 1                |
| −0.75 | 0.884862 / 0       | 1.387040          | 0.625 / 0         | 1                |
| −0.5  | 1.006835 / 0       | 1.306563          | 0.75 / 0          | 1                |
| −0.25 | 1.049878 / 0       | 1.175876          | 0.875 / 0         | 1                |
| 0     | 1 / 0              | 1                 | 1 / 0             | 1                |
| +0.5  | 0.541196 / 0.299728 | 0.541196         | 0.5 / 0.25        | 0.5              |
| +1    | 0 / 0.707107       | 0                 | 0 / 0.5           | 0                |

## 5. 四种组合的形态

### 5.1 Mixer × Circular

$$
p\le 0:\quad L'=A\left[\frac{1+B}{2}L+\frac{1-B}{2}R\right],\quad R'=BR,
$$

$$
p\ge 0:\quad L'=AL,\quad R'=B\left[\frac{1+A}{2}R+\frac{1-A}{2}L\right].
$$

以 $p\le0$ 支为例：括号内是权重和为 $1$ 的混合，$B=1$ 时权重为 $(1,0)$（左输出仅取左声道），$B=0$ 时权重为 $(1/2,1/2)$；外部增益 $A$ 同时由 $1$ 升到 $\sqrt2$。混合权重下降、外部增益上升，两者反向变化，乘积在区间内部出现极大值。另一侧 $R'=BR$ 只是淡出。

因此该组合的结构是：**把远端信号按随 pan 变化的权重混入近端，再对近端整体施加增益**，而不是对两声道分别施加独立系数。$100\%$ 时混合权重为 $50/50$，近端输出为 $(L+R)/\sqrt2$。

**峰值解析解**。$p\le0$ 支在 $L=1,R=0$ 时为

$$
L'(\theta)=\frac{A(1+B)}{2}=\frac{\sqrt2\cos\theta+\sin2\theta}{2}.
$$

令 $\mathrm dL'/\mathrm d\theta=0$：

$$
2\cos2\theta=\sqrt2\sin\theta
\;\Longrightarrow\;
4\sin^2\theta+\sqrt2\sin\theta-2=0
\;\Longrightarrow\;
\sin\theta=\frac{\sqrt{34}-\sqrt2}{8}.
$$

代回得

$$
L'_{\max}=\frac{\sqrt{142+34\sqrt{17}}}{16}=1.0498987884\ldots
$$

对应 $\theta=33.5107^\circ$，即 $p=-0.2553184$；增益 $>1$ 的区间为 $p\in[-0.519251,0]$。实测峰值 $1.04989886$，偏差 $7.4\times10^{-8}$。

该峰值的意义在于：纯 balance 模型（$L'=\sqrt2\cos\theta\cdot L$）在 $p\le0$ 上单调，从 $p=-1$ 的 $1.4142$ 一路降到 $p=0$ 的 $1$，不可能出现 $p=-0.255$ 处的内部极大值，而且在 $p=-1$ 就与实测相差一倍。因此这个突起直接证明 pan 内部先做交叉混合、再施加增益；官方 Circular / Triangular 的描述都不包含这一层。

![Mixer Circular 渲染](<images/Circular Panning Law.png>)

图：上为左声道、下为右声道。左声道由 $0.707$ 上升，约 3 秒处越过 $0\,\text{dB}$ 并达峰值后回落；右声道在 $p<0$ 区间恒为零，至 4 秒（$p=0$）方开始变化。两条曲线分别对应 $g_{LL}$ 与 $g_{RL}$。

### 5.2 Mixer × Triangular

$$
p\le 0:\quad L'=\frac{2+p}{2}L-\frac{p}{2}R,\quad R'=(1+p)R,
$$

$$
p\ge 0:\quad L'=(1-p)L,\quad R'=\frac{p}{2}L+\left(1-\frac{p}{2}\right)R.
$$

近端保持满电平、远端线性淡出到 $0$；$100\%$ 时近端为 $(L+R)/2$。与 5.1 对照，混合权重的变化是线性的、没有外部增益补偿，因此全程不出现 $>1$ 的增益，$L=1,R=0$ 时最大值为 $1$（在 $p\le0$）。

![Mixer Triangular 渲染](<images/Triangular Panning Law.png>)

图：左声道在中点达到 $0\,\text{dB}$ 后线性折返 —— $p\le0$ 时由 $0.5$ 升到 $1$，$p\ge0$ 时由 $1$ 降到 $0$；右声道自中点线性上升至 $0.5$。与 Circular 的圆顶曲线形态明显不同。

### 5.3 Channel × Circular

$$
L'=\sqrt2\cos\theta\cdot L,\qquad R'=\sqrt2\sin\theta\cdot R.
$$

纯 balance：每个声道只乘自己的增益，不引入对方的信号。$100\%$ 时一端为 $\sqrt2$、另一端为 $0$，**不做单声道和**。$L=1,R=0$ 时左输出在 $p=-1$ 处取到全程最大值 $\sqrt2=1.414214$，此后随 $p$ 单调下降，中途没有突起。

与 5.1 的差别值得强调：同一份 $L=1,R=0$ 输入，Mixer×Circular 在 $p=-1$ 只有 $0.707$、却在 $p=-0.255$ 升到 $1.0499$；Channel×Circular 在 $p=-1$ 就是 $1.4142$、之后单调下降。两条曲线完全无法用同一组参数互推（第 6.4 节给出量化残差）。

![Channel Circular 渲染](<images/Audio Clip Circular Panning.png>)

图：左右声道各为一条单调曲线，左声道由 $1.4142$（$+3.01\,\text{dB}$）降到 $0$，右声道恒为零（因输入 $R\equiv0$）。

### 5.4 Channel × Triangular

$$
L'=\big(1-\max(p,0)\big)L,\qquad R'=\big(1+\min(p,0)\big)R.
$$

$p\le0$ 时 $L'=L$ 保持不变、$R'=(1+p)R$ 线性淡出；$p\ge0$ 时 $L'=(1-p)L$ 线性淡出、$R'=R$ 保持不变。全程最大增益为 $1$，因此对 $0\,\text{dBFS}$ 素材不会引入削波风险。

![Channel Triangular 渲染](<images/Audio Clip Triangular Panning.png>)

图：左声道在 $p\le0$ 区间恒为 $1.0$（完全水平），$p\ge0$ 后线性降到 $0$；右声道恒为零。

### 5.5 四种组合对比

| 组合              | $p=-1$（$L=1,R=0$） | 单调性           | 最大增益 | $p=\pm1$ 时输出            |
| ----------------- | ------------------- | ---------------- | -------- | -------------------------- |
| Mixer×Circular    | 0.7071              | 先升后降         | 1.0499   | 近端 $(L+R)/\sqrt2$，远端 0 |
| Mixer×Triangular  | 0.5                 | 先升后降         | 1.0      | 近端 $(L+R)/2$，远端 0      |
| Channel×Circular  | 1.4142              | 单调下降         | 1.4142   | 近端 $\sqrt2\,L$，远端 0    |
| Channel×Triangular| 1.0                 | 先平后降         | 1.0      | 近端 $L$，远端 0            |

只有混音台会在极值把两声道折叠成单声道和；只有 Mixer×Circular 存在中间突起。四个组合在单声道输入下完全相同。

## 6. 验证

### 6.1 名义 pan 的前向残差

直接以名义线性斜坡代入模型：

| 组合                | $L'$ 最大误差       | $L'$ rms            | $R'$ 最大误差       | $R'$ rms            |
| ------------------- | ------------------- | ------------------- | ------------------- | ------------------- |
| Mixer×Circular      | $6.46\times10^{-5}$ | $2.39\times10^{-5}$ | $5.38\times10^{-5}$ | $1.55\times10^{-5}$ |
| Mixer×Triangular    | $5.73\times10^{-5}$ | $2.36\times10^{-5}$ | $2.87\times10^{-5}$ | $1.06\times10^{-5}$ |
| Channel×Circular    | $6.37\times10^{-5}$ | $2.39\times10^{-5}$ | $0$                 | $0$                 |
| Channel×Triangular  | $5.73\times10^{-5}$ | $2.14\times10^{-5}$ | $0$                 | $0$                 |

该量级高于 float32 精度，原因在于自动化时间轴并非数学上严格的线性斜坡（见 6.5）。四组残差的峰峰值都在 $1.1\times10^{-4}$ 量级、主周期同为 $750$ 帧，说明它们同源。

Channel 两份渲染的 $R'$ 是**精确 $0$**，不是小量：若通道 Pan 与混音台一样带交叉项，右半区必然出现 $g_R(1-g_L)/2\approx0.3$ 的泄漏。

### 6.2 反解实际 $\theta$

以 Mixer×Circular 为例，由实测 $L'$ 按分支反解每帧的 $\theta$ 后重算：

| 通道 | 最大误差            | rms                 |
| ---- | ------------------- | ------------------- |
| $L'$ | $7.44\times10^{-8}$ | $1.90\times10^{-9}$ |
| $R'$ | $8.41\times10^{-6}$ | $1.35\times10^{-6}$ |

$7.44\times10^{-8}$ 约为 $1.0$ 附近 float32 的一个 ULP（$2^{-24}\approx6\times10^{-8}$）。即在给定实际 pan 位置的条件下，模型与渲染结果在 float32 精度内一致；6.1 中的 $6.5\times10^{-5}$ 全部来自名义 pan 与实际 pan 的偏差。

需注意，峰值附近 $\mathrm dL'/\mathrm d\theta=0$，由 $L'$ 反解 $\theta$ 为病态，float32 舍入会被放大。故反解仅用于规则验证；衡量自动化时间轴抖动须使用前向残差。

同一方法用在另外三份渲染上，反解后残差同样落到 $10^{-8}\sim10^{-5}$：

| 组合                | 反解依据                    | 反解后残差                                                     |
| ------------------- | --------------------------- | -------------------------------------------------------------- |
| Mixer×Circular      | $L'$（按峰值分两支）        | $L'$ $7.44\times10^{-8}$，$R'$ $8.41\times10^{-6}$             |
| Mixer×Triangular    | $L'$（$p\le0$）/ $R'$（$p\ge0$） | $L'$ $7.54\times10^{-6}$，$R'$ 精确 $0$                   |
| Channel×Circular    | $L'$                        | 反解闭合；反解出的 $p$ 与名义斜坡差异 max $4.4\times10^{-4}$（$p>-0.98$） |
| Channel×Triangular  | $L'$（$p\ge0$）             | $3.0\times10^{-8}$                                             |

### 6.3 无自由参数的恒等式

每种组合都能导出一个只含实测值的恒等式：

**Mixer×Circular**，右半区 $L'=A$，由 $A^2+B^2=2$ 得 $B=\sqrt{2-L'^2}$，于是

$$
R'=\frac{(1-L')\sqrt{2-L'^2}}{2},
$$

192000 帧（右半区全部）上最大误差 $8.41\times10^{-6}$。

**Mixer×Triangular**，右半区 $R'=p/2$、$L'=1-p$，故

$$
L'=1-2R',\qquad \max\ \text{误差}\ 7.54\times10^{-6}.
$$

**Channel×Circular**，右半区 $L'$ 与 Mixer×Circular 的 $L'$ 应逐点相等（两者都等于 $A$，且两工程自动化形状相同），最大差 $7.39\times10^{-6}$。

**Channel×Triangular**，左半区 $L'\equiv1$（最大偏差 $1.79\times10^{-7}$）；右半区 $L'=1-p$ 而 Mixer×Triangular 的 $R'=p/2$，故

$$
L'=1-2R'_{\text{Mixer×Tri}},\qquad \max\ \text{差}\ 5.69\times10^{-6}.
$$

这些式子右侧只含实测值，不含拟合常数。若模型形状有误（例如缺少 $(1-A)/2$ 因子，或 $B\neq\sqrt{2-L'^2}$），它们会立即失配。

### 6.4 交叉证伪

把一种组合的式子套到另一种的数据上（$L$ 通道残差 rms）：

| 错误假设                            | 残差 rms |
| ----------------------------------- | -------- |
| 用 balance 描述 Mixer×Circular      | $0.270$  |
| 用 balance 描述 Mixer×Triangular    | $0.416$  |
| 用混音台式子描述 Channel×Circular   | $0.270$  |
| 用混音台式子描述 Channel×Triangular | $0.204$  |
| 用 Triangular 式子描述 Mixer×Circular   | $0.155$ |
| 用 Circular 式子描述 Mixer×Triangular   | $0.155$ |

残差比正常拟合（$10^{-5}$ 量级）大四个数量级，属形状级别的失配，而非参数偏差。这组对照说明四组模型彼此可区分，本方法具备判别能力。

### 6.5 自动化时间轴的残差

前向残差呈周期性起伏：

- 峰峰值 $1.213\times10^{-4}$（约 $-78.3\,\text{dB}$），rms $2.4\times10^{-5}$；
- 周期 $750$ 帧，48 kHz 下为 $15.625\,\text{ms}$；$8$ 秒内共 $512$ 个周期；
- 左右半区同相，仅与帧序号有关，与 pan 位置无关。

该分量属于 FL 自动化时间轴相对理想线性的偏差，可能源于 $750$ 帧周期的控制率，不属于 pan 增益规则。这解释了为什么此前用正弦/多项式拟合永远得不到"完美结论"：规则本身是精确的，不完美的部分是自动化时间轴。

### 6.6 单声道等功率的独立验证

四种模型对单声道输入都预测 $L'^2+R'^2=2s^2$ 与 pan 无关。独立渲染的单声道正弦按 $10\,\text{ms}$ 窗口取包络，共 $779$ 个有效窗口：

| 量                                          | 值                        |
| ------------------------------------------- | ------------------------- |
| $\min(\mathrm{peak}_L^2+\mathrm{peak}_R^2)$ | $0.999999$                |
| $\max(\mathrm{peak}_L^2+\mathrm{peak}_R^2)$ | $1.001971$                |
| 均值                                        | $1.001219$                |
| 标准差                                      | $5.80\times10^{-4}$       |
| 相对离散度                                  | $1.97\times10^{-3}$       |
| 隐含源幅度 $s$                              | $0.707538\approx1/\sqrt2$ |
| 输出峰值 $\sqrt2s$                          | $1.0000$                  |

该数据与主实验来自两次独立渲染。它同时说明：等功率性质由 law 决定，与实现无关 —— 因此光靠单声道素材无法区分混音台 Pan 与通道 Pan。

### 6.7 误差来源汇总

| 来源         | 量级                               | 说明                                   |
| ------------ | ---------------------------------- | -------------------------------------- |
| float32 舍入 | $1\times10^{-8}\sim1\times10^{-6}$ | $1.0$ 附近一个 ULP 约 $6\times10^{-8}$ |
| $R'$ 重构    | $8.4\times10^{-6}$                 | 由 $L'$ 推 $R'$ 的误差放大             |
| 自动化时间轴 | $1.2\times10^{-4}$ ptp             | 主残差，$-78\,\text{dB}$，750 帧周期   |
| 模型形状误差 | $<1\times10^{-7}$                  | 反解实际 $\theta$ 后仅余舍入           |

误差均已逐项归因，且无一项指向增益公式本身。

## 7. 对混音的影响

1. **单声道素材**：四种组合完全一致，都是等功率法则（Circular）或不补偿（Triangular），中心 $0\,\text{dB}$，Circular 两端 $+3.01\,\text{dB}$。用单声道素材无法察觉混音台 Pan 与通道 Pan 的差别。
2. **立体声素材 × 混音台 Pan**：并非 balance，而是交叉混合加增益。远端信号会混入近端；$100\%$ 时近端为 $(L+R)/\sqrt2$（Circular）或 $(L+R)/2$（Triangular）的单声道和。含反相成分的素材硬 pan 后可能部分抵消、听感变薄，单声道兼容性检查时应予考虑。
3. **立体声素材 × 通道 Pan**：纯 balance，$100\%$ 时只剩一个声道，不做单声道和。想在通道层做"平移而不塌陷"时，这一差别是可利用的。
4. **$0.42\,\text{dB}$ 突起（仅 Mixer×Circular）**：素材接近 $0\,\text{dBFS}$ 且自动化扫过 $p\approx-0.26$ 时可能多出 $0.42\,\text{dB}$；做增益分配时，最大值不在端点而在 $p\approx-0.26$。FL 内部为 float 不会立即削波，但导出至定点格式或经限幅器时该增益真实存在。
5. **立体声宽度**：混音台 Pan 在端点把立体声折叠为单声道和。若需保持左右关系整体平移，应使用 Mid/Side、双 pan、或通道 Pan + 专用立体声定位插件，而非混音台轨道 Pan。

## 8. 适用范围与局限

- 被测版本为 FL Studio 20.8.3.2304（`FLEngine_x64.dll`，2021-03-25）。其他版本不保证一致，需按本文方法重新测量。
- 公式由实验反解得到，**未经源码确认**。静态分析尝试结果：UI 字符串经本地化字符串池按 ID 取值；$1/\sqrt2$ 在 52 MB 镜像中精确匹配 $0$ 次；未发现预计算增益表。
- 四份渲染都只用 $L=1,R=0$ 单一输入，四个增益元素由左右对称性补全。对称性已写入模型，实测形状与之一致；如需严格验证，可追加 $L=0,R=1$ 与 $L=R=1$ 的交叉渲染。
- 通道侧实测的是 **Audio Clip 通道**。Sampler 通道共用同一 Channel Panning 控件（手册将二者并称），但未单独渲染，公式对它只是推测。
- 插件内部的 pan 不在范围内。

## 9. 数据与复现

- 四种组合的渲染：[Mixer Circular Panning.wav](<output-wav-files/Mixer Circular Panning.wav>)、[Mixer Triangular Panning.wav](<output-wav-files/Mixer Triangular Panning.wav>)、[Audio Clip Circular Panning.wav](<output-wav-files/Audio Clip Circular Panning.wav>)、[Audio Clip Triangular Panning.wav](<output-wav-files/Audio Clip Triangular Panning.wav>)
- 四个工程文件：[fl-studio-projects/](<fl-studio-projects/>)
- 输入素材：[Left Channel DC.wav](<input-wav-file/Left Channel DC.wav>)
- 绘图与计算脚本：[scripts/main.py](scripts/main.py)（四种组合的实测/模型对照与残差表）

官方文档：

- Project General Settings（Panning law 定义与补偿曲线）：<https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/songsettings_settings.htm>
- Mixer Explained（轨道 Pan 的作用方式）：<https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/mixer.htm>
- Channel Rack（Channel Panning 是送入插件的 pan 信息）：<https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/channelrack.htm>
- Mixing Advice（Panning Law 注记）：<https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/mixer_levelsandmixing.htm>
- Fruity Stereo Shaper（不做交叉混合的声像方案）：<https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/plugins/Fruity%20Stereo%20Shaper.htm>
- 20.8 版本手册镜像：`https://support.image-line.com/redirect/FLStudio20Help/html/<页面名>.htm`
- 手册补偿曲线原图：<https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/img_shot/songsettings_panning.png>

复现结果不一致时，优先核对：FL 版本、项目 Panning law 设置、自动化目标是否为对应控件、轨道上是否存在其他增益或限幅处理。
