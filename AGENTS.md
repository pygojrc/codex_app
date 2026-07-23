# ChatGPT Adapter 仓库规范

## 项目边界

- `chatgpt_adapter/` 是 ChatGPT macOS DMG 适配 Linux 的独立项目根目录。
- 适配源码、版本配置、补丁、文档、输入副本、下载的 Electron runtime、
  native module 构建环境、构建产物和临时文件都必须位于本项目根目录内。
- `../codex_app/version_26.707.72221/` 只允许作为迁移初期的只读参考；正式构建、
  测试和打包不得依赖其文件。
- `/data/opt/codex-gui` 等已安装版本不得作为新版本构建输入。
- 系统工具以及部署时使用的系统 native `codex` 不属于项目文件；其版本必须写入
  验收记录。

## 开发与文件管理

- 回复、文档和注释使用简体中文；代码变量和函数名使用简单英文。
- 进入项目后依次读取 `AGENTS.md`、`.ms/README.md`、`.ms/CURRENT.md`。
- 新任务文档放入 `.ms/tasks/`；运行记录只允许追加。
- Python 使用 `uv`；JS/TS 和 native module 构建使用 `pnpm`。
- 下载、缓存和临时目录必须通过项目内环境变量指向 `.cache/`、`tmp/` 或对应
  runtime/native 目录，不得把外部缓存当作可复现输入。
- 优先采用最小侵入和配置驱动设计。版本差异应尽量落在
  `versions/<version>/`，通用构建能力放在 `src/`。
- 单个代码文件接近 600 行时，先检查职责是否需要拆分。

## Git

- 跟踪源码、脚本、文档、patch 定义、版本配置、lockfile、manifest、SHA256 和
  小型测试夹具。
- 默认忽略 DMG、Electron 压缩包及解包目录、`node_modules`、native 二进制
  产物、构建目录、发行包、缓存、临时文件和日志。
- 不使用 Git LFS，除非用户以后明确要求对大型二进制做版本管理。
- 提交使用 Conventional Commits；summary 和 body 使用简体中文。
- 不主动回滚用户已有改动，不修改项目外无关文件。

## 验证与部署

- 每个下载输入必须有来源、版本、大小和 SHA256 manifest。
- macOS Mach-O 不得进入 Linux 原型和发行包。
- native module 不仅检查 ELF，还必须用目标 Electron 实际加载。
- 构建、打包和 smoke 默认全部在项目内完成。
- 安装到 `/data/opt`、写 `/data/bin` 或启动 GUI 属于部署阶段；没有用户明确
  要求时不执行。
