# 当前本机的真实生成配置

工作副本默认使用 `deepseek-account`，通过已安装 DeepSeek Harness 的官方账户 SDK 调用已登录账户。当前已实测 `deepseek-flash` 的文字、图片、用量和取消，以及 `deepseek-v4-pro` 的短文字回答；正文审核仍保留原 Pro 角色，作者与视觉角色仍用 Flash。原角色的思考强度、输出额度及重试策略未降低。

账户桥目前需要 macOS、已安装 Harness 和已有登录。SDK 升级后应重新运行契约检查。失败会明确返回，不回退到模拟结果或另一个未经配置的账户。离线客户端接受某个输出额度不等于远端承诺该额度；实际调用仍记录终止状态和供应商用量。

API 用户可以把 provider 改回 `deepseek`，配置自己的 endpoint 和凭据引用。标准 `env:DEEPSEEK_API_KEY` 保留环境变量到 `.secrets/deepseek.env` 的既有解析顺序；其他环境变量引用不会偷用默认密钥。完整的导入前 API 配置留作测试固定材料 `tests/fixtures/legacy-models-http.json`，不含实际密钥。

本地兼容服务须显式设置角色 provider 为 `local-compatible`、真实模型名和 base_url。匿名访问默认只接受loopback，不为未启动的端点假造可用状态。

在本项目的嵌套工作副本运行媒体和浏览器检查时，需指向已有依赖：设置 `AIFORSTUDY_MANIM_PYTHON` 为已安装的独立 Manim 解释器，`AIFS_BROWSER_EXECUTABLE` 为实际 Chromium/Edge 可执行文件，`AIFS_PLAYWRIGHT_MODULE` 为本工作副本 node_modules/playwright。它们是运行环境覆盖，不应把本用户绝对路径写入可分发源代码。

旧源码和旧交付没有更改。新程序需要重新构建冻结快照，不能把旧版本审核记录当作新版本已通过。
