# Electron 42.3.0 Linux x64 runtime

只允许从 Electron 官方 GitHub Releases 下载：

```bash
uv run --no-project scripts/下载_Electron_runtime.py --version 42.3.0 --arch x64
```

下载资产进入 `downloads/`，解包内容进入 `extracted/`；两者均由 Git 忽略。
官方 `SHASUMS256.txt` 和生成的 `manifest.json` 纳入 Git。
