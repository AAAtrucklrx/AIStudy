# 第1–4章教材正文重写记录

交付文件：`lessons-CH01-04.json`。31个单元逐项读过 `data/parse/complex-analysis-v2/chapters.json` 指向的原文，再按同一知识顺序连续重写。正文不复制原有概念卡模板；必要先修在首次使用处补回。章导论约360–397个汉字，实质单元至少800个汉字（包括已保留的例题链接文字），公式另计。

旧阅读包只用JSON解析读取，没有执行data.js；例题、正式证明链接沿用原reader块锚点。20幅可操作图均由实际chooseScene(model_title, "")连同两扩展provider验证kind，公式字段使用所画模型的LaTex。6段媒体的request_id及各step_id逐项对照旧数据，自然讲稿直接合并配音代理给出的neural-authored-steps.json。

## 来源与逐节教学处理

| 单元 | 实际来源文件 | SHA256前12位 | 正文取舍与连接 |
|---|---|---|---|
| CH01 | `data/parse/complex-analysis-v2/original_text/ch01.md` | `46a81a9284a0` | 由实数扩展动机接上代数、几何、极限与点集，建立全章路线。 |
| CH01-S01-SS01 | `data/parse/complex-analysis-v2/original_text/ch01_s01_ss01.md` | `1a282e5d8f6c` | 虚单位与两实分量；从多项式展开得到四则；完整分母共轭、非零条件与验算。 |
| CH01-S01-SS02 | `data/parse/complex-analysis-v2/original_text/ch01_s01_ss02.md` | `1ffc933c252c` | 共轭作实虚部分离与实数判别；约去因子前检查非零；复根共轭成对。 |
| CH01-S01-SS03 | `data/parse/complex-analysis-v2/original_text/ch01_s01_ss03.md` | `7160b974330e` | 点向量与极式；主值区间、零无辐角；距离、模不等式与旋转伸缩。 |
| CH01-S01-SS04 | `data/parse/complex-analysis-v2/original_text/ch01_s01_ss04.md` | `a57b94415de3` | 从重复旋转到德莫弗；先保留整圈再除n；根的正多边形分布与完整性检查。 |
| CH01-S01-SS05 | `data/parse/complex-analysis-v2/original_text/ch01_s01_ss05.md` | `774df9ed570d` | epsilon-N量词与全部尾项；坐标判别；连续选角并区别主值跳跃；唯一无穷远点。 |
| CH01-S02-SS01 | `data/parse/complex-analysis-v2/original_text/ch01_s02_ss01.md` | `ef46c1cc04f1` | 邻域统摄内外边界；存在一个与每个的量词区别；开闭与有界相互独立。 |
| CH01-S02-SS02 | `data/parse/complex-analysis-v2/original_text/ch01_s02_ss02.md` | `7fd08b955b34` | 开放加折线连通；参数曲线、无重点与约当；去心邻域区分连通和单连通。 |
| CH02 | `data/parse/complex-analysis-v2/original_text/ch02.md` | `b59d752e0faf` | 从平面映照到任意方向复微分，再到初等多值函数的章内路线。 |
| CH02-S01 | `data/parse/complex-analysis-v2/original_text/ch02_s01.md` | `7230a836ff70` | 输入输出分工、两个平面、像与原像、单值与一一、像集的方程及参数范围。 |
| CH02-S02 | `data/parse/complex-analysis-v2/original_text/ch02_s02.md` | `a909d3e7524f` | epsilon-delta统一覆盖所有路径；两路径否定与距离估计证明；主值辐角的连续域。 |
| CH02-S03 | `data/parse/complex-analysis-v2/original_text/ch02_s03.md` | `a0b527429bc2` | 差商任意方向统一；一阶复乘法与高阶余项；单点可微和邻域解析；求导法则条件。 |
| CH02-S04 | `data/parse/complex-analysis-v2/original_text/ch02_s04.md` | `c5d7db772576` | 两方向候选导数推出C-R；实二元可微假设；偏导连续的实用充分保证；孤立可微不解析。 |
| CH02-S05 | `data/parse/complex-analysis-v2/original_text/ch02_s05.md` | `d74508ec0030` | 一一解析定义单叶；把定义域限制与单值反函数的生成因果接清。 |
| CH02-S05-SS01 | `data/parse/complex-analysis-v2/original_text/ch02_s05_ss01.md` | `1e7fecfe8062` | 同像的模与角条件；张角不超过2pi/n的开角域；像域覆盖与反向根式。 |
| CH02-S05-SS02 | `data/parse/complex-analysis-v2/original_text/ch02_s05_ss02.md` | `44dfd88ba66c` | 沿路连续选角而非重置主值；零和无穷远支点；切口两岸；复合根式的支点重新判断。 |
| CH02-S05-SS03 | `data/parse/complex-analysis-v2/original_text/ch02_s05_ss03.md` | `9366e89d3163` | 实部控制模与虚部控制角；全平面整函数但不一一；虚周期与水平带映照。 |
| CH02-S05-SS04 | `data/parse/complex-analysis-v2/original_text/ch02_s05_ss04.md` | `1762f979ebb5` | 指数反解；主值与解析支区别；切口与水平带；积法则的值集合含义及反例。 |
| CH02-S05-SS05 | `data/parse/complex-analysis-v2/original_text/ch02_s05_ss05.md` | `0385a9981ee7` | 指数定义；整函数与实周期；复平方而非模平方恒等式；无界、零点及商的排除点。 |
| CH02-S05-SS06 | `data/parse/complex-analysis-v2/original_text/ch02_s05_ss06.md` | `69ccb59d220c` | 指数定义与三角旋转联系；导数、双曲恒等式；商的正确分母零点与虚周期。 |
| CH02-S05-SS07 | `data/parse/complex-analysis-v2/original_text/ch02_s05_ss07.md` | `5e70fd27b5ef` | 统一exp(alpha Ln z)定义；因子重复判据；整数、有理、无理及非实指数；单值exp记号区别。 |
| CH02-S05-SS08 | `data/parse/complex-analysis-v2/original_text/ch02_s05_ss08.md` | `1cabff334063` | 指数换元成二次方程，再经开方对数反解；多值根号与正负号；反函数分支和排除点。 |
| CH03 | `data/parse/complex-analysis-v2/original_text/ch03.md` | `0eb2b9b65d4a` | 从小段方向累积到解析性消除路径依赖，再到边界读出内部与导数。 |
| CH03-S01 | `data/parse/complex-analysis-v2/original_text/ch03_s01.md` | `09395897184f` | 采样乘复增量；实线积分来由；参数化两处替换、方向与长度区别；ML及收缩弧反例。 |
| CH03-S02 | `data/parse/complex-analysis-v2/original_text/ch03_s02.md` | `837bafb9234b` | 闭路与路径无关；内部解析假设；格林与C-R动机；复闭路左右区域方向和辅助线抵消。 |
| CH03-S03 | `data/parse/complex-analysis-v2/original_text/ch03_s03.md` | `68e1f95c0b29` | 变上限积分需先单值；原函数加复常数；牛莱条件；1/z绕行与对数支的同一障碍。 |
| CH03-S04 | `data/parse/complex-analysis-v2/original_text/ch03_s04.md` | `7cd186910ad5` | 固定读值点和边界变量分工；挖小圆与核读值；高阶导数阶乘；例6路径过奇点校正。 |
| CH03-S05 | `data/parse/complex-analysis-v2/original_text/ch03_s05.md` | `a1f37bfe38a5` | 平均权重；最大模的常数及边界条件；Cauchy界依R变化；Liouville统一界；FTA；Morera所有闭路。 |
| CH04 | `data/parse/complex-analysis-v2/original_text/ch04.md` | `038438c5a137` | 由C-R的二阶相消进入调和函数；边界值问题的意义与唯一性不等于存在性。 |
| CH04-S01 | `data/parse/complex-analysis-v2/original_text/ch04_s01.md` | `06ab8bcf2ad6` | 拉普拉斯方程与鞍面；共轭调和不等同复数共轭；非临界正交；单连通构造及积分常数函数。 |
| CH04-S02 | `data/parse/complex-analysis-v2/original_text/ch04_s02.md` | `28d454880949` | 实值平均与双向极值；泊松核各符号和权重；明确cos(nt)数据；狄氏稳定、唯一和广义边界。 |

