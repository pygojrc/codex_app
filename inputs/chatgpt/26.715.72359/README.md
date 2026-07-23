# ChatGPT 26.715.72359 输入

运行：

```bash
uv run --no-project scripts/准备_DMG输入.py
```

脚本会把上级 `macos_pkg/ChatGPT.dmg` 校验后复制到本目录。DMG 本身由
`.gitignore` 忽略，`manifest.json` 和 `ChatGPT.dmg.sha256` 纳入 Git。
