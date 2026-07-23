"""加载版本补丁并执行精确单次替换。"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

from .config import VERSION_ROOT


def _load_version_module() -> ModuleType:
    path = VERSION_ROOT / "patches.py"
    spec = importlib.util.spec_from_file_location("chatgpt_version_patches", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载版本补丁: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _area_files(root: Path, area: str) -> list[Path]:
    if area == "main":
        return sorted((root / ".vite/build").glob("main-*.js"))
    if area == "worker":
        return [root / ".vite/build/worker.js"]
    if area == "webview":
        return sorted((root / "webview/assets").glob("*.js"))
    raise RuntimeError(f"未知补丁区域: {area}")


def apply_patches(root: Path) -> list[str]:
    module = _load_version_module()
    labels: list[str] = []
    for patch in module.PATCHES:
        matches: list[Path] = []
        for path in _area_files(root, patch.area):
            source = path.read_text(encoding="utf-8")
            count = source.count(patch.old)
            if count > 1:
                raise RuntimeError(f"{patch.label} 在 {path} 匹配 {count} 次")
            if count == 1:
                path.write_text(
                    source.replace(patch.old, patch.new, 1),
                    encoding="utf-8",
                )
                matches.append(path)
        print(f"{patch.label}: {len(matches)}")
        if len(matches) != 1:
            raise RuntimeError(f"{patch.label} 总匹配次数异常: {len(matches)}")
        labels.append(patch.label)
    verify_patch_markers(root, labels)
    return labels


def verify_patch_markers(root: Path, labels: list[str]) -> None:
    main = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((root / ".vite/build").glob("main-*.js"))
    )
    worker = (root / ".vite/build/worker.js").read_text(encoding="utf-8")
    webview = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((root / "webview/assets").glob("*.js"))
    )
    markers = {
        "main": (
            "return!I9(e)&&(t||n===`linux`)",
            "linux:{label:`File Manager`,detect:()=>Ds(`xdg-open`)",
            "linuxDetect:()=>Ds(`code`)??`code`",
            "linuxCommand:`idea`",
            "linuxCommand:`rustrover`",
            "linuxCommand:`pycharm`",
            "linuxCommand:`webstorm`",
        ),
        "worker": (
            "linux:{label:`File Manager`,detect:()=>U7(`xdg-open`)",
            "linuxDetect:()=>U7(`code`)??`code`",
            "linuxCommand:`idea`",
            "linuxCommand:`rustrover`",
            "linuxCommand:`pycharm`",
            "linuxCommand:`webstorm`",
        ),
        "webview": (
            "return r===`native`?c([...i,...e.filter",
        ),
    }
    for area, source in (("main", main), ("worker", worker), ("webview", webview)):
        for marker in markers[area]:
            if marker not in source:
                raise RuntimeError(f"{area} 缺少补丁标记: {marker}")
    if len(labels) != 18:
        raise RuntimeError(f"补丁数量异常: {len(labels)}")
