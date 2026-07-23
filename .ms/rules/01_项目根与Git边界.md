# 项目根与 Git 边界

## 项目内归位

- DMG 副本：`inputs/chatgpt/<version>/`。
- Electron 下载和解包：`runtime/electron/<version>/downloads|extracted/`。
- native module 配置和构建：`native/electron-<version>/`。
- 通用代码：`src/chatgpt_adapter/`。
- 版本配置与补丁：`versions/<version>/`。
- 构建、发行、缓存和临时内容：`build/`、`dist/`、`.cache/`、`tmp/`。

正式脚本不得读取上级旧版本目录或外部已安装 runtime。

## Git 跟踪

必须跟踪：

- 源码、脚本、测试和文档。
- `pyproject.toml`、`uv.lock`、`package.json`、`pnpm-lock.yaml`。
- 版本配置、patch 定义、manifest、SHA256。
- 小型可复现测试夹具。

默认忽略：

- DMG、Electron archive、Electron 解包目录。
- `node_modules`、native build/artifacts 和 `.node`。
- build、dist 二进制、缓存、临时文件和日志。

大型二进制保留在项目内，由 manifest 和 SHA256 关联；普通 Git 不存储其内容。
