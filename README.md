# ChatGPT Adapter

本项目从官方 macOS `ChatGPT.dmg` 生成可验证的 Linux x86_64 ChatGPT/Codex
桌面原型、发行包和版本化安装产物。

当前目标版本是 `26.715.72359`，build `5718`，Electron `42.3.0`。

## 核心边界

- 所有适配文件都位于本项目内。
- macOS DMG 和大型 runtime/构建产物保留在项目目录，但不进入普通 Git 历史。
- 正式构建不依赖上级项目的旧版本目录或 `/data/opt` 已安装 runtime。
- Linux 包不携带 macOS `resources/codex`，继续使用系统 native Codex 或外部
  app-server。

当前计划入口：

- `.ms/tasks/01_chatgpt_26_715_72359_linux/docs/2026-07-23_独立项目Linux适配计划.md`

## 构建

所有命令都在项目根执行：

```bash
source scripts/项目环境.sh
uv run --no-project scripts/准备_DMG输入.py
uv run --no-project scripts/下载_Electron_runtime.py
uv run --no-project scripts/下载_Tectonic.py
uv run --no-project scripts/构建_native模块.py
uv run scripts/构建_Linux版本.py
```

`构建_native模块.py` 默认使用 pnpm。当前宿主的 pnpm 11.3.0 网络层在 Node
26 + 代理环境下不可用时，可显式使用项目内后备：

```bash
uv run --no-project scripts/构建_native模块.py --package-manager npm
```

这一路径仍使用固定版本和项目内 npm cache，并生成 `package-lock.json`。不会安装
全局依赖。

## 验证

```bash
uv run python -m unittest discover -s tests -v
uv run --no-project scripts/冒烟_GUI.py --seconds 15
CODEX_APP_SERVER_PORT=18766 uv run --no-project scripts/冒烟_GUI.py --seconds 15
```

- 默认端口有服务时验证 WebSocket 直连。
- 指定未监听端口时验证 Electron 使用 `/data/bin/codex` 启动 stdio app-server。
- 无图形会话时脚本使用 Electron `--headless`，profile 和日志只写入 `tmp/`。

## 当前产物

- 原型：`build/ChatGPT-linux-26.715.72359/`
- 发行包：`dist/chatgpt-linux-26.715.72359-x64.tar.zst`
- 发行清单：`dist/manifest.json`

DMG、runtime archive/解包目录、native binaries、build 和 tar.zst 均由 Git
忽略；来源清单、SHA256、代码、锁文件和文档进入 Git。
