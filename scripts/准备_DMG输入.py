#!/usr/bin/env python3
"""把指定 ChatGPT.dmg 复制到项目输入目录并记录 SHA256。"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


APP_VERSION = "26.715.72359"
EXPECTED_SHA256 = "05a76850a5a035bb3e7e3c0b61b7cb0f359c2509e8ec1ed4810526a6bc751abe"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_ROOT.parent / "macos_pkg/ChatGPT.dmg"
INPUT_ROOT = PROJECT_ROOT / f"inputs/chatgpt/{APP_VERSION}"
TARGET = INPUT_ROOT / "ChatGPT.dmg"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()

    source = args.source.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"DMG 不存在: {source}")
    actual = sha256_file(source)
    if actual != EXPECTED_SHA256:
        raise RuntimeError(
            f"DMG SHA256 不匹配: actual={actual}, expected={EXPECTED_SHA256}"
        )

    INPUT_ROOT.mkdir(parents=True, exist_ok=True)
    if not TARGET.is_file() or sha256_file(TARGET) != EXPECTED_SHA256:
        temporary = TARGET.with_suffix(".dmg.part")
        shutil.copy2(source, temporary)
        temporary.replace(TARGET)
    copied = sha256_file(TARGET)
    if copied != EXPECTED_SHA256:
        raise RuntimeError(f"项目内 DMG SHA256 不匹配: {copied}")

    manifest = {
        "name": TARGET.name,
        "appVersion": APP_VERSION,
        "source": str(source),
        "size": TARGET.stat().st_size,
        "sha256": copied,
    }
    (INPUT_ROOT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (INPUT_ROOT / "ChatGPT.dmg.sha256").write_text(
        f"{copied}  ChatGPT.dmg\n",
        encoding="utf-8",
    )
    print(f"项目内 DMG: {TARGET}")
    print(f"SHA256: {copied}")


if __name__ == "__main__":
    main()
