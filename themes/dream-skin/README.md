# Dream Skin 主题资产

本目录保存 Linux 适配构建所需的最小 Dream Skin 源码和可再分发预设，不依赖
项目根的 `Codex-Dream-Skin/` 参考仓库。

来源：

- 上游：`https://github.com/Fei-Away/Codex-Dream-Skin`
- 上游提交：`0f00dce`
- runtime 版本：`1.3.3`
- 引入日期：`2026-07-24`

引入内容：

- `runtime/renderer-inject.js`
- `runtime/dream-skin.css`
- `selectors.json`
- `presets/gothic-void-crusade/`
- `LICENSE` 与 `NOTICE.md`

`Gothic Void Crusade` 是上游公开安装包使用的可再分发默认背景。不要从参考仓库
引入 Arina Hashimoto、运行截图或其它未明确授予再分发权的素材。

更新 runtime 或 selector contract 时，必须同步运行上游 renderer/doctor 测试和本项目
离线测试，并对目标 Codex 版本重新进行真实 DOM 人工验收。
