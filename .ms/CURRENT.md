# 当前开发主线

## 当前结论

- 当前任务：CHATGPTADAPTER-001 ChatGPT 26.715.72359 Linux 独立适配。
- 当前状态：done_first_pass。
- 当前阶段：Dream Skin 构建期主题原型已完成静态验收，等待人工 GUI 验证；
  主题版本尚未打包、尚未安装。
- 下一步：使用临时 profile 人工检查 Gothic Void Crusade 首页、会话页、设置页、
  菜单、弹窗以及深浅色可读性；人工确认前禁止打包和安装主题版本。
- 完成证据：Electron 42.3.0 官方 SHA256 通过；五个 native artifact 在 ABI 146
  实际加载；18 个补丁精确命中；4 个离线测试通过；两种 transport 均存活 15 秒；
  `dist/manifest.json` 已生成；`inode/directory` 默认程序已修正为 Dolphin；
  JetBrains Linux target 可解析 Toolbox 实际可执行路径；发行包已复制到
  `/data/pkg`，应用、命令入口和 Codex 官方桌面图标已安装；Dream Skin runtime、
  CSS、selector contract 和 Gothic preset 已归档到项目内，主题原型静态验收通过。
- 最后更新：2026-07-24。

## 任务链

| 顺序 | 任务 ID | 名称 | 状态 | 入口 |
| --- | --- | --- | --- | --- |
| 1 | CHATGPTADAPTER-001 | ChatGPT 26.715.72359 Linux 独立适配 | done_first_pass | `.ms/tasks/01_chatgpt_26_715_72359_linux/README.md` |

## 状态规则

- `planned`：计划已确认，尚未实施。
- `in_progress`：正在实现或验证。
- `done_first_pass`：首轮完成，仍有人工或可选能力验收。
- `done`：全部完成并验收。
- `blocked`：明确依赖用户选择或外部条件。
