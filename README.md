# FL Studio 立体声 Pan 规则的实验反解

> 被测版本：FL Studio 20.8.3.2304（`FLEngine_x64.dll`，2021-03-25，未加壳 x64 PE）
> 测量日期：2026-10-15（四种组合的补充测量：2026-10-18）

## 摘要

"Pan 就是把声音推到左边或右边"——这句话对单声道素材大致成立，对立体声素材则掩盖了两层彼此独立的设计。FL Studio 的 Pan 由**项目级的 Pan law**（Circular / Triangular）和**两个不同的控件**（混音台轨道 Pan、通道机架 Pan）共同决定，四种组合的传递函数并不相同。官方手册对它们只有"中心与极值相差 3 dB"这一条定量描述，没有公式，也没有说明两个控件的结构差异。

本文以 $L=1$、$R=0$ 的直流素材为输入，用自动化在 8 秒内把 pan 从 −100% 线性扫到 +100%，从 32-bit float 渲染中逐帧反解 $2\times2$ 传递矩阵，得到四种组合的完整闭式。核心结果是可分离性：传递矩阵由 Pan law 给出的**单声道增益** $(g_L,g_R)$ 与实现决定的**混合规则**两部分构成。Circular 取 $g_L=\sqrt2\cos\theta$、$g_R=\sqrt2\sin\theta$，Triangular 取 $g_L=1-\max(p,0)$、$g_R=1+\min(p,0)$，其中 $\theta=(p+1)\pi/4$；混音台轨道把远端声道按 $(1-g_{\text{远端}})/2$ 的权重混入近端，通道则是左右各自乘增益、互不串扰。

由此得到三条有实际意义的结论：

1. **同一条 law 下，两种实现在单声道素材上完全一致**，差别只存在于立体声的交叉项。这意味着用单声道素材永远无法区分两个控件。
2. **只有混音台的 100% pan 是单声道和**，为 $(L+R)/\sqrt2$（Circular）或 $(L+R)/2$（Triangular）；通道的 100% pan 只是把一个声道关掉。
3. **只有混音台 × Circular 会在区间内部超过 0 dB**：$L=1,R=0$ 时左输出在 $p=-0.2553$ 处达到 $\sqrt{142+34\sqrt{17}}/16=1.0499$（$+0.42$ dB），增益大于 1 的区间为 $p\in[-0.5193,0]$。另外三种组合的最大增益分别是 $\sqrt2$（通道 × Circular，在极值）与 $1$（两种 Triangular）。

验证方面：反解实际 pan 位置后，左通道残差降至 $7.4\times10^{-8}$，约为 float32 的一个 ULP；四种组合各有一个只含实测值的恒等式，最大误差 $8.4\times10^{-6}$。剩余的前向残差峰峰值为 $1.2\times10^{-4}$，其频谱在 64 Hz（$=48\,\text{kHz}/750$）处有窄峰，对应自动化时间轴自身的周期性误差，与增益规则无关。

## 1. 引言

### 1.1 一个旋钮，两种行为

对单声道输入，Pan 旋钮表现为标准的等功率法则：中心 $0\,\text{dB}$，两端各 $+3.01\,\text{dB}$。对立体声输入，它决定的实际问题变成另一些：

- 素材 pan 到极端时是否退化为单声道和，含反相成分的素材会不会部分抵消；
- 自动化扫过某个位置时是否出现电平突起；
- 总线预留的余量是否够覆盖增益变化；
- 听到的宽度与定位来自素材本身，还是来自 pan law。

这些问题在 FL 里会被两个独立的选择同时影响：项目设置里的 Pan law（Circular / Triangular），以及你转动的是哪个旋钮——混音台轨道上的，还是通道机架里的。手册对前者说"把一侧混入另一侧"，对后者说"送进插件的 pan 信息"，两句话都不是公式。

### 1.2 为什么只能实测

FL 是闭源软件。本文尝试过静态分析：在 `FLEngine_x64.dll` 中定位到 `PanLawLabel`、`PanLawSelect`、`Circular`、`Triangular` 等字符串，但对它们做 RIP 相对与绝对地址双重引用扫描后全库 0 命中——FL 的界面字符串走本地化字符串池，代码按 ID 从语言包取值，不直接引用字符串地址。镜像中也没有预计算的增益表（$1/\sqrt2=0.70710677$ 在 52 MB 里精确出现 0 次）。

因此本文采用黑箱测量：输入已知信号，线性扫描 pan，逐样本读取输出并反解传递函数。

