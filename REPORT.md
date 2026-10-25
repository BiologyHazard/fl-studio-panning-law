# FL Studio Panning Law

## 摘要

本研究通过左声道单位直流激励，测量 FL Studio 中 Mixer 与 Audio Clip 两类声像控制在 Circular 和 Triangular 设置下的双声道变换。研究采用无记忆性、线性性和左右交换对称性三个假设，利用全范围声像扫描辨识变换矩阵。四份实验音频均为 48 kHz、32 位浮点、8 s 双声道文件。结果表明，Audio Clip 对左右声道分别施加增益；Mixer 则在增益调整的同时，将另一侧输入混入声像偏转侧。本文给出四种情形仅以归一化声像位置 $p$ 为参数的完整矩阵公式。按采样时间建立名义线性扫描轨迹后，各输出的最大绝对残差均低于 $6.1\times10^{-5}$；消去声像参数后的 Mixer 左右输出关系残差低于 $8.5\times10^{-6}$。由所获公式进一步得到极端声像处的求和关系、同相双声道输入的功率规律，以及 Mixer Circular 在单侧输入下约 $+0.423\,\text{dB}$ 的内部幅度峰值。

**关键词：** FL Studio；panning law；声像法则；双声道变换；增益矩阵；直流测量

## 1. 官方说明与研究问题

### 1.1 官方文档对声像法则的描述

FL Studio 官方手册在 *Project General Settings* 的 “Panning law” 条目中说明，声像法则用于补偿声音从中央移动到两侧时的表观音量变化。关于两种设置，手册给出了以下描述 [1]：

> “Circular - Level compensation is applied when panning (orange). Level drops 3 dB at center pan.”

即 Circular 在声像变化时施加电平补偿，中心位置的电平比极端位置低约 3 dB。

> “Triangular - No level compensation is used as a function of pan position (green).”

即 Triangular 不随声像位置施加上述电平补偿。该条目还说明，其整体电平相对于 Circular 极端声像位置低约 3 dB。

手册随后专门说明了 Audio Clip 的电平基准 [1]：

> “in this case volume is being added at extremes instead of subtracted at the center position.”

即在这里，补偿体现为提高两端的电平。结合该段上下文：在默认 Channel Sampler 设置下，Audio Clip 的电平读数与录制电平相同，使用 Circular 时最多可以增加约 3 dB。因此，中心与两端的相对差异，需要结合实际信号路径的电平基准理解。

关于 Mixer 的声像控制，官方 *Mixer* 页面写道 [2]：

> “The pan works by mixing one side of the stereo track into the other, so a 100% pan is the mono-sum of the Left and Right channels.”

即 Mixer 通过将一侧立体声信号混入另一侧实现声像变化，全偏时得到左右声道的单声道求和。

这些说明给出了声像控制的用途、补偿幅度及 Mixer 的混合行为，但**没有给出增益随声像位置变化的具体公式，也没有给出双声道交叉混合系数的完整表达式**。仅凭中心与端点的电平关系，仍有多种连续函数可以满足要求。因此，要确定任意声像位置下的输出，必须通过实测辨识其变换规律。

### 1.2 研究范围

本研究比较以下四种组合：

| 控制位置                      | Circular            | Triangular            |
| ----------------------------- | ------------------- | --------------------- |
| Mixer Master 的 Panning       | Mixer Circular      | Mixer Triangular      |
| Audio Clip 的 Channel panning | Audio Clip Circular | Audio Clip Triangular |

实验使用 FL Studio 20.8.3.2304，研究两个问题：两类声像控制如何变换左右输入，以及 Circular / Triangular 设置如何改变该变换。

![FL Studio 项目声像法则设置](<images/FL Studio Panning Law Settings.png>)

**图 1. 项目声像法则设置。** “Panning law” 下拉菜单提供 Circular 和 Triangular 两个选项，构成本实验的一个控制因素。

## 2. 符号、假设与测量原理

### 2.1 输入、输出与声像参数

