# FL Studio Pan Rule

逆向 FL Studio 20.8.3.2304（`FLEngine_x64.dll`，未加壳 x64 PE）中 Pan 旋钮对**立体声**信号的规则。

结论分两层：**Pan law**（项目设置里的 Circular / Triangular）只决定**单声道增益**；**实现**
（混音台轨道 Pan，还是通道 / Audio Clip Pan）决定**立体声如何交叉混合**。两者的四种组合
（2 个 law × 2 种实现）都用实测渲染反解并验证过。

交互式曲线：<https://www.desmos.com/calculator/hl9t99uge9>

---

## 1. 结论

### 1.1 Pan law：单声道增益

记 pan $p\in[-1,1]$，$\theta=\dfrac{(p+1)\pi}{4}$（极左 $\theta=0$、中心 $\theta=\pi/4$、极右 $\theta=\pi/2$）：

| law        | $g_L$                    | $g_R$                    |
| ---------- | ------------------------ | ------------------------ |
| Circular   | $\sqrt2\cos\theta$       | $\sqrt2\sin\theta$       |
| Triangular | $1-\max(p,0)$            | $1+\min(p,0)$            |

- **Circular** 严格等功率（$g_L^2+g_R^2=2$）：中心两个 $1$，极值一个 $\sqrt2$（$+3.01\,\text{dB}$），另一个 $0$。
- **Triangular** 不做补偿：近端恒为 $1$，远端从 $1$ 线性衰减到 $0$。

### 1.2 两种实现：交叉混合与 balance

**混音台轨道 Pan** 把远端声道按随 pan 变化的权重混入近端，因此 $100\%$ 时折叠成单声道和：

$$
p\le 0:\quad L'=g_L\left[\frac{1+g_R}{2}L+\frac{1-g_R}{2}R\right],\qquad R'=g_RR,
$$

$$
p\ge 0:\quad L'=g_LL,\qquad R'=g_R\left[\frac{1+g_L}{2}R+\frac{1-g_L}{2}L\right].
$$

**通道 Pan**（Channel Rack / Audio Clip）是纯 balance，左右互不串扰：

$$
L'=g_LL,\qquad R'=g_RR.
$$

两者对**单声道**输入完全一致（$(L',R')=s\,(g_L,g_R)$），差别只在立体声的交叉项。

### 1.3 四种组合的矩阵

$[L',R']^{\mathrm T}=M(p)[L,R]^{\mathrm T}$：

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
\end{pmatrix},
$$

其中 $A=\sqrt2\cos\theta$，$B=\sqrt2\sin\theta$。$p=0$ 时四种组合都退化为单位矩阵，即中心为原样直通。

### 1.4 数值表

输入 $L=1,\ R=0$（即矩阵第一列）。Channel 两列只给出 $L$：这两份渲染的 $R'$ 恒为零，
$R$ 方向的增益由左右对称性补出。

| $p$   | Mixer×Circ $L'/R'$  | Channel×Circ $L'$ | Mixer×Tri $L'/R'$ | Channel×Tri $L'$ |
| ----- | ------------------- | ----------------- | ----------------- | ---------------- |
| −1.00 | 0.70711 / 0         | 1.41421           | 0.50000 / 0       | 1.00000          |
| −0.50 | 1.00683 / 0         | 1.30656           | 0.75000 / 0       | 1.00000          |
| 0.00  | 1.00000 / 0         | 1.00000           | 1.00000 / 0       | 1.00000          |
| +0.50 | 0.54120 / 0.29973   | 0.54120           | 0.50000 / 0.25    | 0.50000          |
| +1.00 | 0.00000 / 0.70711   | 0.00000           | 0.00000 / 0.50    | 0.00000          |

### 1.5 性质

- **只有混音台会折叠成单声道**：$p=\pm1$ 时混音台输出近端 $g\,(L+R)/2$（Circular 为 $(L+R)/\sqrt2$，
  Triangular 为 $(L+R)/2$），远端为 $0$；通道 Pan 在极值只保留近端声道，不做单声道和。
- **只有 Mixer×Circular 会出现 $>1$ 的中间增益**：$L=1,R=0$ 时左输出在
  $\sin\theta=\dfrac{\sqrt{34}-\sqrt2}{8}$（$p=-0.255318408$）处取极大值
  $\dfrac{\sqrt{142+34\sqrt{17}}}{16}=1.049898788409$（$+0.4229\,\text{dB}$），
  增益大于 $1$ 的区间为 $p\in[-0.519251,0]$。其余三种组合的最大增益分别是
  $\sqrt2$（Channel×Circular，在 $p=\mp1$）与 $1$（两种 Triangular）。
