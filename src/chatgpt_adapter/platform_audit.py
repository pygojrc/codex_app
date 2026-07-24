"""验证 Linux 原型中不存在 macOS 二进制，并记录 ELF/native 清单。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .common import run
from .config import APP


def audit_linux_payload(root: Path) -> Path:
    macho: list[str] = []
    native: list[dict[str, str]] = []
    unresolved: list[dict[str, str]] = []

    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = str(path.relative_to(root))
        info = run(["file", "-b", str(path)], capture_output=True).stdout.strip()
        if "Mach-O" in info:
            macho.append(relative)
        if path.suffix in {".node", ".so"} or "ELF " in info:
            native.append({"path": relative, "file": info})
            if "ELF " in info:
                result = run(["ldd", str(path)], capture_output=True, check=False)
                output = (result.stdout or "") + (result.stderr or "")
                missing = "\n".join(
                    line.strip() for line in output.splitlines() if "not found" in line
                )
                if missing:
                    unresolved.append({"path": relative, "missing": missing})

    report_dir = root / ".codex-linux"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = report_dir / "platform-audit.json"
    payload = {
        "schema": "codex-linux-platform-audit/1",
        "appVersion": APP.version,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "architecture": "x86_64",
        "macho": macho,
        "native": native,
        "unresolvedLibraries": unresolved,
    }
    report.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if macho:
        raise RuntimeError(f"Linux 原型仍包含 Mach-O 文件: {macho}")
    if unresolved:
        raise RuntimeError(f"Linux 原型存在未解析共享库: {unresolved}")
    return report