双声道音频由按时间排列的采样帧组成，每帧包含一个左声道样本和一个右声道样本。本文使用下列符号：

| 符号                                  | 定义                                                     |
| ------------------------------------- | -------------------------------------------------------- |
| $n$                                   | 从 0 开始的采样帧序号，$n=0,\ldots,N-1$                  |
| $N$                                   | 音频的总帧数                                             |
| $f_s$                                 | 采样率，单位 Hz                                          |
| $t_n=n/f_s$                           | 第 $n$ 帧对应的时间，单位 s                              |
| $x_{\text{L}}[n],x_{\text{R}}[n]$     | 第 $n$ 帧进入声像变换的左、右声道输入样本值              |
| $y_{\text{L}}[n],y_{\text{R}}[n]$     | 第 $n$ 帧经过声像变换的左、右声道输出样本值              |
| $\boldsymbol{x}[n],\boldsymbol{y}[n]$ | 将左右样本排列为列向量的输入、输出                       |
| $p$                                   | 归一化声像位置；$-1$ 为全左，$0$ 为居中，$1$ 为全右      |
| $p[n]$                                | 第 $n$ 帧采用的声像位置                                  |
| $A(p)$                                | 声像位置为 $p$ 时的 $2\times2$ 实数增益矩阵              |
| $A_{ij}(p)$                           | 从输入声道 $j$ 到输出声道 $i$ 的增益；1 表示左，2 表示右 |

上述样本值是数字音频幅度，本文以数值 1 为幅度参考。上标 $\top$ 表示转置，例如 $(1,0)^\top$ 表示由 1 和 0 组成的列向量。输入和输出向量具体写为

$$
\boldsymbol{x}[n]=
\begin{bmatrix}x_{\text{L}}[n]\\x_{\text{R}}[n]\end{bmatrix},
\qquad
\boldsymbol{y}[n]=
\begin{bmatrix}y_{\text{L}}[n]\\y_{\text{R}}[n]\end{bmatrix}.
\tag{1}
$$

### 2.2 三个建模假设

本研究采用以下三个假设：

1. **无记忆性：** 在给定声像位置时，当前输出由当前帧的左右输入决定。
2. **线性性：** 在给定声像位置时，输入的缩放和叠加对应于输出的相同缩放和叠加。
3. **左右交换对称性：** 同时交换输入、输出声道并反转声像方向，变换规律保持一致。

前两个假设使声像变换可以写成

$$
\boldsymbol{y}[n]=A(p[n])\boldsymbol{x}[n],
\qquad
A(p)=
\begin{bmatrix}
A_{11}(p)&A_{12}(p)\\
A_{21}(p)&A_{22}(p)
\end{bmatrix}.
\tag{2}
$$

展开式（2），有

$$
\begin{aligned}
y_{\text{L}}[n]&=A_{11}(p[n])x_{\text{L}}[n]+A_{12}(p[n])x_{\text{R}}[n],\\
y_{\text{R}}[n]&=A_{21}(p[n])x_{\text{L}}[n]+A_{22}(p[n])x_{\text{R}}[n].
\end{aligned}
\tag{3}
$$

因此，对角元素描述同侧增益，非对角元素描述跨声道混合。线性性针对音频输入；矩阵系数随声像参数 $p$ 的变化可以是非线性的。

令交换矩阵 $J$ 为

$$
J=\begin{bmatrix}0&1\\1&0\end{bmatrix},
$$

则第三个假设表示为

$$
A(-p)=J A(p)J.
\tag{4}
$$

### 2.3 左声道直流激励与矩阵重建

本实验使用恒定输入 $x_{\text{L}}[n]=1$、$x_{\text{R}}[n]=0$。在这一输入下，式（3）直接给出

$$
y_{\text{L}}[n]=A_{11}(p[n]),\qquad y_{\text{R}}[n]=A_{21}(p[n]).
\tag{5}
$$

换言之，输出样本直接读出矩阵第一列的两个增益系数。为表述测量结果，定义 $f(p)=A_{11}(p)$、$h(p)=A_{21}(p)$，分别表示左输入到左输出、左输入到右输出的增益。由式（4），可重建