## 2. 记号

先约定本文使用的符号，后文一律沿用。

**输入与输出。** 记某一瞬间的输入为向量 $x=[L,\ R]^{\mathrm T}$，输出为 $y=[L',\ R']^{\mathrm T}$。本文检验的最简假设是线性、无记忆的：

$$
y=M(p)\,x,\qquad M(p)=\begin{pmatrix}g_{LL}&g_{LR}\\ g_{RL}&g_{RR}\end{pmatrix},
$$

即 Pan 在每个采样点上等价于一个 $2\times2$ 实矩阵，其四个元素只依赖于 pan 位置 $p$。

**pan 位置。** $p\in[-1,1]$，$-1$ 为极左，$0$ 为中心，$+1$ 为极右。为书写方便引入

$$
\theta=\frac{(p+1)\pi}{4}\in\left[0,\frac{\pi}{2}\right],
$$

即极左 $\theta=0$、中心 $\theta=\pi/4$、极右 $\theta=\pi/2$。

**单声道增益。** 若输入是单声道 $L=R=s$，输出可写成 $s\,(g_L,\ g_R)$。$g_L$、$g_R$ 称为该 Pan law 的**单声道增益**，它们是 law 的核心内容，也是本文要测的第一个对象。

**哪些量待定。** 本文的实测任务就是确定两件事：

1. 两条 law 各自的 $(g_L,g_R)$ 作为 $p$ 的函数；
2. $M(p)$ 如何由 $(g_L,g_R)$ 与"实现"构成——也就是两个控件的混合规则。

矩阵的四个元素 $g_{LL},g_{LR},g_{RL},g_{RR}$ 分别是"左入左出""右入左出""左入右出""右入右出"的增益。

## 3. 官方文档怎么说

### 3.1 材料

| 文档                                               | 页面                               | 引用的内容                                |
| -------------------------------------------------- | ---------------------------------- | ----------------------------------------- |
| FL Studio Online Manual — Project General Settings | `songsettings_settings.htm`        | Panning law 的定义、两个选项、补偿曲线图  |
| FL Studio Online Manual — Mixer Explained          | `mixer.htm`                        | 混音台轨道 Pan 的作用方式                 |
| FL Studio Online Manual — Channel Rack             | `channelrack.htm`                  | Channel Panning 是送入插件的 pan 信息     |
| FL Studio Online Manual — Mixing Advice            | `mixer_levelsandmixing.htm`        | Sampler Channel / Audio Clip 的 −3 dB 说明 |
| FL Studio Online Manual — Fruity Stereo Shaper     | `plugins/Fruity Stereo Shaper.htm` | 不做交叉混合的替代声像方案                |
| FL Studio 更新日志                                 | What's New（`WhatsNew.rtf`）       | Triangular 修改记录、pyramid panning 加入记录 |
| 引擎字符串表与中文语言包                           | `FLEngine_x64.dll`、`zh_CN.mo`     | `PanLawLabel`、`PanLawSelect`、`Circular`、`Triangular` |

引用文字与被测版本对应的 20.8 手册镜像、当前在线手册均一致。

### 3.2 Project General Settings — Panning law

> Panning law - The purpose is to maintain a constant apparent volume as a sound is panned. For example, if a sound is panned hard left or right, only one speaker will be active. This will sound quieter than the center position where both speakers are active, unless steps are taken to counteract this effect. Circular panning maintains a constant apparent volume by progressively lowering the combined volume of the L+R channels by -3 dB as the pan passes dead center. Triangular panning does not apply this compensation, so the apparent loudness will increase as the sound passes the center position. … Circular - Level compensation is applied when panning (orange). Level drops 3 dB at center pan. Triangular - No level compensation is used as a function of pan position (green). The overall level is 3 dB lower, across the pan range, compared to the extreme pan positions for circular mode.

同页关于 Audio Clip 的电平读数：

> Also note that for audio clips, at default Channel Sampler settings the level readout will be identical to the recorded level, so when using Circular panning, a maximum of 3 dB can be added. It still works exactly the same way (extreme pan position and center have a 3 dB difference), but in this case volume is being added at extremes instead of subtracted at the center position.

按第 2 节的记号，这两段说的是：$(g_L,g_R)$ 在两个端点与中心之间相差 3 dB，Circular 表现为中心低、Triangular 表现为整体低。这约束了曲线的形状，但没有给出曲线本身。

### 3.3 Mixer Explained — 混音台轨道 Pan

