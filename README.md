# AIforStudy

把教材 PDF 转成带讲解、图片、动画和自测的浏览器学习页面。命令行与本地工作台共用同一个引擎，支持一个教学单元、多个章节或整本教材。

当前阶段图版本为 8.0，以 `src/aiforstudy/pipeline/graph.py`、生产阶段注册表和工作区配置为准。旧运行只读，新运行重新建立来源和审核状态。2026-11-14 已核对实际调用链、配置、历史运行与全书交付，见[生产基线](../research/2026-11-14/baseline-production.txt)和[交付基线](../research/2026-11-14/baseline-delivery.txt)。

已交付的“复变函数全书重讲版”包含 76 个正文单元，使用 `tools/build_wholebook_delivery.py` 组合已修订讲稿、媒体和订正。它与下面的通用生成流程共用阅读器，但不代表任意教材已经能自动生成同等质量的重讲内容。真实运行前使用 `./aifs plan` 检查来源准备状态，使用 `./aifs capabilities --json` 检查当前机器的渲染能力。

上一轮已清理旧驱动并修复运行创建、续跑缓存、取消/连接超时和媒体验收接口。该轮冻结验收Python3282通过/41跳过/0失败，Node20通过，新制媒体HTML专项2项通过，见[上一轮验收报告](../文档/02-记录与报告/接口收尾与旧工具清理-20261009/验收报告.md)。真实业务API调用0。

## 运行流程

```text
MinerU → 双源目录 → 正文结构与目录原书资料 → 全书概念索引
  → 作者同次输出：正文 JSON（含习题/答案区来源行号）+ 图片/动画统一需求
  → 正文审核/返修 → 需求核验与后端路由
  → API 模型写 Manim Python → 旁白准备 → 隔离真实渲染 → 实际媒体验收
  → 交互 → 正文/图片/动画组合排版 → HTML
```

只跑一节也会先准备全书基础索引，后续按内容指纹复用。纯习题/答案章按原目录作为只读资料展示；随节习题由正文作者同次划定来源行范围，宿主逐字保存原文、计算摘要，阅读器在所属单元展示。原书习题不再全书统一抽取、拆题、配答案或求解；原书例题照常解析和讲解。生产解析使用 MinerU 已有结果或 API，不回退旧本地 OCR/正则入口。

作者负责提出媒体的教学目的、对象条件、插入位置和验收标准；同一需求文件同时包含图片和动画。后置媒体模型通过现有 API 生成完整绘图代码或 Manim 代码，不能另起一套需求或静默删请求；不调用图像生成模型。生成代码只在隔离 worker 运行，确定错误的资源局部缺失；未能核实的可用候选带状态进入预览。正文修改后必须核验需求仍然对应当前内容。

新静态图和动画均使用 `GeneratedScene`，支持 Manim 场景子类、镜头、变换和更新器；静态图的 `steps` 为空。旧 Matplotlib `build_figure(context)` 和动作 DSL 仅保留历史兼容。每个请求最多三个代码候选，原代码、真实帧、具体问题、修法和冻结通过标准一同返回模型。旁白由 `config/narration.json` 配置，当前默认 Edge 中文语音；运行时先准备旁白，再将实际音频时长交给渲染 worker。步骤时间、字幕和关键帧按实际运行记录。

模型角色以 `config/models.json` 为准。当前 `figures` 为 deepseek-flash、low、200000；媒体 `judge` 为 deepseek-flash、high、393216，正文 `text_judge` 为 deepseek-v4-pro、high、393216。思考强度通过顶层 `reasoning_effort` 发送。审核证据组必须由模型显式引用，再由宿主核验并展开。

`src/aiforstudy/pipeline/graph.py` 是阶段图唯一来源。全书准备为 `mineru → toc → structure → export → body → concepts`；独立原书资料还可由 `body → source_format` 整理格式。生成与交付为 `lesson → text_audit → media_plan → figures → audit → interaction → render → delivery`，渲染也读取独立资料整理结果。实际图像审核在生成资源后进行。

`config/review_mode.json` 当前为 `balanced`，正文、成品媒体和页面的实质审核会运行，部分旧机器门禁冻结。该模式的运行完成状态、各项审核结果和 `release_ready` 分别记录；正文运行完成不会自动授予整书媒体的验收通过状态。`full` 与 `json_only` 的行为由 `core/review_mode.py` 及相应阶段实现定义。

## 常用入口