$$
A(p)=
\begin{bmatrix}
f(p)&h(-p)\\
h(p)&f(-p)
\end{bmatrix}.
\tag{6}
$$

因此，将同一左声道直流信号从全左扫描到全右，便可得到完整双声道变换所需的信息。

## 3. 实验设计与数据处理

### 3.1 输入材料与控制位置

输入为双声道直流信号：左声道在全部帧上等于 1，右声道在全部帧上等于 0。图 2 展示该信号在音频编辑器中的波形。

![左声道单位直流输入](<images/Left Channel DC.png>)

**图 2. 输入测试信号。** 上方左声道保持单位正幅度，下方右声道保持零。右侧刻度为 dB 显示，红色水平线为零幅度参考。

Mixer 条件对 Master 轨道的 Panning 控件施加自动化，图 3 的自动化片段标为 “Master - Panning”。Audio Clip 条件对音频片段通道的声像控件施加自动化，图 4 中标为 “Left Channel DC - Channel panning”。

![Mixer 声像自动化设置](<images/FL Studio Mixer Panning.png>)

**图 3. Mixer 控制位置。** 自动化目标为 Mixer Master 的声像旋钮，播放列表中的直线覆盖测试音频的时间范围。

![Audio Clip 声像自动化设置](<images/FL Studio Audio Clip Panning.png>)

**图 4. Audio Clip 控制位置。** 自动化目标为音频片段通道设置中的 PAN 旋钮。实验中关闭 “Remove DC offset” 和 “Normalize”，保留输入直流及其幅度基准。

### 3.2 渲染设置与声像扫描

| 项目           | 设置或数值                   |
| -------------- | ---------------------------- |
| 输入、输出格式 | 双声道 WAV，IEEE 754 float32 |
| 采样率 $f_s$   | $48000\,\text{Hz}$           |
| 帧数 $N$       | $384000$                     |
| 时长 $T=N/f_s$ | $8\,\text{s}$                |
| 声像扫描       | 从全左到全右的线性自动化     |
| 实验组合       | 两类控制位置 × 两种声像法则  |
| 输出文件       | 每种组合一份，共四份         |

每种组合分别渲染为一份双声道音频，保留输出样本的浮点幅度，用于逐样本计算增益系数与残差。

为将样本序号转换为声像坐标，定义第 $n$ 帧的**名义声像位置** $\bar p_n$：

$$
\bar p_n=-1+\frac{2t_n}{T}
=-1+\frac{2n}{N},\qquad n=0,\ldots,N-1.
\tag{7}
$$

其中横线表示由实验时间轴指定的参数值。$n=192000$ 对应居中；最后一帧对应 $\bar p_{N-1}=1-2/N\approx0.999994792$。理论全右位置 $p=1$ 对应 8 s 处的区间边界。

### 3.3 残差定义

原始 float32 样本转换为 float64 后用于计算。对输出声道 $c$（$c=\text{L}$ 或 $\text{R}$），记 $\hat y_c(p)$ 为单位左声道输入时公式预测的输出，定义残差

$$
e_c[n]=y_c[n]-\hat y_c(\bar p_n).
\tag{8}
$$

使用最大绝对残差 $E_{\infty,c}$ 和残差均方根 $E_{\text{RMS},c}$ 衡量一致性：

$$
E_{\infty,c}=\max_n|e_c[n]|,\qquad
E_{\text{RMS},c}=
\sqrt{\frac1N\sum_{n=0}^{N-1}e_c[n]^2}.
\tag{9}
$$

全部 $384000$ 帧均参与统计，幅度以输入的单位幅度为参考。另按端点约定 $\bar p_n=-1+2n/(N-1)$ 计算残差，以检查时间坐标选择的影响。

## 4. 辨识结果：四种声像法则的完整公式

