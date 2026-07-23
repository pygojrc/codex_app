#!/usr/bin/env python3
"""把项目内 DMG 的应用资源提取到可重复生成的分析目录。"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DMG = PROJECT_ROOT / "inputs/chatgpt/26.715.72359/ChatGPT.dmg"
OUTPUT = PROJECT_ROOT / "tmp/dmg-analysis"
BUNDLE = OUTPUT / "ChatGPT Installer/ChatGPT.app"
RESOURCES = BUNDLE / "Contents/Resources"
ASAR = (
    PROJECT_ROOT
    / "native/electron-42.3.0/node_modules/.bin/asar"
)


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    print("+", " ".join(args), flush=True)
    return subprocess.run(args, check=check)


def main() -> None:
    if not DMG.is_file():
        raise RuntimeError(f"项目内 DMG 不存在: {DMG}")
    if not ASAR.is_file():
        raise RuntimeError(f"asar CLI 不存在，请先构建 native 依赖: {ASAR}")
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)
    result = run(
        "7z",
        "x",
        "-y",
        f"-o{OUTPUT}",
        str(DMG),
        "ChatGPT Installer/ChatGPT.app/Contents/Info.plist",
        "ChatGPT Installer/ChatGPT.app/Contents/Resources/*",
        check=False,
    )
    app_asar = RESOURCES / "app.asar"
    if not app_asar.is_file():
        raise RuntimeError(f"DMG 缺少 app.asar: {app_asar}")
    if result.returncode:
        print(f"警告: 7z 返回 {result.returncode}，已按关键文件继续检查")
    run(str(ASAR), "extract", str(app_asar), str(OUTPUT / "app"))
    unpacked = RESOURCES / "app.asar.unpacked"
    if unpacked.is_dir():
        shutil.copytree(unpacked, OUTPUT / "app", dirs_exist_ok=True, symlinks=True)
    print(f"分析目录: {OUTPUT}")


if __name__ == "__main__":
    main()
