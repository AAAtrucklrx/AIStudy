# AIforStudy 教学与证据改进 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Track steps with checkboxes. 用户已明确授权自主执行，不再发起常规选择或计划审批问题。

**Goal:** 在保留现有 Reader、graph8 和精修教材的基础上，补齐真实无密钥生成、教学呈现、视频证据、自然配音和来源明确的复习功能。

**Architecture:** 继续复用 Gateway、LessonContentV4/TeachingPlanV1、不可变 ReaderDocument/ReaderProjection 和真实旁白时间线。新增传输与来源适配、显式阅读角色以及宿主编译的呈现元数据；模型输出与核验状态分开。现有精修书通过局部编辑与新快照构建，不重新假设其已有功能缺失。

**Tech Stack:** Python3.12、Pydantic、现有原生 JavaScript/KaTeX/Manim、FFmpeg；可用的本地模型与受支持 Harness 账户接口。

**Spec:** `docs/superpowers/specs/2026-11-15-teaching-upgrade.md`

## Global Constraints

- 视频实验可运行项先完成，外部访问/订阅阻塞如实记录；生产修改在随后执行。
- 原源码非Git仓库。使用独立工作副本 `work/2026-11-15/AIforStudy`，保留原源码、原交付和基线哈希；不在原目录初始化Git或覆盖原成品。
- 用户要求证明和例题默认折叠，核心结论与必要条件默认可读；例题通用结论不能只藏在例题。
- 全应用浅色；现有正确的公式上下限、LaTeX字幕、文字稿和媒体定位保留。
- 本地无需密钥的中国模型允许；需用户提供API密钥的中国云端服务停用。无授权不新增订阅、账户权限或接受新协议。
- 不用假云密钥绕过 factory，不用替身响应冒充真实生成，不从浏览器抽取会话凭据。
- 保持 balanced 实质审核；不一键启用全部旧机器门，也不关闭实质审核来刷通过。
- 模型缓存、凭据、无关下载不进入交付包。编辑后的内容不能沿用编辑前审核结论。

## Review Focus

1. 同名模型切换HTTP/本地/账户后串缓存：传输身份进入新请求身份，旧冻结记录不重写。
2. 核心结论在元数据或折叠例题中存在，但主正文不可见：呈现检查必须看主阅读块。
3. 视频时间、哈希、裁剪和课程归属错配：导入拒绝不一致输入，不能凭模型自述盖验证章。
4. 公式/长小数/否定词正确性被EOS、score或ASR对齐掩盖：保留本轮负例并区分执行与质量。
5. 旧精修书与新普通生成在资产相同而数据不同的情况下行为分叉：两条路径都实际构建和检查。

## Task 0：隔离副本与可重放基线

**Files:** 工作副本全部源文件；研究目录基线清单；新副本 `.gitignore` 与本计划。

**Interfaces:** 后续路径均相对于工作副本。原始素材可复制，生成输出、解析缓存、模型缓存与原目录隔离。

- [x] 确认当前不是Git仓库，检查另一个项目聊天是否仍在写相同原目录并协调来源版本。
- [x] 复制源码、配置、必要数据与测试，排除解释器环境、node_modules、模型缓存和凭据；记录源文件hash。原数据不通过可写符号链接共享。
- [x] 在副本建立本地版本基线，使用已知可用解释器/依赖运行适当基线检查，记录真实失败（包括孤立dsh测试），不把旧报告当本次通过。
- [x] 将spec/plan与审计清单带入副本；明确各实现者文件所有权，汇总文件由协调者合并。

## Task 1：真实本地/账户传输

**Files:** 新建 `src/aiforstudy/providers/dsh_account.py`、必要的受支持账户bridge、`local_compatible.py`、`routing.py`；修改 `providers/factory.py`、`gateway.py` 和配置校验；测试 `tests/test_dsh_account_transport.py`、新增本地路由与缓存用例。

**Interfaces:**
- 所有最终传输保留既有 `Transport.__call__(*, model, effort, messages, images, max_tokens, timeout) -> tuple[str, dict]`。
- `DshAccountTransport(model=..., workspace_root=...)` 提供 `request_body(...) -> dict`、`calls`、真实调用与取消；已有测试约定的 `raise_bridge_error(payload)` 和 `normalize_usage(payload)` 继续成立，计数语义须与官方本地实现核对。
- `LocalCompatibleTransport` 明确接受本地服务配置，不依赖 `DEEPSEEK_API_KEY`。不鉴权模式只默认允许loopback。
- `RoleTransportRouter.for_role(role: str)` 返回相应真实传输，Gateway按角色绑定；单传输旧调用保持可用。每个传输暴露不含密钥的 `cache_identity`，新增身份进入新请求指纹。