以下四个矩阵的元素均仅以 $p\in[-1,1]$ 为参数。将相应矩阵代入式（2），即可由左右输入计算左右输出。下标中的 Mixer、Clip 表示控制位置，Circ、Tri 分别表示 Circular 和 Triangular。

各情形的公式与输出波形如下。波形截图的上半部分为左声道，下半部分为右声道；横轴为时间，纵轴采用音频编辑器的 dB 显示。

### 4.1 Mixer × Circular

$$
A_{\text{Mixer,Circ}}(p)=
\begin{cases}
\begin{bmatrix}
\dfrac{\cos\!\left(\frac{\pi(p+1)}4\right)
 \left[1+\sqrt2\sin\!\left(\frac{\pi(p+1)}4\right)\right]}{\sqrt2}
&
\dfrac{\cos\!\left(\frac{\pi(p+1)}4\right)
 \left[1-\sqrt2\sin\!\left(\frac{\pi(p+1)}4\right)\right]}{\sqrt2}
\\[6pt]
0&\sqrt2\sin\!\left(\frac{\pi(p+1)}4\right)
\end{bmatrix},
&-1\le p\le0,\\[14pt]
\begin{bmatrix}
\sqrt2\cos\!\left(\frac{\pi(p+1)}4\right)&0\\[6pt]
\dfrac{\sin\!\left(\frac{\pi(p+1)}4\right)
 \left[1-\sqrt2\cos\!\left(\frac{\pi(p+1)}4\right)\right]}{\sqrt2}
&
\dfrac{\sin\!\left(\frac{\pi(p+1)}4\right)
 \left[1+\sqrt2\cos\!\left(\frac{\pi(p+1)}4\right)\right]}{\sqrt2}
\end{bmatrix},
&0<p\le1.
\end{cases}
\tag{10}
$$

左偏时，右输入通过第一行第二列的系数混入左输出；右偏时，左输入通过第二行第一列的系数混入右输出。实测左输入响应在左偏区间出现内部幅度极大值，右输出在右偏区间逐渐增大。

![Mixer Circular 原始输出](<images/Mixer Circular Panning.png>)

**图 5. Mixer Circular 的输出波形。** 左输出先升后降，在居中之前略高于单位幅度；右输出从扫描中点之后增加，接近全右时约为 −3 dB。

### 4.2 Mixer × Triangular

$$
A_{\text{Mixer,Tri}}(p)=
\begin{cases}
\begin{bmatrix}
1+\dfrac p2&-\dfrac p2\\[4pt]
0&1+p
\end{bmatrix},
&-1\le p\le0,\\[12pt]
\begin{bmatrix}
1-p&0\\[4pt]
\dfrac p2&1-\dfrac p2
\end{bmatrix},
&0<p\le1.
\end{cases}
\tag{11}
$$

这一变换具有相同方向的交叉混合结构，所有非零系数均为分段线性函数。对单位左输入，左偏时左输出为 $1+p/2$；右偏时左右输出分别为 $1-p$ 和 $p/2$。

![Mixer Triangular 原始输出](<images/Mixer Triangular Panning.png>)

**图 6. Mixer Triangular 的输出波形。** 左输出从约 −6 dB 增至居中的 0 dB，再下降；右输出在右半段增加，末端接近 −6 dB。

### 4.3 Audio Clip × Circular

$$
A_{\text{Clip,Circ}}(p)=
\begin{bmatrix}
\sqrt2\cos\!\left(\dfrac{\pi(p+1)}4\right)&0\\[6pt]
0&\sqrt2\sin\!\left(\dfrac{\pi(p+1)}4\right)
\end{bmatrix},
\qquad -1\le p\le1.
\tag{12}
$$

两个声道分别乘以正弦或余弦增益。左声道输入在全左处获得 $\sqrt2$ 倍增益，居中处为单位增益，全右处为零。

![Audio Clip Circular 原始输出](<images/Audio Clip Circular Panning.png>)

**图 7. Audio Clip Circular 的输出波形。** 左输出从约 +3 dB 逐渐下降，右输出保持为零。

### 4.4 Audio Clip × Triangular

