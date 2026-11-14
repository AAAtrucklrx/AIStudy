import json,re,copy,pathlib,hashlib
R=pathlib.Path(__file__).resolve().parents[3]
D=R/'data/study-revision-20261029'
original={}
for fn in ['lessons-CH01-04.json','lessons-CH05-09.json']:
 for k,v in json.loads((D/fn).read_text())['units'].items():
  if k.startswith(('CH04','CH05','CH06')):original[k]=v
conclusions=json.loads((D/'conclusions-CH04-06.json').read_text())['units']
units={}; review={}; current=None; paragraphs=[]; bindings={}
def unit(uid,bridge):
 global current,paragraphs,bindings
 if current:finish()
 current=uid;paragraphs=[];bindings={};units[uid]=copy.deepcopy(original[uid]);units[uid]['next_bridge']=bridge
 review[uid]={'source_path':conclusions[uid]['source_path'],'source_read':'完整通读本单元原文，包括例题及章末习题；按conclusions主表与补表逐ID核对。','knowledge_ids':[],'understanding_bridges':[],'media_review':[],'pending_items':[]}
def p(text,ids=''):
 text=text.strip(); assert '\n\n' not in text, text[:100]
 paragraphs.append(text)
 if ids:
  for ident in ids.split():
   full=current+'-'+ident if re.match(r'^(?:C|SC)\d+$',ident) else ident
   bindings.setdefault(full,[]).append(text)
