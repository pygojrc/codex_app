"""Linux 原型的静态验收。"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from .common import ensure_dir, ensure_file, is_macho, run, sha256_file
from .config import ASAR_CLI, CODEX_ICON_NAME, NATIVE_ARTIFACTS, WINDOW_CLASS
from .plugins import verify_plugins


def resolve_system_codex(prototype: Path) -> Path:
    command = shutil.which("codex")
    if command is None and Path("/data/bin/codex").is_file():
        command = "/data/bin/codex"
    if command is None:
        raise RuntimeError("PATH 和 /data/bin 中都没有系统 codex")
    path = Path(command).resolve()
    ensure_file(path, "系统 codex 不存在")
    if not os.access(path, os.X_OK):
        raise RuntimeError(f"系统 codex 不可执行: {path}")
    try:
        path.relative_to(prototype.resolve())
    except ValueError:
        pass
    else:
        raise RuntimeError("拒绝使用原型内 codex")
    info = run(["file", str(path)], capture_output=True).stdout
    if "ELF 64-bit" not in info:
        raise RuntimeError(f"系统 codex 不是 Linux ELF: {info.strip()}")
    return path


def _verify_native(prototype: Path) -> None:
    resources = prototype / "resources"
    listing = run(
        [str(ASAR_CLI), "list", "--is-pack", str(resources / "app.asar")],
        capture_output=True,
    ).stdout
    for artifact in NATIVE_ARTIFACTS:
        marker = f"unpack : /node_modules/{artifact.destination}"
        if marker not in listing:
            raise RuntimeError(f"asar 缺少 native unpack 标记: {artifact.name}")
        path = resources / "app.asar.unpacked/node_modules" / artifact.destination
        ensure_file(path, f"缺少 native artifact {artifact.name}")
        info = run(["file", str(path)], capture_output=True).stdout
        if "ELF 64-bit" not in info or "x86-64" not in info:
            raise RuntimeError(f"native artifact 架构异常: {path}")
    if "/webview/dream-skin/theme.js" not in listing:
        raise RuntimeError("asar 缺少 Dream Skin 主题脚本")


def _verify_no_macos(prototype: Path) -> None:
    forbidden_names = {
        "codex", "codex-code-mode-host", "codex_chronicle", "rg",
        "cua_node", "native", "default_app",
    }
    resources = prototype / "resources"
    present = sorted(name for name in forbidden_names if (resources / name).exists())
    if present:
        raise RuntimeError(f"禁用资源仍存在: {present}")
    bad: list[Path] = []
    for path in prototype.rglob("*"):
        if path.is_file() and (
            path.suffix.lower() in {".dylib", ".icns"} or is_macho(path)
        ):
            bad.append(path)
    if bad:
        raise RuntimeError(f"原型残留 macOS artifact: {bad[:10]}")


def verify_prototype(prototype: Path) -> Path:
    for relative in (
        "electron",
        "ChatGPT",
        "Codex",
        "run-chatgpt-linux.sh",
        "resources/app.asar",
        f"resources/{CODEX_ICON_NAME}",
    ):
        ensure_file(prototype / relative, "原型缺少关键文件")
    ensure_dir(
        prototype / "resources/app.asar.unpacked",
        "原型缺少 app.asar.unpacked",
    )
    binaries = run(
        ["file", str(prototype / "electron"), str(prototype / "ChatGPT")],
        capture_output=True,
    ).stdout
    if binaries.count("ELF 64-bit") != 2:
        raise RuntimeError(f"Electron 外壳异常:\n{binaries}")
    icon = prototype / "resources" / CODEX_ICON_NAME
    tray_icon = prototype / "resources/icon-chatgpt.png"
    icon_info = run(["file", str(icon)], capture_output=True).stdout
    if "PNG image data, 1024 x 1024" not in icon_info:
        raise RuntimeError(f"Codex 图标异常: {icon_info.strip()}")
    if sha256_file(icon) != sha256_file(tray_icon):
        raise RuntimeError("桌面图标与 Linux tray 图标不一致")
    launcher = (prototype / "run-chatgpt-linux.sh").read_text(encoding="utf-8")
    for marker in (
        "CODEX_APP_SERVER_WS_URL",
        'export CODEX_CLI_PATH="$native_codex"',
        "CODEX_ELECTRON_USER_DATA_PATH",
        f"exec ./ChatGPT --class={WINDOW_CLASS} --no-sandbox",
    ):
        if marker not in launcher:
            raise RuntimeError(f"launcher 缺少标记: {marker}")
    _verify_native(prototype)
    verify_plugins(prototype / "resources")
    _verify_no_macos(prototype)
    codex = resolve_system_codex(prototype)
    print(f"静态验收通过，系统 codex: {codex}")
    return codex
