# CHATGPTADAPTER-001 ChatGPT 26.715.72359 Linux 适配

## 目标

在独立 `chatgpt_adapter/` Git 项目中，从项目内 DMG 输入构建并验证
ChatGPT/Codex `26.715.72359` Linux x86_64 版本。

## 状态

- `done_first_pass`
- 正式计划：`docs/2026-07-23_独立项目Linux适配计划.md`
- 首轮独立构建、发行包、静态验收与 headless 动态冒烟已经完成。
- 待有图形会话时人工验收登录、线程、终端、Open with 和 Spark 请求。

## 完成标准

- 所有适配文件和构建输入位于项目内。
- Electron 42.3.0 与 native modules 可复现构建并实际加载。
- Linux patch、sidecar、插件、stdio/WebSocket 路径通过验证。
- Git 工作树不包含 DMG、runtime、native binary、build/dist 等大文件。
- 发行包有 manifest 和 SHA256，部署不覆盖旧版本。