- **对称性**：$M(p)=J\,M(-p)\,J$，$J=\begin{pmatrix}0&1\\1&0\end{pmatrix}$，四种组合均成立。

---

## 2. 官方文档记载

### 2.1 文档来源

| 文档                                               | 位置                               | 本文引用内容                                                                      |
| -------------------------------------------------- | ---------------------------------- | --------------------------------------------------------------------------------- |
| FL Studio Online Manual — Project General Settings | `songsettings_settings.htm`        | Panning law 定义、两个选项、补偿曲线图                                            |
| FL Studio Online Manual — Mixer Explained          | `mixer.htm`                        | 混音台轨道 Pan 的作用方式                                                         |
| FL Studio Online Manual — Channel Rack             | `channelrack.htm`                  | Channel Panning 是送入插件的 pan 信息                                             |
| FL Studio Online Manual — Mixing Advice            | `mixer_levelsandmixing.htm`        | Sampler Channel / Audio Clip 的 $-3\,\text{dB}$ 说明                              |
| FL Studio Online Manual — Fruity Stereo Shaper     | `plugins/Fruity Stereo Shaper.htm` | 不做交叉混合的替代声像方案                                                        |
| FL Studio 更新日志                                 | What's New（`WhatsNew.rtf`）       | Triangular 修改记录、pyramid panning 加入记录                                     |
| 引擎字符串表与中文语言包                           | `FLEngine_x64.dll`、`zh_CN.mo`     | `PanLawLabel`、`PanLawSelect`、`Circular`、`Triangular`；`Panning law → 声像法则` |

对应 20.8 的版本化镜像为 `support.image-line.com/redirect/FLStudio20Help/html/` 下的同名页面；
本文引用的段落与在线手册文字一致。

### 2.2 Panning law 的定义

> Circular panning maintains a constant apparent volume by progressively lowering the combined volume
> of the L+R channels by -3 dB as the pan passes dead center. Triangular panning does not apply this
> compensation, so the apparent loudness will increase as the sound passes the center position. …
> Circular - Level compensation is applied when panning (orange). Level drops 3 dB at center pan.
> Triangular - No level compensation is used as a function of pan position (green). The overall level
> is 3 dB lower, across the pan range, compared to the extreme pan positions for circular mode.

同页关于 Audio Clip 电平读数：

> Also note that for audio clips, at default Channel Sampler settings the level readout will be
> identical to the recorded level, so when using Circular panning, a maximum of 3 dB can be added.
> It still works exactly the same way (extreme pan position and center have a 3 dB difference), but
> in this case volume is being added at extremes instead of subtracted at the center position.

手册给出的定量约束只有「中心与极值相差 $3\,\text{dB}$」这一条，未给出中间位置的函数形式。

### 2.3 混音台轨道 Pan

> The pan works by mixing one side of the stereo track into the other, so a 100% pan is the mono-sum
> of the Left and Right channels. If you would like to pan using independent Left & Right level
> changes with no cross channel mixing use Fruity Stereo Shaper. By default a 'Circular Panning Law'
> is used.

手册把混音台 Pan 定性描述为「把一侧混入另一侧、$100\%$ 为单声道和」，与实测的交叉混合结构一致，
但未给出混合权重；实测的极值是 $(L+R)/\sqrt2$，与「单声道和」相差常数因子 $1/\sqrt2$。

### 2.4 通道 Pan

> This is pan information sent to the plugin, so what this does will depend entirely on the plugin
> loaded in the Channel. … Normally you would use the Mixer track Pan controls.

即通道 Pan 只是「送进插件的 pan 信息」，手册不承诺任何波形层面的结构。

### 2.5 变更记录

- 2.5.0（2000-04-13）：`Added support for pyramid panning shape (circular is good but can generate clipping).`
- `Updated triangle panning law not to sound louder (uncompatible).`
  该条表明 Triangular 的绝对电平曾在校正中被修改，不同版本的 Triangular 数据不可直接比较。
- 当前引擎字符串表中相关字符串只有 `Panning law`、`PanLawLabel`、`PanLawSelect`、`Circular`、
  `Triangular`；即当前版本只暴露两个选项。

### 2.6 文档有没有说 Mixer Pan 与 Audio Clip Pan 的区别