> The pan works by mixing one side of the stereo track into the other, so a 100% pan is the mono-sum of the Left and Right channels. If you would like to pan using independent Left & Right level changes with no cross channel mixing use Fruity Stereo Shaper. By default a 'Circular Panning Law' is used.

手册把混音台 Pan 定性描述为"把一侧混入另一侧、100% 为单声道和"，即 $g_{LR},g_{RL}$ 不全为零。至于混合的权重、以及"单声道和"前面的常数因子，都没有说明。

### 3.4 Channel Rack — 通道 Pan

> This is pan information sent to the plugin, so what this does will depend entirely on the plugin loaded in the Channel. All native plugins will pan, some VST/AU plugins won't respond to this parameter. Normally you would use the Mixer track Pan controls.

通道 Pan 被描述为"送进插件的 pan 信息"，手册不承诺 $M$ 的任何结构，也没有说它与混音台相同。手册建议"通常应使用混音台轨道 Pan"，说明两者作用位置不同：通道 Pan 在插件之前，混音台 Pan 在效果之后。

### 3.5 Mixing Advice — Sampler Channel 与 Audio Clip

> Panning Law - While both Sampler Channels and Audio Clips adhere to the default 'Circular Panning' law. This reduces sample gain by -3 dB when panned to the center, to maintain apparent loudness compared to hard panning and so can be another source of unexpected level changes compared to careful inspection of the originally recorded levels.

承诺的仍然是 $(g_L,g_R)$ 的电平关系：中心处相对极值低 3 dB。

### 3.6 版本变更

- 2.5.0（2000-04-13）：`Added support for pyramid panning shape (circular is good but can generate clipping).`
- `Updated triangle panning law not to sound louder (uncompatible).` —— Triangular 的绝对电平曾在校正中被修改，不同版本的 Triangular 数据不可直接比较。
- 当前引擎字符串表中相关字符串只有 `Panning law`、`PanLawLabel`、`PanLawSelect`、`Circular`、`Triangular`，即当前版本只暴露两个选项，pyramid 不在其中。

### 3.7 文档留下的空白

对照第 2 节的记号，手册给出的信息可以概括为：

- $(g_L,g_R)$：只有"中心与极值相差 3 dB"这一条约束，没有闭式，也没有 Triangular 的绝对电平。
- $M(p)$ 的结构：只有混音台"把一侧混入另一侧、100% 为单声道和"这一句定性描述；通道完全没有描述。
- 两者是否相同：从未提及。手册没有说明通道 Pan 与混音台 Pan 在结构上是否一致。
- 是否存在区间内部的极大值：没有提及。用 3 dB 端点约束无法推断出这一点。

## 4. 方法

### 4.1 测试信号

素材是 32-bit float 立体声 WAV，左声道恒为 $1.0$（$0\,\text{dB}$ 直流），右声道恒为 $0$。

![左声道直流素材（上：左声道；下：右声道）](<images/Left Channel DC.png>)

*测试素材：左声道恒为 1（0 dB 直流），右声道恒为 0。*

三个选择各有理由：

- **直流**：pan 在每个采样点上等效为静态增益，输出直接等于增益，无需包络估计、相位对齐或频率响应校正。
- **$x=[1,\ 0]^{\mathrm T}$**：输出直接暴露矩阵第一列，$L'=g_{LL}$、$R'=g_{RL}$。再由左右镜像对称

  $$
  M(p)=J\,M(-p)\,J,\qquad J=\begin{pmatrix}0&1\\1&0\end{pmatrix},
  $$

  补出 $g_{LR}(p)=g_{RL}(-p)$、$g_{RR}(p)=g_{LL}(-p)$，一次扫描即可还原全部四个元素。

- **float32**：中间结果存在大于 1 的样本（峰值 $1.0499$），定点格式会削波，float 渲染能原样保留。

### 4.2 四份渲染

素材分别放在混音台轨道和 Audio Clip 通道上，用 `Link to controller...` 把对应 Pan 绑定到自动化控制器，8 秒内从 −100% 线性移到 +100%，48 kHz 导出，共 384000 帧。第 $i$ 帧对应名义 pan

$$
p_i=\frac{2i}{N-1}-1,\qquad N=384000 .
$$

