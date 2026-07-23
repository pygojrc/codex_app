# Electron 42.3.0 native modules

本目录固定 ChatGPT Linux 适配所需的 native module 版本。依赖源码和构建产物都
留在本目录，但 `node_modules/`、`build/`、`artifacts/` 由 Git 忽略。

统一入口：

```bash
source scripts/项目环境.sh
uv run --no-project scripts/构建_native模块.py
```

脚本会使用项目内 pnpm store，为 Electron 42.3.0 x64 重新编译四个模块，并用
项目内 Electron runtime 实际加载。

DMG 应用层声明 `better-sqlite3 12.9.0`，但该版本源码不能通过 Electron 42.3.0
的 V8 external pointer tag API 编译。本目录使用兼容版本 12.11.1 构建二进制，
最终组装时只替换 `better_sqlite3.node`，不替换 DMG 内的 JS。