## 原文录入问题的处理

- 1.1.1的z乘共轭识别式和除法分母按标准平方和还原；不重复原文排印中错误的共轭范围。
- 1.1.2例2条件应为z不等于正负i而非实变量y不等于正负i；例3分母使用(1-x)平方加y平方。正文解释原分母非零与约去因子条件，折叠原有例题已含修正。
- 1.1.3只在非零且同向时讨论相应等号条件，正文不复制原文不严谨的零向量辐角说法。
- 1.1.4及2.5.1/2.5.2的OCR中n、3、5、6混用，统一还原一般n次根；各分支按k增加时乘exp(2pi i/n)写出。
- 2.5.3指数定义恢复e的z次幂；无穷远无统一极限不被当作一个可直接代入点。
- 2.5.6原文把tanh和coth的排除点对调，正文依各自分母得到正确零点。
- 2.5.7原文一般幂例子有i的i次幂、2的1+i次幂等OCR误识，正文按定义给出i的i次幂的正实值族。
- 3.2原文部分零积分公式缺失，正文补回定理结论；复闭路统一说明外逆时针、内顺时针，与各内圈另取逆时针记号的公式区别。
- 3.4例6原半径2使z=0位于路径，普通积分无定义；正文明确说明并链接旧包已改为0<r<2的折叠例题，不静默套公式。
- 4.1构造共轭的v_y应等于u_x，原文推导负号误写；同时避免复制“多连通必多值”的过强说法，改为全局共轭可能失败、看实际绕行积分。

## 验证证据

- 先写专属验证并运行，初始因目标教材文件尚不存在而失败。追加图formula契约与实际registry匹配后，再观察到缺formula和两个错误title分类的失败，随后修正。
- `python3 -m unittest tests.test_textbook_lessons_ch01_04 -v`：2项通过，内含31节来源、正文长度、旧锚点、marker独立行及前后解释、20幅图的模型分类、6个媒体ID和33个自然讲稿step的对应、LaTex美元定界符配对。
- 全量用相邻`.venv-linux`运行pytest时，因并行中的`tests/test_revise_textbook_reader.py`引用当时尚未新增的`tools.revise_textbook_reader`而在收集阶段失败；已告知主代理，未修改其他代理文件。系统python没有pytest，故专属测试用标准库unittest也能独立复查。
- 自动检查保证结构与来源身份，不声称能替代数学和教学审阅；逐节内容和已识别OCR修正经过人工式交叉检查。