| 渲染文件                            | 自动化目标                          | 组合                |
| ----------------------------------- | ----------------------------------- | ------------------- |
| `Mixer Circular Panning.wav`        | `Master - Panning`                  | Mixer × Circular    |
| `Mixer Triangular Panning.wav`      | `Master - Panning`                  | Mixer × Triangular  |
| `Audio Clip Circular Panning.wav`   | `Left Channel DC - Channel panning` | Channel × Circular  |
| `Audio Clip Triangular Panning.wav` | `Left Channel DC - Channel panning` | Channel × Triangular |

两个自动化目标名称的差异本身就是一个证据：混音台 Pan 与通道 Pan 是两个独立控件。

![测量工程（混音台 Pan 的自动化）](<images/FL Studio.png>)

*测量工程：素材放在一条混音台轨道上，轨道 Pan 由自动化控制器在 8 秒内线性扫过 −100% → +100%。*

### 4.3 识别与验证

1. **形状识别**：把实测第一列与候选函数逐点比对，先定 $(g_L,g_R)$，再定 $M$ 的混合结构。
2. **前向残差**：直接以名义 $p_i$ 代入模型相减。该量级反映自动化时间轴相对理想斜坡的偏差。
3. **反解实际 pan**：用实测 $L'$ 逐帧反解真实 $\theta$ 再重算，可把时间轴抖动从模型误差中分离。
4. **不含自由参数的恒等式**：用实测的一个通道预言另一个通道，不含任何拟合常数，可直接检验模型形状。

## 5. 结果

### 5.1 Pan law：单声道增益

两条 law 的 $(g_L,g_R)$ 为

$$
\text{Circular:}\qquad g_L=\sqrt2\cos\theta,\qquad g_R=\sqrt2\sin\theta,\qquad g_L^2+g_R^2=2,
$$

$$
\text{Triangular:}\qquad g_L=1-\max(p,0),\qquad g_R=1+\min(p,0).
$$

Circular 严格等功率：中心 $g_L=g_R=1$，极左 $(\sqrt2,0)$，极右 $(0,\sqrt2)$。Triangular 不做补偿：近端恒为 1，远端从 1 线性降到 0。

![两种 Pan law 的单声道增益与声像轨迹](<images/fig01-law.png>)

图 1：左图是两条 law 的增益曲线，Circular 为圆弧、Triangular 为直线加平台。右图把 $(g_L,g_R)$ 画成平面上的轨迹：Circular 走四分之一圆弧，Triangular 走由 $(0,1)$、$(1,1)$、$(1,0)$ 连成的折线。这正是"circular / triangular"两个名字的来源。

### 5.2 实现：$M$ 如何由增益构成

**混音台轨道 Pan** 把远端声道按 $(1-g_{\text{远端}})/2$ 的权重混入近端，再对近端整体施加 $g_{\text{近端}}$：

$$
p\le 0:\quad L'=g_L\left[\frac{1+g_R}{2}L+\frac{1-g_R}{2}R\right],\quad R'=g_RR,
$$

$$
p\ge 0:\quad L'=g_LL,\quad R'=g_R\left[\frac{1+g_L}{2}R+\frac{1-g_L}{2}L\right].
$$

**通道 Pan** 是纯 balance，左右互不串扰：

$$
L'=g_LL,\qquad R'=g_RR.
$$

两者的差别只在交叉项。代入单声道输入 $L=R=s$，混音台括号内的权重和为 1，两种实现都退化为

$$
(L',R')=s\,(g_L,g_R),
$$

即**单声道响应完全由 law 决定，与实现无关**。这既是官方文档只能谈"3 dB"的原因，也是用单声道素材永远区分不出两种实现的原因。

### 5.3 四种组合的矩阵

记 $A=\sqrt2\cos\theta$、$B=\sqrt2\sin\theta$（即 Circular 的 $g_L,g_R$），四种组合的 $M(p)$ 为

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

四者在 $p=0$ 处都退化为单位矩阵，因此中心是原样直通。令 $\varphi=p\pi/4$（此时 $A=\cos\varphi-\sin\varphi$、$B=\cos\varphi+\sin\varphi$），Circular 的两支还可以写成更"像代码"的形式：

$$
\begin{aligned}
p\le 0:\quad & g_{LL}=\frac{A+\cos2\varphi}{2},\quad g_{LR}=\frac{A-\cos2\varphi}{2},\quad g_{RL}=0,\quad g_{RR}=B,\\
p\ge 0:\quad & g_{LL}=A,\quad g_{LR}=0,\quad g_{RL}=\frac{B-\cos2\varphi}{2},\quad g_{RR}=\frac{B+\cos2\varphi}{2}.
\end{aligned}
$$