$$
A_{\text{Clip,Tri}}(p)=
\begin{cases}
\begin{bmatrix}1&0\\0&1+p\end{bmatrix},
&-1\le p\le0,\\[8pt]
\begin{bmatrix}1-p&0\\0&1\end{bmatrix},
&0<p\le1.
\end{cases}
\tag{13}
$$

偏转侧的同侧增益保持为 1，另一侧随声像位置线性衰减。对单位左输入，左输出在左半区保持为 1，在右半区线性降至零。

![Audio Clip Triangular 原始输出](<images/Audio Clip Triangular Panning.png>)

**图 8. Audio Clip Triangular 的输出波形。** 左输出在前半段保持 0 dB，后半段下降；右输出保持为零。

### 4.5 响应对比与结构总结

![四种声像法则的实测响应与解析公式](images/figures/01-response.png)

**图 9. 单位左声道输入的输出响应。** 蓝色和橙色分别表示左、右输出；实线为式（10）—（13）的计算结果，空心符号为均匀选取的 61 个实测样本。横坐标使用式（7）的名义声像位置。原始输出波形见图 5—8。

两份 Audio Clip 输出的右声道在全部帧上均为数值零；两份 Mixer 输出的右声道在右半段出现信号。两类控制的核心区别是：**Audio Clip 分别调整两侧增益，Mixer 将另一侧输入混入声像偏转侧。**

![四种声像法则的矩阵系数](images/figures/02-matrix.png)

**图 10. 完整矩阵的四个系数。** 实线为通过左声道激励辨识的第一列，虚线为按式（6）补全的第二列。蓝色表示同侧增益，橙色表示交叉混合增益；部分零系数曲线重合。

四种公式均在居中处满足 $A(0)=I$，其中 $I$ 为 $2\times2$ 单位矩阵。因此，居中时输出逐声道等于输入。

## 5. 定量验证

### 5.1 全范围逐样本残差

按式（7）—（9）计算，得到表 1。

**表 1. 四种声像法则的前向残差。**

| 条件                  |   左输出最大绝对残差 |           左输出 RMS |   右输出最大绝对残差 |           右输出 RMS |
| --------------------- | -------------------: | -------------------: | -------------------: | -------------------: |
| Mixer Circular        | $6.074\times10^{-5}$ | $2.369\times10^{-5}$ | $5.030\times10^{-5}$ | $1.533\times10^{-5}$ |
| Mixer Triangular      | $5.360\times10^{-5}$ | $2.345\times10^{-5}$ | $2.677\times10^{-5}$ | $1.051\times10^{-5}$ |
| Audio Clip Circular   | $5.826\times10^{-5}$ | $2.372\times10^{-5}$ |                  $0$ |                  $0$ |
| Audio Clip Triangular | $5.363\times10^{-5}$ | $2.122\times10^{-5}$ |                  $0$ |                  $0$ |

使用首末帧覆盖双端点的坐标约定时，四种条件的左输出最大绝对残差依次为 $6.464\times10^{-5}$、$5.732\times10^{-5}$、$6.366\times10^{-5}$ 和 $5.732\times10^{-5}$。两种约定得到相同的误差量级。

![全范围残差与局部波形](images/figures/03-residual.png)

**图 11. 实测值减去公式预测值。** 左列将所有样本划分为 800 个连续区间，绘制每个区间的最小—最大残差包络及其上下界中点；右列显示前 100 ms 的全部样本。各子图独立设置纵轴范围，单位为 $10^{-6}$。包络保留各区间极值，局部波形展示残差的时间结构。

### 5.2 消去声像参数的输出关系检验

对于 Mixer 的右偏区间，可以消去 $p$，直接检验同一帧左右输出之间的关系。这样，公式的检验只需使用输出幅度。

对 Mixer Circular，式（10）给出

$$
\hat y_{\text{R}}=
\frac{(1-y_{\text{L}})\sqrt{2-y_{\text{L}}^2}}2.
\tag{14}
$$

对 Mixer Triangular，式（11）给出

