"""封装并校验 tar.zst 发行包。"""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from .common import ensure_dir, ensure_file, run, sha256_file, write_json
from .config import APP, CODEX_ICON_NAME, DIST_ROOT, PACKAGE_NAME


def verify_package(package: Path) -> list[str]:
    """检查压缩包路径边界和安装所需关键文件。"""
    ensure_file(package, "发行包不存在")
    result = run(["tar", "--zstd", "-tf", str(package)], capture_output=True)
    entries = [line.rstrip("/") for line in result.stdout.splitlines() if line]
    for entry in entries:
        path = PurePosixPath(entry)
        if path.is_absolute() or ".." in path.parts or path.parts[0] != APP.prototype_name:
            raise RuntimeError(f"发行包包含不安全路径: {entry}")
    required = {
        f"{APP.prototype_name}/ChatGPT",
        f"{APP.prototype_name}/run-chatgpt-linux.sh",
        f"{APP.prototype_name}/resources/app.asar",
        f"{APP.prototype_name}/resources/{CODEX_ICON_NAME}",
    }
    missing = required - set(entries)
    if missing:
        raise RuntimeError(f"发行包缺少关键文件: {sorted(missing)}")
    return entries


def package_prototype(prototype: Path) -> Path:
    ensure_dir(prototype, "待打包原型不存在")
    DIST_ROOT.mkdir(parents=True, exist_ok=True)
    package = DIST_ROOT / PACKAGE_NAME
    temporary = DIST_ROOT / f".{PACKAGE_NAME}.tmp"
    temporary.unlink(missing_ok=True)
    run(["tar", "--zstd", "-cf", str(temporary), "-C", str(prototype.parent), prototype.name])
    temporary.replace(package)
    entries = verify_package(package)
    digest = sha256_file(package)
    (DIST_ROOT / f"{PACKAGE_NAME}.sha256").write_text(
        f"{digest}  {PACKAGE_NAME}\n", encoding="utf-8"
    )
    write_json(
        DIST_ROOT / "manifest.json",
        {
            "appVersion": APP.version,
            "electronVersion": APP.electron_version,
            "name": PACKAGE_NAME,
            "size": package.stat().st_size,
            "sha256": digest,
            "entries": len(entries),
        },
    )
    return package
