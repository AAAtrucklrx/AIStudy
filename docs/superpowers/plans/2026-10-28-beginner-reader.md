# Beginner Reader Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. 用户已选择并行代理并授权执行。

**Goal:** 实现全书证明与例题默认折叠、逐知识点交互图、浅深分区 UI、有声分步动画，并生成可检查的新阅读包。

**Architecture:** 保留 Python 生成引擎与原生静态阅读器，增加本地交互场景和可替换宿主配音。原 ZIP 与旧阅读页保留，新包独立生成。

**Tech Stack:** Python 3.12、原生 JS/CSS、KaTeX/Marked、Three.js、FFmpeg、本机中文 TTS。

**Spec:** docs/superpowers/specs/2026-10-28-beginner-reader-design.md

## Global Constraints

- 全部证明和全部例题默认折叠，数学内容不删除；不自动打开首次证明。
- 浅色正文＋深色图像区；保持离线资源与原生前端。
- 图像具有真实参数和旋转交互；静态视频不作为交互覆盖。
- 音频必须真实生成并保留在交付中；不以浏览器不确定的语音能力冒充已生成配音。
- 不覆盖原始教材、历史 run 和旧交付物；不公开发布。

## Review Focus

- 正文中夹带的无标题证明，及公式/链接/媒体跨越折叠边界。
- 首次定理和复用浮窗必须采用一致的默认收起行为，点击引用不能无意泄漏答案。
- 多图滚动、导航与折叠后资源释放，不能耗尽 WebGL 上下文。
- 音频长度与原视频步骤不等，暂停/跳步/重播必须对齐。
- 历史空正文、缓存及媒体路径迁移，不能改写原 run 或误标审核通过。

### Task 1: Content and disclosure
Files: content policy/prompts/review, reader_document/theorem_index, render-core.js/app.js/reader-layout.js, associated tests.
- [x] 先更新证明/例题默认折叠的行为测试，运行确认旧实现失败。
- [x] 实现语义证明区和全例题折叠，保留公式与源内容身份；同步生成/审核口径。
- [x] 跑内容与 Node 展示相关回归。

验证：新增行为用例已在旧实现上确认失败；最终 Node DOM 回归（排除 *.browser.test.cjs）226 项中 225 通过、1 跳过、0 失败。内容/渲染 Python 定向回归 169 通过、1 跳过；5 个依赖旧 Linux Chromium 路径的检查未在此命令中执行。完整 pytest 收集被缺少 pymupdf 阻断。原始字段、source map、数学与媒体节点身份均保留，未调用模型、未改旧 run。交叉审阅已修复例题浮窗根节点自动展开、两处真实教材证明提示漏识别，并验证后续结论/解释可见及必要/充分证明原顺序。恢复双曲篇使用真实 5017 字修订与来源 SHA 验证的 6 段精确显示投影，不改原文或哈希；裸“例题”标题的全部 3 个媒体 mount 随例题收起，真实 Edge 已验证展开前后可见性。顶部支持 display_title，保留 book 来源身份。最后修复带题号外层例题一次点击即打开唯一同题内层（裸例题集合保持各题关闭）；引用浮窗与旧概念/详解抽屉按真实来源单元挂接独立 study scope，复用不重复挂载，关闭、替换、换节及 pagehide 释放副本控制器，源图不变。例题summary内原题号链接仅在显示层解包为普通标签，真实app委托下点击标题内部节点也能一次展开；正文其他位置仍保留引用浮窗。

### Task 2: Theme and interactive mathematics
Files: new assets/study-visuals.js, study-reader.css, template; interactive UI tests. 不改 Task 1 所有的三个阅读器 JS 文件。
- [x] 为真实参数变化、旋转/复位、目标绑定与资源释放写测试并确认失败。
- [x] 实现各章数学场景、逐目标挂载、播放演示与统一控制器，加入浅深分区样式。
- [x] 跑离线 Node 测试并以真实教材浏览器验证。

### Task 3: Narration and media pipeline
Files: media contracts/runtime/execution, worker audio handling, assets/animations.js, new narration adapter and tests.
- [x] 为保留合法音轨与分步配音同步写失败测试。
- [x] 增加宿主配音/口语化、实际音频时长、音轨合成/资源登记、播放器音量与同步；更新旧无音轨规则。
- [x] 测试音频流、字幕和分步控制，实际生成中文音频。

### Task 4: Integration and full-book delivery
Files: blocks/render/build.py, tools/upgrade_study_reader.py, config, delivery docs and integration tests.
- [x] 建立依赖与相关基线，记录已有失败。
- [x] 使生产打包携带新资源；另建全书升级包并恢复已确认的双曲函数正确内容。
- [x] 全书遍历验证折叠、图像绑定、实际音频覆盖；抽查跨章与窄屏。
- [x] 独立审阅改动，修正实质问题，记录验证结果与剩余限制。

最终验收：76/76单元，2284处绑定、102类场景，漏挂/未匹配/渲染异常/例题图泄漏0；130/130有声动画全量独立音视频包时钟验收通过，102类图解音频有效；IAB实际桌面、390px、一次展开及浮窗独立调参通过。旧Linux隔离Manim完整重新生成未在Mac执行，未降低隔离。原ZIP与旧阅读器保留。
