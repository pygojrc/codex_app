# 项目共享语言

- `项目根`：`/data/projects/Local/codex_app/chatgpt_adapter`。
- `输入`：复制到 `inputs/` 的 DMG、校验和及来源 manifest。
- `runtime`：项目内下载并解包的目标 Electron Linux runtime。
- `native module`：为目标 Electron 构建的 Linux `.node` 模块及其可复现构建配置。
- `原型`：尚未打包的 Linux 应用目录。
- `发行包`：由原型生成的 tar.zst 等可部署文件。
- `部署产物`：明确部署后位于 `/data/opt`、`/data/bin` 或 `/data/pkg` 的文件，
  不属于项目构建输入。

不要把上级项目的 `version_26.707.72221` 或已安装 `/data/opt/codex-gui`
称为当前 runtime；它们只属于参考或历史部署。
