# CHATGPTADAPTER-001 ChatGPT 26.715.72359 Linux 适配

## 目标

在独立 `chatgpt_adapter/` Git 项目中，从项目内 DMG 输入构建并验证
ChatGPT/Codex `26.715.72359` Linux x86_64 版本。

## 状态

- `planned`
- 正式计划：`docs/2026-07-23_独立项目Linux适配计划.md`
- 本轮只完成项目边界和计划，不下载 runtime、不实现、不构建、不安装、不启动。

## 完成标准

- 所有适配文件和构建输入位于项目内。
- Electron 42.3.0 与 native modules 可复现构建并实际加载。
- Linux patch、sidecar、插件、stdio/WebSocket 路径通过验证。
- Git 工作树不包含 DMG、runtime、native binary、build/dist 等大文件。
- 发行包有 manifest 和 SHA256，部署不覆盖旧版本。