def bridge(s):review[current]['understanding_bridges'].append(s)
def finish():
 b='\n\n'.join(paragraphs)
 # Preserve old reader targets; existing inline links stay at their explanatory positions.
 oldlinks=re.findall(r'\[[^\]]*\]\(#reader-[^)]*\)',original[current]['body_markdown'])
 missing=[x for x in oldlinks if x not in b]
 if missing:b+='\n\n完整证明、逐步演算和原题保留在折叠资料：'+'、'.join(missing)+'。'
 expected=[x['id'] for x in conclusions[current].get('conclusions',[])+conclusions[current].get('supplementary_conclusions',[])]
 assert set(expected)==set(bindings),(current,set(expected)-set(bindings),set(bindings)-set(expected))
 units[current]['body_markdown']=b
 units[current]['knowledge_coverage']=[{'id':x,'excerpts':bindings[x]} for x in expected]
 review[current]['knowledge_ids']=expected
 review[current]['body_paragraphs']=len(b.split('\n\n'))
 source=R/conclusions[current]['source_path']
 review[current]['source_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
 review[current]['source_line_count']=len(source.read_text().splitlines())

unit('CH04','先从两个分量之间的一阶关系，理解调和方程与共轭函数的来由。')
p(r'''此前研究解析函数时，实部和虚部总被放在同一个复函数里。本章把一个分量单独拿出来：平面稳定温度、静电势等模型只需要实数值，却仍受解析函数理论的约束。我们先弄清这种约束是什么，再问只知道其中一个分量能否恢复另一个。''')
p(r'''第二个问题从“已知一个分量”走向“只知边界”：边缘温度如何决定内部温度，边界测量误差又会怎样传入内部？圆盘上将有具体的积分构造，一般有界区域上则先讨论解的唯一性和稳定性。把构造、唯一性和误差控制分清，才能知道每条结论实际解决了哪一部分问题。''')
bridge('把解析函数的实虚部约束连接到实值平面场；以边界温度区分存在性、唯一性和稳定性。')

unit('CH04-S01','共轭构造把调和函数接入解析理论，随后用这条联系研究平均、极值和边界值。')
p(r'''写成 $f(z)=u(x,y)+\mathrm i v(x,y)$ 后，解析性首先表现为 C-R 方程 $u_x=v_y$、$u_y=-v_x$。解析函数有各阶连续导数，所以两式还能继续求偏导；混合偏导相等使相反项消去，得到
$$\Delta u:=u_{xx}+u_{yy}=0,\qquad\Delta v=v_{xx}+v_{yy}=0.$$
这里下标表示偏导，$\Delta$ 是二维拉普拉斯算子。具有二阶连续偏导并满足 $\Delta u=0$ 的实函数叫调和函数。这个定义要求两个方向的弯曲相抵，并不要求曲面平坦：$x^2-y^2$ 调和，而 $x^2+y^2$ 不调和。推演见[解析函数分量的调和性](#reader-451cfb7e6d389d16983c)。''','C001 C002')
p(r'''两个调和函数若还满足上述 C-R 方程，就构成一对共轭调和函数，组合 $u+\mathrm i v$ 解析。因此每个解析函数的实部、虚部都是共轭调和的；反过来只检验两者各自调和还不够，必须核对它们之间的偏导联系。“共轭”在这里指配对关系。''','C002 C003')
p(r'''当交点处 $f'(z)\ne0$，等值线 $u=K_1$ 与 $v=K_2$ 的切线互相垂直：C-R 使法向量 $\nabla u$ 与 $\nabla v$ 垂直，导数非零保证这些法向量不消失。在[例1（$z^2$ 的共轭调和函数与等值曲线）](#reader-f1bcd15721b354574c2c)中，$u=x^2-y^2$、$v=2xy$ 给出两族双曲线；原点处 $f'=0$，不能在那里直接引用正交结论。''','C004')
p(r'''右侧模型实际显示 $u=c(x^2-y^2)$ 的鞍面和金色等值线 $u=\text{常数}$。调节正系数 $c$，比较沿两个坐标方向的弯曲：$u_{xx}=2c$ 与 $u_{yy}=-2c$ 始终相抵。移动等值高度只换选中的水平截线；共轭等值线的正交关系由上段的两组方程判断。''')
p('[[TEACHING_VISUAL:CH04-harmonic]]')
p(r'''现在给定实部 $u$，C-R 已经规定需要补出的偏导：$v_x=-u_y$、$v_y=u_x$。若 $u$ 在单连通区域 $D$ 内调和，固定基点 $(x_0,y_0)$，则
$$v(x,y)=\int_{(x_0,y_0)}^{(x,y)}\bigl(-u_y\,\mathrm dx+u_x\,\mathrm dy\bigr)+C_2,\qquad C_2\in\mathbb R.$$
调和性保证这份微分局部相容，单连通性保证在 $D$ 内换路不改积分，因此所得 $v$ 全域单值，$u+\mathrm i v$ 解析。自由常数只加在虚部上，所以同一实部对应的解析函数相差纯虚常数。''','C005')
p(r'''若给定的是调和虚部 $v$，同一思路改为
$$u(x,y)=\int_{(x_0,y_0)}^{(x,y)}\bigl(v_y\,\mathrm dx-v_x\,\mathrm dy\bigr)+C_1,\qquad C_1\in\mathbb R.$$
这次解析函数相差实常数。[例2（由虚部构造解析函数）](#reader-b8b008ca7d0443bacae7)给定 $v=2x^2-2y^2+x$，先积 $u_x=-4y$ 得 $u=-4xy+\varphi(y)$，再用 $u_y=-(4x+1)$ 求出 $\varphi(y)=-y+C_1$。于是 $f(z)=2\mathrm iz^2+\mathrm iz+C_1$，由 $f(0)=1$ 得 $C_1=1$。偏导积分中的“常数”先保留为另一变量的函数，是避免漏解的关键。''','C006')
p(r'''区域有洞时，调和性仍保证局部共轭，却未必保证全域单值；准确条件是每条闭路上的相应微分积分都为零。比如 $u=\ln|z|$ 在 $z\ne0$ 调和，沿单位圆累积 $-u_y\,\mathrm dx+u_x\,\mathrm dy$ 得 $2\pi$，绕一圈便不能回到同一个虚部值。带洞本身并不强迫失败：若全部闭路周期为零，共轭仍可全域单值。''','C007')
bridge('以两坐标方向弯曲相消解释拉普拉斯方程；分开局部相容与全域路径无关；展示偏导积分的变量函数与常数自由度。')
review[current]['media_review'].append({'id':'CH04-harmonic','evidence':'blocks/render/assets/study-visuals.js harmonic分支：网格曲面及金色u=p.level线；未生成v等值线。','body_alignment':'正文只用图核对鞍面与二阶抵消，正交结论由公式及reader例1承担。','fix':'若需图中直接核对正交，在xy底面增加u等值双曲线与v=2cxy的另一族曲线，并在非临界交点显示两切向和直角；原点标f\u2032=0。'})

unit('CH04-S02','边界约束说明整体控制；下一章换用级数把局部变化拆成可计算的项。')
p(r'''把 $u(x,y)$ 简记成 $u(z)$ 只是记号压缩，它仍为实值函数。若 $u$ 在包含闭圆盘 $|z-a|\le R$ 的开区域内调和，圆心值等于圆周值的平均：
$$u(a)=\frac1{2\pi R}\int_{|z-a|=R}u(z)\,\mathrm ds=\frac1{2\pi}\int_0^{2\pi}u(a+Re^{\mathrm i\theta})\,\mathrm d\theta.$$
弧长元 $\mathrm ds=R\,\mathrm d\theta$ 解释两种写法的系数。平均的是实值本身；圆盘附近调和的条件使整圈都能用于平均。''','C001')
p(r'''一个点若是内部最大值，围绕它的小圆平均还要等于它，就会迫使附近取同样的值，进而传播成常数。这给出极值原理：$D$ 有界、$u$ 在 $D$ 调和并在 $\overline D$ 连续且不恒定时，整个闭域的最大值和最小值只能在边界取得。连续性和有界域保证闭域极值能取得；对最小值可把函数换成 $-u$。证明见[极值原理](#reader-f2f9f2813f5daabfbfea)。''','C002')
p(r'''偏离圆心后，近处边界应占更多权重。设 $z=a+re^{\mathrm i\varphi}$、$0\le r<R$，记边界数据为 $g(\theta)=u(a+Re^{\mathrm i\theta})$，泊松积分公式写成
$$u(a+re^{\mathrm i\varphi})=\frac1{2\pi}\int_0^{2\pi}g(\theta)\frac{R^2-r^2}{R^2-2Rr\cos(\theta-\varphi)+r^2}\,\mathrm d\theta.$$
这里 $u$ 仍须在闭圆盘的邻近区域调和。分式称泊松核，它在内部为正，归一化后权重总和为 $1$；$r=0$ 时核为 $1$，回到等权平均。内点方向 $\varphi$ 固定，积分变量 $\theta$ 扫过边界，两者不能混用。''','C003')
p(r'''在单位圆的右图中固定边界数据 $g(\theta)=\cos(n\theta)$，比较数值泊松积分与 $r^n\cos(n\varphi)$ 的读数。先固定 $n$ 向圆心移动，再增大 $n$：前者让幅度按 $r^n$ 减弱，后者让较高频的边界起伏更快向内部衰减。这里比较的是明确的一组边界数据；泊松核不能直接在 $r=1$ 的奇异表达式上代值，边界要取极限。''')
p('[[TEACHING_VISUAL:CH04-poisson]]')
p(r'''给定区域 $D$、边界 $C=\partial D$ 及连续数据 $g$，寻找 $u\in C(\overline D)$ 满足
$$\Delta u=0\quad(z\in D),\qquad u|_C=g,$$
就是狄利克雷问题。圆盘的泊松公式给出具体构造；一般区域不能仅凭“指定了边界”就宣称解存在，还要另做存在性分析。''','C004')
p(r'''若 $u_1,u_2$ 在有界 $D$ 内调和、闭域连续，且边界上 $|u_1-u_2|\le\varepsilon$，对差函数用极值原理得到
$$|u_1(z)-u_2(z)|\le\varepsilon,\qquad z\in\overline D.$$
因此边界误差不会在内部被放大；取 $\varepsilon=0$，同一边界的两个解必相等。这同时是稳定性和“若存在则唯一”，推演见[稳定性与唯一性](#reader-6d58f72e5246ec48ad0c)。''','C005')
p(r'''若边界数据只有有限个第一类间断点、其余处连续，可改问广义狄利克雷问题：内部解有界且调和，并在每个连续边界点 $\zeta$ 满足 $\lim_{z\to\zeta,\,z\in D}u(z)=g(\zeta)$，不要求跳点取得互相冲突的两侧值。圆盘上，把这样的 $g$ 放进前面的泊松积分，仍得到有界调和函数，并在所有连续点达到给定边界极限，所以该积分也是广义问题的解。''','C006 C007')
p(r'''几个章末工具说明调和性对运算有多严格。若 $f$ 解析，则在 $f\ne0$ 的开集上 $\ln|f|$ 调和，因为局部可取解析对数；在整个解析域则有
$$\Delta|f|^2=4|f'|^2.$$
平方模通常不是调和函数，右端恰好测量其偏离调和的程度。[验证调和函数条件](#reader-0f03b2242d928c14d93a)中的三次多项式 $ax^3+bx^2y+cxy^2+dy^3$ 调和，等价于 $c=-3a$、$b=-3d$。''','SC001')
p(r'''对非恒定实调和函数 $u$，链式求导给出 $\Delta F(u)=F''(u)|\nabla u|^2$。所以 $u^2$ 不可能在整个区域调和；对 $F\in C^2(u(D))$，复合 $F(u)$ 调和当且仅当 $F(t)=at+b$ 在取值区间上为仿射函数。非恒定调和函数的临界点不妨碍这个结论，连续性会把非临界值处的限制延续到整个取值区间。''','SC002')
p(r'''若调和函数在整个复平面有界，它必为常数。可在全平面取共轭，把 $u$ 放进解析函数 $F=u+\mathrm iv$；$e^F$ 的模是有界的 $e^u$，整函数的刘维尔定理便迫使它、进而 $u$ 为常数。这是把第三章整函数工具转回实值函数的例子，见[有界全平面调和函数](#reader-83f50a153f25fecad662)。''','SC003')
bridge('将泊松核解释为归一化正权重；同一差函数连接误差稳定性和唯一性；链式拉普拉斯解释平方与复合的限制。')
review[current]['media_review'].append({'id':'CH04-poisson','evidence':'study-foundation-scenes.js poisson分支：1024点泊松积分与r^n cos(n angle)并列计算；radius为内点半径。','body_alignment':'明确单位圆、cos(nθ)边界、数值/解析读数以及r<1限制。','fix':None})

unit('CH05','从固定复数的无穷和开始，再让各项随点变化，建立可交换积分与求导的依据。')
p(r'''柯西公式用边界积分表示内部值，级数则用许多简单项描述同一个函数。有限多项式容易计算，但想把有限项换成无限项，必须知道部分和会不会收敛、误差能否在一整个集合上受控。因而本章先建立复级数的运算规则，再把它们用于解析函数。''')
p(r'''解析点附近用非负次幂展开，系数储存各阶导数；中心有孤立奇点时则允许负次幂，讨论区域相应变成圆环。每份展开都带着中心和有效区域，不能只背一串系数。负次幂的结构将区分奇点类型，其中负一次幂系数又会成为下一章连接局部行为与整体闭路积分的工具。''')
bridge('把收敛误差作为级数运算前提，并提前区分圆盘展开与圆环展开。')

unit('CH05-S01-SS01','固定点的求和规则准备好后，还要检查同一个误差界能否同时覆盖移动的点。')
p(r'''复级数 $\sum_{k=1}^{\infty}z_k$ 的意义由有限部分和 $S_n=\sum_{k=1}^n z_k$ 定义：若 $S_n\to S\in\mathbb C$，称级数收敛，$S$ 是它的和；没有有限复数极限就称发散。判断对象是部分和列，不能把各项趋零直接当成求和成功。''','C001')
p(r'''若 $z_k=a_k+\mathrm ib_k$，部分和的两个坐标分别是 $\sum_{k=1}^n a_k$ 与 $\sum_{k=1}^n b_k$。因此 $\sum z_k$ 收敛，当且仅当 $\sum a_k$、$\sum b_k$ 都收敛，和为两分量和组成的复数。[例1](#reader-b41eee9921873b92252f)中 $\sum(2^{-n}+\mathrm i/n)$ 的实部虽收敛，虚部调和级数发散，整体仍发散。''','C002')
p(r'''不知道和时，可检查任何足够靠后的有限尾和。柯西准则完整地说：对每个 $\varepsilon>0$，存在正整数 $N=N(\varepsilon)$，使所有 $n>N$ 和所有正整数 $p$ 都有
$$\left|\sum_{k=n+1}^{n+p}z_k\right|<\varepsilon.$$
这与收敛等价；同一个 $N$ 要管任意尾段长度 $p$，否则许多小项仍可累成大改变量。''','C003')
p(r'''只取尾段的一项便知：收敛必有 $z_n\to0$。反过来不成立，$1/n\to0$ 而 $\sum1/n$ 发散。因此发现一般项不趋零可以立即判发散，发现它趋零则还需继续判别。''','C004')
p(r'''更便于估计的条件是绝对收敛，即 $\sum|z_k|<\infty$。这时正项级数的比较、比值、根值等方法可以直接使用。它也等价于实部级数和虚部级数分别绝对收敛，因为 $|a_k|,|b_k|\le|z_k|\le|a_k|+|b_k|$；绝对收敛必推出原复级数收敛。''','C005 C006')
p(r'''绝对收敛还使运算可控：任意重排仍绝对收敛且和不变。若 $\sum u_k=A$、$\sum v_k=B$ 均绝对收敛，按总下标合并乘积，令
$$c_k=\sum_{j=1}^k u_jv_{k+1-j},$$
则 $\sum c_k$ 也绝对收敛且和为 $AB$。这里每个 $c_k$ 收集一条“对角线”上的所有乘积，正是柯西乘积；后面合并指数和三角级数时要用这个许可条件。''','C007 C008')
p(r'''基本积木是几何级数。[例2](#reader-6eab90e736e074a236d3)先用有限等式
$$1+z+\cdots+z^{n-1}=\frac{1-z^n}{1-z}\quad(z\ne1).$$
当 $|z|<1$，$z^n\to0$ 且 $\sum|z|^n$ 收敛，所以 $\sum_{n=0}^{\infty}z^n=1/(1-z)$，并为绝对收敛。若 $|z|\ge1$，项本身不趋零，故发散；$z=1$ 也直接由部分和 $n$ 发散。下一节将让 $z$ 在集合里移动，检验这个收敛是否能统一控制。''','C009')
bridge('将部分和与一般项分开；解释任意尾段长度的量词以及柯西乘积按对角线分组。')

unit('CH05-S01-SS02','每个较小闭圆上的一致控制，正是幂级数和函数保持解析的依据。')
p(r'''各项变成 $E$ 上的函数 $f_k(z)$ 后，每个固定点都对应上一节的数项级数。如果对所有 $z\in E$ 都收敛，便定义和函数 $f(z)=\sum_{k=1}^{\infty}f_k(z)$，称在 $E$ 上逐点收敛。它允许不同点需要不同的项数：给定精度后，靠近边界的点可能比中心慢得多。''','C001')
p(r'''记 $S_n(z)=\sum_{k=1}^n f_k(z)$。一致收敛要求
$$\forall\varepsilon>0\ \exists N=N(\varepsilon)\ \forall n\ge N\ \forall z\in E:\quad |S_n(z)-f(z)|<\varepsilon.$$
先定同一个 $N$，再让 $z$ 任意变动；逐点收敛则把选 $N$ 放在固定 $z$ 之后，允许 $N=N(\varepsilon,z)$。量词次序表达的是一份有限近似能否同时适用于整个集合。''','C002')
p(r'''无需先求出和函数也能判断：柯西一致收敛准则要求
$$\forall\varepsilon>0\ \exists N\ \forall n>N\ \forall p\ge1\ \forall z\in E:\quad\left|\sum_{k=n+1}^{n+p}f_k(z)\right|<\varepsilon.$$
这里 $p$ 为正整数，$N$ 同时不能依赖 $z$ 和 $p$。它将“接近未知的和”改成任意靠后尾段都统一很小，且此条件与一致收敛等价。''','C003')
p(r'''维尔斯特拉斯比较判别法寻找统一的数值上界：对所有 $z\in E$ 及每个 $k$ 有 $|f_k(z)|\le M_k$，其中 $M_k\ge0$、$\sum M_k<\infty$，则 $\sum f_k$ 在 $E$ 上绝对一致收敛，绝对值级数本身也一致收敛。$\sum M_k$ 称强级数；上界必须与 $z$ 无关，才有统一尾和估计。''','C004')
p(r'''例如[例3](#reader-76cad8ac36e8b88744cd)的 $\sum_{k=0}^{\infty}z^k/k!$，在任意有限闭圆 $|z|\le r$ 上用 $|z^k/k!|\le r^k/k!$，而 $\sum r^k/k!$ 收敛，故每个这样的闭圆上都绝对一致收敛。这里每个有限 $r$ 可各有自己的估计，并没有声称全平面共用同一上界。''','C005')
p(r'''[例4](#reader-a0aeb64f37b0923a8118)与[例5](#reader-c1ffb8d4c469b983f89f)使用望远镜级数 $z+(z^2-z)+(z^3-z^2)+\cdots$，其部分和恰为 $z^n$。在 $|z|<1$ 中它逐点趋于 $0$；每个固定闭小圆 $|z|\le b<1$ 上，用 $|z^k-z^{k-1}|\le(1+b)b^{k-1}$ 控制后续项，可得绝对一致收敛。但整个开圆上，每个 $n$ 都能另取 $z_n=2^{-1/n}<1$ 使 $|z_n|^n=1/2$，因而不存在覆盖全部点的统一项数。''','C006')
p(r'''视频的固定 $n=8$ 画面中，蓝线是沿实轴的误差剖面，绿色点 $z=2^{-1/8}$ 的高度恰为 $1/2$，橙色带表示要求误差严格小于 $1/2$。比较绿色点与带的上边界，再看靠近两端仍穿出带外的曲线：固定八项还不能管住全部点。对任意其他 $n$，同样的公式给出新的反例点；对开圆，$|z|=1$ 不包含在集合里，上确界为 $1$ 却不取到。''')
p('[[TEACHING_MEDIA:CH05-NONUNIFORM]]')
p(r'''再把交互图设成闭小圆 $b=0.99$、阈值 $\varepsilon=0.05$，查看统一界 $b^n$，并用跳转按钮到 $n=299$：这时 $0.99^{299}<0.05$，而 $n=298$ 仍不满足严格不等式。一般地，$0<b<1$、$0<\varepsilon<1$ 时所需最小整数为
$$N=\left\lfloor\frac{\ln\varepsilon}{\ln b}\right\rfloor+1.$$
严格小于决定这个取整方式；改回 $b=1$ 后不存在这样的有限统一项数。''')
p('[[TEACHING_VISUAL:CH05-U]]')
p(r'''统一误差让有限和的性质可以传给极限：若每个 $f_k$ 在区域 $D$ 连续，并且级数在 $D$ 一致收敛，则和函数连续。若各项在有限长分段光滑曲线 $C$ 上连续，并在 $C$ 一致收敛，则
$$\int_C f(z)\,\mathrm dz=\sum_{k=1}^{\infty}\int_C f_k(z)\,\mathrm dz.$$
误差积分的模不超过曲线长乘统一误差，解释了曲线上为何要统一控制。''','C007 C008')
p(r'''若各 $f_n$ 在 $D$ 内解析，且级数在 $D$ 一致收敛，则和函数也解析，并可逐项求任意阶导数：
$$f^{(k)}(z)=\sum_{n=1}^{\infty}f_n^{(k)}(z),\qquad z\in D,\quad k=1,2,\ldots.$$
复解析函数的导数可写成小圆周上的柯西积分，这才使求导受统一误差控制。实际只要每个紧含于 $D$ 的小闭圆上有这种一致收敛，就能逐点应用同一论证；下一节幂级数正以这种方式工作。''','C009')
bridge('逐点/一致收敛量词并列；尾段准则同时独立于点和长度；以.99与.05的严格界连接定义到可操作误差；柯西公式解释复函数逐项求导。')
review[current]['media_review'].append({'id':'CH05-U','evidence':'study-visuals.js uniform分支：开圆upper=1-1e-5，sup=1，witness=2^(-1/n)，closed sup=b^n；terms上限300，minimumUniformTerms及跳转按钮保留。','body_alignment':'明确开圆上确界不取到；闭小圆b=.99、epsilon=.05所需299，保持严格<。','fix':None})
review[current]['media_review'].append({'id':'CH05-NONUNIFORM','request_id':'MR-2fc4ad49b6be9910049e','evidence':'旧lesson narration_steps与run-20261016-151603-c8c8f3/state.json记录的video/poster/captions/transcript SHA256可读；所指/home/aaatrucklrx路径的实际视频与动画脚本未在当前仓库发现。','body_alignment':'保留request_id及视频标记；正文数学断言由公式和交互脚本承担，未声称视频实际画有动态坏点。','fix':'交付前在实际资源目录核对视频是否显示坏点2^(-1/n)与开圆右端空心点；若现片只有固定n=8曲线，应将旁白改成固定八项演示，或重渲染n变化且同步移动坏点，request_id不改。'})
review[current]['pending_items'].append('无法从此工作副本访问MR-2fc4ad49b6be9910049e实际视频/动画脚本；视频帧级核对尚未完成，不能据旧旁白判为通过。')

unit('CH05-S02','幂级数产生解析函数；接下来证明每个解析函数也必能局部写成这种形式。')
p(r'''幂级数是按距某个中心的幂来组织的函数项级数：
$$\sum_{n=0}^{\infty}a_n(z-a)^n.$$
中心 $a$ 和系数 $a_n$ 都是复常数，每项为整多项式。先选择中心，是为了用 $z-a$ 描述局部距离；随后的任务是找出哪些距离允许无限求和。''','C001')
p(r'''阿贝尔定理使收敛性沿半径有序：若级数在 $z_0\ne a$ 收敛，则在 $|z-a|<|z_0-a|$ 绝对收敛，并在每个 $|z-a|\le\rho<|z_0-a|$ 一致收敛；若它在 $z_1$ 发散，则 $|z-a|>|z_1-a|$ 处处发散。原因是把项写成 $a_n(z_0-a)^n[(z-a)/(z_0-a)]^n$ 后，前因子有界，后因子可被严格小于 $1$ 的几何比控制。''','C002')
p(r'''于是存在收敛半径 $R$，与实幂级数 $\sum|a_n|x^n$ 的半径相同。$0<R<\infty$ 时，圆内绝对收敛、圆外处处发散，圆周另判；$R=\infty$ 时全平面收敛，$R=0$ 时只在中心收敛。只要 $R>0$，每个严格较小闭圆 $|z-a|\le\rho<R$ 都一致收敛。不要把这句话改成在整个开收敛圆一致收敛，上一节的边界反例已经说明差别。''','C003')
p(r'''计算半径时，若相邻系数最终非零且极限存在，可用
$$R=\lim_{n\to\infty}\left|\frac{a_{n-1}}{a_n}\right|=\frac1{\lim_{n\to\infty}|a_n/a_{n-1}|}.$$
若根值极限存在，也可用 $R=1/\lim_{n\to\infty}\sqrt[n]{|a_n|}$，约定 $1/0=\infty$、$1/\infty=0$。缺项时相邻比值可能根本无定义，应重新编号或改用根值方法；比值公式中的“逆”不能颠倒。''','C004')
p(r'''对 $R>0$ 的幂级数，和函数在 $|z-a|<R$ 解析，因为任一点周围都能放进一个具有一致收敛的小闭圆。在该开圆内，对任意正整数 $k$，
$$\begin{aligned}f^{(k)}(z)&=\sum_{n=k}^{\infty}\frac{n!}{(n-k)!}a_n(z-a)^{n-k}\\&=\sum_{n=0}^{\infty}\frac{(n+k)!}{n!}a_{n+k}(z-a)^n.\end{aligned}$$
导数级数仍有同一收敛半径，边界是否收敛要重判。''','C005')
p(r'''在导数公式中令 $z=a$，只有常数项留下，于是
$$a_n=\frac{f^{(n)}(a)}{n!},\qquad n=0,1,2,\ldots.$$
系数因此不能任意挑：只要和函数与中心确定，它们就被各阶导数唯一确定。下一节反过来从解析函数出发，证明这些被迫的系数确实能拼回原函数。''','C006')
bridge('以相对距离的几何比解释收敛圆；区分小闭圆一致收敛和整个开圆；修正原文半径倒数混淆。')

unit('CH05-S03','泰勒展开描述解析中心；若中心不能解析，就要在去心圆环上允许负次幂。')
p(r'''上一节从幂级数得到解析性，这里走反方向：$f$ 在 $a$ 解析时，把以 $a$ 为中心的圆扩到最近的不可解析障碍之前，圆内必有
$$f(z)=\sum_{n=0}^{\infty}a_n(z-a)^n,\qquad a_n=\frac{f^{(n)}(a)}{n!}.$$
这叫泰勒展开。所指同一解析函数能延伸的最大圆盘，其半径等于到最近奇点的距离；整函数没有有限奇点，半径为 $\infty$。仅仅人为限制了定义域时，域的边缘不一定是真奇点，要先分清限制来自表达式还是函数本身。''','C001')
p(r'''系数也可从围绕中心的正向圆周读取。若 $C$ 及其内部邻近区域都在解析域中、$a$ 位于圆内，则
$$a_n=\frac1{2\pi\mathrm i}\int_C\frac{f(\zeta)}{(\zeta-a)^{n+1}}\,\mathrm d\zeta.$$
柯西核 $1/(\zeta-z)$ 可按 $(z-a)/(\zeta-a)$ 作几何展开，严格小于 $1$ 的比值使其在 $C$ 上一致收敛，再逐项积分。这说明泰勒表示有收敛依据，并非形式上把所有导数排在一起。''','C002')
p(r'''各阶导数已确定每个系数，因而同一中心的泰勒展开唯一；反之，任何半径为正的幂级数就是其和函数在该中心的泰勒展开。综合两个方向，$f$ 在区域 $D$ 解析，当且仅当每个 $a\in D$ 都有一个邻域，能把 $f$ 写成 $z-a$ 的收敛幂级数。“每点有一个邻域”是局部刻画，并不要求整域共用一个中心。''','C003 C004')
p(r'''后续间接展开常用三份全平面有效的积木：
$$\begin{aligned}e^z&=\sum_{n=0}^{\infty}\frac{z^n}{n!},\\\cos z&=\sum_{n=0}^{\infty}\frac{(-1)^nz^{2n}}{(2n)!},\\\sin z&=\sum_{n=0}^{\infty}\frac{(-1)^nz^{2n+1}}{(2n+1)!}.\end{aligned}$$
只含偶次或奇次幂来自函数的奇偶性。使用这些积木相乘、复合时，仍要检查新函数的展开区域。''','C005')
p(r'''换中心要先换变量。[例6](#reader-1b7d792ca18450fdfd65)令 $h=z-\mathrm i$，把分母写成 $(1-\mathrm i)-h$，于是
$$\frac1{1-z}=\sum_{n=0}^{\infty}\frac{(z-\mathrm i)^n}{(1-\mathrm i)^{n+1}},\qquad |z-\mathrm i|<\sqrt2.$$
几何比 $h/(1-\mathrm i)$ 和到奇点 $1$ 的距离给出同一半径。''','C006')
p(r'''[例7](#reader-a83f0f45f16e6beaea37)用 $e^{(1\pm\mathrm i)z}$ 的和、差合并系数，避免反复求乘积导数；对全部复数 $z$ 得
$$\begin{aligned}e^z\cos z&=\sum_{n=0}^{\infty}\frac{2^{n/2}\cos(n\pi/4)}{n!}z^n,\\e^z\sin z&=\sum_{n=0}^{\infty}\frac{2^{n/2}\sin(n\pi/4)}{n!}z^n.\end{aligned}$$
这是代数相加、相减所得，不能对任意复变量把“取实部”当成产生两个解析函数的规则。''','C007')
p(r'''对数先选支再展开。[例8](#reader-7d93617dd74757e4a49b)在 $|z|<1$ 中选定 $\log_k(1)=2k\pi\mathrm i$，由 $1/(1+z)$ 的级数逐项积分得
$$\log_k(1+z)=2k\pi\mathrm i+\sum_{n=1}^{\infty}\frac{(-1)^{n-1}}n z^n,\qquad k\in\mathbb Z.$$
各支只差常数项，最近的支点为 $z=-1$，故半径均为 $1$；$k=0$ 取在 $1$ 处值为 $0$ 的分支。''','C008')
p(r'''生成函数则把一整串多项式藏在系数中。[例9](#reader-fc7b8930601e6a3f9f34)给定实参数 $-1\le t\le1$，令 $t=\cos u$ 后分解为两个几何分式，得
$$\frac{4-z^2}{4-4tz+z^2}=1+\sum_{n=1}^{\infty}T_n(t)z^n,\qquad |z|<2,$$
$$T_n(t)=\frac{\cos(n\arccos t)}{2^{n-1}},\qquad n\ge1.$$
这是本书归一化的切比雪夫多项式，不能略去系数中的 $2^{n-1}$；它与常见另一归一化记法不同。''','C009')
p(r'''若求倒数的首项，比较乘积系数比高阶求导省力。$\sec z$ 是偶函数，在 $|z|<\pi/2$ 有
$$\sec z=1+\frac{z^2}{2!}+\frac{5z^4}{4!}+O(z^6).$$
把它乘上 $\cos z$ 并令结果为 $1$ 即可依次定系数；最近的两个极点是 $\pm\pi/2$，它们限制展开圆。''','C010')
p(r'''只求有限阶复合时，余项必须跟着阶数走。记 $O(z^k)$ 为从 $z^k$ 开始的解析幂级数余项，则在 $|z|<1$ 的函数 $\exp(z/(z-1))$ 在原点有
$$\exp\!\left(\frac z{z-1}\right)=1-z-\frac{z^2}{2}-\frac{z^3}{6}+O(z^4).$$
先把内层写成 $-z-z^2-z^3+O(z^4)$，再代入指数积木；只保留会影响前三次幂的项，不必展开全部无穷乘积。''','C011')
p(r'''展开还能测量函数消失的速度。$f$ 在 $z_0$ 解析且 $f(z_0)=0$ 时称为零点；若第一个非零泰勒系数是 $a_m$，称 $m$ 阶零点，$m=1$ 为单零点。全部系数为零时，函数在某邻域恒为零，不能把它当成某个有限阶。导数判别与此等价：
$$f(z_0)=f'(z_0)=\cdots=f^{(m-1)}(z_0)=0,\qquad f^{(m)}(z_0)\ne0.$$
例如 $z-\sin z=z^3/3!+O(z^5)$ 在原点是三阶零点。''','C012 C013')
p(r'''把首个非零幂提出，可将非恒零解析函数局部写成
$$f(z)=(z-z_0)^m g(z),\qquad g\text{ 在 }z_0\text{ 解析},\quad g(z_0)\ne0.$$
这与 $m$ 阶零点等价。因 $g$ 在足够小邻域仍不为零，$z_0$ 是其中唯一零点，所以解析函数的零点要么孤立，要么函数在一个邻域恒零。这个因子分解会在约去奇点、判断极点阶数以及用对数导数数根时反复出现。''','C014 C015')
bridge('以柯西核的一致几何展开解释Taylor必然收敛；分别示范换中心、乘积、选支、生成函数与截阶；用首个非零项桥接零点阶数和孤立性。')
review[current]['pending_items'].append('旧lesson中本节例10/例11 reader hash分别为3d5d2e3af9a2110e7e88与23aa816448d1fbf0925f，恰与CH06-S02-SS04例10/例11共用；保留原reader链接，需主集成核验原折叠资料是否按unit命名空间解析，避免跳到杂例。')

unit('CH05-S04','圆环中负次幂的多少，将直接决定中心孤立奇点的类型。')
p(r'''中心不解析时，泰勒圆盘的要求太强，可以只在围住中心的圆环中讨论。罗朗级数允许所有整数次幂：
$$\sum_{n=-\infty}^{\infty}a_n(z-a)^n=\sum_{n=1}^{\infty}\frac{a_{-n}}{(z-a)^n}+\sum_{n=0}^{\infty}a_n(z-a)^n.$$
右侧两份级数必须各自收敛，才定义其和；不能把正负下标对称截断后的偶然抵消当成收敛。''','C001')
p(r'''非负次幂要求 $|z-a|<R$；负次幂看作 $\zeta=1/(z-a)$ 的幂级数，若其收敛半径为 $1/r$，便要求 $|z-a|>r$。两条件交集是 $r<|z-a|<R$，其中 $r<R$，和函数在这个圆环内解析。每个紧含于圆环的闭子圆环上可一致收敛，内外边界仍须另判。''','C002')
p(r'''反过来，若 $f$ 在 $r<|z-a|<R$ 解析，就有且仅有一份该圆环中的罗朗展开；系数是
$$a_n=\frac1{2\pi\mathrm i}\int_C\frac{f(\zeta)}{(\zeta-a)^{n+1}}\,\mathrm d\zeta,\qquad n\in\mathbb Z.$$
$C$ 必须位于圆环中、正向绕 $a$ 一次，系数与这样的闭路如何弯曲无关。唯一性固定的是中心和圆环；跨过另一个奇点换了圆环，系数就可以改变。''','C003 C004')
p(r'''为何积分能抽出单个系数？对正向绕 $a$ 一次且避开它的闭路，以及任意整数 $n$，
$$\int_C\frac{\mathrm dz}{(z-a)^n}=\begin{cases}2\pi\mathrm i,&n=1,\\0,&n\ne1.\end{cases}$$
在展开式两边乘上合适的整数幂再积分，只留下要找的系数。下一章留数正是直接读取负一次幂的这项选择作用。''','C005')
p(r'''右图采用 $f(z)=1/[z(z-1)]$，与教材例题的中心不同。分别在 $0<|z|<1$ 和 $|z|>1$ 使用
$$-\frac1z-1-z-\cdots,\qquad \frac1{z^2}+\frac1{z^3}+\cdots.$$
把采样半径从 $0.6$ 改到 $1.4$，比较有限部分和与原函数的像曲线：换用的几何比从 $z$ 变成 $1/z$。恰在半径 $1$ 时采样圆经过奇点，任何一份都不能作为该整圆上的收敛展开。''')
p('[[TEACHING_VISUAL:CH05-L]]')
p(r'''教材[例12](#reader-ffd4e4fccbef001c6ee9)对 $1/[(z-1)(z-2)]$ 也先部分分式，再按区域选择小参数，得到
$$\begin{aligned}f(z)&=-\sum_{n=-1}^{\infty}(z-1)^n,&&0<|z-1|<1,\\f(z)&=\sum_{n=2}^{\infty}\frac{2^{n-1}-1}{z^n},&&2<|z|<\infty.\end{aligned}$$
两式的中心分别为 $1$ 与 $0$，外边界也不同；只抄等号右侧会把方法的适用条件丢掉。''','C006')
p(r'''复合函数常可换成倒数变量后直接代入熟悉积木。[例13](#reader-000014a1807334921007)先用 $z/(z-1)=1+1/(z-1)$，在全部 $0<|z-1|<\infty$ 得
$$\begin{aligned}\sin\frac z{z-1}={}&\sin1\sum_{n=0}^{\infty}\frac{(-1)^n}{(2n)!(z-1)^{2n}}\\&+\cos1\sum_{n=0}^{\infty}\frac{(-1)^n}{(2n+1)!(z-1)^{2n+1}}.\end{aligned}$$
原来的正弦和余弦级数对倒数变量全平面收敛，所以这里除中心外没有有限半径限制。''','C007')
p(r'''[例14](#reader-475ad4a6ec72a084962e)把两个指数级数相乘、按同一整数次幂收集，得到贝塞尔生成展开。固定实参数 $t$ 时，在 $0<|z|<\infty$ 有
$$\exp\!\left[\frac t2\left(z-\frac1z\right)\right]=\sum_{n=-\infty}^{\infty}J_n(t)z^n.$$
对整数 $n\ge0$，
$$J_n(t)=\sum_{\ell=0}^{\infty}\frac{(-1)^\ell}{\ell!(n+\ell)!}\left(\frac t2\right)^{2\ell+n},\qquad J_{-n}(t)=(-1)^nJ_n(t).$$
这些是整数阶贝塞尔函数；把 $t$ 当复变量，它们的级数半径为 $\infty$，所以均为整函数。''','C008')
p(r'''系数公式还提供同一特殊函数的另一种计算入口：对实数 $t$、任意整数 $n$，在单位圆取 $z=e^{\mathrm i\theta}$ 可得
$$J_n(t)=\frac1{2\pi}\int_0^{2\pi}\cos(t\sin\theta-n\theta)\,\mathrm d\theta.$$
指数形式中的虚部由对称性积分为零。级数适合按参数求近似，积分适合研究振荡；系数唯一性保证两种表示指向同一对象。''','C009')
bridge('从两个方向的收敛限制得到圆环；显示系数积分的筛选作用；明确交互函数与原例不是同一个函数；将贝塞尔级数/积分统一为同一罗朗系数。')
review[current]['media_review'].append({'id':'CH05-L','evidence':'study-visuals.js laurent分支：内侧-sum(z)/z，外侧z^-2 sum(1/z)，金线原函数1/[z(z-1)]。','body_alignment':'正文单独明确模型函数与两份展开，避免把教材1/[(z−1)(z−2)]硬说成现图。','fix':None})

unit('CH05-S05','奇点类型给出局部结构；下一章只取其中负一次幂系数来计算闭路积分。')
p(r'''“孤立”先限定了环境：存在 $\rho>0$，$f$ 在去心邻域 $0<|z-a|<\rho$ 解析，只有中心 $a$ 可能出问题。其罗朗展开中，负次幂叫主要部分，非负次幂叫正则部分。分类必须用这个能无限靠近中心的去心邻域展开；外部另一个圆环中的负次幂不能拿来判断中心。''','C001')
p(r'''若主要部分全空，$a$ 是可去奇点；补定义 $f(a)=a_0$，同一展开便在整圆盘成为泰勒级数。对已知孤立奇点，可去、在某个去心邻域有界、具有有限极限 $\lim_{z\to a}f(z)=A$ 三者等价，补值就是 $A$。例如 $\sin z/z$ 在原点未定义，但展开为 $1-z^2/3!+\cdots$，补成 $f(0)=1$ 即解析。''','C002 C003')
p(r'''若主要部分只有有限个非零项，最高负次幂为 $a_{-m}(z-a)^{-m}$、$a_{-m}\ne0$，则为 $m$ 阶极点。这等价于局部分解
$$f(z)=\frac{\varphi(z)}{(z-a)^m},\qquad\varphi\text{ 在 }a\text{ 解析},\quad\varphi(a)\ne0,$$
也等价于 $1/f$ 补值后在 $a$ 有 $m$ 阶零点。阶数来自约去共同零因子后的真实差额，不是眼见分母的幂就结束。[例15](#reader-4401895b8cab034562aa)的 $\sin z$ 抵消一个原点零因子，使原点实际为单极点，另两点 $1,-1$ 分别为二、三阶极点。''','C004 C005')
p(r'''极点也可由极限识别：在 $a$ 已知孤立的前提下，$a$ 是极点当且仅当 $|f(z)|\to\infty$。这要求所有复方向的趋近，不能仅看一条曲线上发散。“趋于无穷”说的是模离开任何有限界，复函数的相位仍可变化。''','C006')
p(r'''若主要部分有无限多个非零负次幂，就是本性奇点；等价地，孤立中心既无有限极限，也无无穷极限。$e^{1/z}$ 沿正实轴趋近原点时增长，沿负实轴则趋于 $0$，两种结果排除统一极限；其展开确有无限负次幂。[例16](#reader-40485690e656cc1093f1)的 $\cos(1/(z+\mathrm i))$ 在 $-\mathrm i$ 也有同样的无限主要部分判别。''','C007')
p(r'''右图用 $e^{1/z}$ 比较趋近方向：在 $z=re^{\mathrm i\theta}$ 上，模为 $e^{\cos\theta/r}$。固定 $r$ 后改变 $\theta$，再减小 $r$，正实轴方向增长、负实轴方向衰减；虚轴方向模为 $1$，相位却不断振荡。画面会截掉超出视野的部分，有限视野中的曲线长度不能代表函数有界。''')
p('[[TEACHING_VISUAL:CH05-E]]')
p(r'''本性行为不能被非零的有限阶因子消掉：若 $a$ 是 $g$ 的孤立本性奇点，$f$ 在 $a$ 解析或有极点且邻域不恒零，则 $fg$、$g/f$ 仍以 $a$ 为本性奇点。若还要讨论 $1/g$ 或 $f/g$，必须先保证 $g$ 在一个去心邻域无零点，从而这些商在那里解析；满足此前提时它们也有本性奇点。[例17](#reader-bb5724e931546e5d3bce)的乘除法要带着这个限制读，否则倒数可能出现向中心聚集的极点，中心便不再孤立。''','C008')
p(r'''无穷远的定义要换坐标。若 $f$ 在某圆外域 $R<|z|<\infty$ 解析，才称 $\infty$ 为孤立奇点；令 $\zeta=1/z$、$\varphi(\zeta)=f(1/\zeta)$，将它归为 $\zeta=0$ 的可去、$m$ 阶极点或本性奇点。若有限奇点无限向外分布，就找不到这样的圆外解析域，不能硬套这一分类，例如 $\tan z$。''','C009')
p(r'''若圆外展开写成 $\sum b_nz^n$，由于 $z^n=\zeta^{-n}$，无穷远要数的是正次幂：没有正次幂则可去；正次幂有限且最高为 $b_mz^m$、$m>0$，则是 $m$ 阶极点；无限多个正次幂则为本性奇点。相应极限分别为有限值、模趋于无穷、有限和无穷极限都不存在。非恒定 $m$ 次多项式在无穷远有 $m$ 阶极点，$e^z$ 则有本性奇点。''','C010 C011')
p(r'''有理函数 $P/Q$ 可直接用次数判断无穷远。设 $\deg P=m$、$\deg Q=n$、首项系数为 $a_0,b_0\ne0$：$m\le n$ 时极限有限，故无穷远可去；$m>n$ 时有 $m-n$ 阶极点，首项为 $(a_0/b_0)z^{m-n}$。这条全局增长信息会在下一章决定大圆弧能否消失。''','C012')
p(r'''章末练习把边界情形补齐：$\sum z^n/n^2$ 由统一上界 $1/n^2$ 可知在 $|z|\le1$ 上绝对一致收敛；$\sum_{n=1}^{\infty}z^n$ 在 $|z|=1$ 则处处发散，在每个 $|z|\le r<1$ 绝对一致收敛，在整个开单位圆不一致收敛。相同半径并不决定圆周表现；例如 $\sum z^n/n$ 在 $z=-1$ 收敛、在 $z=1$ 发散。''','SC001')
p(r'''把恒等式两边按系数比较还能直接产生递推。若 $1/(1-z-z^2)=\sum_{n=0}^{\infty}C_nz^n$，乘回分母得 $C_0=C_1=1$，并有
$$C_{n+2}=C_{n+1}+C_n,\qquad n\ge0.$$
所以前五项为 $1+z+2z^2+3z^3+5z^4$，半径为最近分母零点到原点的距离 $(\sqrt5-1)/2$。递推来自乘积系数唯一性，而非凭数列样子猜测。''','SC002')
p(r'''另一生成函数在 $t=0$ 附近取平方根值为 $1$ 的分支，定义勒让德多项式：
$$\frac1{\sqrt{1-2zt+t^2}}=\sum_{n=0}^{\infty}p_n(z)t^n.$$
对 $n\ge1$ 有
$$\begin{aligned}(n+1)p_{n+1}-(2n+1)zp_n+np_{n-1}&=0,\\p_n&=p'_{n+1}-2zp'_n+p'_{n-1},\\(2n+1)p_n&=p'_{n+1}-p'_{n-1}.\end{aligned}$$
撇号对 $z$ 求导；先分别对生成函数的 $z$ 与 $t$ 求导，再比较同次 $t$ 系数，就把无限项展开转成可逐项计算的恒等式。''','SC003')
p(r'''对实数 $a,\theta$ 且 $|a|<1$，几何级数与对数级数分别给出三个可复用的三角恒等式：
$$\begin{aligned}\frac{1-a\cos\theta}{1-2a\cos\theta+a^2}&=\sum_{n=0}^{\infty}a^n\cos(n\theta),\\\frac{a\sin\theta}{1-2a\cos\theta+a^2}&=\sum_{n=1}^{\infty}a^n\sin(n\theta),\\\ln(1-2a\cos\theta+a^2)&=-2\sum_{n=1}^{\infty}\frac{a^n}{n}\cos(n\theta).\end{aligned}$$
将 $ae^{\mathrm i\theta}$ 代入基本积木后按实虚部分开即可；$|a|<1$ 保障展开和交换运算，第三式的实对数也因分母对应的平方模为正而有意义。''','SC004')
p(r'''指数级数的绝对值估计还给出，对任意 $z\in\mathbb C$，
$$|e^z-1|\le e^{|z|}-1\le |z|e^{|z|}.$$
它把复方向的增量压到只依赖距离的正项上界，适合统一控制误差。若分子 $f$ 在 $z_0$ 至少有 $n$ 阶零点、分母 $\varphi$ 恰有 $n$ 阶零点，则约去共同因子后
$$\lim_{z\to z_0}\frac{f(z)}{\varphi(z)}=\frac{f^{(n)}(z_0)}{\varphi^{(n)}(z_0)},\qquad\varphi^{(n)}(z_0)\ne0.$$
分子阶数更高时该值为 $0$，相同阶数时为首系数之比。''','SC005 SC006')
bridge('区分用于分类的去心展开与外环展开；沿方向公式解释本性行为；强调倒数孤立性前提；将无穷远与大弧衰减相连；显式讲解章末生成递推/三角恒等式/商极限。')
review[current]['media_review'].append({'id':'CH05-E','evidence':'study-visuals.js essential映照map=exp(1/z)，extent与phase控制采样；scene说明超出视野曲线截去。','body_alignment':'正文以模公式解释三个方向，明说截屏裁剪不能证明有界。','fix':None})
p(r'''做章末乘除分类时，先比较最低非零幂就能统一处理：两个零点阶数为 $m,n$ 时，乘积阶数为 $m+n$，商的阶数差为 $m-n$；正差是零点，负差是极点，零差则补成非零解析值。和的阶数在 $m\ne n$ 时为 $\min(m,n)$，同阶时首项可能抵消而升阶或恒零。两个极点相乘阶数相加，相除仍看阶数差；相加在不同阶时保留较高极点阶，同阶时则必须重查抵消。有限阶因子计算到这里就够，本性因子则要回到去心解析性条件。''')

unit('CH06','先定义奇点周围闭路积分的局部贡献，再研究怎样从展开式里读取它。')
p(r'''上一章的罗朗展开保留了奇点附近所有整数次幂。本章问一个更集中的问题：沿包围奇点的闭路积分时，哪些项真正留下贡献？只需要一个局部系数，就能把整条路径的计算缩成有限个数的相加，这个系数称为留数。''')
p(r'''留数的用途有两条线：把实定积分嵌入合适的复闭路，以及把对数导数的积分变成内部零点、极点的计数。前者最难的是辅助路径和极限，后者最要紧的是边界不经过零极点与重数。它们都从同一个局部积分定理出发。''')
bridge('从全部罗朗信息收缩到积分选择的一项，再区分积分计算和零极点计数两条应用。')

unit('CH06-S01','知道留数怎样算之后，还要把实积分放到闭路中，处理补路留下的积分。')
p(r'''设 $a$ 是 $f$ 的孤立奇点，在充分小去心邻域取正向简单闭路 $C$，只包围 $a$ 一次。定义
$$\operatorname{Res}(f,a)=\frac1{2\pi\mathrm i}\int_C f(z)\,\mathrm dz.$$
只要闭路始终留在这份去心邻域并保持绕行，形状改变不改积分；所以留数描述的是函数和奇点，积分等于 $2\pi\mathrm i$ 乘这个局部贡献。''','C001')
p(r'''若正向简单闭路 $C$ 上及内部，$f$ 除有限个孤立奇点 $a_1,\ldots,a_n$ 外解析，留数定理给出
$$\int_C f(z)\,\mathrm dz=2\pi\mathrm i\sum_{k=1}^n\operatorname{Res}(f,a_k).$$
只计严格在内部的奇点，路径上的奇点不能列入后照算；反向绕行使整体变号。切开挖掉小圆后的解析区域，整体积分被分成各个奇点周围的小圈积分，这是局部贡献可以相加的原因。''','C002')
p(r'''右图固定 $f(z)=1/(z-a)$，正向圆的半径为 $R$。移动实轴参数 $a$，先比较 $|a|<R$ 与 $|a|>R$ 的读数，再靠近 $|a|=R$：前两种分别为 $2\pi\mathrm i$ 与 $0$，临界位置函数在路径上未定义，不能把它当成中间积分值。图中只展示一个单极点，这足以解释“哪些奇点属于内部”的选择。''')
p('[[TEACHING_VISUAL:CH06-R]]')
p(r'''局部罗朗展开 $f(z)=\sum_{n=-\infty}^{\infty}a_n(z-a)^n$ 中，只有负一次幂绕圈积分非零，因此
$$\operatorname{Res}(f,a)=a_{-1}.$$
可去奇点的留数为零，反过来留数为零不代表可去：$(z-a)^{-2}$ 有极点，$e^{1/(z-a)^2}$ 有本性奇点，但都没有负一次幂项。''','C003')
p(r'''若 $a$ 是 $m$ 阶极点，先消去极点写 $\varphi(z)=(z-a)^mf(z)$ 并在中心解析补值。要取回 $f$ 的负一次幂，就要读 $\varphi$ 的第 $m-1$ 次系数：
$$\operatorname{Res}(f,a)=\frac{\varphi^{(m-1)}(a)}{(m-1)!}=\frac1{(m-1)!}\lim_{z\to a}\frac{\mathrm d^{m-1}}{\mathrm dz^{m-1}}\bigl[(z-a)^mf(z)\bigr].$$
先确定真实极点阶数再用此式，若只需一个系数也可直接截取局部展开。''','C004')
p(r'''单极点时无需高阶导数：$\operatorname{Res}(f,a)=\lim_{z\to a}(z-a)f(z)$。若 $f=P/Q$，$P,Q$ 在 $a$ 解析，且 $P(a)\ne0$、$Q(a)=0$、$Q'(a)\ne0$，分母为单零点，便有
$$\operatorname{Res}\!\left(\frac P Q,a\right)=\frac{P(a)}{Q'(a)}.$$
分母多重零点、或分子也为零时，要先重新判阶，不能直接套这一商公式。''','C005 C006')
p(r'''[例1](#reader-d8fcb526c5f350d68025)的 $1/[z^3(z-1)]$ 在 $1$ 的留数为 $1$，在 $0$ 为 $-1$；后一个可由 $-z^{-3}-z^{-2}-z^{-1}-\cdots$ 直接读取。[例2](#reader-49762b2a448da763ded6)中 $\tan(\pi z)$ 的每个极点 $k+1/2$ 留数都为 $-1/\pi$：半径 $1/3$ 的圈积分为 $0$，半径正整数 $n$ 的圈内有 $2n$ 个极点，积分为 $-4n\mathrm i$。相同留数并不代替内部极点数的清点。''')
p(r'''[例3](#reader-8279001fa1436a5e4894)的 $z^3\sin^5(1/z)$ 虽有本性奇点，但所有幂的奇偶结构排除了 $z^{-1}$，单位圆积分为 $0$。[例4](#reader-040a84237909718a10a8)的 $z\sin z/(1-e^z)^3$ 在原点分子二阶消失、分母三阶消失，首项为 $-1/z$，故单位圆积分为 $-2\pi\mathrm i$。这些例子说明目标若只是积分，未必需要求完整罗朗展开。''')
bridge('解释高阶极点公式为何取m−1阶系数；留数零不等于可去；用案例奇偶性和首项比较避免完整展开。')
review[current]['media_review'].append({'id':'CH06-R','evidence':'study-visuals.js contour分支：圆与实轴极点标记；按abs(pole)与radius判内部并提示路径奇点。','body_alignment':'仅称单极点位置与读数演示，不宣称显示多奇点挖洞证明。','fix':None})

unit('CH06-S02','先用完整周期的圆参数直接闭合积分，再处理需要添加路径的情形。')
p(r'''实积分通常只沿一条线段，而留数定理处理闭路。两者之间的工作是找复辅助函数 $F$，使实轴上的 $F(x)$，或其实部、虚部等于目标被积函数，再补一条能处理的路线。辅助函数与路线必须配合选择，单纯把实变量换成复变量还没有完成方法。''')
p(r'''有限实线段 $[a,b]$ 与回程 $L$ 组成正向闭路时，要先写全等式：目标所在线段的复积分、补路积分之和，等于内部留数的 $2\pi\mathrm i$ 倍。补路可能可直接计算，可能变成原积分的另一个倍数，或随参数趋于零。决定办法是否成功的，是这一额外项能否真正处理。''')
p(r'''无限区间要先截成有限闭路，再处理大半径极限；实轴奇点要挖小弧；对数和非整数幂要先定分支。对称截断首先得到主值，能否称普通广义积分要另查两端及各内瑕点的独立收敛。接下来每种积分分别说明选路、误差估计和参数限制，不把留数数值当成全部答案。''')
bridge('把补路积分视为需要处理的实际代价；先有限闭路后极限，并区分辅助复积分与原实积分收敛。')

unit('CH06-S02-SS01','整周期参数能直接闭合；全实轴则需额外证明大弧积分消失。')
p(r'''对于无瑕点的 $\int_0^{2\pi}R(\cos\theta,\sin\theta)\,\mathrm d\theta$，令 $z=e^{\mathrm i\theta}$，周期参数正好沿单位圆逆时针一周，同时替换
$$\cos\theta=\frac{z+z^{-1}}2,\quad\sin\theta=\frac{z-z^{-1}}{2\mathrm i},\quad\mathrm d\theta=\frac{\mathrm dz}{\mathrm iz}.$$
于是
$$\int_0^{2\pi}R(\cos\theta,\sin\theta)\,\mathrm d\theta=\int_{|z|=1}\frac1{\mathrm iz}R\!\left(\frac{z+z^{-1}}2,\frac{z-z^{-1}}{2\mathrm i}\right)\,\mathrm dz.$$
右侧整个式子整理为有理函数且圆周无极点后，才按圆内奇点用留数。''','C001')
p(r'''右图沿圆移动角参数，比较蓝色半径与金色切向。$\mathrm dz/\mathrm d\theta=\mathrm iz$ 的 $\mathrm i$ 负责转向，$z$ 含方向与长度；粉色径向是漏掉转向因子的对照。减小角增量时，短弦更贴近切向，但微分元中的 $1/(\mathrm iz)$ 始终不能省。代换后的额外 $1/z$ 也须加入极点判别。''')
p('[[TEACHING_VISUAL:CH06-D]]')
p(r'''[例5](#reader-85b72aa49f433c037eca)给出泊松型积分，条件 $0<p<1$ 使变换后的单极点 $p$ 在圆内、$1/p$ 在圆外，因此
$$\int_0^{2\pi}\frac{\mathrm d\theta}{1-2p\cos\theta+p^2}=\frac{2\pi}{1-p^2}.$$
若极点落到单位圆上，这套普通闭路公式失效；参数条件在此承担的是选内外及避免路径奇点的职责。''','C002')
p(r'''半周期先利用对称性补成一周。[例6](#reader-84c3f0235e5b910f82ad)对正整数 $m$ 合并成指数、用 $e^{\mathrm imx}=z^m$，得到
$$\begin{aligned}\int_0^\pi\frac{\cos(mx)}{5-4\cos x}\,\mathrm dx&=\frac{\pi}{3\cdot2^m},\\\int_{-\pi}^{\pi}\frac{\cos(mx)}{5-4\cos x}\,\mathrm dx&=\frac{\pi}{3\cdot2^{m-1}},\\\int_{-\pi}^{\pi}\frac{\sin(mx)}{5-4\cos x}\,\mathrm dx&=0.\end{aligned}$$
第一式的半倍来自偶性，第三式也可由奇性核对；这些区间和因子应在代换前记录。''','C003')
p(r'''不能直接由周期闭合时，一般桥梁是添加回程。若 $[a,b]$ 与从 $b$ 到 $a$ 的辅助曲线 $L$ 围成正向简单闭路，$F$ 在边界解析、内部仅有有限孤立奇点 $a_k$，则
$$\int_a^b F(x)\,\mathrm dx+\int_LF(z)\,\mathrm dz=2\pi\mathrm i\sum_k\operatorname{Res}(F,a_k).$$
若目标是 $\operatorname{Re}F(x)$ 或 $\operatorname{Im}F(x)$，先处理回程积分，再取相应分量。这一等式将成为后面半圆、扇形、矩形与钥匙孔路线的共同起点。''','C004')
bridge('以径向/切向解释微分元；把参数条件与极点内外相连；明确整周和半周因子；统一补路恒等式。')
review[current]['media_review'].append({'id':'CH06-D','evidence':'study-visuals.js circle-differential分支：蓝径向、金切向、粉漏i径向、绿色下一点；derivative=[−y,x]。','body_alignment':'准确描述径切向比较与增量趋小，不声称图上完成留数计算。','fix':None})

unit('CH06-S02-SS02','有理函数本身衰减不足时，振荡指数会提供另一份大弧控制。')
p(r'''设有理函数 $R=P/Q$ 在实轴无极点，且 $\deg Q\ge\deg P+2$。两项条件分别排除有限内瑕点、保证无穷远有 $O(x^{-2})$ 或更快衰减，所以全轴普通广义积分绝对收敛。用从左到右的实段和上半圆回程闭合，才有机会用上半平面留数求它。''')
p(r'''普通广义积分的两端必须独立取极限：
$$\int_{-\infty}^{\infty}f(x)\,\mathrm dx=\lim_{\substack{A\to\infty\\B\to-\infty}}\int_B^A f(x)\,\mathrm dx.$$
柯西主值只取对称截断 $\operatorname{v.p.}\int_{-\infty}^{\infty}f=\lim_{T\to\infty}\int_{-T}^T f$。普通积分存在则主值相同，反向不成立；例如在 $|x|\ge1$ 取 $f(x)=1/x$、其余取零，两端分别发散但对称主值为 $0$。闭半圆自然产生对称截断，所以这里必须先有普通收敛的保证。''','C002')
p(r'''若有限区间有唯一内瑕点 $c\in(a,b)$，普通积分要求左右两边各自收敛、截去距离彼此独立；主值则是
$$\operatorname{v.p.}\int_a^bf(x)\,\mathrm dx=\lim_{r\to0^+}\left[\int_a^{c-r}f(x)\,\mathrm dx+\int_{c+r}^bf(x)\,\mathrm dx\right].$$
同一个 $r$ 让两侧可能发生对称抵消，这不是原普通积分收敛的证明。多个瑕点要各自作局部对称截断。''','C003')
p(r'''大弧消失靠的是积分估计。若 $f$ 在充分大的 $C_T:z=Te^{\mathrm i\theta}$、$\alpha\le\theta\le\beta$ 上连续，且 $zf(z)\to0$ 在这些弧上一致成立，则
$$\left|\int_{C_T}f(z)\,\mathrm dz\right|\le(\beta-\alpha)\sup_{C_T}|zf(z)|\longrightarrow0.$$
有理函数分母次数至少高两次时自动满足。弧长随 $T$ 增长，单说 $f(z)\to0$ 并不够。''','C004')
p(r'''右图用 $f(z)=z^{-q}$ 单独展示这份竞争：左侧是按 $z/T$ 归一化显示的半圆，右侧绿色是实际积分向量，金色是长大界 $\pi T^{1-q}$。保持 $q=1$ 增大 $T$，上界不变，实际积分为 $\pi\mathrm i$；改成 $q=2$，界随 $1/T$ 下降。图的作用是核对弧长增长与衰减次数，并不是绘出任意有理函数。''')
p('[[TEACHING_VISUAL:CH06-A]]')
p(r'''让半径足够大以包围严格上半平面的全部极点 $a_k$，然后使大弧积分趋零，便得到
$$\int_{-\infty}^{\infty}R(x)\,\mathrm dx=2\pi\mathrm i\sum_{\operatorname{Im}a_k>0}\operatorname{Res}(R,a_k).$$
这里仍带着实轴无极点、次数差至少两次两项条件。[例7](#reader-b0aa47de5b70eb6513db)在 $a>0$ 时只有 $a\mathrm i$ 这个上半平面三级极点，结果为
$$\int_{-\infty}^{\infty}\frac{\mathrm dx}{(x^2+a^2)^3}=\frac{3\pi}{8a^5}.$$
相应大弧估计可写成 $\pi T/(T^2-a^2)^3\to0$，以确保留数等式确实回到原积分。''','C005 C001')
p(r'''小弧则可能留下有限量。设 $z=a+\rho e^{\mathrm i\theta}$ 从角度 $\alpha$ 增到 $\beta$，$f$ 在足够小弧上连续，且 $(z-a)f(z)\to k$，则
$$\lim_{\rho\to0^+}\int_{C_\rho}f(z)\,\mathrm dz=\mathrm i(\beta-\alpha)k.$$
若 $k=0$，小弧消失；若中心是单极点，$k=\operatorname{Res}(f,a)$，逆时针半圆贡献 $+\pi\mathrm i\operatorname{Res}$、顺时针贡献负号。弧虽短，函数却可能按 $1/\rho$ 增长，两者正好抵消。''','C006 C007')
p(r'''引入指数后可用约当引理：固定 $h>0$，若 $g$ 在充分大的圆弧 $C_T=\{|z|=T,\ \operatorname{Im}z>-h\}$ 上连续，并且 $g(z)\to0$ 在这些弧上一致成立，则对每个 $\lambda>0$，
$$\lim_{T\to\infty}\int_{C_T}g(z)e^{\mathrm i\lambda z}\,\mathrm dz=0.$$
特别适用于上半圆。因为指数的模为 $e^{-\lambda\operatorname{Im}z}$，整体积分能比单用长大界得到更强控制；这使有理部分只需趋零即可，下一节便可放宽一次次数差。''','C008')
bridge('先独立定义两种主值与普通收敛；用弧长乘界解释大弧、小弧不同结果；区分不带指数与约当引理的条件。')
review[current]['media_review'].append({'id':'CH06-A','evidence':'study-visuals.js arc-decay分支：q=1 integral=[0,π]，q>1按幂积分显式求值；bound=πR^(1−q)，左图归一化。','body_alignment':'正文明确归一化图、实际积分向量和ML界的不同角色。','fix':None})

unit('CH06-S02-SS03','指数的衰减决定半平面；更复杂指数则需要按自己的衰减方向选其他闭路。')
p(r'''设目标含 $R(x)\cos(mx)$ 或 $R(x)\sin(mx)$，$m>0$。取 $F(z)=R(z)e^{\mathrm imz}$，将两者合并成
$$J=\operatorname{v.p.}\int_{-\infty}^{\infty}R(x)e^{\mathrm imx}\,\mathrm dx=I_1+\mathrm iI_2.$$
只有 $R(x)$ 在实轴为实值时，才可将 $I_1,I_2$ 直接读成 $\operatorname{Re}J,\operatorname{Im}J$；若 $R$ 复值，代数合并仍成立，读实虚部的规则却不能照搬。''','C001')
p(r'''写 $z=x+\mathrm iy$ 后，$|e^{\mathrm imz}|=e^{-my}$，所以 $m>0$ 时选上半圆。若有理部分分母次数至少比分子高一次，$R(z)\to0$，约当引理使大弧消失。比没有指数时少要求一次衰减，依据来自整段圆弧的指数估计；只看弧顶趋零不能替代这个估计。''')
p(r'''若 $R$ 在实轴上还有有限个单极点 $x_j$，就从上方用小半圆挖开。实段左到右，小弧从角度 $\pi$ 走向 $0$，是顺时针，故
$$\lim_{r\to0^+}\int_{C_{r,j}}F(z)\,\mathrm dz=-\pi\mathrm i\operatorname{Res}(F,x_j).$$
这些点已被排除在内部，不能再计入严格上半平面留数和。负号来自行走方向，不能靠“小弧”二字记忆。''','C003')
p(r'''设上述有理次数条件成立，实轴至多有有限单极点，$a_k$ 为严格上半平面的全部极点，则把小弧贡献移到等式右端得到
$$\begin{aligned}\operatorname{v.p.}\int_{-\infty}^{\infty}R(x)e^{\mathrm imx}\,\mathrm dx={}&2\pi\mathrm i\sum_{\operatorname{Im}a_k>0}\operatorname{Res}(F,a_k)\\&+\pi\mathrm i\sum_j\operatorname{Res}(F,x_j).\end{aligned}$$
实轴无极点时第二和为空；只有确认普通广义积分存在，才可删掉主值记号。实轴有高阶极点时本式的半留数规则不直接适用。''','C002')
p(r'''[例8](#reader-d1d0d9fecaa5d7f1092f)对 $a>0$ 给出
$$\int_0^{\infty}\frac{\sin x}{x(x^2+a^2)^2}\,\mathrm dx=\frac{\pi}{4a^4}\bigl[2-(a+2)e^{-a}\bigr].$$
辅助复函数在原点有单极点、在 $a\mathrm i$ 有二阶极点；但目标实函数因 $\sin x/x\to1$ 在原点可补值，无穷远又绝对可积，所以这个结果是普通积分。先求主值复积分，再取虚部、用偶性取全轴的一半，恰好消除了辅助函数引入的原点障碍。''','C004')
p(r'''[例9](#reader-2587f6ed46acdb77c0c1)的 $R(x)=x/[(x-2)(x-3)]$ 则确有两个实轴极点，上半平面无极点，故只有两份半留数贡献。取分量得
$$\begin{aligned}\operatorname{v.p.}\int_{-\infty}^{\infty}\frac{x\cos x}{x^2-5x+6}\,\mathrm dx&=\pi(2\sin2-3\sin3),\\\operatorname{v.p.}\int_{-\infty}^{\infty}\frac{x\sin x}{x^2-5x+6}\,\mathrm dx&=\pi(3\cos3-2\cos2).\end{aligned}$$
此处主值不能去掉，因为在 $2,3$ 的单极点需要局部对称抵消。''','C005')
bridge('明确实虚部分离需要R实值；用小弧角度方向推导符号；区分辅助函数有瑕点与目标实函数普通可积。')

unit('CH06-S02-SS04','路线可以为指数重新设计；遇到对数与非整数幂，还要加上确定单值分支这一步。')
p(r'''标准半圆不是普遍路线，选择应服从指数在哪个方向衰减，以及另一条边能否变回已知积分。下面三个例子都用整函数或补成整函数的辅助函数，因此闭路积分为零；有用的信息来自不同边之间的关系，而不一定来自非零留数。''')
p(r'''[例10](#reader-3d5d2e3af9a2110e7e88)取 $F(z)=(e^{\mathrm iz}-e^{-z})/z$，原点可去；第一象限四分之一圆把正实轴与正虚轴连接。令 $z=\mathrm iy$ 时，两种指数互换，回程方向使两条直边的实部合成目标积分的两倍；分别估计大弧两种指数后得到普通广义积分
$$\int_0^{\infty}\frac{\cos x-e^{-x}}x\,\mathrm dx=0.$$
原点分子为 $O(x)$，尾部 $\cos x/x$ 条件收敛；若机械补负实轴，$e^{-x}$ 会增长，反而失去这个联系。''','C001')
p(r'''[例11](#reader-23aa816448d1fbf0925f)用 $e^{\mathrm iz^2}$：沿 $z=re^{\mathrm i\pi/4}$ 有 $\mathrm iz^2=-r^2$，振荡被转成高斯衰减。教材取顶点 $0,R,R+\mathrm iR$ 的三角闭路；竖边的积分模不超过 $\int_0^R e^{-2Ry}\,\mathrm dy\to0$，斜边回程带着 $-e^{\mathrm i\pi/4}$ 的微分因子。由高斯积分
$$\int_0^{\infty}e^{-r^2}\,\mathrm dr=\frac{\sqrt\pi}{2},$$
便把实轴上的复振荡积分表示成 $e^{\mathrm i\pi/4}\sqrt\pi/2$。''','C003')
p(r'''比较上式实虚部，就得到两个都收敛的弗雷涅积分：
$$\int_0^{\infty}\cos(x^2)\,\mathrm dx=\int_0^{\infty}\sin(x^2)\,\mathrm dx=\frac12\sqrt{\frac\pi2}.$$
旋转路线并不意味着积分值不变，$\mathrm dz=e^{\mathrm i\pi/4}\mathrm dr$ 是两项相等的来源。无穷远收敛可用变量 $t=x^2$ 后的振荡积分判别，因此最终写的是普通条件收敛积分。''','C002')
p(r'''[例12](#reader-906937b7cb3ea1bfb10c)对 $a>0$、$b\in\mathbb R$，先把指数配方，再把积分线平移至 $\operatorname{Im}z=b/(2a)$。用两条竖边组成矩形，整函数 $e^{-az^2}$ 的闭路积分为零，而竖边有 $e^{-aT^2}$ 的统一衰减，故平移后的积分等于实轴高斯积分。结果为
$$\int_0^{\infty}e^{-ax^2}\cos(bx)\,\mathrm dx=\frac12\sqrt{\frac\pi a}\,e^{-b^2/(4a)}.$$
$a>0$ 保证实轴衰减；$b<0$ 时可向下平移，也可用余弦对 $b$ 的偶性。关键步骤是证明连接边消失，不能仅做配方就宣布路径可平移。''','C004')
bridge('用四分之一圆、三角形、矩形分别解释交换指数、旋转振荡和平移高斯的目的；显式保留三项最终公式与普通收敛限制。')

unit('CH06-S02-SS05','分支差给出积分关系；下一节对数导数则把绕行关系变成零极点的计数。')
p(r'''对数或非整数幂作辅助函数时，先选一个区域内单值解析的分支，才能谈留数。支点必须由割线或绕行排除，不能把不同路径取得的函数值混在一次积分里。分支规定不仅影响两岸值，也影响极点处算出的留数，必须从头到尾一致。''','C001')
p(r'''对[例13](#reader-c2e7dbfb1feb23f90a8e)取 $F(z)=\log z/(1+z^2)^2$，在上半平面固定 $0<\arg z<\pi$ 的限制，并沿原文所用 $0<\arg z<2\pi$ 分支取边界极限。正轴上岸为 $\ln x$，负轴上方为 $\ln x+\mathrm i\pi$；外大半圆和原点上方小半圆闭合。回程方向与偶分母使两直边的目标实部相加，大弧由 $O(\ln T/T^3)$、小弧由 $O(r|\ln r|)$ 消失，所得普通积分为
$$\int_0^{\infty}\frac{\ln x}{(1+x^2)^2}\,\mathrm dx=-\frac\pi4.$$
这不是通常 $(-\pi,\pi)$ 的主辐角命名约定；题目明确的辐角范围优先。''','C002')
p(r'''这条方法可用于 $\int_0^{\infty}R(x)\ln x\,\mathrm dx$：$R$ 需为偶有理函数，正实轴无极点，分母次数至少高两次，并且原点处满足可积条件。取 $R(z)\log z$ 后，负轴边界多出的 $\mathrm i\pi$ 产生可解的积分等式；无穷远和原点的弧估计分别保证闭路的额外项不遗留。只说正实轴无奇点并不能排除原点极点造成发散。''','C003')
p(r'''对实非整数 $p$ 及正实轴无极点的有理函数 $R$，沿正轴割开，取 $0<\arg z<2\pi$。钥匙孔闭路上岸向外、外圆正向一周、下岸向内、内圆反向闭合。上岸 $z^p=x^p$，下岸 $z^p=e^{2\pi\mathrm ip}x^p$，两岸方向相反，故共同系数是 $1-e^{2\pi\mathrm ip}$。若
$$\lim_{z\to0}z^{p+1}R(z)=0,\qquad\lim_{z\to\infty}z^{p+1}R(z)=0,$$
内外弧都消失，并有
$$\int_0^{\infty}x^pR(x)\,\mathrm dx=\frac{2\pi\mathrm i}{1-e^{2\pi\mathrm ip}}\sum_k\operatorname{Res}(z^pR(z),a_k).$$
留数在同一分支下对除原点外全部有限奇点求和；$p\notin\mathbb Z$ 保证分母非零，端点条件对有理函数的幂次保证原积分可积。''','C004')
p(r'''[例14](#reader-d60b0f226a665e952a2f)的 $R(z)=1/(1+z)$ 要同时满足原点和无穷远条件，恰为 $-1<p<0$。唯一极点 $-1$ 的辐角在所选支中是 $\pi$，故留数为 $(-1)^p=e^{\mathrm i\pi p}$，得到
$$\int_0^{\infty}\frac{x^p}{1+x}\,\mathrm dx=-\frac\pi{\sin(\pi p)},\qquad -1<p<0.$$
若选成另一幂值，右侧相位会错；若 $p$ 走到端点，原积分本身也不再收敛。带 $\ln x$ 的目标也可在钥匙孔中用 $(\log z)^2R(z)$，利用两岸平方的差产生线性对数项，但仍需重新算分支值与留数。''','C005')
bridge('将单值性、两岸相位、方向与端点可积性连成同一计算链；明确主支命名不覆盖题设；解释钥匙孔分母和p端点。')

unit('CH06-S03','零点计数只靠边界信息；下一章进一步研究局部信息怎样唯一决定解析函数。')
p(r'''若不求根的位置，只想知道区域里有多少根，应把 $f$ 换成对数导数 $f'/f$。在 $m$ 阶零点 $a$ 附近，分解 $f(z)=(z-a)^m\varphi(z)$、$\varphi(a)\ne0$，便有
$$\frac{f'}f=\frac m{z-a}+\frac{\varphi'}\varphi.$$
后一项在中心解析，所以 $\operatorname{Res}(f'/f,a)=m$；在 $n$ 阶极点 $b$ 同理有 $\operatorname{Res}(f'/f,b)=-n$。不论原来阶数多高，对数导数都变成单极点，其留数恰好保留带符号的重数。''','C001')
p(r'''设 $C$ 为正向简单闭路，$f$ 在 $C$ 及内部除有限极点外解析，并在 $C$ 无零点、极点。内部零点、极点按重数分别计为 $N,P$，则
$$\frac1{2\pi\mathrm i}\int_C\frac{f'(z)}{f(z)}\,\mathrm dz=N-P.$$
边界无零极点保证沿路的商有定义；内部若有本性奇点，也就不满足这条只按零极点计数的条件。''','C002')
p(r'''令 $w=f(z)$，沿 $C$ 一周时，像曲线不穿过 $w=0$。因为 $\mathrm dw=f'(z)\mathrm dz$，积分成为 $\int\mathrm dw/w$：模的对数绕行后回到起值，余下连续辐角的总变化。因此辐角原理为
$$N-P=\frac1{2\pi}\Delta_C\arg f(z).$$
必须沿整条曲线连续追踪角度，起终点的主辐角相减会丢掉所有整圈。[辐角原理示例](#reader-8bb62cbc81bdf9a6ca50)在 $|z|=3$ 内有两个单零点、一个三阶极点，所以总变化为 $-2\pi$。''','C003')
p(r'''右图采用 $f(z)=(z^m-a)/z^p$：左侧是原平面的正向闭圆，右侧是像曲线。先取 $p=0$，移动 $a$ 越过 $R^m$，比较像曲线围住原点的圈数；等号时出现边界零点，公式条件失效。再取 $p>0$，观察原点极点如何扣减绕数；$a=0$ 时必须先约去共同因子，以约后真实零极点计重数。''')
p('[[TEACHING_VISUAL:CH06-N]]')
p(r'''不想直接追踪像曲线时，可找一个边界上占优势的简单项。儒歇定理说：$f,\varphi$ 在简单闭路 $C$ 及其内部解析，且边界处处满足严格不等式 $|\varphi(z)|<|f(z)|$，则 $f+\varphi$ 与 $f$ 内部零点总数相同，均计重数。严格不等式保证从 $f$ 连续变到 $f+\varphi$ 时，边界像不碰原点；若只有等号可能出现，便需另行处理。''','C004')
p(r'''[例15](#reader-aab584a87964965ad6a6)对 $z^6-z^4-5z^3+2$，在单位圆让 $-5z^3$ 主导，其余项的模至多 $1+1+2=4<5$。故单位圆内有三根，虽然主导项只有一个位置为原点，却有三重。章末在环域数根的题同理：分别数外圆和内圆内的根，再作差，但先要检查两条边界都无根。''')
p(r'''首一多项式 $P(z)=z^n+a_1z^{n-1}+\cdots+a_n$ 若在虚轴上无零点，可用从下到上的虚轴和左半大圆闭合。大圆上最高次项贡献 $n\pi$；因此令连续角度变化为 $\Delta_{y:-\infty\to\infty}\arg P(\mathrm iy)=2k\pi$，左半平面根数是
$$N_L=\frac{n+2k}{2}=\frac n2+\frac1{2\pi}\Delta\arg P(\mathrm iy).$$
这里虚轴像线不是闭曲线，$k$ 可以是半整数。[例16](#reader-85699ba620c18755acb4)的 $P(z)=z^5+z^2+1$ 在虚轴变成 $(1-y^2)+\mathrm iy^5$，实虚部不同时为零，连续角度增量为 $\pi$，故左半平面有三根。若虚轴有根，须先单独分离，不能直接代式。''','C005')
p(r'''章末还有用于积分的全局快捷工具。若 $f$ 在某圆外域解析，取绕有限区域一周的负向闭路 $C^-$，定义无穷远留数
$$\operatorname{Res}(f,\infty)=\frac1{2\pi\mathrm i}\int_{C^-}f(z)\,\mathrm dz.$$
若圆外展开为 $\sum b_nz^n$，便有 $\operatorname{Res}(f,\infty)=-b_{-1}$。同一系数在有限点读正号、在无穷远读负号，来自绕无穷远正向对应有限平面的顺时针方向；它与上一章用正次幂分类无穷远奇点是两件不同的读取任务。''','SC001')
p(r'''若 $f$ 在扩充复平面上除有限点 $a_1,\ldots,a_n$ 及 $\infty$ 外解析，则
$$\sum_{k=1}^n\operatorname{Res}(f,a_k)+\operatorname{Res}(f,\infty)=0.$$
这允许用圆外展开代替逐个有限留数相加，也能检查符号。例如 $e^{1/z}=1+1/z+\cdots$ 在无穷远的留数为 $-1$，尽管无穷远是可去奇点；因而“可去点留数为零”那条有限点结论不能原样搬到无穷远的定义。''','SC002')
bridge('用对数导数将阶数压成留数；连续追角与主辐角区别；解释严格儒歇不等式；虚轴开曲线的半圈与无穷远留数的方向符号。')
review[current]['media_review'].append({'id':'CH06-N','evidence':'study-visuals.js argument分支：映射(z^m−a)/z^p；a=0时按max(m−p,0)与max(p−m,0)约因子计数；shift=R^m时返回winding=null。','body_alignment':'正文区分左右平面、边界穿零临界和a=0约因子规则。','fix':None})
finish()
current=None
# Keep every original field while replacing vague repeated captions with concrete mathematical tasks.
updates={
 'CH04-harmonic':{'title':'调和鞍面与实部等值线','model_title':'调和鞍面与实部等值线','formula':r'u=c(x^2-y^2),\quad u_{xx}+u_{yy}=2c-2c=0','purpose':'核对 $u_{xx}=2c$ 与 $u_{yy}=-2c$ 的抵消','action':'改变 $c$ 与 $u$ 等值高度','observation':'显示实部鞍面及单族金色 $u$ 等值线','conclusion':'这份图核对调和性；正交性另用共轭方程判断'},
 'CH04-poisson':{'purpose':'比较 $\u0072^n\u005ccos(n\u005cvarphi)$ 与泊松积分数值','action':'先减小内点半径 $r$，再增大边界次数 $n$','observation':'两种读数一致，高次边界模式向内衰减更快','conclusion':'明确边界数据 $\u005ccos(n\u005ctheta)$ 决定对应圆盘调和延拓'},
 'CH05-U':{'purpose':'比较开圆与闭小圆的统一误差','action':'设 $b=0.99$、$\u005cvarepsilon=0.05$ 后跳至 $n=299$，再对照 $b=1$','observation':'闭小圆为 $b^n$；开圆上确界为 $1$ 且不取到','conclusion':'量词中的同一个 $N$ 只能在固定闭小圆上得到'},
 'CH05-L':{'purpose':'核对 $1/[z(z-1)]$ 的内外两份展开范围','action':'把采样半径从 $0.6$ 调到 $1.4$','observation':'小参数从 $z$ 切换为 $1/z$','conclusion':'中心与有效圆环是展开式的一部分'},
 'CH05-E':{'purpose':'核对 $|e^{1/z}|=e^{\u005ccos\u005ctheta/r}$ 的方向差异','action':'改变接近方向，再减小采样尺度','observation':'正实轴增长、负实轴衰减，图上越界部分被截去','conclusion':'有限图幅不能用来判断函数有界'},
 'CH06-R':{'purpose':'核对极点处于圆内、圆外及路径上的区别','action':'移动实轴极点 $a$，对照 $|a|$ 与 $R$','observation':'内为 $2\u005cpi\u005cmathrm i$、外为 $0$、路径上无定义','conclusion':'留数和只计严格内部奇点'},
 'CH06-D':{'purpose':'比较微分中的径向与切向','action':'移动角参数并减小角增量','observation':'金色切向为 $\u005cmathrm iz$；粉色是漏掉旋转的径向','conclusion':'微分元 $\u005cmathrm d\u005ctheta=\u005cmathrm dz/(\u005cmathrm iz)$ 与三角代换同时保留'},
 'CH06-A':{'purpose':'比较大弧的实际积分与长大上界','action':'分别固定 $q=1,2$ 并增加半径','observation':'绿色积分向量与金色 $\u005cpi R^{1-q}$ 界并列，左图半圆归一化','conclusion':'积分消失要抵消弧长增长'},
 'CH06-N':{'purpose':'比较原闭圆、像曲线与计重绕数','action':'让 $a$ 越过 $R^m$，并检验 $a=0$ 时约因子','observation':'边界像穿原点时计数条件失效','conclusion':'内部零点数减极点数等于连续辐角增量除以 $2\u005cpi$'}
}
for uid,v in units.items():
 for plan in v['visuals']:
  if plan['id'] in updates:plan.update(updates[plan['id']])
 # Ownership is content-only: compact 2/3 prose + 1/3 figure layout is implemented by parent renderer.
 review[uid]['layout_contract']='正文为主线；媒体标记邻接其所解释的具体正文段落。正文2/3与右侧媒体1/3的CSS/渲染由主集成统一实施，本文件不改共享渲染器。'
 review[uid]['reader_anchors_preserved']=re.findall(r'#reader-[0-9a-f]+',original[uid]['body_markdown'])
 if not v['visuals'] and not v['media']:review[uid]['media_review'].append({'status':'本单元无既有选定媒体；未新增kind或音频。'})
 # Strict excerpt condition: an excerpt is one complete unique paragraph of the authored body.
 ps=v['body_markdown'].split('\n\n')
 for c in v['knowledge_coverage']:
  assert c['excerpts'] and all(ps.count(e)==1 for e in c['excerpts']),(uid,c['id'])
 for anchor in review[uid]['reader_anchors_preserved']:assert anchor in v['body_markdown']
 for typ,marker in [('visuals','TEACHING_VISUAL'),('media','TEACHING_MEDIA')]:
  for item in v[typ]:assert v['body_markdown'].count(item['marker'])==1,(uid,item['id'])
 # A metadata-only field is never used to stand in for a visible knowledge paragraph.
 assert list(v['knowledge_coverage']) or not conclusions[uid].get('conclusions')
media=units['CH05-S01-SS02']['media'][0]
media.update({'title':'固定八项的坏点与统一误差带','purpose':'比较绿色坏点与严格误差阈值带的边界','watch_for':'固定八项画面中绿色点恰在上边界，两端曲线仍穿出带外','conclusion':'固定八项的反例由同一构造推广到任意项数，数学公式见正文'})
output={'schema_version':'1.0','units':units}
(D/'wholebook/lessons-CH04-06.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
report={'schema_version':'1.0','scope':'CH04—CH06全部19单元','source_corpus':'data/parse/complex-analysis-v2/original_text','source_lessons':['lessons-CH01-04.json','lessons-CH05-09.json'],'conclusions_source':'conclusions-CH04-06.json','units':review,'verification':{'unit_count':len(units),'main_ids':sum(len(x.get('conclusions',[])) for x in conclusions.values()),'supplement_ids':sum(len(x.get('supplementary_conclusions',[])) for x in conclusions.values()),'coverage_count':sum(len(x['knowledge_coverage']) for x in units.values()),'unique_complete_paragraph_excerpts':True,'all_original_reader_anchors_preserved':True,'all_original_request_ids_preserved':True,'all_original_visual_kinds_preserved':True,'no_new_audio_or_visual_kind':True},'integration_pending':['全书统一正文2/3、右侧紧凑媒体1/3布局由主任务集成。','视频帧级核对由主任务与独立审查承接；本review不代替实际视频观看结论。']}
# Actual current delivery was located by parent; do not confuse historical run-machine paths with missing files.
rr=report['units']['CH05-S01-SS02']
rr['pending_items']=['现片帧级核对由主任务与独立审查承接；本单元保留原request_id与narration，不宣称未观看片段具有动态坏点。']
for mr in rr['media_review']:
 if mr.get('id')=='CH05-NONUNIFORM':
  mr['evidence']='已读旧lesson narration_steps与run state SHA256记录；实际现片由主任务定位到 ../delivery/复变函数-教材连贯版-20261029/book/assets/narrated/，历史/home路径不是当前资源位置。'
  mr['fix']='主任务应结合neural-media.json及poster-curation-report.json核对现片帧与这里的固定n=8解说；若缺动态坏点，只作固定八项演示描述，不能声称画有随n移动的点。'
for mr in rr['media_review']:
 if mr.get('id')=='CH05-NONUNIFORM':
  mr['evidence']='已实际读取delivery/复变函数-教材连贯版-20261029/neural-media.json、narrated.narration.json和poster-curation-report.json；并查看36.266667秒的1280×720 poster：n=8蓝色剖面、绿色1/2坏点、橙色阈值带、sup=1均存在。资源视频SHA256为2845bee1871a581012f27c93d885e7058de19dc86c46d3f4648bcdc41dfe62ce。'
  mr['body_alignment']='正文准确要求比较固定n=8画面中的绿色点、橙色上边界与两端越界部分；任意n的推广由公式说明，不冒称现片中坏点持续移动。'
  mr['fix']='现poster在实轴±1边缘未明确用空心点排除端点，可在后续重渲染中画空心端点并加|z|<1标签；不能把sup=1画为开圆内取得的最大值。完整视频运动帧级由主任务与独立审查复核。'
rr['pending_items']=['已核对现片资源元数据与36.266667秒代表poster，未逐段观看完整视频；完整运动帧级由主任务与独立审查承接。']
(D/'wholebook/author-review-CH04-06.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report['verification'],ensure_ascii=False))
