# 本机真实教材节选验证

`tools/verify_live_unit.py` 使用当前 `config/models.json` 的账户或 API 路由，通过生产 Gateway、普通作者、正文审核及 Reader 投影函数运行；不注入模型回复，不生成全书准备或发布收据。默认账户路由使用本机已登录账户，无需另填 API key。

先用已核对的真实 PDF 物理页图建立独立实验目录，再运行：

```sh
PYTHONPATH="$AIFS_WORKSPACE/src" "$AIFS_PYTHON" "$AIFS_WORKSPACE/tools/verify_live_unit.py" \
  --workspace "$AIFS_WORKSPACE" --out "$AIFS_EVIDENCE" --pages "$AIFS_PAGE_IMAGES"
```

`AIFS_PAGE_IMAGES` 必须包含 `physical-012.png`、`physical-013.png`、`physical-014.png`，对应当前复变函数教材共轭复数小节。脚本保留原有 OCR、页图哈希、视觉校勘回复、完整提示、真实模型响应、Gateway 调用与执行记录；`--source-only` 只准备页图转录。视觉转录的修正建议是模型意见，不自动当作数学真值；原书印刷差异保留在转录，交普通作者及独立 Pro 审核处理。

输出的 Reader 是明确的节选预览，`preview_only=true`、`production_accepted=false`。这项实验不等于整本 239 页冷 OCR、双源目录、structure 合同或正式 CLI 发布通过。全书入口仍按实际准备依赖执行。已有 `authored.json` 会复用当前实验的实际作者产物；若要证明新生成，必须选一个空的新输出目录。不会回落到 stub。

绘图或动画运行环境需按本机实际安装显式提供 `AIFORSTUDY_MANIM_PYTHON`、`AIFS_BROWSER_EXECUTABLE`、`AIFS_BROWSER_NODE`、`AIFS_PLAYWRIGHT_MODULE`。不要将其他机器的路径照抄进生产配置；缺少依赖时保留阻断及未核实状态。

作者与审核完成后，可在同一目录加 `--media` 继续执行真实作者申请的媒体。脚本使用生产技术规划将图片意图编译为绘图、保留动画需求，通过隔离 Manim 运行及真实画面审核后接入 Reader。账户模型配置与审核额度保持生产值。正文和媒体是否通过以 `review.json`、`media/*/verified-result.json` 及其画面审核证据为准，不能只看脚本退出码。

默认本机 Qwen 旁白必须另外设置 `AIFORSTUDY_TTS_MODEL_DIR`、`AIFORSTUDY_TTS_MODEL_MANIFEST`（verified_complete下载校验记录）、`AIFORSTUDY_TTS_PYTHON`、`AIFORSTUDY_TTS_CACHE_DIR`。未命中缓存时生产后端会真实生成，不要求预先人工写缓存，也不会静默降级到其他语音。

续跑先只读比较旧PDF、页图及原文身份；PDF改变会在执行记录或产物写入前拒绝，并保留原provenance。缓存作者正文及媒体需求必须与原accepted author journal、保留的lesson模型回复经生产归一化后的完整信封一致；缓存正文审核的每份exchange还必须绑定当前正文、来源和策略摘要。任一缺失或不匹配均要求新输出目录，不能借旧accepted结论给改写内容授予通过。单纯更新Reader资源允许离线重建，原模型回复、作者与审核收据不改写，也不算新生成。