**没有。**文档只把混音台描述成「交叉混合、$100\%$ 为单声道和」，把通道 Pan 描述成「送给插件的
pan 信息」；「adhere to Circular Panning law」「works exactly the same way」两处只在
**$3\,\text{dB}$ 电平关系**上成立，从未涉及交叉混合结构。

### 2.7 文档记载与实测的对应

| 文档表述                                                        | 实测 / 模型                                                                                   | 判定                     |
| --------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ------------------------ |
| Circular 中心相对极值 $-3\,\text{dB}$                           | 单声道输入：中心 $\lvert L'\rvert=\lvert R'\rvert=1$，极值 $\sqrt2$，差 $3.01\,\text{dB}$      | 一致                     |
| 「a maximum of 3 dB can be added」                              | 单声道极值 $+3.01\,\text{dB}$                                                                  | 一致                     |
| 「a 100% pan is the mono-sum of the Left and Right channels」   | $p=+1$：$L'=0$，$R'=(L+R)/\sqrt2$（仅混音台）                                                  | 一致（差常数因子）       |
| 「mixing one side of the stereo track into the other」          | 近端 $=\big((1+g_R)L+(1-g_R)R\big)/2$，权重随 pan 变化                                         | 定性一致；定量为本文补充 |
| Triangular「no level compensation」                             | $g_L=1-\max(p,0)$、$g_R=1+\min(p,0)$，无 $>1$ 增益                                             | 形态可区分               |
| Channel Panning「pan information sent to the plugin」           | 通道 Pan 为纯 balance，与混音台的交叉混合结构不同                                              | 一致（手册未明说结构）   |
| 「中心与极值相差 3 dB」为唯一定量约束                           | 模型另给出中间区段函数、交叉项与 $>1$ 的峰值                                                    | 超出文档                 |

### 2.8 文档未覆盖的内容

1. 未给出任何 $g_{LL},g_{LR},g_{RL},g_{RR}$ 的闭式，只有端点处的 $3\,\text{dB}$ 约束。
2. 未区分混音台 Pan 与通道 Pan 的结构差异；「$100\%$ pan is the mono-sum」只对混音台成立。
3. 未说明 $p=0$ 处的分支结构，也未给出交叉权重的形式。
4. 未提及不对称立体声输入（$L=1,R=0$）时增益可超过 $1$（峰值 $+0.42\,\text{dB}$，$p\approx-0.2553$）。
5. 未给出 Triangular 的绝对电平定义，无法由文档推出第一列数值。

---

## 3. 测量与反解

### 3.1 测试信号与反解

源码层面未取得（见第 6 节），故采用黑箱测量：输入 32-bit float 立体声 $L=1$（$0\,\text{dB}$ 直流）、
$R=0$，把 Pan 在 $8$ 秒内从 $-100\%$ 线性推到
$+100\%$，逐帧读取输出即得增益矩阵第一列 $L'=g_{LL}$、$R'=g_{RL}$；再由左右对称性
$M(p)=J\,M(-p)\,J$ 补出 $g_{LR}(p)=g_{RL}(-p)$、$g_{RR}(p)=g_{LL}(-p)$。

选择依据：

- **直流**：每一采样点上 pan 等效为静态增益，输出即等于增益，无需包络估计或相位对齐。
- **float32**：中间结果存在大于 $1$ 的样本（峰值 $1.0499$），定点格式会削波。

### 3.2 四份渲染

四份渲染使用同一素材、形状相同的 $8$ 秒线性自动化，48 kHz、384000 帧，第 $i$ 帧对应名义 pan

$$
p_i=\frac{2i}{N-1}-1,\qquad N=384000 .
$$

| 渲染文件                          | 自动化目标                      | 组合                |
| --------------------------------- | ------------------------------- | ------------------- |
| `Mixer Circular Panning.wav`      | `Master - Panning`              | Mixer×Circular      |
| `Mixer Triangular Panning.wav`    | `Master - Panning`              | Mixer×Triangular    |
| `Audio Clip Circular Panning.wav` | `Left Channel DC - Channel panning` | Channel×Circular |
| `Audio Clip Triangular Panning.wav` | `Left Channel DC - Channel panning` | Channel×Triangular |

通道侧实测的是 **Audio Clip 通道**（自动化目标即其 Channel Panning 旋钮）。

### 3.3 反解与验证思路

- **前向残差**：直接以名义 $p_i$ 代入模型，残差量级反映自动化时间轴相对理想斜坡的偏差。
- **反解实际 $\theta$**：用实测 $L'$ 逐帧反解 $\theta$，再重算 $R'$，可把时间轴抖动从模型误差中分离。
  注意在 $\mathrm dL'/\mathrm d\theta=0$ 处反解病态，故反解只用于规则验证。