$$
\hat y_{\text{R}}=\frac{1-y_{\text{L}}}{2}.
\tag{15}
$$

这里 $y_{\text{L}}$ 是同一帧的实测左输出，$\hat y_{\text{R}}$ 是由该左输出预测的右输出。令关系残差 $r=y_{\text{R}}-\hat y_{\text{R}}$，在全部名义 $p>0$ 的 $191999$ 帧上得到：

**表 2. Mixer 左右输出关系的残差。**

| 条件                       |         最大绝对残差 |                  RMS |
| -------------------------- | -------------------: | -------------------: |
| Mixer Circular，式（14）   | $8.411\times10^{-6}$ | $1.906\times10^{-6}$ |
| Mixer Triangular，式（15） | $3.770\times10^{-6}$ | $1.064\times10^{-6}$ |

![Mixer 左右输出关系检验](images/figures/04-identity.png)

**图 12. 消去声像参数后的输出关系。** 左列实线为式（14）或式（15），空心符号为 61 对实测输出；右列直方图包含所有右偏样本的关系残差。

输出关系残差较前向残差减小，说明声像时间坐标对前向误差具有影响，同时表明左右输出之间满足所辨识的函数关系。图 11 中残差呈现结构性变化，与控制参数更新、插值及有限精度计算等机制相容。

float32 在 $[1,2)$ 区间的相邻数间距为 $2^{-23}\approx1.192\times10^{-7}$，在 $[0.5,1)$ 区间为 $2^{-24}\approx5.960\times10^{-8}$。表 1 的残差高于单位幅度附近单次存储舍入的量级，反映的是扫描轨迹与整个处理过程的综合差异。

## 6. 声像变换的性质

### 6.1 极端声像处的输出

令 $k$ 表示端点增益常数：Circular 对应 $k=\sqrt2$，Triangular 对应 $k=1$。四个公式在端点可归纳为

$$
A_{\text{Mixer}}(-1)=\frac{k}{2}
\begin{bmatrix}1&1\\0&0\end{bmatrix},
\qquad
A_{\text{Mixer}}(1)=\frac{k}{2}
\begin{bmatrix}0&0\\1&1\end{bmatrix},
\tag{16}
$$

$$
A_{\text{Clip}}(-1)=
\begin{bmatrix}k&0\\0&0\end{bmatrix},
\qquad
A_{\text{Clip}}(1)=
\begin{bmatrix}0&0\\0&k\end{bmatrix}.
\tag{17}
$$

因此，Mixer 全偏时，偏转侧输出为左右输入的加权和：Circular 为 $(x_{\text{L}}+x_{\text{R}})/\sqrt2$，Triangular 为 $(x_{\text{L}}+x_{\text{R}})/2$。这给出了官方 “mono-sum” 描述中的具体比例系数。Audio Clip 全偏时，偏转侧输出为该侧原输入的 $k$ 倍。

对于左右反相输入 $(s,-s)^\top$，其中 $s$ 为任意瞬时样本值，Mixer 全偏时两侧输入在求和中抵消；Audio Clip 则保留偏转侧的输入分量。

**表 3. 单位左输入的模型端点与实测边界样本。**

| 条件                  | 公式在 $p=-1$ 的输出 $(y_{\text{L}},y_{\text{R}})$ | 实测首帧          | 公式在 $p=1$ 的输出 $(y_{\text{L}},y_{\text{R}})$ | 实测末帧                              |
| --------------------- | -------------------------------------------------- | ----------------- | ------------------------------------------------- | ------------------------------------- |
| Mixer Circular        | $(0.707106781,0)$                                  | $(0.707106709,0)$ | $(0,0.707106781)$                                 | $(5.556781\times10^{-6},0.707104146)$ |
| Mixer Triangular      | $(0.5,0)$                                          | $(0.499999881,0)$ | $(0,0.5)$                                         | $(4.999208\times10^{-6},0.499998212)$ |
| Audio Clip Circular   | $(1.414213562,0)$                                  | $(1.414212704,0)$ | $(0,0)$                                           | $(5.554710\times10^{-6},0)$           |
| Audio Clip Triangular | $(1,0)$                                            | $(0.999999821,0)$ | $(0,0)$                                           | $(5.000166\times10^{-6},0)$           |