在源码目录优先使用 `./aifs`，它固定选择相邻 `.venv-linux`，可用 `AIFORSTUDY_PYTHON` 显式覆盖；环境缺失时明确退出，不退回系统 Python 或自动安装。CLI 和本地界面都可通过此入口启动，例如 `./aifs books --json`、`./aifs ui --port 8765 --open`。安装包的 `aifs`/模块入口仍可用，解释器需满足项目依赖。

原有模块入口等价：

```bash
# 列出教材、预览计划：只读，不调用模型
../.venv-linux/bin/python -m aiforstudy books --json
../.venv-linux/bin/python -m aiforstudy plan --book linear-algebra-full --units CH01-S01-SS02 --json

# 能力预检
../.venv-linux/bin/python -m aiforstudy capabilities --json

# 本地浏览器工作台
../.venv-linux/bin/python -m aiforstudy ui --port 8765 --open

# 正式单元运行；会按需调用 API（本轮未执行）
../.venv-linux/bin/python -m aiforstudy run --book linear-algebra-full \
  --units CH01-S01-SS02 --profile release --prepare ensure --parallel 1 \
  --delivery scope-html --json

# 章节范围可替换为 --chapters CH01 或 --chapters CH01,CH02；整本用 --all
# 只检查到需求文件时加 --until media_plan，结果属于阶段完成而非最终交付
# 中断后按原请求/范围恢复（保留每对象返修和每请求尝试次数）
../.venv-linux/bin/python -m aiforstudy resume --run <run-id> --json

# 从已有审核正文与媒体生成诊断快照，不调用模型、不改变原运行状态
../.venv-linux/bin/python -m aiforstudy preview --run <run-id> --units CH01-S01 --json
```

诊断页面及媒体位置清单位于原 run 的 `diagnostics/<snapshot>/`，本地工作台也提供“生成诊断预览（未验收）”。正式页面与诊断页面共用阅读器、媒体样式和播放器。正文使用不可变 ReaderDocument，媒体与交互通过 ReaderLayout/ReaderMount 挂到完整 Markdown 语法块边缘；新生产采用 ReaderProjectionV1，组合身份与是否核实独立；旧 CompositionBinding 只用于显式历史校验。

提示词位于 `src/aiforstudy/blocks/content/prompts` 与 `src/aiforstudy/blocks/media/prompts`。原书习题/答案区只检查来源、归属、边界与原文完整性，不审核题目或原书答案的数学正确性，不要求媒体或交互。生成质量约定与审核输出格式分开；真正生效的缓存是 Runner 阶段快照与逐资源生成/审核身份，旧 `pipeline/cache.py` 已退役。

`release` 使用真实服务；`replay` 只用已保存缓存，缺项即阻断；`smoke` 使用受控替身。模型配置在 `config/models.json`，密钥通过已有本地配置或环境注入，不写入文档或产物。正式程序没有累计 token、费用或总时长预算。`config/execution.json` 只控制单次超时、并发、取消和有限尝试；内容返修按每个对象最多2轮。历史预算模块只供显式本地测试工具使用。

`plan` 不创建 run、不补数据。目录过期时先返回需要准备，准备后重新证明单元身份；不能据旧目录编号生成另一段内容。非法范围语法仍立即拒绝。

## 本地真实试跑的准备与观察

`./aifs local-test` 是测试工具，默认只读，使用生产计划器，不创建运行或统计文件。实际执行须显式加 `--execute --observations <独立日志目录>`；仍由正式引擎运行，不注入受控正文或媒体响应。全书准备和选定单元生成分开调用，准备未完成时工具拒绝直接生成，避免旧ID在目录重建后指向不同内容。

```bash
# 下列两条默认都只看计划，不调用模型
./aifs local-test --book complex-analysis-v2 --phase prepare
./aifs local-test --book complex-analysis-v2 --phase deliver \
  --target '1.1.1=复数的四则运算' --target '1.1.2=共轭复数'
# --target 在准备后的目录中按锚点+标题唯一匹配；不把章引言算作第一单元。
# 确认开跑后，再给对应命令加 --execute --observations <prepare或deliver独立目录>
# 中断后保留原请求和同一观察目录，显式 --phase resume --run-id <原run-id>
```

日志 `model-observations.jsonl` 保存每次真实模型调用的阶段、角色、单元、资源、持久尝试编号、耗时和供应商返回的token字段。媒体审核角色是judge，但发生于figures阶段；audit阶段只核对已有证据。观察器不改模型返回，不影响重试策略，不在正式程序增加费用或累计预算。缓存命中单列，超时、缺失usage及没有观察记录的历史调用标为未知；最终摘要与execution日志对账。阶段总体时间继续看原执行记录，不能把并发请求耗时相加当整次运行时间。

