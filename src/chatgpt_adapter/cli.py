"""ChatGPT Linux 适配构建入口。"""

from __future__ import annotations

import argparse
import shutil

from .builder import build_prototype
from .config import BUILD_ROOT
from .packaging import package_prototype
from .platform_audit import audit_linux_payload
from .verify import verify_prototype


def _finalize_linux_prototype(prototype) -> None:
    launcher = prototype / "run-chatgpt-linux.sh"
    source = launcher.read_text(encoding="utf-8")
    old = 'port="${CODEX_APP_SERVER_PORT:-18765}"'
    new = 'port="${CODEX_APP_SERVER_PORT:-18767}"'
    if old in source:
        launcher.write_text(source.replace(old, new, 1), encoding="utf-8")
    elif new not in source:
        raise RuntimeError("无法确认默认 app-server 端口")

    report_dir = prototype / ".codex-linux"
    report_dir.mkdir(parents=True, exist_ok=True)
    patch_report = BUILD_ROOT / "app-extracted/.codex-linux/patch-report.json"
    if not patch_report.is_file():
        raise FileNotFoundError(f"缺少补丁报告: {patch_report}")
    shutil.copy2(patch_report, report_dir / "patch-report.json")
    print(f"平台审计: {audit_linux_payload(prototype)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-package", action="store_true", help="只构建原型")
    args = parser.parse_args()
    prototype = build_prototype(BUILD_ROOT)
    _finalize_linux_prototype(prototype)
    verify_prototype(prototype)
    print(f"原型目录: {prototype}")
    if not args.no_package:
        print(f"发行包: {package_prototype(prototype)}")


if __name__ == "__main__":
    main()