末帧的名义位置为 $1-2/N$；表中分别列出理论端点与采样边界，便于比较。

### 6.2 同相双声道输入的功率关系

对于左右相同的输入 $\boldsymbol{x}=(s,s)^\top$，两类声像控制在相同声像法则下得到相同输出。Circular 为

$$
\boldsymbol{y}=
\begin{bmatrix}
\sqrt2\cos\!\left(\dfrac{\pi(p+1)}4\right)s\\[4pt]
\sqrt2\sin\!\left(\dfrac{\pi(p+1)}4\right)s
\end{bmatrix};
\tag{18}
$$

Triangular 为

$$
\boldsymbol{y}=
\begin{cases}
\begin{bmatrix}s\\(1+p)s\end{bmatrix},&-1\le p\le0,\\[6pt]
\begin{bmatrix}(1-p)s\\s\end{bmatrix},&0<p\le1.
\end{cases}
\tag{19}
$$

定义输入、输出的瞬时双声道平方和分别为 $Q_x=x_{\text{L}}^2+x_{\text{R}}^2$、$Q_y=y_{\text{L}}^2+y_{\text{R}}^2$。对这些平方量作时间平均即得到相应数字信号的均方功率。Circular 满足

$$
Q_y=2s^2=Q_x,
\tag{20}
$$

即对同相同幅双声道输入保持功率。Triangular 对应

$$
\frac{Q_y}{Q_x}=
\frac{1+(1-|p|)^2}{2},\qquad s\ne0,
\tag{21}
$$

从中心的 1 降至端点的 $1/2$。

对单侧输入 $(1,0)^\top$，输出平方和为 $f(p)^2+h(p)^2$，随声像位置变化，如图 13(b)。对于一般双声道输入，Mixer 的交叉混合还使输出功率依赖左右输入的相关性。

### 6.3 Mixer Circular 的内部幅度峰值

对单位左输入，在 $p\in[-1,0]$ 区间定义角变量 $\theta=\pi(p+1)/4$，因此 $\theta\in[0,\pi/4]$。由式（10），左输出可写为

$$
f(\theta)=\frac{\sqrt2\cos\theta+\sin2\theta}{2}.
\tag{22}
$$

对 $\theta$ 求导，驻点满足

$$
\frac{\mathrm{d}f}{\mathrm{d}\theta}=0
\iff 2\cos2\theta=\sqrt2\sin\theta
\iff 4\sin^2\theta+\sqrt2\sin\theta-2=0.
$$

记极大值处的角变量和声像位置分别为 $\theta_*$、$p_*$，则

$$
\sin\theta_*=\frac{\sqrt{34}-\sqrt2}{8},
\qquad
p_*=\frac4\pi\arcsin\!\left(\frac{\sqrt{34}-\sqrt2}{8}\right)-1
\approx-0.255318408.
\tag{23}
$$

该点二阶导数为负；结合两端值可得最大幅度

$$
f_{\max}=\frac{\sqrt{142+34\sqrt{17}}}{16}
\approx1.049898788,
\qquad
20\log_{10}f_{\max}\approx0.422949\,\text{dB}.
\tag{24}
$$

实测 Mixer Circular 左输出最大值为 $1.049898863$，与式（24）相差约 $7.443\times10^{-8}$。该峰值位于全左与居中之间，构成这一组合的局部电平凸起。

Audio Clip Circular 的最大左声道增益位于全左端点，为 $\sqrt2$，对应 $+3.010300\,\text{dB}$，与官方所述端点约增加 3 dB 一致。浮点音频可以保存这些超过单位幅度的样本；最终输出的削波情况取决于后续处理和编码范围。

![功率关系与内部峰值](images/figures/05-consequences.png)