统计写入失败会在摘要的write_errors/token_accounting_complete中明确反映，不为补统计重新付费调用。观察日志没有正文、响应文本、密钥或异常原文；一个日志目录只属于一本书的一次run，续写要求匹配的resume。

## 产物与状态

每个 run 的 `state.json`、`events.jsonl` 和 `execution.json` 记录阶段与调用情况。`work/` 保存版本化正文、作者媒体需求、编译后需求、媒体资源和组合页面。`work/products/render/<章节>.json` 中的 ReaderProjectionV1 与其不可变快照记录实际页面、媒体落点、资源、内容版本和核实状态；现行验收不依赖旧 `media-placements.json`。

- 作者需求与正文同次返回、分开保存；明确无需媒体与缺失需求是不同状态。
- 图片/视频必须有实际文件和对应结果，不能只拿计划或动画代码算完成。
- 媒体资源与当前正文、需求版本绑定；失败、未审核、不可用有具体原因。
- 正式交付须满足当前内容与媒体验收；未验收预览始终带状态，不充当正式通过。
- 旧图运行只读，不能直接套用当前批准；历史文件不是新运行缓存正确性的证明。
- `source_materials.json` 保存独立目录习题/答案资料的原文、目录归属与来源状态；正文 `exercise_regions` 保存随节资料的 1-based 闭区间行号、原文和 `sha256:` 摘要。未定位资料保留目录及页码线索并明确显示状态。
- 自动核实未决会明确保留；局部失败不阻止无关单元渲染，运行可返回 `partial` 和 `preview_available=true`。

## 环境与目录

```text
src/aiforstudy/    当前引擎、内容、媒体、服务与控制台
blocks/parse/     当前解析适配器
blocks/render/    组合阅读器、模板与静态资源
blocks/figures/   仍使用的受控图形库适配器
blocks/model/     仍使用的交互适配器
config/           工作区配置
data/            原始教材、解析/索引及运行数据
tests/            当前回归与受控工程验收
tools/manim_worker/ 隔离动画执行环境
```

Python 3.12 依赖以 `requirements.lock` 为准，Node 检查依赖以 `package-lock.json` 为准。Manim 独立环境由 `requirements-manim.lock` 和 `tools/manim_worker/install_manim_env.sh` 管理；解释器可由 `AIFORSTUDY_MANIM_PYTHON` 或能力配置指定。缺环境应报告阻断，不能自动算通过。

旧 CourseForgeV2 执行源码、旧交付和复制测试工作区已清理；它的安装来源包因锁定记录仍保留。部分 `blocks`/`lib` 是当前明确打包的运行适配器，不能仅因目录名旧就删除。旧直接生成入口仅保留拒绝运行的迁移提示。无消费者的 parse_pipeline、clean_rebuild、authority_chain、authority_promote、reconcepts、run_real_chapter 驱动已删除；使用统一 CLI/工作台，详见[清理清单](../文档/02-记录与报告/接口收尾与旧工具清理-20261009/接口与清理清单.md)。

## 验证与构包

```bash
# 作者协议、提示词和媒体编译的快速回归
../.venv-linux/bin/python -m pytest tests/test_author_media_requirements.py \
  tests/test_content_prompt_v4.py tests/test_media_plan_stage.py -q

# 一图一动画到HTML：受控模型响应，实际绘图、Manim和浏览器验收
# 每次使用新的空输出目录；已有文件会被明确拒绝，避免旧视频冒充新生成
../.venv-linux/bin/python tools/verify_code_media_e2e.py \
  --out /tmp/aifs-media-check-01

# 已有API授权时，使用同一小样真实生成代码并审核实际画面
# 预算包括多帧审核的保守预约；输出目录必须为空
../.venv-linux/bin/python tools/verify_code_media_e2e.py --live-media \
  --budget-tokens 1300000 --out /tmp/aifs-media-api-check-01

# 当前工作区全套测试；tests/conftest.py 加载离线网络保护
../.venv-linux/bin/python -m pytest -q

# 构建到工作区外，避免再次留下可误读的build源码副本
../.venv-linux/bin/python setup.py build --build-base /tmp/aifs-build \
  bdist_wheel -d /tmp/aifs-wheel
```

安装包包含当前 Python 模块、阅读器资源、Manim worker 和必要适配器；工作区 `config`、数据与密钥不打包。独立安装和仓库外调用须实际验证，不能只检查 wheel 文件存在。受控模型响应下的工程通过与真实教材教学质量验收分别记录。
