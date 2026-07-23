#!/usr/bin/env python3
"""从 Tectonic 官方 GitHub Release 下载 Linux x64 runtime。"""

from __future__ import annotations

import hashlib
import json
import shutil
import tarfile
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.16.9"
NAME = f"tectonic-{VERSION}-x86_64-unknown-linux-musl.tar.gz"
URL = (
    "https://github.com/tectonic-typesetting/tectonic/releases/download/"
    f"tectonic%40{VERSION}/{NAME}"
)
EXPECTED = "60b13a0826ae7ad9ce34b4a2df06bff2cfcfa6dda8a915477c0cbb84e1a4a902"
RUNTIME = ROOT / f"runtime/tectonic/{VERSION}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    downloads = RUNTIME / "downloads"
    extracted = RUNTIME / "extracted"
    archive = downloads / NAME
    downloads.mkdir(parents=True, exist_ok=True)
    if not archive.is_file() or sha256_file(archive) != EXPECTED:
        temporary = archive.with_suffix(".part")
        with urllib.request.urlopen(URL) as response, temporary.open("wb") as output:
            shutil.copyfileobj(response, output)
        temporary.replace(archive)
    actual = sha256_file(archive)
    if actual != EXPECTED:
        raise RuntimeError(f"Tectonic SHA256 不匹配: {actual}")
    if extracted.exists():
        shutil.rmtree(extracted)
    extracted.mkdir(parents=True)
    with tarfile.open(archive) as source:
        source.extractall(extracted, filter="data")
    binary = extracted / "tectonic"
    if not binary.is_file():
        raise RuntimeError("Tectonic archive 缺少 tectonic")
    binary.chmod(0o755)
    (RUNTIME / "manifest.json").write_text(
        json.dumps(
            {
                "name": NAME,
                "version": VERSION,
                "source": URL,
                "sha256": actual,
                "size": archive.stat().st_size,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Tectonic runtime: {binary}")


if __name__ == "__main__":
    main()