### 5.4 四种组合的形态

![四种组合的实测与模型](<images/fig02-combinations.png>)

图 2：四种组合在 $L=1,R=0$ 下的输出。彩色细线是渲染实测，灰色粗线是模型，两者在整段 pan 范围内重合；虚线是 $0\,\text{dB}$ 参考。

四种形态可以这样记：

- **Mixer × Circular**：左输出先按 $A(1+B)/2$ 上升，越过 $0\,\text{dB}$ 后在 $p=0$ 前又回落到 1；右输出在 $p<0$ 恒为 0，$p>0$ 时才按 $B(1-A)/2$ 升起。
- **Mixer × Triangular**：左输出在 $p\le0$ 从 $0.5$ 线性升到 1，在 $p>0$ 线性降到 0；右输出自中心线性升到 $0.5$。折线，没有突起。
- **Channel × Circular**：左输出从 $\sqrt2$ 单调降到 0，右输出恒为 0。单调，没有突起。
- **Channel × Triangular**：左输出在 $p\le0$ 是一条水平线（恒为 1），$p>0$ 后线性降到 0。

它们的数值（矩阵第一列）：

| $p$   | Mixer×Circ $L'/R'$  | Channel×Circ $L'$ | Mixer×Tri $L'/R'$ | Channel×Tri $L'$ |
| ----- | ------------------- | ----------------- | ----------------- | ---------------- |
| −1.00 | 0.707107 / 0        | 1.414214          | 0.500000 / 0      | 1.000000         |
| −0.75 | 0.884862 / 0        | 1.387040          | 0.625000 / 0      | 1.000000         |
| −0.50 | 1.006835 / 0        | 1.306563          | 0.750000 / 0      | 1.000000         |
| −0.25 | 1.049878 / 0        | 1.175876          | 0.875000 / 0      | 1.000000         |
| 0.00  | 1.000000 / 0        | 1.000000          | 1.000000 / 0      | 1.000000         |
| +0.50 | 0.541196 / 0.299728 | 0.541196          | 0.500000 / 0.25   | 0.500000         |
| +1.00 | 0 / 0.707107        | 0                 | 0 / 0.500000      | 0                |

对比要点：

| 组合               | $p=-1$ 时 $L'$ | 单调性   | 最大增益 | $p=\pm1$ 的输出            |
| ------------------ | -------------- | -------- | -------- | -------------------------- |
| Mixer×Circular     | 0.7071         | 先升后降 | 1.0499   | 近端 $(L+R)/\sqrt2$，远端 0 |
| Mixer×Triangular   | 0.5000         | 先升后降 | 1.0000   | 近端 $(L+R)/2$，远端 0      |
| Channel×Circular   | 1.4142         | 单调下降 | 1.4142   | 近端 $\sqrt2\,L$，远端 0    |
| Channel×Triangular | 1.0000         | 先平后降 | 1.0000   | 近端 $L$，远端 0            |

只有混音台会在极值把两个声道折叠成单声道和；只有 Mixer × Circular 存在中间突起。

### 5.5 唯一超过 0 dB 的组合

Mixer × Circular 的 $p\le0$ 支在 $L=1,R=0$ 时为

$$
L'(\theta)=\frac{A(1+B)}{2}=\frac{\sqrt2\cos\theta+\sin2\theta}{2}.
$$

括号内是权重和为 1 的混合：$B=1$ 时权重 $(1,0)$，$B=0$ 时权重 $(1/2,1/2)$；与此同时外部增益 $A$ 从 1 升到 $\sqrt2$。权重下降、增益上升，两者反向变化，乘积于是在区间内部出现极大值。

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

对应 $\theta=33.5107^\circ$，即 $p=-0.2553184$；增益大于 1 的区间为 $p\in[-0.519251,0]$。实测峰值 $1.04989886$，与理论值相差 $7.4\times10^{-8}$。

![Mixer × Circular 的中间突起](<images/fig03-peak.png>)

图 3：$L=1,R=0$ 时的左输出。阴影区是增益大于 1 的部分，峰值为 $1.0498988$，位于 $p=-0.255318$。

需要强调这是**区间内部**的极大值：同一组合在 $p=-1$ 处只有 $0.707$，在 $p=0$ 处为 $1$，端点都不超过 0 dB。只有交叉混合与增益补偿同时存在时才会出现这种现象，因此它同时也是"混音台先混合、再施加增益"这一结构的直接证据。

## 6. 验证

### 6.1 逐帧残差