- **无自由参数的恒等式**：用实测 $L'$ 直接预言 $R'$，不含任何拟合常数，可直接证伪模型形状。

---

## 4. 四种组合的形态

### 4.1 Mixer × Circular

$$
p\le 0:\quad L'=A\left[\frac{1+B}{2}L+\frac{1-B}{2}R\right],\quad R'=BR;\qquad
p\ge 0:\quad L'=AL,\quad R'=B\left[\frac{1+A}{2}R+\frac{1-A}{2}L\right].
$$

括号内是权重和为 $1$ 的混合：$B=1$ 时权重 $(1,0)$，$B=0$ 时 $(1/2,1/2)$；外部增益 $A$ 由 $1$ 升到
$\sqrt2$。两者反向变化，乘积在区间内部出现极大值。

**峰值解析解**。$p\le0$ 支在 $L=1,R=0$ 时为

$$
L'(\theta)=\frac{A(1+B)}{2}=\frac{\sqrt2\cos\theta+\sin2\theta}{2},
$$

令 $\mathrm dL'/\mathrm d\theta=0$ 得 $2\cos2\theta=\sqrt2\sin\theta$，即
$4\sin^2\theta+\sqrt2\sin\theta-2=0$，故

$$
\sin\theta=\frac{\sqrt{34}-\sqrt2}{8},\qquad
L'_{\max}=\frac{\sqrt{142+34\sqrt{17}}}{16}=1.0498987884\ldots
$$

对应 $\theta=33.5107^\circ$，$p=-0.2553184$。

![Mixer Circular 渲染](<images/Circular Panning Law.png>)

上为左声道、下为右声道。左声道自 $0.707$（$-3\,\text{dB}$）上升，越过 $0\,\text{dB}$ 后回落；
右声道在 $p<0$ 区间恒为零，至 $4$ 秒（$p=0$）方开始变化。

### 4.2 Mixer × Triangular

$g_L=1-\max(p,0)$、$g_R=1+\min(p,0)$ 代入混音台式子：

$$
p\le 0:\quad L'=\frac{2+p}{2}L-\frac{p}{2}R,\quad R'=(1+p)R;\qquad
p\ge 0:\quad L'=(1-p)L,\quad R'=\frac{p}{2}L+\left(1-\frac{p}{2}\right)R.
$$

近端保持满电平、远端线性淡出到 $0$；$100\%$ 时近端为 $(L+R)/2$。全程无 $>1$ 增益。

![Mixer Triangular 渲染](<images/Triangular Panning Law.png>)

左声道自 $0.5$（$-6\,\text{dB}$）线性升至中心 $1.0$ 后线性折返；右声道自中点线性上升。

### 4.3 Channel × Circular

$$
L'=A\,L=\sqrt2\cos\theta\cdot L,\qquad R'=B\,R=\sqrt2\sin\theta\cdot R .
$$

纯 balance：$100\%$ 时只保留近端声道，不做单声道和。$L=1,R=0$ 时左输出最大为 $\sqrt2$
（$+3.01\,\text{dB}$，在 $p=-1$），全程单调，无中间突起。

![Channel Circular 渲染](<images/Audio Clip Circular Panning.png>)

左声道由 $\sqrt2$（$+3.01\,\text{dB}$）单调降到 $0$；因输入 $R\equiv0$，右声道全程为零。

### 4.4 Channel × Triangular

$$
L'=\big(1-\max(p,0)\big)L,\qquad R'=\big(1+\min(p,0)\big)R .
$$

$p\le0$ 时 $L'=L$ 不变、$R'=(1+p)R$ 线性淡出；$p\ge0$ 时 $L'=(1-p)L$ 线性淡出、$R'=R$ 不变。
全程最大增益为 $1$。

![Channel Triangular 渲染](<images/Audio Clip Triangular Panning.png>)

左声道在 $p\le0$ 区间保持水平（恒为 $1$），$p\ge0$ 后线性降到 $0$；右声道全程为零。

---

## 5. 验证

### 5.1 名义 pan 下的前向残差

