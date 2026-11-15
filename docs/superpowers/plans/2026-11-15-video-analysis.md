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
- [ ] Local worker：ASR20秒重叠窗口、OCR帧、原始文本/时间/模型身份；真实小样本与取消回归。
- [ ] Core service：导入、持久任务、抽音频与帧、worker调度、真实图像理解/讲义/审核、结果JSON、状态/取消/恢复、CLI。
- [ ] UI/server：视频页面、上传/样例/提交/进度/取消/恢复/结果入口，连贯讲解+转写+帧+原片定位，LaTeX与有声兼容。
- [ ] 协调者：依赖配置、真实第一讲完整新运行、与已有原片核验关键公式/限定，修复独立审查问题；浏览器验证全过程，打包更新源码与结果。

## Frozen service interface
`VideoAnalysisService(workspace_root: Path)` exposes `capabilities()->dict`, `list_jobs()->list[dict]`, `register_upload(stream,length,filename)->dict{id,filename,bytes}`, `submit(payload)->dict`, `get(job_id)->dict`, `cancel(job_id)->dict`, `resume(job_id)->dict`, `artifact(job_id,relative)->Path|None`. `submit` consumes `{source_id, title?,course_id?,force?:bool}`; optional `source_path` is CLI/sample only, not arbitrary frontend payload. `sample()` returns registered supplied example if configured.
Worker CLI `--mode asr|ocr --input PATH --output PATH --model PATH [--chunk-seconds20 --overlap-seconds2]`; asr JSON `{segments:[{id,start,end,text,...}],coverage:{...},identity:{...}}`; ocr input frames manifest `{frames:[{id,path,start,end,...}]}`, output `{frames:[{id,start,end,text,...}],identity:{...}}`. All output IDs stable from caller's input, no model source override.
