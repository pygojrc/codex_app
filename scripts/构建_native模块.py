#!/usr/bin/env python3
"""为项目内 Electron runtime 构建并验证 native modules。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ELECTRON_VERSION = "42.3.0"
NATIVE_ROOT = PROJECT_ROOT / f"native/electron-{ELECTRON_VERSION}"
ELECTRON = PROJECT_ROOT / f"runtime/electron/{ELECTRON_VERSION}/extracted/electron"
ARTIFACTS = {
    "better-sqlite3": "better-sqlite3/build/Release/better_sqlite3.node",
    "node-pty": "node-pty/build/Release/pty.node",
    "@serialport/bindings-cpp": (
        "@serialport/bindings-cpp/build/Release/bindings.node"
    ),
    "node-hid": "node-hid/build/Release/HID.node",
    "node-hid-hidraw": "node-hid/build/Release/HID_hidraw.node",
}
BUILD_MODULES = (
    "better-sqlite3",
    "node-pty",
    "@serialport/bindings-cpp",
    "node-hid",
)


def run(*args: str, env: dict[str, str]) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=NATIVE_ROOT, env=env, check=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def patch_rebuild_cache_path() -> None:
    """让 electron-rebuild 的 headers 缓存遵守项目目录边界。"""
    constants = NATIVE_ROOT / "node_modules/@electron/rebuild/lib/constants.js"
    text = constants.read_text(encoding="utf-8")
    original = (
        "export const ELECTRON_GYP_DIR = "
        "path.resolve(os.homedir(), '.electron-gyp');"
    )
    patched = (
        "export const ELECTRON_GYP_DIR = process.env.ELECTRON_GYP_DIR "
        "|| path.resolve(os.homedir(), '.electron-gyp');"
    )
    if original in text:
        constants.write_text(text.replace(original, patched), encoding="utf-8")
    elif patched not in text:
        raise RuntimeError(f"无法重定向 electron-rebuild cache: {constants}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--package-manager",
        choices=("pnpm", "npm"),
        default="pnpm",
        help="默认使用 pnpm；仅在 pnpm 网络层不可用时显式选择 npm",
    )
    args = parser.parse_args()

    if not ELECTRON.is_file():
        raise RuntimeError(f"请先下载项目内 Electron runtime: {ELECTRON}")
    if shutil.which(args.package_manager) is None:
        raise RuntimeError(f"未找到 {args.package_manager}")

    env = os.environ.copy()
    env.update(
        {
            "PNPM_STORE_PATH": str(PROJECT_ROOT / ".cache/pnpm-store"),
            "npm_config_cache": str(PROJECT_ROOT / ".cache/npm"),
            "npm_config_devdir": str(PROJECT_ROOT / ".cache/node-gyp"),
            "ELECTRON_CACHE": str(PROJECT_ROOT / ".cache/electron"),
            "ELECTRON_GYP_DIR": str(PROJECT_ROOT / ".cache/electron-gyp"),
            "TMPDIR": str(PROJECT_ROOT / "tmp"),
        }
    )
    for path in (
        Path(env["PNPM_STORE_PATH"]),
        Path(env["npm_config_cache"]),
        Path(env["npm_config_devdir"]),
        Path(env["ELECTRON_CACHE"]),
        Path(env["ELECTRON_GYP_DIR"]),
        Path(env["TMPDIR"]),
    ):
        path.mkdir(parents=True, exist_ok=True)

    if args.package_manager == "pnpm":
        run(
            "pnpm",
            "install",
            "--ignore-scripts",
            "--frozen-lockfile=false",
            "--store-dir",
            env["PNPM_STORE_PATH"],
            env=env,
        )
        rebuild = ("pnpm", "exec", "electron-rebuild")
    else:
        run("npm", "install", "--ignore-scripts", env=env)
        rebuild = ("npm", "exec", "--", "electron-rebuild")

    patch_rebuild_cache_path()
    run(
        *rebuild,
        "--version",
        ELECTRON_VERSION,
        "--arch",
        "x64",
        "--force",
        "--build-from-source",
        "--only",
        ",".join(BUILD_MODULES),
        env=env,
    )
    # electron-rebuild 不会重建带 N-API prebuild 的 serialport，显式从源码构建。
    run(
        str(NATIVE_ROOT / "node_modules/.bin/node-gyp"),
        "rebuild",
        "--directory",
        str(NATIVE_ROOT / "node_modules/@serialport/bindings-cpp"),
        f"--target={ELECTRON_VERSION}",
        "--arch=x64",
        "--dist-url=https://electronjs.org/headers",
        f"--devdir={env['ELECTRON_GYP_DIR']}",
        env=env,
    )

    artifacts: list[dict[str, object]] = []
    for name, relative in ARTIFACTS.items():
        source = NATIVE_ROOT / "node_modules" / relative
        if not source.is_file():
            raise RuntimeError(f"native module 构建产物不存在: {source}")
        artifacts.append(
            {
                "module": name,
                "relativePath": f"node_modules/{relative}",
                "size": source.stat().st_size,
                "sha256": sha256_file(source),
            }
        )

    probe = NATIVE_ROOT / "scripts/验证加载.cjs"
    probe_env = env.copy()
    probe_env["ELECTRON_RUN_AS_NODE"] = "1"
    run(str(ELECTRON), str(probe), env=probe_env)
    manifest = {
        "electronVersion": ELECTRON_VERSION,
        "electronArch": "x64",
        "compatibilityOverrides": {
            "better-sqlite3": {
                "appJavaScriptVersion": "12.9.0",
                "nativeBuildSourceVersion": "12.11.1",
                "scope": "仅替换 better_sqlite3.node",
            }
        },
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "artifacts": artifacts,
    }
    (NATIVE_ROOT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"native manifest: {NATIVE_ROOT / 'manifest.json'}")


if __name__ == "__main__":
    main()
