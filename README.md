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
