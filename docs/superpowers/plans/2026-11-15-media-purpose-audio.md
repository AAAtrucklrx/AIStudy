# Media Purpose Audio Implementation Plan

> 用户已授权自主执行。内容、配音和诊断并行；协调者实现UI与集成，修改所有权分离。

**Goal:** 每项现役教学媒体都有可读用途和真实可播放配音，修复实际无声播放。
**Architecture:** authored purpose manifest keyed by unit_id/id; immutable model/text-bound audio; shared player presentation and lifecycle; data binding during delivery build.
**Tech Stack:** Existing Python/JavaScript/KaTeX, local Qwen, FFmpeg, Edge.
**Spec:** docs/superpowers/specs/2026-11-15-media-purpose-audio-design.md

## Constraints / Review Focus
- 原程序和已交付ZIP保留；新增版本发布；用户的扩展/系统配置不改。
- purpose不是画图指令；plan哈希绑定，不能错配或静默缺项。
- file://离线与HTTP均能读取用途音频；拒绝外部/越界资源路径。
- 单一音源、折叠/换页停止；播放拒绝/解码失败必须可见，不能按钮假显示播放。
- 用实际用户profile验证，无声原因与硬件听感证据分开。

## Tasks
- [x] 内容代理：清点Reader实际媒体；逐项读正文/参数，写data/visual-purpose-20261115.json，51项具体用途及spoken_text、plan_sha256。
- [x] 配音代理：tools/media_purpose_audio.py，输入/缓存/失败契约RED→GREEN，分批真实合成51条，逐MP3解码RMS与时长/哈希验收。
- [x] 诊断代理：HTTP/file、静音/未静音、直接视频/Reader隔离Edge对照；原始记录保存；协调者检查实际Edge输出日志和同音频对照。
- [ ] 协调者UI：tests/ui/media_purpose.test.cjs先验证用途可见、公式、互斥/取消/错误/隐藏生命周期；新media-purpose.js/css，study-lesson挂载和模板/build资产接线。
- [ ] 协调者构建：严格用途/plan/音频对应，新增发布版并检查全部51媒体；读取器现有内容与音视频时间线不改变。
- [ ] 独立复核新差异，相关回归、实际有声输出验证；新交付包与明确完成报告。