直接以名义线性斜坡代入模型：

| 组合              | $L'$ 最大误差       | $L'$ rms            | $R'$ 最大误差       | $R'$ rms            |
| ----------------- | ------------------- | ------------------- | ------------------- | ------------------- |
| Mixer×Circular    | $6.46\times10^{-5}$ | $2.39\times10^{-5}$ | $5.38\times10^{-5}$ | $1.55\times10^{-5}$ |
| Mixer×Triangular  | $5.73\times10^{-5}$ | $2.36\times10^{-5}$ | $2.87\times10^{-5}$ | $1.06\times10^{-5}$ |
| Channel×Circular  | $6.37\times10^{-5}$ | $2.39\times10^{-5}$ | $0$                 | $0$                 |
| Channel×Triangular| $5.73\times10^{-5}$ | $2.14\times10^{-5}$ | $0$                 | $0$                 |

![四种组合的逐帧残差](<images/fig04-residual.png>)

图 4：实测减模型，单位 $10^{-6}$。四组残差都呈同一量级的周期性起伏。

Channel 两组的 $R'$ 残差是**精确 0**：模型预测 $R'=g_RR=0$，实测也恰为 0。若通道 Pan 带有交叉项，$p>0$ 时应有 $R'=g_R(1-g_L)L/2\neq0$；实测没有。这是通道 Pan 不做交叉混合的直接证据。

### 6.2 反解实际 pan

前向残差的量级高于 float32 精度，原因是自动化时间轴并不是数学上严格的线性斜坡。用实测 $L'$ 按分支反解每帧的真实 $\theta$ 后重算：

| 通道 | 最大误差            | rms                 |
| ---- | ------------------- | ------------------- |
| $L'$ | $7.44\times10^{-8}$ | $1.90\times10^{-9}$ |
| $R'$ | $8.41\times10^{-6}$ | $1.35\times10^{-6}$ |

$7.44\times10^{-8}$ 约为 1.0 附近 float32 的一个 ULP（$2^{-24}\approx6\times10^{-8}$）。给定真实 pan 位置时，模型与渲染在 float32 精度内一致；6.1 里的 $6.5\times10^{-5}$ 全部来自名义 pan 与实际 pan 的偏差。

峰值附近 $\mathrm dL'/\mathrm d\theta=0$，由 $L'$ 反解 $\theta$ 是病态的，float32 舍入会被放大，因此反解只用于规则验证，衡量时间轴抖动必须用前向残差。

另外三组同法处理，反解后残差分别为 $7.54\times10^{-6}$（Mixer×Triangular）、闭合（Channel×Circular，反解出的 pan 与名义斜坡差异最大 $4.4\times10^{-4}$）、$3.0\times10^{-8}$（Channel×Triangular，右半区）。

### 6.3 不含自由参数的恒等式

每种组合都能导出一个只含实测值的恒等式：

