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

## Dream Skin 主题原型

当前版本通过 `versions/26.715.72359/theme.toml` 启用构建期 Dream Skin，首轮预设为
`Gothic Void Crusade`。主题编译器只向 `webview/index.html` 注册同源外部脚本，
生产 launcher 不开放 CDP。

主题原型只构建、不打包：

```bash
uv run scripts/构建_Linux版本.py --no-package
```

人工验收完成前，不运行正式打包和安装命令。需要恢复官方外观时，将
`theme.toml` 的 `enabled` 改为 `false` 后重新构建原型。

## 当前产物

- 原型：`build/ChatGPT-linux-26.715.72359/`
- 通用发行包：`dist/chatgpt-linux-26.715.72359-x64.tar.zst`
- Arch Linux 安装包：`codex-app-linux-26.715.72359-1-x86_64.pkg.tar.zst`
- 发行清单：`dist/manifest.json`

## Arch Linux 软件包

`packaging/arch/PKGBUILD` 将已构建的 Linux 原型封装为仅支持 x86_64 的 pacman
软件包。安装路径为：

- `/opt/codex-app/`
- `/usr/bin/codex-app`
- `/usr/share/applications/codex-app.desktop`
- `/usr/share/icons/hicolor/512x512/apps/codex-app.png`

本地构建：

```bash
uv run scripts/构建_Linux版本.py --no-package
cd packaging/arch
makepkg --cleanbuild --force
```

安装生成的软件包：

```bash
sudo pacman -U ./codex-app-linux-26.715.72359-1-x86_64.pkg.tar.zst
```

GitHub Actions 工作流 `.github/workflows/build-linux-release.yml` 支持手动运行以及
推送 `v*` 标签。手动运行会上传 Actions Artifact；标签运行还会创建 Release。
工作流默认从官方地址下载 DMG，并按源码中的固定 SHA256 校验。仓库 Secret
`CHATGPT_DMG_URL` 可覆盖默认下载地址。

## 本地版本化安装

构建和项目内验收通过后，也可使用原有的本地版本化安装脚本：

```bash
uv run scripts/安装_Linux版本.py
```

脚本会完成以下部署：

- 发行包：`/data/pkg/chatgpt-linux-26.715.72359-x64.tar.zst`
- 应用目录：`/data/opt/chatgpt-gui-26.715.72359`
- 主入口：`/data/bin/chatgpt_gui_26_715_72359`
- Codex 兼容入口：`/data/bin/codex_gui_26_715_72359`
- 应用菜单与桌面快捷方式使用当前 DMG 中的 Codex 官方图标

安装过程不会主动启动 GUI；同版本目录已存在时会保留时间戳备份。

DMG、runtime archive/解包目录、native binaries、build 和发行二进制均由 Git
忽略；来源清单、SHA256、代码、锁文件和文档进入 Git。