| 组合                  | $L'$ 最大误差           | $L'$ rms              | $R'$ 最大误差           | $R'$ rms              |
| --------------------- | ----------------------- | --------------------- | ----------------------- | --------------------- |
| Mixer×Circular        | $6.46\times10^{-5}$     | $2.39\times10^{-5}$   | $5.38\times10^{-5}$     | $1.55\times10^{-5}$   |
| Mixer×Triangular      | $5.73\times10^{-5}$     | $2.36\times10^{-5}$   | $2.87\times10^{-5}$     | $1.06\times10^{-5}$   |
| Channel×Circular      | $6.37\times10^{-5}$     | $2.39\times10^{-5}$   | $0$                     | $0$                   |
| Channel×Triangular    | $5.73\times10^{-5}$     | $2.14\times10^{-5}$   | $0$                     | $0$                   |

四组残差峰峰值都在 $1.1\times10^{-4}$ 量级、主周期 **750 帧**，与 5.5 节识别出的自动化抖动同源，
说明残差来自自动化时间轴而非规则本身。

### 5.2 反解实际 $\theta$（Mixer×Circular）

由实测 $L'$ 按分支反解每帧的 $\theta$ 后重算：

| 通道 | 最大误差              | rms                   |
| ---- | --------------------- | --------------------- |
| $L'$ | $7.44\times10^{-8}$   | $1.90\times10^{-9}$   |
| $R'$ | $8.41\times10^{-6}$   | $1.35\times10^{-6}$   |

$7.44\times10^{-8}$ 约为 $1.0$ 附近 float32 的一个 ULP（$2^{-24}\approx6\times10^{-8}$）。
即给定实际 pan 位置时，模型与渲染在 float32 精度内一致；5.1 中的 $6.5\times10^{-5}$ 全部来自
名义 pan 与实际 pan 的偏差。另外三份渲染反解后的残差同样在 $10^{-8}\sim10^{-5}$ 之间。

### 5.3 无自由参数的恒等式