- [x] 运行已有8个dsh契约用例，保存缺模块基线；增加显式本地无密钥、非loopback拒绝、角色路由和同模型不同传输不串缓存的失败用例。
- [x] 按官方已安装 Harness 的支持接口实现bridge。先校验输入/图像，再访问账户；拒绝不支持的tool/audio/远程图像输入，不能静默降级。不得自行实现网页登录/抽取cookie。
- [x] 保留角色顺序、实际图像字节、来源标签、原始响应、供应商实际usage及取消语义。provider私有参数按能力映射，不能统一发送空think/JSON参数。
- [x] 运行离线契约及真实短文本/真实图片调用，验证内容、取消、脱敏、供应商身份与计数；账户图像不可用则明确限制并为图像角色选择已实测本地路径。
- [x] 对工作副本提交这一独立变更与验证记录。

## Task 2：通用教学呈现与显式折叠角色

**Files:** `blocks/content/content_contracts.py`、作者/审核提示词、`reader_document.py`、新建 `teaching_projection.py`；`blocks/render/diagnostics.py`；必要的 `blocks/render/assets/reader-layout.js`、`study-lesson.js`；新增Python/Node呈现行为用例。

**Interfaces:**
- 继续以 `TeachingPlanV1.claims`、conditions、source_refs 为内容真值，不新增另一套作者结论库。
- 给 `TeachingEvidenceV1` 增加可选精确正文 `quote` 与 `reader_role`（`main/proof/worked_example`，兼容默认main）。既有theorem/examples结构继续支持。
- `compile_teaching_presentation(content: LessonContentV4, reader: ReaderDocumentV1) -> dict` 校验引用并编译稳定block身份、核心claim覆盖和折叠区。拒绝歧义/不存在/跨不完整Markdown块的定位；不能改动冻结正文来伪造旧hash。
- Reader接收宿主编译的呈现元数据；旧手写 `study_lesson` 保持兼容。媒体仍取已有ReaderLayout/ReaderMount，不另生随机需求。

- [x] 添加行为用例：结论含条件在main可见；证明/完整例题默认关闭；例题迁移结论主线可见；错误quote/claim/旧document hash被拒绝；旧精修单元保持内容和媒体身份。
- [x] 修改作者合同：连续解释问题、符号、意义、使用条件和承接；将正式推演显式标为可选。首次术语提供短解释；不得只把教学目标和条件写进元数据。
- [x] 让普通生成的Reader也消费该投影。正文媒体的右侧呈现复用已有机制，折叠证明内的媒体不能被拉到主阅读区泄露。
- [x] 将来源覆盖检查与语义审核分开：有效锚点不自动等于完整/正确。复用已有SourceObligation；对新教学合同逐项反馈缺失，不强迫作者逐字照抄原书。
- [x] 实际构建一个普通生成单元与一个既有精修单元，检查可见正文、折叠、source refs、媒体绑定与页面审核身份。

## Task 3：正式视频证据与回看

**Files:** 新建 `core/video_evidence.py`、相关CLI导入/检查入口及Reader证据视图；扩展现有source-reference/catalog和snapshot依赖接缝，避免平行生成器。

**Interfaces:**
- `validate_video_evidence(manifest_path: Path) -> dict` 做版本、文件/hash、流/时基、区间、bbox、ID与引用验证。
- `import_video_evidence(manifest_path: Path, destination: Path) -> dict` 建内容寻址只读包；不自动关联不同课程。
- `project_video_evidence(bundle: Path, output: Path) -> dict` 提供原片/帧/时间定位与观察记录；模型候选、识别原稿、解释和核查分开。
- 既有 `SourceRefV1` 的kind/id/path/json_pointer/hash可定位视频观察；视频具体PTS等放在专属manifest，由宿主解析并纳入冻结上下文身份。

- [x] 添加失败用例：路径越界/外部符号链接、文件hash变化、负或越界时间、错误time_base、裁剪越界、重复ID、引用不存在、模型自称verified不能自动升为宿主核验。
- [x] 导入本轮第一讲真实产物，保留原片SHA、真实音频/帧和失败状态；不把电磁学实验自动算入复变考点。
- [x] 为真实可用路径提供可恢复的提取/导入入口，复用实验中验证过的解码、短窗及原始输出记录。无需把33种试验全部设为产品默认依赖。
- [x] 将数字负号、重复输出、同页中间态、时间偏移和口述限定丢失纳入回归材料。新增Reader回看用实际视频验证跳转。

## Task 4：正文局部编辑、图文语义与全浅色

