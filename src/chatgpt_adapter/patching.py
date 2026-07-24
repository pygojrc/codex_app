"""加载版本补丁、执行精确替换并生成机器可读报告。"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType

from .config import APP, VERSION_ROOT


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


def _write_report(root: Path, entries: list[dict[str, object]]) -> Path:
    report_dir = root / ".codex-linux"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "patch-report.json"
    required_failures = [
        entry for entry in entries
        if entry["policy"] == "required-upstream" and entry["status"] != "applied"
    ]
    payload = {
        "schema": "codex-linux-patch-report/1",
        "appVersion": APP.version,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": len(entries),
            "applied": sum(entry["status"] == "applied" for entry in entries),
            "requiredFailures": len(required_failures),
        },
        "patches": entries,
    }
    report_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report_path


def apply_patches(root: Path) -> list[str]:
    module = _load_version_module()
    labels: list[str] = []
    entries: list[dict[str, object]] = []
    failure: RuntimeError | None = None

    for index, patch in enumerate(module.PATCHES, start=1):
        matches: list[Path] = []
        status = "missing"
        error_message: str | None = None
        try:
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
            if len(matches) != 1:
                raise RuntimeError(f"{patch.label} 总匹配次数异常: {len(matches)}")
            status = "applied"
            labels.append(patch.label)
        except RuntimeError as error:
            status = "failed"
            error_message = str(error)
            if failure is None:
                failure = error

        print(f"{patch.label}: {status} ({len(matches)})")
        entries.append(
            {
                "id": f"version-{index:02d}",
                "label": patch.label,
                "area": patch.area,
                "policy": "required-upstream",
                "status": status,
                "expectedMatches": 1,
                "matches": len(matches),
                "files": [str(path.relative_to(root)) for path in matches],
                "error": error_message,
            }
        )

    if failure is None:
        try:
            verify_patch_markers(root, labels)
        except RuntimeError as error:
            failure = error
            entries.append(
                {
                    "id": "marker-verification",
                    "label": "Linux 补丁标记验证",
                    "area": "all",
                    "policy": "required-upstream",
                    "status": "failed",
                    "expectedMatches": None,
                    "matches": 0,
                    "files": [],
                    "error": str(error),
                }
            )

    report_path = _write_report(root, entries)
    print(f"补丁报告: {report_path}")
    if failure is not None:
        raise RuntimeError(f"关键 Linux 补丁失败；详见 {report_path}: {failure}") from failure
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
            "icon:process.platform===`linux`?(0,f.join)"
            "(process.resourcesPath,`codex-gui.png`)",
            "linux:{label:`File Manager`,detect:()=>Ds(`xdg-open`)",
            "linuxDetect:()=>Ds(`code`)??`code`",
            "`.local`,`share`,`JetBrains`,`Toolbox`,`apps`,"
            "r===`intellij`?`intellij-idea`:r",
            "linuxCommand:`idea`",
            "linuxCommand:`rustrover`",
            "linuxCommand:`pycharm`",
            "linuxCommand:`webstorm`",
        ),
        "worker": (
            "linux:{label:`File Manager`,detect:()=>U7(`xdg-open`)",
            "linuxDetect:()=>U7(`code`)??`code`",
            "`.local`,`share`,`JetBrains`,`Toolbox`,`apps`,"
            "r===`intellij`?`intellij-idea`:r",
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
    if len(labels) != 19:
        raise RuntimeError(f"补丁数量异常: {len(labels)}")
