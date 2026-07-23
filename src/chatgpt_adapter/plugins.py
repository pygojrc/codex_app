"""从当前 DMG 组装经白名单审计的插件集合。"""

from __future__ import annotations

import shutil
from pathlib import Path

from .common import ensure_dir, ensure_file, is_macho, read_json, write_json
from .config import APP, TECTONIC


def _prune_macos(root: Path) -> None:
    for path in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if not path.exists() or path.is_symlink():
            continue
        parts = {part.lower() for part in path.parts}
        if path.is_dir() and (
            "macos" in parts or any("darwin" in part for part in parts)
        ):
            shutil.rmtree(path)
        elif path.is_file() and is_macho(path):
            path.unlink()


def compose_plugins(dmg_resources: Path, target_resources: Path) -> None:
    source_root = dmg_resources / "plugins/openai-bundled"
    target_root = target_resources / "plugins/openai-bundled"
    target_plugins = target_root / "plugins"
    target_plugins.mkdir(parents=True)
    for name in APP.active_plugins:
        source = source_root / "plugins" / name
        ensure_dir(source, f"DMG 缺少插件 {name}")
        shutil.copytree(source, target_plugins / name, symlinks=True)
    _prune_macos(target_plugins)
    ensure_file(TECTONIC, "缺少 Linux Tectonic，请先运行下载脚本")
    tectonic = target_plugins / "latex/bin/tectonic"
    tectonic.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TECTONIC, tectonic)
    tectonic.chmod(0o755)

    marketplace = read_json(source_root / ".agents/plugins/marketplace.json")
    entries = marketplace.get("plugins")
    if not isinstance(entries, list):
        raise RuntimeError("marketplace.json 缺少 plugins 数组")
    marketplace["plugins"] = [
        item
        for item in entries
        if isinstance(item, dict) and item.get("name") in APP.active_plugins
    ]
    write_json(target_root / ".agents/plugins/marketplace.json", marketplace)
    verify_plugins(target_resources)


def verify_plugins(resources: Path) -> None:
    root = resources / "plugins/openai-bundled"
    dirs = {path.name for path in (root / "plugins").iterdir() if path.is_dir()}
    expected = set(APP.active_plugins)
    if dirs != expected:
        raise RuntimeError(f"插件目录异常: actual={sorted(dirs)}")
    marketplace = read_json(root / ".agents/plugins/marketplace.json")
    names = {
        item.get("name")
        for item in marketplace.get("plugins", [])
        if isinstance(item, dict)
    }
    if names != expected:
        raise RuntimeError(f"插件注册异常: actual={sorted(names)}")
    for name in APP.excluded_plugins:
        if (root / "plugins" / name).exists() or name in names:
            raise RuntimeError(f"已排除插件仍存在: {name}")