**Files:** 三份 `data/study-revision-20261029/wholebook/lessons-CH*.json`、必要的图解计划及作者提示词；`resources/control-ui/styles.css`；复用现有全文构建工具。

- [x] 逐单元核对76份主叙述，重点正式证明/完整例题演算泄漏、首次术语和前后承接。使用教学审计的7单元/30页证据为起点，未查69单元继续审，不宣称抽样等于全书检查。
- [x] 仅折叠正式推演，保留可直接使用的结论、条件、意义和方法。修正源证据确认的OCR/原书笔误归因；φ/θ只按具体原页修改，不做全局替换。
- [x] 每个保留或新增视觉计划有明确问题/对象/参数/观察点/结论，且定位到实际正文。检查原有39图与12动画，修正不合题意或缺连接的项；补图以教学缺口为依据。
- [x] 控制台固定浅色，保留已有Reader/书架浅色与正常交互。只有实际视觉检查发现问题时才调整现有Reader资产。
- [x] 重新验证418来源/覆盖锚点、必要条件、主线可见性和media marks；实际浏览器看前三节、极限/一致收敛及后章，含窄屏和数学文字稿。

## Task 5：真实自然配音

**Files:** 复用 `blocks/media/narration.py`、`narration_providers.py`、`code_runtime.py`；必要时新增独立本地speech worker；配音配置和现有重配音工具。

- [x] 使用既有真实口播脚本冻结同稿对照。至少两个实际可运行候选生成音频，记录提供商/模型/声音身份、文本、原始wav、读音/时长/停顿核对及选择理由；不以注册接口或模型宣传代替试听/实验。
- [x] 对数学符号口播与LaTeX展示分别管理，保留已有禁止模型自盖spoken_review的合同。声线前后一致；不克隆本次教师声音。
- [x] 通过已有command/HTTP或明确本地适配接入所选方案，缓存身份包含有效模型/声线/文本配置；缺依赖明确失败，不静默回退机械语音。
- [x] 实际替换12段动画的57步骤口播，使用实测PCM时长重配视频、字幕和文字稿。检查短段/长段、公式读法、断句、音画动作与播放跳转。

## Task 6：习题、考试来源与回测

**Files:** 扩展现有 `core/course_library.py` 附近的独立题目/考点分析模块与工具，保留原题；复用研究归档及Reader资料库。

- [x] 从原PDF建立可追溯题目/小问/公式/题型记录，答案与题目独立归属；教材题池与已布置状态分开。
- [x] 严格区分A/B、专业/H、年份和教师；去重题源，标记仅答案或原题已知错误。
- [x] 实现冻结历史输入、按时间留出卷的确定性复习排序与基线回测。固定推荐题数/覆盖预算；不能把留出材料用于调参或题目生成输入。
- [x] 输出有原题定位的复习优先级/模拟练习及不确定性。验证来源、题型/条件、计算与答案，不承诺未知未来原题。

## Task 7：新快照、独立复核与交付

- [x] 运行各任务针对性检查，再跑项目要求的相关回归；已有成功项不无故重复测试。确认遗留失败已解释或修复。
- [x] 使用真实生成路径跑代表性端到端；来源准备不满足时补真实准备或明确测试为节选，不伪造原书全流程通过。
- [x] 对修改文件和成品做独立审查，检查未解决问题、源版本、审核状态、未渲染资源与播放器/字幕。
- [x] 构建新的本地阅读成品和完整源码包，包含必要声明及复现入口，不含凭据/模型缓存。保留旧成品作对照。
- [x] 最终逐项报告改了什么、实际执行了什么检查、哪些外部限制仍在；只按真实产物声明完成。

## 自查与执行方式

本计划覆盖教学文字、结论完整性、折叠、可解释媒体、音频、LaTeX、浅色、视频证据、习题/考试、账户接入及验证。执行采用职责分开的子agent与协调者集成；共享schema/配置/汇总由指定单一所有者修改，其他任务用既定接口。用户已授权自主选择与执行，计划不再送交常规审批。遇到新的事实应更新本计划与结果记录，而不是静默扩大结论。

## 最终执行口径

勾选表示已执行本条工作并交付证据，不表示解除所有限制。完整原书冷启动生成只完成真实节选及正常快照重建；视频不具备完全理解保证；考试分析不具备严格历史可得性或未来命中保证；配音和教学收益未做真人偏好或学习实验。最终相关回归808项Python、330项Node通过，分别1项跳过；不宣称全部遗留Python测试通过。详细验收、保留限制和打包结果见交付说明及 .superpowers/sdd/2026-11-15-teaching-upgrade/progress.md。
