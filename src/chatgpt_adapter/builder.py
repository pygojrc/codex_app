"""从项目内 DMG 和 Electron runtime 组装 Linux 原型。"""

from __future__ import annotations

import os
import plistlib
import shutil
import textwrap
from pathlib import Path

from .common import (
    copy_entry,
    ensure_dir,
    ensure_file,
    is_macho,
    make_executable,
    read_json,
    run,
    sha256_file,
)
from .config import APP, ASAR_CLI, DMG, NATIVE_ARTIFACTS, NATIVE_MODULES, RUNTIME
from .patching import apply_patches
from .plugins import compose_plugins


def _extract_dmg(extract_root: Path) -> tuple[Path, Path]:
    prefix = APP.resources_prefix
    wanted = [
        f"{APP.bundle_root}/Contents/Info.plist",
        f"{prefix}/app.asar",
        f"{prefix}/app.asar.unpacked/*",
        f"{prefix}/codex-notification.wav",
        f"{prefix}/icon-chatgpt.png",
        f"{prefix}/owl-electron-app.json",
        f"{prefix}/plugins/openai-bundled/.agents/plugins/marketplace.json",
    ]
    for name in APP.active_plugins:
        wanted.append(f"{prefix}/plugins/openai-bundled/plugins/{name}/*")
    result = run(["7z", "x", "-y", f"-o{extract_root}", str(DMG), *wanted])
    if result.returncode:
        raise RuntimeError(f"7z 解包失败: {result.returncode}")
    bundle = extract_root / APP.bundle_root
    resources = bundle / "Contents/Resources"
    ensure_file(bundle / "Contents/Info.plist", "DMG 缺少 Info.plist")
    ensure_file(resources / "app.asar", "DMG 缺少 app.asar")
    ensure_dir(resources / "app.asar.unpacked", "DMG 缺少 app.asar.unpacked")
    return bundle, resources


def _validate_metadata(bundle: Path, extracted: Path) -> None:
    with (bundle / "Contents/Info.plist").open("rb") as stream:
        info = plistlib.load(stream)
    plist_expected = {
        "CFBundleShortVersionString": APP.version,
        "CFBundleVersion": APP.build_number,
        "CFBundleIdentifier": "com.openai.codex",
    }
    for key, expected in plist_expected.items():
        if info.get(key) != expected:
            raise RuntimeError(f"Info.plist {key} 异常: {info.get(key)!r}")
    package = read_json(extracted / "package.json")
    expected_values = {
        "name": APP.package_name,
        "version": APP.version,
        "codexBuildNumber": APP.build_number,
        "codexAppBrand": APP.brand,
    }
    for key, expected in expected_values.items():
        if package.get(key) != expected:
            raise RuntimeError(f"package.json {key} 异常: {package.get(key)!r}")
    if package.get("devDependencies", {}).get("electron") != APP.electron_version:
        raise RuntimeError("app Electron 版本异常")


def _validate_inputs() -> None:
    ensure_file(DMG, "项目内 DMG 不存在")
    ensure_file(RUNTIME / "electron", "项目内 Electron runtime 不存在")
    ensure_file(ASAR_CLI, "asar CLI 不存在，请先构建 native modules")
    version = run(
        [str(RUNTIME / "electron"), "--version"],
        capture_output=True,
    ).stdout.strip()
    if version != f"v{APP.electron_version}":
        raise RuntimeError(f"Electron runtime 版本异常: {version}")
    print(f"DMG SHA256: {sha256_file(DMG)}")


def _copy_runtime(prototype: Path) -> None:
    for item in RUNTIME.iterdir():
        if item.name == "resources":
            continue
        copy_entry(item, prototype / item.name)
    for name in ("electron", "chrome_crashpad_handler"):
        path = prototype / name
        if path.exists():
            make_executable(path)
    for name in ("ChatGPT", "Codex"):
        shutil.copy2(prototype / "electron", prototype / name)
        make_executable(prototype / name)


def _prune_macos(root: Path) -> None:
    for path in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if not path.exists() or path.is_symlink():
            continue
        parts = {part.lower() for part in path.parts}
        if path.is_dir() and (
            path.name.endswith((".app", ".dSYM"))
            or any("darwin" in part for part in parts)
        ):
            shutil.rmtree(path)
        elif path.is_file() and (
            path.suffix.lower() in {".dylib", ".icns"}
            or path.name == "spawn-helper"
            or any("darwin" in part for part in parts)
            or is_macho(path)
        ):
            path.unlink()


