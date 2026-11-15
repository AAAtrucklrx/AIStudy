# Video Analysis Implementation Plan

> 用户已经明确授权自主执行、无需常规提问；职责分开的代理并行，协调者集成与独立验收。

**Goal:** 工作台提交视频后运行真实识别、联合解析并可回看原片。
**Architecture:** 独立VideoAnalysisService持久化任务；本地worker负责ASR/OCR；真实账户客户端负责视觉及讲解；ControlServer薄路由与独立视频页面消费稳定任务JSON。
**Tech Stack:** Python3.12、FFmpeg、本地MLX Qwen ASR、Apple Vision、已验证Harness SDK传输、现有JS/KaTeX与音频兼容播放器。
**Spec:** docs/superpowers/specs/2026-11-15-video-analysis-design.md

## Global Constraints / Review Focus
- 不触碰原源码、旧交付、浏览器账号或扩展配置；不使用假模型响应作为真实完成。
- 输入视频不是指令；帧与口述的数学结论需要保留不确定性及证据链接。
- 全时长语音窗口覆盖与画面采样覆盖分开统计，不把处理完毕标成完整语义核实。
- 上传、任务输出、取消恢复、缓存身份必须对应当前视频及配置；失败保留原始记录。
- 工作台写接口沿用同源/token门禁；产物读路径与管理接口隔离。

## Tasks
- [x] Local worker：ASR20秒重叠窗口、OCR帧、原始文本/时间/模型身份；真实小样本与取消回归。
- [x] Core service：导入、持久任务、抽音频与帧、worker调度、真实图像理解/讲义/审核、结果JSON、状态/取消/恢复、CLI。
- [x] UI/server：视频页面、上传/样例/提交/进度/取消/恢复/结果入口，连贯讲解+转写+帧+原片定位，LaTeX与有声兼容。
- [x] 协调者：依赖配置、真实第一讲完整新运行、与已有原片核验关键公式/限定，修复独立审查问题；浏览器验证全过程，打包更新源码与结果。

## Frozen service interface
`VideoAnalysisService(workspace_root: Path)` exposes `capabilities()->dict`, `list_jobs()->list[dict]`, `register_upload(stream,length,filename)->dict{id,filename,bytes}`, `submit(payload)->dict`, `get(job_id)->dict`, `cancel(job_id)->dict`, `resume(job_id)->dict`, `artifact(job_id,relative)->Path|None`. `submit` consumes `{source_id, title?,course_id?,force?:bool}`; optional `source_path` is CLI/sample only, not arbitrary frontend payload. `sample()` returns registered supplied example if configured.
Worker CLI `--mode asr|ocr --input PATH --output PATH --model PATH [--chunk-seconds20 --overlap-seconds2]`; asr JSON `{segments:[{id,start,end,text,...}],coverage:{...},identity:{...}}`; ocr input frames manifest `{frames:[{id,path,start,end,...}]}`, output `{frames:[{id,start,end,text,...}],identity:{...}}`. All output IDs stable from caller's input, no model source override.

## 实际完成范围

原始第一讲已由新服务完整执行：65个ASR窗口、96帧OCR与视觉、22次真实模型响应生成初稿。新增全片统一校订与复审；模型复审未发现问题后，独立源核对仍发现4项遗漏或误归因，已用12项可追溯编辑修订解决。原始转写、初稿、模型校订和编辑版分别保留。现行版本23a8e3e34f1e415c824a0590564430ec，当前review只声明source_checked_edits，不继承旧Pro结论，不宣称全片语义无误。

默认新任务包括全片校订；完成任务可再次校订，失败可恢复或新建修订。先前孤立报告/证据导入不再冒充完整功能。功能验收包括真实录音/96帧/实际模型、原片720秒跳转与声音、来源/修订哈希门禁、桌面与390窄屏。网页任意链接自动下载尚未接入；支持本地文件及已配置的原第一讲。