- **Mixer×Circular**：右半区 $L'=A$，由 $A^2+B^2=2$ 得 $B=\sqrt{2-L'^2}$，于是

  $$
  R'=\frac{(1-L')\sqrt{2-L'^2}}{2},
  $$

  右半区 192000 帧上最大误差 $8.41\times10^{-6}$。

- **Mixer×Triangular**：右半区 $R'=p/2$、$L'=1-p$，故 $L'=1-2R'$，最大误差 $7.54\times10^{-6}$。

- **Channel×Circular**：模型给出 $L'=A$，与 Mixer×Circular 右半区（$p\ge0$）的 $L'=A$ 为同一函数；两份渲染逐点最大差 $7.39\times10^{-6}$。

- **Channel×Triangular**：左半区 $L'\equiv1$（最大偏差 $1.79\times10^{-7}$）；右半区 $L'=1-p$ 而 Mixer×Triangular 的 $R'=p/2$，故 $L'=1-2R'_{\text{Mixer×Tri}}$，最大差 $5.69\times10^{-6}$。

这些式子右侧只含实测值，不含任何拟合常数。若模型形状有误（例如缺少 $(1-A)/2$ 因子，或 $B\neq\sqrt{2-L'^2}$），它们会立刻失配。

### 6.4 自动化时间轴的误差

把前向残差除以 $\mathrm dL'/\mathrm dp$，得到每帧的实际 pan 与名义 pan 之差：

![自动化时间轴误差的波形与频谱](<images/fig05-spectrum.png>)

图 5：左图是前 100 ms 的 pan 偏差，呈锯齿状，周期 15.625 ms。右图是其频谱，主频恰好 64 Hz —— 即 48 kHz 除以 750 帧。偏差峰峰值约 $10^{-4}$（相对 pan 满量程），与残差量级一致。

这说明 6.1 中剩余的误差**不在增益公式里，而在自动化时间轴里**：实际 pan 相对理想线性斜坡存在固定周期的锯齿偏差，周期恰为 750 帧（15.625 ms）。至于 FL 内部为何是 750 帧，本文没有进一步确认——它不影响 Pan 增益规则本身的结论。这也解释了此前用正弦或多项式拟合永远得不到"完美结论"的原因。

### 6.5 单声道等功率的独立验证

Circular 模型对单声道输入预测 $L'^2+R'^2=2s^2$ 与 pan 无关（Triangular 不做补偿，因此不是等功率，这条检验只针对 Circular）。另取一份独立渲染的单声道正弦（早期测试数据，未随本仓库分发），按 10 ms 窗口取包络，共 779 个有效窗口：

| 量                                          | 值                        |
| ------------------------------------------- | ------------------------- |
| $\min(\mathrm{peak}_L^2+\mathrm{peak}_R^2)$ | $0.999999$                |
| $\max(\mathrm{peak}_L^2+\mathrm{peak}_R^2)$ | $1.001971$                |
| 均值                                        | $1.001219$                |
| 标准差                                      | $5.80\times10^{-4}$       |
| 相对离散度                                  | $1.97\times10^{-3}$       |
| 隐含源幅度 $s$                              | $0.707538\approx1/\sqrt2$ |
| 输出峰值 $\sqrt2s$                          | $1.0000$                  |

相对离散度正好是 16-bit 量化量级。该数据与主实验来自两次独立渲染。

### 6.6 误差来源

| 来源         | 量级                               | 说明                                   |
| ------------ | ---------------------------------- | -------------------------------------- |
| float32 舍入 | $1\times10^{-8}\sim1\times10^{-6}$ | 1.0 附近一个 ULP 约 $6\times10^{-8}$   |
| $R'$ 重构    | $8.4\times10^{-6}$                 | 由 $L'$ 推 $R'$ 的误差放大             |
| 自动化时间轴 | $1.2\times10^{-4}$ ptp             | 主残差，64 Hz，750 帧周期              |
| 模型形状误差 | $<1\times10^{-7}$                  | 反解实际 $\theta$ 后仅余舍入           |

每一项都已归因，且没有一项指向增益公式本身。

## 7. 与官方文档对照

现在可以用第 5 节的结果回答第 3 节留下的空白：

| 文档表述                                                      | 实测                                                          | 判定                     |
| ------------------------------------------------------------- | ------------------------------------------------------------- | ------------------------ |
| Circular 中心相对极值 −3 dB                                   | 单声道：中心 $g_L=g_R=1$，极值 $\sqrt2$，差 $3.01\,\text{dB}$  | 一致                     |
| 「a maximum of 3 dB can be added」                            | 单声道极值 $+3.01\,\text{dB}$                                  | 一致                     |
| 「a 100% pan is the mono-sum of the Left and Right channels」 | $p=\pm1$：近端 $=(L+R)/\sqrt2$（Circular）或 $(L+R)/2$（Triangular），远端 $=0$（**仅混音台**） | 一致（差常数因子） |
| 「mixing one side of the stereo track into the other」        | $g_{LR},g_{RL}$ 非零，权重为 $(1\mp g)/2$                      | 一致，且本文给出权重     |
| Triangular「no level compensation」                           | $g_L=1-\max(p,0)$、$g_R=1+\min(p,0)$，无 $>1$ 增益             | 一致                     |
| Channel Panning「pan information sent to the plugin」         | 通道 Pan 为纯 balance，$g_{LR}=g_{RL}=0$                       | 一致（手册未明说结构）   |
| 通道的 100% pan 是否为单声道和（文档未提及）                  | 不是；只保留近端声道                                           | 文档未覆盖，本文补充     |
| 是否存在区间内部的极大值（文档未提及）                        | Mixer×Circular 在 $p=-0.2553$ 处有 $1.0499$ 的极大值            | 文档未覆盖，本文补充     |

**结论：文档能支持的只有两条 law 的电平关系和"混音台会交叉混合"这一句定性描述。**"100% pan is the mono-sum"只对混音台成立；通道 Pan 的结构差异，以及内部极大值，都是本文新增的实测结论。

## 8. 讨论：对混音的影响

1. **单声道素材**：同一条 law 下两种实现完全一致（Circular 为等功率，Triangular 为不补偿）。用单声道素材无法察觉混音台 Pan 与通道 Pan 的差别。
2. **立体声素材 + 混音台 Pan**：不是 balance，而是交叉混合加增益。远端信号会混进近端；100% 时近端变成 $(L+R)/\sqrt2$（Circular）或 $(L+R)/2$（Triangular）的单声道和。含反相成分的素材硬 pan 后可能部分抵消、听感变薄，做单声道兼容性检查时值得注意。
3. **立体声素材 + 通道 Pan**：纯 balance，100% 时只剩一个声道。要在通道层做"平移而不塌陷"，这个差别正好可以利用。
4. **0.42 dB 突起（仅 Mixer × Circular）**：接近 0 dBFS 的素材在自动化扫过 $p\approx-0.26$ 时会多出 0.42 dB。做增益分配时，最大值不在端点而在 $p\approx-0.26$。FL 内部是 float 不会立即削波，但导出到定点格式或经过限幅器时这个增益是真实存在的。
5. **立体声宽度**：混音台 Pan 在端点把立体声折叠成单声道和；若想保持左右关系整体平移，应使用 Mid/Side、双 pan，或通道 Pan 配合专用定位插件。

## 9. 局限

- 结论针对 FL Studio 20.8.3.2304。其他版本不保证一致，需按第 4 节的方法重新测量。
- 公式由实验反解得到，**未经源码确认**（静态分析受阻的原因见 1.2 节）。
- 四份渲染都只用 $L=1,R=0$ 一种输入，四个增益元素由左右对称性补全。对称性已写入模型且实测形状与之一致；若要严格验证，可追加 $L=0,R=1$ 与 $L=R=1$ 的交叉渲染。
- 通道侧实测的是 **Audio Clip 通道**。Sampler 通道共用同一个 Channel Panning 控件（手册将二者并称），但未单独渲染，公式对它只是推测。
- 插件内部的 pan 不在范围内。

## 10. 数据与复现

四份渲染与工程文件都在仓库里，插图由脚本从渲染数据直接生成：

```bash
uv sync
uv run python scripts/make_figures.py --stats
```

| 位置                              | 内容                                                     |
| --------------------------------- | -------------------------------------------------------- |
| `output-wav-files/`               | 四种组合的 32-bit float 渲染（48 kHz、384000 帧）        |
| `fl-studio-projects/`             | 四个 FLP，自动化目标分别为混音台 Pan 与通道 Pan          |
| `input-wav-file/Left Channel DC.wav` | 测试素材（$L=1,\ R=0$ 直流）                          |
| `scripts/make_figures.py`         | 生成图 1–5，并可打印残差统计                             |
| `scripts/make_left_channel_dc.py` | 重新生成测试素材                                         |

复现结果不一致时，优先核对：FL 版本、项目 Panning law 设置、自动化目标是否为对应控件、轨道上是否存在其他增益或限幅处理。

---

## 附录 A：原始渲染截图

以下两图是导出后在 Adobe Audition 中查看的原始渲染，可直接看到两种 law 在混音台上的曲线形状差异。

![Mixer Circular 原始渲染](<images/Circular Panning Law.png>)

*图 A1：`Mixer Circular Panning.wav`。左声道自 −3 dB 上升并越过 0 dB，右声道在中心之后才出现。*

![Mixer Triangular 原始渲染](<images/Triangular Panning Law.png>)

*图 A2：`Mixer Triangular Panning.wav`。左声道在中心折返，右声道在中心之后线性上升。*

---

## 参考

1. Image-Line. *FL Studio Online Manual — Project General Settings（Panning law）*. <https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/songsettings_settings.htm>
2. Image-Line. *FL Studio Online Manual — Mixer Explained*. <https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/mixer.htm>
3. Image-Line. *FL Studio Online Manual — Channel Rack*. <https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/channelrack.htm>
4. Image-Line. *FL Studio Online Manual — Mixing Advice*. <https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/mixer_levelsandmixing.htm>
5. Image-Line. *FL Studio Online Manual — Fruity Stereo Shaper*. <https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/plugins/Fruity%20Stereo%20Shaper.htm>
6. Image-Line. *What's New*（`WhatsNew.rtf`，随 FL Studio 20.8.3.2304 分发）。
7. 20.8 手册版本化镜像：`https://support.image-line.com/redirect/FLStudio20Help/html/<页面名>.htm`