**图 13. 由声像公式计算的功率与峰值特征。** (a) 同相同幅双声道输入的输出／输入平方和之比；(b) 单位左输入的输出平方和；(c) Mixer Circular 左偏区间的幅度极大值。

### 6.4 与官方说明的对应关系

| 官方描述                           | 本研究给出的定量结果                                                                      |
| ---------------------------------- | ----------------------------------------------------------------------------------------- |
| Circular 中心与两端相差约 3 dB [1] | 同相同幅输入下，中心每侧增益为 1，端点活动声道增益为 $\sqrt2$，相差 $3.010300\,\text{dB}$ |
| Audio Clip 在两端增加电平 [1]      | 式（12）在中心为单位增益，在活动侧端点为 $\sqrt2$ 倍增益                                  |
| Triangular 使用无补偿模式 [1]      | 式（13）保持偏转侧单位增益，另一侧线性衰减；同相双声道输入的总功率按式（21）变化          |
| Mixer 将一侧混入另一侧 [2]         | 式（10）、（11）的非对角元素给出交叉混合的具体系数                                        |
| Mixer 全偏时为左右单声道求和 [2]   | 式（16）给出 Circular 的 $1/\sqrt2$ 与 Triangular 的 $1/2$ 求和比例                       |

## 7. 结论

本实验得到了 FL Studio 20.8.3.2304 四种声像控制情形的完整双声道变换：Mixer Circular 由式（10）给出，Mixer Triangular 由式（11）给出，Audio Clip Circular 由式（12）给出，Audio Clip Triangular 由式（13）给出。四个公式均以声像位置 $p$ 为唯一控制参数，可直接用于计算左右输入到左右输出的变换。

两类控制的结构区别在于交叉混合：Audio Clip 分别改变两声道增益；Mixer 将另一侧信号混入偏转侧，并在极端声像处形成加权单声道和。Circular 与 Triangular 分别采用三角函数和分段线性系数。它们在居中处均保持输入，在同相同幅双声道输入下表现出相同控制位置间的等价性。

逐样本比较与消参关系检验共同支持上述公式：全范围前向最大绝对残差低于 $6.1\times10^{-5}$，Mixer 输出关系最大绝对残差低于 $8.5\times10^{-6}$。公式进一步解释了 Circular 的功率补偿、Mixer 全偏求和的比例，以及 Mixer Circular 单侧输入响应中的 $+0.423\,\text{dB}$ 内部峰值，补全了官方定性说明所缺少的具体变换关系。

## 8. 局限与后续验证

本研究使用每种条件一次、单一幅度的左声道直流扫描。无记忆性、线性性和左右交换对称性作为建模假设，分别可通过宽带或脉冲输入、多幅度与叠加输入、右声道独立输入进一步验证。直流测量直接约束零频响应，推广到一般音频时可用固定声像的宽带测量检查频率响应与延迟。

前向残差同时包含公式近似和实际控制轨迹相对于名义时间轴的差异。本实验使用线性自动化扫描；固定声像平台以及改变扫描速度与采样率的对照实验，有助于分离这些误差来源。本文报告描述性残差统计，独立重复渲染可进一步评估重复性。

实测控制对象为 Mixer Master 和 Audio Clip Channel panning；其他轨道路由、插件通道及软件版本可使用相同方法复测。所引用在线手册为 2026-10-25 查阅的版本。输入—输出公式描述外部变换关系，软件内部运算顺序仍需实现层面的证据。

实验数据与分析代码见文献 [3]。

## 参考文献

[1] Image-Line. *FL Studio Online Manual: Project General Settings*, “Panning law”. [官方页面](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/songsettings_settings.htm#Panning_Law). 查阅日期：2026-10-25。

[2] Image-Line. *FL Studio Online Manual: Mixer*, “Panning”. [官方页面](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/mixer.htm). 查阅日期：2026-10-25。

[3] BiologyHazard. *FL Studio Panning Law*. [代码仓库](https://github.com/BiologyHazard/fl-studio-panning-law).