- **Mixer×Circular**，右半区 $L'=A$，由 $A^2+B^2=2$ 得 $B=\sqrt{2-L'^2}$，于是

  $$
  R'=\frac{(1-L')\sqrt{2-L'^2}}{2}.
  $$

  右半区 192000 帧上最大误差 $8.41\times10^{-6}$。

- **Mixer×Triangular**，右半区 $R'=p/2$、$L'=1-p$，故 $L'=1-2R'$，最大误差 $7.54\times10^{-6}$。

- **Channel×Circular**，右半区 $L'$ 与 Mixer×Circular 的 $L'$ 逐点相等（两工程自动化形状相同），
  最大差 $7.39\times10^{-6}$。

- **Channel×Triangular**，左半区 $L'\equiv1$（最大偏差 $1.79\times10^{-7}$）；右半区
  $L'=1-2R'_{\text{Mixer×Tri}}$，最大差 $5.69\times10^{-6}$。

这些式子右侧只含实测值，不含拟合常数，因此它们证伪的是模型形状，而不是又一次"拟合成功"。

### 5.4 交叉证伪

把一种组合的式子套到另一种的数据上（$L'$ 残差 rms）：

| 错误假设                                | 残差 rms |
| --------------------------------------- | -------- |
| 用 balance 描述 Mixer×Circular          | $0.270$  |
| 用 balance 描述 Mixer×Triangular        | $0.416$  |
| 用混音台式子描述 Channel×Circular       | $0.270$  |
| 用混音台式子描述 Channel×Triangular     | $0.204$  |
| 用 Triangular 式子描述 Mixer×Circular   | $0.155$  |
| 用 Circular 式子描述 Mixer×Triangular   | $0.155$  |

残差比正常拟合（$10^{-5}$ 量级）大四个数量级，属形状级别的失配，而非参数偏差。**Channel 两份渲染的
$R'$ 是精确 $0$**：若它与混音台一样带交叉项，右半区必然出现 $g_R(1-g_L)/2\approx0.3$ 的泄漏；实测没有，
因此通道 Pan 是纯 balance。

### 5.5 自动化时间轴的残差

前向残差呈周期性起伏：

- 峰峰值 $1.213\times10^{-4}$（约 $-78.3\,\text{dB}$），rms $2.4\times10^{-5}$；
- 周期 $750$ 帧，48 kHz 下为 $15.625\,\text{ms}$；$8$ 秒内共 $512$ 个周期；
- 左右半区同相，只依赖帧序号，与 pan 位置无关。

该分量属于 FL 自动化时间轴相对理想线性的偏差（可能是 $750$ 帧周期的控制率），不属于 Pan 规则。
这也解释了此前用正弦/多项式拟合为什么拿不到"完美结论"。

### 5.6 单声道等功率的独立验证

模型对单声道输入预测 $L'^2+R'^2=2s^2$ 与 pan 无关。独立渲染的单声道正弦按 $10\,\text{ms}$ 窗口取包络，
共 $779$ 个有效窗口：

| 量                                            | 值                        |
| --------------------------------------------- | ------------------------- |
| $\min(\mathrm{peak}_L^2+\mathrm{peak}_R^2)$   | $0.999999$                |
| $\max(\mathrm{peak}_L^2+\mathrm{peak}_R^2)$   | $1.001971$                |
| 均值                                          | $1.001219$                |
| 标准差                                        | $5.80\times10^{-4}$       |
| 相对离散度                                    | $1.97\times10^{-3}$       |
| 隐含源幅度 $s$                                | $0.707538\approx1/\sqrt2$ |
| 输出峰值 $\sqrt2s$                            | $1.0000$                  |

该数据与主实验来自两次独立渲染。

### 5.7 误差来源

| 来源         | 量级                                     | 说明                                   |
| ------------ | ---------------------------------------- | -------------------------------------- |
| float32 舍入 | $1\times10^{-8}\sim1\times10^{-6}$       | $1.0$ 附近一个 ULP 约 $6\times10^{-8}$ |
| $R'$ 重构    | $8.4\times10^{-6}$                       | 由 $L'$ 推 $R'$ 的误差放大             |
| 自动化时间轴 | $1.2\times10^{-4}$ ptp                   | 主残差，$-78\,\text{dB}$，750 帧周期   |
| 模型形状误差 | $<1\times10^{-7}$                        | 反解实际 $\theta$ 后仅余舍入           |

---

## 6. 还没做成的部分（逆向代码）

本机 Ghidra provider 未配置（缺 `GHIDRA_INSTALL_DIR`，且只有 JDK 17 而要求 JDK 21+），
故未能用反编译器读出 Pan 代码。用 `capstone` / `pefile` 自建的静态扫描结论：

- 已定位字符串：`PanLawLabel`、`PanLawSelect`、`Circular`、`Triangular`、`Panning law`、
  `Center panned signal`、`Get/Set track pan`、`Get/Set channel pan`。
- 对它们做 RIP 相对（disp32）与绝对（VA 字面量）双重引用扫描，**全库 0 命中**。
  这与 FL 的**本地化字符串池**机制一致（字符串按 ID 从语言包 `.mo` 取，代码不直接引用地址）。
- 未发现任何 float32 预计算 pan 增益表（$1/\sqrt2=0.70710677$ 在整个 52 MB 镜像里精确出现 $0$ 次）。

因此**代码级确认尚未完成**；但第 5 节的实测已在 float32 精度上把规则钉死。

---

## 7. 使用与目录

```bash
uv sync
uv run python scripts/main.py     # 四种组合的实测/模型对照与误差
```

| 位置                                | 内容                                                         |
| ----------------------------------- | ------------------------------------------------------------ |
| `scripts/main.py`                   | 四种组合的模型与实测对照                                     |
| `scripts/make_left_channel_dc.py`   | 重新生成 `input-wav-file/Left Channel DC.wav`                |
| `input-wav-file/`                   | 测试素材（$L=1,\ R=0$ 直流）                                 |
| `output-wav-files/`                 | 四种组合的 32-bit float 渲染                                 |
| `fl-studio-projects/`               | 四个 FLP（自动化目标分别为混音台 Pan / 通道 Pan）            |
| `images/`                           | 实测曲线图                                                   |
| `article.md`                        | 测量报告（面向读者的完整推导）                               |

## 8. 证据强度

- **实验**：四种组合的闭式形式（曲线形状、交叉项、驼峰、通道的无交叉混合）全部来自实测，
  残差与已识别的自动化抖动同量级。
- **官方文档**：能交叉验证的只有端点行为、单声道电平差，以及"混音台会交叉混合"；
  文档没有公式，也没有混音台/通道的结构差异。
- **论坛**：查了 19 个 Image-Line 论坛帖，没有任何公式可供核对。
- **源代码**：没有取得（见第 6 节）。这是唯一的缺口。

## 9. 数据说明

`output-wav-files/*.wav` 是四种组合的渲染：输入恒为 $L=1,\ R=0$，pan 在 $8$ 秒内线性从 $-100\%$
扫到 $+100\%$，48 kHz、32-bit float、384000 帧。通道侧用的是 Audio Clip 通道，Sampler 通道共用同一
Channel Panning 控件但未单独渲染。`input-wav-file/Left Channel DC.wav` 可用
`uv run python scripts/make_left_channel_dc.py` 重新生成。