def _install_native(extracted: Path) -> None:
    root = extracted / "node_modules"
    for artifact in NATIVE_ARTIFACTS:
        source = NATIVE_MODULES / artifact.source
        ensure_file(source, f"缺少 native artifact {artifact.name}")
        info = run(["file", str(source)], capture_output=True).stdout
        if "ELF 64-bit" not in info or "x86-64" not in info:
            raise RuntimeError(f"native artifact 架构异常: {source}")
        target = root / artifact.destination
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _repack_app(dmg_resources: Path, prototype: Path, build_root: Path) -> None:
    resources = prototype / "resources"
    resources.mkdir()
    extracted = build_root / "app-extracted"
    packed = build_root / "app.asar.repacked"
    unpacked = build_root / "app.asar.repacked.unpacked"
    ordering = build_root / "app.asar.ordering"
    for path in (extracted, unpacked):
        if path.exists():
            shutil.rmtree(path)
    packed.unlink(missing_ok=True)

    run([str(ASAR_CLI), "extract", str(dmg_resources / "app.asar"), str(extracted)])
    shutil.copytree(
        dmg_resources / "app.asar.unpacked",
        extracted,
        dirs_exist_ok=True,
        symlinks=True,
    )
    _validate_metadata(dmg_resources.parent.parent, extracted)
    _prune_macos(extracted)
    _install_native(extracted)
    labels = apply_patches(extracted)
    print(f"已应用 Linux 补丁: {len(labels)}")

    files = sorted(
        str(path.relative_to(extracted))
        for path in extracted.rglob("*")
        if path.is_file()
    )
    ordering.write_text("\n".join(files) + "\n", encoding="utf-8")
    run(
        [
            str(ASAR_CLI), "pack", str(extracted), str(packed),
            "--ordering", str(ordering), "--unpack", "{*.node,*.so}",
        ]
    )
    ensure_dir(unpacked, "asar 重包后缺少 unpacked 目录")
    packed.replace(resources / "app.asar")
    unpacked.replace(resources / "app.asar.unpacked")

    for name in ("codex-notification.wav", "icon-chatgpt.png", "owl-electron-app.json"):
        source = dmg_resources / name
        if source.is_file():
            shutil.copy2(source, resources / name)
    compose_plugins(dmg_resources, resources)


def _write_launcher(prototype: Path) -> None:
    launcher = prototype / "run-chatgpt-linux.sh"
    launcher.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env bash
            # 支持直连既有 app-server，也支持由 Electron 启动系统 native codex。
            set -euo pipefail
            cd "$(dirname "$0")"

            host="${CODEX_APP_SERVER_HOST:-127.0.0.1}"
            port="${CODEX_APP_SERVER_PORT:-18765}"
            if (exec 3<>"/dev/tcp/$host/$port") 2>/dev/null; then
              export CODEX_APP_SERVER_WS_URL="${CODEX_APP_SERVER_WS_URL:-ws://$host:$port}"
              unset CODEX_CLI_PATH
              echo "连接现有 app-server: $CODEX_APP_SERVER_WS_URL" >&2
            else
              native_codex="${CODEX_CLI_PATH:-$(command -v codex || true)}"
              if [ -z "$native_codex" ] && [ -x /data/bin/codex ]; then
                native_codex=/data/bin/codex
              fi
              if [ -z "$native_codex" ]; then
                echo "未找到系统 native codex" >&2
                exit 1
              fi
              native_codex="$(readlink -f "$native_codex")"
              if [ ! -x "$native_codex" ]; then
                echo "系统 codex 不可执行: $native_codex" >&2
                exit 1
              fi
              unset CODEX_APP_SERVER_WS_URL
              export CODEX_CLI_PATH="$native_codex"
              echo "由应用启动 app-server: $CODEX_CLI_PATH" >&2
            fi

            default_profile="${XDG_CONFIG_HOME:-$HOME/.config}/ChatGPT-Linux"
            export CODEX_ELECTRON_USER_DATA_PATH="${CODEX_ELECTRON_USER_DATA_PATH:-$default_profile}"
            export ELECTRON_ENABLE_LOGGING=1
            unset ELECTRON_RUN_AS_NODE
            exec ./ChatGPT --no-sandbox "$@"
            """
        ),
        encoding="utf-8",
    )
    launcher.chmod(0o755)


def build_prototype(build_root: Path) -> Path:
    _validate_inputs()
    prototype = build_root / APP.prototype_name
    extract_root = build_root / "_extract"
    for path in (prototype, extract_root):
        if path.exists():
            shutil.rmtree(path)
    prototype.mkdir(parents=True)
    _copy_runtime(prototype)
    bundle, resources = _extract_dmg(extract_root)
    _repack_app(resources, prototype, build_root)
    _write_launcher(prototype)
    shutil.rmtree(extract_root)
    return prototype
