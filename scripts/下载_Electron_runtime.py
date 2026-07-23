#!/usr/bin/env python3
"""从 Electron 官方 GitHub Releases 下载并解包 Linux runtime。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import time
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GITHUB_RELEASES = "https://github.com/electron/electron/releases"
USER_AGENT = "chatgpt-adapter-electron-downloader/1.0"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, target: Path, *, reset: bool = False) -> None:
    """按服务端声明的长度循环续传，完成后再原子替换目标。"""
    temporary = target.with_name(f".{target.name}.part")
    if reset:
        temporary.unlink(missing_ok=True)
        target.unlink(missing_ok=True)
    elif target.is_file() and not temporary.exists():
        target.replace(temporary)

    for attempt in range(1, 21):
        offset = temporary.stat().st_size if temporary.is_file() else 0
        headers = {"User-Agent": USER_AGENT}
        if offset:
            headers["Range"] = f"bytes={offset}-"
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request) as response:
                append = offset > 0 and response.status == 206
                mode = "ab" if append else "wb"
                content_range = response.headers.get("Content-Range", "")
                content_length = int(response.headers.get("Content-Length", "0"))
                total = (
                    int(content_range.rpartition("/")[2])
                    if "/" in content_range
                    else content_length
                )
                with temporary.open(mode) as output:
                    shutil.copyfileobj(response, output)
            size = temporary.stat().st_size
            if total and size < total:
                print(f"下载未完整，继续续传: {size}/{total}（第 {attempt} 次）")
                time.sleep(1)
                continue
            break
        except OSError as error:
            if attempt == 20:
                raise
            print(f"下载中断，准备续传: {error}（第 {attempt} 次）")
            time.sleep(1)
    else:
        raise RuntimeError(f"下载重试次数已耗尽: {url}")
    temporary.replace(target)


def expected_sha256(text: str, asset_name: str) -> str:
    for line in text.splitlines():
        digest, _, name = line.partition(" *")
        if name == asset_name and len(digest) == 64:
            return digest
    raise RuntimeError(f"官方 SHASUMS256.txt 中没有资产: {asset_name}")


def extract_zip(archive: Path, target: Path) -> None:
    """安全解包并恢复 ZIP 中记录的 Unix 可执行权限。"""
    temporary = target.with_name(f".{target.name}.extracting")
    if temporary.exists():
        shutil.rmtree(temporary)
    temporary.mkdir(parents=True)
    with zipfile.ZipFile(archive) as source:
        for info in source.infolist():
            path = PurePosixPath(info.filename)
            if path.is_absolute() or ".." in path.parts:
                raise RuntimeError(f"Electron ZIP 包含不安全路径: {info.filename}")
            source.extract(info, temporary)
            mode = info.external_attr >> 16
            extracted = temporary.joinpath(*path.parts)
            if mode and extracted.exists():
                os.chmod(extracted, mode)
    if target.exists():
        shutil.rmtree(target)
    temporary.replace(target)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="42.3.0")
    parser.add_argument("--arch", default="x64", choices=("x64", "arm64"))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    version = args.version.removeprefix("v")
    asset_name = f"electron-v{version}-linux-{args.arch}.zip"
    root = PROJECT_ROOT / f"runtime/electron/{version}"
    downloads = root / "downloads"
    extracted = root / "extracted"
    checksums = root / "SHASUMS256.txt"
    archive = downloads / asset_name
    base_url = f"{GITHUB_RELEASES}/download/v{version}"
    checksum_url = f"{base_url}/SHASUMS256.txt"
    asset_url = f"{base_url}/{asset_name}"

    downloads.mkdir(parents=True, exist_ok=True)
    root.mkdir(parents=True, exist_ok=True)
    if args.force or not checksums.is_file():
        download(checksum_url, checksums, reset=args.force)
    expected = expected_sha256(checksums.read_text(encoding="utf-8"), asset_name)

    if args.force or not archive.is_file() or sha256_file(archive) != expected:
        download(asset_url, archive, reset=args.force)
    actual = sha256_file(archive)
    if actual != expected:
        raise RuntimeError(
            f"Electron ZIP SHA256 不匹配: actual={actual}, expected={expected}"
        )

    if args.force or not (extracted / "electron").is_file():
        extract_zip(archive, extracted)
    version_file = extracted / "version"
    if not version_file.is_file() or version_file.read_text().strip() != version:
        raise RuntimeError(f"Electron 解包版本异常: {version_file}")
    electron = extracted / "electron"
    if not electron.is_file() or not os.access(electron, os.X_OK):
        raise RuntimeError(f"Electron 主程序不存在或不可执行: {electron}")

    manifest = {
        "name": asset_name,
        "version": version,
        "platform": "linux",
        "arch": args.arch,
        "releaseUrl": f"{GITHUB_RELEASES}/tag/v{version}",
        "assetUrl": asset_url,
        "checksumsUrl": checksum_url,
        "size": archive.stat().st_size,
        "sha256": actual,
        "extractedDirectory": "extracted",
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Electron archive: {archive}")
    print(f"Electron runtime: {extracted}")
    print(f"SHA256: {actual}")


if __name__ == "__main__":
    main()
