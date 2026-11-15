# 视频解析工作台

运行 `aifs ui --workspace /path/to/workspace --host 127.0.0.1 --port 18916`，打开 `/video`。首页也有“解析教学视频”入口。支持选择本地视频并上传，或者使用已配置的样例视频；任意网站链接自动下载尚未接入此入口。已提供的 Bilibili 第一讲原片可通过样例按钮使用，无需重新找文件。

语音转写和画面文字识别在本机运行；关键帧及识别文字交给当前工作区配置的模型进行视觉理解、连贯讲义整理及独立文本审核。当前本机沿用已登录 DeepSeek Harness 账户，不需要新增 API 密钥。失败不会回退到预写讲义或旧人工整理结果。

环境变量：`AIFORSTUDY_VIDEO_ASR_PYTHON` 指向有 mlx-audio 的解释器，`AIFORSTUDY_VIDEO_ASR_MODEL` 指向已下载的本地 Qwen ASR 模型目录，`AIFORSTUDY_VIDEO_OCR_PYTHON` 可指定普通 Python（默认复用 ASR 环境），`AIFORSTUDY_VIDEO_SAMPLE` 是样例原视频。Apple Vision OCR 需要 macOS 与已有 clang，首次运行编译本机识别器。其余参数参见 `config/video-analysis.example.json`，可以复制为本机 `config/video-analysis.json`；该文件不要放入账号或密钥。

源码 CLI 与网页共用持久服务：`python tools/analyze_video.py --workspace /path/to/workspace --source /path/to/video.mp4 --title 课程标题`；`--sample` 使用已配置原片，`--resume JOB_ID` 恢复。运行记录保存在 `data/video-analysis/jobs/`，上传来源保存在受控的 `data/video-analysis/uploads/`。浏览器只能提交来源ID；任意本地路径导入只提供给本机CLI。

流程包括源检查、完整音轨提取、定时与变化抽帧、20秒/2秒重叠ASR窗口、OCR、实际多图模型分析、连续讲义、独立审核和导出。默认每20秒采样并补充变化帧，总上限96；超长视频会调整采样间隔。输入时长完整处理不等于每句每帧语义正确，结果页分别显示转写窗口、采样帧、原始识别与审核疑问。公式数字、负号和前提冲突不会因任务完成而自动获准。

结果入口 `/video-result.html?job=JOB_ID` 包含连续讲义、章节目录、逐窗转写、画面文字与模型解释、公式及待核实项、来源时间跳转。原图与原始模型回应保留，可导出 Markdown/JSON，原视频可下载。播放器复用纯画面与独立WebAudio兼容输出；1倍速保持原声，倍速会改变音高。

上传、提交、取消和恢复沿用工作台同源与启动令牌保护。新任务和恢复绑定视频、配置、模型权重、运行时、有效传输和代码身份，变更后不能拼接旧阶段。已完成阶段通过原文件hash验证后才复用。当前服务取消会终止并回收子进程；若服务重启后留下识别进程，取消文件在识别窗口/帧边界生效，锁释放前保持“正在取消”。

当前视频功能独立于PDF的MinerU准备路线，不使缺失PDF准备静默退回OCR。视频也不会自动归入复变教材，避免把不同课程的证据混用。
